"""
Syllabus Generation Service Implementation
Single Responsibility: Implement syllabus generation business logic
Dependency Inversion: Depends on repository and AI service abstractions
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from ...domain.entities.course_content import Syllabus, DifficultyLevel
from ...domain.interfaces.content_generation_service import ISyllabusGenerationService
from ...domain.interfaces.content_repository import ISyllabusRepository
from ...domain.interfaces.ai_service import IAIService, ContentGenerationType, IPromptTemplateService

class SyllabusGenerationService(ISyllabusGenerationService):
    """
    Syllabus generation service implementation with business logic
    """
    
    def __init__(self, 
                 syllabus_repository: ISyllabusRepository,
                 ai_service: IAIService,
                 prompt_service: IPromptTemplateService):
        self._syllabus_repository = syllabus_repository
        self._ai_service = ai_service
        self._prompt_service = prompt_service
    
    async def generate_syllabus(self, course_id: str, title: str, description: str, 
                               category: str, difficulty_level: str, 
                               estimated_duration: int, context: Dict[str, Any] = None) -> Syllabus:
        """Generate a course syllabus using AI"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if not title or len(title.strip()) == 0:
            raise ValueError("Title is required")
        
        if not description or len(description.strip()) == 0:
            raise ValueError("Description is required")
        
        # Check if syllabus already exists for this course
        existing_syllabus = await self._syllabus_repository.get_by_course_id(course_id)
        if existing_syllabus:
            raise ValueError(f"Syllabus already exists for course {course_id}")
        
        # Validate difficulty level
        try:
            difficulty_enum = DifficultyLevel(difficulty_level.lower())
        except ValueError:
            raise ValueError(f"Invalid difficulty level: {difficulty_level}")
        
        # Prepare context for AI generation
        generation_context = {
            'title': title,
            'description': description,
            'category': category,
            'difficulty_level': difficulty_level,
            'estimated_duration': estimated_duration,
            'context': context or {}
        }
        
        # Get prompt template
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.SYLLABUS, "comprehensive"
        )
        
        # Render prompt with context
        prompt = self._prompt_service.render_prompt(template, generation_context)
        
        # Generate structured syllabus content
        syllabus_schema = self._get_syllabus_schema()
        generated_content = await self._ai_service.generate_structured_content(
            ContentGenerationType.SYLLABUS,
            prompt,
            syllabus_schema,
            generation_context
        )
        
        # Create syllabus entity
        syllabus = Syllabus(
            course_id=course_id,
            title=title,
            description=description,
            category=category,
            difficulty_level=difficulty_enum,
            estimated_duration=estimated_duration
        )
        
        # Populate with AI-generated content
        self._populate_syllabus_from_ai_content(syllabus, generated_content)
        
        # Save to repository
        return await self._syllabus_repository.create(syllabus)
    
    async def update_syllabus(self, syllabus: Syllabus, updates: Dict[str, Any]) -> Syllabus:
        """Update an existing syllabus"""
        if not syllabus.id:
            raise ValueError("Syllabus ID is required for update")
        
        # Check if syllabus exists
        existing_syllabus = await self._syllabus_repository.get_by_id(syllabus.id)
        if not existing_syllabus:
            raise ValueError(f"Syllabus with ID {syllabus.id} not found")
        
        # Apply updates
        if 'title' in updates:
            syllabus.title = updates['title']
        
        if 'description' in updates:
            syllabus.description = updates['description']
        
        if 'learning_objectives' in updates:
            syllabus.learning_objectives = updates['learning_objectives']
        
        if 'topics' in updates:
            syllabus.topics = updates['topics']
        
        if 'prerequisites' in updates:
            syllabus.prerequisites = updates['prerequisites']
        
        if 'resources' in updates:
            syllabus.resources = updates['resources']
        
        if 'assessment_methods' in updates:
            syllabus.assessment_methods = updates['assessment_methods']
        
        # Validate updated syllabus
        syllabus.validate()
        
        # Save changes
        return await self._syllabus_repository.update(syllabus)
    
    async def analyze_syllabus_content(self, content: str) -> Dict[str, Any]:
        """Analyze uploaded syllabus content and extract structured data"""
        if not content or len(content.strip()) == 0:
            raise ValueError("Content cannot be empty")
        
        # Prepare analysis prompt
        analysis_context = {
            'content': content,
            'extract_objectives': True,
            'extract_topics': True,
            'extract_prerequisites': True,
            'extract_resources': True
        }
        
        template = self._prompt_service.get_prompt_template(
            ContentGenerationType.SYLLABUS, "analysis"
        )
        
        prompt = self._prompt_service.render_prompt(template, analysis_context)
        
        # Analyze content using AI
        analysis_schema = self._get_syllabus_analysis_schema()
        analysis_result = await self._ai_service.generate_structured_content(
            ContentGenerationType.SYLLABUS,
            prompt,
            analysis_schema,
            analysis_context
        )
        
        return analysis_result
    
    # Helper methods
    def _get_syllabus_schema(self) -> Dict[str, Any]:
        """Get schema for structured syllabus generation"""
        return {
            "type": "object",
            "properties": {
                "learning_objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific learning objectives"
                },
                "topics": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "duration_hours": {"type": "integer"},
                            "subtopics": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["name", "duration_hours"]
                    }
                },
                "prerequisites": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of course prerequisites"
                },
                "resources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "type": {"type": "string"},
                            "url": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["title", "type"]
                    }
                },
                "assessment_methods": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of assessment methods"
                }
            },
            "required": ["learning_objectives", "topics", "assessment_methods"]
        }
    
    def _get_syllabus_analysis_schema(self) -> Dict[str, Any]:
        """Get schema for syllabus content analysis"""
        return {
            "type": "object",
            "properties": {
                "extracted_title": {"type": "string"},
                "extracted_description": {"type": "string"},
                "estimated_difficulty": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced"]
                },
                "estimated_duration": {"type": "integer"},
                "learning_objectives": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "topics": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "duration_hours": {"type": "integer"}
                        }
                    }
                },
                "prerequisites": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "subject_category": {"type": "string"},
                "quality_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                }
            }
        }
    
    def _populate_syllabus_from_ai_content(self, syllabus: Syllabus, content: Dict[str, Any]) -> None:
        """Populate syllabus entity with AI-generated content"""
        if 'learning_objectives' in content:
            syllabus.learning_objectives = content['learning_objectives']
        
        if 'topics' in content:
            syllabus.topics = content['topics']
        
        if 'prerequisites' in content:
            syllabus.prerequisites = content['prerequisites']
        
        if 'resources' in content:
            syllabus.resources = content['resources']
        
        if 'assessment_methods' in content:
            syllabus.assessment_methods = content['assessment_methods']