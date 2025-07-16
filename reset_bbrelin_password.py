#!/usr/bin/env python3
"""
Reset bbrelin's password to a known value
"""
import asyncio
import os
import databases
import hashlib
from sqlalchemy.dialects import postgresql

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

async def reset_bbrelin_password():
    """Reset bbrelin's password to a known value"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Get bbrelin user
        bbrelin_query = "SELECT id, email, full_name FROM users WHERE email = 'bbrelin@gmail.com'"
        bbrelin_user = await database.fetch_one(bbrelin_query)
        
        if not bbrelin_user:
            print("❌ bbrelin user not found!")
            return
        
        print(f"Found bbrelin user: {bbrelin_user['email']} ({bbrelin_user['full_name']})")
        
        # Set a new password
        new_password = "Bbrelin123!"
        hashed_password = hash_password(new_password)
        
        # Update password
        update_query = "UPDATE users SET hashed_password = :hashed_password WHERE email = 'bbrelin@gmail.com'"
        await database.execute(update_query, {"hashed_password": hashed_password})
        
        print(f"✅ Reset bbrelin's password to: {new_password}")
        print(f"Password hash: {hashed_password}")
        
        # Verify the user can be found with the new password
        verify_query = "SELECT id, email, hashed_password FROM users WHERE email = 'bbrelin@gmail.com'"
        user = await database.fetch_one(verify_query)
        
        if user and user['hashed_password'] == hashed_password:
            print("✅ Password reset verified!")
        else:
            print("❌ Password reset verification failed")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(reset_bbrelin_password())