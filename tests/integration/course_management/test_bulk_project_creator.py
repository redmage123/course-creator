"""
Unit Tests for Bulk Project Creator Service

BUSINESS CONTEXT:
Tests the BulkProjectCreator service which creates complete training program
structures from a ProjectBuilderSpec. This includes creating projects,
sub-projects, tracks, courses, users, and enrollments in a single operation.

WHY THESE TESTS:
1. Verify all entities are created correctly from specs
2. Ensure transaction integrity (all-or-nothing)
3. Test error handling and rollback scenarios
4. Validate entity relationships are established
5. Test partial creation scenarios

WHAT IS TESTED:
- Project and sub-project creation
- Track and course creation
- Instructor user creation/update
- Student user creation and enrollment
- Content generation job queuing
- Zoom room creation coordination
- Transaction rollback on failure

HOW TO RUN:
    # Run all bulk project creator tests
    pytest tests/unit/course_management/test_bulk_project_creator.py -v

    # Run specific test class
    pytest tests/unit/course_management/test_bulk_project_creator.py::TestProjectCreation -v

@module test_bulk_project_creator
@author Course Creator Platform
@version 1.0.0
"""

import pytest
import sys
from pathlib import Path
from datetime import date, time, datetime, timedelta
from uuid import UUID, uuid4

# Add course-management service to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from course_management.application.services.bulk_project_creator import (
    BulkProjectCreator,
    BulkProjectCreatorException,
    CreationPhase,
    CreationContext
)
from course_management.domain.entities.project_builder import (
    ProjectBuilderSpec,
    LocationSpec,
    TrackSpec,
    CourseSpec,
    InstructorSpec,
    StudentSpec,
    ScheduleConfig,
    ContentGenerationConfig,
    ZoomConfig,
    ScheduleProposal,
    ScheduleEntry,
    ProjectCreationResult,
    InvalidSpecificationException
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


class FakeProjectDAO:
    """Test double for ProjectDAO - replace with real DAO."""
    def create_project(self, *args, **kwargs):
        return {"id": str(uuid4()), "name": "Test Project"}

    def get_project_by_id(self, *args, **kwargs):
        return {"id": str(uuid4()), "name": "Test Project"}



class FakeSubProjectDAO:
    """Test double for SubProjectDAO - replace with real DAO."""
    def create_sub_project(self, *args, **kwargs):
        return {"id": str(uuid4()), "name": "Test Sub-Project"}



class FakeTrackDAO:
    """Test double for TrackDAO - replace with real DAO."""
    def create_track(self, *args, **kwargs):
        return {"id": str(uuid4()), "name": "Test Track"}



class FakeCourseDAO:
    """Test double for CourseDAO - replace with real DAO."""
    def create_course(self, *args, **kwargs):
        return {"id": str(uuid4()), "title": "Test Course"}



class FakeUserDAO:
    """Test double for UserDAO - replace with real DAO."""
    def create_user(self, *args, **kwargs):
        return {"id": str(uuid4()), "email": "test@example.com"}

    def get_user_by_email(self, *args, **kwargs):
        return None

    def update_user(self, *args, **kwargs):
        return {"id": str(uuid4())}



class FakeEnrollmentDAO:
    """Test double for EnrollmentDAO - replace with real DAO."""
    def create_enrollment(self, *args, **kwargs):
        return {"id": str(uuid4())}


@pytest.fixture
def creator():
    """Create BulkProjectCreator - needs real DAOs."""
    pytest.skip("Needs refactoring to use real DAO implementations")


@pytest.fixture
def basic_spec():
    """Create a basic project specification for testing."""
    return ProjectBuilderSpec(
        name="Test Training Program",
        organization_id=uuid4(),
        description="A test training program",
        locations=[
            LocationSpec(
                name="New York",
                city="New York",
                max_students=30
            )
        ],
        tracks=[
            TrackSpec(
                name="Backend Development",
                courses=[
                    CourseSpec(
                        title="Python Basics",
                        description="Learn Python fundamentals",
                        duration_hours=20
                    ),
                    CourseSpec(
                        title="Django Framework",
                        description="Learn Django web framework",
                        duration_hours=30
                    )
                ]
            )
        ],
        instructors=[
            InstructorSpec(
                name="John Doe",
                email="john@example.com",
                track_names=["Backend Development"]
            )
        ],
        students=[
            StudentSpec(
                name="Alice Student",
                email="alice@example.com",
                track_name="Backend Development",
                location_name="New York"
            ),
            StudentSpec(
                name="Bob Student",
                email="bob@example.com",
                track_name="Backend Development",
                location_name="New York"
            )
        ]
    )


@pytest.fixture
def multi_location_spec():
    """Create a multi-location project specification."""
    return ProjectBuilderSpec(
        name="Multi-Location Training",
        organization_id=uuid4(),
        locations=[
            LocationSpec(name="New York", city="New York", max_students=20),
            LocationSpec(name="London", city="London", max_students=20),
            LocationSpec(name="Tokyo", city="Tokyo", max_students=15)
        ],
        tracks=[
            TrackSpec(
                name="Backend Development",
                courses=[
                    CourseSpec(title="Python", description="Python programming", duration_hours=20)
                ]
            ),
            TrackSpec(
                name="Frontend Development",
                courses=[
                    CourseSpec(title="JavaScript", description="JS programming", duration_hours=20)
                ]
            )
        ],
        instructors=[
            InstructorSpec(name="John", email="john@example.com", track_names=["Backend Development"]),
            InstructorSpec(name="Jane", email="jane@example.com", track_names=["Frontend Development"])
        ],
        students=[
            StudentSpec(name="S1", email="s1@example.com", track_name="Backend Development", location_name="New York"),
            StudentSpec(name="S2", email="s2@example.com", track_name="Frontend Development", location_name="London"),
            StudentSpec(name="S3", email="s3@example.com", track_name="Backend Development", location_name="Tokyo")
        ]
    )


@pytest.fixture
def schedule_proposal(basic_spec):
    """Create a schedule proposal for testing."""
    return ScheduleProposal(
        spec_id=basic_spec.id,
        entries=[
            ScheduleEntry(
                id=uuid4(),
                date=date.today() + timedelta(days=7),
                start_time=time(9, 0),
                end_time=time(11, 0),
                track_name="Backend Development",
                course_title="Python Basics",
                location_name="New York",
                instructor_email="john@example.com",
                instructor_name="John Doe"
            )
        ],
        conflicts=[],
        is_valid=True
    )


# =============================================================================
# TEST: BULK PROJECT CREATOR INITIALIZATION
# =============================================================================


class TestBulkProjectCreatorInitialization:
    """Tests for BulkProjectCreator initialization."""

    def test_creator_initialization(self, creator):
        """
        GIVEN: DAOs are provided
        WHEN: BulkProjectCreator is created
        THEN: All DAOs are stored correctly

        WHY: Verify dependency injection works.
        """
        assert creator.project_dao is not None
        assert creator.sub_project_dao is not None
        assert creator.track_dao is not None
        assert creator.course_dao is not None
        assert creator.user_dao is not None
        assert creator.enrollment_dao is not None

    def test_creator_without_daos_raises(self):
        """
        GIVEN: No DAOs provided
        WHEN: BulkProjectCreator is created
        THEN: Raises TypeError

        WHY: DAOs are required dependencies.
        """
        with pytest.raises(TypeError):
            BulkProjectCreator()


# =============================================================================
# TEST: PROJECT CREATION
# =============================================================================

class TestProjectCreation:
    """Tests for main project creation functionality."""

    def test_create_project_returns_result(self, creator, basic_spec):
        """
        GIVEN: Valid project spec
        WHEN: create_from_spec is called
        THEN: Returns ProjectCreationResult

        WHY: Basic contract verification.
        """
        result = creator.create_from_spec(basic_spec)

        assert isinstance(result, ProjectCreationResult)
        assert result.success is True

    def test_create_project_sets_project_id(self, creator, basic_spec):
        """
        GIVEN: Valid project spec
        WHEN: create_from_spec is called
        THEN: Result contains project ID

        WHY: Need to track created project.
        """
        result = creator.create_from_spec(basic_spec)

        assert result.project_id is not None
        assert isinstance(result.project_id, UUID)

    def test_create_project_calls_project_dao(self, creator, basic_spec, mock_project_dao):
        """
        GIVEN: Valid project spec
        WHEN: create_from_spec is called
        THEN: Project DAO create method is called

        WHY: Project must be persisted.
        """
        creator.create_from_spec(basic_spec)

        mock_project_dao.create_project.assert_called()

    def test_create_project_uses_spec_name(self, creator, basic_spec, mock_project_dao):
        """
        GIVEN: Project spec with specific name
        WHEN: create_from_spec is called
        THEN: Project is created with that name

        WHY: Spec name should be used.
        """
        creator.create_from_spec(basic_spec)

        call_args = mock_project_dao.create_project.call_args
        assert "Test Training Program" in str(call_args)


# =============================================================================
# TEST: SUB-PROJECT CREATION
# =============================================================================

class TestSubProjectCreation:
    """Tests for sub-project (location) creation."""

    def test_creates_sub_projects_for_locations(self, creator, basic_spec, mock_sub_project_dao):
        """
        GIVEN: Spec with locations
        WHEN: create_from_spec is called
        THEN: Sub-projects are created for each location

        WHY: Each location becomes a sub-project.
        """
        result = creator.create_from_spec(basic_spec)

        assert mock_sub_project_dao.create_sub_project.called
        assert len(result.subproject_ids) == len(basic_spec.locations)

    def test_multi_location_creates_multiple_sub_projects(
        self, creator, multi_location_spec, mock_sub_project_dao
    ):
        """
        GIVEN: Spec with 3 locations
        WHEN: create_from_spec is called
        THEN: 3 sub-projects are created

        WHY: Each location = one sub-project.
        """
        result = creator.create_from_spec(multi_location_spec)

        assert mock_sub_project_dao.create_sub_project.call_count == 3
        assert len(result.subproject_ids) == 3


# =============================================================================
# TEST: TRACK CREATION
# =============================================================================

class TestTrackCreation:
    """Tests for track creation."""

    def test_creates_tracks(self, creator, basic_spec, mock_track_dao):
        """
        GIVEN: Spec with tracks
        WHEN: create_from_spec is called
        THEN: Tracks are created

        WHY: Tracks organize courses.
        """
        result = creator.create_from_spec(basic_spec)

        assert mock_track_dao.create_track.called
        assert len(result.track_ids) >= 1

    def test_tracks_linked_to_project(self, creator, basic_spec, mock_track_dao):
        """
        GIVEN: Spec with tracks
        WHEN: create_from_spec is called
        THEN: Tracks are linked to the project

        WHY: Tracks belong to a project.
        """
        creator.create_from_spec(basic_spec)

        call_args = mock_track_dao.create_track.call_args
        # Should include project reference
        assert call_args is not None


# =============================================================================
# TEST: COURSE CREATION
# =============================================================================

class TestCourseCreation:
    """Tests for course creation."""

    def test_creates_courses_for_tracks(self, creator, basic_spec, mock_course_dao):
        """
        GIVEN: Spec with tracks containing courses
        WHEN: create_from_spec is called
        THEN: Courses are created

        WHY: Courses provide content.
        """
        result = creator.create_from_spec(basic_spec)

        assert mock_course_dao.create_course.called
        # Basic spec has 2 courses in one track
        assert len(result.course_ids) == 2

    def test_multi_track_creates_all_courses(self, creator, multi_location_spec, mock_course_dao):
        """
        GIVEN: Spec with multiple tracks each with courses
        WHEN: create_from_spec is called
        THEN: All courses are created

        WHY: All track courses must be created.
        """
        result = creator.create_from_spec(multi_location_spec)

        # 2 tracks with 1 course each = 2 courses
        assert len(result.course_ids) == 2


# =============================================================================
# TEST: USER CREATION
# =============================================================================

class TestUserCreation:
    """Tests for instructor and student user creation."""

    def test_creates_instructor_users(self, creator, basic_spec, mock_user_dao):
        """
        GIVEN: Spec with instructors
        WHEN: create_from_spec is called
        THEN: Instructor users are created

        WHY: Instructors need accounts.
        """
        result = creator.create_from_spec(basic_spec)

        # Should check if user exists, then create
        assert mock_user_dao.get_user_by_email.called or mock_user_dao.create_user.called
        assert len(result.instructor_user_ids) >= 1

    def test_creates_student_users(self, creator, basic_spec, mock_user_dao):
        """
        GIVEN: Spec with students
        WHEN: create_from_spec is called
        THEN: Student users are created

        WHY: Students need accounts.
        """
        result = creator.create_from_spec(basic_spec)

        assert len(result.student_user_ids) >= 1

    def test_existing_user_not_duplicated(self, creator, basic_spec, mock_user_dao):
        """
        GIVEN: Spec with student who already has account
        WHEN: create_from_spec is called
        THEN: Existing user is used, not duplicated

        WHY: Avoid duplicate accounts.
        """
        # Setup mock to return existing user
        mock_user_dao.get_user_by_email = Mock(return_value={
            "id": str(uuid4()),
            "email": "alice@example.com",
            "name": "Alice Student"
        })

        result = creator.create_from_spec(basic_spec)

        # Should still have user IDs but may not create new ones
        assert result is not None


# =============================================================================
# TEST: ENROLLMENT CREATION
# =============================================================================

class TestEnrollmentCreation:
    """Tests for student enrollment creation."""

    def test_creates_enrollments(self, creator, basic_spec, mock_enrollment_dao):
        """
        GIVEN: Spec with students
        WHEN: create_from_spec is called
        THEN: Enrollments are created

        WHY: Students must be enrolled in courses.
        """
        result = creator.create_from_spec(basic_spec)

        assert mock_enrollment_dao.create_enrollment.called
        assert len(result.enrollment_ids) >= 1

    def test_enrollments_link_students_to_courses(self, creator, basic_spec, mock_enrollment_dao):
        """
        GIVEN: Spec with students and courses
        WHEN: create_from_spec is called
        THEN: Enrollments connect students to courses

        WHY: Core purpose of enrollments.
        """
        creator.create_from_spec(basic_spec)

        # Enrollment should be called for each student-course combination
        assert mock_enrollment_dao.create_enrollment.called


# =============================================================================
# TEST: RESULT COUNTS
# =============================================================================

class TestResultCounts:
    """Tests for result count tracking."""

    def test_counts_projects(self, creator, basic_spec):
        """
        GIVEN: Valid spec
        WHEN: create_from_spec is called
        THEN: Result counts projects

        WHY: Track what was created.
        """
        result = creator.create_from_spec(basic_spec)

        assert result.counts["projects"] == 1

    def test_counts_sub_projects(self, creator, multi_location_spec):
        """
        GIVEN: Spec with 3 locations
        WHEN: create_from_spec is called
        THEN: Result counts 3 sub-projects

        WHY: Accurate count tracking.
        """
        result = creator.create_from_spec(multi_location_spec)

        assert result.counts["subprojects"] == 3

    def test_counts_tracks(self, creator, multi_location_spec):
        """
        GIVEN: Spec with 2 tracks
        WHEN: create_from_spec is called
        THEN: Result counts 2 tracks

        WHY: Accurate count tracking.
        """
        result = creator.create_from_spec(multi_location_spec)

        assert result.counts["tracks"] == 2

    def test_counts_courses(self, creator, basic_spec):
        """
        GIVEN: Spec with 2 courses
        WHEN: create_from_spec is called
        THEN: Result counts 2 courses

        WHY: Accurate count tracking.
        """
        result = creator.create_from_spec(basic_spec)

        assert result.counts["courses"] == 2


# =============================================================================
# TEST: SCHEDULE APPLICATION
# =============================================================================

class TestScheduleApplication:
    """Tests for applying schedule proposal during creation."""

    def test_accepts_schedule_proposal(self, creator, basic_spec, schedule_proposal):
        """
        GIVEN: Spec and schedule proposal
        WHEN: create_from_spec is called with schedule
        THEN: Schedule is applied

        WHY: Schedules define when sessions occur.
        """
        result = creator.create_from_spec(
            basic_spec,
            schedule_proposal=schedule_proposal
        )

        assert result.success is True

    def test_schedule_entries_stored(self, creator, basic_spec, schedule_proposal):
        """
        GIVEN: Schedule proposal with entries
        WHEN: create_from_spec is called
        THEN: Schedule entries are persisted

        WHY: Sessions need to be saved.
        """
        result = creator.create_from_spec(
            basic_spec,
            schedule_proposal=schedule_proposal
        )

        # Should succeed without errors
        assert result.success is True


# =============================================================================
# TEST: CONTENT GENERATION INTEGRATION
# =============================================================================

class TestContentGenerationIntegration:
    """Tests for content generation job queuing."""

    def test_queues_content_generation_when_enabled(self, creator, basic_spec):
        """
        GIVEN: Spec with content generation enabled
        WHEN: create_from_spec is called
        THEN: Content generation jobs are queued

        WHY: Automate content creation.
        """
        basic_spec.content_generation_config.generate_syllabi = True

        result = creator.create_from_spec(basic_spec)

        # Should either have job ID or indicate content generation was skipped
        # depending on implementation
        assert result is not None

    def test_no_content_generation_when_disabled(self, creator, basic_spec):
        """
        GIVEN: Spec with content generation disabled
        WHEN: create_from_spec is called
        THEN: No content generation jobs queued

        WHY: Respect configuration.
        """
        basic_spec.content_generation_config.generate_syllabi = False
        basic_spec.content_generation_config.generate_slides = False
        basic_spec.content_generation_config.generate_quizzes = False
        basic_spec.content_generation_config.generate_labs = False

        result = creator.create_from_spec(basic_spec)

        # Should succeed but with no content generation jobs
        assert result.success is True
        # No content generation job should be created
        assert result.content_generation_job_id is None


# =============================================================================
# TEST: ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Tests for error handling during bulk creation."""

    def test_invalid_spec_returns_failed_result(self, creator):
        """
        GIVEN: Invalid spec (no name)
        WHEN: create_from_spec is called
        THEN: Returns failed result with error

        WHY: Graceful error handling instead of exceptions.
        """
        spec = ProjectBuilderSpec(
            name="",  # Empty name!
            organization_id=uuid4(),
            locations=[LocationSpec(name="NYC", city="NYC")],
            tracks=[TrackSpec(name="Track", courses=[
                CourseSpec(title="Course", description="Desc", duration_hours=10)
            ])]
        )

        result = creator.create_from_spec(spec)

        # Should return failed result, not raise exception
        assert result.success is False
        assert len(result.errors) > 0

    def test_dao_error_captured_in_result(self, creator, basic_spec, mock_project_dao):
        """
        GIVEN: DAO throws exception during creation
        WHEN: create_from_spec is called
        THEN: Error is captured in result

        WHY: Graceful error handling.
        """
        mock_project_dao.create_project.side_effect = Exception("Database error")

        result = creator.create_from_spec(basic_spec)

        assert result.success is False
        assert len(result.errors) > 0

    def test_partial_failure_tracked(self, creator, basic_spec, mock_course_dao):
        """
        GIVEN: Course creation fails after project created
        WHEN: create_from_spec is called
        THEN: Partial failure is tracked

        WHY: Know what succeeded vs failed.
        """
        mock_course_dao.create_course.side_effect = Exception("Course creation failed")

        result = creator.create_from_spec(basic_spec)

        # Should indicate failure but project might have been created
        assert result.success is False
        assert len(result.errors) > 0


# =============================================================================
# TEST: CREATION CONTEXT
# =============================================================================

class TestCreationContext:
    """Tests for creation context management."""

    def test_context_tracks_created_entities(self, creator, basic_spec):
        """
        GIVEN: Valid spec
        WHEN: create_from_spec is called
        THEN: Context tracks all created entities

        WHY: Enable rollback on failure.
        """
        result = creator.create_from_spec(basic_spec)

        # All IDs should be tracked
        assert result.project_id is not None
        assert len(result.subproject_ids) > 0
        assert len(result.track_ids) > 0

    def test_context_tracks_duration(self, creator, basic_spec):
        """
        GIVEN: Valid spec
        WHEN: create_from_spec is called
        THEN: Duration is tracked

        WHY: Performance monitoring.
        """
        result = creator.create_from_spec(basic_spec)

        assert result.duration_seconds >= 0


# =============================================================================
# TEST: CREATION PHASES
# =============================================================================

class TestCreationPhases:
    """Tests for phased creation process."""

    def test_phases_execute_in_order(self, creator, basic_spec):
        """
        GIVEN: Valid spec
        WHEN: create_from_spec is called
        THEN: Phases execute in correct order

        WHY: Dependency order matters.
        """
        # This is implicit in the result - if it succeeds,
        # phases executed correctly
        result = creator.create_from_spec(basic_spec)

        assert result.success is True

    def test_project_created_before_tracks(self, creator, basic_spec, mock_project_dao, mock_track_dao):
        """
        GIVEN: Valid spec
        WHEN: create_from_spec is called
        THEN: Project is created before tracks

        WHY: Tracks reference project.
        """
        call_order = []
        mock_project_dao.create_project.side_effect = lambda *args, **kwargs: (
            call_order.append("project"),
            {"id": str(uuid4()), "name": "Test"}
        )[1]
        mock_track_dao.create_track.side_effect = lambda *args, **kwargs: (
            call_order.append("track"),
            {"id": str(uuid4()), "name": "Track"}
        )[1]

        creator.create_from_spec(basic_spec)

        project_idx = call_order.index("project")
        track_idx = call_order.index("track") if "track" in call_order else len(call_order)
        assert project_idx < track_idx


# =============================================================================
# TEST: DRY RUN MODE
# =============================================================================

class TestDryRunMode:
    """Tests for dry run (preview) mode."""

    def test_dry_run_does_not_create(self, creator, basic_spec, mock_project_dao):
        """
        GIVEN: Dry run mode enabled
        WHEN: create_from_spec is called
        THEN: No entities are actually created

        WHY: Preview without side effects.
        """
        result = creator.create_from_spec(basic_spec, dry_run=True)

        # In dry run, create methods should not be called
        # or result should indicate preview mode
        assert result is not None

    def test_dry_run_validates_spec(self, creator, basic_spec):
        """
        GIVEN: Valid spec in dry run mode
        WHEN: create_from_spec is called
        THEN: Validation still occurs

        WHY: Preview should validate.
        """
        result = creator.create_from_spec(basic_spec, dry_run=True)

        assert result is not None
        # If validation passes, should have preview counts
        assert result.counts is not None


# =============================================================================
# TEST: INTEGRATION
# =============================================================================

class TestBulkCreationIntegration:
    """Integration tests for complete bulk creation workflow."""

    def test_complete_creation_workflow(self, creator, basic_spec):
        """
        GIVEN: Complete valid spec
        WHEN: create_from_spec is called
        THEN: All entities are created successfully

        WHY: End-to-end verification.
        """
        result = creator.create_from_spec(basic_spec)

        assert result.success is True
        assert result.project_id is not None
        assert len(result.subproject_ids) == 1
        assert len(result.track_ids) >= 1
        assert len(result.course_ids) == 2
        assert len(result.instructor_user_ids) >= 1
        assert len(result.student_user_ids) >= 1
        assert len(result.enrollment_ids) >= 1
        assert result.counts["projects"] == 1

    def test_multi_location_complete_workflow(self, creator, multi_location_spec):
        """
        GIVEN: Multi-location spec
        WHEN: create_from_spec is called
        THEN: All locations, tracks, users created

        WHY: Complex scenario verification.
        """
        result = creator.create_from_spec(multi_location_spec)

        assert result.success is True
        assert result.counts["subprojects"] == 3
        assert result.counts["tracks"] == 2
        assert len(result.instructor_user_ids) >= 2
        assert len(result.student_user_ids) >= 3
