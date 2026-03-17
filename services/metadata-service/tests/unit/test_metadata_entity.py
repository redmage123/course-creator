"""
Unit tests for Metadata Entity (TDD)

Following Test-Driven Development:
1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor while keeping tests green
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Dict, Any, List

# Tests will import from domain/entities/metadata.py (to be created)
import sys
sys.path.append('/home/bbrelin/course-creator/services/metadata-service')


class TestMetadataEntity:
    """Test suite for Metadata entity"""

    def test_metadata_entity_creation_with_required_fields(self):
        """Test: Should create metadata entity with required fields only"""
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        entity_type = "course"

        # Act
        metadata = Metadata(
            entity_id=entity_id,
            entity_type=entity_type
        )

        # Assert
        assert metadata.entity_id == entity_id
        assert metadata.entity_type == entity_type
        assert metadata.metadata == {}
        assert metadata.title is None
        assert metadata.description is None
        assert metadata.tags == []
        assert metadata.keywords == []
        assert metadata.id is not None  # Auto-generated
        assert isinstance(metadata.created_at, datetime)

    def test_metadata_entity_creation_with_all_fields(self):
        """Test: Should create metadata entity with all fields"""
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        metadata_dict = {
            "educational": {
                "difficulty": "intermediate",
                "topics": ["Python", "FastAPI"]
            },
            "quality": {"rating": 4.5}
        }

        # Act
        metadata = Metadata(
            entity_id=entity_id,
            entity_type="course",
            metadata=metadata_dict,
            title="Advanced Python Programming",
            description="Learn advanced Python concepts",
            tags=["python", "advanced", "programming"],
            keywords=["async", "fastapi", "oop"]
        )

        # Assert
        assert metadata.title == "Advanced Python Programming"
        assert metadata.description == "Learn advanced Python concepts"
        assert "python" in metadata.tags
        assert "async" in metadata.keywords
        assert metadata.metadata["educational"]["difficulty"] == "intermediate"

    def test_metadata_entity_type_validation(self):
        """Test: Should validate entity_type against allowed values"""
        from domain.entities.metadata import Metadata, InvalidEntityTypeError

        # Arrange
        valid_types = ['course', 'content', 'user', 'lab', 'project', 'track']
        invalid_type = 'invalid_type'

        # Act & Assert - valid types should work
        for entity_type in valid_types:
            metadata = Metadata(entity_id=uuid4(), entity_type=entity_type)
            assert metadata.entity_type == entity_type

        # Act & Assert - invalid type should raise error
        with pytest.raises(InvalidEntityTypeError) as exc_info:
            Metadata(entity_id=uuid4(), entity_type=invalid_type)

        assert "invalid_type" in str(exc_info.value)

    def test_metadata_tags_normalization(self):
        """Test: Should normalize tags to lowercase and strip whitespace"""
        from domain.entities.metadata import Metadata

        # Arrange & Act
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            tags=["  Python  ", "FASTAPI", "Web-Development"]
        )

        # Assert
        assert metadata.tags == ["python", "fastapi", "web-development"]

    def test_metadata_keywords_normalization(self):
        """Test: Should normalize keywords to lowercase"""
        from domain.entities.metadata import Metadata

        # Arrange & Act
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            keywords=["Async", "AWAIT", "Coroutines"]
        )

        # Assert
        assert metadata.keywords == ["async", "await", "coroutines"]

    def test_metadata_to_dict_method(self):
        """Test: Should convert metadata entity to dictionary"""
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        metadata = Metadata(
            entity_id=entity_id,
            entity_type="course",
            title="Test Course",
            metadata={"key": "value"}
        )

        # Act
        result = metadata.to_dict()

        # Assert
        assert result["entity_id"] == str(entity_id)
        assert result["entity_type"] == "course"
        assert result["title"] == "Test Course"
        assert result["metadata"] == {"key": "value"}
        assert "created_at" in result

    def test_metadata_from_dict_method(self):
        """Test: Should create metadata entity from dictionary"""
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        data = {
            "entity_id": str(entity_id),
            "entity_type": "course",
            "title": "Test Course",
            "metadata": {"key": "value"},
            "tags": ["python"],
            "keywords": ["async"]
        }

        # Act
        metadata = Metadata.from_dict(data)

        # Assert
        assert metadata.entity_id == entity_id
        assert metadata.entity_type == "course"
        assert metadata.title == "Test Course"
        assert metadata.tags == ["python"]

    def test_metadata_update_method(self):
        """Test: Should update metadata fields"""
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            title="Original Title"
        )
        original_created_at = metadata.created_at

        # Act
        metadata.update(
            title="Updated Title",
            tags=["new-tag"]
        )

        # Assert
        assert metadata.title == "Updated Title"
        assert "new-tag" in metadata.tags
        assert metadata.updated_at > original_created_at

    def test_metadata_merge_metadata_dict(self):
        """Test: Should merge metadata dictionaries"""
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            metadata={"existing": "value", "nested": {"key1": "val1"}}
        )

        # Act
        metadata.merge_metadata({
            "new": "field",
            "nested": {"key2": "val2"}
        })

        # Assert
        assert metadata.metadata["existing"] == "value"
        assert metadata.metadata["new"] == "field"
        assert metadata.metadata["nested"]["key1"] == "val1"
        assert metadata.metadata["nested"]["key2"] == "val2"

    def test_metadata_get_search_text(self):
        """Test: Should generate searchable text from metadata"""
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            title="Python Programming",
            description="Learn Python basics",
            tags=["python", "programming"],
            keywords=["beginner", "tutorial"]
        )

        # Act
        search_text = metadata.get_search_text()

        # Assert
        assert "Python Programming" in search_text
        assert "Learn Python basics" in search_text
        assert "python" in search_text.lower()
        assert "beginner" in search_text.lower()

    def test_metadata_equality(self):
        """Test: Two metadata entities with same entity_id and type should be equal"""
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        metadata1 = Metadata(entity_id=entity_id, entity_type="course", title="Test 1")
        metadata2 = Metadata(entity_id=entity_id, entity_type="course", title="Test 2")
        metadata3 = Metadata(entity_id=uuid4(), entity_type="course", title="Test 1")

        # Act & Assert
        assert metadata1 == metadata2  # Same entity_id and type
        assert metadata1 != metadata3  # Different entity_id

    def test_metadata_string_representation(self):
        """Test: Should have readable string representation"""
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            title="Test Course"
        )

        # Act
        str_repr = str(metadata)

        # Assert
        assert "course" in str_repr
        assert "Test Course" in str_repr


class TestMetadataValidation:
    """Test suite for Metadata validation"""

    def test_empty_entity_id_raises_error(self):
        """Test: Should raise error for empty entity_id"""
        from domain.entities.metadata import Metadata, MetadataValidationError

        # Act & Assert
        with pytest.raises(MetadataValidationError):
            Metadata(entity_id=None, entity_type="course")

    def test_empty_entity_type_raises_error(self):
        """Test: Should raise error for empty entity_type"""
        from domain.entities.metadata import Metadata, MetadataValidationError

        # Act & Assert
        with pytest.raises(MetadataValidationError):
            Metadata(entity_id=uuid4(), entity_type="")

    def test_title_max_length_validation(self):
        """Test: Should enforce title maximum length"""
        from domain.entities.metadata import Metadata, MetadataValidationError

        # Arrange
        long_title = "a" * 1001  # Assuming 1000 char limit

        # Act & Assert
        with pytest.raises(MetadataValidationError) as exc_info:
            Metadata(entity_id=uuid4(), entity_type="course", title=long_title)

        assert "title" in str(exc_info.value).lower()

    def test_description_max_length_validation(self):
        """Test: Should enforce description maximum length"""
        from domain.entities.metadata import Metadata, MetadataValidationError

        # Arrange
        long_description = "a" * 10001  # Assuming 10000 char limit

        # Act & Assert
        with pytest.raises(MetadataValidationError) as exc_info:
            Metadata(
                entity_id=uuid4(),
                entity_type="course",
                description=long_description
            )

        assert "description" in str(exc_info.value).lower()

    def test_metadata_dict_must_be_json_serializable(self):
        """Test: Should validate metadata dict is JSON serializable"""
        from domain.entities.metadata import Metadata, MetadataValidationError

        # Arrange
        non_serializable_metadata = {
            "key": lambda x: x  # Functions not JSON serializable
        }

        # Act & Assert
        with pytest.raises(MetadataValidationError):
            Metadata(
                entity_id=uuid4(),
                entity_type="course",
                metadata=non_serializable_metadata
            )


class TestMetadataQueries:
    """Test suite for Metadata query helpers"""

    def test_extract_topics_from_metadata(self):
        """Test: Should extract topics from metadata"""
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            metadata={
                "educational": {
                    "topics": ["Python", "FastAPI", "Async Programming"]
                }
            }
        )

        # Act
        topics = metadata.get_topics()

        # Assert
        assert "Python" in topics
        assert "FastAPI" in topics
        assert len(topics) == 3

    def test_extract_difficulty_from_metadata(self):
        """Test: Should extract difficulty level from metadata"""
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            metadata={
                "educational": {"difficulty": "intermediate"}
            }
        )

        # Act
        difficulty = metadata.get_difficulty()

        # Assert
        assert difficulty == "intermediate"

    def test_get_metadata_path(self):
        """Test: Should get nested metadata value by path"""
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            metadata={
                "educational": {
                    "quality": {"rating": 4.5}
                }
            }
        )

        # Act
        rating = metadata.get_metadata_value("educational.quality.rating")

        # Assert
        assert rating == 4.5

    def test_set_metadata_path(self):
        """Test: Should set nested metadata value by path"""
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type="course",
            metadata={}
        )

        # Act
        metadata.set_metadata_value("educational.quality.rating", 4.7)

        # Assert
        assert metadata.metadata["educational"]["quality"]["rating"] == 4.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
