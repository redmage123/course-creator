"""
Integration Tests for Sub-Project DAO with Real Database

BUSINESS CONTEXT:
Tests data access operations for sub-projects (locations) using real PostgreSQL database.
Verifies complete CRUD operations, locations filtering, date range queries, and track assignments.

TESTING APPROACH:
- Uses real database connection (not mocks)
- Creates and cleans up test data
- Tests actual SQL execution and constraints
- Validates triggers and database logic
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from uuid import uuid4
import os
import sys
from pathlib import Path

# Add course-management service to Python path
project_root = Path(__file__).parent.parent.parent
course_mgmt_path = project_root / "services" / "course-management"
if str(course_mgmt_path) not in sys.path:
    sys.path.insert(0, str(course_mgmt_path))

# Import DAO and entities
from data_access.sub_project_dao import SubProjectDAO
from course_management.domain.entities.sub_project import SubProject
from course_management.infrastructure.exceptions import (
    SubProjectNotFoundException,
    DuplicateSubProjectException,
    InvalidLocationException,
    InvalidDateRangeException,
    SubProjectCapacityException
)


# Database connection parameters
TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres_password@localhost:5433/course_creator"
)


@pytest.fixture(scope="function")
def db_connection():
    """
    Create real database connection for each test

    BUSINESS CONTEXT:
    Integration tests require real database to verify SQL execution,
    constraints, triggers, and data persistence.
    """
    conn = psycopg2.connect(TEST_DATABASE_URL)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def clean_test_data(db_connection):
    """
    Clean up test data before and after each test

    WORKFLOW:
    1. Delete test sub-projects before test
    2. Yield to run test
    3. Delete test sub-projects after test
    """
    cursor = db_connection.cursor()

    # Clean before test
    cursor.execute("DELETE FROM sub_projects WHERE name LIKE 'Test%' OR name LIKE '%Integration%'")
    db_connection.commit()

    yield

    # Clean after test
    cursor.execute("DELETE FROM sub_projects WHERE name LIKE 'Test%' OR name LIKE '%Integration%'")
    db_connection.commit()
    cursor.close()


@pytest.fixture(scope="function")
def sub_project_dao(db_connection):
    """Create SubProjectDAO instance with real connection"""
    return SubProjectDAO(db_connection)


@pytest.fixture(scope="function")
def test_organization_id(db_connection):
    """Get existing organization ID from database"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Get existing project and its organization_id
    cursor.execute("SELECT organization_id FROM projects LIMIT 1")
    result = cursor.fetchone()

    if result:
        org_id = str(result['organization_id'])
    else:
        # Use a fixed UUID for testing
        org_id = "e3eed65f-c023-47bf-b811-05fc7138cca8"

    cursor.close()
    return org_id


@pytest.fixture(scope="function")
def test_parent_project(db_connection, test_organization_id):
    """Create test parent project"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)

    # Create a unique slug for this test run
    import time
    unique_slug = f'test-parent-project-{int(time.time() * 1000)}'

    cursor.execute("""
        INSERT INTO projects (
            organization_id, name, slug, description, has_sub_projects, status
        ) VALUES (
            %s, 'Test Parent Project', %s,
            'Integration test parent project', TRUE, 'active'
        )
        RETURNING id
    """, (test_organization_id, unique_slug))

    project_id = str(cursor.fetchone()['id'])
    db_connection.commit()
    cursor.close()

    yield project_id

    # Cleanup
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    db_connection.commit()
    cursor.close()


@pytest.fixture(scope="function")
def sample_sub_project_data(test_parent_project, test_organization_id):
    """Sample sub-project data for testing"""
    return {
        'parent_project_id': test_parent_project,
        'organization_id': test_organization_id,
        'name': 'Test Boston Locations Fall 2025',
        'slug': 'test-boston-fall-2025',
        'description': 'Integration test locations for Boston office',
        'location_country': 'United States',
        'location_region': 'Massachusetts',
        'location_city': 'Boston',
        'location_address': '123 Main Street, Boston, MA 02101',
        'timezone': 'America/New_York',
        'start_date': datetime.now() + timedelta(days=30),
        'end_date': datetime.now() + timedelta(days=150),
        'max_participants': 30,
        'current_participants': 0,
        'status': 'draft',
        'created_by': test_organization_id,
        'metadata': {}
    }


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestSubProjectCreationIntegration:
    """Test creating sub-projects with real database"""

    def test_create_sub_project_success(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test successfully creating a new sub-project"""
        # Create sub-project
        result = sub_project_dao.create_sub_project(sample_sub_project_data)

        # Verify result
        assert result is not None
        assert 'id' in result
        assert result['name'] == 'Test Boston Locations Fall 2025'
        assert result['location_city'] == 'Boston'
        assert result['location_country'] == 'United States'
        assert result['status'] == 'draft'

        # Verify duration was auto-calculated
        assert result['duration_weeks'] is not None
        assert result['duration_weeks'] > 0

    def test_create_sub_project_with_duplicate_slug(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test creating sub-project with duplicate slug raises exception"""
        # Create first sub-project
        sub_project_dao.create_sub_project(sample_sub_project_data)

        # Try to create with same slug
        with pytest.raises(DuplicateSubProjectException):
            sub_project_dao.create_sub_project(sample_sub_project_data)

    def test_create_sub_project_validates_location(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test that locations validation occurs during creation"""
        # Missing required locations field
        invalid_data = sample_sub_project_data.copy()
        invalid_data['location_country'] = None

        with pytest.raises(InvalidLocationException):
            sub_project_dao.create_sub_project(invalid_data)

    def test_create_sub_project_validates_dates(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test that date validation occurs (start_date < end_date)"""
        # Invalid date range
        invalid_data = sample_sub_project_data.copy()
        invalid_data['start_date'] = datetime.now() + timedelta(days=100)
        invalid_data['end_date'] = datetime.now() + timedelta(days=50)

        with pytest.raises(InvalidDateRangeException):
            sub_project_dao.create_sub_project(invalid_data)


class TestSubProjectRetrievalIntegration:
    """Test retrieving sub-projects from database"""

    def test_get_sub_project_by_id_success(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test retrieving sub-project by ID"""
        # Create sub-project
        created = sub_project_dao.create_sub_project(sample_sub_project_data)

        # Retrieve by ID
        result = sub_project_dao.get_sub_project_by_id(created['id'])

        assert result is not None
        assert result['id'] == created['id']
        assert result['name'] == 'Test Boston Locations Fall 2025'

    def test_get_sub_project_by_id_not_found(
        self, sub_project_dao, clean_test_data
    ):
        """Test retrieving non-existent sub-project raises exception"""
        fake_id = str(uuid4())

        with pytest.raises(SubProjectNotFoundException):
            sub_project_dao.get_sub_project_by_id(fake_id)

    def test_get_sub_projects_by_parent_project(
        self, sub_project_dao, sample_sub_project_data, test_parent_project, clean_test_data
    ):
        """Test retrieving all sub-projects for a parent project"""
        # Create 3 sub-projects
        data1 = sample_sub_project_data.copy()
        data1['name'] = 'Test Boston Locations'
        data1['slug'] = 'test-boston-locations'

        data2 = sample_sub_project_data.copy()
        data2['name'] = 'Test London Locations'
        data2['slug'] = 'test-london-locations'
        data2['location_city'] = 'London'
        data2['location_country'] = 'United Kingdom'

        data3 = sample_sub_project_data.copy()
        data3['name'] = 'Test Tokyo Locations'
        data3['slug'] = 'test-tokyo-locations'
        data3['location_city'] = 'Tokyo'
        data3['location_country'] = 'Japan'

        sub_project_dao.create_sub_project(data1)
        sub_project_dao.create_sub_project(data2)
        sub_project_dao.create_sub_project(data3)

        # Retrieve all
        results = sub_project_dao.get_sub_projects_by_parent(test_parent_project)

        assert len(results) == 3
        cities = [r['location_city'] for r in results]
        assert 'Boston' in cities
        assert 'London' in cities
        assert 'Tokyo' in cities

    def test_get_sub_projects_with_location_filter(
        self, sub_project_dao, sample_sub_project_data, test_parent_project, clean_test_data
    ):
        """Test filtering sub-projects by locations"""
        # Create locations in different locations
        data_us = sample_sub_project_data.copy()
        data_us['name'] = 'Test US Locations'
        data_us['slug'] = 'test-us-locations'

        data_uk = sample_sub_project_data.copy()
        data_uk['name'] = 'Test UK Locations'
        data_uk['slug'] = 'test-uk-locations'
        data_uk['location_country'] = 'United Kingdom'
        data_uk['location_city'] = 'London'

        sub_project_dao.create_sub_project(data_us)
        sub_project_dao.create_sub_project(data_uk)

        # Filter by country
        results = sub_project_dao.get_sub_projects_by_parent(
            test_parent_project,
            filters={'location_country': 'United States'}
        )

        assert len(results) == 1
        assert results[0]['location_country'] == 'United States'


class TestSubProjectUpdateIntegration:
    """Test updating sub-projects"""

    def test_update_sub_project_success(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test successfully updating a sub-project"""
        # Create sub-project
        created = sub_project_dao.create_sub_project(sample_sub_project_data)

        # Update fields
        updated_data = {
            'name': 'Test Boston Locations Spring 2026',
            'max_participants': 35,
            'status': 'active'
        }

        result = sub_project_dao.update_sub_project(created['id'], updated_data)
        assert result is True

        # Verify update
        retrieved = sub_project_dao.get_sub_project_by_id(created['id'])
        assert retrieved['name'] == 'Test Boston Locations Spring 2026'
        assert retrieved['max_participants'] == 35
        assert retrieved['status'] == 'active'

    def test_update_sub_project_not_found(
        self, sub_project_dao, clean_test_data
    ):
        """Test updating non-existent sub-project"""
        fake_id = str(uuid4())

        with pytest.raises(SubProjectNotFoundException):
            sub_project_dao.update_sub_project(fake_id, {'name': 'New Name'})


class TestSubProjectDeletionIntegration:
    """Test deleting sub-projects"""

    def test_delete_sub_project_success(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test successfully deleting a sub-project"""
        # Create sub-project
        created = sub_project_dao.create_sub_project(sample_sub_project_data)

        # Delete
        result = sub_project_dao.delete_sub_project(created['id'])
        assert result is True

        # Verify deletion
        with pytest.raises(SubProjectNotFoundException):
            sub_project_dao.get_sub_project_by_id(created['id'])

    def test_delete_sub_project_not_found(
        self, sub_project_dao, clean_test_data
    ):
        """Test deleting non-existent sub-project"""
        fake_id = str(uuid4())

        with pytest.raises(SubProjectNotFoundException):
            sub_project_dao.delete_sub_project(fake_id)


class TestSubProjectCapacityManagementIntegration:
    """Test participant capacity tracking"""

    def test_increment_participant_count(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test incrementing current_participants when student enrolls"""
        # Create sub-project
        created = sub_project_dao.create_sub_project(sample_sub_project_data)

        # Increment
        result = sub_project_dao.increment_participant_count(created['id'])

        assert result['current_participants'] == 1
        assert result['max_participants'] == 30

    def test_increment_participant_count_at_capacity_fails(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test cannot enroll when at max capacity"""
        # Create sub-project with capacity 2
        data = sample_sub_project_data.copy()
        data['max_participants'] = 2
        data['current_participants'] = 2

        created = sub_project_dao.create_sub_project(data)

        # Try to increment when at capacity
        with pytest.raises(SubProjectCapacityException):
            sub_project_dao.increment_participant_count(created['id'])


class TestSubProjectStatusTransitionsIntegration:
    """Test status lifecycle management"""

    def test_activate_sub_project(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test transitioning from draft to active"""
        # Create sub-project
        created = sub_project_dao.create_sub_project(sample_sub_project_data)

        # Activate
        result = sub_project_dao.update_status(created['id'], 'active')
        assert result is True

        # Verify
        retrieved = sub_project_dao.get_sub_project_by_id(created['id'])
        assert retrieved['status'] == 'active'

    def test_invalid_status_transition_fails(
        self, sub_project_dao, sample_sub_project_data, clean_test_data
    ):
        """Test invalid status value raises exception"""
        # Create sub-project
        created = sub_project_dao.create_sub_project(sample_sub_project_data)

        with pytest.raises(ValueError):
            sub_project_dao.update_status(created['id'], 'invalid_status')


# ==============================================================================
# TEST EXECUTION
# ==============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
