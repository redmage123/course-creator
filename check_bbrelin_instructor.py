#!/usr/bin/env python3
"""
Check bbrelin instructor user and their courses
"""
import asyncio
import os
import databases
import sqlalchemy
from sqlalchemy.dialects import postgresql

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

async def check_bbrelin_instructor():
    """Check bbrelin instructor user and their courses"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Look for bbrelin user
        bbrelin_patterns = ['bbrelin', '%bbrelin%', 'bbrelin@%']
        
        for pattern in bbrelin_patterns:
            user_query = "SELECT id, email, full_name, role FROM users WHERE email ILIKE :pattern"
            users = await database.fetch_all(user_query, {"pattern": pattern})
            
            if users:
                print(f"\nFound users matching '{pattern}':")
                for user in users:
                    print(f"  - {user['email']} ({user['full_name']}) - Role: {user['role']} - ID: {user['id']}")
                    
                    # Check courses for this user
                    courses_query = "SELECT id, title, created_at FROM courses WHERE instructor_id = :instructor_id"
                    courses = await database.fetch_all(courses_query, {"instructor_id": user['id']})
                    
                    print(f"    Courses: {len(courses)}")
                    for course in courses:
                        print(f"      - {course['title']} (ID: {course['id']})")
        
        # Check for "Introduction to Python" course specifically
        python_course_query = "SELECT id, title, instructor_id, created_at FROM courses WHERE title ILIKE '%python%'"
        python_courses = await database.fetch_all(python_course_query)
        
        print(f"\nPython courses found: {len(python_courses)}")
        for course in python_courses:
            instructor_query = "SELECT email, full_name FROM users WHERE id = :instructor_id"
            instructor = await database.fetch_one(instructor_query, {"instructor_id": course['instructor_id']})
            
            instructor_info = f"{instructor['email']} ({instructor['full_name']})" if instructor else "UNKNOWN"
            print(f"  - {course['title']} - Instructor: {instructor_info}")
        
        # Check all instructors with courses
        print(f"\nAll instructors with courses:")
        all_instructors_query = """
            SELECT u.id, u.email, u.full_name, COUNT(c.id) as course_count
            FROM users u
            LEFT JOIN courses c ON u.id = c.instructor_id
            WHERE u.role = 'instructor'
            GROUP BY u.id, u.email, u.full_name
            ORDER BY course_count DESC
        """
        instructors = await database.fetch_all(all_instructors_query)
        
        for instructor in instructors:
            print(f"  - {instructor['email']} ({instructor['full_name']}) - {instructor['course_count']} courses")
            
            if instructor['course_count'] > 0:
                courses_query = "SELECT title FROM courses WHERE instructor_id = :instructor_id"
                courses = await database.fetch_all(courses_query, {"instructor_id": instructor['id']})
                for course in courses:
                    print(f"    - {course['title']}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(check_bbrelin_instructor())