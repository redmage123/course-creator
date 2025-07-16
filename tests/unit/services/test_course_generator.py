"""
Unit tests for Course Generator Service

Tests all components of the course generator service including:
- Course generation models
- AI integration
- Slide generation
- Quiz generation
- Lab environment
- Content processors
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException
import uuid
import json

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/course-generator'))

from models.course import (
    Course, CourseCreate, CourseUpdate, CourseGenerationRequest,
    GeneratedCourse, Slide, Quiz, QuizQuestion, QuizAnswer,
    LabEnvironment, LabSession
)
from models.common import BaseModel, ErrorResponse, SuccessResponse
from services.course_service import CourseService
from services.ai_service import AIService
from services.slide_service import SlideService
from services.quiz_service import QuizService
from services.lab_service import LabService
from repositories.course_repository import CourseRepository
from repositories.slide_repository import SlideRepository
from repositories.quiz_repository import QuizRepository
from repositories.lab_repository import LabRepository


class TestCourseGeneratorModels:
    """Test course generator data models."""
    
    def test_course_generation_request_validation(self):
        """Test course generation request validation."""
        request_data = {
            "title": "Python Programming",
            "description": "Learn Python from basics to advanced",
            "difficulty": "beginner",
            "duration_hours": 40,
            "topics": ["variables", "functions", "classes"],
            "learning_objectives": ["Understand Python syntax", "Build applications"],
            "target_audience": "beginners"
        }
        
        request = CourseGenerationRequest(**request_data)
        assert request.title == "Python Programming"
        assert request.difficulty == "beginner"
        assert request.duration_hours == 40
        assert len(request.topics) == 3
        assert len(request.learning_objectives) == 2
    
    def test_course_generation_request_title_validation(self):
        """Test course generation request title validation."""
        # Title too short
        with pytest.raises(ValueError):
            CourseGenerationRequest(
                title="AB",
                description="Description",
                difficulty="beginner"
            )
        
        # Title too long
        with pytest.raises(ValueError):
            CourseGenerationRequest(
                title="A" * 201,
                description="Description",
                difficulty="beginner"
            )
    
    def test_course_generation_request_duration_validation(self):
        """Test course generation request duration validation."""
        # Valid duration
        request = CourseGenerationRequest(
            title="Test Course",
            description="Description",
            difficulty="beginner",
            duration_hours=20
        )
        assert request.duration_hours == 20
        
        # Invalid duration (too short)
        with pytest.raises(ValueError):
            CourseGenerationRequest(
                title="Test Course",
                description="Description",
                difficulty="beginner",
                duration_hours=0
            )
        
        # Invalid duration (too long)
        with pytest.raises(ValueError):
            CourseGenerationRequest(
                title="Test Course",
                description="Description",
                difficulty="beginner",
                duration_hours=1000
            )
    
    def test_generated_course_model(self):
        """Test generated course model."""
        generated_course = GeneratedCourse(
            id=str(uuid.uuid4()),
            title="Python Programming",
            description="Learn Python programming",
            difficulty="beginner",
            duration_hours=40,
            topics=["variables", "functions"],
            learning_objectives=["Learn syntax", "Build apps"],
            syllabus={"week1": "Basics", "week2": "Advanced"},
            slides=[],
            quizzes=[],
            lab_exercises=[],
            generated_at=datetime.utcnow(),
            generated_by="ai_service"
        )
        
        assert generated_course.title == "Python Programming"
        assert generated_course.difficulty == "beginner"
        assert generated_course.duration_hours == 40
        assert len(generated_course.topics) == 2
        assert generated_course.generated_by == "ai_service"
    
    def test_slide_model_validation(self):
        """Test slide model validation."""
        slide = Slide(
            id=str(uuid.uuid4()),
            course_id=str(uuid.uuid4()),
            title="Introduction to Python",
            content="Python is a programming language...",
            slide_number=1,
            slide_type="text",
            notes="Speaker notes here",
            duration_minutes=10
        )
        
        assert slide.title == "Introduction to Python"
        assert slide.slide_number == 1
        assert slide.slide_type == "text"
        assert slide.duration_minutes == 10
    
    def test_slide_model_duration_validation(self):
        """Test slide duration validation."""
        # Valid duration
        slide = Slide(
            id=str(uuid.uuid4()),
            course_id=str(uuid.uuid4()),
            title="Test Slide",
            content="Content",
            slide_number=1,
            duration_minutes=5
        )
        assert slide.duration_minutes == 5
        
        # Invalid duration (negative)
        with pytest.raises(ValueError):
            Slide(
                id=str(uuid.uuid4()),
                course_id=str(uuid.uuid4()),
                title="Test Slide",
                content="Content",
                slide_number=1,
                duration_minutes=-1
            )
    
    def test_quiz_model_validation(self):
        """Test quiz model validation."""
        quiz = Quiz(
            id=str(uuid.uuid4()),
            course_id=str(uuid.uuid4()),
            title="Python Basics Quiz",
            description="Test your Python knowledge",
            questions=[],
            time_limit_minutes=30,
            passing_score=80,
            max_attempts=3
        )
        
        assert quiz.title == "Python Basics Quiz"
        assert quiz.time_limit_minutes == 30
        assert quiz.passing_score == 80
        assert quiz.max_attempts == 3
    
    def test_quiz_question_model(self):
        """Test quiz question model."""
        question = QuizQuestion(
            id=str(uuid.uuid4()),
            quiz_id=str(uuid.uuid4()),
            question_text="What is a variable in Python?",
            question_type="multiple_choice",
            points=10,
            correct_answers=["A container for storing data"],
            options=["A container for storing data", "A function", "A class", "A module"],
            explanation="Variables are used to store data values"
        )
        
        assert question.question_text == "What is a variable in Python?"
        assert question.question_type == "multiple_choice"
        assert question.points == 10
        assert len(question.options) == 4
        assert question.explanation == "Variables are used to store data values"
    
    def test_lab_environment_model(self):
        """Test lab environment model."""
        lab_env = LabEnvironment(
            id=str(uuid.uuid4()),
            course_id=str(uuid.uuid4()),
            name="Python Lab",
            description="Interactive Python programming lab",
            environment_type="jupyter",
            configuration={"python_version": "3.9", "packages": ["numpy", "pandas"]},
            resources={"cpu": "2", "memory": "4Gi", "storage": "10Gi"},
            instructions="Follow the exercises step by step"
        )
        
        assert lab_env.name == "Python Lab"
        assert lab_env.environment_type == "jupyter"
        assert lab_env.configuration["python_version"] == "3.9"
        assert lab_env.resources["cpu"] == "2"
    
    def test_lab_session_model(self):
        """Test lab session model."""
        lab_session = LabSession(
            id=str(uuid.uuid4()),
            lab_environment_id=str(uuid.uuid4()),
            student_id=str(uuid.uuid4()),
            status="active",
            start_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            session_data={"code": "print('Hello World')", "output": "Hello World"},
            progress=50.0
        )
        
        assert lab_session.status == "active"
        assert lab_session.progress == 50.0
        assert lab_session.session_data["code"] == "print('Hello World')"
        assert lab_session.session_data["output"] == "Hello World"


class TestCourseService:
    """Test course service for generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_course_repo = AsyncMock()
        self.mock_ai_service = AsyncMock()
        self.mock_slide_service = AsyncMock()
        self.mock_quiz_service = AsyncMock()
        self.mock_lab_service = AsyncMock()
        
        self.course_service = CourseService(
            self.mock_course_repo,
            self.mock_ai_service,
            self.mock_slide_service,
            self.mock_quiz_service,
            self.mock_lab_service
        )
    
    @pytest.mark.asyncio
    async def test_generate_course(self):
        """Test course generation."""
        generation_request = CourseGenerationRequest(
            title="Python Programming",
            description="Learn Python from basics to advanced",
            difficulty="beginner",
            duration_hours=40,
            topics=["variables", "functions", "classes"],
            learning_objectives=["Understand Python syntax", "Build applications"],
            target_audience="beginners"
        )
        
        # Mock AI-generated content
        mock_syllabus = {
            "week1": {"title": "Python Basics", "topics": ["variables", "data types"]},
            "week2": {"title": "Functions", "topics": ["function definition", "parameters"]},
            "week3": {"title": "Classes", "topics": ["class definition", "methods"]}
        }
        
        mock_slides = [
            Slide(
                id=str(uuid.uuid4()),
                course_id=str(uuid.uuid4()),
                title="Introduction to Python",
                content="Python is a programming language...",
                slide_number=1,
                slide_type="text",
                duration_minutes=10
            ),
            Slide(
                id=str(uuid.uuid4()),
                course_id=str(uuid.uuid4()),
                title="Variables in Python",
                content="Variables are containers for storing data...",
                slide_number=2,
                slide_type="text",
                duration_minutes=15
            )
        ]
        
        mock_quizzes = [
            Quiz(
                id=str(uuid.uuid4()),
                course_id=str(uuid.uuid4()),
                title="Python Basics Quiz",
                description="Test your Python knowledge",
                questions=[],
                time_limit_minutes=30,
                passing_score=80,
                max_attempts=3
            )
        ]
        
        # Mock generated course
        mock_generated_course = GeneratedCourse(
            id=str(uuid.uuid4()),
            title=generation_request.title,
            description=generation_request.description,
            difficulty=generation_request.difficulty,
            duration_hours=generation_request.duration_hours,
            topics=generation_request.topics,
            learning_objectives=generation_request.learning_objectives,
            syllabus=mock_syllabus,
            slides=mock_slides,
            quizzes=mock_quizzes,
            lab_exercises=[],
            generated_at=datetime.utcnow(),
            generated_by="ai_service"
        )
        
        # Mock service responses
        self.mock_ai_service.generate_syllabus.return_value = mock_syllabus
        self.mock_slide_service.generate_slides.return_value = mock_slides
        self.mock_quiz_service.generate_quizzes.return_value = mock_quizzes
        self.mock_lab_service.generate_lab_exercises.return_value = []
        self.mock_course_repo.save_generated_course.return_value = mock_generated_course
        
        result = await self.course_service.generate_course(generation_request)
        
        assert result is not None
        assert result.title == generation_request.title
        assert result.difficulty == generation_request.difficulty
        assert len(result.slides) == 2
        assert len(result.quizzes) == 1
        
        # Verify all services were called
        self.mock_ai_service.generate_syllabus.assert_called_once()
        self.mock_slide_service.generate_slides.assert_called_once()
        self.mock_quiz_service.generate_quizzes.assert_called_once()
        self.mock_lab_service.generate_lab_exercises.assert_called_once()
        self.mock_course_repo.save_generated_course.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_regenerate_course_content(self):
        """Test regenerating specific course content."""
        course_id = str(uuid.uuid4())
        content_types = ["slides", "quizzes"]
        
        # Mock existing course
        mock_course = GeneratedCourse(
            id=course_id,
            title="Python Programming",
            description="Learn Python programming",
            difficulty="beginner",
            duration_hours=40,
            topics=["variables", "functions"],
            learning_objectives=["Learn syntax", "Build apps"],
            syllabus={"week1": "Basics"},
            slides=[],
            quizzes=[],
            lab_exercises=[],
            generated_at=datetime.utcnow(),
            generated_by="ai_service"
        )
        
        # Mock regenerated content
        mock_new_slides = [
            Slide(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title="Updated Introduction",
                content="Updated content...",
                slide_number=1,
                slide_type="text",
                duration_minutes=12
            )
        ]
        
        mock_new_quizzes = [
            Quiz(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title="Updated Quiz",
                description="Updated quiz",
                questions=[],
                time_limit_minutes=25,
                passing_score=85,
                max_attempts=2
            )
        ]
        
        self.mock_course_repo.get_generated_course.return_value = mock_course
        self.mock_slide_service.regenerate_slides.return_value = mock_new_slides
        self.mock_quiz_service.regenerate_quizzes.return_value = mock_new_quizzes
        
        # Mock updated course
        updated_course = GeneratedCourse(
            id=course_id,
            title=mock_course.title,
            description=mock_course.description,
            difficulty=mock_course.difficulty,
            duration_hours=mock_course.duration_hours,
            topics=mock_course.topics,
            learning_objectives=mock_course.learning_objectives,
            syllabus=mock_course.syllabus,
            slides=mock_new_slides,
            quizzes=mock_new_quizzes,
            lab_exercises=mock_course.lab_exercises,
            generated_at=mock_course.generated_at,
            updated_at=datetime.utcnow(),
            generated_by=mock_course.generated_by
        )
        
        self.mock_course_repo.update_generated_course.return_value = updated_course
        
        result = await self.course_service.regenerate_course_content(course_id, content_types)
        
        assert result is not None
        assert len(result.slides) == 1
        assert len(result.quizzes) == 1
        assert result.slides[0].title == "Updated Introduction"
        assert result.quizzes[0].title == "Updated Quiz"
        
        # Verify services were called
        self.mock_course_repo.get_generated_course.assert_called_once_with(course_id)
        self.mock_slide_service.regenerate_slides.assert_called_once()
        self.mock_quiz_service.regenerate_quizzes.assert_called_once()
        self.mock_course_repo.update_generated_course.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_course_by_id(self):
        """Test getting course by ID."""
        course_id = str(uuid.uuid4())
        
        mock_course = GeneratedCourse(
            id=course_id,
            title="Python Programming",
            description="Learn Python programming",
            difficulty="beginner",
            duration_hours=40,
            topics=["variables", "functions"],
            learning_objectives=["Learn syntax", "Build apps"],
            syllabus={"week1": "Basics"},
            slides=[],
            quizzes=[],
            lab_exercises=[],
            generated_at=datetime.utcnow(),
            generated_by="ai_service"
        )
        
        self.mock_course_repo.get_generated_course.return_value = mock_course
        
        result = await self.course_service.get_course_by_id(course_id)
        
        assert result is not None
        assert result.id == course_id
        assert result.title == "Python Programming"
        
        self.mock_course_repo.get_generated_course.assert_called_once_with(course_id)
    
    @pytest.mark.asyncio
    async def test_update_course(self):
        """Test updating course."""
        course_id = str(uuid.uuid4())
        update_data = CourseUpdate(
            title="Updated Python Programming",
            description="Updated description",
            difficulty="intermediate"
        )
        
        mock_updated_course = GeneratedCourse(
            id=course_id,
            title="Updated Python Programming",
            description="Updated description",
            difficulty="intermediate",
            duration_hours=40,
            topics=["variables", "functions"],
            learning_objectives=["Learn syntax", "Build apps"],
            syllabus={"week1": "Basics"},
            slides=[],
            quizzes=[],
            lab_exercises=[],
            generated_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            generated_by="ai_service"
        )
        
        self.mock_course_repo.update_generated_course.return_value = mock_updated_course
        
        result = await self.course_service.update_course(course_id, update_data)
        
        assert result is not None
        assert result.title == "Updated Python Programming"
        assert result.description == "Updated description"
        assert result.difficulty == "intermediate"
        
        self.mock_course_repo.update_generated_course.assert_called_once()


class TestAIService:
    """Test AI service for content generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_ai_client = Mock()
        self.ai_service = AIService(self.mock_ai_client)
    
    @pytest.mark.asyncio
    async def test_generate_syllabus(self):
        """Test syllabus generation."""
        course_info = {
            "title": "Python Programming",
            "description": "Learn Python from basics to advanced",
            "difficulty": "beginner",
            "duration_hours": 40,
            "topics": ["variables", "functions", "classes"],
            "learning_objectives": ["Understand Python syntax", "Build applications"]
        }
        
        mock_syllabus = {
            "week1": {
                "title": "Python Basics",
                "topics": ["variables", "data types", "operators"],
                "duration_hours": 10,
                "learning_objectives": ["Understand variables", "Use data types"]
            },
            "week2": {
                "title": "Functions",
                "topics": ["function definition", "parameters", "return values"],
                "duration_hours": 15,
                "learning_objectives": ["Define functions", "Use parameters"]
            },
            "week3": {
                "title": "Classes and Objects",
                "topics": ["class definition", "methods", "inheritance"],
                "duration_hours": 15,
                "learning_objectives": ["Create classes", "Use inheritance"]
            }
        }
        
        self.mock_ai_client.generate_content.return_value = {
            "content": json.dumps(mock_syllabus),
            "type": "syllabus"
        }
        
        result = await self.ai_service.generate_syllabus(course_info)
        
        assert result is not None
        assert "week1" in result
        assert "week2" in result
        assert "week3" in result
        assert result["week1"]["title"] == "Python Basics"
        assert result["week2"]["duration_hours"] == 15
        
        self.mock_ai_client.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_slide_content(self):
        """Test slide content generation."""
        slide_info = {
            "title": "Introduction to Python",
            "topic": "Python basics",
            "learning_objectives": ["Understand what Python is", "Know Python applications"],
            "duration_minutes": 10,
            "audience_level": "beginner"
        }
        
        mock_slide_content = {
            "title": "Introduction to Python",
            "content": "Python is a high-level programming language...",
            "bullet_points": [
                "Python is interpreted",
                "Python is object-oriented",
                "Python has simple syntax"
            ],
            "examples": ["print('Hello World')", "x = 5", "if x > 0: print('positive')"],
            "notes": "Emphasize Python's readability and simplicity"
        }
        
        self.mock_ai_client.generate_content.return_value = {
            "content": json.dumps(mock_slide_content),
            "type": "slide"
        }
        
        result = await self.ai_service.generate_slide_content(slide_info)
        
        assert result is not None
        assert result["title"] == "Introduction to Python"
        assert "Python is a high-level programming language" in result["content"]
        assert len(result["bullet_points"]) == 3
        assert len(result["examples"]) == 3
        
        self.mock_ai_client.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_quiz_questions(self):
        """Test quiz question generation."""
        quiz_info = {
            "topic": "Python variables",
            "difficulty": "beginner",
            "question_count": 5,
            "question_types": ["multiple_choice", "true_false"],
            "learning_objectives": ["Understand variables", "Use variables correctly"]
        }
        
        mock_questions = [
            {
                "question_text": "What is a variable in Python?",
                "question_type": "multiple_choice",
                "options": ["A container for data", "A function", "A class", "A module"],
                "correct_answer": "A container for data",
                "explanation": "Variables store data values in Python",
                "points": 10
            },
            {
                "question_text": "Variables in Python are case-sensitive.",
                "question_type": "true_false",
                "correct_answer": "True",
                "explanation": "Python variables are case-sensitive",
                "points": 5
            }
        ]
        
        self.mock_ai_client.generate_content.return_value = {
            "content": json.dumps(mock_questions),
            "type": "quiz_questions"
        }
        
        result = await self.ai_service.generate_quiz_questions(quiz_info)
        
        assert result is not None
        assert len(result) == 2
        assert result[0]["question_text"] == "What is a variable in Python?"
        assert result[0]["question_type"] == "multiple_choice"
        assert result[1]["question_type"] == "true_false"
        assert result[1]["correct_answer"] == "True"
        
        self.mock_ai_client.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_lab_exercise(self):
        """Test lab exercise generation."""
        exercise_info = {
            "topic": "Python functions",
            "difficulty": "beginner",
            "duration_minutes": 30,
            "learning_objectives": ["Define functions", "Use parameters", "Return values"],
            "prerequisites": ["variables", "basic syntax"]
        }
        
        mock_exercise = {
            "title": "Working with Python Functions",
            "description": "Practice defining and using functions in Python",
            "instructions": [
                "Define a function that takes two parameters",
                "Use the function to calculate the sum",
                "Return the result from the function"
            ],
            "starter_code": "def add_numbers(a, b):\n    # Your code here\n    pass",
            "solution": "def add_numbers(a, b):\n    return a + b",
            "test_cases": [
                {"input": "add_numbers(2, 3)", "expected": "5"},
                {"input": "add_numbers(10, 20)", "expected": "30"}
            ],
            "hints": ["Use the return statement", "Add the parameters together"]
        }
        
        self.mock_ai_client.generate_content.return_value = {
            "content": json.dumps(mock_exercise),
            "type": "lab_exercise"
        }
        
        result = await self.ai_service.generate_lab_exercise(exercise_info)
        
        assert result is not None
        assert result["title"] == "Working with Python Functions"
        assert len(result["instructions"]) == 3
        assert "def add_numbers(a, b):" in result["starter_code"]
        assert "return a + b" in result["solution"]
        assert len(result["test_cases"]) == 2
        
        self.mock_ai_client.generate_content.assert_called_once()


class TestSlideService:
    """Test slide service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_slide_repo = AsyncMock()
        self.mock_ai_service = AsyncMock()
        self.slide_service = SlideService(self.mock_slide_repo, self.mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_generate_slides(self):
        """Test generating slides from syllabus."""
        course_info = {
            "id": str(uuid.uuid4()),
            "title": "Python Programming",
            "difficulty": "beginner",
            "syllabus": {
                "week1": {
                    "title": "Python Basics",
                    "topics": ["variables", "data types"],
                    "duration_hours": 10
                },
                "week2": {
                    "title": "Functions",
                    "topics": ["function definition", "parameters"],
                    "duration_hours": 15
                }
            }
        }
        
        # Mock AI-generated slide content
        mock_slide_content_1 = {
            "title": "Introduction to Python",
            "content": "Python is a programming language...",
            "bullet_points": ["Easy to learn", "Versatile", "Large community"],
            "examples": ["print('Hello World')"],
            "notes": "Emphasize Python's simplicity"
        }
        
        mock_slide_content_2 = {
            "title": "Python Variables",
            "content": "Variables store data values...",
            "bullet_points": ["Dynamic typing", "Case sensitive", "Multiple assignment"],
            "examples": ["x = 5", "name = 'John'"],
            "notes": "Show variable assignment examples"
        }
        
        self.mock_ai_service.generate_slide_content.side_effect = [
            mock_slide_content_1,
            mock_slide_content_2
        ]
        
        # Mock created slides
        mock_slides = [
            Slide(
                id=str(uuid.uuid4()),
                course_id=course_info["id"],
                title="Introduction to Python",
                content="Python is a programming language...",
                slide_number=1,
                slide_type="text",
                duration_minutes=10
            ),
            Slide(
                id=str(uuid.uuid4()),
                course_id=course_info["id"],
                title="Python Variables",
                content="Variables store data values...",
                slide_number=2,
                slide_type="text",
                duration_minutes=15
            )
        ]
        
        self.mock_slide_repo.create_slides.return_value = mock_slides
        
        result = await self.slide_service.generate_slides(course_info)
        
        assert result is not None
        assert len(result) == 2
        assert result[0].title == "Introduction to Python"
        assert result[1].title == "Python Variables"
        assert result[0].slide_number == 1
        assert result[1].slide_number == 2
        
        # Verify AI service was called for each slide
        assert self.mock_ai_service.generate_slide_content.call_count == 2
        self.mock_slide_repo.create_slides.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_regenerate_slides(self):
        """Test regenerating slides."""
        course_id = str(uuid.uuid4())
        
        # Mock existing slides
        existing_slides = [
            Slide(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title="Old Title 1",
                content="Old content 1",
                slide_number=1,
                slide_type="text",
                duration_minutes=10
            ),
            Slide(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title="Old Title 2",
                content="Old content 2",
                slide_number=2,
                slide_type="text",
                duration_minutes=15
            )
        ]
        
        # Mock course info
        mock_course_info = {
            "id": course_id,
            "title": "Python Programming",
            "difficulty": "beginner",
            "syllabus": {
                "week1": {
                    "title": "Python Basics",
                    "topics": ["variables", "data types"]
                }
            }
        }
        
        # Mock regenerated slide content
        mock_new_slide_content = {
            "title": "Updated Python Introduction",
            "content": "Updated Python content...",
            "bullet_points": ["Updated point 1", "Updated point 2"],
            "examples": ["print('Updated example')"],
            "notes": "Updated notes"
        }
        
        self.mock_slide_repo.get_slides_by_course.return_value = existing_slides
        self.mock_ai_service.generate_slide_content.return_value = mock_new_slide_content
        
        # Mock updated slides
        mock_updated_slides = [
            Slide(
                id=existing_slides[0].id,
                course_id=course_id,
                title="Updated Python Introduction",
                content="Updated Python content...",
                slide_number=1,
                slide_type="text",
                duration_minutes=10
            ),
            Slide(
                id=existing_slides[1].id,
                course_id=course_id,
                title="Updated Python Introduction",
                content="Updated Python content...",
                slide_number=2,
                slide_type="text",
                duration_minutes=15
            )
        ]
        
        self.mock_slide_repo.update_slides.return_value = mock_updated_slides
        
        result = await self.slide_service.regenerate_slides(mock_course_info)
        
        assert result is not None
        assert len(result) == 2
        assert result[0].title == "Updated Python Introduction"
        assert result[1].title == "Updated Python Introduction"
        
        # Verify existing slides were retrieved and updated
        self.mock_slide_repo.get_slides_by_course.assert_called_once_with(course_id)
        self.mock_slide_repo.update_slides.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_slides_by_course(self):
        """Test getting slides by course."""
        course_id = str(uuid.uuid4())
        
        mock_slides = [
            Slide(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title="Slide 1",
                content="Content 1",
                slide_number=1,
                slide_type="text",
                duration_minutes=10
            ),
            Slide(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title="Slide 2",
                content="Content 2",
                slide_number=2,
                slide_type="text",
                duration_minutes=15
            )
        ]
        
        self.mock_slide_repo.get_slides_by_course.return_value = mock_slides
        
        result = await self.slide_service.get_slides_by_course(course_id)
        
        assert result is not None
        assert len(result) == 2
        assert result[0].title == "Slide 1"
        assert result[1].title == "Slide 2"
        
        self.mock_slide_repo.get_slides_by_course.assert_called_once_with(course_id)


class TestQuizService:
    """Test quiz service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_quiz_repo = AsyncMock()
        self.mock_ai_service = AsyncMock()
        self.quiz_service = QuizService(self.mock_quiz_repo, self.mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_generate_quizzes(self):
        """Test generating quizzes from course content."""
        course_info = {
            "id": str(uuid.uuid4()),
            "title": "Python Programming",
            "difficulty": "beginner",
            "topics": ["variables", "functions"],
            "learning_objectives": ["Understand variables", "Use functions"]
        }
        
        # Mock AI-generated quiz questions
        mock_questions = [
            {
                "question_text": "What is a variable?",
                "question_type": "multiple_choice",
                "options": ["A container", "A function", "A class", "A module"],
                "correct_answer": "A container",
                "explanation": "Variables store data",
                "points": 10
            },
            {
                "question_text": "How do you define a function?",
                "question_type": "multiple_choice",
                "options": ["def func():", "function func():", "func():", "create func():"],
                "correct_answer": "def func():",
                "explanation": "Use def keyword",
                "points": 10
            }
        ]
        
        self.mock_ai_service.generate_quiz_questions.return_value = mock_questions
        
        # Mock created quiz
        mock_quiz = Quiz(
            id=str(uuid.uuid4()),
            course_id=course_info["id"],
            title="Python Programming Quiz",
            description="Test your Python knowledge",
            questions=[],
            time_limit_minutes=30,
            passing_score=80,
            max_attempts=3
        )
        
        self.mock_quiz_repo.create_quiz.return_value = mock_quiz
        
        result = await self.quiz_service.generate_quizzes(course_info)
        
        assert result is not None
        assert len(result) == 1
        assert result[0].title == "Python Programming Quiz"
        assert result[0].time_limit_minutes == 30
        assert result[0].passing_score == 80
        
        # Verify AI service was called
        self.mock_ai_service.generate_quiz_questions.assert_called_once()
        self.mock_quiz_repo.create_quiz.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_regenerate_quizzes(self):
        """Test regenerating quizzes."""
        course_info = {
            "id": str(uuid.uuid4()),
            "title": "Python Programming",
            "difficulty": "beginner",
            "topics": ["variables", "functions"],
            "learning_objectives": ["Understand variables", "Use functions"]
        }
        
        # Mock existing quiz
        existing_quiz = Quiz(
            id=str(uuid.uuid4()),
            course_id=course_info["id"],
            title="Old Quiz Title",
            description="Old description",
            questions=[],
            time_limit_minutes=30,
            passing_score=80,
            max_attempts=3
        )
        
        # Mock regenerated questions
        mock_new_questions = [
            {
                "question_text": "Updated question about variables?",
                "question_type": "multiple_choice",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A",
                "explanation": "Updated explanation",
                "points": 10
            }
        ]
        
        self.mock_quiz_repo.get_quizzes_by_course.return_value = [existing_quiz]
        self.mock_ai_service.generate_quiz_questions.return_value = mock_new_questions
        
        # Mock updated quiz
        mock_updated_quiz = Quiz(
            id=existing_quiz.id,
            course_id=course_info["id"],
            title="Updated Python Programming Quiz",
            description="Updated test your Python knowledge",
            questions=[],
            time_limit_minutes=30,
            passing_score=80,
            max_attempts=3
        )
        
        self.mock_quiz_repo.update_quiz.return_value = mock_updated_quiz
        
        result = await self.quiz_service.regenerate_quizzes(course_info)
        
        assert result is not None
        assert len(result) == 1
        assert result[0].title == "Updated Python Programming Quiz"
        
        # Verify existing quizzes were retrieved and updated
        self.mock_quiz_repo.get_quizzes_by_course.assert_called_once_with(course_info["id"])
        self.mock_ai_service.generate_quiz_questions.assert_called_once()
        self.mock_quiz_repo.update_quiz.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_quizzes_by_course(self):
        """Test getting quizzes by course."""
        course_id = str(uuid.uuid4())
        
        mock_quizzes = [
            Quiz(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title="Quiz 1",
                description="First quiz",
                questions=[],
                time_limit_minutes=30,
                passing_score=80,
                max_attempts=3
            ),
            Quiz(
                id=str(uuid.uuid4()),
                course_id=course_id,
                title="Quiz 2",
                description="Second quiz",
                questions=[],
                time_limit_minutes=45,
                passing_score=85,
                max_attempts=2
            )
        ]
        
        self.mock_quiz_repo.get_quizzes_by_course.return_value = mock_quizzes
        
        result = await self.quiz_service.get_quizzes_by_course(course_id)
        
        assert result is not None
        assert len(result) == 2
        assert result[0].title == "Quiz 1"
        assert result[1].title == "Quiz 2"
        assert result[0].time_limit_minutes == 30
        assert result[1].time_limit_minutes == 45
        
        self.mock_quiz_repo.get_quizzes_by_course.assert_called_once_with(course_id)


class TestLabService:
    """Test lab service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_lab_repo = AsyncMock()
        self.mock_ai_service = AsyncMock()
        self.lab_service = LabService(self.mock_lab_repo, self.mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_generate_lab_exercises(self):
        """Test generating lab exercises."""
        course_info = {
            "id": str(uuid.uuid4()),
            "title": "Python Programming",
            "difficulty": "beginner",
            "topics": ["variables", "functions"],
            "learning_objectives": ["Use variables", "Define functions"]
        }
        
        # Mock AI-generated lab exercise
        mock_exercise = {
            "title": "Python Variables Lab",
            "description": "Practice working with variables",
            "instructions": [
                "Create a variable named 'name'",
                "Assign your name to the variable",
                "Print the variable"
            ],
            "starter_code": "# Your code here\n",
            "solution": "name = 'John'\nprint(name)",
            "test_cases": [
                {"input": "name = 'Alice'", "expected": "Alice"},
                {"input": "name = 'Bob'", "expected": "Bob"}
            ],
            "hints": ["Use quotes for strings", "Use print() to display"]
        }
        
        self.mock_ai_service.generate_lab_exercise.return_value = mock_exercise
        
        # Mock created lab environment
        mock_lab_env = LabEnvironment(
            id=str(uuid.uuid4()),
            course_id=course_info["id"],
            name="Python Variables Lab",
            description="Practice working with variables",
            environment_type="jupyter",
            configuration={"python_version": "3.9"},
            resources={"cpu": "1", "memory": "2Gi"},
            instructions="Follow the lab instructions"
        )
        
        self.mock_lab_repo.create_lab_environment.return_value = mock_lab_env
        
        result = await self.lab_service.generate_lab_exercises(course_info)
        
        assert result is not None
        assert len(result) == 1
        assert result[0].name == "Python Variables Lab"
        assert result[0].environment_type == "jupyter"
        
        # Verify AI service was called
        self.mock_ai_service.generate_lab_exercise.assert_called_once()
        self.mock_lab_repo.create_lab_environment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_lab_session(self):
        """Test creating a lab session."""
        lab_env_id = str(uuid.uuid4())
        student_id = str(uuid.uuid4())
        
        # Mock lab environment
        mock_lab_env = LabEnvironment(
            id=lab_env_id,
            course_id=str(uuid.uuid4()),
            name="Python Lab",
            description="Interactive Python lab",
            environment_type="jupyter",
            configuration={"python_version": "3.9"},
            resources={"cpu": "2", "memory": "4Gi"},
            instructions="Follow the exercises"
        )
        
        self.mock_lab_repo.get_lab_environment.return_value = mock_lab_env
        
        # Mock created lab session
        mock_lab_session = LabSession(
            id=str(uuid.uuid4()),
            lab_environment_id=lab_env_id,
            student_id=student_id,
            status="active",
            start_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            session_data={},
            progress=0.0
        )
        
        self.mock_lab_repo.create_lab_session.return_value = mock_lab_session
        
        result = await self.lab_service.create_lab_session(lab_env_id, student_id)
        
        assert result is not None
        assert result.lab_environment_id == lab_env_id
        assert result.student_id == student_id
        assert result.status == "active"
        assert result.progress == 0.0
        
        # Verify dependencies were called
        self.mock_lab_repo.get_lab_environment.assert_called_once_with(lab_env_id)
        self.mock_lab_repo.create_lab_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_lab_session(self):
        """Test updating lab session."""
        session_id = str(uuid.uuid4())
        session_data = {
            "code": "print('Hello World')",
            "output": "Hello World",
            "current_exercise": 1
        }
        progress = 25.0
        
        # Mock updated session
        mock_updated_session = LabSession(
            id=session_id,
            lab_environment_id=str(uuid.uuid4()),
            student_id=str(uuid.uuid4()),
            status="active",
            start_time=datetime.utcnow() - timedelta(minutes=30),
            last_activity=datetime.utcnow(),
            session_data=session_data,
            progress=progress
        )
        
        self.mock_lab_repo.update_lab_session.return_value = mock_updated_session
        
        result = await self.lab_service.update_lab_session(session_id, session_data, progress)
        
        assert result is not None
        assert result.session_data == session_data
        assert result.progress == progress
        
        self.mock_lab_repo.update_lab_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_lab_session(self):
        """Test getting lab session."""
        session_id = str(uuid.uuid4())
        
        mock_session = LabSession(
            id=session_id,
            lab_environment_id=str(uuid.uuid4()),
            student_id=str(uuid.uuid4()),
            status="active",
            start_time=datetime.utcnow() - timedelta(minutes=30),
            last_activity=datetime.utcnow(),
            session_data={"code": "x = 5", "output": ""},
            progress=50.0
        )
        
        self.mock_lab_repo.get_lab_session.return_value = mock_session
        
        result = await self.lab_service.get_lab_session(session_id)
        
        assert result is not None
        assert result.id == session_id
        assert result.status == "active"
        assert result.progress == 50.0
        
        self.mock_lab_repo.get_lab_session.assert_called_once_with(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])