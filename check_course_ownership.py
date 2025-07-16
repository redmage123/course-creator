#!/usr/bin/env python3
"""
Check course ownership and instructor IDs
"""
import asyncio
import os
import databases
import sqlalchemy
from sqlalchemy.dialects import postgresql

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

async def check_course_ownership():
    """Check course ownership and instructor IDs"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Check all users
        users_query = "SELECT id, email, full_name, role FROM users WHERE role = 'instructor'"
        users = await database.fetch_all(users_query)
        
        print(f"\nInstructor users ({len(users)}):")
        for user in users:
            print(f"  - {user['email']} ({user['full_name']}) - ID: {user['id']}")
        
        # Check all courses
        courses_query = "SELECT id, title, instructor_id, created_at FROM courses"
        courses = await database.fetch_all(courses_query)
        
        print(f"\nCourses ({len(courses)}):")
        for course in courses:
            print(f"  - {course['title']} - Instructor ID: {course['instructor_id']}")
            
            # Find instructor name
            instructor_query = "SELECT email, full_name FROM users WHERE id = $1"
            instructor = await database.fetch_one(instructor_query, course['instructor_id'])
            if instructor:
                print(f"    Instructor: {instructor['email']} ({instructor['full_name']})")
            else:
                print(f"    Instructor: NOT FOUND")
        
        # Check if our test instructor has any courses
        test_instructor_email = "instructor@courseplatform.com"
        test_instructor_query = "SELECT id FROM users WHERE email = $1"
        test_instructor = await database.fetch_one(test_instructor_query, test_instructor_email)
        
        if test_instructor:
            test_instructor_id = test_instructor['id']
            print(f"\nTest instructor ID: {test_instructor_id}")
            
            # Check courses for test instructor
            instructor_courses_query = "SELECT * FROM courses WHERE instructor_id = $1"
            instructor_courses = await database.fetch_all(instructor_courses_query, test_instructor_id)
            
            print(f"Courses for test instructor: {len(instructor_courses)}")
            for course in instructor_courses:
                print(f"  - {course['title']}")
                
            if len(instructor_courses) == 0:
                print("❌ Test instructor has no courses - this is why the API returns empty!")
                print("Solution: Either create courses for the test instructor or fix the API filtering")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(check_course_ownership())