"""
Data Access Object (DAO) Package for Content Storage Service

BUSINESS REQUIREMENT:
Centralized SQL query management following DAO pattern for clean separation
of concerns between data access logic and business logic.

TECHNICAL IMPLEMENTATION:
- All SQL queries isolated in dedicated DAO classes
- Repository classes call DAO functions for data operations
- Improved maintainability and testability
- Single source of truth for database schema interactions

ARCHITECTURE BENEFITS:
- Separation of Concerns: SQL isolated from business logic
- Maintainability: Easy to find and modify specific queries
- Reusability: Same queries used by multiple repositories
- Testing: Easier to mock and test data access separately
"""

from .storage_queries import StorageQueries
from .backup_queries import BackupQueries
from .content_queries import ContentQueries

__all__ = ['StorageQueries', 'BackupQueries', 'ContentQueries']