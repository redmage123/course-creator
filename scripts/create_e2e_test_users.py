#!/usr/bin/env python3
"""
Create E2E Test Users for Notification Tests

Creates test users with expected credentials for E2E notification tests:
- org_admin / org_admin_password
- instructor / instructor_password
- student / student_password
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import sys

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'course_creator',
    'user': 'postgres',
    'password': 'postgres_password'
}

# E2E test users (matching test expectations)
E2E_TEST_USERS = {
    'org_admin': {
        'username': 'org_admin',
        'email': 'orgadmin@e2etest.com',
        'password': 'org_admin_password',
        'role': 'organization_admin',
        'first_name': 'Test',
        'last_name': 'OrgAdmin'
    },
    'instructor': {
        'username': 'instructor',
        'email': 'instructor@e2etest.com',
        'password': 'instructor_password',
        'role': 'instructor',
        'first_name': 'Test',
        'last_name': 'Instructor'
    },
    'student': {
        'username': 'student',
        'email': 'student@e2etest.com',
        'password': 'student_password',
        'role': 'student',
        'first_name': 'Test',
        'last_name': 'Student'
    }
}


def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_e2e_test_users():
    """Create E2E test users and organization"""
    conn = None
    try:
        print("="*80)
        print("🧪 Creating E2E Test Users for Notification Tests")
        print("="*80)

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Create Test Organization
        print("\n1️⃣ Creating test organization...")
        org_slug = 'e2e-test-org'
        cur.execute("""
            INSERT INTO course_creator.organizations (
                name, slug, domain, description, created_at, updated_at
            ) VALUES (
                'E2E Test Organization', %s, 'e2etest.com',
                'Test organization for E2E notification tests',
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
        org_id = result['id']
        print(f"   ✅ Organization: E2E Test Organization (ID: {org_id})")

        # 2. Create Test Users
        print("\n2️⃣ Creating test users...")
        user_ids = {}

        for role_key, user_data in E2E_TEST_USERS.items():
            hashed_pw = hash_password(user_data['password'])

            full_name = f"{user_data['first_name']} {user_data['last_name']}"
            cur.execute("""
                INSERT INTO course_creator.users (
                    username, email, hashed_password, role,
                    full_name, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, NOW(), NOW()
                )
                ON CONFLICT (username) DO UPDATE
                SET email = EXCLUDED.email,
                    hashed_password = EXCLUDED.hashed_password,
                    role = EXCLUDED.role,
                    full_name = EXCLUDED.full_name,
                    updated_at = NOW()
                RETURNING id
            """, (
                user_data['username'], user_data['email'], hashed_pw, user_data['role'],
                full_name
            ))
            result = cur.fetchone()
            user_ids[role_key] = result['id']
            print(f"   ✅ {user_data['role']:20} | {user_data['username']:15} | {user_data['email']}")

        # 3. Create organization membership for org_admin
        print("\n3️⃣ Creating organization memberships...")
        cur.execute("""
            INSERT INTO course_creator.organization_memberships (
                user_id, organization_id, role, is_active, joined_at
            ) VALUES (
                %s, %s, 'organization_admin', true, NOW()
            )
            ON CONFLICT (user_id, organization_id) DO UPDATE
            SET role = EXCLUDED.role,
                is_active = EXCLUDED.is_active
            RETURNING id
        """, (user_ids['org_admin'], org_id))
        print(f"   ✅ Added org_admin to E2E Test Organization")

        conn.commit()

        print("\n" + "="*80)
        print("✅ E2E Test Users Created Successfully!")
        print("="*80)
        print("\n📝 Test Credentials:")
        print("-" * 80)
        for role_key, user_data in E2E_TEST_USERS.items():
            print(f"  {user_data['role']:20} | Username: {user_data['username']:15} | Password: {user_data['password']}")
        print("-" * 80)
        print(f"\n🏢 Organization: E2E Test Organization (slug: {org_slug})")
        print("\n🚀 Ready for E2E tests!")
        print("   Run: HEADLESS=true TEST_BASE_URL=https://localhost:3000 pytest tests/e2e/test_org_admin_notifications_e2e.py -v")
        print("="*80)

        return True

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    success = create_e2e_test_users()
    sys.exit(0 if success else 1)
