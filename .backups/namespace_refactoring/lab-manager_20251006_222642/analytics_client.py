"""
Analytics Client for Lab Container Service
Handles analytics tracking for lab-related events
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional
import aiohttp
import structlog

logger = structlog.get_logger()

class AnalyticsClient:
    """Client for tracking lab analytics events"""
    
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
    
    async def track_lab_activity(self, student_id: str, course_id: str, 
                                activity_type: str, activity_data: Dict, 
                                session_id: Optional[str] = None):
        """Track a lab-related student activity"""
        try:
            session = await self._get_session()
            
            payload = {
                "student_id": student_id,
                "course_id": course_id,
                "activity_type": activity_type,
                "activity_data": activity_data,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id
            }
            
            async with session.post(
                f"{self.analytics_url}/activities/track",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Lab activity tracked", 
                              student_id=student_id, 
                              activity_type=activity_type)
                else:
                    logger.warning("Failed to track lab activity", 
                                 status=response.status,
                                 student_id=student_id,
                                 activity_type=activity_type)
                    
        except Exception as e:
            logger.error("Error tracking lab activity", 
                        student_id=student_id,
                        activity_type=activity_type, 
                        error=str(e))
    
    async def track_lab_usage(self, student_id: str, course_id: str, lab_id: str,
                             session_start: datetime, session_end: Optional[datetime] = None,
                             actions_performed: int = 0, code_executions: int = 0,
                             errors_encountered: int = 0, completion_status: str = "in_progress",
                             final_code: Optional[str] = None):
        """Track detailed lab usage metrics"""
        try:
            session = await self._get_session()
            
            payload = {
                "student_id": student_id,
                "course_id": course_id,
                "lab_id": lab_id,
                "session_start": session_start.isoformat(),
                "session_end": session_end.isoformat() if session_end else None,
                "actions_performed": actions_performed,
                "code_executions": code_executions,
                "errors_encountered": errors_encountered,
                "completion_status": completion_status,
                "final_code": final_code
            }
            
            async with session.post(
                f"{self.analytics_url}/lab-usage/track",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Lab usage tracked", 
                              student_id=student_id, 
                              lab_id=lab_id)
                else:
                    logger.warning("Failed to track lab usage", 
                                 status=response.status,
                                 student_id=student_id,
                                 lab_id=lab_id)
                    
        except Exception as e:
            logger.error("Error tracking lab usage", 
                        student_id=student_id,
                        lab_id=lab_id, 
                        error=str(e))
    
    async def update_student_progress(self, student_id: str, course_id: str, 
                                    content_item_id: str, content_type: str = "lab",
                                    status: str = "in_progress", progress_percentage: float = 0.0,
                                    time_spent_minutes: int = 0, mastery_score: Optional[float] = None):
        """Update student progress for lab completion"""
        try:
            session = await self._get_session()
            
            payload = {
                "student_id": student_id,
                "course_id": course_id,
                "content_item_id": content_item_id,
                "content_type": content_type,
                "status": status,
                "progress_percentage": progress_percentage,
                "time_spent_minutes": time_spent_minutes,
                "last_accessed": datetime.utcnow().isoformat(),
                "completion_date": datetime.utcnow().isoformat() if status == "completed" else None,
                "mastery_score": mastery_score
            }
            
            async with session.post(
                f"{self.analytics_url}/progress/update",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Student progress updated", 
                              student_id=student_id, 
                              content_item_id=content_item_id,
                              status=status)
                else:
                    logger.warning("Failed to update student progress", 
                                 status=response.status,
                                 student_id=student_id,
                                 content_item_id=content_item_id)
                    
        except Exception as e:
            logger.error("Error updating student progress", 
                        student_id=student_id,
                        content_item_id=content_item_id, 
                        error=str(e))

# Global analytics client instance
analytics_client = AnalyticsClient()