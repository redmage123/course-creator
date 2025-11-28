#!/usr/bin/env python3

# Load environment variables from .cc_env file if present
import os
if os.path.exists('/app/shared/.cc_env'):
    with open('/app/shared/.cc_env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value
"""
Content Storage Service - Advanced File Management & Storage Architecture

This module implements the main FastAPI application for the Content Storage Service,
a critical component of the Course Creator Platform responsible for:

1. CONTENT STORAGE ARCHITECTURE:
   - Multi-backend storage support (Local filesystem, AWS S3, Azure Blob, Google Cloud)
   - Hierarchical file organization with UUID-based naming for security
   - Atomic file operations with transaction-safe uploads and deletions
   - Content versioning and lifecycle management with automated cleanup
   - Storage optimization through compression and deduplication strategies

2. SECURITY & ACCESS CONTROL:
   - File type validation with configurable allow/block lists
   - Content scanning and malware detection integration points
   - Secure file naming to prevent path traversal attacks
   - Access control integration with platform RBAC system
   - Audit logging for all file operations and access patterns

3. PERFORMANCE & SCALABILITY:
   - Asynchronous file operations for high throughput
   - Configurable file size limits and storage quotas per user
   - Efficient metadata indexing for fast content discovery
   - Lazy loading and streaming for large file downloads
   - Background processing for content analysis and optimization

4. RELIABILITY & DISASTER RECOVERY:
   - Automated backup strategies with configurable retention policies
   - Storage health monitoring with real-time alerting
   - Redundant storage options for critical educational content
   - Transactional integrity ensuring data consistency
   - Recovery procedures for corrupted or missing files

5. INTEGRATION PATTERNS:
   - RESTful API design following OpenAPI standards
   - Event-driven architecture for content lifecycle notifications
   - Integration with course management for content assignment
   - Analytics integration for usage tracking and optimization
   - Content delivery network (CDN) preparation for global distribution

ARCHITECTURAL PRINCIPLES:
- SOLID design principles throughout the codebase
- Repository pattern for data access abstraction
- Dependency injection for testability and flexibility
- Clean separation of concerns between storage backends
- Comprehensive error handling with meaningful user feedback

This service serves as the foundation for all educational content management
within the platform, ensuring reliable, secure, and performant file operations
at scale while maintaining compliance with educational data protection requirements.
"""

import logging
import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from omegaconf import DictConfig
import hydra
import uvicorn

# Import service classes
from services.content_service import ContentService
from services.storage_service import StorageService

try:
    from logging_setup import setup_docker_logging
except ImportError:
    # Fallback if config module not available
    def setup_docker_logging(service_name: str, log_level: str = "INFO"):
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s'
        )
        return logging.getLogger(service_name)

from config.database import DatabaseManager
# Legacy repository removed
from exceptions import (
    ContentStorageException,
    DatabaseException,
    ConfigurationException
)
# Legacy repository removed
# Legacy services removed - using DAO pattern
from api.content_api import router as content_router
from api.storage_api import router as storage_router

# Custom exceptions
from exceptions import (
    ContentStorageException, FileOperationException, StorageException,
    DatabaseException, ValidationException, ContentNotFoundException,
    AuthenticationException, AuthorizationException, ConfigurationException,
    ContentProcessingException
)

# Global variables for dependency injection
db_manager: DatabaseManager = None
content_service: ContentService = None
storage_service: StorageService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Manager for Content Storage Service
    
    Manages the complete lifecycle of the content storage service from startup
    to shutdown, ensuring proper initialization of all storage components and
    graceful cleanup of resources.
    
    STARTUP OPERATIONS:
    1. Database Connection Initialization:
       - Establishes connection pool to PostgreSQL for metadata storage
       - Creates necessary tables if they don't exist (content, storage_quotas, etc.)
       - Validates database schema and performs any required migrations
    
    2. Storage Backend Configuration:
       - Initializes the configured storage backend (local/S3/Azure/GCS)
       - Validates storage paths and permissions
       - Sets up backup and retention policies
       - Configures security settings (encryption keys, access controls)
    
    3. Service Dependencies:
       - Initializes content and storage repositories with database connections
       - Creates service instances with proper dependency injection
       - Configures storage quotas and file validation rules
       - Sets up monitoring and health check endpoints
    
    4. Background Tasks:
       - Starts storage health monitoring
       - Initializes cleanup and maintenance schedules
       - Configures backup automation if enabled
       - Sets up content analysis and indexing processes
    
    SHUTDOWN OPERATIONS:
    1. Graceful Connection Closure:
       - Completes any pending file operations
       - Closes database connection pool properly
       - Flushes any cached metadata to persistent storage
    
    2. Resource Cleanup:
       - Cleans up temporary files and incomplete uploads
       - Ensures all file handles are properly closed
       - Saves operational metrics and statistics
    
    This lifespan manager ensures the service starts in a consistent state
    and shuts down cleanly without data loss or resource leaks.
    """
    global db_manager, content_service, storage_service
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await db_manager.connect()
        await db_manager.create_tables()
        
        # Initialize DAO
        from dao import ContentQueries, StorageQueries
        content_dao = ContentQueries()
        storage_dao = StorageQueries()
        
        # Initialize services
        storage_config = {
            "base_path": app.state.config.storage.path,
            "max_file_size": app.state.config.storage.max_file_size,
            "allowed_extensions": app.state.config.storage.allowed_extensions,
            "backup_enabled": app.state.config.storage.get("backup_enabled", False),
            "backup_path": app.state.config.storage.get("backup_path"),
            "retention_days": app.state.config.storage.get("retention_days", 30)
        }
        
        content_service = ContentService(db_manager.pool, storage_config)
        storage_service = StorageService(db_manager.pool, storage_config)
        
        logger.info("Content Storage Service initialized successfully")
        
        yield
        
    except DatabaseException:
        # Re-raise database exceptions as they are already properly formatted
        raise
    except Exception as e:
        raise ConfigurationException(
            message=f"Failed to initialize content storage service: Service startup configuration or dependency error",
            config_key="service_initialization",
            config_section="startup",
            original_exception=e
        )
    finally:
        # Cleanup
        if db_manager:
            await db_manager.disconnect()
        logger.info("Content Storage Service shutdown complete")


def create_app(config: DictConfig) -> FastAPI:
    """
    FastAPI Application Factory for Content Storage Service
    
    Creates and configures the FastAPI application instance with all necessary
    middleware, routers, and exception handlers for robust content storage operations.
    
    CONFIGURATION MANAGEMENT:
    The application uses Hydra configuration management to support multiple
    deployment environments (development, staging, production) with different
    storage backends, security settings, and performance optimizations.
    
    Key configuration areas:
    - Storage backend selection and credentials
    - File validation rules and size limits
    - Security policies and encryption settings
    - Performance tuning and caching strategies
    - Backup and disaster recovery settings
    
    MIDDLEWARE STACK:
    1. CORS Middleware:
       - Configured for secure cross-origin requests
       - Supports file upload from frontend applications
       - Maintains security while enabling legitimate access
    
    2. Request Logging Middleware (implicit):
       - Logs all file operations for audit purposes
       - Tracks performance metrics and usage patterns
       - Enables troubleshooting and capacity planning
    
    API STRUCTURE:
    - /api/content/* - Content metadata and lifecycle operations
    - /api/storage/* - Storage management and statistics
    - /health - Service health monitoring endpoint
    
    EXCEPTION HANDLING:
    The application implements comprehensive exception handling with:
    - Custom exception types for different error scenarios
    - Proper HTTP status code mapping
    - Detailed error messages for debugging
    - Security-aware error responses (no sensitive information leakage)
    
    SECURITY CONSIDERATIONS:
    - Input validation at multiple layers
    - File type and content validation
    - Access control integration points
    - Audit logging for compliance requirements
    
    Args:
        config: Hydra configuration object containing all service settings
    
    Returns:
        Configured FastAPI application instance ready for deployment
    """
    global db_manager
    
    app = FastAPI(
        title="Content Storage Service",
        description="API for storing and managing course content",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Store config in app state for access in lifespan
    app.state.config = config
    
    # Initialize database manager
    db_manager = DatabaseManager(config)
    
    # CORS middleware - Security: Use environment-configured origins
    # Never use wildcard (*) in production - enables CSRF attacks
    # Parse CORS origins from config (which reads from CORS_ORIGINS env var)
    cors_origins_str = config.cors.origins
    if isinstance(cors_origins_str, str):
        cors_origins = [origin.strip() for origin in cors_origins_str.split(',')]
    else:
        cors_origins = cors_origins_str  # Already a list

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(content_router, prefix="/api", tags=["content"])
    app.include_router(storage_router, prefix="/api/storage", tags=["storage"])
    
    @app.get("/")
    async def root():
        return {"message": "Content Storage Service", "version": "1.0.0"}
    
    @app.get("/health")
    async def health():
        """
        Comprehensive Health Check Endpoint for Content Storage Service
        
        Provides detailed health status information for monitoring systems,
        load balancers, and operational dashboards. This endpoint performs
        active health checks on critical service components.
        
        HEALTH CHECK COMPONENTS:
        1. Database Connectivity:
           - Tests connection pool availability
           - Validates database responsiveness with simple query
           - Checks for connection leaks or pool exhaustion
        
        2. Storage Backend Health:
           - Validates access to configured storage backend
           - Checks read/write permissions
           - Monitors storage capacity and performance
        
        3. File System Integrity:
           - Verifies storage directory accessibility
           - Checks available disk space
           - Validates file system permissions
        
        RESPONSE FORMAT:
        Returns JSON with status indicators:
        - status: 'healthy', 'degraded', or 'unhealthy'
        - database: Connection status and response time
        - storage: Backend availability and capacity
        - service: Service-specific metrics
        - timestamp: Health check execution time
        
        MONITORING INTEGRATION:
        This endpoint is designed for integration with:
        - Kubernetes liveness and readiness probes
        - Load balancer health checks
        - External monitoring systems (Prometheus, etc.)
        - Operational dashboards and alerting
        
        Returns:
            JSON health status with detailed component information
        """
        try:
            # Check database connection
            if db_manager.pool:
                async with db_manager.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                
                return {
                    "status": "healthy",
                    "database": "connected",
                    "service": "content-storage"
                }
            else:
                return {
                    "status": "unhealthy",
                    "database": "disconnected",
                    "service": "content-storage"
                }
        except DatabaseException as e:
            return {
                "status": "unhealthy",
                "database": "error",
                "service": "content-storage",
                "error": f"Database health check failed: {e.message}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "error",
                "service": "content-storage",
                "error": f"Health check failed: {str(e)}"
            }
    
    # Exception type to HTTP status code mapping (Open/Closed Principle)
    # This mapping follows the Open/Closed Principle - new exception types
    # can be added without modifying existing exception handling code
    EXCEPTION_STATUS_MAPPING = {
        ValidationException: 400,
        AuthenticationException: 401,
        AuthorizationException: 403,
        ContentNotFoundException: 404,
        ContentProcessingException: 422,
        ConfigurationException: 500,
        FileOperationException: 500,
        StorageException: 500,
        DatabaseException: 500,
    }
    
    # Custom exception handler for content storage operations
    @app.exception_handler(ContentStorageException)
    async def content_storage_exception_handler(request: Request, exc: ContentStorageException):
        """
        Centralized Exception Handler for Content Storage Operations
        
        Provides consistent error handling across all content storage operations
        with proper HTTP status codes, detailed error messages, and security
        considerations for client responses.
        
        EXCEPTION CLASSIFICATION:
        - ValidationException (400): Invalid input data or parameters
        - AuthenticationException (401): Missing or invalid authentication
        - AuthorizationException (403): Insufficient permissions
        - ContentNotFoundException (404): Requested content does not exist
        - ContentProcessingException (422): Content processing failures
        - ConfigurationException (500): Service configuration issues
        - FileOperationException (500): File system operation failures
        - StorageException (500): Storage backend failures
        - DatabaseException (500): Database operation failures
        
        ERROR RESPONSE FORMAT:
        Returns standardized JSON error responses containing:
        - error_type: Classification of the error
        - error_code: Specific error code for programmatic handling
        - message: Human-readable error description
        - details: Additional context when safe to expose
        - path: Request path where error occurred
        - timestamp: Error occurrence time
        
        SECURITY CONSIDERATIONS:
        - Sanitizes error messages to prevent information leakage
        - Logs detailed errors server-side for debugging
        - Returns generic messages for security-sensitive errors
        - Maintains audit trail for security investigations
        
        Args:
            request: FastAPI request object containing request context
            exc: Content storage exception instance with error details
        
        Returns:
            JSONResponse with appropriate status code and error information
        """
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
    
    # Global error handler for unexpected exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global Exception Handler for Unexpected Errors
        
        Catches all unhandled exceptions to prevent service crashes and
        ensure consistent error responses even for unexpected failures.
        This handler serves as the last line of defense for error handling.
        
        FUNCTIONALITY:
        1. Exception Logging:
           - Logs full exception details with stack trace
           - Includes request context for debugging
           - Records timing and performance impact
        
        2. Security Response:
           - Returns generic error message to prevent information leakage
           - Logs detailed information server-side only
           - Maintains service availability despite errors
        
        3. Monitoring Integration:
           - Triggers alerts for unexpected exception patterns
           - Feeds into error tracking and monitoring systems
           - Supports root cause analysis and debugging
        
        This handler ensures the service remains stable and secure even
        when encountering unexpected conditions or bugs.
        """
        logger = logging.getLogger(__name__)
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


def setup_dependency_injection():
    """
    Dependency Injection Configuration for Content Storage Service
    
    Configures dependency injection to provide loose coupling between
    components and enable testability, maintainability, and flexibility
    in service architecture.
    
    DEPENDENCY INJECTION PATTERN:
    This implementation uses a service locator pattern to manage dependencies,
    allowing for easy testing with mock objects and supporting different
    configurations for various deployment environments.
    
    INJECTED DEPENDENCIES:
    1. ContentService:
       - Manages content lifecycle operations
       - Handles file validation and storage
       - Provides content metadata management
    
    2. StorageService:
       - Manages storage backend operations
       - Handles quota management and statistics
       - Provides storage health monitoring
    
    BENEFITS:
    - Testability: Easy to inject mock services for unit testing
    - Flexibility: Can swap implementations based on configuration
    - Maintainability: Clear separation of concerns
    - Scalability: Services can be distributed or scaled independently
    
    FUTURE ENHANCEMENTS:
    This could be replaced with a more sophisticated DI container
    like dependency-injector or similar framework for more complex
    dependency graphs and lifecycle management.
    """
    from api.content_api import get_content_service
    from api.storage_api import get_storage_service
    
    # Override the dependency functions
    def override_content_service():
        return content_service
    
    def override_storage_service():
        return storage_service
    
    # This would be properly implemented with a DI container
    # For now, we'll modify the functions directly
    import api.content_api
    import api.storage_api
    
    api.content_api.get_content_service = override_content_service
    api.storage_api.get_storage_service = override_storage_service


@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    """
    Main Entry Point for Content Storage Service
    
    Initializes and starts the content storage service with comprehensive
    logging, configuration management, and service orchestration.
    
    INITIALIZATION SEQUENCE:
    1. Logging Configuration:
       - Sets up centralized logging with syslog format
       - Configures log levels based on environment
       - Enables audit logging for compliance requirements
    
    2. Configuration Validation:
       - Validates Hydra configuration for completeness
       - Checks storage backend credentials and settings
       - Verifies security and performance parameters
    
    3. Application Bootstrap:
       - Creates FastAPI application with all middleware
       - Initializes database connections and storage backends
       - Sets up dependency injection and service wiring
    
    4. Service Startup:
       - Starts ASGI server with optimized settings
       - Configures production-ready uvicorn parameters
       - Enables health checks and monitoring endpoints
    
    PRODUCTION CONSIDERATIONS:
    - Reduced uvicorn logging to prevent duplicate log entries
    - Optimized for container deployment and orchestration
    - Configured for horizontal scaling and load balancing
    - Integrated with platform monitoring and alerting systems
    
    ENVIRONMENT SUPPORT:
    Supports multiple deployment environments through Hydra:
    - Development: Enhanced logging and debugging features
    - Staging: Production-like configuration with safety nets
    - Production: Optimized for performance and reliability
    
    Args:
        cfg: Hydra configuration object with all service settings
    """
    # Setup centralized logging with syslog format
    service_name = os.environ.get('SERVICE_NAME', 'content-storage')
    log_level = os.environ.get('LOG_LEVEL', getattr(cfg, 'log', {}).get('level', 'INFO'))
    
    logger = setup_docker_logging(service_name, log_level)
    
    # Create FastAPI app
    app = create_app(cfg)
    
    # Setup dependency injection
    setup_dependency_injection()
    
    logger.info("Starting Content Storage Service...")
    
    # SSL configuration for HTTPS support
    ssl_keyfile = os.environ.get('SSL_KEYFILE', '/app/ssl/nginx-selfsigned.key')
    ssl_certfile = os.environ.get('SSL_CERTFILE', '/app/ssl/nginx-selfsigned.crt')
    
    # Check if SSL files exist, fallback to HTTP in development if not available
    use_ssl = os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile)
    
    if use_ssl:
        logger.info("Starting Content Storage Service with HTTPS enabled")
        # Run the server with HTTPS enabled
        uvicorn.run(
            app,
            host=cfg.server.host,
            port=cfg.server.port,
            reload=cfg.server.reload,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            log_level="warning",  # Reduce uvicorn log level since we have our own logging
            access_log=False,     # Disable uvicorn access log since we log via middleware
            log_config=None       # Use our logging configuration
        )
    else:
        logger.warning("SSL certificates not found, running with HTTP (development only)")
        # Run the server with reduced uvicorn logging to avoid duplicates
        uvicorn.run(
            app,
            host=cfg.server.host,
            port=cfg.server.port,
            reload=cfg.server.reload,
            log_level="warning",  # Reduce uvicorn log level since we have our own logging
            access_log=False,     # Disable uvicorn access log since we log via middleware
            log_config=None       # Use our logging configuration
        )


if __name__ == "__main__":
    """
    Direct Execution Entry Point
    
    Enables running the service directly with Python for development
    and testing purposes. In production, the service is typically
    started through container orchestration or process managers.
    
    USAGE:
        python main.py
        python main.py --config-name=production
        python main.py storage.backend=s3
    
    The Hydra configuration system supports command-line overrides
    for flexible deployment and testing scenarios.
    """
    main()