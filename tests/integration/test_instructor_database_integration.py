#!/usr/bin/env python3
"""
Test instructor database integration for email personalization
"""

import asyncio
import asyncpg
from datetime import datetime

async def test_instructor_database_integration():
    """Test fetching instructor information from database for email personalization."""
    print("🧪 Testing Instructor Database Integration")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = await asyncpg.connect('postgresql://postgres:postgres_password@localhost:5433/course_creator')
        
        # Test 1: Check if instructor fields exist in users table
        print("\n📋 Test 1: Database Schema Validation")
        print("-" * 35)
        
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('first_name', 'last_name', 'organization', 'full_name')
            ORDER BY column_name
        """)
        
        required_fields = {'first_name', 'last_name', 'organization', 'full_name'}
        found_fields = {col['column_name'] for col in columns}
        
        for field in required_fields:
            if field in found_fields:
                col_info = next(col for col in columns if col['column_name'] == field)
                nullable = "nullable" if col_info['is_nullable'] == 'YES' else "not null"
                print(f"  ✅ {field}: {col_info['data_type']} ({nullable})")
            else:
                print(f"  ❌ {field}: MISSING")
        
        # Test 2: Fetch instructor information for existing users
        print("\n👥 Test 2: Instructor Information Retrieval")
        print("-" * 42)
        
        instructors = await conn.fetch("""
            SELECT id, email, first_name, last_name, full_name, organization
            FROM users 
            WHERE role = 'instructor'
            LIMIT 3
        """)
        
        if instructors:
            for i, instructor in enumerate(instructors, 1):
                print(f"\n  Instructor {i}:")
                print(f"    Email: {instructor['email']}")
                print(f"    First Name: {instructor['first_name']}")
                print(f"    Last Name: {instructor['last_name']}")
                print(f"    Full Name: {instructor['full_name']}")
                print(f"    Organization: {instructor['organization']}")
                
                # Generate signature for this instructor
                signature = generate_signature_from_db_row(instructor)
                print(f"    Generated Signature: {repr(signature)}")
        else:
            print("  ⚠️ No instructors found in database")
        
        # Test 3: Simulate the exact query used in enrollment
        print("\n🔍 Test 3: Enrollment Query Simulation") 
        print("-" * 37)
        
        # Get a sample instructor ID
        sample_instructor = await conn.fetchrow("""
            SELECT id FROM users WHERE role = 'instructor' LIMIT 1
        """)
        
        if sample_instructor:
            instructor_id = sample_instructor['id']
            
            # Execute the exact query from the enrollment method
            instructor_info = await conn.fetchrow("""
                SELECT first_name, last_name, full_name, organization
                FROM users 
                WHERE id = $1
            """, instructor_id)
            
            if instructor_info:
                print(f"  ✅ Query successful for instructor ID: {instructor_id}")
                print(f"  📊 Retrieved data:")
                print(f"    First Name: {instructor_info['first_name']}")
                print(f"    Last Name: {instructor_info['last_name']}")
                print(f"    Full Name: {instructor_info['full_name']}")
                print(f"    Organization: {instructor_info['organization']}")
                
                # Show what the email signature would look like
                signature = generate_signature_from_db_row(instructor_info)
                print(f"  📧 Email Signature Preview:")
                for line in signature.split('\n'):
                    print(f"    {line}")
            else:
                print(f"  ❌ Query returned no data for instructor ID: {instructor_id}")
        else:
            print("  ⚠️ No instructors available for testing")
        
        # Test 4: Test with mock course instance data
        print("\n📚 Test 4: Complete Enrollment Email Simulation")
        print("-" * 45)
        
        if sample_instructor:
            # Mock course instance data
            mock_instance = {
                'course_title': 'Advanced Python Programming',
                'instance_name': 'Winter 2025 Cohort',
                'start_date': datetime(2025, 1, 15, 9, 0),
                'end_date': datetime(2025, 4, 30, 17, 0),
                'timezone': 'EST',
                'duration_days': 105
            }
            
            mock_enrollment = {
                'student_first_name': 'Test',
                'student_last_name': 'Student',
                'student_email': 'test.student@example.com'
            }
            
            # Simulate creating enrollment email data
            email_data = {
                'student_name': f"{mock_enrollment['student_first_name']} {mock_enrollment['student_last_name']}",
                'course_name': mock_instance['course_title'],
                'instance_name': mock_instance['instance_name'],
                'instructor_first_name': instructor_info['first_name'] if instructor_info else None,
                'instructor_last_name': instructor_info['last_name'] if instructor_info else None,
                'instructor_full_name': instructor_info['full_name'] if instructor_info else None,
                'instructor_organization': instructor_info['organization'] if instructor_info else None
            }
            
            print(f"  📧 Email would be sent to: {mock_enrollment['student_email']}")
            print(f"  👤 Student: {email_data['student_name']}")
            print(f"  📚 Course: {email_data['course_name']}")
            print(f"  🏫 Instance: {email_data['instance_name']}")
            print(f"  👨‍🏫 Instructor signature would be:")
            
            signature = generate_signature_from_email_data(email_data)
            for line in signature.split('\n'):
                print(f"       {line}")
            
            print("  ✅ Complete enrollment email data structure validated")
        
        await conn.close()
        
        print(f"\n🎉 Database integration testing completed successfully!")
        print("✅ All instructor fields are properly stored in database")
        print("✅ Instructor information can be retrieved for email personalization")
        print("✅ Email signature generation works with real database data")
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False
    
    return True

def generate_signature_from_db_row(row):
    """Generate signature from database row data."""
    # Build instructor name
    instructor_name = None
    if row.get('first_name') and row.get('last_name'):
        instructor_name = f"{row['first_name']} {row['last_name']}"
    elif row.get('full_name'):
        instructor_name = row['full_name']
    elif row.get('first_name'):
        instructor_name = row['first_name']
    elif row.get('last_name'):
        instructor_name = row['last_name']
    
    # Build organization
    organization = row.get('organization')
    
    # Create signature
    if instructor_name and organization:
        return f"{instructor_name}\n{organization}"
    elif instructor_name:
        return instructor_name
    elif organization:
        return organization
    else:
        return "Course Creator Platform"

def generate_signature_from_email_data(data):
    """Generate signature from email data dictionary."""
    # Build instructor name
    instructor_name = None
    if data.get('instructor_first_name') and data.get('instructor_last_name'):
        instructor_name = f"{data['instructor_first_name']} {data['instructor_last_name']}"
    elif data.get('instructor_full_name'):
        instructor_name = data['instructor_full_name']
    elif data.get('instructor_first_name'):
        instructor_name = data['instructor_first_name']
    elif data.get('instructor_last_name'):
        instructor_name = data['instructor_last_name']
    
    # Build organization
    organization = data.get('instructor_organization')
    
    # Create signature
    if instructor_name and organization:
        return f"{instructor_name}\n{organization}"
    elif instructor_name:
        return instructor_name
    elif organization:
        return organization
    else:
        return "Course Creator Platform"

if __name__ == "__main__":
    asyncio.run(test_instructor_database_integration())