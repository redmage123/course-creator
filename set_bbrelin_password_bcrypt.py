#!/usr/bin/env python3
"""
Set bbrelin's password using bcrypt (same as the system uses)
"""
import asyncio
import os
import databases
from passlib.context import CryptContext
from sqlalchemy.dialects import postgresql

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

# Same password context as the system
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def set_bbrelin_password():
    """Set bbrelin's password using bcrypt"""
    
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
        
        # Set password to the provided value
        new_password = "P0stgr3s:atao12e"
        hashed_password = pwd_context.hash(new_password)
        
        print(f"Setting password to: {new_password}")
        print(f"Bcrypt hash: {hashed_password}")
        
        # Update password
        update_query = "UPDATE users SET hashed_password = :hashed_password WHERE email = 'bbrelin@gmail.com'"
        await database.execute(update_query, {"hashed_password": hashed_password})
        
        print(f"✅ Updated bbrelin's password")
        
        # Verify the password works
        verify_query = "SELECT hashed_password FROM users WHERE email = 'bbrelin@gmail.com'"
        user = await database.fetch_one(verify_query)
        
        if user:
            stored_hash = user['hashed_password']
            if pwd_context.verify(new_password, stored_hash):
                print("✅ Password verification successful!")
            else:
                print("❌ Password verification failed!")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(set_bbrelin_password())