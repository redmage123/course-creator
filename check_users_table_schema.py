#!/usr/bin/env python3
"""
Check the users table schema to find the password column name
"""
import asyncio
import os
import databases
from sqlalchemy.dialects import postgresql

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

async def check_users_table_schema():
    """Check the users table schema"""
    
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Get table schema
        schema_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """
        
        columns = await database.fetch_all(schema_query)
        
        print("Users table schema:")
        for column in columns:
            print(f"  - {column['column_name']}: {column['data_type']} (nullable: {column['is_nullable']})")
        
        # Also check a sample user to see the data
        print("\nSample user data:")
        sample_query = "SELECT * FROM users WHERE email = 'bbrelin@gmail.com' LIMIT 1"
        sample_user = await database.fetch_one(sample_query)
        
        if sample_user:
            for key, value in sample_user.items():
                if 'password' in key.lower():
                    print(f"  - {key}: {value}")
                else:
                    print(f"  - {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(check_users_table_schema())