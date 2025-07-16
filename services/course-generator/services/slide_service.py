"""
Slide Service

Business logic for slide generation and management.
"""

import logging
import sys
import os
from typing import Dict, Any, Optional, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.slide_repository import SlideRepository
from ai.generators.slide_generator import SlideGenerator
from ai.fallback.fallback_slide import FallbackSlideGenerator


class SlideService:
    """
    Service for slide generation and management.
    
    Handles business logic for slide operations including generation,
    storage, and retrieval.
    """
    
    def __init__(self, 
                 slide_repository: SlideRepository,
                 slide_generator: SlideGenerator,
                 fallback_generator: FallbackSlideGenerator = None):
        """
        Initialize slide service.
        
        Args:
            slide_repository: Repository for slide data operations
            slide_generator: AI-powered slide generator
            fallback_generator: Fallback slide generator (optional)
        """
        self.slide_repository = slide_repository
        self.slide_generator = slide_generator
        self.fallback_generator = fallback_generator
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_slides(self, syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate slides from syllabus data.
        
        Args:
            syllabus_data: Syllabus data to generate slides from
            
        Returns:
            Generated slides data or None if generation fails
        """
        try:
            self.logger.info("Generating slides from syllabus")
            
            # Try AI generation first
            slides_data = await self.slide_generator.generate_from_syllabus(syllabus_data)
            
            # Fall back to template generation if AI fails
            if not slides_data and self.fallback_generator:
                self.logger.warning("AI slide generation failed, using fallback")
                slides_data = await self.fallback_generator.generate_from_syllabus(syllabus_data)
            
            return slides_data
            
        except Exception as e:
            self.logger.error(f"Error generating slides: {e}")
            return None
    
    async def generate_slides_for_module(self, 
                                       syllabus_data: Dict[str, Any], 
                                       module_number: int) -> Optional[Dict[str, Any]]:
        """
        Generate slides for a specific module.
        
        Args:
            syllabus_data: Syllabus data
            module_number: Module number to generate slides for
            
        Returns:
            Generated slides data or None if generation fails
        """
        try:
            self.logger.info(f"Generating slides for module {module_number}")
            
            # Try AI generation first
            slides_data = await self.slide_generator.generate_for_module(syllabus_data, module_number)
            
            # Fall back to template generation if AI fails
            if not slides_data and self.fallback_generator:
                self.logger.warning("AI slide generation failed, using fallback")
                slides_data = await self.fallback_generator.generate_for_module(syllabus_data, module_number)
            
            return slides_data
            
        except Exception as e:
            self.logger.error(f"Error generating slides for module {module_number}: {e}")
            return None
    
    async def save_slides(self, course_id: str, slides_data: Dict[str, Any]) -> bool:
        """
        Save slides data for a course.
        
        Args:
            course_id: Course identifier
            slides_data: Slides data to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            return await self.slide_repository.save_slides(course_id, slides_data)
            
        except Exception as e:
            self.logger.error(f"Error saving slides for course {course_id}: {e}")
            return False
    
    async def get_slides(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve slides data for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Slides data or None if not found
        """
        try:
            return await self.slide_repository.get_slides(course_id)
            
        except Exception as e:
            self.logger.error(f"Error retrieving slides for course {course_id}: {e}")
            return None
    
    async def update_slides(self, course_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in slides data.
        
        Args:
            course_id: Course identifier
            updates: Dictionary containing fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            return await self.slide_repository.update_slides(course_id, updates)
            
        except Exception as e:
            self.logger.error(f"Error updating slides for course {course_id}: {e}")
            return False
    
    async def delete_slides(self, course_id: str) -> bool:
        """
        Delete slides data for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            return await self.slide_repository.delete_slides(course_id)
            
        except Exception as e:
            self.logger.error(f"Error deleting slides for course {course_id}: {e}")
            return False
    
    async def list_slides(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all slides with pagination.
        
        Args:
            limit: Maximum number of slides to return
            offset: Number of slides to skip
            
        Returns:
            List of slides data
        """
        try:
            return await self.slide_repository.list_slides(limit, offset)
            
        except Exception as e:
            self.logger.error(f"Error listing slides: {e}")
            return []
    
    async def search_slides(self, search_term: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search slides by title or content.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching slides data
        """
        try:
            return await self.slide_repository.search_slides(search_term, limit)
            
        except Exception as e:
            self.logger.error(f"Error searching slides: {e}")
            return []
    
    async def get_slide_by_number(self, course_id: str, slide_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific slide by its number.
        
        Args:
            course_id: Course identifier
            slide_number: Slide number
            
        Returns:
            Slide data or None if not found
        """
        try:
            return await self.slide_repository.get_slide_by_number(course_id, slide_number)
            
        except Exception as e:
            self.logger.error(f"Error getting slide {slide_number} for course {course_id}: {e}")
            return None
    
    async def get_slides_by_module(self, course_id: str, module_number: int) -> List[Dict[str, Any]]:
        """
        Get all slides for a specific module.
        
        Args:
            course_id: Course identifier
            module_number: Module number
            
        Returns:
            List of slide data for the module
        """
        try:
            return await self.slide_repository.get_slides_by_module(course_id, module_number)
            
        except Exception as e:
            self.logger.error(f"Error getting slides for module {module_number} in course {course_id}: {e}")
            return []
    
    async def count_slides(self, course_id: str) -> int:
        """
        Count the total number of slides for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Total number of slides
        """
        try:
            return await self.slide_repository.count_slides(course_id)
            
        except Exception as e:
            self.logger.error(f"Error counting slides for course {course_id}: {e}")
            return 0
    
    async def regenerate_slides(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Regenerate slides for a course using existing syllabus.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Regenerated slides data or None if regeneration fails
        """
        try:
            # Get existing syllabus (would need syllabus service)
            # For now, return None to indicate not implemented
            self.logger.warning("Regenerate slides not implemented - requires syllabus service")
            return None
            
        except Exception as e:
            self.logger.error(f"Error regenerating slides for course {course_id}: {e}")
            return None
    
    async def validate_slides(self, slides_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate slides data structure and content.
        
        Args:
            slides_data: Slides data to validate
            
        Returns:
            Validation results
        """
        try:
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Check required fields
            required_fields = ['slides', 'course_title']
            for field in required_fields:
                if field not in slides_data:
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Missing required field: {field}")
            
            # Validate slides structure
            slides = slides_data.get('slides', [])
            if not isinstance(slides, list):
                validation_results['valid'] = False
                validation_results['errors'].append("Slides must be a list")
            elif len(slides) == 0:
                validation_results['warnings'].append("No slides found")
            
            # Validate individual slides
            for i, slide in enumerate(slides):
                if not isinstance(slide, dict):
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Slide {i+1} must be a dictionary")
                    continue
                
                # Check required slide fields
                slide_required = ['title', 'content']
                for field in slide_required:
                    if field not in slide:
                        validation_results['valid'] = False
                        validation_results['errors'].append(f"Slide {i+1} missing required field: {field}")
                
                # Check slide content length
                content = slide.get('content', '')
                if len(content) > 2000:
                    validation_results['warnings'].append(f"Slide {i+1} content is very long")
                elif len(content) < 10:
                    validation_results['warnings'].append(f"Slide {i+1} content is very short")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating slides: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }