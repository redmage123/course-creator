"""
CourseRepository implementation following Repository pattern.
Provides data access layer for course operations.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CourseRepository:
    """
    Repository for course data operations following Repository pattern.
    Provides abstraction over database operations for courses.
    """
    
    def __init__(self, db):
        """
        Initialize CourseRepository with database connection.
        
        Args:
            db: Database connection/pool
        """
        self.db = db
    
    async def get_by_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a course by its ID.
        
        Args:
            course_id: The course ID
            
        Returns:
            Course dictionary or None if not found
        """
        try:
            query = """
                SELECT id, title, description, category, instructor_id, created_at, updated_at
                FROM courses 
                WHERE id = %s
            """
            
            row = await self.db.fetch_one(query, (course_id,))
            
            if row:
                return self._row_to_course(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting course {course_id}: {e}")
            raise
    
    async def save(self, course_data: Dict[str, Any]) -> str:
        """
        Save a course to the database.
        
        Args:
            course_data: Course data dictionary
            
        Returns:
            Course ID
        """
        try:
            query = """
                INSERT INTO courses (
                    id, title, description, category, instructor_id, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    instructor_id = EXCLUDED.instructor_id,
                    updated_at = EXCLUDED.updated_at
            """
            
            values = (
                course_data['id'],
                course_data['title'],
                course_data['description'],
                course_data.get('category', ''),
                course_data.get('instructor_id', ''),
                course_data.get('created_at', datetime.now().isoformat()),
                datetime.now().isoformat()
            )
            
            await self.db.execute(query, values)
            return course_data['id']
            
        except Exception as e:
            logger.error(f"Error saving course: {e}")
            raise
    
    def _row_to_course(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert database row to course dictionary.
        
        Args:
            row: Database row dictionary
            
        Returns:
            Course dictionary
        """
        return {
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'category': row['category'],
            'instructor_id': row['instructor_id'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }