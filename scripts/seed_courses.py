#!/usr/bin/env python3
"""
Seed sample published courses for E2E testing.

Business Context:
Creates realistic course data for testing student course discovery and enrollment flows.
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime

# Database connection config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'course_creator',
    'user': 'postgres',
    'password': 'postgres_password'
}

SAMPLE_COURSES = [
    {
        'title': 'Introduction to Python Programming',
        'description': 'Learn Python programming from scratch. Perfect for beginners who want to start their coding journey.',
        'category': 'Programming',
        'difficulty_level': 'beginner',
        'estimated_duration': 40,
        'prerequisites': [],
        'learning_objectives': [
            'Understand Python syntax and basic concepts',
            'Write simple Python programs',
            'Work with data structures like lists and dictionaries',
            'Debug and test Python code'
        ]
    },
    {
        'title': 'Web Development with JavaScript',
        'description': 'Master modern web development using JavaScript, HTML, and CSS. Build interactive websites.',
        'category': 'Web Development',
        'difficulty_level': 'intermediate',
        'estimated_duration': 60,
        'prerequisites': ['Basic HTML knowledge', 'Basic CSS knowledge'],
        'learning_objectives': [
            'Build responsive web pages',
            'Use JavaScript for interactivity',
            'Understand the DOM and event handling',
            'Work with APIs and asynchronous code'
        ]
    },
    {
        'title': 'Data Science Fundamentals',
        'description': 'Explore data science concepts including statistics, data analysis, and machine learning basics.',
        'category': 'Data Science',
        'difficulty_level': 'intermediate',
        'estimated_duration': 80,
        'prerequisites': ['Basic Python programming', 'High school mathematics'],
        'learning_objectives': [
            'Analyze data using pandas and numpy',
            'Visualize data with matplotlib',
            'Understand basic machine learning algorithms',
            'Clean and preprocess datasets'
        ]
    },
    {
        'title': 'Database Design and SQL',
        'description': 'Learn how to design relational databases and write efficient SQL queries.',
        'category': 'Databases',
        'difficulty_level': 'beginner',
        'estimated_duration': 35,
        'prerequisites': [],
        'learning_objectives': [
            'Design normalized database schemas',
            'Write complex SQL queries',
            'Understand indexes and performance',
            'Use transactions and constraints'
        ]
    },
    {
        'title': 'Advanced Docker and Kubernetes',
        'description': 'Deep dive into containerization and orchestration for production deployments.',
        'category': 'DevOps',
        'difficulty_level': 'advanced',
        'estimated_duration': 50,
        'prerequisites': ['Linux basics', 'Basic Docker knowledge', 'Understanding of networking'],
        'learning_objectives': [
            'Deploy applications with Docker',
            'Orchestrate containers with Kubernetes',
            'Implement CI/CD pipelines',
            'Monitor and troubleshoot containerized apps'
        ]
    }
]

async def seed_courses():
    """Seed sample courses into the database."""
    conn = None
    try:
        # Connect to database
        print(f"Connecting to database at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✓ Connected to database")

        # Get or create test instructor
        instructor_id = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1",
            'instructor@example.com'
        )

        if not instructor_id:
            print("Creating test instructor...")
            instructor_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO users (id, username, email, hashed_password, full_name, role, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                instructor_id,
                'testinstructor',
                'instructor@example.com',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7T8qD2XmwO',  # hashed "password123"
                'Test Instructor',
                'instructor',
                datetime.utcnow()
            )
            print(f"✓ Created test instructor: {instructor_id}")
        else:
            print(f"✓ Found existing instructor: {instructor_id}")

        # Clear existing test courses
        deleted = await conn.execute("DELETE FROM courses WHERE instructor_id = $1", instructor_id)
        print(f"✓ Cleared {deleted.split()[-1]} existing test courses")

        # Insert sample courses
        print(f"\nInserting {len(SAMPLE_COURSES)} sample courses...")
        for idx, course_data in enumerate(SAMPLE_COURSES, 1):
            course_id = str(uuid.uuid4())

            await conn.execute(
                """
                INSERT INTO courses (
                    id, title, description, instructor_id, category,
                    difficulty_level, estimated_duration, is_published,
                    status, created_at, updated_at, published_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                course_id,
                course_data['title'],
                course_data['description'],
                instructor_id,
                course_data['category'],
                course_data['difficulty_level'],
                course_data['estimated_duration'],
                True,  # is_published
                'published',  # status
                datetime.utcnow(),
                datetime.utcnow(),
                datetime.utcnow()  # published_at
            )
            print(f"  {idx}. {course_data['title']} (ID: {course_id[:8]}...)")

        # Verify insertion
        count = await conn.fetchval("SELECT COUNT(*) FROM courses WHERE is_published = true")
        print(f"\n✓ Successfully seeded {count} published courses")

        # Show summary
        courses = await conn.fetch(
            """
            SELECT title, category, difficulty_level, estimated_duration
            FROM courses
            WHERE is_published = true
            ORDER BY created_at DESC
            LIMIT 10
            """
        )

        print("\n📚 Published Courses:")
        print("-" * 80)
        for course in courses:
            print(f"  • {course['title']}")
            print(f"    Category: {course['category']} | Difficulty: {course['difficulty_level']} | Duration: {course['estimated_duration']}h")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            await conn.close()
            print("\n✓ Database connection closed")

    return True

if __name__ == "__main__":
    print("=" * 80)
    print("COURSE SEEDING SCRIPT")
    print("=" * 80)
    print()

    success = asyncio.run(seed_courses())

    if success:
        print("\n" + "=" * 80)
        print("✓ SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 80)
        exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ SEEDING FAILED")
        print("=" * 80)
        exit(1)
