"""
PostgreSQL Course Repository Implementation
Single Responsibility: Handle course data persistence in PostgreSQL
Dependency Inversion: Implements abstract repository interface
"""
import asyncpg
from typing import List, Optional, Dict, Any
from datetime import datetime
from domain.entities.course import Course, CourseStatistics, DifficultyLevel, DurationUnit
from domain.interfaces.course_repository import ICourseRepository

class PostgreSQLCourseRepository(ICourseRepository):
    """
    PostgreSQL implementation of course repository
    """
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def create(self, course: Course) -> Course:
        """Create a new course in PostgreSQL"""
        async with self._pool.acquire() as connection:
            query = """
                INSERT INTO courses (
                    id, title, description, instructor_id, category, 
                    difficulty_level, estimated_duration, duration_unit, 
                    price, is_published, thumbnail_url, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING *
            """
            
            row = await connection.fetchrow(
                query,
                course.id,
                course.title,
                course.description,
                course.instructor_id,
                course.category,
                course.difficulty_level.value if course.difficulty_level else None,
                course.estimated_duration,
                course.duration_unit.value if course.duration_unit else None,
                course.price,
                course.is_published,
                course.thumbnail_url,
                course.created_at or datetime.utcnow(),
                course.updated_at or datetime.utcnow()
            )
            
            return self._row_to_course(row)
    
    async def get_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID from PostgreSQL"""
        async with self._pool.acquire() as connection:
            query = "SELECT * FROM courses WHERE id = $1"
            row = await connection.fetchrow(query, course_id)
            
            return self._row_to_course(row) if row else None
    
    async def get_by_instructor_id(self, instructor_id: str) -> List[Course]:
        """Get all courses for an instructor"""
        async with self._pool.acquire() as connection:
            query = """
                SELECT * FROM courses 
                WHERE instructor_id = $1 
                ORDER BY created_at DESC
            """
            rows = await connection.fetch(query, instructor_id)
            
            return [self._row_to_course(row) for row in rows]
    
    async def get_published_courses(self, limit: int = 50, offset: int = 0) -> List[Course]:
        """Get paginated list of published courses"""
        async with self._pool.acquire() as connection:
            query = """
                SELECT * FROM courses 
                WHERE is_published = true 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
            """
            rows = await connection.fetch(query, limit, offset)
            
            return [self._row_to_course(row) for row in rows]
    
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Course]:
        """Search courses by query and optional filters"""
        async with self._pool.acquire() as connection:
            # Build dynamic query
            where_conditions = ["is_published = true"]
            params = []
            param_count = 1
            
            # Text search
            where_conditions.append(f"(title ILIKE ${param_count} OR description ILIKE ${param_count})")
            params.append(f"%{query}%")
            param_count += 1
            
            # Apply filters if provided
            if filters:
                if 'category' in filters:
                    where_conditions.append(f"category = ${param_count}")
                    params.append(filters['category'])
                    param_count += 1
                
                if 'difficulty_level' in filters:
                    where_conditions.append(f"difficulty_level = ${param_count}")
                    params.append(filters['difficulty_level'])
                    param_count += 1
            
            search_query = f"""
                SELECT * FROM courses 
                WHERE {' AND '.join(where_conditions)}
                ORDER BY created_at DESC
                LIMIT 100
            """
            
            rows = await connection.fetch(search_query, *params)
            return [self._row_to_course(row) for row in rows]
    
    async def update(self, course: Course) -> Course:
        """Update an existing course"""
        async with self._pool.acquire() as connection:
            query = """
                UPDATE courses SET 
                    title = $2, description = $3, category = $4,
                    difficulty_level = $5, estimated_duration = $6, 
                    duration_unit = $7, price = $8, is_published = $9,
                    thumbnail_url = $10, updated_at = $11
                WHERE id = $1
                RETURNING *
            """
            
            row = await connection.fetchrow(
                query,
                course.id,
                course.title,
                course.description,
                course.category,
                course.difficulty_level.value if course.difficulty_level else None,
                course.estimated_duration,
                course.duration_unit.value if course.duration_unit else None,
                course.price,
                course.is_published,
                course.thumbnail_url,
                datetime.utcnow()
            )
            
            return self._row_to_course(row) if row else course
    
    async def delete(self, course_id: str) -> bool:
        """Delete a course from PostgreSQL"""
        async with self._pool.acquire() as connection:
            query = "DELETE FROM courses WHERE id = $1"
            result = await connection.execute(query, course_id)
            
            # Check if any rows were affected
            return result.split()[-1] == '1'
    
    async def exists(self, course_id: str) -> bool:
        """Check if course exists"""
        async with self._pool.acquire() as connection:
            query = "SELECT 1 FROM courses WHERE id = $1"
            row = await connection.fetchrow(query, course_id)
            
            return row is not None
    
    async def count_by_instructor(self, instructor_id: str) -> int:
        """Count courses by instructor"""
        async with self._pool.acquire() as connection:
            query = "SELECT COUNT(*) FROM courses WHERE instructor_id = $1"
            count = await connection.fetchval(query, instructor_id)
            
            return count or 0
    
    async def get_statistics(self, course_id: str) -> Optional[CourseStatistics]:
        """Get course statistics"""
        async with self._pool.acquire() as connection:
            # Get basic course info
            course_query = "SELECT id FROM courses WHERE id = $1"
            course_row = await connection.fetchrow(course_query, course_id)
            
            if not course_row:
                return None
            
            # Get enrollment statistics
            enrollment_query = """
                SELECT 
                    COUNT(*) as total_enrollments,
                    COUNT(*) FILTER (WHERE status = 'active') as active_enrollments,
                    AVG(progress_percentage) as avg_progress
                FROM enrollments 
                WHERE course_id = $1
            """
            enrollment_stats = await connection.fetchrow(enrollment_query, course_id)
            
            # Get feedback statistics
            feedback_query = """
                SELECT 
                    COUNT(*) as total_feedback,
                    AVG(overall_rating) as avg_rating
                FROM course_feedback 
                WHERE course_id = $1 AND status = 'active'
            """
            feedback_stats = await connection.fetchrow(feedback_query, course_id)
            
            return CourseStatistics(
                course_id=course_id,
                enrolled_students=enrollment_stats['total_enrollments'] or 0,
                active_enrollments=enrollment_stats['active_enrollments'] or 0,
                completion_rate=enrollment_stats['avg_progress'] or 0.0,
                average_rating=float(feedback_stats['avg_rating'] or 0.0),
                total_feedback=feedback_stats['total_feedback'] or 0,
                last_updated=datetime.utcnow()
            )
    
    async def get_courses_by_category(self, category: str) -> List[Course]:
        """Get courses by category"""
        async with self._pool.acquire() as connection:
            query = """
                SELECT * FROM courses 
                WHERE category = $1 AND is_published = true
                ORDER BY created_at DESC
            """
            rows = await connection.fetch(query, category)
            
            return [self._row_to_course(row) for row in rows]
    
    async def get_courses_by_difficulty(self, difficulty: str) -> List[Course]:
        """Get courses by difficulty level"""
        async with self._pool.acquire() as connection:
            query = """
                SELECT * FROM courses 
                WHERE difficulty_level = $1 AND is_published = true
                ORDER BY created_at DESC
            """
            rows = await connection.fetch(query, difficulty)
            
            return [self._row_to_course(row) for row in rows]
    
    def _row_to_course(self, row) -> Course:
        """Convert database row to Course entity"""
        if not row:
            return None
        
        # Handle enum conversions
        difficulty_level = None
        if row['difficulty_level']:
            try:
                difficulty_level = DifficultyLevel(row['difficulty_level'])
            except ValueError:
                difficulty_level = DifficultyLevel.BEGINNER
        
        duration_unit = None
        if row['duration_unit']:
            try:
                duration_unit = DurationUnit(row['duration_unit'])
            except ValueError:
                duration_unit = DurationUnit.WEEKS
        
        return Course(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            instructor_id=row['instructor_id'],
            category=row['category'],
            difficulty_level=difficulty_level or DifficultyLevel.BEGINNER,
            estimated_duration=row['estimated_duration'],
            duration_unit=duration_unit or DurationUnit.WEEKS,
            price=float(row['price'] or 0.0),
            is_published=row['is_published'] or False,
            thumbnail_url=row['thumbnail_url'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )