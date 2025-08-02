"""
Slide Generation Service Implementation
Single Responsibility: Implement slide generation business logic
Dependency Inversion: Depends on repository and AI service abstractions
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from domain.entities.course_content import Slide, SlideType, DifficultyLevel
from domain.interfaces.content_generation_service import ISlideGenerationService
from domain.interfaces.content_repository import ISlideRepository, ISyllabusRepository
from domain.interfaces.ai_service import IAIService, ContentGenerationType, IPromptTemplateService

class SlideGenerationService(ISlideGenerationService):
    """
    Slide generation service implementation with business logic
    """
    
    def __init__(self, 
                 slide_repository: ISlideRepository,
                 syllabus_repository: ISyllabusRepository,
                 ai_service: IAIService,
                 prompt_service: IPromptTemplateService):
        self._slide_repository = slide_repository
        self._syllabus_repository = syllabus_repository
        self._ai_service = ai_service
        self._prompt_service = prompt_service
    
    async def generate_slides(self, course_id: str, title: str, description: str, 
                             topic: str, slide_count: int = 10, 
                             use_custom_template: bool = False) -> List[Slide]:
        """Generate slides for a course topic using AI"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not title or len(title.strip()) == 0:
            raise ValueError("Title is required")
        
        if not topic or len(topic.strip()) == 0:
            raise ValueError("Topic is required")
        
        if slide_count <= 0 or slide_count > 50:
            raise ValueError("Slide count must be between 1 and 50")
        
        # Get syllabus context if available
        syllabus = await self._syllabus_repository.get_by_course_id(course_id)
        syllabus_context = self._extract_syllabus_context(syllabus) if syllabus else {}
        
        # Prepare generation context
        generation_context = {
            'course_id': course_id,
            'title': title,
            'description': description,
            'topic': topic,
            'slide_count': slide_count,
            'use_custom_template': use_custom_template,
            'syllabus_context': syllabus_context
        }
        
        # Get appropriate template
        template_name = "custom" if use_custom_template else "standard"
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.SLIDE, template_name
        )
        
        # Render prompt
        prompt = self._prompt_service.render_prompt(template, generation_context)
        
        # Generate structured slide content
        slides_schema = self._get_slides_schema(slide_count)
        generated_content = await self._ai_service.generate_structured_content(
            ContentGenerationType.SLIDE,
            prompt,
            slides_schema,
            generation_context
        )
        
        # Convert to Slide entities
        slides = []
        for i, slide_data in enumerate(generated_content.get('slides', [])):
            slide = Slide(
                course_id=course_id,
                title=slide_data.get('title', f"Slide {i+1}"),
                content=slide_data.get('content', ''),
                slide_type=self._determine_slide_type(slide_data.get('type', 'content')),
                order=i + 1,
                topic=topic,
                notes=slide_data.get('notes', ''),
                duration_minutes=slide_data.get('duration_minutes', 5)
            )
            
            # Add slide metadata
            if 'learning_objectives' in slide_data:
                slide.metadata['learning_objectives'] = slide_data['learning_objectives']
            
            if 'key_concepts' in slide_data:
                slide.metadata['key_concepts'] = slide_data['key_concepts']
            
            slides.append(slide)
        
        # Save slides to repository
        saved_slides = await self._slide_repository.bulk_create(slides)
        return saved_slides
    
    async def generate_single_slide(self, course_id: str, topic: str, 
                                   slide_type: str, content_focus: str,
                                   context: Dict[str, Any] = None) -> Slide:
        """Generate a single slide with specific focus"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not topic:
            raise ValueError("Topic is required")
        
        if not content_focus:
            raise ValueError("Content focus is required")
        
        # Prepare generation context
        generation_context = {
            'course_id': course_id,
            'topic': topic,
            'slide_type': slide_type,
            'content_focus': content_focus,
            'context': context or {}
        }
        
        # Get template for single slide generation
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.SLIDE, "single_slide"
        )
        
        # Render prompt
        prompt = self._prompt_service.render_prompt(template, generation_context)
        
        # Generate single slide content
        single_slide_schema = self._get_single_slide_schema()
        generated_content = await self._ai_service.generate_structured_content(
            ContentGenerationType.SLIDE,
            prompt,
            single_slide_schema,
            generation_context
        )
        
        # Create slide entity
        slide = Slide(
            course_id=course_id,
            title=generated_content.get('title', content_focus),
            content=generated_content.get('content', ''),
            slide_type=self._determine_slide_type(slide_type),
            topic=topic,
            notes=generated_content.get('notes', ''),
            duration_minutes=generated_content.get('duration_minutes', 5)
        )
        
        # Set order based on existing slides
        existing_slides = await self._slide_repository.get_by_course_id(course_id)
        slide.order = len(existing_slides) + 1
        
        # Save slide
        return await self._slide_repository.create(slide)
    
    async def regenerate_slide(self, slide_id: str, new_focus: str = None, 
                              context: Dict[str, Any] = None) -> Slide:
        """Regenerate an existing slide with new content"""
        if not slide_id:
            raise ValueError("Slide ID is required")
        
        # Get existing slide
        existing_slide = await self._slide_repository.get_by_id(slide_id)
        if not existing_slide:
            raise ValueError(f"Slide with ID {slide_id} not found")
        
        # Use new focus or keep existing title
        content_focus = new_focus or existing_slide.title
        
        # Generate new content
        regenerated_slide = await self.generate_single_slide(
            course_id=existing_slide.course_id,
            topic=existing_slide.topic,
            slide_type=existing_slide.slide_type.value,
            content_focus=content_focus,
            context=context
        )
        
        # Update existing slide properties
        existing_slide.title = regenerated_slide.title
        existing_slide.content = regenerated_slide.content
        existing_slide.notes = regenerated_slide.notes
        existing_slide.duration_minutes = regenerated_slide.duration_minutes
        existing_slide.updated_at = datetime.utcnow()
        
        # Save updated slide
        return await self._slide_repository.update(existing_slide)
    
    async def customize_slide_template(self, course_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Customize slide template based on course requirements"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not template_data:
            raise ValueError("Template data is required")
        
        # Get course context
        syllabus = await self._syllabus_repository.get_by_course_id(course_id)
        course_context = self._extract_syllabus_context(syllabus) if syllabus else {}
        
        # Prepare customization context
        customization_context = {
            'course_id': course_id,
            'template_data': template_data,
            'course_context': course_context
        }
        
        # Get template customization prompt
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.SLIDE, "template_customization"
        )
        
        # Render prompt
        prompt = self._prompt_service.render_prompt(template, customization_context)
        
        # Generate customized template
        template_schema = self._get_template_customization_schema()
        customized_template = await self._ai_service.generate_structured_content(
            ContentGenerationType.SLIDE,
            prompt,
            template_schema,
            customization_context
        )
        
        return customized_template
    
    # Helper methods
    def _determine_slide_type(self, type_str: str) -> SlideType:
        """Determine slide type from string"""
        type_mapping = {
            'title': SlideType.TITLE,
            'content': SlideType.CONTENT,
            'exercise': SlideType.EXERCISE,
            'summary': SlideType.SUMMARY,
            'quiz': SlideType.QUIZ
        }
        return type_mapping.get(type_str.lower(), SlideType.CONTENT)
    
    def _extract_syllabus_context(self, syllabus) -> Dict[str, Any]:
        """Extract relevant context from syllabus"""
        if not syllabus:
            return {}
        
        return {
            'learning_objectives': syllabus.learning_objectives,
            'topics': syllabus.topics,
            'difficulty_level': syllabus.difficulty_level.value,
            'estimated_duration': syllabus.estimated_duration,
            'category': syllabus.category
        }
    
    def _get_slides_schema(self, slide_count: int) -> Dict[str, Any]:
        """Get schema for slides generation"""
        return {
            "type": "object",
            "properties": {
                "slides": {
                    "type": "array",
                    "minItems": slide_count,
                    "maxItems": slide_count,
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Slide title"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["title", "content", "exercise", "summary", "quiz"],
                                "description": "Type of slide"
                            },
                            "content": {
                                "type": "string",
                                "description": "Main slide content in markdown format"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Speaker notes for the slide"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 30,
                                "description": "Estimated time to present this slide"
                            },
                            "learning_objectives": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Learning objectives covered by this slide"
                            },
                            "key_concepts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Key concepts introduced in this slide"
                            }
                        },
                        "required": ["title", "type", "content"]
                    }
                }
            },
            "required": ["slides"]
        }
    
    def _get_single_slide_schema(self) -> Dict[str, Any]:
        """Get schema for single slide generation"""
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Slide title"
                },
                "content": {
                    "type": "string",
                    "description": "Main slide content in markdown format"
                },
                "notes": {
                    "type": "string",
                    "description": "Speaker notes for the slide"
                },
                "duration_minutes": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 30,
                    "description": "Estimated time to present this slide"
                },
                "learning_objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Learning objectives covered by this slide"
                },
                "key_concepts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key concepts introduced in this slide"
                }
            },
            "required": ["title", "content"]
        }
    
    def _get_template_customization_schema(self) -> Dict[str, Any]:
        """Get schema for template customization"""
        return {
            "type": "object",
            "properties": {
                "template_name": {
                    "type": "string",
                    "description": "Name of the customized template"
                },
                "template_description": {
                    "type": "string",
                    "description": "Description of template purpose and usage"
                },
                "slide_structure": {
                    "type": "object",
                    "properties": {
                        "header_format": {"type": "string"},
                        "content_format": {"type": "string"},
                        "footer_format": {"type": "string"}
                    }
                },
                "styling_preferences": {
                    "type": "object",
                    "properties": {
                        "color_scheme": {"type": "string"},
                        "font_preferences": {"type": "string"},
                        "layout_style": {"type": "string"}
                    }
                },
                "content_guidelines": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Guidelines for content creation with this template"
                }
            },
            "required": ["template_name", "template_description", "slide_structure"]
        }