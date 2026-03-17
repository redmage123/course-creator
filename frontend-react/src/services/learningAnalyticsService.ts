/**
 * Learning Analytics Service
 *
 * BUSINESS CONTEXT:
 * Provides comprehensive learning analytics for students, instructors, and administrators.
 * Tracks learning paths, skill mastery, session activity, and progress metrics to enable
 * data-driven decisions and personalized learning experiences.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Connects to analytics backend endpoints (port 8004)
 * - Provides learning path progress tracking
 * - Delivers skill mastery metrics with SM-2 spaced repetition
 * - Tracks session activity and engagement patterns
 * - Supports all user roles (student, instructor, org_admin, site_admin)
 *
 * WHY THIS APPROACH:
 * - Centralized learning analytics API logic separate from general analytics
 * - Type-safe interfaces for dashboard data consistency
 * - Role-appropriate data access controls
 * - Comprehensive documentation for maintainability
 */

import { apiClient } from './apiClient';

/**
 * Learning Path Progress Data
 * Tracks student progress through structured learning paths
 */
export interface LearningPathProgress {
  id: string;
  user_id: string;
  track_id: string;
  overall_progress: number;
  current_course_id?: string;
  current_module_order?: number;
  milestones_completed: MilestoneData[];
  started_at?: string;
  estimated_completion_at?: string;
  actual_completion_at?: string;
  total_time_spent_minutes: number;
  avg_quiz_score?: number;
  avg_assignment_score?: number;
  status: LearningPathStatus;
  last_activity_at?: string;
}

/**
 * Learning Path Status Enum
 * Current state of student's learning path
 */
export type LearningPathStatus =
  | 'not_started'
  | 'in_progress'
  | 'on_track'
  | 'behind'
  | 'at_risk'
  | 'completed'
  | 'abandoned';

/**
 * Milestone Data
 * Significant checkpoints in learning path
 */
export interface MilestoneData {
  milestone_id: string;
  name: string;
  completed_at: string;
  score?: number;
}

/**
 * Skill Mastery Data
 * Tracks mastery level for specific skills/topics
 */
export interface SkillMastery {
  id: string;
  student_id: string;
  skill_topic: string;
  mastery_level: MasteryLevel;
  mastery_score: number;
  assessments_completed: number;
  assessments_passed: number;
  average_score?: number;
  best_score?: number;
  total_practice_time_minutes: number;
  last_practiced_at?: string;
  practice_streak_days: number;
  last_assessment_at?: string;
  retention_estimate: number;
  next_review_recommended_at?: string;
  // SM-2 Spaced Repetition Fields
  ease_factor: number;
  repetition_count: number;
  current_interval_days: number;
  last_quality_rating: number;
}

/**
 * Mastery Level Enum
 * Fine-grained skill progression levels
 */
export type MasteryLevel =
  | 'novice'
  | 'beginner'
  | 'intermediate'
  | 'proficient'
  | 'expert'
  | 'master';

/**
 * Session Activity Data
 * Tracks learning session metrics
 */
export interface SessionActivity {
  session_id: string;
  user_id: string;
  course_id?: string;
  started_at: string;
  ended_at?: string;
  duration_minutes: number;
  activities_count: number;
  engagement_score: number;
  content_items_viewed: number;
  quizzes_attempted: number;
  labs_worked_on: number;
  pages_visited: string[];
}

/**
 * Learning Progress Chart Data Point
 * Time-series data for progress visualization
 */
export interface LearningProgressDataPoint {
  date: string;
  progress_percentage: number;
  items_completed: number;
  time_spent_minutes: number;
  engagement_score: number;
}

/**
 * Aggregated Learning Analytics
 * Comprehensive analytics summary for dashboard
 */
export interface LearningAnalyticsSummary {
  student_id: string;
  course_id?: string;
  overall_engagement_score: number;
  total_learning_time_minutes: number;
  active_learning_paths: number;
  completed_learning_paths: number;
  total_skills_tracked: number;
  skills_mastered: number;
  average_mastery_score: number;
  current_streak_days: number;
  longest_streak_days: number;
  sessions_this_week: number;
  sessions_this_month: number;
  skills_needing_review: SkillMastery[];
  recent_milestones: MilestoneData[];
}

/**
 * Time Range Type
 * Supported time range filters for analytics
 */
export type TimeRange = '7d' | '30d' | '90d' | '6m' | '1y' | 'all';

/**
 * Learning Analytics Service Class
 *
 * WHY THIS APPROACH:
 * - Encapsulates all learning analytics API calls
 * - Provides type-safe interfaces for data consistency
 * - Supports role-based access to analytics data
 * - Enables progressive enhancement of analytics features
 * - Follows singleton pattern for efficient resource usage
 */
class LearningAnalyticsService {
  private baseUrl = '/analytics/learning';

  /**
   * Get student's learning analytics summary
   *
   * WHAT: Retrieves comprehensive learning analytics overview
   * WHERE: Student dashboard main analytics widget
   * WHY: Provides quick snapshot of overall learning performance
   */
  async getStudentLearningAnalytics(studentId: string): Promise<LearningAnalyticsSummary> {
    return await apiClient.get<LearningAnalyticsSummary>(
      `${this.baseUrl}/student/${studentId}/summary`
    );
  }

  /**
   * Get current user's learning analytics
   *
   * WHAT: Retrieves learning analytics for logged-in user
   * WHERE: Student dashboard (no ID required)
   * WHY: Convenience method for current user analytics
   */
  async getMyLearningAnalytics(): Promise<LearningAnalyticsSummary> {
    return await apiClient.get<LearningAnalyticsSummary>(`${this.baseUrl}/student/me/summary`);
  }

  /**
   * Get learning path progress for student
   *
   * WHAT: Retrieves detailed learning path progress data
   * WHERE: Learning path progress visualization components
   * WHY: Tracks student advancement through structured curriculum
   */
  async getLearningPathProgress(studentId: string, trackId: string): Promise<LearningPathProgress> {
    return await apiClient.get<LearningPathProgress>(
      `${this.baseUrl}/student/${studentId}/path/${trackId}`
    );
  }

  /**
   * Get all learning paths for student
   *
   * WHAT: Retrieves all active and completed learning paths
   * WHERE: Learning paths overview page
   * WHY: Shows complete learning journey across multiple tracks
   */
  async getStudentLearningPaths(studentId: string): Promise<LearningPathProgress[]> {
    return await apiClient.get<LearningPathProgress[]>(
      `${this.baseUrl}/student/${studentId}/paths`
    );
  }

  /**
   * Get skill mastery data for student
   *
   * WHAT: Retrieves mastery levels for all tracked skills
   * WHERE: Skill mastery dashboard widget
   * WHY: Identifies strengths, weaknesses, and review needs
   */
  async getSkillMastery(studentId: string, courseId?: string): Promise<SkillMastery[]> {
    const params = courseId ? { course_id: courseId } : {};
    return await apiClient.get<SkillMastery[]>(
      `${this.baseUrl}/student/${studentId}/skills`,
      { params }
    );
  }

  /**
   * Get specific skill mastery data
   *
   * WHAT: Retrieves detailed mastery data for a single skill
   * WHERE: Skill detail page, spaced repetition scheduler
   * WHY: Supports targeted practice and review scheduling
   */
  async getSkillMasteryDetail(studentId: string, skillTopic: string): Promise<SkillMastery> {
    return await apiClient.get<SkillMastery>(
      `${this.baseUrl}/student/${studentId}/skill/${encodeURIComponent(skillTopic)}`
    );
  }

  /**
   * Get skills needing review (spaced repetition)
   *
   * WHAT: Retrieves skills due for review based on SM-2 algorithm
   * WHERE: Review scheduler, practice recommendations
   * WHY: Optimizes retention through spaced repetition
   */
  async getSkillsNeedingReview(studentId: string): Promise<SkillMastery[]> {
    return await apiClient.get<SkillMastery[]>(
      `${this.baseUrl}/student/${studentId}/skills/review-needed`
    );
  }

  /**
   * Get session activity data
   *
   * WHAT: Retrieves learning session activity history
   * WHERE: Session activity widget, engagement analytics
   * WHY: Tracks learning patterns and engagement trends
   */
  async getSessionActivity(
    studentId: string,
    timeRange: TimeRange = '30d'
  ): Promise<SessionActivity[]> {
    return await apiClient.get<SessionActivity[]>(
      `${this.baseUrl}/student/${studentId}/sessions`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get learning progress over time
   *
   * WHAT: Retrieves time-series progress data for charts
   * WHERE: Progress chart visualizations
   * WHY: Shows learning trajectory and velocity
   */
  async getLearningProgressTimeSeries(
    studentId: string,
    courseId?: string,
    timeRange: TimeRange = '30d'
  ): Promise<LearningProgressDataPoint[]> {
    const params: any = { range: timeRange };
    if (courseId) {
      params.course_id = courseId;
    }
    return await apiClient.get<LearningProgressDataPoint[]>(
      `${this.baseUrl}/student/${studentId}/progress-timeline`,
      { params }
    );
  }

  /**
   * Get course-level learning analytics (instructor view)
   *
   * WHAT: Retrieves aggregated learning analytics for entire course
   * WHERE: Instructor dashboard, course analytics page
   * WHY: Enables instructors to monitor class progress and identify issues
   */
  async getCourseLearningAnalytics(courseId: string): Promise<{
    course_id: string;
    total_students: number;
    students_by_status: Record<LearningPathStatus, number>;
    average_progress: number;
    average_mastery_score: number;
    skills_by_mastery_level: Record<MasteryLevel, number>;
    at_risk_students: number;
    completed_students: number;
    average_time_spent_minutes: number;
  }> {
    return await apiClient.get(
      `${this.baseUrl}/course/${courseId}/summary`
    );
  }

  /**
   * Get organization-level learning analytics (org admin view)
   *
   * WHAT: Retrieves aggregated learning analytics for organization
   * WHERE: Organization admin dashboard
   * WHY: Provides organizational insights for resource allocation
   */
  async getOrganizationLearningAnalytics(organizationId: string): Promise<{
    organization_id: string;
    total_students: number;
    active_learning_paths: number;
    completed_learning_paths: number;
    average_completion_rate: number;
    total_skills_tracked: number;
    average_mastery_score: number;
    students_at_risk: number;
    engagement_trend: 'improving' | 'stable' | 'declining';
  }> {
    return await apiClient.get(
      `${this.baseUrl}/organization/${organizationId}/summary`
    );
  }

  /**
   * Export learning analytics report
   *
   * WHAT: Generates downloadable analytics report
   * WHERE: Export functionality in analytics dashboards
   * WHY: Enables offline analysis and record keeping
   */
  async exportLearningAnalytics(
    studentId: string,
    format: 'pdf' | 'csv' | 'excel' = 'pdf'
  ): Promise<Blob> {
    return await apiClient.get(
      `${this.baseUrl}/student/${studentId}/export`,
      {
        params: { format },
        responseType: 'blob',
      }
    );
  }
}

// Export singleton instance
export const learningAnalyticsService = new LearningAnalyticsService();
