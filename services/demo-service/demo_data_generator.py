"""
Demo Data Generator - Realistic Sample Data for Platform Demonstration

Generates comprehensive, realistic data that showcases all platform
features without storing any actual user information.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker
from pydantic import BaseModel

fake = Faker()

class DemoUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    organization: str
    is_demo: bool = True

# Realistic course topics by subject area
COURSE_TOPICS = {
    "programming": [
        "Python for Data Science", "JavaScript Fundamentals", "React Development",
        "Machine Learning Basics", "Database Design", "API Development",
        "DevOps Essentials", "Cybersecurity Fundamentals", "Mobile App Development"
    ],
    "business": [
        "Digital Marketing Strategy", "Project Management", "Financial Analysis",
        "Leadership Skills", "Business Analytics", "Operations Management",
        "Entrepreneurship Basics", "Supply Chain Management"
    ],
    "design": [
        "UI/UX Design Principles", "Graphic Design Fundamentals", "Web Design",
        "Product Design", "Design Systems", "User Research Methods"
    ],
    "science": [
        "Introduction to Biology", "Chemistry Fundamentals", "Physics Concepts",
        "Environmental Science", "Statistics for Scientists", "Research Methods"
    ]
}

# Realistic student names and profiles
SAMPLE_STUDENTS = [
    {"name": "Emma Rodriguez", "performance": "excellent", "engagement": "high"},
    {"name": "Liam Chen", "performance": "good", "engagement": "medium"},
    {"name": "Sophia Patel", "performance": "excellent", "engagement": "high"},
    {"name": "Noah Johnson", "performance": "average", "engagement": "medium"},
    {"name": "Olivia Kim", "performance": "good", "engagement": "high"},
    {"name": "William Davis", "performance": "poor", "engagement": "low"},
    {"name": "Ava Thompson", "performance": "excellent", "engagement": "high"},
    {"name": "James Wilson", "performance": "average", "engagement": "low"},
    {"name": "Isabella Garcia", "performance": "good", "engagement": "medium"},
    {"name": "Benjamin Lee", "performance": "excellent", "engagement": "high"}
]

def generate_demo_courses(user_type: str, user_data: Dict, count: int = 10) -> List[Dict[str, Any]]:
    """Generate realistic course data based on user context"""
    courses = []
    
    for i in range(count):
        subject = random.choice(list(COURSE_TOPICS.keys()))
        course_title = random.choice(COURSE_TOPICS[subject])
        
        # Vary course data based on user type
        if user_type == "instructor":
            # Instructor sees their own courses with detailed metrics
            enrollment = random.randint(15, 150)
            completion_rate = random.randint(65, 95)
            rating = round(random.uniform(3.8, 4.9), 1)
        elif user_type == "student":
            # Student sees courses they can enroll in
            enrollment = random.randint(50, 500)
            completion_rate = random.randint(70, 90)
            rating = round(random.uniform(4.0, 4.8), 1)
        else:  # admin
            # Admin sees system-wide course statistics
            enrollment = random.randint(100, 1000)
            completion_rate = random.randint(60, 85)
            rating = round(random.uniform(3.5, 4.7), 1)
        
        course = {
            "id": str(uuid.uuid4()),
            "title": course_title,
            "description": f"Comprehensive {course_title.lower()} course with hands-on projects and real-world applications.",
            "subject": subject,
            "difficulty": random.choice(["Beginner", "Intermediate", "Advanced"]),
            "duration": f"{random.randint(4, 20)} hours",
            "enrollment_count": enrollment,
            "completion_rate": completion_rate,
            "rating": rating,
            "review_count": random.randint(10, 200),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "last_updated": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "instructor": {
                "name": user_data["name"] if user_type == "instructor" else fake.name(),
                "title": "Senior Instructor",
                "rating": round(random.uniform(4.2, 4.9), 1)
            },
            "modules": [
                {
                    "id": str(uuid.uuid4()),
                    "title": f"Module {j+1}: {fake.catch_phrase()}",
                    "lessons": random.randint(3, 8),
                    "duration": f"{random.randint(30, 120)} minutes",
                    "completed": random.choice([True, False]) if user_type == "student" else None
                }
                for j in range(random.randint(4, 8))
            ],
            "skills_taught": [fake.word().title() for _ in range(random.randint(3, 6))],
            "prerequisites": [fake.word().title() for _ in range(random.randint(0, 3))],
            "has_labs": random.choice([True, False]),
            "has_certificates": True,
            "price": random.choice([0, 29, 49, 99, 149]) if user_type != "instructor" else None,
            "ai_generated_content": random.randint(20, 80),  # Percentage of AI-generated content
            "demo_note": "Sample course data for demonstration purposes"
        }
        
        courses.append(course)
    
    return courses

def generate_demo_students(course_id: Optional[str] = None, instructor_context: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Generate realistic student progress data"""
    students = []
    
    # Ensure we don't sample more than available
    num_students = min(random.randint(8, 15), len(SAMPLE_STUDENTS))
    for student_data in random.sample(SAMPLE_STUDENTS, num_students):
        progress = random.randint(10, 100)
        last_active = datetime.now() - timedelta(days=random.randint(0, 14))
        
        # Performance mapping
        performance_map = {
            "excellent": {"grade": random.randint(90, 100), "engagement": "high"},
            "good": {"grade": random.randint(80, 89), "engagement": "medium"},
            "average": {"grade": random.randint(70, 79), "engagement": "medium"},
            "poor": {"grade": random.randint(50, 69), "engagement": "low"}
        }
        
        perf = performance_map[student_data["performance"]]
        
        student = {
            "id": str(uuid.uuid4()),
            "name": student_data["name"],
            "email": f"{student_data['name'].lower().replace(' ', '.')}.demo@student.edu",
            "avatar": f"https://ui-avatars.com/api/?name={student_data['name'].replace(' ', '+')}&background=random",
            "progress": progress,
            "grade": perf["grade"] if progress > 50 else None,
            "engagement_level": perf["engagement"],
            "time_spent": random.randint(5, 200),  # hours
            "last_active": last_active.isoformat(),
            "completed_lessons": random.randint(0, 25),
            "quiz_scores": [random.randint(60, 100) for _ in range(random.randint(2, 8))],
            "lab_completions": random.randint(0, 5),
            "discussion_posts": random.randint(0, 15),
            "achievements": [
                {"title": "Fast Learner", "earned": True},
                {"title": "Lab Master", "earned": random.choice([True, False])},
                {"title": "Discussion Leader", "earned": random.choice([True, False])}
            ],
            "enrollment_date": (datetime.now() - timedelta(days=random.randint(30, 180))).isoformat(),
            "completion_date": (datetime.now() + timedelta(days=random.randint(1, 60))).isoformat() if progress > 80 else None,
            "demo_note": "Synthetic student data with realistic learning patterns"
        }
        
        students.append(student)
    
    return students

def generate_demo_analytics(user_type: str, user_data: Dict, timeframe: str = "30d") -> Dict[str, Any]:
    """Generate comprehensive analytics data"""
    
    # Base metrics vary by user type and timeframe
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[timeframe]
    base_multiplier = {"7d": 1, "30d": 4, "90d": 12, "1y": 48}[timeframe]
    
    if user_type == "instructor":
        analytics = {
            "overview": {
                "total_students": random.randint(50, 300) * base_multiplier,
                "active_courses": random.randint(3, 12),
                "completion_rate": round(random.uniform(68, 85), 1),
                "average_rating": round(random.uniform(4.1, 4.8), 1),
                "total_revenue": random.randint(2000, 15000) * base_multiplier,
                "engagement_score": round(random.uniform(75, 92), 1)
            },
            "student_progress": [
                {
                    "date": (datetime.now() - timedelta(days=i)).isoformat(),
                    "new_enrollments": random.randint(2, 15),
                    "completions": random.randint(1, 8),
                    "active_students": random.randint(20, 80)
                }
                for i in range(0, days, max(1, days//20))
            ],
            "course_performance": [
                {
                    "course_name": random.choice(COURSE_TOPICS["programming"]),
                    "students": random.randint(25, 100),
                    "completion_rate": random.randint(65, 95),
                    "rating": round(random.uniform(3.8, 4.9), 1),
                    "revenue": random.randint(500, 3000)
                }
                for _ in range(5)
            ],
            "engagement_metrics": {
                "discussion_posts": random.randint(50, 200) * base_multiplier,
                "lab_submissions": random.randint(30, 150) * base_multiplier,
                "quiz_attempts": random.randint(100, 500) * base_multiplier,
                "video_watch_time": random.randint(200, 1000) * base_multiplier  # hours
            }
        }
    
    elif user_type == "student":
        analytics = {
            "learning_progress": {
                "courses_enrolled": random.randint(3, 8),
                "courses_completed": random.randint(1, 5),
                "total_study_time": random.randint(50, 200),  # hours
                "certificates_earned": random.randint(1, 4),
                "current_streak": random.randint(1, 30),  # days
                "skill_points": random.randint(500, 2000)
            },
            "weekly_activity": [
                {
                    "week": f"Week {i+1}",
                    "study_hours": round(random.uniform(2, 15), 1),
                    "lessons_completed": random.randint(1, 8),
                    "quizzes_taken": random.randint(0, 3)
                }
                for i in range(min(12, days//7))
            ],
            "skill_development": [
                {
                    "skill": skill,
                    "level": random.choice(["Beginner", "Intermediate", "Advanced"]),
                    "progress": random.randint(20, 100),
                    "courses_completed": random.randint(1, 3)
                }
                for skill in ["Python", "Data Analysis", "Web Development", "Machine Learning", "Project Management"]
            ]
        }
    
    else:  # admin
        analytics = {
            "platform_overview": {
                "total_users": random.randint(500, 5000),
                "active_instructors": random.randint(50, 300),
                "total_courses": random.randint(200, 1000),
                "platform_revenue": random.randint(50000, 500000),
                "user_satisfaction": round(random.uniform(4.2, 4.7), 1),
                "system_uptime": round(random.uniform(99.5, 99.9), 2)
            },
            "growth_metrics": [
                {
                    "month": (datetime.now() - timedelta(days=30*i)).strftime("%B %Y"),
                    "new_users": random.randint(100, 500),
                    "course_completions": random.randint(200, 800),
                    "revenue": random.randint(10000, 50000)
                }
                for i in range(12)
            ],
            "content_statistics": {
                "ai_generated_courses": random.randint(100, 400),
                "human_created_courses": random.randint(200, 600),
                "total_video_hours": random.randint(2000, 10000),
                "interactive_labs": random.randint(150, 500),
                "assessment_questions": random.randint(5000, 20000)
            }
        }
    
    analytics["timeframe"] = timeframe
    analytics["generated_at"] = datetime.now().isoformat()
    analytics["demo_note"] = "Real-time analytics simulation with trending data patterns"
    
    return analytics

def generate_demo_labs(user_type: str, course_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate interactive lab environment data"""
    
    lab_types = [
        {"name": "Python Development", "ide": "jupyter", "difficulty": "Beginner"},
        {"name": "React Components", "ide": "vscode", "difficulty": "Intermediate"},
        {"name": "Database Design", "ide": "mysql-workbench", "difficulty": "Advanced"},
        {"name": "Machine Learning", "ide": "jupyter", "difficulty": "Advanced"},
        {"name": "API Development", "ide": "postman", "difficulty": "Intermediate"}
    ]
    
    labs = []
    for i, lab_type in enumerate(random.sample(lab_types, random.randint(3, 5))):
        lab = {
            "id": str(uuid.uuid4()),
            "title": f"Lab {i+1}: {lab_type['name']}",
            "description": f"Hands-on {lab_type['name'].lower()} exercise with real-world scenarios",
            "ide_type": lab_type["ide"],
            "difficulty": lab_type["difficulty"],
            "estimated_time": random.randint(30, 120),  # minutes
            "completion_rate": random.randint(60, 95),
            "student_rating": round(random.uniform(3.8, 4.9), 1),
            "technologies": random.sample(["Python", "JavaScript", "React", "SQL", "Docker", "Git"], random.randint(2, 4)),
            "learning_objectives": [
                f"Understand {fake.word()} concepts",
                f"Implement {fake.word()} functionality", 
                f"Debug {fake.word()} issues"
            ],
            "starter_code_available": True,
            "solution_provided": random.choice([True, False]),
            "auto_grading": True,
            "container_resources": {
                "cpu": "2 cores",
                "memory": "4GB",
                "storage": "10GB",
                "network": "Enabled"
            },
            "last_updated": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
            "demo_note": "Fully functional lab environment simulation"
        }
        labs.append(lab)
    
    return labs

def generate_demo_feedback(course_id: Optional[str] = None, instructor_context: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Generate realistic student feedback and reviews"""
    
    positive_comments = [
        "Excellent course structure and clear explanations!",
        "The hands-on labs really helped me understand the concepts.",
        "Great instructor, very responsive to questions.",
        "Perfect balance of theory and practical applications.",
        "AI-generated content was surprisingly good and relevant."
    ]
    
    constructive_comments = [
        "Would benefit from more advanced examples.",
        "Some sections could use more detailed explanations.",
        "Lab instructions could be clearer in module 3.",
        "More interactive elements would be helpful.",
        "Could use more real-world case studies."
    ]
    
    feedback = []
    for i in range(random.randint(8, 20)):
        is_positive = random.choices([True, False], weights=[75, 25])[0]
        rating = random.randint(4, 5) if is_positive else random.randint(2, 4)
        
        student = random.choice(SAMPLE_STUDENTS)
        
        feedback_item = {
            "id": str(uuid.uuid4()),
            "student_name": student["name"],
            "student_avatar": f"https://ui-avatars.com/api/?name={student['name'].replace(' ', '+')}&background=random",
            "rating": rating,
            "comment": random.choice(positive_comments if is_positive else constructive_comments),
            "date": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
            "course_progress": random.randint(50, 100),
            "verified_completion": random.choice([True, False]),
            "helpful_votes": random.randint(0, 25),
            "sentiment": "positive" if is_positive else "constructive",
            "topics_mentioned": random.sample(["content", "instructor", "labs", "difficulty", "pace"], random.randint(1, 3)),
            "demo_note": "AI-analyzed feedback with sentiment scoring"
        }
        
        feedback.append(feedback_item)
    
    # Sort by date (newest first)
    feedback.sort(key=lambda x: str(x["date"]), reverse=True)
    
    return feedback