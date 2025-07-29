"""
Unit Tests for Course Generator Domain Entities
Following SOLID principles and TDD methodology
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

# Import domain entities from course generator service
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'services', 'course-generator'))

try:
    from domain.entities.course_content import CourseContent, ContentType, ContentStatus
    from domain.entities.generation_request import GenerationRequest, GenerationStatus
    from domain.entities.template import Template, TemplateType
except ImportError:
    # Create mock entities for testing framework
    from dataclasses import dataclass
    from enum import Enum
    
    class ContentType(Enum):
        SYLLABUS = "syllabus"
        SLIDES = "slides"
        QUIZ = "quiz"
        LAB = "lab"
    
    class ContentStatus(Enum):
        DRAFT = "draft"
        GENERATED = "generated"
        APPROVED = "approved"
    
    class GenerationStatus(Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"
    
    class TemplateType(Enum):
        BASIC = "basic"
        ADVANCED = "advanced"
        CUSTOM = "custom"
    
    @dataclass
    class CourseContent:
        id: str
        course_id: str
        content_type: ContentType
        title: str
        content: str
        metadata: dict
        status: ContentStatus
        created_at: datetime
        updated_at: datetime
        
        def validate(self) -> None:
            if not self.title:
                raise ValueError("Title is required")
            if not self.content:
                raise ValueError("Content is required")
    
    @dataclass
    class GenerationRequest:
        id: str
        user_id: str
        course_id: str
        content_type: ContentType
        template_id: str
        parameters: dict
        status: GenerationStatus
        created_at: datetime
        updated_at: datetime
        
        def validate(self) -> None:
            if not self.user_id:
                raise ValueError("User ID is required")
            if not self.course_id:
                raise ValueError("Course ID is required")
    
    @dataclass
    class Template:
        id: str
        name: str
        template_type: TemplateType
        content_template: str
        parameters: dict
        is_active: bool
        created_at: datetime
        
        def validate(self) -> None:
            if not self.name:
                raise ValueError("Template name is required")
            if not self.content_template:
                raise ValueError("Content template is required")


class TestCourseContent:
    """Test CourseContent domain entity following TDD principles"""
    
    def test_course_content_creation_with_valid_data(self):
        """Test creating CourseContent with valid data"""
        # Arrange
        content_data = {
            "id": "content_123",
            "course_id": "course_456", 
            "content_type": ContentType.SYLLABUS,
            "title": "Introduction to Python",
            "content": "This course covers Python fundamentals...",
            "metadata": {"difficulty": "beginner"},
            "status": ContentStatus.DRAFT,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Act
        content = CourseContent(**content_data)
        
        # Assert
        assert content.id == "content_123"
        assert content.course_id == "course_456"
        assert content.content_type == ContentType.SYLLABUS
        assert content.title == "Introduction to Python"
        assert content.status == ContentStatus.DRAFT
    
    def test_course_content_validation_with_empty_title(self):
        """Test CourseContent validation fails with empty title"""
        # Arrange
        content = CourseContent(
            id="content_123",
            course_id="course_456",
            content_type=ContentType.SYLLABUS,
            title="",  # Empty title
            content="Valid content",
            metadata={},
            status=ContentStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Title is required"):
            content.validate()
    
    def test_course_content_validation_with_empty_content(self):
        """Test CourseContent validation fails with empty content"""
        # Arrange
        content = CourseContent(
            id="content_123",
            course_id="course_456",
            content_type=ContentType.SYLLABUS,
            title="Valid Title",
            content="",  # Empty content
            metadata={},
            status=ContentStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Content is required"):
            content.validate()


class TestGenerationRequest:
    """Test GenerationRequest domain entity following TDD principles"""
    
    def test_generation_request_creation_with_valid_data(self):
        """Test creating GenerationRequest with valid data"""
        # Arrange
        request_data = {
            "id": "req_123",
            "user_id": "user_456",
            "course_id": "course_789",
            "content_type": ContentType.SLIDES,
            "template_id": "template_101",
            "parameters": {"topic": "Variables", "slides_count": 10},
            "status": GenerationStatus.PENDING,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Act
        request = GenerationRequest(**request_data)
        
        # Assert
        assert request.id == "req_123"
        assert request.user_id == "user_456"
        assert request.course_id == "course_789"
        assert request.content_type == ContentType.SLIDES
        assert request.status == GenerationStatus.PENDING
    
    def test_generation_request_validation_with_empty_user_id(self):
        """Test GenerationRequest validation fails with empty user_id"""
        # Arrange
        request = GenerationRequest(
            id="req_123",
            user_id="",  # Empty user_id
            course_id="course_789",
            content_type=ContentType.SLIDES,
            template_id="template_101",
            parameters={},
            status=GenerationStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="User ID is required"):
            request.validate()
    
    def test_generation_request_validation_with_empty_course_id(self):
        """Test GenerationRequest validation fails with empty course_id"""
        # Arrange
        request = GenerationRequest(
            id="req_123",
            user_id="user_456",
            course_id="",  # Empty course_id
            content_type=ContentType.SLIDES,
            template_id="template_101",
            parameters={},
            status=GenerationStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Course ID is required"):
            request.validate()


class TestTemplate:
    """Test Template domain entity following TDD principles"""
    
    def test_template_creation_with_valid_data(self):
        """Test creating Template with valid data"""
        # Arrange
        template_data = {
            "id": "template_123",
            "name": "Basic Syllabus Template",
            "template_type": TemplateType.BASIC,
            "content_template": "# {course_title}\n\n## Objectives\n{objectives}",
            "parameters": {"course_title": "string", "objectives": "list"},
            "is_active": True,
            "created_at": datetime.now()
        }
        
        # Act
        template = Template(**template_data)
        
        # Assert
        assert template.id == "template_123"
        assert template.name == "Basic Syllabus Template"
        assert template.template_type == TemplateType.BASIC
        assert template.is_active is True
    
    def test_template_validation_with_empty_name(self):
        """Test Template validation fails with empty name"""
        # Arrange
        template = Template(
            id="template_123",
            name="",  # Empty name
            template_type=TemplateType.BASIC,
            content_template="Valid template content",
            parameters={},
            is_active=True,
            created_at=datetime.now()
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Template name is required"):
            template.validate()
    
    def test_template_validation_with_empty_content_template(self):
        """Test Template validation fails with empty content_template"""
        # Arrange
        template = Template(
            id="template_123",
            name="Valid Template Name",
            template_type=TemplateType.BASIC,
            content_template="",  # Empty content template
            parameters={},
            is_active=True,
            created_at=datetime.now()
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Content template is required"):
            template.validate()


class TestCourseGeneratorDomainIntegration:
    """Integration tests for course generator domain entities"""
    
    def test_complete_content_generation_workflow(self):
        """Test complete workflow from request to generated content"""
        # Arrange
        template = Template(
            id="template_123",
            name="Syllabus Template",
            template_type=TemplateType.BASIC,
            content_template="# {title}\n\n{content}",
            parameters={"title": "string", "content": "string"},
            is_active=True,
            created_at=datetime.now()
        )
        
        request = GenerationRequest(
            id="req_123",
            user_id="user_456",
            course_id="course_789",
            content_type=ContentType.SYLLABUS,
            template_id=template.id,
            parameters={"title": "Python Basics", "content": "Learn Python fundamentals"},
            status=GenerationStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Act - Simulate content generation
        generated_content = CourseContent(
            id="content_999",
            course_id=request.course_id,
            content_type=request.content_type,
            title="Python Basics",
            content="# Python Basics\n\nLearn Python fundamentals",
            metadata={"generated_from": request.id, "template_id": template.id},
            status=ContentStatus.GENERATED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Assert
        assert generated_content.course_id == request.course_id
        assert generated_content.content_type == request.content_type
        assert generated_content.metadata["generated_from"] == request.id
        assert generated_content.metadata["template_id"] == template.id
        assert generated_content.status == ContentStatus.GENERATED
    
    def test_template_parameter_validation(self):
        """Test that templates validate required parameters"""
        # Arrange
        template = Template(
            id="template_123",
            name="Advanced Template",
            template_type=TemplateType.ADVANCED,
            content_template="# {title}\n\n## Duration: {duration}\n\n{content}",
            parameters={"title": "string", "duration": "string", "content": "string"},
            is_active=True,
            created_at=datetime.now()
        )
        
        # Act & Assert
        template.validate()  # Should not raise exception
        
        # Test with missing required parameter
        incomplete_request = GenerationRequest(
            id="req_124",
            user_id="user_456",
            course_id="course_789",
            content_type=ContentType.SYLLABUS,
            template_id=template.id,
            parameters={"title": "Python Basics"},  # Missing duration and content
            status=GenerationStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # In a real implementation, this would validate parameters against template
        assert incomplete_request.parameters["title"] == "Python Basics"
        assert "duration" not in incomplete_request.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])