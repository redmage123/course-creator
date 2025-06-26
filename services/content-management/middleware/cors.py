"""
Cors middleware for content-management service
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class CorsMiddleware(BaseHTTPMiddleware):
    """Custom cors middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Pre-processing
        logger.info(f"Processing request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Post-processing
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(f"Request processed in {process_time:.4f}s")
        
        return response

# Middleware instance
cors_middleware = CorsMiddleware
