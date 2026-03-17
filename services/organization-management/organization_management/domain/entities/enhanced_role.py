"""
Enhanced Role System with Granular Permissions
Implements comprehensive RBAC for organization management
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime


class Permission(Enum):
    """Granular permissions for the system"""
    # Site Admin Powers
    DELETE_ANY_ORGANIZATION = "delete_any_organization"
    VIEW_ALL_ORGANIZATIONS = "view_all_organizations"
    MANAGE_SITE_SETTINGS = "manage_site_settings"

    # Organization Admin Powers
    MANAGE_ORGANIZATION = "manage_organization"
    ADD_ORGANIZATION_ADMINS = "add_organization_admins"
    REMOVE_ORGANIZATION_ADMINS = "remove_organization_admins"
    ADD_INSTRUCTORS_TO_ORG = "add_instructors_to_org"
    REMOVE_INSTRUCTORS_FROM_ORG = "remove_instructors_from_org"
    CREATE_PROJECTS = "create_projects"
    DELETE_PROJECTS = "delete_projects"

    # Project Management Powers
    CREATE_TRACKS = "create_tracks"
    DELETE_TRACKS = "delete_tracks"
    ASSIGN_STUDENTS_TO_TRACKS = "assign_students_to_tracks"
    ASSIGN_INSTRUCTORS_TO_TRACKS = "assign_instructors_to_tracks"
    MANAGE_TRACK_MODULES = "manage_track_modules"

    # Course Management Powers
    VIEW_COURSES = "view_courses"
    MANAGE_COURSES = "manage_courses"
    DELETE_COURSES = "delete_courses"

    # Sub-Project Management Powers
    DELETE_SUBPROJECTS = "delete_subprojects"

    # Instructor Assignment Powers
    MANAGE_INSTRUCTORS = "manage_instructors"
    VIEW_INSTRUCTORS = "view_instructors"

    # Scheduling Powers
    VIEW_SCHEDULES = "view_schedules"
    MANAGE_SCHEDULES = "manage_schedules"

    # Meeting Room Integration Powers
    CREATE_TEAMS_ROOMS = "create_teams_rooms"
    CREATE_ZOOM_ROOMS = "create_zoom_rooms"
    CREATE_SLACK_ROOMS = "create_slack_rooms"
    MANAGE_MEETING_ROOMS = "manage_meeting_rooms"

    # Student Management Powers
    ADD_STUDENTS_TO_PROJECT = "add_students_to_project"
    REMOVE_STUDENTS_FROM_PROJECT = "remove_students_from_project"
    VIEW_STUDENT_PROGRESS = "view_student_progress"

    # Instructor Powers
    TEACH_TRACKS = "teach_tracks"
    GRADE_STUDENTS = "grade_students"
    VIEW_ASSIGNED_STUDENTS = "view_assigned_students"
    MANAGE_ASSIGNED_CONTENT = "manage_assigned_content"

    # Student Powers
    ACCESS_ASSIGNED_TRACKS = "access_assigned_tracks"
    SUBMIT_ASSIGNMENTS = "submit_assignments"
    VIEW_OWN_PROGRESS = "view_own_progress"

    # Guest Powers (Read-Only, Limited Access)
    ACCESS_DEMO_SERVICE = "access_demo_service"
    VIEW_PUBLIC_COURSES = "view_public_courses"
    USE_AI_ASSISTANT_LIMITED = "use_ai_assistant_limited"
    BROWSE_COURSE_CATALOG = "browse_course_catalog"


class RoleType(Enum):
    """
    Enhanced role types with clear hierarchy

    BUSINESS CONTEXT:
    The platform supports 5 user role types:
    - SITE_ADMIN: Platform-wide administration
    - ORGANIZATION_ADMIN: Organization-level management
    - INSTRUCTOR: Course creation and student management
    - STUDENT: Learning and coursework submission
    - GUEST: Unauthenticated users with read-only demo access
    """
    SITE_ADMIN = "site_admin"
    ORGANIZATION_ADMIN = "organization_admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"
    GUEST = "guest"

@dataclass

class EnhancedRole:
    """Enhanced role with granular permissions and context"""
    role_type: RoleType
    permissions: Set[Permission] = field(default_factory=set)
    organization_id: Optional[UUID] = None
    project_ids: List[UUID] = field(default_factory=list)
    track_ids: List[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Automatically assign permissions based on role type"""
        if not self.permissions:
            self.permissions = self._get_default_permissions()

    def _get_default_permissions(self) -> Set[Permission]:
        """Get default permissions for role type"""
        permission_map = {
            RoleType.SITE_ADMIN: {
                Permission.DELETE_ANY_ORGANIZATION,
                Permission.VIEW_ALL_ORGANIZATIONS,
                Permission.MANAGE_SITE_SETTINGS,
                Permission.MANAGE_ORGANIZATION,
                Permission.ADD_ORGANIZATION_ADMINS,
                Permission.REMOVE_ORGANIZATION_ADMINS,
                Permission.ADD_INSTRUCTORS_TO_ORG,
                Permission.REMOVE_INSTRUCTORS_FROM_ORG,
                Permission.CREATE_PROJECTS,
                Permission.DELETE_PROJECTS,
                Permission.CREATE_TRACKS,
                Permission.DELETE_TRACKS,
                Permission.DELETE_SUBPROJECTS,
                Permission.ASSIGN_STUDENTS_TO_TRACKS,
                Permission.ASSIGN_INSTRUCTORS_TO_TRACKS,
                Permission.MANAGE_TRACK_MODULES,
                Permission.VIEW_COURSES,
                Permission.MANAGE_COURSES,
                Permission.DELETE_COURSES,
                Permission.MANAGE_INSTRUCTORS,
                Permission.VIEW_INSTRUCTORS,
                Permission.VIEW_SCHEDULES,
                Permission.MANAGE_SCHEDULES,
                Permission.CREATE_TEAMS_ROOMS,
                Permission.CREATE_ZOOM_ROOMS,
                Permission.CREATE_SLACK_ROOMS,
                Permission.MANAGE_MEETING_ROOMS,
                Permission.ADD_STUDENTS_TO_PROJECT,
                Permission.REMOVE_STUDENTS_FROM_PROJECT,
                Permission.VIEW_STUDENT_PROGRESS
            },
            RoleType.ORGANIZATION_ADMIN: {
                Permission.MANAGE_ORGANIZATION,
                Permission.ADD_ORGANIZATION_ADMINS,
                Permission.REMOVE_ORGANIZATION_ADMINS,
                Permission.ADD_INSTRUCTORS_TO_ORG,
                Permission.REMOVE_INSTRUCTORS_FROM_ORG,
                Permission.CREATE_PROJECTS,
                Permission.DELETE_PROJECTS,
                Permission.CREATE_TRACKS,
                Permission.DELETE_TRACKS,
                Permission.DELETE_SUBPROJECTS,
                Permission.ASSIGN_STUDENTS_TO_TRACKS,
                Permission.ASSIGN_INSTRUCTORS_TO_TRACKS,
                Permission.MANAGE_TRACK_MODULES,
                Permission.VIEW_COURSES,
                Permission.MANAGE_COURSES,
                Permission.DELETE_COURSES,
                Permission.MANAGE_INSTRUCTORS,
                Permission.VIEW_INSTRUCTORS,
                Permission.VIEW_SCHEDULES,
                Permission.MANAGE_SCHEDULES,
                Permission.CREATE_TEAMS_ROOMS,
                Permission.CREATE_ZOOM_ROOMS,
                Permission.CREATE_SLACK_ROOMS,
                Permission.MANAGE_MEETING_ROOMS,
                Permission.ADD_STUDENTS_TO_PROJECT,
                Permission.REMOVE_STUDENTS_FROM_PROJECT,
                Permission.VIEW_STUDENT_PROGRESS
            },
            RoleType.INSTRUCTOR: {
                Permission.TEACH_TRACKS,
                Permission.GRADE_STUDENTS,
                Permission.VIEW_ASSIGNED_STUDENTS,
                Permission.MANAGE_ASSIGNED_CONTENT,
                Permission.VIEW_STUDENT_PROGRESS,
                Permission.VIEW_COURSES,
                Permission.VIEW_INSTRUCTORS,
                Permission.VIEW_SCHEDULES
            },
            RoleType.STUDENT: {
                Permission.ACCESS_ASSIGNED_TRACKS,
                Permission.SUBMIT_ASSIGNMENTS,
                Permission.VIEW_OWN_PROGRESS,
                Permission.VIEW_COURSES
            },
            RoleType.GUEST: {
                Permission.ACCESS_DEMO_SERVICE,
                Permission.VIEW_PUBLIC_COURSES,
                Permission.VIEW_COURSES,
                Permission.USE_AI_ASSISTANT_LIMITED,
                Permission.BROWSE_COURSE_CATALOG
            }
        }

        return permission_map.get(self.role_type, set())

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions

    def can_manage_organization(self, org_id: UUID) -> bool:
        """Check if can manage specific organization"""
        if self.role_type == RoleType.SITE_ADMIN:
            return True

        return (
            self.has_permission(Permission.MANAGE_ORGANIZATION) and
            self.organization_id == org_id
        )

    def can_manage_project(self, project_id: UUID) -> bool:
        """Check if can manage specific project"""
        if self.role_type == RoleType.SITE_ADMIN:
            return True

        return (
            self.has_permission(Permission.CREATE_PROJECTS) and
            (not self.project_ids or project_id in self.project_ids)
        )

    def can_teach_track(self, track_id: UUID) -> bool:
        """Check if can teach specific track"""
        return (
            self.has_permission(Permission.TEACH_TRACKS) and
            (not self.track_ids or track_id in self.track_ids)
        )

    def can_access_track(self, track_id: UUID) -> bool:
        """Check if can access specific track (for students)"""
        return (
            self.has_permission(Permission.ACCESS_ASSIGNED_TRACKS) and
            track_id in self.track_ids
        )

    def add_project_access(self, project_id: UUID):
        """
        Add project access to role

        BUSINESS REQUIREMENT:
        Guest users cannot be assigned to projects - they have read-only access
        """
        # Guest role cannot have project assignments
        if self.role_type == RoleType.GUEST:
            return  # Silently ignore for guest role

        if project_id not in self.project_ids:
            self.project_ids.append(project_id)

    def add_track_access(self, track_id: UUID):
        """
        Add track access to role

        BUSINESS REQUIREMENT:
        Guest users cannot be assigned to tracks - they have read-only access
        """
        # Guest role cannot have track assignments
        if self.role_type == RoleType.GUEST:
            return  # Silently ignore for guest role

        if track_id not in self.track_ids:
            self.track_ids.append(track_id)

    def remove_project_access(self, project_id: UUID):
        """Remove project access from role"""
        if project_id in self.project_ids:
            self.project_ids.remove(project_id)

    def remove_track_access(self, track_id: UUID):
        """Remove track access from role"""
        if track_id in self.track_ids:
            self.track_ids.remove(track_id)

    def is_valid(self) -> bool:
        """
        Validate role configuration

        BUSINESS REQUIREMENT:
        - Organization-scoped roles (ORG_ADMIN, INSTRUCTOR, STUDENT) require organization_id
        - Platform-scoped roles (SITE_ADMIN, GUEST) do NOT require organization_id
        - Guest role is valid without organization_id (not organization-scoped)
        """
        if not self.role_type:
            return False

        # Organization-scoped roles must have organization_id
        # Guest and Site Admin are NOT organization-scoped
        if self.role_type in [RoleType.ORGANIZATION_ADMIN, RoleType.INSTRUCTOR, RoleType.STUDENT]:
            if not self.organization_id:
                return False

        return True

    def to_dict(self) -> Dict:
        """Convert role to dictionary representation"""
        return {
            "role_type": self.role_type.value,
            "permissions": [p.value for p in self.permissions],
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "project_ids": [str(pid) for pid in self.project_ids],
            "track_ids": [str(tid) for tid in self.track_ids],
            "created_at": self.created_at.isoformat()
        }

@dataclass

class OrganizationMembership:
    """Represents a user's membership in an organization"""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = None
    organization_id: UUID = None
    role: EnhancedRole = None
    invited_by: Optional[UUID] = None
    invited_at: datetime = field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    status: str = "pending"  # pending, active, inactive

    def accept_invitation(self):
        """
        Accept membership invitation to join organization

        BUSINESS PURPOSE:
        Transitions membership from pending to active status when user accepts
        invitation. Users must explicitly accept to comply with consent requirements.

        WHY THIS APPROACH:
        - Records acceptance timestamp for audit trail
        - Status change enables access to organization resources
        - Explicit acceptance ensures user awareness of membership

        Returns:
            None - updates entity in place
        """
        self.status = "active"
        self.accepted_at = datetime.utcnow()

    def deactivate(self):
        """
        Deactivate organization membership

        BUSINESS PURPOSE:
        Suspends user access to organization without deleting membership record.
        Used for temporary suspensions, role changes, or voluntary departures.

        WHY THIS APPROACH:
        - Preserves membership history for audit trail
        - Reversible operation (can be reactivated)
        - Does not delete user data or progress

        MULTI-TENANT CONSIDERATION:
        User retains memberships in other organizations. Only this specific
        organization membership is deactivated.

        Returns:
            None - updates entity in place
        """
        self.status = "inactive"

    def is_active(self) -> bool:
        """
        Check if membership is currently active

        BUSINESS PURPOSE:
        Quick status check for permission validation. Inactive members cannot
        access organization resources even if they have valid roles.

        WHY THIS APPROACH:
        - Simple boolean for readability
        - Encapsulates status check logic
        - Used throughout permission checks

        Returns:
            bool: True if status is "active", False otherwise
        """
        return self.status == "active"

    def is_valid(self) -> bool:
        """
        Validate membership entity data integrity

        BUSINESS PURPOSE:
        Ensures membership has all required references before creation or updates.
        Prevents orphaned memberships or invalid role assignments.

        WHY THIS APPROACH:
        - Validates foreign key relationships (user, organization)
        - Delegates role validation to EnhancedRole.is_valid()
        - Comprehensive check prevents data corruption

        VALIDATION RULES:
        - user_id must be set (valid user reference)
        - organization_id must be set (valid organization reference)
        - role must be set and pass role.is_valid() check

        Returns:
            bool: True if all validations pass, False otherwise
        """
        return (
            self.user_id is not None and
            self.organization_id is not None and
            self.role is not None and
            self.role.is_valid()
        )

@dataclass

class TrackAssignment:
    """Represents assignment of instructor or student to track"""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = None
    track_id: UUID = None
    role_type: RoleType = None  # INSTRUCTOR or STUDENT
    assigned_by: UUID = None
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"  # active, inactive, completed

    def is_instructor_assignment(self) -> bool:
        """
        Check if this is an instructor assignment to track

        BUSINESS PURPOSE:
        Determines if assignment represents an instructor teaching assignment.
        Used for filtering and permission checks.

        WHY THIS APPROACH:
        - Simple role type check for readability
        - Returns boolean for conditional logic
        - Encapsulates role type comparison

        Returns:
            bool: True if role_type is INSTRUCTOR, False otherwise
        """
        return self.role_type == RoleType.INSTRUCTOR

    def is_student_assignment(self) -> bool:
        """
        Check if this is a student enrollment to track

        BUSINESS PURPOSE:
        Determines if assignment represents a student enrollment.
        Used for filtering and permission checks.

        WHY THIS APPROACH:
        - Simple role type check for readability
        - Returns boolean for conditional logic
        - Encapsulates role type comparison

        Returns:
            bool: True if role_type is STUDENT, False otherwise
        """
        return self.role_type == RoleType.STUDENT

    def complete(self):
        """
        Mark track assignment as completed

        BUSINESS PURPOSE:
        Records that user has finished the track (student completion or
        instructor teaching term ended).

        WHY THIS APPROACH:
        - Status change preserves assignment record
        - No timestamp update (assigned_at remains original)
        - Allows analytics on completion rates

        BUSINESS RULE:
        Completed assignments remain in system for progress tracking and
        certificate generation. Do not delete completed assignments.

        Returns:
            None - updates entity in place
        """
        self.status = "completed"

    def deactivate(self):
        """
        Deactivate track assignment

        BUSINESS PURPOSE:
        Suspends user access to track without deleting assignment record.
        Used for temporary removals or role changes.

        WHY THIS APPROACH:
        - Preserves assignment history for audit trail
        - Reversible operation (can be reactivated)
        - Does not delete progress data

        BUSINESS RULE:
        Deactivated students cannot access track materials.
        Deactivated instructors cannot grade assignments.

        Returns:
            None - updates entity in place
        """
        self.status = "inactive"

    def is_valid(self) -> bool:
        """
        Validate track assignment data integrity

        BUSINESS PURPOSE:
        Ensures assignment has all required references before creation.
        Prevents orphaned assignments or invalid role assignments.

        WHY THIS APPROACH:
        - Validates foreign key relationships (user, track)
        - Ensures role type is set (INSTRUCTOR or STUDENT)
        - Requires assigned_by for audit trail

        VALIDATION RULES:
        - user_id must be set (valid user reference)
        - track_id must be set (valid track reference)
        - role_type must be INSTRUCTOR or STUDENT
        - assigned_by must be set (org admin who created assignment)

        Returns:
            bool: True if all validations pass, False otherwise
        """
        return (
            self.user_id is not None and
            self.track_id is not None and
            self.role_type is not None and
            self.assigned_by is not None
        )