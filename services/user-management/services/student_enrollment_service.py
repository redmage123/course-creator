"""
Student enrollment service for handling automatic enrollment with password generation.
"""
import uuid
import secrets
import string
from datetime import datetime
from typing import Dict, List, Optional


class PasswordGenerator:
    """Generates secure random passwords for students"""
    
    def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password


class EmailService:
    """Service for sending enrollment notification emails"""
    
    async def send_enrollment_notification(self, **kwargs) -> bool:
        """Send enrollment notification email to student"""
        # This will be implemented in the next iteration
        return True


class StudentEnrollmentService:
    """Service for managing student enrollments with auto-generated credentials"""
    
    def __init__(self, db_pool, email_service=None, password_generator=None):
        self.db_pool = db_pool
        self.email_service = email_service or EmailService()
        self.password_generator = password_generator or PasswordGenerator()
    
    async def enroll_student(self, student_email: str, course_instance: Dict) -> Dict:
        """
        Enroll a student in a course instance with auto-generated password
        
        Args:
            student_email: Email address of the student
            course_instance: Dictionary containing course instance details
            
        Returns:
            Dictionary with enrollment result including password if new user
        """
        # Check if student already exists
        existing_user = await self.db_pool.fetch(
            "SELECT id, email, role FROM users WHERE email = $1",
            student_email
        )
        
        if existing_user:
            # Student exists, just create enrollment
            user_id = existing_user[0]['id']
            password = None
        else:
            # Create new student account with generated password
            password = self.password_generator.generate_password()
            user_id = str(uuid.uuid4())
            
            # Hash password (simplified for now)
            password_hash = password  # In real implementation, use bcrypt
            
            await self.db_pool.execute(
                """
                INSERT INTO users (id, email, password_hash, role, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id, student_email, password_hash, 'student', datetime.now()
            )
        
        # Create enrollment record
        enrollment_id = str(uuid.uuid4())
        await self.db_pool.execute(
            """
            INSERT INTO enrollments (id, student_id, course_instance_id, enrolled_at, status)
            VALUES ($1, $2, $3, $4, $5)
            """,
            enrollment_id, user_id, course_instance['id'], datetime.now(), 'active'
        )
        
        # Send enrollment notification email
        await self.email_service.send_enrollment_notification(
            student_email=student_email,
            course_title=course_instance['title'],
            instructor_name=course_instance['instructor_name'],
            start_date=course_instance['start_date'],
            end_date=course_instance['end_date'],
            login_email=student_email,
            password=password
        )
        
        return {
            'user_id': user_id,
            'email': student_email,
            'password': password,
            'enrollment_id': enrollment_id
        }