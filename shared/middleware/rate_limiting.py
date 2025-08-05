"""
Rate Limiting Middleware for Course Creator Platform

SECURITY PROTECTION:
Implements rate limiting to protect against abuse, brute force attacks,
and denial of service attempts. Provides configurable rate limits
per endpoint, user, and IP address.

RATE LIMITING STRATEGY:
- Token bucket algorithm for smooth rate limiting
- Redis-based storage for distributed environments
- Configurable limits per endpoint and user type
- Graceful degradation when Redis is unavailable
- Detailed logging for security monitoring

PROTECTION CATEGORIES:
1. Authentication endpoints: Strict limits to prevent brute force
2. API endpoints: Standard limits to prevent abuse  
3. Admin endpoints: Restrictive limits for sensitive operations
4. File upload endpoints: Conservative limits for resource protection
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from datetime import datetime, timedelta
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm
    
    Provides distributed rate limiting with Redis backend and configurable
    limits for different endpoint categories and user types.
    """
    
    def __init__(self, app, config: Dict[str, Any]):
        super().__init__(app)
        self.config = config
        self.redis_client = None
        self.fallback_storage = {}  # In-memory fallback
        self.logger = logging.getLogger(__name__)
        
        # Default rate limits (requests per minute)
        self.default_limits = {
            # Authentication endpoints - strict limits
            'auth_login': {'requests': 5, 'window': 60, 'burst': 10},
            'auth_register': {'requests': 3, 'window': 60, 'burst': 5},
            'auth_password_reset': {'requests': 2, 'window': 300, 'burst': 3},
            
            # API endpoints - standard limits
            'api_read': {'requests': 100, 'window': 60, 'burst': 150},
            'api_write': {'requests': 30, 'window': 60, 'burst': 50},
            'api_search': {'requests': 20, 'window': 60, 'burst': 30},
            
            # Admin endpoints - restrictive limits  
            'admin_users': {'requests': 10, 'window': 60, 'burst': 15},
            'admin_statistics': {'requests': 5, 'window': 60, 'burst': 10},
            
            # File operations - conservative limits
            'file_upload': {'requests': 5, 'window': 60, 'burst': 8},
            'file_export': {'requests': 3, 'window': 60, 'burst': 5},
            
            # Default for unclassified endpoints
            'default': {'requests': 60, 'window': 60, 'burst': 100}
        }
        
        # User type multipliers
        self.user_multipliers = {
            'admin': 2.0,      # Admins get 2x the limits
            'instructor': 1.5, # Instructors get 1.5x the limits  
            'student': 1.0     # Students get base limits
        }
        
        # Initialize Redis connection
        asyncio.create_task(self._init_redis())
    
    async def _init_redis(self):
        """Initialize Redis connection for distributed rate limiting"""
        try:
            redis_config = self.config.get('redis', {})
            if redis_config:
                self.redis_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    db=redis_config.get('db', 0),
                    decode_responses=True
                )
                await self.redis_client.ping()
                self.logger.info("Rate limiting: Redis connection established")
            else:
                self.logger.warning("Rate limiting: No Redis config, using in-memory fallback")
        except Exception as e:
            self.logger.error(f"Rate limiting: Redis connection failed: {e}")
            self.redis_client = None
    
    def _classify_endpoint(self, path: str, method: str) -> str:
        """Classify endpoint for rate limiting category"""
        path_lower = path.lower()
        
        # Authentication endpoints
        if '/auth/login' in path_lower:
            return 'auth_login'
        elif '/auth/register' in path_lower:
            return 'auth_register'
        elif '/auth/password' in path_lower:
            return 'auth_password_reset'
        
        # Admin endpoints
        elif '/admin/' in path_lower:
            if '/users' in path_lower:
                return 'admin_users'
            elif '/statistics' in path_lower:
                return 'admin_statistics'
            else:
                return 'admin_users'  # Default admin limit
        
        # File operations
        elif '/upload' in path_lower or method == 'POST' and '/content' in path_lower:
            return 'file_upload'
        elif '/export' in path_lower:
            return 'file_export'
        
        # API operations by method
        elif method in ['GET', 'HEAD']:
            if '/search' in path_lower:
                return 'api_search'
            else:
                return 'api_read'
        elif method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return 'api_write'
        
        return 'default'
    
    def _get_client_identifier(self, request: Request) -> Tuple[str, str]:
        """Get client identifier for rate limiting"""
        # Try to get user ID from JWT token
        user_id = None
        user_role = 'student'  # Default role
        
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                import jwt
                token = auth_header.split(' ')[1]
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get('sub') or payload.get('user_id')
                user_role = payload.get('role', 'student')
            except:
                pass
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else 'unknown'
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0].strip()
        
        identifier = user_id if user_id else f"ip:{client_ip}"
        return identifier, user_role
    
    async def _check_rate_limit(self, key: str, limit_config: Dict[str, int]) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using token bucket algorithm"""
        now = time.time()
        window = limit_config['window']
        max_requests = limit_config['requests']
        burst_limit = limit_config['burst']
        
        try:
            if self.redis_client:
                # Use Redis for distributed rate limiting
                pipe = self.redis_client.pipeline()
                
                # Get current bucket state
                pipe.hgetall(key)
                pipe.expire(key, window * 2)  # Keep data for 2x window
                
                result = await pipe.execute()
                bucket_data = result[0] if result[0] else {}
                
                # Initialize bucket if empty
                if not bucket_data:
                    bucket_data = {
                        'tokens': str(max_requests),
                        'last_refill': str(now),
                        'requests_made': '0'
                    }
                
                tokens = float(bucket_data.get('tokens', max_requests))
                last_refill = float(bucket_data.get('last_refill', now))
                requests_made = int(bucket_data.get('requests_made', 0))
                
                # Refill tokens based on elapsed time
                elapsed = now - last_refill
                tokens_to_add = elapsed * (max_requests / window)
                tokens = min(burst_limit, tokens + tokens_to_add)
                
                # Check if request is allowed
                if tokens >= 1:
                    tokens -= 1
                    requests_made += 1
                    allowed = True
                else:
                    allowed = False
                
                # Update bucket state
                new_bucket_data = {
                    'tokens': str(tokens),
                    'last_refill': str(now),
                    'requests_made': str(requests_made)
                }
                
                await self.redis_client.hset(key, mapping=new_bucket_data)
                await self.redis_client.expire(key, window * 2)
                
                return allowed, {
                    'allowed': allowed,
                    'tokens_remaining': int(tokens),
                    'requests_made': requests_made,
                    'reset_time': int(now + window)
                }
            
            else:
                # Fallback to in-memory storage
                if key not in self.fallback_storage:
                    self.fallback_storage[key] = {
                        'tokens': max_requests,
                        'last_refill': now,
                        'requests_made': 0
                    }
                
                bucket = self.fallback_storage[key]
                
                # Refill tokens
                elapsed = now - bucket['last_refill']
                tokens_to_add = elapsed * (max_requests / window)
                bucket['tokens'] = min(burst_limit, bucket['tokens'] + tokens_to_add)
                bucket['last_refill'] = now
                
                # Check if request is allowed
                if bucket['tokens'] >= 1:
                    bucket['tokens'] -= 1
                    bucket['requests_made'] += 1
                    allowed = True
                else:
                    allowed = False
                
                return allowed, {
                    'allowed': allowed,
                    'tokens_remaining': int(bucket['tokens']),
                    'requests_made': bucket['requests_made'],
                    'reset_time': int(now + window)
                }
                
        except Exception as e:
            self.logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {'allowed': True, 'error': str(e)}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for health checks and static files
        if request.url.path in ['/health', '/docs', '/openapi.json'] or request.url.path.startswith('/static'):
            return await call_next(request)
        
        # Get client identifier and endpoint classification
        client_id, user_role = self._get_client_identifier(request)
        endpoint_category = self._classify_endpoint(request.url.path, request.method)
        
        # Get rate limit configuration
        limit_config = self.default_limits.get(endpoint_category, self.default_limits['default']).copy()
        
        # Apply user role multiplier
        multiplier = self.user_multipliers.get(user_role, 1.0)
        limit_config['requests'] = int(limit_config['requests'] * multiplier)
        limit_config['burst'] = int(limit_config['burst'] * multiplier)
        
        # Create rate limiting key
        rate_limit_key = f"rate_limit:{endpoint_category}:{client_id}"
        
        # Check rate limit
        allowed, limit_info = await self._check_rate_limit(rate_limit_key, limit_config)
        
        if not allowed:
            # Log rate limit violation
            self.logger.warning(
                f"Rate limit exceeded: {client_id} for {endpoint_category} "
                f"({request.method} {request.url.path})"
            )
            
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": limit_config['window'],
                    "limit_info": {
                        "requests_allowed": limit_config['requests'],
                        "window_seconds": limit_config['window'],
                        "reset_time": limit_info.get('reset_time')
                    }
                },
                headers={
                    "Retry-After": str(limit_config['window']),
                    "X-RateLimit-Limit": str(limit_config['requests']),
                    "X-RateLimit-Remaining": str(limit_info.get('tokens_remaining', 0)),
                    "X-RateLimit-Reset": str(limit_info.get('reset_time', 0))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit_config['requests'])
        response.headers["X-RateLimit-Remaining"] = str(limit_info.get('tokens_remaining', 0))
        response.headers["X-RateLimit-Reset"] = str(limit_info.get('reset_time', 0))
        
        return response


def setup_rate_limiting(app, config: Dict[str, Any]):
    """Set up rate limiting middleware"""
    if config.get('rate_limiting', {}).get('enabled', True):
        app.add_middleware(RateLimitMiddleware, config=config)
        logging.getLogger(__name__).info("Rate limiting middleware enabled")
    else:
        logging.getLogger(__name__).info("Rate limiting middleware disabled by configuration")