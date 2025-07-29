"""
Course Domain Entity
Single Responsibility: Represent a course with its business logic and invariants
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"  
    ADVANCED = "advanced"

class DurationUnit(Enum):
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"

@dataclass
class Course:
    """
    Course domain entity encapsulating business rules and invariants
    """
    title: str
    description: str
    instructor_id: str
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    price: float = 0.00
    is_published: bool = False
    id: Optional[str] = None
    category: Optional[str] = None
    estimated_duration: Optional[int] = None
    duration_unit: Optional[DurationUnit] = DurationUnit.WEEKS
    thumbnail_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate invariants after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate business rules and invariants"""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Course title cannot be empty")
        
        if len(self.title) > 200:
            raise ValueError("Course title cannot exceed 200 characters")
        
        if not self.description or len(self.description.strip()) == 0:
            raise ValueError("Course description cannot be empty")
        
        if len(self.description) > 2000:
            raise ValueError("Course description cannot exceed 2000 characters")
        
        if not self.instructor_id:
            raise ValueError("Course must have an instructor")
        
        if self.price < 0:
            raise ValueError("Course price cannot be negative")
        
        if self.estimated_duration is not None and self.estimated_duration <= 0:
            raise ValueError("Course duration must be positive")
    
    def can_be_published(self) -> bool:
        """Business rule: Check if course meets publication requirements"""
        return (
            self.title and 
            self.description and 
            self.instructor_id and
            len(self.title.strip()) > 0 and
            len(self.description.strip()) > 0
        )
    
    def publish(self) -> None:
        """Business rule: Publish course if it meets requirements"""
        if not self.can_be_published():
            raise ValueError("Course does not meet publication requirements")
        
        self.is_published = True
        self.updated_at = datetime.utcnow()
    
    def unpublish(self) -> None:
        """Business rule: Unpublish course"""
        self.is_published = False
        self.updated_at = datetime.utcnow()
    
    def update_details(self, title: Optional[str] = None, 
                      description: Optional[str] = None,
                      category: Optional[str] = None,
                      difficulty_level: Optional[DifficultyLevel] = None,
                      price: Optional[float] = None,
                      estimated_duration: Optional[int] = None,
                      duration_unit: Optional[DurationUnit] = None) -> None:
        """Update course details maintaining business rules"""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if category is not None:
            self.category = category
        if difficulty_level is not None:
            self.difficulty_level = difficulty_level
        if price is not None:
            self.price = price
        if estimated_duration is not None:
            self.estimated_duration = estimated_duration
        if duration_unit is not None:
            self.duration_unit = duration_unit
        
        self.updated_at = datetime.utcnow()
        self.validate()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the course"""
        if tag and tag.strip() and tag not in self.tags:
            self.tags.append(tag.strip())
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the course"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def get_formatted_duration(self) -> str:
        """Get human-readable duration string"""
        if not self.estimated_duration or not self.duration_unit:
            return "Duration not specified"
        
        return f"{self.estimated_duration} {self.duration_unit.value}"
    
    def is_free(self) -> bool:
        """Check if course is free"""
        return self.price == 0.0
    
    def get_difficulty_display(self) -> str:
        """Get formatted difficulty level"""
        return self.difficulty_level.value.title()

@dataclass 
class CourseStatistics:
    """Value object for course statistics"""
    course_id: str
    enrolled_students: int = 0
    active_enrollments: int = 0
    completion_rate: float = 0.0
    average_rating: float = 0.0
    total_feedback: int = 0
    revenue: float = 0.0
    last_updated: Optional[datetime] = None