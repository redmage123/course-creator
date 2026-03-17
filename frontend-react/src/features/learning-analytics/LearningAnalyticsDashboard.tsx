/**
 * Learning Analytics Dashboard Component
 *
 * WHAT: Main dashboard for comprehensive learning analytics
 * WHERE: Accessible from student, instructor, and admin dashboards
 * WHY: Provides unified view of learning progress, skill mastery, and engagement metrics
 *
 * BUSINESS CONTEXT:
 * Comprehensive learning analytics interface showing:
 * - Learning path progress and trajectory
 * - Skill mastery levels with spaced repetition recommendations
 * - Session activity and engagement patterns
 * - Progress charts and time-series visualizations
 * - Role-appropriate analytics (student/instructor/admin views)
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses custom hook for data fetching and state management
 * - Responsive grid layout for widget placement
 * - Chart.js for interactive visualizations
 * - CSS modules for scoped styling
 * - Loading and error states with user-friendly messages
 *
 * @module features/learning-analytics/LearningAnalyticsDashboard
 */

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useLearningAnalytics } from './hooks/useLearningAnalytics';
import { LearningProgressChart } from './components/LearningProgressChart';
import { SkillMasteryWidget } from './components/SkillMasteryWidget';
import { LearningPathProgress } from './components/LearningPathProgress';
import { SessionActivityWidget } from './components/SessionActivityWidget';
import type { TimeRange } from '../../services/learningAnalyticsService';
import styles from './LearningAnalyticsDashboard.module.css';

/**
 * View Type Enum
 * Determines which analytics perspective to display
 */
export type LearningAnalyticsViewType = 'student' | 'instructor' | 'org_admin';

/**
 * Dashboard Props Interface
 */
export interface LearningAnalyticsDashboardProps {
  viewType: LearningAnalyticsViewType;
  studentId?: string;
  courseId?: string;
  organizationId?: string;
}

/**
 * Learning Analytics Dashboard Component
 *
 * WHY THIS APPROACH:
 * - Modular widget design for flexible dashboard composition
 * - Time range selector for adjustable analytics periods
 * - Role-based view customization
 * - Loading states prevent premature rendering
 * - Error boundaries handle API failures gracefully
 */
export const LearningAnalyticsDashboard: React.FC<LearningAnalyticsDashboardProps> = ({
  viewType,
  studentId,
  courseId,
  organizationId,
}) => {
  const { studentId: paramStudentId, courseId: paramCourseId } = useParams<{
    studentId?: string;
    courseId?: string;
  }>();

  // Use prop values or fall back to URL params
  const effectiveStudentId = studentId || paramStudentId;
  const effectiveCourseId = courseId || paramCourseId;

  const [timeRange, setTimeRange] = useState<TimeRange>('30d');

  const {
    summary,
    learningPaths,
    skillMastery,
    sessionActivity,
    progressTimeSeries,
    isLoading,
    error,
    refetch,
  } = useLearningAnalytics(effectiveStudentId, effectiveCourseId, timeRange);

  /**
   * Loading State Handler
   *
   * WHAT: Displays loading spinner while data fetches
   * WHERE: Shown during initial load and refetch operations
   * WHY: Provides feedback to prevent user confusion
   */
  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} aria-label="Loading analytics"></div>
        <p>Loading learning analytics...</p>
      </div>
    );
  }

  /**
   * Error State Handler
   *
   * WHAT: Displays error message if data fetch fails
   * WHERE: Shown when API call returns error
   * WHY: Informs user of issue and provides retry option
   */
  if (error) {
    return (
      <div className={styles.errorContainer}>
        <h2>Error Loading Learning Analytics</h2>
        <p>{error}</p>
        <button onClick={refetch} className={styles.retryButton}>
          Retry
        </button>
      </div>
    );
  }

  /**
   * Time Range Options Configuration
   *
   * WHAT: Available time range filter options
   * WHERE: Time range selector buttons
   * WHY: Provides standard analytics time periods
   */
  const timeRangeOptions: { value: TimeRange; label: string }[] = [
    { value: '7d', label: 'Week' },
    { value: '30d', label: 'Month' },
    { value: '90d', label: 'Quarter' },
    { value: '6m', label: '6 Months' },
    { value: '1y', label: 'Year' },
    { value: 'all', label: 'All Time' },
  ];

  /**
   * Dashboard Title Logic
   *
   * WHAT: Determines appropriate dashboard title
   * WHERE: Dashboard header
   * WHY: Provides context-appropriate title based on view type
   */
  const getDashboardTitle = () => {
    switch (viewType) {
      case 'student':
        return 'My Learning Analytics';
      case 'instructor':
        return 'Student Learning Analytics';
      case 'org_admin':
        return 'Organization Learning Analytics';
      default:
        return 'Learning Analytics';
    }
  };

  return (
    <div className={styles.dashboardContainer}>
      {/* Header Section */}
      <div className={styles.dashboardHeader}>
        <div className={styles.titleSection}>
          <h1>{getDashboardTitle()}</h1>
          <p className={styles.subtitle}>
            {viewType === 'student' && 'Track your learning progress and skill development'}
            {viewType === 'instructor' && 'Monitor student learning outcomes and engagement'}
            {viewType === 'org_admin' && 'Organizational learning insights and trends'}
          </p>
        </div>

        {/* Time Range Selector */}
        <div className={styles.timeRangeSelector}>
          {timeRangeOptions.map((option) => (
            <button
              key={option.value}
              className={`${styles.timeRangeBtn} ${
                timeRange === option.value ? styles.active : ''
              }`}
              onClick={() => setTimeRange(option.value)}
              aria-pressed={timeRange === option.value}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Stats Cards */}
      {summary && (
        <div className={styles.summaryGrid}>
          <div className={styles.statCard}>
            <span className={styles.statIcon}>📈</span>
            <div className={styles.statContent}>
              <h3>Engagement Score</h3>
              <p className={styles.statValue}>{summary.overall_engagement_score}%</p>
              <p className={styles.statLabel}>Overall engagement</p>
            </div>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statIcon}>🎯</span>
            <div className={styles.statContent}>
              <h3>Skills Mastered</h3>
              <p className={styles.statValue}>
                {summary.skills_mastered}/{summary.total_skills_tracked}
              </p>
              <p className={styles.statLabel}>
                {summary.total_skills_tracked > 0
                  ? `${Math.round((summary.skills_mastered / summary.total_skills_tracked) * 100)}% mastery rate`
                  : 'No skills tracked'}
              </p>
            </div>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statIcon}>🔥</span>
            <div className={styles.statContent}>
              <h3>Current Streak</h3>
              <p className={styles.statValue}>{summary.current_streak_days} days</p>
              <p className={styles.statLabel}>
                Longest: {summary.longest_streak_days} days
              </p>
            </div>
          </div>

          <div className={styles.statCard}>
            <span className={styles.statIcon}>⏱️</span>
            <div className={styles.statContent}>
              <h3>Learning Time</h3>
              <p className={styles.statValue}>
                {Math.round(summary.total_learning_time_minutes / 60)}h
              </p>
              <p className={styles.statLabel}>Total time invested</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Analytics Widgets */}
      <div className={styles.widgetsGrid}>
        {/* Learning Progress Chart */}
        {progressTimeSeries && progressTimeSeries.length > 0 && (
          <div className={styles.widgetCard}>
            <h2>Learning Progress Over Time</h2>
            <LearningProgressChart data={progressTimeSeries} />
          </div>
        )}

        {/* Skill Mastery Widget */}
        {skillMastery && skillMastery.length > 0 && (
          <div className={styles.widgetCard}>
            <h2>Skill Mastery</h2>
            <SkillMasteryWidget skills={skillMastery} />
          </div>
        )}

        {/* Learning Path Progress */}
        {learningPaths && learningPaths.length > 0 && (
          <div className={styles.widgetCard}>
            <h2>Learning Path Progress</h2>
            <LearningPathProgress paths={learningPaths} />
          </div>
        )}

        {/* Session Activity */}
        {sessionActivity && sessionActivity.length > 0 && (
          <div className={styles.widgetCard}>
            <h2>Session Activity</h2>
            <SessionActivityWidget sessions={sessionActivity} />
          </div>
        )}
      </div>

      {/* Skills Needing Review Section */}
      {summary && summary.skills_needing_review && summary.skills_needing_review.length > 0 && (
        <div className={styles.reviewSection}>
          <h2>Skills Due for Review</h2>
          <p className={styles.reviewSubtitle}>
            Based on spaced repetition schedule (SM-2 algorithm)
          </p>
          <div className={styles.reviewGrid}>
            {summary.skills_needing_review.map((skill) => (
              <div key={skill.id} className={styles.reviewCard}>
                <h3>{skill.skill_topic}</h3>
                <div className={styles.reviewMeta}>
                  <span className={styles.reviewBadge}>
                    {skill.mastery_level.charAt(0).toUpperCase() + skill.mastery_level.slice(1)}
                  </span>
                  <span className={styles.reviewInterval}>
                    Next review: {skill.current_interval_days} days
                  </span>
                </div>
                <div className={styles.reviewProgress}>
                  <div className={styles.reviewProgressBar}>
                    <div
                      className={styles.reviewProgressFill}
                      style={{ width: `${skill.mastery_score}%` }}
                    />
                  </div>
                  <span className={styles.reviewScore}>{skill.mastery_score}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Milestones */}
      {summary && summary.recent_milestones && summary.recent_milestones.length > 0 && (
        <div className={styles.milestonesSection}>
          <h2>Recent Milestones</h2>
          <div className={styles.milestonesList}>
            {summary.recent_milestones.map((milestone, index) => (
              <div key={index} className={styles.milestoneItem}>
                <span className={styles.milestoneIcon}>🏆</span>
                <div className={styles.milestoneContent}>
                  <h3>{milestone.name}</h3>
                  <p className={styles.milestoneDate}>
                    Completed: {new Date(milestone.completed_at).toLocaleDateString()}
                  </p>
                  {milestone.score && (
                    <p className={styles.milestoneScore}>Score: {milestone.score}%</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default LearningAnalyticsDashboard;
