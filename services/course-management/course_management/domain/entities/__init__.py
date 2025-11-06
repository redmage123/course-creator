"""
Course Management Domain Entities Package

This package contains all domain entities for the course-management microservice,
following Domain-Driven Design (DDD) principles and Clean Architecture patterns.

DOMAIN LAYER RESPONSIBILITY:
The entities in this package represent the core business concepts and rules for
educational course management, enrollment tracking, feedback systems, and
organizational project structures. These entities are framework-agnostic and
contain pure business logic without infrastructure concerns.

ENTITY CATALOG:

1. Course Entities (course.py):
   - Course: Core educational content entity with publication lifecycle
   - DifficultyLevel: Educational taxonomy (Beginner/Intermediate/Advanced)
   - DurationUnit: Time units for course duration estimation
   - CourseStatistics: Analytics value object for course performance metrics

2. Enrollment Entities (enrollment.py):
   - Enrollment: Student course participation lifecycle management
   - EnrollmentStatus: State taxonomy (Active/Completed/Suspended/Cancelled/Expired)
   - EnrollmentRequest: Value object for single enrollment creation
   - BulkEnrollmentRequest: Value object for batch enrollment operations

3. Feedback Entities (feedback.py):
   - CourseFeedback: Student feedback about courses
   - StudentFeedback: Instructor feedback about students
   - FeedbackResponse: Instructor responses to student feedback
   - FeedbackStatus: Lifecycle state (Active/Archived/Flagged)
   - FeedbackType: Timing taxonomy (Regular/Midterm/Final/Intervention)
   - ProgressAssessment: Qualitative progress levels
   - ExpectedOutcome: Predictive success forecasts
   - AcknowledgmentType: Response formality levels

4. Sub-Project Entities (sub_project.py):
   - SubProject: Organizational locations/instance of main project
   - Supports multi-locations training programs with independent scheduling

DESIGN PATTERNS:

Entity Pattern:
- Rich domain models with behavior, not anemic data containers
- Business rule enforcement through validation methods
- Immutable value objects for data integrity
- Clear separation of concerns

Value Object Pattern:
- CourseStatistics: Immutable analytics aggregation
- EnrollmentRequest/BulkEnrollmentRequest: Data transfer objects
- Defined by attributes, not identity

Domain Events (Implicit):
- Course publication triggers notification workflows
- Enrollment completion triggers certificate issuance
- Feedback submission triggers instructor notifications

BUSINESS INVARIANTS:
- Courses require instructor attribution before publication
- Enrollments must maintain progress percentage 0-100
- Feedback ratings constrained to 1-5 scale
- Sub-projects enforce capacity limits and date logic

INTEGRATION BOUNDARIES:
- Entities are persistence-agnostic (no database annotations)
- Infrastructure layer maps entities to database schema
- Application layer coordinates entity interactions
- API layer serializes entities for external communication

USAGE GUIDELINES:
1. Always create entities through their constructors (automatic validation)
2. Use entity methods for state changes (don't manipulate attributes directly)
3. Validate business rules before persistence operations
4. Use value objects for data transfer across layers
5. Maintain entity purity (no infrastructure dependencies)

EDUCATIONAL DOMAIN CONCEPTS:
- Courses: Educational content delivery units
- Enrollments: Student learning journey tracking
- Feedback: Bi-directional quality improvement system
- Projects/Sub-Projects: Organizational training program structure

For detailed entity documentation, see individual module docstrings.
"""