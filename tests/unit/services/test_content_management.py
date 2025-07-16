"""
Unit tests for Content Management Service

Tests all components of the content management service including:
- Content models validation
- Content repositories
- Content services
- API routes
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException, UploadFile
from io import BytesIO
import uuid
import json

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/content-management'))

from models.common import (
    ContentType, ProcessingStatus, ExportFormat, DifficultyLevel,
    create_api_response, create_error_response, create_success_response
)
from models.content import (
    SyllabusContent, SyllabusCreate, SyllabusUpdate, SyllabusResponse,
    SlideContent, SlideCreate, SlideUpdate, SlideResponse,
    Quiz, QuizCreate, QuizUpdate, QuizResponse, QuizQuestion,
    Exercise, ExerciseCreate, ExerciseUpdate, ExerciseResponse, ExerciseStep,
    LabEnvironment, LabEnvironmentCreate, LabEnvironmentUpdate, LabEnvironmentResponse,
    CourseInfo, LearningObjective, CourseModule, QuestionType, ExerciseType, SlideType
)
from repositories.content_repository import (
    ContentRepository, SyllabusRepository, SlideRepository, 
    QuizRepository, ExerciseRepository, LabEnvironmentRepository
)
from services.content_service import ContentService


class TestContentModels:
    """Test content data models."""
    
    def test_course_info_model_validation(self):
        """Test CourseInfo model validation."""
        course_info_data = {
            "course_code": "CS101",
            "course_title": "Introduction to Computer Science",
            "instructor": "Dr. Smith",
            "department": "Computer Science",
            "credits": 3,
            "duration_weeks": 16,
            "prerequisites": ["Math 101"]
        }
        
        course_info = CourseInfo(**course_info_data)
        assert course_info.course_code == "CS101"
        assert course_info.course_title == "Introduction to Computer Science"
        assert course_info.instructor == "Dr. Smith"
        assert course_info.credits == 3
        assert course_info.duration_weeks == 16
        assert len(course_info.prerequisites) == 1
    
    def test_learning_objective_model_validation(self):
        """Test LearningObjective model validation."""
        objective_data = {
            "id": str(uuid.uuid4()),
            "objective": "Students will understand basic programming concepts",
            "bloom_level": "Understanding",
            "assessment_method": "Quiz and Assignment",
            "module_id": str(uuid.uuid4())
        }
        
        learning_objective = LearningObjective(**objective_data)
        assert learning_objective.objective == "Students will understand basic programming concepts"
        assert learning_objective.bloom_level == "Understanding"
        assert learning_objective.assessment_method == "Quiz and Assignment"
    
    def test_syllabus_content_model_validation(self):
        """Test SyllabusContent model validation."""
        course_info = CourseInfo(
            course_code="CS101",
            course_title="Introduction to Computer Science",
            instructor="Dr. Smith",
            credits=3,
            duration_weeks=16
        )
        
        syllabus_data = {
            "id": str(uuid.uuid4()),
            "title": "CS101 Syllabus",
            "description": "Course syllabus for Introduction to Computer Science",
            "course_info": course_info,
            "learning_objectives": [],
            "modules": [],
            "assessment_methods": ["Quizzes", "Assignments", "Final Exam"],
            "grading_scheme": {"Quizzes": 30.0, "Assignments": 40.0, "Final Exam": 30.0},
            "policies": {"Attendance": "Mandatory", "Late Work": "10% penalty per day"},
            "schedule": [],
            "textbooks": ["Introduction to Programming", "Data Structures"]
        }
        
        syllabus = SyllabusContent(**syllabus_data)
        assert syllabus.title == "CS101 Syllabus"
        assert syllabus.course_info.course_code == "CS101"
        assert len(syllabus.assessment_methods) == 3
        assert syllabus.grading_scheme["Quizzes"] == 30.0
        assert "Attendance" in syllabus.policies
    
    def test_slide_content_model_validation(self):
        """Test SlideContent model validation."""
        slide_data = {
            "id": str(uuid.uuid4()),
            "title": "Introduction Slide",
            "slide_number": 1,
            "slide_type": SlideType.TITLE,
            "content": "Welcome to Computer Science 101",
            "speaker_notes": "Introduce yourself and the course",
            "layout": "title_slide",
            "background": "blue_gradient",
            "animations": ["fade_in", "slide_up"],
            "duration_minutes": 2.5
        }
        
        slide = SlideContent(**slide_data)
        assert slide.title == "Introduction Slide"
        assert slide.slide_number == 1
        assert slide.slide_type == SlideType.TITLE
        assert slide.content == "Welcome to Computer Science 101"
        assert slide.duration_minutes == 2.5
        assert len(slide.animations) == 2
    
    def test_quiz_question_model_validation(self):
        """Test QuizQuestion model validation."""
        question_data = {
            "question_id": str(uuid.uuid4()),
            "question": "What is the capital of France?",
            "question_type": QuestionType.MULTIPLE_CHOICE,
            "options": ["London", "Berlin", "Paris", "Madrid"],
            "correct_answer": "Paris",
            "explanation": "Paris is the capital and largest city of France.",
            "points": 2,
            "difficulty": DifficultyLevel.BEGINNER,
            "tags": ["geography", "europe"]
        }
        
        question = QuizQuestion(**question_data)
        assert question.question == "What is the capital of France?"
        assert question.question_type == QuestionType.MULTIPLE_CHOICE
        assert len(question.options) == 4
        assert question.correct_answer == "Paris"
        assert question.points == 2
        assert question.difficulty == DifficultyLevel.BEGINNER
    
    def test_exercise_step_model_validation(self):
        """Test ExerciseStep model validation."""
        step_data = {
            "step_number": 1,
            "instruction": "Create a new Python file called 'hello.py'",
            "expected_output": "File created successfully",
            "hints": ["Use your favorite text editor", "Save the file in the project directory"],
            "code_template": "# Write your code here\nprint('Hello, World!')"
        }
        
        exercise_step = ExerciseStep(**step_data)
        assert exercise_step.step_number == 1
        assert exercise_step.instruction == "Create a new Python file called 'hello.py'"
        assert exercise_step.expected_output == "File created successfully"
        assert len(exercise_step.hints) == 2
        assert "print('Hello, World!')" in exercise_step.code_template
    
    def test_lab_environment_model_validation(self):
        """Test LabEnvironment model validation."""
        lab_data = {
            "id": str(uuid.uuid4()),
            "title": "Python Programming Lab",
            "description": "Interactive Python programming environment",
            "environment_type": "docker",
            "base_image": "python:3.9",
            "tools": [{"name": "python", "version": "3.9"}, {"name": "pip", "version": "latest"}],
            "datasets": [{"name": "sample_data", "size": "1MB", "format": "csv"}],
            "setup_scripts": ["pip install -r requirements.txt", "python setup.py"],
            "access_instructions": "Use the terminal to run Python commands",
            "estimated_setup_time_minutes": 5,
            "resource_requirements": {"cpu": "1 core", "memory": "512MB", "storage": "1GB"}
        }
        
        lab_environment = LabEnvironment(**lab_data)
        assert lab_environment.title == "Python Programming Lab"
        assert lab_environment.environment_type == "docker"
        assert lab_environment.base_image == "python:3.9"
        assert len(lab_environment.tools) == 2
        assert len(lab_environment.datasets) == 1
        assert lab_environment.estimated_setup_time_minutes == 5


class TestContentRepositories:
    """Test content repository operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_pool = AsyncMock()
        self.content_repository = ContentRepository(self.mock_db_pool)
        self.syllabus_repository = SyllabusRepository(self.mock_db_pool)
        self.slide_repository = SlideRepository(self.mock_db_pool)
        self.quiz_repository = QuizRepository(self.mock_db_pool)
        self.exercise_repository = ExerciseRepository(self.mock_db_pool)
        self.lab_repository = LabEnvironmentRepository(self.mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_syllabus_repository_create(self):
        """Test syllabus repository creation."""
        course_info = CourseInfo(
            course_code="CS101",
            course_title="Introduction to Computer Science",
            instructor="Dr. Smith",
            credits=3
        )
        
        syllabus_data = SyllabusContent(
            id=str(uuid.uuid4()),
            title="CS101 Syllabus",
            description="Course syllabus",
            course_info=course_info,
            learning_objectives=[],
            modules=[],
            assessment_methods=["Quizzes", "Assignments"],
            grading_scheme={"Quizzes": 50.0, "Assignments": 50.0},
            policies={},
            schedule=[],
            textbooks=[]
        )
        
        # Mock database response
        mock_row = {
            "id": syllabus_data.id,
            "title": syllabus_data.title,
            "description": syllabus_data.description,
            "course_info": json.dumps(syllabus_data.course_info.model_dump()),
            "learning_objectives": json.dumps([]),
            "modules": json.dumps([]),
            "assessment_methods": json.dumps(syllabus_data.assessment_methods),
            "grading_scheme": json.dumps(syllabus_data.grading_scheme),
            "policies": json.dumps({}),
            "schedule": json.dumps([]),
            "textbooks": json.dumps([]),
            "tags": json.dumps([]),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "test_user",
            "course_id": None
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.syllabus_repository.create(syllabus_data)
        
        assert result is not None
        assert result.title == syllabus_data.title
        assert result.course_info.course_code == "CS101"
        mock_conn.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_slide_repository_get_ordered_slides(self):
        """Test getting ordered slides."""
        course_id = str(uuid.uuid4())
        
        mock_rows = [
            {
                "id": str(uuid.uuid4()),
                "title": "Slide 1",
                "slide_number": 1,
                "slide_type": "title",
                "content": "Introduction",
                "speaker_notes": None,
                "layout": None,
                "background": None,
                "animations": json.dumps([]),
                "duration_minutes": 2.0,
                "course_id": course_id,
                "tags": json.dumps([]),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "test_user"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Slide 2",
                "slide_number": 2,
                "slide_type": "content",
                "content": "Main content",
                "speaker_notes": None,
                "layout": None,
                "background": None,
                "animations": json.dumps([]),
                "duration_minutes": 3.0,
                "course_id": course_id,
                "tags": json.dumps([]),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": "test_user"
            }
        ]
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        self.mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        result = await self.slide_repository.get_ordered_slides(course_id)
        
        assert len(result) == 2
        assert result[0].slide_number == 1
        assert result[1].slide_number == 2
        assert result[0].title == "Slide 1"
        assert result[1].title == "Slide 2"
    
    @pytest.mark.asyncio
    async def test_content_repository_get_course_content(self):
        """Test getting all course content."""
        course_id = str(uuid.uuid4())
        
        # Mock each repository method
        self.content_repository.syllabus_repo.find_by_course_id = AsyncMock(return_value=[])
        self.content_repository.slide_repo.find_by_course_id = AsyncMock(return_value=[])
        self.content_repository.quiz_repo.find_by_course_id = AsyncMock(return_value=[])
        self.content_repository.exercise_repo.find_by_course_id = AsyncMock(return_value=[])
        self.content_repository.lab_repo.find_by_course_id = AsyncMock(return_value=[])
        
        result = await self.content_repository.get_course_content(course_id)
        
        assert "syllabus" in result
        assert "slides" in result
        assert "quizzes" in result
        assert "exercises" in result
        assert "labs" in result
        
        # Verify all repositories were called
        self.content_repository.syllabus_repo.find_by_course_id.assert_called_once_with(course_id)
        self.content_repository.slide_repo.find_by_course_id.assert_called_once_with(course_id)
        self.content_repository.quiz_repo.find_by_course_id.assert_called_once_with(course_id)
        self.content_repository.exercise_repo.find_by_course_id.assert_called_once_with(course_id)
        self.content_repository.lab_repo.find_by_course_id.assert_called_once_with(course_id)
    
    @pytest.mark.asyncio
    async def test_content_repository_get_content_statistics(self):
        """Test getting content statistics."""
        # Mock count methods
        self.content_repository.syllabus_repo.count = AsyncMock(return_value=5)
        self.content_repository.slide_repo.count = AsyncMock(return_value=25)
        self.content_repository.quiz_repo.count = AsyncMock(return_value=10)
        self.content_repository.exercise_repo.count = AsyncMock(return_value=15)
        self.content_repository.lab_repo.count = AsyncMock(return_value=3)
        
        result = await self.content_repository.get_content_statistics()
        
        assert result["syllabi_count"] == 5
        assert result["slides_count"] == 25
        assert result["quizzes_count"] == 10
        assert result["exercises_count"] == 15
        assert result["labs_count"] == 3
        assert result["total_content"] == 58


class TestContentService:
    """Test content service business logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_content_repository = Mock()
        self.mock_content_repository.syllabus_repo = AsyncMock()
        self.mock_content_repository.slide_repo = AsyncMock()
        self.mock_content_repository.quiz_repo = AsyncMock()
        self.mock_content_repository.exercise_repo = AsyncMock()
        self.mock_content_repository.lab_repo = AsyncMock()
        self.content_service = ContentService(self.mock_content_repository)
    
    @pytest.mark.asyncio
    async def test_create_syllabus(self):
        """Test syllabus creation."""
        course_info = CourseInfo(
            course_code="CS101",
            course_title="Introduction to Computer Science",
            instructor="Dr. Smith",
            credits=3
        )
        
        syllabus_data = SyllabusCreate(
            title="CS101 Syllabus",
            description="Course syllabus",
            course_info=course_info,
            learning_objectives=[],
            modules=[],
            assessment_methods=["Quizzes", "Assignments"],
            grading_scheme={"Quizzes": 50.0, "Assignments": 50.0},
            policies={},
            schedule=[],
            textbooks=[]
        )
        
        # Mock repository response
        mock_syllabus = Mock()
        mock_syllabus.id = str(uuid.uuid4())
        mock_syllabus.title = syllabus_data.title
        mock_syllabus.description = syllabus_data.description
        mock_syllabus.course_info = course_info
        mock_syllabus.learning_objectives = []
        mock_syllabus.modules = []
        mock_syllabus.assessment_methods = syllabus_data.assessment_methods
        mock_syllabus.grading_scheme = syllabus_data.grading_scheme
        mock_syllabus.policies = {}
        mock_syllabus.schedule = []
        mock_syllabus.textbooks = []
        mock_syllabus.course_id = None
        mock_syllabus.tags = []
        mock_syllabus.created_at = datetime.utcnow()
        mock_syllabus.updated_at = datetime.utcnow()
        mock_syllabus.created_by = "test_user"
        
        self.mock_content_repository.syllabus_repo.create.return_value = mock_syllabus
        
        result = await self.content_service.create_syllabus(syllabus_data, "test_user")
        
        assert result is not None
        assert result.title == syllabus_data.title
        assert result.course_info.course_code == "CS101"
        assert len(result.assessment_methods) == 2
        
        # Verify repository was called
        self.mock_content_repository.syllabus_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_syllabus_not_found(self):
        """Test getting non-existent syllabus."""
        syllabus_id = str(uuid.uuid4())
        
        self.mock_content_repository.syllabus_repo.get_by_id.return_value = None
        
        result = await self.content_service.get_syllabus(syllabus_id)
        
        assert result is None
        self.mock_content_repository.syllabus_repo.get_by_id.assert_called_once_with(syllabus_id)
    
    @pytest.mark.asyncio
    async def test_create_slide(self):
        """Test slide creation."""
        slide_data = SlideCreate(
            title="Introduction Slide",
            slide_number=1,
            slide_type=SlideType.TITLE,
            content="Welcome to the course",
            speaker_notes="Introduce yourself",
            layout="title_slide",
            background="blue",
            animations=["fade_in"],
            duration_minutes=2.0
        )
        
        # Mock repository response
        mock_slide = Mock()
        mock_slide.id = str(uuid.uuid4())
        mock_slide.title = slide_data.title
        mock_slide.slide_number = slide_data.slide_number
        mock_slide.slide_type = slide_data.slide_type
        mock_slide.content = slide_data.content
        mock_slide.speaker_notes = slide_data.speaker_notes
        mock_slide.layout = slide_data.layout
        mock_slide.background = slide_data.background
        mock_slide.animations = slide_data.animations
        mock_slide.duration_minutes = slide_data.duration_minutes
        mock_slide.course_id = None
        mock_slide.tags = []
        mock_slide.created_at = datetime.utcnow()
        mock_slide.updated_at = datetime.utcnow()
        mock_slide.created_by = "test_user"
        
        self.mock_content_repository.slide_repo.create.return_value = mock_slide
        
        result = await self.content_service.create_slide(slide_data, "test_user")
        
        assert result is not None
        assert result.title == slide_data.title
        assert result.slide_number == 1
        assert result.slide_type == SlideType.TITLE
        assert result.content == slide_data.content
        
        # Verify repository was called
        self.mock_content_repository.slide_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_quiz(self):
        """Test quiz creation."""
        quiz_question = QuizQuestion(
            question_id=str(uuid.uuid4()),
            question="What is 2+2?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["3", "4", "5", "6"],
            correct_answer="4",
            explanation="Basic arithmetic",
            points=1,
            difficulty=DifficultyLevel.BEGINNER,
            tags=["math"]
        )
        
        quiz_data = QuizCreate(
            title="Math Quiz",
            description="Basic math questions",
            questions=[quiz_question],
            time_limit_minutes=30,
            attempts_allowed=3,
            shuffle_questions=True,
            shuffle_options=True,
            show_correct_answers=True,
            passing_score=70.0
        )
        
        # Mock repository response
        mock_quiz = Mock()
        mock_quiz.id = str(uuid.uuid4())
        mock_quiz.title = quiz_data.title
        mock_quiz.description = quiz_data.description
        mock_quiz.questions = quiz_data.questions
        mock_quiz.time_limit_minutes = quiz_data.time_limit_minutes
        mock_quiz.attempts_allowed = quiz_data.attempts_allowed
        mock_quiz.shuffle_questions = quiz_data.shuffle_questions
        mock_quiz.shuffle_options = quiz_data.shuffle_options
        mock_quiz.show_correct_answers = quiz_data.show_correct_answers
        mock_quiz.passing_score = quiz_data.passing_score
        mock_quiz.course_id = None
        mock_quiz.tags = []
        mock_quiz.created_at = datetime.utcnow()
        mock_quiz.updated_at = datetime.utcnow()
        mock_quiz.created_by = "test_user"
        
        self.mock_content_repository.quiz_repo.create.return_value = mock_quiz
        
        result = await self.content_service.create_quiz(quiz_data, "test_user")
        
        assert result is not None
        assert result.title == quiz_data.title
        assert len(result.questions) == 1
        assert result.questions[0].question == "What is 2+2?"
        assert result.passing_score == 70.0
        
        # Verify repository was called
        self.mock_content_repository.quiz_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_exercise(self):
        """Test exercise creation."""
        exercise_step = ExerciseStep(
            step_number=1,
            instruction="Write a hello world program",
            expected_output="Hello, World!",
            hints=["Use print statement"],
            code_template="print('Hello, World!')"
        )
        
        exercise_data = ExerciseCreate(
            title="Hello World Exercise",
            description="Create your first program",
            exercise_type=ExerciseType.CODING,
            difficulty=DifficultyLevel.BEGINNER,
            estimated_time_minutes=15,
            learning_objectives=["Understand basic syntax"],
            prerequisites=["None"],
            steps=[exercise_step],
            solution="print('Hello, World!')",
            grading_rubric={"correctness": 100},
            resources=["Python documentation"]
        )
        
        # Mock repository response
        mock_exercise = Mock()
        mock_exercise.id = str(uuid.uuid4())
        mock_exercise.title = exercise_data.title
        mock_exercise.description = exercise_data.description
        mock_exercise.exercise_type = exercise_data.exercise_type
        mock_exercise.difficulty = exercise_data.difficulty
        mock_exercise.estimated_time_minutes = exercise_data.estimated_time_minutes
        mock_exercise.learning_objectives = exercise_data.learning_objectives
        mock_exercise.prerequisites = exercise_data.prerequisites
        mock_exercise.steps = exercise_data.steps
        mock_exercise.solution = exercise_data.solution
        mock_exercise.grading_rubric = exercise_data.grading_rubric
        mock_exercise.resources = exercise_data.resources
        mock_exercise.course_id = None
        mock_exercise.tags = []
        mock_exercise.created_at = datetime.utcnow()
        mock_exercise.updated_at = datetime.utcnow()
        mock_exercise.created_by = "test_user"
        
        self.mock_content_repository.exercise_repo.create.return_value = mock_exercise
        
        result = await self.content_service.create_exercise(exercise_data, "test_user")
        
        assert result is not None
        assert result.title == exercise_data.title
        assert result.exercise_type == ExerciseType.CODING
        assert result.difficulty == DifficultyLevel.BEGINNER
        assert len(result.steps) == 1
        assert result.steps[0].instruction == "Write a hello world program"
        
        # Verify repository was called
        self.mock_content_repository.exercise_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_lab_environment(self):
        """Test lab environment creation."""
        lab_data = LabEnvironmentCreate(
            title="Python Lab",
            description="Python programming environment",
            environment_type="docker",
            base_image="python:3.9",
            tools=[{"name": "python", "version": "3.9"}],
            datasets=[{"name": "sample_data", "size": "1MB"}],
            setup_scripts=["pip install requirements.txt"],
            access_instructions="Use the terminal",
            estimated_setup_time_minutes=5,
            resource_requirements={"cpu": "1 core", "memory": "512MB"}
        )
        
        # Mock repository response
        mock_lab = Mock()
        mock_lab.id = str(uuid.uuid4())
        mock_lab.title = lab_data.title
        mock_lab.description = lab_data.description
        mock_lab.environment_type = lab_data.environment_type
        mock_lab.base_image = lab_data.base_image
        mock_lab.tools = lab_data.tools
        mock_lab.datasets = lab_data.datasets
        mock_lab.setup_scripts = lab_data.setup_scripts
        mock_lab.access_instructions = lab_data.access_instructions
        mock_lab.estimated_setup_time_minutes = lab_data.estimated_setup_time_minutes
        mock_lab.resource_requirements = lab_data.resource_requirements
        mock_lab.course_id = None
        mock_lab.tags = []
        mock_lab.created_at = datetime.utcnow()
        mock_lab.updated_at = datetime.utcnow()
        mock_lab.created_by = "test_user"
        
        self.mock_content_repository.lab_repo.create.return_value = mock_lab
        
        result = await self.content_service.create_lab_environment(lab_data, "test_user")
        
        assert result is not None
        assert result.title == lab_data.title
        assert result.environment_type == "docker"
        assert result.base_image == "python:3.9"
        assert len(result.tools) == 1
        assert result.estimated_setup_time_minutes == 5
        
        # Verify repository was called
        self.mock_content_repository.lab_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_syllabus(self):
        """Test syllabus update."""
        syllabus_id = str(uuid.uuid4())
        
        # Mock existing syllabus
        mock_existing_syllabus = Mock()
        mock_existing_syllabus.id = syllabus_id
        mock_existing_syllabus.title = "Old Title"
        
        # Mock updated syllabus
        mock_updated_syllabus = Mock()
        mock_updated_syllabus.id = syllabus_id
        mock_updated_syllabus.title = "New Title"
        mock_updated_syllabus.description = "Updated description"
        mock_updated_syllabus.course_info = CourseInfo(course_title="Updated Course")
        mock_updated_syllabus.learning_objectives = []
        mock_updated_syllabus.modules = []
        mock_updated_syllabus.assessment_methods = []
        mock_updated_syllabus.grading_scheme = {}
        mock_updated_syllabus.policies = {}
        mock_updated_syllabus.schedule = []
        mock_updated_syllabus.textbooks = []
        mock_updated_syllabus.course_id = None
        mock_updated_syllabus.tags = []
        mock_updated_syllabus.created_at = datetime.utcnow()
        mock_updated_syllabus.updated_at = datetime.utcnow()
        mock_updated_syllabus.created_by = "test_user"
        
        self.mock_content_repository.syllabus_repo.get_by_id.return_value = mock_existing_syllabus
        self.mock_content_repository.syllabus_repo.update.return_value = mock_updated_syllabus
        
        updates = SyllabusUpdate(title="New Title", description="Updated description")
        
        result = await self.content_service.update_syllabus(syllabus_id, updates)
        
        assert result is not None
        assert result.title == "New Title"
        assert result.description == "Updated description"
        
        # Verify repository methods were called
        self.mock_content_repository.syllabus_repo.get_by_id.assert_called_once_with(syllabus_id)
        self.mock_content_repository.syllabus_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_syllabus(self):
        """Test syllabus deletion."""
        syllabus_id = str(uuid.uuid4())
        
        self.mock_content_repository.syllabus_repo.delete.return_value = True
        
        result = await self.content_service.delete_syllabus(syllabus_id)
        
        assert result is True
        self.mock_content_repository.syllabus_repo.delete.assert_called_once_with(syllabus_id)
    
    @pytest.mark.asyncio
    async def test_search_content(self):
        """Test content search."""
        query = "programming"
        content_types = [ContentType.SLIDES, ContentType.EXERCISES]
        
        # Mock repository search results
        mock_search_results = {
            "slides": [Mock(title="Programming Basics Slide")],
            "exercises": [Mock(title="Programming Exercise")]
        }
        
        self.mock_content_repository.search_all_content = AsyncMock(return_value=mock_search_results)
        
        result = await self.content_service.search_content(query, content_types)
        
        assert result is not None
        assert "slides" in result
        assert "exercises" in result
        
        # Verify repository method was called
        self.mock_content_repository.search_all_content.assert_called_once_with(query, content_types)
    
    @pytest.mark.asyncio
    async def test_get_content_statistics(self):
        """Test getting content statistics."""
        mock_stats = {
            "syllabi_count": 5,
            "slides_count": 25,
            "quizzes_count": 10,
            "exercises_count": 15,
            "labs_count": 3,
            "total_content": 58
        }
        
        self.mock_content_repository.get_content_statistics = AsyncMock(return_value=mock_stats)
        
        result = await self.content_service.get_content_statistics()
        
        assert result is not None
        assert result["syllabi_count"] == 5
        assert result["slides_count"] == 25
        assert result["total_content"] == 58
        
        # Verify repository method was called
        self.mock_content_repository.get_content_statistics.assert_called_once()


class TestContentAPI:
    """Test content management API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # This would require setting up a test client with the actual FastAPI app
        # For now, we'll test the core functionality through service layer
        pass
    
    def test_api_response_models(self):
        """Test API response model creation."""
        # Test success response
        success_response = create_success_response(
            "Operation successful",
            data={"id": "test-id"}
        )
        
        assert success_response.success is True
        assert success_response.message == "Operation successful"
        assert success_response.data["id"] == "test-id"
        
        # Test error response
        error_response = create_error_response(
            "Operation failed",
            "VALIDATION_ERROR",
            details={"field": "title", "issue": "required"}
        )
        
        assert error_response.success is False
        assert error_response.message == "Operation failed"
        assert error_response.error_code == "VALIDATION_ERROR"
        assert error_response.details["field"] == "title"
    
    def test_content_type_validation(self):
        """Test content type validation."""
        # Test valid content types
        valid_types = [
            ContentType.SYLLABUS,
            ContentType.SLIDES,
            ContentType.EXERCISES,
            ContentType.QUIZZES,
            ContentType.LABS
        ]
        
        for content_type in valid_types:
            assert content_type in ContentType
        
        # Test content type string values
        assert ContentType.SYLLABUS == "syllabus"
        assert ContentType.SLIDES == "slides"
        assert ContentType.EXERCISES == "exercises"
        assert ContentType.QUIZZES == "quizzes"
        assert ContentType.LABS == "labs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])