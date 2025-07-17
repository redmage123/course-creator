"""
Course instantiation service for creating scheduled course instances with start/end dates.
Following TDD approach and SOLID principles.
"""
import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CourseInstantiationService:
    """
    Service for creating and managing course instances with scheduling.
    Follows Single Responsibility Principle - only handles course instantiation logic.
    """
    
    def __init__(self, db_pool):
        """
        Initialize course instantiation service.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    async def create_course_instance(
        self,
        course_id: str,
        start_date: datetime,
        end_date: datetime,
        max_students: int = 25,
        timezone: str = 'UTC',
        meeting_schedule: Optional[str] = None
    ) -> Dict:
        """
        Create a new course instance with specific start/end dates.
        
        Args:
            course_id: ID of the course to instantiate
            start_date: When the course instance starts
            end_date: When the course instance ends
            max_students: Maximum number of students allowed
            timezone: Timezone for the course
            meeting_schedule: Optional meeting schedule description
            
        Returns:
            Dict: Created course instance data
            
        Raises:
            ValueError: If dates are invalid
        """
        # Validate dates
        if end_date <= start_date:
            raise ValueError("End date must be after start date")
        
        # Determine initial status based on dates
        current_time = datetime.now()
        if current_time < start_date:
            initial_status = 'scheduled'
        elif start_date <= current_time <= end_date:
            initial_status = 'active'
        else:
            initial_status = 'completed'
        
        # Only validate past dates for scheduled courses
        if initial_status == 'scheduled' and start_date < current_time:
            raise ValueError("Start date cannot be in the past")
        
        # Create course instance
        instance_id = str(uuid.uuid4())
        instance_data = {
            'id': instance_id,
            'course_id': course_id,
            'start_date': start_date,
            'end_date': end_date,
            'max_students': max_students,
            'current_enrollment': 0,
            'timezone': timezone,
            'meeting_schedule': meeting_schedule,
            'status': initial_status,
            'created_at': datetime.now()
        }
        
        # Insert into database
        await self.db_pool.execute(
            """
            INSERT INTO course_instances 
            (id, course_id, start_date, end_date, max_students, current_enrollment, 
             timezone, meeting_schedule, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            instance_id, course_id, start_date, end_date, max_students, 0,
            timezone, meeting_schedule, initial_status, datetime.now()
        )
        
        logger.info(f"Created course instance {instance_id} for course {course_id}")
        return instance_data
    
    async def get_active_course_instances(self) -> List[Dict]:
        """
        Get all currently active course instances.
        
        Returns:
            List[Dict]: Active course instances
        """
        current_date = datetime.now()
        rows = await self.db_pool.fetch(
            """
            SELECT id, course_id, start_date, end_date, max_students, current_enrollment,
                   timezone, meeting_schedule, status, created_at
            FROM course_instances 
            WHERE start_date <= $1 AND end_date >= $1 AND status = 'active'
            ORDER BY start_date ASC
            """,
            current_date
        )
        
        return [dict(row) for row in rows]
    
    async def update_course_instance_status(self, instance_id: str) -> str:
        """
        Update course instance status based on current date.
        
        Args:
            instance_id: Course instance ID
            
        Returns:
            str: Updated status
        """
        current_date = datetime.now()
        
        # Get current instance data
        instance_data = await self.db_pool.fetch(
            "SELECT start_date, end_date, status FROM course_instances WHERE id = $1",
            instance_id
        )
        
        if not instance_data:
            raise ValueError(f"Course instance {instance_id} not found")
        
        instance = instance_data[0]
        start_date = instance['start_date']
        end_date = instance['end_date']
        current_status = instance['status']
        
        # Determine new status
        if current_date < start_date:
            new_status = 'scheduled'
        elif start_date <= current_date <= end_date:
            new_status = 'active'
        else:
            new_status = 'completed'
        
        # Update status if changed
        if new_status != current_status:
            await self.db_pool.execute(
                "UPDATE course_instances SET status = $1 WHERE id = $2",
                new_status, instance_id
            )
            logger.info(f"Updated course instance {instance_id} status from {current_status} to {new_status}")
        
        return new_status
    
    async def get_upcoming_course_instances(self, days_ahead: int = 30) -> List[Dict]:
        """
        Get upcoming course instances within specified days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List[Dict]: Upcoming course instances
        """
        current_date = datetime.now()
        end_date = current_date + timedelta(days=days_ahead)
        
        rows = await self.db_pool.fetch(
            """
            SELECT id, course_id, start_date, end_date, max_students, current_enrollment,
                   timezone, meeting_schedule, status, created_at
            FROM course_instances 
            WHERE start_date > $1 AND start_date <= $2
            ORDER BY start_date ASC
            """,
            current_date, end_date
        )
        
        return [dict(row) for row in rows]