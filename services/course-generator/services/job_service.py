"""
Job service for handling background tasks.
Single Responsibility: Manage job lifecycle and execution.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Job:
    """Job entity."""
    
    def __init__(self, job_id: str, task_name: str):
        self.id = job_id
        self.task_name = task_name
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.progress: int = 0

class JobService:
    """Service for managing background jobs."""
    
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
    
    def create_job(self, task_name: str) -> str:
        """Create a new job."""
        job_id = str(uuid.uuid4())
        job = Job(job_id, task_name)
        self._jobs[job_id] = job
        
        logger.info(f"Created job {job_id} for task '{task_name}'")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status."""
        job = self.get_job(job_id)
        return job.status if job else None
    
    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job result."""
        job = self.get_job(job_id)
        return job.result if job else None
    
    async def execute_job(
        self, 
        job_id: str, 
        task_func: Callable[..., Any], 
        *args, 
        **kwargs
    ) -> None:
        """Execute a job asynchronously."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status != JobStatus.PENDING:
            raise ValueError(f"Job {job_id} is not in pending state")
        
        # Create and store the task
        task = asyncio.create_task(self._run_job(job, task_func, *args, **kwargs))
        self._tasks[job_id] = task
        
        # Don't await here - let it run in background
        logger.info(f"Started job {job_id}")
    
    async def _run_job(
        self, 
        job: Job, 
        task_func: Callable[..., Any], 
        *args, 
        **kwargs
    ) -> None:
        """Internal method to run a job."""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            logger.info(f"Executing job {job.id}")
            
            # Execute the task
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                result = task_func(*args, **kwargs)
            
            # Store result
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
            logger.info(f"Job {job.id} completed successfully")
            
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            logger.info(f"Job {job.id} was cancelled")
            raise
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            
            logger.error(f"Job {job.id} failed: {e}")
            
        finally:
            # Clean up task reference
            if job.id in self._tasks:
                del self._tasks[job.id]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled job {job_id}")
            return True
        return False
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed jobs."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        jobs_to_remove = []
        for job_id, job in self._jobs.items():
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] 
                and job.completed_at 
                and job.completed_at.timestamp() < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self._jobs[job_id]
        
        logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        return len(jobs_to_remove)
    
    def get_all_jobs(self) -> Dict[str, Job]:
        """Get all jobs (for debugging/monitoring)."""
        return self._jobs.copy()
    
    def get_running_jobs_count(self) -> int:
        """Get count of currently running jobs."""
        return sum(1 for job in self._jobs.values() if job.status == JobStatus.RUNNING)