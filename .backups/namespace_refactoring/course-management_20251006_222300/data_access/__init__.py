"""
Course Management Data Access Layer

This package implements the Data Access Object (DAO) pattern for the course management service,
centralizing all SQL operations and database interactions.

Business Context:
The data access layer provides a clean separation between business logic and database operations,
enabling better maintainability, testing, and architectural consistency across the platform.

Technical Architecture:
- CourseManagementDAO: Centralized SQL operations for all course-related database interactions
- Transaction support: Ensures data consistency for complex operations
- Exception handling: Standardized error handling using shared platform exceptions
- Connection pooling: Optimized database resource usage through asyncpg pool management
"""

from .course_dao import CourseManagementDAO

__all__ = ['CourseManagementDAO']