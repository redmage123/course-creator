"""
Analytics Client for Course Generator Service
Handles analytics tracking for quiz generation and course-related events
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import structlog

logger = structlog.get_logger()

class CourseAnalyticsClient:
    """Client for tracking course generator analytics events"""
    
    def __init__(self, analytics_url: str = "http://localhost:8007"):
        self.analytics_url = analytics_url
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def track_quiz_generation(self, course_id: str, instructor_id: str, 
                                  quiz_count: int, difficulty: str = "beginner"):
        """Track quiz generation activity"""
        try:
            session = await self._get_session()
            
            payload = {
                "student_id": instructor_id,  # Using instructor as user for this action
                "course_id": course_id,
                "activity_type": "quiz_generated",
                "activity_data": {
                    "quiz_count": quiz_count,
                    "difficulty": difficulty,
                    "generation_method": "ai_powered"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with session.post(
                f"{self.analytics_url}/activities/track",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Quiz generation tracked", 
                              course_id=course_id, 
                              quiz_count=quiz_count)
                else:
                    logger.warning("Failed to track quiz generation", 
                                 status=response.status,
                                 course_id=course_id)
                    
        except Exception as e:
            logger.error("Error tracking quiz generation", 
                        course_id=course_id, 
                        error=str(e))
    
    async def track_quiz_attempt_start(self, student_id: str, course_id: str, 
                                     quiz_id: str, questions_total: int):
        """Track when a student starts a quiz"""
        try:
            session = await self._get_session()
            
            payload = {
                "student_id": student_id,
                "course_id": course_id,
                "activity_type": "quiz_start",
                "activity_data": {
                    "quiz_id": quiz_id,
                    "questions_total": questions_total
                },
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": f"quiz-{quiz_id}"
            }
            
            async with session.post(
                f"{self.analytics_url}/activities/track",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Quiz start tracked", 
                              student_id=student_id, 
                              quiz_id=quiz_id)
                    
        except Exception as e:
            logger.error("Error tracking quiz start", 
                        student_id=student_id,
                        quiz_id=quiz_id, 
                        error=str(e))
    
    async def track_quiz_completion(self, student_id: str, course_id: str, 
                                  quiz_id: str, score_percentage: float,
                                  questions_total: int, questions_correct: int,
                                  duration_minutes: int, answers: Dict):
        """Track quiz completion and performance"""
        try:
            # Track quiz performance
            session = await self._get_session()
            
            performance_payload = {
                "student_id": student_id,
                "course_id": course_id,
                "quiz_id": quiz_id,
                "start_time": (datetime.utcnow() - timedelta(minutes=duration_minutes)).isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "questions_total": questions_total,
                "questions_answered": questions_total,
                "questions_correct": questions_correct,
                "answers": answers,
                "status": "completed"
            }
            
            async with session.post(
                f"{self.analytics_url}/quiz-performance/track",
                json=performance_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Quiz performance tracked", 
                              student_id=student_id, 
                              quiz_id=quiz_id,
                              score=score_percentage)
            
            # Track completion activity
            activity_payload = {
                "student_id": student_id,
                "course_id": course_id,
                "activity_type": "quiz_complete",
                "activity_data": {
                    "quiz_id": quiz_id,
                    "score_percentage": score_percentage,
                    "questions_correct": questions_correct,
                    "questions_total": questions_total,
                    "duration_minutes": duration_minutes
                },
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": f"quiz-{quiz_id}"
            }
            
            async with session.post(
                f"{self.analytics_url}/activities/track",
                json=activity_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Quiz completion tracked", 
                              student_id=student_id, 
                              quiz_id=quiz_id)
                    
        except Exception as e:
            logger.error("Error tracking quiz completion", 
                        student_id=student_id,
                        quiz_id=quiz_id, 
                        error=str(e))
    
    async def track_course_content_generation(self, course_id: str, instructor_id: str,
                                            content_type: str, content_count: int):
        """Track course content generation (slides, syllabus, etc.)"""
        try:
            session = await self._get_session()
            
            payload = {
                "student_id": instructor_id,
                "course_id": course_id,
                "activity_type": "content_generated",
                "activity_data": {
                    "content_type": content_type,
                    "content_count": content_count,
                    "generation_method": "ai_powered"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with session.post(
                f"{self.analytics_url}/activities/track",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Content generation tracked", 
                              course_id=course_id, 
                              content_type=content_type)
                    
        except Exception as e:
            logger.error("Error tracking content generation", 
                        course_id=course_id,
                        content_type=content_type, 
                        error=str(e))
    
    async def update_content_progress(self, student_id: str, course_id: str,
                                    content_item_id: str, content_type: str,
                                    progress_percentage: float, time_spent_minutes: int):
        """Update student progress for course content"""
        try:
            session = await self._get_session()
            
            payload = {
                "student_id": student_id,
                "course_id": course_id,
                "content_item_id": content_item_id,
                "content_type": content_type,
                "status": "completed" if progress_percentage >= 100 else "in_progress",
                "progress_percentage": progress_percentage,
                "time_spent_minutes": time_spent_minutes,
                "last_accessed": datetime.utcnow().isoformat()
            }
            
            async with session.post(
                f"{self.analytics_url}/progress/update",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Content progress updated", 
                              student_id=student_id, 
                              content_item_id=content_item_id)
                    
        except Exception as e:
            logger.error("Error updating content progress", 
                        student_id=student_id,
                        content_item_id=content_item_id, 
                        error=str(e))

# Global analytics client instance  
course_analytics_client = CourseAnalyticsClient()