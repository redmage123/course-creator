"""
Organization-Aware Redis Cache with Multi-Tenant Key Isolation

BUSINESS REQUIREMENT:
Prevent cache data leakage between organizations by implementing tenant-isolated
cache keys. Ensures that no organization can access cached data from another
organization, even if cache keys are predictable or enumerable.

TECHNICAL IMPLEMENTATION:
1. Prefix all cache keys with organization_id
2. Validate organization context before cache operations
3. Implement cache key namespacing by tenant
4. Provide organization-scoped cache operations
5. Add security logging for cache access patterns

SECURITY CONSIDERATIONS:
- Prevents cross-tenant cache data access
- Blocks enumeration attacks on cache keys
- Provides audit trail for cache operations
- Implements cache-level defense-in-depth
- Validates organization context on every cache operation

WHY THIS PREVENTS CACHE LEAKAGE:
- Previous cache implementation used predictable keys without tenant isolation
- Instructors could potentially access other organizations' cached data
- Cache keys like "course:123" were globally accessible
- Now all keys are prefixed with organization_id like "org:uuid:course:123"
- Cache operations require valid organization context to proceed
"""

import logging
import json
import pickle
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class OrganizationRedisCache:
    """
    Multi-tenant Redis cache with organization-based key isolation
    
    Ensures complete data isolation between organizations by prefixing
    all cache keys with organization_id and validating access permissions.
    """
    
    def __init__(self, redis_client: redis.Redis, default_ttl: int = 3600):
        """
        Initialize organization-aware Redis cache
        
        Args:
            redis_client: Configured Redis client instance
            default_ttl: Default time-to-live for cache entries in seconds
        """
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        
        # Key prefixes for different data types
        self.key_prefixes = {
            'course': 'course',
            'user': 'user', 
            'quiz': 'quiz',
            'lab': 'lab',
            'analytics': 'analytics',
            'session': 'session',
            'content': 'content'
        }
    
    def _build_key(self, organization_id: str, key_type: str, key_id: str) -> str:
        """
        Build organization-isolated cache key
        
        KEY FORMAT: org:{organization_id}:{key_type}:{key_id}
        
        EXAMPLES:
        - org:550e8400-e29b-41d4-a716-446655440000:course:123
        - org:550e8400-e29b-41d4-a716-446655440000:user:profile:456
        - org:550e8400-e29b-41d4-a716-446655440000:quiz:attempts:789
        
        Args:
            organization_id: Organization UUID
            key_type: Type of cached data (course, user, quiz, etc.)
            key_id: Specific identifier for the cached item
            
        Returns:
            Fully qualified cache key with organization isolation
        """
        if not organization_id:
            raise ValueError("Organization ID is required for cache operations")
        
        if key_type not in self.key_prefixes:
            logger.warning(f"Unknown cache key type: {key_type}")
        
        return f"org:{organization_id}:{key_type}:{key_id}"
    
    def _validate_organization_context(self, organization_id: str) -> None:
        """
        Validate organization context for cache operations
        
        Args:
            organization_id: Organization UUID to validate
            
        Raises:
            ValueError: If organization_id is invalid or missing
        """
        if not organization_id:
            raise ValueError("Organization ID is required for cache operations")
        
        if not isinstance(organization_id, str):
            raise ValueError("Organization ID must be a string")
        
        # Basic UUID format validation
        if len(organization_id) != 36 or organization_id.count('-') != 4:
            raise ValueError("Organization ID must be a valid UUID")
    
    async def get(
        self,
        organization_id: str,
        key_type: str,
        key_id: str,
        deserialize: bool = True
    ) -> Optional[Any]:
        """
        Get cached value with organization isolation
        
        Args:
            organization_id: Organization UUID
            key_type: Type of cached data
            key_id: Specific identifier
            deserialize: Whether to deserialize JSON data
            
        Returns:
            Cached value or None if not found
        """
        try:
            self._validate_organization_context(organization_id)
            cache_key = self._build_key(organization_id, key_type, key_id)
            
            value = await self.redis_client.get(cache_key)
            if value is None:
                return None
            
            if deserialize:
                try:
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Fallback to pickle for complex objects
                    try:
                        return pickle.loads(value)
                    except pickle.PickleError:
                        logger.warning(f"Failed to deserialize cache value for key: {cache_key}")
                        return value.decode('utf-8')
            
            return value.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Cache get error for org {organization_id}: {e}")
            return None
    
    async def set(
        self,
        organization_id: str,
        key_type: str,
        key_id: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        Set cached value with organization isolation
        
        Args:
            organization_id: Organization UUID
            key_type: Type of cached data
            key_id: Specific identifier
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            serialize: Whether to serialize value as JSON
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._validate_organization_context(organization_id)
            cache_key = self._build_key(organization_id, key_type, key_id)
            
            if serialize:
                try:
                    cache_value = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    # Fallback to pickle for complex objects
                    cache_value = pickle.dumps(value)
            else:
                cache_value = str(value)
            
            ttl = ttl or self.default_ttl
            
            result = await self.redis_client.setex(cache_key, ttl, cache_value)
            
            self._log_cache_operation(
                organization_id=organization_id,
                operation='SET',
                key_type=key_type,
                key_id=key_id,
                success=bool(result)
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache set error for org {organization_id}: {e}")
            self._log_cache_operation(
                organization_id=organization_id,
                operation='SET',
                key_type=key_type,
                key_id=key_id,
                success=False,
                error=str(e)
            )
            return False
    
    async def delete(self, organization_id: str, key_type: str, key_id: str) -> bool:
        """
        Delete cached value with organization isolation
        
        Args:
            organization_id: Organization UUID
            key_type: Type of cached data
            key_id: Specific identifier
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            self._validate_organization_context(organization_id)
            cache_key = self._build_key(organization_id, key_type, key_id)
            
            result = await self.redis_client.delete(cache_key)
            
            self._log_cache_operation(
                organization_id=organization_id,
                operation='DELETE',
                key_type=key_type,
                key_id=key_id,
                success=bool(result)
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete error for org {organization_id}: {e}")
            return False
    
    async def exists(self, organization_id: str, key_type: str, key_id: str) -> bool:
        """
        Check if cached value exists with organization isolation
        
        Args:
            organization_id: Organization UUID
            key_type: Type of cached data
            key_id: Specific identifier
            
        Returns:
            True if exists, False otherwise
        """
        try:
            self._validate_organization_context(organization_id)
            cache_key = self._build_key(organization_id, key_type, key_id)
            
            result = await self.redis_client.exists(cache_key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache exists error for org {organization_id}: {e}")
            return False
    
    async def get_keys_by_pattern(
        self,
        organization_id: str,
        key_type: str,
        pattern: str = "*"
    ) -> List[str]:
        """
        Get cache keys matching pattern within organization scope
        
        SECURITY NOTE:
        This method only returns keys within the organization's namespace,
        preventing cross-tenant key enumeration attacks.
        
        Args:
            organization_id: Organization UUID
            key_type: Type of cached data
            pattern: Pattern to match (Redis glob pattern)
            
        Returns:
            List of matching cache keys (organization namespace removed)
        """
        try:
            self._validate_organization_context(organization_id)
            org_prefix = f"org:{organization_id}:{key_type}:"
            search_pattern = f"{org_prefix}{pattern}"
            
            keys = await self.redis_client.keys(search_pattern)
            
            # Remove organization prefix from returned keys
            cleaned_keys = []
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if key.startswith(org_prefix):
                    cleaned_keys.append(key[len(org_prefix):])
            
            return cleaned_keys
            
        except Exception as e:
            logger.error(f"Cache keys error for org {organization_id}: {e}")
            return []
    
    async def flush_organization_cache(self, organization_id: str) -> bool:
        """
        Delete all cached data for a specific organization
        
        SECURITY OPERATION:
        Used for organization cleanup, data compliance (GDPR), or security incidents.
        Removes all cached data associated with the organization.
        
        Args:
            organization_id: Organization UUID to flush
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._validate_organization_context(organization_id)
            org_pattern = f"org:{organization_id}:*"
            
            keys = await self.redis_client.keys(org_pattern)
            
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
                
                self._log_cache_operation(
                    organization_id=organization_id,
                    operation='FLUSH_ORG',
                    key_type='all',
                    key_id='*',
                    success=True,
                    details={'deleted_keys': deleted_count}
                )
                
                logger.info(f"Flushed {deleted_count} cache keys for organization {organization_id}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Cache flush error for org {organization_id}: {e}")
            self._log_cache_operation(
                organization_id=organization_id,
                operation='FLUSH_ORG',
                key_type='all',
                key_id='*',
                success=False,
                error=str(e)
            )
            return False
    
    async def get_organization_cache_stats(self, organization_id: str) -> Dict[str, Any]:
        """
        Get cache statistics for a specific organization
        
        Args:
            organization_id: Organization UUID
            
        Returns:
            Dictionary containing cache statistics
        """
        try:
            self._validate_organization_context(organization_id)
            org_pattern = f"org:{organization_id}:*"
            
            keys = await self.redis_client.keys(org_pattern)
            
            stats = {
                'organization_id': organization_id,
                'total_keys': len(keys),
                'key_types': {},
                'memory_usage': 0,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Analyze key types
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                
                # Extract key type from org:uuid:type:id format
                parts = key.split(':')
                if len(parts) >= 3:
                    key_type = parts[2]
                    stats['key_types'][key_type] = stats['key_types'].get(key_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Cache stats error for org {organization_id}: {e}")
            return {'error': str(e)}
    
    def _log_cache_operation(
        self,
        organization_id: str,
        operation: str,
        key_type: str,
        key_id: str,
        success: bool,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log cache operations for security monitoring and performance analysis
        
        Args:
            organization_id: Organization UUID
            operation: Cache operation type (GET, SET, DELETE, etc.)
            key_type: Type of cached data
            key_id: Specific identifier
            success: Whether operation succeeded
            error: Error message if operation failed
            details: Additional operation details
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'organization_id': organization_id,
            'operation': operation,
            'key_type': key_type,
            'key_id': key_id,
            'success': success,
            'error': error,
            'details': details or {}
        }
        
        if success:
            logger.debug(f"Cache operation {operation} succeeded", extra=log_entry)
        else:
            logger.warning(f"Cache operation {operation} failed", extra=log_entry)


class OrganizationCacheManager:
    """
    High-level cache manager providing organization-scoped cache operations
    
    Simplifies cache usage for application services while maintaining
    strict organization isolation and security controls.
    """
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """
        Initialize organization cache manager
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default cache TTL in seconds
        """
        try:
            self.redis_client = redis.from_url(redis_url)
            self.cache = OrganizationRedisCache(self.redis_client, default_ttl)
            logger.info("Organization cache manager initialized successfully")
        except RedisError as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
    
    async def cache_course_data(
        self,
        organization_id: str,
        course_id: str,
        course_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache course data with organization isolation"""
        return await self.cache.set(
            organization_id=organization_id,
            key_type='course',
            key_id=course_id,
            value=course_data,
            ttl=ttl
        )
    
    async def get_cached_course_data(
        self,
        organization_id: str,
        course_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached course data with organization isolation"""
        return await self.cache.get(
            organization_id=organization_id,
            key_type='course',
            key_id=course_id
        )
    
    async def cache_user_session(
        self,
        organization_id: str,
        user_id: str,
        session_data: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Cache user session data with organization isolation"""
        return await self.cache.set(
            organization_id=organization_id,
            key_type='session',
            key_id=user_id,
            value=session_data,
            ttl=ttl
        )
    
    async def get_cached_user_session(
        self,
        organization_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached user session data with organization isolation"""
        return await self.cache.get(
            organization_id=organization_id,
            key_type='session',
            key_id=user_id
        )
    
    async def invalidate_organization_cache(self, organization_id: str) -> bool:
        """Invalidate all cache data for an organization"""
        return await self.cache.flush_organization_cache(organization_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check
        
        Returns:
            Health status and basic metrics
        """
        try:
            # Test basic Redis connectivity
            await self.redis_client.ping()
            
            # Get Redis info
            info = await self.redis_client.info()
            
            return {
                'status': 'healthy',
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'uptime_seconds': info.get('uptime_in_seconds', 0),
                'redis_version': info.get('redis_version', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }