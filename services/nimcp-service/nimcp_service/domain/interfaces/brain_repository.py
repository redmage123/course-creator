"""
Brain Repository Interface

This module defines the repository interface for brain persistence following
the Repository Pattern from Domain-Driven Design. The interface abstracts
data access details and provides a clean contract for brain storage operations.

Business Context:
    Brain instances must persist their neural state (weights, topology, learning
    history) across application restarts. The repository manages both database
    metadata and filesystem storage of binary neural states (.bin files).

Architectural Principles:
    - Dependency Inversion: Domain layer defines interface, infrastructure implements
    - Repository Pattern: Collection-like interface for aggregate persistence
    - Interface Segregation: Minimal, focused interface for brain operations
    - Separation of Concerns: Domain logic separate from persistence details

Author: Course Creator Platform Team
Version: 1.0.0
Last Updated: 2025-11-09
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from nimcp_service.domain.entities.brain import Brain, BrainType


class BrainRepository(ABC):
    """
    Abstract repository interface for brain persistence operations.

    Business Responsibilities:
        - Create and persist new brain instances
        - Load existing brain instances by ID or owner
        - Update brain state and metrics after learning
        - Delete or deactivate brain instances
        - Query brains by various criteria (type, owner, parent)

    Implementation Notes:
        Concrete implementations must handle:
        - Database persistence of brain metadata
        - Filesystem storage of binary neural state (.bin files)
        - Transactional consistency between DB and filesystem
        - COW clone creation with parent linking
    """

    @abstractmethod
    async def create(self, brain: Brain) -> Brain:
        """
        Persist a new brain instance to the repository.

        Business Logic:
            Creates database record with brain metadata and initializes
            empty neural state file. For COW clones, links to parent brain.

        Args:
            brain: Brain entity to persist

        Returns:
            Brain: Persisted brain with confirmed ID and file path

        Raises:
            BrainAlreadyExistsError: If brain_id already exists
            BrainPersistenceError: If database or filesystem operation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, brain_id: UUID) -> Optional[Brain]:
        """
        Retrieve brain instance by unique ID.

        Args:
            brain_id: UUID of the brain to retrieve

        Returns:
            Brain instance if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID, brain_type: BrainType) -> Optional[Brain]:
        """
        Retrieve brain instance by owner ID and type.

        Business Logic:
            Each student/instructor should have exactly one brain of each type.
            This method retrieves that brain, or None if it doesn't exist yet.

        Args:
            owner_id: UUID of the brain owner (student_id, instructor_id)
            brain_type: Type of brain to retrieve

        Returns:
            Brain instance if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_platform_brain(self) -> Optional[Brain]:
        """
        Retrieve the singleton platform brain (master orchestrator).

        Business Logic:
            There should be exactly one platform brain that controls the
            entire application. This method retrieves it.

        Returns:
            Platform brain if exists, None otherwise
        """
        pass

    @abstractmethod
    async def get_children(self, parent_brain_id: UUID) -> List[Brain]:
        """
        Retrieve all child brains (COW clones) of a parent brain.

        Business Logic:
            Used to find all student brains cloned from platform brain,
            or all sub-brains within a hierarchical structure.

        Args:
            parent_brain_id: UUID of the parent brain

        Returns:
            List of child brain instances (may be empty)
        """
        pass

    @abstractmethod
    async def update(self, brain: Brain) -> Brain:
        """
        Update an existing brain instance with new state and metrics.

        Business Logic:
            Called after every learning interaction to persist updated
            performance metrics, self-awareness data, and COW statistics.
            Neural state file is updated separately through NIMCP API.

        Args:
            brain: Brain entity with updated state

        Returns:
            Updated brain instance

        Raises:
            BrainNotFoundError: If brain_id doesn't exist
            BrainPersistenceError: If update operation fails
        """
        pass

    @abstractmethod
    async def delete(self, brain_id: UUID) -> bool:
        """
        Delete a brain instance and its associated neural state.

        Business Logic:
            Removes database record and deletes .bin file from filesystem.
            Should cascade-delete or orphan child brains depending on policy.

        Args:
            brain_id: UUID of the brain to delete

        Returns:
            True if brain was deleted, False if not found

        Raises:
            BrainPersistenceError: If deletion operation fails
        """
        pass

    @abstractmethod
    async def deactivate(self, brain_id: UUID) -> bool:
        """
        Deactivate a brain instance without deleting it.

        Business Logic:
            Marks brain as inactive (is_active=False) for soft deletion.
            Preserves neural state for potential reactivation or audit trail.

        Args:
            brain_id: UUID of the brain to deactivate

        Returns:
            True if brain was deactivated, False if not found
        """
        pass

    @abstractmethod
    async def get_all_active(self, brain_type: Optional[BrainType] = None) -> List[Brain]:
        """
        Retrieve all active brain instances, optionally filtered by type.

        Business Logic:
            Used for platform-wide analytics, monitoring, and resource management.

        Args:
            brain_type: Optional filter by brain type

        Returns:
            List of active brain instances (may be empty)
        """
        pass

    @abstractmethod
    async def count_by_type(self, brain_type: BrainType) -> int:
        """
        Count the number of brain instances of a specific type.

        Business Logic:
            Used for resource planning and capacity monitoring.

        Args:
            brain_type: Type of brains to count

        Returns:
            Integer count of brains
        """
        pass

    @abstractmethod
    async def get_top_performers(self, brain_type: BrainType, limit: int = 10) -> List[Brain]:
        """
        Retrieve top-performing brain instances by accuracy.

        Business Logic:
            Used for analytics dashboards and identifying successful learning patterns.

        Args:
            brain_type: Type of brains to query
            limit: Maximum number of results to return

        Returns:
            List of top-performing brains ordered by average_accuracy descending
        """
        pass
