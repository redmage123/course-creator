"""
Fallback Syllabus Generator

Provides fallback syllabus generation when AI services are unavailable.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


class FallbackSyllabusGenerator:
    """
    Fallback syllabus generator.
    
    Provides basic syllabus generation using templates and predefined structures
    when AI services are unavailable.
    """
    
    def __init__(self):
        """Initialize fallback syllabus generator."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_from_course_info(self, course_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate syllabus from course information using fallback templates.
        
        Args:
            course_info: Dictionary containing course information
            
        Returns:
            Generated syllabus data or None if generation fails
        """
        try:
            self.logger.info(f"Generating fallback syllabus for course: {course_info.get('title', 'Unknown')}")
            
            # Use template-based generation
            syllabus_data = self._create_template_syllabus(course_info)
            
            if syllabus_data:
                self.logger.info("Successfully generated fallback syllabus")
                return syllabus_data
            else:
                self.logger.error("Failed to generate fallback syllabus")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating fallback syllabus: {e}")
            return None
    
    async def refine_syllabus(self, 
                            existing_syllabus: Dict[str, Any], 
                            feedback: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Refine existing syllabus using fallback methods.
        
        Args:
            existing_syllabus: Current syllabus data
            feedback: Refinement feedback
            
        Returns:
            Refined syllabus data or None if refinement fails
        """
        try:
            self.logger.info("Refining syllabus with fallback methods")
            
            # Apply basic refinements
            refined_syllabus = self._apply_basic_refinements(existing_syllabus, feedback)
            
            if refined_syllabus:
                self.logger.info("Successfully refined syllabus using fallback methods")
                return refined_syllabus
            else:
                self.logger.error("Failed to refine syllabus using fallback methods")
                return None
                
        except Exception as e:
            self.logger.error(f"Error refining fallback syllabus: {e}")
            return None
    
    def _create_template_syllabus(self, course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a template-based syllabus.
        
        Args:
            course_info: Course information
            
        Returns:
            Template syllabus data
        """
        title = course_info.get('title', 'Course Title')
        description = course_info.get('description', 'Course description')
        level = course_info.get('level', 'beginner')
        
        # Create basic module structure based on course type
        modules = self._generate_template_modules(title, level)
        
        syllabus = {
            'title': title,
            'description': description,
            'level': level,
            'duration': course_info.get('duration', 40),
            'objectives': course_info.get('objectives', self._get_default_objectives(level)),
            'prerequisites': course_info.get('prerequisites', self._get_default_prerequisites(level)),
            'target_audience': course_info.get('target_audience', self._get_default_target_audience(level)),
            'modules': modules,
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'fallback'
        }
        
        return syllabus
    
    def _generate_template_modules(self, title: str, level: str) -> list:
        """
        Generate template modules based on course title and level.
        
        Args:
            title: Course title
            level: Course level
            
        Returns:
            List of template modules
        """
        # Determine course type from title
        title_lower = title.lower()
        
        if 'python' in title_lower:
            return self._get_python_modules(level)
        elif 'javascript' in title_lower or 'js' in title_lower:
            return self._get_javascript_modules(level)
        elif 'web' in title_lower or 'html' in title_lower:
            return self._get_web_modules(level)
        elif 'data' in title_lower or 'analytics' in title_lower:
            return self._get_data_modules(level)
        else:
            return self._get_generic_modules(level)
    
    def _get_python_modules(self, level: str) -> list:
        """Get Python course modules."""
        if level == 'beginner':
            return [
                {
                    'module_number': 1,
                    'title': 'Python Fundamentals',
                    'description': 'Introduction to Python programming language',
                    'duration': 120,
                    'objectives': ['Understand Python syntax', 'Write basic programs'],
                    'topics': [
                        {'title': 'Variables and Data Types', 'description': 'Python variables and basic data types', 'duration': 30},
                        {'title': 'Control Structures', 'description': 'If statements, loops, and conditionals', 'duration': 45},
                        {'title': 'Functions', 'description': 'Creating and using functions', 'duration': 45}
                    ]
                },
                {
                    'module_number': 2,
                    'title': 'Data Structures',
                    'description': 'Working with Python data structures',
                    'duration': 90,
                    'objectives': ['Master lists and dictionaries', 'Understand data manipulation'],
                    'topics': [
                        {'title': 'Lists and Tuples', 'description': 'Working with sequences', 'duration': 45},
                        {'title': 'Dictionaries and Sets', 'description': 'Key-value pairs and unique collections', 'duration': 45}
                    ]
                }
            ]
        else:
            return [
                {
                    'module_number': 1,
                    'title': 'Advanced Python Concepts',
                    'description': 'Advanced Python programming techniques',
                    'duration': 150,
                    'objectives': ['Master OOP in Python', 'Understand decorators and generators'],
                    'topics': [
                        {'title': 'Object-Oriented Programming', 'description': 'Classes, inheritance, and polymorphism', 'duration': 60},
                        {'title': 'Decorators and Generators', 'description': 'Advanced Python features', 'duration': 90}
                    ]
                }
            ]
    
    def _get_javascript_modules(self, level: str) -> list:
        """Get JavaScript course modules."""
        return [
            {
                'module_number': 1,
                'title': 'JavaScript Fundamentals',
                'description': 'Introduction to JavaScript programming',
                'duration': 120,
                'objectives': ['Understand JavaScript syntax', 'Create interactive web pages'],
                'topics': [
                    {'title': 'Variables and Functions', 'description': 'JavaScript basics', 'duration': 60},
                    {'title': 'DOM Manipulation', 'description': 'Interacting with web pages', 'duration': 60}
                ]
            }
        ]
    
    def _get_web_modules(self, level: str) -> list:
        """Get Web development course modules."""
        return [
            {
                'module_number': 1,
                'title': 'HTML & CSS Fundamentals',
                'description': 'Building web pages with HTML and CSS',
                'duration': 120,
                'objectives': ['Create structured web pages', 'Style web content'],
                'topics': [
                    {'title': 'HTML Structure', 'description': 'Creating web page structure', 'duration': 60},
                    {'title': 'CSS Styling', 'description': 'Styling web pages', 'duration': 60}
                ]
            }
        ]
    
    def _get_data_modules(self, level: str) -> list:
        """Get Data science course modules."""
        return [
            {
                'module_number': 1,
                'title': 'Data Analysis Fundamentals',
                'description': 'Introduction to data analysis',
                'duration': 120,
                'objectives': ['Understand data types', 'Perform basic analysis'],
                'topics': [
                    {'title': 'Data Types and Structures', 'description': 'Understanding data', 'duration': 60},
                    {'title': 'Basic Analysis Techniques', 'description': 'Analyzing data', 'duration': 60}
                ]
            }
        ]
    
    def _get_generic_modules(self, level: str) -> list:
        """Get generic course modules."""
        return [
            {
                'module_number': 1,
                'title': 'Introduction and Fundamentals',
                'description': 'Course introduction and fundamental concepts',
                'duration': 90,
                'objectives': ['Understand core concepts', 'Apply basic principles'],
                'topics': [
                    {'title': 'Core Concepts', 'description': 'Fundamental principles', 'duration': 45},
                    {'title': 'Basic Applications', 'description': 'Practical applications', 'duration': 45}
                ]
            },
            {
                'module_number': 2,
                'title': 'Intermediate Topics',
                'description': 'Building on fundamental knowledge',
                'duration': 90,
                'objectives': ['Apply intermediate concepts', 'Solve complex problems'],
                'topics': [
                    {'title': 'Advanced Concepts', 'description': 'More complex topics', 'duration': 45},
                    {'title': 'Problem Solving', 'description': 'Practical problem solving', 'duration': 45}
                ]
            }
        ]
    
    def _get_default_objectives(self, level: str) -> list:
        """Get default learning objectives based on level."""
        if level == 'beginner':
            return [
                'Understand fundamental concepts',
                'Apply basic principles',
                'Complete practical exercises'
            ]
        elif level == 'intermediate':
            return [
                'Apply intermediate concepts',
                'Solve complex problems',
                'Build practical projects'
            ]
        else:
            return [
                'Master advanced concepts',
                'Design complex solutions',
                'Lead projects and teams'
            ]
    
    def _get_default_prerequisites(self, level: str) -> list:
        """Get default prerequisites based on level."""
        if level == 'beginner':
            return ['Basic computer literacy']
        elif level == 'intermediate':
            return ['Basic programming knowledge', 'Fundamental concepts']
        else:
            return ['Intermediate knowledge', 'Project experience']
    
    def _get_default_target_audience(self, level: str) -> str:
        """Get default target audience based on level."""
        if level == 'beginner':
            return 'Beginners with no prior experience'
        elif level == 'intermediate':
            return 'Students with basic knowledge'
        else:
            return 'Advanced learners and professionals'
    
    def _apply_basic_refinements(self, syllabus: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply basic refinements to syllabus.
        
        Args:
            syllabus: Current syllabus
            feedback: Refinement feedback
            
        Returns:
            Refined syllabus
        """
        refined = syllabus.copy()
        
        # Apply suggestions if provided
        suggestions = feedback.get('suggestions', [])
        if suggestions:
            # Add suggestions to course description
            current_desc = refined.get('description', '')
            refined['description'] = f"{current_desc}\n\nSuggestions incorporated: {', '.join(suggestions[:3])}"
        
        # Adjust duration if requested
        duration_adjustment = feedback.get('duration_adjustment')
        if duration_adjustment:
            current_duration = refined.get('duration', 40)
            refined['duration'] = max(10, current_duration + duration_adjustment)
        
        # Add timestamp for refinement
        refined['refined_at'] = datetime.now().isoformat()
        refined['refinement_method'] = 'fallback'
        
        return refined