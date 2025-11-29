/**
 * Instructor Insights Dashboard
 *
 * Comprehensive analytics dashboard for instructors to track teaching
 * effectiveness, student engagement, and receive improvement recommendations.
 *
 * BUSINESS CONTEXT:
 * Empowers instructors with actionable data to improve teaching quality.
 * Displays effectiveness metrics, course performance, student engagement,
 * content effectiveness, and AI-powered recommendations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses useInstructorInsights hook for data fetching
 * - Time range selector for historical analysis
 * - Responsive grid layout with multiple widgets
 * - Loading and error states
 *
 * @module features/instructor-insights/InstructorInsightsDashboard
 */

import React, { useState } from 'react';
import { useInstructorInsights } from './hooks/useInstructorInsights';
import { ContentEffectivenessChart } from './components/ContentEffectivenessChart';
import { StudentEngagementWidget } from './components/StudentEngagementWidget';
import { CoursePerformanceWidget } from './components/CoursePerformanceWidget';
import { TeachingRecommendationsWidget } from './components/TeachingRecommendationsWidget';
import type { TimeRange } from '@services/instructorInsightsService';
import styles from './InstructorInsightsDashboard.module.css';

/**
 * Dashboard Props
 */
export interface InstructorInsightsDashboardProps {
  /** Optional instructor ID (defaults to current user) */
  instructorId?: string;
  /** Optional course filter */
  courseId?: string;
}

/**
 * Instructor Insights Dashboard Component
 *
 * WHY THIS APPROACH:
 * - Single-page dashboard with all key metrics
 * - Time range selector for trend analysis
 * - Modular widget-based layout for maintainability
 * - Responsive grid adapts to screen size
 * - Clear loading and error states
 */
export const InstructorInsightsDashboard: React.FC<InstructorInsightsDashboardProps> = ({
  instructorId,
  courseId,
}) => {
  // Time range state
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');

  // Fetch instructor insights data
  const {
    effectiveness,
    coursePerformances,
    engagement,
    recommendations,
    peerComparisons,
    contentEffectiveness,
    isLoading,
    error,
    refetch,
    acknowledgeRecommendation,
    startRecommendation,
    completeRecommendation,
    dismissRecommendation,
  } = useInstructorInsights(instructorId, courseId, timeRange);

  /**
   * Handle time range change
   */
  const handleTimeRangeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setTimeRange(event.target.value as TimeRange);
  };

  /**
   * Handle refresh
   */
  const handleRefresh = () => {
    refetch();
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.dashboard}>
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Loading instructor insights...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.dashboard}>
        <div className={styles.errorContainer}>
          <h2>Error Loading Insights</h2>
          <p>{error}</p>
          <button onClick={handleRefresh} className={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Instructor Insights</h1>
          <p className={styles.subtitle}>
            Track your teaching effectiveness and receive personalized improvement recommendations
          </p>
        </div>

        {/* Controls */}
        <div className={styles.controls}>
          <label htmlFor="timeRange" className={styles.label}>
            Time Range:
          </label>
          <select
            id="timeRange"
            value={timeRange}
            onChange={handleTimeRangeChange}
            className={styles.select}
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="1y">Last Year</option>
            <option value="all">All Time</option>
          </select>

          <button onClick={handleRefresh} className={styles.refreshButton} title="Refresh data">
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Effectiveness Summary Cards */}
      {effectiveness && (
        <div className={styles.summaryCards}>
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ color: '#4caf50' }}>
              ⭐
            </div>
            <div className={styles.cardContent}>
              <h3 className={styles.cardTitle}>Overall Rating</h3>
              <div className={styles.cardValue}>
                {effectiveness.overall_rating?.toFixed(1) || 'N/A'}
                <span className={styles.cardSubvalue}> / 5.0</span>
              </div>
              {effectiveness.rating_trend && (
                <div className={`${styles.trend} ${styles[effectiveness.rating_trend]}`}>
                  {effectiveness.rating_trend === 'improving' && '↑'}
                  {effectiveness.rating_trend === 'declining' && '↓'}
                  {effectiveness.rating_trend === 'stable' && '→'}
                  {' '}{effectiveness.rating_trend}
                </div>
              )}
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ color: '#2196f3' }}>
              👥
            </div>
            <div className={styles.cardContent}>
              <h3 className={styles.cardTitle}>Students Taught</h3>
              <div className={styles.cardValue}>{effectiveness.total_students_taught}</div>
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ color: '#ff9800' }}>
              📈
            </div>
            <div className={styles.cardContent}>
              <h3 className={styles.cardTitle}>Completion Rate</h3>
              <div className={styles.cardValue}>
                {effectiveness.course_completion_rate?.toFixed(1) || 'N/A'}
                <span className={styles.cardSubvalue}>%</span>
              </div>
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ color: '#9c27b0' }}>
              🎯
            </div>
            <div className={styles.cardContent}>
              <h3 className={styles.cardTitle}>Engagement Score</h3>
              <div className={styles.cardValue}>
                {effectiveness.engagement_score?.toFixed(0) || 'N/A'}
                <span className={styles.cardSubvalue}> / 100</span>
              </div>
              {effectiveness.engagement_trend && (
                <div className={`${styles.trend} ${styles[effectiveness.engagement_trend]}`}>
                  {effectiveness.engagement_trend === 'improving' && '↑'}
                  {effectiveness.engagement_trend === 'declining' && '↓'}
                  {effectiveness.engagement_trend === 'stable' && '→'}
                  {' '}{effectiveness.engagement_trend}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Widgets Grid */}
      <div className={styles.widgetsGrid}>
        {/* Teaching Recommendations */}
        <div className={styles.widgetFull}>
          <TeachingRecommendationsWidget
            recommendations={recommendations}
            onAcknowledge={acknowledgeRecommendation}
            onStart={startRecommendation}
            onComplete={completeRecommendation}
            onDismiss={dismissRecommendation}
          />
        </div>

        {/* Course Performance */}
        <div className={styles.widgetHalf}>
          <CoursePerformanceWidget
            coursePerformances={coursePerformances}
            peerComparisons={peerComparisons}
          />
        </div>

        {/* Student Engagement */}
        <div className={styles.widgetHalf}>
          <StudentEngagementWidget engagement={engagement} />
        </div>

        {/* Content Effectiveness */}
        <div className={styles.widgetFull}>
          <ContentEffectivenessChart
            contentEffectiveness={contentEffectiveness}
            timeRange={timeRange}
          />
        </div>
      </div>
    </div>
  );
};

export default InstructorInsightsDashboard;
