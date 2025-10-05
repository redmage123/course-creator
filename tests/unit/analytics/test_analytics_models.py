"""
Unit Tests for Analytics Domain Models

BUSINESS REQUIREMENT:
Validates domain models for learning analytics including student activities,
lab usage metrics, quiz performance, progress tracking, and comprehensive
analytics aggregations for educational effectiveness measurement.

TECHNICAL IMPLEMENTATION:
- Tests Pydantic model validation and business rules
- Tests domain entity validation from dataclasses
- Tests enum values and type constraints
- Tests calculated properties and methods
- Tests edge cases and boundary conditions
"""


import pytest
from datetime import datetime, timedelta
from domain.entities.student_analytics import (
    ActivityType,
    CompletionStatus,
    RiskLevel,
    ContentType,
    StudentActivity,
    LabUsageMetrics,
    QuizPerformance,
    StudentProgress,
    LearningAnalytics
)


class TestStudentActivityModel:
    """Test StudentActivity domain entity validation."""

    def test_create_valid_student_activity(self):
        """Test creating valid student activity."""
        activity = StudentActivity(
            student_id="student-123",
            course_id="course-456",
            activity_type=ActivityType.LAB_ACCESS,
            activity_data={"lab_id": "lab-789"}
        )

        assert activity.student_id == "student-123"
        assert activity.course_id == "course-456"
        assert activity.activity_type == ActivityType.LAB_ACCESS
        assert activity.activity_data["lab_id"] == "lab-789"
        assert activity.id is not None
        assert isinstance(activity.timestamp, datetime)

    def test_student_activity_missing_student_id(self):
        """Test activity validation fails without student_id."""
        with pytest.raises(ValueError, match="Student ID is required"):
            StudentActivity(
                student_id="",
                course_id="course-456",
                activity_type=ActivityType.LOGIN
            )

    def test_student_activity_missing_course_id(self):
        """Test activity validation fails without course_id."""
        with pytest.raises(ValueError, match="Course ID is required"):
            StudentActivity(
                student_id="student-123",
                course_id="",
                activity_type=ActivityType.LOGIN
            )

    def test_student_activity_future_timestamp_rejected(self):
        """Test that future timestamps are rejected."""
        future_time = datetime.utcnow() + timedelta(days=1)
        with pytest.raises(ValueError, match="timestamp cannot be in the future"):
            StudentActivity(
                student_id="student-123",
                course_id="course-456",
                activity_type=ActivityType.LOGIN,
                timestamp=future_time
            )

    def test_quiz_start_activity_requires_quiz_id(self):
        """Test quiz start activity requires quiz_id in activity_data."""
        with pytest.raises(ValueError, match="Quiz start activity must include quiz_id"):
            StudentActivity(
                student_id="student-123",
                course_id="course-456",
                activity_type=ActivityType.QUIZ_START,
                activity_data={}  # Missing quiz_id
            )

    def test_quiz_complete_activity_validation(self):
        """Test quiz complete activity requires all fields."""
        with pytest.raises(ValueError):
            StudentActivity(
                student_id="student-123",
                course_id="course-456",
                activity_type=ActivityType.QUIZ_COMPLETE,
                activity_data={"quiz_id": "quiz-123"}  # Missing score fields
            )

    def test_lab_access_activity_requires_lab_id(self):
        """Test lab access activity requires lab_id."""
        with pytest.raises(ValueError, match="Lab access activity must include lab_id"):
            StudentActivity(
                student_id="student-123",
                course_id="course-456",
                activity_type=ActivityType.LAB_ACCESS,
                activity_data={}
            )

    def test_code_execution_activity_requires_code_snippet(self):
        """Test code execution activity requires code_snippet."""
        with pytest.raises(ValueError, match="Code execution activity must include code_snippet"):
            StudentActivity(
                student_id="student-123",
                course_id="course-456",
                activity_type=ActivityType.CODE_EXECUTION,
                activity_data={}
            )

    def test_activity_duration_calculation(self):
        """Test duration calculation between activities."""
        activity1 = StudentActivity(
            student_id="student-123",
            course_id="course-456",
            activity_type=ActivityType.LOGIN,
            timestamp=datetime.utcnow() - timedelta(minutes=10)
        )

        activity2 = StudentActivity(
            student_id="student-123",
            course_id="course-456",
            activity_type=ActivityType.LOGOUT,
            timestamp=datetime.utcnow()
        )

        duration = activity2.get_duration_from_previous(activity1)
        assert duration.total_seconds() >= 600  # At least 10 minutes

    def test_is_engagement_activity(self):
        """Test engagement activity detection."""
        engagement_activity = StudentActivity(
            student_id="student-123",
            course_id="course-456",
            activity_type=ActivityType.LAB_ACCESS,
            activity_data={"lab_id": "lab-123"}
        )
        assert engagement_activity.is_engagement_activity() is True

        non_engagement_activity = StudentActivity(
            student_id="student-123",
            course_id="course-456",
            activity_type=ActivityType.LOGIN
        )
        assert non_engagement_activity.is_engagement_activity() is False


class TestLabUsageMetrics:
    """Test LabUsageMetrics domain entity validation."""

    def test_create_valid_lab_usage(self):
        """Test creating valid lab usage metrics."""
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
        assert lab_usage.completion_status == CompletionStatus.IN_PROGRESS

    def test_lab_usage_missing_required_fields(self):
        """Test validation fails with missing fields."""
        with pytest.raises(ValueError, match="Student ID is required"):
            LabUsageMetrics(
                student_id="",
                course_id="course-456",
                lab_id="lab-789",
                session_start=datetime.utcnow()
            )

    def test_lab_usage_negative_values_rejected(self):
        """Test negative values are rejected."""
        with pytest.raises(ValueError, match="Actions performed cannot be negative"):
            LabUsageMetrics(
                student_id="student-123",
                course_id="course-456",
                lab_id="lab-789",
                session_start=datetime.utcnow(),
                actions_performed=-5
            )

    def test_lab_usage_invalid_session_times(self):
        """Test session end before start is rejected."""
        start_time = datetime.utcnow()
        end_time = start_time - timedelta(minutes=10)

        with pytest.raises(ValueError, match="Session end cannot be before session start"):
            LabUsageMetrics(
                student_id="student-123",
                course_id="course-456",
                lab_id="lab-789",
                session_start=start_time,
                session_end=end_time
            )

    def test_lab_usage_duration_calculation(self):
        """Test session duration calculation."""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=45)

        lab_usage = LabUsageMetrics(
            student_id="student-123",
            course_id="course-456",
            lab_id="lab-789",
            session_start=start_time,
            session_end=end_time
        )

        duration = lab_usage.get_duration_minutes()
        assert duration == 45

    def test_lab_usage_productivity_score(self):
        """Test productivity score calculation."""
        lab_usage = LabUsageMetrics(
            student_id="student-123",
            course_id="course-456",
            lab_id="lab-789",
            session_start=datetime.utcnow(),
            actions_performed=50,  # High activity
            code_executions=25,
            errors_encountered=2  # Low errors
        )

        score = lab_usage.get_productivity_score()
        assert score == 4.0  # 50 actions / 10 = 5.0, minus 2 errors * 0.5 = 4.0

    def test_lab_usage_engagement_levels(self):
        """Test engagement level determination."""
        # High engagement
        high_engagement = LabUsageMetrics(
            student_id="student-123",
            course_id="course-456",
            lab_id="lab-789",
            session_start=datetime.utcnow() - timedelta(minutes=30),
            session_end=datetime.utcnow(),
            actions_performed=20
        )
        assert high_engagement.get_engagement_level() == "high"

        # Low engagement
        low_engagement = LabUsageMetrics(
            student_id="student-123",
            course_id="course-456",
            lab_id="lab-789",
            session_start=datetime.utcnow() - timedelta(minutes=3),
            session_end=datetime.utcnow(),
            actions_performed=1
        )
        assert low_engagement.get_engagement_level() == "low"

    def test_end_session_updates_status(self):
        """Test ending session updates completion status."""
        lab_usage = LabUsageMetrics(
            student_id="student-123",
            course_id="course-456",
            lab_id="lab-789",
            session_start=datetime.utcnow(),
            actions_performed=10,
            code_executions=5
        )

        lab_usage.end_session(final_code="print('Hello World')")

        assert lab_usage.session_end is not None
        assert lab_usage.final_code == "print('Hello World')"
        assert lab_usage.completion_status == CompletionStatus.COMPLETED


class TestQuizPerformance:
    """Test QuizPerformance domain entity validation."""

    def test_create_valid_quiz_performance(self):
        """Test creating valid quiz performance record."""
        quiz_perf = QuizPerformance(
            student_id="student-123",
            course_id="course-456",
            quiz_id="quiz-789",
            attempt_number=1,
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=8
        )

        assert quiz_perf.student_id == "student-123"
        assert quiz_perf.questions_total == 10
        assert quiz_perf.questions_correct == 8
        assert quiz_perf.status == CompletionStatus.IN_PROGRESS

    def test_quiz_performance_score_calculation(self):
        """Test score percentage calculation."""
        quiz_perf = QuizPerformance(
            student_id="student-123",
            course_id="course-456",
            quiz_id="quiz-789",
            attempt_number=1,
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=8
        )

        score = quiz_perf.get_score_percentage()
        assert score == 80.0

    def test_quiz_performance_validation_errors(self):
        """Test validation rejects invalid quiz data."""
        with pytest.raises(ValueError, match="Attempt number must be positive"):
            QuizPerformance(
                student_id="student-123",
                course_id="course-456",
                quiz_id="quiz-789",
                attempt_number=0,  # Invalid
                start_time=datetime.utcnow(),
                questions_total=10
            )

    def test_quiz_duration_calculation(self):
        """Test quiz duration calculation."""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=15)

        quiz_perf = QuizPerformance(
            student_id="student-123",
            course_id="course-456",
            quiz_id="quiz-789",
            attempt_number=1,
            start_time=start_time,
            end_time=end_time,
            questions_total=10
        )

        duration = quiz_perf.get_duration_minutes()
        assert duration == 15

    def test_quiz_performance_levels(self):
        """Test performance level categorization."""
        excellent_quiz = QuizPerformance(
            student_id="student-123",
            course_id="course-456",
            quiz_id="quiz-789",
            attempt_number=1,
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=9
        )
        assert excellent_quiz.get_performance_level() == "excellent"

        poor_quiz = QuizPerformance(
            student_id="student-123",
            course_id="course-456",
            quiz_id="quiz-789",
            attempt_number=1,
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=4
        )
        assert poor_quiz.get_performance_level() == "poor"


class TestStudentProgress:
    """Test StudentProgress domain entity validation."""

    def test_create_valid_student_progress(self):
        """Test creating valid progress record."""
        progress = StudentProgress(
            student_id="student-123",
            course_id="course-456",
            content_item_id="lesson-789",
            content_type=ContentType.LESSON,
            progress_percentage=75.5,
            time_spent_minutes=45
        )

        assert progress.student_id == "student-123"
        assert progress.progress_percentage == 75.5
        assert progress.status == CompletionStatus.NOT_STARTED

    def test_progress_percentage_validation(self):
        """Test progress percentage bounds validation."""
        with pytest.raises(ValueError, match="Progress percentage must be between 0 and 100"):
            StudentProgress(
                student_id="student-123",
                course_id="course-456",
                content_item_id="lesson-789",
                content_type=ContentType.LESSON,
                progress_percentage=150.0  # Invalid
            )

    def test_update_progress_changes_status(self):
        """Test updating progress changes completion status."""
        progress = StudentProgress(
            student_id="student-123",
            course_id="course-456",
            content_item_id="lesson-789",
            content_type=ContentType.LESSON
        )

        progress.update_progress(50.0, time_spent_additional=30)
        assert progress.progress_percentage == 50.0
        assert progress.status == CompletionStatus.IN_PROGRESS

        progress.update_progress(100.0, time_spent_additional=30)
        assert progress.status == CompletionStatus.COMPLETED
        assert progress.completion_date is not None

    def test_mark_mastered_sets_completion(self):
        """Test marking content as mastered."""
        progress = StudentProgress(
            student_id="student-123",
            course_id="course-456",
            content_item_id="lesson-789",
            content_type=ContentType.LESSON
        )

        progress.mark_mastered(mastery_score=92.5)

        assert progress.status == CompletionStatus.MASTERED
        assert progress.mastery_score == 92.5
        assert progress.progress_percentage == 100.0
        assert progress.completion_date is not None

    def test_learning_velocity_calculation(self):
        """Test learning velocity calculation."""
        progress = StudentProgress(
            student_id="student-123",
            course_id="course-456",
            content_item_id="lesson-789",
            content_type=ContentType.LESSON,
            progress_percentage=60.0
        )

        velocity = progress.get_learning_velocity(days_since_start=10)
        assert velocity == 6.0  # 60% / 10 days

    def test_at_risk_student_detection(self):
        """Test at-risk student identification."""
        progress = StudentProgress(
            student_id="student-123",
            course_id="course-456",
            content_item_id="lesson-789",
            content_type=ContentType.LESSON,
            progress_percentage=30.0,  # Behind expected
            last_accessed=datetime.utcnow() - timedelta(days=5)  # Not accessed recently
        )

        is_at_risk = progress.is_at_risk(expected_progress=70.0, days_since_start=10)
        assert is_at_risk is True


class TestLearningAnalytics:
    """Test LearningAnalytics comprehensive domain entity."""

    def test_create_valid_learning_analytics(self):
        """Test creating comprehensive learning analytics."""
        analytics = LearningAnalytics(
            student_id="student-123",
            course_id="course-456",
            engagement_score=78.5,
            progress_velocity=2.3,
            lab_proficiency=82.1,
            quiz_performance=75.2,
            time_on_platform=120,
            streak_days=7,
            risk_level=RiskLevel.LOW
        )

        assert analytics.engagement_score == 78.5
        assert analytics.risk_level == RiskLevel.LOW

    def test_overall_performance_calculation(self):
        """Test overall performance score calculation."""
        analytics = LearningAnalytics(
            student_id="student-123",
            course_id="course-456",
            engagement_score=80.0,
            progress_velocity=5.0,  # Will be normalized
            lab_proficiency=85.0,
            quiz_performance=90.0
        )

        overall = analytics.calculate_overall_performance()
        assert 0 <= overall <= 100
        assert overall > 75  # Should be high overall

    def test_risk_level_update_critical(self):
        """Test risk level update for critical risk."""
        analytics = LearningAnalytics(
            student_id="student-123",
            course_id="course-456",
            engagement_score=25.0,  # Low
            progress_velocity=0.5,
            lab_proficiency=30.0,
            quiz_performance=35.0,
            streak_days=0
        )

        analytics.update_risk_level()
        assert analytics.risk_level == RiskLevel.CRITICAL

    def test_generate_recommendations_low_engagement(self):
        """Test recommendation generation for low engagement."""
        analytics = LearningAnalytics(
            student_id="student-123",
            course_id="course-456",
            engagement_score=40.0,  # Low
            progress_velocity=2.0,
            lab_proficiency=70.0,
            quiz_performance=75.0,
            time_on_platform=30
        )

        recommendations = analytics.generate_recommendations()
        assert any("engagement" in rec.lower() for rec in recommendations)
        assert any("study time" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_low_lab_proficiency(self):
        """Test recommendations for low lab proficiency."""
        analytics = LearningAnalytics(
            student_id="student-123",
            course_id="course-456",
            engagement_score=70.0,
            progress_velocity=2.0,
            lab_proficiency=50.0,  # Low
            quiz_performance=75.0
        )

        recommendations = analytics.generate_recommendations()
        assert any("lab" in rec.lower() or "coding practice" in rec.lower() for rec in recommendations)


# Run tests with: pytest tests/unit/analytics/test_analytics_models.py -v
