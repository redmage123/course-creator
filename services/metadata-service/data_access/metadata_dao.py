"""
MetadataDAO - Data Access Object for Metadata

BUSINESS REQUIREMENT:
Provide data access layer for metadata CRUD operations with PostgreSQL integration,
supporting full-text search, tag-based queries, and transactional operations.

DESIGN PATTERN:
Data Access Object (DAO) pattern with async/await PostgreSQL operations
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import asyncpg
import json
from datetime import datetime, timezone

from metadata_service.domain.entities.metadata import Metadata


# Custom Exceptions
class MetadataDAOError(Exception):
    """Base exception for MetadataDAO errors"""
    pass


class MetadataAlreadyExistsError(MetadataDAOError):
    """Raised when attempting to create duplicate metadata"""
    pass


class MetadataNotFoundError(MetadataDAOError):
    """Raised when metadata not found for update operation"""
    pass


class MetadataDAO:
    """
    Data Access Object for Metadata operations

    RESPONSIBILITIES:
    - CRUD operations for entity_metadata table
    - Full-text search using PostgreSQL tsvector
    - Tag-based queries using array operators
    - Transaction support for atomic operations
    - Connection pooling for performance

    DATABASE SCHEMA:
    Uses entity_metadata table with:
    - id (UUID primary key)
    - entity_id, entity_type (composite unique)
    - metadata (JSONB)
    - title, description (TEXT)
    - tags, keywords (TEXT[])
    - search_vector (tsvector, auto-generated)
    - timestamps and user tracking
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize MetadataDAO with connection pool

        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool

    async def create(
        self,
        metadata: Metadata,
        connection: Optional[asyncpg.Connection] = None
    ) -> Metadata:
        """
        Create new metadata record

        BUSINESS LOGIC:
        - Inserts metadata into entity_metadata table
        - Auto-generates search_vector via database trigger
        - Enforces unique constraint on (entity_id, entity_type)

        Args:
            metadata: Metadata entity to create
            connection: Optional connection for transaction support

        Returns:
            Created metadata with generated ID and timestamps

        Raises:
            MetadataAlreadyExistsError: If entity_id + entity_type already exists
        """
        query = """
            INSERT INTO entity_metadata (
                id, entity_id, entity_type, metadata,
                title, description, tags, keywords,
                created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id, created_at, updated_at
        """

        try:
            conn = connection or await self.pool.acquire()
            try:
                row = await conn.fetchrow(
                    query,
                    metadata.id,
                    metadata.entity_id,
                    metadata.entity_type,
                    json.dumps(metadata.metadata),  # Convert dict to JSON string
                    metadata.title,
                    metadata.description,
                    metadata.tags,
                    metadata.keywords,
                    metadata.created_at,
                    metadata.updated_at,
                    metadata.created_by,
                    metadata.updated_by
                )

                # Update metadata with database-generated values
                metadata.id = row['id']
                metadata.created_at = row['created_at']
                metadata.updated_at = row['updated_at']

                return metadata

            finally:
                if not connection:
                    await self.pool.release(conn)

        except asyncpg.UniqueViolationError:
            raise MetadataAlreadyExistsError(
                f"Metadata already exists for entity_id={metadata.entity_id}, "
                f"entity_type={metadata.entity_type}"
            )

    async def get_by_id(self, metadata_id: UUID) -> Optional[Metadata]:
        """
        Retrieve metadata by ID

        Args:
            metadata_id: Metadata ID (primary key)

        Returns:
            Metadata entity or None if not found
        """
        query = """
            SELECT id, entity_id, entity_type, metadata,
                   title, description, tags, keywords,
                   created_at, updated_at, created_by, updated_by
            FROM entity_metadata
            WHERE id = $1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, metadata_id)

            if row is None:
                return None

            return self._row_to_metadata(row)

    async def get_by_entity(
        self,
        entity_id: UUID,
        entity_type: str
    ) -> Optional[Metadata]:
        """
        Retrieve metadata by entity_id and entity_type

        PRIMARY USE CASE:
        Most common query pattern - get metadata for a specific entity

        Args:
            entity_id: Entity UUID
            entity_type: Entity type (course, content, user, etc.)

        Returns:
            Metadata entity or None if not found
        """
        query = """
            SELECT id, entity_id, entity_type, metadata,
                   title, description, tags, keywords,
                   created_at, updated_at, created_by, updated_by
            FROM entity_metadata
            WHERE entity_id = $1 AND entity_type = $2
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, entity_id, entity_type)

            if row is None:
                return None

            return self._row_to_metadata(row)

    async def list_by_entity_type(
        self,
        entity_type: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Metadata]:
        """
        List all metadata for a given entity_type

        PAGINATION:
        Supports limit and offset for large result sets

        Args:
            entity_type: Entity type to filter by
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of metadata entities
        """
        query = """
            SELECT id, entity_id, entity_type, metadata,
                   title, description, tags, keywords,
                   created_at, updated_at, created_by, updated_by
            FROM entity_metadata
            WHERE entity_type = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, entity_type, limit, offset)
            return [self._row_to_metadata(row) for row in rows]

    async def update(
        self,
        metadata: Metadata,
        connection: Optional[asyncpg.Connection] = None
    ) -> Metadata:
        """
        Update existing metadata record

        BUSINESS LOGIC:
        - Updates all fields except id and created_at
        - Auto-updates updated_at via database trigger
        - Regenerates search_vector via database trigger

        Args:
            metadata: Metadata entity with updated values
            connection: Optional connection for transaction support

        Returns:
            Updated metadata

        Raises:
            MetadataNotFoundError: If metadata ID not found
        """
        query = """
            UPDATE entity_metadata
            SET entity_id = $2,
                entity_type = $3,
                metadata = $4,
                title = $5,
                description = $6,
                tags = $7,
                keywords = $8,
                updated_by = $9
            WHERE id = $1
            RETURNING updated_at
        """

        try:
            conn = connection or await self.pool.acquire()
            try:
                row = await conn.fetchrow(
                    query,
                    metadata.id,
                    metadata.entity_id,
                    metadata.entity_type,
                    json.dumps(metadata.metadata),  # Convert dict to JSON string
                    metadata.title,
                    metadata.description,
                    metadata.tags,
                    metadata.keywords,
                    metadata.updated_by
                )

                if row is None:
                    raise MetadataNotFoundError(
                        f"Metadata not found with id={metadata.id}"
                    )

                metadata.updated_at = row['updated_at']
                return metadata

            finally:
                if not connection:
                    await self.pool.release(conn)

        except asyncpg.PostgresError as e:
            if isinstance(e, asyncpg.exceptions.DataError):
                raise MetadataDAOError(f"Invalid data: {str(e)}")
            raise

    async def delete(self, metadata_id: UUID) -> bool:
        """
        Delete metadata by ID

        IDEMPOTENCY:
        Returns False if metadata doesn't exist (not an error)

        Args:
            metadata_id: Metadata ID to delete

        Returns:
            True if deleted, False if not found
        """
        query = """
            DELETE FROM entity_metadata
            WHERE id = $1
        """

        async with self.pool.acquire() as conn:
            result = await conn.execute(query, metadata_id)

            # result is like "DELETE 1" or "DELETE 0"
            deleted_count = int(result.split()[-1])
            return deleted_count > 0

    async def search(
        self,
        search_query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Metadata]:
        """
        Full-text search on metadata

        SEARCH STRATEGY:
        - Uses PostgreSQL full-text search with tsvector
        - Searches across title, description, tags, keywords
        - Returns results ranked by relevance (ts_rank)
        - Weights: title (A=highest), description (B), tags (C), keywords (D)

        Args:
            search_query: Text query (will be converted to tsquery)
            entity_types: Optional list of entity types to filter
            limit: Maximum number of results

        Returns:
            List of metadata entities ranked by relevance
        """
        # Build query dynamically based on whether entity_types filter is provided
        if entity_types:
            query = """
                SELECT id, entity_id, entity_type, metadata,
                       title, description, tags, keywords,
                       created_at, updated_at, created_by, updated_by,
                       ts_rank(search_vector, to_tsquery('english', $1)) AS rank
                FROM entity_metadata
                WHERE search_vector @@ to_tsquery('english', $1)
                  AND entity_type = ANY($2)
                ORDER BY rank DESC
                LIMIT $3
            """
            params = [search_query, entity_types, limit]
        else:
            query = """
                SELECT id, entity_id, entity_type, metadata,
                       title, description, tags, keywords,
                       created_at, updated_at, created_by, updated_by,
                       ts_rank(search_vector, to_tsquery('english', $1)) AS rank
                FROM entity_metadata
                WHERE search_vector @@ to_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT $2
            """
            params = [search_query, limit]

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_metadata(row) for row in rows]

    async def search_fuzzy(
        self,
        search_query: str,
        entity_types: Optional[List[str]] = None,
        similarity_threshold: float = 0.3,
        limit: int = 20
    ) -> List[Tuple[Metadata, float]]:
        """
        Fuzzy search with typo tolerance using trigram similarity

        FUZZY SEARCH STRATEGY:
        - Uses PostgreSQL pg_trgm extension for similarity matching
        - Handles typos: "pyton" → "python"
        - Handles partial matches: "prog" → "programming"
        - Returns (metadata, similarity_score) tuples

        SIMILARITY THRESHOLD:
        - 0.0-0.3: Very loose matching (many typos)
        - 0.3-0.5: Moderate matching (some typos, partial words)
        - 0.5-0.7: Strong matching (close to exact)
        - 0.7-1.0: Very strong matching (almost exact)
        - 1.0: Exact match

        BUSINESS VALUE:
        Students can find courses even with typos or incomplete search terms

        Args:
            search_query: Text query (typos allowed!)
            entity_types: Optional list of entity types to filter
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of (Metadata, similarity_score) tuples ordered by relevance
        """
        # Use database function for fuzzy search
        query = """
            SELECT id, entity_id, entity_type, metadata,
                   title, description, tags, keywords,
                   created_at, updated_at, created_by, updated_by,
                   similarity_score
            FROM search_metadata_fuzzy($1, $2, $3, $4)
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                query,
                search_query,
                entity_types,
                similarity_threshold,
                limit
            )

            # Return tuples of (Metadata, similarity_score)
            results = []
            for row in rows:
                metadata = self._row_to_metadata(row)
                similarity_score = float(row['similarity_score'])
                results.append((metadata, similarity_score))

            return results

    async def get_by_tags(
        self,
        tags: List[str],
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Metadata]:
        """
        Query metadata by tags

        TAG MATCHING:
        - Uses PostgreSQL array operators (@>)
        - Finds metadata that contains ALL specified tags (AND logic)
        - Case-insensitive matching (tags normalized to lowercase)

        Args:
            tags: List of tags to match (must have all)
            entity_type: Optional entity type filter
            limit: Maximum number of results

        Returns:
            List of metadata entities with matching tags
        """
        # Normalize tags to lowercase for case-insensitive matching
        normalized_tags = [tag.lower() for tag in tags]

        if entity_type:
            query = """
                SELECT id, entity_id, entity_type, metadata,
                       title, description, tags, keywords,
                       created_at, updated_at, created_by, updated_by
                FROM entity_metadata
                WHERE tags @> $1
                  AND entity_type = $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            params = [normalized_tags, entity_type, limit]
        else:
            query = """
                SELECT id, entity_id, entity_type, metadata,
                       title, description, tags, keywords,
                       created_at, updated_at, created_by, updated_by
                FROM entity_metadata
                WHERE tags @> $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            params = [normalized_tags, limit]

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_metadata(row) for row in rows]

    def _row_to_metadata(self, row: asyncpg.Record) -> Metadata:
        """
        Convert database row to Metadata entity

        DESERIALIZATION:
        Maps database columns to Metadata entity fields

        JSONB HANDLING:
        asyncpg returns JSONB as strings in some cases, so parse if needed

        Args:
            row: asyncpg Record from query

        Returns:
            Metadata entity
        """
        # Parse JSONB field if it's a string
        metadata_value = row['metadata'] or {}
        if isinstance(metadata_value, str):
            metadata_value = json.loads(metadata_value)

        return Metadata(
            id=row['id'],
            entity_id=row['entity_id'],
            entity_type=row['entity_type'],
            metadata=metadata_value,
            title=row['title'],
            description=row['description'],
            tags=list(row['tags']) if row['tags'] else [],
            keywords=list(row['keywords']) if row['keywords'] else [],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=row['created_by'],
            updated_by=row['updated_by']
        )
