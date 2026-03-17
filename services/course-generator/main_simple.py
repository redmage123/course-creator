"""
Simplified Course Generator Service Entry Point

This is a simplified version of main.py that doesn't require hydra configuration.
"""
import logging
import os
import uvicorn
from omegaconf import DictConfig, OmegaConf

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_minimal_config() -> DictConfig:
    """Create a minimal configuration for the service."""
    config_dict = {
        'service': {
            'debug': True,
            'host': '0.0.0.0',
            'port': 8002,
            'workers': 1
        },
        'database': {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': 5432,
            'name': os.getenv('DB_NAME', 'course_creator'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        },
        'ai': {
            'provider': 'anthropic',
            'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
            'model': 'claude-3-haiku-20240307'
        }
    }
    return OmegaConf.create(config_dict)

def main():
    """Main entry point for the simplified course generator service."""
    try:
        logger.info("Starting Course Generator Service (Simplified)")
        
        # Create minimal configuration
        config = create_minimal_config()
        
        # Import and create application
        from app.factory import ApplicationFactory
        app = ApplicationFactory.create_app(config)
        
        # Start the service
        uvicorn.run(
            app,
            host=config.service.host,
            port=config.service.port,
            workers=config.service.workers,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Failed to start Course Generator Service: {e}")
        raise

if __name__ == "__main__":
    main()