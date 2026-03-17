# Models module for Content Management Service

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ContentResponse(BaseModel):
    """
    Standardized response model for all educational content types.

    Provides consistent data structure for educational content presentation
    across different panes and content management operations.

    Content Lifecycle Support:
    - Tracks content creation and modification timestamps
    - Maintains content status (draft, published, archived)
    - Provides consistent metadata structure
    - Supports content versioning and audit trails

    Integration Benefits:
    - Uniform API response structure across all content types
    - Simplified client-side content handling
    - Consistent metadata representation
    - Standardized content identification and linking

    Educational Context:
    - Enables content relationship mapping and dependency tracking
    - Supports educational content analytics and usage monitoring
    - Facilitates content quality assessment and improvement
    """
    id: str
    title: str
    description: Optional[str] = None
    course_id: str
    created_by: str
    tags: List[str] = []
    status: str
    content_type: str
    created_at: datetime
    updated_at: datetime


__all__ = ['ContentResponse']