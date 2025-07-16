"""
Progress Repository

Database operations for progress tracking.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncpg
from datetime import datetime

from .base_repository import BaseRepository


class ProgressRepository(BaseRepository):
    """
    Repository for progress tracking operations.
    
    Handles database operations for progress management.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize progress repository.
        
        Args:
            db_pool: Database connection pool
        """
        super().__init__(db_pool)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def update_enrollment_progress(self, enrollment_id: str, 
                                       progress_percentage: float,
                                       last_accessed: datetime = None) -> bool:
        """
        Update enrollment progress.
        
        Args:
            enrollment_id: Enrollment ID
            progress_percentage: Progress percentage
            last_accessed: Last accessed timestamp
            
        Returns:
            True if successful, False otherwise
        """
        try:
            now = self.current_timestamp()
            last_accessed = last_accessed or now
            
            update_data = {
                'progress_percentage': progress_percentage,
                'last_accessed': last_accessed,
                'updated_at': now
            }
            
            # Mark as completed if progress is 100%
            if progress_percentage >= 100:
                update_data['completed_at'] = now
                update_data['status'] = 'completed'
            
            query, args = self.build_update_query(
                'enrollments',
                update_data,
                f"id = ${len(update_data) + 1}"
            )
            args.append(self.parse_uuid(enrollment_id))
            
            result = await self.execute_query(query, *args)
            
            success = result != "UPDATE 0"
            if success:
                self.logger.info(f"Updated progress for enrollment {enrollment_id}: {progress_percentage}%")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating enrollment progress: {e}")
            raise
    
    async def get_student_progress_summary(self, student_id: str) -> Dict[str, Any]:
        """
        Get progress summary for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            Progress summary dictionary
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_enrollments,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_enrollments,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_enrollments,
                    AVG(progress_percentage) as average_progress,
                    SUM(CASE WHEN progress_percentage > 0 THEN 1 ELSE 0 END) as started_courses
                FROM enrollments
                WHERE student_id = $1
            """
            
            row = await self.fetch_one(query, self.parse_uuid(student_id))
            
            if row:
                return {
                    'total_enrollments': row['total_enrollments'],
                    'active_enrollments': row['active_enrollments'],
                    'completed_enrollments': row['completed_enrollments'],
                    'average_progress': float(row['average_progress']) if row['average_progress'] else 0.0,
                    'started_courses': row['started_courses']
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting student progress summary: {e}")
            raise
    
    async def get_course_progress_summary(self, course_id: str) -> Dict[str, Any]:
        """
        Get progress summary for a course.
        
        Args:
            course_id: Course ID
            
        Returns:
            Progress summary dictionary
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_students,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_students,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_students,
                    AVG(progress_percentage) as average_progress,
                    COUNT(CASE WHEN progress_percentage > 0 THEN 1 END) as started_students
                FROM enrollments
                WHERE course_id = $1
            """
            
            row = await self.fetch_one(query, self.parse_uuid(course_id))
            
            if row:
                total_students = row['total_students']
                completion_rate = (row['completed_students'] / total_students * 100) if total_students > 0 else 0.0
                
                return {
                    'total_students': total_students,
                    'active_students': row['active_students'],
                    'completed_students': row['completed_students'],
                    'average_progress': float(row['average_progress']) if row['average_progress'] else 0.0,
                    'started_students': row['started_students'],
                    'completion_rate': completion_rate
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting course progress summary: {e}")
            raise