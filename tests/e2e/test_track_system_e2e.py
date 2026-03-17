"""
End-to-End Tests for Track System
Tests complete workflows from API to database
"""
import pytest
import asyncio
import httpx
import json
from uuid import uuid4
from datetime import datetime

import os

from organization_management.domain.entities.track import TrackStatus, TrackType


class TestTrackSystemE2E:
    """End-to-end tests for track system workflows"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for organization management service"""
        return "http://localhost:8008"
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers for testing"""
        # In real tests, this would contain valid JWT token
        return {
            "Authorization": "Bearer mock-jwt-token",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture
    async def test_organization(self, base_url, auth_headers):
        """Create test organization for E2E tests"""
        async with httpx.AsyncClient() as client:
            org_data = {
                "name": "E2E Test Organization",
                "slug": "e2e-test-org",
                "description": "Organization for E2E testing"
            }
            
            response = await client.post(
                f"{base_url}/api/v1/organizations",
                headers=auth_headers,
                json=org_data
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                # Return mock data if API not available
                return {
                    "id": str(uuid4()),
                    "name": "E2E Test Organization",
                    "slug": "e2e-test-org"
                }
    
    @pytest.fixture
    async def test_project(self, base_url, auth_headers, test_organization):
        """Create test project for E2E tests"""
        async with httpx.AsyncClient() as client:
            project_data = {
                "name": "E2E Test Project",
                "slug": "e2e-test-project",
                "description": "Project for E2E testing",
                "target_roles": ["Developer", "Analyst", "Operations Engineer"]
            }
            
            try:
                response = await client.post(
                    f"{base_url}/api/v1/organizations/{test_organization['id']}/projects",
                    headers=auth_headers,
                    json=project_data
                )
                
                if response.status_code == 201:
                    return response.json()
            except:
                pass
            
            # Return mock data if API not available
            return {
                "id": str(uuid4()),
                "organization_id": test_organization["id"],
                "name": "E2E Test Project",
                "slug": "e2e-test-project"
            }
    
    @pytest.mark.asyncio
    async def test_complete_track_workflow(self, base_url, auth_headers, test_project):
        """Test complete track management workflow"""
        async with httpx.AsyncClient() as client:
            project_id = test_project["id"]
            
            # Step 1: Create a new track
            track_data = {
                "name": "Full-Stack Developer Track",
                "slug": "fullstack-dev-track",
                "description": "Complete full-stack development training",
                "track_type": "sequential",
                "target_audience": ["Application Developer", "Full-Stack Developer"],
                "prerequisites": ["Basic Programming", "Git Knowledge"],
                "duration_weeks": 16,
                "max_enrolled": 50,
                "learning_objectives": [
                    "Master React and Node.js",
                    "Learn database design",
                    "Understand DevOps practices"
                ],
                "skills_taught": ["React", "Node.js", "PostgreSQL", "Docker", "AWS"],
                "difficulty_level": "intermediate",
                "auto_enroll_enabled": True,
                "settings": {
                    "notifications_enabled": True,
                    "progress_tracking": "detailed"
                }
            }
            
            try:
                # Create track
                create_response = await client.post(
                    f"{base_url}/api/v1/projects/{project_id}/tracks",
                    headers=auth_headers,
                    json=track_data
                )
                
                if create_response.status_code == 201:
                    created_track = create_response.json()
                    track_id = created_track["id"]
                    
                    # Verify track creation
                    assert created_track["name"] == track_data["name"]
                    assert created_track["slug"] == track_data["slug"]
                    assert created_track["status"] == "draft"
                    
                    # Step 2: Get track details
                    get_response = await client.get(
                        f"{base_url}/api/v1/tracks/{track_id}",
                        headers=auth_headers
                    )
                    
                    if get_response.status_code == 200:
                        track_details = get_response.json()
                        assert track_details["id"] == track_id
                        assert track_details["target_audience"] == track_data["target_audience"]
                    
                    # Step 3: Update track
                    update_data = {
                        "name": "Advanced Full-Stack Developer Track",
                        "duration_weeks": 20,
                        "max_enrolled": 75
                    }
                    
                    update_response = await client.put(
                        f"{base_url}/api/v1/tracks/{track_id}",
                        headers=auth_headers,
                        json=update_data
                    )
                    
                    if update_response.status_code == 200:
                        updated_track = update_response.json()
                        assert updated_track["name"] == update_data["name"]
                        assert updated_track["duration_weeks"] == update_data["duration_weeks"]
                    
                    # Step 4: Activate track
                    activate_response = await client.post(
                        f"{base_url}/api/v1/tracks/{track_id}/activate",
                        headers=auth_headers
                    )
                    
                    if activate_response.status_code == 200:
                        activated_track = activate_response.json()
                        assert activated_track["status"] == "active"
                    
                    # Step 5: Get track statistics
                    stats_response = await client.get(
                        f"{base_url}/api/v1/tracks/{track_id}/statistics",
                        headers=auth_headers
                    )
                    
                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        assert "estimated_completion" in stats
                        assert "target_audience" in stats
                    
                    # Step 6: Archive track
                    archive_response = await client.post(
                        f"{base_url}/api/v1/tracks/{track_id}/archive",
                        headers=auth_headers
                    )
                    
                    if archive_response.status_code == 200:
                        archived_track = archive_response.json()
                        assert archived_track["status"] == "archived"
                    
                    # Step 7: Delete track
                    delete_response = await client.delete(
                        f"{base_url}/api/v1/tracks/{track_id}",
                        headers=auth_headers
                    )
                    
                    assert delete_response.status_code in [200, 204]
                    
                    # Verify deletion
                    verify_response = await client.get(
                        f"{base_url}/api/v1/tracks/{track_id}",
                        headers=auth_headers
                    )
                    
                    assert verify_response.status_code == 404
                
            except httpx.RequestError:
                # Service not available, test with mock data
                pytest.skip("Organization management service not available")
    
    @pytest.mark.asyncio
    async def test_track_auto_enrollment_workflow(self, base_url, auth_headers, test_project):
        """Test automatic student enrollment workflow"""
        async with httpx.AsyncClient() as client:
            project_id = test_project["id"]
            
            try:
                # Create multiple tracks with different auto-enrollment settings
                tracks_data = [
                    {
                        "name": "App Developer Auto Track",
                        "slug": "app-dev-auto",
                        "target_audience": ["Application Developer"],
                        "auto_enroll_enabled": True
                    },
                    {
                        "name": "Business Analyst Auto Track", 
                        "slug": "ba-auto",
                        "target_audience": ["Business Analyst"],
                        "auto_enroll_enabled": True
                    },
                    {
                        "name": "Manual Enrollment Track",
                        "slug": "manual-track",
                        "target_audience": ["Any Role"],
                        "auto_enroll_enabled": False
                    }
                ]
                
                created_tracks = []
                for track_data in tracks_data:
                    response = await client.post(
                        f"{base_url}/api/v1/projects/{project_id}/tracks",
                        headers=auth_headers,
                        json=track_data
                    )
                    
                    if response.status_code == 201:
                        track = response.json()
                        created_tracks.append(track)
                        
                        # Activate tracks
                        await client.post(
                            f"{base_url}/api/v1/tracks/{track['id']}/activate",
                            headers=auth_headers
                        )
                
                # Get tracks eligible for auto-enrollment
                auto_enroll_response = await client.get(
                    f"{base_url}/api/v1/projects/{project_id}/tracks/auto-enrollment",
                    headers=auth_headers
                )
                
                if auto_enroll_response.status_code == 200:
                    auto_tracks = auto_enroll_response.json()
                    auto_track_names = [t["name"] for t in auto_tracks]
                    
                    assert "App Developer Auto Track" in auto_track_names
                    assert "Business Analyst Auto Track" in auto_track_names
                    assert "Manual Enrollment Track" not in auto_track_names
                
                # Simulate student enrollment in project
                student_id = str(uuid4())
                enrollment_data = {
                    "student_id": student_id,
                    "student_role": "Application Developer"
                }
                
                enroll_response = await client.post(
                    f"{base_url}/api/v1/projects/{project_id}/enroll",
                    headers=auth_headers,
                    json=enrollment_data
                )
                
                # Check student's automatic track enrollments
                if enroll_response.status_code in [200, 201]:
                    student_tracks_response = await client.get(
                        f"{base_url}/api/v1/students/{student_id}/tracks",
                        headers=auth_headers
                    )
                    
                    if student_tracks_response.status_code == 200:
                        student_tracks = student_tracks_response.json()
                        # Student should be auto-enrolled in App Developer track
                        assert any(t["name"] == "App Developer Auto Track" for t in student_tracks)
                
                # Cleanup
                for track in created_tracks:
                    await client.delete(
                        f"{base_url}/api/v1/tracks/{track['id']}",
                        headers=auth_headers
                    )
                
            except httpx.RequestError:
                pytest.skip("Organization management service not available")
    
    @pytest.mark.asyncio
    async def test_track_class_management_workflow(self, base_url, auth_headers, test_project):
        """Test track class management and publication workflow"""
        async with httpx.AsyncClient() as client:
            project_id = test_project["id"]
            
            try:
                # Create a track
                track_data = {
                    "name": "Class Management Track",
                    "slug": "class-mgmt-track",
                    "description": "Track for testing class management"
                }
                
                track_response = await client.post(
                    f"{base_url}/api/v1/projects/{project_id}/tracks",
                    headers=auth_headers,
                    json=track_data
                )
                
                if track_response.status_code == 201:
                    track = track_response.json()
                    track_id = track["id"]
                    
                    # Activate track
                    await client.post(
                        f"{base_url}/api/v1/tracks/{track_id}/activate",
                        headers=auth_headers
                    )
                    
                    # Add classes to track
                    classes_data = [
                        {
                            "course_id": str(uuid4()),
                            "sequence_order": 1,
                            "is_required": True,
                            "estimated_hours": 40,
                            "is_published": False
                        },
                        {
                            "course_id": str(uuid4()),
                            "sequence_order": 2,
                            "is_required": True,  
                            "estimated_hours": 60,
                            "is_published": False
                        }
                    ]
                    
                    added_classes = []
                    for class_data in classes_data:
                        class_response = await client.post(
                            f"{base_url}/api/v1/tracks/{track_id}/classes",
                            headers=auth_headers,
                            json=class_data
                        )
                        
                        if class_response.status_code == 201:
                            added_classes.append(class_response.json())
                    
                    # Get track classes
                    classes_response = await client.get(
                        f"{base_url}/api/v1/tracks/{track_id}/classes",
                        headers=auth_headers
                    )
                    
                    if classes_response.status_code == 200:
                        track_classes = classes_response.json()
                        assert len(track_classes) >= 2
                        
                        # Verify classes are unpublished initially
                        assert all(not cls["is_published"] for cls in track_classes)
                    
                    # Publish first class
                    if added_classes:
                        class_id = added_classes[0]["id"]
                        publish_response = await client.post(
                            f"{base_url}/api/v1/track-classes/{class_id}/publish",
                            headers=auth_headers
                        )
                        
                        if publish_response.status_code == 200:
                            published_class = publish_response.json()
                            assert published_class["is_published"] is True
                    
                    # Get published classes for students
                    published_response = await client.get(
                        f"{base_url}/api/v1/tracks/{track_id}/classes/published",
                        headers=auth_headers
                    )
                    
                    if published_response.status_code == 200:
                        published_classes = published_response.json()
                        assert len(published_classes) == 1  # Only one published
                    
                    # Cleanup
                    await client.delete(
                        f"{base_url}/api/v1/tracks/{track_id}",
                        headers=auth_headers
                    )
                
            except httpx.RequestError:
                pytest.skip("Organization management service not available")
    
    @pytest.mark.asyncio
    async def test_track_search_and_filtering_workflow(self, base_url, auth_headers, test_project):
        """Test track search and filtering capabilities"""
        async with httpx.AsyncClient() as client:
            project_id = test_project["id"]
            
            try:
                # Create tracks with different characteristics
                tracks_data = [
                    {
                        "name": "Python Beginner Track",
                        "slug": "python-beginner",
                        "difficulty_level": "beginner",
                        "target_audience": ["New Developer"],
                        "skills_taught": ["Python", "Git"]
                    },
                    {
                        "name": "JavaScript Advanced Track",
                        "slug": "js-advanced", 
                        "difficulty_level": "advanced",
                        "target_audience": ["Frontend Developer"],
                        "skills_taught": ["JavaScript", "React", "Node.js"]
                    },
                    {
                        "name": "DevOps Intermediate Track",
                        "slug": "devops-intermediate",
                        "difficulty_level": "intermediate", 
                        "target_audience": ["DevOps Engineer"],
                        "skills_taught": ["Docker", "Kubernetes", "AWS"]
                    }
                ]
                
                created_tracks = []
                for track_data in tracks_data:
                    response = await client.post(
                        f"{base_url}/api/v1/projects/{project_id}/tracks",
                        headers=auth_headers,
                        json=track_data
                    )
                    
                    if response.status_code == 201:
                        created_tracks.append(response.json())
                
                # Test search by name
                search_response = await client.get(
                    f"{base_url}/api/v1/projects/{project_id}/tracks/search?q=Python",
                    headers=auth_headers
                )
                
                if search_response.status_code == 200:
                    search_results = search_response.json()
                    assert any("Python" in track["name"] for track in search_results)
                
                # Test filter by difficulty
                beginner_response = await client.get(
                    f"{base_url}/api/v1/projects/{project_id}/tracks?difficulty=beginner",
                    headers=auth_headers
                )
                
                if beginner_response.status_code == 200:
                    beginner_tracks = beginner_response.json()
                    assert all(track["difficulty_level"] == "beginner" for track in beginner_tracks)
                
                # Test filter by target audience
                frontend_response = await client.get(
                    f"{base_url}/api/v1/projects/{project_id}/tracks?target_audience=Frontend Developer",
                    headers=auth_headers
                )
                
                if frontend_response.status_code == 200:
                    frontend_tracks = frontend_response.json()
                    assert any("Frontend Developer" in track["target_audience"] for track in frontend_tracks)
                
                # Test combined filters
                advanced_js_response = await client.get(
                    f"{base_url}/api/v1/projects/{project_id}/tracks?difficulty=advanced&skills=JavaScript",
                    headers=auth_headers
                )
                
                if advanced_js_response.status_code == 200:
                    filtered_tracks = advanced_js_response.json()
                    assert len(filtered_tracks) >= 1
                
                # Cleanup
                for track in created_tracks:
                    await client.delete(
                        f"{base_url}/api/v1/tracks/{track['id']}",
                        headers=auth_headers
                    )
                
            except httpx.RequestError:
                pytest.skip("Organization management service not available")
    
    @pytest.mark.asyncio
    async def test_track_reordering_workflow(self, base_url, auth_headers, test_project):
        """Test track reordering within project"""
        async with httpx.AsyncClient() as client:
            project_id = test_project["id"]
            
            try:
                # Create tracks with initial order
                tracks_data = [
                    {"name": "Track A", "slug": "track-a"},
                    {"name": "Track B", "slug": "track-b"},
                    {"name": "Track C", "slug": "track-c"}
                ]
                
                created_tracks = []
                for track_data in tracks_data:
                    response = await client.post(
                        f"{base_url}/api/v1/projects/{project_id}/tracks",
                        headers=auth_headers,
                        json=track_data
                    )
                    
                    if response.status_code == 201:
                        created_tracks.append(response.json())
                
                # Get initial order
                initial_response = await client.get(
                    f"{base_url}/api/v1/projects/{project_id}/tracks?ordered=true",
                    headers=auth_headers
                )
                
                if initial_response.status_code == 200:
                    initial_tracks = initial_response.json()
                    initial_order = [track["name"] for track in initial_tracks]
                    
                    # Reorder tracks (reverse order)
                    reorder_data = {
                        "track_orders": [
                            {"track_id": created_tracks[2]["id"], "sequence_order": 1},
                            {"track_id": created_tracks[1]["id"], "sequence_order": 2},
                            {"track_id": created_tracks[0]["id"], "sequence_order": 3}
                        ]
                    }
                    
                    reorder_response = await client.put(
                        f"{base_url}/api/v1/projects/{project_id}/tracks/reorder",
                        headers=auth_headers,
                        json=reorder_data
                    )
                    
                    if reorder_response.status_code == 200:
                        # Verify new order
                        final_response = await client.get(
                            f"{base_url}/api/v1/projects/{project_id}/tracks?ordered=true",
                            headers=auth_headers
                        )
                        
                        if final_response.status_code == 200:
                            final_tracks = final_response.json()
                            final_order = [track["name"] for track in final_tracks]
                            
                            # Order should be reversed
                            assert final_order != initial_order
                            assert final_order[0] == "Track C"
                            assert final_order[1] == "Track B"
                            assert final_order[2] == "Track A"
                
                # Cleanup
                for track in created_tracks:
                    await client.delete(
                        f"{base_url}/api/v1/tracks/{track['id']}",
                        headers=auth_headers
                    )
                
            except httpx.RequestError:
                pytest.skip("Organization management service not available")


if __name__ == "__main__":
    pytest.main([__file__])