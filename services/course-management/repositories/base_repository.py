"""
Base Repository

Base repository class with common database operations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncpg
from datetime import datetime
import uuid


class BaseRepository(ABC):
    """
    Base repository class with common database operations.
    
    Provides common database operations that can be shared across repositories.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize base repository.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_connection(self):
        """
        Get database connection from pool.
        
        Returns:
            Database connection context manager
        """
        if not self.db_pool:
            raise RuntimeError("Database pool not initialized")
        return self.db_pool.acquire()
    
    async def execute_query(self, query: str, *args) -> str:
        """
        Execute a database query without returning results.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Query result status
        """
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(query, *args)
                return result
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise
    
    async def fetch_one(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch a single row from the database.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Single row as asyncpg.Record or None
        """
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchrow(query, *args)
                return result
        except Exception as e:
            self.logger.error(f"Error fetching single row: {e}")
            raise
    
    async def fetch_all(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Fetch all rows from the database.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            List of rows as asyncpg.Record
        """
        try:
            async with self.get_connection() as conn:
                results = await conn.fetch(query, *args)
                return results
        except Exception as e:
            self.logger.error(f"Error fetching all rows: {e}")
            raise
    
    async def fetch_val(self, query: str, *args) -> Any:
        """
        Fetch a single value from the database.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Single value
        """
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval(query, *args)
                return result
        except Exception as e:
            self.logger.error(f"Error fetching value: {e}")
            raise
    
    async def execute_in_transaction(self, operations: List[tuple]) -> None:
        """
        Execute multiple operations in a transaction.
        
        Args:
            operations: List of (query, args) tuples
        """
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    for query, args in operations:
                        await conn.execute(query, *args)
        except Exception as e:
            self.logger.error(f"Error in transaction: {e}")
            raise
    
    def generate_uuid(self) -> str:
        """
        Generate a new UUID string.
        
        Returns:
            UUID string
        """
        return str(uuid.uuid4())
    
    def current_timestamp(self) -> datetime:
        """
        Get current timestamp.
        
        Returns:
            Current datetime
        """
        return datetime.utcnow()
    
    def parse_uuid(self, uuid_str: str) -> uuid.UUID:
        """
        Parse UUID string to UUID object.
        
        Args:
            uuid_str: UUID string
            
        Returns:
            UUID object
            
        Raises:
            ValueError: If UUID string is invalid
        """
        try:
            return uuid.UUID(uuid_str)
        except ValueError as e:
            self.logger.error(f"Invalid UUID format: {uuid_str}")
            raise ValueError(f"Invalid UUID format: {uuid_str}") from e
    
    async def count_records(self, table: str, where_clause: str = None, *args) -> int:
        """
        Count records in a table.
        
        Args:
            table: Table name
            where_clause: Optional WHERE clause
            *args: Query parameters
            
        Returns:
            Number of records
        """
        try:
            query = f"SELECT COUNT(*) FROM {table}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            count = await self.fetch_val(query, *args)
            return count or 0
        except Exception as e:
            self.logger.error(f"Error counting records in {table}: {e}")
            raise
    
    async def record_exists(self, table: str, where_clause: str, *args) -> bool:
        """
        Check if a record exists.
        
        Args:
            table: Table name
            where_clause: WHERE clause
            *args: Query parameters
            
        Returns:
            True if record exists, False otherwise
        """
        try:
            query = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {where_clause})"
            exists = await self.fetch_val(query, *args)
            return exists or False
        except Exception as e:
            self.logger.error(f"Error checking record existence in {table}: {e}")
            raise
    
    def build_update_query(self, table: str, updates: Dict[str, Any], 
                          where_clause: str) -> tuple:
        """
        Build UPDATE query from dictionary.
        
        Args:
            table: Table name
            updates: Dictionary of field updates
            where_clause: WHERE clause
            
        Returns:
            Tuple of (query, args)
        """
        if not updates:
            raise ValueError("No updates provided")
        
        set_clauses = []
        args = []
        arg_index = 1
        
        for field, value in updates.items():
            set_clauses.append(f"{field} = ${arg_index}")
            args.append(value)
            arg_index += 1
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {where_clause}"
        return query, args
    
    def build_insert_query(self, table: str, data: Dict[str, Any]) -> tuple:
        """
        Build INSERT query from dictionary.
        
        Args:
            table: Table name
            data: Dictionary of field values
            
        Returns:
            Tuple of (query, args)
        """
        if not data:
            raise ValueError("No data provided")
        
        fields = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(fields))]
        args = list(data.values())
        
        query = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        return query, args
    
    def build_search_conditions(self, search_params: Dict[str, Any]) -> tuple:
        """
        Build WHERE conditions from search parameters.
        
        Args:
            search_params: Dictionary of search parameters
            
        Returns:
            Tuple of (where_clause, args)
        """
        conditions = []
        args = []
        arg_index = 1
        
        for field, value in search_params.items():
            if value is not None:
                if isinstance(value, str) and '%' in value:
                    conditions.append(f"{field} ILIKE ${arg_index}")
                else:
                    conditions.append(f"{field} = ${arg_index}")
                args.append(value)
                arg_index += 1
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        return where_clause, args