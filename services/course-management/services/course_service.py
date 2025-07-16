"""
Course Service

Business logic for course management operations.
"""

import logging
from typing import Optional, List, Dict, Any

from ..repositories.course_repository import CourseRepository
from ..repositories.enrollment_repository import EnrollmentRepository
from ..models.course import Course, CourseCreate, CourseUpdate, CourseSearchRequest, CourseStats


class CourseService:
    """
    Service for course management operations.
    
    Handles business logic for course-related operations.
    """
    
    def __init__(self, course_repository: CourseRepository, 
                 enrollment_repository: EnrollmentRepository):
        """
        Initialize course service.
        
        Args:
            course_repository: Course repository
            enrollment_repository: Enrollment repository
        """
        self.course_repository = course_repository
        self.enrollment_repository = enrollment_repository
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def create_course(self, course_data: CourseCreate) -> Optional[Course]:
        """
        Create a new course.
        
        Args:
            course_data: Course creation data
            
        Returns:
            Created course or None if creation fails
        """
        try:
            # Validate course data
            if not course_data.title.strip():
                raise ValueError("Course title cannot be empty")
            
            if not course_data.description.strip():
                raise ValueError("Course description cannot be empty")
            
            # Create course
            course = await self.course_repository.create_course(course_data)
            
            if course:
                self.logger.info(f"Course created successfully: {course.title}")
                return course
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating course: {e}")
            raise
    
    async def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """
        Get course by ID.
        
        Args:
            course_id: Course ID
            
        Returns:
            Course or None if not found
        """
        try:
            return await self.course_repository.get_course_by_id(course_id)
            
        except Exception as e:
            self.logger.error(f"Error getting course by ID {course_id}: {e}")
            raise
    
    async def get_courses_by_instructor(self, instructor_id: str, 
                                      limit: int = 100, offset: int = 0) -> List[Course]:
        """
        Get courses by instructor.
        
        Args:
            instructor_id: Instructor ID
            limit: Maximum number of courses to return
            offset: Number of courses to skip
            
        Returns:
            List of courses
        """
        try:
            courses = await self.course_repository.get_courses_by_instructor(
                instructor_id, limit, offset
            )
            
            # Enrich courses with enrollment statistics
            enriched_courses = []
            for course in courses:
                # Get enrollment statistics
                stats = await self._get_course_enrollment_stats(course.id)
                
                # Add statistics to course
                course.total_enrollments = stats.get('total_enrollments', 0)
                course.active_enrollments = stats.get('active_enrollments', 0)
                course.completion_rate = stats.get('completion_rate', 0.0)
                
                enriched_courses.append(course)
            
            return enriched_courses
            
        except Exception as e:
            self.logger.error(f"Error getting courses by instructor {instructor_id}: {e}")
            raise
    
    async def update_course(self, course_id: str, updates: CourseUpdate) -> Optional[Course]:
        """
        Update course information.
        
        Args:
            course_id: Course ID
            updates: Updates to apply
            
        Returns:
            Updated course or None if not found
        """
        try:
            # Validate updates
            if updates.title is not None and not updates.title.strip():
                raise ValueError("Course title cannot be empty")
            
            if updates.description is not None and not updates.description.strip():
                raise ValueError("Course description cannot be empty")
            
            # Update course
            course = await self.course_repository.update_course(course_id, updates)
            
            if course:
                self.logger.info(f"Course updated successfully: {course.title}")
                return course
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating course {course_id}: {e}")
            raise
    
    async def delete_course(self, course_id: str) -> bool:
        """
        Delete a course.
        
        Args:
            course_id: Course ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if course has enrollments
            enrollment_count = await self.enrollment_repository.count_enrollments(
                course_id=course_id
            )
            
            if enrollment_count > 0:
                raise ValueError(f"Cannot delete course with {enrollment_count} enrollments")
            
            # Delete course
            success = await self.course_repository.delete_course(course_id)
            
            if success:
                self.logger.info(f"Course deleted successfully: {course_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting course {course_id}: {e}")
            raise
    
    async def search_courses(self, search_request: CourseSearchRequest,
                           limit: int = 100, offset: int = 0) -> List[Course]:
        """
        Search courses.
        
        Args:
            search_request: Search criteria
            limit: Maximum number of courses to return
            offset: Number of courses to skip
            
        Returns:
            List of matching courses
        """
        try:
            return await self.course_repository.search_courses(
                search_request, limit, offset
            )
            
        except Exception as e:
            self.logger.error(f"Error searching courses: {e}")
            raise
    
    async def get_published_courses(self, limit: int = 100, offset: int = 0) -> List[Course]:
        """
        Get published courses.
        
        Args:
            limit: Maximum number of courses to return
            offset: Number of courses to skip
            
        Returns:
            List of published courses
        """
        try:
            return await self.course_repository.get_published_courses(limit, offset)
            
        except Exception as e:
            self.logger.error(f"Error getting published courses: {e}")
            raise
    
    async def publish_course(self, course_id: str) -> bool:
        """
        Publish a course.
        
        Args:
            course_id: Course ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get course to validate it exists
            course = await self.course_repository.get_course_by_id(course_id)
            if not course:
                raise ValueError("Course not found")
            
            # Validate course is ready for publishing
            if not course.title.strip():
                raise ValueError("Course must have a title to be published")
            
            if not course.description.strip():
                raise ValueError("Course must have a description to be published")
            
            # Update course to published
            updates = CourseUpdate(is_published=True)
            updated_course = await self.course_repository.update_course(course_id, updates)
            
            if updated_course:
                self.logger.info(f"Course published successfully: {course.title}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error publishing course {course_id}: {e}")
            raise
    
    async def unpublish_course(self, course_id: str) -> bool:
        """
        Unpublish a course.
        
        Args:
            course_id: Course ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update course to unpublished
            updates = CourseUpdate(is_published=False)
            updated_course = await self.course_repository.update_course(course_id, updates)
            
            if updated_course:
                self.logger.info(f"Course unpublished successfully: {course_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error unpublishing course {course_id}: {e}")
            raise
    
    async def get_course_statistics(self) -> CourseStats:
        """
        Get course statistics.
        
        Returns:
            Course statistics
        """
        try:
            # Get statistics from repository
            stats = await self.course_repository.get_course_statistics()
            
            # Get enrollment statistics
            enrollment_stats = await self.enrollment_repository.get_enrollment_statistics()
            
            # Combine statistics
            return CourseStats(
                total_courses=stats.get('total_courses', 0),
                published_courses=stats.get('published_courses', 0),
                draft_courses=stats.get('draft_courses', 0),
                archived_courses=stats.get('archived_courses', 0),
                total_enrollments=enrollment_stats.get('total_enrollments', 0),
                courses_by_difficulty=stats.get('courses_by_difficulty', {}),
                courses_by_category=stats.get('courses_by_category', {})
            )
            
        except Exception as e:
            self.logger.error(f"Error getting course statistics: {e}")
            raise
    
    async def count_courses(self, instructor_id: str = None) -> int:
        """
        Count courses.
        
        Args:
            instructor_id: Optional instructor ID filter
            
        Returns:
            Number of courses
        """
        try:
            return await self.course_repository.count_courses(instructor_id)
            
        except Exception as e:
            self.logger.error(f"Error counting courses: {e}")
            raise
    
    async def validate_course_access(self, course_id: str, user_id: str) -> bool:
        """
        Validate if user has access to course.
        
        Args:
            course_id: Course ID
            user_id: User ID
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            course = await self.course_repository.get_course_by_id(course_id)
            if not course:
                return False
            
            # Check if user is the instructor
            if course.instructor_id == user_id:
                return True
            
            # Check if user is enrolled (for students)
            enrollment = await self.enrollment_repository.get_enrollment_by_student_and_course(
                user_id, course_id
            )
            
            return enrollment is not None
            
        except Exception as e:
            self.logger.error(f"Error validating course access: {e}")
            return False
    
    async def _get_course_enrollment_stats(self, course_id: str) -> Dict[str, Any]:
        """
        Get enrollment statistics for a course.
        
        Args:
            course_id: Course ID
            
        Returns:
            Dictionary with enrollment statistics
        """
        try:
            total_enrollments = await self.enrollment_repository.count_enrollments(
                course_id=course_id
            )
            
            active_enrollments = await self.enrollment_repository.count_enrollments(
                course_id=course_id, status='active'
            )
            
            completed_enrollments = await self.enrollment_repository.count_enrollments(
                course_id=course_id, status='completed'
            )
            
            completion_rate = (
                (completed_enrollments / total_enrollments * 100) 
                if total_enrollments > 0 else 0.0
            )
            
            return {
                'total_enrollments': total_enrollments,
                'active_enrollments': active_enrollments,
                'completed_enrollments': completed_enrollments,
                'completion_rate': completion_rate
            }
            
        except Exception as e:
            self.logger.error(f"Error getting course enrollment stats: {e}")
            return {
                'total_enrollments': 0,
                'active_enrollments': 0,
                'completed_enrollments': 0,
                'completion_rate': 0.0
            }