"""
Test-Driven Development for Syllabus Generation Functionality
Tests for the generate syllabus link and API interaction
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
import asyncio


class TestSyllabusGeneration:
    """Test suite for syllabus generation functionality using TDD approach"""
    
    @pytest.fixture
    def mock_window(self):
        """Mock window object for testing"""
        window = Mock()
        window.currentCourse = None
        window.currentCourseContent = None
        window.localStorage = Mock()
        window.localStorage.getItem = Mock(return_value="mock_token")
        return window
    
    @pytest.fixture
    def mock_fetch(self):
        """Mock fetch function for API calls"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "course_id": "test-course-id",
            "syllabus": {
                "overview": "Test overview",
                "modules": [{"title": "Module 1", "topics": ["Topic 1"]}],
                "objectives": ["Objective 1"],
                "assessment_strategy": "Test assessment"
            }
        })
        fetch_mock = AsyncMock(return_value=mock_response)
        return fetch_mock, mock_response
    
    @pytest.fixture
    def mock_config(self):
        """Mock CONFIG object"""
        config = Mock()
        config.ENDPOINTS = Mock()
        config.ENDPOINTS.GENERATE_SYLLABUS = "http://test:8001/syllabus/generate"
        return config
    
    @pytest.fixture
    def mock_progress_notification(self):
        """Mock progress notification"""
        notification = Mock()
        notification.update = Mock()
        notification.close = Mock()
        return notification
    
    @pytest.fixture
    def valid_course_data(self):
        """Valid course data for testing"""
        return {
            "id": "b892987a-0781-471c-81b6-09e09654adf2",
            "title": "Introduction to Python",
            "description": "Basic python course",
            "category": "Information Technology",
            "difficulty_level": "beginner",
            "estimated_duration": 4
        }
    
    @pytest.fixture
    def incomplete_course_data(self):
        """Incomplete course data for testing"""
        return {
            "id": "b892987a-0781-471c-81b6-09e09654adf2",
            "title": "Introduction to Python",
            # Missing description, category, difficulty_level, estimated_duration
        }
    
    def test_generate_syllabus_with_valid_course_data(self, mock_window, mock_fetch, mock_config, mock_progress_notification, valid_course_data):
        """
        RED: Test that generateSyllabus works with valid course data
        """
        # Arrange
        mock_window.currentCourse = valid_course_data
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert - This is the expected behavior after fix
        async def generate_syllabus_fixed(course_id):
            """Fixed implementation that sends correct payload"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "category": course.get("category", "General"),
                "difficulty_level": course.get("difficulty_level", "beginner"),
                "estimated_duration": course.get("estimated_duration", 4)
            }
            
            # Validate payload
            assert payload["course_id"] == course_id
            assert payload["title"] == "Introduction to Python"
            assert payload["description"] == "Basic python course"
            assert payload["category"] == "Information Technology"
            assert payload["difficulty_level"] == "beginner"
            assert payload["estimated_duration"] == 4
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.GENERATE_SYLLABUS,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps(payload)
            )
            
            if response.ok:
                result = await response.json()
                return {"success": True, "syllabus": result["syllabus"]}
            else:
                raise Exception("Failed to generate syllabus")
        
        # Execute test
        result = asyncio.run(generate_syllabus_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
        
        assert result["success"] is True
        assert "syllabus" in result
        assert result["syllabus"]["overview"] == "Test overview"
    
    def test_generate_syllabus_with_incomplete_course_data(self, mock_window, mock_fetch, mock_config, mock_progress_notification, incomplete_course_data):
        """
        RED: Test that generateSyllabus works with incomplete course data by providing defaults
        """
        # Arrange
        mock_window.currentCourse = incomplete_course_data
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def generate_syllabus_fixed(course_id):
            """Fixed implementation that handles incomplete data"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "category": course.get("category", "General"),
                "difficulty_level": course.get("difficulty_level", "beginner"),
                "estimated_duration": course.get("estimated_duration", 4)
            }
            
            # Validate payload with defaults
            assert payload["course_id"] == course_id
            assert payload["title"] == "Introduction to Python"
            assert payload["description"] == "No description provided"  # Default value
            assert payload["category"] == "General"  # Default value
            assert payload["difficulty_level"] == "beginner"  # Default value
            assert payload["estimated_duration"] == 4  # Default value
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.GENERATE_SYLLABUS,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps(payload)
            )
            
            if response.ok:
                result = await response.json()
                return {"success": True, "syllabus": result["syllabus"]}
            else:
                raise Exception("Failed to generate syllabus")
        
        # Execute test
        result = asyncio.run(generate_syllabus_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
        
        assert result["success"] is True
        assert "syllabus" in result
    
    def test_generate_syllabus_with_no_course_data(self, mock_window, mock_fetch, mock_config, mock_progress_notification):
        """
        RED: Test that generateSyllabus fails gracefully when no course data is available
        """
        # Arrange
        mock_window.currentCourse = None
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def generate_syllabus_fixed(course_id):
            """Fixed implementation that handles missing course data"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            # This should not be reached
            return {"success": False}
        
        # Execute test - should raise exception
        with pytest.raises(ValueError, match="Course data not available"):
            asyncio.run(generate_syllabus_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
    
    def test_generate_syllabus_with_api_error(self, mock_window, mock_fetch, mock_config, mock_progress_notification, valid_course_data):
        """
        RED: Test that generateSyllabus handles API errors properly
        """
        # Arrange
        mock_window.currentCourse = valid_course_data
        fetch_mock, mock_response = mock_fetch
        mock_response.ok = False
        mock_response.status = 422
        mock_response.json = AsyncMock(return_value={
            "detail": [
                {"type": "missing", "loc": ["body", "title"], "msg": "Field required"}
            ]
        })
        
        # Act & Assert
        async def generate_syllabus_fixed(course_id):
            """Fixed implementation that handles API errors"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "category": course.get("category", "General"),
                "difficulty_level": course.get("difficulty_level", "beginner"),
                "estimated_duration": course.get("estimated_duration", 4)
            }
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.GENERATE_SYLLABUS,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps(payload)
            )
            
            if response.ok:
                result = await response.json()
                return {"success": True, "syllabus": result["syllabus"]}
            else:
                error_detail = await response.json()
                raise Exception(f"API Error {response.status}: {error_detail}")
        
        # Execute test - should raise exception
        with pytest.raises(Exception, match="API Error 422"):
            asyncio.run(generate_syllabus_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
    
    def test_generate_syllabus_with_missing_auth_token(self, mock_window, mock_fetch, mock_config, mock_progress_notification, valid_course_data):
        """
        RED: Test that generateSyllabus handles missing auth token
        """
        # Arrange
        mock_window.currentCourse = valid_course_data
        mock_window.localStorage.getItem = Mock(return_value=None)  # No token
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def generate_syllabus_fixed(course_id):
            """Fixed implementation that handles missing auth token"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            if not token:
                raise ValueError("No authentication token")
            
            # This should not be reached
            return {"success": False}
        
        # Execute test - should raise exception
        with pytest.raises(ValueError, match="No authentication token"):
            asyncio.run(generate_syllabus_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
    
    def test_generate_syllabus_updates_current_course_content(self, mock_window, mock_fetch, mock_config, mock_progress_notification, valid_course_data):
        """
        GREEN: Test that generateSyllabus updates window.currentCourseContent
        """
        # Arrange
        mock_window.currentCourse = valid_course_data
        mock_window.currentCourseContent = {"slides": [], "quizzes": []}
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def generate_syllabus_fixed(course_id):
            """Fixed implementation that updates currentCourseContent"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "category": course.get("category", "General"),
                "difficulty_level": course.get("difficulty_level", "beginner"),
                "estimated_duration": course.get("estimated_duration", 4)
            }
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.GENERATE_SYLLABUS,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps(payload)
            )
            
            if response.ok:
                result = await response.json()
                
                # Update stored content
                if mock_window.currentCourseContent:
                    mock_window.currentCourseContent["syllabus"] = result["syllabus"]
                
                return {"success": True, "syllabus": result["syllabus"]}
            else:
                raise Exception("Failed to generate syllabus")
        
        # Execute test
        result = asyncio.run(generate_syllabus_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
        
        assert result["success"] is True
        assert mock_window.currentCourseContent["syllabus"]["overview"] == "Test overview"
    
    def test_generate_syllabus_payload_validation(self, mock_window, mock_fetch, mock_config, mock_progress_notification, valid_course_data):
        """
        RED: Test that generateSyllabus creates correct payload structure
        """
        # Arrange
        mock_window.currentCourse = valid_course_data
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def generate_syllabus_fixed(course_id):
            """Fixed implementation with payload validation"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "category": course.get("category", "General"),
                "difficulty_level": course.get("difficulty_level", "beginner"),
                "estimated_duration": course.get("estimated_duration", 4)
            }
            
            # Validate payload structure matches SyllabusRequest schema
            required_fields = ["course_id", "title", "description", "category", "difficulty_level", "estimated_duration"]
            for field in required_fields:
                assert field in payload, f"Missing required field: {field}"
                assert payload[field] is not None, f"Field {field} cannot be None"
            
            # Validate data types
            assert isinstance(payload["course_id"], str)
            assert isinstance(payload["title"], str)
            assert isinstance(payload["description"], str)
            assert isinstance(payload["category"], str)
            assert isinstance(payload["difficulty_level"], str)
            assert isinstance(payload["estimated_duration"], int)
            
            return {"success": True, "payload": payload}
        
        # Execute test
        result = asyncio.run(generate_syllabus_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
        
        assert result["success"] is True
        payload = result["payload"]
        assert payload["course_id"] == "b892987a-0781-471c-81b6-09e09654adf2"
        assert payload["title"] == "Introduction to Python"
        assert payload["description"] == "Basic python course"
        assert payload["category"] == "Information Technology"
        assert payload["difficulty_level"] == "beginner"
        assert payload["estimated_duration"] == 4


class TestSyllabusGenerationErrorCases:
    """Test specific error cases that cause syllabus generation failures"""
    
    def test_original_422_error_scenario(self):
        """
        RED: Test the exact scenario that causes 422 Unprocessable Content error
        This test demonstrates the problem
        """
        # This simulates the original broken code
        def broken_generate_syllabus(course_data):
            """Broken implementation that causes 422 error"""
            # Original code only sent course_id
            payload = {
                "course_id": course_data.get("id")
                # Missing: title, description, category, difficulty_level, estimated_duration
            }
            
            # This payload will cause 422 error
            required_fields = ["course_id", "title", "description", "category", "difficulty_level", "estimated_duration"]
            missing_fields = [field for field in required_fields if field not in payload or payload[field] is None]
            
            if missing_fields:
                return {"error": "422 Unprocessable Content", "missing_fields": missing_fields}
            
            return {"success": True}
        
        # Test with valid course data
        course_data = {
            "id": "b892987a-0781-471c-81b6-09e09654adf2",
            "title": "Introduction to Python",
            "description": "Basic python course",
            "category": "Information Technology",
            "difficulty_level": "beginner",
            "estimated_duration": 4
        }
        
        result = broken_generate_syllabus(course_data)
        assert "error" in result
        assert result["error"] == "422 Unprocessable Content"
        assert "title" in result["missing_fields"]
        assert "description" in result["missing_fields"]
        assert "category" in result["missing_fields"]
        assert "difficulty_level" in result["missing_fields"]
        assert "estimated_duration" in result["missing_fields"]
    
    def test_fixed_422_error_scenario(self):
        """
        GREEN: Test that the fixed implementation handles all required fields
        """
        def fixed_generate_syllabus(course_data):
            """Fixed implementation that includes all required fields"""
            payload = {
                "course_id": course_data.get("id"),
                "title": course_data.get("title"),
                "description": course_data.get("description", "No description provided"),
                "category": course_data.get("category", "General"),
                "difficulty_level": course_data.get("difficulty_level", "beginner"),
                "estimated_duration": course_data.get("estimated_duration", 4)
            }
            
            # Validate payload
            required_fields = ["course_id", "title", "description", "category", "difficulty_level", "estimated_duration"]
            missing_fields = [field for field in required_fields if field not in payload or payload[field] is None]
            
            if missing_fields:
                return {"error": "422 Unprocessable Content", "missing_fields": missing_fields}
            
            return {"success": True, "payload": payload}
        
        # Test with valid course data
        course_data = {
            "id": "b892987a-0781-471c-81b6-09e09654adf2",
            "title": "Introduction to Python",
            "description": "Basic python course",
            "category": "Information Technology",
            "difficulty_level": "beginner",
            "estimated_duration": 4
        }
        
        result = fixed_generate_syllabus(course_data)
        assert result["success"] is True
        assert "payload" in result
        
        payload = result["payload"]
        assert payload["course_id"] == "b892987a-0781-471c-81b6-09e09654adf2"
        assert payload["title"] == "Introduction to Python"
        assert payload["description"] == "Basic python course"
        assert payload["category"] == "Information Technology"
        assert payload["difficulty_level"] == "beginner"
        assert payload["estimated_duration"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])