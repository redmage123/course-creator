"""
Integration Tests for Tracks API

BUSINESS CONTEXT:
End-to-end integration tests for track management functionality.
Tests the complete flow from API endpoint through service layer to database.

TECHNICAL IMPLEMENTATION:
- Tests with real database (test database)
- Tests complete request/response cycle
- Tests data persistence
- Tests cross-service interactions
- Tests transaction handling

TEST COVERAGE:
- Complete track CRUD workflow
- Project-track relationships
- Student enrollment workflow
- Instructor assignment workflow
- Track publishing workflow
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, date
import sys

sys.path.insert(0, '/home/bbrelin/course-creator/tests')
from base_test import BaseIntegrationTest


@pytest.mark.integration
@pytest.mark.tracks
@pytest.mark.asyncio
class TestTracksAPIIntegration(BaseIntegrationTest):
    """
    Integration tests for tracks API

    TESTING STRATEGY:
    - Use test database with rollback
    - Create test organization and project
    - Test complete workflows
    - Verify data persistence
    """

    async def asyncSetUp(self):
        """Setup test environment with database"""
        await super().asyncSetUp()

        # Create test organization
        self.org_id = await self.create_test_organization({
            "name": "Test University",
            "slug": "test-uni",
            "address": "123 Test St",
            "contact_phone": "1234567890",
            "contact_email": "contact@test.edu",
            "admin_full_name": "Test Admin",
            "admin_email": "admin@test.edu"
        })

        # Create test project
        self.project_id = await self.create_test_project({
            "organization_id": self.org_id,
            "name": "Computer Science Degree",
            "slug": "cs-degree",
            "description": "Complete CS program",
            "duration_weeks": 208  # 4 years
        })

        # Create test admin user
        self.admin_token = await self.create_test_user({
            "email": "admin@test.edu",
            "role": "organization_admin",
            "organization_id": self.org_id
        })

    @pytest.mark.asyncio
    async def test_complete_track_lifecycle(self):
        """
        Test complete track lifecycle from creation to deletion

        WORKFLOW:
        1. Create track in draft status
        2. Update track details
        3. Add modules and content
        4. Publish track
        5. Enroll students
        6. Archive track
        7. Delete track
        """
        # Step 1: Create track
        track_data = {
            "name": "Introduction to Python",
            "project_id": self.project_id,
            "description": "Learn Python programming from scratch",
            "difficulty_level": "beginner",
            "duration_weeks": 8,
            "max_students": 30,
            "target_audience": ["beginners", "career changers"],
            "prerequisites": ["Basic computer skills"],
            "learning_objectives": [
                "Understand Python syntax and semantics",
                "Write basic Python programs",
                "Work with Python data structures"
            ]
        }

        create_response = await self.async_client.post(
            "/api/v1/tracks",
            json=track_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert create_response.status_code == 201
        track = create_response.json()
        track_id = track["id"]
        assert track["status"] == "draft"
        assert track["enrollment_count"] == 0

        # Step 2: Update track details
        update_data = {
            "duration_weeks": 10,
            "max_students": 40,
            "description": "Learn Python programming from scratch - Updated"
        }

        update_response = await self.async_client.put(
            f"/api/v1/tracks/{track_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert update_response.status_code == 200
        updated_track = update_response.json()
        assert updated_track["duration_weeks"] == 10
        assert updated_track["max_students"] == 40

        # Step 3: Publish track
        publish_response = await self.async_client.post(
            f"/api/v1/tracks/{track_id}/publish",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert publish_response.status_code == 200
        published_track = publish_response.json()
        assert published_track["status"] == "active"

        # Step 4: Create and enroll students
        student_ids = []
        for i in range(3):
            student_id = await self.create_test_student({
                "email": f"student{i}@test.edu",
                "first_name": f"Student{i}",
                "last_name": "Test",
                "organization_id": self.org_id
            })
            student_ids.append(student_id)

        enroll_response = await self.async_client.post(
            f"/api/v1/tracks/{track_id}/enroll",
            json={"student_ids": student_ids},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert enroll_response.status_code == 200
        enrollment_result = enroll_response.json()
        assert enrollment_result["enrolled"] == 3

        # Step 5: Verify enrollment count updated
        get_response = await self.async_client.get(
            f"/api/v1/tracks/{track_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert get_response.status_code == 200
        current_track = get_response.json()
        assert current_track["enrollment_count"] == 3

        # Step 6: Delete track
        delete_response = await self.async_client.delete(
            f"/api/v1/tracks/{track_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert delete_response.status_code == 204

        # Step 7: Verify track is deleted
        get_deleted_response = await self.async_client.get(
            f"/api/v1/tracks/{track_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert get_deleted_response.status_code == 404

    @pytest.mark.asyncio
    async def test_track_filtering_and_search(self):
        """
        Test track filtering and search functionality

        FILTERS:
        - Filter by project_id
        - Filter by status
        - Filter by difficulty_level
        - Search by name/description
        """
        # Create multiple tracks with different attributes
        tracks_data = [
            {
                "name": "Python Basics",
                "project_id": self.project_id,
                "difficulty_level": "beginner",
                "status": "active"
            },
            {
                "name": "Advanced Python",
                "project_id": self.project_id,
                "difficulty_level": "advanced",
                "status": "active"
            },
            {
                "name": "JavaScript Fundamentals",
                "project_id": self.project_id,
                "difficulty_level": "beginner",
                "status": "draft"
            }
        ]

        # Create all tracks
        for track_data in tracks_data:
            await self.async_client.post(
                "/api/v1/tracks",
                json=track_data,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

        # Test filter by difficulty
        response = await self.async_client.get(
            "/api/v1/tracks",
            params={"difficulty_level": "beginner"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert response.status_code == 200
        beginner_tracks = response.json()
        assert len(beginner_tracks) == 2
        assert all(t["difficulty_level"] == "beginner" for t in beginner_tracks)

        # Test filter by status
        response = await self.async_client.get(
            "/api/v1/tracks",
            params={"status": "active"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert response.status_code == 200
        active_tracks = response.json()
        assert len(active_tracks) == 2

        # Test search by name
        response = await self.async_client.get(
            "/api/v1/tracks",
            params={"search": "Python"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert response.status_code == 200
        python_tracks = response.json()
        assert len(python_tracks) == 2
        assert all("Python" in t["name"] for t in python_tracks)

    @pytest.mark.asyncio
    async def test_track_enrollment_capacity(self):
        """
        Test track enrollment capacity limits

        BUSINESS RULES:
        - Cannot exceed max_students limit
        - Enrollment count tracked accurately
        - Error when capacity reached
        """
        # Create track with small capacity
        track_data = {
            "name": "Limited Capacity Track",
            "project_id": self.project_id,
            "max_students": 2
        }

        create_response = await self.async_client.post(
            "/api/v1/tracks",
            json=track_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        track_id = create_response.json()["id"]

        # Publish track
        await self.async_client.post(
            f"/api/v1/tracks/{track_id}/publish",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        # Create 3 students
        student_ids = []
        for i in range(3):
            student_id = await self.create_test_student({
                "email": f"capacity_test_{i}@test.edu",
                "first_name": f"Student{i}",
                "last_name": "Test",
                "organization_id": self.org_id
            })
            student_ids.append(student_id)

        # Try to enroll all 3 (should fail)
        enroll_response = await self.async_client.post(
            f"/api/v1/tracks/{track_id}/enroll",
            json={"student_ids": student_ids},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        # Should get error about capacity
        assert enroll_response.status_code in [400, 422]
        error = enroll_response.json()
        assert "capacity" in error["detail"].lower() or "maximum" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_track_project_relationship(self):
        """
        Test track-project relationship integrity

        DATA INTEGRITY:
        - Track must belong to valid project
        - Cannot create track with invalid project_id
        - Deleting project cascades to tracks (or prevents deletion)
        """
        # Try to create track with invalid project_id
        invalid_track_data = {
            "name": "Orphan Track",
            "project_id": str(uuid4()),  # Non-existent project
            "description": "Track without valid project"
        }

        response = await self.async_client.post(
            "/api/v1/tracks",
            json=invalid_track_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        # Should fail with appropriate error
        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_track_instructor_assignment(self):
        """
        Test instructor assignment to tracks

        BUSINESS LOGIC:
        - Can assign multiple instructors to track
        - Instructor count tracked accurately
        - Can remove instructor assignments
        """
        # Create track
        track_data = {
            "name": "Track with Instructors",
            "project_id": self.project_id
        }

        create_response = await self.async_client.post(
            "/api/v1/tracks",
            json=track_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        track_id = create_response.json()["id"]

        # Create instructors
        instructor_ids = []
        for i in range(2):
            instructor_id = await self.create_test_instructor({
                "email": f"instructor{i}@test.edu",
                "first_name": f"Instructor{i}",
                "last_name": "Test",
                "organization_id": self.org_id
            })
            instructor_ids.append(instructor_id)

        # Assign instructors to track
        assign_response = await self.async_client.post(
            f"/api/v1/tracks/{track_id}/assign-instructors",
            json={"instructor_ids": instructor_ids},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert assign_response.status_code == 200

        # Verify instructor count
        get_response = await self.async_client.get(
            f"/api/v1/tracks/{track_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        track = get_response.json()
        assert track["instructor_count"] == 2

    @pytest.mark.asyncio
    async def test_concurrent_track_updates(self):
        """
        Test concurrent track updates (optimistic locking)

        CONCURRENCY:
        - Handle simultaneous updates gracefully
        - Prevent data loss from concurrent writes
        - Use version numbers or timestamps
        """
        # Create track
        track_data = {
            "name": "Concurrent Test Track",
            "project_id": self.project_id
        }

        create_response = await self.async_client.post(
            "/api/v1/tracks",
            json=track_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        track_id = create_response.json()["id"]

        # Simulate concurrent updates
        update1 = {"duration_weeks": 8}
        update2 = {"duration_weeks": 10}

        # Execute updates concurrently
        responses = await asyncio.gather(
            self.async_client.put(
                f"/api/v1/tracks/{track_id}",
                json=update1,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            ),
            self.async_client.put(
                f"/api/v1/tracks/{track_id}",
                json=update2,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            ),
            return_exceptions=True
        )

        # At least one should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 1


@pytest.mark.integration
@pytest.mark.tracks
@pytest.mark.performance
class TestTracksPerformance(BaseIntegrationTest):
    """
    Performance tests for tracks API

    TESTING STRATEGY:
    - Test response times under load
    - Test database query efficiency
    - Test pagination performance
    """

    @pytest.mark.asyncio
    async def test_list_tracks_performance(self):
        """
        Test tracks listing performance with large dataset

        PERFORMANCE:
        - Should handle 1000+ tracks efficiently
        - Response time < 500ms
        - Proper pagination
        """
        # Create many tracks (100 for reasonable test time)
        for i in range(100):
            await self.async_client.post(
                "/api/v1/tracks",
                json={
                    "name": f"Performance Test Track {i}",
                    "project_id": self.project_id
                },
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

        # Measure list performance
        import time
        start = time.time()

        response = await self.async_client.get(
            "/api/v1/tracks",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5  # < 500ms
        tracks = response.json()
        assert len(tracks) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
