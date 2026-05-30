"""
Middleware components for the Drug Discovery AI Agent.
Handles authentication, rate limiting, logging, and request processing.
"""
import time
import uuid
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import request, g, jsonify
from werkzeug.exceptions import HTTPException

from config import get_config
from database import log_system_event, create_user_session
from models import ErrorResponse

logger = logging.getLogger(__name__)


def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()

class RateLimiter:
    """Rate limiting middleware"""

    def __init__(self):
        self.config = get_config()
        self.requests: Dict[str, list] = {}

    def is_allowed(self, key: str, limit: int, window: int = 3600) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        window_start = now - window

        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]

        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True

        return False

    def get_remaining_requests(self, key: str, limit: int, window: int = 3600) -> int:
        """Get remaining requests in current window"""
        now = time.time()
        window_start = now - window

        if key not in self.requests:
            return limit

        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]

        return max(0, limit - len(self.requests[key]))

# Global rate limiter
rate_limiter = RateLimiter()

def rate_limit(limit: int = 100, window: int = 3600, key_func: Optional[Callable] = None):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get rate limit key
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr

            if not rate_limiter.is_allowed(key, limit, window):
                remaining = rate_limiter.get_remaining_requests(key, limit, window)
                reset_time = int(time.time() + window)

                response = jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} per {window//3600} hour(s)",
                    "remaining": remaining,
                    "reset_time": reset_time
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(reset_time)

                log_system_event('WARNING', f'Rate limit exceeded for {key}', 'middleware', f.__name__)
                return response

            return f(*args, **kwargs)
        return wrapper
    return decorator

def session_management():
    """Session management middleware"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Generate or get session ID
            session_id = request.headers.get('X-Session-ID') or str(uuid.uuid4())

            # Store in Flask g object
            g.session_id = session_id
            g.start_time = time.time()

            # Ensure session exists in database
            try:
                create_user_session(
                    session_id=session_id,
                    user_agent=request.headers.get('User-Agent'),
                    ip_address=request.remote_addr
                )
            except Exception as e:
                logger.warning(f"Failed to create session: {e}")

            # Add session ID to response headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-Session-ID'] = session_id

            return response
        return wrapper
    return decorator

def request_logging():
    """Request logging middleware"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Log request
            logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

            try:
                response = f(*args, **kwargs)
                processing_time = time.time() - start_time

                # Log successful response
                if hasattr(response, 'status_code'):
                    status_code = response.status_code
                else:
                    status_code = 200

                logger.info(f"Response: {status_code} in {processing_time:.3f}s")

                # Log to database for important endpoints
                if request.path.startswith('/api/chat') or request.path.startswith('/api/search'):
                    log_system_event(
                        'INFO',
                        f'{request.method} {request.path} - {status_code} ({processing_time:.3f}s)',
                        'api',
                        f.__name__,
                        session_id=getattr(g, 'session_id', None)
                    )

                return response

            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Request error: {e} (took {processing_time:.3f}s)")

                log_system_event(
                    'ERROR',
                    f'{request.method} {request.path} failed: {e}',
                    'api',
                    f.__name__,
                    session_id=getattr(g, 'session_id', None)
                )
                raise

        return wrapper
    return decorator

def error_handler():
    """Global error handling middleware"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except HTTPException as e:
                # Flask HTTP exceptions
                return jsonify({
                    "error": e.description,
                    "status": "error",
                    "code": e.code
                }), e.code
            except Exception as e:
                # General exceptions
                logger.error(f"Unhandled error: {e}", exc_info=True)

                # Log to database
                log_system_event(
                    'ERROR',
                    f'Unhandled error: {e}',
                    'api',
                    f.__name__,
                    session_id=getattr(g, 'session_id', None)
                )

                # Return error response
                error_response = ErrorResponse(
                    error="Internal server error",
                    status="error",
                    code=500,
                    details=str(e) if get_config().flask.debug else None,
                    traceback=str(e) if get_config().flask.debug else None
                )

                return jsonify(model_to_dict(error_response)), 500

        return wrapper
    return decorator

def cors_middleware(app):
    """CORS middleware setup"""
    @app.after_request
    def after_request(response):
        config = get_config()

        # Set CORS headers. With credentials enabled, browsers require one
        # concrete origin instead of a comma-separated list.
        origin = request.headers.get('Origin')
        if origin in config.flask.cors_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = config.flask.cors_origins[0]
        response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Session-ID'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours

        return response

def security_headers():
    """Security headers middleware"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            response = f(*args, **kwargs)

            # Handle tuple responses (response, status_code)
            if isinstance(response, tuple):
                resp, status = response
                # Add security headers to the response object
                resp.headers['X-Content-Type-Options'] = 'nosniff'
                resp.headers['X-Frame-Options'] = 'DENY'
                resp.headers['X-XSS-Protection'] = '1; mode=block'
                resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                resp.headers['Content-Security-Policy'] = "default-src 'self'"
                return resp, status
            else:
                # Add security headers
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                response.headers['Content-Security-Policy'] = "default-src 'self'"
                return response
        return wrapper
    return decorator

def cache_control(max_age: int = 300):
    """Cache control middleware"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            response = f(*args, **kwargs)

            # Handle tuple responses (response, status_code)
            if isinstance(response, tuple):
                resp, status = response
                resp.headers['Cache-Control'] = f'public, max-age={max_age}'
                resp.headers['Expires'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                                                      time.gmtime(time.time() + max_age))
                return resp, status
            else:
                response.headers['Cache-Control'] = f'public, max-age={max_age}'
                response.headers['Expires'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                                                      time.gmtime(time.time() + max_age))
                return response

        return wrapper
    return decorator

# Combined middleware decorator for API endpoints
def api_middleware(rate_limit_enabled: bool = True, cache_enabled: bool = False):
    """Combined middleware for API endpoints"""
    def decorator(f):
        # Apply middleware in order
        f = error_handler()(f)
        f = request_logging()(f)
        f = session_management()(f)
        f = security_headers()(f)

        if rate_limit_enabled:
            f = rate_limit()(f)

        if cache_enabled:
            f = cache_control()(f)

        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator
