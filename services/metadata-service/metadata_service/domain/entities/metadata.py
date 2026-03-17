"""
Metadata Entity - Domain Model

BUSINESS REQUIREMENT:
Unified metadata model for all platform entities enabling advanced search,
filtering, recommendations, and intelligent discovery.

DESIGN PATTERN:
Domain-Driven Design (DDD) - Entity with rich domain logic
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
import json


# Custom Exceptions
class MetadataValidationError(ValueError):
    """Raised when metadata validation fails"""
    pass


class InvalidEntityTypeError(MetadataValidationError):
    """Raised when entity_type is not valid"""
    pass


@dataclass
class Metadata:
    """
    Metadata Entity - Core domain model for platform metadata

    DOMAIN RESPONSIBILITY:
    Encapsulates all metadata for an entity with validation, normalization,
    and query helper methods for search and discovery.

    VALID ENTITY TYPES:
    - course: Educational courses
    - content: Course content (lessons, videos, slides)
    - user: Students and instructors
    - lab: Lab environments
    - project: Student projects
    - track: Learning tracks
    - quiz: Quizzes and assessments
    - exercise: Practice exercises
    - video: Video content
    - slide: Presentation slides
    """

    # Required fields
    entity_id: UUID
    entity_type: str

    # Optional fields
    metadata: Dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    # Auto-generated fields
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    # Valid entity types
    VALID_ENTITY_TYPES = [
        'course', 'content', 'user', 'lab', 'project',
        'track', 'quiz', 'exercise', 'video', 'slide',
        'course_material_upload', 'course_material_download',  # File tracking
        'test'  # test for unit testing
    ]

    # Field constraints
    MAX_TITLE_LENGTH = 1000
    MAX_DESCRIPTION_LENGTH = 10000

    def __post_init__(self):
        """Validate and normalize metadata after initialization"""
        self._validate()
        self._normalize()

    def _validate(self):
        """
        Validate metadata fields

        VALIDATION RULES:
        - entity_id must not be None
        - entity_type must be in VALID_ENTITY_TYPES
        - title must not exceed MAX_TITLE_LENGTH
        - description must not exceed MAX_DESCRIPTION_LENGTH
        - metadata dict must be JSON serializable
        """
        # Validate entity_id
        if self.entity_id is None:
            raise MetadataValidationError("entity_id cannot be None")

        # Validate entity_type
        if not self.entity_type or self.entity_type.strip() == "":
            raise MetadataValidationError("entity_type cannot be empty")

        if self.entity_type not in self.VALID_ENTITY_TYPES:
            raise InvalidEntityTypeError(
                f"Invalid entity_type '{self.entity_type}'. "
                f"Must be one of: {', '.join(self.VALID_ENTITY_TYPES)}"
            )

        # Validate title length
        if self.title and len(self.title) > self.MAX_TITLE_LENGTH:
            raise MetadataValidationError(
                f"title exceeds maximum length of {self.MAX_TITLE_LENGTH} characters"
            )

        # Validate description length
        if self.description and len(self.description) > self.MAX_DESCRIPTION_LENGTH:
            raise MetadataValidationError(
                f"description exceeds maximum length of {self.MAX_DESCRIPTION_LENGTH} characters"
            )

        # Validate metadata is JSON serializable
        if self.metadata:
            try:
                json.dumps(self.metadata)
            except (TypeError, ValueError) as e:
                raise MetadataValidationError(
                    f"metadata dict is not JSON serializable: {str(e)}"
                )

    def _normalize(self):
        """
        Normalize metadata fields

        NORMALIZATION:
        - Convert tags to lowercase and strip whitespace
        - Convert keywords to lowercase and strip whitespace
        - Ensure metadata is a dict (not None)
        """
        # Normalize tags
        if self.tags:
            self.tags = [
                tag.strip().lower()
                for tag in self.tags
                if tag and tag.strip()
            ]

        # Normalize keywords
        if self.keywords:
            self.keywords = [
                keyword.strip().lower()
                for keyword in self.keywords
                if keyword and keyword.strip()
            ]

        # Ensure metadata is a dict
        if self.metadata is None:
            self.metadata = {}

    def update(self, **kwargs):
        """
        Update metadata fields

        BUSINESS LOGIC:
        - Updates specified fields
        - Automatically updates updated_at timestamp
        - Validates after update

        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.updated_at = datetime.now(timezone.utc)
        self._validate()
        self._normalize()

    def merge_metadata(self, new_metadata: Dict[str, Any]):
        """
        Merge new metadata dict with existing metadata

        MERGE STRATEGY:
        - Deep merge for nested dictionaries
        - New values override existing values
        - Preserves existing keys not in new_metadata

        Args:
            new_metadata: Dictionary to merge
        """
        def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
            """Recursively merge dict2 into dict1"""
            result = dict1.copy()
            for key, value in dict2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        self.metadata = deep_merge(self.metadata, new_metadata)
        self.updated_at = datetime.now(timezone.utc)

    def get_search_text(self) -> str:
        """
        Generate searchable text from metadata

        SEARCH TEXT COMPOSITION:
        - Title (highest weight)
        - Description
        - Tags
        - Keywords

        Returns:
            Combined searchable text
        """
        parts = []

        if self.title:
            parts.append(self.title)

        if self.description:
            parts.append(self.description)

        if self.tags:
            parts.extend(self.tags)

        if self.keywords:
            parts.extend(self.keywords)

        return " ".join(parts)

    def get_topics(self) -> List[str]:
        """
        Extract topics from metadata

        EXTRACTION PATH:
        metadata.educational.topics

        Returns:
            List of topics or empty list
        """
        try:
            return self.metadata.get("educational", {}).get("topics", [])
        except (AttributeError, TypeError):
            return []

    def get_difficulty(self) -> Optional[str]:
        """
        Extract difficulty level from metadata

        EXTRACTION PATH:
        metadata.educational.difficulty

        Returns:
            Difficulty level or None
        """
        try:
            return self.metadata.get("educational", {}).get("difficulty")
        except (AttributeError, TypeError):
            return None

    def get_metadata_value(self, path: str, default: Any = None) -> Any:
        """
        Get nested metadata value by dot-separated path

        USAGE:
        metadata.get_metadata_value("educational.quality.rating")

        Args:
            path: Dot-separated path (e.g., "key1.key2.key3")
            default: Default value if path not found

        Returns:
            Value at path or default
        """
        keys = path.split(".")
        value = self.metadata

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value

    def set_metadata_value(self, path: str, value: Any):
        """
        Set nested metadata value by dot-separated path

        USAGE:
        metadata.set_metadata_value("educational.quality.rating", 4.5)

        Creates nested dictionaries as needed

        Args:
            path: Dot-separated path
            value: Value to set
        """
        keys = path.split(".")
        current = self.metadata

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Set the final key
        current[keys[-1]] = value
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metadata entity to dictionary

        SERIALIZATION:
        - UUID fields converted to strings
        - Datetime fields converted to ISO format

        Returns:
            Dictionary representation
        """
        return {
            "id": str(self.id),
            "entity_id": str(self.entity_id),
            "entity_type": self.entity_type,
            "metadata": self.metadata,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "keywords": self.keywords,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_by": str(self.updated_by) if self.updated_by else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metadata':
        """
        Create metadata entity from dictionary

        DESERIALIZATION:
        - String UUIDs converted to UUID objects
        - ISO datetime strings converted to datetime objects

        Args:
            data: Dictionary representation

        Returns:
            Metadata entity
        """
        # Convert string UUIDs to UUID objects
        if isinstance(data.get("id"), str):
            data["id"] = UUID(data["id"])
        if isinstance(data.get("entity_id"), str):
            data["entity_id"] = UUID(data["entity_id"])
        if isinstance(data.get("created_by"), str):
            data["created_by"] = UUID(data["created_by"])
        if isinstance(data.get("updated_by"), str):
            data["updated_by"] = UUID(data["updated_by"])

        # Convert ISO datetime strings to datetime objects
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return cls(**data)

    def __eq__(self, other: object) -> bool:
        """
        Equality comparison

        EQUALITY RULE:
        Two metadata entities are equal if they have the same entity_id and entity_type

        Args:
            other: Object to compare

        Returns:
            True if equal, False otherwise
        """
        if not isinstance(other, Metadata):
            return False

        return (
            self.entity_id == other.entity_id and
            self.entity_type == other.entity_type
        )

    def __str__(self) -> str:
        """
        String representation

        Returns:
            Human-readable string
        """
        title_part = f" - {self.title}" if self.title else ""
        return f"Metadata({self.entity_type}: {self.entity_id}{title_part})"

    def __repr__(self) -> str:
        """Technical representation"""
        return (
            f"Metadata(id={self.id}, entity_id={self.entity_id}, "
            f"entity_type={self.entity_type}, title={self.title})"
        )
