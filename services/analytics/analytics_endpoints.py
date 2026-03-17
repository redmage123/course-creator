"""
Analytics API Endpoints
Provides endpoints for tracking student activities, generating analytics, and creating reports
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, Depends, Query, Request, BackgroundTasks
import asyncpg
import json
from statistics import mean, median
import asyncio

from main import (
    app, db_pool, get_current_user, logger,
    StudentActivity, LabUsageMetrics, QuizPerformance, 
    StudentProgress, LearningAnalytics, AnalyticsRequest, AnalyticsResponse
)

# Activity Tracking Endpoints

@app.post("/activities/track", response_model=Dict)
async def track_student_activity(
    activity: StudentActivity,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Track a student activity"""
    try:
        # Extract request metadata
        activity.ip_address = request.client.host
        activity.user_agent = request.headers.get("user-agent")
        
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO student_activities 
                (activity_id, student_id, course_id, activity_type, activity_data, 
                 timestamp, session_id, ip_address, user_agent)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
            activity.activity_id, activity.student_id, activity.course_id,
            activity.activity_type, json.dumps(activity.activity_data),
            activity.timestamp, activity.session_id, 
            activity.ip_address, activity.user_agent)
        
        logger.info(f"Tracked activity: {activity.activity_type} for student {activity.student_id}")
        
        return {
            "message": "Activity tracked successfully",
            "activity_id": activity.activity_id,
            "timestamp": activity.timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to track activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track activity")

@app.post("/activities/batch", response_model=Dict)
async def track_batch_activities(
    activities: List[StudentActivity],
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Track multiple student activities in batch"""
    try:
        async with db_pool.acquire() as conn:
            # Prepare batch insert
            values = []
            for activity in activities:
                activity.ip_address = request.client.host
                activity.user_agent = request.headers.get("user-agent")
                
                values.extend([
                    activity.activity_id, activity.student_id, activity.course_id,
                    activity.activity_type, json.dumps(activity.activity_data),
                    activity.timestamp, activity.session_id,
                    activity.ip_address, activity.user_agent
                ])
            
            # Batch insert
            placeholders = ",".join([f"(${i*9+1}, ${i*9+2}, ${i*9+3}, ${i*9+4}, ${i*9+5}, ${i*9+6}, ${i*9+7}, ${i*9+8}, ${i*9+9})" 
                                   for i in range(len(activities))])
            
            query = f"""
                INSERT INTO student_activities 
                (activity_id, student_id, course_id, activity_type, activity_data, 
                 timestamp, session_id, ip_address, user_agent)
                VALUES {placeholders}
            """
            
            await conn.execute(query, *values)
        
        logger.info(f"Tracked {len(activities)} activities in batch")
        
        return {
            "message": f"Tracked {len(activities)} activities successfully",
            "activities_tracked": len(activities)
        }
        
    except Exception as e:
        logger.error(f"Failed to track batch activities: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track activities")

# Lab Usage Tracking

@app.post("/lab-usage/track", response_model=Dict)
async def track_lab_usage(
    lab_usage: LabUsageMetrics,
    current_user: dict = Depends(get_current_user)
):
    """Track lab usage metrics"""
    try:
        # Calculate duration if session ended
        if lab_usage.session_end:
            duration = lab_usage.session_end - lab_usage.session_start
            lab_usage.duration_minutes = int(duration.total_seconds() / 60)
        
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO lab_usage_metrics 
                (metric_id, student_id, course_id, lab_id, session_start, session_end,
                 duration_minutes, actions_performed, code_executions, errors_encountered,
                 completion_status, final_code)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (metric_id) DO UPDATE SET
                    session_end = EXCLUDED.session_end,
                    duration_minutes = EXCLUDED.duration_minutes,
                    actions_performed = EXCLUDED.actions_performed,
                    code_executions = EXCLUDED.code_executions,
                    errors_encountered = EXCLUDED.errors_encountered,
                    completion_status = EXCLUDED.completion_status,
                    final_code = EXCLUDED.final_code
            """,
            lab_usage.metric_id, lab_usage.student_id, lab_usage.course_id,
            lab_usage.lab_id, lab_usage.session_start, lab_usage.session_end,
            lab_usage.duration_minutes, lab_usage.actions_performed,
            lab_usage.code_executions, lab_usage.errors_encountered,
            lab_usage.completion_status, lab_usage.final_code)
        
        logger.info(f"Tracked lab usage for student {lab_usage.student_id}, lab {lab_usage.lab_id}")
        
        return {
            "message": "Lab usage tracked successfully",
            "metric_id": lab_usage.metric_id
        }
        
    except Exception as e:
        logger.error(f"Failed to track lab usage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track lab usage")

# Quiz Performance Tracking

@app.post("/quiz-performance/track", response_model=Dict)
async def track_quiz_performance(
    quiz_performance: QuizPerformance,
    current_user: dict = Depends(get_current_user)
):
    """Track quiz performance metrics"""
    try:
        # Calculate duration and score if quiz completed
        if quiz_performance.end_time and quiz_performance.start_time:
            duration = quiz_performance.end_time - quiz_performance.start_time
            quiz_performance.duration_minutes = int(duration.total_seconds() / 60)
        
        if quiz_performance.questions_total > 0:
            quiz_performance.score_percentage = (
                quiz_performance.questions_correct / quiz_performance.questions_total
            ) * 100
        
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO quiz_performance 
                (performance_id, student_id, course_id, quiz_id, attempt_number,
                 start_time, end_time, duration_minutes, questions_total,
                 questions_answered, questions_correct, score_percentage,
                 answers, time_per_question, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (performance_id) DO UPDATE SET
                    end_time = EXCLUDED.end_time,
                    duration_minutes = EXCLUDED.duration_minutes,
                    questions_answered = EXCLUDED.questions_answered,
                    questions_correct = EXCLUDED.questions_correct,
                    score_percentage = EXCLUDED.score_percentage,
                    answers = EXCLUDED.answers,
                    time_per_question = EXCLUDED.time_per_question,
                    status = EXCLUDED.status
            """,
            quiz_performance.performance_id, quiz_performance.student_id,
            quiz_performance.course_id, quiz_performance.quiz_id,
            quiz_performance.attempt_number, quiz_performance.start_time,
            quiz_performance.end_time, quiz_performance.duration_minutes,
            quiz_performance.questions_total, quiz_performance.questions_answered,
            quiz_performance.questions_correct, quiz_performance.score_percentage,
            json.dumps(quiz_performance.answers),
            json.dumps(quiz_performance.time_per_question),
            quiz_performance.status)
        
        logger.info(f"Tracked quiz performance for student {quiz_performance.student_id}")
        
        return {
            "message": "Quiz performance tracked successfully",
            "performance_id": quiz_performance.performance_id,
            "score_percentage": quiz_performance.score_percentage
        }
        
    except Exception as e:
        logger.error(f"Failed to track quiz performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track quiz performance")

# Student Progress Tracking

@app.post("/progress/update", response_model=Dict)
async def update_student_progress(
    progress: StudentProgress,
    current_user: dict = Depends(get_current_user)
):
    """Update student progress for a content item"""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO student_progress 
                (progress_id, student_id, course_id, content_item_id, content_type,
                 status, progress_percentage, time_spent_minutes, last_accessed,
                 completion_date, mastery_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (student_id, course_id, content_item_id) 
                DO UPDATE SET
                    status = EXCLUDED.status,
                    progress_percentage = EXCLUDED.progress_percentage,
                    time_spent_minutes = student_progress.time_spent_minutes + EXCLUDED.time_spent_minutes,
                    last_accessed = EXCLUDED.last_accessed,
                    completion_date = EXCLUDED.completion_date,
                    mastery_score = EXCLUDED.mastery_score,
                    updated_at = NOW()
            """,
            progress.progress_id, progress.student_id, progress.course_id,
            progress.content_item_id, progress.content_type, progress.status,
            progress.progress_percentage, progress.time_spent_minutes,
            progress.last_accessed, progress.completion_date, progress.mastery_score)
        
        logger.info(f"Updated progress for student {progress.student_id}, content {progress.content_item_id}")
        
        return {
            "message": "Progress updated successfully",
            "progress_id": progress.progress_id,
            "progress_percentage": progress.progress_percentage
        }
        
    except Exception as e:
        logger.error(f"Failed to update progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update progress")

# Analytics Generation Endpoints

@app.get("/analytics/student/{student_id}", response_model=Dict)
async def get_student_analytics(
    student_id: str,
    course_id: Optional[str] = Query(None),
    days_back: int = Query(30, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive analytics for a student"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        async with db_pool.acquire() as conn:
            # Get student activities
            activities_query = """
                SELECT activity_type, COUNT(*) as count, 
                       DATE_TRUNC('day', timestamp) as day
                FROM student_activities 
                WHERE student_id = $1 
                AND timestamp >= $2 AND timestamp <= $3
            """
            activities_params = [student_id, start_date, end_date]
            
            if course_id:
                activities_query += " AND course_id = $4"
                activities_params.append(course_id)
            
            activities_query += " GROUP BY activity_type, DATE_TRUNC('day', timestamp) ORDER BY day"
            
            activities = await conn.fetch(activities_query, *activities_params)
            
            # Get lab usage metrics
            lab_query = """
                SELECT AVG(duration_minutes) as avg_duration,
                       SUM(actions_performed) as total_actions,
                       COUNT(*) as total_sessions,
                       AVG(code_executions) as avg_executions,
                       AVG(errors_encountered) as avg_errors
                FROM lab_usage_metrics 
                WHERE student_id = $1 
                AND session_start >= $2 AND session_start <= $3
            """
            lab_params = [student_id, start_date, end_date]
            
            if course_id:
                lab_query += " AND course_id = $4"
                lab_params.append(course_id)
            
            lab_metrics = await conn.fetchrow(lab_query, *lab_params)
            
            # Get quiz performance
            quiz_query = """
                SELECT AVG(score_percentage) as avg_score,
                       COUNT(*) as total_quizzes,
                       AVG(duration_minutes) as avg_duration,
                       COUNT(CASE WHEN score_percentage >= 80 THEN 1 END) as passed_quizzes
                FROM quiz_performance 
                WHERE student_id = $1 
                AND start_time >= $2 AND start_time <= $3
                AND status = 'completed'
            """
            quiz_params = [student_id, start_date, end_date]
            
            if course_id:
                quiz_query += " AND course_id = $4"
                quiz_params.append(course_id)
            
            quiz_metrics = await conn.fetchrow(quiz_query, *quiz_params)
            
            # Get progress summary
            progress_query = """
                SELECT content_type, status, COUNT(*) as count,
                       AVG(progress_percentage) as avg_progress,
                       SUM(time_spent_minutes) as total_time
                FROM student_progress 
                WHERE student_id = $1
            """
            progress_params = [student_id]
            
            if course_id:
                progress_query += " AND course_id = $2"
                progress_params.append(course_id)
            
            progress_query += " GROUP BY content_type, status"
            
            progress_data = await conn.fetch(progress_query, *progress_params)
        
        # Process and structure the analytics data
        analytics_data = {
            "student_id": student_id,
            "course_id": course_id,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_back
            },
            "activity_summary": {
                "total_activities": sum(row['count'] for row in activities),
                "daily_activities": [
                    {
                        "date": row['day'].isoformat(),
                        "activity_type": row['activity_type'],
                        "count": row['count']
                    } for row in activities
                ]
            },
            "lab_metrics": {
                "average_session_duration": float(lab_metrics['avg_duration'] or 0),
                "total_actions": int(lab_metrics['total_actions'] or 0),
                "total_sessions": int(lab_metrics['total_sessions'] or 0),
                "average_code_executions": float(lab_metrics['avg_executions'] or 0),
                "average_errors": float(lab_metrics['avg_errors'] or 0)
            },
            "quiz_performance": {
                "average_score": float(quiz_metrics['avg_score'] or 0),
                "total_quizzes": int(quiz_metrics['total_quizzes'] or 0),
                "average_duration": float(quiz_metrics['avg_duration'] or 0),
                "passed_quizzes": int(quiz_metrics['passed_quizzes'] or 0),
                "pass_rate": (int(quiz_metrics['passed_quizzes'] or 0) / max(int(quiz_metrics['total_quizzes'] or 1), 1)) * 100
            },
            "progress_summary": {
                "by_content_type": [
                    {
                        "content_type": row['content_type'],
                        "status": row['status'],
                        "count": row['count'],
                        "average_progress": float(row['avg_progress']),
                        "total_time_minutes": int(row['total_time'])
                    } for row in progress_data
                ]
            }
        }
        
        # Calculate engagement score
        engagement_score = calculate_engagement_score(analytics_data)
        analytics_data["engagement_score"] = engagement_score
        
        # Generate recommendations
        recommendations = generate_recommendations(analytics_data)
        analytics_data["recommendations"] = recommendations
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"Failed to get student analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")

@app.get("/analytics/course/{course_id}", response_model=Dict)
async def get_course_analytics(
    course_id: str,
    days_back: int = Query(30, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive analytics for a course"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        async with db_pool.acquire() as conn:
            # Get enrolled students count
            students_query = """
                SELECT COUNT(DISTINCT student_id) as student_count
                FROM student_activities 
                WHERE course_id = $1
            """
            student_count = await conn.fetchval(students_query, course_id)
            
            # Get activity metrics
            activity_metrics = await conn.fetch("""
                SELECT student_id, activity_type, COUNT(*) as count
                FROM student_activities 
                WHERE course_id = $1 
                AND timestamp >= $2 AND timestamp <= $3
                GROUP BY student_id, activity_type
            """, course_id, start_date, end_date)
            
            # Get lab completion rates
            lab_completion = await conn.fetch("""
                SELECT completion_status, COUNT(*) as count,
                       AVG(duration_minutes) as avg_duration
                FROM lab_usage_metrics 
                WHERE course_id = $1 
                AND session_start >= $2 AND session_start <= $3
                GROUP BY completion_status
            """, course_id, start_date, end_date)
            
            # Get quiz statistics
            quiz_stats = await conn.fetchrow("""
                SELECT AVG(score_percentage) as avg_score,
                       STDDEV(score_percentage) as score_stddev,
                       COUNT(DISTINCT student_id) as students_attempted,
                       COUNT(*) as total_attempts
                FROM quiz_performance 
                WHERE course_id = $1 
                AND start_time >= $2 AND start_time <= $3
                AND status = 'completed'
            """, course_id, start_date, end_date)
            
            # Get progress distribution
            progress_dist = await conn.fetch("""
                SELECT status, COUNT(*) as count,
                       AVG(progress_percentage) as avg_progress
                FROM student_progress 
                WHERE course_id = $1
                GROUP BY status
            """, course_id)
        
        # Structure course analytics
        course_analytics = {
            "course_id": course_id,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_back
            },
            "enrollment": {
                "total_students": student_count,
                "active_students": len(set(row['student_id'] for row in activity_metrics))
            },
            "lab_completion": {
                "completion_rates": [
                    {
                        "status": row['completion_status'],
                        "count": row['count'],
                        "average_duration": float(row['avg_duration'] or 0)
                    } for row in lab_completion
                ]
            },
            "quiz_performance": {
                "average_score": float(quiz_stats['avg_score'] or 0),
                "score_standard_deviation": float(quiz_stats['score_stddev'] or 0),
                "students_attempted": int(quiz_stats['students_attempted'] or 0),
                "total_attempts": int(quiz_stats['total_attempts'] or 0)
            },
            "progress_distribution": [
                {
                    "status": row['status'],
                    "count": row['count'],
                    "average_progress": float(row['avg_progress'])
                } for row in progress_dist
            ]
        }
        
        return course_analytics
        
    except Exception as e:
        logger.error(f"Failed to get course analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate course analytics")

# Helper functions

def calculate_engagement_score(analytics_data: Dict) -> float:
    """Calculate student engagement score based on various metrics"""
    try:
        # Factors for engagement calculation
        activity_factor = min(analytics_data['activity_summary']['total_activities'] / 50, 1.0) * 30
        lab_factor = min(analytics_data['lab_metrics']['total_sessions'] / 10, 1.0) * 25
        quiz_factor = (analytics_data['quiz_performance']['average_score'] / 100) * 25
        time_factor = min(
            sum(item['total_time_minutes'] for item in analytics_data['progress_summary']['by_content_type']) / 300,
            1.0
        ) * 20
        
        engagement_score = activity_factor + lab_factor + quiz_factor + time_factor
        return round(engagement_score, 2)
        
    except Exception:
        return 0.0

def generate_recommendations(analytics_data: Dict) -> List[str]:
    """Generate personalized recommendations based on analytics"""
    recommendations = []
    
    try:
        # Low activity recommendations
        if analytics_data['activity_summary']['total_activities'] < 10:
            recommendations.append("Increase platform engagement by logging in more frequently")
        
        # Lab performance recommendations
        if analytics_data['lab_metrics']['average_errors'] > 5:
            recommendations.append("Focus on debugging skills to reduce coding errors")
        
        if analytics_data['lab_metrics']['average_session_duration'] < 15:
            recommendations.append("Spend more time in lab sessions to improve understanding")
        
        # Quiz performance recommendations
        if analytics_data['quiz_performance']['average_score'] < 70:
            recommendations.append("Review course materials and retake quizzes to improve understanding")
        
        if analytics_data['quiz_performance']['pass_rate'] < 0.6:
            recommendations.append("Consider seeking additional help or tutoring")
        
        # Engagement recommendations
        if analytics_data['engagement_score'] < 50:
            recommendations.append("Increase overall course engagement through regular participation")
        
        # Default positive reinforcement
        if not recommendations:
            recommendations.append("Great job! Continue your excellent progress and engagement")
        
        return recommendations
        
    except Exception:
        return ["Continue working on course materials and practice regularly"]