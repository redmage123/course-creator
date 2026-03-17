"""
Course Management Service Configuration - Hydra-based Configuration Management

This module defines the comprehensive configuration schema for the Course Management Service
using Hydra and OmegaConf for enterprise-grade configuration management and validation.

BUSINESS CONTEXT:
Configuration management is critical for operating educational platforms across multiple
environments (development, staging, production) with varying infrastructure requirements,
security policies, and integration patterns.

CONFIGURATION ARCHITECTURE:
This module implements a hierarchical configuration structure using dataclasses and Hydra's
ConfigStore pattern, enabling type-safe configuration with built-in validation, environment
overrides, and composition capabilities.

CONFIGURATION DOMAINS:
1. Logging Configuration: Centralized logging setup with levels, formats, and destinations
2. Database Configuration: PostgreSQL connection pooling, SSL, and retry policies
3. Redis Configuration: Caching layer configuration with cluster support
4. Service Integration: External service URLs, timeouts, and circuit breaker settings
5. Security Configuration: JWT authentication, API keys, and CORS policies
6. Service Discovery: Consul integration for dynamic service discovery

WHY HYDRA CONFIGURATION:
- Type Safety: Dataclass validation ensures configuration correctness at startup
- Composition: Hierarchical configuration enables DRY principles
- Environment Overrides: Easy per-environment customization via config files or CLI
- Validation: Automatic type checking and constraint validation
- IDE Support: Full autocomplete and type hints for configuration access
- Testing: Simplified test configuration through programmatic overrides

DEPLOYMENT FLEXIBILITY:
- Local Development: SQLite with mock services for rapid development
- Staging: PostgreSQL with Redis caching for integration testing
- Production: Clustered PostgreSQL, Redis, and full observability stack
- Multi-Tenant: Organization-specific configuration overrides

SECURITY CONSIDERATIONS:
- Secrets Management: Integration with secret stores for production credentials
- SSL/TLS Configuration: Database and service communication encryption
- API Key Rotation: Support for rotating service authentication credentials
- CORS Configuration: Fine-grained cross-origin request policies
"""
from dataclasses import dataclass
from typing import List, Optional
from omegaconf import MISSING
from hydra.core.config_store import ConfigStore

@dataclass
class LoggingConfig:
    """
    Logging configuration for the Course Management Service.

    Configures centralized logging with support for multiple log levels, formats,
    and destinations (console, file, syslog) across all service components.

    Attributes:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log message format (syslog, json, structured)
        file: Log file path for persistent logging
    """
    level: str
    format: str
    file: str

@dataclass
class DatabaseConfig:
    """
    PostgreSQL database configuration with connection pooling and high availability.

    Supports production-grade database connectivity with SSL/TLS encryption,
    connection pooling for performance, and automatic retry logic for resilience.

    Attributes:
        type: Database type (postgresql, mysql, sqlite for testing)
        host: Database server hostname or IP address
        port: Database server port (default 5432 for PostgreSQL)
        name: Database name (schema)
        user: Database authentication username
        password: Database authentication password
        pool_size: Connection pool size for concurrent operations
        pool_timeout: Connection pool acquisition timeout in seconds
        ssl_mode: SSL/TLS mode (require, prefer, disable)
        connection_retry_attempts: Number of retry attempts for failed connections
        connection_retry_delay: Delay between retry attempts in seconds
    """
    type: str
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int
    pool_timeout: int
    ssl_mode: str
    connection_retry_attempts: int
    connection_retry_delay: int

@dataclass
class RedisConfig:
    """
    Redis cache configuration for performance optimization and session management.

    Configures distributed caching layer for course data, enrollment state,
    and analytics aggregations to reduce database load and improve response times.

    Attributes:
        host: Redis server hostname
        port: Redis server port (default 6379)
        db: Redis database number (0-15)
        password: Redis authentication password (if enabled)
        ssl: Enable SSL/TLS encryption for Redis connections
        timeout: Command timeout in seconds
        retry_attempts: Number of retry attempts for failed commands
        pool_size: Connection pool size
    """
    host: str
    port: int
    db: int
    password: str
    ssl: bool
    timeout: int
    retry_attempts: int
    pool_size: int

@dataclass
class ServiceConfig:
    """
    External service integration configuration.

    Defines connection parameters for external microservices including
    timeouts, retry policies, and circuit breaker settings.

    Attributes:
        url: Service base URL (e.g., https://user-service:8000)
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts for failed requests
    """
    url: str
    timeout: int
    retry_attempts: int

@dataclass
class ServicesConfig:
    """
    Composite configuration for all external service integrations.

    Centralizes configuration for inter-service communication across the
    educational platform's microservices architecture.

    Attributes:
        user_service: User management service configuration
        notification_service: Email and notification service configuration
        content_service: Course content management service configuration
    """
    user_service: ServiceConfig
    notification_service: ServiceConfig
    content_service: ServiceConfig

@dataclass
class ApiGatewayConfig:
    """
    API Gateway configuration for frontend-backend communication.

    Configures the central API gateway that routes requests from frontend
    applications to appropriate backend microservices.

    Attributes:
        url: API Gateway base URL
        timeout: Gateway request timeout in seconds
    """
    url: str
    timeout: int

@dataclass
class JWTConfig:
    """
    JSON Web Token (JWT) authentication configuration.

    Configures JWT-based authentication for secure API access including
    signing algorithms, token expiration, and secret key management.

    Attributes:
        secret_key: JWT signing secret key (rotate regularly in production)
        algorithm: Signing algorithm (HS256, RS256, etc.)
        token_expiry: Token expiration time in seconds
    """
    secret_key: str
    algorithm: str
    token_expiry: int

@dataclass
class ApiKeysConfig:
    """
    API key configuration for service-to-service authentication.

    Manages API keys for authenticated inter-service communication,
    enabling service mesh security and request authorization.

    Attributes:
        user_service: API key for user service authentication
        notification_service: API key for notification service authentication
        content_service: API key for content service authentication
    """
    user_service: str
    notification_service: str
    content_service: str

@dataclass
class CorsConfig:
    """
    Cross-Origin Resource Sharing (CORS) security configuration.

    Defines allowed origins, methods, and headers for cross-origin requests
    from frontend applications to API endpoints.

    Attributes:
        allowed_origins: List of allowed origin URLs
        allowed_methods: List of allowed HTTP methods
        allowed_headers: List of allowed request headers
    """
    allowed_origins: List[str]
    allowed_methods: List[str]
    allowed_headers: List[str]

@dataclass
class SecurityConfig:
    """
    Comprehensive security configuration for the Course Management Service.

    Centralizes all security-related configurations including authentication,
    authorization, API keys, and CORS policies.

    Attributes:
        jwt: JWT authentication configuration
        api_keys: Service-to-service API key configuration
        cors: CORS policy configuration
    """
    jwt: JWTConfig
    api_keys: ApiKeysConfig
    cors: CorsConfig

@dataclass
class ServiceDiscoveryConfig:
    """
    Service discovery configuration for dynamic service mesh integration.

    Enables integration with Consul or similar service discovery platforms
    for automatic service registration, health checking, and dynamic routing.

    Attributes:
        enabled: Enable service discovery integration
        consul_host: Consul server hostname
        consul_port: Consul server port
        service_check_interval: Health check interval in seconds
        health_check_endpoint: Health check HTTP endpoint path
    """
    enabled: bool
    consul_host: str
    consul_port: int
    service_check_interval: int
    health_check_endpoint: str

@dataclass
class AppConfig:
    """
    Root configuration class for the Course Management Service.

    Aggregates all configuration domains into a single, type-safe configuration
    object managed by Hydra. This configuration is loaded at service startup
    and can be overridden via environment-specific config files or CLI arguments.

    CONFIGURATION LOADING:
    Configuration is loaded in this priority order:
    1. Default values defined in conf/config.yaml
    2. Environment-specific overrides (conf/env/production.yaml)
    3. CLI overrides (--config-name=production)
    4. Environment variables (via Hydra resolvers)

    Attributes:
        name: Service name for identification and logging
        version: Service version for deployment tracking
        host: Service bind host (0.0.0.0 for containers)
        port: Service port number
        debug: Enable debug mode (never in production)
        logging: Logging configuration
        database: Database connection configuration
        redis: Redis cache configuration
        services: External service integration configuration
        api_gateway: API Gateway configuration
        security: Security and authentication configuration
        service_discovery: Service mesh discovery configuration
    """
    name: str
    version: str
    host: str
    port: int
    debug: bool
    logging: LoggingConfig
    database: DatabaseConfig
    redis: RedisConfig
    services: ServicesConfig
    api_gateway: ApiGatewayConfig
    security: SecurityConfig
    service_discovery: ServiceDiscoveryConfig

cs = ConfigStore.instance()
cs.store(name="config", node=AppConfig)