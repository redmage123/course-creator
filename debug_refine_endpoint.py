#!/usr/bin/env python3
"""
Debug script to check if refine endpoint is being registered properly
"""

import requests
import json

API_BASE = "http://176.9.99.103:8001"

def test_endpoints():
    """Test all available endpoints"""
    
    print("🔍 Checking available endpoints...")
    
    try:
        # Get OpenAPI spec
        response = requests.get(f"{API_BASE}/openapi.json")
        if response.status_code == 200:
            spec = response.json()
            paths = spec.get('paths', {})
            
            print(f"📊 Total endpoints: {len(paths)}")
            print("\n🔗 Available endpoints:")
            for path in sorted(paths.keys()):
                methods = list(paths[path].keys())
                print(f"   {path} - {methods}")
            
            # Check specifically for refine endpoint
            if '/syllabus/refine' in paths:
                print(f"\n✅ /syllabus/refine endpoint found!")
                refine_spec = paths['/syllabus/refine']
                print(f"   Methods: {list(refine_spec.keys())}")
                if 'post' in refine_spec:
                    print(f"   POST method available")
                    print(f"   Summary: {refine_spec['post'].get('summary', 'N/A')}")
                    return True
            else:
                print(f"\n❌ /syllabus/refine endpoint NOT found!")
                return False
        else:
            print(f"❌ Failed to get OpenAPI spec: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking endpoints: {e}")
        return False

def test_direct_call():
    """Test direct call to refine endpoint"""
    
    print("\n🧪 Testing direct call to refine endpoint...")
    
    test_payload = {
        "course_id": "test_123",
        "feedback": "Test feedback",
        "current_syllabus": {"test": "data"}
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/syllabus/refine",
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📥 Response: {response.status_code}")
        print(f"📄 Body: {response.text}")
        
        if response.status_code == 405:
            print("❌ Method Not Allowed - endpoint not registered")
        elif response.status_code == 422:
            print("✅ Endpoint exists but has validation errors")
        elif response.status_code == 200:
            print("✅ Endpoint works correctly")
        else:
            print(f"❓ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error making request: {e}")

if __name__ == "__main__":
    print("🐛 Debug: Refine Endpoint Registration")
    print("=" * 50)
    
    if test_endpoints():
        test_direct_call()
    else:
        print("\n🔍 Endpoint not found in API spec")
        test_direct_call()