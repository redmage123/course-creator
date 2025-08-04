"""
Database Configuration

Database connection and configuration management.
"""

import logging
import asyncpg
from typing import Optional
from omegaconf import DictConfig
from exceptions import (
    ContentStorageException,
    DatabaseException,
    ConfigurationException
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self, config: DictConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> asyncpg.Pool:
        """Create database connection pool."""
        try:
            # Use URL directly if available, otherwise build from components
            if hasattr(self.config.database, 'url'):
                database_url = self.config.database.url
            else:
                database_url = self._build_database_url()
            
            # Default connection pool settings
            min_size = getattr(self.config.database, 'min_connections', 5)
            max_size = getattr(self.config.database, 'max_connections', 20)
            command_timeout = getattr(self.config.database, 'command_timeout', 60)
            
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=command_timeout,
                server_settings={
                    'jit': 'off'
                }
            )
            
            logger.info("Database pool created successfully")
            return self.pool
            
        except asyncpg.PostgreSQLError as e:
            raise DatabaseException(
                message=f"PostgreSQL error while creating database pool: Failed to establish database connection",
                operation="create_database_pool",
                original_exception=e
            )
        except Exception as e:
            raise ConfigurationException(
                message=f"Database configuration error: Unable to create database connection pool",
                config_key="database",
                config_section="database_connection",
                original_exception=e
            )
    
    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    async def create_tables(self):
        """Create database tables."""
        try:
            async with self.pool.acquire() as conn:
                # Check if the content table already exists with the correct structure
                result = await conn.fetchrow('''
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'content' AND column_name = 'filename'
                ''')
                
                if result is None:
                    # Table doesn't exist or doesn't have the expected schema
                    # Create the content_storage table with a different name to avoid conflicts
                    await conn.execute('''
                        CREATE TABLE IF NOT EXISTS content_storage (
                            id VARCHAR PRIMARY KEY,
                            filename VARCHAR NOT NULL,
                            content_type VARCHAR NOT NULL,
                            size INTEGER NOT NULL,
                            path VARCHAR NOT NULL,
                            url VARCHAR NOT NULL,
                            content_category VARCHAR NOT NULL,
                            status VARCHAR NOT NULL DEFAULT 'ready',
                            uploaded_by VARCHAR,
                            description TEXT,
                            tags TEXT[] DEFAULT '{}',
                            metadata JSONB DEFAULT '{}',
                            storage_path VARCHAR NOT NULL,
                            storage_backend VARCHAR DEFAULT 'local',
                            backup_path VARCHAR,
                            is_public BOOLEAN DEFAULT FALSE,
                            access_permissions TEXT[] DEFAULT '{}',
                            access_count INTEGER DEFAULT 0,
                            last_accessed TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                else:
                    # Table exists with the correct structure
                    pass
                
                # Create storage quotas table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS storage_quotas (
                        user_id VARCHAR PRIMARY KEY,
                        quota_limit BIGINT NOT NULL,
                        quota_used BIGINT DEFAULT 0,
                        file_count_limit INTEGER,
                        file_count_used INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create storage operations table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS storage_operations (
                        id VARCHAR PRIMARY KEY,
                        operation_type VARCHAR NOT NULL,
                        file_path VARCHAR NOT NULL,
                        status VARCHAR NOT NULL,
                        size BIGINT,
                        duration REAL,
                        error_message TEXT,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_content_storage_filename ON content_storage(filename);
                ''')
                
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_content_storage_uploaded_by ON content_storage(uploaded_by);
                ''')
                
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_content_storage_status ON content_storage(status);
                ''')
                
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_content_storage_category ON content_storage(content_category);
                ''')
                
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_content_storage_created_at ON content_storage(created_at);
                ''')
                
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_storage_operations_created_at ON storage_operations(created_at);
                ''')
                
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_storage_operations_status ON storage_operations(status);
                ''')
                
                logger.info("Database tables created successfully")
                
        except asyncpg.PostgreSQLError as e:
            raise DatabaseException(
                message=f"PostgreSQL error while creating database tables: Failed to execute table creation DDL",
                operation="create_database_tables",
                original_exception=e
            )
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to create database tables: Unable to initialize database schema",
                operation="create_database_tables",
                original_exception=e
            )
    
    def _build_database_url(self) -> str:
        """Build database URL from configuration."""
        return (
            f"postgresql://{self.config.database.username}:"
            f"{self.config.database.password}@"
            f"{self.config.database.host}:"
            f"{self.config.database.port}/"
            f"{self.config.database.name}"
        )