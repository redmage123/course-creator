"""
Student Analytics Service
Provides comprehensive analytics and reporting for student progress, lab usage, quiz performance, and engagement metrics.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import uuid
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg
import structlog
from pydantic import BaseModel, Field
import json
import os
from pathlib import Path

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
security = HTTPBearer()

# Initialize FastAPI app
app = FastAPI(
    title="Student Analytics Service",
    description="Comprehensive student analytics, progress tracking, and reporting",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
db_pool = None

# Pydantic Models
class StudentActivity(BaseModel):
    """Student activity tracking model"""
    activity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    activity_type: str  # login, logout, lab_access, quiz_start, quiz_complete, content_view
    activity_data: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class LabUsageMetrics(BaseModel):
    """Lab usage metrics model"""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    lab_id: str
    session_start: datetime
    session_end: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    actions_performed: int = 0
    code_executions: int = 0
    errors_encountered: int = 0
    completion_status: str = "in_progress"  # in_progress, completed, abandoned
    final_code: Optional[str] = None

class QuizPerformance(BaseModel):
    """Quiz performance tracking model"""
    performance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    quiz_id: str
    attempt_number: int = 1
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    questions_total: int
    questions_answered: int = 0
    questions_correct: int = 0
    score_percentage: Optional[float] = None
    answers: Dict = Field(default_factory=dict)  # question_id -> answer
    time_per_question: Dict = Field(default_factory=dict)  # question_id -> seconds
    status: str = "in_progress"  # in_progress, completed, abandoned

class StudentProgress(BaseModel):
    """Student progress tracking model"""
    progress_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    content_item_id: str
    content_type: str  # module, lesson, lab, quiz, assignment
    status: str  # not_started, in_progress, completed, mastered
    progress_percentage: float = 0.0
    time_spent_minutes: int = 0
    last_accessed: datetime
    completion_date: Optional[datetime] = None
    mastery_score: Optional[float] = None

class LearningAnalytics(BaseModel):
    """Comprehensive learning analytics model"""
    analytics_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    engagement_score: float = 0.0  # 0-100
    progress_velocity: float = 0.0  # content items per week
    lab_proficiency: float = 0.0  # 0-100
    quiz_performance: float = 0.0  # average percentage
    time_on_platform: int = 0  # minutes
    streak_days: int = 0
    risk_level: str = "low"  # low, medium, high
    recommendations: List[str] = Field(default_factory=list)

class AnalyticsRequest(BaseModel):
    """Analytics request model"""
    student_id: Optional[str] = None
    course_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = Field(default_factory=list)  # specific metrics to include
    aggregation: str = "daily"  # daily, weekly, monthly
    export_format: str = "json"  # json, csv, pdf

class AnalyticsResponse(BaseModel):
    """Analytics response model"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    data_range: Dict[str, datetime]
    summary: Dict
    detailed_data: Dict
    visualizations: List[Dict] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

# Database connection functions
async def init_db():
    """Initialize database connection pool"""
    global db_pool
    
    # Use shared database configuration - same as other services
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'course_creator'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres_password')
    }
    
    try:
        db_pool = await asyncpg.create_pool(**db_config, min_size=5, max_size=20)
        logger.info("Analytics service connected to shared course creator database")
        
        # Check if analytics tables exist (they should be created via migrations)
        await check_analytics_tables()
        
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {str(e)}")
        raise

async def check_analytics_tables():
    """Check if analytics tables exist in the shared database"""
    async with db_pool.acquire() as conn:
        # Check for analytics tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('student_activities', 'lab_usage_metrics', 'quiz_performance', 'student_progress', 'learning_analytics')
        """)
        
        table_names = [row['table_name'] for row in tables]
        expected_tables = ['student_activities', 'lab_usage_metrics', 'quiz_performance', 'student_progress', 'learning_analytics']
        
        missing_tables = set(expected_tables) - set(table_names)
        
        if missing_tables:
            logger.warning(f"Missing analytics tables: {missing_tables}")
            logger.info("Please run database migrations: python setup-database.py")
        else:
            logger.info("All analytics tables are present in shared database")

# Startup event
@app.on_event("startup")
async def startup():
    await init_db()

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "analytics",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "database_status": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user info"""
    # TODO: Implement JWT verification
    # For now, return mock user
    return {
        "id": "user-123",
        "role": "instructor",
        "email": "instructor@example.com"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)