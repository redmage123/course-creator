"""
Bug Tracking Pydantic Models

BUSINESS CONTEXT:
API request/response models for bug tracking endpoints.
Provides validation, serialization, and documentation.

TECHNICAL CONTEXT:
- Uses Pydantic v2 for validation
- EmailStr validates email format
- Field constraints enforce data quality
- Enums ensure type safety
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BugSeverityEnum(str, Enum):
    """Bug severity classification for API."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class BugStatusEnum(str, Enum):
    """Bug processing status for API."""
    submitted = "submitted"
    analyzing = "analyzing"
    analysis_complete = "analysis_complete"
    analysis_failed = "analysis_failed"
    fixing = "fixing"
    fix_ready = "fix_ready"
    pr_opened = "pr_opened"
    resolved = "resolved"
    closed = "closed"
    wont_fix = "wont_fix"


class FixStatusEnum(str, Enum):
    """Fix attempt status for API."""
    pending = "pending"
    generating = "generating"
    testing = "testing"
    tests_failed = "tests_failed"
    creating_pr = "creating_pr"
    pr_created = "pr_created"
    pr_merged = "pr_merged"
    pr_closed = "pr_closed"
    failed = "failed"


# Request Models

class BugSubmissionRequest(BaseModel):
    """
    Request model for submitting a new bug report.

    Attributes:
        title: Brief bug title (10-255 chars)
        description: Detailed description (min 20 chars)
        submitter_email: Email for notifications
        steps_to_reproduce: Steps to reproduce the bug
        expected_behavior: Expected behavior
        actual_behavior: Actual behavior observed
        severity: Bug severity level
        affected_component: Service/module affected
        browser_info: Browser/device info for frontend bugs
        error_logs: Any error logs or stack traces

    Example:
        {
            "title": "Login fails on Safari browser",
            "description": "When attempting to login using Safari 17.0...",
            "submitter_email": "user@example.com",
            "severity": "high",
            "affected_component": "frontend-react"
        }
    """
    title: str = Field(
        ...,
        min_length=10,
        max_length=255,
        description="Brief bug title",
        examples=["Login button not responding on Safari"]
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Detailed bug description",
        examples=["When clicking the login button on Safari 17.0, nothing happens..."]
    )
    submitter_email: EmailStr = Field(
        ...,
        description="Email address for notifications",
        examples=["user@example.com"]
    )
    steps_to_reproduce: Optional[str] = Field(
        None,
        description="Step-by-step reproduction instructions",
        examples=["1. Open login page\n2. Enter credentials\n3. Click login button"]
    )
    expected_behavior: Optional[str] = Field(
        None,
        description="Expected behavior",
        examples=["User should be redirected to dashboard"]
    )
    actual_behavior: Optional[str] = Field(
        None,
        description="Actual behavior observed",
        examples=["Nothing happens, button appears to freeze"]
    )
    severity: BugSeverityEnum = Field(
        BugSeverityEnum.medium,
        description="Bug severity level"
    )
    affected_component: Optional[str] = Field(
        None,
        description="Service or module affected",
        examples=["frontend-react", "user-management", "course-generator"]
    )
    browser_info: Optional[str] = Field(
        None,
        description="Browser/device information for frontend bugs",
        examples=["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."]
    )
    error_logs: Optional[str] = Field(
        None,
        description="Error logs or stack traces"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Login button not responding on Safari",
                "description": "When clicking the login button on Safari 17.0 on macOS Sonoma, the button doesn't respond. No network requests are made and no errors appear in console.",
                "submitter_email": "user@example.com",
                "steps_to_reproduce": "1. Open https://example.com/login\n2. Enter valid credentials\n3. Click the Login button",
                "expected_behavior": "User should be logged in and redirected to dashboard",
                "actual_behavior": "Nothing happens, button appears frozen",
                "severity": "high",
                "affected_component": "frontend-react",
                "browser_info": "Safari 17.0 on macOS 14.0"
            }
        }
    )


class BugUpdateRequest(BaseModel):
    """Request model for updating a bug report."""
    severity: Optional[BugSeverityEnum] = None
    status: Optional[BugStatusEnum] = None
    affected_component: Optional[str] = None


# Response Models

class BugReportResponse(BaseModel):
    """
    Response model for bug report summary.

    Used in list views and after submission.
    """
    id: str = Field(..., description="Bug report ID")
    title: str = Field(..., description="Bug title")
    status: BugStatusEnum = Field(..., description="Current status")
    severity: BugSeverityEnum = Field(..., description="Severity level")
    affected_component: Optional[str] = Field(None, description="Affected component")
    created_at: datetime = Field(..., description="Submission time")
    updated_at: datetime = Field(..., description="Last update time")

    model_config = ConfigDict(from_attributes=True)


class BugAnalysisResponse(BaseModel):
    """
    Response model for bug analysis results.

    Returned when analysis is complete.
    """
    id: str = Field(..., description="Analysis ID")
    bug_report_id: str = Field(..., description="Bug report ID")
    root_cause_analysis: str = Field(..., description="Root cause explanation")
    suggested_fix: str = Field(..., description="Recommended fix approach")
    affected_files: List[str] = Field(..., description="Files to modify")
    confidence_score: float = Field(..., description="Analysis confidence (0-100)")
    complexity_estimate: str = Field(..., description="Fix complexity estimate")
    claude_model_used: str = Field(..., description="Claude model used")
    tokens_used: int = Field(..., description="Tokens consumed")
    analysis_completed_at: Optional[datetime] = Field(None, description="Completion time")

    model_config = ConfigDict(from_attributes=True)


class FileChangeResponse(BaseModel):
    """Response model for a single file change."""
    file_path: str
    change_type: str
    lines_added: int
    lines_removed: int


class BugFixResponse(BaseModel):
    """
    Response model for bug fix attempt.

    Returned when fix is attempted or PR is created.
    """
    id: str = Field(..., description="Fix attempt ID")
    bug_report_id: str = Field(..., description="Bug report ID")
    status: FixStatusEnum = Field(..., description="Fix status")
    branch_name: Optional[str] = Field(None, description="Git branch name")
    pr_number: Optional[int] = Field(None, description="PR number")
    pr_url: Optional[str] = Field(None, description="PR URL")
    files_changed: List[FileChangeResponse] = Field(default_factory=list, description="Changed files")
    lines_added: int = Field(0, description="Total lines added")
    lines_removed: int = Field(0, description="Total lines removed")
    tests_passed: int = Field(0, description="Tests passed")
    tests_failed: int = Field(0, description="Tests failed")
    error_message: Optional[str] = Field(None, description="Error if failed")
    created_at: datetime = Field(..., description="Creation time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")

    model_config = ConfigDict(from_attributes=True)


class BugDetailResponse(BaseModel):
    """
    Complete bug detail response with analysis and fix info.

    Used for individual bug detail view.
    """
    id: str
    title: str
    description: str
    submitter_email: str
    status: BugStatusEnum
    severity: BugSeverityEnum
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    affected_component: Optional[str] = None
    browser_info: Optional[str] = None
    error_logs: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    analysis: Optional[BugAnalysisResponse] = None
    fix_attempt: Optional[BugFixResponse] = None

    model_config = ConfigDict(from_attributes=True)


class BugListResponse(BaseModel):
    """
    Response model for paginated bug list.
    """
    bugs: List[BugReportResponse] = Field(..., description="List of bugs")
    total_count: int = Field(..., description="Total number of bugs")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Items per page")
    has_next: bool = Field(False, description="Has next page")
    has_prev: bool = Field(False, description="Has previous page")

    model_config = ConfigDict(from_attributes=True)


class BugSubmissionResponse(BaseModel):
    """
    Response after successful bug submission.
    """
    id: str = Field(..., description="Bug report ID for tracking")
    message: str = Field(..., description="Success message")
    status: BugStatusEnum = Field(..., description="Initial status")
    estimated_analysis_time: str = Field(
        "5-10 minutes",
        description="Estimated time for analysis"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Bug report submitted successfully. You will receive an email when analysis is complete.",
                "status": "submitted",
                "estimated_analysis_time": "5-10 minutes"
            }
        }
    )
