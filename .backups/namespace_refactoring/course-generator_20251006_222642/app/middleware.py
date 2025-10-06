"""
Middleware setup following Single Responsibility Principle.
"""
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import DictConfig

logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI, config: DictConfig) -> None:
    """Setup all middleware for the application."""
    setup_cors_middleware(app, config)
    setup_logging_middleware(app)
    setup_timing_middleware(app)

def setup_cors_middleware(app: FastAPI, config: DictConfig) -> None:
    """Setup CORS middleware."""
    cors_config = config.get("cors", {})
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_config.get("origins", ["*"]),
        allow_credentials=cors_config.get("credentials", True),
        allow_methods=cors_config.get("methods", ["*"]),
        allow_headers=cors_config.get("headers", ["*"]),
    )

def setup_logging_middleware(app: FastAPI) -> None:
    """Setup request logging middleware."""
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests."""
        start_time = time.time()
        
        logger.info(f"Request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - "
            f"Process time: {process_time:.4f}s"
        )
        
        return response

def setup_timing_middleware(app: FastAPI) -> None:
    """Setup timing header middleware."""
    
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """Add process time header to responses."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response