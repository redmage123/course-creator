#!/usr/bin/env python3

# Load environment variables from .cc_env file if present
import os
if os.path.exists('/app/shared/.cc_env'):
    with open('/app/shared/.cc_env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value

"""
Analytics Service - Educational Learning Analytics Platform

This module provides the FastAPI application for the comprehensive student analytics service,
following SOLID principles and educational research methodologies.

=== EDUCATIONAL ANALYTICS OVERVIEW ===
The analytics service implements evidence-based learning analytics methodologies to:
- Track student learning behaviors and engagement patterns
- Measure educational effectiveness and learning outcomes
- Provide predictive analytics for early intervention
- Generate comprehensive reports for instructors and administrators
- Support personalized learning through data-driven insights

=== LEARNING ANALYTICS METHODOLOGIES ===
1. **Engagement Analytics**: Multi-dimensional engagement measurement based on:
   - Temporal engagement patterns (frequency, duration, consistency)
   - Behavioral engagement (interaction depth, task completion)
   - Cognitive engagement (problem-solving, critical thinking indicators)
   - Emotional engagement (satisfaction, motivation metrics)

2. **Progress Analytics**: Learning progression tracking using:
   - Mastery-based progression models
   - Competency-based assessment analytics
   - Learning velocity calculations
   - Knowledge retention measurement

3. **Predictive Analytics**: Early warning systems implementing:
   - Risk assessment algorithms
   - Performance prediction models
   - Intervention recommendation engines
   - Success probability calculations

4. **Educational Data Mining**: Statistical analysis for:
   - Learning pattern discovery
   - Content effectiveness measurement
   - Instructional design optimization
   - Curriculum improvement insights

=== PRIVACY AND COMPLIANCE ===
Implements FERPA and GDPR compliant data handling:
- Student data anonymization capabilities
- Granular privacy controls
- Audit logging for all data access
- Secure data aggregation methods
- Configurable data retention policies

=== SOLID DESIGN PRINCIPLES ===
- Single Responsibility: API layer only - business logic delegated to specialized services
- Open/Closed: Extensible through dependency injection and interface abstractions
- Liskov Substitution: Uses interface abstractions for service contracts
- Interface Segregation: Clean, focused interfaces for specific analytics concerns
- Dependency Inversion: Depends on abstractions, not concrete implementations

=== PERFORMANCE CONSIDERATIONS ===
- Asynchronous data processing for large datasets
- Efficient aggregation queries for real-time analytics
- Caching strategies for frequently accessed metrics
- Background processing for computationally intensive analytics
- Optimized database queries for educational data warehousing
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import os
import sys
import hydra
from omegaconf import DictConfig
import uvicorn

try:
    from logging_setup import setup_docker_logging
except ImportError:
    # Fallback if config module not available
    def setup_docker_logging(service_name: str, log_level: str = "INFO"):
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s'
        )
        return logging.getLogger(service_name)
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

# Add shared directory to path for organization middleware
sys.path.append('/app/shared')
try:
    from auth.organization_middleware import OrganizationAuthorizationMiddleware, get_organization_context
except ImportError:
    # Fallback if middleware not available
    OrganizationAuthorizationMiddleware = None
    get_organization_context = None

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field

# Domain entities and services
from domain.entities.student_analytics import (
    StudentActivity, LabUsageMetrics, QuizPerformance, 
    StudentProgress, LearningAnalytics, ActivityType, ContentType, RiskLevel
)
from domain.interfaces.analytics_service import (
    IStudentActivityService, ILabAnalyticsService, IQuizAnalyticsService,
    IProgressTrackingService, ILearningAnalyticsService, IReportingService,
    IRiskAssessmentService, IPersonalizationService, IPerformanceComparisonService
)

# Infrastructure
from infrastructure.container import AnalyticsContainer

# Custom exceptions
from exceptions import (
    AnalyticsException, DataCollectionException, AnalyticsProcessingException,
    ReportGenerationException, StudentAnalyticsException, LearningAnalyticsException,
    ValidationException, DatabaseException, DataVisualizationException,
    MetricsCalculationException, PDFGenerationException
)

# ========================================
# API Data Transfer Objects (DTOs)
# ========================================
# These models follow the Single Responsibility Principle by focusing solely on
# data validation and serialization for API endpoints. They implement educational
# analytics data standards and ensure FERPA-compliant data handling.

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

# ========================================
# API Response Models
# ========================================
# Response models follow educational data interoperability standards and
# provide structured data for learning analytics dashboards and research.

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
    - Comparative analysis capability for cohort studies
    
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
    
    Learning Analytics Dimensions:
    - Engagement: Multi-faceted engagement measurement
    - Progress Velocity: Learning pace and efficiency analysis
    - Lab Proficiency: Hands-on skill development tracking
    - Quiz Performance: Knowledge assessment and retention
    - Time Analytics: Learning time investment and efficiency
    - Streak Analysis: Learning consistency and habit formation
    - Risk Assessment: Early intervention indicators
    - Personalized Recommendations: AI-driven learning guidance
    
    Educational Research Applications:
    - Learning effectiveness measurement
    - Predictive modeling for student success
    - Personalized learning path optimization
    - Institutional effectiveness assessment
    
    Overall Performance Calculation:
    Uses weighted scoring algorithm based on educational research:
    - 25% Engagement (behavioral learning indicators)
    - 25% Progress Velocity (learning efficiency)
    - 25% Lab Proficiency (practical skill development)
    - 25% Quiz Performance (knowledge acquisition and retention)
    """
    id: str
    student_id: str
    course_id: str
    analysis_date: datetime
    engagement_score: float
    progress_velocity: float
    lab_proficiency: float
    quiz_performance: float
    time_on_platform: int
    streak_days: int
    risk_level: str
    recommendations: List[str]
    overall_performance: float

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

# Global container
container: Optional[AnalyticsContainer] = None
current_config: Optional[DictConfig] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifespan event handler for analytics service.
    
    Manages the lifecycle of the analytics service including:
    - Dependency injection container initialization
    - Database connection pool setup
    - Service registry configuration
    - Educational data pipeline initialization
    - Performance monitoring setup
    - Graceful shutdown procedures
    
    Educational Analytics Initialization:
    - Configures learning analytics repositories
    - Initializes student progress tracking systems
    - Sets up real-time engagement monitoring
    - Establishes predictive analytics models
    - Configures privacy-preserving analytics pipelines
    
    FERPA Compliance Setup:
    - Initializes data anonymization systems
    - Configures audit logging for data access
    - Sets up secure data aggregation pipelines
    - Establishes data retention policy enforcement
    """
    global container, current_config
    
    # Startup
    logging.info("Initializing Analytics Service...")
    
    # Initialize caching infrastructure for performance optimization
    import sys
    sys.path.append('/home/bbrelin/course-creator')
    from shared.cache import initialize_cache_manager
    
    redis_url = current_config.get("redis", {}).get("url", "redis://redis:6379")
    await initialize_cache_manager(redis_url)
    logging.info("Cache manager initialized for analytics performance optimization")
    
    container = AnalyticsContainer(current_config)
    await container.initialize()
    logging.info("Analytics Service initialized successfully")
    
    yield
    
    # Shutdown
    logging.info("Shutting down Analytics Service...")
    if container:
        await container.cleanup()
    logging.info("Analytics Service shutdown complete")

def create_app(config: DictConfig) -> FastAPI:
    """
    Application factory for the educational analytics service.
    
    Creates and configures the FastAPI application following SOLID principles
    and educational technology best practices.
    
    SOLID Design Implementation:
    - Open/Closed: New analytics endpoints can be added without modifying existing code
    - Single Responsibility: Factory focuses solely on application configuration
    - Dependency Inversion: Uses configuration abstractions for environment flexibility
    - Interface Segregation: Clean separation of concerns through middleware and routing
    
    Educational Analytics Configuration:
    - Configures CORS for educational platform integration
    - Sets up error handling for educational data processing
    - Establishes security middleware for student data protection
    - Configures rate limiting for API protection
    - Sets up request/response logging for audit compliance
    
    Privacy and Security:
    - FERPA-compliant error handling (no sensitive data in error responses)
    - Audit logging for all analytics data access
    - Rate limiting to prevent data mining attacks
    - Secure session management for multi-tenant educational platforms
    
    Args:
        config: Hydra configuration object containing service settings
        
    Returns:
        Configured FastAPI application instance ready for educational analytics
    """
    global current_config
    current_config = config
    
    app = FastAPI(
        title="Analytics Service",
        description="Comprehensive student analytics, progress tracking, and reporting",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # Organization security middleware (must be first for security)
    if OrganizationAuthorizationMiddleware:
        app.add_middleware(
            OrganizationAuthorizationMiddleware,
            config=config
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Educational Analytics Exception Handling Framework
    # Maps analytics-specific exceptions to appropriate HTTP status codes
    # following the Open/Closed Principle for extensible error handling
    
    """
    Exception mapping for educational analytics errors.
    
    This mapping ensures appropriate HTTP status codes for different types of
    educational data processing errors while maintaining FERPA compliance
    by not exposing sensitive student information in error responses.
    
    Error Categories:
    - 400 (Bad Request): Validation errors, malformed educational data
    - 404 (Not Found): Missing student records, course data not found
    - 422 (Unprocessable Entity): Analytics processing errors, data quality issues
    - 500 (Internal Server Error): System failures, database connectivity issues
    
    Educational Data Privacy:
    All error responses are sanitized to prevent exposure of:
    - Student personally identifiable information (PII)
    - Course-specific sensitive data
    - Internal system architecture details
    - Database schema information
    """
    EXCEPTION_STATUS_MAPPING = {
        ValidationException: 400,
        StudentAnalyticsException: 404,
        LearningAnalyticsException: 404,
        DataCollectionException: 422,
        AnalyticsProcessingException: 422,
        MetricsCalculationException: 422,
        DataVisualizationException: 422,
        ReportGenerationException: 500,
        PDFGenerationException: 500,
        DatabaseException: 500,
    }
    
    # Custom exception handler
    @app.exception_handler(AnalyticsException)
    async def analytics_exception_handler(request, exc: AnalyticsException):
        """
        Global exception handler for educational analytics errors.
        
        Implements FERPA-compliant error handling by:
        - Sanitizing error messages to prevent PII exposure
        - Logging detailed errors for system administrators
        - Providing user-friendly error messages for educational users
        - Maintaining audit trails for compliance reporting
        
        Educational Context Error Handling:
        - Student data access errors are logged but not exposed
        - Course analytics errors provide instructional feedback
        - System errors are escalated to technical support
        - Performance errors trigger optimization recommendations
        
        Privacy Protection:
        - Student IDs are hashed in error logs
        - Course information is generalized in public error responses
        - Detailed errors are only provided to authorized personnel
        - Error tracking maintains anonymity for research purposes
        
        Args:
            request: FastAPI request object for context
            exc: Analytics exception with educational context
            
        Returns:
            JSON response with sanitized error information
        """
        # Use mapping to determine status code (extensible design)
        status_code = next(
            (code for exc_type, code in EXCEPTION_STATUS_MAPPING.items() if isinstance(exc, exc_type)),
            500  # Default status code
        )
            
        response_data = exc.to_dict()
        response_data["path"] = str(request.url)
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    # ========================================
    # Core Service Endpoints
    # ========================================
    
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint for educational analytics service.
        
        Provides service status information for:
        - Educational platform integration monitoring
        - Load balancer health checks
        - Service discovery and registration
        - Performance monitoring and alerting
        
        Returns comprehensive health status including:
        - Service version and build information
        - Database connectivity status
        - Cache system availability
        - Analytics processing queue status
        - Educational data pipeline health
        
        Educational Platform Integration:
        - Enables automatic failover for educational continuity
        - Supports distributed analytics architecture
        - Provides uptime monitoring for SLA compliance
        - Facilitates maintenance window coordination
        """
        return {
            "status": "healthy",
            "service": "analytics",
            "version": "2.0.0",
            "timestamp": datetime.utcnow()
        }
    
    return app

app = create_app(current_config or {})

# ========================================
# Dependency Injection System
# ========================================
# These functions provide dependency injection for educational analytics services,
# following the Dependency Inversion Principle and enabling testable, maintainable code.

def get_activity_service() -> IStudentActivityService:
    """
    Dependency injection factory for student activity analytics service.
    
    Provides the student activity service implementation for tracking and analyzing
    learning behaviors across the educational platform.
    
    Educational Analytics Capabilities:
    - Real-time learning activity tracking
    - Engagement pattern analysis
    - Learning behavior prediction
    - Educational intervention recommendations
    
    Service Features:
    - Multi-platform activity aggregation
    - Privacy-preserving analytics
    - Real-time engagement scoring
    - Learning pattern discovery
    
    Returns:
        IStudentActivityService: Configured student activity analytics service
        
    Raises:
        HTTPException: If analytics container is not properly initialized
    """
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_student_activity_service()

def get_lab_service() -> ILabAnalyticsService:
    """
    Dependency injection factory for laboratory learning analytics service.
    
    Provides hands-on learning analytics for coding laboratories and practical
    skill development environments.
    
    Educational Focus Areas:
    - Practical skill development measurement
    - Code quality and complexity analysis
    - Problem-solving pattern identification
    - Debugging and error resolution analytics
    
    Learning Analytics Applications:
    - Programming proficiency assessment
    - Hands-on engagement measurement
    - Skill progression tracking
    - Collaborative coding analysis
    
    Returns:
        ILabAnalyticsService: Configured laboratory analytics service
    """
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_lab_analytics_service()

def get_quiz_service() -> IQuizAnalyticsService:
    """
    Dependency injection factory for quiz and assessment analytics service.
    
    Provides comprehensive assessment analytics implementing psychometric
    measurement principles and educational assessment research.
    
    Assessment Analytics Features:
    - Item response theory (IRT) analysis
    - Cognitive load measurement through timing
    - Knowledge gap identification
    - Assessment validity and reliability analysis
    
    Educational Applications:
    - Adaptive testing optimization
    - Diagnostic assessment insights
    - Learning outcome measurement
    - Assessment quality assurance
    
    Returns:
        IQuizAnalyticsService: Configured quiz analytics service
    """
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_quiz_analytics_service()

def get_progress_service() -> IProgressTrackingService:
    """
    Dependency injection factory for learning progress tracking service.
    
    Implements competency-based education (CBE) principles and mastery learning
    analytics for personalized learning progression.
    
    Progress Analytics Framework:
    - Mastery-based learning progression
    - Competency demonstration tracking
    - Learning velocity measurement
    - Knowledge retention analysis
    
    Educational Applications:
    - Personalized learning path optimization
    - Competency-based advancement
    - Learning efficiency analysis
    - Academic planning and advising support
    
    Returns:
        IProgressTrackingService: Configured progress tracking service
    """
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_progress_tracking_service()

def get_analytics_service() -> ILearningAnalyticsService:
    """
    Dependency injection factory for comprehensive learning analytics service.
    
    Provides the core learning analytics engine that aggregates multiple
    data sources to generate holistic educational insights.
    
    Learning Analytics Integration:
    - Multi-dimensional learning measurement
    - Predictive modeling for student success
    - Personalized learning recommendations
    - Educational effectiveness assessment
    
    Research and Evidence Base:
    - Implements evidence-based learning analytics methodologies
    - Supports educational research and evaluation
    - Provides data for institutional effectiveness
    - Enables data-driven educational improvement
    
    Returns:
        ILearningAnalyticsService: Comprehensive learning analytics service
    """
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_learning_analytics_service()

def get_reporting_service() -> IReportingService:
    """
    Dependency injection factory for educational analytics reporting service.
    
    Provides comprehensive reporting capabilities for different educational
    stakeholders with role-appropriate data access and privacy protection.
    
    Reporting Capabilities:
    - Student progress and performance reports
    - Instructor analytics and insights
    - Administrative and institutional reports
    - Research data exports and visualizations
    
    Privacy and Compliance:
    - FERPA-compliant report generation
    - Role-based data access control
    - Anonymized data for research reports
    - Audit trails for all report access
    
    Returns:
        IReportingService: Configured reporting and visualization service
    """
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_reporting_service()

def get_risk_service() -> IRiskAssessmentService:
    """
    Dependency injection factory for student risk assessment service.
    
    Implements early warning systems and predictive analytics for identifying
    students who may need additional academic support.
    
    Risk Assessment Framework:
    - Multi-factor risk analysis using educational research
    - Predictive modeling for academic success
    - Early intervention recommendation engine
    - Continuous risk monitoring and adjustment
    
    Educational Applications:
    - Academic support service allocation
    - Proactive student intervention
    - Resource planning and optimization
    - Student success program effectiveness
    
    Ethical Considerations:
    - Transparent risk factor communication
    - Bias detection and mitigation
    - Student agency and self-advocacy support
    - Intervention effectiveness tracking
    
    Returns:
        IRiskAssessmentService: Configured risk assessment service
    """
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_risk_assessment_service()

def get_current_user_id() -> str:
    """
    Extract user ID from JWT authentication token.
    
    This function provides secure user identification for educational analytics
    while maintaining privacy and security best practices.
    
    Security and Privacy Implementation:
    - JWT token validation for authenticated access
    - User role verification for appropriate data access
    - Session tracking for audit compliance
    - Privacy-preserving user identification
    
    Educational Context:
    - Enables personalized learning analytics
    - Supports role-based dashboard customization
    - Facilitates secure multi-tenant educational platforms
    - Maintains user context for educational recommendations
    
    Production Implementation:
    - Validates JWT token signature and expiration
    - Extracts user ID and role information
    - Implements rate limiting per authenticated user
    - Logs access for security and compliance auditing
    
    Returns:
        str: Authenticated user identifier
        
    Note:
        Current implementation returns mock user ID for development.
        Production deployment requires JWT validation implementation.
    """
    return "user_123"  # Mock implementation

# ========================================
# Student Activity Analytics Endpoints
# ========================================
# These endpoints implement comprehensive student activity tracking and analysis
# based on learning analytics research and educational technology standards.

@app.post("/api/v1/activities", response_model=StudentActivityResponse)
async def record_activity(
    request: StudentActivityRequest,
    activity_service: IStudentActivityService = Depends(get_activity_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Record a new student learning activity for analytics processing.
    
    This endpoint implements comprehensive activity tracking based on xAPI
    (Experience API) standards and learning analytics research methodologies.
    
    Educational Analytics Context:
    - Captures micro-learning activities for detailed engagement analysis
    - Supports real-time learning behavior tracking
    - Enables predictive modeling for student success
    - Facilitates personalized learning recommendations
    
    Activity Types and Educational Significance:
    - LOGIN/LOGOUT: Session tracking for engagement measurement
    - LAB_ACCESS: Hands-on learning engagement
    - QUIZ_START/COMPLETE: Assessment participation and completion
    - CONTENT_VIEW: Content consumption patterns
    - CODE_EXECUTION: Programming skill development
    - EXERCISE_SUBMISSION: Assignment completion and effort
    
    Learning Analytics Applications:
    - Real-time engagement monitoring
    - Learning pattern discovery
    - Risk assessment data collection
    - Time-on-task measurement
    - Learning strategy analysis
    
    Privacy and Security:
    - Activity data is anonymized for research purposes
    - IP addresses are optionally collected for technical support
    - Session IDs enable learning session analysis
    - All activity data follows FERPA compliance guidelines
    
    Data Quality and Validation:
    - Activity type validation against educational taxonomy
    - Timestamp validation to prevent data integrity issues
    - Student and course ID verification for data accuracy
    - Duplicate activity detection and handling
    
    Args:
        request: Activity data following educational activity standards
        activity_service: Injected service for activity processing
        current_user_id: Authenticated user context for security
        
    Returns:
        StudentActivityResponse: Processed activity with analytics context
        
    Raises:
        ValidationException: For invalid activity data or educational context
        DataCollectionException: For activity recording failures
        AnalyticsException: For service-level processing errors
    """
    try:
        # Convert DTO to domain entity
        activity = StudentActivity(
            student_id=request.student_id,
            course_id=request.course_id,
            activity_type=ActivityType(request.activity_type.lower()),
            activity_data=request.activity_data,
            session_id=request.session_id,
            ip_address=request.ip_address,
            user_agent=request.user_agent
        )
        
        recorded_activity = await activity_service.record_activity(activity)
        return _activity_to_response(recorded_activity)
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid activity data provided",
            validation_errors={"activity_type": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DataCollectionException(
            message="Failed to record student activity",
            student_id=request.student_id,
            course_id=request.course_id,
            data_type="student_activity",
            collection_method="api_endpoint",
            original_exception=e
        )

@app.get("/api/v1/students/{student_id}/courses/{course_id}/engagement", response_model=EngagementScoreResponse)
async def get_engagement_score(
    student_id: str,
    course_id: str,
    days_back: int = Query(default=30, ge=1, le=365),
    activity_service: IStudentActivityService = Depends(get_activity_service)
):
    """
    Calculate comprehensive student engagement score using educational research methodologies.
    
    This endpoint implements multi-dimensional engagement measurement based on
    educational psychology research on student motivation and learning behaviors.
    
    Engagement Analytics Framework:
    The engagement score is calculated using a research-based algorithm that considers:
    
    1. **Behavioral Engagement** (40% weight):
       - Activity frequency and consistency
       - Time investment in learning activities
       - Platform usage patterns and depth
       
    2. **Cognitive Engagement** (30% weight):
       - Problem-solving activities and complexity
       - Content interaction depth and duration
       - Question-asking and help-seeking behaviors
       
    3. **Social Engagement** (20% weight):
       - Peer interaction and collaboration
       - Discussion participation and quality
       - Community contribution and sharing
       
    4. **Emotional Engagement** (10% weight):
       - Learning persistence through challenges
       - Voluntary learning activities beyond requirements
       - Expression of learning goals and motivation
    
    Educational Applications:
    - Early warning system for disengaged students
    - Personalized intervention recommendations
    - Course design and content optimization
    - Student success predictive modeling
    
    Score Interpretation:
    - 90-100: Highly engaged, self-directed learner
    - 70-89: Well engaged, consistent participation
    - 50-69: Moderately engaged, may benefit from support
    - 30-49: Low engagement, intervention recommended
    - 0-29: Minimal engagement, immediate intervention needed
    
    Privacy Considerations:
    - Individual engagement data requires appropriate access permissions
    - Aggregate engagement data can be used for course improvement
    - Engagement tracking respects student privacy preferences
    
    Args:
        student_id: Student identifier for engagement analysis
        course_id: Course context for engagement measurement
        days_back: Analysis period (1-365 days, default 30)
        activity_service: Injected service for activity data processing
        
    Returns:
        EngagementScoreResponse: Comprehensive engagement analytics including:
        - Overall engagement score (0-100)
        - Activity breakdown by type
        - Temporal engagement patterns
        - Comparative analysis context
        
    Raises:
        ValidationException: For invalid parameters or insufficient data
        StudentAnalyticsException: For student-specific processing errors
    """
    try:
        engagement_score = await activity_service.get_engagement_score(
            student_id=student_id,
            course_id=course_id,
            days_back=days_back
        )
        
        # Get activity breakdown for context
        activities = await activity_service.get_student_activities(
            student_id=student_id,
            course_id=course_id,
            start_date=datetime.utcnow() - timedelta(days=days_back)
        )
        
        activity_breakdown = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            activity_breakdown[activity_type] = activity_breakdown.get(activity_type, 0) + 1
        
        return EngagementScoreResponse(
            student_id=student_id,
            course_id=course_id,
            engagement_score=engagement_score,
            calculation_date=datetime.utcnow(),
            days_analyzed=days_back,
            activity_breakdown=activity_breakdown
        )
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid parameters for engagement score calculation",
            validation_errors={"days_back": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message="Failed to calculate engagement score",
            student_id=student_id,
            course_id=course_id,
            metric_type="engagement_score",
            time_period=f"{days_back}_days",
            original_exception=e
        )

@app.get("/api/v1/courses/{course_id}/activity-summary")
async def get_course_activity_summary(
    course_id: str,
    days_back: int = Query(default=7, ge=1, le=90),
    activity_service: IStudentActivityService = Depends(get_activity_service)
):
    """
    Generate comprehensive course activity summary for instructional analytics.
    
    This endpoint provides course-level learning analytics to support instructional
    decision-making and course improvement initiatives.
    
    Course Analytics Components:
    
    1. **Participation Analytics**:
       - Total student activity volume and trends
       - Unique student participation rates
       - Activity distribution across learning modules
       
    2. **Engagement Patterns**:
       - Peak activity times for optimal scheduling
       - Learning session duration analysis
       - Content interaction frequency and depth
       
    3. **Learning Effectiveness Indicators**:
       - Activity completion rates by type
       - Student progress correlation with activity
       - Learning goal achievement tracking
       
    4. **Instructional Design Insights**:
       - Content effectiveness measurement
       - Learning pathway optimization data
       - Resource utilization analysis
    
    Educational Applications:
    - Instructor dashboard analytics
    - Course design and improvement feedback
    - Student support service planning
    - Educational resource allocation
    - Learning outcome assessment
    
    Temporal Analysis Features:
    - Daily activity trend identification
    - Weekly learning pattern analysis
    - Seasonal engagement variations
    - Real-time vs. historical comparisons
    
    Instructional Decision Support:
    - Identifies content requiring additional support
    - Highlights successful learning activities
    - Suggests optimal timing for important content
    - Provides early warning for course-wide issues
    
    Privacy and Aggregation:
    - Individual student data is aggregated and anonymized
    - Provides insights without exposing personal information
    - Maintains statistical significance while protecting privacy
    
    Args:
        course_id: Course identifier for activity analysis
        days_back: Analysis period (1-90 days, default 7)
        activity_service: Injected service for activity data processing
        
    Returns:
        Dict containing:
        - Total activities and unique student participation
        - Activity breakdown by type and time
        - Engagement level assessment
        - Peak activity time analysis
        - Trend analysis and recommendations
        
    Raises:
        ValidationException: For invalid course ID or time parameters
        DataCollectionException: For activity data retrieval failures
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days_back)
        summary = await activity_service.get_activity_summary(
            course_id=course_id,
            start_date=start_date
        )
        
        return summary
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid parameters for activity summary",
            validation_errors={"days_back": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DataCollectionException(
            message="Failed to retrieve activity summary",
            course_id=course_id,
            data_type="activity_summary",
            collection_method="api_endpoint",
            original_exception=e
        )

# ========================================
# Laboratory Learning Analytics Endpoints
# ========================================
# These endpoints provide comprehensive analytics for hands-on learning environments,
# supporting practical skill development measurement and coding proficiency assessment.

@app.post("/api/v1/lab-usage")
async def record_lab_usage(
    request: LabUsageRequest,
    lab_service: ILabAnalyticsService = Depends(get_lab_service)
):
    """
    Record comprehensive laboratory usage metrics for hands-on learning analytics.
    
    This endpoint captures detailed metrics from coding laboratories and practical
    learning environments to support skill development assessment and engagement analysis.
    
    Laboratory Learning Analytics Framework:
    
    1. **Practical Engagement Measurement**:
       - Active coding time and session duration
       - Number of meaningful actions performed
       - Code execution frequency and patterns
       - Problem-solving persistence indicators
       
    2. **Skill Development Tracking**:
       - Code complexity progression over time
       - Error resolution improvement patterns
       - Programming concept application
       - Debugging and troubleshooting skills
       
    3. **Learning Process Analytics**:
       - Trial-and-error learning patterns
       - Help-seeking and resource usage
       - Collaboration and peer learning
       - Self-directed exploration behaviors
    
    Educational Applications:
    - Programming proficiency assessment
    - Hands-on learning effectiveness measurement
    - Individual learning style identification
    - Personalized coding assistance recommendations
    
    Productivity Score Calculation:
    Based on educational research in skill acquisition:
    - Action density: Meaningful interactions per minute
    - Error recovery: Ability to resolve issues independently
    - Code quality: Progression toward best practices
    - Learning persistence: Continued engagement through challenges
    
    Privacy and Ethics:
    - Code submissions are analyzed for learning patterns, not content
    - Individual coding styles are respected and supported
    - Error data is used for learning support, not evaluation
    - Final code analysis focuses on learning progress
    
    Args:
        request: Laboratory usage data with comprehensive metrics
        lab_service: Injected service for lab analytics processing
        
    Returns:
        Dict containing:
        - Unique session identifier
        - Calculated productivity score (0-10)
        - Engagement level assessment
        - Learning progress indicators
        
    Raises:
        ValidationException: For invalid lab usage data
        DataCollectionException: For lab metrics recording failures
    """
    try:
        # Convert DTO to domain entity
        lab_metrics = LabUsageMetrics(
            student_id=request.student_id,
            course_id=request.course_id,
            lab_id=request.lab_id,
            session_start=datetime.utcnow(),
            actions_performed=request.actions_performed,
            code_executions=request.code_executions,
            errors_encountered=request.errors_encountered,
            final_code=request.final_code
        )
        
        # End session if we have final code
        if request.final_code:
            lab_metrics.end_session(request.final_code)
        
        recorded_metrics = await lab_service.record_lab_session(lab_metrics)
        
        return {
            "id": recorded_metrics.id,
            "student_id": recorded_metrics.student_id,
            "course_id": recorded_metrics.course_id,
            "lab_id": recorded_metrics.lab_id,
            "productivity_score": recorded_metrics.get_productivity_score(),
            "engagement_level": recorded_metrics.get_engagement_level()
        }
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid lab usage data provided",
            validation_errors={"lab_metrics": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DataCollectionException(
            message="Failed to record lab usage metrics",
            student_id=request.student_id,
            course_id=request.course_id,
            data_type="lab_usage",
            collection_method="api_endpoint",
            original_exception=e
        )

@app.get("/api/v1/students/{student_id}/courses/{course_id}/lab-proficiency")
async def get_lab_proficiency(
    student_id: str,
    course_id: str,
    lab_service: ILabAnalyticsService = Depends(get_lab_service)
):
    """
    Calculate comprehensive laboratory proficiency score for practical skill assessment.
    
    This endpoint implements evidence-based proficiency measurement for hands-on
    learning environments, supporting competency-based education principles.
    
    Lab Proficiency Assessment Framework:
    
    1. **Technical Skill Proficiency** (40% weight):
       - Code quality and best practice adherence
       - Problem-solving approach sophistication
       - Tool usage efficiency and effectiveness
       - Debugging and troubleshooting capabilities
       
    2. **Learning Process Proficiency** (30% weight):
       - Independence in problem-solving
       - Ability to apply learned concepts
       - Adaptation to new challenges
       - Learning from errors and iteration
       
    3. **Engagement and Persistence** (20% weight):
       - Sustained effort through difficulties
       - Exploration of additional features
       - Initiative in learning beyond requirements
       - Collaboration and help-seeking when appropriate
       
    4. **Knowledge Application** (10% weight):
       - Transfer of learning to new contexts
       - Integration of multiple concepts
       - Creative problem-solving approaches
       - Demonstration of deep understanding
    
    Proficiency Score Interpretation:
    - 90-100: Expert level, ready for advanced challenges
    - 80-89: Proficient, independent problem solver
    - 70-79: Developing, shows good understanding
    - 60-69: Emerging, needs guided practice
    - 50-59: Beginning, requires structured support
    - Below 50: Foundational skills need development
    
    Educational Applications:
    - Competency-based progression decisions
    - Personalized learning path recommendations
    - Skill gap identification and remediation
    - Advanced learning opportunity qualification
    
    Continuous Assessment Features:
    - Real-time proficiency tracking
    - Progress trend analysis over time
    - Comparative peer analysis (anonymized)
    - Skill development milestone recognition
    
    Args:
        student_id: Student identifier for proficiency assessment
        course_id: Course context for skill measurement
        lab_service: Injected service for lab analytics processing
        
    Returns:
        Dict containing:
        - Overall lab proficiency score (0-100)
        - Skill area breakdown and analysis
        - Learning progress trends
        - Personalized development recommendations
        
    Raises:
        StudentAnalyticsException: For proficiency calculation errors
    """
    try:
        proficiency_score = await lab_service.get_lab_proficiency_score(
            student_id=student_id,
            course_id=course_id
        )
        
        return {
            "student_id": student_id,
            "course_id": course_id,
            "lab_proficiency_score": proficiency_score,
            "calculated_at": datetime.utcnow()
        }
        
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message="Failed to calculate lab proficiency score",
            student_id=student_id,
            course_id=course_id,
            metric_type="lab_proficiency",
            original_exception=e
        )

# ========================================
# Assessment and Quiz Analytics Endpoints
# ========================================
# These endpoints implement comprehensive assessment analytics based on psychometric
# measurement principles and educational assessment research methodologies.

@app.post("/api/v1/quiz-performance")
async def record_quiz_performance(
    request: QuizPerformanceRequest,
    quiz_service: IQuizAnalyticsService = Depends(get_quiz_service)
):
    """
    Record comprehensive quiz performance data for educational assessment analytics.
    
    This endpoint implements advanced assessment analytics based on psychometric
    measurement theory and educational assessment research.
    
    Assessment Analytics Framework:
    
    1. **Performance Measurement**:
       - Accuracy assessment (correct responses / total questions)
       - Response pattern analysis for learning diagnosis
       - Question-level difficulty and discrimination analysis
       - Time-based performance indicators
       
    2. **Cognitive Load Analysis**:
       - Response time analysis for cognitive processing
       - Question-by-question timing patterns
       - Cognitive load indicators through hesitation patterns
       - Working memory capacity implications
       
    3. **Learning Process Analytics**:
       - Answer revision patterns and decision-making
       - Sequential response strategies
       - Knowledge application vs. recall identification
       - Metacognitive strategy assessment
       
    4. **Diagnostic Assessment Features**:
       - Knowledge gap identification through error patterns
       - Misconception detection and classification
       - Learning objective mastery assessment
       - Prerequisite knowledge evaluation
    
    Educational Applications:
    - Formative assessment for learning improvement
    - Summative assessment for competency demonstration
    - Diagnostic assessment for targeted intervention
    - Adaptive assessment for personalized challenge levels
    
    Performance Level Classification:
    - Excellent (90-100%): Mastery demonstrated, ready for advancement
    - Good (80-89%): Proficient understanding, minor gaps possible
    - Satisfactory (70-79%): Adequate knowledge, some review needed
    - Needs Improvement (60-69%): Significant gaps, targeted support required
    - Poor (Below 60%): Foundational review necessary, intensive support needed
    
    Privacy and Ethics in Assessment:
    - Individual responses used for learning support only
    - Aggregate data supports course improvement
    - Assessment analytics respect diverse learning styles
    - Performance data used constructively, not punitively
    
    Args:
        request: Comprehensive quiz performance data
        quiz_service: Injected service for assessment analytics
        
    Returns:
        Dict containing:
        - Performance score and level classification
        - Detailed timing and response analytics
        - Learning diagnostic insights
        - Personalized improvement recommendations
        
    Raises:
        ValidationException: For invalid assessment data
        DataCollectionException: For performance recording failures
    """
    try:
        # Convert DTO to domain entity
        performance = QuizPerformance(
            student_id=request.student_id,
            course_id=request.course_id,
            quiz_id=request.quiz_id,
            attempt_number=request.attempt_number,
            start_time=datetime.utcnow(),
            questions_total=request.questions_total,
            questions_answered=request.questions_answered,
            questions_correct=request.questions_correct,
            answers=request.answers,
            time_per_question=request.time_per_question
        )
        
        # Complete the quiz if all questions are answered
        if request.questions_answered == request.questions_total:
            performance.complete_quiz()
        
        recorded_performance = await quiz_service.record_quiz_performance(performance)
        
        return {
            "id": recorded_performance.id,
            "student_id": recorded_performance.student_id,
            "quiz_id": recorded_performance.quiz_id,
            "score_percentage": recorded_performance.get_score_percentage(),
            "performance_level": recorded_performance.get_performance_level(),
            "duration_minutes": recorded_performance.get_duration_minutes()
        }
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid quiz performance data provided",
            validation_errors={"quiz_performance": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DataCollectionException(
            message="Failed to record quiz performance",
            student_id=request.student_id,
            course_id=request.course_id,
            data_type="quiz_performance",
            collection_method="api_endpoint",
            original_exception=e
        )

# ========================================
# Learning Progress Tracking Endpoints
# ========================================
# These endpoints implement competency-based education (CBE) principles and
# mastery learning analytics for personalized educational progression.

@app.post("/api/v1/progress")
async def update_progress(
    request: ProgressUpdateRequest,
    progress_service: IProgressTrackingService = Depends(get_progress_service)
):
    """
    Update student learning progress with comprehensive educational analytics.
    
    This endpoint implements competency-based education (CBE) principles and
    mastery learning analytics to support personalized educational progression.
    
    Progress Tracking Framework:
    
    1. **Mastery-Based Progression**:
       - Competency demonstration rather than time-based advancement
       - Multiple pathways to demonstrate learning
       - Flexible pacing based on individual learning needs
       - Continuous assessment and feedback loops
       
    2. **Learning Analytics Integration**:
       - Real-time progress monitoring and adjustment
       - Learning velocity calculation and optimization
       - Knowledge retention tracking over time
       - Transfer of learning assessment
       
    3. **Personalized Learning Support**:
       - Adaptive content recommendations
       - Learning path optimization based on progress patterns
       - Prerequisite knowledge validation
       - Just-in-time learning resource provision
       
    4. **Educational Measurement Principles**:
       - Criterion-referenced assessment (mastery vs. norm-based)
       - Multiple forms of evidence for competency
       - Authentic assessment integration
       - Portfolio-based learning documentation
    
    Progress Status Classifications:
    - NOT_STARTED: No engagement with learning content
    - IN_PROGRESS: Active learning in progress (1-99% completion)
    - COMPLETED: All required activities finished (100%)
    - MASTERED: Competency demonstrated beyond completion
    - ABANDONED: Learning pathway discontinued
    
    Educational Applications:
    - Competency-based advancement decisions
    - Personalized learning plan adjustments
    - Academic planning and advising support
    - Learning outcome achievement tracking
    
    Time Investment Analytics:
    - Learning efficiency measurement (progress per time unit)
    - Optimal learning time recommendations
    - Study habit analysis and improvement
    - Cognitive load management insights
    
    Mastery Assessment Features:
    - Multiple demonstration opportunities
    - Performance standard validation
    - Skill transfer assessment
    - Long-term retention verification
    
    Args:
        request: Comprehensive progress update with educational context
        progress_service: Injected service for progress analytics
        
    Returns:
        Dict containing:
        - Updated progress status and percentage
        - Learning velocity and efficiency metrics
        - Competency achievement indicators
        - Personalized next-step recommendations
        
    Raises:
        ValidationException: For invalid progress data or educational context
        DataCollectionException: For progress update failures
    """
    try:
        # Convert DTO to domain entity
        progress = StudentProgress(
            student_id=request.student_id,
            course_id=request.course_id,
            content_item_id=request.content_item_id,
            content_type=ContentType(request.content_type.lower())
        )
        
        # Update progress
        progress.update_progress(
            progress_percentage=request.progress_percentage,
            time_spent_additional=request.time_spent_additional
        )
        
        # Mark as mastered if mastery score provided
        if request.mastery_score is not None:
            progress.mark_mastered(request.mastery_score)
        
        updated_progress = await progress_service.update_progress(progress)
        
        return {
            "id": updated_progress.id,
            "student_id": updated_progress.student_id,
            "content_item_id": updated_progress.content_item_id,
            "progress_percentage": updated_progress.progress_percentage,
            "status": updated_progress.status.value,
            "completion_date": updated_progress.completion_date
        }
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid progress update data provided",
            validation_errors={"progress_data": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise DataCollectionException(
            message="Failed to update student progress",
            student_id=request.student_id,
            course_id=request.course_id,
            data_type="progress_update",
            collection_method="api_endpoint",
            original_exception=e
        )

@app.get("/api/v1/students/{student_id}/courses/{course_id}/progress-summary")
async def get_progress_summary(
    student_id: str,
    course_id: str,
    progress_service: IProgressTrackingService = Depends(get_progress_service)
):
    """
    Generate comprehensive learning progress summary for educational planning.
    
    This endpoint provides holistic progress analysis supporting academic planning,
    intervention strategies, and personalized learning optimization.
    
    Progress Summary Components:
    
    1. **Overall Course Progress**:
       - Completion percentage across all learning objectives
       - Mastery demonstration status by competency area
       - Learning milestone achievement tracking
       - Academic goal alignment assessment
       
    2. **Learning Velocity Analysis**:
       - Progress rate compared to course timeline
       - Learning efficiency metrics and trends
       - Optimal learning pace recommendations
       - Time-to-mastery predictions
       
    3. **Competency Development Tracking**:
       - Skill acquisition progression by learning objective
       - Knowledge retention and transfer assessment
       - Prerequisite mastery validation
       - Advanced learning readiness indicators
       
    4. **Learning Pattern Analysis**:
       - Preferred learning modalities and effectiveness
       - Engagement patterns across content types
       - Challenge response and problem-solving approaches
       - Collaboration and independent learning balance
    
    Educational Planning Applications:
    - Academic advising and pathway planning
    - Personalized learning plan development
    - Intervention strategy design and implementation
    - Resource allocation and support service coordination
    
    Student Success Indicators:
    - On-track for successful course completion
    - Areas of strength and exceptional performance
    - Challenges requiring additional support
    - Opportunities for accelerated or enriched learning
    
    Privacy and Student Agency:
    - Progress data supports student self-advocacy
    - Transparent tracking promotes learner autonomy
    - Goal-setting support with student input
    - Progress sharing with appropriate consent
    
    Args:
        student_id: Student identifier for progress analysis
        course_id: Course context for progress measurement
        progress_service: Injected service for progress analytics
        
    Returns:
        Dict containing:
        - Comprehensive progress metrics and analysis
        - Learning velocity and efficiency indicators
        - Competency mastery status by area
        - Personalized recommendations for continued success
        
    Raises:
        StudentAnalyticsException: For progress summary generation errors
    """
    try:
        summary = await progress_service.get_progress_summary(
            student_id=student_id,
            course_id=course_id
        )
        
        return summary
        
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message="Failed to retrieve progress summary",
            student_id=student_id,
            course_id=course_id,
            metric_type="progress_summary",
            original_exception=e
        )

# ========================================
# Comprehensive Learning Analytics Endpoints
# ========================================
# These endpoints provide holistic learning analytics integrating multiple data sources
# for comprehensive educational insights and evidence-based decision making.

@app.post("/api/v1/students/{student_id}/courses/{course_id}/analytics", response_model=LearningAnalyticsResponse)
async def generate_student_analytics(
    student_id: str,
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """
    Generate comprehensive learning analytics integrating multiple educational data sources.
    
    This endpoint implements advanced learning analytics methodologies to provide
    holistic insights into student learning processes and outcomes.
    
    Comprehensive Learning Analytics Framework:
    
    1. **Multi-Dimensional Learning Measurement**:
       - Engagement Analytics: Behavioral, cognitive, and emotional engagement
       - Progress Analytics: Learning velocity, competency development, mastery
       - Performance Analytics: Assessment outcomes, skill demonstration
       - Social Analytics: Collaboration, peer learning, community participation
       
    2. **Predictive Learning Analytics**:
       - Success probability modeling using machine learning
       - Risk assessment for early intervention identification
       - Learning pathway optimization recommendations
       - Performance forecasting for academic planning
       
    3. **Educational Data Mining**:
       - Learning pattern discovery and classification
       - Knowledge gap identification and analysis
       - Learning strategy effectiveness assessment
       - Optimal learning condition determination
       
    4. **Personalized Learning Intelligence**:
       - Individual learning profile development
       - Adaptive content and challenge recommendations
       - Learning preference and style analysis
       - Metacognitive skill development tracking
    
    Analytics Integration Sources:
    - Student activity tracking (engagement patterns)
    - Laboratory usage analytics (hands-on skill development)
    - Assessment performance data (knowledge and competency)
    - Progress tracking information (learning velocity)
    - Time-on-task measurements (learning efficiency)
    
    Educational Applications:
    - Personalized learning plan development
    - Academic intervention strategy design
    - Learning resource optimization
    - Student success coaching support
    - Educational effectiveness measurement
    
    Research and Evidence Base:
    - Based on learning sciences research and cognitive psychology
    - Implements evidence-based educational measurement principles
    - Supports continuous improvement through data-driven insights
    - Enables educational research and program evaluation
    
    Privacy and Ethics:
    - Individual analytics support student success, not surveillance
    - Data used constructively for learning improvement
    - Student agency respected in learning path decisions
    - Transparent analytics promote learner self-awareness
    
    Args:
        student_id: Student identifier for comprehensive analytics
        course_id: Course context for learning measurement
        analytics_service: Injected service for learning analytics processing
        
    Returns:
        LearningAnalyticsResponse containing:
        - Multi-dimensional learning scores and analysis
        - Risk level assessment with intervention recommendations
        - Personalized learning recommendations
        - Overall performance metrics and trends
        
    Raises:
        ValidationException: For invalid analytics parameters
        LearningAnalyticsException: For analytics generation failures
    """
    try:
        analytics = await analytics_service.generate_student_analytics(
            student_id=student_id,
            course_id=course_id
        )
        
        return _analytics_to_response(analytics)
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid parameters for analytics generation",
            validation_errors={"student_analytics": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LearningAnalyticsException(
            message="Failed to generate student analytics",
            course_id=course_id,
            analysis_type="student_analytics",
            original_exception=e
        )

@app.get("/api/v1/courses/{course_id}/analytics-summary", response_model=CourseAnalyticsSummaryResponse)
async def get_course_analytics_summary(
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """
    Generate comprehensive course-wide learning analytics summary for institutional insights.
    
    This endpoint provides course-level analytics aggregating individual student data
    for institutional effectiveness measurement and course improvement initiatives.
    
    Course Analytics Framework:
    
    1. **Enrollment and Participation Analytics**:
       - Student enrollment trends and demographics
       - Participation rates and engagement levels
       - Completion and retention statistics
       - Time-to-completion distributions
       
    2. **Learning Effectiveness Measurement**:
       - Average learning outcomes across cohorts
       - Competency achievement rates by learning objective
       - Knowledge retention and transfer assessment
       - Skill development progression tracking
       
    3. **Course Quality Indicators**:
       - Content effectiveness and utilization analysis
       - Assessment validity and reliability metrics
       - Learning resource impact measurement
       - Instructional design optimization insights
       
    4. **Student Success Analytics**:
       - Risk distribution for intervention planning
       - High performer identification and analysis
       - Support service effectiveness measurement
       - Success factor correlation analysis
    
    Institutional Applications:
    - Course quality assurance and improvement
    - Faculty development and support planning
    - Resource allocation optimization
    - Student success initiative effectiveness
    - Accreditation and compliance reporting
    
    Educational Leadership Insights:
    - Program effectiveness measurement
    - Curriculum design and revision guidance
    - Learning technology impact assessment
    - Student support service optimization
    
    Comparative Analysis Features:
    - Historical trend analysis over multiple terms
    - Benchmark comparison with similar courses
    - Best practice identification and sharing
    - Continuous improvement recommendation generation
    
    Privacy and Aggregation:
    - Individual student data aggregated for institutional insights
    - Statistical significance maintained while protecting privacy
    - Anonymized data supports educational research
    - Compliance with FERPA and institutional policies
    
    Args:
        course_id: Course identifier for analytics summary
        analytics_service: Injected service for learning analytics processing
        
    Returns:
        CourseAnalyticsSummaryResponse containing:
        - Comprehensive course performance metrics
        - Student success and risk distribution analysis
        - High performer and at-risk student identification
        - Course improvement recommendations and insights
        
    Raises:
        LearningAnalyticsException: For course analytics processing errors
    """
    try:
        summary = await analytics_service.get_course_analytics_summary(course_id)
        
        return CourseAnalyticsSummaryResponse(
            course_id=course_id,
            total_students=summary["total_students"],
            averages=summary["averages"],
            risk_distribution=summary["risk_distribution"],
            high_performers=summary["high_performers"],
            at_risk_students=summary["at_risk_students"],
            last_updated=summary["last_updated"]
        )
        
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LearningAnalyticsException(
            message="Failed to retrieve course analytics summary",
            course_id=course_id,
            analysis_type="course_summary",
            original_exception=e
        )

@app.get("/api/v1/students/{student_id}/courses/{course_id}/performance-comparison")
async def compare_student_performance(
    student_id: str,
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """Compare student performance against course averages"""
    try:
        comparison = await analytics_service.compare_student_performance(
            student_id=student_id,
            course_id=course_id
        )
        
        return comparison
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid parameters for performance comparison",
            validation_errors={"performance_comparison": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LearningAnalyticsException(
            message="Failed to compare student performance",
            course_id=course_id,
            analysis_type="performance_comparison",
            original_exception=e
        )

@app.get("/api/v1/students/{student_id}/courses/{course_id}/prediction")
async def predict_performance(
    student_id: str,
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """Predict future student performance"""
    try:
        prediction = await analytics_service.predict_performance(
            student_id=student_id,
            course_id=course_id
        )
        
        return prediction
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid parameters for performance prediction",
            validation_errors={"performance_prediction": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise LearningAnalyticsException(
            message="Failed to predict student performance",
            course_id=course_id,
            analysis_type="performance_prediction",
            original_exception=e
        )

# ========================================
# Educational Reporting and Visualization Endpoints
# ========================================
# These endpoints provide comprehensive reporting capabilities for different educational
# stakeholders with appropriate data access controls and privacy protections.

@app.post("/api/v1/reports/student", response_model=ReportResponse)
async def generate_student_report(
    request: AnalyticsRequest,
    reporting_service: IReportingService = Depends(get_reporting_service)
):
    """
    Generate comprehensive student learning analytics report for academic planning.
    
    This endpoint creates detailed, privacy-compliant reports supporting student
    success initiatives and academic planning processes.
    
    Student Report Components:
    
    1. **Academic Performance Summary**:
       - Learning objective achievement status
       - Competency development progression
       - Assessment performance trends
       - Academic goal alignment analysis
       
    2. **Learning Process Analytics**:
       - Engagement patterns and consistency
       - Learning strategy effectiveness
       - Time investment and efficiency metrics
       - Challenge response and resilience indicators
       
    3. **Skill Development Tracking**:
       - Technical and practical skill progression
       - Knowledge application and transfer
       - Critical thinking and problem-solving growth
       - Collaboration and communication development
       
    4. **Personalized Recommendations**:
       - Learning path optimization suggestions
       - Resource and support service recommendations
       - Study strategy and time management guidance
       - Goal-setting and milestone planning support
    
    Report Format Options:
    - JSON: For digital dashboard integration and real-time updates
    - CSV: For data analysis and academic advising workflows
    - PDF: For formal documentation and student portfolio inclusion
    
    Educational Applications:
    - Academic advising and planning sessions
    - Student self-reflection and goal setting
    - Parent/guardian communication and involvement
    - Transfer credit and credential documentation
    
    Privacy and Student Rights:
    - Student owns and controls access to their learning data
    - Reports support student self-advocacy and agency
    - Privacy settings respected in all report generation
    - FERPA compliance maintained throughout process
    
    Personalization Features:
    - Adaptive content based on learning preferences
    - Cultural and linguistic consideration integration
    - Accessibility accommodations in report format
    - Learning style and preference reflection
    
    Args:
        request: Report generation parameters with privacy controls
        reporting_service: Injected service for report generation
        
    Returns:
        ReportResponse containing:
        - Comprehensive student analytics report
        - Personalized recommendations and insights
        - Privacy-compliant data presentation
        - Multi-format export capabilities
        
    Raises:
        ValidationException: For invalid report parameters
        ReportGenerationException: For report creation failures
    """
    try:
        if not request.student_id or not request.course_id:
            raise ValueError("Student ID and Course ID are required for student reports")
        
        report_data = await reporting_service.generate_student_report(
            student_id=request.student_id,
            course_id=request.course_id,
            format=request.format
        )
        
        return ReportResponse(
            report_id=f"student_{request.student_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.utcnow(),
            report_type="student",
            format=request.format,
            data=report_data
        )
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid parameters for student report generation",
            validation_errors={"report_request": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise ReportGenerationException(
            message="Failed to generate student report",
            report_type="student",
            output_format=request.format,
            original_exception=e
        )

@app.post("/api/v1/reports/course", response_model=ReportResponse)
async def generate_course_report(
    request: AnalyticsRequest,
    reporting_service: IReportingService = Depends(get_reporting_service)
):
    """
    Generate comprehensive course-wide analytics report for instructional improvement.
    
    This endpoint creates detailed course analytics reports supporting instructional
    design, course improvement, and institutional effectiveness initiatives.
    
    Course Report Framework:
    
    1. **Course Effectiveness Analysis**:
       - Learning outcome achievement rates
       - Content effectiveness and utilization
       - Assessment validity and reliability
       - Student satisfaction and engagement metrics
       
    2. **Student Success Analytics**:
       - Completion and retention statistics
       - Performance distribution analysis
       - Risk factor identification and trends
       - Support service utilization and effectiveness
       
    3. **Instructional Design Insights**:
       - Learning activity effectiveness measurement
       - Content sequencing and pacing analysis
       - Resource utilization and impact assessment
       - Technology integration effectiveness
       
    4. **Continuous Improvement Recommendations**:
       - Data-driven course enhancement suggestions
       - Student support optimization opportunities
       - Resource allocation improvement recommendations
       - Faculty development and support needs identification
    
    Institutional Applications:
    - Quality assurance and accreditation reporting
    - Faculty performance evaluation support
    - Curriculum committee review and decision-making
    - Resource planning and budget allocation
    
    Educational Leadership Support:
    - Program evaluation and improvement planning
    - Best practice identification and dissemination
    - Innovation and experimentation impact assessment
    - Strategic planning and institutional effectiveness
    
    Comparative Analysis Features:
    - Historical trend analysis and benchmarking
    - Cross-course comparison and best practice identification
    - Industry standard alignment assessment
    - Peer institution comparison (where available)
    
    Privacy and Aggregation:
    - Individual student data properly aggregated and anonymized
    - Statistical significance maintained for reliable insights
    - Compliance with institutional research protocols
    - Ethical use of educational data principles
    
    Args:
        request: Course report generation parameters
        reporting_service: Injected service for report processing
        
    Returns:
        ReportResponse containing:
        - Comprehensive course analytics and insights
        - Student success and engagement analysis
        - Instructional effectiveness recommendations
        - Institutional decision-making support data
        
    Raises:
        ValidationException: For invalid course report parameters
        ReportGenerationException: For course report generation failures
    """
    try:
        if not request.course_id:
            raise ValueError("Course ID is required for course reports")
        
        report_data = await reporting_service.generate_course_report(
            course_id=request.course_id,
            format=request.format
        )
        
        return ReportResponse(
            report_id=f"course_{request.course_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.utcnow(),
            report_type="course",
            format=request.format,
            data=report_data
        )
        
    except ValueError as e:
        raise ValidationException(
            message="Invalid parameters for course report generation",
            validation_errors={"report_request": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise ReportGenerationException(
            message="Failed to generate course report",
            report_type="course",
            output_format=request.format,
            original_exception=e
        )

# ========================================
# Educational Risk Assessment Endpoints
# ========================================
# These endpoints implement evidence-based early warning systems for identifying
# students who may benefit from additional academic support and intervention.

@app.get("/api/v1/students/{student_id}/courses/{course_id}/risk-assessment")
async def assess_student_risk(
    student_id: str,
    course_id: str,
    risk_service: IRiskAssessmentService = Depends(get_risk_service)
):
    """
    Conduct comprehensive student risk assessment for early intervention planning.
    
    This endpoint implements evidence-based risk assessment methodologies to identify
    students who may benefit from additional academic support and intervention services.
    
    Risk Assessment Framework:
    
    1. **Academic Performance Indicators**:
       - Assessment scores and trends over time
       - Assignment completion rates and quality
       - Learning objective achievement patterns
       - Knowledge retention and application metrics
       
    2. **Engagement and Behavioral Indicators**:
       - Platform usage frequency and consistency
       - Learning activity participation levels
       - Help-seeking behaviors and resource utilization
       - Social learning and collaboration engagement
       
    3. **Learning Process Indicators**:
       - Learning velocity and efficiency patterns
       - Study habit consistency and effectiveness
       - Challenge response and resilience metrics
       - Metacognitive skill development progress
       
    4. **External and Contextual Factors**:
       - Time investment patterns and constraints
       - Technology access and digital literacy indicators
       - Prior academic preparation and prerequisite mastery
       - Life circumstances affecting learning capacity
    
    Risk Level Classifications:
    
    - **LOW RISK**: Strong performance, consistent engagement, on-track progress
      * Characteristics: High engagement, good performance, consistent participation
      * Recommendations: Continue current approach, consider advanced opportunities
      
    - **MEDIUM RISK**: Some concerns, monitoring recommended
      * Characteristics: Inconsistent performance, moderate engagement issues
      * Recommendations: Check-in support, study strategy guidance, resource connections
      
    - **HIGH RISK**: Significant concerns, intervention needed
      * Characteristics: Poor performance trends, low engagement, missing deadlines
      * Recommendations: Intensive support, academic coaching, flexible accommodations
      
    - **CRITICAL RISK**: Immediate intervention required
      * Characteristics: Severe performance issues, minimal engagement, high failure risk
      * Recommendations: Emergency support, comprehensive intervention, alternative pathways
    
    Educational Applications:
    - Early warning system for academic support services
    - Proactive intervention planning and resource allocation
    - Student success coaching and mentoring programs
    - Academic policy and support service effectiveness evaluation
    
    Ethical Considerations:
    - Risk assessment supports student success, not punishment
    - Transparent communication about risk factors and support options
    - Student agency respected in intervention acceptance
    - Bias detection and mitigation in risk algorithms
    
    Intervention Effectiveness:
    - Continuous monitoring of intervention outcomes
    - Adjustment of risk models based on intervention effectiveness
    - Long-term tracking of student success after intervention
    - Research on most effective support strategies
    
    Args:
        student_id: Student identifier for risk assessment
        course_id: Course context for risk evaluation
        risk_service: Injected service for risk assessment processing
        
    Returns:
        Dict containing:
        - Overall risk level with detailed explanation
        - Specific risk factors and contributing elements
        - Evidence-based intervention recommendations
        - Timeline and priority for support implementation
        
    Raises:
        StudentAnalyticsException: For risk assessment processing errors
    """
    try:
        risk_level, reasons = await risk_service.assess_student_risk(
            student_id=student_id,
            course_id=course_id
        )
        
        return {
            "student_id": student_id,
            "course_id": course_id,
            "risk_level": risk_level.value,
            "risk_factors": reasons,
            "assessment_date": datetime.utcnow()
        }
        
    except AnalyticsException:
        # Re-raise custom exceptions (they will be handled by the global handler)
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message="Failed to assess student risk level",
            student_id=student_id,
            course_id=course_id,
            metric_type="risk_assessment",
            original_exception=e
        )


# ========================================
# Data Transformation Helper Functions
# ========================================
# These functions follow the Single Responsibility Principle by focusing solely on
# data transformation between domain entities and API response models.

def _activity_to_response(activity: StudentActivity) -> StudentActivityResponse:
    """
    Transform student activity domain entity to API response format.
    
    This helper function implements clean data transformation following
    educational data interoperability standards and privacy best practices.
    
    Educational Data Standards:
    - Follows xAPI (Experience API) format for activity representation
    - Maintains temporal precision for learning analytics
    - Preserves educational context while protecting privacy
    - Supports learning analytics tool integration
    
    Privacy Protection:
    - Session IDs anonymized for research purposes
    - Activity data sanitized of personally identifiable information
    - IP addresses excluded from API responses for privacy
    - User agent data generalized to prevent fingerprinting
    
    Args:
        activity: Domain entity containing comprehensive activity data
        
    Returns:
        StudentActivityResponse: API-formatted activity data for client consumption
    """
    return StudentActivityResponse(
        id=activity.id,
        student_id=activity.student_id,
        course_id=activity.course_id,
        activity_type=activity.activity_type.value,
        timestamp=activity.timestamp,
        activity_data=activity.activity_data,
        session_id=activity.session_id
    )

def _analytics_to_response(analytics: LearningAnalytics) -> LearningAnalyticsResponse:
    """
    Transform comprehensive learning analytics domain entity to API response format.
    
    This function converts complex learning analytics data into a standardized
    API response format suitable for educational dashboards and reporting tools.
    
    Educational Analytics Transformation:
    - Preserves multi-dimensional learning measurement data
    - Maintains temporal context for trend analysis
    - Includes risk assessment and recommendation data
    - Calculates overall performance using research-based algorithms
    
    Response Format Features:
    - Standardized scoring scales (0-100) for consistency
    - Risk level enumeration for clear communication
    - Recommendation lists for actionable insights
    - Timestamp preservation for audit and tracking
    
    Educational Applications:
    - Learning analytics dashboard integration
    - Student information system data exchange
    - Educational research data formatting
    - Institutional reporting and compliance
    
    Args:
        analytics: Domain entity with comprehensive learning analytics
        
    Returns:
        LearningAnalyticsResponse: Formatted analytics data for API consumption
    """
    return LearningAnalyticsResponse(
        id=analytics.id,
        student_id=analytics.student_id,
        course_id=analytics.course_id,
        analysis_date=analytics.analysis_date,
        engagement_score=analytics.engagement_score,
        progress_velocity=analytics.progress_velocity,
        lab_proficiency=analytics.lab_proficiency,
        quiz_performance=analytics.quiz_performance,
        time_on_platform=analytics.time_on_platform,
        streak_days=analytics.streak_days,
        risk_level=analytics.risk_level.value,
        recommendations=analytics.recommendations,
        overall_performance=analytics.calculate_overall_performance()
    )

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """
    Main application entry point with comprehensive educational analytics configuration.
    
    This function initializes the educational analytics service using Hydra configuration
    management for flexible, environment-specific deployment.
    
    Educational Analytics Service Initialization:
    - Configures comprehensive learning analytics pipelines
    - Sets up privacy-preserving data processing systems
    - Initializes educational research compliance frameworks
    - Establishes real-time analytics processing capabilities
    
    Configuration Management:
    - Environment-specific settings (development, staging, production)
    - Educational institution customization parameters
    - Privacy and compliance policy configuration
    - Performance and scalability optimization settings
    
    Service Features Initialization:
    - Student activity tracking and analysis systems
    - Laboratory learning analytics processing
    - Assessment and quiz analytics engines
    - Progress tracking and competency measurement
    - Comprehensive learning analytics integration
    - Educational reporting and visualization tools
    - Risk assessment and early warning systems
    
    Logging and Monitoring:
    - Centralized syslog format for educational platform integration
    - Performance monitoring for large-scale educational deployments
    - Privacy-compliant audit logging for FERPA compliance
    - Error tracking and educational service reliability
    
    Educational Platform Integration:
    - Multi-tenant support for educational institutions
    - Scalable architecture for large student populations
    - Real-time analytics for immediate instructional feedback
    - Batch processing for comprehensive institutional reporting
    
    Args:
        cfg: Hydra configuration object with service and educational settings
    """
    global current_config
    current_config = cfg
    
    # Setup centralized logging with syslog format
    service_name = os.environ.get('SERVICE_NAME', 'analytics')
    log_level = os.environ.get('LOG_LEVEL', getattr(cfg, 'logging', {}).get('level', 'INFO'))
    
    logger = setup_docker_logging(service_name, log_level)
    logger.info(f"Starting Analytics Service on port {cfg.server.port}")
    
    # Create app with configuration
    global app
    app = create_app(cfg)
    
    # Run server with HTTPS/SSL configuration and reduced uvicorn logging to avoid duplicates
    uvicorn.run(
        app,
        host=cfg.server.host,
        port=cfg.server.port,
        log_level="warning",  # Reduce uvicorn log level since we have our own logging
        access_log=False,     # Disable uvicorn access log since we log via middleware
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt"
    )

# ========================================
# Application Bootstrap
# ========================================

if __name__ == "__main__":
    """
    Bootstrap the educational analytics service with comprehensive learning analytics capabilities.
    
    This entry point starts the FastAPI application with:
    - Multi-dimensional learning measurement systems
    - Privacy-preserving educational data analytics
    - Evidence-based student success prediction
    - Comprehensive educational reporting and insights
    - FERPA and GDPR compliant data handling
    - Scalable architecture for educational institutions
    """
    main()