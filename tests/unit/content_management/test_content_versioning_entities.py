"""
Unit Tests for Content Versioning Domain Entities

WHAT: Comprehensive test suite for content versioning entities
WHERE: Tests run as part of content-management unit test suite
WHY: Ensures version control functionality works correctly including
     status transitions, branching, merging, and approval workflows

Test Coverage:
- All enum types and values
- All custom exception types
- ContentVersion entity with all status transitions
- VersionDiff change tracking
- VersionBranch lifecycle
- VersionApproval workflow
- ContentLock expiration and heartbeat
- VersionMerge conflict handling
- VersionHistory aggregation
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import json
import hashlib

from content_management.domain.entities.content_versioning import (
    # Enums
    ContentEntityType,
    VersionStatus,
    ChangeType,
    ApprovalStatus,
    MergeStrategy,
    # Exceptions
    ContentVersioningException,
    VersionNotFoundException,
    InvalidVersionTransitionException,
    ContentLockedException,
    MergeConflictException,
    BranchNotFoundException,
    InvalidApprovalException,
    # Entities
    ContentVersion,
    VersionDiff,
    VersionBranch,
    VersionApproval,
    ContentLock,
    VersionMerge,
    VersionHistory,
)


# =============================================================================
# Enum Tests
# =============================================================================

class TestContentEntityTypeEnum:
    """Tests for ContentEntityType enum."""

    def test_all_entity_types_exist(self):
        """Verifies all expected entity types are defined."""
        expected_types = [
            "course", "module", "lesson", "quiz", "question",
            "assignment", "resource", "syllabus", "interactive_element",
            "slide", "video", "document"
        ]
        actual_types = [t.value for t in ContentEntityType]
        assert set(actual_types) == set(expected_types)

    def test_entity_type_count(self):
        """Ensures correct number of entity types."""
        assert len(ContentEntityType) == 12

    def test_entity_type_values(self):
        """Tests specific entity type values."""
        assert ContentEntityType.COURSE.value == "course"
        assert ContentEntityType.QUIZ.value == "quiz"
        assert ContentEntityType.INTERACTIVE_ELEMENT.value == "interactive_element"


class TestVersionStatusEnum:
    """Tests for VersionStatus enum."""

    def test_all_statuses_exist(self):
        """Verifies all expected status values are defined."""
        expected = [
            "draft", "pending_review", "in_review", "approved",
            "rejected", "published", "superseded", "archived"
        ]
        actual = [s.value for s in VersionStatus]
        assert set(actual) == set(expected)

    def test_status_count(self):
        """Ensures correct number of statuses."""
        assert len(VersionStatus) == 8

    def test_initial_status_is_draft(self):
        """Confirms draft is available as initial status."""
        assert VersionStatus.DRAFT.value == "draft"


class TestChangeTypeEnum:
    """Tests for ChangeType enum."""

    def test_all_change_types_exist(self):
        """Verifies all expected change types."""
        expected = ["created", "updated", "deleted", "renamed", "moved", "restructured"]
        actual = [c.value for c in ChangeType]
        assert set(actual) == set(expected)

    def test_change_type_count(self):
        """Ensures correct number of change types."""
        assert len(ChangeType) == 6


class TestApprovalStatusEnum:
    """Tests for ApprovalStatus enum."""

    def test_all_approval_statuses_exist(self):
        """Verifies all expected approval statuses."""
        expected = ["pending", "approved", "rejected", "changes_requested", "withdrawn"]
        actual = [s.value for s in ApprovalStatus]
        assert set(actual) == set(expected)

    def test_approval_status_count(self):
        """Ensures correct number of approval statuses."""
        assert len(ApprovalStatus) == 5


class TestMergeStrategyEnum:
    """Tests for MergeStrategy enum."""

    def test_all_strategies_exist(self):
        """Verifies all expected merge strategies."""
        expected = ["ours", "theirs", "manual", "auto"]
        actual = [s.value for s in MergeStrategy]
        assert set(actual) == set(expected)

    def test_merge_strategy_count(self):
        """Ensures correct number of merge strategies."""
        assert len(MergeStrategy) == 4


# =============================================================================
# Exception Tests
# =============================================================================

class TestContentVersioningException:
    """Tests for base versioning exception."""

    def test_exception_with_message(self):
        """Tests exception creation with message."""
        exc = ContentVersioningException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.details == {}

    def test_exception_with_details(self):
        """Tests exception creation with details."""
        details = {"version_id": "123", "status": "draft"}
        exc = ContentVersioningException("Test error", details)
        assert exc.details == details

    def test_exception_inheritance(self):
        """Tests that it inherits from Exception."""
        exc = ContentVersioningException("Test")
        assert isinstance(exc, Exception)


class TestVersionNotFoundException:
    """Tests for VersionNotFoundException."""

    def test_inheritance(self):
        """Tests proper inheritance chain."""
        exc = VersionNotFoundException("Not found")
        assert isinstance(exc, ContentVersioningException)
        assert isinstance(exc, Exception)


class TestInvalidVersionTransitionException:
    """Tests for InvalidVersionTransitionException."""

    def test_inheritance_and_details(self):
        """Tests inheritance and detail propagation."""
        exc = InvalidVersionTransitionException(
            "Cannot transition",
            {"from": "draft", "to": "published"}
        )
        assert isinstance(exc, ContentVersioningException)
        assert exc.details["from"] == "draft"


class TestContentLockedException:
    """Tests for ContentLockedException."""

    def test_locked_exception(self):
        """Tests locked exception creation."""
        exc = ContentLockedException("Content locked", {"locked_by": "user123"})
        assert isinstance(exc, ContentVersioningException)
        assert "user123" in exc.details["locked_by"]


class TestMergeConflictException:
    """Tests for MergeConflictException."""

    def test_conflict_exception(self):
        """Tests merge conflict exception."""
        exc = MergeConflictException("Merge conflict", {"field": "title"})
        assert isinstance(exc, ContentVersioningException)


class TestBranchNotFoundException:
    """Tests for BranchNotFoundException."""

    def test_branch_not_found(self):
        """Tests branch not found exception."""
        exc = BranchNotFoundException("Branch not found")
        assert isinstance(exc, ContentVersioningException)


class TestInvalidApprovalException:
    """Tests for InvalidApprovalException."""

    def test_invalid_approval(self):
        """Tests invalid approval exception."""
        exc = InvalidApprovalException("Invalid approval operation")
        assert isinstance(exc, ContentVersioningException)


# =============================================================================
# ContentVersion Entity Tests
# =============================================================================

class TestContentVersionCreation:
    """Tests for ContentVersion entity creation."""

    def test_basic_creation(self):
        """Tests basic version creation."""
        version_id = uuid4()
        entity_id = uuid4()
        creator_id = uuid4()

        version = ContentVersion(
            id=version_id,
            entity_type=ContentEntityType.COURSE,
            entity_id=entity_id,
            version_number=1,
            created_by=creator_id
        )

        assert version.id == version_id
        assert version.entity_type == ContentEntityType.COURSE
        assert version.entity_id == entity_id
        assert version.version_number == 1
        assert version.status == VersionStatus.DRAFT
        assert version.is_latest is True
        assert version.is_current is False

    def test_creation_with_content(self):
        """Tests creation with content data."""
        content = {"title": "Test Course", "description": "A test course"}

        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            content_data=content
        )

        assert version.content_data == content
        assert version.content_hash != ""
        assert version.content_size_bytes > 0

    def test_content_hash_calculation(self):
        """Tests that content hash is correctly calculated."""
        content = {"title": "Test", "body": "Content"}
        expected_hash = hashlib.sha256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()

        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.LESSON,
            entity_id=uuid4(),
            version_number=1,
            content_data=content
        )

        assert version.content_hash == expected_hash

    def test_word_count_calculation(self):
        """Tests word count calculation from content."""
        content = {
            "title": "Test Title",
            "body": "This is the body text with several words",
            "nested": {"description": "More text here"}
        }

        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.LESSON,
            entity_id=uuid4(),
            version_number=1,
            content_data=content
        )

        assert version.word_count > 0

    def test_default_branch_name(self):
        """Tests default branch name is main."""
        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1
        )

        assert version.branch_name == "main"


class TestContentVersionStatusTransitions:
    """Tests for ContentVersion status transitions."""

    @pytest.fixture
    def draft_version(self):
        """Creates a draft version for testing."""
        return ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            content_data={"title": "Test"}
        )

    def test_submit_for_review_from_draft(self, draft_version):
        """Tests submitting draft for review."""
        draft_version.submit_for_review("Initial submission")

        assert draft_version.status == VersionStatus.PENDING_REVIEW
        assert draft_version.changelog == "Initial submission"

    def test_submit_for_review_invalid_status(self, draft_version):
        """Tests that non-draft cannot be submitted for review."""
        draft_version.status = VersionStatus.PUBLISHED

        with pytest.raises(InvalidVersionTransitionException) as exc_info:
            draft_version.submit_for_review()

        assert "Cannot submit for review" in str(exc_info.value)

    def test_start_review_from_pending(self, draft_version):
        """Tests starting review from pending status."""
        reviewer_id = uuid4()
        draft_version.submit_for_review()
        draft_version.start_review(reviewer_id)

        assert draft_version.status == VersionStatus.IN_REVIEW
        assert draft_version.reviewer_id == reviewer_id

    def test_start_review_invalid_status(self, draft_version):
        """Tests starting review from invalid status."""
        with pytest.raises(InvalidVersionTransitionException):
            draft_version.start_review(uuid4())

    def test_approve_from_in_review(self, draft_version):
        """Tests approval from in_review status."""
        reviewer_id = uuid4()
        draft_version.submit_for_review()
        draft_version.start_review(reviewer_id)
        draft_version.approve("Looks good")

        assert draft_version.status == VersionStatus.APPROVED
        assert draft_version.review_notes == "Looks good"
        assert draft_version.reviewed_at is not None

    def test_approve_invalid_status(self, draft_version):
        """Tests approval from invalid status."""
        with pytest.raises(InvalidVersionTransitionException):
            draft_version.approve()

    def test_reject_from_in_review(self, draft_version):
        """Tests rejection from in_review status."""
        draft_version.submit_for_review()
        draft_version.start_review(uuid4())
        draft_version.reject("Needs improvement")

        assert draft_version.status == VersionStatus.REJECTED
        assert draft_version.review_notes == "Needs improvement"

    def test_reject_invalid_status(self, draft_version):
        """Tests rejection from invalid status."""
        with pytest.raises(InvalidVersionTransitionException):
            draft_version.reject("Reason")

    def test_publish_from_approved(self, draft_version):
        """Tests publishing approved version."""
        draft_version.submit_for_review()
        draft_version.start_review(uuid4())
        draft_version.approve()
        draft_version.publish()

        assert draft_version.status == VersionStatus.PUBLISHED
        assert draft_version.is_current is True
        assert draft_version.published_at is not None

    def test_publish_invalid_status(self, draft_version):
        """Tests publishing from invalid status."""
        with pytest.raises(InvalidVersionTransitionException):
            draft_version.publish()

    def test_supersede_published_version(self, draft_version):
        """Tests superseding a published version."""
        draft_version.submit_for_review()
        draft_version.start_review(uuid4())
        draft_version.approve()
        draft_version.publish()
        draft_version.supersede()

        assert draft_version.status == VersionStatus.SUPERSEDED
        assert draft_version.is_current is False

    def test_archive_version(self, draft_version):
        """Tests archiving a version."""
        draft_version.archive()

        assert draft_version.status == VersionStatus.ARCHIVED
        assert draft_version.is_current is False


class TestContentVersionContentUpdate:
    """Tests for ContentVersion content update."""

    def test_update_content_in_draft(self):
        """Tests updating content in draft status."""
        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            content_data={"title": "Original"}
        )
        original_hash = version.content_hash

        version.update_content({"title": "Updated"})

        assert version.content_data["title"] == "Updated"
        assert version.content_hash != original_hash

    def test_update_content_in_rejected(self):
        """Tests updating content in rejected status."""
        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            content_data={"title": "Original"},
            status=VersionStatus.REJECTED
        )

        version.update_content({"title": "Fixed"})

        assert version.content_data["title"] == "Fixed"
        assert version.status == VersionStatus.DRAFT

    def test_update_content_invalid_status(self):
        """Tests updating content in non-editable status."""
        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            status=VersionStatus.PUBLISHED
        )

        with pytest.raises(InvalidVersionTransitionException) as exc_info:
            version.update_content({"title": "Update"})

        assert "Cannot update content" in str(exc_info.value)


class TestContentVersionChildCreation:
    """Tests for creating child versions."""

    def test_create_child_version(self):
        """Tests creating a child version."""
        parent = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            content_data={"title": "Parent"},
            tags=["tag1", "tag2"]
        )

        child = parent.create_child_version()

        assert child.id != parent.id
        assert child.version_number == 2
        assert child.parent_version_id == parent.id
        assert child.entity_id == parent.entity_id
        assert child.status == VersionStatus.DRAFT
        assert child.is_latest is True
        assert child.content_data == parent.content_data

    def test_child_version_tags_are_copied(self):
        """Tests that tags are copied to child."""
        parent = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            tags=["important"]
        )

        child = parent.create_child_version()

        assert "important" in child.tags
        # Verify it's a copy, not reference
        child.tags.append("new_tag")
        assert "new_tag" not in parent.tags


# =============================================================================
# VersionDiff Entity Tests
# =============================================================================

class TestVersionDiffCreation:
    """Tests for VersionDiff entity."""

    def test_basic_creation(self):
        """Tests basic diff creation."""
        diff = VersionDiff(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_version_id=uuid4(),
            target_version_id=uuid4()
        )

        assert diff.changes == []
        assert diff.total_changes == 0

    def test_add_created_change(self):
        """Tests adding a created change."""
        diff = VersionDiff(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_version_id=uuid4(),
            target_version_id=uuid4()
        )

        diff.add_change("title", ChangeType.CREATED, None, "New Title")

        assert len(diff.changes) == 1
        assert diff.fields_added == 1
        assert diff.total_changes == 1

    def test_add_updated_change(self):
        """Tests adding an updated change."""
        diff = VersionDiff(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_version_id=uuid4(),
            target_version_id=uuid4()
        )

        diff.add_change("title", ChangeType.UPDATED, "Old", "New")

        assert diff.fields_modified == 1

    def test_add_deleted_change(self):
        """Tests adding a deleted change."""
        diff = VersionDiff(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_version_id=uuid4(),
            target_version_id=uuid4()
        )

        diff.add_change("description", ChangeType.DELETED, "Old desc", None)

        assert diff.fields_deleted == 1

    def test_get_changes_by_type(self):
        """Tests filtering changes by type."""
        diff = VersionDiff(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_version_id=uuid4(),
            target_version_id=uuid4()
        )

        diff.add_change("field1", ChangeType.CREATED, None, "new")
        diff.add_change("field2", ChangeType.UPDATED, "old", "new")
        diff.add_change("field3", ChangeType.CREATED, None, "another")

        created = diff.get_changes_by_type(ChangeType.CREATED)
        assert len(created) == 2

    def test_has_content_changes(self):
        """Tests detecting content changes."""
        diff = VersionDiff(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_version_id=uuid4(),
            target_version_id=uuid4()
        )

        diff.add_change("metadata.author", ChangeType.UPDATED, "old", "new")
        assert diff.has_content_changes() is False

        diff.add_change("content.body", ChangeType.UPDATED, "old", "new")
        assert diff.has_content_changes() is True


# =============================================================================
# VersionBranch Entity Tests
# =============================================================================

class TestVersionBranchCreation:
    """Tests for VersionBranch entity."""

    def test_basic_creation(self):
        """Tests basic branch creation."""
        branch = VersionBranch(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            name="feature-x"
        )

        assert branch.name == "feature-x"
        assert branch.is_active is True
        assert branch.is_default is False
        assert branch.parent_branch_name == "main"

    def test_mark_merged(self):
        """Tests marking branch as merged."""
        branch = VersionBranch(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            name="feature-x"
        )
        target_id = uuid4()
        merge_version_id = uuid4()

        branch.mark_merged(target_id, merge_version_id)

        assert branch.merged_to_branch_id == target_id
        assert branch.merge_commit_version_id == merge_version_id
        assert branch.is_active is False
        assert branch.merged_at is not None

    def test_close_branch(self):
        """Tests closing a branch."""
        branch = VersionBranch(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            name="experiment"
        )

        branch.close()

        assert branch.is_active is False


# =============================================================================
# VersionApproval Entity Tests
# =============================================================================

class TestVersionApprovalCreation:
    """Tests for VersionApproval entity."""

    def test_basic_creation(self):
        """Tests basic approval creation."""
        approval = VersionApproval(
            id=uuid4(),
            version_id=uuid4(),
            reviewer_id=uuid4()
        )

        assert approval.status == ApprovalStatus.PENDING
        assert approval.requested_changes == []

    def test_approve(self):
        """Tests approval action."""
        approval = VersionApproval(
            id=uuid4(),
            version_id=uuid4(),
            reviewer_id=uuid4()
        )

        approval.approve("Well done!")

        assert approval.status == ApprovalStatus.APPROVED
        assert approval.decision_notes == "Well done!"
        assert approval.decided_at is not None

    def test_reject(self):
        """Tests rejection action."""
        approval = VersionApproval(
            id=uuid4(),
            version_id=uuid4(),
            reviewer_id=uuid4()
        )

        approval.reject("Needs work")

        assert approval.status == ApprovalStatus.REJECTED
        assert approval.decision_notes == "Needs work"

    def test_request_changes(self):
        """Tests requesting changes."""
        approval = VersionApproval(
            id=uuid4(),
            version_id=uuid4(),
            reviewer_id=uuid4()
        )

        changes = [
            {"field": "title", "suggestion": "Make it clearer", "priority": "required"}
        ]
        approval.request_changes(changes, "Please address these")

        assert approval.status == ApprovalStatus.CHANGES_REQUESTED
        assert len(approval.requested_changes) == 1
        assert approval.requested_changes[0]["field"] == "title"

    def test_withdraw(self):
        """Tests withdrawal."""
        approval = VersionApproval(
            id=uuid4(),
            version_id=uuid4(),
            reviewer_id=uuid4()
        )

        approval.withdraw()

        assert approval.status == ApprovalStatus.WITHDRAWN


# =============================================================================
# ContentLock Entity Tests
# =============================================================================

class TestContentLockCreation:
    """Tests for ContentLock entity."""

    def test_basic_creation(self):
        """Tests basic lock creation."""
        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4()
        )

        assert lock.is_active is True
        assert lock.lock_level == "exclusive"

    def test_is_expired_no_expiry(self):
        """Tests expiration check without expiry time."""
        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4()
        )

        assert lock.is_expired() is False

    def test_is_expired_with_future_expiry(self):
        """Tests expiration check with future expiry."""
        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        assert lock.is_expired() is False

    def test_is_expired_with_past_expiry(self):
        """Tests expiration check with past expiry."""
        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4(),
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )

        assert lock.is_expired() is True

    def test_refresh_heartbeat(self):
        """Tests heartbeat refresh."""
        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4()
        )
        original_heartbeat = lock.last_heartbeat

        # Small delay to ensure time difference
        import time
        time.sleep(0.01)
        lock.refresh_heartbeat()

        assert lock.last_heartbeat >= original_heartbeat

    def test_extend_lock(self):
        """Tests lock extension."""
        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4(),
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        original_expiry = lock.expires_at

        lock.extend(30)

        assert lock.expires_at > original_expiry

    def test_extend_lock_without_expiry(self):
        """Tests extending lock that has no expiry."""
        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4()
        )

        lock.extend(60)

        assert lock.expires_at is not None

    def test_release_lock(self):
        """Tests lock release."""
        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4()
        )

        lock.release()

        assert lock.is_active is False


# =============================================================================
# VersionMerge Entity Tests
# =============================================================================

class TestVersionMergeCreation:
    """Tests for VersionMerge entity."""

    def test_basic_creation(self):
        """Tests basic merge creation."""
        merge = VersionMerge(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_branch_id=uuid4(),
            source_version_id=uuid4(),
            target_branch_id=uuid4(),
            target_version_id=uuid4()
        )

        assert merge.is_complete is False
        assert merge.had_conflicts is False
        assert merge.conflicts_resolved is True

    def test_add_conflict(self):
        """Tests adding a conflict."""
        merge = VersionMerge(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_branch_id=uuid4(),
            source_version_id=uuid4(),
            target_branch_id=uuid4(),
            target_version_id=uuid4()
        )

        merge.add_conflict("title", "Source Title", "Target Title")

        assert merge.had_conflicts is True
        assert merge.conflicts_resolved is False
        assert len(merge.conflict_details) == 1

    def test_resolve_conflict(self):
        """Tests resolving a conflict."""
        merge = VersionMerge(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_branch_id=uuid4(),
            source_version_id=uuid4(),
            target_branch_id=uuid4(),
            target_version_id=uuid4()
        )
        merge.add_conflict("title", "Source", "Target")

        merge.resolve_conflict("title", "Used source value")

        assert merge.conflicts_resolved is True

    def test_complete_without_conflicts(self):
        """Tests completing merge without conflicts."""
        merge = VersionMerge(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_branch_id=uuid4(),
            source_version_id=uuid4(),
            target_branch_id=uuid4(),
            target_version_id=uuid4()
        )
        result_id = uuid4()

        merge.complete(result_id)

        assert merge.is_complete is True
        assert merge.result_version_id == result_id
        assert merge.completed_at is not None

    def test_complete_with_resolved_conflicts(self):
        """Tests completing merge with resolved conflicts."""
        merge = VersionMerge(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_branch_id=uuid4(),
            source_version_id=uuid4(),
            target_branch_id=uuid4(),
            target_version_id=uuid4()
        )
        merge.add_conflict("title", "A", "B")
        merge.resolve_conflict("title", "A")

        merge.complete(uuid4())

        assert merge.is_complete is True

    def test_complete_with_unresolved_conflicts_fails(self):
        """Tests that completing with unresolved conflicts raises exception."""
        merge = VersionMerge(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_branch_id=uuid4(),
            source_version_id=uuid4(),
            target_branch_id=uuid4(),
            target_version_id=uuid4()
        )
        merge.add_conflict("title", "A", "B")

        with pytest.raises(MergeConflictException) as exc_info:
            merge.complete(uuid4())

        assert "unresolved conflicts" in str(exc_info.value)


# =============================================================================
# VersionHistory Entity Tests
# =============================================================================

class TestVersionHistoryCreation:
    """Tests for VersionHistory entity."""

    def test_basic_creation(self):
        """Tests basic history creation."""
        history = VersionHistory(
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4()
        )

        assert history.total_versions == 0
        assert history.total_branches == 0
        assert history.branches == []

    def test_creation_with_statistics(self):
        """Tests history creation with statistics."""
        entity_id = uuid4()
        history = VersionHistory(
            entity_type=ContentEntityType.COURSE,
            entity_id=entity_id,
            total_versions=10,
            total_branches=3,
            active_branches=2,
            current_version_number=5,
            latest_version_number=10
        )

        assert history.total_versions == 10
        assert history.total_branches == 3
        assert history.active_branches == 2
        assert history.current_version_number == 5
        assert history.latest_version_number == 10


# =============================================================================
# Integration Tests - Complete Workflow
# =============================================================================

class TestContentVersionWorkflow:
    """Integration tests for complete version workflows."""

    def test_full_publishing_workflow(self):
        """Tests complete workflow from draft to published."""
        # Create initial draft
        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            content_data={"title": "My Course", "description": "A great course"}
        )

        # Verify initial state
        assert version.status == VersionStatus.DRAFT
        assert version.is_current is False

        # Submit for review
        version.submit_for_review("Initial version ready for review")
        assert version.status == VersionStatus.PENDING_REVIEW

        # Start review
        reviewer_id = uuid4()
        version.start_review(reviewer_id)
        assert version.status == VersionStatus.IN_REVIEW

        # Approve
        version.approve("Content looks good!")
        assert version.status == VersionStatus.APPROVED

        # Publish
        version.publish()
        assert version.status == VersionStatus.PUBLISHED
        assert version.is_current is True
        assert version.published_at is not None

    def test_rejection_and_revision_workflow(self):
        """Tests workflow when content is rejected and revised."""
        version = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.LESSON,
            entity_id=uuid4(),
            version_number=1,
            content_data={"title": "Lesson 1", "body": "Content"}
        )

        # Submit and review
        version.submit_for_review()
        version.start_review(uuid4())

        # Reject
        version.reject("Needs more examples")
        assert version.status == VersionStatus.REJECTED

        # Revise content
        version.update_content({
            "title": "Lesson 1",
            "body": "Content with more examples"
        })
        assert version.status == VersionStatus.DRAFT

        # Resubmit
        version.submit_for_review("Added more examples")
        assert version.status == VersionStatus.PENDING_REVIEW

    def test_version_supersession_workflow(self):
        """Tests workflow when new version supersedes old."""
        # Create and publish first version
        v1 = ContentVersion(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            version_number=1,
            content_data={"version": 1}
        )
        v1.submit_for_review()
        v1.start_review(uuid4())
        v1.approve()
        v1.publish()

        # Create child version
        v2 = v1.create_child_version()
        v2.update_content({"version": 2})

        # Publish new version
        v2.submit_for_review()
        v2.start_review(uuid4())
        v2.approve()
        v2.publish()

        # Supersede old version
        v1.supersede()

        assert v1.status == VersionStatus.SUPERSEDED
        assert v1.is_current is False
        assert v2.status == VersionStatus.PUBLISHED
        assert v2.is_current is True

    def test_branch_and_merge_workflow(self):
        """Tests branching and merging workflow."""
        entity_id = uuid4()

        # Create main branch
        main_branch = VersionBranch(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=entity_id,
            name="main",
            is_default=True
        )

        # Create feature branch
        feature_branch = VersionBranch(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=entity_id,
            name="feature-new-content",
            parent_branch_id=main_branch.id
        )

        assert feature_branch.is_active is True
        assert feature_branch.parent_branch_name == "main"

        # Simulate merge
        merge = VersionMerge(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=entity_id,
            source_branch_id=feature_branch.id,
            source_version_id=uuid4(),
            target_branch_id=main_branch.id,
            target_version_id=uuid4()
        )

        result_version_id = uuid4()
        merge.complete(result_version_id)
        feature_branch.mark_merged(main_branch.id, result_version_id)

        assert merge.is_complete is True
        assert feature_branch.is_active is False
        assert feature_branch.merged_to_branch_id == main_branch.id

    def test_approval_workflow_with_changes(self):
        """Tests approval workflow with change requests."""
        version_id = uuid4()

        approval = VersionApproval(
            id=uuid4(),
            version_id=version_id,
            reviewer_id=uuid4()
        )

        # Request changes
        changes = [
            {"field": "title", "suggestion": "More descriptive", "priority": "required"},
            {"field": "objectives", "suggestion": "Add more detail", "priority": "optional"}
        ]
        approval.request_changes(changes, "Please address the required changes")

        assert approval.status == ApprovalStatus.CHANGES_REQUESTED
        assert len(approval.requested_changes) == 2

        # After changes are made to the version, reviewer approves
        approval.approve("Changes look good")
        assert approval.status == ApprovalStatus.APPROVED


class TestContentLockConcurrency:
    """Tests for content lock behavior."""

    def test_lock_prevents_concurrent_edit(self):
        """Tests that lock indicates content is locked."""
        user1 = uuid4()
        user2 = uuid4()

        lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.LESSON,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=user1,
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )

        # Lock is active for user1
        assert lock.is_active is True
        assert not lock.is_expired()

        # Another user would need to check lock
        assert lock.locked_by != user2

    def test_expired_lock_allows_new_lock(self):
        """Tests that expired lock doesn't block."""
        old_lock = ContentLock(
            id=uuid4(),
            entity_type=ContentEntityType.LESSON,
            entity_id=uuid4(),
            version_id=uuid4(),
            locked_by=uuid4(),
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )

        assert old_lock.is_expired() is True


class TestVersionDiffAnalysis:
    """Tests for version diff analysis capabilities."""

    def test_multiple_field_changes(self):
        """Tests diff with multiple field changes."""
        diff = VersionDiff(
            id=uuid4(),
            entity_type=ContentEntityType.COURSE,
            entity_id=uuid4(),
            source_version_id=uuid4(),
            target_version_id=uuid4()
        )

        # Add various changes
        diff.add_change("title", ChangeType.UPDATED, "Old Title", "New Title")
        diff.add_change("description", ChangeType.CREATED, None, "New description")
        diff.add_change("old_field", ChangeType.DELETED, "Old value", None)
        diff.add_change("metadata.author", ChangeType.UPDATED, "Author 1", "Author 2")

        assert diff.total_changes == 4
        assert diff.fields_added == 1
        assert diff.fields_modified == 2
        assert diff.fields_deleted == 1

    def test_diff_change_structure(self):
        """Tests that changes have correct structure."""
        diff = VersionDiff(
            id=uuid4(),
            entity_type=ContentEntityType.LESSON,
            entity_id=uuid4(),
            source_version_id=uuid4(),
            target_version_id=uuid4()
        )

        diff.add_change("content.body", ChangeType.UPDATED, "old", "new")

        change = diff.changes[0]
        assert "field" in change
        assert "change_type" in change
        assert "old_value" in change
        assert "new_value" in change
        assert change["field"] == "content.body"
        assert change["change_type"] == "updated"
