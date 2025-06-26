"""
FastAPI dependencies for enrollment service
"""

import asyncio
from typing import AsyncGenerator
from fastapi import Depends
import asyncpg
import aioredis
from ...shared.utils.config_manager import config_manager

# Database dependency
async def get_database() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get database connection"""
    config = config_manager.get_database_config()
    
    conn = await asyncpg.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.name
    )
    
    try:
        yield conn
    finally:
        await conn.close()

# Redis dependency
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Get Redis connection"""
    config = config_manager.get_messaging_config()
    
    redis = aioredis.from_url(
        f"redis://{config.host}:{config.port}",
        password=config.password,
        db=config.db
    )
    
    try:
        yield redis
    finally:
        await redis.close()
