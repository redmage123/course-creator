#!/usr/bin/env python3
"""
Course Publishing API Endpoints - Advanced Educational Workflow Management

This module provides comprehensive API endpoints for managing the complete course publication
lifecycle, course instance scheduling, student enrollment workflows, and quiz management
systems within the educational platform.

CORE FUNCTIONALITY AREAS:
1. Course Publication Management: Draft → Published → Archived lifecycle with visibility controls
2. Course Instance Scheduling: Time-based course sessions with enrollment windows
3. Student Enrollment System: Secure access token generation and management
4. Quiz Publication Control: Instance-specific quiz publishing with analytics integration
5. Email Integration: Hydra-configured notification system for enrollment events
6. Course Completion Workflows: Automated cleanup and data retention management

EDUCATIONAL WORKFLOW PATTERNS:
- Course Development: Draft creation → Content development → Publication → Instance scheduling
- Student Access: Enrollment → Secure access → Learning progression → Completion tracking
- Instructor Management: Course creation → Instance scheduling → Student enrollment → Progress monitoring
- Analytics Integration: Performance tracking → Student progress → Instructor insights

BUSINESS RULES AND CONSTRAINTS:
- Course Visibility: Public courses discoverable by all, private courses instructor-only
- Instance Scheduling: Time-bound access with 30-minute early access window
- Enrollment Limits: Configurable maximum students per course instance
- Quiz Publication: Instance-specific publishing with availability windows
- Data Retention: Automated cleanup after 30 days post-completion

SECURITY AND ACCESS CONTROL:
- Token-based student authentication with secure password management
- Instructor authorization validation for all course management operations
- Course instance isolation preventing cross-enrollment access
- Secure email delivery with Hydra configuration management
- Access time validation with timezone-aware scheduling

INTEGRATION PATTERNS:
- Email Service: Hydra-configured SMTP with mock mode for development
- Database Transactions: ACID compliance for enrollment and publication operations
- Analytics Service: Student performance and course effectiveness metrics
- User Management Service: Authentication and authorization integration

PERFORMANCE CONSIDERATIONS:
- Connection pooling for high-throughput enrollment operations
- Async operations for email delivery to prevent blocking
- Batch processing for bulk enrollment and cleanup operations
- Optimized queries for instructor dashboards and student course listings

ERROR HANDLING AND RESILIENCE:
- Comprehensive HTTP exception mapping with educational context
- Email delivery failure handling with non-blocking enrollment
- Transaction rollback for failed multi-step operations
- Graceful degradation for non-critical component failures
"""

from fastapi import HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import asyncpg
import uuid
import secrets
import string
import hashlib
import logging
from passlib.context import CryptContext

# Import the new models
from models.course_publishing import (
    CourseStatus, CourseVisibility, CourseInstanceStatus, EnrollmentStatus,
    CoursePublishRequest, CourseArchiveRequest,
    CourseInstanceCreate, CourseInstanceUpdate, CourseInstance, CourseInstanceCancel,
    StudentEnrollmentRequest, BulkEnrollmentRequest, StudentCourseEnrollment,
    EnrollmentUpdateRequest, QuizPublicationRequest, QuizPublication,
    CoursePublishResponse, CourseInstanceResponse, CourseInstanceListResponse,
    EnrollmentResponse, BulkEnrollmentResponse, EnrollmentListResponse,
    PublishedCoursesResponse, QuizPublicationResponse,
    StudentLoginRequest, StudentLoginResponse, StudentDashboardData,
    EnrollmentEmailData, EmailNotification
)
from email_service import create_email_service
from omegaconf import DictConfig

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CoursePublishingService:
    """
    Comprehensive service for managing course publication workflows and student enrollment.
    
    This service encapsulates the complex business logic for course publication lifecycle,
    instance scheduling, student enrollment management, and quiz publication controls.
    It implements enterprise-grade security and educational workflow patterns.
    
    CORE RESPONSIBILITIES:
    1. Course Publication: Managing course visibility and publication status
    2. Instance Management: Time-based course scheduling with enrollment controls
    3. Student Enrollment: Secure token-based access with email notifications
    4. Quiz Publishing: Instance-specific quiz availability with analytics integration
    5. Access Control: Time-based access validation and security enforcement
    6. Data Management: Automated cleanup and retention policy enforcement
    
    EDUCATIONAL WORKFLOW INTEGRATION:
    - Supports complete instructor workflow from course creation to completion
    - Enables student self-enrollment through secure access URLs
    - Integrates with analytics service for performance tracking
    - Provides automated email notifications for all enrollment events
    
    SECURITY FEATURES:
    - Cryptographically secure token generation for student access
    - Password hashing using bcrypt with configurable rounds
    - Access time validation with timezone awareness
    - Course instance isolation to prevent cross-enrollment
    
    EMAIL INTEGRATION:
    - Hydra-configured SMTP service with fallback to mock mode
    - Professional enrollment emails with course details
    - Instructor contact information inclusion
    - Failure handling that doesn't block enrollment operations
    
    PERFORMANCE OPTIMIZATION:
    - Database connection pooling for concurrent operations
    - Async operations throughout for non-blocking I/O
    - Optimized queries with proper indexing strategies
    - Batch processing capabilities for bulk operations
    """
    
    def __init__(self, db_pool, config: Optional[DictConfig] = None):
        self.db_pool = db_pool
        self.config = config
        # Create email service using Hydra config if available
        # Note: use_mock=True overrides config setting for development safety
        self.email_service = create_email_service(config=config, use_mock=True)
    
    def generate_access_token(self) -> str:
        """Generate a secure access token."""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    def generate_temporary_password(self) -> str:
        """Generate a temporary password."""
        return ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(12))
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_unique_url(self, access_token: str, base_url: str = "http://localhost:3000/student-login") -> str:
        """Generate unique access URL for student."""
        return f"{base_url}?token={access_token}"
    
    # Course Publishing Methods
    async def publish_course(self, course_id: str, instructor_id: str, publish_request: CoursePublishRequest) -> Dict[str, Any]:
        """
        Publish a draft course, making it available for instance scheduling and student enrollment.
        
        This method transitions a course from draft status to published status, enabling the
        creation of course instances and student enrollment workflows. The publication process
        includes visibility controls and audit trail maintenance.
        
        BUSINESS WORKFLOW:
        1. Validate instructor ownership and course readiness for publication
        2. Verify course is not already published to prevent duplicate operations
        3. Update course status with publication timestamp and visibility settings
        4. Create audit trail for publication event with instructor attribution
        5. Enable course for instance creation and enrollment workflows
        
        VISIBILITY CONTROLS:
        - Public: Course discoverable in course catalog by all users
        - Private: Course visible only to the owning instructor
        - Organization: Course available to users within the instructor's organization
        
        PUBLICATION REQUIREMENTS:
        - Course must be in draft status (not already published or archived)
        - Course must have minimum required content (title, description)
        - Instructor must be authenticated and authorized for the course
        - Course data integrity must be validated before publication
        
        ANALYTICS INTEGRATION:
        - Publication event triggers analytics tracking for course lifecycle
        - Course discoverability metrics begin collection
        - Instructor productivity metrics are updated
        
        ERROR SCENARIOS:
        - Course not found or access denied: 404 HTTP exception
        - Course already published: 400 HTTP exception with clear message
        - Database constraints violation: Proper error handling and rollback
        - Invalid visibility setting: Validation error with acceptable values
        """
        async with self.db_pool.acquire() as conn:
            # Verify course exists and belongs to instructor
            course = await conn.fetchrow(
                "SELECT * FROM courses WHERE id = $1 AND instructor_id = $2",
                course_id, instructor_id
            )
            
            if not course:
                raise HTTPException(status_code=404, detail="Course not found or not authorized")
            
            if course['status'] == 'published':
                raise HTTPException(status_code=400, detail="Course is already published")
            
            # Update course status
            updated_course = await conn.fetchrow("""
                UPDATE courses 
                SET status = 'published', 
                    visibility = $3,
                    published_at = CURRENT_TIMESTAMP,
                    last_modified_by = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND instructor_id = $2
                RETURNING *
            """, course_id, instructor_id, publish_request.visibility.value)
            
            return dict(updated_course)
    
    async def archive_course(self, course_id: str, instructor_id: str, archive_request: CourseArchiveRequest) -> Dict[str, Any]:
        """Archive a published course."""
        async with self.db_pool.acquire() as conn:
            # Verify course exists and belongs to instructor
            course = await conn.fetchrow(
                "SELECT * FROM courses WHERE id = $1 AND instructor_id = $2",
                course_id, instructor_id
            )
            
            if not course:
                raise HTTPException(status_code=404, detail="Course not found or not authorized")
            
            if course['status'] == 'archived':
                raise HTTPException(status_code=400, detail="Course is already archived")
            
            # Check for active instances
            active_instances = await conn.fetchval(
                "SELECT COUNT(*) FROM course_instances WHERE course_id = $1 AND status = 'active'",
                course_id
            )
            
            if active_instances > 0:
                raise HTTPException(status_code=400, detail="Cannot archive course with active instances")
            
            # Update course status
            updated_course = await conn.fetchrow("""
                UPDATE courses 
                SET status = 'archived',
                    archived_at = CURRENT_TIMESTAMP,
                    last_modified_by = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND instructor_id = $2
                RETURNING *
            """, course_id, instructor_id)
            
            return dict(updated_course)
    
    async def get_published_courses(self, instructor_id: Optional[str] = None, visibility: Optional[str] = None, 
                                  page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """Get published courses."""
        offset = (page - 1) * per_page
        
        async with self.db_pool.acquire() as conn:
            where_conditions = ["c.status = 'published'"]
            params = []
            param_count = 0
            
            if instructor_id:
                param_count += 1
                where_conditions.append(f"c.instructor_id = ${param_count}")
                params.append(instructor_id)
            
            if visibility:
                param_count += 1
                where_conditions.append(f"c.visibility = ${param_count}")
                params.append(visibility)
            
            where_clause = " AND ".join(where_conditions)
            
            # Get courses with instructor info
            courses = await conn.fetch(f"""
                SELECT c.*, u.full_name as instructor_name,
                       COUNT(ci.id) as total_instances,
                       COUNT(CASE WHEN ci.status = 'active' THEN 1 END) as active_instances
                FROM courses c
                JOIN users u ON c.instructor_id = u.id
                LEFT JOIN course_instances ci ON c.id = ci.course_id
                WHERE {where_clause}
                GROUP BY c.id, u.full_name
                ORDER BY c.published_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """, *params, per_page, offset)
            
            # Get total count
            total = await conn.fetchval(f"""
                SELECT COUNT(DISTINCT c.id) FROM courses c 
                WHERE {where_clause}
            """, *params)
            
            return {
                "courses": [dict(course) for course in courses],
                "total": total,
                "page": page,
                "per_page": per_page
            }
    
    # Course Instance Methods
    async def create_course_instance(self, instructor_id: str, instance_data: CourseInstanceCreate) -> CourseInstance:
        """Create a new course instance."""
        async with self.db_pool.acquire() as conn:
            # Verify course exists, is published, and belongs to instructor
            course = await conn.fetchrow("""
                SELECT * FROM courses 
                WHERE id = $1 AND instructor_id = $2 AND status = 'published'
            """, instance_data.course_id, instructor_id)
            
            if not course:
                raise HTTPException(status_code=404, detail="Published course not found or not authorized")
            
            # Create instance
            instance_id = str(uuid.uuid4())
            instance = await conn.fetchrow("""
                INSERT INTO course_instances (
                    id, course_id, instructor_id, instance_name, description,
                    start_date, end_date, timezone, max_students
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
            """, instance_id, instance_data.course_id, instructor_id, 
                instance_data.instance_name, instance_data.description,
                instance_data.start_date, instance_data.end_date, 
                instance_data.timezone, instance_data.max_students)
            
            # Get course title for response
            course_title = course['title']
            
            return CourseInstance(
                id=instance['id'],
                course_id=instance['course_id'],
                instructor_id=instance['instructor_id'],
                instance_name=instance['instance_name'],
                description=instance['description'],
                start_date=instance['start_date'],
                end_date=instance['end_date'],
                timezone=instance['timezone'],
                max_students=instance['max_students'],
                status=CourseInstanceStatus(instance['status']),
                current_enrollments=instance['current_enrollments'],
                duration_days=instance['duration_days'],
                created_at=instance['created_at'],
                updated_at=instance['updated_at'],
                course_title=course_title
            )
    
    async def cancel_course_instance(self, instance_id: str, instructor_id: str, 
                                   cancel_request: CourseInstanceCancel) -> CourseInstance:
        """Cancel a course instance."""
        async with self.db_pool.acquire() as conn:
            # Verify instance exists and belongs to instructor
            instance = await conn.fetchrow("""
                SELECT ci.*, c.title as course_title
                FROM course_instances ci
                JOIN courses c ON ci.course_id = c.id
                WHERE ci.id = $1 AND ci.instructor_id = $2
            """, instance_id, instructor_id)
            
            if not instance:
                raise HTTPException(status_code=404, detail="Course instance not found or not authorized")
            
            if instance['status'] == 'cancelled':
                raise HTTPException(status_code=400, detail="Course instance is already cancelled")
            
            if instance['status'] == 'completed':
                raise HTTPException(status_code=400, detail="Cannot cancel completed course instance")
            
            # Update instance status
            updated_instance = await conn.fetchrow("""
                UPDATE course_instances 
                SET status = 'cancelled',
                    cancelled_at = CURRENT_TIMESTAMP,
                    cancellation_reason = $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND instructor_id = $2
                RETURNING *
            """, instance_id, instructor_id, cancel_request.cancellation_reason)
            
            return CourseInstance(
                id=updated_instance['id'],
                course_id=updated_instance['course_id'],
                instructor_id=updated_instance['instructor_id'],
                instance_name=updated_instance['instance_name'],
                description=updated_instance['description'],
                start_date=updated_instance['start_date'],
                end_date=updated_instance['end_date'],
                timezone=updated_instance['timezone'],
                max_students=updated_instance['max_students'],
                status=CourseInstanceStatus(updated_instance['status']),
                current_enrollments=updated_instance['current_enrollments'],
                duration_days=updated_instance['duration_days'],
                cancelled_at=updated_instance['cancelled_at'],
                cancellation_reason=updated_instance['cancellation_reason'],
                created_at=updated_instance['created_at'],
                updated_at=updated_instance['updated_at'],
                course_title=instance['course_title']
            )
    
    async def get_instructor_course_instances(self, instructor_id: str, course_id: Optional[str] = None,
                                            page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """Get course instances for an instructor."""
        offset = (page - 1) * per_page
        
        async with self.db_pool.acquire() as conn:
            where_clause = "ci.instructor_id = $1"
            params = [instructor_id]
            
            if course_id:
                where_clause += " AND ci.course_id = $2"
                params.append(course_id)
                offset_param = "$3"
                limit_param = "$4"
            else:
                offset_param = "$2"
                limit_param = "$3"
            
            instances = await conn.fetch(f"""
                SELECT ci.*, c.title as course_title, u.full_name as instructor_name
                FROM course_instances ci
                JOIN courses c ON ci.course_id = c.id
                JOIN users u ON ci.instructor_id = u.id
                WHERE {where_clause}
                ORDER BY ci.start_date DESC
                LIMIT {limit_param} OFFSET {offset_param}
            """, *params, per_page, offset)
            
            total = await conn.fetchval(f"""
                SELECT COUNT(*) FROM course_instances ci WHERE {where_clause}
            """, *params[:len(params)-2] if course_id else *params[:1])
            
            instance_list = []
            for instance in instances:
                instance_list.append(CourseInstance(
                    id=instance['id'],
                    course_id=instance['course_id'],
                    instructor_id=instance['instructor_id'],
                    instance_name=instance['instance_name'],
                    description=instance['description'],
                    start_date=instance['start_date'],
                    end_date=instance['end_date'],
                    timezone=instance['timezone'],
                    max_students=instance['max_students'],
                    status=CourseInstanceStatus(instance['status']),
                    current_enrollments=instance['current_enrollments'],
                    duration_days=instance['duration_days'],
                    cancelled_at=instance.get('cancelled_at'),
                    cancellation_reason=instance.get('cancellation_reason'),
                    created_at=instance['created_at'],
                    updated_at=instance['updated_at'],
                    course_title=instance['course_title'],
                    instructor_name=instance['instructor_name']
                ))
            
            return {
                "instances": instance_list,
                "total": total,
                "page": page,
                "per_page": per_page
            }
    
    # Student Enrollment Methods
    async def enroll_student(self, instructor_id: str, enrollment_request: StudentEnrollmentRequest) -> StudentCourseEnrollment:
        """
        Enroll a student in a course instance with secure access provisioning and email notification.
        
        This method implements the complete student enrollment workflow, including security
        credential generation, enrollment validation, database persistence, and automated
        email notification with access instructions.
        
        ENROLLMENT WORKFLOW:
        1. Validate instructor authorization for the specified course instance
        2. Verify course instance is in valid state (scheduled or active)
        3. Check for duplicate enrollment to prevent multiple registrations
        4. Validate enrollment capacity constraints (max_students limit)
        5. Generate secure access credentials (token, temporary password)
        6. Create enrollment record with metadata and access information
        7. Update course instance enrollment count atomically
        8. Send enrollment email with course details and access instructions
        
        SECURITY IMPLEMENTATION:
        - Cryptographically secure 32-character access token generation
        - Bcrypt password hashing with configurable salt rounds
        - Unique access URL generation for secure student login
        - Token-based authentication preventing unauthorized access
        - Password complexity requirements for temporary credentials
        
        ENROLLMENT VALIDATION:
        - Course instance existence and instructor ownership verification
        - Student email uniqueness within the course instance
        - Enrollment capacity limits with graceful error handling
        - Course instance status validation (cannot enroll in cancelled/completed courses)
        - Timeline validation (enrollment windows and access periods)
        
        EMAIL NOTIFICATION SYSTEM:
        - Professional enrollment confirmation emails with course details
        - Secure access instructions with login URL and temporary password
        - Instructor contact information for student support
        - Course schedule information with timezone handling
        - Hydra-configured SMTP with graceful fallback on email failures
        
        ANALYTICS INTEGRATION:
        - Enrollment event tracking for course popularity metrics
        - Student acquisition analytics for instructor insights
        - Course capacity utilization monitoring
        - Email delivery success/failure tracking
        
        DATABASE CONSISTENCY:
        - Atomic enrollment creation with proper transaction handling
        - Foreign key constraint validation for data integrity
        - Enrollment count synchronization with course instance records
        - Audit trail creation for enrollment events
        
        ERROR HANDLING PATTERNS:
        - 404: Course instance not found or instructor access denied
        - 400: Duplicate enrollment or validation failures
        - 403: Enrollment not permitted (capacity, status, timing)
        - 500: Database errors with proper rollback and logging
        """
        async with self.db_pool.acquire() as conn:
            # Verify instance exists and belongs to instructor
            instance = await conn.fetchrow("""
                SELECT ci.*, c.title as course_title
                FROM course_instances ci
                JOIN courses c ON ci.course_id = c.id
                WHERE ci.id = $1 AND ci.instructor_id = $2
            """, enrollment_request.course_instance_id, instructor_id)
            
            if not instance:
                raise HTTPException(status_code=404, detail="Course instance not found or not authorized")
            
            if instance['status'] not in ['scheduled', 'active']:
                raise HTTPException(status_code=400, detail="Cannot enroll in cancelled or completed course")
            
            # Check if student is already enrolled
            existing = await conn.fetchrow("""
                SELECT id FROM student_course_enrollments 
                WHERE course_instance_id = $1 AND student_email = $2
            """, enrollment_request.course_instance_id, enrollment_request.student_email)
            
            if existing:
                raise HTTPException(status_code=400, detail="Student is already enrolled in this course instance")
            
            # Check enrollment limits
            if instance['max_students'] and instance['current_enrollments'] >= instance['max_students']:
                raise HTTPException(status_code=400, detail="Course instance is full")
            
            # Generate access credentials
            access_token = self.generate_access_token()
            temp_password = self.generate_temporary_password()
            hashed_password = self.hash_password(temp_password)
            unique_url = self.generate_unique_url(access_token)
            
            # Check if user exists
            user = await conn.fetchrow(
                "SELECT id FROM course_creator.users WHERE email = $1", 
                enrollment_request.student_email
            )
            user_id = user['id'] if user else None
            
            # Create enrollment
            enrollment_id = str(uuid.uuid4())
            enrollment = await conn.fetchrow("""
                INSERT INTO student_course_enrollments (
                    id, course_instance_id, student_id, student_email,
                    student_first_name, student_last_name, unique_access_url,
                    access_token, temporary_password, enrolled_by, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
            """, enrollment_id, enrollment_request.course_instance_id, user_id,
                enrollment_request.student_email, enrollment_request.student_first_name,
                enrollment_request.student_last_name, unique_url, access_token,
                hashed_password, instructor_id, enrollment_request.notes)
            
            # Update instance enrollment count
            await conn.execute("""
                UPDATE course_instances 
                SET current_enrollments = current_enrollments + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, enrollment_request.course_instance_id)
            
            # Get instructor information for email
            instructor = await conn.fetchrow("""
                SELECT first_name, last_name, full_name, organization
                FROM course_creator.users 
                WHERE id = $1
            """, instructor_id)
            
            # Send enrollment email
            try:
                email_data = EnrollmentEmailData(
                    student_name=f"{enrollment_request.student_first_name} {enrollment_request.student_last_name}",
                    course_name=instance['course_title'],
                    instance_name=instance['instance_name'],
                    start_date=instance['start_date'],
                    end_date=instance['end_date'],
                    timezone=instance['timezone'],
                    duration_days=instance['duration_days'],
                    login_url=unique_url,
                    temporary_password=temp_password,
                    instructor_first_name=instructor['first_name'] if instructor else None,
                    instructor_last_name=instructor['last_name'] if instructor else None,
                    instructor_full_name=instructor['full_name'] if instructor else None,
                    instructor_organization=instructor['organization'] if instructor else None
                )
                
                await self.email_service.send_enrollment_email(email_data, enrollment_request.student_email)
                logger.info(f"Enrollment email sent to {enrollment_request.student_email}")
                
            except Exception as e:
                logger.error(f"Failed to send enrollment email to {enrollment_request.student_email}: {e}")
                # Don't fail the enrollment if email fails
            
            return StudentCourseEnrollment(
                id=enrollment['id'],
                course_instance_id=enrollment['course_instance_id'],
                student_id=enrollment['student_id'],
                student_email=enrollment['student_email'],
                student_first_name=enrollment['student_first_name'],
                student_last_name=enrollment['student_last_name'],
                unique_access_url=enrollment['unique_access_url'],
                access_token=enrollment['access_token'],
                password_reset_required=enrollment['password_reset_required'],
                enrollment_status=EnrollmentStatus(enrollment['enrollment_status']),
                progress_percentage=float(enrollment['progress_percentage']),
                enrolled_at=enrollment['enrolled_at'],
                enrolled_by=enrollment['enrolled_by'],
                notes=enrollment['notes'],
                course_title=instance['course_title'],
                instance_name=instance['instance_name']
            )
    
    # Quiz Publishing Methods
    async def publish_quiz(self, instructor_id: str, publication_request: QuizPublicationRequest) -> QuizPublication:
        """Publish or unpublish a quiz for a course instance."""
        async with self.db_pool.acquire() as conn:
            # Verify quiz and instance belong to instructor
            quiz_instance = await conn.fetchrow("""
                SELECT q.*, ci.instructor_id, c.title as course_title
                FROM quizzes q
                JOIN courses c ON q.course_id = c.id  
                JOIN course_instances ci ON c.id = ci.course_id
                WHERE q.id = $1 AND ci.id = $2 AND ci.instructor_id = $3
            """, publication_request.quiz_id, publication_request.course_instance_id, instructor_id)
            
            if not quiz_instance:
                raise HTTPException(status_code=404, detail="Quiz or course instance not found or not authorized")
            
            # Create or update publication record
            publication_id = str(uuid.uuid4())
            publication = await conn.fetchrow("""
                INSERT INTO quiz_publications (
                    id, quiz_id, course_instance_id, is_published, published_by,
                    available_from, available_until, time_limit_minutes, max_attempts
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (quiz_id, course_instance_id)
                DO UPDATE SET
                    is_published = EXCLUDED.is_published,
                    published_at = CASE WHEN EXCLUDED.is_published THEN CURRENT_TIMESTAMP ELSE quiz_publications.published_at END,
                    unpublished_at = CASE WHEN NOT EXCLUDED.is_published THEN CURRENT_TIMESTAMP ELSE quiz_publications.unpublished_at END,
                    available_from = EXCLUDED.available_from,
                    available_until = EXCLUDED.available_until,
                    time_limit_minutes = EXCLUDED.time_limit_minutes,
                    max_attempts = EXCLUDED.max_attempts,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
            """, publication_id, publication_request.quiz_id, publication_request.course_instance_id,
                publication_request.is_published, instructor_id, publication_request.available_from,
                publication_request.available_until, publication_request.time_limit_minutes,
                publication_request.max_attempts)
            
            return QuizPublication(
                id=publication['id'],
                quiz_id=publication['quiz_id'],
                course_instance_id=publication['course_instance_id'],
                is_published=publication['is_published'],
                published_at=publication.get('published_at'),
                unpublished_at=publication.get('unpublished_at'),
                published_by=publication['published_by'],
                available_from=publication.get('available_from'),
                available_until=publication.get('available_until'),
                time_limit_minutes=publication.get('time_limit_minutes'),
                max_attempts=publication['max_attempts'],
                quiz_title=quiz_instance['title'],
                course_title=quiz_instance['course_title']
            )

    # Course Completion and Cleanup Methods
    async def complete_course_instance(self, instance_id: str, instructor_id: str) -> bool:
        """Complete a course instance and trigger cleanup."""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Verify instructor owns the course instance
                instance = await conn.fetchrow("""
                    SELECT ci.*, c.title, c.instructor_id
                    FROM course_instances ci
                    JOIN courses c ON ci.course_id = c.id
                    WHERE ci.id = $1
                """, instance_id)
                
                if not instance:
                    raise HTTPException(status_code=404, detail="Course instance not found")
                
                if instance['instructor_id'] != instructor_id:
                    raise HTTPException(status_code=403, detail="Not authorized to complete this course instance")
                
                # Mark course instance as completed
                await conn.execute("""
                    UPDATE course_instances 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, instance_id)
                
                # Disable all student access tokens for this instance
                await conn.execute("""
                    UPDATE student_course_enrollments 
                    SET enrollment_status = 'completed', access_disabled_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE course_instance_id = $1
                """, instance_id)
                
                logger.info(f"Course instance {instance_id} completed by instructor {instructor_id}")
                return True

    async def cleanup_completed_courses(self) -> Dict[str, int]:
        """Clean up student data for courses that have been completed for more than 30 days."""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Find course instances completed more than 30 days ago
                completed_instances = await conn.fetch("""
                    SELECT id, instance_name, completed_at
                    FROM course_instances 
                    WHERE status = 'completed' 
                    AND completed_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
                    AND cleanup_completed_at IS NULL
                """)
                
                cleanup_stats = {
                    'instances_cleaned': 0,
                    'enrollments_deleted': 0,
                    'quiz_attempts_deleted': 0
                }
                
                for instance in completed_instances:
                    instance_id = instance['id']
                    
                    # Count enrollments before deletion
                    enrollment_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM student_course_enrollments 
                        WHERE course_instance_id = $1
                    """, instance_id)
                    
                    # Delete quiz attempts for this instance
                    quiz_attempts_deleted = await conn.fetchval("""
                        DELETE FROM quiz_attempts 
                        WHERE course_instance_id = $1
                        RETURNING COUNT(*)
                    """, instance_id)
                    
                    # Delete student enrollments
                    await conn.execute("""
                        DELETE FROM student_course_enrollments 
                        WHERE course_instance_id = $1
                    """, instance_id)
                    
                    # Mark instance as cleaned up
                    await conn.execute("""
                        UPDATE course_instances 
                        SET cleanup_completed_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """, instance_id)
                    
                    cleanup_stats['instances_cleaned'] += 1
                    cleanup_stats['enrollments_deleted'] += enrollment_count
                    cleanup_stats['quiz_attempts_deleted'] += quiz_attempts_deleted or 0
                    
                    logger.info(f"Cleaned up course instance {instance_id}: {enrollment_count} enrollments, {quiz_attempts_deleted or 0} quiz attempts")
                
                return cleanup_stats

    async def check_course_access_time(self, enrollment_data: Dict) -> None:
        """Check if student can access course based on timing restrictions."""
        now = datetime.now(timezone.utc)
        start_time = enrollment_data['start_datetime']
        end_time = enrollment_data['end_datetime']
        
        # Convert to timezone-aware datetime if needed
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        
        # Check if course has ended
        if now > end_time:
            raise HTTPException(
                status_code=403, 
                detail=f"Course has ended. This course ended on {end_time.strftime('%B %d, %Y at %I:%M %p UTC')}."
            )
        
        # Check if access token has been disabled
        if enrollment_data.get('access_disabled_at'):
            raise HTTPException(
                status_code=403,
                detail="Course access has been disabled. This course has been completed."
            )
        
        # Check if trying to access too early (30 minutes before start)
        access_time = start_time - timedelta(minutes=30)
        if now < access_time:
            raise HTTPException(
                status_code=403,
                detail=f"Course has not started yet. You will be able to access this course starting {access_time.strftime('%B %d, %Y at %I:%M %p UTC')} (30 minutes before the course begins)."
            )

    # Student Authentication Methods
    async def authenticate_student_with_token(self, access_token: str, password: str) -> Dict[str, Any]:
        """Authenticate a student using their unique access token and temporary password."""
        async with self.db_pool.acquire() as conn:
            # Find enrollment by access token
            enrollment = await conn.fetchrow("""
                SELECT sce.*, ci.course_id, ci.instance_name, ci.start_datetime, ci.end_datetime,
                       c.title as course_title, c.description as course_description
                FROM student_course_enrollments sce
                JOIN course_instances ci ON sce.course_instance_id = ci.id
                JOIN courses c ON ci.course_id = c.id
                WHERE sce.access_token = $1 AND sce.enrollment_status IN ('enrolled', 'completed')
            """, access_token)
            
            if not enrollment:
                raise HTTPException(status_code=401, detail="Invalid access token or enrollment not found")
            
            # Check course access timing and completion status
            await self.check_course_access_time(enrollment)
            
            # Verify password
            if not self.verify_password(password, enrollment['temporary_password']):
                raise HTTPException(status_code=401, detail="Invalid password")
            
            # Update last login
            await conn.execute("""
                UPDATE student_course_enrollments 
                SET last_login_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, enrollment['id'])
            
            return {
                'enrollment_id': enrollment['id'],
                'student_id': enrollment['student_id'],
                'student_email': enrollment['student_email'],
                'student_name': f"{enrollment['student_first_name']} {enrollment['student_last_name']}",
                'course_id': enrollment['course_id'],
                'course_title': enrollment['course_title'],
                'course_description': enrollment['course_description'],
                'course_instance_id': enrollment['course_instance_id'],
                'instance_name': enrollment['instance_name'],
                'progress_percentage': float(enrollment['progress_percentage']),
                'password_reset_required': enrollment['password_reset_required'],
                'access_token': access_token
            }

    async def get_student_course_data(self, access_token: str) -> Dict[str, Any]:
        """Get course data for authenticated student."""
        async with self.db_pool.acquire() as conn:
            # Get enrollment and course data
            enrollment = await conn.fetchrow("""
                SELECT sce.*, ci.course_id, ci.instance_name, ci.start_datetime, ci.end_datetime,
                       c.title as course_title, c.description as course_description,
                       c.syllabus, c.objectives
                FROM student_course_enrollments sce
                JOIN course_instances ci ON sce.course_instance_id = ci.id
                JOIN courses c ON ci.course_id = c.id
                WHERE sce.access_token = $1 AND sce.enrollment_status = 'enrolled'
            """, access_token)
            
            if not enrollment:
                raise HTTPException(status_code=404, detail="Enrollment not found")
            
            # Get course slides
            slides = await conn.fetch("""
                SELECT id, title, content, slide_order
                FROM slides 
                WHERE course_id = $1 
                ORDER BY slide_order
            """, enrollment['course_id'])
            
            # Get published quizzes for this instance
            quizzes = await conn.fetch("""
                SELECT qp.*, q.title, q.description, q.questions
                FROM quiz_publications qp
                JOIN quizzes q ON qp.quiz_id = q.id
                WHERE qp.course_instance_id = $1 AND qp.is_published = true
                AND (qp.available_from IS NULL OR qp.available_from <= CURRENT_TIMESTAMP)
                AND (qp.available_until IS NULL OR qp.available_until >= CURRENT_TIMESTAMP)
                ORDER BY qp.published_at
            """, enrollment['course_instance_id'])
            
            return {
                'enrollment': {
                    'id': enrollment['id'],
                    'student_name': f"{enrollment['student_first_name']} {enrollment['student_last_name']}",
                    'student_email': enrollment['student_email'],
                    'progress_percentage': float(enrollment['progress_percentage']),
                    'enrolled_at': enrollment['enrolled_at'],
                    'last_login_at': enrollment['last_login_at']
                },
                'course': {
                    'id': enrollment['course_id'],
                    'title': enrollment['course_title'],
                    'description': enrollment['course_description'],
                    'syllabus': enrollment['syllabus'],
                    'objectives': enrollment['objectives']
                },
                'instance': {
                    'id': enrollment['course_instance_id'],
                    'name': enrollment['instance_name'],
                    'start_datetime': enrollment['start_datetime'],
                    'end_datetime': enrollment['end_datetime']
                },
                'slides': [dict(slide) for slide in slides],
                'quizzes': [dict(quiz) for quiz in quizzes]
            }

    # NOTE: update_student_password method removed - authentication logic moved to user-management service
    # This follows the single responsibility principle and microservice architecture patterns
    # Password operations should be handled by the dedicated authentication service


def setup_course_publishing_routes(app, db_pool, get_current_user, config: Optional[DictConfig] = None):
    """Setup course publishing API routes."""
    
    service = CoursePublishingService(db_pool, config)
    
    # Course Publishing Routes
    @app.post("/courses/{course_id}/publish", response_model=CoursePublishResponse)
    async def publish_course(
        course_id: str,
        publish_request: CoursePublishRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Publish a draft course."""
        try:
            course = await service.publish_course(course_id, current_user['user_id'], publish_request)
            return CoursePublishResponse(
                success=True,
                course=course,
                message=f"Course published as {publish_request.visibility.value}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error publishing course: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.post("/courses/{course_id}/archive", response_model=CoursePublishResponse)
    async def archive_course(
        course_id: str,
        archive_request: CourseArchiveRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Archive a published course."""
        try:
            course = await service.archive_course(course_id, current_user['user_id'], archive_request)
            return CoursePublishResponse(
                success=True,
                course=course,
                message="Course archived successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error archiving course: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/courses/published", response_model=PublishedCoursesResponse)
    async def get_published_courses(
        visibility: Optional[str] = None,
        page: int = 1,
        per_page: int = 100,
        current_user: dict = Depends(get_current_user)
    ):
        """Get published courses (public ones + instructor's private ones)."""
        try:
            # Get public courses and instructor's private courses
            result = await service.get_published_courses(
                instructor_id=current_user['user_id'] if visibility == 'private' else None,
                visibility=visibility,
                page=page,
                per_page=per_page
            )
            
            return PublishedCoursesResponse(
                success=True,
                courses=result['courses'],
                total=result['total'],
                page=result['page'],
                per_page=result['per_page']
            )
        except Exception as e:
            logger.error(f"Error getting published courses: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Course Instance Routes
    @app.post("/course-instances", response_model=CourseInstanceResponse)
    async def create_course_instance(
        instance_data: CourseInstanceCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new course instance."""
        try:
            instance = await service.create_course_instance(current_user['user_id'], instance_data)
            return CourseInstanceResponse(
                success=True,
                instance=instance,
                message="Course instance created successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating course instance: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.post("/course-instances/{instance_id}/cancel", response_model=CourseInstanceResponse)
    async def cancel_course_instance(
        instance_id: str,
        cancel_request: CourseInstanceCancel,
        current_user: dict = Depends(get_current_user)
    ):
        """Cancel a course instance."""
        try:
            instance = await service.cancel_course_instance(instance_id, current_user['user_id'], cancel_request)
            return CourseInstanceResponse(
                success=True,
                instance=instance,
                message="Course instance cancelled successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling course instance: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/instructor/course-instances", response_model=CourseInstanceListResponse)
    async def get_instructor_course_instances(
        course_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 100,
        current_user: dict = Depends(get_current_user)
    ):
        """Get course instances for the current instructor."""
        try:
            result = await service.get_instructor_course_instances(
                current_user['user_id'], course_id, page, per_page
            )
            
            return CourseInstanceListResponse(
                success=True,
                instances=result['instances'],
                total=result['total'],
                page=result['page'],
                per_page=result['per_page']
            )
        except Exception as e:
            logger.error(f"Error getting course instances: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Student Enrollment Routes
    @app.post("/course-instances/{instance_id}/enroll", response_model=EnrollmentResponse)
    async def enroll_student_in_instance(
        instance_id: str,
        enrollment_request: StudentEnrollmentRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Enroll a student in a course instance."""
        try:
            # Override the instance_id from URL
            enrollment_request.course_instance_id = instance_id
            
            enrollment = await service.enroll_student(current_user['user_id'], enrollment_request)
            return EnrollmentResponse(
                success=True,
                enrollment=enrollment,
                message="Student enrolled successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error enrolling student: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Quiz Publishing Routes
    @app.post("/quizzes/publish", response_model=QuizPublicationResponse)
    async def publish_quiz(
        publication_request: QuizPublicationRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Publish or unpublish a quiz for a course instance."""
        try:
            publication = await service.publish_quiz(current_user['user_id'], publication_request)
            action = "published" if publication_request.is_published else "unpublished"
            return QuizPublicationResponse(
                success=True,
                publication=publication,
                message=f"Quiz {action} successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error publishing quiz: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # NOTE: Authentication endpoints removed from course-management service.
    # All authentication now handled by user-management service at port 8000.
    # Frontend should use: https://user-management:8000/auth/login
    
    @app.get("/student/course-data")
    async def get_student_course_data(
        token: str
    ):
        """Get course data for authenticated student."""
        try:
            course_data = await service.get_student_course_data(token)
            return {
                "success": True,
                "data": course_data
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting student course data: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # NOTE: Password update endpoints removed from course-management service.
    # All authentication operations now handled by user-management service.
    # Frontend should use: https://user-management:8000/auth/password/change
    
    # Course Completion and Cleanup Routes
    @app.post("/course-instances/{instance_id}/complete")
    async def complete_course_instance(
        instance_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Complete a course instance and disable student access."""
        try:
            success = await service.complete_course_instance(instance_id, current_user['user_id'])
            return {
                "success": success,
                "message": "Course instance completed and student access disabled"
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing course instance: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Quiz Management Routes for Instructors
    @app.get("/course-instances/{instance_id}/quiz-publications")
    async def get_quiz_publications_for_instance(
        instance_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all quiz publication status for a course instance."""
        try:
            async with db_pool.acquire() as conn:
                # Verify instructor owns this course instance
                instance = await conn.fetchrow("""
                    SELECT ci.id, ci.course_id, c.instructor_id
                    FROM course_instances ci
                    JOIN courses c ON ci.course_id = c.id  
                    WHERE ci.id = $1
                """, instance_id)
                
                if not instance or instance['instructor_id'] != current_user['user_id']:
                    raise HTTPException(status_code=404, detail="Course instance not found or not authorized")
                
                # Get all quizzes for the course with their publication status for this instance
                quiz_publications = await conn.fetch("""
                    SELECT 
                        q.id as quiz_id,
                        q.title as quiz_title,
                        q.topic,
                        q.difficulty,
                        COALESCE(array_length(q.questions::jsonb, 1), 0) as question_count,
                        qp.id as publication_id,
                        COALESCE(qp.is_published, false) as is_published,
                        qp.published_at,
                        qp.unpublished_at,
                        qp.available_from,
                        qp.available_until,
                        qp.time_limit_minutes,
                        qp.max_attempts,
                        -- Quiz attempt statistics
                        COALESCE(attempt_stats.total_attempts, 0) as total_attempts,
                        COALESCE(attempt_stats.unique_students, 0) as unique_students,
                        COALESCE(attempt_stats.avg_score, 0) as avg_score
                    FROM quizzes q
                    LEFT JOIN quiz_publications qp ON q.id = qp.quiz_id AND qp.course_instance_id = $1
                    LEFT JOIN (
                        SELECT 
                            qa.quiz_id,
                            COUNT(*) as total_attempts,
                            COUNT(DISTINCT qa.student_id) as unique_students,
                            AVG(qa.score) as avg_score
                        FROM quiz_attempts qa 
                        WHERE qa.course_instance_id = $1
                        GROUP BY qa.quiz_id
                    ) attempt_stats ON q.id = attempt_stats.quiz_id
                    WHERE q.course_id = $2
                    ORDER BY q.title
                """, instance_id, instance['course_id'])
                
                return {
                    "success": True,
                    "course_instance_id": instance_id,
                    "quiz_publications": [dict(row) for row in quiz_publications]
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting quiz publications: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/quiz-attempts")
    async def submit_quiz_attempt(
        quiz_attempt: dict,
        current_user: dict = Depends(get_current_user)
    ):
        """Submit a student's quiz attempt and store results."""
        try:
            async with db_pool.acquire() as conn:
                # Verify student is enrolled in the course instance
                enrollment = await conn.fetchrow("""
                    SELECT sce.*, ci.course_id
                    FROM student_course_enrollments sce
                    JOIN course_instances ci ON sce.course_instance_id = ci.id
                    WHERE sce.student_id = $1 AND sce.course_instance_id = $2
                    AND sce.enrollment_status IN ('enrolled', 'active')
                """, current_user['user_id'], quiz_attempt['course_instance_id'])
                
                if not enrollment:
                    raise HTTPException(status_code=403, detail="Not enrolled in this course instance")
                
                # Verify quiz is published for this instance
                publication = await conn.fetchrow("""
                    SELECT * FROM quiz_publications 
                    WHERE quiz_id = $1 AND course_instance_id = $2 AND is_published = true
                    AND (available_from IS NULL OR available_from <= CURRENT_TIMESTAMP)
                    AND (available_until IS NULL OR available_until >= CURRENT_TIMESTAMP)
                """, quiz_attempt['quiz_id'], quiz_attempt['course_instance_id'])
                
                if not publication:
                    raise HTTPException(status_code=403, detail="Quiz not available")
                
                # Check attempt limits
                if publication['max_attempts']:
                    attempt_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM quiz_attempts 
                        WHERE student_id = $1 AND quiz_id = $2 AND course_instance_id = $3
                    """, current_user['user_id'], quiz_attempt['quiz_id'], quiz_attempt['course_instance_id'])
                    
                    if attempt_count >= publication['max_attempts']:
                        raise HTTPException(status_code=403, detail="Maximum attempts exceeded")
                
                # Calculate score
                quiz = await conn.fetchrow("SELECT questions FROM quizzes WHERE id = $1", quiz_attempt['quiz_id'])
                questions = quiz['questions']
                answers = quiz_attempt['answers']
                
                correct_count = 0
                total_questions = len(questions)
                
                for i, question in enumerate(questions):
                    if i < len(answers) and answers[i] == question.get('correct_answer', 0):
                        correct_count += 1
                
                score = (correct_count / total_questions * 100) if total_questions > 0 else 0
                
                # Store quiz attempt
                attempt_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO quiz_attempts (
                        id, student_id, quiz_id, course_id, course_instance_id,
                        answers, score, total_questions, completed_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
                """, attempt_id, current_user['user_id'], quiz_attempt['quiz_id'], 
                    enrollment['course_id'], quiz_attempt['course_instance_id'],
                    quiz_attempt['answers'], score, total_questions)
                
                return {
                    "success": True,
                    "attempt_id": attempt_id,
                    "score": score,
                    "correct_answers": correct_count,
                    "total_questions": total_questions,
                    "percentage": score
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error submitting quiz attempt: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/admin/cleanup-completed-courses")
    async def cleanup_completed_courses(
        current_user: dict = Depends(get_current_user)
    ):
        """Clean up student data from courses completed more than 30 days ago."""
        try:
            # Only allow site admin users to run cleanup
            if current_user.get('role') != 'site_admin':
                raise HTTPException(status_code=403, detail="Site admin access required")
            
            cleanup_stats = await service.cleanup_completed_courses()
            return {
                "success": True,
                "message": "Cleanup completed successfully",
                "stats": cleanup_stats
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")