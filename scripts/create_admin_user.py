#!/usr/bin/env python3
"""
Create a site admin user in the database
"""
import psycopg
from passlib.context import CryptContext
import uuid
from datetime import datetime

# Password context for bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = 5433
DB_USER = "postgres"
DB_PASSWORD = "postgres_password"
DB_NAME = "course_creator"
DB_SCHEMA = "course_creator"

# Admin user details
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@courseplatform.com"
ADMIN_PASSWORD = "admin123!"
ADMIN_ROLE = "site_admin"

def create_admin_user():
    """Create the site admin user"""

    # Hash the password
    hashed_password = pwd_context.hash(ADMIN_PASSWORD)
    user_id = str(uuid.uuid4())

    print(f"Connecting to database...")
    conn = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )

    try:
        cursor = conn.cursor()

        # Check if admin already exists
        cursor.execute(
            f"""
            SELECT id FROM {DB_SCHEMA}.users
            WHERE username = %s OR email = %s
            """,
            (ADMIN_USERNAME, ADMIN_EMAIL)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            print(f"⚠️  User already exists with username '{ADMIN_USERNAME}' or email '{ADMIN_EMAIL}'")
            print(f"Updating password instead...")

            cursor.execute(
                f"""
                UPDATE {DB_SCHEMA}.users
                SET hashed_password = %s, updated_at = CURRENT_TIMESTAMP
                WHERE username = %s
                """,
                (hashed_password, ADMIN_USERNAME)
            )
            conn.commit()
            print(f"✅ Admin password updated successfully")
        else:
            # Insert new admin user
            cursor.execute(
                f"""
                INSERT INTO {DB_SCHEMA}.users
                (id, username, email, hashed_password, role, is_active, created_at, updated_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    ADMIN_USERNAME,
                    ADMIN_EMAIL,
                    hashed_password,
                    ADMIN_ROLE,
                    True,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )

            conn.commit()
            print(f"✅ Admin user created successfully")

        print(f"\n📋 Admin Credentials:")
        print(f"   Username: {ADMIN_USERNAME}")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print(f"   Role: {ADMIN_ROLE}")

        cursor.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin_user()
