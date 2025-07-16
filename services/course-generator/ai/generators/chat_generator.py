"""
Chat Generator

AI-powered chat response generation for course interactions.
"""

import logging
from typing import Dict, Any, Optional, List
import json

from ..client import AIClient
from ..prompts import PromptTemplates


class ChatGenerator:
    """
    AI-powered chat response generator.
    
    Handles generation of contextual responses for course-related questions.
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Initialize chat generator.
        
        Args:
            ai_client: AI client for content generation
        """
        self.ai_client = ai_client
        self.prompt_templates = PromptTemplates()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_response(self, 
                              question: str, 
                              context: Dict[str, Any] = None,
                              conversation_history: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a contextual response to a question.
        
        Args:
            question: User's question
            context: Course context information
            conversation_history: Previous conversation messages
            
        Returns:
            Generated response data or None if generation fails
        """
        try:
            self.logger.info(f"Generating chat response for question: {question[:50]}...")
            
            # Build context-aware prompt
            prompt = self._build_chat_prompt(question, context, conversation_history)
            
            # Generate response using AI
            response = await self.ai_client.generate_content(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.7,
                system_prompt=self._get_chat_system_prompt()
            )
            
            if response:
                # Structure the response
                structured_response = {
                    'question': question,
                    'answer': response,
                    'context_used': bool(context),
                    'timestamp': self._get_current_timestamp(),
                    'generation_method': 'ai'
                }
                
                # Add context information if available
                if context:
                    structured_response['course_context'] = {
                        'course_title': context.get('course_title', 'Unknown'),
                        'module_number': context.get('module_number'),
                        'topic': context.get('topic')
                    }
                
                self.logger.info("Successfully generated chat response using AI")
                return structured_response
            else:
                self.logger.warning("AI failed to generate chat response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating chat response: {e}")
            return None
    
    async def generate_explanation(self, 
                                 concept: str, 
                                 level: str = 'beginner',
                                 context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Generate an explanation for a specific concept.
        
        Args:
            concept: Concept to explain
            level: Difficulty level for explanation
            context: Course context information
            
        Returns:
            Generated explanation data or None if generation fails
        """
        try:
            self.logger.info(f"Generating explanation for concept: {concept}")
            
            # Build explanation prompt
            prompt = self._build_explanation_prompt(concept, level, context)
            
            # Generate explanation using AI
            response = await self.ai_client.generate_content(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                temperature=0.7,
                system_prompt=self._get_explanation_system_prompt()
            )
            
            if response:
                # Structure the explanation
                structured_explanation = {
                    'concept': concept,
                    'level': level,
                    'explanation': response,
                    'timestamp': self._get_current_timestamp(),
                    'generation_method': 'ai'
                }
                
                # Add context information if available
                if context:
                    structured_explanation['course_context'] = {
                        'course_title': context.get('course_title', 'Unknown'),
                        'module_number': context.get('module_number'),
                        'topic': context.get('topic')
                    }
                
                self.logger.info("Successfully generated explanation using AI")
                return structured_explanation
            else:
                self.logger.warning("AI failed to generate explanation")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating explanation: {e}")
            return None
    
    async def generate_hint(self, 
                          exercise_context: Dict[str, Any], 
                          student_progress: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a hint for an exercise.
        
        Args:
            exercise_context: Exercise information
            student_progress: Student's current progress
            
        Returns:
            Generated hint data or None if generation fails
        """
        try:
            exercise_title = exercise_context.get('title', 'Unknown Exercise')
            self.logger.info(f"Generating hint for exercise: {exercise_title}")
            
            # Build hint prompt
            prompt = self._build_hint_prompt(exercise_context, student_progress)
            
            # Generate hint using AI
            response = await self.ai_client.generate_content(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.7,
                system_prompt=self._get_hint_system_prompt()
            )
            
            if response:
                # Structure the hint
                structured_hint = {
                    'exercise_title': exercise_title,
                    'hint': response,
                    'timestamp': self._get_current_timestamp(),
                    'generation_method': 'ai'
                }
                
                # Add progress information if available
                if student_progress:
                    structured_hint['student_progress'] = student_progress
                
                self.logger.info("Successfully generated hint using AI")
                return structured_hint
            else:
                self.logger.warning("AI failed to generate hint")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating hint: {e}")
            return None
    
    def _build_chat_prompt(self, 
                          question: str, 
                          context: Dict[str, Any] = None,
                          conversation_history: List[Dict[str, Any]] = None) -> str:
        """
        Build prompt for chat response generation.
        
        Args:
            question: User's question
            context: Course context information
            conversation_history: Previous conversation messages
            
        Returns:
            Formatted prompt for chat response
        """
        prompt_parts = [f"Answer the following question: {question}"]
        
        if context:
            course_title = context.get('course_title', 'Unknown Course')
            module_number = context.get('module_number')
            topic = context.get('topic')
            
            prompt_parts.append(f"\\nCourse Context: {course_title}")
            if module_number:
                prompt_parts.append(f"Module: {module_number}")
            if topic:
                prompt_parts.append(f"Topic: {topic}")
        
        if conversation_history:
            prompt_parts.append("\\nConversation History:")
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role.title()}: {content}")
        
        prompt_parts.append("\\nProvide a helpful, accurate, and contextually appropriate response.")
        
        return ''.join(prompt_parts)
    
    def _build_explanation_prompt(self, 
                                concept: str, 
                                level: str,
                                context: Dict[str, Any] = None) -> str:
        """
        Build prompt for concept explanation generation.
        
        Args:
            concept: Concept to explain
            level: Difficulty level for explanation
            context: Course context information
            
        Returns:
            Formatted prompt for explanation generation
        """
        prompt_parts = [
            f"Explain the concept of '{concept}' at a {level} level.",
            "\\nRequirements:",
            "- Use clear, accessible language",
            "- Provide relevant examples",
            "- Include practical applications where appropriate",
            "- Structure the explanation logically"
        ]
        
        if context:
            course_title = context.get('course_title', 'Unknown Course')
            prompt_parts.append(f"\\nCourse Context: {course_title}")
            prompt_parts.append("- Relate the explanation to the course content")
        
        return ''.join(prompt_parts)
    
    def _build_hint_prompt(self, 
                          exercise_context: Dict[str, Any], 
                          student_progress: Dict[str, Any] = None) -> str:
        """
        Build prompt for hint generation.
        
        Args:
            exercise_context: Exercise information
            student_progress: Student's current progress
            
        Returns:
            Formatted prompt for hint generation
        """
        exercise_title = exercise_context.get('title', 'Unknown Exercise')
        exercise_description = exercise_context.get('description', '')
        
        prompt_parts = [
            f"Generate a helpful hint for the exercise: {exercise_title}",
            f"\\nExercise Description: {exercise_description}"
        ]
        
        if student_progress:
            current_code = student_progress.get('current_code', '')
            errors = student_progress.get('errors', [])
            
            if current_code:
                prompt_parts.append(f"\\nStudent's Current Code:\\n{current_code}")
            
            if errors:
                prompt_parts.append(f"\\nErrors Encountered: {', '.join(errors)}")
        
        prompt_parts.extend([
            "\\nHint Requirements:",
            "- Don't give away the complete solution",
            "- Point the student in the right direction",
            "- Be encouraging and supportive",
            "- Focus on the next step they should take"
        ])
        
        return ''.join(prompt_parts)
    
    def _get_chat_system_prompt(self) -> str:
        """Get system prompt for chat responses."""
        return """
        You are a helpful course assistant AI. Your role is to provide accurate, 
        contextual responses to student questions about course content. 
        
        Guidelines:
        - Be helpful and encouraging
        - Provide accurate information
        - Use course context when available
        - Keep responses concise but thorough
        - Encourage critical thinking
        - Admit when you don't know something
        """
    
    def _get_explanation_system_prompt(self) -> str:
        """Get system prompt for concept explanations."""
        return """
        You are an expert educator specializing in clear, accessible explanations. 
        Your task is to explain complex concepts in ways that are appropriate for 
        the student's level.
        
        Guidelines:
        - Use clear, simple language
        - Provide concrete examples
        - Build from basic to advanced concepts
        - Include real-world applications
        - Make explanations engaging and memorable
        """
    
    def _get_hint_system_prompt(self) -> str:
        """Get system prompt for exercise hints."""
        return """
        You are a supportive programming mentor. Your role is to provide helpful 
        hints that guide students toward solutions without giving away the answer.
        
        Guidelines:
        - Don't provide complete solutions
        - Guide toward the next logical step
        - Be encouraging and positive
        - Focus on the learning process
        - Help students think through problems
        """
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()