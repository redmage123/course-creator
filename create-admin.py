#!/usr/bin/env python3
"""
Create initial admin user for Course Creator Platform
"""

import asyncio
import os
import sys
from passlib.context import CryptContext
import databases
import sqlalchemy
from sqlalchemy.dialects import postgresql

# Add the services directory to the path
sys.path.append('/home/bbrelin/course-creator/services/user-management')

# Database configuration
DB_PASSWORD = os.getenv('DB_PASSWORD', 'c0urs3:atao12e')
DATABASE_URL = f"postgresql+asyncpg://course_user:{DB_PASSWORD}@localhost:5433/course_creator"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Users table definition
users_table = sqlalchemy.Table(
    'users',
    sqlalchemy.MetaData(),
    sqlalchemy.Column('id', postgresql.UUID, primary_key=True, server_default=sqlalchemy.text('uuid_generate_v4()')),
    sqlalchemy.Column('email', sqlalchemy.String(255), unique=True, nullable=False),
    sqlalchemy.Column('username', sqlalchemy.String(100), unique=True, nullable=False),
    sqlalchemy.Column('full_name', sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column('hashed_password', sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column('is_active', sqlalchemy.Boolean, default=True),
    sqlalchemy.Column('is_verified', sqlalchemy.Boolean, default=False),
    sqlalchemy.Column('role', sqlalchemy.String(50), default='student'),
)

async def create_admin_user():
    """Create the initial admin user"""
    
    # Admin user details
    admin_email = "admin@courseplatform.com"
    admin_password = "Admin123!"
    admin_full_name = "Platform Administrator"
    
    # Connect to database
    database = databases.Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database")
        
        # Check if admin already exists
        existing_query = users_table.select().where(users_table.c.email == admin_email)
        existing_admin = await database.fetch_one(existing_query)
        
        if existing_admin:
            print(f"Admin user {admin_email} already exists!")
            return
        
        # Hash password
        hashed_password = pwd_context.hash(admin_password)
        
        # Create admin user
        insert_query = users_table.insert().values(
            email=admin_email,
            username="admin",
            full_name=admin_full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            role='admin'
        )
        
        result = await database.execute(insert_query)
        print(f"✅ Admin user created successfully!")
        print(f"📧 Email: {admin_email}")
        print(f"🔐 Password: {admin_password}")
        print(f"👤 Role: admin")
        print(f"\n🚨 IMPORTANT: Change the default password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(create_admin_user())