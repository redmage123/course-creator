"""
Brain Data Access Object (DAO)

This module implements the concrete repository for brain persistence using PostgreSQL.
It provides the infrastructure layer implementation of the BrainRepository interface.

Business Context:
    Manages database persistence for brain instances, including metadata storage
    and transaction management. Ensures data consistency between database records
    and filesystem-stored neural states.

Architectural Principles:
    - Repository Pattern: Collection-like interface for brain aggregates
    - Infrastructure Layer: Concrete implementation with database dependencies
    - Dependency Inversion: Implements domain-defined repository interface
    - Transactional Consistency: Database and filesystem operations are coordinated

Author: Course Creator Platform Team
Version: 1.0.0
Last Updated: 2025-11-09
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
import json

import asyncpg
from asyncpg import Connection, Pool

from nimcp_service.domain.entities.brain import (
    Brain,
    BrainType,
    PerformanceMetrics,
    COWStats,
    SelfAwareness
)
from nimcp_service.domain.interfaces.brain_repository import BrainRepository


class BrainPersistenceError(Exception):
    """Raised when brain persistence operations fail."""
    pass


class BrainAlreadyExistsError(BrainPersistenceError):
    """Raised when attempting to create a brain that already exists."""
    pass


class BrainNotFoundError(BrainPersistenceError):
    """Raised when brain is not found in repository."""
    pass


class BrainDAO(BrainRepository):
    """
    PostgreSQL implementation of brain repository.

    Business Responsibilities:
        - Persist brain instances to PostgreSQL database
        - Load brain instances with all related data
        - Update brain metrics and state after interactions
        - Query brains by various criteria
        - Maintain transactional consistency

    Database Schema:
        - brain_instances: Main table with brain metadata
        - brain_interactions: Interaction history (not managed by DAO directly)
        - brain_self_assessments: Meta-cognitive snapshots

    Dependencies:
        - asyncpg: Async PostgreSQL driver
        - PostgreSQL 12+: Database with JSONB support
    """

    def __init__(self, db_pool: Pool):
        """
        Initialize DAO with database connection pool.

        Args:
            db_pool: asyncpg connection pool for database operations
        """
        self.db_pool = db_pool

    async def create(self, brain: Brain) -> Brain:
        """
        Persist a new brain instance to the database.

        Business Logic:
            Creates database record with brain metadata. Does NOT create
            the .bin file - that's handled by the BrainService using NIMCP API.

        Args:
            brain: Brain entity to persist

        Returns:
            Persisted brain with confirmed ID

        Raises:
            BrainAlreadyExistsError: If brain_id already exists
            BrainPersistenceError: If database operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Check if brain already exists
                existing = await conn.fetchrow(
                    "SELECT brain_id FROM brain_instances WHERE brain_id = $1",
                    brain.brain_id
                )
                if existing:
                    raise BrainAlreadyExistsError(f"Brain {brain.brain_id} already exists")

                # Insert new brain
                await conn.execute(
                    """
                    INSERT INTO brain_instances (
                        brain_id, brain_type, owner_id, parent_brain_id,
                        created_at, last_updated, state_file_path, is_active,
                        total_interactions, neural_inference_count, llm_query_count,
                        average_confidence, average_accuracy, last_learning_timestamp,
                        is_cow_clone, cow_shared_bytes, cow_copied_bytes,
                        strong_domains, weak_domains, bias_detections, capability_boundaries
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                        $15, $16, $17, $18, $19, $20, $21
                    )
                    """,
                    brain.brain_id,
                    brain.brain_type.value,
                    brain.owner_id,
                    brain.parent_brain_id,
                    brain.created_at,
                    brain.last_updated,
                    brain.state_file_path,
                    brain.is_active,
                    brain.performance.total_interactions,
                    brain.performance.neural_inference_count,
                    brain.performance.llm_query_count,
                    brain.performance.average_confidence,
                    brain.performance.average_accuracy,
                    brain.performance.last_learning_timestamp,
                    brain.cow_stats.is_cow_clone,
                    brain.cow_stats.cow_shared_bytes,
                    brain.cow_stats.cow_copied_bytes,
                    json.dumps(brain.self_awareness.strong_domains),
                    json.dumps(brain.self_awareness.weak_domains),
                    json.dumps(brain.self_awareness.bias_detections),
                    json.dumps(brain.self_awareness.capability_boundaries)
                )

                return brain

        except BrainAlreadyExistsError:
            raise
        except Exception as e:
            raise BrainPersistenceError(f"Failed to create brain: {str(e)}") from e

    async def get_by_id(self, brain_id: UUID) -> Optional[Brain]:
        """Retrieve brain instance by unique ID."""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM brain_instances WHERE brain_id = $1",
                    brain_id
                )

                if not row:
                    return None

                return self._row_to_brain(row)

        except Exception as e:
            raise BrainPersistenceError(f"Failed to get brain {brain_id}: {str(e)}") from e

    async def get_by_owner(self, owner_id: UUID, brain_type: BrainType) -> Optional[Brain]:
        """Retrieve brain instance by owner ID and type."""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM brain_instances WHERE owner_id = $1 AND brain_type = $2",
                    owner_id,
                    brain_type.value
                )

                if not row:
                    return None

                return self._row_to_brain(row)

        except Exception as e:
            raise BrainPersistenceError(f"Failed to get brain for owner {owner_id}: {str(e)}") from e

    async def get_platform_brain(self) -> Optional[Brain]:
        """Retrieve the singleton platform brain."""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM brain_instances WHERE brain_type = $1 LIMIT 1",
                    BrainType.PLATFORM.value
                )

                if not row:
                    return None

                return self._row_to_brain(row)

        except Exception as e:
            raise BrainPersistenceError(f"Failed to get platform brain: {str(e)}") from e

    async def get_children(self, parent_brain_id: UUID) -> List[Brain]:
        """Retrieve all child brains (COW clones) of a parent brain."""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM brain_instances WHERE parent_brain_id = $1",
                    parent_brain_id
                )

                return [self._row_to_brain(row) for row in rows]

        except Exception as e:
            raise BrainPersistenceError(f"Failed to get child brains: {str(e)}") from e

    async def update(self, brain: Brain) -> Brain:
        """Update an existing brain instance with new state and metrics."""
        try:
            async with self.db_pool.acquire() as conn:
                # Check if brain exists
                existing = await conn.fetchrow(
                    "SELECT brain_id FROM brain_instances WHERE brain_id = $1",
                    brain.brain_id
                )
                if not existing:
                    raise BrainNotFoundError(f"Brain {brain.brain_id} not found")

                # Update brain
                await conn.execute(
                    """
                    UPDATE brain_instances SET
                        last_updated = $1,
                        state_file_path = $2,
                        is_active = $3,
                        total_interactions = $4,
                        neural_inference_count = $5,
                        llm_query_count = $6,
                        average_confidence = $7,
                        average_accuracy = $8,
                        last_learning_timestamp = $9,
                        is_cow_clone = $10,
                        cow_shared_bytes = $11,
                        cow_copied_bytes = $12,
                        strong_domains = $13,
                        weak_domains = $14,
                        bias_detections = $15,
                        capability_boundaries = $16
                    WHERE brain_id = $17
                    """,
                    brain.last_updated,
                    brain.state_file_path,
                    brain.is_active,
                    brain.performance.total_interactions,
                    brain.performance.neural_inference_count,
                    brain.performance.llm_query_count,
                    brain.performance.average_confidence,
                    brain.performance.average_accuracy,
                    brain.performance.last_learning_timestamp,
                    brain.cow_stats.is_cow_clone,
                    brain.cow_stats.cow_shared_bytes,
                    brain.cow_stats.cow_copied_bytes,
                    json.dumps(brain.self_awareness.strong_domains),
                    json.dumps(brain.self_awareness.weak_domains),
                    json.dumps(brain.self_awareness.bias_detections),
                    json.dumps(brain.self_awareness.capability_boundaries),
                    brain.brain_id
                )

                return brain

        except BrainNotFoundError:
            raise
        except Exception as e:
            raise BrainPersistenceError(f"Failed to update brain: {str(e)}") from e

    async def delete(self, brain_id: UUID) -> bool:
        """Delete a brain instance and its associated data."""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM brain_instances WHERE brain_id = $1",
                    brain_id
                )

                # result is like "DELETE 1" or "DELETE 0"
                rows_deleted = int(result.split()[-1])
                return rows_deleted > 0

        except Exception as e:
            raise BrainPersistenceError(f"Failed to delete brain: {str(e)}") from e

    async def deactivate(self, brain_id: UUID) -> bool:
        """Deactivate a brain instance without deleting it."""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE brain_instances
                    SET is_active = FALSE, last_updated = $1
                    WHERE brain_id = $2
                    """,
                    datetime.utcnow(),
                    brain_id
                )

                rows_updated = int(result.split()[-1])
                return rows_updated > 0

        except Exception as e:
            raise BrainPersistenceError(f"Failed to deactivate brain: {str(e)}") from e

    async def get_all_active(self, brain_type: Optional[BrainType] = None) -> List[Brain]:
        """Retrieve all active brain instances, optionally filtered by type."""
        try:
            async with self.db_pool.acquire() as conn:
                if brain_type:
                    rows = await conn.fetch(
                        "SELECT * FROM brain_instances WHERE is_active = TRUE AND brain_type = $1",
                        brain_type.value
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT * FROM brain_instances WHERE is_active = TRUE"
                    )

                return [self._row_to_brain(row) for row in rows]

        except Exception as e:
            raise BrainPersistenceError(f"Failed to get active brains: {str(e)}") from e

    async def count_by_type(self, brain_type: BrainType) -> int:
        """Count the number of brain instances of a specific type."""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT COUNT(*) as count FROM brain_instances WHERE brain_type = $1",
                    brain_type.value
                )

                return row['count'] if row else 0

        except Exception as e:
            raise BrainPersistenceError(f"Failed to count brains: {str(e)}") from e

    async def get_top_performers(self, brain_type: BrainType, limit: int = 10) -> List[Brain]:
        """Retrieve top-performing brain instances by accuracy."""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM brain_instances
                    WHERE brain_type = $1 AND is_active = TRUE
                    ORDER BY average_accuracy DESC
                    LIMIT $2
                    """,
                    brain_type.value,
                    limit
                )

                return [self._row_to_brain(row) for row in rows]

        except Exception as e:
            raise BrainPersistenceError(f"Failed to get top performers: {str(e)}") from e

    def _row_to_brain(self, row) -> Brain:
        """
        Convert database row to Brain entity.

        Business Logic:
            Reconstructs the full Brain aggregate from database row,
            including all value objects (PerformanceMetrics, COWStats, SelfAwareness).
        """
        # Parse JSONB fields
        strong_domains = json.loads(row['strong_domains']) if isinstance(row['strong_domains'], str) else row['strong_domains']
        weak_domains = json.loads(row['weak_domains']) if isinstance(row['weak_domains'], str) else row['weak_domains']
        bias_detections = json.loads(row['bias_detections']) if isinstance(row['bias_detections'], str) else row['bias_detections']
        capability_boundaries = json.loads(row['capability_boundaries']) if isinstance(row['capability_boundaries'], str) else row['capability_boundaries']

        # Reconstruct value objects
        performance = PerformanceMetrics(
            total_interactions=row['total_interactions'],
            neural_inference_count=row['neural_inference_count'],
            llm_query_count=row['llm_query_count'],
            average_confidence=row['average_confidence'],
            average_accuracy=row['average_accuracy'],
            last_learning_timestamp=row['last_learning_timestamp']
        )

        cow_stats = COWStats(
            is_cow_clone=row['is_cow_clone'],
            cow_shared_bytes=row['cow_shared_bytes'],
            cow_copied_bytes=row['cow_copied_bytes']
        )

        self_awareness = SelfAwareness(
            strong_domains=strong_domains,
            weak_domains=weak_domains,
            bias_detections=bias_detections,
            capability_boundaries=capability_boundaries
        )

        # Reconstruct brain entity
        return Brain(
            brain_id=row['brain_id'],
            brain_type=BrainType(row['brain_type']),
            owner_id=row['owner_id'],
            parent_brain_id=row['parent_brain_id'],
            created_at=row['created_at'],
            last_updated=row['last_updated'],
            state_file_path=row['state_file_path'],
            is_active=row['is_active'],
            performance=performance,
            cow_stats=cow_stats,
            self_awareness=self_awareness
        )
