"""
Exercise Generator

AI-powered exercise generation for courses.
"""

import logging
from typing import Dict, Any, Optional, List
import json

from ..client import AIClient
from ..prompts import PromptTemplates


class ExerciseGenerator:
    """
    AI-powered exercise generator.
    
    Handles generation of practical exercises from syllabus data.
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Initialize exercise generator.
        
        Args:
            ai_client: AI client for content generation
        """
        self.ai_client = ai_client
        self.prompt_templates = PromptTemplates()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_from_syllabus(self, 
                                   syllabus_data: Dict[str, Any], 
                                   topic: str = None) -> Optional[Dict[str, Any]]:
        """
        Generate exercises from syllabus data.
        
        Args:
            syllabus_data: Syllabus data dictionary
            topic: Specific topic to focus on (optional)
            
        Returns:
            Generated exercises data or None if generation fails
        """
        try:
            course_title = syllabus_data.get('title', 'Unknown')
            focus_text = f" for topic: {topic}" if topic else ""
            self.logger.info(f"Generating exercises for course: {course_title}{focus_text}")
            
            # Build exercise generation prompt
            prompt = self.prompt_templates.build_exercise_generation_prompt(syllabus_data, topic)
            
            # Generate exercises using AI
            response = await self.ai_client.generate_structured_content(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=6000,
                temperature=0.7,
                system_prompt=self.prompt_templates.get_exercise_system_prompt()
            )
            
            if response:
                # Validate and enhance the response
                validated_exercises = self._validate_and_enhance_exercises(response, syllabus_data)
                
                if validated_exercises:
                    self.logger.info("Successfully generated exercises using AI")
                    return validated_exercises
                else:
                    self.logger.warning("AI generated invalid exercises structure")
                    return None
            else:
                self.logger.warning("AI failed to generate exercises")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating exercises: {e}")
            return None
    
    async def generate_for_module(self, 
                                syllabus_data: Dict[str, Any], 
                                module_number: int) -> Optional[Dict[str, Any]]:
        """
        Generate exercises for a specific module.
        
        Args:
            syllabus_data: Syllabus data dictionary
            module_number: Module number to generate exercises for
            
        Returns:
            Generated exercises data or None if generation fails
        """
        try:
            modules = syllabus_data.get('modules', [])
            if module_number < 1 or module_number > len(modules):
                self.logger.error(f"Invalid module number: {module_number}")
                return None
            
            module = modules[module_number - 1]
            self.logger.info(f"Generating exercises for module {module_number}: {module.get('title', 'Unknown')}")
            
            # Create a focused syllabus for this module
            focused_syllabus = syllabus_data.copy()
            focused_syllabus['modules'] = [module]
            
            # Generate exercises for this module
            exercises_data = await self.generate_from_syllabus(focused_syllabus)
            
            if exercises_data:
                # Ensure all exercises are tagged with correct module number
                for exercise in exercises_data.get('exercises', []):
                    exercise['module_number'] = module_number
                
                return exercises_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating exercises for module {module_number}: {e}")
            return None
    
    async def generate_for_topic(self, 
                               syllabus_data: Dict[str, Any], 
                               topic_title: str) -> Optional[Dict[str, Any]]:
        """
        Generate exercises for a specific topic.
        
        Args:
            syllabus_data: Syllabus data dictionary
            topic_title: Specific topic to generate exercises for
            
        Returns:
            Generated exercises data or None if generation fails
        """
        try:
            self.logger.info(f"Generating exercises for topic: {topic_title}")
            
            # Generate exercises focused on this topic
            exercises_data = await self.generate_from_syllabus(syllabus_data, topic_title)
            
            if exercises_data:
                # Filter exercises to focus on the specific topic
                filtered_exercises = []
                for exercise in exercises_data.get('exercises', []):
                    if topic_title.lower() in exercise.get('title', '').lower() or \
                       topic_title.lower() in exercise.get('description', '').lower():
                        filtered_exercises.append(exercise)
                
                exercises_data['exercises'] = filtered_exercises
                exercises_data['total_exercises'] = len(filtered_exercises)
                
                return exercises_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating exercises for topic {topic_title}: {e}")
            return None
    
    def _validate_and_enhance_exercises(self, 
                                      exercises_data: Dict[str, Any], 
                                      syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and enhance AI-generated exercises data.
        
        Args:
            exercises_data: Raw exercises data from AI
            syllabus_data: Original syllabus data
            
        Returns:
            Validated and enhanced exercises data or None if invalid
        """
        try:
            # Required fields validation
            if 'exercises' not in exercises_data:
                self.logger.error("Missing required field: exercises")
                return None
            
            exercises = exercises_data.get('exercises', [])
            if not isinstance(exercises, list) or len(exercises) == 0:
                self.logger.error("Invalid exercises structure")
                return None
            
            # Validate each exercise
            for i, exercise in enumerate(exercises):
                if not isinstance(exercise, dict):
                    self.logger.error(f"Exercise {i} is not a dictionary")
                    return None
                
                exercise_required = ['title', 'description']
                for field in exercise_required:
                    if field not in exercise:
                        self.logger.error(f"Exercise {i} missing required field: {field}")
                        return None
                
                # Ensure exercise has an id
                if 'id' not in exercise:
                    exercise['id'] = f"exercise_{i+1}"
                
                # Ensure exercise has a module_number
                if 'module_number' not in exercise:
                    exercise['module_number'] = 1
                
                # Ensure exercise has a difficulty level
                if 'difficulty' not in exercise:
                    exercise['difficulty'] = 'medium'
                
                # Ensure exercise has starter_code (even if empty)
                if 'starter_code' not in exercise:
                    exercise['starter_code'] = ''
                
                # Ensure exercise has solution
                if 'solution' not in exercise:
                    exercise['solution'] = 'Solution not provided'
                
                # Ensure exercise has instructions
                if 'instructions' not in exercise:
                    exercise['instructions'] = 'Instructions not provided'
            
            # Enhance with course info
            exercises_data['course_title'] = syllabus_data.get('title', 'Unknown Course')
            exercises_data['total_exercises'] = len(exercises)
            
            # Add metadata
            exercises_data['generated_at'] = str(self._get_current_timestamp())
            exercises_data['generation_method'] = 'ai'
            
            self.logger.info("Exercises validation and enhancement completed")
            return exercises_data
            
        except Exception as e:
            self.logger.error(f"Error validating exercises: {e}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _extract_exercise_structure(self, exercises: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract and analyze exercise structure for validation.
        
        Args:
            exercises: List of exercise dictionaries
            
        Returns:
            Structure analysis results
        """
        structure = {
            'total_exercises': len(exercises),
            'difficulty_levels': {},
            'modules_covered': set(),
            'exercise_titles': [],
            'has_starter_code': 0,
            'has_solutions': 0,
            'issues': []
        }
        
        for i, exercise in enumerate(exercises):
            try:
                structure['exercise_titles'].append(exercise.get('title', f'Exercise {i+1}'))
                
                # Count difficulty levels
                difficulty = exercise.get('difficulty', 'medium')
                structure['difficulty_levels'][difficulty] = structure['difficulty_levels'].get(difficulty, 0) + 1
                
                # Track modules covered
                module_number = exercise.get('module_number', 1)
                structure['modules_covered'].add(module_number)
                
                # Count exercises with starter code
                if exercise.get('starter_code'):
                    structure['has_starter_code'] += 1
                
                # Count exercises with solutions
                if exercise.get('solution'):
                    structure['has_solutions'] += 1
                
            except Exception as e:
                structure['issues'].append(f"Exercise {i}: {str(e)}")
        
        structure['modules_covered'] = list(structure['modules_covered'])
        return structure