"""
Email service for sending enrollment notifications to students.
Following TDD approach and SOLID principles.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending email notifications.
    Follows Single Responsibility Principle - only handles email sending.
    """
    
    def __init__(self, smtp_config: Optional[Dict] = None):
        """
        Initialize email service with SMTP configuration.
        
        Args:
            smtp_config: Dictionary with SMTP settings (host, port, username, password)
        """
        self.smtp_config = smtp_config or {
            'host': 'localhost',
            'port': 1025,  # Default for development (mailhog/similar)
            'username': None,
            'password': None,
            'use_tls': False
        }
    
    async def send_enrollment_notification(
        self,
        student_email: str,
        course_title: str,
        instructor_name: str,
        start_date: datetime,
        end_date: datetime,
        login_email: str,
        password: str
    ) -> bool:
        """
        Send enrollment notification email to student.
        
        Args:
            student_email: Student's email address
            course_title: Title of the course
            instructor_name: Full name of the instructor
            start_date: Course start date
            end_date: Course end date
            login_email: Email to use for login
            password: Generated password for student
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get('from_email', 'noreply@courseplatform.com')
            msg['To'] = student_email
            msg['Subject'] = f"Course Enrollment: {course_title}"
            
            # Create email body
            body = self._create_enrollment_email_body(
                course_title=course_title,
                instructor_name=instructor_name,
                start_date=start_date,
                end_date=end_date,
                login_email=login_email,
                password=password
            )
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            await self._send_email(msg)
            
            logger.info(f"Enrollment notification sent to {student_email} for course {course_title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send enrollment notification to {student_email}: {str(e)}")
            return False
    
    def _create_enrollment_email_body(
        self,
        course_title: str,
        instructor_name: str,
        start_date: datetime,
        end_date: datetime,
        login_email: str,
        password: str
    ) -> str:
        """
        Create HTML email body for enrollment notification.
        
        Returns:
            str: HTML formatted email body
        """
        return f"""
        <html>
        <body>
            <h2>Welcome to {course_title}!</h2>
            
            <p>You have been enrolled in the following course:</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <h3>Course Details</h3>
                <ul>
                    <li><strong>Course Title:</strong> {course_title}</li>
                    <li><strong>Instructor:</strong> {instructor_name}</li>
                    <li><strong>Start Date:</strong> {start_date.strftime('%B %d, %Y at %I:%M %p')}</li>
                    <li><strong>End Date:</strong> {end_date.strftime('%B %d, %Y at %I:%M %p')}</li>
                </ul>
            </div>
            
            <div style="background-color: #e8f4fd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <h3>Login Credentials</h3>
                <ul>
                    <li><strong>Login Email:</strong> {login_email}</li>
                    <li><strong>Password:</strong> {password}</li>
                </ul>
                <p><em>Please keep these credentials secure and change your password after first login.</em></p>
            </div>
            
            <p>You will be able to access the course starting on {start_date.strftime('%B %d, %Y')}. 
            Please log in using the credentials above.</p>
            
            <p>If you have any questions about the course, please contact your instructor {instructor_name}.</p>
            
            <hr>
            <p><small>This is an automated message from the Course Management Platform.</small></p>
        </body>
        </html>
        """
    
    async def _send_email(self, msg: MIMEMultipart) -> None:
        """
        Send email using SMTP configuration.
        
        Args:
            msg: Email message to send
            
        Raises:
            Exception: If email sending fails
        """
        # For development/testing, we'll log the email instead of actually sending
        # In production, this would use real SMTP
        if self.smtp_config.get('development_mode', True):
            logger.info(f"[DEV MODE] Email would be sent:")
            logger.info(f"To: {msg['To']}")
            logger.info(f"Subject: {msg['Subject']}")
            logger.info(f"Body preview: {str(msg.get_payload()[0])[:200]}...")
            return
        
        # Real SMTP sending (commented out for development)
        # with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
        #     if self.smtp_config.get('use_tls'):
        #         server.starttls()
        #     if self.smtp_config.get('username'):
        #         server.login(self.smtp_config['username'], self.smtp_config['password'])
        #     server.send_message(msg)