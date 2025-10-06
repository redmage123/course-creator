"""
Organization Management Data Access Layer

This package implements the Data Access Object (DAO) pattern for the organization management service,
centralizing all SQL operations and database interactions.

Business Context:
The data access layer provides a clean separation between business logic and database operations,
enabling better maintainability, testing, and architectural consistency across the platform.
The Organization Management service is critical for multi-tenant operations, user management,
and role-based access control across the entire Course Creator Platform.

Technical Architecture:
- OrganizationManagementDAO: Centralized SQL operations for all organization-related database interactions
- Multi-tenant data isolation: Ensures proper organizational data separation and security
- Transaction support: Ensures data consistency for complex organizational operations
- Exception handling: Standardized error handling using shared platform exceptions
- Connection pooling: Optimized database resource usage through asyncpg pool management

Security and Compliance:
- Audit logging: Comprehensive activity tracking for compliance and security monitoring
- Role-based access: Proper multi-tenant permission and role management
- Data isolation: Ensures organizations cannot access each other's data
- Permission validation: Consistent authorization patterns across all operations
"""

from .organization_dao import OrganizationManagementDAO

__all__ = ['OrganizationManagementDAO']