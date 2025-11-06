"""
User Management Service Configuration Module

This module defines the configuration data classes for the User Management Service using
Hydra's configuration management system. It provides type-safe configuration structures
for all service components including database, caching, dependent services, security, and monitoring.

Business Context:
Centralized configuration management enables environment-specific deployments (dev, staging, prod)
with type validation and hierarchical composition. This follows the 12-factor app methodology
for storing configuration in the environment while maintaining type safety and validation.

Technical Rationale:
- Uses dataclasses for immutability and type hints
- Integrates with Hydra for composition and environment variable interpolation
- Supports configuration overrides via command-line and config files
- Enables multi-environment deployments with minimal code changes

Why Hydra:
- Hierarchical configuration composition (base + environment-specific overrides)
- Type-safe configuration with validation
- Command-line configuration overrides for operational flexibility
- Environment variable interpolation (${oc.env:VAR} syntax)
- Configuration groups for different deployment scenarios

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""
from dataclasses import dataclass
from typing import Optional, List
from hydra.core.config_store import ConfigStore

@dataclass
class DatabaseConfig:
    """
    PostgreSQL database configuration.

    Business Context:
    Database configuration supports multi-tenant architecture with connection pooling
    for scalability and SSL encryption for security compliance (GDPR/CCPA requirements).

    Attributes:
        host (str): Database server hostname or IP address
        port (int): Database server port (default: 5432)
        username (str): Database authentication username
        password (str): Database authentication password (use environment variables)
        database (str): Target database name (typically 'course_creator')
        pool_size (int): Connection pool size for concurrent request handling
        ssl_mode (str): SSL mode ('require', 'verify-ca', 'verify-full') for encryption
    """
    host: str
    port: int
    username: str
    password: str
    database: str
    pool_size: int
    ssl_mode: str

@dataclass
class RedisConfig:
    """
    Redis caching and session storage configuration.

    Business Context:
    Redis provides high-performance session caching, token storage, and temporary data
    management for stateless authentication with JWT tokens. Critical for horizontal
    scalability and sub-millisecond session validation performance.

    Attributes:
        host (str): Redis server hostname or IP address
        port (int): Redis server port (default: 6379)
        password (Optional[str]): Redis authentication password (required for production)
        db (int): Redis database number (0-15)
        ssl (bool): Enable SSL/TLS encryption for Redis connections (production requirement)
    """
    host: str
    port: int
    password: Optional[str]
    db: int
    ssl: bool

@dataclass
class ServiceConfig:
    """
    Configuration for dependent microservice connections.

    Business Context:
    Defines connection parameters, timeouts, and retry logic for inter-service
    communication in the microservices architecture. Ensures resilient communication
    with proper timeout and retry strategies to handle transient failures.

    Attributes:
        host (str): Service hostname or IP address
        port (int): Service port number
        timeout (int): HTTP request timeout in seconds
        retry_attempts (int): Number of retry attempts for failed requests
        health_check_path (str): Health check endpoint path (e.g., '/health')
    """
    host: str
    port: int
    timeout: int
    retry_attempts: int
    health_check_path: str

@dataclass
class DependentServices:
    """
    Configuration for all dependent microservices.

    Business Context:
    Aggregates connection configurations for microservices that the user-management
    service depends on. Enables service discovery and health-aware routing for
    distributed system resilience.

    Attributes:
        course_management: Course management service configuration
        course_generator: AI course generation service configuration
        content_storage: Content storage service configuration
    """
    course_management: ServiceConfig
    course_generator: ServiceConfig
    content_storage: ServiceConfig

@dataclass
class Security:
    """
    Security and authentication configuration.

    Business Context:
    Defines security parameters for JWT authentication, API security, and CORS policies.
    Critical for GDPR/CCPA compliance and protection against common web vulnerabilities
    (XSS, CSRF, JWT attacks). Token expiry balances security (shorter = more secure)
    with user experience (longer = fewer re-authentications).

    Attributes:
        jwt_secret (str): Secret key for JWT token signing (256-bit recommended)
        api_key (str): API key for inter-service authentication
        token_expiry (int): JWT token expiry in seconds (default: 3600 = 1 hour)
        allowed_origins (List[str]): CORS allowed origins for cross-origin requests
    """
    jwt_secret: str
    api_key: str
    token_expiry: int
    allowed_origins: List[str]

@dataclass
class Monitoring:
    """
    Monitoring, logging, and observability configuration.

    Business Context:
    Defines monitoring parameters for logging, distributed tracing, metrics collection,
    and health checks. Essential for production observability, debugging, and SLA compliance.
    Enables centralized log aggregation and real-time system health monitoring.

    Attributes:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_tracing (bool): Enable distributed tracing (OpenTelemetry/Jaeger)
        metrics_port (int): Port for Prometheus metrics endpoint
        health_check_interval (int): Health check polling interval in seconds
    """
    log_level: str
    enable_tracing: bool
    metrics_port: int
    health_check_interval: int

@dataclass
class AppConfig:
    """
    Root application configuration aggregating all service configurations.

    Business Context:
    Serves as the top-level configuration container for the User Management Service.
    Hydra loads this configuration from YAML files with environment-specific overrides,
    enabling seamless deployment across dev, staging, and production environments.

    This configuration follows the 12-factor app methodology:
    - Configuration stored in environment (not code)
    - Strict separation between environments
    - Config validation at startup
    - No environment-specific code branches

    Attributes:
        service_name (str): Service identifier for logging and monitoring
        environment (str): Environment name (dev, staging, prod)
        debug (bool): Enable debug mode (detailed errors, API docs)
        database (DatabaseConfig): PostgreSQL database configuration
        redis (RedisConfig): Redis caching configuration
        dependent_services (DependentServices): Dependent microservices configuration
        security (Security): Security and authentication configuration
        monitoring (Monitoring): Monitoring and observability configuration

    Example:
        Configuration is loaded automatically by Hydra:
        ```
        @hydra.main(version_base=None, config_path="conf", config_name="config")
        def main(cfg: AppConfig):
            # Access typed configuration
            db_host = cfg.database.host
            jwt_secret = cfg.security.jwt_secret
        ```
    """
    service_name: str
    environment: str
    debug: bool
    database: DatabaseConfig
    redis: RedisConfig
    dependent_services: DependentServices
    security: Security
    monitoring: Monitoring

cs = ConfigStore.instance()
cs.store(name="config", node=AppConfig)