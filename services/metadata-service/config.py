"""
Configuration for Metadata Service

BUSINESS REQUIREMENT:
Centralized configuration management with environment-based settings.

DESIGN PATTERN:
Environment-based configuration with sensible defaults
"""

import os
from typing import Optional


class Config:
    """
    Application configuration

    CONFIGURATION SOURCES:
    1. Environment variables (highest priority)
    2. Default values (fallback)
    """

    # Service configuration
    SERVICE_NAME: str = "metadata-service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8011"))

    # Database configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5433"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres_password")
    DB_NAME: str = os.getenv("DB_NAME", "course_creator")

    # Connection pool configuration
    DB_POOL_MIN_SIZE: int = int(os.getenv("DB_POOL_MIN_SIZE", "2"))
    DB_POOL_MAX_SIZE: int = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
    DB_COMMAND_TIMEOUT: int = int(os.getenv("DB_COMMAND_TIMEOUT", "60"))

    # SSL configuration
    SSL_ENABLED: bool = os.getenv("SSL_ENABLED", "false").lower() == "true"
    SSL_KEY_FILE: Optional[str] = os.getenv("SSL_KEY_FILE")
    SSL_CERT_FILE: Optional[str] = os.getenv("SSL_CERT_FILE")

    # CORS configuration
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Service-specific configuration
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "100"))
    MAX_BULK_CREATE_SIZE: int = int(os.getenv("MAX_BULK_CREATE_SIZE", "1000"))
    AUTO_TAG_EXTRACTION: bool = os.getenv("AUTO_TAG_EXTRACTION", "true").lower() == "true"

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.ENVIRONMENT == "development"

    @classmethod
    def get_database_url(cls) -> str:
        """Get PostgreSQL database URL"""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"


# Singleton instance
config = Config()
