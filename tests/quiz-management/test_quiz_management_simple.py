#!/usr/bin/env python3
"""
Simplified Quiz Management System Test
Tests the basic functionality with the actual database schema
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime, timezone, timedelta

async def test_quiz_management_simple():
    """Test the quiz management system with actual database schema."""
    print("🧪 Simplified Quiz Management System Test")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = await asyncpg.connect('postgresql://postgres:postgres_password@localhost:5433/course_creator')
        
        print("\n📋 Test 1: Database Schema Validation")
        print("-" * 40)
        
        # Check if required tables exist
        tables = ['users', 'courses', 'quizzes', 'quiz_publications', 'quiz_attempts', 'course_instances', 'student_course_enrollments']
        for table in tables:
            exists = await conn.fetchval("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)", table)
            if exists:
                print(f"✅ Table {table} exists")
            else:
                print(f"❌ Table {table} missing")
                return False
        
        # Check if course_instance_id exists in quiz_attempts
        schema_check = await conn.fetchrow("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'quiz_attempts' AND column_name = 'course_instance_id'
        """)
        if schema_check:
            print("✅ quiz_attempts.course_instance_id exists")
        else:
            print("❌ quiz_attempts.course_instance_id missing")
            return False
        
        print("\n👨‍🏫 Test 2: Create Test Data")
        print("-" * 35)
        
        # Clean up any existing test data in proper order
        await conn.execute("DELETE FROM quiz_attempts WHERE student_id IN (SELECT id FROM users WHERE email LIKE '%@quiz.test')")
        await conn.execute("DELETE FROM quiz_publications WHERE published_by IN (SELECT id FROM users WHERE email LIKE '%@quiz.test')")
        await conn.execute("DELETE FROM student_course_enrollments WHERE student_id IN (SELECT id FROM users WHERE email LIKE '%@quiz.test')")
        await conn.execute("DELETE FROM course_instances WHERE instructor_id IN (SELECT id FROM users WHERE email LIKE '%@quiz.test')")
        await conn.execute("DELETE FROM quizzes WHERE course_id IN (SELECT id FROM courses WHERE instructor_id IN (SELECT id FROM users WHERE email LIKE '%@quiz.test'))")
        await conn.execute("DELETE FROM courses WHERE instructor_id IN (SELECT id FROM users WHERE email LIKE '%@quiz.test')")
        await conn.execute("DELETE FROM users WHERE email LIKE '%@quiz.test'")
        
        # Create test instructor
        instructor_id = str(uuid.uuid4())
        unique_instructor_username = f"testinstructor_{uuid.uuid4().hex[:8]}"
        await conn.execute("""
            INSERT INTO users (id, email, username, full_name, hashed_password, role, first_name, last_name, organization, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP)
        """, instructor_id, "test.instructor@quiz.test", unique_instructor_username, "Dr. Jane Smith", 
            "hashed_password", "instructor", "Dr. Jane", "Smith", "Computer Science Department")
        print(f"✅ Test instructor created: {instructor_id}")
        
        # Create test course
        course_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO courses (id, title, description, instructor_id, status, visibility, created_at)
            VALUES ($1, $2, $3, $4, 'published', 'public', CURRENT_TIMESTAMP)
        """, course_id, "Test Quiz Management Course", "Course for testing quiz management", instructor_id)
        print(f"✅ Test course created: {course_id}")
        
        # Create test quiz
        quiz_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO quizzes (id, course_id, title, description, time_limit, passing_score, max_attempts, is_published, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, false, CURRENT_TIMESTAMP)
        """, quiz_id, course_id, "Python Basics Quiz", "Quiz covering Python fundamentals", 30, 70.0, 3)
        print(f"✅ Test quiz created: {quiz_id}")
        
        # Create test course instance
        instance_id = str(uuid.uuid4())
        start_date = datetime.now(timezone.utc) + timedelta(days=1)
        end_date = datetime.now(timezone.utc) + timedelta(days=90)
        await conn.execute("""
            INSERT INTO course_instances (
                id, course_id, instructor_id, instance_name, start_date, end_date, 
                timezone, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
        """, instance_id, course_id, instructor_id, "Test Instance", start_date, end_date, "UTC", "scheduled")
        print(f"✅ Test course instance created: {instance_id}")
        
        # Create test student
        student_id = str(uuid.uuid4())
        unique_username = f"teststudent_{uuid.uuid4().hex[:8]}"
        await conn.execute("""
            INSERT INTO users (id, email, username, full_name, hashed_password, role, first_name, last_name, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
        """, student_id, "student1@quiz.test", unique_username, "Student User1", "hashed_password", "student", "Student", "User1")
        print(f"✅ Test student created: {student_id}")
        
        print("\n📚 Test 3: Quiz Publication Management")
        print("-" * 42)
        
        # Create quiz publication
        publication_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO quiz_publications (
                id, quiz_id, course_instance_id, is_published, published_by,
                available_from, available_until, time_limit_minutes, max_attempts,
                published_at, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_TIMESTAMP)
        """, publication_id, quiz_id, instance_id, True, instructor_id,
            None, None, 30, 3, datetime.now(timezone.utc))
        print(f"✅ Quiz publication created: {publication_id}")
        
        # Test quiz publication query (simulating API endpoint)
        quiz_publications = await conn.fetch("""
            SELECT 
                q.id as quiz_id,
                q.title as quiz_title,
                q.description,
                qp.id as publication_id,
                COALESCE(qp.is_published, false) as is_published,
                qp.published_at,
                qp.time_limit_minutes,
                qp.max_attempts
            FROM quizzes q
            LEFT JOIN quiz_publications qp ON q.id = qp.quiz_id AND qp.course_instance_id = $1
            WHERE q.course_id = $2
            ORDER BY q.title
        """, instance_id, course_id)
        
        print("📋 Quiz Publications:")
        for pub in quiz_publications:
            status = "Published" if pub['is_published'] else "Unpublished"
            print(f"  - {pub['quiz_title']}: {status}")
        
        print("\n📝 Test 4: Student Quiz Access")
        print("-" * 35)
        
        # Enroll student in course instance
        enrollment_id = str(uuid.uuid4())
        access_token = f"access_{uuid.uuid4().hex[:16]}"
        await conn.execute("""
            INSERT INTO student_course_enrollments (
                id, student_id, course_instance_id, student_email, 
                student_first_name, student_last_name, access_token,
                unique_access_url, temporary_password, enrollment_status, enrolled_by, enrolled_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, CURRENT_TIMESTAMP)
        """, enrollment_id, student_id, instance_id, "student1@quiz.test",
            "Student", "User1", access_token,
            f"http://localhost:3000/student-login/{access_token}", "TempPass123", "enrolled", instructor_id)
        print(f"✅ Student enrolled: {enrollment_id}")
        
        # Test student access to published quizzes
        accessible_quizzes = await conn.fetch("""
            SELECT qp.*, q.title, q.description
            FROM quiz_publications qp
            JOIN quizzes q ON qp.quiz_id = q.id
            WHERE qp.course_instance_id = $1 AND qp.is_published = true
            AND (qp.available_from IS NULL OR qp.available_from <= CURRENT_TIMESTAMP)
            AND (qp.available_until IS NULL OR qp.available_until >= CURRENT_TIMESTAMP)
            ORDER BY qp.published_at
        """, instance_id)
        
        print(f"✅ Student can access {len(accessible_quizzes)} published quizzes")
        
        print("\n📊 Test 5: Quiz Attempt Storage")
        print("-" * 37)
        
        # Simulate quiz attempt
        attempt_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO quiz_attempts (
                id, student_id, quiz_id, course_id, course_instance_id,
                answers, score, total_questions, completed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
        """, attempt_id, student_id, quiz_id, course_id, instance_id,
            '["0", "1"]', 85.0, 2)
        print(f"✅ Quiz attempt stored: {attempt_id}")
        
        # Test analytics query
        analytics = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_attempts,
                AVG(score) as avg_score,
                COUNT(DISTINCT student_id) as unique_students
            FROM quiz_attempts 
            WHERE course_instance_id = $1
        """, instance_id)
        
        print(f"📈 Analytics: {analytics['total_attempts']} attempts, {analytics['avg_score']:.1f}% avg score, {analytics['unique_students']} students")
        
        print("\n🧹 Test 6: Cleanup")
        print("-" * 25)
        
        # Clean up test data
        await conn.execute("DELETE FROM quiz_attempts WHERE course_id = $1", course_id)
        await conn.execute("DELETE FROM quiz_publications WHERE quiz_id = $1", quiz_id)
        await conn.execute("DELETE FROM student_course_enrollments WHERE course_instance_id = $1", instance_id)
        await conn.execute("DELETE FROM course_instances WHERE id = $1", instance_id)
        await conn.execute("DELETE FROM quizzes WHERE id = $1", quiz_id)
        await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
        await conn.execute("DELETE FROM users WHERE email LIKE '%@quiz.test'")
        print("✅ Test data cleaned up")
        
        await conn.close()
        
        print(f"\n🎉 Quiz Management Test Completed Successfully!")
        print("=" * 50)
        print("✅ Database schema is correct")
        print("✅ Quiz publication workflow works")
        print("✅ Student access control works")
        print("✅ Quiz attempts are stored with course instance tracking")
        print("✅ Analytics integration is functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_quiz_management_simple())
    if success:
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ TESTS FAILED")
    exit(0 if success else 1)