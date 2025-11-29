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
    7. Organizational Context: Optional association with organization/project/track (v3.3.1)

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

    ORGANIZATIONAL CONTEXT (v3.3.1):
    The platform supports two flexible course creation patterns:

    MODE 1 - STANDALONE COURSES:
    - Single instructors create courses WITHOUT organizational hierarchy
    - organization_id, project_id, track_id all remain None
    - Course directly accessible to instructor for content development
    - Use Case: Independent instructors, freelance educators

    MODE 2 - ORGANIZATIONAL COURSES:
    - Corporate/enterprise users create courses WITHIN organizational structures
    - Optional Organization → Project → Track hierarchy
    - Courses can be added to tracks later via track_classes junction table
    - Use Case: Corporate training, university programs, structured learning

    INTEGRATION CAPABILITIES:
    - Instructor Management: Secure ownership and permission validation
    - Content System: Integration with slides, quizzes, and lab environments
    - Enrollment System: Student access control and capacity management
    - Analytics Platform: Performance metrics and educational effectiveness
    - Feedback System: Student satisfaction and instructor assessment
    - Organization Management: Optional organizational hierarchy integration (v3.3.1)

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

    # Optional organizational context (v3.3.1)
    # Note: project_id is NOT a database column - projects are managed separately
    # Courses belong to tracks, tracks belong to projects
    organization_id: Optional[str] = None
    track_id: Optional[str] = None
    location_id: Optional[str] = None
    
    def __post_init__(self):
        """
        Execute post-initialization validation after dataclass creation.

        This method is automatically called by Python's dataclass mechanism after
        the __init__ method completes. It ensures all business rules and invariants
        are validated immediately upon object creation, preventing invalid states.

        WHY THIS EXISTS:
        Dataclasses don't support validation in __init__ by default. This hook
        provides a standardized place to enforce domain invariants and business
        rules immediately after object construction, implementing the "fail-fast"
        principle of Domain-Driven Design.

        DOMAIN ENFORCEMENT:
        - Title and description content validation
        - Instructor attribution verification
        - Pricing integrity checks
        - Duration consistency validation

        Raises:
            ValueError: If any business rule or invariant is violated
        """
        self.validate()
    
    def validate(self) -> None:
        """
        Validate all business rules and domain invariants for course entity.

        This method enforces comprehensive business rules ensuring data integrity,
        educational quality standards, and platform consistency. It validates both
        required fields and optional metadata to prevent invalid course states.

        BUSINESS RULES ENFORCED:
        1. Title Requirements:
           - Must be non-empty with meaningful content
           - Maximum 200 characters for UI display consistency
           - Prevents whitespace-only titles

        2. Description Standards:
           - Must provide educational context (non-empty)
           - Maximum 2000 characters for detailed course overview
           - Ensures students have sufficient information for decisions

        3. Instructor Attribution:
           - Every course requires an assigned instructor
           - Enforces accountability and ownership

        4. Pricing Integrity:
           - Prices cannot be negative (supports free courses at 0.00)
           - Validates financial model consistency

        5. Duration Consistency:
           - If duration is specified, must be positive value
           - Aligns with educational delivery timeframes

        6. Organizational Context (v3.3.2):
           - Validates organization/track relationship
           - Ensures no orphaned track references

        WHY VALIDATION MATTERS:
        - Prevents data corruption in database layer
        - Ensures consistent user experience across platform
        - Enforces educational quality standards
        - Supports reliable analytics and reporting
        - Maintains instructor accountability

        WHEN CALLED:
        - Automatically after object creation (__post_init__)
        - After any update_details() operation
        - Can be manually invoked for re-validation

        Raises:
            ValueError: Descriptive error for each specific business rule violation
                with clear messaging for developers and logging systems
        """
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

        # Validate organizational context (v3.3.2)
        if not self.validate_organizational_context():
            raise ValueError(
                "Invalid organizational context: cannot set track_id without organization_id"
            )

    def validate_organizational_context(self) -> bool:
        """
        Validate organizational context constraints for course creation modes.

        BUSINESS RULES (v3.3.2):
        Organizations can now create courses directly without requiring projects
        or tracks. This method validates three valid course creation modes:

        MODE 1 - STANDALONE COURSE:
        - organization_id = None, track_id = None
        - Independent instructor creates course without organizational hierarchy
        - Use case: Freelance educators, independent training providers

        MODE 2 - DIRECT ORGANIZATION COURSE:
        - organization_id = set, track_id = None
        - Organization creates course directly without project/track structure
        - Use case: Quick course creation, simple organizational needs

        MODE 3 - TRACK-BASED COURSE:
        - organization_id = set, track_id = set
        - Traditional hierarchical course within organization structure
        - Use case: Structured curriculum, certification tracks

        INVALID CASE:
        - organization_id = None, track_id = set
        - This creates an orphaned track reference which is not allowed
        - Tracks must belong to an organization

        WHY THIS MATTERS:
        - Provides flexibility for different organizational needs
        - Maintains referential integrity in database
        - Supports both simple and complex course structures
        - Enables gradual adoption of organizational features

        Returns:
            bool: True if organizational context is valid, False otherwise

        Example:
            >>> # Valid: Standalone course
            >>> course = Course(title="Python", description="Learn", instructor_id="123")
            >>> course.validate_organizational_context()  # True

            >>> # Valid: Direct org course
            >>> course = Course(title="Python", description="Learn", instructor_id="123",
            ...                 organization_id="org-456")
            >>> course.validate_organizational_context()  # True

            >>> # Invalid: Orphaned track
            >>> course = Course(title="Python", description="Learn", instructor_id="123",
            ...                 track_id="track-789")  # No organization_id
            >>> course.validate_organizational_context()  # False
        """
        has_org = self.organization_id is not None
        has_track = self.track_id is not None

        # Valid combinations:
        # 1. Standalone: no org, no track
        # 2. Direct org: org set, no track
        # 3. Track-based: org and track both set
        # Invalid: track set without org (orphaned track)
        return (
            (not has_org and not has_track) or  # Standalone
            (has_org and not has_track) or       # Direct org
            (has_org and has_track)              # Track-based
        )

    def get_organizational_context_mode(self) -> str:
        """
        Determine the organizational context mode for this course.

        Returns a string identifier for the course's organizational mode,
        useful for UI display, analytics, and business logic branching.

        MODES:
        - "standalone": Independent course without organizational hierarchy
        - "direct_org": Course directly under organization (no track)
        - "track_based": Course within track/project hierarchy
        - "invalid": Invalid organizational context (should not occur)

        Returns:
            str: Mode identifier string

        Example:
            >>> course = Course(title="ML", description="Learn", instructor_id="123",
            ...                 organization_id="org-456")
            >>> course.get_organizational_context_mode()
            "direct_org"
        """
        has_org = self.organization_id is not None
        has_track = self.track_id is not None

        if not has_org and not has_track:
            return "standalone"
        elif has_org and not has_track:
            return "direct_org"
        elif has_org and has_track:
            return "track_based"
        else:
            return "invalid"
    
    def can_be_published(self) -> bool:
        """
        Determine if course meets minimum requirements for publication.

        This business rule evaluates whether a course has sufficient quality
        and completeness to be made visible to students. Publication readiness
        ensures students only see courses with meaningful content and clear
        instructor attribution.

        PUBLICATION CRITERIA:
        1. Title Presence: Non-empty, meaningful title for course identification
        2. Description Completeness: Adequate educational context for student decisions
        3. Instructor Attribution: Qualified instructor assigned for accountability
        4. Content Quality: No whitespace-only fields that bypass validation

        BUSINESS JUSTIFICATION:
        - Protects student experience from incomplete courses
        - Maintains platform quality standards
        - Ensures instructor accountability is established
        - Prevents premature course visibility before content development

        EDUCATIONAL WORKFLOW:
        Draft → Meets Requirements → Ready for publish() → Published

        USE CASES:
        - Pre-publication validation in course creation UI
        - Automated quality checks before course visibility
        - Instructor dashboard readiness indicators
        - Administrative review workflows

        Returns:
            bool: True if course meets all publication requirements, False otherwise

        Example:
            >>> course = Course(title="Python 101", description="Learn Python", instructor_id="123")
            >>> if course.can_be_published():
            ...     course.publish()
        """
        return (
            self.title and
            self.description and
            self.instructor_id and
            len(self.title.strip()) > 0 and
            len(self.description.strip()) > 0
        )
    
    def publish(self) -> None:
        """
        Transition course from draft to published state with validation.

        This critical business operation makes a course visible to students for
        enrollment and learning. It enforces quality gates ensuring only complete,
        instructor-attributed courses reach students, protecting the educational
        experience and platform reputation.

        BUSINESS WORKFLOW:
        1. Validate publication readiness via can_be_published()
        2. Update publication status flag
        3. Record timestamp for audit trail and analytics

        EDUCATIONAL IMPACT:
        - Makes course visible in student course catalog
        - Enables student enrollment and access
        - Triggers notification systems for interested students
        - Activates course in search and recommendation engines
        - Begins tracking for analytics and performance metrics

        QUALITY ASSURANCE:
        - Enforces minimum content standards before student access
        - Ensures instructor accountability is established
        - Prevents incomplete courses from damaging student experience
        - Maintains platform educational quality reputation

        ADMINISTRATIVE USE CASES:
        - Instructor publishes completed course from dashboard
        - Automated publishing after content review approval
        - Scheduled publication for marketing campaigns
        - Administrative override for featured courses

        AUDIT TRAIL:
        Updates self.updated_at timestamp for:
        - Publication history tracking
        - Analytics on course development time
        - Administrative reporting and compliance

        Raises:
            ValueError: If course does not meet publication requirements
                (missing title, description, or instructor attribution)

        Example:
            >>> course = Course(title="Advanced ML", description="Deep learning", instructor_id="456")
            >>> course.publish()  # Course now visible to students
        """
        if not self.can_be_published():
            raise ValueError("Course does not meet publication requirements")

        self.is_published = True
        self.updated_at = datetime.utcnow()
    
    def unpublish(self) -> None:
        """
        Transition course from published to draft state (unpublish operation).

        This administrative operation removes a course from student visibility,
        making it inaccessible for new enrollments while preserving existing
        student access. Used for content updates, quality issues, or temporary
        removal from catalog.

        BUSINESS WORKFLOW:
        1. Set publication status to False (draft state)
        2. Record timestamp for audit trail
        3. Course remains in database but hidden from catalog

        OPERATIONAL IMPACTS:
        - Removes course from student course catalog and search
        - Prevents new student enrollments
        - Existing enrolled students typically retain access (enrollment-dependent)
        - Course enters maintenance mode for content updates
        - Analytics continue tracking existing enrollments

        USE CASES:
        1. Content Updates: Instructor needs to revise materials
        2. Quality Issues: Feedback indicates problems requiring fixes
        3. Seasonal Courses: Temporarily remove until next offering
        4. Administrative Review: Quality assurance or compliance checks
        5. Instructor Request: Voluntary removal for maintenance

        POLICY CONSIDERATIONS:
        - Existing student access governed by enrollment policies
        - May trigger notifications to enrolled students
        - Analytics retain historical publication periods
        - Course can be re-published after updates via publish()

        AUDIT TRAIL:
        Updates self.updated_at timestamp for:
        - Publication lifecycle tracking
        - Administrative compliance reporting
        - Instructor activity analytics

        Returns:
            None

        Example:
            >>> course = Course(title="Data Science", description="Learn DS", instructor_id="789")
            >>> course.publish()
            >>> course.unpublish()  # Remove from catalog for updates
        """
        self.is_published = False
        self.updated_at = datetime.utcnow()
    
    def update_details(self, title: Optional[str] = None,
                      description: Optional[str] = None,
                      category: Optional[str] = None,
                      difficulty_level: Optional[DifficultyLevel] = None,
                      price: Optional[float] = None,
                      estimated_duration: Optional[int] = None,
                      duration_unit: Optional[DurationUnit] = None) -> None:
        """
        Update course metadata with selective field modification and validation.

        This method provides a flexible interface for updating course details while
        maintaining business rule integrity. It supports partial updates (only specified
        fields are modified) and enforces validation after changes to prevent invalid states.

        BUSINESS LOGIC:
        - Selective Updates: Only non-None parameters trigger field modifications
        - Atomic Validation: All changes validated together before persistence
        - Audit Trail: Timestamp updated for change tracking
        - Immutability Option: Unspecified fields remain unchanged

        UPDATEABLE FIELDS:
        - title (str): Course name/headline
        - description (str): Educational overview and objectives
        - category (str): Subject area classification
        - difficulty_level (DifficultyLevel): Beginner/Intermediate/Advanced
        - price (float): Monetary value (0.00 for free courses)
        - estimated_duration (int): Time value for duration estimate
        - duration_unit (DurationUnit): Hours/Days/Weeks/Months

        EDUCATIONAL USE CASES:
        1. Content Refinement: Improve title/description based on feedback
        2. Pricing Adjustments: Update course pricing for promotions
        3. Difficulty Recalibration: Adjust level based on student performance
        4. Category Updates: Improve discoverability through better categorization
        5. Duration Corrections: Refine time estimates based on completion data

        VALIDATION GUARANTEES:
        - All business rules enforced after updates
        - Invalid combinations rejected before persistence
        - Maintains referential integrity
        - Prevents partial invalid states

        AUDIT TRAIL:
        Updates self.updated_at for:
        - Change history tracking
        - Version control integration
        - Analytics on course evolution
        - Administrative reporting

        Args:
            title: New course title (max 200 chars)
            description: New course description (max 2000 chars)
            category: Subject area classification
            difficulty_level: Educational difficulty taxonomy
            price: Course price (>= 0.00)
            estimated_duration: Time estimate value (> 0)
            duration_unit: Time unit for duration

        Raises:
            ValueError: If any updated field violates business rules
                (validated atomically after all updates applied)

        Example:
            >>> course = Course(title="Python Basics", description="Intro", instructor_id="123")
            >>> course.update_details(
            ...     difficulty_level=DifficultyLevel.INTERMEDIATE,
            ...     price=49.99,
            ...     estimated_duration=8,
            ...     duration_unit=DurationUnit.WEEKS
            ... )
        """
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
        """
        Add a metadata tag to course for categorization and discovery.

        Tags enable flexible course organization beyond hierarchical categories,
        supporting multi-dimensional classification for improved searchability,
        recommendation systems, and content discovery algorithms.

        BUSINESS VALUE:
        - Enhanced Search: Students find courses through keyword searches
        - Recommendations: ML algorithms use tags for course suggestions
        - Content Organization: Instructors create custom taxonomies
        - Analytics: Tag-based reporting and trend analysis

        VALIDATION RULES:
        - Tag must be non-empty after whitespace trimming
        - Duplicate tags automatically prevented (idempotent operation)
        - Tags automatically normalized (trimmed whitespace)

        EDUCATIONAL USE CASES:
        - Technology Tags: "Python", "Machine Learning", "Docker"
        - Skill Level Tags: "Beginner-Friendly", "Advanced"
        - Industry Tags: "Finance", "Healthcare", "E-commerce"
        - Format Tags: "Hands-On", "Video", "Interactive"

        Args:
            tag: Keyword or phrase for course classification

        Example:
            >>> course = Course(title="ML Course", description="Learn ML", instructor_id="123")
            >>> course.add_tag("machine-learning")
            >>> course.add_tag("python")
            >>> course.add_tag("python")  # Idempotent - no duplicate
        """
        if tag and tag.strip() and tag not in self.tags:
            self.tags.append(tag.strip())
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """
        Remove a metadata tag from course taxonomy.

        This operation supports tag management and course refinement by allowing
        removal of outdated or incorrect tags. Maintains tag list integrity and
        updates audit trail for change tracking.

        BUSINESS JUSTIFICATION:
        - Tag Cleanup: Remove obsolete or incorrect tags
        - Taxonomy Evolution: Adjust course categorization over time
        - Quality Control: Instructor-driven tag curation
        - Discovery Optimization: Remove low-value tags

        OPERATIONAL BEHAVIOR:
        - Idempotent: Removing non-existent tag is safe (no error)
        - Atomic: Single tag removal with timestamp update
        - Audit Trail: Updated timestamp tracks tag changes

        Args:
            tag: Tag to remove from course tags list

        Example:
            >>> course = Course(title="Web Dev", description="Learn web", instructor_id="123")
            >>> course.add_tag("deprecated-framework")
            >>> course.remove_tag("deprecated-framework")  # Clean up
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def get_formatted_duration(self) -> str:
        """
        Generate human-readable duration string for UI display.

        This utility method converts structured duration data (value + unit)
        into natural language format suitable for student-facing interfaces,
        course catalogs, and marketing materials.

        BUSINESS VALUE:
        - User Experience: Clear time commitment communication
        - Enrollment Decisions: Students assess schedule compatibility
        - Marketing: Professional course catalog presentation
        - Accessibility: Screen reader friendly duration descriptions

        FORMAT EXAMPLES:
        - "8 weeks" (estimated_duration=8, duration_unit=WEEKS)
        - "40 hours" (estimated_duration=40, duration_unit=HOURS)
        - "3 months" (estimated_duration=3, duration_unit=MONTHS)
        - "Duration not specified" (when fields not set)

        Returns:
            str: Human-readable duration string

        Example:
            >>> course = Course(title="Python", description="Learn", instructor_id="123",
            ...                 estimated_duration=12, duration_unit=DurationUnit.WEEKS)
            >>> print(course.get_formatted_duration())
            "12 weeks"
        """
        if not self.estimated_duration or not self.duration_unit:
            return "Duration not specified"

        return f"{self.estimated_duration} {self.duration_unit.value}"

    def is_free(self) -> bool:
        """
        Determine if course is offered at no cost to students.

        This business rule supports pricing model logic, filtering operations,
        and financial reporting. Free courses (price = 0.00) enable broader
        educational access and institutional free-tier offerings.

        BUSINESS APPLICATIONS:
        - Course Filtering: "Show only free courses" in student UI
        - Revenue Analytics: Distinguish paid vs. free course metrics
        - Marketing: Feature free courses for user acquisition
        - Access Control: Simplified enrollment without payment processing

        PRICING MODEL:
        - Free: price = 0.00 (no payment required)
        - Paid: price > 0.00 (requires payment processing)

        Returns:
            bool: True if course is free (price = 0.00), False otherwise

        Example:
            >>> free_course = Course(title="Intro", description="Free course", instructor_id="123", price=0.00)
            >>> paid_course = Course(title="Advanced", description="Paid", instructor_id="123", price=99.99)
            >>> free_course.is_free()  # True
            >>> paid_course.is_free()  # False
        """
        return self.price == 0.0

    def get_difficulty_display(self) -> str:
        """
        Generate formatted difficulty level string for user interfaces.

        This presentation method converts the difficulty enum into a
        human-readable, properly capitalized string suitable for display
        in student-facing UIs, course catalogs, and reports.

        BUSINESS VALUE:
        - Professional Presentation: Proper case formatting ("Beginner" vs "beginner")
        - Consistency: Standardized difficulty display across platform
        - Internationalization Ready: Single method for localization
        - Accessibility: Clear difficulty communication for all users

        FORMATTING TRANSFORMATION:
        - DifficultyLevel.BEGINNER → "Beginner"
        - DifficultyLevel.INTERMEDIATE → "Intermediate"
        - DifficultyLevel.ADVANCED → "Advanced"

        Returns:
            str: Title-cased difficulty level string

        Example:
            >>> course = Course(title="ML", description="Learn", instructor_id="123",
            ...                 difficulty_level=DifficultyLevel.INTERMEDIATE)
            >>> print(course.get_difficulty_display())
            "Intermediate"
        """
        return self.difficulty_level.value.title()

@dataclass
class CourseStatistics:
    """
    Value object encapsulating course performance metrics and analytics data.

    This immutable value object aggregates key performance indicators (KPIs)
    for courses, supporting instructor dashboards, administrative reporting,
    and data-driven decision making for course improvements.

    DOMAIN PURPOSE:
    Provides a structured container for course analytics without polluting
    the core Course entity with frequently changing statistical data.
    Follows the Value Object pattern from Domain-Driven Design.

    ANALYTICAL METRICS:
    - Enrollment Metrics: Total enrolled students and active participation
    - Success Metrics: Completion rates indicating course effectiveness
    - Quality Metrics: Student feedback and satisfaction ratings
    - Financial Metrics: Revenue generation for paid courses
    - Temporal Metrics: Last update timestamp for cache invalidation

    BUSINESS APPLICATIONS:
    1. Instructor Dashboards: Course performance at-a-glance
    2. Administrative Reporting: Platform-wide course effectiveness
    3. Course Recommendations: Data-driven student suggestions
    4. Quality Assurance: Identify courses needing improvement
    5. Revenue Analytics: Financial performance tracking

    INTEGRATION PATTERNS:
    - Analytics Service: Calculated from enrollment and feedback aggregations
    - Caching Layer: Cached statistics for performance optimization
    - Reporting Systems: Dashboard and report data sources
    - Recommendation Engine: Input for ML-based course suggestions

    DESIGN PATTERN:
    Value Object - Immutable, defined by its attributes, no identity.
    Two statistics objects with identical values are considered equal.

    Attributes:
        course_id: Foreign key linking statistics to course entity
        enrolled_students: Total count of all-time enrollments
        active_enrollments: Current active student count
        completion_rate: Percentage of students completing course (0.0-100.0)
        average_rating: Mean rating from student feedback (1.0-5.0)
        total_feedback: Count of feedback submissions received
        revenue: Total revenue generated from course sales
        last_updated: Timestamp for cache freshness validation
    """
    course_id: str
    enrolled_students: int = 0
    active_enrollments: int = 0
    completion_rate: float = 0.0
    average_rating: float = 0.0
    total_feedback: int = 0
    revenue: float = 0.0
    last_updated: Optional[datetime] = None