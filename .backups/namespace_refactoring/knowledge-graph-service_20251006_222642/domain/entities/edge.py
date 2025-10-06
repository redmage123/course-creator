"""
Knowledge Graph Edge Entity

BUSINESS REQUIREMENT:
Represent relationships between nodes with typed edges and weights
for semantic relationship modeling.

TECHNICAL IMPLEMENTATION:
- Directed edges with source and target
- Multiple edge types for different relationships
- Weighted edges for relationship strength
- Flexible properties for edge-specific data

WHY:
Edges encode the semantics of how educational entities relate,
enabling intelligent path finding and prerequisite tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from decimal import Decimal


class EdgeType(Enum):
    """
    Types of relationships in the knowledge graph

    BUSINESS CONTEXT:
    Each edge type has specific semantics for learning paths
    """
    PREREQUISITE_OF = 'prerequisite_of'  # Course A is prerequisite of Course B
    TEACHES = 'teaches'                  # Course teaches Concept
    BUILDS_ON = 'builds_on'              # Concept builds on another Concept
    COVERS = 'covers'                    # Course covers Topic
    DEVELOPS = 'develops'                # Course develops Skill
    ACHIEVES = 'achieves'                # Course achieves Learning Outcome
    RELATES_TO = 'relates_to'            # General relationship
    PART_OF = 'part_of'                  # Topic is part of Domain
    REQUIRES = 'requires'                # Skill requires another Skill
    REFERENCES = 'references'            # Resource references Entity
    SIMILAR_TO = 'similar_to'            # Entities are similar
    ALTERNATIVE_TO = 'alternative_to'    # Alternative learning path


class InvalidEdgeTypeError(ValueError):
    """Raised when invalid edge type is provided"""
    pass


class InvalidWeightError(ValueError):
    """Raised when weight is outside valid range"""
    pass


class SelfLoopError(ValueError):
    """Raised when edge creates invalid self-loop"""
    pass


@dataclass
class Edge:
    """
    Knowledge Graph Edge Entity

    BUSINESS VALUE:
    Represents directed relationships between entities with
    semantic meaning and strength indicators.

    PROPERTIES:
    - id: Unique edge identifier
    - edge_type: Type of relationship
    - source_node_id: Starting node
    - target_node_id: Ending node
    - weight: Relationship strength (0.0 to 1.0)
    - properties: Flexible edge properties
    - metadata: Additional metadata

    VALIDATION:
    - edge_type must be valid EdgeType
    - weight must be between 0.0 and 1.0
    - source and target must be different (except for specific types)
    """

    # Required fields
    edge_type: EdgeType
    source_node_id: UUID
    target_node_id: UUID

    # Optional fields
    id: UUID = field(default_factory=uuid4)
    weight: Decimal = field(default=Decimal('1.0'))
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    def __post_init__(self):
        """
        Validate edge after initialization

        WHY: Ensure data integrity and business rules
        """
        # Convert string to EdgeType enum if needed
        if isinstance(self.edge_type, str):
            try:
                self.edge_type = EdgeType(self.edge_type)
            except ValueError:
                raise InvalidEdgeTypeError(
                    f"Invalid edge type: {self.edge_type}. "
                    f"Must be one of: {[t.value for t in EdgeType]}"
                )

        # Convert weight to Decimal if needed
        if not isinstance(self.weight, Decimal):
            self.weight = Decimal(str(self.weight))

        # Validate weight range
        if not (Decimal('0.0') <= self.weight <= Decimal('1.0')):
            raise InvalidWeightError(
                f"Weight must be between 0.0 and 1.0, got {self.weight}"
            )

        # Validate no self-loops except for specific edge types
        allowed_self_loop_types = {EdgeType.RELATES_TO, EdgeType.SIMILAR_TO}
        if self.source_node_id == self.target_node_id:
            if self.edge_type not in allowed_self_loop_types:
                raise SelfLoopError(
                    f"Self-loops not allowed for edge type {self.edge_type.value}"
                )

        # Validate UUIDs
        if not isinstance(self.source_node_id, UUID):
            try:
                self.source_node_id = UUID(str(self.source_node_id))
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid source_node_id: {self.source_node_id}")

        if not isinstance(self.target_node_id, UUID):
            try:
                self.target_node_id = UUID(str(self.target_node_id))
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid target_node_id: {self.target_node_id}")

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get property value with default"""
        return self.properties.get(key, default)

    def set_property(self, key: str, value: Any) -> None:
        """Set property value"""
        self.properties[key] = value
        self.updated_at = datetime.now()

    def has_property(self, key: str) -> bool:
        """Check if property exists"""
        return key in self.properties

    def is_strong(self, threshold: float = 0.7) -> bool:
        """
        Check if edge is strong relationship

        WHY: Distinguish between strong and weak relationships
        """
        return float(self.weight) >= threshold

    def is_weak(self, threshold: float = 0.3) -> bool:
        """Check if edge is weak relationship"""
        return float(self.weight) <= threshold

    def is_mandatory_prerequisite(self) -> bool:
        """
        Check if prerequisite is mandatory

        WHY: Business logic for course prerequisites
        """
        if self.edge_type != EdgeType.PREREQUISITE_OF:
            return False
        return self.get_property('mandatory', True)

    def is_substitutable(self) -> bool:
        """
        Check if prerequisite can be substituted

        WHY: Some prerequisites have alternatives
        """
        if self.edge_type != EdgeType.PREREQUISITE_OF:
            return False
        return self.get_property('substitutable', False)

    def get_coverage_depth(self) -> Optional[str]:
        """
        Get coverage depth for 'teaches' edges

        WHY: Understand how deeply a course covers a concept
        """
        if self.edge_type != EdgeType.TEACHES:
            return None
        return self.get_property('coverage_depth', 'medium')

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary"""
        return {
            'id': str(self.id),
            'edge_type': self.edge_type.value,
            'source_node_id': str(self.source_node_id),
            'target_node_id': str(self.target_node_id),
            'weight': float(self.weight),
            'properties': self.properties,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_by': str(self.updated_by) if self.updated_by else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Create edge from dictionary"""
        return cls(
            id=UUID(data['id']) if 'id' in data else uuid4(),
            edge_type=EdgeType(data['edge_type']),
            source_node_id=UUID(data['source_node_id']),
            target_node_id=UUID(data['target_node_id']),
            weight=Decimal(str(data.get('weight', 1.0))),
            properties=data.get('properties', {}),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now(),
            created_by=UUID(data['created_by']) if data.get('created_by') else None,
            updated_by=UUID(data['updated_by']) if data.get('updated_by') else None
        )

    def reverse(self) -> 'Edge':
        """
        Create reverse edge

        WHY: Some relationships are bidirectional
        """
        return Edge(
            edge_type=self.edge_type,
            source_node_id=self.target_node_id,
            target_node_id=self.source_node_id,
            weight=self.weight,
            properties=self.properties.copy(),
            metadata={**self.metadata, 'reversed': True}
        )

    def __eq__(self, other):
        """Equality based on edge_type and nodes"""
        if not isinstance(other, Edge):
            return False
        return (
            self.edge_type == other.edge_type and
            self.source_node_id == other.source_node_id and
            self.target_node_id == other.target_node_id
        )

    def __hash__(self):
        """Hash based on edge_type and nodes"""
        return hash((self.edge_type, self.source_node_id, self.target_node_id))

    def __repr__(self):
        """String representation"""
        return f"Edge({self.edge_type.value}, {self.source_node_id} → {self.target_node_id}, w={self.weight})"


# Factory functions for common edge types

def create_prerequisite_edge(
    source_course_id: UUID,
    target_course_id: UUID,
    weight: float = 1.0,
    mandatory: bool = True,
    substitutable: bool = False
) -> Edge:
    """
    Factory for prerequisite edges

    WHY: Convenience for course prerequisites
    """
    return Edge(
        edge_type=EdgeType.PREREQUISITE_OF,
        source_node_id=source_course_id,
        target_node_id=target_course_id,
        weight=Decimal(str(weight)),
        properties={
            'mandatory': mandatory,
            'substitutable': substitutable
        }
    )


def create_teaches_edge(
    course_id: UUID,
    concept_id: UUID,
    weight: float = 1.0,
    coverage_depth: str = 'medium',
    bloom_level: Optional[str] = None
) -> Edge:
    """
    Factory for teaching edges

    WHY: Convenience for course-concept relationships
    """
    properties = {'coverage_depth': coverage_depth}
    if bloom_level:
        properties['bloom_level'] = bloom_level

    return Edge(
        edge_type=EdgeType.TEACHES,
        source_node_id=course_id,
        target_node_id=concept_id,
        weight=Decimal(str(weight)),
        properties=properties
    )


def create_builds_on_edge(
    concept_id: UUID,
    prerequisite_concept_id: UUID,
    weight: float = 1.0,
    dependency_strength: str = 'strong'
) -> Edge:
    """
    Factory for concept dependency edges

    WHY: Convenience for concept relationships
    """
    return Edge(
        edge_type=EdgeType.BUILDS_ON,
        source_node_id=concept_id,
        target_node_id=prerequisite_concept_id,
        weight=Decimal(str(weight)),
        properties={'dependency_strength': dependency_strength}
    )
