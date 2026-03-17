"""
Content Versioning Data Access Object

WHAT: DAO for content version CRUD operations and queries
WHERE: Used by ContentVersionService to interact with the database
WHY: Encapsulates all database operations for version control,
     providing clean separation between business logic and persistence

This DAO handles:
- Version CRUD operations
- Branch management
- Diff generation and storage
- Approval workflow persistence
- Lock management
- Merge tracking
"""

import asyncpg
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
import json

from content_management.domain.entities.content_versioning import (
    ContentEntityType,
    VersionStatus,
    ChangeType,
    ApprovalStatus,
    MergeStrategy,
    ContentVersion,
    VersionDiff,
    VersionBranch,
    VersionApproval,
    ContentLock,
    VersionMerge,
    VersionHistory,
    VersionNotFoundException,
    ContentLockedException,
    BranchNotFoundException,
)


class ContentVersionDAO:
    """
    WHAT: Data Access Object for content versioning
    WHERE: Used by ContentVersionService for database operations
    WHY: Provides clean database abstraction for version control

    This class implements:
    - Async database operations with connection pooling
    - Transaction support for multi-step operations
    - Row-to-entity conversion helpers
    - Efficient queries with proper indexing
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        WHAT: Initializes the DAO with a connection pool
        WHERE: Called during service initialization
        WHY: Enables efficient connection reuse

        Args:
            pool: asyncpg connection pool
        """
        self._pool = pool

    # =========================================================================
    # ContentVersion Operations
    # =========================================================================

    async def create_version(self, version: ContentVersion) -> ContentVersion:
        """
        WHAT: Creates a new content version
        WHERE: Called when saving new version snapshots
        WHY: Persists version data with all metadata

        Args:
            version: ContentVersion to create

        Returns:
            Created ContentVersion with ID
        """
        query = """
            INSERT INTO content_versions (
                id, entity_type, entity_id, version_number,
                content_data, content_hash, title, description,
                changelog, tags, status, is_current, is_latest,
                created_by, organization_id, parent_version_id,
                branch_id, branch_name, content_size_bytes, word_count,
                reviewer_id, reviewed_at, review_notes,
                created_at, updated_at, published_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                $21, $22, $23, $24, $25, $26
            )
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                version.id,
                version.entity_type.value,
                version.entity_id,
                version.version_number,
                json.dumps(version.content_data),
                version.content_hash,
                version.title,
                version.description,
                version.changelog,
                version.tags,
                version.status.value,
                version.is_current,
                version.is_latest,
                version.created_by,
                version.organization_id,
                version.parent_version_id,
                version.branch_id,
                version.branch_name,
                version.content_size_bytes,
                version.word_count,
                version.reviewer_id,
                version.reviewed_at,
                version.review_notes,
                version.created_at,
                version.updated_at,
                version.published_at
            )
            return self._row_to_version(row)

    async def get_version_by_id(self, version_id: UUID) -> Optional[ContentVersion]:
        """
        WHAT: Retrieves a version by ID
        WHERE: Called for version lookups
        WHY: Provides direct access to specific versions

        Args:
            version_id: ID of version to retrieve

        Returns:
            ContentVersion or None if not found
        """
        query = "SELECT * FROM content_versions WHERE id = $1"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, version_id)
            return self._row_to_version(row) if row else None

    async def get_current_version(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID
    ) -> Optional[ContentVersion]:
        """
        WHAT: Gets the current published version for an entity
        WHERE: Called when loading active content
        WHY: Returns the version users see

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity

        Returns:
            Current published ContentVersion or None
        """
        query = """
            SELECT * FROM content_versions
            WHERE entity_type = $1
              AND entity_id = $2
              AND is_current = TRUE
              AND status = 'published'
            LIMIT 1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, entity_type.value, entity_id)
            return self._row_to_version(row) if row else None

    async def get_latest_version(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        branch_name: str = "main"
    ) -> Optional[ContentVersion]:
        """
        WHAT: Gets the latest version in a branch
        WHERE: Called when starting new edits
        WHY: Provides base for new version creation

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            branch_name: Branch to look in

        Returns:
            Latest ContentVersion in branch or None
        """
        query = """
            SELECT * FROM content_versions
            WHERE entity_type = $1
              AND entity_id = $2
              AND branch_name = $3
              AND is_latest = TRUE
            LIMIT 1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, entity_type.value, entity_id, branch_name)
            return self._row_to_version(row) if row else None

    async def update_version(self, version: ContentVersion) -> ContentVersion:
        """
        WHAT: Updates an existing version
        WHERE: Called when modifying version metadata or status
        WHY: Persists version changes

        Args:
            version: ContentVersion with updates

        Returns:
            Updated ContentVersion
        """
        query = """
            UPDATE content_versions SET
                content_data = $2,
                content_hash = $3,
                title = $4,
                description = $5,
                changelog = $6,
                tags = $7,
                status = $8,
                is_current = $9,
                is_latest = $10,
                reviewer_id = $11,
                reviewed_at = $12,
                review_notes = $13,
                updated_at = $14,
                published_at = $15,
                content_size_bytes = $16,
                word_count = $17
            WHERE id = $1
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                version.id,
                json.dumps(version.content_data),
                version.content_hash,
                version.title,
                version.description,
                version.changelog,
                version.tags,
                version.status.value,
                version.is_current,
                version.is_latest,
                version.reviewer_id,
                version.reviewed_at,
                version.review_notes,
                version.updated_at,
                version.published_at,
                version.content_size_bytes,
                version.word_count
            )
            return self._row_to_version(row)

    async def get_version_history(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        branch_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ContentVersion]:
        """
        WHAT: Gets version history for an entity
        WHERE: Called for version timeline display
        WHY: Provides chronological version list

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            branch_name: Optional branch filter
            limit: Maximum versions to return
            offset: Pagination offset

        Returns:
            List of ContentVersions in reverse chronological order
        """
        if branch_name:
            query = """
                SELECT * FROM content_versions
                WHERE entity_type = $1
                  AND entity_id = $2
                  AND branch_name = $3
                ORDER BY version_number DESC
                LIMIT $4 OFFSET $5
            """
            params = [entity_type.value, entity_id, branch_name, limit, offset]
        else:
            query = """
                SELECT * FROM content_versions
                WHERE entity_type = $1
                  AND entity_id = $2
                ORDER BY version_number DESC
                LIMIT $3 OFFSET $4
            """
            params = [entity_type.value, entity_id, limit, offset]

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_version(row) for row in rows]

    async def get_versions_by_status(
        self,
        entity_type: ContentEntityType,
        status: VersionStatus,
        organization_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[ContentVersion]:
        """
        WHAT: Gets versions by status
        WHERE: Called for workflow dashboards
        WHY: Enables filtering by review state

        Args:
            entity_type: Type of content entity
            status: Status to filter by
            organization_id: Optional org filter
            limit: Maximum versions to return

        Returns:
            List of ContentVersions with specified status
        """
        if organization_id:
            query = """
                SELECT * FROM content_versions
                WHERE entity_type = $1
                  AND status = $2
                  AND organization_id = $3
                ORDER BY created_at DESC
                LIMIT $4
            """
            params = [entity_type.value, status.value, organization_id, limit]
        else:
            query = """
                SELECT * FROM content_versions
                WHERE entity_type = $1
                  AND status = $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            params = [entity_type.value, status.value, limit]

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_version(row) for row in rows]

    async def get_next_version_number(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        branch_name: str = "main"
    ) -> int:
        """
        WHAT: Gets the next version number for a branch
        WHERE: Called when creating new versions
        WHY: Ensures sequential version numbering

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            branch_name: Branch name

        Returns:
            Next version number
        """
        query = """
            SELECT COALESCE(MAX(version_number), 0) + 1 as next_version
            FROM content_versions
            WHERE entity_type = $1
              AND entity_id = $2
              AND branch_name = $3
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, entity_type.value, entity_id, branch_name)
            return row["next_version"]

    # =========================================================================
    # VersionBranch Operations
    # =========================================================================

    async def create_branch(self, branch: VersionBranch) -> VersionBranch:
        """
        WHAT: Creates a new version branch
        WHERE: Called when branching for parallel development
        WHY: Enables independent version tracks

        Args:
            branch: VersionBranch to create

        Returns:
            Created VersionBranch
        """
        query = """
            INSERT INTO version_branches (
                id, entity_type, entity_id, name, description,
                parent_branch_id, parent_branch_name, branched_from_version_id,
                is_active, is_default, is_protected,
                created_by, organization_id, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
            )
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                branch.id,
                branch.entity_type.value,
                branch.entity_id,
                branch.name,
                branch.description,
                branch.parent_branch_id,
                branch.parent_branch_name,
                branch.branched_from_version_id,
                branch.is_active,
                branch.is_default,
                branch.is_protected,
                branch.created_by,
                branch.organization_id,
                branch.created_at,
                branch.updated_at
            )
            return self._row_to_branch(row)

    async def get_branch_by_id(self, branch_id: UUID) -> Optional[VersionBranch]:
        """
        WHAT: Gets a branch by ID
        WHERE: Called for branch lookups
        WHY: Provides direct branch access

        Args:
            branch_id: ID of branch

        Returns:
            VersionBranch or None
        """
        query = "SELECT * FROM version_branches WHERE id = $1"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, branch_id)
            return self._row_to_branch(row) if row else None

    async def get_branch_by_name(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        branch_name: str
    ) -> Optional[VersionBranch]:
        """
        WHAT: Gets a branch by name
        WHERE: Called for named branch lookups
        WHY: Enables branch access by name

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            branch_name: Name of the branch

        Returns:
            VersionBranch or None
        """
        query = """
            SELECT * FROM version_branches
            WHERE entity_type = $1
              AND entity_id = $2
              AND name = $3
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, entity_type.value, entity_id, branch_name)
            return self._row_to_branch(row) if row else None

    async def get_entity_branches(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        include_inactive: bool = False
    ) -> List[VersionBranch]:
        """
        WHAT: Gets all branches for an entity
        WHERE: Called for branch listing
        WHY: Shows available development tracks

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            include_inactive: Whether to include closed branches

        Returns:
            List of VersionBranches
        """
        if include_inactive:
            query = """
                SELECT * FROM version_branches
                WHERE entity_type = $1 AND entity_id = $2
                ORDER BY is_default DESC, created_at DESC
            """
            params = [entity_type.value, entity_id]
        else:
            query = """
                SELECT * FROM version_branches
                WHERE entity_type = $1 AND entity_id = $2 AND is_active = TRUE
                ORDER BY is_default DESC, created_at DESC
            """
            params = [entity_type.value, entity_id]

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_branch(row) for row in rows]

    async def update_branch(self, branch: VersionBranch) -> VersionBranch:
        """
        WHAT: Updates a branch
        WHERE: Called when modifying branch state
        WHY: Persists branch changes

        Args:
            branch: VersionBranch with updates

        Returns:
            Updated VersionBranch
        """
        query = """
            UPDATE version_branches SET
                description = $2,
                is_active = $3,
                is_protected = $4,
                merged_to_branch_id = $5,
                merged_at = $6,
                merge_commit_version_id = $7,
                updated_at = $8
            WHERE id = $1
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                branch.id,
                branch.description,
                branch.is_active,
                branch.is_protected,
                branch.merged_to_branch_id,
                branch.merged_at,
                branch.merge_commit_version_id,
                branch.updated_at
            )
            return self._row_to_branch(row)

    # =========================================================================
    # VersionDiff Operations
    # =========================================================================

    async def create_diff(self, diff: VersionDiff) -> VersionDiff:
        """
        WHAT: Stores a version diff
        WHERE: Called after generating diff
        WHY: Enables diff caching and retrieval

        Args:
            diff: VersionDiff to store

        Returns:
            Created VersionDiff
        """
        query = """
            INSERT INTO version_diffs (
                id, entity_type, entity_id, source_version_id, target_version_id,
                changes, fields_added, fields_modified, fields_deleted, total_changes,
                words_added, words_deleted, net_word_change,
                generated_by, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
            )
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                diff.id,
                diff.entity_type.value,
                diff.entity_id,
                diff.source_version_id,
                diff.target_version_id,
                json.dumps(diff.changes),
                diff.fields_added,
                diff.fields_modified,
                diff.fields_deleted,
                diff.total_changes,
                diff.words_added,
                diff.words_deleted,
                diff.net_word_change,
                diff.generated_by,
                diff.created_at
            )
            return self._row_to_diff(row)

    async def get_diff(
        self,
        source_version_id: UUID,
        target_version_id: UUID
    ) -> Optional[VersionDiff]:
        """
        WHAT: Gets a diff between two versions
        WHERE: Called for change comparison
        WHY: Returns cached diff if available

        Args:
            source_version_id: Base version ID
            target_version_id: Comparison version ID

        Returns:
            VersionDiff or None if not cached
        """
        query = """
            SELECT * FROM version_diffs
            WHERE source_version_id = $1 AND target_version_id = $2
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, source_version_id, target_version_id)
            return self._row_to_diff(row) if row else None

    # =========================================================================
    # VersionApproval Operations
    # =========================================================================

    async def create_approval(self, approval: VersionApproval) -> VersionApproval:
        """
        WHAT: Creates an approval record
        WHERE: Called when assigning reviewer
        WHY: Tracks approval workflow

        Args:
            approval: VersionApproval to create

        Returns:
            Created VersionApproval
        """
        query = """
            INSERT INTO version_approvals (
                id, version_id, reviewer_id, status, decision_notes,
                requested_changes, assigned_at, decided_at,
                changes_addressed, follow_up_version_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
            )
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                approval.id,
                approval.version_id,
                approval.reviewer_id,
                approval.status.value,
                approval.decision_notes,
                json.dumps(approval.requested_changes),
                approval.assigned_at,
                approval.decided_at,
                approval.changes_addressed,
                approval.follow_up_version_id
            )
            return self._row_to_approval(row)

    async def get_approval_by_id(self, approval_id: UUID) -> Optional[VersionApproval]:
        """
        WHAT: Gets an approval by ID
        WHERE: Called for approval lookups
        WHY: Provides direct approval access

        Args:
            approval_id: ID of approval

        Returns:
            VersionApproval or None
        """
        query = "SELECT * FROM version_approvals WHERE id = $1"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, approval_id)
            return self._row_to_approval(row) if row else None

    async def get_approvals_for_version(self, version_id: UUID) -> List[VersionApproval]:
        """
        WHAT: Gets all approvals for a version
        WHERE: Called for review status display
        WHY: Shows all reviewer decisions

        Args:
            version_id: ID of version

        Returns:
            List of VersionApprovals
        """
        query = """
            SELECT * FROM version_approvals
            WHERE version_id = $1
            ORDER BY assigned_at DESC
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, version_id)
            return [self._row_to_approval(row) for row in rows]

    async def get_pending_approvals_for_reviewer(
        self,
        reviewer_id: UUID,
        limit: int = 50
    ) -> List[VersionApproval]:
        """
        WHAT: Gets pending approvals for a reviewer
        WHERE: Called for reviewer dashboard
        WHY: Shows assigned reviews

        Args:
            reviewer_id: ID of reviewer
            limit: Maximum approvals to return

        Returns:
            List of pending VersionApprovals
        """
        query = """
            SELECT * FROM version_approvals
            WHERE reviewer_id = $1 AND status = 'pending'
            ORDER BY assigned_at ASC
            LIMIT $2
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, reviewer_id, limit)
            return [self._row_to_approval(row) for row in rows]

    async def update_approval(self, approval: VersionApproval) -> VersionApproval:
        """
        WHAT: Updates an approval record
        WHERE: Called when reviewer makes decision
        WHY: Records approval decisions

        Args:
            approval: VersionApproval with updates

        Returns:
            Updated VersionApproval
        """
        query = """
            UPDATE version_approvals SET
                status = $2,
                decision_notes = $3,
                requested_changes = $4,
                decided_at = $5,
                changes_addressed = $6,
                follow_up_version_id = $7
            WHERE id = $1
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                approval.id,
                approval.status.value,
                approval.decision_notes,
                json.dumps(approval.requested_changes),
                approval.decided_at,
                approval.changes_addressed,
                approval.follow_up_version_id
            )
            return self._row_to_approval(row)

    # =========================================================================
    # ContentLock Operations
    # =========================================================================

    async def create_lock(self, lock: ContentLock) -> ContentLock:
        """
        WHAT: Creates an editing lock
        WHERE: Called when user begins editing
        WHY: Prevents concurrent edit conflicts

        Args:
            lock: ContentLock to create

        Returns:
            Created ContentLock

        Raises:
            ContentLockedException: If already locked by another user
        """
        # Check for existing lock
        existing = await self.get_active_lock(
            lock.entity_type,
            lock.entity_id,
            lock.locked_by
        )
        if existing:
            raise ContentLockedException(
                f"Content is locked by another user",
                {"locked_by": str(existing.locked_by), "locked_at": str(existing.acquired_at)}
            )

        query = """
            INSERT INTO content_locks (
                id, entity_type, entity_id, version_id, locked_by,
                lock_reason, is_active, lock_level, inherited_from_parent,
                acquired_at, expires_at, last_heartbeat, user_agent, ip_address
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
            )
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                lock.id,
                lock.entity_type.value,
                lock.entity_id,
                lock.version_id,
                lock.locked_by,
                lock.lock_reason,
                lock.is_active,
                lock.lock_level,
                lock.inherited_from_parent,
                lock.acquired_at,
                lock.expires_at,
                lock.last_heartbeat,
                lock.user_agent,
                lock.ip_address
            )
            return self._row_to_lock(row)

    async def get_active_lock(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        exclude_user: Optional[UUID] = None
    ) -> Optional[ContentLock]:
        """
        WHAT: Gets active lock for entity
        WHERE: Called to check lock status
        WHY: Determines if editing is blocked

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            exclude_user: User to exclude (their own lock)

        Returns:
            Active ContentLock or None
        """
        if exclude_user:
            query = """
                SELECT * FROM content_locks
                WHERE entity_type = $1
                  AND entity_id = $2
                  AND is_active = TRUE
                  AND (expires_at IS NULL OR expires_at > NOW())
                  AND locked_by != $3
                LIMIT 1
            """
            params = [entity_type.value, entity_id, exclude_user]
        else:
            query = """
                SELECT * FROM content_locks
                WHERE entity_type = $1
                  AND entity_id = $2
                  AND is_active = TRUE
                  AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1
            """
            params = [entity_type.value, entity_id]

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            return self._row_to_lock(row) if row else None

    async def update_lock(self, lock: ContentLock) -> ContentLock:
        """
        WHAT: Updates a lock
        WHERE: Called for heartbeat, extend, release
        WHY: Maintains lock state

        Args:
            lock: ContentLock with updates

        Returns:
            Updated ContentLock
        """
        query = """
            UPDATE content_locks SET
                is_active = $2,
                expires_at = $3,
                last_heartbeat = $4
            WHERE id = $1
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                lock.id,
                lock.is_active,
                lock.expires_at,
                lock.last_heartbeat
            )
            return self._row_to_lock(row)

    async def release_lock(self, lock_id: UUID) -> None:
        """
        WHAT: Releases a lock by ID
        WHERE: Called when editing completes
        WHY: Allows others to edit

        Args:
            lock_id: ID of lock to release
        """
        query = "UPDATE content_locks SET is_active = FALSE WHERE id = $1"
        async with self._pool.acquire() as conn:
            await conn.execute(query, lock_id)

    async def cleanup_expired_locks(self) -> int:
        """
        WHAT: Cleans up expired locks
        WHERE: Called periodically by scheduler
        WHY: Prevents stale locks from blocking

        Returns:
            Number of locks cleaned up
        """
        query = """
            UPDATE content_locks
            SET is_active = FALSE
            WHERE is_active = TRUE
              AND expires_at IS NOT NULL
              AND expires_at < NOW()
        """
        async with self._pool.acquire() as conn:
            result = await conn.execute(query)
            return int(result.split()[-1])

    # =========================================================================
    # VersionMerge Operations
    # =========================================================================

    async def create_merge(self, merge: VersionMerge) -> VersionMerge:
        """
        WHAT: Creates a merge record
        WHERE: Called when starting branch merge
        WHY: Tracks merge operations

        Args:
            merge: VersionMerge to create

        Returns:
            Created VersionMerge
        """
        query = """
            INSERT INTO version_merges (
                id, entity_type, entity_id,
                source_branch_id, source_version_id,
                target_branch_id, target_version_id,
                result_version_id, merge_strategy,
                is_complete, had_conflicts, conflicts_resolved,
                conflict_details, merged_by, started_at, completed_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
            )
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                merge.id,
                merge.entity_type.value,
                merge.entity_id,
                merge.source_branch_id,
                merge.source_version_id,
                merge.target_branch_id,
                merge.target_version_id,
                merge.result_version_id,
                merge.merge_strategy.value,
                merge.is_complete,
                merge.had_conflicts,
                merge.conflicts_resolved,
                json.dumps(merge.conflict_details),
                merge.merged_by,
                merge.started_at,
                merge.completed_at
            )
            return self._row_to_merge(row)

    async def get_merge_by_id(self, merge_id: UUID) -> Optional[VersionMerge]:
        """
        WHAT: Gets a merge by ID
        WHERE: Called for merge lookups
        WHY: Provides direct merge access

        Args:
            merge_id: ID of merge

        Returns:
            VersionMerge or None
        """
        query = "SELECT * FROM version_merges WHERE id = $1"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, merge_id)
            return self._row_to_merge(row) if row else None

    async def update_merge(self, merge: VersionMerge) -> VersionMerge:
        """
        WHAT: Updates a merge record
        WHERE: Called during merge progress
        WHY: Tracks merge state

        Args:
            merge: VersionMerge with updates

        Returns:
            Updated VersionMerge
        """
        query = """
            UPDATE version_merges SET
                result_version_id = $2,
                is_complete = $3,
                had_conflicts = $4,
                conflicts_resolved = $5,
                conflict_details = $6,
                completed_at = $7
            WHERE id = $1
            RETURNING *
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                merge.id,
                merge.result_version_id,
                merge.is_complete,
                merge.had_conflicts,
                merge.conflicts_resolved,
                json.dumps(merge.conflict_details),
                merge.completed_at
            )
            return self._row_to_merge(row)

    # =========================================================================
    # Aggregate Operations
    # =========================================================================

    async def get_version_history_summary(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID
    ) -> VersionHistory:
        """
        WHAT: Gets aggregated version history
        WHERE: Called for history overview
        WHY: Provides summary statistics

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity

        Returns:
            VersionHistory with aggregated data
        """
        # Get basic counts
        count_query = """
            SELECT
                COUNT(*) as total_versions,
                COUNT(DISTINCT branch_name) as branch_count,
                COUNT(DISTINCT created_by) as author_count,
                MIN(created_at) as first_created,
                MAX(updated_at) as last_updated,
                MAX(published_at) as last_published
            FROM content_versions
            WHERE entity_type = $1 AND entity_id = $2
        """

        # Get current version
        current_query = """
            SELECT id FROM content_versions
            WHERE entity_type = $1 AND entity_id = $2 AND is_current = TRUE
            LIMIT 1
        """

        # Get recent versions
        recent_query = """
            SELECT id, version_number, status, created_at, created_by, branch_name
            FROM content_versions
            WHERE entity_type = $1 AND entity_id = $2
            ORDER BY created_at DESC
            LIMIT 10
        """

        # Get branches
        branches_query = """
            SELECT DISTINCT branch_name FROM content_versions
            WHERE entity_type = $1 AND entity_id = $2
        """

        async with self._pool.acquire() as conn:
            stats = await conn.fetchrow(count_query, entity_type.value, entity_id)
            current = await conn.fetchrow(current_query, entity_type.value, entity_id)
            recent = await conn.fetch(recent_query, entity_type.value, entity_id)
            branches = await conn.fetch(branches_query, entity_type.value, entity_id)

        return VersionHistory(
            entity_type=entity_type,
            entity_id=entity_id,
            current_version_id=current["id"] if current else None,
            total_versions=stats["total_versions"],
            branches=[b["branch_name"] for b in branches],
            total_authors=stats["author_count"],
            first_created_at=stats["first_created"],
            last_updated_at=stats["last_updated"],
            last_published_at=stats["last_published"],
            recent_versions=[
                {
                    "version_id": str(r["id"]),
                    "version_number": r["version_number"],
                    "status": r["status"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "branch_name": r["branch_name"]
                }
                for r in recent
            ]
        )

    # =========================================================================
    # Row Conversion Helpers
    # =========================================================================

    def _row_to_version(self, row: asyncpg.Record) -> ContentVersion:
        """Converts database row to ContentVersion entity."""
        return ContentVersion(
            id=row["id"],
            entity_type=ContentEntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            version_number=row["version_number"],
            content_data=json.loads(row["content_data"]) if row["content_data"] else {},
            content_hash=row["content_hash"],
            title=row["title"] or "",
            description=row["description"] or "",
            changelog=row["changelog"] or "",
            tags=row["tags"] or [],
            status=VersionStatus(row["status"]),
            is_current=row["is_current"],
            is_latest=row["is_latest"],
            created_by=row["created_by"],
            organization_id=row["organization_id"],
            parent_version_id=row["parent_version_id"],
            branch_id=row["branch_id"],
            branch_name=row["branch_name"],
            content_size_bytes=row["content_size_bytes"] or 0,
            word_count=row["word_count"] or 0,
            reviewer_id=row["reviewer_id"],
            reviewed_at=row["reviewed_at"],
            review_notes=row["review_notes"] or "",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            published_at=row["published_at"]
        )

    def _row_to_branch(self, row: asyncpg.Record) -> VersionBranch:
        """Converts database row to VersionBranch entity."""
        return VersionBranch(
            id=row["id"],
            entity_type=ContentEntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            name=row["name"],
            description=row["description"] or "",
            parent_branch_id=row["parent_branch_id"],
            parent_branch_name=row["parent_branch_name"] or "main",
            branched_from_version_id=row["branched_from_version_id"],
            is_active=row["is_active"],
            is_default=row["is_default"],
            is_protected=row["is_protected"],
            merged_to_branch_id=row["merged_to_branch_id"],
            merged_at=row["merged_at"],
            merge_commit_version_id=row["merge_commit_version_id"],
            created_by=row["created_by"],
            organization_id=row["organization_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _row_to_diff(self, row: asyncpg.Record) -> VersionDiff:
        """Converts database row to VersionDiff entity."""
        return VersionDiff(
            id=row["id"],
            entity_type=ContentEntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            source_version_id=row["source_version_id"],
            target_version_id=row["target_version_id"],
            changes=json.loads(row["changes"]) if row["changes"] else [],
            fields_added=row["fields_added"] or 0,
            fields_modified=row["fields_modified"] or 0,
            fields_deleted=row["fields_deleted"] or 0,
            total_changes=row["total_changes"] or 0,
            words_added=row["words_added"] or 0,
            words_deleted=row["words_deleted"] or 0,
            net_word_change=row["net_word_change"] or 0,
            generated_by=row["generated_by"],
            created_at=row["created_at"]
        )

    def _row_to_approval(self, row: asyncpg.Record) -> VersionApproval:
        """Converts database row to VersionApproval entity."""
        return VersionApproval(
            id=row["id"],
            version_id=row["version_id"],
            reviewer_id=row["reviewer_id"],
            status=ApprovalStatus(row["status"]),
            decision_notes=row["decision_notes"] or "",
            requested_changes=json.loads(row["requested_changes"]) if row["requested_changes"] else [],
            assigned_at=row["assigned_at"],
            decided_at=row["decided_at"],
            changes_addressed=row["changes_addressed"],
            follow_up_version_id=row["follow_up_version_id"]
        )

    def _row_to_lock(self, row: asyncpg.Record) -> ContentLock:
        """Converts database row to ContentLock entity."""
        return ContentLock(
            id=row["id"],
            entity_type=ContentEntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            version_id=row["version_id"],
            locked_by=row["locked_by"],
            lock_reason=row["lock_reason"] or "",
            is_active=row["is_active"],
            lock_level=row["lock_level"],
            inherited_from_parent=row["inherited_from_parent"],
            acquired_at=row["acquired_at"],
            expires_at=row["expires_at"],
            last_heartbeat=row["last_heartbeat"],
            user_agent=row["user_agent"] or "",
            ip_address=row["ip_address"] or ""
        )

    def _row_to_merge(self, row: asyncpg.Record) -> VersionMerge:
        """Converts database row to VersionMerge entity."""
        return VersionMerge(
            id=row["id"],
            entity_type=ContentEntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            source_branch_id=row["source_branch_id"],
            source_version_id=row["source_version_id"],
            target_branch_id=row["target_branch_id"],
            target_version_id=row["target_version_id"],
            result_version_id=row["result_version_id"],
            merge_strategy=MergeStrategy(row["merge_strategy"]),
            is_complete=row["is_complete"],
            had_conflicts=row["had_conflicts"],
            conflicts_resolved=row["conflicts_resolved"],
            conflict_details=json.loads(row["conflict_details"]) if row["conflict_details"] else [],
            merged_by=row["merged_by"],
            started_at=row["started_at"],
            completed_at=row["completed_at"]
        )
