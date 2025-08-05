"""
Application Factory Module - User Management Service

This module implements the Factory pattern for creating and configuring FastAPI
application instances for the User Management Service. It encapsulates all the
complex setup logic required to bootstrap a fully functional microservice.

Architectural Principles:
    Single Responsibility: Solely responsible for application creation and configuration
    Open/Closed: Extensible through dependency injection without modification
    Liskov Substitution: Uses abstract interfaces for all dependencies
    Interface Segregation: Clean separation of concerns across components
    Dependency Inversion: Depends on abstractions, not concrete implementations

Application Setup Process:
    1. FastAPI application instance creation with metadata
    2. Dependency injection container initialization
    3. Database connection pool setup
    4. Redis connection configuration
    5. Middleware stack registration (CORS, logging, authentication)
    6. Exception handler registration
    7. Route registration (auth, users, sessions, admin)
    8. Health check endpoint configuration
    9. Lifespan event handler setup for graceful startup/shutdown

Why Factory Pattern:
    - Encapsulates complex object creation logic
    - Allows for different configurations (dev, staging, prod)
    - Centralizes application setup concerns
    - Enables testing with mock configurations
    - Supports dependency injection patterns

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from omegaconf import DictConfig
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from typing import Optional
import sys
import os

# Add shared directory to path for organization middleware
sys.path.append('/app/shared')
try:
    from auth.organization_middleware import OrganizationAuthorizationMiddleware, get_organization_context
except ImportError:
    # Fallback if middleware not available
    OrganizationAuthorizationMiddleware = None
    get_organization_context = None

"""
Path setup for importing modules from parent directory.

This is necessary because of our directory structure where the app/ subdirectory
needs to import modules from the service root directory. While not ideal from
a packaging perspective, this pattern is common in microservice architectures
where we want to keep related functionality grouped but maintain clean imports.

Alternative approaches considered:
- Relative imports: Breaks when running modules directly
- Package installation: Overkill for containerized microservices
- PYTHONPATH manipulation: Environment-dependent and fragile

Current approach provides the best balance of simplicity and reliability.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

"""
Core application components import.

These imports bring in all the necessary components for building the FastAPI
application. Each component is responsible for a specific aspect of the
application setup:

Routes: Define API endpoints and their handlers
Middleware: Handle cross-cutting concerns (CORS, logging, auth)
Error Handlers: Standardize error responses across the API
Container: Dependency injection container for service management
Exceptions: Custom exception types for domain-specific errors
"""
from routes import setup_auth_routes, setup_user_routes, setup_session_routes, setup_admin_routes, set_container
from middleware import setup_cors_middleware, setup_logging_middleware
from error_handlers import setup_exception_handlers
from infrastructure.container import UserManagementContainer
from exceptions import UserManagementException

class ApplicationFactory:
    """
    Factory class for creating configured FastAPI application instances.
    
    This class follows the Factory pattern to encapsulate the complex logic
    required to create a fully configured FastAPI application for the User
    Management Service. It handles all aspects of application setup including
    dependency injection, middleware configuration, route registration, and
    lifecycle management.
    
    Key Responsibilities:
        - FastAPI application instantiation with proper metadata
        - Dependency injection container setup and initialization
        - Database and cache connection management
        - Middleware stack configuration
        - Route and endpoint registration
        - Exception handler setup
        - Health check endpoint configuration
        - Application lifecycle management
    
    Design Benefits:
        - Centralized application configuration
        - Environment-agnostic setup (dev, staging, prod)
        - Testable application creation
        - Clean separation of setup concerns
        - Support for configuration injection
    
    Usage:
        app = ApplicationFactory.create_app(config)
    """
    
    @staticmethod
    def create_app(config: DictConfig) -> FastAPI:
        """
        Create and configure a complete FastAPI application instance.
        
        This method orchestrates the entire application setup process, from
        basic FastAPI instantiation through complete service configuration.
        It follows a specific setup order to ensure dependencies are properly
        initialized before they're needed.
        
        Setup Order:
            1. Define lifespan handler for startup/shutdown events
            2. Create FastAPI instance with metadata and configuration
            3. Register middleware (order matters - CORS first, then logging)
            4. Register exception handlers
            5. Register route handlers
            6. Add health check endpoint
        
        Args:
            config (DictConfig): Hydra configuration object containing:
                - server: Server configuration (host, port, debug)
                - database: PostgreSQL connection settings
                - redis: Redis connection settings  
                - cors: CORS policy configuration
                - logging: Logging configuration
                - auth: Authentication settings (JWT secrets, etc.)
                
        Returns:
            FastAPI: Fully configured FastAPI application ready for deployment
            
        Raises:
            ConfigurationError: If required configuration is missing
            ConnectionError: If database/Redis connections fail during startup
            
        Note:
            The returned application includes a configured dependency injection
            container accessible via app.state.container for use in route handlers.
        """
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """
            FastAPI lifespan event handler for graceful startup and shutdown.
            
            This async context manager handles the complete lifecycle of the
            User Management Service, ensuring proper resource initialization
            during startup and clean shutdown when the service stops.
            
            Startup Process:
                1. Initialize dependency injection container with configuration
                2. Establish database connection pools
                3. Initialize Redis connections for session management
                4. Set up authentication components (JWT managers, etc.)
                5. Register container for dependency injection
                6. Verify all critical components are healthy
            
            Shutdown Process:
                1. Close database connection pools gracefully
                2. Disconnect from Redis
                3. Clean up any temporary resources
                4. Ensure no hanging connections or processes
            
            Why This Pattern:
                - Ensures proper resource management
                - Enables graceful degradation on shutdown signals
                - Supports health checks by container orchestrators
                - Prevents resource leaks in container environments
                - Allows for cleanup of background tasks
            
            Args:
                app (FastAPI): The FastAPI application instance
                
            Yields:
                None: Context manager yields control to FastAPI runtime
                
            Raises:
                InitializationError: If critical components fail to initialize
                ConnectionError: If database or Redis connections fail
            """
            """
            STARTUP PHASE
            Initialize all service dependencies and verify system health
            """
            logging.info("Initializing User Management Service...")
            
            """
            Create and initialize the dependency injection container.
            The container manages all service dependencies including:
            - Database repositories
            - Authentication services
            - Session management
            - External service clients
            """
            container = UserManagementContainer(config)
            await container.initialize()
            app.state.container = container
            
            """
            Set global container for dependency injection in route handlers.
            This allows FastAPI dependency injection to access our services
            without circular import issues.
            """
            set_container(container)
            
            logging.info("User Management Service initialized successfully")
            
            yield
            
            """
            SHUTDOWN PHASE
            Clean up resources and ensure graceful service termination
            """
            logging.info("Shutting down User Management Service...")
            
            """
            Perform cleanup if container was successfully initialized.
            This ensures we don't attempt cleanup if startup failed.
            """
            if hasattr(app.state, 'container'):
                await app.state.container.cleanup()
            
            logging.info("User Management Service shutdown complete")
        
        """
        Create FastAPI application instance with comprehensive metadata.
        
        API Documentation Configuration:
        - Swagger UI (/docs) and ReDoc (/redoc) are conditionally enabled
        - Only available in debug mode to prevent production exposure
        - Provides interactive API testing in development environments
        
        Lifespan Integration:
        - Custom lifespan handler manages startup/shutdown events
        - Ensures proper resource initialization and cleanup
        - Critical for containerized deployment patterns
        """
        app = FastAPI(
            title="User Management Service",
            description="User authentication, authorization, and profile management for Course Creator Platform",
            version="2.3.0",
            docs_url="/docs" if getattr(config, 'service', {}).get('debug', False) else None,
            redoc_url="/redoc" if getattr(config, 'service', {}).get('debug', False) else None,
            lifespan=lifespan
        )
        
        """
        MIDDLEWARE SETUP PHASE
        
        Middleware order is critical - each middleware wraps the next in the chain.
        FastAPI processes middleware in registration order for requests and
        reverse order for responses.
        
        Order Explanation:
        1. CORS - Must be first to handle preflight requests properly
        2. Logging - Should capture all requests after CORS processing
        3. Authentication - Applied via dependencies, not global middleware
        
        Why Not Global Auth Middleware:
        - Some endpoints (health, docs) should be publicly accessible
        - Different endpoints may require different auth levels
        - Route-level dependencies provide more flexibility
        """
        # Organization security middleware (must be first for security)
        if OrganizationAuthorizationMiddleware:
            app.add_middleware(
                OrganizationAuthorizationMiddleware,
                config=config
            )
        
        setup_cors_middleware(app, config)
        setup_logging_middleware(app, config)
        setup_exception_handlers(app)
        
        """
        ROUTE SETUP PHASE
        
        Routes are organized by functional domain:
        - Auth: Login, logout, token refresh, password reset
        - Users: Profile management, user CRUD operations
        - Sessions: Session management and validation
        - Admin: Administrative operations and user management
        
        Each route module encapsulates related endpoints and their
        specific business logic while sharing common dependencies
        through the dependency injection container.
        """
        setup_auth_routes(app)
        setup_user_routes(app)
        setup_session_routes(app)
        setup_admin_routes(app)
        
        """
        HEALTH CHECK ENDPOINT
        
        Critical for container orchestration and monitoring systems.
        This endpoint should always be accessible without authentication
        to allow health checks from:
        - Docker health checks
        - Kubernetes liveness/readiness probes
        - Load balancers
        - Monitoring systems
        
        Response includes service metadata for debugging and monitoring.
        """
        @app.get("/health")
        async def health_check():
            """
            Service health check endpoint for monitoring and orchestration.
            
            This endpoint provides a simple way to verify that the User Management
            Service is running and ready to accept requests. It's designed to be
            called frequently by monitoring systems and should be fast and reliable.
            
            Health Check Criteria:
            - Service is running (if this endpoint responds, service is up)
            - Basic service metadata is accessible
            - No authentication required for accessibility
            
            Returns:
                dict: Health status information including:
                    - status: "healthy" if service is operational
                    - service: Service identifier for monitoring
                    - version: Current service version
                    - timestamp: Current server time (useful for debugging)
                    
            Note:
                This endpoint intentionally does NOT check:
                - Database connectivity (would slow down health checks)
                - Redis connectivity (could cause false negatives)
                - External service dependencies (not this service's responsibility)
                
                Deep health checks should use dedicated diagnostic endpoints.
            """
            return {
                "status": "healthy",
                "service": "user-management",
                "version": "2.3.0",
                "timestamp": datetime.utcnow()
            }
        
        """
        Return the fully configured FastAPI application.
        
        At this point, the application has:
        - Complete middleware stack configured
        - All routes and endpoints registered
        - Exception handlers in place
        - Health check endpoint available
        - Dependency injection container ready (will be initialized on startup)
        
        The application is ready for deployment via uvicorn or other ASGI servers.
        """
        return app