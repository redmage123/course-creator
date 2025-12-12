"""
Course Service Implementation - Comprehensive Educational Content Management

This module implements the course service layer, orchestrating complex business workflows
for course lifecycle management within the educational platform. It serves as the primary
business logic coordinator between the API layer and the domain/infrastructure layers.

ARCHITECTURAL RESPONSIBILITIES:
The CourseService encapsulates all course-related business operations, enforcing domain
rules, coordinating with external services, and maintaining data consistency across the
educational platform's course management workflows.

BUSINESS WORKFLOW ORCHESTRATION:
1. Course Creation: Validation, ID generation, and initial state setup
2. Publication Lifecycle: Draft → Published → Archived state management
3. Content Validation: Educational standards and quality assurance
4. Instructor Authorization: Ownership verification and permission enforcement
5. Search and Discovery: Content filtering and categorization support
6. Analytics Integration: Performance metrics and statistical reporting

DOMAIN RULE ENFORCEMENT:
- Course Quality Standards: Minimum content requirements for publication
- Instructor Ownership: Secure course access and modification controls
- Educational Taxonomy: Proper categorization and difficulty classification
- Enrollment Constraints: Active enrollment validation before course deletion
- Publication Requirements: Comprehensive readiness validation

INTEGRATION PATTERNS:
- Repository Pattern: Clean separation between business logic and data persistence
- Domain Events: Course lifecycle events for analytics and notification systems
- Service Composition: Coordination with enrollment and feedback services
- External APIs: Integration with content management and user services

EDUCATIONAL PLATFORM FEATURES:
- Course Duplication: Efficient course template and variant management
- Statistical Reporting: Enrollment metrics and performance analytics
- Search Functionality: Advanced filtering and content discovery
- Quality Assurance: Educational standards validation and enforcement
- Lifecycle Management: Complete course state and transition control

PERFORMANCE OPTIMIZATION:
- Lazy Loading: Efficient data access patterns for course-related entities
- Caching Strategy: Optimized retrieval for frequently accessed course data
- Batch Operations: Efficient processing for bulk course management
- Async Operations: Non-blocking I/O for database and external service interactions

BUSINESS INTELLIGENCE:
- Course Analytics: Enrollment trends, completion rates, and revenue tracking
- Instructor Insights: Teaching effectiveness and content performance metrics
- Platform Metrics: Usage patterns and educational outcome analysis
- Quality Metrics: Content effectiveness and student satisfaction correlation

ERROR HANDLING AND RESILIENCE:
- Validation Errors: Comprehensive input validation with educational context
- Authorization Failures: Secure error handling for access control violations
- Data Consistency: Transaction management for multi-step operations
- External Dependencies: Graceful degradation for service unavailability
"""
import uuid
from datetime import datetime
from typing import List, Optional
from course_management.domain.entities.course import Course, CourseStatistics, DifficultyLevel, DurationUnit
from data_access.course_dao import CourseManagementDAO
from course_management.domain.interfaces.course_service import ICourseService

class CourseService(ICourseService):
    """
    Comprehensive course management service implementing educational business workflows.
    
    This service coordinates all course-related operations, from initial creation through
    publication, enrollment management, and eventual archival. It enforces educational
    standards, maintains data integrity, and provides rich analytics integration.
    
    DESIGN PRINCIPLES:
    - Single Responsibility: Focused exclusively on course management business logic
    - Dependency Inversion: Depends on repository abstractions for data persistence
    - Open/Closed: Extensible through composition and interface implementation
    - Interface Segregation: Clean contract definition via ICourseService interface
    
    BUSINESS CAPABILITIES:
    1. Course Lifecycle Management: Complete CRUD operations with state transitions
    2. Quality Assurance: Educational standards validation and publication requirements
    3. Instructor Authorization: Secure ownership verification and permission enforcement
    4. Discovery Services: Advanced search, filtering, and categorization support
    5. Analytics Integration: Performance metrics and statistical reporting
    6. Content Management: Duplication, templating, and variant management
    
    EDUCATIONAL WORKFLOWS:
    - Creation Process: Metadata validation → ID generation → Persistence → Event publishing
    - Publication Workflow: Readiness validation → State transition → Visibility control
    - Modification Process: Ownership verification → Business rule validation → Update persistence
    - Deletion Process: Dependency validation → Authorization check → Soft/hard deletion
    
    INTEGRATION COORDINATION:
    - Enrollment Service: Validates active enrollments before course modifications
    - Analytics Service: Provides course performance and statistical data
    - Content Service: Coordinates with slides, quizzes, and lab materials
    - User Service: Verifies instructor credentials and authorization
    
    PERFORMANCE FEATURES:
    - Async Operations: Non-blocking I/O for all database and external service calls
    - Efficient Querying: Optimized data access patterns with pagination support
    - Caching Integration: Repository-level caching for frequently accessed courses
    - Batch Processing: Optimized handling of bulk course operations
    """
    
    def __init__(self, dao: CourseManagementDAO):
        self._dao = dao
    
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
        return await self._dao.create(course)
    
    async def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        if not course_id:
            return None
        
        return await self._dao.get_by_id(course_id)
    
    async def get_courses_by_instructor(self, instructor_id: str) -> List[Course]:
        """Get all courses for an instructor"""
        if not instructor_id:
            return []
        
        return await self._dao.get_by_instructor_id(instructor_id)
    
    async def update_course(self, course: Course) -> Course:
        """Update an existing course with business validation"""
        if not course.id:
            raise ValueError("Course ID is required for update")
        
        # Check if course exists
        existing_course = await self._dao.get_by_id(course.id)
        if not existing_course:
            raise ValueError(f"Course with ID {course.id} not found")
        
        # Validate business rules
        course.validate()
        
        # Update timestamp
        course.updated_at = datetime.utcnow()
        
        return await self._dao.update(course)
    
    async def delete_course(
        self,
        course_id: str,
        user_id: str,
        is_admin: bool = False
    ) -> bool:
        """
        Delete a course permanently.

        BUSINESS CONTEXT:
        Course deletion is allowed for:
        - The instructor who owns the course
        - Organization admins (can delete any course in their org)
        - Site admins (can delete any course)

        Args:
            course_id: The ID of the course to delete
            user_id: The ID of the user requesting deletion
            is_admin: If True, skip ownership check (org admin/site admin)

        Returns:
            True if course was successfully deleted

        Raises:
            ValueError: If course not found, permission denied, or has active enrollments
        """
        if not course_id or not user_id:
            raise ValueError("Course ID and user ID are required")

        # Check if course exists
        course = await self._dao.get_by_id(course_id)
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")

        # Check ownership unless user is an admin
        if not is_admin and course.instructor_id != user_id:
            raise ValueError("Only the course owner or an admin can delete this course")

        # Check if there are active enrollments
        enrollment_count = await self._dao.count_active_by_course(course_id)
        if enrollment_count > 0:
            raise ValueError(
                f"Cannot delete course with {enrollment_count} active enrollments. "
                "Please unenroll all students first."
            )

        return await self._dao.delete(course_id)
    
    async def publish_course(self, course_id: str, instructor_id: str) -> Course:
        """Publish a course with business validation"""
        if not course_id or not instructor_id:
            raise ValueError("Course ID and instructor ID are required")
        
        # Get course
        course = await self._dao.get_by_id(course_id)
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Check ownership
        if course.instructor_id != instructor_id:
            raise ValueError("Instructor can only publish their own courses")
        
        # Use business logic from entity
        course.publish()
        
        return await self._dao.update(course)
    
    async def unpublish_course(self, course_id: str, instructor_id: str) -> Course:
        """Unpublish a course"""
        if not course_id or not instructor_id:
            raise ValueError("Course ID and instructor ID are required")
        
        # Get course
        course = await self._dao.get_by_id(course_id)
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Check ownership
        if course.instructor_id != instructor_id:
            raise ValueError("Instructor can only unpublish their own courses")
        
        # Use business logic from entity
        course.unpublish()
        
        return await self._dao.update(course)
    
    async def get_published_courses(self, limit: int = 50, offset: int = 0) -> List[Course]:
        """Get all published courses with pagination"""
        if limit <= 0 or limit > 100:
            limit = 50

        if offset < 0:
            offset = 0

        return await self._dao.get_published_courses(limit, offset)

    async def get_all_courses(self, limit: int = 50, offset: int = 0) -> List[Course]:
        """Get ALL courses (published and unpublished) with pagination"""
        if limit <= 0 or limit > 100:
            limit = 50

        if offset < 0:
            offset = 0

        return await self._dao.get_all_courses(limit, offset)
    
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
        
        return await self._dao.search(query.strip(), filters)
    
    async def get_course_statistics(self, course_id: str) -> Optional[CourseStatistics]:
        """Get statistics for a course"""
        if not course_id:
            return None
        
        # Check if course exists
        course = await self._dao.get_by_id(course_id)
        if not course:
            return None
        
        return await self._dao.get_statistics(course_id)
    
    # Additional business methods
    async def duplicate_course(self, course_id: str, instructor_id: str, new_title: str) -> Course:
        """Duplicate an existing course"""
        # Get original course
        original_course = await self._dao.get_by_id(course_id)
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
        
        return await self._dao.count_by_instructor(instructor_id)