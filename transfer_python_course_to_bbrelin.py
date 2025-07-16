#!/usr/bin/env python3
"""
Transfer the Introduction to Python course to bbrelin instructor
"""
import asyncio
import os
import databases
import sqlalchemy
from sqlalchemy.dialects import postgresql

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

async def transfer_python_course_to_bbrelin():
    """Transfer the Introduction to Python course to bbrelin instructor"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Get bbrelin user
        bbrelin_query = "SELECT id, email, full_name FROM users WHERE email = 'bbrelin@gmail.com'"
        bbrelin_user = await database.fetch_one(bbrelin_query)
        
        if not bbrelin_user:
            print("❌ bbrelin user not found!")
            return
        
        bbrelin_id = bbrelin_user['id']
        print(f"Found bbrelin user: {bbrelin_user['email']} ({bbrelin_user['full_name']})")
        print(f"Bbrelin ID: {bbrelin_id}")
        
        # Get the Introduction to Python course
        python_course_query = "SELECT id, title, instructor_id FROM courses WHERE title = 'Introduction to Python'"
        python_course = await database.fetch_one(python_course_query)
        
        if not python_course:
            print("❌ Introduction to Python course not found!")
            return
        
        print(f"Found course: {python_course['title']} (ID: {python_course['id']})")
        
        # Get current instructor info
        current_instructor_query = "SELECT email, full_name FROM users WHERE id = :instructor_id"
        current_instructor = await database.fetch_one(current_instructor_query, {"instructor_id": python_course['instructor_id']})
        
        if current_instructor:
            print(f"Current instructor: {current_instructor['email']} ({current_instructor['full_name']})")
        
        # Transfer the course to bbrelin
        transfer_query = "UPDATE courses SET instructor_id = :new_instructor_id WHERE id = :course_id"
        await database.execute(transfer_query, {
            "new_instructor_id": bbrelin_id,
            "course_id": python_course['id']
        })
        
        print(f"✅ Transferred 'Introduction to Python' course to bbrelin")
        
        # Verify the transfer
        verify_query = "SELECT id, title, instructor_id FROM courses WHERE instructor_id = :instructor_id"
        bbrelin_courses = await database.fetch_all(verify_query, {"instructor_id": bbrelin_id})
        
        print(f"\nBbrelin now has {len(bbrelin_courses)} courses:")
        for course in bbrelin_courses:
            print(f"  - {course['title']}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(transfer_python_course_to_bbrelin())