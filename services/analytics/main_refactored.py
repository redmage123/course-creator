#!/usr/bin/env python3
"""
Analytics Service - Refactored following SOLID principles
Single Responsibility: API layer only - business logic delegated to services
Open/Closed: Extensible through dependency injection
Liskov Substitution: Uses interface abstractions
Interface Segregation: Clean, focused interfaces
Dependency Inversion: Depends on abstractions, not concretions
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import hydra
from omegaconf import DictConfig
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

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

# API Models (DTOs - following Single Responsibility)
class StudentActivityRequest(BaseModel):
    student_id: str
    course_id: str
    activity_type: str = Field(..., description="Activity type (login, quiz_start, etc.)")
    activity_data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class LabUsageRequest(BaseModel):
    student_id: str
    course_id: str
    lab_id: str
    actions_performed: int = 0
    code_executions: int = 0
    errors_encountered: int = 0
    final_code: Optional[str] = None

class QuizPerformanceRequest(BaseModel):
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
    student_id: str
    course_id: str
    content_item_id: str
    content_type: str = Field(..., pattern="^(module|lesson|lab|quiz|assignment|exercise)$")
    progress_percentage: float = Field(..., ge=0, le=100)
    time_spent_additional: int = Field(default=0, ge=0)
    mastery_score: Optional[float] = Field(None, ge=0, le=100)

class AnalyticsRequest(BaseModel):
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = Field(default_factory=list)
    aggregation: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")
    format: str = Field(default="json", pattern="^(json|csv|pdf)$")

# Response Models
class StudentActivityResponse(BaseModel):
    id: str
    student_id: str
    course_id: str
    activity_type: str
    timestamp: datetime
    activity_data: Dict[str, Any]
    session_id: Optional[str] = None

class EngagementScoreResponse(BaseModel):
    student_id: str
    course_id: str
    engagement_score: float
    calculation_date: datetime
    days_analyzed: int
    activity_breakdown: Dict[str, int]

class LearningAnalyticsResponse(BaseModel):
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
    course_id: str
    total_students: int
    averages: Dict[str, float]
    risk_distribution: Dict[str, int]
    high_performers: List[Dict[str, Any]]
    at_risk_students: List[Dict[str, Any]]
    last_updated: datetime

class ReportResponse(BaseModel):
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
    """FastAPI lifespan event handler"""
    global container, current_config
    
    # Startup
    logging.info("Initializing Analytics Service...")
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
    Application factory following SOLID principles
    Open/Closed: New routes can be added without modifying existing code
    """
    global current_config
    current_config = config
    
    app = FastAPI(
        title="Analytics Service",
        description="Comprehensive student analytics, progress tracking, and reporting",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

app = create_app(current_config or {})

# Dependency injection helpers
def get_activity_service() -> IStudentActivityService:
    """Dependency injection for student activity service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_student_activity_service()

def get_lab_service() -> ILabAnalyticsService:
    """Dependency injection for lab analytics service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_lab_analytics_service()

def get_quiz_service() -> IQuizAnalyticsService:
    """Dependency injection for quiz analytics service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_quiz_analytics_service()

def get_progress_service() -> IProgressTrackingService:
    """Dependency injection for progress tracking service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_progress_tracking_service()

def get_analytics_service() -> ILearningAnalyticsService:
    """Dependency injection for learning analytics service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_learning_analytics_service()

def get_reporting_service() -> IReportingService:
    """Dependency injection for reporting service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_reporting_service()

def get_risk_service() -> IRiskAssessmentService:
    """Dependency injection for risk assessment service"""
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_risk_assessment_service()

def get_current_user_id() -> str:
    """
    Extract user ID from JWT token
    For now, return a mock user ID - in production, this would validate JWT
    """
    return "user_123"  # Mock implementation

# Student Activity Endpoints
@app.post("/api/v1/activities", response_model=StudentActivityResponse)
async def record_activity(
    request: StudentActivityRequest,
    activity_service: IStudentActivityService = Depends(get_activity_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """Record a new student activity"""
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error recording activity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/students/{student_id}/courses/{course_id}/engagement", response_model=EngagementScoreResponse)
async def get_engagement_score(
    student_id: str,
    course_id: str,
    days_back: int = Query(default=30, ge=1, le=365),
    activity_service: IStudentActivityService = Depends(get_activity_service)
):
    """Get student engagement score"""
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting engagement score: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/courses/{course_id}/activity-summary")
async def get_course_activity_summary(
    course_id: str,
    days_back: int = Query(default=7, ge=1, le=90),
    activity_service: IStudentActivityService = Depends(get_activity_service)
):
    """Get activity summary for a course"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days_back)
        summary = await activity_service.get_activity_summary(
            course_id=course_id,
            start_date=start_date
        )
        
        return summary
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting activity summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Lab Analytics Endpoints
@app.post("/api/v1/lab-usage")
async def record_lab_usage(
    request: LabUsageRequest,
    lab_service: ILabAnalyticsService = Depends(get_lab_service)
):
    """Record lab usage metrics"""
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error recording lab usage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/students/{student_id}/courses/{course_id}/lab-proficiency")
async def get_lab_proficiency(
    student_id: str,
    course_id: str,
    lab_service: ILabAnalyticsService = Depends(get_lab_service)
):
    """Get student's lab proficiency score"""
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
        
    except Exception as e:
        logging.error(f"Error getting lab proficiency: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Quiz Analytics Endpoints
@app.post("/api/v1/quiz-performance")
async def record_quiz_performance(
    request: QuizPerformanceRequest,
    quiz_service: IQuizAnalyticsService = Depends(get_quiz_service)
):
    """Record quiz performance data"""
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error recording quiz performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Progress Tracking Endpoints
@app.post("/api/v1/progress")
async def update_progress(
    request: ProgressUpdateRequest,
    progress_service: IProgressTrackingService = Depends(get_progress_service)
):
    """Update student progress on content item"""
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error updating progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/students/{student_id}/courses/{course_id}/progress-summary")
async def get_progress_summary(
    student_id: str,
    course_id: str,
    progress_service: IProgressTrackingService = Depends(get_progress_service)
):
    """Get student's progress summary for a course"""
    try:
        summary = await progress_service.get_progress_summary(
            student_id=student_id,
            course_id=course_id
        )
        
        return summary
        
    except Exception as e:
        logging.error(f"Error getting progress summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Learning Analytics Endpoints
@app.post("/api/v1/students/{student_id}/courses/{course_id}/analytics", response_model=LearningAnalyticsResponse)
async def generate_student_analytics(
    student_id: str,
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """Generate comprehensive analytics for a student"""
    try:
        analytics = await analytics_service.generate_student_analytics(
            student_id=student_id,
            course_id=course_id
        )
        
        return _analytics_to_response(analytics)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error generating analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/courses/{course_id}/analytics-summary", response_model=CourseAnalyticsSummaryResponse)
async def get_course_analytics_summary(
    course_id: str,
    analytics_service: ILearningAnalyticsService = Depends(get_analytics_service)
):
    """Get analytics summary for entire course"""
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
        
    except Exception as e:
        logging.error(f"Error getting course analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error comparing performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error predicting performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Reporting Endpoints
@app.post("/api/v1/reports/student", response_model=ReportResponse)
async def generate_student_report(
    request: AnalyticsRequest,
    reporting_service: IReportingService = Depends(get_reporting_service)
):
    """Generate comprehensive student report"""
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error generating student report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/reports/course", response_model=ReportResponse)
async def generate_course_report(
    request: AnalyticsRequest,
    reporting_service: IReportingService = Depends(get_reporting_service)
):
    """Generate course-wide analytics report"""
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error generating course report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Risk Assessment Endpoints
@app.get("/api/v1/students/{student_id}/courses/{course_id}/risk-assessment")
async def assess_student_risk(
    student_id: str,
    course_id: str,
    risk_service: IRiskAssessmentService = Depends(get_risk_service)
):
    """Assess student risk level"""
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
        
    except Exception as e:
        logging.error(f"Error assessing risk: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "2.0.0",
        "timestamp": datetime.utcnow()
    }

# Helper functions (following Single Responsibility)
def _activity_to_response(activity: StudentActivity) -> StudentActivityResponse:
    """Convert domain entity to API response DTO"""
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
    """Convert domain entity to API response DTO"""
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
    """Main entry point using Hydra configuration"""
    global current_config
    current_config = cfg
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, cfg.logging.level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Analytics Service on port {cfg.server.port}")
    
    # Create app with configuration
    global app
    app = create_app(cfg)
    
    # Run server
    uvicorn.run(
        app,
        host=cfg.server.host,
        port=cfg.server.port,
        log_level=cfg.logging.level.lower()
    )

if __name__ == "__main__":
    main()