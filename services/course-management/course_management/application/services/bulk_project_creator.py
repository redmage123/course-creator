"""
Bulk Project Creator Service

BUSINESS CONTEXT:
This service handles the bulk creation of training programs from a
ProjectBuilderSpec. It coordinates the creation of all related entities:
projects, sub-projects, tracks, courses, users, and enrollments in a
single transactional operation.

WHY THIS EXISTS:
Creating a complete training program involves multiple database operations
across different entity types. This service:
1. Ensures all-or-nothing creation (transaction integrity)
2. Handles relationships between entities correctly
3. Provides detailed feedback on what was created
4. Supports preview/dry-run mode for validation
5. Coordinates with external services (content generation, Zoom)

WHAT THIS SERVICE DOES:
- Creates project from spec metadata
- Creates sub-projects for each location
- Creates tracks within the project
- Creates courses within tracks
- Creates or updates instructor user accounts
- Creates student user accounts
- Creates enrollments for students in courses
- Optionally queues content generation jobs
- Optionally creates Zoom rooms

HOW IT WORKS:
1. Validate the specification
2. Create project entity
3. Create sub-projects for locations
4. Create tracks
5. Create courses
6. Create/update instructor users
7. Create student users
8. Create enrollments
9. Apply schedule if provided
10. Queue content generation if enabled
11. Return detailed result

TRANSACTION HANDLING:
The service tracks all created entities in a CreationContext. If any
phase fails, the context can be used for cleanup/rollback.

@module bulk_project_creator
@author Course Creator Platform
@version 1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from uuid import UUID, uuid4

from course_management.domain.entities.project_builder import (
    ProjectBuilderSpec,
    ProjectCreationResult,
    ScheduleProposal,
    InvalidSpecificationException
)

logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class BulkProjectCreatorException(Exception):
    """
    Base exception for bulk project creator errors.

    WHY: Provides specific error type for bulk creation failures,
    distinguishing them from other application errors.

    WHAT: Contains error message, phase where failure occurred,
    and context about what was already created.

    HOW: Raised during creation phases, caught by calling code
    for error handling and rollback.
    """

    def __init__(
        self,
        message: str,
        phase: Optional['CreationPhase'] = None,
        context: Optional['CreationContext'] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize bulk project creator exception.

        Args:
            message: Human-readable error description
            phase: The creation phase where failure occurred
            context: CreationContext with entities created before failure
            original_error: The underlying exception that caused the failure
        """
        super().__init__(message)
        self.message = message
        self.phase = phase
        self.context = context
        self.original_error = original_error

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": "BULK_CREATION_ERROR",
            "message": self.message,
            "phase": self.phase.value if self.phase else None,
            "original_error": str(self.original_error) if self.original_error else None
        }


# =============================================================================
# ENUMERATIONS
# =============================================================================

class CreationPhase(str, Enum):
    """
    Phases of the bulk creation process.

    WHY: Tracks progress through multi-step creation for
    error reporting and potential rollback.

    WHAT: Enumerates all phases in creation order.

    HOW: Used by CreationContext and error handling.
    """
    VALIDATION = "validation"
    PROJECT = "project"
    SUB_PROJECTS = "sub_projects"
    TRACKS = "tracks"
    COURSES = "courses"
    INSTRUCTORS = "instructors"
    STUDENTS = "students"
    ENROLLMENTS = "enrollments"
    SCHEDULE = "schedule"
    CONTENT_GENERATION = "content_generation"
    ZOOM_ROOMS = "zoom_rooms"
    COMPLETE = "complete"


# =============================================================================
# CREATION CONTEXT
# =============================================================================

@dataclass
class CreationContext:
    """
    Tracks entities created during bulk creation.

    WHY: Enables tracking of what was created for:
    - Detailed result reporting
    - Potential rollback on failure
    - Debugging and auditing

    WHAT: Contains all created entity IDs organized by type.

    HOW: Updated as each phase creates entities.
    """

    # Tracking IDs
    project_id: Optional[UUID] = None
    subproject_ids: List[UUID] = field(default_factory=list)
    track_ids: List[UUID] = field(default_factory=list)
    course_ids: List[UUID] = field(default_factory=list)
    instructor_user_ids: List[UUID] = field(default_factory=list)
    student_user_ids: List[UUID] = field(default_factory=list)
    enrollment_ids: List[UUID] = field(default_factory=list)
    zoom_room_ids: List[str] = field(default_factory=list)

    # Mapping for lookups
    track_name_to_id: Dict[str, UUID] = field(default_factory=dict)
    course_title_to_id: Dict[str, UUID] = field(default_factory=dict)
    user_email_to_id: Dict[str, UUID] = field(default_factory=dict)
    location_name_to_subproject_id: Dict[str, UUID] = field(default_factory=dict)

    # Phase tracking
    current_phase: CreationPhase = CreationPhase.VALIDATION
    completed_phases: List[CreationPhase] = field(default_factory=list)

    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Errors and warnings
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str, phase: CreationPhase, details: Dict[str, Any] = None):
        """Add an error to the context."""
        self.errors.append({
            "message": message,
            "phase": phase.value,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })

    def complete_phase(self, phase: CreationPhase):
        """Mark a phase as complete."""
        if phase not in self.completed_phases:
            self.completed_phases.append(phase)

    def get_duration_seconds(self) -> float:
        """Get total duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


# =============================================================================
# BULK PROJECT CREATOR SERVICE
# =============================================================================

class BulkProjectCreator:
    """
    Service for bulk creation of training programs.

    WHY: Orchestrates complex multi-entity creation with
    proper ordering, error handling, and result tracking.

    WHAT: Creates complete training programs from specs:
    - Projects, sub-projects, tracks, courses
    - User accounts for instructors and students
    - Enrollments linking students to courses
    - Schedule entries for sessions
    - Content generation jobs
    - Zoom rooms

    HOW: Executes creation phases in dependency order,
    tracking progress in CreationContext.

    USAGE:
        creator = BulkProjectCreator(
            project_dao=project_dao,
            sub_project_dao=sub_project_dao,
            track_dao=track_dao,
            course_dao=course_dao,
            user_dao=user_dao,
            enrollment_dao=enrollment_dao
        )

        result = creator.create_from_spec(spec)
        if result.success:
            print(f"Created project: {result.project_id}")
        else:
            print(f"Errors: {result.errors}")
    """

    def __init__(
        self,
        project_dao,
        sub_project_dao,
        track_dao,
        course_dao,
        user_dao,
        enrollment_dao,
        schedule_dao=None,
        content_generation_service=None,
        zoom_service=None
    ):
        """
        Initialize BulkProjectCreator with required DAOs.

        WHY: Dependency injection enables testing and flexibility.

        WHAT: Stores references to all required data access objects.

        HOW: DAOs are injected at construction time.

        Args:
            project_dao: DAO for project persistence
            sub_project_dao: DAO for sub-project persistence
            track_dao: DAO for track persistence
            course_dao: DAO for course persistence
            user_dao: DAO for user persistence
            enrollment_dao: DAO for enrollment persistence
            schedule_dao: Optional DAO for schedule persistence
            content_generation_service: Optional service for content generation
            zoom_service: Optional service for Zoom room creation
        """
        self.project_dao = project_dao
        self.sub_project_dao = sub_project_dao
        self.track_dao = track_dao
        self.course_dao = course_dao
        self.user_dao = user_dao
        self.enrollment_dao = enrollment_dao
        self.schedule_dao = schedule_dao
        self.content_generation_service = content_generation_service
        self.zoom_service = zoom_service

        logger.info("BulkProjectCreator initialized with all required DAOs")

    def create_from_spec(
        self,
        spec: ProjectBuilderSpec,
        schedule_proposal: Optional[ScheduleProposal] = None,
        dry_run: bool = False
    ) -> ProjectCreationResult:
        """
        Create a complete training program from specification.

        WHY: Main entry point for bulk creation operation.

        WHAT: Orchestrates all creation phases and returns result.

        HOW:
        1. Initialize creation context
        2. Validate specification
        3. Execute creation phases in order
        4. Handle errors gracefully
        5. Return detailed result

        Args:
            spec: Complete project specification
            schedule_proposal: Optional approved schedule
            dry_run: If True, validate only without creating

        Returns:
            ProjectCreationResult with success status and details

        Raises:
            InvalidSpecificationException: If spec fails validation
            BulkProjectCreatorException: If creation fails
        """
        logger.info(f"Starting bulk creation for project: {spec.name}")

        # Initialize context
        context = CreationContext()
        result = ProjectCreationResult()

        try:
            # Phase 1: Validation
            context.current_phase = CreationPhase.VALIDATION
            self._validate_spec(spec, context)
            context.complete_phase(CreationPhase.VALIDATION)

            # If dry run, return preview without creating
            if dry_run:
                return self._generate_preview_result(spec, context)

            # Phase 2: Create Project
            context.current_phase = CreationPhase.PROJECT
            self._create_project(spec, context)
            context.complete_phase(CreationPhase.PROJECT)

            # Phase 3: Create Sub-Projects (Locations)
            context.current_phase = CreationPhase.SUB_PROJECTS
            self._create_sub_projects(spec, context)
            context.complete_phase(CreationPhase.SUB_PROJECTS)

            # Phase 4: Create Tracks
            context.current_phase = CreationPhase.TRACKS
            self._create_tracks(spec, context)
            context.complete_phase(CreationPhase.TRACKS)

            # Phase 5: Create Courses
            context.current_phase = CreationPhase.COURSES
            self._create_courses(spec, context)
            context.complete_phase(CreationPhase.COURSES)

            # Phase 6: Create/Update Instructor Users
            context.current_phase = CreationPhase.INSTRUCTORS
            self._create_instructors(spec, context)
            context.complete_phase(CreationPhase.INSTRUCTORS)

            # Phase 7: Create Student Users
            context.current_phase = CreationPhase.STUDENTS
            self._create_students(spec, context)
            context.complete_phase(CreationPhase.STUDENTS)

            # Phase 8: Create Enrollments
            context.current_phase = CreationPhase.ENROLLMENTS
            self._create_enrollments(spec, context)
            context.complete_phase(CreationPhase.ENROLLMENTS)

            # Phase 9: Apply Schedule (if provided)
            if schedule_proposal:
                context.current_phase = CreationPhase.SCHEDULE
                self._apply_schedule(schedule_proposal, context)
                context.complete_phase(CreationPhase.SCHEDULE)

            # Phase 10: Queue Content Generation (if enabled)
            context.current_phase = CreationPhase.CONTENT_GENERATION
            content_job_id = self._queue_content_generation(spec, context)
            context.complete_phase(CreationPhase.CONTENT_GENERATION)

            # Phase 11: Create Zoom Rooms (if enabled)
            if spec.zoom_config.create_zoom_rooms and self.zoom_service:
                context.current_phase = CreationPhase.ZOOM_ROOMS
                self._create_zoom_rooms(spec, context)
                context.complete_phase(CreationPhase.ZOOM_ROOMS)

            # Mark complete
            context.current_phase = CreationPhase.COMPLETE
            context.end_time = datetime.now()
            context.complete_phase(CreationPhase.COMPLETE)

            # Build success result
            result = self._build_result(spec, context, content_job_id)
            result.success = True

            logger.info(
                f"Bulk creation completed successfully for project: {spec.name} "
                f"in {context.get_duration_seconds():.2f}s"
            )

        except InvalidSpecificationException as e:
            logger.error(f"Specification validation failed: {e.message}")
            context.add_error(e.message, context.current_phase)
            context.end_time = datetime.now()
            result = self._build_error_result(context, e)

        except Exception as e:
            logger.error(f"Bulk creation failed at phase {context.current_phase}: {str(e)}")
            context.add_error(str(e), context.current_phase)
            context.end_time = datetime.now()
            result = self._build_error_result(context, e)

        return result

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def _validate_spec(self, spec: ProjectBuilderSpec, context: CreationContext) -> None:
        """
        Validate project specification before creation.

        WHY: Catch errors early before expensive database operations.

        WHAT: Validates all required fields and business rules.

        HOW: Calls spec's validate method plus additional checks.
        """
        logger.debug("Validating project specification")

        # Use entity's built-in validation
        try:
            spec.validate()
        except InvalidSpecificationException:
            raise

        # Additional business rule validation
        if not spec.name or not spec.name.strip():
            raise InvalidSpecificationException(
                "Project name is required",
                field="name"
            )

        if not spec.locations:
            raise InvalidSpecificationException(
                "At least one location is required",
                field="locations"
            )

        if not spec.tracks:
            raise InvalidSpecificationException(
                "At least one track is required",
                field="tracks"
            )

        logger.debug("Specification validation passed")

    # =========================================================================
    # PROJECT CREATION
    # =========================================================================

    def _create_project(self, spec: ProjectBuilderSpec, context: CreationContext) -> None:
        """
        Create the main project entity.

        WHY: Project is the root entity that others reference.

        WHAT: Creates project with metadata from spec.

        HOW: Calls project DAO to persist.
        """
        logger.debug(f"Creating project: {spec.name}")

        try:
            project_data = self.project_dao.create_project(
                name=spec.name,
                description=spec.description,
                organization_id=str(spec.organization_id) if spec.organization_id else None,
                created_by=str(spec.created_by) if spec.created_by else None
            )

            context.project_id = UUID(project_data["id"]) if isinstance(project_data["id"], str) else project_data["id"]
            logger.info(f"Created project with ID: {context.project_id}")

        except Exception as e:
            raise BulkProjectCreatorException(
                f"Failed to create project: {str(e)}",
                phase=CreationPhase.PROJECT,
                context=context,
                original_error=e
            )

    # =========================================================================
    # SUB-PROJECT CREATION
    # =========================================================================

    def _create_sub_projects(self, spec: ProjectBuilderSpec, context: CreationContext) -> None:
        """
        Create sub-projects for each location.

        WHY: Locations become sub-projects in the system.

        WHAT: Creates sub-project for each LocationSpec.

        HOW: Iterates locations, creates sub-projects linked to project.
        """
        logger.debug(f"Creating {len(spec.locations)} sub-projects")

        for location in spec.locations:
            try:
                sub_project_data = self.sub_project_dao.create_sub_project(
                    name=location.name,
                    project_id=str(context.project_id),
                    city=location.city,
                    country=location.country,
                    timezone=location.timezone,
                    max_students=location.max_students
                )

                sub_project_id = UUID(sub_project_data["id"]) if isinstance(sub_project_data["id"], str) else sub_project_data["id"]
                context.subproject_ids.append(sub_project_id)
                context.location_name_to_subproject_id[location.name] = sub_project_id

                logger.debug(f"Created sub-project '{location.name}' with ID: {sub_project_id}")

            except Exception as e:
                context.add_error(
                    f"Failed to create sub-project for location '{location.name}': {str(e)}",
                    CreationPhase.SUB_PROJECTS
                )
                raise BulkProjectCreatorException(
                    f"Failed to create sub-project: {str(e)}",
                    phase=CreationPhase.SUB_PROJECTS,
                    context=context,
                    original_error=e
                )

        logger.info(f"Created {len(context.subproject_ids)} sub-projects")

    # =========================================================================
    # TRACK CREATION
    # =========================================================================

    def _create_tracks(self, spec: ProjectBuilderSpec, context: CreationContext) -> None:
        """
        Create tracks within the project.

        WHY: Tracks organize courses into learning paths.

        WHAT: Creates track for each TrackSpec.

        HOW: Iterates tracks, creates linked to project.
        """
        logger.debug(f"Creating {len(spec.tracks)} tracks")

        for track in spec.tracks:
            try:
                track_data = self.track_dao.create_track(
                    name=track.name,
                    description=track.description,
                    project_id=str(context.project_id),
                    color=track.color,
                    icon=track.icon
                )

                track_id = UUID(track_data["id"]) if isinstance(track_data["id"], str) else track_data["id"]
                context.track_ids.append(track_id)
                context.track_name_to_id[track.name] = track_id

                logger.debug(f"Created track '{track.name}' with ID: {track_id}")

            except Exception as e:
                context.add_error(
                    f"Failed to create track '{track.name}': {str(e)}",
                    CreationPhase.TRACKS
                )
                raise BulkProjectCreatorException(
                    f"Failed to create track: {str(e)}",
                    phase=CreationPhase.TRACKS,
                    context=context,
                    original_error=e
                )

        logger.info(f"Created {len(context.track_ids)} tracks")

    # =========================================================================
    # COURSE CREATION
    # =========================================================================

    def _create_courses(self, spec: ProjectBuilderSpec, context: CreationContext) -> None:
        """
        Create courses within tracks.

        WHY: Courses are the content units students learn.

        WHAT: Creates courses for each CourseSpec in each track.

        HOW: Iterates tracks and their courses.
        """
        logger.debug("Creating courses")

        for track in spec.tracks:
            track_id = context.track_name_to_id.get(track.name)
            if not track_id:
                logger.warning(f"Track ID not found for track: {track.name}")
                continue

            for course in track.courses:
                try:
                    course_data = self.course_dao.create_course(
                        title=course.title,
                        description=course.description,
                        track_id=str(track_id),
                        difficulty=course.difficulty,
                        duration_hours=course.duration_hours,
                        order_index=course.order_index
                    )

                    course_id = UUID(course_data["id"]) if isinstance(course_data["id"], str) else course_data["id"]
                    context.course_ids.append(course_id)
                    context.course_title_to_id[course.title] = course_id

                    logger.debug(f"Created course '{course.title}' with ID: {course_id}")

                except Exception as e:
                    context.add_error(
                        f"Failed to create course '{course.title}': {str(e)}",
                        CreationPhase.COURSES
                    )
                    raise BulkProjectCreatorException(
                        f"Failed to create course: {str(e)}",
                        phase=CreationPhase.COURSES,
                        context=context,
                        original_error=e
                    )

        logger.info(f"Created {len(context.course_ids)} courses")

    # =========================================================================
    # INSTRUCTOR CREATION
    # =========================================================================

    def _create_instructors(self, spec: ProjectBuilderSpec, context: CreationContext) -> None:
        """
        Create or update instructor user accounts.

        WHY: Instructors need accounts to access platform.

        WHAT: Creates new users or updates existing for instructors.

        HOW: Checks for existing user by email, creates if not found.
        """
        logger.debug(f"Processing {len(spec.instructors)} instructors")

        for instructor in spec.instructors:
            try:
                # Check if user already exists
                existing_user = self.user_dao.get_user_by_email(instructor.email)

                if existing_user:
                    user_id = UUID(existing_user["id"]) if isinstance(existing_user["id"], str) else existing_user["id"]
                    logger.debug(f"Using existing user for instructor: {instructor.email}")
                else:
                    # Create new user
                    user_data = self.user_dao.create_user(
                        name=instructor.name,
                        email=instructor.email,
                        role="instructor"
                    )
                    user_id = UUID(user_data["id"]) if isinstance(user_data["id"], str) else user_data["id"]
                    logger.debug(f"Created new user for instructor: {instructor.email}")

                context.instructor_user_ids.append(user_id)
                context.user_email_to_id[instructor.email] = user_id

            except Exception as e:
                context.add_error(
                    f"Failed to create/update instructor '{instructor.email}': {str(e)}",
                    CreationPhase.INSTRUCTORS
                )
                # Continue with other instructors - this is a soft failure
                context.warnings.append(f"Could not create instructor user: {instructor.email}")

        logger.info(f"Processed {len(context.instructor_user_ids)} instructors")

    # =========================================================================
    # STUDENT CREATION
    # =========================================================================

    def _create_students(self, spec: ProjectBuilderSpec, context: CreationContext) -> None:
        """
        Create student user accounts.

        WHY: Students need accounts for course access.

        WHAT: Creates new users for students.

        HOW: Checks for existing, creates if not found.
        """
        logger.debug(f"Processing {len(spec.students)} students")

        for student in spec.students:
            try:
                # Check if user already exists
                existing_user = self.user_dao.get_user_by_email(student.email)

                if existing_user:
                    user_id = UUID(existing_user["id"]) if isinstance(existing_user["id"], str) else existing_user["id"]
                    logger.debug(f"Using existing user for student: {student.email}")
                else:
                    # Create new user
                    user_data = self.user_dao.create_user(
                        name=student.name,
                        email=student.email,
                        role="student"
                    )
                    user_id = UUID(user_data["id"]) if isinstance(user_data["id"], str) else user_data["id"]
                    logger.debug(f"Created new user for student: {student.email}")

                context.student_user_ids.append(user_id)
                context.user_email_to_id[student.email] = user_id

            except Exception as e:
                context.add_error(
                    f"Failed to create student '{student.email}': {str(e)}",
                    CreationPhase.STUDENTS
                )
                context.warnings.append(f"Could not create student user: {student.email}")

        logger.info(f"Processed {len(context.student_user_ids)} students")

    # =========================================================================
    # ENROLLMENT CREATION
    # =========================================================================

    def _create_enrollments(self, spec: ProjectBuilderSpec, context: CreationContext) -> None:
        """
        Create enrollments linking students to courses.

        WHY: Enrollments grant students access to courses.

        WHAT: Creates enrollment for each student in their track's courses.

        HOW: Looks up student's track, enrolls in all track courses.
        """
        logger.debug("Creating enrollments")

        for student in spec.students:
            user_id = context.user_email_to_id.get(student.email)
            if not user_id:
                logger.warning(f"No user ID found for student: {student.email}")
                continue

            # Find the track for this student
            track_id = context.track_name_to_id.get(student.track_name)
            if not track_id:
                logger.warning(f"No track found for student {student.email}: {student.track_name}")
                continue

            # Get courses for this track
            track_spec = next(
                (t for t in spec.tracks if t.name == student.track_name),
                None
            )
            if not track_spec:
                continue

            for course in track_spec.courses:
                course_id = context.course_title_to_id.get(course.title)
                if not course_id:
                    continue

                try:
                    enrollment_data = self.enrollment_dao.create_enrollment(
                        user_id=str(user_id),
                        course_id=str(course_id),
                        enrollment_type="student"
                    )

                    enrollment_id = UUID(enrollment_data["id"]) if isinstance(enrollment_data["id"], str) else enrollment_data["id"]
                    context.enrollment_ids.append(enrollment_id)

                except Exception as e:
                    context.warnings.append(
                        f"Could not enroll {student.email} in {course.title}: {str(e)}"
                    )

        logger.info(f"Created {len(context.enrollment_ids)} enrollments")

    # =========================================================================
    # SCHEDULE APPLICATION
    # =========================================================================

    def _apply_schedule(
        self,
        schedule_proposal: ScheduleProposal,
        context: CreationContext
    ) -> None:
        """
        Apply approved schedule to created courses.

        WHY: Schedule defines when sessions occur.

        WHAT: Creates schedule entries for each session.

        HOW: Iterates schedule entries, creates in database.
        """
        logger.debug(f"Applying schedule with {len(schedule_proposal.entries)} entries")

        if not self.schedule_dao:
            logger.warning("No schedule DAO provided, skipping schedule application")
            return

        for entry in schedule_proposal.entries:
            try:
                # Map entry to created entities
                course_id = context.course_title_to_id.get(entry.course_title)
                instructor_id = context.user_email_to_id.get(entry.instructor_email)
                subproject_id = context.location_name_to_subproject_id.get(entry.location_name)

                self.schedule_dao.create_schedule_entry(
                    course_id=str(course_id) if course_id else None,
                    instructor_id=str(instructor_id) if instructor_id else None,
                    subproject_id=str(subproject_id) if subproject_id else None,
                    date=entry.date,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    session_number=entry.session_number
                )

            except Exception as e:
                context.warnings.append(f"Could not create schedule entry: {str(e)}")

        logger.info("Schedule applied")

    # =========================================================================
    # CONTENT GENERATION
    # =========================================================================

    def _queue_content_generation(
        self,
        spec: ProjectBuilderSpec,
        context: CreationContext
    ) -> Optional[UUID]:
        """
        Queue content generation jobs if enabled.

        WHY: Automates content creation for courses.

        WHAT: Queues jobs for syllabus, slides, quizzes, labs.

        HOW: Checks config, queues appropriate jobs.

        Returns:
            Job ID if content generation queued, None otherwise
        """
        config = spec.content_generation_config

        # Check if any content generation is enabled
        if not any([
            config.generate_syllabi,
            config.generate_slides,
            config.generate_quizzes,
            config.generate_labs
        ]):
            logger.debug("No content generation enabled")
            return None

        if not self.content_generation_service:
            logger.warning("Content generation enabled but no service provided")
            return None

        try:
            # Queue content generation for all courses
            job_id = self.content_generation_service.queue_bulk_generation(
                course_ids=[str(cid) for cid in context.course_ids],
                config=config
            )
            logger.info(f"Queued content generation job: {job_id}")
            return UUID(job_id) if isinstance(job_id, str) else job_id

        except Exception as e:
            context.warnings.append(f"Could not queue content generation: {str(e)}")
            return None

    # =========================================================================
    # ZOOM ROOM CREATION
    # =========================================================================

    def _create_zoom_rooms(
        self,
        spec: ProjectBuilderSpec,
        context: CreationContext
    ) -> None:
        """
        Create Zoom rooms for the project.

        WHY: Virtual classrooms need Zoom links.

        WHAT: Creates classroom and office hour rooms.

        HOW: Uses Zoom service to create rooms.
        """
        if not self.zoom_service:
            logger.warning("Zoom service not provided, skipping room creation")
            return

        try:
            # Create track classrooms
            if spec.zoom_config.create_track_classrooms:
                for track in spec.tracks:
                    room_id = self.zoom_service.create_classroom(
                        name=f"{spec.name} - {track.name}",
                        config=spec.zoom_config
                    )
                    if room_id:
                        context.zoom_room_ids.append(room_id)

            logger.info(f"Created {len(context.zoom_room_ids)} Zoom rooms")

        except Exception as e:
            context.warnings.append(f"Could not create Zoom rooms: {str(e)}")

    # =========================================================================
    # RESULT BUILDING
    # =========================================================================

    def _build_result(
        self,
        spec: ProjectBuilderSpec,
        context: CreationContext,
        content_job_id: Optional[UUID]
    ) -> ProjectCreationResult:
        """
        Build successful result from context.

        WHY: Structured result for caller.

        WHAT: Aggregates all created entity IDs and counts.

        HOW: Transfers data from context to result.
        """
        return ProjectCreationResult(
            success=True,
            project_id=context.project_id,
            subproject_ids=context.subproject_ids,
            track_ids=context.track_ids,
            course_ids=context.course_ids,
            instructor_user_ids=context.instructor_user_ids,
            student_user_ids=context.student_user_ids,
            enrollment_ids=context.enrollment_ids,
            zoom_room_ids=context.zoom_room_ids,
            counts={
                "projects": 1 if context.project_id else 0,
                "subprojects": len(context.subproject_ids),
                "tracks": len(context.track_ids),
                "courses": len(context.course_ids),
                "instructors": len(context.instructor_user_ids),
                "students": len(context.student_user_ids),
                "enrollments": len(context.enrollment_ids),
                "zoom_rooms": len(context.zoom_room_ids),
                "content_jobs": 1 if content_job_id else 0
            },
            errors=[],
            warnings=context.warnings,
            content_generation_job_id=content_job_id,
            duration_seconds=context.get_duration_seconds()
        )

    def _build_error_result(
        self,
        context: CreationContext,
        error: Exception
    ) -> ProjectCreationResult:
        """
        Build error result from context.

        WHY: Even failures need structured results.

        WHAT: Includes what was created before failure.

        HOW: Transfers context data plus error info.
        """
        return ProjectCreationResult(
            success=False,
            project_id=context.project_id,
            subproject_ids=context.subproject_ids,
            track_ids=context.track_ids,
            course_ids=context.course_ids,
            instructor_user_ids=context.instructor_user_ids,
            student_user_ids=context.student_user_ids,
            enrollment_ids=context.enrollment_ids,
            zoom_room_ids=context.zoom_room_ids,
            counts={
                "projects": 1 if context.project_id else 0,
                "subprojects": len(context.subproject_ids),
                "tracks": len(context.track_ids),
                "courses": len(context.course_ids),
                "instructors": len(context.instructor_user_ids),
                "students": len(context.student_user_ids),
                "enrollments": len(context.enrollment_ids),
                "zoom_rooms": len(context.zoom_room_ids),
                "content_jobs": 0
            },
            errors=context.errors + [{
                "message": str(error),
                "phase": context.current_phase.value,
                "type": type(error).__name__
            }],
            warnings=context.warnings,
            duration_seconds=context.get_duration_seconds()
        )

    def _generate_preview_result(
        self,
        spec: ProjectBuilderSpec,
        context: CreationContext
    ) -> ProjectCreationResult:
        """
        Generate preview result without creating entities.

        WHY: Dry run shows what would be created.

        WHAT: Counts based on spec without database changes.

        HOW: Calculates counts from spec directly.
        """
        total_courses = sum(len(t.courses) for t in spec.tracks)
        total_enrollments = len(spec.students) * total_courses // max(1, len(spec.tracks))

        return ProjectCreationResult(
            success=True,
            counts={
                "projects": 1,
                "subprojects": len(spec.locations),
                "tracks": len(spec.tracks),
                "courses": total_courses,
                "instructors": len(spec.instructors),
                "students": len(spec.students),
                "enrollments": total_enrollments,
                "zoom_rooms": len(spec.tracks) if spec.zoom_config.create_zoom_rooms else 0,
                "content_jobs": 1 if any([
                    spec.content_generation_config.generate_syllabi,
                    spec.content_generation_config.generate_slides,
                    spec.content_generation_config.generate_quizzes,
                    spec.content_generation_config.generate_labs
                ]) else 0
            },
            errors=[],
            warnings=["This is a dry run - no entities were created"],
            duration_seconds=context.get_duration_seconds()
        )
