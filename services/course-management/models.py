from datetime import datetime
from typing import List
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
import uuid
import enum

Base = declarative_base()

class CourseStatusEnum(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Course(Base):
    __tablename__ = 'courses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(CourseStatusEnum), default=CourseStatusEnum.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}', status={self.status})>"

class CourseModule(Base):
    __tablename__ = 'course_modules'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="modules")
    lessons = relationship("CourseLesson", back_populates="module", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CourseModule(id={self.id}, title='{self.title}', course_id={self.course_id})>"

class CourseLesson(Base):
    __tablename__ = 'course_lessons'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey('course_modules.id'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    module = relationship("CourseModule", back_populates="lessons")
    progress = relationship("Progress", back_populates="lesson", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CourseLesson(id={self.id}, title='{self.title}', module_id={self.module_id})>"

class Enrollment(Base):
    __tablename__ = 'enrollments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    course = relationship("Course", back_populates="enrollments")
    progress = relationship("Progress", back_populates="enrollment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Enrollment(id={self.id}, user_id={self.user_id}, course_id={self.course_id})>"

class Progress(Base):
    __tablename__ = 'progress'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey('enrollments.id'), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('course_lessons.id'), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    enrollment = relationship("Enrollment", back_populates="progress")
    lesson = relationship("CourseLesson", back_populates="progress")

    def __repr__(self):
        return f"<Progress(id={self.id}, enrollment_id={self.enrollment_id}, lesson_id={self.lesson_id})>"