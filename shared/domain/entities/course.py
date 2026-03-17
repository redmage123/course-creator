"""
Course domain entity following SOLID principles.
Single Responsibility: Represents a course with business logic.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from decimal import Decimal

from ...database.interfaces import BaseEntity

class DifficultyLevel(Enum):
    """Course difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class DurationUnit(Enum):
    """Duration unit enumeration."""
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"

class Course(BaseEntity):
    """Course domain entity."""
    
    def __init__(
        self,
        title: str,
        instructor_id: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER,
        estimated_duration: Optional[int] = None,
        duration_unit: DurationUnit = DurationUnit.WEEKS,
        price: Decimal = Decimal('0.00'),
        is_published: bool = False,
        thumbnail_url: Optional[str] = None
    ):
        super().__init__()
        self.title = title
        self.instructor_id = instructor_id
        self.description = description
        self.category = category
        self.difficulty_level = difficulty_level
        self.estimated_duration = estimated_duration
        self.duration_unit = duration_unit
        self.price = price
        self.is_published = is_published
        self.thumbnail_url = thumbnail_url
    
    def publish(self) -> None:
        """Publish the course."""
        if not self.title or not self.description:
            raise ValueError("Course must have title and description to be published")
        self.is_published = True
        self.updated_at = datetime.utcnow()
    
    def unpublish(self) -> None:
        """Unpublish the course."""
        self.is_published = False
        self.updated_at = datetime.utcnow()
    
    def update_content(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
        estimated_duration: Optional[int] = None,
        duration_unit: Optional[DurationUnit] = None,
        thumbnail_url: Optional[str] = None
    ) -> None:
        """Update course content."""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if category is not None:
            self.category = category
        if difficulty_level is not None:
            self.difficulty_level = difficulty_level
        if estimated_duration is not None:
            self.estimated_duration = estimated_duration
        if duration_unit is not None:
            self.duration_unit = duration_unit
        if thumbnail_url is not None:
            self.thumbnail_url = thumbnail_url
        
        self.updated_at = datetime.utcnow()
    
    def update_pricing(self, price: Decimal) -> None:
        """Update course pricing."""
        if price < Decimal('0'):
            raise ValueError("Price cannot be negative")
        self.price = price
        self.updated_at = datetime.utcnow()
    
    def is_free(self) -> bool:
        """Check if course is free."""
        return self.price == Decimal('0.00')
    
    def get_duration_text(self) -> str:
        """Get human-readable duration."""
        if not self.estimated_duration:
            return "Duration not specified"
        
        unit_text = self.duration_unit.value
        if self.estimated_duration == 1:
            unit_text = unit_text.rstrip('s')  # Remove plural 's'
        
        return f"{self.estimated_duration} {unit_text}"
    
    def can_be_purchased(self) -> bool:
        """Check if course can be purchased."""
        return self.is_published and self.price > Decimal('0')
    
    def can_be_enrolled(self) -> bool:
        """Check if course allows enrollment."""
        return self.is_published
    
    def __str__(self) -> str:
        """String representation of course."""
        return f"Course({self.title}, {self.difficulty_level.value})"
    
    def __repr__(self) -> str:
        """Developer representation of course."""
        return (f"Course(id={self.id}, title='{self.title}', "
                f"instructor_id='{self.instructor_id}', is_published={self.is_published})")
    
    def to_dict(self) -> dict:
        """Convert course to dictionary (for API responses)."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'instructor_id': self.instructor_id,
            'category': self.category,
            'difficulty_level': self.difficulty_level.value,
            'estimated_duration': self.estimated_duration,
            'duration_unit': self.duration_unit.value,
            'price': str(self.price),
            'is_published': self.is_published,
            'thumbnail_url': self.thumbnail_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }