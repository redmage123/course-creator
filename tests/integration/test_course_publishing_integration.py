"""
Integration tests for the course publishing system.
Tests the interaction between different components and services.
"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
import uuid
import os
import asyncpg

# Test configuration
TEST_CONFIG = {
    'BASE_URL': 'http://localhost:8004',
    'DATABASE_URL': os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:postgres_password@localhost:5433/course_creator_test')
}

@pytest.fixture(scope='session')
async def test_db_pool():
    """Create test database connection pool."""
    pool = await asyncpg.create_pool(TEST_CONFIG['DATABASE_URL'])
    yield pool
    await pool.close()

@pytest.fixture
async def clean_db(test_db_pool):
    """Clean database before each test."""
    async with test_db_pool.acquire() as conn:
        # Clean up test data in reverse dependency order
        await conn.execute("DELETE FROM quiz_publications WHERE course_instance_id IN (SELECT id FROM course_instances WHERE instance_name LIKE 'TEST_%')")
        await conn.execute("DELETE FROM student_course_enrollments WHERE course_instance_id IN (SELECT id FROM course_instances WHERE instance_name LIKE 'TEST_%')")
        await conn.execute("DELETE FROM course_instances WHERE instance_name LIKE 'TEST_%'")
        await conn.execute("DELETE FROM courses WHERE title LIKE 'TEST_%'")
        await conn.execute("DELETE FROM users WHERE email LIKE '%@test.example.com'")
    yield
    # Cleanup after test
    async with test_db_pool.acquire() as conn:
        await conn.execute("DELETE FROM quiz_publications WHERE course_instance_id IN (SELECT id FROM course_instances WHERE instance_name LIKE 'TEST_%')")
        await conn.execute("DELETE FROM student_course_enrollments WHERE course_instance_id IN (SELECT id FROM course_instances WHERE instance_name LIKE 'TEST_%')")
        await conn.execute("DELETE FROM course_instances WHERE instance_name LIKE 'TEST_%'")
        await conn.execute("DELETE FROM courses WHERE title LIKE 'TEST_%'")
        await conn.execute("DELETE FROM users WHERE email LIKE '%@test.example.com'")

@pytest.fixture
async def test_instructor(test_db_pool):
    """Create test instructor user."""
    instructor_id = str(uuid.uuid4())
    async with test_db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, email, password_hash, full_name, role, is_active, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, instructor_id, 'instructor@test.example.com', 'hashed_password', 
            'Test Instructor', 'instructor', True, datetime.utcnow())
    
    return instructor_id

@pytest.fixture
async def test_course(test_db_pool, test_instructor):
    """Create test course."""
    course_id = str(uuid.uuid4())
    async with test_db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO courses (id, title, description, instructor_id, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, course_id, 'TEST_Integration_Course', 'Test course description', 
            test_instructor, 'draft', datetime.utcnow())
    
    return course_id

@pytest.fixture
async def published_course(test_db_pool, test_course, test_instructor):
    """Create published test course."""
    async with test_db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE courses 
            SET status = 'published', visibility = 'public', published_at = $1
            WHERE id = $2
        """, datetime.utcnow(), test_course)
    
    return test_course

@pytest.fixture
async def mock_auth_token():
    """Mock authentication token."""
    return "test_jwt_token"

@pytest.fixture
def mock_get_current_user(test_instructor):
    pytest.skip("Needs refactoring to use real objects")

@pytest.mark.skip(reason="Needs refactoring to use real objects")
class TestCoursePublishingIntegration:
    """Integration tests for course publishing workflow."""

    @pytest.mark.asyncio
    async def test_course_publishing_workflow(self, clean_db, test_course, test_instructor, mock_auth_token):
        """Test complete course publishing workflow."""
        async with httpx.AsyncClient() as client:
            # Mock authentication
            headers = {'Authorization': f'Bearer {mock_auth_token}'}
            
            with patch('services.course_management.main.get_current_user') as mock_auth:
                mock_auth.return_value = {
                    'user_id': test_instructor,
                    'email': 'instructor@test.example.com',
                    'role': 'instructor'
                }
                
                # Step 1: Publish course
                publish_data = {
                    'visibility': 'public',
                    'description': 'Updated course description'
                }
                
                response = await client.post(
                    f"{TEST_CONFIG['BASE_URL']}/courses/{test_course}/publish",
                    json=publish_data,
                    headers=headers
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result['success'] == True
                assert 'course' in result
                
                # Step 2: Verify course is published
                # This would require a GET endpoint to verify the course status
                # For now, we'll check the database directly
                
        # Verify in database
        async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
            course = await conn.fetchrow(
                "SELECT * FROM courses WHERE id = $1", test_course
            )
            assert course['status'] == 'published'
            assert course['visibility'] == 'public'
            assert course['published_at'] is not None

    @pytest.mark.asyncio
    async def test_course_instance_creation_workflow(self, clean_db, published_course, test_instructor, mock_auth_token):
        """Test course instance creation workflow."""
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {mock_auth_token}'}
            
            with patch('services.course_management.main.get_current_user') as mock_auth:
                mock_auth.return_value = {
                    'user_id': test_instructor,
                    'email': 'instructor@test.example.com',
                    'role': 'instructor'
                }
                
                # Create course instance
                instance_data = {
                    'course_id': published_course,
                    'instance_name': 'TEST_Fall_2024',
                    'start_datetime': (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    'end_datetime': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    'timezone': 'UTC',
                    'max_students': 25,
                    'description': 'Test instance description'
                }
                
                response = await client.post(
                    f"{TEST_CONFIG['BASE_URL']}/course-instances",
                    json=instance_data,
                    headers=headers
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result['success'] == True
                assert 'instance' in result
                
                instance_id = result['instance']['id']
                
                # Verify in database
                async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
                    instance = await conn.fetchrow(
                        "SELECT * FROM course_instances WHERE id = $1", instance_id
                    )
                    assert instance['instance_name'] == 'TEST_Fall_2024'
                    assert instance['max_students'] == 25
                    assert instance['status'] == 'scheduled'

    @pytest.mark.asyncio
    async def test_student_enrollment_workflow(self, clean_db, published_course, test_instructor, mock_auth_token):
        """Test complete student enrollment workflow."""
        # First create course instance
        async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
            instance_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO course_instances (
                    id, course_id, instance_name, start_datetime, end_datetime,
                    timezone, max_students, instructor_id, status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, instance_id, published_course, 'TEST_Enrollment_Instance',
                datetime.utcnow() + timedelta(days=1),
                datetime.utcnow() + timedelta(days=30),
                'UTC', 30, test_instructor, 'scheduled', datetime.utcnow())
        
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {mock_auth_token}'}
            
            with patch('services.course_management.main.get_current_user') as mock_auth:
                mock_auth.return_value = {
                    'user_id': test_instructor,
                    'email': 'instructor@test.example.com',
                    'role': 'instructor'
                }
                
                # Enroll student
                enrollment_data = {
                    'student_email': 'student@test.example.com',
                    'student_first_name': 'John',
                    'student_last_name': 'Doe',
                    'send_welcome_email': True
                }
                
                response = await client.post(
                    f"{TEST_CONFIG['BASE_URL']}/course-instances/{instance_id}/enroll",
                    json=enrollment_data,
                    headers=headers
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result['success'] == True
                assert 'enrollment' in result
                
                enrollment = result['enrollment']
                assert enrollment['student_email'] == 'student@test.example.com'
                assert enrollment['student_first_name'] == 'John'
                assert enrollment['student_last_name'] == 'Doe'
                assert 'unique_access_url' in enrollment
                assert 'access_token' in enrollment
                
                # Verify in database
                async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
                    db_enrollment = await conn.fetchrow(
                        "SELECT * FROM student_course_enrollments WHERE student_email = $1",
                        'student@test.example.com'
                    )
                    assert db_enrollment is not None
                    assert db_enrollment['enrollment_status'] == 'enrolled'
                    assert db_enrollment['access_token'] is not None
                    assert len(db_enrollment['access_token']) == 32

    @pytest.mark.asyncio 
    async def test_student_authentication_workflow(self, clean_db, published_course, test_instructor):
        """Test student authentication workflow."""
        # Setup: Create enrollment with known credentials
        instance_id = str(uuid.uuid4())
        enrollment_id = str(uuid.uuid4())
        access_token = 'test_token_12345678901234567890'  # 32 chars
        temp_password = 'TempPass123!'
        
        # Hash the password (simulate the service behavior)
        from services.course_management.course_publishing_api import CoursePublishingService
        import asyncpg
        
        # Create a temporary service instance to hash password
        test_pool = await asyncpg.create_pool(TEST_CONFIG['DATABASE_URL'])
        service = CoursePublishingService(test_pool)
        hashed_password = service.hash_password(temp_password)
        
        async with test_pool.acquire() as conn:
            # Create course instance
            await conn.execute("""
                INSERT INTO course_instances (
                    id, course_id, instance_name, start_datetime, end_datetime,
                    timezone, max_students, instructor_id, status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, instance_id, published_course, 'TEST_Auth_Instance',
                datetime.utcnow() - timedelta(days=1),  # Started yesterday
                datetime.utcnow() + timedelta(days=30), # Ends in 30 days
                'UTC', 30, test_instructor, 'active', datetime.utcnow())
            
            # Create enrollment
            await conn.execute("""
                INSERT INTO student_course_enrollments (
                    id, course_instance_id, student_email, student_first_name,
                    student_last_name, unique_access_url, access_token,
                    temporary_password, enrolled_by, enrollment_status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, enrollment_id, instance_id, 'auth.test@test.example.com',
                'Jane', 'Smith', f'http://localhost:3000/student-login?token={access_token}',
                access_token, hashed_password, test_instructor, 'enrolled', datetime.utcnow())
        
        await test_pool.close()
        
        # Test authentication
        async with httpx.AsyncClient() as client:
            # Test successful authentication
            auth_data = {
                'access_token': access_token,
                'password': temp_password
            }
            
            response = await client.post(
                f"{TEST_CONFIG['BASE_URL']}/student/auth/login",
                json=auth_data
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result['success'] == True
            assert 'student' in result
            
            student_data = result['student']
            assert student_data['student_email'] == 'auth.test@test.example.com'
            assert student_data['student_name'] == 'Jane Smith'
            assert student_data['access_token'] == access_token
            
            # Test getting course data
            response = await client.get(
                f"{TEST_CONFIG['BASE_URL']}/student/course-data",
                params={'token': access_token}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result['success'] == True
            assert 'data' in result
            
            course_data = result['data']
            assert 'enrollment' in course_data
            assert 'course' in course_data
            assert 'instance' in course_data
            assert 'slides' in course_data
            assert 'quizzes' in course_data

    @pytest.mark.asyncio
    async def test_student_password_update_workflow(self, clean_db, published_course, test_instructor):
        """Test student password update workflow."""
        # Setup enrollment with known credentials
        instance_id = str(uuid.uuid4())
        enrollment_id = str(uuid.uuid4())
        access_token = 'pwd_update_token_1234567890123'  # 32 chars
        current_password = 'CurrentPass123!'
        new_password = 'NewSecurePass123!'
        
        # Setup database
        test_pool = await asyncpg.create_pool(TEST_CONFIG['DATABASE_URL'])
        service = CoursePublishingService(test_pool)
        hashed_current = service.hash_password(current_password)
        
        async with test_pool.acquire() as conn:
            # Create course instance
            await conn.execute("""
                INSERT INTO course_instances (
                    id, course_id, instance_name, start_datetime, end_datetime,
                    timezone, max_students, instructor_id, status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, instance_id, published_course, 'TEST_Password_Instance',
                datetime.utcnow() - timedelta(days=1),
                datetime.utcnow() + timedelta(days=30),
                'UTC', 30, test_instructor, 'active', datetime.utcnow())
            
            # Create enrollment
            await conn.execute("""
                INSERT INTO student_course_enrollments (
                    id, course_instance_id, student_email, student_first_name,
                    student_last_name, unique_access_url, access_token,
                    temporary_password, enrolled_by, enrollment_status, 
                    password_reset_required, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, enrollment_id, instance_id, 'pwd.test@test.example.com',
                'Bob', 'Johnson', f'http://localhost:3000/student-login?token={access_token}',
                access_token, hashed_current, test_instructor, 'enrolled', 
                True, datetime.utcnow())
        
        await test_pool.close()
        
        # Test password update
        async with httpx.AsyncClient() as client:
            update_data = {
                'access_token': access_token,
                'current_password': current_password,
                'new_password': new_password
            }
            
            response = await client.post(
                f"{TEST_CONFIG['BASE_URL']}/student/password/update",
                json=update_data
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result['success'] == True
            
            # Verify password was updated in database
            async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
                enrollment = await conn.fetchrow(
                    "SELECT * FROM student_course_enrollments WHERE access_token = $1",
                    access_token
                )
                assert enrollment['password_reset_required'] == False
                
                # Verify new password works
                service = CoursePublishingService(None)  # Just for password verification
                assert service.verify_password(new_password, enrollment['temporary_password']) == True

    @pytest.mark.asyncio
    async def test_quiz_publishing_workflow(self, clean_db, published_course, test_instructor, mock_auth_token):
        """Test quiz publishing workflow."""
        # Setup: Create course instance and quiz
        quiz_id = str(uuid.uuid4())
        instance_id = str(uuid.uuid4())
        
        async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
            # Create quiz
            await conn.execute("""
                INSERT INTO quizzes (id, title, description, course_id, instructor_id, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, quiz_id, 'TEST_Integration_Quiz', 'Test quiz description',
                published_course, test_instructor, datetime.utcnow())
            
            # Create course instance
            await conn.execute("""
                INSERT INTO course_instances (
                    id, course_id, instance_name, start_datetime, end_datetime,
                    timezone, max_students, instructor_id, status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, instance_id, published_course, 'TEST_Quiz_Instance',
                datetime.utcnow() + timedelta(days=1),
                datetime.utcnow() + timedelta(days=30),
                'UTC', 30, test_instructor, 'scheduled', datetime.utcnow())
        
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {mock_auth_token}'}
            
            with patch('services.course_management.main.get_current_user') as mock_auth:
                mock_auth.return_value = {
                    'user_id': test_instructor,
                    'email': 'instructor@test.example.com',
                    'role': 'instructor'
                }
                
                # Publish quiz
                quiz_publication_data = {
                    'quiz_id': quiz_id,
                    'course_instance_id': instance_id,
                    'is_published': True,
                    'available_from': None,
                    'available_until': None,
                    'time_limit_minutes': 60,
                    'max_attempts': 3
                }
                
                response = await client.post(
                    f"{TEST_CONFIG['BASE_URL']}/quizzes/publish",
                    json=quiz_publication_data,
                    headers=headers
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result['success'] == True
                assert 'publication' in result
                
                publication = result['publication']
                assert publication['is_published'] == True
                assert publication['max_attempts'] == 3
                assert publication['time_limit_minutes'] == 60
                
                # Verify in database
                async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
                    db_publication = await conn.fetchrow(
                        "SELECT * FROM quiz_publications WHERE quiz_id = $1 AND course_instance_id = $2",
                        quiz_id, instance_id
                    )
                    assert db_publication is not None
                    assert db_publication['is_published'] == True
                    assert db_publication['max_attempts'] == 3

    @pytest.mark.asyncio
    async def test_end_to_end_course_lifecycle(self, clean_db, test_instructor, mock_auth_token):
        """Test complete end-to-end course lifecycle."""
        course_id = str(uuid.uuid4())
        
        # Step 1: Create course
        async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
            await conn.execute("""
                INSERT INTO courses (id, title, description, instructor_id, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, course_id, 'TEST_E2E_Course', 'End-to-end test course', 
                test_instructor, 'draft', datetime.utcnow())
        
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {mock_auth_token}'}
            
            with patch('services.course_management.main.get_current_user') as mock_auth:
                mock_auth.return_value = {
                    'user_id': test_instructor,
                    'email': 'instructor@test.example.com',
                    'role': 'instructor'
                }
                
                # Step 2: Publish course
                publish_data = {
                    'visibility': 'public',
                    'description': 'Updated description for E2E test'
                }
                
                response = await client.post(
                    f"{TEST_CONFIG['BASE_URL']}/courses/{course_id}/publish",
                    json=publish_data,
                    headers=headers
                )
                
                assert response.status_code == 200
                
                # Step 3: Create course instance
                instance_data = {
                    'course_id': course_id,
                    'instance_name': 'TEST_E2E_Instance',
                    'start_datetime': (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    'end_datetime': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    'timezone': 'UTC',
                    'max_students': 20
                }
                
                response = await client.post(
                    f"{TEST_CONFIG['BASE_URL']}/course-instances",
                    json=instance_data,
                    headers=headers
                )
                
                assert response.status_code == 200
                instance_result = response.json()
                instance_id = instance_result['instance']['id']
                
                # Step 4: Enroll student
                enrollment_data = {
                    'student_email': 'e2e.student@test.example.com',
                    'student_first_name': 'E2E',
                    'student_last_name': 'Student',
                    'send_welcome_email': False  # Don't send actual email in test
                }
                
                response = await client.post(
                    f"{TEST_CONFIG['BASE_URL']}/course-instances/{instance_id}/enroll",
                    json=enrollment_data,
                    headers=headers
                )
                
                assert response.status_code == 200
                enrollment_result = response.json()
                access_token = enrollment_result['enrollment']['access_token']
                
                # Step 5: Student authentication (simulate student login)
                # First, we need to get the temporary password from the database
                async with asyncpg.connect(TEST_CONFIG['DATABASE_URL']) as conn:
                    enrollment = await conn.fetchrow(
                        "SELECT temporary_password FROM student_course_enrollments WHERE access_token = $1",
                        access_token
                    )
                    
                    # For testing, we'll use the service to create a known password
                    from services.course_management.course_publishing_api import CoursePublishingService
                    test_pool = await asyncpg.create_pool(TEST_CONFIG['DATABASE_URL'])
                    service = CoursePublishingService(test_pool)
                    
                    known_password = 'TestPass123!'
                    hashed_known = service.hash_password(known_password)
                    
                    # Update enrollment with known password
                    await conn.execute(
                        "UPDATE student_course_enrollments SET temporary_password = $1 WHERE access_token = $2",
                        hashed_known, access_token
                    )
                    
                    await test_pool.close()
                
                # Now test student authentication
                auth_data = {
                    'access_token': access_token,
                    'password': known_password
                }
                
                response = await client.post(
                    f"{TEST_CONFIG['BASE_URL']}/student/auth/login",
                    json=auth_data
                )
                
                assert response.status_code == 200
                auth_result = response.json()
                assert auth_result['success'] == True
                
                # Step 6: Get student course data
                response = await client.get(
                    f"{TEST_CONFIG['BASE_URL']}/student/course-data",
                    params={'token': access_token}
                )
                
                assert response.status_code == 200
                course_data_result = response.json()
                assert course_data_result['success'] == True
                
                # Verify complete workflow
                data = course_data_result['data']
                assert data['course']['title'] == 'TEST_E2E_Course'
                assert data['instance']['name'] == 'TEST_E2E_Instance'
                assert data['enrollment']['student_email'] == 'e2e.student@test.example.com'


if __name__ == '__main__':
    pytest.main([__file__])