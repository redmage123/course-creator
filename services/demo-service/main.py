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
Demo Service - Realistic Platform Demonstration Backend

BUSINESS REQUIREMENT:
This service provides a fully functional demo backend that simulates all Course Creator 
Platform features with realistic sample data for potential customers, stakeholders, and 
system demonstrations. No real data is stored - everything is generated on-demand to 
showcase platform capabilities while maintaining data privacy and security.

TECHNICAL ARCHITECTURE:
The demo service implements a stateless demonstration layer that generates realistic 
educational data patterns, user interactions, and system responses to provide authentic 
platform experiences without requiring actual user data or system integrations.

KEY DEMO FEATURES:
1. **Multi-Role Experiences**: Separate demo flows for instructors, students, and administrators
2. **Realistic Data Generation**: Authentic educational content, user profiles, and analytics
3. **Session Management**: Time-limited demo sessions with automatic cleanup
4. **Feature Showcasing**: Demonstrates all platform capabilities including AI-powered features
5. **Performance Simulation**: Realistic response times and data volumes for authentic experience
6. **Security Compliance**: No real data storage, privacy-safe demonstration environment

INTEGRATION POINTS:
- Sales and Marketing: Customer demonstrations and platform showcases
- Training and Onboarding: New user orientation and feature education
- Development Testing: Realistic data for frontend and integration testing
- Stakeholder Reviews: Executive and investor platform demonstrations
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from exceptions import (
    CourseCreatorBaseException,
    ValidationException,
    BusinessRuleException,
    ConfigurationException
)

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

# Global exception handlers for structured error responses
@app.exception_handler(ValidationException)
async def validation_exception_handler(request, exc: ValidationException):
    """
    Handle validation exceptions with detailed error information.
    
    Business Context:
    Validation errors in demo service indicate incorrect API usage or invalid
    demo session parameters, requiring clear guidance for users.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "validation_errors": exc.details.get("field_errors", {}),
            "details": exc.details,
            "demo_context": {
                "service": "demo-service",
                "timestamp": exc.timestamp.isoformat(),
                "help": "Check demo session parameters and try again"
            }
        }
    )

@app.exception_handler(BusinessRuleException) 
async def business_rule_exception_handler(request, exc: BusinessRuleException):
    """
    Handle business rule exceptions for demo service operations.
    
    Business Context:
    Business rule violations in demo service typically relate to session
    management, user type restrictions, or demo capability limits.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "demo_context": {
                "service": "demo-service", 
                "timestamp": exc.timestamp.isoformat(),
                "help": "Review demo session requirements or start a new session"
            }
        }
    )

@app.exception_handler(CourseCreatorBaseException)
async def course_creator_exception_handler(request, exc: CourseCreatorBaseException):
    """
    Handle generic platform exceptions in demo service.
    
    Business Context:
    Platform exceptions in demo service indicate system-level issues that
    may affect demo functionality and user experience.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "demo_context": {
                "service": "demo-service",
                "timestamp": exc.timestamp.isoformat(),
                "help": "Demo service encountered an issue. Please try again or start a new session."
            }
        }
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
    Start a new demo session with realistic user context and role-specific capabilities.
    
    Business Context:
    Demo sessions provide time-limited, realistic platform experiences for different user roles,
    enabling effective product demonstrations, user training, and stakeholder presentations
    without requiring actual user data or system setup.
    
    Available user types:
    - instructor: Experience as course creator and teacher with content generation capabilities
    - student: Experience as learner taking courses with progress tracking and lab access
    - admin: Experience as organization administrator with user and system management features
    
    Technical Implementation:
    - Generates unique session identifiers with automatic expiration
    - Creates role-specific user contexts with realistic data patterns
    - Maintains stateless demo environment with in-memory session management
    """
    try:
        if user_type not in DEMO_USER_TYPES:
            raise ValidationException(
                message="Invalid demo user type specified",
                error_code="INVALID_DEMO_USER_TYPE",
                validation_errors={"user_type": f"User type '{user_type}' not supported"},
                details={"supported_types": list(DEMO_USER_TYPES.keys())}
            )
        
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
            "message": f"Demo session started as {user_type}. This session will expire in 2 hours.",
            "demo_capabilities": {
                "instructor": ["AI course creation", "Student analytics", "Lab management", "Content generation"],
                "student": ["Course enrollment", "Interactive labs", "Progress tracking", "Assignment submission"], 
                "admin": ["User management", "Organization setup", "System analytics", "Platform configuration"]
            }.get(user_type, [])
        }
        
    except ValidationException:
        # Re-raise validation exceptions
        raise
    except Exception as e:
        raise BusinessRuleException(
            message="Failed to create demo session",
            error_code="DEMO_SESSION_CREATION_FAILED",
            details={"user_type": user_type},
            original_exception=e
        )

def get_demo_session(session_id: str = Query(...)):
    """
    Dependency to validate and retrieve demo session with comprehensive error handling.
    
    Business Context:
    Session validation ensures secure demo access, prevents unauthorized usage,
    and maintains demo session lifecycle with automatic cleanup of expired sessions.
    
    Technical Implementation:
    - Validates session existence and expiration
    - Provides structured error responses for different failure scenarios
    - Automatically cleans up expired sessions for memory management
    """
    try:
        if session_id not in demo_sessions:
            raise ValidationException(
                message="Demo session not found",
                error_code="DEMO_SESSION_NOT_FOUND",
                validation_errors={"session_id": "Session ID does not exist or has been cleaned up"},
                details={"session_id": session_id}
            )
        
        session = demo_sessions[session_id]
        if datetime.now() > session.expires_at:
            # Clean up expired session
            del demo_sessions[session_id]
            raise BusinessRuleException(
                message="Demo session has expired",
                error_code="DEMO_SESSION_EXPIRED",
                details={
                    "session_id": session_id,
                    "expired_at": session.expires_at.isoformat(),
                    "action_required": "Start a new demo session"
                }
            )
        
        return session
        
    except (ValidationException, BusinessRuleException):
        # Re-raise structured exceptions 
        raise
    except Exception as e:
        raise BusinessRuleException(
            message="Failed to validate demo session",
            error_code="DEMO_SESSION_VALIDATION_ERROR",
            details={"session_id": session_id},
            original_exception=e
        )

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
    """
    Get realistic demo student data with progress tracking and engagement metrics.
    
    Business Context:
    Student data demonstrations showcase progress tracking, engagement analytics,
    and instructor dashboard capabilities essential for educational platform evaluation.
    Access is restricted to instructor and admin roles to simulate proper RBAC.
    
    Technical Implementation:
    - Role-based access control validation
    - Realistic student profile generation with authentic engagement patterns
    - Course-specific filtering when course_id provided
    - Performance metrics and learning analytics simulation
    """
    try:
        if session.user_type not in ["instructor", "admin"]:
            raise BusinessRuleException(
                message="Insufficient permissions to view student data",
                error_code="DEMO_INSUFFICIENT_PERMISSIONS",
                details={
                    "user_type": session.user_type,
                    "required_roles": ["instructor", "admin"],
                    "available_features": {
                        "student": ["Course enrollment", "Progress viewing", "Lab access"],
                        "instructor": ["Student analytics", "Course management", "Grading"],
                        "admin": ["All features", "User management", "System analytics"]
                    }
                }
            )
        
        students = generate_demo_students(
            course_id=course_id,
            instructor_context=session.user_data
        )
        
        return {
            "students": students,
            "total_students": len(students),
            "demo_context": {
                "message": "Sample student data with realistic progress and engagement metrics",
                "features_demonstrated": [
                    "Student progress tracking",
                    "Engagement analytics", 
                    "Performance metrics",
                    "Learning outcomes assessment"
                ],
                "course_filter": f"Filtered by course: {course_id}" if course_id else "All courses shown"
            }
        }
        
    except BusinessRuleException:
        # Re-raise business rule exceptions
        raise
    except Exception as e:
        raise BusinessRuleException(
            message="Failed to generate demo student data",
            error_code="DEMO_STUDENT_GENERATION_ERROR",
            details={"course_id": course_id, "user_type": session.user_type},
            original_exception=e
        )

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
        log_level="info",
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt"
    )