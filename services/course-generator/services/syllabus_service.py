"""
Syllabus Service

Business logic for syllabus operations.
Orchestrates between repositories and AI components for syllabus management.
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.syllabus_repository import SyllabusRepository
from ai.client import AIClient
from ai.generators.syllabus_generator import SyllabusGenerator
from ai.fallback.fallback_syllabus import FallbackSyllabusGenerator


class SyllabusService:
    """
    Service for syllabus business logic.
    
    Handles syllabus generation, refinement, and management operations.
    Coordinates between data repositories and AI components.
    """
    
    def __init__(self, syllabus_repo: SyllabusRepository, ai_client: AIClient):
        """
        Initialize syllabus service.
        
        Args:
            syllabus_repo: Repository for syllabus data operations
            ai_client: AI client for content generation
        """
        self.syllabus_repo = syllabus_repo
        self.ai_client = ai_client
        self.syllabus_generator = SyllabusGenerator(ai_client)
        self.syllabus_fallback = FallbackSyllabusGenerator()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_syllabus(self, course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a new syllabus for a course.
        
        Args:
            course_info: Dictionary containing course information
                - title: Course title
                - description: Course description
                - duration: Course duration
                - level: Course level (beginner, intermediate, advanced)
                - objectives: Learning objectives
                
        Returns:
            Generated syllabus data
            
        Raises:
            Exception: If generation fails
        """
        try:
            self.logger.info(f"Generating syllabus for course: {course_info.get('title', 'Unknown')}")
            
            # Try AI generation first
            if self.ai_client.is_available:
                syllabus_data = await self.syllabus_generator.generate_from_course_info(course_info)
                
                if syllabus_data:
                    # Add metadata
                    syllabus_data['generated_at'] = datetime.utcnow().isoformat()
                    syllabus_data['generation_method'] = 'ai'
                    
                    self.logger.info("Successfully generated syllabus using AI")
                    return syllabus_data
            
            # Fall back to template-based generation
            self.logger.info("Using fallback syllabus generation")
            syllabus_data = await self.syllabus_fallback.generate_from_course_info(course_info)
            
            # Add metadata
            syllabus_data['generated_at'] = datetime.utcnow().isoformat()
            syllabus_data['generation_method'] = 'fallback'
            
            return syllabus_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate syllabus: {e}")
            raise
    
    async def refine_syllabus(self, course_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine an existing syllabus based on feedback.
        
        Args:
            course_id: Course identifier
            feedback: Feedback for refinement
                - suggestions: List of suggestions
                - focus_areas: Areas to focus on
                - adjustments: Specific adjustments to make
                
        Returns:
            Refined syllabus data
            
        Raises:
            Exception: If refinement fails
        """
        try:
            self.logger.info(f"Refining syllabus for course: {course_id}")
            
            # Get existing syllabus
            existing_syllabus = await self.syllabus_repo.get_syllabus(course_id)
            
            if not existing_syllabus:
                raise ValueError(f"No syllabus found for course {course_id}")
            
            # Try AI refinement if available
            if self.ai_client.is_available:
                refined_syllabus = await self.syllabus_generator.refine_syllabus(
                    existing_syllabus, 
                    feedback
                )
                
                if refined_syllabus:
                    # Add metadata
                    refined_syllabus['refined_at'] = datetime.utcnow().isoformat()
                    refined_syllabus['refinement_method'] = 'ai'
                    
                    # Save refined syllabus
                    await self.syllabus_repo.save_syllabus(course_id, refined_syllabus)
                    
                    self.logger.info("Successfully refined syllabus using AI")
                    return refined_syllabus
            
            # Fall back to manual refinement
            self.logger.info("Using fallback syllabus refinement")
            refined_syllabus = await self.syllabus_fallback.refine_syllabus(
                existing_syllabus, 
                feedback
            )
            
            # Add metadata
            refined_syllabus['refined_at'] = datetime.utcnow().isoformat()
            refined_syllabus['refinement_method'] = 'fallback'
            
            # Save refined syllabus
            await self.syllabus_repo.save_syllabus(course_id, refined_syllabus)
            
            return refined_syllabus
            
        except Exception as e:
            self.logger.error(f"Failed to refine syllabus for course {course_id}: {e}")
            raise
    
    async def save_syllabus(self, course_id: str, syllabus_data: Dict[str, Any]) -> None:
        """
        Save syllabus data for a course.
        
        Args:
            course_id: Course identifier
            syllabus_data: Syllabus data to save
            
        Raises:
            Exception: If save operation fails
        """
        try:
            # Add save timestamp
            syllabus_data['saved_at'] = datetime.utcnow().isoformat()
            
            await self.syllabus_repo.save_syllabus(course_id, syllabus_data)
            
            self.logger.info(f"Saved syllabus for course {course_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save syllabus for course {course_id}: {e}")
            raise
    
    async def get_syllabus(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve syllabus data for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Syllabus data or None if not found
            
        Raises:
            Exception: If retrieval fails
        """
        try:
            syllabus_data = await self.syllabus_repo.get_syllabus(course_id)
            
            if syllabus_data:
                self.logger.info(f"Retrieved syllabus for course {course_id}")
            else:
                self.logger.info(f"No syllabus found for course {course_id}")
            
            return syllabus_data
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve syllabus for course {course_id}: {e}")
            raise
    
    async def delete_syllabus(self, course_id: str) -> bool:
        """
        Delete syllabus data for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            True if syllabus was deleted, False if not found
            
        Raises:
            Exception: If deletion fails
        """
        try:
            deleted = await self.syllabus_repo.delete_syllabus(course_id)
            
            if deleted:
                self.logger.info(f"Deleted syllabus for course {course_id}")
            else:
                self.logger.info(f"No syllabus found to delete for course {course_id}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Failed to delete syllabus for course {course_id}: {e}")
            raise
    
    async def update_syllabus(self, course_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in syllabus data.
        
        Args:
            course_id: Course identifier
            updates: Dictionary containing fields to update
            
        Returns:
            True if syllabus was updated, False if not found
            
        Raises:
            Exception: If update fails
        """
        try:
            # Add update timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            updated = await self.syllabus_repo.update_syllabus(course_id, updates)
            
            if updated:
                self.logger.info(f"Updated syllabus for course {course_id}")
            else:
                self.logger.info(f"No syllabus found to update for course {course_id}")
            
            return updated
            
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
            List of syllabus data
            
        Raises:
            Exception: If listing fails
        """
        try:
            syllabi = await self.syllabus_repo.list_syllabi(limit, offset)
            
            self.logger.info(f"Listed {len(syllabi)} syllabi")
            return syllabi
            
        except Exception as e:
            self.logger.error(f"Failed to list syllabi: {e}")
            raise
    
    async def search_syllabi(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search syllabi by content.
        
        Args:
            search_term: Term to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching syllabi
            
        Raises:
            Exception: If search fails
        """
        try:
            syllabi = await self.syllabus_repo.search_syllabi(search_term, limit)
            
            self.logger.info(f"Found {len(syllabi)} syllabi matching '{search_term}'")
            return syllabi
            
        except Exception as e:
            self.logger.error(f"Failed to search syllabi: {e}")
            raise
    
    async def validate_syllabus(self, syllabus_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate syllabus data structure and content.
        
        Args:
            syllabus_data: Syllabus data to validate
            
        Returns:
            Validation results with errors and warnings
            
        Raises:
            Exception: If validation fails
        """
        try:
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Check required fields
            required_fields = ['title', 'description', 'modules', 'objectives']
            for field in required_fields:
                if field not in syllabus_data:
                    validation_results['errors'].append(f"Missing required field: {field}")
                    validation_results['valid'] = False
            
            # Check modules structure
            if 'modules' in syllabus_data:
                modules = syllabus_data['modules']
                if not isinstance(modules, list):
                    validation_results['errors'].append("Modules must be a list")
                    validation_results['valid'] = False
                elif len(modules) == 0:
                    validation_results['warnings'].append("No modules defined")
                else:
                    # Check module structure
                    for i, module in enumerate(modules):
                        if not isinstance(module, dict):
                            validation_results['errors'].append(f"Module {i} must be a dictionary")
                            validation_results['valid'] = False
                        else:
                            module_required = ['title', 'description', 'topics']
                            for field in module_required:
                                if field not in module:
                                    validation_results['errors'].append(
                                        f"Module {i} missing required field: {field}"
                                    )
                                    validation_results['valid'] = False
            
            # Check objectives structure
            if 'objectives' in syllabus_data:
                objectives = syllabus_data['objectives']
                if not isinstance(objectives, list):
                    validation_results['warnings'].append("Objectives should be a list")
                elif len(objectives) == 0:
                    validation_results['warnings'].append("No learning objectives defined")
            
            self.logger.info(f"Validated syllabus: {validation_results}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Failed to validate syllabus: {e}")
            raise