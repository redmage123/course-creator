#!/usr/bin/env python3
"""
Create initial instructor user for Course Creator Platform
"""

import asyncio
import os
import sys
from passlib.context import CryptContext
import databases
import sqlalchemy
from sqlalchemy.dialects import postgresql

# Add the services directory to the path
sys.path.append('/home/bbrelin/course-creator/services/user-management')

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Users table definition
users_table = sqlalchemy.Table(
    'users',
    sqlalchemy.MetaData(),
    sqlalchemy.Column('id', postgresql.UUID, primary_key=True, server_default=sqlalchemy.text('uuid_generate_v4()')),
    sqlalchemy.Column('email', sqlalchemy.String(255), unique=True, nullable=False),
    sqlalchemy.Column('username', sqlalchemy.String(100), unique=True, nullable=False),
    sqlalchemy.Column('full_name', sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column('hashed_password', sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column('is_active', sqlalchemy.Boolean, default=True),
    sqlalchemy.Column('is_verified', sqlalchemy.Boolean, default=False),
    sqlalchemy.Column('role', sqlalchemy.String(50), default='student'),
)

async def create_instructor_user():
    """Create the initial instructor user"""
    
    # Instructor user details
    instructor_email = "instructor@courseplatform.com"
    instructor_password = "Instructor123!"
    instructor_full_name = "Test Instructor"
    
    # Connect to database
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Check if instructor already exists
        existing_query = users_table.select().where(users_table.c.email == instructor_email)
        existing_instructor = await database.fetch_one(existing_query)
        
        if existing_instructor:
            print(f"Instructor user {instructor_email} already exists!")
            print(f"User ID: {existing_instructor['id']}")
            print(f"Role: {existing_instructor['role']}")
            return existing_instructor['id']
        
        # Hash password
        hashed_password = pwd_context.hash(instructor_password)
        
        # Create instructor user
        insert_query = users_table.insert().values(
            email=instructor_email,
            username="instructor",
            full_name=instructor_full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            role='instructor'
        )
        
        result = await database.execute(insert_query)
        print(f"✅ Instructor user created successfully!")
        print(f"📧 Email: {instructor_email}")
        print(f"🔐 Password: {instructor_password}")
        print(f"👤 Role: instructor")
        
        # Get the created user ID
        user_query = users_table.select().where(users_table.c.email == instructor_email)
        user = await database.fetch_one(user_query)
        return user['id']
        
    except Exception as e:
        print(f"❌ Error creating instructor user: {e}")
        return None
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    user_id = asyncio.run(create_instructor_user())
    if user_id:
        print(f"User ID: {user_id}")