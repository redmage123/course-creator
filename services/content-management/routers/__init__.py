"""
API routers for content-management service
"""

from .upload_content import router as upload_content_router
from .get_content import router as get_content_router
from .update_content import router as update_content_router
from .delete_content import router as delete_content_router
from .list_content import router as list_content_router
from .get_content_by_lesson import router as get_content_by_lesson_router
from .attach_to_lesson import router as attach_to_lesson_router
from .process_video import router as process_video_router
from .get_processing_status import router as get_processing_status_router

__all__ = ['upload_content_router', 'get_content_router', 'update_content_router', 'delete_content_router', 'list_content_router', 'get_content_by_lesson_router', 'attach_to_lesson_router', 'process_video_router', 'get_processing_status_router']
