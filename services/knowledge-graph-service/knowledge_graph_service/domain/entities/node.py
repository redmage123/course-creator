"""
Knowledge Graph Node Entity

BUSINESS REQUIREMENT:
Represent entities (courses, concepts, skills, topics) as nodes
in the knowledge graph for relationship modeling.

TECHNICAL IMPLEMENTATION:
- Immutable node entity with validation
- Support for multiple node types
- Flexible properties via dictionary
- Type-safe entity references

WHY:
Nodes are the foundation of the knowledge graph, enabling us to
represent any educational entity with consistent semantics.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class NodeType(Enum):
    """
    Types of nodes in the knowledge graph

    BUSINESS CONTEXT:
    Different entity types have different semantics and relationships
    """
    COURSE = 'course'
    TOPIC = 'topic'
    CONCEPT = 'concept'
    SKILL = 'skill'
    LEARNING_OUTCOME = 'learning_outcome'
    RESOURCE = 'resource'


class InvalidNodeTypeError(ValueError):
    """Raised when invalid node type is provided"""
    pass


class MissingRequiredPropertyError(ValueError):
    """Raised when required property is missing"""
    pass


@dataclass
class Node:
    """
    Knowledge Graph Node Entity

    BUSINESS VALUE:
    Represents any entity in the educational knowledge graph with
    standardized structure for relationships and queries.

    PROPERTIES:
    - id: Unique node identifier
    - node_type: Type of entity (course, concept, etc.)
    - entity_id: Reference to actual entity in its source table
    - label: Human-readable name
    - properties: Flexible property dictionary
    - metadata: Additional metadata

    VALIDATION:
    - node_type must be valid NodeType
    - entity_id must be valid UUID
    - label cannot be empty
    - properties must be dictionary
    """

    # Required fields
    node_type: NodeType
    entity_id: UUID
    label: str

    # Optional fields
    id: UUID = field(default_factory=uuid4)
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    def __post_init__(self):
        """
        Validate node after initialization

        WHY: Ensure data integrity at creation time
        """
        # Convert string to NodeType enum if needed
        if isinstance(self.node_type, str):
            try:
                self.node_type = NodeType(self.node_type)
            except ValueError:
                raise InvalidNodeTypeError(
                    f"Invalid node type: {self.node_type}. "
                    f"Must be one of: {[t.value for t in NodeType]}"
                )

        # Validate label
        if not self.label or not self.label.strip():
            raise ValueError("Node label cannot be empty")

        # Validate entity_id
        if not isinstance(self.entity_id, UUID):
            try:
                self.entity_id = UUID(str(self.entity_id))
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid entity_id: {self.entity_id}")

        # Validate properties is dict
        if not isinstance(self.properties, dict):
            raise TypeError("Properties must be a dictionary")

        # Validate metadata is dict
        if not isinstance(self.metadata, dict):
            raise TypeError("Metadata must be a dictionary")

    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get property value with default

        WHY: Safe property access with fallback
        """
        return self.properties.get(key, default)

    def set_property(self, key: str, value: Any) -> None:
        """
        Set property value

        WHY: Controlled property mutation
        """
        self.properties[key] = value
        self.updated_at = datetime.now()

    def has_property(self, key: str) -> bool:
        """Check if property exists"""
        return key in self.properties

    def remove_property(self, key: str) -> None:
        """Remove property if exists"""
        if key in self.properties:
            del self.properties[key]
            self.updated_at = datetime.now()

    def get_difficulty(self) -> Optional[str]:
        """
        Get difficulty level for course nodes

        WHY: Common property for course nodes
        """
        return self.get_property('difficulty')

    def get_complexity(self) -> Optional[str]:
        """
        Get complexity level for concept nodes

        WHY: Common property for concept nodes
        """
        return self.get_property('complexity')

    def get_category(self) -> Optional[str]:
        """Get category/domain"""
        return self.get_property('category') or self.get_property('domain')

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node to dictionary

        WHY: Serialization for API responses and database storage
        """
        return {
            'id': str(self.id),
            'node_type': self.node_type.value,
            'entity_id': str(self.entity_id),
            'label': self.label,
            'properties': self.properties,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_by': str(self.updated_by) if self.updated_by else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """
        Create node from dictionary

        WHY: Deserialization from database or API
        """
        return cls(
            id=UUID(data['id']) if 'id' in data else uuid4(),
            node_type=NodeType(data['node_type']),
            entity_id=UUID(data['entity_id']),
            label=data['label'],
            properties=data.get('properties', {}),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now(),
            created_by=UUID(data['created_by']) if data.get('created_by') else None,
            updated_by=UUID(data['updated_by']) if data.get('updated_by') else None
        )

    def __eq__(self, other):
        """Equality based on node_type and entity_id"""
        if not isinstance(other, Node):
            return False
        return (
            self.node_type == other.node_type and
            self.entity_id == other.entity_id
        )

    def __hash__(self):
        """Hash based on node_type and entity_id"""
        return hash((self.node_type, self.entity_id))

    def __repr__(self):
        """String representation"""
        return f"Node({self.node_type.value}, {self.label}, {self.id})"


# Type-specific node factory functions

def create_course_node(
    entity_id: UUID,
    label: str,
    difficulty: Optional[str] = None,
    duration: Optional[int] = None,
    category: Optional[str] = None,
    **kwargs
) -> Node:
    """
    Factory for creating course nodes

    WHY: Convenience function with course-specific defaults
    """
    properties = {}
    if difficulty:
        properties['difficulty'] = difficulty
    if duration:
        properties['duration'] = duration
    if category:
        properties['category'] = category

    properties.update(kwargs)

    return Node(
        node_type=NodeType.COURSE,
        entity_id=entity_id,
        label=label,
        properties=properties
    )


def create_concept_node(
    entity_id: UUID,
    label: str,
    complexity: Optional[str] = None,
    domain: Optional[str] = None,
    **kwargs
) -> Node:
    """
    Factory for creating concept nodes

    WHY: Convenience function with concept-specific defaults
    """
    properties = {}
    if complexity:
        properties['complexity'] = complexity
    if domain:
        properties['domain'] = domain

    properties.update(kwargs)

    return Node(
        node_type=NodeType.CONCEPT,
        entity_id=entity_id,
        label=label,
        properties=properties
    )


def create_skill_node(
    entity_id: UUID,
    label: str,
    proficiency_level: Optional[str] = None,
    category: Optional[str] = None,
    **kwargs
) -> Node:
    """
    Factory for creating skill nodes

    WHY: Convenience function with skill-specific defaults
    """
    properties = {}
    if proficiency_level:
        properties['proficiency_level'] = proficiency_level
    if category:
        properties['category'] = category

    properties.update(kwargs)

    return Node(
        node_type=NodeType.SKILL,
        entity_id=entity_id,
        label=label,
        properties=properties
    )
