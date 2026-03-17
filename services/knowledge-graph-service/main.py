"""
Knowledge Graph Service - Main Application Entry Point

BUSINESS REQUIREMENT:
Provide a standalone microservice for knowledge graph operations
supporting course relationships, prerequisites, and learning paths.

BUSINESS VALUE:
- Enables intelligent course discovery
- Powers prerequisite validation
- Generates optimal learning paths
- Supports curriculum visualization

TECHNICAL IMPLEMENTATION:
- FastAPI application with async support
- CORS configuration for frontend access
- Health check endpoints
- OpenAPI documentation
- Graceful shutdown handling

SERVICE INFORMATION:
- Port: 8012
- Base Path: /api/v1/graph
- Database: PostgreSQL (shared with other services)
- Technology: FastAPI + asyncpg + Python 3.9+

WHY:
Centralized knowledge graph service provides a single source of truth
for course relationships and learning path generation across the platform.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api.graph_endpoints import router as graph_router
from api.path_endpoints import router as path_router
from knowledge_graph_service.infrastructure.database import (
    get_database_pool,
    close_database_pool,
    check_database_health
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# ========================================
# LIFESPAN MANAGEMENT
# ========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management

    BUSINESS LOGIC:
    Initialize database pool on startup, close on shutdown
    """
    # Startup
    logger.info("Starting Knowledge Graph Service...")

    try:
        # Initialize database pool
        pool = await get_database_pool()
        logger.info("Database connection pool initialized")

        # Check database health
        is_healthy = await check_database_health()
        if is_healthy:
            logger.info("Database health check: PASSED")
        else:
            logger.warning("Database health check: FAILED")

        logger.info("Knowledge Graph Service started successfully")

        yield  # Application runs here

    finally:
        # Shutdown
        logger.info("Shutting down Knowledge Graph Service...")

        try:
            await close_database_pool()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")

        logger.info("Knowledge Graph Service shutdown complete")


# ========================================
# APPLICATION SETUP
# ========================================

app = FastAPI(
    title="Knowledge Graph Service",
    description="""
    ## Knowledge Graph API for Course Relationships and Learning Paths

    This service provides graph-based course relationship management including:

    ### Core Features
    - **Graph Management**: Create and manage nodes (courses, concepts, skills) and edges (relationships)
    - **Learning Paths**: Find optimal learning sequences between courses
    - **Prerequisites**: Validate course prerequisites and student readiness
    - **Recommendations**: Suggest next courses and skill progression paths
    - **Visualization**: Provide graph data for frontend visualization

    ### Node Types
    - `course`: Course entities
    - `topic`: High-level topics
    - `concept`: Specific concepts taught
    - `skill`: Skills developed
    - `learning_outcome`: Learning outcomes achieved
    - `resource`: Additional resources

    ### Edge Types
    - `prerequisite_of`: Course A is prerequisite for Course B
    - `teaches`: Course teaches a concept
    - `builds_on`: Concept builds on another concept
    - `develops`: Course develops a skill
    - `achieves`: Course achieves learning outcome
    - `relates_to`: General relationship
    - `similar_to`: Similar content
    - `alternative_to`: Alternative prerequisite
    - And more...

    ### Business Value
    - Reduces course dropout by ensuring proper prerequisites
    - Improves learning outcomes through optimal path planning
    - Increases student engagement via personalized recommendations
    - Enables data-driven curriculum design
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/v1/graph/docs",
    redoc_url="/api/v1/graph/redoc",
    openapi_url="/api/v1/graph/openapi.json"
)

# ========================================
# MIDDLEWARE
# ========================================

# CORS middleware - Security: Use environment-configured origins
# Never use wildcard (*) in production - enables CSRF attacks
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://localhost:3000,https://localhost:3001').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests

    BUSINESS VALUE:
    Provides audit trail and debugging information
    """
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    response = await call_next(request)

    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"status={response.status_code}"
    )

    return response


# ========================================
# EXCEPTION HANDLERS
# ========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler

    BUSINESS LOGIC:
    Catch all unhandled exceptions and return structured error response
    """
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {exc}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": str(request.url.path)
        }
    )


# ========================================
# ROUTERS
# ========================================

# Include API routers
app.include_router(graph_router, prefix="/api/v1")
app.include_router(path_router, prefix="/api/v1")


# ========================================
# HEALTH CHECK ENDPOINTS
# ========================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check

    BUSINESS USE CASE:
    Used by orchestration tools and monitoring systems
    """
    return {
        "status": "healthy",
        "service": "knowledge-graph-service",
        "version": "1.0.0"
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check (includes database connectivity)

    BUSINESS USE CASE:
    Kubernetes/Docker readiness probe
    """
    is_db_healthy = await check_database_health()

    if is_db_healthy:
        return {
            "status": "ready",
            "service": "knowledge-graph-service",
            "database": "connected"
        }
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "knowledge-graph-service",
                "database": "disconnected"
            }
        )


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint

    BUSINESS USE CASE:
    Provides service information and documentation links
    """
    return {
        "service": "Knowledge Graph Service",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/api/v1/graph/docs",
        "endpoints": {
            "graph_operations": "/api/v1/graph",
            "learning_paths": "/api/v1/paths",
            "health": "/health",
            "readiness": "/health/ready"
        },
        "description": "Graph-based course relationship and learning path service"
    }


# ========================================
# STARTUP MESSAGE
# ========================================

@app.on_event("startup")
async def startup_message():
    """
    Display startup message

    WHY:
    Provides clear indication that service is running
    """
    logger.info("=" * 80)
    logger.info("  KNOWLEDGE GRAPH SERVICE")
    logger.info("=" * 80)
    logger.info("  Port: 8012")
    logger.info("  Documentation: http://localhost:8012/api/v1/graph/docs")
    logger.info("  Health Check: http://localhost:8012/health")
    logger.info("=" * 80)


# ========================================
# MAIN ENTRY POINT
# ========================================

if __name__ == "__main__":
    """
    Run service directly (for development)

    PRODUCTION:
    Use: uvicorn main:app --host 0.0.0.0 --port 8012
    """
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8012,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info",
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt"
    )
