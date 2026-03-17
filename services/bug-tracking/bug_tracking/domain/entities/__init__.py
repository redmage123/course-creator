"""
Bug Tracking Domain Entities

Core domain entities for the bug tracking system:
- BugReport: User-submitted bug reports
- BugAnalysisResult: Claude AI analysis results
- BugFixAttempt: Automated fix attempts and PR tracking
- BugTrackingJob: Background job management
"""

from bug_tracking.domain.entities.bug_report import (
    BugReport,
    BugSeverity,
    BugStatus,
)
from bug_tracking.domain.entities.bug_analysis import (
    BugAnalysisResult,
    ComplexityEstimate,
)
from bug_tracking.domain.entities.bug_fix import (
    BugFixAttempt,
    FixStatus,
)
from bug_tracking.domain.entities.bug_job import (
    BugTrackingJob,
    JobType,
    JobStatus,
)

__all__ = [
    "BugReport",
    "BugSeverity",
    "BugStatus",
    "BugAnalysisResult",
    "ComplexityEstimate",
    "BugFixAttempt",
    "FixStatus",
    "BugTrackingJob",
    "JobType",
    "JobStatus",
]
