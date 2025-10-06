"""
Course Instance models for managing instantiated courses with dates.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class CourseInstanceBase(BaseModel):
    """Base course instance model"""
    course_id: str = Field(..., description="ID of the base course")
    title: str = Field(..., description="Course title")
    instructor_id: str = Field(..., description="ID of the instructor")
    instructor_name: str = Field(..., description="Full name of the instructor")
    start_date: datetime = Field(..., description="Course start date and time")
    end_date: datetime = Field(..., description="Course end date and time")
    max_students: Optional[int] = Field(None, description="Maximum number of students")
    status: str = Field(default="scheduled", description="Course instance status")


class CourseInstanceCreate(CourseInstanceBase):
    """Model for creating a new course instance"""
    pass


class CourseInstance(CourseInstanceBase):
    """Complete course instance model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class Enrollment(BaseModel):
    """Student enrollment in a course instance"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = Field(..., description="ID of the enrolled student")
    course_instance_id: str = Field(..., description="ID of the course instance")
    enrolled_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="active", description="Enrollment status")
    progress: Optional[float] = Field(None, description="Student progress percentage")
    
    class Config:
        from_attributes = True