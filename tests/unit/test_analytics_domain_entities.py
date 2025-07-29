"""
Unit Tests for Analytics Domain Entities
Testing analytics domain business logic and validation rules following SOLID principles
"""
import pytest
from datetime import datetime, timedelta
from services.analytics.domain.entities.student_analytics import (
    StudentActivity, LabUsageMetrics, QuizPerformance, 
    StudentProgress, LearningAnalytics, 
    ActivityType, CompletionStatus, RiskLevel, ContentType
)

class TestStudentActivity:
    """Test student activity domain entity business logic"""
    
    def test_student_activity_creation_valid(self):
        """Test valid student activity creation"""
        activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.LAB_ACCESS,
            activity_data={"lab_id": "lab_001", "action": "start_session"}
        )
        
        assert activity.student_id == "student_123"
        assert activity.course_id == "course_456"
        assert activity.activity_type == ActivityType.LAB_ACCESS
        assert activity.activity_data["lab_id"] == "lab_001"
        assert isinstance(activity.timestamp, datetime)
        assert len(activity.id) > 0
    
    def test_student_activity_validation_empty_student_id(self):
        """Test activity validation with empty student ID"""
        with pytest.raises(ValueError, match="Student ID is required"):
            StudentActivity(
                student_id="",
                course_id="course_456",
                activity_type=ActivityType.LOGIN
            )
    
    def test_student_activity_validation_empty_course_id(self):
        """Test activity validation with empty course ID"""
        with pytest.raises(ValueError, match="Course ID is required"):
            StudentActivity(
                student_id="student_123",
                course_id="",
                activity_type=ActivityType.LOGIN
            )
    
    def test_student_activity_validation_future_timestamp(self):
        """Test activity validation with future timestamp"""
        with pytest.raises(ValueError, match="Activity timestamp cannot be in the future"):
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.LOGIN,
                timestamp=datetime.utcnow() + timedelta(hours=1)
            )
    
    def test_student_activity_validate_quiz_start_data(self):
        """Test validation of quiz start activity data"""
        with pytest.raises(ValueError, match="Quiz start activity must include quiz_id"):
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.QUIZ_START,
                activity_data={"action": "start"}  # Missing quiz_id
            )
    
    def test_student_activity_validate_quiz_complete_data(self):
        """Test validation of quiz complete activity data"""
        with pytest.raises(ValueError, match="Quiz complete activity must include score"):
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.QUIZ_COMPLETE,
                activity_data={"quiz_id": "quiz_001"}  # Missing required fields
            )
    
    def test_student_activity_get_duration_from_previous(self):
        """Test calculating duration between activities"""
        earlier_activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.LOGIN,
            timestamp=datetime.utcnow() - timedelta(minutes=30)
        )
        
        later_activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.LOGOUT,
            timestamp=datetime.utcnow()
        )
        
        duration = later_activity.get_duration_from_previous(earlier_activity)
        assert duration.total_seconds() >= 1800  # At least 30 minutes
    
    def test_student_activity_get_duration_invalid_order(self):
        """Test duration calculation with invalid activity order"""
        later_activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.LOGIN,
            timestamp=datetime.utcnow()
        )
        
        earlier_activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.LOGOUT,
            timestamp=datetime.utcnow() - timedelta(minutes=30)
        )
        
        with pytest.raises(ValueError, match="Previous activity cannot be after current activity"):
            later_activity.get_duration_from_previous(earlier_activity)
    
    def test_student_activity_is_engagement_activity(self):
        """Test identifying engagement activities"""
        engagement_activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.LAB_ACCESS
        )
        
        non_engagement_activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.LOGOUT
        )
        
        assert engagement_activity.is_engagement_activity() == True
        assert non_engagement_activity.is_engagement_activity() == False

class TestLabUsageMetrics:
    """Test lab usage metrics domain entity business logic"""
    
    def test_lab_usage_creation_valid(self):
        """Test valid lab usage metrics creation"""
        lab_metrics = LabUsageMetrics(
            student_id="student_123",
            course_id="course_456",
            lab_id="lab_python_basics",
            session_start=datetime.utcnow() - timedelta(minutes=45),
            actions_performed=25,
            code_executions=8,
            errors_encountered=3
        )
        
        assert lab_metrics.student_id == "student_123"
        assert lab_metrics.course_id == "course_456"
        assert lab_metrics.lab_id == "lab_python_basics"
        assert lab_metrics.actions_performed == 25
        assert lab_metrics.code_executions == 8
        assert lab_metrics.errors_encountered == 3
        assert lab_metrics.completion_status == CompletionStatus.IN_PROGRESS
    
    def test_lab_usage_validation_empty_fields(self):
        """Test lab usage validation with empty required fields"""
        with pytest.raises(ValueError, match="Student ID is required"):
            LabUsageMetrics(
                student_id="",
                course_id="course_456",
                lab_id="lab_001",
                session_start=datetime.utcnow()
            )
    
    def test_lab_usage_validation_negative_values(self):
        """Test lab usage validation with negative values"""
        with pytest.raises(ValueError, match="Actions performed cannot be negative"):
            LabUsageMetrics(
                student_id="student_123",
                course_id="course_456",
                lab_id="lab_001",
                session_start=datetime.utcnow(),
                actions_performed=-5
            )
    
    def test_lab_usage_validation_invalid_session_times(self):
        """Test lab usage validation with invalid session times"""
        with pytest.raises(ValueError, match="Session end cannot be before session start"):
            LabUsageMetrics(
                student_id="student_123",
                course_id="course_456",
                lab_id="lab_001",
                session_start=datetime.utcnow(),
                session_end=datetime.utcnow() - timedelta(minutes=30)
            )
    
    def test_lab_usage_get_duration_minutes(self):
        """Test calculating session duration in minutes"""
        start_time = datetime.utcnow() - timedelta(minutes=45)
        end_time = datetime.utcnow()
        
        lab_metrics = LabUsageMetrics(
            student_id="student_123",
            course_id="course_456",
            lab_id="lab_001",
            session_start=start_time,
            session_end=end_time,
            actions_performed=20
        )
        
        duration = lab_metrics.get_duration_minutes()
        assert duration >= 44  # Should be approximately 45 minutes
        assert duration <= 46
    
    def test_lab_usage_get_duration_no_end_time(self):
        """Test duration calculation with no end time"""
        lab_metrics = LabUsageMetrics(
            student_id="student_123",
            course_id="course_456",
            lab_id="lab_001",
            session_start=datetime.utcnow(),
            actions_performed=10
        )
        
        duration = lab_metrics.get_duration_minutes()
        assert duration is None
    
    def test_lab_usage_get_productivity_score(self):
        """Test calculating productivity score"""
        lab_metrics = LabUsageMetrics(
            student_id="student_123",
            course_id="course_456",
            lab_id="lab_001",
            session_start=datetime.utcnow(),
            actions_performed=30,  # High activity
            errors_encountered=2   # Few errors
        )
        
        productivity_score = lab_metrics.get_productivity_score()
        assert productivity_score > 0
        assert productivity_score <= 10  # Max score is 10
    
    def test_lab_usage_get_productivity_score_no_actions(self):
        """Test productivity score with no actions"""
        lab_metrics = LabUsageMetrics(
            student_id="student_123",
            course_id="course_456",
            lab_id="lab_001",
            session_start=datetime.utcnow(),
            actions_performed=0
        )
        
        productivity_score = lab_metrics.get_productivity_score()
        assert productivity_score == 0.0
    
    def test_lab_usage_get_engagement_level(self):
        """Test determining engagement level"""
        # High engagement: long session with many actions
        high_engagement = LabUsageMetrics(
            student_id="student_123",
            course_id="course_456",
            lab_id="lab_001",
            session_start=datetime.utcnow() - timedelta(minutes=35),
            session_end=datetime.utcnow(),
            actions_performed=20
        )
        
        assert high_engagement.get_engagement_level() == "high"
        
        # Low engagement: short session with few actions
        low_engagement = LabUsageMetrics(
            student_id="student_123",
            course_id="course_456",
            lab_id="lab_001",
            session_start=datetime.utcnow() - timedelta(minutes=3),
            session_end=datetime.utcnow(),
            actions_performed=1
        )
        
        assert low_engagement.get_engagement_level() == "low"
    
    def test_lab_usage_end_session(self):
        """Test ending a lab session"""
        lab_metrics = LabUsageMetrics(
            student_id="student_123",
            course_id="course_456",
            lab_id="lab_001",
            session_start=datetime.utcnow() - timedelta(minutes=30),
            actions_performed=15,
            code_executions=5
        )
        
        final_code = "print('Hello, World!')"
        lab_metrics.end_session(final_code)
        
        assert lab_metrics.session_end is not None
        assert lab_metrics.final_code == final_code
        assert lab_metrics.completion_status == CompletionStatus.COMPLETED

class TestQuizPerformance:
    """Test quiz performance domain entity business logic"""
    
    def test_quiz_performance_creation_valid(self):
        """Test valid quiz performance creation"""
        performance = QuizPerformance(
            student_id="student_123",
            course_id="course_456",
            quiz_id="quiz_001",
            attempt_number=1,
            start_time=datetime.utcnow() - timedelta(minutes=15),
            questions_total=10,
            questions_answered=8,
            questions_correct=6
        )
        
        assert performance.student_id == "student_123"
        assert performance.quiz_id == "quiz_001"
        assert performance.attempt_number == 1
        assert performance.questions_total == 10
        assert performance.questions_answered == 8
        assert performance.questions_correct == 6
    
    def test_quiz_performance_validation_empty_fields(self):
        """Test quiz performance validation with empty required fields"""
        with pytest.raises(ValueError, match="Quiz ID is required"):
            QuizPerformance(
                student_id="student_123",
                course_id="course_456",
                quiz_id="",
                attempt_number=1,
                start_time=datetime.utcnow(),
                questions_total=10
            )
    
    def test_quiz_performance_validation_invalid_attempt_number(self):
        """Test quiz performance validation with invalid attempt number"""
        with pytest.raises(ValueError, match="Attempt number must be positive"):
            QuizPerformance(
                student_id="student_123",
                course_id="course_456",
                quiz_id="quiz_001",
                attempt_number=0,
                start_time=datetime.utcnow(),
                questions_total=10
            )
    
    def test_quiz_performance_validation_invalid_question_counts(self):
        """Test quiz performance validation with invalid question counts"""
        with pytest.raises(ValueError, match="Questions answered cannot exceed total questions"):
            QuizPerformance(
                student_id="student_123",
                course_id="course_456",
                quiz_id="quiz_001",
                attempt_number=1,
                start_time=datetime.utcnow(),
                questions_total=10,
                questions_answered=15  # More than total
            )
    
    def test_quiz_performance_get_score_percentage(self):
        """Test calculating score percentage"""
        performance = QuizPerformance(
            student_id="student_123",
            course_id="course_456",
            quiz_id="quiz_001",
            attempt_number=1,
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_answered=10,
            questions_correct=8
        )
        
        score_percentage = performance.get_score_percentage()
        assert score_percentage == 80.0
    
    def test_quiz_performance_get_score_percentage_zero_questions(self):
        """Test score percentage calculation with zero questions"""
        performance = QuizPerformance(
            student_id="student_123",
            course_id="course_456",
            quiz_id="quiz_001",
            attempt_number=1,
            start_time=datetime.utcnow(),
            questions_total=0  # Edge case
        )
        
        score_percentage = performance.get_score_percentage()
        assert score_percentage is None
    
    def test_quiz_performance_get_performance_level(self):
        """Test determining performance level"""
        # Excellent performance
        excellent_performance = QuizPerformance(
            student_id="student_123",
            course_id="course_456",
            quiz_id="quiz_001",
            attempt_number=1,
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_correct=9
        )
        
        assert excellent_performance.get_performance_level() == "excellent"
        
        # Poor performance
        poor_performance = QuizPerformance(
            student_id="student_123",
            course_id="course_456",
            quiz_id="quiz_001",
            attempt_number=1,
            start_time=datetime.utcnow(),
            questions_total=10,
            questions_correct=4
        )
        
        assert poor_performance.get_performance_level() == "poor"
    
    def test_quiz_performance_complete_quiz(self):
        """Test completing a quiz"""
        performance = QuizPerformance(
            student_id="student_123",
            course_id="course_456",
            quiz_id="quiz_001",
            attempt_number=1,
            start_time=datetime.utcnow() - timedelta(minutes=20),
            questions_total=10
        )
        
        performance.complete_quiz()
        
        assert performance.end_time is not None
        assert performance.status == CompletionStatus.COMPLETED
        assert performance.is_completed() == True

class TestStudentProgress:
    """Test student progress domain entity business logic"""
    
    def test_student_progress_creation_valid(self):
        """Test valid student progress creation"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_456",
            content_item_id="module_001",
            content_type=ContentType.MODULE,
            progress_percentage=65.0,
            time_spent_minutes=120
        )
        
        assert progress.student_id == "student_123"
        assert progress.course_id == "course_456"
        assert progress.content_item_id == "module_001"
        assert progress.content_type == ContentType.MODULE
        assert progress.progress_percentage == 65.0
        assert progress.time_spent_minutes == 120
    
    def test_student_progress_validation_empty_fields(self):
        """Test student progress validation with empty required fields"""
        with pytest.raises(ValueError, match="Content item ID is required"):
            StudentProgress(
                student_id="student_123",
                course_id="course_456",
                content_item_id="",
                content_type=ContentType.MODULE
            )
    
    def test_student_progress_validation_invalid_progress_percentage(self):
        """Test student progress validation with invalid progress percentage"""
        with pytest.raises(ValueError, match="Progress percentage must be between 0 and 100"):
            StudentProgress(
                student_id="student_123",
                course_id="course_456",
                content_item_id="module_001",
                content_type=ContentType.MODULE,
                progress_percentage=150.0  # Invalid
            )
    
    def test_student_progress_validation_negative_time(self):
        """Test student progress validation with negative time"""
        with pytest.raises(ValueError, match="Time spent cannot be negative"):
            StudentProgress(
                student_id="student_123",
                course_id="course_456",
                content_item_id="module_001",
                content_type=ContentType.MODULE,
                time_spent_minutes=-30
            )
    
    def test_student_progress_update_progress(self):
        """Test updating student progress"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_456",
            content_item_id="module_001",
            content_type=ContentType.MODULE,
            progress_percentage=30.0,
            time_spent_minutes=60
        )
        
        progress.update_progress(75.0, 45)
        
        assert progress.progress_percentage == 75.0
        assert progress.time_spent_minutes == 105  # 60 + 45
        assert progress.status == CompletionStatus.IN_PROGRESS
        assert isinstance(progress.last_accessed, datetime)
    
    def test_student_progress_update_progress_complete(self):
        """Test updating progress to completion"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_456",
            content_item_id="module_001",
            content_type=ContentType.MODULE,
            progress_percentage=80.0
        )
        
        progress.update_progress(100.0, 30)
        
        assert progress.progress_percentage == 100.0
        assert progress.status == CompletionStatus.COMPLETED
        assert progress.completion_date is not None
    
    def test_student_progress_mark_mastered(self):
        """Test marking content as mastered"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_456",
            content_item_id="module_001",
            content_type=ContentType.MODULE,
            progress_percentage=85.0
        )
        
        progress.mark_mastered(92.0)
        
        assert progress.status == CompletionStatus.MASTERED
        assert progress.mastery_score == 92.0
        assert progress.progress_percentage == 100.0
        assert progress.completion_date is not None
    
    def test_student_progress_get_learning_velocity(self):
        """Test calculating learning velocity"""
        progress = StudentProgress(
            student_id="student_123",
            course_id="course_456",
            content_item_id="module_001",
            content_type=ContentType.MODULE,
            progress_percentage=60.0
        )
        
        velocity = progress.get_learning_velocity(days_since_start=10)
        assert velocity == 6.0  # 60% over 10 days = 6% per day
    
    def test_student_progress_is_at_risk(self):
        """Test determining if student is at risk"""
        # Student who is behind and hasn't accessed recently
        at_risk_progress = StudentProgress(
            student_id="student_123",
            course_id="course_456",
            content_item_id="module_001",
            content_type=ContentType.MODULE,
            progress_percentage=20.0,  # Low progress
            last_accessed=datetime.utcnow() - timedelta(days=5)  # Haven't accessed recently
        )
        
        # Expected progress should be 70% after significant time
        is_at_risk = at_risk_progress.is_at_risk(expected_progress=70.0, days_since_start=14)
        assert is_at_risk == True
        
        # Student with good progress
        good_progress = StudentProgress(
            student_id="student_456",
            course_id="course_456",
            content_item_id="module_001",
            content_type=ContentType.MODULE,
            progress_percentage=80.0,
            last_accessed=datetime.utcnow() - timedelta(hours=2)
        )
        
        is_at_risk = good_progress.is_at_risk(expected_progress=70.0, days_since_start=14)
        assert is_at_risk == False

class TestLearningAnalytics:
    """Test learning analytics domain entity business logic"""
    
    def test_learning_analytics_creation_valid(self):
        """Test valid learning analytics creation"""
        analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=75.5,
            progress_velocity=2.3,
            lab_proficiency=68.0,
            quiz_performance=82.5,
            time_on_platform=450,
            streak_days=7
        )
        
        assert analytics.student_id == "student_123"
        assert analytics.course_id == "course_456"
        assert analytics.engagement_score == 75.5
        assert analytics.progress_velocity == 2.3
        assert analytics.lab_proficiency == 68.0
        assert analytics.quiz_performance == 82.5
        assert analytics.time_on_platform == 450
        assert analytics.streak_days == 7
        assert analytics.risk_level == RiskLevel.LOW
    
    def test_learning_analytics_validation_empty_fields(self):
        """Test learning analytics validation with empty required fields"""
        with pytest.raises(ValueError, match="Student ID is required"):
            LearningAnalytics(
                student_id="",
                course_id="course_456",
                engagement_score=75.0
            )
    
    def test_learning_analytics_validation_invalid_scores(self):
        """Test learning analytics validation with invalid scores"""
        with pytest.raises(ValueError, match="Engagement score must be between 0 and 100"):
            LearningAnalytics(
                student_id="student_123",
                course_id="course_456",
                engagement_score=150.0  # Invalid
            )
    
    def test_learning_analytics_validation_negative_values(self):
        """Test learning analytics validation with negative values"""
        with pytest.raises(ValueError, match="Progress velocity cannot be negative"):
            LearningAnalytics(
                student_id="student_123",
                course_id="course_456",
                progress_velocity=-1.5  # Invalid
            )
    
    def test_learning_analytics_calculate_overall_performance(self):
        """Test calculating overall performance score"""
        analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=80.0,
            progress_velocity=3.0,  # 3 items per week
            lab_proficiency=75.0,
            quiz_performance=85.0
        )
        
        overall_performance = analytics.calculate_overall_performance()
        assert isinstance(overall_performance, float)
        assert 0 <= overall_performance <= 100
        assert overall_performance > 70  # Should be good performance
    
    def test_learning_analytics_update_risk_level(self):
        """Test updating risk level based on metrics"""
        # High-performing student
        high_performer = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=90.0,
            progress_velocity=4.0,
            lab_proficiency=88.0,
            quiz_performance=92.0,
            streak_days=14
        )
        
        high_performer.update_risk_level()
        assert high_performer.risk_level == RiskLevel.LOW
        
        # Struggling student
        struggling_student = LearningAnalytics(
            student_id="student_456",
            course_id="course_456",
            engagement_score=25.0,  # Very low engagement
            progress_velocity=0.5,
            lab_proficiency=30.0,
            quiz_performance=45.0,
            streak_days=0,
            analysis_date=datetime.utcnow() - timedelta(days=10)  # Old analysis
        )
        
        struggling_student.update_risk_level()
        assert struggling_student.risk_level == RiskLevel.CRITICAL
    
    def test_learning_analytics_generate_recommendations(self):
        """Test generating personalized recommendations"""
        # Student with specific weaknesses
        analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=40.0,  # Low engagement
            progress_velocity=1.5,
            lab_proficiency=30.0,   # Low lab proficiency
            quiz_performance=55.0,  # Below average quiz performance
            time_on_platform=30,    # Very low time
            streak_days=0           # No streak
        )
        
        recommendations = analytics.generate_recommendations()
        
        assert len(recommendations) > 0
        assert any("engagement" in rec.lower() for rec in recommendations)
        assert any("lab" in rec.lower() or "coding" in rec.lower() for rec in recommendations)
        assert any("quiz" in rec.lower() for rec in recommendations)
        assert any("routine" in rec.lower() or "streak" in rec.lower() for rec in recommendations)
    
    def test_learning_analytics_generate_recommendations_high_performer(self):
        """Test recommendations for high-performing student"""
        high_performer = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=95.0,
            progress_velocity=4.5,
            lab_proficiency=92.0,
            quiz_performance=88.0,
            time_on_platform=300,
            streak_days=12
        )
        
        recommendations = high_performer.generate_recommendations()
        
        # High performers should have fewer or no recommendations
        assert len(recommendations) == 0 or all("continue" in rec.lower() or "maintain" in rec.lower() for rec in recommendations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])