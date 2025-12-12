"""
Bug Tracking Domain Entities Unit Tests

BUSINESS CONTEXT:
Tests for bug tracking domain entities to ensure correct
entity creation, validation, and serialization.

TECHNICAL IMPLEMENTATION:
Tests BugReport, BugAnalysisResult, BugFixAttempt, and BugTrackingJob entities.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/bug-tracking'))

from bug_tracking.domain.entities.bug_report import (
    BugReport, BugSeverity, BugStatus
)
from bug_tracking.domain.entities.bug_analysis import (
    BugAnalysisResult, ComplexityEstimate
)
from bug_tracking.domain.entities.bug_fix import (
    BugFixAttempt, FixStatus, FileChange
)
from bug_tracking.domain.entities.bug_job import (
    BugTrackingJob, JobType, JobStatus
)


class TestBugReport:
    """Tests for BugReport entity."""

    def test_create_bug_report_success(self):
        """Test creating a valid bug report."""
        bug = BugReport.create(
            title="Login button not working",
            description="When I click the login button, nothing happens.",
            submitter_email="test@example.com"
        )

        assert bug.id is not None
        assert bug.title == "Login button not working"
        assert bug.description == "When I click the login button, nothing happens."
        assert bug.submitter_email == "test@example.com"
        assert bug.severity == BugSeverity.MEDIUM
        assert bug.status == BugStatus.SUBMITTED
        assert bug.created_at is not None
        assert bug.updated_at is not None

    def test_create_bug_report_with_severity(self):
        """Test creating a bug report with custom severity."""
        bug = BugReport.create(
            title="Critical security vulnerability",
            description="SQL injection in login form allows unauthorized access.",
            submitter_email="security@example.com",
            severity=BugSeverity.CRITICAL
        )

        assert bug.severity == BugSeverity.CRITICAL

    def test_create_bug_report_with_all_fields(self):
        """Test creating a bug report with all optional fields."""
        bug = BugReport.create(
            title="Form validation error",
            description="Email validation accepts invalid formats.",
            submitter_email="test@example.com",
            severity=BugSeverity.HIGH,
            steps_to_reproduce="1. Go to register\n2. Enter invalid email",
            expected_behavior="Show error message",
            actual_behavior="Form submits successfully",
            affected_component="authentication",
            browser_info="Chrome 120"
        )

        assert bug.steps_to_reproduce == "1. Go to register\n2. Enter invalid email"
        assert bug.expected_behavior == "Show error message"
        assert bug.actual_behavior == "Form submits successfully"
        assert bug.affected_component == "authentication"
        assert bug.browser_info == "Chrome 120"

    def test_bug_report_title_validation_too_short(self):
        """Test that short titles are rejected."""
        with pytest.raises(ValueError, match="Title must be at least 10 characters"):
            BugReport.create(
                title="Short",
                description="This is a valid description for the bug report.",
                submitter_email="test@example.com"
            )

    def test_bug_report_description_validation_too_short(self):
        """Test that short descriptions are rejected."""
        with pytest.raises(ValueError, match="Description must be at least 20 characters"):
            BugReport.create(
                title="Valid bug report title",
                description="Too short",
                submitter_email="test@example.com"
            )

    def test_bug_report_email_validation(self):
        """Test that invalid emails are rejected."""
        with pytest.raises(ValueError, match="Invalid email address"):
            BugReport.create(
                title="Valid bug report title",
                description="This is a valid description for the bug report.",
                submitter_email="invalid-email"
            )

    def test_bug_report_update_status(self):
        """Test updating bug status."""
        bug = BugReport.create(
            title="Valid bug report title",
            description="This is a valid description for the bug report.",
            submitter_email="test@example.com"
        )

        original_updated_at = bug.updated_at
        bug.update_status(BugStatus.ANALYZING)

        assert bug.status == BugStatus.ANALYZING
        assert bug.updated_at >= original_updated_at

    def test_bug_report_to_dict(self):
        """Test serialization to dictionary."""
        bug = BugReport.create(
            title="Serialization test bug",
            description="Testing serialization to dictionary format.",
            submitter_email="test@example.com"
        )

        bug_dict = bug.to_dict()

        assert bug_dict["id"] == bug.id
        assert bug_dict["title"] == "Serialization test bug"
        assert bug_dict["severity"] == "medium"
        assert bug_dict["status"] == "submitted"
        assert "created_at" in bug_dict
        assert "updated_at" in bug_dict


class TestBugAnalysisResult:
    """Tests for BugAnalysisResult entity."""

    def test_create_analysis_result_success(self):
        """Test creating a valid analysis result."""
        analysis = BugAnalysisResult.create(
            bug_report_id=str(uuid4()),
            root_cause_analysis="The issue is caused by a race condition in the authentication flow.",
            suggested_fix="Add mutex lock around the auth token refresh.",
            affected_files=["services/auth/token_service.py"],
            confidence_score=85.5,
            complexity_estimate=ComplexityEstimate.MODERATE,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=1500
        )

        assert analysis.id is not None
        assert analysis.root_cause_analysis.startswith("The issue is caused")
        assert len(analysis.affected_files) == 1
        assert analysis.confidence_score == 85.5
        assert analysis.complexity_estimate == ComplexityEstimate.MODERATE

    def test_analysis_is_safe_to_autofix_high_confidence_simple(self):
        """Test that simple bugs with high confidence are safe to autofix."""
        analysis = BugAnalysisResult.create(
            bug_report_id=str(uuid4()),
            root_cause_analysis="Typo in variable name.",
            suggested_fix="Rename variable from 'usre' to 'user'.",
            affected_files=["frontend/components/Login.tsx"],
            confidence_score=95.0,
            complexity_estimate=ComplexityEstimate.TRIVIAL,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=500
        )

        assert analysis.is_safe_to_autofix() is True

    def test_analysis_not_safe_to_autofix_low_confidence(self):
        """Test that low confidence bugs are not safe to autofix."""
        analysis = BugAnalysisResult.create(
            bug_report_id=str(uuid4()),
            root_cause_analysis="Possible issue with state management.",
            suggested_fix="Consider refactoring the Redux store.",
            affected_files=["frontend/store/auth.ts"],
            confidence_score=60.0,
            complexity_estimate=ComplexityEstimate.SIMPLE,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=800
        )

        assert analysis.is_safe_to_autofix() is False

    def test_analysis_not_safe_to_autofix_complex(self):
        """Test that complex bugs are not safe to autofix."""
        analysis = BugAnalysisResult.create(
            bug_report_id=str(uuid4()),
            root_cause_analysis="Architectural issue in the microservice communication.",
            suggested_fix="Redesign the message queue infrastructure.",
            affected_files=["services/api-gateway/routes.py", "services/auth/handler.py"],
            confidence_score=90.0,
            complexity_estimate=ComplexityEstimate.VERY_COMPLEX,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=3000
        )

        assert analysis.is_safe_to_autofix() is False

    def test_analysis_to_dict(self):
        """Test serialization to dictionary."""
        analysis = BugAnalysisResult.create(
            bug_report_id=str(uuid4()),
            root_cause_analysis="Test root cause.",
            suggested_fix="Test fix.",
            affected_files=["file1.py", "file2.py"],
            confidence_score=75.0,
            complexity_estimate=ComplexityEstimate.MODERATE,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=1000
        )

        analysis_dict = analysis.to_dict()

        assert analysis_dict["confidence_score"] == 75.0
        assert analysis_dict["complexity_estimate"] == "moderate"
        assert len(analysis_dict["affected_files"]) == 2


class TestBugFixAttempt:
    """Tests for BugFixAttempt entity."""

    def test_create_fix_attempt_success(self):
        """Test creating a valid fix attempt."""
        fix = BugFixAttempt.create(
            bug_report_id=str(uuid4()),
            analysis_id=str(uuid4())
        )

        assert fix.id is not None
        assert fix.status == FixStatus.PENDING
        assert fix.pr_number is None
        assert fix.pr_url is None

    def test_fix_attempt_start_progress(self):
        """Test starting fix generation."""
        fix = BugFixAttempt.create(
            bug_report_id=str(uuid4()),
            analysis_id=str(uuid4())
        )

        fix.start_progress("bugfix/auto-abc123")

        assert fix.status == FixStatus.IN_PROGRESS
        assert fix.branch_name == "bugfix/auto-abc123"

    def test_fix_attempt_complete_with_pr(self):
        """Test completing fix with PR."""
        fix = BugFixAttempt.create(
            bug_report_id=str(uuid4()),
            analysis_id=str(uuid4())
        )

        file_changes = [
            FileChange(
                file_path="services/auth/login.py",
                change_type="modify",
                diff="- old_code\n+ new_code",
                description="Fixed login validation"
            )
        ]

        fix.complete_with_pr(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            files_changed=file_changes,
            lines_added=10,
            lines_removed=5,
            tests_passed=25,
            tests_failed=0
        )

        assert fix.status == FixStatus.PR_CREATED
        assert fix.pr_number == 123
        assert fix.pr_url == "https://github.com/owner/repo/pull/123"
        assert len(fix.files_changed) == 1
        assert fix.lines_added == 10
        assert fix.tests_passed == 25
        assert fix.completed_at is not None

    def test_fix_attempt_complete_with_error(self):
        """Test completing fix with error."""
        fix = BugFixAttempt.create(
            bug_report_id=str(uuid4()),
            analysis_id=str(uuid4())
        )

        fix.complete_with_error("Tests failed after applying fix")

        assert fix.status == FixStatus.FAILED
        assert fix.error_message == "Tests failed after applying fix"
        assert fix.completed_at is not None


class TestBugTrackingJob:
    """Tests for BugTrackingJob entity."""

    def test_create_job_success(self):
        """Test creating a valid job."""
        job = BugTrackingJob.create(
            bug_report_id=str(uuid4()),
            job_type=JobType.ANALYZE
        )

        assert job.id is not None
        assert job.job_type == JobType.ANALYZE
        assert job.status == JobStatus.PENDING
        assert job.retry_count == 0
        assert job.max_retries == 3

    def test_job_start(self):
        """Test starting a job."""
        job = BugTrackingJob.create(
            bug_report_id=str(uuid4()),
            job_type=JobType.ANALYZE
        )

        job.start()

        assert job.status == JobStatus.PROCESSING
        assert job.started_at is not None

    def test_job_complete(self):
        """Test completing a job."""
        job = BugTrackingJob.create(
            bug_report_id=str(uuid4()),
            job_type=JobType.ANALYZE
        )

        job.start()
        job.complete("Analysis completed successfully")

        assert job.status == JobStatus.COMPLETED
        assert job.result_message == "Analysis completed successfully"
        assert job.completed_at is not None

    def test_job_fail_with_retry(self):
        """Test job failure with retry available."""
        job = BugTrackingJob.create(
            bug_report_id=str(uuid4()),
            job_type=JobType.ANALYZE
        )

        job.start()
        job.fail("Temporary API error")

        assert job.status == JobStatus.RETRY_PENDING
        assert job.retry_count == 1
        assert job.can_retry() is True

    def test_job_fail_no_retry(self):
        """Test job failure with no retries left."""
        job = BugTrackingJob.create(
            bug_report_id=str(uuid4()),
            job_type=JobType.ANALYZE,
            max_retries=0
        )

        job.start()
        job.fail("Permanent error")

        assert job.status == JobStatus.FAILED
        assert job.can_retry() is False

    def test_job_retry_backoff(self):
        """Test exponential backoff calculation."""
        job = BugTrackingJob.create(
            bug_report_id=str(uuid4()),
            job_type=JobType.ANALYZE
        )

        # First failure
        job.start()
        job.fail("Error 1")
        backoff_1 = job.get_retry_backoff_seconds()

        # Second failure
        job.start()
        job.fail("Error 2")
        backoff_2 = job.get_retry_backoff_seconds()

        # Backoff should increase exponentially
        assert backoff_2 > backoff_1


class TestBugSeverityEnum:
    """Tests for BugSeverity enum."""

    def test_severity_values(self):
        """Test all severity values exist."""
        assert BugSeverity.LOW.value == "low"
        assert BugSeverity.MEDIUM.value == "medium"
        assert BugSeverity.HIGH.value == "high"
        assert BugSeverity.CRITICAL.value == "critical"


class TestBugStatusEnum:
    """Tests for BugStatus enum."""

    def test_status_values(self):
        """Test all status values exist."""
        assert BugStatus.SUBMITTED.value == "submitted"
        assert BugStatus.ANALYZING.value == "analyzing"
        assert BugStatus.ANALYSIS_COMPLETE.value == "analysis_complete"
        assert BugStatus.FIXING.value == "fixing"
        assert BugStatus.FIX_READY.value == "fix_ready"
        assert BugStatus.PR_OPENED.value == "pr_opened"
        assert BugStatus.RESOLVED.value == "resolved"
        assert BugStatus.CLOSED.value == "closed"
        assert BugStatus.WONT_FIX.value == "wont_fix"


class TestComplexityEstimateEnum:
    """Tests for ComplexityEstimate enum."""

    def test_complexity_values(self):
        """Test all complexity values exist."""
        assert ComplexityEstimate.TRIVIAL.value == "trivial"
        assert ComplexityEstimate.SIMPLE.value == "simple"
        assert ComplexityEstimate.MODERATE.value == "moderate"
        assert ComplexityEstimate.COMPLEX.value == "complex"
        assert ComplexityEstimate.VERY_COMPLEX.value == "very_complex"
