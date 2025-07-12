"""
Content Management Service - FastAPI Application
Handles file upload, processing, AI integration, and multi-format export
"""

import os
import uuid
import asyncio
import json
import mimetypes
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiofiles

# Import processing modules
from file_processors import SyllabusProcessor, SlidesProcessor, ExportProcessor
from ai_integration import AIContentGenerator
from storage_manager import StorageManager
from models import ContentType, ProcessingStatus, ExportFormat

# Initialize FastAPI app
app = FastAPI(
    title="Content Management Service",
    description="Handles file upload, processing, and export for Course Creator Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors and managers
storage_manager = StorageManager()
syllabus_processor = SyllabusProcessor()
slides_processor = SlidesProcessor()
export_processor = ExportProcessor()
ai_generator = AIContentGenerator()

# Request models
class ContentGenerationRequest(BaseModel):
    generate_slides: bool = True
    generate_exercises: bool = True
    generate_quizzes: bool = True
    generate_labs: bool = True

class CustomGenerationRequest(BaseModel):
    prompt: str
    content_type: str

class ExportRequest(BaseModel):
    course_id: str
    format: str

# Response models
class UploadResponse(BaseModel):
    success: bool
    message: str
    file_id: str
    processing_id: Optional[str] = None

class ProcessingStatusResponse(BaseModel):
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    result: Optional[Dict[str, Any]] = None

# Global processing status storage
processing_status = {}

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "content-management",
        "timestamp": datetime.utcnow()
    }

# ===================================
# FILE UPLOAD ENDPOINTS
# ===================================

@app.post("/api/content/upload", response_model=UploadResponse)
async def upload_content(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    type: str = Form(...),
    process_with_ai: bool = Form(False)
):
    """Upload and process content files"""
    try:
        # Validate file type
        if not validate_file_type(file.filename, type):
            raise HTTPException(status_code=400, detail="Invalid file type for content type")
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Save file to storage
        file_path = await storage_manager.save_file(file, file_id, type)
        
        # Initialize response
        response = UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=file_id
        )
        
        # Process with AI if requested
        if process_with_ai and type == "syllabus":
            processing_id = str(uuid.uuid4())
            response.processing_id = processing_id
            response.message = "File uploaded successfully. AI processing started."
            
            # Start background processing
            background_tasks.add_task(
                process_syllabus_with_ai,
                file_path,
                file_id,
                processing_id
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/content/upload/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    type: str = Form(...)
):
    """Upload multiple files (for materials)"""
    try:
        uploaded_files = []
        
        for file in files:
            if not validate_file_type(file.filename, type):
                continue  # Skip invalid files
            
            file_id = str(uuid.uuid4())
            file_path = await storage_manager.save_file(file, file_id, type)
            
            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "path": str(file_path)
            })
        
        return {
            "success": True,
            "message": f"Uploaded {len(uploaded_files)} files successfully",
            "files": uploaded_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ===================================
# AI PROCESSING ENDPOINTS
# ===================================

@app.post("/api/content/generate/from-syllabus")
async def generate_from_syllabus(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate course content from uploaded syllabus"""
    try:
        processing_id = str(uuid.uuid4())
        
        # Initialize processing status
        processing_status[processing_id] = {
            "status": "pending",
            "progress": 0,
            "message": "Starting content generation from syllabus"
        }
        
        # Start background processing
        background_tasks.add_task(
            generate_content_from_syllabus,
            processing_id,
            request
        )
        
        return {
            "success": True,
            "message": "Content generation started",
            "processing_id": processing_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/api/content/generate/custom")
async def generate_custom_content(
    request: CustomGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate custom content based on prompt"""
    try:
        processing_id = str(uuid.uuid4())
        
        # Initialize processing status
        processing_status[processing_id] = {
            "status": "pending",
            "progress": 0,
            "message": f"Starting custom {request.content_type} generation"
        }
        
        # Start background processing
        background_tasks.add_task(
            generate_custom_content_task,
            processing_id,
            request
        )
        
        return {
            "success": True,
            "message": "Custom content generation started",
            "processing_id": processing_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/api/content/processing/{processing_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(processing_id: str):
    """Get the status of a processing task"""
    if processing_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    
    status_data = processing_status[processing_id]
    return ProcessingStatusResponse(**status_data)

# ===================================
# EXPORT ENDPOINTS
# ===================================

@app.post("/api/content/export/slides")
async def export_slides(request: ExportRequest):
    """Export course slides in specified format"""
    try:
        # Get course content
        course_data = await get_course_data(request.course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Generate export file
        export_file = await export_processor.export_slides(
            course_data,
            ExportFormat(request.format)
        )
        
        # Return file
        return FileResponse(
            export_file,
            media_type=get_media_type(request.format),
            filename=f"slides_{request.course_id}.{get_file_extension(request.format)}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/api/content/export/exercises")
async def export_exercises(request: ExportRequest):
    """Export course exercises in specified format"""
    try:
        course_data = await get_course_data(request.course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Course not found")
        
        export_file = await export_processor.export_exercises(
            course_data,
            ExportFormat(request.format)
        )
        
        return FileResponse(
            export_file,
            media_type=get_media_type(request.format),
            filename=f"exercises_{request.course_id}.{get_file_extension(request.format)}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/api/content/export/quizzes")
async def export_quizzes(request: ExportRequest):
    """Export course quizzes in specified format"""
    try:
        course_data = await get_course_data(request.course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Course not found")
        
        export_file = await export_processor.export_quizzes(
            course_data,
            ExportFormat(request.format)
        )
        
        return FileResponse(
            export_file,
            media_type=get_media_type(request.format),
            filename=f"quizzes_{request.course_id}.{get_file_extension(request.format)}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/api/content/export/complete")
async def export_complete_course(request: ExportRequest):
    """Export complete course package"""
    try:
        course_data = await get_course_data(request.course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Course not found")
        
        export_file = await export_processor.export_complete_course(
            course_data,
            ExportFormat(request.format)
        )
        
        return FileResponse(
            export_file,
            media_type=get_media_type(request.format),
            filename=f"course_complete_{request.course_id}.{get_file_extension(request.format)}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# ===================================
# HELPER FUNCTIONS
# ===================================

def validate_file_type(filename: str, content_type: str) -> bool:
    """Validate file type based on content type"""
    if not filename:
        return False
    
    file_ext = Path(filename).suffix.lower()
    
    allowed_types = {
        "syllabus": [".pdf", ".doc", ".docx", ".txt"],
        "slides": [".ppt", ".pptx", ".pdf", ".json"],
        "materials": [".pdf", ".doc", ".docx", ".zip", ".jpg", ".png", ".mp4", ".mp3"]
    }
    
    return file_ext in allowed_types.get(content_type, [])

def get_media_type(format: str) -> str:
    """Get media type for export format"""
    media_types = {
        "powerpoint": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "json": "application/json",
        "pdf": "application/pdf",
        "zip": "application/zip",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "scorm": "application/zip"
    }
    return media_types.get(format, "application/octet-stream")

def get_file_extension(format: str) -> str:
    """Get file extension for export format"""
    extensions = {
        "powerpoint": "pptx",
        "json": "json",
        "pdf": "pdf",
        "zip": "zip",
        "excel": "xlsx",
        "scorm": "zip"
    }
    return extensions.get(format, "zip")

async def get_course_data(course_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve course data from database"""
    # This would typically query the database
    # For now, return mock data
    return {
        "id": course_id,
        "title": "Sample Course",
        "slides": [],
        "exercises": [],
        "quizzes": [],
        "modules": []
    }

# ===================================
# BACKGROUND TASKS
# ===================================

async def process_syllabus_with_ai(file_path: str, file_id: str, processing_id: str):
    """Background task to process syllabus with AI"""
    try:
        # Update status
        processing_status[processing_id] = {
            "status": "processing",
            "progress": 10,
            "message": "Extracting content from syllabus"
        }
        
        # Extract text from syllabus
        syllabus_content = await syllabus_processor.extract_text(file_path)
        
        processing_status[processing_id]["progress"] = 30
        processing_status[processing_id]["message"] = "Analyzing syllabus structure"
        
        # Analyze syllabus structure
        syllabus_analysis = await syllabus_processor.analyze_structure(syllabus_content)
        
        processing_status[processing_id]["progress"] = 50
        processing_status[processing_id]["message"] = "Generating course outline"
        
        # Generate course outline
        course_outline = await ai_generator.generate_course_outline(syllabus_analysis)
        
        processing_status[processing_id]["progress"] = 100
        processing_status[processing_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Syllabus processing completed",
            "result": {
                "syllabus_analysis": syllabus_analysis,
                "course_outline": course_outline
            }
        }
        
    except Exception as e:
        processing_status[processing_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"Processing failed: {str(e)}"
        }

async def generate_content_from_syllabus(processing_id: str, request: ContentGenerationRequest):
    """Background task to generate content from syllabus"""
    try:
        processing_status[processing_id]["status"] = "processing"
        processing_status[processing_id]["progress"] = 10
        
        # Get the latest syllabus analysis
        syllabus_data = await get_latest_syllabus_analysis()
        
        if not syllabus_data:
            raise Exception("No syllabus found. Please upload a syllabus first.")
        
        results = {}
        total_tasks = sum([request.generate_slides, request.generate_exercises, 
                          request.generate_quizzes, request.generate_labs])
        completed_tasks = 0
        
        if request.generate_slides:
            processing_status[processing_id]["message"] = "Generating slides"
            results["slides"] = await ai_generator.generate_slides(syllabus_data)
            completed_tasks += 1
            processing_status[processing_id]["progress"] = int((completed_tasks / total_tasks) * 80)
        
        if request.generate_exercises:
            processing_status[processing_id]["message"] = "Generating exercises"
            results["exercises"] = await ai_generator.generate_exercises(syllabus_data)
            completed_tasks += 1
            processing_status[processing_id]["progress"] = int((completed_tasks / total_tasks) * 80)
        
        if request.generate_quizzes:
            processing_status[processing_id]["message"] = "Generating quizzes"
            results["quizzes"] = await ai_generator.generate_quizzes(syllabus_data)
            completed_tasks += 1
            processing_status[processing_id]["progress"] = int((completed_tasks / total_tasks) * 80)
        
        if request.generate_labs:
            processing_status[processing_id]["message"] = "Generating lab environment"
            results["labs"] = await ai_generator.generate_lab_environment(syllabus_data)
            completed_tasks += 1
            processing_status[processing_id]["progress"] = int((completed_tasks / total_tasks) * 80)
        
        processing_status[processing_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Content generation completed",
            "result": results
        }
        
    except Exception as e:
        processing_status[processing_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"Generation failed: {str(e)}"
        }

async def generate_custom_content_task(processing_id: str, request: CustomGenerationRequest):
    """Background task to generate custom content"""
    try:
        processing_status[processing_id]["status"] = "processing"
        processing_status[processing_id]["progress"] = 20
        processing_status[processing_id]["message"] = f"Generating {request.content_type}"
        
        # Generate content based on type
        if request.content_type == "slides":
            result = await ai_generator.generate_custom_slides(request.prompt)
        elif request.content_type == "exercises":
            result = await ai_generator.generate_custom_exercises(request.prompt)
        elif request.content_type == "quizzes":
            result = await ai_generator.generate_custom_quizzes(request.prompt)
        elif request.content_type == "lab":
            result = await ai_generator.generate_custom_lab(request.prompt)
        else:
            result = await ai_generator.generate_mixed_content(request.prompt)
        
        processing_status[processing_id] = {
            "status": "completed",
            "progress": 100,
            "message": f"Custom {request.content_type} generation completed",
            "result": result
        }
        
    except Exception as e:
        processing_status[processing_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"Generation failed: {str(e)}"
        }

async def get_latest_syllabus_analysis():
    """Get the most recent syllabus analysis"""
    # This would typically query the database for the latest syllabus
    # For now, return mock data
    return {
        "topics": ["Introduction", "Basic Concepts", "Advanced Topics"],
        "learning_objectives": ["Understand basics", "Apply concepts", "Master skills"],
        "assessment_methods": ["Quizzes", "Projects", "Final Exam"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)