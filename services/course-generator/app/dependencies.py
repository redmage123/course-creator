"""
Simplified dependency injection setup for course generator service.
"""
from fastapi import FastAPI
from omegaconf import DictConfig

class DependencyContainer:
    """Simplified container for managing service dependencies."""
    
    def __init__(self, config: DictConfig):
        self.config = config
        self._services = {}
        self._repositories = {}
        self._db_factory = None

# Global container instance
_container: DependencyContainer = None

def setup_dependencies(app: FastAPI, config: DictConfig) -> None:
    """Setup dependency injection container."""
    global _container
    _container = DependencyContainer(config)
    
    # Store container in app state for access in routes
    app.state.container = _container

def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    if not _container:
        raise RuntimeError("Dependencies not initialized")
    return _container