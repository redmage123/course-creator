"""
PostgreSQL Organization Repository Implementation
Single Responsibility: Organization data persistence with PostgreSQL
Dependency Inversion: Implements abstract repository interface
"""
from typing import List, Optional
from uuid import UUID
import asyncpg
import json
from datetime import datetime

from domain.interfaces.organization_repository import IOrganizationRepository
from domain.entities.organization import Organization


class PostgreSQLOrganizationRepository(IOrganizationRepository):
    """
    PostgreSQL implementation of organization repository
    """

    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool

    async def create(self, organization: Organization) -> Organization:
        """Create a new organization"""
        query = """
        INSERT INTO course_creator.organizations (
            id, name, slug, description, logo_url, domain,
            address, contact_phone, contact_email, logo_file_path,
            settings, is_active, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
        ) RETURNING *
        """

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                organization.id, organization.name, organization.slug,
                organization.description, organization.logo_url, organization.domain,
                organization.address, organization.contact_phone, organization.contact_email,
                organization.logo_file_path,
                json.dumps(organization.settings), organization.is_active,
                organization.created_at, organization.updated_at
            )

            return self._row_to_organization(row)

    async def get_by_id(self, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        query = "SELECT * FROM course_creator.organizations WHERE id = $1"

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, organization_id)

            return self._row_to_organization(row) if row else None

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        query = "SELECT * FROM course_creator.organizations WHERE slug = $1"

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, slug)

            return self._row_to_organization(row) if row else None

    async def get_by_domain(self, domain: str) -> Optional[Organization]:
        """Get organization by domain"""
        query = "SELECT * FROM course_creator.organizations WHERE domain = $1"

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, domain)

            return self._row_to_organization(row) if row else None

    async def update(self, organization: Organization) -> Organization:
        """Update organization"""
        query = """
        UPDATE course_creator.organizations SET
            name = $2, slug = $3, description = $4, logo_url = $5, domain = $6,
            address = $7, contact_phone = $8, contact_email = $9, logo_file_path = $10,
            settings = $11, is_active = $12, updated_at = $13
        WHERE id = $1
        RETURNING *
        """

        organization.updated_at = datetime.utcnow()

        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                query,
                organization.id, organization.name, organization.slug,
                organization.description, organization.logo_url, organization.domain,
                organization.address, organization.contact_phone, organization.contact_email,
                organization.logo_file_path,
                json.dumps(organization.settings), organization.is_active,
                organization.updated_at
            )

            return self._row_to_organization(row)

    async def delete(self, organization_id: UUID) -> bool:
        """Delete organization"""
        query = "DELETE FROM course_creator.organizations WHERE id = $1"

        async with self._pool.acquire() as connection:
            result = await connection.execute(query, organization_id)

            return result.split()[-1] == "1"  # Check if one row was affected

    async def exists_by_slug(self, slug: str) -> bool:
        """Check if organization exists by slug"""
        query = "SELECT EXISTS(SELECT 1 FROM course_creator.organizations WHERE slug = $1)"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, slug)

    async def exists_by_domain(self, domain: str) -> bool:
        """Check if organization exists by domain"""
        query = "SELECT EXISTS(SELECT 1 FROM course_creator.organizations WHERE domain = $1)"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, domain)

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Organization]:
        """Get all organizations with pagination"""
        query = "SELECT * FROM course_creator.organizations ORDER BY created_at DESC LIMIT $1 OFFSET $2"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query, limit, offset)

            return [self._row_to_organization(row) for row in rows]

    async def get_active(self) -> List[Organization]:
        """Get all active organizations"""
        query = "SELECT * FROM course_creator.organizations WHERE is_active = true ORDER BY name"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(query)

            return [self._row_to_organization(row) for row in rows]

    async def search(self, query: str, limit: int = 50) -> List[Organization]:
        """Search organizations by name or slug"""
        search_query = """
        SELECT * FROM course_creator.organizations
        WHERE name ILIKE $1 OR slug ILIKE $1
        ORDER BY
            CASE
                WHEN slug ILIKE $1 THEN 1
                WHEN name ILIKE $1 THEN 2
                ELSE 3
            END,
            name
        LIMIT $2
        """

        search_pattern = f"%{query}%"

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(search_query, search_pattern, limit)

            return [self._row_to_organization(row) for row in rows]

    async def count(self) -> int:
        """Count total organizations"""
        query = "SELECT COUNT(*) FROM course_creator.organizations"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query)

    async def count_active(self) -> int:
        """Count active organizations"""
        query = "SELECT COUNT(*) FROM course_creator.organizations WHERE is_active = true"

        async with self._pool.acquire() as connection:
            return await connection.fetchval(query)

    def _row_to_organization(self, row) -> Organization:
        """Convert database row to Organization entity"""
        if not row:
            return None

        # Parse settings JSON
        settings = json.loads(row['settings']) if row['settings'] else {}

        return Organization(
            id=row['id'],
            name=row['name'],
            slug=row['slug'],
            address=row.get('address', ''),
            contact_phone=row.get('contact_phone', ''),
            contact_email=row.get('contact_email', ''),
            description=row['description'],
            logo_url=row['logo_url'],
            logo_file_path=row.get('logo_file_path'),
            domain=row['domain'],
            settings=settings,
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )