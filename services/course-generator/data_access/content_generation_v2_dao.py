"""
Content Generation V2 Data Access Object (DAO)

WHAT: Data Access Object implementing the DAO pattern for AI-powered content generation V2
WHERE: Used by course-generator service for advanced content generation operations
WHY: Centralizes all SQL queries and database interactions for the enhanced content
     generation system, enabling request tracking, quality scoring, templates,
     refinements, batch operations, and analytics

Enhancement 4: AI-Powered Content Generation V2

Business Context:
The Content Generation V2 system provides advanced AI-powered educational content creation
with enhanced quality metrics, customizable templates, iterative refinement workflows,
and comprehensive analytics. By centralizing all SQL operations in this DAO, we achieve:
- Single source of truth for all generation V2 database queries
- Enhanced tracking of generation requests, results, and quality metrics
- Improved performance through optimized query patterns
- Better maintainability and testing capabilities
- Clear separation between generation logic and data persistence

Technical Rationale:
- Follows the Single Responsibility Principle by isolating generation V2 data access
- Enables comprehensive transaction support for complex generation operations
- Provides consistent error handling using custom exceptions
- Supports connection pooling for optimal database resource utilization
- Facilitates schema evolution without affecting generation logic
"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
import json
import sys

sys.path.append('/app/shared')
from exceptions import (
    CourseCreatorBaseException,
    DatabaseException,
    ValidationException,
    ContentException,
    ContentNotFoundException
)

# Import domain entities for type hints
from course_generator.domain.entities.content_generation_v2 import (
    GenerationRequest,
    GenerationResult,
    ContentQualityScore,
    GenerationTemplate,
    ContentRefinement,
    BatchGeneration,
    GenerationAnalytics,
    GenerationContentType,
    GenerationStatus,
    QualityLevel,
    RefinementType,
    BatchStatus,
    TemplateCategory,
    ContentGenerationException,
    TemplateNotFoundException
)


class ContentGenerationV2DAO:
    """
    Data Access Object for Content Generation V2 Operations

    WHAT: Centralizes all SQL queries and database operations for enhanced content generation
    WHERE: Used by ContentGenerationService for all database interactions
    WHY: Follows DAO pattern for clean architecture, enabling testability and maintainability

    Business Context:
    Provides comprehensive data access methods for:
    - Generation request tracking with full parameters and status
    - Generation result storage with raw and processed content
    - Multi-dimensional quality scoring for content evaluation
    - Customizable template management for consistent generation
    - Content refinement workflow for iterative improvements
    - Batch generation operations for bulk content creation
    - Analytics tracking for performance and quality monitoring

    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex operations
    - Includes comprehensive error handling and validation
    - Supports prepared statements for performance optimization
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the Content Generation V2 DAO with database connection pool.

        WHAT: Constructor that initializes database connection pool
        WHERE: Called when creating DAO instance
        WHY: Enables efficient database connection management

        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # GENERATION REQUEST OPERATIONS
    # ================================================================

    async def create_generation_request(
        self,
        request: GenerationRequest
    ) -> UUID:
        """
        Create a new generation request record.

        WHAT: Inserts a generation request into the database
        WHERE: Called when initiating content generation
        WHY: Tracks generation requests for auditing, caching, and analytics

        Args:
            request: GenerationRequest entity with all parameters

        Returns:
            UUID of created request

        Raises:
            ContentException: If creation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    """INSERT INTO generation_requests (
                        id, course_id, content_type, requester_id, organization_id,
                        module_id, template_id, status, parameters, difficulty_level,
                        target_audience, language, model_name, max_tokens, temperature,
                        use_rag, use_cache, max_retries, retry_count, timeout_seconds,
                        started_at, completed_at, result_id, error_message,
                        input_tokens, output_tokens, estimated_cost,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                        $21, $22, $23, $24, $25, $26, $27, $28, $29
                    ) RETURNING id""",
                    request.id,
                    request.course_id,
                    request.content_type.value,
                    request.requester_id,
                    request.organization_id,
                    request.module_id,
                    request.template_id,
                    request.status.value,
                    json.dumps(request.parameters),
                    request.difficulty_level,
                    request.target_audience,
                    request.language,
                    request.model_name,
                    request.max_tokens,
                    request.temperature,
                    request.use_rag,
                    request.use_cache,
                    request.max_retries,
                    request.retry_count,
                    request.timeout_seconds,
                    request.started_at,
                    request.completed_at,
                    request.result_id,
                    request.error_message,
                    request.input_tokens,
                    request.output_tokens,
                    float(request.estimated_cost),
                    request.created_at,
                    request.updated_at
                )
                return result
        except Exception as e:
            raise ContentException(
                message="Failed to create generation request",
                error_code="GENERATION_REQUEST_CREATE_ERROR",
                details={
                    "course_id": str(request.course_id),
                    "content_type": request.content_type.value
                },
                original_exception=e
            )

    async def get_generation_request(self, request_id: UUID) -> Optional[GenerationRequest]:
        """
        Retrieve a generation request by ID.

        WHAT: Fetches a generation request record from database
        WHERE: Called when checking request status or processing
        WHY: Enables request tracking and status monitoring

        Args:
            request_id: UUID of request to retrieve

        Returns:
            GenerationRequest entity or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT * FROM generation_requests WHERE id = $1""",
                    request_id
                )
                if not row:
                    return None
                return self._row_to_generation_request(dict(row))
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve generation request",
                error_code="GENERATION_REQUEST_GET_ERROR",
                details={"request_id": str(request_id)},
                original_exception=e
            )

    async def update_generation_request(self, request: GenerationRequest) -> bool:
        """
        Update a generation request record.

        WHAT: Updates generation request in database
        WHERE: Called when request status changes
        WHY: Tracks request lifecycle and results

        Args:
            request: GenerationRequest entity with updated values

        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE generation_requests SET
                        status = $1, started_at = $2, completed_at = $3,
                        result_id = $4, error_message = $5, retry_count = $6,
                        input_tokens = $7, output_tokens = $8, estimated_cost = $9,
                        updated_at = $10
                    WHERE id = $11""",
                    request.status.value,
                    request.started_at,
                    request.completed_at,
                    request.result_id,
                    request.error_message,
                    request.retry_count,
                    request.input_tokens,
                    request.output_tokens,
                    float(request.estimated_cost),
                    datetime.utcnow(),
                    request.id
                )
                return "UPDATE 1" in result
        except Exception as e:
            raise DatabaseException(
                message="Failed to update generation request",
                error_code="GENERATION_REQUEST_UPDATE_ERROR",
                details={"request_id": str(request.id)},
                original_exception=e
            )

    async def get_pending_requests(
        self,
        limit: int = 10
    ) -> List[GenerationRequest]:
        """
        Get pending generation requests for processing.

        WHAT: Retrieves pending requests ordered by creation time
        WHERE: Called by job processor to find work
        WHY: Enables queue-based processing of requests

        Args:
            limit: Maximum number of requests to return

        Returns:
            List of pending GenerationRequest entities
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT * FROM generation_requests
                       WHERE status = 'pending'
                       ORDER BY created_at ASC
                       LIMIT $1""",
                    limit
                )
                return [self._row_to_generation_request(dict(row)) for row in rows]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve pending requests",
                error_code="PENDING_REQUESTS_ERROR",
                details={"limit": limit},
                original_exception=e
            )

    async def get_requests_by_course(
        self,
        course_id: UUID,
        content_type: Optional[GenerationContentType] = None,
        limit: int = 50
    ) -> List[GenerationRequest]:
        """
        Get generation requests for a specific course.

        WHAT: Retrieves requests filtered by course and optionally content type
        WHERE: Called when viewing course generation history
        WHY: Enables tracking of course content generation

        Args:
            course_id: Course to filter by
            content_type: Optional content type filter
            limit: Maximum number of requests to return

        Returns:
            List of GenerationRequest entities
        """
        try:
            async with self.db_pool.acquire() as conn:
                if content_type:
                    rows = await conn.fetch(
                        """SELECT * FROM generation_requests
                           WHERE course_id = $1 AND content_type = $2
                           ORDER BY created_at DESC
                           LIMIT $3""",
                        course_id, content_type.value, limit
                    )
                else:
                    rows = await conn.fetch(
                        """SELECT * FROM generation_requests
                           WHERE course_id = $1
                           ORDER BY created_at DESC
                           LIMIT $2""",
                        course_id, limit
                    )
                return [self._row_to_generation_request(dict(row)) for row in rows]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve course requests",
                error_code="COURSE_REQUESTS_ERROR",
                details={"course_id": str(course_id)},
                original_exception=e
            )

    # ================================================================
    # GENERATION RESULT OPERATIONS
    # ================================================================

    async def create_generation_result(
        self,
        result: GenerationResult
    ) -> UUID:
        """
        Create a new generation result record.

        WHAT: Inserts generated content into database
        WHERE: Called when generation completes successfully
        WHY: Stores generated content for retrieval and caching

        Args:
            result: GenerationResult entity with content

        Returns:
            UUID of created result
        """
        try:
            async with self.db_pool.acquire() as conn:
                result_id = await conn.fetchval(
                    """INSERT INTO generation_results (
                        id, request_id, course_id, content_type,
                        raw_output, processed_content, quality_score_id,
                        quality_level, model_used, generation_method,
                        rag_context_used, cached, cache_key, version,
                        parent_result_id, created_at, expires_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17
                    ) RETURNING id""",
                    result.id,
                    result.request_id,
                    result.course_id,
                    result.content_type.value,
                    result.raw_output,
                    json.dumps(result.processed_content),
                    result.quality_score_id,
                    result.quality_level.value,
                    result.model_used,
                    result.generation_method,
                    result.rag_context_used,
                    result.cached,
                    result.cache_key,
                    result.version,
                    result.parent_result_id,
                    result.created_at,
                    result.expires_at
                )
                return result_id
        except Exception as e:
            raise ContentException(
                message="Failed to create generation result",
                error_code="GENERATION_RESULT_CREATE_ERROR",
                details={
                    "request_id": str(result.request_id),
                    "content_type": result.content_type.value
                },
                original_exception=e
            )

    async def get_generation_result(self, result_id: UUID) -> Optional[GenerationResult]:
        """
        Retrieve a generation result by ID.

        WHAT: Fetches generated content from database
        WHERE: Called when retrieving generated content
        WHY: Provides access to stored generated content

        Args:
            result_id: UUID of result to retrieve

        Returns:
            GenerationResult entity or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT * FROM generation_results WHERE id = $1""",
                    result_id
                )
                if not row:
                    return None
                return self._row_to_generation_result(dict(row))
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve generation result",
                error_code="GENERATION_RESULT_GET_ERROR",
                details={"result_id": str(result_id)},
                original_exception=e
            )

    async def get_result_by_cache_key(
        self,
        cache_key: str
    ) -> Optional[GenerationResult]:
        """
        Retrieve a cached generation result by cache key.

        WHAT: Fetches cached content by key
        WHERE: Called when checking cache before generation
        WHY: Enables cache-based response optimization

        Args:
            cache_key: Cache key to look up

        Returns:
            GenerationResult entity or None if not found/expired
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT * FROM generation_results
                       WHERE cache_key = $1
                       AND (expires_at IS NULL OR expires_at > $2)
                       ORDER BY created_at DESC
                       LIMIT 1""",
                    cache_key,
                    datetime.utcnow()
                )
                if not row:
                    return None
                return self._row_to_generation_result(dict(row))
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve cached result",
                error_code="CACHE_LOOKUP_ERROR",
                details={"cache_key": cache_key},
                original_exception=e
            )

    async def update_result_quality(
        self,
        result_id: UUID,
        quality_score_id: UUID,
        quality_level: QualityLevel
    ) -> bool:
        """
        Update quality assessment for a generation result.

        WHAT: Links quality score to result
        WHERE: Called after quality scoring completes
        WHY: Associates quality metrics with generated content

        Args:
            result_id: Result to update
            quality_score_id: ID of quality score
            quality_level: Calculated quality level

        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE generation_results SET
                        quality_score_id = $1, quality_level = $2
                    WHERE id = $3""",
                    quality_score_id,
                    quality_level.value,
                    result_id
                )
                return "UPDATE 1" in result
        except Exception as e:
            raise DatabaseException(
                message="Failed to update result quality",
                error_code="RESULT_QUALITY_UPDATE_ERROR",
                details={"result_id": str(result_id)},
                original_exception=e
            )

    # ================================================================
    # CONTENT QUALITY SCORE OPERATIONS
    # ================================================================

    async def create_quality_score(
        self,
        score: ContentQualityScore
    ) -> UUID:
        """
        Create a new quality score record.

        WHAT: Inserts quality assessment into database
        WHERE: Called after content quality evaluation
        WHY: Tracks detailed quality metrics for generated content

        Args:
            score: ContentQualityScore entity with dimension scores

        Returns:
            UUID of created score
        """
        try:
            async with self.db_pool.acquire() as conn:
                score_id = await conn.fetchval(
                    """INSERT INTO content_quality_scores (
                        id, result_id, accuracy_score, relevance_score,
                        completeness_score, clarity_score, structure_score,
                        engagement_score, difficulty_alignment_score,
                        overall_score, quality_level, weights,
                        scoring_method, scorer_id, confidence,
                        strengths, weaknesses, improvement_suggestions,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
                    ) RETURNING id""",
                    score.id,
                    score.result_id,
                    score.accuracy_score,
                    score.relevance_score,
                    score.completeness_score,
                    score.clarity_score,
                    score.structure_score,
                    score.engagement_score,
                    score.difficulty_alignment_score,
                    score.overall_score,
                    score.quality_level.value,
                    json.dumps(score.weights),
                    score.scoring_method,
                    score.scorer_id,
                    float(score.confidence),
                    json.dumps(score.strengths),
                    json.dumps(score.weaknesses),
                    json.dumps(score.improvement_suggestions),
                    score.created_at,
                    score.updated_at
                )
                return score_id
        except Exception as e:
            raise ContentException(
                message="Failed to create quality score",
                error_code="QUALITY_SCORE_CREATE_ERROR",
                details={"result_id": str(score.result_id)},
                original_exception=e
            )

    async def get_quality_score(
        self,
        score_id: UUID
    ) -> Optional[ContentQualityScore]:
        """
        Retrieve a quality score by ID.

        WHAT: Fetches quality assessment from database
        WHERE: Called when viewing content quality
        WHY: Provides access to detailed quality metrics

        Args:
            score_id: UUID of score to retrieve

        Returns:
            ContentQualityScore entity or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT * FROM content_quality_scores WHERE id = $1""",
                    score_id
                )
                if not row:
                    return None
                return self._row_to_quality_score(dict(row))
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve quality score",
                error_code="QUALITY_SCORE_GET_ERROR",
                details={"score_id": str(score_id)},
                original_exception=e
            )

    async def get_quality_score_by_result(
        self,
        result_id: UUID
    ) -> Optional[ContentQualityScore]:
        """
        Retrieve quality score for a generation result.

        WHAT: Fetches quality assessment linked to result
        WHERE: Called when viewing result quality
        WHY: Gets quality metrics for specific content

        Args:
            result_id: Result to get score for

        Returns:
            ContentQualityScore entity or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT * FROM content_quality_scores WHERE result_id = $1""",
                    result_id
                )
                if not row:
                    return None
                return self._row_to_quality_score(dict(row))
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve result quality score",
                error_code="RESULT_QUALITY_GET_ERROR",
                details={"result_id": str(result_id)},
                original_exception=e
            )

    async def update_quality_score(
        self,
        score: ContentQualityScore
    ) -> bool:
        """
        Update a quality score record.

        WHAT: Updates quality assessment in database
        WHERE: Called after manual review or recalculation
        WHY: Allows quality score updates and manual overrides

        Args:
            score: ContentQualityScore entity with updated values

        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE content_quality_scores SET
                        accuracy_score = $1, relevance_score = $2,
                        completeness_score = $3, clarity_score = $4,
                        structure_score = $5, engagement_score = $6,
                        difficulty_alignment_score = $7, overall_score = $8,
                        quality_level = $9, scoring_method = $10,
                        scorer_id = $11, confidence = $12,
                        strengths = $13, weaknesses = $14,
                        improvement_suggestions = $15, updated_at = $16
                    WHERE id = $17""",
                    score.accuracy_score,
                    score.relevance_score,
                    score.completeness_score,
                    score.clarity_score,
                    score.structure_score,
                    score.engagement_score,
                    score.difficulty_alignment_score,
                    score.overall_score,
                    score.quality_level.value,
                    score.scoring_method,
                    score.scorer_id,
                    float(score.confidence),
                    json.dumps(score.strengths),
                    json.dumps(score.weaknesses),
                    json.dumps(score.improvement_suggestions),
                    datetime.utcnow(),
                    score.id
                )
                return "UPDATE 1" in result
        except Exception as e:
            raise DatabaseException(
                message="Failed to update quality score",
                error_code="QUALITY_SCORE_UPDATE_ERROR",
                details={"score_id": str(score.id)},
                original_exception=e
            )

    # ================================================================
    # GENERATION TEMPLATE OPERATIONS
    # ================================================================

    async def create_template(
        self,
        template: GenerationTemplate
    ) -> UUID:
        """
        Create a new generation template.

        WHAT: Inserts template into database
        WHERE: Called when creating new template
        WHY: Stores customizable generation templates

        Args:
            template: GenerationTemplate entity

        Returns:
            UUID of created template
        """
        try:
            async with self.db_pool.acquire() as conn:
                template_id = await conn.fetchval(
                    """INSERT INTO generation_templates (
                        id, name, description, content_type, category,
                        system_prompt, user_prompt_template, output_schema,
                        required_variables, default_parameters, difficulty_levels,
                        target_audiences, creator_id, organization_id, is_global,
                        is_active, is_archived, min_quality_score,
                        auto_retry_on_low_quality, max_auto_retries,
                        usage_count, success_count, avg_quality_score,
                        created_at, updated_at, archived_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                        $21, $22, $23, $24, $25, $26
                    ) RETURNING id""",
                    template.id,
                    template.name,
                    template.description,
                    template.content_type.value,
                    template.category.value,
                    template.system_prompt,
                    template.user_prompt_template,
                    json.dumps(template.output_schema),
                    json.dumps(template.required_variables),
                    json.dumps(template.default_parameters),
                    json.dumps(template.difficulty_levels),
                    json.dumps(template.target_audiences),
                    template.creator_id,
                    template.organization_id,
                    template.is_global,
                    template.is_active,
                    template.is_archived,
                    template.min_quality_score,
                    template.auto_retry_on_low_quality,
                    template.max_auto_retries,
                    template.usage_count,
                    template.success_count,
                    float(template.avg_quality_score),
                    template.created_at,
                    template.updated_at,
                    template.archived_at
                )
                return template_id
        except Exception as e:
            raise ContentException(
                message="Failed to create generation template",
                error_code="TEMPLATE_CREATE_ERROR",
                details={"name": template.name},
                original_exception=e
            )

    async def get_template(self, template_id: UUID) -> Optional[GenerationTemplate]:
        """
        Retrieve a generation template by ID.

        WHAT: Fetches template from database
        WHERE: Called when using template for generation
        WHY: Loads template configuration for generation

        Args:
            template_id: UUID of template to retrieve

        Returns:
            GenerationTemplate entity or None if not found

        Raises:
            TemplateNotFoundException: If template not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT * FROM generation_templates WHERE id = $1""",
                    template_id
                )
                if not row:
                    return None
                return self._row_to_template(dict(row))
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve template",
                error_code="TEMPLATE_GET_ERROR",
                details={"template_id": str(template_id)},
                original_exception=e
            )

    async def get_templates(
        self,
        content_type: Optional[GenerationContentType] = None,
        category: Optional[TemplateCategory] = None,
        organization_id: Optional[UUID] = None,
        include_global: bool = True,
        active_only: bool = True
    ) -> List[GenerationTemplate]:
        """
        Retrieve generation templates with filters.

        WHAT: Fetches templates matching criteria
        WHERE: Called when listing available templates
        WHY: Provides template discovery and selection

        Args:
            content_type: Optional content type filter
            category: Optional category filter
            organization_id: Organization to include templates for
            include_global: Whether to include global templates
            active_only: Whether to include only active templates

        Returns:
            List of GenerationTemplate entities
        """
        try:
            conditions = []
            params = []
            param_idx = 1

            if content_type:
                conditions.append(f"content_type = ${param_idx}")
                params.append(content_type.value)
                param_idx += 1

            if category:
                conditions.append(f"category = ${param_idx}")
                params.append(category.value)
                param_idx += 1

            if active_only:
                conditions.append("is_active = TRUE")
                conditions.append("is_archived = FALSE")

            # Organization scope
            org_conditions = []
            if organization_id:
                org_conditions.append(f"organization_id = ${param_idx}")
                params.append(organization_id)
                param_idx += 1
            if include_global:
                org_conditions.append("is_global = TRUE")

            if org_conditions:
                conditions.append(f"({' OR '.join(org_conditions)})")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""SELECT * FROM generation_templates
                        {where_clause}
                        ORDER BY usage_count DESC, name ASC""",
                    *params
                )
                return [self._row_to_template(dict(row)) for row in rows]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve templates",
                error_code="TEMPLATES_LIST_ERROR",
                details={
                    "content_type": content_type.value if content_type else None,
                    "category": category.value if category else None
                },
                original_exception=e
            )

    async def update_template(self, template: GenerationTemplate) -> bool:
        """
        Update a generation template.

        WHAT: Updates template in database
        WHERE: Called when modifying template
        WHY: Allows template configuration changes

        Args:
            template: GenerationTemplate entity with updates

        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE generation_templates SET
                        name = $1, description = $2, system_prompt = $3,
                        user_prompt_template = $4, output_schema = $5,
                        required_variables = $6, default_parameters = $7,
                        difficulty_levels = $8, target_audiences = $9,
                        is_active = $10, is_archived = $11,
                        min_quality_score = $12, auto_retry_on_low_quality = $13,
                        max_auto_retries = $14, usage_count = $15,
                        success_count = $16, avg_quality_score = $17,
                        updated_at = $18, archived_at = $19
                    WHERE id = $20""",
                    template.name,
                    template.description,
                    template.system_prompt,
                    template.user_prompt_template,
                    json.dumps(template.output_schema),
                    json.dumps(template.required_variables),
                    json.dumps(template.default_parameters),
                    json.dumps(template.difficulty_levels),
                    json.dumps(template.target_audiences),
                    template.is_active,
                    template.is_archived,
                    template.min_quality_score,
                    template.auto_retry_on_low_quality,
                    template.max_auto_retries,
                    template.usage_count,
                    template.success_count,
                    float(template.avg_quality_score),
                    datetime.utcnow(),
                    template.archived_at,
                    template.id
                )
                return "UPDATE 1" in result
        except Exception as e:
            raise DatabaseException(
                message="Failed to update template",
                error_code="TEMPLATE_UPDATE_ERROR",
                details={"template_id": str(template.id)},
                original_exception=e
            )

    async def increment_template_usage(
        self,
        template_id: UUID,
        success: bool,
        quality_score: Optional[int] = None
    ) -> bool:
        """
        Increment template usage counters.

        WHAT: Updates template usage statistics
        WHERE: Called after using template for generation
        WHY: Tracks template effectiveness

        Args:
            template_id: Template that was used
            success: Whether generation succeeded
            quality_score: Optional quality score of result

        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                if success and quality_score is not None:
                    # Update usage count, success count, and rolling average
                    result = await conn.execute(
                        """UPDATE generation_templates SET
                            usage_count = usage_count + 1,
                            success_count = success_count + 1,
                            avg_quality_score = (
                                (avg_quality_score * success_count + $1) /
                                (success_count + 1)
                            ),
                            updated_at = $2
                        WHERE id = $3""",
                        quality_score,
                        datetime.utcnow(),
                        template_id
                    )
                elif success:
                    result = await conn.execute(
                        """UPDATE generation_templates SET
                            usage_count = usage_count + 1,
                            success_count = success_count + 1,
                            updated_at = $1
                        WHERE id = $2""",
                        datetime.utcnow(),
                        template_id
                    )
                else:
                    result = await conn.execute(
                        """UPDATE generation_templates SET
                            usage_count = usage_count + 1,
                            updated_at = $1
                        WHERE id = $2""",
                        datetime.utcnow(),
                        template_id
                    )
                return "UPDATE 1" in result
        except Exception as e:
            raise DatabaseException(
                message="Failed to update template usage",
                error_code="TEMPLATE_USAGE_UPDATE_ERROR",
                details={"template_id": str(template_id)},
                original_exception=e
            )

    # ================================================================
    # CONTENT REFINEMENT OPERATIONS
    # ================================================================

    async def create_refinement(
        self,
        refinement: ContentRefinement
    ) -> UUID:
        """
        Create a new content refinement record.

        WHAT: Inserts refinement request into database
        WHERE: Called when user requests content improvement
        WHY: Tracks iterative content refinement workflow

        Args:
            refinement: ContentRefinement entity

        Returns:
            UUID of created refinement
        """
        try:
            async with self.db_pool.acquire() as conn:
                refinement_id = await conn.fetchval(
                    """INSERT INTO content_refinements (
                        id, result_id, refinement_type, requester_id,
                        feedback, specific_instructions, target_sections,
                        preserve_structure, max_changes, refined_result_id,
                        status, changes_made, original_quality_score,
                        refined_quality_score, quality_improvement,
                        iteration_number, max_iterations,
                        created_at, completed_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19
                    ) RETURNING id""",
                    refinement.id,
                    refinement.result_id,
                    refinement.refinement_type.value,
                    refinement.requester_id,
                    refinement.feedback,
                    refinement.specific_instructions,
                    json.dumps(refinement.target_sections),
                    refinement.preserve_structure,
                    refinement.max_changes,
                    refinement.refined_result_id,
                    refinement.status.value,
                    json.dumps(refinement.changes_made),
                    refinement.original_quality_score,
                    refinement.refined_quality_score,
                    refinement.quality_improvement,
                    refinement.iteration_number,
                    refinement.max_iterations,
                    refinement.created_at,
                    refinement.completed_at
                )
                return refinement_id
        except Exception as e:
            raise ContentException(
                message="Failed to create refinement",
                error_code="REFINEMENT_CREATE_ERROR",
                details={"result_id": str(refinement.result_id)},
                original_exception=e
            )

    async def get_refinement(
        self,
        refinement_id: UUID
    ) -> Optional[ContentRefinement]:
        """
        Retrieve a content refinement by ID.

        WHAT: Fetches refinement from database
        WHERE: Called when checking refinement status
        WHY: Provides access to refinement details

        Args:
            refinement_id: UUID of refinement to retrieve

        Returns:
            ContentRefinement entity or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT * FROM content_refinements WHERE id = $1""",
                    refinement_id
                )
                if not row:
                    return None
                return self._row_to_refinement(dict(row))
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve refinement",
                error_code="REFINEMENT_GET_ERROR",
                details={"refinement_id": str(refinement_id)},
                original_exception=e
            )

    async def get_refinements_for_result(
        self,
        result_id: UUID
    ) -> List[ContentRefinement]:
        """
        Get all refinements for a generation result.

        WHAT: Fetches refinement history for result
        WHERE: Called when viewing refinement history
        WHY: Shows iterative improvement history

        Args:
            result_id: Result to get refinements for

        Returns:
            List of ContentRefinement entities
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT * FROM content_refinements
                       WHERE result_id = $1
                       ORDER BY iteration_number ASC""",
                    result_id
                )
                return [self._row_to_refinement(dict(row)) for row in rows]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve result refinements",
                error_code="RESULT_REFINEMENTS_ERROR",
                details={"result_id": str(result_id)},
                original_exception=e
            )

    async def update_refinement(
        self,
        refinement: ContentRefinement
    ) -> bool:
        """
        Update a content refinement record.

        WHAT: Updates refinement in database
        WHERE: Called when refinement completes
        WHY: Records refinement outcome

        Args:
            refinement: ContentRefinement entity with updates

        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE content_refinements SET
                        refined_result_id = $1, status = $2, changes_made = $3,
                        refined_quality_score = $4, quality_improvement = $5,
                        completed_at = $6
                    WHERE id = $7""",
                    refinement.refined_result_id,
                    refinement.status.value,
                    json.dumps(refinement.changes_made),
                    refinement.refined_quality_score,
                    refinement.quality_improvement,
                    refinement.completed_at,
                    refinement.id
                )
                return "UPDATE 1" in result
        except Exception as e:
            raise DatabaseException(
                message="Failed to update refinement",
                error_code="REFINEMENT_UPDATE_ERROR",
                details={"refinement_id": str(refinement.id)},
                original_exception=e
            )

    async def count_refinements_for_result(
        self,
        result_id: UUID
    ) -> int:
        """
        Count refinements for a result.

        WHAT: Gets refinement count for result
        WHERE: Called when checking if more refinements allowed
        WHY: Enforces maximum refinement limit

        Args:
            result_id: Result to count refinements for

        Returns:
            Number of refinements
        """
        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.fetchval(
                    """SELECT COUNT(*) FROM content_refinements
                       WHERE result_id = $1""",
                    result_id
                )
                return count or 0
        except Exception as e:
            raise DatabaseException(
                message="Failed to count refinements",
                error_code="REFINEMENT_COUNT_ERROR",
                details={"result_id": str(result_id)},
                original_exception=e
            )

    # ================================================================
    # BATCH GENERATION OPERATIONS
    # ================================================================

    async def create_batch(self, batch: BatchGeneration) -> UUID:
        """
        Create a new batch generation record.

        WHAT: Inserts batch into database
        WHERE: Called when creating batch generation
        WHY: Tracks bulk content generation operations

        Args:
            batch: BatchGeneration entity

        Returns:
            UUID of created batch
        """
        try:
            async with self.db_pool.acquire() as conn:
                batch_id = await conn.fetchval(
                    """INSERT INTO batch_generations (
                        id, name, description, course_id, requester_id,
                        organization_id, shared_parameters, content_types,
                        target_modules, max_batch_size, parallel_workers,
                        request_ids, status, total_items, completed_items,
                        failed_items, progress_percentage, current_item_index,
                        started_at, completed_at, estimated_completion,
                        total_estimated_cost, actual_cost, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                        $21, $22, $23, $24, $25
                    ) RETURNING id""",
                    batch.id,
                    batch.name,
                    batch.description,
                    batch.course_id,
                    batch.requester_id,
                    batch.organization_id,
                    json.dumps(batch.shared_parameters),
                    json.dumps([ct.value for ct in batch.content_types]),
                    json.dumps([str(m) for m in batch.target_modules]),
                    batch.max_batch_size,
                    batch.parallel_workers,
                    json.dumps([str(r) for r in batch.request_ids]),
                    batch.status.value,
                    batch.total_items,
                    batch.completed_items,
                    batch.failed_items,
                    float(batch.progress_percentage),
                    batch.current_item_index,
                    batch.started_at,
                    batch.completed_at,
                    batch.estimated_completion,
                    float(batch.total_estimated_cost),
                    float(batch.actual_cost),
                    batch.created_at,
                    batch.updated_at
                )
                return batch_id
        except Exception as e:
            raise ContentException(
                message="Failed to create batch generation",
                error_code="BATCH_CREATE_ERROR",
                details={"name": batch.name},
                original_exception=e
            )

    async def get_batch(self, batch_id: UUID) -> Optional[BatchGeneration]:
        """
        Retrieve a batch generation by ID.

        WHAT: Fetches batch from database
        WHERE: Called when checking batch status
        WHY: Provides access to batch details

        Args:
            batch_id: UUID of batch to retrieve

        Returns:
            BatchGeneration entity or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT * FROM batch_generations WHERE id = $1""",
                    batch_id
                )
                if not row:
                    return None
                return self._row_to_batch(dict(row))
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve batch",
                error_code="BATCH_GET_ERROR",
                details={"batch_id": str(batch_id)},
                original_exception=e
            )

    async def update_batch(self, batch: BatchGeneration) -> bool:
        """
        Update a batch generation record.

        WHAT: Updates batch in database
        WHERE: Called when batch status/progress changes
        WHY: Tracks batch execution progress

        Args:
            batch: BatchGeneration entity with updates

        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE batch_generations SET
                        request_ids = $1, status = $2, total_items = $3,
                        completed_items = $4, failed_items = $5,
                        progress_percentage = $6, current_item_index = $7,
                        started_at = $8, completed_at = $9,
                        estimated_completion = $10, actual_cost = $11,
                        updated_at = $12
                    WHERE id = $13""",
                    json.dumps([str(r) for r in batch.request_ids]),
                    batch.status.value,
                    batch.total_items,
                    batch.completed_items,
                    batch.failed_items,
                    float(batch.progress_percentage),
                    batch.current_item_index,
                    batch.started_at,
                    batch.completed_at,
                    batch.estimated_completion,
                    float(batch.actual_cost),
                    datetime.utcnow(),
                    batch.id
                )
                return "UPDATE 1" in result
        except Exception as e:
            raise DatabaseException(
                message="Failed to update batch",
                error_code="BATCH_UPDATE_ERROR",
                details={"batch_id": str(batch.id)},
                original_exception=e
            )

    async def get_active_batches(
        self,
        organization_id: Optional[UUID] = None
    ) -> List[BatchGeneration]:
        """
        Get active batch generations.

        WHAT: Fetches batches in processing state
        WHERE: Called for monitoring active batches
        WHY: Enables batch progress monitoring

        Args:
            organization_id: Optional organization filter

        Returns:
            List of active BatchGeneration entities
        """
        try:
            async with self.db_pool.acquire() as conn:
                if organization_id:
                    rows = await conn.fetch(
                        """SELECT * FROM batch_generations
                           WHERE status IN ('created', 'queued', 'processing')
                           AND organization_id = $1
                           ORDER BY created_at DESC""",
                        organization_id
                    )
                else:
                    rows = await conn.fetch(
                        """SELECT * FROM batch_generations
                           WHERE status IN ('created', 'queued', 'processing')
                           ORDER BY created_at DESC"""
                    )
                return [self._row_to_batch(dict(row)) for row in rows]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve active batches",
                error_code="ACTIVE_BATCHES_ERROR",
                details={},
                original_exception=e
            )

    # ================================================================
    # GENERATION ANALYTICS OPERATIONS
    # ================================================================

    async def get_or_create_analytics(
        self,
        organization_id: Optional[UUID] = None,
        period_start: Optional[datetime] = None
    ) -> GenerationAnalytics:
        """
        Get or create analytics record for period.

        WHAT: Retrieves or creates analytics record
        WHERE: Called when recording generation metrics
        WHY: Ensures analytics record exists for updates

        Args:
            organization_id: Organization to track (None for global)
            period_start: Start of period (default: start of current day)

        Returns:
            GenerationAnalytics entity
        """
        if period_start is None:
            period_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        try:
            async with self.db_pool.acquire() as conn:
                # Try to get existing record
                if organization_id:
                    row = await conn.fetchrow(
                        """SELECT * FROM generation_analytics
                           WHERE organization_id = $1
                           AND period_start = $2""",
                        organization_id, period_start
                    )
                else:
                    row = await conn.fetchrow(
                        """SELECT * FROM generation_analytics
                           WHERE organization_id IS NULL
                           AND period_start = $1""",
                        period_start
                    )

                if row:
                    return self._row_to_analytics(dict(row))

                # Create new record
                from uuid import uuid4
                analytics = GenerationAnalytics(
                    id=uuid4(),
                    organization_id=organization_id,
                    period_start=period_start
                )

                await conn.execute(
                    """INSERT INTO generation_analytics (
                        id, organization_id, period_start, period_end,
                        total_requests, completed_requests, failed_requests,
                        cached_responses, avg_generation_time_seconds,
                        min_generation_time_seconds, max_generation_time_seconds,
                        total_generation_time_seconds, total_input_tokens,
                        total_output_tokens, avg_tokens_per_request,
                        total_cost, avg_cost_per_request, cost_savings_from_cache,
                        avg_quality_score, excellent_count, good_count,
                        acceptable_count, needs_work_count, poor_count,
                        content_type_counts, total_refinements,
                        successful_refinements, avg_quality_improvement,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                        $21, $22, $23, $24, $25, $26, $27, $28, $29, $30
                    )""",
                    analytics.id, analytics.organization_id,
                    analytics.period_start, analytics.period_end,
                    0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0.0,
                    0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0,
                    json.dumps({}), 0, 0, 0.0,
                    datetime.utcnow(), datetime.utcnow()
                )
                return analytics
        except Exception as e:
            raise DatabaseException(
                message="Failed to get or create analytics",
                error_code="ANALYTICS_GET_CREATE_ERROR",
                details={"organization_id": str(organization_id) if organization_id else None},
                original_exception=e
            )

    async def update_analytics(
        self,
        analytics: GenerationAnalytics
    ) -> bool:
        """
        Update analytics record.

        WHAT: Updates analytics in database
        WHERE: Called after recording metrics
        WHY: Persists analytics updates

        Args:
            analytics: GenerationAnalytics entity with updates

        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """UPDATE generation_analytics SET
                        total_requests = $1, completed_requests = $2,
                        failed_requests = $3, cached_responses = $4,
                        avg_generation_time_seconds = $5,
                        min_generation_time_seconds = $6,
                        max_generation_time_seconds = $7,
                        total_generation_time_seconds = $8,
                        total_input_tokens = $9, total_output_tokens = $10,
                        avg_tokens_per_request = $11, total_cost = $12,
                        avg_cost_per_request = $13, cost_savings_from_cache = $14,
                        avg_quality_score = $15, excellent_count = $16,
                        good_count = $17, acceptable_count = $18,
                        needs_work_count = $19, poor_count = $20,
                        content_type_counts = $21, total_refinements = $22,
                        successful_refinements = $23, avg_quality_improvement = $24,
                        updated_at = $25
                    WHERE id = $26""",
                    analytics.total_requests,
                    analytics.completed_requests,
                    analytics.failed_requests,
                    analytics.cached_responses,
                    float(analytics.avg_generation_time_seconds),
                    float(analytics.min_generation_time_seconds),
                    float(analytics.max_generation_time_seconds),
                    float(analytics.total_generation_time_seconds),
                    analytics.total_input_tokens,
                    analytics.total_output_tokens,
                    float(analytics.avg_tokens_per_request),
                    float(analytics.total_cost),
                    float(analytics.avg_cost_per_request),
                    float(analytics.cost_savings_from_cache),
                    float(analytics.avg_quality_score),
                    analytics.excellent_count,
                    analytics.good_count,
                    analytics.acceptable_count,
                    analytics.needs_work_count,
                    analytics.poor_count,
                    json.dumps(analytics.content_type_counts),
                    analytics.total_refinements,
                    analytics.successful_refinements,
                    float(analytics.avg_quality_improvement),
                    datetime.utcnow(),
                    analytics.id
                )
                return "UPDATE 1" in result
        except Exception as e:
            raise DatabaseException(
                message="Failed to update analytics",
                error_code="ANALYTICS_UPDATE_ERROR",
                details={"analytics_id": str(analytics.id)},
                original_exception=e
            )

    async def get_analytics_history(
        self,
        organization_id: Optional[UUID] = None,
        days: int = 30
    ) -> List[GenerationAnalytics]:
        """
        Get analytics history for specified period.

        WHAT: Fetches historical analytics records
        WHERE: Called for trend analysis
        WHY: Enables performance trend reporting

        Args:
            organization_id: Organization to filter by (None for global)
            days: Number of days of history

        Returns:
            List of GenerationAnalytics entities
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            async with self.db_pool.acquire() as conn:
                if organization_id:
                    rows = await conn.fetch(
                        """SELECT * FROM generation_analytics
                           WHERE organization_id = $1
                           AND period_start >= $2
                           ORDER BY period_start ASC""",
                        organization_id, start_date
                    )
                else:
                    rows = await conn.fetch(
                        """SELECT * FROM generation_analytics
                           WHERE organization_id IS NULL
                           AND period_start >= $1
                           ORDER BY period_start ASC""",
                        start_date
                    )
                return [self._row_to_analytics(dict(row)) for row in rows]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve analytics history",
                error_code="ANALYTICS_HISTORY_ERROR",
                details={"days": days},
                original_exception=e
            )

    # ================================================================
    # ROW CONVERSION HELPERS
    # ================================================================

    def _row_to_generation_request(self, row: Dict[str, Any]) -> GenerationRequest:
        """Convert database row to GenerationRequest entity."""
        return GenerationRequest(
            id=row['id'],
            course_id=row['course_id'],
            content_type=GenerationContentType(row['content_type']),
            requester_id=row['requester_id'],
            organization_id=row.get('organization_id'),
            module_id=row.get('module_id'),
            template_id=row.get('template_id'),
            status=GenerationStatus(row['status']),
            parameters=json.loads(row['parameters']) if isinstance(row['parameters'], str) else row['parameters'],
            difficulty_level=row['difficulty_level'],
            target_audience=row['target_audience'],
            language=row['language'],
            model_name=row['model_name'],
            max_tokens=row['max_tokens'],
            temperature=float(row['temperature']),
            use_rag=row['use_rag'],
            use_cache=row['use_cache'],
            max_retries=row['max_retries'],
            retry_count=row['retry_count'],
            timeout_seconds=row['timeout_seconds'],
            started_at=row.get('started_at'),
            completed_at=row.get('completed_at'),
            result_id=row.get('result_id'),
            error_message=row.get('error_message'),
            input_tokens=row['input_tokens'],
            output_tokens=row['output_tokens'],
            estimated_cost=Decimal(str(row['estimated_cost'])),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_generation_result(self, row: Dict[str, Any]) -> GenerationResult:
        """Convert database row to GenerationResult entity."""
        return GenerationResult(
            id=row['id'],
            request_id=row['request_id'],
            course_id=row['course_id'],
            content_type=GenerationContentType(row['content_type']),
            raw_output=row['raw_output'],
            processed_content=json.loads(row['processed_content']) if isinstance(row['processed_content'], str) else row['processed_content'],
            quality_score_id=row.get('quality_score_id'),
            quality_level=QualityLevel(row['quality_level']),
            model_used=row['model_used'],
            generation_method=row['generation_method'],
            rag_context_used=row['rag_context_used'],
            cached=row['cached'],
            cache_key=row.get('cache_key'),
            version=row['version'],
            parent_result_id=row.get('parent_result_id'),
            created_at=row['created_at'],
            expires_at=row.get('expires_at')
        )

    def _row_to_quality_score(self, row: Dict[str, Any]) -> ContentQualityScore:
        """Convert database row to ContentQualityScore entity."""
        return ContentQualityScore(
            id=row['id'],
            result_id=row['result_id'],
            accuracy_score=row['accuracy_score'],
            relevance_score=row['relevance_score'],
            completeness_score=row['completeness_score'],
            clarity_score=row['clarity_score'],
            structure_score=row['structure_score'],
            engagement_score=row['engagement_score'],
            difficulty_alignment_score=row['difficulty_alignment_score'],
            overall_score=row['overall_score'],
            quality_level=QualityLevel(row['quality_level']),
            weights=json.loads(row['weights']) if isinstance(row['weights'], str) else row['weights'],
            scoring_method=row['scoring_method'],
            scorer_id=row.get('scorer_id'),
            confidence=float(row['confidence']),
            strengths=json.loads(row['strengths']) if isinstance(row['strengths'], str) else row['strengths'],
            weaknesses=json.loads(row['weaknesses']) if isinstance(row['weaknesses'], str) else row['weaknesses'],
            improvement_suggestions=json.loads(row['improvement_suggestions']) if isinstance(row['improvement_suggestions'], str) else row['improvement_suggestions'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_template(self, row: Dict[str, Any]) -> GenerationTemplate:
        """Convert database row to GenerationTemplate entity."""
        return GenerationTemplate(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            content_type=GenerationContentType(row['content_type']),
            category=TemplateCategory(row['category']),
            system_prompt=row['system_prompt'],
            user_prompt_template=row['user_prompt_template'],
            output_schema=json.loads(row['output_schema']) if isinstance(row['output_schema'], str) else row['output_schema'],
            required_variables=json.loads(row['required_variables']) if isinstance(row['required_variables'], str) else row['required_variables'],
            default_parameters=json.loads(row['default_parameters']) if isinstance(row['default_parameters'], str) else row['default_parameters'],
            difficulty_levels=json.loads(row['difficulty_levels']) if isinstance(row['difficulty_levels'], str) else row['difficulty_levels'],
            target_audiences=json.loads(row['target_audiences']) if isinstance(row['target_audiences'], str) else row['target_audiences'],
            creator_id=row.get('creator_id'),
            organization_id=row.get('organization_id'),
            is_global=row['is_global'],
            is_active=row['is_active'],
            is_archived=row['is_archived'],
            min_quality_score=row['min_quality_score'],
            auto_retry_on_low_quality=row['auto_retry_on_low_quality'],
            max_auto_retries=row['max_auto_retries'],
            usage_count=row['usage_count'],
            success_count=row['success_count'],
            avg_quality_score=float(row['avg_quality_score']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            archived_at=row.get('archived_at')
        )

    def _row_to_refinement(self, row: Dict[str, Any]) -> ContentRefinement:
        """Convert database row to ContentRefinement entity."""
        return ContentRefinement(
            id=row['id'],
            result_id=row['result_id'],
            refinement_type=RefinementType(row['refinement_type']),
            requester_id=row['requester_id'],
            feedback=row['feedback'],
            specific_instructions=row['specific_instructions'],
            target_sections=json.loads(row['target_sections']) if isinstance(row['target_sections'], str) else row['target_sections'],
            preserve_structure=row['preserve_structure'],
            max_changes=row['max_changes'],
            refined_result_id=row.get('refined_result_id'),
            status=GenerationStatus(row['status']),
            changes_made=json.loads(row['changes_made']) if isinstance(row['changes_made'], str) else row['changes_made'],
            original_quality_score=row['original_quality_score'],
            refined_quality_score=row['refined_quality_score'],
            quality_improvement=row['quality_improvement'],
            iteration_number=row['iteration_number'],
            max_iterations=row['max_iterations'],
            created_at=row['created_at'],
            completed_at=row.get('completed_at')
        )

    def _row_to_batch(self, row: Dict[str, Any]) -> BatchGeneration:
        """Convert database row to BatchGeneration entity."""
        content_types_raw = json.loads(row['content_types']) if isinstance(row['content_types'], str) else row['content_types']
        target_modules_raw = json.loads(row['target_modules']) if isinstance(row['target_modules'], str) else row['target_modules']
        request_ids_raw = json.loads(row['request_ids']) if isinstance(row['request_ids'], str) else row['request_ids']

        return BatchGeneration(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            course_id=row['course_id'],
            requester_id=row['requester_id'],
            organization_id=row.get('organization_id'),
            shared_parameters=json.loads(row['shared_parameters']) if isinstance(row['shared_parameters'], str) else row['shared_parameters'],
            content_types=[GenerationContentType(ct) for ct in content_types_raw],
            target_modules=[UUID(m) for m in target_modules_raw],
            max_batch_size=row['max_batch_size'],
            parallel_workers=row['parallel_workers'],
            request_ids=[UUID(r) for r in request_ids_raw],
            status=BatchStatus(row['status']),
            total_items=row['total_items'],
            completed_items=row['completed_items'],
            failed_items=row['failed_items'],
            progress_percentage=float(row['progress_percentage']),
            current_item_index=row['current_item_index'],
            started_at=row.get('started_at'),
            completed_at=row.get('completed_at'),
            estimated_completion=row.get('estimated_completion'),
            total_estimated_cost=Decimal(str(row['total_estimated_cost'])),
            actual_cost=Decimal(str(row['actual_cost'])),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_analytics(self, row: Dict[str, Any]) -> GenerationAnalytics:
        """Convert database row to GenerationAnalytics entity."""
        return GenerationAnalytics(
            id=row['id'],
            organization_id=row.get('organization_id'),
            period_start=row['period_start'],
            period_end=row.get('period_end'),
            total_requests=row['total_requests'],
            completed_requests=row['completed_requests'],
            failed_requests=row['failed_requests'],
            cached_responses=row['cached_responses'],
            avg_generation_time_seconds=float(row['avg_generation_time_seconds']),
            min_generation_time_seconds=float(row['min_generation_time_seconds']),
            max_generation_time_seconds=float(row['max_generation_time_seconds']),
            total_generation_time_seconds=float(row['total_generation_time_seconds']),
            total_input_tokens=row['total_input_tokens'],
            total_output_tokens=row['total_output_tokens'],
            avg_tokens_per_request=float(row['avg_tokens_per_request']),
            total_cost=Decimal(str(row['total_cost'])),
            avg_cost_per_request=Decimal(str(row['avg_cost_per_request'])),
            cost_savings_from_cache=Decimal(str(row['cost_savings_from_cache'])),
            avg_quality_score=float(row['avg_quality_score']),
            excellent_count=row['excellent_count'],
            good_count=row['good_count'],
            acceptable_count=row['acceptable_count'],
            needs_work_count=row['needs_work_count'],
            poor_count=row['poor_count'],
            content_type_counts=json.loads(row['content_type_counts']) if isinstance(row['content_type_counts'], str) else row['content_type_counts'],
            total_refinements=row['total_refinements'],
            successful_refinements=row['successful_refinements'],
            avg_quality_improvement=float(row['avg_quality_improvement']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
