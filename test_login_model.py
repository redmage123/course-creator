#!/usr/bin/env python3
"""
Test script to verify the LoginRequest model works correctly
"""
import sys
import json
sys.path.append('/home/bbrelin/course-creator')

from services.user_management.models.auth import LoginRequest
from pydantic import ValidationError

def test_login_model():
    print("Testing LoginRequest model...")
    
    # Test 1: Valid username
    try:
        request = LoginRequest(username="admin_123", password="password123")
        print(f"✅ Username test passed: {request.dict()}")
    except ValidationError as e:
        print(f"❌ Username test failed: {e}")
    
    # Test 2: Valid email (backward compatibility)
    try:
        request = LoginRequest(username="user@example.com", password="password123")
        print(f"✅ Email test passed: {request.dict()}")
    except ValidationError as e:
        print(f"❌ Email test failed: {e}")
    
    # Test 3: Missing field
    try:
        request = LoginRequest(password="password123")
        print(f"❌ Should have failed but didn't: {request.dict()}")
    except ValidationError as e:
        print(f"✅ Missing field validation works: {e}")
    
    # Test 4: JSON parsing
    try:
        json_data = '{"username": "test_user", "password": "test_pass"}'
        data = json.loads(json_data)
        request = LoginRequest(**data)
        print(f"✅ JSON parsing test passed: {request.dict()}")
    except Exception as e:
        print(f"❌ JSON parsing test failed: {e}")

if __name__ == "__main__":
    test_login_model()