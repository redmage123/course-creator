"""
Student access control service for managing time-based course access.
Following TDD approach and SOLID principles.
"""
import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)


class StudentAccessControlService:
    """
    Service for controlling student access to courses based on enrollment dates.
    Follows Single Responsibility Principle - only handles access control logic.
    """
    
    def __init__(self, db_pool):
        """
        Initialize student access control service.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    async def check_course_access(
        self,
        student_id: str,
        course_instance_id: str,
        user_role: str = 'student',
        grace_period_hours: int = 0,
        maintenance_mode: bool = False,
        user_timezone: str = 'UTC',
        log_access: bool = False
    ) -> Dict:
        """
        Check if a student has access to a specific course instance.
        
        Args:
            student_id: ID of the student/user
            course_instance_id: ID of the course instance
            user_role: Role of the user (student, instructor, admin)
            grace_period_hours: Grace period for late access in hours
            maintenance_mode: Whether system is in maintenance mode
            user_timezone: User's timezone for date calculations
            log_access: Whether to log the access attempt
            
        Returns:
            Dict: Access result with has_access, reason, and message
        """
        current_time = datetime.now()
        
        # Check maintenance mode first
        if maintenance_mode:
            return {
                'has_access': False,
                'reason': 'maintenance_mode',
                'message': 'System is currently under maintenance. Please try again later.'
            }
        
        # Site admin and instructor overrides
        if user_role == 'site_admin':
            return {
                'has_access': True,
                'reason': 'site_admin_override',
                'message': 'Site admin access granted'
            }
        
        if user_role == 'instructor':
            return {
                'has_access': True,
                'reason': 'instructor_override',
                'message': 'Instructor access granted'
            }
        
        # Get enrollment and course instance data
        enrollment_data = await self.db_pool.fetch(
            """
            SELECT e.student_id, e.enrolled_at, e.status as enrollment_status,
                   ci.id, ci.course_id, ci.start_date, ci.end_date, ci.status,
                   ci.timezone, c.title
            FROM enrollments e
            JOIN course_instances ci ON e.course_instance_id = ci.id
            JOIN courses c ON ci.course_id = c.id
            WHERE e.student_id = $1 AND ci.id = $2
            """,
            student_id, course_instance_id
        )
        
        if not enrollment_data:
            return {
                'has_access': False,
                'reason': 'not_enrolled',
                'message': 'You are not enrolled in this course'
            }
        
        enrollment = enrollment_data[0]
        start_date = enrollment['start_date']
        end_date = enrollment['end_date']
        
        # Apply grace period if specified
        effective_start = start_date - timedelta(hours=grace_period_hours)
        
        # Check date-based access
        if current_time < effective_start:
            return {
                'has_access': False,
                'reason': 'course_not_started',
                'message': f"Course access will be available on {start_date.strftime('%B %d, %Y')}",
                'start_date': start_date
            }
        
        if current_time > end_date:
            return {
                'has_access': False,
                'reason': 'course_completed',
                'message': 'This course has been completed and is no longer accessible'
            }
        
        # Course is accessible
        result = {
            'has_access': True,
            'reason': 'course_active',
            'message': f"Course is currently active until {end_date.strftime('%B %d, %Y')}",
            'end_date': end_date
        }
        
        # Log access attempt if requested
        if log_access:
            await self.db_pool.execute(
                """
                INSERT INTO access_logs (id, student_id, course_instance_id, access_time, 
                                       access_granted, reason, user_agent, ip_address)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                str(uuid.uuid4()), student_id, course_instance_id, current_time,
                result['has_access'], result['reason'], None, None
            )
        
        return result
    
    async def get_accessible_courses(self, student_id: str) -> List[Dict]:
        """
        Get all courses that a student can currently access.
        
        Args:
            student_id: ID of the student
            
        Returns:
            List[Dict]: List of accessible course instances
        """
        current_time = datetime.now()
        
        rows = await self.db_pool.fetch(
            """
            SELECT ci.id as course_instance_id, c.title as course_title,
                   ci.start_date, ci.end_date, ci.status, c.description,
                   ci.timezone, ci.meeting_schedule
            FROM enrollments e
            JOIN course_instances ci ON e.course_instance_id = ci.id
            JOIN courses c ON ci.course_id = c.id
            WHERE e.student_id = $1 
              AND ci.start_date <= $2 
              AND ci.end_date >= $2
              AND e.status = 'enrolled'
            ORDER BY ci.start_date ASC
            """,
            student_id, current_time
        )
        
        return [dict(row) for row in rows]
    
    async def get_upcoming_courses(self, student_id: str) -> List[Dict]:
        """
        Get courses that the student will have access to in the future.
        
        Args:
            student_id: ID of the student
            
        Returns:
            List[Dict]: List of upcoming course instances
        """
        current_time = datetime.now()
        
        rows = await self.db_pool.fetch(
            """
            SELECT ci.id as course_instance_id, c.title as course_title,
                   ci.start_date, ci.end_date, ci.status, c.description,
                   ci.timezone, ci.meeting_schedule
            FROM enrollments e
            JOIN course_instances ci ON e.course_instance_id = ci.id
            JOIN courses c ON ci.course_id = c.id
            WHERE e.student_id = $1 
              AND ci.start_date > $2
              AND e.status = 'enrolled'
            ORDER BY ci.start_date ASC
            """,
            student_id, current_time
        )
        
        return [dict(row) for row in rows]
    
    async def bulk_check_course_access(
        self,
        student_id: str,
        course_instance_ids: List[str]
    ) -> List[Dict]:
        """
        Check access to multiple courses at once.
        
        Args:
            student_id: ID of the student
            course_instance_ids: List of course instance IDs
            
        Returns:
            List[Dict]: List of access results
        """
        results = []
        
        for course_instance_id in course_instance_ids:
            access_result = await self.check_course_access(
                student_id=student_id,
                course_instance_id=course_instance_id
            )
            access_result['course_instance_id'] = course_instance_id
            results.append(access_result)
        
        return results