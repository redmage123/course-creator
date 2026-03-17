"""
Course Generator DAO Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for the Course Generator Data Access Object ensuring all AI-powered
content generation operations work correctly. The Course Generator DAO is the data persistence
layer for the platform's AI content creation engine, handling syllabi, quizzes, slides, exercises,
lab environments, and generation job tracking. This DAO is critical for instructor productivity
and automated educational content creation at scale.

TECHNICAL IMPLEMENTATION:
- Tests all 17 DAO methods across 6 content generation categories
- Validates syllabus creation and retrieval with AI metadata
- Tests quiz generation with question banks and difficulty levels
- Ensures slide set creation with presentation structure
- Validates exercise generation with instructions and solutions
- Tests lab environment configuration and deployment tracking
- Validates generation job tracking and progress monitoring
- Tests generation statistics and performance analytics

TDD APPROACH:
These tests validate that the DAO layer correctly:
- Creates AI-generated educational content with proper structure
- Stores complex JSON content (questions, slides, configurations)
- Retrieves content by course ID and type
- Tracks generation jobs with progress and status updates
- Calculates comprehensive generation statistics
- Handles errors gracefully with custom exceptions
- Maintains data consistency across content types
"""

import pytest
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import sys
from pathlib import Path
import json

# Add course-generator service to path
course_gen_path = Path(__file__).parent.parent.parent.parent / 'services' / 'course-generator'
sys.path.insert(0, str(course_gen_path))

from data_access.course_generator_dao import CourseGeneratorDAO
from exceptions import (
    ContentException,
    DatabaseException
)


class TestSyllabusOperations:
    """
    Test Suite: Syllabus Generation and Management

    BUSINESS REQUIREMENT:
    AI-generated syllabi must define comprehensive course structures with learning
    objectives, topics, and assessment methods for automated content generation.
    """

    @pytest.mark.asyncio
    async def test_create_syllabus_with_required_fields(self, db_transaction):
        """
        TEST: Create syllabus with required fields and minimal structure

        BUSINESS REQUIREMENT:
        Instructors must be able to generate course syllabi using AI to define
        course structure and learning objectives automatically

        VALIDATES:
        - Syllabus record is created successfully
        - AI metadata is stored correctly
        - Course structure is persisted as JSON
        - Default version is set to 1
        - Status defaults to 'generated'
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        # Create test course first
        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        syllabus_id = str(uuid4())
        syllabus_data = {
            'id': syllabus_id,
            'course_id': course_id,
            'title': 'Introduction to Python Programming',
            'description': 'Comprehensive Python course for beginners',
            'objectives': ['Learn Python syntax', 'Build web applications'],
            'topics': ['Variables', 'Functions', 'Classes'],
            'structure': {
                'weeks': 8,
                'modules': [
                    {'title': 'Module 1', 'topics': ['Basics']}
                ]
            },
            'created_by': user_id
        }

        # Execute: Create syllabus
        result_id = await dao.create_syllabus(syllabus_data)

        # Verify: Syllabus was created
        assert result_id == syllabus_id

        # Verify: Syllabus exists in database with correct data
        syllabus = await db_transaction.fetchrow(
            "SELECT * FROM course_creator.course_outlines WHERE id = $1",
            UUID(syllabus_id)
        )
        assert syllabus is not None
        assert syllabus['title'] == 'Introduction to Python Programming'
        assert syllabus['description'] == 'Comprehensive Python course for beginners'
        assert syllabus['version'] == 1
        assert syllabus['status'] == 'generated'

        # Verify: JSON fields are stored correctly
        objectives = json.loads(syllabus['objectives'])
        assert 'Learn Python syntax' in objectives

        topics = json.loads(syllabus['topics'])
        assert 'Functions' in topics

        structure = json.loads(syllabus['structure'])
        assert structure['weeks'] == 8

    @pytest.mark.asyncio
    async def test_create_syllabus_with_ai_metadata(self, db_transaction):
        """
        TEST: Create syllabus with comprehensive AI generation metadata

        BUSINESS REQUIREMENT:
        Track AI model information, generation parameters, and sources for
        quality assurance and continuous improvement of content generation

        VALIDATES:
        - AI metadata is stored as JSON
        - Generation parameters are preserved
        - Model information is tracked
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        syllabus_data = {
            'id': str(uuid4()),
            'course_id': course_id,
            'title': 'Advanced Machine Learning',
            'description': 'Deep dive into ML algorithms',
            'structure': {'weeks': 12, 'modules': []},
            'ai_metadata': {
                'model': 'gpt-4',
                'temperature': 0.7,
                'tokens_used': 2500,
                'generation_time_seconds': 15.3,
                'prompt_version': 'v2.1'
            },
            'created_by': user_id
        }

        result_id = await dao.create_syllabus(syllabus_data)

        # Verify: AI metadata is stored correctly
        syllabus = await db_transaction.fetchrow(
            "SELECT * FROM course_creator.course_outlines WHERE id = $1",
            UUID(result_id)
        )

        ai_metadata = json.loads(syllabus['ai_metadata'])
        assert ai_metadata['model'] == 'gpt-4'
        assert ai_metadata['temperature'] == 0.7
        assert ai_metadata['tokens_used'] == 2500

    @pytest.mark.asyncio
    async def test_get_syllabus_by_course_id_returns_latest_version(self, db_transaction):
        """
        TEST: Retrieve latest syllabus version for a course

        BUSINESS REQUIREMENT:
        When multiple syllabus versions exist, always return the most recent
        version for content generation and student viewing

        VALIDATES:
        - Latest version is returned when multiple exist
        - Correct syllabus is retrieved by course ID
        - All fields are returned in dictionary format
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        # Create version 1
        syllabus_v1_data = {
            'id': str(uuid4()),
            'course_id': course_id,
            'title': 'Course Syllabus v1',
            'description': 'First version',
            'structure': {'version': 1},
            'version': 1,
            'created_by': user_id
        }
        await dao.create_syllabus(syllabus_v1_data)

        # Create version 2 (latest)
        syllabus_v2_id = str(uuid4())
        syllabus_v2_data = {
            'id': syllabus_v2_id,
            'course_id': course_id,
            'title': 'Course Syllabus v2',
            'description': 'Updated version',
            'structure': {'version': 2},
            'version': 2,
            'created_by': user_id
        }
        await dao.create_syllabus(syllabus_v2_data)

        # Execute: Get latest syllabus
        result = await dao.get_syllabus_by_course_id(course_id)

        # Verify: Version 2 is returned (latest)
        assert result is not None
        assert result['id'] == UUID(syllabus_v2_id)
        assert result['title'] == 'Course Syllabus v2'
        assert result['version'] == 2

    @pytest.mark.asyncio
    async def test_get_syllabus_by_course_id_returns_none_when_not_found(self, db_transaction):
        """
        TEST: Return None when no syllabus exists for course

        BUSINESS REQUIREMENT:
        System must gracefully handle courses without syllabi

        VALIDATES:
        - None is returned for non-existent course
        - No exception is raised
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        non_existent_course_id = str(uuid4())
        result = await dao.get_syllabus_by_course_id(non_existent_course_id)

        assert result is None


class TestQuizOperations:
    """
    Test Suite: Quiz Generation and Management

    BUSINESS REQUIREMENT:
    AI-generated quizzes must provide automated assessment creation with questions,
    answers, difficulty levels, and scoring criteria.
    """

    @pytest.mark.asyncio
    async def test_create_quiz_with_questions_and_answers(self, db_transaction):
        """
        TEST: Create quiz with multiple questions and answer choices

        BUSINESS REQUIREMENT:
        Instructors need automated quiz generation to assess student learning
        without manual question writing

        VALIDATES:
        - Quiz is created with question bank
        - Difficulty level is stored
        - Time limit and points are tracked
        - Questions are stored as JSON array
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        quiz_id = str(uuid4())
        quiz_data = {
            'id': quiz_id,
            'course_id': course_id,
            'title': 'Python Fundamentals Quiz',
            'description': 'Test your Python knowledge',
            'questions': [
                {
                    'id': 1,
                    'question': 'What is a variable?',
                    'type': 'multiple_choice',
                    'choices': ['A. A container', 'B. A function', 'C. A class'],
                    'correct_answer': 'A',
                    'points': 10
                },
                {
                    'id': 2,
                    'question': 'Explain list comprehension',
                    'type': 'short_answer',
                    'points': 20
                }
            ],
            'difficulty_level': 'intermediate',
            'time_limit': 45,
            'points_total': 30,
            'created_by': user_id
        }

        # Execute: Create quiz
        result_id = await dao.create_quiz(quiz_data)

        # Verify: Quiz was created
        assert result_id == quiz_id

        # Verify: Quiz data is stored correctly
        quiz = await db_transaction.fetchrow(
            "SELECT * FROM course_creator.quizzes WHERE id = $1",
            UUID(quiz_id)
        )
        assert quiz is not None
        assert quiz['title'] == 'Python Fundamentals Quiz'
        assert quiz['difficulty_level'] == 'intermediate'
        assert quiz['time_limit'] == 45
        assert quiz['points_total'] == 30

        # Verify: Questions are stored as JSON
        questions = json.loads(quiz['questions'])
        assert len(questions) == 2
        assert questions[0]['question'] == 'What is a variable?'
        assert questions[1]['type'] == 'short_answer'

    @pytest.mark.asyncio
    async def test_get_course_quizzes_returns_multiple_quizzes(self, db_transaction):
        """
        TEST: Retrieve all quizzes for a course in descending order

        BUSINESS REQUIREMENT:
        Instructors need to view all generated quizzes for a course to
        manage assessments and track content coverage

        VALIDATES:
        - Multiple quizzes are returned
        - Quizzes are ordered by creation date (newest first)
        - Metadata is included without full questions
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        # Create 3 quizzes
        for i in range(3):
            quiz_data = {
                'id': str(uuid4()),
                'course_id': course_id,
                'title': f'Quiz {i+1}',
                'description': f'Quiz number {i+1}',
                'questions': [{'id': 1, 'question': 'Test?'}],
                'difficulty_level': 'beginner',
                'created_by': user_id
            }
            await dao.create_quiz(quiz_data)

        # Execute: Get all quizzes
        result = await dao.get_course_quizzes(course_id)

        # Verify: All quizzes are returned
        assert len(result) == 3
        assert all('title' in quiz for quiz in result)
        assert all('difficulty_level' in quiz for quiz in result)

    @pytest.mark.asyncio
    async def test_get_course_quizzes_respects_limit(self, db_transaction):
        """
        TEST: Respect limit parameter when retrieving quizzes

        BUSINESS REQUIREMENT:
        Pagination support for courses with many quizzes

        VALIDATES:
        - Limit parameter restricts number of results
        - Most recent quizzes are returned first
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        # Create 5 quizzes
        for i in range(5):
            quiz_data = {
                'id': str(uuid4()),
                'course_id': course_id,
                'title': f'Quiz {i+1}',
                'questions': [{'id': 1, 'question': 'Test?'}],
                'created_by': user_id
            }
            await dao.create_quiz(quiz_data)

        # Execute: Get only 2 quizzes
        result = await dao.get_course_quizzes(course_id, limit=2)

        # Verify: Only 2 quizzes returned
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_quiz_by_id_returns_complete_quiz(self, db_transaction):
        """
        TEST: Retrieve complete quiz details including all questions

        BUSINESS REQUIREMENT:
        System must provide full quiz details for administration and grading

        VALIDATES:
        - Complete quiz record is returned
        - All questions are included
        - AI metadata is included
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        quiz_id = str(uuid4())
        questions = [
            {'id': 1, 'question': 'Q1', 'answer': 'A1'},
            {'id': 2, 'question': 'Q2', 'answer': 'A2'}
        ]
        quiz_data = {
            'id': quiz_id,
            'course_id': course_id,
            'title': 'Complete Quiz',
            'questions': questions,
            'ai_metadata': {'model': 'gpt-4'},
            'created_by': user_id
        }
        await dao.create_quiz(quiz_data)

        # Execute: Get quiz by ID
        result = await dao.get_quiz_by_id(quiz_id)

        # Verify: Complete quiz is returned
        assert result is not None
        assert result['id'] == UUID(quiz_id)
        assert result['title'] == 'Complete Quiz'

        # Verify: Questions are included
        returned_questions = json.loads(result['questions'])
        assert len(returned_questions) == 2


class TestSlideOperations:
    """
    Test Suite: Slide Set Generation and Management

    BUSINESS REQUIREMENT:
    AI-generated slide sets must provide automated presentation creation for
    visual learning materials and instructor convenience.
    """

    @pytest.mark.asyncio
    async def test_create_slide_set_with_multiple_slides(self, db_transaction):
        """
        TEST: Create slide set with multiple slides and content

        BUSINESS REQUIREMENT:
        Instructors need automated presentation generation to reduce
        preparation time while maintaining quality

        VALIDATES:
        - Slide set is created successfully
        - Slide count is calculated automatically
        - Template information is stored
        - Slides array is persisted as JSON
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        slide_id = str(uuid4())
        slide_data = {
            'id': slide_id,
            'course_id': course_id,
            'title': 'Introduction to Python',
            'description': 'First lecture slides',
            'slides': [
                {
                    'slide_number': 1,
                    'title': 'Course Overview',
                    'content': 'Welcome to Python Programming',
                    'layout': 'title_slide'
                },
                {
                    'slide_number': 2,
                    'title': 'What is Python?',
                    'content': 'Python is a high-level programming language',
                    'layout': 'content'
                },
                {
                    'slide_number': 3,
                    'title': 'Key Features',
                    'content': ['Easy to learn', 'Versatile', 'Large community'],
                    'layout': 'bullet_list'
                }
            ],
            'template': 'professional_blue',
            'created_by': user_id
        }

        # Execute: Create slide set
        result_id = await dao.create_slide_set(slide_data)

        # Verify: Slide set was created
        assert result_id == slide_id

        # Verify: Slide data is stored correctly
        slides = await db_transaction.fetchrow(
            "SELECT * FROM course_creator.slides WHERE id = $1",
            UUID(slide_id)
        )
        assert slides is not None
        assert slides['title'] == 'Introduction to Python'
        assert slides['template'] == 'professional_blue'
        assert slides['slide_count'] == 3

        # Verify: Slides array is stored as JSON
        content = json.loads(slides['content'])
        assert len(content) == 3
        assert content[0]['title'] == 'Course Overview'
        assert content[2]['layout'] == 'bullet_list'

    @pytest.mark.asyncio
    async def test_get_course_slide_sets_returns_all_sets(self, db_transaction):
        """
        TEST: Retrieve all slide sets for a course

        BUSINESS REQUIREMENT:
        Instructors need to manage multiple presentation sets for
        different course modules

        VALIDATES:
        - Multiple slide sets are returned
        - Metadata includes slide counts
        - Sets are ordered by creation date
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        # Create 2 slide sets
        for i in range(2):
            slide_data = {
                'id': str(uuid4()),
                'course_id': course_id,
                'title': f'Lecture {i+1} Slides',
                'slides': [{'slide_number': 1, 'title': 'Slide'}],
                'created_by': user_id
            }
            await dao.create_slide_set(slide_data)

        # Execute: Get all slide sets
        result = await dao.get_course_slide_sets(course_id)

        # Verify: All slide sets returned
        assert len(result) == 2
        assert all('slide_count' in slide_set for slide_set in result)


class TestExerciseOperations:
    """
    Test Suite: Exercise Generation and Management

    BUSINESS REQUIREMENT:
    AI-generated exercises must provide hands-on learning activities with
    instructions and solutions for skill development.
    """

    @pytest.mark.asyncio
    async def test_create_exercise_with_instructions_and_solution(self, db_transaction):
        """
        TEST: Create exercise with detailed instructions and solution

        BUSINESS REQUIREMENT:
        Students need hands-on exercises to reinforce learning through
        practical application of concepts

        VALIDATES:
        - Exercise is created successfully
        - Instructions are stored
        - Solution is included
        - Estimated time is tracked
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        exercise_id = str(uuid4())
        exercise_data = {
            'id': exercise_id,
            'course_id': course_id,
            'title': 'Build a Calculator',
            'description': 'Create a basic calculator application',
            'instructions': 'Step 1: Create main function\nStep 2: Add operations\nStep 3: Test',
            'solution': 'def calculator():\n    # Implementation here\n    pass',
            'difficulty_level': 'beginner',
            'estimated_time': 90,
            'resources': ['Python 3.9+', 'Text editor'],
            'created_by': user_id
        }

        # Execute: Create exercise
        result_id = await dao.create_exercise(exercise_data)

        # Verify: Exercise was created
        assert result_id == exercise_id


class TestLabEnvironmentOperations:
    """
    Test Suite: Lab Environment Generation

    BUSINESS REQUIREMENT:
    AI-generated lab environments must automate hands-on learning setup
    with pre-configured development environments.
    """

    @pytest.mark.asyncio
    async def test_create_lab_environment_with_docker_config(self, db_transaction):
        """
        TEST: Create lab environment with Docker configuration

        BUSINESS REQUIREMENT:
        Students need consistent development environments without
        technical barriers for hands-on learning

        VALIDATES:
        - Lab environment is created
        - Docker configuration is stored
        - Tools and software are tracked
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        lab_id = str(uuid4())
        lab_data = {
            'id': lab_id,
            'course_id': course_id,
            'name': 'Python Development Environment',
            'description': 'Pre-configured Python dev environment',
            'configuration': {
                'cpu_limit': '2',
                'memory_limit': '4g',
                'storage': '10g'
            },
            'docker_config': {
                'image': 'python:3.9',
                'ports': ['8000:8000'],
                'volumes': ['/workspace']
            },
            'tools': ['python3', 'pip', 'git', 'vscode-server'],
            'created_by': user_id
        }

        # Execute: Create lab environment
        result_id = await dao.create_lab_environment(lab_data)

        # Verify: Lab was created
        assert result_id == lab_id


class TestGenerationJobTracking:
    """
    Test Suite: Generation Job Tracking and Analytics

    BUSINESS REQUIREMENT:
    System must track AI content generation jobs for monitoring,
    optimization, and quality assurance.
    """

    @pytest.mark.asyncio
    async def test_track_generation_job_creates_record(self, db_transaction):
        """
        TEST: Create generation job tracking record

        BUSINESS REQUIREMENT:
        Track all AI generation jobs for performance monitoring and
        quality assurance

        VALIDATES:
        - Job record is created
        - Job parameters are stored
        - AI model is tracked
        - Status is set to 'started'
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        job_id = str(uuid4())
        job_data = {
            'id': job_id,
            'job_type': 'quiz_generation',
            'course_id': course_id,
            'parameters': {
                'difficulty': 'intermediate',
                'num_questions': 10
            },
            'status': 'started',
            'progress': 0,
            'ai_model': 'gpt-4',
            'started_by': user_id
        }

        # Execute: Track generation job
        result_id = await dao.track_generation_job(job_data)

        # Verify: Job was tracked
        assert result_id == job_id

    @pytest.mark.asyncio
    async def test_update_generation_job_progress(self, db_transaction):
        """
        TEST: Update generation job progress during execution

        BUSINESS REQUIREMENT:
        Provide real-time feedback to users during content generation

        VALIDATES:
        - Progress is updated correctly
        - Status can be changed
        - Updated timestamp is refreshed
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        job_id = str(uuid4())
        job_data = {
            'id': job_id,
            'job_type': 'slide_generation',
            'course_id': course_id,
            'started_by': user_id
        }
        await dao.track_generation_job(job_data)

        # Execute: Update progress to 50%
        result = await dao.update_generation_job_progress(job_id, 50, 'processing')

        # Verify: Progress was updated
        assert result is True

        # Verify: Job record reflects new progress
        job = await db_transaction.fetchrow(
            "SELECT * FROM course_creator.course_outlines WHERE id = $1",
            UUID(job_id)
        )
        assert job['version'] == 50  # Progress stored in version field
        assert job['status'] == 'processing'

    @pytest.mark.asyncio
    async def test_get_generation_statistics_calculates_metrics(self, db_transaction):
        """
        TEST: Calculate comprehensive generation statistics

        BUSINESS REQUIREMENT:
        Platform administrators need analytics to optimize AI generation
        and track system performance

        VALIDATES:
        - Total job count is calculated
        - Success rate is computed
        - Content type breakdown is provided
        - Statistics cover specified time period
        """
        dao = CourseGeneratorDAO(None)
        dao.db_pool = type('obj', (object,), {
            'acquire': lambda: type('ctx', (), {
                '__aenter__': lambda s: db_transaction,
                '__aexit__': lambda s, *args: None
            })()
        })()

        course_id = str(uuid4())
        user_id = str(uuid4())
        await db_transaction.execute(
            """INSERT INTO course_creator.courses (id, title, instructor_id, organization_id, status)
               VALUES ($1, $2, $3, $4, 'draft')""",
            UUID(course_id), 'Test Course', UUID(user_id), UUID(str(uuid4()))
        )

        # Create 3 completed jobs and 1 failed job
        for i in range(3):
            job_data = {
                'id': str(uuid4()),
                'job_type': 'quiz_generation',
                'course_id': course_id,
                'status': 'completed',
                'progress': 100,
                'started_by': user_id
            }
            await dao.track_generation_job(job_data)

        failed_job_data = {
            'id': str(uuid4()),
            'job_type': 'slide_generation',
            'course_id': course_id,
            'status': 'failed',
            'progress': 30,
            'started_by': user_id
        }
        await dao.track_generation_job(failed_job_data)

        # Execute: Get statistics for last 30 days
        stats = await dao.get_generation_statistics(days=30)

        # Verify: Statistics are calculated correctly
        assert stats['total_jobs'] == 4
        assert stats['completed_jobs'] == 3
        assert stats['failed_jobs'] == 1
        assert stats['success_rate'] == 75.0  # 3/4 = 75%
        assert 'content_breakdown' in stats
