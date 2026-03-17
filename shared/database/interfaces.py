"""
Database abstraction interfaces following SOLID principles.
This module defines the contracts for database interactions.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from datetime import datetime
import uuid

T = TypeVar('T')

class BaseEntity:
    """Base entity class with common fields."""
    def __init__(self):
        self.id: Optional[str] = None
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None

class DatabaseConnection(ABC):
    """Abstract database connection interface."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> 'DatabaseTransaction':
        """Begin a database transaction."""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        pass
    
    @abstractmethod
    async def execute_non_query(self, query: str, params: Dict[str, Any] = None) -> int:
        """Execute a non-query statement and return affected rows."""
        pass

class DatabaseTransaction(ABC):
    """Abstract database transaction interface."""
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        pass
    
    @abstractmethod
    async def __aenter__(self):
        """Enter transaction context."""
        return self
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context."""
        pass

class BaseRepository(ABC, Generic[T]):
    """Base repository interface for CRUD operations."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass
    
    @abstractmethod
    async def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Find all entities with optional pagination."""
        pass
    
    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities by criteria."""
        pass

class QueryBuilder(ABC):
    """Abstract query builder interface."""
    
    @abstractmethod
    def select(self, columns: List[str]) -> 'QueryBuilder':
        """Add SELECT clause."""
        pass
    
    @abstractmethod
    def from_table(self, table: str) -> 'QueryBuilder':
        """Add FROM clause."""
        pass
    
    @abstractmethod
    def where(self, condition: str, params: Dict[str, Any] = None) -> 'QueryBuilder':
        """Add WHERE clause."""
        pass
    
    @abstractmethod
    def join(self, table: str, condition: str) -> 'QueryBuilder':
        """Add JOIN clause."""
        pass
    
    @abstractmethod
    def order_by(self, column: str, direction: str = 'ASC') -> 'QueryBuilder':
        """Add ORDER BY clause."""
        pass
    
    @abstractmethod
    def limit(self, count: int) -> 'QueryBuilder':
        """Add LIMIT clause."""
        pass
    
    @abstractmethod
    def offset(self, count: int) -> 'QueryBuilder':
        """Add OFFSET clause."""
        pass
    
    @abstractmethod
    def build(self) -> tuple[str, Dict[str, Any]]:
        """Build the final query and parameters."""
        pass

class DatabaseFactory(ABC):
    """Abstract factory for creating database-specific implementations."""
    
    @abstractmethod
    def create_connection(self, config: Dict[str, Any]) -> DatabaseConnection:
        """Create a database connection."""
        pass
    
    @abstractmethod
    def create_query_builder(self) -> QueryBuilder:
        """Create a query builder."""
        pass
    
    @abstractmethod
    def create_repository(self, entity_type: Type[T], connection: DatabaseConnection) -> BaseRepository[T]:
        """Create a repository for the given entity type."""
        pass