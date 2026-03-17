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

7. Project Builder Entities (project_builder.py):
   - ProjectBuilderSpec: Complete specification for AI-assisted project creation
   - LocationSpec: Specification for sub-projects (training locations)
   - TrackSpec: Specification for learning tracks with courses
   - CourseSpec: Specification for individual courses
   - InstructorSpec: Specification for instructor assignments
   - StudentSpec: Specification for student enrollments
   - ScheduleConfig: Configuration for schedule generation
   - ContentGenerationConfig: Configuration for content auto-generation
   - ZoomConfig: Configuration for Zoom room creation
   - ScheduleEntry: Individual scheduled session
   - ScheduleProposal: Generated schedule with conflict analysis
   - Conflict: Schedule conflict detection result
   - ProjectCreationResult: Result of bulk project creation
   - ProjectBuilderState: State machine states for conversation flow
   - ContentType: Types of auto-generated content
   - ConflictType: Types of scheduling conflicts
   - ZoomRoomType: Types of Zoom rooms to create

8. File Import Entities (file_import.py):
   - FileUpload: Metadata for uploaded roster files
   - ColumnMapping: Maps source columns to target fields
   - ParsedRoster: Container for parsed roster data
   - InstructorRosterEntry: Parsed instructor from roster file
   - StudentRosterEntry: Parsed student from roster file
   - RosterValidationResult: Validation results for roster
   - ValidationIssue: Individual validation issue
   - ImportProgress: Tracks multi-file import progress
   - FileFormat: Supported file formats (CSV, Excel, JSON)
   - RosterType: Types of rosters (instructor, student)
   - FileUploadStatus: Status of file processing

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

5. Learning Path Entities (learning_path.py):
   - LearningPath: Personalized learning journey for students
   - LearningPathNode: Individual steps in a learning path
   - PrerequisiteRule: Content dependency definitions
   - AdaptiveRecommendation: AI-driven learning suggestions
   - StudentMasteryLevel: Skill mastery tracking for spaced repetition
   - PathType/PathStatus/NodeStatus: State taxonomies
   - ContentType/RequirementType: Content classification enums
   - RecommendationType/RecommendationStatus: Recommendation lifecycle
   - MasteryLevel/DifficultyLevel: Educational progression levels

6. Peer Learning Entities (peer_learning.py):
   - StudyGroup: Collaborative learning groups for courses
   - StudyGroupMembership: User membership in study groups
   - PeerReview: Student-to-student assignment feedback
   - DiscussionThread: Course-specific threaded discussions
   - DiscussionReply: Replies to discussion threads
   - HelpRequest: Peer-to-peer help system
   - PeerReputation: Student reputation tracking
   - StudyGroupStatus/MembershipRole/MembershipStatus: Study group state taxonomies
   - PeerReviewStatus/ReviewQuality: Peer review state taxonomies
   - ThreadStatus: Discussion thread state taxonomy
   - HelpRequestStatus/HelpCategory: Help request state taxonomies
"""

from course_management.domain.entities.learning_path import (
    LearningPath,
    LearningPathNode,
    PrerequisiteRule,
    AdaptiveRecommendation,
    StudentMasteryLevel,
    PathType,
    PathStatus,
    NodeStatus,
    ContentType,
    RequirementType,
    RecommendationType,
    RecommendationStatus,
    MasteryLevel,
    DifficultyLevel,
    AdaptiveLearningException,
    NodeNotUnlockedException,
    InvalidProgressException,
    CannotSkipRequiredNodeException,
    InvalidPathStateException,
    InvalidFeedbackException,
    PrerequisiteNotMetException,
    LearningPathNotFoundException,
    RecommendationNotFoundException
)

from course_management.domain.entities.peer_learning import (
    StudyGroup,
    StudyGroupMembership,
    PeerReview,
    DiscussionThread,
    DiscussionReply,
    HelpRequest,
    PeerReputation,
    StudyGroupStatus,
    MembershipRole,
    MembershipStatus,
    PeerReviewStatus,
    ReviewQuality,
    ThreadStatus,
    HelpRequestStatus,
    HelpCategory,
    PeerLearningException,
    StudyGroupFullException,
    StudyGroupNotFoundException,
    NotGroupMemberException,
    InsufficientPermissionException,
    ReviewAssignmentException,
    HelpRequestNotFoundException
)

from course_management.domain.entities.project_builder import (
    # Main specification entities
    ProjectBuilderSpec,
    LocationSpec,
    TrackSpec,
    CourseSpec,
    InstructorSpec,
    StudentSpec,
    # Configuration entities
    ScheduleConfig,
    ContentGenerationConfig,
    ZoomConfig,
    # Schedule entities
    ScheduleEntry,
    ScheduleProposal,
    Conflict,
    # Result entities
    ProjectCreationResult,
    # Enumerations
    ProjectBuilderState,
    ContentType as ProjectContentType,  # Aliased to avoid conflict with learning_path.ContentType
    ConflictType,
    ZoomRoomType,
    # Exceptions
    ProjectBuilderException,
    InvalidSpecificationException,
    ScheduleConflictException,
    RosterParseException,
    ZoomConfigurationException,
    ContentGenerationException
)

from course_management.domain.entities.file_import import (
    # File upload entities
    FileUpload,
    ColumnMapping,
    ColumnAlias,
    ParsedRoster,
    # Roster entry entities
    InstructorRosterEntry,
    StudentRosterEntry,
    # Validation entities
    ValidationIssue,
    RosterValidationResult,
    ImportProgress,
    # Column alias configurations
    INSTRUCTOR_COLUMN_ALIASES,
    STUDENT_COLUMN_ALIASES,
    # Enumerations
    FileFormat,
    RosterType,
    FileUploadStatus,
    ValidationSeverity,
    # Exceptions
    FileImportException,
    UnsupportedFileFormatException,
    MissingRequiredColumnException,
    InvalidDataException,
    EmptyFileException,
    DuplicateEntryException
)

__all__ = [
    # Learning Path Entities
    'LearningPath',
    'LearningPathNode',
    'PrerequisiteRule',
    'AdaptiveRecommendation',
    'StudentMasteryLevel',
    'PathType',
    'PathStatus',
    'NodeStatus',
    'ContentType',
    'RequirementType',
    'RecommendationType',
    'RecommendationStatus',
    'MasteryLevel',
    'DifficultyLevel',
    'AdaptiveLearningException',
    'NodeNotUnlockedException',
    'InvalidProgressException',
    'CannotSkipRequiredNodeException',
    'InvalidPathStateException',
    'InvalidFeedbackException',
    'PrerequisiteNotMetException',
    'LearningPathNotFoundException',
    'RecommendationNotFoundException',
    # Peer Learning Entities
    'StudyGroup',
    'StudyGroupMembership',
    'PeerReview',
    'DiscussionThread',
    'DiscussionReply',
    'HelpRequest',
    'PeerReputation',
    'StudyGroupStatus',
    'MembershipRole',
    'MembershipStatus',
    'PeerReviewStatus',
    'ReviewQuality',
    'ThreadStatus',
    'HelpRequestStatus',
    'HelpCategory',
    'PeerLearningException',
    'StudyGroupFullException',
    'StudyGroupNotFoundException',
    'NotGroupMemberException',
    'InsufficientPermissionException',
    'ReviewAssignmentException',
    'HelpRequestNotFoundException',
    # Project Builder Entities
    'ProjectBuilderSpec',
    'LocationSpec',
    'TrackSpec',
    'CourseSpec',
    'InstructorSpec',
    'StudentSpec',
    'ScheduleConfig',
    'ContentGenerationConfig',
    'ZoomConfig',
    'ScheduleEntry',
    'ScheduleProposal',
    'Conflict',
    'ProjectCreationResult',
    'ProjectBuilderState',
    'ProjectContentType',
    'ConflictType',
    'ZoomRoomType',
    'ProjectBuilderException',
    'InvalidSpecificationException',
    'ScheduleConflictException',
    'RosterParseException',
    'ZoomConfigurationException',
    'ContentGenerationException',
    # File Import Entities
    'FileUpload',
    'ColumnMapping',
    'ColumnAlias',
    'ParsedRoster',
    'InstructorRosterEntry',
    'StudentRosterEntry',
    'ValidationIssue',
    'RosterValidationResult',
    'ImportProgress',
    'INSTRUCTOR_COLUMN_ALIASES',
    'STUDENT_COLUMN_ALIASES',
    'FileFormat',
    'RosterType',
    'FileUploadStatus',
    'ValidationSeverity',
    'FileImportException',
    'UnsupportedFileFormatException',
    'MissingRequiredColumnException',
    'InvalidDataException',
    'EmptyFileException',
    'DuplicateEntryException'
]