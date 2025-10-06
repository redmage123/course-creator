"""
Meeting Room Management Service
Handles MS Teams and Zoom integration for meeting rooms
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from organization_management.domain.entities.enhanced_role import EnhancedRole, Permission
from organization_management.domain.entities.meeting_room import MeetingPlatform, MeetingRoom, RoomType
from data_access.organization_dao import OrganizationManagementDAO
from organization_management.infrastructure.integrations.teams_integration import TeamsCredentials, TeamsIntegrationService
from organization_management.infrastructure.integrations.zoom_integration import ZoomCredentials, ZoomIntegrationService


class MeetingRoomService:
    """Service for meeting room management with platform integrations"""

    def __init__(
        self,
        organization_dao: OrganizationManagementDAO,
        teams_credentials: Optional[TeamsCredentials] = None,
        zoom_credentials: Optional[ZoomCredentials] = None
    ):
        self._organization_dao = organization_dao
        self._teams_credentials = teams_credentials
        self._zoom_credentials = zoom_credentials
        self._logger = logging.getLogger(__name__)

    async def create_meeting_room(
        self,
        organization_id: UUID,
        name: str,
        platform: MeetingPlatform,
        room_type: RoomType,
        created_by: UUID,
        project_id: Optional[UUID] = None,
        track_id: Optional[UUID] = None,
        instructor_id: Optional[UUID] = None,
        settings: Optional[Dict] = None
    ) -> MeetingRoom:
        """Create new meeting room with platform integration"""
        try:
            # Create room entity
            room = MeetingRoom(
                name=name,
                platform=platform,
                room_type=room_type,
                organization_id=organization_id,
                project_id=project_id,
                track_id=track_id,
                instructor_id=instructor_id,
                settings=settings or {},
                created_by=created_by
            )

            if not room.is_valid():
                raise ValueError("Invalid room configuration")

            # Create room on platform
            platform_data = {}
            if platform == MeetingPlatform.TEAMS:
                platform_data = await self._create_teams_room(room)
            elif platform == MeetingPlatform.ZOOM:
                platform_data = await self._create_zoom_room(room)

            # Update room with platform data
            if platform_data:
                room.external_room_id = platform_data.get("external_room_id")
                room.join_url = platform_data.get("join_url")
                room.host_url = platform_data.get("host_url")
                room.meeting_id = platform_data.get("meeting_id")
                room.passcode = platform_data.get("passcode")

            # Save to database
            created_room = await self._organization_dao.create_room(room)

            self._logger.info(f"Created {platform.value} meeting room: {created_room.id}")
            return created_room

        except Exception as e:
            self._logger.error(f"Failed to create meeting room: {e}")
            raise

    async def _create_teams_room(self, room: MeetingRoom) -> Dict:
        """Create room in Microsoft Teams"""
        if not self._teams_credentials:
            raise ValueError("Teams credentials not configured")

        async with TeamsIntegrationService(self._teams_credentials) as teams:
            return await teams.create_meeting_room(room)

    async def _create_zoom_room(self, room: MeetingRoom) -> Dict:
        """Create room in Zoom"""
        if not self._zoom_credentials:
            raise ValueError("Zoom credentials not configured")

        async with ZoomIntegrationService(self._zoom_credentials) as zoom:
            return await zoom.create_meeting_room(room)

    async def create_track_room(
        self,
        track_id: UUID,
        organization_id: UUID,
        platform: MeetingPlatform,
        created_by: UUID,
        name: Optional[str] = None
    ) -> MeetingRoom:
        """Create meeting room for a track"""
        room_name = name or f"Track Room - {track_id}"

        return await self.create_meeting_room(
            organization_id=organization_id,
            name=room_name,
            platform=platform,
            room_type=RoomType.TRACK_ROOM,
            created_by=created_by,
            track_id=track_id
        )

    async def create_instructor_room(
        self,
        instructor_id: UUID,
        organization_id: UUID,
        platform: MeetingPlatform,
        created_by: UUID,
        name: Optional[str] = None
    ) -> MeetingRoom:
        """Create personal room for instructor"""
        room_name = name or f"Instructor Room - {instructor_id}"

        return await self.create_meeting_room(
            organization_id=organization_id,
            name=room_name,
            platform=platform,
            room_type=RoomType.INSTRUCTOR_ROOM,
            created_by=created_by,
            instructor_id=instructor_id
        )

    async def create_project_room(
        self,
        project_id: UUID,
        organization_id: UUID,
        platform: MeetingPlatform,
        created_by: UUID,
        name: Optional[str] = None
    ) -> MeetingRoom:
        """Create meeting room for a project"""
        room_name = name or f"Project Room - {project_id}"

        return await self.create_meeting_room(
            organization_id=organization_id,
            name=room_name,
            platform=platform,
            room_type=RoomType.PROJECT_ROOM,
            created_by=created_by,
            project_id=project_id
        )

    async def update_meeting_room(
        self,
        room_id: UUID,
        name: Optional[str] = None,
        settings: Optional[Dict] = None
    ) -> MeetingRoom:
        """Update existing meeting room"""
        try:
            # Get existing room
            room = await self._organization_dao.get_room_by_id(room_id)
            if not room:
                raise ValueError(f"Room {room_id} not found")

            # Update room properties
            if name:
                room.name = name
            if settings:
                room.settings.update(settings)

            room.updated_at = datetime.utcnow()

            # Update on platform
            if room.platform == MeetingPlatform.TEAMS:
                await self._update_teams_room(room)
            elif room.platform == MeetingPlatform.ZOOM:
                await self._update_zoom_room(room)

            # Save to database
            updated_room = await self._organization_dao.update_room(room)

            self._logger.info(f"Updated meeting room: {room_id}")
            return updated_room

        except Exception as e:
            self._logger.error(f"Failed to update meeting room: {e}")
            raise

    async def _update_teams_room(self, room: MeetingRoom):
        """Update room in Microsoft Teams"""
        if not self._teams_credentials:
            return

        async with TeamsIntegrationService(self._teams_credentials) as teams:
            await teams.update_meeting_room(room, {})

    async def _update_zoom_room(self, room: MeetingRoom):
        """Update room in Zoom"""
        if not self._zoom_credentials:
            return

        async with ZoomIntegrationService(self._zoom_credentials) as zoom:
            await zoom.update_meeting_room(room, {})

    async def delete_meeting_room(self, room_id: UUID) -> bool:
        """Delete meeting room"""
        try:
            # Get room
            room = await self._organization_dao.get_room_by_id(room_id)
            if not room:
                return False

            # Delete from platform
            if room.external_room_id:
                if room.platform == MeetingPlatform.TEAMS:
                    await self._delete_teams_room(room.external_room_id)
                elif room.platform == MeetingPlatform.ZOOM:
                    await self._delete_zoom_room(room.external_room_id)

            # Delete from database
            db_success = await self._organization_dao.delete_room(room_id)

            if db_success:
                self._logger.info(f"Deleted meeting room: {room_id}")

            return db_success

        except Exception as e:
            self._logger.error(f"Failed to delete meeting room: {e}")
            return False

    async def _delete_teams_room(self, external_room_id: str) -> bool:
        """Delete room from Microsoft Teams"""
        if not self._teams_credentials:
            return True

        try:
            async with TeamsIntegrationService(self._teams_credentials) as teams:
                return await teams.delete_meeting_room(external_room_id)
        except Exception as e:
            self._logger.warning(f"Failed to delete Teams room: {e}")
            return False

    async def _delete_zoom_room(self, external_room_id: str) -> bool:
        """Delete room from Zoom"""
        if not self._zoom_credentials:
            return True

        try:
            async with ZoomIntegrationService(self._zoom_credentials) as zoom:
                return await zoom.delete_meeting_room(external_room_id)
        except Exception as e:
            self._logger.warning(f"Failed to delete Zoom room: {e}")
            return False

    async def get_organization_rooms(
        self,
        organization_id: UUID,
        platform: Optional[MeetingPlatform] = None,
        room_type: Optional[RoomType] = None
    ) -> List[MeetingRoom]:
        """Get all meeting rooms for organization"""
        try:
            if room_type:
                rooms = await self._organization_dao.get_rooms_by_type(
                    room_type, organization_id
                )
                if platform:
                    rooms = [r for r in rooms if r.platform == platform]
            else:
                rooms = await self._organization_dao.get_organization_rooms(
                    organization_id, platform
                )

            return rooms

        except Exception as e:
            self._logger.error(f"Failed to get organization rooms: {e}")
            raise

    async def get_track_rooms(self, track_id: UUID) -> List[MeetingRoom]:
        """Get all rooms for track"""
        try:
            return await self._organization_dao.get_track_rooms(track_id)
        except Exception as e:
            self._logger.error(f"Failed to get track rooms: {e}")
            raise

    async def get_instructor_rooms(self, instructor_id: UUID) -> List[MeetingRoom]:
        """Get all rooms for instructor"""
        try:
            return await self._organization_dao.get_instructor_rooms(instructor_id)
        except Exception as e:
            self._logger.error(f"Failed to get instructor rooms: {e}")
            raise

    async def get_accessible_rooms(
        self,
        user_id: UUID,
        user_role: EnhancedRole,
        organization_id: UUID
    ) -> List[MeetingRoom]:
        """Get rooms accessible by user based on their role"""
        try:
            all_rooms = await self._organization_dao.get_organization_rooms(organization_id)

            accessible_rooms = []
            for room in all_rooms:
                if room.is_accessible_by_user(user_id, user_role):
                    accessible_rooms.append(room)

            return accessible_rooms

        except Exception as e:
            self._logger.error(f"Failed to get accessible rooms: {e}")
            raise

    async def send_room_invitation(
        self,
        room_id: UUID,
        invitee_emails: List[str]
    ) -> bool:
        """Send room invitation to users"""
        try:
            # Get room
            room = await self._organization_dao.get_room_by_id(room_id)
            if not room or not room.is_active():
                return False

            # Send invitations via platform
            success = False
            if room.platform == MeetingPlatform.TEAMS:
                success = await self._send_teams_invitation(room, invitee_emails)
            elif room.platform == MeetingPlatform.ZOOM:
                success = await self._send_zoom_invitation(room, invitee_emails)

            if success:
                self._logger.info(f"Sent room invitations for room {room_id}")

            return success

        except Exception as e:
            self._logger.error(f"Failed to send room invitation: {e}")
            return False

    async def _send_teams_invitation(self, room: MeetingRoom, emails: List[str]) -> bool:
        """Send Teams meeting invitation"""
        if not self._teams_credentials or not room.external_room_id:
            return False

        try:
            async with TeamsIntegrationService(self._teams_credentials) as teams:
                return await teams.send_meeting_invitation(room.external_room_id, emails)
        except Exception as e:
            self._logger.warning(f"Failed to send Teams invitation: {e}")
            return False

    async def _send_zoom_invitation(self, room: MeetingRoom, emails: List[str]) -> bool:
        """Send Zoom meeting invitation"""
        if not self._zoom_credentials or not room.external_room_id:
            return False

        try:
            async with ZoomIntegrationService(self._zoom_credentials) as zoom:
                return await zoom.send_meeting_invitation(room.external_room_id, emails)
        except Exception as e:
            self._logger.warning(f"Failed to send Zoom invitation: {e}")
            return False

    async def get_room_statistics(self, organization_id: UUID) -> Dict:
        """Get meeting room usage statistics"""
        try:
            rooms = await self._organization_dao.get_organization_rooms(organization_id)

            stats = {
                "total_rooms": len(rooms),
                "by_platform": {},
                "by_type": {},
                "active_rooms": 0
            }

            for room in rooms:
                # Count by platform
                platform_key = room.platform.value
                stats["by_platform"][platform_key] = stats["by_platform"].get(platform_key, 0) + 1

                # Count by type
                type_key = room.room_type.value
                stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1

                # Count active
                if room.is_active():
                    stats["active_rooms"] += 1

            return stats

        except Exception as e:
            self._logger.error(f"Failed to get room statistics: {e}")
            return {}

    def validate_platform_configuration(self, platform: MeetingPlatform) -> bool:
        """Validate platform integration configuration"""
        if platform == MeetingPlatform.TEAMS:
            return self._teams_credentials is not None and TeamsIntegrationService(self._teams_credentials).validate_configuration()
        elif platform == MeetingPlatform.ZOOM:
            return self._zoom_credentials is not None and ZoomIntegrationService(self._zoom_credentials).validate_configuration()

        return False
