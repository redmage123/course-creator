"""
Course Management Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for course management operations,
centralizing all SQL queries and database interactions in a single, maintainable locations.

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
from course_management.domain.entities.course import Course, DifficultyLevel, DurationUnit


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

    async def create(self, course: Course) -> Course:
        """Create a new course"""
        try:
            import json
            # Prepare metadata JSONB column with tags only (organizational fields now in dedicated columns)
            metadata = {
                'tags': course.tags or []
            }

            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO course_creator.courses (
                        id, title, description, instructor_id, category,
                        difficulty_level, estimated_duration, duration_unit,
                        price, is_published, created_at, updated_at, metadata,
                        organization_id, track_id, location_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)""",
                    course.id, course.title, course.description, course.instructor_id,
                    course.category, course.difficulty_level.value, course.estimated_duration,
                    course.duration_unit.value if course.duration_unit else None,
                    course.price, course.is_published, course.created_at, course.updated_at,
                    json.dumps(metadata),
                    getattr(course, 'organization_id', None),
                    getattr(course, 'track_id', None),
                    getattr(course, 'location_id', None)
                )
                return course
        except Exception as e:
            raise DatabaseException(
                message="Failed to create course",
                operation="create",
                table_name="courses",
                original_exception=e
            )

    async def get_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM course_creator.courses WHERE id = $1",
                    course_id
                )
                if not row:
                    return None
                return self._row_to_course(row)
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve course {course_id}",
                operation="get_by_id",
                table_name="courses",
                record_id=course_id,
                original_exception=e
            )

    async def get_by_instructor_id(self, instructor_id: str) -> List[Course]:
        """Get all courses for an instructor"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM course_creator.courses WHERE instructor_id = $1 ORDER BY created_at DESC",
                    instructor_id
                )
                return [self._row_to_course(row) for row in rows]
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve courses for instructor {instructor_id}",
                operation="get_by_instructor_id",
                table_name="courses",
                original_exception=e
            )

    async def update(self, course: Course) -> Course:
        """Update an existing course"""
        try:
            import json
            # Prepare metadata JSONB column with tags only (organizational fields now in dedicated columns)
            metadata = {
                'tags': course.tags or []
            }

            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """UPDATE course_creator.courses SET
                        title = $2, description = $3, category = $4,
                        difficulty_level = $5, estimated_duration = $6, duration_unit = $7,
                        price = $8, is_published = $9, updated_at = $10, metadata = $11,
                        organization_id = $12, project_id = $13, track_id = $14, location_id = $15
                    WHERE id = $1""",
                    course.id, course.title, course.description, course.category,
                    course.difficulty_level.value, course.estimated_duration,
                    course.duration_unit.value if course.duration_unit else None,
                    course.price, course.is_published, course.updated_at,
                    json.dumps(metadata),
                    getattr(course, 'organization_id', None),
                    getattr(course, 'project_id', None),
                    getattr(course, 'track_id', None),
                    getattr(course, 'location_id', None)
                )
                return course
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to update course {course.id}",
                operation="update",
                table_name="courses",
                record_id=course.id,
                original_exception=e
            )

    async def delete(self, course_id: str) -> bool:
        """Delete a course"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM course_creator.courses WHERE id = $1",
                    course_id
                )
                return int(result.split()[-1]) > 0 if result else False
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to delete course {course_id}",
                operation="delete",
                table_name="courses",
                record_id=course_id,
                original_exception=e
            )

    async def count_active_by_course(self, course_id: str) -> int:
        """Count active enrollments for a course"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    """SELECT COUNT(*) FROM student_course_enrollments sce
                       JOIN course_instances ci ON sce.course_instance_id = ci.id
                       WHERE ci.course_id = $1 AND ci.status = 'active'""",
                    course_id
                )
                return result or 0
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to count active enrollments for course {course_id}",
                operation="count_active_by_course",
                table_name="courses",
                record_id=course_id,
                original_exception=e
            )

    async def count_by_instructor(self, instructor_id: str) -> int:
        """Count courses by instructor"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM course_creator.courses WHERE instructor_id = $1",
                    instructor_id
                )
                return result or 0
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to count courses for instructor {instructor_id}",
                operation="count_by_instructor",
                table_name="courses",
                original_exception=e
            )

    async def search(self, query: str, filters: Dict[str, Any]) -> List[Course]:
        """Search courses by query and filters"""
        try:
            where_conditions = ["is_published = true"]
            params = []
            param_num = 1

            if query:
                where_conditions.append(f"(title ILIKE ${param_num} OR description ILIKE ${param_num})")
                params.append(f"%{query}%")
                param_num += 1

            if filters.get('category'):
                where_conditions.append(f"category = ${param_num}")
                params.append(filters['category'])
                param_num += 1

            if filters.get('difficulty_level'):
                where_conditions.append(f"difficulty_level = ${param_num}")
                params.append(filters['difficulty_level'])
                param_num += 1

            where_clause = " AND ".join(where_conditions)

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""SELECT * FROM course_creator.courses WHERE {where_clause}
                        ORDER BY created_at DESC LIMIT 100""",
                    *params
                )
                return [self._row_to_course(row) for row in rows]
        except Exception as e:
            raise DatabaseException(
                message="Failed to search courses",
                operation="search",
                table_name="courses",
                original_exception=e
            )

    async def get_statistics(self, course_id: str):
        """Get course statistics (placeholder)"""
        return None

    def _row_to_course(self, row) -> Course:
        """Convert database row to Course entity"""
        from course_management.domain.entities.course import DurationUnit
        import json

        # Extract metadata from JSONB column (now only contains tags)
        metadata = row.get('metadata', {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        elif metadata is None:
            metadata = {}

        return Course(
            id=str(row['id']),
            title=row['title'],
            description=row['description'],
            instructor_id=str(row['instructor_id']),
            category=row.get('category'),
            difficulty_level=DifficultyLevel(row['difficulty_level']),
            estimated_duration=row.get('estimated_duration'),
            duration_unit=DurationUnit(row['duration_unit']) if row.get('duration_unit') else None,
            price=row.get('price', 0.0),
            is_published=row.get('is_published', False),
            thumbnail_url=row.get('thumbnail_url'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            tags=metadata.get('tags', []),
            organization_id=str(row['organization_id']) if row.get('organization_id') else None,
            project_id=str(row['project_id']) if row.get('project_id') else None,
            track_id=str(row['track_id']) if row.get('track_id') else None,
            location_id=str(row['location_id']) if row.get('location_id') else None
        )

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
                    "SELECT * FROM course_creator.courses WHERE id = $1 AND instructor_id = $2",
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
                    "SELECT COUNT(DISTINCT c.id) FROM course_creator.courses c WHERE c.instructor_id = $1",
                    instructor_id
                )
                
                # Get courses with detailed information
                courses = await conn.fetch(
                    """SELECT * FROM course_creator.courses 
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

    async def get_published_courses(self, limit: int = 50, offset: int = 0) -> List[Course]:
        """
        Retrieve all published courses with pagination.

        Business Context:
        Published courses are available for student browsing and enrollment.
        This query supports the public course catalog feature.

        Args:
            limit: Maximum number of courses to return (default: 50, max: 100)
            offset: Number of courses to skip for pagination (default: 0)

        Returns:
            List of published Course domain entities
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, title, description, instructor_id, category,
                           difficulty_level, estimated_duration, is_published,
                           created_at, updated_at
                    FROM course_creator.courses
                    WHERE is_published = true
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit, offset
                )

                courses = []
                for row in rows:
                    # Convert database row to Course domain entity
                    course = Course(
                        id=str(row['id']),
                        title=row['title'],
                        description=row['description'],
                        instructor_id=str(row['instructor_id']),
                        category=row['category'] or 'General',
                        difficulty_level=DifficultyLevel(row['difficulty_level'] or 'beginner'),
                        estimated_duration=row['estimated_duration'] or 0,
                        is_published=row['is_published'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        tags=[]  # Tags loaded separately if needed
                    )
                    courses.append(course)

                return courses

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve published courses (limit={limit}, offset={offset})",
                operation="get_published_courses",
                table_name="courses",
                original_exception=e
            )

    async def get_all_courses(self, limit: int = 50, offset: int = 0) -> List[Course]:
        """
        Retrieve ALL courses (both published and unpublished) with pagination.

        Business Context:
        This method returns both published and draft courses, useful for:
        - Organization admins managing their training programs
        - Instructors viewing their course portfolios
        - Administrative interfaces requiring full course visibility

        Args:
            limit: Maximum number of courses to return (default: 50, max: 100)
            offset: Number of courses to skip for pagination (default: 0)

        Returns:
            List of all Course domain entities (published + unpublished)
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, title, description, instructor_id, category,
                           difficulty_level, estimated_duration, duration_unit,
                           price, is_published, created_at, updated_at, metadata,
                           organization_id, track_id, location_id
                    FROM course_creator.courses
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit, offset
                )

                courses = []
                for row in rows:
                    # Extract tags from metadata JSONB column
                    tags = []
                    if row['metadata']:
                        import json
                        metadata = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
                        tags = metadata.get('tags', [])

                    # Convert database row to Course domain entity
                    course = Course(
                        id=str(row['id']),
                        title=row['title'],
                        description=row['description'],
                        instructor_id=str(row['instructor_id']),
                        category=row['category'] or 'General',
                        difficulty_level=DifficultyLevel(row['difficulty_level'] or 'beginner'),
                        estimated_duration=row['estimated_duration'] if row['estimated_duration'] is not None else None,
                        duration_unit=DurationUnit(row['duration_unit']) if row['duration_unit'] else DurationUnit.WEEKS,
                        price=float(row['price']) if row['price'] else 0.0,
                        is_published=row['is_published'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        tags=tags,
                        organization_id=str(row['organization_id']) if row['organization_id'] else None,
                        track_id=str(row['track_id']) if row['track_id'] else None,
                        location_id=str(row['location_id']) if row['location_id'] else None
                    )
                    courses.append(course)

                return courses

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve all courses (limit={limit}, offset={offset})",
                operation="get_all_courses",
                table_name="courses",
                original_exception=e
            )