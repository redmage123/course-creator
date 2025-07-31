"""
Lab Container Management Service - Refactored using SOLID principles
Single Responsibility: API layer only - business logic delegated to services
Open/Closed: Extensible through dependency injection
Liskov Substitution: Uses interface abstractions
Interface Segregation: Clean, focused interfaces
Dependency Inversion: Depends on abstractions, not concretions
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from logging_setup import setup_docker_logging
except ImportError:
    # Fallback if config module not available
    def setup_docker_logging(service_name: str, log_level: str = "INFO"):
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s'
        )
        return logging.getLogger(service_name)

# Import modular services
from services.docker_service import DockerService
from services.lab_lifecycle_service import LabLifecycleService
from models.lab_models import (
    LabRequest, LabResponse, StudentLabRequest, LabListResponse,
    LabEnvironment, LabHealthCheck, LabAnalytics
)

# Global services (initialized at startup)
docker_service: Optional[DockerService] = None
lab_lifecycle_service: Optional[LabLifecycleService] = None
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Lab Container Management Service",
    description="Manages individual Docker containers for student lab environments",
    version="2.1.0"
)

# API Models for requests/responses
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    active_labs: int

class LabStatusResponse(BaseModel):
    lab_id: str
    status: str
    ide_urls: Dict[str, str]
    created_at: datetime
    last_accessed: Optional[datetime]

# Dependency injection helpers
def get_docker_service() -> DockerService:
    """Get Docker service instance"""
    if not docker_service:
        raise HTTPException(status_code=500, detail="Docker service not initialized")
    return docker_service

def get_lab_lifecycle_service() -> LabLifecycleService:
    """Get Lab lifecycle service instance"""
    if not lab_lifecycle_service:
        raise HTTPException(status_code=500, detail="Lab lifecycle service not initialized")
    return lab_lifecycle_service

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    lifecycle_service = get_lab_lifecycle_service()
    active_count = len(lifecycle_service.active_labs)
    
    return HealthResponse(
        status="healthy",
        service="lab-containers",
        version="2.1.0",
        timestamp=datetime.utcnow(),
        active_labs=active_count
    )

# Lab Management Endpoints
@app.post("/labs", response_model=LabResponse)
async def create_lab(
    request: LabRequest,
    background_tasks: BackgroundTasks
):
    """Create a new lab container"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        
        # Convert LabRequest to StudentLabRequest for the service
        student_request = StudentLabRequest(
            course_id=request.course_id,
            config=None  # Use default config for now
        )
        
        # Create lab using lifecycle service
        result = await lifecycle_service.create_student_lab(
            student_id="instructor",  # Default for instructor labs
            request=student_request
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to create lab: %s", e)
        raise HTTPException(status_code=500, detail=f"Lab creation failed: {str(e)}") from e

@app.post("/labs/student", response_model=LabResponse)
async def create_student_lab(
    request: StudentLabRequest,
    user_id: str = Query(..., description="Student user ID")
):
    """Create or retrieve student lab container"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.create_student_lab(user_id, request)
        return result
        
    except Exception as e:
        logger.error("Failed to create student lab: %s", e)
        raise HTTPException(status_code=500, detail=f"Student lab creation failed: {str(e)}") from e

@app.get("/labs", response_model=LabListResponse)
async def list_labs():
    """List all active lab containers"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        labs = list(lifecycle_service.active_labs.values())
        
        return LabListResponse(
            labs=labs,
            total_count=len(labs)
        )
        
    except Exception as e:
        logger.error("Failed to list labs: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to list labs: {str(e)}") from e

@app.get("/labs/{lab_id}", response_model=LabStatusResponse)
async def get_lab_status(lab_id: str):
    """Get lab container status"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        lab = lifecycle_service.get_lab_status(lab_id)
        
        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")
        
        return LabStatusResponse(
            lab_id=lab.id,
            status=lab.status.value,
            ide_urls=lab.ide_urls,
            created_at=lab.created_at,
            last_accessed=lab.last_accessed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get lab status: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get lab status: {str(e)}") from e

@app.post("/labs/{lab_id}/pause", response_model=LabResponse)
async def pause_lab(lab_id: str):
    """Pause a lab container"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.pause_lab(lab_id)
        return result
        
    except Exception as e:
        logger.error("Failed to pause lab: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to pause lab: {str(e)}") from e

@app.post("/labs/{lab_id}/resume", response_model=LabResponse)
async def resume_lab(lab_id: str):
    """Resume a paused lab container"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.resume_lab(lab_id)
        return result
        
    except Exception as e:
        logger.error("Failed to resume lab: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to resume lab: {str(e)}") from e

@app.delete("/labs/{lab_id}", response_model=LabResponse)
async def delete_lab(lab_id: str):
    """Delete a lab container"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.delete_lab(lab_id)
        return result
        
    except Exception as e:
        logger.error("Failed to delete lab: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to delete lab: {str(e)}") from e

@app.get("/labs/instructor/{course_id}")
async def get_instructor_lab_overview(course_id: str):
    """Get lab overview for instructors"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        labs = lifecycle_service.list_course_labs(course_id)
        
        # Generate summary statistics
        total_labs = len(labs)
        active_labs = len([lab for lab in labs if lab.status.value == "running"])
        
        return {
            "course_id": course_id,
            "total_labs": total_labs,
            "active_labs": active_labs,
            "labs": [
                {
                    "lab_id": lab.id,
                    "student_id": lab.student_id,
                    "status": lab.status.value,
                    "created_at": lab.created_at,
                    "last_accessed": lab.last_accessed,
                    "ide_urls": lab.ide_urls
                }
                for lab in labs
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get instructor overview: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}") from e

# Cleanup endpoint for maintenance
@app.post("/labs/cleanup")
async def cleanup_idle_labs(max_idle_hours: int = Query(24, description="Max idle hours before cleanup")):
    """Clean up idle lab containers"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        cleaned_count = await lifecycle_service.cleanup_idle_labs(max_idle_hours)
        
        return {
            "message": f"Cleaned up {cleaned_count} idle labs",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error("Failed to cleanup labs: %s", e)
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}") from e

# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize the lab manager service"""
    global docker_service, lab_lifecycle_service
    
    logger.info("Lab Container Management Service starting up")
    
    try:
        # Initialize services
        docker_service = DockerService(logger)
        lab_lifecycle_service = LabLifecycleService(docker_service, logger)
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services: %s", e)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Lab Container Management Service shutting down")
    
    try:
        if lab_lifecycle_service:
            # Clean up all active labs
            lab_ids = list(lab_lifecycle_service.active_labs.keys())
            for lab_id in lab_ids:
                try:
                    await lab_lifecycle_service.delete_lab(lab_id)
                except Exception as e:
                    logger.error("Error cleaning up lab during shutdown: %s", e)
        
        logger.info("Shutdown complete")
        
    except Exception as e:
        logger.error("Error during shutdown: %s", e)

if __name__ == "__main__":
    import uvicorn
    
    # Setup centralized logging with syslog format
    service_name = os.environ.get('SERVICE_NAME', 'lab-containers')
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    
    logger = setup_docker_logging(service_name, log_level)
    logger.info("Starting Lab Container Management Service on port 8006")
    
    # Run server with reduced uvicorn logging to avoid duplicates
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8006,
        log_level="warning",  # Reduce uvicorn log level since we have our own logging
        access_log=False      # Disable uvicorn access log since we log via middleware
    )