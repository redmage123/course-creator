"""
Repository interface for meeting room management
Follows Interface Segregation Principle
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.meeting_room import MeetingRoom, MeetingRoomUsage, MeetingRoomInvitation, MeetingPlatform, RoomType


class IMeetingRoomRepository(ABC):
    """Interface for meeting room data access"""

    @abstractmethod
    async def create_room(self, room: MeetingRoom) -> MeetingRoom:
        """Create new meeting room"""
        pass

    @abstractmethod
    async def get_room_by_id(self, room_id: UUID) -> Optional[MeetingRoom]:
        """Get room by ID"""
        pass

    @abstractmethod
    async def get_organization_rooms(self, organization_id: UUID, platform: Optional[MeetingPlatform] = None) -> List[MeetingRoom]:
        """Get all rooms for organization"""
        pass

    @abstractmethod
    async def get_project_rooms(self, project_id: UUID, platform: Optional[MeetingPlatform] = None) -> List[MeetingRoom]:
        """Get all rooms for project"""
        pass

    @abstractmethod
    async def get_track_rooms(self, track_id: UUID, platform: Optional[MeetingPlatform] = None) -> List[MeetingRoom]:
        """Get all rooms for track"""
        pass

    @abstractmethod
    async def get_instructor_rooms(self, instructor_id: UUID, platform: Optional[MeetingPlatform] = None) -> List[MeetingRoom]:
        """Get all rooms for instructor"""
        pass

    @abstractmethod
    async def get_rooms_by_type(self, room_type: RoomType, organization_id: UUID) -> List[MeetingRoom]:
        """Get rooms by type within organization"""
        pass

    @abstractmethod
    async def update_room(self, room: MeetingRoom) -> MeetingRoom:
        """Update existing room"""
        pass

    @abstractmethod
    async def delete_room(self, room_id: UUID) -> bool:
        """Delete room"""
        pass

    @abstractmethod
    async def deactivate_room(self, room_id: UUID) -> bool:
        """Deactivate room"""
        pass

    @abstractmethod
    async def get_room_by_external_id(self, external_room_id: str, platform: MeetingPlatform) -> Optional[MeetingRoom]:
        """Get room by external platform ID"""
        pass

    @abstractmethod
    async def search_rooms(self, organization_id: UUID, query: str) -> List[MeetingRoom]:
        """Search rooms by name or description"""
        pass


class IMeetingRoomUsageRepository(ABC):
    """Interface for meeting room usage tracking"""

    @abstractmethod
    async def record_join(self, room_id: UUID, user_id: UUID) -> MeetingRoomUsage:
        """Record user joining room"""
        pass

    @abstractmethod
    async def record_leave(self, usage_id: UUID) -> MeetingRoomUsage:
        """Record user leaving room"""
        pass

    @abstractmethod
    async def get_room_usage(self, room_id: UUID, limit: int = 100) -> List[MeetingRoomUsage]:
        """Get usage history for room"""
        pass

    @abstractmethod
    async def get_user_usage(self, user_id: UUID, limit: int = 100) -> List[MeetingRoomUsage]:
        """Get usage history for user"""
        pass

    @abstractmethod
    async def get_active_sessions(self, room_id: UUID) -> List[MeetingRoomUsage]:
        """Get currently active sessions in room"""
        pass

    @abstractmethod
    async def get_usage_statistics(self, organization_id: UUID, days: int = 30) -> dict:
        """Get usage statistics for organization"""
        pass


class IMeetingRoomInvitationRepository(ABC):
    """Interface for meeting room invitation management"""

    @abstractmethod
    async def create_invitation(self, invitation: MeetingRoomInvitation) -> MeetingRoomInvitation:
        """Create new room invitation"""
        pass

    @abstractmethod
    async def get_invitation_by_id(self, invitation_id: UUID) -> Optional[MeetingRoomInvitation]:
        """Get invitation by ID"""
        pass

    @abstractmethod
    async def get_room_invitations(self, room_id: UUID) -> List[MeetingRoomInvitation]:
        """Get all invitations for room"""
        pass

    @abstractmethod
    async def get_user_invitations(self, user_id: UUID) -> List[MeetingRoomInvitation]:
        """Get all invitations for user"""
        pass

    @abstractmethod
    async def get_pending_invitations(self, room_id: UUID) -> List[MeetingRoomInvitation]:
        """Get pending invitations for room"""
        pass

    @abstractmethod
    async def accept_invitation(self, invitation_id: UUID) -> bool:
        """Accept invitation"""
        pass

    @abstractmethod
    async def expire_invitation(self, invitation_id: UUID) -> bool:
        """Expire invitation"""
        pass

    @abstractmethod
    async def delete_invitation(self, invitation_id: UUID) -> bool:
        """Delete invitation"""
        pass

    @abstractmethod
    async def cleanup_expired_invitations(self) -> int:
        """Clean up expired invitations"""
        pass