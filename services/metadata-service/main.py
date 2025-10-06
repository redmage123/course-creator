"""
Metadata Service - FastAPI Application

BUSINESS REQUIREMENT:
REST API microservice for unified metadata management across the platform.
Provides CRUD operations, search, enrichment, and bulk operations for entity metadata.

DESIGN PATTERN:
FastAPI application with dependency injection, async operations,
and proper lifecycle management.

SERVICE INFORMATION:
- Port: 8011
- Base URL: /api/v1/metadata
- Health: /health
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add service directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.metadata_endpoints import router as metadata_router
from metadata_service.infrastructure.database import get_database_pool, close_database_pool


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager

    LIFECYCLE:
    - Startup: Initialize database connection pool
    - Shutdown: Close database connections gracefully
    """
    # Startup
    logger.info("Starting Metadata Service...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Database: {os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5433')}")

    try:
        # Initialize database pool
        pool = await get_database_pool()
        logger.info(f"Database connection pool created (min=2, max=10)")

        # Test database connection
        async with pool.acquire() as conn:
            version = await conn.fetchval('SELECT version()')
            logger.info(f"Database connected: {version[:50]}...")

    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    logger.info("Metadata Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Metadata Service...")

    try:
        await close_database_pool()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database pool: {e}")

    logger.info("Metadata Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Metadata Service",
    description="Unified metadata management for Course Creator Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(metadata_router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - Service information

    Returns:
        Service metadata and links
    """
    return {
        "service": "metadata-service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "api": {
            "base": "/api/v1/metadata",
            "endpoints": [
                "POST   /api/v1/metadata - Create metadata",
                "GET    /api/v1/metadata/{id} - Get metadata by ID",
                "GET    /api/v1/metadata/entity/{entity_id} - Get by entity",
                "GET    /api/v1/metadata/type/{entity_type} - List by type",
                "PUT    /api/v1/metadata/{id} - Update metadata",
                "DELETE /api/v1/metadata/{id} - Delete metadata",
                "POST   /api/v1/metadata/search - Search metadata",
                "GET    /api/v1/metadata/tags/{tags} - Get by tags",
                "POST   /api/v1/metadata/bulk - Bulk create",
                "POST   /api/v1/metadata/{id}/enrich - Enrich metadata"
            ]
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors

    LOGGING:
    Logs all unhandled exceptions for debugging

    Args:
        request: Request object
        exc: Exception

    Returns:
        500 error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8011"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    logger.info(f"Starting uvicorn server on {host}:{port}")

    # Run application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        ssl_keyfile=os.getenv("SSL_KEY_FILE"),
        ssl_certfile=os.getenv("SSL_CERT_FILE")
    )
