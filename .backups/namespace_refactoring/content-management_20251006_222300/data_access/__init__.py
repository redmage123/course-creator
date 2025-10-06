"""
Content Management Data Access Layer

This package implements the Data Access Object (DAO) pattern for the content management service,
centralizing all SQL operations and database interactions for educational content lifecycle management.

Business Context:
The content management data access layer provides centralized management of all educational content
operations including content creation, validation, search, organization, and delivery. This service
is fundamental to the educational experience, enabling instructors to create high-quality courses,
assessments, and learning materials while providing students with organized, discoverable educational
content. The DAO pattern ensures:
- Single source of truth for all content management database operations
- Enhanced data consistency for critical educational content operations
- Improved maintainability and testing capabilities for content workflows
- Clear separation between content business logic and data access concerns
- Better performance through optimized content search and retrieval patterns

Technical Architecture:
- ContentManagementDAO: Centralized SQL operations for all content-related database interactions
- Content lifecycle management: Creation, validation, publishing, and archival workflows
- Transaction support: Ensures data consistency for complex content operations
- Exception handling: Standardized error handling using shared platform exceptions
- Connection pooling: Optimized database resource usage through asyncpg pool management

Content Management Capabilities:
- Content creation: Comprehensive content development with metadata and validation
- Search and discovery: Advanced content search with filtering and ranking capabilities
- Quality assurance: Content quality scoring and assessment workflows
- Version control: Content versioning and change tracking for collaborative development
- Analytics integration: Content usage analytics and performance measurement
- Workflow management: Status-based content workflows for review and approval processes
"""

from .content_management_dao import ContentManagementDAO

__all__ = ['ContentManagementDAO']