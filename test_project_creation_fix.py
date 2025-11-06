#!/usr/bin/env python3
"""
Test script to verify the 422 API error fix for project creation.

This script tests that the corrected payload (without extra fields) successfully
creates a project via the API.
"""

import requests
import json
import sys
from datetime import date

# Test configuration
ORG_MANAGEMENT_URL = "http://localhost:8008"
ORG_ID = "259da6df-c148-40c2-bcd9-dc6889e7e9fb"

# Corrected payload matching API schema
project_data = {
    "name": "Test Project - API Fix Verification",
    "slug": "test-project-api-fix-2024",
    "description": "This is a test project to verify the 422 API error fix is working correctly. The description must be at least 10 characters.",
    "target_roles": ["junior_developer", "senior_developer"],
    "duration_weeks": 12,
    "max_participants": 30,
    "start_date": "2024-11-01",
    "end_date": "2025-01-31",
    "selected_track_templates": []
}

print("=" * 80)
print("Testing Project Creation API Fix")
print("=" * 80)
print()

print("📋 Test Configuration:")
print(f"  • API URL: {ORG_MANAGEMENT_URL}")
print(f"  • Organization ID: {ORG_ID}")
print(f"  • Endpoint: POST /api/v1/organizations/{ORG_ID}/projects")
print()

print("📤 Payload to send:")
print(json.dumps(project_data, indent=2))
print()

# Attempt to create project
try:
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer mock-token-org-admin"
    }

    url = f"{ORG_MANAGEMENT_URL}/api/v1/organizations/{ORG_ID}/projects"

    print(f"🌐 Making POST request to: {url}")
    print()

    response = requests.post(
        url,
        headers=headers,
        json=project_data,
        timeout=10
    )

    print(f"📊 Response Status: {response.status_code} {response.reason}")
    print()

    # Try to parse response as JSON
    try:
        response_data = response.json()
        print("📄 Response Body:")
        print(json.dumps(response_data, indent=2))
        print()
    except:
        print("📄 Response Body (raw):")
        print(response.text)
        print()

    # Check result
    if response.status_code == 200 or response.status_code == 201:
        print("✅ SUCCESS: Project created successfully!")
        print()
        print("Test Result: PASSED ✅")
        print("The 422 API error fix is working correctly.")
        sys.exit(0)
    elif response.status_code == 422:
        print("❌ FAILURE: Still getting 422 validation error")
        print()
        print("Validation errors:")
        if isinstance(response_data.get('detail'), list):
            for error in response_data['detail']:
                loc = '.'.join(str(x) for x in error.get('loc', []))
                msg = error.get('msg', 'Unknown error')
                print(f"  • {loc}: {msg}")
        else:
            print(f"  {response_data.get('detail', 'Unknown error')}")
        print()
        print("Test Result: FAILED ❌")
        sys.exit(1)
    else:
        print(f"⚠️  UNEXPECTED: Got status code {response.status_code}")
        print()
        print("Test Result: INCONCLUSIVE ⚠️")
        sys.exit(1)

except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR: Cannot connect to organization-management service")
    print()
    print("Please ensure the service is running:")
    print("  docker-compose ps organization-management")
    print()
    sys.exit(1)

except requests.exceptions.Timeout:
    print("❌ TIMEOUT ERROR: Request took too long")
    print()
    sys.exit(1)

except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
