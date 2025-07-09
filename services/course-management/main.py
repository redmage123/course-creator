#!/usr/bin/env python3
"""
Course Management Service - Fixed Hydra Configuration
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import hydra
from omegaconf import DictConfig
import uvicorn
from datetime import datetime
from pydantic import BaseModel, Field
import databases
import sqlalchemy
import sqlalchemy.dialects.postgresql
import uuid

# Models
class Course(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    instructor_id: str
    category: Optional[str] = None
    difficulty_level: str = "beginner"
    estimated_duration: Optional[int] = None
    price: float = 0.00
    is_published: bool = False
    thumbnail_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Enrollment(BaseModel):
    id: Optional[int] = None 
    student_id: str
    course_id: str
    enrolled_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"  # active, completed, dropped

class EnrollmentRequest(BaseModel):
    student_email: str
    course_id: str
    
class StudentRegistrationRequest(BaseModel):
    course_id: str
    student_emails: List[str]

class Progress(BaseModel):
    id: Optional[int] = None
    enrollment_id: int
    completed_modules: int
    grade: float
    last_activity: datetime = Field(default_factory=datetime.now)

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
        title="Course Management Service",
        description="API for managing courses and enrollments",
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
    courses = []
    enrollments = []
    progress_records = []
    
    @app.get("/")
    async def root():
        return {"message": "Course Management Service"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now()}
    
    @app.get("/courses", response_model=List[Course])
    async def get_courses():
        return courses
    
    @app.post("/courses", response_model=Course)
    async def create_course(course: Course):
        course.id = len(courses) + 1
        course.created_at = datetime.now()
        course.updated_at = datetime.now()
        courses.append(course)
        logger.info(f"Created course: {course.title}")
        return course
    
    @app.get("/courses/{course_id}", response_model=Course)
    async def get_course(course_id: int):
        for course in courses:
            if course.id == course_id:
                return course
        raise HTTPException(status_code=404, detail="Course not found")
    
    @app.put("/courses/{course_id}", response_model=Course)
    async def update_course(course_id: int, updated_course: Course):
        for i, course in enumerate(courses):
            if course.id == course_id:
                updated_course.id = course_id
                updated_course.updated_at = datetime.now()
                courses[i] = updated_course
                logger.info(f"Updated course: {course_id}")
                return updated_course
        raise HTTPException(status_code=404, detail="Course not found")
    
    @app.delete("/courses/{course_id}")
    async def delete_course(course_id: int):
        for i, course in enumerate(courses):
            if course.id == course_id:
                del courses[i]
                logger.info(f"Deleted course: {course_id}")
                return {"message": "Course deleted successfully"}
        raise HTTPException(status_code=404, detail="Course not found")
    
    @app.post("/enrollments", response_model=Enrollment)
    async def create_enrollment(enrollment: Enrollment):
        enrollment.id = len(enrollments) + 1
        enrollment.enrolled_at = datetime.now()
        enrollments.append(enrollment)
        logger.info(f"Created enrollment: student {enrollment.student_id} -> course {enrollment.course_id}")
        return enrollment
    
    @app.get("/enrollments")
    async def get_enrollments():
        return {"enrollments": enrollments}
    
    @app.get("/courses/{course_id}/enrollments")
    async def get_course_enrollments(course_id: int):
        course_enrollments = [e for e in enrollments if e.course_id == course_id]
        return {"enrollments": course_enrollments}
    
    @app.post("/instructor/enroll-student")
    async def enroll_student(request: EnrollmentRequest):
        """Instructor endpoint to enroll a student in a course"""
        logger.info(f"Enrolling student {request.student_email} in course {request.course_id}")
        
        # In a real implementation, you would:
        # 1. Verify instructor has permission to enroll students in this course
        # 2. Look up student by email from user management service
        # 3. Create enrollment record
        
        # For demo, we'll create a mock enrollment
        enrollment = Enrollment(
            id=len(enrollments) + 1,
            student_id=request.student_email,  # In real app, would be user ID
            course_id=request.course_id,
            enrolled_at=datetime.now(),
            status="active"
        )
        enrollments.append(enrollment)
        
        return {"message": "Student enrolled successfully", "enrollment": enrollment}
    
    @app.post("/instructor/register-students")
    async def register_multiple_students(request: StudentRegistrationRequest):
        """Instructor endpoint to register multiple students for a course"""
        logger.info(f"Registering {len(request.student_emails)} students for course {request.course_id}")
        
        enrolled_students = []
        failed_enrollments = []
        
        for email in request.student_emails:
            try:
                # Check if student is already enrolled
                existing_enrollment = next(
                    (e for e in enrollments if e.student_id == email and e.course_id == request.course_id), 
                    None
                )
                
                if existing_enrollment:
                    failed_enrollments.append({"email": email, "reason": "Already enrolled"})
                    continue
                
                # Create enrollment
                enrollment = Enrollment(
                    id=len(enrollments) + 1,
                    student_id=email,
                    course_id=request.course_id,
                    enrolled_at=datetime.now(),
                    status="active"
                )
                enrollments.append(enrollment)
                enrolled_students.append(email)
                
            except Exception as e:
                failed_enrollments.append({"email": email, "reason": str(e)})
        
        return {
            "message": f"Enrolled {len(enrolled_students)} students",
            "enrolled_students": enrolled_students,
            "failed_enrollments": failed_enrollments
        }
    
    @app.get("/instructor/course/{course_id}/students")
    async def get_course_students(course_id: str):
        """Get all students enrolled in a course"""
        course_enrollments = [e for e in enrollments if e.course_id == course_id]
        return {
            "course_id": course_id,
            "total_students": len(course_enrollments),
            "enrollments": course_enrollments
        }
    
    @app.delete("/instructor/enrollment/{enrollment_id}")
    async def remove_student_enrollment(enrollment_id: int):
        """Remove a student from a course"""
        enrollment = next((e for e in enrollments if e.id == enrollment_id), None)
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        
        enrollments.remove(enrollment)
        return {"message": "Student removed from course successfully"}
    
    @app.get("/student/my-courses/{student_id}")
    async def get_student_courses(student_id: str):
        """Get all courses a student is enrolled in"""
        student_enrollments = [e for e in enrollments if e.student_id == student_id]
        return {
            "student_id": student_id,
            "enrollments": student_enrollments
        }
    
    # Error handling
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTP error occurred: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error occurred: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Start the server
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, reload=cfg.server.reload)

if __name__ == "__main__":
    main()