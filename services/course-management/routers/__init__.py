"""
API routers for course-management service
"""

from .courses import router as courses_router
from .create_course import router as create_course_router
from .get_course import router as get_course_router
from .update_course import router as update_course_router
from .delete_course import router as delete_course_router
from .course_lessons import router as course_lessons_router
from .add_lesson import router as add_lesson_router
from .get_lesson import router as get_lesson_router
from .update_lesson import router as update_lesson_router
from .delete_lesson import router as delete_lesson_router
from .publish_course import router as publish_course_router

__all__ = ['courses_router', 'create_course_router', 'get_course_router', 'update_course_router', 'delete_course_router', 'course_lessons_router', 'add_lesson_router', 'get_lesson_router', 'update_lesson_router', 'delete_lesson_router', 'publish_course_router']
