/**
 * Analytics Service API Client
 *
 * Centralized API client for analytics operations.
 * Communicates with analytics service (port 8000).
 *
 * BUSINESS CONTEXT:
 * Provides type-safe interface to analytics backend, handling
 * data fetching for engagement, progress, quiz performance, and lab proficiency.
 *
 * @module features/analytics/services/analyticsService
 */

import type { EngagementData, ProgressData, QuizPerformanceData, LabProficiencyData, CourseAnalyticsData } from '../hooks/useAnalytics';
import type { RiskAssessment } from '../components/RiskAssessmentCard';

const ANALYTICS_API_BASE = 'https://176.9.99.103:8000/api/v1';

/**
 * Custom error class for analytics service errors
 */
export class AnalyticsServiceError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'AnalyticsServiceError';
  }
}

/**
 * Handle API response and errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: 'An error occurred'
    }));

    throw new AnalyticsServiceError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData.detail
    );
  }

  return response.json();
}

/**
 * Analytics Service
 */
export const analyticsService = {
  /**
   * Get student engagement data
   */
  async getEngagement(
    studentId: string,
    courseId: string,
    timeRange: 'week' | 'month' | 'quarter' | 'year'
  ): Promise<EngagementData> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/engagement?time_range=${timeRange}`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get student progress data
   */
  async getProgress(
    studentId: string,
    courseId: string
  ): Promise<ProgressData> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/progress-summary`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get quiz performance data
   */
  async getQuizPerformance(
    studentId: string,
    courseId: string
  ): Promise<QuizPerformanceData> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/quiz-performance`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get lab proficiency data
   */
  async getLabProficiency(
    studentId: string,
    courseId: string
  ): Promise<LabProficiencyData> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/lab-proficiency`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get risk assessment for student (instructor view)
   */
  async getRiskAssessment(
    studentId: string,
    courseId: string
  ): Promise<RiskAssessment> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/students/${studentId}/courses/${courseId}/risk-assessment`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get course-level analytics
   */
  async getCourseAnalytics(
    courseId: string,
    timeRange: 'week' | 'month' | 'quarter' | 'year'
  ): Promise<CourseAnalyticsData> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/courses/${courseId}/analytics?time_range=${timeRange}`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Record student activity
   */
  async recordActivity(
    studentId: string,
    courseId: string,
    activityType: string,
    metadata?: Record<string, any>
  ): Promise<void> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/activities`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          activity_type: activityType,
          timestamp: new Date().toISOString(),
          metadata
        })
      }
    );
    return handleResponse(response);
  },

  /**
   * Record quiz performance
   */
  async recordQuizPerformance(
    studentId: string,
    courseId: string,
    quizId: string,
    score: number,
    passed: boolean
  ): Promise<void> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/quiz-performance`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          quiz_id: quizId,
          score,
          passed,
          timestamp: new Date().toISOString()
        })
      }
    );
    return handleResponse(response);
  },

  /**
   * Record lab usage
   */
  async recordLabUsage(
    studentId: string,
    courseId: string,
    labId: string,
    duration: number,
    completed: boolean
  ): Promise<void> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/lab-usage`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          lab_id: labId,
          duration_seconds: duration,
          completed,
          timestamp: new Date().toISOString()
        })
      }
    );
    return handleResponse(response);
  },

  /**
   * Update progress
   */
  async updateProgress(
    studentId: string,
    courseId: string,
    completedItems: number,
    totalItems: number
  ): Promise<void> {
    const response = await fetch(
      `${ANALYTICS_API_BASE}/progress`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          completed_items: completedItems,
          total_items: totalItems,
          completion_percentage: (completedItems / totalItems) * 100,
          timestamp: new Date().toISOString()
        })
      }
    );
    return handleResponse(response);
  }
};

export default analyticsService;
