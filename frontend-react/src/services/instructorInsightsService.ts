/**
 * Instructor Insights Service
 *
 * BUSINESS CONTEXT:
 * Provides instructors with actionable analytics to improve teaching effectiveness.
 * Connects to the analytics service backend to fetch:
 * - Teaching effectiveness metrics
 * - Course performance analytics
 * - Student engagement patterns
 * - AI-powered teaching recommendations
 * - Peer comparison benchmarks (anonymized)
 * - Personal improvement goals
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses centralized apiClient with authentication
 * - Type-safe interfaces aligned with backend entities
 * - Supports time-range filtering for trend analysis
 * - Integrates with analytics service (port 8004)
 *
 * @module services/instructorInsightsService
 */

import { apiClient } from './apiClient';

/**
 * Trend Direction
 * Indicates whether a metric is improving, stable, or declining
 */
export type Trend = 'improving' | 'stable' | 'declining';

/**
 * Recommendation Priority
 * Helps instructors focus on high-impact improvements
 */
export type RecommendationPriority = 'low' | 'medium' | 'high' | 'critical';

/**
 * Recommendation Category
 * Categories for filtering and organizing recommendations
 */
export type RecommendationCategory =
  | 'engagement'
  | 'content_quality'
  | 'responsiveness'
  | 'assessment'
  | 'communication'
  | 'organization'
  | 'accessibility'
  | 'technical';

/**
 * Instructor Effectiveness Metrics
 * Core teaching effectiveness scores and performance indicators
 */
export interface InstructorEffectivenessMetrics {
  id: string;
  instructor_id: string;
  organization_id?: string;

  // Core metrics (0-100 scale for scores, 0-5 for ratings)
  overall_rating?: number;
  teaching_quality_score?: number;
  content_clarity_score?: number;
  engagement_score?: number;
  responsiveness_score?: number;

  // Derived metrics
  total_students_taught: number;
  course_completion_rate?: number;
  average_quiz_score?: number;
  student_retention_rate?: number;

  // Trends
  rating_trend?: Trend;
  engagement_trend?: Trend;

  // Period tracking
  period_start: string;
  period_end: string;

  calculated_at: string;
}

/**
 * Course Performance Metrics
 * Per-course analytics for instructors
 */
export interface InstructorCoursePerformance {
  id: string;
  instructor_id: string;
  course_id: string;
  course_title?: string;
  organization_id?: string;

  // Enrollment metrics
  total_enrolled: number;
  active_students: number;
  completed_students: number;
  dropped_students: number;

  // Performance metrics
  average_score?: number;
  median_score?: number;
  pass_rate?: number;

  // Engagement metrics
  average_time_to_complete?: number; // days
  content_views_per_student?: number;
  lab_completions_per_student?: number;
  quiz_attempts_per_student?: number;

  // Quality ratings (1-5 scale)
  content_rating?: number;
  difficulty_rating?: number;
  workload_rating?: number;

  period_start: string;
  period_end: string;
  calculated_at: string;
}

/**
 * Student Engagement Metrics
 * Aggregated student engagement data for instructor
 */
export interface InstructorStudentEngagement {
  id: string;
  instructor_id: string;
  organization_id?: string;

  // Session metrics
  total_sessions: number;
  average_session_duration?: number; // minutes
  peak_hour?: number; // 0-23

  // Interaction metrics
  total_content_views: number;
  total_lab_sessions: number;
  total_quiz_attempts: number;
  total_forum_posts: number;
  total_questions_asked: number;

  // Response metrics
  questions_answered: number;
  average_response_time?: number; // hours
  response_rate?: number; // percentage

  // Engagement patterns
  most_active_day?: string;
  engagement_distribution?: Record<string, any>;
  activity_heatmap?: Record<string, any>;

  period_start: string;
  period_end: string;
  calculated_at: string;
}

/**
 * Teaching Recommendation
 * AI-generated improvement suggestion
 */
export interface TeachingRecommendation {
  id: string;
  instructor_id: string;
  course_id?: string;

  // Recommendation details
  priority: RecommendationPriority;
  category: RecommendationCategory;
  title: string;
  description: string;
  action_items: string[];
  expected_impact?: string;
  estimated_effort?: string;

  // Status
  status: 'pending' | 'acknowledged' | 'in_progress' | 'completed' | 'dismissed';
  acknowledged_at?: string;
  completed_at?: string;

  generated_at: string;
  expires_at?: string;
}

/**
 * Peer Comparison Data
 * Anonymized benchmarking against peers
 */
export interface PeerComparison {
  id: string;
  instructor_id: string;
  metric_name: string;

  // Instructor's metric
  instructor_score?: number;

  // Peer metrics (anonymized)
  peer_average?: number;
  peer_median?: number;
  peer_min?: number;
  peer_max?: number;

  // Percentile ranking
  percentile_rank?: number; // 0-100
  position_description: string; // "Top 10%", "Above Average", etc.

  period_start: string;
  period_end: string;
}

/**
 * Content Effectiveness Data
 * Breakdown of content performance by type
 */
export interface ContentEffectiveness {
  content_type: string;
  total_items: number;
  average_rating: number;
  completion_rate: number;
  engagement_score: number;
  needs_improvement: boolean;
}

/**
 * Time Range Filter
 * Standard time ranges for analytics queries
 */
export type TimeRange = '7d' | '30d' | '90d' | '1y' | 'all';

/**
 * Instructor Insights Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized instructor analytics API logic
 * - Type-safe interfaces matching backend entities
 * - Supports time-range filtering for trend analysis
 * - Comprehensive error handling
 * - Easy to test and mock
 */
class InstructorInsightsService {
  private baseUrl = '/analytics/instructor';

  /**
   * Get instructor effectiveness metrics
   *
   * @param instructorId - Instructor UUID
   * @param timeRange - Time range for metrics
   * @returns Teaching effectiveness metrics
   */
  async getEffectivenessMetrics(
    instructorId: string,
    timeRange: TimeRange = '30d'
  ): Promise<InstructorEffectivenessMetrics> {
    return await apiClient.get<InstructorEffectivenessMetrics>(
      `${this.baseUrl}/${instructorId}/effectiveness`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get current instructor's effectiveness metrics
   */
  async getMyEffectivenessMetrics(
    timeRange: TimeRange = '30d'
  ): Promise<InstructorEffectivenessMetrics> {
    return await apiClient.get<InstructorEffectivenessMetrics>(
      `${this.baseUrl}/me/effectiveness`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get course performance for specific course
   *
   * @param courseId - Course UUID
   * @param timeRange - Time range for metrics
   * @returns Course performance analytics
   */
  async getCoursePerformance(
    courseId: string,
    timeRange: TimeRange = '30d'
  ): Promise<InstructorCoursePerformance> {
    return await apiClient.get<InstructorCoursePerformance>(
      `${this.baseUrl}/courses/${courseId}/performance`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get all course performances for instructor
   *
   * @param instructorId - Instructor UUID
   * @param timeRange - Time range for metrics
   * @returns Array of course performance data
   */
  async getAllCoursePerformances(
    instructorId: string,
    timeRange: TimeRange = '30d'
  ): Promise<InstructorCoursePerformance[]> {
    return await apiClient.get<InstructorCoursePerformance[]>(
      `${this.baseUrl}/${instructorId}/courses/performance`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get current instructor's course performances
   */
  async getMyCoursePerformances(
    timeRange: TimeRange = '30d'
  ): Promise<InstructorCoursePerformance[]> {
    return await apiClient.get<InstructorCoursePerformance[]>(
      `${this.baseUrl}/me/courses/performance`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get student engagement metrics
   *
   * @param instructorId - Instructor UUID
   * @param timeRange - Time range for metrics
   * @returns Student engagement analytics
   */
  async getStudentEngagement(
    instructorId: string,
    timeRange: TimeRange = '30d'
  ): Promise<InstructorStudentEngagement> {
    return await apiClient.get<InstructorStudentEngagement>(
      `${this.baseUrl}/${instructorId}/engagement`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get current instructor's student engagement
   */
  async getMyStudentEngagement(
    timeRange: TimeRange = '30d'
  ): Promise<InstructorStudentEngagement> {
    return await apiClient.get<InstructorStudentEngagement>(
      `${this.baseUrl}/me/engagement`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get teaching recommendations
   *
   * @param instructorId - Instructor UUID
   * @param category - Optional category filter
   * @param priority - Optional priority filter
   * @returns Array of recommendations
   */
  async getRecommendations(
    instructorId: string,
    category?: RecommendationCategory,
    priority?: RecommendationPriority
  ): Promise<TeachingRecommendation[]> {
    const params: Record<string, string> = {};
    if (category) params.category = category;
    if (priority) params.priority = priority;

    return await apiClient.get<TeachingRecommendation[]>(
      `${this.baseUrl}/${instructorId}/recommendations`,
      { params }
    );
  }

  /**
   * Get current instructor's recommendations
   */
  async getMyRecommendations(
    category?: RecommendationCategory,
    priority?: RecommendationPriority
  ): Promise<TeachingRecommendation[]> {
    const params: Record<string, string> = {};
    if (category) params.category = category;
    if (priority) params.priority = priority;

    return await apiClient.get<TeachingRecommendation[]>(
      `${this.baseUrl}/me/recommendations`,
      { params }
    );
  }

  /**
   * Acknowledge a recommendation
   *
   * @param recommendationId - Recommendation UUID
   */
  async acknowledgeRecommendation(recommendationId: string): Promise<void> {
    await apiClient.post(
      `${this.baseUrl}/recommendations/${recommendationId}/acknowledge`
    );
  }

  /**
   * Mark recommendation as in progress
   *
   * @param recommendationId - Recommendation UUID
   */
  async startRecommendation(recommendationId: string): Promise<void> {
    await apiClient.post(
      `${this.baseUrl}/recommendations/${recommendationId}/start`
    );
  }

  /**
   * Complete a recommendation
   *
   * @param recommendationId - Recommendation UUID
   * @param outcomeData - Optional outcome tracking data
   */
  async completeRecommendation(
    recommendationId: string,
    outcomeData?: Record<string, any>
  ): Promise<void> {
    await apiClient.post(
      `${this.baseUrl}/recommendations/${recommendationId}/complete`,
      outcomeData
    );
  }

  /**
   * Dismiss a recommendation
   *
   * @param recommendationId - Recommendation UUID
   * @param reason - Reason for dismissal
   */
  async dismissRecommendation(
    recommendationId: string,
    reason: string
  ): Promise<void> {
    await apiClient.post(
      `${this.baseUrl}/recommendations/${recommendationId}/dismiss`,
      { reason }
    );
  }

  /**
   * Get peer comparisons
   *
   * @param instructorId - Instructor UUID
   * @param timeRange - Time range for comparison
   * @returns Array of peer comparison data
   */
  async getPeerComparisons(
    instructorId: string,
    timeRange: TimeRange = '30d'
  ): Promise<PeerComparison[]> {
    return await apiClient.get<PeerComparison[]>(
      `${this.baseUrl}/${instructorId}/peer-comparisons`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get current instructor's peer comparisons
   */
  async getMyPeerComparisons(
    timeRange: TimeRange = '30d'
  ): Promise<PeerComparison[]> {
    return await apiClient.get<PeerComparison[]>(
      `${this.baseUrl}/me/peer-comparisons`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get content effectiveness breakdown
   *
   * @param instructorId - Instructor UUID
   * @param courseId - Optional course filter
   * @param timeRange - Time range for analysis
   * @returns Array of content effectiveness data
   */
  async getContentEffectiveness(
    instructorId: string,
    courseId?: string,
    timeRange: TimeRange = '30d'
  ): Promise<ContentEffectiveness[]> {
    const params: Record<string, string> = { range: timeRange };
    if (courseId) params.course_id = courseId;

    return await apiClient.get<ContentEffectiveness[]>(
      `${this.baseUrl}/${instructorId}/content-effectiveness`,
      { params }
    );
  }

  /**
   * Get current instructor's content effectiveness
   */
  async getMyContentEffectiveness(
    courseId?: string,
    timeRange: TimeRange = '30d'
  ): Promise<ContentEffectiveness[]> {
    const params: Record<string, string> = { range: timeRange };
    if (courseId) params.course_id = courseId;

    return await apiClient.get<ContentEffectiveness[]>(
      `${this.baseUrl}/me/content-effectiveness`,
      { params }
    );
  }

  /**
   * Export insights report
   *
   * @param instructorId - Instructor UUID
   * @param format - Report format (pdf, csv, excel)
   * @param timeRange - Time range for report
   * @returns Report blob
   */
  async exportReport(
    instructorId: string,
    format: 'pdf' | 'csv' | 'excel' = 'pdf',
    timeRange: TimeRange = '30d'
  ): Promise<Blob> {
    return await apiClient.get(
      `${this.baseUrl}/${instructorId}/export`,
      {
        params: { format, range: timeRange },
        responseType: 'blob',
      }
    );
  }
}

// Export singleton instance
export const instructorInsightsService = new InstructorInsightsService();

export default instructorInsightsService;
