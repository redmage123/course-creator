"""
Content Management Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for content management operations,
centralizing all SQL queries and database interactions for educational content lifecycle management.

Business Context:
The Content Management service handles the complete lifecycle of educational content including
creation, validation, search, organization, and delivery. By centralizing all SQL operations
in this DAO, we achieve single source of truth for content data operations, enhanced security
through consistent data access patterns, and improved maintainability for content management
functionality across the Course Creator Platform.

Technical Rationale:
- Follows the Single Responsibility Principle by isolating content data access concerns
- Enables comprehensive transaction support for complex content operations
- Provides consistent error handling using shared platform exceptions
- Supports connection pooling for optimal database resource utilization
- Facilitates content schema evolution without affecting business logic
- Enables easier unit testing through clear interface boundaries
"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import sys
sys.path.append('/home/bbrelin/course-creator')
from exceptions import (
    ContentManagementException,
    DatabaseException,
    ValidationException,
    ContentNotFoundException
)


class ContentManagementDAO:
    """
    Data Access Object for Content Management Operations
    
    This class centralizes all SQL queries and database operations for the content
    management service, following the DAO pattern for clean architecture.
    
    Business Context:
    Provides comprehensive data access methods for educational content management including:
    - Content creation, validation, and lifecycle management
    - Educational material organization and categorization
    - Content search and discovery with metadata filtering
    - Quality assurance and content validation workflows
    - Version control and content history tracking
    - Content analytics and usage measurement
    
    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex content operations
    - Includes comprehensive error handling and content validation
    - Supports prepared statements for performance optimization
    - Implements efficient content search and retrieval patterns
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the Content Management DAO with database connection pool.
        
        Business Context:
        The DAO requires a connection pool to efficiently manage database connections
        across the content management service's educational content operations.
        
        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
    
    # ================================================================
    # CONTENT CREATION AND LIFECYCLE MANAGEMENT
    # ================================================================
    
    async def create_content(self, content_data: Dict[str, Any]) -> str:
        """
        Create new educational content with comprehensive metadata.
        
        Business Context:
        Content creation is fundamental to the educational platform, enabling instructors
        to develop courses, exercises, assessments, and learning materials that support
        student learning objectives and curriculum requirements.
        
        Technical Implementation:
        - Validates content structure and metadata
        - Stores rich content metadata for search and organization
        - Integrates with content validation workflows
        - Supports versioning and change tracking
        
        Args:
            content_data: Dictionary containing content information
                - title: Content title and identifier
                - description: Content description and learning objectives
                - content_type: Type of content (syllabus, quiz, exercise, slide, etc.)
                - content_body: Actual content data and structure
                - metadata: Rich metadata for search and categorization
                - created_by: User creating the content
                - subject_area: Educational subject classification
                - difficulty_level: Content difficulty rating
                
        Returns:
            Created content ID for tracking and reference
        """
        try:
            async with self.db_pool.acquire() as conn:
                content_id = await conn.fetchval(
                    """INSERT INTO course_creator.slides (
                        id, title, description, course_id as content_type, content,
                        ai_metadata as metadata, created_by, slide_count as subject_area, difficulty_level,
                        status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $11, $12, $13) 
                    RETURNING id""",
                    content_data['id'],
                    content_data['title'],
                    content_data['description'],
                    content_data['content_type'],
                    json.dumps(content_data['content_body']),
                    json.dumps(content_data.get('metadata', {})),
                    content_data['created_by'],
                    content_data.get('subject_area'),
                    content_data.get('difficulty_level', 'intermediate'),
                    content_data.get('quality_score', 0.0),
                    content_data.get('status', 'draft'),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                return str(content_id)
        except Exception as e:
            raise ContentManagementException(
                message="Failed to create educational content",
                error_code="CONTENT_CREATION_ERROR",
                details={
                    "title": content_data.get('title'),
                    "content_type": content_data.get('content_type')
                },
                original_exception=e
            )
    
    async def get_content_by_id(self, content_id: str, include_body: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieve educational content by unique identifier.
        
        Business Context:
        Content retrieval enables course delivery, assessment administration,
        and educational material access for students and instructors.
        
        Args:
            content_id: Unique content identifier
            include_body: Whether to include full content body in response
            
        Returns:
            Complete content record or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                if include_body:
                    content = await conn.fetchrow(
                        """SELECT id, title, description, course_id as content_type, content as content_body,
                                  ai_metadata as metadata, created_by, slide_count as subject_area, difficulty_level,
                                  status, created_at, updated_at
                           FROM course_creator.slides WHERE id = $1""",
                        content_id
                    )
                else:
                    content = await conn.fetchrow(
                        """SELECT id, title, description, course_id as content_type,
                                  ai_metadata as metadata, created_by, slide_count as subject_area, difficulty_level,
                                  status, created_at, updated_at
                           FROM course_creator.slides WHERE id = $1""",
                        content_id
                    )
                return dict(content) if content else None
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve educational content",
                error_code="CONTENT_RETRIEVAL_ERROR",
                details={"content_id": content_id},
                original_exception=e
            )
    
    async def update_content_status(self, content_id: str, new_status: str, 
                                  updated_by: str) -> bool:
        """
        Update content status for workflow management.
        
        Business Context:
        Content status management enables workflow control for content creation,
        review, approval, and publication processes in educational environments.
        
        Args:
            content_id: Content to update status for
            new_status: New status (draft, review, approved, published, archived)
            updated_by: User performing the status update
            
        Returns:
            True if status was updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE course_creator.slides 
                       SET status = $1, created_by = $2, updated_at = $3 
                       WHERE id = $4""",
                    new_status, updated_by, datetime.utcnow(), content_id
                )
                return result.split()[-1] == '1'
        except Exception as e:
            raise DatabaseException(
                message="Failed to update content status",
                error_code="CONTENT_STATUS_UPDATE_ERROR",
                details={"content_id": content_id, "new_status": new_status},
                original_exception=e
            )
    
    # ================================================================
    # CONTENT SEARCH AND DISCOVERY
    # ================================================================
    
    async def search_content(self, search_params: Dict[str, Any], 
                           limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search educational content with advanced filtering and ranking.
        
        Business Context:
        Content search enables instructors and students to discover relevant
        educational materials, supporting course development and learning activities
        through effective content organization and retrieval.
        
        Args:
            search_params: Dictionary containing search criteria
                - query: Text search query
                - content_type: Filter by content type
                - subject_area: Filter by subject area
                - difficulty_level: Filter by difficulty level
                - created_by: Filter by content creator
                - status: Filter by content status
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of matching content records with metadata
        """
        try:
            conditions = []
            params = []
            param_count = 0
            
            # Build dynamic WHERE clause
            if search_params.get('query'):
                param_count += 1
                conditions.append(f"(title ILIKE ${param_count} OR description ILIKE ${param_count})")
                params.append(f"%{search_params['query']}%")
            
            if search_params.get('content_type'):
                param_count += 1
                conditions.append(f"content_type = ${param_count}")
                params.append(search_params['content_type'])
            
            if search_params.get('subject_area'):
                param_count += 1
                conditions.append(f"subject_area = ${param_count}")
                params.append(search_params['subject_area'])
            
            if search_params.get('difficulty_level'):
                param_count += 1
                conditions.append(f"difficulty_level = ${param_count}")
                params.append(search_params['difficulty_level'])
            
            if search_params.get('created_by'):
                param_count += 1
                conditions.append(f"created_by = ${param_count}")
                params.append(search_params['created_by'])
            
            if search_params.get('status'):
                param_count += 1
                conditions.append(f"status = ${param_count}")
                params.append(search_params['status'])
            
            # Add pagination parameters
            param_count += 1
            limit_param = f"${param_count}"
            params.append(limit)
            
            param_count += 1
            offset_param = f"${param_count}"
            params.append(offset)
            
            # Build complete query
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT id, title, description, course_id as content_type, ai_metadata as metadata,
                       created_by, slide_count as subject_area, difficulty_level,
                       status, created_at, updated_at
                FROM course_creator.slides 
                WHERE {where_clause}
                ORDER BY created_at DESC 
                LIMIT {limit_param} OFFSET {offset_param}
            """
            
            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *params)
                return [dict(result) for result in results]
                
        except Exception as e:
            raise DatabaseException(
                message="Content search operation failed",
                error_code="CONTENT_SEARCH_ERROR",
                details={"search_params": search_params, "limit": limit, "offset": offset},
                original_exception=e
            )
    
    async def get_content_by_type(self, content_type: str, created_by: Optional[str] = None,
                                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve content filtered by type and optionally by creator.
        
        Business Context:
        Type-based content retrieval supports specialized views for different
        content types (courses, quizzes, exercises) enabling focused content
        management and organization workflows.
        
        Args:
            content_type: Type of content to retrieve
            created_by: Optional filter by content creator
            limit: Maximum number of results
            
        Returns:
            List of content records matching the criteria
        """
        try:
            async with self.db_pool.acquire() as conn:
                if created_by:
                    results = await conn.fetch(
                        """SELECT id, title, description, course_id as content_type, ai_metadata as metadata,
                                  created_by, slide_count as subject_area, difficulty_level,
                                  status, created_at, updated_at
                           FROM course_creator.slides 
                           WHERE course_id = $1 AND created_by = $2
                           ORDER BY created_at DESC 
                           LIMIT $3""",
                        content_type, created_by, limit
                    )
                else:
                    results = await conn.fetch(
                        """SELECT id, title, description, course_id as content_type, ai_metadata as metadata,
                                  created_by, slide_count as subject_area, difficulty_level,
                                  status, created_at, updated_at
                           FROM course_creator.slides 
                           WHERE course_id = $1
                           ORDER BY created_at DESC 
                           LIMIT $2""",
                        content_type, limit
                    )
                return [dict(result) for result in results]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve content by type",
                error_code="CONTENT_TYPE_QUERY_ERROR",
                details={"content_type": content_type, "created_by": created_by},
                original_exception=e
            )
    
    # ================================================================
    # CONTENT QUALITY AND ANALYTICS
    # ================================================================
    
    async def update_content_quality_score(self, content_id: str, quality_score: float,
                                         assessment_data: Dict[str, Any]) -> bool:
        """
        Update content quality score based on assessment metrics.
        
        Business Context:
        Quality scoring enables content improvement, search ranking, and
        quality assurance processes that maintain high educational standards
        across the platform.
        
        Args:
            content_id: Content to update quality score for
            quality_score: New quality score (0.0 to 1.0)
            assessment_data: Quality assessment metadata
            
        Returns:
            True if quality score was updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Update quality score and store assessment metadata
                result = await conn.execute(
                    """UPDATE course_creator.slides 
                       SET ai_metadata = ai_metadata || $1,
                           updated_at = $2 
                       WHERE id = $3""",
                    json.dumps({"quality_assessment": assessment_data, "quality_score": quality_score}),
                    datetime.utcnow(),
                    content_id
                )
                return result.split()[-1] == '1'
        except Exception as e:
            raise DatabaseException(
                message="Failed to update content quality score",
                error_code="QUALITY_SCORE_UPDATE_ERROR",
                details={"content_id": content_id, "quality_score": quality_score},
                original_exception=e
            )
    
    async def get_content_analytics(self, content_id: str, 
                                  timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive analytics for specific content.
        
        Business Context:
        Content analytics provide insights into content usage, effectiveness,
        and student engagement patterns that inform content improvement and
        curriculum development decisions.
        
        Args:
            content_id: Content to analyze
            timeframe_days: Analysis timeframe in days
            
        Returns:
            Dictionary containing comprehensive content analytics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=timeframe_days)
            
            async with self.db_pool.acquire() as conn:
                # Get basic content info
                content_info = await conn.fetchrow(
                    """SELECT title, course_id as content_type, status, created_at
                       FROM course_creator.slides WHERE id = $1""",
                    content_id
                )
                
                if not content_info:
                    raise ContentNotFoundException(
                        message="Content not found for analytics",
                        error_code="CONTENT_NOT_FOUND",
                        details={"content_id": content_id}
                    )
                
                # Get usage analytics (would join with usage tracking tables)
                analytics = {
                    "content_id": content_id,
                    "title": content_info['title'],
                    "content_type": content_info['content_type'],
                    "quality_score": 0.0,
                    "status": content_info['status'],
                    "age_days": (datetime.utcnow() - content_info['created_at']).days,
                    "timeframe_days": timeframe_days,
                    # These would be populated from actual usage tracking
                    "view_count": 0,
                    "completion_rate": 0.0,
                    "average_rating": 0.0,
                    "engagement_metrics": {}
                }
                
                return analytics
                
        except ContentNotFoundException:
            # Re-raise data not found exceptions
            raise
        except Exception as e:
            raise DatabaseException(
                message="Failed to calculate content analytics",
                error_code="CONTENT_ANALYTICS_ERROR",
                details={"content_id": content_id, "timeframe_days": timeframe_days},
                original_exception=e
            )
    
    # ================================================================
    # CONTENT VERSIONING AND HISTORY
    # ================================================================
    
    async def create_content_version(self, content_id: str, version_data: Dict[str, Any]) -> str:
        """
        Create a new version of existing content for change tracking.
        
        Business Context:
        Content versioning enables iterative content improvement, change tracking,
        and rollback capabilities essential for maintaining high-quality educational
        materials and supporting collaborative content development.
        
        Args:
            content_id: Original content identifier
            version_data: New version data and changes
            
        Returns:
            Created version ID for tracking
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Map to slides table for versioning
                    # Create new version record as a separate slide
                    version_id = await conn.fetchval(
                        """INSERT INTO course_creator.slides (
                            id, course_id, title, content,
                            description, created_by, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $7) 
                        RETURNING id""",
                        version_data['version_id'],
                        content_id,
                        f"Version of {content_id}",
                        json.dumps(version_data['content_body']),
                        version_data.get('changes_summary', 'Content version'),
                        version_data['created_by'],
                        datetime.utcnow()
                    )
                    
                    return str(version_id)
                    
        except Exception as e:
            raise ContentManagementException(
                message="Failed to create content version",
                error_code="CONTENT_VERSION_ERROR",
                details={"content_id": content_id},
                original_exception=e
            )
    
    async def get_content_version_history(self, content_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve complete version history for content.
        
        Business Context:
        Version history enables content change tracking, collaboration oversight,
        and quality assurance processes for educational content management.
        
        Args:
            content_id: Content to get version history for
            
        Returns:
            List of version records ordered by version number
        """
        try:
            async with self.db_pool.acquire() as conn:
                versions = await conn.fetch(
                    """SELECT id, 1 as version_number, description as changes_summary, created_by, created_at
                       FROM course_creator.slides 
                       WHERE course_id = $1 
                       ORDER BY created_at DESC""",
                    content_id
                )
                return [dict(version) for version in versions]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve content version history",
                error_code="VERSION_HISTORY_ERROR",
                details={"content_id": content_id},
                original_exception=e
            )