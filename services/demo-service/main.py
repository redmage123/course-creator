"""
Demo Service - Realistic Platform Demonstration Backend

This service provides a fully functional demo backend that simulates
all Course Creator Platform features with realistic sample data.
No real data is stored - everything is generated on-demand.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Demo data generators
from demo_data_generator import (
    DemoUser,
    generate_demo_analytics,
    generate_demo_courses,
    generate_demo_feedback,
    generate_demo_labs,
    generate_demo_students,
)

app = FastAPI(
    title="Course Creator Demo Service",
    description="Realistic demo backend showcasing platform capabilities",
    version="1.0.0"
)

# CORS configuration for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://176.9.99.103:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo session storage (in-memory for demo purposes)
demo_sessions = {}

# Demo user types with different experiences
DEMO_USER_TYPES = {
    "instructor": {
        "name": "Dr. Sarah Johnson",
        "email": "sarah.johnson@democorp.edu",
        "role": "instructor",
        "organization": "Demo University",
        "courses_created": 12,
        "students_taught": 340,
        "experience_level": "expert"
    },
    "student": {
        "name": "Alex Chen",
        "email": "alex.chen@student.edu", 
        "role": "student",
        "organization": "Demo University",
        "courses_enrolled": 5,
        "completion_rate": 78,
        "experience_level": "intermediate"
    },
    "admin": {
        "name": "Marcus Williams",
        "email": "marcus.williams@democorp.edu",
        "role": "admin",
        "organization": "Demo Corporation",
        "users_managed": 1250,
        "organizations": 3,
        "experience_level": "expert"
    }
}

class DemoSession(BaseModel):
    """Demo session model"""
    session_id: str
    user_type: str
    created_at: datetime
    expires_at: datetime
    user_data: Dict[str, Any]

@app.post("/api/v1/demo/start")
async def start_demo_session(user_type: str = "instructor"):
    """
    Start a new demo session with realistic user context
    
    Available user types:
    - instructor: Experience as course creator and teacher
    - student: Experience as learner taking courses
    - admin: Experience as organization administrator
    """
    if user_type not in DEMO_USER_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid user type. Available: {list(DEMO_USER_TYPES.keys())}")
    
    session_id = str(uuid.uuid4())
    user_data = DEMO_USER_TYPES[user_type].copy()
    user_data["id"] = f"demo-{user_type}-{session_id[:8]}"
    user_data["is_demo"] = True
    
    demo_session = DemoSession(
        session_id=session_id,
        user_type=user_type,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=2),  # 2 hour demo session
        user_data=user_data
    )
    
    demo_sessions[session_id] = demo_session
    
    return {
        "session_id": session_id,
        "user": user_data,
        "expires_at": demo_session.expires_at.isoformat(),
        "message": f"Demo session started as {user_type}. This session will expire in 2 hours."
    }

def get_demo_session(session_id: str = Query(...)):
    """Dependency to validate demo session"""
    if session_id not in demo_sessions:
        raise HTTPException(status_code=404, detail="Demo session not found")
    
    session = demo_sessions[session_id]
    if datetime.now() > session.expires_at:
        del demo_sessions[session_id]
        raise HTTPException(status_code=401, detail="Demo session expired")
    
    return session

@app.get("/api/v1/demo/courses")
async def get_demo_courses(
    session: DemoSession = Depends(get_demo_session),
    limit: int = Query(10, ge=1, le=100)
):
    """Get realistic demo courses based on user type"""
    courses = generate_demo_courses(
        user_type=session.user_type,
        user_data=session.user_data,
        count=limit
    )
    
    return {
        "courses": courses,
        "total": len(courses),
        "demo_context": {
            "user_type": session.user_type,
            "message": "These are realistic sample courses generated for demonstration"
        }
    }

@app.get("/api/v1/demo/students")
async def get_demo_students(
    session: DemoSession = Depends(get_demo_session),
    course_id: Optional[str] = None
):
    """Get demo students data"""
    if session.user_type not in ["instructor", "admin"]:
        raise HTTPException(status_code=403, detail="Only instructors and admins can view student data")
    
    students = generate_demo_students(
        course_id=course_id,
        instructor_context=session.user_data
    )
    
    return {
        "students": students,
        "demo_context": {
            "message": "Sample student data with realistic progress and engagement metrics"
        }
    }

@app.get("/api/v1/demo/analytics")
async def get_demo_analytics(
    session: DemoSession = Depends(get_demo_session),
    timeframe: str = Query("30d", regex="^(7d|30d|90d|1y)$")
):
    """Get comprehensive demo analytics"""
    analytics = generate_demo_analytics(
        user_type=session.user_type,
        user_data=session.user_data,
        timeframe=timeframe
    )
    
    return {
        "analytics": analytics,
        "timeframe": timeframe,
        "demo_context": {
            "message": "Real-time style analytics with trending data and insights"
        }
    }

@app.get("/api/v1/demo/labs")
async def get_demo_labs(
    session: DemoSession = Depends(get_demo_session),
    course_id: Optional[str] = None
):
    """Get demo interactive lab environments"""
    labs = generate_demo_labs(
        user_type=session.user_type,
        course_id=course_id
    )
    
    return {
        "labs": labs,
        "demo_context": {
            "message": "Interactive coding labs with multiple IDE options"
        }
    }

@app.get("/api/v1/demo/feedback")
async def get_demo_feedback(
    session: DemoSession = Depends(get_demo_session),
    course_id: Optional[str] = None
):
    """Get realistic student feedback and ratings"""
    feedback = generate_demo_feedback(
        course_id=course_id,
        instructor_context=session.user_data if session.user_type == "instructor" else None
    )
    
    return {
        "feedback": feedback,
        "demo_context": {
            "message": "Realistic student feedback with sentiment analysis"
        }
    }

@app.post("/api/v1/demo/course/create")
async def create_demo_course(
    course_data: Dict[str, Any],
    session: DemoSession = Depends(get_demo_session)
):
    """Simulate AI-powered course creation"""
    if session.user_type not in ["instructor", "admin"]:
        raise HTTPException(status_code=403, detail="Only instructors can create courses")
    
    # Simulate AI processing time
    import asyncio
    await asyncio.sleep(2)
    
    # Generate realistic course based on input
    new_course = {
        "id": str(uuid.uuid4()),
        "title": course_data.get("title", "Demo Course"),
        "description": course_data.get("description", "AI-generated course content"),
        "created_by": session.user_data["id"],
        "created_at": datetime.now().isoformat(),
        "ai_generated": True,
        "modules": [
            {
                "id": str(uuid.uuid4()),
                "title": f"Module {i+1}: {topic}",
                "lessons": random.randint(3, 8),
                "quizzes": random.randint(1, 3),
                "labs": random.randint(0, 2)
            }
            for i, topic in enumerate(["Introduction", "Core Concepts", "Advanced Topics", "Practical Applications"])
        ],
        "estimated_duration": f"{random.randint(4, 12)} hours",
        "difficulty": random.choice(["Beginner", "Intermediate", "Advanced"]),
        "demo_note": "This course was generated instantly using AI for demonstration"
    }
    
    return {
        "course": new_course,
        "message": "Course created successfully with AI assistance!",
        "demo_context": {
            "ai_features": ["Content generation", "Quiz creation", "Lab setup", "Learning path optimization"]
        }
    }

@app.get("/api/v1/demo/session/info")
async def get_demo_session_info(session: DemoSession = Depends(get_demo_session)):
    """Get current demo session information"""
    time_remaining = session.expires_at - datetime.now()
    minutes_remaining = int(time_remaining.total_seconds() / 60)
    
    return {
        "session_id": session.session_id,
        "user": session.user_data,
        "expires_at": session.expires_at.isoformat(),
        "minutes_remaining": minutes_remaining,
        "user_type": session.user_type,
        "demo_features_available": [
            "AI course generation",
            "Interactive labs", 
            "Real-time analytics",
            "Student progress tracking",
            "Automated assessments",
            "Multi-IDE support"
        ]
    }

@app.delete("/api/v1/demo/session")
async def end_demo_session(session: DemoSession = Depends(get_demo_session)):
    """End demo session and cleanup"""
    session_id = session.session_id
    if session_id in demo_sessions:
        del demo_sessions[session_id]
    
    return {
        "message": "Demo session ended successfully",
        "thank_you": "Thanks for trying Course Creator Platform!"
    }

@app.get("/api/v1/demo/health")
async def demo_health_check():
    """Health check for demo service"""
    return {
        "status": "healthy",
        "service": "demo-service",
        "active_sessions": len(demo_sessions),
        "uptime": datetime.now().isoformat(),
        "demo_ready": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8010,
        reload=True,
        log_level="info"
    )