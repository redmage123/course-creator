#!/usr/bin/env python3
"""
Create Test Users for E2E Testing

This script creates test users directly in the database for E2E testing.
Passwords are hashed using bcrypt as expected by the user-management service.
"""

import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import bcrypt

# Database connection parameters
DB_PARAMS = {
    'host': 'localhost',
    'port': 5433,  # Docker-mapped port
    'user': 'postgres',
    'password': 'postgres_password',
    'database': 'course_creator'
}

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_users_table(cursor):
    """Create users table if it doesn't exist."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role_name VARCHAR(50) NOT NULL,
            organization_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)
    print("✅ Users table created/verified")

def create_test_users(cursor):
    """Create test users for E2E testing."""

    # Hash passwords once
    hashed_pw = hash_password('password123')

    test_users = [
        ('admin', 'admin@example.com', hashed_pw, 'site_admin', None),
        ('instructor1', 'instructor@example.com', hashed_pw, 'instructor', 1),
        ('orgadmin1', 'orgadmin@example.com', hashed_pw, 'organization_admin', 1),
        ('student1', 'student@example.com', hashed_pw, 'student', 1),
    ]

    for username, email, password_hash, role, org_id in test_users:
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role_name, organization_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, (username, email, password_hash, role, org_id))
            print(f"✅ Created user: {username} ({role}) - {email}")
        except Exception as e:
            print(f"⚠️  User {username} might already exist: {e}")

def main():
    """Main function to create test users."""
    try:
        # Connect to PostgreSQL
        print(f"🔌 Connecting to database at {DB_PARAMS['host']}:{DB_PARAMS['port']}...")
        conn = psycopg2.connect(**DB_PARAMS)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Create tables
        create_users_table(cursor)

        # Create test users
        print("\n👥 Creating test users...")
        create_test_users(cursor)

        # Verify users
        cursor.execute("SELECT username, email, role_name FROM users ORDER BY role_name;")
        users = cursor.fetchall()

        print("\n📋 Current users in database:")
        for username, email, role in users:
            print(f"  - {username:20} {email:30} {role}")

        cursor.close()
        conn.close()

        print("\n✅ Test users created successfully!")
        print("\n🔑 Test Credentials:")
        print("  Username/Email: instructor@example.com | Password: password123")
        print("  Username/Email: orgadmin@example.com  | Password: password123")
        print("  Username/Email: student@example.com   | Password: password123")
        print("  Username/Email: admin@example.com     | Password: password123")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
