#!/usr/bin/env python3
"""
Create Demo Users - Simplified version matching actual schema
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'course_creator',
    'user': 'postgres',
    'password': 'postgres_password'
}

DEMO_USERS = [
    {
        'username': 'demo_orgadmin',
        'email': 'demo.admin@techcorp.training',
        'password': 'Demo1234!',
        'role': 'organization_admin',
        'full_name': 'Sarah Martinez'
    },
    {
        'username': 'demo_instructor',
        'email': 'demo.instructor@techcorp.training',
        'password': 'Demo1234!',
        'role': 'instructor',
        'full_name': 'James Chen'
    },
    {
        'username': 'demo_student',
        'email': 'demo.student@techcorp.training',
        'password': 'Demo1234!',
        'role': 'student',
        'full_name': 'Alex Johnson'
    }
]

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_demo_users():
    conn = None
    try:
        print("="*80)
        print("🎬 Creating Demo Users")
        print("="*80)
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n📋 Creating users...\n")
        
        for user in DEMO_USERS:
            hashed_pw = hash_password(user['password'])
            
            cur.execute("""
                INSERT INTO users (
                    username, email, hashed_password, role, full_name
                ) VALUES (
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (username) DO UPDATE
                SET email = EXCLUDED.email,
                    hashed_password = EXCLUDED.hashed_password,
                    role = EXCLUDED.role,
                    full_name = EXCLUDED.full_name
                RETURNING id, username, role, email
            """, (
                user['username'],
                user['email'],
                hashed_pw,
                user['role'],
                user['full_name']
            ))
            
            result = cur.fetchone()
            print(f"   ✅ {result['role']}: {result['username']}")
            print(f"      Email: {result['email']}")
            print(f"      Password: {user['password']}")
            print(f"      ID: {result['id']}")
            print()
        
        conn.commit()
        
        print("="*80)
        print("✅ DEMO USERS CREATED SUCCESSFULLY")
        print("="*80)
        print("\n🔐 Demo Credentials:\n")
        for user in DEMO_USERS:
            print(f"   {user['role'].upper()}:")
            print(f"      Username: {user['username']}")
            print(f"      Password: {user['password']}")
            print()
        
        print("="*80)
        print("🎯 Ready for video recording!")
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
    success = create_demo_users()
    sys.exit(0 if success else 1)
