"""
Base Repository

Base repository class with common database operations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import databases
import sqlalchemy


class BaseRepository(ABC):
    """
    Base repository class with common database operations.
    
    Provides common database operations that can be shared across repositories.
    """
    
    def __init__(self, database: databases.Database):
        """
        Initialize base repository.
        
        Args:
            database: Database connection instance
        """
        self.database = database
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute_query(self, query: str, *args) -> None:
        """
        Execute a database query without returning results.
        
        Args:
            query: SQL query string
            *args: Query parameters
        """
        try:
            await self.database.execute(query, args)
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise
    
    async def fetch_one(self, query: str, *args) -> Optional[dict]:
        """
        Fetch a single row from the database.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Single row as dictionary or None
        """
        try:
            result = await self.database.fetch_one(query, args)
            return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Error fetching single row: {e}")
            raise
    
    async def fetch_all(self, query: str, *args) -> List[dict]:
        """
        Fetch all rows from the database.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            List of rows as dictionaries
        """
        try:
            results = await self.database.fetch_all(query, args)
            return [dict(row) for row in results]
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
            return await self.database.fetch_val(query, args)
        except Exception as e:
            self.logger.error(f"Error fetching value: {e}")
            raise
    
    async def upsert(self, table: sqlalchemy.Table, data: Dict[str, Any], 
                    conflict_columns: List[str]) -> None:
        """
        Insert or update a record.
        
        Args:
            table: SQLAlchemy table object
            data: Data to insert/update
            conflict_columns: Columns to check for conflicts
        """
        try:
            # Build insert query
            insert_query = table.insert().values(**data)
            
            # Build update data (exclude conflict columns)
            update_data = {k: v for k, v in data.items() if k not in conflict_columns}
            
            if update_data:
                # PostgreSQL upsert
                upsert_query = insert_query.on_conflict_do_update(
                    index_elements=conflict_columns,
                    set_=update_data
                )
            else:
                # Just insert if no update data
                upsert_query = insert_query.on_conflict_do_nothing(
                    index_elements=conflict_columns
                )
            
            await self.database.execute(upsert_query)
            
        except Exception as e:
            self.logger.error(f"Error in upsert operation: {e}")
            raise
    
    async def transaction(self):
        """
        Get a database transaction context.
        
        Returns:
            Database transaction context
        """
        return self.database.transaction()
    
    async def execute_in_transaction(self, queries: List[tuple]) -> None:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, args) tuples
        """
        try:
            async with self.database.transaction():
                for query, args in queries:
                    await self.database.execute(query, args)
        except Exception as e:
            self.logger.error(f"Error in transaction: {e}")
            raise