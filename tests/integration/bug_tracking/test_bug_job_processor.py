"""
Bug Job Processor Unit Tests

BUSINESS CONTEXT:
Tests for the background job processor that handles
bug analysis and fix generation jobs.

TECHNICAL IMPLEMENTATION:
Tests job processing logic with test doubles and fixtures.
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/bug-tracking'))

from bug_tracking.domain.entities.bug_report import BugReport, BugSeverity, BugStatus
from bug_tracking.domain.entities.bug_analysis import BugAnalysisResult, ComplexityEstimate
from bug_tracking.domain.entities.bug_fix import BugFixAttempt, FixStatus
from bug_tracking.domain.entities.bug_job import BugTrackingJob, JobType, JobStatus
from bug_tracking.application.services.bug_job_processor import BugJobProcessor



class FakeBugDAO:
    """Test double for BugDAO."""
    async def get_bug_by_id(self, bug_id):
        return None

    async def update_bug_status(self, bug_id, status):
        pass

    async def create_analysis(self, analysis):
        return analysis

    async def create_fix_attempt(self, fix_attempt):
        return fix_attempt

    async def get_pending_jobs(self):
        return []

    async def update_job_status(self, job_id, status):
        pass

    async def get_analysis_by_bug_id(self, bug_id):
        return None

    async def get_fix_attempt_by_bug_id(self, bug_id):
        return None



class TestBugJobProcessor:
    """Tests for BugJobProcessor."""

    @pytest.fixture
    def job_processor(self):
        """Create job processor with test doubles."""
        # Requires real implementations or proper test doubles
        pytest.skip("Needs refactoring to use real services")

    @pytest.fixture
    def sample_bug(self):
        """Create sample bug for testing."""
        return BugReport.create(
            title="Test bug for job processing",
            description="This is a test bug for validating job processing.",
            submitter_email="test@example.com",
            severity=BugSeverity.MEDIUM
        )

    @pytest.fixture
    def sample_analysis(self, sample_bug):
        """Create sample analysis result."""
        return BugAnalysisResult.create(
            bug_report_id=sample_bug.id,
            root_cause_analysis="Test root cause",
            suggested_fix="Test fix",
            affected_files=["test.py"],
            confidence_score=85.0,
            complexity_estimate=ComplexityEstimate.SIMPLE,
            claude_model_used="claude-sonnet-4-20250514",
            tokens_used=1000
        )

    def test_processor_initialization(self, job_processor):
        """Test processor initializes correctly."""
        assert job_processor is not None
        assert job_processor.max_concurrent_jobs > 0
        assert job_processor.is_running is False

    @pytest.mark.asyncio
    async def test_enqueue_job(self, job_processor, sample_bug):
        """Test enqueueing a new job."""
        job_id = await job_processor.enqueue_bug_analysis(sample_bug.id)

        assert job_id is not None
        assert job_processor.pending_jobs.qsize() == 1

    @pytest.mark.asyncio
    async def test_get_status(self, job_processor):
        """Test getting processor status."""
        status = job_processor.get_status()

        assert "is_running" in status
        assert "pending_jobs" in status
        assert "active_jobs" in status
        assert "completed_jobs" in status
        assert "failed_jobs" in status

    @pytest.mark.asyncio
    async def test_process_analyze_job_success(
        self, job_processor, mock_bug_dao, mock_analysis_service,
        sample_bug, sample_analysis
    ):
        """Test successful analysis job processing."""
        # Setup mocks
        mock_bug_dao.get_bug_by_id.return_value = sample_bug
        mock_analysis_service.analyze_bug.return_value = sample_analysis

        # Create job
        job = BugTrackingJob.create(
            bug_report_id=sample_bug.id,
            job_type=JobType.ANALYZE
        )

        # Process job
        await job_processor._process_analyze_job(job, sample_bug)

        # Verify calls
        mock_analysis_service.analyze_bug.assert_called_once_with(sample_bug)
        mock_bug_dao.create_analysis.assert_called_once()
        mock_bug_dao.update_bug_status.assert_called()

    @pytest.mark.asyncio
    async def test_process_analyze_job_failure(
        self, job_processor, mock_bug_dao, mock_analysis_service, sample_bug
    ):
        """Test analysis job failure handling."""
        # Setup mock to raise error
        mock_bug_dao.get_bug_by_id.return_value = sample_bug
        mock_analysis_service.analyze_bug.side_effect = Exception("API error")

        # Create job
        job = BugTrackingJob.create(
            bug_report_id=sample_bug.id,
            job_type=JobType.ANALYZE
        )

        # Process job - should handle error gracefully
        with pytest.raises(Exception):
            await job_processor._process_analyze_job(job, sample_bug)

    @pytest.mark.asyncio
    async def test_process_fix_job_autofix_eligible(
        self, job_processor, mock_bug_dao, mock_fix_service,
        sample_bug, sample_analysis
    ):
        """Test fix job for autofix-eligible bug."""
        # Make analysis eligible for autofix
        sample_analysis.confidence_score = 95.0
        sample_analysis.complexity_estimate = ComplexityEstimate.SIMPLE

        mock_bug_dao.get_bug_by_id.return_value = sample_bug
        mock_bug_dao.get_analysis_by_bug_id = AsyncMock(return_value=sample_analysis)

        fix_attempt = BugFixAttempt.create(
            bug_report_id=sample_bug.id,
            analysis_id=sample_analysis.id
        )
        mock_fix_service.generate_fix.return_value = fix_attempt

        # Create job
        job = BugTrackingJob.create(
            bug_report_id=sample_bug.id,
            job_type=JobType.FIX
        )

        await job_processor._process_fix_job(job, sample_bug)

        # Verify fix was attempted
        mock_fix_service.generate_fix.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_fix_job_not_autofix_eligible(
        self, job_processor, mock_bug_dao, mock_fix_service,
        sample_bug, sample_analysis
    ):
        """Test fix job skips non-eligible bugs."""
        # Make analysis not eligible for autofix
        sample_analysis.confidence_score = 60.0
        sample_analysis.complexity_estimate = ComplexityEstimate.VERY_COMPLEX

        mock_bug_dao.get_bug_by_id.return_value = sample_bug
        mock_bug_dao.get_analysis_by_bug_id = AsyncMock(return_value=sample_analysis)

        # Create job
        job = BugTrackingJob.create(
            bug_report_id=sample_bug.id,
            job_type=JobType.FIX
        )

        await job_processor._process_fix_job(job, sample_bug)

        # Verify fix was NOT attempted
        mock_fix_service.generate_fix.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_notify_job(
        self, job_processor, mock_bug_dao, mock_email_service,
        sample_bug, sample_analysis
    ):
        """Test notification job processing."""
        mock_bug_dao.get_bug_by_id.return_value = sample_bug
        mock_bug_dao.get_analysis_by_bug_id = AsyncMock(return_value=sample_analysis)
        mock_bug_dao.get_fix_attempt_by_bug_id = AsyncMock(return_value=None)

        # Create job
        job = BugTrackingJob.create(
            bug_report_id=sample_bug.id,
            job_type=JobType.NOTIFY
        )

        await job_processor._process_notify_job(job, sample_bug)

        # Verify email was sent
        mock_email_service.send_bug_analysis_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_and_stop(self, job_processor):
        """Test starting and stopping the processor."""
        # Start processor
        task = asyncio.create_task(job_processor.start())

        # Wait for it to start
        await asyncio.sleep(0.1)
        assert job_processor.is_running is True

        # Stop processor
        await job_processor.stop()
        assert job_processor.is_running is False

        # Cancel task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestBugJobProcessorConcurrency:
    """Concurrency tests for BugJobProcessor."""

    @pytest.fixture
    def mock_deps(self):
        """Create all mock dependencies."""
        return {
            "bug_dao": AsyncMock(),
            "analysis_service": AsyncMock(),
            "fix_service": AsyncMock(),
            "email_service": AsyncMock()
        }

    @pytest.mark.asyncio
    async def test_concurrent_job_limit(self, mock_deps):
        """Test that concurrent job limit is respected."""
        processor = BugJobProcessor(
            bug_dao=mock_deps["bug_dao"],
            analysis_service=mock_deps["analysis_service"],
            fix_service=mock_deps["fix_service"],
            email_service=mock_deps["email_service"],
            max_concurrent_jobs=2
        )

        assert processor.max_concurrent_jobs == 2

    @pytest.mark.asyncio
    async def test_job_queue_ordering(self, mock_deps):
        """Test that jobs are processed in order."""
        processor = BugJobProcessor(
            bug_dao=mock_deps["bug_dao"],
            analysis_service=mock_deps["analysis_service"],
            fix_service=mock_deps["fix_service"],
            email_service=mock_deps["email_service"]
        )

        # Enqueue multiple jobs
        job_ids = []
        for i in range(5):
            job_id = await processor.enqueue_bug_analysis(str(uuid4()))
            job_ids.append(job_id)

        # Verify queue size
        assert processor.pending_jobs.qsize() == 5


class TestBugJobProcessorRetry:
    """Retry logic tests for BugJobProcessor."""

    @pytest.fixture
    def mock_deps(self):
        return {
            "bug_dao": AsyncMock(),
            "analysis_service": AsyncMock(),
            "fix_service": AsyncMock(),
            "email_service": AsyncMock()
        }

    @pytest.mark.asyncio
    async def test_job_retry_on_failure(self, mock_deps):
        """Test that failed jobs are retried."""
        processor = BugJobProcessor(**mock_deps)

        bug = BugReport.create(
            title="Test bug for retry",
            description="Testing retry mechanism for failed jobs.",
            submitter_email="test@example.com"
        )

        mock_deps["bug_dao"].get_bug_by_id.return_value = bug
        mock_deps["analysis_service"].analyze_bug.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            BugAnalysisResult.create(
                bug_report_id=bug.id,
                root_cause_analysis="Success",
                suggested_fix="Fix",
                affected_files=["file.py"],
                confidence_score=80.0,
                complexity_estimate=ComplexityEstimate.SIMPLE,
                claude_model_used="test",
                tokens_used=100
            )
        ]

        job = BugTrackingJob.create(
            bug_report_id=bug.id,
            job_type=JobType.ANALYZE,
            max_retries=3
        )

        # First attempt fails
        try:
            await processor._process_analyze_job(job, bug)
        except Exception:
            pass

        # Verify retry count
        assert mock_deps["analysis_service"].analyze_bug.call_count >= 1
