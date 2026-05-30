"""
Utility functions for the Drug Discovery AI Agent.
Common helpers, validators, and data processing functions.
"""
import re
import hashlib
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return str(uuid.uuid4())

def hash_string(text: str) -> str:
    """Generate SHA256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input by removing potentially harmful content"""
    if not text:
        return ""

    # Remove null bytes and other control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # Limit length
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text.strip()

def format_timestamp(timestamp: Union[str, float, datetime]) -> str:
    """Format timestamp to ISO format"""
    if isinstance(timestamp, str):
        try:
            # Try to parse string timestamp
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return timestamp
    elif isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        return str(timestamp)

    return dt.isoformat()

def calculate_relevance_score(query: str, text: str) -> float:
    """Calculate relevance score between query and text"""
    query_words = set(query.lower().split())
    text_words = set(text.lower().split())

    if not query_words:
        return 0.0

    intersection = query_words.intersection(text_words)
    union = query_words.union(text_words)

    # Jaccard similarity
    return len(intersection) / len(union) if union else 0.0

def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text using simple frequency analysis"""
    if not text:
        return []

    # Simple word extraction (in production, use NLTK or spaCy)
    words = re.findall(r'\b\w+\b', text.lower())

    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'}

    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    # Count frequency
    from collections import Counter
    word_counts = Counter(keywords)

    # Return most common keywords
    return [word for word, _ in word_counts.most_common(max_keywords)]

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely serialize to JSON string"""
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError):
        return default

def parse_pubmed_id(text: str) -> Optional[str]:
    """Extract PubMed ID from text"""
    match = re.search(r'PMID:\s*(\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Try to find standalone numbers that look like PMIDs
    match = re.search(r'\b(\d{7,8})\b', text)
    if match:
        return match.group(1)

    return None

def format_file_size(bytes_size: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return ".1f"
        bytes_size /= 1024.0
    return ".1f"

def validate_api_key(api_key: str, service: str) -> bool:
    """Validate API key format for different services"""
    if not api_key:
        return False

    # Service-specific validation patterns
    patterns = {
        'groq': r'^gsk_[a-zA-Z0-9]{48}$',
        'gemini': r'^AIza[0-9A-Za-z-_]{35}$',
        'openai': r'^sk-[a-zA-Z0-9]{48}$',
    }

    pattern = patterns.get(service)
    if pattern:
        return re.match(pattern, api_key) is not None

    # Generic validation for other services
    return len(api_key) >= 10

def create_cache_key(*args, **kwargs) -> str:
    """Create a cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def time_since(timestamp: Union[str, datetime, float]) -> str:
    """Get human readable time since timestamp"""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return "Unknown"
    elif isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        return "Unknown"

    now = datetime.now()
    diff = now - dt

    if diff.days > 365:
        return f"{diff.days // 365}y ago"
    elif diff.days > 30:
        return f"{diff.days // 30}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return f"{diff.seconds}s ago"

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result

def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """Mask sensitive data in dictionary"""
    if sensitive_keys is None:
        sensitive_keys = ['api_key', 'password', 'secret', 'token', 'key']

    masked = {}

    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value, sensitive_keys)
        elif isinstance(value, list):
            masked[key] = [
                mask_sensitive_data(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            masked[key] = value

    return masked

class Timer:
    """Context manager for timing operations"""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"Starting {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        logger.debug(".3f")

        if exc_type:
            logger.error(f"{self.name} failed after {duration:.3f}s: {exc_val}")
        else:
            logger.info(".3f")