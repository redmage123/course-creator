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
Course Generator Service - AI-Powered Educational Content Creation Platform

This module serves as the main entry point for the Course Generator Service, a sophisticated
microservice that leverages AI (primarily Anthropic Claude) to generate comprehensive
educational content including syllabi, slides, quizzes, and interactive exercises.

ARCHITECTURAL OVERVIEW:
======================

The Course Generator Service implements a clean architecture following SOLID principles:

1. **Domain Layer**: Core business entities and interfaces for AI content generation
2. **Application Layer**: Business logic orchestrating AI workflows and content validation
3. **Infrastructure Layer**: Concrete implementations of AI services, repositories, and external integrations
4. **API Layer**: FastAPI endpoints exposing content generation capabilities to other services

AI INTEGRATION ARCHITECTURE:
============================

The service integrates with multiple AI providers through a unified interface:

- **Primary Provider**: Anthropic Claude (claude-3-sonnet-20240229, claude-3-haiku-20240307)
- **Fallback Provider**: OpenAI GPT models (optional)
- **Mock Provider**: Local fallback for development/testing

CONTENT GENERATION WORKFLOW:
============================

1. **Request Processing**: API receives content generation requests with parameters
2. **Context Preparation**: Service builds AI-specific prompts with educational context
3. **AI Generation**: Claude API generates structured educational content
4. **Validation & Enhancement**: Generated content is validated and enhanced with metadata
5. **Storage & Retrieval**: Content is stored in PostgreSQL with full audit trails
6. **Response Delivery**: Validated content is returned to requesting services

SUPPORTED CONTENT TYPES:
========================

- **Syllabi**: Comprehensive course outlines with learning objectives and module structures
- **Slides**: Presentation content organized by modules with clear educational flow
- **Quizzes**: Assessment questions with multiple choice, explanations, and difficulty levels
- **Exercises**: Interactive coding labs and practical assignments
- **Chat Responses**: AI-powered educational assistance and clarifications

AI OPTIMIZATION STRATEGIES:
===========================

- **Prompt Engineering**: Sophisticated prompts optimized for educational content quality
- **Cost Management**: Token usage optimization and model selection based on content complexity
- **Rate Limiting**: Built-in rate limiting to prevent API quota exhaustion
- **Caching**: Intelligent caching of generated content to reduce AI API calls
- **Fallback Mechanisms**: Multiple fallback layers ensuring service availability

PERFORMANCE CONSIDERATIONS:
===========================

- **Async Processing**: All AI calls are asynchronous for optimal throughput
- **Connection Pooling**: Database connection pooling for efficient resource utilization
- **Error Recovery**: Robust error handling with automatic retries and circuit breakers
- **Monitoring**: Comprehensive logging and metrics for AI service performance

SOLID PRINCIPLES IMPLEMENTATION:
================================

- **Single Responsibility**: Each class has one reason to change (content generation, validation, storage)
- **Open/Closed**: Extensible through dependency injection for new AI providers
- **Liskov Substitution**: AI service interfaces allow seamless provider substitution
- **Interface Segregation**: Clean, focused interfaces for specific content generation needs
- **Dependency Inversion**: Depends on abstractions (IAIService) not concretions (Claude client)

BUSINESS VALUE:
===============

This service enables the platform to automatically generate high-quality educational content,
reducing content creation time from hours to minutes while maintaining educational standards
and pedagogical best practices.
"""
import logging
import os
# Removed unused imports: sys, Path

try:
    import hydra
    HYDRA_AVAILABLE = True
except ImportError:
    HYDRA_AVAILABLE = False
    hydra = None

import uvicorn
from omegaconf import DictConfig, OmegaConf

from app.factory import ApplicationFactory

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

# Will be configured via setup_docker_logging in main()
logger = logging.getLogger(__name__)

# Default configuration for when not using Hydra
_default_config = {
    'app': {
        'host': '0.0.0.0',
        'port': 8001,
        'debug': True
    }
}

def create_app_instance(config_dict: dict = None):
    """
    Create FastAPI application instance with AI content generation capabilities.
    
    This factory function creates a fully configured FastAPI application that provides
    AI-powered educational content generation services. The application is configured
    with dependency injection, middleware, error handling, and AI service integration.
    
    CONFIGURATION MANAGEMENT:
    =========================
    
    The application supports multiple configuration sources:
    - Hydra configuration files (preferred for production)
    - Environment variables (for containerized deployments)
    - Default configuration dictionary (fallback for development)
    
    AI SERVICE INITIALIZATION:
    ==========================
    
    During application creation, the following AI-related components are initialized:
    - Anthropic Claude client with API key validation
    - Prompt template management system
    - Content validation and quality assurance
    - Fallback mechanisms for service resilience
    
    DEPENDENCY INJECTION SETUP:
    ===========================
    
    The application factory configures dependency injection for:
    - AI service interfaces (IAIService, IPromptTemplateService)
    - Repository interfaces (ISyllabusRepository, IQuizRepository)
    - Application services (content generation, validation)
    - Configuration and logging services
    
    Args:
        config_dict (dict, optional): Configuration dictionary. If None, uses default
                                     configuration suitable for development environments.
                                     In production, configuration should come from Hydra.
    
    Returns:
        FastAPI: Fully configured FastAPI application instance with AI content generation
                endpoints, middleware, and dependency injection configured.
    
    Raises:
        ConfigurationError: If required AI API keys or configuration values are missing
        InitializationError: If critical dependencies cannot be initialized
        
    Example:
        # Development usage with default config
        app = create_app_instance()
        
        # Production usage with custom config
        config = {"ai": {"anthropic": {"api_key": "sk-..."}}}
        app = create_app_instance(config)
    
    Note:
        This function is primarily used by Uvicorn for automatic app discovery.
        In production deployments, the main() function with Hydra configuration
        is the preferred entry point.
    """
    if config_dict is None:
        config_dict = _default_config

    # Convert dict to DictConfig for ApplicationFactory compatibility
    # This ensures consistent configuration handling across all application components
    from omegaconf import OmegaConf
    config = OmegaConf.create(config_dict)

    return ApplicationFactory.create_app(config)

# Create app instance for uvicorn to find
app = create_app_instance()

def main(config: DictConfig = None) -> None:
    """
    Main entry point for the AI-powered Course Generator Service.
    
    This function serves as the production entry point for the Course Generator Service,
    providing comprehensive AI-driven educational content creation capabilities. It leverages
    Hydra for configuration management and sets up enterprise-grade logging, monitoring,
    and error handling.
    
    SERVICE INITIALIZATION WORKFLOW:
    ================================
    
    1. **Configuration Loading**: Hydra loads configuration from YAML files and environment variables
    2. **Logging Setup**: Centralized syslog-format logging for production monitoring
    3. **AI Service Validation**: Validates AI API keys and connectivity
    4. **Dependency Injection**: Initializes dependency injection container
    5. **Application Creation**: Creates FastAPI app with all AI content generation endpoints
    6. **Server Startup**: Launches Uvicorn server with optimized settings
    
    AI SERVICE CONFIGURATION:
    =========================
    
    The service expects the following AI configuration structure:
    
    ```yaml
    ai:
      anthropic:
        api_key: "${ANTHROPIC_API_KEY}"
        default_model: "claude-3-sonnet-20240229"
        max_tokens: 4000
        temperature: 0.7
        rate_limit:
          requests_per_minute: 50
          tokens_per_minute: 100000
      openai:  # Optional fallback
        api_key: "${OPENAI_API_KEY}"
        default_model: "gpt-4"
      fallback:
        enabled: true
        quality_threshold: 0.7
    ```
    
    LOGGING CONFIGURATION:
    ======================
    
    The service implements centralized logging with:
    - **Format**: RFC 3164 syslog format for enterprise monitoring
    - **Levels**: DEBUG (file only), INFO+ (console and file)
    - **Rotation**: 50MB max file size, 10 backup files
    - **Locations**: /var/log/course-creator/course-generator.log
    
    PERFORMANCE OPTIMIZATIONS:
    ==========================
    
    The service is configured for optimal AI content generation performance:
    - **Async I/O**: All AI API calls are non-blocking
    - **Connection Pooling**: Database connections are pooled for efficiency
    - **Request Batching**: Multiple content requests can be batched
    - **Caching**: Generated content is cached to reduce AI API costs
    
    MONITORING AND OBSERVABILITY:
    =============================
    
    The service exposes comprehensive monitoring capabilities:
    - **Health Endpoints**: /health for basic health checks
    - **Metrics Endpoints**: /metrics for Prometheus integration
    - **AI Usage Tracking**: Token usage and cost monitoring
    - **Error Tracking**: Detailed error logging with correlation IDs
    
    Args:
        config (DictConfig): Hydra configuration object containing:
            - service: Host, port, debug settings
            - ai: AI provider configurations and API keys
            - database: PostgreSQL connection settings
            - logging: Log levels and output configurations
            - cors: Cross-origin request settings
    
    Raises:
        ConfigurationError: If required configuration values are missing or invalid
        AIServiceError: If AI service initialization fails
        DatabaseError: If database connection cannot be established
        NetworkError: If the service cannot bind to the specified host/port
        
    Example Usage:
        # Production deployment with full configuration
        python main.py
        
        # Development with debug enabled
        python main.py service.debug=true
        
        # Override specific settings
        python main.py service.port=8002 ai.anthropic.api_key=sk-new-key
    
    Note:
        This function should only be called directly for production deployments.
        For development and testing, use create_app_instance() instead.
    """
    # If no config provided (hydra not available), create default config
    if config is None:
        config = OmegaConf.create(_default_config)
    
    # Setup centralized logging with syslog format for production monitoring
    service_name = os.environ.get('SERVICE_NAME', 'course-generator')
    log_level = os.environ.get('LOG_LEVEL', getattr(config, 'log', {}).get('level', 'INFO'))

    service_logger = setup_docker_logging(service_name, log_level)
    service_logger.info("Starting Course Generator Service with AI content generation capabilities")
    service_logger.info("Service configuration loaded successfully")
    
    # Log AI service configuration (without exposing API keys)
    ai_config = getattr(config, 'ai', {})
    if ai_config:
        anthropic_configured = bool(ai_config.get('anthropic', {}).get('api_key'))
        openai_configured = bool(ai_config.get('openai', {}).get('api_key'))
        service_logger.info(f"AI Services - Anthropic: {'✓' if anthropic_configured else '✗'}, "
                           f"OpenAI: {'✓' if openai_configured else '✗'}")
    else:
        service_logger.warning("No AI configuration found - service will use fallback content generation")

    try:
        # Create application using factory pattern with comprehensive dependency injection
        service_logger.info("Initializing FastAPI application with AI service dependencies")
        course_app = ApplicationFactory.create_app(config)
        
        # Extract server configuration with safe defaults
        host = getattr(config, 'service', {}).get('host', '0.0.0.0')
        port = getattr(config, 'service', {}).get('port', 8001)
        debug_mode = getattr(config, 'service', {}).get('debug', False)
        
        service_logger.info(f"Starting Course Generator Service on {host}:{port} (debug: {debug_mode})")
        
        # Start server with HTTPS/SSL configuration and optimized settings for AI content generation workloads
        uvicorn.run(
            course_app,
            host=host,
            port=port,
            log_level="warning",  # Reduce uvicorn log level since we have comprehensive logging
            access_log=False,     # Disable uvicorn access log to prevent log duplication
            reload=debug_mode,    # Enable hot reload only in debug mode
            workers=1 if debug_mode else None,  # Single worker in debug, auto-detect in production
            # SSL configuration for HTTPS
            ssl_keyfile="/app/ssl/nginx-selfsigned.key",
            ssl_certfile="/app/ssl/nginx-selfsigned.crt",
            # Optimize for AI content generation workloads
            loop="asyncio",       # Use asyncio for optimal async performance
            http="httptools",     # Use httptools for better HTTP parsing performance
            lifespan="on"         # Enable lifespan events for proper cleanup
        )

    except Exception as e:
        service_logger.error(f"Failed to start Course Generator Service: {e}")
        service_logger.error("This may be due to missing AI API keys, database connectivity, or port conflicts")
        # Import shared exceptions
        import sys
        from exceptions import ConfigurationException
        raise ConfigurationException(
            message="Course Generator Service failed to start",
            error_code="SERVICE_STARTUP_ERROR",
            details={
                "service": "course-generator",
                "common_causes": ["missing AI API keys", "database connectivity", "port conflicts"]
            },
            original_exception=e
        )

if __name__ == "__main__":
    if HYDRA_AVAILABLE:
        # Use hydra configuration if available
        @hydra.main(version_base=None, config_path="conf", config_name="config")
        def main_with_config(config: DictConfig) -> None:
            main(config)
        main_with_config()
    else:
        # Use default configuration if hydra not available
        main()