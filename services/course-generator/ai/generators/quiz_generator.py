"""
Quiz Generator

AI-powered quiz generation for courses.
"""

import logging
from typing import Dict, Any, Optional, List
import json

from ..client import AIClient
from ..prompts import PromptTemplates


class QuizGenerator:
    """
    AI-powered quiz generator.
    
    Handles generation of comprehensive quizzes from syllabus data.
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Initialize quiz generator.
        
        Args:
            ai_client: AI client for content generation
        """
        self.ai_client = ai_client
        self.prompt_templates = PromptTemplates()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_from_syllabus(self, syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate quizzes from syllabus data.
        
        Args:
            syllabus_data: Syllabus data dictionary
            
        Returns:
            Generated quizzes data or None if generation fails
        """
        try:
            self.logger.info(f"Generating quizzes for course: {syllabus_data.get('title', 'Unknown')}")
            
            # Build quiz generation prompt
            prompt = self.prompt_templates.build_quiz_generation_prompt(syllabus_data)
            
            # Generate quizzes using AI
            response = await self.ai_client.generate_structured_content(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=8000,
                temperature=0.7,
                system_prompt=self.prompt_templates.get_quiz_system_prompt()
            )
            
            if response:
                # Validate and enhance the response
                validated_quizzes = self._validate_and_enhance_quizzes(response, syllabus_data)
                
                if validated_quizzes:
                    self.logger.info("Successfully generated quizzes using AI")
                    return validated_quizzes
                else:
                    self.logger.warning("AI generated invalid quizzes structure")
                    return None
            else:
                self.logger.warning("AI failed to generate quizzes")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating quizzes: {e}")
            return None
    
    async def generate_for_module(self, 
                                syllabus_data: Dict[str, Any], 
                                module_number: int) -> Optional[Dict[str, Any]]:
        """
        Generate quiz for a specific module.
        
        Args:
            syllabus_data: Syllabus data dictionary
            module_number: Module number to generate quiz for
            
        Returns:
            Generated quiz data or None if generation fails
        """
        try:
            modules = syllabus_data.get('modules', [])
            if module_number < 1 or module_number > len(modules):
                self.logger.error(f"Invalid module number: {module_number}")
                return None
            
            module = modules[module_number - 1]
            self.logger.info(f"Generating quiz for module {module_number}: {module.get('title', 'Unknown')}")
            
            # Create a focused syllabus for this module
            focused_syllabus = syllabus_data.copy()
            focused_syllabus['modules'] = [module]
            
            # Generate quiz for this module
            quizzes_data = await self.generate_from_syllabus(focused_syllabus)
            
            if quizzes_data:
                # Filter quizzes for this module only
                filtered_quizzes = []
                for quiz in quizzes_data.get('quizzes', []):
                    if quiz.get('module_number') == module_number:
                        filtered_quizzes.append(quiz)
                
                quizzes_data['quizzes'] = filtered_quizzes
                quizzes_data['total_quizzes'] = len(filtered_quizzes)
                
                return quizzes_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating quiz for module {module_number}: {e}")
            return None
    
    async def generate_practice_quiz(self, 
                                   syllabus_data: Dict[str, Any], 
                                   difficulty: str = 'medium',
                                   num_questions: int = 10) -> Optional[Dict[str, Any]]:
        """
        Generate a practice quiz with specific parameters.
        
        Args:
            syllabus_data: Syllabus data dictionary
            difficulty: Quiz difficulty level
            num_questions: Number of questions to generate
            
        Returns:
            Generated practice quiz data or None if generation fails
        """
        try:
            self.logger.info(f"Generating practice quiz with {num_questions} questions at {difficulty} level")
            
            # Generate full quiz set first
            quizzes_data = await self.generate_from_syllabus(syllabus_data)
            
            if quizzes_data:
                # Create a practice quiz by combining questions from all modules
                practice_questions = []
                all_quizzes = quizzes_data.get('quizzes', [])
                
                # Collect questions from all quizzes
                for quiz in all_quizzes:
                    for question in quiz.get('questions', []):
                        if question.get('difficulty', 'medium') == difficulty:
                            practice_questions.append(question)
                
                # Limit to requested number of questions
                if len(practice_questions) > num_questions:
                    practice_questions = practice_questions[:num_questions]
                
                # Create practice quiz structure
                practice_quiz = {
                    'course_title': syllabus_data.get('title', 'Unknown Course'),
                    'total_quizzes': 1,
                    'quizzes': [{
                        'id': 'practice_quiz',
                        'title': f'Practice Quiz - {difficulty.title()} Level',
                        'description': f'Practice quiz covering all course topics at {difficulty} difficulty',
                        'module_number': 0,  # 0 indicates cross-module quiz
                        'duration': max(30, len(practice_questions) * 2),  # 2 minutes per question, min 30
                        'difficulty': difficulty,
                        'questions': practice_questions
                    }]
                }
                
                return practice_quiz
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating practice quiz: {e}")
            return None
    
    def _validate_and_enhance_quizzes(self, 
                                    quizzes_data: Dict[str, Any], 
                                    syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and enhance AI-generated quizzes data.
        
        Args:
            quizzes_data: Raw quizzes data from AI
            syllabus_data: Original syllabus data
            
        Returns:
            Validated and enhanced quizzes data or None if invalid
        """
        try:
            # Required fields validation
            if 'quizzes' not in quizzes_data:
                self.logger.error("Missing required field: quizzes")
                return None
            
            quizzes = quizzes_data.get('quizzes', [])
            if not isinstance(quizzes, list) or len(quizzes) == 0:
                self.logger.error("Invalid quizzes structure")
                return None
            
            # Validate each quiz
            for i, quiz in enumerate(quizzes):
                if not isinstance(quiz, dict):
                    self.logger.error(f"Quiz {i} is not a dictionary")
                    return None
                
                quiz_required = ['title', 'questions']
                for field in quiz_required:
                    if field not in quiz:
                        self.logger.error(f"Quiz {i} missing required field: {field}")
                        return None
                
                # Ensure quiz has an id
                if 'id' not in quiz:
                    quiz['id'] = f"quiz_{i+1}"
                
                # Ensure quiz has a module_number
                if 'module_number' not in quiz:
                    quiz['module_number'] = i + 1
                
                # Ensure quiz has a difficulty level
                if 'difficulty' not in quiz:
                    quiz['difficulty'] = 'beginner'
                
                # Ensure quiz has a duration
                if 'duration' not in quiz:
                    quiz['duration'] = len(quiz.get('questions', [])) * 2  # 2 minutes per question
                
                # Validate questions
                questions = quiz.get('questions', [])
                if not isinstance(questions, list) or len(questions) == 0:
                    self.logger.error(f"Quiz {i} has invalid questions structure")
                    return None
                
                # Validate each question
                for j, question in enumerate(questions):
                    if not isinstance(question, dict):
                        self.logger.error(f"Quiz {i}, Question {j} is not a dictionary")
                        return None
                    
                    question_required = ['question', 'options', 'correct_answer']
                    for field in question_required:
                        if field not in question:
                            self.logger.error(f"Quiz {i}, Question {j} missing required field: {field}")
                            return None
                    
                    # Validate options
                    options = question.get('options', [])
                    if not isinstance(options, list) or len(options) < 2:
                        self.logger.error(f"Quiz {i}, Question {j} has invalid options")
                        return None
                    
                    # Validate correct_answer
                    correct_answer = question.get('correct_answer')
                    if not isinstance(correct_answer, int) or correct_answer < 0 or correct_answer >= len(options):
                        self.logger.error(f"Quiz {i}, Question {j} has invalid correct_answer")
                        return None
                    
                    # Ensure question has explanation
                    if 'explanation' not in question:
                        question['explanation'] = 'No explanation provided'
                    
                    # Ensure question has topic_tested
                    if 'topic_tested' not in question:
                        question['topic_tested'] = 'General knowledge'
                    
                    # Ensure question has difficulty
                    if 'difficulty' not in question:
                        question['difficulty'] = 'medium'
            
            # Enhance with course info
            quizzes_data['course_title'] = syllabus_data.get('title', 'Unknown Course')
            quizzes_data['total_quizzes'] = len(quizzes)
            
            # Add metadata
            quizzes_data['generated_at'] = str(self._get_current_timestamp())
            quizzes_data['generation_method'] = 'ai'
            
            self.logger.info("Quizzes validation and enhancement completed")
            return quizzes_data
            
        except Exception as e:
            self.logger.error(f"Error validating quizzes: {e}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _extract_quiz_structure(self, quizzes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract and analyze quiz structure for validation.
        
        Args:
            quizzes: List of quiz dictionaries
            
        Returns:
            Structure analysis results
        """
        structure = {
            'total_quizzes': len(quizzes),
            'total_questions': 0,
            'difficulty_levels': {},
            'modules_covered': set(),
            'quiz_titles': [],
            'question_types': {},
            'issues': []
        }
        
        for i, quiz in enumerate(quizzes):
            try:
                structure['quiz_titles'].append(quiz.get('title', f'Quiz {i+1}'))
                
                # Count questions
                questions = quiz.get('questions', [])
                structure['total_questions'] += len(questions)
                
                # Count difficulty levels
                difficulty = quiz.get('difficulty', 'beginner')
                structure['difficulty_levels'][difficulty] = structure['difficulty_levels'].get(difficulty, 0) + 1
                
                # Track modules covered
                module_number = quiz.get('module_number', 1)
                structure['modules_covered'].add(module_number)
                
                # Analyze question types
                for question in questions:
                    options = question.get('options', [])
                    if len(options) == 2:
                        question_type = 'true_false'
                    elif len(options) <= 4:
                        question_type = 'multiple_choice'
                    else:
                        question_type = 'multi_select'
                    
                    structure['question_types'][question_type] = structure['question_types'].get(question_type, 0) + 1
                
            except Exception as e:
                structure['issues'].append(f"Quiz {i}: {str(e)}")
        
        structure['modules_covered'] = list(structure['modules_covered'])
        return structure