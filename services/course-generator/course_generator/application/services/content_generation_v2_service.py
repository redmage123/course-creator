"""
Content Generation V2 Application Service

WHAT: Application service implementing business logic for AI-powered content generation V2
WHERE: Used by API layer to orchestrate content generation operations
WHY: Provides a clean interface for content generation with quality tracking,
     template management, refinement workflows, and batch operations

Enhancement 4: AI-Powered Content Generation V2

Business Context:
The Content Generation V2 service provides advanced AI-powered educational content
creation with:
- Request lifecycle management with full tracking
- Quality scoring and threshold enforcement
- Customizable templates for consistent generation
- Iterative refinement workflows for content improvement
- Batch operations for efficient bulk content creation
- Comprehensive analytics for performance monitoring

Technical Implementation:
- Follows application service pattern for business logic orchestration
- Uses DAO for all database operations
- Integrates with AI client for content generation
- Implements quality scoring for generated content
- Provides caching for improved performance
"""

import logging
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4

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
    InvalidGenerationParametersException,
    GenerationTimeoutException,
    QualityThresholdNotMetException,
    MaxRefinementsExceededException,
    BatchSizeLimitException,
    TemplateNotFoundException
)

from data_access.content_generation_v2_dao import ContentGenerationV2DAO


class ContentGenerationV2Service:
    """
    Application service for Content Generation V2 operations.

    WHAT: Orchestrates content generation business logic and workflows
    WHERE: Used by API endpoints and background job processors
    WHY: Encapsulates generation logic, quality assessment, and analytics tracking

    Business Context:
    This service provides the primary interface for all content generation
    operations, coordinating between:
    - Content Generation DAO for persistence
    - AI client for content generation
    - Quality scoring system for content evaluation
    - Analytics tracking for performance monitoring
    """

    def __init__(
        self,
        dao: ContentGenerationV2DAO,
        ai_client: Any,  # Type will be specific AI client
        rag_client: Optional[Any] = None
    ):
        """
        Initialize the Content Generation V2 Service.

        WHAT: Constructor that sets up service dependencies
        WHERE: Called when creating service instance
        WHY: Enables dependency injection for testability

        Args:
            dao: Content Generation V2 DAO for database operations
            ai_client: AI client for content generation
            rag_client: Optional RAG client for context enhancement
        """
        self.dao = dao
        self.ai_client = ai_client
        self.rag_client = rag_client
        self.logger = logging.getLogger(__name__)

    # ================================================================
    # GENERATION REQUEST OPERATIONS
    # ================================================================

    async def create_generation_request(
        self,
        course_id: UUID,
        content_type: GenerationContentType,
        requester_id: UUID,
        organization_id: Optional[UUID] = None,
        module_id: Optional[UUID] = None,
        template_id: Optional[UUID] = None,
        parameters: Optional[Dict[str, Any]] = None,
        difficulty_level: str = "intermediate",
        target_audience: str = "general",
        language: str = "en",
        use_rag: bool = True,
        use_cache: bool = True
    ) -> GenerationRequest:
        """
        Create a new content generation request.

        WHAT: Creates and validates a generation request
        WHERE: Called when user initiates content generation
        WHY: Provides entry point for content generation workflow

        Args:
            course_id: Course to generate content for
            content_type: Type of content to generate
            requester_id: User requesting generation
            organization_id: Organization context
            module_id: Optional specific module
            template_id: Optional template to use
            parameters: Additional generation parameters
            difficulty_level: Target difficulty level
            target_audience: Target audience
            language: Content language
            use_rag: Whether to use RAG enhancement
            use_cache: Whether to use caching

        Returns:
            Created GenerationRequest entity

        Raises:
            InvalidGenerationParametersException: If parameters invalid
            TemplateNotFoundException: If template not found
        """
        self.logger.info(
            f"Creating generation request for course {course_id}, "
            f"type {content_type.value}"
        )

        # Validate template if specified
        template = None
        if template_id:
            template = await self.dao.get_template(template_id)
            if not template:
                raise TemplateNotFoundException(
                    f"Template {template_id} not found"
                )
            if template.is_archived or not template.is_active:
                raise TemplateNotFoundException(
                    f"Template {template_id} is not active"
                )

        # Check cache first if enabled
        if use_cache:
            cache_key = self._generate_cache_key(
                course_id, content_type, parameters, difficulty_level,
                target_audience, language
            )
            cached_result = await self.dao.get_result_by_cache_key(cache_key)
            if cached_result and not cached_result.is_expired():
                self.logger.info(f"Cache hit for key {cache_key}")
                # Create request linked to cached result
                request = GenerationRequest(
                    id=uuid4(),
                    course_id=course_id,
                    content_type=content_type,
                    requester_id=requester_id,
                    organization_id=organization_id,
                    module_id=module_id,
                    template_id=template_id,
                    status=GenerationStatus.COMPLETED,
                    parameters=parameters or {},
                    difficulty_level=difficulty_level,
                    target_audience=target_audience,
                    language=language,
                    use_rag=use_rag,
                    use_cache=use_cache,
                    result_id=cached_result.id,
                    completed_at=datetime.utcnow()
                )
                await self.dao.create_generation_request(request)

                # Record analytics
                await self._record_analytics(
                    organization_id=organization_id,
                    success=True,
                    cached=True,
                    generation_time=0.0,
                    input_tokens=0,
                    output_tokens=0,
                    cost=Decimal("0.00"),
                    quality_level=cached_result.quality_level,
                    content_type=content_type
                )

                return request

        # Create new request
        request = GenerationRequest(
            id=uuid4(),
            course_id=course_id,
            content_type=content_type,
            requester_id=requester_id,
            organization_id=organization_id,
            module_id=module_id,
            template_id=template_id,
            parameters=parameters or {},
            difficulty_level=difficulty_level,
            target_audience=target_audience,
            language=language,
            use_rag=use_rag,
            use_cache=use_cache
        )

        # Apply template defaults if available
        if template:
            request.parameters = {
                **template.default_parameters,
                **(parameters or {})
            }

        await self.dao.create_generation_request(request)
        self.logger.info(f"Created generation request {request.id}")

        return request

    async def get_generation_request(
        self,
        request_id: UUID
    ) -> Optional[GenerationRequest]:
        """
        Get a generation request by ID.

        WHAT: Retrieves generation request details
        WHERE: Called when checking request status
        WHY: Provides request status and tracking

        Args:
            request_id: UUID of request to retrieve

        Returns:
            GenerationRequest entity or None if not found
        """
        return await self.dao.get_generation_request(request_id)

    async def process_generation_request(
        self,
        request_id: UUID
    ) -> GenerationResult:
        """
        Process a generation request to completion.

        WHAT: Executes full generation workflow
        WHERE: Called by job processor or synchronously
        WHY: Generates content and records quality metrics

        Args:
            request_id: UUID of request to process

        Returns:
            GenerationResult with generated content

        Raises:
            ContentGenerationException: If generation fails
            GenerationTimeoutException: If generation times out
            QualityThresholdNotMetException: If quality too low after retries
        """
        request = await self.dao.get_generation_request(request_id)
        if not request:
            raise ContentGenerationException(
                f"Request {request_id} not found"
            )

        self.logger.info(f"Processing generation request {request_id}")

        # Mark as started
        request.start()
        await self.dao.update_generation_request(request)

        start_time = datetime.utcnow()

        try:
            # Get template if specified
            template = None
            if request.template_id:
                template = await self.dao.get_template(request.template_id)

            # Build prompt
            prompt = await self._build_prompt(request, template)

            # Get RAG context if enabled
            rag_context = None
            if request.use_rag and self.rag_client:
                rag_context = await self._get_rag_context(request)

            # Generate content
            raw_output, input_tokens, output_tokens = await self._generate_content(
                prompt=prompt,
                rag_context=rag_context,
                model_name=request.model_name,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            # Process output
            processed_content = await self._process_output(
                raw_output=raw_output,
                content_type=request.content_type,
                template=template
            )

            # Create result
            cache_key = None
            if request.use_cache:
                cache_key = self._generate_cache_key(
                    request.course_id,
                    request.content_type,
                    request.parameters,
                    request.difficulty_level,
                    request.target_audience,
                    request.language
                )

            result = GenerationResult(
                id=uuid4(),
                request_id=request.id,
                course_id=request.course_id,
                content_type=request.content_type,
                raw_output=raw_output,
                processed_content=processed_content,
                model_used=request.model_name,
                generation_method="hybrid" if rag_context else "ai",
                rag_context_used=rag_context is not None,
                cached=False,
                cache_key=cache_key
            )

            result_id = await self.dao.create_generation_result(result)
            result.id = result_id

            # Score quality
            quality_score = await self._score_quality(result)
            score_id = await self.dao.create_quality_score(quality_score)
            await self.dao.update_result_quality(
                result_id,
                score_id,
                quality_score.quality_level
            )
            result.quality_score_id = score_id
            result.quality_level = quality_score.quality_level

            # Update template usage
            if template:
                await self.dao.increment_template_usage(
                    template.id,
                    success=True,
                    quality_score=quality_score.overall_score
                )

            # Check quality threshold
            min_quality = QualityLevel.ACCEPTABLE
            if template and template.min_quality_score > 60:
                min_quality = QualityLevel.GOOD

            if not result.meets_quality_threshold(min_quality):
                # Check if we should retry
                if template and template.auto_retry_on_low_quality:
                    if request.retry_count < template.max_auto_retries:
                        request.retry()
                        await self.dao.update_generation_request(request)
                        return await self.process_generation_request(request_id)

                self.logger.warning(
                    f"Quality threshold not met for request {request_id}: "
                    f"{quality_score.quality_level.value}"
                )

            # Mark request complete
            end_time = datetime.utcnow()
            generation_time = (end_time - start_time).total_seconds()

            request.complete(result_id, input_tokens, output_tokens)
            await self.dao.update_generation_request(request)

            # Record analytics
            await self._record_analytics(
                organization_id=request.organization_id,
                success=True,
                cached=False,
                generation_time=generation_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=request.estimated_cost,
                quality_level=quality_score.quality_level,
                content_type=request.content_type
            )

            self.logger.info(
                f"Completed generation request {request_id} with quality "
                f"{quality_score.quality_level.value}"
            )

            return result

        except Exception as e:
            # Handle failure
            error_msg = str(e)
            request.fail(error_msg)
            await self.dao.update_generation_request(request)

            # Record failed analytics
            end_time = datetime.utcnow()
            generation_time = (end_time - start_time).total_seconds()

            await self._record_analytics(
                organization_id=request.organization_id,
                success=False,
                cached=False,
                generation_time=generation_time,
                input_tokens=0,
                output_tokens=0,
                cost=Decimal("0.00"),
                quality_level=None,
                content_type=request.content_type
            )

            self.logger.error(f"Generation failed for request {request_id}: {e}")
            raise ContentGenerationException(
                f"Generation failed: {error_msg}"
            )

    # ================================================================
    # RESULT OPERATIONS
    # ================================================================

    async def get_generation_result(
        self,
        result_id: UUID
    ) -> Optional[GenerationResult]:
        """
        Get a generation result by ID.

        WHAT: Retrieves generated content
        WHERE: Called when accessing generated content
        WHY: Provides access to generation output

        Args:
            result_id: UUID of result to retrieve

        Returns:
            GenerationResult entity or None if not found
        """
        return await self.dao.get_generation_result(result_id)

    async def get_result_with_quality(
        self,
        result_id: UUID
    ) -> Tuple[Optional[GenerationResult], Optional[ContentQualityScore]]:
        """
        Get result with associated quality score.

        WHAT: Retrieves result and quality metrics together
        WHERE: Called when viewing content with quality
        WHY: Provides complete quality context

        Args:
            result_id: UUID of result to retrieve

        Returns:
            Tuple of (GenerationResult, ContentQualityScore) or (None, None)
        """
        result = await self.dao.get_generation_result(result_id)
        if not result:
            return None, None

        quality_score = None
        if result.quality_score_id:
            quality_score = await self.dao.get_quality_score(result.quality_score_id)

        return result, quality_score

    # ================================================================
    # TEMPLATE OPERATIONS
    # ================================================================

    async def create_template(
        self,
        name: str,
        description: str,
        content_type: GenerationContentType,
        category: TemplateCategory,
        system_prompt: str,
        user_prompt_template: str,
        required_variables: List[str],
        creator_id: UUID,
        organization_id: Optional[UUID] = None,
        is_global: bool = False,
        output_schema: Optional[Dict[str, Any]] = None,
        default_parameters: Optional[Dict[str, Any]] = None,
        min_quality_score: int = 60
    ) -> GenerationTemplate:
        """
        Create a new generation template.

        WHAT: Creates customizable generation template
        WHERE: Called when defining new templates
        WHY: Enables consistent content generation

        Args:
            name: Template name
            description: Template description
            content_type: Type of content this template generates
            category: Template category
            system_prompt: System prompt for AI
            user_prompt_template: User prompt with variables
            required_variables: Variables needed in prompts
            creator_id: User creating template
            organization_id: Organization scope (None for global)
            is_global: Whether template is globally available
            output_schema: Optional JSON schema for output
            default_parameters: Default generation parameters
            min_quality_score: Minimum quality threshold

        Returns:
            Created GenerationTemplate entity
        """
        template = GenerationTemplate(
            id=uuid4(),
            name=name,
            description=description,
            content_type=content_type,
            category=category,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            required_variables=required_variables,
            creator_id=creator_id,
            organization_id=organization_id,
            is_global=is_global,
            output_schema=output_schema or {},
            default_parameters=default_parameters or {},
            min_quality_score=min_quality_score
        )

        template_id = await self.dao.create_template(template)
        template.id = template_id

        self.logger.info(f"Created template {template_id}: {name}")
        return template

    async def get_template(
        self,
        template_id: UUID
    ) -> Optional[GenerationTemplate]:
        """
        Get a generation template by ID.

        WHAT: Retrieves template details
        WHERE: Called when using or viewing templates
        WHY: Provides template configuration

        Args:
            template_id: UUID of template to retrieve

        Returns:
            GenerationTemplate entity or None if not found
        """
        return await self.dao.get_template(template_id)

    async def list_templates(
        self,
        content_type: Optional[GenerationContentType] = None,
        category: Optional[TemplateCategory] = None,
        organization_id: Optional[UUID] = None
    ) -> List[GenerationTemplate]:
        """
        List available templates with filters.

        WHAT: Retrieves templates matching criteria
        WHERE: Called when browsing templates
        WHY: Enables template discovery

        Args:
            content_type: Optional content type filter
            category: Optional category filter
            organization_id: Organization to include templates for

        Returns:
            List of matching GenerationTemplate entities
        """
        return await self.dao.get_templates(
            content_type=content_type,
            category=category,
            organization_id=organization_id,
            include_global=True,
            active_only=True
        )

    async def archive_template(
        self,
        template_id: UUID
    ) -> bool:
        """
        Archive a template.

        WHAT: Marks template as archived
        WHERE: Called when retiring templates
        WHY: Prevents use while preserving history

        Args:
            template_id: UUID of template to archive

        Returns:
            True if archived successfully
        """
        template = await self.dao.get_template(template_id)
        if not template:
            raise TemplateNotFoundException(f"Template {template_id} not found")

        template.archive()
        return await self.dao.update_template(template)

    # ================================================================
    # REFINEMENT OPERATIONS
    # ================================================================

    async def create_refinement(
        self,
        result_id: UUID,
        refinement_type: RefinementType,
        requester_id: UUID,
        feedback: str,
        specific_instructions: str = "",
        target_sections: Optional[List[str]] = None
    ) -> ContentRefinement:
        """
        Create a content refinement request.

        WHAT: Initiates content improvement workflow
        WHERE: Called when user requests refinement
        WHY: Enables iterative content improvement

        Args:
            result_id: Result to refine
            refinement_type: Type of refinement
            requester_id: User requesting refinement
            feedback: User feedback for refinement
            specific_instructions: Additional instructions
            target_sections: Specific sections to refine

        Returns:
            Created ContentRefinement entity

        Raises:
            MaxRefinementsExceededException: If max refinements reached
        """
        # Check refinement count
        refinement_count = await self.dao.count_refinements_for_result(result_id)
        if refinement_count >= 5:  # Max iterations
            raise MaxRefinementsExceededException(
                f"Maximum refinements ({5}) already reached for result {result_id}"
            )

        # Get original quality score
        result = await self.dao.get_generation_result(result_id)
        if not result:
            raise ContentGenerationException(f"Result {result_id} not found")

        original_quality = 0
        if result.quality_score_id:
            score = await self.dao.get_quality_score(result.quality_score_id)
            if score:
                original_quality = score.overall_score

        refinement = ContentRefinement(
            id=uuid4(),
            result_id=result_id,
            refinement_type=refinement_type,
            requester_id=requester_id,
            feedback=feedback,
            specific_instructions=specific_instructions,
            target_sections=target_sections or [],
            original_quality_score=original_quality,
            iteration_number=refinement_count + 1
        )

        refinement_id = await self.dao.create_refinement(refinement)
        refinement.id = refinement_id

        self.logger.info(
            f"Created refinement {refinement_id} for result {result_id}"
        )

        return refinement

    async def process_refinement(
        self,
        refinement_id: UUID
    ) -> GenerationResult:
        """
        Process a refinement to completion.

        WHAT: Executes refinement workflow
        WHERE: Called to process refinement request
        WHY: Generates improved content version

        Args:
            refinement_id: UUID of refinement to process

        Returns:
            Refined GenerationResult

        Raises:
            ContentGenerationException: If refinement fails
        """
        refinement = await self.dao.get_refinement(refinement_id)
        if not refinement:
            raise ContentGenerationException(
                f"Refinement {refinement_id} not found"
            )

        original_result = await self.dao.get_generation_result(refinement.result_id)
        if not original_result:
            raise ContentGenerationException(
                f"Original result {refinement.result_id} not found"
            )

        self.logger.info(f"Processing refinement {refinement_id}")

        try:
            # Build refinement prompt
            prompt = await self._build_refinement_prompt(
                original_result=original_result,
                refinement=refinement
            )

            # Generate refined content
            raw_output, input_tokens, output_tokens = await self._generate_content(
                prompt=prompt,
                rag_context=None,
                model_name="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.5  # Lower temperature for refinements
            )

            # Process output
            processed_content = await self._process_output(
                raw_output=raw_output,
                content_type=original_result.content_type,
                template=None
            )

            # Create refined result
            refined_result = original_result.create_refinement_version()
            refined_result.raw_output = raw_output
            refined_result.processed_content = processed_content

            result_id = await self.dao.create_generation_result(refined_result)
            refined_result.id = result_id

            # Score quality
            quality_score = await self._score_quality(refined_result)
            score_id = await self.dao.create_quality_score(quality_score)
            await self.dao.update_result_quality(
                result_id,
                score_id,
                quality_score.quality_level
            )
            refined_result.quality_score_id = score_id
            refined_result.quality_level = quality_score.quality_level

            # Update refinement
            refinement.complete(result_id, quality_score.overall_score)
            await self.dao.update_refinement(refinement)

            # Record analytics
            await self._record_refinement_analytics(
                organization_id=None,  # Get from context
                success=True,
                quality_improvement=refinement.quality_improvement
            )

            self.logger.info(
                f"Completed refinement {refinement_id}, "
                f"quality improvement: {refinement.quality_improvement}"
            )

            return refined_result

        except Exception as e:
            refinement.fail(str(e))
            await self.dao.update_refinement(refinement)

            await self._record_refinement_analytics(
                organization_id=None,
                success=False,
                quality_improvement=0
            )

            self.logger.error(f"Refinement failed: {e}")
            raise ContentGenerationException(f"Refinement failed: {e}")

    # ================================================================
    # BATCH OPERATIONS
    # ================================================================

    async def create_batch(
        self,
        name: str,
        description: str,
        course_id: UUID,
        requester_id: UUID,
        content_types: List[GenerationContentType],
        organization_id: Optional[UUID] = None,
        target_modules: Optional[List[UUID]] = None,
        shared_parameters: Optional[Dict[str, Any]] = None
    ) -> BatchGeneration:
        """
        Create a batch generation request.

        WHAT: Creates batch for bulk content generation
        WHERE: Called when generating multiple content pieces
        WHY: Enables efficient bulk operations

        Args:
            name: Batch name
            description: Batch description
            course_id: Course to generate content for
            requester_id: User requesting batch
            content_types: Types of content to generate
            organization_id: Organization context
            target_modules: Optional specific modules
            shared_parameters: Parameters shared across all items

        Returns:
            Created BatchGeneration entity

        Raises:
            BatchSizeLimitException: If batch would exceed limit
        """
        # Calculate total items
        total_items = len(content_types)
        if target_modules:
            total_items *= len(target_modules)

        if total_items > 50:
            raise BatchSizeLimitException(
                f"Batch size {total_items} exceeds limit of 50"
            )

        batch = BatchGeneration(
            id=uuid4(),
            name=name,
            description=description,
            course_id=course_id,
            requester_id=requester_id,
            organization_id=organization_id,
            content_types=content_types,
            target_modules=target_modules or [],
            shared_parameters=shared_parameters or {},
            total_items=total_items
        )

        batch_id = await self.dao.create_batch(batch)
        batch.id = batch_id

        self.logger.info(f"Created batch {batch_id}: {name} with {total_items} items")

        return batch

    async def process_batch(
        self,
        batch_id: UUID
    ) -> BatchGeneration:
        """
        Process a batch to completion.

        WHAT: Executes batch generation workflow
        WHERE: Called by job processor
        WHY: Generates all batch items with progress tracking

        Args:
            batch_id: UUID of batch to process

        Returns:
            Updated BatchGeneration entity
        """
        batch = await self.dao.get_batch(batch_id)
        if not batch:
            raise ContentGenerationException(f"Batch {batch_id} not found")

        self.logger.info(f"Processing batch {batch_id}")

        batch.start()
        await self.dao.update_batch(batch)

        try:
            # Create individual requests for each item
            for content_type in batch.content_types:
                if batch.target_modules:
                    for module_id in batch.target_modules:
                        request = await self.create_generation_request(
                            course_id=batch.course_id,
                            content_type=content_type,
                            requester_id=batch.requester_id,
                            organization_id=batch.organization_id,
                            module_id=module_id,
                            parameters=batch.shared_parameters
                        )
                        batch.add_request(request.id)
                else:
                    request = await self.create_generation_request(
                        course_id=batch.course_id,
                        content_type=content_type,
                        requester_id=batch.requester_id,
                        organization_id=batch.organization_id,
                        parameters=batch.shared_parameters
                    )
                    batch.add_request(request.id)

            await self.dao.update_batch(batch)

            # Process each request
            for request_id in batch.request_ids:
                try:
                    result = await self.process_generation_request(request_id)
                    request = await self.dao.get_generation_request(request_id)
                    batch.record_item_completion(
                        success=True,
                        cost=request.estimated_cost if request else Decimal("0.00")
                    )
                except Exception as e:
                    self.logger.error(
                        f"Batch item {request_id} failed: {e}"
                    )
                    batch.record_item_completion(success=False)

                await self.dao.update_batch(batch)

            batch.complete()
            await self.dao.update_batch(batch)

            self.logger.info(
                f"Completed batch {batch_id}: {batch.completed_items}/{batch.total_items} "
                f"succeeded, {batch.failed_items} failed"
            )

            return batch

        except Exception as e:
            batch.status = BatchStatus.FAILED
            batch.completed_at = datetime.utcnow()
            await self.dao.update_batch(batch)

            self.logger.error(f"Batch {batch_id} failed: {e}")
            raise ContentGenerationException(f"Batch failed: {e}")

    async def get_batch(
        self,
        batch_id: UUID
    ) -> Optional[BatchGeneration]:
        """
        Get a batch by ID.

        WHAT: Retrieves batch details
        WHERE: Called when checking batch status
        WHY: Provides batch progress information

        Args:
            batch_id: UUID of batch to retrieve

        Returns:
            BatchGeneration entity or None if not found
        """
        return await self.dao.get_batch(batch_id)

    async def cancel_batch(
        self,
        batch_id: UUID
    ) -> bool:
        """
        Cancel a batch generation.

        WHAT: Stops batch processing
        WHERE: Called when user cancels batch
        WHY: Allows stopping long-running batches

        Args:
            batch_id: UUID of batch to cancel

        Returns:
            True if cancelled successfully
        """
        batch = await self.dao.get_batch(batch_id)
        if not batch:
            return False

        batch.cancel()
        await self.dao.update_batch(batch)

        self.logger.info(f"Cancelled batch {batch_id}")
        return True

    # ================================================================
    # ANALYTICS OPERATIONS
    # ================================================================

    async def get_analytics(
        self,
        organization_id: Optional[UUID] = None,
        days: int = 30
    ) -> List[GenerationAnalytics]:
        """
        Get generation analytics history.

        WHAT: Retrieves analytics for specified period
        WHERE: Called for analytics dashboard
        WHY: Provides performance insights

        Args:
            organization_id: Organization to filter by (None for global)
            days: Number of days of history

        Returns:
            List of GenerationAnalytics entities
        """
        return await self.dao.get_analytics_history(
            organization_id=organization_id,
            days=days
        )

    async def get_current_analytics(
        self,
        organization_id: Optional[UUID] = None
    ) -> GenerationAnalytics:
        """
        Get current day's analytics.

        WHAT: Retrieves today's analytics
        WHERE: Called for real-time monitoring
        WHY: Shows current performance

        Args:
            organization_id: Organization to filter by (None for global)

        Returns:
            GenerationAnalytics entity for current period
        """
        return await self.dao.get_or_create_analytics(organization_id)

    # ================================================================
    # PRIVATE HELPER METHODS
    # ================================================================

    def _generate_cache_key(
        self,
        course_id: UUID,
        content_type: GenerationContentType,
        parameters: Optional[Dict[str, Any]],
        difficulty_level: str,
        target_audience: str,
        language: str
    ) -> str:
        """Generate deterministic cache key for request."""
        key_parts = [
            str(course_id),
            content_type.value,
            difficulty_level,
            target_audience,
            language,
            str(sorted(parameters.items()) if parameters else [])
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    async def _build_prompt(
        self,
        request: GenerationRequest,
        template: Optional[GenerationTemplate]
    ) -> str:
        """Build generation prompt from request and template."""
        if template:
            variables = {
                "difficulty_level": request.difficulty_level,
                "target_audience": request.target_audience,
                **request.parameters
            }
            return template.render_prompt(variables)

        # Default prompt building
        prompt = (
            f"Generate {request.content_type.value} content for an educational course.\n"
            f"Difficulty: {request.difficulty_level}\n"
            f"Target Audience: {request.target_audience}\n"
            f"Language: {request.language}\n"
        )

        if request.parameters:
            prompt += f"\nAdditional requirements: {request.parameters}"

        return prompt

    async def _build_refinement_prompt(
        self,
        original_result: GenerationResult,
        refinement: ContentRefinement
    ) -> str:
        """Build refinement prompt from original content and feedback."""
        prompt = (
            f"Refine the following {original_result.content_type.value} content.\n\n"
            f"Original content:\n{original_result.raw_output}\n\n"
            f"Refinement type: {refinement.refinement_type.value}\n"
            f"User feedback: {refinement.feedback}\n"
        )

        if refinement.specific_instructions:
            prompt += f"\nSpecific instructions: {refinement.specific_instructions}\n"

        if refinement.target_sections:
            prompt += f"\nFocus on sections: {', '.join(refinement.target_sections)}\n"

        if refinement.preserve_structure:
            prompt += "\nPreserve the overall structure while improving content quality.\n"

        prompt += f"\nMake at most {refinement.max_changes} significant changes."

        return prompt

    async def _get_rag_context(
        self,
        request: GenerationRequest
    ) -> Optional[str]:
        """Get RAG context for request."""
        if not self.rag_client:
            return None

        try:
            # This would call the RAG service
            # context = await self.rag_client.get_context(
            #     course_id=request.course_id,
            #     content_type=request.content_type.value,
            #     query=request.parameters.get("topic", "")
            # )
            # return context
            return None  # Placeholder
        except Exception as e:
            self.logger.warning(f"Failed to get RAG context: {e}")
            return None

    async def _generate_content(
        self,
        prompt: str,
        rag_context: Optional[str],
        model_name: str,
        max_tokens: int,
        temperature: float
    ) -> Tuple[str, int, int]:
        """Generate content using AI client."""
        if rag_context:
            full_prompt = f"Context:\n{rag_context}\n\n{prompt}"
        else:
            full_prompt = prompt

        # This would call the actual AI client
        # response = await self.ai_client.generate(
        #     prompt=full_prompt,
        #     model=model_name,
        #     max_tokens=max_tokens,
        #     temperature=temperature
        # )
        # return response.text, response.input_tokens, response.output_tokens

        # Placeholder for testing
        return f"Generated content for: {prompt[:50]}...", 100, 500

    async def _process_output(
        self,
        raw_output: str,
        content_type: GenerationContentType,
        template: Optional[GenerationTemplate]
    ) -> Dict[str, Any]:
        """Process raw AI output into structured format."""
        # This would parse the output based on content type and template schema
        return {"content": raw_output}

    async def _score_quality(
        self,
        result: GenerationResult
    ) -> ContentQualityScore:
        """Score the quality of generated content."""
        # This would implement actual quality scoring logic
        # For now, generate reasonable default scores
        score = ContentQualityScore(
            id=uuid4(),
            result_id=result.id,
            accuracy_score=75,
            relevance_score=80,
            completeness_score=70,
            clarity_score=85,
            structure_score=75,
            engagement_score=70,
            difficulty_alignment_score=80,
            scoring_method="automated",
            confidence=0.75,
            strengths=["Well-structured", "Clear explanations"],
            weaknesses=["Could include more examples"],
            improvement_suggestions=["Add practical exercises"]
        )
        score.calculate_overall_score()
        return score

    async def _record_analytics(
        self,
        organization_id: Optional[UUID],
        success: bool,
        cached: bool,
        generation_time: float,
        input_tokens: int,
        output_tokens: int,
        cost: Decimal,
        quality_level: Optional[QualityLevel],
        content_type: GenerationContentType
    ) -> None:
        """Record generation metrics to analytics."""
        try:
            analytics = await self.dao.get_or_create_analytics(organization_id)
            analytics.record_generation(
                success=success,
                cached=cached,
                generation_time=generation_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                quality_level=quality_level,
                content_type=content_type
            )
            await self.dao.update_analytics(analytics)
        except Exception as e:
            self.logger.warning(f"Failed to record analytics: {e}")

    async def _record_refinement_analytics(
        self,
        organization_id: Optional[UUID],
        success: bool,
        quality_improvement: int
    ) -> None:
        """Record refinement metrics to analytics."""
        try:
            analytics = await self.dao.get_or_create_analytics(organization_id)
            analytics.record_refinement(success, quality_improvement)
            await self.dao.update_analytics(analytics)
        except Exception as e:
            self.logger.warning(f"Failed to record refinement analytics: {e}")
