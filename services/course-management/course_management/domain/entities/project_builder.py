"""
Project Builder Domain Entities

BUSINESS CONTEXT:
This module defines the core domain entities for the AI-powered project builder
feature. The project builder enables organization administrators to create complete
training program structures through natural language conversation with an AI assistant.

WHY THIS EXISTS:
Traditional project creation requires manually configuring projects, sub-projects,
tracks, courses, instructors, and students through multiple UI screens. This is
time-consuming for large training programs with multiple locations and tracks.
The project builder automates this by:
1. Parsing natural language descriptions of training programs
2. Processing roster files (instructors, students) in multiple formats
3. Generating intelligent schedules with conflict detection
4. Creating Zoom rooms for virtual classrooms
5. Optionally generating course content (syllabi, slides, quizzes, labs)

WHAT THIS MODULE PROVIDES:
- ProjectBuilderSpec: Complete specification for a training program
- LocationSpec: Specification for a sub-project (training location)
- TrackSpec: Specification for a learning track with courses
- CourseSpec: Specification for an individual course
- InstructorSpec: Specification for an instructor assignment
- StudentSpec: Specification for a student enrollment
- ScheduleConfig: Configuration for schedule generation
- ContentGenerationConfig: Configuration for content auto-generation
- ZoomConfig: Configuration for Zoom room creation
- ScheduleEntry: Individual schedule entry (class session)
- ScheduleProposal: Generated schedule with conflict analysis
- Conflict: Schedule conflict detection result
- ProjectCreationResult: Result of bulk project creation

HOW TO USE:
1. Create a ProjectBuilderSpec from AI-parsed user input
2. Attach roster files and parse them into InstructorSpec/StudentSpec lists
3. Generate a ScheduleProposal using the ScheduleGenerator service
4. Present the proposal to the user for confirmation
5. Execute creation using BulkProjectCreator service

DOMAIN MODEL RELATIONSHIPS:
ProjectBuilderSpec
├── LocationSpec[] (sub-projects/cohorts)
├── TrackSpec[] (learning paths)
│   └── CourseSpec[] (courses in track)
├── InstructorSpec[] (instructor assignments)
├── StudentSpec[] (student enrollments)
├── ScheduleConfig (timing configuration)
├── ContentGenerationConfig (content generation settings)
└── ZoomConfig (Zoom room configuration)

@module project_builder
@author Course Creator Platform
@version 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class ProjectBuilderException(Exception):
    """
    Base exception for all project builder domain errors.

    WHY: Provides a common base class for catching all project builder
    related errors while maintaining specific error types for different
    failure scenarios.

    WHAT: Base exception that all project builder exceptions inherit from.
    Includes error code and context for detailed error handling.

    HOW: Catch ProjectBuilderException to handle any project builder error,
    or catch specific subclasses for targeted error handling.
    """

    def __init__(self, message: str, code: str = "PROJECT_BUILDER_ERROR", context: Dict[str, Any] = None):
        """
        Initialize project builder exception.

        Args:
            message: Human-readable error description
            code: Machine-readable error code for programmatic handling
            context: Additional context data for debugging
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.code,
            "message": self.message,
            "context": self.context
        }


class InvalidSpecificationException(ProjectBuilderException):
    """
    Raised when a project specification is invalid.

    WHY: Enables early validation of project specifications before
    expensive creation operations are attempted.

    WHAT: Indicates that the provided specification violates business
    rules or contains invalid/missing data.

    HOW: Raised during validation of ProjectBuilderSpec or its components.
    """

    def __init__(self, message: str, field: str = None, context: Dict[str, Any] = None):
        ctx = context or {}
        if field:
            ctx["field"] = field
        super().__init__(message, "INVALID_SPECIFICATION", ctx)
        self.field = field


class ScheduleConflictException(ProjectBuilderException):
    """
    Raised when schedule generation encounters unresolvable conflicts.

    WHY: Prevents creation of schedules that would double-book
    instructors, rooms, or violate capacity constraints.

    WHAT: Indicates that the requested schedule configuration cannot
    be satisfied without conflicts.

    HOW: Raised by ScheduleGenerator when conflicts cannot be
    automatically resolved.
    """

    def __init__(self, message: str, conflicts: List['Conflict'] = None, context: Dict[str, Any] = None):
        ctx = context or {}
        if conflicts:
            ctx["conflicts"] = [c.to_dict() for c in conflicts]
        super().__init__(message, "SCHEDULE_CONFLICT", ctx)
        self.conflicts = conflicts or []


class RosterParseException(ProjectBuilderException):
    """
    Raised when roster file parsing fails.

    WHY: Provides detailed error information when instructor or student
    roster files cannot be parsed, enabling users to fix their files.

    WHAT: Indicates that a roster file has invalid format, missing
    required columns, or unparseable data.

    HOW: Raised by RosterFileParser when file parsing fails.
    """

    def __init__(self, message: str, filename: str = None, row: int = None, context: Dict[str, Any] = None):
        ctx = context or {}
        if filename:
            ctx["filename"] = filename
        if row is not None:
            ctx["row"] = row
        super().__init__(message, "ROSTER_PARSE_ERROR", ctx)
        self.filename = filename
        self.row = row


class ZoomConfigurationException(ProjectBuilderException):
    """
    Raised when Zoom room configuration or creation fails.

    WHY: Separates Zoom-related errors from other project creation errors,
    allowing for graceful degradation (manual Zoom input) when API fails.

    WHAT: Indicates that Zoom room creation failed due to API errors,
    invalid configuration, or missing credentials.

    HOW: Raised by Zoom integration services when room creation fails.
    """

    def __init__(self, message: str, room_type: str = None, context: Dict[str, Any] = None):
        ctx = context or {}
        if room_type:
            ctx["room_type"] = room_type
        super().__init__(message, "ZOOM_CONFIGURATION_ERROR", ctx)
        self.room_type = room_type


class ContentGenerationException(ProjectBuilderException):
    """
    Raised when content generation fails.

    WHY: Allows content generation failures to be handled separately,
    as content can be generated later if initial generation fails.

    WHAT: Indicates that automatic content generation (syllabi, slides,
    quizzes, labs) failed for one or more courses.

    HOW: Raised by ContentGenerationCoordinator when generation fails.
    """

    def __init__(self, message: str, content_type: str = None, course_id: UUID = None, context: Dict[str, Any] = None):
        ctx = context or {}
        if content_type:
            ctx["content_type"] = content_type
        if course_id:
            ctx["course_id"] = str(course_id)
        super().__init__(message, "CONTENT_GENERATION_ERROR", ctx)
        self.content_type = content_type
        self.course_id = course_id


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ProjectBuilderState(str, Enum):
    """
    State machine states for project builder conversation flow.

    WHY: Manages the multi-step conversation flow where users progressively
    provide information about their training program.

    WHAT: Defines all possible states in the project builder workflow,
    from initial description to final creation.

    HOW: Used by ProjectBuilderOrchestrator to track conversation state
    and determine appropriate next actions.
    """
    INITIAL = "initial"                    # Waiting for project description
    COLLECTING_DETAILS = "collecting_details"  # Gathering additional info
    AWAITING_ROSTERS = "awaiting_rosters"  # Waiting for file uploads
    PARSING_ROSTERS = "parsing_rosters"    # Processing uploaded files
    SCHEDULE_REVIEW = "schedule_review"    # Presenting schedule for approval
    CONTENT_CONFIG = "content_config"      # Configuring content generation
    ZOOM_CONFIG = "zoom_config"            # Configuring Zoom rooms
    PREVIEW = "preview"                    # Showing creation preview
    CREATING = "creating"                  # Executing creation
    COMPLETE = "complete"                  # Creation finished
    ERROR = "error"                        # Error state


class ContentType(str, Enum):
    """
    Types of content that can be auto-generated.

    WHY: Allows granular control over which content types to generate,
    as different organizations have different needs and existing content.

    WHAT: Enumerates all content types supported by the content
    generation system.

    HOW: Used in ContentGenerationConfig to specify which content
    types should be automatically generated.
    """
    SYLLABUS = "syllabus"      # Course syllabus/outline
    SLIDES = "slides"          # Presentation slides
    QUIZ = "quiz"              # Assessment quizzes
    LAB = "lab"                # Hands-on lab exercises
    ASSIGNMENT = "assignment"  # Take-home assignments
    READING = "reading"        # Reading materials/summaries


class ConflictType(str, Enum):
    """
    Types of scheduling conflicts.

    WHY: Enables specific handling of different conflict types,
    as some conflicts (instructor double-booking) are harder to
    resolve than others (room conflicts).

    WHAT: Categorizes scheduling conflicts for targeted resolution.

    HOW: Used in Conflict entities to classify the type of conflict
    detected during schedule generation.
    """
    INSTRUCTOR_DOUBLE_BOOKING = "instructor_double_booking"
    ROOM_CONFLICT = "room_conflict"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    DATE_CONFLICT = "date_conflict"
    INSTRUCTOR_UNAVAILABLE = "instructor_unavailable"


class ZoomRoomType(str, Enum):
    """
    Types of Zoom rooms to create.

    WHY: Different room types have different configurations
    (classroom vs office hours have different settings).

    WHAT: Categorizes Zoom rooms by their purpose.

    HOW: Used in ZoomConfig and room creation to apply
    appropriate settings per room type.
    """
    CLASSROOM = "classroom"        # Track classroom (recurring)
    OFFICE_HOURS = "office_hours"  # Instructor office hours
    WORKSHOP = "workshop"          # One-off workshop sessions
    ORIENTATION = "orientation"    # Program orientation meetings


# =============================================================================
# VALUE OBJECTS - Specification Components
# =============================================================================

@dataclass
class CourseSpec:
    """
    Specification for a course to be created.

    WHY: Captures all information needed to create a course within a track,
    separate from database representation for clean domain modeling.

    WHAT: Contains course metadata, difficulty, duration, and optional
    content generation settings.

    HOW: Created from AI parsing of user input or roster files,
    then used by BulkProjectCreator to create actual Course entities.
    """

    # Required fields
    title: str
    description: str

    # Optional fields with defaults
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    duration_hours: int = 8
    order_index: int = 0

    # Content generation overrides (None = use project default)
    generate_syllabus: Optional[bool] = None
    generate_slides: Optional[bool] = None
    generate_quizzes: Optional[bool] = None
    generate_labs: Optional[bool] = None

    # Additional metadata
    prerequisites: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate course specification.

        WHY: Ensures course has required data before creation is attempted.

        WHAT: Validates title, description, difficulty, and duration.

        HOW: Called during ProjectBuilderSpec validation.

        Raises:
            InvalidSpecificationException: If validation fails
        """
        if not self.title or not self.title.strip():
            raise InvalidSpecificationException(
                "Course title is required",
                field="title"
            )

        if not self.description or not self.description.strip():
            raise InvalidSpecificationException(
                "Course description is required",
                field="description"
            )

        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if self.difficulty not in valid_difficulties:
            raise InvalidSpecificationException(
                f"Invalid difficulty: {self.difficulty}. Must be one of {valid_difficulties}",
                field="difficulty"
            )

        if self.duration_hours < 1:
            raise InvalidSpecificationException(
                "Course duration must be at least 1 hour",
                field="duration_hours"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "duration_hours": self.duration_hours,
            "order_index": self.order_index,
            "generate_syllabus": self.generate_syllabus,
            "generate_slides": self.generate_slides,
            "generate_quizzes": self.generate_quizzes,
            "generate_labs": self.generate_labs,
            "prerequisites": self.prerequisites,
            "learning_objectives": self.learning_objectives,
            "tags": self.tags,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CourseSpec':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TrackSpec:
    """
    Specification for a track (learning path) to be created.

    WHY: Tracks group related courses into a coherent learning journey.
    The project builder needs to capture track structure before creation.

    WHAT: Contains track metadata and a list of courses belonging to
    this track.

    HOW: Created from AI parsing, then used by BulkProjectCreator to
    create Track entities with their associated courses.
    """

    # Required fields
    name: str

    # Optional fields
    description: str = ""
    courses: List[CourseSpec] = field(default_factory=list)

    # Instructor assignments for this track
    instructor_emails: List[str] = field(default_factory=list)

    # Additional metadata
    order_index: int = 0
    color: str = "#3B82F6"  # Default blue
    icon: str = "book"
    estimated_duration_weeks: int = 6
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate track specification.

        WHY: Ensures track has required data and all courses are valid.

        WHAT: Validates track name and recursively validates all courses.

        HOW: Called during ProjectBuilderSpec validation.

        Raises:
            InvalidSpecificationException: If validation fails
        """
        if not self.name or not self.name.strip():
            raise InvalidSpecificationException(
                "Track name is required",
                field="name"
            )

        # Validate all courses
        for i, course in enumerate(self.courses):
            try:
                course.validate()
            except InvalidSpecificationException as e:
                raise InvalidSpecificationException(
                    f"Invalid course at index {i} in track '{self.name}': {e.message}",
                    field=f"courses[{i}].{e.field}" if e.field else f"courses[{i}]",
                    context={"track_name": self.name, "course_index": i}
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "courses": [c.to_dict() for c in self.courses],
            "instructor_emails": self.instructor_emails,
            "order_index": self.order_index,
            "color": self.color,
            "icon": self.icon,
            "estimated_duration_weeks": self.estimated_duration_weeks,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackSpec':
        """Create from dictionary."""
        courses_data = data.pop("courses", [])
        track = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        track.courses = [CourseSpec.from_dict(c) for c in courses_data]
        return track


@dataclass
class LocationSpec:
    """
    Specification for a location (sub-project) to be created.

    WHY: Multi-location training programs run the same curriculum in
    different cities/regions with independent schedules and capacity.

    WHAT: Contains location metadata including geographic information,
    schedule, and capacity constraints.

    HOW: Created from AI parsing (e.g., "London, NYC, Chicago"),
    then used by BulkProjectCreator to create SubProject entities.
    """

    # Required fields
    name: str

    # Geographic information
    country: str = "United States"
    region: Optional[str] = None  # State/Province
    city: Optional[str] = None
    address: Optional[str] = None
    timezone: str = "America/New_York"

    # Schedule
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Capacity
    max_students: Optional[int] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate location specification.

        WHY: Ensures location has required data and logical date ranges.

        WHAT: Validates name, country, timezone, and date logic.

        HOW: Called during ProjectBuilderSpec validation.

        Raises:
            InvalidSpecificationException: If validation fails
        """
        if not self.name or not self.name.strip():
            raise InvalidSpecificationException(
                "Location name is required",
                field="name"
            )

        if not self.country or not self.country.strip():
            raise InvalidSpecificationException(
                "Location country is required",
                field="country"
            )

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise InvalidSpecificationException(
                "Location start date must be before end date",
                field="start_date",
                context={"start_date": str(self.start_date), "end_date": str(self.end_date)}
            )

        if self.max_students is not None and self.max_students < 1:
            raise InvalidSpecificationException(
                "Max students must be at least 1",
                field="max_students"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "address": self.address,
            "timezone": self.timezone,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "max_students": self.max_students,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationSpec':
        """Create from dictionary."""
        # Convert date strings
        if "start_date" in data and isinstance(data["start_date"], str):
            data["start_date"] = date.fromisoformat(data["start_date"])
        if "end_date" in data and isinstance(data["end_date"], str):
            data["end_date"] = date.fromisoformat(data["end_date"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class InstructorSpec:
    """
    Specification for an instructor assignment.

    WHY: Instructors need to be assigned to tracks with specific date
    ranges, enabling schedule generation and Zoom room creation.

    WHAT: Contains instructor identity, track assignments, availability,
    and optional Zoom room preferences.

    HOW: Created from roster file parsing or AI conversation,
    then used for schedule generation and user creation/assignment.
    """

    # Required fields
    name: str
    email: str

    # Track assignments
    track_names: List[str] = field(default_factory=list)

    # Availability
    available_days: List[str] = field(default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    available_start_time: time = field(default_factory=lambda: time(9, 0))
    available_end_time: time = field(default_factory=lambda: time(17, 0))

    # Date range (if instructor is only available for part of program)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Zoom preferences
    create_office_hours_room: bool = True
    office_hours_weekly_slots: int = 2  # Number of office hour slots per week

    # Role within program
    role: str = "instructor"  # instructor, lead_instructor, teaching_assistant

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate instructor specification.

        WHY: Ensures instructor has valid identity and time constraints.

        WHAT: Validates name, email format, and time range logic.

        HOW: Called during ProjectBuilderSpec validation.

        Raises:
            InvalidSpecificationException: If validation fails
        """
        if not self.name or not self.name.strip():
            raise InvalidSpecificationException(
                "Instructor name is required",
                field="name"
            )

        if not self.email or "@" not in self.email:
            raise InvalidSpecificationException(
                "Valid instructor email is required",
                field="email"
            )

        if self.available_start_time >= self.available_end_time:
            raise InvalidSpecificationException(
                "Available start time must be before end time",
                field="available_start_time"
            )

        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in self.available_days:
            if day not in valid_days:
                raise InvalidSpecificationException(
                    f"Invalid day: {day}. Must be one of {valid_days}",
                    field="available_days"
                )

        valid_roles = ["instructor", "lead_instructor", "teaching_assistant"]
        if self.role not in valid_roles:
            raise InvalidSpecificationException(
                f"Invalid role: {self.role}. Must be one of {valid_roles}",
                field="role"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "email": self.email,
            "track_names": self.track_names,
            "available_days": self.available_days,
            "available_start_time": self.available_start_time.isoformat(),
            "available_end_time": self.available_end_time.isoformat(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "create_office_hours_room": self.create_office_hours_room,
            "office_hours_weekly_slots": self.office_hours_weekly_slots,
            "role": self.role,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstructorSpec':
        """Create from dictionary."""
        # Convert time strings
        if "available_start_time" in data and isinstance(data["available_start_time"], str):
            data["available_start_time"] = time.fromisoformat(data["available_start_time"])
        if "available_end_time" in data and isinstance(data["available_end_time"], str):
            data["available_end_time"] = time.fromisoformat(data["available_end_time"])
        # Convert date strings
        if "start_date" in data and isinstance(data["start_date"], str):
            data["start_date"] = date.fromisoformat(data["start_date"])
        if "end_date" in data and isinstance(data["end_date"], str):
            data["end_date"] = date.fromisoformat(data["end_date"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class StudentSpec:
    """
    Specification for a student enrollment.

    WHY: Students need to be enrolled in specific tracks at specific
    locations, with optional group assignments.

    WHAT: Contains student identity, track and location assignments,
    and enrollment metadata.

    HOW: Created from roster file parsing, then used by BulkProjectCreator
    to create user accounts and enrollments.
    """

    # Required fields
    name: str
    email: str

    # Assignments
    track_name: str = ""
    location_name: Optional[str] = None

    # Instructor preference (optional)
    preferred_instructor_email: Optional[str] = None

    # Group assignment (for study groups)
    group_name: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate student specification.

        WHY: Ensures student has valid identity and track assignment.

        WHAT: Validates name, email, and track assignment.

        HOW: Called during ProjectBuilderSpec validation.

        Raises:
            InvalidSpecificationException: If validation fails
        """
        if not self.name or not self.name.strip():
            raise InvalidSpecificationException(
                "Student name is required",
                field="name"
            )

        if not self.email or "@" not in self.email:
            raise InvalidSpecificationException(
                "Valid student email is required",
                field="email"
            )

        if not self.track_name or not self.track_name.strip():
            raise InvalidSpecificationException(
                "Student track assignment is required",
                field="track_name"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "email": self.email,
            "track_name": self.track_name,
            "location_name": self.location_name,
            "preferred_instructor_email": self.preferred_instructor_email,
            "group_name": self.group_name,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentSpec':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# =============================================================================
# CONFIGURATION VALUE OBJECTS
# =============================================================================

@dataclass
class ScheduleConfig:
    """
    Configuration for schedule generation.

    WHY: Schedule generation needs to know time boundaries, working days,
    and session duration preferences to create a viable schedule.

    WHAT: Contains all parameters needed to generate a schedule including
    date range, working days, hours, and session preferences.

    HOW: Created from user preferences in AI conversation, then passed
    to ScheduleGenerator service.
    """

    # Date range
    start_date: date = field(default_factory=date.today)
    duration_weeks: int = 6

    # Working days (default: Monday-Friday)
    working_days: List[str] = field(default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

    # Daily hours
    day_start_time: time = field(default_factory=lambda: time(9, 0))
    day_end_time: time = field(default_factory=lambda: time(17, 0))
    hours_per_day: int = 8

    # Session preferences
    session_duration_hours: int = 2  # Default session length
    break_between_sessions_minutes: int = 15
    lunch_break_start: time = field(default_factory=lambda: time(12, 0))
    lunch_break_duration_minutes: int = 60

    # Advanced options
    allow_parallel_tracks: bool = True  # Can different tracks run simultaneously?
    prefer_morning_sessions: bool = False

    def validate(self) -> None:
        """Validate schedule configuration."""
        if self.duration_weeks < 1:
            raise InvalidSpecificationException(
                "Duration must be at least 1 week",
                field="duration_weeks"
            )

        if self.hours_per_day < 1:
            raise InvalidSpecificationException(
                "Hours per day must be at least 1",
                field="hours_per_day"
            )

        if not self.working_days:
            raise InvalidSpecificationException(
                "At least one working day is required",
                field="working_days"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "start_date": self.start_date.isoformat(),
            "duration_weeks": self.duration_weeks,
            "working_days": self.working_days,
            "day_start_time": self.day_start_time.isoformat(),
            "day_end_time": self.day_end_time.isoformat(),
            "hours_per_day": self.hours_per_day,
            "session_duration_hours": self.session_duration_hours,
            "break_between_sessions_minutes": self.break_between_sessions_minutes,
            "lunch_break_start": self.lunch_break_start.isoformat(),
            "lunch_break_duration_minutes": self.lunch_break_duration_minutes,
            "allow_parallel_tracks": self.allow_parallel_tracks,
            "prefer_morning_sessions": self.prefer_morning_sessions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleConfig':
        """Create from dictionary."""
        # Convert date/time strings
        if "start_date" in data and isinstance(data["start_date"], str):
            data["start_date"] = date.fromisoformat(data["start_date"])
        for time_field in ["day_start_time", "day_end_time", "lunch_break_start"]:
            if time_field in data and isinstance(data[time_field], str):
                data[time_field] = time.fromisoformat(data[time_field])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ContentGenerationConfig:
    """
    Configuration for automatic content generation.

    WHY: Organizations have different content needs - some want full
    auto-generation, others have existing content and only need quizzes.

    WHAT: Specifies which content types to generate and quality parameters.

    HOW: Configured during project builder conversation, then used by
    ContentGenerationCoordinator to queue generation jobs.
    """

    # Content type toggles
    generate_syllabi: bool = True
    generate_slides: bool = True
    generate_quizzes: bool = True
    generate_labs: bool = True
    generate_assignments: bool = False
    generate_readings: bool = False

    # Quality parameters
    quiz_questions_per_course: int = 10
    quiz_difficulty_mix: Dict[str, float] = field(default_factory=lambda: {
        "easy": 0.3,
        "medium": 0.5,
        "hard": 0.2
    })

    # Lab parameters
    lab_exercises_per_course: int = 3
    include_lab_solutions: bool = True

    # Slides parameters
    slides_per_course_hour: int = 5  # Approximately 5 slides per hour of content

    # AI model preferences
    use_advanced_model: bool = False  # Use more capable (but slower) model

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "generate_syllabi": self.generate_syllabi,
            "generate_slides": self.generate_slides,
            "generate_quizzes": self.generate_quizzes,
            "generate_labs": self.generate_labs,
            "generate_assignments": self.generate_assignments,
            "generate_readings": self.generate_readings,
            "quiz_questions_per_course": self.quiz_questions_per_course,
            "quiz_difficulty_mix": self.quiz_difficulty_mix,
            "lab_exercises_per_course": self.lab_exercises_per_course,
            "include_lab_solutions": self.include_lab_solutions,
            "slides_per_course_hour": self.slides_per_course_hour,
            "use_advanced_model": self.use_advanced_model
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentGenerationConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ZoomConfig:
    """
    Configuration for Zoom room creation.

    WHY: Zoom integration is optional and has multiple modes (API vs manual).
    This configuration captures all Zoom-related preferences.

    WHAT: Specifies whether to create rooms, room types, and fallback options.

    HOW: Configured during project builder conversation, then used by
    ZoomIntegrationService to create rooms or enable manual input.
    """

    # Master toggle
    create_zoom_rooms: bool = True

    # Room types to create
    create_track_classrooms: bool = True
    create_instructor_office_hours: bool = True
    create_orientation_room: bool = True

    # Room settings
    waiting_room_enabled: bool = True
    auto_recording: str = "cloud"  # none, local, cloud
    mute_on_entry: bool = True

    # Fallback options
    allow_manual_input: bool = True  # Allow manual Zoom link entry if API fails
    manual_zoom_links: Dict[str, str] = field(default_factory=dict)  # Pre-configured links

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "create_zoom_rooms": self.create_zoom_rooms,
            "create_track_classrooms": self.create_track_classrooms,
            "create_instructor_office_hours": self.create_instructor_office_hours,
            "create_orientation_room": self.create_orientation_room,
            "waiting_room_enabled": self.waiting_room_enabled,
            "auto_recording": self.auto_recording,
            "mute_on_entry": self.mute_on_entry,
            "allow_manual_input": self.allow_manual_input,
            "manual_zoom_links": self.manual_zoom_links
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ZoomConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# =============================================================================
# MAIN SPECIFICATION ENTITY
# =============================================================================

@dataclass
class ProjectBuilderSpec:
    """
    Complete specification for a training program to be created.

    WHY: The project builder needs a single, comprehensive data structure
    that captures ALL information needed to create a complete training
    program, from project metadata to individual student enrollments.

    WHAT: The root entity containing:
    - Project metadata (name, description)
    - Locations (sub-projects for multi-site programs)
    - Tracks (learning paths with courses)
    - Instructors (with track assignments and availability)
    - Students (with track and location assignments)
    - Schedule configuration
    - Content generation settings
    - Zoom room settings

    HOW: Built incrementally through AI conversation:
    1. User describes project in natural language
    2. AI extracts entities and creates initial spec
    3. User uploads roster files, spec is enriched
    4. User configures schedule, content, Zoom options
    5. Final spec is validated and executed by BulkProjectCreator

    DOMAIN INVARIANTS:
    - Project name is required
    - At least one track is required
    - All instructors must be assigned to at least one track
    - All students must be assigned to a track
    - Schedule must fit within project date range
    """

    # Project identification
    id: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Project metadata
    name: str = ""
    slug: str = ""
    description: str = ""

    # Program structure
    locations: List[LocationSpec] = field(default_factory=list)
    tracks: List[TrackSpec] = field(default_factory=list)

    # People
    instructors: List[InstructorSpec] = field(default_factory=list)
    students: List[StudentSpec] = field(default_factory=list)

    # Configurations
    schedule_config: ScheduleConfig = field(default_factory=ScheduleConfig)
    content_generation_config: ContentGenerationConfig = field(default_factory=ContentGenerationConfig)
    zoom_config: ZoomConfig = field(default_factory=ZoomConfig)

    # Builder state
    state: ProjectBuilderState = ProjectBuilderState.INITIAL

    # Audit
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[UUID] = None

    # Metadata for AI conversation context
    conversation_context: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate the complete project specification.

        WHY: Comprehensive validation before expensive creation operations
        prevents partial creation failures and ensures data integrity.

        WHAT: Validates all components and cross-references:
        - Required fields present
        - All nested specs valid
        - Instructor track assignments reference existing tracks
        - Student assignments reference existing tracks and locations

        HOW: Called before executing creation, raises detailed exceptions
        for any validation failures.

        Raises:
            InvalidSpecificationException: If any validation fails
        """
        # Validate required fields
        if not self.name or not self.name.strip():
            raise InvalidSpecificationException(
                "Project name is required",
                field="name"
            )

        if not self.tracks:
            raise InvalidSpecificationException(
                "At least one track is required",
                field="tracks"
            )

        # Validate nested specs
        for i, location in enumerate(self.locations):
            try:
                location.validate()
            except InvalidSpecificationException as e:
                raise InvalidSpecificationException(
                    f"Invalid location at index {i}: {e.message}",
                    field=f"locations[{i}].{e.field}" if e.field else f"locations[{i}]"
                )

        for i, track in enumerate(self.tracks):
            try:
                track.validate()
            except InvalidSpecificationException as e:
                raise InvalidSpecificationException(
                    f"Invalid track at index {i}: {e.message}",
                    field=f"tracks[{i}].{e.field}" if e.field else f"tracks[{i}]"
                )

        for i, instructor in enumerate(self.instructors):
            try:
                instructor.validate()
            except InvalidSpecificationException as e:
                raise InvalidSpecificationException(
                    f"Invalid instructor at index {i}: {e.message}",
                    field=f"instructors[{i}].{e.field}" if e.field else f"instructors[{i}]"
                )

        for i, student in enumerate(self.students):
            try:
                student.validate()
            except InvalidSpecificationException as e:
                raise InvalidSpecificationException(
                    f"Invalid student at index {i}: {e.message}",
                    field=f"students[{i}].{e.field}" if e.field else f"students[{i}]"
                )

        # Validate configurations
        self.schedule_config.validate()

        # Cross-reference validation
        track_names = {t.name.lower() for t in self.tracks}
        location_names = {l.name.lower() for l in self.locations}

        # Validate instructor track assignments
        for instructor in self.instructors:
            for track_name in instructor.track_names:
                if track_name.lower() not in track_names:
                    raise InvalidSpecificationException(
                        f"Instructor '{instructor.name}' assigned to unknown track '{track_name}'",
                        field="instructors",
                        context={"instructor_email": instructor.email, "track_name": track_name}
                    )

        # Validate student assignments
        for student in self.students:
            if student.track_name.lower() not in track_names:
                raise InvalidSpecificationException(
                    f"Student '{student.name}' assigned to unknown track '{student.track_name}'",
                    field="students",
                    context={"student_email": student.email, "track_name": student.track_name}
                )

            if student.location_name and student.location_name.lower() not in location_names:
                raise InvalidSpecificationException(
                    f"Student '{student.name}' assigned to unknown location '{student.location_name}'",
                    field="students",
                    context={"student_email": student.email, "location_name": student.location_name}
                )

    def get_track_by_name(self, name: str) -> Optional[TrackSpec]:
        """Get track by name (case-insensitive)."""
        name_lower = name.lower()
        for track in self.tracks:
            if track.name.lower() == name_lower:
                return track
        return None

    def get_location_by_name(self, name: str) -> Optional[LocationSpec]:
        """Get location by name (case-insensitive)."""
        name_lower = name.lower()
        for location in self.locations:
            if location.name.lower() == name_lower:
                return location
        return None

    def get_instructors_for_track(self, track_name: str) -> List[InstructorSpec]:
        """Get all instructors assigned to a track."""
        name_lower = track_name.lower()
        return [
            i for i in self.instructors
            if any(t.lower() == name_lower for t in i.track_names)
        ]

    def get_students_for_track(self, track_name: str) -> List[StudentSpec]:
        """Get all students enrolled in a track."""
        name_lower = track_name.lower()
        return [s for s in self.students if s.track_name.lower() == name_lower]

    def get_students_for_location(self, location_name: str) -> List[StudentSpec]:
        """Get all students at a location."""
        name_lower = location_name.lower()
        return [
            s for s in self.students
            if s.location_name and s.location_name.lower() == name_lower
        ]

    def get_total_courses(self) -> int:
        """Get total number of courses across all tracks."""
        return sum(len(track.courses) for track in self.tracks)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the specification for preview display.

        WHY: Users need to see a summary of what will be created before
        confirming the creation operation.

        WHAT: Returns counts and key information about all components.

        HOW: Called by frontend to display preview card.
        """
        return {
            "project_name": self.name,
            "locations_count": len(self.locations),
            "locations": [l.name for l in self.locations],
            "tracks_count": len(self.tracks),
            "tracks": [{"name": t.name, "courses_count": len(t.courses)} for t in self.tracks],
            "total_courses": self.get_total_courses(),
            "instructors_count": len(self.instructors),
            "students_count": len(self.students),
            "schedule": {
                "start_date": self.schedule_config.start_date.isoformat(),
                "duration_weeks": self.schedule_config.duration_weeks
            },
            "content_generation": {
                "syllabi": self.content_generation_config.generate_syllabi,
                "slides": self.content_generation_config.generate_slides,
                "quizzes": self.content_generation_config.generate_quizzes,
                "labs": self.content_generation_config.generate_labs
            },
            "zoom_rooms": self.zoom_config.create_zoom_rooms
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "locations": [l.to_dict() for l in self.locations],
            "tracks": [t.to_dict() for t in self.tracks],
            "instructors": [i.to_dict() for i in self.instructors],
            "students": [s.to_dict() for s in self.students],
            "schedule_config": self.schedule_config.to_dict(),
            "content_generation_config": self.content_generation_config.to_dict(),
            "zoom_config": self.zoom_config.to_dict(),
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "conversation_context": self.conversation_context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectBuilderSpec':
        """Create from dictionary."""
        # Convert nested objects
        locations = [LocationSpec.from_dict(l) for l in data.pop("locations", [])]
        tracks = [TrackSpec.from_dict(t) for t in data.pop("tracks", [])]
        instructors = [InstructorSpec.from_dict(i) for i in data.pop("instructors", [])]
        students = [StudentSpec.from_dict(s) for s in data.pop("students", [])]

        schedule_config = ScheduleConfig.from_dict(data.pop("schedule_config", {}))
        content_config = ContentGenerationConfig.from_dict(data.pop("content_generation_config", {}))
        zoom_config = ZoomConfig.from_dict(data.pop("zoom_config", {}))

        # Convert UUIDs
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])
        if "organization_id" in data and data["organization_id"] and isinstance(data["organization_id"], str):
            data["organization_id"] = UUID(data["organization_id"])
        if "created_by" in data and data["created_by"] and isinstance(data["created_by"], str):
            data["created_by"] = UUID(data["created_by"])

        # Convert state
        if "state" in data and isinstance(data["state"], str):
            data["state"] = ProjectBuilderState(data["state"])

        # Convert datetime
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        spec = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        spec.locations = locations
        spec.tracks = tracks
        spec.instructors = instructors
        spec.students = students
        spec.schedule_config = schedule_config
        spec.content_generation_config = content_config
        spec.zoom_config = zoom_config

        return spec


# =============================================================================
# SCHEDULE-RELATED VALUE OBJECTS
# =============================================================================

@dataclass
class ScheduleEntry:
    """
    A single scheduled session in the training program.

    WHY: Schedule generation produces individual session entries that
    specify when each course session occurs and who teaches it.

    WHAT: Contains all information needed to create a calendar event
    for a training session.

    HOW: Created by ScheduleGenerator, collected into ScheduleProposal.
    """

    # Identification
    id: UUID = field(default_factory=uuid4)

    # What
    track_name: str = ""
    course_title: str = ""
    session_number: int = 1  # Session 1 of N for this course

    # When
    date: date = field(default_factory=date.today)
    start_time: time = field(default_factory=lambda: time(9, 0))
    end_time: time = field(default_factory=lambda: time(11, 0))

    # Who
    instructor_email: Optional[str] = None
    instructor_name: Optional[str] = None

    # Where
    location_name: Optional[str] = None
    zoom_link: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "track_name": self.track_name,
            "course_title": self.course_title,
            "session_number": self.session_number,
            "date": self.date.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "instructor_email": self.instructor_email,
            "instructor_name": self.instructor_name,
            "location_name": self.location_name,
            "zoom_link": self.zoom_link
        }


@dataclass
class Conflict:
    """
    A scheduling conflict detected during schedule generation.

    WHY: Schedule generation must detect and report conflicts so users
    can resolve them (change dates, add instructors, etc.).

    WHAT: Describes a specific conflict with type, affected entities,
    and suggested resolutions.

    HOW: Created by ScheduleGenerator when conflicts are detected,
    returned in ScheduleProposal for user review.
    """

    # Identification
    id: UUID = field(default_factory=uuid4)

    # Conflict details
    conflict_type: ConflictType = ConflictType.INSTRUCTOR_DOUBLE_BOOKING
    description: str = ""
    severity: str = "error"  # warning, error

    # Affected entities
    affected_entries: List[UUID] = field(default_factory=list)
    affected_date: Optional[date] = None
    affected_instructor: Optional[str] = None
    affected_track: Optional[str] = None

    # Resolution suggestions
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "conflict_type": self.conflict_type.value,
            "description": self.description,
            "severity": self.severity,
            "affected_entries": [str(e) for e in self.affected_entries],
            "affected_date": self.affected_date.isoformat() if self.affected_date else None,
            "affected_instructor": self.affected_instructor,
            "affected_track": self.affected_track,
            "suggestions": self.suggestions
        }


@dataclass
class ScheduleProposal:
    """
    A proposed schedule for the training program.

    WHY: Schedule generation produces a proposal that users review
    before confirmation, allowing them to request changes or resolve
    conflicts.

    WHAT: Contains all scheduled entries, detected conflicts, and
    optimization suggestions.

    HOW: Created by ScheduleGenerator, presented to user for approval,
    then used for actual schedule creation if approved.
    """

    # Identification
    id: UUID = field(default_factory=uuid4)
    spec_id: UUID = field(default_factory=uuid4)  # Reference to ProjectBuilderSpec

    # Schedule
    entries: List[ScheduleEntry] = field(default_factory=list)

    # Conflicts and warnings
    conflicts: List[Conflict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Optimization suggestions
    suggestions: List[str] = field(default_factory=list)

    # Status
    is_valid: bool = True  # False if has unresolved errors

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)

    def has_errors(self) -> bool:
        """Check if proposal has error-level conflicts."""
        return any(c.severity == "error" for c in self.conflicts)

    def has_warnings(self) -> bool:
        """Check if proposal has warnings."""
        return bool(self.warnings) or any(c.severity == "warning" for c in self.conflicts)

    def get_entries_by_track(self, track_name: str) -> List[ScheduleEntry]:
        """Get all entries for a specific track."""
        return [e for e in self.entries if e.track_name == track_name]

    def get_entries_by_date(self, target_date: date) -> List[ScheduleEntry]:
        """Get all entries for a specific date."""
        return [e for e in self.entries if e.date == target_date]

    def get_entries_by_instructor(self, instructor_email: str) -> List[ScheduleEntry]:
        """Get all entries for a specific instructor."""
        return [e for e in self.entries if e.instructor_email == instructor_email]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "spec_id": str(self.spec_id),
            "entries": [e.to_dict() for e in self.entries],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "is_valid": self.is_valid,
            "generated_at": self.generated_at.isoformat()
        }


# =============================================================================
# RESULT VALUE OBJECTS
# =============================================================================

@dataclass
class ProjectCreationResult:
    """
    Result of bulk project creation.

    WHY: Creation is a complex multi-step process. Users need to know
    what was created, what failed, and how to access created entities.

    WHAT: Contains success status, created entity IDs and counts,
    any errors that occurred, and URLs for accessing created content.

    HOW: Returned by BulkProjectCreator after executing creation.
    """

    # Status
    success: bool = True

    # Created entity IDs
    project_id: Optional[UUID] = None
    subproject_ids: List[UUID] = field(default_factory=list)
    track_ids: List[UUID] = field(default_factory=list)
    course_ids: List[UUID] = field(default_factory=list)
    instructor_user_ids: List[UUID] = field(default_factory=list)
    student_user_ids: List[UUID] = field(default_factory=list)
    enrollment_ids: List[UUID] = field(default_factory=list)
    zoom_room_ids: List[str] = field(default_factory=list)

    # Counts
    counts: Dict[str, int] = field(default_factory=lambda: {
        "projects": 0,
        "subprojects": 0,
        "tracks": 0,
        "courses": 0,
        "instructors": 0,
        "students": 0,
        "enrollments": 0,
        "zoom_rooms": 0,
        "content_jobs": 0
    })

    # Errors (for partial failures)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # URLs for accessing created content
    project_url: Optional[str] = None
    dashboard_url: Optional[str] = None

    # Content generation job (if content generation was requested)
    content_generation_job_id: Optional[UUID] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "project_id": str(self.project_id) if self.project_id else None,
            "subproject_ids": [str(i) for i in self.subproject_ids],
            "track_ids": [str(i) for i in self.track_ids],
            "course_ids": [str(i) for i in self.course_ids],
            "instructor_user_ids": [str(i) for i in self.instructor_user_ids],
            "student_user_ids": [str(i) for i in self.student_user_ids],
            "enrollment_ids": [str(i) for i in self.enrollment_ids],
            "zoom_room_ids": self.zoom_room_ids,
            "counts": self.counts,
            "errors": self.errors,
            "warnings": self.warnings,
            "project_url": self.project_url,
            "dashboard_url": self.dashboard_url,
            "content_generation_job_id": str(self.content_generation_job_id) if self.content_generation_job_id else None,
            "created_at": self.created_at.isoformat(),
            "duration_seconds": self.duration_seconds
        }
