"""
Unit tests for demo data generator functionality
Tests data generation logic, realistic content creation, and edge cases
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add demo service to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/demo-service'))

from demo_data_generator import (
    generate_demo_courses,
    generate_demo_students, 
    generate_demo_analytics,
    generate_demo_labs,
    generate_demo_feedback,
    COURSE_TOPICS,
    SAMPLE_STUDENTS
)


class TestDemoDataGenerator:
    """Test suite for demo data generation functionality"""

    def test_course_topics_structure(self):
        """Test that course topics are properly structured"""
        assert isinstance(COURSE_TOPICS, dict)
        assert len(COURSE_TOPICS) > 0
        
        # Check each category has topics
        for category, topics in COURSE_TOPICS.items():
            assert isinstance(topics, list)
            assert len(topics) > 0
            assert all(isinstance(topic, str) for topic in topics)

    def test_sample_students_structure(self):
        """Test that sample students are properly structured"""
        assert isinstance(SAMPLE_STUDENTS, list)
        assert len(SAMPLE_STUDENTS) > 0
        
        for student in SAMPLE_STUDENTS:
            assert "name" in student
            assert "performance" in student
            assert "engagement" in student
            assert student["performance"] in ["excellent", "good", "average", "poor"]
            assert student["engagement"] in ["high", "medium", "low"]

    def test_generate_demo_courses_instructor(self):
        """Test course generation for instructor user type"""
        user_data = {
            "name": "Dr. Test Instructor",
            "role": "instructor",
            "organization": "Test University"
        }
        
        courses = generate_demo_courses("instructor", user_data, count=5)
        
        assert len(courses) == 5
        assert all(isinstance(course, dict) for course in courses)
        
        # Check required fields
        required_fields = ["id", "title", "description", "subject", "difficulty", 
                          "duration", "enrollment_count", "completion_rate", "rating"]
        
        for course in courses:
            for field in required_fields:
                assert field in course
                
            # Validate data types and ranges
            assert isinstance(course["enrollment_count"], int)
            assert 15 <= course["enrollment_count"] <= 150  # Instructor range
            assert 65 <= course["completion_rate"] <= 95
            assert 3.8 <= course["rating"] <= 4.9
            assert course["difficulty"] in ["Beginner", "Intermediate", "Advanced"]
            assert course["subject"] in COURSE_TOPICS.keys()

    def test_generate_demo_courses_student(self):
        """Test course generation for student user type"""
        user_data = {
            "name": "Test Student",
            "role": "student",
            "organization": "Test University"
        }
        
        courses = generate_demo_courses("student", user_data, count=3)
        
        assert len(courses) == 3
        
        for course in courses:
            # Student sees different enrollment ranges
            assert 50 <= course["enrollment_count"] <= 500
            assert 70 <= course["completion_rate"] <= 90
            assert 4.0 <= course["rating"] <= 4.8
            
            # Student courses have completion status
            for module in course["modules"]:
                assert "completed" in module
                assert isinstance(module["completed"], (bool, type(None)))

    def test_generate_demo_courses_admin(self):
        """Test course generation for admin user type"""
        user_data = {
            "name": "Test Admin",
            "role": "admin",
            "organization": "Test Corp"
        }
        
        courses = generate_demo_courses("admin", user_data, count=2)
        
        assert len(courses) == 2
        
        for course in courses:
            # Admin sees system-wide ranges
            assert 100 <= course["enrollment_count"] <= 1000
            assert 60 <= course["completion_rate"] <= 85
            assert 3.5 <= course["rating"] <= 4.7

    def test_generate_demo_students(self):
        """Test student data generation"""
        instructor_context = {
            "name": "Dr. Test",
            "role": "instructor"
        }
        
        students = generate_demo_students(course_id="test-course", instructor_context=instructor_context)
        
        assert len(students) >= 8  # Minimum students
        assert len(students) <= 10  # Maximum available sample students
        
        required_fields = ["id", "name", "email", "progress", "engagement_level", 
                          "time_spent", "last_active", "quiz_scores"]
        
        for student in students:
            for field in required_fields:
                assert field in student
                
            # Validate ranges
            assert 10 <= student["progress"] <= 100
            assert student["engagement_level"] in ["high", "medium", "low"]
            assert isinstance(student["quiz_scores"], list)
            assert all(60 <= score <= 100 for score in student["quiz_scores"])

    def test_generate_demo_analytics_instructor(self):
        """Test analytics generation for instructor"""
        user_data = {
            "name": "Dr. Test",
            "role": "instructor"
        }
        
        analytics = generate_demo_analytics("instructor", user_data, "30d")
        
        assert "overview" in analytics
        assert "student_progress" in analytics
        assert "course_performance" in analytics
        assert "engagement_metrics" in analytics
        
        # Validate overview metrics
        overview = analytics["overview"]
        assert isinstance(overview["total_students"], int)
        assert isinstance(overview["completion_rate"], float)
        assert isinstance(overview["average_rating"], float)
        assert 4.1 <= overview["average_rating"] <= 4.8

    def test_generate_demo_analytics_student(self):
        """Test analytics generation for student"""
        user_data = {
            "name": "Test Student",
            "role": "student"
        }
        
        analytics = generate_demo_analytics("student", user_data, "7d")
        
        assert "learning_progress" in analytics
        assert "weekly_activity" in analytics
        assert "skill_development" in analytics
        
        # Validate learning progress
        progress = analytics["learning_progress"]
        assert isinstance(progress["courses_enrolled"], int)
        assert isinstance(progress["total_study_time"], int)
        assert isinstance(progress["current_streak"], int)

    def test_generate_demo_analytics_admin(self):
        """Test analytics generation for admin"""
        user_data = {
            "name": "Test Admin",
            "role": "admin"
        }
        
        analytics = generate_demo_analytics("admin", user_data, "1y")
        
        assert "platform_overview" in analytics
        assert "growth_metrics" in analytics
        assert "content_statistics" in analytics
        
        # Validate platform overview
        overview = analytics["platform_overview"]
        assert isinstance(overview["total_users"], int)
        assert isinstance(overview["platform_revenue"], int)
        assert 99.5 <= overview["system_uptime"] <= 99.9

    def test_generate_demo_labs(self):
        """Test lab environment generation"""
        labs = generate_demo_labs("instructor", course_id="test-course")
        
        assert len(labs) >= 3
        assert len(labs) <= 5
        
        required_fields = ["id", "title", "description", "ide_type", "difficulty",
                          "estimated_time", "completion_rate", "technologies"]
        
        for lab in labs:
            for field in required_fields:
                assert field in lab
                
            # Validate lab data
            assert lab["ide_type"] in ["jupyter", "vscode", "mysql-workbench", "postman"]
            assert lab["difficulty"] in ["Beginner", "Intermediate", "Advanced"]
            assert 30 <= lab["estimated_time"] <= 120
            assert 60 <= lab["completion_rate"] <= 95
            assert isinstance(lab["technologies"], list)
            assert len(lab["technologies"]) >= 2

    def test_generate_demo_feedback(self):
        """Test feedback generation"""
        feedback = generate_demo_feedback(course_id="test-course")
        
        assert len(feedback) >= 8
        assert len(feedback) <= 20
        
        required_fields = ["id", "student_name", "rating", "comment", "date",
                          "course_progress", "sentiment", "topics_mentioned"]
        
        for review in feedback:
            for field in required_fields:
                assert field in review
                
            # Validate feedback data
            assert 2 <= review["rating"] <= 5
            assert review["sentiment"] in ["positive", "constructive"]
            assert 50 <= review["course_progress"] <= 100
            assert isinstance(review["topics_mentioned"], list)
            
        # Check sorting (newest first)
        dates = [datetime.fromisoformat(review["date"]) for review in feedback]
        assert dates == sorted(dates, reverse=True)

    def test_timeframe_variations(self):
        """Test analytics generation with different timeframes"""
        user_data = {"name": "Test User", "role": "instructor"}
        
        timeframes = ["7d", "30d", "90d", "1y"]
        
        for timeframe in timeframes:
            analytics = generate_demo_analytics("instructor", user_data, timeframe)
            assert analytics["timeframe"] == timeframe
            assert "generated_at" in analytics
            
            # Validate student progress has appropriate data points
            progress_data = analytics["student_progress"]
            assert len(progress_data) > 0

    def test_data_consistency(self):
        """Test that generated data is internally consistent"""
        user_data = {"name": "Dr. Consistency", "role": "instructor"}
        
        # Generate multiple datasets
        courses1 = generate_demo_courses("instructor", user_data, count=3)
        courses2 = generate_demo_courses("instructor", user_data, count=3)
        
        # Should generate different data each time
        course_titles1 = {course["title"] for course in courses1}
        course_titles2 = {course["title"] for course in courses2}
        
        # While data is random, structure should be consistent
        for courses in [courses1, courses2]:
            for course in courses:
                assert course["instructor"]["name"] == user_data["name"]
                assert len(course["modules"]) >= 4
                assert course["ai_generated_content"] >= 20

    @patch('demo_data_generator.random.randint')
    def test_deterministic_generation(self, mock_randint):
        """Test that we can control randomness for predictable testing"""
        # Use a repeating mock that returns predictable values
        mock_randint.return_value = 50
        
        user_data = {"name": "Test User", "role": "instructor"}
        courses = generate_demo_courses("instructor", user_data, count=1)
        
        assert len(courses) == 1
        # With controlled randomness, we can test specific values
        assert mock_randint.called
        assert courses[0]["enrollment_count"] == 50  # Uses mocked randint

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        user_data = {"name": "Edge Case User", "role": "instructor"}
        
        # Test minimum count
        courses = generate_demo_courses("instructor", user_data, count=1)
        assert len(courses) == 1
        
        # Test with empty instructor context
        students = generate_demo_students(course_id=None, instructor_context=None)
        assert len(students) > 0
        
        # Test analytics with minimal data
        analytics = generate_demo_analytics("student", {"name": "Test"}, "7d")
        assert "learning_progress" in analytics

    def test_data_types_and_validation(self):
        """Test that all generated data has correct types"""
        user_data = {"name": "Type Test User", "role": "instructor"}
        
        courses = generate_demo_courses("instructor", user_data, count=2)
        
        for course in courses:
            # String fields
            assert isinstance(course["id"], str)
            assert isinstance(course["title"], str)
            assert isinstance(course["description"], str)
            
            # Numeric fields
            assert isinstance(course["enrollment_count"], int)
            assert isinstance(course["completion_rate"], int)
            assert isinstance(course["rating"], float)
            
            # List fields
            assert isinstance(course["modules"], list)
            assert isinstance(course["skills_taught"], list)
            
            # Boolean fields
            assert isinstance(course["has_labs"], bool)
            assert isinstance(course["has_certificates"], bool)
            
            # Date fields should be ISO format
            try:
                datetime.fromisoformat(course["created_at"])
                datetime.fromisoformat(course["last_updated"])
            except ValueError:
                pytest.fail("Date fields should be in ISO format")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])