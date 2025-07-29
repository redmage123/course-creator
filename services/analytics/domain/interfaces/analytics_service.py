"""
Analytics Service Interfaces
Single Responsibility: Define service contracts for analytics operations
Interface Segregation: Focused interfaces for specific analytics concerns
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from ..entities.student_analytics import (
    StudentActivity, LabUsageMetrics, QuizPerformance, 
    StudentProgress, LearningAnalytics, RiskLevel, ActivityType, ContentType
)

class IStudentActivityService(ABC):
    """Interface for student activity tracking and analysis"""
    
    @abstractmethod
    async def record_activity(self, activity: StudentActivity) -> StudentActivity:
        """Record a new student activity"""
        pass
    
    @abstractmethod
    async def get_student_activities(self, student_id: str, course_id: str, 
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None,
                                   activity_types: Optional[List[ActivityType]] = None) -> List[StudentActivity]:
        """Get student activities with filtering"""
        pass
    
    @abstractmethod
    async def get_engagement_score(self, student_id: str, course_id: str, 
                                 days_back: int = 30) -> float:
        """Calculate student engagement score"""
        pass
    
    @abstractmethod
    async def get_activity_summary(self, course_id: str, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get activity summary for a course"""
        pass
    
    @abstractmethod
    async def detect_learning_patterns(self, student_id: str, 
                                     course_id: str) -> Dict[str, Any]:
        """Detect learning patterns from student activities"""
        pass

class ILabAnalyticsService(ABC):
    """Interface for lab usage analytics"""
    
    @abstractmethod
    async def record_lab_session(self, lab_metrics: LabUsageMetrics) -> LabUsageMetrics:
        """Record lab usage metrics"""
        pass
    
    @abstractmethod
    async def update_lab_session(self, session_id: str, 
                               updates: Dict[str, Any]) -> Optional[LabUsageMetrics]:
        """Update lab session metrics"""
        pass
    
    @abstractmethod
    async def get_lab_proficiency_score(self, student_id: str, 
                                      course_id: str) -> float:
        """Calculate lab proficiency score"""
        pass
    
    @abstractmethod
    async def get_lab_usage_trends(self, course_id: str, 
                                 days_back: int = 30) -> Dict[str, Any]:
        """Get lab usage trends for a course"""
        pass
    
    @abstractmethod
    async def identify_struggling_students(self, course_id: str, 
                                         threshold_score: float = 60.0) -> List[Dict[str, Any]]:
        """Identify students struggling with lab work"""
        pass
    
    @abstractmethod
    async def get_lab_completion_rates(self, course_id: str) -> Dict[str, float]:
        """Get lab completion rates by lab ID"""
        pass

class IQuizAnalyticsService(ABC):
    """Interface for quiz performance analytics"""
    
    @abstractmethod
    async def record_quiz_performance(self, performance: QuizPerformance) -> QuizPerformance:
        """Record quiz performance data"""
        pass
    
    @abstractmethod
    async def get_quiz_statistics(self, quiz_id: str) -> Dict[str, Any]:
        """Get comprehensive quiz statistics"""
        pass
    
    @abstractmethod
    async def get_student_quiz_history(self, student_id: str, 
                                     course_id: str) -> List[QuizPerformance]:
        """Get student's quiz performance history"""
        pass
    
    @abstractmethod
    async def calculate_quiz_difficulty(self, quiz_id: str) -> float:
        """Calculate quiz difficulty based on student performance"""
        pass
    
    @abstractmethod
    async def get_question_analysis(self, quiz_id: str) -> List[Dict[str, Any]]:
        """Analyze individual question performance"""
        pass
    
    @abstractmethod
    async def get_performance_trends(self, student_id: str, 
                                   course_id: str) -> Dict[str, Any]:
        """Get quiz performance trends for a student"""
        pass

class IProgressTrackingService(ABC):
    """Interface for student progress tracking"""
    
    @abstractmethod
    async def update_progress(self, progress: StudentProgress) -> StudentProgress:
        """Update student progress on content item"""
        pass
    
    @abstractmethod
    async def get_course_progress(self, student_id: str, 
                                course_id: str) -> List[StudentProgress]:
        """Get student's progress across all course content"""
        pass
    
    @abstractmethod
    async def get_progress_summary(self, student_id: str, 
                                 course_id: str) -> Dict[str, Any]:
        """Get summarized progress information"""
        pass
    
    @abstractmethod
    async def calculate_completion_rate(self, student_id: str, 
                                      course_id: str) -> float:
        """Calculate overall course completion rate"""
        pass
    
    @abstractmethod
    async def get_learning_velocity(self, student_id: str, 
                                  course_id: str, days_back: int = 30) -> float:
        """Calculate learning velocity (progress per day)"""
        pass
    
    @abstractmethod
    async def identify_at_risk_students(self, course_id: str) -> List[Dict[str, Any]]:
        """Identify students at risk of not completing"""
        pass

class ILearningAnalyticsService(ABC):
    """Interface for comprehensive learning analytics"""
    
    @abstractmethod
    async def generate_student_analytics(self, student_id: str, 
                                       course_id: str) -> LearningAnalytics:
        """Generate comprehensive analytics for a student"""
        pass
    
    @abstractmethod
    async def update_analytics(self, analytics_id: str) -> Optional[LearningAnalytics]:
        """Update existing analytics record"""
        pass
    
    @abstractmethod
    async def get_course_analytics_summary(self, course_id: str) -> Dict[str, Any]:
        """Get analytics summary for entire course"""
        pass
    
    @abstractmethod
    async def compare_student_performance(self, student_id: str, 
                                        course_id: str) -> Dict[str, Any]:
        """Compare student performance against course averages"""
        pass
    
    @abstractmethod
    async def predict_performance(self, student_id: str, 
                                course_id: str) -> Dict[str, Any]:
        """Predict future student performance"""
        pass
    
    @abstractmethod
    async def generate_insights(self, course_id: str, 
                              time_period_days: int = 30) -> List[Dict[str, Any]]:
        """Generate actionable insights for course improvement"""
        pass

class IReportingService(ABC):
    """Interface for analytics reporting and visualization"""
    
    @abstractmethod
    async def generate_student_report(self, student_id: str, course_id: str, 
                                    format: str = "json") -> Dict[str, Any]:
        """Generate comprehensive student report"""
        pass
    
    @abstractmethod
    async def generate_course_report(self, course_id: str, 
                                   format: str = "json") -> Dict[str, Any]:
        """Generate course-wide analytics report"""
        pass
    
    @abstractmethod
    async def generate_instructor_dashboard(self, instructor_id: str, 
                                          course_ids: List[str]) -> Dict[str, Any]:
        """Generate instructor dashboard data"""
        pass
    
    @abstractmethod
    async def export_analytics_data(self, course_id: str, 
                                  data_types: List[str],
                                  format: str = "csv") -> str:
        """Export analytics data in specified format"""
        pass
    
    @abstractmethod
    async def generate_visualizations(self, course_id: str, 
                                    chart_types: List[str]) -> List[Dict[str, Any]]:
        """Generate visualization data for charts"""
        pass

class IRiskAssessmentService(ABC):
    """Interface for student risk assessment"""
    
    @abstractmethod
    async def assess_student_risk(self, student_id: str, 
                                course_id: str) -> Tuple[RiskLevel, List[str]]:
        """Assess student risk level and provide reasons"""
        pass
    
    @abstractmethod
    async def get_risk_factors(self, student_id: str, 
                             course_id: str) -> Dict[str, float]:
        """Get individual risk factors with weights"""
        pass
    
    @abstractmethod
    async def get_intervention_recommendations(self, student_id: str, 
                                             course_id: str, 
                                             risk_level: RiskLevel) -> List[str]:
        """Get intervention recommendations based on risk level"""
        pass
    
    @abstractmethod
    async def track_intervention_effectiveness(self, student_id: str, 
                                             course_id: str, 
                                             intervention_type: str) -> Dict[str, Any]:
        """Track effectiveness of interventions"""
        pass
    
    @abstractmethod
    async def batch_risk_assessment(self, course_id: str) -> List[Dict[str, Any]]:
        """Perform risk assessment for all students in a course"""
        pass

class IPersonalizationService(ABC):
    """Interface for learning personalization based on analytics"""
    
    @abstractmethod
    async def get_personalized_recommendations(self, student_id: str, 
                                             course_id: str) -> List[Dict[str, Any]]:
        """Get personalized learning recommendations"""
        pass
    
    @abstractmethod
    async def suggest_learning_path(self, student_id: str, 
                                  course_id: str) -> List[str]:
        """Suggest optimal learning path based on performance"""
        pass
    
    @abstractmethod
    async def recommend_content_difficulty(self, student_id: str, 
                                         course_id: str, 
                                         content_type: ContentType) -> str:
        """Recommend appropriate content difficulty level"""
        pass
    
    @abstractmethod
    async def get_study_time_recommendations(self, student_id: str, 
                                           course_id: str) -> Dict[str, Any]:
        """Recommend optimal study times and durations"""
        pass
    
    @abstractmethod
    async def identify_knowledge_gaps(self, student_id: str, 
                                    course_id: str) -> List[Dict[str, Any]]:
        """Identify knowledge gaps and suggest remediation"""
        pass

class IPerformanceComparisonService(ABC):
    """Interface for performance comparison and benchmarking"""
    
    @abstractmethod
    async def compare_to_cohort(self, student_id: str, 
                              course_id: str) -> Dict[str, Any]:
        """Compare student performance to course cohort"""
        pass
    
    @abstractmethod
    async def compare_to_historical(self, student_id: str, 
                                  course_id: str) -> Dict[str, Any]:
        """Compare current performance to historical data"""
        pass
    
    @abstractmethod
    async def get_percentile_ranking(self, student_id: str, 
                                   course_id: str, 
                                   metric: str) -> float:
        """Get student's percentile ranking for specific metric"""
        pass
    
    @abstractmethod
    async def identify_high_performers(self, course_id: str, 
                                     top_percentage: float = 10.0) -> List[Dict[str, Any]]:
        """Identify top performing students"""
        pass
    
    @abstractmethod
    async def benchmark_against_similar_courses(self, course_id: str) -> Dict[str, Any]:
        """Benchmark course performance against similar courses"""
        pass