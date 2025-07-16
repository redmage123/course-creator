"""
LabEnvironmentRepository implementation following Repository pattern.
Provides data access layer for lab environment operations.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LabEnvironmentRepository:
    """
    Repository for lab environment data operations following Repository pattern.
    Provides abstraction over database operations for lab environments.
    """
    
    def __init__(self, db):
        """
        Initialize LabEnvironmentRepository with database connection.
        
        Args:
            db: Database connection/pool
        """
        self.db = db
    
    async def get_by_course_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Get lab environment by course ID.
        
        Args:
            course_id: The course ID
            
        Returns:
            Lab environment dictionary or None if not found
        """
        try:
            query = """
                SELECT id, course_id, name, description, environment_type, 
                       config, exercises, is_active, created_at, updated_at
                FROM lab_environments 
                WHERE course_id = %s AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            row = await self.db.fetch_one(query, (course_id,))
            
            if row:
                return self._row_to_lab_environment(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting lab environment for course {course_id}: {e}")
            raise
    
    async def save(self, lab_data: Dict[str, Any]) -> str:
        """
        Save a lab environment to the database.
        
        Args:
            lab_data: Lab environment data dictionary
            
        Returns:
            Lab environment ID
        """
        try:
            query = """
                INSERT INTO lab_environments (
                    id, course_id, name, description, environment_type, 
                    config, exercises, is_active, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    environment_type = EXCLUDED.environment_type,
                    config = EXCLUDED.config,
                    exercises = EXCLUDED.exercises,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
            """
            
            values = (
                lab_data['id'],
                lab_data['course_id'],
                lab_data['name'],
                lab_data['description'],
                lab_data['environment_type'],
                json.dumps(lab_data.get('config', {})),
                json.dumps(lab_data.get('exercises', [])),
                lab_data.get('is_active', True),
                lab_data.get('created_at', datetime.now().isoformat()),
                datetime.now().isoformat()
            )
            
            await self.db.execute(query, values)
            return lab_data['id']
            
        except Exception as e:
            logger.error(f"Error saving lab environment: {e}")
            raise
    
    def _row_to_lab_environment(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert database row to lab environment dictionary.
        
        Args:
            row: Database row dictionary
            
        Returns:
            Lab environment dictionary
        """
        return {
            'id': row['id'],
            'course_id': row['course_id'],
            'name': row['name'],
            'description': row['description'],
            'environment_type': row['environment_type'],
            'config': json.loads(row['config']) if row['config'] else {},
            'exercises': json.loads(row['exercises']) if row['exercises'] else [],
            'is_active': row['is_active'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }