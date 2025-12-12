"""
Bug Report Domain Entity

BUSINESS CONTEXT:
Represents a user-submitted bug report with all context needed for
automated analysis and fix generation using Claude AI.

SECURITY CONTEXT:
- submitter_email required for notification delivery
- submitter_user_id links to authenticated users (optional)
- May contain sensitive data subject to GDPR/privacy policies

TECHNICAL CONTEXT:
- Uses dataclasses for clean domain modeling
- Enum types ensure data integrity
- Optional fields support minimal and detailed submissions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class BugSeverity(Enum):
    """
    Bug severity classification.

    LOW: Minor cosmetic issues, no functional impact
    MEDIUM: Functional issues with workarounds available
    HIGH: Significant functional issues affecting user experience
    CRITICAL: System-breaking issues requiring immediate attention
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BugStatus(Enum):
    """
    Bug processing status tracking.

    Represents the lifecycle of a bug from submission through resolution:
    1. SUBMITTED -> ANALYZING (Claude starts analysis)
    2. ANALYZING -> ANALYSIS_COMPLETE or ANALYSIS_FAILED
    3. ANALYSIS_COMPLETE -> FIXING (generating fix)
    4. FIXING -> FIX_READY or fix failed
    5. FIX_READY -> PR_OPENED
    6. PR_OPENED -> RESOLVED (after merge) or CLOSED
    """
    SUBMITTED = "submitted"
    ANALYZING = "analyzing"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_FAILED = "analysis_failed"
    FIXING = "fixing"
    FIX_READY = "fix_ready"
    PR_OPENED = "pr_opened"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WONT_FIX = "wont_fix"


@dataclass
class BugReport:
    """
    Domain entity representing a user-submitted bug report.

    Attributes:
        id: Unique identifier (UUID)
        title: Brief bug title (10-255 chars)
        description: Detailed bug description (min 20 chars)
        submitter_email: Email for notifications (required)
        severity: Bug severity classification
        status: Current processing status
        steps_to_reproduce: Step-by-step reproduction instructions
        expected_behavior: What should happen
        actual_behavior: What actually happens
        affected_component: Service/module affected (e.g., 'course-management')
        browser_info: User agent string for frontend bugs
        error_logs: Any error logs or stack traces
        screenshot_urls: List of uploaded screenshot URLs
        submitter_user_id: Authenticated user ID (optional)
        created_at: Submission timestamp
        updated_at: Last update timestamp

    Example:
        bug = BugReport(
            id=str(uuid.uuid4()),
            title="Login button not responding on Safari",
            description="When clicking the login button on Safari 17.0...",
            submitter_email="user@example.com",
            severity=BugSeverity.HIGH,
            affected_component="frontend-react",
            browser_info="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
        )
    """
    id: str
    title: str
    description: str
    submitter_email: str
    severity: BugSeverity = BugSeverity.MEDIUM
    status: BugStatus = BugStatus.SUBMITTED
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    affected_component: Optional[str] = None
    browser_info: Optional[str] = None
    error_logs: Optional[str] = None
    screenshot_urls: List[str] = field(default_factory=list)
    submitter_user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate bug report data after initialization."""
        if len(self.title) < 10:
            raise ValueError("Bug title must be at least 10 characters")
        if len(self.description) < 20:
            raise ValueError("Bug description must be at least 20 characters")
        if "@" not in self.submitter_email:
            raise ValueError("Invalid submitter email address")

    @classmethod
    def create(
        cls,
        title: str,
        description: str,
        submitter_email: str,
        severity: str = "medium",
        **kwargs
    ) -> "BugReport":
        """
        Factory method to create a new BugReport.

        Args:
            title: Bug title
            description: Bug description
            submitter_email: Submitter's email
            severity: Severity string ('low', 'medium', 'high', 'critical')
            **kwargs: Additional optional fields

        Returns:
            BugReport: New bug report instance
        """
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            submitter_email=submitter_email,
            severity=BugSeverity(severity),
            status=BugStatus.SUBMITTED,
            **kwargs
        )

    def update_status(self, new_status: BugStatus) -> None:
        """
        Update bug status with timestamp.

        Args:
            new_status: New status to set
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def is_actionable(self) -> bool:
        """Check if bug can be processed (not closed/resolved)."""
        return self.status not in (
            BugStatus.RESOLVED,
            BugStatus.CLOSED,
            BugStatus.WONT_FIX
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "submitter_email": self.submitter_email,
            "severity": self.severity.value,
            "status": self.status.value,
            "steps_to_reproduce": self.steps_to_reproduce,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "affected_component": self.affected_component,
            "browser_info": self.browser_info,
            "error_logs": self.error_logs,
            "screenshot_urls": self.screenshot_urls,
            "submitter_user_id": self.submitter_user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BugReport":
        """Create BugReport from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            submitter_email=data["submitter_email"],
            severity=BugSeverity(data.get("severity", "medium")),
            status=BugStatus(data.get("status", "submitted")),
            steps_to_reproduce=data.get("steps_to_reproduce"),
            expected_behavior=data.get("expected_behavior"),
            actual_behavior=data.get("actual_behavior"),
            affected_component=data.get("affected_component"),
            browser_info=data.get("browser_info"),
            error_logs=data.get("error_logs"),
            screenshot_urls=data.get("screenshot_urls", []),
            submitter_user_id=data.get("submitter_user_id"),
            created_at=datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else data.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(data["updated_at"])
                if isinstance(data.get("updated_at"), str)
                else data.get("updated_at", datetime.utcnow()),
        )
