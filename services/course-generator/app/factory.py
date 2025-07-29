"""
Application factory following SOLID principles.
Single Responsibility: Create and configure the FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import DictConfig

from .middleware import setup_middleware
from .routes import setup_routes
from .dependencies import setup_dependencies
from .error_handlers import setup_error_handlers

class ApplicationFactory:
    """Factory for creating FastAPI application instances."""
    
    @staticmethod
    def create_app(config: DictConfig) -> FastAPI:
        """
        Create and configure a FastAPI application.
        
        Args:
            config: Application configuration
            
        Returns:
            Configured FastAPI application
        """
        app = FastAPI(
            title="Course Generator Service",
            description="AI-powered course generation service",
            version="2.0.0",
            docs_url="/docs" if config.app.debug else None,
            redoc_url="/redoc" if config.app.debug else None
        )
        
        # Setup components (Dependency Injection)
        setup_middleware(app, config)
        setup_dependencies(app, config)
        setup_routes(app)
        setup_error_handlers(app)
        
        return app

def setup_cors(app: FastAPI, config: DictConfig) -> None:
    """Setup CORS middleware."""
    allowed_origins = config.get("cors", {}).get("origins", ["*"])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )