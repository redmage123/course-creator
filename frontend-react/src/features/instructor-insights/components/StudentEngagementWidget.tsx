/**
 * Student Engagement Widget Component
 *
 * Displays student engagement metrics including session data,
 * interaction counts, and response metrics.
 *
 * BUSINESS CONTEXT:
 * Shows instructors how actively students are engaging with course content
 * and how responsive the instructor is to student questions.
 *
 * @module features/instructor-insights/components/StudentEngagementWidget
 */

import React from 'react';
import type { InstructorStudentEngagement } from '@services/instructorInsightsService';
import styles from './StudentEngagementWidget.module.css';

export interface StudentEngagementWidgetProps {
  /** Student engagement data */
  engagement: InstructorStudentEngagement | null;
}

/**
 * Student Engagement Widget
 *
 * WHY THIS APPROACH:
 * - Card-based metrics display
 * - Clear visualization of engagement patterns
 * - Highlights response rate and responsiveness
 * - Shows peak activity times for planning
 */
export const StudentEngagementWidget: React.FC<StudentEngagementWidgetProps> = ({
  engagement,
}) => {
  if (!engagement) {
    return (
      <div className={styles.widget}>
        <h2 className={styles.title}>Student Engagement</h2>
        <div className={styles.emptyState}>
          <p>No engagement data available.</p>
        </div>
      </div>
    );
  }

  /**
   * Format duration in hours/minutes
   */
  const formatDuration = (minutes?: number): string => {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  /**
   * Format hour (0-23) to 12-hour format
   */
  const formatHour = (hour?: number): string => {
    if (hour === undefined || hour === null) return 'N/A';
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:00 ${period}`;
  };

  /**
   * Get response rate color
   */
  const getResponseRateColor = (rate?: number): string => {
    if (!rate) return '#999';
    if (rate >= 90) return '#4caf50';
    if (rate >= 70) return '#ff9800';
    return '#f44336';
  };

  return (
    <div className={styles.widget}>
      <h2 className={styles.title}>Student Engagement</h2>

      {/* Key Metrics Grid */}
      <div className={styles.metricsGrid}>
        <div className={styles.metric}>
          <div className={styles.metricIcon}>📊</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Total Sessions</div>
            <div className={styles.metricValue}>{engagement.total_sessions.toLocaleString()}</div>
          </div>
        </div>

        <div className={styles.metric}>
          <div className={styles.metricIcon}>⏱️</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Avg Session</div>
            <div className={styles.metricValue}>
              {formatDuration(engagement.average_session_duration)}
            </div>
          </div>
        </div>

        <div className={styles.metric}>
          <div className={styles.metricIcon}>🕐</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Peak Hour</div>
            <div className={styles.metricValue}>{formatHour(engagement.peak_hour)}</div>
          </div>
        </div>

        <div className={styles.metric}>
          <div className={styles.metricIcon}>📅</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Most Active</div>
            <div className={styles.metricValue}>
              {engagement.most_active_day || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Interaction Metrics */}
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Student Interactions</h3>
        <div className={styles.statsList}>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Content Views</span>
            <span className={styles.statValue}>
              {engagement.total_content_views.toLocaleString()}
            </span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Lab Sessions</span>
            <span className={styles.statValue}>
              {engagement.total_lab_sessions.toLocaleString()}
            </span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Quiz Attempts</span>
            <span className={styles.statValue}>
              {engagement.total_quiz_attempts.toLocaleString()}
            </span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Forum Posts</span>
            <span className={styles.statValue}>
              {engagement.total_forum_posts.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Response Metrics */}
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Instructor Responsiveness</h3>
        <div className={styles.responseMetrics}>
          <div className={styles.responseRate}>
            <div
              className={styles.responseCircle}
              style={{
                background: `conic-gradient(${getResponseRateColor(engagement.response_rate)} ${
                  (engagement.response_rate || 0) * 3.6
                }deg, #f0f0f0 0deg)`,
              }}
            >
              <div className={styles.responseInner}>
                <div className={styles.responseValue}>
                  {engagement.response_rate?.toFixed(0) || 'N/A'}
                  {engagement.response_rate !== undefined && <span className={styles.responsePercent}>%</span>}
                </div>
                <div className={styles.responseLabel}>Response Rate</div>
              </div>
            </div>
          </div>

          <div className={styles.responseStats}>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>Questions Asked</span>
              <span className={styles.statValue}>
                {engagement.total_questions_asked.toLocaleString()}
              </span>
            </div>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>Questions Answered</span>
              <span className={styles.statValue}>
                {engagement.questions_answered.toLocaleString()}
              </span>
            </div>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>Avg Response Time</span>
              <span className={styles.statValue}>
                {engagement.average_response_time
                  ? `${engagement.average_response_time.toFixed(1)}h`
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentEngagementWidget;
