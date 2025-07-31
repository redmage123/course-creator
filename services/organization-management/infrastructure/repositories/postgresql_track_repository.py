"""
PostgreSQL Track Repository Implementation
Single Responsibility: Track data persistence with PostgreSQL
Dependency Inversion: Implements abstract repository interface
"""
from typing import List, Optional
from uuid import UUID
import asyncpg
import json
from datetime import datetime

from domain.interfaces.track_repository import ITrackRepository
from domain.entities.track import Track, TrackStatus, TrackType


class PostgreSQLTrackRepository(ITrackRepository):
    """
    PostgreSQL implementation of track repository
    """

    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool

    async def create(self, track: Track) -> Track:
        """Create a new track"""
        query = """
        INSERT INTO tracks (
            id, project_id, name, slug, description, track_type, target_audience,
            prerequisites, duration_weeks, max_enrolled, learning_objectives,
            skills_taught, difficulty_level, sequence_order, auto_enroll_enabled,
            status, settings, created_by, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
        ) RETURNING *
        """

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                track.id, track.project_id, track.name, track.slug, track.description,
                track.track_type.value, track.target_audience, track.prerequisites,
                track.duration_weeks, track.max_enrolled, track.learning_objectives,
                track.skills_taught, track.difficulty_level, track.sequence_order,
                track.auto_enroll_enabled, track.status.value, json.dumps(track.settings),
                track.created_by, track.created_at, track.updated_at
            )

            return self._row_to_track(row)

    async def get_by_id(self, track_id: UUID) -> Optional[Track]:
        """Get track by ID"""
        query = "SELECT * FROM tracks WHERE id = $1"

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, track_id)

            return self._row_to_track(row) if row else None

    async def get_by_project_and_slug(self, project_id: UUID, slug: str) -> Optional[Track]:
        """Get track by project ID and slug"""
        query = "SELECT * FROM tracks WHERE project_id = $1 AND slug = $2"

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, project_id, slug)

            return self._row_to_track(row) if row else None

    async def update(self, track: Track) -> Track:
        """Update track"""
        query = """
        UPDATE tracks SET
            name = $3, slug = $4, description = $5, track_type = $6, target_audience = $7,
            prerequisites = $8, duration_weeks = $9, max_enrolled = $10, learning_objectives = $11,
            skills_taught = $12, difficulty_level = $13, sequence_order = $14,
            auto_enroll_enabled = $15, status = $16, settings = $17, updated_at = $18
        WHERE id = $1 AND project_id = $2
        RETURNING *
        """

        track.updated_at = datetime.utcnow()

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                track.id, track.project_id, track.name, track.slug, track.description,
                track.track_type.value, track.target_audience, track.prerequisites,
                track.duration_weeks, track.max_enrolled, track.learning_objectives,
                track.skills_taught, track.difficulty_level, track.sequence_order,
                track.auto_enroll_enabled, track.status.value, json.dumps(track.settings),
                track.updated_at
            )

            return self._row_to_track(row)

    async def delete(self, track_id: UUID) -> bool:
        """Delete track"""
        query = "DELETE FROM tracks WHERE id = $1"

        async with self._pool.acquire() as connection:
            result = await connection.execute(query, track_id)

            return result.split()[-1] == "1"  # Check if one row was affected

    async def exists_by_project_and_slug(self, project_id: UUID, slug: str) -> bool:
        """Check if track exists by project ID and slug"""
        query = "SELECT EXISTS(SELECT 1 FROM tracks WHERE project_id = $1 AND slug = $2)"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, project_id, slug)

    async def get_by_project(self, project_id: UUID, limit: int = 100, offset: int = 0) -> List[Track]:
        """Get tracks by project"""
        query = """
        SELECT * FROM tracks
        WHERE project_id = $1
        ORDER BY sequence_order ASC, created_at DESC
        LIMIT $2 OFFSET $3
        """

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, project_id, limit, offset)

            return [self._row_to_track(row) for row in rows]

    async def get_by_status(self, status: TrackStatus, limit: int = 100, offset: int = 0) -> List[Track]:
        """Get tracks by status"""
        query = "SELECT * FROM tracks WHERE status = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, status.value, limit, offset)

            return [self._row_to_track(row) for row in rows]

    async def get_by_project_and_status(self, project_id: UUID, status: TrackStatus) -> List[Track]:
        """Get tracks by project and status"""
        query = """
        SELECT * FROM tracks
        WHERE project_id = $1 AND status = $2
        ORDER BY sequence_order ASC, created_at DESC
        """

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, project_id, status.value)

            return [self._row_to_track(row) for row in rows]

    async def get_by_track_type(self, track_type: TrackType) -> List[Track]:
        """Get tracks by type"""
        query = "SELECT * FROM tracks WHERE track_type = $1 ORDER BY created_at DESC"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, track_type.value)

            return [self._row_to_track(row) for row in rows]

    async def get_by_target_audience(self, target_audience: str, project_id: UUID = None) -> List[Track]:
        """Get tracks by target audience"""
        if project_id:
            query = """
            SELECT * FROM tracks
            WHERE project_id = $2 AND $1 = ANY(target_audience)
            ORDER BY sequence_order ASC, created_at DESC
            """
            args = [target_audience, project_id]
        else:
            query = "SELECT * FROM tracks WHERE $1 = ANY(target_audience) ORDER BY created_at DESC"
            args = [target_audience]

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, *args)

            return [self._row_to_track(row) for row in rows]

    async def get_by_difficulty_level(self, difficulty_level: str, project_id: UUID = None) -> List[Track]:
        """Get tracks by difficulty level"""
        if project_id:
            query = """
            SELECT * FROM tracks
            WHERE project_id = $2 AND difficulty_level = $1
            ORDER BY sequence_order ASC, created_at DESC
            """
            args = [difficulty_level, project_id]
        else:
            query = "SELECT * FROM tracks WHERE difficulty_level = $1 ORDER BY created_at DESC"
            args = [difficulty_level]

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, *args)

            return [self._row_to_track(row) for row in rows]

    async def search_by_project(self, project_id: UUID, query: str, limit: int = 50) -> List[Track]:
        """Search tracks within project"""
        search_query = """
        SELECT * FROM tracks
        WHERE project_id = $1 AND (name ILIKE $2 OR description ILIKE $2 OR $3 = ANY(skills_taught))
        ORDER BY
            CASE
                WHEN name ILIKE $2 THEN 1
                ELSE 2
            END,
            sequence_order ASC,
            name
        LIMIT $4
        """

        search_pattern = f"%{query}%"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(search_query, project_id, search_pattern, query, limit)

            return [self._row_to_track(row) for row in rows]

    async def get_by_creator(self, creator_id: UUID) -> List[Track]:
        """Get tracks created by user"""
        query = "SELECT * FROM tracks WHERE created_by = $1 ORDER BY created_at DESC"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, creator_id)

            return [self._row_to_track(row) for row in rows]

    async def get_active_tracks_with_auto_enroll(self, project_id: UUID) -> List[Track]:
        """Get active tracks with auto-enrollment enabled"""
        query = """
        SELECT * FROM tracks
        WHERE project_id = $1 AND status = 'active' AND auto_enroll_enabled = true
        ORDER BY sequence_order ASC, created_at DESC
        """

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, project_id)

            return [self._row_to_track(row) for row in rows]

    async def count_by_project(self, project_id: UUID) -> int:
        """Count tracks in project"""
        query = "SELECT COUNT(*) FROM tracks WHERE project_id = $1"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, project_id)

    async def count_by_status(self, status: TrackStatus) -> int:
        """Count tracks by status"""
        query = "SELECT COUNT(*) FROM tracks WHERE status = $1"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, status.value)

    async def get_ordered_tracks_by_project(self, project_id: UUID) -> List[Track]:
        """Get tracks ordered by sequence_order"""
        query = """
        SELECT * FROM tracks
        WHERE project_id = $1
        ORDER BY sequence_order ASC, name ASC
        """

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, project_id)

            return [self._row_to_track(row) for row in rows]

    def _row_to_track(self, row) -> Track:
        """Convert database row to Track entity"""
        if not row:
            return None

        # Parse settings JSON
        settings = json.loads(row['settings']) if row['settings'] else {}

        return Track(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            slug=row['slug'],
            description=row['description'],
            track_type=TrackType(row['track_type']),
            target_audience=row['target_audience'] or [],
            prerequisites=row['prerequisites'] or [],
            duration_weeks=row['duration_weeks'],
            max_enrolled=row['max_enrolled'],
            learning_objectives=row['learning_objectives'] or [],
            skills_taught=row['skills_taught'] or [],
            difficulty_level=row['difficulty_level'],
            sequence_order=row['sequence_order'],
            auto_enroll_enabled=row['auto_enroll_enabled'],
            status=TrackStatus(row['status']),
            settings=settings,
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )