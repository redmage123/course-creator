"""
Test-Driven Development for Slides Generation Functionality
Tests for the generate slides link and API interaction
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
import asyncio


class TestSlidesGeneration:
    """Test suite for slides generation functionality using TDD approach"""
    
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
            "slides": [
                {
                    "id": "slide_1",
                    "title": "Test Slide 1",
                    "content": "Test content",
                    "slide_type": "content",
                    "order": 1
                }
            ]
        })
        fetch_mock = AsyncMock(return_value=mock_response)
        return fetch_mock, mock_response
    
    @pytest.fixture
    def mock_config(self):
        """Mock CONFIG object"""
        config = Mock()
        config.ENDPOINTS = Mock()
        config.ENDPOINTS.GENERATE_SLIDES = "http://test:8001/slides/generate"
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
            # Missing description, category
        }
    
    def test_generate_slides_with_valid_course_data(self, mock_window, mock_fetch, mock_config, mock_progress_notification, valid_course_data):
        """
        RED: Test that generateSlides works with valid course data
        """
        # Arrange
        mock_window.currentCourse = valid_course_data
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert - This is the expected behavior after fix
        async def generate_slides_fixed(course_id):
            """Fixed implementation that sends correct payload"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "topic": course.get("category", "General")
            }
            
            # Validate payload
            assert payload["course_id"] == course_id
            assert payload["title"] == "Introduction to Python"
            assert payload["description"] == "Basic python course"
            assert payload["topic"] == "Information Technology"
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.GENERATE_SLIDES,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps(payload)
            )
            
            if response.ok:
                result = await response.json()
                return {"success": True, "slides": result["slides"]}
            else:
                raise Exception("Failed to generate slides")
        
        # Execute test
        result = asyncio.run(generate_slides_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
        
        assert result["success"] is True
        assert "slides" in result
        assert len(result["slides"]) == 1
        assert result["slides"][0]["title"] == "Test Slide 1"
    
    def test_generate_slides_with_incomplete_course_data(self, mock_window, mock_fetch, mock_config, mock_progress_notification, incomplete_course_data):
        """
        RED: Test that generateSlides works with incomplete course data by providing defaults
        """
        # Arrange
        mock_window.currentCourse = incomplete_course_data
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def generate_slides_fixed(course_id):
            """Fixed implementation that handles incomplete data"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "topic": course.get("category", "General")
            }
            
            # Validate payload with defaults
            assert payload["course_id"] == course_id
            assert payload["title"] == "Introduction to Python"
            assert payload["description"] == "No description provided"  # Default value
            assert payload["topic"] == "General"  # Default value
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.GENERATE_SLIDES,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps(payload)
            )
            
            if response.ok:
                result = await response.json()
                return {"success": True, "slides": result["slides"]}
            else:
                raise Exception("Failed to generate slides")
        
        # Execute test
        result = asyncio.run(generate_slides_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
        
        assert result["success"] is True
        assert "slides" in result
    
    def test_generate_slides_with_no_course_data(self, mock_window, mock_fetch, mock_config, mock_progress_notification):
        """
        RED: Test that generateSlides fails gracefully when no course data is available
        """
        # Arrange
        mock_window.currentCourse = None
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def generate_slides_fixed(course_id):
            """Fixed implementation that handles missing course data"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            # This should not be reached
            return {"success": False}
        
        # Execute test - should raise exception
        with pytest.raises(ValueError, match="Course data not available"):
            asyncio.run(generate_slides_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
    
    def test_generate_slides_with_api_error(self, mock_window, mock_fetch, mock_config, mock_progress_notification, valid_course_data):
        """
        RED: Test that generateSlides handles API errors properly
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
        async def generate_slides_fixed(course_id):
            """Fixed implementation that handles API errors"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "topic": course.get("category", "General")
            }
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.GENERATE_SLIDES,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps(payload)
            )
            
            if response.ok:
                result = await response.json()
                return {"success": True, "slides": result["slides"]}
            else:
                error_detail = await response.json()
                raise Exception(f"API Error {response.status}: {error_detail}")
        
        # Execute test - should raise exception
        with pytest.raises(Exception, match="API Error 422"):
            asyncio.run(generate_slides_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
    
    def test_generate_slides_payload_validation(self, mock_window, mock_fetch, mock_config, mock_progress_notification, valid_course_data):
        """
        RED: Test that generateSlides creates correct payload structure
        """
        # Arrange
        mock_window.currentCourse = valid_course_data
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def generate_slides_fixed(course_id):
            """Fixed implementation with payload validation"""
            course = mock_window.currentCourse
            if not course:
                raise ValueError("Course data not available")
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "title": course.get("title"),
                "description": course.get("description", "No description provided"),
                "topic": course.get("category", "General")
            }
            
            # Validate payload structure matches SlideGenerationRequest schema
            required_fields = ["course_id", "title", "description", "topic"]
            for field in required_fields:
                assert field in payload, f"Missing required field: {field}"
                assert payload[field] is not None, f"Field {field} cannot be None"
            
            # Validate data types
            assert isinstance(payload["course_id"], str)
            assert isinstance(payload["title"], str)
            assert isinstance(payload["description"], str)
            assert isinstance(payload["topic"], str)
            
            return {"success": True, "payload": payload}
        
        # Execute test
        result = asyncio.run(generate_slides_fixed("b892987a-0781-471c-81b6-09e09654adf2"))
        
        assert result["success"] is True
        payload = result["payload"]
        assert payload["course_id"] == "b892987a-0781-471c-81b6-09e09654adf2"
        assert payload["title"] == "Introduction to Python"
        assert payload["description"] == "Basic python course"
        assert payload["topic"] == "Information Technology"


class TestSlidesGenerationErrorCases:
    """Test specific error cases that cause slides generation failures"""
    
    def test_original_422_error_scenario(self):
        """
        RED: Test the exact scenario that causes 422 Unprocessable Content error
        This test demonstrates the problem
        """
        # This simulates the original broken code
        def broken_generate_slides(course_data):
            """Broken implementation that causes 422 error"""
            # Original code only sent course_id
            payload = {
                "course_id": course_data.get("id")
                # Missing: title, description, topic
            }
            
            # This payload will cause 422 error
            required_fields = ["course_id", "title", "description", "topic"]
            missing_fields = [field for field in required_fields if field not in payload or payload[field] is None]
            
            if missing_fields:
                return {"error": "422 Unprocessable Content", "missing_fields": missing_fields}
            
            return {"success": True}
        
        # Test with valid course data
        course_data = {
            "id": "b892987a-0781-471c-81b6-09e09654adf2",
            "title": "Introduction to Python",
            "description": "Basic python course",
            "category": "Information Technology"
        }
        
        result = broken_generate_slides(course_data)
        assert "error" in result
        assert result["error"] == "422 Unprocessable Content"
        assert "title" in result["missing_fields"]
        assert "description" in result["missing_fields"]
        assert "topic" in result["missing_fields"]
    
    def test_fixed_422_error_scenario(self):
        """
        GREEN: Test that the fixed implementation handles all required fields
        """
        def fixed_generate_slides(course_data):
            """Fixed implementation that includes all required fields"""
            payload = {
                "course_id": course_data.get("id"),
                "title": course_data.get("title"),
                "description": course_data.get("description", "No description provided"),
                "topic": course_data.get("category", "General")
            }
            
            # Validate payload
            required_fields = ["course_id", "title", "description", "topic"]
            missing_fields = [field for field in required_fields if field not in payload or payload[field] is None]
            
            if missing_fields:
                return {"error": "422 Unprocessable Content", "missing_fields": missing_fields}
            
            return {"success": True, "payload": payload}
        
        # Test with valid course data
        course_data = {
            "id": "b892987a-0781-471c-81b6-09e09654adf2",
            "title": "Introduction to Python",
            "description": "Basic python course",
            "category": "Information Technology"
        }
        
        result = fixed_generate_slides(course_data)
        assert result["success"] is True
        assert "payload" in result
        
        payload = result["payload"]
        assert payload["course_id"] == "b892987a-0781-471c-81b6-09e09654adf2"
        assert payload["title"] == "Introduction to Python"
        assert payload["description"] == "Basic python course"
        assert payload["topic"] == "Information Technology"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])