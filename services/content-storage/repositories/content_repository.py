"""
Content Repository

Repository pattern implementation for content data access.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg

from models.content import Content, ContentCreate, ContentUpdate, ContentSearchRequest, ContentStatus
from models.common import BaseModel

logger = logging.getLogger(__name__)


class ContentRepository:
    """Repository for content data operations."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def create_content(self, content_data: ContentCreate, content_id: str, file_path: str, url: str) -> Optional[Content]:
        """Create new content record."""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    INSERT INTO content_storage (
                        id, filename, content_type, size, path, url, 
                        content_category, status, uploaded_by, description, 
                        tags, storage_path, is_public, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                    ) RETURNING *
                """
                
                now = datetime.utcnow()
                
                # Determine content category based on MIME type
                content_category = self._determine_content_category(content_data.content_type)
                
                row = await conn.fetchrow(
                    query,
                    content_id,
                    content_data.filename,
                    content_data.content_type,
                    content_data.size,
                    file_path,
                    url,
                    content_category,
                    ContentStatus.READY.value,
                    content_data.uploaded_by,
                    content_data.description,
                    content_data.tags,
                    file_path,
                    False,  # is_public
                    now,
                    now
                )
                
                return self._row_to_content(row) if row else None
                
        except Exception as e:
            logger.error(f"Error creating content: {e}")
            return None
    
    async def get_content_by_id(self, content_id: str) -> Optional[Content]:
        """Get content by ID."""
        try:
            async with self.db_pool.acquire() as conn:
                query = "SELECT * FROM content_storage WHERE id = $1 AND status != $2"
                row = await conn.fetchrow(query, content_id, ContentStatus.DELETED.value)
                return self._row_to_content(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting content by ID: {e}")
            return None
    
    async def get_content_by_filename(self, filename: str, uploaded_by: str = None) -> Optional[Content]:
        """Get content by filename."""
        try:
            async with self.db_pool.acquire() as conn:
                if uploaded_by:
                    query = "SELECT * FROM content_storage WHERE filename = $1 AND uploaded_by = $2 AND status != $3"
                    row = await conn.fetchrow(query, filename, uploaded_by, ContentStatus.DELETED.value)
                else:
                    query = "SELECT * FROM content_storage WHERE filename = $1 AND status != $2"
                    row = await conn.fetchrow(query, filename, ContentStatus.DELETED.value)
                    
                return self._row_to_content(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting content by filename: {e}")
            return None
    
    async def list_content(self, page: int = 1, per_page: int = 100, uploaded_by: str = None) -> List[Content]:
        """List content with pagination."""
        try:
            offset = (page - 1) * per_page
            
            async with self.db_pool.acquire() as conn:
                if uploaded_by:
                    query = """
                        SELECT * FROM content_storage 
                        WHERE uploaded_by = $1 AND status != $2 
                        ORDER BY created_at DESC 
                        LIMIT $3 OFFSET $4
                    """
                    rows = await conn.fetch(query, uploaded_by, ContentStatus.DELETED.value, per_page, offset)
                else:
                    query = """
                        SELECT * FROM content_storage 
                        WHERE status != $1 
                        ORDER BY created_at DESC 
                        LIMIT $2 OFFSET $3
                    """
                    rows = await conn.fetch(query, ContentStatus.DELETED.value, per_page, offset)
                
                return [self._row_to_content(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error listing content: {e}")
            return []
    
    async def search_content(self, search_req: ContentSearchRequest, page: int = 1, per_page: int = 100) -> List[Content]:
        """Search content with filters."""
        try:
            conditions = ["status != $1"]
            params = [ContentStatus.DELETED.value]
            param_count = 1
            
            # Build dynamic query based on search criteria
            if search_req.query:
                param_count += 1
                conditions.append(f"filename ILIKE ${param_count}")
                params.append(f"%{search_req.query}%")
            
            if search_req.content_type:
                param_count += 1
                conditions.append(f"content_type = ${param_count}")
                params.append(search_req.content_type)
            
            if search_req.content_category:
                param_count += 1
                conditions.append(f"content_category = ${param_count}")
                params.append(search_req.content_category.value)
            
            if search_req.uploaded_by:
                param_count += 1
                conditions.append(f"uploaded_by = ${param_count}")
                params.append(search_req.uploaded_by)
            
            if search_req.tags:
                param_count += 1
                conditions.append(f"tags && ${param_count}")
                params.append(search_req.tags)
            
            if search_req.size_min is not None:
                param_count += 1
                conditions.append(f"size >= ${param_count}")
                params.append(search_req.size_min)
            
            if search_req.size_max is not None:
                param_count += 1
                conditions.append(f"size <= ${param_count}")
                params.append(search_req.size_max)
            
            if search_req.uploaded_after:
                param_count += 1
                conditions.append(f"created_at >= ${param_count}")
                params.append(search_req.uploaded_after)
            
            if search_req.uploaded_before:
                param_count += 1
                conditions.append(f"created_at <= ${param_count}")
                params.append(search_req.uploaded_before)
            
            if search_req.status:
                param_count += 1
                conditions.append(f"status = ${param_count}")
                params.append(search_req.status.value)
            
            # Add pagination
            offset = (page - 1) * per_page
            param_count += 1
            limit_param = param_count
            param_count += 1
            offset_param = param_count
            
            params.extend([per_page, offset])
            
            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT * FROM content_storage 
                WHERE {where_clause} 
                ORDER BY created_at DESC 
                LIMIT ${limit_param} OFFSET ${offset_param}
            """
            
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [self._row_to_content(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []
    
    async def update_content(self, content_id: str, update_data: ContentUpdate) -> Optional[Content]:
        """Update content record."""
        try:
            update_fields = []
            params = []
            param_count = 0
            
            if update_data.filename is not None:
                param_count += 1
                update_fields.append(f"filename = ${param_count}")
                params.append(update_data.filename)
            
            if update_data.description is not None:
                param_count += 1
                update_fields.append(f"description = ${param_count}")
                params.append(update_data.description)
            
            if update_data.tags is not None:
                param_count += 1
                update_fields.append(f"tags = ${param_count}")
                params.append(update_data.tags)
            
            if update_data.metadata is not None:
                param_count += 1
                update_fields.append(f"metadata = ${param_count}")
                params.append(update_data.metadata)
            
            if update_data.status is not None:
                param_count += 1
                update_fields.append(f"status = ${param_count}")
                params.append(update_data.status.value)
            
            if not update_fields:
                return await self.get_content_by_id(content_id)
            
            # Always update the updated_at timestamp
            param_count += 1
            update_fields.append(f"updated_at = ${param_count}")
            params.append(datetime.utcnow())
            
            # Add content_id as last parameter
            param_count += 1
            params.append(content_id)
            
            query = f"""
                UPDATE content_storage 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
                RETURNING *
            """
            
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                return self._row_to_content(row) if row else None
                
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            return None
    
    async def delete_content(self, content_id: str) -> bool:
        """Soft delete content (mark as deleted)."""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    UPDATE content_storage 
                    SET status = $1, updated_at = $2 
                    WHERE id = $3 AND status != $1
                    RETURNING id
                """
                row = await conn.fetchrow(query, ContentStatus.DELETED.value, datetime.utcnow(), content_id)
                return row is not None
                
        except Exception as e:
            logger.error(f"Error deleting content: {e}")
            return False
    
    async def hard_delete_content(self, content_id: str) -> bool:
        """Hard delete content record."""
        try:
            async with self.db_pool.acquire() as conn:
                query = "DELETE FROM content_storage_storage WHERE id = $1 RETURNING id"
                row = await conn.fetchrow(query, content_id)
                return row is not None
                
        except Exception as e:
            logger.error(f"Error hard deleting content: {e}")
            return False
    
    async def update_access_count(self, content_id: str) -> bool:
        """Update content access count and timestamp."""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    UPDATE content_storage 
                    SET access_count = access_count + 1, last_accessed = $1, updated_at = $1
                    WHERE id = $2
                    RETURNING id
                """
                row = await conn.fetchrow(query, datetime.utcnow(), content_id)
                return row is not None
                
        except Exception as e:
            logger.error(f"Error updating access count: {e}")
            return False
    
    async def get_content_stats(self, uploaded_by: str = None) -> Dict[str, Any]:
        """Get content statistics."""
        try:
            async with self.db_pool.acquire() as conn:
                base_condition = "status != $1"
                params = [ContentStatus.DELETED.value]
                
                if uploaded_by:
                    base_condition += " AND uploaded_by = $2"
                    params.append(uploaded_by)
                
                # Total stats
                stats_query = f"""
                    SELECT 
                        COUNT(*) as total_files,
                        COALESCE(SUM(size), 0) as total_size,
                        COALESCE(AVG(size), 0) as average_file_size
                    FROM content_storage 
                    WHERE {base_condition}
                """
                
                stats_row = await conn.fetchrow(stats_query, *params)
                
                # Files by type
                type_query = f"""
                    SELECT content_type, COUNT(*) as count
                    FROM content_storage 
                    WHERE {base_condition}
                    GROUP BY content_type
                """
                
                type_rows = await conn.fetch(type_query, *params)
                
                # Files by category
                category_query = f"""
                    SELECT content_category, COUNT(*) as count
                    FROM content_storage 
                    WHERE {base_condition}
                    GROUP BY content_category
                """
                
                category_rows = await conn.fetch(category_query, *params)
                
                # Most accessed files
                accessed_query = f"""
                    SELECT filename, access_count, last_accessed
                    FROM content_storage 
                    WHERE {base_condition}
                    ORDER BY access_count DESC, last_accessed DESC
                    LIMIT 10
                """
                
                accessed_rows = await conn.fetch(accessed_query, *params)
                
                return {
                    "total_files": stats_row["total_files"],
                    "total_size": stats_row["total_size"],
                    "average_file_size": float(stats_row["average_file_size"]),
                    "files_by_type": {row["content_type"]: row["count"] for row in type_rows},
                    "files_by_category": {row["content_category"]: row["count"] for row in category_rows},
                    "most_accessed_files": [
                        {
                            "filename": row["filename"],
                            "access_count": row["access_count"],
                            "last_accessed": row["last_accessed"]
                        }
                        for row in accessed_rows
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting content stats: {e}")
            return {}
    
    async def count_content(self, uploaded_by: str = None) -> int:
        """Count total content records."""
        try:
            async with self.db_pool.acquire() as conn:
                if uploaded_by:
                    query = "SELECT COUNT(*) FROM content_storage WHERE uploaded_by = $1 AND status != $2"
                    row = await conn.fetchrow(query, uploaded_by, ContentStatus.DELETED.value)
                else:
                    query = "SELECT COUNT(*) FROM content_storage WHERE status != $1"
                    row = await conn.fetchrow(query, ContentStatus.DELETED.value)
                    
                return row["count"] if row else 0
                
        except Exception as e:
            logger.error(f"Error counting content: {e}")
            return 0
    
    def _determine_content_category(self, content_type: str) -> str:
        """Determine content category from MIME type."""
        content_type = content_type.lower()
        
        if content_type.startswith('image/'):
            return 'image'
        elif content_type.startswith('video/'):
            return 'video'
        elif content_type.startswith('audio/'):
            return 'audio'
        elif content_type in ['application/pdf', 'application/msword', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'document'
        elif content_type in ['application/zip', 'application/x-tar', 'application/gzip']:
            return 'archive'
        else:
            return 'other'
    
    def _row_to_content(self, row: asyncpg.Record) -> Content:
        """Convert database row to Content model."""
        return Content(
            id=row["id"],
            filename=row["filename"],
            content_type=row["content_type"],
            size=row["size"],
            path=row["path"],
            url=row["url"],
            content_category=row["content_category"],
            status=row["status"],
            uploaded_by=row["uploaded_by"],
            description=row["description"],
            tags=row["tags"] or [],
            storage_path=row["storage_path"],
            is_public=row["is_public"],
            access_count=row["access_count"] or 0,
            last_accessed=row["last_accessed"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            access_permissions=row.get("access_permissions", []) or [],
            backup_path=row.get("backup_path"),
            storage_backend=row.get("storage_backend", "local"),
            metadata=row.get("metadata", {}) or {}
        )