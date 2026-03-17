#!/usr/bin/env python3
"""
Database Setup Script for CI/CD Pipeline
Creates minimal database schema for testing
"""
import os
import sys
import asyncpg
import asyncio

async def setup_database():
    """
    Set up minimal database schema for CI testing

    Business Context:
    This script creates the essential database tables needed for CI/CD testing
    without requiring the full application stack to be running.
    """
    database_url = os.getenv('DATABASE_URL', 'postgresql://test_user:test_password@localhost:5432/course_creator_test')

    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        print(f"✅ Connected to database")

        # Create essential tables for testing
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'student',
                organization_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Created users table")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                domain VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Created organizations table")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                instructor_id INTEGER REFERENCES users(id),
                organization_id INTEGER REFERENCES organizations(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Created courses table")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES users(id),
                course_id INTEGER REFERENCES courses(id),
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, course_id)
            );
        """)
        print("✅ Created enrollments table")

        await conn.close()
        print("✅ Database setup completed successfully")
        return 0

    except Exception as e:
        print(f"❌ Database setup failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(setup_database())
    sys.exit(exit_code)
