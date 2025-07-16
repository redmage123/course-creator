#!/usr/bin/env python3
"""
Check what bbrelin's current password hash is in the database
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

async def check_bbrelin_current_password():
    """Check bbrelin's current password hash"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Get bbrelin's current password hash
        query = "SELECT email, hashed_password FROM users WHERE email = 'bbrelin@gmail.com'"
        user = await database.fetch_one(query)
        
        if not user:
            print("❌ bbrelin user not found!")
            return
        
        current_hash = user['hashed_password']
        print(f"Current password hash: {current_hash}")
        
        # Test if the password you provided works
        test_password = "P0stgr3s:atao12e"
        if pwd_context.verify(test_password, current_hash):
            print(f"✅ Password '{test_password}' works with current hash")
        else:
            print(f"❌ Password '{test_password}' does NOT work with current hash")
            
        # Test other possible passwords
        other_passwords = [
            "P0stgr3s",
            "atao12e", 
            "postgres",
            "password123",
            "Password123!"
        ]
        
        print("\nTesting other passwords:")
        for password in other_passwords:
            if pwd_context.verify(password, current_hash):
                print(f"✅ Password '{password}' works!")
            else:
                print(f"❌ Password '{password}' does not work")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(check_bbrelin_current_password())