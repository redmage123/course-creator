"""
Unit tests for course management service.
Tests course creation, retrieval, and management functionality.
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/course-management'))

# Import the main application
try:
    from main import app, courses_collection, enrollments_collection
    from fastapi.testclient import TestClient
except ImportError:
    pytest.skip("Course management service not available", allow_module_level=True)


class TestCourseManagement:
    """Test suite for course management service."""
    
    def setup_method(self):
        """Set up test client and mock data."""
        self.client = TestClient(app)
        self.test_course = {
            "title": "Test Course",
            "description": "A test course for unit testing",
            "instructor": "Test Instructor",
            "category": "IT",
            "difficulty": "beginner",
            "duration": "4 weeks"
        }
        
        self.test_enrollment = {
            "course_id": "test_course_id",
            "student_email": "student@example.com",
            "student_name": "Test Student"
        }
        
    @patch('main.courses_collection')
    def test_create_course(self, mock_collection):
        """Test creating a new course."""
        mock_collection.insert_one.return_value = Mock(inserted_id="course_id_123")
        
        response = self.client.post("/courses", json=self.test_course)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == self.test_course["title"]
        assert data["id"] == "course_id_123"
        assert data["status"] == "draft"
        
    @patch('main.courses_collection')
    def test_get_all_courses(self, mock_collection):
        """Test retrieving all courses."""
        mock_courses = [
            {
                "_id": "course1",
                "title": "Course 1",
                "description": "Description 1",
                "instructor": "Instructor 1",
                "status": "published"
            },
            {
                "_id": "course2", 
                "title": "Course 2",
                "description": "Description 2",
                "instructor": "Instructor 2",
                "status": "draft"
            }
        ]
        mock_collection.find.return_value = mock_courses
        
        response = self.client.get("/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Course 1"
        assert data[1]["title"] == "Course 2"
        
    @patch('main.courses_collection')
    def test_get_course_by_id(self, mock_collection):
        """Test retrieving a specific course by ID."""
        mock_course = {
            "_id": "course_123",
            "title": "Test Course",
            "description": "Test Description",
            "instructor": "Test Instructor",
            "status": "published"
        }
        mock_collection.find_one.return_value = mock_course
        
        response = self.client.get("/courses/course_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Course"
        assert data["id"] == "course_123"
        
    @patch('main.courses_collection')
    def test_get_nonexistent_course(self, mock_collection):
        """Test retrieving a non-existent course."""
        mock_collection.find_one.return_value = None
        
        response = self.client.get("/courses/nonexistent_id")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
        
    @patch('main.courses_collection')
    def test_update_course(self, mock_collection):
        """Test updating a course."""
        mock_collection.find_one.return_value = {"_id": "course_123", "title": "Old Title"}
        mock_collection.update_one.return_value = Mock(modified_count=1)
        
        update_data = {"title": "Updated Title", "description": "Updated Description"}
        
        response = self.client.put("/courses/course_123", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Course updated successfully"
        
    @patch('main.courses_collection')
    def test_delete_course(self, mock_collection):
        """Test deleting a course."""
        mock_collection.delete_one.return_value = Mock(deleted_count=1)
        
        response = self.client.delete("/courses/course_123")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
    @patch('main.courses_collection')
    def test_delete_nonexistent_course(self, mock_collection):
        """Test deleting a non-existent course."""
        mock_collection.delete_one.return_value = Mock(deleted_count=0)
        
        response = self.client.delete("/courses/nonexistent_id")
        
        assert response.status_code == 404
        
    @patch('main.courses_collection')
    def test_publish_course(self, mock_collection):
        """Test publishing a course."""
        mock_collection.find_one.return_value = {"_id": "course_123", "status": "draft"}
        mock_collection.update_one.return_value = Mock(modified_count=1)
        
        response = self.client.post("/courses/course_123/publish")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Course published successfully"
        
    @patch('main.enrollments_collection')
    def test_enroll_student(self, mock_enrollments):
        """Test enrolling a student in a course."""
        mock_enrollments.find_one.return_value = None  # No existing enrollment
        mock_enrollments.insert_one.return_value = Mock(inserted_id="enrollment_id")
        
        response = self.client.post("/courses/course_123/enroll", json=self.test_enrollment)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Student enrolled successfully"
        
    @patch('main.enrollments_collection')
    def test_enroll_already_enrolled_student(self, mock_enrollments):
        """Test enrolling a student who is already enrolled."""
        mock_enrollments.find_one.return_value = {"course_id": "course_123", "student_email": "student@example.com"}
        
        response = self.client.post("/courses/course_123/enroll", json=self.test_enrollment)
        
        assert response.status_code == 400
        data = response.json()
        assert "already enrolled" in data["detail"]
        
    @patch('main.enrollments_collection')
    def test_get_course_enrollments(self, mock_enrollments):
        """Test getting all enrollments for a course."""
        mock_enrollments_data = [
            {
                "course_id": "course_123",
                "student_email": "student1@example.com",
                "student_name": "Student 1",
                "enrollment_date": datetime.now(),
                "status": "active"
            },
            {
                "course_id": "course_123",
                "student_email": "student2@example.com", 
                "student_name": "Student 2",
                "enrollment_date": datetime.now(),
                "status": "active"
            }
        ]
        mock_enrollments.find.return_value = mock_enrollments_data
        
        response = self.client.get("/courses/course_123/enrollments")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["student_name"] == "Student 1"
        
    @patch('main.enrollments_collection')
    def test_bulk_enroll_students(self, mock_enrollments):
        """Test bulk enrolling students."""
        mock_enrollments.find_one.return_value = None  # No existing enrollments
        mock_enrollments.insert_many.return_value = Mock(inserted_ids=["id1", "id2"])
        
        bulk_data = {
            "course_id": "course_123",
            "students": [
                {"email": "student1@example.com", "name": "Student 1"},
                {"email": "student2@example.com", "name": "Student 2"}
            ]
        }
        
        response = self.client.post("/courses/course_123/bulk-enroll", json=bulk_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["enrolled_count"] == 2
        assert data["failed_count"] == 0
        
    @patch('main.enrollments_collection')
    def test_unenroll_student(self, mock_enrollments):
        """Test unenrolling a student from a course."""
        mock_enrollments.delete_one.return_value = Mock(deleted_count=1)
        
        response = self.client.delete("/courses/course_123/enrollments/student@example.com")
        
        assert response.status_code == 200
        data = response.json()
        assert "unenrolled successfully" in data["message"]
        
    @patch('main.courses_collection')
    def test_get_courses_by_instructor(self, mock_collection):
        """Test getting courses by instructor."""
        mock_courses = [
            {"_id": "course1", "title": "Course 1", "instructor": "Test Instructor"},
            {"_id": "course2", "title": "Course 2", "instructor": "Test Instructor"}
        ]
        mock_collection.find.return_value = mock_courses
        
        response = self.client.get("/courses/instructor/Test Instructor")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(course["instructor"] == "Test Instructor" for course in data)
        
    def test_create_course_validation_errors(self):
        """Test course creation with validation errors."""
        invalid_course = {"title": ""}  # Missing required fields
        
        response = self.client.post("/courses", json=invalid_course)
        
        assert response.status_code == 422  # Validation error
        
    @patch('main.courses_collection')
    def test_get_course_statistics(self, mock_collection):
        """Test getting course statistics."""
        mock_courses = [
            {"status": "published", "category": "IT"},
            {"status": "draft", "category": "IT"},
            {"status": "published", "category": "Business"}
        ]
        mock_collection.find.return_value = mock_courses
        
        with patch('main.enrollments_collection') as mock_enrollments:
            mock_enrollments.count_documents.return_value = 5
            
            response = self.client.get("/courses/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_courses"] == 3
            assert data["published_courses"] == 2
            assert data["draft_courses"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])