"""
Unit Tests for Project Builder Domain Entities

BUSINESS CONTEXT:
These tests verify the domain entities used by the AI-powered project builder
feature. The project builder enables organization admins to create complete
training programs through natural language conversation.

WHY THESE TESTS EXIST:
1. Validate business rules encoded in domain entities
2. Ensure proper validation of specifications
3. Verify serialization/deserialization (to_dict/from_dict)
4. Test exception handling and error messages
5. Verify cross-reference validation between entities

WHAT IS TESTED:
- CourseSpec: Course specification validation and serialization
- TrackSpec: Track specification with nested courses
- LocationSpec: Location/sub-project specification
- InstructorSpec: Instructor assignment specification
- StudentSpec: Student enrollment specification
- ScheduleConfig: Schedule generation configuration
- ContentGenerationConfig: Content generation settings
- ZoomConfig: Zoom room configuration
- ProjectBuilderSpec: Complete project specification with cross-refs
- ScheduleEntry, Conflict, ScheduleProposal: Schedule entities
- ProjectCreationResult: Creation result tracking
- Custom exceptions: All project builder exceptions

HOW TO RUN:
    pytest tests/unit/course_management/test_project_builder_entities.py -v

TDD: Tests written BEFORE implementation verification.

@module test_project_builder_entities
@author Course Creator Platform
@version 1.0.0
"""

import pytest
from datetime import date, time, datetime
from uuid import UUID, uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from course_management.domain.entities.project_builder import (
    # Main entities
    ProjectBuilderSpec,
    LocationSpec,
    TrackSpec,
    CourseSpec,
    InstructorSpec,
    StudentSpec,
    # Configuration entities
    ScheduleConfig,
    ContentGenerationConfig,
    ZoomConfig,
    # Schedule entities
    ScheduleEntry,
    ScheduleProposal,
    Conflict,
    # Result entities
    ProjectCreationResult,
    # Enumerations
    ProjectBuilderState,
    ContentType,
    ConflictType,
    ZoomRoomType,
    # Exceptions
    ProjectBuilderException,
    InvalidSpecificationException,
    ScheduleConflictException,
    RosterParseException,
    ZoomConfigurationException,
    ContentGenerationException
)


# =============================================================================
# COURSE SPEC TESTS
# =============================================================================

class TestCourseSpec:
    """
    Test suite for CourseSpec domain entity.

    WHY: CourseSpec is the building block for tracks. Proper validation
    ensures courses have required data before creation.
    """

    def test_create_valid_course_spec(self):
        """
        Test creating a valid course specification.

        WHY: Basic happy path - courses with title and description should be valid.
        """
        course = CourseSpec(
            title="Python Basics",
            description="Introduction to Python programming"
        )

        assert course.title == "Python Basics"
        assert course.description == "Introduction to Python programming"
        assert course.difficulty == "beginner"
        assert course.duration_hours == 8

    def test_course_spec_with_all_fields(self):
        """
        Test creating course spec with all optional fields.

        WHY: Verify all optional fields are correctly stored.
        """
        course = CourseSpec(
            title="Advanced Python",
            description="Advanced Python concepts",
            difficulty="advanced",
            duration_hours=16,
            order_index=2,
            generate_syllabus=True,
            generate_slides=True,
            generate_quizzes=False,
            generate_labs=True,
            prerequisites=["Python Basics"],
            learning_objectives=["Master decorators", "Understand metaclasses"],
            tags=["python", "advanced"]
        )

        assert course.difficulty == "advanced"
        assert course.duration_hours == 16
        assert course.generate_quizzes is False
        assert len(course.prerequisites) == 1
        assert len(course.learning_objectives) == 2

    def test_course_spec_validation_missing_title(self):
        """
        Test that missing title raises validation error.

        WHY: Course title is required - validates business rule.
        """
        course = CourseSpec(title="", description="Some description")

        with pytest.raises(InvalidSpecificationException) as exc_info:
            course.validate()

        assert "title" in str(exc_info.value).lower()
        assert exc_info.value.field == "title"

    def test_course_spec_validation_missing_description(self):
        """
        Test that missing description raises validation error.

        WHY: Course description is required - validates business rule.
        """
        course = CourseSpec(title="Python Basics", description="")

        with pytest.raises(InvalidSpecificationException) as exc_info:
            course.validate()

        assert "description" in str(exc_info.value).lower()

    def test_course_spec_validation_invalid_difficulty(self):
        """
        Test that invalid difficulty raises validation error.

        WHY: Difficulty must be one of beginner/intermediate/advanced.
        """
        course = CourseSpec(
            title="Python Basics",
            description="Intro",
            difficulty="expert"  # Invalid
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            course.validate()

        assert "difficulty" in str(exc_info.value).lower()
        assert "expert" in str(exc_info.value)

    def test_course_spec_validation_invalid_duration(self):
        """
        Test that zero/negative duration raises validation error.

        WHY: Course must have positive duration.
        """
        course = CourseSpec(
            title="Python Basics",
            description="Intro",
            duration_hours=0
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            course.validate()

        assert "duration" in str(exc_info.value).lower()

    def test_course_spec_to_dict(self):
        """
        Test serialization to dictionary.

        WHY: Entities need to be serialized for API responses and storage.
        """
        course = CourseSpec(
            title="Python Basics",
            description="Intro to Python",
            difficulty="beginner",
            tags=["python"]
        )

        result = course.to_dict()

        assert result["title"] == "Python Basics"
        assert result["description"] == "Intro to Python"
        assert result["difficulty"] == "beginner"
        assert result["tags"] == ["python"]

    def test_course_spec_from_dict(self):
        """
        Test deserialization from dictionary.

        WHY: Entities need to be reconstructed from stored data.
        """
        data = {
            "title": "Python Basics",
            "description": "Intro to Python",
            "difficulty": "intermediate",
            "duration_hours": 12,
            "tags": ["python", "intro"]
        }

        course = CourseSpec.from_dict(data)

        assert course.title == "Python Basics"
        assert course.difficulty == "intermediate"
        assert course.duration_hours == 12


# =============================================================================
# TRACK SPEC TESTS
# =============================================================================

class TestTrackSpec:
    """
    Test suite for TrackSpec domain entity.

    WHY: TrackSpec groups courses into learning paths. Must validate
    track data and all nested courses.
    """

    def test_create_valid_track_spec(self):
        """
        Test creating a valid track specification.

        WHY: Basic happy path for track creation.
        """
        track = TrackSpec(
            name="Backend Development",
            description="Server-side programming track"
        )

        assert track.name == "Backend Development"
        assert track.description == "Server-side programming track"
        assert track.courses == []

    def test_track_spec_with_courses(self):
        """
        Test creating track with nested courses.

        WHY: Tracks typically contain multiple courses.
        """
        track = TrackSpec(
            name="Backend Development",
            description="Server-side programming",
            courses=[
                CourseSpec(title="Python Basics", description="Intro"),
                CourseSpec(title="Django Framework", description="Web framework")
            ]
        )

        assert len(track.courses) == 2
        assert track.courses[0].title == "Python Basics"
        assert track.courses[1].title == "Django Framework"

    def test_track_spec_with_instructors(self):
        """
        Test track with assigned instructors.

        WHY: Tracks have instructor assignments for schedule generation.
        """
        track = TrackSpec(
            name="Backend Development",
            description="Server-side programming",
            instructor_emails=["john@example.com", "jane@example.com"]
        )

        assert len(track.instructor_emails) == 2
        assert "john@example.com" in track.instructor_emails

    def test_track_spec_validation_missing_name(self):
        """
        Test that missing name raises validation error.

        WHY: Track name is required.
        """
        track = TrackSpec(name="", description="Some track")

        with pytest.raises(InvalidSpecificationException) as exc_info:
            track.validate()

        assert "name" in str(exc_info.value).lower()

    def test_track_spec_validation_cascades_to_courses(self):
        """
        Test that validation cascades to nested courses.

        WHY: Invalid courses should cause track validation to fail.
        """
        track = TrackSpec(
            name="Backend Development",
            description="Track",
            courses=[
                CourseSpec(title="Valid Course", description="Valid"),
                CourseSpec(title="", description="Invalid - no title")  # Invalid
            ]
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            track.validate()

        assert "course" in str(exc_info.value).lower()
        assert "index 1" in str(exc_info.value)

    def test_track_spec_to_dict_with_courses(self):
        """
        Test serialization includes nested courses.

        WHY: Full track structure must serialize correctly.
        """
        track = TrackSpec(
            name="Backend Development",
            description="Track",
            courses=[
                CourseSpec(title="Python Basics", description="Intro")
            ]
        )

        result = track.to_dict()

        assert result["name"] == "Backend Development"
        assert len(result["courses"]) == 1
        assert result["courses"][0]["title"] == "Python Basics"

    def test_track_spec_from_dict_with_courses(self):
        """
        Test deserialization reconstructs nested courses.

        WHY: Full track structure must deserialize correctly.
        """
        data = {
            "name": "Backend Development",
            "description": "Track",
            "courses": [
                {"title": "Python Basics", "description": "Intro"}
            ]
        }

        track = TrackSpec.from_dict(data)

        assert track.name == "Backend Development"
        assert len(track.courses) == 1
        assert isinstance(track.courses[0], CourseSpec)


# =============================================================================
# LOCATION SPEC TESTS
# =============================================================================

class TestLocationSpec:
    """
    Test suite for LocationSpec domain entity.

    WHY: LocationSpec represents sub-projects (training locations).
    Must validate geographic and scheduling data.
    """

    def test_create_valid_location_spec(self):
        """
        Test creating a valid location specification.

        WHY: Basic happy path for location creation.
        """
        location = LocationSpec(
            name="New York Office",
            country="United States",
            city="New York",
            timezone="America/New_York"
        )

        assert location.name == "New York Office"
        assert location.country == "United States"
        assert location.city == "New York"

    def test_location_spec_with_schedule(self):
        """
        Test location with schedule dates.

        WHY: Locations have independent schedules.
        """
        location = LocationSpec(
            name="NYC Q1 2024",
            country="United States",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 6, 30),
            max_students=30
        )

        assert location.start_date == date(2024, 1, 15)
        assert location.end_date == date(2024, 6, 30)
        assert location.max_students == 30

    def test_location_spec_validation_missing_name(self):
        """
        Test that missing name raises validation error.

        WHY: Location name is required.
        """
        location = LocationSpec(name="", country="US")

        with pytest.raises(InvalidSpecificationException) as exc_info:
            location.validate()

        assert "name" in str(exc_info.value).lower()

    def test_location_spec_validation_missing_country(self):
        """
        Test that missing country raises validation error.

        WHY: Country is required for location.
        """
        location = LocationSpec(name="NYC Office", country="")

        with pytest.raises(InvalidSpecificationException) as exc_info:
            location.validate()

        assert "country" in str(exc_info.value).lower()

    def test_location_spec_validation_invalid_dates(self):
        """
        Test that end_date before start_date raises validation error.

        WHY: Date range must be logical.
        """
        location = LocationSpec(
            name="NYC Office",
            country="United States",
            start_date=date(2024, 6, 30),
            end_date=date(2024, 1, 15)  # Before start
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            location.validate()

        assert "date" in str(exc_info.value).lower()

    def test_location_spec_validation_invalid_max_students(self):
        """
        Test that zero/negative max_students raises validation error.

        WHY: Capacity must be positive if specified.
        """
        location = LocationSpec(
            name="NYC Office",
            country="United States",
            max_students=0
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            location.validate()

        assert "students" in str(exc_info.value).lower()


# =============================================================================
# INSTRUCTOR SPEC TESTS
# =============================================================================

class TestInstructorSpec:
    """
    Test suite for InstructorSpec domain entity.

    WHY: InstructorSpec defines instructor assignments and availability
    for schedule generation.
    """

    def test_create_valid_instructor_spec(self):
        """
        Test creating a valid instructor specification.

        WHY: Basic happy path for instructor assignment.
        """
        instructor = InstructorSpec(
            name="John Doe",
            email="john@example.com"
        )

        assert instructor.name == "John Doe"
        assert instructor.email == "john@example.com"
        assert instructor.role == "instructor"

    def test_instructor_spec_with_track_assignments(self):
        """
        Test instructor with track assignments.

        WHY: Instructors are assigned to specific tracks.
        """
        instructor = InstructorSpec(
            name="John Doe",
            email="john@example.com",
            track_names=["Backend Development", "DevOps"]
        )

        assert len(instructor.track_names) == 2
        assert "Backend Development" in instructor.track_names

    def test_instructor_spec_with_availability(self):
        """
        Test instructor with custom availability.

        WHY: Availability affects schedule generation.
        """
        instructor = InstructorSpec(
            name="John Doe",
            email="john@example.com",
            available_days=["Monday", "Wednesday", "Friday"],
            available_start_time=time(10, 0),
            available_end_time=time(18, 0)
        )

        assert len(instructor.available_days) == 3
        assert instructor.available_start_time == time(10, 0)

    def test_instructor_spec_validation_missing_name(self):
        """
        Test that missing name raises validation error.

        WHY: Instructor name is required.
        """
        instructor = InstructorSpec(name="", email="john@example.com")

        with pytest.raises(InvalidSpecificationException) as exc_info:
            instructor.validate()

        assert "name" in str(exc_info.value).lower()

    def test_instructor_spec_validation_invalid_email(self):
        """
        Test that invalid email raises validation error.

        WHY: Valid email is required for instructor.
        """
        instructor = InstructorSpec(name="John Doe", email="invalid-email")

        with pytest.raises(InvalidSpecificationException) as exc_info:
            instructor.validate()

        assert "email" in str(exc_info.value).lower()

    def test_instructor_spec_validation_invalid_time_range(self):
        """
        Test that end time before start time raises validation error.

        WHY: Time range must be logical.
        """
        instructor = InstructorSpec(
            name="John Doe",
            email="john@example.com",
            available_start_time=time(17, 0),
            available_end_time=time(9, 0)  # Before start
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            instructor.validate()

        assert "time" in str(exc_info.value).lower()

    def test_instructor_spec_validation_invalid_role(self):
        """
        Test that invalid role raises validation error.

        WHY: Role must be valid enum value.
        """
        instructor = InstructorSpec(
            name="John Doe",
            email="john@example.com",
            role="professor"  # Invalid
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            instructor.validate()

        assert "role" in str(exc_info.value).lower()


# =============================================================================
# STUDENT SPEC TESTS
# =============================================================================

class TestStudentSpec:
    """
    Test suite for StudentSpec domain entity.

    WHY: StudentSpec defines student enrollments for bulk creation.
    """

    def test_create_valid_student_spec(self):
        """
        Test creating a valid student specification.

        WHY: Basic happy path for student enrollment.
        """
        student = StudentSpec(
            name="Jane Smith",
            email="jane@example.com",
            track_name="Backend Development"
        )

        assert student.name == "Jane Smith"
        assert student.email == "jane@example.com"
        assert student.track_name == "Backend Development"

    def test_student_spec_with_location(self):
        """
        Test student with location assignment.

        WHY: Students are assigned to specific locations.
        """
        student = StudentSpec(
            name="Jane Smith",
            email="jane@example.com",
            track_name="Backend Development",
            location_name="New York Office"
        )

        assert student.location_name == "New York Office"

    def test_student_spec_validation_missing_track(self):
        """
        Test that missing track raises validation error.

        WHY: Track assignment is required for students.
        """
        student = StudentSpec(
            name="Jane Smith",
            email="jane@example.com",
            track_name=""
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            student.validate()

        assert "track" in str(exc_info.value).lower()


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

class TestScheduleConfig:
    """
    Test suite for ScheduleConfig value object.

    WHY: ScheduleConfig controls schedule generation parameters.
    """

    def test_create_default_schedule_config(self):
        """
        Test creating schedule config with defaults.

        WHY: Defaults should be sensible for typical use case.
        """
        config = ScheduleConfig()

        assert config.duration_weeks == 6
        assert len(config.working_days) == 5
        assert config.hours_per_day == 8

    def test_schedule_config_custom_values(self):
        """
        Test schedule config with custom values.

        WHY: Config must support customization.
        """
        config = ScheduleConfig(
            start_date=date(2024, 1, 15),
            duration_weeks=8,
            working_days=["Monday", "Tuesday", "Wednesday"],
            hours_per_day=6
        )

        assert config.duration_weeks == 8
        assert len(config.working_days) == 3
        assert config.hours_per_day == 6

    def test_schedule_config_validation_invalid_duration(self):
        """
        Test that zero duration raises validation error.

        WHY: Duration must be positive.
        """
        config = ScheduleConfig(duration_weeks=0)

        with pytest.raises(InvalidSpecificationException) as exc_info:
            config.validate()

        assert "duration" in str(exc_info.value).lower()

    def test_schedule_config_validation_empty_working_days(self):
        """
        Test that empty working days raises validation error.

        WHY: At least one working day is required.
        """
        config = ScheduleConfig(working_days=[])

        with pytest.raises(InvalidSpecificationException) as exc_info:
            config.validate()

        assert "working" in str(exc_info.value).lower()


class TestContentGenerationConfig:
    """
    Test suite for ContentGenerationConfig value object.

    WHY: Controls which content types are auto-generated.
    """

    def test_create_default_content_config(self):
        """
        Test creating content config with defaults.

        WHY: Defaults enable common content types.
        """
        config = ContentGenerationConfig()

        assert config.generate_syllabi is True
        assert config.generate_slides is True
        assert config.generate_quizzes is True
        assert config.generate_labs is True
        assert config.generate_assignments is False

    def test_content_config_custom_values(self):
        """
        Test content config with custom values.

        WHY: Admins can choose which content to generate.
        """
        config = ContentGenerationConfig(
            generate_syllabi=True,
            generate_slides=False,
            generate_quizzes=True,
            generate_labs=False
        )

        assert config.generate_slides is False
        assert config.generate_labs is False


class TestZoomConfig:
    """
    Test suite for ZoomConfig value object.

    WHY: Controls Zoom room creation settings.
    """

    def test_create_default_zoom_config(self):
        """
        Test creating Zoom config with defaults.

        WHY: Defaults enable typical Zoom setup.
        """
        config = ZoomConfig()

        assert config.create_zoom_rooms is True
        assert config.create_track_classrooms is True
        assert config.allow_manual_input is True

    def test_zoom_config_disabled(self):
        """
        Test Zoom config with rooms disabled.

        WHY: Some orgs don't use Zoom.
        """
        config = ZoomConfig(create_zoom_rooms=False)

        assert config.create_zoom_rooms is False


# =============================================================================
# PROJECT BUILDER SPEC TESTS
# =============================================================================

class TestProjectBuilderSpec:
    """
    Test suite for ProjectBuilderSpec - the main specification entity.

    WHY: ProjectBuilderSpec is the root entity containing all project
    configuration. Comprehensive testing ensures proper validation.
    """

    def test_create_minimal_project_spec(self):
        """
        Test creating minimal valid project specification.

        WHY: Minimum viable spec should be valid.
        """
        spec = ProjectBuilderSpec(
            name="Python Training Program",
            tracks=[
                TrackSpec(
                    name="Backend Development",
                    description="Server-side programming",
                    courses=[
                        CourseSpec(title="Python Basics", description="Intro")
                    ]
                )
            ]
        )

        # Should not raise
        spec.validate()

        assert spec.name == "Python Training Program"
        assert len(spec.tracks) == 1

    def test_create_full_project_spec(self):
        """
        Test creating full project specification with all components.

        WHY: Full spec should be valid and properly structured.
        """
        spec = ProjectBuilderSpec(
            name="JPMorgan Technology Analyst Program",
            description="6-week technology training program",
            locations=[
                LocationSpec(name="New York", country="United States"),
                LocationSpec(name="London", country="United Kingdom")
            ],
            tracks=[
                TrackSpec(
                    name="App Developers",
                    description="Application development track",
                    courses=[
                        CourseSpec(title="Python Basics", description="Intro"),
                        CourseSpec(title="Django Framework", description="Web framework")
                    ]
                ),
                TrackSpec(
                    name="Business Analysts",
                    description="Business analysis track",
                    courses=[
                        CourseSpec(title="Data Analysis", description="Data analysis with Python")
                    ]
                )
            ],
            instructors=[
                InstructorSpec(
                    name="John Doe",
                    email="john@example.com",
                    track_names=["App Developers"]
                )
            ],
            students=[
                StudentSpec(
                    name="Jane Smith",
                    email="jane@example.com",
                    track_name="App Developers",
                    location_name="New York"
                )
            ]
        )

        # Should not raise
        spec.validate()

        assert len(spec.locations) == 2
        assert len(spec.tracks) == 2
        assert spec.get_total_courses() == 3

    def test_project_spec_validation_missing_name(self):
        """
        Test that missing project name raises validation error.

        WHY: Project name is required.
        """
        spec = ProjectBuilderSpec(
            name="",
            tracks=[
                TrackSpec(name="Track", description="Desc", courses=[
                    CourseSpec(title="Course", description="Desc")
                ])
            ]
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            spec.validate()

        assert "name" in str(exc_info.value).lower()

    def test_project_spec_validation_missing_tracks(self):
        """
        Test that missing tracks raises validation error.

        WHY: At least one track is required.
        """
        spec = ProjectBuilderSpec(
            name="Test Project",
            tracks=[]
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            spec.validate()

        assert "track" in str(exc_info.value).lower()

    def test_project_spec_validation_instructor_unknown_track(self):
        """
        Test that instructor assigned to unknown track raises error.

        WHY: Cross-reference validation catches configuration errors.
        """
        spec = ProjectBuilderSpec(
            name="Test Project",
            tracks=[
                TrackSpec(name="Backend", description="Desc", courses=[
                    CourseSpec(title="Course", description="Desc")
                ])
            ],
            instructors=[
                InstructorSpec(
                    name="John Doe",
                    email="john@example.com",
                    track_names=["Frontend"]  # Doesn't exist
                )
            ]
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            spec.validate()

        assert "unknown track" in str(exc_info.value).lower()
        assert "Frontend" in str(exc_info.value)

    def test_project_spec_validation_student_unknown_track(self):
        """
        Test that student assigned to unknown track raises error.

        WHY: Cross-reference validation catches configuration errors.
        """
        spec = ProjectBuilderSpec(
            name="Test Project",
            tracks=[
                TrackSpec(name="Backend", description="Desc", courses=[
                    CourseSpec(title="Course", description="Desc")
                ])
            ],
            students=[
                StudentSpec(
                    name="Jane Smith",
                    email="jane@example.com",
                    track_name="Frontend"  # Doesn't exist
                )
            ]
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            spec.validate()

        assert "unknown track" in str(exc_info.value).lower()

    def test_project_spec_validation_student_unknown_location(self):
        """
        Test that student assigned to unknown location raises error.

        WHY: Cross-reference validation catches configuration errors.
        """
        spec = ProjectBuilderSpec(
            name="Test Project",
            locations=[
                LocationSpec(name="New York", country="United States")
            ],
            tracks=[
                TrackSpec(name="Backend", description="Desc", courses=[
                    CourseSpec(title="Course", description="Desc")
                ])
            ],
            students=[
                StudentSpec(
                    name="Jane Smith",
                    email="jane@example.com",
                    track_name="Backend",
                    location_name="London"  # Doesn't exist
                )
            ]
        )

        with pytest.raises(InvalidSpecificationException) as exc_info:
            spec.validate()

        assert "unknown location" in str(exc_info.value).lower()

    def test_project_spec_get_track_by_name(self):
        """
        Test getting track by name (case-insensitive).

        WHY: Helper methods simplify working with spec.
        """
        spec = ProjectBuilderSpec(
            name="Test",
            tracks=[
                TrackSpec(name="Backend Development", description="Desc", courses=[
                    CourseSpec(title="Course", description="Desc")
                ])
            ]
        )

        # Exact match
        track = spec.get_track_by_name("Backend Development")
        assert track is not None
        assert track.name == "Backend Development"

        # Case insensitive
        track = spec.get_track_by_name("backend development")
        assert track is not None

        # Not found
        track = spec.get_track_by_name("Frontend")
        assert track is None

    def test_project_spec_get_instructors_for_track(self):
        """
        Test getting instructors assigned to a track.

        WHY: Helper for schedule generation.
        """
        spec = ProjectBuilderSpec(
            name="Test",
            tracks=[
                TrackSpec(name="Backend", description="Desc", courses=[
                    CourseSpec(title="Course", description="Desc")
                ])
            ],
            instructors=[
                InstructorSpec(name="John", email="john@example.com", track_names=["Backend"]),
                InstructorSpec(name="Jane", email="jane@example.com", track_names=["Frontend"]),
                InstructorSpec(name="Bob", email="bob@example.com", track_names=["Backend", "DevOps"])
            ]
        )

        instructors = spec.get_instructors_for_track("Backend")

        assert len(instructors) == 2
        emails = [i.email for i in instructors]
        assert "john@example.com" in emails
        assert "bob@example.com" in emails

    def test_project_spec_get_summary(self):
        """
        Test getting specification summary.

        WHY: Summary is displayed in preview before creation.
        """
        spec = ProjectBuilderSpec(
            name="Test Project",
            locations=[
                LocationSpec(name="NYC", country="US"),
                LocationSpec(name="London", country="UK")
            ],
            tracks=[
                TrackSpec(name="Backend", description="Desc", courses=[
                    CourseSpec(title="Python", description="D"),
                    CourseSpec(title="Django", description="D")
                ]),
                TrackSpec(name="Frontend", description="Desc", courses=[
                    CourseSpec(title="React", description="D")
                ])
            ],
            instructors=[
                InstructorSpec(name="John", email="john@example.com", track_names=["Backend"])
            ],
            students=[
                StudentSpec(name="Jane", email="jane@example.com", track_name="Backend"),
                StudentSpec(name="Bob", email="bob@example.com", track_name="Frontend")
            ]
        )

        summary = spec.get_summary()

        assert summary["project_name"] == "Test Project"
        assert summary["locations_count"] == 2
        assert summary["tracks_count"] == 2
        assert summary["total_courses"] == 3
        assert summary["instructors_count"] == 1
        assert summary["students_count"] == 2

    def test_project_spec_to_dict_and_from_dict(self):
        """
        Test full serialization/deserialization roundtrip.

        WHY: Spec must survive storage and retrieval.
        """
        original = ProjectBuilderSpec(
            name="Test Project",
            organization_id=uuid4(),
            locations=[
                LocationSpec(name="NYC", country="US")
            ],
            tracks=[
                TrackSpec(name="Backend", description="Desc", courses=[
                    CourseSpec(title="Python", description="Intro")
                ])
            ],
            instructors=[
                InstructorSpec(name="John", email="john@example.com", track_names=["Backend"])
            ],
            students=[
                StudentSpec(name="Jane", email="jane@example.com", track_name="Backend")
            ]
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = ProjectBuilderSpec.from_dict(data)

        assert restored.name == original.name
        assert str(restored.organization_id) == str(original.organization_id)
        assert len(restored.locations) == 1
        assert len(restored.tracks) == 1
        assert len(restored.instructors) == 1
        assert len(restored.students) == 1


# =============================================================================
# SCHEDULE ENTITY TESTS
# =============================================================================

class TestScheduleEntry:
    """
    Test suite for ScheduleEntry value object.

    WHY: ScheduleEntry represents individual scheduled sessions.
    """

    def test_create_schedule_entry(self):
        """
        Test creating a schedule entry.

        WHY: Basic creation test.
        """
        entry = ScheduleEntry(
            track_name="Backend Development",
            course_title="Python Basics",
            session_number=1,
            date=date(2024, 1, 15),
            start_time=time(9, 0),
            end_time=time(11, 0),
            instructor_email="john@example.com"
        )

        assert entry.track_name == "Backend Development"
        assert entry.course_title == "Python Basics"
        assert entry.session_number == 1


class TestConflict:
    """
    Test suite for Conflict value object.

    WHY: Conflict represents scheduling conflicts detected during generation.
    """

    def test_create_conflict(self):
        """
        Test creating a conflict.

        WHY: Basic creation test.
        """
        conflict = Conflict(
            conflict_type=ConflictType.INSTRUCTOR_DOUBLE_BOOKING,
            description="John Doe is scheduled for two classes at the same time",
            severity="error",
            affected_date=date(2024, 1, 15),
            affected_instructor="john@example.com"
        )

        assert conflict.conflict_type == ConflictType.INSTRUCTOR_DOUBLE_BOOKING
        assert conflict.severity == "error"


class TestScheduleProposal:
    """
    Test suite for ScheduleProposal value object.

    WHY: ScheduleProposal aggregates schedule entries and conflicts.
    """

    def test_create_schedule_proposal(self):
        """
        Test creating a schedule proposal.

        WHY: Basic creation test.
        """
        proposal = ScheduleProposal(
            entries=[
                ScheduleEntry(track_name="Backend", course_title="Python", session_number=1,
                              date=date(2024, 1, 15), start_time=time(9, 0), end_time=time(11, 0))
            ],
            is_valid=True
        )

        assert len(proposal.entries) == 1
        assert proposal.is_valid is True
        assert proposal.has_errors() is False

    def test_schedule_proposal_with_conflicts(self):
        """
        Test schedule proposal with conflicts.

        WHY: Conflicts affect validity.
        """
        proposal = ScheduleProposal(
            entries=[],
            conflicts=[
                Conflict(
                    conflict_type=ConflictType.INSTRUCTOR_DOUBLE_BOOKING,
                    description="Double booking",
                    severity="error"
                )
            ],
            is_valid=False
        )

        assert proposal.has_errors() is True


# =============================================================================
# RESULT ENTITY TESTS
# =============================================================================

class TestProjectCreationResult:
    """
    Test suite for ProjectCreationResult value object.

    WHY: Result tracks what was created during bulk creation.
    """

    def test_create_success_result(self):
        """
        Test creating a success result.

        WHY: Basic success scenario.
        """
        result = ProjectCreationResult(
            success=True,
            project_id=uuid4(),
            counts={
                "projects": 1,
                "subprojects": 2,
                "tracks": 3,
                "courses": 10,
                "instructors": 5,
                "students": 50,
                "enrollments": 50,
                "zoom_rooms": 8,
                "content_jobs": 1
            }
        )

        assert result.success is True
        assert result.counts["courses"] == 10

    def test_create_partial_failure_result(self):
        """
        Test creating a partial failure result.

        WHY: Some operations may fail while others succeed.
        """
        result = ProjectCreationResult(
            success=False,
            project_id=uuid4(),
            errors=[
                {"type": "zoom_error", "message": "Failed to create room"}
            ]
        )

        assert result.success is False
        assert len(result.errors) == 1


# =============================================================================
# EXCEPTION TESTS
# =============================================================================

class TestExceptions:
    """
    Test suite for custom exceptions.

    WHY: Exceptions must have proper structure and messages.
    """

    def test_project_builder_exception(self):
        """
        Test base ProjectBuilderException.

        WHY: Base exception establishes pattern for others.
        """
        exc = ProjectBuilderException(
            message="Something went wrong",
            code="TEST_ERROR",
            context={"key": "value"}
        )

        assert exc.message == "Something went wrong"
        assert exc.code == "TEST_ERROR"
        assert exc.context["key"] == "value"

        result = exc.to_dict()
        assert result["error"] == "TEST_ERROR"
        assert result["message"] == "Something went wrong"

    def test_invalid_specification_exception(self):
        """
        Test InvalidSpecificationException with field.

        WHY: Field info helps users fix issues.
        """
        exc = InvalidSpecificationException(
            message="Title is required",
            field="title"
        )

        assert exc.field == "title"
        assert exc.code == "INVALID_SPECIFICATION"

    def test_schedule_conflict_exception(self):
        """
        Test ScheduleConflictException with conflicts.

        WHY: Conflict details help users resolve issues.
        """
        conflicts = [
            Conflict(
                conflict_type=ConflictType.INSTRUCTOR_DOUBLE_BOOKING,
                description="Double booking"
            )
        ]

        exc = ScheduleConflictException(
            message="Unresolvable conflicts",
            conflicts=conflicts
        )

        assert len(exc.conflicts) == 1
        assert exc.code == "SCHEDULE_CONFLICT"

    def test_roster_parse_exception(self):
        """
        Test RosterParseException with row info.

        WHY: Row info helps users fix specific rows.
        """
        exc = RosterParseException(
            message="Invalid email format",
            filename="instructors.csv",
            row=5
        )

        assert exc.filename == "instructors.csv"
        assert exc.row == 5


# =============================================================================
# ENUMERATION TESTS
# =============================================================================

class TestEnumerations:
    """
    Test suite for enumeration types.

    WHY: Enums must have expected values.
    """

    def test_project_builder_state_values(self):
        """
        Test ProjectBuilderState enum values.

        WHY: State machine relies on these values.
        """
        assert ProjectBuilderState.INITIAL.value == "initial"
        assert ProjectBuilderState.COMPLETE.value == "complete"

    def test_content_type_values(self):
        """
        Test ContentType enum values.

        WHY: Content generation uses these values.
        """
        assert ContentType.SYLLABUS.value == "syllabus"
        assert ContentType.QUIZ.value == "quiz"

    def test_conflict_type_values(self):
        """
        Test ConflictType enum values.

        WHY: Conflict detection uses these values.
        """
        assert ConflictType.INSTRUCTOR_DOUBLE_BOOKING.value == "instructor_double_booking"

    def test_zoom_room_type_values(self):
        """
        Test ZoomRoomType enum values.

        WHY: Zoom room creation uses these values.
        """
        assert ZoomRoomType.CLASSROOM.value == "classroom"
        assert ZoomRoomType.OFFICE_HOURS.value == "office_hours"
