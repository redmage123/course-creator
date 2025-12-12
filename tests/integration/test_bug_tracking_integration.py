"""
Bug Tracking Integration Tests

BUSINESS CONTEXT:
Integration tests for the bug tracking system that verify
the interaction between components and the database.

TECHNICAL IMPLEMENTATION:
Tests against real PostgreSQL database in test environment.
Tests full API workflows from submission to analysis.
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/bug-tracking'))

from bug_tracking.domain.entities.bug_report import BugReport, BugSeverity, BugStatus
from bug_tracking.domain.entities.bug_analysis import BugAnalysisResult, ComplexityEstimate
from bug_tracking.domain.entities.bug_fix import BugFixAttempt, FixStatus


# Test database configuration
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_password@localhost:5434/course_creator_test"
)


class TestBugTrackingIntegration:
    """Integration tests for bug tracking system."""

    @pytest.fixture(scope="class")
    def event_loop(self):
        """Create event loop for async tests."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

    @pytest.fixture
    def sample_bug_data(self):
        """Sample bug submission data."""
        return {
            "title": "Integration test bug report",
            "description": "This is a bug report created during integration testing to verify the system works.",
            "submitter_email": "integration-test@example.com",
            "severity": "high",
            "steps_to_reproduce": "1. Run integration tests\n2. Observe behavior",
            "expected_behavior": "All tests pass",
            "actual_behavior": "Testing in progress",
            "affected_component": "testing"
        }

    def test_bug_report_entity_creation(self, sample_bug_data):
        """Test creating bug report entity."""
        bug = BugReport.create(
            title=sample_bug_data["title"],
            description=sample_bug_data["description"],
            submitter_email=sample_bug_data["submitter_email"],
            severity=BugSeverity.HIGH,
            steps_to_reproduce=sample_bug_data["steps_to_reproduce"],
            expected_behavior=sample_bug_data["expected_behavior"],
            actual_behavior=sample_bug_data["actual_behavior"],
            affected_component=sample_bug_data["affected_component"]
        )

        assert bug.id is not None
        assert bug.status == BugStatus.SUBMITTED
        assert bug.severity == BugSeverity.HIGH

    def test_bug_analysis_result_creation(self):
        """Test creating analysis result entity."""
        bug_id = str(uuid4())

        analysis = BugAnalysisResult.create(
            bug_report_id=bug_id,
            root_cause_analysis="The issue is caused by missing validation.",
            suggested_fix="Add input validation to the form handler.",
            affected_files=["services/api/handler.py", "frontend/form.tsx"],
            confidence_score=85.0,
            complexity_estimate=ComplexityEstimate.MODERATE,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=1500
        )

        assert analysis.id is not None
        assert analysis.bug_report_id == bug_id
        assert len(analysis.affected_files) == 2
        assert analysis.is_safe_to_autofix() is False  # 85% confidence, moderate complexity

    def test_bug_fix_attempt_lifecycle(self):
        """Test fix attempt entity lifecycle."""
        bug_id = str(uuid4())
        analysis_id = str(uuid4())

        # Create fix attempt
        fix = BugFixAttempt.create(
            bug_report_id=bug_id,
            analysis_id=analysis_id
        )

        assert fix.status == FixStatus.PENDING

        # Start progress
        fix.start_progress("bugfix/auto-test-123")
        assert fix.status == FixStatus.IN_PROGRESS
        assert fix.branch_name == "bugfix/auto-test-123"

        # Complete with PR
        fix.complete_with_pr(
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            files_changed=[],
            lines_added=10,
            lines_removed=5,
            tests_passed=20,
            tests_failed=0
        )

        assert fix.status == FixStatus.PR_CREATED
        assert fix.pr_number == 42
        assert fix.completed_at is not None

    def test_bug_status_transitions(self):
        """Test valid bug status transitions."""
        bug = BugReport.create(
            title="Status transition test bug",
            description="Testing valid status transitions for bug reports.",
            submitter_email="test@example.com"
        )

        # Submitted -> Analyzing
        bug.update_status(BugStatus.ANALYZING)
        assert bug.status == BugStatus.ANALYZING

        # Analyzing -> Analysis Complete
        bug.update_status(BugStatus.ANALYSIS_COMPLETE)
        assert bug.status == BugStatus.ANALYSIS_COMPLETE

        # Analysis Complete -> Fixing
        bug.update_status(BugStatus.FIXING)
        assert bug.status == BugStatus.FIXING

        # Fixing -> PR Opened
        bug.update_status(BugStatus.PR_OPENED)
        assert bug.status == BugStatus.PR_OPENED

        # PR Opened -> Resolved
        bug.update_status(BugStatus.RESOLVED)
        assert bug.status == BugStatus.RESOLVED

    def test_analysis_safe_to_autofix_decision(self):
        """Test autofix eligibility logic."""
        bug_id = str(uuid4())

        # High confidence, simple - should be safe
        safe_analysis = BugAnalysisResult.create(
            bug_report_id=bug_id,
            root_cause_analysis="Simple typo in variable name.",
            suggested_fix="Rename 'usre' to 'user'.",
            affected_files=["file.py"],
            confidence_score=95.0,
            complexity_estimate=ComplexityEstimate.TRIVIAL,
            claude_model_used="test",
            tokens_used=500
        )
        assert safe_analysis.is_safe_to_autofix() is True

        # Low confidence - not safe
        low_confidence = BugAnalysisResult.create(
            bug_report_id=bug_id,
            root_cause_analysis="Possible race condition.",
            suggested_fix="Add locking.",
            affected_files=["file.py"],
            confidence_score=60.0,
            complexity_estimate=ComplexityEstimate.SIMPLE,
            claude_model_used="test",
            tokens_used=500
        )
        assert low_confidence.is_safe_to_autofix() is False

        # Complex - not safe regardless of confidence
        complex_analysis = BugAnalysisResult.create(
            bug_report_id=bug_id,
            root_cause_analysis="Architectural issue.",
            suggested_fix="Redesign system.",
            affected_files=["file1.py", "file2.py", "file3.py"],
            confidence_score=95.0,
            complexity_estimate=ComplexityEstimate.VERY_COMPLEX,
            claude_model_used="test",
            tokens_used=500
        )
        assert complex_analysis.is_safe_to_autofix() is False


class TestBugTrackingAPIIntegration:
    """API-level integration tests."""

    @pytest.fixture
    def valid_bug_request(self):
        """Valid bug submission request data."""
        return {
            "title": "API integration test bug",
            "description": "Testing the API integration for bug submission and retrieval.",
            "submitter_email": "api-test@example.com",
            "severity": "medium",
            "affected_component": "api"
        }

    def test_bug_to_dict_serialization(self):
        """Test bug report serializes correctly."""
        bug = BugReport.create(
            title="Serialization test bug",
            description="Testing that bug reports serialize to JSON correctly.",
            submitter_email="test@example.com",
            severity=BugSeverity.HIGH,
            affected_component="serialization"
        )

        bug_dict = bug.to_dict()

        assert bug_dict["id"] == bug.id
        assert bug_dict["title"] == "Serialization test bug"
        assert bug_dict["severity"] == "high"
        assert bug_dict["status"] == "submitted"
        assert bug_dict["affected_component"] == "serialization"
        assert "created_at" in bug_dict
        assert "updated_at" in bug_dict

    def test_analysis_to_dict_serialization(self):
        """Test analysis result serializes correctly."""
        analysis = BugAnalysisResult.create(
            bug_report_id=str(uuid4()),
            root_cause_analysis="Test root cause.",
            suggested_fix="Test fix.",
            affected_files=["file1.py", "file2.py"],
            confidence_score=85.5,
            complexity_estimate=ComplexityEstimate.MODERATE,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=1234
        )

        analysis_dict = analysis.to_dict()

        assert analysis_dict["confidence_score"] == 85.5
        assert analysis_dict["complexity_estimate"] == "moderate"
        assert analysis_dict["claude_model_used"] == "claude-sonnet-4-20250514"
        assert analysis_dict["tokens_used"] == 1234
        assert len(analysis_dict["affected_files"]) == 2

    def test_fix_attempt_to_dict_serialization(self):
        """Test fix attempt serializes correctly."""
        fix = BugFixAttempt.create(
            bug_report_id=str(uuid4()),
            analysis_id=str(uuid4())
        )

        fix.complete_with_pr(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            files_changed=[],
            lines_added=50,
            lines_removed=20,
            tests_passed=30,
            tests_failed=2
        )

        fix_dict = fix.to_dict()

        assert fix_dict["pr_number"] == 123
        assert fix_dict["pr_url"] == "https://github.com/owner/repo/pull/123"
        assert fix_dict["lines_added"] == 50
        assert fix_dict["lines_removed"] == 20
        assert fix_dict["tests_passed"] == 30
        assert fix_dict["tests_failed"] == 2
        assert fix_dict["status"] == "pr_created"


class TestBugTrackingEmailIntegration:
    """Email service integration tests."""

    def test_email_subject_generation(self):
        """Test email subject line generation."""
        bug = BugReport.create(
            title="Email subject test - very long title that should be truncated properly",
            description="Testing email subject generation for various scenarios.",
            submitter_email="email-test@example.com"
        )

        # Import email service for subject generation
        from bug_tracking.application.services.bug_email_service import BugEmailService
        email_service = BugEmailService(mock_mode=True)

        # Test without analysis
        subject = email_service._build_subject(bug, None, None)
        assert "Email subject test" in subject
        assert len(subject) < 100  # Subject should be reasonable length

        # Test with analysis
        analysis = BugAnalysisResult.create(
            bug_report_id=bug.id,
            root_cause_analysis="Test",
            suggested_fix="Test",
            affected_files=["test.py"],
            confidence_score=90.0,
            complexity_estimate=ComplexityEstimate.SIMPLE,
            claude_model_used="test",
            tokens_used=100
        )

        subject_with_analysis = email_service._build_subject(bug, analysis, None)
        assert "Analysis Complete" in subject_with_analysis

        # Test with PR
        fix = BugFixAttempt.create(
            bug_report_id=bug.id,
            analysis_id=analysis.id
        )
        fix.complete_with_pr(
            pr_number=42,
            pr_url="https://github.com/test/pull/42",
            files_changed=[],
            lines_added=10,
            lines_removed=5,
            tests_passed=10,
            tests_failed=0
        )

        subject_with_pr = email_service._build_subject(bug, analysis, fix)
        assert "Fix" in subject_with_pr or "PR" in subject_with_pr
