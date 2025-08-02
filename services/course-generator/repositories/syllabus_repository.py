"""
Syllabus Repository

Handles database operations for syllabus data.
Implements the Repository pattern for syllabus persistence.
"""

from typing import Optional, Dict, Any, List
import json
from datetime import datetime
import asyncpg

from repositories.base_repository import BaseRepository


class SyllabusRepository(BaseRepository):
    """
    Repository for syllabus data operations.
    
    Handles CRUD operations for syllabus data in the database,
    providing clean separation between data access and business logic.
    """
    
    async def save_syllabus(self, course_id: str, syllabus_data: Dict[str, Any]) -> None:
        """
        Save or update syllabus data for a course.
        
        Args:
            course_id: Unique identifier for the course
            syllabus_data: Dictionary containing syllabus information
            
        Raises:
            Exception: If save operation fails
        """
        try:
            data = {
                'course_id': course_id,
                'syllabus_json': json.dumps(syllabus_data),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            await self.upsert(
                table='syllabi',
                data=data,
                conflict_columns=['course_id']
            )
            
            self.logger.info(f"Saved syllabus for course {course_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save syllabus for course {course_id}: {e}")
            raise
    
    async def get_syllabus(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve syllabus data for a course.
        
        Args:
            course_id: Unique identifier for the course
            
        Returns:
            Dictionary containing syllabus data or None if not found
            
        Raises:
            Exception: If retrieval operation fails
        """
        try:
            query = """
                SELECT syllabus_json, created_at, updated_at 
                FROM syllabi 
                WHERE course_id = $1 AND deleted_at IS NULL
            """
            
            result = await self.fetch_one(query, course_id)
            
            if result:
                syllabus_data = json.loads(result['syllabus_json'])
                syllabus_data['created_at'] = result['created_at']
                syllabus_data['updated_at'] = result['updated_at']
                
                self.logger.info(f"Retrieved syllabus for course {course_id}")
                return syllabus_data
            
            self.logger.info(f"No syllabus found for course {course_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve syllabus for course {course_id}: {e}")
            raise
    
    async def delete_syllabus(self, course_id: str) -> bool:
        """
        Soft delete syllabus data for a course.
        
        Args:
            course_id: Unique identifier for the course
            
        Returns:
            True if syllabus was found and deleted, False otherwise
            
        Raises:
            Exception: If delete operation fails
        """
        try:
            # Check if syllabus exists
            exists = await self.check_exists(
                table='syllabi',
                condition='course_id = $1 AND deleted_at IS NULL',
                params=[course_id]
            )
            
            if not exists:
                self.logger.info(f"No syllabus found to delete for course {course_id}")
                return False
            
            # Perform soft delete
            await self.soft_delete(
                table='syllabi',
                condition='course_id = $1',
                params=[course_id]
            )
            
            self.logger.info(f"Deleted syllabus for course {course_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete syllabus for course {course_id}: {e}")
            raise
    
    async def update_syllabus(self, course_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in syllabus data.
        
        Args:
            course_id: Unique identifier for the course
            updates: Dictionary containing fields to update
            
        Returns:
            True if syllabus was found and updated, False otherwise
            
        Raises:
            Exception: If update operation fails
        """
        try:
            # First get the existing syllabus
            existing_syllabus = await self.get_syllabus(course_id)
            
            if not existing_syllabus:
                self.logger.info(f"No syllabus found to update for course {course_id}")
                return False
            
            # Remove metadata from existing syllabus
            existing_syllabus.pop('created_at', None)
            existing_syllabus.pop('updated_at', None)
            
            # Merge updates with existing data
            updated_syllabus = {**existing_syllabus, **updates}
            
            # Save the updated syllabus
            await self.save_syllabus(course_id, updated_syllabus)
            
            self.logger.info(f"Updated syllabus for course {course_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update syllabus for course {course_id}: {e}")
            raise
    
    async def list_syllabi(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all syllabi with pagination.
        
        Args:
            limit: Maximum number of syllabi to return
            offset: Number of syllabi to skip
            
        Returns:
            List of syllabus data dictionaries
            
        Raises:
            Exception: If list operation fails
        """
        try:
            query = """
                SELECT course_id, syllabus_json, created_at, updated_at 
                FROM syllabi 
                WHERE deleted_at IS NULL
                ORDER BY updated_at DESC
                LIMIT $1 OFFSET $2
            """
            
            results = await self.fetch_all(query, limit, offset)
            
            syllabi = []
            for result in results:
                syllabus_data = json.loads(result['syllabus_json'])
                syllabus_data['course_id'] = result['course_id']
                syllabus_data['created_at'] = result['created_at']
                syllabus_data['updated_at'] = result['updated_at']
                syllabi.append(syllabus_data)
            
            self.logger.info(f"Listed {len(syllabi)} syllabi")
            return syllabi
            
        except Exception as e:
            self.logger.error(f"Failed to list syllabi: {e}")
            raise
    
    async def search_syllabi(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search syllabi by title or description.
        
        Args:
            search_term: Term to search for in syllabus content
            limit: Maximum number of results to return
            
        Returns:
            List of matching syllabus data dictionaries
            
        Raises:
            Exception: If search operation fails
        """
        try:
            query = """
                SELECT course_id, syllabus_json, created_at, updated_at 
                FROM syllabi 
                WHERE deleted_at IS NULL
                AND (
                    syllabus_json::text ILIKE $1 
                    OR course_id ILIKE $1
                )
                ORDER BY updated_at DESC
                LIMIT $2
            """
            
            search_pattern = f"%{search_term}%"
            results = await self.fetch_all(query, search_pattern, limit)
            
            syllabi = []
            for result in results:
                syllabus_data = json.loads(result['syllabus_json'])
                syllabus_data['course_id'] = result['course_id']
                syllabus_data['created_at'] = result['created_at']
                syllabus_data['updated_at'] = result['updated_at']
                syllabi.append(syllabus_data)
            
            self.logger.info(f"Found {len(syllabi)} syllabi matching '{search_term}'")
            return syllabi
            
        except Exception as e:
            self.logger.error(f"Failed to search syllabi: {e}")
            raise