"""
User Management Data Access Layer

This package implements the Data Access Object (DAO) pattern for the user management service,
centralizing all SQL operations and database interactions.

Business Context:
The data access layer provides a clean separation between business logic and database operations,
enabling better maintainability, testing, and architectural consistency across the platform.
The User Management service is critical for authentication, authorization, and user lifecycle
management across the entire Course Creator Platform.

Technical Architecture:
- UserManagementDAO: Centralized SQL operations for all user-related database interactions
- Session management: Comprehensive session lifecycle and security operations
- Transaction support: Ensures data consistency for complex user operations
- Exception handling: Standardized error handling using shared platform exceptions
- Connection pooling: Optimized database resource usage through asyncpg pool management

Security Considerations:
- All password operations use pre-hashed values (never plaintext)
- Session tokens are handled securely without logging
- User data access includes privacy protections
- Authentication operations include comprehensive audit logging
"""

from .user_dao import UserManagementDAO

__all__ = ['UserManagementDAO']