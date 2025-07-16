"""
Syllabus Generator

AI-powered syllabus generation and refinement.
"""

import logging
from typing import Dict, Any, Optional
import json

from ..client import AIClient
from ..prompts import PromptTemplates


class SyllabusGenerator:
    """
    AI-powered syllabus generator.
    
    Handles generation and refinement of course syllabi using AI.
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Initialize syllabus generator.
        
        Args:
            ai_client: AI client for content generation
        """
        self.ai_client = ai_client
        self.prompt_templates = PromptTemplates()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_from_course_info(self, course_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate syllabus from course information.
        
        Args:
            course_info: Dictionary containing course information
            
        Returns:
            Generated syllabus data or None if generation fails
        """
        try:
            self.logger.info(f"Generating syllabus for course: {course_info.get('title', 'Unknown')}")
            
            # Build generation prompt
            prompt = self.prompt_templates.build_syllabus_generation_prompt(course_info)
            
            # Generate syllabus using AI
            response = await self.ai_client.generate_structured_content(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0.7,
                system_prompt=self.prompt_templates.get_syllabus_system_prompt()
            )
            
            if response:
                # Validate and enhance the response
                validated_syllabus = self._validate_and_enhance_syllabus(response, course_info)
                
                if validated_syllabus:
                    self.logger.info("Successfully generated syllabus using AI")
                    return validated_syllabus
                else:
                    self.logger.warning("AI generated invalid syllabus structure")
                    return None
            else:
                self.logger.warning("AI failed to generate syllabus")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating syllabus: {e}")
            return None
    
    async def refine_syllabus(self, 
                            existing_syllabus: Dict[str, Any], 
                            feedback: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Refine existing syllabus based on feedback.
        
        Args:
            existing_syllabus: Current syllabus data
            feedback: Refinement feedback
            
        Returns:
            Refined syllabus data or None if refinement fails
        """
        try:
            self.logger.info("Refining syllabus with AI")
            
            # Build refinement prompt
            prompt = self.prompt_templates.build_syllabus_refinement_prompt(
                existing_syllabus, 
                feedback
            )
            
            # Refine syllabus using AI
            response = await self.ai_client.generate_structured_content(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0.7,
                system_prompt=self.prompt_templates.get_syllabus_system_prompt()
            )
            
            if response:
                # Validate and enhance the response
                validated_syllabus = self._validate_and_enhance_syllabus(response)
                
                if validated_syllabus:
                    self.logger.info("Successfully refined syllabus using AI")
                    return validated_syllabus
                else:
                    self.logger.warning("AI generated invalid refined syllabus structure")
                    return None
            else:
                self.logger.warning("AI failed to refine syllabus")
                return None
                
        except Exception as e:
            self.logger.error(f"Error refining syllabus: {e}")
            return None
    
    def _validate_and_enhance_syllabus(self, 
                                     syllabus_data: Dict[str, Any], 
                                     course_info: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Validate and enhance AI-generated syllabus data.
        
        Args:
            syllabus_data: Raw syllabus data from AI
            course_info: Original course information (optional)
            
        Returns:
            Validated and enhanced syllabus data or None if invalid
        """
        try:
            # Required fields validation
            required_fields = ['title', 'description', 'modules']
            for field in required_fields:
                if field not in syllabus_data:
                    self.logger.error(f"Missing required field: {field}")
                    return None
            
            # Validate modules structure
            modules = syllabus_data.get('modules', [])
            if not isinstance(modules, list) or len(modules) == 0:
                self.logger.error("Invalid modules structure")
                return None
            
            # Validate each module
            for i, module in enumerate(modules):
                if not isinstance(module, dict):
                    self.logger.error(f"Module {i} is not a dictionary")
                    return None
                
                module_required = ['title', 'description']
                for field in module_required:
                    if field not in module:
                        self.logger.error(f"Module {i} missing required field: {field}")
                        return None
                
                # Ensure module has a module_number
                if 'module_number' not in module:
                    module['module_number'] = i + 1
                
                # Ensure module has topics (even if empty)
                if 'topics' not in module:
                    module['topics'] = []
                
                # Ensure module has objectives (even if empty)
                if 'objectives' not in module:
                    module['objectives'] = []
            
            # Enhance with course info if provided
            if course_info:
                # Override with original course info where appropriate
                if 'title' in course_info:
                    syllabus_data['title'] = course_info['title']
                if 'description' in course_info:
                    syllabus_data['description'] = course_info['description']
                if 'level' in course_info:
                    syllabus_data['level'] = course_info['level']
                if 'duration' in course_info:
                    syllabus_data['duration'] = course_info['duration']
                if 'objectives' in course_info:
                    syllabus_data['objectives'] = course_info['objectives']
                if 'prerequisites' in course_info:
                    syllabus_data['prerequisites'] = course_info['prerequisites']
                if 'target_audience' in course_info:
                    syllabus_data['target_audience'] = course_info['target_audience']
            
            # Ensure all required fields have defaults
            syllabus_data.setdefault('level', 'beginner')
            syllabus_data.setdefault('objectives', [])
            syllabus_data.setdefault('prerequisites', [])
            syllabus_data.setdefault('target_audience', '')
            
            self.logger.info("Syllabus validation and enhancement completed")
            return syllabus_data
            
        except Exception as e:
            self.logger.error(f"Error validating syllabus: {e}")
            return None
    
    def _extract_module_structure(self, modules: list) -> Dict[str, Any]:
        """
        Extract and analyze module structure for validation.
        
        Args:
            modules: List of module dictionaries
            
        Returns:
            Structure analysis results
        """
        structure = {
            'total_modules': len(modules),
            'total_topics': 0,
            'total_duration': 0,
            'module_titles': [],
            'issues': []
        }
        
        for i, module in enumerate(modules):
            try:
                structure['module_titles'].append(module.get('title', f'Module {i+1}'))
                
                # Count topics
                topics = module.get('topics', [])
                structure['total_topics'] += len(topics)
                
                # Sum duration if available
                duration = module.get('duration', 0)
                if isinstance(duration, (int, float)):
                    structure['total_duration'] += duration
                
            except Exception as e:
                structure['issues'].append(f"Module {i}: {str(e)}")
        
        return structure