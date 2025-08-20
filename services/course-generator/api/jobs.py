"""
Job management API routes.
Single Responsibility: Handle job-related HTTP requests.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, Optional

from app.dependencies import get_container, DependencyContainer
from application.services.job_management_service import JobManagementService
from domain.entities.course_content import JobStatus

router = APIRouter()

def get_job_service(request: Request):
    """Dependency to get job service."""
    container: DependencyContainer = request.app.state.container
    return container.get_job_service()

@router.get("/{job_id}")
async def get_job_status(
    job_id: str, 
    job_service: JobManagementService = Depends(get_job_service)
) -> Dict[str, Any]:
    """Get job status and details."""
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "task_name": job.task_name,
        "status": job.status.value,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "progress": job.progress,
        "result": job.result,
        "error": job.error
    }

@router.get("/{job_id}/result")
async def get_job_result(
    job_id: str,
    job_service: JobManagementService = Depends(get_job_service)
) -> Dict[str, Any]:
    """Get job result."""
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == JobStatus.PENDING:
        raise HTTPException(status_code=202, detail="Job is still pending")
    elif job.status == JobStatus.RUNNING:
        raise HTTPException(status_code=202, detail="Job is still running")
    elif job.status == JobStatus.FAILED:
        raise HTTPException(status_code=500, detail=f"Job failed: {job.error}")
    elif job.status == JobStatus.CANCELLED:
        raise HTTPException(status_code=410, detail="Job was cancelled")
    
    return {
        "id": job.id,
        "status": job.status.value,
        "result": job.result,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }

@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    job_service: JobManagementService = Depends(get_job_service)
) -> Dict[str, str]:
    """Cancel a running job."""
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job.status.value}"
        )
    
    cancelled = job_service.cancel_job(job_id)
    
    if cancelled:
        return {"message": f"Job {job_id} cancelled successfully"}
    else:
        return {"message": f"Job {job_id} could not be cancelled"}

@router.get("")
async def list_jobs(
    job_service: JobManagementService = Depends(get_job_service)
) -> Dict[str, Any]:
    """List all jobs (for debugging/monitoring)."""
    jobs = job_service.get_all_jobs()
    
    job_list = []
    for job in jobs.values():
        job_list.append({
            "id": job.id,
            "task_name": job.task_name,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "progress": job.progress
        })
    
    return {
        "jobs": job_list,
        "total": len(job_list),
        "running": job_service.get_running_jobs_count()
    }