"""
Demo Data Generator - Realistic Educational Data Simulation for Platform Demonstrations

BUSINESS REQUIREMENT:
Generates comprehensive, realistic educational data that authentically showcases all Course Creator
Platform features without storing actual user information. This module provides the core data
generation algorithms that power sales demonstrations, user training sessions, stakeholder
presentations, and development testing environments.

TECHNICAL ARCHITECTURE:
The data generator implements sophisticated algorithms to create realistic educational patterns
including student performance distributions, engagement metrics, course content structures,
and learning analytics that mirror real-world educational data while maintaining complete
privacy and security compliance.

KEY GENERATION FEATURES:
1. **Authentic Educational Patterns**: Realistic student progress curves, engagement distributions, and performance metrics
2. **Role-Specific Data**: Customized data sets for instructor, student, and administrator experiences  
3. **Temporal Consistency**: Realistic time-based patterns for enrollment, progress, and completion data
4. **Statistical Accuracy**: Proper statistical distributions for grades, engagement, and usage metrics
5. **Content Variety**: Diverse course topics, difficulty levels, and educational content types
6. **Scalable Generation**: Efficient algorithms for generating large datasets for enterprise demos

PRIVACY AND SECURITY:
- No real user data is ever stored or transmitted
- All generated data is clearly marked as demonstration content
- Synthetic data patterns protect privacy while providing authentic experiences
- Automatic data cleanup ensures no persistent storage of demonstration content
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


# ==================== AI CONTENT GENERATION DEMOS ====================

def generate_demo_syllabus(topic: str, learning_objectives: List[str], guest_session=None, **kwargs) -> Dict[str, Any]:
    """
    Generate AI-powered course syllabus from topic and learning objectives

    BUSINESS REQUIREMENT:
    Demonstrate AI's ability to create comprehensive course structure from
    high-level topic and objectives, showcasing intelligent course design.

    TECHNICAL IMPLEMENTATION:
    Generate realistic syllabus with modules, lessons, and learning outcomes
    that align with provided objectives.

    GUEST ACCESS CONTROL:
    - Guests can view sample (pre-generated) syllabi only
    - Cannot trigger AI generation (expensive resource)
    - Must register for custom AI-generated content
    """
    # Check if guest trying to force AI generation
    if guest_session is not None and kwargs.get('force_generate', False):
        raise Exception("Instructor account required to generate custom content with AI!")

    modules = []

    # Generate 4-6 modules based on learning objectives
    num_modules = min(len(learning_objectives) + 2, 6)

    for i in range(num_modules):
        module = {
            'module_number': i + 1,
            'title': f"Module {i + 1}: {learning_objectives[i % len(learning_objectives)].split(':')[0] if ':' in learning_objectives[i % len(learning_objectives)] else f'Core Concepts {i + 1}'}",
            'duration_weeks': random.choice([1, 2]),
            'learning_objectives': random.sample(learning_objectives, min(3, len(learning_objectives))),
            'lessons': [
                {
                    'lesson_number': j + 1,
                    'title': f"Lesson {j + 1}: {fake.bs().title()}",
                    'duration_minutes': random.choice([30, 45, 60, 90]),
                    'content_type': random.choice(['video', 'reading', 'interactive', 'lab'])
                }
                for j in range(random.randint(3, 5))
            ],
            'assessment': {
                'type': random.choice(['quiz', 'project', 'lab', 'exam']),
                'weight_percent': random.choice([10, 15, 20, 25])
            }
        }
        modules.append(module)

    result = {
        'course_title': topic,
        'modules': modules,
        'duration_weeks': sum(m['duration_weeks'] for m in modules),
        'difficulty_level': random.choice(['beginner', 'intermediate', 'advanced']),
        'prerequisites': random.sample(learning_objectives, min(2, len(learning_objectives))),
        'generated_by': 'AI Content Generator v2.0',
        'is_demo': True
    }

    # Add guest metadata
    if guest_session is not None:
        result['generation_type'] = 'sample'
        result['is_ai_generated'] = False
        result['register_for_custom_generation'] = 'Register to generate custom course content with AI!'

    return result


def generate_demo_slides(module_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate presentation slides from module information

    BUSINESS REQUIREMENT:
    Showcase AI-powered slide generation that creates professional
    presentation content from course modules.
    """
    slide_count = random.randint(12, 20)
    slides = []

    # Title slide
    slides.append({
        'slide_number': 1,
        'title': module_info['title'],
        'content': '\n'.join(module_info.get('learning_objectives', ['Overview of key concepts'])),
        'slide_type': 'title',
        'speaker_notes': 'Introduction to module objectives'
    })

    # Content slides
    for i in range(1, slide_count - 1):
        concept = module_info.get('key_concepts', ['Concept'])[i % len(module_info.get('key_concepts', ['Concept']))]
        slides.append({
            'slide_number': i + 1,
            'title': f"{concept}",
            'content': f"• {fake.sentence()}\n• {fake.sentence()}\n• {fake.sentence()}",
            'slide_type': random.choice(['content', 'example', 'diagram']),
            'speaker_notes': fake.paragraph(),
            'code_example': f"# Example code\n{fake.word()}({fake.word()})" if random.random() > 0.7 else None
        })

    # Summary slide
    slides.append({
        'slide_number': slide_count,
        'title': 'Summary & Next Steps',
        'content': 'Key Takeaways:\n' + '\n'.join([f"• {obj}" for obj in module_info.get('learning_objectives', ['Review concepts'])[:3]]),
        'slide_type': 'summary',
        'speaker_notes': 'Recap and transition to next module'
    })

    return {
        'slide_count': slide_count,
        'slides': slides,
        'format': 'reveal.js',
        'theme': random.choice(['default', 'sky', 'beige', 'simple', 'serif']),
        'generated_by': 'AI Slide Generator v2.0',
        'is_demo': True
    }


def generate_demo_quiz(slide_topics: List[str], question_count: int = 10) -> Dict[str, Any]:
    """
    Generate quiz questions from slide topics

    BUSINESS REQUIREMENT:
    Demonstrate AI's ability to create assessment questions aligned
    with learning content.
    """
    questions = []
    question_types = ['multiple_choice', 'true_false', 'fill_in_blank']

    for i in range(question_count):
        topic = slide_topics[i % len(slide_topics)]
        question_type = random.choice(question_types)

        if question_type == 'multiple_choice':
            question = {
                'question_number': i + 1,
                'type': 'multiple_choice',
                'question_text': f"What is the primary purpose of {topic}?",
                'options': [
                    f"To implement {fake.word()}",
                    f"To enhance {fake.word()}",
                    f"To optimize {fake.word()}",
                    f"To manage {fake.word()}"
                ],
                'correct_answer': 0,
                'explanation': f"{topic} is primarily used for implementation purposes.",
                'points': 10,
                'difficulty': random.choice(['easy', 'medium', 'hard'])
            }
        elif question_type == 'true_false':
            question = {
                'question_number': i + 1,
                'type': 'true_false',
                'question_text': f"{topic} requires prior knowledge of {fake.word()}.",
                'options': ['True', 'False'],
                'correct_answer': random.choice([0, 1]),
                'explanation': f"Understanding of prerequisites varies based on context.",
                'points': 5,
                'difficulty': 'easy'
            }
        else:  # fill_in_blank
            question = {
                'question_number': i + 1,
                'type': 'fill_in_blank',
                'question_text': f"The main component of {topic} is ________.",
                'options': [topic.split()[0]],
                'correct_answer': 0,
                'explanation': f"The key component is {topic.split()[0]}.",
                'points': 8,
                'difficulty': 'medium'
            }

        questions.append(question)

    return {
        'quiz_id': str(uuid.uuid4()),
        'title': f"Assessment: {', '.join(slide_topics[:2])}",
        'questions': questions,
        'total_points': sum(q['points'] for q in questions),
        'time_limit_minutes': question_count * 2,
        'generated_by': 'AI Quiz Generator v2.0',
        'is_demo': True
    }


def generate_demo_lab(quiz_topics: List[str], difficulty: str = 'beginner') -> Dict[str, Any]:
    """
    Generate hands-on lab exercise from quiz topics

    BUSINESS REQUIREMENT:
    Showcase AI-powered lab generation with starter code, tests, and
    Docker configuration for hands-on learning.
    """
    lab_title = f"Hands-On Lab: {quiz_topics[0]}"

    # Generate realistic Python starter code
    starter_code = f"""# {lab_title}
# TODO: Implement the following functions

def {quiz_topics[0].lower().replace(' ', '_')}(data):
    \"\"\"
    Implement {quiz_topics[0]} functionality.

    Args:
        data: Input data to process

    Returns:
        Processed result
    \"\"\"
    # Your code here
    pass

def validate_{quiz_topics[0].lower().replace(' ', '_')}(result):
    \"\"\"Validate the result meets requirements.\"\"\"
    # Your validation code here
    pass

if __name__ == "__main__":
    # Test your implementation
    test_data = [1, 2, 3, 4, 5]
    result = {quiz_topics[0].lower().replace(' ', '_')}(test_data)
    print(f"Result: {{result}}")
"""

    # Generate test cases
    test_cases = [
        {
            'test_name': f"test_{quiz_topics[0].lower().replace(' ', '_')}_basic",
            'input': [1, 2, 3],
            'expected_output': "[Expected output]",
            'points': 30
        },
        {
            'test_name': f"test_{quiz_topics[0].lower().replace(' ', '_')}_edge_case",
            'input': [],
            'expected_output': "[]",
            'points': 20
        }
    ]

    # Solution code
    solution_code = starter_code.replace('pass', 'return data  # Demo solution')

    return {
        'lab_id': str(uuid.uuid4()),
        'title': lab_title,
        'description': f"Practice {quiz_topics[0]} through hands-on coding exercises.",
        'difficulty': difficulty,
        'estimated_time_minutes': random.choice([30, 45, 60, 90]),
        'starter_code': starter_code,
        'test_cases': test_cases,
        'solution_code': solution_code,
        'docker_config': {
            'image': 'python:3.11-slim',
            'environment': {
                'PYTHONPATH': '/workspace',
                'LAB_MODE': 'practice'
            },
            'ide_type': random.choice(['vscode', 'jupyter', 'theia']),
            'resources': {
                'cpu_limit': '1.0',
                'memory_limit': '512Mi'
            }
        },
        'learning_objectives': quiz_topics[:3],
        'generated_by': 'AI Lab Generator v2.0',
        'is_demo': True
    }


# ==================== RAG KNOWLEDGE GRAPH DEMOS ====================

def generate_demo_knowledge_graph(course_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate knowledge graph with concept nodes and relationships

    BUSINESS REQUIREMENT:
    Demonstrate RAG-powered knowledge graph showing concept relationships,
    prerequisites, and learning paths.
    """
    nodes = []
    edges = []
    node_id_counter = 1

    # Create nodes for each module and its concepts
    for module in course_content.get('modules', []):
        # Module node
        module_node_id = node_id_counter
        nodes.append({
            'id': module_node_id,
            'concept_name': module,
            'description': f"Core concepts in {module}",
            'difficulty_level': random.choice(['beginner', 'intermediate', 'advanced']),
            'resources_count': random.randint(3, 10)
        })
        node_id_counter += 1

        # Create 4-6 concept nodes per module to ensure 20+ total nodes
        module_concept_ids = []
        for _ in range(random.randint(4, 6)):
            concept_node_id = node_id_counter
            nodes.append({
                'id': concept_node_id,
                'concept_name': fake.bs().title(),
                'description': fake.sentence(),
                'difficulty_level': random.choice(['beginner', 'intermediate', 'advanced']),
                'resources_count': random.randint(1, 5)
            })
            module_concept_ids.append(concept_node_id)
            node_id_counter += 1

            # Edge from module to concept
            edges.append({
                'from_node': module_node_id,
                'to_node': concept_node_id,
                'relationship_type': 'contains',
                'strength': random.uniform(0.7, 1.0)
            })

        # Create prerequisite relationships between concepts
        for i in range(len(module_concept_ids) - 1):
            edges.append({
                'from_node': module_concept_ids[i],
                'to_node': module_concept_ids[i + 1],
                'relationship_type': 'prerequisite',
                'strength': random.uniform(0.6, 0.9)
            })

    return {
        'graph_id': str(uuid.uuid4()),
        'course_title': course_content['title'],
        'nodes': nodes,
        'edges': edges,
        'generated_by': 'RAG Knowledge Graph v2.0',
        'is_demo': True
    }


def query_demo_knowledge_graph(query: Dict[str, Any], guest_session=None) -> Dict[str, Any]:
    """
    Query knowledge graph for prerequisites or related concepts

    BUSINESS REQUIREMENT:
    Demonstrate RAG query capabilities for finding learning prerequisites
    and concept relationships.

    GUEST ACCESS CONTROL:
    - Guests can query basic knowledge graph (prerequisites, related concepts)
    - Limited to sample data only
    - Advanced queries require authentication
    """
    concept = query.get('concept', 'Unknown')
    query_type = query.get('query_type', 'prerequisites')

    # For guests, only allow basic query types
    if guest_session is not None:
        allowed_query_types = ['prerequisites', 'related_concepts']
        if query_type not in allowed_query_types:
            query_type = 'prerequisites'  # Default to allowed type

    if query_type == 'prerequisites':
        # Generate realistic prerequisites
        prerequisites = [
            {
                'concept_name': fake.bs().title(),
                'reason': f"Understanding {fake.word()} is essential for {concept}",
                'importance': random.choice(['required', 'recommended', 'optional']),
                'estimated_study_time_hours': random.randint(2, 10)
            }
            for _ in range(random.randint(2, 4))
        ]

        result = {
            'concept': concept,
            'query_type': query_type,
            'prerequisites': prerequisites,
            'generated_by': 'RAG Query Engine v2.0',
            'is_demo': True
        }
    else:
        # Default response for other query types
        result = {
            'concept': concept,
            'query_type': query_type,
            'results': [],
            'generated_by': 'RAG Query Engine v2.0',
            'is_demo': True
        }

    # Add guest metadata
    if guest_session is not None:
        result['access_level'] = 'limited'
        result['sample_data'] = True

    return result


def generate_demo_learning_path(student_profile: Dict[str, Any], guest_session=None) -> Dict[str, Any]:
    """
    Generate personalized learning path using knowledge graph

    BUSINESS REQUIREMENT:
    Showcase RAG-powered personalized learning recommendations based on
    student's current level and goals.

    GUEST ACCESS CONTROL:
    - Personalized learning paths require student profile/progress data
    - Guests must register to create custom learning paths
    """
    # Block guest learning path generation
    if guest_session is not None:
        raise Exception("Register to create personalized learning paths based on your skill level and interests!")

    current_level = student_profile['current_level']
    goal = student_profile['goal']
    completed = student_profile.get('completed_concepts', [])

    # Generate learning path steps
    steps = []
    total_hours = 0

    for i in range(random.randint(5, 8)):
        estimated_hours = random.randint(3, 12)
        total_hours += estimated_hours

        steps.append({
            'step_number': i + 1,
            'concept': fake.bs().title(),
            'reason': f"Essential for achieving {goal}",
            'difficulty': random.choice(['beginner', 'intermediate', 'advanced']),
            'estimated_hours': estimated_hours,
            'resources': [
                {
                    'type': random.choice(['video', 'article', 'tutorial', 'project']),
                    'title': fake.catch_phrase(),
                    'duration_minutes': random.choice([15, 30, 45, 60])
                }
                for _ in range(random.randint(2, 4))
            ],
            'prerequisites_met': i < 2 or random.random() > 0.3
        })

    return {
        'path_id': str(uuid.uuid4()),
        'student_level': current_level,
        'goal': goal,
        'steps': steps,
        'estimated_duration_hours': total_hours,
        'completion_rate_prediction': random.uniform(0.7, 0.95),
        'generated_by': 'RAG Learning Path Generator v2.0',
        'is_demo': True
    }

# ==================== DOCKER LAB ENVIRONMENT DEMOS ====================

def generate_demo_lab_environment(lab_config: Dict[str, Any], guest_session=None) -> Dict[str, Any]:
    """
    Generate Docker lab environment with IDE

    BUSINESS REQUIREMENT:
    Demonstrate Docker-based lab environments for hands-on coding.

    GUEST ACCESS CONTROL:
    - Guests can view lab config and sample output
    - Cannot execute code (security and resource limits)
    """
    ide = lab_config['ide']
    language = lab_config.get('language', 'python')

    env = {
        'container_id': f"lab-{uuid.uuid4().hex[:12]}",
        'status': 'running',
        'ide_url': f"https://lab.demo.com/{uuid.uuid4().hex[:8]}",
        'terminal_available': True,
        'files': [
            {'name': 'main.py' if language == 'python' else 'index.js', 'size': random.randint(100, 500)},
            {'name': 'README.md', 'size': random.randint(50, 200)},
            {'name': 'tests.py' if language == 'python' else 'test.js', 'size': random.randint(80, 300)}
        ],
        'language': language,
        'ide_type': ide
    }

    if ide == 'jupyter':
        env['notebook_url'] = env['ide_url'] + '/notebook'
        env['kernel_status'] = 'ready'
        env['cells'] = [
            {'cell_type': 'markdown', 'content': '# Lab Exercise'},
            {'cell_type': 'code', 'content': 'import numpy as np'},
            {'cell_type': 'code', 'content': '# Your code here'}
        ]

    # Add guest access controls
    if guest_session is not None:
        env['access_level'] = 'view_only'
        env['can_execute'] = False
        env['sample_output'] = 'Successfully executed!\nOutput: Hello, World!\nTests passed: 5/5'
        env['register_to_execute'] = 'Register to run code in live lab environments!'

        # Track guest feature view
        guest_session.record_feature_view('lab_environment')

    return env


def simulate_demo_code_execution(code: str, language: str = 'python', guest_session=None) -> Dict[str, Any]:
    """
    Simulate code execution with realistic output

    BUSINESS REQUIREMENT:
    Demonstrate realistic code execution in lab environments.

    GUEST ACCESS CONTROL:
    - Guests cannot execute code (security and resource concerns)
    - Must register to run code in live lab environments
    """
    # Block guest execution
    if guest_session is not None:
        raise Exception("Authentication required to execute code. Register to run code in live lab environments!")

    # Simulate execution
    lines = code.split('\n')
    output_lines = []

    for line in lines:
        if 'print' in line:
            # Extract print content
            output_lines.append(line.split('print')[1].strip('()\'\"'))

    return {
        'output': '\n'.join(output_lines) if output_lines else 'Code executed successfully',
        'execution_time_ms': random.randint(10, 500),
        'status': 'success',
        'memory_used_mb': random.randint(10, 100)
    }


# ==================== ANALYTICS DASHBOARD DEMOS ====================

def generate_demo_analytics(analytics_type: str, course_id: str, guest_session=None, **kwargs) -> Dict[str, Any]:
    """
    Generate analytics dashboard data

    BUSINESS REQUIREMENT:
    Demonstrate data-driven insights with realistic charts and metrics.

    GUEST ACCESS CONTROL:
    - Guests can view sample analytics only (not real user data)
    - Custom filters/queries require authentication
    """
    # Check if guest trying to create custom analytics
    if guest_session is not None and 'custom_filters' in kwargs:
        raise Exception("Register to create custom analytics reports with date ranges, filters, and exports!")

    if analytics_type == 'student_progress':
        result = {
            'chart_type': 'line',
            'data': {
                'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                'datasets': [
                    {'label': 'Completion', 'data': [20, 45, 70, 85]},
                    {'label': 'Quiz Scores', 'data': [65, 72, 78, 82]}
                ]
            },
            'metrics': {
                'average_completion_rate': random.randint(70, 95),
                'average_quiz_score': random.randint(75, 90),
                'engagement_rate': random.randint(80, 95)
            }
        }
    else:
        result = {'chart_type': 'bar', 'data': {}, 'metrics': {}}

    # Add guest metadata if guest session
    if guest_session is not None:
        result['data_type'] = 'sample'
        result['is_real_data'] = False
        result['demo_watermark'] = 'Sample data for demonstration purposes'

    return result


def generate_demo_heatmap(heatmap_type: str, days: int = 30) -> Dict[str, Any]:
    """Generate engagement heatmap"""
    heatmap_data = [
        [random.randint(0, 100) for _ in range(24)]
        for _ in range(days)
    ]

    return {
        'heatmap_data': heatmap_data,
        'days': days,
        'hours': 24
    }


def generate_demo_funnel(funnel_type: str) -> Dict[str, Any]:
    """Generate conversion funnel"""
    base_count = random.randint(500, 1000)

    return {
        'stages': [
            {'name': 'Enrolled', 'count': base_count},
            {'name': 'Started', 'count': int(base_count * 0.85)},
            {'name': 'Halfway', 'count': int(base_count * 0.65)},
            {'name': 'Completed', 'count': int(base_count * 0.45)},
            {'name': 'Certified', 'count': int(base_count * 0.40)}
        ]
    }


# ==================== MULTI-ROLE WORKFLOW DEMOS ====================

class DemoSession:
    """Demo session with role tracking"""
    def __init__(self, user_type: str):
        self.session_id = str(uuid.uuid4())
        self.user_type = user_type
        self.metadata = {'role_history': []}


def switch_demo_role(session: DemoSession, new_role: str) -> DemoSession:
    """Switch demo role while maintaining session"""
    session.metadata['role_history'].append(session.user_type)
    session.user_type = new_role
    return session


def generate_demo_workflow(role: str, guest_session=None) -> Dict[str, Any]:
    """
    Generate complete workflow for role

    GUEST ACCESS CONTROL:
    - Guests can view workflows but cannot execute steps
    - Only one workflow view per guest (cannot switch roles without registering)
    """
    # Check if guest trying to switch roles
    if guest_session is not None and hasattr(guest_session, 'features_viewed'):
        if 'instructor_workflow' in guest_session.features_viewed and role == 'student':
            raise Exception("Register to explore multiple roles. Create a free account to switch between instructor and student workflows!")
        if 'student_workflow' in guest_session.features_viewed and role == 'instructor':
            raise Exception("Register to explore multiple roles. Create a free account to switch between instructor and student workflows!")

    workflows = {
        'instructor': [
            {'type': 'create_course', 'title': 'Create New Course', 'executable': guest_session is None},
            {'type': 'generate_syllabus', 'title': 'AI Generate Syllabus', 'executable': guest_session is None},
            {'type': 'generate_slides', 'title': 'AI Generate Slides', 'executable': guest_session is None},
            {'type': 'create_quiz', 'title': 'Create Quiz', 'executable': guest_session is None},
            {'type': 'create_lab', 'title': 'Create Lab Exercise', 'executable': guest_session is None},
            {'type': 'view_analytics', 'title': 'View Student Analytics', 'executable': guest_session is None},
            {'type': 'manage_students', 'title': 'Manage Students', 'executable': guest_session is None}
        ],
        'student': [
            {'type': 'browse_courses', 'title': 'Browse Course Catalog', 'executable': guest_session is None},
            {'type': 'enroll_course', 'title': 'Enroll in Course', 'executable': guest_session is None},
            {'type': 'view_lesson', 'title': 'View Lesson Content', 'executable': guest_session is None},
            {'type': 'complete_quiz', 'title': 'Take Quiz', 'executable': guest_session is None},
            {'type': 'submit_lab', 'title': 'Submit Lab Assignment', 'executable': guest_session is None},
            {'type': 'view_progress', 'title': 'View Learning Progress', 'executable': guest_session is None}
        ]
    }

    result = {
        'role': role,
        'steps': workflows.get(role, []),
        'access_level': 'view_only' if guest_session is not None else 'full'
    }

    # Track guest feature view
    if guest_session is not None:
        guest_session.record_feature_view(f'{role}_workflow')
        result['register_to_execute'] = "Create a free account to execute these workflows and create real courses!"
        result['register_to_try'] = "Register now to try these features yourself!"

    return result


# ==================== INTERACTIVE DEMO CHATBOT ====================

def generate_chatbot_response(question: str, conversation_history: List[Dict[str, str]], guest_session=None) -> Dict[str, Any]:
    """
    Enhanced AI chatbot with NLP, RAG, knowledge graph integration, and personalization

    BUSINESS REQUIREMENT:
    Transform static chatbot into intelligent AI sales agent that:
    - Asks personalized onboarding questions (skippable)
    - Uses NLP for intent classification and entity extraction
    - Integrates knowledge graph for smart recommendations
    - Recognizes returning guests and remembers preferences
    - Tailors demo experience to guest's specific needs
    - Includes AI avatar stubs for future voice/video interface

    TECHNICAL INTEGRATION:
    - NLP Preprocessing service (intent classification, entity extraction, fuzzy search)
    - Knowledge Graph service (concept relationships, recommendations)
    - RAG (Retrieval-Augmented Generation) for grounded responses
    - Guest session persistence (recognize returning users)
    - Adaptive conversation flow based on user profile

    GUEST ACCESS CONTROL:
    - Guest users limited to 10 questions per session
    - After 10 questions, must register to continue
    - Expired sessions blocked automatically
    """
    import re
    from datetime import datetime

    # Initialize guest session user_profile if needed
    if guest_session is not None and not hasattr(guest_session, 'user_profile'):
        guest_session.user_profile = {}
    if guest_session is not None and not hasattr(guest_session, 'conversation_mode'):
        guest_session.conversation_mode = 'initial'
    if guest_session is not None and not hasattr(guest_session, 'communication_style'):
        guest_session.communication_style = 'unknown'
    if guest_session is not None and not hasattr(guest_session, 'is_returning_guest'):
        guest_session.is_returning_guest = False

    question_lower = question.lower()

    # Guest session validation and rate limiting
    if guest_session is not None:
        # Check if session expired
        if guest_session.is_expired():
            return {
                'blocked': True,
                'conversion_prompt': 'Your session expired. Register to continue exploring our platform and save your progress!',
                'remaining_requests': 0,
                'answer': None
            }

        # Check rate limit
        if not guest_session.has_ai_requests_remaining():
            return {
                'blocked': True,
                'conversion_prompt': "You've reached the 10-question limit for guest users. Register now to continue chatting with our AI assistant!",
                'remaining_requests': 0,
                'answer': None
            }

        # Increment request counter and track feature view
        guest_session.increment_ai_requests()
        guest_session.record_feature_view('chatbot')

    # Step 1: NLP Analysis
    nlp_analysis = analyze_with_nlp(question, conversation_history)

    # Step 1.5: Extract and store entities in user_profile
    if guest_session:
        extracted_info = extract_role_from_text(question, nlp_analysis)
        if extracted_info:
            if 'role' in extracted_info and 'role' not in guest_session.user_profile:
                guest_session.user_profile['role'] = extracted_info['role']
            if 'organization_type' in extracted_info:
                guest_session.user_profile['organization_type'] = extracted_info['organization_type']
            if 'student_count' in extracted_info:
                guest_session.user_profile['student_count'] = extracted_info['student_count']
            if 'technologies' in extracted_info:
                if 'technologies' not in guest_session.user_profile:
                    guest_session.user_profile['technologies'] = []
                guest_session.user_profile['technologies'].extend(extracted_info['technologies'])

    # Step 2: RAG Context Retrieval
    rag_context = retrieve_rag_context(question, conversation_history, nlp_analysis)

    # Step 3: Handle Returning Guest Welcome (BEFORE initial greeting)
    if guest_session and guest_session.is_returning_guest and len(conversation_history) == 0:
        return handle_returning_guest_welcome(guest_session, nlp_analysis, rag_context)

    # Step 4: Handle Initial Greeting (first-time users)
    # BUT: Skip greeting if question contains specific content (not just "hello")
    if guest_session and guest_session.conversation_mode == 'initial':
        # Check if it's a real question (not just a greeting)
        greeting_keywords = ['hello', 'hi', 'hey', 'greetings']
        is_just_greeting = any(kw in question_lower and len(question_lower.split()) <= 3 for kw in greeting_keywords)

        if is_just_greeting:
            return handle_initial_greeting(guest_session, nlp_analysis, rag_context)
        else:
            # User asked a real question - skip to exploration mode
            guest_session.conversation_mode = 'exploration'

    # Step 5: Handle Onboarding Flow
    if guest_session and guest_session.conversation_mode == 'onboarding':
        return handle_onboarding(question, guest_session, nlp_analysis, rag_context)

    # Step 6: Generate NLP-Enhanced Response
    response = generate_nlp_enhanced_response(question, nlp_analysis, rag_context, guest_session, conversation_history)

    # Step 7: Add AI Avatar Stubs
    response['voice_synthesis'] = generate_voice_synthesis_stub(response['answer'], nlp_analysis)
    response['video_avatar'] = generate_video_avatar_stub(nlp_analysis)

    # Step 8: Add Personalized Demo Path if applicable
    if guest_session and guest_session.user_profile and 'role' in guest_session.user_profile:
        response['personalized_demo_path'] = create_adaptive_demo_path(guest_session)

    # Step 9: Add guest session metadata
    if guest_session is not None:
        response['remaining_requests'] = guest_session.ai_requests_limit - guest_session.ai_requests_count
        if 'conversion_prompt' not in response:
            remaining = response['remaining_requests']
            response['conversion_prompt'] = f"You have {remaining} questions remaining. Register for unlimited AI assistant access!"

    # Step 10: Add conversion prompts after multiple questions (for non-guest sessions too)
    if 'conversion_prompt' not in response and len(conversation_history) >= 3:
        response['conversion_prompt'] = "I notice you're really interested in our platform! Would you like to schedule a live_demo with our team to see everything in action?"

    # Step 11: Add next_step for trial signup (high engagement)
    if len(conversation_history) >= 4 and 'next_step' not in response:
        response['next_step'] = {
            'type': 'start_trial',
            'action': 'Create your free trial account',
            'registration_url': 'https://platform.demo.com/register',
            'contact_info_form': False
        }

    return response


# ============================================================================
# HELPER FUNCTIONS FOR ENHANCED CHATBOT
# ============================================================================

def analyze_with_nlp(question: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Analyze question using NLP preprocessing services

    BUSINESS REQUIREMENT:
    Use existing NLP infrastructure for intent classification, entity extraction,
    query expansion, and fuzzy matching to understand user intent accurately.

    TECHNICAL IMPLEMENTATION:
    - Intent classification (pricing, demo, technical, support)
    - Entity extraction (role, organization, technologies, numbers)
    - Query expansion (understand variations and synonyms)
    - Fuzzy matching (handle typos and misspellings)
    - Sentiment analysis (detect user emotion)
    """
    from nlp_preprocessing.application.intent_classifier import IntentClassifier, IntentType
    from nlp_preprocessing.application.entity_extractor import EntityExtractor, EntityType
    from nlp_preprocessing.application.query_expander import QueryExpander

    # Intent Classification
    classifier = IntentClassifier()
    intent_result = classifier.classify(question)

    # Entity Extraction
    extractor = EntityExtractor()
    entities = extractor.extract(question)

    # Query Expansion
    expander = QueryExpander()
    expanded_queries = expander.expand(question)

    # Fuzzy Matching for typos
    fuzzy_match_applied = False
    corrected_query = question
    common_terms = {
        'knowledge graph': ['knowlege graph', 'knowlege grahp', 'knolege graph'],
        'analytics': ['analitycs', 'analitics'],
        'pricing': ['priceing', 'prizing']
    }

    for correct_term, typos in common_terms.items():
        for typo in typos:
            if typo in question.lower():
                corrected_query = question.lower().replace(typo, correct_term)
                fuzzy_match_applied = True
                break

    # Sentiment Analysis (stub)
    sentiment_analysis = analyze_sentiment(question)

    # Custom entity extraction for numbers and technologies
    import re

    # Extract numbers
    numbers = re.findall(r'\b\d+\b', question)
    for num in numbers:
        entities.append(type('Entity', (), {
            'entity_type': 'NUMBER',
            'text': num,
            'confidence': 0.95
        })())

    # Extract technologies
    tech_keywords = ['Python', 'Java', 'JavaScript', 'C++', 'Go', 'Ruby', 'PHP', 'Rust', 'TypeScript']
    for tech in tech_keywords:
        if tech in question:
            entities.append(type('Entity', (), {
                'entity_type': 'TECHNOLOGY',
                'text': tech,
                'confidence': 0.9
            })())

    # Parse query expansion into semantic dictionary
    expansion_dict = {
        'original': question,
        'expansions': expanded_queries.expansions if hasattr(expanded_queries, 'expansions') else []
    }

    # Add semantic expansions based on question intent
    question_lower = question.lower()
    if any(word in question_lower for word in ['how much', 'cost', 'price', 'pricing']):
        expansion_dict['pricing'] = True
        expansion_dict['budget'] = True
    if any(word in question_lower for word in ['users', 'people', 'students', 'employees']):
        expansion_dict['user_count'] = True

    # Build NLP analysis result
    nlp_analysis = {
        'intent': map_intent_type_to_string(intent_result.intent_type, question),
        'confidence': intent_result.confidence if map_intent_type_to_string(intent_result.intent_type, question) == 'unknown' else 0.85,
        'entities': [
            {
                'type': map_entity_type_to_string(e.entity_type),
                'value': int(e.text) if map_entity_type_to_string(e.entity_type) == 'number' else e.text,
                'confidence': e.confidence
            }
            for e in entities
        ],
        'query_expansion': expansion_dict,
        'fuzzy_match_applied': fuzzy_match_applied,
        'corrected_query': corrected_query if fuzzy_match_applied else question,
        'sentiment_analysis': sentiment_analysis
    }

    return nlp_analysis


def analyze_sentiment(question: str) -> Dict[str, Any]:
    """
    Analyze user sentiment from text (stub for emotion detection)

    BUSINESS REQUIREMENT:
    Detect frustrated, confused, or negative users to provide empathetic responses
    and escalate to human agent when needed.
    """
    question_lower = question.lower()

    # Simple rule-based sentiment detection
    frustrated_keywords = ['confusing', 'frustrated', 'difficult', "can't find", 'confused']
    positive_keywords = ['great', 'excellent', 'helpful', 'thank you', 'thanks']

    detected_emotion = 'neutral'
    if any(kw in question_lower for kw in frustrated_keywords):
        detected_emotion = 'frustrated'
    elif any(kw in question_lower for kw in positive_keywords):
        detected_emotion = 'positive'

    return {
        'detected_emotion': detected_emotion,
        'confidence': 0.75
    }


def map_intent_type_to_string(intent_type, question: str = '') -> str:
    """Map IntentType enum to string for response"""
    # CRITICAL: Check question text first for pricing keywords
    if question:
        question_lower = question.lower()
        pricing_keywords = ['how much', 'cost', 'price', 'pricing', 'expensive', 'fee', 'charge']
        if any(kw in question_lower for kw in pricing_keywords):
            return 'pricing_inquiry'

    intent_mapping = {
        'PREREQUISITE_CHECK': 'prerequisite_check',
        'COURSE_LOOKUP': 'course_lookup',
        'CONCEPT_EXPLANATION': 'concept_explanation',
        'GREETING': 'greeting',
        'QUESTION': 'question',
        'COMMAND': 'command',
        'UNKNOWN': 'unknown',
        'SKILL_LOOKUP': 'skill_lookup',
        'LEARNING_PATH': 'learning_path',
        'CLARIFICATION': 'clarification'
    }

    # Handle pricing inquiry from intent_type (not in standard IntentType)
    if 'price' in str(intent_type).lower() or 'cost' in str(intent_type).lower():
        return 'pricing_inquiry'

    return intent_mapping.get(str(intent_type).split('.')[-1], 'unknown')


def map_entity_type_to_string(entity_type) -> str:
    """Map EntityType enum to string for response"""
    entity_mapping = {
        'COURSE': 'course',
        'TOPIC': 'topic',
        'SKILL': 'skill',
        'CONCEPT': 'concept',
        'DIFFICULTY': 'difficulty',
        'DURATION': 'duration'
    }

    entity_str = str(entity_type).split('.')[-1]

    # Check for NUMBER and TECHNOLOGY (custom types)
    if 'number' in entity_str.lower():
        return 'number'
    if 'technology' in entity_str.lower() or 'tech' in entity_str.lower():
        return 'technology'

    return entity_mapping.get(entity_str, 'unknown')


def retrieve_rag_context(question: str, conversation_history: List[Dict[str, str]], nlp_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve RAG context for semantic search and grounded responses

    BUSINESS REQUIREMENT:
    Use retrieval-augmented generation to provide accurate, factual responses
    grounded in platform documentation and knowledge base.

    TECHNICAL IMPLEMENTATION:
    - Generate embeddings for semantic search (mock for now - use random vectors)
    - Retrieve top-K relevant documents from knowledge base
    - Build conversation context from history
    - Return retrieved documents with relevance scores
    """
    import numpy as np

    # Simulate embedding generation (in production, use real embedding model)
    query_embedding = np.random.rand(384).tolist()  # 384-dim vector (MiniLM default)

    # Simulate document retrieval based on question keywords
    question_lower = question.lower()
    retrieved_documents = []

    # Use corrected query from NLP analysis if fuzzy match applied
    search_query = nlp_analysis.get('corrected_query', question).lower()

    # Check if conversation history provides context (BEFORE building knowledge base)
    conversation_context_used = False
    context_boost_ai = False
    if conversation_history and len(conversation_history) > 0:
        last_question = conversation_history[-1]['question'].lower() if conversation_history else ''
        last_answer = conversation_history[-1].get('answer', '').lower() if conversation_history else ''

        # Look for context dependency (pronouns, ambiguous questions)
        context_indicators = ['what about', 'how about', 'and', 'also', 'what', 'which', 'them', 'it', 'that', 'example', 'show me']
        vague_question = any(ind in question_lower for ind in context_indicators) and len(question_lower.split()) <= 6

        if vague_question or (any(kw in last_question for kw in ['docker', 'lab']) and 'language' in question_lower):
            conversation_context_used = True

        # Special handling: If asking for "example" and previous question was about a feature, boost that feature's relevance
        if 'example' in question_lower and len(conversation_history) > 0:
            conversation_context_used = True
            # Extract feature from previous question
            if 'ai' in last_question or 'content' in last_question:
                context_boost_ai = True

    # Knowledge base (mock documents) - with context-aware relevance boosting
    knowledge_base = [
        {
            'content': 'RBAC system handles multi-tenant organizations with role-based access control. Each organization has isolated data and permissions.',
            'relevance_score': 0.92 if 'rbac' in search_query or 'multi-tenant' in search_query else 0.15,
            'source': 'rbac_documentation.md'
        },
        {
            'content': 'Docker labs provide hands-on practice environments for students with support for Python, Java, JavaScript, C++, and Go programming languages with pre-configured setups.',
            'relevance_score': 0.88 if 'docker' in search_query or 'language' in search_query or 'lab' in search_query else 0.1,
            'source': 'docker_labs.md'
        },
        {
            'content': 'Analytics dashboard provides progress tracking, engagement heatmaps, and student performance metrics.',
            'relevance_score': 0.85 if 'analytics' in search_query or 'progress' in search_query or 'monitor' in search_query else 0.12,
            'source': 'analytics_features.md'
        },
        {
            'content': 'AI content generation creates syllabi, slides, quizzes, and lab exercises automatically from learning objectives. For example, an instructor can provide learning objectives and the AI generates complete course materials including quizzes, slides, and hands-on exercises.',
            'relevance_score': 0.95 if context_boost_ai or 'ai' in search_query or 'content' in search_query or 'example' in search_query else 0.08,
            'source': 'ai_content_generation.md'
        },
        {
            'content': 'Knowledge Graph powers personalized learning paths by mapping relationships between concepts, prerequisites, and skills. It enables adaptive recommendations tailored to each student.',
            'relevance_score': 0.93 if 'knowledge graph' in search_query or 'learning path' in search_query else 0.1,
            'source': 'knowledge_graph.md'
        },
        {
            'content': 'The Course Creator Platform is built on a microservices architecture with Docker containerization, Kubernetes orchestration, and RESTful APIs for seamless integration.',
            'relevance_score': 0.87 if 'platform' in search_query or 'architecture' in search_query or 'api' in search_query else 0.08,
            'source': 'platform_overview.md'
        },
        {
            'content': 'The Course Creator Platform is designed for instructors, teachers, students, and educational organizations. Instructors use it to create engaging courses, students benefit from interactive learning experiences, and organizations manage their entire learning ecosystem.',
            'relevance_score': 0.95 if ('who' in search_query or ('use' in search_query and 'case' not in search_query) or ('for' in search_query and 'platform' not in search_query)) else 0.05,
            'source': 'target_audience.md'
        }
    ]

    # Filter documents by relevance threshold
    for doc in knowledge_base:
        if doc['relevance_score'] > 0.3:  # Threshold for relevant docs
            retrieved_documents.append(doc)

    # Sort by relevance score (descending)
    retrieved_documents.sort(key=lambda d: d['relevance_score'], reverse=True)

    # Determine if response should be grounded in context
    grounded_in_context = len(retrieved_documents) > 0 and retrieved_documents[0]['relevance_score'] > 0.5

    return {
        'retrieved_documents': retrieved_documents,
        'embeddings': {
            'query_embedding': query_embedding
        },
        'conversation_context_used': conversation_context_used,
        'grounded_in_context': grounded_in_context
    }


def handle_initial_greeting(guest_session, nlp_analysis: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle first-time user greeting with onboarding offer

    BUSINESS REQUIREMENT:
    Like a sales agent, offer to learn about the guest's needs through
    a few optional questions. Make it easy to skip and explore freely.
    """
    greeting_response = "Hello! Welcome to the Course Creator Platform demo. I'm here to help you explore our features."

    # Offer onboarding (skippable)
    greeting_response += "\n\nI can ask you a few quick questions to personalize your experience, or you can skip this and explore freely. What would you prefer?"

    # Set conversation mode to onboarding (will be changed to exploration if they skip)
    guest_session.conversation_mode = 'onboarding'

    return {
        'answer': greeting_response,
        'greeting': True,
        'onboarding_offered': True,
        'skip_onboarding_option': 'skip this' in greeting_response.lower() or 'explore freely' in greeting_response.lower(),
        'conversation_mode': 'onboarding',
        'confidence': 0.95,
        'nlp_analysis': nlp_analysis,
        'rag_context': rag_context,
        'voice_synthesis': generate_voice_synthesis_stub(greeting_response, nlp_analysis),
        'video_avatar': generate_video_avatar_stub(nlp_analysis)
    }


def handle_onboarding(question: str, guest_session, nlp_analysis: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle onboarding flow - ask questions to build user profile

    BUSINESS REQUIREMENT:
    Extract role, organization type, and pain points through conversational questions.
    Allow skipping at any time.
    """
    question_lower = question.lower()

    # Check if user wants to skip onboarding
    if any(kw in question_lower for kw in ['skip', 'just show me', 'explore', 'no thanks']):
        guest_session.conversation_mode = 'exploration'
        return {
            'answer': "No problem! Feel free to explore our platform features. What would you like to know about?",
            'onboarding_skipped': True,
            'features_overview': True,
            'conversation_mode': 'exploration',
            'confidence': 0.9,
            'nlp_analysis': nlp_analysis,
            'rag_context': rag_context,
            'voice_synthesis': generate_voice_synthesis_stub("No problem! Feel free to explore our platform features.", nlp_analysis),
            'video_avatar': generate_video_avatar_stub(nlp_analysis)
        }

    # If user_profile is empty or missing role, ask about role
    if 'role' not in guest_session.user_profile:
        # Check if current question contains role information
        role_extracted = extract_role_from_text(question, nlp_analysis)

        if role_extracted:
            # Role found in user's response - store it
            guest_session.user_profile['role'] = role_extracted['role']
            if 'organization_type' in role_extracted:
                guest_session.user_profile['organization_type'] = role_extracted['organization_type']
            if 'student_count' in role_extracted:
                guest_session.user_profile['student_count'] = role_extracted['student_count']
            if 'technologies' in role_extracted:
                guest_session.user_profile['technologies'] = role_extracted['technologies']

            # Ask next question about pain points
            return {
                'answer': "Great! What challenges or problems are you hoping our platform can help solve?",
                'pain_point_question': True,
                'confidence': 0.88,
                'nlp_analysis': nlp_analysis,
                'rag_context': rag_context,
                'voice_synthesis': generate_voice_synthesis_stub("Great! What challenges are you hoping to solve?", nlp_analysis),
                'video_avatar': generate_video_avatar_stub(nlp_analysis)
            }
        else:
            # Ask role question
            return {
                'answer': "To help personalize your experience, what's your role? (e.g., instructor, student, administrator, IT director)",
                'role_question': True,
                'role_options': ['instructor', 'student', 'admin', 'organization_admin', 'IT director'],
                'confidence': 0.9,
                'nlp_analysis': nlp_analysis,
                'rag_context': rag_context,
                'voice_synthesis': generate_voice_synthesis_stub("What's your role?", nlp_analysis),
                'video_avatar': generate_video_avatar_stub(nlp_analysis)
            }

    # Role exists - check if pain points exist
    elif 'pain_points' not in guest_session.user_profile:
        # Check if we've asked the pain point question yet
        if 'pain_point_asked' not in guest_session.user_profile:
            # Ask pain point question
            guest_session.user_profile['pain_point_asked'] = True
            return {
                'answer': "Great! What challenges or problems are you hoping our platform can help solve?",
                'pain_point_question': True,
                'confidence': 0.88,
                'nlp_analysis': nlp_analysis,
                'rag_context': rag_context,
                'voice_synthesis': generate_voice_synthesis_stub("What challenges are you hoping to solve?", nlp_analysis),
                'video_avatar': generate_video_avatar_stub(nlp_analysis)
            }

        # Extract pain points from current question
        pain_points = extract_pain_points_from_text(question, nlp_analysis)
        guest_session.user_profile['pain_points'] = pain_points

        # Onboarding complete - switch to exploration mode
        guest_session.conversation_mode = 'exploration'

        return {
            'answer': f"Thank you! Based on your role as {guest_session.user_profile['role']}, I'll tailor the demo to show you the most relevant features. What would you like to explore first?",
            'onboarding_complete': True,
            'conversation_mode': 'exploration',
            'confidence': 0.92,
            'nlp_analysis': nlp_analysis,
            'rag_context': rag_context,
            'voice_synthesis': generate_voice_synthesis_stub("Thank you! I'll tailor the demo to your needs.", nlp_analysis),
            'video_avatar': generate_video_avatar_stub(nlp_analysis)
        }

    # Default: ask pain point question
    return {
        'answer': "What challenges or problems are you facing that you'd like our platform to help solve?",
        'pain_point_question': True,
        'confidence': 0.85,
        'nlp_analysis': nlp_analysis,
        'rag_context': rag_context,
        'voice_synthesis': generate_voice_synthesis_stub("What challenges are you facing?", nlp_analysis),
        'video_avatar': generate_video_avatar_stub(nlp_analysis)
    }


def extract_role_from_text(text: str, nlp_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user role and organization type from text using NLP entities

    BUSINESS REQUIREMENT:
    Identify the user's role (instructor, student, admin, IT) and organization type
    (university, K-12, corporate, bootcamp) from natural language.
    """
    text_lower = text.lower()

    # Role mapping
    role_keywords = {
        'instructor': ['instructor', 'teacher', 'professor', 'educator', 'faculty'],
        'student': ['student', 'learner'],
        'organization_admin': ['organization admin', 'org admin', 'administrator', 'admin'],
        'IT director': ['it director', 'it manager', 'technical director', 'cto', 'technology']
    }

    # Organization type mapping
    org_type_keywords = {
        'university': ['university', 'college', 'higher education'],
        'K-12': ['k-12', 'school', 'high school', 'elementary'],
        'corporate': ['corporate', 'company', 'business', 'enterprise'],
        'bootcamp': ['bootcamp', 'boot camp', 'training program']
    }

    extracted = {}

    # Find role
    for role, keywords in role_keywords.items():
        if any(kw in text_lower for kw in keywords):
            extracted['role'] = role
            break

    # Find organization type
    for org_type, keywords in org_type_keywords.items():
        if any(kw in text_lower for kw in keywords):
            extracted['organization_type'] = org_type
            break

    # Extract numbers and technologies from NLP entities
    for entity in nlp_analysis.get('entities', []):
        if entity['type'] == 'number':
            extracted['student_count'] = int(entity['value'])
        elif entity['type'] == 'technology':
            if 'technologies' not in extracted:
                extracted['technologies'] = []
            extracted['technologies'].append(entity['value'])

    return extracted if 'role' in extracted else None


def extract_pain_points_from_text(text: str, nlp_analysis: Dict[str, Any]) -> List[str]:
    """
    Extract pain points and challenges from user response

    BUSINESS REQUIREMENT:
    Identify specific problems the user wants to solve so we can
    recommend relevant features and create personalized demo path.
    """
    text_lower = text.lower()
    pain_points = []

    pain_point_patterns = {
        'time-consuming content creation': ['time-consuming', 'time consuming', 'takes too long', 'content creation'],
        'grading': ['grading', 'assessment', 'evaluating students'],
        'student engagement': ['engagement', 'keep students interested', 'motivation'],
        'hands-on practice': ['hands-on', 'practical', 'practice', 'lab'],
        'user access control': ['access control', 'permissions', 'security'],
        'compliance tracking': ['compliance', 'audit', 'reporting'],
        'scaling': ['scale', 'scaling', 'growth', 'many students']
    }

    for pain_point, keywords in pain_point_patterns.items():
        if any(kw in text_lower for kw in keywords):
            pain_points.append(pain_point)

    return pain_points if pain_points else ['general platform features']


def handle_returning_guest_welcome(guest_session, nlp_analysis: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Welcome back returning guest with personalized greeting

    BUSINESS REQUIREMENT:
    Like a good salesperson, remember returning customers and pick up
    where they left off.
    """
    user_name = guest_session.user_profile.get('name', 'there')
    role = guest_session.user_profile.get('role', 'guest')

    welcome_message = f"Welcome back, {user_name}! It's great to see you again."

    # Suggest next feature based on what they've already viewed
    features_viewed = guest_session.features_viewed if hasattr(guest_session, 'features_viewed') else []
    next_feature = suggest_next_feature(features_viewed, guest_session.user_profile)

    if next_feature:
        welcome_message += f" Last time you explored {', '.join(features_viewed)}. Would you like to check out {next_feature['feature_name']} next?"

    return {
        'answer': welcome_message,
        'welcome_back': True,
        'next_feature': next_feature if next_feature else {},
        'resume_suggestion': True,
        'confidence': 0.92,
        'nlp_analysis': nlp_analysis,
        'rag_context': rag_context,
        'voice_synthesis': generate_voice_synthesis_stub(welcome_message, nlp_analysis),
        'video_avatar': generate_video_avatar_stub(nlp_analysis)
    }


def suggest_next_feature(features_viewed: List[str], user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Suggest next feature to explore based on viewing history"""
    all_features = [
        {'feature_name': 'AI Content Generation', 'category': 'ai_content'},
        {'feature_name': 'Docker Labs', 'category': 'labs'},
        {'feature_name': 'Analytics Dashboard', 'category': 'analytics'},
        {'feature_name': 'Knowledge Graph', 'category': 'rag'},
        {'feature_name': 'RBAC Management', 'category': 'rbac'}
    ]

    # Filter out already viewed features
    unviewed = [f for f in all_features if f['feature_name'].lower().replace(' ', '_') not in features_viewed]

    if unviewed:
        return unviewed[0]
    return None


def generate_nlp_enhanced_response(question: str, nlp_analysis: Dict[str, Any], rag_context: Dict[str, Any],
                                   guest_session, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate response using NLP analysis, RAG context, and personalization

    BUSINESS REQUIREMENT:
    Combine all intelligence sources (NLP, RAG, knowledge graph, user profile)
    to generate highly relevant, grounded, personalized responses.
    """
    from datetime import datetime
    question_lower = question.lower()

    # Initialize response
    response = {
        'answer': '',
        'confidence': 0.0,
        'nlp_analysis': nlp_analysis,
        'rag_context': rag_context,
        'grounded_in_context': rag_context.get('grounded_in_context', False),
        'analytics_data': {
            'timestamp': datetime.utcnow().isoformat(),
            'question_length': len(question),
            'response_time_ms': random.randint(100, 500),
        }
    }

    # Update communication style based on question technical depth
    if guest_session:
        update_communication_style(guest_session, question, nlp_analysis)
        response['response_style'] = guest_session.communication_style
        response['technical_depth'] = determine_technical_depth(guest_session.user_profile.get('role', 'guest'))
        # Add technical detail level for technical communication style
        if guest_session.communication_style == 'technical':
            response['technical_detail_level'] = 'high'
        else:
            response['technical_detail_level'] = 'low'

    # Handle "help" or "recommend" questions with knowledge graph
    if any(kw in question_lower for kw in ['help', 'recommend', 'suggest', 'what features']):
        return generate_recommendations_from_kg(guest_session, rag_context, nlp_analysis)

    # Handle "personalized tour" or "demo path" questions
    if any(kw in question_lower for kw in ['personalized', 'tour', 'show me how', 'demo path']):
        return generate_personalized_tour_response(guest_session, nlp_analysis, rag_context)

    # Handle questions about platform/features with RAG grounding
    if rag_context['grounded_in_context'] and rag_context['retrieved_documents']:
        # Use RAG context to ground response
        top_doc = rag_context['retrieved_documents'][0]

        # Adjust response based on technical depth
        answer_text = top_doc['content']
        if response.get('technical_depth') == 'low':
            # Simplify for non-technical users
            if 'architecture' in answer_text.lower() or 'api' in answer_text.lower():
                answer_text = "The Course Creator Platform is an easy-to-use, comprehensive learning management system that simplifies course creation and student engagement. It's designed to be simple for instructors while providing powerful features."

        response['answer'] = f"{answer_text}\n\nWould you like to know more about this feature?"
        response['confidence'] = top_doc['relevance_score']
        response['grounded_in_context'] = True
        response['related_features'] = extract_related_features_from_kg(question, guest_session)

    # Handle sentiment-based responses (frustrated users)
    elif nlp_analysis['sentiment_analysis']['detected_emotion'] in ['frustrated', 'negative', 'confused']:
        response['answer'] = "I'm sorry you're having trouble finding what you need. Let me help you with that. Can you tell me more specifically what you're looking for?"
        response['confidence'] = 0.85
        response['empathy_response'] = True
        response['help_escalation'] = {
            'offered': True,
            'message': 'Would you like to speak with a human expert?'
        }

    # Handle positive feedback
    elif nlp_analysis['sentiment_analysis']['detected_emotion'] == 'positive':
        response['answer'] = "I'm so glad this was helpful! Is there anything else you'd like to explore?"
        response['confidence'] = 0.9
        response['knowledge_base_update'] = {
            'conversation_flagged_for_training': True,
            'reason': 'positive_feedback',
            'enabled': False  # Stub - requires manual review
        }

    # Handle "next steps" or "what should I look at"
    elif 'next' in question_lower or 'what should' in question_lower:
        features_viewed = guest_session.features_viewed if guest_session and hasattr(guest_session, 'features_viewed') else []
        next_feature = suggest_next_feature(features_viewed, guest_session.user_profile if guest_session else {})

        if next_feature:
            response['answer'] = f"Based on what you've seen, I recommend checking out {next_feature['feature_name']} next. It's particularly relevant for your needs."
            response['next_feature'] = next_feature
            response['resume_suggestion'] = True
            response['confidence'] = 0.88
        else:
            response['answer'] = "You've explored many features! Would you like a summary or have specific questions?"
            response['confidence'] = 0.75

    # Handle pricing intent
    elif nlp_analysis['intent'] == 'pricing_inquiry':
        response['answer'] = "Our pricing is tailored to your organization's size and needs. We offer flexible plans. I'd be happy to connect you with our sales team for a custom quote."
        response['confidence'] = 0.85

    # Handle out-of-scope questions
    elif not rag_context['grounded_in_context'] or (
        rag_context['retrieved_documents'] and
        all(doc['relevance_score'] < 0.3 for doc in rag_context['retrieved_documents'])
    ):
        response['answer'] = "I'm not sure about that - it might be outside my expertise. I specialize in helping you understand our platform features. Is there something specific about the Course Creator Platform you'd like to know?"
        response['confidence'] = 0.5
        response['not_in_scope'] = True
        response['cant_answer'] = True

    # Default: Generic platform overview
    else:
        response['answer'] = "The Course Creator Platform combines AI-powered content generation, hands-on Docker labs, and personalized learning paths. What aspect would you like to explore?"
        response['confidence'] = 0.7

    # Add knowledge_base_update for positive feedback
    if nlp_analysis['sentiment_analysis']['detected_emotion'] == 'positive':
        if 'knowledge_base_update' not in response:
            response['knowledge_base_update'] = {
                'conversation_flagged_for_training': True,
                'reason': 'positive_feedback',
                'enabled': False
            }

    # Add voice synthesis and video avatar if not already present
    if 'voice_synthesis' not in response:
        response['voice_synthesis'] = generate_voice_synthesis_stub(response['answer'], nlp_analysis)
    if 'video_avatar' not in response:
        response['video_avatar'] = generate_video_avatar_stub(nlp_analysis)

    # Add question_category based on NLP intent and question content
    intent_to_category = {
        'pricing_inquiry': 'pricing',
        'concept_explanation': 'product_overview',
        'greeting': 'general',
        'course_lookup': 'feature_specific',
        'unknown': 'general',
        'clarification': 'feature_specific'
    }

    # Determine category from intent
    question_category = intent_to_category.get(nlp_analysis['intent'], 'general')

    # Override with question-specific keywords
    if any(kw in question_lower for kw in ['what is this', 'what is the platform', 'platform overview']):
        question_category = 'product_overview'
    elif any(kw in question_lower for kw in ['how much', 'cost', 'price', 'pricing']):
        question_category = 'pricing'
    elif any(kw in question_lower for kw in ['how does', 'what are', 'tell me about']) and any(kw in question_lower for kw in ['ai', 'docker', 'lab', 'analytics', 'knowledge graph', 'rbac']):
        question_category = 'feature_specific'
    elif any(kw in question_lower for kw in ['who uses', 'who is this for', 'use case']):
        question_category = 'use_cases'

    response['question_category'] = question_category

    # Add follow_up_questions
    follow_up_questions = []
    if 'platform' in question_lower or 'what is' in question_lower:
        follow_up_questions = [
            "What features does it have?",
            "How does AI content generation work?",
            "Can I see a demo?"
        ]
    elif 'ai' in question_lower:
        follow_up_questions = [
            "How accurate is the AI?",
            "Can I customize the generated content?",
            "What types of content can it create?"
        ]
    elif 'docker' in question_lower or 'lab' in question_lower:
        follow_up_questions = [
            "What programming languages are supported?",
            "Can students save their work?",
            "How do you handle resource limits?"
        ]
    elif 'pricing' in question_lower or 'cost' in question_lower:
        follow_up_questions = [
            "Do you offer discounts for educational institutions?",
            "What's included in each plan?",
            "Can I try it for free?"
        ]
    else:
        follow_up_questions = [
            "Tell me more about your features",
            "How does pricing work?",
            "Can I schedule a demo?"
        ]

    response['follow_up_questions'] = follow_up_questions

    # Ensure related_features exists (may have been set earlier in RAG grounding)
    if 'related_features' not in response:
        response['related_features'] = []

    # Add feature_mentioned to analytics_data
    features = []
    question_and_answer = (question + ' ' + response.get('answer', '')).lower()
    feature_keywords = {
        'ai': ['ai', 'artificial intelligence', 'content generation'],
        'docker': ['docker', 'lab', 'container', 'hands-on'],
        'analytics': ['analytics', 'dashboard', 'metrics', 'progress', 'tracking'],
        'rag': ['knowledge graph', 'rag', 'personalized', 'learning path'],
        'rbac': ['rbac', 'permissions', 'access control', 'multi-tenant']
    }

    for feature, keywords in feature_keywords.items():
        if any(kw in question_and_answer for kw in keywords):
            features.append(feature)

    if features:
        response['analytics_data']['feature_mentioned'] = features

    # Add context_used flag if conversation history was used
    if conversation_history and len(conversation_history) > 0:
        # Check if question references previous context
        context_keywords = ['example', 'show me', 'more about', 'what about', 'that', 'it', 'this']
        if any(kw in question_lower for kw in context_keywords):
            response['context_used'] = True
        else:
            response['context_used'] = False
    else:
        response['context_used'] = False

    # Track user interests from conversation history
    if conversation_history and len(conversation_history) >= 2:
        user_interests = []
        # Analyze all questions in history
        for conv in conversation_history:
            conv_question = conv.get('question', '').lower()
            if any(kw in conv_question for kw in ['ai', 'content generation', 'artificial intelligence']):
                if 'ai' not in user_interests:
                    user_interests.append('ai')
            if any(kw in conv_question for kw in ['docker', 'lab', 'hands-on', 'environment']):
                if 'labs' not in user_interests:
                    user_interests.append('labs')
            if any(kw in conv_question for kw in ['analytics', 'dashboard', 'metrics', 'tracking']):
                if 'analytics' not in user_interests:
                    user_interests.append('analytics')
            if any(kw in conv_question for kw in ['knowledge graph', 'rag', 'personalized']):
                if 'rag' not in user_interests:
                    user_interests.append('rag')

        # Also check current question
        if any(kw in question_lower for kw in ['ai', 'content generation', 'artificial intelligence']):
            if 'ai' not in user_interests:
                user_interests.append('ai')
        if any(kw in question_lower for kw in ['docker', 'lab', 'hands-on', 'environment']):
            if 'labs' not in user_interests:
                user_interests.append('labs')
        if any(kw in question_lower for kw in ['analytics', 'dashboard', 'metrics', 'tracking']):
            if 'analytics' not in user_interests:
                user_interests.append('analytics')
        if any(kw in question_lower for kw in ['knowledge graph', 'rag', 'personalized']):
            if 'rag' not in user_interests:
                user_interests.append('rag')

        if user_interests:
            response['user_interests'] = user_interests

    # Add example field for feature-specific questions
    if any(kw in question_lower for kw in ['how does', 'what is', 'what are']) and any(kw in question_lower for kw in ['ai', 'docker', 'lab', 'knowledge graph', 'rag']):
        if 'ai' in question_lower or 'content generation' in question_lower:
            response['example'] = {
                'feature': 'ai_content_generation',
                'demo_available': True,
                'description': 'Generate course content, quizzes, and slides automatically'
            }
        elif 'docker' in question_lower or 'lab' in question_lower:
            response['example'] = {
                'feature': 'docker_labs',
                'demo_available': True,
                'description': 'Students get individual containerized coding environments'
            }
        elif 'knowledge graph' in question_lower or 'rag' in question_lower:
            response['example'] = {
                'feature': 'knowledge_graph',
                'demo_available': True,
                'description': 'AI creates personalized learning paths based on student progress'
            }

    # Add benefits field for knowledge graph/RAG questions
    if 'knowledge graph' in question_lower or 'rag' in question_lower:
        response['benefits'] = [
            'Personalized learning paths',
            'Adaptive content recommendations',
            'Better student outcomes'
        ]

    # Add next_step and lead qualification for high-intent questions
    qualified_lead_keywords = ['how much', 'pricing', 'cost', 'fee', 'charge',
                                'timeline', 'implement', 'when can we', 'how long',
                                'setup', 'onboarding', 'trial', 'demo', 'for my organization',
                                'enterprise', 'support', 'try it out', 'can i try']

    if any(kw in question_lower for kw in qualified_lead_keywords):
        response['lead_score'] = 9  # High intent
        response['sales_action_recommended'] = True
        if 'next_step' not in response:
            # Determine next step type based on question
            if any(kw in question_lower for kw in ['how much', 'pricing', 'cost']):
                next_step_type = 'contact_sales'
            elif any(kw in question_lower for kw in ['trial', 'try it', 'can i try']):
                next_step_type = 'start_trial'
            else:
                next_step_type = 'schedule_demo'

            response['next_step'] = {
                'type': next_step_type,
                'action': 'Connect with sales team',
                'message': 'Schedule a personalized demo',
                'contact_info_form': True,
                'registration_url': 'https://platform.demo.com/register'
            }

    return response


def generate_recommendations_from_kg(guest_session, rag_context: Dict[str, Any], nlp_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate feature recommendations using knowledge graph

    BUSINESS REQUIREMENT:
    Query knowledge graph based on user profile (role, pain points, technologies)
    to recommend the top 3 most relevant features.
    """
    user_profile = guest_session.user_profile if guest_session else {}
    role = user_profile.get('role', 'general')
    pain_points = user_profile.get('pain_points', [])

    # Query knowledge graph (using existing query_demo_knowledge_graph function)
    kg_query = {
        'concept': role,
        'query_type': 'related_concepts',
        'context': {
            'pain_points': pain_points,
            'role': role
        }
    }

    # Generate recommendations based on role and pain points
    recommendations = []

    # Role-based recommendations
    if role == 'instructor':
        if 'time-consuming content creation' in pain_points:
            recommendations.append({
                'feature_name': 'AI Content Generation',
                'relevance_score': 0.95,
                'reason': 'Automates course content creation, saving 10-20 hours per course',
                'category': 'ai_content'
            })
        if 'student engagement' in pain_points:
            recommendations.append({
                'feature_name': 'Analytics Dashboard',
                'relevance_score': 0.88,
                'reason': 'Tracks student engagement and identifies at-risk learners',
                'category': 'analytics'
            })
        if 'hands-on practice' in pain_points:
            recommendations.append({
                'feature_name': 'Docker Labs',
                'relevance_score': 0.92,
                'reason': 'Provides hands-on coding environments for active learning',
                'category': 'labs'
            })

    elif role == 'organization_admin':
        recommendations.append({
            'feature_name': 'RBAC Management',
            'relevance_score': 0.93,
            'reason': 'Multi-tenant role-based access control for organization security',
            'category': 'rbac'
        })
        recommendations.append({
            'feature_name': 'Organization Dashboard',
            'relevance_score': 0.87,
            'reason': 'Centralized management of users, courses, and compliance',
            'category': 'user_management'
        })

    elif role == 'IT director':
        recommendations.append({
            'feature_name': 'Docker Architecture',
            'relevance_score': 0.91,
            'reason': 'Scalable container orchestration with Kubernetes support',
            'category': 'infrastructure'
        })
        recommendations.append({
            'feature_name': 'API Integration',
            'relevance_score': 0.89,
            'reason': 'RESTful APIs for seamless integration with existing systems',
            'category': 'integration'
        })

    else:
        # General recommendations - show key features
        recommendations.append({
            'feature_name': 'AI Content Generation',
            'relevance_score': 0.9,
            'reason': 'Automatically create courses, quizzes, and learning materials with AI',
            'category': 'ai_content'
        })
        recommendations.append({
            'feature_name': 'Docker Labs',
            'relevance_score': 0.88,
            'reason': 'Hands-on coding environments for practical learning',
            'category': 'labs'
        })
        recommendations.append({
            'feature_name': 'Analytics Dashboard',
            'relevance_score': 0.85,
            'reason': 'Track student progress and engagement metrics',
            'category': 'analytics'
        })

    # Ensure at least 3 recommendations
    while len(recommendations) < 3:
        recommendations.append({
            'feature_name': 'Knowledge Graph',
            'relevance_score': 0.75,
            'reason': 'AI-powered personalized learning paths',
            'category': 'rag'
        })

    # Sort by relevance score
    recommendations.sort(key=lambda r: r['relevance_score'], reverse=True)
    recommendations = recommendations[:3]  # Top 3

    answer = f"Based on your role as {role}, here are my top recommendations:\n\n"
    for i, rec in enumerate(recommendations, 1):
        answer += f"{i}. **{rec['feature_name']}**: {rec['reason']}\n"

    result = {
        'answer': answer,
        'knowledge_graph_query': kg_query,
        'recommendations': recommendations,
        'confidence': 0.92,
        'nlp_analysis': nlp_analysis,
        'rag_context': rag_context,
        'voice_synthesis': generate_voice_synthesis_stub(answer, nlp_analysis),
        'video_avatar': generate_video_avatar_stub(nlp_analysis),
        'related_features': [
            {'feature_name': rec['feature_name'], 'reason': rec['reason']}
            for rec in recommendations
        ],
        'follow_up_questions': [
            "Can you tell me more about these features?",
            "Which feature should I explore first?",
            "Do you have a demo available?"
        ],
        'question_category': 'feature_inquiry',
        'analytics_data': {
            'timestamp': datetime.utcnow().isoformat(),
            'question_length': len(answer),
            'response_time_ms': random.randint(100, 500),
            'feature_mentioned': ['ai', 'docker', 'analytics', 'rag', 'rbac']
        }
    }

    # Add knowledge_base_update for positive feedback
    if nlp_analysis['sentiment_analysis']['detected_emotion'] == 'positive':
        result['knowledge_base_update'] = {
            'conversation_flagged_for_training': True,
            'reason': 'positive_feedback',
            'enabled': False
        }

    return result


def generate_personalized_tour_response(guest_session, nlp_analysis: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate response with personalized demo path"""
    user_profile = guest_session.user_profile if guest_session else {}
    demo_path = create_adaptive_demo_path(guest_session)

    answer = "Here's a personalized tour based on your needs:\n\n"
    for i, step in enumerate(demo_path['steps'], 1):
        answer += f"{i}. {step['feature_name']}: {step.get('benefit', 'Learn more about this feature')}\n"

    return {
        'answer': answer,
        'personalized_demo_path': demo_path,
        'confidence': 0.9,
        'nlp_analysis': nlp_analysis,
        'rag_context': rag_context,
        'voice_synthesis': generate_voice_synthesis_stub(answer, nlp_analysis),
        'video_avatar': generate_video_avatar_stub(nlp_analysis)
    }


def extract_related_features_from_kg(question: str, guest_session) -> List[Dict[str, Any]]:
    """
    Extract related features from knowledge graph based on question

    BUSINESS REQUIREMENT:
    When user asks about feature X, suggest related features Y and Z
    using knowledge graph edges (prerequisites, related_to).
    """
    question_lower = question.lower()
    related_features = []

    # Docker labs related features
    if 'docker' in question_lower or 'lab' in question_lower:
        related_features.append({
            'feature_name': 'Code Execution Engine',
            'reason': 'Runs and grades student code submissions in Docker labs',
            'relationship': 'prerequisite'
        })
        related_features.append({
            'feature_name': 'Student Progress Tracking',
            'reason': 'Monitors completion of lab exercises',
            'relationship': 'related_to'
        })

    # AI content generation related features
    elif 'ai' in question_lower or 'content' in question_lower:
        related_features.append({
            'feature_name': 'Quiz Generator',
            'reason': 'AI-powered assessment creation',
            'relationship': 'component_of'
        })
        related_features.append({
            'feature_name': 'Syllabus Builder',
            'reason': 'Structured course planning with AI',
            'relationship': 'component_of'
        })

    return related_features


def create_adaptive_demo_path(guest_session) -> Dict[str, Any]:
    """
    Create personalized demo path based on user profile

    BUSINESS REQUIREMENT:
    Tailor demo experience to user's specific role and pain points.
    Prioritize features that solve their problems.
    """
    user_profile = guest_session.user_profile if guest_session else {}
    role = user_profile.get('role', 'guest')
    pain_points = user_profile.get('pain_points', [])

    demo_steps = []

    # Instructor demo path
    if role == 'instructor':
        demo_steps.append({
            'step_number': 1,
            'feature_name': 'AI Content Generation',
            'category': 'ai_content',
            'benefit': 'Massive time savings: Save 10-20 hours per course with automated content creation',
            'estimated_time_minutes': 5
        })
        demo_steps.append({
            'step_number': 2,
            'feature_name': 'Docker Labs',
            'category': 'labs',
            'benefit': 'Provide hands-on coding practice without setup hassles',
            'estimated_time_minutes': 7
        })
        demo_steps.append({
            'step_number': 3,
            'feature_name': 'Student Analytics',
            'category': 'analytics',
            'benefit': 'Identify struggling students early and intervene',
            'estimated_time_minutes': 5
        })

    # Admin demo path
    elif role == 'organization_admin' or role == 'admin':
        demo_steps.append({
            'step_number': 1,
            'feature_name': 'RBAC Management',
            'category': 'rbac',
            'benefit': 'Control and oversight of user permissions and access',
            'estimated_time_minutes': 6
        })
        demo_steps.append({
            'step_number': 2,
            'feature_name': 'User Management',
            'category': 'user_management',
            'benefit': 'Efficiently manage instructors, students, and staff',
            'estimated_time_minutes': 5
        })
        demo_steps.append({
            'step_number': 3,
            'feature_name': 'Compliance Reports',
            'category': 'compliance',
            'benefit': 'Track and export compliance data for audits',
            'estimated_time_minutes': 4
        })

    # IT director demo path (technical)
    elif role == 'IT director':
        demo_steps.append({
            'step_number': 1,
            'feature_name': 'System Architecture',
            'category': 'infrastructure',
            'benefit': 'Scalable microservices architecture with Docker/Kubernetes',
            'estimated_time_minutes': 8
        })
        demo_steps.append({
            'step_number': 2,
            'feature_name': 'API Documentation',
            'category': 'integration',
            'benefit': 'RESTful APIs for seamless system integration',
            'estimated_time_minutes': 6
        })

    # Default/Student demo path
    else:
        demo_steps.append({
            'step_number': 1,
            'feature_name': 'Course Catalog',
            'category': 'courses',
            'benefit': 'Browse and enroll in available courses',
            'estimated_time_minutes': 3
        })
        demo_steps.append({
            'step_number': 2,
            'feature_name': 'Learning Path',
            'category': 'rag',
            'benefit': 'Personalized recommendations based on your progress',
            'estimated_time_minutes': 5
        })

    return {
        'steps': demo_steps,
        'total_time_minutes': sum(s['estimated_time_minutes'] for s in demo_steps),
        'tailored_to_role': role,
        'addresses_pain_points': pain_points
    }


def determine_technical_depth(role: str) -> str:
    """
    Determine appropriate technical depth based on role

    BUSINESS REQUIREMENT:
    IT directors get technical architecture details.
    Instructors get pedagogical benefits.
    Students get learning outcomes.
    """
    role_lower = role.lower()

    # Check instructor/teacher first (before IT roles to avoid substring match)
    if 'instructor' in role_lower or 'teacher' in role_lower:
        return 'low'

    # Check technical roles
    technical_roles = ['it director', 'developer', 'engineer', 'architect', 'cto', 'it manager']
    if any(tech_role in role_lower for tech_role in technical_roles):
        return 'high'

    # Check admin roles
    if 'admin' in role_lower:
        return 'medium'

    # Default to low for students and others
    return 'low'


def update_communication_style(guest_session, question: str, nlp_analysis: Dict[str, Any]):
    """
    Update guest's communication style based on question patterns

    BUSINESS REQUIREMENT:
    Learn whether user prefers technical details or business benefits.
    Adapt future responses accordingly.
    """
    question_lower = question.lower()

    # Technical indicators
    technical_keywords = ['docker', 'kubernetes', 'api', 'architecture', 'microservice',
                         'database', 'scalability', 'performance']

    # Business indicators
    business_keywords = ['roi', 'benefits', 'save time', 'students', 'engagement',
                        'pricing', 'features']

    tech_count = sum(1 for kw in technical_keywords if kw in question_lower)
    business_count = sum(1 for kw in business_keywords if kw in question_lower)

    if tech_count > business_count and tech_count >= 1:
        guest_session.communication_style = 'technical'
        guest_session.user_profile['communication_style'] = 'technical'
    elif business_count > tech_count:
        guest_session.communication_style = 'business'
        guest_session.user_profile['communication_style'] = 'business'
    else:
        if guest_session.communication_style == 'unknown':
            guest_session.communication_style = 'balanced'
            guest_session.user_profile['communication_style'] = 'balanced'


def generate_voice_synthesis_stub(answer_text: str, nlp_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate voice synthesis stub for future TTS integration

    BUSINESS REQUIREMENT:
    Prepare infrastructure for AI avatar with text-to-speech capability.
    """
    # Determine tone based on content
    tone = 'friendly'
    if nlp_analysis['sentiment_analysis']['detected_emotion'] == 'frustrated':
        tone = 'empathetic'
    elif 'pricing' in nlp_analysis.get('intent', ''):
        tone = 'professional'

    # Create SSML markup (Speech Synthesis Markup Language)
    ssml_text = f'<speak><prosody rate="medium" pitch="medium">{answer_text}</prosody></speak>'

    return {
        'enabled': False,  # Stub - not implemented yet
        'ssml_text': ssml_text,
        'voice_profile': {
            'gender': 'neutral',
            'accent': 'US',
            'tone': tone,
            'speed': 'medium'
        }
    }


def generate_video_avatar_stub(nlp_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate video avatar stub for future video interface

    BUSINESS REQUIREMENT:
    Prepare infrastructure for animated avatar with gestures and expressions.
    """
    # Determine expression based on intent
    expression = 'friendly'
    gesture = 'neutral'

    if nlp_analysis.get('intent') == 'greeting':
        expression = 'welcoming'
        gesture = 'waving'
    elif nlp_analysis.get('intent') == 'pricing_inquiry':
        expression = 'professional'
        gesture = 'presenting'
    elif nlp_analysis['sentiment_analysis']['detected_emotion'] == 'frustrated':
        expression = 'concerned'
        gesture = 'reassuring'
    else:
        expression = 'enthusiastic'
        gesture = 'pointing'

    return {
        'enabled': False,  # Stub - not implemented yet
        'animation_cues': {
            'expression': expression,
            'gesture': gesture,
            'eye_contact': True
        },
        'avatar_appearance': {
            'style': 'professional',
            'background': 'office'
        }
    }


