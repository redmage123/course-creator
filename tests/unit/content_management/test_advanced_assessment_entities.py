"""
Unit Tests for Advanced Assessment Domain Entities

WHAT: Comprehensive unit tests for advanced assessment domain entities including
      rubrics, competencies, portfolios, peer reviews, and submissions.

WHERE: Tests for content-management service domain layer entities.

WHY: Ensures advanced assessment domain logic is correct and validates:
     - Entity creation and validation
     - Business rule enforcement
     - Status transitions and workflows
     - Score calculations and analytics
     - Error handling and exceptions

Test Coverage:
- 7 Custom exception types
- 5 Enumeration types with utility methods
- 10 Domain entities with comprehensive validation
- Complex workflows (peer review, portfolio, project milestones)
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

from content_management.domain.entities.advanced_assessment import (
    # Exceptions
    AdvancedAssessmentError,
    AssessmentValidationError,
    RubricValidationError,
    SubmissionError,
    PeerReviewError,
    CompetencyError,
    PortfolioError,
    ProjectError,
    # Enums
    AssessmentType,
    AssessmentStatus,
    SubmissionStatus,
    ProficiencyLevel,
    ReviewType,
    # Entities
    RubricPerformanceLevel,
    RubricCriterion,
    AssessmentRubric,
    Competency,
    CompetencyProgress,
    ProjectMilestone,
    PortfolioArtifact,
    PeerReviewAssignment,
    PeerReview,
    AdvancedAssessment,
    AssessmentSubmission,
    RubricEvaluation,
    AssessmentAnalytics,
)


# ============================================================================
# EXCEPTION TESTS
# Verify exception hierarchy and error handling
# ============================================================================

class TestExceptionHierarchy:
    """
    Tests for custom exception hierarchy.

    WHAT: Validates exception inheritance and categorization.
    WHY: Proper exception hierarchy enables granular error handling
         at service and API layers.
    """

    def test_all_exceptions_inherit_from_base(self):
        """All custom exceptions should inherit from AdvancedAssessmentError."""
        exceptions = [
            AssessmentValidationError,
            RubricValidationError,
            SubmissionError,
            PeerReviewError,
            CompetencyError,
            PortfolioError,
            ProjectError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, AdvancedAssessmentError)

    def test_base_exception_inherits_from_exception(self):
        """Base exception should inherit from Python's Exception."""
        assert issubclass(AdvancedAssessmentError, Exception)

    def test_exception_messages_are_preserved(self):
        """Exception messages should be accessible."""
        message = "Test error message"
        exc = AssessmentValidationError(message)
        assert str(exc) == message

    def test_exceptions_can_be_caught_by_base_class(self):
        """All specific exceptions should be catchable by base class."""
        with pytest.raises(AdvancedAssessmentError):
            raise RubricValidationError("Test")


# ============================================================================
# ENUMERATION TESTS
# Verify enum values and utility methods
# ============================================================================

class TestAssessmentType:
    """Tests for AssessmentType enumeration."""

    def test_all_assessment_types_defined(self):
        """All 10 assessment types should be defined."""
        expected_types = {
            'performance', 'peer_review', 'portfolio', 'competency',
            'project', 'rubric', 'presentation', 'interview',
            'simulation', 'self_reflection'
        }
        actual_types = {t.value for t in AssessmentType}
        assert actual_types == expected_types

    def test_assessment_type_values_are_strings(self):
        """Assessment type values should be lowercase strings."""
        for assessment_type in AssessmentType:
            assert isinstance(assessment_type.value, str)
            assert assessment_type.value.islower() or '_' in assessment_type.value


class TestAssessmentStatus:
    """Tests for AssessmentStatus enumeration."""

    def test_all_statuses_defined(self):
        """All assessment statuses should be defined."""
        expected = {
            'draft', 'published', 'in_progress', 'submitted',
            'under_review', 'requires_revision', 'completed', 'archived'
        }
        actual = {s.value for s in AssessmentStatus}
        assert actual == expected


class TestSubmissionStatus:
    """Tests for SubmissionStatus enumeration."""

    def test_all_submission_statuses_defined(self):
        """All submission statuses should be defined."""
        expected = {
            'not_started', 'in_progress', 'submitted', 'under_review',
            'needs_revision', 'revised', 'graded', 'approved', 'rejected'
        }
        actual = {s.value for s in SubmissionStatus}
        assert actual == expected


class TestProficiencyLevel:
    """Tests for ProficiencyLevel enumeration and utility methods."""

    def test_all_levels_defined(self):
        """All proficiency levels should be defined."""
        expected = {
            'not_demonstrated', 'emerging', 'developing',
            'proficient', 'advanced', 'expert'
        }
        actual = {l.value for l in ProficiencyLevel}
        assert actual == expected

    def test_from_percentage_expert(self):
        """95%+ should map to expert level."""
        assert ProficiencyLevel.from_percentage(100) == ProficiencyLevel.EXPERT
        assert ProficiencyLevel.from_percentage(95) == ProficiencyLevel.EXPERT

    def test_from_percentage_advanced(self):
        """85-94% should map to advanced level."""
        assert ProficiencyLevel.from_percentage(94) == ProficiencyLevel.ADVANCED
        assert ProficiencyLevel.from_percentage(85) == ProficiencyLevel.ADVANCED

    def test_from_percentage_proficient(self):
        """70-84% should map to proficient level."""
        assert ProficiencyLevel.from_percentage(84) == ProficiencyLevel.PROFICIENT
        assert ProficiencyLevel.from_percentage(70) == ProficiencyLevel.PROFICIENT

    def test_from_percentage_developing(self):
        """50-69% should map to developing level."""
        assert ProficiencyLevel.from_percentage(69) == ProficiencyLevel.DEVELOPING
        assert ProficiencyLevel.from_percentage(50) == ProficiencyLevel.DEVELOPING

    def test_from_percentage_emerging(self):
        """25-49% should map to emerging level."""
        assert ProficiencyLevel.from_percentage(49) == ProficiencyLevel.EMERGING
        assert ProficiencyLevel.from_percentage(25) == ProficiencyLevel.EMERGING

    def test_from_percentage_not_demonstrated(self):
        """0-24% should map to not_demonstrated level."""
        assert ProficiencyLevel.from_percentage(24) == ProficiencyLevel.NOT_DEMONSTRATED
        assert ProficiencyLevel.from_percentage(0) == ProficiencyLevel.NOT_DEMONSTRATED

    def test_to_percentage_range_returns_tuple(self):
        """to_percentage_range should return (min, max) tuple."""
        result = ProficiencyLevel.PROFICIENT.to_percentage_range()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] < result[1]


class TestReviewType:
    """Tests for ReviewType enumeration."""

    def test_all_review_types_defined(self):
        """All review types should be defined."""
        expected = {'single_blind', 'double_blind', 'open', 'collaborative'}
        actual = {r.value for r in ReviewType}
        assert actual == expected


# ============================================================================
# RUBRIC PERFORMANCE LEVEL TESTS
# ============================================================================

class TestRubricPerformanceLevel:
    """Tests for RubricPerformanceLevel entity."""

    def test_valid_creation(self):
        """Should create valid performance level with required fields."""
        level = RubricPerformanceLevel(
            level=ProficiencyLevel.PROFICIENT,
            name="Proficient",
            description="Meets expectations",
            points=Decimal("80")
        )
        assert level.level == ProficiencyLevel.PROFICIENT
        assert level.name == "Proficient"
        assert level.points == Decimal("80")
        assert level.id is not None

    def test_auto_generates_id(self):
        """Should auto-generate UUID if not provided."""
        level = RubricPerformanceLevel(
            level=ProficiencyLevel.PROFICIENT,
            name="Test",
            description="Test",
            points=Decimal("10")
        )
        assert isinstance(level.id, UUID)

    def test_validates_name_required(self):
        """Should raise error for empty name."""
        with pytest.raises(RubricValidationError, match="name is required"):
            RubricPerformanceLevel(
                level=ProficiencyLevel.PROFICIENT,
                name="",
                description="Test",
                points=Decimal("10")
            )

    def test_validates_description_required(self):
        """Should raise error for empty description."""
        with pytest.raises(RubricValidationError, match="description is required"):
            RubricPerformanceLevel(
                level=ProficiencyLevel.PROFICIENT,
                name="Test",
                description="",
                points=Decimal("10")
            )

    def test_validates_points_not_negative(self):
        """Should raise error for negative points."""
        with pytest.raises(RubricValidationError, match="cannot be negative"):
            RubricPerformanceLevel(
                level=ProficiencyLevel.PROFICIENT,
                name="Test",
                description="Test",
                points=Decimal("-10")
            )

    def test_validates_color_format(self):
        """Should raise error for invalid color format."""
        with pytest.raises(RubricValidationError, match="hex color code"):
            RubricPerformanceLevel(
                level=ProficiencyLevel.PROFICIENT,
                name="Test",
                description="Test",
                points=Decimal("10"),
                color="red"  # Should be #FF0000
            )

    def test_valid_color_accepted(self):
        """Should accept valid hex color code."""
        level = RubricPerformanceLevel(
            level=ProficiencyLevel.PROFICIENT,
            name="Test",
            description="Test",
            points=Decimal("10"),
            color="#FF0000"
        )
        assert level.color == "#FF0000"

    def test_to_dict_returns_all_fields(self):
        """to_dict should return all fields."""
        level = RubricPerformanceLevel(
            level=ProficiencyLevel.EXPERT,
            name="Expert",
            description="Exceeds expectations",
            points=Decimal("100"),
            color="#00FF00"
        )
        data = level.to_dict()
        assert data['level'] == 'expert'
        assert data['name'] == 'Expert'
        assert data['points'] == 100.0


# ============================================================================
# RUBRIC CRITERION TESTS
# ============================================================================

class TestRubricCriterion:
    """Tests for RubricCriterion entity."""

    def test_valid_creation(self):
        """Should create valid criterion with required fields."""
        criterion = RubricCriterion(
            name="Code Quality",
            description="Evaluate code cleanliness and readability",
            max_points=Decimal("30")
        )
        assert criterion.name == "Code Quality"
        assert criterion.max_points == Decimal("30")
        assert criterion.weight == Decimal("1.0")
        assert criterion.is_required is True

    def test_validates_name_required(self):
        """Should raise error for empty name."""
        with pytest.raises(RubricValidationError, match="name is required"):
            RubricCriterion(
                name="",
                description="Test",
                max_points=Decimal("10")
            )

    def test_validates_max_points_positive(self):
        """Should raise error for non-positive max points."""
        with pytest.raises(RubricValidationError, match="must be positive"):
            RubricCriterion(
                name="Test",
                description="Test",
                max_points=Decimal("0")
            )

    def test_validates_weight_positive(self):
        """Should raise error for non-positive weight."""
        with pytest.raises(RubricValidationError, match="must be positive"):
            RubricCriterion(
                name="Test",
                description="Test",
                max_points=Decimal("10"),
                weight=Decimal("0")
            )

    def test_add_performance_level(self):
        """Should add performance levels to criterion."""
        criterion = RubricCriterion(
            name="Test",
            description="Test",
            max_points=Decimal("10")
        )
        level = RubricPerformanceLevel(
            level=ProficiencyLevel.PROFICIENT,
            name="Proficient",
            description="Meets standard",
            points=Decimal("7")
        )
        criterion.add_performance_level(level)
        assert len(criterion.performance_levels) == 1
        assert level.criterion_id == criterion.id

    def test_add_duplicate_level_raises_error(self):
        """Should raise error when adding duplicate proficiency level."""
        criterion = RubricCriterion(
            name="Test",
            description="Test",
            max_points=Decimal("10")
        )
        level1 = RubricPerformanceLevel(
            level=ProficiencyLevel.PROFICIENT,
            name="Proficient",
            description="Standard",
            points=Decimal("7")
        )
        level2 = RubricPerformanceLevel(
            level=ProficiencyLevel.PROFICIENT,
            name="Also Proficient",
            description="Duplicate",
            points=Decimal("8")
        )
        criterion.add_performance_level(level1)
        with pytest.raises(RubricValidationError, match="already exists"):
            criterion.add_performance_level(level2)

    def test_calculate_weighted_score(self):
        """Should calculate weighted score correctly."""
        criterion = RubricCriterion(
            name="Test",
            description="Test",
            max_points=Decimal("10"),
            weight=Decimal("2.0")
        )
        weighted = criterion.calculate_weighted_score(Decimal("8"))
        assert weighted == Decimal("16")


# ============================================================================
# ASSESSMENT RUBRIC TESTS
# ============================================================================

class TestAssessmentRubric:
    """Tests for AssessmentRubric entity."""

    def test_valid_creation(self):
        """Should create valid rubric with required fields."""
        rubric = AssessmentRubric(
            name="Code Review Rubric",
            max_score=Decimal("100"),
            created_by=uuid4()
        )
        assert rubric.name == "Code Review Rubric"
        assert rubric.max_score == Decimal("100")
        assert rubric.passing_percentage == Decimal("70")
        assert rubric.id is not None

    def test_auto_calculates_passing_score(self):
        """Should auto-calculate passing score from percentage."""
        rubric = AssessmentRubric(
            name="Test",
            max_score=Decimal("100"),
            created_by=uuid4(),
            passing_percentage=Decimal("80")
        )
        assert rubric.passing_score == Decimal("80")

    def test_validates_name_required(self):
        """Should raise error for empty name."""
        with pytest.raises(RubricValidationError, match="name is required"):
            AssessmentRubric(
                name="",
                max_score=Decimal("100"),
                created_by=uuid4()
            )

    def test_validates_max_score_positive(self):
        """Should raise error for non-positive max score."""
        with pytest.raises(RubricValidationError, match="must be positive"):
            AssessmentRubric(
                name="Test",
                max_score=Decimal("0"),
                created_by=uuid4()
            )

    def test_validates_passing_score_not_exceed_max(self):
        """Should raise error if passing score exceeds max."""
        with pytest.raises(RubricValidationError, match="cannot exceed"):
            AssessmentRubric(
                name="Test",
                max_score=Decimal("100"),
                created_by=uuid4(),
                passing_score=Decimal("110")
            )

    def test_add_criterion(self):
        """Should add criteria to rubric."""
        rubric = AssessmentRubric(
            name="Test",
            max_score=Decimal("100"),
            created_by=uuid4()
        )
        criterion = RubricCriterion(
            name="Quality",
            description="Test quality",
            max_points=Decimal("30")
        )
        rubric.add_criterion(criterion)
        assert len(rubric.criteria) == 1
        assert criterion.rubric_id == rubric.id

    def test_remove_criterion(self):
        """Should remove criterion by ID."""
        rubric = AssessmentRubric(
            name="Test",
            max_score=Decimal("100"),
            created_by=uuid4()
        )
        criterion = RubricCriterion(
            name="Quality",
            description="Test quality",
            max_points=Decimal("30")
        )
        rubric.add_criterion(criterion)
        assert rubric.remove_criterion(criterion.id) is True
        assert len(rubric.criteria) == 0

    def test_remove_nonexistent_criterion_returns_false(self):
        """Should return False when removing non-existent criterion."""
        rubric = AssessmentRubric(
            name="Test",
            max_score=Decimal("100"),
            created_by=uuid4()
        )
        assert rubric.remove_criterion(uuid4()) is False

    def test_calculate_total_weight(self):
        """Should calculate sum of criterion weights."""
        rubric = AssessmentRubric(
            name="Test",
            max_score=Decimal("100"),
            created_by=uuid4()
        )
        rubric.add_criterion(RubricCriterion(
            name="C1",
            description="Test",
            max_points=Decimal("30"),
            weight=Decimal("2.0")
        ))
        rubric.add_criterion(RubricCriterion(
            name="C2",
            description="Test",
            max_points=Decimal("20"),
            weight=Decimal("1.5")
        ))
        assert rubric.calculate_total_weight() == Decimal("3.5")

    def test_calculate_score_with_weighted_criteria(self):
        """Should calculate score correctly with weighted criteria."""
        rubric = AssessmentRubric(
            name="Test",
            max_score=Decimal("100"),
            created_by=uuid4(),
            passing_score=Decimal("70")
        )
        c1 = RubricCriterion(
            name="C1",
            description="Test",
            max_points=Decimal("50"),
            weight=Decimal("2.0")
        )
        c2 = RubricCriterion(
            name="C2",
            description="Test",
            max_points=Decimal("50"),
            weight=Decimal("1.0")
        )
        rubric.add_criterion(c1)
        rubric.add_criterion(c2)

        scores = {c1.id: Decimal("40"), c2.id: Decimal("45")}
        result = rubric.calculate_score(scores)

        # Total: 40 + 45 = 85
        # Weighted: (40 * 2) + (45 * 1) = 80 + 45 = 125
        # Max weighted: (50 * 2) + (50 * 1) = 150
        # Percentage: 125 / 150 * 100 = 83.33%
        assert result['total_points'] == 85.0
        assert result['weighted_score'] == 125.0
        assert result['passed'] is True

    def test_calculate_score_missing_required_criterion(self):
        """Should raise error if required criterion is missing."""
        rubric = AssessmentRubric(
            name="Test",
            max_score=Decimal("100"),
            created_by=uuid4()
        )
        criterion = RubricCriterion(
            name="Required",
            description="Test",
            max_points=Decimal("50"),
            is_required=True
        )
        rubric.add_criterion(criterion)

        with pytest.raises(RubricValidationError, match="Missing scores"):
            rubric.calculate_score({})

    def test_create_template_copy(self):
        """Should create a copy of template rubric."""
        template = AssessmentRubric(
            name="Template",
            max_score=Decimal("100"),
            created_by=uuid4(),
            is_template=True
        )
        template.add_criterion(RubricCriterion(
            name="Quality",
            description="Test",
            max_points=Decimal("30")
        ))

        copy_creator = uuid4()
        copy = template.create_template_copy(copy_creator)

        assert copy.id != template.id
        assert copy.name == "Template (Copy)"
        assert copy.is_template is False
        assert copy.created_by == copy_creator
        assert len(copy.criteria) == 1
        assert copy.criteria[0].id != template.criteria[0].id


# ============================================================================
# COMPETENCY TESTS
# ============================================================================

class TestCompetency:
    """Tests for Competency entity."""

    def test_valid_creation(self):
        """Should create valid competency with required fields."""
        competency = Competency(
            code="PROG-001",
            name="Python Fundamentals"
        )
        assert competency.code == "PROG-001"
        assert competency.name == "Python Fundamentals"
        assert competency.required_proficiency == ProficiencyLevel.PROFICIENT
        assert competency.level == 1

    def test_validates_code_required(self):
        """Should raise error for empty code."""
        with pytest.raises(CompetencyError, match="code is required"):
            Competency(code="", name="Test")

    def test_validates_name_required(self):
        """Should raise error for empty name."""
        with pytest.raises(CompetencyError, match="name is required"):
            Competency(code="TEST-001", name="")

    def test_validates_level_minimum(self):
        """Should raise error for level less than 1."""
        with pytest.raises(CompetencyError, match="at least 1"):
            Competency(code="TEST", name="Test", level=0)

    def test_is_child_of(self):
        """Should correctly identify parent relationship."""
        parent_id = uuid4()
        child = Competency(
            code="CHILD",
            name="Child",
            parent_id=parent_id
        )
        assert child.is_child_of(parent_id) is True
        assert child.is_child_of(uuid4()) is False


class TestCompetencyProgress:
    """Tests for CompetencyProgress entity."""

    def test_valid_creation(self):
        """Should create valid progress tracking."""
        progress = CompetencyProgress(
            student_id=uuid4(),
            competency_id=uuid4()
        )
        assert progress.current_level == ProficiencyLevel.NOT_DEMONSTRATED
        assert progress.evidence_submissions == []

    def test_update_level_increases_level(self):
        """Should update level when higher level achieved."""
        progress = CompetencyProgress(
            student_id=uuid4(),
            competency_id=uuid4()
        )
        submission_id = uuid4()
        result = progress.update_level(ProficiencyLevel.PROFICIENT, submission_id)

        assert result is True
        assert progress.current_level == ProficiencyLevel.PROFICIENT
        assert progress.previous_level == ProficiencyLevel.NOT_DEMONSTRATED
        assert submission_id in progress.evidence_submissions
        assert progress.first_demonstrated_at is not None

    def test_update_level_no_regression(self):
        """Should not decrease level (no regression)."""
        progress = CompetencyProgress(
            student_id=uuid4(),
            competency_id=uuid4(),
            current_level=ProficiencyLevel.PROFICIENT
        )
        result = progress.update_level(ProficiencyLevel.DEVELOPING)

        assert result is False
        assert progress.current_level == ProficiencyLevel.PROFICIENT

    def test_verify_records_verification(self):
        """Should record verification details."""
        progress = CompetencyProgress(
            student_id=uuid4(),
            competency_id=uuid4(),
            current_level=ProficiencyLevel.PROFICIENT
        )
        verifier_id = uuid4()
        progress.verify(verifier_id, "Excellent work")

        assert progress.verified_by == verifier_id
        assert progress.verified_at is not None
        assert progress.assessor_notes == "Excellent work"

    def test_meets_requirement(self):
        """Should correctly check if requirement is met."""
        progress = CompetencyProgress(
            student_id=uuid4(),
            competency_id=uuid4(),
            current_level=ProficiencyLevel.PROFICIENT
        )

        assert progress.meets_requirement(ProficiencyLevel.PROFICIENT) is True
        assert progress.meets_requirement(ProficiencyLevel.DEVELOPING) is True
        assert progress.meets_requirement(ProficiencyLevel.ADVANCED) is False


# ============================================================================
# PROJECT MILESTONE TESTS
# ============================================================================

class TestProjectMilestone:
    """Tests for ProjectMilestone entity."""

    def test_valid_creation(self):
        """Should create valid milestone."""
        milestone = ProjectMilestone(
            name="Design Document",
            assessment_id=uuid4(),
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        assert milestone.name == "Design Document"
        assert milestone.weight == Decimal("1.0")

    def test_validates_name_required(self):
        """Should raise error for empty name."""
        with pytest.raises(ProjectError, match="name is required"):
            ProjectMilestone(name="", assessment_id=uuid4())

    def test_validates_weight_positive(self):
        """Should raise error for non-positive weight."""
        with pytest.raises(ProjectError, match="must be positive"):
            ProjectMilestone(
                name="Test",
                assessment_id=uuid4(),
                weight=Decimal("0")
            )

    def test_is_overdue_before_due_date(self):
        """Should not be overdue before due date."""
        milestone = ProjectMilestone(
            name="Test",
            assessment_id=uuid4(),
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        assert milestone.is_overdue() is False

    def test_is_overdue_after_due_date(self):
        """Should be overdue after due date."""
        milestone = ProjectMilestone(
            name="Test",
            assessment_id=uuid4(),
            due_date=datetime.utcnow() - timedelta(days=1)
        )
        assert milestone.is_overdue() is True

    def test_is_overdue_no_due_date(self):
        """Should not be overdue if no due date set."""
        milestone = ProjectMilestone(
            name="Test",
            assessment_id=uuid4()
        )
        assert milestone.is_overdue() is False

    def test_days_until_due(self):
        """Should calculate days until due correctly."""
        milestone = ProjectMilestone(
            name="Test",
            assessment_id=uuid4(),
            due_date=datetime.utcnow() + timedelta(days=5)
        )
        days = milestone.days_until_due()
        assert 4 <= days <= 5  # Allow for timing variations


# ============================================================================
# PORTFOLIO ARTIFACT TESTS
# ============================================================================

class TestPortfolioArtifact:
    """Tests for PortfolioArtifact entity."""

    def test_valid_creation_with_url(self):
        """Should create valid artifact with URL content."""
        artifact = PortfolioArtifact(
            title="Project Report",
            submission_id=uuid4(),
            student_id=uuid4(),
            artifact_type="document",
            content_url="https://example.com/report.pdf"
        )
        assert artifact.title == "Project Report"
        assert artifact.artifact_type == "document"

    def test_valid_creation_with_text(self):
        """Should create valid artifact with text content."""
        artifact = PortfolioArtifact(
            title="Code Sample",
            submission_id=uuid4(),
            student_id=uuid4(),
            artifact_type="code",
            content_text="def hello(): print('Hello')"
        )
        assert artifact.content_text is not None

    def test_validates_title_required(self):
        """Should raise error for empty title."""
        with pytest.raises(PortfolioError, match="title is required"):
            PortfolioArtifact(
                title="",
                submission_id=uuid4(),
                student_id=uuid4(),
                artifact_type="document",
                content_url="https://test.com"
            )

    def test_validates_artifact_type_required(self):
        """Should raise error for empty artifact type."""
        with pytest.raises(PortfolioError, match="type is required"):
            PortfolioArtifact(
                title="Test",
                submission_id=uuid4(),
                student_id=uuid4(),
                artifact_type="",
                content_url="https://test.com"
            )

    def test_validates_content_required(self):
        """Should raise error if no content provided."""
        with pytest.raises(PortfolioError, match="must have content"):
            PortfolioArtifact(
                title="Test",
                submission_id=uuid4(),
                student_id=uuid4(),
                artifact_type="document"
                # No content_url, content_text, or attachments
            )

    def test_add_reflection(self):
        """Should add student reflection."""
        artifact = PortfolioArtifact(
            title="Test",
            submission_id=uuid4(),
            student_id=uuid4(),
            artifact_type="document",
            content_url="https://test.com"
        )
        artifact.add_reflection(
            "This artifact demonstrates my learning in...",
            "I learned to apply design patterns"
        )
        assert artifact.student_reflection is not None
        assert artifact.learning_demonstrated is not None

    def test_add_reflection_validates_not_empty(self):
        """Should raise error for empty reflection."""
        artifact = PortfolioArtifact(
            title="Test",
            submission_id=uuid4(),
            student_id=uuid4(),
            artifact_type="document",
            content_url="https://test.com"
        )
        with pytest.raises(PortfolioError, match="cannot be empty"):
            artifact.add_reflection("")

    def test_evaluate_artifact(self):
        """Should record evaluation."""
        artifact = PortfolioArtifact(
            title="Test",
            submission_id=uuid4(),
            student_id=uuid4(),
            artifact_type="document",
            content_url="https://test.com"
        )
        evaluator_id = uuid4()
        artifact.evaluate(Decimal("85"), "Good work!", evaluator_id)

        assert artifact.score == Decimal("85")
        assert artifact.feedback == "Good work!"
        assert artifact.evaluated_by == evaluator_id
        assert artifact.evaluated_at is not None

    def test_evaluate_validates_score_not_negative(self):
        """Should raise error for negative score."""
        artifact = PortfolioArtifact(
            title="Test",
            submission_id=uuid4(),
            student_id=uuid4(),
            artifact_type="document",
            content_url="https://test.com"
        )
        with pytest.raises(PortfolioError, match="cannot be negative"):
            artifact.evaluate(Decimal("-10"), "Bad", uuid4())


# ============================================================================
# PEER REVIEW ASSIGNMENT TESTS
# ============================================================================

class TestPeerReviewAssignment:
    """Tests for PeerReviewAssignment entity."""

    def test_valid_creation(self):
        """Should create valid assignment."""
        assignment = PeerReviewAssignment(
            submission_id=uuid4(),
            reviewer_id=uuid4()
        )
        assert assignment.status == SubmissionStatus.NOT_STARTED
        assert assignment.is_anonymous is True

    def test_start_review(self):
        """Should start review and update status."""
        assignment = PeerReviewAssignment(
            submission_id=uuid4(),
            reviewer_id=uuid4()
        )
        assignment.start_review()

        assert assignment.status == SubmissionStatus.IN_PROGRESS
        assert assignment.started_at is not None

    def test_start_review_already_started_raises_error(self):
        """Should raise error if review already started."""
        assignment = PeerReviewAssignment(
            submission_id=uuid4(),
            reviewer_id=uuid4(),
            status=SubmissionStatus.IN_PROGRESS
        )
        with pytest.raises(PeerReviewError, match="already been started"):
            assignment.start_review()

    def test_complete_review(self):
        """Should complete review and update status."""
        assignment = PeerReviewAssignment(
            submission_id=uuid4(),
            reviewer_id=uuid4(),
            status=SubmissionStatus.IN_PROGRESS
        )
        assignment.complete_review()

        assert assignment.status == SubmissionStatus.GRADED
        assert assignment.completed_at is not None

    def test_is_overdue(self):
        """Should detect overdue reviews."""
        assignment = PeerReviewAssignment(
            submission_id=uuid4(),
            reviewer_id=uuid4(),
            due_date=datetime.utcnow() - timedelta(days=1)
        )
        assert assignment.is_overdue() is True


# ============================================================================
# PEER REVIEW TESTS
# ============================================================================

class TestPeerReview:
    """Tests for PeerReview entity."""

    def test_valid_creation(self):
        """Should create valid peer review."""
        review = PeerReview(
            assignment_id=uuid4(),
            submission_id=uuid4(),
            reviewer_id=uuid4()
        )
        assert review.submitted_at is None

    def test_submit_review(self):
        """Should submit review with required feedback."""
        review = PeerReview(
            assignment_id=uuid4(),
            submission_id=uuid4(),
            reviewer_id=uuid4(),
            overall_feedback="Good work!"
        )
        review.submit()

        assert review.submitted_at is not None

    def test_submit_without_feedback_raises_error(self):
        """Should raise error if no feedback provided."""
        review = PeerReview(
            assignment_id=uuid4(),
            submission_id=uuid4(),
            reviewer_id=uuid4()
        )
        with pytest.raises(PeerReviewError, match="feedback is required"):
            review.submit()

    def test_submit_twice_raises_error(self):
        """Should raise error if already submitted."""
        review = PeerReview(
            assignment_id=uuid4(),
            submission_id=uuid4(),
            reviewer_id=uuid4(),
            overall_feedback="Good!",
            submitted_at=datetime.utcnow()
        )
        with pytest.raises(PeerReviewError, match="already been submitted"):
            review.submit()

    def test_rate_helpfulness(self):
        """Should record helpfulness rating."""
        review = PeerReview(
            assignment_id=uuid4(),
            submission_id=uuid4(),
            reviewer_id=uuid4()
        )
        review.rate_helpfulness(4, "Very helpful feedback")

        assert review.helpfulness_rating == 4
        assert review.helpfulness_feedback == "Very helpful feedback"

    def test_rate_helpfulness_invalid_rating_raises_error(self):
        """Should raise error for invalid rating."""
        review = PeerReview(
            assignment_id=uuid4(),
            submission_id=uuid4(),
            reviewer_id=uuid4()
        )
        with pytest.raises(PeerReviewError, match="between 1 and 5"):
            review.rate_helpfulness(6)

    def test_set_instructor_quality_score(self):
        """Should set instructor quality score."""
        review = PeerReview(
            assignment_id=uuid4(),
            submission_id=uuid4(),
            reviewer_id=uuid4()
        )
        review.set_instructor_quality_score(Decimal("85"))

        assert review.instructor_quality_score == Decimal("85")

    def test_set_instructor_quality_score_invalid_raises_error(self):
        """Should raise error for invalid quality score."""
        review = PeerReview(
            assignment_id=uuid4(),
            submission_id=uuid4(),
            reviewer_id=uuid4()
        )
        with pytest.raises(PeerReviewError, match="between 0 and 100"):
            review.set_instructor_quality_score(Decimal("150"))


# ============================================================================
# ADVANCED ASSESSMENT TESTS
# ============================================================================

class TestAdvancedAssessment:
    """Tests for AdvancedAssessment entity."""

    def test_valid_creation_performance(self):
        """Should create valid performance assessment."""
        assessment = AdvancedAssessment(
            title="Lab Demonstration",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE
        )
        assert assessment.title == "Lab Demonstration"
        assert assessment.assessment_type == AssessmentType.PERFORMANCE
        assert assessment.status == AssessmentStatus.DRAFT

    def test_valid_creation_peer_review(self):
        """Should create valid peer review assessment."""
        assessment = AdvancedAssessment(
            title="Code Review",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PEER_REVIEW,
            peer_review_enabled=True,
            peer_review_type=ReviewType.DOUBLE_BLIND
        )
        assert assessment.peer_review_enabled is True

    def test_validates_title_required(self):
        """Should raise error for empty title."""
        with pytest.raises(AssessmentValidationError, match="title is required"):
            AdvancedAssessment(
                title="",
                course_id=uuid4(),
                created_by=uuid4(),
                assessment_type=AssessmentType.PERFORMANCE
            )

    def test_validates_max_score_positive(self):
        """Should raise error for non-positive max score."""
        with pytest.raises(AssessmentValidationError, match="must be positive"):
            AdvancedAssessment(
                title="Test",
                course_id=uuid4(),
                created_by=uuid4(),
                assessment_type=AssessmentType.PERFORMANCE,
                max_score=Decimal("0")
            )

    def test_validates_passing_score_not_exceed_max(self):
        """Should raise error if passing exceeds max."""
        with pytest.raises(AssessmentValidationError, match="cannot exceed"):
            AdvancedAssessment(
                title="Test",
                course_id=uuid4(),
                created_by=uuid4(),
                assessment_type=AssessmentType.PERFORMANCE,
                max_score=Decimal("100"),
                passing_score=Decimal("110")
            )

    def test_validates_available_dates_order(self):
        """Should raise error if available_until before available_from."""
        with pytest.raises(AssessmentValidationError, match="must be after"):
            AdvancedAssessment(
                title="Test",
                course_id=uuid4(),
                created_by=uuid4(),
                assessment_type=AssessmentType.PERFORMANCE,
                available_from=datetime.utcnow() + timedelta(days=7),
                available_until=datetime.utcnow()
            )

    def test_validates_peer_review_enabled_for_peer_type(self):
        """Should raise error if peer review not enabled for peer_review type."""
        with pytest.raises(AssessmentValidationError, match="must be enabled"):
            AdvancedAssessment(
                title="Test",
                course_id=uuid4(),
                created_by=uuid4(),
                assessment_type=AssessmentType.PEER_REVIEW,
                peer_review_enabled=False
            )

    def test_publish_assessment(self):
        """Should publish draft assessment."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE
        )
        assessment.publish()

        assert assessment.status == AssessmentStatus.PUBLISHED
        assert assessment.published_at is not None

    def test_publish_non_draft_raises_error(self):
        """Should raise error when publishing non-draft."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE,
            status=AssessmentStatus.PUBLISHED
        )
        with pytest.raises(AssessmentValidationError, match="Cannot publish"):
            assessment.publish()

    def test_archive_assessment(self):
        """Should archive assessment."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE
        )
        assessment.archive()

        assert assessment.status == AssessmentStatus.ARCHIVED

    def test_is_available_draft(self):
        """Draft assessment should not be available."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE
        )
        assert assessment.is_available() is False

    def test_is_available_published(self):
        """Published assessment should be available."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE,
            status=AssessmentStatus.PUBLISHED
        )
        assert assessment.is_available() is True

    def test_is_available_respects_dates(self):
        """Should respect availability window."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE,
            status=AssessmentStatus.PUBLISHED,
            available_from=datetime.utcnow() + timedelta(days=7)
        )
        assert assessment.is_available() is False

    def test_is_past_due(self):
        """Should detect past due assessments."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE,
            due_date=datetime.utcnow() - timedelta(days=1)
        )
        assert assessment.is_past_due() is True

    def test_calculate_late_penalty_before_due(self):
        """Should return 0 penalty for on-time submission."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE,
            due_date=datetime.utcnow() + timedelta(days=7),
            late_penalty_percentage=Decimal("10")
        )
        penalty = assessment.calculate_late_penalty(datetime.utcnow())
        assert penalty == Decimal("0")

    def test_calculate_late_penalty_after_due(self):
        """Should return configured penalty for late submission."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE,
            due_date=datetime.utcnow() - timedelta(days=1),
            late_submission_allowed=True,
            late_penalty_percentage=Decimal("15")
        )
        penalty = assessment.calculate_late_penalty(datetime.utcnow())
        assert penalty == Decimal("15")

    def test_calculate_late_penalty_not_allowed(self):
        """Should return 100% penalty if late submissions not allowed."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE,
            due_date=datetime.utcnow() - timedelta(days=1),
            late_submission_allowed=False
        )
        penalty = assessment.calculate_late_penalty(datetime.utcnow())
        assert penalty == Decimal("100")

    def test_add_milestone(self):
        """Should add milestone to project assessment."""
        assessment = AdvancedAssessment(
            title="Capstone",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PROJECT
        )
        milestone = ProjectMilestone(
            name="Design Phase",
            assessment_id=assessment.id
        )
        assessment.add_milestone(milestone)

        assert len(assessment.milestones) == 1

    def test_add_milestone_wrong_type_raises_error(self):
        """Should raise error when adding milestone to non-project type."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PERFORMANCE
        )
        milestone = ProjectMilestone(
            name="Test",
            assessment_id=assessment.id
        )
        with pytest.raises(AssessmentValidationError, match="only be added to project"):
            assessment.add_milestone(milestone)

    def test_add_competency(self):
        """Should map competency to assessment."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.COMPETENCY
        )
        comp_id = uuid4()
        assessment.add_competency(comp_id)

        assert comp_id in assessment.competencies

    def test_add_competency_no_duplicates(self):
        """Should not add duplicate competencies."""
        assessment = AdvancedAssessment(
            title="Test",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.COMPETENCY
        )
        comp_id = uuid4()
        assessment.add_competency(comp_id)
        assessment.add_competency(comp_id)

        assert assessment.competencies.count(comp_id) == 1


# ============================================================================
# ASSESSMENT SUBMISSION TESTS
# ============================================================================

class TestAssessmentSubmission:
    """Tests for AssessmentSubmission entity."""

    def test_valid_creation(self):
        """Should create valid submission."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4()
        )
        assert submission.status == SubmissionStatus.NOT_STARTED
        assert submission.attempt_number == 1

    def test_start_submission(self):
        """Should start submission and record time."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4()
        )
        submission.start()

        assert submission.status == SubmissionStatus.IN_PROGRESS
        assert submission.started_at is not None

    def test_start_already_started_raises_error(self):
        """Should raise error if already started."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4(),
            status=SubmissionStatus.IN_PROGRESS
        )
        with pytest.raises(SubmissionError, match="already been started"):
            submission.start()

    def test_submit_from_in_progress(self):
        """Should submit from in_progress status."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4(),
            status=SubmissionStatus.IN_PROGRESS,
            started_at=datetime.utcnow() - timedelta(hours=1)
        )
        submission.submit()

        assert submission.status == SubmissionStatus.SUBMITTED
        assert submission.submitted_at is not None
        assert submission.time_spent_minutes >= 60

    def test_submit_calculates_lateness(self):
        """Should calculate lateness on submit."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4(),
            status=SubmissionStatus.IN_PROGRESS
        )
        due_date = datetime.utcnow() - timedelta(days=2)
        submission.submit(due_date)

        assert submission.is_late is True
        assert submission.late_days >= 2

    def test_submit_from_wrong_status_raises_error(self):
        """Should raise error when submitting from invalid status."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4(),
            status=SubmissionStatus.NOT_STARTED
        )
        with pytest.raises(SubmissionError, match="Cannot submit"):
            submission.submit()

    def test_request_revision(self):
        """Should request revision with feedback."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4(),
            status=SubmissionStatus.SUBMITTED
        )
        submission.request_revision("Please improve the code quality")

        assert submission.status == SubmissionStatus.NEEDS_REVISION
        assert submission.instructor_feedback == "Please improve the code quality"

    def test_submit_revision(self):
        """Should submit revision."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4(),
            status=SubmissionStatus.NEEDS_REVISION
        )
        submission.submit_revision()

        assert submission.status == SubmissionStatus.REVISED

    def test_grade_submission(self):
        """Should grade submission with scores."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4(),
            status=SubmissionStatus.SUBMITTED
        )
        grader_id = uuid4()
        submission.grade(
            raw_score=Decimal("85"),
            max_score=Decimal("100"),
            passing_score=Decimal("70"),
            grader_id=grader_id,
            feedback="Good work!"
        )

        assert submission.raw_score == Decimal("85")
        assert submission.final_score == Decimal("85")
        assert submission.percentage == Decimal("85")
        assert submission.passed is True
        assert submission.status == SubmissionStatus.GRADED

    def test_grade_with_late_penalty(self):
        """Should apply late penalty to score."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4(),
            status=SubmissionStatus.SUBMITTED,
            is_late=True
        )
        submission.grade(
            raw_score=Decimal("100"),
            max_score=Decimal("100"),
            passing_score=Decimal("70"),
            grader_id=uuid4(),
            late_penalty=Decimal("10")
        )

        assert submission.raw_score == Decimal("100")
        assert submission.adjusted_score == Decimal("90")
        assert submission.final_score == Decimal("90")

    def test_add_artifact_to_portfolio(self):
        """Should add artifact to portfolio submission."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4()
        )
        artifact = PortfolioArtifact(
            title="Code Sample",
            submission_id=submission.id,
            student_id=submission.student_id,
            artifact_type="code",
            content_text="print('hello')"
        )
        submission.add_artifact(artifact)

        assert len(submission.portfolio_artifacts) == 1
        assert artifact.submission_id == submission.id

    def test_update_milestone_progress(self):
        """Should update milestone progress."""
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4()
        )
        milestone_id = uuid4()
        submission.update_milestone_progress(
            milestone_id,
            "completed",
            "All deliverables submitted"
        )

        progress = submission.milestone_progress[str(milestone_id)]
        assert progress['status'] == 'completed'
        assert progress['notes'] == 'All deliverables submitted'


# ============================================================================
# RUBRIC EVALUATION TESTS
# ============================================================================

class TestRubricEvaluation:
    """Tests for RubricEvaluation entity."""

    def test_valid_creation(self):
        """Should create valid evaluation."""
        evaluation = RubricEvaluation(
            submission_id=uuid4(),
            criterion_id=uuid4(),
            evaluated_by=uuid4()
        )
        assert evaluation.id is not None

    def test_update_score(self):
        """Should update score with level and points."""
        evaluation = RubricEvaluation(
            submission_id=uuid4(),
            criterion_id=uuid4(),
            evaluated_by=uuid4()
        )
        evaluation.update_score(
            level=ProficiencyLevel.PROFICIENT,
            points=Decimal("25"),
            feedback="Good understanding demonstrated"
        )

        assert evaluation.proficiency_level == ProficiencyLevel.PROFICIENT
        assert evaluation.points_awarded == Decimal("25")
        assert evaluation.feedback == "Good understanding demonstrated"

    def test_update_score_negative_raises_error(self):
        """Should raise error for negative points."""
        evaluation = RubricEvaluation(
            submission_id=uuid4(),
            criterion_id=uuid4(),
            evaluated_by=uuid4()
        )
        with pytest.raises(RubricValidationError, match="cannot be negative"):
            evaluation.update_score(
                level=ProficiencyLevel.PROFICIENT,
                points=Decimal("-5")
            )


# ============================================================================
# ASSESSMENT ANALYTICS TESTS
# ============================================================================

class TestAssessmentAnalytics:
    """Tests for AssessmentAnalytics entity."""

    def test_valid_creation(self):
        """Should create valid analytics."""
        analytics = AssessmentAnalytics(
            assessment_id=uuid4()
        )
        assert analytics.total_students == 0
        assert analytics.pass_count == 0

    def test_calculate_pass_rate(self):
        """Should calculate pass rate correctly."""
        analytics = AssessmentAnalytics(
            assessment_id=uuid4(),
            pass_count=75,
            fail_count=25
        )
        analytics.calculate_pass_rate()

        assert analytics.pass_rate == Decimal("75")

    def test_calculate_pass_rate_zero_total(self):
        """Should handle zero total submissions."""
        analytics = AssessmentAnalytics(
            assessment_id=uuid4(),
            pass_count=0,
            fail_count=0
        )
        analytics.calculate_pass_rate()

        assert analytics.pass_rate is None

    def test_update_timestamp(self):
        """Should update calculation timestamp."""
        analytics = AssessmentAnalytics(
            assessment_id=uuid4()
        )
        old_time = analytics.calculated_at
        analytics.update_timestamp()

        assert analytics.calculated_at >= old_time

    def test_to_dict_includes_all_metrics(self):
        """to_dict should include all analytics metrics."""
        analytics = AssessmentAnalytics(
            assessment_id=uuid4(),
            total_students=100,
            average_score=Decimal("82.5")
        )
        data = analytics.to_dict()

        assert 'total_students' in data
        assert 'average_score' in data
        assert 'pass_rate' in data
        assert 'criterion_averages' in data


# ============================================================================
# INTEGRATION WORKFLOW TESTS
# Test complete workflows across multiple entities
# ============================================================================

class TestPeerReviewWorkflow:
    """Integration tests for peer review workflow."""

    def test_complete_peer_review_workflow(self):
        """Test complete peer review from assignment to rating."""
        # Create submission
        submission_id = uuid4()
        student_id = uuid4()
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=student_id,
            status=SubmissionStatus.SUBMITTED,
            submitted_at=datetime.utcnow()
        )

        # Assign reviewer
        reviewer_id = uuid4()
        assignment = PeerReviewAssignment(
            submission_id=submission_id,
            reviewer_id=reviewer_id
        )

        # Start review
        assignment.start_review()
        assert assignment.status == SubmissionStatus.IN_PROGRESS

        # Create review
        review = PeerReview(
            assignment_id=assignment.id,
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            overall_feedback="Great work! Clear code structure.",
            strengths="Good variable naming",
            areas_for_improvement="Add more comments"
        )

        # Submit review
        review.submit()
        assignment.complete_review()

        assert review.submitted_at is not None
        assert assignment.status == SubmissionStatus.GRADED

        # Rate helpfulness
        review.rate_helpfulness(5, "Very helpful feedback!")
        assert review.helpfulness_rating == 5


class TestPortfolioWorkflow:
    """Integration tests for portfolio assessment workflow."""

    def test_complete_portfolio_workflow(self):
        """Test complete portfolio from creation to evaluation."""
        # Create portfolio submission
        submission = AssessmentSubmission(
            assessment_id=uuid4(),
            student_id=uuid4()
        )
        submission.start()

        # Add artifacts
        artifact1 = PortfolioArtifact(
            title="Final Project",
            submission_id=submission.id,
            student_id=submission.student_id,
            artifact_type="code",
            content_url="https://github.com/student/project"
        )
        artifact1.add_reflection(
            "This project demonstrates my ability to...",
            "Full-stack development skills"
        )

        artifact2 = PortfolioArtifact(
            title="Research Paper",
            submission_id=submission.id,
            student_id=submission.student_id,
            artifact_type="document",
            content_url="https://docs.example.com/paper"
        )
        artifact2.add_reflection(
            "This paper shows my research abilities..."
        )

        submission.add_artifact(artifact1)
        submission.add_artifact(artifact2)

        # Submit portfolio
        submission.submit()
        assert submission.status == SubmissionStatus.SUBMITTED
        assert len(submission.portfolio_artifacts) == 2

        # Evaluate artifacts
        evaluator_id = uuid4()
        artifact1.evaluate(Decimal("90"), "Excellent project!", evaluator_id)
        artifact2.evaluate(Decimal("85"), "Good research!", evaluator_id)

        # Grade portfolio
        submission.grade(
            raw_score=Decimal("87.5"),
            max_score=Decimal("100"),
            passing_score=Decimal("70"),
            grader_id=evaluator_id,
            feedback="Strong portfolio demonstrating growth."
        )

        assert submission.passed is True


class TestProjectMilestoneWorkflow:
    """Integration tests for project milestone workflow."""

    def test_complete_project_workflow(self):
        """Test complete project from milestones to completion."""
        # Create project assessment
        assessment = AdvancedAssessment(
            title="Capstone Project",
            course_id=uuid4(),
            created_by=uuid4(),
            assessment_type=AssessmentType.PROJECT
        )

        # Add milestones
        milestone1 = ProjectMilestone(
            name="Proposal",
            assessment_id=assessment.id,
            sort_order=1,
            due_date=datetime.utcnow() + timedelta(days=7),
            weight=Decimal("0.2")
        )
        milestone2 = ProjectMilestone(
            name="Implementation",
            assessment_id=assessment.id,
            sort_order=2,
            due_date=datetime.utcnow() + timedelta(days=30),
            weight=Decimal("0.6")
        )
        milestone3 = ProjectMilestone(
            name="Presentation",
            assessment_id=assessment.id,
            sort_order=3,
            due_date=datetime.utcnow() + timedelta(days=45),
            weight=Decimal("0.2")
        )

        assessment.add_milestone(milestone1)
        assessment.add_milestone(milestone2)
        assessment.add_milestone(milestone3)

        assert len(assessment.milestones) == 3

        # Create submission
        submission = AssessmentSubmission(
            assessment_id=assessment.id,
            student_id=uuid4()
        )
        submission.start()

        # Track milestone progress
        submission.update_milestone_progress(milestone1.id, "completed", "Approved")
        submission.update_milestone_progress(milestone2.id, "in_progress", "50% done")

        assert len(submission.milestone_progress) == 2


class TestCompetencyWorkflow:
    """Integration tests for competency tracking workflow."""

    def test_complete_competency_workflow(self):
        """Test competency demonstration and verification."""
        # Create competency
        competency = Competency(
            code="PY-101",
            name="Python Basics",
            required_proficiency=ProficiencyLevel.PROFICIENT
        )

        # Create student progress
        progress = CompetencyProgress(
            student_id=uuid4(),
            competency_id=competency.id
        )

        # Demonstrate through assessment
        submission_id = uuid4()
        progress.update_level(ProficiencyLevel.DEVELOPING, submission_id)
        assert progress.current_level == ProficiencyLevel.DEVELOPING
        assert progress.meets_requirement(competency.required_proficiency) is False

        # Improve proficiency
        submission_id_2 = uuid4()
        progress.update_level(ProficiencyLevel.PROFICIENT, submission_id_2)
        assert progress.current_level == ProficiencyLevel.PROFICIENT
        assert progress.meets_requirement(competency.required_proficiency) is True

        # Verify competency
        verifier_id = uuid4()
        progress.verify(verifier_id, "Competency verified through assessment performance")

        assert progress.verified_at is not None
        assert len(progress.evidence_submissions) == 2


class TestRubricScoring:
    """Integration tests for rubric-based scoring."""

    def test_complete_rubric_scoring_workflow(self):
        """Test complete rubric evaluation with multiple criteria."""
        # Create rubric
        rubric = AssessmentRubric(
            name="Code Review Rubric",
            max_score=Decimal("100"),
            created_by=uuid4(),
            passing_score=Decimal("70")
        )

        # Add criteria
        c1 = RubricCriterion(
            name="Functionality",
            description="Does the code work correctly?",
            max_points=Decimal("40"),
            weight=Decimal("2.0")
        )
        c2 = RubricCriterion(
            name="Code Quality",
            description="Is the code clean and maintainable?",
            max_points=Decimal("30"),
            weight=Decimal("1.5")
        )
        c3 = RubricCriterion(
            name="Documentation",
            description="Are comments and docs adequate?",
            max_points=Decimal("30"),
            weight=Decimal("1.0")
        )

        rubric.add_criterion(c1)
        rubric.add_criterion(c2)
        rubric.add_criterion(c3)

        # Create evaluations
        evaluator_id = uuid4()
        submission_id = uuid4()

        eval1 = RubricEvaluation(
            submission_id=submission_id,
            criterion_id=c1.id,
            evaluated_by=evaluator_id
        )
        eval1.update_score(ProficiencyLevel.PROFICIENT, Decimal("35"))

        eval2 = RubricEvaluation(
            submission_id=submission_id,
            criterion_id=c2.id,
            evaluated_by=evaluator_id
        )
        eval2.update_score(ProficiencyLevel.ADVANCED, Decimal("28"))

        eval3 = RubricEvaluation(
            submission_id=submission_id,
            criterion_id=c3.id,
            evaluated_by=evaluator_id
        )
        eval3.update_score(ProficiencyLevel.PROFICIENT, Decimal("25"))

        # Calculate total score
        scores = {
            c1.id: Decimal("35"),
            c2.id: Decimal("28"),
            c3.id: Decimal("25")
        }
        result = rubric.calculate_score(scores)

        assert result['total_points'] == 88.0  # 35 + 28 + 25
        assert result['passed'] is True
