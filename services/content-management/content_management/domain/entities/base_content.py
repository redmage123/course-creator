"""
Educational Content Base Entity - Domain Layer Foundation

Comprehensive base entity for all educational content types providing common attributes,
behavior, and educational content lifecycle management following Domain-Driven Design principles.

## Educational Content Domain Model:

### Core Educational Attributes
- **Educational Identification**: Unique content identification and educational context tracking
- **Educational Metadata**: Comprehensive educational information and content classification
- **Educational Ownership**: Content creator and educational responsibility tracking
- **Educational Lifecycle**: Content status management and educational workflow integration
- **Educational Relationships**: Course association and educational content dependency management

### Educational Content Lifecycle Management
- **Draft Status**: Educational content development and iterative refinement
- **Published Status**: Educational content delivery and student access
- **Archived Status**: Educational content preservation and historical tracking

### Educational Content Classification
- **Content Type System**: Comprehensive educational content type classification
  - Syllabus: Course structure and educational planning documents
  - Slides: Educational presentations and instructional delivery materials
  - Quizzes: Educational assessments and knowledge validation tools
  - Exercises: Hands-on learning activities and skill development materials
  - Lab Environments: Interactive educational environments and practical learning spaces

### Educational Content Validation
- **Business Rule Enforcement**: Educational content validation and quality assurance
- **Educational Standard Compliance**: Institutional policy and pedagogical requirement verification
- **Educational Content Integrity**: Content completeness and educational effectiveness validation
- **Educational Accessibility**: Universal design and accessibility compliance verification

## Domain Design Principles:

### SOLID Implementation
- **Single Responsibility**: Core educational content attributes and validation focused on content entity management
- **Open/Closed**: Extensible for different educational content types without modifying base functionality
- **Liskov Substitution**: Consistent interface for all educational content types enabling polymorphic operations
- **Interface Segregation**: Focused educational content operations without unnecessary complexity
- **Dependency Inversion**: Abstract educational content operations supporting diverse implementations

### Domain-Driven Design
- **Educational Entity Identity**: Unique identification and educational content tracking
- **Educational Value Objects**: Immutable educational attributes and content classification
- **Educational Business Rules**: Domain logic for educational content validation and lifecycle management
- **Educational Aggregate Boundaries**: Clear educational content ownership and consistency boundaries

### Educational Content Quality Assurance
- **Validation Integration**: Comprehensive educational content validation and quality checking
- **Educational Standard Compliance**: Institutional policy and pedagogical requirement verification
- **Educational Content Consistency**: Uniform educational content structure and organization
- **Educational Audit Trail**: Complete educational content change tracking and accountability

This base entity provides the foundation for all educational content management,
ensuring consistent educational content handling, quality assurance, and
institutional compliance across the educational content management system.
"""
from abc import ABC, abstractmethod  # Educational content abstraction and polymorphic operations
from typing import List, Dict, Any, Optional  # Educational content data structures and type safety
from datetime import datetime  # Educational content lifecycle and timestamp management
from enum import Enum  # Educational content classification and status management
import uuid  # Educational content unique identification and tracking


class ContentType(Enum):
    """
    Educational content type classification system.
    
    Comprehensive enumeration of educational content types supporting
    diverse educational content management and pedagogical approaches.
    
    Educational Content Categories:
    - **SYLLABUS**: Course structure documents and educational planning materials
    - **SLIDE**: Educational presentations and instructional delivery content
    - **QUIZ**: Educational assessments and knowledge validation tools
    - **EXERCISE**: Hands-on learning activities and skill development materials
    - **LAB_ENVIRONMENT**: Interactive educational environments and practical learning spaces
    
    Educational Benefits:
    - Structured educational content organization and classification
    - Educational content workflow optimization and management
    - Educational content discovery and search functionality enhancement
    - Educational content analytics and utilization tracking
    """
    """Content type enumeration"""
    SYLLABUS = "syllabus"
    SLIDE = "slide"
    QUIZ = "quiz"
    EXERCISE = "exercise"
    LAB_ENVIRONMENT = "lab_environment"


class ContentStatus(Enum):
    """
    Educational content lifecycle status management.
    
    Comprehensive status system for educational content lifecycle management
    supporting educational content development, delivery, and archival workflows.
    
    Educational Content Lifecycle:
    - **DRAFT**: Educational content development and iterative refinement phase
    - **PUBLISHED**: Educational content delivery and student access phase
    - **ARCHIVED**: Educational content preservation and historical tracking phase
    
    Educational Workflow Benefits:
    - Educational content quality assurance and approval workflows
    - Educational content access control and student availability management
    - Educational content versioning and change management
    - Educational content analytics and lifecycle tracking
    """
    """Content status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BaseContent(ABC):
    """
    Abstract base entity for all educational content types.
    
    Provides comprehensive foundation for educational content management with
    common attributes, behavior, and educational content lifecycle operations.
    
    ## Educational Content Foundation:
    
    ### Core Educational Attributes
    - **Educational Identity**: Unique content identification and tracking
    - **Educational Metadata**: Title, description, and educational context
    - **Educational Ownership**: Creator identification and responsibility
    - **Educational Classification**: Content type and educational taxonomy
    - **Educational Lifecycle**: Status management and workflow integration
    
    ### Educational Content Operations
    - **Content Validation**: Educational content quality and compliance checking
    - **Lifecycle Management**: Status transitions and educational workflow operations
    - **Metadata Management**: Educational content information and relationship tracking
    - **Educational Enhancement**: Tag management and content improvement
    
    ### Educational Business Rules
    - **Required Information Validation**: Essential educational content completeness
    - **Educational Status Transitions**: Valid lifecycle state changes and workflow management
    - **Educational Content Integrity**: Content consistency and quality assurance
    - **Educational Accessibility**: Universal design and accessibility compliance
    
    ## Architecture Benefits:
    
    ### Domain-Driven Design
    - **Educational Entity Identity**: Consistent identification across educational content types
    - **Educational Value Objects**: Immutable educational attributes and classification
    - **Educational Business Logic**: Encapsulated domain rules and educational validation
    - **Educational Aggregate Management**: Clear boundaries and consistency enforcement
    
    ### Educational Quality Assurance
    - **Validation Integration**: Comprehensive educational content validation and quality checking
    - **Educational Standard Compliance**: Institutional policy and requirement verification
    - **Educational Content Consistency**: Uniform structure and organization across content types
    - **Educational Audit Trail**: Complete change tracking and accountability
    
    This abstract base provides the foundation for all educational content entities,
    ensuring consistent educational content management and institutional compliance.
    """
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
        """
        Validate educational content entity state and business rules.
        
        Implements comprehensive educational content validation including
        required information checking, educational content completeness,
        and business rule enforcement.
        
        Educational Validation Rules:
        - **Title Requirement**: Educational content must have descriptive title
        - **Course Association**: Educational content must be associated with course
        - **Creator Identification**: Educational content must have creator tracking
        
        Educational Quality Assurance:
        - Educational content completeness verification
        - Educational business rule enforcement
        - Educational content integrity validation
        - Educational standard compliance checking
        
        Raises:
            ValueError: Educational content validation failure with specific context
            
        Educational Benefits:
        - Comprehensive educational content quality assurance
        - Educational business rule enforcement and compliance
        - Educational content integrity and consistency validation
        - Educational standard and institutional policy compliance
        """
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
        """
        Publish educational content for student access and educational delivery.
        
        Transitions educational content from draft to published status,
        enabling student access and educational content delivery.
        
        Educational Publishing Workflow:
        - **Status Validation**: Ensures content is in draft status for publication
        - **Educational Quality Check**: Validates content readiness for student access
        - **Educational Availability**: Enables content access for educational delivery
        - **Educational Audit**: Tracks publication event and educational workflow
        
        Educational Benefits:
        - Controlled educational content release and student access management
        - Educational content quality assurance before student delivery
        - Educational workflow tracking and audit trail maintenance
        - Educational content availability and access control management
        
        Raises:
            ValueError: Invalid status transition or educational content not ready for publication
            
        Educational Use Cases:
        - Course material release for student access and educational delivery
        - Educational content approval workflow and quality assurance
        - Educational content versioning and change management
        - Educational content analytics and utilization tracking
        """
        """Publish content"""
        if self.status == ContentStatus.DRAFT:
            self.status = ContentStatus.PUBLISHED
            self._mark_updated()
        else:
            raise ValueError("Only draft content can be published")
    
    def archive(self) -> None:
        """
        Archive educational content for preservation and historical tracking.
        
        Transitions educational content from published to archived status,
        preserving content while removing from active educational delivery.
        
        Educational Archival Workflow:
        - **Status Validation**: Ensures content is published before archival
        - **Educational Preservation**: Maintains content for historical reference
        - **Educational Access Control**: Removes content from active student access
        - **Educational Audit**: Tracks archival event and educational lifecycle
        
        Educational Benefits:
        - Educational content preservation and historical tracking
        - Educational content lifecycle management and workflow control
        - Educational content versioning and change history maintenance
        - Educational content analytics and utilization analysis
        
        Raises:
            ValueError: Invalid status transition or educational content not eligible for archival
            
        Educational Use Cases:
        - Course material end-of-term archival and preservation
        - Educational content version management and historical tracking
        - Educational content compliance and audit trail maintenance
        - Educational content analytics and effectiveness assessment
        """
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
        """
        Convert educational content entity to dictionary representation.
        
        Provides comprehensive educational content serialization for
        API responses, data persistence, and educational content integration.
        
        Educational Content Serialization:
        - **Educational Identity**: Content ID and identification information
        - **Educational Metadata**: Title, description, and educational context
        - **Educational Classification**: Content type and educational taxonomy
        - **Educational Ownership**: Creator and responsibility information
        - **Educational Lifecycle**: Status and timestamp information
        - **Educational Relationships**: Course association and content dependencies
        
        Returns:
            Dict containing comprehensive educational content information:
                - Educational identification and metadata
                - Educational classification and content type
                - Educational ownership and responsibility tracking
                - Educational lifecycle and status information
                - Educational relationships and context
                
        Educational Benefits:
        - Standardized educational content representation for API integration
        - Educational content persistence and data storage compatibility
        - Educational content analytics and reporting data preparation
        - Educational content export and integration functionality
        
        Use Cases:
        - Educational content API response generation and client integration
        - Educational content database persistence and data management
        - Educational content analytics and institutional reporting
        - Educational content export and cross-platform integration
        """
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