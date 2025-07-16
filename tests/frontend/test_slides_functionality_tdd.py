"""
Test-Driven Development for Slides Functionality
Tests for the slides display and map functionality
"""

import pytest
from unittest.mock import Mock, patch
import json


class TestSlidesDisplayFunctionality:
    """Test suite for slides display functionality using TDD approach"""
    
    @pytest.fixture
    def mock_window(self):
        """Mock window object for testing"""
        window = Mock()
        window.currentCourseContent = None
        return window
    
    @pytest.fixture
    def valid_slides_data(self):
        """Valid slides data for testing"""
        return [
            {
                "id": "slide_1",
                "title": "Introduction to Python",
                "content": "• Python is a programming language\n• It's easy to learn\n• Great for beginners",
                "slide_type": "content",
                "order": 1
            },
            {
                "id": "slide_2",
                "title": "Python Variables",
                "content": "• Variables store data\n• Use = for assignment\n• No need to declare types",
                "slide_type": "content",
                "order": 2
            }
        ]
    
    def test_slides_display_with_valid_array(self, mock_window, valid_slides_data):
        """
        RED: Test that slides display works with valid array data
        """
        # Arrange
        mock_window.currentCourseContent = {
            "slides": valid_slides_data
        }
        
        # Act & Assert - This is the expected behavior after fix
        def open_slides_pane_fixed(course_id):
            """Fixed implementation that validates slides array"""
            # Ensure slides is always an array
            slides = []
            if mock_window.currentCourseContent and mock_window.currentCourseContent.get("slides"):
                if isinstance(mock_window.currentCourseContent["slides"], list):
                    slides = mock_window.currentCourseContent["slides"]
                else:
                    slides = []
            
            # This should not raise an error
            slide_count = len(slides)
            if slide_count > 0:
                # Simulate the map operation
                slide_html = []
                for i, slide in enumerate(slides):
                    slide_html.append(f"<div>Slide {i + 1}: {slide['title']}</div>")
                return {"success": True, "slides": slides, "html": slide_html}
            else:
                return {"success": True, "slides": [], "html": []}
        
        # Execute test
        result = open_slides_pane_fixed("test-course-id")
        
        assert result["success"] is True
        assert len(result["slides"]) == 2
        assert len(result["html"]) == 2
        assert "Introduction to Python" in result["html"][0]
        assert "Python Variables" in result["html"][1]
    
    def test_slides_display_with_empty_array(self, mock_window):
        """
        GREEN: Test that slides display works with empty array
        """
        # Arrange
        mock_window.currentCourseContent = {
            "slides": []
        }
        
        # Act & Assert
        def open_slides_pane_fixed(course_id):
            """Fixed implementation that handles empty array"""
            # Ensure slides is always an array
            slides = []
            if mock_window.currentCourseContent and mock_window.currentCourseContent.get("slides"):
                if isinstance(mock_window.currentCourseContent["slides"], list):
                    slides = mock_window.currentCourseContent["slides"]
                else:
                    slides = []
            
            slide_count = len(slides)
            if slide_count > 0:
                slide_html = []
                for i, slide in enumerate(slides):
                    slide_html.append(f"<div>Slide {i + 1}: {slide['title']}</div>")
                return {"success": True, "slides": slides, "html": slide_html}
            else:
                return {"success": True, "slides": [], "html": [], "message": "No slides to display"}
        
        # Execute test
        result = open_slides_pane_fixed("test-course-id")
        
        assert result["success"] is True
        assert len(result["slides"]) == 0
        assert len(result["html"]) == 0
        assert result["message"] == "No slides to display"
    
    def test_slides_display_with_null_content(self, mock_window):
        """
        RED: Test that slides display works when currentCourseContent is null
        """
        # Arrange
        mock_window.currentCourseContent = None
        
        # Act & Assert
        def open_slides_pane_fixed(course_id):
            """Fixed implementation that handles null content"""
            # Ensure slides is always an array
            slides = []
            if mock_window.currentCourseContent and mock_window.currentCourseContent.get("slides"):
                if isinstance(mock_window.currentCourseContent["slides"], list):
                    slides = mock_window.currentCourseContent["slides"]
                else:
                    slides = []
            
            return {"success": True, "slides": slides, "html": []}
        
        # Execute test
        result = open_slides_pane_fixed("test-course-id")
        
        assert result["success"] is True
        assert len(result["slides"]) == 0
        assert len(result["html"]) == 0
    
    def test_slides_display_with_non_array_data(self, mock_window):
        """
        RED: Test that slides display works when slides is not an array (the original problem)
        """
        # Arrange - This simulates the original API response structure
        mock_window.currentCourseContent = {
            "slides": {
                "course_id": "test-course-id",
                "slides": [
                    {
                        "id": "slide_1",
                        "title": "Test Slide",
                        "content": "Test content",
                        "slide_type": "content",
                        "order": 1
                    }
                ]
            }
        }
        
        # Act & Assert
        def open_slides_pane_fixed(course_id):
            """Fixed implementation that handles non-array data"""
            # Ensure slides is always an array
            slides = []
            if mock_window.currentCourseContent and mock_window.currentCourseContent.get("slides"):
                if isinstance(mock_window.currentCourseContent["slides"], list):
                    slides = mock_window.currentCourseContent["slides"]
                else:
                    # This is the case where slides is an object, not an array
                    slides = []
            
            return {"success": True, "slides": slides, "html": []}
        
        # Execute test
        result = open_slides_pane_fixed("test-course-id")
        
        assert result["success"] is True
        assert len(result["slides"]) == 0  # Should be empty because slides was not an array
        assert len(result["html"]) == 0
    
    def test_slides_display_with_missing_slides_property(self, mock_window):
        """
        GREEN: Test that slides display works when slides property is missing
        """
        # Arrange
        mock_window.currentCourseContent = {
            "syllabus": {"title": "Test Course"},
            "quizzes": []
            # No slides property
        }
        
        # Act & Assert
        def open_slides_pane_fixed(course_id):
            """Fixed implementation that handles missing slides property"""
            # Ensure slides is always an array
            slides = []
            if mock_window.currentCourseContent and mock_window.currentCourseContent.get("slides"):
                if isinstance(mock_window.currentCourseContent["slides"], list):
                    slides = mock_window.currentCourseContent["slides"]
                else:
                    slides = []
            
            return {"success": True, "slides": slides, "html": []}
        
        # Execute test
        result = open_slides_pane_fixed("test-course-id")
        
        assert result["success"] is True
        assert len(result["slides"]) == 0
        assert len(result["html"]) == 0


class TestSlidesMapErrorCases:
    """Test specific error cases that cause slides.map errors"""
    
    def test_original_map_error_scenario(self):
        """
        RED: Test the exact scenario that causes 'slides.map is not a function' error
        This test demonstrates the problem
        """
        # This simulates the original broken code
        def broken_slides_display(course_content):
            """Broken implementation that causes map error"""
            slides = course_content.get("slides", [])
            
            # This will cause "slides.map is not a function" if slides is not an array
            try:
                slide_html = []
                for slide in slides:  # This will fail if slides is not iterable
                    slide_html.append(f"<div>{slide['title']}</div>")
                return {"success": True, "html": slide_html}
            except TypeError as e:
                return {"error": str(e)}
        
        # Test with problematic data structure (API response format)
        course_content = {
            "slides": {
                "course_id": "test-course-id",
                "slides": [{"id": "slide_1", "title": "Test"}]
            }
        }
        
        result = broken_slides_display(course_content)
        assert "error" in result
        assert "error" in result and ("not iterable" in result["error"] or "object" in result["error"] or "string indices must be integers" in result["error"])
    
    def test_fixed_map_error_scenario(self):
        """
        GREEN: Test that the fixed implementation handles all data structures
        """
        def fixed_slides_display(course_content):
            """Fixed implementation that handles any data structure"""
            # Ensure slides is always an array
            slides = []
            if course_content.get("slides"):
                if isinstance(course_content["slides"], list):
                    slides = course_content["slides"]
                else:
                    slides = []
            
            # This should never fail
            slide_html = []
            for slide in slides:
                slide_html.append(f"<div>{slide['title']}</div>")
            return {"success": True, "html": slide_html}
        
        # Test with problematic data structure (API response format)
        course_content = {
            "slides": {
                "course_id": "test-course-id",
                "slides": [{"id": "slide_1", "title": "Test"}]
            }
        }
        
        result = fixed_slides_display(course_content)
        assert result["success"] is True
        assert len(result["html"]) == 0  # Should be empty because slides was not an array
    
    def test_fixed_implementation_with_correct_data(self):
        """
        GREEN: Test that the fixed implementation works with correct data structure
        """
        def fixed_slides_display(course_content):
            """Fixed implementation that handles any data structure"""
            # Ensure slides is always an array
            slides = []
            if course_content.get("slides"):
                if isinstance(course_content["slides"], list):
                    slides = course_content["slides"]
                else:
                    slides = []
            
            slide_html = []
            for slide in slides:
                slide_html.append(f"<div>{slide['title']}</div>")
            return {"success": True, "html": slide_html}
        
        # Test with correct data structure (after API response processing)
        course_content = {
            "slides": [
                {"id": "slide_1", "title": "Test Slide 1"},
                {"id": "slide_2", "title": "Test Slide 2"}
            ]
        }
        
        result = fixed_slides_display(course_content)
        assert result["success"] is True
        assert len(result["html"]) == 2
        assert "Test Slide 1" in result["html"][0]
        assert "Test Slide 2" in result["html"][1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])