"""
Base Repository

Provides common database operations and connection management for all repositories.
Implements the Repository pattern with async database operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import asyncpg
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    Base repository class providing common database operations.
    
    Following the Repository pattern, this class encapsulates database access
    and provides a consistent interface for data operations.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize repository with database connection pool.
        
        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute_query(self, query: str, *args) -> None:
        """
        Execute a query without returning results.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Raises:
            Exception: If query execution fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *args)
                self.logger.debug(f"Executed query: {query}")
        except Exception as e:
            self.logger.error(f"Query execution failed: {query}, Error: {e}")
            raise
    
    async def fetch_one(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch a single record from the database.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Single database record or None
            
        Raises:
            Exception: If query execution fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *args)
                self.logger.debug(f"Fetched one record: {query}")
                return result
        except Exception as e:
            self.logger.error(f"Fetch one failed: {query}, Error: {e}")
            raise
    
    async def fetch_all(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Fetch all records from the database.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            List of database records
            
        Raises:
            Exception: If query execution fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *args)
                self.logger.debug(f"Fetched {len(results)} records: {query}")
                return results
        except Exception as e:
            self.logger.error(f"Fetch all failed: {query}, Error: {e}")
            raise
    
    async def upsert(self, table: str, data: Dict[str, Any], 
                    conflict_columns: List[str]) -> None:
        """
        Insert or update a record in the database.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
            conflict_columns: Columns to check for conflicts
            
        Raises:
            Exception: If upsert operation fails
        """
        try:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = [f"${i+1}" for i in range(len(values))]
            
            # Build the conflict resolution part
            conflict_clause = ", ".join(conflict_columns)
            update_clause = ", ".join([
                f"{col} = EXCLUDED.{col}" 
                for col in columns if col not in conflict_columns
            ])
            
            query = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT ({conflict_clause})
                DO UPDATE SET {update_clause}
            """
            
            await self.execute_query(query, *values)
            self.logger.debug(f"Upserted record in {table}")
            
        except Exception as e:
            self.logger.error(f"Upsert failed for table {table}: {e}")
            raise
    
    async def soft_delete(self, table: str, condition: str, *args) -> None:
        """
        Perform a soft delete by setting deleted_at timestamp.
        
        Args:
            table: Table name
            condition: WHERE clause condition
            *args: Query parameters
            
        Raises:
            Exception: If soft delete fails
        """
        try:
            query = f"""
                UPDATE {table} 
                SET deleted_at = $1 
                WHERE {condition} AND deleted_at IS NULL
            """
            await self.execute_query(query, datetime.utcnow(), *args)
            self.logger.debug(f"Soft deleted from {table}")
        except Exception as e:
            self.logger.error(f"Soft delete failed for table {table}: {e}")
            raise
    
    async def check_exists(self, table: str, condition: str, *args) -> bool:
        """
        Check if a record exists in the database.
        
        Args:
            table: Table name
            condition: WHERE clause condition
            *args: Query parameters
            
        Returns:
            True if record exists, False otherwise
            
        Raises:
            Exception: If check fails
        """
        try:
            query = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {condition})"
            result = await self.fetch_one(query, *args)
            return result[0] if result else False
        except Exception as e:
            self.logger.error(f"Existence check failed for table {table}: {e}")
            raise
    
    async def get_connection(self) -> asyncpg.Connection:
        """
        Get a database connection from the pool.
        
        Returns:
            Database connection
            
        Note:
            Remember to release the connection back to the pool
        """
        return await self.db_pool.acquire()
    
    def release_connection(self, conn: asyncpg.Connection) -> None:
        """
        Release a database connection back to the pool.
        
        Args:
            conn: Database connection to release
        """
        self.db_pool.release(conn)