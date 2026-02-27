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

      // Helper to validate API responses are JSON objects (not HTML fallback)
      const isValidResponse = (data: unknown): boolean =>
        data !== null && data !== undefined && typeof data === 'object' && !Array.isArray(data);
      const isValidArrayResponse = (data: unknown): data is unknown[] =>
        Array.isArray(data);

      // Fetch summary first - needed for student_id when no studentId prop
      let summaryData: LearningAnalyticsSummary | null = null;
      try {
        const raw = studentId
          ? await learningAnalyticsService.getStudentLearningAnalytics(studentId)
          : await learningAnalyticsService.getMyLearningAnalytics();
        summaryData = isValidResponse(raw) ? raw : null;
      } catch {
        summaryData = null;
      }

      // Determine effective student ID for subsequent calls
      const effectiveId = studentId || (summaryData?.student_id as string | undefined);

      // Fetch remaining data in parallel (only if we have a student ID)
      let pathsData: LearningPathProgress[] = [];
      let skillsData: SkillMastery[] = [];
      let sessionsData: SessionActivity[] = [];
      let progressData: LearningProgressDataPoint[] = [];

      if (effectiveId) {
        const [rawPaths, rawSkills, rawSessions, rawProgress] = await Promise.allSettled([
          learningAnalyticsService.getStudentLearningPaths(effectiveId),
          learningAnalyticsService.getSkillMastery(effectiveId, courseId),
          learningAnalyticsService.getSessionActivity(effectiveId, timeRange),
          learningAnalyticsService.getLearningProgressTimeSeries(effectiveId, courseId, timeRange),
        ]);

        pathsData = rawPaths.status === 'fulfilled' && isValidArrayResponse(rawPaths.value)
          ? rawPaths.value as LearningPathProgress[] : [];
        skillsData = rawSkills.status === 'fulfilled' && isValidArrayResponse(rawSkills.value)
          ? rawSkills.value as SkillMastery[] : [];
        sessionsData = rawSessions.status === 'fulfilled' && isValidArrayResponse(rawSessions.value)
          ? rawSessions.value as SessionActivity[] : [];
        progressData = rawProgress.status === 'fulfilled' && isValidArrayResponse(rawProgress.value)
          ? rawProgress.value as LearningProgressDataPoint[] : [];
      }

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
