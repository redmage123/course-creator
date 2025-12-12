#!/usr/bin/env python3
"""
Bug Tracking Service - Main Entry Point

BUSINESS CONTEXT:
FastAPI service providing automated bug tracking with Claude AI integration:
- Bug report submission and management
- Automated analysis using Claude API
- Auto-fix generation and PR creation
- Email notifications

SERVICE PORT: 8017
"""

import logging
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.bug_endpoints import router as bug_router
from data_access.bug_dao import BugDAO
from bug_tracking.application.services.bug_analysis_service import BugAnalysisService
from bug_tracking.application.services.fix_generation_service import FixGenerationService
from bug_tracking.application.services.bug_email_service import BugEmailService
from bug_tracking.application.services.bug_job_processor import BugJobProcessor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://course_user:course_pass@localhost:5433/course_creator"
)
SERVICE_PORT = int(os.environ.get("BUG_TRACKING_PORT", "8017"))
HOST = os.environ.get("BUG_TRACKING_HOST", "0.0.0.0")

# Global service instances
bug_dao: Optional[BugDAO] = None
analysis_service: Optional[BugAnalysisService] = None
fix_service: Optional[FixGenerationService] = None
email_service: Optional[BugEmailService] = None
job_processor: Optional[BugJobProcessor] = None
job_processor_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles:
    - Database connection pool creation
    - Service initialization
    - Background job processor startup
    - Graceful shutdown
    """
    global bug_dao, analysis_service, fix_service, email_service
    global job_processor, job_processor_task

    logger.info("Starting Bug Tracking Service...")

    try:
        # Initialize database connection
        bug_dao = BugDAO(DATABASE_URL)
        await bug_dao.connect()
        logger.info("Database connection established")

        # Initialize services
        analysis_service = BugAnalysisService()
        fix_service = FixGenerationService()
        email_service = BugEmailService(
            mock_mode=os.environ.get("EMAIL_MOCK_MODE", "true").lower() == "true"
        )

        # Initialize job processor
        job_processor = BugJobProcessor(
            bug_dao=bug_dao,
            analysis_service=analysis_service,
            fix_service=fix_service,
            email_service=email_service
        )

        # Start job processor in background
        job_processor_task = asyncio.create_task(job_processor.start())
        logger.info("Job processor started")

        logger.info(f"Bug Tracking Service ready on port {SERVICE_PORT}")

        yield

    finally:
        logger.info("Shutting down Bug Tracking Service...")

        # Stop job processor
        if job_processor:
            await job_processor.stop()
        if job_processor_task:
            job_processor_task.cancel()
            try:
                await job_processor_task
            except asyncio.CancelledError:
                pass

        # Close database connection
        if bug_dao:
            await bug_dao.disconnect()

        logger.info("Bug Tracking Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Bug Tracking Service",
    description="""
    Automated bug tracking service with Claude AI integration.

    ## Features

    - **Bug Submission**: Submit bug reports via API or web form
    - **Automated Analysis**: Claude AI analyzes bugs and identifies root causes
    - **Auto-Fix Generation**: Generates fixes for high-confidence bugs
    - **PR Creation**: Automatically creates pull requests for fixes
    - **Email Notifications**: Sends analysis results to submitters

    ## Endpoints

    - `POST /bugs` - Submit a new bug report
    - `GET /bugs/{bug_id}` - Get bug status and analysis
    - `GET /bugs` - List all bugs
    - `GET /bugs/my/reports` - List user's submitted bugs
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:3000",
        "https://176.9.99.103:3000",
        "https://coursecreator.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bug_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Service health status
    """
    db_healthy = bug_dao is not None and bug_dao.pool is not None
    processor_status = job_processor.get_status() if job_processor else {}

    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": "bug-tracking",
        "version": "1.0.0",
        "database": "connected" if db_healthy else "disconnected",
        "job_processor": processor_status
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Bug Tracking Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    # Get SSL paths from environment variables or use defaults
    # Using SERVICE_SSL_* to avoid conflicting with Python's SSL_CERT_FILE for CA verification
    ssl_keyfile = os.environ.get("SERVICE_SSL_KEY", "/app/ssl/nginx-selfsigned.key")
    ssl_certfile = os.environ.get("SERVICE_SSL_CERT", "/app/ssl/nginx-selfsigned.crt")

    uvicorn.run(
        "main:app",
        host=HOST,
        port=SERVICE_PORT,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        reload=False,
        log_level="info"
    )
