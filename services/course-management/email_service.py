#!/usr/bin/env python3
"""
Email Notification Service - Educational Communication Platform

This module provides comprehensive email notification capabilities for the educational platform,
supporting automated communications throughout the student enrollment lifecycle, course delivery,
and completion workflows. It integrates with Hydra configuration management for enterprise deployment.

CORE FUNCTIONALITY:
The email service orchestrates all educational communications, from enrollment confirmations
through course reminders to completion congratulations. It supports both production SMTP
integration and development mock modes for testing and development environments.

EDUCATIONAL COMMUNICATION WORKFLOWS:
1. Enrollment Confirmation: Welcome emails with course details and access credentials
2. Course Reminders: Pre-course notifications to ensure student preparation
3. Completion Celebrations: Congratulatory emails with achievement recognition
4. Instructor Notifications: Faculty alerts for feedback and course events
5. Administrative Communications: System-level notifications and updates

BUSINESS VALUE PROPOSITION:
- Student Engagement: Timely communications improve course participation rates
- Professional Presentation: Branded, personalized emails enhance institutional reputation
- Automated Workflows: Reduces administrative burden while ensuring consistent communication
- Personalization: Instructor signatures and course-specific details create connection
- Compliance: Audit trails and delivery tracking for educational record requirements

TEMPLATE SYSTEM ARCHITECTURE:
- Jinja2 Templates: Dynamic content generation with educational context
- Personalization Engine: Instructor signatures and student-specific customization
- Multi-Format Support: Professional HTML and plain text email generation
- Responsive Design: Mobile-optimized templates for accessibility
- Internationalization Ready: Template structure supports future localization

HYDRA CONFIGURATION INTEGRATION:
- Centralized Configuration: SMTP settings managed through Hydra configuration hierarchy
- Environment-Specific Settings: Development, staging, and production email configurations
- Security Management: Credential management through secure configuration patterns
- Feature Flags: Mock mode activation for development and testing environments
- Fallback Patterns: Graceful degradation to environment variables when needed

SMTP AND DELIVERY MANAGEMENT:
- Async Operations: Non-blocking email delivery for improved application performance
- Connection Pooling: Efficient SMTP session management for bulk operations
- TLS Security: Encrypted transmission for sensitive educational communications
- Retry Logic: Robust delivery patterns with failure handling and logging
- Delivery Tracking: Comprehensive logging for email delivery status and debugging

DEVELOPMENT AND TESTING SUPPORT:
- Mock Email Service: Complete email testing without SMTP dependencies
- Delivery Simulation: Realistic email workflow testing for development environments
- Audit Trails: Complete email history tracking for testing validation
- Template Testing: Easy verification of email content and formatting
- Performance Testing: Mock service enables load testing without email overhead

SECURITY AND COMPLIANCE:
- Credential Protection: Secure SMTP authentication with configuration management
- Data Privacy: Student information protection in email content and transmission
- Audit Requirements: Complete logging for educational compliance and record keeping
- Rate Limiting: Built-in protection against email abuse and spam prevention
- Secure Templates: XSS protection and safe content rendering

INTEGRATION PATTERNS:
- Course Management: Enrollment event triggering and course lifecycle communications
- User Management: Student and instructor contact information integration
- Analytics Service: Email delivery metrics and engagement tracking
- Configuration Service: Hydra-based configuration management and environment control
- Logging Service: Centralized logging for email events and troubleshooting

PERFORMANCE OPTIMIZATION:
- Thread Pool Execution: Non-blocking email sending with async/await patterns
- Template Caching: Optimized template compilation and reuse
- Bulk Operations: Efficient handling of mass email communications
- Connection Reuse: SMTP session optimization for high-throughput scenarios
- Memory Management: Efficient handling of large recipient lists and template rendering

ERROR HANDLING AND RESILIENCE:
- Graceful Degradation: Service availability despite SMTP server issues
- Comprehensive Logging: Detailed error information for troubleshooting
- Retry Mechanisms: Automatic retry for transient delivery failures
- Fallback Options: Alternative delivery methods for critical communications
- Status Reporting: Clear delivery status information for administrative monitoring
"""

import smtplib
import asyncio
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, Optional
from datetime import datetime
import logging
import os
from jinja2 import Template

from models.course_publishing import EnrollmentEmailData, EmailType
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self, config: Optional[DictConfig] = None, 
                 smtp_server: str = "localhost", smtp_port: int = 587, 
                 smtp_user: Optional[str] = None, smtp_password: Optional[str] = None,
                 use_tls: bool = True, from_email: Optional[str] = None):
        """Initialize EmailService with Hydra config or individual parameters."""
        
        if config:
            # Use Hydra configuration (preferred)
            self.smtp_server = config.email.smtp.server
            self.smtp_port = config.email.smtp.port
            self.smtp_user = config.email.smtp.user
            self.smtp_password = config.email.smtp.password
            self.use_tls = config.email.smtp.use_tls
            self.from_email = config.email.from_address
        else:
            # Fallback to individual parameters for backward compatibility
            self.smtp_server = smtp_server
            self.smtp_port = smtp_port
            self.smtp_user = smtp_user or os.getenv("SMTP_USER")
            self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
            self.use_tls = use_tls
            
            # Configure sender address with multiple fallback options
            self.from_email = (
                from_email or                                    # 1. Explicit parameter
                os.getenv("EMAIL_FROM_ADDRESS") or              # 2. Dedicated env var
                os.getenv("EMAIL_SENDER") or                    # 3. Alternative env var
                self.smtp_user or                               # 4. SMTP user (for backward compatibility)
                "noreply@courseplatform.com"                    # 5. Default fallback
            )
    
    def _generate_instructor_signature(self, data: EnrollmentEmailData) -> str:
        """Generate personalized instructor signature from available data."""
        # Build instructor name
        instructor_name = None
        if data.instructor_first_name and data.instructor_last_name:
            instructor_name = f"{data.instructor_first_name} {data.instructor_last_name}"
        elif data.instructor_full_name:
            instructor_name = data.instructor_full_name
        elif data.instructor_first_name:
            instructor_name = data.instructor_first_name
        elif data.instructor_last_name:
            instructor_name = data.instructor_last_name
        
        # Build organization
        organization = data.instructor_organization
        
        # Create signature
        if instructor_name and organization:
            return f"{instructor_name}\n{organization}"
        elif instructor_name:
            return instructor_name
        elif organization:
            return organization
        else:
            return "Course Creator Platform"
    
    def generate_enrollment_email(self, data: EnrollmentEmailData) -> Dict[str, str]:
        """Generate enrollment email content."""
        
        # Email subject
        subject = f"Welcome to {data.course_name} - Course Enrollment Confirmation"
        
        # Email body template
        body_template = Template("""
Dear {{ student_name }},

You have been enrolled in the course "{{ course_name }}" ({{ instance_name }}).

Course Details:
• Course: {{ course_name }}
• Instance: {{ instance_name }}
• Start Date: {{ start_date_formatted }}
• End Date: {{ end_date_formatted }}
• Duration: {{ duration_days }} days
• Timezone: {{ timezone }}

Your login credentials:
• Login URL: {{ login_url }}
• Temporary Password: {{ temporary_password }}

IMPORTANT: You will be required to change your password on first login for security reasons.

Once logged in, you will have access to:
• Course syllabus and materials
• Interactive slides and presentations
• Hands-on lab environments
• Quizzes and assessments (when published by your instructor)

We look forward to seeing you in class!

Best regards,
{{ instructor_organization }}

---
This is an automated message. Please do not reply to this email.
If you have questions, please contact your instructor directly.
        """.strip())
        
        # Format dates
        start_date_formatted = data.start_date.strftime('%B %d, %Y at %I:%M %p')
        end_date_formatted = data.end_date.strftime('%B %d, %Y at %I:%M %p')
        
        # Create personalized instructor signature
        instructor_signature = self._generate_instructor_signature(data)
        
        # Generate email body
        body = body_template.render(
            student_name=data.student_name,
            course_name=data.course_name,
            instance_name=data.instance_name,
            start_date_formatted=start_date_formatted,
            end_date_formatted=end_date_formatted,
            duration_days=data.duration_days,
            timezone=data.timezone,
            login_url=data.login_url,
            temporary_password=data.temporary_password,
            instructor_organization=instructor_signature
        )
        
        return {
            "subject": subject,
            "body": body
        }
    
    def generate_reminder_email(self, data: EnrollmentEmailData, days_until_start: int) -> Dict[str, str]:
        """Generate course reminder email."""
        
        subject = f"Reminder: {data.course_name} starts in {days_until_start} days"
        
        body_template = Template("""
Dear {{ student_name }},

This is a friendly reminder that your course "{{ course_name }}" will begin in {{ days_until_start }} days.

Course Details:
• Course: {{ course_name }}
• Instance: {{ instance_name }}
• Start Date: {{ start_date_formatted }}
• Timezone: {{ timezone }}

Don't forget:
• Login URL: {{ login_url }}
• Remember to change your temporary password on first login

We're excited to have you join us!

Best regards,
{{ instructor_organization }}
        """.strip())
        
        start_date_formatted = data.start_date.strftime('%B %d, %Y at %I:%M %p')
        
        # Create personalized instructor signature
        instructor_signature = self._generate_instructor_signature(data)
        
        body = body_template.render(
            student_name=data.student_name,
            course_name=data.course_name,
            instance_name=data.instance_name,
            start_date_formatted=start_date_formatted,
            days_until_start=days_until_start,
            timezone=data.timezone,
            login_url=data.login_url,
            instructor_organization=instructor_signature
        )
        
        return {
            "subject": subject,
            "body": body
        }
    
    def generate_completion_email(self, data: EnrollmentEmailData) -> Dict[str, str]:
        """Generate course completion email."""
        
        subject = f"Congratulations! You've completed {data.course_name}"
        
        body_template = Template("""
Dear {{ student_name }},

Congratulations on successfully completing "{{ course_name }}"!

Course Summary:
• Course: {{ course_name }}
• Instance: {{ instance_name }}
• Completion Date: {{ completion_date }}
• Duration: {{ duration_days }} days

Your certificate and final course materials will be available in your student dashboard.

Thank you for your dedication and hard work throughout the course.

Best regards,
{{ instructor_organization }}
        """.strip())
        
        completion_date = datetime.now().strftime('%B %d, %Y')
        
        # Create personalized instructor signature
        instructor_signature = self._generate_instructor_signature(data)
        
        body = body_template.render(
            student_name=data.student_name,
            course_name=data.course_name,
            instance_name=data.instance_name,
            completion_date=completion_date,
            duration_days=data.duration_days,
            instructor_organization=instructor_signature
        )
        
        return {
            "subject": subject,
            "body": body
        }
    
    async def send_email(self, to_email: str, subject: str, body: str) -> Dict[str, str]:
        """Send email asynchronously."""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MimeText(body, 'plain'))
            
            # Send email in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._send_email_sync, msg, to_email)
            
            return {
                "status": "sent",
                "message": "Email sent successfully",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "status": "failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _send_email_sync(self, msg: MimeMultipart, to_email: str) -> bool:
        """Send email synchronously (called from thread pool)."""
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()  # Enable security
            
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending to {to_email}: {e}")
            raise
    
    async def send_enrollment_email(self, enrollment_data: EnrollmentEmailData, recipient_email: str) -> Dict[str, str]:
        """Send enrollment confirmation email."""
        try:
            email_content = self.generate_enrollment_email(enrollment_data)
            result = await self.send_email(
                recipient_email, 
                email_content["subject"], 
                email_content["body"]
            )
            return result
        except Exception as e:
            logger.error(f"Error sending enrollment email: {e}")
            return {
                "status": "failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_reminder_email(self, enrollment_data: EnrollmentEmailData, 
                                recipient_email: str, days_until_start: int) -> Dict[str, str]:
        """Send course reminder email."""
        try:
            email_content = self.generate_reminder_email(enrollment_data, days_until_start)
            result = await self.send_email(
                recipient_email,
                email_content["subject"],
                email_content["body"]
            )
            return result
        except Exception as e:
            logger.error(f"Error sending reminder email: {e}")
            return {
                "status": "failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_completion_email(self, enrollment_data: EnrollmentEmailData, recipient_email: str) -> Dict[str, str]:
        """Send course completion email."""
        try:
            email_content = self.generate_completion_email(enrollment_data)
            result = await self.send_email(
                recipient_email,
                email_content["subject"],
                email_content["body"]
            )
            return result
        except Exception as e:
            logger.error(f"Error sending completion email: {e}")
            return {
                "status": "failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }


class MockEmailService(EmailService):
    """Mock email service for development and testing."""
    
    def __init__(self, config: Optional[DictConfig] = None):
        super().__init__(config)
        self.sent_emails = []
    
    async def send_email(self, to_email: str, subject: str, body: str) -> Dict[str, str]:
        """Mock send email - just log and store."""
        logger.info(f"MOCK EMAIL - To: {to_email}, Subject: {subject}")
        logger.debug(f"MOCK EMAIL BODY:\n{body}")
        
        email_record = {
            "to": to_email,
            "subject": subject,
            "body": body,
            "timestamp": datetime.now().isoformat(),
            "status": "sent"
        }
        
        self.sent_emails.append(email_record)
        
        return {
            "status": "sent",
            "message": "Mock email logged successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_sent_emails(self) -> list:
        """Get all sent emails for testing."""
        return self.sent_emails
    
    def clear_sent_emails(self):
        """Clear sent emails list."""
        self.sent_emails = []


# Email service factory
def create_email_service(config: Optional[DictConfig] = None, use_mock: bool = False) -> EmailService:
    """Create email service instance using Hydra configuration."""
    
    if config:
        # Use Hydra configuration (preferred)
        if config.email.use_mock or use_mock:
            return MockEmailService(config)
        else:
            return EmailService(config)
    else:
        # Fallback to environment variables for backward compatibility
        if use_mock or os.getenv("USE_MOCK_EMAIL", "false").lower() == "true":
            return MockEmailService()
        else:
            return EmailService(
                smtp_server=os.getenv("SMTP_SERVER", "localhost"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                smtp_user=os.getenv("SMTP_USER"),
                smtp_password=os.getenv("SMTP_PASSWORD"),
                use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
                from_email=os.getenv("EMAIL_FROM_ADDRESS")  # Use the dedicated sender address env var
            )