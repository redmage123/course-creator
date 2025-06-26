"""
Integration tests for enrollment service
"""

import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_integration(async_client):
    """Test full service integration"""
    
    # Test health check
    response = await async_client.get("/health")
    assert response.status_code == 200
    
    # Test service is responsive
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.integration
async def test_endpoints_integration(async_client):
    """Test all endpoints are accessible"""
    
    endpoints = ["/enroll_student/", "/get_enrollment/", "/list_enrollments/", "/update_enrollment/", "/unenroll_student/", "/get_student_courses/", "/get_course_students/", "/update_lesson_progress/", "/get_course_progress/", "/get_student_progress/", "/mark_lesson_complete/", "/get_certificates/", "/issue_certificate/"]
    
    for endpoint in endpoints:
        response = await async_client.get(endpoint)
        # Should not return 500 (server error)
        assert response.status_code < 500
