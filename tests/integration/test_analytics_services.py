"""
Integration Tests for Analytics Services
Testing analytics service integration and dependency injection following SOLID principles
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from omegaconf import DictConfig

from services.analytics.infrastructure.container import AnalyticsContainer
from services.analytics.domain.entities.student_analytics import (
    StudentActivity, LabUsageMetrics, QuizPerformance, 
    StudentProgress, LearningAnalytics,
    ActivityType, CompletionStatus, RiskLevel, ContentType
)
from services.analytics.application.services.student_activity_service import StudentActivityService
from services.analytics.application.services.learning_analytics_service import LearningAnalyticsService

class TestStudentActivityServiceIntegration:
    """Test student activity service integration with dependencies"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'},
            'server': {'host': '0.0.0.0', 'port': 8007}
        })
    
    @pytest.fixture
    def mock_container(self, mock_config):
        """Create container with mocked dependencies"""
        container = AnalyticsContainer(mock_config)
        
        # Mock the repositories
        container._student_activity_repository = AsyncMock()
        
        return container
    
    @pytest.fixture
    def activity_service(self, mock_container):
        """Create activity service with mocked dependencies"""
        return mock_container.get_student_activity_service()
    
    @pytest.mark.asyncio
    async def test_record_activity_integration(self, activity_service, mock_container):
        """Test complete activity recording workflow"""
        # Create activity
        activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.LAB_ACCESS,
            activity_data={"lab_id": "lab_001", "action": "start_session"}
        )
        
        # Mock repository behavior
        mock_container._student_activity_repository.create.return_value = activity
        mock_container._student_activity_repository.get_by_student_and_course.return_value = []
        
        # Execute service method
        result = await activity_service.record_activity(activity)
        
        # Verify results
        assert result.student_id == "student_123"
        assert result.course_id == "course_456"
        assert result.activity_type == ActivityType.LAB_ACCESS
        
        # Verify repository was called
        mock_container._student_activity_repository.create.assert_called_once_with(activity)
    
    @pytest.mark.asyncio
    async def test_record_activity_validation_failure(self, activity_service, mock_container):
        """Test activity recording with validation failure"""
        # Create invalid activity (empty student_id)
        activity = StudentActivity(
            student_id="",  # Invalid
            course_id="course_456",
            activity_type=ActivityType.LOGIN
        )
        
        # Should raise ValueError before reaching repository
        with pytest.raises(ValueError, match="Student ID is required"):
            await activity_service.record_activity(activity)
        
        # Repository should not be called
        mock_container._student_activity_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_engagement_score_integration(self, activity_service, mock_container):
        """Test engagement score calculation workflow"""
        # Create mock activities
        activities = [
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.LAB_ACCESS,
                timestamp=datetime.utcnow() - timedelta(days=1)
            ),
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.QUIZ_COMPLETE,
                timestamp=datetime.utcnow() - timedelta(days=2),
                activity_data={"quiz_id": "quiz_001", "score": 85}
            ),
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.CODE_EXECUTION,
                timestamp=datetime.utcnow() - timedelta(days=3)
            )
        ]
        
        # Mock repository response
        mock_container._student_activity_repository.get_by_student_and_course.return_value = activities
        
        # Execute service method
        engagement_score = await activity_service.get_engagement_score(
            student_id="student_123",
            course_id="course_456",
            days_back=30
        )
        
        # Verify results
        assert isinstance(engagement_score, float)
        assert 0 <= engagement_score <= 100
        assert engagement_score > 0  # Should have some engagement based on activities
        
        # Verify repository was called with correct parameters
        mock_container._student_activity_repository.get_by_student_and_course.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_learning_patterns_integration(self, activity_service, mock_container):
        """Test learning pattern detection workflow"""
        # Create diverse activities across different times and days
        base_time = datetime.utcnow()
        activities = [
            # Monday activities
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.LOGIN,
                timestamp=base_time - timedelta(days=6, hours=9)  # Monday 9 AM
            ),
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.LAB_ACCESS,
                timestamp=base_time - timedelta(days=6, hours=9, minutes=5)
            ),
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.CODE_EXECUTION,
                timestamp=base_time - timedelta(days=6, hours=9, minutes=30)
            ),
            # Tuesday activities
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.LOGIN,
                timestamp=base_time - timedelta(days=5, hours=14)  # Tuesday 2 PM
            ),
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.QUIZ_START,
                timestamp=base_time - timedelta(days=5, hours=14, minutes=10)
            ),
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.QUIZ_COMPLETE,
                timestamp=base_time - timedelta(days=5, hours=14, minutes=25)
            )
        ]
        
        # Mock repository response
        mock_container._student_activity_repository.get_by_student_and_course.return_value = activities
        
        # Execute service method
        patterns = await activity_service.detect_learning_patterns(
            student_id="student_123",
            course_id="course_456"
        )
        
        # Verify results structure
        assert "patterns" in patterns
        assert "insights" in patterns
        assert "analysis_date" in patterns
        assert "total_activities" in patterns
        
        # Verify pattern analysis
        temporal_patterns = patterns["patterns"].get("temporal", {})
        assert "day_distribution" in temporal_patterns
        assert "hour_distribution" in temporal_patterns
        assert "most_active_day" in temporal_patterns
        
        sequence_patterns = patterns["patterns"].get("sequences", {})
        assert "common_sequences" in sequence_patterns
        
        # Verify insights are generated
        assert isinstance(patterns["insights"], list)
        assert patterns["total_activities"] == len(activities)

class TestLearningAnalyticsServiceIntegration:
    """Test learning analytics service integration with multiple dependencies"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.fixture
    def mock_container(self, mock_config):
        """Create container with mocked dependencies"""
        container = AnalyticsContainer(mock_config)
        
        # Mock all repositories
        container._learning_analytics_repository = AsyncMock()
        container._student_activity_repository = AsyncMock()
        
        # Mock all services
        container._student_activity_service = AsyncMock()
        container._lab_analytics_service = AsyncMock()
        container._quiz_analytics_service = AsyncMock()
        container._progress_tracking_service = AsyncMock()
        
        return container
    
    @pytest.fixture
    def analytics_service(self, mock_container):
        """Create learning analytics service with mocked dependencies"""
        return mock_container.get_learning_analytics_service()
    
    @pytest.mark.asyncio
    async def test_generate_student_analytics_integration(self, analytics_service, mock_container):
        """Test complete student analytics generation workflow"""
        # Setup mock responses from dependent services
        mock_container._student_activity_service.get_engagement_score.return_value = 75.5
        mock_container._lab_analytics_service.get_lab_proficiency_score.return_value = 68.0
        mock_container._quiz_analytics_service.get_student_quiz_history.return_value = [
            QuizPerformance(
                student_id="student_123",
                course_id="course_456",
                quiz_id="quiz_001",
                attempt_number=1,
                start_time=datetime.utcnow() - timedelta(hours=2),
                end_time=datetime.utcnow() - timedelta(hours=1, minutes=45),
                questions_total=10,
                questions_answered=10,
                questions_correct=8,
                status=CompletionStatus.COMPLETED
            )
        ]
        mock_container._progress_tracking_service.get_progress_summary.return_value = {
            'completion_rate': 0.6,
            'time_in_course_days': 30,
            'items_completed': 15,
            'total_time_spent_minutes': 450
        }
        mock_container._student_activity_service.get_student_activities.return_value = [
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.LAB_ACCESS,
                timestamp=datetime.utcnow() - timedelta(days=1)
            )
        ]
        
        # Create expected analytics result
        expected_analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=75.5,
            progress_velocity=2.5,
            lab_proficiency=68.0,
            quiz_performance=80.0,
            time_on_platform=450,
            streak_days=1
        )
        mock_container._learning_analytics_repository.create.return_value = expected_analytics
        
        # Execute service method
        result = await analytics_service.generate_student_analytics(
            student_id="student_123",
            course_id="course_456"
        )
        
        # Verify results
        assert result.student_id == "student_123"
        assert result.course_id == "course_456"
        assert result.engagement_score == 75.5
        assert result.lab_proficiency == 68.0
        assert isinstance(result.risk_level, RiskLevel)
        assert isinstance(result.recommendations, list)
        
        # Verify all dependent services were called
        mock_container._student_activity_service.get_engagement_score.assert_called_once()
        mock_container._lab_analytics_service.get_lab_proficiency_score.assert_called_once()
        mock_container._quiz_analytics_service.get_student_quiz_history.assert_called_once()
        mock_container._progress_tracking_service.get_progress_summary.assert_called_once()
        mock_container._learning_analytics_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_analytics_with_partial_failures(self, analytics_service, mock_container):
        """Test analytics generation with partial service failures"""
        # Setup some services to succeed and others to fail
        mock_container._student_activity_service.get_engagement_score.return_value = 70.0
        mock_container._lab_analytics_service.get_lab_proficiency_score.side_effect = Exception("Lab service error")
        mock_container._quiz_analytics_service.get_student_quiz_history.return_value = []
        mock_container._progress_tracking_service.get_progress_summary.side_effect = Exception("Progress service error")
        mock_container._student_activity_service.get_student_activities.return_value = []
        
        # Should use fallback data gathering
        expected_analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=70.0,
            progress_velocity=0.0,
            lab_proficiency=0.0,  # Fallback value
            quiz_performance=0.0,
            time_on_platform=0,
            streak_days=0
        )
        mock_container._learning_analytics_repository.create.return_value = expected_analytics
        
        # Execute service method - should not raise exception
        result = await analytics_service.generate_student_analytics(
            student_id="student_123",
            course_id="course_456"
        )
        
        # Verify graceful degradation
        assert result.student_id == "student_123"
        assert result.engagement_score == 70.0
        assert result.lab_proficiency == 0.0  # Fallback value used
        
        # Repository should still be called
        mock_container._learning_analytics_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_course_analytics_summary_integration(self, analytics_service, mock_container):
        """Test course analytics summary generation"""
        # Create mock analytics for multiple students
        course_analytics = [
            LearningAnalytics(
                student_id="student_1",
                course_id="course_456",
                engagement_score=85.0,
                progress_velocity=3.0,
                lab_proficiency=80.0,
                quiz_performance=88.0,
                time_on_platform=300,
                streak_days=5,
                risk_level=RiskLevel.LOW
            ),
            LearningAnalytics(
                student_id="student_2",
                course_id="course_456",
                engagement_score=60.0,
                progress_velocity=1.5,
                lab_proficiency=55.0,
                quiz_performance=65.0,
                time_on_platform=180,
                streak_days=2,
                risk_level=RiskLevel.MEDIUM
            ),
            LearningAnalytics(
                student_id="student_3",
                course_id="course_456",
                engagement_score=30.0,
                progress_velocity=0.8,
                lab_proficiency=25.0,
                quiz_performance=40.0,
                time_on_platform=90,
                streak_days=0,
                risk_level=RiskLevel.HIGH
            )
        ]
        
        # Mock repository response
        mock_container._learning_analytics_repository.get_by_course.return_value = course_analytics
        
        # Execute service method
        summary = await analytics_service.get_course_analytics_summary("course_456")
        
        # Verify summary structure
        assert summary["total_students"] == 3
        assert "averages" in summary
        assert "risk_distribution" in summary
        assert "high_performers" in summary
        assert "at_risk_students" in summary
        
        # Verify calculated averages
        averages = summary["averages"]
        assert averages["engagement_score"] == 58.33  # (85+60+30)/3
        assert averages["lab_proficiency"] == 53.33   # (80+55+25)/3
        
        # Verify risk distribution
        risk_dist = summary["risk_distribution"]
        assert risk_dist[RiskLevel.LOW.value] == 1
        assert risk_dist[RiskLevel.MEDIUM.value] == 1
        assert risk_dist[RiskLevel.HIGH.value] == 1
        
        # Verify high performers and at-risk students
        assert len(summary["high_performers"]) > 0
        assert len(summary["at_risk_students"]) > 0
    
    @pytest.mark.asyncio
    async def test_compare_student_performance_integration(self, analytics_service, mock_container):
        """Test student performance comparison workflow"""
        # Setup student analytics
        student_analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=85.0,
            progress_velocity=3.2,
            lab_proficiency=78.0,
            quiz_performance=82.0,
            time_on_platform=360,
            streak_days=8
        )
        mock_container._learning_analytics_repository.get_by_student_and_course.return_value = student_analytics
        
        # Mock course summary
        course_summary = {
            "total_students": 50,
            "averages": {
                "engagement_score": 70.0,
                "progress_velocity": 2.5,
                "lab_proficiency": 65.0,
                "quiz_performance": 75.0,
                "time_on_platform": 240,
                "streak_days": 4,
                "overall_performance": 68.0
            }
        }
        mock_container._learning_analytics_repository.get_by_course.return_value = []  # Will use mock summary
        
        # Mock the get_course_analytics_summary method
        analytics_service.get_course_analytics_summary = AsyncMock(return_value=course_summary)
        
        # Execute service method
        comparison = await analytics_service.compare_student_performance(
            student_id="student_123",
            course_id="course_456"
        )
        
        # Verify comparison structure
        assert comparison["student_id"] == "student_123"
        assert comparison["course_id"] == "course_456"
        assert "overall_standing" in comparison
        assert "detailed_comparisons" in comparison
        assert "percentile_estimate" in comparison
        
        # Verify performance comparisons
        detailed_comparisons = comparison["detailed_comparisons"]
        assert "engagement_score" in detailed_comparisons
        assert "quiz_performance" in detailed_comparisons
        
        # Student should be above average in most metrics
        engagement_comparison = detailed_comparisons["engagement_score"]
        assert engagement_comparison["status"] == "above_average"
        assert engagement_comparison["percentage_difference"] > 0

class TestAnalyticsContainerIntegration:
    """Test analytics dependency injection container integration"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.mark.asyncio
    async def test_container_initialization(self, mock_config):
        """Test container initialization and cleanup"""
        container = AnalyticsContainer(mock_config)
        
        # Mock the database connection
        container._connection_pool = AsyncMock()
        
        await container.initialize()
        assert container._connection_pool is not None
        
        await container.cleanup()
    
    def test_container_service_creation(self, mock_config):
        """Test container creates services correctly"""
        container = AnalyticsContainer(mock_config)
        
        # Test service creation
        activity_service = container.get_student_activity_service()
        assert isinstance(activity_service, StudentActivityService)
        
        analytics_service = container.get_learning_analytics_service()
        assert isinstance(analytics_service, LearningAnalyticsService)
        
        # Test singleton behavior
        activity_service2 = container.get_student_activity_service()
        assert activity_service is activity_service2
    
    def test_container_repository_creation(self, mock_config):
        """Test container creates repositories correctly"""
        container = AnalyticsContainer(mock_config)
        
        # Test repository creation
        activity_repo = container.get_student_activity_repository()
        assert activity_repo is not None
        
        analytics_repo = container.get_learning_analytics_repository()
        assert analytics_repo is not None
        
        # Test singleton behavior
        activity_repo2 = container.get_student_activity_repository()
        assert activity_repo is activity_repo2

class TestCrossServiceAnalyticsIntegration:
    """Test integration between different analytics services"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return DictConfig({
            'database': {'url': 'postgresql://test:test@localhost:5432/test'},
            'logging': {'level': 'INFO'}
        })
    
    @pytest.fixture
    def container_with_mocks(self, mock_config):
        """Create container with mocked external dependencies"""
        container = AnalyticsContainer(mock_config)
        
        # Mock all repositories
        container._student_activity_repository = AsyncMock()
        container._learning_analytics_repository = AsyncMock()
        container._lab_usage_repository = AsyncMock()
        container._quiz_performance_repository = AsyncMock()
        container._student_progress_repository = AsyncMock()
        
        return container
    
    @pytest.mark.asyncio
    async def test_activity_to_analytics_workflow(self, container_with_mocks):
        """Test workflow from activity recording to analytics generation"""
        # Step 1: Record student activities
        activity_service = container_with_mocks.get_student_activity_service()
        
        activities = [
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.LAB_ACCESS,
                activity_data={"lab_id": "lab_001"}
            ),
            StudentActivity(
                student_id="student_123",
                course_id="course_456",
                activity_type=ActivityType.QUIZ_COMPLETE,
                activity_data={"quiz_id": "quiz_001", "score": 85}
            )
        ]
        
        # Mock activity recording
        for activity in activities:
            container_with_mocks._student_activity_repository.create.return_value = activity
            container_with_mocks._student_activity_repository.get_by_student_and_course.return_value = []
            
            await activity_service.record_activity(activity)
        
        # Step 2: Generate analytics based on activities
        analytics_service = container_with_mocks.get_learning_analytics_service()
        
        # Mock the data gathering for analytics
        container_with_mocks._student_activity_repository.get_by_student_and_course.return_value = activities
        
        # Mock other service responses
        analytics_service._activity_service.get_engagement_score = AsyncMock(return_value=80.0)
        analytics_service._lab_service.get_lab_proficiency_score = AsyncMock(return_value=75.0)
        analytics_service._quiz_service.get_student_quiz_history = AsyncMock(return_value=[])
        analytics_service._progress_service.get_progress_summary = AsyncMock(return_value={
            'completion_rate': 0.7,
            'time_in_course_days': 15,
            'items_completed': 12,
            'total_time_spent_minutes': 300
        })
        
        # Create expected analytics
        expected_analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=80.0,
            progress_velocity=3.36,  # 12 items / (15/7) weeks
            lab_proficiency=75.0,
            quiz_performance=0.0,
            time_on_platform=300,
            streak_days=0
        )
        container_with_mocks._learning_analytics_repository.create.return_value = expected_analytics
        
        analytics = await analytics_service.generate_student_analytics(
            student_id="student_123",
            course_id="course_456"
        )
        
        # Verify the workflow worked
        assert analytics.student_id == "student_123"
        assert analytics.course_id == "course_456"
        assert analytics.engagement_score == 80.0
        
        # Both repositories should have been used
        container_with_mocks._student_activity_repository.create.assert_called()
        container_with_mocks._learning_analytics_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_real_time_analytics_update_workflow(self, container_with_mocks):
        """Test real-time analytics update when new activities are recorded"""
        activity_service = container_with_mocks.get_student_activity_service()
        analytics_service = container_with_mocks.get_learning_analytics_service()
        
        # Step 1: Existing analytics
        existing_analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=70.0,
            progress_velocity=2.0,
            lab_proficiency=60.0,
            quiz_performance=75.0,
            time_on_platform=200,
            streak_days=3
        )
        container_with_mocks._learning_analytics_repository.get_by_student_and_course.return_value = existing_analytics
        
        # Step 2: Record new high-engagement activity
        new_activity = StudentActivity(
            student_id="student_123",
            course_id="course_456",
            activity_type=ActivityType.EXERCISE_SUBMISSION,
            activity_data={"exercise_id": "ex_001", "success": True}
        )
        
        container_with_mocks._student_activity_repository.create.return_value = new_activity
        container_with_mocks._student_activity_repository.get_by_student_and_course.return_value = []
        
        await activity_service.record_activity(new_activity)
        
        # Step 3: Update analytics based on new activity
        updated_analytics = LearningAnalytics(
            student_id="student_123",
            course_id="course_456",
            engagement_score=85.0,  # Increased due to new activity
            progress_velocity=2.2,
            lab_proficiency=60.0,
            quiz_performance=75.0,
            time_on_platform=220,
            streak_days=4  # Increased streak
        )
        
        # Mock analytics update
        analytics_service._activity_service.get_engagement_score = AsyncMock(return_value=85.0)
        analytics_service._lab_service.get_lab_proficiency_score = AsyncMock(return_value=60.0)
        analytics_service._quiz_service.get_student_quiz_history = AsyncMock(return_value=[])
        analytics_service._progress_service.get_progress_summary = AsyncMock(return_value={
            'completion_rate': 0.75,
            'time_in_course_days': 20,
            'items_completed': 15,
            'total_time_spent_minutes': 220
        })
        
        updated_analytics.id = existing_analytics.id
        container_with_mocks._learning_analytics_repository.update.return_value = updated_analytics
        
        result = await analytics_service.update_analytics(existing_analytics.id)
        
        # Verify analytics were updated
        assert result.engagement_score == 85.0
        assert result.streak_days == 4
        
        # Verify both services were involved
        container_with_mocks._student_activity_repository.create.assert_called_once()
        container_with_mocks._learning_analytics_repository.update.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])