"""
Error handling setup following Single Responsibility Principle.
"""
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Custom exceptions - ABSOLUTE IMPORTS ONLY
import sys
from pathlib import Path

# Import shared exceptions from platform-wide exception hierarchy
import sys
from exceptions import (
    CourseCreatorBaseException,
    ContentException,
    ContentNotFoundException,
    ContentValidationException,
    FileStorageException,
    ValidationException,
    DatabaseException,
    AuthenticationException,
    AuthorizationException,
    ConfigurationException,
    APIException,
    BusinessRuleException
)

logger = logging.getLogger(__name__)

def setup_error_handlers(app: FastAPI) -> None:
    """Setup global error handlers."""
    
    # Exception type to HTTP status code mapping (Open/Closed Principle)
    EXCEPTION_STATUS_MAPPING = {
        ValidationException: 400,
        ConfigurationException: 500,
        FileStorageException: 422,
        ContentException: 500,
        APIException: 503,
        DatabaseException: 500,
        ContentValidationException: 422,
        BusinessRuleException: 500,
    }
    
    @app.exception_handler(CourseCreatorBaseException)
    async def course_generator_exception_handler(request: Request, exc: CourseCreatorBaseException):
        """Handle custom course generator exceptions."""
        # Use mapping to determine status code (extensible design)
        status_code = next(
            (code for exc_type, code in EXCEPTION_STATUS_MAPPING.items() if isinstance(exc, exc_type)),
            500  # Default status code
        )
            
        response_data = exc.to_dict()
        response_data["path"] = str(request.url)
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url)
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions."""
        logger.warning(f"Starlette HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "details": exc.errors(),
                "status_code": 422,
                "path": str(request.url)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "status_code": 500,
                "path": str(request.url)
            }
        )