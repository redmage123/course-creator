"""
API routers for enrollment service
"""

from .enroll_student import router as enroll_student_router
from .get_enrollment import router as get_enrollment_router
from .list_enrollments import router as list_enrollments_router
from .update_enrollment import router as update_enrollment_router
from .unenroll_student import router as unenroll_student_router
from .get_student_courses import router as get_student_courses_router
from .get_course_students import router as get_course_students_router
from .update_lesson_progress import router as update_lesson_progress_router
from .get_course_progress import router as get_course_progress_router
from .get_student_progress import router as get_student_progress_router
from .mark_lesson_complete import router as mark_lesson_complete_router
from .get_certificates import router as get_certificates_router
from .issue_certificate import router as issue_certificate_router

__all__ = ['enroll_student_router', 'get_enrollment_router', 'list_enrollments_router', 'update_enrollment_router', 'unenroll_student_router', 'get_student_courses_router', 'get_course_students_router', 'update_lesson_progress_router', 'get_course_progress_router', 'get_student_progress_router', 'mark_lesson_complete_router', 'get_certificates_router', 'issue_certificate_router']
