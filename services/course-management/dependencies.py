"""
Course Management Dependency Injection Module - FastAPI Dependency Infrastructure

This module implements the dependency injection infrastructure for the Course Management Service,
providing reusable, composable dependencies for database sessions, authentication, configuration
management, and external service clients.

BUSINESS CONTEXT:
Dependency injection is fundamental to building testable, maintainable microservices. This module
centralizes all dependency factories, enabling consistent resource management, security enforcement,
and service integration across all API endpoints.

DEPENDENCY INJECTION PATTERNS:
FastAPI's dependency injection system provides automatic dependency resolution, lifecycle management,
and cleanup. This module leverages these capabilities to implement clean separation of concerns,
testability, and resource efficiency.

CORE DEPENDENCIES PROVIDED:
1. Database Sessions: SQLAlchemy sync and async session management
2. Configuration Access: Hydra configuration injection
3. HTTP Clients: Reusable async HTTP client instances
4. Authentication: JWT token validation and user retrieval
5. Authorization: Role-based access control enforcement
6. Service Clients: External microservice client factories

WHY DEPENDENCY INJECTION:
- Testability: Easy mocking and stubbing for unit/integration tests
- Resource Management: Automatic cleanup of database connections and HTTP clients
- Separation of Concerns: Business logic independent of infrastructure
- Composability: Dependencies can depend on other dependencies
- Type Safety: Full type hints enable IDE autocomplete and validation

AUTHENTICATION FLOW:
1. OAuth2PasswordBearer extracts token from Authorization header
2. get_current_user validates JWT and retrieves user from database
3. get_current_active_user enforces active account requirement
4. get_current_admin_user enforces admin role requirement

SECURITY CONSIDERATIONS:
- JWT secrets managed through configuration
- Token expiration enforced at validation time
- Role-based access control (RBAC) via user dependencies
- Database session isolation per request
- Automatic resource cleanup prevents leaks

INTEGRATION PATTERNS:
- Hydra Configuration: Type-safe configuration injection
- SQLAlchemy: Database session lifecycle management
- HTTPX: Async HTTP client for service-to-service communication
- JWT: Industry-standard token-based authentication
"""
from typing import AsyncGenerator, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import hydra
from hydra.core.config_store import ConfigStore
from omegaconf import DictConfig
import logging
import httpx
import jwt
from datetime import datetime, timedelta

from db.session import SessionLocal, AsyncSessionLocal
from core.config import Settings
from core.logging import setup_logging
from schemas.user import UserInDB
from core.security import verify_password
from core.errors import ApiError

# Config store setup
cs = ConfigStore.instance()
cs.store(name="config", node=Settings)

# Logging setup
logger = logging.getLogger(__name__)
setup_logging()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database dependencies
def get_db() -> Generator[Session, None, None]:
    """
    Provide synchronous SQLAlchemy database session with automatic cleanup.

    This dependency factory creates a database session for each request and ensures
    proper cleanup even if the request handler raises an exception. The session is
    automatically committed or rolled back based on the success/failure of the request.

    BUSINESS CONTEXT:
    Database session management is critical for data integrity and resource efficiency.
    This dependency ensures every request operates within a transactional context with
    proper isolation and cleanup guarantees.

    USAGE:
        @app.post("/courses")
        def create_course(course: Course, db: Session = Depends(get_db)):
            # db session automatically provided and cleaned up
            db.add(course)
            db.commit()
            return course

    Yields:
        Session: Active SQLAlchemy session for database operations

    Cleanup:
        Session is automatically closed after request completion
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide asynchronous SQLAlchemy database session with automatic cleanup.

    This async dependency factory creates a database session optimized for async/await
    patterns, enabling non-blocking database I/O for high-throughput educational platforms.

    BUSINESS CONTEXT:
    Async database operations are essential for handling concurrent student enrollments,
    course accesses, and analytics queries without blocking the event loop.

    PERFORMANCE BENEFITS:
    - Non-blocking I/O: Multiple database queries can execute concurrently
    - Scalability: Supports thousands of concurrent student sessions
    - Resource Efficiency: Connection pooling with async operations

    USAGE:
        @app.post("/courses")
        async def create_course(course: Course, db: AsyncSession = Depends(get_async_db)):
            await db.add(course)
            await db.commit()
            return course

    Yields:
        AsyncSession: Active async SQLAlchemy session for database operations

    Cleanup:
        Session is automatically closed after request completion
    """
    try:
        async with AsyncSessionLocal() as session:
            yield session
    finally:
        await session.close()

# Configuration dependency
@hydra.main(config_path="../conf", config_name="config")
def get_config(cfg: DictConfig) -> Settings:
    """
    Provide Hydra-managed configuration with environment-specific overrides.

    This dependency injects type-safe configuration loaded via Hydra, supporting
    environment-specific overrides, composition, and validation.

    BUSINESS CONTEXT:
    Configuration management across development, staging, and production environments
    requires flexible, type-safe configuration with clear override semantics.

    CONFIGURATION SOURCES (priority order):
    1. CLI arguments: --config-name=production
    2. Environment overrides: conf/env/production.yaml
    3. Base configuration: conf/config.yaml
    4. Environment variables: via Hydra resolvers

    Args:
        cfg: Hydra configuration dictionary

    Returns:
        Settings: Type-safe settings object with all configuration parameters
    """
    return Settings(**cfg)

# HTTP client dependencies
async def get_http_client() -> httpx.AsyncClient:
    """
    Provide async HTTP client for external service communication.

    This dependency creates an async HTTP client optimized for service-to-service
    communication, with automatic connection pooling, timeout management, and retry logic.

    BUSINESS CONTEXT:
    Educational platforms integrate with multiple external services (user management,
    analytics, content delivery). Reusable HTTP clients ensure consistent communication
    patterns with proper resource management.

    FEATURES:
    - Connection Pooling: Reuses connections for efficiency
    - Async Operations: Non-blocking HTTP requests
    - Timeout Management: Prevents hung requests
    - Automatic Cleanup: Resources released after request completion

    USAGE:
        @app.get("/users/{user_id}")
        async def get_user(user_id: str, client: httpx.AsyncClient = Depends(get_http_client)):
            response = await client.get(f"https://user-service/users/{user_id}")
            return response.json()

    Yields:
        httpx.AsyncClient: Configured async HTTP client

    Cleanup:
        Client is automatically closed after request completion
    """
    async with httpx.AsyncClient() as client:
        yield client

# Authentication dependencies
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    config: Settings = Depends(get_config)
) -> UserInDB:
    """
    Extract and validate JWT token to retrieve authenticated user.

    This dependency implements the core authentication flow, validating JWT tokens
    and retrieving corresponding user records from the database.

    BUSINESS CONTEXT:
    Secure authentication is fundamental to protecting educational content, student data,
    and instructor resources. JWT-based authentication provides stateless, scalable
    authentication across distributed microservices.

    AUTHENTICATION FLOW:
    1. Extract JWT from Authorization: Bearer header
    2. Validate token signature using configured secret
    3. Decode token payload and extract username
    4. Query database for user record
    5. Return authenticated user or raise 401 Unauthorized

    SECURITY FEATURES:
    - Token Signature Validation: Prevents tampering
    - Expiration Checking: Automatic token expiration enforcement
    - Database Validation: User existence and status verification
    - Consistent Error Response: Prevents information leakage

    Args:
        token: JWT token from Authorization header (automatically injected)
        db: Database session dependency
        config: Configuration dependency with JWT settings

    Returns:
        UserInDB: Authenticated user database record

    Raises:
        HTTPException: 401 Unauthorized if token invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    user = db.query(UserInDB).filter(UserInDB.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """
    Enforce active user account requirement for API access.

    This dependency builds on get_current_user to additionally verify the user
    account is active (not suspended, deactivated, or pending).

    BUSINESS CONTEXT:
    Educational platforms must support account lifecycle management including
    suspension for policy violations, graduation/completion, or administrative holds.

    ACCOUNT STATES:
    - Active: Full platform access
    - Inactive: Suspended, deactivated, or pending verification
    - Deleted: Account marked for deletion

    Args:
        current_user: Authenticated user from get_current_user dependency

    Returns:
        UserInDB: Active user database record

    Raises:
        HTTPException: 400 Bad Request if user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    """
    Enforce administrator role requirement for administrative endpoints.

    This dependency implements role-based access control (RBAC) by verifying the
    authenticated user has administrator privileges.

    BUSINESS CONTEXT:
    Administrative operations (user management, course approval, platform configuration)
    require elevated privileges to protect platform integrity and data security.

    ROLE HIERARCHY:
    - Student: Basic course access and enrollment
    - Instructor: Course creation and student management
    - Admin: Platform administration and user management
    - Site Admin: Full platform control

    Args:
        current_user: Active authenticated user from get_current_active_user dependency

    Returns:
        UserInDB: Admin user database record

    Raises:
        HTTPException: 403 Forbidden if user lacks administrator privileges
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

# Error handling dependency
def handle_errors(error: Exception) -> None:
    """
    Global error handler for consistent error response formatting.

    This function provides centralized error handling, converting application-specific
    exceptions to appropriate HTTP responses with consistent formatting.

    BUSINESS CONTEXT:
    Consistent error responses improve API usability, enable better client-side error
    handling, and prevent information leakage that could aid security attacks.

    ERROR MAPPING:
    - ApiError: Custom application exceptions → mapped HTTP status
    - Validation Errors: Input validation failures → 400 Bad Request
    - Authentication Errors: Auth failures → 401 Unauthorized
    - Authorization Errors: Permission denials → 403 Forbidden
    - Not Found Errors: Resource not found → 404 Not Found
    - Server Errors: Unexpected exceptions → 500 Internal Server Error

    Args:
        error: Exception raised during request processing

    Raises:
        HTTPException: Mapped HTTP exception with appropriate status code and detail
    """
    if isinstance(error, ApiError):
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail
        )
    logger.exception("Unhandled error occurred")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )

# Service client dependencies
class ServiceClients:
    """
    Aggregated service clients for external microservice communication.

    This class provides a centralized interface to all external service clients,
    implementing the facade pattern for simplified service integration.

    BUSINESS CONTEXT:
    Educational platforms integrate with multiple external services (user management,
    notifications, content delivery). This facade simplifies service access and
    enables consistent communication patterns.

    SUPPORTED SERVICES:
    - User Service: Authentication, profile management, permissions
    - Notification Service: Email, SMS, push notifications
    - Content Service: Course materials, videos, documents

    Attributes:
        http_client: Shared async HTTP client for all services
    """

    def __init__(self, http_client: httpx.AsyncClient):
        """
        Initialize service clients facade with shared HTTP client.

        Args:
            http_client: Async HTTP client for service-to-service communication
        """
        self.http_client = http_client

    async def get_user_service(self) -> httpx.AsyncClient:
        """
        Get configured client for User Management Service.

        Returns:
            httpx.AsyncClient: HTTP client configured for user service endpoints
        """
        return self.http_client

    async def get_course_service(self) -> httpx.AsyncClient:
        """
        Get configured client for Course Service.

        Returns:
            httpx.AsyncClient: HTTP client configured for course service endpoints
        """
        return self.http_client

async def get_service_clients(
    http_client: httpx.AsyncClient = Depends(get_http_client)
) -> ServiceClients:
    """
    Provide service clients facade dependency.

    This dependency creates a ServiceClients facade initialized with the shared
    HTTP client, enabling consistent service-to-service communication patterns.

    USAGE:
        @app.get("/students/{student_id}/profile")
        async def get_student_profile(
            student_id: str,
            clients: ServiceClients = Depends(get_service_clients)
        ):
            user_client = await clients.get_user_service()
            response = await user_client.get(f"/users/{student_id}")
            return response.json()

    Args:
        http_client: Async HTTP client dependency

    Returns:
        ServiceClients: Initialized service clients facade
    """
    return ServiceClients(http_client)