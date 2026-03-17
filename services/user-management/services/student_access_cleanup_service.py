"""
Student access cleanup service for automatic cleanup after course completion.
Following TDD approach and SOLID principles.
"""
import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StudentAccessCleanupService:
    """
    Service for automatically cleaning up student access after course completion.
    Follows Single Responsibility Principle - only handles cleanup operations.
    """
    
    def __init__(self, db_pool, notification_service):
        """
        Initialize student access cleanup service.
        
        Args:
            db_pool: Database connection pool
            notification_service: Service for sending notifications
        """
        self.db_pool = db_pool
        self.notification_service = notification_service
    
    async def identify_courses_needing_cleanup(self, grace_period_hours: int = 0) -> List[Dict]:
        """
        Identify courses that need access cleanup.
        
        Args:
            grace_period_hours: Grace period after course completion before cleanup
            
        Returns:
            List[Dict]: List of course instances needing cleanup
        """
        current_time = datetime.now()
        grace_cutoff = current_time - timedelta(hours=grace_period_hours)
        
        rows = await self.db_pool.fetch(
            """
            SELECT ci.id as course_instance_id, ci.course_id, c.title as course_title,
                   ci.start_date, ci.end_date, ci.status, 
                   ARRAY_AGG(DISTINCT e.student_id) as student_ids,
                   ARRAY_AGG(DISTINCT u.email) as student_emails
            FROM course_instances ci
            JOIN courses c ON ci.course_id = c.id
            LEFT JOIN enrollments e ON e.course_instance_id = ci.id
            LEFT JOIN users u ON e.student_id = u.id
            WHERE ci.status = 'completed' 
              AND ci.end_date < $1
              AND ci.end_date < $2
            GROUP BY ci.id, ci.course_id, c.title, ci.start_date, ci.end_date, ci.status
            ORDER BY ci.end_date ASC
            """,
            current_time, grace_cutoff
        )
        
        return [dict(row) for row in rows]
    
    async def cleanup_lab_sessions(self, course_instance_id: str) -> Dict:
        """
        Cleanup lab sessions for a completed course.
        
        Args:
            course_instance_id: ID of the course instance
            
        Returns:
            Dict: Cleanup result with count of sessions cleaned
        """
        # Get active lab sessions for this course
        rows = await self.db_pool.fetch(
            """
            SELECT session_id, student_id, status, created_at
            FROM lab_sessions
            WHERE course_instance_id = $1 AND status = 'active'
            """,
            course_instance_id
        )
        
        session_count = len(rows)
        
        if session_count > 0:
            # Terminate active lab sessions
            await self.db_pool.execute(
                """
                UPDATE lab_sessions 
                SET status = 'terminated', terminated_at = $1, termination_reason = 'course_completed'
                WHERE course_instance_id = $2 AND status = 'active'
                """,
                datetime.now(), course_instance_id
            )
        
        return {'sessions_cleaned': session_count}
    
    async def cleanup_access_tokens(self, course_instance_id: str) -> Dict:
        """
        Cleanup access tokens for a completed course.
        
        Args:
            course_instance_id: ID of the course instance
            
        Returns:
            Dict: Cleanup result with count of tokens revoked
        """
        # Get active access tokens for this course
        rows = await self.db_pool.fetch(
            """
            SELECT token_id, student_id, status
            FROM access_tokens
            WHERE course_instance_id = $1 AND status = 'active'
            """,
            course_instance_id
        )
        
        token_count = len(rows)
        
        if token_count > 0:
            # Revoke active access tokens
            await self.db_pool.execute(
                """
                UPDATE access_tokens 
                SET status = 'revoked', revoked_at = $1, revocation_reason = 'course_completed'
                WHERE course_instance_id = $2 AND status = 'active'
                """,
                datetime.now(), course_instance_id
            )
        
        return {'tokens_revoked': token_count}
    
    async def cleanup_temporary_files(self, course_instance_id: str) -> Dict:
        """
        Cleanup temporary files for a completed course.
        
        Args:
            course_instance_id: ID of the course instance
            
        Returns:
            Dict: Cleanup result with count of files cleaned
        """
        # Get temporary files for this course
        rows = await self.db_pool.fetch(
            """
            SELECT file_id, file_path, created_at
            FROM temporary_files
            WHERE course_instance_id = $1
            """,
            course_instance_id
        )
        
        file_count = len(rows)
        
        if file_count > 0:
            # Delete temporary files from database (actual file cleanup would be separate)
            await self.db_pool.execute(
                """
                DELETE FROM temporary_files 
                WHERE course_instance_id = $1
                """,
                course_instance_id
            )
        
        return {'files_cleaned': file_count}
    
    async def send_completion_notifications(self, course_instance_id: str, course_title: str) -> Dict:
        """
        Send course completion notifications to students.
        
        Args:
            course_instance_id: ID of the course instance
            course_title: Title of the course
            
        Returns:
            Dict: Notification result with count sent
        """
        # Get enrolled students
        rows = await self.db_pool.fetch(
            """
            SELECT u.email, u.full_name, e.student_id
            FROM enrollments e
            JOIN users u ON e.student_id = u.id
            WHERE e.course_instance_id = $1 AND e.status = 'enrolled'
            """,
            course_instance_id
        )
        
        notification_count = 0
        
        for row in rows:
            try:
                await self.notification_service.send_notification(
                    recipient_email=row['email'],
                    recipient_name=row['full_name'],
                    subject=f"Course Completion: {course_title}",
                    message=f"Congratulations! You have completed the course '{course_title}'. Your progress has been saved and access to course materials will be archived.",
                    notification_type='course_completion'
                )
                notification_count += 1
            except Exception as e:
                logger.error(f"Failed to send completion notification to {row['email']}: {e}")
        
        return {'notifications_sent': notification_count}
    
    async def archive_progress_data(self, course_instance_id: str) -> Dict:
        """
        Archive student progress data before cleanup.
        
        Args:
            course_instance_id: ID of the course instance
            
        Returns:
            Dict: Archive result with count of records archived
        """
        # Get progress data to archive
        rows = await self.db_pool.fetch(
            """
            SELECT e.student_id, e.course_instance_id, e.progress, e.status as enrollment_status,
                   e.enrolled_at, e.completed_at, c.title as course_title
            FROM enrollments e
            JOIN course_instances ci ON e.course_instance_id = ci.id
            JOIN courses c ON ci.course_id = c.id
            WHERE e.course_instance_id = $1
            """,
            course_instance_id
        )
        
        archive_count = len(rows)
        
        if archive_count > 0:
            # Insert into archive table
            for row in rows:
                await self.db_pool.execute(
                    """
                    INSERT INTO archived_progress 
                    (id, student_id, course_instance_id, course_title, progress, 
                     enrollment_status, enrolled_at, completed_at, archived_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    str(uuid.uuid4()), row['student_id'], row['course_instance_id'],
                    row['course_title'], row['progress'], row['enrollment_status'],
                    row['enrolled_at'], row['completed_at'], datetime.now()
                )
        
        return {'records_archived': archive_count}
    
    async def update_enrollment_status(self, course_instance_id: str, status: str) -> Dict:
        """
        Update enrollment status after cleanup.
        
        Args:
            course_instance_id: ID of the course instance
            status: New status to set
            
        Returns:
            Dict: Update result with count of enrollments updated
        """
        # Update enrollment status
        result = await self.db_pool.execute(
            """
            UPDATE enrollments 
            SET status = $1, updated_at = $2
            WHERE course_instance_id = $3
            """,
            status, datetime.now(), course_instance_id
        )
        
        # Extract the number of affected rows from the result
        # Parse result string like 'UPDATE 1' or 'UPDATE 3'
        updated_count = 0
        if result and isinstance(result, str) and result.startswith('UPDATE'):
            try:
                updated_count = int(result.split(' ')[1])
            except (IndexError, ValueError):
                updated_count = 0
        elif hasattr(result, 'count') and result.count:
            updated_count = result.count
        
        return {'enrollments_updated': updated_count}
    
    async def run_full_cleanup(self, course_instance_id: str) -> Dict:
        """
        Run the complete cleanup process for a course.
        
        Args:
            course_instance_id: ID of the course instance
            
        Returns:
            Dict: Complete cleanup results
        """
        try:
            logger.info(f"Starting full cleanup for course instance {course_instance_id}")
            
            # Get course info
            course_info = await self.db_pool.fetch_one(
                """
                SELECT ci.id, c.title, ci.end_date
                FROM course_instances ci
                JOIN courses c ON ci.course_id = c.id
                WHERE ci.id = $1
                """,
                course_instance_id
            )
            
            if not course_info:
                return {'success': False, 'error': 'Course instance not found'}
            
            course_title = course_info['title']
            
            # Run all cleanup operations
            lab_result = await self.cleanup_lab_sessions(course_instance_id)
            token_result = await self.cleanup_access_tokens(course_instance_id)
            file_result = await self.cleanup_temporary_files(course_instance_id)
            archive_result = await self.archive_progress_data(course_instance_id)
            notification_result = await self.send_completion_notifications(course_instance_id, course_title)
            status_result = await self.update_enrollment_status(course_instance_id, 'completed')
            
            # Log the cleanup operation
            await self.log_cleanup_operation(
                course_instance_id, 
                'full_cleanup',
                {
                    'lab_sessions': lab_result,
                    'access_tokens': token_result,
                    'temporary_files': file_result,
                    'archived_records': archive_result,
                    'notifications': notification_result,
                    'enrollment_updates': status_result
                }
            )
            
            logger.info(f"Completed full cleanup for course instance {course_instance_id}")
            
            return {
                'success': True,
                'course_instance_id': course_instance_id,
                'course_title': course_title,
                'lab_sessions': lab_result,
                'access_tokens': token_result,
                'temporary_files': file_result,
                'archived_records': archive_result,
                'notifications': notification_result,
                'enrollment_updates': status_result
            }
            
        except Exception as e:
            logger.error(f"Error during full cleanup for course {course_instance_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_scheduled_cleanup(self, grace_period_hours: int = 24) -> Dict:
        """
        Run scheduled cleanup job for all completed courses.
        
        Args:
            grace_period_hours: Grace period before cleanup
            
        Returns:
            Dict: Scheduled cleanup results
        """
        try:
            logger.info("Starting scheduled cleanup job")
            
            courses_needing_cleanup = await self.identify_courses_needing_cleanup(grace_period_hours)
            
            cleanup_results = []
            success_count = 0
            error_count = 0
            
            for course in courses_needing_cleanup:
                course_instance_id = course['course_instance_id']
                try:
                    result = await self.run_full_cleanup(course_instance_id)
                    cleanup_results.append(result)
                    
                    if result.get('success'):
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to cleanup course {course_instance_id}: {e}")
                    error_count += 1
                    cleanup_results.append({
                        'success': False,
                        'course_instance_id': course_instance_id,
                        'error': str(e)
                    })
            
            total_processed = len(courses_needing_cleanup)
            
            logger.info(f"Scheduled cleanup completed: {success_count} success, {error_count} errors")
            
            return {
                'success': True,
                'courses_processed': total_processed,
                'successful_cleanups': success_count,
                'failed_cleanups': error_count,
                'results': cleanup_results
            }
            
        except Exception as e:
            logger.error(f"Error during scheduled cleanup: {e}")
            return {'success': False, 'error': str(e)}
    
    async def log_cleanup_operation(self, course_instance_id: str, operation_type: str, result_data: Dict) -> None:
        """
        Log cleanup operation for audit purposes.
        
        Args:
            course_instance_id: ID of the course instance
            operation_type: Type of cleanup operation
            result_data: Results of the cleanup operation
        """
        await self.db_pool.execute(
            """
            INSERT INTO cleanup_audit_log 
            (id, course_instance_id, operation_type, result_data, performed_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            str(uuid.uuid4()), course_instance_id, operation_type, 
            str(result_data), datetime.now()
        )