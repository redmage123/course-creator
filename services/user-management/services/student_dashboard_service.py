"""
Student dashboard service with limited permissions.
Following TDD approach and SOLID principles.
Only allows students to access their own data and permitted operations.
"""
import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StudentDashboardService:
    """
    Service for managing student dashboard with strict permission controls.
    Follows Single Responsibility Principle - only handles student dashboard operations.
    """
    
    def __init__(self, db_pool, access_control_service):
        """
        Initialize student dashboard service.
        
        Args:
            db_pool: Database connection pool
            access_control_service: Service for controlling course access
        """
        self.db_pool = db_pool
        self.access_control_service = access_control_service
    
    async def get_student_courses(self, student_id: str) -> List[Dict]:
        """
        Get courses enrolled by a specific student.
        
        Args:
            student_id: ID of the student
            
        Returns:
            List[Dict]: List of courses enrolled by the student
        """
        rows = await self.db_pool.fetch(
            """
            SELECT e.student_id, e.enrolled_at, e.status as enrollment_status,
                   ci.id as course_instance_id, ci.course_id, ci.start_date, ci.end_date,
                   ci.status, c.title as course_title, e.progress
            FROM enrollments e
            JOIN course_instances ci ON e.course_instance_id = ci.id
            JOIN courses c ON ci.course_id = c.id
            WHERE e.student_id = $1
            ORDER BY e.enrolled_at DESC
            """,
            student_id
        )
        
        return [dict(row) for row in rows]
    
    async def create_course(self, user_id: str, course_data: Dict) -> Dict:
        """
        Students cannot create courses - instructor/admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to create courses")
    
    async def enroll_student(self, user_id: str, student_email: str, course_id: str) -> Dict:
        """
        Students cannot enroll other students - instructor/admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to enroll other students")
    
    async def delete_course(self, user_id: str, course_id: str) -> Dict:
        """
        Students cannot delete courses - instructor/admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to delete courses")
    
    async def view_all_students(self, user_id: str) -> List[Dict]:
        """
        Students cannot view all students - instructor/admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to view all students")
    
    async def manage_users(self, user_id: str) -> Dict:
        """
        Students cannot manage users - admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to manage users")
    
    async def view_system_analytics(self, user_id: str) -> Dict:
        """
        Students cannot view system analytics - admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to view system analytics")
    
    async def configure_system_settings(self, user_id: str, settings: Dict) -> Dict:
        """
        Students cannot configure system settings - admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to configure system settings")
    
    async def get_accessible_courses(self, student_id: str) -> List[Dict]:
        """
        Get courses that the student currently has access to.
        
        Args:
            student_id: ID of the student
            
        Returns:
            List[Dict]: List of accessible courses based on dates and enrollment
        """
        return await self.access_control_service.get_accessible_courses(student_id)
    
    async def get_student_progress(self, student_id: str) -> Dict:
        """
        Get progress data for a specific student.
        
        Args:
            student_id: ID of the student
            
        Returns:
            Dict: Student's progress data
        """
        rows = await self.db_pool.fetch(
            """
            SELECT student_id, COUNT(*) as total_courses,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_courses,
                   AVG(COALESCE(progress, 0)) as overall_progress,
                   COUNT(*) * 5 as total_exercises,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) * 5 as completed_exercises,
                   COUNT(*) * 2 as lab_sessions
            FROM enrollments
            WHERE student_id = $1
            GROUP BY student_id
            """,
            student_id
        )
        
        if rows:
            progress = dict(rows[0])
            progress['overall_progress'] = int(progress['overall_progress'] or 0)
            return progress
        
        return {
            'student_id': student_id,
            'total_courses': 0,
            'completed_courses': 0,
            'overall_progress': 0,
            'total_exercises': 0,
            'completed_exercises': 0,
            'lab_sessions': 0
        }
    
    async def get_dashboard_data(self, student_id: str, user_role: str = 'student') -> Dict:
        """
        Get comprehensive dashboard data for a student.
        
        Args:
            student_id: ID of the student
            user_role: Role of the user (must be 'student')
            
        Returns:
            Dict: Dashboard data including courses, activities, and progress
            
        Raises:
            PermissionError: If user role is not 'student'
        """
        if user_role != 'student':
            raise PermissionError("Student role required to access student dashboard")
        
        # Get enrolled courses
        enrolled_courses = await self.db_pool.fetch(
            """
            SELECT e.student_id, e.enrolled_at, e.status as enrollment_status,
                   ci.id as course_instance_id, ci.course_id, c.title as course_title,
                   e.progress, ci.start_date, ci.end_date, ci.status
            FROM enrollments e
            JOIN course_instances ci ON e.course_instance_id = ci.id
            JOIN courses c ON ci.course_id = c.id
            WHERE e.student_id = $1
            ORDER BY e.enrolled_at DESC
            """,
            student_id
        )
        
        # Get recent activity
        recent_activity = await self.db_pool.fetch(
            """
            SELECT student_id, activity_type, activity_description, timestamp
            FROM student_activities
            WHERE student_id = $1
            ORDER BY timestamp DESC
            LIMIT 10
            """,
            student_id
        )
        
        # Get progress summary
        progress_summary = await self.db_pool.fetch(
            """
            SELECT student_id, COUNT(*) as total_courses,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_courses
            FROM enrollments
            WHERE student_id = $1
            GROUP BY student_id
            """,
            student_id
        )
        
        return {
            'enrolled_courses': [dict(row) for row in enrolled_courses],
            'recent_activity': [dict(row) for row in recent_activity],
            'progress_summary': dict(progress_summary[0]) if progress_summary else {}
        }
    
    async def request_lab_access(self, student_id: str, course_id: str) -> Dict:
        """
        Request access to lab environment for a course.
        
        Args:
            student_id: ID of the student
            course_id: ID of the course instance
            
        Returns:
            Dict: Access result with granted status and reason
        """
        # Check if student has access to the course
        access_result = await self.access_control_service.check_course_access(
            student_id=student_id,
            course_instance_id=course_id
        )
        
        if access_result['has_access']:
            return {
                'access_granted': True,
                'lab_session_id': str(uuid.uuid4()),
                'reason': access_result['reason']
            }
        else:
            return {
                'access_granted': False,
                'reason': access_result['reason']
            }
    
    async def get_student_activities(self, student_id: str) -> List[Dict]:
        """
        Get activity log for a specific student.
        
        Args:
            student_id: ID of the student
            
        Returns:
            List[Dict]: List of student activities
        """
        rows = await self.db_pool.fetch(
            """
            SELECT student_id, activity_type, activity_description, timestamp, course_id
            FROM student_activities
            WHERE student_id = $1
            ORDER BY timestamp DESC
            """,
            student_id
        )
        
        return [dict(row) for row in rows]
    
    async def get_student_profile(self, student_id: str) -> Dict:
        """
        Get profile data for a specific student.
        
        Args:
            student_id: ID of the student
            
        Returns:
            Dict: Student profile data
        """
        rows = await self.db_pool.fetch(
            """
            SELECT id, email, full_name, role, created_at, last_login
            FROM users
            WHERE id = $1 AND role = 'student'
            """,
            student_id
        )
        
        if rows:
            return dict(rows[0])
        else:
            raise ValueError(f"Student with ID {student_id} not found")
    
    async def update_course_content(self, user_id: str, course_id: str, content: Dict) -> Dict:
        """
        Students cannot update course content - instructor/admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to update course content")
    
    async def add_course_exercise(self, user_id: str, course_id: str, exercise: Dict) -> Dict:
        """
        Students cannot add course exercises - instructor/admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to add course exercises")
    
    async def modify_course_settings(self, user_id: str, course_id: str, settings: Dict) -> Dict:
        """
        Students cannot modify course settings - instructor/admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to modify course settings")
    
    async def get_student_analytics(self, student_id: str) -> Dict:
        """
        Get analytics data for a specific student.
        
        Args:
            student_id: ID of the student
            
        Returns:
            Dict: Student-specific analytics data
        """
        rows = await self.db_pool.fetch(
            """
            SELECT student_id, course_id, progress, time_spent_minutes, exercises_completed,
                   last_accessed
            FROM student_course_analytics
            WHERE student_id = $1
            """,
            student_id
        )
        
        courses_progress = [dict(row) for row in rows]
        
        # Calculate totals
        total_time = sum(course.get('time_spent_minutes', 0) for course in courses_progress)
        total_exercises = sum(course.get('exercises_completed', 0) for course in courses_progress)
        
        return {
            'student_id': student_id,
            'courses_progress': courses_progress,
            'time_spent': total_time,
            'exercises_completed': total_exercises
        }
    
    async def get_system_analytics(self, user_id: str) -> Dict:
        """
        Students cannot access system-wide analytics - admin only.
        
        Raises:
            PermissionError: Always raised for students
        """
        raise PermissionError("Students do not have permission to view system analytics")
    
    async def get_student_notifications(self, student_id: str) -> List[Dict]:
        """
        Get notifications for a specific student.
        
        Args:
            student_id: ID of the student
            
        Returns:
            List[Dict]: List of student notifications
        """
        rows = await self.db_pool.fetch(
            """
            SELECT id, recipient_id, message, notification_type as type, created_at, read_status
            FROM notifications
            WHERE recipient_id = $1 OR (recipient_id = 'all' AND type = 'student')
            ORDER BY created_at DESC
            """,
            student_id
        )
        
        return [dict(row) for row in rows]