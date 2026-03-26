"""
API Data Transfer Objects (DTOs) for Analytics Service

BUSINESS CONTEXT:
These Pydantic models define the contract between API consumers and the analytics service.
They implement educational activity tracking standards and learning analytics data models.

TECHNICAL IMPLEMENTATION:
- Request models: Validate incoming data from API clients
- Response models: Structure outgoing data for API consumers
- Follow Single Responsibility Principle: Each model handles one data structure

SOLID PRINCIPLES:
- Single Responsibility: Each model represents one coherent data concept
- Open/Closed: Models can be extended through inheritance
- Liskov Substitution: All models follow BaseModel contract
- Interface Segregation: Models are focused and minimal
- Dependency Inversion: Models depend on Pydantic abstractions

EDUCATIONAL STANDARDS:
- Implements xAPI (Experience API) standards for activity tracking
- Follows FERPA compliance requirements for student data
- Supports educational data interoperability
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ========================================
# Request Models (Input DTOs)
# ========================================

class StudentActivityRequest(BaseModel):
    """
    Request model for recording student learning activities.

    Implements educational activity tracking standards based on xAPI (Experience API)
    and learning analytics research. Captures both explicit learning actions and
    implicit behavioral indicators for comprehensive learning analytics.

    Educational Context:
    - Supports micro-learning activity tracking
    - Enables learning behavior pattern analysis
    - Facilitates engagement measurement
    - Provides data for predictive learning models

    Privacy Considerations:
    - IP address collection is optional and can be disabled for privacy
    - User agent data helps identify technical barriers to learning
    - Session tracking enables learning session analysis while maintaining anonymity
    """
    student_id: str
    course_id: str
    activity_type: str = Field(..., description="Activity type (login, quiz_start, etc.)")
    activity_data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class LabUsageRequest(BaseModel):
    """
    Request model for recording laboratory learning environment usage.

    Captures hands-on learning analytics specific to coding laboratories,
    implementing research-based metrics for practical skill development.

    Educational Methodologies:
    - Active learning measurement through action counting
    - Problem-solving analytics via error tracking
    - Skill development progression through execution patterns
    - Code quality assessment through final code analysis

    Learning Analytics Applications:
    - Identifies struggling students through error patterns
    - Measures hands-on engagement and persistence
    - Tracks practical skill development over time
    - Enables personalized coding assistance recommendations
    """
    student_id: str
    course_id: str
    lab_id: str
    actions_performed: int = 0
    code_executions: int = 0
    errors_encountered: int = 0
    final_code: Optional[str] = None


class QuizPerformanceRequest(BaseModel):
    """
    Request model for comprehensive quiz performance analytics.

    Implements psychometric measurement principles and educational assessment
    analytics to capture both performance outcomes and learning processes.

    Assessment Analytics Features:
    - Item-level response analysis for diagnostic assessment
    - Time-based performance measurement for cognitive load analysis
    - Attempt pattern tracking for learning strategy analysis
    - Question-by-question timing for attention and difficulty analysis

    Educational Research Applications:
    - Identifies knowledge gaps through response patterns
    - Measures cognitive load through timing analysis
    - Tracks learning strategy effectiveness
    - Enables adaptive assessment through difficulty analysis

    FERPA Compliance:
    - Individual responses are encrypted and anonymized for research
    - Aggregate analytics protect individual student privacy
    - Detailed data access requires appropriate permissions
    """
    student_id: str
    course_id: str
    quiz_id: str
    attempt_number: int = 1
    questions_total: int
    questions_answered: int = 0
    questions_correct: int = 0
    answers: Dict[str, Any] = Field(default_factory=dict)
    time_per_question: Dict[str, float] = Field(default_factory=dict)


class ProgressUpdateRequest(BaseModel):
    """
    Request model for updating student learning progress.

    Implements competency-based education (CBE) principles and mastery learning
    analytics to track genuine learning progression rather than just completion.

    Learning Science Foundations:
    - Mastery-based progression tracking
    - Time-to-mastery analytics
    - Learning velocity measurement
    - Competency demonstration validation

    Educational Applications:
    - Supports personalized learning pace
    - Enables mastery-based advancement
    - Tracks learning efficiency over time
    - Identifies optimal learning paths

    Progress Analytics:
    - Granular progress tracking (0-100% with validation)
    - Time investment analysis for learning efficiency
    - Mastery score validation for competency demonstration
    - Content type-specific progression modeling
    """
    student_id: str
    course_id: str
    content_item_id: str
    content_type: str = Field(..., pattern="^(module|lesson|lab|quiz|assignment|exercise)$")
    progress_percentage: float = Field(..., ge=0, le=100)
    time_spent_additional: int = Field(default=0, ge=0)
    mastery_score: Optional[float] = Field(None, ge=0, le=100)


class AnalyticsRequest(BaseModel):
    """
    Request model for comprehensive learning analytics generation and reporting.

    Supports flexible analytics queries with configurable parameters for
    different educational research needs and reporting requirements.

    Educational Research Support:
    - Longitudinal learning analytics with configurable time periods
    - Multi-dimensional metric analysis (engagement, performance, progress)
    - Flexible aggregation for different research granularities
    - Multiple export formats for research and institutional reporting

    Analytics Methodologies:
    - Daily aggregation for immediate instructional feedback
    - Weekly aggregation for learning trend analysis
    - Monthly aggregation for course-level effectiveness measurement

    Reporting Standards:
    - JSON format for real-time dashboard integration
    - CSV format for statistical analysis and research
    - PDF format for institutional and stakeholder reporting
    """
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = Field(default_factory=list)
    aggregation: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")
    format: str = Field(default="json", pattern="^(json|csv|pdf)$")
    export_format: Optional[str] = None  # Alias for format


# ========================================
# Response Models (Output DTOs)
# ========================================

class StudentActivityResponse(BaseModel):
    """
    Response model for student activity data with educational context.

    Provides standardized activity data format for learning analytics
    tools and educational research platforms.

    Educational Data Standards:
    - Follows xAPI (Experience API) principles for activity tracking
    - Provides temporal data for learning pattern analysis
    - Includes contextual data for educational effectiveness measurement
    - Supports learning analytics interoperability
    """
    id: str
    student_id: str
    course_id: str
    activity_type: str
    timestamp: datetime
    activity_data: Dict[str, Any]
    session_id: Optional[str] = None


class EngagementScoreResponse(BaseModel):
    """
    Response model for student engagement analytics.

    Implements multi-dimensional engagement measurement based on educational
    research on student engagement and learning motivation.

    Engagement Analytics Framework:
    - Quantitative engagement scoring (0-100 scale)
    - Temporal engagement analysis over configurable periods
    - Activity breakdown for engagement pattern identification
    - Comparative analysis capability for locations studies

    Educational Applications:
    - Early warning system for disengaged students
    - Instructional design feedback through engagement patterns
    - Personalized learning recommendations
    - Course effectiveness measurement
    """
    student_id: str
    course_id: str
    engagement_score: float
    calculation_date: datetime
    days_analyzed: int
    activity_breakdown: Dict[str, int]


class LearningAnalyticsResponse(BaseModel):
    """
    Response model for comprehensive learning analytics.

    Provides a holistic view of student learning incorporating multiple
    educational metrics and research-based learning indicators.
    """
    # New flexible format fields
    data_range: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    detailed_data: Optional[Dict[str, Any]] = None
    recommendations: List[str] = Field(default_factory=list)
    request_id: Optional[str] = None
    generated_at: Optional[datetime] = None

    # Legacy detailed fields (all optional for backward compatibility)
    id: Optional[str] = None
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    analysis_date: Optional[datetime] = None
    engagement_score: Optional[float] = None
    progress_velocity: Optional[float] = None
    lab_proficiency: Optional[float] = None
    quiz_performance: Optional[float] = None
    time_on_platform: Optional[int] = None
    streak_days: Optional[int] = None
    risk_level: Optional[str] = None
    overall_performance: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        """Auto-populate request_id and generated_at if not provided."""
        import uuid
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()


class CourseAnalyticsSummaryResponse(BaseModel):
    """
    Response model for course-wide learning analytics summary.

    Provides institutional and instructional analytics for course effectiveness
    measurement and educational improvement initiatives.

    Course-Level Analytics:
    - Enrollment and participation analytics
    - Learning outcome effectiveness measurement
    - Risk distribution for early intervention planning
    - Performance benchmarking and comparison
    - High performer identification for peer learning
    - At-risk student identification for support services

    Educational Leadership Applications:
    - Course quality assurance and improvement
    - Resource allocation optimization
    - Faculty development and support
    - Student success initiative planning
    - Institutional effectiveness reporting
    """
    course_id: str
    total_students: int
    averages: Dict[str, float]
    risk_distribution: Dict[str, int]
    high_performers: List[Dict[str, Any]]
    at_risk_students: List[Dict[str, Any]]
    last_updated: datetime


class ReportResponse(BaseModel):
    """
    Response model for comprehensive analytics reports.

    Supports multi-format reporting for different educational stakeholders
    and research requirements with timestamps for audit trails.

    Report Types and Applications:
    - Student Reports: Individual learning progress and recommendations
    - Course Reports: Instructional effectiveness and improvement insights
    - Institutional Reports: Program effectiveness and resource optimization
    - Research Reports: Educational data for academic research

    Compliance and Privacy:
    - Audit trail with generation timestamps
    - Report type classification for access control
    - Format specification for appropriate data handling
    - Export URL for secure report delivery
    """
    report_id: str
    generated_at: datetime
    report_type: str
    format: str
    data: Dict[str, Any]
    export_url: Optional[str] = None
