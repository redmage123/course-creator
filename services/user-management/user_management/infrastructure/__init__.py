"""
User Management Infrastructure Layer Module

BUSINESS CONTEXT:
This module serves as the entry point for the user management infrastructure layer,
providing a clean abstraction between the application layer and external infrastructure
concerns such as database connections, caching, and third-party integrations.

INFRASTRUCTURE RESPONSIBILITIES:
The infrastructure layer handles all external system interactions including:
- Database connection pooling and management (PostgreSQL with asyncpg)
- Redis caching for authentication performance optimization
- Dependency injection container for service lifecycle management
- External API integrations (if needed for user verification, SSO, etc.)
- Message queue integration for async user operations
- File storage for user profile images and documents

ARCHITECTURAL PATTERN:
This layer implements the Repository and Adapter patterns from Clean Architecture,
ensuring that business logic in the domain and application layers remains independent
of infrastructure details. Changes to database technology, caching strategy, or
external services can be made here without affecting core business rules.

CLEAN ARCHITECTURE COMPLIANCE:
- Infrastructure depends on domain interfaces (Dependency Inversion Principle)
- Domain and application layers never import from infrastructure
- All infrastructure implementations are injected via the DI container
- External framework details are isolated to this layer

KEY COMPONENTS EXPORTED:
- UserManagementContainer: Dependency injection container for service wiring
- Database connection pool management utilities
- Redis cache manager initialization and configuration
- Infrastructure-specific exception types

INTEGRATION POINTS:
- Database: PostgreSQL connection pool via asyncpg
- Cache: Redis via shared cache manager for authentication memoization
- Configuration: Hydra OmegaConf for environment-specific settings
- Logging: Centralized logging infrastructure for monitoring

USAGE IN APPLICATION:
The FastAPI application factory initializes this infrastructure layer during startup,
creating the container and establishing all external connections. The container then
provides properly configured service instances to API endpoints via dependency injection.

WHY THIS MATTERS:
By isolating infrastructure concerns, we achieve:
- Testability: Can easily mock infrastructure for unit tests
- Flexibility: Can swap implementations without changing business logic
- Maintainability: Clear separation of concerns and responsibilities
- Scalability: Infrastructure optimizations don't affect application code
- Compliance: Security and audit requirements handled in one layer

VERSION HISTORY:
- v1.0.0: Initial infrastructure layer with basic DI container
- v2.0.0: Added Redis caching integration for authentication
- v2.3.0: Enhanced container documentation and lifecycle management
- v2.4.0: Added performance optimization with memoization decorators

Author: Course Creator Platform Team
Last Updated: 2025-08-02
"""

# User Management Infrastructure Layer