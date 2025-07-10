#!/usr/bin/env python3
"""
Course Management Service - PostgreSQL Database Integration
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import hydra
from omegaconf import DictConfig
import uvicorn
from datetime import datetime
from pydantic import BaseModel, Field
import asyncpg
import os
import uuid
from contextlib import asynccontextmanager

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
    id: Optional[str] = None
    student_id: str
    course_id: str
    enrollment_date: Optional[datetime] = None
    status: str = "active"
    progress_percentage: float = 0.00
    last_accessed: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    certificate_issued: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EnrollmentRequest(BaseModel):
    student_email: str
    course_id: str
    
class StudentRegistrationRequest(BaseModel):
    course_id: str
    student_emails: List[str]

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logging.info("Database connection pool created successfully")
        except Exception as e:
            logging.error(f"Failed to create database pool: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logging.info("Database connection pool closed")
    
    def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise HTTPException(status_code=500, detail="Database not connected")
        return self.pool.acquire()

# Global database manager
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    global db_manager
    
    # Startup
    db_password = os.getenv('DB_PASSWORD', '')
    if not db_password:
        raise ValueError("DB_PASSWORD environment variable not set")
    
    database_url = f"postgresql://course_user:{db_password}@localhost:5433/course_creator"
    db_manager = DatabaseManager(database_url)
    await db_manager.connect()
    
    yield
    
    # Shutdown
    await db_manager.disconnect()

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    # Logging setup
    logging.basicConfig(
        level=cfg.log.level,
        format=cfg.log.format
    )
    logger = logging.getLogger(__name__)
    
    # FastAPI app with lifespan
    app = FastAPI(
        title="Course Management Service",
        description="API for managing courses and enrollments",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Course Management Service"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now()}
    
    @app.get("/courses", response_model=List[Course])
    async def get_courses():
        """Get all courses from database"""
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, description, instructor_id, category, 
                           difficulty_level, estimated_duration, price, is_published,
                           thumbnail_url, created_at, updated_at
                    FROM courses
                    ORDER BY created_at DESC
                """)
                
                courses = []
                for row in rows:
                    course = Course(
                        id=str(row['id']),
                        title=row['title'],
                        description=row['description'],
                        instructor_id=str(row['instructor_id']),
                        category=row['category'],
                        difficulty_level=row['difficulty_level'],
                        estimated_duration=row['estimated_duration'],
                        price=float(row['price']),
                        is_published=row['is_published'],
                        thumbnail_url=row['thumbnail_url'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    courses.append(course)
                
                logger.info(f"Retrieved {len(courses)} courses from database")
                return courses
                
        except Exception as e:
            logger.error(f"Error retrieving courses: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve courses")
    
    @app.post("/courses", response_model=Course)
    async def create_course(course: Course):
        """Create a new course in database"""
        try:
            course_id = str(uuid.uuid4())
            now = datetime.now()
            
            async with db_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO courses (id, title, description, instructor_id, category,
                                       difficulty_level, estimated_duration, price, is_published,
                                       thumbnail_url, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """, course_id, course.title, course.description, course.instructor_id,
                    course.category, course.difficulty_level, course.estimated_duration,
                    course.price, course.is_published, course.thumbnail_url, now, now)
                
                course.id = course_id
                course.created_at = now
                course.updated_at = now
                
                logger.info(f"Created course: {course.title} (ID: {course_id})")
                return course
                
        except Exception as e:
            logger.error(f"Error creating course: {e}")
            raise HTTPException(status_code=500, detail="Failed to create course")
    
    @app.get("/courses/{course_id}", response_model=Course)
    async def get_course(course_id: str):
        """Get a specific course by ID"""
        try:
            async with db_manager.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT id, title, description, instructor_id, category, 
                           difficulty_level, estimated_duration, price, is_published,
                           thumbnail_url, created_at, updated_at
                    FROM courses WHERE id = $1
                """, uuid.UUID(course_id))
                
                if not row:
                    raise HTTPException(status_code=404, detail="Course not found")
                
                course = Course(
                    id=str(row['id']),
                    title=row['title'],
                    description=row['description'],
                    instructor_id=str(row['instructor_id']),
                    category=row['category'],
                    difficulty_level=row['difficulty_level'],
                    estimated_duration=row['estimated_duration'],
                    price=float(row['price']),
                    is_published=row['is_published'],
                    thumbnail_url=row['thumbnail_url'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                
                return course
                
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid course ID format")
        except Exception as e:
            logger.error(f"Error retrieving course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve course")
    
    @app.put("/courses/{course_id}", response_model=Course)
    async def update_course(course_id: str, updated_course: Course):
        """Update an existing course"""
        try:
            now = datetime.now()
            
            async with db_manager.get_connection() as conn:
                result = await conn.execute("""
                    UPDATE courses SET 
                        title = $2, description = $3, instructor_id = $4, category = $5,
                        difficulty_level = $6, estimated_duration = $7, price = $8,
                        is_published = $9, thumbnail_url = $10, updated_at = $11
                    WHERE id = $1
                """, uuid.UUID(course_id), updated_course.title, updated_course.description,
                    updated_course.instructor_id, updated_course.category,
                    updated_course.difficulty_level, updated_course.estimated_duration,
                    updated_course.price, updated_course.is_published,
                    updated_course.thumbnail_url, now)
                
                if result == "UPDATE 0":
                    raise HTTPException(status_code=404, detail="Course not found")
                
                updated_course.id = course_id
                updated_course.updated_at = now
                
                logger.info(f"Updated course: {course_id}")
                return updated_course
                
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid course ID format")
        except Exception as e:
            logger.error(f"Error updating course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update course")
    
    @app.delete("/courses/{course_id}")
    async def delete_course(course_id: str):
        """Delete a course"""
        try:
            async with db_manager.get_connection() as conn:
                result = await conn.execute("""
                    DELETE FROM courses WHERE id = $1
                """, uuid.UUID(course_id))
                
                if result == "DELETE 0":
                    raise HTTPException(status_code=404, detail="Course not found")
                
                logger.info(f"Deleted course: {course_id}")
                return {"message": "Course deleted successfully"}
                
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid course ID format")
        except Exception as e:
            logger.error(f"Error deleting course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete course")
    
    @app.post("/enrollments", response_model=Enrollment)
    async def create_enrollment(enrollment: Enrollment):
        """Create a new enrollment"""
        try:
            enrollment_id = str(uuid.uuid4())
            now = datetime.now()
            
            async with db_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO enrollments (id, student_id, course_id, enrollment_date,
                                           status, progress_percentage, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, enrollment_id, enrollment.student_id, enrollment.course_id,
                    now, enrollment.status, enrollment.progress_percentage, now, now)
                
                enrollment.id = enrollment_id
                enrollment.enrollment_date = now
                enrollment.created_at = now
                enrollment.updated_at = now
                
                logger.info(f"Created enrollment: student {enrollment.student_id} -> course {enrollment.course_id}")
                return enrollment
                
        except Exception as e:
            logger.error(f"Error creating enrollment: {e}")
            raise HTTPException(status_code=500, detail="Failed to create enrollment")
    
    @app.get("/enrollments")
    async def get_enrollments():
        """Get all enrollments"""
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT id, student_id, course_id, enrollment_date, status,
                           progress_percentage, last_accessed, completed_at,
                           certificate_issued, created_at, updated_at
                    FROM enrollments
                    ORDER BY enrollment_date DESC
                """)
                
                enrollments = []
                for row in rows:
                    enrollment = Enrollment(
                        id=str(row['id']),
                        student_id=str(row['student_id']),
                        course_id=str(row['course_id']),
                        enrollment_date=row['enrollment_date'],
                        status=row['status'],
                        progress_percentage=float(row['progress_percentage']),
                        last_accessed=row['last_accessed'],
                        completed_at=row['completed_at'],
                        certificate_issued=row['certificate_issued'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    enrollments.append(enrollment)
                
                return {"enrollments": enrollments}
                
        except Exception as e:
            logger.error(f"Error retrieving enrollments: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve enrollments")
    
    @app.get("/courses/{course_id}/enrollments")
    async def get_course_enrollments(course_id: str):
        """Get enrollments for a specific course"""
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT id, student_id, course_id, enrollment_date, status,
                           progress_percentage, last_accessed, completed_at,
                           certificate_issued, created_at, updated_at
                    FROM enrollments
                    WHERE course_id = $1
                    ORDER BY enrollment_date DESC
                """, uuid.UUID(course_id))
                
                enrollments = []
                for row in rows:
                    enrollment = Enrollment(
                        id=str(row['id']),
                        student_id=str(row['student_id']),
                        course_id=str(row['course_id']),
                        enrollment_date=row['enrollment_date'],
                        status=row['status'],
                        progress_percentage=float(row['progress_percentage']),
                        last_accessed=row['last_accessed'],
                        completed_at=row['completed_at'],
                        certificate_issued=row['certificate_issued'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    enrollments.append(enrollment)
                
                return {"enrollments": enrollments}
                
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid course ID format")
        except Exception as e:
            logger.error(f"Error retrieving course enrollments: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve course enrollments")
    
    @app.post("/instructor/enroll-student")
    async def enroll_student(request: EnrollmentRequest):
        """Instructor endpoint to enroll a student in a course"""
        logger.info(f"Enrolling student {request.student_email} in course {request.course_id}")
        
        try:
            # For demo purposes, we'll use email as student_id
            # In production, you'd look up the user ID from the email
            enrollment = Enrollment(
                student_id=request.student_email,
                course_id=request.course_id,
                status="active"
            )
            
            created_enrollment = await create_enrollment(enrollment)
            
            return {"message": "Student enrolled successfully", "enrollment": created_enrollment}
            
        except Exception as e:
            logger.error(f"Error enrolling student: {e}")
            raise HTTPException(status_code=500, detail="Failed to enroll student")
    
    @app.post("/instructor/register-students")
    async def register_multiple_students(request: StudentRegistrationRequest):
        """Instructor endpoint to register multiple students for a course"""
        logger.info(f"Registering {len(request.student_emails)} students for course {request.course_id}")
        
        enrolled_students = []
        failed_enrollments = []
        
        try:
            async with db_manager.get_connection() as conn:
                for email in request.student_emails:
                    try:
                        # Check if student is already enrolled
                        existing = await conn.fetchrow("""
                            SELECT id FROM enrollments 
                            WHERE student_id = $1 AND course_id = $2
                        """, email, uuid.UUID(request.course_id))
                        
                        if existing:
                            failed_enrollments.append({"email": email, "reason": "Already enrolled"})
                            continue
                        
                        # Create enrollment
                        enrollment = Enrollment(
                            student_id=email,
                            course_id=request.course_id,
                            status="active"
                        )
                        
                        created_enrollment = await create_enrollment(enrollment)
                        enrolled_students.append(email)
                        
                    except Exception as e:
                        failed_enrollments.append({"email": email, "reason": str(e)})
                
                return {
                    "message": f"Enrolled {len(enrolled_students)} students",
                    "enrolled_students": enrolled_students,
                    "failed_enrollments": failed_enrollments
                }
                
        except Exception as e:
            logger.error(f"Error registering students: {e}")
            raise HTTPException(status_code=500, detail="Failed to register students")
    
    @app.get("/instructor/course/{course_id}/students")
    async def get_course_students(course_id: str):
        """Get all students enrolled in a course"""
        try:
            course_enrollments = await get_course_enrollments(course_id)
            return {
                "course_id": course_id,
                "total_students": len(course_enrollments["enrollments"]),
                "enrollments": course_enrollments["enrollments"]
            }
        except Exception as e:
            logger.error(f"Error retrieving course students: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve course students")
    
    @app.delete("/instructor/enrollment/{enrollment_id}")
    async def remove_student_enrollment(enrollment_id: str):
        """Remove a student from a course"""
        try:
            async with db_manager.get_connection() as conn:
                result = await conn.execute("""
                    DELETE FROM enrollments WHERE id = $1
                """, uuid.UUID(enrollment_id))
                
                if result == "DELETE 0":
                    raise HTTPException(status_code=404, detail="Enrollment not found")
                
                return {"message": "Student removed from course successfully"}
                
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid enrollment ID format")
        except Exception as e:
            logger.error(f"Error removing enrollment: {e}")
            raise HTTPException(status_code=500, detail="Failed to remove enrollment")
    
    @app.get("/student/my-courses/{student_id}")
    async def get_student_courses(student_id: str):
        """Get all courses a student is enrolled in"""
        try:
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT e.id, e.student_id, e.course_id, e.enrollment_date, e.status,
                           e.progress_percentage, e.last_accessed, e.completed_at,
                           e.certificate_issued, e.created_at, e.updated_at
                    FROM enrollments e
                    WHERE e.student_id = $1
                    ORDER BY e.enrollment_date DESC
                """, student_id)
                
                enrollments = []
                for row in rows:
                    enrollment = Enrollment(
                        id=str(row['id']),
                        student_id=str(row['student_id']),
                        course_id=str(row['course_id']),
                        enrollment_date=row['enrollment_date'],
                        status=row['status'],
                        progress_percentage=float(row['progress_percentage']),
                        last_accessed=row['last_accessed'],
                        completed_at=row['completed_at'],
                        certificate_issued=row['certificate_issued'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    enrollments.append(enrollment)
                
                return {
                    "student_id": student_id,
                    "enrollments": enrollments
                }
                
        except Exception as e:
            logger.error(f"Error retrieving student courses: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve student courses")
    
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