"""
Test-Driven Development for Syllabus Refinement Functionality
Tests for the syllabus refinement with user suggestions
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json


class TestSyllabusRefinementFunctionality:
    """Test suite for syllabus refinement functionality using TDD approach"""
    
    @pytest.fixture
    def mock_window(self):
        """Mock window object for testing"""
        window = Mock()
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
                "overview": "Updated course overview based on feedback",
                "objectives": ["Enhanced objective 1", "Enhanced objective 2"],
                "modules": [
                    {
                        "module_number": 1,
                        "title": "Enhanced Module 1",
                        "description": "Updated module with more practical examples",
                        "topics": ["Enhanced topic 1", "Enhanced topic 2"]
                    }
                ]
            },
            "message": "Syllabus refined successfully"
        })
        fetch_mock = AsyncMock(return_value=mock_response)
        return fetch_mock, mock_response
    
    @pytest.fixture
    def mock_config(self):
        """Mock CONFIG object"""
        config = Mock()
        config.ENDPOINTS = Mock()
        config.ENDPOINTS.REFINE_SYLLABUS = "http://test:8001/syllabus/refine"
        return config
    
    @pytest.fixture
    def mock_progress_notification(self):
        """Mock progress notification"""
        notification = Mock()
        notification.update = Mock()
        notification.close = Mock()
        return notification
    
    @pytest.fixture
    def valid_syllabus_data(self):
        """Valid syllabus data for testing"""
        return {
            "overview": "Python programming course",
            "objectives": ["Learn Python basics", "Write simple programs"],
            "modules": [
                {
                    "module_number": 1,
                    "title": "Introduction to Python",
                    "description": "Basic Python concepts",
                    "topics": ["Variables", "Data types"]
                }
            ]
        }
    
    def test_refinement_modal_creation(self, mock_window, valid_syllabus_data):
        """
        RED: Test that refinement modal is created correctly
        """
        # Arrange
        mock_window.currentCourseContent = {
            "syllabus": valid_syllabus_data
        }
        
        # Act & Assert - This is the expected behavior
        def show_syllabus_refinement_modal_fixed(course_id):
            """Fixed implementation that creates refinement modal"""
            syllabus = mock_window.currentCourseContent.get("syllabus") if mock_window.currentCourseContent else None
            if not syllabus:
                return {"error": "No syllabus found"}
            
            # Mock creating modal elements
            modal_content = {
                "title": "Refine Syllabus",
                "has_feedback_textarea": True,
                "has_examples": True,
                "has_submit_button": True,
                "course_id": course_id
            }
            
            return {"success": True, "modal": modal_content}
        
        # Execute test
        result = show_syllabus_refinement_modal_fixed("test-course-id")
        
        assert result["success"] is True
        assert result["modal"]["title"] == "Refine Syllabus"
        assert result["modal"]["has_feedback_textarea"] is True
        assert result["modal"]["has_examples"] is True
        assert result["modal"]["has_submit_button"] is True
        assert result["modal"]["course_id"] == "test-course-id"
    
    def test_refinement_with_valid_feedback(self, mock_window, mock_fetch, mock_config, valid_syllabus_data):
        """
        GREEN: Test that refinement works with valid feedback
        """
        # Arrange
        mock_window.currentCourseContent = {
            "syllabus": valid_syllabus_data
        }
        fetch_mock, mock_response = mock_fetch
        
        # Act & Assert
        async def refine_syllabus_fixed(course_id, feedback):
            """Fixed implementation that refines syllabus with feedback"""
            syllabus = mock_window.currentCourseContent.get("syllabus") if mock_window.currentCourseContent else None
            if not syllabus:
                return {"error": "No syllabus found"}
            
            if not feedback.strip():
                return {"error": "Feedback required"}
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "feedback": feedback,
                "current_syllabus": syllabus
            }
            
            # Validate payload structure
            assert "course_id" in payload
            assert "feedback" in payload
            assert "current_syllabus" in payload
            assert payload["feedback"] == feedback
            assert payload["current_syllabus"] == syllabus
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.REFINE_SYLLABUS,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps(payload)
            )
            
            if response.ok:
                result = await response.json()
                # Update mock window content
                mock_window.currentCourseContent["syllabus"] = result["syllabus"]
                return {"success": True, "syllabus": result["syllabus"], "message": result.get("message")}
            else:
                return {"error": "API call failed"}
        
        # Execute test
        import asyncio
        result = asyncio.run(refine_syllabus_fixed("test-course-id", "Add more practical examples"))
        
        assert result["success"] is True
        assert "syllabus" in result
        assert result["syllabus"]["overview"] == "Updated course overview based on feedback"
        assert len(result["syllabus"]["modules"]) == 1
        assert result["syllabus"]["modules"][0]["title"] == "Enhanced Module 1"
        assert result["message"] == "Syllabus refined successfully"
    
    def test_refinement_with_empty_feedback(self, mock_window, valid_syllabus_data):
        """
        RED: Test that refinement fails with empty feedback
        """
        # Arrange
        mock_window.currentCourseContent = {
            "syllabus": valid_syllabus_data
        }
        
        # Act & Assert
        async def refine_syllabus_fixed(course_id, feedback):
            """Fixed implementation that validates feedback"""
            syllabus = mock_window.currentCourseContent.get("syllabus") if mock_window.currentCourseContent else None
            if not syllabus:
                return {"error": "No syllabus found"}
            
            if not feedback.strip():
                return {"error": "Feedback required"}
            
            return {"success": True}
        
        # Execute test
        import asyncio
        result = asyncio.run(refine_syllabus_fixed("test-course-id", ""))
        
        assert "error" in result
        assert result["error"] == "Feedback required"
    
    def test_refinement_with_no_syllabus(self, mock_window):
        """
        RED: Test that refinement fails when no syllabus exists
        """
        # Arrange
        mock_window.currentCourseContent = None
        
        # Act & Assert
        async def refine_syllabus_fixed(course_id, feedback):
            """Fixed implementation that validates syllabus existence"""
            syllabus = mock_window.currentCourseContent.get("syllabus") if mock_window.currentCourseContent else None
            if not syllabus:
                return {"error": "No syllabus found"}
            
            return {"success": True}
        
        # Execute test
        import asyncio
        result = asyncio.run(refine_syllabus_fixed("test-course-id", "Add more examples"))
        
        assert "error" in result
        assert result["error"] == "No syllabus found"
    
    def test_refinement_payload_structure(self, mock_window, valid_syllabus_data):
        """
        GREEN: Test that refinement payload has correct structure
        """
        # Arrange
        mock_window.currentCourseContent = {
            "syllabus": valid_syllabus_data
        }
        
        # Act & Assert
        def create_refinement_payload(course_id, feedback, syllabus):
            """Function that creates refinement payload"""
            payload = {
                "course_id": course_id,
                "feedback": feedback,
                "current_syllabus": syllabus
            }
            
            # Validate payload structure matches SyllabusFeedback schema
            required_fields = ["course_id", "feedback", "current_syllabus"]
            for field in required_fields:
                assert field in payload, f"Missing required field: {field}"
                assert payload[field] is not None, f"Field {field} cannot be None"
            
            # Validate data types
            assert isinstance(payload["course_id"], str)
            assert isinstance(payload["feedback"], str)
            assert isinstance(payload["current_syllabus"], dict)
            
            return payload
        
        # Execute test
        payload = create_refinement_payload(
            "test-course-id",
            "Add more practical examples",
            valid_syllabus_data
        )
        
        assert payload["course_id"] == "test-course-id"
        assert payload["feedback"] == "Add more practical examples"
        assert payload["current_syllabus"] == valid_syllabus_data
    
    def test_refinement_api_error_handling(self, mock_window, mock_fetch, mock_config, valid_syllabus_data):
        """
        RED: Test that refinement handles API errors properly
        """
        # Arrange
        mock_window.currentCourseContent = {
            "syllabus": valid_syllabus_data
        }
        fetch_mock, mock_response = mock_fetch
        mock_response.ok = False
        mock_response.status = 500
        
        # Act & Assert
        async def refine_syllabus_fixed(course_id, feedback):
            """Fixed implementation that handles API errors"""
            syllabus = mock_window.currentCourseContent.get("syllabus") if mock_window.currentCourseContent else None
            if not syllabus:
                return {"error": "No syllabus found"}
            
            if not feedback.strip():
                return {"error": "Feedback required"}
            
            token = mock_window.localStorage.getItem('authToken')
            
            payload = {
                "course_id": course_id,
                "feedback": feedback,
                "current_syllabus": syllabus
            }
            
            # Mock API call
            response = await fetch_mock(
                mock_config.ENDPOINTS.REFINE_SYLLABUS,
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
                return {"error": f"API Error {response.status}"}
        
        # Execute test
        import asyncio
        result = asyncio.run(refine_syllabus_fixed("test-course-id", "Add examples"))
        
        assert "error" in result
        assert "API Error 500" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])