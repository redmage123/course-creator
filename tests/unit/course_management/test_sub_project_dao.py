"""
Unit Tests for Sub-Project DAO

BUSINESS CONTEXT:
Tests data access operations for sub-projects (locations) including CRUD operations,
locations filtering, date range queries, and track assignments.

TDD RED PHASE - These tests should FAIL initially
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4


# Import the modules we'll implement
# These imports will fail initially (RED PHASE)
try:
    from course_management.data_access.sub_project_dao import SubProjectDAO
    from course_management.domain.entities.sub_project import SubProject
    from course_management.infrastructure.exceptions import (
        SubProjectNotFoundException,
        DuplicateSubProjectException,
        InvalidLocationException,
        InvalidDateRangeException
    )
except ImportError:
    # Placeholder for imports during RED phase
    SubProjectDAO = None
    SubProject = None
    SubProjectNotFoundException = Exception
    DuplicateSubProjectException = Exception
    InvalidLocationException = Exception
    InvalidDateRangeException = Exception


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    conn = Mock()
    cursor = Mock()
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn


@pytest.fixture
def sub_project_dao(mock_db_connection):
    """Create SubProjectDAO instance with mocked connection"""
    if SubProjectDAO is None:
        pytest.skip("SubProjectDAO not yet implemented (TDD RED PHASE)")
    return SubProjectDAO(mock_db_connection)


@pytest.fixture
def sample_sub_project_data():
    """Sample sub-project data for testing"""
    return {
        'id': str(uuid4()),
        'parent_project_id': str(uuid4()),
        'organization_id': str(uuid4()),
        'name': 'Boston Locations Fall 2025',
        'slug': 'boston-fall-2025',
        'description': 'Graduate training program for Boston office',
        'location_country': 'United States',
        'location_region': 'Massachusetts',
        'location_city': 'Boston',
        'location_address': '123 Main Street, Boston, MA 02101',
        'timezone': 'America/New_York',
        'start_date': datetime.now() + timedelta(days=30),
        'end_date': datetime.now() + timedelta(days=150),
        'duration_weeks': 17,
        'max_participants': 30,
        'current_participants': 0,
        'status': 'draft',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }


class TestSubProjectCreation:
    """Test creating new sub-projects"""

    def test_create_sub_project_success(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test successfully creating a new sub-project"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = sample_sub_project_data

        # Create sub-project
        result = sub_project_dao.create_sub_project(sample_sub_project_data)

        # Verify INSERT query was executed
        assert cursor.execute.called
        query = cursor.execute.call_args[0][0]
        assert 'INSERT INTO sub_projects' in query
        assert 'parent_project_id' in query
        assert 'location_country' in query

        # Verify result
        assert result['id'] == sample_sub_project_data['id']
        assert result['name'] == 'Boston Locations Fall 2025'
        assert result['location_city'] == 'Boston'

    def test_create_sub_project_with_duplicate_slug(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test creating sub-project with duplicate slug raises exception"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value

        # Simulate unique constraint violation
        from psycopg2 import IntegrityError
        cursor.execute.side_effect = IntegrityError("unique constraint violated")

        # Should raise DuplicateSubProjectException
        with pytest.raises(DuplicateSubProjectException):
            sub_project_dao.create_sub_project(sample_sub_project_data)

    def test_create_sub_project_validates_location(self, sub_project_dao, sample_sub_project_data):
        """Test that locations validation occurs during creation"""
        # Missing required locations fields
        invalid_data = sample_sub_project_data.copy()
        invalid_data['location_country'] = None

        with pytest.raises(InvalidLocationException):
            sub_project_dao.create_sub_project(invalid_data)

    def test_create_sub_project_validates_dates(self, sub_project_dao, sample_sub_project_data):
        """Test that date validation occurs (start_date < end_date)"""
        # Invalid date range (end before start)
        invalid_data = sample_sub_project_data.copy()
        invalid_data['start_date'] = datetime.now() + timedelta(days=100)
        invalid_data['end_date'] = datetime.now() + timedelta(days=50)

        with pytest.raises(InvalidDateRangeException):
            sub_project_dao.create_sub_project(invalid_data)

    def test_create_sub_project_auto_calculates_duration(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test that duration_weeks is auto-calculated if not provided"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = sample_sub_project_data

        # Remove duration from input
        data = sample_sub_project_data.copy()
        del data['duration_weeks']

        result = sub_project_dao.create_sub_project(data)

        # Verify duration was calculated (approximately 17 weeks for 120 days)
        assert result['duration_weeks'] in range(16, 18)


class TestSubProjectRetrieval:
    """Test retrieving sub-projects"""

    def test_get_sub_project_by_id_success(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test retrieving sub-project by ID"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = sample_sub_project_data

        result = sub_project_dao.get_sub_project_by_id(sample_sub_project_data['id'])

        # Verify SELECT query
        assert cursor.execute.called
        query = cursor.execute.call_args[0][0]
        assert 'SELECT' in query
        assert 'FROM sub_projects' in query
        assert 'WHERE id = %s' in query

        # Verify result
        assert result['id'] == sample_sub_project_data['id']
        assert result['name'] == 'Boston Locations Fall 2025'

    def test_get_sub_project_by_id_not_found(self, sub_project_dao, mock_db_connection):
        """Test retrieving non-existent sub-project raises exception"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None

        with pytest.raises(SubProjectNotFoundException):
            sub_project_dao.get_sub_project_by_id(str(uuid4()))

    def test_get_sub_projects_by_parent_project(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test retrieving all sub-projects for a parent project"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value

        # Mock 3 sub-projects
        cursor.fetchall.return_value = [
            {**sample_sub_project_data, 'name': 'Boston Locations'},
            {**sample_sub_project_data, 'name': 'London Locations', 'location_city': 'London'},
            {**sample_sub_project_data, 'name': 'Tokyo Locations', 'location_city': 'Tokyo'}
        ]

        parent_id = sample_sub_project_data['parent_project_id']
        results = sub_project_dao.get_sub_projects_by_parent(parent_id)

        # Verify query
        query = cursor.execute.call_args[0][0]
        assert 'WHERE parent_project_id = %s' in query

        # Verify results
        assert len(results) == 3
        assert results[0]['name'] == 'Boston Locations'
        assert results[1]['name'] == 'London Locations'
        assert results[2]['name'] == 'Tokyo Locations'

    def test_get_sub_projects_with_location_filter(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test filtering sub-projects by locations"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [sample_sub_project_data]

        filters = {
            'location_country': 'United States',
            'location_region': 'Massachusetts'
        }

        parent_id = sample_sub_project_data['parent_project_id']
        results = sub_project_dao.get_sub_projects_by_parent(parent_id, filters=filters)

        # Verify filtering query
        query = cursor.execute.call_args[0][0]
        assert 'location_country = %s' in query
        assert 'location_region = %s' in query

    def test_get_sub_projects_with_date_range_filter(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test filtering sub-projects by date range"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [sample_sub_project_data]

        filters = {
            'start_date_from': datetime.now(),
            'start_date_to': datetime.now() + timedelta(days=365)
        }

        parent_id = sample_sub_project_data['parent_project_id']
        results = sub_project_dao.get_sub_projects_by_parent(parent_id, filters=filters)

        # Verify date filtering query
        query = cursor.execute.call_args[0][0]
        assert 'start_date >=' in query or 'start_date BETWEEN' in query

    def test_get_sub_projects_with_status_filter(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test filtering sub-projects by status"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [sample_sub_project_data]

        filters = {'status': 'active'}

        parent_id = sample_sub_project_data['parent_project_id']
        results = sub_project_dao.get_sub_projects_by_parent(parent_id, filters=filters)

        # Verify status filtering
        query = cursor.execute.call_args[0][0]
        assert 'status = %s' in query


class TestSubProjectUpdate:
    """Test updating sub-projects"""

    def test_update_sub_project_success(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test successfully updating a sub-project"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        updated_data = {
            'name': 'Boston Locations Spring 2026',
            'max_participants': 35,
            'status': 'active'
        }

        result = sub_project_dao.update_sub_project(sample_sub_project_data['id'], updated_data)

        # Verify UPDATE query
        query = cursor.execute.call_args[0][0]
        assert 'UPDATE sub_projects' in query
        assert 'SET' in query
        assert 'WHERE id = %s' in query

        assert result is True

    def test_update_sub_project_not_found(self, sub_project_dao, mock_db_connection):
        """Test updating non-existent sub-project"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 0

        with pytest.raises(SubProjectNotFoundException):
            sub_project_dao.update_sub_project(str(uuid4()), {'name': 'New Name'})

    def test_update_sub_project_validates_dates(self, sub_project_dao, sample_sub_project_data):
        """Test that date validation occurs during update"""
        invalid_update = {
            'start_date': datetime.now() + timedelta(days=100),
            'end_date': datetime.now() + timedelta(days=50)
        }

        with pytest.raises(InvalidDateRangeException):
            sub_project_dao.update_sub_project(sample_sub_project_data['id'], invalid_update)


class TestSubProjectDeletion:
    """Test deleting sub-projects"""

    def test_delete_sub_project_success(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test successfully deleting a sub-project"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        result = sub_project_dao.delete_sub_project(sample_sub_project_data['id'])

        # Verify DELETE query
        query = cursor.execute.call_args[0][0]
        assert 'DELETE FROM sub_projects' in query
        assert 'WHERE id = %s' in query

        assert result is True

    def test_delete_sub_project_not_found(self, sub_project_dao, mock_db_connection):
        """Test deleting non-existent sub-project"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 0

        with pytest.raises(SubProjectNotFoundException):
            sub_project_dao.delete_sub_project(str(uuid4()))

    def test_delete_sub_project_cascades_to_tracks(self, sub_project_dao, mock_db_connection, sample_sub_project_data):
        """Test that deleting sub-project cascades to sub_project_tracks"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        # Mock fetching related tracks before deletion
        cursor.fetchall.return_value = [
            {'track_id': str(uuid4())},
            {'track_id': str(uuid4())}
        ]

        result = sub_project_dao.delete_sub_project(sample_sub_project_data['id'])

        # Verify cascade deletion was handled
        assert cursor.execute.call_count >= 2  # One for tracks, one for sub-project


class TestSubProjectTrackAssignment:
    """Test assigning tracks to sub-projects"""

    def test_assign_track_to_sub_project(self, sub_project_dao, mock_db_connection):
        """Test assigning a track to a sub-project"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {
            'id': str(uuid4()),
            'sub_project_id': str(uuid4()),
            'track_id': str(uuid4()),
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=45),
            'sequence_order': 1
        }

        assignment_data = {
            'sub_project_id': str(uuid4()),
            'track_id': str(uuid4()),
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=45),
            'primary_instructor_id': str(uuid4()),
            'sequence_order': 1
        }

        result = sub_project_dao.assign_track_to_sub_project(assignment_data)

        # Verify INSERT into sub_project_tracks
        query = cursor.execute.call_args[0][0]
        assert 'INSERT INTO sub_project_tracks' in query
        assert 'track_id' in query
        assert 'start_date' in query

    def test_assign_duplicate_track_fails(self, sub_project_dao, mock_db_connection):
        """Test assigning same track twice fails"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value

        from psycopg2 import IntegrityError
        cursor.execute.side_effect = IntegrityError("unique constraint")

        assignment_data = {
            'sub_project_id': str(uuid4()),
            'track_id': str(uuid4())
        }

        with pytest.raises(DuplicateSubProjectException):
            sub_project_dao.assign_track_to_sub_project(assignment_data)

    def test_get_tracks_for_sub_project(self, sub_project_dao, mock_db_connection):
        """Test retrieving all tracks assigned to a sub-project"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            {
                'track_id': str(uuid4()),
                'track_name': 'Application Development',
                'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(days=45),
                'sequence_order': 1
            },
            {
                'track_id': str(uuid4()),
                'track_name': 'DevOps Engineering',
                'start_date': datetime.now() + timedelta(days=46),
                'end_date': datetime.now() + timedelta(days=90),
                'sequence_order': 2
            }
        ]

        sub_project_id = str(uuid4())
        results = sub_project_dao.get_tracks_for_sub_project(sub_project_id)

        # Verify JOIN query
        query = cursor.execute.call_args[0][0]
        assert 'JOIN tracks' in query
        assert 'sub_project_tracks' in query

        # Verify results
        assert len(results) == 2
        assert results[0]['sequence_order'] == 1
        assert results[1]['sequence_order'] == 2


class TestSubProjectCapacityManagement:
    """Test participant capacity tracking"""

    def test_increment_participant_count(self, sub_project_dao, mock_db_connection):
        """Test incrementing current_participants when student enrolls"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {'current_participants': 5, 'max_participants': 30}

        sub_project_id = str(uuid4())
        result = sub_project_dao.increment_participant_count(sub_project_id)

        # Verify UPDATE with increment
        query = cursor.execute.call_args[0][0]
        assert 'UPDATE sub_projects' in query
        assert 'current_participants = current_participants + 1' in query

        assert result['current_participants'] == 5

    def test_increment_participant_count_at_capacity_fails(self, sub_project_dao, mock_db_connection):
        """Test cannot enroll when at max capacity"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {'current_participants': 30, 'max_participants': 30}

        from course_management.infrastructure.exceptions import SubProjectCapacityException

        with pytest.raises(SubProjectCapacityException):
            sub_project_dao.increment_participant_count(str(uuid4()))

    def test_decrement_participant_count(self, sub_project_dao, mock_db_connection):
        """Test decrementing when student unenrolls"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        result = sub_project_dao.decrement_participant_count(str(uuid4()))

        # Verify UPDATE with decrement
        query = cursor.execute.call_args[0][0]
        assert 'current_participants = current_participants - 1' in query


class TestSubProjectStatusTransitions:
    """Test status lifecycle management"""

    def test_activate_sub_project(self, sub_project_dao, mock_db_connection):
        """Test transitioning from draft to active"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        sub_project_id = str(uuid4())
        result = sub_project_dao.update_status(sub_project_id, 'active')

        query = cursor.execute.call_args[0][0]
        assert "status = %s" in query
        assert result is True

    def test_complete_sub_project(self, sub_project_dao, mock_db_connection):
        """Test marking sub-project as completed"""
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1

        result = sub_project_dao.update_status(str(uuid4()), 'completed')
        assert result is True

    def test_invalid_status_transition_fails(self, sub_project_dao):
        """Test invalid status value raises exception"""
        with pytest.raises(ValueError):
            sub_project_dao.update_status(str(uuid4()), 'invalid_status')


# ==============================================================================
# TEST EXECUTION
# ==============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
