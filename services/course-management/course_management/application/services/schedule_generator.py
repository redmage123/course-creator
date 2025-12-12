"""
Schedule Generator Service

BUSINESS CONTEXT:
This service generates training schedules for projects created through the
AI-powered project builder. It considers instructor availability, track
durations, location constraints, and working hours to create conflict-free
schedules or identify conflicts that need resolution.

WHY THIS EXISTS:
Creating schedules manually for multi-track, multi-location training programs
is complex and error-prone. This service:
1. Generates proposed schedules based on constraints
2. Detects scheduling conflicts automatically
3. Suggests resolutions for conflicts
4. Supports various scheduling strategies (parallel, sequential, etc.)

WHAT THIS MODULE PROVIDES:
- ScheduleGenerator: Main service class for schedule generation
- generate_schedule: Create schedule based on project specification
- detect_conflicts: Find scheduling conflicts
- suggest_resolutions: Propose solutions for conflicts

HOW TO USE:
    generator = ScheduleGenerator()

    # Generate schedule from project spec
    proposal = generator.generate_schedule(
        project_spec=project_builder_spec,
        schedule_config=schedule_config
    )

    # Check for conflicts
    if proposal.has_conflicts:
        for conflict in proposal.conflicts:
            print(f"Conflict: {conflict.description}")

    # Get schedule entries
    for entry in proposal.entries:
        print(f"{entry.date} {entry.start_time}: {entry.course_name}")

SCHEDULING STRATEGIES:
- SEQUENTIAL: One track at a time across all locations
- PARALLEL: Multiple tracks simultaneously at different locations
- INSTRUCTOR_OPTIMIZED: Minimize instructor travel/context switching
- LOCATION_OPTIMIZED: Keep instructors at one location as long as possible

CONFLICT TYPES:
- INSTRUCTOR_DOUBLE_BOOKING: Same instructor scheduled at two places
- ROOM_CONFLICT: Same room double-booked
- CAPACITY_EXCEEDED: More students than room capacity
- INSTRUCTOR_UNAVAILABLE: Instructor not available on scheduled day

@module schedule_generator
@author Course Creator Platform
@version 1.0.0
"""

import logging
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4
from collections import defaultdict

from course_management.domain.entities.project_builder import (
    # Configuration entities
    ProjectBuilderSpec,
    ScheduleConfig,
    # Schedule entities
    ScheduleEntry,
    ScheduleProposal,
    Conflict,
    # Specification entities
    LocationSpec,
    TrackSpec,
    CourseSpec,
    InstructorSpec,
    StudentSpec,
    # Enumerations
    ConflictType,
    # Exceptions
    ScheduleConflictException,
    InvalidSpecificationException
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class SchedulingStrategy(Enum):
    """
    Available scheduling strategies.

    WHY: Different programs have different constraints and preferences
    for how schedules should be organized.

    WHAT: Enum defining scheduling optimization priorities.

    Values:
        SEQUENTIAL: Complete one track before starting the next
        PARALLEL: Run multiple tracks at same time in different locations
        INSTRUCTOR_OPTIMIZED: Minimize instructor switching/travel
        LOCATION_OPTIMIZED: Keep activities at same location grouped
    """
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    INSTRUCTOR_OPTIMIZED = "instructor_optimized"
    LOCATION_OPTIMIZED = "location_optimized"


class SessionType(Enum):
    """
    Types of scheduled sessions.

    WHY: Different session types may have different duration and
    resource requirements.

    Values:
        LECTURE: Instructor-led content delivery
        LAB: Hands-on coding/practice session
        QUIZ: Assessment session
        WORKSHOP: Interactive group activity
        REVIEW: Content review/Q&A session
    """
    LECTURE = "lecture"
    LAB = "lab"
    QUIZ = "quiz"
    WORKSHOP = "workshop"
    REVIEW = "review"


# =============================================================================
# HELPER DATA CLASSES
# =============================================================================

@dataclass
class InstructorAssignment:
    """
    Tracks instructor assignment to a track at a location.

    WHY: Needed to track which instructor is teaching what where,
    enabling conflict detection.
    """
    instructor_email: str
    instructor_name: str
    track_name: str
    location_name: str
    courses: List[str] = field(default_factory=list)


@dataclass
class TimeSlot:
    """
    Represents a time slot in the schedule.

    WHY: Atomic unit for schedule generation and conflict detection.
    """
    date: date
    start_time: time
    end_time: time
    location: str
    track: str
    instructor_email: Optional[str] = None

    def overlaps(self, other: 'TimeSlot') -> bool:
        """Check if this time slot overlaps with another."""
        if self.date != other.date:
            return False
        return (self.start_time < other.end_time and
                self.end_time > other.start_time)


# =============================================================================
# MAIN SERVICE CLASS
# =============================================================================

class ScheduleGenerator:
    """
    Service for generating training schedules.

    BUSINESS REQUIREMENTS:
    - Generate conflict-free schedules when possible
    - Respect instructor availability constraints
    - Support multiple scheduling strategies
    - Provide clear conflict reporting
    - Support 6-week program duration (configurable)

    DESIGN PRINCIPLES:
    - Fail gracefully with meaningful conflict information
    - Support iterative schedule refinement
    - Provide scheduling flexibility through configuration
    """

    # Default working hours
    DEFAULT_START_TIME = time(9, 0)
    DEFAULT_END_TIME = time(17, 0)
    DEFAULT_BREAK_START = time(12, 0)
    DEFAULT_BREAK_END = time(13, 0)

    # Session durations (in minutes)
    DEFAULT_SESSION_DURATION = 90
    DEFAULT_LAB_DURATION = 120
    DEFAULT_QUIZ_DURATION = 60

    def __init__(self):
        """
        Initialize the schedule generator.

        WHY: Sets up default configurations for schedule generation.
        """
        self.working_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
        self.session_duration = self.DEFAULT_SESSION_DURATION
        self.lab_duration = self.DEFAULT_LAB_DURATION
        self.quiz_duration = self.DEFAULT_QUIZ_DURATION

    # =========================================================================
    # PUBLIC METHODS - Main Entry Points
    # =========================================================================

    def generate_schedule(
        self,
        project_spec: ProjectBuilderSpec,
        schedule_config: Optional[ScheduleConfig] = None,
        strategy: SchedulingStrategy = SchedulingStrategy.PARALLEL
    ) -> ScheduleProposal:
        """
        Generate a complete schedule for a project.

        WHY: Main entry point for schedule generation. Takes project
        specification and returns a complete schedule proposal.

        WHAT: Creates ScheduleProposal with entries and any conflicts.

        HOW:
        1. Validate input specification
        2. Assign instructors to tracks/locations
        3. Generate time slots for each session
        4. Detect any conflicts
        5. Build and return proposal

        Args:
            project_spec: Complete project specification
            schedule_config: Optional schedule configuration overrides
            strategy: Scheduling strategy to use

        Returns:
            ScheduleProposal with entries and conflicts

        Raises:
            InvalidSpecificationException: If spec is invalid
        """
        start_time = datetime.now()
        logger.info(
            f"Generating schedule for project: {project_spec.name}"
        )

        # Apply configuration
        config = schedule_config or project_spec.schedule_config or ScheduleConfig()
        self._apply_config(config)

        # Validate specification
        self._validate_specification(project_spec)

        # Generate instructor assignments
        assignments = self._assign_instructors(project_spec)

        # Generate schedule entries
        entries = self._generate_entries(
            project_spec,
            assignments,
            config,
            strategy
        )

        # Detect conflicts
        conflicts = self._detect_conflicts(entries, assignments, project_spec)

        # Build proposal
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        proposal = ScheduleProposal(
            spec_id=project_spec.id,
            entries=entries,
            conflicts=conflicts,
            is_valid=len([c for c in conflicts if c.severity == "error"]) == 0,
            generated_at=datetime.now()
        )

        logger.info(
            f"Generated schedule: {len(entries)} sessions, "
            f"{len(conflicts)} conflicts in {duration_ms}ms"
        )

        return proposal

    def detect_conflicts(
        self,
        entries: List[ScheduleEntry],
        project_spec: Optional[ProjectBuilderSpec] = None
    ) -> List[Conflict]:
        """
        Detect conflicts in a list of schedule entries.

        WHY: Allows checking for conflicts without full generation,
        useful for manual schedule adjustments.

        WHAT: Returns list of all detected conflicts.

        HOW: Checks for instructor double-booking, room conflicts,
        and availability issues.

        Args:
            entries: List of schedule entries to check
            project_spec: Optional spec for additional validation

        Returns:
            List of detected conflicts
        """
        logger.debug(f"Detecting conflicts in {len(entries)} entries")

        conflicts = []

        # Group entries by date
        entries_by_date: Dict[date, List[ScheduleEntry]] = defaultdict(list)
        for entry in entries:
            entries_by_date[entry.date].append(entry)

        # Check each day for conflicts
        for day_date, day_entries in entries_by_date.items():
            # Instructor conflicts
            conflicts.extend(
                self._check_instructor_conflicts(day_entries)
            )

            # Room conflicts
            conflicts.extend(
                self._check_room_conflicts(day_entries)
            )

        # Check instructor availability if spec provided
        if project_spec:
            conflicts.extend(
                self._check_instructor_availability(entries, project_spec)
            )

        logger.info(f"Detected {len(conflicts)} conflicts")
        return conflicts

    def suggest_resolutions(
        self,
        conflicts: List[Conflict],
        entries: List[ScheduleEntry],
        project_spec: ProjectBuilderSpec
    ) -> Dict[UUID, List[str]]:
        """
        Suggest resolutions for schedule conflicts.

        WHY: Helps admins resolve conflicts by providing actionable
        suggestions.

        WHAT: Returns dict mapping conflict IDs to resolution suggestions.

        HOW: Analyzes conflict type and context to propose solutions.

        Args:
            conflicts: List of conflicts to resolve
            entries: Current schedule entries
            project_spec: Project specification

        Returns:
            Dict mapping conflict ID to list of suggestions
        """
        logger.debug(f"Generating resolutions for {len(conflicts)} conflicts")

        resolutions: Dict[UUID, List[str]] = {}

        for conflict in conflicts:
            suggestions = self._generate_suggestions(
                conflict, entries, project_spec
            )
            resolutions[conflict.id] = suggestions

        return resolutions

    # =========================================================================
    # SCHEDULE GENERATION METHODS
    # =========================================================================

    def _apply_config(self, config: ScheduleConfig) -> None:
        """
        Apply schedule configuration settings.

        WHY: Customizes generation based on config.

        NOTE: ScheduleConfig uses:
        - working_days: List[str]
        - session_duration_hours: int (not minutes)
        - day_start_time/day_end_time (not start_time/end_time)
        """
        if config.working_days:
            self.working_days = set(config.working_days)

        if config.session_duration_hours:
            # Convert hours to minutes for internal use
            self.session_duration = config.session_duration_hours * 60

        logger.debug(
            f"Applied config: working_days={self.working_days}, "
            f"session_duration={self.session_duration}min"
        )

    def _validate_specification(self, spec: ProjectBuilderSpec) -> None:
        """
        Validate project specification for scheduling.

        WHY: Catches issues early before generation.

        Raises:
            InvalidSpecificationException: If validation fails
        """
        if not spec.locations:
            raise InvalidSpecificationException(
                "At least one location is required for scheduling"
            )

        if not spec.tracks:
            raise InvalidSpecificationException(
                "At least one track is required for scheduling"
            )

        # Validate that tracks have courses
        for track in spec.tracks:
            if not track.courses:
                logger.warning(f"Track '{track.name}' has no courses")

    def _assign_instructors(
        self,
        spec: ProjectBuilderSpec
    ) -> List[InstructorAssignment]:
        """
        Create instructor assignments for tracks at locations.

        WHY: Determines who teaches what where before generating schedule.

        WHAT: Returns list of InstructorAssignment objects.

        HOW:
        1. Match instructors to tracks based on track assignment
        2. For each location, assign instructors to their tracks
        """
        assignments = []

        # Build instructor lookup by email
        instructor_by_email: Dict[str, InstructorSpec] = {
            i.email: i for i in spec.instructors
        }

        # Build instructor lookup by track
        # InstructorSpec uses track_names (List[str]) not tracks
        instructors_by_track: Dict[str, List[InstructorSpec]] = defaultdict(list)
        for instructor in spec.instructors:
            for track in instructor.track_names:
                instructors_by_track[track].append(instructor)

        # For each location and track, assign an instructor
        # Note: LocationSpec doesn't have a tracks field, all tracks run at all locations
        for location in spec.locations:
            location_tracks = [t.name for t in spec.tracks]

            for track_name in location_tracks:
                # Find available instructors for this track
                available = instructors_by_track.get(track_name, [])

                if available:
                    # Use first available (could be enhanced with load balancing)
                    instructor = available[0]
                    assignment = InstructorAssignment(
                        instructor_email=instructor.email,
                        instructor_name=instructor.name,
                        track_name=track_name,
                        location_name=location.name,
                        courses=[
                            c.title for t in spec.tracks
                            if t.name == track_name
                            for c in t.courses
                        ]
                    )
                    assignments.append(assignment)
                    logger.debug(
                        f"Assigned {instructor.name} to {track_name} at {location.name}"
                    )
                else:
                    logger.warning(
                        f"No instructor available for track '{track_name}' "
                        f"at location '{location.name}'"
                    )

        return assignments

    def _generate_entries(
        self,
        spec: ProjectBuilderSpec,
        assignments: List[InstructorAssignment],
        config: ScheduleConfig,
        strategy: SchedulingStrategy
    ) -> List[ScheduleEntry]:
        """
        Generate schedule entries based on strategy.

        WHY: Core scheduling logic that creates actual schedule entries.

        WHAT: Returns list of ScheduleEntry objects.

        HOW: Dispatches to strategy-specific generation method.
        """
        if strategy == SchedulingStrategy.PARALLEL:
            return self._generate_parallel_schedule(spec, assignments, config)
        elif strategy == SchedulingStrategy.SEQUENTIAL:
            return self._generate_sequential_schedule(spec, assignments, config)
        elif strategy == SchedulingStrategy.INSTRUCTOR_OPTIMIZED:
            return self._generate_instructor_optimized_schedule(
                spec, assignments, config
            )
        else:
            return self._generate_parallel_schedule(spec, assignments, config)

    def _generate_parallel_schedule(
        self,
        spec: ProjectBuilderSpec,
        assignments: List[InstructorAssignment],
        config: ScheduleConfig
    ) -> List[ScheduleEntry]:
        """
        Generate schedule with parallel tracks.

        WHY: Allows multiple tracks to run simultaneously at different
        locations, maximizing throughput.

        HOW:
        1. For each location, schedule all tracks
        2. Sessions run at the same time slots across locations
        3. Each day has morning and afternoon slots

        NOTE: ScheduleConfig uses day_start_time/day_end_time (not start_time/end_time)
        and lunch_break_start (not break_start_time/break_end_time)
        """
        entries = []
        entry_id = 0

        # Get program duration
        duration_weeks = config.duration_weeks or 6
        program_start = config.start_date or date.today() + timedelta(days=7)

        # Build track info lookup
        track_info: Dict[str, TrackSpec] = {t.name: t for t in spec.tracks}

        # Process each assignment
        for assignment in assignments:
            track = track_info.get(assignment.track_name)
            if not track:
                continue

            current_date = program_start
            course_idx = 0
            session_in_course = 0

            # Calculate sessions per course
            sessions_per_week = len(self.working_days) * 2  # AM and PM
            total_sessions = duration_weeks * sessions_per_week
            sessions_per_course = max(
                1, total_sessions // max(1, len(track.courses))
            )

            for week in range(duration_weeks):
                for day_offset in range(7):
                    current_date = program_start + timedelta(
                        days=week * 7 + day_offset
                    )
                    day_name = current_date.strftime('%A')

                    if day_name not in self.working_days:
                        continue

                    if course_idx >= len(track.courses):
                        break

                    course = track.courses[course_idx]

                    # Get start time from config (day_start_time, not start_time)
                    start = config.day_start_time or self.DEFAULT_START_TIME

                    # Morning session
                    entry = ScheduleEntry(
                        id=uuid4(),
                        date=current_date,
                        start_time=start,
                        end_time=time(
                            start.hour + (self.session_duration // 60),
                            start.minute + (self.session_duration % 60)
                        ),
                        track_name=track.name,
                        course_title=course.title,
                        location_name=assignment.location_name,
                        instructor_email=assignment.instructor_email,
                        instructor_name=assignment.instructor_name,
                        session_number=session_in_course + 1
                    )
                    entries.append(entry)
                    session_in_course += 1

                    # Afternoon session (lab or continuation)
                    # Calculate PM start based on lunch break
                    lunch_start = config.lunch_break_start or self.DEFAULT_BREAK_START
                    lunch_duration = config.lunch_break_duration_minutes or 60
                    pm_start = time(
                        lunch_start.hour + (lunch_duration // 60),
                        lunch_start.minute + (lunch_duration % 60)
                    )
                    entry = ScheduleEntry(
                        id=uuid4(),
                        date=current_date,
                        start_time=pm_start,
                        end_time=time(
                            pm_start.hour + (self.lab_duration // 60),
                            pm_start.minute + (self.lab_duration % 60)
                        ),
                        track_name=track.name,
                        course_title=course.title,
                        location_name=assignment.location_name,
                        instructor_email=assignment.instructor_email,
                        instructor_name=assignment.instructor_name,
                        session_number=session_in_course + 1
                    )
                    entries.append(entry)
                    session_in_course += 1

                    # Move to next course if enough sessions
                    if session_in_course >= sessions_per_course:
                        course_idx += 1
                        session_in_course = 0

        logger.info(f"Generated {len(entries)} entries using parallel strategy")
        return entries

    def _generate_sequential_schedule(
        self,
        spec: ProjectBuilderSpec,
        assignments: List[InstructorAssignment],
        config: ScheduleConfig
    ) -> List[ScheduleEntry]:
        """
        Generate schedule with sequential tracks.

        WHY: Completes one track before starting the next, useful when
        instructors teach multiple tracks or when tracks have dependencies.

        HOW:
        1. Order tracks by priority or name
        2. Schedule each track completely before moving to next
        3. Apply to all locations simultaneously

        NOTE: ScheduleConfig uses day_start_time (not start_time)
        """
        entries = []

        duration_weeks = config.duration_weeks or 6
        program_start = config.start_date or date.today() + timedelta(days=7)
        weeks_per_track = max(1, duration_weeks // max(1, len(spec.tracks)))

        track_info: Dict[str, TrackSpec] = {t.name: t for t in spec.tracks}
        track_order = list(track_info.keys())

        for track_idx, track_name in enumerate(track_order):
            track = track_info[track_name]
            track_start = program_start + timedelta(weeks=track_idx * weeks_per_track)

            # Get assignments for this track
            track_assignments = [
                a for a in assignments if a.track_name == track_name
            ]

            for assignment in track_assignments:
                current_date = track_start
                course_idx = 0
                days_in_track = 0

                for week in range(weeks_per_track):
                    for day_offset in range(7):
                        current_date = track_start + timedelta(
                            days=week * 7 + day_offset
                        )
                        day_name = current_date.strftime('%A')

                        if day_name not in self.working_days:
                            continue

                        if course_idx >= len(track.courses):
                            break

                        course = track.courses[course_idx]

                        # Get start time from config (day_start_time, not start_time)
                        start = config.day_start_time or self.DEFAULT_START_TIME

                        # Create session entry
                        entry = ScheduleEntry(
                            id=uuid4(),
                            date=current_date,
                            start_time=start,
                            end_time=time(
                                start.hour + (self.session_duration // 60),
                                0
                            ),
                            track_name=track.name,
                            course_title=course.title,
                            location_name=assignment.location_name,
                            instructor_email=assignment.instructor_email,
                            instructor_name=assignment.instructor_name,
                            session_number=days_in_track + 1
                        )
                        entries.append(entry)
                        days_in_track += 1

                        # Advance course every few days
                        if days_in_track % 3 == 0 and course_idx < len(track.courses) - 1:
                            course_idx += 1

        logger.info(f"Generated {len(entries)} entries using sequential strategy")
        return entries

    def _generate_instructor_optimized_schedule(
        self,
        spec: ProjectBuilderSpec,
        assignments: List[InstructorAssignment],
        config: ScheduleConfig
    ) -> List[ScheduleEntry]:
        """
        Generate schedule optimizing for instructor utilization.

        WHY: Minimizes instructor travel and context switching by
        grouping their sessions.

        HOW:
        1. Group assignments by instructor
        2. For each instructor, schedule all their sessions together
        3. Move between locations only when necessary

        NOTE: ScheduleConfig uses day_start_time (not start_time)
        """
        entries = []

        duration_weeks = config.duration_weeks or 6
        program_start = config.start_date or date.today() + timedelta(days=7)

        # Group by instructor
        by_instructor: Dict[str, List[InstructorAssignment]] = defaultdict(list)
        for assignment in assignments:
            by_instructor[assignment.instructor_email].append(assignment)

        track_info: Dict[str, TrackSpec] = {t.name: t for t in spec.tracks}

        for instructor_email, instructor_assignments in by_instructor.items():
            # Sort assignments by location to minimize travel
            sorted_assignments = sorted(
                instructor_assignments,
                key=lambda a: a.location_name
            )

            # Distribute across weeks
            weeks_per_assignment = max(
                1, duration_weeks // max(1, len(instructor_assignments))
            )

            for idx, assignment in enumerate(sorted_assignments):
                assignment_start = program_start + timedelta(
                    weeks=idx * weeks_per_assignment
                )
                track = track_info.get(assignment.track_name)
                if not track:
                    continue

                current_date = assignment_start
                course_idx = 0

                for week in range(weeks_per_assignment):
                    for day_offset in range(7):
                        current_date = assignment_start + timedelta(
                            days=week * 7 + day_offset
                        )
                        day_name = current_date.strftime('%A')

                        if day_name not in self.working_days:
                            continue

                        if course_idx >= len(track.courses):
                            break

                        course = track.courses[course_idx]

                        # Get start time from config (day_start_time, not start_time)
                        start = config.day_start_time or self.DEFAULT_START_TIME

                        entry = ScheduleEntry(
                            id=uuid4(),
                            date=current_date,
                            start_time=start,
                            end_time=time(
                                start.hour + (self.session_duration // 60),
                                0
                            ),
                            track_name=track.name,
                            course_title=course.title,
                            location_name=assignment.location_name,
                            instructor_email=assignment.instructor_email,
                            instructor_name=assignment.instructor_name,
                            session_number=course_idx + 1
                        )
                        entries.append(entry)

                        # Advance course periodically
                        if (week * 5 + day_offset) % 4 == 0:
                            course_idx = min(course_idx + 1, len(track.courses) - 1)

        logger.info(
            f"Generated {len(entries)} entries using instructor-optimized strategy"
        )
        return entries

    # =========================================================================
    # CONFLICT DETECTION METHODS
    # =========================================================================

    def _detect_conflicts(
        self,
        entries: List[ScheduleEntry],
        assignments: List[InstructorAssignment],
        spec: ProjectBuilderSpec
    ) -> List[Conflict]:
        """
        Detect all conflicts in generated schedule.

        WHY: Comprehensive conflict detection enables informed decision making.

        WHAT: Returns list of all detected conflicts.

        HOW: Runs multiple conflict detection checks and aggregates results.
        """
        conflicts = []

        # Instructor double-booking
        conflicts.extend(self._check_instructor_conflicts(entries))

        # Room conflicts
        conflicts.extend(self._check_room_conflicts(entries))

        # Instructor availability
        conflicts.extend(
            self._check_instructor_availability(entries, spec)
        )

        # Capacity issues
        conflicts.extend(
            self._check_capacity_conflicts(entries, spec)
        )

        return conflicts

    def _check_instructor_conflicts(
        self,
        entries: List[ScheduleEntry]
    ) -> List[Conflict]:
        """
        Check for instructor double-booking conflicts.

        WHY: An instructor cannot be in two places at the same time.

        WHAT: Returns conflicts where same instructor is scheduled
        at overlapping times.
        """
        conflicts = []

        # Group by instructor and date
        by_instructor_date: Dict[Tuple[str, date], List[ScheduleEntry]] = defaultdict(list)
        for entry in entries:
            if entry.instructor_email:
                key = (entry.instructor_email, entry.date)
                by_instructor_date[key].append(entry)

        # Check each instructor's day for overlaps
        for (instructor, day), day_entries in by_instructor_date.items():
            if len(day_entries) < 2:
                continue

            # Sort by start time
            sorted_entries = sorted(day_entries, key=lambda e: e.start_time)

            for i in range(len(sorted_entries) - 1):
                curr = sorted_entries[i]
                next_entry = sorted_entries[i + 1]

                # Check for overlap
                if curr.end_time > next_entry.start_time:
                    # Check if at different locations
                    if curr.location_name != next_entry.location_name:
                        conflict = Conflict(
                            id=uuid4(),
                            conflict_type=ConflictType.INSTRUCTOR_DOUBLE_BOOKING,
                            description=(
                                f"Instructor {curr.instructor_name} scheduled at "
                                f"'{curr.location_name}' and '{next_entry.location_name}' "
                                f"at overlapping times on {day}"
                            ),
                            affected_entries=[curr.id, next_entry.id],
                            affected_instructor=instructor,
                            affected_date=day,
                            severity="error"
                        )
                        conflicts.append(conflict)
                        logger.warning(f"Conflict: {conflict.description}")

        return conflicts

    def _check_room_conflicts(
        self,
        entries: List[ScheduleEntry]
    ) -> List[Conflict]:
        """
        Check for room/location conflicts.

        WHY: Same location cannot host multiple sessions simultaneously
        (unless different rooms are specified).

        WHAT: Returns conflicts where same location has overlapping sessions.
        """
        conflicts = []

        # Group by location and date
        by_location_date: Dict[Tuple[str, date], List[ScheduleEntry]] = defaultdict(list)
        for entry in entries:
            key = (entry.location_name, entry.date)
            by_location_date[key].append(entry)

        for (location, day), day_entries in by_location_date.items():
            if len(day_entries) < 2:
                continue

            sorted_entries = sorted(day_entries, key=lambda e: e.start_time)

            for i in range(len(sorted_entries) - 1):
                curr = sorted_entries[i]
                next_entry = sorted_entries[i + 1]

                if curr.end_time > next_entry.start_time:
                    # Different tracks at same time is okay (different rooms assumed)
                    if curr.track_name == next_entry.track_name:
                        conflict = Conflict(
                            id=uuid4(),
                            conflict_type=ConflictType.ROOM_CONFLICT,
                            description=(
                                f"Room conflict at '{location}' on {day}: "
                                f"'{curr.course_title}' and '{next_entry.course_title}' "
                                f"overlap"
                            ),
                            affected_entries=[curr.id, next_entry.id],
                            affected_date=day,
                            severity="warning"
                        )
                        conflicts.append(conflict)

        return conflicts

    def _check_instructor_availability(
        self,
        entries: List[ScheduleEntry],
        spec: ProjectBuilderSpec
    ) -> List[Conflict]:
        """
        Check if instructors are available on scheduled days.

        WHY: Instructors may have specified availability constraints.

        WHAT: Returns conflicts where instructor not available.
        """
        conflicts = []

        # Build instructor availability map
        instructor_availability: Dict[str, Set[str]] = {}
        for instructor in spec.instructors:
            instructor_availability[instructor.email] = set(
                instructor.available_days or list(self.working_days)
            )

        # Check each entry
        for entry in entries:
            if not entry.instructor_email:
                continue

            available_days = instructor_availability.get(
                entry.instructor_email, self.working_days
            )

            day_of_week = entry.date.strftime('%A')
            if day_of_week not in available_days:
                conflict = Conflict(
                    id=uuid4(),
                    conflict_type=ConflictType.INSTRUCTOR_UNAVAILABLE,
                    description=(
                        f"Instructor {entry.instructor_name} is not available on "
                        f"{day_of_week} ({entry.date})"
                    ),
                    affected_entries=[entry.id],
                    affected_instructor=entry.instructor_email,
                    affected_date=entry.date,
                    severity="error"
                )
                conflicts.append(conflict)

        return conflicts

    def _check_capacity_conflicts(
        self,
        entries: List[ScheduleEntry],
        spec: ProjectBuilderSpec
    ) -> List[Conflict]:
        """
        Check for capacity issues.

        WHY: Ensures session capacity matches student enrollment.

        WHAT: Returns conflicts where capacity would be exceeded.

        NOTE: StudentSpec uses location_name and track_name (not location and track)
        """
        conflicts = []

        # Build location capacity map
        location_capacity: Dict[str, int] = {
            loc.name: loc.max_students or 100
            for loc in spec.locations
        }

        # Count students per location/track
        # StudentSpec uses location_name and track_name
        students_per_location_track: Dict[Tuple[str, str], int] = defaultdict(int)
        for student in spec.students:
            key = (student.location_name or "Default", student.track_name)
            students_per_location_track[key] += 1

        # Check entries
        for entry in entries:
            key = (entry.location_name, entry.track_name)
            student_count = students_per_location_track.get(key, 0)
            capacity = location_capacity.get(entry.location_name, 100)

            if student_count > capacity:
                conflict = Conflict(
                    id=uuid4(),
                    conflict_type=ConflictType.CAPACITY_EXCEEDED,
                    description=(
                        f"Session at '{entry.location_name}' for track "
                        f"'{entry.track_name}' has {student_count} students but "
                        f"capacity is {capacity}"
                    ),
                    affected_entries=[entry.id],
                    severity="warning"
                )
                conflicts.append(conflict)

        return conflicts

    # =========================================================================
    # RESOLUTION SUGGESTION METHODS
    # =========================================================================

    def _generate_suggestions(
        self,
        conflict: Conflict,
        entries: List[ScheduleEntry],
        spec: ProjectBuilderSpec
    ) -> List[str]:
        """
        Generate resolution suggestions for a conflict.

        WHY: Actionable suggestions help admins resolve issues quickly.

        WHAT: Returns list of suggestion strings.
        """
        suggestions = []

        if conflict.conflict_type == ConflictType.INSTRUCTOR_DOUBLE_BOOKING:
            suggestions.extend([
                "Reschedule one of the sessions to a different time",
                "Assign a different instructor to one of the sessions",
                "Consider using the sequential scheduling strategy"
            ])

            # Find alternative instructors
            alt_instructors = self._find_alternative_instructors(
                conflict, entries, spec
            )
            if alt_instructors:
                suggestions.append(
                    f"Alternative instructors available: {', '.join(alt_instructors)}"
                )

        elif conflict.conflict_type == ConflictType.INSTRUCTOR_UNAVAILABLE:
            suggestions.extend([
                "Reschedule to a day when the instructor is available",
                "Assign a different instructor who is available on this day"
            ])

        elif conflict.conflict_type == ConflictType.CAPACITY_EXCEEDED:
            suggestions.extend([
                "Split the group into multiple sessions",
                "Use a larger venue",
                "Reduce enrollment for this track at this location"
            ])

        elif conflict.conflict_type == ConflictType.ROOM_CONFLICT:
            suggestions.extend([
                "Reschedule one session to a different time",
                "Book an additional room"
            ])

        return suggestions

    def _find_alternative_instructors(
        self,
        conflict: Conflict,
        entries: List[ScheduleEntry],
        spec: ProjectBuilderSpec
    ) -> List[str]:
        """
        Find instructors who could replace a conflicted instructor.

        WHY: Suggests specific alternatives to resolve conflicts.

        NOTE: InstructorSpec uses track_names (List[str]) not tracks
        """
        alternatives = []

        # Get affected entries
        affected_entry_list = [e for e in entries if e.id in conflict.affected_entries]
        if not affected_entry_list:
            return alternatives

        # Get track from first affected entry
        target_track = affected_entry_list[0].track_name

        # Find instructors who teach this track
        # InstructorSpec uses track_names (List[str]) not tracks
        for instructor in spec.instructors:
            if target_track in instructor.track_names:
                # Check if this is not the affected instructor
                if instructor.email != conflict.affected_instructor:
                    # Check if they're available
                    is_available = True
                    for entry in affected_entry_list:
                        day_of_week = entry.date.strftime('%A')
                        if day_of_week not in (
                            instructor.available_days or list(self.working_days)
                        ):
                            is_available = False
                            break

                    if is_available:
                        alternatives.append(instructor.name)

        return alternatives
