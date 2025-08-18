"""
Analytics Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for analytics operations,
centralizing all SQL queries and database interactions for student activity tracking,
performance metrics, and educational analytics.

Business Context:
The Analytics service is crucial for educational effectiveness measurement and platform
optimization. It tracks student interactions, learning outcomes, performance metrics,
and engagement patterns to provide actionable insights for instructors, administrators,
and platform optimization. By centralizing all SQL operations in this DAO, we achieve:
- Single source of truth for all analytics-related database queries
- Enhanced data consistency for critical educational metrics
- Improved performance through optimized analytics query patterns
- Better maintainability and testing for analytics operations
- Clear separation between analytics business logic and data access concerns

Technical Rationale:
- Follows the Single Responsibility Principle by isolating analytics data access
- Enables comprehensive transaction support for complex analytics operations
- Provides consistent error handling using shared platform exceptions
- Supports connection pooling for optimal database resource utilization
- Facilitates analytics schema evolution without affecting business logic
- Enables easier unit testing and analytics data validation
"""

import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, median
import json
import sys
sys.path.append('/app/shared')
from exceptions import (
    CourseCreatorBaseException,
    DatabaseException,
    ValidationException,
    DataNotFoundException
)


class AnalyticsDAO:
    """
    Data Access Object for Analytics Operations
    
    This class centralizes all SQL queries and database operations for the analytics
    service, following the DAO pattern for clean architecture.
    
    Business Context:
    Provides comprehensive data access methods for educational analytics including:
    - Student activity tracking and behavioral analysis
    - Learning performance metrics and outcome measurement
    - Lab usage analytics and resource optimization data
    - Quiz performance analysis and learning assessment
    - Engagement metrics and retention analytics
    - Course effectiveness measurement and improvement insights
    
    Technical Implementation:
    - Uses asyncpg for high-performance PostgreSQL operations
    - Implements connection pooling for optimal resource usage
    - Provides transaction support for complex analytics operations
    - Includes comprehensive error handling and data validation
    - Supports prepared statements for performance optimization
    - Implements efficient aggregation queries for large datasets
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the Analytics DAO with database connection pool.
        
        Business Context:
        The DAO requires a connection pool to efficiently manage database connections
        across the analytics service's operations.
        
        Args:
            db_pool: AsyncPG connection pool for database operations
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
    
    # ================================================================
    # STUDENT ACTIVITY TRACKING QUERIES
    # ================================================================
    
    async def track_student_activity(self, activity_data: Dict[str, Any]) -> str:
        """
        Record a student activity event for analytics tracking.
        
        Business Context:
        Student activity tracking is fundamental for understanding learning patterns,
        engagement levels, and educational effectiveness. This data drives personalized
        learning recommendations, course improvements, and student success initiatives.
        
        Technical Implementation:
        - Records comprehensive activity metadata for analysis
        - Includes session context for behavioral pattern analysis
        - Captures timestamps for temporal analytics
        - Stores structured activity data for flexible querying
        
        Args:
            activity_data: Dictionary containing activity information
                - activity_id: Unique activity identifier
                - student_id: Student performing the activity
                - course_id: Course context for the activity
                - activity_type: Type of activity performed
                - activity_data: Structured activity details
                - timestamp: When the activity occurred
                - session_id: User session identifier
                - ip_address: Client IP for security analysis
                - user_agent: Browser/client information
                
        Returns:
            Activity ID for tracking and reference
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO course_creator.student_analytics 
                       (id, user_id, course_id, event_type, event_data, 
                        timestamp, session_id, ip_address)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                    activity_data['activity_id'],
                    activity_data['student_id'],
                    activity_data['course_id'],
                    activity_data['activity_type'],
                    json.dumps(activity_data['activity_data']),
                    activity_data['timestamp'],
                    activity_data['session_id'],
                    activity_data.get('ip_address')
                )
                return activity_data['activity_id']
        except Exception as e:
            raise DatabaseException(
                message="Failed to track student activity",
                error_code="ACTIVITY_TRACKING_ERROR",
                details={
                    "student_id": activity_data.get('student_id'),
                    "activity_type": activity_data.get('activity_type')
                },
                original_exception=e
            )
    
    async def get_student_activities(self, student_id: str, course_id: Optional[str] = None, 
                                   start_date: Optional[datetime] = None, 
                                   end_date: Optional[datetime] = None,
                                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve student activities with optional filtering and pagination.
        
        Business Context:
        Student activity history supports personalized learning analytics, progress
        tracking, and behavioral pattern analysis for educational optimization.
        
        Args:
            student_id: Student to get activities for
            course_id: Optional course filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of activities to return
            
        Returns:
            List of student activity records
        """
        try:
            query_conditions = ["student_id = $1"]
            query_params = [student_id]
            param_count = 1
            
            if course_id:
                param_count += 1
                query_conditions.append(f"course_id = ${param_count}")
                query_params.append(course_id)
            
            if start_date:
                param_count += 1
                query_conditions.append(f"timestamp >= ${param_count}")
                query_params.append(start_date)
            
            if end_date:
                param_count += 1
                query_conditions.append(f"timestamp <= ${param_count}")
                query_params.append(end_date)
            
            param_count += 1
            query_params.append(limit)
            
            where_clause = " AND ".join(query_conditions)
            query = f"""
                SELECT id as activity_id, user_id as student_id, course_id, event_type as activity_type, 
                       event_data as activity_data, timestamp, session_id
                FROM course_creator.student_analytics 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ${param_count}
            """
            
            async with self.db_pool.acquire() as conn:
                activities = await conn.fetch(query, *query_params)
                return [dict(activity) for activity in activities]
        except Exception as e:
            raise DatabaseException(
                message="Failed to retrieve student activities",
                error_code="ACTIVITY_QUERY_ERROR",
                details={"student_id": student_id, "course_id": course_id},
                original_exception=e
            )
    
    # ================================================================
    # PERFORMANCE ANALYTICS QUERIES
    # ================================================================
    
    async def track_quiz_performance(self, performance_data: Dict[str, Any]) -> str:
        """
        Record quiz performance metrics for learning analytics.
        
        Business Context:
        Quiz performance tracking enables assessment effectiveness analysis,
        learning outcome measurement, and personalized feedback generation
        for continuous educational improvement.
        
        Args:
            performance_data: Dictionary containing quiz performance information
                - performance_id: Unique performance record identifier
                - student_id: Student who took the quiz
                - quiz_id: Quiz identifier
                - course_id: Course context
                - score: Numeric score achieved
                - max_score: Maximum possible score
                - time_taken: Time spent on quiz (seconds)
                - answers: Student answer details
                - completed_at: Quiz completion timestamp
                
        Returns:
            Performance record ID for tracking
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO course_creator.quiz_attempts 
                       (id, user_id, quiz_id, course_instance_id, score, total_questions,
                        time_taken, answers, completed_at, attempt_number, correct_answers)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 1, $10)""",
                    performance_data['performance_id'],
                    performance_data['student_id'],
                    performance_data['quiz_id'],
                    performance_data['course_id'],
                    performance_data['score'],
                    performance_data['max_score'],
                    performance_data['time_taken'],
                    json.dumps(performance_data['answers']),
                    performance_data['completed_at'],
                    performance_data.get('correct_answers', 0)
                )
                return performance_data['performance_id']
        except Exception as e:
            raise DatabaseException(
                message="Failed to track quiz performance",
                error_code="QUIZ_PERFORMANCE_ERROR",
                details={
                    "student_id": performance_data.get('student_id'),
                    "quiz_id": performance_data.get('quiz_id')
                },
                original_exception=e
            )
    
    async def get_student_quiz_analytics(self, student_id: str, course_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive quiz analytics for a student.
        
        Business Context:
        Student quiz analytics provide insights into learning progress, strengths,
        weaknesses, and areas needing additional support for personalized education.
        
        Args:
            student_id: Student to analyze
            course_id: Optional course filter
            
        Returns:
            Dictionary containing comprehensive quiz analytics
        """
        try:
            async with self.db_pool.acquire() as conn:
                conditions = ["student_id = $1"]
                params = [student_id]
                
                if course_id:
                    conditions.append("course_id = $2")
                    params.append(course_id)
                
                where_clause = " AND ".join(conditions)
                
                # Get quiz performance statistics
                stats = await conn.fetchrow(f"""
                    SELECT 
                        COUNT(*) as total_quizzes,
                        AVG(score::float / total_questions) as avg_percentage,
                        MAX(score::float / total_questions) as best_percentage,
                        MIN(score::float / total_questions) as worst_percentage,
                        AVG(time_taken) as avg_time_taken,
                        SUM(CASE WHEN score::float / total_questions >= 0.8 THEN 1 ELSE 0 END) as high_scores
                    FROM course_creator.quiz_attempts 
                    WHERE {where_clause}
                """, *params)
                
                # Get recent performance trend (last 10 quizzes)
                recent_performance = await conn.fetch(f"""
                    SELECT score::float / total_questions as percentage, completed_at
                    FROM course_creator.quiz_attempts 
                    WHERE {where_clause}
                    ORDER BY completed_at DESC 
                    LIMIT 10
                """, *params)
                
                return {
                    "total_quizzes": stats['total_quizzes'] or 0,
                    "average_percentage": float(stats['avg_percentage'] or 0),
                    "best_percentage": float(stats['best_percentage'] or 0),
                    "worst_percentage": float(stats['worst_percentage'] or 0),
                    "average_time_minutes": int((stats['avg_time_taken'] or 0) / 60),
                    "high_score_count": stats['high_scores'] or 0,
                    "recent_trend": [
                        {"percentage": float(row['percentage']), "date": row['completed_at']}
                        for row in recent_performance
                    ]
                }
        except Exception as e:
            raise DatabaseException(
                message="Failed to calculate student quiz analytics",
                error_code="QUIZ_ANALYTICS_ERROR",
                details={"student_id": student_id, "course_id": course_id},
                original_exception=e
            )
    
    # ================================================================
    # LAB USAGE ANALYTICS QUERIES
    # ================================================================
    
    async def track_lab_usage(self, lab_usage_data: Dict[str, Any]) -> str:
        """
        Record lab environment usage metrics for resource optimization.
        
        Business Context:
        Lab usage tracking enables infrastructure optimization, resource allocation
        decisions, and understanding of hands-on learning engagement patterns.
        
        Args:
            lab_usage_data: Dictionary containing lab usage information
                - usage_id: Unique usage record identifier
                - student_id: Student using the lab
                - lab_id: Lab environment identifier
                - course_id: Course context
                - created_at: Lab session start time
                - end_time: Lab session end time
                - activities_performed: List of activities in the lab
                - resources_used: System resources utilized
                
        Returns:
            Usage record ID for tracking
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO course_creator.lab_sessions 
                       (id, user_id, course_id, container_id, container_name, status,
                        created_at, updated_at, ended_at, port_mapping, environment_config)
                       VALUES ($1, $2, $3, $4, $5, 'completed', $6, $7, $8, $9, $10)""",
                    lab_usage_data['usage_id'],
                    lab_usage_data['student_id'],
                    lab_usage_data['course_id'],
                    lab_usage_data.get('lab_id', 'unknown'),
                    f"lab-{lab_usage_data['student_id'][:8]}",
                    lab_usage_data['created_at'],
                    lab_usage_data['end_time'], 
                    lab_usage_data['end_time'],
                    json.dumps(lab_usage_data.get('port_mappings', {})),
                    json.dumps(lab_usage_data.get('environment_config', {}))
                )
                return lab_usage_data['usage_id']
        except Exception as e:
            raise DatabaseException(
                message="Failed to track lab usage",
                error_code="LAB_USAGE_TRACKING_ERROR",
                details={
                    "student_id": lab_usage_data.get('student_id'),
                    "lab_id": lab_usage_data.get('lab_id')
                },
                original_exception=e
            )
    
    async def get_lab_usage_analytics(self, lab_id: Optional[str] = None, 
                                    course_id: Optional[str] = None,
                                    days: int = 30) -> Dict[str, Any]:
        """
        Calculate lab usage analytics for resource optimization.
        
        Business Context:
        Lab usage analytics support infrastructure planning, cost optimization,
        and understanding of hands-on learning patterns for better resource allocation.
        
        Args:
            lab_id: Optional specific lab to analyze
            course_id: Optional course context filter
            days: Number of days to analyze (default 30)
            
        Returns:
            Dictionary containing lab usage analytics
        """
        try:
            conditions = ["created_at >= $1"]
            params = [datetime.utcnow() - timedelta(days=days)]
            param_count = 1
            
            if lab_id:
                param_count += 1
                conditions.append(f"lab_id = ${param_count}")
                params.append(lab_id)
            
            if course_id:
                param_count += 1
                conditions.append(f"course_id = ${param_count}")
                params.append(course_id)
            
            where_clause = " AND ".join(conditions)
            
            async with self.db_pool.acquire() as conn:
                # Get usage statistics
                stats = await conn.fetchrow(f"""
                    SELECT 
                        COUNT(*) as total_sessions,
                        COUNT(DISTINCT user_id) as unique_users,
                        AVG(EXTRACT(EPOCH FROM (ended_at - created_at))/60) as avg_session_duration,
                        MAX(EXTRACT(EPOCH FROM (ended_at - created_at))/60) as max_session_duration,
                        SUM(EXTRACT(EPOCH FROM (ended_at - created_at))/60) as total_usage_minutes
                    FROM course_creator.lab_sessions 
                    WHERE {where_clause} AND ended_at IS NOT NULL
                """, *params)
                
                # Get peak usage hours
                peak_hours = await conn.fetch(f"""
                    SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as session_count
                    FROM course_creator.lab_sessions 
                    WHERE {where_clause}
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY session_count DESC
                    LIMIT 5
                """, *params)
                
                # Get daily usage trend
                daily_usage = await conn.fetch(f"""
                    SELECT DATE(created_at) as usage_date, 
                           COUNT(*) as sessions, 
                           SUM(duration_minutes) as total_minutes
                    FROM course_creator.lab_sessions 
                    WHERE {where_clause}
                    GROUP BY DATE(created_at)
                    ORDER BY usage_date
                """, *params)
                
                return {
                    "total_sessions": stats['total_sessions'] or 0,
                    "unique_users": stats['unique_users'] or 0,
                    "average_session_minutes": int(stats['avg_session_duration'] or 0),
                    "max_session_minutes": int(stats['max_session_duration'] or 0),
                    "total_usage_hours": int((stats['total_usage_minutes'] or 0) / 60),
                    "peak_usage_hours": [
                        {"hour": int(row['hour']), "sessions": row['session_count']}
                        for row in peak_hours
                    ],
                    "daily_trend": [
                        {
                            "date": row['usage_date'],
                            "sessions": row['sessions'],
                            "hours_used": int(row['total_minutes'] / 60)
                        }
                        for row in daily_usage
                    ]
                }
        except Exception as e:
            raise DatabaseException(
                message="Failed to calculate lab usage analytics",
                error_code="LAB_ANALYTICS_ERROR",
                details={"lab_id": lab_id, "course_id": course_id, "days": days},
                original_exception=e
            )
    
    # ================================================================
    # LEARNING PROGRESS ANALYTICS QUERIES
    # ================================================================
    
    async def update_student_progress(self, progress_data: Dict[str, Any]) -> str:
        """
        Update or create student progress record for learning analytics.
        
        Business Context:
        Student progress tracking enables personalized learning paths, early
        intervention for struggling students, and measurement of educational effectiveness.
        
        Args:
            progress_data: Dictionary containing progress information
                - student_id: Student making progress
                - course_id: Course context
                - module_id: Specific module or section
                - progress_percentage: Completion percentage (0-100)
                - time_spent: Time invested in learning
                - last_accessed: Last interaction timestamp
                - completion_status: Current completion state
                
        Returns:
            Progress record ID for tracking
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Use UPSERT pattern for progress tracking
                progress_id = await conn.fetchval(
                    """INSERT INTO course_creator.student_course_enrollments 
                       (student_id, course_instance_id, enrollment_date, status, progress_percentage, completion_date)
                       VALUES ($1, $2, $3, 'active', $4, $5)
                       ON CONFLICT (student_id, course_instance_id) 
                       DO UPDATE SET 
                           progress_percentage = EXCLUDED.progress_percentage,
                           completion_date = EXCLUDED.completion_date,
                           status = EXCLUDED.status
                       RETURNING id""",
                    progress_data['student_id'],
                    progress_data['course_id'],
                    datetime.utcnow(),
                    progress_data['progress_percentage'],
                    progress_data.get('completion_date')
                )
                return str(progress_id)
        except Exception as e:
            raise DatabaseException(
                message="Failed to update student progress",
                error_code="PROGRESS_UPDATE_ERROR",
                details=progress_data,
                original_exception=e
            )
    
    async def get_student_progress_analytics(self, student_id: str, course_id: str) -> Dict[str, Any]:
        """
        Calculate comprehensive progress analytics for a student in a course.
        
        Business Context:
        Progress analytics enable personalized learning recommendations, identification
        of learning gaps, and measurement of educational effectiveness over time.
        
        Args:
            student_id: Student to analyze
            course_id: Course to analyze progress for
            
        Returns:
            Dictionary containing detailed progress analytics
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get overall progress statistics
                progress_stats = await conn.fetchrow(
                    """SELECT 
                        COUNT(*) as modules_started,
                        COUNT(CASE WHEN completion_status = 'completed' THEN 1 END) as modules_completed,
                        AVG(progress_percentage) as overall_progress,
                        SUM(time_spent) as total_time_minutes,
                        MAX(last_accessed) as last_activity
                       FROM course_creator.student_course_enrollments 
                       WHERE student_id = $1 AND course_id = $2""",
                    student_id, course_id
                )
                
                # Get module-level progress details
                module_progress = await conn.fetch(
                    """SELECT module_id, progress_percentage, completion_status, 
                              time_spent, last_accessed
                       FROM course_creator.student_course_enrollments 
                       WHERE student_id = $1 AND course_id = $2
                       ORDER BY last_accessed DESC""",
                    student_id, course_id
                )
                
                return {
                    "modules_started": progress_stats['modules_started'] or 0,
                    "modules_completed": progress_stats['modules_completed'] or 0,
                    "overall_progress_percentage": float(progress_stats['overall_progress'] or 0),
                    "total_time_hours": int((progress_stats['total_time_minutes'] or 0) / 60),
                    "last_activity": progress_stats['last_activity'],
                    "module_details": [
                        {
                            "module_id": row['module_id'],
                            "progress": row['progress_percentage'],
                            "status": row['completion_status'],
                            "time_spent_minutes": row['time_spent'],
                            "last_accessed": row['last_accessed']
                        }
                        for row in module_progress
                    ]
                }
        except Exception as e:
            raise DatabaseException(
                message="Failed to calculate student progress analytics",
                error_code="PROGRESS_ANALYTICS_ERROR",
                details={"student_id": student_id, "course_id": course_id},
                original_exception=e
            )
    
    # ================================================================
    # ENGAGEMENT AND RETENTION ANALYTICS
    # ================================================================
    
    async def calculate_engagement_metrics(self, course_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculate student engagement metrics for a course.
        
        Business Context:
        Engagement metrics help identify course effectiveness, student satisfaction,
        and areas needing instructional improvement for better learning outcomes.
        
        Args:
            course_id: Course to analyze engagement for
            days: Time period for analysis (default 30 days)
            
        Returns:
            Dictionary containing comprehensive engagement metrics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            async with self.db_pool.acquire() as conn:
                # Calculate activity-based engagement
                engagement_stats = await conn.fetchrow(
                    """SELECT 
                        COUNT(DISTINCT student_id) as active_students,
                        COUNT(*) as total_activities,
                        AVG(daily_activity.activity_count) as avg_daily_activities
                       FROM (
                           SELECT user_id as student_id, DATE(timestamp) as activity_date, 
                                  COUNT(*) as activity_count
                           FROM course_creator.student_analytics 
                           WHERE course_id = $1 AND timestamp >= $2
                           GROUP BY user_id, DATE(timestamp)
                       ) daily_activity""",
                    course_id, start_date
                )
                
                # Calculate session duration patterns
                session_stats = await conn.fetchrow(
                    """SELECT 
                        AVG(duration_minutes) as avg_session_duration,
                        MAX(duration_minutes) as max_session_duration,
                        COUNT(*) as total_sessions
                       FROM course_creator.lab_sessions 
                       WHERE course_id = $1 AND created_at >= $2""",
                    course_id, start_date
                )
                
                # Get activity type distribution
                activity_distribution = await conn.fetch(
                    """SELECT event_type as activity_type, COUNT(*) as count
                       FROM course_creator.student_analytics 
                       WHERE course_id = $1 AND timestamp >= $2
                       GROUP BY event_type
                       ORDER BY count DESC""",
                    course_id, start_date
                )
                
                return {
                    "active_students": engagement_stats['active_students'] or 0,
                    "total_activities": engagement_stats['total_activities'] or 0,
                    "average_daily_activities": float(engagement_stats['avg_daily_activities'] or 0),
                    "average_session_minutes": int(session_stats['avg_session_duration'] or 0),
                    "max_session_minutes": int(session_stats['max_session_duration'] or 0),
                    "total_lab_sessions": session_stats['total_sessions'] or 0,
                    "activity_breakdown": [
                        {"type": row['activity_type'], "count": row['count']}
                        for row in activity_distribution
                    ]
                }
        except Exception as e:
            raise DatabaseException(
                message="Failed to calculate engagement metrics",
                error_code="ENGAGEMENT_ANALYTICS_ERROR",
                details={"course_id": course_id, "days": days},
                original_exception=e
            )