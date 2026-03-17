"""
Demo Data Access Object (DAO)

This module implements the Data Access Object (DAO) pattern for demo data generation operations,
centralizing all demo data creation, session management, and realistic data simulation patterns.

Business Context:
The Demo DAO encapsulates all demonstration data generation and session management logic,
providing a clean abstraction layer for creating realistic platform demonstrations without
storing actual user data. This separation enables better testing, maintenance, and consistent
demo experiences while maintaining security and privacy compliance.

Technical Rationale:
- Follows the Single Responsibility Principle by isolating demo data operations
- Enables comprehensive session management for time-limited demonstrations
- Provides consistent data generation patterns across all demo scenarios
- Supports role-based demo experiences for different user types
- Facilitates demo data schema evolution without affecting API logic
- Enables easier unit testing and demo scenario validation
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import json
import sys
sys.path.append('/app/shared')
from exceptions import (
    ValidationException,
    BusinessRuleException,
    CourseCreatorBaseException
)


class DemoDAO:
    """
    Data Access Object for Demo Data Generation and Session Management
    
    This class centralizes all demo data generation and session management operations,
    following the DAO pattern for clean architecture.
    
    Business Context:
    Provides comprehensive demo data generation methods including:
    - Session lifecycle management with automatic expiration
    - Role-based demo data generation for different user experiences
    - Realistic educational content simulation with authentic patterns
    - Performance analytics and engagement metrics generation
    - Demo environment state management and cleanup
    
    Technical Implementation:
    - Uses in-memory storage for session management (appropriate for demos)
    - Implements realistic data generation algorithms for authentic experiences
    - Provides session validation and security for demo access control
    - Includes comprehensive error handling and validation
    - Supports configurable demo parameters and customization
    - Implements efficient data generation patterns for performance
    """
    
    def __init__(self):
        """
        Initialize the Demo DAO with session storage and configuration.
        
        Business Context:
        The DAO manages demo sessions and provides data generation capabilities
        for realistic platform demonstrations without persistent data storage.
        """
        self.sessions = {}  # In-memory session storage for demo purposes
        self.logger = logging.getLogger(__name__)
        self.session_duration_hours = 2  # Default demo session duration
    
    # ================================================================
    # SESSION MANAGEMENT OPERATIONS
    # ================================================================
    
    def create_demo_session(self, user_type: str, session_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new demo session with role-specific configuration.
        
        Business Context:
        Demo session creation establishes a time-limited, secure environment for
        platform demonstrations, enabling role-specific experiences without
        affecting production data or requiring actual user registration.
        
        Args:
            user_type: Type of demo user (instructor, student, admin)
            session_config: Optional session configuration parameters
            
        Returns:
            Dictionary containing session information and user context
        """
        try:
            session_id = str(uuid.uuid4())
            config = session_config or {}
            duration_hours = config.get('duration_hours', self.session_duration_hours)
            
            # Generate realistic user context based on role
            user_context = self._generate_user_context(user_type, session_id)
            
            session_data = {
                "session_id": session_id,
                "user_type": user_type,
                "user_context": user_context,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=duration_hours),
                "capabilities": self._get_role_capabilities(user_type),
                "demo_config": config,
                "access_count": 0,
                "last_accessed": datetime.now()
            }
            
            self.sessions[session_id] = session_data
            
            self.logger.info(f"Created demo session {session_id} for user type: {user_type}")
            return session_data
            
        except Exception as e:
            raise BusinessRuleException(
                message="Failed to create demo session",
                error_code="DEMO_SESSION_CREATION_FAILED",
                details={"user_type": user_type, "config": session_config},
                original_exception=e
            )
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """
        Validate demo session and return session data if valid.
        
        Business Context:
        Session validation ensures secure demo access and maintains session
        lifecycle with automatic cleanup of expired sessions.
        
        Args:
            session_id: Session identifier to validate
            
        Returns:
            Valid session data with updated access tracking
        """
        try:
            if session_id not in self.sessions:
                raise ValidationException(
                    message="Demo session not found",
                    error_code="DEMO_SESSION_NOT_FOUND",
                    validation_errors={"session_id": "Session does not exist or has been cleaned up"},
                    details={"session_id": session_id}
                )
            
            session_data = self.sessions[session_id]
            
            # Check expiration
            if datetime.now() > session_data["expires_at"]:
                # Clean up expired session
                del self.sessions[session_id]
                raise BusinessRuleException(
                    message="Demo session has expired",
                    error_code="DEMO_SESSION_EXPIRED",
                    details={
                        "session_id": session_id,
                        "expired_at": session_data["expires_at"].isoformat(),
                        "session_duration": f"{self.session_duration_hours} hours"
                    }
                )
            
            # Update access tracking
            session_data["access_count"] += 1
            session_data["last_accessed"] = datetime.now()
            
            return session_data
            
        except (ValidationException, BusinessRuleException):
            # Re-raise structured exceptions
            raise
        except Exception as e:
            raise BusinessRuleException(
                message="Session validation failed",
                error_code="SESSION_VALIDATION_ERROR",
                details={"session_id": session_id},
                original_exception=e
            )
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired demo sessions to manage memory usage.
        
        Business Context:
        Regular session cleanup prevents memory leaks and maintains system
        performance for long-running demo service instances.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            current_time = datetime.now()
            expired_sessions = [
                session_id for session_id, data in self.sessions.items()
                if current_time > data["expires_at"]
            ]
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                self.logger.info(f"Cleaned up {len(expired_sessions)} expired demo sessions")
            
            return len(expired_sessions)
            
        except Exception as e:
            self.logger.warning(f"Session cleanup failed: {str(e)}")
            return 0
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive session statistics for monitoring.
        
        Business Context:
        Session statistics provide insights into demo usage patterns,
        performance metrics, and system load for capacity planning.
        
        Returns:
            Dictionary containing session statistics and metrics
        """
        try:
            current_time = datetime.now()
            active_sessions = [s for s in self.sessions.values() if current_time <= s["expires_at"]]
            
            stats = {
                "total_sessions": len(self.sessions),
                "active_sessions": len(active_sessions),
                "expired_sessions": len(self.sessions) - len(active_sessions),
                "user_type_distribution": {},
                "average_session_duration_hours": self.session_duration_hours,
                "oldest_session": None,
                "newest_session": None
            }
            
            # Calculate user type distribution
            for session in active_sessions:
                user_type = session["user_type"]
                stats["user_type_distribution"][user_type] = stats["user_type_distribution"].get(user_type, 0) + 1
            
            # Find oldest and newest sessions
            if active_sessions:
                sorted_sessions = sorted(active_sessions, key=lambda x: x["created_at"])
                stats["oldest_session"] = sorted_sessions[0]["created_at"].isoformat()
                stats["newest_session"] = sorted_sessions[-1]["created_at"].isoformat()
            
            return stats
            
        except Exception as e:
            raise BusinessRuleException(
                message="Failed to calculate session statistics",
                error_code="SESSION_STATS_ERROR",
                original_exception=e
            )
    
    # ================================================================
    # DEMO DATA GENERATION OPERATIONS  
    # ================================================================
    
    def generate_role_based_demo_data(self, user_type: str, data_type: str, 
                                     context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate role-specific demo data for different content types.
        
        Business Context:
        Role-based demo data generation provides authentic user experiences
        tailored to specific user types, showcasing relevant platform features
        and capabilities for each audience.
        
        Args:
            user_type: Type of user for data generation (instructor, student, admin)
            data_type: Type of data to generate (courses, analytics, labs, etc.)
            context: Optional context for data customization
            
        Returns:
            List of generated demo data objects
        """
        try:
            context = context or {}
            data_generators = {
                "courses": self._generate_demo_courses,
                "students": self._generate_demo_students,
                "analytics": self._generate_demo_analytics,
                "labs": self._generate_demo_labs,
                "feedback": self._generate_demo_feedback
            }
            
            if data_type not in data_generators:
                raise ValidationException(
                    message="Invalid demo data type requested",
                    error_code="INVALID_DEMO_DATA_TYPE",
                    validation_errors={"data_type": f"Data type '{data_type}' not supported"},
                    details={"supported_types": list(data_generators.keys())}
                )
            
            generator_func = data_generators[data_type]
            demo_data = generator_func(user_type, context)
            
            self.logger.debug(f"Generated {len(demo_data)} {data_type} items for {user_type}")
            return demo_data
            
        except ValidationException:
            # Re-raise validation exceptions
            raise
        except Exception as e:
            raise BusinessRuleException(
                message=f"Failed to generate demo data",
                error_code="DEMO_DATA_GENERATION_ERROR",
                details={"user_type": user_type, "data_type": data_type, "context": context},
                original_exception=e
            )
    
    # ================================================================
    # PRIVATE HELPER METHODS
    # ================================================================
    
    def _generate_user_context(self, user_type: str, session_id: str) -> Dict[str, Any]:
        """Generate realistic user context based on role type."""
        user_profiles = {
            "instructor": {
                "name": "Dr. Sarah Johnson",
                "email": f"demo-instructor-{session_id[:8]}@democorp.edu",
                "role": "instructor",
                "organization": "Demo University",
                "courses_created": random.randint(5, 25),
                "students_taught": random.randint(100, 500),
                "experience_level": random.choice(["experienced", "expert"])
            },
            "student": {
                "name": "Alex Chen",
                "email": f"demo-student-{session_id[:8]}@student.edu",
                "role": "student", 
                "organization": "Demo University",
                "courses_enrolled": random.randint(3, 8),
                "completion_rate": random.randint(60, 95),
                "experience_level": random.choice(["beginner", "intermediate"])
            },
            "admin": {
                "name": "Marcus Williams",
                "email": f"demo-admin-{session_id[:8]}@democorp.edu",
                "role": "admin",
                "organization": "Demo Corporation",
                "users_managed": random.randint(500, 2000),
                "organizations": random.randint(1, 5),
                "experience_level": "expert"
            }
        }
        
        base_context = user_profiles.get(user_type, user_profiles["instructor"])
        base_context.update({
            "id": f"demo-{user_type}-{session_id[:8]}",
            "is_demo": True,
            "demo_session": session_id
        })
        
        return base_context
    
    def _get_role_capabilities(self, user_type: str) -> List[str]:
        """Get role-specific capabilities for demo sessions."""
        capabilities_map = {
            "instructor": [
                "AI course creation", "Student analytics", "Lab management", 
                "Content generation", "Assessment creation", "Progress tracking"
            ],
            "student": [
                "Course enrollment", "Interactive labs", "Progress tracking", 
                "Assignment submission", "Quiz taking", "Resource access"
            ],
            "admin": [
                "User management", "Organization setup", "System analytics", 
                "Platform configuration", "Role management", "Usage monitoring"
            ]
        }
        
        return capabilities_map.get(user_type, capabilities_map["instructor"])
    
    def _generate_demo_courses(self, user_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate realistic demo courses based on user type and context."""
        course_count = context.get('count', random.randint(5, 15))
        courses = []
        
        subjects = ["Programming", "Data Science", "Web Development", "Machine Learning", "Cybersecurity"]
        levels = ["Beginner", "Intermediate", "Advanced"]
        
        for i in range(course_count):
            course = {
                "id": str(uuid.uuid4()),
                "title": f"{random.choice(subjects)} {random.choice(['Fundamentals', 'Advanced Topics', 'Practical Applications'])}",
                "description": f"Comprehensive course covering essential concepts and practical applications",
                "instructor": context.get('name', 'Demo Instructor'),
                "difficulty": random.choice(levels),
                "duration_hours": random.randint(10, 40),
                "enrollment_count": random.randint(15, 200),
                "rating": round(random.uniform(4.2, 5.0), 1),
                "completion_rate": random.randint(70, 95),
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "is_demo": True
            }
            courses.append(course)
        
        return courses
    
    def _generate_demo_students(self, user_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate realistic demo student data with progress and engagement metrics."""
        student_count = context.get('count', random.randint(20, 50))
        students = []
        
        names = [
            "Emma Rodriguez", "Liam Thompson", "Sophia Kumar", "Noah Wilson", 
            "Olivia Chen", "Ethan Martinez", "Ava Johnson", "Mason Davis"
        ]
        
        for i in range(student_count):
            student = {
                "id": str(uuid.uuid4()),
                "name": random.choice(names),
                "email": f"student{i+1}@demo.edu",
                "progress_percentage": random.randint(25, 100),
                "engagement_score": round(random.uniform(0.6, 1.0), 2),
                "last_active": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
                "assignments_completed": random.randint(5, 20),
                "quiz_average": round(random.uniform(70, 98), 1),
                "lab_hours": random.randint(10, 50),
                "is_demo": True
            }
            students.append(student)
        
        return students
    
    def _generate_demo_analytics(self, user_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive demo analytics data."""
        return {
            "overview": {
                "total_students": random.randint(150, 500),
                "active_courses": random.randint(10, 25),
                "completion_rate": round(random.uniform(78, 92), 1),
                "engagement_score": round(random.uniform(0.75, 0.95), 2)
            },
            "trends": {
                "enrollment_trend": [random.randint(10, 50) for _ in range(12)],
                "completion_trend": [random.randint(70, 95) for _ in range(12)],
                "engagement_trend": [round(random.uniform(0.7, 0.95), 2) for _ in range(12)]
            },
            "is_demo": True
        }
    
    def _generate_demo_labs(self, user_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate realistic demo lab environments."""
        lab_count = context.get('count', random.randint(5, 12))
        labs = []
        
        lab_types = ["Python Programming", "Web Development", "Data Analysis", "Machine Learning"]
        
        for i in range(lab_count):
            lab = {
                "id": str(uuid.uuid4()),
                "name": f"{random.choice(lab_types)} Lab {i+1}",
                "environment": random.choice(["Python", "JavaScript", "Jupyter", "VS Code"]),
                "status": random.choice(["available", "running", "completed"]),
                "usage_hours": random.randint(1, 10),
                "completion_rate": random.randint(65, 95),
                "is_demo": True
            }
            labs.append(lab)
        
        return labs
    
    def _generate_demo_feedback(self, user_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate realistic student feedback data."""
        feedback_count = context.get('count', random.randint(10, 30))
        feedback_items = []
        
        sample_feedback = [
            "Great course! Very comprehensive and well-structured.",
            "The labs were particularly helpful for hands-on learning.",
            "Could use more advanced examples in some sections.",
            "Excellent instructor and clear explanations.",
            "Perfect balance of theory and practical application."
        ]
        
        for i in range(feedback_count):
            feedback = {
                "id": str(uuid.uuid4()),
                "student_name": f"Student {i+1}",
                "rating": random.randint(4, 5),
                "comment": random.choice(sample_feedback),
                "sentiment": random.choice(["positive", "neutral", "positive"]),
                "date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "is_demo": True
            }
            feedback_items.append(feedback)
        
        return feedback_items