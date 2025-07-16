#!/usr/bin/env python3
"""
Check bbrelin's password hash in the database
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

async def check_bbrelin_password():
    """Check bbrelin's password hash and test various formats"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Get bbrelin user's password hash
        query = "SELECT email, hashed_password FROM users WHERE email = 'bbrelin@gmail.com'"
        user = await database.fetch_one(query)
        
        if not user:
            print("❌ bbrelin user not found!")
            return
        
        current_hash = user['hashed_password']
        print(f"Current password hash: {current_hash}")
        
        # Test various password formats
        test_passwords = [
            "P0stgr3s:atao12e",
            "P0stgr3s",
            "atao12e",
            "postgres",
            "password123",
            "Password123!",
            "bbrelin123",
            "Bbrelin123!"
        ]
        
        print("\nTesting password formats:")
        for password in test_passwords:
            test_hash = hash_password(password)
            matches = test_hash == current_hash
            print(f"  {password} -> {test_hash} {'✅' if matches else '❌'}")
            
            if matches:
                print(f"🎉 Found matching password: {password}")
                return password
        
        print("\n❌ No matching password found with SHA-256 hashing")
        print("The password might use a different hashing algorithm")
        
        # Let's also check what a working user's password hash looks like
        print("\nChecking test instructor password hash for comparison:")
        test_query = "SELECT email, hashed_password FROM users WHERE email = 'instructor@courseplatform.com'"
        test_user = await database.fetch_one(test_query)
        
        if test_user:
            test_hash = test_user['hashed_password']
            print(f"Test instructor hash: {test_hash}")
            
            # Test if it matches our known password
            known_password = "Instructor123!"
            known_hash = hash_password(known_password)
            print(f"Known password '{known_password}' -> {known_hash}")
            print(f"Matches: {'✅' if known_hash == test_hash else '❌'}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(check_bbrelin_password())