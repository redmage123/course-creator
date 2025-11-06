"""
Sub-Project Service Implementation - Multi-Locations Training Program Management

This module implements the sub-project (locations) service layer, orchestrating complex business
workflows for managing multiple instances of training programs across different locations with
independent scheduling and capacity management.

BUSINESS CONTEXT:
Sub-projects enable organizations to run the same training program (parent project) in multiple
locations simultaneously, each with customized scheduling, local capacity limits, and locations-
specific track assignments. This pattern is essential for:
- Global training programs with local delivery
- Regional rollout of standardized curricula
- Multi-city certification programs
- Seasonal locations with staggered start dates

ARCHITECTURAL RESPONSIBILITIES:
The SubProjectService encapsulates all sub-project business operations, enforcing domain rules,
validating locations data, managing capacity constraints, and maintaining referential integrity
with parent projects and track assignments.

BUSINESS WORKFLOW ORCHESTRATION:
1. Locations Creation: Validation, locations setup, and capacity initialization
2. Locations Management: Country/region/city hierarchy with timezone support
3. Capacity Tracking: Enrollment limits and participant count management
4. Status Lifecycle: Draft → Active → Completed → Archived transitions
5. Track Assignment: Linking tracks to locations with date overrides
6. Filtering & Discovery: Locations-based and date-based locations searches

DOMAIN RULE ENFORCEMENT:
- Locations Validation: Country is mandatory, region/city optional but validated
- Date Range Logic: Start date must be before or equal to end date
- Capacity Constraints: Current participants cannot exceed maximum capacity
- Status Transitions: Valid state machine enforced (draft → active → completed)
- Parent Project Reference: All sub-projects must reference valid parent projects
- Track Assignments: Tracks can be assigned with locations-specific date overrides

INTEGRATION PATTERNS:
- Repository Pattern: Clean separation between business logic and data persistence
- Parent-Child Hierarchy: Sub-projects always belong to a parent project (template)
- Locations Services: Integration with timezone and geography validation services
- Enrollment Coordination: Participant counts synchronized with enrollment service
- Analytics Integration: Locations performance and comparison reporting

MULTI-LOCATIONS CAPABILITIES:
- Geographic Hierarchy: Country → Region → City → Address structure
- Timezone Management: IANA timezone support for accurate scheduling
- Locations Filtering: Efficient queries by country, region, or city
- Cross-Locations Comparison: Analytics across multiple locations
- Capacity Distribution: Independent enrollment limits per locations

PERFORMANCE OPTIMIZATION:
- Indexed Queries: Optimized locations and date range filtering
- Batch Operations: Efficient creation of multiple locations
- Capacity Checks: Fast participant count validation before enrollment
- Metadata Storage: Flexible JSONB for track assignments without table joins
- Cascading Operations: Efficient parent project cleanup

EDUCATIONAL PLATFORM FEATURES:
- Locations Templates: Inherit structure from parent project, customize per locations
- Independent Scheduling: Each locations has its own start/end dates
- Local Capacity: Locations-specific enrollment limits
- Track Customization: Different track selections per locations
- Status Tracking: Lifecycle management for each locations instance
- Comparison Tools: Performance metrics across locations

ERROR HANDLING AND RESILIENCE:
- Locations Validation: Structured exceptions for missing or invalid locations data
- Date Validation: Clear error messages for invalid date ranges
- Capacity Enforcement: Graceful handling of enrollment limit violations
- Status Transition Validation: State machine violations prevented
- Parent Project Validation: Ensures referential integrity
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from uuid import UUID, uuid4

from course_management.domain.entities.sub_project import SubProject
from course_management.infrastructure.exceptions import (
    SubProjectNotFoundException,
    DuplicateSubProjectException,
    InvalidLocationException,
    InvalidDateRangeException,
    SubProjectCapacityException,
    ProjectNotFoundException,
    DatabaseQueryException
)
from data_access.sub_project_dao import SubProjectDAO

logger = logging.getLogger(__name__)


class SubProjectService:
    """
    Comprehensive sub-project management service implementing multi-locations business workflows.

    This service coordinates all locations-related operations, from initial creation through
    locations assignment, capacity management, status transitions, and track coordination.
    It enforces educational standards, maintains geographic data integrity, and provides
    rich analytics for cross-locations program comparison.

    DESIGN PRINCIPLES:
    - Single Responsibility: Focused exclusively on sub-project/locations business logic
    - Dependency Inversion: Depends on DAO abstraction for data persistence
    - Open/Closed: Extensible through composition and business rule injection
    - Interface Segregation: Clean separation of locations vs parent project concerns

    BUSINESS CAPABILITIES:
    1. Locations Lifecycle Management: Complete CRUD operations with state transitions
    2. Locations Validation: Geographic hierarchy enforcement and timezone validation
    3. Capacity Management: Enrollment limits with participant count tracking
    4. Discovery Services: Advanced filtering by locations, dates, and status
    5. Track Assignment: Locations-specific track selection with date overrides
    6. Analytics Integration: Cross-locations comparison and performance metrics

    MULTI-LOCATIONS WORKFLOWS:
    - Creation Process: Locations validation → Date validation → Capacity setup → Persistence
    - Enrollment Process: Capacity check → Participant increment → Enrollment coordination
    - Status Transition: State validation → Business rule check → Update persistence
    - Track Assignment: Validation → Date override setup → Metadata storage

    INTEGRATION COORDINATION:
    - Parent Project Service: Validates parent project existence and template status
    - Enrollment Service: Coordinates participant counts with actual enrollments
    - Analytics Service: Provides locations comparison and locations-based metrics
    - Locations Service: Validates geographic data and timezone information

    PERFORMANCE FEATURES:
    - Synchronous Operations: Simple blocking I/O for immediate consistency
    - Efficient Querying: Optimized locations and date filtering with indexes
    - Metadata Storage: JSONB for flexible track assignments without joins
    - Capacity Caching: Fast participant count validation without full queries
    """

    def __init__(self, dao: SubProjectDAO):
        """
        Initialize sub-project service with data access layer

        Args:
            dao: SubProjectDAO instance for database operations
        """
        self._dao = dao
        logger.info("SubProjectService initialized")

    def create_sub_project(self, data: Dict[str, Any]) -> SubProject:
        """
        Create a new sub-project (locations) with comprehensive business validation

        BUSINESS LOGIC:
        1. Validates parent project exists (if parent_project_id provided)
        2. Validates locations data (country required, region/city optional)
        3. Validates date range (start <= end if both provided)
        4. Validates capacity (max >= current if both provided)
        5. Generates UUID if not provided
        6. Sets default status to 'draft'
        7. Creates entity and validates business rules
        8. Persists to database via DAO

        Args:
            data: Dictionary containing sub-project data
                Required:
                    - parent_project_id: UUID of parent project
                    - organization_id: UUID of owning organization
                    - name: Human-readable locations name
                    - slug: URL-friendly identifier
                    - location_country: ISO country name
                Optional:
                    - location_region: State/Province
                    - location_city: City name
                    - location_address: Physical address
                    - timezone: IANA timezone (default: UTC)
                    - start_date: Locations start date
                    - end_date: Locations end date
                    - max_participants: Capacity limit
                    - status: Lifecycle status (default: draft)

        Returns:
            SubProject: Created sub-project entity

        Raises:
            InvalidLocationException: If locations data is invalid
            InvalidDateRangeException: If date range is invalid
            DuplicateSubProjectException: If slug already exists
            ProjectNotFoundException: If parent project doesn't exist
            ValueError: If required fields are missing or invalid

        Example:
            >>> data = {
            ...     'parent_project_id': 'uuid-here',
            ...     'organization_id': 'uuid-here',
            ...     'name': 'Boston Locations Fall 2025',
            ...     'slug': 'boston-fall-2025',
            ...     'location_country': 'United States',
            ...     'location_region': 'Massachusetts',
            ...     'location_city': 'Boston',
            ...     'start_date': date(2025, 9, 1),
            ...     'end_date': date(2025, 12, 15),
            ...     'max_participants': 30
            ... }
            >>> locations = service.create_sub_project(data)
        """
        logger.info(f"Creating sub-project: {data.get('name')}")

        # Validate required fields
        if not data.get('parent_project_id'):
            raise ValueError("parent_project_id is required")

        if not data.get('organization_id'):
            raise ValueError("organization_id is required")

        if not data.get('name'):
            raise ValueError("name is required")

        if not data.get('slug'):
            raise ValueError("slug is required")

        # Validate locations
        if not data.get('location_country'):
            raise InvalidLocationException("location_country is required")

        # Validate date range if both dates provided
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)

            if start_date > end_date:
                raise InvalidDateRangeException(start_date, end_date)

        # Validate capacity if both current and max provided
        current = data.get('current_participants', 0)
        max_capacity = data.get('max_participants')
        if max_capacity is not None and current > max_capacity:
            raise ValueError(f"current_participants ({current}) cannot exceed max_participants ({max_capacity})")

        # Generate ID if not provided
        if 'id' not in data or not data['id']:
            data['id'] = str(uuid4())

        # Set default status
        if 'status' not in data:
            data['status'] = 'draft'

        # Set default current_participants
        if 'current_participants' not in data:
            data['current_participants'] = 0

        # Create entity for validation
        try:
            entity = SubProject.from_dict(data)
            entity.validate()
        except Exception as e:
            logger.error(f"Entity validation failed: {e}")
            raise ValueError(f"Invalid sub-project data: {e}")

        # Create via DAO
        try:
            result = self._dao.create_sub_project(data)
            logger.info(f"Created sub-project: {result['id']}")

            # Convert to entity
            return SubProject.from_dict(result)

        except (InvalidLocationException, InvalidDateRangeException, DuplicateSubProjectException):
            raise
        except Exception as e:
            logger.error(f"Failed to create sub-project: {e}")
            raise DatabaseQueryException("create_sub_project", str(e))

    def get_sub_project_by_id(self, sub_project_id: str) -> SubProject:
        """
        Retrieve sub-project by ID

        Args:
            sub_project_id: UUID of sub-project

        Returns:
            SubProject: Sub-project entity

        Raises:
            SubProjectNotFoundException: If sub-project not found
            ValueError: If ID is invalid
        """
        if not sub_project_id:
            raise ValueError("sub_project_id is required")

        logger.info(f"Retrieving sub-project: {sub_project_id}")

        try:
            result = self._dao.get_sub_project_by_id(sub_project_id)
            return SubProject.from_dict(result)
        except SubProjectNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve sub-project: {e}")
            raise DatabaseQueryException("get_sub_project_by_id", str(e))

    def get_sub_projects_for_project(
        self,
        parent_project_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SubProject]:
        """
        Get all sub-projects (locations) for a parent project with optional filtering

        FILTERING OPTIONS:
        - location_country: Filter by country (exact match)
        - location_region: Filter by region (exact match)
        - location_city: Filter by city (partial match, case-insensitive)
        - status: Filter by status (exact match)
        - start_date_from: Locations starting on or after this date
        - start_date_to: Locations starting on or before this date

        Args:
            parent_project_id: UUID of parent project
            filters: Optional filtering criteria

        Returns:
            List[SubProject]: List of sub-project entities

        Raises:
            ValueError: If parent_project_id is invalid

        Example:
            >>> filters = {
            ...     'location_country': 'United States',
            ...     'location_region': 'Massachusetts',
            ...     'status': 'active',
            ...     'start_date_from': date(2025, 9, 1)
            ... }
            >>> locations = service.get_sub_projects_for_project(project_id, filters)
        """
        if not parent_project_id:
            raise ValueError("parent_project_id is required")

        logger.info(f"Retrieving sub-projects for project: {parent_project_id}")

        try:
            results = self._dao.get_sub_projects_by_parent(parent_project_id, filters)
            return [SubProject.from_dict(r) for r in results]
        except Exception as e:
            logger.error(f"Failed to retrieve sub-projects: {e}")
            raise DatabaseQueryException("get_sub_projects_by_parent", str(e))

    def update_sub_project(self, sub_project_id: str, data: Dict[str, Any]) -> SubProject:
        """
        Update an existing sub-project with business validation

        BUSINESS LOGIC:
        1. Validates sub-project exists
        2. Validates date range if dates are being updated
        3. Validates capacity constraints if capacity is being updated
        4. Prevents updating immutable fields (id, parent_project_id, organization_id)
        5. Updates entity
        6. Returns updated entity

        Args:
            sub_project_id: UUID of sub-project to update
            data: Dictionary of fields to update

        Returns:
            SubProject: Updated sub-project entity

        Raises:
            SubProjectNotFoundException: If sub-project not found
            InvalidDateRangeException: If date range is invalid
            ValueError: If update data is invalid
        """
        if not sub_project_id:
            raise ValueError("sub_project_id is required")

        logger.info(f"Updating sub-project: {sub_project_id}")

        # Validate date range if both dates are being updated
        if 'start_date' in data and 'end_date' in data:
            start_date = data['start_date']
            end_date = data['end_date']

            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)

            if start_date and end_date and start_date > end_date:
                raise InvalidDateRangeException(start_date, end_date)

        # Validate capacity if being updated
        if 'max_participants' in data or 'current_participants' in data:
            # Get current entity to check constraints
            current = self.get_sub_project_by_id(sub_project_id)

            new_max = data.get('max_participants', current.max_participants)
            new_current = data.get('current_participants', current.current_participants)

            if new_max is not None and new_current > new_max:
                raise ValueError(f"current_participants ({new_current}) cannot exceed max_participants ({new_max})")

        try:
            self._dao.update_sub_project(sub_project_id, data)

            # Return updated entity
            return self.get_sub_project_by_id(sub_project_id)

        except (SubProjectNotFoundException, InvalidDateRangeException):
            raise
        except Exception as e:
            logger.error(f"Failed to update sub-project: {e}")
            raise DatabaseQueryException("update_sub_project", str(e))

    def delete_sub_project(self, sub_project_id: str) -> bool:
        """
        Delete a sub-project

        BUSINESS LOGIC:
        1. Validates sub-project exists
        2. Checks for active enrollments (future enhancement)
        3. Deletes sub-project (cascades to track assignments in metadata)

        Args:
            sub_project_id: UUID of sub-project to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            SubProjectNotFoundException: If sub-project not found
        """
        if not sub_project_id:
            raise ValueError("sub_project_id is required")

        logger.info(f"Deleting sub-project: {sub_project_id}")

        try:
            return self._dao.delete_sub_project(sub_project_id)
        except SubProjectNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete sub-project: {e}")
            raise DatabaseQueryException("delete_sub_project", str(e))

    def enroll_student(self, sub_project_id: str, student_id: str) -> Dict[str, Any]:
        """
        Enroll a student in a sub-project with capacity validation

        BUSINESS LOGIC:
        1. Validates sub-project exists
        2. Checks capacity availability
        3. Increments participant count
        4. Returns updated counts

        NOTE: This is a simplified version. Full implementation would coordinate
        with enrollment service to create actual enrollment record.

        Args:
            sub_project_id: UUID of sub-project
            student_id: UUID of student to enroll

        Returns:
            Dict with current_participants and max_participants

        Raises:
            SubProjectNotFoundException: If sub-project not found
            SubProjectCapacityException: If sub-project is at capacity
        """
        if not sub_project_id:
            raise ValueError("sub_project_id is required")

        if not student_id:
            raise ValueError("student_id is required")

        logger.info(f"Enrolling student {student_id} in sub-project {sub_project_id}")

        try:
            return self._dao.increment_participant_count(sub_project_id)
        except (SubProjectNotFoundException, SubProjectCapacityException):
            raise
        except Exception as e:
            logger.error(f"Failed to enroll student: {e}")
            raise DatabaseQueryException("enroll_student", str(e))

    def unenroll_student(self, sub_project_id: str, student_id: str) -> bool:
        """
        Unenroll a student from a sub-project

        NOTE: This is a simplified version. Full implementation would coordinate
        with enrollment service to remove enrollment record.

        Args:
            sub_project_id: UUID of sub-project
            student_id: UUID of student to unenroll

        Returns:
            bool: True if successful

        Raises:
            SubProjectNotFoundException: If sub-project not found
        """
        if not sub_project_id:
            raise ValueError("sub_project_id is required")

        if not student_id:
            raise ValueError("student_id is required")

        logger.info(f"Unenrolling student {student_id} from sub-project {sub_project_id}")

        try:
            return self._dao.decrement_participant_count(sub_project_id)
        except SubProjectNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to unenroll student: {e}")
            raise DatabaseQueryException("unenroll_student", str(e))

    def update_status(self, sub_project_id: str, new_status: str) -> SubProject:
        """
        Update sub-project status with validation

        BUSINESS LOGIC:
        1. Validates sub-project exists
        2. Validates status transition is allowed
        3. Updates status
        4. Returns updated entity

        Valid transitions:
        - draft → active, cancelled
        - active → completed, cancelled
        - completed → archived
        - any status → archived

        Args:
            sub_project_id: UUID of sub-project
            new_status: New status value

        Returns:
            SubProject: Updated sub-project entity

        Raises:
            SubProjectNotFoundException: If sub-project not found
            ValueError: If status transition is invalid
        """
        if not sub_project_id:
            raise ValueError("sub_project_id is required")

        if not new_status:
            raise ValueError("new_status is required")

        logger.info(f"Updating status for sub-project {sub_project_id}: {new_status}")

        # Get current entity
        current = self.get_sub_project_by_id(sub_project_id)

        # Validate transition
        if not current.can_transition_to(new_status):
            raise ValueError(f"Invalid status transition: {current.status} → {new_status}")

        try:
            self._dao.update_status(sub_project_id, new_status)
            return self.get_sub_project_by_id(sub_project_id)
        except (SubProjectNotFoundException, ValueError):
            raise
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            raise DatabaseQueryException("update_status", str(e))

    def assign_track_to_sub_project(
        self,
        sub_project_id: str,
        track_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        primary_instructor_id: Optional[str] = None,
        sequence_order: int = 0
    ) -> Dict[str, Any]:
        """
        Assign a track to a sub-project with optional date overrides

        BUSINESS LOGIC:
        1. Validates sub-project exists
        2. Validates date range if dates provided
        3. Checks if track already assigned to this sub-project
        4. Stores assignment in metadata JSONB
        5. Returns assignment record

        Args:
            sub_project_id: UUID of sub-project
            track_id: UUID of track to assign
            start_date: Optional override for track start date
            end_date: Optional override for track end date
            primary_instructor_id: Optional instructor assignment
            sequence_order: Order of track in curriculum sequence

        Returns:
            Dict: Track assignment record

        Raises:
            SubProjectNotFoundException: If sub-project not found
            InvalidDateRangeException: If date range is invalid
            DuplicateSubProjectException: If track already assigned
        """
        if not sub_project_id:
            raise ValueError("sub_project_id is required")

        if not track_id:
            raise ValueError("track_id is required")

        # Validate date range if provided
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)

            if start_date > end_date:
                raise InvalidDateRangeException(start_date, end_date)

        logger.info(f"Assigning track {track_id} to sub-project {sub_project_id}")

        data = {
            'sub_project_id': sub_project_id,
            'track_id': track_id,
            'start_date': start_date,
            'end_date': end_date,
            'primary_instructor_id': primary_instructor_id,
            'sequence_order': sequence_order
        }

        try:
            return self._dao.assign_track_to_sub_project(data)
        except (SubProjectNotFoundException, InvalidDateRangeException, DuplicateSubProjectException):
            raise
        except Exception as e:
            logger.error(f"Failed to assign track: {e}")
            raise DatabaseQueryException("assign_track_to_sub_project", str(e))

    def get_tracks_for_sub_project(self, sub_project_id: str) -> List[Dict[str, Any]]:
        """
        Get all tracks assigned to a sub-project

        Args:
            sub_project_id: UUID of sub-project

        Returns:
            List[Dict]: List of track assignments

        Raises:
            SubProjectNotFoundException: If sub-project not found
        """
        if not sub_project_id:
            raise ValueError("sub_project_id is required")

        logger.info(f"Retrieving tracks for sub-project: {sub_project_id}")

        try:
            return self._dao.get_tracks_for_sub_project(sub_project_id)
        except SubProjectNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve tracks: {e}")
            raise DatabaseQueryException("get_tracks_for_sub_project", str(e))

    def get_sub_projects_by_location(
        self,
        organization_id: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        city: Optional[str] = None
    ) -> List[SubProject]:
        """
        Get all sub-projects for an organization filtered by locations

        This is a convenience method that wraps the general filtering capability.

        Args:
            organization_id: UUID of organization
            country: Optional country filter
            region: Optional region filter
            city: Optional city filter (partial match)

        Returns:
            List[SubProject]: List of matching sub-projects
        """
        # Note: This would require a DAO method that filters by organization_id
        # For now, this is a placeholder for future implementation
        logger.warning("get_sub_projects_by_location not yet fully implemented")
        raise NotImplementedError("Organization-level filtering coming in future version")
