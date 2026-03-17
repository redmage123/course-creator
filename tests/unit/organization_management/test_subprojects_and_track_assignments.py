"""
TDD Tests for Sub-Projects and Track Assignment System

BUSINESS PURPOSE:
Test the optional sub-project hierarchy and track assignment system that allows:
- Optional sub-projects under main projects
- Tracks can belong to project OR sub-project
- Minimum 1 instructor per track
- Student-instructor assignment with load balancing
- Org admin can be an instructor

TEST STRATEGY (RED PHASE):
All tests written BEFORE implementation - these should FAIL initially
Following strict TDD: RED → GREEN → REFACTOR
"""

import pytest
from uuid import uuid4
from datetime import datetime


# ==============================================================================
# RED PHASE: Sub-Project Creation and Validation
# ==============================================================================

class TestSubProjectCreation:
    """Test optional sub-project creation under main projects"""

    def test_create_sub_project_under_main_project(self, test_organization, test_project):
        """
        RED: Should create sub-project with parent_project_id

        BUSINESS VALUE:
        Organizations can create optional sub-projects (Q1, Q2, Q3, Q4)
        to organize tracks hierarchically
        """
        # Arrange
        org_id = test_organization
        main_project_id = test_project['id']

        # Act
        sub_project = create_sub_project(
            organization_id=org_id,
            parent_project_id=main_project_id,
            name="Q1 2025 Training",
            slug="q1-2025-training"
        )

        # Assert
        assert sub_project is not None
        assert str(sub_project['parent_project_id']) == str(main_project_id)
        assert sub_project['is_sub_project'] is True
        assert sub_project['name'] == "Q1 2025 Training"

    def test_sub_project_must_have_parent(self):
        """
        RED: Should require parent_project_id when is_sub_project=True

        BUSINESS RULE:
        Sub-projects must reference a parent project
        """
        # Arrange
        org_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Sub-project must have parent_project_id"):
            create_sub_project(
                organization_id=org_id,
                parent_project_id=None,  # Invalid: no parent
                name="Orphan Sub-Project",
                slug="orphan"
            )

    def test_main_project_cannot_have_parent(self):
        """
        RED: Should prevent main projects from having parent_project_id

        BUSINESS RULE:
        Only sub-projects can have parents (no recursive hierarchy)
        """
        # Arrange
        org_id = uuid4()
        parent_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Main project cannot have parent"):
            create_project(
                organization_id=org_id,
                parent_project_id=parent_id,  # Invalid for main project
                is_sub_project=False,
                name="Invalid Main Project",
                slug="invalid-main"
            )

    def test_list_sub_projects_for_main_project(self, test_organization, test_project, test_sub_project):
        """
        RED: Should retrieve all sub-projects for a main project

        BUSINESS VALUE:
        Org admins can view all sub-projects under a main project
        """
        # Arrange
        org_id = test_organization
        main_project_id = test_project['id']

        # Act
        sub_projects = list_sub_projects(
            organization_id=org_id,
            parent_project_id=main_project_id
        )

        # Assert
        assert isinstance(sub_projects, list)
        assert len(sub_projects) >= 1  # At least the test_sub_project fixture
        for sub_proj in sub_projects:
            assert str(sub_proj['parent_project_id']) == str(main_project_id)
            assert sub_proj['is_sub_project'] is True


# ==============================================================================
# RED PHASE: Track Assignment (Project OR Sub-Project)
# ==============================================================================

class TestTrackAssignment:
    """Test tracks can belong to project OR sub-project (not both)"""

    def test_create_track_under_main_project(self, test_organization, test_project):
        """
        RED: Should create track directly under main project

        BUSINESS VALUE:
        When no sub-projects exist, tracks go directly under main project
        """
        # Arrange
        org_id = test_organization
        project_id = test_project['id']

        # Act
        track = create_track(
            organization_id=org_id,
            project_id=project_id,
            sub_project_id=None,  # No sub-project
            name="Application Development",
            slug="app-dev"
        )

        # Assert
        assert track is not None
        assert str(track['project_id']) == str(project_id)
        assert track['sub_project_id'] is None

    def test_create_track_under_sub_project(self, test_organization, test_sub_project):
        """
        RED: Should create track under sub-project

        BUSINESS VALUE:
        When sub-projects exist, tracks belong to specific sub-project
        """
        # Arrange
        org_id = test_organization
        sub_project_id = test_sub_project['id']

        # Act
        track = create_track(
            organization_id=org_id,
            project_id=None,  # No direct project
            sub_project_id=sub_project_id,
            name="Data Science Track",
            slug="data-science"
        )

        # Assert
        assert track is not None
        assert track['project_id'] is None
        assert str(track['sub_project_id']) == str(sub_project_id)

    def test_track_must_reference_project_or_subproject(self):
        """
        RED: Should require either project_id OR sub_project_id (not both, not neither)

        BUSINESS RULE:
        Track must belong to exactly one: project XOR sub-project
        """
        # Arrange
        org_id = uuid4()

        # Act & Assert - Neither
        with pytest.raises(ValueError, match="Track must reference project OR sub-project"):
            create_track(
                organization_id=org_id,
                project_id=None,
                sub_project_id=None,  # Invalid: neither
                name="Orphan Track",
                slug="orphan"
            )

        # Act & Assert - Both
        project_id = uuid4()
        sub_project_id = uuid4()
        with pytest.raises(ValueError, match="Track cannot reference both project AND sub-project"):
            create_track(
                organization_id=org_id,
                project_id=project_id,
                sub_project_id=sub_project_id,  # Invalid: both
                name="Confused Track",
                slug="confused"
            )


# ==============================================================================
# RED PHASE: Track Instructor Assignment
# ==============================================================================

class TestTrackInstructorAssignment:
    """Test instructor assignment to tracks with minimum 1 requirement"""

    def test_assign_instructor_to_track(self, test_track, test_instructor):
        """
        RED: Should assign instructor to track with communication links

        BUSINESS VALUE:
        Instructors assigned to tracks can provide Zoom/Teams/Slack links
        """
        # Arrange
        track_id = test_track['id']
        instructor_id = test_instructor

        # Act
        assignment = assign_instructor_to_track(
            track_id=track_id,
            instructor_id=instructor_id,
            zoom_link="https://zoom.us/j/123456789",
            teams_link="https://teams.microsoft.com/l/channel/...",
            slack_links=["#dev-track-q1", "@john.doe"]
        )

        # Assert
        assert assignment is not None
        assert str(assignment['track_id']) == str(track_id)
        assert str(assignment['user_id']) == str(instructor_id)
        assert assignment['zoom_link'] == "https://zoom.us/j/123456789"
        assert assignment['teams_link'] is not None
        assert len(assignment['slack_links']) == 2

    def test_track_must_have_at_least_one_instructor(self):
        """
        RED: Should enforce minimum 1 instructor per track

        BUSINESS RULE:
        Cannot create track without at least 1 instructor
        Cannot remove last instructor from track
        """
        # Arrange
        track_id = uuid4()

        # Act & Assert - No instructors
        instructors = get_track_instructors(track_id)
        assert len(instructors) == 0

        with pytest.raises(ValueError, match="Track must have at least 1 instructor"):
            validate_track_has_instructors(track_id)

    def test_cannot_remove_last_instructor_from_track(self, test_track, test_instructor):
        """
        RED: Should prevent removing last instructor

        BUSINESS RULE:
        Track must always have at least 1 instructor assigned
        """
        # Arrange
        track_id = test_track['id']
        instructor_id = test_instructor

        # Setup: Track has 1 instructor
        assign_instructor_to_track(track_id, instructor_id)

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot remove last instructor"):
            remove_instructor_from_track(track_id, instructor_id)

    def test_can_remove_instructor_when_multiple_exist(self, test_track):
        """
        RED: Should allow removing instructor when 2+ remain

        BUSINESS LOGIC:
        Can remove instructors as long as at least 1 remains
        """
        # Arrange
        track_id = test_track['id']
        instructor1_id = uuid4()
        instructor2_id = uuid4()

        # Setup: Track has 2 instructors
        assign_instructor_to_track(track_id, instructor1_id)
        assign_instructor_to_track(track_id, instructor2_id)

        # Act
        remove_instructor_from_track(track_id, instructor1_id)

        # Assert
        instructors = get_track_instructors(track_id)
        assert len(instructors) == 1
        assert str(instructors[0]['user_id']) == str(instructor2_id)

    def test_org_admin_can_be_assigned_as_instructor(self, test_track):
        """
        RED: Should allow org admin to be assigned as instructor

        BUSINESS VALUE:
        Org admins can teach tracks in addition to managing them
        """
        # Arrange
        track_id = test_track['id']
        org_admin_id = uuid4()  # User with org_admin role

        # Act
        assignment = assign_instructor_to_track(
            track_id=track_id,
            instructor_id=org_admin_id,
            zoom_link="https://zoom.us/j/admin-office-hours"
        )

        # Assert
        assert assignment is not None
        assert str(assignment['user_id']) == str(org_admin_id)


# ==============================================================================
# RED PHASE: Track Student Assignment
# ==============================================================================

class TestTrackStudentAssignment:
    """Test student assignment to tracks with instructor assignment"""

    def test_assign_student_to_track_with_instructor(self, test_track, test_instructor, test_student):
        """
        RED: Should assign student to track and assign to instructor

        BUSINESS VALUE:
        Students are assigned to specific instructor for personalized guidance
        """
        # Arrange
        track_id = test_track['id']
        student_id = test_student
        instructor_id = test_instructor

        # Setup: Assign instructor to track first
        assign_instructor_to_track(track_id, instructor_id)

        # Act
        assignment = assign_student_to_track(
            track_id=track_id,
            student_id=student_id,
            instructor_id=instructor_id
        )

        # Assert
        assert assignment is not None
        assert str(assignment['track_id']) == str(track_id)
        assert str(assignment['student_id']) == str(student_id)
        assert str(assignment['assigned_instructor_id']) == str(instructor_id)

    def test_assigned_instructor_must_be_track_instructor(self, test_track, test_student):
        """
        RED: Should enforce FK constraint for instructor assignment

        BUSINESS RULE:
        Student can only be assigned to instructors who teach that track
        """
        # Arrange
        track_id = test_track['id']
        student_id = test_student
        random_instructor_id = uuid4()  # Not assigned to this track

        # Act & Assert
        with pytest.raises(ValueError, match="Instructor not assigned to this track"):
            assign_student_to_track(
                track_id=track_id,
                student_id=student_id,
                instructor_id=random_instructor_id  # Invalid
            )

    def test_reassign_student_to_different_instructor(self, test_track, test_student):
        """
        RED: Should allow org admin to reassign student to different instructor

        BUSINESS VALUE:
        Load balancing or student preference accommodations
        """
        # Arrange
        track_id = test_track['id']
        student_id = test_student
        old_instructor_id = uuid4()
        new_instructor_id = uuid4()
        org_admin_id = uuid4()

        # Setup: Assign both instructors to track first
        assign_instructor_to_track(track_id, old_instructor_id)
        assign_instructor_to_track(track_id, new_instructor_id)

        # Setup: Student initially assigned to old instructor
        assign_student_to_track(track_id, student_id, old_instructor_id)

        # Act
        reassignment = reassign_student_to_instructor(
            track_id=track_id,
            student_id=student_id,
            new_instructor_id=new_instructor_id,
            reassigned_by=org_admin_id
        )

        # Assert
        assert str(reassignment['assigned_instructor_id']) == str(new_instructor_id)
        assert reassignment['last_reassigned_at'] is not None


# ==============================================================================
# RED PHASE: Load Balancing Algorithm
# ==============================================================================

class TestLoadBalancingAlgorithm:
    """Test auto-balance student distribution across instructors"""

    def test_auto_balance_flag_defaults_to_false(self, test_organization):
        """
        RED: Should default auto_balance_students to FALSE

        BUSINESS RULE:
        Auto-balancing is opt-in, not automatic
        """
        # Arrange & Act
        project = create_project(
            organization_id=test_organization,
            name="Test Project",
            slug="test-project"
        )

        # Assert
        assert project['auto_balance_students'] is False

    def test_enable_auto_balance_for_project(self, test_project):
        """
        RED: Should allow org admin to enable auto-balance

        BUSINESS VALUE:
        Org admin can turn on auto-balancing per project
        """
        # Arrange
        project_id = test_project['id']

        # Act
        updated_project = update_project(
            project_id=project_id,
            auto_balance_students=True
        )

        # Assert
        assert updated_project['auto_balance_students'] is True

    def test_balance_students_across_instructors_evenly(self, test_track):
        """
        RED: Should distribute students evenly across instructors

        ALGORITHM:
        - 3 instructors, 10 students
        - Distribution: 4, 3, 3 (as even as possible)

        BUSINESS VALUE:
        Fair workload distribution for instructors
        """
        # Arrange
        track_id = test_track['id']
        instructor1_id = uuid4()
        instructor2_id = uuid4()
        instructor3_id = uuid4()
        student_ids = [uuid4() for _ in range(10)]

        # Setup: 3 instructors assigned to track
        assign_instructor_to_track(track_id, instructor1_id)
        assign_instructor_to_track(track_id, instructor2_id)
        assign_instructor_to_track(track_id, instructor3_id)

        # Act
        assignments = auto_balance_students(
            track_id=track_id,
            student_ids=student_ids
        )

        # Assert
        instructor_loads = count_students_per_instructor(track_id)
        assert instructor_loads[str(instructor1_id)] in [3, 4]  # Even distribution
        assert instructor_loads[str(instructor2_id)] in [3, 4]
        assert instructor_loads[str(instructor3_id)] in [3, 4]
        assert sum(instructor_loads.values()) == 10

    def test_balance_considers_existing_student_load(self, test_track):
        """
        RED: Should account for existing students when balancing

        ALGORITHM:
        - Instructor A: 5 students (existing)
        - Instructor B: 2 students (existing)
        - Instructor C: 0 students (existing)
        - 6 new students to assign
        - Result: A=6, B=5, C=5 (balanced)

        BUSINESS VALUE:
        Fair distribution considering current workload
        """
        # Arrange
        track_id = test_track['id']
        instructor_a_id = uuid4()
        instructor_b_id = uuid4()
        instructor_c_id = uuid4()

        # Setup: Assign all 3 instructors to track
        assign_instructor_to_track(track_id, instructor_a_id)
        assign_instructor_to_track(track_id, instructor_b_id)
        assign_instructor_to_track(track_id, instructor_c_id)

        # Setup: Existing students
        for _ in range(5):
            assign_student_to_track(track_id, uuid4(), instructor_a_id)
        for _ in range(2):
            assign_student_to_track(track_id, uuid4(), instructor_b_id)

        # New students to balance
        new_student_ids = [uuid4() for _ in range(6)]

        # Act
        auto_balance_students(track_id, new_student_ids)

        # Assert
        loads = count_students_per_instructor(track_id)
        # Should prioritize instructors with fewer students
        assert loads[str(instructor_c_id)] >= 2  # Gets priority (had 0)
        assert loads[str(instructor_b_id)] >= 3  # Gets priority (had 2)
        assert abs(loads[str(instructor_a_id)] - loads[str(instructor_c_id)]) <= 1  # Balanced

    def test_balance_only_when_flag_enabled(self, test_organization):
        """
        RED: Should NOT auto-balance when flag is FALSE

        BUSINESS RULE:
        Auto-balancing only occurs when explicitly enabled
        """
        # Arrange: Create project with auto_balance_students = FALSE
        project = create_project(
            organization_id=test_organization,
            name="Test Project No Auto Balance",
            slug="test-no-auto-balance"
        )
        assert project['auto_balance_students'] is False

        # Create track under this project
        track = create_track(
            organization_id=test_organization,
            project_id=project['id'],
            name="Test Track",
            slug="test-track-no-balance"
        )

        # Assign instructor (to avoid "must have 1 instructor" error)
        instructor_id = uuid4()
        assign_instructor_to_track(track['id'], instructor_id)

        # Act
        student_ids = [uuid4() for _ in range(5)]

        # Should NOT auto-balance because flag is disabled
        with pytest.raises(ValueError, match="Auto-balance not enabled"):
            auto_balance_students(track['id'], student_ids)


# ==============================================================================
# GREEN PHASE: Import Implementation from Service Module
# ==============================================================================

from organization_management.application.services.track_management_service import (
    create_project,
    create_sub_project,
    list_sub_projects,
    create_track,
    assign_instructor_to_track,
    remove_instructor_from_track,
    get_track_instructors,
    validate_track_has_instructors,
    assign_student_to_track,
    reassign_student_to_instructor,
    update_project,
    auto_balance_students,
    count_students_per_instructor
)
