"""
Unit Tests for Course Generator Domain Entities
Testing domain business logic and validation rules following SOLID principles
"""
import pytest
from datetime import datetime, timedelta
from services.course_generator.domain.entities.course_content import (
    Syllabus, Slide, Exercise, LabEnvironment, GenerationJob,
    DifficultyLevel, SlideType, ExerciseType, JobStatus, ContentType
)
from services.course_generator.domain.entities.quiz import (
    Quiz, QuizQuestion, QuizAttempt, QuizGenerationRequest,
    QuestionType, DifficultyLevel as QuizDifficultyLevel
)
from services.course_generator.domain.entities.student_interaction import (
    StudentProgress, ChatInteraction, LabSession, DynamicContentRequest
)

class TestSyllabus:
    """Test syllabus domain entity business logic"""
    
    def test_syllabus_creation_valid(self):
        """Test valid syllabus creation"""
        syllabus = Syllabus(
            course_id="course_123",
            title="Introduction to Python",
            description="Learn Python fundamentals",
            category="Programming",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_duration=40
        )
        
        assert syllabus.course_id == "course_123"
        assert syllabus.title == "Introduction to Python"
        assert syllabus.difficulty_level == DifficultyLevel.BEGINNER
        assert syllabus.estimated_duration == 40
        assert isinstance(syllabus.created_at, datetime)
        assert isinstance(syllabus.updated_at, datetime)
        assert len(syllabus.id) > 0
    
    def test_syllabus_validation_empty_course_id(self):
        """Test syllabus validation with empty course ID"""
        with pytest.raises(ValueError, match="Course ID is required"):
            Syllabus(
                course_id="",
                title="Test Course",
                description="Test Description",
                category="Test",
                difficulty_level=DifficultyLevel.BEGINNER,
                estimated_duration=40
            )
    
    def test_syllabus_validation_empty_title(self):
        """Test syllabus validation with empty title"""
        with pytest.raises(ValueError, match="Title is required"):
            Syllabus(
                course_id="course_123",
                title="",
                description="Test Description",
                category="Test",
                difficulty_level=DifficultyLevel.BEGINNER,
                estimated_duration=40
            )
    
    def test_syllabus_validation_negative_duration(self):
        """Test syllabus validation with negative duration"""
        with pytest.raises(ValueError, match="Estimated duration must be positive"):
            Syllabus(
                course_id="course_123",
                title="Test Course",
                description="Test Description",
                category="Test",
                difficulty_level=DifficultyLevel.BEGINNER,
                estimated_duration=-10
            )
    
    def test_syllabus_add_learning_objective(self):
        """Test adding learning objectives"""
        syllabus = Syllabus(
            course_id="course_123",
            title="Test Course",
            description="Test Description",
            category="Test",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_duration=40
        )
        
        syllabus.add_learning_objective("Understand Python syntax")
        syllabus.add_learning_objective("Write basic Python programs")
        
        assert len(syllabus.learning_objectives) == 2
        assert "Understand Python syntax" in syllabus.learning_objectives
    
    def test_syllabus_add_duplicate_objective(self):
        """Test adding duplicate learning objective"""
        syllabus = Syllabus(
            course_id="course_123",
            title="Test Course",
            description="Test Description",
            category="Test",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_duration=40
        )
        
        syllabus.add_learning_objective("Understand Python syntax")
        syllabus.add_learning_objective("Understand Python syntax")  # Duplicate
        
        # Should only have one instance
        assert len(syllabus.learning_objectives) == 1
    
    def test_syllabus_calculate_total_topic_duration(self):
        """Test calculating total duration from topics"""
        syllabus = Syllabus(
            course_id="course_123",
            title="Test Course",
            description="Test Description",
            category="Test",
            difficulty_level=DifficultyLevel.BEGINNER,
            estimated_duration=40
        )
        
        syllabus.topics = [
            {"name": "Variables", "duration_hours": 4, "subtopics": ["Types", "Assignment"]},
            {"name": "Functions", "duration_hours": 6, "subtopics": ["Definition", "Parameters"]}
        ]
        
        total_duration = syllabus.calculate_total_topic_duration()
        assert total_duration == 10

class TestQuiz:
    """Test quiz domain entity business logic"""
    
    def test_quiz_creation_valid(self):
        """Test valid quiz creation"""
        questions = [
            QuizQuestion(
                question="What is Python?",
                options=["Language", "Snake", "Tool", "Framework"],
                correct_answer=0,
                points=1
            ),
            QuizQuestion(
                question="What is a variable?",
                options=["Container", "Function", "Loop", "Class"],
                correct_answer=0,
                points=1
            )
        ]
        
        quiz = Quiz(
            course_id="course_123",
            title="Python Basics Quiz",
            topic="Python Fundamentals",
            difficulty="beginner",
            questions=questions
        )
        
        assert quiz.course_id == "course_123"
        assert quiz.title == "Python Basics Quiz"
        assert len(quiz.questions) == 2
        assert quiz.get_question_count() == 2
        assert quiz.get_total_points() == 2
    
    def test_quiz_validation_empty_questions(self):
        """Test quiz validation with no questions"""
        with pytest.raises(ValueError, match="Quiz must have at least one question"):
            Quiz(
                course_id="course_123",
                title="Empty Quiz",
                topic="Test",
                difficulty="beginner",
                questions=[]
            )
    
    def test_quiz_calculate_score(self):
        """Test quiz score calculation"""
        questions = [
            QuizQuestion(
                question="What is 2+2?",
                options=["3", "4", "5", "6"],
                correct_answer=1,
                points=2
            ),
            QuizQuestion(
                question="What is 3*3?",
                options=["6", "9", "12", "15"],
                correct_answer=1,
                points=3
            )
        ]
        
        quiz = Quiz(
            course_id="course_123",
            title="Math Quiz",
            topic="Arithmetic",
            difficulty="beginner",
            questions=questions
        )
        
        # Answer both correctly
        answers = [1, 1]
        score_result = quiz.calculate_score(answers)
        
        assert score_result["total_questions"] == 2
        assert score_result["correct_answers"] == 2
        assert score_result["earned_points"] == 5
        assert score_result["total_points"] == 5
        assert score_result["percentage"] == 100.0
        assert score_result["passed"] == True
    
    def test_quiz_calculate_score_partial(self):
        """Test quiz score calculation with partial correct answers"""
        questions = [
            QuizQuestion(
                question="What is 2+2?",
                options=["3", "4", "5", "6"],
                correct_answer=1,
                points=2
            ),
            QuizQuestion(
                question="What is 3*3?",
                options=["6", "9", "12", "15"],
                correct_answer=1,
                points=3
            )
        ]
        
        quiz = Quiz(
            course_id="course_123",
            title="Math Quiz",
            topic="Arithmetic",
            difficulty="beginner",
            questions=questions,
            passing_score=60
        )
        
        # Answer first correctly, second incorrectly
        answers = [1, 0]
        score_result = quiz.calculate_score(answers)
        
        assert score_result["correct_answers"] == 1
        assert score_result["earned_points"] == 2
        assert score_result["percentage"] == 40.0
        assert score_result["passed"] == False  # Below 60% passing score

class TestQuizQuestion:
    """Test quiz question domain entity"""
    
    def test_quiz_question_creation_valid(self):
        """Test valid quiz question creation"""
        question = QuizQuestion(
            question="What is Python?",
            options=["Language", "Snake", "Tool", "Framework"],
            correct_answer=0,
            points=1
        )
        
        assert question.question == "What is Python?"
        assert len(question.options) == 4
        assert question.correct_answer == 0
        assert question.points == 1
    
    def test_quiz_question_validation_empty_question(self):
        """Test quiz question validation with empty question text"""
        with pytest.raises(ValueError, match="Question text is required"):
            QuizQuestion(
                question="",
                options=["A", "B", "C", "D"],
                correct_answer=0,
                points=1
            )
    
    def test_quiz_question_validation_insufficient_options(self):
        """Test quiz question validation with too few options"""
        with pytest.raises(ValueError, match="Question must have at least 2 options"):
            QuizQuestion(
                question="What is Python?",
                options=["Language"],
                correct_answer=0,
                points=1
            )
    
    def test_quiz_question_validation_invalid_correct_answer(self):
        """Test quiz question validation with invalid correct answer index"""
        with pytest.raises(ValueError, match="Correct answer index is out of range"):
            QuizQuestion(
                question="What is Python?",
                options=["Language", "Snake"],
                correct_answer=2,  # Out of range
                points=1
            )
    
    def test_quiz_question_is_correct_answer(self):
        """Test checking if answer is correct"""
        question = QuizQuestion(
            question="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct_answer=1,
            points=1
        )
        
        assert question.is_correct_answer(1) == True
        assert question.is_correct_answer(0) == False
        assert question.is_correct_answer(2) == False
    
    def test_quiz_question_get_correct_option(self):
        """Test getting the correct option text"""
        question = QuizQuestion(
            question="What is the capital of France?",
            options=["London", "Paris", "Berlin", "Madrid"],
            correct_answer=1,
            points=1
        )
        
        assert question.get_correct_option() == "Paris"

class TestExercise:
    """Test exercise domain entity business logic"""
    
    def test_exercise_creation_valid(self):
        """Test valid exercise creation"""
        exercise = Exercise(
            course_id="course_123",
            title="Hello World",
            description="Write a Hello World program",
            topic="Basic Programming",
            difficulty=DifficultyLevel.BEGINNER,
            exercise_type=ExerciseType.CODING,
            instructions="Print 'Hello, World!' to the console"
        )
        
        assert exercise.course_id == "course_123"
        assert exercise.title == "Hello World"
        assert exercise.difficulty == DifficultyLevel.BEGINNER
        assert exercise.exercise_type == ExerciseType.CODING
    
    def test_exercise_validation_empty_title(self):
        """Test exercise validation with empty title"""
        with pytest.raises(ValueError, match="Title is required"):
            Exercise(
                course_id="course_123",
                title="",
                description="Test Description",
                topic="Test Topic",
                difficulty=DifficultyLevel.BEGINNER,
                exercise_type=ExerciseType.CODING,
                instructions="Test instructions"
            )
    
    def test_exercise_add_test_case(self):
        """Test adding test cases to exercise"""
        exercise = Exercise(
            course_id="course_123",
            title="Sum Function",
            description="Write a function that adds two numbers",
            topic="Functions",
            difficulty=DifficultyLevel.BEGINNER,
            exercise_type=ExerciseType.CODING,
            instructions="Create a function called sum(a, b)"
        )
        
        exercise.add_test_case("sum(2, 3)", "5", "Basic addition")
        exercise.add_test_case("sum(0, 0)", "0", "Zero addition")
        
        assert len(exercise.test_cases) == 2
        assert exercise.test_cases[0]["input"] == "sum(2, 3)"
        assert exercise.test_cases[0]["expected_output"] == "5"
    
    def test_exercise_calculate_estimated_time(self):
        """Test calculating estimated completion time"""
        exercise = Exercise(
            course_id="course_123",
            title="Complex Algorithm",
            description="Implement a sorting algorithm",
            topic="Algorithms",
            difficulty=DifficultyLevel.ADVANCED,
            exercise_type=ExerciseType.CODING,
            instructions="Implement quicksort"
        )
        
        # Advanced coding exercises should have longer estimated times
        estimated_time = exercise.calculate_estimated_time()
        assert estimated_time >= 45  # Advanced exercises take more time

class TestGenerationJob:
    """Test generation job domain entity"""
    
    def test_generation_job_creation(self):
        """Test generation job creation"""
        job = GenerationJob(
            content_type=ContentType.SYLLABUS,
            course_id="course_123",
            parameters={"title": "Test Course", "difficulty": "beginner"}
        )
        
        assert job.content_type == ContentType.SYLLABUS
        assert job.course_id == "course_123"
        assert job.status == JobStatus.PENDING
        assert job.progress_percentage == 0
        assert isinstance(job.created_at, datetime)
    
    def test_generation_job_start(self):
        """Test starting a generation job"""
        job = GenerationJob(
            content_type=ContentType.QUIZ,
            course_id="course_123",
            parameters={"topic": "Python Basics"}
        )
        
        job.start()
        
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        assert isinstance(job.started_at, datetime)
    
    def test_generation_job_complete(self):
        """Test completing a generation job"""
        job = GenerationJob(
            content_type=ContentType.EXERCISE,
            course_id="course_123",
            parameters={"topic": "Variables"}
        )
        
        job.start()
        result = {"exercise_id": "ex_123", "title": "Variable Practice"}
        job.complete(result)
        
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.progress_percentage == 100
        assert job.result == result
    
    def test_generation_job_fail(self):
        """Test failing a generation job"""
        job = GenerationJob(
            content_type=ContentType.SLIDE,
            course_id="course_123",
            parameters={"topic": "Introduction"}
        )
        
        job.start()
        error_message = "AI service unavailable"
        job.fail(error_message)
        
        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None
        assert job.error_message == error_message
    
    def test_generation_job_update_progress(self):
        """Test updating job progress"""
        job = GenerationJob(
            content_type=ContentType.LAB_ENVIRONMENT,
            course_id="course_123",
            parameters={"environment": "python"}
        )
        
        job.start()
        job.update_progress(50, "Halfway complete")
        
        assert job.progress_percentage == 50
        assert job.status == JobStatus.RUNNING
    
    def test_generation_job_validation_invalid_progress(self):
        """Test job progress validation"""
        job = GenerationJob(
            content_type=ContentType.SYLLABUS,
            course_id="course_123",
            parameters={}
        )
        
        job.start()
        
        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            job.update_progress(150)
    
    def test_generation_job_get_duration(self):
        """Test getting job duration"""
        job = GenerationJob(
            content_type=ContentType.QUIZ,
            course_id="course_123",
            parameters={}
        )
        
        job.start()
        # Simulate some time passing
        job.started_at = datetime.utcnow() - timedelta(minutes=5)
        job.complete({"quiz_id": "quiz_123"})
        
        duration = job.get_duration_minutes()
        assert duration >= 4  # Should be approximately 5 minutes

class TestStudentProgress:
    """Test student progress domain entity"""
    
    def test_student_progress_creation(self):
        """Test student progress creation"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_123",
            overall_progress=75.5,
            completed_exercises=8,
            total_exercises=10
        )
        
        assert progress.student_id == "student_123"
        assert progress.course_id == "course_123"
        assert progress.overall_progress == 75.5
        assert progress.completed_exercises == 8
    
    def test_student_progress_validation_negative_progress(self):
        """Test progress validation with negative values"""
        with pytest.raises(ValueError, match="Overall progress cannot be negative"):
            StudentProgress(
                student_id="student_123",
                course_id="course_123",
                overall_progress=-10.0,
                completed_exercises=0,
                total_exercises=10
            )
    
    def test_student_progress_validation_excessive_progress(self):
        """Test progress validation with values over 100%"""
        with pytest.raises(ValueError, match="Overall progress cannot exceed 100%"):
            StudentProgress(
                student_id="student_123",
                course_id="course_123",
                overall_progress=150.0,
                completed_exercises=10,
                total_exercises=10
            )
    
    def test_student_progress_calculate_completion_rate(self):
        """Test calculating completion rate"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_123",
            overall_progress=80.0,
            completed_exercises=8,
            total_exercises=10
        )
        
        completion_rate = progress.calculate_completion_rate()
        assert completion_rate == 80.0  # 8/10 * 100
    
    def test_student_progress_is_at_risk(self):
        """Test determining if student is at risk"""
        # Student with low progress and many failed attempts
        at_risk_progress = StudentProgress(
            student_id="student_123",
            course_id="course_123",
            overall_progress=25.0,
            completed_exercises=2,
            total_exercises=10,
            quiz_scores=[45.0, 38.0, 52.0],  # Low quiz scores
            last_login=datetime.utcnow() - timedelta(days=7)  # Haven't logged in for a week
        )
        
        assert at_risk_progress.is_at_risk() == True
        
        # Student with good progress
        good_progress = StudentProgress(
            student_id="student_456",
            course_id="course_123",
            overall_progress=85.0,
            completed_exercises=9,
            total_exercises=10,
            quiz_scores=[88.0, 92.0, 85.0],
            last_login=datetime.utcnow() - timedelta(hours=2)
        )
        
        assert good_progress.is_at_risk() == False
    
    def test_student_progress_update_quiz_score(self):
        """Test updating quiz scores"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_123",
            overall_progress=60.0,
            completed_exercises=5,
            total_exercises=10
        )
        
        progress.add_quiz_score(85.0)
        progress.add_quiz_score(92.0)
        
        assert len(progress.quiz_scores) == 2
        assert progress.get_average_quiz_score() == 88.5
    
    def test_student_progress_time_tracking(self):
        """Test time tracking functionality"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_123",
            overall_progress=30.0,
            completed_exercises=3,
            total_exercises=10
        )
        
        # Add study time
        progress.add_study_time(120)  # 2 hours
        progress.add_study_time(90)   # 1.5 hours
        
        assert progress.total_study_time_minutes == 210
        assert progress.get_study_time_hours() == 3.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])