"""
Base Content Entity - Domain Layer
Single Responsibility: Base content entity with common attributes and behavior
Open/Closed: Extensible for different content types
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class ContentType(Enum):
    """Content type enumeration"""
    SYLLABUS = "syllabus"
    SLIDE = "slide"
    QUIZ = "quiz"
    EXERCISE = "exercise"
    LAB_ENVIRONMENT = "lab_environment"


class ContentStatus(Enum):
    """Content status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BaseContent(ABC):
    """
    Base content entity following SOLID principles
    Single Responsibility: Core content attributes and validation
    """
    
    def __init__(
        self,
        title: str,
        course_id: str,
        created_by: str,
        id: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: ContentStatus = ContentStatus.DRAFT,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.description = description or ""
        self.course_id = course_id
        self.created_by = created_by
        self.tags = tags or []
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.metadata = metadata or {}
        
        # Domain validation
        self.validate()
    
    @abstractmethod
    def get_content_type(self) -> ContentType:
        """Get the content type - must be implemented by subclasses"""
        pass
    
    def validate(self) -> None:
        """Validate entity state"""
        if not self.title:
            raise ValueError("Title is required")
        if not self.course_id:
            raise ValueError("Course ID is required")
        if not self.created_by:
            raise ValueError("Created by is required")
    
    def update_title(self, title: str) -> None:
        """Update content title"""
        if not title:
            raise ValueError("Title cannot be empty")
        self.title = title
        self._mark_updated()
    
    def update_description(self, description: str) -> None:
        """Update content description"""
        self.description = description
        self._mark_updated()
    
    def add_tag(self, tag: str) -> None:
        """Add tag to content"""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self._mark_updated()
    
    def remove_tag(self, tag: str) -> None:
        """Remove tag from content"""
        if tag in self.tags:
            self.tags.remove(tag)
            self._mark_updated()
    
    def publish(self) -> None:
        """Publish content"""
        if self.status == ContentStatus.DRAFT:
            self.status = ContentStatus.PUBLISHED
            self._mark_updated()
        else:
            raise ValueError("Only draft content can be published")
    
    def archive(self) -> None:
        """Archive content"""
        if self.status == ContentStatus.PUBLISHED:
            self.status = ContentStatus.ARCHIVED
            self._mark_updated()
        else:
            raise ValueError("Only published content can be archived")
    
    def is_published(self) -> bool:
        """Check if content is published"""
        return self.status == ContentStatus.PUBLISHED
    
    def is_draft(self) -> bool:
        """Check if content is draft"""
        return self.status == ContentStatus.DRAFT
    
    def is_archived(self) -> bool:
        """Check if content is archived"""
        return self.status == ContentStatus.ARCHIVED
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update metadata field"""
        self.metadata[key] = value
        self._mark_updated()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata field"""
        return self.metadata.get(key, default)
    
    def _mark_updated(self) -> None:
        """Mark entity as updated"""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "course_id": self.course_id,
            "created_by": self.created_by,
            "tags": self.tags,
            "status": self.status.value,
            "content_type": self.get_content_type().value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    def __eq__(self, other) -> bool:
        """Entity equality based on ID"""
        if not isinstance(other, BaseContent):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Entity hash based on ID"""
        return hash(self.id)
    
    def __str__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}(id={self.id}, title='{self.title}')"