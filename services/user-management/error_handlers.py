"""
Error handlers following SOLID principles.
Single Responsibility: Handle exceptions and convert to HTTP responses.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

# Custom exceptions
from exceptions import (
    UserManagementException,
    UserNotFoundException,
    UserValidationException,
    AuthenticationException,
    AuthorizationException,
    SessionException,
    JWTException,
    DatabaseException,
    EmailServiceException
)

def setup_exception_handlers(app: FastAPI) -> None:
    """Setup custom exception handlers"""
    
    # Exception type to HTTP status code mapping (Open/Closed Principle)
    EXCEPTION_STATUS_MAPPING = {
        AuthenticationException: 401,
        AuthorizationException: 403,
        UserNotFoundException: 404,
        UserValidationException: 400,
        SessionException: 401,
        JWTException: 401,
        DatabaseException: 500,
        EmailServiceException: 500,
    }
    
    @app.exception_handler(UserManagementException)
    async def user_management_exception_handler(request, exc: UserManagementException):
        """Handle custom user management exceptions"""
        # Use mapping to determine status code (extensible design)
        status_code = next(
            (code for exc_type, code in EXCEPTION_STATUS_MAPPING.items() if isinstance(exc, exc_type)),
            500  # Default status code
        )
            
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """Handle unexpected exceptions"""
        logging.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        )