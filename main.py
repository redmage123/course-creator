"""
Course Creator Platform - FastAPI Backend
Main application file with all routes and database integration
"""
import os
import asyncio
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr
import bcrypt

# Database imports
from shared.database.base import engine, get_database, Base
from shared.database.models import User, Course, Lesson, Enrollment

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = "student"

class UserLogin(BaseModel):
    username: str
    password: str

class CourseCreate(BaseModel):
    title: str
    description: str
    price: Optional[float] = None
    duration_hours: Optional[int] = None
    difficulty_level: Optional[str] = "beginner"

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_hours: Optional[int] = None
    difficulty_level: Optional[str] = None
    is_published: Optional[bool] = None

class LessonCreate(BaseModel):
    title: str
    content: str
    order_index: int
    duration_minutes: Optional[int] = None

class EnrollmentCreate(BaseModel):
    user_id: int
    course_id: int

# Database initialization
async def init_database():
    """Initialize database tables"""
    print("📊 Initializing database...")
    try:
        async with engine.begin() as conn:
            # Test connection first
            await conn.execute(select(1))
            # Create all tables (will skip if they exist)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created/verified")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    print("🚀 Starting Course Creator Platform...")
    
    # Initialize database
    db_success = await init_database()
    if not db_success:
        print("❌ Failed to initialize database. Exiting...")
        raise RuntimeError("Database initialization failed")
    
    print("✅ Application startup complete")
    yield
    print("🛑 Application shutdown")

# Create FastAPI application
app = FastAPI(
    title="Course Creator Platform API",
    description="Backend API for the Course Creator Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Root endpoint - API information
@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "name": "Course Creator Platform API",
        "version": "1.0.0",
        "description": "Backend API for the Course Creator Platform",
        "docs_url": "/docs",
        "health_url": "/health",
        "endpoints": {
            "courses": "/api/courses",
            "auth": "/api/auth",
            "users": "/api/users",
            "enrollments": "/api/enrollments",
            "dashboard": "/api/dashboard/stats"
        }
    }

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_database)):
    """Health check endpoint with database connectivity test"""
    try:
        # Test database connection
        await db.execute(select(1))
        
        # Get basic stats
        user_count = await db.execute(select(func.count(User.user_id)))
        course_count = await db.execute(select(func.count(Course.course_id)))
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "version": "1.0.0",
            "stats": {
                "total_users": user_count.scalar(),
                "total_courses": course_count.scalar()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "database": "disconnected",
                "error": str(e)
            }
        )

# User Authentication Endpoints
@app.post("/api/auth/register")
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_database)):
    """Register a new user"""
    try:
        # Check if username or email already exists
        existing_user = await db.execute(
            select(User).where(
                (User.username == user_data.username) | (User.email == user_data.email)
            )
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return {
            "message": "User registered successfully",
            "user": {
                "id": new_user.user_id,
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

@app.post("/api/auth/login")
async def login_user(login_data: UserLogin, db: AsyncSession = Depends(get_database)):
    """Authenticate user login"""
    try:
        # Find user
        result = await db.execute(
            select(User).where(User.username == login_data.username)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        return {
            "message": "Login successful",
            "user": {
                "id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

# User Management Endpoints
@app.get("/api/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_database)):
    """Get user profile by ID"""
    try:
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )

@app.get("/api/users")
async def get_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_database)):
    """Get list of users with pagination"""
    try:
        result = await db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        users = result.scalars().all()
        
        return {
            "users": [
                {
                    "id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                } for user in users
            ],
            "total": len(users)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

# Course Management Endpoints
@app.get("/api/courses")
async def get_courses(
    published_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_database)
):
    """Get list of courses with pagination"""
    try:
        query = select(Course, User).join(User, Course.instructor_id == User.user_id)
        
        if published_only:
            query = query.where(Course.is_published == True)
        
        query = query.order_by(Course.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        courses_data = result.all()
        
        courses = []
        for course, instructor in courses_data:
            courses.append({
                "id": course.course_id,
                "title": course.title,
                "description": course.description,
                "instructor": f"{instructor.first_name or ''} {instructor.last_name or ''}".strip() or instructor.username,
                "instructor_id": instructor.user_id,
                "price": float(course.price) if course.price else None,
                "duration_hours": course.duration_hours,
                "difficulty_level": course.difficulty_level,
                "is_published": course.is_published,
                "created_at": course.created_at.isoformat() if course.created_at else None
            })
        
        return {"courses": courses, "total": len(courses)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch courses: {str(e)}"
        )

@app.get("/api/courses/{course_id}")
async def get_course(course_id: int, db: AsyncSession = Depends(get_database)):
    """Get detailed course information including lessons"""
    try:
        # Get course with instructor
        result = await db.execute(
            select(Course, User)
            .join(User, Course.instructor_id == User.user_id)
            .where(Course.course_id == course_id)
        )
        course_data = result.first()
        
        if not course_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        course, instructor = course_data
        
        # Get lessons for this course
        lessons_result = await db.execute(
            select(Lesson)
            .where(Lesson.course_id == course_id)
            .order_by(Lesson.order_index)
        )
        lessons = lessons_result.scalars().all()
        
        # Get enrollment count
        enrollment_count_result = await db.execute(
            select(func.count(Enrollment.enrollment_id))
            .where(Enrollment.course_id == course_id)
        )
        enrollment_count = enrollment_count_result.scalar()
        
        return {
            "id": course.course_id,
            "title": course.title,
            "description": course.description,
            "instructor": f"{instructor.first_name or ''} {instructor.last_name or ''}".strip() or instructor.username,
            "instructor_id": instructor.user_id,
            "price": float(course.price) if course.price else None,
            "duration_hours": course.duration_hours,
            "difficulty_level": course.difficulty_level,
            "is_published": course.is_published,
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "enrollment_count": enrollment_count,
            "lesson_count": len(lessons),
            "lessons": [
                {
                    "id": lesson.lesson_id,
                    "title": lesson.title,
                    "content": lesson.content,
                    "order_index": lesson.order_index,
                    "duration_minutes": lesson.duration_minutes,
                    "created_at": lesson.created_at.isoformat() if lesson.created_at else None
                } for lesson in lessons
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch course: {str(e)}"
        )

@app.post("/api/courses")
async def create_course(course_data: CourseCreate, db: AsyncSession = Depends(get_database)):
    """Create a new course"""
    try:
        # For now, assign to first instructor user
        # In production, this would come from authenticated user
        instructor_result = await db.execute(
            select(User).where(User.role == "instructor").limit(1)
        )
        instructor = instructor_result.scalar_one_or_none()
        
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No instructor found. Please create an instructor user first"
            )
        
        new_course = Course(
            title=course_data.title,
            description=course_data.description,
            instructor_id=instructor.user_id,
            price=course_data.price,
            duration_hours=course_data.duration_hours,
            difficulty_level=course_data.difficulty_level,
            is_published=False  # New courses start as drafts
        )
        
        db.add(new_course)
        await db.commit()
        await db.refresh(new_course)
        
        return {
            "message": "Course created successfully",
            "course": {
                "id": new_course.course_id,
                "title": new_course.title,
                "description": new_course.description,
                "instructor_id": new_course.instructor_id,
                "price": float(new_course.price) if new_course.price else None,
                "difficulty_level": new_course.difficulty_level,
                "is_published": new_course.is_published
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course: {str(e)}"
        )

@app.put("/api/courses/{course_id}")
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: AsyncSession = Depends(get_database)
):
    """Update an existing course"""
    try:
        result = await db.execute(
            select(Course).where(Course.course_id == course_id)
        )
        course = result.scalar_one_or_none()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Update fields that were provided
        update_data = course_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        
        await db.commit()
        await db.refresh(course)
        
        return {
            "message": "Course updated successfully",
            "course": {
                "id": course.course_id,
                "title": course.title,
                "description": course.description,
                "price": float(course.price) if course.price else None,
                "difficulty_level": course.difficulty_level,
                "is_published": course.is_published
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update course: {str(e)}"
        )

# Lesson Management Endpoints
@app.post("/api/courses/{course_id}/lessons")
async def create_lesson(
    course_id: int,
    lesson_data: LessonCreate,
    db: AsyncSession = Depends(get_database)
):
    """Create a new lesson for a course"""
    try:
        # Verify course exists
        course_result = await db.execute(
            select(Course).where(Course.course_id == course_id)
        )
        course = course_result.scalar_one_or_none()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        new_lesson = Lesson(
            course_id=course_id,
            title=lesson_data.title,
            content=lesson_data.content,
            order_index=lesson_data.order_index,
            duration_minutes=lesson_data.duration_minutes
        )
        
        db.add(new_lesson)
        await db.commit()
        await db.refresh(new_lesson)
        
        return {
            "message": "Lesson created successfully",
            "lesson": {
                "id": new_lesson.lesson_id,
                "course_id": new_lesson.course_id,
                "title": new_lesson.title,
                "order_index": new_lesson.order_index,
                "duration_minutes": new_lesson.duration_minutes
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lesson: {str(e)}"
        )

# Enrollment Management Endpoints
@app.post("/api/enrollments")
async def create_enrollment(enrollment_data: EnrollmentCreate, db: AsyncSession = Depends(get_database)):
    """Enroll a user in a course"""
    try:
        # Check if already enrolled
        existing_enrollment = await db.execute(
            select(Enrollment).where(
                and_(
                    Enrollment.user_id == enrollment_data.user_id,
                    Enrollment.course_id == enrollment_data.course_id
                )
            )
        )
        if existing_enrollment.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already enrolled in this course"
            )
        
        # Verify course exists and is published
        course_result = await db.execute(
            select(Course).where(
                and_(
                    Course.course_id == enrollment_data.course_id,
                    Course.is_published == True
                )
            )
        )
        course = course_result.scalar_one_or_none()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or not published"
            )
        
        # Verify user exists
        user_result = await db.execute(
            select(User).where(User.user_id == enrollment_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        new_enrollment = Enrollment(
            user_id=enrollment_data.user_id,
            course_id=enrollment_data.course_id,
            completion_status="in_progress",
            progress_percentage=0
        )
        
        db.add(new_enrollment)
        await db.commit()
        await db.refresh(new_enrollment)
        
        return {
            "message": "Enrollment successful",
            "enrollment": {
                "id": new_enrollment.enrollment_id,
                "user_id": new_enrollment.user_id,
                "course_id": new_enrollment.course_id,
                "enrollment_date": new_enrollment.enrollment_date.isoformat(),
                "completion_status": new_enrollment.completion_status,
                "progress_percentage": new_enrollment.progress_percentage
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrollment failed: {str(e)}"
        )

@app.get("/api/users/{user_id}/enrollments")
async def get_user_enrollments(user_id: int, db: AsyncSession = Depends(get_database)):
    """Get all courses a user is enrolled in"""
    try:
        result = await db.execute(
            select(Enrollment, Course, User)
            .join(Course, Enrollment.course_id == Course.course_id)
            .join(User, Course.instructor_id == User.user_id)
            .where(Enrollment.user_id == user_id)
            .order_by(Enrollment.enrollment_date.desc())
        )
        enrollments_data = result.all()
        
        enrollments = []
        for enrollment, course, instructor in enrollments_data:
            enrollments.append({
                "enrollment_id": enrollment.enrollment_id,
                "course": {
                    "id": course.course_id,
                    "title": course.title,
                    "description": course.description,
                    "instructor": f"{instructor.first_name or ''} {instructor.last_name or ''}".strip() or instructor.username,
                    "difficulty_level": course.difficulty_level,
                    "duration_hours": course.duration_hours
                },
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "completion_status": enrollment.completion_status,
                "progress_percentage": enrollment.progress_percentage
            })
        
        return {"enrollments": enrollments, "total": len(enrollments)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch enrollments: {str(e)}"
        )

# Dashboard and Analytics Endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_database)):
    """Get dashboard statistics and analytics"""
    try:
        # Get various counts
        total_courses_result = await db.execute(select(func.count(Course.course_id)))
        total_courses = total_courses_result.scalar()
        
        published_courses_result = await db.execute(
            select(func.count(Course.course_id)).where(Course.is_published == True)
        )
        published_courses = published_courses_result.scalar()
        
        total_users_result = await db.execute(select(func.count(User.user_id)))
        total_users = total_users_result.scalar()
        
        total_enrollments_result = await db.execute(select(func.count(Enrollment.enrollment_id)))
        total_enrollments = total_enrollments_result.scalar()
        
        # Get user counts by role
        students_result = await db.execute(
            select(func.count(User.user_id)).where(User.role == "student")
        )
        total_students = students_result.scalar()
        
        instructors_result = await db.execute(
            select(func.count(User.user_id)).where(User.role == "instructor")
        )
        total_instructors = instructors_result.scalar()
        
        return {
            "courses": {
                "total": total_courses,
                "published": published_courses,
                "draft": total_courses - published_courses
            },
            "users": {
                "total": total_users,
                "students": total_students,
                "instructors": total_instructors
            },
            "enrollments": {
                "total": total_enrollments
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )

# Search and Filter Endpoints
@app.get("/api/courses/search")
async def search_courses(
    q: str = "",
    difficulty: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: AsyncSession = Depends(get_database)
):
    """Search and filter courses"""
    try:
        query = select(Course, User).join(User, Course.instructor_id == User.user_id).where(Course.is_published == True)
        
        # Text search in title and description
        if q:
            query = query.where(
                (Course.title.ilike(f"%{q}%")) | (Course.description.ilike(f"%{q}%"))
            )
        
        # Filter by difficulty
        if difficulty:
            query = query.where(Course.difficulty_level == difficulty)
        
        # Filter by price range
        if min_price is not None:
            query = query.where(Course.price >= min_price)
        if max_price is not None:
            query = query.where(Course.price <= max_price)
        
        result = await db.execute(query.order_by(Course.created_at.desc()))
        courses_data = result.all()
        
        courses = []
        for course, instructor in courses_data:
            courses.append({
                "id": course.course_id,
                "title": course.title,
                "description": course.description,
                "instructor": f"{instructor.first_name or ''} {instructor.last_name or ''}".strip() or instructor.username,
                "price": float(course.price) if course.price else None,
                "duration_hours": course.duration_hours,
                "difficulty_level": course.difficulty_level,
                "created_at": course.created_at.isoformat() if course.created_at else None
            })
        
        return {"courses": courses, "total": len(courses), "query": q}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
