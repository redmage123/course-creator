"""
Metadata Service E2E Tests

DEVELOPMENT METHODOLOGY:
This file follows TDD (Test-Driven Development) - RED-GREEN-REFACTOR cycle.
Each test was written FIRST (expecting failure), then code was fixed to make it pass.

BUSINESS REQUIREMENT:
Test the complete metadata service integration with real PostgreSQL database
to ensure entity metadata CRUD operations work correctly end-to-end.

TECHNICAL APPROACH:
- Real database connection via asyncpg
- Test fixtures with proper cleanup
- Function-scoped event loops (pytest-asyncio)
- Tests organized by DAO, Service, and Complete Workflow categories

WHY E2E TESTS:
Unit tests mock the database. E2E tests catch real integration issues like:
- Database connection handling
- Transaction management
- JSON/JSONB serialization
- UUID type handling
- Actual SQL query correctness
"""

import pytest
import pytest_asyncio
import asyncpg
import json
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Dict, Any
import os

# Add metadata-service to path

# Import domain entities
from metadata_service.domain.entities.metadata import Metadata
from data_access.metadata_dao import MetadataDAO


# ========================================
# TEST FIXTURES
# ========================================

@pytest_asyncio.fixture(scope="function")
async def db_pool():
    """
    Create database connection pool for tests

    BUSINESS VALUE:
    Real database testing catches integration issues that mocks cannot

    TECHNICAL IMPLEMENTATION:
    - Function-scoped to avoid event loop issues
    - Proper cleanup after each test
    - Uses course_creator database
    """
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='postgres',
        password='postgres_password',
        database='course_creator',
        min_size=1,
        max_size=5
    )

    yield pool

    await pool.close()


@pytest_asyncio.fixture(scope="function")
async def dao(db_pool):
    """
    Create MetadataDAO instance with database pool

    BUSINESS VALUE:
    DAO layer handles all database operations for metadata

    Args:
        db_pool: Database connection pool

    Returns:
        MetadataDAO instance
    """
    return MetadataDAO(db_pool)


@pytest_asyncio.fixture(scope="function")
async def cleanup_metadata(db_pool):
    """
    Clean up test metadata after each test

    BUSINESS VALUE:
    Ensures test isolation and prevents data pollution

    TECHNICAL IMPLEMENTATION:
    - Runs after test completes
    - Deletes all test metadata from database
    - Uses CASCADE to handle relationships
    """
    created_ids = []

    yield created_ids

    # Cleanup after test
    if created_ids:
        async with db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM entity_metadata WHERE id = ANY($1)",
                created_ids
            )


# ========================================
# METADATA DAO E2E TESTS
# ========================================

class TestMetadataDAOE2E:
    """
    E2E tests for MetadataDAO with real database

    BUSINESS VALUE:
    Verify that metadata CRUD operations work correctly with actual PostgreSQL
    """

    @pytest.mark.asyncio
    async def test_create_and_retrieve_metadata(self, dao, cleanup_metadata):
        """
        TEST 1: Create metadata and retrieve it by ID

        TDD CYCLE:
        - RED: Write this test expecting it to FAIL
        - GREEN: Fix DAO transaction pattern to make it PASS
        - REFACTOR: Clean up code if needed

        BUSINESS USE CASE:
        When creating course metadata, we need to store and retrieve it

        EXPECTED BEHAVIOR:
        1. Create metadata with all fields
        2. Retrieve by ID
        3. Verify all fields match
        """
        # Create test metadata
        metadata = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'beginner', 'duration': 40, 'category': 'programming'},
            title='Introduction to Python',
            description='Learn Python programming from scratch',
            tags=['python', 'programming', 'beginner'],
            keywords=['python', 'coding', 'tutorial']
        )

        # Create in database
        created = await dao.create(metadata)
        cleanup_metadata.append(created.id)

        # Verify creation
        assert created.id is not None
        assert created.entity_type == 'course'
        assert created.title == 'Introduction to Python'
        assert created.metadata == {'difficulty': 'beginner', 'duration': 40, 'category': 'programming'}

        # Retrieve by ID
        retrieved = await dao.get_by_id(created.id)

        # Verify retrieval
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.entity_type == metadata.entity_type
        assert retrieved.entity_id == metadata.entity_id
        assert retrieved.title == metadata.title
        assert retrieved.description == metadata.description
        assert retrieved.metadata == metadata.metadata
        assert retrieved.tags == metadata.tags
        assert retrieved.keywords == metadata.keywords

    @pytest.mark.asyncio
    async def test_search_metadata(self, dao, cleanup_metadata):
        """
        TEST 2: Search metadata with full-text search

        TDD CYCLE:
        - RED: Write this test expecting it to FAIL
        - GREEN: Fix DAO search implementation if needed
        - REFACTOR: Clean up code if needed

        BUSINESS USE CASE:
        Students search for courses by keywords in title/description/tags

        EXPECTED BEHAVIOR:
        1. Create multiple metadata entries
        2. Search by keyword
        3. Verify correct results returned
        """
        # Create test metadata entries
        metadata1 = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'beginner'},
            title='Python Programming Basics',
            description='Learn Python from scratch',
            tags=['python', 'programming'],
            keywords=['python', 'beginner']
        )

        metadata2 = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'advanced'},
            title='JavaScript Advanced Patterns',
            description='Master JavaScript design patterns',
            tags=['javascript', 'programming'],
            keywords=['javascript', 'advanced']
        )

        metadata3 = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'intermediate'},
            title='Python Data Science',
            description='Data analysis with Python pandas',
            tags=['python', 'data-science'],
            keywords=['python', 'data', 'pandas']
        )

        # Create in database
        created1 = await dao.create(metadata1)
        created2 = await dao.create(metadata2)
        created3 = await dao.create(metadata3)

        cleanup_metadata.extend([created1.id, created2.id, created3.id])

        # Search for "python" - should return 2 results
        results = await dao.search('python', entity_types=['course'], limit=10)

        assert len(results) >= 2  # At least our 2 python courses
        python_courses = [r for r in results if 'python' in r.title.lower() or 'python' in r.tags]
        assert len(python_courses) >= 2

        # Verify python courses are in results
        result_ids = [r.id for r in results]
        assert created1.id in result_ids
        assert created3.id in result_ids

    @pytest.mark.asyncio
    async def test_update_metadata(self, dao, cleanup_metadata):
        """
        TEST 3: Update metadata

        TDD CYCLE:
        - RED: Write this test expecting it to FAIL
        - GREEN: Fix DAO update implementation if needed
        - REFACTOR: Clean up code if needed

        BUSINESS USE CASE:
        Instructor updates course metadata (title, description, tags)

        EXPECTED BEHAVIOR:
        1. Create metadata
        2. Update fields
        3. Verify changes persisted
        """
        # Create test metadata
        metadata = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'beginner'},
            title='Original Title',
            description='Original description',
            tags=['original'],
            keywords=['original']
        )

        # Create in database
        created = await dao.create(metadata)
        cleanup_metadata.append(created.id)

        # Update metadata
        created.title = 'Updated Title'
        created.description = 'Updated description'
        created.tags = ['updated', 'new-tag']
        created.metadata = {'difficulty': 'intermediate', 'category': 'advanced'}

        # Perform update
        updated = await dao.update(created)

        # Verify update
        assert updated.id == created.id
        assert updated.title == 'Updated Title'
        assert updated.description == 'Updated description'
        assert updated.tags == ['updated', 'new-tag']
        assert updated.metadata == {'difficulty': 'intermediate', 'category': 'advanced'}

        # Retrieve from database to confirm persistence
        retrieved = await dao.get_by_id(created.id)
        assert retrieved.title == 'Updated Title'
        assert retrieved.metadata == {'difficulty': 'intermediate', 'category': 'advanced'}

    @pytest.mark.asyncio
    async def test_delete_metadata(self, dao, cleanup_metadata):
        """
        TEST 4: Delete metadata

        TDD CYCLE:
        - RED: Write this test expecting it to FAIL
        - GREEN: Fix DAO delete implementation if needed
        - REFACTOR: Clean up code if needed

        BUSINESS USE CASE:
        Remove metadata when course is deleted

        EXPECTED BEHAVIOR:
        1. Create metadata
        2. Delete it
        3. Verify it's gone
        """
        # Create test metadata
        metadata = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'test': 'data'},
            title='Test Course',
            description='Test description',
            tags=['test'],
            keywords=['test']
        )

        # Create in database
        created = await dao.create(metadata)

        # Verify it exists
        exists = await dao.get_by_id(created.id)
        assert exists is not None

        # Delete it
        deleted = await dao.delete(created.id)
        assert deleted is True

        # Verify it's gone
        not_found = await dao.get_by_id(created.id)
        assert not_found is None


# ========================================
# FUZZY LOGIC TESTS
# ========================================

class TestFuzzySearchE2E:
    """
    E2E tests for fuzzy search with typo tolerance and partial matching

    BUSINESS VALUE:
    Students can find courses even with typos or imperfect search terms
    """

    @pytest.mark.asyncio
    async def test_fuzzy_search_with_typos(self, dao, cleanup_metadata):
        """
        TEST 5: Fuzzy search handles typos

        TDD CYCLE:
        - RED: Write this test expecting it to FAIL (no fuzzy search method yet)
        - GREEN: Implement fuzzy search in DAO
        - REFACTOR: Clean up code if needed

        BUSINESS USE CASE:
        Student searches for "pyton" instead of "python" - should still find courses

        EXPECTED BEHAVIOR:
        1. Create course with "Python" in title
        2. Search for "pyton" (typo)
        3. Should still find the course with similarity score
        """
        # Create test course
        metadata = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'beginner'},
            title='Python Programming Fundamentals',
            description='Learn Python from scratch with hands-on projects',
            tags=['python', 'programming', 'beginner'],
            keywords=['python', 'coding', 'fundamentals']
        )

        created = await dao.create(metadata)
        cleanup_metadata.append(created.id)

        # Test 1: Search with typo "pyton" should find "Python"
        # Note: trigram similarity works on individual words in tags
        # "pyton" has 0.44 similarity to "python" tag
        results = await dao.search_fuzzy('pyton', entity_types=['course'], similarity_threshold=0.2)

        # Should find the course despite typo (matches 'python' tag)
        assert len(results) > 0, "Should find course with 'pyton' matching 'python' tag"

        # Results should be tuples of (metadata, similarity_score)
        found_course = None
        for result_metadata, similarity_score in results:
            if result_metadata.id == created.id:
                found_course = result_metadata
                # Similarity between "pyton" and tags containing "python" should be reasonable
                assert similarity_score > 0.2, f"Similarity too low: {similarity_score}"
                assert similarity_score < 1.0, "Not exact match"
                break

        assert found_course is not None, "Should find course with typo 'pyton'"

        # Test 2: Search with another typo "progamming" (missing 'r')
        # "progamming" has ~0.5 similarity to "programming"
        results2 = await dao.search_fuzzy('progamming', entity_types=['course'], similarity_threshold=0.2)

        found_ids = [m.id for m, score in results2]
        assert created.id in found_ids, "Should find course with typo 'progamming'"

    @pytest.mark.asyncio
    async def test_fuzzy_search_partial_match(self, dao, cleanup_metadata):
        """
        TEST 6: Fuzzy search handles partial matches

        TDD CYCLE:
        - RED: Write this test expecting current behavior
        - GREEN: Verify fuzzy search handles partial terms
        - REFACTOR: Optimize if needed

        BUSINESS USE CASE:
        Student searches for "prog" - should find "Programming" courses

        EXPECTED BEHAVIOR:
        1. Create courses with various programming-related titles
        2. Search for partial term "prog"
        3. Should find courses with similarity scores
        """
        # Create test courses
        metadata1 = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'beginner'},
            title='Introduction to Programming',
            description='Learn programming basics',
            tags=['programming', 'beginner'],
            keywords=['programming', 'coding']
        )

        metadata2 = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'intermediate'},
            title='Advanced Programming Techniques',
            description='Master programming concepts',
            tags=['programming', 'advanced'],
            keywords=['programming', 'algorithms']
        )

        metadata3 = Metadata(
            entity_type='course',
            entity_id=uuid4(),
            metadata={'difficulty': 'beginner'},
            title='Web Design Fundamentals',
            description='Learn HTML and CSS',
            tags=['web', 'design'],
            keywords=['html', 'css', 'design']
        )

        created1 = await dao.create(metadata1)
        created2 = await dao.create(metadata2)
        created3 = await dao.create(metadata3)

        cleanup_metadata.extend([created1.id, created2.id, created3.id])

        # Search for partial term "prog" - should match "programming"
        results = await dao.search_fuzzy('prog', entity_types=['course'], similarity_threshold=0.3)

        # Should find programming courses
        found_ids = [m.id for m, score in results]
        assert created1.id in found_ids, "Should find 'Introduction to Programming'"
        assert created2.id in found_ids, "Should find 'Advanced Programming Techniques'"

        # Should NOT find web design course (or if found, should have low similarity)
        web_design_found = any(m.id == created3.id for m, score in results)
        if web_design_found:
            # If found, similarity should be very low
            for m, score in results:
                if m.id == created3.id:
                    assert score < 0.5, "Web design should have low similarity to 'prog'"


# ========================================
# END OF FILE
# ========================================
