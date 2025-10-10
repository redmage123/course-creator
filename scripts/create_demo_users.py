#!/usr/bin/env python3
"""
Create Demo Users and Data Structure for Video Recording
Creates a complete demo environment with org admin, instructor, and student
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import sys
import uuid

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'course_creator',
    'user': 'postgres',
    'password': 'postgres_password'
}

# Demo credentials (simple for automation)
DEMO_USERS = {
    'org_admin': {
        'username': 'demo_orgadmin',
        'email': 'demo.admin@techcorp.training',
        'password': 'Demo1234!',
        'role': 'organization_admin',
        'first_name': 'Sarah',
        'last_name': 'Martinez'
    },
    'instructor': {
        'username': 'demo_instructor',
        'email': 'demo.instructor@techcorp.training',
        'password': 'Demo1234!',
        'role': 'instructor',
        'first_name': 'James',
        'last_name': 'Chen'
    },
    'student': {
        'username': 'demo_student',
        'email': 'demo.student@techcorp.training',
        'password': 'Demo1234!',
        'role': 'student',
        'first_name': 'Alex',
        'last_name': 'Johnson'
    }
}

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_demo_structure():
    """Create complete demo structure"""
    conn = None
    try:
        print("="*80)
        print("🎬 Creating Demo Users and Structure")
        print("="*80)
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Create Demo Organization
        print("\n1️⃣ Creating demo organization...")
        org_slug = 'techcorp-global-training'
        cur.execute("""
            INSERT INTO organizations (
                name, slug, domain, description, created_at, updated_at
            ) VALUES (
                'TechCorp Global Training', %s, 'techcorp.training',
                'Enterprise software development training for 500+ engineers worldwide',
                NOW(), NOW()
            )
            ON CONFLICT (slug) DO UPDATE
            SET name = EXCLUDED.name,
                domain = EXCLUDED.domain,
                description = EXCLUDED.description,
                updated_at = NOW()
            RETURNING id
        """, (org_slug,))
        result = cur.fetchone()
        org_id = result['id']  # Use the returned ID
        print(f"   ✅ Organization: TechCorp Global Training (ID: {org_id})")
        
        # 2. Create Demo Users
        print("\n2️⃣ Creating demo users...")
        user_ids = {}
        
        for role_key, user_data in DEMO_USERS.items():
            hashed_pw = hash_password(user_data['password'])
            
            cur.execute("""
                INSERT INTO users (
                    username, email, hashed_password, role_name,
                    organization_id, first_name, last_name,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                ON CONFLICT (username) DO UPDATE
                SET email = EXCLUDED.email,
                    hashed_password = EXCLUDED.hashed_password,
                    role_name = EXCLUDED.role_name,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    organization_id = EXCLUDED.organization_id,
                    updated_at = NOW()
                RETURNING id, username, role_name
            """, (
                user_data['username'],
                user_data['email'],
                hashed_pw,
                user_data['role'],
                org_id,
                user_data['first_name'],
                user_data['last_name']
            ))
            
            result = cur.fetchone()
            user_ids[role_key] = result['id']
            print(f"   ✅ {result['role_name']}: {result['username']} (ID: {result['id']})")
        
        # 3. Create Demo Project
        print("\n3️⃣ Creating demo project...")
        cur.execute("""
            INSERT INTO projects (
                name, description, organization_id, created_by_user_id,
                created_at, updated_at
            ) VALUES (
                'Web Development Bootcamp',
                'Comprehensive full-stack web development training program',
                %s, %s, NOW(), NOW()
            )
            ON CONFLICT (name, organization_id) DO UPDATE
            SET description = EXCLUDED.description,
                updated_at = NOW()
            RETURNING id, name
        """, (org_id, user_ids['org_admin']))
        project = cur.fetchone()
        print(f"   ✅ Project: {project['name']} (ID: {project['id']})")
        
        # 4. Create Demo Track
        print("\n4️⃣ Creating demo track...")
        cur.execute("""
            INSERT INTO tracks (
                name, description, project_id, organization_id,
                created_at, updated_at
            ) VALUES (
                'Frontend Developer Path',
                'Master modern frontend technologies: React, TypeScript, and more',
                %s, %s, NOW(), NOW()
            )
            ON CONFLICT (name, project_id) DO UPDATE
            SET description = EXCLUDED.description,
                updated_at = NOW()
            RETURNING id, name
        """, (project['id'], org_id))
        track = cur.fetchone()
        print(f"   ✅ Track: {track['name']} (ID: {track['id']})")
        
        # 5. Create Demo Course
        print("\n5️⃣ Creating demo course...")
        cur.execute("""
            INSERT INTO courses (
                title, description, instructor_id, organization_id,
                status, created_at, updated_at
            ) VALUES (
                'Introduction to React',
                'Learn React fundamentals from scratch with hands-on projects',
                %s, %s, 'published', NOW(), NOW()
            )
            ON CONFLICT (title, organization_id) DO UPDATE
            SET description = EXCLUDED.description,
                instructor_id = EXCLUDED.instructor_id,
                status = EXCLUDED.status,
                updated_at = NOW()
            RETURNING id, title
        """, (user_ids['instructor'], org_id))
        course = cur.fetchone()
        print(f"   ✅ Course: {course['title']} (ID: {course['id']})")
        
        # 6. Enroll student in course
        print("\n6️⃣ Enrolling demo student...")
        cur.execute("""
            INSERT INTO enrollments (
                user_id, course_id, enrolled_at, status
            ) VALUES (
                %s, %s, NOW(), 'active'
            )
            ON CONFLICT (user_id, course_id) DO UPDATE
            SET status = 'active',
                enrolled_at = NOW()
            RETURNING id
        """, (user_ids['student'], course['id']))
        enrollment = cur.fetchone()
        print(f"   ✅ Enrollment created (ID: {enrollment['id']})")
        
        conn.commit()
        
        # Print summary
        print("\n" + "="*80)
        print("✅ DEMO STRUCTURE CREATED SUCCESSFULLY")
        print("="*80)
        print("\n📋 Demo Credentials:\n")
        for role_key, user_data in DEMO_USERS.items():
            print(f"   {user_data['role'].upper()}:")
            print(f"      Username: {user_data['username']}")
            print(f"      Password: {user_data['password']}")
            print(f"      Email: {user_data['email']}")
            print()
        
        print("="*80)
        print("🎯 Ready for video recording with real authentication!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    success = create_demo_structure()
    sys.exit(0 if success else 1)
