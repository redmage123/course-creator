"""
Bug Fix Attempt Domain Entity

BUSINESS CONTEXT:
Tracks automated fix generation attempts including:
- Branch and PR creation
- Test execution results
- Success/failure status

TECHNICAL CONTEXT:
- Links to BugReport and BugAnalysisResult
- Tracks git operations and GitHub PR lifecycle
- Supports retry logic for failed attempts
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class FixStatus(Enum):
    """
    Fix generation and PR lifecycle status.

    PENDING: Awaiting processing
    GENERATING: Claude is generating fix code
    TESTING: Running automated tests
    TESTS_FAILED: Tests did not pass
    CREATING_PR: Creating GitHub pull request
    PR_CREATED: PR successfully opened
    PR_MERGED: PR was merged (bug resolved)
    PR_CLOSED: PR closed without merge
    FAILED: Fix generation failed
    """
    PENDING = "pending"
    GENERATING = "generating"
    TESTING = "testing"
    TESTS_FAILED = "tests_failed"
    CREATING_PR = "creating_pr"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"
    PR_CLOSED = "pr_closed"
    FAILED = "failed"


@dataclass
class FileChange:
    """
    Represents a single file change in a fix attempt.

    Attributes:
        file_path: Path to the modified file
        change_type: Type of change (add, modify, delete)
        lines_added: Number of lines added
        lines_removed: Number of lines removed
        diff: Actual diff content
    """
    file_path: str
    change_type: str  # 'add', 'modify', 'delete'
    lines_added: int = 0
    lines_removed: int = 0
    diff: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "change_type": self.change_type,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "diff": self.diff
        }


@dataclass
class BugFixAttempt:
    """
    Domain entity representing an automated fix attempt.

    Attributes:
        id: Unique identifier
        bug_report_id: Reference to the bug being fixed
        analysis_id: Reference to the analysis guiding the fix
        status: Current fix status
        branch_name: Git branch for the fix
        pr_number: GitHub PR number
        pr_url: Full URL to the PR
        commit_sha: Git commit SHA
        files_changed: List of FileChange objects
        lines_added: Total lines added
        lines_removed: Total lines removed
        tests_run: Number of tests executed
        tests_passed: Number of tests that passed
        tests_failed: Number of tests that failed
        test_output: Test execution output/logs
        error_message: Error message if failed
        fix_tokens_used: Claude tokens for fix generation
        created_at: Record creation timestamp
        completed_at: When fix attempt completed

    Example:
        fix = BugFixAttempt(
            id=str(uuid.uuid4()),
            bug_report_id="bug-123",
            analysis_id="analysis-456",
            status=FixStatus.PR_CREATED,
            branch_name="bugfix/auto-bug-123",
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42"
        )
    """
    id: str
    bug_report_id: str
    analysis_id: str
    status: FixStatus = FixStatus.PENDING
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    commit_sha: Optional[str] = None
    files_changed: List[FileChange] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    test_output: Optional[str] = None
    error_message: Optional[str] = None
    fix_tokens_used: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        bug_report_id: str,
        analysis_id: str
    ) -> "BugFixAttempt":
        """
        Factory method to create a new fix attempt.

        Args:
            bug_report_id: ID of the bug being fixed
            analysis_id: ID of the guiding analysis

        Returns:
            BugFixAttempt: New fix attempt in pending status
        """
        return cls(
            id=str(uuid.uuid4()),
            bug_report_id=bug_report_id,
            analysis_id=analysis_id,
            status=FixStatus.PENDING
        )

    def update_status(self, new_status: FixStatus) -> None:
        """
        Update fix status.

        Args:
            new_status: New status to set
        """
        self.status = new_status
        if new_status in (
            FixStatus.PR_CREATED,
            FixStatus.PR_MERGED,
            FixStatus.PR_CLOSED,
            FixStatus.FAILED,
            FixStatus.TESTS_FAILED
        ):
            self.completed_at = datetime.utcnow()

    def set_pr_info(
        self,
        branch_name: str,
        pr_number: int,
        pr_url: str,
        commit_sha: str
    ) -> None:
        """
        Set PR information after successful creation.

        Args:
            branch_name: Git branch name
            pr_number: GitHub PR number
            pr_url: Full PR URL
            commit_sha: Git commit SHA
        """
        self.branch_name = branch_name
        self.pr_number = pr_number
        self.pr_url = pr_url
        self.commit_sha = commit_sha
        self.status = FixStatus.PR_CREATED
        self.completed_at = datetime.utcnow()

    def set_test_results(
        self,
        tests_run: int,
        tests_passed: int,
        tests_failed: int,
        test_output: str
    ) -> None:
        """
        Record test execution results.

        Args:
            tests_run: Total tests executed
            tests_passed: Passing tests
            tests_failed: Failing tests
            test_output: Test output/logs
        """
        self.tests_run = tests_run
        self.tests_passed = tests_passed
        self.tests_failed = tests_failed
        self.test_output = test_output

        if tests_failed > 0:
            self.status = FixStatus.TESTS_FAILED

    def set_error(self, error_message: str) -> None:
        """
        Record fix failure.

        Args:
            error_message: Error description
        """
        self.error_message = error_message
        self.status = FixStatus.FAILED
        self.completed_at = datetime.utcnow()

    def add_file_change(self, file_change: FileChange) -> None:
        """
        Add a file change to the fix.

        Args:
            file_change: FileChange object to add
        """
        self.files_changed.append(file_change)
        self.lines_added += file_change.lines_added
        self.lines_removed += file_change.lines_removed

    def is_successful(self) -> bool:
        """Check if fix was successfully created as PR."""
        return self.status in (FixStatus.PR_CREATED, FixStatus.PR_MERGED)

    def is_complete(self) -> bool:
        """Check if fix attempt is complete (success or failure)."""
        return self.status in (
            FixStatus.PR_CREATED,
            FixStatus.PR_MERGED,
            FixStatus.PR_CLOSED,
            FixStatus.FAILED,
            FixStatus.TESTS_FAILED
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "bug_report_id": self.bug_report_id,
            "analysis_id": self.analysis_id,
            "status": self.status.value,
            "branch_name": self.branch_name,
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "commit_sha": self.commit_sha,
            "files_changed": [f.to_dict() for f in self.files_changed],
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "test_output": self.test_output,
            "error_message": self.error_message,
            "fix_tokens_used": self.fix_tokens_used,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
                if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BugFixAttempt":
        """Create BugFixAttempt from dictionary."""
        files_changed = [
            FileChange(**f) for f in data.get("files_changed", [])
        ]

        return cls(
            id=data["id"],
            bug_report_id=data["bug_report_id"],
            analysis_id=data["analysis_id"],
            status=FixStatus(data.get("status", "pending")),
            branch_name=data.get("branch_name"),
            pr_number=data.get("pr_number"),
            pr_url=data.get("pr_url"),
            commit_sha=data.get("commit_sha"),
            files_changed=files_changed,
            lines_added=data.get("lines_added", 0),
            lines_removed=data.get("lines_removed", 0),
            tests_run=data.get("tests_run", 0),
            tests_passed=data.get("tests_passed", 0),
            tests_failed=data.get("tests_failed", 0),
            test_output=data.get("test_output"),
            error_message=data.get("error_message"),
            fix_tokens_used=data.get("fix_tokens_used", 0),
            created_at=datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else data.get("created_at", datetime.utcnow()),
            completed_at=datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at") else None,
        )
