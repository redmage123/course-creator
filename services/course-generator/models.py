from datetime import datetime
import uuid
from typing import List
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class CourseTemplate(Base):
    __tablename__ = 'course_templates'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    target_audience = Column(String(255))
    difficulty_level = Column(String(50))
    estimated_duration = Column(Integer)  # in minutes
    metadata = Column(JSON)

    generation_jobs = relationship("GenerationJob", back_populates="course_template")
    content_prompts = relationship("ContentPrompt", back_populates="course_template")

    def __repr__(self):
        return f"<CourseTemplate(id={self.id}, title='{self.title}')>"


class GenerationJob(Base):
    __tablename__ = 'generation_jobs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_template_id = Column(UUID(as_uuid=True), ForeignKey('course_templates.id'), nullable=False)
    status = Column(String(50), nullable=False, default='pending')  # pending, in_progress, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    result_data = Column(JSON)
    metadata = Column(JSON)

    course_template = relationship("CourseTemplate", back_populates="generation_jobs")

    def __repr__(self):
        return f"<GenerationJob(id={self.id}, status='{self.status}')>"


class ContentPrompt(Base):
    __tablename__ = 'content_prompts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_template_id = Column(UUID(as_uuid=True), ForeignKey('course_templates.id'), nullable=False)
    prompt_type = Column(String(50), nullable=False)  # outline, content, quiz, etc.
    prompt_text = Column(Text, nullable=False)
    order = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    metadata = Column(JSON)

    course_template = relationship("CourseTemplate", back_populates="content_prompts")

    def __repr__(self):
        return f"<ContentPrompt(id={self.id}, type='{self.prompt_type}')>"