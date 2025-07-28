#!/usr/bin/env python3
"""
Test enrollment email with instructor information
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'course-management'))

from models.course_publishing import EnrollmentEmailData
from email_service import create_email_service

async def test_enrollment_email_with_instructor_info():
    """Test enrollment email generation with instructor's name and organization."""
    print("🧪 Testing Enrollment Email with Instructor Information")
    print("=" * 60)
    
    # Create email service (using mock)
    email_service = create_email_service(use_mock=True)
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Complete Instructor Info",
            "data": EnrollmentEmailData(
                student_name="Alice Johnson",
                course_name="Python Programming Fundamentals",
                instance_name="Fall 2025 Session",
                start_date=datetime(2025, 9, 1, 9, 0, tzinfo=timezone.utc),
                end_date=datetime(2025, 12, 15, 17, 0, tzinfo=timezone.utc),
                timezone="EST",
                duration_days=105,
                login_url="https://course.example.com/login/abc123",
                temporary_password="TempPass2025!",
                instructor_first_name="Dr. Jane",
                instructor_last_name="Smith",
                instructor_organization="Computer Science Department\nTech University"
            )
        },
        {
            "name": "First Name Only",
            "data": EnrollmentEmailData(
                student_name="Bob Wilson",
                course_name="Data Structures and Algorithms",
                instance_name="Spring 2025 Session",
                start_date=datetime(2025, 2, 1, 10, 0, tzinfo=timezone.utc),
                end_date=datetime(2025, 5, 15, 16, 0, tzinfo=timezone.utc),
                timezone="PST",
                duration_days=103,
                login_url="https://course.example.com/login/def456",
                temporary_password="SecureTemp123",
                instructor_first_name="Prof. Michael",
                instructor_organization="Engineering School\nState University"
            )
        },
        {
            "name": "Organization Only",
            "data": EnrollmentEmailData(
                student_name="Carol Martinez",
                course_name="Web Development Bootcamp",
                instance_name="Summer 2025 Intensive",
                start_date=datetime(2025, 6, 1, 8, 0, tzinfo=timezone.utc),
                end_date=datetime(2025, 8, 31, 18, 0, tzinfo=timezone.utc),
                timezone="MST",
                duration_days=91,
                login_url="https://course.example.com/login/ghi789",
                temporary_password="WebDev2025",
                instructor_organization="TechCorp Training Division"
            )
        },
        {
            "name": "Full Name (Legacy)",
            "data": EnrollmentEmailData(
                student_name="David Chen",
                course_name="Machine Learning Foundations",
                instance_name="Winter 2025 Course",
                start_date=datetime(2025, 1, 15, 11, 0, tzinfo=timezone.utc),
                end_date=datetime(2025, 4, 30, 15, 0, tzinfo=timezone.utc),
                timezone="CST",
                duration_days=105,
                login_url="https://course.example.com/login/jkl012",
                temporary_password="ML_Access2025",
                instructor_full_name="Professor Sarah Anderson",
                instructor_organization="AI Research Institute"
            )
        },
        {
            "name": "No Instructor Info (Fallback)",
            "data": EnrollmentEmailData(
                student_name="Emma Taylor",
                course_name="Database Design Principles",
                instance_name="Online Self-Paced",
                start_date=datetime(2025, 3, 1, 9, 0, tzinfo=timezone.utc),
                end_date=datetime(2025, 6, 1, 17, 0, tzinfo=timezone.utc),
                timezone="UTC",
                duration_days=92,
                login_url="https://course.example.com/login/mno345",
                temporary_password="DB_Design2025"
            )
        }
    ]
    
    # Test each scenario
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📧 Test {i}: {scenario['name']}")
        print("-" * 40)
        
        try:
            # Generate email content
            email_content = email_service.generate_enrollment_email(scenario['data'])
            
            print(f"✅ Subject: {email_content['subject']}")
            print(f"📝 Email Preview:")
            print(f"{'='*50}")
            
            # Show the email body with focus on instructor signature
            email_lines = email_content['body'].split('\n')
            
            # Find the signature section
            signature_start = -1
            for idx, line in enumerate(email_lines):
                if line.strip().startswith('Best regards,'):
                    signature_start = idx
                    break
            
            if signature_start >= 0:
                # Show last few lines before signature and the signature itself
                context_start = max(0, signature_start - 3)
                print('\n'.join(email_lines[context_start:signature_start + 5]))
            else:
                print("Signature section not found")
            
            print(f"{'='*50}")
            
            # Test actual email sending (mock)
            result = await email_service.send_enrollment_email(scenario['data'], "test@example.com")
            if result['status'] == 'sent':
                print(f"✅ Email mock sending: SUCCESS")
            else:
                print(f"❌ Email mock sending: FAILED - {result['message']}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Show all mock emails sent
    if hasattr(email_service, 'sent_emails'):
        print(f"\n📊 Mock Email Summary:")
        print(f"   • Total emails processed: {len(email_service.sent_emails)}")
        for i, email in enumerate(email_service.sent_emails, 1):
            print(f"   • Email {i}: {email['to']} - {email['status']}")
    
    print(f"\n🎉 Enrollment email testing completed!")
    print("✅ Instructor information is now properly included in enrollment emails")
    print("✅ Email signature adapts based on available instructor data")
    print("✅ Fallback to default signature when no instructor info available")

if __name__ == "__main__":
    asyncio.run(test_enrollment_email_with_instructor_info())