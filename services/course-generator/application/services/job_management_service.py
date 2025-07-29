"""
Job Management Service Implementation
Single Responsibility: Manage content generation jobs and their lifecycle
Dependency Inversion: Depends on repository abstractions for data access
"""
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from ...domain.entities.course_content import GenerationJob, JobStatus, ContentType
from ...domain.interfaces.content_generation_service import IJobManagementService
from ...domain.interfaces.content_repository import IGenerationJobRepository
from ...domain.interfaces.ai_service import IAIService

class JobPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class JobManagementService(IJobManagementService):
    """
    Job management service implementation with business logic
    """
    
    def __init__(self, 
                 job_repository: IGenerationJobRepository,
                 ai_service: IAIService):
        self._job_repository = job_repository
        self._ai_service = ai_service
        self._job_processors: Dict[ContentType, Callable] = {}
        self._running_jobs: Dict[str, asyncio.Task] = {}
        self._max_concurrent_jobs = 5
        self._job_timeout_minutes = 30
    
    async def create_generation_job(self, content_type: ContentType, course_id: str, 
                                   parameters: Dict[str, Any],
                                   priority: str = "normal",
                                   scheduled_time: Optional[datetime] = None) -> GenerationJob:
        """Create a new content generation job"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not isinstance(parameters, dict):
            raise ValueError("Parameters must be a dictionary")
        
        # Validate priority
        try:
            job_priority = JobPriority(priority.lower())
        except ValueError:
            raise ValueError(f"Invalid priority: {priority}")
        
        # Create job entity
        job = GenerationJob(
            content_type=content_type,
            course_id=course_id,
            parameters=parameters,
            status=JobStatus.PENDING,
            scheduled_time=scheduled_time or datetime.utcnow()
        )
        
        # Add priority to metadata
        job.metadata['priority'] = job_priority.value
        job.metadata['created_by'] = parameters.get('user_id', 'system')
        job.metadata['retry_count'] = 0
        job.metadata['max_retries'] = 3
        
        # Save job
        created_job = await self._job_repository.create(job)
        
        # If job should start immediately, queue it
        if not scheduled_time or scheduled_time <= datetime.utcnow():
            await self._queue_job(created_job)
        
        return created_job
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get detailed status of a generation job"""
        if not job_id:
            raise ValueError("Job ID is required")
        
        job = await self._job_repository.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
        
        status_info = {
            'job_id': job.id,
            'content_type': job.content_type.value,
            'course_id': job.course_id,
            'status': job.status.value,
            'created_at': job.created_at,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
            'progress_percentage': job.progress_percentage,
            'error_message': job.error_message,
            'priority': job.metadata.get('priority', 'normal'),
            'retry_count': job.metadata.get('retry_count', 0),
            'estimated_completion': self._estimate_completion_time(job)
        }
        
        # Add running job info if applicable
        if job.id in self._running_jobs:
            task = self._running_jobs[job.id]
            status_info['is_running'] = not task.done()
            status_info['time_running'] = (datetime.utcnow() - job.started_at).total_seconds() if job.started_at else 0
        
        return status_info
    
    async def cancel_job(self, job_id: str, reason: str = None) -> bool:
        """Cancel a pending or running job"""
        if not job_id:
            raise ValueError("Job ID is required")
        
        job = await self._job_repository.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
        
        # Check if job can be cancelled
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False
        
        # Cancel running task if exists
        if job_id in self._running_jobs:
            task = self._running_jobs[job_id]
            task.cancel()
            del self._running_jobs[job_id]
        
        # Update job status
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        job.error_message = reason or "Job cancelled by user"
        
        await self._job_repository.update(job)
        return True
    
    async def retry_failed_job(self, job_id: str) -> GenerationJob:
        """Retry a failed job"""
        if not job_id:
            raise ValueError("Job ID is required")
        
        job = await self._job_repository.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
        
        if job.status != JobStatus.FAILED:
            raise ValueError(f"Job {job_id} is not in failed state")
        
        retry_count = job.metadata.get('retry_count', 0)
        max_retries = job.metadata.get('max_retries', 3)
        
        if retry_count >= max_retries:
            raise ValueError(f"Job {job_id} has exceeded maximum retry attempts")
        
        # Reset job for retry
        job.status = JobStatus.PENDING
        job.started_at = None
        job.completed_at = None
        job.progress_percentage = 0
        job.error_message = None
        job.result = None
        job.metadata['retry_count'] = retry_count + 1
        job.metadata['last_retry_at'] = datetime.utcnow().isoformat()
        
        # Save and queue job
        updated_job = await self._job_repository.update(job)
        await self._queue_job(updated_job)
        
        return updated_job
    
    async def get_jobs_by_course(self, course_id: str, status_filter: Optional[str] = None,
                                limit: int = 50) -> List[GenerationJob]:
        """Get jobs for a specific course"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        jobs = await self._job_repository.get_by_course_id(course_id)
        
        # Filter by status if specified
        if status_filter:
            try:
                status_enum = JobStatus(status_filter.lower())
                jobs = [job for job in jobs if job.status == status_enum]
            except ValueError:
                raise ValueError(f"Invalid status filter: {status_filter}")
        
        # Sort by created date (newest first) and limit
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[:limit]
    
    async def get_job_queue_status(self) -> Dict[str, Any]:
        """Get overall status of the job queue"""
        pending_jobs = await self._job_repository.get_pending_jobs(limit=100)
        
        # Count jobs by priority
        priority_counts = {'low': 0, 'normal': 0, 'high': 0, 'urgent': 0}
        for job in pending_jobs:
            priority = job.metadata.get('priority', 'normal')
            priority_counts[priority] += 1
        
        # Count jobs by content type
        content_type_counts = {}
        for job in pending_jobs:
            content_type = job.content_type.value
            content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
        
        return {
            'total_pending': len(pending_jobs),
            'running_jobs': len(self._running_jobs),
            'max_concurrent': self._max_concurrent_jobs,
            'priority_breakdown': priority_counts,
            'content_type_breakdown': content_type_counts,
            'average_wait_time_minutes': self._calculate_average_wait_time(pending_jobs),
            'estimated_queue_completion': self._estimate_queue_completion_time(pending_jobs)
        }
    
    async def process_job_queue(self) -> None:
        """Process pending jobs in the queue"""
        # Get pending jobs sorted by priority and creation time
        pending_jobs = await self._get_prioritized_pending_jobs()
        
        for job in pending_jobs:
            # Check if we've reached the concurrent job limit
            if len(self._running_jobs) >= self._max_concurrent_jobs:
                break
            
            # Check if job is scheduled for the future
            if job.scheduled_time and job.scheduled_time > datetime.utcnow():
                continue
            
            # Start processing the job
            await self._queue_job(job)
    
    async def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed jobs"""
        if days_old <= 0:
            raise ValueError("Days old must be positive")
        
        return await self._job_repository.cleanup_old_jobs(days_old)
    
    async def get_job_statistics(self, time_period_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive job statistics"""
        if time_period_days <= 0:
            raise ValueError("Time period must be positive")
        
        return await self._job_repository.get_job_statistics(time_period_days)
    
    # Helper methods
    async def _queue_job(self, job: GenerationJob) -> None:
        """Queue a job for processing"""
        if job.id in self._running_jobs:
            return  # Job already running
        
        # Create processing task
        task = asyncio.create_task(self._process_job(job))
        self._running_jobs[job.id] = task
        
        # Set up task completion callback
        task.add_done_callback(lambda t: self._on_job_completed(job.id, t))
    
    async def _process_job(self, job: GenerationJob) -> None:
        """Process a single job"""
        try:
            # Update job status to running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.progress_percentage = 0
            await self._job_repository.update(job)
            
            # Set up timeout
            timeout_seconds = self._job_timeout_minutes * 60
            
            # Process job based on content type
            async with asyncio.timeout(timeout_seconds):
                result = await self._execute_job(job)
            
            # Job completed successfully
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress_percentage = 100
            job.result = result
            
        except asyncio.TimeoutError:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = f"Job timed out after {self._job_timeout_minutes} minutes"
            
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.error_message = "Job was cancelled"
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            
        finally:
            # Save final job state
            await self._job_repository.update(job)
    
    async def _execute_job(self, job: GenerationJob) -> Dict[str, Any]:
        """Execute the actual job processing"""
        # This would delegate to the appropriate service based on content type
        # For now, simulate job processing
        
        # Update progress periodically
        for progress in [25, 50, 75, 90]:
            await asyncio.sleep(1)  # Simulate work
            job.progress_percentage = progress
            await self._job_repository.update(job)
        
        # Simulate final result
        return {
            'content_type': job.content_type.value,
            'course_id': job.course_id,
            'generated_content': f"Generated {job.content_type.value} content",
            'processing_time_seconds': (datetime.utcnow() - job.started_at).total_seconds(),
            'metadata': job.metadata
        }
    
    def _on_job_completed(self, job_id: str, task: asyncio.Task) -> None:
        """Callback when job task is completed"""
        if job_id in self._running_jobs:
            del self._running_jobs[job_id]
    
    async def _get_prioritized_pending_jobs(self) -> List[GenerationJob]:
        """Get pending jobs sorted by priority and creation time"""
        pending_jobs = await self._job_repository.get_pending_jobs(limit=50)
        
        # Define priority order
        priority_order = {'urgent': 0, 'high': 1, 'normal': 2, 'low': 3}
        
        # Sort by priority first, then by creation time
        pending_jobs.sort(key=lambda job: (
            priority_order.get(job.metadata.get('priority', 'normal'), 2),
            job.created_at
        ))
        
        return pending_jobs
    
    def _estimate_completion_time(self, job: GenerationJob) -> Optional[datetime]:
        """Estimate when a job will complete"""
        if job.status == JobStatus.COMPLETED:
            return job.completed_at
        
        if job.status == JobStatus.RUNNING and job.started_at:
            # Estimate based on progress
            if job.progress_percentage > 0:
                elapsed = (datetime.utcnow() - job.started_at).total_seconds()
                estimated_total = elapsed * (100 / job.progress_percentage)
                return job.started_at + timedelta(seconds=estimated_total)
        
        # For pending jobs, estimate based on queue position
        if job.status == JobStatus.PENDING:
            # This would need more sophisticated logic based on queue analysis
            return datetime.utcnow() + timedelta(minutes=10)  # Simple estimate
        
        return None
    
    def _calculate_average_wait_time(self, pending_jobs: List[GenerationJob]) -> float:
        """Calculate average wait time for pending jobs"""
        if not pending_jobs:
            return 0.0
        
        total_wait_time = 0
        for job in pending_jobs:
            wait_time = (datetime.utcnow() - job.created_at).total_seconds() / 60  # Convert to minutes
            total_wait_time += wait_time
        
        return total_wait_time / len(pending_jobs)
    
    def _estimate_queue_completion_time(self, pending_jobs: List[GenerationJob]) -> Optional[datetime]:
        """Estimate when all pending jobs will be completed"""
        if not pending_jobs:
            return datetime.utcnow()
        
        # Simple estimation: assume average job takes 5 minutes
        # and we can process max_concurrent_jobs simultaneously
        avg_job_time_minutes = 5
        total_jobs = len(pending_jobs)
        concurrent_capacity = self._max_concurrent_jobs
        
        estimated_minutes = (total_jobs / concurrent_capacity) * avg_job_time_minutes
        return datetime.utcnow() + timedelta(minutes=estimated_minutes)