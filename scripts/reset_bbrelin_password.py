#!/usr/bin/env python3
"""
Script to reset bbrelin user password
Used for E2E testing to ensure known credentials
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bcrypt
import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "course_creator"
DB_USER = "course_user"
DB_PASSWORD = "course_pass"

# bbrelin user credentials
BBRELIN_USERNAME = "bbrelin"
BBRELIN_PASSWORD = "TestPassword123!"

def reset_bbrelin_password():
    """Reset bbrelin user password to known value"""
    try:
        # Hash the password
        password_bytes = BBRELIN_PASSWORD.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        hashed_str = hashed.decode('utf-8')

        print(f"🔑 Connecting to database...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Check if bbrelin user exists
        cursor.execute(
            "SELECT id, username, email, role FROM users WHERE username = %s",
            (BBRELIN_USERNAME,)
        )
        user = cursor.fetchone()

        if user:
            print(f"✅ Found existing user: {user[1]} ({user[2]}) - Role: {user[3]}")

            # Update password
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE username = %s",
                (hashed_str, BBRELIN_USERNAME)
            )
            conn.commit()
            print(f"✅ Password reset for user '{BBRELIN_USERNAME}'")
            print(f"   New password: {BBRELIN_PASSWORD}")
        else:
            print(f"❌ User '{BBRELIN_USERNAME}' not found in database")
            print(f"   Please create the user first")
            return False

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Resetting bbrelin user password...")
    success = reset_bbrelin_password()
    sys.exit(0 if success else 1)
