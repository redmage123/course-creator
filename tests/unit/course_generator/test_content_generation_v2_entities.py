"""
Unit Tests for Content Generation V2 Domain Entities

WHAT: Comprehensive unit tests for AI-powered content generation entities
WHERE: Tests for course_generator.domain.entities.content_generation_v2
WHY: Validates business logic, state transitions, and data integrity
     for all content generation V2 domain entities

Enhancement 4: AI-Powered Content Generation V2

Test Categories:
1. GenerationRequest entity tests
2. GenerationResult entity tests
3. ContentQualityScore entity tests
4. GenerationTemplate entity tests
5. ContentRefinement entity tests
6. BatchGeneration entity tests
7. GenerationAnalytics entity tests
8. Enum validation tests
9. Exception tests
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import sys
from pathlib import Path

# Add service path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-generator'))

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


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_generation_request():
    """Create a sample generation request for testing."""
    return GenerationRequest(
        id=uuid4(),
        course_id=uuid4(),
        content_type=GenerationContentType.SYLLABUS,
        requester_id=uuid4(),
        organization_id=uuid4(),
        parameters={"topic": "Python Programming"},
        difficulty_level="intermediate",
        target_audience="developers",
        language="en"
    )


@pytest.fixture
def sample_generation_result():
    """Create a sample generation result for testing."""
    return GenerationResult(
        id=uuid4(),
        request_id=uuid4(),
        course_id=uuid4(),
        content_type=GenerationContentType.SYLLABUS,
        raw_output="Sample generated content",
        processed_content={"sections": ["intro", "main", "conclusion"]},
        model_used="claude-3-sonnet"
    )


@pytest.fixture
def sample_quality_score():
    """Create a sample quality score for testing."""
    return ContentQualityScore(
        id=uuid4(),
        result_id=uuid4(),
        accuracy_score=85,
        relevance_score=80,
        completeness_score=75,
        clarity_score=90,
        structure_score=70,
        engagement_score=65,
        difficulty_alignment_score=80
    )


@pytest.fixture
def sample_template():
    """Create a sample generation template for testing."""
    return GenerationTemplate(
        id=uuid4(),
        name="Test Template",
        description="A test template",
        content_type=GenerationContentType.QUIZ,
        category=TemplateCategory.STANDARD,
        system_prompt="You are an expert quiz creator",
        user_prompt_template="Create a quiz about {{topic}} for {{audience}}",
        required_variables=["topic", "audience"],
        creator_id=uuid4()
    )


@pytest.fixture
def sample_refinement():
    """Create a sample refinement for testing."""
    return ContentRefinement(
        id=uuid4(),
        result_id=uuid4(),
        refinement_type=RefinementType.EXPAND,
        requester_id=uuid4(),
        feedback="Please add more examples",
        original_quality_score=75
    )


@pytest.fixture
def sample_batch():
    """Create a sample batch generation for testing."""
    return BatchGeneration(
        id=uuid4(),
        name="Test Batch",
        description="A test batch",
        course_id=uuid4(),
        requester_id=uuid4(),
        content_types=[GenerationContentType.SYLLABUS, GenerationContentType.QUIZ],
        request_ids=[uuid4(), uuid4()],  # Start with 2 requests
        total_items=2
    )


@pytest.fixture
def sample_analytics():
    """Create sample analytics for testing."""
    return GenerationAnalytics(
        id=uuid4(),
        organization_id=uuid4()
    )


# ============================================================================
# GENERATION REQUEST TESTS
# ============================================================================

class TestGenerationRequest:
    """Tests for GenerationRequest entity."""

    def test_creation_with_defaults(self):
        """Test creating request with default values."""
        request = GenerationRequest(
            id=uuid4(),
            course_id=uuid4(),
            content_type=GenerationContentType.SYLLABUS,
            requester_id=uuid4()
        )

        assert request.status == GenerationStatus.PENDING
        assert request.difficulty_level == "intermediate"
        assert request.target_audience == "general"
        assert request.language == "en"
        assert request.use_rag == True
        assert request.use_cache == True
        assert request.max_retries == 3
        assert request.retry_count == 0

    def test_start_generation(self, sample_generation_request):
        """Test starting a generation request."""
        sample_generation_request.start()

        assert sample_generation_request.status == GenerationStatus.GENERATING
        assert sample_generation_request.started_at is not None

    def test_complete_generation(self, sample_generation_request):
        """Test completing a generation request."""
        result_id = uuid4()
        sample_generation_request.start()
        sample_generation_request.complete(result_id, input_tokens=100, output_tokens=500)

        assert sample_generation_request.status == GenerationStatus.COMPLETED
        assert sample_generation_request.result_id == result_id
        assert sample_generation_request.input_tokens == 100
        assert sample_generation_request.output_tokens == 500
        assert sample_generation_request.completed_at is not None
        assert sample_generation_request.estimated_cost > Decimal("0")

    def test_fail_generation(self, sample_generation_request):
        """Test failing a generation request."""
        sample_generation_request.start()
        sample_generation_request.fail("AI model error")

        assert sample_generation_request.status == GenerationStatus.FAILED
        assert sample_generation_request.error_message == "AI model error"
        assert sample_generation_request.completed_at is not None

    def test_cancel_generation(self, sample_generation_request):
        """Test canceling a generation request."""
        sample_generation_request.cancel()

        assert sample_generation_request.status == GenerationStatus.CANCELLED
        assert sample_generation_request.completed_at is not None

    def test_timeout_generation(self, sample_generation_request):
        """Test timeout of a generation request."""
        sample_generation_request.timeout()

        assert sample_generation_request.status == GenerationStatus.TIMEOUT
        assert "timeout" in sample_generation_request.error_message.lower()

    def test_retry_allowed(self, sample_generation_request):
        """Test retry when under limit."""
        sample_generation_request.fail("Temporary error")

        assert sample_generation_request.retry() == True
        assert sample_generation_request.retry_count == 1
        assert sample_generation_request.status == GenerationStatus.PENDING

    def test_retry_exhausted(self, sample_generation_request):
        """Test retry when limit exceeded."""
        sample_generation_request.retry_count = 3

        assert sample_generation_request.retry() == False

    def test_is_timed_out_false(self, sample_generation_request):
        """Test timeout check when not started."""
        assert sample_generation_request.is_timed_out() == False

    def test_is_timed_out_true(self, sample_generation_request):
        """Test timeout check when exceeded."""
        sample_generation_request.started_at = datetime.utcnow() - timedelta(seconds=400)
        sample_generation_request.timeout_seconds = 300

        assert sample_generation_request.is_timed_out() == True

    def test_get_duration_seconds(self, sample_generation_request):
        """Test duration calculation."""
        sample_generation_request.started_at = datetime.utcnow() - timedelta(seconds=30)
        sample_generation_request.completed_at = datetime.utcnow()

        duration = sample_generation_request.get_duration_seconds()
        assert 29 <= duration <= 31

    def test_cost_calculation(self, sample_generation_request):
        """Test cost calculation based on token usage."""
        sample_generation_request.complete(uuid4(), input_tokens=1000, output_tokens=2000)

        # Expected: (1000/1000 * 0.003) + (2000/1000 * 0.015) = 0.003 + 0.030 = 0.033
        assert sample_generation_request.estimated_cost == Decimal("0.033")


# ============================================================================
# GENERATION RESULT TESTS
# ============================================================================

class TestGenerationResult:
    """Tests for GenerationResult entity."""

    def test_creation_with_defaults(self):
        """Test creating result with default values."""
        result = GenerationResult(
            id=uuid4(),
            request_id=uuid4(),
            course_id=uuid4(),
            content_type=GenerationContentType.QUIZ,
            raw_output="Quiz content"
        )

        assert result.quality_level == QualityLevel.ACCEPTABLE
        assert result.version == 1
        assert result.cached == False
        assert result.expires_at is not None

    def test_set_quality(self, sample_generation_result):
        """Test setting quality for result."""
        score_id = uuid4()
        sample_generation_result.set_quality(score_id, QualityLevel.GOOD)

        assert sample_generation_result.quality_score_id == score_id
        assert sample_generation_result.quality_level == QualityLevel.GOOD

    def test_create_refinement_version(self, sample_generation_result):
        """Test creating refinement version."""
        refined = sample_generation_result.create_refinement_version()

        assert refined.id != sample_generation_result.id
        assert refined.request_id == sample_generation_result.request_id
        assert refined.version == sample_generation_result.version + 1
        assert refined.parent_result_id == sample_generation_result.id

    def test_is_expired_false(self, sample_generation_result):
        """Test expiration check when not expired."""
        sample_generation_result.expires_at = datetime.utcnow() + timedelta(days=1)

        assert sample_generation_result.is_expired() == False

    def test_is_expired_true(self, sample_generation_result):
        """Test expiration check when expired."""
        sample_generation_result.expires_at = datetime.utcnow() - timedelta(days=1)

        assert sample_generation_result.is_expired() == True

    def test_meets_quality_threshold_acceptable(self, sample_generation_result):
        """Test quality threshold with acceptable level."""
        sample_generation_result.quality_level = QualityLevel.ACCEPTABLE

        assert sample_generation_result.meets_quality_threshold(QualityLevel.ACCEPTABLE) == True
        assert sample_generation_result.meets_quality_threshold(QualityLevel.POOR) == True
        assert sample_generation_result.meets_quality_threshold(QualityLevel.GOOD) == False

    def test_meets_quality_threshold_excellent(self, sample_generation_result):
        """Test quality threshold with excellent level."""
        sample_generation_result.quality_level = QualityLevel.EXCELLENT

        assert sample_generation_result.meets_quality_threshold(QualityLevel.EXCELLENT) == True
        assert sample_generation_result.meets_quality_threshold(QualityLevel.GOOD) == True


# ============================================================================
# CONTENT QUALITY SCORE TESTS
# ============================================================================

class TestContentQualityScore:
    """Tests for ContentQualityScore entity."""

    def test_calculate_overall_score(self, sample_quality_score):
        """Test overall score calculation."""
        sample_quality_score.calculate_overall_score()

        # With default weights, calculate expected score
        expected = int(
            85 * 0.20 +  # accuracy
            80 * 0.15 +  # relevance
            75 * 0.15 +  # completeness
            90 * 0.20 +  # clarity
            70 * 0.10 +  # structure
            65 * 0.10 +  # engagement
            80 * 0.10    # difficulty_alignment
        )
        assert sample_quality_score.overall_score == expected

    def test_quality_level_excellent(self, sample_quality_score):
        """Test quality level set to excellent."""
        sample_quality_score.accuracy_score = 95
        sample_quality_score.relevance_score = 95
        sample_quality_score.completeness_score = 90
        sample_quality_score.clarity_score = 95
        sample_quality_score.structure_score = 90
        sample_quality_score.engagement_score = 90
        sample_quality_score.difficulty_alignment_score = 90
        sample_quality_score.calculate_overall_score()

        assert sample_quality_score.quality_level == QualityLevel.EXCELLENT

    def test_quality_level_poor(self, sample_quality_score):
        """Test quality level set to poor."""
        sample_quality_score.accuracy_score = 30
        sample_quality_score.relevance_score = 30
        sample_quality_score.completeness_score = 30
        sample_quality_score.clarity_score = 30
        sample_quality_score.structure_score = 30
        sample_quality_score.engagement_score = 30
        sample_quality_score.difficulty_alignment_score = 30
        sample_quality_score.calculate_overall_score()

        assert sample_quality_score.quality_level == QualityLevel.POOR

    def test_set_dimension_score(self, sample_quality_score):
        """Test setting individual dimension score."""
        sample_quality_score.set_dimension_score("accuracy", 95)

        assert sample_quality_score.accuracy_score == 95

    def test_set_dimension_score_clamp(self, sample_quality_score):
        """Test score clamping to 0-100."""
        sample_quality_score.set_dimension_score("accuracy", 150)
        assert sample_quality_score.accuracy_score == 100

        sample_quality_score.set_dimension_score("accuracy", -10)
        assert sample_quality_score.accuracy_score == 0

    def test_get_lowest_dimensions(self, sample_quality_score):
        """Test getting lowest scoring dimensions."""
        lowest = sample_quality_score.get_lowest_dimensions(3)

        assert len(lowest) == 3
        # Should be sorted by score ascending
        assert lowest[0][1] <= lowest[1][1] <= lowest[2][1]

    def test_override_with_manual(self, sample_quality_score):
        """Test manual score override."""
        scorer_id = uuid4()
        new_scores = {"accuracy": 90, "clarity": 95}

        sample_quality_score.override_with_manual(scorer_id, new_scores)

        assert sample_quality_score.accuracy_score == 90
        assert sample_quality_score.clarity_score == 95
        assert sample_quality_score.scorer_id == scorer_id
        assert sample_quality_score.scoring_method == "manual"


# ============================================================================
# GENERATION TEMPLATE TESTS
# ============================================================================

class TestGenerationTemplate:
    """Tests for GenerationTemplate entity."""

    def test_creation_with_defaults(self):
        """Test creating template with default values."""
        template = GenerationTemplate(
            id=uuid4(),
            name="Test",
            description="Test template",
            content_type=GenerationContentType.QUIZ,
            system_prompt="System",
            user_prompt_template="User"
        )

        assert template.category == TemplateCategory.STANDARD
        assert template.is_active == True
        assert template.is_archived == False
        assert template.is_global == False

    def test_render_prompt_success(self, sample_template):
        """Test successful prompt rendering."""
        variables = {"topic": "Python", "audience": "beginners"}
        rendered = sample_template.render_prompt(variables)

        assert "Python" in rendered
        assert "beginners" in rendered

    def test_render_prompt_missing_variable(self, sample_template):
        """Test prompt rendering with missing variable."""
        variables = {"topic": "Python"}  # Missing "audience"

        with pytest.raises(InvalidGenerationParametersException):
            sample_template.render_prompt(variables)

    def test_record_usage_success(self, sample_template):
        """Test recording successful usage."""
        sample_template.record_usage(success=True, quality_score=85)

        assert sample_template.usage_count == 1
        assert sample_template.success_count == 1
        assert sample_template.avg_quality_score == 85.0

    def test_record_usage_failure(self, sample_template):
        """Test recording failed usage."""
        sample_template.record_usage(success=False)

        assert sample_template.usage_count == 1
        assert sample_template.success_count == 0

    def test_archive(self, sample_template):
        """Test archiving template."""
        sample_template.archive()

        assert sample_template.is_archived == True
        assert sample_template.is_active == False
        assert sample_template.archived_at is not None

    def test_get_success_rate(self, sample_template):
        """Test success rate calculation."""
        sample_template.usage_count = 10
        sample_template.success_count = 8

        assert sample_template.get_success_rate() == 0.8

    def test_get_success_rate_no_usage(self, sample_template):
        """Test success rate with no usage."""
        assert sample_template.get_success_rate() == 0.0


# ============================================================================
# CONTENT REFINEMENT TESTS
# ============================================================================

class TestContentRefinement:
    """Tests for ContentRefinement entity."""

    def test_creation_with_defaults(self):
        """Test creating refinement with default values."""
        refinement = ContentRefinement(
            id=uuid4(),
            result_id=uuid4(),
            refinement_type=RefinementType.EXPAND,
            requester_id=uuid4(),
            feedback="Add more content"
        )

        assert refinement.status == GenerationStatus.PENDING
        assert refinement.iteration_number == 1
        assert refinement.max_iterations == 5
        assert refinement.preserve_structure == True

    def test_complete_refinement(self, sample_refinement):
        """Test completing refinement."""
        refined_result_id = uuid4()
        sample_refinement.complete(refined_result_id, refined_quality_score=85)

        assert sample_refinement.refined_result_id == refined_result_id
        assert sample_refinement.refined_quality_score == 85
        assert sample_refinement.quality_improvement == 10  # 85 - 75
        assert sample_refinement.status == GenerationStatus.COMPLETED
        assert sample_refinement.completed_at is not None

    def test_fail_refinement(self, sample_refinement):
        """Test failing refinement."""
        sample_refinement.fail("Error occurred")

        assert sample_refinement.status == GenerationStatus.FAILED
        assert "Error" in sample_refinement.changes_made[0]

    def test_can_refine_further_yes(self, sample_refinement):
        """Test can refine when under limit."""
        sample_refinement.iteration_number = 3

        assert sample_refinement.can_refine_further() == True

    def test_can_refine_further_no(self, sample_refinement):
        """Test cannot refine when at limit."""
        sample_refinement.iteration_number = 5

        assert sample_refinement.can_refine_further() == False


# ============================================================================
# BATCH GENERATION TESTS
# ============================================================================

class TestBatchGeneration:
    """Tests for BatchGeneration entity."""

    def test_creation_with_defaults(self):
        """Test creating batch with default values."""
        batch = BatchGeneration(
            id=uuid4(),
            name="Test Batch",
            description="Test",
            course_id=uuid4(),
            requester_id=uuid4()
        )

        assert batch.status == BatchStatus.CREATED
        assert batch.max_batch_size == 50
        assert batch.parallel_workers == 5

    def test_add_request(self, sample_batch):
        """Test adding request to batch."""
        request_id = uuid4()
        sample_batch.add_request(request_id)

        assert request_id in sample_batch.request_ids
        assert sample_batch.total_items == 3  # Original 2 + 1

    def test_add_request_exceeds_limit(self, sample_batch):
        """Test adding request when at limit."""
        sample_batch.max_batch_size = 2
        sample_batch.request_ids = [uuid4(), uuid4()]

        with pytest.raises(BatchSizeLimitException):
            sample_batch.add_request(uuid4())

    def test_start_batch(self, sample_batch):
        """Test starting batch processing."""
        sample_batch.start()

        assert sample_batch.status == BatchStatus.PROCESSING
        assert sample_batch.started_at is not None
        assert sample_batch.estimated_completion is not None

    def test_record_item_completion_success(self, sample_batch):
        """Test recording successful item completion."""
        sample_batch.total_items = 10
        sample_batch.record_item_completion(success=True, cost=Decimal("0.05"))

        assert sample_batch.completed_items == 1
        assert sample_batch.failed_items == 0
        assert sample_batch.actual_cost == Decimal("0.05")
        assert sample_batch.progress_percentage == 10.0

    def test_record_item_completion_failure(self, sample_batch):
        """Test recording failed item completion."""
        sample_batch.total_items = 10
        sample_batch.record_item_completion(success=False)

        assert sample_batch.completed_items == 0
        assert sample_batch.failed_items == 1
        assert sample_batch.progress_percentage == 10.0

    def test_complete_all_success(self, sample_batch):
        """Test completing batch with all successes."""
        sample_batch.total_items = 2
        sample_batch.completed_items = 2
        sample_batch.failed_items = 0
        sample_batch.complete()

        assert sample_batch.status == BatchStatus.COMPLETED
        assert sample_batch.progress_percentage == 100.0

    def test_complete_partial(self, sample_batch):
        """Test completing batch with partial success."""
        sample_batch.total_items = 10
        sample_batch.completed_items = 7
        sample_batch.failed_items = 3
        sample_batch.complete()

        assert sample_batch.status == BatchStatus.PARTIAL

    def test_complete_all_failed(self, sample_batch):
        """Test completing batch with all failures."""
        sample_batch.total_items = 5
        sample_batch.completed_items = 0
        sample_batch.failed_items = 5
        sample_batch.complete()

        assert sample_batch.status == BatchStatus.FAILED

    def test_cancel(self, sample_batch):
        """Test canceling batch."""
        sample_batch.cancel()

        assert sample_batch.status == BatchStatus.CANCELLED
        assert sample_batch.completed_at is not None

    def test_get_remaining_items(self, sample_batch):
        """Test getting remaining items count."""
        sample_batch.total_items = 10
        sample_batch.completed_items = 3
        sample_batch.failed_items = 2

        assert sample_batch.get_remaining_items() == 5


# ============================================================================
# GENERATION ANALYTICS TESTS
# ============================================================================

class TestGenerationAnalytics:
    """Tests for GenerationAnalytics entity."""

    def test_creation_with_defaults(self):
        """Test creating analytics with default values."""
        analytics = GenerationAnalytics(
            id=uuid4()
        )

        assert analytics.total_requests == 0
        assert analytics.completed_requests == 0
        assert analytics.avg_quality_score == 0.0

    def test_record_generation_success(self, sample_analytics):
        """Test recording successful generation."""
        sample_analytics.record_generation(
            success=True,
            cached=False,
            generation_time=30.0,
            input_tokens=100,
            output_tokens=500,
            cost=Decimal("0.05"),
            quality_level=QualityLevel.GOOD,
            content_type=GenerationContentType.SYLLABUS
        )

        assert sample_analytics.total_requests == 1
        assert sample_analytics.completed_requests == 1
        assert sample_analytics.failed_requests == 0
        assert sample_analytics.good_count == 1
        assert sample_analytics.total_cost == Decimal("0.05")

    def test_record_generation_failure(self, sample_analytics):
        """Test recording failed generation."""
        sample_analytics.record_generation(
            success=False,
            cached=False,
            generation_time=5.0,
            input_tokens=50,
            output_tokens=0,
            cost=Decimal("0.01"),
            quality_level=None,
            content_type=GenerationContentType.QUIZ
        )

        assert sample_analytics.total_requests == 1
        assert sample_analytics.completed_requests == 0
        assert sample_analytics.failed_requests == 1

    def test_record_generation_cached(self, sample_analytics):
        """Test recording cached response."""
        sample_analytics.record_generation(
            success=True,
            cached=True,
            generation_time=0.0,
            input_tokens=0,
            output_tokens=0,
            cost=Decimal("0.05"),
            quality_level=QualityLevel.EXCELLENT,
            content_type=GenerationContentType.SLIDES
        )

        assert sample_analytics.cached_responses == 1
        assert sample_analytics.cost_savings_from_cache == Decimal("0.05")

    def test_record_refinement_success(self, sample_analytics):
        """Test recording successful refinement."""
        sample_analytics.record_refinement(success=True, quality_improvement=10)

        assert sample_analytics.total_refinements == 1
        assert sample_analytics.successful_refinements == 1
        assert sample_analytics.avg_quality_improvement == 10.0

    def test_record_refinement_failure(self, sample_analytics):
        """Test recording failed refinement."""
        sample_analytics.record_refinement(success=False, quality_improvement=0)

        assert sample_analytics.total_refinements == 1
        assert sample_analytics.successful_refinements == 0

    def test_get_success_rate(self, sample_analytics):
        """Test success rate calculation."""
        sample_analytics.total_requests = 10
        sample_analytics.completed_requests = 8

        assert sample_analytics.get_success_rate() == 0.8

    def test_get_cache_hit_rate(self, sample_analytics):
        """Test cache hit rate calculation."""
        sample_analytics.completed_requests = 10
        sample_analytics.cached_responses = 4

        assert sample_analytics.get_cache_hit_rate() == 0.4

    def test_get_quality_distribution(self, sample_analytics):
        """Test quality distribution calculation."""
        sample_analytics.excellent_count = 10
        sample_analytics.good_count = 30
        sample_analytics.acceptable_count = 40
        sample_analytics.needs_work_count = 15
        sample_analytics.poor_count = 5

        distribution = sample_analytics.get_quality_distribution()

        assert distribution["excellent"] == 10.0
        assert distribution["good"] == 30.0
        assert distribution["acceptable"] == 40.0
        assert distribution["needs_work"] == 15.0
        assert distribution["poor"] == 5.0


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Tests for content generation enums."""

    def test_generation_content_types(self):
        """Test all content types are defined."""
        assert GenerationContentType.SYLLABUS.value == "syllabus"
        assert GenerationContentType.SLIDES.value == "slides"
        assert GenerationContentType.QUIZ.value == "quiz"
        assert GenerationContentType.EXERCISE.value == "exercise"
        assert GenerationContentType.LEARNING_OBJECTIVES.value == "learning_objectives"
        assert GenerationContentType.CASE_STUDY.value == "case_study"

    def test_generation_status(self):
        """Test all generation statuses are defined."""
        assert GenerationStatus.PENDING.value == "pending"
        assert GenerationStatus.GENERATING.value == "generating"
        assert GenerationStatus.COMPLETED.value == "completed"
        assert GenerationStatus.FAILED.value == "failed"
        assert GenerationStatus.TIMEOUT.value == "timeout"

    def test_quality_levels(self):
        """Test all quality levels are defined."""
        assert QualityLevel.EXCELLENT.value == "excellent"
        assert QualityLevel.GOOD.value == "good"
        assert QualityLevel.ACCEPTABLE.value == "acceptable"
        assert QualityLevel.NEEDS_WORK.value == "needs_work"
        assert QualityLevel.POOR.value == "poor"

    def test_refinement_types(self):
        """Test all refinement types are defined."""
        assert RefinementType.EXPAND.value == "expand"
        assert RefinementType.SIMPLIFY.value == "simplify"
        assert RefinementType.CORRECT.value == "correct"
        assert RefinementType.ADD_EXAMPLES.value == "add_examples"

    def test_batch_statuses(self):
        """Test all batch statuses are defined."""
        assert BatchStatus.CREATED.value == "created"
        assert BatchStatus.PROCESSING.value == "processing"
        assert BatchStatus.COMPLETED.value == "completed"
        assert BatchStatus.PARTIAL.value == "partial"
        assert BatchStatus.CANCELLED.value == "cancelled"

    def test_template_categories(self):
        """Test all template categories are defined."""
        assert TemplateCategory.STANDARD.value == "standard"
        assert TemplateCategory.TECHNICAL.value == "technical"
        assert TemplateCategory.BUSINESS.value == "business"
        assert TemplateCategory.CUSTOM.value == "custom"


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestExceptions:
    """Tests for content generation exceptions."""

    def test_content_generation_exception(self):
        """Test base content generation exception."""
        with pytest.raises(ContentGenerationException):
            raise ContentGenerationException("Test error")

    def test_invalid_generation_parameters_exception(self):
        """Test invalid parameters exception."""
        with pytest.raises(InvalidGenerationParametersException):
            raise InvalidGenerationParametersException("Invalid params")

    def test_generation_timeout_exception(self):
        """Test generation timeout exception."""
        with pytest.raises(GenerationTimeoutException):
            raise GenerationTimeoutException("Timeout")

    def test_quality_threshold_not_met_exception(self):
        """Test quality threshold exception."""
        with pytest.raises(QualityThresholdNotMetException):
            raise QualityThresholdNotMetException("Low quality")

    def test_max_refinements_exceeded_exception(self):
        """Test max refinements exception."""
        with pytest.raises(MaxRefinementsExceededException):
            raise MaxRefinementsExceededException("Max reached")

    def test_batch_size_limit_exception(self):
        """Test batch size limit exception."""
        with pytest.raises(BatchSizeLimitException):
            raise BatchSizeLimitException("Too large")

    def test_template_not_found_exception(self):
        """Test template not found exception."""
        with pytest.raises(TemplateNotFoundException):
            raise TemplateNotFoundException("Not found")

    def test_exception_inheritance(self):
        """Test exception inheritance hierarchy."""
        # All specific exceptions should inherit from base
        assert issubclass(InvalidGenerationParametersException, ContentGenerationException)
        assert issubclass(GenerationTimeoutException, ContentGenerationException)
        assert issubclass(QualityThresholdNotMetException, ContentGenerationException)
        assert issubclass(MaxRefinementsExceededException, ContentGenerationException)
        assert issubclass(BatchSizeLimitException, ContentGenerationException)
        assert issubclass(TemplateNotFoundException, ContentGenerationException)


# ============================================================================
# INTEGRATION TESTS (Entity Interactions)
# ============================================================================

class TestEntityIntegrations:
    """Tests for entity interactions."""

    def test_request_to_result_workflow(self):
        """Test complete request-to-result workflow."""
        # Create request
        request = GenerationRequest(
            id=uuid4(),
            course_id=uuid4(),
            content_type=GenerationContentType.QUIZ,
            requester_id=uuid4()
        )

        # Start generation
        request.start()
        assert request.status == GenerationStatus.GENERATING

        # Create result
        result = GenerationResult(
            id=uuid4(),
            request_id=request.id,
            course_id=request.course_id,
            content_type=request.content_type,
            raw_output="Generated quiz"
        )

        # Complete request
        request.complete(result.id, 100, 500)
        assert request.status == GenerationStatus.COMPLETED
        assert request.result_id == result.id

    def test_result_to_quality_workflow(self):
        """Test result quality scoring workflow."""
        result = GenerationResult(
            id=uuid4(),
            request_id=uuid4(),
            course_id=uuid4(),
            content_type=GenerationContentType.SYLLABUS,
            raw_output="Content"
        )

        # Create quality score
        score = ContentQualityScore(
            id=uuid4(),
            result_id=result.id,
            accuracy_score=85,
            relevance_score=80,
            completeness_score=75,
            clarity_score=90,
            structure_score=70,
            engagement_score=65,
            difficulty_alignment_score=80
        )
        score.calculate_overall_score()

        # Link score to result
        result.set_quality(score.id, score.quality_level)

        assert result.quality_score_id == score.id
        assert result.quality_level == score.quality_level

    def test_refinement_version_chain(self):
        """Test refinement version chain."""
        # Original result
        original = GenerationResult(
            id=uuid4(),
            request_id=uuid4(),
            course_id=uuid4(),
            content_type=GenerationContentType.SLIDES,
            raw_output="Original content",
            version=1
        )

        # First refinement
        v2 = original.create_refinement_version()
        v2.raw_output = "Refined content v2"

        # Second refinement
        v3 = v2.create_refinement_version()
        v3.raw_output = "Refined content v3"

        assert v2.version == 2
        assert v2.parent_result_id == original.id

        assert v3.version == 3
        assert v3.parent_result_id == v2.id

    def test_batch_with_requests(self):
        """Test batch with multiple requests."""
        batch = BatchGeneration(
            id=uuid4(),
            name="Test Batch",
            description="Test",
            course_id=uuid4(),
            requester_id=uuid4(),
            content_types=[
                GenerationContentType.SYLLABUS,
                GenerationContentType.QUIZ,
                GenerationContentType.SLIDES
            ],
            total_items=3
        )

        # Add requests
        for _ in range(3):
            batch.add_request(uuid4())

        batch.start()
        assert batch.status == BatchStatus.PROCESSING

        # Simulate completions
        batch.record_item_completion(success=True, cost=Decimal("0.05"))
        batch.record_item_completion(success=True, cost=Decimal("0.04"))
        batch.record_item_completion(success=False)

        batch.complete()

        assert batch.status == BatchStatus.PARTIAL
        assert batch.completed_items == 2
        assert batch.failed_items == 1
        assert batch.actual_cost == Decimal("0.09")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
