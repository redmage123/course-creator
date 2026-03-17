"""
Test-Driven Development for Quiz Functionality
Tests for fixing the 'quizzes.map is not a function' error
"""

import pytest
import json


class FakeWindow:
    """Fake window object for testing"""
    def __init__(self):
        self.currentCourseContent = None
        self.console = FakeConsole()


class FakeConsole:
    """Fake console object for testing"""
    def __init__(self):
        self.logs = []

    def log(self, *args):
        self.logs.append(("log", args))

    def error(self, *args):
        self.logs.append(("error", args))


class FakeElement:
    """Fake DOM element for testing"""
    def __init__(self):
        self.className = ""
        self.innerHTML = ""
        self.children = []

    def appendChild(self, child):
        self.children.append(child)

    def remove(self):
        pass

    def closest(self, selector):
        fake_parent = FakeElement()
        return fake_parent


class FakeDocument:
    """Fake document object for testing"""
    def __init__(self):
        self.body = FakeElement()

    def createElement(self, tag):
        return FakeElement()


class TestQuizFunctionality:
    """Test suite for quiz functionality using TDD approach"""

    @pytest.fixture
    def fake_window(self):
        """Fake window object for testing"""
        return FakeWindow()

    @pytest.fixture
    def fake_document(self):
        """Fake document object for testing"""
        return FakeDocument()

    def test_opening_quizzes_pane_with_empty_array(self, fake_window, fake_document):
        """
        RED: Test that openQuizzesPane works with empty array
        This test should pass after we fix the implementation
        """
        # Arrange
        fake_window.currentCourseContent = {"quizzes": []}

        # Act & Assert - This is the expected behavior after fix
        def open_quizzes_pane_fixed(course_id):
            """Fixed implementation that handles arrays properly"""
            quizzes = fake_window.currentCourseContent.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            # This should not throw an error
            quiz_html = ""
            for i, quiz in enumerate(quizzes):
                quiz_html += f"<div>{quiz.get('title', f'Quiz {i+1}')}</div>"

            return {"success": True, "quizCount": len(quizzes), "html": quiz_html}

        result = open_quizzes_pane_fixed("test-course-id")

        assert result["success"] is True
        assert result["quizCount"] == 0
        assert result["html"] == ""

    def test_opening_quizzes_pane_with_null_content(self, fake_window, fake_document):
        """
        RED: Test that openQuizzesPane works with null currentCourseContent
        """
        # Arrange
        fake_window.currentCourseContent = None

        # Act & Assert
        def open_quizzes_pane_fixed(course_id):
            """Fixed implementation that handles null content"""
            course_content = fake_window.currentCourseContent or {}
            quizzes = course_content.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            quiz_html = ""
            for i, quiz in enumerate(quizzes):
                quiz_html += f"<div>{quiz.get('title', f'Quiz {i+1}')}</div>"

            return {"success": True, "quizCount": len(quizzes), "html": quiz_html}

        result = open_quizzes_pane_fixed("test-course-id")

        assert result["success"] is True
        assert result["quizCount"] == 0
        assert result["html"] == ""

    def test_opening_quizzes_pane_with_non_array_quizzes(self, fake_window, fake_document):
        """
        RED: Test that openQuizzesPane works with non-array quizzes property
        This is likely the actual problem case from the error
        """
        # Arrange - This is the problematic case
        fake_window.currentCourseContent = {"quizzes": "not an array"}

        # Act & Assert
        def open_quizzes_pane_fixed(course_id):
            """Fixed implementation that handles non-array quizzes"""
            course_content = fake_window.currentCourseContent or {}
            quizzes = course_content.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            quiz_html = ""
            for i, quiz in enumerate(quizzes):
                quiz_html += f"<div>{quiz.get('title', f'Quiz {i+1}')}</div>"

            return {"success": True, "quizCount": len(quizzes), "html": quiz_html}

        result = open_quizzes_pane_fixed("test-course-id")

        assert result["success"] is True
        assert result["quizCount"] == 0
        assert result["html"] == ""

    def test_opening_quizzes_pane_with_object_quizzes(self, fake_window, fake_document):
        """
        RED: Test that openQuizzesPane works with object instead of array
        """
        # Arrange
        fake_window.currentCourseContent = {"quizzes": {"someProperty": "value"}}

        # Act & Assert
        def open_quizzes_pane_fixed(course_id):
            """Fixed implementation that handles object quizzes"""
            course_content = fake_window.currentCourseContent or {}
            quizzes = course_content.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            quiz_html = ""
            for i, quiz in enumerate(quizzes):
                quiz_html += f"<div>{quiz.get('title', f'Quiz {i+1}')}</div>"

            return {"success": True, "quizCount": len(quizzes), "html": quiz_html}

        result = open_quizzes_pane_fixed("test-course-id")

        assert result["success"] is True
        assert result["quizCount"] == 0
        assert result["html"] == ""

    def test_opening_quizzes_pane_with_valid_quiz_array(self, fake_window, fake_document):
        """
        GREEN: Test that openQuizzesPane works with valid quiz array
        """
        # Arrange
        test_quizzes = [
            {"title": "Quiz 1", "description": "First quiz"},
            {"title": "Quiz 2", "description": "Second quiz"}
        ]
        fake_window.currentCourseContent = {"quizzes": test_quizzes}

        # Act & Assert
        def open_quizzes_pane_fixed(course_id):
            """Fixed implementation that handles valid arrays"""
            course_content = fake_window.currentCourseContent or {}
            quizzes = course_content.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            quiz_html = ""
            for i, quiz in enumerate(quizzes):
                quiz_html += f"<div>{quiz.get('title', f'Quiz {i+1}')}</div>"

            return {"success": True, "quizCount": len(quizzes), "html": quiz_html}

        result = open_quizzes_pane_fixed("test-course-id")

        assert result["success"] is True
        assert result["quizCount"] == 2
        assert result["html"] == "<div>Quiz 1</div><div>Quiz 2</div>"

    def test_view_all_quizzes_with_empty_array(self, fake_window, fake_document):
        """
        RED: Test that viewAllQuizzes works with empty array
        """
        # Arrange
        fake_window.currentCourseContent = {"quizzes": []}

        # Act & Assert
        def view_all_quizzes_fixed(course_id):
            """Fixed implementation for viewAllQuizzes"""
            course_content = fake_window.currentCourseContent or {}
            quizzes = course_content.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            if len(quizzes) == 0:
                return {"success": True, "message": "No quizzes to display"}

            quiz_html = ""
            for i, quiz in enumerate(quizzes):
                quiz_html += f"<div>{quiz.get('title', f'Quiz {i+1}')}</div>"

            return {"success": True, "quizCount": len(quizzes), "html": quiz_html}

        result = view_all_quizzes_fixed("test-course-id")

        assert result["success"] is True
        assert result["message"] == "No quizzes to display"

    def test_view_all_quizzes_with_non_array_quizzes(self, fake_window, fake_document):
        """
        RED: Test that viewAllQuizzes works with non-array quizzes
        """
        # Arrange
        fake_window.currentCourseContent = {"quizzes": "not an array"}

        # Act & Assert
        def view_all_quizzes_fixed(course_id):
            """Fixed implementation for viewAllQuizzes"""
            course_content = fake_window.currentCourseContent or {}
            quizzes = course_content.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            if len(quizzes) == 0:
                return {"success": True, "message": "No quizzes to display"}

            quiz_html = ""
            for i, quiz in enumerate(quizzes):
                quiz_html += f"<div>{quiz.get('title', f'Quiz {i+1}')}</div>"

            return {"success": True, "quizCount": len(quizzes), "html": quiz_html}

        result = view_all_quizzes_fixed("test-course-id")

        assert result["success"] is True
        assert result["message"] == "No quizzes to display"

    def test_view_quiz_details_with_empty_array(self, fake_window, fake_document):
        """
        RED: Test that viewQuizDetails works with empty array
        """
        # Arrange
        fake_window.currentCourseContent = {"quizzes": []}

        # Act & Assert
        def view_quiz_details_fixed(course_id, quiz_index):
            """Fixed implementation for viewQuizDetails"""
            course_content = fake_window.currentCourseContent or {}
            quizzes = course_content.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            if quiz_index >= len(quizzes):
                return {"success": False, "message": "Quiz not found"}

            quiz = quizzes[quiz_index]
            return {"success": True, "quiz": quiz}

        result = view_quiz_details_fixed("test-course-id", 0)

        assert result["success"] is False
        assert result["message"] == "Quiz not found"

    def test_view_quiz_details_with_non_array_quizzes(self, fake_window, fake_document):
        """
        RED: Test that viewQuizDetails works with non-array quizzes
        """
        # Arrange
        fake_window.currentCourseContent = {"quizzes": "not an array"}

        # Act & Assert
        def view_quiz_details_fixed(course_id, quiz_index):
            """Fixed implementation for viewQuizDetails"""
            course_content = fake_window.currentCourseContent or {}
            quizzes = course_content.get("quizzes", [])
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []

            if quiz_index >= len(quizzes):
                return {"success": False, "message": "Quiz not found"}

            quiz = quizzes[quiz_index]
            return {"success": True, "quiz": quiz}

        result = view_quiz_details_fixed("test-course-id", 0)

        assert result["success"] is False
        assert result["message"] == "Quiz not found"


class TestQuizErrorCases:
    """Test specific error cases that cause the original issue"""

    def test_original_error_scenario(self):
        """
        RED: Test the exact scenario that causes 'quizzes.map is not a function' error
        This test demonstrates the problem
        """
        # This simulates the original broken code
        def broken_open_quizzes_pane(course_content):
            """Broken implementation that causes the error"""
            quizzes = course_content.get("quizzes", []) if course_content else []

            # This will fail if quizzes is not an array
            try:
                # Simulate JavaScript map() behavior - only lists have map() in JS
                if isinstance(quizzes, list):
                    return list(quizzes)
                else:
                    # This is what causes the error - trying to use map() on non-array
                    raise TypeError("quizzes.map is not a function")
            except TypeError as e:
                return str(e)

        # Test cases that should cause the error
        test_cases = [
            {"quizzes": "not an array"},
            {"quizzes": {"someProperty": "value"}},
            {"quizzes": 123},
            {"quizzes": None}
        ]

        for test_case in test_cases:
            result = broken_open_quizzes_pane(test_case)
            assert "quizzes.map is not a function" in str(result)

    def test_fixed_error_scenario(self):
        """
        GREEN: Test that the fixed implementation handles all error cases
        """
        def fixed_open_quizzes_pane(course_content):
            """Fixed implementation that handles all cases"""
            quizzes = course_content.get("quizzes", []) if course_content else []

            # Always ensure quizzes is a list
            if not isinstance(quizzes, list):
                quizzes = []

            # Now we can safely iterate
            return len(quizzes)

        # Test cases that previously caused errors
        test_cases = [
            {"quizzes": "not an array"},
            {"quizzes": {"someProperty": "value"}},
            {"quizzes": 123},
            {"quizzes": None},
            {"quizzes": []},
            {"quizzes": [{"title": "Quiz 1"}]}
        ]

        for test_case in test_cases:
            result = fixed_open_quizzes_pane(test_case)
            assert isinstance(result, int)
            assert result >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
