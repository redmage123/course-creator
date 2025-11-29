/**
 * useInstructorInsights Hook
 *
 * Custom hook for fetching and managing instructor insights data.
 * Handles loading states, error handling, and automatic data refetching.
 *
 * BUSINESS CONTEXT:
 * Centralizes instructor analytics data fetching logic and provides
 * reactive state management for instructor dashboard components.
 * Enables instructors to track their teaching effectiveness and
 * receive actionable improvement recommendations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches effectiveness metrics, course performance, engagement data
 * - Manages loading and error states
 * - Automatically refetches when parameters change
 * - Provides manual refetch capability
 * - Type-safe return values
 *
 * @module features/instructor-insights/hooks/useInstructorInsights
 */

import { useState, useEffect } from 'react';
import { instructorInsightsService } from '@services/instructorInsightsService';
import type {
  InstructorEffectivenessMetrics,
  InstructorCoursePerformance,
  InstructorStudentEngagement,
  TeachingRecommendation,
  PeerComparison,
  ContentEffectiveness,
  TimeRange,
} from '@services/instructorInsightsService';

/**
 * Hook return type
 * All data fetched for instructor insights dashboard
 */
export interface UseInstructorInsightsResult {
  // Core metrics
  effectiveness: InstructorEffectivenessMetrics | null;
  coursePerformances: InstructorCoursePerformance[];
  engagement: InstructorStudentEngagement | null;
  recommendations: TeachingRecommendation[];
  peerComparisons: PeerComparison[];
  contentEffectiveness: ContentEffectiveness[];

  // State management
  isLoading: boolean;
  error: string | null;

  // Actions
  refetch: () => Promise<void>;
  acknowledgeRecommendation: (id: string) => Promise<void>;
  startRecommendation: (id: string) => Promise<void>;
  completeRecommendation: (id: string, outcome?: Record<string, any>) => Promise<void>;
  dismissRecommendation: (id: string, reason: string) => Promise<void>;
}

/**
 * useInstructorInsights Hook
 *
 * WHY THIS APPROACH:
 * - Encapsulates all instructor insights data fetching logic
 * - Manages loading and error states centrally
 * - Provides refetch capability for manual updates
 * - Automatically refetches when time range changes
 * - Type-safe return values for dashboard components
 * - Handles recommendation actions (acknowledge, complete, dismiss)
 *
 * @param instructorId - Instructor UUID (optional, defaults to current user)
 * @param courseId - Optional course filter
 * @param timeRange - Time range for analytics
 * @returns Instructor insights data and state
 */
export const useInstructorInsights = (
  instructorId?: string,
  courseId?: string,
  timeRange: TimeRange = '30d'
): UseInstructorInsightsResult => {
  // State for all data types
  const [effectiveness, setEffectiveness] = useState<InstructorEffectivenessMetrics | null>(null);
  const [coursePerformances, setCoursePerformances] = useState<InstructorCoursePerformance[]>([]);
  const [engagement, setEngagement] = useState<InstructorStudentEngagement | null>(null);
  const [recommendations, setRecommendations] = useState<TeachingRecommendation[]>([]);
  const [peerComparisons, setPeerComparisons] = useState<PeerComparison[]>([]);
  const [contentEffectiveness, setContentEffectiveness] = useState<ContentEffectiveness[]>([]);

  // Loading and error state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch all instructor insights data
   *
   * WHAT: Fetches effectiveness, performance, engagement, recommendations
   * WHERE: Called on mount and when parameters change
   * WHY: Provides complete instructor analytics in one operation
   */
  const fetchInsights = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Determine if we're fetching for current user or specific instructor
      const useMe = !instructorId;

      // Fetch all data in parallel for performance
      const [
        effectivenessData,
        performanceData,
        engagementData,
        recommendationsData,
        peerComparisonsData,
        contentEffectivenessData,
      ] = await Promise.all([
        // Effectiveness metrics
        useMe
          ? instructorInsightsService.getMyEffectivenessMetrics(timeRange)
          : instructorInsightsService.getEffectivenessMetrics(instructorId!, timeRange),

        // Course performances
        useMe
          ? instructorInsightsService.getMyCoursePerformances(timeRange)
          : instructorInsightsService.getAllCoursePerformances(instructorId!, timeRange),

        // Student engagement
        useMe
          ? instructorInsightsService.getMyStudentEngagement(timeRange)
          : instructorInsightsService.getStudentEngagement(instructorId!, timeRange),

        // Recommendations
        useMe
          ? instructorInsightsService.getMyRecommendations()
          : instructorInsightsService.getRecommendations(instructorId!),

        // Peer comparisons
        useMe
          ? instructorInsightsService.getMyPeerComparisons(timeRange)
          : instructorInsightsService.getPeerComparisons(instructorId!, timeRange),

        // Content effectiveness
        useMe
          ? instructorInsightsService.getMyContentEffectiveness(courseId, timeRange)
          : instructorInsightsService.getContentEffectiveness(instructorId!, courseId, timeRange),
      ]);

      // Update all state
      setEffectiveness(effectivenessData);
      setCoursePerformances(performanceData);
      setEngagement(engagementData);
      setRecommendations(recommendationsData);
      setPeerComparisons(peerComparisonsData);
      setContentEffectiveness(contentEffectivenessData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load instructor insights';
      setError(message);
      console.error('Instructor insights fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Acknowledge a recommendation
   *
   * WHAT: Mark recommendation as acknowledged
   * WHERE: Called from recommendations widget
   * WHY: Track instructor engagement with recommendations
   */
  const acknowledgeRecommendation = async (id: string): Promise<void> => {
    try {
      await instructorInsightsService.acknowledgeRecommendation(id);
      // Update local state
      setRecommendations((prev) =>
        prev.map((rec) =>
          rec.id === id
            ? { ...rec, status: 'acknowledged', acknowledged_at: new Date().toISOString() }
            : rec
        )
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to acknowledge recommendation';
      console.error('Error acknowledging recommendation:', err);
      throw new Error(message);
    }
  };

  /**
   * Start working on a recommendation
   *
   * WHAT: Mark recommendation as in progress
   * WHERE: Called from recommendations widget
   * WHY: Track active improvement efforts
   */
  const startRecommendation = async (id: string): Promise<void> => {
    try {
      await instructorInsightsService.startRecommendation(id);
      // Update local state
      setRecommendations((prev) =>
        prev.map((rec) =>
          rec.id === id ? { ...rec, status: 'in_progress' } : rec
        )
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start recommendation';
      console.error('Error starting recommendation:', err);
      throw new Error(message);
    }
  };

  /**
   * Complete a recommendation
   *
   * WHAT: Mark recommendation as completed
   * WHERE: Called from recommendations widget
   * WHY: Track completed improvements and measure impact
   */
  const completeRecommendation = async (
    id: string,
    outcome?: Record<string, any>
  ): Promise<void> => {
    try {
      await instructorInsightsService.completeRecommendation(id, outcome);
      // Update local state
      setRecommendations((prev) =>
        prev.map((rec) =>
          rec.id === id
            ? { ...rec, status: 'completed', completed_at: new Date().toISOString() }
            : rec
        )
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to complete recommendation';
      console.error('Error completing recommendation:', err);
      throw new Error(message);
    }
  };

  /**
   * Dismiss a recommendation
   *
   * WHAT: Dismiss recommendation with reason
   * WHERE: Called from recommendations widget
   * WHY: Allow instructors to hide irrelevant recommendations
   */
  const dismissRecommendation = async (id: string, reason: string): Promise<void> => {
    try {
      await instructorInsightsService.dismissRecommendation(id, reason);
      // Remove from local state
      setRecommendations((prev) => prev.filter((rec) => rec.id !== id));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to dismiss recommendation';
      console.error('Error dismissing recommendation:', err);
      throw new Error(message);
    }
  };

  // Fetch on mount and when parameters change
  useEffect(() => {
    fetchInsights();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [instructorId, courseId, timeRange]);

  return {
    // Data
    effectiveness,
    coursePerformances,
    engagement,
    recommendations,
    peerComparisons,
    contentEffectiveness,

    // State
    isLoading,
    error,

    // Actions
    refetch: fetchInsights,
    acknowledgeRecommendation,
    startRecommendation,
    completeRecommendation,
    dismissRecommendation,
  };
};

export default useInstructorInsights;
