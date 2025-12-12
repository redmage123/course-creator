"""
Bug Job Processor Service

BUSINESS CONTEXT:
Asyncio-based background job processor for bug tracking:
- Processes analysis jobs
- Processes fix generation jobs
- Processes email notification jobs
- Supports priority queuing and retry logic

TECHNICAL CONTEXT:
- Uses asyncio.Queue for job management
- Follows existing job_management_service.py pattern
- Supports concurrent job processing
- Implements exponential backoff for retries
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import uuid

from bug_tracking.domain.entities.bug_report import BugReport, BugStatus
from bug_tracking.domain.entities.bug_job import BugTrackingJob, JobType, JobStatus
from bug_tracking.application.services.bug_analysis_service import BugAnalysisService
from bug_tracking.application.services.fix_generation_service import FixGenerationService
from bug_tracking.application.services.bug_email_service import BugEmailService
from data_access.bug_dao import BugDAO


logger = logging.getLogger(__name__)


class BugJobProcessor:
    """
    Asyncio-based background job processor for bug tracking.

    Handles:
    - Bug analysis jobs (Claude analysis)
    - Fix generation jobs (auto-fix + PR)
    - Email notification jobs

    Example:
        processor = BugJobProcessor(
            bug_dao=bug_dao,
            analysis_service=analysis_service,
            fix_service=fix_service,
            email_service=email_service
        )
        await processor.start()
        await processor.enqueue_job(job_id)
    """

    def __init__(
        self,
        bug_dao: BugDAO,
        analysis_service: BugAnalysisService,
        fix_service: FixGenerationService,
        email_service: BugEmailService,
        max_concurrent_jobs: int = 3,
        worker_id: Optional[str] = None
    ):
        """
        Initialize BugJobProcessor.

        Args:
            bug_dao: Bug data access object
            analysis_service: Bug analysis service
            fix_service: Fix generation service
            email_service: Email notification service
            max_concurrent_jobs: Max concurrent jobs
            worker_id: Unique worker identifier
        """
        self.bug_dao = bug_dao
        self.analysis_service = analysis_service
        self.fix_service = fix_service
        self.email_service = email_service
        self.max_concurrent_jobs = max_concurrent_jobs
        self.worker_id = worker_id or str(uuid.uuid4())[:8]

        # Job tracking
        self.pending_jobs: asyncio.Queue = asyncio.Queue()
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.completed_jobs: Dict[str, bool] = {}

        # Control flags
        self._running = False
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the job processor."""
        if self._running:
            logger.warning("Job processor already running")
            return

        self._running = True
        self._shutdown_event.clear()

        logger.info(f"Bug job processor started (worker: {self.worker_id})")

        # Start worker tasks
        workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_concurrent_jobs)
        ]

        # Start job polling task
        poll_task = asyncio.create_task(self._poll_jobs())

        try:
            # Wait for shutdown signal
            await self._shutdown_event.wait()
        finally:
            # Cancel all workers
            for worker in workers:
                worker.cancel()
            poll_task.cancel()

            # Wait for workers to finish
            await asyncio.gather(*workers, poll_task, return_exceptions=True)

            self._running = False
            logger.info("Bug job processor stopped")

    async def stop(self) -> None:
        """Stop the job processor."""
        self._shutdown_event.set()

    async def enqueue_job(self, job_id: str) -> None:
        """
        Add a job to the processing queue.

        Args:
            job_id: ID of the job to process
        """
        await self.pending_jobs.put(job_id)
        logger.debug(f"Job {job_id} enqueued")

    async def _poll_jobs(self) -> None:
        """Poll database for pending jobs."""
        while self._running:
            try:
                # Check for queued jobs in database
                job = await self.bug_dao.get_next_job()
                if job and job.id not in self.active_jobs:
                    await self.enqueue_job(job.id)

                await asyncio.sleep(5)  # Poll every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Job polling error: {e}")
                await asyncio.sleep(10)

    async def _worker(self, worker_num: int) -> None:
        """Worker task that processes jobs from the queue."""
        while self._running:
            try:
                # Get next job from queue
                job_id = await asyncio.wait_for(
                    self.pending_jobs.get(),
                    timeout=10.0
                )

                # Process the job
                task = asyncio.create_task(self._process_job(job_id))
                self.active_jobs[job_id] = task

                try:
                    await task
                finally:
                    self.active_jobs.pop(job_id, None)
                    self.pending_jobs.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_num} error: {e}")

    async def _process_job(self, job_id: str) -> None:
        """
        Process a single job.

        Args:
            job_id: Job ID to process
        """
        job = await self.bug_dao.get_job(job_id) if hasattr(self.bug_dao, 'get_job') else None

        # If get_job not available, fetch from next_job
        if not job:
            job = await self.bug_dao.get_next_job()
            if not job or job.id != job_id:
                logger.warning(f"Job {job_id} not found")
                return

        try:
            logger.info(f"Processing job {job.id} (type: {job.job_type.value})")

            # Mark job as processing
            job.start_processing(self.worker_id)
            await self.bug_dao.update_job(job)

            # Get bug report
            bug = await self.bug_dao.get_bug_report(job.bug_report_id)
            if not bug:
                raise JobProcessingError(f"Bug report not found: {job.bug_report_id}")

            # Process based on job type
            if job.job_type == JobType.ANALYZE:
                await self._process_analysis_job(job, bug)
            elif job.job_type == JobType.FIX:
                await self._process_fix_job(job, bug)
            elif job.job_type == JobType.NOTIFY:
                await self._process_notify_job(job, bug)
            else:
                raise JobProcessingError(f"Unknown job type: {job.job_type}")

            # Mark job as completed
            job.complete()
            await self.bug_dao.update_job(job)

            logger.info(f"Job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")

            # Handle retry
            should_retry = job.fail(str(e))
            await self.bug_dao.update_job(job)

            if should_retry:
                # Re-queue with backoff
                wait_time = job.get_wait_time_seconds()
                logger.info(f"Retrying job {job.id} in {wait_time}s (attempt {job.retry_count})")
                await asyncio.sleep(wait_time)
                await self.enqueue_job(job.id)

    async def _process_analysis_job(
        self,
        job: BugTrackingJob,
        bug: BugReport
    ) -> None:
        """Process a bug analysis job."""
        # Update bug status
        bug.update_status(BugStatus.ANALYZING)
        await self.bug_dao.update_bug_report(bug)

        try:
            # Run analysis
            analysis = await self.analysis_service.analyze_bug(bug)

            # Save analysis result
            await self.bug_dao.create_analysis(analysis)

            # Update bug status
            bug.update_status(BugStatus.ANALYSIS_COMPLETE)
            await self.bug_dao.update_bug_report(bug)

            # Queue fix job if high confidence
            if analysis.is_safe_to_autofix():
                fix_job = BugTrackingJob.create(
                    bug_report_id=bug.id,
                    job_type=JobType.FIX,
                    priority=job.priority
                )
                await self.bug_dao.create_job(fix_job)
                await self.enqueue_job(fix_job.id)

            # Queue notification job
            notify_job = BugTrackingJob.create(
                bug_report_id=bug.id,
                job_type=JobType.NOTIFY,
                priority=5
            )
            await self.bug_dao.create_job(notify_job)
            await self.enqueue_job(notify_job.id)

        except Exception as e:
            bug.update_status(BugStatus.ANALYSIS_FAILED)
            await self.bug_dao.update_bug_report(bug)
            raise

    async def _process_fix_job(
        self,
        job: BugTrackingJob,
        bug: BugReport
    ) -> None:
        """Process a fix generation job."""
        # Get analysis
        analysis = await self.bug_dao.get_latest_analysis(bug.id)
        if not analysis:
            raise JobProcessingError("No analysis found for bug")

        # Update bug status
        bug.update_status(BugStatus.FIXING)
        await self.bug_dao.update_bug_report(bug)

        try:
            # Generate fix
            fix_attempt = await self.fix_service.generate_fix(analysis, bug)

            # Save fix attempt
            await self.bug_dao.create_fix_attempt(fix_attempt)

            # Update bug status based on result
            if fix_attempt.is_successful():
                bug.update_status(BugStatus.PR_OPENED)
            else:
                bug.update_status(BugStatus.ANALYSIS_COMPLETE)  # Revert to analysis done

            await self.bug_dao.update_bug_report(bug)

            # Queue notification for fix result
            notify_job = BugTrackingJob.create(
                bug_report_id=bug.id,
                job_type=JobType.NOTIFY,
                priority=5
            )
            await self.bug_dao.create_job(notify_job)
            await self.enqueue_job(notify_job.id)

        except Exception as e:
            bug.update_status(BugStatus.ANALYSIS_COMPLETE)
            await self.bug_dao.update_bug_report(bug)
            raise

    async def _process_notify_job(
        self,
        job: BugTrackingJob,
        bug: BugReport
    ) -> None:
        """Process an email notification job."""
        # Get analysis and fix attempt
        analysis = await self.bug_dao.get_latest_analysis(bug.id)
        fix_attempt = await self.bug_dao.get_latest_fix_attempt(bug.id)

        # Send email
        await self.email_service.send_bug_analysis_email(
            bug=bug,
            analysis=analysis,
            fix_attempt=fix_attempt
        )

    def get_status(self) -> Dict:
        """Get processor status."""
        return {
            "running": self._running,
            "worker_id": self.worker_id,
            "active_jobs": len(self.active_jobs),
            "pending_jobs": self.pending_jobs.qsize(),
            "completed_jobs": len(self.completed_jobs)
        }


class JobProcessingError(Exception):
    """Exception raised when job processing fails."""
    pass
