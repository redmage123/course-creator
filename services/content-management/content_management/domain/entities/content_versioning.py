"""
Content Versioning Domain Entities

WHAT: Domain entities for managing content versions and change tracking
WHERE: Used throughout the content-management service for version control
WHY: Enables non-destructive editing, audit trails, rollback capabilities,
     and collaborative content development with approval workflows

This module defines entities for:
- ContentVersion: Individual version snapshots of content
- VersionDiff: Changes between two versions
- VersionBranch: Parallel development branches
- VersionApproval: Approval workflow for version promotion
- ContentLock: Editing locks to prevent conflicts
- VersionMerge: Record of branch merges
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from uuid import UUID, uuid4
import hashlib
import json


class ContentEntityType(Enum):
    """
    WHAT: Types of content entities that can be versioned
    WHERE: Used to identify the type of content being versioned
    WHY: Enables generic versioning across different content types
    """
    COURSE = "course"
    MODULE = "module"
    LESSON = "lesson"
    QUIZ = "quiz"
    QUESTION = "question"
    ASSIGNMENT = "assignment"
    RESOURCE = "resource"
    SYLLABUS = "syllabus"
    INTERACTIVE_ELEMENT = "interactive_element"
    SLIDE = "slide"
    VIDEO = "video"
    DOCUMENT = "document"


class VersionStatus(Enum):
    """
    WHAT: Status states for content versions
    WHERE: Used to track version lifecycle
    WHY: Enables workflow management for version review and publishing
    """
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ChangeType(Enum):
    """
    WHAT: Types of changes in a version diff
    WHERE: Used to categorize modifications
    WHY: Enables understanding of what changed between versions
    """
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RENAMED = "renamed"
    MOVED = "moved"
    RESTRUCTURED = "restructured"


class ApprovalStatus(Enum):
    """
    WHAT: Status of version approval
    WHERE: Used in approval workflow
    WHY: Tracks review decisions for version promotion
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    WITHDRAWN = "withdrawn"


class MergeStrategy(Enum):
    """
    WHAT: Strategies for merging version branches
    WHERE: Used when combining parallel versions
    WHY: Defines how conflicts are resolved during merge
    """
    OURS = "ours"  # Keep current branch's changes
    THEIRS = "theirs"  # Take incoming branch's changes
    MANUAL = "manual"  # Require manual resolution
    AUTO = "auto"  # Attempt automatic merge


# =============================================================================
# Custom Exceptions
# =============================================================================

class ContentVersioningException(Exception):
    """
    WHAT: Base exception for content versioning operations
    WHERE: Used throughout version control handling
    WHY: Provides consistent error handling with context
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class VersionNotFoundException(ContentVersioningException):
    """
    WHAT: Exception when a version is not found
    WHERE: Raised when looking up non-existent versions
    WHY: Provides clear feedback for missing version lookups
    """
    pass


class InvalidVersionTransitionException(ContentVersioningException):
    """
    WHAT: Exception for invalid version status transitions
    WHERE: Raised when attempting invalid workflow transitions
    WHY: Enforces valid version lifecycle state machine
    """
    pass


class ContentLockedException(ContentVersioningException):
    """
    WHAT: Exception when content is locked by another user
    WHERE: Raised when attempting to edit locked content
    WHY: Prevents concurrent editing conflicts
    """
    pass


class MergeConflictException(ContentVersioningException):
    """
    WHAT: Exception when merge conflicts cannot be auto-resolved
    WHERE: Raised during branch merge operations
    WHY: Signals need for manual conflict resolution
    """
    pass


class BranchNotFoundException(ContentVersioningException):
    """
    WHAT: Exception when a branch is not found
    WHERE: Raised when looking up non-existent branches
    WHY: Provides clear feedback for missing branch lookups
    """
    pass


class InvalidApprovalException(ContentVersioningException):
    """
    WHAT: Exception for invalid approval operations
    WHERE: Raised when approval workflow is violated
    WHY: Enforces proper approval workflow
    """
    pass


# =============================================================================
# Domain Entities
# =============================================================================

@dataclass
class ContentVersion:
    """
    WHAT: Snapshot of content at a specific point in time
    WHERE: Used to track all versions of any content entity
    WHY: Enables full history, rollback, and audit capabilities

    This entity tracks:
    - Complete content snapshot with hash for integrity
    - Version metadata and changelog
    - Status and workflow state
    - Lineage (parent version, branch)
    """
    id: UUID
    entity_type: ContentEntityType
    entity_id: UUID
    version_number: int

    # Content snapshot
    content_data: Dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""

    # Metadata
    title: str = ""
    description: str = ""
    changelog: str = ""
    tags: List[str] = field(default_factory=list)

    # Status
    status: VersionStatus = VersionStatus.DRAFT
    is_current: bool = False  # Is this the current published version?
    is_latest: bool = True  # Is this the latest version in branch?

    # Authorship
    created_by: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Lineage
    parent_version_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    branch_name: str = "main"

    # Size and metrics
    content_size_bytes: int = 0
    word_count: int = 0

    # Review
    reviewer_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: str = ""

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    def __post_init__(self):
        """Calculate content hash and metrics if not set."""
        if not self.content_hash and self.content_data:
            self._calculate_hash()
        if self.content_data and not self.content_size_bytes:
            self._calculate_metrics()

    def _calculate_hash(self) -> None:
        """
        WHAT: Calculates SHA-256 hash of content
        WHERE: Called when content is set
        WHY: Enables integrity verification and change detection
        """
        content_str = json.dumps(self.content_data, sort_keys=True)
        self.content_hash = hashlib.sha256(content_str.encode()).hexdigest()

    def _calculate_metrics(self) -> None:
        """
        WHAT: Calculates content size and word count
        WHERE: Called when content is set
        WHY: Provides content metrics for analytics
        """
        content_str = json.dumps(self.content_data)
        self.content_size_bytes = len(content_str.encode('utf-8'))

        # Simple word count from text fields
        text_content = self._extract_text_content()
        self.word_count = len(text_content.split()) if text_content else 0

    def _extract_text_content(self) -> str:
        """
        WHAT: Extracts text content from nested structure
        WHERE: Used for word count calculation
        WHY: Handles various content structures
        """
        text_parts = []

        def extract_text(obj: Any) -> None:
            if isinstance(obj, str):
                text_parts.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_text(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text(item)

        extract_text(self.content_data)
        return " ".join(text_parts)

    def submit_for_review(self, changelog: str = "") -> None:
        """
        WHAT: Submits version for review
        WHERE: Called when author completes editing
        WHY: Initiates review workflow

        Args:
            changelog: Description of changes

        Raises:
            InvalidVersionTransitionException: If not in draft status
        """
        if self.status != VersionStatus.DRAFT:
            raise InvalidVersionTransitionException(
                f"Cannot submit for review from {self.status.value} status",
                {"current_status": self.status.value, "required_status": "draft"}
            )
        self.changelog = changelog or self.changelog
        self.status = VersionStatus.PENDING_REVIEW
        self.updated_at = datetime.utcnow()

    def start_review(self, reviewer_id: UUID) -> None:
        """
        WHAT: Marks version as being actively reviewed
        WHERE: Called when reviewer begins review
        WHY: Tracks review assignment and progress

        Args:
            reviewer_id: ID of the reviewer

        Raises:
            InvalidVersionTransitionException: If not pending review
        """
        if self.status != VersionStatus.PENDING_REVIEW:
            raise InvalidVersionTransitionException(
                f"Cannot start review from {self.status.value} status",
                {"current_status": self.status.value, "required_status": "pending_review"}
            )
        self.reviewer_id = reviewer_id
        self.status = VersionStatus.IN_REVIEW
        self.updated_at = datetime.utcnow()

    def approve(self, notes: str = "") -> None:
        """
        WHAT: Approves the version after review
        WHERE: Called by reviewer after successful review
        WHY: Marks version ready for publishing

        Args:
            notes: Review notes

        Raises:
            InvalidVersionTransitionException: If not in review
        """
        if self.status != VersionStatus.IN_REVIEW:
            raise InvalidVersionTransitionException(
                f"Cannot approve from {self.status.value} status",
                {"current_status": self.status.value, "required_status": "in_review"}
            )
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
        self.status = VersionStatus.APPROVED
        self.updated_at = datetime.utcnow()

    def reject(self, notes: str) -> None:
        """
        WHAT: Rejects the version
        WHERE: Called by reviewer when version fails review
        WHY: Returns version for author revision

        Args:
            notes: Reason for rejection

        Raises:
            InvalidVersionTransitionException: If not in review
        """
        if self.status != VersionStatus.IN_REVIEW:
            raise InvalidVersionTransitionException(
                f"Cannot reject from {self.status.value} status",
                {"current_status": self.status.value, "required_status": "in_review"}
            )
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
        self.status = VersionStatus.REJECTED
        self.updated_at = datetime.utcnow()

    def publish(self) -> None:
        """
        WHAT: Publishes the approved version
        WHERE: Called when version becomes live
        WHY: Makes version the current active version

        Raises:
            InvalidVersionTransitionException: If not approved
        """
        if self.status != VersionStatus.APPROVED:
            raise InvalidVersionTransitionException(
                f"Cannot publish from {self.status.value} status",
                {"current_status": self.status.value, "required_status": "approved"}
            )
        self.status = VersionStatus.PUBLISHED
        self.is_current = True
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def supersede(self) -> None:
        """
        WHAT: Marks version as superseded by a newer version
        WHERE: Called when new version is published
        WHY: Maintains history while marking as replaced
        """
        if self.status == VersionStatus.PUBLISHED:
            self.status = VersionStatus.SUPERSEDED
            self.is_current = False
            self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """
        WHAT: Archives the version
        WHERE: Called when version is no longer needed actively
        WHY: Preserves history while hiding from active views
        """
        self.status = VersionStatus.ARCHIVED
        self.is_current = False
        self.updated_at = datetime.utcnow()

    def update_content(self, new_content: Dict[str, Any]) -> None:
        """
        WHAT: Updates the content data
        WHERE: Called during editing
        WHY: Recalculates hash and metrics on content change

        Args:
            new_content: New content data

        Raises:
            InvalidVersionTransitionException: If not in editable status
        """
        if self.status not in [VersionStatus.DRAFT, VersionStatus.REJECTED]:
            raise InvalidVersionTransitionException(
                f"Cannot update content in {self.status.value} status",
                {"current_status": self.status.value, "editable_statuses": ["draft", "rejected"]}
            )
        self.content_data = new_content
        self._calculate_hash()
        self._calculate_metrics()

        # Reset to draft if was rejected
        if self.status == VersionStatus.REJECTED:
            self.status = VersionStatus.DRAFT

        self.updated_at = datetime.utcnow()

    def create_child_version(self) -> 'ContentVersion':
        """
        WHAT: Creates a new version based on this one
        WHERE: Called when starting new edits
        WHY: Enables non-destructive editing with lineage

        Returns:
            New ContentVersion as draft
        """
        return ContentVersion(
            id=uuid4(),
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            version_number=self.version_number + 1,
            content_data=self.content_data.copy(),
            title=self.title,
            description=self.description,
            tags=self.tags.copy(),
            status=VersionStatus.DRAFT,
            is_current=False,
            is_latest=True,
            created_by=self.created_by,
            organization_id=self.organization_id,
            parent_version_id=self.id,
            branch_id=self.branch_id,
            branch_name=self.branch_name
        )


@dataclass
class VersionDiff:
    """
    WHAT: Represents differences between two versions
    WHERE: Used for change tracking and review
    WHY: Enables understanding of what changed between versions

    Tracks:
    - Field-level changes
    - Change types (added, modified, deleted)
    - Change statistics
    """
    id: UUID
    entity_type: ContentEntityType
    entity_id: UUID
    source_version_id: UUID
    target_version_id: UUID

    # Diff data
    changes: List[Dict[str, Any]] = field(default_factory=list)
    # Format: {"field": "...", "change_type": "...", "old_value": ..., "new_value": ...}

    # Statistics
    fields_added: int = 0
    fields_modified: int = 0
    fields_deleted: int = 0
    total_changes: int = 0

    # Content changes
    words_added: int = 0
    words_deleted: int = 0
    net_word_change: int = 0

    # Metadata
    generated_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_change(
        self,
        field_path: str,
        change_type: ChangeType,
        old_value: Any = None,
        new_value: Any = None
    ) -> None:
        """
        WHAT: Records a field change
        WHERE: Called during diff generation
        WHY: Builds comprehensive change record

        Args:
            field_path: Dot-notation path to changed field
            change_type: Type of change
            old_value: Previous value
            new_value: New value
        """
        self.changes.append({
            "field": field_path,
            "change_type": change_type.value,
            "old_value": old_value,
            "new_value": new_value
        })

        self.total_changes += 1

        if change_type == ChangeType.CREATED:
            self.fields_added += 1
        elif change_type == ChangeType.UPDATED:
            self.fields_modified += 1
        elif change_type == ChangeType.DELETED:
            self.fields_deleted += 1

    def get_changes_by_type(self, change_type: ChangeType) -> List[Dict[str, Any]]:
        """
        WHAT: Filters changes by type
        WHERE: Used for focused change review
        WHY: Enables viewing specific change categories

        Args:
            change_type: Type to filter by

        Returns:
            List of changes of specified type
        """
        return [c for c in self.changes if c["change_type"] == change_type.value]

    def has_content_changes(self) -> bool:
        """
        WHAT: Checks if there are any content changes
        WHERE: Used for filtering meaningful diffs
        WHY: Differentiates metadata-only from content changes

        Returns:
            True if content fields were changed
        """
        content_fields = ["content", "body", "text", "html", "markdown"]
        return any(
            any(cf in c["field"].lower() for cf in content_fields)
            for c in self.changes
        )


@dataclass
class VersionBranch:
    """
    WHAT: Parallel development branch for content
    WHERE: Used when multiple versions need independent development
    WHY: Enables parallel work without conflicts (like git branches)

    Features:
    - Named branches (main, feature, experiment)
    - Branch from any version
    - Merge back to main
    """
    id: UUID
    entity_type: ContentEntityType
    entity_id: UUID
    name: str
    description: str = ""

    # Branch point
    parent_branch_id: Optional[UUID] = None
    parent_branch_name: str = "main"
    branched_from_version_id: Optional[UUID] = None

    # Status
    is_active: bool = True
    is_default: bool = False  # Is this the main branch?
    is_protected: bool = False  # Requires approval for changes?

    # Merge info
    merged_to_branch_id: Optional[UUID] = None
    merged_at: Optional[datetime] = None
    merge_commit_version_id: Optional[UUID] = None

    # Ownership
    created_by: UUID = field(default_factory=uuid4)
    organization_id: Optional[UUID] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_merged(
        self,
        target_branch_id: UUID,
        merge_version_id: UUID
    ) -> None:
        """
        WHAT: Marks branch as merged into another
        WHERE: Called after successful merge
        WHY: Records merge completion and prevents duplicate merges

        Args:
            target_branch_id: Branch merged into
            merge_version_id: Version created by merge
        """
        self.merged_to_branch_id = target_branch_id
        self.merged_at = datetime.utcnow()
        self.merge_commit_version_id = merge_version_id
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def close(self) -> None:
        """
        WHAT: Closes the branch without merging
        WHERE: Called when branch is abandoned
        WHY: Marks branch as inactive
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()


@dataclass
class VersionApproval:
    """
    WHAT: Approval record for version promotion
    WHERE: Used in approval workflow for content changes
    WHY: Tracks review decisions and enables multi-reviewer workflows

    Features:
    - Individual reviewer decisions
    - Approval with conditions
    - Change requests
    """
    id: UUID
    version_id: UUID
    reviewer_id: UUID

    # Decision
    status: ApprovalStatus = ApprovalStatus.PENDING
    decision_notes: str = ""

    # Change requests
    requested_changes: List[Dict[str, Any]] = field(default_factory=list)
    # Format: {"field": "...", "suggestion": "...", "priority": "required|optional"}

    # Metadata
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None

    # Follow-up
    changes_addressed: bool = False
    follow_up_version_id: Optional[UUID] = None

    def approve(self, notes: str = "") -> None:
        """
        WHAT: Records approval decision
        WHERE: Called when reviewer approves
        WHY: Advances version through workflow

        Args:
            notes: Optional approval notes
        """
        self.status = ApprovalStatus.APPROVED
        self.decision_notes = notes
        self.decided_at = datetime.utcnow()

    def reject(self, notes: str) -> None:
        """
        WHAT: Records rejection decision
        WHERE: Called when reviewer rejects
        WHY: Blocks version from publishing

        Args:
            notes: Reason for rejection
        """
        self.status = ApprovalStatus.REJECTED
        self.decision_notes = notes
        self.decided_at = datetime.utcnow()

    def request_changes(
        self,
        changes: List[Dict[str, Any]],
        notes: str = ""
    ) -> None:
        """
        WHAT: Requests changes before approval
        WHERE: Called when version needs modifications
        WHY: Provides actionable feedback to author

        Args:
            changes: List of requested changes
            notes: Additional notes
        """
        self.status = ApprovalStatus.CHANGES_REQUESTED
        self.requested_changes = changes
        self.decision_notes = notes
        self.decided_at = datetime.utcnow()

    def withdraw(self) -> None:
        """
        WHAT: Withdraws the approval request
        WHERE: Called when author withdraws version
        WHY: Cancels pending approval
        """
        self.status = ApprovalStatus.WITHDRAWN
        self.decided_at = datetime.utcnow()


@dataclass
class ContentLock:
    """
    WHAT: Editing lock to prevent concurrent modifications
    WHERE: Used when user begins editing content
    WHY: Prevents lost work from conflicting edits

    Features:
    - Time-limited locks
    - Force-break for admins
    - Lock inheritance
    """
    id: UUID
    entity_type: ContentEntityType
    entity_id: UUID
    version_id: UUID

    # Lock holder
    locked_by: UUID
    lock_reason: str = ""

    # Lock settings
    is_active: bool = True
    lock_level: str = "exclusive"  # exclusive, shared
    inherited_from_parent: bool = False

    # Timing
    acquired_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)

    # Metadata
    user_agent: str = ""
    ip_address: str = ""

    def is_expired(self) -> bool:
        """
        WHAT: Checks if lock has expired
        WHERE: Used before honoring locks
        WHY: Prevents stale locks from blocking

        Returns:
            True if lock has expired
        """
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False

    def refresh_heartbeat(self) -> None:
        """
        WHAT: Updates heartbeat timestamp
        WHERE: Called periodically by lock holder
        WHY: Indicates lock is still actively used
        """
        self.last_heartbeat = datetime.utcnow()

    def extend(self, duration_minutes: int) -> None:
        """
        WHAT: Extends lock expiration
        WHERE: Called when user needs more time
        WHY: Prevents lock expiring during active work

        Args:
            duration_minutes: Additional minutes to extend
        """
        from datetime import timedelta
        if self.expires_at:
            self.expires_at = self.expires_at + timedelta(minutes=duration_minutes)
        else:
            self.expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)

    def release(self) -> None:
        """
        WHAT: Releases the lock
        WHERE: Called when editing is complete
        WHY: Allows others to edit
        """
        self.is_active = False


@dataclass
class VersionMerge:
    """
    WHAT: Record of merging two version branches
    WHERE: Used when combining parallel development
    WHY: Tracks merge history and conflict resolution

    Features:
    - Source and target tracking
    - Conflict documentation
    - Merge result
    """
    id: UUID
    entity_type: ContentEntityType
    entity_id: UUID

    # Merge participants
    source_branch_id: UUID
    source_version_id: UUID
    target_branch_id: UUID
    target_version_id: UUID

    # Result
    result_version_id: Optional[UUID] = None
    merge_strategy: MergeStrategy = MergeStrategy.AUTO

    # Status
    is_complete: bool = False
    had_conflicts: bool = False
    conflicts_resolved: bool = True

    # Conflicts
    conflict_details: List[Dict[str, Any]] = field(default_factory=list)
    # Format: {"field": "...", "source_value": ..., "target_value": ..., "resolution": "..."}

    # Authorship
    merged_by: UUID = field(default_factory=uuid4)

    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def add_conflict(
        self,
        field_path: str,
        source_value: Any,
        target_value: Any,
        resolution: Optional[str] = None
    ) -> None:
        """
        WHAT: Records a merge conflict
        WHERE: Called during merge when conflict detected
        WHY: Tracks conflicts for resolution

        Args:
            field_path: Path to conflicting field
            source_value: Value from source branch
            target_value: Value from target branch
            resolution: How conflict was resolved (if resolved)
        """
        self.conflict_details.append({
            "field": field_path,
            "source_value": source_value,
            "target_value": target_value,
            "resolution": resolution,
            "resolved": resolution is not None
        })
        self.had_conflicts = True
        self.conflicts_resolved = all(
            c.get("resolved", False) for c in self.conflict_details
        )

    def resolve_conflict(self, field_path: str, resolution: str) -> None:
        """
        WHAT: Records conflict resolution
        WHERE: Called when user resolves a conflict
        WHY: Updates conflict status

        Args:
            field_path: Path to resolved field
            resolution: How it was resolved
        """
        for conflict in self.conflict_details:
            if conflict["field"] == field_path:
                conflict["resolution"] = resolution
                conflict["resolved"] = True
                break

        self.conflicts_resolved = all(
            c.get("resolved", False) for c in self.conflict_details
        )

    def complete(self, result_version_id: UUID) -> None:
        """
        WHAT: Marks merge as complete
        WHERE: Called when merge is finalized
        WHY: Records successful merge

        Args:
            result_version_id: ID of merged version

        Raises:
            MergeConflictException: If unresolved conflicts exist
        """
        if self.had_conflicts and not self.conflicts_resolved:
            raise MergeConflictException(
                "Cannot complete merge with unresolved conflicts",
                {"unresolved_count": sum(
                    1 for c in self.conflict_details if not c.get("resolved")
                )}
            )

        self.result_version_id = result_version_id
        self.is_complete = True
        self.completed_at = datetime.utcnow()


@dataclass
class VersionHistory:
    """
    WHAT: Aggregated history for a content entity
    WHERE: Used to display version timeline
    WHY: Provides comprehensive view of content evolution
    """
    entity_type: ContentEntityType
    entity_id: UUID

    # Version counts
    total_versions: int = 0
    current_version_id: Optional[UUID] = None
    current_version_number: Optional[int] = None
    latest_version_number: int = 0

    # Branch information
    total_branches: int = 0
    active_branches: int = 0
    branches: List[str] = field(default_factory=list)

    # Merge and approval statistics
    total_merges: int = 0
    total_approvals: int = 0
    pending_approvals: int = 0

    # Statistics
    total_authors: int = 0
    total_reviews: int = 0
    average_review_time_hours: float = 0.0

    # Timeline
    first_version_at: Optional[datetime] = None
    last_version_at: Optional[datetime] = None
    last_published_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Recent activity
    recent_versions: List[Dict[str, Any]] = field(default_factory=list)
    # Format: {"version_id": ..., "version_number": ..., "status": ..., "created_at": ...}


# =============================================================================
# Export all entities
# =============================================================================

__all__ = [
    # Enums
    "ContentEntityType",
    "VersionStatus",
    "ChangeType",
    "ApprovalStatus",
    "MergeStrategy",

    # Exceptions
    "ContentVersioningException",
    "VersionNotFoundException",
    "InvalidVersionTransitionException",
    "ContentLockedException",
    "MergeConflictException",
    "BranchNotFoundException",
    "InvalidApprovalException",

    # Core Entities
    "ContentVersion",
    "VersionDiff",
    "VersionBranch",
    "VersionApproval",
    "ContentLock",
    "VersionMerge",
    "VersionHistory",
]
