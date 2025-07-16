"""
Base repository class for Content Management Service.

This module provides the abstract base repository class that all
specific repositories should inherit from, following the Repository pattern.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime
import asyncpg
import json
import uuid

from pydantic import BaseModel
from models.common import PaginatedResponse

T = TypeVar('T', bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository class"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Get the table name for this repository"""
        pass
    
    @abstractmethod
    def _row_to_model(self, row: asyncpg.Record) -> T:
        """Convert database row to model"""
        pass
    
    @abstractmethod
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """Convert model to dictionary for database storage"""
        pass
    
    async def create(self, model: T) -> T:
        """Create a new record"""
        data = self._model_to_dict(model)
        
        # Generate ID if not provided
        if 'id' not in data or data['id'] is None:
            data['id'] = str(uuid.uuid4())
        
        # Set timestamps
        now = datetime.utcnow()
        data['created_at'] = now
        data['updated_at'] = now
        
        # Build insert query
        columns = list(data.keys())
        placeholders = [f'${i+1}' for i in range(len(columns))]
        values = [data[col] for col in columns]
        
        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            return self._row_to_model(row)
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get record by ID"""
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, id)
            return self._row_to_model(row) if row else None
    
    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[T]:
        """Update record by ID"""
        if not updates:
            return await self.get_by_id(id)
        
        # Add updated_at timestamp
        updates['updated_at'] = datetime.utcnow()
        
        # Build update query
        set_clauses = [f"{col} = ${i+1}" for i, col in enumerate(updates.keys())]
        values = list(updates.values()) + [id]
        
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE id = ${len(values)}
            RETURNING *
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            return self._row_to_model(row) if row else None
    
    async def delete(self, id: str) -> bool:
        """Delete record by ID"""
        query = f"DELETE FROM {self.table_name} WHERE id = $1"
        
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(query, id)
            return result.split()[-1] == '1'
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all records with pagination"""
        query = f"""
            SELECT * FROM {self.table_name}
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, limit, offset)
            return [self._row_to_model(row) for row in rows]
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters"""
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        values = []
        
        if filters:
            where_clauses = []
            for i, (key, value) in enumerate(filters.items()):
                where_clauses.append(f"{key} = ${i+1}")
                values.append(value)
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(query, *values)
            return result
    
    async def find_by_field(self, field: str, value: Any) -> List[T]:
        """Find records by field value"""
        query = f"SELECT * FROM {self.table_name} WHERE {field} = $1"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, value)
            return [self._row_to_model(row) for row in rows]
    
    async def find_by_filters(self, filters: Dict[str, Any], 
                            limit: int = 100, offset: int = 0) -> List[T]:
        """Find records by multiple filters"""
        if not filters:
            return await self.list_all(limit, offset)
        
        where_clauses = []
        values = []
        
        for i, (key, value) in enumerate(filters.items()):
            where_clauses.append(f"{key} = ${i+1}")
            values.append(value)
        
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' AND '.join(where_clauses)}
            ORDER BY created_at DESC
            LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}
        """
        
        values.extend([limit, offset])
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *values)
            return [self._row_to_model(row) for row in rows]
    
    async def search(self, query: str, fields: List[str], 
                    limit: int = 100, offset: int = 0) -> List[T]:
        """Search records by text query in specified fields"""
        search_clauses = []
        values = [f"%{query}%"] * len(fields)
        
        for i, field in enumerate(fields):
            search_clauses.append(f"{field} ILIKE ${i+1}")
        
        sql_query = f"""
            SELECT * FROM {self.table_name}
            WHERE {' OR '.join(search_clauses)}
            ORDER BY created_at DESC
            LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}
        """
        
        values.extend([limit, offset])
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(sql_query, *values)
            return [self._row_to_model(row) for row in rows]
    
    async def get_paginated(self, page: int = 1, page_size: int = 50,
                           filters: Optional[Dict[str, Any]] = None) -> PaginatedResponse:
        """Get paginated results"""
        offset = (page - 1) * page_size
        
        # Get total count
        total_count = await self.count(filters)
        
        # Get items
        if filters:
            items = await self.find_by_filters(filters, page_size, offset)
        else:
            items = await self.list_all(page_size, offset)
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=items,
            total_count=total_count,
            page_size=page_size,
            current_page=page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    async def exists(self, id: str) -> bool:
        """Check if record exists"""
        query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE id = $1)"
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(query, id)
            return result
    
    async def bulk_create(self, models: List[T]) -> List[T]:
        """Create multiple records"""
        if not models:
            return []
        
        created_models = []
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for model in models:
                    data = self._model_to_dict(model)
                    
                    # Generate ID if not provided
                    if 'id' not in data or data['id'] is None:
                        data['id'] = str(uuid.uuid4())
                    
                    # Set timestamps
                    now = datetime.utcnow()
                    data['created_at'] = now
                    data['updated_at'] = now
                    
                    # Build insert query
                    columns = list(data.keys())
                    placeholders = [f'${i+1}' for i in range(len(columns))]
                    values = [data[col] for col in columns]
                    
                    query = f"""
                        INSERT INTO {self.table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        RETURNING *
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    created_models.append(self._row_to_model(row))
        
        return created_models
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> List[T]:
        """Update multiple records"""
        if not updates:
            return []
        
        updated_models = []
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for update_data in updates:
                    if 'id' not in update_data:
                        continue
                    
                    record_id = update_data.pop('id')
                    update_data['updated_at'] = datetime.utcnow()
                    
                    # Build update query
                    set_clauses = [f"{col} = ${i+1}" for i, col in enumerate(update_data.keys())]
                    values = list(update_data.values()) + [record_id]
                    
                    query = f"""
                        UPDATE {self.table_name}
                        SET {', '.join(set_clauses)}
                        WHERE id = ${len(values)}
                        RETURNING *
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    if row:
                        updated_models.append(self._row_to_model(row))
        
        return updated_models
    
    async def bulk_delete(self, ids: List[str]) -> int:
        """Delete multiple records"""
        if not ids:
            return 0
        
        placeholders = [f'${i+1}' for i in range(len(ids))]
        query = f"DELETE FROM {self.table_name} WHERE id IN ({', '.join(placeholders)})"
        
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(query, *ids)
            return int(result.split()[-1])
    
    def _serialize_json_fields(self, data: Dict[str, Any], json_fields: List[str]) -> Dict[str, Any]:
        """Serialize JSON fields for database storage"""
        for field in json_fields:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field])
        return data
    
    def _deserialize_json_fields(self, data: Dict[str, Any], json_fields: List[str]) -> Dict[str, Any]:
        """Deserialize JSON fields from database"""
        for field in json_fields:
            if field in data and data[field] is not None:
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    data[field] = None
        return data