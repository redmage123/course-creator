"""
Analytics Repository Interfaces
Single Responsibility: Define data access contracts for analytics entities
Dependency Inversion: Abstract interfaces for data persistence
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from ..entities.student_analytics import (
    StudentActivity, LabUsageMetrics, QuizPerformance, 
    StudentProgress, LearningAnalytics, ActivityType, ContentType, RiskLevel
)

class IStudentActivityRepository(ABC):
    """Interface for student activity data access operations"""
    
    @abstractmethod
    async def create(self, activity: StudentActivity) -> StudentActivity:
        """Create a new student activity record"""
        pass
    
    @abstractmethod
    async def get_by_id(self, activity_id: str) -> Optional[StudentActivity]:
        """Get activity by ID"""
        pass
    
    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, course_id: str,
                                       start_date: Optional[datetime] = None,
                                       end_date: Optional[datetime] = None,
                                       activity_types: Optional[List[ActivityType]] = None,
                                       limit: int = 100) -> List[StudentActivity]:
        """Get activities for a student in a course with filtering"""
        pass
    
    @abstractmethod
    async def get_by_course(self, course_id: str,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: int = 1000) -> List[StudentActivity]:
        """Get all activities for a course"""
        pass
    
    @abstractmethod
    async def get_by_session(self, session_id: str) -> List[StudentActivity]:
        """Get all activities for a session"""
        pass
    
    @abstractmethod
    async def get_activity_counts(self, course_id: str,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, int]:
        """Get activity counts by type"""
        pass
    
    @abstractmethod
    async def get_engagement_metrics(self, student_id: str, course_id: str,
                                   days_back: int = 30) -> Dict[str, Any]:
        """Get engagement metrics for a student"""
        pass
    
    @abstractmethod
    async def delete_old_activities(self, days_old: int = 90) -> int:
        """Delete old activity records"""
        pass

class ILabUsageRepository(ABC):
    """Interface for lab usage metrics data access operations"""
    
    @abstractmethod
    async def create(self, lab_metrics: LabUsageMetrics) -> LabUsageMetrics:
        """Create a new lab usage record"""
        pass
    
    @abstractmethod
    async def get_by_id(self, metrics_id: str) -> Optional[LabUsageMetrics]:
        """Get lab metrics by ID"""
        pass
    
    @abstractmethod
    async def update(self, lab_metrics: LabUsageMetrics) -> LabUsageMetrics:
        """Update lab usage metrics"""
        pass
    
    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, 
                                       course_id: str) -> List[LabUsageMetrics]:
        """Get lab usage for a student in a course"""
        pass
    
    @abstractmethod
    async def get_by_lab_id(self, lab_id: str) -> List[LabUsageMetrics]:
        """Get all usage metrics for a specific lab"""
        pass
    
    @abstractmethod
    async def get_active_sessions(self, course_id: str) -> List[LabUsageMetrics]:
        """Get currently active lab sessions"""
        pass
    
    @abstractmethod
    async def get_completion_rates(self, course_id: str) -> Dict[str, float]:
        """Get lab completion rates by lab ID"""
        pass
    
    @abstractmethod
    async def get_proficiency_scores(self, student_id: str, 
                                   course_id: str) -> List[Dict[str, Any]]:
        """Get lab proficiency scores for a student"""
        pass
    
    @abstractmethod
    async def get_usage_trends(self, course_id: str, 
                             days_back: int = 30) -> Dict[str, Any]:
        """Get lab usage trend data"""
        pass

class IQuizPerformanceRepository(ABC):
    """Interface for quiz performance data access operations"""
    
    @abstractmethod
    async def create(self, performance: QuizPerformance) -> QuizPerformance:
        """Create a new quiz performance record"""
        pass
    
    @abstractmethod
    async def get_by_id(self, performance_id: str) -> Optional[QuizPerformance]:
        """Get quiz performance by ID"""
        pass
    
    @abstractmethod
    async def update(self, performance: QuizPerformance) -> QuizPerformance:
        """Update quiz performance record"""
        pass
    
    @abstractmethod
    async def get_by_student_and_quiz(self, student_id: str, 
                                    quiz_id: str) -> List[QuizPerformance]:
        """Get all attempts by a student for a specific quiz"""
        pass
    
    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, 
                                      course_id: str) -> List[QuizPerformance]:
        """Get all quiz performances for a student in a course"""
        pass
    
    @abstractmethod
    async def get_by_quiz_id(self, quiz_id: str) -> List[QuizPerformance]:
        """Get all performances for a specific quiz"""
        pass
    
    @abstractmethod
    async def get_quiz_statistics(self, quiz_id: str) -> Dict[str, Any]:
        """Get comprehensive quiz statistics"""
        pass
    
    @abstractmethod
    async def get_question_analytics(self, quiz_id: str) -> List[Dict[str, Any]]:
        """Get analytics for individual questions"""
        pass
    
    @abstractmethod
    async def get_performance_trends(self, student_id: str, 
                                   course_id: str) -> List[Dict[str, Any]]:
        """Get performance trend data for a student"""
        pass

class IStudentProgressRepository(ABC):
    """Interface for student progress data access operations"""
    
    @abstractmethod
    async def create(self, progress: StudentProgress) -> StudentProgress:
        """Create a new progress record"""
        pass
    
    @abstractmethod
    async def get_by_id(self, progress_id: str) -> Optional[StudentProgress]:
        """Get progress by ID"""
        pass
    
    @abstractmethod
    async def update(self, progress: StudentProgress) -> StudentProgress:
        """Update progress record"""
        pass
    
    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, 
                                       course_id: str) -> List[StudentProgress]:
        """Get all progress for a student in a course"""
        pass
    
    @abstractmethod
    async def get_by_content_item(self, content_item_id: str) -> List[StudentProgress]:
        """Get all progress records for a content item"""
        pass
    
    @abstractmethod
    async def get_course_completion_rates(self, course_id: str) -> Dict[str, float]:
        """Get completion rates by content type"""
        pass
    
    @abstractmethod
    async def get_at_risk_students(self, course_id: str, 
                                 risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Get students at risk of not completing"""
        pass
    
    @abstractmethod
    async def get_learning_velocity(self, student_id: str, course_id: str, 
                                  days_back: int = 30) -> float:
        """Calculate learning velocity for a student"""
        pass
    
    @abstractmethod
    async def get_progress_summary(self, student_id: str, 
                                 course_id: str) -> Dict[str, Any]:
        """Get summarized progress information"""
        pass

class ILearningAnalyticsRepository(ABC):
    """Interface for learning analytics data access operations"""
    
    @abstractmethod
    async def create(self, analytics: LearningAnalytics) -> LearningAnalytics:
        """Create a new analytics record"""
        pass
    
    @abstractmethod
    async def get_by_id(self, analytics_id: str) -> Optional[LearningAnalytics]:
        """Get analytics by ID"""
        pass
    
    @abstractmethod
    async def update(self, analytics: LearningAnalytics) -> LearningAnalytics:
        """Update analytics record"""
        pass
    
    @abstractmethod
    async def get_by_student_and_course(self, student_id: str, 
                                       course_id: str) -> Optional[LearningAnalytics]:
        """Get latest analytics for a student in a course"""
        pass
    
    @abstractmethod
    async def get_by_course(self, course_id: str) -> List[LearningAnalytics]:
        """Get analytics for all students in a course"""
        pass
    
    @abstractmethod
    async def get_by_risk_level(self, course_id: str, 
                              risk_level: RiskLevel) -> List[LearningAnalytics]:
        """Get students by risk level"""
        pass
    
    @abstractmethod
    async def get_course_summary(self, course_id: str) -> Dict[str, Any]:
        """Get aggregated analytics summary for a course"""
        pass
    
    @abstractmethod
    async def get_historical_analytics(self, student_id: str, course_id: str,
                                     days_back: int = 90) -> List[LearningAnalytics]:
        """Get historical analytics for trend analysis"""
        pass
    
    @abstractmethod
    async def cleanup_old_analytics(self, days_old: int = 180) -> int:
        """Clean up old analytics records"""
        pass

class IAnalyticsAggregationRepository(ABC):
    """Interface for analytics aggregation and reporting queries"""
    
    @abstractmethod
    async def get_engagement_trends(self, course_id: str, 
                                  days_back: int = 30,
                                  granularity: str = "daily") -> List[Dict[str, Any]]:
        """Get engagement trends over time"""
        pass
    
    @abstractmethod
    async def get_performance_distributions(self, course_id: str) -> Dict[str, Any]:
        """Get performance distribution statistics"""
        pass
    
    @abstractmethod
    async def get_cohort_comparisons(self, course_ids: List[str]) -> Dict[str, Any]:
        """Compare performance across course cohorts"""
        pass
    
    @abstractmethod
    async def get_content_effectiveness(self, course_id: str) -> List[Dict[str, Any]]:
        """Analyze effectiveness of different content types"""
        pass
    
    @abstractmethod
    async def get_time_to_completion(self, course_id: str, 
                                   content_type: Optional[ContentType] = None) -> Dict[str, Any]:
        """Get time to completion statistics"""
        pass
    
    @abstractmethod
    async def get_learning_path_analysis(self, course_id: str) -> Dict[str, Any]:
        """Analyze common learning paths and outcomes"""
        pass
    
    @abstractmethod
    async def get_intervention_effectiveness(self, course_id: str) -> Dict[str, Any]:
        """Analyze effectiveness of different interventions"""
        pass
    
    @abstractmethod
    async def generate_predictive_features(self, student_id: str, 
                                         course_id: str) -> Dict[str, float]:
        """Generate features for predictive modeling"""
        pass

class IReportingRepository(ABC):
    """Interface for report generation and data export"""
    
    @abstractmethod
    async def generate_student_report_data(self, student_id: str, 
                                         course_id: str) -> Dict[str, Any]:
        """Generate comprehensive student report data"""
        pass
    
    @abstractmethod
    async def generate_course_report_data(self, course_id: str) -> Dict[str, Any]:
        """Generate course-wide report data"""
        pass
    
    @abstractmethod
    async def generate_instructor_dashboard_data(self, instructor_id: str,
                                               course_ids: List[str]) -> Dict[str, Any]:
        """Generate instructor dashboard data"""
        pass
    
    @abstractmethod
    async def export_raw_data(self, course_id: str, 
                            data_types: List[str],
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, List[Dict]]:
        """Export raw analytics data"""
        pass
    
    @abstractmethod
    async def get_visualization_data(self, course_id: str, 
                                   chart_types: List[str]) -> Dict[str, Any]:
        """Get data formatted for visualizations"""
        pass
    
    @abstractmethod
    async def get_benchmark_data(self, course_id: str) -> Dict[str, Any]:
        """Get benchmark comparison data"""
        pass