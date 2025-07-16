#!/usr/bin/env python3
"""
Assign existing courses to test instructor
"""
import asyncio
import os
import databases
import sqlalchemy
from sqlalchemy.dialects import postgresql

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

async def assign_courses_to_instructor():
    """Assign existing courses to test instructor"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Get test instructor ID
        test_instructor_email = "instructor@courseplatform.com"
        instructor_query = "SELECT id, email, full_name FROM users WHERE email = :email"
        instructor = await database.fetch_one(instructor_query, {"email": test_instructor_email})
        
        if not instructor:
            print(f"❌ Test instructor {test_instructor_email} not found!")
            return
        
        instructor_id = instructor['id']
        print(f"Test instructor: {instructor['email']} ({instructor['full_name']})")
        print(f"Instructor ID: {instructor_id}")
        
        # Get all courses
        courses_query = "SELECT id, title, instructor_id FROM courses"
        courses = await database.fetch_all(courses_query)
        
        print(f"\nFound {len(courses)} courses:")
        for course in courses:
            print(f"  - {course['title']} (ID: {course['id']})")
        
        # Assign all courses to test instructor
        for course in courses:
            update_query = "UPDATE courses SET instructor_id = :instructor_id WHERE id = :course_id"
            await database.execute(update_query, {"instructor_id": instructor_id, "course_id": course['id']})
            print(f"✅ Assigned '{course['title']}' to test instructor")
        
        # Verify assignment
        print(f"\nVerifying assignment...")
        instructor_courses_query = "SELECT id, title FROM courses WHERE instructor_id = :instructor_id"
        instructor_courses = await database.fetch_all(instructor_courses_query, {"instructor_id": instructor_id})
        
        print(f"Test instructor now has {len(instructor_courses)} courses:")
        for course in instructor_courses:
            print(f"  - {course['title']}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(assign_courses_to_instructor())