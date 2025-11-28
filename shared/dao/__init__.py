"""
Course Creator Platform - Base DAO Framework

BUSINESS REQUIREMENT:
Provide a unified Data Access Object pattern across all microservices
to ensure consistent database operations, connection management,
and exception handling.

DESIGN PATTERN:
Abstract base DAO with common CRUD operations following:
- Repository pattern for data access abstraction
- Unit of Work pattern for transaction management
- Connection pooling for performance
- Custom exception wrapping for all database errors

USAGE:
```python
from shared.dao import BaseDAO, TransactionManager
from shared.exceptions import DAOException, DAOQueryException

class UserDAO(BaseDAO):
    def __init__(self, pool: asyncpg.Pool):
        super().__init__(pool, "users", "user-management")

    async def find_by_email(self, email: str) -> Optional[Dict]:
        try:
            return await self.find_one({"email": email})
        except Exception as e:
            raise DAOQueryException(
                message=f"Failed to find user by email",
                query_type="SELECT",
                table_name="users",
                original_exception=e,
                service_name=self.service_name
            )
```
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar, Generic
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from shared.exceptions import (
    DAOException,
    DAOConnectionException,
    DAOQueryException,
    DatabaseException
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseDAO(ABC, Generic[T]):
    """
    Abstract base class for Data Access Objects.

    RESPONSIBILITIES:
    - Manage database connection pooling
    - Provide common CRUD operations
    - Wrap all database exceptions in custom exceptions
    - Support transaction management
    - Enforce consistent error handling

    SUBCLASSES MUST:
    - Call super().__init__ with pool, table_name, service_name
    - Implement entity-specific methods
    - Use _execute_query for all database operations
    """

    def __init__(
        self,
        pool: Any,  # asyncpg.Pool or similar
        table_name: str,
        service_name: str
    ):
        """
        Initialize base DAO.

        Args:
            pool: Database connection pool
            table_name: Primary table this DAO operates on
            service_name: Name of the owning service for logging
        """
        self.pool = pool
        self.table_name = table_name
        self.service_name = service_name
        self._logger = logging.getLogger(f"{service_name}.dao.{table_name}")

    async def _execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        connection: Optional[Any] = None,
        operation: str = "query"
    ) -> Any:
        """
        Execute a database query with proper exception handling.

        DESIGN:
        All database operations should go through this method
        to ensure consistent exception wrapping and logging.

        Args:
            query: SQL query string
            params: Query parameters
            connection: Optional existing connection (for transactions)
            operation: Operation name for logging (SELECT, INSERT, etc.)

        Returns:
            Query result

        Raises:
            DAOQueryException: If query execution fails
        """
        try:
            if connection:
                return await connection.fetch(query, *params) if params else await connection.fetch(query)

            async with self.pool.acquire() as conn:
                if params:
                    return await conn.fetch(query, *params)
                return await conn.fetch(query)

        except Exception as e:
            self._logger.error(
                f"Query failed: {operation} on {self.table_name}",
                exc_info=True
            )
            raise DAOQueryException(
                message=f"Failed to execute {operation} on {self.table_name}",
                query_type=operation,
                table_name=self.table_name,
                original_exception=e,
                service_name=self.service_name
            )

    async def _execute_one(
        self,
        query: str,
        params: Optional[tuple] = None,
        connection: Optional[Any] = None,
        operation: str = "query"
    ) -> Optional[Any]:
        """
        Execute a query and return single result.

        Args:
            query: SQL query string
            params: Query parameters
            connection: Optional existing connection
            operation: Operation name for logging

        Returns:
            Single record or None
        """
        try:
            if connection:
                return await connection.fetchrow(query, *params) if params else await connection.fetchrow(query)

            async with self.pool.acquire() as conn:
                if params:
                    return await conn.fetchrow(query, *params)
                return await conn.fetchrow(query)

        except Exception as e:
            self._logger.error(
                f"Query failed: {operation} on {self.table_name}",
                exc_info=True
            )
            raise DAOQueryException(
                message=f"Failed to execute {operation} on {self.table_name}",
                query_type=operation,
                table_name=self.table_name,
                original_exception=e,
                service_name=self.service_name
            )

    async def _execute_scalar(
        self,
        query: str,
        params: Optional[tuple] = None,
        connection: Optional[Any] = None,
        operation: str = "query"
    ) -> Any:
        """
        Execute a query and return scalar value.

        Args:
            query: SQL query string
            params: Query parameters
            connection: Optional existing connection
            operation: Operation name for logging

        Returns:
            Scalar value
        """
        try:
            if connection:
                return await connection.fetchval(query, *params) if params else await connection.fetchval(query)

            async with self.pool.acquire() as conn:
                if params:
                    return await conn.fetchval(query, *params)
                return await conn.fetchval(query)

        except Exception as e:
            self._logger.error(
                f"Scalar query failed: {operation} on {self.table_name}",
                exc_info=True
            )
            raise DAOQueryException(
                message=f"Failed to execute scalar {operation} on {self.table_name}",
                query_type=operation,
                table_name=self.table_name,
                original_exception=e,
                service_name=self.service_name
            )

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions.

        USAGE:
        ```python
        async with dao.transaction() as conn:
            await dao.create(entity, connection=conn)
            await dao.update(entity, connection=conn)
        # Commits on success, rolls back on exception
        ```

        Yields:
            Database connection with active transaction
        """
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    yield connection
        except Exception as e:
            self._logger.error(
                f"Transaction failed on {self.table_name}",
                exc_info=True
            )
            raise DAOException(
                message=f"Transaction failed on {self.table_name}",
                dao_name=self.__class__.__name__,
                operation="transaction",
                entity_type=self.table_name,
                original_exception=e,
                service_name=self.service_name
            )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check database connectivity and pool health.

        Returns:
            Dictionary with health status and metrics
        """
        try:
            result = await self._execute_scalar("SELECT 1", operation="health_check")
            return {
                "healthy": result == 1,
                "table": self.table_name,
                "service": self.service_name,
                "pool_size": getattr(self.pool, 'get_size', lambda: 'N/A')(),
                "pool_free": getattr(self.pool, 'get_idle_size', lambda: 'N/A')(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "healthy": False,
                "table": self.table_name,
                "service": self.service_name,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


class CRUDMixin:
    """
    Mixin providing standard CRUD operations.

    DESIGN:
    Separates CRUD logic from base DAO to allow
    flexible composition of DAO capabilities.
    """

    async def create(
        self,
        entity: Dict[str, Any],
        connection: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new entity in the database.

        Args:
            entity: Dictionary of entity attributes
            connection: Optional transaction connection

        Returns:
            Created entity with generated ID
        """
        columns = list(entity.keys())
        values = list(entity.values())
        placeholders = [f"${i+1}" for i in range(len(values))]

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """

        result = await self._execute_one(
            query,
            tuple(values),
            connection=connection,
            operation="INSERT"
        )
        return dict(result) if result else None

    async def find_by_id(
        self,
        entity_id: Any,
        connection: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find entity by primary key.

        Args:
            entity_id: Primary key value
            connection: Optional transaction connection

        Returns:
            Entity dictionary or None if not found
        """
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"
        result = await self._execute_one(
            query,
            (entity_id,),
            connection=connection,
            operation="SELECT"
        )
        return dict(result) if result else None

    async def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        connection: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all entities with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            connection: Optional transaction connection

        Returns:
            List of entity dictionaries
        """
        query = f"SELECT * FROM {self.table_name} LIMIT $1 OFFSET $2"
        results = await self._execute_query(
            query,
            (limit, offset),
            connection=connection,
            operation="SELECT"
        )
        return [dict(r) for r in results]

    async def update(
        self,
        entity_id: Any,
        updates: Dict[str, Any],
        connection: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing entity.

        Args:
            entity_id: Primary key of entity to update
            updates: Dictionary of fields to update
            connection: Optional transaction connection

        Returns:
            Updated entity or None if not found
        """
        if not updates:
            return await self.find_by_id(entity_id, connection)

        set_clauses = [f"{k} = ${i+2}" for i, k in enumerate(updates.keys())]
        values = [entity_id] + list(updates.values())

        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE id = $1
            RETURNING *
        """

        result = await self._execute_one(
            query,
            tuple(values),
            connection=connection,
            operation="UPDATE"
        )
        return dict(result) if result else None

    async def delete(
        self,
        entity_id: Any,
        connection: Optional[Any] = None
    ) -> bool:
        """
        Delete an entity by primary key.

        Args:
            entity_id: Primary key of entity to delete
            connection: Optional transaction connection

        Returns:
            True if entity was deleted, False otherwise
        """
        query = f"DELETE FROM {self.table_name} WHERE id = $1 RETURNING id"
        result = await self._execute_one(
            query,
            (entity_id,),
            connection=connection,
            operation="DELETE"
        )
        return result is not None

    async def count(
        self,
        where: Optional[str] = None,
        params: Optional[tuple] = None,
        connection: Optional[Any] = None
    ) -> int:
        """
        Count entities matching criteria.

        Args:
            where: Optional WHERE clause (without 'WHERE' keyword)
            params: Query parameters for WHERE clause
            connection: Optional transaction connection

        Returns:
            Count of matching entities
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        if where:
            query += f" WHERE {where}"

        result = await self._execute_scalar(
            query,
            params or (),
            connection=connection,
            operation="COUNT"
        )
        return result or 0


class StandardDAO(BaseDAO, CRUDMixin):
    """
    Standard DAO with full CRUD operations.

    USAGE:
    Extend this class for DAOs that need standard CRUD operations.

    ```python
    class UserDAO(StandardDAO):
        def __init__(self, pool):
            super().__init__(pool, "users", "user-management")

        async def find_by_email(self, email: str):
            query = "SELECT * FROM users WHERE email = $1"
            return await self._execute_one(query, (email,), operation="SELECT")
    ```
    """
    pass


# Export all DAO classes
__all__ = [
    "BaseDAO",
    "CRUDMixin",
    "StandardDAO",
]
