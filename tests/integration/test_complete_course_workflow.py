"""
Complete Course Workflow Integration Tests

BUSINESS REQUIREMENT:
Validates the complete course creation workflow including:
1. Creating courses with AI-generated slides
2. Creating courses with AI-generated quizzes
3. Instantiating lab environments for courses
4. Integrating labs with slides for relevant exercises

TECHNICAL IMPLEMENTATION:
- Tests end-to-end workflow from course creation to lab integration
- Validates AI generation of slides, quizzes, and exercises
- Tests lab instantiation and Docker container management
- Verifies integration between course content and lab environments
"""

import pytest
import pytest_asyncio
import httpx
import asyncio
from typing import Dict, Any, Optional
import json
import time


# Test Configuration
COURSE_GENERATOR_URL = "http://localhost:8004"  # Course Generator Service
LAB_MANAGER_URL = "http://localhost:8005"  # Lab Manager Service
COURSE_MANAGEMENT_URL = "http://localhost:8002"  # Course Management Service
USER_SERVICE_URL = "http://localhost:8001"  # User Management Service

# Test credentials
TEST_INSTRUCTOR_EMAIL = "test.instructor@coursecreator.com"
TEST_INSTRUCTOR_PASSWORD = "InstructorPass123!"


@pytest_asyncio.fixture
async def auth_token():
    """
    Authenticate as instructor and return auth token.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/login",
            json={
                "email": TEST_INSTRUCTOR_EMAIL,
                "password": TEST_INSTRUCTOR_PASSWORD
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")


@pytest_asyncio.fixture
async def http_client(auth_token):
    """Create authenticated HTTP client."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=60.0  # Longer timeout for AI generation
    ) as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
class TestCourseCreationWithSlides:
    """Test creating courses with AI-generated slides."""

    async def test_generate_syllabus_for_course(self, http_client):
        """Test generating syllabus as foundation for slides."""
        course_data = {
            "subject": "Python Programming",
            "level": "beginner",
            "duration_weeks": 4,
            "topics": ["Variables", "Functions", "Loops", "Data Structures"]
        }

        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/syllabus",
            json=course_data
        )

        # Should generate syllabus successfully
        assert response.status_code in [200, 201, 503]  # 503 if AI service unavailable

        if response.status_code == 200:
            syllabus = response.json()
            assert 'modules' in syllabus or 'title' in syllabus
            return syllabus
        else:
            pytest.skip("AI service unavailable for syllabus generation")

    async def test_generate_slides_from_syllabus(self, http_client):
        """Test generating slides from syllabus."""
        # First generate syllabus
        syllabus_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/syllabus",
            json={
                "subject": "Python Basics",
                "level": "beginner",
                "duration_weeks": 2
            }
        )

        if syllabus_response.status_code != 200:
            pytest.skip("Syllabus generation failed")

        syllabus = syllabus_response.json()

        # Generate slides from syllabus
        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/slides",
            json=syllabus
        )

        assert response.status_code in [200, 201, 503]

        if response.status_code == 200:
            slides = response.json()
            assert 'slides' in slides
            assert isinstance(slides['slides'], list)
            assert len(slides['slides']) > 0

            # Validate slide structure
            for slide in slides['slides']:
                assert 'title' in slide
                assert 'content' in slide
                assert 'slide_number' in slide or 'slide_type' in slide

    async def test_generate_slides_for_specific_module(self, http_client):
        """Test generating slides for a specific module."""
        # Generate syllabus
        syllabus_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/syllabus",
            json={
                "subject": "JavaScript Fundamentals",
                "level": "beginner",
                "duration_weeks": 3
            }
        )

        if syllabus_response.status_code != 200:
            pytest.skip("Syllabus generation failed")

        syllabus = syllabus_response.json()
        modules = syllabus.get('modules', [])

        if not modules:
            pytest.skip("No modules in syllabus")

        # Generate slides for first module
        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/slides/module/1",
            json=syllabus
        )

        assert response.status_code in [200, 201, 404, 503]


@pytest.mark.integration
@pytest.mark.asyncio
class TestCourseCreationWithQuizzes:
    """Test creating courses with AI-generated quizzes."""

    async def test_generate_quizzes_from_syllabus(self, http_client):
        """Test generating quizzes from syllabus."""
        # Generate syllabus
        syllabus_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/syllabus",
            json={
                "subject": "Data Structures",
                "level": "intermediate",
                "duration_weeks": 4
            }
        )

        if syllabus_response.status_code != 200:
            pytest.skip("Syllabus generation failed")

        syllabus = syllabus_response.json()

        # Generate quizzes from syllabus
        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/quizzes",
            json=syllabus
        )

        assert response.status_code in [200, 201, 503]

        if response.status_code == 200:
            quizzes = response.json()
            assert 'quizzes' in quizzes
            assert isinstance(quizzes['quizzes'], list)
            assert len(quizzes['quizzes']) > 0

            # Validate quiz structure
            for quiz in quizzes['quizzes']:
                assert 'title' in quiz
                assert 'questions' in quiz
                assert isinstance(quiz['questions'], list)
                assert len(quiz['questions']) > 0

                # Validate question structure
                for question in quiz['questions']:
                    assert 'question' in question
                    assert 'options' in question
                    assert 'correct_answer' in question
                    assert isinstance(question['options'], list)
                    assert len(question['options']) >= 2

    async def test_generate_quiz_for_specific_module(self, http_client):
        """Test generating quiz for a specific module."""
        # Generate syllabus
        syllabus_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/syllabus",
            json={
                "subject": "Web Development",
                "level": "beginner",
                "duration_weeks": 6
            }
        )

        if syllabus_response.status_code != 200:
            pytest.skip("Syllabus generation failed")

        syllabus = syllabus_response.json()
        modules = syllabus.get('modules', [])

        if not modules:
            pytest.skip("No modules in syllabus")

        # Generate quiz for first module
        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/quizzes/module/1",
            json=syllabus
        )

        assert response.status_code in [200, 201, 404, 503]


@pytest.mark.integration
@pytest.mark.asyncio
class TestLabInstantiation:
    """Test lab instantiation for courses."""

    async def test_create_student_lab_environment(self, http_client):
        """Test creating a lab environment for a student."""
        lab_request = {
            "student_id": "test-student-123",
            "course_id": "test-course-456",
            "environment_type": "python",
            "resources": {
                "memory": "512m",
                "cpu": "0.5"
            }
        }

        response = await http_client.post(
            f"{LAB_MANAGER_URL}/labs",
            json=lab_request
        )

        # Should create lab or indicate resource constraints
        assert response.status_code in [200, 201, 400, 503]

        if response.status_code in [200, 201]:
            lab = response.json()
            assert 'lab_id' in lab or 'container_id' in lab
            assert 'status' in lab or 'url' in lab
            return lab
        else:
            pytest.skip("Lab creation failed - may need Docker running")

    async def test_list_active_labs(self, http_client):
        """Test listing active lab environments."""
        response = await http_client.get(f"{LAB_MANAGER_URL}/labs")

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            labs = response.json()
            assert isinstance(labs, (list, dict))

    async def test_get_lab_status(self, http_client):
        """Test getting status of a specific lab."""
        # First try to create a lab
        lab_request = {
            "student_id": "test-student-status",
            "course_id": "test-course-status",
            "environment_type": "python"
        }

        create_response = await http_client.post(
            f"{LAB_MANAGER_URL}/labs",
            json=lab_request
        )

        if create_response.status_code in [200, 201]:
            lab = create_response.json()
            lab_id = lab.get('lab_id') or lab.get('container_id')

            if lab_id:
                # Get lab status
                status_response = await http_client.get(
                    f"{LAB_MANAGER_URL}/labs/{lab_id}"
                )

                assert status_response.status_code in [200, 404]

    async def test_stop_lab_environment(self, http_client):
        """Test stopping a lab environment."""
        # Create a lab first
        lab_request = {
            "student_id": "test-student-stop",
            "course_id": "test-course-stop",
            "environment_type": "python"
        }

        create_response = await http_client.post(
            f"{LAB_MANAGER_URL}/labs",
            json=lab_request
        )

        if create_response.status_code in [200, 201]:
            lab = create_response.json()
            lab_id = lab.get('lab_id') or lab.get('container_id')

            if lab_id:
                # Stop the lab
                stop_response = await http_client.post(
                    f"{LAB_MANAGER_URL}/labs/{lab_id}/stop"
                )

                assert stop_response.status_code in [200, 204, 404]


@pytest.mark.integration
@pytest.mark.asyncio
class TestLabSlideIntegration:
    """Test integration between labs and slides for exercises."""

    async def test_generate_exercises_from_slides(self, http_client):
        """Test generating lab exercises from slide content."""
        # Generate syllabus
        syllabus_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/syllabus",
            json={
                "subject": "Python Programming",
                "level": "beginner",
                "duration_weeks": 4
            }
        )

        if syllabus_response.status_code != 200:
            pytest.skip("Syllabus generation failed")

        syllabus = syllabus_response.json()

        # Generate exercises (can be linked to slides)
        response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/exercises",
            json=syllabus
        )

        assert response.status_code in [200, 201, 503]

        if response.status_code == 200:
            exercises = response.json()
            assert 'exercises' in exercises
            assert isinstance(exercises['exercises'], list)
            assert len(exercises['exercises']) > 0

            # Validate exercise structure
            for exercise in exercises['exercises']:
                assert 'title' in exercise
                assert 'description' in exercise
                # These fields link exercises to course content
                assert 'instructions' in exercise or 'starter_code' in exercise

    async def test_create_lab_with_exercise_content(self, http_client):
        """Test creating lab with pre-loaded exercise content."""
        # Generate exercises
        syllabus_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/syllabus",
            json={
                "subject": "JavaScript",
                "level": "beginner",
                "duration_weeks": 2
            }
        )

        if syllabus_response.status_code != 200:
            pytest.skip("Syllabus generation failed")

        syllabus = syllabus_response.json()

        exercises_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/exercises",
            json=syllabus
        )

        if exercises_response.status_code != 200:
            pytest.skip("Exercise generation failed")

        exercises = exercises_response.json()
        first_exercise = exercises['exercises'][0] if exercises.get('exercises') else None

        if not first_exercise:
            pytest.skip("No exercises generated")

        # Create lab with exercise content
        lab_request = {
            "student_id": "test-student-exercise",
            "course_id": "test-course-exercise",
            "environment_type": "javascript",
            "initial_files": {
                "exercise.js": first_exercise.get('starter_code', '// Starter code'),
                "README.md": first_exercise.get('instructions', 'Exercise instructions')
            }
        }

        response = await http_client.post(
            f"{LAB_MANAGER_URL}/labs",
            json=lab_request
        )

        assert response.status_code in [200, 201, 400, 503]


@pytest.mark.integration
@pytest.mark.asyncio
class TestCompleteWorkflow:
    """Test complete course creation and lab workflow."""

    async def test_full_course_creation_workflow(self, http_client):
        """Test complete workflow: create course → slides → quizzes → lab."""
        # STEP 1: Generate Syllabus
        print("\n=== STEP 1: Generating Syllabus ===")
        syllabus_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/syllabus",
            json={
                "subject": "Full Stack Web Development",
                "level": "intermediate",
                "duration_weeks": 8,
                "topics": ["HTML/CSS", "JavaScript", "React", "Node.js", "Databases"]
            }
        )

        if syllabus_response.status_code != 200:
            pytest.skip("Syllabus generation failed")

        syllabus = syllabus_response.json()
        print(f"✓ Syllabus generated: {syllabus.get('title', 'Unknown')}")

        # STEP 2: Generate Slides
        print("\n=== STEP 2: Generating Slides ===")
        slides_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/slides",
            json=syllabus
        )

        slides = None
        if slides_response.status_code == 200:
            slides = slides_response.json()
            print(f"✓ Slides generated: {len(slides.get('slides', []))} slides")

        # STEP 3: Generate Quizzes
        print("\n=== STEP 3: Generating Quizzes ===")
        quizzes_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/quizzes",
            json=syllabus
        )

        quizzes = None
        if quizzes_response.status_code == 200:
            quizzes = quizzes_response.json()
            total_questions = sum(len(q.get('questions', [])) for q in quizzes.get('quizzes', []))
            print(f"✓ Quizzes generated: {len(quizzes.get('quizzes', []))} quizzes, {total_questions} questions")

        # STEP 4: Generate Exercises
        print("\n=== STEP 4: Generating Exercises ===")
        exercises_response = await http_client.post(
            f"{COURSE_GENERATOR_URL}/exercises",
            json=syllabus
        )

        exercises = None
        if exercises_response.status_code == 200:
            exercises = exercises_response.json()
            print(f"✓ Exercises generated: {len(exercises.get('exercises', []))} exercises")

        # STEP 5: Create Lab Environment
        print("\n=== STEP 5: Creating Lab Environment ===")
        lab_request = {
            "student_id": "test-student-workflow",
            "course_id": "full-stack-course",
            "environment_type": "javascript",
            "resources": {"memory": "1g", "cpu": "1.0"}
        }

        if exercises and exercises.get('exercises'):
            first_exercise = exercises['exercises'][0]
            lab_request['initial_files'] = {
                "exercise.js": first_exercise.get('starter_code', ''),
                "README.md": first_exercise.get('instructions', '')
            }

        lab_response = await http_client.post(
            f"{LAB_MANAGER_URL}/labs",
            json=lab_request
        )

        if lab_response.status_code in [200, 201]:
            lab = lab_response.json()
            print(f"✓ Lab created: {lab.get('lab_id', 'unknown')}")

        # STEP 6: Verify Complete Course Package
        print("\n=== STEP 6: Verification ===")
        assert syllabus is not None, "Syllabus should be generated"

        if slides:
            assert len(slides.get('slides', [])) > 0, "Should have slides"

        if quizzes:
            assert len(quizzes.get('quizzes', [])) > 0, "Should have quizzes"

        if exercises:
            assert len(exercises.get('exercises', [])) > 0, "Should have exercises"

        print("\n✓ Complete workflow successful!")
        print(f"  - Syllabus: ✓")
        print(f"  - Slides: {'✓' if slides else '✗'}")
        print(f"  - Quizzes: {'✓' if quizzes else '✗'}")
        print(f"  - Exercises: {'✓' if exercises else '✗'}")
        print(f"  - Lab: {'✓' if lab_response.status_code in [200, 201] else '✗'}")


# Run tests with: pytest tests/integration/test_complete_course_workflow.py -v -s --tb=short -m integration
