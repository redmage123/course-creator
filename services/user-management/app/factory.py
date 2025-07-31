"""
User Management Service Application Factory.
Single Responsibility: Create and configure the FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import DictConfig

from .middleware import setup_middleware
from .routes import setup_routes
from .dependencies import setup_dependencies
from .error_handlers import setup_error_handlers

class UserManagementApplicationFactory:
    """Factory for creating User Management FastAPI application instances."""
    
    @staticmethod
    def create_app(config: DictConfig) -> FastAPI:
        """
        Create and configure a FastAPI application for user management.
        
        Args:
            config: Application configuration
            
        Returns:
            Configured FastAPI application
        """
        app = FastAPI(
            title="User Management Service",
            description="Authentication and user management service",
            version="2.0.0",
            docs_url="/docs" if getattr(config, 'service', {}).get('debug', False) else None,
            redoc_url="/redoc" if getattr(config, 'service', {}).get('debug', False) else None
        )
        
        # Setup components following dependency injection pattern
        setup_middleware(app, config)
        setup_dependencies(app, config)
        setup_routes(app)
        setup_error_handlers(app)
        
        return app