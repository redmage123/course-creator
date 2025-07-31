"""
Organization Membership Management Service
Handles organization membership, roles, and permissions
"""
from typing import List, Optional, Dict
from uuid import UUID
import logging
from datetime import datetime

from domain.entities.enhanced_role import (
    OrganizationMembership, TrackAssignment, EnhancedRole,
    RoleType, Permission
)
from domain.interfaces.membership_repository import IMembershipRepository, ITrackAssignmentRepository
from domain.interfaces.user_repository import IUserRepository


class MembershipService:
    """Service for organization membership management"""

    def __init__(
        self,
        membership_repository: IMembershipRepository,
        track_assignment_repository: ITrackAssignmentRepository,
        user_repository: IUserRepository
    ):
        self._membership_repository = membership_repository
        self._track_assignment_repository = track_assignment_repository
        self._user_repository = user_repository
        self._logger = logging.getLogger(__name__)

    async def add_organization_admin(
        self,
        organization_id: UUID,
        user_email: str,
        invited_by: UUID
    ) -> OrganizationMembership:
        """Add organization admin to organization"""
        try:
            # Get or create user
            user = await self._user_repository.get_by_email(user_email)
            if not user:
                # Create pending user
                user = await self._user_repository.create_pending_user(user_email)

            # Check if membership already exists
            existing = await self._membership_repository.get_user_membership(
                user.id, organization_id
            )
            if existing and existing.is_active():
                raise ValueError(f"User {user_email} is already a member of this organization")

            # Create organization admin role
            admin_role = EnhancedRole(
                role_type=RoleType.ORGANIZATION_ADMIN,
                organization_id=organization_id
            )

            # Create membership
            membership = OrganizationMembership(
                user_id=user.id,
                organization_id=organization_id,
                role=admin_role,
                invited_by=invited_by
            )

            if not membership.is_valid():
                raise ValueError("Invalid membership data")

            created_membership = await self._membership_repository.create_membership(membership)

            self._logger.info(f"Added organization admin {user_email} to organization {organization_id}")
            return created_membership

        except Exception as e:
            self._logger.error(f"Failed to add organization admin: {e}")
            raise

    async def add_instructor_to_organization(
        self,
        organization_id: UUID,
        user_email: str,
        invited_by: UUID,
        project_ids: Optional[List[UUID]] = None
    ) -> OrganizationMembership:
        """Add instructor to organization"""
        try:
            # Get or create user
            user = await self._user_repository.get_by_email(user_email)
            if not user:
                user = await self._user_repository.create_pending_user(user_email)

            # Check if membership already exists
            existing = await self._membership_repository.get_user_membership(
                user.id, organization_id
            )
            if existing and existing.is_active():
                raise ValueError(f"User {user_email} is already a member of this organization")

            # Create instructor role
            instructor_role = EnhancedRole(
                role_type=RoleType.INSTRUCTOR,
                organization_id=organization_id,
                project_ids=project_ids or []
            )

            # Create membership
            membership = OrganizationMembership(
                user_id=user.id,
                organization_id=organization_id,
                role=instructor_role,
                invited_by=invited_by
            )

            if not membership.is_valid():
                raise ValueError("Invalid membership data")

            created_membership = await self._membership_repository.create_membership(membership)

            self._logger.info(f"Added instructor {user_email} to organization {organization_id}")
            return created_membership

        except Exception as e:
            self._logger.error(f"Failed to add instructor to organization: {e}")
            raise

    async def add_student_to_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        user_email: str,
        track_id: UUID,
        assigned_by: UUID
    ) -> tuple[OrganizationMembership, TrackAssignment]:
        """Add student to project and assign to track"""
        try:
            # Get or create user
            user = await self._user_repository.get_by_email(user_email)
            if not user:
                user = await self._user_repository.create_pending_user(user_email)

            # Check if organization membership exists
            membership = await self._membership_repository.get_user_membership(
                user.id, organization_id
            )

            if not membership:
                # Create student organization membership
                student_role = EnhancedRole(
                    role_type=RoleType.STUDENT,
                    organization_id=organization_id,
                    project_ids=[project_id],
                    track_ids=[track_id]
                )

                membership = OrganizationMembership(
                    user_id=user.id,
                    organization_id=organization_id,
                    role=student_role,
                    invited_by=assigned_by
                )

                membership = await self._membership_repository.create_membership(membership)
            else:
                # Update existing membership to add project and track access
                membership.role.add_project_access(project_id)
                membership.role.add_track_access(track_id)
                membership = await self._membership_repository.update_membership(membership)

            # Create track assignment
            assignment = TrackAssignment(
                user_id=user.id,
                track_id=track_id,
                role_type=RoleType.STUDENT,
                assigned_by=assigned_by
            )

            created_assignment = await self._track_assignment_repository.create_assignment(assignment)

            self._logger.info(f"Added student {user_email} to project {project_id} and track {track_id}")
            return membership, created_assignment

        except Exception as e:
            self._logger.error(f"Failed to add student to project: {e}")
            raise

    async def assign_instructor_to_track(
        self,
        instructor_id: UUID,
        track_id: UUID,
        assigned_by: UUID
    ) -> TrackAssignment:
        """Assign instructor to teach a track"""
        try:
            # Check if assignment already exists
            exists = await self._track_assignment_repository.exists_assignment(
                instructor_id, track_id, RoleType.INSTRUCTOR
            )
            if exists:
                raise ValueError("Instructor is already assigned to this track")

            # Create assignment
            assignment = TrackAssignment(
                user_id=instructor_id,
                track_id=track_id,
                role_type=RoleType.INSTRUCTOR,
                assigned_by=assigned_by
            )

            created_assignment = await self._track_assignment_repository.create_assignment(assignment)

            # Update instructor's organization membership to include track access
            # This would require getting the instructor's membership and updating it

            self._logger.info(f"Assigned instructor {instructor_id} to track {track_id}")
            return created_assignment

        except Exception as e:
            self._logger.error(f"Failed to assign instructor to track: {e}")
            raise

    async def remove_organization_member(
        self,
        membership_id: UUID,
        removed_by: UUID
    ) -> bool:
        """Remove member from organization"""
        try:
            # Get membership
            membership = await self._membership_repository.get_membership_by_id(membership_id)
            if not membership:
                raise ValueError("Membership not found")

            # Deactivate membership
            success = await self._membership_repository.deactivate_membership(membership_id)

            # Deactivate all track assignments for this user in this organization
            user_assignments = await self._track_assignment_repository.get_user_track_assignments(
                membership.user_id
            )

            for assignment in user_assignments:
                await self._track_assignment_repository.deactivate_assignment(assignment.id)

            self._logger.info(f"Removed organization member {membership.user_id}")
            return success

        except Exception as e:
            self._logger.error(f"Failed to remove organization member: {e}")
            raise

    async def get_organization_members(
        self,
        organization_id: UUID,
        role_type: Optional[RoleType] = None
    ) -> List[Dict]:
        """Get organization members with user details"""
        try:
            memberships = await self._membership_repository.get_organization_memberships(
                organization_id, role_type
            )

            members = []
            for membership in memberships:
                user = await self._user_repository.get_by_id(membership.user_id)
                if user:
                    members.append({
                        "membership_id": str(membership.id),
                        "user_id": str(user.id),
                        "email": user.email,
                        "name": user.name,
                        "role_type": membership.role.role_type.value,
                        "permissions": [p.value for p in membership.role.permissions],
                        "project_ids": [str(pid) for pid in membership.role.project_ids],
                        "track_ids": [str(tid) for tid in membership.role.track_ids],
                        "status": membership.status,
                        "invited_at": membership.invited_at.isoformat(),
                        "accepted_at": membership.accepted_at.isoformat() if membership.accepted_at else None
                    })

            return members

        except Exception as e:
            self._logger.error(f"Failed to get organization members: {e}")
            raise

    async def get_track_instructors(self, track_id: UUID) -> List[Dict]:
        """Get instructors assigned to track"""
        try:
            assignments = await self._track_assignment_repository.get_track_assignments(
                track_id, RoleType.INSTRUCTOR
            )

            instructors = []
            for assignment in assignments:
                user = await self._user_repository.get_by_id(assignment.user_id)
                if user:
                    instructors.append({
                        "assignment_id": str(assignment.id),
                        "user_id": str(user.id),
                        "email": user.email,
                        "name": user.name,
                        "assigned_at": assignment.assigned_at.isoformat(),
                        "status": assignment.status
                    })

            return instructors

        except Exception as e:
            self._logger.error(f"Failed to get track instructors: {e}")
            raise

    async def get_track_students(self, track_id: UUID) -> List[Dict]:
        """Get students assigned to track"""
        try:
            assignments = await self._track_assignment_repository.get_track_assignments(
                track_id, RoleType.STUDENT
            )

            students = []
            for assignment in assignments:
                user = await self._user_repository.get_by_id(assignment.user_id)
                if user:
                    students.append({
                        "assignment_id": str(assignment.id),
                        "user_id": str(user.id),
                        "email": user.email,
                        "name": user.name,
                        "assigned_at": assignment.assigned_at.isoformat(),
                        "status": assignment.status
                    })

            return students

        except Exception as e:
            self._logger.error(f"Failed to get track students: {e}")
            raise

    async def check_user_permission(
        self,
        user_id: UUID,
        organization_id: UUID,
        permission: Permission
    ) -> bool:
        """Check if user has specific permission in organization"""
        try:
            membership = await self._membership_repository.get_user_membership(
                user_id, organization_id
            )

            if not membership or not membership.is_active():
                return False

            return membership.role.has_permission(permission)

        except Exception as e:
            self._logger.error(f"Failed to check user permission: {e}")
            return False

    async def accept_membership_invitation(self, membership_id: UUID) -> bool:
        """Accept membership invitation"""
        try:
            success = await self._membership_repository.activate_membership(membership_id)

            if success:
                self._logger.info(f"Accepted membership invitation {membership_id}")

            return success

        except Exception as e:
            self._logger.error(f"Failed to accept membership invitation: {e}")
            raise
