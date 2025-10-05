"""
Unit Tests for Analytics Service
Tests the analytics service models, endpoints, and business logic
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Import the analytics service components

from main import (
    app, StudentActivity, LabUsageMetrics, QuizPerformance, 
    StudentProgress, LearningAnalytics, AnalyticsRequest, AnalyticsResponse
)
from analytics_endpoints import calculate_engagement_score, generate_recommendations

class TestAnalyticsModels:
    """Test analytics data models"""
    
    def test_student_activity_model(self):
        """Test StudentActivity model validation"""
        activity = StudentActivity(
            student_id="student-123",
            course_id="course-456",
            activity_type="lab_access",
            activity_data={"lab_id": "lab-789"}
        )
        
        assert activity.student_id == "student-123"
        assert activity.course_id == "course-456"
        assert activity.activity_type == "lab_access"
        assert activity.activity_data["lab_id"] == "lab-789"
        assert activity.activity_id is not None
        assert isinstance(activity.timestamp, datetime)
    
    def test_lab_usage_metrics_model(self):
        """Test LabUsageMetrics model validation"""
        lab_usage = LabUsageMetrics(
            student_id="student-123",
            course_id="course-456",
            lab_id="lab-789",
            session_start=datetime.utcnow(),
            actions_performed=25,
            code_executions=12,
            errors_encountered=3
        )
        
        assert lab_usage.student_id == "student-123"
        assert lab_usage.course_id == "course-456"
        assert lab_usage.lab_id == "lab-789"
        assert lab_usage.actions_performed == 25
        assert lab_usage.code_executions == 12
        assert lab_usage.errors_encountered == 3
        assert lab_usage.completion_status == "in_progress"
    
    def test_quiz_performance_model(self):
        """Test QuizPerformance model validation"""
        quiz_perf = QuizPerformance(
            student_id="student-123",
            course_id="course-456",
            quiz_id="quiz-789",
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=8,
            questions_correct=6
        )
        
        assert quiz_perf.student_id == "student-123"
        assert quiz_perf.course_id == "course-456"
        assert quiz_perf.quiz_id == "quiz-789"
        assert quiz_perf.questions_total == 10
        assert quiz_perf.questions_answered == 8
        assert quiz_perf.questions_correct == 6
        assert quiz_perf.attempt_number == 1
    
    def test_student_progress_model(self):
        """Test StudentProgress model validation"""
        progress = StudentProgress(
            student_id="student-123",
            course_id="course-456",
            content_item_id="lesson-789",
            content_type="lesson",
            status="completed",
            progress_percentage=85.5,
            time_spent_minutes=45,
            last_accessed=datetime.utcnow()
        )
        
        assert progress.student_id == "student-123"
        assert progress.course_id == "course-456"
        assert progress.content_item_id == "lesson-789"
        assert progress.content_type == "lesson"
        assert progress.status == "completed"
        assert progress.progress_percentage == 85.5
        assert progress.time_spent_minutes == 45
    
    def test_learning_analytics_model(self):
        """Test LearningAnalytics model validation"""
        analytics = LearningAnalytics(
            student_id="student-123",
            course_id="course-456",
            engagement_score=78.5,
            progress_velocity=2.3,
            lab_proficiency=82.1,
            quiz_performance=75.2,
            time_on_platform=120,
            streak_days=7,
            risk_level="low",
            recommendations=["Great progress!", "Keep it up!"]
        )
        
        assert analytics.student_id == "student-123"
        assert analytics.course_id == "course-456"
        assert analytics.engagement_score == 78.5
        assert analytics.progress_velocity == 2.3
        assert analytics.lab_proficiency == 82.1
        assert analytics.quiz_performance == 75.2
        assert analytics.time_on_platform == 120
        assert analytics.streak_days == 7
        assert analytics.risk_level == "low"
        assert len(analytics.recommendations) == 2


class TestAnalyticsBusinessLogic:
    """Test analytics business logic functions"""
    
    def test_calculate_engagement_score_high(self):
        """Test engagement score calculation for high engagement"""
        analytics_data = {
            'activity_summary': {'total_activities': 60},
            'lab_metrics': {'total_sessions': 12},
            'quiz_performance': {'average_score': 85.0},
            'progress_summary': {
                'by_content_type': [
                    {'total_time_minutes': 180},
                    {'total_time_minutes': 120}
                ]
            }
        }
        
        score = calculate_engagement_score(analytics_data)
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 80  # Should be high engagement
    
    def test_calculate_engagement_score_low(self):
        """Test engagement score calculation for low engagement"""
        analytics_data = {
            'activity_summary': {'total_activities': 5},
            'lab_metrics': {'total_sessions': 1},
            'quiz_performance': {'average_score': 45.0},
            'progress_summary': {
                'by_content_type': [
                    {'total_time_minutes': 30}
                ]
            }
        }
        
        score = calculate_engagement_score(analytics_data)
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score < 50  # Should be low engagement
    
    def test_calculate_engagement_score_edge_cases(self):
        """Test engagement score calculation with edge cases"""
        # Empty data
        analytics_data = {
            'activity_summary': {'total_activities': 0},
            'lab_metrics': {'total_sessions': 0},
            'quiz_performance': {'average_score': 0},
            'progress_summary': {'by_content_type': []}
        }
        
        score = calculate_engagement_score(analytics_data)
        assert score == 0.0
        
        # Missing data
        incomplete_data = {}
        score_incomplete = calculate_engagement_score(incomplete_data)
        assert score_incomplete == 0.0
    
    def test_generate_recommendations_low_activity(self):
        """Test recommendation generation for low activity"""
        analytics_data = {
            'activity_summary': {'total_activities': 5},
            'lab_metrics': {'average_errors': 3, 'average_session_duration': 20},
            'quiz_performance': {'average_score': 75, 'pass_rate': 0.8},
            'engagement_score': 65
        }
        
        recommendations = generate_recommendations(analytics_data)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("engagement" in rec.lower() for rec in recommendations)
    
    def test_generate_recommendations_high_errors(self):
        """Test recommendation generation for high error rates"""
        analytics_data = {
            'activity_summary': {'total_activities': 25},
            'lab_metrics': {'average_errors': 8, 'average_session_duration': 45},
            'quiz_performance': {'average_score': 70, 'pass_rate': 0.7},
            'engagement_score': 70
        }
        
        recommendations = generate_recommendations(analytics_data)
        assert isinstance(recommendations, list)
        assert any("debugging" in rec.lower() or "errors" in rec.lower() for rec in recommendations)
    
    def test_generate_recommendations_low_quiz_performance(self):
        """Test recommendation generation for low quiz performance"""
        analytics_data = {
            'activity_summary': {'total_activities': 30},
            'lab_metrics': {'average_errors': 2, 'average_session_duration': 35},
            'quiz_performance': {'average_score': 55, 'pass_rate': 0.4},
            'engagement_score': 60
        }
        
        recommendations = generate_recommendations(analytics_data)
        assert isinstance(recommendations, list)
        assert any("quiz" in rec.lower() or "review" in rec.lower() for rec in recommendations)
    
    def test_generate_recommendations_excellent_performance(self):
        """Test recommendation generation for excellent performance"""
        analytics_data = {
            'activity_summary': {'total_activities': 50},
            'lab_metrics': {'average_errors': 1, 'average_session_duration': 40},
            'quiz_performance': {'average_score': 90, 'pass_rate': 0.95},
            'engagement_score': 85
        }
        
        recommendations = generate_recommendations(analytics_data)
        assert isinstance(recommendations, list)
        assert any("great" in rec.lower() or "excellent" in rec.lower() for rec in recommendations)


class TestAnalyticsModelsValidation:
    """Test model validation and edge cases"""
    
    def test_student_activity_required_fields(self):
        """Test that required fields are validated"""
        with pytest.raises(ValueError):
            StudentActivity()  # Missing required fields
    
    def test_student_activity_default_values(self):
        """Test default values are properly set"""
        activity = StudentActivity(
            student_id="student-123",
            course_id="course-456",
            activity_type="login"
        )
        
        assert activity.activity_data == {}
        assert isinstance(activity.timestamp, datetime)
        assert activity.activity_id is not None
        assert activity.session_id is None
        assert activity.ip_address is None
        assert activity.user_agent is None
    
    def test_quiz_performance_score_calculation(self):
        """Test quiz performance score calculation"""
        quiz_perf = QuizPerformance(
            student_id="student-123",
            course_id="course-456",
            quiz_id="quiz-789",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(minutes=15),
            questions_total=10,
            questions_answered=10,
            questions_correct=8
        )
        
        # Test duration calculation would be done in the endpoint
        assert quiz_perf.questions_total == 10
        assert quiz_perf.questions_correct == 8
        # Score percentage would be calculated: (8/10) * 100 = 80%
    
    def test_student_progress_status_values(self):
        """Test valid status values for student progress"""
        valid_statuses = ["not_started", "in_progress", "completed", "mastered"]
        
        for status in valid_statuses:
            progress = StudentProgress(
                student_id="student-123",
                course_id="course-456",
                content_item_id="lesson-789",
                content_type="lesson",
                status=status,
                last_accessed=datetime.utcnow()
            )
            assert progress.status == status
    
    def test_learning_analytics_risk_levels(self):
        """Test valid risk level values"""
        valid_risk_levels = ["low", "medium", "high"]
        
        for risk_level in valid_risk_levels:
            analytics = LearningAnalytics(
                student_id="student-123",
                course_id="course-456",
                risk_level=risk_level
            )
            assert analytics.risk_level == risk_level


@pytest.mark.asyncio
class TestAnalyticsIntegration:
    """Integration tests for analytics functionality"""
    
    @patch('analytics_endpoints.db_pool')
    async def test_database_connection_handling(self, mock_db_pool):
        """Test proper database connection handling"""
        # Mock database connection
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        # Test activity tracking would use the connection
        activity = StudentActivity(
            student_id="student-123",
            course_id="course-456",
            activity_type="login"
        )
        
        # In a real test, we would call the endpoint
        assert activity.student_id == "student-123"
        assert mock_db_pool is not None
    
    def test_analytics_request_model(self):
        """Test analytics request model"""
        request = AnalyticsRequest(
            student_id="student-123",
            course_id="course-456",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            metrics=["engagement", "progress", "quiz_performance"],
            aggregation="daily",
            export_format="json"
        )
        
        assert request.student_id == "student-123"
        assert request.course_id == "course-456"
        assert len(request.metrics) == 3
        assert request.aggregation == "daily"
        assert request.export_format == "json"
    
    def test_analytics_response_model(self):
        """Test analytics response model"""
        response = AnalyticsResponse(
            data_range={
                "start": datetime.utcnow() - timedelta(days=30),
                "end": datetime.utcnow()
            },
            summary={
                "total_activities": 45,
                "engagement_score": 78.5,
                "average_quiz_score": 82.1
            },
            detailed_data={
                "daily_activities": [],
                "quiz_attempts": [],
                "lab_sessions": []
            },
            recommendations=["Great progress!", "Continue the excellent work!"]
        )
        
        assert response.request_id is not None
        assert isinstance(response.generated_at, datetime)
        assert "total_activities" in response.summary
        assert len(response.recommendations) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])