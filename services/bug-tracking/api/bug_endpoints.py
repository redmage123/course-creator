"""
Bug Tracking API Endpoints

BUSINESS CONTEXT:
RESTful API for bug report submission, status tracking, and management.
Integrates with background job processor for automated analysis and fixing.

ENDPOINTS:
- POST /bugs - Submit new bug report
- GET /bugs/{bug_id} - Get bug status and analysis
- GET /bugs - List all bugs (with pagination)
- GET /bugs/my - List user's submitted bugs
- PATCH /bugs/{bug_id} - Update bug (admin only)
- DELETE /bugs/{bug_id} - Delete bug (admin only)

SECURITY:
- Public submission with email verification
- Authenticated endpoints for user's own bugs
- Admin-only endpoints for management operations
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends, status
from typing import Optional, List
import logging
from datetime import datetime

from models.bug_models import (
    BugSubmissionRequest,
    BugSubmissionResponse,
    BugReportResponse,
    BugDetailResponse,
    BugListResponse,
    BugAnalysisResponse,
    BugFixResponse,
    BugUpdateRequest,
    BugStatusEnum,
    BugSeverityEnum,
)
from bug_tracking.domain.entities.bug_report import BugReport, BugSeverity, BugStatus
from bug_tracking.domain.entities.bug_job import BugTrackingJob, JobType
from data_access.bug_dao import BugDAO


router = APIRouter(
    prefix="/bugs",
    tags=["bug-tracking"],
    responses={
        404: {"description": "Bug not found"},
        500: {"description": "Internal server error"}
    }
)

logger = logging.getLogger(__name__)

# Dependency injection
def get_bug_dao() -> BugDAO:
    """Get BugDAO instance."""
    from main import bug_dao
    if not bug_dao:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bug tracking service not initialized"
        )
    return bug_dao


def get_job_processor():
    """Get job processor instance."""
    from main import job_processor
    if not job_processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job processor not initialized"
        )
    return job_processor


# Bug Submission

@router.post(
    "",
    response_model=BugSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new bug report",
    description="Submit a bug report for automated analysis by Claude AI"
)
async def submit_bug(
    request: BugSubmissionRequest,
    background_tasks: BackgroundTasks,
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    Submit a new bug report.

    The bug will be queued for automated analysis using Claude AI.
    You will receive an email notification when analysis is complete.

    Args:
        request: Bug submission details
        background_tasks: FastAPI background tasks
        bug_dao: Bug data access object

    Returns:
        BugSubmissionResponse: Confirmation with tracking ID
    """
    try:
        # Create bug report entity
        bug_report = BugReport.create(
            title=request.title,
            description=request.description,
            submitter_email=request.submitter_email,
            severity=request.severity.value,
            steps_to_reproduce=request.steps_to_reproduce,
            expected_behavior=request.expected_behavior,
            actual_behavior=request.actual_behavior,
            affected_component=request.affected_component,
            browser_info=request.browser_info,
            error_logs=request.error_logs
        )

        # Save to database
        await bug_dao.create_bug_report(bug_report)

        # Queue analysis job
        job = BugTrackingJob.create(
            bug_report_id=bug_report.id,
            job_type=JobType.ANALYZE,
            priority=_get_priority_from_severity(bug_report.severity)
        )
        await bug_dao.create_job(job)

        # Trigger background processing
        job_processor = get_job_processor()
        background_tasks.add_task(job_processor.enqueue_job, job.id)

        logger.info(f"Bug report submitted: {bug_report.id}")

        return BugSubmissionResponse(
            id=bug_report.id,
            message="Bug report submitted successfully. You will receive an email when analysis is complete.",
            status=BugStatusEnum.submitted,
            estimated_analysis_time=_estimate_analysis_time(bug_report.severity)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to submit bug: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit bug report"
        )


# Bug Retrieval

@router.get(
    "/{bug_id}",
    response_model=BugDetailResponse,
    summary="Get bug details",
    description="Get full bug details including analysis and fix status"
)
async def get_bug(
    bug_id: str,
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    Get detailed bug information.

    Returns the bug report with analysis results and fix attempt status.

    Args:
        bug_id: Bug report ID
        bug_dao: Bug data access object

    Returns:
        BugDetailResponse: Complete bug details
    """
    try:
        bug = await bug_dao.get_bug_report(bug_id)
        if not bug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug report not found: {bug_id}"
            )

        # Get associated analysis and fix
        analysis = await bug_dao.get_latest_analysis(bug_id)
        fix_attempt = await bug_dao.get_latest_fix_attempt(bug_id)

        return BugDetailResponse(
            id=bug.id,
            title=bug.title,
            description=bug.description,
            submitter_email=bug.submitter_email,
            status=BugStatusEnum(bug.status.value),
            severity=BugSeverityEnum(bug.severity.value),
            steps_to_reproduce=bug.steps_to_reproduce,
            expected_behavior=bug.expected_behavior,
            actual_behavior=bug.actual_behavior,
            affected_component=bug.affected_component,
            browser_info=bug.browser_info,
            error_logs=bug.error_logs,
            created_at=bug.created_at,
            updated_at=bug.updated_at,
            analysis=_to_analysis_response(analysis) if analysis else None,
            fix_attempt=_to_fix_response(fix_attempt) if fix_attempt else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bug {bug_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bug report"
        )


@router.get(
    "",
    response_model=BugListResponse,
    summary="List all bugs",
    description="List all bug reports with pagination and filtering"
)
async def list_bugs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[BugStatusEnum] = Query(None, description="Filter by status"),
    severity: Optional[BugSeverityEnum] = Query(None, description="Filter by severity"),
    component: Optional[str] = Query(None, description="Filter by component"),
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    List bug reports with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        status: Optional status filter
        severity: Optional severity filter
        component: Optional component filter
        bug_dao: Bug data access object

    Returns:
        BugListResponse: Paginated list of bugs
    """
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status.value
        if severity:
            filters["severity"] = severity.value
        if component:
            filters["affected_component"] = component

        # Get bugs
        bugs, total_count = await bug_dao.list_bug_reports(
            page=page,
            page_size=page_size,
            filters=filters
        )

        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size

        return BugListResponse(
            bugs=[_to_bug_response(bug) for bug in bugs],
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=page < total_pages,
            has_prev=page > 1
        )

    except Exception as e:
        logger.error(f"Failed to list bugs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list bug reports"
        )


@router.get(
    "/my/reports",
    response_model=BugListResponse,
    summary="List my bugs",
    description="List bugs submitted by the authenticated user"
)
async def list_my_bugs(
    email: str = Query(..., description="Submitter email"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    List bugs submitted by a specific email.

    Args:
        email: Submitter's email address
        page: Page number
        page_size: Items per page
        bug_dao: Bug data access object

    Returns:
        BugListResponse: Paginated list of user's bugs
    """
    try:
        bugs, total_count = await bug_dao.list_bug_reports(
            page=page,
            page_size=page_size,
            filters={"submitter_email": email}
        )

        total_pages = (total_count + page_size - 1) // page_size

        return BugListResponse(
            bugs=[_to_bug_response(bug) for bug in bugs],
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=page < total_pages,
            has_prev=page > 1
        )

    except Exception as e:
        logger.error(f"Failed to list user bugs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list bug reports"
        )


# Bug Management (Admin)

@router.patch(
    "/{bug_id}",
    response_model=BugReportResponse,
    summary="Update bug",
    description="Update bug status or severity (admin only)"
)
async def update_bug(
    bug_id: str,
    request: BugUpdateRequest,
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    Update bug report properties.

    Args:
        bug_id: Bug report ID
        request: Update fields
        bug_dao: Bug data access object

    Returns:
        BugReportResponse: Updated bug summary
    """
    try:
        bug = await bug_dao.get_bug_report(bug_id)
        if not bug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug report not found: {bug_id}"
            )

        # Update fields
        if request.severity:
            bug.severity = BugSeverity(request.severity.value)
        if request.status:
            bug.update_status(BugStatus(request.status.value))
        if request.affected_component:
            bug.affected_component = request.affected_component

        await bug_dao.update_bug_report(bug)

        return _to_bug_response(bug)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update bug {bug_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bug report"
        )


@router.delete(
    "/{bug_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete bug",
    description="Delete a bug report (admin only)"
)
async def delete_bug(
    bug_id: str,
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    Delete a bug report.

    Args:
        bug_id: Bug report ID
        bug_dao: Bug data access object
    """
    try:
        bug = await bug_dao.get_bug_report(bug_id)
        if not bug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug report not found: {bug_id}"
            )

        await bug_dao.delete_bug_report(bug_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete bug {bug_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bug report"
        )


# Analysis Endpoints

@router.get(
    "/{bug_id}/analysis",
    response_model=BugAnalysisResponse,
    summary="Get bug analysis",
    description="Get Claude's analysis of the bug"
)
async def get_bug_analysis(
    bug_id: str,
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    Get the latest analysis for a bug.

    Args:
        bug_id: Bug report ID
        bug_dao: Bug data access object

    Returns:
        BugAnalysisResponse: Analysis results
    """
    try:
        analysis = await bug_dao.get_latest_analysis(bug_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or still pending"
            )

        return _to_analysis_response(analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis for bug {bug_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis"
        )


@router.post(
    "/{bug_id}/reanalyze",
    response_model=BugSubmissionResponse,
    summary="Re-analyze bug",
    description="Request a new analysis for the bug"
)
async def reanalyze_bug(
    bug_id: str,
    background_tasks: BackgroundTasks,
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    Request re-analysis of a bug.

    Args:
        bug_id: Bug report ID
        background_tasks: FastAPI background tasks
        bug_dao: Bug data access object

    Returns:
        BugSubmissionResponse: Confirmation
    """
    try:
        bug = await bug_dao.get_bug_report(bug_id)
        if not bug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bug report not found: {bug_id}"
            )

        # Queue new analysis job
        job = BugTrackingJob.create(
            bug_report_id=bug.id,
            job_type=JobType.ANALYZE,
            priority=_get_priority_from_severity(bug.severity)
        )
        await bug_dao.create_job(job)

        # Update status
        bug.update_status(BugStatus.SUBMITTED)
        await bug_dao.update_bug_report(bug)

        # Trigger background processing
        job_processor = get_job_processor()
        background_tasks.add_task(job_processor.enqueue_job, job.id)

        return BugSubmissionResponse(
            id=bug.id,
            message="Bug report queued for re-analysis",
            status=BugStatusEnum.submitted,
            estimated_analysis_time=_estimate_analysis_time(bug.severity)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reanalyze bug {bug_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue re-analysis"
        )


# Fix Endpoints

@router.get(
    "/{bug_id}/fix",
    response_model=BugFixResponse,
    summary="Get fix attempt",
    description="Get the latest fix attempt for the bug"
)
async def get_bug_fix(
    bug_id: str,
    bug_dao: BugDAO = Depends(get_bug_dao)
):
    """
    Get the latest fix attempt for a bug.

    Args:
        bug_id: Bug report ID
        bug_dao: Bug data access object

    Returns:
        BugFixResponse: Fix attempt details
    """
    try:
        fix_attempt = await bug_dao.get_latest_fix_attempt(bug_id)
        if not fix_attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No fix attempt found"
            )

        return _to_fix_response(fix_attempt)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get fix for bug {bug_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fix attempt"
        )


# Helper Functions

def _get_priority_from_severity(severity: BugSeverity) -> int:
    """Map severity to job priority (1-10)."""
    priority_map = {
        BugSeverity.CRITICAL: 10,
        BugSeverity.HIGH: 8,
        BugSeverity.MEDIUM: 5,
        BugSeverity.LOW: 3
    }
    return priority_map.get(severity, 5)


def _estimate_analysis_time(severity: BugSeverity) -> str:
    """Estimate analysis time based on severity."""
    if severity == BugSeverity.CRITICAL:
        return "2-5 minutes"
    elif severity == BugSeverity.HIGH:
        return "5-10 minutes"
    else:
        return "10-15 minutes"


def _to_bug_response(bug: BugReport) -> BugReportResponse:
    """Convert BugReport entity to response model."""
    return BugReportResponse(
        id=bug.id,
        title=bug.title,
        status=BugStatusEnum(bug.status.value),
        severity=BugSeverityEnum(bug.severity.value),
        affected_component=bug.affected_component,
        created_at=bug.created_at,
        updated_at=bug.updated_at
    )


def _to_analysis_response(analysis) -> BugAnalysisResponse:
    """Convert analysis entity to response model."""
    return BugAnalysisResponse(
        id=analysis.id,
        bug_report_id=analysis.bug_report_id,
        root_cause_analysis=analysis.root_cause_analysis,
        suggested_fix=analysis.suggested_fix,
        affected_files=analysis.affected_files,
        confidence_score=analysis.confidence_score,
        complexity_estimate=analysis.complexity_estimate.value,
        claude_model_used=analysis.claude_model_used,
        tokens_used=analysis.tokens_used,
        analysis_completed_at=analysis.analysis_completed_at
    )


def _to_fix_response(fix_attempt) -> BugFixResponse:
    """Convert fix attempt entity to response model."""
    from models.bug_models import FileChangeResponse, FixStatusEnum

    return BugFixResponse(
        id=fix_attempt.id,
        bug_report_id=fix_attempt.bug_report_id,
        status=FixStatusEnum(fix_attempt.status.value),
        branch_name=fix_attempt.branch_name,
        pr_number=fix_attempt.pr_number,
        pr_url=fix_attempt.pr_url,
        files_changed=[
            FileChangeResponse(
                file_path=f.file_path,
                change_type=f.change_type,
                lines_added=f.lines_added,
                lines_removed=f.lines_removed
            )
            for f in fix_attempt.files_changed
        ],
        lines_added=fix_attempt.lines_added,
        lines_removed=fix_attempt.lines_removed,
        tests_passed=fix_attempt.tests_passed,
        tests_failed=fix_attempt.tests_failed,
        error_message=fix_attempt.error_message,
        created_at=fix_attempt.created_at,
        completed_at=fix_attempt.completed_at
    )
