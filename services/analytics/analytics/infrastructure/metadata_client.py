"""
Metadata Service Client for Analytics Service

BUSINESS REQUIREMENT:
Integrate metadata service with analytics to provide enriched insights
about content, courses, and learning patterns.

TECHNICAL IMPLEMENTATION:
- HTTP client for metadata service API
- Async operations for non-blocking analytics
- Caching layer for performance optimization
- Error handling with graceful degradation

WHY:
Combining metadata with analytics provides deeper insights into:
- Content effectiveness by topic/difficulty
- Learning path optimization
- Content gap identification
- Search pattern analysis
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MetadataServiceClient:
    """
    Client for interacting with metadata service from analytics

    BUSINESS VALUE:
    - Enriches analytics with course metadata (topics, difficulty, tags)
    - Enables content-driven insights and recommendations
    - Supports intelligent search pattern analysis
    """

    def __init__(self, base_url: str = "https://localhost:8011/api/v1/metadata"):
        self.base_url = base_url
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP session

        WHY: Reuse connection for better performance
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and params"""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}?{param_str}"

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_data
            else:
                del self.cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, data: Any):
        """Set value in cache with timestamp"""
        self.cache[cache_key] = (data, datetime.now())

    async def search_metadata(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        required_tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search metadata using full-text search

        BUSINESS USE CASE:
        Analytics can search for courses by topic to enrich
        activity data with course metadata

        Args:
            query: Search query text
            entity_types: Filter by entity types (course, content, etc.)
            required_tags: Filter by required tags
            limit: Maximum results

        Returns:
            List of metadata records matching search
        """
        cache_key = self._get_cache_key('search', {
            'query': query,
            'entity_types': str(entity_types),
            'required_tags': str(required_tags),
            'limit': limit
        })

        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "entity_types": entity_types,
                    "required_tags": required_tags,
                    "limit": limit
                }
            ) as response:
                if response.status == 200:
                    results = await response.json()
                    self._set_cache(cache_key, results)
                    return results
                else:
                    logger.error(f"Metadata search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching metadata: {e}")
            return []

    async def get_by_entity(
        self,
        entity_id: str,
        entity_type: str
    ) -> Optional[Dict]:
        """
        Get metadata for specific entity

        BUSINESS USE CASE:
        Enrich course analytics with metadata (topics, difficulty, duration)

        Args:
            entity_id: Entity UUID
            entity_type: Type of entity (course, content, etc.)

        Returns:
            Metadata record or None if not found
        """
        cache_key = self._get_cache_key(f'entity/{entity_id}', {'entity_type': entity_type})

        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/entity/{entity_id}",
                params={"entity_type": entity_type}
            ) as response:
                if response.status == 200:
                    metadata = await response.json()
                    self._set_cache(cache_key, metadata)
                    return metadata
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"Failed to get metadata: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting metadata for {entity_id}: {e}")
            return None

    async def get_by_tags(
        self,
        tags: List[str],
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get metadata by tags

        BUSINESS USE CASE:
        Find all courses with specific tags for analytics grouping
        (e.g., all "python" courses, all "beginner" content)

        Args:
            tags: List of required tags
            entity_type: Optional entity type filter
            limit: Maximum results

        Returns:
            List of metadata records with matching tags
        """
        cache_key = self._get_cache_key(f'tags/{",".join(tags)}', {
            'entity_type': entity_type or '',
            'limit': limit
        })

        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            session = await self._get_session()
            params = {"limit": limit}
            if entity_type:
                params["entity_type"] = entity_type

            async with session.get(
                f"{self.base_url}/tags/{','.join(tags)}",
                params=params
            ) as response:
                if response.status == 200:
                    results = await response.json()
                    self._set_cache(cache_key, results)
                    return results
                else:
                    logger.error(f"Failed to get by tags: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting by tags: {e}")
            return []

    async def get_popular_tags(
        self,
        entity_type: str = 'course',
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get popular tags for analytics

        BUSINESS USE CASE:
        Identify trending topics and content areas

        Args:
            entity_type: Type of entity to analyze
            limit: Maximum tags to return

        Returns:
            List of {tag, count} dictionaries sorted by popularity
        """
        try:
            # Get all metadata of this type
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/type/{entity_type}",
                params={"limit": 1000}
            ) as response:
                if response.status != 200:
                    return []

                metadata_list = await response.json()

                # Count tag frequencies
                tag_counts = {}
                for item in metadata_list:
                    for tag in item.get('tags', []):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Sort by frequency
                popular_tags = [
                    {"tag": tag, "count": count}
                    for tag, count in sorted(
                        tag_counts.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:limit]
                ]

                return popular_tags

        except Exception as e:
            logger.error(f"Error getting popular tags: {e}")
            return []

    async def enrich_analytics_data(
        self,
        analytics_data: Dict,
        entity_id_key: str = 'course_id'
    ) -> Dict:
        """
        Enrich analytics data with metadata

        BUSINESS USE CASE:
        Add metadata context to analytics results for richer insights

        Args:
            analytics_data: Raw analytics data
            entity_id_key: Key containing entity ID in analytics data

        Returns:
            Analytics data enriched with metadata
        """
        try:
            entity_id = analytics_data.get(entity_id_key)
            if not entity_id:
                return analytics_data

            # Get metadata for entity
            metadata = await self.get_by_entity(entity_id, 'course')

            if metadata:
                # Add metadata fields to analytics
                enriched = {
                    **analytics_data,
                    'metadata': {
                        'title': metadata.get('title'),
                        'description': metadata.get('description'),
                        'tags': metadata.get('tags', []),
                        'topics': metadata.get('metadata', {}).get('educational', {}).get('topics', []),
                        'difficulty': metadata.get('metadata', {}).get('educational', {}).get('difficulty'),
                        'duration': metadata.get('metadata', {}).get('educational', {}).get('duration')
                    }
                }
                return enriched

            return analytics_data

        except Exception as e:
            logger.error(f"Error enriching analytics data: {e}")
            return analytics_data

    async def analyze_content_gaps(
        self,
        active_courses: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze content gaps using metadata

        BUSINESS USE CASE:
        Identify underrepresented topics and difficulty levels
        to guide content creation

        Args:
            active_courses: List of active course IDs

        Returns:
            Gap analysis with recommendations
        """
        try:
            # Get metadata for all active courses
            course_metadata = []
            for course_id in active_courses:
                metadata = await self.get_by_entity(course_id, 'course')
                if metadata:
                    course_metadata.append(metadata)

            # Analyze difficulty distribution
            difficulty_counts = {}
            topic_counts = {}

            for metadata in course_metadata:
                difficulty = metadata.get('metadata', {}).get('educational', {}).get('difficulty', 'beginner')
                difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

                topics = metadata.get('metadata', {}).get('educational', {}).get('topics', [])
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # Identify gaps
            total = len(course_metadata)
            ideal_percentage = 25  # 25% for each difficulty level

            gaps = {
                'difficulty_gaps': [],
                'topic_gaps': [],
                'recommendations': []
            }

            # Check difficulty gaps
            for level in ['beginner', 'intermediate', 'advanced', 'expert']:
                count = difficulty_counts.get(level, 0)
                percentage = (count / total * 100) if total > 0 else 0
                if percentage < ideal_percentage - 10:
                    gaps['difficulty_gaps'].append({
                        'level': level,
                        'count': count,
                        'percentage': round(percentage, 1),
                        'gap': round(ideal_percentage - percentage, 1)
                    })

            # Check topic gaps (topics with < 3 courses)
            for topic, count in topic_counts.items():
                if count < 3:
                    gaps['topic_gaps'].append({
                        'topic': topic,
                        'count': count,
                        'recommendation': f'Create more {topic} courses'
                    })

            return gaps

        except Exception as e:
            logger.error(f"Error analyzing content gaps: {e}")
            return {'difficulty_gaps': [], 'topic_gaps': [], 'recommendations': []}


# Singleton instance
_metadata_client = None

def get_metadata_client() -> MetadataServiceClient:
    """
    Get singleton metadata client instance

    TECHNICAL PATTERN: Dependency injection via singleton
    WHY: Single connection pool, cached data sharing
    """
    global _metadata_client
    if _metadata_client is None:
        _metadata_client = MetadataServiceClient()
    return _metadata_client
