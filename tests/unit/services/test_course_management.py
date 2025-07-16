"""
Unit tests for Course Management Service

Tests all components of the course management service including:
- Course models validation
- Course repositories
- Course services
- Enrollment management
- API routes
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException
from decimal import Decimal
import uuid

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/course-management'))

from models.course import (
    Course, CourseCreate, CourseUpdate, CourseResponse, 
    CourseDifficulty, CourseCategory, CourseStatus
)
from models.enrollment import (
    Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse,
    EnrollmentStatus
)
from models.common import BaseModel, ErrorResponse, SuccessResponse
from repositories.course_repository import CourseRepository
from repositories.enrollment_repository import EnrollmentRepository
from services.course_service import CourseService
from services.enrollment_service import EnrollmentService


class TestCourseModels:
    """Test course data models."""
    
    def test_course_base_model_validation(self):
        """Test basic course model validation."""
        course_data = {
            "title": "Test Course",
            "description": "A test course description",
            "instructor_id": str(uuid.uuid4()),
            "difficulty": CourseDifficulty.BEGINNER,
            "category": CourseCategory.PROGRAMMING
        }
        
        course_create = CourseCreate(**course_data)
        assert course_create.title == "Test Course"
        assert course_create.description == "A test course description"
        assert course_create.difficulty == CourseDifficulty.BEGINNER
        assert course_create.category == CourseCategory.PROGRAMMING
        assert course_create.is_published is False  # Default
    
    def test_course_title_validation(self):
        """Test course title validation."""
        # Title too short
        with pytest.raises(ValueError):
            CourseCreate(
                title="AB",
                description="Description",
                instructor_id=str(uuid.uuid4())
            )
        
        # Title too long
        with pytest.raises(ValueError):
            CourseCreate(
                title="A" * 201,
                description="Description",
                instructor_id=str(uuid.uuid4())
            )
    
    def test_course_difficulty_validation(self):
        """Test course difficulty validation."""
        for difficulty in [CourseDifficulty.BEGINNER, CourseDifficulty.INTERMEDIATE, CourseDifficulty.ADVANCED]:
            course = CourseCreate(
                title="Test Course",
                description="Description",
                instructor_id=str(uuid.uuid4()),
                difficulty=difficulty
            )
            assert course.difficulty == difficulty
    
    def test_course_category_validation(self):
        """Test course category validation."""
        for category in [CourseCategory.PROGRAMMING, CourseCategory.DATA_SCIENCE, CourseCategory.DESIGN]:
            course = CourseCreate(
                title="Test Course",
                description="Description",
                instructor_id=str(uuid.uuid4()),
                category=category
            )
            assert course.category == category
    
    def test_course_price_validation(self):
        """Test course price validation."""
        # Valid price
        course = CourseCreate(
            title="Test Course",
            description="Description",
            instructor_id=str(uuid.uuid4()),
            price=Decimal("99.99")
        )
        assert course.price == Decimal("99.99")
        
        # Negative price should raise error
        with pytest.raises(ValueError):
            CourseCreate(
                title="Test Course",
                description="Description",
                instructor_id=str(uuid.uuid4()),
                price=Decimal("-10.00")
            )
    
    def test_course_duration_validation(self):
        """Test course duration validation."""
        # Valid duration
        course = CourseCreate(
            title="Test Course",
            description="Description",
            instructor_id=str(uuid.uuid4()),
            duration_hours=40
        )
        assert course.duration_hours == 40
        
        # Invalid duration (negative)
        with pytest.raises(ValueError):
            CourseCreate(
                title="Test Course",
                description="Description",
                instructor_id=str(uuid.uuid4()),
                duration_hours=-5
            )


class TestEnrollmentModels:
    """Test enrollment data models."""
    
    def test_enrollment_base_model_validation(self):
        """Test basic enrollment model validation."""
        enrollment_data = {
            "student_id": str(uuid.uuid4()),
            "course_id": str(uuid.uuid4()),
            "status": EnrollmentStatus.ACTIVE
        }
        
        enrollment_create = EnrollmentCreate(**enrollment_data)
        assert enrollment_create.student_id == enrollment_data["student_id"]
        assert enrollment_create.course_id == enrollment_data["course_id"]
        assert enrollment_create.status == EnrollmentStatus.ACTIVE
    
    def test_enrollment_status_validation(self):
        """Test enrollment status validation."""
        for status in [EnrollmentStatus.PENDING, EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED, EnrollmentStatus.CANCELLED]:
            enrollment = EnrollmentCreate(
                student_id=str(uuid.uuid4()),
                course_id=str(uuid.uuid4()),
                status=status
            )
            assert enrollment.status == status
    
    def test_enrollment_progress_validation(self):
        """Test enrollment progress validation."""
        # Valid progress
        enrollment = EnrollmentCreate(
            student_id=str(uuid.uuid4()),
            course_id=str(uuid.uuid4()),
            progress=75.5
        )
        assert enrollment.progress == 75.5
        
        # Invalid progress (over 100)
        with pytest.raises(ValueError):
            EnrollmentCreate(
                student_id=str(uuid.uuid4()),
                course_id=str(uuid.uuid4()),
                progress=150.0
            )
        
        # Invalid progress (negative)
        with pytest.raises(ValueError):
            EnrollmentCreate(
                student_id=str(uuid.uuid4()),
                course_id=str(uuid.uuid4()),
                progress=-10.0
            )


class TestCourseRepository:
    """Test course repository operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_pool = AsyncMock()
        self.course_repository = CourseRepository(self.mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_create_course(self):
        """Test course creation."""
        course_data = CourseCreate(
            title="Test Course",
            description="A test course",
            instructor_id=str(uuid.uuid4()),
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING
        )
        
        # Mock database response
        mock_row = {
            "id": str(uuid.uuid4()),
            "title": course_data.title,
            "description": course_data.description,
            "instructor_id": course_data.instructor_id,
            "difficulty": course_data.difficulty.value,
            "category": course_data.category.value,
            "is_published": False,
            "price": None,
            "duration_hours": None,
            "max_students": None,
            "enrolled_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        course = await self.course_repository.create_course(course_data)
        
        assert course is not None
        assert course.title == course_data.title
        assert course.description == course_data.description
        assert course.instructor_id == course_data.instructor_id
        assert course.difficulty == course_data.difficulty
        assert course.category == course_data.category
    
    @pytest.mark.asyncio
    async def test_get_course_by_id(self):
        """Test getting course by ID."""
        course_id = str(uuid.uuid4())
        
        mock_row = {
            "id": course_id,
            "title": "Test Course",
            "description": "A test course",
            "instructor_id": str(uuid.uuid4()),
            "difficulty": "beginner",
            "category": "programming",
            "is_published": True,
            "price": None,
            "duration_hours": 40,
            "max_students": 100,
            "enrolled_count": 25,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        course = await self.course_repository.get_course_by_id(course_id)
        
        assert course is not None
        assert course.id == course_id
        assert course.title == "Test Course"
        assert course.enrolled_count == 25
    
    @pytest.mark.asyncio
    async def test_get_courses_by_instructor(self):
        """Test getting courses by instructor."""
        instructor_id = str(uuid.uuid4())
        
        mock_rows = [
            {
                "id": str(uuid.uuid4()),
                "title": "Course 1",
                "description": "Description 1",
                "instructor_id": instructor_id,
                "difficulty": "beginner",
                "category": "programming",
                "is_published": True,
                "price": None,
                "duration_hours": 40,
                "max_students": 100,
                "enrolled_count": 25,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Course 2",
                "description": "Description 2",
                "instructor_id": instructor_id,
                "difficulty": "intermediate",
                "category": "data_science",
                "is_published": False,
                "price": None,
                "duration_hours": 60,
                "max_students": 50,
                "enrolled_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        courses = await self.course_repository.get_courses_by_instructor(instructor_id)
        
        assert len(courses) == 2
        assert courses[0].title == "Course 1"
        assert courses[1].title == "Course 2"
        assert all(course.instructor_id == instructor_id for course in courses)
    
    @pytest.mark.asyncio
    async def test_update_course(self):
        """Test course update."""
        course_id = str(uuid.uuid4())
        update_data = CourseUpdate(
            title="Updated Course",
            description="Updated description",
            is_published=True
        )
        
        mock_row = {
            "id": course_id,
            "title": "Updated Course",
            "description": "Updated description",
            "instructor_id": str(uuid.uuid4()),
            "difficulty": "beginner",
            "category": "programming",
            "is_published": True,
            "price": None,
            "duration_hours": 40,
            "max_students": 100,
            "enrolled_count": 25,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        course = await self.course_repository.update_course(course_id, update_data)
        
        assert course is not None
        assert course.title == "Updated Course"
        assert course.description == "Updated description"
        assert course.is_published is True
    
    @pytest.mark.asyncio
    async def test_delete_course(self):
        """Test course deletion."""
        course_id = str(uuid.uuid4())
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"id": course_id}
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.course_repository.delete_course(course_id)
        
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_courses(self):
        """Test course search."""
        search_params = {
            "query": "python",
            "category": "programming",
            "difficulty": "beginner",
            "is_published": True
        }
        
        mock_rows = [
            {
                "id": str(uuid.uuid4()),
                "title": "Python Basics",
                "description": "Learn Python programming",
                "instructor_id": str(uuid.uuid4()),
                "difficulty": "beginner",
                "category": "programming",
                "is_published": True,
                "price": None,
                "duration_hours": 40,
                "max_students": 100,
                "enrolled_count": 25,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        courses = await self.course_repository.search_courses(search_params)
        
        assert len(courses) == 1
        assert courses[0].title == "Python Basics"
        assert courses[0].category == CourseCategory.PROGRAMMING
    
    @pytest.mark.asyncio
    async def test_get_course_stats(self):
        """Test getting course statistics."""
        course_id = str(uuid.uuid4())
        
        mock_row = {
            "total_enrollments": 50,
            "active_enrollments": 35,
            "completed_enrollments": 15,
            "average_progress": 75.5,
            "completion_rate": 30.0
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        stats = await self.course_repository.get_course_stats(course_id)
        
        assert stats["total_enrollments"] == 50
        assert stats["active_enrollments"] == 35
        assert stats["completed_enrollments"] == 15
        assert stats["average_progress"] == 75.5
        assert stats["completion_rate"] == 30.0


class TestEnrollmentRepository:
    """Test enrollment repository operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_pool = AsyncMock()
        self.enrollment_repository = EnrollmentRepository(self.mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_create_enrollment(self):
        """Test enrollment creation."""
        enrollment_data = EnrollmentCreate(
            student_id=str(uuid.uuid4()),
            course_id=str(uuid.uuid4()),
            status=EnrollmentStatus.ACTIVE
        )
        
        mock_row = {
            "id": str(uuid.uuid4()),
            "student_id": enrollment_data.student_id,
            "course_id": enrollment_data.course_id,
            "status": enrollment_data.status.value,
            "progress": 0.0,
            "enrolled_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        enrollment = await self.enrollment_repository.create_enrollment(enrollment_data)
        
        assert enrollment is not None
        assert enrollment.student_id == enrollment_data.student_id
        assert enrollment.course_id == enrollment_data.course_id
        assert enrollment.status == enrollment_data.status
    
    @pytest.mark.asyncio
    async def test_get_enrollment_by_id(self):
        """Test getting enrollment by ID."""
        enrollment_id = str(uuid.uuid4())
        
        mock_row = {
            "id": enrollment_id,
            "student_id": str(uuid.uuid4()),
            "course_id": str(uuid.uuid4()),
            "status": "active",
            "progress": 50.0,
            "enrolled_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        enrollment = await self.enrollment_repository.get_enrollment_by_id(enrollment_id)
        
        assert enrollment is not None
        assert enrollment.id == enrollment_id
        assert enrollment.progress == 50.0
    
    @pytest.mark.asyncio
    async def test_get_student_enrollments(self):
        """Test getting student enrollments."""
        student_id = str(uuid.uuid4())
        
        mock_rows = [
            {
                "id": str(uuid.uuid4()),
                "student_id": student_id,
                "course_id": str(uuid.uuid4()),
                "status": "active",
                "progress": 25.0,
                "enrolled_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "completed_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "student_id": student_id,
                "course_id": str(uuid.uuid4()),
                "status": "completed",
                "progress": 100.0,
                "enrolled_at": datetime.utcnow() - timedelta(days=30),
                "last_activity": datetime.utcnow() - timedelta(days=1),
                "completed_at": datetime.utcnow() - timedelta(days=1),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        enrollments = await self.enrollment_repository.get_student_enrollments(student_id)
        
        assert len(enrollments) == 2
        assert enrollments[0].progress == 25.0
        assert enrollments[1].progress == 100.0
        assert all(enrollment.student_id == student_id for enrollment in enrollments)
    
    @pytest.mark.asyncio
    async def test_get_course_enrollments(self):
        """Test getting course enrollments."""
        course_id = str(uuid.uuid4())
        
        mock_rows = [
            {
                "id": str(uuid.uuid4()),
                "student_id": str(uuid.uuid4()),
                "course_id": course_id,
                "status": "active",
                "progress": 60.0,
                "enrolled_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "completed_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        enrollments = await self.enrollment_repository.get_course_enrollments(course_id)
        
        assert len(enrollments) == 1
        assert enrollments[0].course_id == course_id
        assert enrollments[0].progress == 60.0
    
    @pytest.mark.asyncio
    async def test_update_enrollment(self):
        """Test enrollment update."""
        enrollment_id = str(uuid.uuid4())
        update_data = EnrollmentUpdate(
            progress=75.0,
            status=EnrollmentStatus.ACTIVE
        )
        
        mock_row = {
            "id": enrollment_id,
            "student_id": str(uuid.uuid4()),
            "course_id": str(uuid.uuid4()),
            "status": "active",
            "progress": 75.0,
            "enrolled_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        enrollment = await self.enrollment_repository.update_enrollment(enrollment_id, update_data)
        
        assert enrollment is not None
        assert enrollment.progress == 75.0
        assert enrollment.status == EnrollmentStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_delete_enrollment(self):
        """Test enrollment deletion."""
        enrollment_id = str(uuid.uuid4())
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"id": enrollment_id}
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.enrollment_repository.delete_enrollment(enrollment_id)
        
        assert result is True
        mock_conn.execute.assert_called_once()


class TestCourseService:
    """Test course service business logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_course_repo = AsyncMock()
        self.mock_enrollment_repo = AsyncMock()
        self.course_service = CourseService(self.mock_course_repo, self.mock_enrollment_repo)
    
    @pytest.mark.asyncio
    async def test_create_course(self):
        """Test course creation."""
        course_data = CourseCreate(
            title="Test Course",
            description="A test course",
            instructor_id=str(uuid.uuid4()),
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING
        )
        
        mock_course = Course(
            id=str(uuid.uuid4()),
            title=course_data.title,
            description=course_data.description,
            instructor_id=course_data.instructor_id,
            difficulty=course_data.difficulty,
            category=course_data.category,
            is_published=False,
            enrolled_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_course_repo.create_course.return_value = mock_course
        
        result = await self.course_service.create_course(course_data)
        
        assert result is not None
        assert result.title == course_data.title
        assert result.instructor_id == course_data.instructor_id
        
        self.mock_course_repo.create_course.assert_called_once_with(course_data)
    
    @pytest.mark.asyncio
    async def test_get_course_by_id(self):
        """Test getting course by ID."""
        course_id = str(uuid.uuid4())
        
        mock_course = Course(
            id=course_id,
            title="Test Course",
            description="A test course",
            instructor_id=str(uuid.uuid4()),
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING,
            is_published=True,
            enrolled_count=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_course_repo.get_course_by_id.return_value = mock_course
        
        result = await self.course_service.get_course_by_id(course_id)
        
        assert result is not None
        assert result.id == course_id
        assert result.title == "Test Course"
        
        self.mock_course_repo.get_course_by_id.assert_called_once_with(course_id)
    
    @pytest.mark.asyncio
    async def test_publish_course(self):
        """Test course publishing."""
        course_id = str(uuid.uuid4())
        
        # Mock original course
        original_course = Course(
            id=course_id,
            title="Test Course",
            description="A test course",
            instructor_id=str(uuid.uuid4()),
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING,
            is_published=False,
            enrolled_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock updated course
        updated_course = Course(
            id=course_id,
            title="Test Course",
            description="A test course",
            instructor_id=original_course.instructor_id,
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING,
            is_published=True,
            enrolled_count=0,
            created_at=original_course.created_at,
            updated_at=datetime.utcnow()
        )
        
        self.mock_course_repo.get_course_by_id.return_value = original_course
        self.mock_course_repo.update_course.return_value = updated_course
        
        result = await self.course_service.publish_course(course_id)
        
        assert result is True
        
        # Verify the update was called with is_published=True
        self.mock_course_repo.update_course.assert_called_once()
        update_call_args = self.mock_course_repo.update_course.call_args[0]
        assert update_call_args[0] == course_id
        assert update_call_args[1].is_published is True
    
    @pytest.mark.asyncio
    async def test_unpublish_course(self):
        """Test course unpublishing."""
        course_id = str(uuid.uuid4())
        
        # Mock published course
        published_course = Course(
            id=course_id,
            title="Test Course",
            description="A test course",
            instructor_id=str(uuid.uuid4()),
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING,
            is_published=True,
            enrolled_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock unpublished course
        unpublished_course = Course(
            id=course_id,
            title="Test Course",
            description="A test course",
            instructor_id=published_course.instructor_id,
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING,
            is_published=False,
            enrolled_count=0,
            created_at=published_course.created_at,
            updated_at=datetime.utcnow()
        )
        
        self.mock_course_repo.get_course_by_id.return_value = published_course
        self.mock_course_repo.update_course.return_value = unpublished_course
        
        result = await self.course_service.unpublish_course(course_id)
        
        assert result is True
        
        # Verify the update was called with is_published=False
        self.mock_course_repo.update_course.assert_called_once()
        update_call_args = self.mock_course_repo.update_course.call_args[0]
        assert update_call_args[0] == course_id
        assert update_call_args[1].is_published is False
    
    @pytest.mark.asyncio
    async def test_get_instructor_courses(self):
        """Test getting instructor courses."""
        instructor_id = str(uuid.uuid4())
        
        mock_courses = [
            Course(
                id=str(uuid.uuid4()),
                title="Course 1",
                description="Description 1",
                instructor_id=instructor_id,
                difficulty=CourseDifficulty.BEGINNER,
                category=CourseCategory.PROGRAMMING,
                is_published=True,
                enrolled_count=10,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Course(
                id=str(uuid.uuid4()),
                title="Course 2",
                description="Description 2",
                instructor_id=instructor_id,
                difficulty=CourseDifficulty.INTERMEDIATE,
                category=CourseCategory.DATA_SCIENCE,
                is_published=False,
                enrolled_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        self.mock_course_repo.get_courses_by_instructor.return_value = mock_courses
        
        result = await self.course_service.get_instructor_courses(instructor_id)
        
        assert len(result) == 2
        assert result[0].title == "Course 1"
        assert result[1].title == "Course 2"
        assert all(course.instructor_id == instructor_id for course in result)
        
        self.mock_course_repo.get_courses_by_instructor.assert_called_once_with(instructor_id)
    
    @pytest.mark.asyncio
    async def test_get_course_statistics(self):
        """Test getting course statistics."""
        course_id = str(uuid.uuid4())
        
        mock_stats = {
            "total_enrollments": 50,
            "active_enrollments": 35,
            "completed_enrollments": 15,
            "average_progress": 75.5,
            "completion_rate": 30.0
        }
        
        self.mock_course_repo.get_course_stats.return_value = mock_stats
        
        result = await self.course_service.get_course_statistics(course_id)
        
        assert result["total_enrollments"] == 50
        assert result["active_enrollments"] == 35
        assert result["completion_rate"] == 30.0
        
        self.mock_course_repo.get_course_stats.assert_called_once_with(course_id)


class TestEnrollmentService:
    """Test enrollment service business logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_enrollment_repo = AsyncMock()
        self.mock_course_repo = AsyncMock()
        self.enrollment_service = EnrollmentService(self.mock_enrollment_repo, self.mock_course_repo)
    
    @pytest.mark.asyncio
    async def test_enroll_student(self):
        """Test student enrollment."""
        student_id = str(uuid.uuid4())
        course_id = str(uuid.uuid4())
        
        # Mock course exists and is published
        mock_course = Course(
            id=course_id,
            title="Test Course",
            description="A test course",
            instructor_id=str(uuid.uuid4()),
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING,
            is_published=True,
            enrolled_count=10,
            max_students=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock no existing enrollment
        self.mock_enrollment_repo.get_enrollment_by_student_and_course.return_value = None
        self.mock_course_repo.get_course_by_id.return_value = mock_course
        
        # Mock created enrollment
        mock_enrollment = Enrollment(
            id=str(uuid.uuid4()),
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.ACTIVE,
            progress=0.0,
            enrolled_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_enrollment_repo.create_enrollment.return_value = mock_enrollment
        
        result = await self.enrollment_service.enroll_student(student_id, course_id)
        
        assert result is not None
        assert result.student_id == student_id
        assert result.course_id == course_id
        assert result.status == EnrollmentStatus.ACTIVE
        
        # Verify dependencies were called
        self.mock_course_repo.get_course_by_id.assert_called_once_with(course_id)
        self.mock_enrollment_repo.get_enrollment_by_student_and_course.assert_called_once_with(student_id, course_id)
        self.mock_enrollment_repo.create_enrollment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enroll_student_already_enrolled(self):
        """Test enrolling student who is already enrolled."""
        student_id = str(uuid.uuid4())
        course_id = str(uuid.uuid4())
        
        # Mock existing enrollment
        existing_enrollment = Enrollment(
            id=str(uuid.uuid4()),
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.ACTIVE,
            progress=50.0,
            enrolled_at=datetime.utcnow() - timedelta(days=10),
            last_activity=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_enrollment_repo.get_enrollment_by_student_and_course.return_value = existing_enrollment
        
        with pytest.raises(HTTPException) as exc_info:
            await self.enrollment_service.enroll_student(student_id, course_id)
        
        assert exc_info.value.status_code == 400
        assert "already enrolled" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_enroll_student_course_not_published(self):
        """Test enrolling in unpublished course."""
        student_id = str(uuid.uuid4())
        course_id = str(uuid.uuid4())
        
        # Mock unpublished course
        mock_course = Course(
            id=course_id,
            title="Test Course",
            description="A test course",
            instructor_id=str(uuid.uuid4()),
            difficulty=CourseDifficulty.BEGINNER,
            category=CourseCategory.PROGRAMMING,
            is_published=False,
            enrolled_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.mock_enrollment_repo.get_enrollment_by_student_and_course.return_value = None
        self.mock_course_repo.get_course_by_id.return_value = mock_course
        
        with pytest.raises(HTTPException) as exc_info:
            await self.enrollment_service.enroll_student(student_id, course_id)
        
        assert exc_info.value.status_code == 400
        assert "not published" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_enrollment_progress(self):
        """Test updating enrollment progress."""
        enrollment_id = str(uuid.uuid4())
        new_progress = 75.0
        
        # Mock existing enrollment
        existing_enrollment = Enrollment(
            id=enrollment_id,
            student_id=str(uuid.uuid4()),
            course_id=str(uuid.uuid4()),
            status=EnrollmentStatus.ACTIVE,
            progress=50.0,
            enrolled_at=datetime.utcnow() - timedelta(days=10),
            last_activity=datetime.utcnow() - timedelta(hours=1),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock updated enrollment
        updated_enrollment = Enrollment(
            id=enrollment_id,
            student_id=existing_enrollment.student_id,
            course_id=existing_enrollment.course_id,
            status=EnrollmentStatus.ACTIVE,
            progress=new_progress,
            enrolled_at=existing_enrollment.enrolled_at,
            last_activity=datetime.utcnow(),
            created_at=existing_enrollment.created_at,
            updated_at=datetime.utcnow()
        )
        
        self.mock_enrollment_repo.get_enrollment_by_id.return_value = existing_enrollment
        self.mock_enrollment_repo.update_enrollment.return_value = updated_enrollment
        
        result = await self.enrollment_service.update_enrollment_progress(enrollment_id, new_progress)
        
        assert result is not None
        assert result.progress == new_progress
        
        # Verify dependencies were called
        self.mock_enrollment_repo.get_enrollment_by_id.assert_called_once_with(enrollment_id)
        self.mock_enrollment_repo.update_enrollment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_enrollment(self):
        """Test completing an enrollment."""
        enrollment_id = str(uuid.uuid4())
        
        # Mock active enrollment
        active_enrollment = Enrollment(
            id=enrollment_id,
            student_id=str(uuid.uuid4()),
            course_id=str(uuid.uuid4()),
            status=EnrollmentStatus.ACTIVE,
            progress=100.0,
            enrolled_at=datetime.utcnow() - timedelta(days=10),
            last_activity=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock completed enrollment
        completed_enrollment = Enrollment(
            id=enrollment_id,
            student_id=active_enrollment.student_id,
            course_id=active_enrollment.course_id,
            status=EnrollmentStatus.COMPLETED,
            progress=100.0,
            enrolled_at=active_enrollment.enrolled_at,
            last_activity=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            created_at=active_enrollment.created_at,
            updated_at=datetime.utcnow()
        )
        
        self.mock_enrollment_repo.get_enrollment_by_id.return_value = active_enrollment
        self.mock_enrollment_repo.update_enrollment.return_value = completed_enrollment
        
        result = await self.enrollment_service.complete_enrollment(enrollment_id)
        
        assert result is not None
        assert result.status == EnrollmentStatus.COMPLETED
        assert result.completed_at is not None
        
        # Verify dependencies were called
        self.mock_enrollment_repo.get_enrollment_by_id.assert_called_once_with(enrollment_id)
        self.mock_enrollment_repo.update_enrollment.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])