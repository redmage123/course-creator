"""
PostgreSQL Project Repository Implementation
Single Responsibility: Project data persistence with PostgreSQL
Dependency Inversion: Implements abstract repository interface
"""
from typing import List, Optional
from uuid import UUID
import asyncpg
import json
from datetime import datetime, timedelta

from domain.interfaces.project_repository import IProjectRepository
from domain.entities.project import Project, ProjectStatus


class PostgreSQLProjectRepository(IProjectRepository):
    """
    PostgreSQL implementation of project repository
    """

    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool

    async def create(self, project: Project) -> Project:
        """Create a new project"""
        query = """
        INSERT INTO projects (
            id, organization_id, name, slug, description, objectives,
            target_roles, duration_weeks, max_participants, start_date,
            end_date, status, settings, created_by, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
        ) RETURNING *
        """

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                project.id, project.organization_id, project.name, project.slug,
                project.description, project.objectives, project.target_roles,
                project.duration_weeks, project.max_participants, project.start_date,
                project.end_date, project.status.value, json.dumps(project.settings),
                project.created_by, project.created_at, project.updated_at
            )

            return self._row_to_project(row)

    async def get_by_id(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID"""
        query = "SELECT * FROM projects WHERE id = $1"

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, project_id)

            return self._row_to_project(row) if row else None

    async def get_by_organization_and_slug(self, organization_id: UUID, slug: str) -> Optional[Project]:
        """Get project by organization ID and slug"""
        query = "SELECT * FROM projects WHERE organization_id = $1 AND slug = $2"

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, organization_id, slug)

            return self._row_to_project(row) if row else None

    async def update(self, project: Project) -> Project:
        """Update project"""
        query = """
        UPDATE projects SET
            name = $3, slug = $4, description = $5, objectives = $6,
            target_roles = $7, duration_weeks = $8, max_participants = $9,
            start_date = $10, end_date = $11, status = $12, settings = $13,
            updated_at = $14
        WHERE id = $1 AND organization_id = $2
        RETURNING *
        """

        project.updated_at = datetime.utcnow()

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                project.id, project.organization_id, project.name, project.slug,
                project.description, project.objectives, project.target_roles,
                project.duration_weeks, project.max_participants, project.start_date,
                project.end_date, project.status.value, json.dumps(project.settings),
                project.updated_at
            )

            return self._row_to_project(row)

    async def delete(self, project_id: UUID) -> bool:
        """Delete project"""
        query = "DELETE FROM projects WHERE id = $1"

        async with self._pool.acquire() as connection:
            result = await connection.execute(query, project_id)

            return result.split()[-1] == "1"  # Check if one row was affected

    async def exists_by_organization_and_slug(self, organization_id: UUID, slug: str) -> bool:
        """Check if project exists by organization ID and slug"""
        query = "SELECT EXISTS(SELECT 1 FROM projects WHERE organization_id = $1 AND slug = $2)"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, organization_id, slug)

    async def get_by_organization(self, organization_id: UUID, limit: int = 100, offset: int = 0) -> List[Project]:
        """Get projects by organization"""
        query = """
        SELECT * FROM projects
        WHERE organization_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, organization_id, limit, offset)

            return [self._row_to_project(row) for row in rows]

    async def get_by_status(self, status: ProjectStatus, limit: int = 100, offset: int = 0) -> List[Project]:
        """Get projects by status"""
        query = "SELECT * FROM projects WHERE status = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, status.value, limit, offset)

            return [self._row_to_project(row) for row in rows]

    async def get_by_organization_and_status(self, organization_id: UUID, status: ProjectStatus) -> List[Project]:
        """Get projects by organization and status"""
        query = """
        SELECT * FROM projects
        WHERE organization_id = $1 AND status = $2
        ORDER BY created_at DESC
        """

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, organization_id, status.value)

            return [self._row_to_project(row) for row in rows]

    async def search_by_organization(self, organization_id: UUID, query: str, limit: int = 50) -> List[Project]:
        """Search projects within organization"""
        search_query = """
        SELECT * FROM projects
        WHERE organization_id = $1 AND (name ILIKE $2 OR description ILIKE $2)
        ORDER BY
            CASE
                WHEN name ILIKE $2 THEN 1
                ELSE 2
            END,
            name
        LIMIT $3
        """

        search_pattern = f"%{query}%"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(search_query, organization_id, search_pattern, limit)

            return [self._row_to_project(row) for row in rows]

    async def get_by_creator(self, creator_id: UUID) -> List[Project]:
        """Get projects created by user"""
        query = "SELECT * FROM projects WHERE created_by = $1 ORDER BY created_at DESC"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, creator_id)

            return [self._row_to_project(row) for row in rows]

    async def count_by_organization(self, organization_id: UUID) -> int:
        """Count projects in organization"""
        query = "SELECT COUNT(*) FROM projects WHERE organization_id = $1"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, organization_id)

    async def count_by_status(self, status: ProjectStatus) -> int:
        """Count projects by status"""
        query = "SELECT COUNT(*) FROM projects WHERE status = $1"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, status.value)

    async def get_recent_by_organization(self, organization_id: UUID, days: int = 30) -> List[Project]:
        """Get recently created projects in organization"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = """
        SELECT * FROM projects
        WHERE organization_id = $1 AND created_at >= $2
        ORDER BY created_at DESC
        """

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, organization_id, cutoff_date)

            return [self._row_to_project(row) for row in rows]

    def _row_to_project(self, row) -> Project:
        """Convert database row to Project entity"""
        if not row:
            return None

        # Parse settings JSON
        settings = json.loads(row['settings']) if row['settings'] else {}

        return Project(
            id=row['id'],
            organization_id=row['organization_id'],
            name=row['name'],
            slug=row['slug'],
            description=row['description'],
            objectives=row['objectives'] or [],
            target_roles=row['target_roles'] or [],
            duration_weeks=row['duration_weeks'],
            max_participants=row['max_participants'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            status=ProjectStatus(row['status']),
            settings=settings,
            created_by=row['created_by'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )