/**
 * useLearningAnalytics Hook
 *
 * WHAT: Custom hook for fetching and managing learning analytics data
 * WHERE: Learning Analytics Dashboard component
 * WHY: Centralizes data fetching logic and provides reactive state management
 *
 * BUSINESS CONTEXT:
 * Manages comprehensive learning analytics data:
 * - Learning path progress
 * - Skill mastery levels
 * - Session activity tracking
 * - Progress time series
 * - Overall analytics summary
 *
 * TECHNICAL IMPLEMENTATION:
 * - React hooks for state management
 * - Automatic data fetching on mount and parameter changes
 * - Error handling with user-friendly messages
 * - Loading states for smooth UX
 * - Refetch capability for manual updates
 * - Parallel API calls for optimal performance
 *
 * @module features/learning-analytics/hooks/useLearningAnalytics
 */

import { useState, useEffect } from 'react';
import {
  learningAnalyticsService,
  type LearningAnalyticsSummary,
  type LearningPathProgress,
  type SkillMastery,
  type SessionActivity,
  type LearningProgressDataPoint,
  type TimeRange,
} from '../../../services/learningAnalyticsService';

/**
 * Hook Return Interface
 *
 * WHAT: Defines return type for useLearningAnalytics hook
 * WHERE: Type definitions for hook consumers
 * WHY: Ensures type safety and code clarity
 */
export interface UseLearningAnalyticsResult {
  summary: LearningAnalyticsSummary | null;
  learningPaths: LearningPathProgress[] | null;
  skillMastery: SkillMastery[] | null;
  sessionActivity: SessionActivity[] | null;
  progressTimeSeries: LearningProgressDataPoint[] | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * useLearningAnalytics Hook
 *
 * WHY THIS APPROACH:
 * - Encapsulates complex data fetching logic
 * - Manages loading and error states
 * - Provides refetch capability for manual updates
 * - Automatically refetches when parameters change
 * - Type-safe return values for dashboard components
 * - Parallel API calls for optimal performance
 *
 * @param studentId - Student ID (optional, uses current user if not provided)
 * @param courseId - Course ID for filtering (optional)
 * @param timeRange - Time range for analytics data
 * @returns Learning analytics data and state management functions
 */
export const useLearningAnalytics = (
  studentId?: string,
  courseId?: string,
  timeRange: TimeRange = '30d'
): UseLearningAnalyticsResult => {
  const [summary, setSummary] = useState<LearningAnalyticsSummary | null>(null);
  const [learningPaths, setLearningPaths] = useState<LearningPathProgress[] | null>(null);
  const [skillMastery, setSkillMastery] = useState<SkillMastery[] | null>(null);
  const [sessionActivity, setSessionActivity] = useState<SessionActivity[] | null>(null);
  const [progressTimeSeries, setProgressTimeSeries] = useState<LearningProgressDataPoint[] | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch Learning Analytics Data
   *
   * WHAT: Main data fetching function
   * WHERE: Called on mount and parameter changes
   * WHY: Retrieves all required analytics data from backend
   *
   * TECHNICAL NOTES:
   * - Uses Promise.all for parallel API calls
   * - Handles errors gracefully with user-friendly messages
   * - Sets loading states appropriately
   * - Supports both authenticated user and specific student ID
   */
  const fetchLearningAnalytics = async () => {
    try {
      setIsLoading(true);
      setError(null);

      /**
       * Parallel Data Fetching
       *
       * WHAT: Fetches all analytics data concurrently
       * WHERE: API service calls
       * WHY: Reduces total loading time vs sequential calls
       */
      const [
        summaryData,
        pathsData,
        skillsData,
        sessionsData,
        progressData,
      ] = await Promise.all([
        // Summary analytics (overall metrics)
        studentId
          ? learningAnalyticsService.getStudentLearningAnalytics(studentId)
          : learningAnalyticsService.getMyLearningAnalytics(),

        // Learning paths progress
        studentId
          ? learningAnalyticsService.getStudentLearningPaths(studentId)
          : learningAnalyticsService
              .getMyLearningAnalytics()
              .then((data) =>
                learningAnalyticsService.getStudentLearningPaths(data.student_id)
              ),

        // Skill mastery data
        studentId
          ? learningAnalyticsService.getSkillMastery(studentId, courseId)
          : learningAnalyticsService
              .getMyLearningAnalytics()
              .then((data) => learningAnalyticsService.getSkillMastery(data.student_id, courseId)),

        // Session activity
        studentId
          ? learningAnalyticsService.getSessionActivity(studentId, timeRange)
          : learningAnalyticsService
              .getMyLearningAnalytics()
              .then((data) =>
                learningAnalyticsService.getSessionActivity(data.student_id, timeRange)
              ),

        // Progress time series
        studentId
          ? learningAnalyticsService.getLearningProgressTimeSeries(
              studentId,
              courseId,
              timeRange
            )
          : learningAnalyticsService
              .getMyLearningAnalytics()
              .then((data) =>
                learningAnalyticsService.getLearningProgressTimeSeries(
                  data.student_id,
                  courseId,
                  timeRange
                )
              ),
      ]);

      // Update state with fetched data
      setSummary(summaryData);
      setLearningPaths(pathsData);
      setSkillMastery(skillsData);
      setSessionActivity(sessionsData);
      setProgressTimeSeries(progressData);
    } catch (err) {
      /**
       * Error Handling
       *
       * WHAT: Converts errors to user-friendly messages
       * WHERE: Catch block for all API calls
       * WHY: Provides actionable feedback to users
       */
      const message = err instanceof Error ? err.message : 'Failed to load learning analytics';
      setError(message);
      console.error('Learning analytics fetch error:', err);

      // Reset data on error
      setSummary(null);
      setLearningPaths(null);
      setSkillMastery(null);
      setSessionActivity(null);
      setProgressTimeSeries(null);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Effect Hook - Auto Fetch on Mount/Parameter Change
   *
   * WHAT: Triggers data fetch when dependencies change
   * WHERE: React useEffect hook
   * WHY: Keeps data synchronized with component parameters
   */
  useEffect(() => {
    fetchLearningAnalytics();
  }, [studentId, courseId, timeRange]);

  /**
   * Return Hook Results
   *
   * WHAT: Provides analytics data and control functions
   * WHERE: Hook return value
   * WHY: Enables consuming components to access data and trigger refetch
   */
  return {
    summary,
    learningPaths,
    skillMastery,
    sessionActivity,
    progressTimeSeries,
    isLoading,
    error,
    refetch: fetchLearningAnalytics,
  };
};

export default useLearningAnalytics;
