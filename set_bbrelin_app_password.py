#!/usr/bin/env python3
"""
Set bbrelin's app login password to f00bar123
"""
import asyncio
import os
import databases
from passlib.context import CryptContext

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

# Same password context as the system
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def set_bbrelin_app_password():
    """Set bbrelin's app login password to f00bar123"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Set the correct app login password
        app_password = "f00bar123"
        hashed_password = pwd_context.hash(app_password)
        
        print(f"Setting bbrelin's app login password to: {app_password}")
        
        # Update password
        update_query = "UPDATE users SET hashed_password = :hashed_password WHERE email = 'bbrelin@gmail.com'"
        await database.execute(update_query, {"hashed_password": hashed_password})
        
        print(f"✅ Updated bbrelin's app login password")
        
        # Verify the password works
        verify_query = "SELECT hashed_password FROM users WHERE email = 'bbrelin@gmail.com'"
        user = await database.fetch_one(verify_query)
        
        if user:
            stored_hash = user['hashed_password']
            if pwd_context.verify(app_password, stored_hash):
                print("✅ Password verification successful!")
                print(f"You can now login as bbrelin@gmail.com with password: {app_password}")
            else:
                print("❌ Password verification failed!")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(set_bbrelin_app_password())