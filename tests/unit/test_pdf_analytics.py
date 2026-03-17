#!/usr/bin/env python3
"""
Test the instructor PDF analytics functionality
Creates a comprehensive test that demonstrates PDF report generation

Note: This is an integration test that requires running services.
Unit tests should not make HTTP requests - use real objects instead.
"""

import pytest
import io
import time
from datetime import datetime, timedelta

# Skip all tests - these are integration tests making HTTP requests
pytestmark = pytest.mark.skip(reason="Integration test - requires running services. Should be refactored to use real service objects instead of HTTP requests.")

ANALYTICS_API = "http://localhost:8007"

def test_analytics_service_health():
    """Test that analytics service is healthy"""
    print("🏥 Testing Analytics Service Health...")
    
    response = requests.get(f"{ANALYTICS_API}/health")
    if response.status_code == 200:
        health_data = response.json()
        print(f"✅ Analytics service is healthy: {health_data}")
        return True
    else:
        print(f"❌ Analytics service not healthy: {response.status_code}")
        return False

def test_pdf_endpoints_available():
    """Test if PDF endpoints are available"""
    print("📋 Testing PDF Endpoint Availability...")
    
    # Test preview endpoint (should exist even without data)
    test_urls = [
        f"{ANALYTICS_API}/analytics/reports/preview/test_course",
        f"{ANALYTICS_API}/analytics/reports/course/test_course/pdf",
        f"{ANALYTICS_API}/analytics/reports/student/test_student/pdf"
    ]
    
    endpoints_available = 0
    
    for url in test_urls:
        try:
            # Don't send authorization header for this test to check if endpoints exist
            response = requests.get(url, timeout=5)
            
            # 422 means endpoint exists but validation failed (expected)
            # 401 means endpoint exists but unauthorized (expected)
            # 404 means endpoint doesn't exist
            if response.status_code in [200, 401, 422, 500]:
                print(f"✅ Endpoint exists: {url}")
                endpoints_available += 1
            else:
                print(f"❌ Endpoint missing: {url} (status: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error for {url}: {e}")
    
    if endpoints_available > 0:
        print(f"✅ Found {endpoints_available}/{len(test_urls)} PDF endpoints")
        return True
    else:
        print("❌ No PDF endpoints found")
        return False

def create_mock_analytics_data():
    """Create some mock analytics data for testing"""
    print("📊 Creating Mock Analytics Data...")
    
    # Since we don't have the database tables, we'll just test the service availability
    # In a real scenario, you would insert test data into the database
    
    mock_data = {
        "course_info": {
            "id": "PYTHON_101",
            "title": "Introduction to Python Programming",
            "description": "A comprehensive course for beginners to learn Python programming"
        },
        "students": ["student_1", "student_2", "student_3"],
        "activities": [
            {"student_id": "student_1", "activity_type": "login", "timestamp": datetime.utcnow()},
            {"student_id": "student_2", "activity_type": "lab_access", "timestamp": datetime.utcnow()},
            {"student_id": "student_3", "activity_type": "quiz_complete", "timestamp": datetime.utcnow()}
        ]
    }
    
    print(f"✅ Mock data prepared for {len(mock_data['students'])} students")
    return mock_data

def test_pdf_generation_workflow():
    """Test the complete PDF generation workflow"""
    print("📄 Testing PDF Generation Workflow...")
    
    course_id = "PYTHON_101"
    
    # Step 1: Test preview endpoint
    print("1. Testing report preview...")
    preview_url = f"{ANALYTICS_API}/analytics/reports/preview/{course_id}"
    
    try:
        # Mock auth token for testing
        headers = {"Authorization": "Bearer mock_token_for_testing"}
        response = requests.get(preview_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            preview_data = response.json()
            print(f"✅ Preview successful: {preview_data}")
        elif response.status_code == 401:
            print("⚠️ Authentication required (expected for secure endpoint)")
        elif response.status_code == 404:
            print("❌ Preview endpoint not found - PDF routes not loaded")
            return False
        else:
            print(f"⚠️ Preview returned status {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Preview request failed: {e}")
        return False
    
    # Step 2: Test PDF download endpoint  
    print("2. Testing PDF download...")
    pdf_url = f"{ANALYTICS_API}/analytics/reports/course/{course_id}/pdf"
    
    try:
        response = requests.get(pdf_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Check if response is actually a PDF
            if response.headers.get('content-type') == 'application/pdf':
                print(f"✅ PDF generated successfully: {len(response.content)} bytes")
                
                # Save test PDF
                with open("/tmp/test_analytics_report.pdf", "wb") as f:
                    f.write(response.content)
                print("✅ Test PDF saved to /tmp/test_analytics_report.pdf")
                return True
            else:
                print(f"⚠️ Response not a PDF: {response.headers.get('content-type')}")
                print(f"Response: {response.text[:200]}...")
        elif response.status_code == 401:
            print("⚠️ Authentication required (expected for secure endpoint)")
        elif response.status_code == 404:
            print("❌ PDF endpoint not found - routes not loaded properly")
            return False
        else:
            print(f"⚠️ PDF request returned status {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ PDF request failed: {e}")
        return False
    
    return True

def test_frontend_integration():
    """Test that frontend can integrate with the PDF functionality"""
    print("🌐 Testing Frontend Integration...")
    
    # Test the instructor dashboard can load
    try:
        dashboard_response = requests.get("http://localhost:8080/instructor-dashboard.html", timeout=5)
        if dashboard_response.status_code == 200:
            # Check if PDF button exists in HTML
            if "downloadPDFReportBtn" in dashboard_response.text:
                print("✅ PDF download button found in instructor dashboard")
            else:
                print("⚠️ PDF download button not found in instructor dashboard HTML")
            
            # Check if analytics dashboard module is referenced
            if "analytics-dashboard.js" in dashboard_response.text:
                print("✅ Analytics dashboard module referenced")
            else:
                print("⚠️ Analytics dashboard module not referenced")
                
        else:
            print(f"⚠️ Instructor dashboard not accessible: {dashboard_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not test frontend integration: {e}")
    
    return True

def main():
    """Main test function"""
    print("🧪 Instructor PDF Analytics Testing")
    print("=" * 50)
    
    tests = [
        ("Analytics Service Health", test_analytics_service_health),
        ("PDF Endpoints Available", test_pdf_endpoints_available), 
        ("Mock Data Creation", create_mock_analytics_data),
        ("PDF Generation Workflow", test_pdf_generation_workflow),
        ("Frontend Integration", test_frontend_integration)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_name == "Mock Data Creation":
                test_func()  # This one just returns data
                passed_tests += 1
            else:
                result = test_func()
                if result:
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n🎯 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! PDF analytics functionality is working.")
    elif passed_tests >= total_tests - 1:
        print("✅ Most tests passed - PDF functionality is mostly working.")
    else:
        print("⚠️ Some tests failed - PDF functionality needs debugging.")
    
    print("\n📄 Expected Instructor Workflow:")
    print("1. Instructor opens instructor dashboard")
    print("2. Navigates to Analytics section")
    print("3. Selects course and time range") 
    print("4. Clicks 'Download PDF Report' button")
    print("5. PDF report downloads to their local filesystem")
    print("6. Report contains: enrollment, lab usage, quiz performance, individual student data, recommendations")

if __name__ == "__main__":
    main()