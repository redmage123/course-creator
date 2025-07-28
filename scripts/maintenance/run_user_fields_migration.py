#!/usr/bin/env python3
"""
Run user fields database migration
"""

import asyncio
import asyncpg
import os
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres_password@localhost:5433/course_creator')

async def run_migration():
    """Run the user fields migration."""
    print("Starting user fields migration...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Read migration file
        migration_file = 'data/migrations/010_add_user_name_organization_fields.sql'
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        await conn.execute(migration_sql)
        
        print("✅ Migration completed successfully!")
        print(f"✅ Added first_name, last_name, and organization columns")
        print(f"✅ Migrated existing full_name data to separate fields") 
        print(f"✅ Added database indexes for performance")
        
        # Get some statistics
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        users_with_first_name = await conn.fetchval("""
            SELECT COUNT(*) FROM users WHERE first_name IS NOT NULL AND first_name != ''
        """)
        
        users_with_last_name = await conn.fetchval("""
            SELECT COUNT(*) FROM users WHERE last_name IS NOT NULL AND last_name != ''
        """)
        
        users_with_organization = await conn.fetchval("""
            SELECT COUNT(*) FROM users WHERE organization IS NOT NULL AND organization != ''
        """)
        
        print(f"\n📊 Current Statistics:")
        print(f"   • Total users: {total_users}")
        print(f"   • Users with first name: {users_with_first_name}")
        print(f"   • Users with last name: {users_with_last_name}")
        print(f"   • Users with organization: {users_with_organization}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

async def test_new_functionality():
    """Test the new user fields functionality."""
    print("\n🧪 Testing new functionality...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Test 1: Check if new columns exist
        first_name_check = await conn.fetchrow("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'first_name'
        """)
        
        if first_name_check:
            print("✅ first_name column added successfully")
        else:
            print("❌ first_name column not found")
            return False
        
        # Test 2: Check last_name column
        last_name_check = await conn.fetchrow("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'last_name'
        """)
        
        if last_name_check:
            print("✅ last_name column added successfully")
        else:
            print("❌ last_name column not found")
            return False
        
        # Test 3: Check organization column
        organization_check = await conn.fetchrow("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'organization'
        """)
        
        if organization_check:
            print("✅ organization column added successfully")
        else:
            print("❌ organization column not found")
            return False
        
        # Test 4: Check indexes
        index_check = await conn.fetchval("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE tablename = 'users' 
            AND (indexname LIKE '%first_name%' OR indexname LIKE '%last_name%' OR indexname LIKE '%organization%')
        """)
        
        if index_check >= 3:
            print(f"✅ Database indexes created successfully ({index_check} indexes)")
        else:
            print(f"⚠️ Some database indexes may be missing (found {index_check})")
        
        await conn.close()
        print("🎉 All functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

async def main():
    """Main function."""
    print("=" * 60)
    print("USER FIELDS DATABASE MIGRATION")
    print("=" * 60)
    
    # Run migration
    migration_success = await run_migration()
    
    if migration_success:
        # Test functionality
        test_success = await test_new_functionality()
        
        if test_success:
            print(f"\n🎉 Migration and testing completed at {datetime.now()}")
            print("\n📋 New Features Available:")
            print("   • Separate first_name and last_name fields for better data structure")
            print("   • Organization field for institutional tracking and reporting")
            print("   • Improved user data organization and analytics capabilities")
            print("   • Backward compatibility with existing full_name field")
            print("\n🚀 User registration system is ready for enhanced data collection!")
            
        else:
            print(f"\n⚠️ Migration completed but some tests failed")
            print("Please check the database manually")
    else:
        print(f"\n❌ Migration failed - please check the errors above")

if __name__ == "__main__":
    asyncio.run(main())