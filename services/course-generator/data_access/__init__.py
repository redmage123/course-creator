"""
Course Generator Data Access Layer

This package implements the Data Access Object (DAO) pattern for the course generator service,
centralizing all SQL operations and database interactions for AI-powered educational content creation.

Business Context:
The course generator data access layer provides centralized management of all AI-powered content
creation operations including syllabus generation, quiz creation, slide development, exercise
design, and lab environment configuration. This service is the content creation engine of the
Course Creator Platform, enabling automated generation of comprehensive educational materials.
The DAO pattern ensures:
- Single source of truth for all course generation database operations
- Enhanced data consistency for AI-generated educational content
- Improved maintainability and testing capabilities for content generation
- Clear separation between AI generation logic and data persistence concerns
- Better performance through optimized content creation query patterns

Technical Architecture:
- CourseGeneratorDAO: Centralized SQL operations for all course generation database interactions
- AI generation tracking: Comprehensive job monitoring and performance analytics
- Transaction support: Ensures data consistency for complex content creation operations
- Exception handling: Standardized error handling using shared platform exceptions
- Connection pooling: Optimized database resource usage through asyncpg pool management

Content Generation Capabilities:
- Syllabus generation: AI-powered course structure and curriculum development
- Quiz creation: Automated assessment generation with multiple question types
- Slide development: Presentation content creation with template integration
- Exercise design: Hands-on learning activity generation with solutions
- Lab environment setup: Automated development environment configuration
- Content versioning: Iterative improvement tracking and management
- Generation analytics: Performance monitoring and optimization insights
"""

from .course_generator_dao import CourseGeneratorDAO

__all__ = ['CourseGeneratorDAO']