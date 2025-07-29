"""
Learning Analytics Service Implementation
Single Responsibility: Implement comprehensive learning analytics business logic
Dependency Inversion: Depends on repository and service abstractions
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from ...domain.entities.student_analytics import LearningAnalytics, RiskLevel
from ...domain.interfaces.analytics_service import (
    ILearningAnalyticsService, IStudentActivityService, 
    ILabAnalyticsService, IQuizAnalyticsService, IProgressTrackingService
)
from ...domain.interfaces.analytics_repository import ILearningAnalyticsRepository

class LearningAnalyticsService(ILearningAnalyticsService):
    """
    Comprehensive learning analytics service implementation
    """
    
    def __init__(self, 
                 analytics_repository: ILearningAnalyticsRepository,
                 activity_service: IStudentActivityService,
                 lab_service: ILabAnalyticsService,
                 quiz_service: IQuizAnalyticsService,
                 progress_service: IProgressTrackingService):
        self._analytics_repository = analytics_repository
        self._activity_service = activity_service
        self._lab_service = lab_service
        self._quiz_service = quiz_service
        self._progress_service = progress_service
    
    async def generate_student_analytics(self, student_id: str, 
                                       course_id: str) -> LearningAnalytics:
        """Generate comprehensive analytics for a student"""
        if not student_id or not course_id:
            raise ValueError("Student ID and Course ID are required")
        
        # Gather data from all service components concurrently
        analytics_data = await self._gather_analytics_data(student_id, course_id)
        
        # Calculate derived metrics
        engagement_score = await self._calculate_engagement_score(analytics_data)
        progress_velocity = await self._calculate_progress_velocity(analytics_data)
        lab_proficiency = await self._calculate_lab_proficiency(analytics_data)
        quiz_performance = await self._calculate_quiz_performance(analytics_data)
        time_on_platform = await self._calculate_time_on_platform(analytics_data)
        streak_days = await self._calculate_streak_days(analytics_data)
        
        # Create learning analytics entity
        analytics = LearningAnalytics(
            student_id=student_id,
            course_id=course_id,
            engagement_score=engagement_score,
            progress_velocity=progress_velocity,
            lab_proficiency=lab_proficiency,
            quiz_performance=quiz_performance,
            time_on_platform=time_on_platform,
            streak_days=streak_days
        )
        
        # Update risk level based on calculated metrics
        analytics.update_risk_level()
        
        # Generate personalized recommendations
        analytics.generate_recommendations()
        
        # Save analytics
        return await self._analytics_repository.create(analytics)
    
    async def update_analytics(self, analytics_id: str) -> Optional[LearningAnalytics]:
        """Update existing analytics record"""
        if not analytics_id:
            raise ValueError("Analytics ID is required")
        
        # Get existing analytics
        existing_analytics = await self._analytics_repository.get_by_id(analytics_id)
        if not existing_analytics:
            return None
        
        # Generate fresh analytics
        updated_analytics = await self.generate_student_analytics(
            existing_analytics.student_id,
            existing_analytics.course_id
        )
        
        # Update the existing record ID
        updated_analytics.id = analytics_id
        updated_analytics.analysis_date = datetime.utcnow()
        
        return await self._analytics_repository.update(updated_analytics)
    
    async def get_course_analytics_summary(self, course_id: str) -> Dict[str, Any]:
        """Get analytics summary for entire course"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        # Get all student analytics for the course
        course_analytics = await self._analytics_repository.get_by_course(course_id)
        
        if not course_analytics:
            return self._empty_course_summary()
        
        return await self._generate_course_summary(course_analytics, course_id)
    
    async def compare_student_performance(self, student_id: str, 
                                        course_id: str) -> Dict[str, Any]:
        """Compare student performance against course averages"""
        if not student_id or not course_id:
            raise ValueError("Student ID and Course ID are required")
        
        # Get student analytics
        student_analytics = await self._analytics_repository.get_by_student_and_course(
            student_id, course_id
        )
        
        if not student_analytics:
            # Generate fresh analytics if none exist
            student_analytics = await self.generate_student_analytics(student_id, course_id)
        
        # Get course averages
        course_summary = await self.get_course_analytics_summary(course_id)
        course_averages = course_summary.get("averages", {})
        
        return self._generate_performance_comparison(student_analytics, course_averages)
    
    async def predict_performance(self, student_id: str, 
                                course_id: str) -> Dict[str, Any]:
        """Predict future student performance"""
        if not student_id or not course_id:
            raise ValueError("Student ID and Course ID are required")
        
        # Get historical analytics
        historical_analytics = await self._analytics_repository.get_historical_analytics(
            student_id=student_id,
            course_id=course_id,
            days_back=90
        )
        
        if len(historical_analytics) < 2:
            return {
                "prediction_available": False,
                "reason": "Insufficient historical data for prediction",
                "minimum_data_points": 2,
                "available_data_points": len(historical_analytics)
            }
        
        return await self._generate_performance_prediction(historical_analytics)
    
    async def generate_insights(self, course_id: str, 
                              time_period_days: int = 30) -> List[Dict[str, Any]]:
        """Generate actionable insights for course improvement"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        if time_period_days <= 0:
            raise ValueError("Time period must be positive")
        
        # Get recent analytics data
        course_analytics = await self._analytics_repository.get_by_course(course_id)
        
        # Filter for recent data
        recent_date = datetime.utcnow() - timedelta(days=time_period_days)
        recent_analytics = [
            analytics for analytics in course_analytics
            if analytics.analysis_date >= recent_date
        ]
        
        if not recent_analytics:
            return []
        
        return await self._generate_course_insights(recent_analytics, course_id, time_period_days)
    
    # Helper methods
    async def _gather_analytics_data(self, student_id: str, course_id: str) -> Dict[str, Any]:
        """Gather data from all analytics components concurrently"""
        # Use asyncio.gather for concurrent data collection
        tasks = [
            self._activity_service.get_engagement_score(student_id, course_id, days_back=30),
            self._lab_service.get_lab_proficiency_score(student_id, course_id),
            self._quiz_service.get_student_quiz_history(student_id, course_id),
            self._progress_service.get_progress_summary(student_id, course_id),
            self._activity_service.get_student_activities(
                student_id, course_id, 
                start_date=datetime.utcnow() - timedelta(days=30)
            )
        ]
        
        try:
            engagement_score, lab_proficiency, quiz_history, progress_summary, activities = await asyncio.gather(*tasks)
            
            return {
                "engagement_score": engagement_score,
                "lab_proficiency": lab_proficiency,
                "quiz_history": quiz_history,
                "progress_summary": progress_summary,
                "activities": activities
            }
        except Exception as e:
            # Handle partial failures gracefully
            return await self._gather_analytics_data_fallback(student_id, course_id)
    
    async def _gather_analytics_data_fallback(self, student_id: str, course_id: str) -> Dict[str, Any]:
        """Fallback data gathering with individual error handling"""
        data = {}
        
        try:
            data["engagement_score"] = await self._activity_service.get_engagement_score(
                student_id, course_id, days_back=30
            )
        except Exception:
            data["engagement_score"] = 0.0
        
        try:
            data["lab_proficiency"] = await self._lab_service.get_lab_proficiency_score(
                student_id, course_id
            )
        except Exception:
            data["lab_proficiency"] = 0.0
        
        try:
            data["quiz_history"] = await self._quiz_service.get_student_quiz_history(
                student_id, course_id
            )
        except Exception:
            data["quiz_history"] = []
        
        try:
            data["progress_summary"] = await self._progress_service.get_progress_summary(
                student_id, course_id
            )
        except Exception:
            data["progress_summary"] = {}
        
        try:
            data["activities"] = await self._activity_service.get_student_activities(
                student_id, course_id, 
                start_date=datetime.utcnow() - timedelta(days=30)
            )
        except Exception:
            data["activities"] = []
        
        return data
    
    async def _calculate_engagement_score(self, analytics_data: Dict[str, Any]) -> float:
        """Calculate comprehensive engagement score"""
        base_engagement = analytics_data.get("engagement_score", 0.0)
        activities = analytics_data.get("activities", [])
        
        if not activities:
            return base_engagement
        
        # Add bonus for recent activity
        recent_activities = [
            activity for activity in activities
            if (datetime.utcnow() - activity.timestamp).days <= 7
        ]
        
        recent_activity_bonus = min(len(recent_activities) * 2, 10)  # Max 10 points bonus
        
        return min(base_engagement + recent_activity_bonus, 100.0)
    
    async def _calculate_progress_velocity(self, analytics_data: Dict[str, Any]) -> float:
        """Calculate learning progress velocity"""
        progress_summary = analytics_data.get("progress_summary", {})
        
        # Get completion rate and time metrics
        completion_rate = progress_summary.get("completion_rate", 0.0)
        time_in_course_days = progress_summary.get("time_in_course_days", 1)
        
        if time_in_course_days <= 0:
            return 0.0
        
        # Calculate items completed per week
        items_completed = progress_summary.get("items_completed", 0)
        weeks_in_course = max(time_in_course_days / 7, 1)
        
        velocity = items_completed / weeks_in_course
        return round(velocity, 2)
    
    async def _calculate_lab_proficiency(self, analytics_data: Dict[str, Any]) -> float:
        """Calculate lab proficiency score"""
        return analytics_data.get("lab_proficiency", 0.0)
    
    async def _calculate_quiz_performance(self, analytics_data: Dict[str, Any]) -> float:
        """Calculate average quiz performance"""
        quiz_history = analytics_data.get("quiz_history", [])
        
        if not quiz_history:
            return 0.0
        
        # Calculate average score from completed quizzes
        completed_quizzes = [quiz for quiz in quiz_history if quiz.is_completed()]
        
        if not completed_quizzes:
            return 0.0
        
        total_score = sum(quiz.get_score_percentage() or 0 for quiz in completed_quizzes)
        return round(total_score / len(completed_quizzes), 2)
    
    async def _calculate_time_on_platform(self, analytics_data: Dict[str, Any]) -> int:
        """Calculate total time on platform in minutes"""
        progress_summary = analytics_data.get("progress_summary", {})
        total_time = progress_summary.get("total_time_spent_minutes", 0)
        
        # Add estimated time from activities
        activities = analytics_data.get("activities", [])
        if len(activities) > 1:
            # Estimate session durations from activity gaps
            estimated_time = 0
            for i in range(len(activities) - 1):
                time_gap = (activities[i].timestamp - activities[i+1].timestamp).total_seconds() / 60
                if 1 <= time_gap <= 120:  # Between 1 minute and 2 hours
                    estimated_time += time_gap
            
            total_time = max(total_time, int(estimated_time))
        
        return total_time
    
    async def _calculate_streak_days(self, analytics_data: Dict[str, Any]) -> int:
        """Calculate current learning streak in days"""
        activities = analytics_data.get("activities", [])
        
        if not activities:
            return 0
        
        # Sort activities by date (most recent first)
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Check for activity in recent days
        streak = 0
        current_date = datetime.utcnow().date()
        
        # Group activities by date
        daily_activities = {}
        for activity in activities:
            date_key = activity.timestamp.date()
            if date_key not in daily_activities:
                daily_activities[date_key] = []
            daily_activities[date_key].append(activity)
        
        # Count consecutive days with activity
        while current_date in daily_activities:
            # Check if there's meaningful activity (not just login/logout)
            meaningful_activities = [
                activity for activity in daily_activities[current_date]
                if activity.is_engagement_activity()
            ]
            
            if meaningful_activities:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _empty_course_summary(self) -> Dict[str, Any]:
        """Return empty course summary structure"""
        return {
            "total_students": 0,
            "averages": {
                "engagement_score": 0.0,
                "progress_velocity": 0.0,
                "lab_proficiency": 0.0,
                "quiz_performance": 0.0,
                "time_on_platform": 0,
                "streak_days": 0
            },
            "risk_distribution": {level.value: 0 for level in RiskLevel},
            "trends": {},
            "insights": []
        }
    
    async def _generate_course_summary(self, course_analytics: List[LearningAnalytics], 
                                     course_id: str) -> Dict[str, Any]:
        """Generate comprehensive course summary"""
        total_students = len(course_analytics)
        
        if total_students == 0:
            return self._empty_course_summary()
        
        # Calculate averages
        averages = {
            "engagement_score": sum(a.engagement_score for a in course_analytics) / total_students,
            "progress_velocity": sum(a.progress_velocity for a in course_analytics) / total_students,
            "lab_proficiency": sum(a.lab_proficiency for a in course_analytics) / total_students,
            "quiz_performance": sum(a.quiz_performance for a in course_analytics) / total_students,
            "time_on_platform": sum(a.time_on_platform for a in course_analytics) // total_students,
            "streak_days": sum(a.streak_days for a in course_analytics) // total_students
        }
        
        # Round averages
        for key, value in averages.items():
            if isinstance(value, float):
                averages[key] = round(value, 2)
        
        # Risk distribution
        risk_distribution = {level.value: 0 for level in RiskLevel}
        for analytics in course_analytics:
            risk_distribution[analytics.risk_level.value] += 1
        
        # Calculate trends (if we have historical data)
        trends = await self._calculate_course_trends(course_id)
        
        # Generate insights
        insights = await self._generate_course_insights(course_analytics, course_id, 30)
        
        return {
            "total_students": total_students,
            "averages": averages,
            "risk_distribution": risk_distribution,
            "trends": trends,
            "insights": insights[:5],  # Top 5 insights
            "last_updated": datetime.utcnow(),
            "high_performers": [
                {"student_id": a.student_id, "overall_score": a.calculate_overall_performance()}
                for a in sorted(course_analytics, key=lambda x: x.calculate_overall_performance(), reverse=True)[:5]
            ],
            "at_risk_students": [
                {"student_id": a.student_id, "risk_level": a.risk_level.value, "overall_score": a.calculate_overall_performance()}
                for a in course_analytics if a.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            ]
        }
    
    def _generate_performance_comparison(self, student_analytics: LearningAnalytics, 
                                       course_averages: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance comparison against course averages"""
        student_metrics = {
            "engagement_score": student_analytics.engagement_score,
            "progress_velocity": student_analytics.progress_velocity,
            "lab_proficiency": student_analytics.lab_proficiency,
            "quiz_performance": student_analytics.quiz_performance,
            "time_on_platform": student_analytics.time_on_platform,
            "streak_days": student_analytics.streak_days,
            "overall_performance": student_analytics.calculate_overall_performance()
        }
        
        comparisons = {}
        for metric, student_value in student_metrics.items():
            course_avg = course_averages.get(metric, 0)
            if course_avg > 0:
                percentage_diff = ((student_value - course_avg) / course_avg) * 100
                status = "above_average" if percentage_diff > 5 else "below_average" if percentage_diff < -5 else "average"
            else:
                percentage_diff = 0
                status = "no_comparison"
            
            comparisons[metric] = {
                "student_value": student_value,
                "course_average": course_avg,
                "percentage_difference": round(percentage_diff, 1),
                "status": status
            }
        
        # Generate summary
        above_average_count = sum(1 for comp in comparisons.values() if comp["status"] == "above_average")
        total_metrics = len([comp for comp in comparisons.values() if comp["status"] != "no_comparison"])
        
        overall_standing = "excellent" if above_average_count >= total_metrics * 0.8 else \
                          "good" if above_average_count >= total_metrics * 0.6 else \
                          "needs_improvement"
        
        return {
            "student_id": student_analytics.student_id,
            "course_id": student_analytics.course_id,
            "comparison_date": datetime.utcnow(),
            "overall_standing": overall_standing,
            "metrics_above_average": above_average_count,
            "total_comparable_metrics": total_metrics,
            "detailed_comparisons": comparisons,
            "percentile_estimate": self._estimate_percentile(student_analytics.calculate_overall_performance(), course_averages)
        }
    
    def _estimate_percentile(self, student_score: float, course_averages: Dict[str, Any]) -> int:
        """Estimate student's percentile ranking"""
        course_overall_avg = course_averages.get("overall_performance", 50)
        
        # Simple percentile estimation based on standard deviation assumptions
        if student_score >= course_overall_avg + 20:
            return 90
        elif student_score >= course_overall_avg + 10:
            return 75
        elif student_score >= course_overall_avg:
            return 60
        elif student_score >= course_overall_avg - 10:
            return 40
        elif student_score >= course_overall_avg - 20:
            return 25
        else:
            return 10
    
    async def _generate_performance_prediction(self, historical_analytics: List[LearningAnalytics]) -> Dict[str, Any]:
        """Generate performance prediction based on trends"""
        if len(historical_analytics) < 2:
            return {"prediction_available": False}
        
        # Sort by analysis date
        historical_analytics.sort(key=lambda x: x.analysis_date)
        
        # Calculate trends for key metrics
        trends = {}
        metrics = ["engagement_score", "progress_velocity", "lab_proficiency", "quiz_performance"]
        
        for metric in metrics:
            values = [getattr(analytics, metric) for analytics in historical_analytics]
            
            # Simple linear trend calculation
            if len(values) >= 2:
                trend_slope = (values[-1] - values[0]) / (len(values) - 1)
                trends[metric] = {
                    "current_value": values[-1],
                    "trend_slope": round(trend_slope, 3),
                    "direction": "improving" if trend_slope > 0.1 else "declining" if trend_slope < -0.1 else "stable"
                }
        
        # Predict future performance (simple extrapolation)
        prediction_weeks = 4  # 4 weeks ahead
        predictions = {}
        
        for metric, trend_data in trends.items():
            current = trend_data["current_value"]
            slope = trend_data["trend_slope"]
            predicted = max(0, min(100, current + (slope * prediction_weeks)))
            predictions[metric] = round(predicted, 2)
        
        # Generate prediction confidence
        confidence = self._calculate_prediction_confidence(historical_analytics)
        
        return {
            "prediction_available": True,
            "prediction_horizon_weeks": prediction_weeks,
            "current_trends": trends,
            "predicted_values": predictions,
            "confidence_level": confidence,
            "prediction_date": datetime.utcnow(),
            "recommendations": self._generate_prediction_recommendations(trends)
        }
    
    def _calculate_prediction_confidence(self, historical_analytics: List[LearningAnalytics]) -> str:
        """Calculate confidence level for predictions"""
        data_points = len(historical_analytics)
        
        if data_points >= 8:
            return "high"
        elif data_points >= 4:
            return "medium"
        else:
            return "low"
    
    def _generate_prediction_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on predicted trends"""
        recommendations = []
        
        for metric, trend_data in trends.items():
            direction = trend_data["direction"]
            
            if direction == "declining":
                if metric == "engagement_score":
                    recommendations.append("Focus on increasing platform engagement through interactive content")
                elif metric == "lab_proficiency":
                    recommendations.append("Allocate more time to hands-on coding practice")
                elif metric == "quiz_performance":
                    recommendations.append("Review course materials and seek additional help")
                elif metric == "progress_velocity":
                    recommendations.append("Establish a more consistent study schedule")
        
        if not recommendations:
            recommendations.append("Continue current learning approach - trends are positive or stable")
        
        return recommendations
    
    async def _calculate_course_trends(self, course_id: str) -> Dict[str, Any]:
        """Calculate course-wide trends"""
        # This would require historical course analytics
        # For now, return empty trends
        return {
            "engagement_trend": "stable",
            "performance_trend": "stable",
            "enrollment_trend": "stable"
        }
    
    async def _generate_course_insights(self, course_analytics: List[LearningAnalytics], 
                                      course_id: str, time_period_days: int) -> List[Dict[str, Any]]:
        """Generate actionable insights for course improvement"""
        insights = []
        
        if not course_analytics:
            return insights
        
        # Analyze risk distribution
        high_risk_count = sum(1 for a in course_analytics if a.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL])
        total_students = len(course_analytics)
        
        if high_risk_count > total_students * 0.3:
            insights.append({
                "type": "alert",
                "priority": "high",
                "title": "High number of at-risk students",
                "description": f"{high_risk_count} out of {total_students} students are at high risk",
                "recommendation": "Consider implementing early intervention strategies"
            })
        
        # Analyze engagement patterns
        avg_engagement = sum(a.engagement_score for a in course_analytics) / len(course_analytics)
        if avg_engagement < 60:
            insights.append({
                "type": "improvement",
                "priority": "medium",
                "title": "Low course engagement",
                "description": f"Average engagement score is {avg_engagement:.1f}",
                "recommendation": "Add more interactive content and gamification elements"
            })
        
        # Analyze lab proficiency
        avg_lab_proficiency = sum(a.lab_proficiency for a in course_analytics) / len(course_analytics)
        if avg_lab_proficiency < 50:
            insights.append({
                "type": "improvement",
                "priority": "high",
                "title": "Low lab proficiency",
                "description": f"Average lab proficiency is {avg_lab_proficiency:.1f}",
                "recommendation": "Provide additional lab support and coding tutorials"
            })
        
        # Analyze quiz performance
        avg_quiz_performance = sum(a.quiz_performance for a in course_analytics) / len(course_analytics)
        if avg_quiz_performance < 70:
            insights.append({
                "type": "improvement",
                "priority": "medium",
                "title": "Quiz performance concerns",
                "description": f"Average quiz performance is {avg_quiz_performance:.1f}%",
                "recommendation": "Review quiz difficulty and provide additional study materials"
            })
        
        # Analyze learning streaks
        students_with_streaks = sum(1 for a in course_analytics if a.streak_days >= 3)
        if students_with_streaks < total_students * 0.5:
            insights.append({
                "type": "engagement",
                "priority": "medium",
                "title": "Low learning consistency",
                "description": f"Only {students_with_streaks} students have learning streaks of 3+ days",
                "recommendation": "Implement daily challenges or reminders to encourage consistent engagement"
            })
        
        return insights