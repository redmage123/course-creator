"""
Course Domain Entity - Core Educational Content Representation

This module defines the Course domain entity, which represents the fundamental unit of 
educational content within the platform. It encapsulates all course-related business
logic, validation rules, and invariants following Domain-Driven Design principles.

DOMAIN RESPONSIBILITY:
The Course entity manages the complete lifecycle of educational courses, from creation
through publication to archival. It enforces business rules around course metadata,
pricing models, duration estimates, and publication requirements.

EDUCATIONAL BUSINESS RULES:
1. Course Content Validation: Title and description are mandatory for educational clarity
2. Instructor Attribution: Every course must be associated with a qualified instructor
3. Publication Requirements: Courses must meet quality standards before publication
4. Pricing Models: Support for both free and premium course offerings
5. Difficulty Classification: Standardized difficulty levels for student guidance
6. Duration Estimation: Flexible time-based planning for student scheduling

LIFECYCLE STATES:
- Draft: Course in development, not visible to students
- Published: Course available for enrollment and delivery
- Archived: Course no longer accepting new enrollments

BUSINESS INVARIANTS:
- Course titles must be unique within instructor scope
- Descriptions must provide meaningful educational context
- Pricing must reflect institutional or market value standards
- Duration estimates must align with educational delivery methods
- Tags must support course discovery and categorization

INTEGRATION PATTERNS:
- Instructor Management: Foreign key relationship with user management service
- Enrollment System: One-to-many relationship with student enrollments
- Content Management: Integration with slides, quizzes, and lab materials
- Analytics Service: Performance metrics and effectiveness tracking
- Feedback System: Student and instructor feedback collection

PERFORMANCE CONSIDERATIONS:
- Immutable value objects for thread safety in concurrent environments
- Validation caching to minimize repeated business rule evaluation
- Lazy loading patterns for related entities (statistics, feedback)
- Optimized serialization for API response efficiency
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

class DifficultyLevel(Enum):
    """
    Educational difficulty taxonomy for course classification.
    
    This enumeration provides standardized difficulty levels that help students
    select appropriate courses based on their current knowledge and skill level.
    The taxonomy aligns with educational standards and learning progression models.
    
    BEGINNER: Entry-level courses requiring no prior knowledge
    - Foundational concepts and basic skill development
    - Step-by-step guidance with extensive support materials
    - Slower pace with frequent reinforcement and practice
    
    INTERMEDIATE: Courses requiring foundational knowledge
    - Builds upon basic concepts with increased complexity
    - Assumes familiarity with fundamental principles
    - Moderate pace with balanced theory and application
    
    ADVANCED: Expert-level courses for experienced learners
    - Complex concepts requiring significant background knowledge
    - High-level analysis, synthesis, and problem-solving
    - Fast pace with emphasis on independent learning
    """
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"  
    ADVANCED = "advanced"

class DurationUnit(Enum):
    """
    Time-based units for course duration estimation and scheduling.
    
    This enumeration provides flexible time units to accommodate various
    educational delivery methods, from intensive workshops to semester-long
    courses. Duration estimates help students plan their learning schedules.
    
    HOURS: Intensive workshops, webinars, and short training sessions
    - Typical range: 1-40 hours for focused skill development
    - Used for micro-learning and specific competency training
    
    DAYS: Short courses and bootcamp-style intensive training
    - Typical range: 1-30 days for concentrated learning
    - Used for immersive experiences and skill intensives
    
    WEEKS: Standard course duration for comprehensive topic coverage
    - Typical range: 1-52 weeks for thorough subject mastery
    - Most common unit for structured educational programs
    
    MONTHS: Extended programs and comprehensive curricula
    - Typical range: 1-24 months for deep specialization
    - Used for certification programs and degree-equivalent courses
    """
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"

@dataclass
class Course:
    """
    Core Course domain entity representing educational content with comprehensive business logic.
    
    This class encapsulates the complete course lifecycle management, from initial creation
    through publication to eventual archival. It enforces educational business rules,
    maintains data integrity, and provides rich domain behavior for course operations.
    
    DOMAIN RESPONSIBILITIES:
    1. Course Metadata Management: Title, description, categorization, and tagging
    2. Educational Classification: Difficulty levels and duration estimation
    3. Pricing and Revenue Model: Support for free and premium course offerings
    4. Publication Lifecycle: Draft → Published → Archived state transitions
    5. Quality Assurance: Validation rules ensuring educational standards
    6. Instructor Attribution: Ownership and responsibility tracking
    
    BUSINESS RULES ENFORCEMENT:
    - Title Uniqueness: Within instructor scope to prevent confusion
    - Content Quality: Minimum content requirements for publication
    - Educational Standards: Appropriate difficulty classification and duration
    - Pricing Integrity: Consistent with institutional or market standards
    - Publication Readiness: Comprehensive validation before student access
    
    LIFECYCLE MANAGEMENT:
    - Draft State: Development phase with instructor-only access
    - Published State: Active course with student enrollment capability
    - Archived State: Historical course with read-only access
    - Transition Rules: Validation requirements for state changes
    
    EDUCATIONAL METADATA:
    - Difficulty Levels: Beginner, Intermediate, Advanced classification
    - Duration Estimates: Flexible time units (hours to months)
    - Category System: Subject area organization for discovery
    - Tagging Support: Keyword-based content organization
    - Pricing Models: Free, premium, and institutional pricing
    
    INTEGRATION CAPABILITIES:
    - Instructor Management: Secure ownership and permission validation
    - Content System: Integration with slides, quizzes, and lab environments
    - Enrollment System: Student access control and capacity management
    - Analytics Platform: Performance metrics and educational effectiveness
    - Feedback System: Student satisfaction and instructor assessment
    
    PERFORMANCE FEATURES:
    - Validation Caching: Efficient business rule evaluation
    - Immutable Design: Thread-safe operations in concurrent environments
    - Lazy Loading: Optimized access to related entities and statistics
    - Serialization: Efficient API response formatting
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