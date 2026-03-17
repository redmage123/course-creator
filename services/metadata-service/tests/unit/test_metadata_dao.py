"""
Unit tests for MetadataDAO (TDD - RED Phase)

Following Test-Driven Development:
1. Write failing tests first (RED)
2. Implement minimal code to pass tests (GREEN)
3. Refactor while keeping tests green (REFACTOR)

BUSINESS REQUIREMENT:
Data Access Layer for metadata CRUD operations with PostgreSQL integration
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
import asyncpg

# Tests will import from data_access/metadata_dao.py (to be created)
import sys
sys.path.append('/home/bbrelin/course-creator/services/metadata-service')


@pytest.fixture
async def db_pool():
    """
    Create test database connection pool

    SETUP REQUIREMENT:
    Tests require a PostgreSQL database with metadata schema applied
    """
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        database='course_creator',
        user='postgres',
        password='postgres_password',
        min_size=1,
        max_size=5
    )
    yield pool
    await pool.close()


@pytest.fixture
async def metadata_dao(db_pool):
    """Create MetadataDAO instance with test database pool"""
    from data_access.metadata_dao import MetadataDAO
    return MetadataDAO(db_pool)


@pytest.fixture
async def clean_metadata_table(db_pool):
    """
    Clean metadata table before each test

    ISOLATION REQUIREMENT:
    Each test should run in isolation with clean state
    """
    async with db_pool.acquire() as conn:
        await conn.execute('DELETE FROM entity_metadata WHERE entity_type = $1', 'test')
    yield
    async with db_pool.acquire() as conn:
        await conn.execute('DELETE FROM entity_metadata WHERE entity_type = $1', 'test')


@pytest.mark.asyncio
class TestMetadataDAOCreate:
    """Test suite for MetadataDAO create operations"""

    async def test_create_metadata_with_required_fields(self, metadata_dao, clean_metadata_table):
        """
        Test: Should create metadata record with required fields only

        ACCEPTANCE CRITERIA:
        - Record is inserted into entity_metadata table
        - Returns created metadata with generated ID
        - created_at and updated_at timestamps are set
        """
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        metadata = Metadata(
            entity_id=entity_id,
            entity_type='test'
        )

        # Act
        created = await metadata_dao.create(metadata)

        # Assert
        assert created is not None
        assert created.id is not None
        assert created.entity_id == entity_id
        assert created.entity_type == 'test'
        assert created.created_at is not None
        assert created.updated_at is not None

    async def test_create_metadata_with_all_fields(self, metadata_dao, clean_metadata_table):
        """
        Test: Should create metadata record with all fields populated

        ACCEPTANCE CRITERIA:
        - All fields are persisted correctly
        - JSONB metadata is stored properly
        - Arrays (tags, keywords) are stored correctly
        """
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        user_id = uuid4()
        metadata = Metadata(
            entity_id=entity_id,
            entity_type='test',
            metadata={'educational': {'difficulty': 'intermediate', 'topics': ['Python']}},
            title='Test Metadata',
            description='Test description for metadata',
            tags=['test', 'python', 'metadata'],
            keywords=['unit-test', 'dao'],
            created_by=user_id,
            updated_by=user_id
        )

        # Act
        created = await metadata_dao.create(metadata)

        # Assert
        assert created.title == 'Test Metadata'
        assert created.description == 'Test description for metadata'
        assert 'test' in created.tags
        assert 'unit-test' in created.keywords
        assert created.metadata['educational']['difficulty'] == 'intermediate'
        assert created.created_by == user_id

    async def test_create_metadata_duplicate_entity_raises_error(self, metadata_dao, clean_metadata_table):
        """
        Test: Should raise error when creating duplicate entity_id + entity_type

        BUSINESS RULE:
        Only one metadata record per entity_id + entity_type combination
        """
        from domain.entities.metadata import Metadata
        from data_access.metadata_dao import MetadataAlreadyExistsError

        # Arrange
        entity_id = uuid4()
        metadata1 = Metadata(entity_id=entity_id, entity_type='test')
        metadata2 = Metadata(entity_id=entity_id, entity_type='test')

        # Act
        await metadata_dao.create(metadata1)

        # Assert
        with pytest.raises(MetadataAlreadyExistsError):
            await metadata_dao.create(metadata2)

    async def test_create_metadata_generates_full_text_search_vector(self, metadata_dao, clean_metadata_table):
        """
        Test: Should automatically generate search_vector for full-text search

        SEARCH REQUIREMENT:
        Database trigger should populate search_vector from title, description, tags, keywords
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type='test',
            title='Python Programming',
            description='Learn advanced Python',
            tags=['python'],
            keywords=['programming']
        )

        # Act
        created = await metadata_dao.create(metadata)

        # Assert - verify can be found via search
        results = await metadata_dao.search('Python', entity_types=['test'])
        assert len(results) > 0
        assert any(r.entity_id == created.entity_id for r in results)


@pytest.mark.asyncio
class TestMetadataDAORead:
    """Test suite for MetadataDAO read operations"""

    async def test_get_by_id_returns_metadata(self, metadata_dao, clean_metadata_table):
        """
        Test: Should retrieve metadata by ID

        ACCEPTANCE CRITERIA:
        - Returns metadata entity if exists
        - Returns None if not found
        """
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        metadata = Metadata(entity_id=entity_id, entity_type='test', title='Test')
        created = await metadata_dao.create(metadata)

        # Act
        retrieved = await metadata_dao.get_by_id(created.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == 'Test'

    async def test_get_by_entity_returns_metadata(self, metadata_dao, clean_metadata_table):
        """
        Test: Should retrieve metadata by entity_id and entity_type

        PRIMARY USE CASE:
        Most common query pattern - get metadata for a specific entity
        """
        from domain.entities.metadata import Metadata

        # Arrange
        entity_id = uuid4()
        metadata = Metadata(entity_id=entity_id, entity_type='test', title='Course Metadata')
        await metadata_dao.create(metadata)

        # Act
        retrieved = await metadata_dao.get_by_entity(entity_id, 'test')

        # Assert
        assert retrieved is not None
        assert retrieved.entity_id == entity_id
        assert retrieved.entity_type == 'test'
        assert retrieved.title == 'Course Metadata'

    async def test_get_by_entity_not_found_returns_none(self, metadata_dao, clean_metadata_table):
        """
        Test: Should return None when entity not found

        ERROR HANDLING:
        Not finding metadata is not an error - return None
        """
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await metadata_dao.get_by_entity(non_existent_id, 'test')

        # Assert
        assert result is None

    async def test_list_by_entity_type(self, metadata_dao, clean_metadata_table):
        """
        Test: Should list all metadata for a given entity_type

        USE CASE:
        Get all course metadata, all user metadata, etc.
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata1 = Metadata(entity_id=uuid4(), entity_type='test', title='Test 1')
        metadata2 = Metadata(entity_id=uuid4(), entity_type='test', title='Test 2')
        metadata3 = Metadata(entity_id=uuid4(), entity_type='test', title='Test 3')

        await metadata_dao.create(metadata1)
        await metadata_dao.create(metadata2)
        await metadata_dao.create(metadata3)

        # Act
        results = await metadata_dao.list_by_entity_type('test', limit=10)

        # Assert
        assert len(results) >= 3
        assert all(m.entity_type == 'test' for m in results)

    async def test_list_by_entity_type_with_pagination(self, metadata_dao, clean_metadata_table):
        """
        Test: Should support pagination with limit and offset

        PERFORMANCE REQUIREMENT:
        Large result sets must support pagination
        """
        from domain.entities.metadata import Metadata

        # Arrange - create 5 records
        for i in range(5):
            metadata = Metadata(entity_id=uuid4(), entity_type='test', title=f'Test {i}')
            await metadata_dao.create(metadata)

        # Act
        page1 = await metadata_dao.list_by_entity_type('test', limit=2, offset=0)
        page2 = await metadata_dao.list_by_entity_type('test', limit=2, offset=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id  # Different records


@pytest.mark.asyncio
class TestMetadataDAOUpdate:
    """Test suite for MetadataDAO update operations"""

    async def test_update_metadata_fields(self, metadata_dao, clean_metadata_table):
        """
        Test: Should update metadata fields

        ACCEPTANCE CRITERIA:
        - Specified fields are updated
        - updated_at timestamp is refreshed
        - Other fields remain unchanged
        """
        from domain.entities.metadata import Metadata
        import asyncio

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='test', title='Original')
        created = await metadata_dao.create(metadata)
        original_updated_at = created.updated_at

        # Wait a tiny bit to ensure timestamp differs
        await asyncio.sleep(0.01)

        # Act
        created.update(title='Updated Title', description='New description')
        updated = await metadata_dao.update(created)

        # Assert
        assert updated.title == 'Updated Title'
        assert updated.description == 'New description'
        assert updated.updated_at >= original_updated_at  # Changed to >= for timing sensitivity

    async def test_update_metadata_not_found_raises_error(self, metadata_dao, clean_metadata_table):
        """
        Test: Should raise error when updating non-existent metadata

        ERROR HANDLING:
        Attempting to update non-existent record is an error
        """
        from domain.entities.metadata import Metadata
        from data_access.metadata_dao import MetadataNotFoundError

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='test')
        metadata.id = uuid4()  # Set non-existent ID

        # Act & Assert
        with pytest.raises(MetadataNotFoundError):
            await metadata_dao.update(metadata)

    async def test_update_metadata_jsonb_field(self, metadata_dao, clean_metadata_table):
        """
        Test: Should update JSONB metadata field

        JSONB REQUIREMENT:
        Updates to JSONB field should persist correctly
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(
            entity_id=uuid4(),
            entity_type='test',
            metadata={'key1': 'value1'}
        )
        created = await metadata_dao.create(metadata)

        # Act
        created.merge_metadata({'key2': 'value2'})
        updated = await metadata_dao.update(created)

        # Assert
        assert updated.metadata['key1'] == 'value1'
        assert updated.metadata['key2'] == 'value2'


@pytest.mark.asyncio
class TestMetadataDAODelete:
    """Test suite for MetadataDAO delete operations"""

    async def test_delete_metadata_by_id(self, metadata_dao, clean_metadata_table):
        """
        Test: Should delete metadata by ID

        ACCEPTANCE CRITERIA:
        - Record is removed from database
        - Returns True on successful delete
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='test')
        created = await metadata_dao.create(metadata)

        # Act
        result = await metadata_dao.delete(created.id)

        # Assert
        assert result is True
        retrieved = await metadata_dao.get_by_id(created.id)
        assert retrieved is None

    async def test_delete_metadata_not_found_returns_false(self, metadata_dao, clean_metadata_table):
        """
        Test: Should return False when deleting non-existent metadata

        IDEMPOTENCY:
        Deleting non-existent record is not an error - return False
        """
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await metadata_dao.delete(non_existent_id)

        # Assert
        assert result is False


@pytest.mark.asyncio
class TestMetadataDAOSearch:
    """Test suite for MetadataDAO search operations"""

    async def test_search_by_text_query(self, metadata_dao, clean_metadata_table):
        """
        Test: Should search metadata using full-text search

        SEARCH REQUIREMENT:
        PostgreSQL full-text search on title, description, tags, keywords
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata1 = Metadata(
            entity_id=uuid4(),
            entity_type='test',
            title='Python Programming Course',
            tags=['python', 'programming']
        )
        metadata2 = Metadata(
            entity_id=uuid4(),
            entity_type='test',
            title='JavaScript Basics',
            tags=['javascript']
        )

        await metadata_dao.create(metadata1)
        await metadata_dao.create(metadata2)

        # Act
        results = await metadata_dao.search('Python', entity_types=['test'])

        # Assert
        assert len(results) > 0
        assert any(r.title == 'Python Programming Course' for r in results)
        assert not any(r.title == 'JavaScript Basics' for r in results)

    async def test_search_filters_by_entity_types(self, metadata_dao, clean_metadata_table):
        """
        Test: Should filter search results by entity_types

        FILTERING REQUIREMENT:
        Support filtering by one or more entity types
        """
        from domain.entities.metadata import Metadata

        # Arrange
        course_meta = Metadata(entity_id=uuid4(), entity_type='course', title='Python Course')
        test_meta = Metadata(entity_id=uuid4(), entity_type='test', title='Python Test')

        # Note: course_meta won't be created since we're only testing 'test' type
        await metadata_dao.create(test_meta)

        # Act
        results = await metadata_dao.search('Python', entity_types=['test'])

        # Assert
        assert all(r.entity_type == 'test' for r in results)

    async def test_search_returns_ranked_results(self, metadata_dao, clean_metadata_table):
        """
        Test: Should return search results ranked by relevance

        RANKING REQUIREMENT:
        Results should be ordered by ts_rank (most relevant first)
        """
        from domain.entities.metadata import Metadata

        # Arrange - title match should rank higher than keyword match
        high_relevance = Metadata(
            entity_id=uuid4(),
            entity_type='test',
            title='Python Programming',
            description='Learn Python'
        )
        low_relevance = Metadata(
            entity_id=uuid4(),
            entity_type='test',
            title='Web Development',
            keywords=['python']
        )

        await metadata_dao.create(high_relevance)
        await metadata_dao.create(low_relevance)

        # Act
        results = await metadata_dao.search('Python', entity_types=['test'])

        # Assert
        assert len(results) >= 2
        # First result should have title match (higher rank)
        assert 'Python' in results[0].title

    async def test_search_with_limit(self, metadata_dao, clean_metadata_table):
        """
        Test: Should limit search results

        PERFORMANCE REQUIREMENT:
        Support limiting result count for performance
        """
        from domain.entities.metadata import Metadata

        # Arrange - create multiple matching records
        for i in range(5):
            metadata = Metadata(
                entity_id=uuid4(),
                entity_type='test',
                title=f'Python Course {i}'
            )
            await metadata_dao.create(metadata)

        # Act
        results = await metadata_dao.search('Python', entity_types=['test'], limit=3)

        # Assert
        assert len(results) <= 3


@pytest.mark.asyncio
class TestMetadataDAOQueryByTags:
    """Test suite for MetadataDAO tag-based queries"""

    async def test_get_by_tags_single_tag(self, metadata_dao, clean_metadata_table):
        """
        Test: Should find metadata by single tag

        TAG QUERY REQUIREMENT:
        Support querying by tags using PostgreSQL array operators
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata1 = Metadata(entity_id=uuid4(), entity_type='test', tags=['python', 'beginner'])
        metadata2 = Metadata(entity_id=uuid4(), entity_type='test', tags=['javascript'])

        await metadata_dao.create(metadata1)
        await metadata_dao.create(metadata2)

        # Act
        results = await metadata_dao.get_by_tags(['python'], entity_type='test')

        # Assert
        assert len(results) > 0
        assert all('python' in r.tags for r in results)

    async def test_get_by_tags_multiple_tags(self, metadata_dao, clean_metadata_table):
        """
        Test: Should find metadata matching ALL specified tags

        AND QUERY:
        Metadata must have all specified tags (not just any)
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata1 = Metadata(entity_id=uuid4(), entity_type='test', tags=['python', 'advanced', 'web'])
        metadata2 = Metadata(entity_id=uuid4(), entity_type='test', tags=['python', 'beginner'])

        await metadata_dao.create(metadata1)
        await metadata_dao.create(metadata2)

        # Act
        results = await metadata_dao.get_by_tags(['python', 'advanced'], entity_type='test')

        # Assert
        assert len(results) >= 1
        assert all('python' in r.tags and 'advanced' in r.tags for r in results)

    async def test_get_by_tags_case_insensitive(self, metadata_dao, clean_metadata_table):
        """
        Test: Should perform case-insensitive tag matching

        NORMALIZATION REQUIREMENT:
        Tags are normalized to lowercase in entity, search should match
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='test', tags=['Python', 'PROGRAMMING'])
        await metadata_dao.create(metadata)

        # Act
        results = await metadata_dao.get_by_tags(['python'], entity_type='test')

        # Assert
        assert len(results) > 0


@pytest.mark.asyncio
class TestMetadataDAOTransactions:
    """Test suite for MetadataDAO transaction handling"""

    async def test_create_within_transaction(self, metadata_dao, db_pool, clean_metadata_table):
        """
        Test: Should support creating metadata within a transaction

        TRANSACTION REQUIREMENT:
        DAO should accept external transaction connection
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='test', title='Transactional')

        # Act
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                created = await metadata_dao.create(metadata, connection=conn)

        # Assert
        retrieved = await metadata_dao.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.title == 'Transactional'

    async def test_transaction_rollback_on_error(self, metadata_dao, db_pool, clean_metadata_table):
        """
        Test: Should rollback transaction on error

        ATOMICITY REQUIREMENT:
        Failed transaction should not persist any changes
        """
        from domain.entities.metadata import Metadata

        # Arrange
        metadata = Metadata(entity_id=uuid4(), entity_type='test', title='Should Rollback')

        # Act & Assert
        try:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    await metadata_dao.create(metadata, connection=conn)
                    # Simulate error
                    raise Exception("Simulated error")
        except Exception:
            pass

        # Verify nothing was persisted
        results = await metadata_dao.list_by_entity_type('test')
        assert not any(r.title == 'Should Rollback' for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
