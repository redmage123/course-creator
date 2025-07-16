"""
AI Prompt Templates

Centralized prompt templates for AI content generation.
"""

import logging
from typing import Dict, Any, List


class PromptTemplates:
    """
    Centralized AI prompt templates.
    
    Provides consistent, well-structured prompts for various AI generation tasks.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_syllabus_system_prompt(self) -> str:
        """
        Get system prompt for syllabus generation.
        
        Returns:
            System prompt for syllabus generation
        """
        return """
        You are an expert educational content designer specializing in creating comprehensive, 
        well-structured course syllabi. Your task is to generate detailed, practical syllabi 
        that provide clear learning paths for students.
        
        Key principles:
        1. Focus on practical, applicable skills
        2. Structure content in logical, progressive modules
        3. Include specific learning objectives for each module
        4. Ensure appropriate difficulty progression
        5. Include relevant topics and subtopics
        6. Consider diverse learning styles and backgrounds
        
        Always respond with valid JSON format following the specified schema.
        """
    
    def build_syllabus_generation_prompt(self, course_info: Dict[str, Any]) -> str:
        """
        Build prompt for syllabus generation.
        
        Args:
            course_info: Course information dictionary
            
        Returns:
            Formatted prompt for syllabus generation
        """
        title = course_info.get('title', 'Unknown Course')
        description = course_info.get('description', 'No description provided')
        level = course_info.get('level', 'beginner')
        duration = course_info.get('duration', 'Not specified')
        objectives = course_info.get('objectives', [])
        prerequisites = course_info.get('prerequisites', [])
        target_audience = course_info.get('target_audience', 'General audience')
        
        objectives_text = '\n'.join([f"- {obj}" for obj in objectives]) if objectives else "- To be determined"
        prerequisites_text = '\n'.join([f"- {prereq}" for prereq in prerequisites]) if prerequisites else "- None"
        
        return f"""
        Create a comprehensive syllabus for the following course:
        
        **Course Title:** {title}
        **Description:** {description}
        **Level:** {level}
        **Duration:** {duration}
        **Target Audience:** {target_audience}
        
        **Learning Objectives:**
        {objectives_text}
        
        **Prerequisites:**
        {prerequisites_text}
        
        Generate a detailed syllabus with the following structure:
        
        1. **Course Overview:** Enhanced description with key concepts
        2. **Modules:** 4-8 modules with logical progression
        3. **Each Module should contain:**
           - Module number (1, 2, 3, etc.)
           - Clear, descriptive title
           - Detailed description
           - Specific learning objectives (3-5 per module)
           - Duration estimate (if applicable)
           - List of topics/subtopics covered
        
        **Requirements:**
        - Ensure modules build upon each other logically
        - Include practical, hands-on components where appropriate
        - Balance theory with practical application
        - Consider different learning styles
        - Make content engaging and relevant
        
        **Response Format:**
        Return the syllabus as a JSON object with this exact structure:
        ```json
        {{
            "title": "Course Title",
            "description": "Enhanced course description",
            "level": "{level}",
            "duration": duration_in_hours,
            "objectives": ["objective1", "objective2", ...],
            "prerequisites": ["prereq1", "prereq2", ...],
            "target_audience": "target audience description",
            "modules": [
                {{
                    "module_number": 1,
                    "title": "Module Title",
                    "description": "Module description",
                    "duration": duration_in_minutes,
                    "objectives": ["objective1", "objective2", ...],
                    "topics": [
                        {{
                            "title": "Topic Title",
                            "description": "Topic description",
                            "duration": duration_in_minutes
                        }}
                    ]
                }}
            ]
        }}
        ```
        
        Generate a high-quality, educationally sound syllabus that would be valuable for students.
        """
    
    def build_syllabus_refinement_prompt(self, 
                                       existing_syllabus: Dict[str, Any], 
                                       feedback: Dict[str, Any]) -> str:
        """
        Build prompt for syllabus refinement.
        
        Args:
            existing_syllabus: Current syllabus data
            feedback: Refinement feedback
            
        Returns:
            Formatted prompt for syllabus refinement
        """
        suggestions = feedback.get('suggestions', [])
        focus_areas = feedback.get('focus_areas', [])
        adjustments = feedback.get('adjustments', {})
        additional_modules = feedback.get('additional_modules', [])
        remove_modules = feedback.get('remove_modules', [])
        
        suggestions_text = '\n'.join([f"- {sugg}" for sugg in suggestions]) if suggestions else "- None"
        focus_areas_text = '\n'.join([f"- {area}" for area in focus_areas]) if focus_areas else "- None"
        additional_modules_text = '\n'.join([f"- {mod}" for mod in additional_modules]) if additional_modules else "- None"
        remove_modules_text = '\n'.join([f"- {mod}" for mod in remove_modules]) if remove_modules else "- None"
        
        return f"""
        Refine the following course syllabus based on the provided feedback:
        
        **Current Syllabus:**
        ```json
        {existing_syllabus}
        ```
        
        **Refinement Feedback:**
        
        **Suggestions for Improvement:**
        {suggestions_text}
        
        **Areas to Focus On:**
        {focus_areas_text}
        
        **Additional Modules to Include:**
        {additional_modules_text}
        
        **Modules to Remove:**
        {remove_modules_text}
        
        **Specific Adjustments:**
        {adjustments}
        
        **Refinement Instructions:**
        1. Carefully analyze the existing syllabus
        2. Apply the suggested improvements
        3. Enhance focus areas with more detail
        4. Add requested additional modules
        5. Remove or modify unwanted modules
        6. Ensure logical flow and progression
        7. Maintain educational quality and coherence
        8. Preserve the original course objectives unless feedback suggests otherwise
        
        **Response Format:**
        Return the refined syllabus as a JSON object with the same structure as the original:
        ```json
        {{
            "title": "Course Title",
            "description": "Enhanced course description",
            "level": "course_level",
            "duration": duration_in_hours,
            "objectives": ["objective1", "objective2", ...],
            "prerequisites": ["prereq1", "prereq2", ...],
            "target_audience": "target audience description",
            "modules": [
                {{
                    "module_number": 1,
                    "title": "Module Title",
                    "description": "Module description",
                    "duration": duration_in_minutes,
                    "objectives": ["objective1", "objective2", ...],
                    "topics": [
                        {{
                            "title": "Topic Title",
                            "description": "Topic description",
                            "duration": duration_in_minutes
                        }}
                    ]
                }}
            ]
        }}
        ```
        
        Generate a refined, improved syllabus that addresses all the feedback points.
        """
    
    def get_slide_system_prompt(self) -> str:
        """
        Get system prompt for slide generation.
        
        Returns:
            System prompt for slide generation
        """
        return """
        You are an expert instructional designer specializing in creating engaging, 
        educational slide presentations. Your task is to generate comprehensive slide 
        content that effectively communicates course material.
        
        Key principles:
        1. Create clear, concise slide content
        2. Use engaging titles and descriptions
        3. Include relevant examples and explanations
        4. Structure content for optimal learning
        5. Balance text with conceptual clarity
        6. Ensure slides build upon each other logically
        
        Always respond with valid JSON format following the specified schema.
        """
    
    def build_slide_generation_prompt(self, syllabus_data: Dict[str, Any]) -> str:
        """
        Build prompt for slide generation from syllabus.
        
        Args:
            syllabus_data: Syllabus data to generate slides from
            
        Returns:
            Formatted prompt for slide generation
        """
        title = syllabus_data.get('title', 'Unknown Course')
        description = syllabus_data.get('description', 'No description')
        modules = syllabus_data.get('modules', [])
        
        modules_summary = []
        for i, module in enumerate(modules):
            module_title = module.get('title', f'Module {i+1}')
            module_desc = module.get('description', 'No description')
            modules_summary.append(f"Module {i+1}: {module_title} - {module_desc}")
        
        modules_text = '\n'.join(modules_summary)
        
        return f"""
        Generate comprehensive slide content for the following course:
        
        **Course:** {title}
        **Description:** {description}
        
        **Modules:**
        {modules_text}
        
        **Slide Generation Requirements:**
        1. Create 3-5 slides per module
        2. Include a title slide for the course
        3. Include overview and conclusion slides
        4. Each slide should have:
           - Clear, engaging title
           - Concise content (bullet points, explanations)
           - Relevant examples where appropriate
           - Logical flow and progression
        
        **Response Format:**
        Return the slides as a JSON object with this structure:
        ```json
        {{
            "course_title": "{title}",
            "total_slides": number_of_slides,
            "slides": [
                {{
                    "slide_number": 1,
                    "title": "Slide Title",
                    "content": "Slide content with bullet points, explanations, examples",
                    "module_number": module_number_or_0_for_intro,
                    "slide_type": "title|content|overview|conclusion"
                }}
            ]
        }}
        ```
        
        Generate engaging, educational slides that effectively teach the course material.
        """
    
    def get_exercise_system_prompt(self) -> str:
        """
        Get system prompt for exercise generation.
        
        Returns:
            System prompt for exercise generation
        """
        return """
        You are an expert educator specializing in creating practical, hands-on exercises 
        that reinforce learning objectives. Your task is to generate meaningful exercises 
        that help students apply their knowledge in real-world scenarios.
        
        Key principles:
        1. Create practical, applicable exercises
        2. Include clear instructions and objectives
        3. Provide starter code or templates where appropriate
        4. Include comprehensive solutions
        5. Ensure exercises build skills progressively
        6. Consider different skill levels and learning styles
        
        Always respond with valid JSON format following the specified schema.
        """
    
    def build_exercise_generation_prompt(self, 
                                       syllabus_data: Dict[str, Any], 
                                       topic: str = None) -> str:
        """
        Build prompt for exercise generation.
        
        Args:
            syllabus_data: Syllabus data to generate exercises from
            topic: Specific topic to focus on (optional)
            
        Returns:
            Formatted prompt for exercise generation
        """
        title = syllabus_data.get('title', 'Unknown Course')
        level = syllabus_data.get('level', 'beginner')
        modules = syllabus_data.get('modules', [])
        
        focus_text = f"Focus specifically on: {topic}" if topic else "Cover all course topics"
        
        return f"""
        Generate practical exercises for the following course:
        
        **Course:** {title}
        **Level:** {level}
        {focus_text}
        
        **Course Modules:**
        {self._format_modules_for_prompt(modules)}
        
        **Exercise Generation Requirements:**
        1. Create 1-2 exercises per module
        2. Each exercise should be practical and applicable
        3. Include clear objectives and instructions
        4. Provide starter code or templates
        5. Include comprehensive solutions
        6. Ensure appropriate difficulty progression
        
        **Response Format:**
        Return the exercises as a JSON object with this structure:
        ```json
        {{
            "course_title": "{title}",
            "total_exercises": number_of_exercises,
            "exercises": [
                {{
                    "id": "exercise_id",
                    "title": "Exercise Title",
                    "description": "Exercise description and objectives",
                    "module_number": module_number,
                    "difficulty": "easy|medium|hard",
                    "starter_code": "Starting code or template",
                    "solution": "Complete solution with explanation",
                    "instructions": "Step-by-step instructions"
                }}
            ]
        }}
        ```
        
        Generate engaging, practical exercises that reinforce learning.
        """
    
    def _format_modules_for_prompt(self, modules: List[Dict[str, Any]]) -> str:
        """
        Format modules for inclusion in prompts.
        
        Args:
            modules: List of module dictionaries
            
        Returns:
            Formatted module text
        """
        formatted_modules = []
        
        for i, module in enumerate(modules):
            module_title = module.get('title', f'Module {i+1}')
            module_desc = module.get('description', 'No description')
            objectives = module.get('objectives', [])
            topics = module.get('topics', [])
            
            obj_text = '\n  '.join([f"- {obj}" for obj in objectives]) if objectives else "  - None"
            topic_text = '\n  '.join([f"- {topic.get('title', 'Topic')}" for topic in topics]) if topics else "  - None"
            
            formatted_modules.append(f"""
Module {i+1}: {module_title}
Description: {module_desc}
Objectives:
  {obj_text}
Topics:
  {topic_text}
""")
        
        return '\n'.join(formatted_modules)
    
    def get_quiz_system_prompt(self) -> str:
        """
        Get system prompt for quiz generation.
        
        Returns:
            System prompt for quiz generation
        """
        return """
        You are an expert assessment designer specializing in creating comprehensive, 
        fair, and educational quizzes. Your task is to generate well-structured quiz 
        questions that accurately assess student understanding.
        
        Key principles:
        1. Create clear, unambiguous questions
        2. Include distractors that test common misconceptions
        3. Ensure questions assess different levels of understanding
        4. Provide detailed explanations for correct answers
        5. Balance question types and difficulty levels
        6. Focus on practical application of knowledge
        
        Always respond with valid JSON format following the specified schema.
        """
    
    def build_quiz_generation_prompt(self, syllabus_data: Dict[str, Any]) -> str:
        """
        Build prompt for quiz generation.
        
        Args:
            syllabus_data: Syllabus data to generate quizzes from
            
        Returns:
            Formatted prompt for quiz generation
        """
        title = syllabus_data.get('title', 'Unknown Course')
        level = syllabus_data.get('level', 'beginner')
        modules = syllabus_data.get('modules', [])
        
        return f"""
        Generate comprehensive quizzes for the following course:
        
        **Course:** {title}
        **Level:** {level}
        
        **Course Modules:**
        {self._format_modules_for_prompt(modules)}
        
        **Quiz Generation Requirements:**
        1. Create 1 quiz per module
        2. Include 8-12 questions per quiz
        3. Mix question types (multiple choice, true/false, etc.)
        4. Include questions at different difficulty levels
        5. Provide detailed explanations for correct answers
        6. Ensure questions test understanding, not just memorization
        
        **Response Format:**
        Return the quizzes as a JSON object with this structure:
        ```json
        {{
            "course_title": "{title}",
            "total_quizzes": number_of_quizzes,
            "quizzes": [
                {{
                    "id": "quiz_id",
                    "title": "Quiz Title",
                    "description": "Quiz description",
                    "module_number": module_number,
                    "duration": duration_in_minutes,
                    "difficulty": "beginner|intermediate|advanced",
                    "questions": [
                        {{
                            "question": "Question text",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "correct_answer": 0,
                            "explanation": "Explanation of correct answer",
                            "topic_tested": "Topic being tested",
                            "difficulty": "easy|medium|hard"
                        }}
                    ]
                }}
            ]
        }}
        ```
        
        Generate comprehensive, educational quizzes that effectively assess learning.
        """