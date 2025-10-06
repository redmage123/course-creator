"""
Metadata-Enhanced Analytics Endpoints

BUSINESS REQUIREMENT:
Provide analytics endpoints that combine activity data with metadata
for richer insights and intelligent reporting.

TECHNICAL IMPLEMENTATION:
- Integrates metadata service with analytics data
- Provides topic-based analytics
- Supports content gap analysis
- Enables search pattern tracking

WHY:
Metadata enrichment transforms raw analytics into actionable insights
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from infrastructure.metadata_client import get_metadata_client, MetadataServiceClient

logger = logging.getLogger(__name__)

# Create router for metadata-enhanced analytics
router = APIRouter(prefix="/api/v1/analytics/metadata", tags=["metadata-analytics"])


@router.get("/content-analytics", response_model=Dict[str, Any])
async def get_content_analytics(
    organization_id: Optional[str] = Query(None),
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    metadata_client: MetadataServiceClient = Depends(get_metadata_client)
):
    """
    Get content analytics enriched with metadata

    BUSINESS VALUE:
    - Understand content effectiveness by topic and difficulty
    - Identify trending content areas
    - Track content engagement patterns

    Args:
        organization_id: Optional organization filter
        time_range: Time range for analytics (1d, 7d, 30d, 90d)
        metadata_client: Injected metadata service client

    Returns:
        Content analytics with metadata insights
    """
    try:
        # Get popular tags from metadata service
        popular_tags = await metadata_client.get_popular_tags('course', limit=20)

        # Get courses by top tags
        tag_analytics = []
        for tag_info in popular_tags[:5]:  # Top 5 tags
            tag = tag_info['tag']
            courses = await metadata_client.get_by_tags([tag], entity_type='course')

            tag_analytics.append({
                'tag': tag,
                'course_count': len(courses),
                'courses': [
                    {
                        'id': c.get('entity_id'),
                        'title': c.get('title'),
                        'difficulty': c.get('metadata', {}).get('educational', {}).get('difficulty')
                    }
                    for c in courses[:10]  # Limit to 10 courses per tag
                ]
            })

        return {
            'popular_tags': popular_tags,
            'tag_analytics': tag_analytics,
            'time_range': time_range,
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting content analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content analytics")


@router.get("/topic-analytics/{topic}", response_model=Dict[str, Any])
async def get_topic_analytics(
    topic: str,
    metadata_client: MetadataServiceClient = Depends(get_metadata_client)
):
    """
    Get analytics for specific topic

    BUSINESS VALUE:
    - Deep dive into topic performance
    - Understand student engagement with topic
    - Identify topic-specific learning patterns

    Args:
        topic: Topic to analyze
        metadata_client: Injected metadata service client

    Returns:
        Topic-specific analytics with metadata
    """
    try:
        # Search for courses on this topic
        courses = await metadata_client.search_metadata(
            query=topic,
            entity_types=['course'],
            limit=50
        )

        # Analyze difficulty distribution
        difficulty_dist = {}
        for course in courses:
            difficulty = course.get('metadata', {}).get('educational', {}).get('difficulty', 'unknown')
            difficulty_dist[difficulty] = difficulty_dist.get(difficulty, 0) + 1

        # Extract related topics
        related_topics = set()
        for course in courses:
            topics = course.get('metadata', {}).get('educational', {}).get('topics', [])
            related_topics.update(topics)

        # Remove the search topic itself
        related_topics.discard(topic)

        return {
            'topic': topic,
            'total_courses': len(courses),
            'difficulty_distribution': difficulty_dist,
            'related_topics': list(related_topics)[:10],  # Top 10 related topics
            'courses': [
                {
                    'id': c.get('entity_id'),
                    'title': c.get('title'),
                    'description': c.get('description'),
                    'difficulty': c.get('metadata', {}).get('educational', {}).get('difficulty'),
                    'tags': c.get('tags', [])
                }
                for c in courses[:20]  # Limit to 20 courses
            ]
        }

    except Exception as e:
        logger.error(f"Error getting topic analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics for topic: {topic}")


@router.get("/content-gaps", response_model=Dict[str, Any])
async def analyze_content_gaps(
    organization_id: Optional[str] = Query(None),
    metadata_client: MetadataServiceClient = Depends(get_metadata_client)
):
    """
    Analyze content gaps using metadata

    BUSINESS VALUE:
    - Identify underrepresented topics
    - Highlight difficulty level imbalances
    - Guide content creation priorities

    Args:
        organization_id: Optional organization filter
        metadata_client: Injected metadata service client

    Returns:
        Content gap analysis with recommendations
    """
    try:
        # For now, analyze all courses
        # In production, this would filter by organization_id
        all_courses = await metadata_client.search_metadata(
            query='',
            entity_types=['course'],
            limit=1000
        )

        course_ids = [c.get('entity_id') for c in all_courses]

        # Use metadata client to analyze gaps
        gaps = await metadata_client.analyze_content_gaps(course_ids)

        return {
            'total_courses_analyzed': len(all_courses),
            'difficulty_gaps': gaps.get('difficulty_gaps', []),
            'topic_gaps': gaps.get('topic_gaps', []),
            'recommendations': gaps.get('recommendations', []),
            'analyzed_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error analyzing content gaps: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze content gaps")


@router.get("/learning-paths/{student_id}", response_model=Dict[str, Any])
async def get_learning_path_suggestions(
    student_id: str,
    metadata_client: MetadataServiceClient = Depends(get_metadata_client)
):
    """
    Get learning path suggestions based on completed courses

    BUSINESS VALUE:
    - Personalized learning recommendations
    - Progressive difficulty advancement
    - Topic-aligned course suggestions

    Args:
        student_id: Student UUID
        metadata_client: Injected metadata service client

    Returns:
        Suggested learning path with courses
    """
    try:
        # This would integrate with student progress tracking
        # For now, return a sample learning path structure

        # In production:
        # 1. Get student's completed courses from analytics
        # 2. Get metadata for completed courses
        # 3. Extract topics and difficulty level
        # 4. Search for next-level courses in same topics

        return {
            'student_id': student_id,
            'current_level': 'beginner',
            'completed_topics': [],
            'suggested_path': [],
            'next_courses': [],
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting learning path: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate learning path")


@router.get("/search-trends", response_model=Dict[str, Any])
async def get_search_trends(
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    limit: int = Query(20, ge=1, le=100),
    metadata_client: MetadataServiceClient = Depends(get_metadata_client)
):
    """
    Get search trends from metadata analytics

    BUSINESS VALUE:
    - Understand what students are searching for
    - Identify content demand signals
    - Guide content creation based on student needs

    Args:
        time_range: Time range for trends
        limit: Maximum trends to return
        metadata_client: Injected metadata service client

    Returns:
        Search trends with metadata context
    """
    try:
        # This would integrate with search logging
        # For now, return popular tags as proxy for search trends

        popular_tags = await metadata_client.get_popular_tags('course', limit=limit)

        return {
            'time_range': time_range,
            'trending_topics': popular_tags,
            'search_insights': {
                'total_searches': 0,  # Would come from search logs
                'unique_queries': 0,
                'top_queries': []
            },
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting search trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search trends")


@router.post("/enrich-course/{course_id}", response_model=Dict[str, Any])
async def enrich_course_analytics(
    course_id: str,
    analytics_data: Dict[str, Any],
    metadata_client: MetadataServiceClient = Depends(get_metadata_client)
):
    """
    Enrich course analytics with metadata

    BUSINESS VALUE:
    - Add context to raw analytics numbers
    - Provide topic and difficulty context
    - Enable more intelligent reporting

    Args:
        course_id: Course UUID
        analytics_data: Raw analytics data
        metadata_client: Injected metadata service client

    Returns:
        Analytics data enriched with metadata
    """
    try:
        enriched = await metadata_client.enrich_analytics_data(
            analytics_data,
            entity_id_key='course_id'
        )

        return enriched

    except Exception as e:
        logger.error(f"Error enriching course analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to enrich analytics")


@router.get("/difficulty-analytics", response_model=Dict[str, Any])
async def get_difficulty_level_analytics(
    metadata_client: MetadataServiceClient = Depends(get_metadata_client)
):
    """
    Get analytics by difficulty level

    BUSINESS VALUE:
    - Understand content distribution across difficulty levels
    - Identify difficulty level gaps
    - Track student progression patterns

    Args:
        metadata_client: Injected metadata service client

    Returns:
        Difficulty level analytics
    """
    try:
        # Get analytics for each difficulty level
        difficulty_analytics = {}

        for difficulty in ['beginner', 'intermediate', 'advanced', 'expert']:
            courses = await metadata_client.get_by_tags(
                [difficulty],
                entity_type='course',
                limit=1000
            )

            # Analyze topics within this difficulty
            topic_counts = {}
            for course in courses:
                topics = course.get('metadata', {}).get('educational', {}).get('topics', [])
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

            top_topics = sorted(
                topic_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            difficulty_analytics[difficulty] = {
                'course_count': len(courses),
                'top_topics': [{'topic': t, 'count': c} for t, c in top_topics],
                'percentage': 0  # Will be calculated below
            }

        # Calculate percentages
        total_courses = sum(d['course_count'] for d in difficulty_analytics.values())
        for difficulty in difficulty_analytics:
            count = difficulty_analytics[difficulty]['course_count']
            difficulty_analytics[difficulty]['percentage'] = round(
                (count / total_courses * 100) if total_courses > 0 else 0,
                1
            )

        return {
            'difficulty_distribution': difficulty_analytics,
            'total_courses': total_courses,
            'analyzed_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting difficulty analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get difficulty analytics")


# Health check
@router.get("/health")
async def metadata_analytics_health():
    """Health check for metadata analytics endpoints"""
    return {
        "status": "healthy",
        "service": "metadata-analytics",
        "timestamp": datetime.now().isoformat()
    }
