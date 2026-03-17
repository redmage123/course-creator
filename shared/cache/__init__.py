"""
Shared Caching Infrastructure for Course Creator Platform

This module provides centralized caching capabilities across all platform services,
implementing Redis-based memoization for performance optimization of expensive operations.

Available Components:
    - RedisCacheManager: Core caching functionality
    - memoize_async: Decorator for automatic function memoization
    - Cache initialization and management utilities

Usage:
    from shared.cache import RedisCacheManager, memoize_async, get_cache_manager
"""

from .redis_cache import (
    RedisCacheManager,
    memoize_async,
    get_cache_manager,
    initialize_cache_manager
)

__all__ = [
    'RedisCacheManager',
    'memoize_async', 
    'get_cache_manager',
    'initialize_cache_manager'
]