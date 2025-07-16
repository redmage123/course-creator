"""
Slide Generator

AI-powered slide generation for courses.
"""

import logging
from typing import Dict, Any, Optional, List
import json

from ..client import AIClient
from ..prompts import PromptTemplates


class SlideGenerator:
    """
    AI-powered slide generator.
    
    Handles generation of course slides from syllabus data.
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Initialize slide generator.
        
        Args:
            ai_client: AI client for content generation
        """
        self.ai_client = ai_client
        self.prompt_templates = PromptTemplates()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_from_syllabus(self, syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate slides from syllabus data.
        
        Args:
            syllabus_data: Syllabus data dictionary
            
        Returns:
            Generated slides data or None if generation fails
        """
        try:
            self.logger.info(f"Generating slides for course: {syllabus_data.get('title', 'Unknown')}")
            
            # Build slide generation prompt
            prompt = self.prompt_templates.build_slide_generation_prompt(syllabus_data)
            
            # Generate slides using AI
            response = await self.ai_client.generate_structured_content(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=6000,
                temperature=0.7,
                system_prompt=self.prompt_templates.get_slide_system_prompt()
            )
            
            if response:
                # Validate and enhance the response
                validated_slides = self._validate_and_enhance_slides(response, syllabus_data)
                
                if validated_slides:
                    self.logger.info("Successfully generated slides using AI")
                    return validated_slides
                else:
                    self.logger.warning("AI generated invalid slides structure")
                    return None
            else:
                self.logger.warning("AI failed to generate slides")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating slides: {e}")
            return None
    
    async def generate_for_module(self, 
                                syllabus_data: Dict[str, Any], 
                                module_number: int) -> Optional[Dict[str, Any]]:
        """
        Generate slides for a specific module.
        
        Args:
            syllabus_data: Syllabus data dictionary
            module_number: Module number to generate slides for
            
        Returns:
            Generated slides data or None if generation fails
        """
        try:
            modules = syllabus_data.get('modules', [])
            if module_number < 1 or module_number > len(modules):
                self.logger.error(f"Invalid module number: {module_number}")
                return None
            
            module = modules[module_number - 1]
            self.logger.info(f"Generating slides for module {module_number}: {module.get('title', 'Unknown')}")
            
            # Create a focused syllabus for this module
            focused_syllabus = syllabus_data.copy()
            focused_syllabus['modules'] = [module]
            
            # Generate slides for this module
            slides_data = await self.generate_from_syllabus(focused_syllabus)
            
            if slides_data:
                # Filter slides for this module only
                filtered_slides = []
                for slide in slides_data.get('slides', []):
                    if slide.get('module_number') == module_number or slide.get('slide_type') in ['title', 'overview']:
                        filtered_slides.append(slide)
                
                slides_data['slides'] = filtered_slides
                slides_data['total_slides'] = len(filtered_slides)
                
                return slides_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating slides for module {module_number}: {e}")
            return None
    
    def _validate_and_enhance_slides(self, 
                                   slides_data: Dict[str, Any], 
                                   syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and enhance AI-generated slides data.
        
        Args:
            slides_data: Raw slides data from AI
            syllabus_data: Original syllabus data
            
        Returns:
            Validated and enhanced slides data or None if invalid
        """
        try:
            # Required fields validation
            if 'slides' not in slides_data:
                self.logger.error("Missing required field: slides")
                return None
            
            slides = slides_data.get('slides', [])
            if not isinstance(slides, list) or len(slides) == 0:
                self.logger.error("Invalid slides structure")
                return None
            
            # Validate each slide
            for i, slide in enumerate(slides):
                if not isinstance(slide, dict):
                    self.logger.error(f"Slide {i} is not a dictionary")
                    return None
                
                slide_required = ['title', 'content']
                for field in slide_required:
                    if field not in slide:
                        self.logger.error(f"Slide {i} missing required field: {field}")
                        return None
                
                # Ensure slide has a slide_number
                if 'slide_number' not in slide:
                    slide['slide_number'] = i + 1
                
                # Ensure slide has a slide_type
                if 'slide_type' not in slide:
                    slide['slide_type'] = 'content'
                
                # Ensure slide has a module_number
                if 'module_number' not in slide:
                    slide['module_number'] = 1
            
            # Enhance with course info
            slides_data['course_title'] = syllabus_data.get('title', 'Unknown Course')
            slides_data['total_slides'] = len(slides)
            
            # Add metadata
            slides_data['generated_at'] = str(self._get_current_timestamp())
            slides_data['generation_method'] = 'ai'
            
            self.logger.info("Slides validation and enhancement completed")
            return slides_data
            
        except Exception as e:
            self.logger.error(f"Error validating slides: {e}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _extract_slide_structure(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract and analyze slide structure for validation.
        
        Args:
            slides: List of slide dictionaries
            
        Returns:
            Structure analysis results
        """
        structure = {
            'total_slides': len(slides),
            'slide_types': {},
            'modules_covered': set(),
            'slide_titles': [],
            'issues': []
        }
        
        for i, slide in enumerate(slides):
            try:
                structure['slide_titles'].append(slide.get('title', f'Slide {i+1}'))
                
                # Count slide types
                slide_type = slide.get('slide_type', 'content')
                structure['slide_types'][slide_type] = structure['slide_types'].get(slide_type, 0) + 1
                
                # Track modules covered
                module_number = slide.get('module_number', 1)
                structure['modules_covered'].add(module_number)
                
            except Exception as e:
                structure['issues'].append(f"Slide {i}: {str(e)}")
        
        structure['modules_covered'] = list(structure['modules_covered'])
        return structure