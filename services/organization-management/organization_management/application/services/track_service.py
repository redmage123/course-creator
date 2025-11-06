"""
Track Service - Business Logic for Track Management and Auto-Enrollment
Single Responsibility: Track business operations and student enrollment automation
Open/Closed: Extensible through dependency injection
Dependency Inversion: Depends on DAO abstractions (converted from repository pattern)
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from organization_management.domain.entities.track import Track, TrackStatus, TrackType
from organization_management.data_access.organization_dao import OrganizationManagementDAO


class TrackService:
    """
    Service class for track business operations including automatic enrollment.

    BUSINESS PURPOSE:
    Manages learning tracks within projects, including creation, configuration,
    lifecycle management, and student auto-enrollment based on target audience.

    CORE RESPONSIBILITIES:
    - Track CRUD operations (create, read, update, delete, archive)
    - Track lifecycle management (draft → active → archived states)
    - Target audience matching and auto-enrollment logic
    - Track prerequisites validation for student eligibility
    - Track sequencing and ordering within projects
    - Track statistics and analytics

    WHAT IS A TRACK:
    A track is a structured learning path within a project that groups related courses.
    Example: "Python Bootcamp" project might have tracks:
    - "Beginner Python Track" (target: new developers)
    - "Advanced Python Track" (target: experienced developers)
    - "Data Science Track" (target: data analysts)

    AUTO-ENROLLMENT FEATURE:
    Tracks can be configured with target_audience tags (e.g., "developer", "manager").
    When enabled (auto_enroll_enabled=True), students matching the audience
    are automatically enrolled in the track, eliminating manual enrollment.

    DESIGN PATTERNS:
    - Single Responsibility: Handles track business logic only
    - Dependency Inversion: Depends on DAO abstraction
    - Service Layer: Orchestrates domain entities and persistence

    Args:
        organization_dao: Data access object for track persistence operations
    """

    def __init__(self, organization_dao: OrganizationManagementDAO):
        """
        Initialize track service with data access object.

        Args:
            organization_dao: OrganizationManagementDAO for database operations
        """
        self._organization_dao = organization_dao
        self._logger = logging.getLogger(__name__)

    async def create_track(self, project_id: UUID, name: str, slug: str,
                           description: str = None, track_type: TrackType = TrackType.SEQUENTIAL,
                           target_audience: List[str] = None, prerequisites: List[str] = None,
                           duration_weeks: int = None, max_enrolled: int = None,
                           learning_objectives: List[str] = None, skills_taught: List[str] = None,
                           difficulty_level: str = "beginner", auto_enroll_enabled: bool = True,
                           settings: Dict[str, Any] = None, created_by: UUID = None) -> Track:
        """
        Create a new learning track within a project.

        WHAT: Creates track entity with metadata, audience targeting, and auto-enrollment
        WHY: Organization admins need to define learning paths for different student locations

        BUSINESS CONTEXT:
        Tracks organize courses into coherent learning paths. Organization admins create
        tracks to serve different audiences (e.g., "Developer Track", "Manager Track").
        Auto-enrollment streamlines student onboarding by matching them to appropriate tracks.

        TRACK LIFECYCLE:
        New tracks start in DRAFT status. Admin must explicitly activate them
        using activate_track() before students can enroll.

        Args:
            project_id: Parent project UUID
            name: Track display name (e.g., "Beginner Python Track")
            slug: URL-safe identifier (e.g., "beginner-python")
            description: Detailed track description
            track_type: SEQUENTIAL (ordered courses) or FLEXIBLE (any order)
            target_audience: List of audience tags (e.g., ["developer", "beginner"])
            prerequisites: Required background knowledge/skills
            duration_weeks: Estimated completion time in weeks
            max_enrolled: Maximum student enrollment (None = unlimited)
            learning_objectives: What students will learn
            skills_taught: Skills students will acquire
            difficulty_level: "beginner", "intermediate", "advanced"
            auto_enroll_enabled: Auto-enroll students matching target_audience
            settings: Additional configuration options
            created_by: UUID of user creating the track

        Returns:
            Created Track entity with DRAFT status

        Raises:
            ValueError: If slug already exists in project or validation fails
            Exception: If database operation fails
        """
        try:
            # Check if slug already exists within project
            if await self._organization_dao.exists_by_project_and_slug(project_id, slug):
                raise ValueError(f"Track with slug '{slug}' already exists in this project")

            # Determine display order
            existing_tracks = await self._organization_dao.get_by_project(project_id)
            display_order = len(existing_tracks) + 1

            # Get organization_id from project
            organization_id = await self._organization_dao.get_project_organization_id(project_id)
            if not organization_id:
                raise ValueError(f"Project {project_id} not found or has no organization")

            # Create track entity
            track = Track(
                organization_id=organization_id,
                project_id=project_id,
                name=name,
                slug=slug,
                description=description,
                track_type=track_type,
                target_audience=target_audience or [],
                prerequisites=prerequisites or [],
                duration_weeks=duration_weeks,
                max_enrolled=max_enrolled,
                learning_objectives=learning_objectives or [],
                skills_taught=skills_taught or [],
                difficulty_level=difficulty_level,
                display_order=display_order,
                auto_enroll_enabled=auto_enroll_enabled,
                settings=settings or {},
                created_by=created_by
            )

            # Validate track
            if not track.is_valid():
                raise ValueError("Invalid track data")

            # Persist track
            created_track = await self._organization_dao.create(track)

            self._logger.info(f"Track created successfully: {created_track.slug} in project {project_id}")
            return created_track

        except Exception as e:
            self._logger.error(f"Error creating track: {str(e)}")
            raise

    async def get_track(self, track_id: UUID) -> Optional[Track]:
        """Get track by ID"""
        try:
            return await self._organization_dao.get_by_id(track_id)
        except Exception as e:
            self._logger.error(f"Error getting track {track_id}: {str(e)}")
            raise

    async def get_track_by_project_and_slug(self, project_id: UUID, slug: str) -> Optional[Track]:
        """Get track by project and slug"""
        try:
            return await self._organization_dao.get_by_project_and_slug(project_id, slug)
        except Exception as e:
            self._logger.error(f"Error getting track by project {project_id} and slug {slug}: {str(e)}")
            raise

    async def update_track(self, track_id: UUID, name: str = None, description: str = None,
                           track_type: TrackType = None, target_audience: List[str] = None,
                           prerequisites: List[str] = None, duration_weeks: int = None,
                           max_enrolled: int = None, learning_objectives: List[str] = None,
                           skills_taught: List[str] = None, difficulty_level: str = None,
                           auto_enroll_enabled: bool = None, settings: Dict[str, Any] = None) -> Track:
        """Update track"""
        try:
            # Get existing track
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            # Update track information
            track.update_info(
                name=name,
                description=description,
                track_type=track_type,
                target_audience=target_audience,
                prerequisites=prerequisites,
                duration_weeks=duration_weeks,
                max_enrolled=max_enrolled,
                learning_objectives=learning_objectives,
                skills_taught=skills_taught,
                difficulty_level=difficulty_level,
                auto_enroll_enabled=auto_enroll_enabled,
                settings=settings
            )

            # Validate updated track
            if not track.is_valid():
                raise ValueError("Invalid track data")

            # Persist changes
            updated_track = await self._organization_dao.update(track)

            self._logger.info(f"Track updated successfully: {track.slug}")
            return updated_track

        except Exception as e:
            self._logger.error(f"Error updating track {track_id}: {str(e)}")
            raise

    async def activate_track(self, track_id: UUID) -> Track:
        """
        Activate track to make it available for student enrollment.

        WHAT: Changes track status from DRAFT to ACTIVE
        WHY: Tracks must be explicitly activated before students can enroll

        BUSINESS CONTEXT:
        Organization admins create tracks in DRAFT status to configure content
        before making them visible to students. Activation is the "go-live" moment
        that makes the track available for enrollment.

        ACTIVATION REQUIREMENTS:
        Track can only be activated if:
        - Current status is DRAFT
        - Track validation passes (name, slug, prerequisites valid)
        - Track has required metadata configured

        POST-ACTIVATION:
        - Track appears in course catalog for students
        - Auto-enrollment triggers for matching students
        - Instructors can be assigned to track

        Args:
            track_id: UUID of track to activate

        Returns:
            Updated Track entity with ACTIVE status

        Raises:
            ValueError: If track not found or cannot be activated
            Exception: If database operation fails
        """
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            if not track.can_activate():
                raise ValueError("Track cannot be activated - check status and validation")

            track.activate()
            updated_track = await self._organization_dao.update(track)

            self._logger.info(f"Track activated: {track.slug}")
            return updated_track

        except Exception as e:
            self._logger.error(f"Error activating track {track_id}: {str(e)}")
            raise

    async def archive_track(self, track_id: UUID) -> Track:
        """Archive track"""
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            track.archive()
            updated_track = await self._organization_dao.update(track)

            self._logger.info(f"Track archived: {track.slug}")
            return updated_track

        except Exception as e:
            self._logger.error(f"Error archiving track {track_id}: {str(e)}")
            raise

    async def delete_track(self, track_id: UUID) -> bool:
        """Delete track"""
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            result = await self._organization_dao.delete(track_id)

            if result:
                self._logger.info(f"Track deleted successfully: {track.slug}")

            return result

        except Exception as e:
            self._logger.error(f"Error deleting track {track_id}: {str(e)}")
            raise

    async def get_tracks_by_project(self, project_id: UUID, status: TrackStatus = None) -> List[Track]:
        """Get tracks by project, optionally filtered by status"""
        try:
            if status:
                return await self._organization_dao.get_by_project_and_status(project_id, status)
            else:
                return await self._organization_dao.get_by_project(project_id)
        except Exception as e:
            self._logger.error(f"Error getting tracks for project {project_id}: {str(e)}")
            raise

    async def get_active_tracks_by_project(self, project_id: UUID) -> List[Track]:
        """Get active tracks by project"""
        try:
            return await self._organization_dao.get_by_project_and_status(project_id, TrackStatus.ACTIVE)
        except Exception as e:
            self._logger.error(f"Error getting active tracks for project {project_id}: {str(e)}")
            raise

    async def get_tracks_for_auto_enrollment(self, project_id: UUID) -> List[Track]:
        """
        Get tracks that have auto-enrollment enabled for student matching.

        WHAT: Retrieves active tracks with auto_enroll_enabled=True
        WHY: Used by enrollment service to auto-assign students to matching tracks

        BUSINESS CONTEXT:
        When a new student joins an organization, the system automatically:
        1. Gets all auto-enrollment tracks in their projects
        2. Matches student attributes against track target_audience
        3. Enrolls student in matching tracks

        This eliminates manual enrollment and ensures students are placed
        in appropriate learning paths automatically.

        Args:
            project_id: UUID of project to filter tracks

        Returns:
            List of active Track entities with auto-enrollment enabled

        Raises:
            Exception: If database query fails
        """
        try:
            return await self._organization_dao.get_active_tracks_with_auto_enroll(project_id)
        except Exception as e:
            self._logger.error(f"Error getting auto-enrollment tracks for project {project_id}: {str(e)}")
            raise

    async def get_tracks_by_target_audience(self, target_audience: str, project_id: UUID = None) -> List[Track]:
        """
        Get tracks targeting a specific audience segment.

        WHAT: Retrieves tracks matching a target audience tag
        WHY: Enables filtering tracks by audience for enrollment and discovery

        BUSINESS CONTEXT:
        Tracks can target multiple audience segments (e.g., "developer", "manager", "analyst").
        This method helps:
        - Auto-enrollment: Find tracks for students with specific roles
        - Course catalog: Show relevant tracks to different user types
        - Reporting: Analyze track distribution by audience

        EXAMPLE:
        Student with role "developer" → System finds all tracks with
        "developer" in target_audience → Auto-enrolls student

        Args:
            target_audience: Audience tag to match (e.g., "developer", "manager")
            project_id: Optional project filter (None = search all projects)

        Returns:
            List of Track entities targeting the specified audience

        Raises:
            Exception: If database query fails
        """
        try:
            return await self._organization_dao.get_by_target_audience(target_audience, project_id)
        except Exception as e:
            self._logger.error(f"Error getting tracks for audience {target_audience}: {str(e)}")
            raise

    async def get_tracks_by_difficulty(self, difficulty_level: str, project_id: UUID = None) -> List[Track]:
        """Get tracks by difficulty level"""
        try:
            return await self._organization_dao.get_by_difficulty_level(difficulty_level, project_id)
        except Exception as e:
            self._logger.error(f"Error getting tracks for difficulty {difficulty_level}: {str(e)}")
            raise

    async def search_tracks(self, project_id: UUID, query: str) -> List[Track]:
        """Search tracks within project"""
        try:
            return await self._organization_dao.search_by_project(project_id, query)
        except Exception as e:
            self._logger.error(f"Error searching tracks in project {project_id}: {str(e)}")
            raise

    async def reorder_tracks(self, project_id: UUID, track_orders: List[Dict[str, int]]) -> List[Track]:
        """Reorder tracks within project"""
        try:
            updated_tracks = []

            for track_order in track_orders:
                track_id = track_order.get('track_id')
                new_order = track_order.get('sequence_order')

                track = await self._organization_dao.get_by_id(track_id)
                if track and track.project_id == project_id:
                    track.sequence_order = new_order
                    updated_track = await self._organization_dao.update(track)
                    updated_tracks.append(updated_track)

            self._logger.info(f"Reordered {len(updated_tracks)} tracks in project {project_id}")
            return updated_tracks

        except Exception as e:
            self._logger.error(f"Error reordering tracks in project {project_id}: {str(e)}")
            raise

    async def get_track_statistics(self, track_id: UUID) -> Dict[str, Any]:
        """Get track statistics"""
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            # Basic stats for now - could be extended with enrollment counts, completion rates, etc.
            return {
                "id": str(track.id),
                "name": track.name,
                "slug": track.slug,
                "status": track.status.value,
                "track_type": track.track_type.value,
                "difficulty_level": track.difficulty_level,
                "target_audience": track.get_target_audience_display(),
                "skills_taught": track.get_skills_display(),
                "estimated_completion": track.estimate_completion_time(),
                "auto_enroll_enabled": track.auto_enroll_enabled,
                "sequence_order": track.sequence_order,
                "created_at": track.created_at.isoformat() if track.created_at else None,
                "updated_at": track.updated_at.isoformat() if track.updated_at else None
            }

        except Exception as e:
            self._logger.error(f"Error getting track statistics {track_id}: {str(e)}")
            raise

    async def validate_track_prerequisites(self, track_id: UUID, student_background: List[str]) -> Dict[str, Any]:
        """
        Validate if student meets track prerequisites for enrollment eligibility.

        WHAT: Checks if student's background matches track's required prerequisites
        WHY: Ensures students have necessary knowledge before enrolling in advanced tracks

        BUSINESS CONTEXT:
        Prerequisites prevent students from enrolling in tracks they're not ready for.
        This improves learning outcomes by ensuring proper sequencing.

        VALIDATION LOGIC:
        - Track prerequisites: ["python_basics", "sql_fundamentals"]
        - Student background: ["python_basics", "git"]
        - Result: FAIL - missing "sql_fundamentals"

        USE CASES:
        - Pre-enrollment validation before allowing track enrollment
        - Recommendation engine suggesting prerequisite tracks
        - Student dashboard showing blocked tracks with missing prerequisites

        Args:
            track_id: UUID of track to validate against
            student_background: List of skills/knowledge student possesses

        Returns:
            Dict containing:
                - meets_requirements: bool (True if all prerequisites met)
                - required_prerequisites: List of all track prerequisites
                - missing_prerequisites: List of prerequisites student lacks
                - student_background: Echo of student's background for reference

        Raises:
            ValueError: If track not found
            Exception: If database query fails
        """
        try:
            track = await self._organization_dao.get_by_id(track_id)
            if not track:
                raise ValueError(f"Track with ID {track_id} not found")

            missing_prerequisites = []
            for prerequisite in track.prerequisites:
                if prerequisite not in student_background:
                    missing_prerequisites.append(prerequisite)

            meets_requirements = len(missing_prerequisites) == 0

            return {
                "meets_requirements": meets_requirements,
                "required_prerequisites": track.prerequisites,
                "missing_prerequisites": missing_prerequisites,
                "student_background": student_background
            }

        except Exception as e:
            self._logger.error(f"Error validating prerequisites for track {track_id}: {str(e)}")
            raise
