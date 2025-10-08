#!/usr/bin/env python3
"""
Reset site admin password to a known value
"""
import psycopg
from passlib.context import CryptContext

# Password context for bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = 5433
DB_USER = "postgres"
DB_PASSWORD = "postgres_password"
DB_NAME = "course_creator"
DB_SCHEMA = "course_creator"

# New admin password
NEW_ADMIN_PASSWORD = "admin123!"

def reset_admin_password():
    """Reset the site admin password"""

    # Hash the new password
    hashed_password = pwd_context.hash(NEW_ADMIN_PASSWORD)

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

        # Update admin password
        cursor.execute(
            f"""
            UPDATE {DB_SCHEMA}.users
            SET hashed_password = %s, updated_at = CURRENT_TIMESTAMP
            WHERE username = 'admin' AND role = 'site_admin'
            """,
            (hashed_password,)
        )

        rows_updated = cursor.rowcount
        conn.commit()

        if rows_updated > 0:
            print(f"✅ Admin password reset successfully")
            print(f"Username: admin")
            print(f"Password: {NEW_ADMIN_PASSWORD}")
        else:
            print(f"❌ No admin user found to update")

        cursor.close()

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    reset_admin_password()
