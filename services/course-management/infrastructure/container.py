"""
Dependency Injection Container
Single Responsibility: Wire up dependencies and manage service lifetimes
Dependency Inversion: Configure concrete implementations for abstract interfaces
"""
import asyncpg
from typing import Optional
from omegaconf import DictConfig

# Domain interfaces
from ..domain.interfaces.course_service import ICourseService
from ..domain.interfaces.enrollment_service import IEnrollmentService
from ..domain.interfaces.feedback_service import IFeedbackService
from ..domain.interfaces.course_repository import ICourseRepository
from ..domain.interfaces.enrollment_repository import IEnrollmentRepository
from ..domain.interfaces.feedback_repository import (
    ICourseFeedbackRepository, IStudentFeedbackRepository, IFeedbackResponseRepository
)

# Application services
from ..application.services.course_service import CourseService
from ..application.services.enrollment_service import EnrollmentService
from ..application.services.feedback_service import FeedbackService

# Infrastructure implementations
from .repositories.postgresql_course_repository import PostgreSQLCourseRepository
# Note: These would need to be implemented following the same pattern
# from .repositories.postgresql_enrollment_repository import PostgreSQLEnrollmentRepository
# from .repositories.postgresql_feedback_repository import (
#     PostgreSQLCourseFeedbackRepository, PostgreSQLStudentFeedbackRepository, 
#     PostgreSQLFeedbackResponseRepository
# )

class Container:
    """
    Dependency injection container following SOLID principles
    """
    
    def __init__(self, config: DictConfig):
        self._config = config
        self._connection_pool: Optional[asyncpg.Pool] = None
        
        # Service instances (singletons)
        self._course_repository: Optional[ICourseRepository] = None
        self._enrollment_repository: Optional[IEnrollmentRepository] = None
        self._course_feedback_repository: Optional[ICourseFeedbackRepository] = None
        self._student_feedback_repository: Optional[IStudentFeedbackRepository] = None
        self._feedback_response_repository: Optional[IFeedbackResponseRepository] = None
        
        self._course_service: Optional[ICourseService] = None
        self._enrollment_service: Optional[IEnrollmentService] = None
        self._feedback_service: Optional[IFeedbackService] = None
    
    async def initialize(self) -> None:
        """Initialize the container and create database connections"""
        # Create database connection pool
        self._connection_pool = await asyncpg.create_pool(
            self._config.database.url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._connection_pool:
            await self._connection_pool.close()
    
    # Repository factories (following Dependency Inversion)
    def get_course_repository(self) -> ICourseRepository:
        """Get course repository instance"""
        if not self._course_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            self._course_repository = PostgreSQLCourseRepository(self._connection_pool)
        
        return self._course_repository
    
    def get_enrollment_repository(self) -> IEnrollmentRepository:
        """Get enrollment repository instance"""
        if not self._enrollment_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            # For now, return a mock implementation
            # In a complete implementation, this would be:
            # self._enrollment_repository = PostgreSQLEnrollmentRepository(self._connection_pool)
            self._enrollment_repository = MockEnrollmentRepository()
        
        return self._enrollment_repository
    
    def get_course_feedback_repository(self) -> ICourseFeedbackRepository:
        """Get course feedback repository instance"""
        if not self._course_feedback_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            # For now, return a mock implementation
            self._course_feedback_repository = MockCourseFeedbackRepository()
        
        return self._course_feedback_repository
    
    def get_student_feedback_repository(self) -> IStudentFeedbackRepository:
        """Get student feedback repository instance"""
        if not self._student_feedback_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            # For now, return a mock implementation
            self._student_feedback_repository = MockStudentFeedbackRepository()
        
        return self._student_feedback_repository
    
    def get_feedback_response_repository(self) -> IFeedbackResponseRepository:
        """Get feedback response repository instance"""
        if not self._feedback_response_repository:
            if not self._connection_pool:
                raise RuntimeError("Container not initialized - call initialize() first")
            
            # For now, return a mock implementation
            self._feedback_response_repository = MockFeedbackResponseRepository()
        
        return self._feedback_response_repository
    
    # Service factories (following Dependency Inversion)
    def get_course_service(self) -> ICourseService:
        """Get course service instance"""
        if not self._course_service:
            self._course_service = CourseService(
                course_repository=self.get_course_repository(),
                enrollment_repository=self.get_enrollment_repository()
            )
        
        return self._course_service
    
    def get_enrollment_service(self) -> IEnrollmentService:
        """Get enrollment service instance"""
        if not self._enrollment_service:
            self._enrollment_service = EnrollmentService(
                enrollment_repository=self.get_enrollment_repository(),
                course_repository=self.get_course_repository()
            )
        
        return self._enrollment_service
    
    def get_feedback_service(self) -> IFeedbackService:
        """Get feedback service instance"""
        if not self._feedback_service:
            self._feedback_service = FeedbackService(
                course_feedback_repository=self.get_course_feedback_repository(),
                student_feedback_repository=self.get_student_feedback_repository(),
                feedback_response_repository=self.get_feedback_response_repository(),
                course_repository=self.get_course_repository(),
                enrollment_repository=self.get_enrollment_repository()
            )
        
        return self._feedback_service


# Mock implementations for demonstration (would be replaced with real PostgreSQL implementations)
class MockEnrollmentRepository(IEnrollmentRepository):
    """Mock enrollment repository for demonstration"""
    
    async def create(self, enrollment):
        return enrollment
    
    async def get_by_id(self, enrollment_id):
        return None
    
    async def get_by_student_and_course(self, student_id, course_id):
        return None
    
    async def get_by_student_id(self, student_id):
        return []
    
    async def get_by_course_id(self, course_id):
        return []
    
    async def get_by_instructor_id(self, instructor_id):
        return []
    
    async def get_by_status(self, status):
        return []
    
    async def update(self, enrollment):
        return enrollment
    
    async def delete(self, enrollment_id):
        return True
    
    async def exists(self, student_id, course_id):
        return False
    
    async def count_by_course(self, course_id):
        return 0
    
    async def count_active_by_course(self, course_id):
        return 0
    
    async def count_completed_by_course(self, course_id):
        return 0
    
    async def get_completion_rate(self, course_id):
        return 0.0
    
    async def get_enrollments_by_date_range(self, start_date, end_date):
        return []
    
    async def get_recent_enrollments(self, limit=10):
        return []
    
    async def bulk_create(self, enrollments):
        return enrollments


class MockCourseFeedbackRepository(ICourseFeedbackRepository):
    """Mock course feedback repository for demonstration"""
    
    async def create(self, feedback):
        return feedback
    
    async def get_by_id(self, feedback_id):
        return None
    
    async def get_by_course_id(self, course_id, include_anonymous=True):
        return []
    
    async def get_by_student_and_course(self, student_id, course_id):
        return None
    
    async def get_by_instructor_id(self, instructor_id):
        return []
    
    async def update(self, feedback):
        return feedback
    
    async def delete(self, feedback_id):
        return True
    
    async def get_average_rating(self, course_id):
        return None
    
    async def get_rating_distribution(self, course_id):
        return {}
    
    async def count_by_course(self, course_id):
        return 0
    
    async def get_by_status(self, status):
        return []


class MockStudentFeedbackRepository(IStudentFeedbackRepository):
    """Mock student feedback repository for demonstration"""
    
    async def create(self, feedback):
        return feedback
    
    async def get_by_id(self, feedback_id):
        return None
    
    async def get_by_student_id(self, student_id, course_id=None):
        return []
    
    async def get_by_instructor_id(self, instructor_id, course_id=None):
        return []
    
    async def get_by_course_id(self, course_id):
        return []
    
    async def update(self, feedback):
        return feedback
    
    async def delete(self, feedback_id):
        return True
    
    async def get_shared_feedback(self, student_id):
        return []
    
    async def count_by_student(self, student_id):
        return 0
    
    async def get_intervention_needed(self, instructor_id):
        return []


class MockFeedbackResponseRepository(IFeedbackResponseRepository):
    """Mock feedback response repository for demonstration"""
    
    async def create(self, response):
        return response
    
    async def get_by_id(self, response_id):
        return None
    
    async def get_by_feedback_id(self, course_feedback_id):
        return []
    
    async def get_by_instructor_id(self, instructor_id):
        return []
    
    async def update(self, response):
        return response
    
    async def delete(self, response_id):
        return True
    
    async def get_public_responses(self, course_id):
        return []