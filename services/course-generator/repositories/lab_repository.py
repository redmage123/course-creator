"""
Lab Repository

Database operations for lab/exercise management.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncpg
import json

from .base_repository import BaseRepository


class LabRepository(BaseRepository):
    """
    Repository for lab/exercise data operations.
    
    Handles database operations for course labs and exercises.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize lab repository.
        
        Args:
            db_pool: Database connection pool
        """
        super().__init__(db_pool)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def save_exercises(self, course_id: str, exercises_data: Dict[str, Any]) -> bool:
        """
        Save exercises data for a course.
        
        Args:
            course_id: Course identifier
            exercises_data: Exercises data to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Prepare data for database
            data = {
                'course_id': course_id,
                'exercises_data': json.dumps(exercises_data),
                'title': exercises_data.get('course_title', 'Unknown Course'),
                'total_exercises': exercises_data.get('total_exercises', 0),
                'generated_at': exercises_data.get('generated_at'),
                'generation_method': exercises_data.get('generation_method', 'unknown')
            }
            
            # Use upsert to save exercises
            await self.upsert(
                table='exercises',
                data=data,
                conflict_columns=['course_id']
            )
            
            self.logger.info(f"Saved exercises for course {course_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving exercises for course {course_id}: {e}")
            return False
    
    async def get_exercises(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve exercises data for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Exercises data or None if not found
        """
        try:
            query = """
            SELECT exercises_data, title, total_exercises, generated_at, generation_method,
                   created_at, updated_at
            FROM exercises 
            WHERE course_id = $1
            """
            
            record = await self.fetch_one(query, course_id)
            
            if record:
                exercises_data = json.loads(record['exercises_data'])
                
                # Add metadata
                exercises_data['title'] = record['title']
                exercises_data['total_exercises'] = record['total_exercises']
                exercises_data['generated_at'] = record['generated_at']
                exercises_data['generation_method'] = record['generation_method']
                exercises_data['created_at'] = record['created_at'].isoformat() if record['created_at'] else None
                exercises_data['updated_at'] = record['updated_at'].isoformat() if record['updated_at'] else None
                
                return exercises_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving exercises for course {course_id}: {e}")
            return None
    
    async def update_exercises(self, course_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in exercises data.
        
        Args:
            course_id: Course identifier
            updates: Dictionary containing fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get current exercises data
            current_exercises = await self.get_exercises(course_id)
            if not current_exercises:
                return False
            
            # Update the exercises data
            current_exercises.update(updates)
            
            # Save the updated exercises
            return await self.save_exercises(course_id, current_exercises)
            
        except Exception as e:
            self.logger.error(f"Error updating exercises for course {course_id}: {e}")
            return False
    
    async def delete_exercises(self, course_id: str) -> bool:
        """
        Delete exercises data for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            query = "DELETE FROM exercises WHERE course_id = $1"
            await self.execute_query(query, course_id)
            
            self.logger.info(f"Deleted exercises for course {course_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting exercises for course {course_id}: {e}")
            return False
    
    async def list_exercises(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all exercises with pagination.
        
        Args:
            limit: Maximum number of exercises to return
            offset: Number of exercises to skip
            
        Returns:
            List of exercises data
        """
        try:
            query = """
            SELECT course_id, title, total_exercises, generated_at, generation_method,
                   created_at, updated_at
            FROM exercises
            ORDER BY updated_at DESC
            LIMIT $1 OFFSET $2
            """
            
            records = await self.fetch_all(query, limit, offset)
            
            exercises_list = []
            for record in records:
                exercises_info = {
                    'course_id': record['course_id'],
                    'title': record['title'],
                    'total_exercises': record['total_exercises'],
                    'generated_at': record['generated_at'],
                    'generation_method': record['generation_method'],
                    'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                    'updated_at': record['updated_at'].isoformat() if record['updated_at'] else None
                }
                exercises_list.append(exercises_info)
            
            return exercises_list
            
        except Exception as e:
            self.logger.error(f"Error listing exercises: {e}")
            return []
    
    async def search_exercises(self, search_term: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search exercises by title or content.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching exercises data
        """
        try:
            query = """
            SELECT course_id, title, total_exercises, generated_at, generation_method,
                   created_at, updated_at
            FROM exercises
            WHERE title ILIKE $1 OR exercises_data::text ILIKE $1
            ORDER BY updated_at DESC
            LIMIT $2
            """
            
            search_pattern = f"%{search_term}%"
            records = await self.fetch_all(query, search_pattern, limit)
            
            exercises_list = []
            for record in records:
                exercises_info = {
                    'course_id': record['course_id'],
                    'title': record['title'],
                    'total_exercises': record['total_exercises'],
                    'generated_at': record['generated_at'],
                    'generation_method': record['generation_method'],
                    'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                    'updated_at': record['updated_at'].isoformat() if record['updated_at'] else None
                }
                exercises_list.append(exercises_info)
            
            return exercises_list
            
        except Exception as e:
            self.logger.error(f"Error searching exercises: {e}")
            return []
    
    async def get_exercise_by_id(self, course_id: str, exercise_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific exercise by its ID.
        
        Args:
            course_id: Course identifier
            exercise_id: Exercise identifier
            
        Returns:
            Exercise data or None if not found
        """
        try:
            exercises_data = await self.get_exercises(course_id)
            if not exercises_data:
                return None
            
            exercises = exercises_data.get('exercises', [])
            for exercise in exercises:
                if exercise.get('id') == exercise_id:
                    return exercise
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting exercise {exercise_id} for course {course_id}: {e}")
            return None
    
    async def get_exercises_by_module(self, course_id: str, module_number: int) -> List[Dict[str, Any]]:
        """
        Get all exercises for a specific module.
        
        Args:
            course_id: Course identifier
            module_number: Module number
            
        Returns:
            List of exercise data for the module
        """
        try:
            exercises_data = await self.get_exercises(course_id)
            if not exercises_data:
                return []
            
            exercises = exercises_data.get('exercises', [])
            module_exercises = []
            
            for exercise in exercises:
                if exercise.get('module_number') == module_number:
                    module_exercises.append(exercise)
            
            return module_exercises
            
        except Exception as e:
            self.logger.error(f"Error getting exercises for module {module_number} in course {course_id}: {e}")
            return []
    
    async def get_exercises_by_difficulty(self, course_id: str, difficulty: str) -> List[Dict[str, Any]]:
        """
        Get all exercises for a specific difficulty level.
        
        Args:
            course_id: Course identifier
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            List of exercise data for the difficulty level
        """
        try:
            exercises_data = await self.get_exercises(course_id)
            if not exercises_data:
                return []
            
            exercises = exercises_data.get('exercises', [])
            difficulty_exercises = []
            
            for exercise in exercises:
                if exercise.get('difficulty') == difficulty:
                    difficulty_exercises.append(exercise)
            
            return difficulty_exercises
            
        except Exception as e:
            self.logger.error(f"Error getting exercises for difficulty {difficulty} in course {course_id}: {e}")
            return []
    
    async def save_lab_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Save lab session data.
        
        Args:
            session_data: Lab session data to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Prepare data for database
            data = {
                'session_id': session_data.get('session_id'),
                'course_id': session_data.get('course_id'),
                'exercise_id': session_data.get('exercise_id'),
                'user_id': session_data.get('user_id'),
                'session_data': json.dumps(session_data),
                'status': session_data.get('status', 'active'),
                'progress': session_data.get('progress', 0)
            }
            
            # Use upsert to save lab session
            await self.upsert(
                table='lab_sessions',
                data=data,
                conflict_columns=['session_id']
            )
            
            self.logger.info(f"Saved lab session {session_data.get('session_id')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving lab session: {e}")
            return False
    
    async def get_lab_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve lab session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Lab session data or None if not found
        """
        try:
            query = """
            SELECT session_data, course_id, exercise_id, user_id, status, progress,
                   created_at, updated_at
            FROM lab_sessions 
            WHERE session_id = $1
            """
            
            record = await self.fetch_one(query, session_id)
            
            if record:
                session_data = json.loads(record['session_data'])
                
                # Add metadata
                session_data['course_id'] = record['course_id']
                session_data['exercise_id'] = record['exercise_id']
                session_data['user_id'] = record['user_id']
                session_data['status'] = record['status']
                session_data['progress'] = record['progress']
                session_data['created_at'] = record['created_at'].isoformat() if record['created_at'] else None
                session_data['updated_at'] = record['updated_at'].isoformat() if record['updated_at'] else None
                
                return session_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving lab session {session_id}: {e}")
            return None
    
    async def count_exercises(self, course_id: str) -> int:
        """
        Count the total number of exercises for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Total number of exercises
        """
        try:
            query = "SELECT total_exercises FROM exercises WHERE course_id = $1"
            record = await self.fetch_one(query, course_id)
            
            if record:
                return record['total_exercises']
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error counting exercises for course {course_id}: {e}")
            return 0