"""
Middleware setup following SOLID principles.
Single Responsibility: Configure middleware components.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import DictConfig
import logging
import time

def setup_cors_middleware(app: FastAPI, config: DictConfig) -> None:
    """Setup CORS middleware"""
    allowed_origins = getattr(config, 'cors', {}).get('origins', ["*"])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_logging_middleware(app: FastAPI, config: DictConfig) -> None:
    """Setup logging middleware"""
    
    @app.middleware("http")
    async def log_requests(request, call_next):
        """Log HTTP requests and responses"""
        start_time = time.time()
        
        # Log request
        logging.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logging.info(
            f"Response: {response.status_code} - "
            f"Time: {process_time:.4f}s - "
            f"Path: {request.url.path}"
        )
        
        return response