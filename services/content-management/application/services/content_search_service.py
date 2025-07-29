"""
Content Search Application Service
Single Responsibility: Handle content search and discovery operations
"""
from typing import List, Optional, Dict, Any

from ...domain.interfaces.content_service import IContentSearchService
from ...domain.interfaces.content_repository import IContentSearchRepository
from ...domain.entities.base_content import ContentType


class ContentSearchService(IContentSearchService):
    """
    Application service for content search operations
    """
    
    def __init__(self, search_repository: IContentSearchRepository):
        self._search_repository = search_repository
    
    async def search_content(
        self, 
        query: str, 
        content_types: Optional[List[ContentType]] = None,
        course_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Any]]:
        """Search content across all types with filters"""
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
            results = await self._search_repository.search_all_content(
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
            results = await self._search_repository.search_by_tags(
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
            recommendations = await self._search_repository.get_recent_content(
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
            
            trending_content = await self._search_repository.get_recent_content(
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
            recent_content = await self._search_repository.get_recent_content(
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