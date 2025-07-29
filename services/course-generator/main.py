"""
Course Generator Service - Refactored following SOLID principles.

Single Responsibility: Entry point for the service.
Open/Closed: Extensible through dependency injection.
Liskov Substitution: Uses abstract interfaces.
Interface Segregation: Clean, focused interfaces.
Dependency Inversion: Depends on abstractions, not concretions.
"""
import logging
import sys
from pathlib import Path

import hydra
import uvicorn
from omegaconf import DictConfig

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.factory import ApplicationFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    logger.info("Starting Course Generator Service")
    logger.info(f"Configuration: {config}")
    
    try:
        # Create application using factory pattern
        app = ApplicationFactory.create_app(config)
        
        # Start server
        uvicorn.run(
            app,
            host=config.app.host,
            port=config.app.port,
            log_level=config.app.get('log_level', 'info').lower(),
            reload=config.app.get('debug', False)
        )
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise

if __name__ == "__main__":
    main()