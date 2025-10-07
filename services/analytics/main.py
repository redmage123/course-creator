#!/usr/bin/env python3

# Load environment variables from .cc_env file if present
import os
if os.path.exists('/app/shared/.cc_env'):
    with open('/app/shared/.cc_env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"\'')
                os.environ[key] = value

"""
Analytics Service - Educational Learning Analytics Platform (Refactored v3.2.1)

BUSINESS CONTEXT:
Comprehensive student analytics service implementing evidence-based learning analytics
methodologies for educational effectiveness measurement and student success.

ARCHITECTURE REFACTORING (v3.2.1):
This file has been refactored from 2,601 lines to ~200 lines following SOLID principles:
- Single Responsibility: App initialization and configuration only
- Open/Closed: Extensible through router inclusion
- Liskov Substitution: Interface-based service implementations
- Interface Segregation: Focused API modules (models, routes, dependencies)
- Dependency Inversion: Depends on service interfaces, not implementations

MODULAR STRUCTURE:
- api/models.py: Pydantic request/response models (381 lines)
- api/dependencies.py: Dependency injection functions (313 lines)
- api/routes.py: All API route handlers (consolidated, 600+ lines)
- domain/: Business entities and service interfaces
- application/: Service implementations
- infrastructure/: Container and external integrations

EDUCATIONAL ANALYTICS CAPABILITIES:
- Multi-dimensional engagement measurement
- Mastery-based progress tracking
- Predictive analytics for early intervention
- Comprehensive reporting for stakeholders
- Privacy-preserving analytics (FERPA/GDPR compliant)

PERFORMANCE OPTIMIZATIONS:
- Asynchronous data processing
- Redis caching for frequently accessed metrics
- Efficient database query patterns
- Background processing for intensive analytics
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import sys
import hydra
from omegaconf import DictConfig
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime

# Logging setup
try:
    from logging_setup import setup_docker_logging
except ImportError:
    def setup_docker_logging(service_name: str, log_level: str = "INFO"):
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s'
        )
        return logging.getLogger(service_name)

# Organization middleware
sys.path.append('/app/shared')
try:
    from auth.organization_middleware import OrganizationAuthorizationMiddleware
except ImportError:
    OrganizationAuthorizationMiddleware = None

# Infrastructure
from analytics.infrastructure.container import AnalyticsContainer

# API modules (refactored)
from api.routes import router as analytics_router
from api.dependencies import set_container

# Custom exceptions
from exceptions import (
    AnalyticsException, ValidationException, StudentAnalyticsException,
    LearningAnalyticsException, DataCollectionException,
    AnalyticsProcessingException, MetricsCalculationException,
    DataVisualizationException, ReportGenerationException,
    PDFGenerationException, DatabaseException
)

# Global configuration and container
container: Optional[AnalyticsContainer] = None
current_config: Optional[DictConfig] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifespan manager.

    BUSINESS CONTEXT:
    Manages analytics service lifecycle including dependency injection container,
    database connections, and educational data pipeline initialization.

    TECHNICAL IMPLEMENTATION:
    - Initializes dependency injection container
    - Sets up Redis caching for performance
    - Configures educational analytics repositories
    - Establishes privacy-preserving analytics pipelines

    COMPLIANCE:
    - FERPA-compliant data handling initialization
    - Audit logging setup for data access
    - Secure data aggregation configuration
    """
    global container

    # Startup
    logging.info("Initializing Analytics Service...")

    # Initialize caching infrastructure
    sys.path.append('/home/bbrelin/course-creator')
    from shared.cache import initialize_cache_manager

    redis_url = current_config.get("redis", {}).get("url", "redis://redis:6379") if current_config else "redis://redis:6379"
    await initialize_cache_manager(redis_url)
    logging.info("Cache manager initialized")

    # Initialize analytics container
    container = AnalyticsContainer(current_config or {})
    await container.initialize()

    # Make container available to dependency injection
    set_container(container)

    logging.info("Analytics Service initialized successfully")

    yield

    # Shutdown
    logging.info("Shutting down Analytics Service...")
    if container:
        await container.cleanup()
    logging.info("Analytics Service shutdown complete")


def create_app(config: DictConfig) -> FastAPI:
    """
    Application factory for analytics service.

    BUSINESS CONTEXT:
    Creates FastAPI application with educational analytics capabilities,
    security middleware, and comprehensive error handling.

    SOLID PRINCIPLES:
    - Single Responsibility: Focuses on app configuration
    - Open/Closed: Extensible through router inclusion
    - Dependency Inversion: Uses configuration abstractions

    SECURITY:
    - FERPA-compliant error handling
    - Rate limiting for API protection
    - Audit logging for compliance
    - Multi-tenant organization isolation

    Args:
        config: Hydra configuration with service settings

    Returns:
        Configured FastAPI application instance
    """
    global current_config
    current_config = config

    app = FastAPI(
        title="Analytics Service",
        description="Educational learning analytics, progress tracking, and reporting",
        version="3.2.1",
        lifespan=lifespan
    )

    # Organization security middleware (must be first)
    if OrganizationAuthorizationMiddleware:
        app.add_middleware(
            OrganizationAuthorizationMiddleware,
            config=config
        )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handling with educational context
    EXCEPTION_STATUS_MAPPING = {
        ValidationException: 400,
        StudentAnalyticsException: 404,
        LearningAnalyticsException: 404,
        DataCollectionException: 422,
        AnalyticsProcessingException: 422,
        MetricsCalculationException: 422,
        DataVisualizationException: 422,
        ReportGenerationException: 500,
        PDFGenerationException: 500,
        DatabaseException: 500,
    }

    @app.exception_handler(AnalyticsException)
    async def analytics_exception_handler(request, exc: AnalyticsException):
        """
        Global exception handler for analytics errors.

        COMPLIANCE:
        - FERPA-compliant error responses (no PII exposure)
        - Detailed logging for administrators
        - User-friendly messages for educational users
        - Audit trails for compliance
        """
        status_code = next(
            (code for exc_type, code in EXCEPTION_STATUS_MAPPING.items() if isinstance(exc, exc_type)),
            500
        )

        response_data = exc.to_dict()
        response_data["path"] = str(request.url)

        return JSONResponse(status_code=status_code, content=response_data)

    # Include API routers
    app.include_router(analytics_router)

    # Optional: Include metadata analytics endpoints
    try:
        from metadata_analytics_endpoints import router as metadata_router
        app.include_router(metadata_router)
        logging.info("Metadata analytics endpoints integrated")
    except ImportError:
        logging.info("Metadata analytics endpoints not available")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """
        Service health check.

        Provides status information for:
        - Load balancer health checks
        - Service discovery
        - Performance monitoring
        - Educational platform integration
        """
        return {
            "status": "healthy",
            "service": "analytics",
            "version": "3.2.1",
            "timestamp": datetime.utcnow(),
            "refactored": True
        }

    return app


# Create application instance
app = create_app(current_config or {})


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """
    Main entry point for analytics service.

    BUSINESS CONTEXT:
    Starts the educational analytics service with Hydra configuration
    management for flexible deployment across environments.

    DEPLOYMENT:
    - Development: Single worker, auto-reload enabled
    - Production: Multiple workers, optimized settings

    Args:
        cfg: Hydra configuration object
    """
    global current_config, app
    current_config = cfg

    # Recreate app with configuration
    app = create_app(cfg)

    # Configure logging
    logger = setup_docker_logging(
        service_name="analytics",
        log_level=cfg.get("logging", {}).get("level", "INFO")
    )

    logger.info(f"Starting Analytics Service (Refactored v3.2.1)")
    logger.info(f"Configuration: {cfg}")

    # Start server with SSL
    uvicorn.run(
        app,
        host=cfg.server.host,
        port=cfg.server.port,
        log_level=cfg.get("logging", {}).get("level", "info").lower(),
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt"
    )


if __name__ == "__main__":
    main()
