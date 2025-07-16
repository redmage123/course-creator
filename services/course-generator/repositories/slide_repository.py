"""
Slide Repository

Database operations for slide management.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncpg
import json

from .base_repository import BaseRepository


class SlideRepository(BaseRepository):
    """
    Repository for slide data operations.
    
    Handles database operations for course slides.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize slide repository.
        
        Args:
            db_pool: Database connection pool
        """
        super().__init__(db_pool)
        self.logger = logging.getLogger(self.__class__.__name__)
    
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
            # Prepare data for database
            data = {
                'course_id': course_id,
                'slides_data': json.dumps(slides_data),
                'title': slides_data.get('course_title', 'Unknown Course'),
                'total_slides': slides_data.get('total_slides', 0),
                'generated_at': slides_data.get('generated_at'),
                'generation_method': slides_data.get('generation_method', 'unknown')
            }
            
            # Use upsert to save slides
            await self.upsert(
                table='slides',
                data=data,
                conflict_columns=['course_id']
            )
            
            self.logger.info(f"Saved slides for course {course_id}")
            return True
            
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
            query = """
            SELECT slides_data, title, total_slides, generated_at, generation_method,
                   created_at, updated_at
            FROM slides 
            WHERE course_id = $1
            """
            
            record = await self.fetch_one(query, course_id)
            
            if record:
                slides_data = json.loads(record['slides_data'])
                
                # Add metadata
                slides_data['title'] = record['title']
                slides_data['total_slides'] = record['total_slides']
                slides_data['generated_at'] = record['generated_at']
                slides_data['generation_method'] = record['generation_method']
                slides_data['created_at'] = record['created_at'].isoformat() if record['created_at'] else None
                slides_data['updated_at'] = record['updated_at'].isoformat() if record['updated_at'] else None
                
                return slides_data
            
            return None
            
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
            # Get current slides data
            current_slides = await self.get_slides(course_id)
            if not current_slides:
                return False
            
            # Update the slides data
            current_slides.update(updates)
            
            # Save the updated slides
            return await self.save_slides(course_id, current_slides)
            
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
            query = "DELETE FROM slides WHERE course_id = $1"
            await self.execute_query(query, course_id)
            
            self.logger.info(f"Deleted slides for course {course_id}")
            return True
            
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
            query = """
            SELECT course_id, title, total_slides, generated_at, generation_method,
                   created_at, updated_at
            FROM slides
            ORDER BY updated_at DESC
            LIMIT $1 OFFSET $2
            """
            
            records = await self.fetch_all(query, limit, offset)
            
            slides_list = []
            for record in records:
                slides_info = {
                    'course_id': record['course_id'],
                    'title': record['title'],
                    'total_slides': record['total_slides'],
                    'generated_at': record['generated_at'],
                    'generation_method': record['generation_method'],
                    'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                    'updated_at': record['updated_at'].isoformat() if record['updated_at'] else None
                }
                slides_list.append(slides_info)
            
            return slides_list
            
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
            query = """
            SELECT course_id, title, total_slides, generated_at, generation_method,
                   created_at, updated_at
            FROM slides
            WHERE title ILIKE $1 OR slides_data::text ILIKE $1
            ORDER BY updated_at DESC
            LIMIT $2
            """
            
            search_pattern = f"%{search_term}%"
            records = await self.fetch_all(query, search_pattern, limit)
            
            slides_list = []
            for record in records:
                slides_info = {
                    'course_id': record['course_id'],
                    'title': record['title'],
                    'total_slides': record['total_slides'],
                    'generated_at': record['generated_at'],
                    'generation_method': record['generation_method'],
                    'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                    'updated_at': record['updated_at'].isoformat() if record['updated_at'] else None
                }
                slides_list.append(slides_info)
            
            return slides_list
            
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
            slides_data = await self.get_slides(course_id)
            if not slides_data:
                return None
            
            slides = slides_data.get('slides', [])
            for slide in slides:
                if slide.get('slide_number') == slide_number:
                    return slide
            
            return None
            
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
            slides_data = await self.get_slides(course_id)
            if not slides_data:
                return []
            
            slides = slides_data.get('slides', [])
            module_slides = []
            
            for slide in slides:
                if slide.get('module_number') == module_number:
                    module_slides.append(slide)
            
            # Sort by slide number
            module_slides.sort(key=lambda x: x.get('slide_number', 0))
            
            return module_slides
            
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
            query = "SELECT total_slides FROM slides WHERE course_id = $1"
            record = await self.fetch_one(query, course_id)
            
            if record:
                return record['total_slides']
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error counting slides for course {course_id}: {e}")
            return 0