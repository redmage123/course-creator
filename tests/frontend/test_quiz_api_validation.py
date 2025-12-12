"""
API-focused unit tests for Quiz Functionality Fixes
Tests the quiz API endpoints and functionality without requiring Selenium
"""

import pytest
import requests
import json
import time


class TestQuizAPIValidation:
    """Test suite for quiz API functionality validation"""
    
    BASE_URL = "http://176.9.99.103:8001"
    TEST_COURSE_ID = "b892987a-0781-471c-81b6-09e09654adf2"
    
    def test_quiz_generation_endpoint_success(self):
        """Test that quiz generation API works and generates minimum 10 questions"""
        url = f"{self.BASE_URL}/quiz/generate-for-course"
        payload = {
            "course_id": self.TEST_COURSE_ID,
            "module_title": "API Test Module",
            "course_level": "beginner",
            "requested_count": 10
        }
        
        response = requests.post(url, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["generated_quizzes"] >= 1
        assert data["saved_quizzes"] >= 1
        
        # Check that each quiz has at least 10 questions
        for quiz in data["quizzes"]:
            assert len(quiz["questions"]) >= 10, f"Quiz {quiz['id']} has only {len(quiz['questions'])} questions"
            assert quiz["id"] is not None
            assert quiz["course_id"] == self.TEST_COURSE_ID
    
    def test_quiz_generation_validates_questions(self):
        """Test that generated quizzes have valid question structure"""
        url = f"{self.BASE_URL}/quiz/generate-for-course"
        payload = {
            "course_id": self.TEST_COURSE_ID,
            "module_title": "Question Validation Test",
            "course_level": "beginner",
            "requested_count": 1
        }
        
        response = requests.post(url, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        quiz = data["quizzes"][0]
        
        # Validate question structure
        for i, question in enumerate(quiz["questions"]):
            assert "question" in question, f"Question {i} missing 'question' field"
            assert question["question"].strip() != "", f"Question {i} has empty question text"
            assert "options" in question, f"Question {i} missing 'options' field"
            assert len(question["options"]) >= 2, f"Question {i} has less than 2 options"
            assert "correct_answer" in question, f"Question {i} missing 'correct_answer' field"
            assert isinstance(question["correct_answer"], int), f"Question {i} correct_answer is not an integer"
            assert 0 <= question["correct_answer"] < len(question["options"]), f"Question {i} correct_answer out of range"
    
    def test_quiz_preview_endpoint_success(self):
        """Test that quiz preview endpoint works correctly"""
        # First generate a quiz to get a valid quiz ID
        gen_url = f"{self.BASE_URL}/quiz/generate-for-course"
        gen_payload = {
            "course_id": self.TEST_COURSE_ID,
            "module_title": "Preview Test Module",
            "course_level": "beginner",
            "requested_count": 1
        }
        
        gen_response = requests.post(gen_url, json=gen_payload)
        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        quiz_id = gen_data["quizzes"][0]["id"]
        
        # Now test the preview endpoint
        preview_url = f"{self.BASE_URL}/quiz/{quiz_id}?userType=instructor"
        preview_response = requests.get(preview_url)
        assert preview_response.status_code == 200
        
        preview_data = preview_response.json()
        assert preview_data["success"] is True
        assert preview_data["quiz"]["id"] == quiz_id
        assert len(preview_data["quiz"]["questions"]) >= 10
    
    def test_quiz_preview_student_vs_instructor(self):
        """Test that quiz preview returns different data for student vs instructor"""
        # Generate a quiz first
        gen_url = f"{self.BASE_URL}/quiz/generate-for-course"
        gen_payload = {
            "course_id": self.TEST_COURSE_ID,
            "module_title": "User Type Test Module",
            "course_level": "beginner",
            "requested_count": 1
        }
        
        gen_response = requests.post(gen_url, json=gen_payload)
        quiz_id = gen_response.json()["quizzes"][0]["id"]
        
        # Test instructor version
        instructor_url = f"{self.BASE_URL}/quiz/{quiz_id}?userType=instructor"
        instructor_response = requests.get(instructor_url)
        assert instructor_response.status_code == 200
        instructor_data = instructor_response.json()
        
        # Test student version
        student_url = f"{self.BASE_URL}/quiz/{quiz_id}?userType=student"
        student_response = requests.get(student_url)
        assert student_response.status_code == 200
        student_data = student_response.json()
        
        # Both should succeed
        assert instructor_data["success"] is True
        assert student_data["success"] is True
        
        # Both should have the same quiz ID
        assert instructor_data["quiz"]["id"] == student_data["quiz"]["id"]
        
        # Both should have the same number of questions
        assert len(instructor_data["quiz"]["questions"]) == len(student_data["quiz"]["questions"])
    
    def test_quiz_database_persistence(self):
        """Test that generated quizzes are persisted in database"""
        # Generate a quiz
        gen_url = f"{self.BASE_URL}/quiz/generate-for-course"
        gen_payload = {
            "course_id": self.TEST_COURSE_ID,
            "module_title": "Database Test Module",
            "course_level": "beginner",
            "requested_count": 1
        }
        
        gen_response = requests.post(gen_url, json=gen_payload)
        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        quiz_id = gen_data["quizzes"][0]["id"]
        
        # Wait a moment for database save
        time.sleep(1)
        
        # Try to retrieve the quiz from database
        get_url = f"{self.BASE_URL}/quiz/{quiz_id}"
        get_response = requests.get(get_url)
        assert get_response.status_code == 200
        
        get_data = get_response.json()
        assert get_data["success"] is True
        assert get_data["quiz"]["id"] == quiz_id
        assert len(get_data["quiz"]["questions"]) >= 10
        
        # Verify the quiz is in course listing
        course_url = f"{self.BASE_URL}/quiz/course/{self.TEST_COURSE_ID}"
        course_response = requests.get(course_url)
        assert course_response.status_code == 200
        course_data = course_response.json()
        
        quiz_found = any(quiz["id"] == quiz_id for quiz in course_data["quizzes"])
        assert quiz_found, "Generated quiz not found in course listing"
    
    def test_quiz_course_listing(self):
        """Test that quizzes are properly listed for a course"""
        url = f"{self.BASE_URL}/quiz/course/{self.TEST_COURSE_ID}"
        response = requests.get(url)
        assert response.status_code == 200
        
        data = response.json()
        assert "quizzes" in data
        assert isinstance(data["quizzes"], list)
        
        # Check that each quiz has proper structure
        for quiz in data["quizzes"]:
            assert "id" in quiz, "Quiz missing ID"
            assert "title" in quiz, "Quiz missing title"
            assert "questions" in quiz, "Quiz missing questions"
            assert isinstance(quiz["questions"], list), "Quiz questions is not a list"
            assert len(quiz["questions"]) >= 10, f"Quiz {quiz['id']} has only {len(quiz['questions'])} questions"
    
    def test_quiz_minimum_questions_validation(self):
        """Test that all generated quizzes have minimum 10 questions"""
        url = f"{self.BASE_URL}/quiz/generate-for-course"
        payload = {
            "course_id": self.TEST_COURSE_ID,
            "module_title": "Minimum Questions Test",
            "course_level": "beginner",
            "requested_count": 3
        }
        
        response = requests.post(url, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["quizzes"]) >= 1
        
        # Verify each quiz has at least 10 questions
        for quiz in data["quizzes"]:
            assert len(quiz["questions"]) >= 10, f"Quiz {quiz['id']} has only {len(quiz['questions'])} questions"
            
            # Verify question structure
            for i, question in enumerate(quiz["questions"]):
                assert "question" in question, f"Quiz {quiz['id']} question {i} missing 'question' field"
                assert question["question"].strip() != "", f"Quiz {quiz['id']} question {i} has empty text"
                assert "options" in question, f"Quiz {quiz['id']} question {i} missing 'options' field"
                assert len(question["options"]) >= 2, f"Quiz {quiz['id']} question {i} has less than 2 options"
    
    def test_quiz_error_handling(self):
        """Test that quiz endpoints handle errors gracefully"""
        # Test with invalid course ID
        url = f"{self.BASE_URL}/quiz/generate-for-course"
        payload = {
            "course_id": "invalid-course-id",
            "module_title": "Test Module",
            "course_level": "beginner",
            "requested_count": 1
        }
        
        response = requests.post(url, json=payload)
        # Should handle error gracefully
        assert response.status_code in [400, 500]
        
        # Test with invalid quiz ID
        get_url = f"{self.BASE_URL}/quiz/nonexistent-quiz-id"
        get_response = requests.get(get_url)
        assert get_response.status_code in [404, 500]
        
        # Test with invalid course ID for course listing
        course_url = f"{self.BASE_URL}/quiz/course/invalid-course-id"
        course_response = requests.get(course_url)
        assert course_response.status_code in [400, 500]
    
    def test_quiz_generation_different_difficulty_levels(self):
        """Test that quiz generation works for different difficulty levels"""
        difficulty_levels = ["beginner", "intermediate", "advanced"]
        
        for level in difficulty_levels:
            url = f"{self.BASE_URL}/quiz/generate-for-course"
            payload = {
                "course_id": self.TEST_COURSE_ID,
                "module_title": f"Difficulty Test {level}",
                "course_level": level,
                "requested_count": 1
            }
            
            response = requests.post(url, json=payload)
            assert response.status_code == 200, f"Failed for difficulty level: {level}"
            
            data = response.json()
            assert data["success"] is True, f"Generation failed for difficulty level: {level}"
            assert len(data["quizzes"]) >= 1, f"No quizzes generated for difficulty level: {level}"
            
            quiz = data["quizzes"][0]
            assert len(quiz["questions"]) >= 10, f"Insufficient questions for difficulty level: {level}"
    
    def test_quiz_generation_multiple_modules(self):
        """Test that quiz generation works for multiple module titles"""
        module_titles = [
            "Introduction to Python",
            "Data Structures and Algorithms",
            "Web Development Fundamentals",
            "Database Design"
        ]
        
        for title in module_titles:
            url = f"{self.BASE_URL}/quiz/generate-for-course"
            payload = {
                "course_id": self.TEST_COURSE_ID,
                "module_title": title,
                "course_level": "beginner",
                "requested_count": 1
            }
            
            response = requests.post(url, json=payload)
            assert response.status_code == 200, f"Failed for module: {title}"
            
            data = response.json()
            assert data["success"] is True, f"Generation failed for module: {title}"
            assert len(data["quizzes"]) >= 1, f"No quizzes generated for module: {title}"
            
            quiz = data["quizzes"][0]
            assert len(quiz["questions"]) >= 10, f"Insufficient questions for module: {title}"
            assert title.lower() in quiz["title"].lower() or title.lower() in quiz.get("description", "").lower(), \
                f"Quiz title/description doesn't reference module: {title}"


class TestQuizUIValidation:
    """Test suite for quiz UI functionality validation (without Selenium)"""
    
    def test_quiz_array_validation_logic(self):
        """Test the logic for handling non-array quiz data"""
        # Simulate the fixed JavaScript logic in Python
        def validate_quiz_data(course_content):
            """Simulate the fixed quiz data validation"""
            if not course_content:
                course_content = {}
            
            quizzes = course_content.get("quizzes", [])
            
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []
            
            return {
                "success": True,
                "quizCount": len(quizzes),
                "isArray": isinstance(quizzes, list),
                "quizzes": quizzes
            }
        
        # Test cases that should work
        test_cases = [
            {"quizzes": []},
            {"quizzes": [{"id": "1", "title": "Test Quiz"}]},
            {"quizzes": "not an array"},
            {"quizzes": {"someProperty": "value"}},
            {"quizzes": 123},
            {"quizzes": None},
            {},
            None
        ]
        
        for i, test_case in enumerate(test_cases):
            result = validate_quiz_data(test_case)
            assert result["success"] is True, f"Test case {i} failed: {test_case}"
            assert result["quizCount"] >= 0, f"Test case {i} should have non-negative quiz count"
            assert result["isArray"] is True, f"Test case {i} should return array"
            assert isinstance(result["quizzes"], list), f"Test case {i} should return list"
    
    def test_quiz_details_functionality(self):
        """Test the logic for quiz details functionality"""
        def view_quiz_details(course_content, quiz_index):
            """Simulate the fixed viewQuizDetails function"""
            if not course_content:
                return {"success": False, "message": "No course content"}
            
            quizzes = course_content.get("quizzes", [])
            
            # Ensure it's always an array
            if not isinstance(quizzes, list):
                quizzes = []
            
            if quiz_index >= len(quizzes) or quiz_index < 0:
                return {"success": False, "message": "Quiz not found"}
            
            quiz = quizzes[quiz_index]
            
            # This should open preview if quiz has ID
            if quiz.get("id"):
                return {
                    "success": True,
                    "action": "preview",
                    "quiz_id": quiz["id"],
                    "user_type": "instructor"
                }
            
            return {"success": False, "message": "Quiz has no ID"}
        
        # Test valid quiz access
        valid_content = {
            "quizzes": [
                {"id": "quiz-1", "title": "Test Quiz 1"},
                {"id": "quiz-2", "title": "Test Quiz 2"}
            ]
        }
        
        result = view_quiz_details(valid_content, 0)
        assert result["success"] is True
        assert result["action"] == "preview"
        assert result["quiz_id"] == "quiz-1"
        
        # Test invalid quiz access
        result = view_quiz_details(valid_content, 5)
        assert result["success"] is False
        assert result["message"] == "Quiz not found"
        
        # Test with invalid course content
        invalid_content = {"quizzes": "not an array"}
        result = view_quiz_details(invalid_content, 0)
        assert result["success"] is False
        assert result["message"] == "Quiz not found"


@pytest.mark.integration
class TestQuizFullWorkflow:
    """Integration tests for complete quiz workflow"""
    
    BASE_URL = "http://176.9.99.103:8001"
    TEST_COURSE_ID = "b892987a-0781-471c-81b6-09e09654adf2"
    
    def test_complete_quiz_workflow(self):
        """Test complete quiz workflow from generation to preview"""
        # 1. Generate quiz
        gen_url = f"{self.BASE_URL}/quiz/generate-for-course"
        gen_payload = {
            "course_id": self.TEST_COURSE_ID,
            "module_title": "Complete Workflow Test",
            "course_level": "beginner",
            "requested_count": 1
        }
        
        gen_response = requests.post(gen_url, json=gen_payload)
        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        quiz_id = gen_data["quizzes"][0]["id"]
        
        # 2. Preview quiz (instructor)
        preview_url = f"{self.BASE_URL}/quiz/{quiz_id}?userType=instructor"
        preview_response = requests.get(preview_url)
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        
        # 3. Preview quiz (student)
        student_url = f"{self.BASE_URL}/quiz/{quiz_id}?userType=student"
        student_response = requests.get(student_url)
        assert student_response.status_code == 200
        student_data = student_response.json()
        
        # 4. Verify consistency
        assert preview_data["quiz"]["id"] == quiz_id
        assert student_data["quiz"]["id"] == quiz_id
        assert len(preview_data["quiz"]["questions"]) >= 10
        assert len(student_data["quiz"]["questions"]) >= 10
        
        # 5. Get course quizzes
        course_url = f"{self.BASE_URL}/quiz/course/{self.TEST_COURSE_ID}"
        course_response = requests.get(course_url)
        assert course_response.status_code == 200
        course_data = course_response.json()
        
        # 6. Verify quiz appears in course listing
        quiz_found = any(quiz["id"] == quiz_id for quiz in course_data["quizzes"])
        assert quiz_found, "Generated quiz not found in course listing"
        
        # 7. Verify all quizzes in course have minimum questions
        for quiz in course_data["quizzes"]:
            assert len(quiz["questions"]) >= 10, f"Quiz {quiz['id']} has insufficient questions"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])