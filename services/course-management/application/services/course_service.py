"""
Course Service Implementation
Single Responsibility: Implement course management business logic
Dependency Inversion: Depends on repository abstraction, not concrete implementation
"""
import uuid
from datetime import datetime
from typing import List, Optional
from ...domain.entities.course import Course, CourseStatistics, DifficultyLevel, DurationUnit
from ...domain.interfaces.course_repository import ICourseRepository
from ...domain.interfaces.course_service import ICourseService
from ...domain.interfaces.enrollment_repository import IEnrollmentRepository

class CourseService(ICourseService):
    """
    Course service implementation with business logic
    """
    
    def __init__(self, course_repository: ICourseRepository, enrollment_repository: IEnrollmentRepository):
        self._course_repository = course_repository
        self._enrollment_repository = enrollment_repository
    
    async def create_course(self, course: Course) -> Course:
        """Create a new course with business validation"""
        # Generate ID if not provided
        if not course.id:
            course.id = str(uuid.uuid4())
        
        # Set creation timestamp
        course.created_at = datetime.utcnow()
        course.updated_at = datetime.utcnow()
        
        # Validate business rules
        course.validate()
        
        # Create in repository
        return await self._course_repository.create(course)
    
    async def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        if not course_id:
            return None
        
        return await self._course_repository.get_by_id(course_id)
    
    async def get_courses_by_instructor(self, instructor_id: str) -> List[Course]:
        """Get all courses for an instructor"""
        if not instructor_id:
            return []
        
        return await self._course_repository.get_by_instructor_id(instructor_id)
    
    async def update_course(self, course: Course) -> Course:
        """Update an existing course with business validation"""
        if not course.id:
            raise ValueError("Course ID is required for update")
        
        # Check if course exists
        existing_course = await self._course_repository.get_by_id(course.id)
        if not existing_course:
            raise ValueError(f"Course with ID {course.id} not found")
        
        # Validate business rules
        course.validate()
        
        # Update timestamp
        course.updated_at = datetime.utcnow()
        
        return await self._course_repository.update(course)
    
    async def delete_course(self, course_id: str, instructor_id: str) -> bool:
        """Delete a course (only if instructor owns it)"""
        if not course_id or not instructor_id:
            raise ValueError("Course ID and instructor ID are required")
        
        # Check if course exists and belongs to instructor
        course = await self._course_repository.get_by_id(course_id)
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        if course.instructor_id != instructor_id:
            raise ValueError("Instructor can only delete their own courses")
        
        # Check if there are active enrollments
        enrollment_count = await self._enrollment_repository.count_active_by_course(course_id)
        if enrollment_count > 0:
            raise ValueError("Cannot delete course with active enrollments")
        
        return await self._course_repository.delete(course_id)
    
    async def publish_course(self, course_id: str, instructor_id: str) -> Course:
        """Publish a course with business validation"""
        if not course_id or not instructor_id:
            raise ValueError("Course ID and instructor ID are required")
        
        # Get course
        course = await self._course_repository.get_by_id(course_id)
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Check ownership
        if course.instructor_id != instructor_id:
            raise ValueError("Instructor can only publish their own courses")
        
        # Use business logic from entity
        course.publish()
        
        return await self._course_repository.update(course)
    
    async def unpublish_course(self, course_id: str, instructor_id: str) -> Course:
        """Unpublish a course"""
        if not course_id or not instructor_id:
            raise ValueError("Course ID and instructor ID are required")
        
        # Get course
        course = await self._course_repository.get_by_id(course_id)
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Check ownership
        if course.instructor_id != instructor_id:
            raise ValueError("Instructor can only unpublish their own courses")
        
        # Use business logic from entity
        course.unpublish()
        
        return await self._course_repository.update(course)
    
    async def get_published_courses(self, limit: int = 50, offset: int = 0) -> List[Course]:
        """Get all published courses with pagination"""
        if limit <= 0 or limit > 100:
            limit = 50
        
        if offset < 0:
            offset = 0
        
        return await self._course_repository.get_published_courses(limit, offset)
    
    async def search_courses(self, query: str, category: Optional[str] = None, 
                            difficulty: Optional[str] = None) -> List[Course]:
        """Search courses by criteria"""
        if not query or len(query.strip()) == 0:
            return []
        
        filters = {}
        if category:
            filters['category'] = category
        if difficulty:
            try:
                # Validate difficulty level
                DifficultyLevel(difficulty)
                filters['difficulty_level'] = difficulty
            except ValueError:
                pass  # Invalid difficulty level, ignore filter
        
        return await self._course_repository.search(query.strip(), filters)
    
    async def get_course_statistics(self, course_id: str) -> Optional[CourseStatistics]:
        """Get statistics for a course"""
        if not course_id:
            return None
        
        # Check if course exists
        course = await self._course_repository.get_by_id(course_id)
        if not course:
            return None
        
        return await self._course_repository.get_statistics(course_id)
    
    # Additional business methods
    async def duplicate_course(self, course_id: str, instructor_id: str, new_title: str) -> Course:
        """Duplicate an existing course"""
        # Get original course
        original_course = await self._course_repository.get_by_id(course_id)
        if not original_course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Check ownership
        if original_course.instructor_id != instructor_id:
            raise ValueError("Instructor can only duplicate their own courses")
        
        # Create duplicate
        duplicate_course = Course(
            title=new_title,
            description=original_course.description,
            instructor_id=instructor_id,
            category=original_course.category,
            difficulty_level=original_course.difficulty_level,
            estimated_duration=original_course.estimated_duration,
            duration_unit=original_course.duration_unit,
            price=original_course.price,
            tags=original_course.tags.copy(),
            is_published=False  # Duplicates start as unpublished
        )
        
        return await self.create_course(duplicate_course)
    
    async def archive_course(self, course_id: str, instructor_id: str) -> Course:
        """Archive a course (soft delete)"""
        # This could be implemented by adding an 'archived' field to the Course entity
        # For now, we'll unpublish the course
        return await self.unpublish_course(course_id, instructor_id)
    
    async def get_instructor_course_count(self, instructor_id: str) -> int:
        """Get count of courses for an instructor"""
        if not instructor_id:
            return 0
        
        return await self._course_repository.count_by_instructor(instructor_id)