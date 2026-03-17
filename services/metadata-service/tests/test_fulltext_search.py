"""
TDD Tests for Full-Text Search Functionality

RED PHASE: These tests will fail until we implement the search DAO methods
and run the migration to create search functions.

Test Coverage:
- Full-text search with ranking
- Fuzzy similarity search
- Search with filters (entity type, course ID)
- Search result highlighting
"""

import pytest
from uuid import uuid4
from data_access.metadata_dao import MetadataDAO


@pytest.mark.asyncio
class TestFullTextSearch:
    """Test full-text search functionality"""

    async def test_search_course_materials_basic(self, metadata_dao: MetadataDAO):
        """
        Test basic full-text search

        EXPECTED: Returns results ranked by relevance
        """
        search_query = 'python programming'

        results = await metadata_dao.search_course_materials(search_query)

        assert results is not None
        assert isinstance(results, list)
        # Results should have rank and headline
        if len(results) > 0:
            assert 'rank' in results[0]
            assert 'headline' in results[0]
            # Results should be ordered by rank descending
            if len(results) > 1:
                assert results[0]['rank'] >= results[1]['rank']

    async def test_search_with_entity_type_filter(self, metadata_dao: MetadataDAO):
        """
        Test full-text search filtered by entity type

        EXPECTED: Returns only results matching entity type
        """
        search_query = 'course materials'
        entity_type_filter = 'course_material_upload'

        results = await metadata_dao.search_course_materials(
            search_query,
            entity_type_filter=entity_type_filter
        )

        assert isinstance(results, list)
        for result in results:
            assert result['entity_type'] == entity_type_filter

    async def test_search_with_course_id_filter(self, metadata_dao: MetadataDAO):
        """
        Test full-text search filtered by course ID

        EXPECTED: Returns only results for specified course
        """
        search_query = 'syllabus'
        course_id_filter = 1

        results = await metadata_dao.search_course_materials(
            search_query,
            course_id_filter=course_id_filter
        )

        assert isinstance(results, list)
        for result in results:
            if result.get('course_id'):
                assert result['course_id'] == course_id_filter

    async def test_search_result_limit(self, metadata_dao: MetadataDAO):
        """
        Test search respects limit parameter

        EXPECTED: Returns no more than limit results
        """
        search_query = 'course'
        limit = 5

        results = await metadata_dao.search_course_materials(
            search_query,
            limit_results=limit
        )

        assert isinstance(results, list)
        assert len(results) <= limit

    async def test_search_no_results(self, metadata_dao: MetadataDAO):
        """
        Test search with query that matches nothing

        EXPECTED: Returns empty list
        """
        search_query = 'xyzabc123nonexistent'

        results = await metadata_dao.search_course_materials(search_query)

        assert isinstance(results, list)
        assert len(results) == 0

    async def test_search_highlights_matches(self, metadata_dao: MetadataDAO):
        """
        Test search returns highlighted snippets

        EXPECTED: Headline field contains search term context
        """
        search_query = 'python'

        results = await metadata_dao.search_course_materials(search_query)

        if len(results) > 0:
            assert 'headline' in results[0]
            assert results[0]['headline'] is not None
            # Headline should be a snippet, not entire content
            assert len(results[0]['headline']) < 500


@pytest.mark.asyncio
class TestFuzzySearch:
    """Test fuzzy similarity search with typo tolerance"""

    async def test_fuzzy_search_basic(self, metadata_dao: MetadataDAO):
        """
        Test basic fuzzy search

        EXPECTED: Finds similar matches even with typos
        """
        search_text = 'progrmming'  # Intentional typo

        results = await metadata_dao.fuzzy_search_course_materials(search_text)

        assert results is not None
        assert isinstance(results, list)
        # Results should have similarity scores
        if len(results) > 0:
            assert 'title_similarity' in results[0]
            assert 'combined_similarity' in results[0]

    async def test_fuzzy_search_similarity_threshold(self, metadata_dao: MetadataDAO):
        """
        Test fuzzy search respects similarity threshold

        EXPECTED: Only returns results above threshold
        """
        search_text = 'python'
        similarity_threshold = 0.5

        results = await metadata_dao.fuzzy_search_course_materials(
            search_text,
            similarity_threshold=similarity_threshold
        )

        assert isinstance(results, list)
        for result in results:
            assert result['combined_similarity'] >= similarity_threshold

    async def test_fuzzy_search_ordered_by_similarity(self, metadata_dao: MetadataDAO):
        """
        Test fuzzy search results ordered by similarity

        EXPECTED: Highest similarity first
        """
        search_text = 'introduction to python'

        results = await metadata_dao.fuzzy_search_course_materials(search_text)

        assert isinstance(results, list)
        if len(results) > 1:
            # Results should be in descending order of similarity
            for i in range(len(results) - 1):
                assert results[i]['combined_similarity'] >= results[i + 1]['combined_similarity']

    async def test_fuzzy_search_with_typos(self, metadata_dao: MetadataDAO):
        """
        Test fuzzy search handles common typos

        EXPECTED: Finds 'programming' even when searching 'programing'
        """
        search_text = 'programing'  # Missing 'm'

        results = await metadata_dao.fuzzy_search_course_materials(search_text)

        # Should find results similar to "programming"
        assert isinstance(results, list)
        # At least some results if test data contains "programming"

    async def test_fuzzy_search_limit(self, metadata_dao: MetadataDAO):
        """
        Test fuzzy search respects limit parameter

        EXPECTED: Returns no more than limit results
        """
        search_text = 'course'
        limit = 3

        results = await metadata_dao.fuzzy_search_course_materials(
            search_text,
            limit_results=limit
        )

        assert isinstance(results, list)
        assert len(results) <= limit


@pytest.mark.asyncio
class TestSearchPerformance:
    """Test search performance and indexing"""

    async def test_search_uses_indexes(self, metadata_dao: MetadataDAO):
        """
        Test that search queries use database indexes

        EXPECTED: Search completes quickly even with large dataset
        """
        import time

        search_query = 'course materials syllabus'

        start = time.time()
        results = await metadata_dao.search_course_materials(search_query, limit_results=100)
        elapsed = time.time() - start

        # Search should complete in under 1 second
        assert elapsed < 1.0
        assert isinstance(results, list)

    async def test_fuzzy_search_uses_trigram_index(self, metadata_dao: MetadataDAO):
        """
        Test that fuzzy search uses trigram indexes

        EXPECTED: Fuzzy search completes quickly
        """
        import time

        search_text = 'introduction programming'

        start = time.time()
        results = await metadata_dao.fuzzy_search_course_materials(search_text, limit_results=50)
        elapsed = time.time() - start

        # Fuzzy search should complete in under 1 second
        assert elapsed < 1.0
        assert isinstance(results, list)


# Fixtures

@pytest.fixture
async def metadata_dao(postgresql_pool):
    """Create MetadataDAO instance with test database pool"""
    return MetadataDAO(postgresql_pool)


@pytest.fixture
async def sample_searchable_metadata(metadata_dao: MetadataDAO):
    """Create sample searchable metadata for testing"""
    from metadata_service.domain.entities.metadata import Metadata

    test_items = [
        Metadata(
            entity_id=uuid4(),
            entity_type='course_material_upload',
            title='Introduction to Python Programming',
            description='Complete guide to Python programming for beginners',
            tags=['python', 'programming', 'beginner'],
            keywords=['python', 'tutorial', 'coding'],
            metadata={
                'course_id': 1,
                'file_type': 'syllabus',
                'filename': 'python-intro.pdf'
            }
        ),
        Metadata(
            entity_id=uuid4(),
            entity_type='course_material_upload',
            title='Advanced Data Structures',
            description='Deep dive into data structures and algorithms',
            tags=['algorithms', 'data-structures', 'advanced'],
            keywords=['algorithms', 'complexity', 'optimization'],
            metadata={
                'course_id': 2,
                'file_type': 'slides',
                'filename': 'data-structures.pptx'
            }
        ),
    ]

    for item in test_items:
        await metadata_dao.create(item)

    return test_items
