"""
Unit Tests for Node Entity

Tests the Node domain entity including validation,
factory functions, and business logic.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/knowledge-graph-service'))

from knowledge_graph_service.domain.entities.node import (
    Node,
    NodeType,
    create_course_node,
    create_concept_node,
    create_skill_node
)


class TestNodeEntity:
    """Test suite for Node entity"""

    def test_create_node_with_valid_data(self):
        """Test creating a node with valid data"""
        entity_id = uuid4()
        node = Node(
            node_type=NodeType.COURSE,
            entity_id=entity_id,
            label="Introduction to Python"
        )

        assert node.node_type == NodeType.COURSE
        assert node.entity_id == entity_id
        assert node.label == "Introduction to Python"
        assert isinstance(node.id, UUID)
        assert node.properties == {}
        assert node.metadata == {}

    def test_create_node_with_string_node_type(self):
        """Test creating node with string node type (auto-conversion)"""
        node = Node(
            node_type='course',
            entity_id=uuid4(),
            label="Test Course"
        )

        assert node.node_type == NodeType.COURSE

    def test_create_node_with_properties(self):
        """Test creating node with properties"""
        node = Node(
            node_type=NodeType.COURSE,
            entity_id=uuid4(),
            label="Advanced Python",
            properties={
                'difficulty': 'advanced',
                'duration': 60,
                'category': 'programming'
            }
        )

        assert node.properties['difficulty'] == 'advanced'
        assert node.properties['duration'] == 60
        assert node.get_property('category') == 'programming'

    def test_node_validation_empty_label(self):
        """Test that empty label raises ValueError"""
        with pytest.raises(ValueError, match="label cannot be empty"):
            Node(
                node_type=NodeType.COURSE,
                entity_id=uuid4(),
                label=""
            )

    def test_node_validation_whitespace_label(self):
        """Test that whitespace-only label raises ValueError"""
        with pytest.raises(ValueError, match="label cannot be empty"):
            Node(
                node_type=NodeType.COURSE,
                entity_id=uuid4(),
                label="   "
            )

    def test_node_validation_invalid_type(self):
        """Test that invalid node type raises ValueError"""
        with pytest.raises(ValueError):
            Node(
                node_type='invalid_type',
                entity_id=uuid4(),
                label="Test"
            )

    def test_set_and_get_property(self):
        """Test setting and getting properties"""
        node = Node(
            node_type=NodeType.CONCEPT,
            entity_id=uuid4(),
            label="Object-Oriented Programming"
        )

        node.set_property('complexity', 'high')
        assert node.get_property('complexity') == 'high'
        assert node.get_property('nonexistent', 'default') == 'default'

    def test_node_to_dict(self):
        """Test converting node to dictionary"""
        entity_id = uuid4()
        node_id = uuid4()
        created_by = uuid4()

        node = Node(
            id=node_id,
            node_type=NodeType.SKILL,
            entity_id=entity_id,
            label="Machine Learning",
            properties={'level': 'advanced'},
            created_by=created_by
        )

        node_dict = node.to_dict()

        assert node_dict['id'] == str(node_id)
        assert node_dict['node_type'] == 'skill'
        assert node_dict['entity_id'] == str(entity_id)
        assert node_dict['label'] == "Machine Learning"
        assert node_dict['properties'] == {'level': 'advanced'}
        assert node_dict['created_by'] == str(created_by)

    def test_node_from_dict(self):
        """Test creating node from dictionary"""
        node_id = str(uuid4())
        entity_id = str(uuid4())

        data = {
            'id': node_id,
            'node_type': 'course',
            'entity_id': entity_id,
            'label': 'Data Science 101',
            'properties': {'difficulty': 'beginner'},
            'metadata': {'source': 'import'},
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }

        node = Node.from_dict(data)

        assert str(node.id) == node_id
        assert node.node_type == NodeType.COURSE
        assert str(node.entity_id) == entity_id
        assert node.label == 'Data Science 101'
        assert node.properties['difficulty'] == 'beginner'

    def test_node_equality(self):
        """Test node equality based on type and entity_id"""
        entity_id = uuid4()

        node1 = Node(
            node_type=NodeType.COURSE,
            entity_id=entity_id,
            label="Course 1"
        )

        node2 = Node(
            node_type=NodeType.COURSE,
            entity_id=entity_id,
            label="Course 1 Updated"  # Different label
        )

        node3 = Node(
            node_type=NodeType.CONCEPT,
            entity_id=entity_id,
            label="Course 1"
        )

        assert node1 == node2  # Same type and entity_id
        assert node1 != node3  # Different type

    def test_node_hash(self):
        """Test that nodes can be used in sets/dicts"""
        entity_id = uuid4()

        node1 = Node(NodeType.COURSE, entity_id, "Test 1")
        node2 = Node(NodeType.COURSE, entity_id, "Test 2")

        node_set = {node1, node2}
        assert len(node_set) == 1  # Same entity, so deduplicated


class TestNodeFactoryFunctions:
    """Test suite for node factory functions"""

    def test_create_course_node(self):
        """Test creating a course node with factory"""
        entity_id = uuid4()
        node = create_course_node(
            entity_id=entity_id,
            label="Python Fundamentals",
            difficulty="beginner",
            duration=40,
            category="programming"
        )

        assert node.node_type == NodeType.COURSE
        assert node.entity_id == entity_id
        assert node.label == "Python Fundamentals"
        assert node.get_property('difficulty') == 'beginner'
        assert node.get_property('duration') == 40
        assert node.get_property('category') == 'programming'

    def test_create_concept_node(self):
        """Test creating a concept node with factory"""
        entity_id = uuid4()
        node = create_concept_node(
            entity_id=entity_id,
            label="Recursion",
            complexity="medium",
            category="algorithms"
        )

        assert node.node_type == NodeType.CONCEPT
        assert node.get_property('complexity') == 'medium'
        assert node.get_property('category') == 'algorithms'

    def test_create_skill_node(self):
        """Test creating a skill node with factory"""
        entity_id = uuid4()
        node = create_skill_node(
            entity_id=entity_id,
            label="Web Development",
            level="intermediate",
            category="technology"
        )

        assert node.node_type == NodeType.SKILL
        assert node.get_property('level') == 'intermediate'
        assert node.get_property('category') == 'technology'


class TestNodeProperties:
    """Test suite for node property helpers"""

    def test_get_difficulty(self):
        """Test getting difficulty property"""
        node = Node(
            NodeType.COURSE,
            uuid4(),
            "Test Course",
            properties={'difficulty': 'advanced'}
        )

        assert node.get_difficulty() == 'advanced'

    def test_get_difficulty_default(self):
        """Test default difficulty when not set"""
        node = Node(NodeType.COURSE, uuid4(), "Test")
        assert node.get_difficulty() is None

    def test_get_complexity(self):
        """Test getting complexity property"""
        node = Node(
            NodeType.CONCEPT,
            uuid4(),
            "Test",
            properties={'complexity': 'high'}
        )

        assert node.get_complexity() == 'high'

    def test_get_category(self):
        """Test getting category property"""
        node = Node(
            NodeType.COURSE,
            uuid4(),
            "Test",
            properties={'category': 'data-science'}
        )

        assert node.get_category() == 'data-science'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
