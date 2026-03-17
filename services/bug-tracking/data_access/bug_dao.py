"""
Bug Tracking Data Access Object (DAO)

BUSINESS CONTEXT:
Provides database operations for bug tracking entities using
the repository pattern with PostgreSQL.

TECHNICAL CONTEXT:
- Async database operations using asyncpg
- Follows existing DAO patterns from other services
- Supports filtering, pagination, and CRUD operations
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json
import asyncpg

from bug_tracking.domain.entities.bug_report import BugReport, BugSeverity, BugStatus
from bug_tracking.domain.entities.bug_analysis import BugAnalysisResult, ComplexityEstimate
from bug_tracking.domain.entities.bug_fix import BugFixAttempt, FixStatus, FileChange
from bug_tracking.domain.entities.bug_job import BugTrackingJob, JobType, JobStatus


logger = logging.getLogger(__name__)


class BugDAO:
    """
    Data Access Object for bug tracking operations.

    Provides CRUD operations and queries for:
    - Bug reports
    - Analysis results
    - Fix attempts
    - Background jobs

    Example:
        dao = BugDAO(database_url="postgresql://user:pass@localhost/db")
        await dao.connect()
        bug = await dao.get_bug_report("bug-123")
    """

    def __init__(self, database_url: str):
        """
        Initialize BugDAO.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Establish database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10
            )
            logger.info("Bug tracking database connection pool created")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Bug tracking database connection pool closed")

    # Bug Report Operations

    async def create_bug_report(self, bug: BugReport) -> BugReport:
        """
        Create a new bug report.

        Args:
            bug: BugReport entity to create

        Returns:
            BugReport: Created bug with ID
        """
        query = """
            INSERT INTO bug_reports (
                id, title, description, steps_to_reproduce,
                expected_behavior, actual_behavior, severity, status,
                submitter_email, submitter_user_id, affected_component,
                browser_info, error_logs, screenshot_urls,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            RETURNING id
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                bug.id,
                bug.title,
                bug.description,
                bug.steps_to_reproduce,
                bug.expected_behavior,
                bug.actual_behavior,
                bug.severity.value,
                bug.status.value,
                bug.submitter_email,
                bug.submitter_user_id,
                bug.affected_component,
                bug.browser_info,
                bug.error_logs,
                json.dumps(bug.screenshot_urls),
                bug.created_at,
                bug.updated_at
            )
            logger.info(f"Created bug report: {bug.id}")
            return bug

    async def get_bug_report(self, bug_id: str) -> Optional[BugReport]:
        """
        Get a bug report by ID.

        Args:
            bug_id: Bug report ID

        Returns:
            BugReport or None if not found
        """
        query = """
            SELECT id, title, description, steps_to_reproduce,
                   expected_behavior, actual_behavior, severity, status,
                   submitter_email, submitter_user_id, affected_component,
                   browser_info, error_logs, screenshot_urls,
                   created_at, updated_at
            FROM bug_reports
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, bug_id)
            if not row:
                return None
            return self._row_to_bug_report(row)

    async def update_bug_report(self, bug: BugReport) -> BugReport:
        """
        Update an existing bug report.

        Args:
            bug: BugReport with updated fields

        Returns:
            BugReport: Updated bug
        """
        query = """
            UPDATE bug_reports
            SET title = $2, description = $3, steps_to_reproduce = $4,
                expected_behavior = $5, actual_behavior = $6,
                severity = $7, status = $8, affected_component = $9,
                browser_info = $10, error_logs = $11, screenshot_urls = $12,
                updated_at = $13
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                bug.id,
                bug.title,
                bug.description,
                bug.steps_to_reproduce,
                bug.expected_behavior,
                bug.actual_behavior,
                bug.severity.value,
                bug.status.value,
                bug.affected_component,
                bug.browser_info,
                bug.error_logs,
                json.dumps(bug.screenshot_urls),
                datetime.utcnow()
            )
            logger.info(f"Updated bug report: {bug.id}")
            return bug

    async def delete_bug_report(self, bug_id: str) -> bool:
        """
        Delete a bug report.

        Args:
            bug_id: Bug report ID

        Returns:
            bool: True if deleted
        """
        query = "DELETE FROM bug_reports WHERE id = $1"
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, bug_id)
            deleted = result == "DELETE 1"
            if deleted:
                logger.info(f"Deleted bug report: {bug_id}")
            return deleted

    async def list_bug_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[BugReport], int]:
        """
        List bug reports with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            filters: Optional filters (status, severity, etc.)

        Returns:
            Tuple of (bugs list, total count)
        """
        filters = filters or {}
        offset = (page - 1) * page_size

        # Build WHERE clause
        where_clauses = []
        params = []
        param_idx = 1

        for key, value in filters.items():
            where_clauses.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count query
        count_query = f"SELECT COUNT(*) FROM bug_reports WHERE {where_sql}"

        # Data query
        data_query = f"""
            SELECT id, title, description, steps_to_reproduce,
                   expected_behavior, actual_behavior, severity, status,
                   submitter_email, submitter_user_id, affected_component,
                   browser_info, error_logs, screenshot_urls,
                   created_at, updated_at
            FROM bug_reports
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([page_size, offset])

        async with self.pool.acquire() as conn:
            total_count = await conn.fetchval(count_query, *params[:-2])
            rows = await conn.fetch(data_query, *params)

            bugs = [self._row_to_bug_report(row) for row in rows]
            return bugs, total_count

    async def update_bug_status(self, bug_id: str, status: BugStatus) -> bool:
        """
        Update bug status.

        Args:
            bug_id: Bug report ID
            status: New status

        Returns:
            bool: True if updated
        """
        query = """
            UPDATE bug_reports
            SET status = $2, updated_at = $3
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, bug_id, status.value, datetime.utcnow())
            return result == "UPDATE 1"

    # Analysis Operations

    async def create_analysis(self, analysis: BugAnalysisResult) -> BugAnalysisResult:
        """Create a bug analysis result."""
        query = """
            INSERT INTO bug_analysis_results (
                id, bug_report_id, root_cause_analysis, suggested_fix,
                affected_files, confidence_score, complexity_estimate,
                claude_model_used, tokens_used, analysis_duration_ms,
                analysis_started_at, analysis_completed_at, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                analysis.id,
                analysis.bug_report_id,
                analysis.root_cause_analysis,
                analysis.suggested_fix,
                json.dumps(analysis.affected_files),
                analysis.confidence_score,
                analysis.complexity_estimate.value,
                analysis.claude_model_used,
                analysis.tokens_used,
                analysis.analysis_duration_ms,
                analysis.analysis_started_at,
                analysis.analysis_completed_at,
                analysis.created_at
            )
            logger.info(f"Created analysis: {analysis.id}")
            return analysis

    async def get_latest_analysis(self, bug_id: str) -> Optional[BugAnalysisResult]:
        """Get the most recent analysis for a bug."""
        query = """
            SELECT id, bug_report_id, root_cause_analysis, suggested_fix,
                   affected_files, confidence_score, complexity_estimate,
                   claude_model_used, tokens_used, analysis_duration_ms,
                   analysis_started_at, analysis_completed_at, created_at
            FROM bug_analysis_results
            WHERE bug_report_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, bug_id)
            if not row:
                return None
            return self._row_to_analysis(row)

    # Fix Attempt Operations

    async def create_fix_attempt(self, fix: BugFixAttempt) -> BugFixAttempt:
        """Create a bug fix attempt."""
        query = """
            INSERT INTO bug_fix_attempts (
                id, bug_report_id, analysis_id, branch_name, pr_number,
                pr_url, commit_sha, files_changed, lines_added, lines_removed,
                status, tests_run, tests_passed, tests_failed, test_output,
                error_message, fix_tokens_used, created_at, completed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                fix.id,
                fix.bug_report_id,
                fix.analysis_id,
                fix.branch_name,
                fix.pr_number,
                fix.pr_url,
                fix.commit_sha,
                json.dumps([f.to_dict() for f in fix.files_changed]),
                fix.lines_added,
                fix.lines_removed,
                fix.status.value,
                fix.tests_run,
                fix.tests_passed,
                fix.tests_failed,
                fix.test_output,
                fix.error_message,
                fix.fix_tokens_used,
                fix.created_at,
                fix.completed_at
            )
            logger.info(f"Created fix attempt: {fix.id}")
            return fix

    async def update_fix_attempt(self, fix: BugFixAttempt) -> BugFixAttempt:
        """Update a fix attempt."""
        query = """
            UPDATE bug_fix_attempts
            SET branch_name = $2, pr_number = $3, pr_url = $4, commit_sha = $5,
                files_changed = $6, lines_added = $7, lines_removed = $8,
                status = $9, tests_run = $10, tests_passed = $11, tests_failed = $12,
                test_output = $13, error_message = $14, fix_tokens_used = $15,
                completed_at = $16
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                fix.id,
                fix.branch_name,
                fix.pr_number,
                fix.pr_url,
                fix.commit_sha,
                json.dumps([f.to_dict() for f in fix.files_changed]),
                fix.lines_added,
                fix.lines_removed,
                fix.status.value,
                fix.tests_run,
                fix.tests_passed,
                fix.tests_failed,
                fix.test_output,
                fix.error_message,
                fix.fix_tokens_used,
                fix.completed_at
            )
            return fix

    async def get_latest_fix_attempt(self, bug_id: str) -> Optional[BugFixAttempt]:
        """Get the most recent fix attempt for a bug."""
        query = """
            SELECT id, bug_report_id, analysis_id, branch_name, pr_number,
                   pr_url, commit_sha, files_changed, lines_added, lines_removed,
                   status, tests_run, tests_passed, tests_failed, test_output,
                   error_message, fix_tokens_used, created_at, completed_at
            FROM bug_fix_attempts
            WHERE bug_report_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, bug_id)
            if not row:
                return None
            return self._row_to_fix_attempt(row)

    # Job Operations

    async def create_job(self, job: BugTrackingJob) -> BugTrackingJob:
        """Create a background job."""
        query = """
            INSERT INTO bug_tracking_jobs (
                id, bug_report_id, job_type, status, priority,
                retry_count, max_retries, error_message, worker_id,
                queued_at, started_at, completed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                job.id,
                job.bug_report_id,
                job.job_type.value,
                job.status.value,
                job.priority,
                job.retry_count,
                job.max_retries,
                job.error_message,
                job.worker_id,
                job.queued_at,
                job.started_at,
                job.completed_at
            )
            return job

    async def get_next_job(self, job_type: Optional[JobType] = None) -> Optional[BugTrackingJob]:
        """Get the next job to process (highest priority, oldest)."""
        query = """
            SELECT id, bug_report_id, job_type, status, priority,
                   retry_count, max_retries, error_message, worker_id,
                   queued_at, started_at, completed_at
            FROM bug_tracking_jobs
            WHERE status = 'queued'
        """
        if job_type:
            query += f" AND job_type = '{job_type.value}'"
        query += " ORDER BY priority DESC, queued_at ASC LIMIT 1"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query)
            if not row:
                return None
            return self._row_to_job(row)

    async def update_job(self, job: BugTrackingJob) -> BugTrackingJob:
        """Update a job."""
        query = """
            UPDATE bug_tracking_jobs
            SET status = $2, retry_count = $3, error_message = $4,
                worker_id = $5, started_at = $6, completed_at = $7
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                job.id,
                job.status.value,
                job.retry_count,
                job.error_message,
                job.worker_id,
                job.started_at,
                job.completed_at
            )
            return job

    # Helper Methods

    def _row_to_bug_report(self, row: asyncpg.Record) -> BugReport:
        """Convert database row to BugReport entity."""
        return BugReport(
            id=str(row["id"]),
            title=row["title"],
            description=row["description"],
            steps_to_reproduce=row["steps_to_reproduce"],
            expected_behavior=row["expected_behavior"],
            actual_behavior=row["actual_behavior"],
            severity=BugSeverity(row["severity"]),
            status=BugStatus(row["status"]),
            submitter_email=row["submitter_email"],
            submitter_user_id=str(row["submitter_user_id"]) if row["submitter_user_id"] else None,
            affected_component=row["affected_component"],
            browser_info=row["browser_info"],
            error_logs=row["error_logs"],
            screenshot_urls=json.loads(row["screenshot_urls"]) if row["screenshot_urls"] else [],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _row_to_analysis(self, row: asyncpg.Record) -> BugAnalysisResult:
        """Convert database row to BugAnalysisResult entity."""
        return BugAnalysisResult(
            id=str(row["id"]),
            bug_report_id=str(row["bug_report_id"]),
            root_cause_analysis=row["root_cause_analysis"],
            suggested_fix=row["suggested_fix"],
            affected_files=json.loads(row["affected_files"]) if row["affected_files"] else [],
            confidence_score=float(row["confidence_score"]),
            complexity_estimate=ComplexityEstimate(row["complexity_estimate"]),
            claude_model_used=row["claude_model_used"],
            tokens_used=row["tokens_used"],
            analysis_duration_ms=row["analysis_duration_ms"],
            analysis_started_at=row["analysis_started_at"],
            analysis_completed_at=row["analysis_completed_at"],
            created_at=row["created_at"]
        )

    def _row_to_fix_attempt(self, row: asyncpg.Record) -> BugFixAttempt:
        """Convert database row to BugFixAttempt entity."""
        files_data = json.loads(row["files_changed"]) if row["files_changed"] else []
        files_changed = [FileChange(**f) for f in files_data]

        return BugFixAttempt(
            id=str(row["id"]),
            bug_report_id=str(row["bug_report_id"]),
            analysis_id=str(row["analysis_id"]),
            status=FixStatus(row["status"]),
            branch_name=row["branch_name"],
            pr_number=row["pr_number"],
            pr_url=row["pr_url"],
            commit_sha=row["commit_sha"],
            files_changed=files_changed,
            lines_added=row["lines_added"],
            lines_removed=row["lines_removed"],
            tests_run=row["tests_run"],
            tests_passed=row["tests_passed"],
            tests_failed=row["tests_failed"],
            test_output=row["test_output"],
            error_message=row["error_message"],
            fix_tokens_used=row["fix_tokens_used"],
            created_at=row["created_at"],
            completed_at=row["completed_at"]
        )

    def _row_to_job(self, row: asyncpg.Record) -> BugTrackingJob:
        """Convert database row to BugTrackingJob entity."""
        return BugTrackingJob(
            id=str(row["id"]),
            bug_report_id=str(row["bug_report_id"]),
            job_type=JobType(row["job_type"]),
            status=JobStatus(row["status"]),
            priority=row["priority"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            error_message=row["error_message"],
            worker_id=row["worker_id"],
            queued_at=row["queued_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"]
        )
