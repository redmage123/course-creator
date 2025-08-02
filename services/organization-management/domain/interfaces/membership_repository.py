"""
Repository interface for organization membership management
Follows Interface Segregation Principle
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.entities.enhanced_role import OrganizationMembership, TrackAssignment, RoleType


class IMembershipRepository(ABC):
    """Interface for organization membership data access"""

    @abstractmethod
    async def create_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        """Create new organization membership"""
        pass

    @abstractmethod
    async def get_membership_by_id(self, membership_id: UUID) -> Optional[OrganizationMembership]:
        """Get membership by ID"""
        pass

    @abstractmethod
    async def get_user_membership(self, user_id: UUID, organization_id: UUID) -> Optional[OrganizationMembership]:
        """Get user's membership in specific organization"""
        pass

    @abstractmethod
    async def get_organization_memberships(self, organization_id: UUID, role_type: Optional[RoleType] = None) -> List[OrganizationMembership]:
        """Get all memberships for organization, optionally filtered by role"""
        pass

    @abstractmethod
    async def get_user_memberships(self, user_id: UUID) -> List[OrganizationMembership]:
        """Get all memberships for user across organizations"""
        pass

    @abstractmethod
    async def update_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        """Update existing membership"""
        pass

    @abstractmethod
    async def delete_membership(self, membership_id: UUID) -> bool:
        """Delete membership"""
        pass

    @abstractmethod
    async def activate_membership(self, membership_id: UUID) -> bool:
        """Activate pending membership"""
        pass

    @abstractmethod
    async def deactivate_membership(self, membership_id: UUID) -> bool:
        """Deactivate membership"""
        pass

    @abstractmethod
    async def get_pending_invitations(self, organization_id: UUID) -> List[OrganizationMembership]:
        """Get pending membership invitations"""
        pass


class ITrackAssignmentRepository(ABC):
    """Interface for track assignment data access"""

    @abstractmethod
    async def create_assignment(self, assignment: TrackAssignment) -> TrackAssignment:
        """Create new track assignment"""
        pass

    @abstractmethod
    async def get_assignment_by_id(self, assignment_id: UUID) -> Optional[TrackAssignment]:
        """Get assignment by ID"""
        pass

    @abstractmethod
    async def get_user_track_assignments(self, user_id: UUID, role_type: Optional[RoleType] = None) -> List[TrackAssignment]:
        """Get all track assignments for user"""
        pass

    @abstractmethod
    async def get_track_assignments(self, track_id: UUID, role_type: Optional[RoleType] = None) -> List[TrackAssignment]:
        """Get all assignments for track"""
        pass

    @abstractmethod
    async def get_instructor_assignments(self, instructor_id: UUID) -> List[TrackAssignment]:
        """Get all track assignments for instructor"""
        pass

    @abstractmethod
    async def get_student_assignments(self, student_id: UUID) -> List[TrackAssignment]:
        """Get all track assignments for student"""
        pass

    @abstractmethod
    async def update_assignment(self, assignment: TrackAssignment) -> TrackAssignment:
        """Update existing assignment"""
        pass

    @abstractmethod
    async def delete_assignment(self, assignment_id: UUID) -> bool:
        """Delete assignment"""
        pass

    @abstractmethod
    async def deactivate_assignment(self, assignment_id: UUID) -> bool:
        """Deactivate assignment"""
        pass

    @abstractmethod
    async def complete_assignment(self, assignment_id: UUID) -> bool:
        """Mark assignment as completed"""
        pass

    @abstractmethod
    async def exists_assignment(self, user_id: UUID, track_id: UUID, role_type: RoleType) -> bool:
        """Check if assignment exists"""
        pass

    @abstractmethod
    async def get_project_assignments(self, project_id: UUID, role_type: Optional[RoleType] = None) -> List[TrackAssignment]:
        """Get all assignments for project tracks"""
        pass