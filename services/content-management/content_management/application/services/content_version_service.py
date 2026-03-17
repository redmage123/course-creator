"""
Content Versioning Application Service

WHAT: Application service for content version control operations
WHERE: Used by API endpoints and other services for versioning
WHY: Provides business logic for version management including
     diff generation, approval workflows, and merge operations

This service handles:
- Version lifecycle management
- Diff generation between versions
- Branch operations
- Approval workflows
- Lock management
- Merge operations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4

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
    ContentVersioningException,
    VersionNotFoundException,
    InvalidVersionTransitionException,
    ContentLockedException,
    MergeConflictException,
    BranchNotFoundException,
    InvalidApprovalException,
)
from data_access.content_version_dao import ContentVersionDAO


class ContentVersionService:
    """
    WHAT: Application service for content versioning
    WHERE: Used by API layer and other services
    WHY: Encapsulates version control business logic

    This service provides:
    - Version creation and management
    - Branch operations
    - Diff generation
    - Approval workflow management
    - Lock management
    - Merge operations
    """

    def __init__(self, dao: ContentVersionDAO):
        """
        WHAT: Initializes the service with DAO
        WHERE: Called during application startup
        WHY: Enables database operations

        Args:
            dao: ContentVersionDAO instance
        """
        self._dao = dao

    # =========================================================================
    # Version Operations
    # =========================================================================

    async def create_version(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        content_data: Dict[str, Any],
        created_by: UUID,
        title: str = "",
        description: str = "",
        organization_id: Optional[UUID] = None,
        branch_name: str = "main"
    ) -> ContentVersion:
        """
        WHAT: Creates a new version of content
        WHERE: Called when saving content changes
        WHY: Creates versioned snapshot of content

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            content_data: Content to version
            created_by: User creating version
            title: Version title
            description: Version description
            organization_id: Organization ID
            branch_name: Branch name

        Returns:
            Created ContentVersion
        """
        # Get next version number
        version_number = await self._dao.get_next_version_number(
            entity_type, entity_id, branch_name
        )

        # Get parent version if exists
        parent_version = await self._dao.get_latest_version(
            entity_type, entity_id, branch_name
        )

        # Get branch if not main
        branch = None
        if branch_name != "main":
            branch = await self._dao.get_branch_by_name(
                entity_type, entity_id, branch_name
            )

        # Create version
        version = ContentVersion(
            id=uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            version_number=version_number,
            content_data=content_data,
            title=title,
            description=description,
            created_by=created_by,
            organization_id=organization_id,
            parent_version_id=parent_version.id if parent_version else None,
            branch_id=branch.id if branch else None,
            branch_name=branch_name
        )

        # Update parent's is_latest flag
        if parent_version:
            parent_version.is_latest = False
            await self._dao.update_version(parent_version)

        return await self._dao.create_version(version)

    async def get_version(self, version_id: UUID) -> ContentVersion:
        """
        WHAT: Gets a version by ID
        WHERE: Called for version retrieval
        WHY: Provides access to specific versions

        Args:
            version_id: ID of version

        Returns:
            ContentVersion

        Raises:
            VersionNotFoundException: If version not found
        """
        version = await self._dao.get_version_by_id(version_id)
        if not version:
            raise VersionNotFoundException(
                f"Version {version_id} not found",
                {"version_id": str(version_id)}
            )
        return version

    async def get_current_version(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID
    ) -> Optional[ContentVersion]:
        """
        WHAT: Gets the current published version
        WHERE: Called when loading active content
        WHY: Returns version shown to users

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity

        Returns:
            Current ContentVersion or None
        """
        return await self._dao.get_current_version(entity_type, entity_id)

    async def get_latest_version(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        branch_name: str = "main"
    ) -> Optional[ContentVersion]:
        """
        WHAT: Gets the latest version in a branch
        WHERE: Called when starting edits
        WHY: Provides base for new versions

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            branch_name: Branch name

        Returns:
            Latest ContentVersion or None
        """
        return await self._dao.get_latest_version(entity_type, entity_id, branch_name)

    async def update_version_content(
        self,
        version_id: UUID,
        content_data: Dict[str, Any],
        user_id: UUID
    ) -> ContentVersion:
        """
        WHAT: Updates version content
        WHERE: Called during editing
        WHY: Updates draft version content

        Args:
            version_id: ID of version
            content_data: New content
            user_id: User making update

        Returns:
            Updated ContentVersion

        Raises:
            ContentLockedException: If locked by another user
        """
        version = await self.get_version(version_id)

        # Check lock
        lock = await self._dao.get_active_lock(
            version.entity_type,
            version.entity_id,
            user_id
        )
        if lock:
            raise ContentLockedException(
                "Content is locked by another user",
                {"locked_by": str(lock.locked_by)}
            )

        version.update_content(content_data)
        return await self._dao.update_version(version)

    async def get_version_history(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        branch_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ContentVersion]:
        """
        WHAT: Gets version history for entity
        WHERE: Called for history display
        WHY: Shows version timeline

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            branch_name: Optional branch filter
            limit: Maximum versions
            offset: Pagination offset

        Returns:
            List of ContentVersions
        """
        return await self._dao.get_version_history(
            entity_type, entity_id, branch_name, limit, offset
        )

    # =========================================================================
    # Workflow Operations
    # =========================================================================

    async def submit_for_review(
        self,
        version_id: UUID,
        changelog: str = ""
    ) -> ContentVersion:
        """
        WHAT: Submits version for review
        WHERE: Called when author completes editing
        WHY: Initiates review workflow

        Args:
            version_id: ID of version
            changelog: Description of changes

        Returns:
            Updated ContentVersion
        """
        version = await self.get_version(version_id)
        version.submit_for_review(changelog)
        return await self._dao.update_version(version)

    async def assign_reviewer(
        self,
        version_id: UUID,
        reviewer_id: UUID
    ) -> VersionApproval:
        """
        WHAT: Assigns a reviewer to version
        WHERE: Called by admin/lead
        WHY: Enables review workflow

        Args:
            version_id: ID of version
            reviewer_id: ID of reviewer

        Returns:
            Created VersionApproval
        """
        version = await self.get_version(version_id)

        if version.status != VersionStatus.PENDING_REVIEW:
            raise InvalidVersionTransitionException(
                "Version must be pending review to assign reviewer",
                {"current_status": version.status.value}
            )

        approval = VersionApproval(
            id=uuid4(),
            version_id=version_id,
            reviewer_id=reviewer_id
        )

        return await self._dao.create_approval(approval)

    async def start_review(
        self,
        version_id: UUID,
        reviewer_id: UUID
    ) -> ContentVersion:
        """
        WHAT: Marks version as being reviewed
        WHERE: Called when reviewer begins review
        WHY: Tracks review progress

        Args:
            version_id: ID of version
            reviewer_id: ID of reviewer

        Returns:
            Updated ContentVersion
        """
        version = await self.get_version(version_id)
        version.start_review(reviewer_id)
        return await self._dao.update_version(version)

    async def approve_version(
        self,
        version_id: UUID,
        reviewer_id: UUID,
        notes: str = ""
    ) -> Tuple[ContentVersion, VersionApproval]:
        """
        WHAT: Approves a version
        WHERE: Called by reviewer after successful review
        WHY: Advances version in workflow

        Args:
            version_id: ID of version
            reviewer_id: ID of reviewer
            notes: Approval notes

        Returns:
            Tuple of (ContentVersion, VersionApproval)
        """
        version = await self.get_version(version_id)
        version.approve(notes)

        # Update approval record
        approvals = await self._dao.get_approvals_for_version(version_id)
        reviewer_approval = None
        for approval in approvals:
            if approval.reviewer_id == reviewer_id:
                approval.approve(notes)
                reviewer_approval = await self._dao.update_approval(approval)
                break

        if not reviewer_approval:
            reviewer_approval = VersionApproval(
                id=uuid4(),
                version_id=version_id,
                reviewer_id=reviewer_id,
                status=ApprovalStatus.APPROVED,
                decision_notes=notes,
                decided_at=datetime.utcnow()
            )
            reviewer_approval = await self._dao.create_approval(reviewer_approval)

        updated_version = await self._dao.update_version(version)
        return updated_version, reviewer_approval

    async def reject_version(
        self,
        version_id: UUID,
        reviewer_id: UUID,
        notes: str
    ) -> Tuple[ContentVersion, VersionApproval]:
        """
        WHAT: Rejects a version
        WHERE: Called by reviewer when version fails review
        WHY: Returns version for revision

        Args:
            version_id: ID of version
            reviewer_id: ID of reviewer
            notes: Rejection reason

        Returns:
            Tuple of (ContentVersion, VersionApproval)
        """
        version = await self.get_version(version_id)
        version.reject(notes)

        # Update approval record
        approvals = await self._dao.get_approvals_for_version(version_id)
        reviewer_approval = None
        for approval in approvals:
            if approval.reviewer_id == reviewer_id:
                approval.reject(notes)
                reviewer_approval = await self._dao.update_approval(approval)
                break

        if not reviewer_approval:
            reviewer_approval = VersionApproval(
                id=uuid4(),
                version_id=version_id,
                reviewer_id=reviewer_id,
                status=ApprovalStatus.REJECTED,
                decision_notes=notes,
                decided_at=datetime.utcnow()
            )
            reviewer_approval = await self._dao.create_approval(reviewer_approval)

        updated_version = await self._dao.update_version(version)
        return updated_version, reviewer_approval

    async def request_changes(
        self,
        version_id: UUID,
        reviewer_id: UUID,
        changes: List[Dict[str, Any]],
        notes: str = ""
    ) -> VersionApproval:
        """
        WHAT: Requests changes before approval
        WHERE: Called when version needs modifications
        WHY: Provides actionable feedback

        Args:
            version_id: ID of version
            reviewer_id: ID of reviewer
            changes: List of requested changes
            notes: Additional notes

        Returns:
            Updated VersionApproval
        """
        # Update approval record
        approvals = await self._dao.get_approvals_for_version(version_id)
        for approval in approvals:
            if approval.reviewer_id == reviewer_id:
                approval.request_changes(changes, notes)
                return await self._dao.update_approval(approval)

        # Create new approval if not found
        approval = VersionApproval(
            id=uuid4(),
            version_id=version_id,
            reviewer_id=reviewer_id
        )
        approval.request_changes(changes, notes)
        return await self._dao.create_approval(approval)

    async def publish_version(self, version_id: UUID) -> ContentVersion:
        """
        WHAT: Publishes an approved version
        WHERE: Called when version goes live
        WHY: Makes version current and visible

        Args:
            version_id: ID of version

        Returns:
            Published ContentVersion
        """
        version = await self.get_version(version_id)
        version.publish()
        return await self._dao.update_version(version)

    async def rollback_to_version(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        target_version_id: UUID,
        user_id: UUID
    ) -> ContentVersion:
        """
        WHAT: Rolls back to a previous version
        WHERE: Called when reverting changes
        WHY: Restores content to earlier state

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            target_version_id: Version to restore
            user_id: User performing rollback

        Returns:
            New version based on target
        """
        target = await self.get_version(target_version_id)

        # Create new version with target's content
        return await self.create_version(
            entity_type=entity_type,
            entity_id=entity_id,
            content_data=target.content_data.copy(),
            created_by=user_id,
            title=f"Rollback to v{target.version_number}",
            description=f"Restored content from version {target.version_number}"
        )

    # =========================================================================
    # Branch Operations
    # =========================================================================

    async def create_branch(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        name: str,
        created_by: UUID,
        description: str = "",
        source_version_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None
    ) -> VersionBranch:
        """
        WHAT: Creates a new development branch
        WHERE: Called when starting parallel work
        WHY: Enables independent development

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            name: Branch name
            created_by: User creating branch
            description: Branch description
            source_version_id: Version to branch from
            organization_id: Organization ID

        Returns:
            Created VersionBranch
        """
        # Check if branch name exists
        existing = await self._dao.get_branch_by_name(entity_type, entity_id, name)
        if existing:
            raise ContentVersioningException(
                f"Branch '{name}' already exists",
                {"entity_id": str(entity_id), "branch_name": name}
            )

        # Get source version
        if source_version_id:
            source = await self.get_version(source_version_id)
        else:
            source = await self._dao.get_latest_version(entity_type, entity_id, "main")

        # Get main branch
        main_branch = await self._dao.get_branch_by_name(entity_type, entity_id, "main")

        branch = VersionBranch(
            id=uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            name=name,
            description=description,
            parent_branch_id=main_branch.id if main_branch else None,
            parent_branch_name="main",
            branched_from_version_id=source.id if source else None,
            created_by=created_by,
            organization_id=organization_id
        )

        return await self._dao.create_branch(branch)

    async def get_branch(self, branch_id: UUID) -> VersionBranch:
        """
        WHAT: Gets a branch by ID
        WHERE: Called for branch retrieval
        WHY: Provides branch access

        Args:
            branch_id: ID of branch

        Returns:
            VersionBranch

        Raises:
            BranchNotFoundException: If branch not found
        """
        branch = await self._dao.get_branch_by_id(branch_id)
        if not branch:
            raise BranchNotFoundException(
                f"Branch {branch_id} not found",
                {"branch_id": str(branch_id)}
            )
        return branch

    async def get_entity_branches(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        include_inactive: bool = False
    ) -> List[VersionBranch]:
        """
        WHAT: Gets all branches for an entity
        WHERE: Called for branch listing
        WHY: Shows available branches

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            include_inactive: Include closed branches

        Returns:
            List of VersionBranches
        """
        return await self._dao.get_entity_branches(
            entity_type, entity_id, include_inactive
        )

    async def close_branch(self, branch_id: UUID) -> VersionBranch:
        """
        WHAT: Closes a branch
        WHERE: Called when branch is no longer needed
        WHY: Marks branch as inactive

        Args:
            branch_id: ID of branch

        Returns:
            Closed VersionBranch
        """
        branch = await self.get_branch(branch_id)
        branch.close()
        return await self._dao.update_branch(branch)

    # =========================================================================
    # Diff Operations
    # =========================================================================

    async def generate_diff(
        self,
        source_version_id: UUID,
        target_version_id: UUID,
        user_id: UUID
    ) -> VersionDiff:
        """
        WHAT: Generates diff between two versions
        WHERE: Called for change comparison
        WHY: Shows what changed between versions

        Args:
            source_version_id: Base version ID
            target_version_id: Comparison version ID
            user_id: User requesting diff

        Returns:
            VersionDiff with changes
        """
        # Check for cached diff
        cached = await self._dao.get_diff(source_version_id, target_version_id)
        if cached:
            return cached

        # Get versions
        source = await self.get_version(source_version_id)
        target = await self.get_version(target_version_id)

        # Generate diff
        diff = VersionDiff(
            id=uuid4(),
            entity_type=source.entity_type,
            entity_id=source.entity_id,
            source_version_id=source_version_id,
            target_version_id=target_version_id,
            generated_by=user_id
        )

        # Compare content
        self._compare_dicts(
            source.content_data,
            target.content_data,
            diff,
            ""
        )

        # Cache and return
        return await self._dao.create_diff(diff)

    def _compare_dicts(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        diff: VersionDiff,
        path: str
    ) -> None:
        """
        WHAT: Recursively compares two dictionaries
        WHERE: Used in diff generation
        WHY: Identifies field-level changes

        Args:
            source: Source dictionary
            target: Target dictionary
            diff: VersionDiff to populate
            path: Current path in structure
        """
        all_keys = set(source.keys()) | set(target.keys())

        for key in all_keys:
            current_path = f"{path}.{key}" if path else key

            source_val = source.get(key)
            target_val = target.get(key)

            if key not in source:
                diff.add_change(current_path, ChangeType.CREATED, None, target_val)
            elif key not in target:
                diff.add_change(current_path, ChangeType.DELETED, source_val, None)
            elif source_val != target_val:
                if isinstance(source_val, dict) and isinstance(target_val, dict):
                    self._compare_dicts(source_val, target_val, diff, current_path)
                else:
                    diff.add_change(current_path, ChangeType.UPDATED, source_val, target_val)

    # =========================================================================
    # Lock Operations
    # =========================================================================

    async def acquire_lock(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        user_id: UUID,
        reason: str = "",
        duration_minutes: int = 30
    ) -> ContentLock:
        """
        WHAT: Acquires an editing lock
        WHERE: Called when starting to edit
        WHY: Prevents concurrent edit conflicts

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            user_id: User acquiring lock
            reason: Reason for lock
            duration_minutes: Lock duration

        Returns:
            Created ContentLock

        Raises:
            ContentLockedException: If already locked
        """
        # Get latest version
        latest = await self._dao.get_latest_version(entity_type, entity_id)
        if not latest:
            raise VersionNotFoundException(
                "No versions exist for this entity",
                {"entity_type": entity_type.value, "entity_id": str(entity_id)}
            )

        lock = ContentLock(
            id=uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            version_id=latest.id,
            locked_by=user_id,
            lock_reason=reason,
            expires_at=datetime.utcnow() + timedelta(minutes=duration_minutes)
        )

        return await self._dao.create_lock(lock)

    async def release_lock(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        user_id: UUID
    ) -> None:
        """
        WHAT: Releases an editing lock
        WHERE: Called when done editing
        WHY: Allows others to edit

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            user_id: User releasing lock
        """
        # Find the user's lock
        # Note: We need to get lock by entity and user
        lock = await self._dao.get_active_lock(entity_type, entity_id)
        if lock and lock.locked_by == user_id:
            await self._dao.release_lock(lock.id)

    async def refresh_lock(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        user_id: UUID
    ) -> Optional[ContentLock]:
        """
        WHAT: Refreshes lock heartbeat
        WHERE: Called periodically during editing
        WHY: Prevents lock expiration during active work

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            user_id: User refreshing lock

        Returns:
            Updated ContentLock or None
        """
        lock = await self._dao.get_active_lock(entity_type, entity_id)
        if lock and lock.locked_by == user_id:
            lock.refresh_heartbeat()
            return await self._dao.update_lock(lock)
        return None

    async def check_lock_status(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        WHAT: Checks lock status for entity
        WHERE: Called before editing
        WHY: Determines if editing is allowed

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity
            user_id: Current user

        Returns:
            Lock status information
        """
        lock = await self._dao.get_active_lock(entity_type, entity_id, user_id)

        if not lock:
            return {"locked": False, "can_edit": True}

        return {
            "locked": True,
            "locked_by": str(lock.locked_by),
            "locked_at": lock.acquired_at.isoformat(),
            "expires_at": lock.expires_at.isoformat() if lock.expires_at else None,
            "reason": lock.lock_reason,
            "can_edit": False
        }

    # =========================================================================
    # Merge Operations
    # =========================================================================

    async def merge_branches(
        self,
        source_branch_id: UUID,
        target_branch_id: UUID,
        user_id: UUID,
        strategy: MergeStrategy = MergeStrategy.AUTO
    ) -> VersionMerge:
        """
        WHAT: Merges one branch into another
        WHERE: Called when combining parallel work
        WHY: Integrates branch changes

        Args:
            source_branch_id: Branch to merge from
            target_branch_id: Branch to merge into
            user_id: User performing merge
            strategy: Merge strategy

        Returns:
            VersionMerge record

        Raises:
            MergeConflictException: If conflicts cannot be auto-resolved
        """
        source_branch = await self.get_branch(source_branch_id)
        target_branch = await self.get_branch(target_branch_id)

        # Get latest versions from each branch
        source_version = await self._dao.get_latest_version(
            source_branch.entity_type,
            source_branch.entity_id,
            source_branch.name
        )
        target_version = await self._dao.get_latest_version(
            target_branch.entity_type,
            target_branch.entity_id,
            target_branch.name
        )

        if not source_version or not target_version:
            raise VersionNotFoundException(
                "Source or target branch has no versions"
            )

        # Create merge record
        merge = VersionMerge(
            id=uuid4(),
            entity_type=source_branch.entity_type,
            entity_id=source_branch.entity_id,
            source_branch_id=source_branch_id,
            source_version_id=source_version.id,
            target_branch_id=target_branch_id,
            target_version_id=target_version.id,
            merge_strategy=strategy,
            merged_by=user_id
        )

        # Detect conflicts
        conflicts = self._detect_conflicts(
            source_version.content_data,
            target_version.content_data
        )

        if conflicts and strategy == MergeStrategy.MANUAL:
            # Record conflicts for manual resolution
            for conflict in conflicts:
                merge.add_conflict(
                    conflict["field"],
                    conflict["source_value"],
                    conflict["target_value"]
                )
            return await self._dao.create_merge(merge)

        # Auto-merge based on strategy
        if strategy == MergeStrategy.AUTO or not conflicts:
            merged_content = self._auto_merge(
                source_version.content_data,
                target_version.content_data,
                strategy
            )

            # Create merged version
            result_version = await self.create_version(
                entity_type=target_branch.entity_type,
                entity_id=target_branch.entity_id,
                content_data=merged_content,
                created_by=user_id,
                title=f"Merge from {source_branch.name}",
                description=f"Merged changes from branch '{source_branch.name}'",
                branch_name=target_branch.name
            )

            merge.complete(result_version.id)
            source_branch.mark_merged(target_branch_id, result_version.id)
            await self._dao.update_branch(source_branch)

        elif strategy == MergeStrategy.OURS:
            # Keep target's content
            merge.complete(target_version.id)
        elif strategy == MergeStrategy.THEIRS:
            # Take source's content
            result_version = await self.create_version(
                entity_type=target_branch.entity_type,
                entity_id=target_branch.entity_id,
                content_data=source_version.content_data.copy(),
                created_by=user_id,
                title=f"Merge from {source_branch.name}",
                description=f"Replaced with content from '{source_branch.name}'",
                branch_name=target_branch.name
            )
            merge.complete(result_version.id)

        return await self._dao.create_merge(merge)

    def _detect_conflicts(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        path: str = ""
    ) -> List[Dict[str, Any]]:
        """
        WHAT: Detects merge conflicts between versions
        WHERE: Used in merge operations
        WHY: Identifies fields that conflict

        Args:
            source: Source content
            target: Target content
            path: Current path

        Returns:
            List of conflicts
        """
        conflicts = []
        all_keys = set(source.keys()) | set(target.keys())

        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            source_val = source.get(key)
            target_val = target.get(key)

            if key in source and key in target:
                if source_val != target_val:
                    if isinstance(source_val, dict) and isinstance(target_val, dict):
                        conflicts.extend(
                            self._detect_conflicts(source_val, target_val, current_path)
                        )
                    else:
                        conflicts.append({
                            "field": current_path,
                            "source_value": source_val,
                            "target_value": target_val
                        })

        return conflicts

    def _auto_merge(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        strategy: MergeStrategy
    ) -> Dict[str, Any]:
        """
        WHAT: Automatically merges two content dicts
        WHERE: Used when no conflicts or auto strategy
        WHY: Combines changes from both versions

        Args:
            source: Source content
            target: Target content
            strategy: Merge strategy

        Returns:
            Merged content
        """
        result = target.copy()

        for key, value in source.items():
            if key not in target:
                # New in source, add it
                result[key] = value
            elif isinstance(value, dict) and isinstance(target.get(key), dict):
                # Recursively merge dicts
                result[key] = self._auto_merge(value, target[key], strategy)
            elif value != target.get(key):
                # Conflict - use strategy
                if strategy == MergeStrategy.THEIRS:
                    result[key] = value
                # OURS keeps target value (already in result)

        return result

    # =========================================================================
    # History & Analytics
    # =========================================================================

    async def get_version_history_summary(
        self,
        entity_type: ContentEntityType,
        entity_id: UUID
    ) -> VersionHistory:
        """
        WHAT: Gets version history summary
        WHERE: Called for history overview
        WHY: Provides aggregated statistics

        Args:
            entity_type: Type of content entity
            entity_id: ID of the entity

        Returns:
            VersionHistory with summary data
        """
        return await self._dao.get_version_history_summary(entity_type, entity_id)

    async def get_pending_reviews(
        self,
        entity_type: ContentEntityType,
        organization_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[ContentVersion]:
        """
        WHAT: Gets versions pending review
        WHERE: Called for review dashboard
        WHY: Shows items needing review

        Args:
            entity_type: Type of content entity
            organization_id: Optional org filter
            limit: Maximum versions

        Returns:
            List of pending ContentVersions
        """
        return await self._dao.get_versions_by_status(
            entity_type,
            VersionStatus.PENDING_REVIEW,
            organization_id,
            limit
        )

    async def get_reviewer_queue(
        self,
        reviewer_id: UUID,
        limit: int = 50
    ) -> List[VersionApproval]:
        """
        WHAT: Gets reviewer's pending approvals
        WHERE: Called for reviewer dashboard
        WHY: Shows assigned reviews

        Args:
            reviewer_id: ID of reviewer
            limit: Maximum approvals

        Returns:
            List of pending VersionApprovals
        """
        return await self._dao.get_pending_approvals_for_reviewer(reviewer_id, limit)
