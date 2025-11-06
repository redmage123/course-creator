"""
User Management Application Services - Service Layer Module

This module exports all application services for the User Management service.
Application services orchestrate business logic by coordinating between domain
entities, repositories (DAOs), and external services.

Exported Services:
    - AuthenticationService: User authentication, password management, and security
    - SessionService: User session lifecycle, JWT token management
    - TokenService: JWT token generation, validation, and revocation
    - UserService: User account CRUD, profile management, role/status changes

Service Layer Responsibilities:
    - Orchestrate business workflows
    - Coordinate domain entities and repositories
    - Enforce business rules and validations
    - Manage transactions and data consistency
    - Provide clean API for use by API endpoints

Design Patterns:
    - Service Layer Pattern: Encapsulates business logic
    - Dependency Injection: Services depend on abstractions
    - Repository Pattern: Data access through DAOs
    - Domain Model Pattern: Rich domain entities with business rules

Usage Example:
    ```python
    from user_management.application.services import (
        AuthenticationService,
        SessionService,
        TokenService,
        UserService
    )

    # Initialize services with dependencies
    auth_service = AuthenticationService(user_dao)
    token_service = TokenService(secret_key)
    session_service = SessionService(session_dao, token_service)
    user_service = UserService(user_dao, auth_service)

    # Use services in API endpoints
    user = await auth_service.authenticate_user(email, password)
    session = await session_service.create_session(user.id)
    ```

Author: Course Creator Platform Team
Version: 2.3.0
Last Updated: 2025-08-02
"""

from user_management.application.services.authentication_service import AuthenticationService
from user_management.application.services.session_service import SessionService, TokenService
from user_management.application.services.user_service import UserService

__all__ = [
    'AuthenticationService',
    'SessionService',
    'TokenService',
    'UserService'
]