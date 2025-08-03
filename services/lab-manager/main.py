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

import hydra
from omegaconf import DictConfig
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

# Import RAG-enhanced lab assistant
from rag_lab_assistant import (
    RAGLabAssistant, AssistanceRequest, AssistanceResponse,
    CodeContext, StudentContext, AssistanceType, SkillLevel,
    get_programming_help, rag_lab_assistant
)

# Custom exceptions
from exceptions import (
    LabContainerException, DockerServiceException, LabCreationException,
    LabNotFoundException, LabLifecycleException, IDEServiceException,
    ResourceLimitException, ValidationException, ServiceInitializationException,
    ContainerImageException, NetworkException
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

# Exception type to HTTP status code mapping (Open/Closed Principle)
EXCEPTION_STATUS_MAPPING = {
    ValidationException: 400,
    LabNotFoundException: 404,
    ResourceLimitException: 409,
    LabCreationException: 422,
    LabLifecycleException: 422,
    IDEServiceException: 422,
    ContainerImageException: 422,
    NetworkException: 422,
    DockerServiceException: 500,
    ServiceInitializationException: 500,
}

# Custom exception handler
@app.exception_handler(LabContainerException)
async def lab_container_exception_handler(request, exc: LabContainerException):
    """Handle custom lab container exceptions."""
    # Use mapping to determine status code (extensible design)
    status_code = next(
        (code for exc_type, code in EXCEPTION_STATUS_MAPPING.items() if isinstance(exc, exc_type)),
        500  # Default status code
    )
        
    response_data = exc.to_dict()
    response_data["path"] = str(request.url)
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
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

# RAG Lab Assistant API Models
class ProgrammingHelpRequest(BaseModel):
    code: str
    language: str
    question: str
    error_message: Optional[str] = None
    student_id: str = "anonymous"
    skill_level: str = "intermediate"

class AssistantStatsResponse(BaseModel):
    assistant_stats: Dict[str, int]
    rag_service_stats: Dict
    timestamp: str

# Dependency injection helpers
def get_docker_service() -> DockerService:
    """Get Docker service instance"""
    if not docker_service:
        raise ServiceInitializationException(
            message="Docker service not initialized",
            service_name="docker_service",
            initialization_stage="startup"
        )
    return docker_service

def get_lab_lifecycle_service() -> LabLifecycleService:
    """Get Lab lifecycle service instance"""
    if not lab_lifecycle_service:
        raise ServiceInitializationException(
            message="Lab lifecycle service not initialized",
            service_name="lab_lifecycle_service",
            initialization_stage="startup"
        )
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
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabCreationException(
            message="Failed to create lab container",
            course_id=request.course_id,
            lab_type="instructor_lab",
            original_exception=e
        )

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
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabCreationException(
            message="Failed to create student lab container",
            student_id=user_id,
            course_id=request.course_id,
            lab_type="student_lab",
            original_exception=e
        )

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
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabLifecycleException(
            message="Failed to list lab containers",
            operation="list_labs",
            original_exception=e
        )

@app.get("/labs/{lab_id}", response_model=LabStatusResponse)
async def get_lab_status(lab_id: str):
    """Get lab container status"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        lab = lifecycle_service.get_lab_status(lab_id)
        
        if not lab:
            raise LabNotFoundException(
                message="Lab container not found",
                lab_id=lab_id
            )
        
        return LabStatusResponse(
            lab_id=lab.id,
            status=lab.status.value,
            ide_urls=lab.ide_urls,
            created_at=lab.created_at,
            last_accessed=lab.last_accessed
        )
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabLifecycleException(
            message="Failed to retrieve lab status",
            lab_id=lab_id,
            operation="get_lab_status",
            original_exception=e
        )

@app.post("/labs/{lab_id}/pause", response_model=LabResponse)
async def pause_lab(lab_id: str):
    """Pause a lab container"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.pause_lab(lab_id)
        return result
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabLifecycleException(
            message="Failed to pause lab container",
            lab_id=lab_id,
            operation="pause_lab",
            target_status="paused",
            original_exception=e
        )

@app.post("/labs/{lab_id}/resume", response_model=LabResponse)
async def resume_lab(lab_id: str):
    """Resume a paused lab container"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.resume_lab(lab_id)
        return result
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabLifecycleException(
            message="Failed to resume lab container",
            lab_id=lab_id,
            operation="resume_lab",
            target_status="running",
            original_exception=e
        )

@app.delete("/labs/{lab_id}", response_model=LabResponse)
async def delete_lab(lab_id: str):
    """Delete a lab container"""
    try:
        lifecycle_service = get_lab_lifecycle_service()
        result = await lifecycle_service.delete_lab(lab_id)
        return result
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabLifecycleException(
            message="Failed to delete lab container",
            lab_id=lab_id,
            operation="delete_lab",
            target_status="deleted",
            original_exception=e
        )

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
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabLifecycleException(
            message="Failed to retrieve instructor lab overview",
            course_id=course_id,
            operation="get_instructor_overview",
            original_exception=e
        )

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
        
    except LabContainerException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LabLifecycleException(
            message="Failed to cleanup idle lab containers",
            operation="cleanup_idle_labs",
            original_exception=e
        )

# RAG-Enhanced Lab Assistant Endpoints
@app.post("/assistant/help", response_model=AssistanceResponse)
async def get_programming_assistance(request: ProgrammingHelpRequest):
    """
    Get RAG-enhanced programming assistance for lab environments
    
    INTELLIGENT ASSISTANCE FEATURES:
    - Context-aware help based on code and error analysis
    - Progressive learning from successful solutions
    - Personalized assistance adapted to student skill level
    - Multi-language programming support with specialized knowledge
    """
    try:
        # Use the convenience function for simple integration
        response = await get_programming_help(
            code=request.code,
            language=request.language,
            question=request.question,
            error_message=request.error_message,
            student_id=request.student_id,
            skill_level=request.skill_level
        )
        
        logger.info(f"Provided programming assistance for {request.language} to student {request.student_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to provide programming assistance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Programming assistance failed: {str(e)}"
        )

@app.get("/assistant/stats", response_model=AssistantStatsResponse)
async def get_assistant_statistics():
    """
    Get RAG lab assistant performance statistics and metrics
    
    PERFORMANCE INSIGHTS:
    - Total assistance requests and success rates
    - RAG enhancement effectiveness metrics  
    - Learning operation success tracking
    - Service health and availability status
    """
    try:
        stats = await rag_lab_assistant.get_assistance_stats()
        return AssistantStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get assistant statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Statistics retrieval failed: {str(e)}"
        )

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
        raise ServiceInitializationException(
            message="Failed to initialize lab container services",
            initialization_stage="startup",
            original_exception=e
        )

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

# Global variables for configuration
current_config: Optional[DictConfig] = None

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point using Hydra configuration"""
    global current_config
    current_config = cfg
    
    # Setup centralized logging with syslog format
    service_name = os.environ.get('SERVICE_NAME', 'lab-containers')
    log_level = os.environ.get('LOG_LEVEL', cfg.logging.level)
    
    logger = setup_docker_logging(service_name, log_level)
    logger.info(f"Starting {cfg.name} on {cfg.host}:{cfg.port}")
    
    # Initialize services with configuration
    global docker_service, lab_lifecycle_service
    docker_service = DockerService(logger, cfg.docker)
    lab_lifecycle_service = LabLifecycleService(docker_service, logger, cfg.lab)
    
    # Run server with configuration
    import uvicorn
    uvicorn.run(
        app,
        host=cfg.host,
        port=cfg.port,
        log_level="warning",  # Reduce uvicorn log level since we have our own logging
        access_log=False      # Disable uvicorn access log since we log via middleware
    )

if __name__ == "__main__":
    main()