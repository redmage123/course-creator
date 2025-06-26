#!/usr/bin/env python3
"""
Database setup script for Course Creator platform
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def create_database():
    """Create the main database if it doesn't exist"""
    
    # Connect to PostgreSQL without specifying database
    admin_url = "postgresql+asyncpg://course_user:course_pass@localhost:5432/postgres"
    engine = create_async_engine(admin_url)
    
    async with engine.begin() as conn:
        # Check if database exists
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname='course_creator'")
        )
        exists = result.fetchone()
        
        if not exists:
            await conn.execute(text("CREATE DATABASE course_creator"))
            print("✅ Created course_creator database")
        else:
            print("✅ Database course_creator already exists")
    
    await engine.dispose()

async def create_tables():
    """Create all tables for all services"""
    from shared.database.base import engine, Base
    
    # Import all service models to register them with Base
    try:
        from services.course_management.database.models import Course, Lesson
        print("✅ Loaded course management models")
    except ImportError as e:
        print(f"⚠️  Could not load course management models: {e}")
    
    try:
        from services.user_management.database.models import User, RefreshToken
        print("✅ Loaded user management models")
    except ImportError as e:
        print(f"⚠️  Could not load user management models: {e}")
    
    try:
        from services.enrollment.database.models import Enrollment, LessonProgress, Certificate, LearningPath
        print("✅ Loaded enrollment models")
    except ImportError as e:
        print(f"⚠️  Could not load enrollment models: {e}")
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Created all database tables")

async def main():
    print("🗄️  Setting up Course Creator database...")
    
    try:
        await create_database()
        await create_tables()
        print("🎉 Database setup completed successfully!")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

chmod +x setup-database.py
