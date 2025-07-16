"""
Fallback Exercise Generator

Provides fallback exercise generation when AI services are unavailable.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


class FallbackExerciseGenerator:
    """
    Fallback exercise generator.
    
    Provides basic exercise generation using templates when AI services are unavailable.
    """
    
    def __init__(self):
        """Initialize fallback exercise generator."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_from_syllabus(self, syllabus_data: Dict[str, Any], topic: str = None) -> Optional[Dict[str, Any]]:
        """
        Generate exercises from syllabus data using fallback templates.
        
        Args:
            syllabus_data: Syllabus data dictionary
            topic: Specific topic to focus on (optional)
            
        Returns:
            Generated exercises data or None if generation fails
        """
        try:
            course_title = syllabus_data.get('title', 'Unknown Course')
            self.logger.info(f"Generating fallback exercises for course: {course_title}")
            
            # Generate template exercises
            exercises_data = self._create_template_exercises(syllabus_data, topic)
            
            if exercises_data:
                self.logger.info("Successfully generated fallback exercises")
                return exercises_data
            else:
                self.logger.error("Failed to generate fallback exercises")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating fallback exercises: {e}")
            return None
    
    async def generate_for_module(self, syllabus_data: Dict[str, Any], module_number: int) -> Optional[Dict[str, Any]]:
        """
        Generate exercises for a specific module using fallback templates.
        
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
            self.logger.info(f"Generating fallback exercises for module {module_number}: {module.get('title', 'Unknown')}")
            
            # Create focused syllabus for this module
            focused_syllabus = syllabus_data.copy()
            focused_syllabus['modules'] = [module]
            
            # Generate exercises for this module
            exercises_data = await self.generate_from_syllabus(focused_syllabus)
            
            return exercises_data
            
        except Exception as e:
            self.logger.error(f"Error generating fallback exercises for module {module_number}: {e}")
            return None
    
    def _create_template_exercises(self, syllabus_data: Dict[str, Any], topic: str = None) -> Dict[str, Any]:
        """
        Create template-based exercises.
        
        Args:
            syllabus_data: Syllabus data
            topic: Specific topic to focus on (optional)
            
        Returns:
            Template exercises data
        """
        course_title = syllabus_data.get('title', 'Course Title')
        modules = syllabus_data.get('modules', [])
        level = syllabus_data.get('level', 'beginner')
        
        exercises = []
        exercise_id = 1
        
        # Generate exercises for each module
        for module in modules:
            module_title = module.get('title', 'Module')
            module_number = module.get('module_number', 1)
            topics = module.get('topics', [])
            
            # Skip if topic filter is specified and doesn't match
            if topic and topic.lower() not in module_title.lower():
                continue
            
            # Create exercises based on module topics
            for topic_data in topics:
                topic_title = topic_data.get('title', 'Topic')
                
                # Generate exercise based on course type and level
                exercise = self._create_exercise_for_topic(
                    course_title, 
                    module_title, 
                    topic_title, 
                    module_number, 
                    level, 
                    exercise_id
                )
                
                if exercise:
                    exercises.append(exercise)
                    exercise_id += 1
        
        # If no exercises generated, create a generic one
        if not exercises:
            exercises.append(self._create_generic_exercise(course_title, level, 1))
        
        exercises_data = {
            'course_title': course_title,
            'total_exercises': len(exercises),
            'exercises': exercises,
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'fallback'
        }
        
        return exercises_data
    
    def _create_exercise_for_topic(self, course_title: str, module_title: str, topic_title: str, 
                                 module_number: int, level: str, exercise_id: int) -> Dict[str, Any]:
        """
        Create an exercise for a specific topic.
        
        Args:
            course_title: Course title
            module_title: Module title
            topic_title: Topic title
            module_number: Module number
            level: Course level
            exercise_id: Exercise ID
            
        Returns:
            Exercise data
        """
        # Determine exercise type based on course content
        course_lower = course_title.lower()
        topic_lower = topic_title.lower()
        
        if 'python' in course_lower:
            return self._create_python_exercise(topic_title, module_number, level, exercise_id)
        elif 'javascript' in course_lower or 'js' in course_lower:
            return self._create_javascript_exercise(topic_title, module_number, level, exercise_id)
        elif 'web' in course_lower or 'html' in course_lower:
            return self._create_web_exercise(topic_title, module_number, level, exercise_id)
        elif 'data' in course_lower:
            return self._create_data_exercise(topic_title, module_number, level, exercise_id)
        else:
            return self._create_generic_exercise(topic_title, level, exercise_id)
    
    def _create_python_exercise(self, topic_title: str, module_number: int, level: str, exercise_id: int) -> Dict[str, Any]:
        """Create a Python exercise."""
        if level == 'beginner':
            return {
                'id': f'exercise_{exercise_id}',
                'title': f'Python Practice: {topic_title}',
                'description': f'Practice Python programming with {topic_title}',
                'module_number': module_number,
                'difficulty': 'easy',
                'starter_code': '# Write your Python code here\\nprint("Hello, World!")',
                'solution': '# Solution\\nprint("Hello, World!")\\n\\n# This is a basic Python program',
                'instructions': '1. Write a Python program\\n2. Test your code\\n3. Submit your solution'
            }
        else:
            return {
                'id': f'exercise_{exercise_id}',
                'title': f'Advanced Python: {topic_title}',
                'description': f'Advanced Python programming exercise for {topic_title}',
                'module_number': module_number,
                'difficulty': 'medium',
                'starter_code': '# Advanced Python exercise\\nclass Solution:\\n    def solve(self):\\n        pass',
                'solution': '# Advanced solution\\nclass Solution:\\n    def solve(self):\\n        return "Solution implemented"',
                'instructions': '1. Implement the solution class\\n2. Test your implementation\\n3. Optimize your code'
            }
    
    def _create_javascript_exercise(self, topic_title: str, module_number: int, level: str, exercise_id: int) -> Dict[str, Any]:
        """Create a JavaScript exercise."""
        return {
            'id': f'exercise_{exercise_id}',
            'title': f'JavaScript Practice: {topic_title}',
            'description': f'Practice JavaScript programming with {topic_title}',
            'module_number': module_number,
            'difficulty': 'easy' if level == 'beginner' else 'medium',
            'starter_code': '// Write your JavaScript code here\\nconsole.log("Hello, World!");',
            'solution': '// Solution\\nconsole.log("Hello, World!");\\n\\n// This is a basic JavaScript program',
            'instructions': '1. Write JavaScript code\\n2. Test in browser console\\n3. Submit your solution'
        }
    
    def _create_web_exercise(self, topic_title: str, module_number: int, level: str, exercise_id: int) -> Dict[str, Any]:
        """Create a web development exercise."""
        return {
            'id': f'exercise_{exercise_id}',
            'title': f'Web Development: {topic_title}',
            'description': f'Create a web page using {topic_title}',
            'module_number': module_number,
            'difficulty': 'easy' if level == 'beginner' else 'medium',
            'starter_code': '<!DOCTYPE html>\\n<html>\\n<head>\\n    <title>My Page</title>\\n</head>\\n<body>\\n    <h1>Hello, World!</h1>\\n</body>\\n</html>',
            'solution': '<!DOCTYPE html>\\n<html>\\n<head>\\n    <title>My Page</title>\\n    <style>\\n        body { font-family: Arial, sans-serif; }\\n    </style>\\n</head>\\n<body>\\n    <h1>Hello, World!</h1>\\n    <p>This is a complete web page.</p>\\n</body>\\n</html>',
            'instructions': '1. Create HTML structure\\n2. Add CSS styling\\n3. Test in browser'
        }
    
    def _create_data_exercise(self, topic_title: str, module_number: int, level: str, exercise_id: int) -> Dict[str, Any]:
        """Create a data science exercise."""
        return {
            'id': f'exercise_{exercise_id}',
            'title': f'Data Analysis: {topic_title}',
            'description': f'Analyze data using {topic_title}',
            'module_number': module_number,
            'difficulty': 'medium',
            'starter_code': '# Data analysis exercise\\nimport pandas as pd\\n\\n# Load your data here\\ndata = pd.read_csv("data.csv")',
            'solution': '# Data analysis solution\\nimport pandas as pd\\n\\n# Load and analyze data\\ndata = pd.read_csv("data.csv")\\nresult = data.describe()\\nprint(result)',
            'instructions': '1. Load the dataset\\n2. Perform analysis\\n3. Interpret results'
        }
    
    def _create_generic_exercise(self, topic_title: str, level: str, exercise_id: int) -> Dict[str, Any]:
        """Create a generic exercise."""
        return {
            'id': f'exercise_{exercise_id}',
            'title': f'Practice Exercise: {topic_title}',
            'description': f'Complete this exercise to practice {topic_title}',
            'module_number': 1,
            'difficulty': 'easy' if level == 'beginner' else 'medium',
            'starter_code': '# Complete this exercise\\n# Your code here',
            'solution': '# Solution\\n# This is a sample solution\\nprint("Exercise completed")',
            'instructions': '1. Read the requirements\\n2. Implement your solution\\n3. Test your code'
        }