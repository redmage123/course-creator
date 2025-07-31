"""
Track Repository Interface
Single Responsibility: Abstract data access contract for tracks
Interface Segregation: Only track-specific operations
Dependency Inversion: Abstract interface for concrete implementations
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.entities.track import Track, TrackStatus, TrackType


class ITrackRepository(ABC):
    """
    Abstract repository interface for track data access
    """

    @abstractmethod
    async def create(self, track: Track) -> Track:
        """Create a new track"""
        pass

    @abstractmethod
    async def get_by_id(self, track_id: UUID) -> Optional[Track]:
        """Get track by ID"""
        pass

    @abstractmethod
    async def get_by_project_and_slug(self, project_id: UUID, slug: str) -> Optional[Track]:
        """Get track by project ID and slug"""
        pass

    @abstractmethod
    async def update(self, track: Track) -> Track:
        """Update track"""
        pass

    @abstractmethod
    async def delete(self, track_id: UUID) -> bool:
        """Delete track"""
        pass

    @abstractmethod
    async def exists_by_project_and_slug(self, project_id: UUID, slug: str) -> bool:
        """Check if track exists by project ID and slug"""
        pass

    @abstractmethod
    async def get_by_project(self, project_id: UUID, limit: int = 100, offset: int = 0) -> List[Track]:
        """Get tracks by project"""
        pass

    @abstractmethod
    async def get_by_status(self, status: TrackStatus, limit: int = 100, offset: int = 0) -> List[Track]:
        """Get tracks by status"""
        pass

    @abstractmethod
    async def get_by_project_and_status(self, project_id: UUID, status: TrackStatus) -> List[Track]:
        """Get tracks by project and status"""
        pass

    @abstractmethod
    async def get_by_track_type(self, track_type: TrackType) -> List[Track]:
        """Get tracks by type"""
        pass

    @abstractmethod
    async def get_by_target_audience(self, target_audience: str, project_id: UUID = None) -> List[Track]:
        """Get tracks by target audience"""
        pass

    @abstractmethod
    async def get_by_difficulty_level(self, difficulty_level: str, project_id: UUID = None) -> List[Track]:
        """Get tracks by difficulty level"""
        pass

    @abstractmethod
    async def search_by_project(self, project_id: UUID, query: str, limit: int = 50) -> List[Track]:
        """Search tracks within project"""
        pass

    @abstractmethod
    async def get_by_creator(self, creator_id: UUID) -> List[Track]:
        """Get tracks created by user"""
        pass

    @abstractmethod
    async def get_active_tracks_with_auto_enroll(self, project_id: UUID) -> List[Track]:
        """Get active tracks with auto-enrollment enabled"""
        pass

    @abstractmethod
    async def count_by_project(self, project_id: UUID) -> int:
        """Count tracks in project"""
        pass

    @abstractmethod
    async def count_by_status(self, status: TrackStatus) -> int:
        """Count tracks by status"""
        pass

    @abstractmethod
    async def get_ordered_tracks_by_project(self, project_id: UUID) -> List[Track]:
        """Get tracks ordered by sequence_order"""
        pass