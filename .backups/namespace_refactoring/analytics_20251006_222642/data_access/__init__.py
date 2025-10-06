"""
Analytics Data Access Layer

This package implements the Data Access Object (DAO) pattern for the analytics service,
centralizing all SQL operations and database interactions for comprehensive educational analytics.

Business Context:
The analytics data access layer provides centralized management of all student activity tracking,
performance metrics, learning analytics, and engagement measurement operations. This service is
critical for educational effectiveness measurement, personalized learning optimization, and
data-driven decision making across the Course Creator Platform. The DAO pattern ensures:
- Single source of truth for all analytics-related database operations
- Enhanced data consistency for critical educational metrics and insights
- Improved maintainability and testing capabilities for analytics operations
- Clear separation between analytics business logic and data access concerns
- Better performance through optimized analytics query patterns

Technical Architecture:
- AnalyticsDAO: Centralized SQL operations for all analytics-related database interactions
- Performance optimization: Efficient aggregation queries and indexing strategies
- Transaction support: Ensures data consistency for complex analytics operations
- Exception handling: Standardized error handling using shared platform exceptions
- Connection pooling: Optimized database resource usage through asyncpg pool management

Analytics Capabilities:
- Student activity tracking: Comprehensive behavioral pattern analysis
- Performance metrics: Quiz scores, lab usage, and learning outcome measurement
- Progress analytics: Individual and cohort learning progress tracking
- Engagement measurement: Course effectiveness and student satisfaction analysis
- Resource optimization: Lab usage patterns and infrastructure planning data
"""

from .analytics_dao import AnalyticsDAO

__all__ = ['AnalyticsDAO']