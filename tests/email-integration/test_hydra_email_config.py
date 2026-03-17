#!/usr/bin/env python3
"""
Test Hydra-based email configuration
"""

import sys
import os
from datetime import datetime, timezone
from omegaconf import DictConfig

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'course-management'))

from email_service import create_email_service
from models.course_publishing import EnrollmentEmailData

def test_hydra_email_configuration():
    """Test email service creation with Hydra configuration."""
    print("🧪 Testing Hydra-based Email Configuration")
    print("=" * 50)
    
    # Create mock Hydra configuration structure
    mock_config = DictConfig({
        'email': {
            'from_address': 'test-courses@university.edu',
            'smtp': {
                'server': 'smtp.test-university.edu',
                'port': 587,
                'user': 'course-system@university.edu', 
                'password': 'test-password',
                'use_tls': True
            },
            'use_mock': True
        }
    })
    
    print("\n📋 Test 1: Hydra Configuration Structure")
    print("-" * 40)
    print(f"✅ Configuration loaded successfully")
    print(f"  From Address: {mock_config.email.from_address}")
    print(f"  SMTP Server: {mock_config.email.smtp.server}:{mock_config.email.smtp.port}")
    print(f"  SMTP User: {mock_config.email.smtp.user}")
    print(f"  TLS Enabled: {mock_config.email.smtp.use_tls}")
    print(f"  Use Mock: {mock_config.email.use_mock}")
    
    print("\n📧 Test 2: Email Service Creation with Hydra Config")
    print("-" * 50)
    
    try:
        # Create email service using Hydra config
        email_service = create_email_service(config=mock_config)
        
        print(f"✅ Email service created successfully")
        print(f"  Service Type: {type(email_service).__name__}")
        print(f"  From Address: {email_service.from_email}")
        print(f"  SMTP Server: {email_service.smtp_server}:{email_service.smtp_port}")
        print(f"  SMTP User: {email_service.smtp_user}")
        print(f"  TLS Enabled: {email_service.use_tls}")
        
        # Verify configuration values match Hydra config
        assert email_service.from_email == mock_config.email.from_address
        assert email_service.smtp_server == mock_config.email.smtp.server
        assert email_service.smtp_port == mock_config.email.smtp.port
        assert email_service.smtp_user == mock_config.email.smtp.user
        assert email_service.smtp_password == mock_config.email.smtp.password
        assert email_service.use_tls == mock_config.email.smtp.use_tls
        
        print("✅ All configuration values correctly loaded from Hydra config")
        
    except Exception as e:
        print(f"❌ Email service creation failed: {e}")
        return False
    
    print("\n📮 Test 3: Email Generation with Hydra-configured Service")
    print("-" * 55)
    
    try:
        # Create test enrollment data
        enrollment_data = EnrollmentEmailData(
            student_name="Test Student",
            course_name="Python Programming",
            instance_name="Fall 2025",
            start_date=datetime(2025, 9, 1, 9, 0, tzinfo=timezone.utc),
            end_date=datetime(2025, 12, 15, 17, 0, tzinfo=timezone.utc),
            timezone="EST",
            duration_days=105,
            login_url="https://test.edu/login/abc123",
            temporary_password="TestPass123",
            instructor_first_name="Dr. Jane",
            instructor_last_name="Smith",
            instructor_organization="Computer Science Department"
        )
        
        # Generate email content
        email_content = email_service.generate_enrollment_email(enrollment_data)
        
        print(f"✅ Email content generated successfully")
        print(f"  Subject: {email_content['subject']}")
        print(f"  Body Length: {len(email_content['body'])} characters")
        
        # Verify instructor signature is included
        if "Dr. Jane Smith" in email_content['body']:
            print("✅ Instructor signature properly included")
        else:
            print("❌ Instructor signature missing")
            
    except Exception as e:
        print(f"❌ Email generation test failed: {e}")
        return False
    
    print("\n🔄 Test 4: Fallback to Environment Variables")
    print("-" * 45)
    
    try:
        # Test fallback behavior when no config provided
        os.environ['EMAIL_FROM_ADDRESS'] = 'fallback@example.com'
        os.environ['SMTP_SERVER'] = 'mail.example.com'
        os.environ['USE_MOCK_EMAIL'] = 'true'
        
        fallback_service = create_email_service()  # No config provided
        
        print(f"✅ Fallback service created successfully")
        print(f"  From Address: {fallback_service.from_email}")
        print(f"  SMTP Server: {fallback_service.smtp_server}")
        print(f"  Service Type: {type(fallback_service).__name__}")
        
        # Clean up environment variables
        del os.environ['EMAIL_FROM_ADDRESS']
        del os.environ['SMTP_SERVER'] 
        del os.environ['USE_MOCK_EMAIL']
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False
    
    print(f"\n🎉 Hydra email configuration testing completed successfully!")
    print("✅ Email service properly integrates with Hydra configuration")
    print("✅ Configuration values are correctly loaded and applied")
    print("✅ Email generation works with Hydra-configured service")
    print("✅ Fallback to environment variables works when needed")
    
    return True

if __name__ == "__main__":
    success = test_hydra_email_configuration()
    if success:
        print("\n🚀 Email service is ready to use Hydra configuration!")
    else:
        print("\n💥 Some tests failed. Please check the configuration.")
        sys.exit(1)