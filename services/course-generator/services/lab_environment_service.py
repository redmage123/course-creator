"""
LabEnvironmentService implementation following SOLID principles.
Handles lab environment creation, management, and student access.
"""
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LabEnvironmentService:
    """
    Service for managing lab environment operations following Single Responsibility Principle.
    Handles lab environment CRUD operations, generation, and student access management.
    """
    
    def __init__(self, db, ai_service, storage):
        """
        Initialize LabEnvironmentService with dependencies.
        
        Args:
            db: Database connection/pool
            ai_service: AI service for lab environment generation
            storage: Storage service for lab files
        """
        self.db = db
        self.ai_service = ai_service
        self.storage = storage
        self._memory_cache = {}  # In-memory fallback cache
        self.repository = None  # Will be set by dependency injection
        
        # Supported environment types
        self.supported_environments = {
            'python': {'language': 'python', 'default_version': '3.9'},
            'javascript': {'language': 'javascript', 'default_version': 'node16'},
            'java': {'language': 'java', 'default_version': '11'},
            'cpp': {'language': 'cpp', 'default_version': 'gcc11'},
            'web': {'language': 'html', 'default_version': 'html5'},
            'data': {'language': 'python', 'default_version': '3.9'},
            'security': {'language': 'linux', 'default_version': 'ubuntu20'},
            'terminal': {'language': 'bash', 'default_version': 'bash5'}
        }
    
    async def get_lab_environment_by_course_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Get lab environment for a course, with database-first approach and memory fallback.
        
        Args:
            course_id: The course ID to get lab environment for
            
        Returns:
            Lab environment dictionary or None if not found
        """
        try:
            # First, try to get from database
            return await self._get_lab_environment_from_database(course_id)
        except Exception as e:
            logger.warning(f"Database unavailable for course {course_id}: {e}")
            # Fallback to memory cache
            return self._get_lab_environment_from_memory(course_id)
    
    async def _get_lab_environment_from_database(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get lab environment from database."""
        if not self.db:
            raise Exception("Database not available")
        
        try:
            # Query using the actual database schema
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
                # Transform database row to lab environment format
                lab_env = {
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
                
                return lab_env
            
            return None
            
        except Exception as e:
            logger.error(f"Database error getting lab environment for course {course_id}: {e}")
            raise
    
    def _get_lab_environment_from_memory(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get lab environment from memory cache."""
        return self._memory_cache.get(course_id)
    
    async def create_lab_environment(self, lab_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new lab environment.
        
        Args:
            lab_data: Lab environment data dictionary
            
        Returns:
            Created lab environment dictionary
        """
        try:
            # Validate lab environment data
            if not self.validate_lab_environment_data(lab_data):
                raise ValueError("Invalid lab environment data")
            
            # Add metadata
            lab_data['id'] = str(uuid.uuid4())
            lab_data['created_at'] = datetime.now().isoformat()
            lab_data['updated_at'] = datetime.now().isoformat()
            lab_data['is_active'] = True
            
            # Ensure config is properly formatted
            if 'config' not in lab_data:
                lab_data['config'] = self._get_default_config(lab_data['environment_type'])
            
            # Save to database
            try:
                await self.save_lab_environment_to_database(lab_data)
            except Exception as e:
                logger.error(f"Failed to save lab environment to database: {e}")
                # Still add to memory cache for immediate use
                self._add_to_memory_cache(lab_data['course_id'], lab_data)
            
            return lab_data
            
        except Exception as e:
            logger.error(f"Error creating lab environment: {e}")
            raise
    
    async def save_lab_environment_to_database(self, lab_data: Dict[str, Any]) -> None:
        """
        Save lab environment to database with proper schema mapping.
        
        Args:
            lab_data: Lab environment data dictionary
        """
        if not self.db:
            raise Exception("Database not available")
        
        try:
            # Map lab environment data to database schema
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
            logger.info(f"Lab environment {lab_data['id']} saved to database")
            
        except Exception as e:
            logger.error(f"Error saving lab environment to database: {e}")
            raise
    
    def validate_lab_environment_data(self, lab_data: Dict[str, Any]) -> bool:
        """
        Validate lab environment data structure and content.
        
        Args:
            lab_data: Lab environment data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['course_id', 'name', 'description', 'environment_type']
            for field in required_fields:
                if not lab_data.get(field) or str(lab_data[field]).strip() == '':
                    logger.warning(f"Lab environment missing required field: {field}")
                    return False
            
            # Check environment type is supported
            if lab_data['environment_type'] not in self.supported_environments:
                logger.warning(f"Unsupported environment type: {lab_data['environment_type']}")
                return False
            
            # Validate config structure
            config = lab_data.get('config', {})
            if not isinstance(config, dict):
                logger.warning("Lab environment config must be a dictionary")
                return False
            
            # Validate exercises if provided
            exercises = lab_data.get('exercises', [])
            if exercises and not isinstance(exercises, list):
                logger.warning("Lab environment exercises must be a list")
                return False
            
            for exercise in exercises:
                if not self._validate_exercise(exercise):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating lab environment data: {e}")
            return False
    
    def _validate_exercise(self, exercise: Dict[str, Any]) -> bool:
        """Validate individual exercise data."""
        try:
            # Check required fields
            required_fields = ['title', 'description']
            for field in required_fields:
                if not exercise.get(field) or exercise[field].strip() == '':
                    return False
            
            # Check optional fields have correct types
            if 'starter_code' in exercise and not isinstance(exercise['starter_code'], str):
                return False
            
            if 'solution' in exercise and not isinstance(exercise['solution'], str):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating exercise: {e}")
            return False
    
    def _get_default_config(self, environment_type: str) -> Dict[str, Any]:
        """Get default configuration for environment type."""
        if environment_type in self.supported_environments:
            base_config = self.supported_environments[environment_type].copy()
            
            # Add environment-specific defaults
            if environment_type == 'python':
                base_config['packages'] = ['numpy', 'pandas', 'matplotlib']
            elif environment_type == 'javascript':
                base_config['packages'] = ['lodash', 'axios']
            elif environment_type == 'data':
                base_config['packages'] = ['numpy', 'pandas', 'matplotlib', 'scikit-learn']
            elif environment_type == 'web':
                base_config['frameworks'] = ['bootstrap', 'jquery']
            
            return base_config
        
        return {}
    
    def _add_to_memory_cache(self, course_id: str, lab_data: Dict[str, Any]) -> None:
        """Add lab environment to memory cache."""
        self._memory_cache[course_id] = lab_data
    
    async def check_student_lab_access(self, course_id: str, student_id: str) -> bool:
        """
        Check if a student has access to a lab environment.
        
        Args:
            course_id: The course ID
            student_id: The student ID
            
        Returns:
            True if student has access, False otherwise
        """
        try:
            # First check if lab environment exists
            lab_env = await self.get_lab_environment_by_course_id(course_id)
            if not lab_env or not lab_env.get('is_active', False):
                return False
            
            # Check if student is enrolled in the course
            return await self._check_student_enrollment(course_id, student_id)
            
        except Exception as e:
            logger.error(f"Error checking student lab access: {e}")
            return False
    
    async def _check_student_enrollment(self, course_id: str, student_id: str) -> bool:
        """Check if student is enrolled in the course."""
        try:
            if not self.db:
                return False
            
            query = """
                SELECT 1 FROM enrollments 
                WHERE course_id = %s AND student_id = %s AND is_active = TRUE
            """
            
            result = await self.db.fetch_one(query, (course_id, student_id))
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking student enrollment: {e}")
            return False
    
    async def generate_lab_environment_from_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate lab environment from course data using AI.
        
        Args:
            course_data: Course data dictionary
            
        Returns:
            Generated lab environment dictionary
        """
        try:
            # Generate lab environment using AI service
            ai_response = await self.ai_service.generate_lab_environment(course_data)
            
            if not ai_response or 'lab_environment' not in ai_response:
                raise ValueError("Invalid AI response for lab environment generation")
            
            lab_env_data = ai_response['lab_environment']
            
            # Add course metadata
            lab_env_data['course_id'] = course_data['id']
            
            # Create the lab environment
            return await self.create_lab_environment(lab_env_data)
            
        except Exception as e:
            logger.error(f"Error generating lab environment from course: {e}")
            raise
    
    async def get_lab_environment_via_repository(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get lab environment via repository pattern (if available)."""
        if not self.repository:
            return await self.get_lab_environment_by_course_id(course_id)
        
        try:
            return await self.repository.get_by_course_id(course_id)
        except Exception as e:
            logger.warning(f"Repository unavailable, falling back to direct database: {e}")
            return await self.get_lab_environment_by_course_id(course_id)
    
    async def update_lab_environment(self, lab_id: str, lab_data: Dict[str, Any]) -> bool:
        """
        Update an existing lab environment.
        
        Args:
            lab_id: The lab environment ID to update
            lab_data: Updated lab environment data
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if not self.validate_lab_environment_data(lab_data):
                return False
            
            lab_data['id'] = lab_id
            lab_data['updated_at'] = datetime.now().isoformat()
            
            await self.save_lab_environment_to_database(lab_data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating lab environment {lab_id}: {e}")
            return False
    
    async def delete_lab_environment(self, lab_id: str) -> bool:
        """
        Delete a lab environment by ID.
        
        Args:
            lab_id: The lab environment ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if not self.db:
                raise Exception("Database not available")
            
            # Soft delete by setting is_active to false
            query = "UPDATE lab_environments SET is_active = FALSE, updated_at = %s WHERE id = %s"
            await self.db.execute(query, (datetime.now().isoformat(), lab_id))
            
            # Also remove from memory cache
            for course_id, lab_data in self._memory_cache.items():
                if lab_data.get('id') == lab_id:
                    del self._memory_cache[course_id]
                    break
            
            logger.info(f"Lab environment {lab_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting lab environment {lab_id}: {e}")
            return False