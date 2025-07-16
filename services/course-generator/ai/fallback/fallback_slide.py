"""
Fallback Slide Generator

Provides fallback slide generation when AI services are unavailable.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


class FallbackSlideGenerator:
    """
    Fallback slide generator.
    
    Provides basic slide generation using templates when AI services are unavailable.
    """
    
    def __init__(self):
        """Initialize fallback slide generator."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_from_syllabus(self, syllabus_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate slides from syllabus data using fallback templates.
        
        Args:
            syllabus_data: Syllabus data dictionary
            
        Returns:
            Generated slides data or None if generation fails
        """
        try:
            course_title = syllabus_data.get('title', 'Unknown Course')
            self.logger.info(f"Generating fallback slides for course: {course_title}")
            
            # Generate template slides
            slides_data = self._create_template_slides(syllabus_data)
            
            if slides_data:
                self.logger.info("Successfully generated fallback slides")
                return slides_data
            else:
                self.logger.error("Failed to generate fallback slides")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating fallback slides: {e}")
            return None
    
    async def generate_for_module(self, syllabus_data: Dict[str, Any], module_number: int) -> Optional[Dict[str, Any]]:
        """
        Generate slides for a specific module using fallback templates.
        
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
            self.logger.info(f"Generating fallback slides for module {module_number}: {module.get('title', 'Unknown')}")
            
            # Create focused syllabus for this module
            focused_syllabus = syllabus_data.copy()
            focused_syllabus['modules'] = [module]
            
            # Generate slides for this module
            slides_data = await self.generate_from_syllabus(focused_syllabus)
            
            return slides_data
            
        except Exception as e:
            self.logger.error(f"Error generating fallback slides for module {module_number}: {e}")
            return None
    
    def _create_template_slides(self, syllabus_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create template-based slides.
        
        Args:
            syllabus_data: Syllabus data
            
        Returns:
            Template slides data
        """
        course_title = syllabus_data.get('title', 'Course Title')
        description = syllabus_data.get('description', 'Course description')
        modules = syllabus_data.get('modules', [])
        
        slides = []
        slide_number = 1
        
        # Title slide
        slides.append({
            'slide_number': slide_number,
            'title': course_title,
            'content': f"Welcome to {course_title}\\n\\n{description}",
            'module_number': 0,
            'slide_type': 'title'
        })
        slide_number += 1
        
        # Course overview slide
        objectives = syllabus_data.get('objectives', [])
        objectives_text = '\\n'.join([f"• {obj}" for obj in objectives]) if objectives else "• Learn fundamental concepts"
        
        slides.append({
            'slide_number': slide_number,
            'title': 'Course Overview',
            'content': f"Learning Objectives:\\n{objectives_text}\\n\\nCourse Structure:\\n• {len(modules)} modules\\n• Practical exercises\\n• Assessment quizzes",
            'module_number': 0,
            'slide_type': 'overview'
        })
        slide_number += 1
        
        # Module slides
        for module in modules:
            module_title = module.get('title', 'Module')
            module_desc = module.get('description', 'Module description')
            module_number = module.get('module_number', 1)
            topics = module.get('topics', [])
            
            # Module introduction slide
            slides.append({
                'slide_number': slide_number,
                'title': f"Module {module_number}: {module_title}",
                'content': f"{module_desc}\\n\\nTopics Covered:\\n" + '\\n'.join([f"• {topic.get('title', 'Topic')}" for topic in topics]),
                'module_number': module_number,
                'slide_type': 'content'
            })
            slide_number += 1
            
            # Topic slides
            for topic in topics:
                topic_title = topic.get('title', 'Topic')
                topic_desc = topic.get('description', 'Topic description')
                
                slides.append({
                    'slide_number': slide_number,
                    'title': topic_title,
                    'content': f"{topic_desc}\\n\\nKey Points:\\n• Understand core concepts\\n• Apply practical skills\\n• Complete exercises",
                    'module_number': module_number,
                    'slide_type': 'content'
                })
                slide_number += 1
        
        # Conclusion slide
        slides.append({
            'slide_number': slide_number,
            'title': 'Course Summary',
            'content': f"Congratulations on completing {course_title}!\\n\\nYou have learned:\\n• Core concepts and principles\\n• Practical applications\\n• Problem-solving skills\\n\\nNext Steps:\\n• Practice with real projects\\n• Explore advanced topics\\n• Apply your knowledge",
            'module_number': 0,
            'slide_type': 'conclusion'
        })
        
        slides_data = {
            'course_title': course_title,
            'total_slides': len(slides),
            'slides': slides,
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'fallback'
        }
        
        return slides_data