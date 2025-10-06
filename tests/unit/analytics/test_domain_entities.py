"""
Unit Tests for Analytics Domain Entities
Following SOLID principles and TDD methodology
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

# Import domain entities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'analytics'))

from analytics.domain.entities.student_analytics import (
    StudentActivity, LabUsageMetrics, QuizPerformance, StudentProgress, 
    LearningAnalytics, ActivityType, ContentType, RiskLevel, ProgressStatus
)


class TestStudentActivity:
    """Test StudentActivity domain entity following TDD principles"""
    
    def test_student_activity_creation_with_valid_data(self):
        """Test creating student activity with valid data"""
        # Arrange
        student_id = str(uuid4())
        course_id = str(uuid4())
        activity_type = ActivityType.LOGIN
        activity_data = {"ip_address": "192.168.1.1"}
        
        # Act
        activity = StudentActivity(
            student_id=student_id,
            course_id=course_id,
            activity_type=activity_type,
            activity_data=activity_data
        )
        
        # Assert
        assert activity.student_id == student_id
        assert activity.course_id == course_id
        assert activity.activity_type == activity_type
        assert activity.activity_data == activity_data
        assert activity.timestamp is not None
        assert isinstance(activity.id, str)
    
    def test_student_activity_creation_with_empty_student_id_raises_error(self):
        """Test creating activity with empty student_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Student ID cannot be empty"):
            StudentActivity(
                student_id="",
                course_id=str(uuid4()),
                activity_type=ActivityType.LOGIN,
                activity_data={}
            )
    
    def test_student_activity_creation_with_empty_course_id_raises_error(self):
        """Test creating activity with empty course_id raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Course ID cannot be empty"):
            StudentActivity(
                student_id=str(uuid4()),
                course_id="",
                activity_type=ActivityType.LOGIN,
                activity_data={}
            )
    
    def test_student_activity_is_engagement_activity_returns_correct_boolean(self):
        """Test is_engagement_activity returns correct boolean"""
        # Arrange
        engagement_activities = [
            ActivityType.QUIZ_START,
            ActivityType.LAB_START,
            ActivityType.CONTENT_VIEW,
            ActivityType.DISCUSSION_POST
        ]
        
        non_engagement_activities = [
            ActivityType.LOGIN,
            ActivityType.LOGOUT
        ]
        
        # Act & Assert
        for activity_type in engagement_activities:
            activity = StudentActivity(
                student_id=str(uuid4()),
                course_id=str(uuid4()),
                activity_type=activity_type,
                activity_data={}
            )
            assert activity.is_engagement_activity()
        
        for activity_type in non_engagement_activities:
            activity = StudentActivity(
                student_id=str(uuid4()),
                course_id=str(uuid4()),
                activity_type=activity_type,
                activity_data={}
            )
            assert not activity.is_engagement_activity()
    
    def test_student_activity_get_duration_returns_none_for_instant_activity(self):
        """Test get_duration returns None for instant activity"""
        # Arrange
        activity = StudentActivity(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            activity_type=ActivityType.LOGIN,
            activity_data={}
        )
        
        # Act & Assert
        assert activity.get_duration() is None
    
    def test_student_activity_get_duration_returns_timedelta_for_duration_activity(self):
        """Test get_duration returns timedelta for activity with duration"""
        # Arrange
        duration_seconds = 300  # 5 minutes
        activity = StudentActivity(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            activity_type=ActivityType.CONTENT_VIEW,
            activity_data={"duration_seconds": duration_seconds}
        )
        
        # Act
        duration = activity.get_duration()
        
        # Assert
        assert duration is not None
        assert duration.total_seconds() == duration_seconds


class TestLabUsageMetrics:
    """Test LabUsageMetrics domain entity following TDD principles"""
    
    def test_lab_usage_metrics_creation_with_valid_data(self):
        """Test creating lab usage metrics with valid data"""
        # Arrange
        student_id = str(uuid4())
        course_id = str(uuid4())
        lab_id = str(uuid4())
        session_start = datetime.utcnow()
        
        # Act
        metrics = LabUsageMetrics(
            student_id=student_id,
            course_id=course_id,
            lab_id=lab_id,
            session_start=session_start
        )
        
        # Assert
        assert metrics.student_id == student_id
        assert metrics.course_id == course_id
        assert metrics.lab_id == lab_id
        assert metrics.session_start == session_start
        assert metrics.actions_performed == 0
        assert metrics.code_executions == 0
        assert metrics.errors_encountered == 0
        assert metrics.session_end is None
        assert isinstance(metrics.id, str)
    
    def test_lab_usage_metrics_end_session_success(self):
        """Test ending lab session successfully"""
        # Arrange
        metrics = LabUsageMetrics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            lab_id=str(uuid4()),
            session_start=datetime.utcnow()
        )
        final_code = "print('Hello, World!')"
        
        # Act
        metrics.end_session(final_code)
        
        # Assert
        assert metrics.session_end is not None
        assert metrics.final_code == final_code
        assert metrics.session_end > metrics.session_start
    
    def test_lab_usage_metrics_get_session_duration_returns_none_for_active_session(self):
        """Test get_session_duration returns None for active session"""
        # Arrange
        metrics = LabUsageMetrics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            lab_id=str(uuid4()),
            session_start=datetime.utcnow()
        )
        
        # Act & Assert
        assert metrics.get_session_duration() is None
    
    def test_lab_usage_metrics_get_session_duration_returns_timedelta_for_ended_session(self):
        """Test get_session_duration returns timedelta for ended session"""
        # Arrange
        start_time = datetime.utcnow()
        metrics = LabUsageMetrics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            lab_id=str(uuid4()),
            session_start=start_time
        )
        
        # Wait and end session
        import time
        time.sleep(0.1)
        metrics.end_session("final code")
        
        # Act
        duration = metrics.get_session_duration()
        
        # Assert
        assert duration is not None
        assert duration.total_seconds() > 0
    
    def test_lab_usage_metrics_get_productivity_score_calculates_correctly(self):
        """Test get_productivity_score calculates score correctly"""
        # Arrange
        metrics = LabUsageMetrics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            lab_id=str(uuid4()),
            session_start=datetime.utcnow(),
            actions_performed=20,
            code_executions=5,
            errors_encountered=2
        )
        
        # Act
        score = metrics.get_productivity_score()
        
        # Assert
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_lab_usage_metrics_get_engagement_level_returns_correct_level(self):
        """Test get_engagement_level returns correct engagement level"""
        # Test high engagement
        high_engagement_metrics = LabUsageMetrics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            lab_id=str(uuid4()),
            session_start=datetime.utcnow(),
            actions_performed=50,
            code_executions=15
        )
        
        # Test low engagement
        low_engagement_metrics = LabUsageMetrics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            lab_id=str(uuid4()),
            session_start=datetime.utcnow(),
            actions_performed=2,
            code_executions=0
        )
        
        # Act & Assert
        assert high_engagement_metrics.get_engagement_level() == "high"
        assert low_engagement_metrics.get_engagement_level() == "low"


class TestQuizPerformance:
    """Test QuizPerformance domain entity following TDD principles"""
    
    def test_quiz_performance_creation_with_valid_data(self):
        """Test creating quiz performance with valid data"""
        # Arrange
        student_id = str(uuid4())
        course_id = str(uuid4())
        quiz_id = str(uuid4())
        start_time = datetime.utcnow()
        questions_total = 10
        
        # Act
        performance = QuizPerformance(
            student_id=student_id,
            course_id=course_id,
            quiz_id=quiz_id,
            start_time=start_time,
            questions_total=questions_total
        )
        
        # Assert
        assert performance.student_id == student_id
        assert performance.course_id == course_id
        assert performance.quiz_id == quiz_id
        assert performance.start_time == start_time
        assert performance.questions_total == questions_total
        assert performance.attempt_number == 1
        assert performance.questions_answered == 0
        assert performance.questions_correct == 0
        assert performance.end_time is None
        assert isinstance(performance.id, str)
    
    def test_quiz_performance_complete_quiz_success(self):
        """Test completing quiz successfully"""
        # Arrange
        performance = QuizPerformance(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            quiz_id=str(uuid4()),
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=8
        )
        
        # Act
        performance.complete_quiz()
        
        # Assert
        assert performance.end_time is not None
        assert performance.end_time > performance.start_time
    
    def test_quiz_performance_get_score_percentage_calculates_correctly(self):
        """Test get_score_percentage calculates percentage correctly"""
        # Arrange
        performance = QuizPerformance(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            quiz_id=str(uuid4()),
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=8
        )
        
        # Act
        score_percentage = performance.get_score_percentage()
        
        # Assert
        assert score_percentage == 80.0
    
    def test_quiz_performance_get_score_percentage_returns_zero_for_no_questions(self):
        """Test get_score_percentage returns 0 for no questions answered"""
        # Arrange
        performance = QuizPerformance(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            quiz_id=str(uuid4()),
            start_time=datetime.utcnow(),
            questions_total=10
        )
        
        # Act & Assert
        assert performance.get_score_percentage() == 0.0
    
    def test_quiz_performance_get_duration_minutes_calculates_correctly(self):
        """Test get_duration_minutes calculates duration correctly"""
        # Arrange
        start_time = datetime.utcnow()
        performance = QuizPerformance(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            quiz_id=str(uuid4()),
            start_time=start_time,
            questions_total=10
        )
        
        # Wait and complete
        import time
        time.sleep(0.1)
        performance.complete_quiz()
        
        # Act
        duration_minutes = performance.get_duration_minutes()
        
        # Assert
        assert duration_minutes > 0
        assert isinstance(duration_minutes, float)
    
    def test_quiz_performance_get_performance_level_returns_correct_level(self):
        """Test get_performance_level returns correct level"""
        # Test excellent performance
        excellent_performance = QuizPerformance(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            quiz_id=str(uuid4()),
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=9
        )
        
        # Test poor performance
        poor_performance = QuizPerformance(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            quiz_id=str(uuid4()),
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=3
        )
        
        # Act & Assert
        assert excellent_performance.get_performance_level() == "excellent"
        assert poor_performance.get_performance_level() == "poor"


class TestStudentProgress:
    """Test StudentProgress domain entity following TDD principles"""
    
    def test_student_progress_creation_with_valid_data(self):
        """Test creating student progress with valid data"""
        # Arrange
        student_id = str(uuid4())
        course_id = str(uuid4())
        content_item_id = str(uuid4())
        content_type = ContentType.MODULE
        
        # Act
        progress = StudentProgress(
            student_id=student_id,
            course_id=course_id,
            content_item_id=content_item_id,
            content_type=content_type
        )
        
        # Assert
        assert progress.student_id == student_id
        assert progress.course_id == course_id
        assert progress.content_item_id == content_item_id
        assert progress.content_type == content_type
        assert progress.progress_percentage == 0.0
        assert progress.status == ProgressStatus.NOT_STARTED
        assert progress.first_accessed is not None
        assert progress.last_accessed is not None
        assert isinstance(progress.id, str)
    
    def test_student_progress_update_progress_success(self):
        """Test updating progress successfully"""
        # Arrange
        progress = StudentProgress(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            content_item_id=str(uuid4()),
            content_type=ContentType.MODULE
        )
        original_last_accessed = progress.last_accessed
        
        # Act
        progress.update_progress(75.5, 120)  # 75.5% progress, 120 seconds additional time
        
        # Assert
        assert progress.progress_percentage == 75.5
        assert progress.time_spent_minutes == 2.0  # 120 seconds = 2 minutes
        assert progress.status == ProgressStatus.IN_PROGRESS
        assert progress.last_accessed > original_last_accessed
    
    def test_student_progress_update_progress_with_invalid_percentage_raises_error(self):
        """Test updating progress with invalid percentage raises ValueError"""
        # Arrange
        progress = StudentProgress(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            content_item_id=str(uuid4()),
            content_type=ContentType.MODULE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Progress percentage must be between 0 and 100"):
            progress.update_progress(150.0)
    
    def test_student_progress_mark_completed_success(self):
        """Test marking progress as completed successfully"""
        # Arrange
        progress = StudentProgress(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            content_item_id=str(uuid4()),
            content_type=ContentType.MODULE
        )
        
        # Act
        progress.mark_completed()
        
        # Assert
        assert progress.progress_percentage == 100.0
        assert progress.status == ProgressStatus.COMPLETED
        assert progress.completion_date is not None
    
    def test_student_progress_mark_mastered_success(self):
        """Test marking progress as mastered successfully"""
        # Arrange
        progress = StudentProgress(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            content_item_id=str(uuid4()),
            content_type=ContentType.MODULE
        )
        mastery_score = 95.0
        
        # Act
        progress.mark_mastered(mastery_score)
        
        # Assert
        assert progress.status == ProgressStatus.MASTERED
        assert progress.mastery_score == mastery_score
        assert progress.mastery_date is not None
    
    def test_student_progress_is_completed_returns_correct_boolean(self):
        """Test is_completed returns correct boolean"""
        # Arrange
        incomplete_progress = StudentProgress(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            content_item_id=str(uuid4()),
            content_type=ContentType.MODULE
        )
        
        completed_progress = StudentProgress(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            content_item_id=str(uuid4()),
            content_type=ContentType.MODULE
        )
        completed_progress.mark_completed()
        
        # Act & Assert
        assert not incomplete_progress.is_completed()
        assert completed_progress.is_completed()


class TestLearningAnalytics:
    """Test LearningAnalytics domain entity following TDD principles"""
    
    def test_learning_analytics_creation_with_valid_data(self):
        """Test creating learning analytics with valid data"""
        # Arrange
        student_id = str(uuid4())
        course_id = str(uuid4())
        analysis_date = datetime.utcnow()
        
        # Act
        analytics = LearningAnalytics(
            student_id=student_id,
            course_id=course_id,
            analysis_date=analysis_date,
            engagement_score=75.5,
            progress_velocity=2.3,
            lab_proficiency=80.0,
            quiz_performance=85.0,
            time_on_platform=120,
            streak_days=7
        )
        
        # Assert
        assert analytics.student_id == student_id
        assert analytics.course_id == course_id
        assert analytics.analysis_date == analysis_date
        assert analytics.engagement_score == 75.5
        assert analytics.progress_velocity == 2.3
        assert analytics.lab_proficiency == 80.0
        assert analytics.quiz_performance == 85.0
        assert analytics.time_on_platform == 120
        assert analytics.streak_days == 7
        assert analytics.risk_level == RiskLevel.LOW  # Default
        assert analytics.recommendations == []
        assert isinstance(analytics.id, str)
    
    def test_learning_analytics_calculate_overall_performance_success(self):
        """Test calculating overall performance successfully"""
        # Arrange
        analytics = LearningAnalytics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            analysis_date=datetime.utcnow(),
            engagement_score=80.0,
            progress_velocity=2.0,
            lab_proficiency=75.0,
            quiz_performance=85.0,
            time_on_platform=100,
            streak_days=5
        )
        
        # Act
        overall_performance = analytics.calculate_overall_performance()
        
        # Assert
        assert isinstance(overall_performance, float)
        assert 0 <= overall_performance <= 100
    
    def test_learning_analytics_assess_risk_level_calculates_correctly(self):
        """Test assess_risk_level calculates risk correctly"""
        # Test high-risk student
        high_risk_analytics = LearningAnalytics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            analysis_date=datetime.utcnow(),
            engagement_score=30.0,
            progress_velocity=0.5,
            lab_proficiency=25.0,
            quiz_performance=35.0,
            time_on_platform=10,
            streak_days=1
        )
        
        # Test low-risk student
        low_risk_analytics = LearningAnalytics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            analysis_date=datetime.utcnow(),
            engagement_score=90.0,
            progress_velocity=3.0,
            lab_proficiency=85.0,
            quiz_performance=90.0,
            time_on_platform=200,
            streak_days=15
        )
        
        # Act
        high_risk_level = high_risk_analytics.assess_risk_level()
        low_risk_level = low_risk_analytics.assess_risk_level()
        
        # Assert
        assert high_risk_level == RiskLevel.HIGH
        assert low_risk_level == RiskLevel.LOW
    
    def test_learning_analytics_add_recommendation_success(self):
        """Test adding recommendation successfully"""
        # Arrange
        analytics = LearningAnalytics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            analysis_date=datetime.utcnow(),
            engagement_score=70.0,
            progress_velocity=2.0,
            lab_proficiency=75.0,
            quiz_performance=80.0,
            time_on_platform=100,
            streak_days=5
        )
        recommendation = "Focus more on lab exercises"
        
        # Act
        analytics.add_recommendation(recommendation)
        
        # Assert
        assert recommendation in analytics.recommendations
    
    def test_learning_analytics_update_risk_level_success(self):
        """Test updating risk level successfully"""
        # Arrange
        analytics = LearningAnalytics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            analysis_date=datetime.utcnow(),
            engagement_score=70.0,
            progress_velocity=2.0,
            lab_proficiency=75.0,
            quiz_performance=80.0,
            time_on_platform=100,
            streak_days=5
        )
        
        # Act
        analytics.update_risk_level(RiskLevel.MEDIUM)
        
        # Assert
        assert analytics.risk_level == RiskLevel.MEDIUM
    
    def test_learning_analytics_get_performance_summary_returns_dict(self):
        """Test get_performance_summary returns dictionary"""
        # Arrange
        analytics = LearningAnalytics(
            student_id=str(uuid4()),
            course_id=str(uuid4()),
            analysis_date=datetime.utcnow(),
            engagement_score=75.0,
            progress_velocity=2.5,
            lab_proficiency=80.0,
            quiz_performance=85.0,
            time_on_platform=120,
            streak_days=8
        )
        
        # Act
        summary = analytics.get_performance_summary()
        
        # Assert
        assert isinstance(summary, dict)
        assert "overall_performance" in summary
        assert "risk_level" in summary
        assert "engagement_score" in summary
        assert "recommendations_count" in summary


class TestEnums:
    """Test enumeration classes"""
    
    def test_activity_type_enum_values(self):
        """Test ActivityType enum has expected values"""
        assert ActivityType.LOGIN.value == "login"
        assert ActivityType.LOGOUT.value == "logout"
        assert ActivityType.CONTENT_VIEW.value == "content_view"
        assert ActivityType.QUIZ_START.value == "quiz_start"
        assert ActivityType.QUIZ_COMPLETE.value == "quiz_complete"
        assert ActivityType.LAB_START.value == "lab_start"
        assert ActivityType.LAB_COMPLETE.value == "lab_complete"
        assert ActivityType.DISCUSSION_POST.value == "discussion_post"
    
    def test_content_type_enum_values(self):
        """Test ContentType enum has expected values"""
        assert ContentType.MODULE.value == "module"
        assert ContentType.LESSON.value == "lesson"
        assert ContentType.LAB.value == "lab"
        assert ContentType.QUIZ.value == "quiz"
        assert ContentType.ASSIGNMENT.value == "assignment"
        assert ContentType.EXERCISE.value == "exercise"
    
    def test_risk_level_enum_values(self):
        """Test RiskLevel enum has expected values"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"
    
    def test_progress_status_enum_values(self):
        """Test ProgressStatus enum has expected values"""
        assert ProgressStatus.NOT_STARTED.value == "not_started"
        assert ProgressStatus.IN_PROGRESS.value == "in_progress"
        assert ProgressStatus.COMPLETED.value == "completed"
        assert ProgressStatus.MASTERED.value == "mastered"