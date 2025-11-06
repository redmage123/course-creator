/**
 * Analytics Service
 *
 * BUSINESS CONTEXT:
 * Handles analytics and reporting for corporate IT training metrics.
 * Provides data for dashboards, compliance reports, and performance tracking.
 * Supports trainer analytics, student progress tracking, and organizational metrics.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses centralized apiClient with authentication
 * - Provides metrics for all user roles (student, instructor, org_admin, site_admin)
 * - Handles time-series data and aggregated statistics
 * - Integrates with analytics service (port 8004)
 */

import { apiClient } from './apiClient';

/**
 * Student Analytics
 * Metrics for individual student performance
 */
export interface StudentAnalytics {
  student_id: string;
  student_name?: string;
  total_courses: number;
  completed_courses: number;
  active_courses: number;
  average_progress: number;
  average_completion_rate: number;
  total_labs_completed: number;
  certificates_earned: number;
  total_learning_time_hours: number;
  last_activity_date?: string;
  engagement_score: number;
}

/**
 * Training Program Analytics
 * Metrics for course performance and effectiveness
 */
export interface TrainingProgramAnalytics {
  course_id: string;
  course_title?: string;
  total_enrollments: number;
  active_students: number;
  completed_students: number;
  average_completion_rate: number;
  average_progress: number;
  average_rating?: number;
  total_feedback_count: number;
  dropout_rate: number;
  average_completion_time_days: number;
}

/**
 * Instructor Analytics
 * Metrics for corporate trainer performance
 */
export interface InstructorAnalytics {
  instructor_id: string;
  instructor_name?: string;
  total_programs: number;
  published_programs: number;
  total_students: number;
  active_students: number;
  average_completion_rate: number;
  average_course_rating?: number;
  total_content_generated: number;
  engagement_score: number;
}

/**
 * Organization Analytics
 * Metrics for corporate training at organization level
 */
export interface OrganizationAnalytics {
  organization_id: string;
  organization_name?: string;
  total_students: number;
  active_students: number;
  total_trainers: number;
  active_trainers: number;
  total_training_programs: number;
  published_programs: number;
  total_enrollments: number;
  average_completion_rate: number;
  certificates_issued: number;
  compliance_score: number;
  engagement_rate: number;
}

/**
 * Dashboard Statistics
 * Quick stats for dashboard widgets
 */
export interface DashboardStats {
  assigned_courses?: number;
  enrolled_students?: number;
  training_programs?: number;
  total_students?: number;
  total_organizations?: number;
  total_users?: number;
  active_users?: number;
  average_progress?: number;
  completion_rate?: number;
  labs_completed?: number;
  certificates_earned?: number;
  engagement_rate?: number;
  system_uptime?: number;
  monthly_revenue?: number;
}

/**
 * Time Series Data Point
 * For charts and graphs
 */
export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  label?: string;
}

/**
 * Analytics Time Range
 */
export type TimeRange = '7d' | '30d' | '90d' | '1y' | 'all';

/**
 * Analytics Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized analytics API logic
 * - Supports all user roles with role-specific metrics
 * - Type-safe interfaces for dashboard data
 * - Handles time-series data for charts
 */
class AnalyticsService {
  private baseUrl = '/analytics';

  /**
   * Get student analytics (for student dashboard)
   */
  async getStudentAnalytics(studentId: string): Promise<StudentAnalytics> {
    return await apiClient.get<StudentAnalytics>(`${this.baseUrl}/student/${studentId}`);
  }

  /**
   * Get current student's analytics (for logged-in student)
   */
  async getMyAnalytics(): Promise<StudentAnalytics> {
    return await apiClient.get<StudentAnalytics>(`${this.baseUrl}/student/me`);
  }

  /**
   * Get training program analytics (for instructor dashboard)
   */
  async getTrainingProgramAnalytics(courseId: string): Promise<TrainingProgramAnalytics> {
    return await apiClient.get<TrainingProgramAnalytics>(`${this.baseUrl}/course/${courseId}`);
  }

  /**
   * Get instructor analytics (for instructor dashboard)
   */
  async getInstructorAnalytics(instructorId: string): Promise<InstructorAnalytics> {
    return await apiClient.get<InstructorAnalytics>(`${this.baseUrl}/instructor/${instructorId}`);
  }

  /**
   * Get current instructor's analytics
   */
  async getMyInstructorAnalytics(): Promise<InstructorAnalytics> {
    return await apiClient.get<InstructorAnalytics>(`${this.baseUrl}/instructor/me`);
  }

  /**
   * Get organization analytics (for org admin dashboard)
   */
  async getOrganizationAnalytics(organizationId: string): Promise<OrganizationAnalytics> {
    return await apiClient.get<OrganizationAnalytics>(`${this.baseUrl}/organization/${organizationId}`);
  }

  /**
   * Get dashboard stats for current user
   * (Returns role-appropriate stats based on user role)
   */
  async getDashboardStats(): Promise<DashboardStats> {
    return await apiClient.get<DashboardStats>(`${this.baseUrl}/dashboard/stats`);
  }

  /**
   * Get platform-wide analytics (for site admin dashboard)
   */
  async getPlatformAnalytics(): Promise<OrganizationAnalytics> {
    return await apiClient.get<OrganizationAnalytics>(`${this.baseUrl}/platform`);
  }

  /**
   * Get progress over time (for charts)
   */
  async getProgressTimeSeries(
    entityType: 'student' | 'course' | 'organization' | 'platform',
    entityId: string,
    timeRange: TimeRange = '30d'
  ): Promise<TimeSeriesDataPoint[]> {
    return await apiClient.get<TimeSeriesDataPoint[]>(
      `${this.baseUrl}/${entityType}/${entityId}/progress-timeline`,
      { params: { range: timeRange } }
    );
  }

  /**
   * Get enrollment trends over time
   */
  async getEnrollmentTrends(
    organizationId?: string,
    timeRange: TimeRange = '30d'
  ): Promise<TimeSeriesDataPoint[]> {
    const params = { range: timeRange, organization_id: organizationId };
    return await apiClient.get<TimeSeriesDataPoint[]>(
      `${this.baseUrl}/enrollments/trends`,
      { params }
    );
  }

  /**
   * Get completion trends over time
   */
  async getCompletionTrends(
    organizationId?: string,
    timeRange: TimeRange = '30d'
  ): Promise<TimeSeriesDataPoint[]> {
    const params = { range: timeRange, organization_id: organizationId };
    return await apiClient.get<TimeSeriesDataPoint[]>(
      `${this.baseUrl}/completions/trends`,
      { params }
    );
  }

  /**
   * Get compliance report (for org admin)
   */
  async getComplianceReport(organizationId: string): Promise<any> {
    return await apiClient.get(`${this.baseUrl}/organization/${organizationId}/compliance`);
  }

  /**
   * Export analytics report
   */
  async exportReport(
    reportType: 'student' | 'instructor' | 'organization' | 'platform',
    entityId: string,
    format: 'pdf' | 'csv' | 'excel' = 'pdf'
  ): Promise<Blob> {
    return await apiClient.get(
      `${this.baseUrl}/${reportType}/${entityId}/export`,
      {
        params: { format },
        responseType: 'blob',
      }
    );
  }
}

// Export singleton instance
export const analyticsService = new AnalyticsService();
