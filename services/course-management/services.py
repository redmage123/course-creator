import logging
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.schemas.course import CourseCreate, CourseUpdate
from app.core.security import get_current_user
from app.core.config import settings
from app.utils.notifications import NotificationService
from app.utils.validators import validate_course_data

logger = logging.getLogger(__name__)

class CourseManagementService:
    def __init__(
        self,
        db: Session,
        notification_service: NotificationService
    ):
        self.db = db
        self.notification_service = notification_service

    async def create_course(self, course_data: CourseCreate, instructor_id: UUID) -> Course:
        """
        Create a new course
        """
        try:
            # Validate course data
            validate_course_data(course_data)

            course = Course(
                title=course_data.title,
                description=course_data.description,
                instructor_id=instructor_id,
                start_date=course_data.start_date,
                end_date=course_data.end_date,
                max_students=course_data.max_students,
                status="active"
            )

            self.db.add(course)
            await self.db.commit()
            await self.db.refresh(course)

            # Notify instructor
            await self.notification_service.send_notification(
                instructor_id,
                f"Course {course.title} has been created successfully"
            )

            logger.info(f"Course created: {course.id}")
            return course

        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create course"
            )

    async def get_course(self, course_id: UUID) -> Course:
        """
        Get course by ID
        """
        try:
            course = await self.db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            return course

        except Exception as e:
            logger.error(f"Error fetching course {course_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch course"
            )

    async def update_course(
        self,
        course_id: UUID,
        course_data: CourseUpdate,
        instructor_id: UUID
    ) -> Course:
        """
        Update existing course
        """
        try:
            course = await self.get_course(course_id)

            # Verify instructor ownership
            if course.instructor_id != instructor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this course"
                )

            # Update fields
            for field, value in course_data.dict(exclude_unset=True).items():
                setattr(course, field, value)

            await self.db.commit()
            await self.db.refresh(course)

            logger.info(f"Course updated: {course_id}")
            return course

        except Exception as e:
            logger.error(f"Error updating course {course_id}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update course"
            )

    async def delete_course(self, course_id: UUID, instructor_id: UUID) -> None:
        """
        Delete course
        """
        try:
            course = await self.get_course(course_id)

            # Verify instructor ownership
            if course.instructor_id != instructor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this course"
                )

            # Check if course has active enrollments
            active_enrollments = await self.db.query(Enrollment).filter(
                Enrollment.course_id == course_id,
                Enrollment.status == "active"
            ).count()

            if active_enrollments > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete course with active enrollments"
                )

            await self.db.delete(course)
            await self.db.commit()

            logger.info(f"Course deleted: {course_id}")

        except Exception as e:
            logger.error(f"Error deleting course {course_id}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete course"
            )

    async def list_courses(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Dict = None
    ) -> List[Course]:
        """
        List courses with optional filtering
        """
        try:
            query = self.db.query(Course)

            if filters:
                if filters.get("instructor_id"):
                    query = query.filter(Course.instructor_id == filters["instructor_id"])
                if filters.get("status"):
                    query = query.filter(Course.status == filters["status"])

            courses = await query.offset(skip).limit(limit).all()
            return courses

        except Exception as e:
            logger.error(f"Error listing courses: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list courses"
            )

    async def enroll_student(
        self,
        course_id: UUID,
        student_id: UUID
    ) -> Enrollment:
        """
        Enroll student in course
        """
        try:
            course = await self.get_course(course_id)

            # Check if course is full
            current_enrollments = await self.db.query(Enrollment).filter(
                Enrollment.course_id == course_id,
                Enrollment.status == "active"
            ).count()

            if current_enrollments >= course.max_students:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Course is full"
                )

            # Check if already enrolled
            existing_enrollment = await self.db.query(Enrollment).filter(
                Enrollment.course_id == course_id,
                Enrollment.student_id == student_id
            ).first()

            if existing_enrollment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student already enrolled in this course"
                )

            enrollment = Enrollment(
                course_id=course_id,
                student_id=student_id,
                enrollment_date=datetime.utcnow(),
                status="active"
            )

            self.db.add(enrollment)
            await self.db.commit()
            await self.db.refresh(enrollment)

            # Notify student and instructor
            await self.notification_service.send_notification(
                student_id,
                f"You have been enrolled in {course.title}"
            )
            await self.notification_service.send_notification(
                course.instructor_id,
                f"New student enrolled in {course.title}"
            )

            logger.info(f"Student {student_id} enrolled in course {course_id}")
            return enrollment

        except Exception as e:
            logger.error(f"Error enrolling student: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enroll student"
            )

    async def unenroll_student(
        self,
        course_id: UUID,
        student_id: UUID
    ) -> None:
        """
        Unenroll student from course
        """
        try:
            enrollment = await self.db.query(Enrollment).filter(
                Enrollment.course_id == course_id,
                Enrollment.student_id == student_id,
                Enrollment.status == "active"
            ).first()

            if not enrollment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active enrollment not found"
                )

            enrollment.status = "inactive"
            enrollment.end_date = datetime.utcnow()

            await self.db.commit()

            course = await self.get_course(course_id)

            # Notify student and instructor
            await self.notification_service.send_notification(
                student_id,
                f"You have been unenrolled from {course.title}"
            )
            await self.notification_service.send_notification(
                course.instructor_id,
                f"Student unenrolled from {course.title}"
            )

            logger.info(f"Student {student_id} unenrolled from course {course_id}")

        except Exception as e:
            logger.error(f"Error unenrolling student: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unenroll student"
            )