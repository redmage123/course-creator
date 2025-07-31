"""
Unit Tests for Track Repository
Tests data access layer with mocked database operations
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4
import json
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../services/organization-management'))

from domain.entities.track import Track, TrackStatus, TrackType
from infrastructure.repositories.postgresql_track_repository import PostgreSQLTrackRepository


class TestPostgreSQLTrackRepository:
    """Test PostgreSQL Track Repository implementation"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database connection pool"""
        pool = MagicMock()
        connection = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = connection
        pool.acquire.return_value.__aexit__.return_value = None
        return pool, connection
    
    @pytest.fixture
    def repository(self, mock_pool):
        """Create repository with mocked pool"""
        pool, _ = mock_pool
        return PostgreSQLTrackRepository(pool)
    
    @pytest.fixture
    def sample_track(self):
        """Sample track for testing"""
        return Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track",
            description="Test track description",
            track_type=TrackType.SEQUENTIAL,
            target_audience=["Developer", "Analyst"],
            prerequisites=["Basic Programming"],
            duration_weeks=12,
            max_enrolled=50,
            learning_objectives=["Learn Python", "Master Git"],
            skills_taught=["Python", "Git"],
            difficulty_level="intermediate",
            sequence_order=1,
            auto_enroll_enabled=True,
            status=TrackStatus.DRAFT,
            settings={"notifications": True},
            created_by=uuid4()
        )
    
    @pytest.fixture
    def sample_db_row(self, sample_track):
        """Sample database row for testing"""
        return {
            'id': sample_track.id,
            'project_id': sample_track.project_id,
            'name': sample_track.name,
            'slug': sample_track.slug,
            'description': sample_track.description,
            'track_type': sample_track.track_type.value,
            'target_audience': sample_track.target_audience,
            'prerequisites': sample_track.prerequisites,
            'duration_weeks': sample_track.duration_weeks,
            'max_enrolled': sample_track.max_enrolled,
            'learning_objectives': sample_track.learning_objectives,
            'skills_taught': sample_track.skills_taught,
            'difficulty_level': sample_track.difficulty_level,
            'sequence_order': sample_track.sequence_order,
            'auto_enroll_enabled': sample_track.auto_enroll_enabled,
            'status': sample_track.status.value,
            'settings': json.dumps(sample_track.settings),
            'created_by': sample_track.created_by,
            'created_at': sample_track.created_at,
            'updated_at': sample_track.updated_at
        }
    
    @pytest.mark.asyncio
    async def test_create_track(self, repository, mock_pool, sample_track, sample_db_row):
        """Test track creation"""
        pool, connection = mock_pool
        connection.fetchrow.return_value = sample_db_row
        
        result = await repository.create(sample_track)
        
        # Verify database call
        connection.fetchrow.assert_called_once()
        call_args = connection.fetchrow.call_args[0]
        assert "INSERT INTO tracks" in call_args[0]
        
        # Verify result
        assert result.id == sample_track.id
        assert result.name == sample_track.name
        assert result.slug == sample_track.slug
        assert result.project_id == sample_track.project_id
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, repository, mock_pool, sample_db_row):
        """Test get track by ID"""
        pool, connection = mock_pool
        connection.fetchrow.return_value = sample_db_row
        
        track_id = sample_db_row['id']
        result = await repository.get_by_id(track_id)
        
        # Verify database call
        connection.fetchrow.assert_called_once_with(
            "SELECT * FROM tracks WHERE id = $1",
            track_id
        )
        
        # Verify result
        assert result.id == track_id
        assert result.name == sample_db_row['name']
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_pool):
        """Test get track by ID when not found"""
        pool, connection = mock_pool
        connection.fetchrow.return_value = None
        
        track_id = uuid4()
        result = await repository.get_by_id(track_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_project_and_slug(self, repository, mock_pool, sample_db_row):
        """Test get track by project and slug"""
        pool, connection = mock_pool
        connection.fetchrow.return_value = sample_db_row
        
        project_id = sample_db_row['project_id']
        slug = sample_db_row['slug']
        result = await repository.get_by_project_and_slug(project_id, slug)
        
        # Verify database call
        connection.fetchrow.assert_called_once_with(
            "SELECT * FROM tracks WHERE project_id = $1 AND slug = $2",
            project_id, slug
        )
        
        # Verify result
        assert result.project_id == project_id
        assert result.slug == slug
    
    @pytest.mark.asyncio
    async def test_update_track(self, repository, mock_pool, sample_track, sample_db_row):
        """Test track update"""
        pool, connection = mock_pool
        updated_row = sample_db_row.copy()
        updated_row['name'] = "Updated Track Name"
        connection.fetchrow.return_value = updated_row
        
        sample_track.name = "Updated Track Name"
        result = await repository.update(sample_track)
        
        # Verify database call
        connection.fetchrow.assert_called_once()
        call_args = connection.fetchrow.call_args[0]
        assert "UPDATE tracks SET" in call_args[0]
        
        # Verify result
        assert result.name == "Updated Track Name"
    
    @pytest.mark.asyncio
    async def test_delete_track(self, repository, mock_pool):
        """Test track deletion"""
        pool, connection = mock_pool
        connection.execute.return_value = "DELETE 1"
        
        track_id = uuid4()
        result = await repository.delete(track_id)
        
        # Verify database call
        connection.execute.assert_called_once_with(
            "DELETE FROM tracks WHERE id = $1",
            track_id
        )
        
        # Verify result
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_track_not_found(self, repository, mock_pool):
        """Test track deletion when track not found"""
        pool, connection = mock_pool
        connection.execute.return_value = "DELETE 0"
        
        track_id = uuid4()
        result = await repository.delete(track_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_exists_by_project_and_slug(self, repository, mock_pool):
        """Test track existence check"""
        pool, connection = mock_pool
        connection.fetchval.return_value = True
        
        project_id = uuid4()
        slug = "test-slug"
        result = await repository.exists_by_project_and_slug(project_id, slug)
        
        # Verify database call
        connection.fetchval.assert_called_once_with(
            "SELECT EXISTS(SELECT 1 FROM tracks WHERE project_id = $1 AND slug = $2)",
            project_id, slug
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_by_project(self, repository, mock_pool, sample_db_row):
        """Test get tracks by project"""
        pool, connection = mock_pool
        connection.fetch.return_value = [sample_db_row, sample_db_row.copy()]
        
        project_id = uuid4()
        result = await repository.get_by_project(project_id, limit=10, offset=0)
        
        # Verify database call
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "WHERE project_id = $1" in call_args[0]
        assert "ORDER BY sequence_order ASC, created_at DESC" in call_args[0]
        
        # Verify result
        assert len(result) == 2
        assert all(track.project_id == sample_db_row['project_id'] for track in result)
    
    @pytest.mark.asyncio
    async def test_get_by_status(self, repository, mock_pool, sample_db_row):
        """Test get tracks by status"""
        pool, connection = mock_pool
        connection.fetch.return_value = [sample_db_row]
        
        status = TrackStatus.ACTIVE
        result = await repository.get_by_status(status)
        
        # Verify database call
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "WHERE status = $1" in call_args[0]
        
        # Verify result
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_by_project_and_status(self, repository, mock_pool, sample_db_row):
        """Test get tracks by project and status"""
        pool, connection = mock_pool
        connection.fetch.return_value = [sample_db_row]
        
        project_id = uuid4()
        status = TrackStatus.ACTIVE
        result = await repository.get_by_project_and_status(project_id, status)
        
        # Verify database call
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "WHERE project_id = $1 AND status = $2" in call_args[0]
        
        # Verify result
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_by_target_audience(self, repository, mock_pool, sample_db_row):
        """Test get tracks by target audience"""
        pool, connection = mock_pool
        connection.fetch.return_value = [sample_db_row]
        
        target_audience = "Developer"
        result = await repository.get_by_target_audience(target_audience)
        
        # Verify database call
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "$1 = ANY(target_audience)" in call_args[0]
        
        # Verify result
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_by_difficulty_level(self, repository, mock_pool, sample_db_row):
        """Test get tracks by difficulty level"""
        pool, connection = mock_pool
        connection.fetch.return_value = [sample_db_row]
        
        difficulty_level = "intermediate"
        result = await repository.get_by_difficulty_level(difficulty_level)
        
        # Verify database call
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "WHERE difficulty_level = $1" in call_args[0]
        
        # Verify result
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_search_by_project(self, repository, mock_pool, sample_db_row):
        """Test search tracks within project"""
        pool, connection = mock_pool
        connection.fetch.return_value = [sample_db_row]
        
        project_id = uuid4()
        query = "python"
        result = await repository.search_by_project(project_id, query)
        
        # Verify database call
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "WHERE project_id = $1" in call_args[0]
        assert "name ILIKE $2 OR description ILIKE $2" in call_args[0]
        
        # Verify result
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_active_tracks_with_auto_enroll(self, repository, mock_pool, sample_db_row):
        """Test get active tracks with auto-enrollment enabled"""
        pool, connection = mock_pool
        connection.fetch.return_value = [sample_db_row]
        
        project_id = uuid4()
        result = await repository.get_active_tracks_with_auto_enroll(project_id)
        
        # Verify database call
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "WHERE project_id = $1 AND status = 'active' AND auto_enroll_enabled = true" in call_args[0]
        
        # Verify result
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_count_by_project(self, repository, mock_pool):
        """Test count tracks by project"""
        pool, connection = mock_pool
        connection.fetchval.return_value = 5
        
        project_id = uuid4()
        result = await repository.count_by_project(project_id)
        
        # Verify database call
        connection.fetchval.assert_called_once_with(
            "SELECT COUNT(*) FROM tracks WHERE project_id = $1",
            project_id
        )
        
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_get_ordered_tracks_by_project(self, repository, mock_pool, sample_db_row):
        """Test get tracks ordered by sequence"""
        pool, connection = mock_pool
        connection.fetch.return_value = [sample_db_row, sample_db_row.copy()]
        
        project_id = uuid4()
        result = await repository.get_ordered_tracks_by_project(project_id)
        
        # Verify database call
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "ORDER BY sequence_order ASC, name ASC" in call_args[0]
        
        # Verify result
        assert len(result) == 2
    
    def test_row_to_track_conversion(self, repository, sample_db_row):
        """Test database row to Track entity conversion"""
        track = repository._row_to_track(sample_db_row)
        
        assert track.id == sample_db_row['id']
        assert track.project_id == sample_db_row['project_id']
        assert track.name == sample_db_row['name']
        assert track.slug == sample_db_row['slug']
        assert track.track_type == TrackType(sample_db_row['track_type'])
        assert track.status == TrackStatus(sample_db_row['status'])
        assert track.target_audience == sample_db_row['target_audience']
        assert track.prerequisites == sample_db_row['prerequisites']
        assert track.settings == json.loads(sample_db_row['settings'])
    
    def test_row_to_track_with_none(self, repository):
        """Test conversion with None row"""
        result = repository._row_to_track(None)
        assert result is None
    
    def test_row_to_track_with_null_arrays(self, repository, sample_db_row):
        """Test conversion with null array fields"""
        sample_db_row['target_audience'] = None
        sample_db_row['prerequisites'] = None
        sample_db_row['learning_objectives'] = None
        sample_db_row['skills_taught'] = None
        sample_db_row['settings'] = None
        
        track = repository._row_to_track(sample_db_row)
        
        assert track.target_audience == []
        assert track.prerequisites == []
        assert track.learning_objectives == []
        assert track.skills_taught == []
        assert track.settings == {}


if __name__ == "__main__":
    pytest.main([__file__])