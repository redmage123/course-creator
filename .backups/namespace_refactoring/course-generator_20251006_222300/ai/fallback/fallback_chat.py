"""
Fallback Chat Generator

Provides fallback chat response generation when AI services are unavailable.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


class FallbackChatGenerator:
    """
    Fallback chat response generator.
    
    Provides basic chat responses using templates when AI services are unavailable.
    """
    
    def __init__(self):
        """Initialize fallback chat generator."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.common_responses = self._initialize_common_responses()
    
    async def generate_response(self, 
                              question: str, 
                              context: Dict[str, Any] = None,
                              conversation_history: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a response to a question using fallback templates.
        
        Args:
            question: User's question
            context: Course context information
            conversation_history: Previous conversation messages
            
        Returns:
            Generated response data or None if generation fails
        """
        try:
            self.logger.info(f"Generating fallback response for question: {question[:50]}...")
            
            # Generate template response
            response_text = self._create_template_response(question, context)
            
            if response_text:
                structured_response = {
                    'question': question,
                    'answer': response_text,
                    'context_used': bool(context),
                    'timestamp': datetime.now().isoformat(),
                    'generation_method': 'fallback'
                }
                
                # Add context information if available
                if context:
                    structured_response['course_context'] = {
                        'course_title': context.get('course_title', 'Unknown'),
                        'module_number': context.get('module_number'),
                        'topic': context.get('topic')
                    }
                
                self.logger.info("Successfully generated fallback response")
                return structured_response
            else:
                self.logger.error("Failed to generate fallback response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating fallback response: {e}")
            return None
    
    async def generate_explanation(self, 
                                 concept: str, 
                                 level: str = 'beginner',
                                 context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Generate an explanation for a concept using fallback templates.
        
        Args:
            concept: Concept to explain
            level: Difficulty level for explanation
            context: Course context information
            
        Returns:
            Generated explanation data or None if generation fails
        """
        try:
            self.logger.info(f"Generating fallback explanation for concept: {concept}")
            
            # Generate template explanation
            explanation_text = self._create_template_explanation(concept, level, context)
            
            if explanation_text:
                structured_explanation = {
                    'concept': concept,
                    'level': level,
                    'explanation': explanation_text,
                    'timestamp': datetime.now().isoformat(),
                    'generation_method': 'fallback'
                }
                
                # Add context information if available
                if context:
                    structured_explanation['course_context'] = {
                        'course_title': context.get('course_title', 'Unknown'),
                        'module_number': context.get('module_number'),
                        'topic': context.get('topic')
                    }
                
                self.logger.info("Successfully generated fallback explanation")
                return structured_explanation
            else:
                self.logger.error("Failed to generate fallback explanation")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating fallback explanation: {e}")
            return None
    
    async def generate_hint(self, 
                          exercise_context: Dict[str, Any], 
                          student_progress: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a hint for an exercise using fallback templates.
        
        Args:
            exercise_context: Exercise information
            student_progress: Student's current progress
            
        Returns:
            Generated hint data or None if generation fails
        """
        try:
            exercise_title = exercise_context.get('title', 'Unknown Exercise')
            self.logger.info(f"Generating fallback hint for exercise: {exercise_title}")
            
            # Generate template hint
            hint_text = self._create_template_hint(exercise_context, student_progress)
            
            if hint_text:
                structured_hint = {
                    'exercise_title': exercise_title,
                    'hint': hint_text,
                    'timestamp': datetime.now().isoformat(),
                    'generation_method': 'fallback'
                }
                
                # Add progress information if available
                if student_progress:
                    structured_hint['student_progress'] = student_progress
                
                self.logger.info("Successfully generated fallback hint")
                return structured_hint
            else:
                self.logger.error("Failed to generate fallback hint")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating fallback hint: {e}")
            return None
    
    def _initialize_common_responses(self) -> Dict[str, str]:
        """Initialize common response templates."""
        return {
            'greeting': "Hello! I'm here to help you with your course. What would you like to know?",
            'help_general': "I can help you with course content, exercises, and general questions. What specific topic would you like to explore?",
            'help_exercise': "For exercises, I can provide hints, explanations, and guidance. What exercise are you working on?",
            'help_concept': "I can explain concepts in different ways. What concept would you like me to clarify?",
            'unknown': "I'm not sure about that specific question, but I'm here to help with your learning. Could you rephrase your question or ask about a specific topic?",
            'error': "I'm sorry, I encountered an issue. Please try asking your question again or contact support if the problem persists.",
            'encouragement': "Great question! Keep up the good work with your learning.",
            'practice': "The best way to learn is through practice. Have you tried working through the exercises?",
            'resources': "There are many resources available to help you learn. Check the course materials and practice exercises."
        }
    
    def _create_template_response(self, question: str, context: Dict[str, Any] = None) -> str:
        """
        Create a template response based on the question.
        
        Args:
            question: User's question
            context: Course context information
            
        Returns:
            Template response text
        """
        question_lower = question.lower()
        
        # Greeting responses
        if any(word in question_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return self.common_responses['greeting']
        
        # Help requests
        if any(word in question_lower for word in ['help', 'assist', 'support']):
            if 'exercise' in question_lower:
                return self.common_responses['help_exercise']
            elif 'concept' in question_lower or 'explain' in question_lower:
                return self.common_responses['help_concept']
            else:
                return self.common_responses['help_general']
        
        # Question about understanding
        if any(word in question_lower for word in ['understand', 'confused', 'unclear', 'explain']):
            if context and context.get('course_title'):
                return f"I understand you're looking for clarification about {context.get('course_title')}. {self.common_responses['help_concept']}"
            else:
                return self.common_responses['help_concept']
        
        # Practice-related questions
        if any(word in question_lower for word in ['practice', 'exercise', 'homework', 'assignment']):
            return self.common_responses['practice']
        
        # Resource requests
        if any(word in question_lower for word in ['resource', 'material', 'reading', 'reference']):
            return self.common_responses['resources']
        
        # Encouraging responses for learning-related questions
        if any(word in question_lower for word in ['learn', 'study', 'master', 'improve']):
            return f"{self.common_responses['encouragement']} {self.common_responses['practice']}"
        
        # Default response for unknown questions
        return self.common_responses['unknown']
    
    def _create_template_explanation(self, concept: str, level: str, context: Dict[str, Any] = None) -> str:
        """
        Create a template explanation for a concept.
        
        Args:
            concept: Concept to explain
            level: Difficulty level
            context: Course context information
            
        Returns:
            Template explanation text
        """
        concept_lower = concept.lower()
        
        # Programming concepts
        if any(word in concept_lower for word in ['variable', 'variables']):
            if level == 'beginner':
                return "A variable is like a container that stores data. You can put different types of information in it, like numbers, text, or lists. Think of it as a labeled box where you can store and retrieve information later."
            else:
                return "Variables are named references to memory locations that store data. They have scope, lifetime, and type (in statically typed languages). Variables allow programs to manipulate data dynamically during execution."
        
        elif any(word in concept_lower for word in ['function', 'functions']):
            if level == 'beginner':
                return "A function is like a recipe or a set of instructions that performs a specific task. You give it some ingredients (inputs), it processes them, and gives you back a result (output). Functions help organize code and avoid repetition."
            else:
                return "Functions are reusable code blocks that encapsulate specific functionality. They promote modularity, reduce code duplication, and implement the DRY (Don't Repeat Yourself) principle. Functions can have parameters, return values, and local scope."
        
        elif any(word in concept_lower for word in ['loop', 'loops']):
            if level == 'beginner':
                return "A loop is a way to repeat code multiple times. Instead of writing the same code over and over, you can use a loop to do it automatically. It's like telling the computer 'keep doing this until I tell you to stop'."
            else:
                return "Loops are control structures that execute code repeatedly based on a condition. They include for loops (definite iteration), while loops (indefinite iteration), and various loop optimizations and patterns."
        
        # Web development concepts
        elif any(word in concept_lower for word in ['html']):
            return "HTML (HyperText Markup Language) is the standard markup language for creating web pages. It uses elements (tags) to structure content and define the meaning of different parts of a webpage."
        
        elif any(word in concept_lower for word in ['css']):
            return "CSS (Cascading Style Sheets) is used to style and layout web pages. It controls the appearance of HTML elements, including colors, fonts, spacing, positioning, and responsive design."
        
        # Data science concepts
        elif any(word in concept_lower for word in ['data', 'dataset']):
            return "Data is information that can be processed and analyzed to gain insights. A dataset is a collection of related data points, usually organized in rows and columns, that can be used for analysis and decision-making."
        
        # Generic explanation
        else:
            return f"The concept of '{concept}' is an important topic in this course. I recommend reviewing the course materials and practicing with examples to better understand this concept. If you need more specific information, please ask a more detailed question."
    
    def _create_template_hint(self, exercise_context: Dict[str, Any], student_progress: Dict[str, Any] = None) -> str:
        """
        Create a template hint for an exercise.
        
        Args:
            exercise_context: Exercise information
            student_progress: Student's current progress
            
        Returns:
            Template hint text
        """
        exercise_title = exercise_context.get('title', 'this exercise')
        difficulty = exercise_context.get('difficulty', 'medium')
        
        # Check if there are errors in student progress
        if student_progress:
            errors = student_progress.get('errors', [])
            if errors:
                return f"I see you're encountering some issues with {exercise_title}. Common problems include syntax errors, logic errors, or missing steps. Review your code carefully and check for typos or missing punctuation."
        
        # General hints based on difficulty
        if difficulty == 'easy':
            return f"For {exercise_title}, start with the basics. Read the instructions carefully, break the problem into small steps, and test your solution as you go. Don't be afraid to experiment!"
        
        elif difficulty == 'medium':
            return f"This is a moderate challenge. For {exercise_title}, think about the problem step by step. Consider what tools or concepts you've learned that might apply here. If you're stuck, try working through a simpler example first."
        
        else:  # hard
            return f"This is a challenging exercise. For {exercise_title}, consider breaking it down into smaller sub-problems. Think about similar problems you've solved before. Don't hesitate to look up documentation or examples for guidance."