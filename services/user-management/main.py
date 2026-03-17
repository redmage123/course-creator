#!/usr/bin/env python3

"""
User Management Service - Main Entry Point

This module serves as the primary entry point for the User Management Service,
which is responsible for handling user authentication, authorization, session
management, and basic user CRUD operations within the Course Creator Platform.

Architectural Principles:
    - Single Responsibility: Entry point focuses solely on service initialization
    - Open/Closed: Extensible through dependency injection without modification
    - Liskov Substitution: Uses abstract interfaces ensuring substitutability
    - Interface Segregation: Clean, focused interfaces prevent fat interfaces
    - Dependency Inversion: Depends on abstractions, not concrete implementations

Service Responsibilities:
    - User registration, authentication, and profile management
    - Session management with JWT token handling
    - Basic role-based access control (enhanced RBAC handled by org-management)
    - Student enrollment and access control for course instances
    - Integration with other microservices for user context

Technical Stack:
    - FastAPI: High-performance async web framework
    - Hydra: Configuration management for different environments
    - PostgreSQL: User data persistence via repository pattern
    - Redis: Session caching and temporary data storage
    - Docker: Containerized deployment with health checks

Port: 8000
Health Endpoint: /health
API Documentation: /docs (when debug=True)

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""

# CRITICAL: Load environment variables BEFORE importing hydra
# This ensures Hydra can resolve ${oc.env:VAR} interpolations when loading config
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

import logging
import hydra
from omegaconf import DictConfig
import uvicorn

from app.factory import ApplicationFactory

# Import centralized logging setup with graceful fallback
# This pattern ensures the service can start even if logging_setup is unavailable
# during development or in minimal deployment scenarios
try:
    from logging_setup import setup_docker_logging
except ImportError:
    # Fallback logging configuration for development/minimal environments
    # Uses basic Python logging with syslog-compatible format
    def setup_docker_logging(service_name: str, log_level: str = "INFO"):
        """
        Fallback logging setup when centralized logging is unavailable.
        
        This provides basic syslog-format logging that's compatible with
        our centralized logging infrastructure but doesn't require external
        dependencies to be available.
        
        Args:
            service_name: Name of the service for log identification
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            Logger instance configured for the service
        """
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s'
        )
        return logging.getLogger(service_name)

# Module-level logger - will be properly configured via setup_docker_logging in main()
# This ensures we have a logger available for module-level operations before
# the main service initialization completes
logger = logging.getLogger(__name__)

# Default configuration for standalone operation without Hydra
# This allows the service to run in development environments or
# when Hydra configuration is not available/desired
# 
# Why these defaults:
# - host='0.0.0.0': Allows Docker container access from outside
# - port=8000: Standard port for user-management service
# - debug=True: Enables FastAPI docs and detailed error messages
_default_config = {
    'server': {
        'host': '0.0.0.0',        # Bind to all interfaces for container access
        'port': 8000,             # Standard user management service port
        'debug': True             # Enable development features
    }
}

def create_app_instance(config_dict: dict = None):
    """
    Create FastAPI application instance with provided configuration.
    
    This function serves as a factory for creating the FastAPI application
    instance. It's designed to work both with Hydra configuration management
    and standalone operation with default configuration.
    
    Why this pattern:
    - Allows uvicorn to discover the app instance at module level
    - Supports both Hydra and non-Hydra deployment scenarios
    - Centralizes application creation logic through ApplicationFactory
    - Enables testing with custom configurations
    
    Args:
        config_dict (dict, optional): Configuration dictionary. If None,
                                     uses _default_config for standalone operation.
                                     
    Returns:
        FastAPI: Configured FastAPI application instance ready for deployment
        
    Note:
        The ApplicationFactory follows the Factory pattern to encapsulate
        the complex application setup including:
        - Dependency injection container configuration
        - Database connection setup
        - Middleware registration
        - Route registration
        - Error handler setup
    """
    if config_dict is None:
        config_dict = _default_config

    """
    Convert plain dict to OmegaConf DictConfig for ApplicationFactory.
    
    OmegaConf provides several advantages over plain dictionaries:
    - Hierarchical configuration access with dot notation (config.server.port)
    - Type safety and automatic validation
    - Environment variable interpolation (${ENV_VAR} syntax)
    - Configuration merging and composition capabilities
    - Immutable configuration objects (prevents accidental modification)
    - YAML/JSON serialization support
    
    This conversion ensures consistent configuration handling whether
    using Hydra (which provides DictConfig) or standalone operation.
    """
    from omegaconf import OmegaConf
    config = OmegaConf.create(config_dict)

    return ApplicationFactory.create_app(config)

# Create module-level app instance for uvicorn auto-discovery
# This pattern allows uvicorn to find the FastAPI app when running:
# - uvicorn main:app
# - python -m uvicorn main:app
# - In Docker containers with "python main.py" command
# 
# The app is created with default configuration for standalone operation
app = create_app_instance()

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """
    Main entry point for the User Management Service with Hydra configuration.
    
    This function serves as the primary entry point when the service is started
    with Hydra configuration management. It handles:
    - Centralized logging setup with syslog format
    - Application factory initialization with Hydra config
    - Uvicorn server startup with optimized settings
    - Graceful error handling and logging
    
    Why Hydra:
    - Environment-specific configuration (dev, staging, prod)
    - Configuration composition and overrides
    - Command-line configuration overrides
    - Configuration validation and type safety
    
    Args:
        cfg (DictConfig): Hydra configuration object containing:
            - server: Server configuration (host, port, debug)
            - database: Database connection settings
            - redis: Redis connection settings
            - logging: Logging configuration
            - auth: Authentication settings (JWT secrets, etc.)
            
    Returns:
        None: This function runs the server and doesn't return
        
    Raises:
        Exception: Any startup errors are logged and re-raised
                  for proper container health check failure
    """
    # Setup centralized logging with syslog format for Docker/Kubernetes environments
    # Service name can be overridden via environment for deployment flexibility
    service_name = os.environ.get('SERVICE_NAME', 'user-management')
    
    # Log level priority: ENV_VAR > Hydra config > default
    # This allows runtime log level adjustment without config changes
    log_level = os.environ.get('LOG_LEVEL', getattr(cfg, 'log', {}).get('level', 'INFO'))

    # Initialize centralized logging that outputs to both console and log files
    # Uses RFC 3164 syslog format for compatibility with log aggregation systems
    service_logger = setup_docker_logging(service_name, log_level)
    service_logger.info("Starting User Management Service")
    service_logger.info("Configuration: %s", cfg)

    try:
        # Create application using factory pattern with Hydra configuration
        # ApplicationFactory encapsulates complex setup including:
        # - Dependency injection container
        # - Database connections
        # - Middleware stack
        # - Route registration
        user_app = ApplicationFactory.create_app(cfg)
        
        # Start uvicorn server with HTTPS/SSL configuration
        # We reduce uvicorn's logging since we handle logging through middleware
        # and centralized logging system to avoid duplicate log entries
        uvicorn.run(
            user_app,
            host=getattr(cfg, 'server', {}).get('host', '0.0.0.0'),
            port=getattr(cfg, 'server', {}).get('port', 8000),
            log_level="warning",  # Reduce uvicorn verbosity (we handle app logging)
            access_log=False,     # Disable uvicorn access log (handled by middleware)
            reload=getattr(cfg, 'server', {}).get('debug', False),  # Auto-reload in dev
            ssl_keyfile="/app/ssl/nginx-selfsigned.key",
            ssl_certfile="/app/ssl/nginx-selfsigned.crt"
        )

    except Exception as e:
        # Log startup failures for debugging and monitoring
        # Re-raise to ensure container health checks fail appropriately
        service_logger.error("Failed to start service: %s", e)
        # Import shared exceptions
        import sys
        sys.path.append('/app/shared')
        from exceptions import ConfigurationException
        raise ConfigurationException(
            message="User Management Service failed to start",
            error_code="SERVICE_STARTUP_ERROR",
            details={
                "service": "user-management",
                "port": 8000,
                "common_causes": ["database connectivity", "configuration issues", "port conflicts"]
            },
            original_exception=e
        )

# Entry point for direct Python execution
# When run as 'python main.py', this will invoke the Hydra-decorated main function
# which will automatically load configuration from conf/config.yaml
if __name__ == "__main__":
    main()