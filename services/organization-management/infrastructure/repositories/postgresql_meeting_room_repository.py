"""
PostgreSQL implementation of meeting room repository
Follows DAO pattern with proper database interaction
"""
import json
from typing import List, Optional
from uuid import UUID
import asyncpg

from domain.interfaces.meeting_room_repository import IMeetingRoomRepository
from domain.entities.meeting_room import MeetingRoom, MeetingPlatform, RoomType


class PostgreSQLMeetingRoomRepository(IMeetingRoomRepository):
    """PostgreSQL implementation of meeting room repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def create_room(self, room: MeetingRoom) -> MeetingRoom:
        """Create new meeting room"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow("""
                INSERT INTO meeting_rooms (
                    id, name, platform, room_type, organization_id,
                    project_id, track_id, instructor_id, external_room_id,
                    join_url, host_url, meeting_id, passcode, settings,
                    is_recurring, max_participants, created_by, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                RETURNING *
            """,
                room.id,
                room.name,
                room.platform.value,
                room.room_type.value,
                room.organization_id,
                room.project_id,
                room.track_id,
                room.instructor_id,
                room.external_room_id,
                room.join_url,
                room.host_url,
                room.meeting_id,
                room.passcode,
                json.dumps(room.settings),
                room.is_recurring,
                room.max_participants,
                room.created_by,
                room.status
            )

            return self._row_to_room(row)

    async def get_room_by_id(self, room_id: UUID) -> Optional[MeetingRoom]:
        """Get room by ID"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT * FROM meeting_rooms WHERE id = $1",
                room_id
            )

            return self._row_to_room(row) if row else None

    async def get_organization_rooms(self, organization_id: UUID, platform: Optional[MeetingPlatform] = None) -> List[MeetingRoom]:
        """Get all rooms for organization"""
        async with self.db_pool.acquire() as connection:
            if platform:
                rows = await connection.fetch("""
                    SELECT * FROM meeting_rooms
                    WHERE organization_id = $1 AND platform = $2 AND status = 'active'
                    ORDER BY created_at DESC
                """, organization_id, platform.value)
            else:
                rows = await connection.fetch("""
                    SELECT * FROM meeting_rooms
                    WHERE organization_id = $1 AND status = 'active'
                    ORDER BY created_at DESC
                """, organization_id)

            return [self._row_to_room(row) for row in rows]

    async def get_project_rooms(self, project_id: UUID, platform: Optional[MeetingPlatform] = None) -> List[MeetingRoom]:
        """Get all rooms for project"""
        async with self.db_pool.acquire() as connection:
            if platform:
                rows = await connection.fetch("""
                    SELECT * FROM meeting_rooms
                    WHERE project_id = $1 AND platform = $2 AND status = 'active'
                    ORDER BY created_at DESC
                """, project_id, platform.value)
            else:
                rows = await connection.fetch("""
                    SELECT * FROM meeting_rooms
                    WHERE project_id = $1 AND status = 'active'
                    ORDER BY created_at DESC
                """, project_id)

            return [self._row_to_room(row) for row in rows]

    async def get_track_rooms(self, track_id: UUID, platform: Optional[MeetingPlatform] = None) -> List[MeetingRoom]:
        """Get all rooms for track"""
        async with self.db_pool.acquire() as connection:
            if platform:
                rows = await connection.fetch("""
                    SELECT * FROM meeting_rooms
                    WHERE track_id = $1 AND platform = $2 AND status = 'active'
                    ORDER BY created_at DESC
                """, track_id, platform.value)
            else:
                rows = await connection.fetch("""
                    SELECT * FROM meeting_rooms
                    WHERE track_id = $1 AND status = 'active'
                    ORDER BY created_at DESC
                """, track_id)

            return [self._row_to_room(row) for row in rows]

    async def get_instructor_rooms(self, instructor_id: UUID, platform: Optional[MeetingPlatform] = None) -> List[MeetingRoom]:
        """Get all rooms for instructor"""
        async with self.db_pool.acquire() as connection:
            if platform:
                rows = await connection.fetch("""
                    SELECT * FROM meeting_rooms
                    WHERE instructor_id = $1 AND platform = $2 AND status = 'active'
                    ORDER BY created_at DESC
                """, instructor_id, platform.value)
            else:
                rows = await connection.fetch("""
                    SELECT * FROM meeting_rooms
                    WHERE instructor_id = $1 AND status = 'active'
                    ORDER BY created_at DESC
                """, instructor_id)

            return [self._row_to_room(row) for row in rows]

    async def get_rooms_by_type(self, room_type: RoomType, organization_id: UUID) -> List[MeetingRoom]:
        """Get rooms by type within organization"""
        async with self.db_pool.acquire() as connection:
            rows = await connection.fetch("""
                SELECT * FROM meeting_rooms
                WHERE room_type = $1 AND organization_id = $2 AND status = 'active'
                ORDER BY created_at DESC
            """, room_type.value, organization_id)

            return [self._row_to_room(row) for row in rows]

    async def update_room(self, room: MeetingRoom) -> MeetingRoom:
        """Update existing room"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow("""
                UPDATE meeting_rooms SET
                    name = $2,
                    external_room_id = $3,
                    join_url = $4,
                    host_url = $5,
                    meeting_id = $6,
                    passcode = $7,
                    settings = $8,
                    is_recurring = $9,
                    max_participants = $10,
                    updated_at = $11,
                    last_used_at = $12,
                    status = $13
                WHERE id = $1
                RETURNING *
            """,
                room.id,
                room.name,
                room.external_room_id,
                room.join_url,
                room.host_url,
                room.meeting_id,
                room.passcode,
                json.dumps(room.settings),
                room.is_recurring,
                room.max_participants,
                room.updated_at,
                room.last_used_at,
                room.status
            )

            return self._row_to_room(row)

    async def delete_room(self, room_id: UUID) -> bool:
        """Delete room"""
        async with self.db_pool.acquire() as connection:
            result = await connection.execute(
                "DELETE FROM meeting_rooms WHERE id = $1",
                room_id
            )

            return result == "DELETE 1"

    async def deactivate_room(self, room_id: UUID) -> bool:
        """Deactivate room"""
        async with self.db_pool.acquire() as connection:
            result = await connection.execute("""
                UPDATE meeting_rooms SET
                    status = 'inactive',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, room_id)

            return result == "UPDATE 1"

    async def get_room_by_external_id(self, external_room_id: str, platform: MeetingPlatform) -> Optional[MeetingRoom]:
        """Get room by external platform ID"""
        async with self.db_pool.acquire() as connection:
            row = await connection.fetchrow("""
                SELECT * FROM meeting_rooms
                WHERE external_room_id = $1 AND platform = $2
            """, external_room_id, platform.value)

            return self._row_to_room(row) if row else None

    async def search_rooms(self, organization_id: UUID, query: str) -> List[MeetingRoom]:
        """Search rooms by name or description"""
        async with self.db_pool.acquire() as connection:
            search_pattern = f"%{query}%"
            rows = await connection.fetch("""
                SELECT * FROM meeting_rooms
                WHERE organization_id = $1
                AND status = 'active'
                AND (name ILIKE $2)
                ORDER BY name ASC
            """, organization_id, search_pattern)

            return [self._row_to_room(row) for row in rows]

    def _row_to_room(self, row) -> Optional[MeetingRoom]:
        """Convert database row to MeetingRoom entity"""
        if not row:
            return None

        return MeetingRoom(
            id=row['id'],
            name=row['name'],
            platform=MeetingPlatform(row['platform']),
            room_type=RoomType(row['room_type']),
            organization_id=row['organization_id'],
            project_id=row['project_id'],
            track_id=row['track_id'],
            instructor_id=row['instructor_id'],
            external_room_id=row['external_room_id'],
            join_url=row['join_url'],
            host_url=row['host_url'],
            meeting_id=row['meeting_id'],
            passcode=row['passcode'],
            settings=json.loads(row['settings']) if row['settings'] else {},
            is_recurring=row['is_recurring'],
            max_participants=row['max_participants'],
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_used_at=row['last_used_at'],
            status=row['status']
        )