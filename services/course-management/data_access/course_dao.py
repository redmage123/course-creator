"""
Course Management Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for course management operations,
centralizing all SQL queries and database interactions in a single, maintainable location.

Business Context:
The Course Management service handles course creation, publishing, student enrollment,
and progress tracking. By centralizing all SQL operations in this DAO, we achieve:
- Single source of truth for all database queries
- Easier maintenance and testing of SQL operations
- Clear separation between business logic and data access
- Improved code organization and architectural consistency

Technical Rationale:
- Follows the Single Responsibility Principle by isolating data access concerns
- Enables easier unit testing through clear interface boundaries
- Provides consistent error handling for all database operations
- Allows for future database optimization without affecting business logic
- Supports database migration and schema evolution
"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import sys
sys.path.append('/app/shared')
from exceptions import (
    CourseCreatorBaseException,
    DatabaseException,
    ContentNotFoundException,
    ValidationException
)


class CourseManagementDAO:
    """
    Data Access Object for Course Management Operations
    
    This class centralizes all SQL queries and database operations for the course
    management service, following the DAO pattern for clean architecture.
    
    Business Context:
    Provides data access methods for course lifecycle management including:
    - Course creation and metadata management
    - Course instance creation and scheduling
    - Student enrollment and progress tracking
    - Quiz publication and assessment management
    - Content delivery and access control
    
    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex operations
    - Includes comprehensive error handling and logging
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the Course Management DAO with database connection pool.
        
        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
    
    # ================================================================
    # COURSE MANAGEMENT QUERIES
    # ================================================================
    
    async def get_course_by_id_and_instructor(self, course_id: str, instructor_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve course information for a specific instructor.
        
        Business Context:
        Instructors can only access courses they own. This query enforces
        ownership validation for security and access control.
        
        Args:
            course_id: Unique course identifier
            instructor_id: Instructor's user ID for ownership validation
            
        Returns:
            Course record or None if not found or not owned by instructor
        """
        try:
            async with self.db_pool.acquire() as conn:
                course = await conn.fetchrow(
                    "SELECT * FROM courses WHERE id = $1 AND instructor_id = $2",
                    course_id, instructor_id
                )
                return dict(course) if course else None
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve course {course_id} for instructor {instructor_id}",
                error_code="COURSE_QUERY_ERROR",
                details={"course_id": course_id, "instructor_id": instructor_id},
                original_exception=e
            )
    
    async def count_active_instances(self, course_id: str) -> int:
        """
        Count active course instances for a given course.
        
        Business Context:
        Course instances represent scheduled offerings of a course. This count
        helps instructors understand course deployment and resource allocation.
        
        Args:
            course_id: Course identifier to count instances for
            
        Returns:
            Number of active course instances
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM course_instances WHERE course_id = $1 AND status = 'active'",
                    course_id
                )
                return result or 0
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to count active instances for course {course_id}",
                error_code="INSTANCE_COUNT_ERROR",
                details={"course_id": course_id},
                original_exception=e
            )
    
    async def get_instructor_course_stats(self, instructor_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for an instructor's courses.
        
        Business Context:
        Provides dashboard metrics for instructors including course counts,
        enrollment statistics, and activity summaries for informed decision making.
        
        Args:
            instructor_id: Instructor's user ID
            
        Returns:
            Dictionary containing course statistics and metrics
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get total course count
                total_courses = await conn.fetchval(
                    "SELECT COUNT(DISTINCT c.id) FROM courses c WHERE c.instructor_id = $1",
                    instructor_id
                )
                
                # Get courses with detailed information
                courses = await conn.fetch(
                    """SELECT * FROM courses 
                       WHERE instructor_id = $1 
                       ORDER BY created_at DESC""",
                    instructor_id
                )
                
                return {
                    "total_courses": total_courses or 0,
                    "courses": [dict(course) for course in courses]
                }
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve course statistics for instructor {instructor_id}",
                error_code="STATS_QUERY_ERROR",
                details={"instructor_id": instructor_id},
                original_exception=e
            )
    
    # ================================================================
    # COURSE INSTANCE MANAGEMENT QUERIES
    # ================================================================
    
    async def create_course_instance(self, course_instance_data: Dict[str, Any]) -> str:
        """
        Create a new course instance with provided data.
        
        Business Context:
        Course instances represent scheduled offerings of courses with specific
        start/end dates, enrollment limits, and access configurations.
        
        Args:
            course_instance_data: Dictionary containing instance information
            
        Returns:
            Created course instance ID
        """
        try:
            async with self.db_pool.acquire() as conn:
                instance_id = await conn.fetchval(
                    """INSERT INTO course_instances (
                        course_id, name, start_datetime, end_datetime, 
                        max_students, status, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7) 
                    RETURNING id""",
                    course_instance_data['course_id'],
                    course_instance_data['name'],
                    course_instance_data['start_datetime'],
                    course_instance_data['end_datetime'],
                    course_instance_data['max_students'],
                    course_instance_data.get('status', 'active'),
                    datetime.utcnow()
                )
                return str(instance_id)
        except Exception as e:
            raise DatabaseException(
                message="Failed to create course instance",
                error_code="INSTANCE_CREATION_ERROR",
                details=course_instance_data,
                original_exception=e
            )
    
    async def count_course_instances(self, filters: Dict[str, Any]) -> int:
        """
        Count course instances with flexible filtering.
        
        Business Context:
        Supports various administrative queries for course instance management
        including filtering by status, date ranges, and instructor ownership.
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            Count of matching course instances
        """
        try:
            # Build WHERE clause dynamically based on filters
            where_conditions = []
            params = []
            param_num = 1
            
            if 'instructor_id' in filters:
                where_conditions.append(f"c.instructor_id = ${param_num}")
                params.append(filters['instructor_id'])
                param_num += 1
                
            if 'status' in filters:
                where_conditions.append(f"ci.status = ${param_num}")
                params.append(filters['status'])
                param_num += 1
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    f"""SELECT COUNT(*) FROM course_instances ci 
                        JOIN courses c ON ci.course_id = c.id 
                        WHERE {where_clause}""",
                    *params
                )
                return result or 0
        except Exception as e:
            raise DatabaseException(
                message="Failed to count course instances",
                error_code="INSTANCE_COUNT_ERROR",
                details={"filters": filters},
                original_exception=e
            )
    
    # ================================================================
    # STUDENT ENROLLMENT QUERIES
    # ================================================================
    
    async def get_enrolled_student_ids(self, course_instance_id: str) -> List[str]:
        """
        Retrieve list of student IDs enrolled in a course instance.
        
        Business Context:
        Student enrollment tracking is essential for course management,
        communication, and resource allocation planning.
        
        Args:
            course_instance_id: Course instance to get enrollments for
            
        Returns:
            List of enrolled student user IDs
        """
        try:
            async with self.db_pool.acquire() as conn:
                students = await conn.fetch(
                    "SELECT id FROM student_course_enrollments WHERE course_instance_id = $1",
                    course_instance_id
                )
                return [str(student['id']) for student in students]
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve enrolled students for instance {course_instance_id}",
                error_code="ENROLLMENT_QUERY_ERROR",
                details={"course_instance_id": course_instance_id},
                original_exception=e
            )
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user information by email address.
        
        Business Context:
        Email-based user lookup is common for enrollment operations
        where instructors add students by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User record or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT id FROM course_creator.users WHERE email = $1",
                    email
                )
                return dict(user) if user else None
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve user by email {email}",
                error_code="USER_LOOKUP_ERROR",
                details={"email": email},
                original_exception=e
            )
    
    async def create_student_enrollment(self, enrollment_data: Dict[str, Any]) -> str:
        """
        Create a new student course enrollment.
        
        Business Context:
        Enrollments link students to course instances with access tokens
        and tracking information for personalized learning experiences.
        
        Args:
            enrollment_data: Dictionary containing enrollment information
            
        Returns:
            Created enrollment ID
        """
        try:
            async with self.db_pool.acquire() as conn:
                enrollment_id = await conn.fetchval(
                    """INSERT INTO student_course_enrollments (
                        course_instance_id, student_id, student_first_name, 
                        student_last_name, student_email, access_token,
                        temporary_password, enrolled_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
                    RETURNING id""",
                    enrollment_data['course_instance_id'],
                    enrollment_data['student_id'],
                    enrollment_data['student_first_name'],
                    enrollment_data['student_last_name'],
                    enrollment_data['student_email'],
                    enrollment_data['access_token'],
                    enrollment_data['temporary_password'],
                    datetime.utcnow()
                )
                return str(enrollment_id)
        except Exception as e:
            raise DatabaseException(
                message="Failed to create student enrollment",
                error_code="ENROLLMENT_CREATION_ERROR",
                details=enrollment_data,
                original_exception=e
            )
    
    # ================================================================
    # QUIZ MANAGEMENT QUERIES
    # ================================================================
    
    async def upsert_quiz_publication(self, quiz_data: Dict[str, Any]) -> None:
        """
        Insert or update quiz publication information.
        
        Business Context:
        Quiz publications link course instances with generated quizzes,
        enabling assessment delivery and student progress tracking.
        
        Args:
            quiz_data: Dictionary containing quiz publication information
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO quiz_publications (
                        course_instance_id, quiz_id, quiz_data, published_at
                    ) VALUES ($1, $2, $3, $4)
                    ON CONFLICT (course_instance_id) 
                    DO UPDATE SET
                        quiz_id = EXCLUDED.quiz_id,
                        quiz_data = EXCLUDED.quiz_data,
                        published_at = EXCLUDED.published_at""",
                    quiz_data['course_instance_id'],
                    quiz_data['quiz_id'],
                    quiz_data['quiz_data'],
                    datetime.utcnow()
                )
        except Exception as e:
            raise DatabaseException(
                message="Failed to create/update quiz publication",
                error_code="QUIZ_PUBLICATION_ERROR",
                details=quiz_data,
                original_exception=e
            )
    
    # ================================================================
    # CLEANUP AND MAINTENANCE QUERIES
    # ================================================================
    
    async def count_student_enrollments(self, course_instance_id: str) -> int:
        """
        Count total student enrollments for a course instance.
        
        Business Context:
        Enrollment counts are used for cleanup verification and
        administrative reporting on course completion and resource usage.
        
        Args:
            course_instance_id: Course instance to count enrollments for
            
        Returns:
            Total number of student enrollments
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM student_course_enrollments WHERE course_instance_id = $1",
                    course_instance_id
                )
                return result or 0
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to count enrollments for instance {course_instance_id}",
                error_code="ENROLLMENT_COUNT_ERROR",
                details={"course_instance_id": course_instance_id},
                original_exception=e
            )
    
    async def delete_quiz_attempts(self, course_instance_id: str) -> int:
        """
        Delete all quiz attempts for a course instance.
        
        Business Context:
        Part of course cleanup process to remove student data when
        courses are completed or decommissioned.
        
        Args:
            course_instance_id: Course instance to clean up
            
        Returns:
            Number of quiz attempts deleted
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM quiz_attempts WHERE course_instance_id = $1",
                    course_instance_id
                )
                # Extract number of affected rows from result
                return int(result.split()[-1]) if result else 0
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to delete quiz attempts for instance {course_instance_id}",
                error_code="QUIZ_CLEANUP_ERROR",
                details={"course_instance_id": course_instance_id},
                original_exception=e
            )
    
    async def delete_student_enrollments(self, course_instance_id: str) -> int:
        """
        Delete all student enrollments for a course instance.
        
        Business Context:
        Final step in course cleanup process to remove all enrollment
        records and associated student access tokens.
        
        Args:
            course_instance_id: Course instance to clean up
            
        Returns:
            Number of enrollments deleted
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM student_course_enrollments WHERE course_instance_id = $1",
                    course_instance_id
                )
                # Extract number of affected rows from result
                return int(result.split()[-1]) if result else 0
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to delete enrollments for instance {course_instance_id}",
                error_code="ENROLLMENT_CLEANUP_ERROR",
                details={"course_instance_id": course_instance_id},
                original_exception=e
            )
    
    # ================================================================
    # COMPLEX QUERY OPERATIONS
    # ================================================================
    
    async def get_student_course_data(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve comprehensive course data for a student using access token.
        
        Business Context:
        Students access courses using unique access tokens. This query provides
        all necessary course information including content, progress, and assessments.
        
        Args:
            access_token: Student's unique course access token
            
        Returns:
            Complete course data structure or None if token invalid
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Complex join query to get all course-related data
                enrollment = await conn.fetchrow(
                    """SELECT 
                        sce.id, sce.student_first_name, sce.student_last_name, 
                        sce.student_email, sce.progress_percentage, sce.enrolled_at, 
                        sce.last_login_at, sce.course_instance_id,
                        c.id as course_id, c.title as course_title, 
                        c.description as course_description, c.syllabus, c.objectives,
                        ci.name as instance_name, ci.start_datetime, ci.end_datetime
                    FROM student_course_enrollments sce
                    JOIN course_instances ci ON sce.course_instance_id = ci.id
                    JOIN courses c ON ci.course_id = c.id
                    WHERE sce.access_token = $1""",
                    access_token
                )
                
                if not enrollment:
                    return None
                
                # Get associated slides and quizzes
                slides = await conn.fetch(
                    "SELECT * FROM course_slides WHERE course_id = $1 ORDER BY slide_number",
                    enrollment['course_id']
                )
                
                quizzes = await conn.fetch(
                    "SELECT * FROM course_quizzes WHERE course_id = $1 ORDER BY created_at",
                    enrollment['course_id']
                )
                
                return {
                    'enrollment': dict(enrollment),
                    'slides': [dict(slide) for slide in slides],
                    'quizzes': [dict(quiz) for quiz in quizzes]
                }
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve course data for token",
                error_code="COURSE_DATA_ERROR",
                details={"has_token": bool(access_token)},  # Don't log actual token for security
                original_exception=e
            )
    
    # ================================================================
    # TRANSACTION SUPPORT METHODS
    # ================================================================
    
    async def execute_in_transaction(self, operations: List[tuple]) -> List[Any]:
        """
        Execute multiple database operations within a single transaction.
        
        Business Context:
        Some course operations require multiple database changes that must
        succeed or fail together to maintain data consistency.
        
        Args:
            operations: List of (query, params) tuples to execute
            
        Returns:
            List of operation results
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    results = []
                    for query, params in operations:
                        if params:
                            result = await conn.execute(query, *params)
                        else:
                            result = await conn.execute(query)
                        results.append(result)
                    return results
        except Exception as e:
            raise DatabaseException(
                message="Failed to execute transaction operations",
                error_code="TRANSACTION_ERROR",
                details={"operation_count": len(operations)},
                original_exception=e
            )