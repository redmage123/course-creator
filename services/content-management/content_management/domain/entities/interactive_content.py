"""
Interactive Content Domain Entities

WHAT: Domain entities for interactive learning content types
WHERE: Used throughout the content-management service for interactive content handling
WHY: Provides rich domain models for creating and managing engaging,
     interactive educational experiences beyond traditional static content

This module defines entities for:
- InteractiveElement: Base element for interactive components
- Simulation: Virtual scenarios with configurable parameters
- DragDropActivity: Items that can be matched, sorted, or categorized
- InteractiveDiagram: Diagrams with clickable hotspots and layers
- CodePlayground: In-browser code editing and execution environments
- BranchingScenario: Decision-tree based learning experiences
- InteractiveTimeline: Chronological exploration of events
- Flashcard: Digital flashcards with spaced repetition support
- InteractiveVideo: Videos with embedded questions and interactions
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class InteractiveContentType(Enum):
    """
    WHAT: Types of interactive content available
    WHERE: Used to categorize interactive elements
    WHY: Enables specialized handling for each content type
    """
    SIMULATION = "simulation"
    DRAG_DROP = "drag_drop"
    INTERACTIVE_DIAGRAM = "interactive_diagram"
    CODE_PLAYGROUND = "code_playground"
    BRANCHING_SCENARIO = "branching_scenario"
    INTERACTIVE_TIMELINE = "interactive_timeline"
    FLASHCARD = "flashcard"
    FLASHCARD_DECK = "flashcard_deck"
    INTERACTIVE_VIDEO = "interactive_video"
    HOTSPOT_IMAGE = "hotspot_image"
    SORTING_ACTIVITY = "sorting_activity"
    MATCHING_PAIRS = "matching_pairs"
    FILL_IN_BLANKS = "fill_in_blanks"
    VIRTUAL_LAB = "virtual_lab"


class InteractiveElementStatus(Enum):
    """
    WHAT: Status states for interactive elements
    WHERE: Used to track element lifecycle
    WHY: Enables workflow management for content review/publishing
    """
    DRAFT = "draft"
    UNDER_REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class DifficultyLevel(Enum):
    """
    WHAT: Difficulty levels for interactive content
    WHERE: Used to categorize challenge level
    WHY: Supports adaptive learning path selection
    """
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class InteractionEventType(Enum):
    """
    WHAT: Types of user interactions with content
    WHERE: Used for tracking and analytics
    WHY: Enables detailed analysis of learner engagement
    """
    STARTED = "started"
    INTERACTED = "interacted"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    RESET = "reset"
    HINT_REQUESTED = "hint_requested"
    ANSWER_SUBMITTED = "answer_submitted"
    FEEDBACK_VIEWED = "feedback_viewed"


class CodeLanguage(Enum):
    """
    WHAT: Programming languages supported in code playgrounds
    WHERE: Used for code playground configuration
    WHY: Enables appropriate syntax highlighting and execution
    """
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    BASH = "bash"


# =============================================================================
# Custom Exceptions
# =============================================================================

class InteractiveContentException(Exception):
    """
    WHAT: Base exception for interactive content operations
    WHERE: Used throughout interactive content handling
    WHY: Provides consistent error handling with context
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidInteractiveStateException(InteractiveContentException):
    """
    WHAT: Exception for invalid state transitions
    WHERE: Raised when attempting invalid status changes
    WHY: Enforces valid workflow state machine transitions
    """
    pass


class InteractiveContentValidationException(InteractiveContentException):
    """
    WHAT: Exception for content validation failures
    WHERE: Raised when content doesn't meet requirements
    WHY: Ensures content integrity before publishing
    """
    pass


class InteractionLimitExceededException(InteractiveContentException):
    """
    WHAT: Exception when interaction limits are reached
    WHERE: Raised when user exceeds allowed attempts
    WHY: Enforces fair usage and prevents abuse
    """
    pass


class UnsupportedLanguageException(InteractiveContentException):
    """
    WHAT: Exception for unsupported programming languages
    WHERE: Raised in code playground operations
    WHY: Prevents runtime errors from unsupported languages
    """
    pass


class BranchNotFoundException(InteractiveContentException):
    """
    WHAT: Exception when a scenario branch is not found
    WHERE: Raised in branching scenario navigation
    WHY: Ensures scenario integrity during execution
    """
    pass


class HotspotNotFoundException(InteractiveContentException):
    """
    WHAT: Exception when a hotspot is not found
    WHERE: Raised in interactive diagram operations
    WHY: Ensures diagram integrity during interactions
    """
    pass


# =============================================================================
# Domain Entities
# =============================================================================

@dataclass
class InteractiveElement:
    """
    WHAT: Base entity for all interactive content elements
    WHERE: Used as foundation for all interactive types
    WHY: Provides common attributes and behaviors for interactive content

    This entity tracks:
    - Basic identification and metadata
    - Status and versioning information
    - Accessibility and difficulty settings
    - Usage analytics and engagement metrics
    """
    id: UUID
    title: str
    description: str
    content_type: InteractiveContentType
    course_id: UUID
    module_id: Optional[UUID] = None
    lesson_id: Optional[UUID] = None
    creator_id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Status and versioning
    status: InteractiveElementStatus = InteractiveElementStatus.DRAFT
    version: int = 1

    # Learning attributes
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_duration_minutes: int = 10
    learning_objectives: List[str] = field(default_factory=list)
    prerequisites: List[UUID] = field(default_factory=list)

    # Engagement settings
    max_attempts: int = 0  # 0 = unlimited
    hints_enabled: bool = True
    feedback_immediate: bool = True
    allow_skip: bool = True
    points_value: int = 10

    # Accessibility
    accessibility_description: str = ""
    screen_reader_text: str = ""
    keyboard_navigable: bool = True
    high_contrast_available: bool = False

    # Analytics
    total_attempts: int = 0
    total_completions: int = 0
    avg_completion_time_seconds: float = 0.0
    avg_score: float = 0.0
    engagement_score: float = 0.0

    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_properties: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    def submit_for_review(self) -> None:
        """
        WHAT: Submits element for review
        WHERE: Called when author completes draft
        WHY: Initiates review workflow for quality assurance

        Raises:
            InvalidInteractiveStateException: If not in draft status
        """
        if self.status != InteractiveElementStatus.DRAFT:
            raise InvalidInteractiveStateException(
                f"Cannot submit for review from {self.status.value} status",
                {"current_status": self.status.value, "required_status": "draft"}
            )
        self.status = InteractiveElementStatus.UNDER_REVIEW
        self.updated_at = datetime.utcnow()

    def approve(self) -> None:
        """
        WHAT: Approves element after review
        WHERE: Called by reviewer after quality check
        WHY: Marks content as ready for publishing

        Raises:
            InvalidInteractiveStateException: If not under review
        """
        if self.status != InteractiveElementStatus.UNDER_REVIEW:
            raise InvalidInteractiveStateException(
                f"Cannot approve from {self.status.value} status",
                {"current_status": self.status.value, "required_status": "review"}
            )
        self.status = InteractiveElementStatus.APPROVED
        self.updated_at = datetime.utcnow()

    def publish(self) -> None:
        """
        WHAT: Publishes approved element
        WHERE: Called when content is made available to students
        WHY: Makes content accessible in courses

        Raises:
            InvalidInteractiveStateException: If not approved
        """
        if self.status != InteractiveElementStatus.APPROVED:
            raise InvalidInteractiveStateException(
                f"Cannot publish from {self.status.value} status",
                {"current_status": self.status.value, "required_status": "approved"}
            )
        self.status = InteractiveElementStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """
        WHAT: Archives the element
        WHERE: Called when content is retired
        WHY: Preserves history while hiding from active use
        """
        self.status = InteractiveElementStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def record_attempt(self, completed: bool, score: float, time_seconds: float) -> None:
        """
        WHAT: Records a user interaction attempt
        WHERE: Called after each user engagement
        WHY: Updates analytics for content effectiveness tracking

        Args:
            completed: Whether user completed the interaction
            score: Score achieved (0-100)
            time_seconds: Time spent on interaction
        """
        self.total_attempts += 1
        if completed:
            self.total_completions += 1

        # Update average score using incremental formula
        old_weight = (self.total_attempts - 1) / self.total_attempts
        new_weight = 1 / self.total_attempts
        self.avg_score = self.avg_score * old_weight + score * new_weight

        # Update average completion time
        self.avg_completion_time_seconds = (
            self.avg_completion_time_seconds * old_weight + time_seconds * new_weight
        )

        # Recalculate engagement score
        self._calculate_engagement_score()
        self.updated_at = datetime.utcnow()

    def _calculate_engagement_score(self) -> None:
        """
        WHAT: Calculates overall engagement score
        WHERE: Called after recording attempts
        WHY: Provides metric for content effectiveness
        """
        if self.total_attempts == 0:
            self.engagement_score = 0.0
            return

        completion_rate = (self.total_completions / self.total_attempts) * 100

        # Weighted formula: 40% completion rate + 30% avg score + 30% time efficiency
        time_efficiency = min(
            100,
            (self.estimated_duration_minutes * 60 / max(self.avg_completion_time_seconds, 1)) * 100
        )

        self.engagement_score = (
            completion_rate * 0.4 +
            self.avg_score * 0.3 +
            time_efficiency * 0.3
        )

    def get_completion_rate(self) -> float:
        """
        WHAT: Calculates completion rate percentage
        WHERE: Used for analytics and reporting
        WHY: Key metric for content effectiveness

        Returns:
            Completion rate as percentage (0-100)
        """
        if self.total_attempts == 0:
            return 0.0
        return (self.total_completions / self.total_attempts) * 100

    def create_new_version(self) -> 'InteractiveElement':
        """
        WHAT: Creates a new version of this element
        WHERE: Called when updating published content
        WHY: Preserves version history while allowing updates

        Returns:
            New InteractiveElement instance as draft
        """
        new_element = InteractiveElement(
            id=uuid4(),
            title=self.title,
            description=self.description,
            content_type=self.content_type,
            course_id=self.course_id,
            module_id=self.module_id,
            lesson_id=self.lesson_id,
            creator_id=self.creator_id,
            organization_id=self.organization_id,
            status=InteractiveElementStatus.DRAFT,
            version=self.version + 1,
            difficulty_level=self.difficulty_level,
            estimated_duration_minutes=self.estimated_duration_minutes,
            learning_objectives=self.learning_objectives.copy(),
            prerequisites=self.prerequisites.copy(),
            max_attempts=self.max_attempts,
            hints_enabled=self.hints_enabled,
            feedback_immediate=self.feedback_immediate,
            allow_skip=self.allow_skip,
            points_value=self.points_value,
            accessibility_description=self.accessibility_description,
            screen_reader_text=self.screen_reader_text,
            keyboard_navigable=self.keyboard_navigable,
            high_contrast_available=self.high_contrast_available,
            tags=self.tags.copy(),
            custom_properties=self.custom_properties.copy()
        )
        return new_element


@dataclass
class Simulation:
    """
    WHAT: Virtual simulation with configurable parameters
    WHERE: Used for hands-on experiential learning
    WHY: Provides safe environment to practice real-world scenarios

    Features:
    - Configurable initial state and parameters
    - Step-by-step guided mode or free exploration
    - State saving and scenario branching
    - Performance metrics and feedback
    """
    id: UUID
    element_id: UUID  # Reference to InteractiveElement
    name: str
    scenario_description: str

    # Configuration
    initial_state: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_outcomes: List[Dict[str, Any]] = field(default_factory=list)

    # Execution settings
    simulation_type: str = "guided"  # guided, sandbox, challenge
    time_limit_seconds: int = 0  # 0 = unlimited
    max_steps: int = 0  # 0 = unlimited
    allow_reset: bool = True
    save_checkpoints: bool = True

    # Guided mode settings
    guided_steps: List[Dict[str, Any]] = field(default_factory=list)
    show_hints: bool = True
    hint_penalty_percent: int = 10

    # Scoring
    scoring_rubric: Dict[str, Any] = field(default_factory=dict)
    passing_score: int = 70
    partial_credit: bool = True

    # State
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def validate_outcome(self, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        WHAT: Validates user's final state against expected outcomes
        WHERE: Called when user completes simulation
        WHY: Determines success and calculates score

        Args:
            user_state: The final state achieved by the user

        Returns:
            Dict containing score, success status, and feedback
        """
        total_points = 0
        max_points = 0
        feedback = []

        for expected in self.expected_outcomes:
            key = expected.get("key")
            expected_value = expected.get("value")
            points = expected.get("points", 10)
            max_points += points

            if key in user_state:
                if user_state[key] == expected_value:
                    total_points += points
                    feedback.append({
                        "key": key,
                        "status": "correct",
                        "points": points
                    })
                elif self.partial_credit:
                    # Award partial credit for close answers
                    partial = self._calculate_partial_credit(
                        user_state[key], expected_value, points
                    )
                    total_points += partial
                    feedback.append({
                        "key": key,
                        "status": "partial",
                        "points": partial,
                        "max_points": points
                    })
                else:
                    feedback.append({
                        "key": key,
                        "status": "incorrect",
                        "points": 0
                    })
            else:
                feedback.append({
                    "key": key,
                    "status": "missing",
                    "points": 0
                })

        score = (total_points / max_points * 100) if max_points > 0 else 0

        return {
            "score": round(score, 2),
            "passed": score >= self.passing_score,
            "total_points": total_points,
            "max_points": max_points,
            "feedback": feedback
        }

    def _calculate_partial_credit(
        self, actual: Any, expected: Any, max_points: int
    ) -> int:
        """
        WHAT: Calculates partial credit for close answers
        WHERE: Used in validation when partial credit enabled
        WHY: Rewards students for getting close to correct answer

        Args:
            actual: User's answer
            expected: Expected answer
            max_points: Maximum points for this outcome

        Returns:
            Partial points awarded
        """
        # Numeric comparison with tolerance
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            difference = abs(actual - expected)
            tolerance = abs(expected) * 0.1 if expected != 0 else 0.1
            if difference <= tolerance:
                return int(max_points * 0.75)
            elif difference <= tolerance * 2:
                return int(max_points * 0.5)
            elif difference <= tolerance * 5:
                return int(max_points * 0.25)

        return 0

    def get_current_step(self, step_index: int) -> Optional[Dict[str, Any]]:
        """
        WHAT: Gets guided step by index
        WHERE: Used in guided simulation mode
        WHY: Provides step-by-step instruction delivery

        Args:
            step_index: Index of step to retrieve

        Returns:
            Step data or None if invalid index
        """
        if 0 <= step_index < len(self.guided_steps):
            return self.guided_steps[step_index]
        return None


@dataclass
class DragDropItem:
    """
    WHAT: Individual item in a drag-drop activity
    WHERE: Used as component of DragDropActivity
    WHY: Represents draggable content with zone mapping
    """
    id: UUID
    content: str
    content_type: str = "text"  # text, image, html
    image_url: Optional[str] = None
    correct_zone_ids: List[UUID] = field(default_factory=list)
    feedback_correct: str = ""
    feedback_incorrect: str = ""
    points: int = 10
    order_index: Optional[int] = None  # For ordering activities


@dataclass
class DropZone:
    """
    WHAT: Drop target zone for drag-drop activities
    WHERE: Used as component of DragDropActivity
    WHY: Defines valid drop targets and their properties
    """
    id: UUID
    label: str
    description: str = ""
    accepts_multiple: bool = False
    max_items: int = 1
    position: Dict[str, int] = field(default_factory=dict)  # x, y, width, height
    style: Dict[str, str] = field(default_factory=dict)


@dataclass
class DragDropActivity:
    """
    WHAT: Interactive drag-and-drop activity
    WHERE: Used for categorization, matching, and ordering tasks
    WHY: Engages learners through hands-on interaction

    Supports:
    - Categorization (items to categories)
    - Matching (pairs)
    - Ordering (sequence)
    - Sorting (groups)
    """
    id: UUID
    element_id: UUID  # Reference to InteractiveElement
    activity_type: str  # categorize, match, order, sort
    instructions: str

    # Items and zones
    items: List[DragDropItem] = field(default_factory=list)
    zones: List[DropZone] = field(default_factory=list)

    # Behavior settings
    shuffle_items: bool = True
    shuffle_zones: bool = False
    show_item_count_per_zone: bool = True
    allow_reorder: bool = True
    snap_to_zone: bool = True

    # Feedback settings
    show_correct_placement: bool = True
    show_feedback_on_drop: bool = False
    show_feedback_on_submit: bool = True

    # Scoring
    partial_credit: bool = True
    deduct_for_incorrect: bool = False
    deduction_percent: int = 10

    # Visual settings
    item_style: Dict[str, str] = field(default_factory=dict)
    zone_style: Dict[str, str] = field(default_factory=dict)

    # State
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def evaluate_submission(
        self, placements: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates user's drag-drop submission
        WHERE: Called when user submits their placements
        WHY: Determines correctness and calculates score

        Args:
            placements: Dict mapping zone_id to list of item_ids

        Returns:
            Evaluation result with score and feedback
        """
        total_points = 0
        max_points = 0
        item_feedback = []

        for item in self.items:
            max_points += item.points
            item_placed_correctly = False
            item_zone = None

            # Find where this item was placed
            for zone_id_str, item_ids in placements.items():
                if str(item.id) in item_ids:
                    item_zone = zone_id_str
                    # Check if this zone is correct
                    correct_zone_ids = [str(z) for z in item.correct_zone_ids]
                    if zone_id_str in correct_zone_ids:
                        item_placed_correctly = True
                        total_points += item.points
                    elif self.deduct_for_incorrect:
                        total_points -= int(item.points * self.deduction_percent / 100)
                    break

            item_feedback.append({
                "item_id": str(item.id),
                "correct": item_placed_correctly,
                "placed_zone": item_zone,
                "correct_zones": [str(z) for z in item.correct_zone_ids],
                "feedback": item.feedback_correct if item_placed_correctly else item.feedback_incorrect,
                "points_earned": item.points if item_placed_correctly else 0
            })

        # Ensure score doesn't go negative
        total_points = max(0, total_points)
        score = (total_points / max_points * 100) if max_points > 0 else 0

        return {
            "score": round(score, 2),
            "total_points": total_points,
            "max_points": max_points,
            "items_correct": sum(1 for f in item_feedback if f["correct"]),
            "items_total": len(self.items),
            "feedback": item_feedback
        }

    def add_item(self, item: DragDropItem) -> None:
        """
        WHAT: Adds a new draggable item
        WHERE: Called during activity construction
        WHY: Enables building activity with multiple items

        Args:
            item: DragDropItem to add
        """
        self.items.append(item)
        self.updated_at = datetime.utcnow()

    def add_zone(self, zone: DropZone) -> None:
        """
        WHAT: Adds a new drop zone
        WHERE: Called during activity construction
        WHY: Enables building activity with multiple zones

        Args:
            zone: DropZone to add
        """
        self.zones.append(zone)
        self.updated_at = datetime.utcnow()


@dataclass
class Hotspot:
    """
    WHAT: Clickable region on an interactive diagram
    WHERE: Used as component of InteractiveDiagram
    WHY: Defines interactive areas with associated content
    """
    id: UUID
    label: str
    description: str
    shape: str = "circle"  # circle, rectangle, polygon
    coordinates: Dict[str, Any] = field(default_factory=dict)  # shape-specific coords
    popup_content: str = ""
    popup_media_url: Optional[str] = None
    linked_content_id: Optional[UUID] = None  # Link to other content
    is_quiz_point: bool = False
    quiz_question: Optional[str] = None
    quiz_answer: Optional[str] = None
    style: Dict[str, str] = field(default_factory=dict)
    order_index: int = 0


@dataclass
class DiagramLayer:
    """
    WHAT: Visual layer in an interactive diagram
    WHERE: Used as component of InteractiveDiagram
    WHY: Enables toggling between different views/states
    """
    id: UUID
    name: str
    description: str = ""
    image_url: str = ""
    is_visible: bool = True
    is_base_layer: bool = False
    opacity: float = 1.0
    order_index: int = 0


@dataclass
class InteractiveDiagram:
    """
    WHAT: Interactive image/diagram with hotspots and layers
    WHERE: Used for visual learning with clickable regions
    WHY: Enables exploration of complex visuals with guided discovery

    Features:
    - Multiple layers (toggleable views)
    - Clickable hotspots with popups
    - Zoom and pan support
    - Guided tour mode
    """
    id: UUID
    element_id: UUID  # Reference to InteractiveElement
    title: str
    base_image_url: str

    # Layers and hotspots
    layers: List[DiagramLayer] = field(default_factory=list)
    hotspots: List[Hotspot] = field(default_factory=list)

    # Interaction settings
    zoom_enabled: bool = True
    pan_enabled: bool = True
    min_zoom: float = 0.5
    max_zoom: float = 3.0

    # Guided tour
    guided_tour_enabled: bool = True
    tour_hotspot_order: List[UUID] = field(default_factory=list)
    tour_auto_advance_seconds: int = 0  # 0 = manual advance

    # Quiz mode settings
    quiz_mode_enabled: bool = False
    quiz_passing_score: int = 70

    # Visual settings
    highlight_on_hover: bool = True
    show_labels: bool = True
    label_position: str = "bottom"  # top, bottom, left, right

    # State
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_hotspot(self, hotspot: Hotspot) -> None:
        """
        WHAT: Adds a hotspot to the diagram
        WHERE: Called during diagram construction
        WHY: Enables building diagram with interactive regions

        Args:
            hotspot: Hotspot to add
        """
        self.hotspots.append(hotspot)
        self.updated_at = datetime.utcnow()

    def add_layer(self, layer: DiagramLayer) -> None:
        """
        WHAT: Adds a layer to the diagram
        WHERE: Called during diagram construction
        WHY: Enables multi-view diagrams

        Args:
            layer: DiagramLayer to add
        """
        self.layers.append(layer)
        self.updated_at = datetime.utcnow()

    def get_hotspot(self, hotspot_id: UUID) -> Hotspot:
        """
        WHAT: Retrieves a hotspot by ID
        WHERE: Called when user clicks a hotspot
        WHY: Provides hotspot data for display

        Args:
            hotspot_id: ID of hotspot to retrieve

        Returns:
            Hotspot instance

        Raises:
            HotspotNotFoundException: If hotspot not found
        """
        for hotspot in self.hotspots:
            if hotspot.id == hotspot_id:
                return hotspot
        raise HotspotNotFoundException(
            f"Hotspot {hotspot_id} not found",
            {"diagram_id": str(self.id), "hotspot_id": str(hotspot_id)}
        )

    def get_quiz_hotspots(self) -> List[Hotspot]:
        """
        WHAT: Gets all quiz-enabled hotspots
        WHERE: Used when entering quiz mode
        WHY: Identifies hotspots with quiz questions

        Returns:
            List of hotspots with quiz questions
        """
        return [h for h in self.hotspots if h.is_quiz_point and h.quiz_question]

    def evaluate_quiz(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """
        WHAT: Evaluates quiz answers for hotspot quiz
        WHERE: Called when user submits quiz answers
        WHY: Scores the diagram exploration quiz

        Args:
            answers: Dict mapping hotspot_id to user's answer

        Returns:
            Quiz result with score and feedback
        """
        quiz_hotspots = self.get_quiz_hotspots()
        if not quiz_hotspots:
            return {"score": 0, "message": "No quiz questions available"}

        correct_count = 0
        feedback = []

        for hotspot in quiz_hotspots:
            user_answer = answers.get(str(hotspot.id), "").strip().lower()
            correct_answer = (hotspot.quiz_answer or "").strip().lower()
            is_correct = user_answer == correct_answer

            if is_correct:
                correct_count += 1

            feedback.append({
                "hotspot_id": str(hotspot.id),
                "label": hotspot.label,
                "correct": is_correct,
                "user_answer": answers.get(str(hotspot.id), ""),
                "correct_answer": hotspot.quiz_answer if not is_correct else None
            })

        score = (correct_count / len(quiz_hotspots)) * 100

        return {
            "score": round(score, 2),
            "passed": score >= self.quiz_passing_score,
            "correct_count": correct_count,
            "total_questions": len(quiz_hotspots),
            "feedback": feedback
        }


@dataclass
class CodePlayground:
    """
    WHAT: In-browser code editing and execution environment
    WHERE: Used for hands-on coding practice
    WHY: Enables learners to write and test code without local setup

    Features:
    - Multiple language support
    - Starter code templates
    - Test case validation
    - Output comparison
    - Performance metrics
    """
    id: UUID
    element_id: UUID  # Reference to InteractiveElement
    title: str
    instructions: str

    # Language settings
    language: CodeLanguage = CodeLanguage.PYTHON
    language_version: str = "3.10"

    # Code templates
    starter_code: str = ""
    solution_code: str = ""
    test_code: str = ""
    hidden_test_code: str = ""  # Hidden tests for grading

    # Execution settings
    timeout_seconds: int = 30
    memory_limit_mb: int = 128
    allowed_imports: List[str] = field(default_factory=list)
    blocked_imports: List[str] = field(default_factory=list)

    # Test cases
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    # Format: {"name": "Test 1", "input": "...", "expected_output": "...", "points": 10}

    # Behavior settings
    show_expected_output: bool = False
    show_test_cases: bool = True
    allow_solution_view: bool = False
    auto_run_on_change: bool = False

    # Scoring
    passing_score: int = 70
    partial_credit: bool = True

    # State
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def validate_language(self, language: str) -> bool:
        """
        WHAT: Validates if a language is supported
        WHERE: Called when setting playground language
        WHY: Prevents configuration errors

        Args:
            language: Language string to validate

        Returns:
            True if language is supported
        """
        try:
            CodeLanguage(language)
            return True
        except ValueError:
            return False

    def add_test_case(
        self,
        name: str,
        input_data: str,
        expected_output: str,
        points: int = 10,
        is_hidden: bool = False
    ) -> None:
        """
        WHAT: Adds a test case for code validation
        WHERE: Called during playground construction
        WHY: Builds test suite for automated grading

        Args:
            name: Test case name
            input_data: Input to provide to code
            expected_output: Expected output
            points: Points for passing this test
            is_hidden: Whether test is hidden from students
        """
        self.test_cases.append({
            "id": str(uuid4()),
            "name": name,
            "input": input_data,
            "expected_output": expected_output,
            "points": points,
            "is_hidden": is_hidden
        })
        self.updated_at = datetime.utcnow()

    def evaluate_output(
        self,
        outputs: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates code outputs against test cases
        WHERE: Called after code execution
        WHY: Determines score based on test results

        Args:
            outputs: List of dicts with 'test_id' and 'output'

        Returns:
            Evaluation result with score and feedback
        """
        total_points = 0
        earned_points = 0
        results = []

        for test in self.test_cases:
            total_points += test["points"]
            test_output = None

            # Find matching output
            for output in outputs:
                if output.get("test_id") == test["id"]:
                    test_output = output.get("output", "").strip()
                    break

            expected = test["expected_output"].strip()
            passed = test_output == expected

            if passed:
                earned_points += test["points"]
            elif self.partial_credit and test_output:
                # Award partial credit for partial match
                similarity = self._calculate_output_similarity(test_output, expected)
                partial = int(test["points"] * similarity)
                earned_points += partial

            results.append({
                "test_id": test["id"],
                "name": test["name"],
                "passed": passed,
                "points_earned": test["points"] if passed else 0,
                "points_possible": test["points"],
                "is_hidden": test.get("is_hidden", False),
                "actual_output": test_output if not test.get("is_hidden") else None,
                "expected_output": expected if self.show_expected_output and not test.get("is_hidden") else None
            })

        score = (earned_points / total_points * 100) if total_points > 0 else 0

        return {
            "score": round(score, 2),
            "passed": score >= self.passing_score,
            "earned_points": earned_points,
            "total_points": total_points,
            "tests_passed": sum(1 for r in results if r["passed"]),
            "tests_total": len(results),
            "results": results
        }

    def _calculate_output_similarity(self, actual: str, expected: str) -> float:
        """
        WHAT: Calculates similarity between actual and expected output
        WHERE: Used for partial credit calculation
        WHY: Rewards students for close answers

        Args:
            actual: Actual output
            expected: Expected output

        Returns:
            Similarity ratio (0-1)
        """
        if not actual or not expected:
            return 0.0

        # Simple line-by-line comparison
        actual_lines = actual.split('\n')
        expected_lines = expected.split('\n')

        if not expected_lines:
            return 0.0

        matching_lines = sum(
            1 for a, e in zip(actual_lines, expected_lines)
            if a.strip() == e.strip()
        )

        return matching_lines / len(expected_lines)


@dataclass
class ScenarioBranch:
    """
    WHAT: A branch/node in a branching scenario
    WHERE: Used as component of BranchingScenario
    WHY: Represents a decision point or outcome
    """
    id: UUID
    content: str
    content_type: str = "text"  # text, image, video, html
    media_url: Optional[str] = None

    # Options leading from this branch
    options: List[Dict[str, Any]] = field(default_factory=list)
    # Format: {"text": "...", "next_branch_id": "...", "feedback": "...", "points": 10}

    # Branch properties
    is_start: bool = False
    is_end: bool = False
    is_success_end: bool = False
    is_failure_end: bool = False
    points_value: int = 0

    # Feedback
    branch_feedback: str = ""

    # Display settings
    style: Dict[str, str] = field(default_factory=dict)


@dataclass
class BranchingScenario:
    """
    WHAT: Decision-tree based interactive learning scenario
    WHERE: Used for situational learning and soft skills training
    WHY: Enables learners to experience consequences of decisions

    Features:
    - Multiple paths through scenario
    - Branching outcomes based on choices
    - Path tracking and analytics
    - Multiple success/failure endings
    """
    id: UUID
    element_id: UUID  # Reference to InteractiveElement
    title: str
    introduction: str

    # Branches
    branches: List[ScenarioBranch] = field(default_factory=list)
    start_branch_id: Optional[UUID] = None

    # Scoring
    max_score: int = 100
    passing_score: int = 70
    track_path: bool = True

    # Behavior settings
    allow_backtrack: bool = False
    show_path_on_complete: bool = True
    show_optimal_path: bool = False

    # Visual settings
    visual_style: str = "cards"  # cards, chat, story
    show_progress: bool = True

    # State
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_branch(self, branch: ScenarioBranch) -> None:
        """
        WHAT: Adds a branch to the scenario
        WHERE: Called during scenario construction
        WHY: Builds the decision tree structure

        Args:
            branch: ScenarioBranch to add
        """
        self.branches.append(branch)
        if branch.is_start:
            self.start_branch_id = branch.id
        self.updated_at = datetime.utcnow()

    def get_branch(self, branch_id: UUID) -> ScenarioBranch:
        """
        WHAT: Retrieves a branch by ID
        WHERE: Called during scenario navigation
        WHY: Provides branch data for display

        Args:
            branch_id: ID of branch to retrieve

        Returns:
            ScenarioBranch instance

        Raises:
            BranchNotFoundException: If branch not found
        """
        for branch in self.branches:
            if branch.id == branch_id:
                return branch
        raise BranchNotFoundException(
            f"Branch {branch_id} not found",
            {"scenario_id": str(self.id), "branch_id": str(branch_id)}
        )

    def get_start_branch(self) -> ScenarioBranch:
        """
        WHAT: Gets the starting branch of the scenario
        WHERE: Called when user begins scenario
        WHY: Provides entry point for navigation

        Returns:
            Starting ScenarioBranch

        Raises:
            BranchNotFoundException: If no start branch defined
        """
        if self.start_branch_id:
            return self.get_branch(self.start_branch_id)

        # Find branch marked as start
        for branch in self.branches:
            if branch.is_start:
                return branch

        raise BranchNotFoundException(
            "No start branch defined for scenario",
            {"scenario_id": str(self.id)}
        )

    def evaluate_path(
        self,
        path: List[UUID],
        choices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates the path taken through the scenario
        WHERE: Called when user completes scenario
        WHY: Calculates score and provides feedback

        Args:
            path: List of branch IDs visited
            choices: List of choices made at each branch

        Returns:
            Evaluation result with score and feedback
        """
        total_points = 0
        feedback = []
        final_branch = None

        for branch_id in path:
            try:
                branch = self.get_branch(branch_id)
                total_points += branch.points_value
                final_branch = branch

                if branch.branch_feedback:
                    feedback.append({
                        "branch_id": str(branch_id),
                        "feedback": branch.branch_feedback
                    })
            except BranchNotFoundException:
                continue

        # Determine outcome
        outcome = "completed"
        if final_branch:
            if final_branch.is_success_end:
                outcome = "success"
            elif final_branch.is_failure_end:
                outcome = "failure"

        score = min(100, (total_points / self.max_score * 100)) if self.max_score > 0 else 0

        return {
            "score": round(score, 2),
            "passed": score >= self.passing_score,
            "outcome": outcome,
            "total_points": total_points,
            "max_score": self.max_score,
            "branches_visited": len(path),
            "feedback": feedback,
            "path": [str(b) for b in path] if self.track_path else []
        }


@dataclass
class TimelineEvent:
    """
    WHAT: An event on an interactive timeline
    WHERE: Used as component of InteractiveTimeline
    WHY: Represents a point in time with associated content
    """
    id: UUID
    title: str
    description: str
    date: datetime
    date_display: str = ""  # Formatted display string

    # Content
    content: str = ""
    content_type: str = "text"  # text, image, video, html
    media_url: Optional[str] = None

    # Properties
    category: str = ""
    importance: int = 1  # 1-5 scale
    is_milestone: bool = False

    # Linked content
    linked_content_ids: List[UUID] = field(default_factory=list)

    # Visual
    icon: str = ""
    color: str = ""
    style: Dict[str, str] = field(default_factory=dict)


@dataclass
class InteractiveTimeline:
    """
    WHAT: Interactive chronological timeline
    WHERE: Used for historical, process, or narrative learning
    WHY: Enables temporal exploration of events and concepts

    Features:
    - Zoomable time scale
    - Event filtering by category
    - Milestone highlighting
    - Event comparison mode
    """
    id: UUID
    element_id: UUID  # Reference to InteractiveElement
    title: str
    description: str

    # Events
    events: List[TimelineEvent] = field(default_factory=list)

    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_scale: str = "years"  # years, months, days, hours

    # Categories
    categories: List[Dict[str, str]] = field(default_factory=list)
    # Format: {"name": "...", "color": "...", "icon": "..."}

    # Interaction settings
    zoom_enabled: bool = True
    filter_by_category: bool = True
    show_milestones_only: bool = False
    comparison_mode: bool = False

    # Visual settings
    orientation: str = "horizontal"  # horizontal, vertical
    event_density: str = "normal"  # compact, normal, expanded
    show_event_images: bool = True

    # State
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_event(self, event: TimelineEvent) -> None:
        """
        WHAT: Adds an event to the timeline
        WHERE: Called during timeline construction
        WHY: Builds the timeline with chronological events

        Args:
            event: TimelineEvent to add
        """
        self.events.append(event)
        # Sort events by date
        self.events.sort(key=lambda e: e.date)

        # Update date range
        if not self.start_date or event.date < self.start_date:
            self.start_date = event.date
        if not self.end_date or event.date > self.end_date:
            self.end_date = event.date

        self.updated_at = datetime.utcnow()

    def get_events_by_category(self, category: str) -> List[TimelineEvent]:
        """
        WHAT: Filters events by category
        WHERE: Called when user filters timeline
        WHY: Enables focused view of specific event types

        Args:
            category: Category to filter by

        Returns:
            List of events in the category
        """
        return [e for e in self.events if e.category == category]

    def get_milestones(self) -> List[TimelineEvent]:
        """
        WHAT: Gets all milestone events
        WHERE: Called when showing milestones only
        WHY: Highlights key events on timeline

        Returns:
            List of milestone events
        """
        return [e for e in self.events if e.is_milestone]

    def get_events_in_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[TimelineEvent]:
        """
        WHAT: Gets events within a date range
        WHERE: Called when user zooms to time range
        WHY: Provides filtered view for zoomed timeline

        Args:
            start: Start of range
            end: End of range

        Returns:
            List of events in range
        """
        return [e for e in self.events if start <= e.date <= end]


@dataclass
class Flashcard:
    """
    WHAT: Individual flashcard with front and back content
    WHERE: Used as component of FlashcardDeck
    WHY: Represents single learning item for memorization
    """
    id: UUID
    front_content: str
    back_content: str
    front_content_type: str = "text"  # text, image, html, audio
    back_content_type: str = "text"
    front_media_url: Optional[str] = None
    back_media_url: Optional[str] = None

    # Spaced repetition data
    difficulty: float = 2.5  # Initial easiness factor
    interval_days: int = 1
    repetitions: int = 0
    next_review: Optional[datetime] = None
    last_reviewed: Optional[datetime] = None

    # Learning data
    times_correct: int = 0
    times_incorrect: int = 0

    # Tags
    tags: List[str] = field(default_factory=list)

    def update_spaced_repetition(self, quality: int) -> None:
        """
        WHAT: Updates spaced repetition parameters based on response quality
        WHERE: Called after user reviews card
        WHY: Implements SM-2 algorithm for optimal review scheduling

        Args:
            quality: Response quality (0-5 scale)
                0: Complete blackout
                1: Incorrect, remembered on seeing answer
                2: Incorrect, easy to recall once seen
                3: Correct, with difficulty
                4: Correct, with some hesitation
                5: Perfect response
        """
        # Update easiness factor (EF)
        self.difficulty = max(
            1.3,
            self.difficulty + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        )

        if quality < 3:
            # Reset repetitions on failure
            self.repetitions = 0
            self.interval_days = 1
            self.times_incorrect += 1
        else:
            self.times_correct += 1
            if self.repetitions == 0:
                self.interval_days = 1
            elif self.repetitions == 1:
                self.interval_days = 6
            else:
                self.interval_days = int(self.interval_days * self.difficulty)
            self.repetitions += 1

        self.last_reviewed = datetime.utcnow()
        self.next_review = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # Add interval days
        from datetime import timedelta
        self.next_review = self.next_review + timedelta(days=self.interval_days)


@dataclass
class FlashcardDeck:
    """
    WHAT: Collection of flashcards for studying
    WHERE: Used for memorization-based learning
    WHY: Enables spaced repetition learning with organized card sets

    Features:
    - Spaced repetition scheduling
    - Progress tracking
    - Study session management
    - Performance analytics
    """
    id: UUID
    element_id: UUID  # Reference to InteractiveElement
    name: str
    description: str

    # Cards
    cards: List[Flashcard] = field(default_factory=list)

    # Study settings
    new_cards_per_day: int = 20
    reviews_per_day: int = 100
    shuffle_new: bool = True
    shuffle_review: bool = True

    # Display settings
    show_remaining: bool = True
    flip_animation: bool = True
    auto_flip_seconds: int = 0  # 0 = manual flip

    # Progress
    total_reviews: int = 0
    correct_reviews: int = 0
    streak_days: int = 0
    last_study_date: Optional[datetime] = None

    # State
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_card(self, card: Flashcard) -> None:
        """
        WHAT: Adds a flashcard to the deck
        WHERE: Called during deck construction
        WHY: Builds the card collection

        Args:
            card: Flashcard to add
        """
        self.cards.append(card)
        self.updated_at = datetime.utcnow()

    def get_cards_for_review(self) -> List[Flashcard]:
        """
        WHAT: Gets cards due for review
        WHERE: Called when starting study session
        WHY: Provides cards based on spaced repetition schedule

        Returns:
            List of cards due for review
        """
        now = datetime.utcnow()
        due_cards = [
            c for c in self.cards
            if c.next_review and c.next_review <= now
        ]

        if self.shuffle_review:
            import random
            random.shuffle(due_cards)

        return due_cards[:self.reviews_per_day]

    def get_new_cards(self) -> List[Flashcard]:
        """
        WHAT: Gets new cards not yet studied
        WHERE: Called when starting study session
        WHY: Introduces new material at controlled pace

        Returns:
            List of new cards
        """
        new_cards = [c for c in self.cards if c.repetitions == 0]

        if self.shuffle_new:
            import random
            random.shuffle(new_cards)

        return new_cards[:self.new_cards_per_day]

    def record_review(self, card_id: UUID, quality: int) -> None:
        """
        WHAT: Records a card review result
        WHERE: Called after user reviews a card
        WHY: Updates deck and card statistics

        Args:
            card_id: ID of reviewed card
            quality: Response quality (0-5)
        """
        for card in self.cards:
            if card.id == card_id:
                card.update_spaced_repetition(quality)
                break

        self.total_reviews += 1
        if quality >= 3:
            self.correct_reviews += 1

        # Update streak
        now = datetime.utcnow().date()
        if self.last_study_date:
            last_date = self.last_study_date.date()
            if (now - last_date).days == 1:
                self.streak_days += 1
            elif (now - last_date).days > 1:
                self.streak_days = 1
        else:
            self.streak_days = 1

        self.last_study_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_retention_rate(self) -> float:
        """
        WHAT: Calculates overall retention rate
        WHERE: Used for progress analytics
        WHY: Measures learning effectiveness

        Returns:
            Retention rate as percentage
        """
        if self.total_reviews == 0:
            return 0.0
        return (self.correct_reviews / self.total_reviews) * 100

    def get_mastery_level(self) -> Dict[str, int]:
        """
        WHAT: Calculates mastery level distribution
        WHERE: Used for progress visualization
        WHY: Shows card distribution by learning stage

        Returns:
            Dict with counts for each mastery level
        """
        levels = {
            "new": 0,
            "learning": 0,
            "young": 0,
            "mature": 0
        }

        for card in self.cards:
            if card.repetitions == 0:
                levels["new"] += 1
            elif card.interval_days < 7:
                levels["learning"] += 1
            elif card.interval_days < 21:
                levels["young"] += 1
            else:
                levels["mature"] += 1

        return levels


@dataclass
class VideoInteraction:
    """
    WHAT: An interaction point within an interactive video
    WHERE: Used as component of InteractiveVideo
    WHY: Defines engagement points at specific timestamps
    """
    id: UUID
    timestamp_seconds: float
    interaction_type: str  # question, hotspot, branch, pause, note

    # Content
    title: str = ""
    content: str = ""
    media_url: Optional[str] = None

    # Question data (if type is question)
    question: Optional[str] = None
    options: List[Dict[str, Any]] = field(default_factory=list)
    correct_answer: Optional[str] = None
    explanation: str = ""
    points: int = 10

    # Behavior
    pause_video: bool = True
    required: bool = False
    skip_allowed: bool = True

    # Display
    duration_seconds: int = 0  # 0 = until dismissed
    position: Dict[str, Any] = field(default_factory=dict)  # x, y positioning
    style: Dict[str, str] = field(default_factory=dict)


@dataclass
class InteractiveVideo:
    """
    WHAT: Video content with embedded interactions
    WHERE: Used for active video-based learning
    WHY: Transforms passive video viewing into active engagement

    Features:
    - Embedded questions at timestamps
    - Clickable hotspots during playback
    - Branching paths based on choices
    - Chapter markers and navigation
    - Transcript synchronization
    """
    id: UUID
    element_id: UUID  # Reference to InteractiveElement
    title: str
    description: str

    # Video source
    video_url: str
    video_duration_seconds: float = 0.0
    thumbnail_url: Optional[str] = None

    # Interactions
    interactions: List[VideoInteraction] = field(default_factory=list)

    # Chapters
    chapters: List[Dict[str, Any]] = field(default_factory=list)
    # Format: {"title": "...", "start_seconds": 0, "end_seconds": 60}

    # Transcript
    transcript_url: Optional[str] = None
    captions_url: Optional[str] = None
    show_transcript: bool = True

    # Playback settings
    allow_skip_interactions: bool = False
    require_all_interactions: bool = False
    allow_playback_speed: bool = True
    allow_seek: bool = True

    # Completion criteria
    watch_percentage_required: int = 80
    interactions_percentage_required: int = 100
    passing_score: int = 70

    # State
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_interaction(self, interaction: VideoInteraction) -> None:
        """
        WHAT: Adds an interaction to the video
        WHERE: Called during video configuration
        WHY: Builds interactive layer over video

        Args:
            interaction: VideoInteraction to add
        """
        self.interactions.append(interaction)
        # Sort by timestamp
        self.interactions.sort(key=lambda i: i.timestamp_seconds)
        self.updated_at = datetime.utcnow()

    def add_chapter(
        self,
        title: str,
        start_seconds: float,
        end_seconds: float
    ) -> None:
        """
        WHAT: Adds a chapter marker to the video
        WHERE: Called during video configuration
        WHY: Enables navigation and organization

        Args:
            title: Chapter title
            start_seconds: Chapter start time
            end_seconds: Chapter end time
        """
        self.chapters.append({
            "id": str(uuid4()),
            "title": title,
            "start_seconds": start_seconds,
            "end_seconds": end_seconds
        })
        # Sort by start time
        self.chapters.sort(key=lambda c: c["start_seconds"])
        self.updated_at = datetime.utcnow()

    def get_interactions_in_range(
        self,
        start_seconds: float,
        end_seconds: float
    ) -> List[VideoInteraction]:
        """
        WHAT: Gets interactions within a time range
        WHERE: Called during video playback
        WHY: Triggers interactions at appropriate times

        Args:
            start_seconds: Range start
            end_seconds: Range end

        Returns:
            List of interactions in range
        """
        return [
            i for i in self.interactions
            if start_seconds <= i.timestamp_seconds <= end_seconds
        ]

    def evaluate_session(
        self,
        watch_time_seconds: float,
        interaction_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        WHAT: Evaluates a video viewing session
        WHERE: Called when user completes or leaves video
        WHY: Determines completion and score

        Args:
            watch_time_seconds: Total watch time
            interaction_responses: Dict mapping interaction_id to response

        Returns:
            Session evaluation result
        """
        # Calculate watch percentage
        watch_percentage = 0.0
        if self.video_duration_seconds > 0:
            watch_percentage = min(100, (watch_time_seconds / self.video_duration_seconds) * 100)

        # Evaluate interactions
        question_interactions = [
            i for i in self.interactions if i.interaction_type == "question"
        ]
        total_points = sum(i.points for i in question_interactions)
        earned_points = 0
        interaction_results = []

        for interaction in question_interactions:
            response = interaction_responses.get(str(interaction.id))
            is_correct = response == interaction.correct_answer

            if is_correct:
                earned_points += interaction.points

            interaction_results.append({
                "interaction_id": str(interaction.id),
                "timestamp": interaction.timestamp_seconds,
                "question": interaction.question,
                "correct": is_correct,
                "user_response": response,
                "correct_answer": interaction.correct_answer if not is_correct else None,
                "explanation": interaction.explanation if not is_correct else None,
                "points_earned": interaction.points if is_correct else 0
            })

        # Calculate completion
        interactions_completed = len(interaction_responses)
        interactions_total = len(question_interactions)
        interactions_percentage = (
            (interactions_completed / interactions_total * 100)
            if interactions_total > 0 else 100
        )

        # Determine if passed
        score = (earned_points / total_points * 100) if total_points > 0 else 100
        watch_passed = watch_percentage >= self.watch_percentage_required
        interactions_passed = interactions_percentage >= self.interactions_percentage_required
        score_passed = score >= self.passing_score

        return {
            "completed": watch_passed and interactions_passed and score_passed,
            "score": round(score, 2),
            "watch_percentage": round(watch_percentage, 2),
            "watch_passed": watch_passed,
            "interactions_completed": interactions_completed,
            "interactions_total": interactions_total,
            "interactions_passed": interactions_passed,
            "earned_points": earned_points,
            "total_points": total_points,
            "results": interaction_results
        }


@dataclass
class InteractionSession:
    """
    WHAT: Tracks a user's session with interactive content
    WHERE: Used for analytics and progress tracking
    WHY: Records user engagement for learning analytics

    This entity tracks:
    - Session timing and duration
    - Actions taken during session
    - Score and completion status
    - Hints used and attempts made
    """
    id: UUID
    element_id: UUID
    user_id: UUID

    # Session timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Progress
    status: str = "in_progress"  # in_progress, completed, abandoned
    completion_percentage: float = 0.0

    # Scoring
    score: float = 0.0
    max_score: float = 100.0
    passed: bool = False

    # Engagement
    attempts: int = 1
    hints_used: int = 0
    actions_count: int = 0

    # Data
    state_data: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    device_type: str = ""
    browser: str = ""

    def record_action(self, action_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        WHAT: Records a user action during session
        WHERE: Called throughout user interaction
        WHY: Enables detailed interaction analytics

        Args:
            action_type: Type of action performed
            data: Optional additional action data
        """
        self.actions.append({
            "type": action_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        })
        self.actions_count += 1

    def complete(self, score: float, passed: bool) -> None:
        """
        WHAT: Marks session as completed
        WHERE: Called when user finishes interaction
        WHY: Finalizes session data for analytics

        Args:
            score: Final score achieved
            passed: Whether user passed
        """
        self.ended_at = datetime.utcnow()
        self.duration_seconds = (self.ended_at - self.started_at).total_seconds()
        self.status = "completed"
        self.completion_percentage = 100.0
        self.score = score
        self.passed = passed

    def abandon(self) -> None:
        """
        WHAT: Marks session as abandoned
        WHERE: Called when user leaves without completing
        WHY: Tracks incomplete interactions
        """
        self.ended_at = datetime.utcnow()
        self.duration_seconds = (self.ended_at - self.started_at).total_seconds()
        self.status = "abandoned"


# =============================================================================
# Export all entities
# =============================================================================

__all__ = [
    # Enums
    "InteractiveContentType",
    "InteractiveElementStatus",
    "DifficultyLevel",
    "InteractionEventType",
    "CodeLanguage",

    # Exceptions
    "InteractiveContentException",
    "InvalidInteractiveStateException",
    "InteractiveContentValidationException",
    "InteractionLimitExceededException",
    "UnsupportedLanguageException",
    "BranchNotFoundException",
    "HotspotNotFoundException",

    # Core Entities
    "InteractiveElement",
    "Simulation",
    "DragDropItem",
    "DropZone",
    "DragDropActivity",
    "Hotspot",
    "DiagramLayer",
    "InteractiveDiagram",
    "CodePlayground",
    "ScenarioBranch",
    "BranchingScenario",
    "TimelineEvent",
    "InteractiveTimeline",
    "Flashcard",
    "FlashcardDeck",
    "VideoInteraction",
    "InteractiveVideo",
    "InteractionSession",
]
