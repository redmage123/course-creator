"""
WHAT: Domain entities for AI-Powered Content Generation V2
WHERE: Used by course-generator service for enhanced content generation
WHY: Provides structured tracking of content generation requests, quality metrics,
     templates, refinements, and batch operations for improved AI content quality

Enhancement 4: AI-Powered Content Generation V2

Key Features:
1. Generation Request Tracking - Track all generation requests with full parameters
2. Quality Scoring System - Multi-dimensional quality assessment for generated content
3. Generation Templates - Customizable templates for consistent content generation
4. Content Refinement Workflow - Iterative improvement based on feedback
5. Batch Generation Support - Generate multiple content pieces efficiently
6. Generation Analytics - Track performance, costs, and quality trends

Business Rules:
- All generated content must be scored for quality before publishing
- Templates define generation parameters and expected output structure
- Refinements are limited to prevent infinite loops
- Batch operations have size limits for resource management
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


# ============================================================================
# ENUMS
# ============================================================================

class GenerationContentType(str, Enum):
    """
    WHAT: Types of content that can be generated
    WHERE: Used in GenerationRequest and GenerationResult
    WHY: Categorizes content for appropriate generator selection
    """
    SYLLABUS = "syllabus"
    SLIDES = "slides"
    QUIZ = "quiz"
    EXERCISE = "exercise"
    LEARNING_OBJECTIVES = "learning_objectives"
    SUMMARY = "summary"
    ASSESSMENT_RUBRIC = "assessment_rubric"
    DISCUSSION_PROMPTS = "discussion_prompts"
    CASE_STUDY = "case_study"


class GenerationStatus(str, Enum):
    """
    WHAT: Status states for generation requests
    WHERE: Used in GenerationRequest entity
    WHY: Tracks generation lifecycle from request to completion
    """
    PENDING = "pending"           # Queued, not started
    VALIDATING = "validating"     # Validating input parameters
    GENERATING = "generating"     # AI generation in progress
    ENHANCING = "enhancing"       # RAG enhancement in progress
    REVIEWING = "reviewing"       # Quality review in progress
    COMPLETED = "completed"       # Successfully generated
    FAILED = "failed"             # Generation error
    CANCELLED = "cancelled"       # User cancelled
    TIMEOUT = "timeout"           # Generation timeout


class QualityLevel(str, Enum):
    """
    WHAT: Quality classification for generated content
    WHERE: Used in ContentQualityScore
    WHY: Enables quick quality assessment and filtering
    """
    EXCELLENT = "excellent"   # Score >= 90
    GOOD = "good"            # Score 75-89
    ACCEPTABLE = "acceptable" # Score 60-74
    NEEDS_WORK = "needs_work" # Score 40-59
    POOR = "poor"            # Score < 40


class RefinementType(str, Enum):
    """
    WHAT: Types of content refinement operations
    WHERE: Used in ContentRefinement entity
    WHY: Categorizes refinement actions for appropriate processing
    """
    EXPAND = "expand"           # Add more detail/content
    SIMPLIFY = "simplify"       # Reduce complexity
    RESTRUCTURE = "restructure" # Change organization
    CORRECT = "correct"         # Fix errors/inaccuracies
    TONE_ADJUST = "tone_adjust" # Adjust writing style
    DIFFICULTY_ADJUST = "difficulty_adjust"  # Change difficulty level
    ADD_EXAMPLES = "add_examples"  # Add practical examples
    ADD_EXERCISES = "add_exercises"  # Add practice exercises


class BatchStatus(str, Enum):
    """
    WHAT: Status states for batch generation operations
    WHERE: Used in BatchGeneration entity
    WHY: Tracks batch operation progress
    """
    CREATED = "created"         # Batch created, not started
    QUEUED = "queued"           # Added to processing queue
    PROCESSING = "processing"   # Actively generating content
    COMPLETED = "completed"     # All items generated
    PARTIAL = "partial"         # Some items failed
    FAILED = "failed"           # Batch failed entirely
    CANCELLED = "cancelled"     # User cancelled


class TemplateCategory(str, Enum):
    """
    WHAT: Categories for generation templates
    WHERE: Used in GenerationTemplate entity
    WHY: Organizes templates for discovery and filtering
    """
    STANDARD = "standard"       # General purpose
    TECHNICAL = "technical"     # Programming/engineering focus
    BUSINESS = "business"       # Business/management focus
    CREATIVE = "creative"       # Arts/humanities focus
    SCIENTIFIC = "scientific"   # Science/research focus
    LANGUAGE = "language"       # Language learning focus
    COMPLIANCE = "compliance"   # Regulatory/compliance focus
    CUSTOM = "custom"           # User-defined


# ============================================================================
# EXCEPTIONS
# ============================================================================

class ContentGenerationException(Exception):
    """
    WHAT: Base exception for content generation errors
    WHERE: Parent for all content generation exceptions
    WHY: Enables catching all generation errors with single handler
    """
    pass


class InvalidGenerationParametersException(ContentGenerationException):
    """
    WHAT: Raised when generation parameters are invalid
    WHERE: When validating generation request
    WHY: Prevents invalid generation attempts
    """
    pass


class GenerationTimeoutException(ContentGenerationException):
    """
    WHAT: Raised when generation exceeds time limit
    WHERE: During AI content generation
    WHY: Prevents runaway generation processes
    """
    pass


class QualityThresholdNotMetException(ContentGenerationException):
    """
    WHAT: Raised when generated content fails quality check
    WHERE: During quality assessment
    WHY: Ensures minimum content quality standards
    """
    pass


class MaxRefinementsExceededException(ContentGenerationException):
    """
    WHAT: Raised when refinement limit is reached
    WHERE: When attempting additional refinement
    WHY: Prevents infinite refinement loops
    """
    pass


class BatchSizeLimitException(ContentGenerationException):
    """
    WHAT: Raised when batch size exceeds limit
    WHERE: When creating batch generation
    WHY: Prevents resource exhaustion
    """
    pass


class TemplateNotFoundException(ContentGenerationException):
    """
    WHAT: Raised when requested template not found
    WHERE: When loading template for generation
    WHY: Provides clear error for missing templates
    """
    pass


# ============================================================================
# GENERATION REQUEST ENTITY
# ============================================================================

@dataclass
class GenerationRequest:
    """
    WHAT: A request for AI content generation
    WHERE: Created when user initiates content generation
    WHY: Tracks generation requests with full parameters and status
         for auditing, caching, and analytics

    Business Rules:
    - Requests must specify content type and target entity (course/module)
    - Parameters are validated before generation starts
    - Failed requests can be retried up to max_retries limit
    - Timeout prevents runaway generation processes
    """
    id: UUID
    course_id: UUID
    content_type: GenerationContentType
    requester_id: UUID
    organization_id: Optional[UUID] = None
    module_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    status: GenerationStatus = GenerationStatus.PENDING
    # Generation parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    difficulty_level: str = "intermediate"
    target_audience: str = "general"
    language: str = "en"
    # Generation settings
    model_name: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4096
    temperature: float = 0.7
    use_rag: bool = True
    use_cache: bool = True
    # Retry configuration
    max_retries: int = 3
    retry_count: int = 0
    # Timing
    timeout_seconds: int = 300
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Results
    result_id: Optional[UUID] = None
    error_message: Optional[str] = None
    # Costs
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: Decimal = Decimal("0.00")
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def start(self) -> None:
        """
        WHAT: Marks generation as started
        WHERE: Called when generation begins
        WHY: Tracks generation start time
        """
        self.status = GenerationStatus.GENERATING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, result_id: UUID, input_tokens: int, output_tokens: int) -> None:
        """
        WHAT: Marks generation as completed
        WHERE: Called when generation succeeds
        WHY: Records successful completion with metrics

        Args:
            result_id: ID of generated content
            input_tokens: Tokens used for input
            output_tokens: Tokens generated for output
        """
        self.status = GenerationStatus.COMPLETED
        self.result_id = result_id
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._calculate_cost()

    def fail(self, error: str) -> None:
        """
        WHAT: Marks generation as failed
        WHERE: Called when generation errors
        WHY: Records failure details for debugging

        Args:
            error: Error message describing failure
        """
        self.status = GenerationStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """
        WHAT: Cancels the generation request
        WHERE: Called when user cancels
        WHY: Stops generation and marks as cancelled
        """
        self.status = GenerationStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def timeout(self) -> None:
        """
        WHAT: Marks generation as timed out
        WHERE: Called when timeout exceeded
        WHY: Handles runaway generation processes
        """
        self.status = GenerationStatus.TIMEOUT
        self.error_message = f"Generation exceeded timeout of {self.timeout_seconds} seconds"
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def retry(self) -> bool:
        """
        WHAT: Attempts to retry failed generation
        WHERE: Called after failure
        WHY: Handles transient failures

        Returns:
            True if retry allowed, False if max retries exceeded
        """
        if self.retry_count >= self.max_retries:
            return False
        self.retry_count += 1
        self.status = GenerationStatus.PENDING
        self.error_message = None
        self.started_at = None
        self.updated_at = datetime.utcnow()
        return True

    def is_timed_out(self) -> bool:
        """
        WHAT: Checks if generation has exceeded timeout
        WHERE: Called during generation monitoring
        WHY: Identifies stuck generation processes
        """
        if self.started_at is None:
            return False
        elapsed = datetime.utcnow() - self.started_at
        return elapsed.total_seconds() > self.timeout_seconds

    def _calculate_cost(self) -> None:
        """
        WHAT: Calculates estimated generation cost
        WHERE: Called after completion
        WHY: Tracks API usage costs

        Cost calculation (approximate Claude pricing):
        - Input: $0.003 per 1K tokens
        - Output: $0.015 per 1K tokens
        """
        input_cost = Decimal(str(self.input_tokens / 1000 * 0.003))
        output_cost = Decimal(str(self.output_tokens / 1000 * 0.015))
        self.estimated_cost = input_cost + output_cost

    def get_duration_seconds(self) -> Optional[int]:
        """
        WHAT: Gets generation duration
        WHERE: Called for analytics
        WHY: Tracks generation performance
        """
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None


# ============================================================================
# GENERATION RESULT ENTITY
# ============================================================================

@dataclass
class GenerationResult:
    """
    WHAT: The result of an AI content generation
    WHERE: Created when generation completes successfully
    WHY: Stores generated content with metadata for retrieval and analysis

    Business Rules:
    - Results are linked to their generation requests
    - Raw AI output is preserved for debugging
    - Processed content is formatted for use
    - Quality score determines usability
    """
    id: UUID
    request_id: UUID
    course_id: UUID
    content_type: GenerationContentType
    # Content
    raw_output: str  # Raw AI-generated text
    processed_content: Dict[str, Any] = field(default_factory=dict)  # Parsed/structured content
    # Quality
    quality_score_id: Optional[UUID] = None
    quality_level: QualityLevel = QualityLevel.ACCEPTABLE
    # Metadata
    model_used: str = ""
    generation_method: str = "ai"  # ai, template, hybrid
    rag_context_used: bool = False
    cached: bool = False
    cache_key: Optional[str] = None
    # Versioning
    version: int = 1
    parent_result_id: Optional[UUID] = None  # For refinements
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default expiration if not provided"""
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(days=30)

    def set_quality(self, quality_score_id: UUID, quality_level: QualityLevel) -> None:
        """
        WHAT: Sets quality assessment for result
        WHERE: Called after quality scoring
        WHY: Links quality metrics to result

        Args:
            quality_score_id: ID of quality assessment
            quality_level: Calculated quality level
        """
        self.quality_score_id = quality_score_id
        self.quality_level = quality_level

    def create_refinement_version(self) -> "GenerationResult":
        """
        WHAT: Creates a new version for refinement
        WHERE: Called when refining content
        WHY: Maintains version history

        Returns:
            New result with incremented version
        """
        return GenerationResult(
            id=uuid4(),
            request_id=self.request_id,
            course_id=self.course_id,
            content_type=self.content_type,
            raw_output="",
            processed_content={},
            model_used=self.model_used,
            version=self.version + 1,
            parent_result_id=self.id
        )

    def is_expired(self) -> bool:
        """
        WHAT: Checks if result has expired
        WHERE: Called when retrieving cached content
        WHY: Ensures content freshness
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def meets_quality_threshold(self, min_level: QualityLevel = QualityLevel.ACCEPTABLE) -> bool:
        """
        WHAT: Checks if result meets minimum quality
        WHERE: Called before using content
        WHY: Prevents low-quality content usage

        Args:
            min_level: Minimum acceptable quality level
        """
        quality_order = [
            QualityLevel.POOR,
            QualityLevel.NEEDS_WORK,
            QualityLevel.ACCEPTABLE,
            QualityLevel.GOOD,
            QualityLevel.EXCELLENT
        ]
        result_index = quality_order.index(self.quality_level)
        min_index = quality_order.index(min_level)
        return result_index >= min_index


# ============================================================================
# CONTENT QUALITY SCORE ENTITY
# ============================================================================

@dataclass
class ContentQualityScore:
    """
    WHAT: Multi-dimensional quality assessment for generated content
    WHERE: Created during quality review phase
    WHY: Provides detailed quality metrics for content evaluation
         and feedback to improve generation

    Business Rules:
    - All dimensions scored 0-100
    - Overall score is weighted average
    - Automated scoring can be overridden manually
    - Low scores trigger refinement suggestions
    """
    id: UUID
    result_id: UUID
    # Dimension scores (0-100)
    accuracy_score: int = 0          # Factual correctness
    relevance_score: int = 0         # Topic relevance
    completeness_score: int = 0      # Coverage completeness
    clarity_score: int = 0           # Readability/understandability
    structure_score: int = 0         # Organization quality
    engagement_score: int = 0        # Learning engagement potential
    difficulty_alignment_score: int = 0  # Matches target difficulty
    # Calculated scores
    overall_score: int = 0
    quality_level: QualityLevel = QualityLevel.ACCEPTABLE
    # Dimension weights (must sum to 1.0)
    weights: Dict[str, float] = field(default_factory=lambda: {
        "accuracy": 0.20,
        "relevance": 0.15,
        "completeness": 0.15,
        "clarity": 0.20,
        "structure": 0.10,
        "engagement": 0.10,
        "difficulty_alignment": 0.10
    })
    # Scoring metadata
    scoring_method: str = "automated"  # automated, manual, hybrid
    scorer_id: Optional[UUID] = None   # For manual scoring
    confidence: float = 0.0            # AI confidence in scoring
    # Feedback
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def calculate_overall_score(self) -> None:
        """
        WHAT: Calculates weighted overall score
        WHERE: Called after setting dimension scores
        WHY: Provides single quality metric

        Formula: Sum of (dimension_score * weight) for all dimensions
        """
        self.overall_score = int(
            self.accuracy_score * self.weights["accuracy"] +
            self.relevance_score * self.weights["relevance"] +
            self.completeness_score * self.weights["completeness"] +
            self.clarity_score * self.weights["clarity"] +
            self.structure_score * self.weights["structure"] +
            self.engagement_score * self.weights["engagement"] +
            self.difficulty_alignment_score * self.weights["difficulty_alignment"]
        )
        self._set_quality_level()
        self.updated_at = datetime.utcnow()

    def _set_quality_level(self) -> None:
        """
        WHAT: Sets quality level based on overall score
        WHERE: Called after calculating overall score
        WHY: Provides categorical quality classification
        """
        if self.overall_score >= 90:
            self.quality_level = QualityLevel.EXCELLENT
        elif self.overall_score >= 75:
            self.quality_level = QualityLevel.GOOD
        elif self.overall_score >= 60:
            self.quality_level = QualityLevel.ACCEPTABLE
        elif self.overall_score >= 40:
            self.quality_level = QualityLevel.NEEDS_WORK
        else:
            self.quality_level = QualityLevel.POOR

    def set_dimension_score(self, dimension: str, score: int) -> None:
        """
        WHAT: Sets a specific dimension score
        WHERE: Called during scoring process
        WHY: Allows individual dimension updates

        Args:
            dimension: Name of dimension (accuracy, relevance, etc.)
            score: Score value (0-100)
        """
        score = max(0, min(100, score))  # Clamp to 0-100
        dimension_map = {
            "accuracy": "accuracy_score",
            "relevance": "relevance_score",
            "completeness": "completeness_score",
            "clarity": "clarity_score",
            "structure": "structure_score",
            "engagement": "engagement_score",
            "difficulty_alignment": "difficulty_alignment_score"
        }
        if dimension in dimension_map:
            setattr(self, dimension_map[dimension], score)
            self.updated_at = datetime.utcnow()

    def get_lowest_dimensions(self, count: int = 3) -> List[tuple]:
        """
        WHAT: Gets dimensions with lowest scores
        WHERE: Called for improvement suggestions
        WHY: Identifies areas needing most improvement

        Args:
            count: Number of dimensions to return

        Returns:
            List of (dimension_name, score) tuples
        """
        dimensions = [
            ("accuracy", self.accuracy_score),
            ("relevance", self.relevance_score),
            ("completeness", self.completeness_score),
            ("clarity", self.clarity_score),
            ("structure", self.structure_score),
            ("engagement", self.engagement_score),
            ("difficulty_alignment", self.difficulty_alignment_score)
        ]
        return sorted(dimensions, key=lambda x: x[1])[:count]

    def override_with_manual(self, scorer_id: UUID, new_scores: Dict[str, int]) -> None:
        """
        WHAT: Overrides automated scores with manual review
        WHERE: Called by content reviewer
        WHY: Allows human correction of AI scoring

        Args:
            scorer_id: ID of human scorer
            new_scores: Dictionary of dimension scores
        """
        for dimension, score in new_scores.items():
            self.set_dimension_score(dimension, score)
        self.scorer_id = scorer_id
        self.scoring_method = "manual"
        self.calculate_overall_score()


# ============================================================================
# GENERATION TEMPLATE ENTITY
# ============================================================================

@dataclass
class GenerationTemplate:
    """
    WHAT: A template defining content generation parameters and structure
    WHERE: Used to standardize and customize content generation
    WHY: Enables consistent generation across similar content types
         and allows customization without code changes

    Business Rules:
    - Templates define expected output structure
    - Variables in prompts are substituted at generation time
    - Templates can be organization-specific or global
    - Archived templates cannot be used for new generations
    """
    id: UUID
    name: str
    description: str
    content_type: GenerationContentType
    category: TemplateCategory = TemplateCategory.STANDARD
    # Template configuration
    system_prompt: str = ""
    user_prompt_template: str = ""
    output_schema: Dict[str, Any] = field(default_factory=dict)  # JSON Schema
    required_variables: List[str] = field(default_factory=list)  # Variables in prompts
    # Default generation parameters
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    difficulty_levels: List[str] = field(default_factory=lambda: ["beginner", "intermediate", "advanced"])
    target_audiences: List[str] = field(default_factory=lambda: ["general", "technical", "business"])
    # Ownership
    creator_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    is_global: bool = False
    is_active: bool = True
    is_archived: bool = False
    # Quality settings
    min_quality_score: int = 60
    auto_retry_on_low_quality: bool = True
    max_auto_retries: int = 2
    # Usage tracking
    usage_count: int = 0
    success_count: int = 0
    avg_quality_score: float = 0.0
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    archived_at: Optional[datetime] = None

    def render_prompt(self, variables: Dict[str, str]) -> str:
        """
        WHAT: Renders user prompt template with variables
        WHERE: Called during generation
        WHY: Substitutes variables into template

        Args:
            variables: Dictionary of variable values

        Returns:
            Rendered prompt string
        """
        prompt = self.user_prompt_template
        for var_name in self.required_variables:
            if var_name not in variables:
                raise InvalidGenerationParametersException(
                    f"Missing required variable: {var_name}"
                )
            prompt = prompt.replace(f"{{{{{var_name}}}}}", variables[var_name])
        return prompt

    def record_usage(self, success: bool, quality_score: Optional[int] = None) -> None:
        """
        WHAT: Records template usage for analytics
        WHERE: Called after generation attempt
        WHY: Tracks template effectiveness

        Args:
            success: Whether generation succeeded
            quality_score: Optional quality score
        """
        self.usage_count += 1
        if success:
            self.success_count += 1
        if quality_score is not None:
            # Update rolling average
            total_quality = self.avg_quality_score * (self.success_count - 1)
            self.avg_quality_score = (total_quality + quality_score) / self.success_count
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """
        WHAT: Archives the template
        WHERE: Called when template should no longer be used
        WHY: Preserves template for history while preventing new usage
        """
        self.is_archived = True
        self.is_active = False
        self.archived_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_success_rate(self) -> float:
        """
        WHAT: Calculates template success rate
        WHERE: Called for analytics
        WHY: Measures template effectiveness
        """
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count


# ============================================================================
# CONTENT REFINEMENT ENTITY
# ============================================================================

@dataclass
class ContentRefinement:
    """
    WHAT: A refinement operation on generated content
    WHERE: Created when user requests content improvement
    WHY: Tracks iterative content improvements based on feedback
         to enhance quality without full regeneration

    Business Rules:
    - Refinements are linked to original result
    - Maximum refinement iterations prevent infinite loops
    - Feedback guides refinement direction
    - Each refinement creates new result version
    """
    id: UUID
    result_id: UUID
    refinement_type: RefinementType
    requester_id: UUID
    # Refinement details
    feedback: str = ""
    specific_instructions: str = ""
    target_sections: List[str] = field(default_factory=list)  # Specific sections to refine
    # Configuration
    preserve_structure: bool = True
    max_changes: int = 5  # Maximum number of changes
    # Results
    refined_result_id: Optional[UUID] = None
    status: GenerationStatus = GenerationStatus.PENDING
    changes_made: List[str] = field(default_factory=list)
    # Quality comparison
    original_quality_score: int = 0
    refined_quality_score: int = 0
    quality_improvement: int = 0
    # Iteration tracking
    iteration_number: int = 1
    max_iterations: int = 5
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def complete(self, refined_result_id: UUID, refined_quality_score: int) -> None:
        """
        WHAT: Marks refinement as completed
        WHERE: Called when refinement succeeds
        WHY: Records refinement outcome

        Args:
            refined_result_id: ID of refined result
            refined_quality_score: Quality score of refined content
        """
        self.refined_result_id = refined_result_id
        self.refined_quality_score = refined_quality_score
        self.quality_improvement = refined_quality_score - self.original_quality_score
        self.status = GenerationStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        """
        WHAT: Marks refinement as failed
        WHERE: Called when refinement errors
        WHY: Records failure for debugging
        """
        self.status = GenerationStatus.FAILED
        self.changes_made = [f"Error: {error}"]
        self.completed_at = datetime.utcnow()

    def can_refine_further(self) -> bool:
        """
        WHAT: Checks if more refinements are allowed
        WHERE: Called before creating new refinement
        WHY: Prevents infinite refinement loops
        """
        return self.iteration_number < self.max_iterations


# ============================================================================
# BATCH GENERATION ENTITY
# ============================================================================

@dataclass
class BatchGeneration:
    """
    WHAT: A batch of multiple content generation requests
    WHERE: Created for bulk content generation operations
    WHY: Enables efficient generation of multiple related content pieces
         with shared context and parameters

    Business Rules:
    - Batch size limited for resource management
    - Items share common parameters but can have overrides
    - Partial completion is tracked
    - Failed items can be retried individually
    """
    id: UUID
    name: str
    description: str
    course_id: UUID
    requester_id: UUID
    organization_id: Optional[UUID] = None
    # Batch configuration
    shared_parameters: Dict[str, Any] = field(default_factory=dict)
    content_types: List[GenerationContentType] = field(default_factory=list)
    target_modules: List[UUID] = field(default_factory=list)
    # Batch limits
    max_batch_size: int = 50
    parallel_workers: int = 5
    # Items
    request_ids: List[UUID] = field(default_factory=list)
    # Status tracking
    status: BatchStatus = BatchStatus.CREATED
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    # Progress
    progress_percentage: float = 0.0
    current_item_index: int = 0
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    # Costs
    total_estimated_cost: Decimal = Decimal("0.00")
    actual_cost: Decimal = Decimal("0.00")
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_request(self, request_id: UUID) -> None:
        """
        WHAT: Adds a generation request to the batch
        WHERE: Called when building batch
        WHY: Tracks requests in batch

        Args:
            request_id: ID of generation request

        Raises:
            BatchSizeLimitException: If batch is at max capacity
        """
        if len(self.request_ids) >= self.max_batch_size:
            raise BatchSizeLimitException(
                f"Batch size limit of {self.max_batch_size} exceeded"
            )
        self.request_ids.append(request_id)
        self.total_items = len(self.request_ids)
        self.updated_at = datetime.utcnow()

    def start(self) -> None:
        """
        WHAT: Starts batch processing
        WHERE: Called when batch begins
        WHY: Tracks batch execution start
        """
        self.status = BatchStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._estimate_completion()

    def record_item_completion(self, success: bool, cost: Decimal = Decimal("0.00")) -> None:
        """
        WHAT: Records completion of a batch item
        WHERE: Called as each item completes
        WHY: Tracks batch progress

        Args:
            success: Whether item succeeded
            cost: Cost of item generation
        """
        if success:
            self.completed_items += 1
        else:
            self.failed_items += 1
        self.actual_cost += cost
        self.current_item_index += 1
        self._update_progress()
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """
        WHAT: Marks batch as completed
        WHERE: Called when all items processed
        WHY: Finalizes batch status
        """
        if self.failed_items > 0 and self.completed_items > 0:
            self.status = BatchStatus.PARTIAL
        elif self.failed_items == self.total_items:
            self.status = BatchStatus.FAILED
        else:
            self.status = BatchStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """
        WHAT: Cancels batch processing
        WHERE: Called when user cancels
        WHY: Stops batch and records cancellation
        """
        self.status = BatchStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def _update_progress(self) -> None:
        """Updates progress percentage"""
        if self.total_items > 0:
            processed = self.completed_items + self.failed_items
            self.progress_percentage = (processed / self.total_items) * 100

    def _estimate_completion(self) -> None:
        """Estimates completion time based on average item time"""
        # Estimate 30 seconds per item
        estimated_seconds = self.total_items * 30 / self.parallel_workers
        self.estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)

    def get_remaining_items(self) -> int:
        """Gets count of items not yet processed"""
        return self.total_items - (self.completed_items + self.failed_items)


# ============================================================================
# GENERATION ANALYTICS ENTITY
# ============================================================================

@dataclass
class GenerationAnalytics:
    """
    WHAT: Analytics tracking for content generation operations
    WHERE: Updated after each generation operation
    WHY: Provides insights into generation performance, costs, and quality
         for optimization and reporting

    Business Rules:
    - Analytics are aggregated at organization and global levels
    - Historical data enables trend analysis
    - Cost tracking enables budget management
    - Quality trends guide template improvements
    """
    id: UUID
    organization_id: Optional[UUID] = None
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: Optional[datetime] = None
    # Volume metrics
    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    cached_responses: int = 0
    # Performance metrics
    avg_generation_time_seconds: float = 0.0
    min_generation_time_seconds: float = 0.0
    max_generation_time_seconds: float = 0.0
    total_generation_time_seconds: float = 0.0
    # Token metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_tokens_per_request: float = 0.0
    # Cost metrics
    total_cost: Decimal = Decimal("0.00")
    avg_cost_per_request: Decimal = Decimal("0.00")
    cost_savings_from_cache: Decimal = Decimal("0.00")
    # Quality metrics
    avg_quality_score: float = 0.0
    excellent_count: int = 0
    good_count: int = 0
    acceptable_count: int = 0
    needs_work_count: int = 0
    poor_count: int = 0
    # Content type breakdown
    content_type_counts: Dict[str, int] = field(default_factory=dict)
    # Refinement metrics
    total_refinements: int = 0
    successful_refinements: int = 0
    avg_quality_improvement: float = 0.0
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def record_generation(
        self,
        success: bool,
        cached: bool,
        generation_time: float,
        input_tokens: int,
        output_tokens: int,
        cost: Decimal,
        quality_level: Optional[QualityLevel],
        content_type: GenerationContentType
    ) -> None:
        """
        WHAT: Records a generation operation
        WHERE: Called after each generation completes
        WHY: Updates analytics metrics

        Args:
            success: Whether generation succeeded
            cached: Whether result was from cache
            generation_time: Time taken in seconds
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
            cost: Cost of generation
            quality_level: Quality level of result
            content_type: Type of content generated
        """
        self.total_requests += 1
        if success:
            self.completed_requests += 1
        else:
            self.failed_requests += 1
        if cached:
            self.cached_responses += 1
            self.cost_savings_from_cache += cost

        # Update time metrics
        self.total_generation_time_seconds += generation_time
        self.avg_generation_time_seconds = (
            self.total_generation_time_seconds / self.total_requests
        )
        if generation_time < self.min_generation_time_seconds or self.min_generation_time_seconds == 0:
            self.min_generation_time_seconds = generation_time
        if generation_time > self.max_generation_time_seconds:
            self.max_generation_time_seconds = generation_time

        # Update token metrics
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.avg_tokens_per_request = (
            (self.total_input_tokens + self.total_output_tokens) / self.total_requests
        )

        # Update cost metrics
        self.total_cost += cost
        self.avg_cost_per_request = self.total_cost / Decimal(str(self.total_requests))

        # Update quality metrics
        if quality_level:
            self._update_quality_counts(quality_level)

        # Update content type counts
        content_type_key = content_type.value
        self.content_type_counts[content_type_key] = (
            self.content_type_counts.get(content_type_key, 0) + 1
        )

        self.updated_at = datetime.utcnow()

    def _update_quality_counts(self, quality_level: QualityLevel) -> None:
        """Updates quality level counters"""
        if quality_level == QualityLevel.EXCELLENT:
            self.excellent_count += 1
        elif quality_level == QualityLevel.GOOD:
            self.good_count += 1
        elif quality_level == QualityLevel.ACCEPTABLE:
            self.acceptable_count += 1
        elif quality_level == QualityLevel.NEEDS_WORK:
            self.needs_work_count += 1
        else:
            self.poor_count += 1

    def record_refinement(self, success: bool, quality_improvement: int) -> None:
        """
        WHAT: Records a refinement operation
        WHERE: Called after refinement completes
        WHY: Tracks refinement effectiveness

        Args:
            success: Whether refinement succeeded
            quality_improvement: Change in quality score
        """
        self.total_refinements += 1
        if success:
            self.successful_refinements += 1
            # Update rolling average
            total_improvement = self.avg_quality_improvement * (self.successful_refinements - 1)
            self.avg_quality_improvement = (
                (total_improvement + quality_improvement) / self.successful_refinements
            )
        self.updated_at = datetime.utcnow()

    def get_success_rate(self) -> float:
        """Gets overall generation success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.completed_requests / self.total_requests

    def get_cache_hit_rate(self) -> float:
        """Gets cache hit rate"""
        if self.completed_requests == 0:
            return 0.0
        return self.cached_responses / self.completed_requests

    def get_quality_distribution(self) -> Dict[str, float]:
        """Gets quality level distribution as percentages"""
        total_scored = (
            self.excellent_count + self.good_count + self.acceptable_count +
            self.needs_work_count + self.poor_count
        )
        if total_scored == 0:
            return {}
        return {
            "excellent": self.excellent_count / total_scored * 100,
            "good": self.good_count / total_scored * 100,
            "acceptable": self.acceptable_count / total_scored * 100,
            "needs_work": self.needs_work_count / total_scored * 100,
            "poor": self.poor_count / total_scored * 100
        }
