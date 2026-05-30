"""
Configuration management for the Drug Discovery AI Agent backend.
Handles environment variables, database connections, API keys, and application settings.
"""
import os
import secrets
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    """API configuration settings"""
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    pubmed_api_key: Optional[str] = None
    ncbi_api_key: Optional[str] = None
    chembl_api_key: Optional[str] = None

    def __post_init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.pubmed_api_key = os.getenv('PUBMED_API_KEY')
        self.ncbi_api_key = os.getenv('NCBI_API_KEY')
        self.chembl_api_key = os.getenv('CHEMBL_API_KEY')

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str = os.getenv("DATABASE_URL", "sqlite:///drug_discovery.db")
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30

@dataclass
class RedisConfig:
    """Redis configuration for caching and background tasks"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    enabled: bool = False

@dataclass
class FlaskConfig:
    """Flask application configuration"""
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    debug: bool = os.getenv('FLASK_DEBUG', 'true' if os.getenv('FLASK_ENV', 'production') == 'development' else 'false').lower() == 'true'
    testing: bool = os.getenv('FLASK_TESTING', 'False').lower() == 'true'
    host: str = os.getenv('FLASK_HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', os.getenv('FLASK_PORT', '5001')))
    cors_origins: list = None

    def __post_init__(self):
        if self.cors_origins is None:
            origins = os.getenv("CORS_ORIGINS")
            self.cors_origins = [origin.strip() for origin in origins.split(",")] if origins else ["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    enabled: bool = True
    default_limits: Dict[str, int] = None

    def __post_init__(self):
        if self.default_limits is None:
            self.default_limits = {
                "chat": 100,  # requests per hour
                "search": 500,
                "download": 50
            }

@dataclass
class AppConfig:
    """Main application configuration"""
    name: str = "Drug Discovery AI Agent"
    version: str = "2.0.0"
    description: str = "Advanced AI-powered drug discovery research assistant"

    api: APIConfig = None
    database: DatabaseConfig = None
    redis: RedisConfig = None
    flask: FlaskConfig = None
    logging: LoggingConfig = None
    rate_limit: RateLimitConfig = None

    def __post_init__(self):
        self.api = APIConfig()
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.flask = FlaskConfig()
        self.logging = LoggingConfig()
        self.rate_limit = RateLimitConfig()

# Global configuration instance
config = AppConfig()

def get_config() -> AppConfig:
    """Get the global application configuration"""
    return config

def is_service_available(service_name: str) -> bool:
    """Check if a service is available based on configuration"""
    api_config = config.api

    service_map = {
        'groq': api_config.groq_api_key is not None,
        'gemini': api_config.gemini_api_key is not None,
        'pubmed': True,  # PubMed doesn't require API key
        'ncbi': True,    # NCBI has rate limits but no key required
        'chembl': True,  # ChEMBL API is free
        'pubchem': True,  # PubChem PUG REST is free
        'pdb': True,     # PDB is free
        'rag': True,     # Local RAG system
        'langchain': True,  # Optional dependency
        'langgraph': True,  # Optional dependency
    }

    return service_map.get(service_name, False)

def get_service_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all services"""
    services = ['groq', 'gemini', 'pubmed', 'ncbi', 'chembl', 'pubchem', 'pdb', 'rag', 'langchain', 'langgraph']

    return {
        service: {
            'available': is_service_available(service),
            'status': 'ready' if is_service_available(service) else 'unavailable'
        }
        for service in services
    }
