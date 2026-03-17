"""
Bug Tracking Job Domain Entity

BUSINESS CONTEXT:
Manages async job processing for bug analysis, fix generation,
and email notifications using asyncio-based queue.

TECHNICAL CONTEXT:
- Follows existing job_management_service.py pattern from course-generator
- Supports priority-based processing
- Includes retry logic for transient failures
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class JobType(Enum):
    """
    Type of bug tracking job.

    ANALYZE: Claude analyzes the bug report
    FIX: Generate and apply fix
    NOTIFY: Send email notification
    """
    ANALYZE = "analyze"
    FIX = "fix"
    NOTIFY = "notify"


class JobStatus(Enum):
    """
    Job processing status.

    QUEUED: Waiting to be processed
    PROCESSING: Currently being processed
    COMPLETED: Successfully finished
    FAILED: Processing failed
    CANCELLED: Cancelled by user/system
    """
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BugTrackingJob:
    """
    Domain entity representing a background job in the bug tracking system.

    Attributes:
        id: Unique job identifier
        bug_report_id: Reference to the bug being processed
        job_type: Type of job (analyze, fix, notify)
        status: Current job status
        priority: Processing priority (1-10, higher = more urgent)
        retry_count: Number of retry attempts
        max_retries: Maximum allowed retries
        error_message: Error message if failed
        worker_id: ID of the worker processing this job
        queued_at: When job was queued
        started_at: When processing started
        completed_at: When job completed

    Example:
        job = BugTrackingJob.create(
            bug_report_id="bug-123",
            job_type=JobType.ANALYZE,
            priority=8  # High priority for critical bug
        )
    """
    id: str
    bug_report_id: str
    job_type: JobType
    status: JobStatus = JobStatus.QUEUED
    priority: int = 5
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    queued_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate job data after initialization."""
        if not 1 <= self.priority <= 10:
            raise ValueError("Priority must be between 1 and 10")

    @classmethod
    def create(
        cls,
        bug_report_id: str,
        job_type: JobType,
        priority: int = 5
    ) -> "BugTrackingJob":
        """
        Factory method to create a new job.

        Args:
            bug_report_id: ID of the bug to process
            job_type: Type of job
            priority: Processing priority (1-10)

        Returns:
            BugTrackingJob: New job in queued status
        """
        return cls(
            id=str(uuid.uuid4()),
            bug_report_id=bug_report_id,
            job_type=job_type,
            priority=priority,
            status=JobStatus.QUEUED
        )

    def start_processing(self, worker_id: str) -> None:
        """
        Mark job as being processed.

        Args:
            worker_id: ID of the worker processing this job
        """
        self.status = JobStatus.PROCESSING
        self.worker_id = worker_id
        self.started_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark job as successfully completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str) -> bool:
        """
        Record job failure and determine if retry is possible.

        Args:
            error_message: Error description

        Returns:
            bool: True if job will be retried, False if max retries reached
        """
        self.error_message = error_message
        self.retry_count += 1

        if self.retry_count >= self.max_retries:
            self.status = JobStatus.FAILED
            self.completed_at = datetime.utcnow()
            return False

        # Reset for retry
        self.status = JobStatus.QUEUED
        self.started_at = None
        self.worker_id = None
        return True

    def cancel(self) -> None:
        """Cancel the job."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries

    def is_complete(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED
        )

    def get_wait_time_seconds(self) -> float:
        """
        Calculate exponential backoff wait time for retry.

        Returns:
            float: Seconds to wait before retry
        """
        if self.retry_count == 0:
            return 0
        # Exponential backoff: 2^retry_count * 10 seconds
        # 1st retry: 20s, 2nd: 40s, 3rd: 80s
        return min(2 ** self.retry_count * 10, 300)  # Max 5 minutes

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "bug_report_id": self.bug_report_id,
            "job_type": self.job_type.value,
            "status": self.status.value,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "worker_id": self.worker_id,
            "queued_at": self.queued_at.isoformat(),
            "started_at": self.started_at.isoformat()
                if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
                if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BugTrackingJob":
        """Create BugTrackingJob from dictionary."""
        return cls(
            id=data["id"],
            bug_report_id=data["bug_report_id"],
            job_type=JobType(data["job_type"]),
            status=JobStatus(data.get("status", "queued")),
            priority=data.get("priority", 5),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error_message=data.get("error_message"),
            worker_id=data.get("worker_id"),
            queued_at=datetime.fromisoformat(data["queued_at"])
                if isinstance(data.get("queued_at"), str)
                else data.get("queued_at", datetime.utcnow()),
            started_at=datetime.fromisoformat(data["started_at"])
                if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at") else None,
        )
