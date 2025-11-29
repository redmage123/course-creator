"""
Interactive Content Domain Entities Unit Tests

WHAT: Comprehensive unit tests for interactive content domain entities
WHERE: Tests entities in content_management/domain/entities/interactive_content.py
WHY: Ensures all interactive content types work correctly with proper
     validation, state management, and business logic

Test Coverage:
- All interactive content type enums
- InteractiveElement status transitions and analytics
- Simulation validation and scoring
- DragDropActivity evaluation
- InteractiveDiagram hotspots and quiz evaluation
- CodePlayground test case evaluation
- BranchingScenario path evaluation
- InteractiveTimeline event management
- FlashcardDeck spaced repetition (SM-2 algorithm)
- InteractiveVideo session evaluation
- InteractionSession tracking
- Custom exceptions
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from content_management.domain.entities.interactive_content import (
    # Enums
    InteractiveContentType,
    InteractiveElementStatus,
    DifficultyLevel,
    InteractionEventType,
    CodeLanguage,
    # Exceptions
    InteractiveContentException,
    InvalidInteractiveStateException,
    InteractiveContentValidationException,
    InteractionLimitExceededException,
    UnsupportedLanguageException,
    BranchNotFoundException,
    HotspotNotFoundException,
    # Entities
    InteractiveElement,
    Simulation,
    DragDropItem,
    DropZone,
    DragDropActivity,
    Hotspot,
    DiagramLayer,
    InteractiveDiagram,
    CodePlayground,
    ScenarioBranch,
    BranchingScenario,
    TimelineEvent,
    InteractiveTimeline,
    Flashcard,
    FlashcardDeck,
    VideoInteraction,
    InteractiveVideo,
    InteractionSession,
)


# =============================================================================
# Enum Tests
# =============================================================================

class TestInteractiveContentTypeEnum:
    """
    WHAT: Tests for InteractiveContentType enum
    WHERE: Tests all interactive content type values
    WHY: Ensures all expected content types are available
    """

    def test_all_content_types_exist(self):
        """Test that all expected content types are defined."""
        expected_types = [
            "simulation", "drag_drop", "interactive_diagram",
            "code_playground", "branching_scenario", "interactive_timeline",
            "flashcard", "flashcard_deck", "interactive_video",
            "hotspot_image", "sorting_activity", "matching_pairs",
            "fill_in_blanks", "virtual_lab"
        ]
        actual_types = [t.value for t in InteractiveContentType]
        for expected in expected_types:
            assert expected in actual_types

    def test_content_type_count(self):
        """Test correct number of content types."""
        assert len(InteractiveContentType) == 14


class TestInteractiveElementStatusEnum:
    """
    WHAT: Tests for InteractiveElementStatus enum
    WHERE: Tests all element status values
    WHY: Ensures proper lifecycle status values
    """

    def test_all_statuses_exist(self):
        """Test all lifecycle statuses."""
        expected = ["draft", "review", "approved", "published", "archived", "deprecated"]
        actual = [s.value for s in InteractiveElementStatus]
        assert set(expected) == set(actual)


class TestDifficultyLevelEnum:
    """
    WHAT: Tests for DifficultyLevel enum
    WHERE: Tests difficulty level values
    WHY: Ensures proper difficulty categorization
    """

    def test_difficulty_levels(self):
        """Test all difficulty levels exist."""
        assert DifficultyLevel.BEGINNER.value == "beginner"
        assert DifficultyLevel.INTERMEDIATE.value == "intermediate"
        assert DifficultyLevel.ADVANCED.value == "advanced"
        assert DifficultyLevel.EXPERT.value == "expert"


class TestInteractionEventTypeEnum:
    """
    WHAT: Tests for InteractionEventType enum
    WHERE: Tests interaction event type values
    WHY: Ensures all tracking events are available
    """

    def test_all_event_types_exist(self):
        """Test all interaction event types."""
        expected = [
            "started", "interacted", "paused", "resumed",
            "completed", "skipped", "reset", "hint_requested",
            "answer_submitted", "feedback_viewed"
        ]
        actual = [e.value for e in InteractionEventType]
        assert set(expected) == set(actual)


class TestCodeLanguageEnum:
    """
    WHAT: Tests for CodeLanguage enum
    WHERE: Tests supported programming languages
    WHY: Ensures all code playground languages are supported
    """

    def test_all_languages_exist(self):
        """Test all supported languages."""
        expected = [
            "python", "javascript", "typescript", "java",
            "csharp", "cpp", "go", "rust", "ruby",
            "php", "sql", "html", "css", "bash"
        ]
        actual = [l.value for l in CodeLanguage]
        assert set(expected) == set(actual)


# =============================================================================
# Exception Tests
# =============================================================================

class TestInteractiveContentExceptions:
    """
    WHAT: Tests for custom exceptions
    WHERE: Tests exception hierarchy and attributes
    WHY: Ensures proper error handling with context
    """

    def test_base_exception_with_message(self):
        """Test base exception stores message."""
        exc = InteractiveContentException("Test error")
        assert exc.message == "Test error"
        assert exc.details == {}

    def test_base_exception_with_details(self):
        """Test base exception stores details."""
        details = {"key": "value", "count": 42}
        exc = InteractiveContentException("Test error", details)
        assert exc.details == details

    def test_invalid_state_exception_inheritance(self):
        """Test InvalidInteractiveStateException inherits correctly."""
        exc = InvalidInteractiveStateException("Invalid state")
        assert isinstance(exc, InteractiveContentException)

    def test_validation_exception_inheritance(self):
        """Test InteractiveContentValidationException inherits correctly."""
        exc = InteractiveContentValidationException("Validation failed")
        assert isinstance(exc, InteractiveContentException)

    def test_limit_exceeded_exception_inheritance(self):
        """Test InteractionLimitExceededException inherits correctly."""
        exc = InteractionLimitExceededException("Limit exceeded")
        assert isinstance(exc, InteractiveContentException)

    def test_unsupported_language_exception_inheritance(self):
        """Test UnsupportedLanguageException inherits correctly."""
        exc = UnsupportedLanguageException("Language not supported")
        assert isinstance(exc, InteractiveContentException)

    def test_branch_not_found_exception_inheritance(self):
        """Test BranchNotFoundException inherits correctly."""
        exc = BranchNotFoundException("Branch not found")
        assert isinstance(exc, InteractiveContentException)

    def test_hotspot_not_found_exception_inheritance(self):
        """Test HotspotNotFoundException inherits correctly."""
        exc = HotspotNotFoundException("Hotspot not found")
        assert isinstance(exc, InteractiveContentException)


# =============================================================================
# InteractiveElement Tests
# =============================================================================

class TestInteractiveElement:
    """
    WHAT: Tests for InteractiveElement base entity
    WHERE: Tests the foundation interactive content entity
    WHY: Ensures base functionality works for all content types
    """

    @pytest.fixture
    def sample_element(self):
        """Create a sample interactive element for testing."""
        return InteractiveElement(
            id=uuid4(),
            title="Test Element",
            description="A test interactive element",
            content_type=InteractiveContentType.SIMULATION,
            course_id=uuid4(),
            creator_id=uuid4(),
            learning_objectives=["Objective 1", "Objective 2"],
            estimated_duration_minutes=15,
            points_value=25
        )

    def test_element_creation(self, sample_element):
        """Test element is created with correct attributes."""
        assert sample_element.title == "Test Element"
        assert sample_element.status == InteractiveElementStatus.DRAFT
        assert sample_element.version == 1
        assert sample_element.difficulty_level == DifficultyLevel.INTERMEDIATE
        assert len(sample_element.learning_objectives) == 2

    def test_element_defaults(self, sample_element):
        """Test element default values."""
        assert sample_element.max_attempts == 0  # unlimited
        assert sample_element.hints_enabled is True
        assert sample_element.feedback_immediate is True
        assert sample_element.keyboard_navigable is True
        assert sample_element.total_attempts == 0
        assert sample_element.total_completions == 0

    def test_submit_for_review_from_draft(self, sample_element):
        """Test submitting draft element for review."""
        sample_element.submit_for_review()
        assert sample_element.status == InteractiveElementStatus.UNDER_REVIEW

    def test_submit_for_review_from_non_draft_fails(self, sample_element):
        """Test submitting non-draft element raises exception."""
        sample_element.status = InteractiveElementStatus.APPROVED
        with pytest.raises(InvalidInteractiveStateException) as exc_info:
            sample_element.submit_for_review()
        assert "Cannot submit for review" in str(exc_info.value)
        assert exc_info.value.details["current_status"] == "approved"

    def test_approve_from_review(self, sample_element):
        """Test approving element under review."""
        sample_element.status = InteractiveElementStatus.UNDER_REVIEW
        sample_element.approve()
        assert sample_element.status == InteractiveElementStatus.APPROVED

    def test_approve_from_non_review_fails(self, sample_element):
        """Test approving non-review element raises exception."""
        with pytest.raises(InvalidInteractiveStateException) as exc_info:
            sample_element.approve()
        assert "Cannot approve" in str(exc_info.value)

    def test_publish_from_approved(self, sample_element):
        """Test publishing approved element."""
        sample_element.status = InteractiveElementStatus.APPROVED
        sample_element.publish()
        assert sample_element.status == InteractiveElementStatus.PUBLISHED
        assert sample_element.published_at is not None

    def test_publish_from_non_approved_fails(self, sample_element):
        """Test publishing non-approved element raises exception."""
        with pytest.raises(InvalidInteractiveStateException) as exc_info:
            sample_element.publish()
        assert "Cannot publish" in str(exc_info.value)

    def test_archive_from_any_status(self, sample_element):
        """Test archiving works from any status."""
        for status in InteractiveElementStatus:
            sample_element.status = status
            sample_element.archive()
            assert sample_element.status == InteractiveElementStatus.ARCHIVED

    def test_record_attempt_updates_counters(self, sample_element):
        """Test recording attempt updates statistics."""
        sample_element.record_attempt(completed=True, score=85.0, time_seconds=300)
        assert sample_element.total_attempts == 1
        assert sample_element.total_completions == 1
        assert sample_element.avg_score == 85.0

    def test_record_multiple_attempts_calculates_averages(self, sample_element):
        """Test multiple attempts calculate correct averages."""
        sample_element.record_attempt(completed=True, score=80.0, time_seconds=300)
        sample_element.record_attempt(completed=True, score=90.0, time_seconds=400)
        assert sample_element.total_attempts == 2
        assert sample_element.avg_score == 85.0  # (80 + 90) / 2

    def test_record_incomplete_attempt(self, sample_element):
        """Test recording incomplete attempt."""
        sample_element.record_attempt(completed=False, score=40.0, time_seconds=150)
        assert sample_element.total_attempts == 1
        assert sample_element.total_completions == 0

    def test_get_completion_rate_zero_attempts(self, sample_element):
        """Test completion rate with no attempts returns 0."""
        assert sample_element.get_completion_rate() == 0.0

    def test_get_completion_rate_with_attempts(self, sample_element):
        """Test completion rate calculation."""
        sample_element.record_attempt(completed=True, score=80.0, time_seconds=300)
        sample_element.record_attempt(completed=False, score=40.0, time_seconds=150)
        assert sample_element.get_completion_rate() == 50.0

    def test_create_new_version(self, sample_element):
        """Test creating new version of element."""
        sample_element.status = InteractiveElementStatus.PUBLISHED
        sample_element.version = 3

        new_version = sample_element.create_new_version()

        assert new_version.id != sample_element.id
        assert new_version.title == sample_element.title
        assert new_version.version == 4
        assert new_version.status == InteractiveElementStatus.DRAFT
        assert new_version.total_attempts == 0  # Analytics reset

    def test_engagement_score_calculation(self, sample_element):
        """Test engagement score is calculated correctly."""
        # Estimate 15 minutes = 900 seconds
        # Record attempt with good completion but slower time
        sample_element.record_attempt(completed=True, score=100.0, time_seconds=1200)

        # Engagement = 40% completion rate + 30% score + 30% time efficiency
        # Completion: 100% * 0.4 = 40
        # Score: 100 * 0.3 = 30
        # Time efficiency: (900/1200)*100 = 75, capped at 100, so 75 * 0.3 = 22.5
        # Total: 40 + 30 + 22.5 = 92.5
        assert 90 <= sample_element.engagement_score <= 95


# =============================================================================
# Simulation Tests
# =============================================================================

class TestSimulation:
    """
    WHAT: Tests for Simulation entity
    WHERE: Tests simulation validation and scoring
    WHY: Ensures simulations evaluate user outcomes correctly
    """

    @pytest.fixture
    def sample_simulation(self):
        """Create a sample simulation for testing."""
        return Simulation(
            id=uuid4(),
            element_id=uuid4(),
            name="Network Configuration Simulation",
            scenario_description="Configure a basic network",
            initial_state={"ip_address": "", "subnet_mask": ""},
            parameters={"max_nodes": 10},
            expected_outcomes=[
                {"key": "ip_address", "value": "192.168.1.1", "points": 30},
                {"key": "subnet_mask", "value": "255.255.255.0", "points": 20},
                {"key": "gateway", "value": "192.168.1.254", "points": 30}
            ],
            passing_score=70,
            partial_credit=True
        )

    def test_simulation_creation(self, sample_simulation):
        """Test simulation is created correctly."""
        assert sample_simulation.name == "Network Configuration Simulation"
        assert sample_simulation.simulation_type == "guided"
        assert len(sample_simulation.expected_outcomes) == 3

    def test_validate_outcome_all_correct(self, sample_simulation):
        """Test validation with all correct answers."""
        user_state = {
            "ip_address": "192.168.1.1",
            "subnet_mask": "255.255.255.0",
            "gateway": "192.168.1.254"
        }
        result = sample_simulation.validate_outcome(user_state)

        assert result["score"] == 100.0
        assert result["passed"] is True
        assert result["total_points"] == 80
        assert result["max_points"] == 80

    def test_validate_outcome_partial_correct(self, sample_simulation):
        """Test validation with some correct answers."""
        user_state = {
            "ip_address": "192.168.1.1",
            "subnet_mask": "255.255.0.0",  # Wrong
            "gateway": "192.168.1.254"
        }
        result = sample_simulation.validate_outcome(user_state)

        assert result["passed"] is True  # 60/80 = 75%
        assert result["total_points"] == 60

    def test_validate_outcome_missing_keys(self, sample_simulation):
        """Test validation with missing keys."""
        user_state = {"ip_address": "192.168.1.1"}
        result = sample_simulation.validate_outcome(user_state)

        # Only ip_address correct (30 points out of 80)
        assert result["score"] == 37.5
        assert result["passed"] is False

    def test_validate_outcome_with_partial_credit(self, sample_simulation):
        """Test partial credit for numeric values."""
        sample_simulation.expected_outcomes = [
            {"key": "temperature", "value": 100.0, "points": 50}
        ]
        user_state = {"temperature": 105.0}  # Within 10% tolerance
        result = sample_simulation.validate_outcome(user_state)

        assert result["total_points"] > 0  # Should get partial credit

    def test_get_current_step_valid_index(self, sample_simulation):
        """Test getting valid guided step."""
        sample_simulation.guided_steps = [
            {"instruction": "Step 1", "action": "configure"},
            {"instruction": "Step 2", "action": "verify"}
        ]
        step = sample_simulation.get_current_step(0)
        assert step["instruction"] == "Step 1"

    def test_get_current_step_invalid_index(self, sample_simulation):
        """Test getting invalid step index returns None."""
        sample_simulation.guided_steps = [{"instruction": "Step 1"}]
        assert sample_simulation.get_current_step(5) is None
        assert sample_simulation.get_current_step(-1) is None


# =============================================================================
# DragDropActivity Tests
# =============================================================================

class TestDragDropActivity:
    """
    WHAT: Tests for DragDropActivity entity
    WHERE: Tests drag-drop evaluation and item management
    WHY: Ensures drag-drop activities evaluate correctly
    """

    @pytest.fixture
    def sample_drag_drop(self):
        """Create a sample drag-drop activity."""
        zone1_id = uuid4()
        zone2_id = uuid4()

        activity = DragDropActivity(
            id=uuid4(),
            element_id=uuid4(),
            activity_type="categorize",
            instructions="Drag items to correct categories",
            items=[
                DragDropItem(
                    id=uuid4(),
                    content="Python",
                    correct_zone_ids=[zone1_id],
                    points=10,
                    feedback_correct="Correct! Python is a programming language.",
                    feedback_incorrect="Python is a programming language."
                ),
                DragDropItem(
                    id=uuid4(),
                    content="JavaScript",
                    correct_zone_ids=[zone1_id],
                    points=10,
                    feedback_correct="Correct!",
                    feedback_incorrect="JavaScript is a programming language."
                ),
                DragDropItem(
                    id=uuid4(),
                    content="HTML",
                    correct_zone_ids=[zone2_id],
                    points=10,
                    feedback_correct="Correct! HTML is a markup language.",
                    feedback_incorrect="HTML is a markup language."
                )
            ],
            zones=[
                DropZone(id=zone1_id, label="Programming Languages"),
                DropZone(id=zone2_id, label="Markup Languages")
            ],
            partial_credit=True,
            deduct_for_incorrect=False
        )
        return activity, zone1_id, zone2_id

    def test_activity_creation(self, sample_drag_drop):
        """Test activity is created correctly."""
        activity, _, _ = sample_drag_drop
        assert activity.activity_type == "categorize"
        assert len(activity.items) == 3
        assert len(activity.zones) == 2

    def test_evaluate_all_correct(self, sample_drag_drop):
        """Test evaluation with all correct placements."""
        activity, zone1_id, zone2_id = sample_drag_drop

        placements = {
            str(zone1_id): [str(activity.items[0].id), str(activity.items[1].id)],
            str(zone2_id): [str(activity.items[2].id)]
        }
        result = activity.evaluate_submission(placements)

        assert result["score"] == 100.0
        assert result["items_correct"] == 3
        assert result["items_total"] == 3

    def test_evaluate_partial_correct(self, sample_drag_drop):
        """Test evaluation with some correct placements."""
        activity, zone1_id, zone2_id = sample_drag_drop

        # Put HTML in wrong zone
        placements = {
            str(zone1_id): [str(activity.items[0].id), str(activity.items[1].id), str(activity.items[2].id)],
            str(zone2_id): []
        }
        result = activity.evaluate_submission(placements)

        assert result["items_correct"] == 2
        assert result["score"] == pytest.approx(66.67, rel=0.1)

    def test_evaluate_with_deduction(self, sample_drag_drop):
        """Test evaluation with deduction for incorrect."""
        activity, zone1_id, zone2_id = sample_drag_drop
        activity.deduct_for_incorrect = True
        activity.deduction_percent = 50

        # Put HTML in wrong zone
        placements = {
            str(zone1_id): [str(activity.items[0].id), str(activity.items[2].id)],  # HTML wrong
            str(zone2_id): [str(activity.items[1].id)]  # JavaScript wrong
        }
        result = activity.evaluate_submission(placements)

        # 1 correct (10), 2 wrong with deductions (-5 each)
        assert result["total_points"] == 0  # Can't go negative

    def test_add_item(self, sample_drag_drop):
        """Test adding items to activity."""
        activity, zone1_id, _ = sample_drag_drop
        new_item = DragDropItem(
            id=uuid4(),
            content="CSS",
            correct_zone_ids=[zone1_id],
            points=10
        )
        activity.add_item(new_item)
        assert len(activity.items) == 4

    def test_add_zone(self, sample_drag_drop):
        """Test adding zones to activity."""
        activity, _, _ = sample_drag_drop
        new_zone = DropZone(id=uuid4(), label="Style Languages")
        activity.add_zone(new_zone)
        assert len(activity.zones) == 3


# =============================================================================
# InteractiveDiagram Tests
# =============================================================================

class TestInteractiveDiagram:
    """
    WHAT: Tests for InteractiveDiagram entity
    WHERE: Tests diagram hotspots and quiz evaluation
    WHY: Ensures diagrams handle interactions correctly
    """

    @pytest.fixture
    def sample_diagram(self):
        """Create a sample interactive diagram."""
        hotspot1_id = uuid4()
        hotspot2_id = uuid4()

        return InteractiveDiagram(
            id=uuid4(),
            element_id=uuid4(),
            title="Human Heart Anatomy",
            base_image_url="https://example.com/heart.png",
            hotspots=[
                Hotspot(
                    id=hotspot1_id,
                    label="Left Ventricle",
                    description="The main pumping chamber",
                    is_quiz_point=True,
                    quiz_question="What is the main function?",
                    quiz_answer="pump blood"
                ),
                Hotspot(
                    id=hotspot2_id,
                    label="Right Atrium",
                    description="Receives blood from body",
                    is_quiz_point=True,
                    quiz_question="What blood does it receive?",
                    quiz_answer="deoxygenated"
                ),
                Hotspot(
                    id=uuid4(),
                    label="Aorta",
                    description="Main artery",
                    is_quiz_point=False  # Not a quiz point
                )
            ],
            layers=[
                DiagramLayer(
                    id=uuid4(),
                    name="Base Layer",
                    image_url="https://example.com/base.png",
                    is_base_layer=True
                ),
                DiagramLayer(
                    id=uuid4(),
                    name="Blood Flow Layer",
                    image_url="https://example.com/blood.png"
                )
            ],
            quiz_passing_score=50
        ), hotspot1_id, hotspot2_id

    def test_diagram_creation(self, sample_diagram):
        """Test diagram is created correctly."""
        diagram, _, _ = sample_diagram
        assert diagram.title == "Human Heart Anatomy"
        assert len(diagram.hotspots) == 3
        assert len(diagram.layers) == 2

    def test_add_hotspot(self, sample_diagram):
        """Test adding hotspot to diagram."""
        diagram, _, _ = sample_diagram
        new_hotspot = Hotspot(
            id=uuid4(),
            label="Pulmonary Artery",
            description="Carries blood to lungs"
        )
        diagram.add_hotspot(new_hotspot)
        assert len(diagram.hotspots) == 4

    def test_add_layer(self, sample_diagram):
        """Test adding layer to diagram."""
        diagram, _, _ = sample_diagram
        new_layer = DiagramLayer(
            id=uuid4(),
            name="Nervous System Layer",
            image_url="https://example.com/nerves.png"
        )
        diagram.add_layer(new_layer)
        assert len(diagram.layers) == 3

    def test_get_hotspot_found(self, sample_diagram):
        """Test getting existing hotspot."""
        diagram, hotspot1_id, _ = sample_diagram
        hotspot = diagram.get_hotspot(hotspot1_id)
        assert hotspot.label == "Left Ventricle"

    def test_get_hotspot_not_found(self, sample_diagram):
        """Test getting non-existent hotspot raises exception."""
        diagram, _, _ = sample_diagram
        with pytest.raises(HotspotNotFoundException) as exc_info:
            diagram.get_hotspot(uuid4())
        assert "Hotspot" in str(exc_info.value)

    def test_get_quiz_hotspots(self, sample_diagram):
        """Test getting only quiz-enabled hotspots."""
        diagram, _, _ = sample_diagram
        quiz_hotspots = diagram.get_quiz_hotspots()
        assert len(quiz_hotspots) == 2  # Only 2 have is_quiz_point=True

    def test_evaluate_quiz_all_correct(self, sample_diagram):
        """Test quiz evaluation with all correct answers."""
        diagram, hotspot1_id, hotspot2_id = sample_diagram
        answers = {
            str(hotspot1_id): "pump blood",
            str(hotspot2_id): "deoxygenated"
        }
        result = diagram.evaluate_quiz(answers)

        assert result["score"] == 100.0
        assert result["passed"] is True
        assert result["correct_count"] == 2

    def test_evaluate_quiz_partial_correct(self, sample_diagram):
        """Test quiz evaluation with some correct answers."""
        diagram, hotspot1_id, hotspot2_id = sample_diagram
        answers = {
            str(hotspot1_id): "pump blood",
            str(hotspot2_id): "oxygenated"  # Wrong
        }
        result = diagram.evaluate_quiz(answers)

        assert result["score"] == 50.0
        assert result["passed"] is True  # Passing score is 50
        assert result["correct_count"] == 1

    def test_evaluate_quiz_no_questions(self, sample_diagram):
        """Test quiz evaluation with no quiz points."""
        diagram, _, _ = sample_diagram
        # Remove quiz points
        for h in diagram.hotspots:
            h.is_quiz_point = False

        result = diagram.evaluate_quiz({})
        assert result["score"] == 0
        assert "No quiz questions" in result["message"]


# =============================================================================
# CodePlayground Tests
# =============================================================================

class TestCodePlayground:
    """
    WHAT: Tests for CodePlayground entity
    WHERE: Tests code execution and evaluation
    WHY: Ensures code playgrounds evaluate student code correctly
    """

    @pytest.fixture
    def sample_playground(self):
        """Create a sample code playground."""
        playground = CodePlayground(
            id=uuid4(),
            element_id=uuid4(),
            title="Python FizzBuzz Challenge",
            instructions="Write a function that prints FizzBuzz",
            language=CodeLanguage.PYTHON,
            starter_code="def fizzbuzz(n):\n    pass",
            solution_code="def fizzbuzz(n):\n    for i in range(1, n+1):\n        if i % 15 == 0:\n            print('FizzBuzz')\n        elif i % 3 == 0:\n            print('Fizz')\n        elif i % 5 == 0:\n            print('Buzz')\n        else:\n            print(i)",
            passing_score=70,
            partial_credit=True
        )
        # Add test cases
        playground.add_test_case("Small input", "3", "1\n2\nFizz", points=20)
        playground.add_test_case("FizzBuzz", "15", "1\n2\nFizz\n4\nBuzz\n...", points=30)
        playground.add_test_case("Hidden test", "100", "...", points=50, is_hidden=True)

        return playground

    def test_playground_creation(self, sample_playground):
        """Test playground is created correctly."""
        assert sample_playground.language == CodeLanguage.PYTHON
        assert len(sample_playground.test_cases) == 3

    def test_validate_language_valid(self, sample_playground):
        """Test validating supported language."""
        assert sample_playground.validate_language("python") is True
        assert sample_playground.validate_language("javascript") is True

    def test_validate_language_invalid(self, sample_playground):
        """Test validating unsupported language."""
        assert sample_playground.validate_language("brainfuck") is False
        assert sample_playground.validate_language("cobol") is False

    def test_add_test_case(self, sample_playground):
        """Test adding test cases."""
        initial_count = len(sample_playground.test_cases)
        sample_playground.add_test_case(
            "Edge case", "0", "", points=10, is_hidden=False
        )
        assert len(sample_playground.test_cases) == initial_count + 1

    def test_evaluate_output_all_correct(self, sample_playground):
        """Test evaluation with all tests passing."""
        outputs = []
        for test in sample_playground.test_cases:
            outputs.append({
                "test_id": test["id"],
                "output": test["expected_output"]
            })

        result = sample_playground.evaluate_output(outputs)

        assert result["score"] == 100.0
        assert result["passed"] is True
        assert result["tests_passed"] == 3

    def test_evaluate_output_partial_correct(self, sample_playground):
        """Test evaluation with some tests passing."""
        outputs = [
            {"test_id": sample_playground.test_cases[0]["id"], "output": "1\n2\nFizz"},
            {"test_id": sample_playground.test_cases[1]["id"], "output": "wrong"},
            {"test_id": sample_playground.test_cases[2]["id"], "output": "wrong"}
        ]

        result = sample_playground.evaluate_output(outputs)

        assert result["tests_passed"] == 1
        assert result["earned_points"] == 20

    def test_evaluate_output_with_partial_credit(self, sample_playground):
        """Test partial credit for close answers."""
        # Create simple test case
        sample_playground.test_cases = [
            {"id": "1", "name": "Test", "input": "", "expected_output": "line1\nline2\nline3", "points": 30}
        ]

        outputs = [
            {"test_id": "1", "output": "line1\nline2\nwrong"}  # 2/3 lines correct
        ]

        result = sample_playground.evaluate_output(outputs)

        # Should get some partial credit
        assert result["earned_points"] > 0
        assert result["earned_points"] < 30

    def test_calculate_output_similarity_exact_match(self, sample_playground):
        """Test similarity calculation for exact match."""
        similarity = sample_playground._calculate_output_similarity(
            "hello\nworld", "hello\nworld"
        )
        assert similarity == 1.0

    def test_calculate_output_similarity_no_match(self, sample_playground):
        """Test similarity calculation for no match."""
        similarity = sample_playground._calculate_output_similarity(
            "completely\ndifferent", "hello\nworld"
        )
        assert similarity == 0.0

    def test_calculate_output_similarity_empty(self, sample_playground):
        """Test similarity calculation for empty strings."""
        assert sample_playground._calculate_output_similarity("", "test") == 0.0
        assert sample_playground._calculate_output_similarity("test", "") == 0.0


# =============================================================================
# BranchingScenario Tests
# =============================================================================

class TestBranchingScenario:
    """
    WHAT: Tests for BranchingScenario entity
    WHERE: Tests scenario branching and path evaluation
    WHY: Ensures scenarios navigate and score correctly
    """

    @pytest.fixture
    def sample_scenario(self):
        """Create a sample branching scenario."""
        start_id = uuid4()
        branch2_id = uuid4()
        success_id = uuid4()
        failure_id = uuid4()

        scenario = BranchingScenario(
            id=uuid4(),
            element_id=uuid4(),
            title="Customer Service Scenario",
            introduction="Handle a customer complaint",
            max_score=100,
            passing_score=60
        )

        # Add branches
        scenario.add_branch(ScenarioBranch(
            id=start_id,
            content="Customer is upset about late delivery",
            is_start=True,
            options=[
                {"text": "Apologize and offer solution", "next_branch_id": str(branch2_id), "points": 30},
                {"text": "Blame shipping company", "next_branch_id": str(failure_id), "points": 0}
            ],
            points_value=10
        ))

        scenario.add_branch(ScenarioBranch(
            id=branch2_id,
            content="Customer appreciates your response",
            options=[
                {"text": "Offer discount", "next_branch_id": str(success_id), "points": 40}
            ],
            points_value=20,
            branch_feedback="Good choice! Empathy is key."
        ))

        scenario.add_branch(ScenarioBranch(
            id=success_id,
            content="Customer leaves satisfied",
            is_end=True,
            is_success_end=True,
            points_value=30
        ))

        scenario.add_branch(ScenarioBranch(
            id=failure_id,
            content="Customer escalates complaint",
            is_end=True,
            is_failure_end=True,
            points_value=0
        ))

        return scenario, start_id, branch2_id, success_id, failure_id

    def test_scenario_creation(self, sample_scenario):
        """Test scenario is created correctly."""
        scenario, _, _, _, _ = sample_scenario
        assert scenario.title == "Customer Service Scenario"
        assert len(scenario.branches) == 4

    def test_add_branch_sets_start(self, sample_scenario):
        """Test adding start branch sets start_branch_id."""
        scenario, start_id, _, _, _ = sample_scenario
        assert scenario.start_branch_id == start_id

    def test_get_branch_found(self, sample_scenario):
        """Test getting existing branch."""
        scenario, start_id, _, _, _ = sample_scenario
        branch = scenario.get_branch(start_id)
        assert branch.is_start is True

    def test_get_branch_not_found(self, sample_scenario):
        """Test getting non-existent branch raises exception."""
        scenario, _, _, _, _ = sample_scenario
        with pytest.raises(BranchNotFoundException):
            scenario.get_branch(uuid4())

    def test_get_start_branch(self, sample_scenario):
        """Test getting start branch."""
        scenario, start_id, _, _, _ = sample_scenario
        start = scenario.get_start_branch()
        assert start.id == start_id
        assert start.is_start is True

    def test_get_start_branch_not_defined(self):
        """Test getting start branch when not defined."""
        scenario = BranchingScenario(
            id=uuid4(),
            element_id=uuid4(),
            title="Empty Scenario",
            introduction="No branches"
        )
        with pytest.raises(BranchNotFoundException) as exc_info:
            scenario.get_start_branch()
        assert "No start branch" in str(exc_info.value)

    def test_evaluate_path_success(self, sample_scenario):
        """Test evaluating successful path."""
        scenario, start_id, branch2_id, success_id, _ = sample_scenario

        path = [start_id, branch2_id, success_id]
        choices = []  # Simplified

        result = scenario.evaluate_path(path, choices)

        assert result["outcome"] == "success"
        assert result["passed"] is True
        assert result["total_points"] == 60  # 10 + 20 + 30

    def test_evaluate_path_failure(self, sample_scenario):
        """Test evaluating failure path."""
        scenario, start_id, _, _, failure_id = sample_scenario

        path = [start_id, failure_id]
        choices = []

        result = scenario.evaluate_path(path, choices)

        assert result["outcome"] == "failure"
        assert result["total_points"] == 10  # Only start branch points

    def test_evaluate_path_includes_feedback(self, sample_scenario):
        """Test path evaluation includes feedback."""
        scenario, start_id, branch2_id, success_id, _ = sample_scenario

        path = [start_id, branch2_id, success_id]
        result = scenario.evaluate_path(path, [])

        # Branch2 has feedback
        assert len(result["feedback"]) >= 1


# =============================================================================
# InteractiveTimeline Tests
# =============================================================================

class TestInteractiveTimeline:
    """
    WHAT: Tests for InteractiveTimeline entity
    WHERE: Tests timeline event management
    WHY: Ensures timelines handle events correctly
    """

    @pytest.fixture
    def sample_timeline(self):
        """Create a sample interactive timeline."""
        timeline = InteractiveTimeline(
            id=uuid4(),
            element_id=uuid4(),
            title="World War II Timeline",
            description="Key events of WWII",
            categories=[
                {"name": "Military", "color": "#FF0000"},
                {"name": "Political", "color": "#0000FF"}
            ]
        )

        # Add events
        timeline.add_event(TimelineEvent(
            id=uuid4(),
            title="D-Day",
            description="Allied invasion of Normandy",
            date=datetime(1944, 6, 6),
            category="Military",
            is_milestone=True
        ))

        timeline.add_event(TimelineEvent(
            id=uuid4(),
            title="Germany Surrenders",
            description="V-E Day",
            date=datetime(1945, 5, 8),
            category="Political",
            is_milestone=True
        ))

        timeline.add_event(TimelineEvent(
            id=uuid4(),
            title="Battle of the Bulge",
            description="German offensive",
            date=datetime(1944, 12, 16),
            category="Military",
            is_milestone=False
        ))

        return timeline

    def test_timeline_creation(self, sample_timeline):
        """Test timeline is created correctly."""
        assert sample_timeline.title == "World War II Timeline"
        assert len(sample_timeline.events) == 3

    def test_add_event_sorts_by_date(self, sample_timeline):
        """Test events are sorted by date after adding."""
        dates = [e.date for e in sample_timeline.events]
        assert dates == sorted(dates)

    def test_add_event_updates_date_range(self, sample_timeline):
        """Test adding events updates start/end dates."""
        assert sample_timeline.start_date == datetime(1944, 6, 6)
        assert sample_timeline.end_date == datetime(1945, 5, 8)

    def test_get_events_by_category(self, sample_timeline):
        """Test filtering events by category."""
        military_events = sample_timeline.get_events_by_category("Military")
        assert len(military_events) == 2

    def test_get_milestones(self, sample_timeline):
        """Test getting milestone events."""
        milestones = sample_timeline.get_milestones()
        assert len(milestones) == 2

    def test_get_events_in_range(self, sample_timeline):
        """Test getting events within date range."""
        start = datetime(1944, 6, 1)
        end = datetime(1944, 12, 31)
        events = sample_timeline.get_events_in_range(start, end)
        assert len(events) == 2  # D-Day and Battle of the Bulge


# =============================================================================
# Flashcard and FlashcardDeck Tests
# =============================================================================

class TestFlashcard:
    """
    WHAT: Tests for Flashcard entity
    WHERE: Tests spaced repetition algorithm
    WHY: Ensures SM-2 algorithm works correctly
    """

    @pytest.fixture
    def sample_flashcard(self):
        """Create a sample flashcard."""
        return Flashcard(
            id=uuid4(),
            front_content="What is the capital of France?",
            back_content="Paris",
            difficulty=2.5,  # Initial easiness factor
            interval_days=1,
            repetitions=0
        )

    def test_flashcard_creation(self, sample_flashcard):
        """Test flashcard is created correctly."""
        assert sample_flashcard.front_content == "What is the capital of France?"
        assert sample_flashcard.difficulty == 2.5
        assert sample_flashcard.repetitions == 0

    def test_update_spaced_repetition_perfect_response(self, sample_flashcard):
        """Test SM-2 with perfect response (quality=5)."""
        sample_flashcard.update_spaced_repetition(quality=5)

        assert sample_flashcard.repetitions == 1
        assert sample_flashcard.interval_days == 1  # First rep
        assert sample_flashcard.times_correct == 1
        assert sample_flashcard.difficulty >= 2.5  # Easiness increases

    def test_update_spaced_repetition_good_response(self, sample_flashcard):
        """Test SM-2 with good response (quality=4)."""
        sample_flashcard.update_spaced_repetition(quality=4)

        assert sample_flashcard.repetitions == 1
        assert sample_flashcard.times_correct == 1

    def test_update_spaced_repetition_failure(self, sample_flashcard):
        """Test SM-2 with failure (quality<3)."""
        # First get some repetitions
        sample_flashcard.repetitions = 5
        sample_flashcard.interval_days = 30

        sample_flashcard.update_spaced_repetition(quality=2)

        assert sample_flashcard.repetitions == 0  # Reset
        assert sample_flashcard.interval_days == 1  # Reset
        assert sample_flashcard.times_incorrect == 1

    def test_update_spaced_repetition_interval_progression(self, sample_flashcard):
        """Test interval increases over successful repetitions."""
        # First review - interval stays 1
        sample_flashcard.update_spaced_repetition(quality=5)
        assert sample_flashcard.interval_days == 1

        # Second review - interval becomes 6
        sample_flashcard.update_spaced_repetition(quality=5)
        assert sample_flashcard.interval_days == 6

        # Third review - interval multiplied by easiness
        sample_flashcard.update_spaced_repetition(quality=5)
        assert sample_flashcard.interval_days > 6

    def test_update_spaced_repetition_sets_next_review(self, sample_flashcard):
        """Test next review date is set."""
        sample_flashcard.update_spaced_repetition(quality=4)
        assert sample_flashcard.next_review is not None
        assert sample_flashcard.last_reviewed is not None


class TestFlashcardDeck:
    """
    WHAT: Tests for FlashcardDeck entity
    WHERE: Tests deck management and review scheduling
    WHY: Ensures deck operations work correctly
    """

    @pytest.fixture
    def sample_deck(self):
        """Create a sample flashcard deck."""
        deck = FlashcardDeck(
            id=uuid4(),
            element_id=uuid4(),
            name="French Vocabulary",
            description="Common French words",
            new_cards_per_day=10,
            reviews_per_day=50
        )

        # Add cards with varying states
        for i in range(15):
            card = Flashcard(
                id=uuid4(),
                front_content=f"Word {i}",
                back_content=f"Translation {i}"
            )
            if i < 5:
                # Make some cards due for review
                card.repetitions = 2
                card.next_review = datetime.utcnow() - timedelta(hours=1)
            deck.add_card(card)

        return deck

    def test_deck_creation(self, sample_deck):
        """Test deck is created correctly."""
        assert sample_deck.name == "French Vocabulary"
        assert len(sample_deck.cards) == 15

    def test_add_card(self, sample_deck):
        """Test adding card to deck."""
        initial_count = len(sample_deck.cards)
        new_card = Flashcard(
            id=uuid4(),
            front_content="New word",
            back_content="New translation"
        )
        sample_deck.add_card(new_card)
        assert len(sample_deck.cards) == initial_count + 1

    def test_get_cards_for_review(self, sample_deck):
        """Test getting cards due for review."""
        due_cards = sample_deck.get_cards_for_review()
        # 5 cards should be due
        assert len(due_cards) == 5

    def test_get_new_cards(self, sample_deck):
        """Test getting new cards."""
        new_cards = sample_deck.get_new_cards()
        # 10 cards should be new (repetitions=0)
        assert len(new_cards) == 10  # Limited by new_cards_per_day

    def test_record_review_updates_stats(self, sample_deck):
        """Test recording review updates deck statistics."""
        card_id = sample_deck.cards[0].id

        sample_deck.record_review(card_id, quality=4)

        assert sample_deck.total_reviews == 1
        assert sample_deck.correct_reviews == 1
        assert sample_deck.streak_days == 1

    def test_record_review_failure(self, sample_deck):
        """Test recording failed review."""
        card_id = sample_deck.cards[0].id

        sample_deck.record_review(card_id, quality=2)

        assert sample_deck.total_reviews == 1
        assert sample_deck.correct_reviews == 0

    def test_get_retention_rate_zero_reviews(self, sample_deck):
        """Test retention rate with no reviews."""
        assert sample_deck.get_retention_rate() == 0.0

    def test_get_retention_rate_with_reviews(self, sample_deck):
        """Test retention rate calculation."""
        sample_deck.total_reviews = 10
        sample_deck.correct_reviews = 8
        assert sample_deck.get_retention_rate() == 80.0

    def test_get_mastery_level(self, sample_deck):
        """Test mastery level distribution."""
        mastery = sample_deck.get_mastery_level()

        assert "new" in mastery
        assert "learning" in mastery
        assert "young" in mastery
        assert "mature" in mastery
        assert mastery["new"] == 10  # Cards with repetitions=0

    def test_streak_continues(self, sample_deck):
        """Test streak continues with consecutive days."""
        sample_deck.last_study_date = datetime.utcnow() - timedelta(days=1)
        sample_deck.streak_days = 5

        sample_deck.record_review(sample_deck.cards[0].id, quality=4)

        assert sample_deck.streak_days == 6

    def test_streak_resets(self, sample_deck):
        """Test streak resets after missed day."""
        sample_deck.last_study_date = datetime.utcnow() - timedelta(days=3)
        sample_deck.streak_days = 5

        sample_deck.record_review(sample_deck.cards[0].id, quality=4)

        assert sample_deck.streak_days == 1


# =============================================================================
# InteractiveVideo Tests
# =============================================================================

class TestInteractiveVideo:
    """
    WHAT: Tests for InteractiveVideo entity
    WHERE: Tests video interactions and session evaluation
    WHY: Ensures video interactions work correctly
    """

    @pytest.fixture
    def sample_video(self):
        """Create a sample interactive video."""
        video = InteractiveVideo(
            id=uuid4(),
            element_id=uuid4(),
            title="Python Basics Tutorial",
            description="Learn Python fundamentals",
            video_url="https://example.com/video.mp4",
            video_duration_seconds=600.0,  # 10 minutes
            watch_percentage_required=80,
            interactions_percentage_required=100,
            passing_score=70
        )

        # Add interactions
        video.add_interaction(VideoInteraction(
            id=uuid4(),
            timestamp_seconds=60.0,
            interaction_type="question",
            question="What is a variable?",
            options=[{"text": "A storage location"}, {"text": "A function"}],
            correct_answer="A storage location",
            points=20
        ))

        video.add_interaction(VideoInteraction(
            id=uuid4(),
            timestamp_seconds=180.0,
            interaction_type="question",
            question="What is a loop?",
            options=[{"text": "Iteration"}, {"text": "Declaration"}],
            correct_answer="Iteration",
            points=30
        ))

        video.add_chapter("Introduction", 0, 60)
        video.add_chapter("Variables", 60, 180)
        video.add_chapter("Loops", 180, 360)

        return video

    def test_video_creation(self, sample_video):
        """Test video is created correctly."""
        assert sample_video.title == "Python Basics Tutorial"
        assert len(sample_video.interactions) == 2
        assert len(sample_video.chapters) == 3

    def test_add_interaction_sorts_by_timestamp(self, sample_video):
        """Test interactions are sorted by timestamp."""
        timestamps = [i.timestamp_seconds for i in sample_video.interactions]
        assert timestamps == sorted(timestamps)

    def test_add_chapter_sorts_by_start_time(self, sample_video):
        """Test chapters are sorted by start time."""
        starts = [c["start_seconds"] for c in sample_video.chapters]
        assert starts == sorted(starts)

    def test_get_interactions_in_range(self, sample_video):
        """Test getting interactions in time range."""
        interactions = sample_video.get_interactions_in_range(0, 100)
        assert len(interactions) == 1  # Only first interaction

    def test_evaluate_session_complete_success(self, sample_video):
        """Test session evaluation with full completion."""
        watch_time = 500.0  # More than 80%
        responses = {
            str(sample_video.interactions[0].id): "A storage location",
            str(sample_video.interactions[1].id): "Iteration"
        }

        result = sample_video.evaluate_session(watch_time, responses)

        assert result["completed"] is True
        assert result["score"] == 100.0
        assert result["watch_passed"] is True
        assert result["interactions_passed"] is True

    def test_evaluate_session_partial_watch(self, sample_video):
        """Test session evaluation with incomplete watch."""
        watch_time = 200.0  # Less than 80%
        responses = {
            str(sample_video.interactions[0].id): "A storage location",
            str(sample_video.interactions[1].id): "Iteration"
        }

        result = sample_video.evaluate_session(watch_time, responses)

        assert result["completed"] is False
        assert result["watch_passed"] is False

    def test_evaluate_session_wrong_answers(self, sample_video):
        """Test session evaluation with wrong answers."""
        watch_time = 500.0
        responses = {
            str(sample_video.interactions[0].id): "A function",  # Wrong
            str(sample_video.interactions[1].id): "Iteration"
        }

        result = sample_video.evaluate_session(watch_time, responses)

        assert result["score"] == 60.0  # 30/50 points
        assert result["earned_points"] == 30

    def test_evaluate_session_missing_interactions(self, sample_video):
        """Test session evaluation with missing interactions."""
        watch_time = 500.0
        responses = {
            str(sample_video.interactions[0].id): "A storage location"
            # Missing second interaction
        }

        result = sample_video.evaluate_session(watch_time, responses)

        assert result["interactions_completed"] == 1
        assert result["interactions_total"] == 2
        assert result["interactions_passed"] is False


# =============================================================================
# InteractionSession Tests
# =============================================================================

class TestInteractionSession:
    """
    WHAT: Tests for InteractionSession entity
    WHERE: Tests session tracking and analytics
    WHY: Ensures session data is tracked correctly
    """

    @pytest.fixture
    def sample_session(self):
        """Create a sample interaction session."""
        return InteractionSession(
            id=uuid4(),
            element_id=uuid4(),
            user_id=uuid4(),
            device_type="desktop",
            browser="Chrome"
        )

    def test_session_creation(self, sample_session):
        """Test session is created correctly."""
        assert sample_session.status == "in_progress"
        assert sample_session.attempts == 1
        assert sample_session.actions_count == 0

    def test_record_action(self, sample_session):
        """Test recording actions."""
        sample_session.record_action("clicked_button", {"button_id": "submit"})
        sample_session.record_action("viewed_hint")

        assert sample_session.actions_count == 2
        assert len(sample_session.actions) == 2
        assert sample_session.actions[0]["type"] == "clicked_button"

    def test_complete_session(self, sample_session):
        """Test completing session."""
        sample_session.complete(score=85.0, passed=True)

        assert sample_session.status == "completed"
        assert sample_session.completion_percentage == 100.0
        assert sample_session.score == 85.0
        assert sample_session.passed is True
        assert sample_session.ended_at is not None
        assert sample_session.duration_seconds > 0

    def test_abandon_session(self, sample_session):
        """Test abandoning session."""
        sample_session.abandon()

        assert sample_session.status == "abandoned"
        assert sample_session.ended_at is not None

    def test_duration_calculation(self, sample_session):
        """Test duration is calculated correctly."""
        import time
        time.sleep(0.1)  # Small delay

        sample_session.complete(score=100.0, passed=True)

        assert sample_session.duration_seconds >= 0.1


# =============================================================================
# Integration Tests
# =============================================================================

class TestInteractiveContentIntegration:
    """
    WHAT: Integration tests for interactive content workflow
    WHERE: Tests full lifecycle of interactive content
    WHY: Ensures all components work together correctly
    """

    def test_element_lifecycle_with_session(self):
        """Test complete element lifecycle with user session."""
        # Create element
        element = InteractiveElement(
            id=uuid4(),
            title="Math Quiz",
            description="Basic math questions",
            content_type=InteractiveContentType.SIMULATION,
            course_id=uuid4(),
            creator_id=uuid4()
        )

        # Publish workflow
        element.submit_for_review()
        element.approve()
        element.publish()
        assert element.status == InteractiveElementStatus.PUBLISHED

        # Create session
        session = InteractionSession(
            id=uuid4(),
            element_id=element.id,
            user_id=uuid4()
        )

        # Record interactions
        session.record_action("started")
        session.record_action("answered_question", {"question": 1, "correct": True})
        session.record_action("answered_question", {"question": 2, "correct": True})
        session.complete(score=100.0, passed=True)

        # Update element analytics
        element.record_attempt(
            completed=True,
            score=session.score,
            time_seconds=session.duration_seconds
        )

        assert element.total_completions == 1
        assert element.avg_score == 100.0

    def test_flashcard_deck_study_session(self):
        """Test complete flashcard study session."""
        deck = FlashcardDeck(
            id=uuid4(),
            element_id=uuid4(),
            name="Test Deck",
            description="Test"
        )

        # Add cards
        for i in range(5):
            deck.add_card(Flashcard(
                id=uuid4(),
                front_content=f"Q{i}",
                back_content=f"A{i}"
            ))

        # Study session
        new_cards = deck.get_new_cards()
        assert len(new_cards) == 5

        # Review all cards with good quality
        for card in new_cards:
            deck.record_review(card.id, quality=4)

        assert deck.total_reviews == 5
        assert deck.correct_reviews == 5
        assert deck.get_retention_rate() == 100.0

    def test_drag_drop_with_multiple_zones(self):
        """Test drag-drop with complex zone configuration."""
        zone_ids = [uuid4() for _ in range(3)]

        activity = DragDropActivity(
            id=uuid4(),
            element_id=uuid4(),
            activity_type="sort",
            instructions="Sort items into categories",
            zones=[
                DropZone(id=zone_ids[0], label="Small", accepts_multiple=True, max_items=5),
                DropZone(id=zone_ids[1], label="Medium", accepts_multiple=True, max_items=5),
                DropZone(id=zone_ids[2], label="Large", accepts_multiple=True, max_items=5)
            ]
        )

        # Add items
        items = []
        for i, size in enumerate(["apple", "car", "house", "ant", "elephant"]):
            item = DragDropItem(
                id=uuid4(),
                content=size,
                correct_zone_ids=[zone_ids[i % 3]],
                points=20
            )
            items.append(item)
            activity.add_item(item)

        # Evaluate correct submission
        placements = {
            str(zone_ids[0]): [str(items[0].id), str(items[3].id)],
            str(zone_ids[1]): [str(items[1].id), str(items[4].id)],
            str(zone_ids[2]): [str(items[2].id)]
        }

        result = activity.evaluate_submission(placements)
        assert result["items_total"] == 5
