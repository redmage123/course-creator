"""Configuration manager for course creator services"""

import os
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    database_url: str = "postgresql://user:password@localhost:5432/course_creator"
    redis_url: str = "redis://localhost:6379"
    
    # Service settings
    debug: bool = True
    log_level: str = "INFO"
    
    # API settings
    api_title: str = "Course Creator Service"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ConfigManager:
    """Configuration manager singleton"""
    
    def __init__(self):
        self.settings = Settings()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self.settings, key, default)
    
    def get_database_url(self) -> str:
        """Get database URL"""
        return self.settings.database_url
    
    def get_redis_url(self) -> str:
        """Get Redis URL"""
        return self.settings.redis_url
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.settings.debug
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get service-specific configuration"""
        return {
            "name": service_name,
            "debug": self.settings.debug,
            "log_level": self.settings.log_level,
            "api_title": self.settings.api_title,
            "api_version": self.settings.api_version,
            "database_url": self.settings.database_url,
            "redis_url": self.settings.redis_url,
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "title": self.settings.api_title,
            "version": self.settings.api_version,
            "debug": self.settings.debug,
        }


# Global config manager instance
config_manager = ConfigManager()
