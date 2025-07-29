"""
Student Activity Service Implementation
Single Responsibility: Implement student activity tracking and analysis business logic
Dependency Inversion: Depends on repository abstractions for data access
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from ...domain.entities.student_analytics import StudentActivity, ActivityType
from ...domain.interfaces.analytics_service import IStudentActivityService
from ...domain.interfaces.analytics_repository import IStudentActivityRepository

class StudentActivityService(IStudentActivityService):
    """
    Student activity service implementation with business logic
    """
    
    def __init__(self, activity_repository: IStudentActivityRepository):
        self._activity_repository = activity_repository
        self._engagement_weights = {
            ActivityType.LOGIN: 1.0,
            ActivityType.LOGOUT: 0.5,
            ActivityType.LAB_ACCESS: 3.0,
            ActivityType.QUIZ_START: 2.5,
            ActivityType.QUIZ_COMPLETE: 4.0,
            ActivityType.CONTENT_VIEW: 2.0,
            ActivityType.CODE_EXECUTION: 3.5,
            ActivityType.EXERCISE_SUBMISSION: 4.5
        }
    
    async def record_activity(self, activity: StudentActivity) -> StudentActivity:
        """Record a new student activity with validation"""
        try:
            # Validate activity before recording
            activity.validate()
            
            # Additional business rule validation
            await self._validate_activity_context(activity)
            
            # Record the activity
            recorded_activity = await self._activity_repository.create(activity)
            
            # Trigger any side effects (analytics updates, notifications, etc.)
            await self._handle_activity_side_effects(recorded_activity)
            
            return recorded_activity
            
        except Exception as e:
            raise ValueError(f"Failed to record activity: {str(e)}")
    
    async def get_student_activities(self, student_id: str, course_id: str,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None,
                                   activity_types: Optional[List[ActivityType]] = None) -> List[StudentActivity]:
        """Get student activities with filtering and validation"""
        if not student_id:
            raise ValueError("Student ID is required")
        
        if not course_id:
            raise ValueError("Course ID is required")
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Validate date range
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        
        if end_date > datetime.utcnow():
            raise ValueError("End date cannot be in the future")
        
        activities = await self._activity_repository.get_by_student_and_course(
            student_id=student_id,
            course_id=course_id,
            start_date=start_date,
            end_date=end_date,
            activity_types=activity_types
        )
        
        return sorted(activities, key=lambda x: x.timestamp, reverse=True)
    
    async def get_engagement_score(self, student_id: str, course_id: str, 
                                 days_back: int = 30) -> float:
        """Calculate student engagement score based on activity patterns"""
        if not student_id or not course_id:
            raise ValueError("Student ID and Course ID are required")
        
        if days_back <= 0:
            raise ValueError("Days back must be positive")
        
        # Get activities for the specified period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        activities = await self.get_student_activities(
            student_id=student_id,
            course_id=course_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not activities:
            return 0.0
        
        # Calculate engagement score
        return self._calculate_engagement_score(activities, days_back)
    
    async def get_activity_summary(self, course_id: str,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get activity summary for a course"""
        if not course_id:
            raise ValueError("Course ID is required")
        
        # Set default date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        activities = await self._activity_repository.get_by_course(
            course_id=course_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return self._generate_activity_summary(activities, start_date, end_date)
    
    async def detect_learning_patterns(self, student_id: str, 
                                     course_id: str) -> Dict[str, Any]:
        """Detect learning patterns from student activities"""
        if not student_id or not course_id:
            raise ValueError("Student ID and Course ID are required")
        
        # Get activities for the last 60 days
        activities = await self.get_student_activities(
            student_id=student_id,
            course_id=course_id,
            start_date=datetime.utcnow() - timedelta(days=60)
        )
        
        if not activities:
            return {"patterns": [], "insights": []}
        
        patterns = {}
        
        # Analyze temporal patterns
        patterns["temporal"] = self._analyze_temporal_patterns(activities)
        
        # Analyze activity sequence patterns
        patterns["sequences"] = self._analyze_sequence_patterns(activities)
        
        # Analyze engagement patterns
        patterns["engagement"] = self._analyze_engagement_patterns(activities)
        
        # Generate insights
        insights = self._generate_pattern_insights(patterns)
        
        return {
            "patterns": patterns,
            "insights": insights,
            "analysis_date": datetime.utcnow(),
            "data_period_days": 60,
            "total_activities": len(activities)
        }
    
    # Helper methods
    async def _validate_activity_context(self, activity: StudentActivity) -> None:
        """Validate activity in business context"""
        # Check for suspicious activity patterns
        recent_activities = await self._activity_repository.get_by_student_and_course(
            student_id=activity.student_id,
            course_id=activity.course_id,
            start_date=datetime.utcnow() - timedelta(minutes=5),
            limit=10
        )
        
        # Check for duplicate activities (same type within 1 minute)
        duplicate_activities = [
            a for a in recent_activities
            if (a.activity_type == activity.activity_type and
                abs((a.timestamp - activity.timestamp).total_seconds()) < 60)
        ]
        
        if len(duplicate_activities) > 3:
            raise ValueError(f"Too many {activity.activity_type.value} activities in short timeframe")
    
    async def _handle_activity_side_effects(self, activity: StudentActivity) -> None:
        """Handle side effects of activity recording"""
        # This could trigger analytics updates, notifications, etc.
        # For now, we'll just log significant activities
        if activity.activity_type in [ActivityType.QUIZ_COMPLETE, ActivityType.EXERCISE_SUBMISSION]:
            # Could trigger real-time analytics update
            pass
    
    def _calculate_engagement_score(self, activities: List[StudentActivity], 
                                  days_back: int) -> float:
        """Calculate engagement score from activities"""
        if not activities:
            return 0.0
        
        # Calculate weighted activity score
        total_weight = 0.0
        for activity in activities:
            weight = self._engagement_weights.get(activity.activity_type, 1.0)
            total_weight += weight
        
        # Normalize by time period and expected activity level
        # Expected baseline: 5 weighted activities per day
        expected_total = days_back * 5.0
        
        # Calculate base score
        base_score = min(total_weight / expected_total, 1.0) * 80
        
        # Add bonus for consistency (activity spread across days)
        consistency_bonus = self._calculate_consistency_bonus(activities, days_back)
        
        # Add bonus for engagement variety
        variety_bonus = self._calculate_variety_bonus(activities)
        
        final_score = min(base_score + consistency_bonus + variety_bonus, 100.0)
        return round(final_score, 2)
    
    def _calculate_consistency_bonus(self, activities: List[StudentActivity], 
                                   days_back: int) -> float:
        """Calculate bonus points for consistent daily activity"""
        if not activities:
            return 0.0
        
        # Group activities by date
        daily_activities = defaultdict(int)
        for activity in activities:
            date_key = activity.timestamp.date()
            daily_activities[date_key] += 1
        
        # Calculate consistency score
        active_days = len(daily_activities)
        consistency_ratio = active_days / days_back
        
        # Bonus up to 15 points for high consistency
        return min(consistency_ratio * 15, 15.0)
    
    def _calculate_variety_bonus(self, activities: List[StudentActivity]) -> float:
        """Calculate bonus points for variety in activity types"""
        if not activities:
            return 0.0
        
        # Count unique activity types
        activity_types = set(activity.activity_type for activity in activities)
        variety_ratio = len(activity_types) / len(ActivityType)
        
        # Bonus up to 5 points for variety
        return min(variety_ratio * 5, 5.0)
    
    def _generate_activity_summary(self, activities: List[StudentActivity],
                                 start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive activity summary"""
        if not activities:
            return {
                "total_activities": 0,
                "unique_students": 0,
                "activity_breakdown": {},
                "daily_trends": [],
                "peak_hours": [],
                "engagement_level": "low"
            }
        
        # Basic counts
        total_activities = len(activities)
        unique_students = len(set(activity.student_id for activity in activities))
        
        # Activity type breakdown
        activity_counts = Counter(activity.activity_type for activity in activities)
        activity_breakdown = {
            activity_type.value: count 
            for activity_type, count in activity_counts.items()
        }
        
        # Daily trends
        daily_trends = self._calculate_daily_trends(activities, start_date, end_date)
        
        # Peak hours analysis
        peak_hours = self._analyze_peak_hours(activities)
        
        # Overall engagement level
        avg_engagement = self._calculate_average_engagement(activities)
        engagement_level = self._categorize_engagement_level(avg_engagement)
        
        return {
            "total_activities": total_activities,
            "unique_students": unique_students,
            "activity_breakdown": activity_breakdown,
            "daily_trends": daily_trends,
            "peak_hours": peak_hours,
            "engagement_level": engagement_level,
            "average_engagement_score": avg_engagement,
            "analysis_period": {
                "start_date": start_date,
                "end_date": end_date,
                "days": (end_date - start_date).days
            }
        }
    
    def _calculate_daily_trends(self, activities: List[StudentActivity],
                              start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Calculate daily activity trends"""
        # Group activities by date
        daily_counts = defaultdict(int)
        for activity in activities:
            date_key = activity.timestamp.date()
            daily_counts[date_key] += 1
        
        # Generate daily trend data
        trends = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            trends.append({
                "date": current_date.isoformat(),
                "activity_count": daily_counts.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        return trends
    
    def _analyze_peak_hours(self, activities: List[StudentActivity]) -> List[Dict[str, int]]:
        """Analyze peak activity hours"""
        hour_counts = defaultdict(int)
        for activity in activities:
            hour = activity.timestamp.hour
            hour_counts[hour] += 1
        
        # Sort by activity count and return top hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"hour": hour, "activity_count": count}
            for hour, count in sorted_hours[:5]
        ]
    
    def _calculate_average_engagement(self, activities: List[StudentActivity]) -> float:
        """Calculate average engagement score for activities"""
        if not activities:
            return 0.0
        
        # Group by student and calculate individual engagement
        student_activities = defaultdict(list)
        for activity in activities:
            student_activities[activity.student_id].append(activity)
        
        if not student_activities:
            return 0.0
        
        total_engagement = 0.0
        for student_id, student_acts in student_activities.items():
            engagement = self._calculate_engagement_score(student_acts, 7)  # 7-day period
            total_engagement += engagement
        
        return total_engagement / len(student_activities)
    
    def _categorize_engagement_level(self, avg_engagement: float) -> str:
        """Categorize engagement level based on score"""
        if avg_engagement >= 80:
            return "high"
        elif avg_engagement >= 60:
            return "medium"
        elif avg_engagement >= 40:
            return "low"
        else:
            return "very_low"
    
    def _analyze_temporal_patterns(self, activities: List[StudentActivity]) -> Dict[str, Any]:
        """Analyze temporal patterns in student activities"""
        if not activities:
            return {}
        
        # Analyze by day of week
        day_counts = defaultdict(int)
        for activity in activities:
            day_of_week = activity.timestamp.strftime("%A")
            day_counts[day_of_week] += 1
        
        # Analyze by hour of day
        hour_counts = defaultdict(int)
        for activity in activities:
            hour = activity.timestamp.hour
            hour_counts[hour] += 1
        
        # Find most active day and time
        most_active_day = max(day_counts.items(), key=lambda x: x[1]) if day_counts else None
        most_active_hour = max(hour_counts.items(), key=lambda x: x[1]) if hour_counts else None
        
        return {
            "day_distribution": dict(day_counts),
            "hour_distribution": dict(hour_counts),
            "most_active_day": most_active_day[0] if most_active_day else None,
            "most_active_hour": most_active_hour[0] if most_active_hour else None,
            "total_active_days": len(set(activity.timestamp.date() for activity in activities)),
            "average_daily_activities": len(activities) / max(len(set(activity.timestamp.date() for activity in activities)), 1)
        }
    
    def _analyze_sequence_patterns(self, activities: List[StudentActivity]) -> Dict[str, Any]:
        """Analyze common sequences of activities"""
        if len(activities) < 2:
            return {}
        
        # Sort activities by timestamp
        sorted_activities = sorted(activities, key=lambda x: x.timestamp)
        
        # Find common sequences
        sequences = []
        for i in range(len(sorted_activities) - 1):
            current = sorted_activities[i]
            next_activity = sorted_activities[i + 1]
            
            # Only consider sequences within reasonable time windows (1 hour)
            time_diff = (next_activity.timestamp - current.timestamp).total_seconds()
            if time_diff <= 3600:  # 1 hour
                sequences.append((current.activity_type.value, next_activity.activity_type.value))
        
        # Count sequence patterns
        sequence_counts = Counter(sequences)
        most_common_sequences = sequence_counts.most_common(5)
        
        return {
            "common_sequences": [
                {"sequence": f"{seq[0]} → {seq[1]}", "count": count}
                for seq, count in most_common_sequences
            ],
            "total_sequences": len(sequences)
        }
    
    def _analyze_engagement_patterns(self, activities: List[StudentActivity]) -> Dict[str, Any]:
        """Analyze engagement patterns over time"""
        if not activities:
            return {}
        
        # Group activities by week
        weekly_engagement = defaultdict(list)
        for activity in activities:
            week_start = activity.timestamp - timedelta(days=activity.timestamp.weekday())
            week_key = week_start.date()
            weekly_engagement[week_key].append(activity)
        
        # Calculate weekly engagement scores
        weekly_scores = {}
        for week, week_activities in weekly_engagement.items():
            score = self._calculate_engagement_score(week_activities, 7)
            weekly_scores[week] = score
        
        # Analyze trends
        scores_list = list(weekly_scores.values())
        if len(scores_list) > 1:
            # Simple trend calculation
            recent_avg = sum(scores_list[-2:]) / 2 if len(scores_list) >= 2 else scores_list[-1]
            overall_avg = sum(scores_list) / len(scores_list)
            trend = "increasing" if recent_avg > overall_avg else "decreasing"
        else:
            trend = "stable"
        
        return {
            "weekly_scores": {week.isoformat(): score for week, score in weekly_scores.items()},
            "trend": trend,
            "average_weekly_score": sum(scores_list) / len(scores_list) if scores_list else 0,
            "peak_week": max(weekly_scores.items(), key=lambda x: x[1])[0].isoformat() if weekly_scores else None
        }
    
    def _generate_pattern_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from detected patterns"""
        insights = []
        
        # Temporal insights
        temporal = patterns.get("temporal", {})
        if temporal.get("most_active_day"):
            insights.append(f"Most active on {temporal['most_active_day']}s")
        
        if temporal.get("most_active_hour") is not None:
            hour = temporal["most_active_hour"]
            time_period = "morning" if 6 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening" if 18 <= hour < 22 else "late night"
            insights.append(f"Peak activity during {time_period} hours ({hour}:00)")
        
        if temporal.get("average_daily_activities", 0) < 3:
            insights.append("Low daily activity frequency - consider setting daily learning goals")
        
        # Engagement insights
        engagement = patterns.get("engagement", {})
        if engagement.get("trend") == "decreasing":
            insights.append("Engagement declining over time - may need intervention")
        elif engagement.get("trend") == "increasing":
            insights.append("Positive engagement trend - student is gaining momentum")
        
        # Sequence insights
        sequences = patterns.get("sequences", {})
        common_seqs = sequences.get("common_sequences", [])
        if common_seqs:
            top_sequence = common_seqs[0]["sequence"]
            insights.append(f"Common learning pattern: {top_sequence}")
        
        return insights