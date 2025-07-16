"""
Content Management Service - FastAPI Application (Refactored)

This module provides the main FastAPI application for the content management service,
following SOLID principles with proper dependency injection and modular architecture.
"""

import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import uvicorn

from models.common import (
    APIResponse, ErrorResponse, SuccessResponse, ContentType, 
    ExportFormat, ProcessingStatus, create_api_response, 
    create_error_response, create_success_response
)
from models.content import (
    SyllabusCreate, SyllabusUpdate, SyllabusResponse,
    SlideCreate, SlideUpdate, SlideResponse,
    QuizCreate, QuizUpdate, QuizResponse,
    ExerciseCreate, ExerciseUpdate, ExerciseResponse,
    LabEnvironmentCreate, LabEnvironmentUpdate, LabEnvironmentResponse,
    ContentGenerationRequest, CustomGenerationRequest
)
from repositories.content_repository import ContentRepository
from services.content_service import ContentService


class ContentManagementApp:
    """Main application class for content management service"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Content Management Service",
            description="Handles content creation, management, and processing for Course Creator Platform",
            version="2.0.0",
            lifespan=self.lifespan
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Application state
        self.db_pool = None
        self.content_repository = None
        self.content_service = None
        
        # Register routes
        self._register_routes()
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Application lifespan management"""
        # Startup
        await self._startup()
        yield
        # Shutdown
        await self._shutdown()
    
    async def _startup(self):
        """Initialize application dependencies"""
        # Initialize database connection
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://course_user:c0urs3:atao12e@localhost:5433/course_creator"
        )
        
        self.db_pool = await asyncpg.create_pool(database_url)
        
        # Initialize repositories and services
        self.content_repository = ContentRepository(self.db_pool)
        self.content_service = ContentService(self.content_repository)
        
        print("✅ Content Management Service started successfully")
    
    async def _shutdown(self):
        """Cleanup application resources"""
        if self.db_pool:
            await self.db_pool.close()
        print("✅ Content Management Service shutdown complete")
    
    def _register_routes(self):
        """Register all application routes"""
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return create_success_response(
                message="Content Management Service is healthy",
                data={
                    "service": "content-management",
                    "version": "2.0.0",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Syllabus endpoints
        @self.app.post("/api/v1/syllabi", response_model=SyllabusResponse)
        async def create_syllabus(
            syllabus_data: SyllabusCreate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Create a new syllabus"""
            try:
                syllabus = await self.content_service.create_syllabus(syllabus_data, current_user)
                return syllabus
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/syllabi/{syllabus_id}", response_model=SyllabusResponse)
        async def get_syllabus(syllabus_id: str):
            """Get syllabus by ID"""
            syllabus = await self.content_service.get_syllabus(syllabus_id)
            if not syllabus:
                raise HTTPException(status_code=404, detail="Syllabus not found")
            return syllabus
        
        @self.app.put("/api/v1/syllabi/{syllabus_id}", response_model=SyllabusResponse)
        async def update_syllabus(
            syllabus_id: str,
            updates: SyllabusUpdate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Update syllabus"""
            syllabus = await self.content_service.update_syllabus(syllabus_id, updates)
            if not syllabus:
                raise HTTPException(status_code=404, detail="Syllabus not found")
            return syllabus
        
        @self.app.delete("/api/v1/syllabi/{syllabus_id}")
        async def delete_syllabus(
            syllabus_id: str,
            current_user: str = Depends(self._get_current_user)
        ):
            """Delete syllabus"""
            success = await self.content_service.delete_syllabus(syllabus_id)
            if not success:
                raise HTTPException(status_code=404, detail="Syllabus not found")
            return create_success_response("Syllabus deleted successfully")
        
        @self.app.get("/api/v1/syllabi", response_model=List[SyllabusResponse])
        async def list_syllabi(
            course_id: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
        ):
            """List syllabi"""
            return await self.content_service.list_syllabi(course_id, limit, offset)
        
        # Slide endpoints
        @self.app.post("/api/v1/slides", response_model=SlideResponse)
        async def create_slide(
            slide_data: SlideCreate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Create a new slide"""
            try:
                slide = await self.content_service.create_slide(slide_data, current_user)
                return slide
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/slides/{slide_id}", response_model=SlideResponse)
        async def get_slide(slide_id: str):
            """Get slide by ID"""
            slide = await self.content_service.get_slide(slide_id)
            if not slide:
                raise HTTPException(status_code=404, detail="Slide not found")
            return slide
        
        @self.app.put("/api/v1/slides/{slide_id}", response_model=SlideResponse)
        async def update_slide(
            slide_id: str,
            updates: SlideUpdate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Update slide"""
            slide = await self.content_service.update_slide(slide_id, updates)
            if not slide:
                raise HTTPException(status_code=404, detail="Slide not found")
            return slide
        
        @self.app.delete("/api/v1/slides/{slide_id}")
        async def delete_slide(
            slide_id: str,
            current_user: str = Depends(self._get_current_user)
        ):
            """Delete slide"""
            success = await self.content_service.delete_slide(slide_id)
            if not success:
                raise HTTPException(status_code=404, detail="Slide not found")
            return create_success_response("Slide deleted successfully")
        
        @self.app.get("/api/v1/slides", response_model=List[SlideResponse])
        async def list_slides(
            course_id: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
        ):
            """List slides"""
            return await self.content_service.list_slides(course_id, limit, offset)
        
        # Quiz endpoints
        @self.app.post("/api/v1/quizzes", response_model=QuizResponse)
        async def create_quiz(
            quiz_data: QuizCreate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Create a new quiz"""
            try:
                quiz = await self.content_service.create_quiz(quiz_data, current_user)
                return quiz
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/quizzes/{quiz_id}", response_model=QuizResponse)
        async def get_quiz(quiz_id: str):
            """Get quiz by ID"""
            quiz = await self.content_service.get_quiz(quiz_id)
            if not quiz:
                raise HTTPException(status_code=404, detail="Quiz not found")
            return quiz
        
        @self.app.put("/api/v1/quizzes/{quiz_id}", response_model=QuizResponse)
        async def update_quiz(
            quiz_id: str,
            updates: QuizUpdate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Update quiz"""
            quiz = await self.content_service.update_quiz(quiz_id, updates)
            if not quiz:
                raise HTTPException(status_code=404, detail="Quiz not found")
            return quiz
        
        @self.app.delete("/api/v1/quizzes/{quiz_id}")
        async def delete_quiz(
            quiz_id: str,
            current_user: str = Depends(self._get_current_user)
        ):
            """Delete quiz"""
            success = await self.content_service.delete_quiz(quiz_id)
            if not success:
                raise HTTPException(status_code=404, detail="Quiz not found")
            return create_success_response("Quiz deleted successfully")
        
        @self.app.get("/api/v1/quizzes", response_model=List[QuizResponse])
        async def list_quizzes(
            course_id: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
        ):
            """List quizzes"""
            return await self.content_service.list_quizzes(course_id, limit, offset)
        
        # Exercise endpoints
        @self.app.post("/api/v1/exercises", response_model=ExerciseResponse)
        async def create_exercise(
            exercise_data: ExerciseCreate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Create a new exercise"""
            try:
                exercise = await self.content_service.create_exercise(exercise_data, current_user)
                return exercise
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/exercises/{exercise_id}", response_model=ExerciseResponse)
        async def get_exercise(exercise_id: str):
            """Get exercise by ID"""
            exercise = await self.content_service.get_exercise(exercise_id)
            if not exercise:
                raise HTTPException(status_code=404, detail="Exercise not found")
            return exercise
        
        @self.app.put("/api/v1/exercises/{exercise_id}", response_model=ExerciseResponse)
        async def update_exercise(
            exercise_id: str,
            updates: ExerciseUpdate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Update exercise"""
            exercise = await self.content_service.update_exercise(exercise_id, updates)
            if not exercise:
                raise HTTPException(status_code=404, detail="Exercise not found")
            return exercise
        
        @self.app.delete("/api/v1/exercises/{exercise_id}")
        async def delete_exercise(
            exercise_id: str,
            current_user: str = Depends(self._get_current_user)
        ):
            """Delete exercise"""
            success = await self.content_service.delete_exercise(exercise_id)
            if not success:
                raise HTTPException(status_code=404, detail="Exercise not found")
            return create_success_response("Exercise deleted successfully")
        
        @self.app.get("/api/v1/exercises", response_model=List[ExerciseResponse])
        async def list_exercises(
            course_id: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
        ):
            """List exercises"""
            return await self.content_service.list_exercises(course_id, limit, offset)
        
        # Lab Environment endpoints
        @self.app.post("/api/v1/labs", response_model=LabEnvironmentResponse)
        async def create_lab_environment(
            lab_data: LabEnvironmentCreate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Create a new lab environment"""
            try:
                lab = await self.content_service.create_lab_environment(lab_data, current_user)
                return lab
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/labs/{lab_id}", response_model=LabEnvironmentResponse)
        async def get_lab_environment(lab_id: str):
            """Get lab environment by ID"""
            lab = await self.content_service.get_lab_environment(lab_id)
            if not lab:
                raise HTTPException(status_code=404, detail="Lab environment not found")
            return lab
        
        @self.app.put("/api/v1/labs/{lab_id}", response_model=LabEnvironmentResponse)
        async def update_lab_environment(
            lab_id: str,
            updates: LabEnvironmentUpdate,
            current_user: str = Depends(self._get_current_user)
        ):
            """Update lab environment"""
            lab = await self.content_service.update_lab_environment(lab_id, updates)
            if not lab:
                raise HTTPException(status_code=404, detail="Lab environment not found")
            return lab
        
        @self.app.delete("/api/v1/labs/{lab_id}")
        async def delete_lab_environment(
            lab_id: str,
            current_user: str = Depends(self._get_current_user)
        ):
            """Delete lab environment"""
            success = await self.content_service.delete_lab_environment(lab_id)
            if not success:
                raise HTTPException(status_code=404, detail="Lab environment not found")
            return create_success_response("Lab environment deleted successfully")
        
        @self.app.get("/api/v1/labs", response_model=List[LabEnvironmentResponse])
        async def list_lab_environments(
            course_id: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
        ):
            """List lab environments"""
            return await self.content_service.list_lab_environments(course_id, limit, offset)
        
        # Search and statistics endpoints
        @self.app.get("/api/v1/search")
        async def search_content(
            query: str,
            content_types: Optional[List[ContentType]] = None
        ):
            """Search content"""
            return await self.content_service.search_content(query, content_types)
        
        @self.app.get("/api/v1/statistics")
        async def get_statistics():
            """Get content statistics"""
            return await self.content_service.get_content_statistics()
        
        @self.app.get("/api/v1/courses/{course_id}/content")
        async def get_course_content(course_id: str):
            """Get all content for a course"""
            return await self.content_service.get_course_content(course_id)
        
        @self.app.delete("/api/v1/courses/{course_id}/content")
        async def delete_course_content(
            course_id: str,
            current_user: str = Depends(self._get_current_user)
        ):
            """Delete all content for a course"""
            deleted_counts = await self.content_service.delete_course_content(course_id)
            return create_success_response(
                "Course content deleted successfully",
                data=deleted_counts
            )
        
        # File upload endpoints (simplified for now)
        @self.app.post("/api/v1/upload")
        async def upload_file(
            file: UploadFile = File(...),
            content_type: str = Form(...),
            current_user: str = Depends(self._get_current_user)
        ):
            """Upload a file"""
            # This is a simplified implementation
            # In a real system, this would integrate with file storage service
            return create_success_response(
                "File uploaded successfully",
                data={"filename": file.filename, "content_type": content_type}
            )
        
        # Error handlers
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            """Handle HTTP exceptions"""
            return create_error_response(
                message=exc.detail,
                error_code=f"HTTP_{exc.status_code}"
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            """Handle general exceptions"""
            return create_error_response(
                message="Internal server error",
                error_code="INTERNAL_SERVER_ERROR",
                details={"error": str(exc)}
            )
    
    async def _get_current_user(self) -> str:
        """Get current user from request (simplified)"""
        # In a real implementation, this would validate JWT token
        # and return user information
        return "current_user_id"


# Create application instance
app_instance = ContentManagementApp()
app = app_instance.app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)