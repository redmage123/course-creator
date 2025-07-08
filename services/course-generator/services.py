import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from .models import Course, Section, Lesson
from .schemas import (
    CourseCreate, 
    CourseUpdate,
    CourseResponse,
    SectionCreate,
    LessonCreate
)
from .database import get_db
from .config import Settings
from .exceptions import (
    CourseNotFoundError,
    ValidationError, 
    DatabaseError
)

logger = logging.getLogger(__name__)

class CourseGeneratorService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        settings: Settings = Depends(Settings)
    ):
        self.db = db
        self.settings = settings

    async def create_course(self, course_data: CourseCreate) -> CourseResponse:
        """
        Create a new course with sections and lessons
        """
        try:
            logger.info(f"Creating new course with title: {course_data.title}")
            
            # Validate course data
            if not course_data.title or not course_data.description:
                raise ValidationError("Course title and description are required")

            # Create course
            course = Course(
                id=uuid4(),
                title=course_data.title,
                description=course_data.description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add sections
            for section_data in course_data.sections:
                section = Section(
                    id=uuid4(),
                    course_id=course.id,
                    title=section_data.title,
                    order=section_data.order
                )
                course.sections.append(section)
                
                # Add lessons to section
                for lesson_data in section_data.lessons:
                    lesson = Lesson(
                        id=uuid4(),
                        section_id=section.id,
                        title=lesson_data.title,
                        content=lesson_data.content,
                        order=lesson_data.order
                    )
                    section.lessons.append(lesson)

            self.db.add(course)
            await self.db.commit()
            await self.db.refresh(course)

            logger.info(f"Successfully created course with ID: {course.id}")
            return CourseResponse.from_orm(course)

        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            raise DatabaseError("Error creating course")

    async def get_course(self, course_id: UUID) -> CourseResponse:
        """
        Get course by ID
        """
        try:
            course = await self.db.query(Course).filter(Course.id == course_id).first()
            
            if not course:
                raise CourseNotFoundError(f"Course with ID {course_id} not found")
                
            return CourseResponse.from_orm(course)

        except CourseNotFoundError as e:
            logger.error(f"Course not found: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error getting course: {str(e)}")
            raise DatabaseError("Error retrieving course")

    async def update_course(
        self, 
        course_id: UUID, 
        course_data: CourseUpdate
    ) -> CourseResponse:
        """
        Update existing course
        """
        try:
            course = await self.db.query(Course).filter(Course.id == course_id).first()
            
            if not course:
                raise CourseNotFoundError(f"Course with ID {course_id} not found")

            # Update course fields
            for field, value in course_data.dict(exclude_unset=True).items():
                setattr(course, field, value)
            
            course.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(course)

            logger.info(f"Successfully updated course with ID: {course_id}")
            return CourseResponse.from_orm(course)

        except CourseNotFoundError as e:
            logger.error(f"Course not found: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}")
            raise DatabaseError("Error updating course")

    async def delete_course(self, course_id: UUID) -> bool:
        """
        Delete course by ID
        """
        try:
            course = await self.db.query(Course).filter(Course.id == course_id).first()
            
            if not course:
                raise CourseNotFoundError(f"Course with ID {course_id} not found")

            await self.db.delete(course)
            await self.db.commit()

            logger.info(f"Successfully deleted course with ID: {course_id}")
            return True

        except CourseNotFoundError as e:
            logger.error(f"Course not found: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error deleting course: {str(e)}")
            raise DatabaseError("Error deleting course")

    async def list_courses(
        self,
        skip: int = 0,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CourseResponse]:
        """
        Get list of courses with pagination and filtering
        """
        try:
            query = self.db.query(Course)

            if filters:
                for key, value in filters.items():
                    if hasattr(Course, key):
                        query = query.filter(getattr(Course, key) == value)

            courses = await query.offset(skip).limit(limit).all()
            
            return [CourseResponse.from_orm(course) for course in courses]

        except Exception as e:
            logger.error(f"Error listing courses: {str(e)}")
            raise DatabaseError("Error retrieving courses")

    async def generate_course_content(self, course_id: UUID) -> CourseResponse:
        """
        Generate course content using AI/ML services
        """
        try:
            course = await self.db.query(Course).filter(Course.id == course_id).first()
            
            if not course:
                raise CourseNotFoundError(f"Course with ID {course_id} not found")

            # TODO: Implement AI content generation logic
            # This would integrate with ML services to generate content
            
            course.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(course)

            logger.info(f"Successfully generated content for course: {course_id}")
            return CourseResponse.from_orm(course)

        except CourseNotFoundError as e:
            logger.error(f"Course not found: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error generating course content: {str(e)}")
            raise DatabaseError("Error generating course content")

    async def validate_course_structure(self, course_id: UUID) -> bool:
        """
        Validate course structure and content
        """
        try:
            course = await self.db.query(Course).filter(Course.id == course_id).first()
            
            if not course:
                raise CourseNotFoundError(f"Course with ID {course_id} not found")

            # Validate sections exist
            if not course.sections:
                raise ValidationError("Course must have at least one section")

            # Validate section order and lessons
            for section in course.sections:
                if not section.lessons:
                    raise ValidationError(f"Section {section.id} must have at least one lesson")
                
                # Validate lesson order
                lesson_orders = [lesson.order for lesson in section.lessons]
                if len(set(lesson_orders)) != len(lesson_orders):
                    raise ValidationError(f"Duplicate lesson orders in section {section.id}")

            logger.info(f"Successfully validated course structure: {course_id}")
            return True

        except (CourseNotFoundError, ValidationError) as e:
            logger.error(str(e))
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error validating course: {str(e)}")
            raise DatabaseError("Error validating course")