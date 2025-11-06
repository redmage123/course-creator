#!/usr/bin/env python3

# Load environment variables from .cc_env file if present
import os
if os.path.exists('/app/shared/.cc_env'):
    with open('/app/shared/.cc_env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value

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
    CourseCreatorBaseException,
    ContentException,
    ContentNotFoundException,
    ContentValidationException,
    FileStorageException,
    ValidationException,
    DatabaseException,
    AuthenticationException,
    AuthorizationException,
    ConfigurationException,
    APIException,
    BusinessRuleException
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

# Include modular routers (following Open/Closed Principle)
from api import lab_lifecycle_router, rag_assistant_router
app.include_router(lab_lifecycle_router)
app.include_router(rag_assistant_router)

# Exception type to HTTP status code mapping (Open/Closed Principle)
EXCEPTION_STATUS_MAPPING = {
    ValidationException: 400,
    ContentNotFoundException: 404,
    APIException: 409,
    APIException: 422,
    ContentException: 422,
    ValidationException: 400,
    ConfigurationException: 500,
}

# Custom exception handler
@app.exception_handler(ContentException)
async def lab_container_exception_handler(request, exc: ContentException):
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
        raise ConfigurationException(
            message="Docker service not initialized",
            error_code="SERVICE_INIT_ERROR",
            details={"service_name": "docker_service", "initialization_stage": "startup"}
        )
    return docker_service

def get_lab_lifecycle_service() -> LabLifecycleService:
    """Get Lab lifecycle service instance"""
    if not lab_lifecycle_service:
        raise ConfigurationException(
            message="Lab lifecycle service not initialized",
            error_code="SERVICE_INIT_ERROR",
            details={"service_name": "lab_lifecycle_service", "initialization_stage": "startup"}
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

# All lab and assistant endpoints extracted to routers
# See api/lab_lifecycle_endpoints.py and api/rag_assistant_endpoints.py

# Application lifecycle events
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
        raise ConfigurationException(
            message="Failed to initialize lab container services",
            error_code="SERVICE_INIT_ERROR",
            details={"initialization_stage": "startup"},
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
    
    # Run server with HTTPS/SSL configuration
    import uvicorn
    uvicorn.run(
        app,
        host=cfg.host,
        port=cfg.port,
        log_level="warning",  # Reduce uvicorn log level since we have our own logging
        access_log=False,     # Disable uvicorn access log since we log via middleware
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt"
    )

if __name__ == "__main__":
    main()