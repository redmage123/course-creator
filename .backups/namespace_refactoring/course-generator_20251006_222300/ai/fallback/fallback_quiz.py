"""
Fallback Quiz Generator

Provides fallback quiz generation when AI services are unavailable.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


class FallbackQuizGenerator:
    """
    Fallback quiz generator.
    
    Provides basic quiz generation using templates when AI services are unavailable.
    """
    
    def __init__(self):
        """Initialize fallback quiz generator."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_from_syllabus(self, syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate quizzes from syllabus data using fallback templates.
        
        Args:
            syllabus_data: Syllabus data dictionary
            
        Returns:
            Generated quizzes data or None if generation fails
        """
        try:
            course_title = syllabus_data.get('title', 'Unknown Course')
            self.logger.info(f"Generating fallback quizzes for course: {course_title}")
            
            # Generate template quizzes
            quizzes_data = self._create_template_quizzes(syllabus_data)
            
            if quizzes_data:
                self.logger.info("Successfully generated fallback quizzes")
                return quizzes_data
            else:
                self.logger.error("Failed to generate fallback quizzes")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating fallback quizzes: {e}")
            return None
    
    async def generate_for_module(self, syllabus_data: Dict[str, Any], module_number: int) -> Optional[Dict[str, Any]]:
        """
        Generate quiz for a specific module using fallback templates.
        
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
            self.logger.info(f"Generating fallback quiz for module {module_number}: {module.get('title', 'Unknown')}")
            
            # Create focused syllabus for this module
            focused_syllabus = syllabus_data.copy()
            focused_syllabus['modules'] = [module]
            
            # Generate quiz for this module
            quizzes_data = await self.generate_from_syllabus(focused_syllabus)
            
            return quizzes_data
            
        except Exception as e:
            self.logger.error(f"Error generating fallback quiz for module {module_number}: {e}")
            return None
    
    def _create_template_quizzes(self, syllabus_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create template-based quizzes.
        
        Args:
            syllabus_data: Syllabus data
            
        Returns:
            Template quizzes data
        """
        course_title = syllabus_data.get('title', 'Course Title')
        modules = syllabus_data.get('modules', [])
        level = syllabus_data.get('level', 'beginner')
        
        quizzes = []
        
        # Generate quiz for each module
        for module in modules:
            module_title = module.get('title', 'Module')
            module_number = module.get('module_number', 1)
            topics = module.get('topics', [])
            
            # Create quiz for this module
            quiz = self._create_quiz_for_module(
                course_title, 
                module_title, 
                module_number, 
                topics, 
                level
            )
            
            if quiz:
                quizzes.append(quiz)
        
        # If no quizzes generated, create a generic one
        if not quizzes:
            quizzes.append(self._create_generic_quiz(course_title, level))
        
        quizzes_data = {
            'course_title': course_title,
            'total_quizzes': len(quizzes),
            'quizzes': quizzes,
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'fallback'
        }
        
        return quizzes_data
    
    def _create_quiz_for_module(self, course_title: str, module_title: str, 
                              module_number: int, topics: list, level: str) -> Dict[str, Any]:
        """
        Create a quiz for a specific module.
        
        Args:
            course_title: Course title
            module_title: Module title
            module_number: Module number
            topics: List of module topics
            level: Course level
            
        Returns:
            Quiz data
        """
        # Determine quiz type based on course content
        course_lower = course_title.lower()
        
        if 'python' in course_lower:
            questions = self._create_python_questions(topics, level)
        elif 'javascript' in course_lower or 'js' in course_lower:
            questions = self._create_javascript_questions(topics, level)
        elif 'web' in course_lower or 'html' in course_lower:
            questions = self._create_web_questions(topics, level)
        elif 'data' in course_lower:
            questions = self._create_data_questions(topics, level)
        else:
            questions = self._create_generic_questions(topics, level)
        
        quiz = {
            'id': f'quiz_module_{module_number}',
            'title': f'Quiz: {module_title}',
            'description': f'Test your knowledge of {module_title}',
            'module_number': module_number,
            'duration': len(questions) * 2,  # 2 minutes per question
            'difficulty': level,
            'questions': questions
        }
        
        return quiz
    
    def _create_python_questions(self, topics: list, level: str) -> list:
        """Create Python-specific questions."""
        questions = []
        
        if level == 'beginner':
            questions.extend([
                {
                    'question': 'What is the correct way to create a variable in Python?',
                    'options': ['var x = 5', 'x = 5', 'int x = 5', 'variable x = 5'],
                    'correct_answer': 1,
                    'explanation': 'In Python, variables are created by simply assigning a value using the = operator.',
                    'topic_tested': 'Variables',
                    'difficulty': 'easy'
                },
                {
                    'question': 'Which of these is a Python data type?',
                    'options': ['list', 'array', 'vector', 'collection'],
                    'correct_answer': 0,
                    'explanation': 'List is a built-in Python data type for storing multiple items.',
                    'topic_tested': 'Data Types',
                    'difficulty': 'easy'
                }
            ])
        else:
            questions.extend([
                {
                    'question': 'What does the @property decorator do in Python?',
                    'options': ['Creates a class method', 'Creates a static method', 'Creates a getter method', 'Creates a constructor'],
                    'correct_answer': 2,
                    'explanation': 'The @property decorator allows you to create getter methods that can be accessed like attributes.',
                    'topic_tested': 'Decorators',
                    'difficulty': 'medium'
                }
            ])
        
        return questions
    
    def _create_javascript_questions(self, topics: list, level: str) -> list:
        """Create JavaScript-specific questions."""
        questions = [
            {
                'question': 'What is the correct way to declare a variable in JavaScript?',
                'options': ['var x = 5;', 'variable x = 5;', 'v x = 5;', 'declare x = 5;'],
                'correct_answer': 0,
                'explanation': 'In JavaScript, variables are declared using var, let, or const keywords.',
                'topic_tested': 'Variables',
                'difficulty': 'easy'
            },
            {
                'question': 'Which method is used to add an element to an array in JavaScript?',
                'options': ['add()', 'push()', 'append()', 'insert()'],
                'correct_answer': 1,
                'explanation': 'The push() method adds one or more elements to the end of an array.',
                'topic_tested': 'Arrays',
                'difficulty': 'easy'
            }
        ]
        
        return questions
    
    def _create_web_questions(self, topics: list, level: str) -> list:
        """Create web development questions."""
        questions = [
            {
                'question': 'What does HTML stand for?',
                'options': ['Hyper Text Markup Language', 'Home Tool Markup Language', 'Hyperlinks Text Mark Language', 'Hyper Tool Multi Language'],
                'correct_answer': 0,
                'explanation': 'HTML stands for Hyper Text Markup Language, used to create web pages.',
                'topic_tested': 'HTML Basics',
                'difficulty': 'easy'
            },
            {
                'question': 'Which CSS property is used to change text color?',
                'options': ['text-color', 'color', 'font-color', 'text-style'],
                'correct_answer': 1,
                'explanation': 'The color property is used to set the color of text in CSS.',
                'topic_tested': 'CSS Properties',
                'difficulty': 'easy'
            }
        ]
        
        return questions
    
    def _create_data_questions(self, topics: list, level: str) -> list:
        """Create data science questions."""
        questions = [
            {
                'question': 'What is the first step in the data analysis process?',
                'options': ['Data visualization', 'Data collection', 'Data modeling', 'Data interpretation'],
                'correct_answer': 1,
                'explanation': 'Data collection is typically the first step in any data analysis process.',
                'topic_tested': 'Data Analysis Process',
                'difficulty': 'easy'
            },
            {
                'question': 'Which measure of central tendency is most affected by outliers?',
                'options': ['Mean', 'Median', 'Mode', 'Range'],
                'correct_answer': 0,
                'explanation': 'The mean is most affected by outliers because it uses all values in its calculation.',
                'topic_tested': 'Statistics',
                'difficulty': 'medium'
            }
        ]
        
        return questions
    
    def _create_generic_questions(self, topics: list, level: str) -> list:
        """Create generic questions."""
        questions = [
            {
                'question': 'What is the most important factor in learning new concepts?',
                'options': ['Practice', 'Memorization', 'Speed', 'Competition'],
                'correct_answer': 0,
                'explanation': 'Practice is essential for mastering new concepts and building understanding.',
                'topic_tested': 'Learning Principles',
                'difficulty': 'easy'
            },
            {
                'question': 'Which approach is best for problem-solving?',
                'options': ['Random guessing', 'Breaking down into smaller parts', 'Asking for immediate help', 'Avoiding difficult problems'],
                'correct_answer': 1,
                'explanation': 'Breaking complex problems into smaller, manageable parts is an effective problem-solving strategy.',
                'topic_tested': 'Problem Solving',
                'difficulty': 'easy'
            }
        ]
        
        return questions
    
    def _create_generic_quiz(self, course_title: str, level: str) -> Dict[str, Any]:
        """Create a generic quiz."""
        questions = self._create_generic_questions([], level)
        
        quiz = {
            'id': 'generic_quiz',
            'title': f'Quiz: {course_title}',
            'description': f'Test your knowledge of {course_title}',
            'module_number': 1,
            'duration': len(questions) * 2,
            'difficulty': level,
            'questions': questions
        }
        
        return quiz