"""
Course Repository

Database operations for course management.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncpg
from datetime import datetime

from repositories.base_repository import BaseRepository
from models.course import Course, CourseCreate, CourseUpdate, CourseSearchRequest


class CourseRepository(BaseRepository):
    """
    Repository for course data operations.
    
    Handles database operations for course management.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize course repository.
        
        Args:
            db_pool: Database connection pool
        """
        super().__init__(db_pool)
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
            course_id = self.generate_uuid()
            now = self.current_timestamp()
            
            query = """
                INSERT INTO courses (id, title, description, instructor_id, category,
                                   difficulty_level, estimated_duration, price, is_published,
                                   thumbnail_url, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """
            
            await self.execute_query(
                query,
                self.parse_uuid(course_id),
                course_data.title,
                course_data.description,
                self.parse_uuid(course_data.instructor_id),
                course_data.category,
                course_data.difficulty_level,
                course_data.estimated_duration,
                course_data.price,
                False,  # is_published defaults to False
                course_data.thumbnail_url,
                now,
                now
            )
            
            # Fetch the created course
            created_course = await self.get_course_by_id(course_id)
            
            if created_course:
                self.logger.info(f"Created course: {course_data.title} (ID: {course_id})")
                return created_course
            
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
            query = """
                SELECT id, title, description, instructor_id, category, 
                       difficulty_level, estimated_duration, price, is_published,
                       thumbnail_url, created_at, updated_at
                FROM courses 
                WHERE id = $1
            """
            
            row = await self.fetch_one(query, self.parse_uuid(course_id))
            
            if row:
                return self._convert_to_course_model(row)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting course by ID {course_id}: {e}")
            raise
    
    async def get_courses_by_instructor(self, instructor_id: str, 
                                      limit: int = 100, offset: int = 0) -> List[Course]:
        """
        Get courses by instructor ID.
        
        Args:
            instructor_id: Instructor ID
            limit: Maximum number of courses to return
            offset: Number of courses to skip
            
        Returns:
            List of courses
        """
        try:
            query = """
                SELECT id, title, description, instructor_id, category, 
                       difficulty_level, estimated_duration, price, is_published,
                       thumbnail_url, created_at, updated_at
                FROM courses
                WHERE instructor_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            
            rows = await self.fetch_all(
                query, 
                self.parse_uuid(instructor_id), 
                limit, 
                offset
            )
            
            courses = [self._convert_to_course_model(row) for row in rows]
            return courses
            
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
            # Build update data
            update_data = {}
            
            if updates.title is not None:
                update_data['title'] = updates.title
            if updates.description is not None:
                update_data['description'] = updates.description
            if updates.category is not None:
                update_data['category'] = updates.category
            if updates.difficulty_level is not None:
                update_data['difficulty_level'] = updates.difficulty_level
            if updates.estimated_duration is not None:
                update_data['estimated_duration'] = updates.estimated_duration
            if updates.price is not None:
                update_data['price'] = updates.price
            if updates.is_published is not None:
                update_data['is_published'] = updates.is_published
            if updates.thumbnail_url is not None:
                update_data['thumbnail_url'] = updates.thumbnail_url
            
            if update_data:
                update_data['updated_at'] = self.current_timestamp()
                
                query, args = self.build_update_query(
                    'courses', 
                    update_data, 
                    f"id = ${len(update_data) + 1}"
                )
                args.append(self.parse_uuid(course_id))
                
                result = await self.execute_query(query, *args)
                
                if result == "UPDATE 0":
                    return None
            
            # Get updated course
            return await self.get_course_by_id(course_id)
            
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
            query = "DELETE FROM courses WHERE id = $1"
            result = await self.execute_query(query, self.parse_uuid(course_id))
            
            success = result != "DELETE 0"
            if success:
                self.logger.info(f"Deleted course: {course_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting course {course_id}: {e}")
            raise
    
    async def search_courses(self, search_request: CourseSearchRequest,
                           limit: int = 100, offset: int = 0) -> List[Course]:
        """
        Search courses based on criteria.
        
        Args:
            search_request: Search criteria
            limit: Maximum number of courses to return
            offset: Number of courses to skip
            
        Returns:
            List of matching courses
        """
        try:
            # Build search conditions
            conditions = []
            args = []
            arg_index = 1
            
            if search_request.query:
                conditions.append(f"(title ILIKE ${arg_index} OR description ILIKE ${arg_index})")
                args.append(f"%{search_request.query}%")
                arg_index += 1
            
            if search_request.category:
                conditions.append(f"category = ${arg_index}")
                args.append(search_request.category)
                arg_index += 1
            
            if search_request.difficulty_level:
                conditions.append(f"difficulty_level = ${arg_index}")
                args.append(search_request.difficulty_level)
                arg_index += 1
            
            if search_request.instructor_id:
                conditions.append(f"instructor_id = ${arg_index}")
                args.append(self.parse_uuid(search_request.instructor_id))
                arg_index += 1
            
            if search_request.is_published is not None:
                conditions.append(f"is_published = ${arg_index}")
                args.append(search_request.is_published)
                arg_index += 1
            
            if search_request.price_min is not None:
                conditions.append(f"price >= ${arg_index}")
                args.append(search_request.price_min)
                arg_index += 1
            
            if search_request.price_max is not None:
                conditions.append(f"price <= ${arg_index}")
                args.append(search_request.price_max)
                arg_index += 1
            
            if search_request.duration_min is not None:
                conditions.append(f"estimated_duration >= ${arg_index}")
                args.append(search_request.duration_min)
                arg_index += 1
            
            if search_request.duration_max is not None:
                conditions.append(f"estimated_duration <= ${arg_index}")
                args.append(search_request.duration_max)
                arg_index += 1
            
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            query = f"""
                SELECT id, title, description, instructor_id, category, 
                       difficulty_level, estimated_duration, price, is_published,
                       thumbnail_url, created_at, updated_at
                FROM courses
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${arg_index} OFFSET ${arg_index + 1}
            """
            
            args.extend([limit, offset])
            
            rows = await self.fetch_all(query, *args)
            courses = [self._convert_to_course_model(row) for row in rows]
            
            return courses
            
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
            query = """
                SELECT id, title, description, instructor_id, category, 
                       difficulty_level, estimated_duration, price, is_published,
                       thumbnail_url, created_at, updated_at
                FROM courses
                WHERE is_published = true
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            
            rows = await self.fetch_all(query, limit, offset)
            courses = [self._convert_to_course_model(row) for row in rows]
            
            return courses
            
        except Exception as e:
            self.logger.error(f"Error getting published courses: {e}")
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
            if instructor_id:
                query = "SELECT COUNT(*) FROM courses WHERE instructor_id = $1"
                return await self.fetch_val(query, self.parse_uuid(instructor_id))
            else:
                query = "SELECT COUNT(*) FROM courses"
                return await self.fetch_val(query)
                
        except Exception as e:
            self.logger.error(f"Error counting courses: {e}")
            raise
    
    async def get_course_statistics(self) -> Dict[str, Any]:
        """
        Get course statistics.
        
        Returns:
            Dictionary with course statistics
        """
        try:
            stats = {}
            
            # Total courses
            stats['total_courses'] = await self.fetch_val("SELECT COUNT(*) FROM courses")
            
            # Published courses
            stats['published_courses'] = await self.fetch_val(
                "SELECT COUNT(*) FROM courses WHERE is_published = true"
            )
            
            # Draft courses
            stats['draft_courses'] = await self.fetch_val(
                "SELECT COUNT(*) FROM courses WHERE is_published = false"
            )
            
            # Courses by difficulty
            difficulty_stats = await self.fetch_all("""
                SELECT difficulty_level, COUNT(*) as count
                FROM courses
                GROUP BY difficulty_level
            """)
            
            stats['courses_by_difficulty'] = {
                row['difficulty_level']: row['count'] for row in difficulty_stats
            }
            
            # Courses by category
            category_stats = await self.fetch_all("""
                SELECT category, COUNT(*) as count
                FROM courses
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """)
            
            stats['courses_by_category'] = {
                row['category']: row['count'] for row in category_stats
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting course statistics: {e}")
            raise
    
    def _convert_to_course_model(self, row: asyncpg.Record) -> Course:
        """
        Convert database row to Course model.
        
        Args:
            row: Database row
            
        Returns:
            Course model instance
        """
        return Course(
            id=str(row['id']),
            title=row['title'],
            description=row['description'],
            instructor_id=str(row['instructor_id']),
            category=row['category'],
            difficulty_level=row['difficulty_level'],
            estimated_duration=row['estimated_duration'],
            price=float(row['price']),
            is_published=row['is_published'],
            thumbnail_url=row['thumbnail_url'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )