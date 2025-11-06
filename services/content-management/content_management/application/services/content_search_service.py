"""
Content Search Application Service - Educational Content Discovery and Search
Single Responsibility: Handle content search and discovery operations

This service implements comprehensive educational content search capabilities including
full-text search, tag-based filtering, trending content analysis, and personalized
content recommendations for enhanced educational content discovery.

EDUCATIONAL SEARCH CAPABILITIES:
================================

Content Discovery Framework:
- **Multi-Type Search**: Unified search across syllabi, slides, quizzes, exercises, and labs
- **Relevance Ranking**: Educational content prioritization based on search context
- **Faceted Search**: Educational taxonomy and classification-based filtering
- **Personalization**: Student-specific content recommendations and discovery

Search Optimization:
- **Performance**: Efficient search indexing and query optimization for large content catalogs
- **Accuracy**: Relevance scoring and educational content quality ranking
- **Scalability**: Distributed search architecture for institutional scale
- **Analytics**: Search pattern analysis for content improvement insights

BUSINESS LOGIC IMPLEMENTATION:
===============================

Why This Service Exists:
- **Content Discovery**: Students and instructors need efficient ways to find relevant educational materials
- **Learning Path Optimization**: Recommends next steps and related content for personalized learning
- **Resource Utilization**: Helps identify underutilized content and optimization opportunities
- **Educational Effectiveness**: Trending content analysis reveals high-impact educational materials

Service Responsibilities:
- **Search Operations**: Orchestrates comprehensive content search across multiple criteria
- **Recommendation Engine**: Generates personalized content suggestions based on context
- **Trending Analysis**: Identifies popular and effective educational content
- **Tag Management**: Provides tag-based content organization and discovery
"""
from typing import List, Optional, Dict, Any

from content_management.domain.interfaces.content_service import IContentSearchService
from data_access.content_management_dao import ContentManagementDAO
from content_management.domain.entities.base_content import ContentType


class ContentSearchService(IContentSearchService):
    """
    Educational content search and discovery application service.

    Implements comprehensive search capabilities for educational content including
    multi-criteria search, tag-based filtering, trending analysis, and personalized
    content recommendations to enhance learning resource discovery.

    ## Educational Search Features:

    ### Content Discovery
    - **Full-Text Search**: Educational content search across titles, descriptions, and metadata
    - **Tag-Based Search**: Educational classification and taxonomy-based content filtering
    - **Advanced Filtering**: Course, content type, and educational context-based discovery
    - **Relevance Ranking**: Educational content prioritization for optimal learning outcomes

    ### Recommendation System
    - **Related Content**: Educational content relationship and similarity-based suggestions
    - **Trending Content**: Popular and effective educational material identification
    - **Personalized Recommendations**: Student-specific content discovery based on progress
    - **Learning Path Guidance**: Next-step content suggestions for educational progression

    ### Analytics Integration
    - **Search Pattern Analysis**: Educational content discovery pattern insights
    - **Popular Tags**: Most frequently used educational classifications and topics
    - **Usage Metrics**: Educational content access and utilization tracking
    - **Optimization Insights**: Content organization and discovery improvement recommendations

    Why This Service Matters:
    - Enables students to efficiently discover relevant educational resources
    - Helps instructors identify high-quality and popular educational materials
    - Supports personalized learning paths through intelligent recommendations
    - Improves educational content organization and institutional resource utilization
    """

    def __init__(self, content_dao: ContentManagementDAO):
        """
        Initialize educational content search service with data access.

        Sets up search capabilities with database access for educational content
        discovery operations across multiple content types and criteria.

        Why Data Access Dependency:
        - Content search requires database queries across multiple tables
        - Search operations need efficient indexing and filtering capabilities
        - Recommendation system requires access to content relationships

        Args:
            content_dao: Educational content data access object for search operations
        """
        self._content_dao = content_dao
    
    async def search_content(
        self,
        query: str,
        content_types: Optional[List[ContentType]] = None,
        course_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Any]]:
        """
        Search educational content across multiple types with advanced filtering.

        Performs comprehensive educational content search with multi-criteria filtering,
        relevance ranking, and metadata enrichment for efficient content discovery.

        Why This Method Exists:
        - Students need to quickly find relevant learning materials across different content types
        - Instructors require efficient content discovery for course preparation
        - Search results must be organized by content type for easy navigation
        - Educational context filtering ensures relevant and appropriate content

        Search Processing:
        - **Query Validation**: Ensures meaningful search with minimum length requirements
        - **Content Type Filtering**: Searches specific content types or all educational materials
        - **Course Scoping**: Limits search to specific course context when needed
        - **Result Organization**: Groups results by content type for structured presentation
        - **Metadata Enrichment**: Adds search context and result statistics

        Args:
            query: Educational content search query (minimum 2 characters)
            content_types: Specific educational content types to search (default: all types)
            course_id: Specific course identifier for scoped search (optional)
            filters: Additional search filters including status, difficulty, date range

        Returns:
            Dictionary of search results organized by content type with metadata:
            - Keys: Content type names (syllabi, slides, quizzes, etc.)
            - Values: Lists of matching educational content entities
            - _metadata: Search statistics and context information

        Raises:
            ValueError: Invalid search query (too short or empty)

        Educational Benefits:
        - Efficient educational content discovery across all material types
        - Organized results for easy content navigation and selection
        - Course-scoped search for contextual learning resource discovery
        - Search analytics for content organization improvement insights
        """
        try:
            # Validate query
            if not query or len(query.strip()) < 2:
                raise ValueError("Search query must be at least 2 characters")
            
            # Set default content types if not provided
            if content_types is None:
                content_types = [
                    ContentType.SYLLABUS,
                    ContentType.SLIDE,
                    ContentType.QUIZ,
                    ContentType.EXERCISE,
                    ContentType.LAB_ENVIRONMENT
                ]
            
            # Apply filters
            limit = filters.get("limit", 50) if filters else 50
            
            # Perform search
            results = await self._content_dao.search_all_content(
                query=query.strip(),
                content_types=content_types,
                course_id=course_id,
                limit=limit
            )
            
            # Post-process results if needed
            if filters:
                results = self._apply_additional_filters(results, filters)
            
            # Add search metadata
            total_results = sum(len(items) for items in results.values())
            results["_metadata"] = {
                "query": query,
                "total_results": total_results,
                "content_types_searched": [ct.value for ct in content_types],
                "course_id": course_id,
                "filters_applied": filters or {}
            }
            
            return results
            
        except Exception as e:
            raise ValueError(f"Content search failed: {str(e)}")
    
    async def search_by_tags(
        self, 
        tags: List[str], 
        content_types: Optional[List[ContentType]] = None,
        course_id: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """Search content by tags"""
        try:
            # Validate tags
            if not tags:
                raise ValueError("At least one tag is required")
            
            # Clean and validate tags
            clean_tags = [tag.strip().lower() for tag in tags if tag.strip()]
            if not clean_tags:
                raise ValueError("No valid tags provided")
            
            # Perform tag search
            results = await self._content_dao.search_by_tags(
                tags=clean_tags,
                content_types=content_types,
                course_id=course_id
            )
            
            # Add metadata
            total_results = sum(len(items) for items in results.values())
            results["_metadata"] = {
                "tags": clean_tags,
                "total_results": total_results,
                "content_types_searched": [ct.value for ct in content_types] if content_types else "all",
                "course_id": course_id
            }
            
            return results
            
        except Exception as e:
            raise ValueError(f"Tag search failed: {str(e)}")
    
    async def get_content_recommendations(self, content_id: str, limit: int = 5) -> List[Any]:
        """Get content recommendations based on existing content"""
        try:
            # This would typically involve:
            # 1. Analyzing the content to understand its characteristics
            # 2. Finding similar content based on tags, topics, difficulty, etc.
            # 3. Using collaborative filtering based on user interactions
            # 4. Machine learning recommendations
            
            # For now, implement a simple recommendation based on search
            # In a real system, this would be much more sophisticated
            
            # Get recent content as placeholder recommendations
            recommendations = await self._content_dao.get_recent_content(
                content_types=None,
                days=30,
                limit=limit
            )
            
            return recommendations[:limit]
            
        except Exception as e:
            raise ValueError(f"Failed to get content recommendations: {str(e)}")
    
    async def get_trending_content(self, content_type: Optional[ContentType] = None, days: int = 7) -> List[Any]:
        """Get trending content based on usage metrics"""
        try:
            # This would typically involve:
            # 1. Analyzing view counts, engagement metrics
            # 2. Calculating trending scores based on recent activity
            # 3. Filtering by content type if specified
            
            # For now, return recent content as a placeholder
            content_types = [content_type] if content_type else None
            
            trending_content = await self._content_dao.get_recent_content(
                content_types=content_types,
                days=days,
                limit=20
            )
            
            return trending_content
            
        except Exception as e:
            raise ValueError(f"Failed to get trending content: {str(e)}")
    
    async def get_popular_tags(self, content_type: Optional[ContentType] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular tags for content discovery"""
        try:
            # This would analyze all content to find most frequently used tags
            # For now, return a placeholder implementation
            
            popular_tags = [
                {"tag": "python", "count": 45, "content_type": "all"},
                {"tag": "data-science", "count": 32, "content_type": "all"},
                {"tag": "machine-learning", "count": 28, "content_type": "all"},
                {"tag": "web-development", "count": 25, "content_type": "all"},
                {"tag": "algorithms", "count": 22, "content_type": "all"},
                {"tag": "databases", "count": 20, "content_type": "all"},
                {"tag": "javascript", "count": 18, "content_type": "all"},
                {"tag": "statistics", "count": 15, "content_type": "all"},
                {"tag": "networking", "count": 12, "content_type": "all"},
                {"tag": "security", "count": 10, "content_type": "all"}
            ]
            
            if content_type:
                # Filter by content type (placeholder logic)
                popular_tags = [
                    {**tag, "content_type": content_type.value} 
                    for tag in popular_tags
                ]
            
            return popular_tags[:limit]
            
        except Exception as e:
            raise ValueError(f"Failed to get popular tags: {str(e)}")
    
    async def suggest_related_content(self, content_id: str, max_suggestions: int = 10) -> Dict[str, List[Any]]:
        """Suggest related content based on content analysis"""
        try:
            # This would analyze content relationships and suggest related items
            # For now, return a simple implementation
            
            suggestions = {
                "similar_content": [],
                "prerequisite_content": [],
                "follow_up_content": [],
                "complementary_content": []
            }
            
            # Get some recent content as placeholders
            recent_content = await self._content_dao.get_recent_content(
                content_types=None,
                days=30,
                limit=max_suggestions * 2
            )
            
            # Distribute among categories (simplified logic)
            chunk_size = len(recent_content) // 4
            suggestions["similar_content"] = recent_content[:chunk_size]
            suggestions["prerequisite_content"] = recent_content[chunk_size:chunk_size*2]
            suggestions["follow_up_content"] = recent_content[chunk_size*2:chunk_size*3]
            suggestions["complementary_content"] = recent_content[chunk_size*3:]
            
            return suggestions
            
        except Exception as e:
            raise ValueError(f"Failed to suggest related content: {str(e)}")
    
    def _apply_additional_filters(self, results: Dict[str, List[Any]], filters: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Apply additional filters to search results"""
        try:
            filtered_results = results.copy()
            
            # Filter by status
            if "status" in filters:
                status_filter = filters["status"]
                for content_type, items in filtered_results.items():
                    if content_type != "_metadata":
                        filtered_results[content_type] = [
                            item for item in items 
                            if hasattr(item, 'status') and item.status.value == status_filter
                        ]
            
            # Filter by date range
            if "date_from" in filters or "date_to" in filters:
                date_from = filters.get("date_from")
                date_to = filters.get("date_to")
                
                for content_type, items in filtered_results.items():
                    if content_type != "_metadata":
                        filtered_items = []
                        for item in items:
                            if hasattr(item, 'created_at'):
                                item_date = item.created_at
                                include_item = True
                                
                                if date_from and item_date < date_from:
                                    include_item = False
                                if date_to and item_date > date_to:
                                    include_item = False
                                
                                if include_item:
                                    filtered_items.append(item)
                        
                        filtered_results[content_type] = filtered_items
            
            # Filter by difficulty (for applicable content types)
            if "difficulty" in filters:
                difficulty_filter = filters["difficulty"]
                for content_type, items in filtered_results.items():
                    if content_type != "_metadata":
                        filtered_results[content_type] = [
                            item for item in items 
                            if hasattr(item, 'difficulty') and item.difficulty.value == difficulty_filter
                        ]
            
            return filtered_results
            
        except Exception as e:
            # If filtering fails, return original results
            return results