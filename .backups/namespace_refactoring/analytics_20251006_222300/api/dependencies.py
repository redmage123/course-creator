"""
Dependency Injection Module for Analytics Service

BUSINESS CONTEXT:
Provides centralized dependency injection for all analytics service components.
Implements Dependency Inversion Principle (SOLID) by depending on interfaces.

TECHNICAL IMPLEMENTATION:
- Factory functions that return service instances
- FastAPI Depends() integration for automatic injection
- Container-based service resolution
- Centralized error handling for missing services

SOLID PRINCIPLES:
- Dependency Inversion: Depends on interfaces (IService*), not concrete implementations
- Single Responsibility: Each function provides one service type
- Interface Segregation: Focused service interfaces
- Open/Closed: New services can be added without modifying existing code

EDUCATIONAL CONTEXT:
Each dependency provides specialized analytics capabilities:
- Activity Service: Learning behavior tracking
- Lab Service: Hands-on skill development analytics
- Quiz Service: Assessment and knowledge measurement
- Progress Service: Mastery and competency tracking
- Analytics Service: Comprehensive learning insights
- Reporting Service: Stakeholder-specific reports
- Risk Service: Early intervention and support
"""

from fastapi import HTTPException
from typing import Optional

# Domain interfaces
from domain.interfaces.analytics_service import (
    IStudentActivityService,
    ILabAnalyticsService,
    IQuizAnalyticsService,
    IProgressTrackingService,
    ILearningAnalyticsService,
    IReportingService,
    IRiskAssessmentService,
)

# Infrastructure
from infrastructure.container import AnalyticsContainer

# Global container instance (initialized in main.py lifespan)
container: Optional[AnalyticsContainer] = None


def set_container(analytics_container: AnalyticsContainer) -> None:
    """
    Set the global analytics container instance.

    Called during application startup to initialize the dependency injection container.

    Args:
        analytics_container: Initialized container with all service instances
    """
    global container
    container = analytics_container


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
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
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

    Raises:
        HTTPException: If analytics container is not properly initialized
    """
    if not container:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
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

    Raises:
        HTTPException: If analytics container is not properly initialized
    """
    if not container:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
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

    Raises:
        HTTPException: If analytics container is not properly initialized
    """
    if not container:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
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

    Raises:
        HTTPException: If analytics container is not properly initialized
    """
    if not container:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
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

    Raises:
        HTTPException: If analytics container is not properly initialized
    """
    if not container:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
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

    Raises:
        HTTPException: If analytics container is not properly initialized
    """
    if not container:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
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

    TODO: Implement JWT validation with proper authentication
    """
    # Mock implementation for development
    # Production: Extract from Authorization header, validate JWT, return user_id
    return "user_123"
