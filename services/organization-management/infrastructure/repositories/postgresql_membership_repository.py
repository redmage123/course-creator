"""
PostgreSQL implementation of membership repository
Follows DAO pattern with proper database interaction
"""
import json
from typing import List, Optional
from uuid import UUID
import asyncpg

from domain.interfaces.membership_repository import IMembershipRepository, ITrackAssignmentRepository
from domain.entities.enhanced_role import OrganizationMembership, TrackAssignment, EnhancedRole, RoleType


class PostgreSQLMembershipRepository(IMembershipRepository):
    """PostgreSQL implementation of membership repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def create_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        """Create new organization membership"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow("""
                INSERT INTO organization_memberships (
                    id, user_id, organization_id, role_type, permissions,
                    project_ids, track_ids, invited_by, invited_at,
                    accepted_at, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
            """,
                membership.id,
                membership.user_id,
                membership.organization_id,
                membership.role.role_type.value,
                [p.value for p in membership.role.permissions],
                [str(pid) for pid in membership.role.project_ids],
                [str(tid) for tid in membership.role.track_ids],
                membership.invited_by,
                membership.invited_at,
                membership.accepted_at,
                membership.status
            )

            return self._row_to_membership(row)

    async def get_membership_by_id(self, membership_id: UUID) -> Optional[OrganizationMembership]:
        """Get membership by ID"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT * FROM organization_memberships WHERE id = $1",
                membership_id
            )

            return self._row_to_membership(row) if row else None

    async def get_user_membership(self, user_id: UUID, organization_id: UUID) -> Optional[OrganizationMembership]:
        """Get user's membership in specific organization"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow("""
                SELECT * FROM organization_memberships
                WHERE user_id = $1 AND organization_id = $2 AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """, user_id, organization_id)

            return self._row_to_membership(row) if row else None

    async def get_organization_memberships(self, organization_id: UUID, role_type: Optional[RoleType] = None) -> List[OrganizationMembership]:
        """Get all memberships for organization, optionally filtered by role"""
        async with self.db_pool.acquire() as connection:
            if role_type:
                rows = await connection.fetch("""
                    SELECT * FROM organization_memberships
                    WHERE organization_id = $1 AND role_type = $2
                    ORDER BY created_at DESC
                """, organization_id, role_type.value)
            else:
                rows = await connection.fetch("""
                    SELECT * FROM organization_memberships
                    WHERE organization_id = $1
                    ORDER BY created_at DESC
                """, organization_id)

            return [self._row_to_membership(row) for row in rows]

    async def get_user_memberships(self, user_id: UUID) -> List[OrganizationMembership]:
        """Get all memberships for user across organizations"""
        async with self.db_pool.acquire() as connection:
            rows = await connection.fetch("""
                SELECT * FROM organization_memberships
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, user_id)

            return [self._row_to_membership(row) for row in rows]

    async def update_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        """Update existing membership"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow("""
                UPDATE organization_memberships SET
                    role_type = $2,
                    permissions = $3,
                    project_ids = $4,
                    track_ids = $5,
                    accepted_at = $6,
                    status = $7,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                RETURNING *
            """,
                membership.id,
                membership.role.role_type.value,
                [p.value for p in membership.role.permissions],
                [str(pid) for pid in membership.role.project_ids],
                [str(tid) for tid in membership.role.track_ids],
                membership.accepted_at,
                membership.status
            )

            return self._row_to_membership(row)

    async def delete_membership(self, membership_id: UUID) -> bool:
        """Delete membership"""
        async with self.db_pool.acquire() as connection:
            result = await connection.execute(
                "DELETE FROM organization_memberships WHERE id = $1",
                membership_id
            )

            return result == "DELETE 1"

    async def activate_membership(self, membership_id: UUID) -> bool:
        """Activate pending membership"""
        async with self.db_pool.acquire() as connection:
            result = await connection.execute("""
                UPDATE organization_memberships SET
                    status = 'active',
                    accepted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND status = 'pending'
            """, membership_id)

            return result == "UPDATE 1"

    async def deactivate_membership(self, membership_id: UUID) -> bool:
        """Deactivate membership"""
        async with self.db_pool.acquire() as connection:
            result = await connection.execute("""
                UPDATE organization_memberships SET
                    status = 'inactive',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, membership_id)

            return result == "UPDATE 1"

    async def get_pending_invitations(self, organization_id: UUID) -> List[OrganizationMembership]:
        """Get pending membership invitations"""
        async with self.db_pool.acquire() as connection:
            rows = await connection.fetch("""
                SELECT * FROM organization_memberships
                WHERE organization_id = $1 AND status = 'pending'
                ORDER BY invited_at DESC
            """, organization_id)

            return [self._row_to_membership(row) for row in rows]

    def _row_to_membership(self, row) -> Optional[OrganizationMembership]:
        """Convert database row to OrganizationMembership entity"""
        if not row:
            return None

        # Create enhanced role
        role = EnhancedRole(
            role_type=RoleType(row['role_type']),
            permissions=set(getattr(p, 'value', p) for p in (row['permissions'] or [])),
            organization_id=row['organization_id'],
            project_ids=[UUID(pid) for pid in (row['project_ids'] or [])],
            track_ids=[UUID(tid) for tid in (row['track_ids'] or [])]
        )

        return OrganizationMembership(
            id=row['id'],
            user_id=row['user_id'],
            organization_id=row['organization_id'],
            role=role,
            invited_by=row['invited_by'],
            invited_at=row['invited_at'],
            accepted_at=row['accepted_at'],
            status=row['status']
        )


class PostgreSQLTrackAssignmentRepository(ITrackAssignmentRepository):
    """PostgreSQL implementation of track assignment repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def create_assignment(self, assignment: TrackAssignment) -> TrackAssignment:
        """Create new track assignment"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow("""
                INSERT INTO track_assignments (
                    id, user_id, track_id, role_type, assigned_by,
                    assigned_at, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """,
                assignment.id,
                assignment.user_id,
                assignment.track_id,
                assignment.role_type.value,
                assignment.assigned_by,
                assignment.assigned_at,
                assignment.status
            )

            return self._row_to_assignment(row)

    async def get_assignment_by_id(self, assignment_id: UUID) -> Optional[TrackAssignment]:
        """Get assignment by ID"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT * FROM track_assignments WHERE id = $1",
                assignment_id
            )

            return self._row_to_assignment(row) if row else None

    async def get_user_track_assignments(self, user_id: UUID, role_type: Optional[RoleType] = None) -> List[TrackAssignment]:
        """Get all track assignments for user"""
        async with self.db_pool.acquire() as connection:
            if role_type:
                rows = await connection.fetch("""
                    SELECT * FROM track_assignments
                    WHERE user_id = $1 AND role_type = $2
                    ORDER BY assigned_at DESC
                """, user_id, role_type.value)
            else:
                rows = await connection.fetch("""
                    SELECT * FROM track_assignments
                    WHERE user_id = $1
                    ORDER BY assigned_at DESC
                """, user_id)

            return [self._row_to_assignment(row) for row in rows]

    async def get_track_assignments(self, track_id: UUID, role_type: Optional[RoleType] = None) -> List[TrackAssignment]:
        """Get all assignments for track"""
        async with self.db_pool.acquire() as connection:
            if role_type:
                rows = await connection.fetch("""
                    SELECT * FROM track_assignments
                    WHERE track_id = $1 AND role_type = $2 AND status = 'active'
                    ORDER BY assigned_at DESC
                """, track_id, role_type.value)
            else:
                rows = await connection.fetch("""
                    SELECT * FROM track_assignments
                    WHERE track_id = $1 AND status = 'active'
                    ORDER BY assigned_at DESC
                """, track_id)

            return [self._row_to_assignment(row) for row in rows]

    async def get_instructor_assignments(self, instructor_id: UUID) -> List[TrackAssignment]:
        """Get all track assignments for instructor"""
        async with self.db_pool.acquire() as connection:
            rows = await connection.fetch("""
                SELECT * FROM track_assignments
                WHERE user_id = $1 AND role_type = 'instructor' AND status = 'active'
                ORDER BY assigned_at DESC
            """, instructor_id)

            return [self._row_to_assignment(row) for row in rows]

    async def get_student_assignments(self, student_id: UUID) -> List[TrackAssignment]:
        """Get all track assignments for student"""
        async with self.db_pool.acquire() as connection:
            rows = await connection.fetch("""
                SELECT * FROM track_assignments
                WHERE user_id = $1 AND role_type = 'student' AND status = 'active'
                ORDER BY assigned_at DESC
            """, student_id)

            return [self._row_to_assignment(row) for row in rows]

    async def update_assignment(self, assignment: TrackAssignment) -> TrackAssignment:
        """Update existing assignment"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow("""
                UPDATE track_assignments SET
                    status = $2
                WHERE id = $1
                RETURNING *
            """,
                assignment.id,
                assignment.status
            )

            return self._row_to_assignment(row)

    async def delete_assignment(self, assignment_id: UUID) -> bool:
        """Delete assignment"""
        async with self.db_pool.acquire() as connection:
            result = await connection.execute(
                "DELETE FROM track_assignments WHERE id = $1",
                assignment_id
            )

            return result == "DELETE 1"

    async def deactivate_assignment(self, assignment_id: UUID) -> bool:
        """Deactivate assignment"""
        async with self.db_pool.acquire() as connection:
            result = await connection.execute("""
                UPDATE track_assignments SET status = 'inactive'
                WHERE id = $1
            """, assignment_id)

            return result == "UPDATE 1"

    async def complete_assignment(self, assignment_id: UUID) -> bool:
        """Mark assignment as completed"""
        async with self.db_pool.acquire() as connection:
            result = await connection.execute("""
                UPDATE track_assignments SET status = 'completed'
                WHERE id = $1
            """, assignment_id)

            return result == "UPDATE 1"

    async def exists_assignment(self, user_id: UUID, track_id: UUID, role_type: RoleType) -> bool:
        """Check if assignment exists"""
        async with self.db_pool.acquire() as connection:
            result = await connection.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM track_assignments
                    WHERE user_id = $1 AND track_id = $2 AND role_type = $3
                )
            """, user_id, track_id, role_type.value)

            return result

    async def get_project_assignments(self, project_id: UUID, role_type: Optional[RoleType] = None) -> List[TrackAssignment]:
        """Get all assignments for project tracks"""
        async with self.db_pool.acquire() as connection:
            if role_type:
                rows = await connection.fetch("""
                    SELECT ta.* FROM track_assignments ta
                    JOIN tracks t ON ta.track_id = t.id
                    WHERE t.project_id = $1 AND ta.role_type = $2 AND ta.status = 'active'
                    ORDER BY ta.assigned_at DESC
                """, project_id, role_type.value)
            else:
                rows = await connection.fetch("""
                    SELECT ta.* FROM track_assignments ta
                    JOIN tracks t ON ta.track_id = t.id
                    WHERE t.project_id = $1 AND ta.status = 'active'
                    ORDER BY ta.assigned_at DESC
                """, project_id)

            return [self._row_to_assignment(row) for row in rows]

    def _row_to_assignment(self, row) -> Optional[TrackAssignment]:
        """Convert database row to TrackAssignment entity"""
        if not row:
            return None

        return TrackAssignment(
            id=row['id'],
            user_id=row['user_id'],
            track_id=row['track_id'],
            role_type=RoleType(row['role_type']),
            assigned_by=row['assigned_by'],
            assigned_at=row['assigned_at'],
            status=row['status']
        )