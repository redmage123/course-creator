"""
Course Generator Service - Refactored following SOLID principles.

Single Responsibility: Entry point for the service.
Open/Closed: Extensible through dependency injection.
Liskov Substitution: Uses abstract interfaces.
Interface Segregation: Clean, focused interfaces.
Dependency Inversion: Depends on abstractions, not concretions.
"""
import logging
import os
# Removed unused imports: sys, Path

import hydra
import uvicorn
from omegaconf import DictConfig

from app.factory import ApplicationFactory

try:
    from logging_setup import setup_docker_logging
except ImportError:
    # Fallback if config module not available
    def setup_docker_logging(service_name: str, log_level: str = "INFO"):
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s'
        )
        return logging.getLogger(service_name)

# Will be configured via setup_docker_logging in main()
logger = logging.getLogger(__name__)

# Default configuration for when not using Hydra
_default_config = {
    'app': {
        'host': '0.0.0.0',
        'port': 8001,
        'debug': True
    }
}

def create_app_instance(config_dict: dict = None):
    """Create FastAPI app instance with provided config"""
    if config_dict is None:
        config_dict = _default_config

    # Convert dict to DictConfig for ApplicationFactory
    from omegaconf import OmegaConf
    config = OmegaConf.create(config_dict)

    return ApplicationFactory.create_app(config)

# Create app instance for uvicorn to find
app = create_app_instance()

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(config: DictConfig) -> None:
    """
    Main entry point for the Course Generator Service.
    
    Args:
        config: Hydra configuration
    """
    # Setup centralized logging with syslog format
    service_name = os.environ.get('SERVICE_NAME', 'course-generator')
    log_level = os.environ.get('LOG_LEVEL', getattr(config, 'log', {}).get('level', 'INFO'))

    service_logger = setup_docker_logging(service_name, log_level)
    service_logger.info("Starting Course Generator Service")
    service_logger.info("Configuration: %s", config)

    try:
        # Create application using factory pattern
        course_app = ApplicationFactory.create_app(config)
        # Start server with reduced uvicorn logging to avoid duplicates
        uvicorn.run(
            course_app,
            host=getattr(config, 'service', {}).get('host', '0.0.0.0'),
            port=getattr(config, 'service', {}).get('port', 8001),
            log_level="warning",  # Reduce uvicorn log level since we have our own logging
            access_log=False,     # Disable uvicorn access log since we log via middleware
            reload=getattr(config, 'service', {}).get('debug', False)
        )

    except Exception as e:
        service_logger.error("Failed to start service: %s", e)
        raise from e

if __name__ == "__main__":
    main()