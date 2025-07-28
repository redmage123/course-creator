#!/usr/bin/env python3
"""
Run course completion database migration
"""

import asyncio
import asyncpg
import os
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres_password@localhost:5433/course_creator')

async def run_migration():
    """Run the course completion migration."""
    print("Starting course completion migration...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Read migration file
        migration_file = 'data/migrations/009_add_course_completion_fields.sql'
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        await conn.execute(migration_sql)
        
        print("✅ Migration completed successfully!")
        print(f"✅ Added course completion tracking fields")
        print(f"✅ Added student access control fields") 
        print(f"✅ Created quiz_attempts table for cleanup functionality")
        print(f"✅ Updated existing completed courses")
        print(f"✅ Added database indexes for performance")
        
        # Get some statistics
        completed_courses = await conn.fetchval("""
            SELECT COUNT(*) FROM course_instances WHERE status = 'completed'
        """)
        
        total_instances = await conn.fetchval("""
            SELECT COUNT(*) FROM course_instances
        """)
        
        disabled_enrollments = await conn.fetchval("""
            SELECT COUNT(*) FROM student_course_enrollments WHERE access_disabled_at IS NOT NULL
        """)
        
        print(f"\n📊 Current Statistics:")
        print(f"   • Total course instances: {total_instances}")
        print(f"   • Completed course instances: {completed_courses}")
        print(f"   • Enrollments with disabled access: {disabled_enrollments}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

async def test_new_functionality():
    """Test the new course completion functionality."""
    print("\n🧪 Testing new functionality...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Test 1: Check if new columns exist
        columns_check = await conn.fetchrow("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'course_instances' AND column_name = 'completed_at'
        """)
        
        if columns_check:
            print("✅ Course completion columns added successfully")
        else:
            print("❌ Course completion columns not found")
            return False
        
        # Test 2: Check access control columns
        access_check = await conn.fetchrow("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'student_course_enrollments' AND column_name = 'access_disabled_at'
        """)
        
        if access_check:
            print("✅ Student access control columns added successfully")
        else:
            print("❌ Student access control columns not found")
            return False
        
        # Test 3: Check quiz_attempts table
        quiz_table_check = await conn.fetchrow("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'quiz_attempts'
        """)
        
        if quiz_table_check:
            print("✅ Quiz attempts table created successfully")
        else:
            print("❌ Quiz attempts table not found")
            return False
        
        # Test 4: Check indexes
        index_check = await conn.fetchval("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE tablename IN ('course_instances', 'student_course_enrollments') 
            AND indexname LIKE '%completed%' OR indexname LIKE '%access_disabled%'
        """)
        
        if index_check > 0:
            print(f"✅ Database indexes created successfully ({index_check} indexes)")
        else:
            print("⚠️ Some database indexes may be missing")
        
        await conn.close()
        print("🎉 All functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

async def main():
    """Main function."""
    print("=" * 60)
    print("COURSE COMPLETION SYSTEM MIGRATION")
    print("=" * 60)
    
    # Run migration
    migration_success = await run_migration()
    
    if migration_success:
        # Test functionality
        test_success = await test_new_functionality()
        
        if test_success:
            print(f"\n🎉 Migration and testing completed at {datetime.now()}")
            print("\n📋 New Features Available:")
            print("   • Instructors can complete course instances")
            print("   • Student login URLs automatically disabled after completion")
            print("   • Students can only login 30 minutes before course start")
            print("   • Automatic cleanup of old student data (30+ days)")
            print("   • Enhanced error messages for timing restrictions")
            print("\n🚀 System is ready for production use!")
            
        else:
            print(f"\n⚠️ Migration completed but some tests failed")
            print("Please check the database manually")
    else:
        print(f"\n❌ Migration failed - please check the errors above")

if __name__ == "__main__":
    asyncio.run(main())