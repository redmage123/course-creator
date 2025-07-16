#!/usr/bin/env python3
"""
Content Storage Service - Refactored with SOLID Principles
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from omegaconf import DictConfig
import hydra
import uvicorn

from config.database import DatabaseManager
from repositories.content_repository import ContentRepository
from repositories.storage_repository import StorageRepository
from services.content_service import ContentService
from services.storage_service import StorageService
from api.content_api import router as content_router
from api.storage_api import router as storage_router

# Global variables for dependency injection
db_manager: DatabaseManager = None
content_service: ContentService = None
storage_service: StorageService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db_manager, content_service, storage_service
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await db_manager.connect()
        await db_manager.create_tables()
        
        # Initialize repositories
        content_repo = ContentRepository(db_manager.pool)
        storage_repo = StorageRepository(db_manager.pool)
        
        # Initialize services
        storage_config = {
            "base_path": app.state.config.storage.path,
            "max_file_size": app.state.config.storage.max_file_size,
            "allowed_extensions": app.state.config.storage.allowed_extensions,
            "backup_enabled": app.state.config.storage.get("backup_enabled", False),
            "backup_path": app.state.config.storage.get("backup_path"),
            "retention_days": app.state.config.storage.get("retention_days", 30)
        }
        
        content_service = ContentService(content_repo, storage_repo, storage_config)
        storage_service = StorageService(storage_repo, storage_config)
        
        logger.info("Content Storage Service initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise
    finally:
        # Cleanup
        if db_manager:
            await db_manager.disconnect()
        logger.info("Content Storage Service shutdown complete")


def create_app(config: DictConfig) -> FastAPI:
    """Create FastAPI application."""
    global db_manager
    
    app = FastAPI(
        title="Content Storage Service",
        description="API for storing and managing course content",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Store config in app state for access in lifespan
    app.state.config = config
    
    # Initialize database manager
    db_manager = DatabaseManager(config)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(content_router, prefix="/api", tags=["content"])
    app.include_router(storage_router, prefix="/api/storage", tags=["storage"])
    
    @app.get("/")
    async def root():
        return {"message": "Content Storage Service", "version": "1.0.0"}
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        try:
            # Check database connection
            if db_manager.pool:
                async with db_manager.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                
                return {
                    "status": "healthy",
                    "database": "connected",
                    "service": "content-storage"
                }
            else:
                return {
                    "status": "unhealthy",
                    "database": "disconnected",
                    "service": "content-storage"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "error",
                "service": "content-storage",
                "error": str(e)
            }
    
    # Global error handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


def setup_dependency_injection():
    """Setup dependency injection for API routes."""
    from api.content_api import get_content_service
    from api.storage_api import get_storage_service
    
    # Override the dependency functions
    def override_content_service():
        return content_service
    
    def override_storage_service():
        return storage_service
    
    # This would be properly implemented with a DI container
    # For now, we'll modify the functions directly
    import api.content_api
    import api.storage_api
    
    api.content_api.get_content_service = override_content_service
    api.storage_api.get_storage_service = override_storage_service


@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=cfg.log.level,
        format=cfg.log.format
    )
    logger = logging.getLogger(__name__)
    
    # Create FastAPI app
    app = create_app(cfg)
    
    # Setup dependency injection
    setup_dependency_injection()
    
    logger.info("Starting Content Storage Service...")
    
    # Run the server
    uvicorn.run(
        app,
        host=cfg.server.host,
        port=cfg.server.port,
        reload=cfg.server.reload,
        log_config=None  # Use our logging configuration
    )


if __name__ == "__main__":
    main()