#!/usr/bin/env python3
"""
Course Management Service - PostgreSQL Database Integration
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
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
from jose import JWTError, jwt

# Models
class Course(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    instructor_id: str
    category: Optional[str] = None
    difficulty_level: str = "beginner"
    estimated_duration: Optional[int] = None
    duration_unit: Optional[str] = "weeks"
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

# Feedback Models
class CourseFeedback(BaseModel):
    feedback_id: Optional[str] = None
    student_id: str
    course_id: str
    instructor_id: str
    overall_rating: int = Field(..., ge=1, le=5)
    content_quality: Optional[int] = Field(None, ge=1, le=5)
    instructor_effectiveness: Optional[int] = Field(None, ge=1, le=5)
    difficulty_appropriateness: Optional[int] = Field(None, ge=1, le=5)
    lab_quality: Optional[int] = Field(None, ge=1, le=5)
    positive_aspects: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    additional_comments: Optional[str] = None
    would_recommend: Optional[bool] = None
    is_anonymous: bool = False
    submission_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class StudentFeedback(BaseModel):
    feedback_id: Optional[str] = None
    instructor_id: str
    student_id: str
    course_id: str
    overall_performance: Optional[int] = Field(None, ge=1, le=5)
    participation: Optional[int] = Field(None, ge=1, le=5)
    lab_performance: Optional[int] = Field(None, ge=1, le=5)
    quiz_performance: Optional[int] = Field(None, ge=1, le=5)
    improvement_trend: Optional[int] = Field(None, ge=1, le=5)
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    specific_recommendations: Optional[str] = None
    notable_achievements: Optional[str] = None
    concerns: Optional[str] = None
    progress_assessment: Optional[str] = Field(None, pattern="^(excellent|good|satisfactory|needs_improvement|poor)$")
    expected_outcome: Optional[str] = Field(None, pattern="^(exceeds_expectations|meets_expectations|below_expectations|at_risk)$")
    feedback_type: str = Field("regular", pattern="^(regular|midterm|final|intervention)$")
    is_shared_with_student: bool = False
    submission_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FeedbackResponse(BaseModel):
    response_id: Optional[str] = None
    course_feedback_id: str
    instructor_id: str
    response_text: str
    action_items: Optional[str] = None
    acknowledgment_type: str = Field("standard", pattern="^(standard|detailed|action_plan)$")
    response_date: Optional[datetime] = None
    is_public: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CourseFeedbackRequest(BaseModel):
    course_id: str
    overall_rating: int = Field(..., ge=1, le=5)
    content_quality: Optional[int] = Field(None, ge=1, le=5)
    instructor_effectiveness: Optional[int] = Field(None, ge=1, le=5)
    difficulty_appropriateness: Optional[int] = Field(None, ge=1, le=5)
    lab_quality: Optional[int] = Field(None, ge=1, le=5)
    positive_aspects: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    additional_comments: Optional[str] = None
    would_recommend: Optional[bool] = None
    is_anonymous: bool = False

class StudentFeedbackRequest(BaseModel):
    student_id: str
    course_id: str
    overall_performance: Optional[int] = Field(None, ge=1, le=5)
    participation: Optional[int] = Field(None, ge=1, le=5)
    lab_performance: Optional[int] = Field(None, ge=1, le=5)
    quiz_performance: Optional[int] = Field(None, ge=1, le=5)
    improvement_trend: Optional[int] = Field(None, ge=1, le=5)
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    specific_recommendations: Optional[str] = None
    notable_achievements: Optional[str] = None
    concerns: Optional[str] = None
    progress_assessment: Optional[str] = Field(None, pattern="^(excellent|good|satisfactory|needs_improvement|poor)$")
    expected_outcome: Optional[str] = Field(None, pattern="^(exceeds_expectations|meets_expectations|below_expectations|at_risk)$")
    feedback_type: str = Field("regular", pattern="^(regular|midterm|final|intervention)$")
    is_shared_with_student: bool = False

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

# Global database manager and config
db_manager = None
current_config = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    global db_manager, current_config
    
    # Startup - Use Hydra configuration for database connection
    database_url = current_config.database.url
    logging.info(f"Connecting to database: {database_url.split('@')[1]}")  # Log without password
    
    db_manager = DatabaseManager(database_url)
    await db_manager.connect()
    
    yield
    
    # Shutdown
    await db_manager.disconnect()

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    global current_config
    current_config = cfg
    
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
    
    # OAuth2 scheme for token authentication
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    
    # Authentication dependency
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        """Extract user information from JWT token"""
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            logger.info(f"Attempting to validate JWT token: {token[:50]}...")
            logger.info(f"Using JWT secret length: {len(cfg.jwt.secret_key)}")
            logger.info(f"Using JWT algorithm: {cfg.jwt.algorithm}")
            
            # Use the same JWT secret as user management service
            payload = jwt.decode(
                token, 
                cfg.jwt.secret_key, 
                algorithms=[cfg.jwt.algorithm]
            )
            logger.info(f"JWT payload decoded successfully: {payload}")
            
            user_id: str = payload.get("sub")
            if user_id is None:
                logger.error("No 'sub' field in JWT payload")
                raise credentials_exception
            logger.info(f"Authenticated user: {user_id}")
            return {"user_id": user_id}
        except JWTError as e:
            logger.error(f"JWT validation error: {e}")
            logger.error(f"Token was: {token[:50]}...")
            logger.error(f"Secret key first 10 chars: {cfg.jwt.secret_key[:10]}...")
            raise credentials_exception
    
    @app.get("/")
    async def root():
        return {"message": "Course Management Service"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now()}
    
    @app.get("/debug-auth")
    async def debug_auth():
        """Debug endpoint to check JWT configuration"""
        return {
            "jwt_secret_length": len(cfg.jwt.secret_key) if hasattr(cfg, 'jwt') else 0,
            "jwt_algorithm": cfg.jwt.algorithm if hasattr(cfg, 'jwt') else "N/A",
            "config_available": hasattr(cfg, 'jwt')
        }
    
    @app.get("/courses", response_model=List[Course])
    async def get_courses(current_user: dict = Depends(get_current_user)):
        """Get courses for the authenticated instructor"""
        try:
            instructor_id = current_user["user_id"]
            logger.info(f"Loading courses for instructor: {instructor_id}")
            
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, description, instructor_id, category, 
                           difficulty_level, estimated_duration, duration_unit, price, is_published,
                           thumbnail_url, created_at, updated_at
                    FROM courses
                    WHERE instructor_id = $1
                    ORDER BY created_at DESC
                """, uuid.UUID(instructor_id))
                
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
                        duration_unit=row['duration_unit'],
                        price=float(row['price']),
                        is_published=row['is_published'],
                        thumbnail_url=row['thumbnail_url'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    courses.append(course)
                
                logger.info(f"Retrieved {len(courses)} courses for instructor {instructor_id}")
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
                                       difficulty_level, estimated_duration, duration_unit, price, is_published,
                                       thumbnail_url, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """, course_id, course.title, course.description, course.instructor_id,
                    course.category, course.difficulty_level, course.estimated_duration,
                    course.duration_unit, course.price, course.is_published, course.thumbnail_url, now, now)
                
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
                           difficulty_level, estimated_duration, duration_unit, price, is_published,
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
                    duration_unit=row['duration_unit'],
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
                        difficulty_level = $6, estimated_duration = $7, duration_unit = $8, price = $9,
                        is_published = $10, thumbnail_url = $11, updated_at = $12
                    WHERE id = $1
                """, uuid.UUID(course_id), updated_course.title, updated_course.description,
                    updated_course.instructor_id, updated_course.category,
                    updated_course.difficulty_level, updated_course.estimated_duration,
                    updated_course.duration_unit, updated_course.price, updated_course.is_published,
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
    
    # Feedback System Endpoints
    
    @app.post("/feedback/course", response_model=CourseFeedback)
    async def submit_course_feedback(
        feedback_request: CourseFeedbackRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Students submit feedback about a course"""
        try:
            student_id = current_user["user_id"]
            feedback_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Get instructor ID for the course
            async with db_manager.get_connection() as conn:
                course_row = await conn.fetchrow("""
                    SELECT instructor_id FROM courses WHERE id = $1
                """, uuid.UUID(feedback_request.course_id))
                
                if not course_row:
                    raise HTTPException(status_code=404, detail="Course not found")
                
                instructor_id = str(course_row['instructor_id'])
                
                # Check if student is enrolled in the course
                enrollment_row = await conn.fetchrow("""
                    SELECT id FROM enrollments 
                    WHERE student_id = $1 AND course_id = $2
                """, uuid.UUID(student_id), uuid.UUID(feedback_request.course_id))
                
                if not enrollment_row:
                    raise HTTPException(status_code=403, detail="You must be enrolled in this course to provide feedback")
                
                # Insert or update feedback (upsert)
                await conn.execute("""
                    INSERT INTO course_feedback (
                        feedback_id, student_id, course_id, instructor_id,
                        overall_rating, content_quality, instructor_effectiveness,
                        difficulty_appropriateness, lab_quality, positive_aspects,
                        areas_for_improvement, additional_comments, would_recommend,
                        is_anonymous, submission_date, last_updated, status,
                        created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                    ON CONFLICT (student_id, course_id) 
                    DO UPDATE SET
                        overall_rating = EXCLUDED.overall_rating,
                        content_quality = EXCLUDED.content_quality,
                        instructor_effectiveness = EXCLUDED.instructor_effectiveness,
                        difficulty_appropriateness = EXCLUDED.difficulty_appropriateness,
                        lab_quality = EXCLUDED.lab_quality,
                        positive_aspects = EXCLUDED.positive_aspects,
                        areas_for_improvement = EXCLUDED.areas_for_improvement,
                        additional_comments = EXCLUDED.additional_comments,
                        would_recommend = EXCLUDED.would_recommend,
                        is_anonymous = EXCLUDED.is_anonymous,
                        last_updated = EXCLUDED.last_updated,
                        updated_at = EXCLUDED.updated_at
                """, feedback_id, uuid.UUID(student_id), uuid.UUID(feedback_request.course_id), 
                    uuid.UUID(instructor_id), feedback_request.overall_rating,
                    feedback_request.content_quality, feedback_request.instructor_effectiveness,
                    feedback_request.difficulty_appropriateness, feedback_request.lab_quality,
                    feedback_request.positive_aspects, feedback_request.areas_for_improvement,
                    feedback_request.additional_comments, feedback_request.would_recommend,
                    feedback_request.is_anonymous, now, now, "active", now, now)
                
                feedback = CourseFeedback(
                    feedback_id=feedback_id,
                    student_id=student_id,
                    course_id=feedback_request.course_id,
                    instructor_id=instructor_id,
                    overall_rating=feedback_request.overall_rating,
                    content_quality=feedback_request.content_quality,
                    instructor_effectiveness=feedback_request.instructor_effectiveness,
                    difficulty_appropriateness=feedback_request.difficulty_appropriateness,
                    lab_quality=feedback_request.lab_quality,
                    positive_aspects=feedback_request.positive_aspects,
                    areas_for_improvement=feedback_request.areas_for_improvement,
                    additional_comments=feedback_request.additional_comments,
                    would_recommend=feedback_request.would_recommend,
                    is_anonymous=feedback_request.is_anonymous,
                    submission_date=now,
                    last_updated=now,
                    status="active",
                    created_at=now,
                    updated_at=now
                )
                
                logger.info(f"Course feedback submitted by student {student_id} for course {feedback_request.course_id}")
                return feedback
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error submitting course feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit course feedback")
    
    @app.get("/feedback/course/{course_id}")
    async def get_course_feedback(
        course_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all feedback for a course (instructors only)"""
        try:
            user_id = current_user["user_id"]
            
            async with db_manager.get_connection() as conn:
                # Verify user is instructor for this course
                course_row = await conn.fetchrow("""
                    SELECT instructor_id FROM courses WHERE id = $1
                """, uuid.UUID(course_id))
                
                if not course_row or str(course_row['instructor_id']) != user_id:
                    raise HTTPException(status_code=403, detail="You can only view feedback for your own courses")
                
                # Get all feedback for the course
                feedback_rows = await conn.fetch("""
                    SELECT cf.*, u.full_name as student_name, u.email as student_email
                    FROM course_feedback cf
                    LEFT JOIN users u ON cf.student_id = u.id
                    WHERE cf.course_id = $1 AND cf.status = 'active'
                    ORDER BY cf.submission_date DESC
                """, uuid.UUID(course_id))
                
                feedback_list = []
                for row in feedback_rows:
                    feedback = CourseFeedback(
                        feedback_id=str(row['feedback_id']),
                        student_id=str(row['student_id']) if not row['is_anonymous'] else "anonymous",
                        course_id=str(row['course_id']),
                        instructor_id=str(row['instructor_id']),
                        overall_rating=row['overall_rating'],
                        content_quality=row['content_quality'],
                        instructor_effectiveness=row['instructor_effectiveness'],
                        difficulty_appropriateness=row['difficulty_appropriateness'],
                        lab_quality=row['lab_quality'],
                        positive_aspects=row['positive_aspects'],
                        areas_for_improvement=row['areas_for_improvement'],
                        additional_comments=row['additional_comments'],
                        would_recommend=row['would_recommend'],
                        is_anonymous=row['is_anonymous'],
                        submission_date=row['submission_date'],
                        last_updated=row['last_updated'],
                        status=row['status'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    feedback_list.append(feedback)
                
                # Get summary statistics
                summary_row = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_feedback,
                        AVG(overall_rating) as avg_overall_rating,
                        AVG(content_quality) as avg_content_quality,
                        AVG(instructor_effectiveness) as avg_instructor_effectiveness,
                        AVG(difficulty_appropriateness) as avg_difficulty_rating,
                        AVG(lab_quality) as avg_lab_quality,
                        ROUND(
                            (COUNT(CASE WHEN would_recommend = true THEN 1 END) * 100.0) / 
                            NULLIF(COUNT(CASE WHEN would_recommend IS NOT NULL THEN 1 END), 0), 
                            2
                        ) as recommendation_rate
                    FROM course_feedback
                    WHERE course_id = $1 AND status = 'active'
                """, uuid.UUID(course_id))
                
                return {
                    "course_id": course_id,
                    "feedback": feedback_list,
                    "summary": {
                        "total_feedback": summary_row['total_feedback'],
                        "avg_overall_rating": float(summary_row['avg_overall_rating']) if summary_row['avg_overall_rating'] else 0,
                        "avg_content_quality": float(summary_row['avg_content_quality']) if summary_row['avg_content_quality'] else 0,
                        "avg_instructor_effectiveness": float(summary_row['avg_instructor_effectiveness']) if summary_row['avg_instructor_effectiveness'] else 0,
                        "avg_difficulty_rating": float(summary_row['avg_difficulty_rating']) if summary_row['avg_difficulty_rating'] else 0,
                        "avg_lab_quality": float(summary_row['avg_lab_quality']) if summary_row['avg_lab_quality'] else 0,
                        "recommendation_rate": float(summary_row['recommendation_rate']) if summary_row['recommendation_rate'] else 0
                    }
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving course feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve course feedback")
    
    @app.post("/feedback/student", response_model=StudentFeedback)
    async def submit_student_feedback(
        feedback_request: StudentFeedbackRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Instructors submit feedback about individual students"""
        try:
            instructor_id = current_user["user_id"]
            feedback_id = str(uuid.uuid4())
            now = datetime.now()
            
            async with db_manager.get_connection() as conn:
                # Verify instructor teaches this course
                course_row = await conn.fetchrow("""
                    SELECT instructor_id FROM courses WHERE id = $1
                """, uuid.UUID(feedback_request.course_id))
                
                if not course_row or str(course_row['instructor_id']) != instructor_id:
                    raise HTTPException(status_code=403, detail="You can only provide feedback for students in your own courses")
                
                # Verify student is enrolled in the course
                enrollment_row = await conn.fetchrow("""
                    SELECT id FROM enrollments 
                    WHERE student_id = $1 AND course_id = $2
                """, uuid.UUID(feedback_request.student_id), uuid.UUID(feedback_request.course_id))
                
                if not enrollment_row:
                    raise HTTPException(status_code=404, detail="Student is not enrolled in this course")
                
                # Insert student feedback
                await conn.execute("""
                    INSERT INTO student_feedback (
                        feedback_id, instructor_id, student_id, course_id,
                        overall_performance, participation, lab_performance,
                        quiz_performance, improvement_trend, strengths,
                        areas_for_improvement, specific_recommendations,
                        notable_achievements, concerns, progress_assessment,
                        expected_outcome, feedback_type, is_shared_with_student,
                        submission_date, last_updated, status, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
                """, feedback_id, uuid.UUID(instructor_id), uuid.UUID(feedback_request.student_id),
                    uuid.UUID(feedback_request.course_id), feedback_request.overall_performance,
                    feedback_request.participation, feedback_request.lab_performance,
                    feedback_request.quiz_performance, feedback_request.improvement_trend,
                    feedback_request.strengths, feedback_request.areas_for_improvement,
                    feedback_request.specific_recommendations, feedback_request.notable_achievements,
                    feedback_request.concerns, feedback_request.progress_assessment,
                    feedback_request.expected_outcome, feedback_request.feedback_type,
                    feedback_request.is_shared_with_student, now, now, "active", now, now)
                
                feedback = StudentFeedback(
                    feedback_id=feedback_id,
                    instructor_id=instructor_id,
                    student_id=feedback_request.student_id,
                    course_id=feedback_request.course_id,
                    overall_performance=feedback_request.overall_performance,
                    participation=feedback_request.participation,
                    lab_performance=feedback_request.lab_performance,
                    quiz_performance=feedback_request.quiz_performance,
                    improvement_trend=feedback_request.improvement_trend,
                    strengths=feedback_request.strengths,
                    areas_for_improvement=feedback_request.areas_for_improvement,
                    specific_recommendations=feedback_request.specific_recommendations,
                    notable_achievements=feedback_request.notable_achievements,
                    concerns=feedback_request.concerns,
                    progress_assessment=feedback_request.progress_assessment,
                    expected_outcome=feedback_request.expected_outcome,
                    feedback_type=feedback_request.feedback_type,
                    is_shared_with_student=feedback_request.is_shared_with_student,
                    submission_date=now,
                    last_updated=now,
                    status="active",
                    created_at=now,
                    updated_at=now
                )
                
                logger.info(f"Student feedback submitted by instructor {instructor_id} for student {feedback_request.student_id}")
                return feedback
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error submitting student feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit student feedback")
    
    @app.get("/feedback/student/{student_id}/course/{course_id}")
    async def get_student_feedback(
        student_id: str,
        course_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all feedback for a specific student in a course"""
        try:
            user_id = current_user["user_id"]
            
            async with db_manager.get_connection() as conn:
                # Verify access permissions (instructor for the course OR the student themselves)
                course_row = await conn.fetchrow("""
                    SELECT instructor_id FROM courses WHERE id = $1
                """, uuid.UUID(course_id))
                
                if not course_row:
                    raise HTTPException(status_code=404, detail="Course not found")
                
                is_instructor = str(course_row['instructor_id']) == user_id
                is_student = student_id == user_id
                
                if not (is_instructor or is_student):
                    raise HTTPException(status_code=403, detail="You can only view feedback for your own courses or your own feedback")
                
                # Get feedback, filtering by sharing preferences if student is viewing
                if is_student:
                    feedback_query = """
                        SELECT sf.*, u.full_name as instructor_name
                        FROM student_feedback sf
                        LEFT JOIN users u ON sf.instructor_id = u.id
                        WHERE sf.student_id = $1 AND sf.course_id = $2 
                        AND sf.status = 'active' AND sf.is_shared_with_student = true
                        ORDER BY sf.submission_date DESC
                    """
                else:
                    feedback_query = """
                        SELECT sf.*, u.full_name as instructor_name
                        FROM student_feedback sf
                        LEFT JOIN users u ON sf.instructor_id = u.id
                        WHERE sf.student_id = $1 AND sf.course_id = $2 AND sf.status = 'active'
                        ORDER BY sf.submission_date DESC
                    """
                
                feedback_rows = await conn.fetch(feedback_query, uuid.UUID(student_id), uuid.UUID(course_id))
                
                feedback_list = []
                for row in feedback_rows:
                    feedback = StudentFeedback(
                        feedback_id=str(row['feedback_id']),
                        instructor_id=str(row['instructor_id']),
                        student_id=str(row['student_id']),
                        course_id=str(row['course_id']),
                        overall_performance=row['overall_performance'],
                        participation=row['participation'],
                        lab_performance=row['lab_performance'],
                        quiz_performance=row['quiz_performance'],
                        improvement_trend=row['improvement_trend'],
                        strengths=row['strengths'],
                        areas_for_improvement=row['areas_for_improvement'],
                        specific_recommendations=row['specific_recommendations'],
                        notable_achievements=row['notable_achievements'],
                        concerns=row['concerns'],
                        progress_assessment=row['progress_assessment'],
                        expected_outcome=row['expected_outcome'],
                        feedback_type=row['feedback_type'],
                        is_shared_with_student=row['is_shared_with_student'],
                        submission_date=row['submission_date'],
                        last_updated=row['last_updated'],
                        status=row['status'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    feedback_list.append(feedback)
                
                return {
                    "student_id": student_id,
                    "course_id": course_id,
                    "feedback": feedback_list
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving student feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve student feedback")
    
    @app.get("/feedback/course/{course_id}/students")
    async def get_all_students_feedback(
        course_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get feedback for all students in a course (instructors only)"""
        try:
            instructor_id = current_user["user_id"]
            
            async with db_manager.get_connection() as conn:
                # Verify instructor teaches this course
                course_row = await conn.fetchrow("""
                    SELECT instructor_id FROM courses WHERE id = $1
                """, uuid.UUID(course_id))
                
                if not course_row or str(course_row['instructor_id']) != instructor_id:
                    raise HTTPException(status_code=403, detail="You can only view feedback for your own courses")
                
                # Get all student feedback for the course
                feedback_rows = await conn.fetch("""
                    SELECT sf.*, u.full_name as student_name, u.email as student_email
                    FROM student_feedback sf
                    LEFT JOIN users u ON sf.student_id = u.id
                    WHERE sf.course_id = $1 AND sf.status = 'active'
                    ORDER BY u.full_name, sf.submission_date DESC
                """, uuid.UUID(course_id))
                
                # Group feedback by student
                students_feedback = {}
                for row in feedback_rows:
                    student_id = str(row['student_id'])
                    if student_id not in students_feedback:
                        students_feedback[student_id] = {
                            "student_id": student_id,
                            "student_name": row['student_name'],
                            "student_email": row['student_email'],
                            "feedback": []
                        }
                    
                    feedback = StudentFeedback(
                        feedback_id=str(row['feedback_id']),
                        instructor_id=str(row['instructor_id']),
                        student_id=str(row['student_id']),
                        course_id=str(row['course_id']),
                        overall_performance=row['overall_performance'],
                        participation=row['participation'],
                        lab_performance=row['lab_performance'],
                        quiz_performance=row['quiz_performance'],
                        improvement_trend=row['improvement_trend'],
                        strengths=row['strengths'],
                        areas_for_improvement=row['areas_for_improvement'],
                        specific_recommendations=row['specific_recommendations'],
                        notable_achievements=row['notable_achievements'],
                        concerns=row['concerns'],
                        progress_assessment=row['progress_assessment'],
                        expected_outcome=row['expected_outcome'],
                        feedback_type=row['feedback_type'],
                        is_shared_with_student=row['is_shared_with_student'],
                        submission_date=row['submission_date'],
                        last_updated=row['last_updated'],
                        status=row['status'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    students_feedback[student_id]["feedback"].append(feedback)
                
                return {
                    "course_id": course_id,
                    "students": list(students_feedback.values())
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving students feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve students feedback")
    
    @app.put("/feedback/student/{feedback_id}/share")
    async def toggle_feedback_sharing(
        feedback_id: str,
        share: bool,
        current_user: dict = Depends(get_current_user)
    ):
        """Toggle whether student feedback is shared with the student"""
        try:
            instructor_id = current_user["user_id"]
            
            async with db_manager.get_connection() as conn:
                # Verify instructor owns this feedback
                feedback_row = await conn.fetchrow("""
                    SELECT instructor_id FROM student_feedback WHERE feedback_id = $1
                """, uuid.UUID(feedback_id))
                
                if not feedback_row or str(feedback_row['instructor_id']) != instructor_id:
                    raise HTTPException(status_code=403, detail="You can only modify your own feedback")
                
                # Update sharing status
                result = await conn.execute("""
                    UPDATE student_feedback 
                    SET is_shared_with_student = $2, updated_at = $3
                    WHERE feedback_id = $1
                """, uuid.UUID(feedback_id), share, datetime.now())
                
                if result == "UPDATE 0":
                    raise HTTPException(status_code=404, detail="Feedback not found")
                
                return {"message": f"Feedback sharing {'enabled' if share else 'disabled'} successfully"}
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error toggling feedback sharing: {e}")
            raise HTTPException(status_code=500, detail="Failed to update feedback sharing")
    
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