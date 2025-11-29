"""
Content Versioning API Endpoints

WHAT: FastAPI router for content version control operations
WHERE: Mounted on content-management service at /api/v1/versions
WHY: Provides REST API for version management, branching, approval workflows,
     and merge operations for content entities

This module provides endpoints for:
- Version CRUD operations and history
- Branch management for parallel development
- Approval workflow operations
- Content locking for conflict prevention
- Diff generation and merge operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from content_management.domain.entities.content_versioning import (
    ContentEntityType,
    VersionStatus,
    ApprovalStatus,
    MergeStrategy,
)
from content_management.application.services.content_version_service import (
    ContentVersionService,
    ContentVersioningException,
    VersionNotFoundException,
    InvalidVersionTransitionException,
    ContentLockedException,
    MergeConflictException,
    BranchNotFoundException,
    InvalidApprovalException,
)
from data_access.content_version_dao import ContentVersionDAO


# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter()


# =============================================================================
# Pydantic DTOs
# =============================================================================

# --- Version DTOs ---

class CreateVersionDTO(BaseModel):
    """
    WHAT: DTO for creating a new content version
    WHERE: Used in POST /versions endpoint
    WHY: Validates input for version creation
    """
    entity_type: ContentEntityType
    entity_id: UUID
    content_data: Dict[str, Any]
    title: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=5000)
    organization_id: Optional[UUID] = None
    branch_name: str = Field(default="main", max_length=100)


class ContentVersionDTO(BaseModel):
    """
    WHAT: DTO for content version responses
    WHERE: Used in version response payloads
    WHY: Standardizes version data format
    """
    id: UUID
    entity_type: str
    entity_id: UUID
    version_number: int
    content_data: Dict[str, Any]
    content_hash: str
    title: str
    description: str
    changelog: Optional[str]
    tags: List[str]
    status: str
    is_current: bool
    is_latest: bool
    created_by: UUID
    organization_id: Optional[UUID]
    parent_version_id: Optional[UUID]
    branch_id: Optional[UUID]
    branch_name: str
    content_size_bytes: int
    word_count: int
    reviewer_id: Optional[UUID]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class UpdateVersionContentDTO(BaseModel):
    """DTO for updating version content."""
    content_data: Dict[str, Any]


class SubmitForReviewDTO(BaseModel):
    """DTO for submitting version for review."""
    changelog: str = Field(default="", max_length=5000)


# --- Branch DTOs ---

class CreateBranchDTO(BaseModel):
    """
    WHAT: DTO for creating a new branch
    WHERE: Used in POST /branches endpoint
    WHY: Validates input for branch creation
    """
    entity_type: ContentEntityType
    entity_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=2000)
    source_version_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None


class VersionBranchDTO(BaseModel):
    """
    WHAT: DTO for version branch responses
    WHERE: Used in branch response payloads
    WHY: Standardizes branch data format
    """
    id: UUID
    entity_type: str
    entity_id: UUID
    name: str
    description: str
    parent_branch_id: Optional[UUID]
    parent_branch_name: str
    branched_from_version_id: Optional[UUID]
    is_active: bool
    is_default: bool
    is_protected: bool
    merged_to_branch_id: Optional[UUID]
    merged_at: Optional[datetime]
    merge_commit_version_id: Optional[UUID]
    created_by: UUID
    organization_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Approval DTOs ---

class AssignReviewerDTO(BaseModel):
    """DTO for assigning a reviewer."""
    reviewer_id: UUID


class ApprovalDecisionDTO(BaseModel):
    """DTO for approval decisions."""
    notes: str = Field(default="", max_length=5000)


class RequestChangesDTO(BaseModel):
    """DTO for requesting changes."""
    changes: List[Dict[str, Any]]
    notes: str = Field(default="", max_length=5000)


class VersionApprovalDTO(BaseModel):
    """
    WHAT: DTO for version approval responses
    WHERE: Used in approval response payloads
    WHY: Standardizes approval data format
    """
    id: UUID
    version_id: UUID
    reviewer_id: UUID
    status: str
    decision_notes: Optional[str]
    requested_changes: List[Dict[str, Any]]
    assigned_at: datetime
    decided_at: Optional[datetime]
    changes_addressed: bool
    follow_up_version_id: Optional[UUID]

    class Config:
        from_attributes = True


# --- Lock DTOs ---

class AcquireLockDTO(BaseModel):
    """
    WHAT: DTO for acquiring content lock
    WHERE: Used in POST /locks endpoint
    WHY: Validates lock acquisition request
    """
    entity_type: ContentEntityType
    entity_id: UUID
    reason: str = Field(default="", max_length=500)
    duration_minutes: int = Field(default=30, ge=1, le=480)


class ContentLockDTO(BaseModel):
    """
    WHAT: DTO for content lock responses
    WHERE: Used in lock response payloads
    WHY: Standardizes lock data format
    """
    id: UUID
    entity_type: str
    entity_id: UUID
    version_id: UUID
    locked_by: UUID
    lock_reason: Optional[str]
    is_active: bool
    lock_level: str
    inherited_from_parent: bool
    acquired_at: datetime
    expires_at: Optional[datetime]
    last_heartbeat: datetime

    class Config:
        from_attributes = True


class LockStatusDTO(BaseModel):
    """DTO for lock status response."""
    locked: bool
    locked_by: Optional[str] = None
    locked_at: Optional[str] = None
    expires_at: Optional[str] = None
    reason: Optional[str] = None
    can_edit: bool


# --- Diff DTOs ---

class GenerateDiffDTO(BaseModel):
    """DTO for generating diff between versions."""
    source_version_id: UUID
    target_version_id: UUID


class VersionDiffDTO(BaseModel):
    """
    WHAT: DTO for version diff responses
    WHERE: Used in diff response payloads
    WHY: Standardizes diff data format
    """
    id: UUID
    entity_type: str
    entity_id: UUID
    source_version_id: UUID
    target_version_id: UUID
    changes: List[Dict[str, Any]]
    fields_added: int
    fields_modified: int
    fields_deleted: int
    total_changes: int
    words_added: int
    words_deleted: int
    net_word_change: int
    generated_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- Merge DTOs ---

class MergeBranchesDTO(BaseModel):
    """
    WHAT: DTO for merging branches
    WHERE: Used in POST /merges endpoint
    WHY: Validates merge request
    """
    source_branch_id: UUID
    target_branch_id: UUID
    strategy: MergeStrategy = MergeStrategy.AUTO


class VersionMergeDTO(BaseModel):
    """
    WHAT: DTO for version merge responses
    WHERE: Used in merge response payloads
    WHY: Standardizes merge data format
    """
    id: UUID
    entity_type: str
    entity_id: UUID
    source_branch_id: UUID
    source_version_id: UUID
    target_branch_id: UUID
    target_version_id: UUID
    result_version_id: Optional[UUID]
    merge_strategy: str
    is_complete: bool
    had_conflicts: bool
    conflicts_resolved: bool
    conflict_details: List[Dict[str, Any]]
    merged_by: UUID
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- History DTOs ---

class VersionHistoryDTO(BaseModel):
    """
    WHAT: DTO for version history summary
    WHERE: Used in history response payloads
    WHY: Provides aggregated history statistics
    """
    entity_type: str
    entity_id: UUID
    total_versions: int
    total_branches: int
    active_branches: int
    total_merges: int
    total_approvals: int
    pending_approvals: int
    first_version_at: Optional[datetime]
    last_version_at: Optional[datetime]
    current_version_number: Optional[int]
    latest_version_number: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Rollback DTOs ---

class RollbackDTO(BaseModel):
    """DTO for rollback operations."""
    entity_type: ContentEntityType
    entity_id: UUID
    target_version_id: UUID


# =============================================================================
# Dependency Injection
# =============================================================================

async def get_service() -> ContentVersionService:
    """
    WHAT: Provides the ContentVersionService instance
    WHERE: Used as dependency in route handlers
    WHY: Enables dependency injection for testability

    Note: In production, this would get the pool from app state
    """
    from main import app
    dao = ContentVersionDAO(app.state.pool)
    return ContentVersionService(dao)


# =============================================================================
# Version Endpoints
# =============================================================================

@router.post(
    "/versions",
    response_model=ContentVersionDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create content version",
    description="Creates a new version of content with snapshot"
)
async def create_version(
    dto: CreateVersionDTO,
    created_by: UUID = Query(..., description="ID of the creating user"),
    service: ContentVersionService = Depends(get_service)
):
    """
    WHAT: Creates a new content version
    WHERE: Called when saving content changes
    WHY: Creates versioned snapshot for history tracking
    """
    try:
        version = await service.create_version(
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            content_data=dto.content_data,
            created_by=created_by,
            title=dto.title,
            description=dto.description,
            organization_id=dto.organization_id,
            branch_name=dto.branch_name
        )
        return _version_to_dto(version)
    except ContentVersioningException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/versions/{version_id}",
    response_model=ContentVersionDTO,
    summary="Get content version",
    description="Retrieves a specific content version by ID"
)
async def get_version(
    version_id: UUID,
    service: ContentVersionService = Depends(get_service)
):
    """Gets a content version by ID."""
    try:
        version = await service.get_version(version_id)
        return _version_to_dto(version)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/entities/{entity_type}/{entity_id}/current",
    response_model=Optional[ContentVersionDTO],
    summary="Get current version",
    description="Gets the currently published version for an entity"
)
async def get_current_version(
    entity_type: ContentEntityType,
    entity_id: UUID,
    service: ContentVersionService = Depends(get_service)
):
    """Gets the current published version."""
    version = await service.get_current_version(entity_type, entity_id)
    if not version:
        return None
    return _version_to_dto(version)


@router.get(
    "/entities/{entity_type}/{entity_id}/latest",
    response_model=Optional[ContentVersionDTO],
    summary="Get latest version",
    description="Gets the latest version in a branch"
)
async def get_latest_version(
    entity_type: ContentEntityType,
    entity_id: UUID,
    branch_name: str = Query(default="main"),
    service: ContentVersionService = Depends(get_service)
):
    """Gets the latest version in a branch."""
    version = await service.get_latest_version(entity_type, entity_id, branch_name)
    if not version:
        return None
    return _version_to_dto(version)


@router.get(
    "/entities/{entity_type}/{entity_id}/history",
    response_model=List[ContentVersionDTO],
    summary="Get version history",
    description="Gets version history for an entity"
)
async def get_version_history(
    entity_type: ContentEntityType,
    entity_id: UUID,
    branch_name: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    service: ContentVersionService = Depends(get_service)
):
    """Gets version history for an entity."""
    versions = await service.get_version_history(
        entity_type, entity_id, branch_name, limit, offset
    )
    return [_version_to_dto(v) for v in versions]


@router.patch(
    "/versions/{version_id}/content",
    response_model=ContentVersionDTO,
    summary="Update version content",
    description="Updates content of a draft version"
)
async def update_version_content(
    version_id: UUID,
    dto: UpdateVersionContentDTO,
    user_id: UUID = Query(..., description="ID of the user updating"),
    service: ContentVersionService = Depends(get_service)
):
    """Updates version content (only for drafts)."""
    try:
        version = await service.update_version_content(
            version_id, dto.content_data, user_id
        )
        return _version_to_dto(version)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ContentLockedException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except ContentVersioningException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Workflow Endpoints
# =============================================================================

@router.post(
    "/versions/{version_id}/submit-for-review",
    response_model=ContentVersionDTO,
    summary="Submit for review",
    description="Submits a version for review approval"
)
async def submit_for_review(
    version_id: UUID,
    dto: SubmitForReviewDTO,
    service: ContentVersionService = Depends(get_service)
):
    """Submits a version for review."""
    try:
        version = await service.submit_for_review(version_id, dto.changelog)
        return _version_to_dto(version)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidVersionTransitionException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/versions/{version_id}/assign-reviewer",
    response_model=VersionApprovalDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Assign reviewer",
    description="Assigns a reviewer to a version"
)
async def assign_reviewer(
    version_id: UUID,
    dto: AssignReviewerDTO,
    service: ContentVersionService = Depends(get_service)
):
    """Assigns a reviewer to a version."""
    try:
        approval = await service.assign_reviewer(version_id, dto.reviewer_id)
        return _approval_to_dto(approval)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidVersionTransitionException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/versions/{version_id}/start-review",
    response_model=ContentVersionDTO,
    summary="Start review",
    description="Marks version as being reviewed"
)
async def start_review(
    version_id: UUID,
    reviewer_id: UUID = Query(..., description="ID of the reviewer"),
    service: ContentVersionService = Depends(get_service)
):
    """Starts the review process."""
    try:
        version = await service.start_review(version_id, reviewer_id)
        return _version_to_dto(version)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidVersionTransitionException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/versions/{version_id}/approve",
    response_model=Dict[str, Any],
    summary="Approve version",
    description="Approves a version after review"
)
async def approve_version(
    version_id: UUID,
    dto: ApprovalDecisionDTO,
    reviewer_id: UUID = Query(..., description="ID of the reviewer"),
    service: ContentVersionService = Depends(get_service)
):
    """Approves a version."""
    try:
        version, approval = await service.approve_version(
            version_id, reviewer_id, dto.notes
        )
        return {
            "version": _version_to_dto(version),
            "approval": _approval_to_dto(approval)
        }
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidVersionTransitionException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/versions/{version_id}/reject",
    response_model=Dict[str, Any],
    summary="Reject version",
    description="Rejects a version with reason"
)
async def reject_version(
    version_id: UUID,
    dto: ApprovalDecisionDTO,
    reviewer_id: UUID = Query(..., description="ID of the reviewer"),
    service: ContentVersionService = Depends(get_service)
):
    """Rejects a version."""
    try:
        if not dto.notes:
            raise HTTPException(
                status_code=400,
                detail="Rejection notes are required"
            )
        version, approval = await service.reject_version(
            version_id, reviewer_id, dto.notes
        )
        return {
            "version": _version_to_dto(version),
            "approval": _approval_to_dto(approval)
        }
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidVersionTransitionException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/versions/{version_id}/request-changes",
    response_model=VersionApprovalDTO,
    summary="Request changes",
    description="Requests specific changes before approval"
)
async def request_changes(
    version_id: UUID,
    dto: RequestChangesDTO,
    reviewer_id: UUID = Query(..., description="ID of the reviewer"),
    service: ContentVersionService = Depends(get_service)
):
    """Requests changes to a version."""
    try:
        approval = await service.request_changes(
            version_id, reviewer_id, dto.changes, dto.notes
        )
        return _approval_to_dto(approval)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidApprovalException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/versions/{version_id}/publish",
    response_model=ContentVersionDTO,
    summary="Publish version",
    description="Publishes an approved version"
)
async def publish_version(
    version_id: UUID,
    service: ContentVersionService = Depends(get_service)
):
    """Publishes an approved version."""
    try:
        version = await service.publish_version(version_id)
        return _version_to_dto(version)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidVersionTransitionException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/rollback",
    response_model=ContentVersionDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Rollback to version",
    description="Creates new version based on a previous version"
)
async def rollback_to_version(
    dto: RollbackDTO,
    user_id: UUID = Query(..., description="ID of the user"),
    service: ContentVersionService = Depends(get_service)
):
    """Rolls back to a previous version."""
    try:
        version = await service.rollback_to_version(
            dto.entity_type,
            dto.entity_id,
            dto.target_version_id,
            user_id
        )
        return _version_to_dto(version)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ContentVersioningException as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Branch Endpoints
# =============================================================================

@router.post(
    "/branches",
    response_model=VersionBranchDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create branch",
    description="Creates a new development branch"
)
async def create_branch(
    dto: CreateBranchDTO,
    created_by: UUID = Query(..., description="ID of the creating user"),
    service: ContentVersionService = Depends(get_service)
):
    """Creates a new branch."""
    try:
        branch = await service.create_branch(
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            name=dto.name,
            created_by=created_by,
            description=dto.description,
            source_version_id=dto.source_version_id,
            organization_id=dto.organization_id
        )
        return _branch_to_dto(branch)
    except ContentVersioningException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/branches/{branch_id}",
    response_model=VersionBranchDTO,
    summary="Get branch",
    description="Retrieves a branch by ID"
)
async def get_branch(
    branch_id: UUID,
    service: ContentVersionService = Depends(get_service)
):
    """Gets a branch by ID."""
    try:
        branch = await service.get_branch(branch_id)
        return _branch_to_dto(branch)
    except BranchNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/entities/{entity_type}/{entity_id}/branches",
    response_model=List[VersionBranchDTO],
    summary="List entity branches",
    description="Lists all branches for an entity"
)
async def list_entity_branches(
    entity_type: ContentEntityType,
    entity_id: UUID,
    include_inactive: bool = Query(default=False),
    service: ContentVersionService = Depends(get_service)
):
    """Lists branches for an entity."""
    branches = await service.get_entity_branches(
        entity_type, entity_id, include_inactive
    )
    return [_branch_to_dto(b) for b in branches]


@router.post(
    "/branches/{branch_id}/close",
    response_model=VersionBranchDTO,
    summary="Close branch",
    description="Closes a branch (marks as inactive)"
)
async def close_branch(
    branch_id: UUID,
    service: ContentVersionService = Depends(get_service)
):
    """Closes a branch."""
    try:
        branch = await service.close_branch(branch_id)
        return _branch_to_dto(branch)
    except BranchNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Diff Endpoints
# =============================================================================

@router.post(
    "/diff",
    response_model=VersionDiffDTO,
    summary="Generate diff",
    description="Generates diff between two versions"
)
async def generate_diff(
    dto: GenerateDiffDTO,
    user_id: UUID = Query(..., description="ID of the requesting user"),
    service: ContentVersionService = Depends(get_service)
):
    """Generates diff between versions."""
    try:
        diff = await service.generate_diff(
            dto.source_version_id,
            dto.target_version_id,
            user_id
        )
        return _diff_to_dto(diff)
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Lock Endpoints
# =============================================================================

@router.post(
    "/locks",
    response_model=ContentLockDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Acquire lock",
    description="Acquires an editing lock on content"
)
async def acquire_lock(
    dto: AcquireLockDTO,
    user_id: UUID = Query(..., description="ID of the user"),
    service: ContentVersionService = Depends(get_service)
):
    """Acquires an editing lock."""
    try:
        lock = await service.acquire_lock(
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            user_id=user_id,
            reason=dto.reason,
            duration_minutes=dto.duration_minutes
        )
        return _lock_to_dto(lock)
    except ContentLockedException as e:
        raise HTTPException(status_code=423, detail=str(e))
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/locks/{entity_type}/{entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Release lock",
    description="Releases an editing lock"
)
async def release_lock(
    entity_type: ContentEntityType,
    entity_id: UUID,
    user_id: UUID = Query(..., description="ID of the user"),
    service: ContentVersionService = Depends(get_service)
):
    """Releases an editing lock."""
    await service.release_lock(entity_type, entity_id, user_id)


@router.post(
    "/locks/{entity_type}/{entity_id}/refresh",
    response_model=Optional[ContentLockDTO],
    summary="Refresh lock",
    description="Refreshes lock heartbeat to prevent expiration"
)
async def refresh_lock(
    entity_type: ContentEntityType,
    entity_id: UUID,
    user_id: UUID = Query(..., description="ID of the user"),
    service: ContentVersionService = Depends(get_service)
):
    """Refreshes a lock heartbeat."""
    lock = await service.refresh_lock(entity_type, entity_id, user_id)
    if not lock:
        return None
    return _lock_to_dto(lock)


@router.get(
    "/locks/{entity_type}/{entity_id}/status",
    response_model=LockStatusDTO,
    summary="Check lock status",
    description="Checks if content is locked"
)
async def check_lock_status(
    entity_type: ContentEntityType,
    entity_id: UUID,
    user_id: Optional[UUID] = None,
    service: ContentVersionService = Depends(get_service)
):
    """Checks lock status for entity."""
    status_info = await service.check_lock_status(entity_type, entity_id, user_id)
    return LockStatusDTO(**status_info)


# =============================================================================
# Merge Endpoints
# =============================================================================

@router.post(
    "/merges",
    response_model=VersionMergeDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Merge branches",
    description="Merges source branch into target branch"
)
async def merge_branches(
    dto: MergeBranchesDTO,
    user_id: UUID = Query(..., description="ID of the user"),
    service: ContentVersionService = Depends(get_service)
):
    """Merges branches."""
    try:
        merge = await service.merge_branches(
            source_branch_id=dto.source_branch_id,
            target_branch_id=dto.target_branch_id,
            user_id=user_id,
            strategy=dto.strategy
        )
        return _merge_to_dto(merge)
    except BranchNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MergeConflictException as e:
        raise HTTPException(status_code=409, detail=str(e))


# =============================================================================
# History & Analytics Endpoints
# =============================================================================

@router.get(
    "/entities/{entity_type}/{entity_id}/history-summary",
    response_model=VersionHistoryDTO,
    summary="Get history summary",
    description="Gets aggregated version history statistics"
)
async def get_history_summary(
    entity_type: ContentEntityType,
    entity_id: UUID,
    service: ContentVersionService = Depends(get_service)
):
    """Gets version history summary."""
    history = await service.get_version_history_summary(entity_type, entity_id)
    return _history_to_dto(history)


@router.get(
    "/pending-reviews",
    response_model=List[ContentVersionDTO],
    summary="Get pending reviews",
    description="Gets versions pending review"
)
async def get_pending_reviews(
    entity_type: ContentEntityType,
    organization_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=200),
    service: ContentVersionService = Depends(get_service)
):
    """Gets versions pending review."""
    versions = await service.get_pending_reviews(
        entity_type, organization_id, limit
    )
    return [_version_to_dto(v) for v in versions]


@router.get(
    "/reviewers/{reviewer_id}/queue",
    response_model=List[VersionApprovalDTO],
    summary="Get reviewer queue",
    description="Gets pending approvals for a reviewer"
)
async def get_reviewer_queue(
    reviewer_id: UUID,
    limit: int = Query(default=50, le=200),
    service: ContentVersionService = Depends(get_service)
):
    """Gets reviewer's pending approvals."""
    approvals = await service.get_reviewer_queue(reviewer_id, limit)
    return [_approval_to_dto(a) for a in approvals]


# =============================================================================
# DTO Conversion Helpers
# =============================================================================

def _version_to_dto(version) -> ContentVersionDTO:
    """
    WHAT: Converts ContentVersion to DTO
    WHERE: Used in endpoint responses
    WHY: Standardizes API output format
    """
    return ContentVersionDTO(
        id=version.id,
        entity_type=version.entity_type.value,
        entity_id=version.entity_id,
        version_number=version.version_number,
        content_data=version.content_data,
        content_hash=version.content_hash,
        title=version.title,
        description=version.description,
        changelog=version.changelog,
        tags=version.tags,
        status=version.status.value,
        is_current=version.is_current,
        is_latest=version.is_latest,
        created_by=version.created_by,
        organization_id=version.organization_id,
        parent_version_id=version.parent_version_id,
        branch_id=version.branch_id,
        branch_name=version.branch_name,
        content_size_bytes=version.content_size_bytes,
        word_count=version.word_count,
        reviewer_id=version.reviewer_id,
        reviewed_at=version.reviewed_at,
        review_notes=version.review_notes,
        created_at=version.created_at,
        updated_at=version.updated_at,
        published_at=version.published_at
    )


def _branch_to_dto(branch) -> VersionBranchDTO:
    """
    WHAT: Converts VersionBranch to DTO
    WHERE: Used in endpoint responses
    WHY: Standardizes API output format
    """
    return VersionBranchDTO(
        id=branch.id,
        entity_type=branch.entity_type.value,
        entity_id=branch.entity_id,
        name=branch.name,
        description=branch.description,
        parent_branch_id=branch.parent_branch_id,
        parent_branch_name=branch.parent_branch_name,
        branched_from_version_id=branch.branched_from_version_id,
        is_active=branch.is_active,
        is_default=branch.is_default,
        is_protected=branch.is_protected,
        merged_to_branch_id=branch.merged_to_branch_id,
        merged_at=branch.merged_at,
        merge_commit_version_id=branch.merge_commit_version_id,
        created_by=branch.created_by,
        organization_id=branch.organization_id,
        created_at=branch.created_at,
        updated_at=branch.updated_at
    )


def _approval_to_dto(approval) -> VersionApprovalDTO:
    """
    WHAT: Converts VersionApproval to DTO
    WHERE: Used in endpoint responses
    WHY: Standardizes API output format
    """
    return VersionApprovalDTO(
        id=approval.id,
        version_id=approval.version_id,
        reviewer_id=approval.reviewer_id,
        status=approval.status.value,
        decision_notes=approval.decision_notes,
        requested_changes=approval.requested_changes,
        assigned_at=approval.assigned_at,
        decided_at=approval.decided_at,
        changes_addressed=approval.changes_addressed,
        follow_up_version_id=approval.follow_up_version_id
    )


def _lock_to_dto(lock) -> ContentLockDTO:
    """
    WHAT: Converts ContentLock to DTO
    WHERE: Used in endpoint responses
    WHY: Standardizes API output format
    """
    return ContentLockDTO(
        id=lock.id,
        entity_type=lock.entity_type.value,
        entity_id=lock.entity_id,
        version_id=lock.version_id,
        locked_by=lock.locked_by,
        lock_reason=lock.lock_reason,
        is_active=lock.is_active,
        lock_level=lock.lock_level,
        inherited_from_parent=lock.inherited_from_parent,
        acquired_at=lock.acquired_at,
        expires_at=lock.expires_at,
        last_heartbeat=lock.last_heartbeat
    )


def _diff_to_dto(diff) -> VersionDiffDTO:
    """
    WHAT: Converts VersionDiff to DTO
    WHERE: Used in endpoint responses
    WHY: Standardizes API output format
    """
    return VersionDiffDTO(
        id=diff.id,
        entity_type=diff.entity_type.value,
        entity_id=diff.entity_id,
        source_version_id=diff.source_version_id,
        target_version_id=diff.target_version_id,
        changes=diff.changes,
        fields_added=diff.fields_added,
        fields_modified=diff.fields_modified,
        fields_deleted=diff.fields_deleted,
        total_changes=diff.total_changes,
        words_added=diff.words_added,
        words_deleted=diff.words_deleted,
        net_word_change=diff.net_word_change,
        generated_by=diff.generated_by,
        created_at=diff.created_at
    )


def _merge_to_dto(merge) -> VersionMergeDTO:
    """
    WHAT: Converts VersionMerge to DTO
    WHERE: Used in endpoint responses
    WHY: Standardizes API output format
    """
    return VersionMergeDTO(
        id=merge.id,
        entity_type=merge.entity_type.value,
        entity_id=merge.entity_id,
        source_branch_id=merge.source_branch_id,
        source_version_id=merge.source_version_id,
        target_branch_id=merge.target_branch_id,
        target_version_id=merge.target_version_id,
        result_version_id=merge.result_version_id,
        merge_strategy=merge.merge_strategy.value,
        is_complete=merge.is_complete,
        had_conflicts=merge.had_conflicts,
        conflicts_resolved=merge.conflicts_resolved,
        conflict_details=merge.conflict_details,
        merged_by=merge.merged_by,
        started_at=merge.started_at,
        completed_at=merge.completed_at
    )


def _history_to_dto(history) -> VersionHistoryDTO:
    """
    WHAT: Converts VersionHistory to DTO
    WHERE: Used in endpoint responses
    WHY: Standardizes API output format
    """
    return VersionHistoryDTO(
        entity_type=history.entity_type.value,
        entity_id=history.entity_id,
        total_versions=history.total_versions,
        total_branches=history.total_branches,
        active_branches=history.active_branches,
        total_merges=history.total_merges,
        total_approvals=history.total_approvals,
        pending_approvals=history.pending_approvals,
        first_version_at=history.first_version_at,
        last_version_at=history.last_version_at,
        current_version_number=history.current_version_number,
        latest_version_number=history.latest_version_number,
        created_at=history.created_at
    )
