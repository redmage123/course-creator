#!/usr/bin/env python3

"""
NIMCP Service - Main Entry Point

This module serves as the primary entry point for the NIMCP (Neural Inference
for Massive Concurrent Processing) Service, which provides the neuromorphic AI
brain system for the Course Creator Platform's self-aware learning capabilities.

Business Context:
    The NIMCP Service implements the platform's "brain" - a hierarchical system
    of continuously learning neural networks that become more intelligent with
    every interaction. The service manages:
    - Platform Brain: Master orchestrator that controls the entire application
    - Student Brains: Personal learning guides (one per student, COW clones)
    - Instructor Brains: Teaching strategy optimization assistants
    - Continuous learning from every interaction with neural weight adjustment
    - Smart routing between neural inference (fast, free) and LLM (slow, costly)

Architectural Principles:
    - Clean Architecture: Domain -> Application -> Infrastructure -> API
    - Dependency Injection: Services receive dependencies via constructor
    - Async/Await: Non-blocking I/O for high concurrency
    - Microservice Pattern: Self-contained service with REST API
    - Database Per Service: Dedicated PostgreSQL schema for brain persistence

Service Responsibilities:
    - Brain lifecycle management (create, load, save, delete)
    - Neural inference with confidence-based LLM fallback
    - Continuous learning (supervised and reinforcement)
    - Performance metrics tracking (neural rate, accuracy, cost savings)
    - Meta-cognitive self-awareness (bias detection, capability assessment)
    - COW clone management for memory-efficient student brains

Technical Stack:
    - FastAPI: High-performance async web framework
    - asyncpg: Async PostgreSQL driver
    - NIMCP: Neuromorphic AI library (C + Python bindings)
    - PostgreSQL: Brain metadata and interaction history
    - Filesystem: Binary neural state (.bin files)

Port: 8016
Health Endpoint: /health
API Documentation: /docs (Swagger UI)
API Documentation: /redoc (ReDoc)

Author: Course Creator Platform Team
Version: 1.0.0
Last Updated: 2025-11-09
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add service directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api.brain_endpoints import router as brain_router, set_brain_service
from nimcp_service.application.services.brain_service import BrainService
from data_access.brain_dao import BrainDAO


# ============================================================================
# Configuration
# ============================================================================

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres_password@postgres:5432/course_creator")
BRAIN_STATES_DIR = os.getenv("BRAIN_STATES_DIR", "/app/brain_states")
PERSISTENCE_INTERVAL = int(os.getenv("BRAIN_PERSISTENCE_INTERVAL", "100"))
CONFIDENCE_THRESHOLD = float(os.getenv("BRAIN_CONFIDENCE_THRESHOLD", "0.85"))
SERVICE_PORT = int(os.getenv("NIMCP_SERVICE_PORT", "8016"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Logging configuration
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("nimcp_service")


# ============================================================================
# Application Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle (startup and shutdown).

    Business Logic:
        - Startup: Initialize database connection pool, create platform brain if needed
        - Shutdown: Clean up resources, close database connections

    This uses FastAPI's lifespan context manager pattern for proper
    resource management.
    """
    logger.info("=" * 80)
    logger.info("NIMCP Service Starting Up")
    logger.info("=" * 80)

    # Initialize database connection pool
    logger.info(f"Connecting to database: {DATABASE_URL.split('@')[-1]}")  # Hide credentials in logs
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("✓ Database connection pool created")
    except Exception as e:
        logger.error(f"✗ Failed to create database pool: {e}")
        raise

    # Initialize repository and service
    logger.info("Initializing brain service...")
    try:
        brain_dao = BrainDAO(db_pool)
        brain_service = BrainService(
            repository=brain_dao,
            brain_states_dir=BRAIN_STATES_DIR,
            persistence_interval=PERSISTENCE_INTERVAL,
            confidence_threshold=CONFIDENCE_THRESHOLD,
            llm_client=None  # TODO: Inject LLM client once AI pipeline integration is ready
        )
        set_brain_service(brain_service)
        logger.info("✓ Brain service initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize brain service: {e}")
        await db_pool.close()
        raise

    # Create brain states directory if it doesn't exist
    Path(BRAIN_STATES_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ Brain states directory: {BRAIN_STATES_DIR}")

    # Check if platform brain exists, create if needed
    try:
        platform_brain = await brain_service.get_platform_brain()
        logger.info(f"✓ Platform brain loaded: {platform_brain.brain_id}")
        logger.info(f"  - Interactions: {platform_brain.performance.total_interactions}")
        logger.info(f"  - Neural rate: {platform_brain.performance.neural_inference_rate:.1f}%")
        logger.info(f"  - Accuracy: {platform_brain.performance.average_accuracy:.2f}")
    except Exception:
        logger.info("Platform brain not found, creating new one...")
        try:
            platform_brain = await brain_service.create_platform_brain(
                neuron_count=50000,
                enable_ethics=True,
                enable_curiosity=True
            )
            logger.info(f"✓ Platform brain created: {platform_brain.brain_id}")
            logger.info(f"  - Neuron count: 50,000")
            logger.info(f"  - Ethics engine: Enabled")
            logger.info(f"  - Curiosity system: Enabled")
        except Exception as e:
            logger.warning(f"Could not create platform brain: {e}")
            # Don't fail startup - brain can be created later via API

    logger.info("=" * 80)
    logger.info("NIMCP Service Ready")
    logger.info(f"Listening on port {SERVICE_PORT}")
    logger.info(f"API Documentation: http://localhost:{SERVICE_PORT}/docs")
    logger.info("=" * 80)

    # Store pool in app state for access in endpoints
    app.state.db_pool = db_pool
    app.state.brain_service = brain_service

    # Application is running (yield control to FastAPI)
    yield

    # Shutdown: Clean up resources
    logger.info("=" * 80)
    logger.info("NIMCP Service Shutting Down")
    logger.info("=" * 80)

    logger.info("Closing database connection pool...")
    await db_pool.close()
    logger.info("✓ Database pool closed")

    logger.info("=" * 80)
    logger.info("NIMCP Service Stopped")
    logger.info("=" * 80)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="NIMCP Service",
    description="""
    Neuromorphic AI Brain System for Course Creator Platform

    This service provides the platform's self-aware learning brain:
    - Platform Brain: Master orchestrator controlling the entire application
    - Student Brains: Personal learning guides (COW clones for memory efficiency)
    - Instructor Brains: Teaching strategy optimization assistants

    Key Features:
    - Continuous learning from every interaction (neural weight adjustment)
    - Smart routing: Neural inference (fast, free) vs LLM fallback (slow, costly)
    - Meta-cognitive self-awareness (bias detection, capability assessment)
    - Cost optimization: 90% LLM cost reduction after 6 months of learning

    The brain becomes more intelligent with every student interaction.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

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

# Include brain endpoints
app.include_router(brain_router)


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for container orchestration.

    Returns:
        200 OK: Service is healthy
        503 Service Unavailable: Service is unhealthy

    Example:
        GET /health
        Response: {"status": "healthy", "service": "nimcp_service", "version": "1.0.0"}
    """
    try:
        # Check database connection
        if not hasattr(app.state, "db_pool"):
            raise Exception("Database pool not initialized")

        async with app.state.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        # Check brain service
        if not hasattr(app.state, "brain_service"):
            raise Exception("Brain service not initialized")

        # Check brain states directory
        if not Path(BRAIN_STATES_DIR).exists():
            raise Exception("Brain states directory not accessible")

        return {
            "status": "healthy",
            "service": "nimcp_service",
            "version": "1.0.0",
            "brain_states_dir": BRAIN_STATES_DIR,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "persistence_interval": PERSISTENCE_INTERVAL
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "nimcp_service",
                "error": str(e)
            }
        )


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint providing service information.

    Example:
        GET /
    """
    return {
        "service": "NIMCP Service",
        "version": "1.0.0",
        "description": "Neuromorphic AI Brain System for Course Creator Platform",
        "documentation": "/docs",
        "health": "/health",
        "api": "/api/v1/brains"
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting NIMCP Service via uvicorn...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=False,  # Disable reload in production
        log_level=LOG_LEVEL.lower(),
        access_log=True
    )
