"""
Main application entry point for the Drug Discovery AI Agent.
Organized Flask application with proper structure, middleware, and error handling.
"""
import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

# Add current directory and modules to path for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Import configuration and components
from config import get_config
from database import db_manager
from middleware import cors_middleware
from api import api_bp

_app_instance = None

def create_app(config_name: str = 'development') -> Flask:
    """Application factory pattern"""
    global _app_instance
    if _app_instance is not None:
        return _app_instance

    config = get_config()

    # Create Flask app
    app = Flask(__name__)

    # Apply proxy fix for production deployments
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure Flask
    app.config['SECRET_KEY'] = config.flask.secret_key
    app.config['DEBUG'] = config.flask.debug
    app.config['TESTING'] = config.flask.testing

    # Setup logging
    setup_logging(app, config)

    # Register middleware
    cors_middleware(app)

    # Register blueprints
    app.register_blueprint(api_bp)

    # Register error handlers
    register_error_handlers(app)

    # Register health check at root level
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with basic info"""
        return jsonify({
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "status": "running",
            "timestamp": datetime.now().isoformat()
        })

    # Warmup services on startup
    with app.app_context():
        warmup_services()

    print_application_banner(config)

    _app_instance = app
    return app

def setup_logging(app: Flask, config):
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    if config.logging.file_path:
        os.makedirs(os.path.dirname(config.logging.file_path), exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.logging.level.upper()),
        format=config.logging.format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.logging.file_path) if config.logging.file_path else logging.NullHandler()
        ]
    )

    # Reduce noise from third-party libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    app.logger.info(f"Logging configured with level: {config.logging.level}")

def register_error_handlers(app: Flask):
    """Register global error handlers"""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Endpoint not found",
            "status": "error",
            "code": 404,
            "message": f"The requested URL {request.path} was not found"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "error": "Method not allowed",
            "status": "error",
            "code": 405,
            "message": f"Method {request.method} not allowed for {request.path}"
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            "error": "Internal server error",
            "status": "error",
            "code": 500,
            "message": "An unexpected error occurred"
        }), 500

def warmup_services():
    """Warm up services on application startup"""
    try:
        # Test database connection
        if db_manager.health_check():
            print("✓ Database connection established")
        else:
            print("✗ Database connection failed")

        # Import and test services
        from services import agent_service, rag_service, paper_service

        # Test service availability
        from config import is_service_available
        services_to_check = ['groq', 'gemini', 'pubmed', 'pdb', 'pubchem', 'ncbi']

        for service in services_to_check:
            status = "✓ Ready" if is_service_available(service) else "✗ Not configured"
            print(f"{service.capitalize()}: {status}")

        print("✓ Service warmup completed")

    except Exception as e:
        print(f"✗ Service warmup failed: {e}")

def print_application_banner(config):
    """Print application startup banner"""
    banner = f"""
{'='*70}
{config.name.upper()} v{config.version}
{'='*70}
Description: {config.description}
Environment: {'Development' if config.flask.debug else 'Production'}
Host: {config.flask.host}:{config.flask.port}
CORS Origins: {', '.join(config.flask.cors_origins)}
Database: {config.database.url}
Logging Level: {config.logging.level}
Rate Limiting: {'Enabled' if config.rate_limit.enabled else 'Disabled'}
{'='*70}
"""

    print(banner)

# Create application instance
app = create_app()

if __name__ == '__main__':
    config = get_config()
    app.run(
        host=config.flask.host,
        port=config.flask.port,
        debug=config.flask.debug,
        threaded=True,
        use_reloader=config.flask.debug
    )
