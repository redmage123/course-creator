#!/usr/bin/env python3
"""
Course Generator Service - Fixed Hydra Configuration
"""
import logging
import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from omegaconf import DictConfig
import hydra
from pydantic import BaseModel
from datetime import datetime
import uvicorn

# Models
class CourseTemplate(BaseModel):
    id: str
    name: str
    description: str
    parameters: Dict

class GenerateCourseRequest(BaseModel):
    template_id: str
    parameters: Dict

class Job(BaseModel):
    id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Dict]

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    # Logging setup
    logging.basicConfig(
        level=cfg.log.level,
        format=cfg.log.format
    )
    logger = logging.getLogger(__name__)
    
    # FastAPI app
    app = FastAPI(
        title="Course Generator API",
        description="API for generating courses from templates",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # In-memory storage for demo
    templates = {
        "basic": {
            "id": "basic",
            "name": "Basic Course Template",
            "description": "Simple course structure",
            "parameters": {"title": "string", "duration": "integer"}
        }
    }
    jobs = {}
    
    @app.get("/")
    async def root():
        return {"message": "Course Generator Service"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now()}
    
    @app.get("/templates")
    async def get_templates():
        return {"templates": list(templates.values())}
    
    @app.post("/generate")
    async def generate_course(request: GenerateCourseRequest):
        logger.info(f"Generating course with template: {request.template_id}")
        
        if request.template_id not in templates:
            raise HTTPException(status_code=404, detail="Template not found")
        
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            status="completed",
            created_at=datetime.now(),
            completed_at=datetime.now(),
            result={"course_id": f"course_{job_id[:8]}", "title": request.parameters.get("title", "Generated Course")}
        )
        jobs[job_id] = job
        
        return {"job_id": job_id, "status": "completed", "result": job.result}
    
    @app.get("/jobs/{job_id}")
    async def get_job(job_id: str):
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        return jobs[job_id]
    
    # Error handling
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Start the server
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, reload=cfg.server.reload)

if __name__ == "__main__":
    main()