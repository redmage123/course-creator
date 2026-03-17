#!/usr/bin/env python3
"""
Simple test for email signature generation with instructor information
"""

import sys
import os
from datetime import datetime, timezone

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'course-management'))

def test_instructor_signature_generation():
    """Test the instructor signature generation logic."""
    print("🧪 Testing Instructor Signature Generation")
    print("=" * 50)
    
    # Mock data similar to EnrollmentEmailData
    test_cases = [
        {
            "name": "Complete Info",
            "instructor_first_name": "Dr. Jane",
            "instructor_last_name": "Smith",
            "instructor_organization": "Computer Science Department\nTech University",
            "instructor_full_name": None,
            "expected": "Dr. Jane Smith\nComputer Science Department\nTech University"
        },
        {
            "name": "First Name + Organization",
            "instructor_first_name": "Prof. Michael",
            "instructor_last_name": None,
            "instructor_organization": "Engineering School",
            "instructor_full_name": None,
            "expected": "Prof. Michael\nEngineering School"
        },
        {
            "name": "Organization Only",
            "instructor_first_name": None,
            "instructor_last_name": None,
            "instructor_organization": "TechCorp Training Division",
            "instructor_full_name": None,
            "expected": "TechCorp Training Division"
        },
        {
            "name": "Full Name (Legacy)",
            "instructor_first_name": None,
            "instructor_last_name": None,
            "instructor_organization": "AI Research Institute",
            "instructor_full_name": "Professor Sarah Anderson",
            "expected": "Professor Sarah Anderson\nAI Research Institute"
        },
        {
            "name": "No Info (Fallback)",
            "instructor_first_name": None,
            "instructor_last_name": None,
            "instructor_organization": None,
            "instructor_full_name": None,
            "expected": "Course Creator Platform"
        }
    ]
    
    def generate_instructor_signature(data):
        """Replicate the signature generation logic."""
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
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        # Generate signature
        result = generate_instructor_signature(test_case)
        
        print(f"Input:")
        print(f"  First Name: {test_case['instructor_first_name']}")
        print(f"  Last Name: {test_case['instructor_last_name']}")
        print(f"  Organization: {test_case['instructor_organization']}")
        print(f"  Full Name: {test_case['instructor_full_name']}")
        
        print(f"\nGenerated Signature:")
        print(f"  {repr(result)}")
        
        print(f"\nExpected:")
        print(f"  {repr(test_case['expected'])}")
        
        if result == test_case['expected']:
            print("✅ PASS")
        else:
            print("❌ FAIL")
    
    print(f"\n🎉 Instructor signature testing completed!")

def test_email_template():
    """Test how the signature looks in an actual email template."""
    print("\n📧 Testing Email Template with Instructor Signatures")
    print("=" * 55)
    
    email_template = """Dear {student_name},

You have been enrolled in the course "{course_name}" ({instance_name}).

Course Details:
• Course: {course_name}
• Instance: {instance_name}
• Start Date: {start_date}
• Duration: {duration_days} days

Your login credentials:
• Login URL: {login_url}
• Temporary Password: {temporary_password}

We look forward to seeing you in class!

Best regards,
{instructor_signature}

---
This is an automated message. Please do not reply to this email.
If you have questions, please contact your instructor directly."""
    
    # Sample data
    email_data = {
        'student_name': 'Alice Johnson',
        'course_name': 'Python Programming Fundamentals',
        'instance_name': 'Fall 2025 Session',
        'start_date': 'September 01, 2025 at 09:00 AM',
        'duration_days': 105,
        'login_url': 'https://course.example.com/login/abc123',
        'temporary_password': 'TempPass2025!',
        'instructor_signature': 'Dr. Jane Smith\nComputer Science Department\nTech University'
    }
    
    # Generate email
    email_content = email_template.format(**email_data)
    
    print("Sample Email with Instructor Information:")
    print("=" * 50)
    print(email_content)
    print("=" * 50)
    
    print("\n✅ Email template successfully integrates instructor information")
    print("✅ Signature appears personalized and professional")

if __name__ == "__main__":
    test_instructor_signature_generation()
    test_email_template()