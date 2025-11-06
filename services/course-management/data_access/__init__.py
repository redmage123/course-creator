"""
Course Management Data Access Layer

This package implements the Data Access Object (DAO) pattern for the course management service,
centralizing all SQL operations and database interactions.

Business Context:
The data access layer provides a clean separation between business logic and database operations,
enabling better maintainability, testing, and architectural consistency across the platform.

Technical Architecture:
- CourseManagementDAO: Centralized SQL operations for all course-related database interactions
- SubProjectDAO: Hierarchical project management with multi-locations locations support
- Transaction support: Ensures data consistency for complex operations
- Exception handling: Standardized error handling using shared platform exceptions
- Connection pooling: Optimized database resource usage through asyncpg pool management

New in v3.4.0:
- SubProjectDAO: Enables multi-locations training programs (locations) with independent scheduling,
  locations tracking, capacity management, and status lifecycle operations
"""

from .course_dao import CourseManagementDAO
from .sub_project_dao import SubProjectDAO

__all__ = ['CourseManagementDAO', 'SubProjectDAO']