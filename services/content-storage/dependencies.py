"""
Content Storage Service Dependencies Module

This module provides FastAPI dependency injection components for the content storage service,
centralizing database session management, authentication, HTTP client creation, and common
service dependencies.

Business Context:
-----------------
The content storage service needs consistent access to:
- PostgreSQL database sessions for content CRUD operations
- Authentication tokens for user identity verification
- HTTP clients for inter-service communication (user service, notifications)
- Configuration settings and logging infrastructure
- Request context (request IDs for distributed tracing)

Technical Implementation:
------------------------
Uses FastAPI's dependency injection system to provide reusable components that can be
injected into API route handlers. This ensures consistent error handling, proper resource
cleanup (database connections), and centralized configuration management.

Key Features:
- Context manager for database session lifecycle
- OAuth2 bearer token authentication with JWT verification
- HTTP client factories with SSL configuration for development
- Centralized error handling and logging
- Combined dependency class for common use cases

Dependencies:
- FastAPI: Web framework and dependency injection
- SQLAlchemy: Database ORM and session management
- Hydra: Configuration management from YAML files
- httpx: Async HTTP client for service-to-service communication
- Custom exceptions for domain-specific error handling
"""
from contextlib import contextmanager
from typing import Generator, Any
import logging
from logging.config import dictConfig
import httpx

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import hydra
from omegaconf import DictConfig

from db.session import SessionLocal
from core.config import Settings
from core.logging_config import LOGGING_CONFIG
from core.security import verify_token
from schemas.auth import TokenData
from exceptions import (
    ContentStorageException,
    AuthenticationException
)

# Initialize logging
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Initialize Hydra config
@hydra.main(config_path="../config", config_name="config")
def get_config(cfg: DictConfig) -> Settings:
    """
    Load application settings from Hydra configuration files.

    Hydra allows configuration management from YAML files with environment-specific overrides.
    This function is decorated to automatically load and merge configuration from the
    ../config directory, using config.yaml as the base configuration.

    Args:
        cfg: Hydra DictConfig object containing merged configuration from YAML files

    Returns:
        Settings: Pydantic Settings object with validated configuration values

    Business Context:
        Configuration management is critical for multi-environment deployments
        (dev, staging, production) with different database URLs, service endpoints,
        and feature flags.
    """
    return Settings(**cfg)

settings = get_config()

# Database dependency
@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database session lifecycle management.

    Creates a new SQLAlchemy session, yields it for database operations, and ensures
    proper cleanup (session close) even if exceptions occur during database operations.

    Yields:
        Session: SQLAlchemy database session for executing queries

    Business Context:
        Proper database session management prevents connection leaks and ensures
        transactions are properly committed or rolled back. Critical for service
        stability under high load.

    Usage:
        with get_db() as db:
            # Perform database operations
            result = db.query(Content).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session(request: Request) -> Session:
    """
    FastAPI dependency to extract database session from request state.

    Assumes a database session has been attached to the request by middleware.
    This pattern allows a single database session to be used across an entire
    request lifecycle.

    Args:
        request: FastAPI request object with database session in state

    Returns:
        Session: SQLAlchemy database session attached to the request

    Business Context:
        Request-scoped database sessions ensure consistent data views within a
        single API request and automatic rollback on request failures.
    """
    return request.state.db

# Auth dependencies
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    FastAPI dependency to extract and validate current authenticated user from JWT token.

    Extracts the bearer token from the Authorization header, verifies its signature and
    expiration, and returns the token payload containing user identity information.

    Args:
        token: JWT bearer token from Authorization header (injected by oauth2_scheme)

    Returns:
        TokenData: Validated token payload containing user_id, username, and roles

    Raises:
        HTTPException: 401 status if token is invalid, expired, or missing
        AuthenticationException: Domain exception wrapping token verification failures

    Business Context:
        JWT-based authentication allows stateless user identity verification across
        microservices without central session storage. Each service can independently
        verify user identity using a shared secret key.

    Security:
        - Token signature verification prevents token tampering
        - Expiration checking prevents replay of stolen tokens
        - Role-based claims enable authorization decisions
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = verify_token(token)
        if token_data is None:
            raise credentials_exception
        return token_data
    except HTTPException:
        raise
    except Exception as e:
        raise AuthenticationException(
            message=f"Token verification failed: Unable to validate authentication credentials",
            auth_method="bearer_token",
            original_exception=e
        )

# HTTP client dependencies
async def get_user_service_client() -> httpx.AsyncClient:
    """
    FastAPI dependency to create async HTTP client for user service communication.

    Creates an httpx.AsyncClient configured with the user service base URL from settings.
    SSL verification is disabled for development environments using self-signed certificates.

    Yields:
        httpx.AsyncClient: Configured async HTTP client for user service requests

    Business Context:
        Content storage service needs to query user service for user profile information
        when associating content with creators, validating ownership, and audit logging.

    Security Note:
        SSL verification is disabled (verify=False) for development convenience with
        self-signed certificates. Production deployments should use valid SSL certificates
        and enable verification.
    """
    # Disable SSL verification for self-signed certificates in development
    async with httpx.AsyncClient(base_url=settings.USER_SERVICE_URL, verify=False) as client:
        yield client

async def get_notification_service_client() -> httpx.AsyncClient:
    """
    FastAPI dependency to create async HTTP client for notification service communication.

    Creates an httpx.AsyncClient configured with the notification service base URL from
    settings. SSL verification is disabled for development environments.

    Yields:
        httpx.AsyncClient: Configured async HTTP client for notification service requests

    Business Context:
        Content storage service sends notifications when content is created, updated,
        deleted, or shared. Examples: notify instructors when course materials are ready,
        notify students when new content is available.

    Security Note:
        SSL verification is disabled (verify=False) for development convenience with
        self-signed certificates. Production deployments should use valid SSL certificates
        and enable verification.
    """
    # Disable SSL verification for self-signed certificates in development
    async with httpx.AsyncClient(base_url=settings.NOTIFICATION_SERVICE_URL, verify=False) as client:
        yield client

# Error handling utilities
class ServiceException(Exception):
    """
    Base exception class for service-level errors with HTTP status code mapping.

    Extends Python's base Exception to include an HTTP status code, allowing exceptions
    to be automatically converted to appropriate HTTP responses by error handlers.

    Attributes:
        message (str): Human-readable error description
        status_code (int): HTTP status code for the error response (default: 500)

    Business Context:
        Structured exception handling enables consistent error responses across API endpoints
        and facilitates debugging by providing clear error messages to API consumers.

    Usage:
        raise ServiceException("Content not found", status_code=404)
    """
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def handle_service_error(e: Exception) -> None:
    """
    Centralized error handler for service exceptions with logging and HTTP exception mapping.

    Logs all service errors and converts ServiceException instances to FastAPI HTTPException
    with appropriate status codes. Other exceptions are mapped to generic 500 Internal Server
    Error to avoid leaking implementation details.

    Args:
        e: Exception to handle and convert to HTTP response

    Raises:
        HTTPException: Always raises HTTPException with appropriate status code and message

    Business Context:
        Centralized error handling ensures consistent error response format across all API
        endpoints and prevents sensitive error details from being exposed to clients.

    Security:
        Generic error messages for unexpected exceptions prevent information disclosure
        while detailed logging enables debugging.
    """
    logger.error(f"Service error occurred: {str(e)}")
    if isinstance(e, ServiceException):
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )

# Configuration dependency
def get_settings() -> Settings:
    """
    FastAPI dependency to inject application settings into route handlers.

    Returns:
        Settings: Application configuration loaded from Hydra YAML files

    Business Context:
        Allows route handlers to access configuration without importing settings globally,
        supporting configuration injection in tests and dynamic configuration updates.
    """
    return settings

# Logging dependency
def get_logger() -> logging.Logger:
    """
    FastAPI dependency to inject configured logger into route handlers.

    Returns:
        logging.Logger: Pre-configured logger instance for the content storage service

    Business Context:
        Provides consistent logging configuration across all endpoints, enabling
        structured logging with appropriate log levels and formatting.
    """
    return logger

# Middleware dependency for request ID
def get_request_id(request: Request) -> str:
    """
    FastAPI dependency to extract request ID from request state for distributed tracing.

    Assumes a request ID has been generated by middleware and attached to request.state.
    Request IDs enable correlation of log entries across service boundaries for debugging.

    Args:
        request: FastAPI request object with request_id in state

    Returns:
        str: Unique request identifier (UUID) for distributed tracing

    Business Context:
        Distributed tracing is essential for debugging issues in microservice architectures
        where a single user action triggers multiple service calls. Request IDs allow
        correlating logs from different services for a single user transaction.
    """
    return request.state.request_id

# Combined dependencies
class CommonDependencies:
    """
    Convenience class combining frequently used dependencies for FastAPI route handlers.

    Aggregates database session, authentication, settings, logging, and request context
    into a single dependency that can be injected into route handlers, reducing boilerplate.

    Attributes:
        db (Session): SQLAlchemy database session for the current request
        current_user (TokenData): Authenticated user information from JWT token
        settings (Settings): Application configuration settings
        logger (logging.Logger): Configured logger instance
        request_id (str): Unique request identifier for distributed tracing

    Business Context:
        Most API endpoints require database access, user authentication, and logging.
        This class reduces repetitive dependency declarations in route handlers.

    Usage:
        @router.get("/content/{content_id}")
        async def get_content(
            content_id: UUID,
            deps: CommonDependencies = Depends()
        ):
            deps.logger.info(f"Fetching content {content_id} for user {deps.current_user.user_id}")
            content = deps.db.query(Content).filter_by(id=content_id).first()
            return content
    """
    def __init__(
        self,
        db: Session = Depends(get_db_session),
        current_user: TokenData = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
        logger: logging.Logger = Depends(get_logger),
        request_id: str = Depends(get_request_id)
    ):
        self.db = db
        self.current_user = current_user
        self.settings = settings
        self.logger = logger
        self.request_id = request_id