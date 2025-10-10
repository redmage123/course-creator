#!/usr/bin/env python3
"""
Demo Data Seeding Script

BUSINESS PURPOSE:
Populates database with realistic demo data for video demonstrations.
Creates organizations, projects, tracks, instructors, courses, and students.

USAGE:
    python3 scripts/seed_demo_data.py
    python3 scripts/seed_demo_data.py --clean  # Clean and reseed
"""

import sys
import os
import uuid
import bcrypt
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
import argparse

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'course_creator',
    'user': 'postgres',
    'password': 'postgres_password'
}

# Demo password (same for all demo accounts)
DEMO_PASSWORD = "DemoPass123!"
DEMO_PASSWORD_HASH = bcrypt.hashpw(DEMO_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_connection():
    """
    Establish database connection
    """
    return psycopg2.connect(**DB_CONFIG)


def clean_demo_data(conn):
    """
    Remove existing demo data

    BUSINESS PURPOSE:
    Allows fresh demo data seeding without duplicates.
    """
    print("🧹 Cleaning existing demo data...")

    cur = conn.cursor()

    try:
        # Delete demo users (this will cascade to related records)
        cur.execute("""
            DELETE FROM users
            WHERE email LIKE 'demo.%@example.com'
               OR email LIKE '%@demo.techacademy.com'
        """)
        deleted_users = cur.rowcount
        print(f"   ✓ Deleted {deleted_users} demo users")

        # Delete demo organization (cascades to projects)
        cur.execute("""
            DELETE FROM organizations
            WHERE slug = 'tech-academy' OR name = 'Tech Academy'
        """)
        deleted_orgs = cur.rowcount
        print(f"   ✓ Deleted {deleted_orgs} demo organizations")

        # Delete demo courses
        cur.execute("""
            DELETE FROM courses
            WHERE title LIKE 'JavaScript%'
               OR title LIKE 'Python%'
               OR title LIKE 'React%'
               OR title LIKE 'Node.js%'
               OR title LIKE 'Database%'
        """)
        deleted_courses = cur.rowcount
        print(f"   ✓ Deleted {deleted_courses} demo courses")

        conn.commit()
        print("✅ Demo data cleaned successfully\n")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error cleaning demo data: {e}")
        raise
    finally:
        cur.close()


def seed_organization(conn):
    """
    Create demo organization: Tech Academy

    RETURNS: organization_id (UUID)
    """
    print("🏢 Creating demo organization...")

    cur = conn.cursor()

    try:
        org_id = str(uuid.uuid4())

        cur.execute("""
            INSERT INTO organizations (
                id, name, slug, description, address,
                contact_phone, contact_email, domain, is_active
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            org_id,
            'Tech Academy',
            'tech-academy',
            'Professional software development training for aspiring developers',
            '123 Tech Street, San Francisco, CA 94105',
            '+1 (555) 123-4567',
            'contact@techacademy.com',
            'techacademy.com',
            True
        ))

        org_id = cur.fetchone()[0]
        conn.commit()

        print(f"   ✓ Created organization: Tech Academy (ID: {org_id})")
        return org_id

    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error creating organization: {e}")
        raise
    finally:
        cur.close()


def seed_project(conn, org_id, creator_id):
    """
    Create demo project: Web Development Bootcamp

    RETURNS: project_id (UUID)
    """
    print("📁 Creating demo project...")

    cur = conn.cursor()

    try:
        project_id = str(uuid.uuid4())

        # Tracks stored in metadata
        tracks_metadata = {
            'tracks': [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Frontend Developer Track',
                    'description': 'Master HTML, CSS, JavaScript, and modern frontend frameworks',
                    'duration_weeks': 12,
                    'courses': ['JavaScript Fundamentals', 'React Development']
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Backend Developer Track',
                    'description': 'Learn server-side development with Python and Node.js',
                    'duration_weeks': 12,
                    'courses': ['Python Basics', 'Node.js & Express', 'Database Design']
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Full Stack Developer Track',
                    'description': 'Complete frontend and backend development training',
                    'duration_weeks': 24,
                    'courses': ['JavaScript Fundamentals', 'React Development', 'Node.js & Express', 'Database Design']
                }
            ]
        }

        cur.execute("""
            INSERT INTO projects (
                id, organization_id, name, slug, description,
                target_roles, duration_weeks, max_participants,
                start_date, status, created_by, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            project_id,
            org_id,
            'Web Development Bootcamp',
            'web-dev-bootcamp',
            'Comprehensive web development training program covering frontend and backend technologies',
            ['Frontend Developer', 'Backend Developer', 'Full Stack Developer'],
            24,
            100,
            datetime.now().date(),
            'active',
            creator_id,
            psycopg2.extras.Json(tracks_metadata)
        ))

        project_id = cur.fetchone()[0]
        conn.commit()

        print(f"   ✓ Created project: Web Development Bootcamp (ID: {project_id})")
        print(f"   ✓ Added 3 tracks: Frontend, Backend, Full Stack")
        return project_id

    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error creating project: {e}")
        raise
    finally:
        cur.close()


def seed_instructors(conn, org_id):
    """
    Create demo instructors

    RETURNS: list of instructor_ids
    """
    print("👨‍🏫 Creating demo instructors...")

    cur = conn.cursor()

    instructors = [
        {
            'email': 'demo.instructor@example.com',
            'username': 'demo.instructor',
            'full_name': 'John Smith',
            'bio': 'Senior Full Stack Developer with 10+ years experience in web development and teaching'
        },
        {
            'email': 'sarah.jones@demo.techacademy.com',
            'username': 'sarah.jones',
            'full_name': 'Sarah Jones',
            'bio': 'Frontend specialist and React expert. Former lead developer at major tech companies'
        },
        {
            'email': 'michael.chen@demo.techacademy.com',
            'username': 'michael.chen',
            'full_name': 'Michael Chen',
            'bio': 'Backend architect specializing in Python and Node.js. 15 years in software engineering'
        },
        {
            'email': 'emily.rodriguez@demo.techacademy.com',
            'username': 'emily.rodriguez',
            'full_name': 'Emily Rodriguez',
            'bio': 'Database expert and DevOps engineer. Passionate about teaching best practices'
        }
    ]

    instructor_ids = []

    try:
        for instructor in instructors:
            instructor_id = str(uuid.uuid4())

            cur.execute("""
                INSERT INTO users (
                    id, email, username, full_name, hashed_password,
                    is_active, is_verified, role, bio
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                instructor_id,
                instructor['email'],
                instructor['username'],
                instructor['full_name'],
                DEMO_PASSWORD_HASH,
                True,
                True,
                'instructor',
                instructor['bio']
            ))

            instructor_id = cur.fetchone()[0]
            instructor_ids.append(instructor_id)
            print(f"   ✓ Created instructor: {instructor['full_name']}")

        conn.commit()
        print(f"   ✓ Total instructors created: {len(instructor_ids)}\n")
        return instructor_ids

    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error creating instructors: {e}")
        raise
    finally:
        cur.close()


def seed_courses(conn, instructor_ids):
    """
    Create demo courses

    RETURNS: list of course_ids
    """
    print("📚 Creating demo courses...")

    cur = conn.cursor()

    courses = [
        {
            'title': 'JavaScript Fundamentals',
            'description': 'Master core JavaScript concepts including variables, functions, objects, arrays, and async programming',
            'instructor_id': instructor_ids[0],  # John Smith
            'category': 'Programming',
            'difficulty_level': 'beginner',
            'estimated_duration': 4,
            'duration_unit': 'weeks',
            'price': 0.00,
            'is_published': True,
            'status': 'published',
            'modules': 4,
            'lessons': 16
        },
        {
            'title': 'Python Basics',
            'description': 'Learn Python programming from scratch - syntax, data structures, OOP, and practical applications',
            'instructor_id': instructor_ids[2],  # Michael Chen
            'category': 'Programming',
            'difficulty_level': 'beginner',
            'estimated_duration': 4,
            'duration_unit': 'weeks',
            'price': 0.00,
            'is_published': True,
            'status': 'published',
            'modules': 4,
            'lessons': 20
        },
        {
            'title': 'React Development',
            'description': 'Build modern web applications with React - components, hooks, state management, and routing',
            'instructor_id': instructor_ids[1],  # Sarah Jones
            'category': 'Web Development',
            'difficulty_level': 'intermediate',
            'estimated_duration': 6,
            'duration_unit': 'weeks',
            'price': 0.00,
            'is_published': True,
            'status': 'published',
            'modules': 5,
            'lessons': 18
        },
        {
            'title': 'Node.js & Express',
            'description': 'Build scalable server-side applications with Node.js and Express framework',
            'instructor_id': instructor_ids[2],  # Michael Chen
            'category': 'Backend Development',
            'difficulty_level': 'intermediate',
            'estimated_duration': 6,
            'duration_unit': 'weeks',
            'price': 0.00,
            'is_published': True,
            'status': 'published',
            'modules': 6,
            'lessons': 22
        },
        {
            'title': 'Database Design & SQL',
            'description': 'Master relational database design, SQL queries, optimization, and best practices',
            'instructor_id': instructor_ids[3],  # Emily Rodriguez
            'category': 'Data & Databases',
            'difficulty_level': 'intermediate',
            'estimated_duration': 5,
            'duration_unit': 'weeks',
            'price': 0.00,
            'is_published': True,
            'status': 'published',
            'modules': 5,
            'lessons': 15
        },
        {
            'title': 'Git & Version Control',
            'description': 'Essential Git commands, workflows, branching strategies, and collaboration with GitHub',
            'instructor_id': instructor_ids[3],  # Emily Rodriguez
            'category': 'DevOps & Tools',
            'difficulty_level': 'beginner',
            'estimated_duration': 2,
            'duration_unit': 'weeks',
            'price': 0.00,
            'is_published': True,
            'status': 'published',
            'modules': 3,
            'lessons': 10
        }
    ]

    course_ids = []

    try:
        for course in courses:
            course_id = str(uuid.uuid4())

            # Create metadata with modules/lessons
            metadata = {
                'modules': course.pop('modules'),
                'lessons': course.pop('lessons'),
                'prerequisites': [],
                'learning_objectives': []
            }

            cur.execute("""
                INSERT INTO courses (
                    id, title, description, instructor_id, category,
                    difficulty_level, estimated_duration, duration_unit,
                    price, is_published, status, published_at,
                    total_enrollments, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                course_id,
                course['title'],
                course['description'],
                course['instructor_id'],
                course['category'],
                course['difficulty_level'],
                course['estimated_duration'],
                course['duration_unit'],
                course['price'],
                course['is_published'],
                course['status'],
                datetime.now() if course['is_published'] else None,
                0,  # Will update after adding enrollments
                psycopg2.extras.Json(metadata)
            ))

            course_id = cur.fetchone()[0]
            course_ids.append(course_id)
            print(f"   ✓ Created course: {course['title']}")

        conn.commit()
        print(f"   ✓ Total courses created: {len(course_ids)}\n")
        return course_ids

    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error creating courses: {e}")
        raise
    finally:
        cur.close()


def seed_students(conn):
    """
    Create demo students

    RETURNS: list of student_ids
    """
    print("👨‍🎓 Creating demo students...")

    cur = conn.cursor()

    students = [
        {'email': 'demo.student@example.com', 'username': 'demo.student', 'full_name': 'Sarah Johnson'},
        {'email': 'alex.martinez@demo.techacademy.com', 'username': 'alex.martinez', 'full_name': 'Alex Martinez'},
        {'email': 'emma.wilson@demo.techacademy.com', 'username': 'emma.wilson', 'full_name': 'Emma Wilson'},
        {'email': 'james.brown@demo.techacademy.com', 'username': 'james.brown', 'full_name': 'James Brown'},
        {'email': 'olivia.davis@demo.techacademy.com', 'username': 'olivia.davis', 'full_name': 'Olivia Davis'},
        {'email': 'noah.garcia@demo.techacademy.com', 'username': 'noah.garcia', 'full_name': 'Noah Garcia'},
        {'email': 'sophia.miller@demo.techacademy.com', 'username': 'sophia.miller', 'full_name': 'Sophia Miller'},
        {'email': 'liam.taylor@demo.techacademy.com', 'username': 'liam.taylor', 'full_name': 'Liam Taylor'},
        {'email': 'ava.anderson@demo.techacademy.com', 'username': 'ava.anderson', 'full_name': 'Ava Anderson'},
        {'email': 'william.thomas@demo.techacademy.com', 'username': 'william.thomas', 'full_name': 'William Thomas'},
        {'email': 'mia.jackson@demo.techacademy.com', 'username': 'mia.jackson', 'full_name': 'Mia Jackson'},
        {'email': 'ethan.white@demo.techacademy.com', 'username': 'ethan.white', 'full_name': 'Ethan White'},
        {'email': 'isabella.harris@demo.techacademy.com', 'username': 'isabella.harris', 'full_name': 'Isabella Harris'},
        {'email': 'mason.martin@demo.techacademy.com', 'username': 'mason.martin', 'full_name': 'Mason Martin'},
        {'email': 'charlotte.thompson@demo.techacademy.com', 'username': 'charlotte.thompson', 'full_name': 'Charlotte Thompson'},
        {'email': 'lucas.lopez@demo.techacademy.com', 'username': 'lucas.lopez', 'full_name': 'Lucas Lopez'},
        {'email': 'amelia.lee@demo.techacademy.com', 'username': 'amelia.lee', 'full_name': 'Amelia Lee'},
        {'email': 'benjamin.gonzalez@demo.techacademy.com', 'username': 'benjamin.gonzalez', 'full_name': 'Benjamin Gonzalez'},
        {'email': 'harper.clark@demo.techacademy.com', 'username': 'harper.clark', 'full_name': 'Harper Clark'},
        {'email': 'henry.rodriguez@demo.techacademy.com', 'username': 'henry.rodriguez', 'full_name': 'Henry Rodriguez'}
    ]

    student_ids = []

    try:
        for student in students:
            student_id = str(uuid.uuid4())

            cur.execute("""
                INSERT INTO users (
                    id, email, username, full_name, hashed_password,
                    is_active, is_verified, role
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                student_id,
                student['email'],
                student['username'],
                student['full_name'],
                DEMO_PASSWORD_HASH,
                True,
                True,
                'student'
            ))

            student_id = cur.fetchone()[0]
            student_ids.append(student_id)

        conn.commit()
        print(f"   ✓ Created {len(student_ids)} demo students\n")
        return student_ids

    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error creating students: {e}")
        raise
    finally:
        cur.close()


def update_course_enrollments(conn, course_ids, enrollment_counts):
    """
    Update course enrollment statistics
    """
    print("📊 Updating course enrollment statistics...")

    cur = conn.cursor()

    try:
        for course_id, count in zip(course_ids, enrollment_counts):
            cur.execute("""
                UPDATE courses
                SET total_enrollments = %s, active_enrollments = %s
                WHERE id = %s
            """, (count, count, course_id))

        conn.commit()
        print(f"   ✓ Updated enrollment statistics for {len(course_ids)} courses\n")

    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error updating enrollments: {e}")
        raise
    finally:
        cur.close()


def main():
    parser = argparse.ArgumentParser(description='Seed demo data for Course Creator Platform')
    parser.add_argument('--clean', action='store_true', help='Clean existing demo data before seeding')
    args = parser.parse_args()

    print("=" * 60)
    print("🌱 DEMO DATA SEEDING")
    print("=" * 60)
    print()

    try:
        # Connect to database
        conn = get_connection()
        print("✅ Connected to database\n")

        # Clean existing demo data if requested
        if args.clean:
            clean_demo_data(conn)

        # Create org admin first (needed as project creator)
        print("👨‍💼 Creating organization admin...")
        cur = conn.cursor()
        org_admin_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO users (
                id, email, username, full_name, hashed_password,
                is_active, is_verified, role
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            org_admin_id,
            'demo.orgadmin@example.com',
            'demo.orgadmin',
            'Demo Org Admin',
            DEMO_PASSWORD_HASH,
            True,
            True,
            'organization_admin'
        ))
        org_admin_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        print(f"   ✓ Created organization admin (ID: {org_admin_id})\n")

        # Seed data in order
        org_id = seed_organization(conn)
        project_id = seed_project(conn, org_id, org_admin_id)
        instructor_ids = seed_instructors(conn, org_id)
        course_ids = seed_courses(conn, instructor_ids)
        student_ids = seed_students(conn)

        # Update enrollment counts (simulate enrollments)
        enrollment_counts = [18, 15, 12, 10, 8, 20]  # Per course
        update_course_enrollments(conn, course_ids, enrollment_counts)

        # Summary
        print("=" * 60)
        print("✅ DEMO DATA SEEDING COMPLETE!")
        print("=" * 60)
        print()
        print(f"📊 Summary:")
        print(f"   • Organizations: 1")
        print(f"   • Projects: 1")
        print(f"   • Tracks: 3")
        print(f"   • Instructors: {len(instructor_ids)}")
        print(f"   • Courses: {len(course_ids)}")
        print(f"   • Students: {len(student_ids)}")
        print()
        print("🔑 Demo Accounts (Password: DemoPass123!):")
        print("   • demo.orgadmin@example.com - Organization Admin")
        print("   • demo.instructor@example.com - Instructor")
        print("   • demo.student@example.com - Student")
        print()
        print("🎥 Ready to regenerate demo videos with realistic data!")
        print()

        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
