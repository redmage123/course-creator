"""
PostgreSQL implementation of the database abstraction layer.
"""
import asyncpg
from typing import Any, Dict, List, Optional, Type, TypeVar
from contextlib import asynccontextmanager

from .interfaces import (
    DatabaseConnection,
    DatabaseTransaction,
    BaseRepository,
    QueryBuilder,
    DatabaseFactory,
    BaseEntity
)

T = TypeVar('T', bound=BaseEntity)

class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL database connection implementation."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Establish connection pool."""
        self.pool = await asyncpg.create_pool(self.connection_string)
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def begin_transaction(self) -> 'PostgreSQLTransaction':
        """Begin a database transaction."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        connection = await self.pool.acquire()
        transaction = await connection.transaction()
        return PostgreSQLTransaction(connection, transaction, self.pool)
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as connection:
            if params:
                rows = await connection.fetch(query, *params.values())
            else:
                rows = await connection.fetch(query)
            
            return [dict(row) for row in rows]
    
    async def execute_non_query(self, query: str, params: Dict[str, Any] = None) -> int:
        """Execute a non-query statement and return affected rows."""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as connection:
            if params:
                result = await connection.execute(query, *params.values())
            else:
                result = await connection.execute(query)
            
            # Extract number from result like "INSERT 0 5" -> 5
            return int(result.split()[-1]) if result.split() else 0

class PostgreSQLTransaction(DatabaseTransaction):
    """PostgreSQL transaction implementation."""
    
    def __init__(self, connection: asyncpg.Connection, transaction: asyncpg.Transaction, pool: asyncpg.Pool):
        self.connection = connection
        self.transaction = transaction
        self.pool = pool
        self._started = False
    
    async def commit(self) -> None:
        """Commit the transaction."""
        if self._started:
            await self.transaction.commit()
    
    async def rollback(self) -> None:
        """Rollback the transaction."""
        if self._started:
            await self.transaction.rollback()
    
    async def __aenter__(self):
        """Enter transaction context."""
        await self.transaction.start()
        self._started = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context."""
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            await self.pool.release(self.connection)

class PostgreSQLQueryBuilder(QueryBuilder):
    """PostgreSQL query builder implementation."""
    
    def __init__(self):
        self._select_columns: List[str] = []
        self._from_table: Optional[str] = None
        self._where_conditions: List[str] = []
        self._joins: List[str] = []
        self._order_by_clauses: List[str] = []
        self._limit_count: Optional[int] = None
        self._offset_count: Optional[int] = None
        self._parameters: Dict[str, Any] = {}
        self._param_counter = 0
    
    def select(self, columns: List[str]) -> 'PostgreSQLQueryBuilder':
        """Add SELECT clause."""
        self._select_columns.extend(columns)
        return self
    
    def from_table(self, table: str) -> 'PostgreSQLQueryBuilder':
        """Add FROM clause."""
        self._from_table = table
        return self
    
    def where(self, condition: str, params: Dict[str, Any] = None) -> 'PostgreSQLQueryBuilder':
        """Add WHERE clause."""
        if params:
            # Replace named parameters with PostgreSQL positional parameters
            modified_condition = condition
            for key, value in params.items():
                self._param_counter += 1
                param_name = f"${self._param_counter}"
                modified_condition = modified_condition.replace(f":{key}", param_name)
                self._parameters[f"param_{self._param_counter}"] = value
            self._where_conditions.append(modified_condition)
        else:
            self._where_conditions.append(condition)
        return self
    
    def join(self, table: str, condition: str) -> 'PostgreSQLQueryBuilder':
        """Add JOIN clause."""
        self._joins.append(f"JOIN {table} ON {condition}")
        return self
    
    def order_by(self, column: str, direction: str = 'ASC') -> 'PostgreSQLQueryBuilder':
        """Add ORDER BY clause."""
        self._order_by_clauses.append(f"{column} {direction}")
        return self
    
    def limit(self, count: int) -> 'PostgreSQLQueryBuilder':
        """Add LIMIT clause."""
        self._limit_count = count
        return self
    
    def offset(self, count: int) -> 'PostgreSQLQueryBuilder':
        """Add OFFSET clause."""
        self._offset_count = count
        return self
    
    def build(self) -> tuple[str, Dict[str, Any]]:
        """Build the final query and parameters."""
        if not self._from_table:
            raise ValueError("FROM clause is required")
        
        query_parts = []
        
        # SELECT
        if self._select_columns:
            query_parts.append(f"SELECT {', '.join(self._select_columns)}")
        else:
            query_parts.append("SELECT *")
        
        # FROM
        query_parts.append(f"FROM {self._from_table}")
        
        # JOINs
        if self._joins:
            query_parts.extend(self._joins)
        
        # WHERE
        if self._where_conditions:
            query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")
        
        # ORDER BY
        if self._order_by_clauses:
            query_parts.append(f"ORDER BY {', '.join(self._order_by_clauses)}")
        
        # LIMIT
        if self._limit_count is not None:
            query_parts.append(f"LIMIT {self._limit_count}")
        
        # OFFSET
        if self._offset_count is not None:
            query_parts.append(f"OFFSET {self._offset_count}")
        
        query = " ".join(query_parts)
        return query, self._parameters

class PostgreSQLRepository(BaseRepository[T]):
    """PostgreSQL repository implementation."""
    
    def __init__(self, connection: DatabaseConnection, table_name: str, entity_class: Type[T]):
        super().__init__(connection)
        self.table_name = table_name
        self.entity_class = entity_class
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        # This is a simplified implementation
        # In practice, you'd use reflection or mapping to convert entity to SQL
        raise NotImplementedError("Specific repository implementations needed")
    
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"
        results = await self.connection.execute_query(query, {"id": entity_id})
        
        if results:
            return self._map_to_entity(results[0])
        return None
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        raise NotImplementedError("Specific repository implementations needed")
    
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        query = f"DELETE FROM {self.table_name} WHERE id = $1"
        affected_rows = await self.connection.execute_non_query(query, {"id": entity_id})
        return affected_rows > 0
    
    async def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Find all entities with optional pagination."""
        builder = PostgreSQLQueryBuilder().from_table(self.table_name)
        
        if limit:
            builder = builder.limit(limit)
        if offset:
            builder = builder.offset(offset)
        
        query, params = builder.build()
        results = await self.connection.execute_query(query, params)
        
        return [self._map_to_entity(row) for row in results]
    
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities by criteria."""
        builder = PostgreSQLQueryBuilder().from_table(self.table_name)
        
        for key, value in criteria.items():
            builder = builder.where(f"{key} = :{key}", {key: value})
        
        query, params = builder.build()
        results = await self.connection.execute_query(query, params)
        
        return [self._map_to_entity(row) for row in results]
    
    def _map_to_entity(self, row: Dict[str, Any]) -> T:
        """Map database row to entity."""
        # This is a simplified mapping - in practice you'd have more sophisticated mapping
        entity = self.entity_class()
        for key, value in row.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        return entity

class PostgreSQLFactory(DatabaseFactory):
    """PostgreSQL database factory."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def create_connection(self, config: Dict[str, Any] = None) -> DatabaseConnection:
        """Create a PostgreSQL connection."""
        connection_string = config.get('connection_string', self.connection_string) if config else self.connection_string
        return PostgreSQLConnection(connection_string)
    
    def create_query_builder(self) -> QueryBuilder:
        """Create a PostgreSQL query builder."""
        return PostgreSQLQueryBuilder()
    
    def create_repository(self, entity_type: Type[T], connection: DatabaseConnection) -> BaseRepository[T]:
        """Create a repository for the given entity type."""
        # This would need mapping configuration in practice
        table_name = getattr(entity_type, '__tablename__', entity_type.__name__.lower())
        return PostgreSQLRepository(connection, table_name, entity_type)