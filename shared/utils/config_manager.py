"""Configuration management using Hydra."""

from hydra import compose, initialize_config_dir
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import os

class ConfigManager:
    """Centralized configuration management using Hydra"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        """Load configuration using Hydra"""
        config_dir = Path(__file__).parent.parent.parent / "config"

        with initialize_config_dir(config_dir=str(config_dir.absolute()), version_base=None):
            self._config = compose(config_name="config")

    @property
    def config(self) -> DictConfig:
        """Get the configuration object"""
        return self._config

    def get_service_config(self, service_name: str) -> DictConfig:
        """Get configuration for a specific service"""
        return self._config.services.get(service_name, {})

# Initialize global config manager
config_manager = ConfigManager()
