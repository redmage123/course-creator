"""
API Routes for Analytics Service - Consolidated Module

BUSINESS CONTEXT:
This module contains all FastAPI route handlers for the analytics service.
Extracted from main.py (2601 lines) to follow Single Responsibility Principle.

TECHNICAL IMPLEMENTATION:
All route handlers imported from main.py.backup and organized by domain:
- Student Activity: Activity tracking and engagement scoring
- Lab Analytics: Hands-on coding lab proficiency measurement
- Quiz Performance: Assessment and knowledge measurement
- Progress Tracking: Mastery and competency progression
- Learning Analytics: Comprehensive multi-dimensional analytics
- Reporting: Student and course report generation
- Risk Assessment: Early intervention and support identification

SOLID PRINCIPLES:
- Single Responsibility: This file only defines route handlers
- Dependency Inversion: Routes depend on service interfaces
- Open/Closed: New routes can be added without modifying existing

USAGE:
Import this module in main.py and include the router:
    from api.routes import router
    app.include_router(router)

NOTE:
This is a transitional module. For full SOLID compliance, routes should be
further split into domain-specific files (activity_routes.py, lab_routes.py, etc.)
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any

# API models
from api.models import (
    StudentActivityRequest, StudentActivityResponse,
    LabUsageRequest, QuizPerformanceRequest,
    ProgressUpdateRequest, AnalyticsRequest,
    EngagementScoreResponse, LearningAnalyticsResponse,
    CourseAnalyticsSummaryResponse, ReportResponse
)

# Dependencies
from api.dependencies import (
    get_activity_service, get_lab_service, get_quiz_service,
    get_progress_service, get_analytics_service,
    get_reporting_service, get_risk_service,
    get_current_user_id
)

# Domain entities and interfaces
from domain.entities.student_analytics import (
    StudentActivity, LabUsageMetrics, QuizPerformance,
    StudentProgress, LearningAnalytics, ActivityType, ContentType, RiskLevel
)
from domain.interfaces.analytics_service import (
    IStudentActivityService, ILabAnalyticsService, IQuizAnalyticsService,
    IProgressTrackingService, ILearningAnalyticsService, IReportingService,
    IRiskAssessmentService
)

# Custom exceptions
from exceptions import (
    ValidationException, DataCollectionException, AnalyticsException,
    StudentAnalyticsException, LearningAnalyticsException
)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["analytics"])


# ========================================
# Helper Functions
# ========================================

def _activity_to_response(activity: StudentActivity) -> StudentActivityResponse:
    """Convert domain entity to API response model."""
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
    """Convert learning analytics domain entity to API response model."""
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
        overall_performance=analytics.overall_performance
    )


# ========================================
# Student Activity Routes
# ========================================

@router.post("/activities", response_model=StudentActivityResponse)
async def record_activity(
    request: StudentActivityRequest,
    activity_service: IStudentActivityService = Depends(get_activity_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Record student learning activity.

    Implements xAPI standards for activity tracking with comprehensive
    educational analytics capabilities.
    """
    try:
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
            message=f"Invalid activity data: {str(e)}",
            validation_errors={"activity_type": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        raise
    except Exception as e:
        raise DataCollectionException(
            message=f"Failed to record activity: {str(e)}",
            student_id=request.student_id,
            course_id=request.course_id,
            data_type="student_activity",
            collection_method="api_endpoint",
            original_exception=e
        )


@router.get("/students/{student_id}/courses/{course_id}/engagement",
            response_model=EngagementScoreResponse)
async def get_engagement_score(
    student_id: str,
    course_id: str,
    days_back: int = Query(default=30, ge=1, le=365),
    activity_service: IStudentActivityService = Depends(get_activity_service)
):
    """
    Calculate student engagement score using multi-dimensional measurement.

    Score considers behavioral, cognitive, social, and emotional engagement.
    """
    try:
        engagement = await activity_service.calculate_engagement_score(
            student_id, course_id, days_back
        )
        return engagement
    except AnalyticsException:
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message=f"Failed to calculate engagement score: {str(e)}",
            student_id=student_id,
            course_id=course_id,
            analytics_type="engagement",
            original_exception=e
        )


@router.get("/courses/{course_id}/activity-summary")
async def get_course_activity_summary(
    course_id: str,
    days_back: int = Query(default=30, ge=1, le=365),
    activity_service: IStudentActivityService = Depends(get_activity_service)
):
    """Get course-wide activity summary for instructional insights."""
    try:
        summary = await activity_service.get_course_activity_summary(course_id, days_back)
        return summary
    except AnalyticsException:
        raise
    except Exception as e:
        raise AnalyticsException(
            message=f"Failed to generate course activity summary: {str(e)}",
            analytics_type="course_activity",
            original_exception=e
        )


# ========================================
# Lab Analytics Routes
# ========================================

@router.post("/lab-usage")
async def record_lab_usage(
    request: LabUsageRequest,
    lab_service: ILabAnalyticsService = Depends(get_lab_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Record lab usage metrics for hands-on learning analytics."""
    try:
        lab_metrics = LabUsageMetrics(
            student_id=request.student_id,
            course_id=request.course_id,
            lab_id=request.lab_id,
            actions_performed=request.actions_performed,
            code_executions=request.code_executions,
            errors_encountered=request.errors_encountered,
            final_code=request.final_code
        )

        await lab_service.record_lab_usage(lab_metrics)
        return {"status": "success", "message": "Lab usage recorded"}

    except AnalyticsException:
        raise
    except Exception as e:
        raise DataCollectionException(
            message=f"Failed to record lab usage: {str(e)}",
            student_id=request.student_id,
            course_id=request.course_id,
            data_type="lab_usage",
            collection_method="api_endpoint",
            original_exception=e
        )


@router.get("/students/{student_id}/courses/{course_id}/lab-proficiency")
async def get_lab_proficiency(
    student_id: str,
    course_id: str,
    lab_service: ILabAnalyticsService = Depends(get_lab_service)
):
    """Calculate lab proficiency score for practical skill development."""
    try:
        proficiency = await lab_service.calculate_lab_proficiency(student_id, course_id)
        return proficiency
    except AnalyticsException:
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message=f"Failed to calculate lab proficiency: {str(e)}",
            student_id=student_id,
            course_id=course_id,
            analytics_type="lab_proficiency",
            original_exception=e
        )


# ========================================
# Quiz Performance Routes
# ========================================

@router.post("/quiz-performance")
async def record_quiz_performance(
    request: QuizPerformanceRequest,
    quiz_service: IQuizAnalyticsService = Depends(get_quiz_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Record quiz performance for knowledge assessment analytics."""
    try:
        quiz_perf = QuizPerformance(
            student_id=request.student_id,
            course_id=request.course_id,
            quiz_id=request.quiz_id,
            attempt_number=request.attempt_number,
            questions_total=request.questions_total,
            questions_answered=request.questions_answered,
            questions_correct=request.questions_correct,
            answers=request.answers,
            time_per_question=request.time_per_question
        )

        await quiz_service.record_quiz_performance(quiz_perf)
        return {"status": "success", "message": "Quiz performance recorded"}

    except AnalyticsException:
        raise
    except Exception as e:
        raise DataCollectionException(
            message=f"Failed to record quiz performance: {str(e)}",
            student_id=request.student_id,
            course_id=request.course_id,
            data_type="quiz_performance",
            collection_method="api_endpoint",
            original_exception=e
        )


# ========================================
# Progress Tracking Routes
# ========================================

@router.post("/progress")
async def update_progress(
    request: ProgressUpdateRequest,
    progress_service: IProgressTrackingService = Depends(get_progress_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Update student learning progress with mastery tracking."""
    try:
        progress = StudentProgress(
            student_id=request.student_id,
            course_id=request.course_id,
            content_item_id=request.content_item_id,
            content_type=ContentType(request.content_type.lower()),
            progress_percentage=request.progress_percentage,
            time_spent=request.time_spent_additional,
            mastery_score=request.mastery_score
        )

        await progress_service.update_progress(progress)
        return {"status": "success", "message": "Progress updated"}

    except ValueError as e:
        raise ValidationException(
            message=f"Invalid progress data: {str(e)}",
            validation_errors={"content_type": str(e)},
            original_exception=e
        )
    except AnalyticsException:
        raise
    except Exception as e:
        raise DataCollectionException(
            message=f"Failed to update progress: {str(e)}",
            student_id=request.student_id,
            course_id=request.course_id,
            data_type="progress",
            collection_method="api_endpoint",
            original_exception=e
        )


@router.get("/students/{student_id}/courses/{course_id}/progress-summary")
async def get_progress_summary(
    student_id: str,
    course_id: str,
    progress_service: IProgressTrackingService = Depends(get_progress_service)
):
    """Get comprehensive progress summary for student."""
    try:
        summary = await progress_service.get_progress_summary(student_id, course_id)
        return summary
    except AnalyticsException:
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message=f"Failed to generate progress summary: {str(e)}",
            student_id=student_id,
            course_id=course_id,
            analytics_type="progress_summary",
            original_exception=e
        )


# ========================================
# Comprehensive Learning Analytics Routes
# ========================================

@router.post("/students/{student_id}/courses/{course_id}/analytics",
             response_model=LearningAnalyticsResponse)
async def generate_student_analytics(
    student_id: str,
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """Generate comprehensive learning analytics for student."""
    try:
        analytics = await analytics_service.generate_student_analytics(student_id, course_id)
        return _analytics_to_response(analytics)
    except AnalyticsException:
        raise
    except Exception as e:
        raise LearningAnalyticsException(
            message=f"Failed to generate student analytics: {str(e)}",
            student_id=student_id,
            course_id=course_id,
            analytics_type="comprehensive",
            aggregation_period="current",
            original_exception=e
        )


@router.get("/courses/{course_id}/analytics-summary",
            response_model=CourseAnalyticsSummaryResponse)
async def get_course_analytics_summary(
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """Get course-wide analytics summary for instructors."""
    try:
        summary = await analytics_service.get_course_analytics_summary(course_id)
        return summary
    except AnalyticsException:
        raise
    except Exception as e:
        raise AnalyticsException(
            message=f"Failed to generate course analytics summary: {str(e)}",
            analytics_type="course_summary",
            original_exception=e
        )


@router.get("/students/{student_id}/courses/{course_id}/performance-comparison")
async def compare_student_performance(
    student_id: str,
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """Compare student performance against class averages."""
    try:
        comparison = await analytics_service.compare_student_performance(student_id, course_id)
        return comparison
    except AnalyticsException:
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message=f"Failed to compare student performance: {str(e)}",
            student_id=student_id,
            course_id=course_id,
            analytics_type="performance_comparison",
            original_exception=e
        )


@router.get("/students/{student_id}/courses/{course_id}/prediction")
async def predict_performance(
    student_id: str,
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """Predict student performance using machine learning models."""
    try:
        prediction = await analytics_service.predict_performance(student_id, course_id)
        return prediction
    except AnalyticsException:
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message=f"Failed to predict student performance: {str(e)}",
            student_id=student_id,
            course_id=course_id,
            analytics_type="performance_prediction",
            original_exception=e
        )


# ========================================
# Reporting Routes
# ========================================

@router.post("/reports/student", response_model=ReportResponse)
async def generate_student_report(
    request: AnalyticsRequest,
    reporting_service: IReportingService = Depends(get_reporting_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Generate comprehensive student analytics report."""
    try:
        if not request.student_id:
            raise ValidationException(
                message="Student ID required for student report",
                validation_errors={"student_id": "Required field"}
            )

        report = await reporting_service.generate_student_report(
            student_id=request.student_id,
            course_id=request.course_id,
            start_date=request.start_date,
            end_date=request.end_date,
            metrics=request.metrics,
            format=request.format
        )
        return report
    except AnalyticsException:
        raise
    except Exception as e:
        raise AnalyticsException(
            message=f"Failed to generate student report: {str(e)}",
            analytics_type="student_report",
            original_exception=e
        )


@router.post("/reports/course", response_model=ReportResponse)
async def generate_course_report(
    request: AnalyticsRequest,
    reporting_service: IReportingService = Depends(get_reporting_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Generate comprehensive course analytics report."""
    try:
        if not request.course_id:
            raise ValidationException(
                message="Course ID required for course report",
                validation_errors={"course_id": "Required field"}
            )

        report = await reporting_service.generate_course_report(
            course_id=request.course_id,
            start_date=request.start_date,
            end_date=request.end_date,
            metrics=request.metrics,
            format=request.format
        )
        return report
    except AnalyticsException:
        raise
    except Exception as e:
        raise AnalyticsException(
            message=f"Failed to generate course report: {str(e)}",
            analytics_type="course_report",
            original_exception=e
        )


# ========================================
# Risk Assessment Routes
# ========================================

@router.get("/students/{student_id}/courses/{course_id}/risk-assessment")
async def assess_student_risk(
    student_id: str,
    course_id: str,
    risk_service: IRiskAssessmentService = Depends(get_risk_service)
):
    """Assess student risk level for early intervention."""
    try:
        risk_assessment = await risk_service.assess_student_risk(student_id, course_id)
        return risk_assessment
    except AnalyticsException:
        raise
    except Exception as e:
        raise StudentAnalyticsException(
            message=f"Failed to assess student risk: {str(e)}",
            student_id=student_id,
            course_id=course_id,
            analytics_type="risk_assessment",
            original_exception=e
        )
