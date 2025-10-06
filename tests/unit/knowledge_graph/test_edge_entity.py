"""
Unit Tests for Edge Entity

Tests the Edge domain entity including validation,
factory functions, and business logic.
"""

import pytest
from uuid import uuid4
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/knowledge-graph-service'))

from knowledge_graph_service.domain.entities.edge import (
    Edge,
    EdgeType,
    InvalidWeightError,
    SelfLoopError,
    create_prerequisite_edge,
    create_teaches_edge,
    create_builds_on_edge
)


class TestEdgeEntity:
    """Test suite for Edge entity"""

    def test_create_edge_with_valid_data(self):
        """Test creating an edge with valid data"""
        source = uuid4()
        target = uuid4()

        edge = Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=source,
            target_node_id=target,
            weight=Decimal('0.8')
        )

        assert edge.edge_type == EdgeType.PREREQUISITE_OF
        assert edge.source_node_id == source
        assert edge.target_node_id == target
        assert edge.weight == Decimal('0.8')

    def test_create_edge_default_weight(self):
        """Test creating edge with default weight"""
        edge = Edge(
            edge_type=EdgeType.TEACHES,
            source_node_id=uuid4(),
            target_node_id=uuid4()
        )

        assert edge.weight == Decimal('1.0')

    def test_create_edge_with_string_type(self):
        """Test creating edge with string edge type"""
        edge = Edge(
            edge_type='prerequisite_of',
            source_node_id=uuid4(),
            target_node_id=uuid4()
        )

        assert edge.edge_type == EdgeType.PREREQUISITE_OF

    def test_edge_weight_validation_too_low(self):
        """Test that weight below 0.0 raises error"""
        with pytest.raises(InvalidWeightError, match="Weight must be between 0.0 and 1.0"):
            Edge(
                edge_type=EdgeType.TEACHES,
                source_node_id=uuid4(),
                target_node_id=uuid4(),
                weight=Decimal('-0.1')
            )

    def test_edge_weight_validation_too_high(self):
        """Test that weight above 1.0 raises error"""
        with pytest.raises(InvalidWeightError, match="Weight must be between 0.0 and 1.0"):
            Edge(
                edge_type=EdgeType.TEACHES,
                source_node_id=uuid4(),
                target_node_id=uuid4(),
                weight=Decimal('1.5')
            )

    def test_edge_weight_boundary_values(self):
        """Test that 0.0 and 1.0 are valid weights"""
        edge1 = Edge(
            EdgeType.TEACHES,
            uuid4(),
            uuid4(),
            weight=Decimal('0.0')
        )
        edge2 = Edge(
            EdgeType.TEACHES,
            uuid4(),
            uuid4(),
            weight=Decimal('1.0')
        )

        assert edge1.weight == Decimal('0.0')
        assert edge2.weight == Decimal('1.0')

    def test_self_loop_not_allowed(self):
        """Test that self-loops raise error for most edge types"""
        node_id = uuid4()

        with pytest.raises(SelfLoopError, match="Self-loops not allowed"):
            Edge(
                edge_type=EdgeType.PREREQUISITE_OF,
                source_node_id=node_id,
                target_node_id=node_id
            )

    def test_self_loop_allowed_for_relates_to(self):
        """Test that self-loops are allowed for RELATES_TO"""
        node_id = uuid4()

        edge = Edge(
            edge_type=EdgeType.RELATES_TO,
            source_node_id=node_id,
            target_node_id=node_id
        )

        assert edge.source_node_id == edge.target_node_id

    def test_self_loop_allowed_for_similar_to(self):
        """Test that self-loops are allowed for SIMILAR_TO"""
        node_id = uuid4()

        edge = Edge(
            edge_type=EdgeType.SIMILAR_TO,
            source_node_id=node_id,
            target_node_id=node_id
        )

        assert edge.source_node_id == edge.target_node_id

    def test_is_strong_relationship(self):
        """Test identifying strong relationships (weight > 0.7)"""
        edge = Edge(
            EdgeType.PREREQUISITE_OF,
            uuid4(),
            uuid4(),
            weight=Decimal('0.8')
        )

        assert edge.is_strong() is True
        assert edge.is_weak() is False

    def test_is_weak_relationship(self):
        """Test identifying weak relationships (weight < 0.3)"""
        edge = Edge(
            EdgeType.RELATES_TO,
            uuid4(),
            uuid4(),
            weight=Decimal('0.2')
        )

        assert edge.is_weak() is True
        assert edge.is_strong() is False

    def test_medium_strength_relationship(self):
        """Test medium strength relationships"""
        edge = Edge(
            EdgeType.TEACHES,
            uuid4(),
            uuid4(),
            weight=Decimal('0.5')
        )

        assert edge.is_strong() is False
        assert edge.is_weak() is False

    def test_is_mandatory_prerequisite_true(self):
        """Test identifying mandatory prerequisites"""
        edge = Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=uuid4(),
            target_node_id=uuid4(),
            properties={'mandatory': True}
        )

        assert edge.is_mandatory_prerequisite() is True

    def test_is_mandatory_prerequisite_default(self):
        """Test that prerequisites are mandatory by default"""
        edge = Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=uuid4(),
            target_node_id=uuid4()
        )

        assert edge.is_mandatory_prerequisite() is True

    def test_is_mandatory_prerequisite_false(self):
        """Test optional prerequisites"""
        edge = Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=uuid4(),
            target_node_id=uuid4(),
            properties={'mandatory': False}
        )

        assert edge.is_mandatory_prerequisite() is False

    def test_is_mandatory_prerequisite_non_prerequisite(self):
        """Test that non-prerequisite edges return False"""
        edge = Edge(
            edge_type=EdgeType.TEACHES,
            source_node_id=uuid4(),
            target_node_id=uuid4()
        )

        assert edge.is_mandatory_prerequisite() is False

    def test_is_substitutable(self):
        """Test checking if edge is substitutable"""
        edge = Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=uuid4(),
            target_node_id=uuid4(),
            properties={'substitutable': True}
        )

        assert edge.is_substitutable() is True

    def test_get_coverage_depth(self):
        """Test getting coverage depth"""
        edge = Edge(
            edge_type=EdgeType.TEACHES,
            source_node_id=uuid4(),
            target_node_id=uuid4(),
            properties={'coverage_depth': 'deep'}
        )

        assert edge.get_coverage_depth() == 'deep'

    def test_get_coverage_depth_default(self):
        """Test default coverage depth"""
        edge = Edge(
            EdgeType.TEACHES,
            uuid4(),
            uuid4()
        )

        assert edge.get_coverage_depth() == 'medium'

    def test_reverse_edge(self):
        """Test reversing an edge"""
        source = uuid4()
        target = uuid4()

        edge = Edge(
            edge_type=EdgeType.PREREQUISITE_OF,
            source_node_id=source,
            target_node_id=target,
            weight=Decimal('0.9'),
            properties={'test': 'value'}
        )

        reversed_edge = edge.reverse()

        assert reversed_edge.source_node_id == target
        assert reversed_edge.target_node_id == source
        assert reversed_edge.weight == edge.weight
        assert reversed_edge.properties == edge.properties
        assert reversed_edge.edge_type == edge.edge_type

    def test_edge_to_dict(self):
        """Test converting edge to dictionary"""
        source = uuid4()
        target = uuid4()
        edge_id = uuid4()

        edge = Edge(
            id=edge_id,
            edge_type=EdgeType.BUILDS_ON,
            source_node_id=source,
            target_node_id=target,
            weight=Decimal('0.75'),
            properties={'depth': 'shallow'}
        )

        edge_dict = edge.to_dict()

        assert edge_dict['id'] == str(edge_id)
        assert edge_dict['edge_type'] == 'builds_on'
        assert edge_dict['source_node_id'] == str(source)
        assert edge_dict['target_node_id'] == str(target)
        assert edge_dict['weight'] == 0.75
        assert edge_dict['properties'] == {'depth': 'shallow'}

    def test_edge_from_dict(self):
        """Test creating edge from dictionary"""
        data = {
            'id': str(uuid4()),
            'edge_type': 'prerequisite_of',
            'source_node_id': str(uuid4()),
            'target_node_id': str(uuid4()),
            'weight': 0.8,
            'properties': {'mandatory': True},
            'metadata': {},
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }

        edge = Edge.from_dict(data)

        assert edge.edge_type == EdgeType.PREREQUISITE_OF
        assert edge.weight == Decimal('0.8')
        assert edge.properties['mandatory'] is True


class TestEdgeFactoryFunctions:
    """Test suite for edge factory functions"""

    def test_create_prerequisite_edge(self):
        """Test creating prerequisite edge with factory"""
        source = uuid4()
        target = uuid4()

        edge = create_prerequisite_edge(
            source_course_id=source,
            target_course_id=target,
            weight=0.9,
            mandatory=True
        )

        assert edge.edge_type == EdgeType.PREREQUISITE_OF
        assert edge.source_node_id == source
        assert edge.target_node_id == target
        assert edge.weight == Decimal('0.9')
        assert edge.get_property('mandatory') is True

    def test_create_prerequisite_edge_default_mandatory(self):
        """Test that prerequisites are mandatory by default"""
        edge = create_prerequisite_edge(
            source_course_id=uuid4(),
            target_course_id=uuid4()
        )

        assert edge.get_property('mandatory') is True

    def test_create_teaches_edge(self):
        """Test creating teaches edge with factory"""
        source = uuid4()
        target = uuid4()

        edge = create_teaches_edge(
            course_id=source,
            concept_id=target,
            weight=0.85,
            coverage_depth='deep'
        )

        assert edge.edge_type == EdgeType.TEACHES
        assert edge.get_property('coverage_depth') == 'deep'

    def test_create_builds_on_edge(self):
        """Test creating builds_on edge with factory"""
        source = uuid4()
        target = uuid4()

        edge = create_builds_on_edge(
            concept_id=source,
            prerequisite_concept_id=target,
            weight=0.7
        )

        assert edge.edge_type == EdgeType.BUILDS_ON
        assert edge.weight == Decimal('0.7')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
