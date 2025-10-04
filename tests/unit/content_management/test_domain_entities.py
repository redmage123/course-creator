"""
Unit Tests for Content Management Domain Entities
Following SOLID principles and TDD methodology
"""

import pytest
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any

# Import domain entities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'content-management'))

from domain.entities.base_content import BaseContent, ContentStatus, ContentType
from domain.entities.syllabus import Syllabus, SyllabusModule, GradingScheme
from domain.entities.slide import Slide, SlideType, SlideLayout, SlideContent, SlideAnimation
from domain.entities.quiz import Quiz, QuizQuestion, QuestionType, QuizSettings


class TestBaseContent:
    """Test BaseContent domain entity following TDD principles"""
    
    def test_base_content_creation_with_valid_data(self):
        """Test creating base content with valid data"""
        # Arrange
        title = "Test Content"
        course_id = str(uuid4())
        creator_id = str(uuid4())
        
        # Act
        content = BaseContent(
            title=title,
            course_id=course_id,
            creator_id=creator_id,
            content_type=ContentType.DOCUMENT
        )
        
        # Assert
        assert content.title == title
        assert content.course_id == course_id
        assert content.creator_id == creator_id
        assert content.content_type == ContentType.DOCUMENT
        assert content.status == ContentStatus.DRAFT
        assert content.created_at is not None
        assert content.updated_at is not None
        assert isinstance(content.id, str)
    
    def test_base_content_creation_with_empty_title_raises_error(self):
        """Test creating content with empty title raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Title is required"):
            BaseContent(
                title="",
                course_id=str(uuid4()),
                creator_id=str(uuid4()),
                content_type=ContentType.DOCUMENT
            )
    
    def test_base_content_creation_with_empty_course_id_raises_error(self):
        """Test creating content with empty course_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Course ID is required"):
            BaseContent(
                title="Test Content",
                course_id="",
                creator_id=str(uuid4()),
                content_type=ContentType.DOCUMENT
            )
    
    def test_base_content_update_title_success(self):
        """Test updating content title successfully"""
        # Arrange
        content = BaseContent(
            title="Original Title",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            content_type=ContentType.DOCUMENT
        )
        original_updated_at = content.updated_at
        new_title = "Updated Title"
        
        # Act
        content.update_title(new_title)
        
        # Assert
        assert content.title == new_title
        assert content.updated_at > original_updated_at
    
    def test_base_content_update_description_success(self):
        """Test updating content description successfully"""
        # Arrange
        content = BaseContent(
            title="Test Content",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            content_type=ContentType.DOCUMENT
        )
        new_description = "Updated description"
        
        # Act
        content.update_description(new_description)
        
        # Assert
        assert content.description == new_description
    
    def test_base_content_publish_success(self):
        """Test publishing content successfully"""
        # Arrange
        content = BaseContent(
            title="Test Content",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            content_type=ContentType.DOCUMENT
        )
        
        # Act
        content.publish()
        
        # Assert
        assert content.status == ContentStatus.PUBLISHED
        assert content.published_at is not None
    
    def test_base_content_archive_success(self):
        """Test archiving content successfully"""
        # Arrange
        content = BaseContent(
            title="Test Content",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            content_type=ContentType.DOCUMENT
        )
        
        # Act
        content.archive()
        
        # Assert
        assert content.status == ContentStatus.ARCHIVED
    
    def test_base_content_is_published_returns_correct_boolean(self):
        """Test is_published returns correct boolean"""
        # Arrange
        draft_content = BaseContent(
            title="Draft Content",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            content_type=ContentType.DOCUMENT
        )
        
        published_content = BaseContent(
            title="Published Content",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            content_type=ContentType.DOCUMENT
        )
        published_content.publish()
        
        # Act & Assert
        assert not draft_content.is_published()
        assert published_content.is_published()


class TestSyllabus:
    """Test Syllabus domain entity following TDD principles"""
    
    def test_syllabus_creation_with_valid_data(self):
        """Test creating syllabus with valid data"""
        # Arrange
        title = "Course Syllabus"
        course_id = str(uuid4())
        creator_id = str(uuid4())
        duration_weeks = 12
        
        # Act
        syllabus = Syllabus(
            title=title,
            course_id=course_id,
            creator_id=creator_id,
            duration_weeks=duration_weeks
        )
        
        # Assert
        assert syllabus.title == title
        assert syllabus.course_id == course_id
        assert syllabus.creator_id == creator_id
        assert syllabus.duration_weeks == duration_weeks
        assert syllabus.content_type == ContentType.SYLLABUS
        assert syllabus.modules == []
        assert syllabus.learning_objectives == []
        assert syllabus.grading_scheme is None
    
    def test_syllabus_creation_with_invalid_duration_raises_error(self):
        """Test creating syllabus with invalid duration raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Duration must be positive"):
            Syllabus(
                title="Test Syllabus",
                course_id=str(uuid4()),
                creator_id=str(uuid4()),
                duration_weeks=0
            )
    
    def test_syllabus_add_module_success(self):
        """Test adding module to syllabus successfully"""
        # Arrange
        syllabus = Syllabus(
            title="Test Syllabus",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            duration_weeks=12
        )
        
        module = SyllabusModule(
            week_number=1,
            title="Introduction",
            description="Course introduction and overview",
            topics=["Course overview", "Learning objectives"]
        )
        
        # Act
        syllabus.add_module(module)
        
        # Assert
        assert len(syllabus.modules) == 1
        assert syllabus.modules[0] == module
    
    def test_syllabus_add_duplicate_module_raises_error(self):
        """Test adding duplicate module raises ValueError"""
        # Arrange
        syllabus = Syllabus(
            title="Test Syllabus",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            duration_weeks=12
        )
        
        module1 = SyllabusModule(
            week_number=1,
            title="Module 1",
            description="First module",
            topics=["Topic 1"]
        )
        
        module2 = SyllabusModule(
            week_number=1,  # Same week number
            title="Module 2",
            description="Second module",
            topics=["Topic 2"]
        )
        
        syllabus.add_module(module1)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Module for week 1 already exists"):
            syllabus.add_module(module2)
    
    def test_syllabus_add_learning_objective_success(self):
        """Test adding learning objective successfully"""
        # Arrange
        syllabus = Syllabus(
            title="Test Syllabus",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            duration_weeks=12
        )
        
        objective = LearningObjective(
            description="Understand basic programming concepts",
            bloom_level="understand",
            assessment_method="quiz"
        )
        
        # Act
        syllabus.add_learning_objective(objective)
        
        # Assert
        assert len(syllabus.learning_objectives) == 1
        assert syllabus.learning_objectives[0] == objective
    
    def test_syllabus_set_grading_scheme_success(self):
        """Test setting grading scheme successfully"""
        # Arrange
        syllabus = Syllabus(
            title="Test Syllabus",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            duration_weeks=12
        )
        
        grading_scheme = GradingScheme(
            assignments_weight=40,
            quizzes_weight=30,
            final_exam_weight=30,
            participation_weight=0
        )
        
        # Act
        syllabus.set_grading_scheme(grading_scheme)
        
        # Assert
        assert syllabus.grading_scheme == grading_scheme
    
    def test_syllabus_get_total_hours_calculates_correctly(self):
        """Test get_total_hours calculates total hours correctly"""
        # Arrange
        syllabus = Syllabus(
            title="Test Syllabus",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            duration_weeks=4
        )
        
        # Add modules with different hours
        module1 = SyllabusModule(
            week_number=1,
            title="Module 1",
            description="First module",
            topics=["Topic 1"],
            hours=3
        )
        
        module2 = SyllabusModule(
            week_number=2,
            title="Module 2",
            description="Second module",
            topics=["Topic 2"],
            hours=4
        )
        
        syllabus.add_module(module1)
        syllabus.add_module(module2)
        
        # Act
        total_hours = syllabus.get_total_hours()
        
        # Assert
        assert total_hours == 7


class TestSlide:
    """Test Slide domain entity following TDD principles"""
    
    def test_slide_creation_with_valid_data(self):
        """Test creating slide with valid data"""
        # Arrange
        title = "Introduction Slide"
        course_id = str(uuid4())
        creator_id = str(uuid4())
        slide_number = 1
        slide_type = SlideType.TITLE
        
        # Act
        slide = Slide(
            title=title,
            course_id=course_id,
            creator_id=creator_id,
            slide_number=slide_number,
            slide_type=slide_type
        )
        
        # Assert
        assert slide.title == title
        assert slide.course_id == course_id
        assert slide.creator_id == creator_id
        assert slide.slide_number == slide_number
        assert slide.slide_type == slide_type
        assert slide.content_type == ContentType.SLIDE
        assert slide.content == ""
        assert slide.speaker_notes == ""
    
    def test_slide_creation_with_invalid_slide_number_raises_error(self):
        """Test creating slide with invalid slide number raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Slide number must be positive"):
            Slide(
                title="Test Slide",
                course_id=str(uuid4()),
                creator_id=str(uuid4()),
                slide_number=0,
                slide_type=SlideType.CONTENT
            )
    
    def test_slide_update_content_success(self):
        """Test updating slide content successfully"""
        # Arrange
        slide = Slide(
            title="Test Slide",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            slide_number=1,
            slide_type=SlideType.CONTENT
        )
        new_content = "Updated slide content"
        
        # Act
        slide.update_content(new_content)
        
        # Assert
        assert slide.content == new_content
    
    def test_slide_add_speaker_notes_success(self):
        """Test adding speaker notes successfully"""
        # Arrange
        slide = Slide(
            title="Test Slide",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            slide_number=1,
            slide_type=SlideType.CONTENT
        )
        notes = "Remember to emphasize this point"
        
        # Act
        slide.add_speaker_notes(notes)
        
        # Assert
        assert slide.speaker_notes == notes
    
    def test_slide_set_transition_success(self):
        """Test setting slide transition successfully"""
        # Arrange
        slide = Slide(
            title="Test Slide",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            slide_number=1,
            slide_type=SlideType.CONTENT
        )
        transition = SlideTransition.FADE
        
        # Act
        slide.set_transition(transition)
        
        # Assert
        assert slide.transition == transition
    
    def test_slide_apply_template_success(self):
        """Test applying template to slide successfully"""
        # Arrange
        slide = Slide(
            title="Test Slide",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            slide_number=1,
            slide_type=SlideType.CONTENT
        )
        template = SlideTemplate.CORPORATE
        
        # Act
        slide.apply_template(template)
        
        # Assert
        assert slide.template == template


class TestLab:
    """Test Lab domain entity following TDD principles"""
    
    def test_lab_creation_with_valid_data(self):
        """Test creating lab with valid data"""
        # Arrange
        title = "Python Basics Lab"
        course_id = str(uuid4())
        creator_id = str(uuid4())
        lab_type = LabType.CODING
        
        # Act
        lab = Lab(
            title=title,
            course_id=course_id,
            creator_id=creator_id,
            lab_type=lab_type
        )
        
        # Assert
        assert lab.title == title
        assert lab.course_id == course_id
        assert lab.creator_id == creator_id
        assert lab.lab_type == lab_type
        assert lab.content_type == ContentType.LAB
        assert lab.files == []
        assert lab.environment is None
        assert lab.instructions is None
    
    def test_lab_add_file_success(self):
        """Test adding file to lab successfully"""
        # Arrange
        lab = Lab(
            title="Test Lab",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            lab_type=LabType.CODING
        )
        
        lab_file = LabFile(
            filename="main.py",
            content="print('Hello, World!')",
            file_type="python",
            is_readonly=False
        )
        
        # Act
        lab.add_file(lab_file)
        
        # Assert
        assert len(lab.files) == 1
        assert lab.files[0] == lab_file
    
    def test_lab_add_duplicate_file_raises_error(self):
        """Test adding duplicate file raises ValueError"""
        # Arrange
        lab = Lab(
            title="Test Lab",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            lab_type=LabType.CODING
        )
        
        file1 = LabFile(
            filename="main.py",
            content="print('Hello!')",
            file_type="python"
        )
        
        file2 = LabFile(
            filename="main.py",  # Same filename
            content="print('World!')",
            file_type="python"
        )
        
        lab.add_file(file1)
        
        # Act & Assert
        with pytest.raises(ValueError, match="File main.py already exists"):
            lab.add_file(file2)
    
    def test_lab_set_environment_success(self):
        """Test setting lab environment successfully"""
        # Arrange
        lab = Lab(
            title="Test Lab",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            lab_type=LabType.CODING
        )
        
        environment = LabEnvironment(
            language="python",
            version="3.9",
            packages=["pandas", "numpy"],
            resources={"cpu": "1", "memory": "512Mi"}
        )
        
        # Act
        lab.set_environment(environment)
        
        # Assert
        assert lab.environment == environment
    
    def test_lab_set_instructions_success(self):
        """Test setting lab instructions successfully"""
        # Arrange
        lab = Lab(
            title="Test Lab",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            lab_type=LabType.CODING
        )
        
        instructions = LabInstructions(
            overview="Complete the programming exercises",
            steps=[
                "Open main.py",
                "Implement the required functions",
                "Run the tests"
            ],
            expected_output="All tests should pass",
            grading_criteria="Functionality: 70%, Code quality: 30%"
        )
        
        # Act
        lab.set_instructions(instructions)
        
        # Assert
        assert lab.instructions == instructions
    
    def test_lab_get_file_by_name_returns_correct_file(self):
        """Test get_file_by_name returns correct file"""
        # Arrange
        lab = Lab(
            title="Test Lab",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            lab_type=LabType.CODING
        )
        
        file1 = LabFile(filename="main.py", content="# Main file", file_type="python")
        file2 = LabFile(filename="utils.py", content="# Utilities", file_type="python")
        
        lab.add_file(file1)
        lab.add_file(file2)
        
        # Act
        found_file = lab.get_file_by_name("utils.py")
        
        # Assert
        assert found_file == file2
    
    def test_lab_get_file_by_name_returns_none_for_nonexistent_file(self):
        """Test get_file_by_name returns None for non-existent file"""
        # Arrange
        lab = Lab(
            title="Test Lab",
            course_id=str(uuid4()),
            creator_id=str(uuid4()),
            lab_type=LabType.CODING
        )
        
        # Act
        found_file = lab.get_file_by_name("nonexistent.py")
        
        # Assert
        assert found_file is None


class TestQuiz:
    """Test Quiz domain entity following TDD principles"""
    
    def test_quiz_creation_with_valid_data(self):
        """Test creating quiz with valid data"""
        # Arrange
        title = "Python Fundamentals Quiz"
        course_id = str(uuid4())
        creator_id = str(uuid4())
        
        # Act
        quiz = Quiz(
            title=title,
            course_id=course_id,
            creator_id=creator_id
        )
        
        # Assert
        assert quiz.title == title
        assert quiz.course_id == course_id
        assert quiz.creator_id == creator_id
        assert quiz.content_type == ContentType.QUIZ
        assert quiz.questions == []
        assert quiz.settings is None
    
    def test_quiz_add_question_success(self):
        """Test adding question to quiz successfully"""
        # Arrange
        quiz = Quiz(
            title="Test Quiz",
            course_id=str(uuid4()),
            creator_id=str(uuid4())
        )
        
        question = Question(
            question_text="What is Python?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["A programming language", "A snake", "A framework", "A database"],
            correct_answer="A programming language",
            points=1
        )
        
        # Act
        quiz.add_question(question)
        
        # Assert
        assert len(quiz.questions) == 1
        assert quiz.questions[0] == question
    
    def test_quiz_remove_question_success(self):
        """Test removing question from quiz successfully"""
        # Arrange
        quiz = Quiz(
            title="Test Quiz",
            course_id=str(uuid4()),
            creator_id=str(uuid4())
        )
        
        question = Question(
            question_text="Test question",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["A", "B", "C", "D"],
            correct_answer="A",
            points=1
        )
        
        quiz.add_question(question)
        
        # Act
        quiz.remove_question(0)  # Remove first question
        
        # Assert
        assert len(quiz.questions) == 0
    
    def test_quiz_set_settings_success(self):
        """Test setting quiz settings successfully"""
        # Arrange
        quiz = Quiz(
            title="Test Quiz",
            course_id=str(uuid4()),
            creator_id=str(uuid4())
        )
        
        settings = QuizSettings(
            time_limit_minutes=30,
            max_attempts=3,
            show_correct_answers=True,
            randomize_questions=False,
            passing_score=70
        )
        
        # Act
        quiz.set_settings(settings)
        
        # Assert
        assert quiz.settings == settings
    
    def test_quiz_calculate_total_points_success(self):
        """Test calculating total points successfully"""
        # Arrange
        quiz = Quiz(
            title="Test Quiz",
            course_id=str(uuid4()),
            creator_id=str(uuid4())
        )
        
        question1 = Question(
            question_text="Question 1",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["A", "B"],
            correct_answer="A",
            points=2
        )
        
        question2 = Question(
            question_text="Question 2",
            question_type=QuestionType.TRUE_FALSE,
            options=["True", "False"],
            correct_answer="True",
            points=3
        )
        
        quiz.add_question(question1)
        quiz.add_question(question2)
        
        # Act
        total_points = quiz.calculate_total_points()
        
        # Assert
        assert total_points == 5


class TestValueObjects:
    """Test value objects used in domain entities"""
    
    def test_syllabus_module_creation_with_valid_data(self):
        """Test creating SyllabusModule with valid data"""
        # Act
        module = SyllabusModule(
            week_number=1,
            title="Introduction",
            description="Course introduction",
            topics=["Overview", "Goals"],
            hours=3
        )
        
        # Assert
        assert module.week_number == 1
        assert module.title == "Introduction"
        assert module.description == "Course introduction"
        assert module.topics == ["Overview", "Goals"]
        assert module.hours == 3
    
    def test_lab_file_creation_with_valid_data(self):
        """Test creating LabFile with valid data"""
        # Act
        lab_file = LabFile(
            filename="test.py",
            content="print('test')",
            file_type="python",
            is_readonly=True
        )
        
        # Assert
        assert lab_file.filename == "test.py"
        assert lab_file.content == "print('test')"
        assert lab_file.file_type == "python"
        assert lab_file.is_readonly == True
    
    def test_question_creation_with_valid_data(self):
        """Test creating Question with valid data"""
        # Act
        question = Question(
            question_text="What is 2+2?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["3", "4", "5", "6"],
            correct_answer="4",
            points=1,
            explanation="Basic arithmetic"
        )
        
        # Assert
        assert question.question_text == "What is 2+2?"
        assert question.question_type == QuestionType.MULTIPLE_CHOICE
        assert question.options == ["3", "4", "5", "6"]
        assert question.correct_answer == "4"
        assert question.points == 1
        assert question.explanation == "Basic arithmetic"


class TestEnums:
    """Test enumeration classes"""
    
    def test_content_status_enum_values(self):
        """Test ContentStatus enum has expected values"""
        assert ContentStatus.DRAFT.value == "draft"
        assert ContentStatus.PUBLISHED.value == "published"
        assert ContentStatus.ARCHIVED.value == "archived"
    
    def test_content_type_enum_values(self):
        """Test ContentType enum has expected values"""
        assert ContentType.DOCUMENT.value == "document"
        assert ContentType.SYLLABUS.value == "syllabus"
        assert ContentType.SLIDE.value == "slide"
        assert ContentType.LAB.value == "lab"
        assert ContentType.QUIZ.value == "quiz"
    
    def test_slide_type_enum_values(self):
        """Test SlideType enum has expected values"""
        assert SlideType.TITLE.value == "title"
        assert SlideType.CONTENT.value == "content"
        assert SlideType.BULLET_POINTS.value == "bullet_points"
        assert SlideType.IMAGE.value == "image"
        assert SlideType.CONCLUSION.value == "conclusion"
    
    def test_lab_type_enum_values(self):
        """Test LabType enum has expected values"""
        assert LabType.CODING.value == "coding"
        assert LabType.SIMULATION.value == "simulation"
        assert LabType.RESEARCH.value == "research"
        assert LabType.PROJECT.value == "project"
    
    def test_question_type_enum_values(self):
        """Test QuestionType enum has expected values"""
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.TRUE_FALSE.value == "true_false"
        assert QuestionType.SHORT_ANSWER.value == "short_answer"
        assert QuestionType.ESSAY.value == "essay"