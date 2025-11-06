/**
 * useAnalytics Hook
 *
 * Custom hook for fetching and managing analytics data.
 * Handles different view types (student, course, instructor) and time ranges.
 *
 * BUSINESS CONTEXT:
 * Centralizes analytics data fetching logic and provides reactive state
 * management for dashboard components.
 *
 * @module features/analytics/hooks/useAnalytics
 */

import { useState, useEffect } from 'react';
import { analyticsService } from '../services/analyticsService';
import type { AnalyticsViewType } from '../AnalyticsDashboard';
import type { EngagementDataPoint } from '../components/EngagementChart';
import type { ProgressDataPoint } from '../components/ProgressChart';
import type { QuizPerformanceDataPoint } from '../components/QuizPerformanceChart';
import type { SkillProficiency } from '../components/LabProficiencyChart';
import type { RiskAssessment } from '../components/RiskAssessmentCard';

export interface EngagementData {
  score: number;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
  history: EngagementDataPoint[];
}

export interface ProgressData {
  completion_percentage: number;
  completed_items: number;
  total_items: number;
  timeline: ProgressDataPoint[];
}

export interface QuizPerformanceData {
  average_score: number;
  quizzes_taken: number;
  quizzes_passed: number;
  history: QuizPerformanceDataPoint[];
}

export interface LabProficiencyData {
  proficiency_score: number;
  labs_completed: number;
  skills: SkillProficiency[];
}

export interface CourseAnalyticsData {
  total_students: number;
  active_students: number;
  completion_rate: number;
  average_grade: number;
}

export interface UseAnalyticsResult {
  engagement: EngagementData | null;
  progress: ProgressData | null;
  quizPerformance: QuizPerformanceData | null;
  labProficiency: LabProficiencyData | null;
  riskAssessment: RiskAssessment | null;
  courseAnalytics: CourseAnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * useAnalytics Hook
 *
 * WHY THIS APPROACH:
 * - Encapsulates analytics data fetching logic
 * - Manages loading and error states
 * - Provides refetch capability for manual updates
 * - Automatically refetches when parameters change
 * - Type-safe return values for dashboard components
 */
export const useAnalytics = (
  viewType: AnalyticsViewType,
  studentId: string | undefined,
  courseId: string | undefined,
  timeRange: 'week' | 'month' | 'quarter' | 'year'
): UseAnalyticsResult => {
  const [engagement, setEngagement] = useState<EngagementData | null>(null);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [quizPerformance, setQuizPerformance] = useState<QuizPerformanceData | null>(null);
  const [labProficiency, setLabProficiency] = useState<LabProficiencyData | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
  const [courseAnalytics, setCourseAnalytics] = useState<CourseAnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch based on view type
      switch (viewType) {
        case 'student':
          if (!studentId || !courseId) {
            throw new Error('Student ID and Course ID required for student view');
          }

          // Fetch student-specific analytics
          const [
            engagementData,
            progressData,
            quizData,
            labData,
          ] = await Promise.all([
            analyticsService.getEngagement(studentId, courseId, timeRange),
            analyticsService.getProgress(studentId, courseId),
            analyticsService.getQuizPerformance(studentId, courseId),
            analyticsService.getLabProficiency(studentId, courseId)
          ]);

          setEngagement(engagementData);
          setProgress(progressData);
          setQuizPerformance(quizData);
          setLabProficiency(labData);
          break;

        case 'instructor':
          if (!studentId || !courseId) {
            throw new Error('Student ID and Course ID required for instructor view');
          }

          // Fetch instructor view (same as student but with risk assessment)
          const [
            instrEngagement,
            instrProgress,
            instrQuiz,
            instrLab,
            riskData
          ] = await Promise.all([
            analyticsService.getEngagement(studentId, courseId, timeRange),
            analyticsService.getProgress(studentId, courseId),
            analyticsService.getQuizPerformance(studentId, courseId),
            analyticsService.getLabProficiency(studentId, courseId),
            analyticsService.getRiskAssessment(studentId, courseId)
          ]);

          setEngagement(instrEngagement);
          setProgress(instrProgress);
          setQuizPerformance(instrQuiz);
          setLabProficiency(instrLab);
          setRiskAssessment(riskData);
          break;

        case 'course':
          if (!courseId) {
            throw new Error('Course ID required for course view');
          }

          // Fetch course-level analytics
          const courseData = await analyticsService.getCourseAnalytics(courseId, timeRange);
          setCourseAnalytics(courseData);
          break;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load analytics';
      setError(message);
      console.error('Analytics fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch on mount and when parameters change
  useEffect(() => {
    fetchAnalytics();
  }, [viewType, studentId, courseId, timeRange]);

  return {
    engagement,
    progress,
    quizPerformance,
    labProficiency,
    riskAssessment,
    courseAnalytics,
    isLoading,
    error,
    refetch: fetchAnalytics
  };
};

export default useAnalytics;
