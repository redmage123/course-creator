"""
Unit Tests for Track Service
Tests business logic and service layer operations
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../services/organization-management'))

from domain.entities.track import Track, TrackStatus, TrackType
from application.services.track_service import TrackService


class TestTrackService:
    """Test Track Service business logic"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock track repository"""
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_repository):
        """Create service with mocked repository"""
        return TrackService(mock_repository)
    
    @pytest.fixture
    def sample_track(self):
        """Sample track for testing"""
        return Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track",
            description="Test description",
            target_audience=["Developer"],
            skills_taught=["Python", "Git"],
            duration_weeks=12,
            difficulty_level="intermediate"
        )
    
    @pytest.mark.asyncio
    async def test_create_track_success(self, service, mock_repository):
        """Test successful track creation"""
        project_id = uuid4()
        created_by = uuid4()
        
        # Mock repository responses
        mock_repository.exists_by_project_and_slug.return_value = False
        mock_repository.get_by_project.return_value = []  # No existing tracks
        mock_repository.create.return_value = Track(
            project_id=project_id,
            name="New Track",
            slug="new-track",
            created_by=created_by
        )
        
        result = await service.create_track(
            project_id=project_id,
            name="New Track",
            slug="new-track",
            description="New track description",
            target_audience=["Developer", "Analyst"],
            duration_weeks=16,
            created_by=created_by
        )
        
        # Verify repository calls
        mock_repository.exists_by_project_and_slug.assert_called_once_with(project_id, "new-track")
        mock_repository.get_by_project.assert_called_once_with(project_id)
        mock_repository.create.assert_called_once()
        
        # Verify result
        assert result.name == "New Track"
        assert result.slug == "new-track"
        assert result.project_id == project_id
    
    @pytest.mark.asyncio
    async def test_create_track_duplicate_slug(self, service, mock_repository):
        """Test track creation with duplicate slug"""
        project_id = uuid4()
        
        # Mock repository to return True for slug existence
        mock_repository.exists_by_project_and_slug.return_value = True
        
        with pytest.raises(ValueError, match="Track with slug 'existing-slug' already exists"):
            await service.create_track(
                project_id=project_id,
                name="New Track",
                slug="existing-slug"
            )
        
        # Verify no create call was made
        mock_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_track_sequence_order(self, service, mock_repository):
        """Test track creation assigns correct sequence order"""
        project_id = uuid4()
        
        # Mock existing tracks
        existing_tracks = [
            Track(project_id=project_id, name="Track 1", slug="track-1"),
            Track(project_id=project_id, name="Track 2", slug="track-2")
        ]
        
        mock_repository.exists_by_project_and_slug.return_value = False
        mock_repository.get_by_project.return_value = existing_tracks
        mock_repository.create.return_value = Track(
            project_id=project_id,
            name="Track 3",
            slug="track-3",
            sequence_order=3
        )
        
        await service.create_track(
            project_id=project_id,
            name="Track 3",
            slug="track-3"
        )
        
        # Verify create was called with correct sequence order
        create_call = mock_repository.create.call_args[0][0]
        assert create_call.sequence_order == 3  # len(existing_tracks) + 1
    
    @pytest.mark.asyncio
    async def test_get_track(self, service, mock_repository, sample_track):
        """Test get track by ID"""
        track_id = uuid4()
        mock_repository.get_by_id.return_value = sample_track
        
        result = await service.get_track(track_id)
        
        mock_repository.get_by_id.assert_called_once_with(track_id)
        assert result == sample_track
    
    @pytest.mark.asyncio
    async def test_get_track_not_found(self, service, mock_repository):
        """Test get track when not found"""
        track_id = uuid4()
        mock_repository.get_by_id.return_value = None
        
        result = await service.get_track(track_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_track_success(self, service, mock_repository, sample_track):
        """Test successful track update"""
        track_id = uuid4()
        sample_track.id = track_id
        
        mock_repository.get_by_id.return_value = sample_track
        mock_repository.update.return_value = sample_track
        
        result = await service.update_track(
            track_id=track_id,
            name="Updated Track",
            description="Updated description",
            duration_weeks=16
        )
        
        mock_repository.get_by_id.assert_called_once_with(track_id)
        mock_repository.update.assert_called_once_with(sample_track)
        
        # Verify track was updated
        assert sample_track.name == "Updated Track"
        assert sample_track.description == "Updated description"
        assert sample_track.duration_weeks == 16
    
    @pytest.mark.asyncio
    async def test_update_track_not_found(self, service, mock_repository):
        """Test update track when not found"""
        track_id = uuid4()
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match=f"Track with ID {track_id} not found"):
            await service.update_track(track_id=track_id, name="Updated Track")
    
    @pytest.mark.asyncio
    async def test_activate_track_success(self, service, mock_repository, sample_track):
        """Test successful track activation"""
        track_id = uuid4()
        sample_track.id = track_id
        sample_track.status = TrackStatus.DRAFT
        
        mock_repository.get_by_id.return_value = sample_track
        mock_repository.update.return_value = sample_track
        
        result = await service.activate_track(track_id)
        
        mock_repository.get_by_id.assert_called_once_with(track_id)
        mock_repository.update.assert_called_once_with(sample_track)
        
        # Verify track was activated
        assert sample_track.status == TrackStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_activate_track_invalid_status(self, service, mock_repository, sample_track):
        """Test activate track with invalid status"""
        track_id = uuid4()
        sample_track.id = track_id
        sample_track.status = TrackStatus.ARCHIVED  # Cannot activate archived track
        
        mock_repository.get_by_id.return_value = sample_track
        
        with pytest.raises(ValueError, match="Track cannot be activated"):
            await service.activate_track(track_id)
    
    @pytest.mark.asyncio
    async def test_archive_track(self, service, mock_repository, sample_track):
        """Test track archival"""
        track_id = uuid4()
        sample_track.id = track_id
        
        mock_repository.get_by_id.return_value = sample_track
        mock_repository.update.return_value = sample_track
        
        result = await service.archive_track(track_id)
        
        # Verify track was archived
        assert sample_track.status == TrackStatus.ARCHIVED
    
    @pytest.mark.asyncio
    async def test_delete_track_success(self, service, mock_repository, sample_track):
        """Test successful track deletion"""
        track_id = uuid4()
        sample_track.id = track_id
        
        mock_repository.get_by_id.return_value = sample_track
        mock_repository.delete.return_value = True
        
        result = await service.delete_track(track_id)
        
        mock_repository.delete.assert_called_once_with(track_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_track_not_found(self, service, mock_repository):
        """Test delete track when not found"""
        track_id = uuid4()
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match=f"Track with ID {track_id} not found"):
            await service.delete_track(track_id)
    
    @pytest.mark.asyncio
    async def test_get_tracks_by_project(self, service, mock_repository, sample_track):
        """Test get tracks by project"""
        project_id = uuid4()
        tracks = [sample_track]
        
        mock_repository.get_by_project.return_value = tracks
        
        result = await service.get_tracks_by_project(project_id)
        
        mock_repository.get_by_project.assert_called_once_with(project_id)
        assert result == tracks
    
    @pytest.mark.asyncio
    async def test_get_tracks_by_project_with_status(self, service, mock_repository, sample_track):
        """Test get tracks by project with status filter"""
        project_id = uuid4()
        status = TrackStatus.ACTIVE
        tracks = [sample_track]
        
        mock_repository.get_by_project_and_status.return_value = tracks
        
        result = await service.get_tracks_by_project(project_id, status=status)
        
        mock_repository.get_by_project_and_status.assert_called_once_with(project_id, status)
        assert result == tracks
    
    @pytest.mark.asyncio
    async def test_get_tracks_for_auto_enrollment(self, service, mock_repository, sample_track):
        """Test get tracks eligible for auto-enrollment"""
        project_id = uuid4()
        tracks = [sample_track]
        
        mock_repository.get_active_tracks_with_auto_enroll.return_value = tracks
        
        result = await service.get_tracks_for_auto_enrollment(project_id)
        
        mock_repository.get_active_tracks_with_auto_enroll.assert_called_once_with(project_id)
        assert result == tracks
    
    @pytest.mark.asyncio
    async def test_get_tracks_by_target_audience(self, service, mock_repository, sample_track):
        """Test get tracks by target audience"""
        target_audience = "Developer"
        project_id = uuid4()
        tracks = [sample_track]
        
        mock_repository.get_by_target_audience.return_value = tracks
        
        result = await service.get_tracks_by_target_audience(target_audience, project_id)
        
        mock_repository.get_by_target_audience.assert_called_once_with(target_audience, project_id)
        assert result == tracks
    
    @pytest.mark.asyncio
    async def test_search_tracks(self, service, mock_repository, sample_track):
        """Test search tracks within project"""
        project_id = uuid4()
        query = "python"
        tracks = [sample_track]
        
        mock_repository.search_by_project.return_value = tracks
        
        result = await service.search_tracks(project_id, query)
        
        mock_repository.search_by_project.assert_called_once_with(project_id, query)
        assert result == tracks
    
    @pytest.mark.asyncio
    async def test_reorder_tracks(self, service, mock_repository):
        """Test reorder tracks within project"""
        project_id = uuid4()
        track1_id = uuid4()
        track2_id = uuid4()
        
        track1 = Track(project_id=project_id, name="Track 1", slug="track-1")
        track1.id = track1_id
        track2 = Track(project_id=project_id, name="Track 2", slug="track-2")
        track2.id = track2_id
        
        track_orders = [
            {'track_id': track1_id, 'sequence_order': 2},
            {'track_id': track2_id, 'sequence_order': 1}
        ]
        
        mock_repository.get_by_id.side_effect = [track1, track2]
        mock_repository.update.side_effect = [track1, track2]
        
        result = await service.reorder_tracks(project_id, track_orders)
        
        # Verify both tracks were updated
        assert len(result) == 2
        assert track1.sequence_order == 2
        assert track2.sequence_order == 1
    
    @pytest.mark.asyncio
    async def test_get_track_statistics(self, service, mock_repository, sample_track):
        """Test get track statistics"""
        track_id = uuid4()
        sample_track.id = track_id
        
        mock_repository.get_by_id.return_value = sample_track
        
        result = await service.get_track_statistics(track_id)
        
        # Verify statistics structure
        assert result['id'] == str(track_id)
        assert result['name'] == sample_track.name
        assert result['slug'] == sample_track.slug
        assert result['status'] == sample_track.status.value
        assert result['track_type'] == sample_track.track_type.value
        assert result['difficulty_level'] == sample_track.difficulty_level
        assert 'target_audience' in result
        assert 'skills_taught' in result
        assert 'estimated_completion' in result
    
    @pytest.mark.asyncio
    async def test_validate_track_prerequisites(self, service, mock_repository, sample_track):
        """Test validate track prerequisites"""
        track_id = uuid4()
        sample_track.id = track_id
        sample_track.prerequisites = ["Basic Programming", "Git Knowledge"]
        
        mock_repository.get_by_id.return_value = sample_track
        
        # Test student with all prerequisites
        student_background = ["Basic Programming", "Git Knowledge", "Python"]
        result = await service.validate_track_prerequisites(track_id, student_background)
        
        assert result['meets_requirements'] is True
        assert result['missing_prerequisites'] == []
        assert result['required_prerequisites'] == sample_track.prerequisites
        
        # Test student missing prerequisites
        student_background = ["Python"]
        result = await service.validate_track_prerequisites(track_id, student_background)
        
        assert result['meets_requirements'] is False
        assert "Basic Programming" in result['missing_prerequisites']
        assert "Git Knowledge" in result['missing_prerequisites']
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self, service, mock_repository):
        """Test service error handling and logging"""
        track_id = uuid4()
        
        # Mock repository to raise exception
        mock_repository.get_by_id.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await service.get_track(track_id)
    
    @pytest.mark.asyncio
    async def test_create_track_with_invalid_data(self, service, mock_repository):
        """Test create track with invalid data"""
        project_id = uuid4()
        
        mock_repository.exists_by_project_and_slug.return_value = False
        mock_repository.get_by_project.return_value = []
        
        # Track with invalid data (empty name will make is_valid() return False)
        with pytest.raises(ValueError, match="Invalid track data"):
            await service.create_track(
                project_id=project_id,
                name="",  # Invalid empty name
                slug="test-track"
            )
    
    @pytest.mark.asyncio
    async def test_update_track_with_invalid_data(self, service, mock_repository, sample_track):
        """Test update track with invalid data"""
        track_id = uuid4()
        sample_track.id = track_id
        
        mock_repository.get_by_id.return_value = sample_track
        
        # Update with invalid data
        with pytest.raises(ValueError, match="Invalid track data"):
            await service.update_track(
                track_id=track_id,
                name="",  # Invalid empty name
            )


if __name__ == "__main__":
    pytest.main([__file__])