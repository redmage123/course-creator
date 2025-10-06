"""
Unit tests for MetadataService (TDD - RED Phase)

Following Test-Driven Development:
1. Write failing tests first (RED)
2. Implement minimal code to pass tests (GREEN)
3. Refactor while keeping tests green (REFACTOR)

BUSINESS REQUIREMENT:
Service layer orchestrates metadata operations, enforces business rules,
handles validation, and coordinates between DAO and domain entities.
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch

# Tests will import from application/services/metadata_service.py (to be created)
import sys
sys.path.append('/home/bbrelin/course-creator/services/metadata-service')


@pytest.fixture
def mock_metadata_dao():
    """Create mock MetadataDAO for testing service layer in isolation"""
    dao = Mock()
    # Make async methods return AsyncMock
    dao.create = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.get_by_entity = AsyncMock()
    dao.list_by_entity_type = AsyncMock()
    dao.update = AsyncMock()
    dao.delete = AsyncMock()
    dao.search = AsyncMock()
    dao.get_by_tags = AsyncMock()
    return dao


@pytest.fixture
def metadata_service(mock_metadata_dao):
    """Create MetadataService instance with mocked DAO"""
    from application.services.metadata_service import MetadataService
    return MetadataService(mock_metadata_dao)


@pytest.mark.asyncio
class TestMetadataServiceCreate:
    """Test suite for MetadataService create operations"""

    async def test_create_metadata_success(self, metadata_service, mock_metadata_dao):
        """
        Test: Should create metadata through service layer

        BUSINESS LOGIC:
        - Validates metadata entity
        - Delegates to DAO
        - Returns created metadata
        """
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        metadata = Metadata(
            entity_id=entity_id,
            entity_type='course',
            title='Python Programming'
        )
        mock_metadata_dao.create.return_value = metadata

        # Act
        result = await metadata_service.create_metadata(metadata)

        # Assert
        assert result == metadata
        mock_metadata_dao.create.assert_called_once_with(metadata, connection=None)

    async def test_create_metadata_with_auto_tag_extraction(self, metadata_service, mock_metadata_dao):
        """
        Test: Should automatically extract tags from title and description

        BUSINESS RULE:
        Service should enhance metadata by extracting common keywords as tags
        """
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        metadata = Metadata(
            entity_id=entity_id,
            entity_type='course',
            title='Learn Python Programming and Web Development',
            description='Master Python, Django, and REST APIs'
        )

        async def create_side_effect(meta, connection=None):
            # Tags should be auto-extracted before DAO call
            assert len(meta.tags) > 0
            assert 'python' in meta.tags
            return meta

        mock_metadata_dao.create.side_effect = create_side_effect

        # Act
        result = await metadata_service.create_metadata(metadata, auto_extract_tags=True)

        # Assert
        mock_metadata_dao.create.assert_called_once()

    async def test_create_metadata_duplicate_returns_error(self, metadata_service, mock_metadata_dao):
        """
        Test: Should handle duplicate metadata gracefully

        ERROR HANDLING:
        Return meaningful error when duplicate exists
        """
        from domain.entities.metadata import Metadata
        from data_access.metadata_dao import MetadataAlreadyExistsError
        from application.services.metadata_service import MetadataServiceError

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='course')
        mock_metadata_dao.create.side_effect = MetadataAlreadyExistsError("Duplicate")

        # Act & Assert
        with pytest.raises(MetadataServiceError) as exc_info:
            await metadata_service.create_metadata(metadata)

        assert "already exists" in str(exc_info.value).lower()

    async def test_create_metadata_validates_required_fields(self, metadata_service, mock_metadata_dao):
        """
        Test: Should validate metadata before creating

        VALIDATION RULE:
        Service layer should validate business rules before delegating to DAO
        """
        from domain.entities.metadata import Metadata
        from application.services.metadata_service import MetadataValidationError

        # Arrange - metadata without title for content type
        metadata = Metadata(entity_id=uuid4(), entity_type='content')

        # Act & Assert
        with pytest.raises(MetadataValidationError) as exc_info:
            await metadata_service.create_metadata(metadata, require_title=True)

        assert "title" in str(exc_info.value).lower()


@pytest.mark.asyncio
class TestMetadataServiceRead:
    """Test suite for MetadataService read operations"""

    async def test_get_metadata_by_id(self, metadata_service, mock_metadata_dao):
        """
        Test: Should retrieve metadata by ID

        BUSINESS LOGIC:
        Simple delegation to DAO with result validation
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata_id = uuid4()
        expected = Metadata(entity_id=uuid4(), entity_type='course', title='Test')
        expected.id = metadata_id
        mock_metadata_dao.get_by_id.return_value = expected

        # Act
        result = await metadata_service.get_metadata_by_id(metadata_id)

        # Assert
        assert result == expected
        mock_metadata_dao.get_by_id.assert_called_once_with(metadata_id)

    async def test_get_metadata_by_id_not_found_returns_none(self, metadata_service, mock_metadata_dao):
        """
        Test: Should return None when metadata not found

        BUSINESS LOGIC:
        Not finding metadata is not an error - return None
        """
        # Arrange
        mock_metadata_dao.get_by_id.return_value = None

        # Act
        result = await metadata_service.get_metadata_by_id(uuid4())

        # Assert
        assert result is None

    async def test_get_metadata_by_entity(self, metadata_service, mock_metadata_dao):
        """
        Test: Should retrieve metadata by entity_id and entity_type

        PRIMARY USE CASE:
        Most common query - get metadata for specific entity
        """
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        expected = Metadata(entity_id=entity_id, entity_type='course')
        mock_metadata_dao.get_by_entity.return_value = expected

        # Act
        result = await metadata_service.get_metadata_by_entity(entity_id, 'course')

        # Assert
        assert result == expected
        mock_metadata_dao.get_by_entity.assert_called_once_with(entity_id, 'course')

    async def test_get_or_create_metadata(self, metadata_service, mock_metadata_dao):
        """
        Test: Should get existing or create new metadata

        BUSINESS LOGIC:
        Common pattern - ensure metadata exists for entity
        """
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        mock_metadata_dao.get_by_entity.return_value = None  # Not found

        new_metadata = Metadata(entity_id=entity_id, entity_type='course')
        mock_metadata_dao.create.return_value = new_metadata

        # Act
        result = await metadata_service.get_or_create_metadata(entity_id, 'course')

        # Assert
        assert result.entity_id == entity_id
        mock_metadata_dao.get_by_entity.assert_called_once()
        mock_metadata_dao.create.assert_called_once()

    async def test_list_metadata_by_type_with_enrichment(self, metadata_service, mock_metadata_dao):
        """
        Test: Should list metadata with optional enrichment

        ENRICHMENT:
        Service can add computed fields, related data, etc.
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata_list = [
            Metadata(entity_id=uuid4(), entity_type='course', title='Course 1'),
            Metadata(entity_id=uuid4(), entity_type='course', title='Course 2')
        ]
        mock_metadata_dao.list_by_entity_type.return_value = metadata_list

        # Act
        result = await metadata_service.list_metadata_by_type('course', limit=10)

        # Assert
        assert len(result) == 2
        mock_metadata_dao.list_by_entity_type.assert_called_once_with('course', limit=10, offset=0)


@pytest.mark.asyncio
class TestMetadataServiceUpdate:
    """Test suite for MetadataService update operations"""

    async def test_update_metadata_success(self, metadata_service, mock_metadata_dao):
        """
        Test: Should update metadata through service layer

        BUSINESS LOGIC:
        - Validates updates
        - Delegates to DAO
        - Returns updated metadata
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='course', title='Original')
        metadata.id = uuid4()

        updated = Metadata(entity_id=metadata.entity_id, entity_type='course', title='Updated')
        updated.id = metadata.id

        mock_metadata_dao.update.return_value = updated

        # Act
        metadata.update(title='Updated')
        result = await metadata_service.update_metadata(metadata)

        # Assert
        assert result.title == 'Updated'
        mock_metadata_dao.update.assert_called_once()

    async def test_update_metadata_with_validation(self, metadata_service, mock_metadata_dao):
        """
        Test: Should validate business rules before update

        VALIDATION:
        Ensure update doesn't violate business constraints
        """
        from domain.entities.metadata import Metadata
        from application.services.metadata_service import MetadataValidationError

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='course')
        metadata.id = uuid4()

        # Act & Assert - try to update with invalid data
        metadata.update(title='')  # Empty title
        with pytest.raises(MetadataValidationError):
            await metadata_service.update_metadata(metadata, validate_title=True)

    async def test_partial_update_metadata(self, metadata_service, mock_metadata_dao):
        """
        Test: Should support partial updates

        BUSINESS LOGIC:
        Update only specified fields, preserve others
        """
        from domain.entities.metadata import Metadata

        # Arrange
        existing = Metadata(
            entity_id=uuid4(),
            entity_type='course',
            title='Original Title',
            description='Original Description'
        )
        existing.id = uuid4()

        mock_metadata_dao.get_by_id.return_value = existing
        mock_metadata_dao.update.return_value = existing

        # Act
        result = await metadata_service.partial_update_metadata(
            existing.id,
            {'title': 'New Title'}
        )

        # Assert
        assert result.title == 'New Title'
        assert result.description == 'Original Description'


@pytest.mark.asyncio
class TestMetadataServiceDelete:
    """Test suite for MetadataService delete operations"""

    async def test_delete_metadata_success(self, metadata_service, mock_metadata_dao):
        """
        Test: Should delete metadata by ID

        BUSINESS LOGIC:
        Simple delegation to DAO
        """
        # Arrange
        metadata_id = uuid4()
        mock_metadata_dao.delete.return_value = True

        # Act
        result = await metadata_service.delete_metadata(metadata_id)

        # Assert
        assert result is True
        mock_metadata_dao.delete.assert_called_once_with(metadata_id)

    async def test_delete_metadata_not_found(self, metadata_service, mock_metadata_dao):
        """
        Test: Should return False when metadata not found

        IDEMPOTENCY:
        Deleting non-existent metadata returns False
        """
        # Arrange
        mock_metadata_dao.delete.return_value = False

        # Act
        result = await metadata_service.delete_metadata(uuid4())

        # Assert
        assert result is False


@pytest.mark.asyncio
class TestMetadataServiceSearch:
    """Test suite for MetadataService search operations"""

    async def test_search_metadata_full_text(self, metadata_service, mock_metadata_dao):
        """
        Test: Should perform full-text search

        BUSINESS LOGIC:
        Delegates to DAO, may enhance results with scoring
        """
        from domain.entities.metadata import Metadata

        # Arrange
        results = [
            Metadata(entity_id=uuid4(), entity_type='course', title='Python Programming'),
            Metadata(entity_id=uuid4(), entity_type='course', title='Python Basics')
        ]
        mock_metadata_dao.search.return_value = results

        # Act
        result = await metadata_service.search_metadata('Python', entity_types=['course'])

        # Assert
        assert len(result) == 2
        mock_metadata_dao.search.assert_called_once_with('Python', entity_types=['course'], limit=20)

    async def test_search_metadata_with_filters(self, metadata_service, mock_metadata_dao):
        """
        Test: Should support complex search with filters

        ADVANCED SEARCH:
        Combine full-text search with tag filters
        """
        from domain.entities.metadata import Metadata

        # Arrange
        results = [Metadata(entity_id=uuid4(), entity_type='course', tags=['python', 'advanced'])]
        mock_metadata_dao.search.return_value = results

        # Act
        result = await metadata_service.search_metadata(
            'programming',
            entity_types=['course'],
            required_tags=['python'],
            limit=10
        )

        # Assert
        assert len(result) == 1
        assert 'python' in result[0].tags

    async def test_search_metadata_with_ranking(self, metadata_service, mock_metadata_dao):
        """
        Test: Should return ranked search results

        RANKING:
        Service may apply additional ranking logic beyond database
        """
        from domain.entities.metadata import Metadata

        # Arrange
        results = [
            Metadata(entity_id=uuid4(), entity_type='course', title='Python Advanced'),
            Metadata(entity_id=uuid4(), entity_type='course', title='Python Basics')
        ]
        mock_metadata_dao.search.return_value = results

        # Act
        result = await metadata_service.search_metadata('Python', rank_by_relevance=True)

        # Assert
        assert len(result) == 2
        # Results should be ranked

    async def test_get_by_tags(self, metadata_service, mock_metadata_dao):
        """
        Test: Should retrieve metadata by tags

        TAG SEARCH:
        Find all metadata with specific tags
        """
        from domain.entities.metadata import Metadata

        # Arrange
        results = [Metadata(entity_id=uuid4(), entity_type='course', tags=['python', 'beginner'])]
        mock_metadata_dao.get_by_tags.return_value = results

        # Act
        result = await metadata_service.get_by_tags(['python', 'beginner'])

        # Assert
        assert len(result) == 1
        mock_metadata_dao.get_by_tags.assert_called_once_with(['python', 'beginner'], entity_type=None, limit=100)


@pytest.mark.asyncio
class TestMetadataServiceBulkOperations:
    """Test suite for MetadataService bulk operations"""

    async def test_bulk_create_metadata(self, metadata_service, mock_metadata_dao):
        """
        Test: Should create multiple metadata records

        BULK OPERATION:
        Efficient batch creation with validation
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata_list = [
            Metadata(entity_id=uuid4(), entity_type='course', title=f'Course {i}')
            for i in range(3)
        ]
        mock_metadata_dao.create.side_effect = lambda m, **kwargs: m

        # Act
        result = await metadata_service.bulk_create_metadata(metadata_list)

        # Assert
        assert len(result) == 3
        assert mock_metadata_dao.create.call_count == 3

    async def test_bulk_create_stops_on_error(self, metadata_service, mock_metadata_dao):
        """
        Test: Should handle errors in bulk operations

        ERROR HANDLING:
        Stop on first error or collect all errors
        """
        from domain.entities.metadata import Metadata
        from data_access.metadata_dao import MetadataAlreadyExistsError
        from application.services.metadata_service import BulkOperationError

        # Arrange
        metadata_list = [
            Metadata(entity_id=uuid4(), entity_type='course', title='Course 1'),
            Metadata(entity_id=uuid4(), entity_type='course', title='Course 2')
        ]
        mock_metadata_dao.create.side_effect = [
            metadata_list[0],
            MetadataAlreadyExistsError("Duplicate")
        ]

        # Act & Assert
        with pytest.raises(BulkOperationError) as exc_info:
            await metadata_service.bulk_create_metadata(metadata_list, stop_on_error=True)

        assert "1 of 2" in str(exc_info.value)


@pytest.mark.asyncio
class TestMetadataServiceEnrichment:
    """Test suite for MetadataService enrichment operations"""

    async def test_enrich_metadata_with_ai(self, metadata_service, mock_metadata_dao):
        """
        Test: Should enrich metadata using tag extraction

        ENRICHMENT:
        Extract topics, keywords, difficulty from content
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type='course',
            title='Advanced Python Programming',
            description='Deep dive into Python internals, async, and metaprogramming'
        )
        metadata.id = uuid4()  # Set ID so enrich will update
        mock_metadata_dao.update.return_value = metadata

        # Act
        result = await metadata_service.enrich_metadata(metadata)

        # Assert
        # Should have extracted tags from title/description
        assert result is not None
        assert len(result.tags) > 0  # Tags should be auto-extracted
        assert 'python' in result.tags or 'async' in result.tags

    async def test_auto_tag_extraction(self, metadata_service, mock_metadata_dao):
        """
        Test: Should automatically extract tags from text

        AUTO-TAGGING:
        Use NLP to extract meaningful tags
        """
        from domain.entities.metadata import Metadata

        # Arrange
        text = "Learn Python programming with Django and REST APIs"

        # Act
        tags = await metadata_service.extract_tags(text)

        # Assert
        assert len(tags) > 0
        assert any('python' in tag.lower() for tag in tags)


@pytest.mark.asyncio
class TestMetadataServiceValidation:
    """Test suite for MetadataService validation logic"""

    async def test_validate_metadata_schema(self, metadata_service):
        """
        Test: Should validate metadata schema

        VALIDATION:
        Ensure metadata dict conforms to expected schema
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type='course',
            metadata={
                'educational': {
                    'difficulty': 'intermediate',
                    'topics': ['Python']
                }
            }
        )

        # Act
        is_valid = await metadata_service.validate_metadata_schema(metadata)

        # Assert
        assert is_valid is True

    async def test_validate_metadata_schema_invalid(self, metadata_service):
        """
        Test: Should detect invalid metadata schema

        VALIDATION:
        Reject metadata that doesn't match schema
        """
        from domain.entities.metadata import Metadata
        from application.services.metadata_service import MetadataValidationError

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type='course',
            metadata={
                'educational': {
                    'difficulty': 'invalid_level'  # Should be beginner/intermediate/advanced
                }
            }
        )

        # Act & Assert
        with pytest.raises(MetadataValidationError):
            await metadata_service.validate_metadata_schema(metadata, strict=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
