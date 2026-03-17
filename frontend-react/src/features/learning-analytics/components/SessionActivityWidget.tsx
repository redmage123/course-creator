/**
 * Session Activity Widget Component
 *
 * WHAT: Displays learning session activity metrics and patterns
 * WHERE: Learning Analytics Dashboard session tracking section
 * WHY: Tracks engagement patterns, session duration, and activity types
 *
 * BUSINESS CONTEXT:
 * Provides session-level analytics:
 * - Session duration tracking
 * - Activity type breakdown
 * - Engagement score per session
 * - Content consumption metrics
 * - Daily/weekly activity patterns
 * - Peak learning times
 *
 * TECHNICAL IMPLEMENTATION:
 * - Bar chart for session durations
 * - Activity breakdown pie chart
 * - Session list with detailed metrics
 * - Time-based filtering
 * - Engagement score visualization
 *
 * @module features/learning-analytics/components/SessionActivityWidget
 */

import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';
import type { SessionActivity } from '../../../services/learningAnalyticsService';
import styles from './SessionActivityWidget.module.css';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

/**
 * Component Props Interface
 */
export interface SessionActivityWidgetProps {
  sessions: SessionActivity[];
}

/**
 * View Mode Type
 */
type ViewMode = 'timeline' | 'breakdown' | 'list';

/**
 * Session Activity Widget Component
 *
 * WHY THIS APPROACH:
 * - Multiple view modes for different insights
 * - Bar chart shows session duration timeline
 * - Pie chart shows activity type breakdown
 * - List view provides detailed session info
 * - Engagement score tracking
 */
export const SessionActivityWidget: React.FC<SessionActivityWidgetProps> = ({ sessions }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');

  /**
   * Empty State Handler
   */
  if (!sessions || sessions.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No session activity recorded</p>
        <span className={styles.emptyIcon}>📊</span>
      </div>
    );
  }

  /**
   * Calculate Activity Breakdown
   *
   * WHAT: Aggregates total activities by type
   * WHERE: Pie chart data
   * WHY: Shows distribution of learning activities
   */
  const activityBreakdown = sessions.reduce(
    (acc, session) => {
      acc.contentViewed += session.content_items_viewed;
      acc.quizzesAttempted += session.quizzes_attempted;
      acc.labsWorked += session.labs_worked_on;
      return acc;
    },
    { contentViewed: 0, quizzesAttempted: 0, labsWorked: 0 }
  );

  /**
   * Timeline Bar Chart Data
   *
   * WHAT: Session duration over time
   * WHERE: Timeline view mode
   * WHY: Shows learning session patterns
   */
  const timelineData = {
    labels: sessions.map((session) => {
      const date = new Date(session.started_at);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    }),
    datasets: [
      {
        label: 'Session Duration (minutes)',
        data: sessions.map((session) => session.duration_minutes),
        backgroundColor: sessions.map((session) => {
          // Color code by engagement score
          if (session.engagement_score >= 80) return 'rgba(76, 175, 80, 0.7)';
          if (session.engagement_score >= 60) return 'rgba(33, 150, 243, 0.7)';
          if (session.engagement_score >= 40) return 'rgba(255, 152, 0, 0.7)';
          return 'rgba(244, 67, 54, 0.7)';
        }),
        borderColor: sessions.map((session) => {
          if (session.engagement_score >= 80) return '#4caf50';
          if (session.engagement_score >= 60) return '#2196f3';
          if (session.engagement_score >= 40) return '#ff9800';
          return '#f44336';
        }),
        borderWidth: 2,
        borderRadius: 4,
      },
    ],
  };

  /**
   * Timeline Chart Options
   */
  const timelineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          title: (context: any) => {
            const session = sessions[context[0].dataIndex];
            const date = new Date(session.started_at);
            return date.toLocaleString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
            });
          },
          afterBody: (context: any) => {
            const session = sessions[context[0].dataIndex];
            return [
              `Engagement: ${session.engagement_score}%`,
              `Activities: ${session.activities_count}`,
              `Content Viewed: ${session.content_items_viewed}`,
            ];
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: any) => `${value}m`,
        },
      },
    },
  };

  /**
   * Activity Breakdown Pie Chart Data
   *
   * WHAT: Distribution of activity types
   * WHERE: Breakdown view mode
   * WHY: Shows what students are working on
   */
  const breakdownData = {
    labels: ['Content Viewed', 'Quizzes Attempted', 'Labs Worked On'],
    datasets: [
      {
        data: [
          activityBreakdown.contentViewed,
          activityBreakdown.quizzesAttempted,
          activityBreakdown.labsWorked,
        ],
        backgroundColor: [
          'rgba(33, 150, 243, 0.7)',
          'rgba(255, 152, 0, 0.7)',
          'rgba(156, 39, 176, 0.7)',
        ],
        borderColor: ['#2196f3', '#ff9800', '#9c27b0'],
        borderWidth: 2,
      },
    ],
  };

  /**
   * Breakdown Chart Options
   */
  const breakdownOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total =
              activityBreakdown.contentViewed +
              activityBreakdown.quizzesAttempted +
              activityBreakdown.labsWorked;
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
            return `${label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  };

  /**
   * Calculate Summary Stats
   */
  const summaryStats = {
    totalSessions: sessions.length,
    totalDuration: sessions.reduce((sum, s) => sum + s.duration_minutes, 0),
    avgDuration: Math.round(
      sessions.reduce((sum, s) => sum + s.duration_minutes, 0) / sessions.length
    ),
    avgEngagement: Math.round(
      sessions.reduce((sum, s) => sum + s.engagement_score, 0) / sessions.length
    ),
    totalActivities: sessions.reduce((sum, s) => sum + s.activities_count, 0),
  };

  return (
    <div className={styles.widgetContainer}>
      {/* View Mode Toggle */}
      <div className={styles.viewToggle}>
        <button
          className={`${styles.toggleBtn} ${viewMode === 'timeline' ? styles.active : ''}`}
          onClick={() => setViewMode('timeline')}
          aria-pressed={viewMode === 'timeline'}
        >
          Timeline
        </button>
        <button
          className={`${styles.toggleBtn} ${viewMode === 'breakdown' ? styles.active : ''}`}
          onClick={() => setViewMode('breakdown')}
          aria-pressed={viewMode === 'breakdown'}
        >
          Breakdown
        </button>
        <button
          className={`${styles.toggleBtn} ${viewMode === 'list' ? styles.active : ''}`}
          onClick={() => setViewMode('list')}
          aria-pressed={viewMode === 'list'}
        >
          List
        </button>
      </div>

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className={styles.chartView}>
          <div className={styles.chartContainer}>
            <Bar data={timelineData} options={timelineOptions} />
          </div>
          <div className={styles.chartLegend}>
            <div className={styles.legendItem}>
              <span className={styles.legendDot} style={{ backgroundColor: '#4caf50' }}></span>
              <span>High Engagement (80%+)</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendDot} style={{ backgroundColor: '#2196f3' }}></span>
              <span>Good Engagement (60-79%)</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendDot} style={{ backgroundColor: '#ff9800' }}></span>
              <span>Moderate Engagement (40-59%)</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendDot} style={{ backgroundColor: '#f44336' }}></span>
              <span>Low Engagement (&lt;40%)</span>
            </div>
          </div>
        </div>
      )}

      {/* Breakdown View */}
      {viewMode === 'breakdown' && (
        <div className={styles.chartView}>
          <div className={styles.pieChartContainer}>
            <Pie data={breakdownData} options={breakdownOptions} />
          </div>
          <div className={styles.breakdownStats}>
            <div className={styles.breakdownItem}>
              <span className={styles.breakdownLabel}>Content Items</span>
              <span className={styles.breakdownValue}>{activityBreakdown.contentViewed}</span>
            </div>
            <div className={styles.breakdownItem}>
              <span className={styles.breakdownLabel}>Quizzes</span>
              <span className={styles.breakdownValue}>{activityBreakdown.quizzesAttempted}</span>
            </div>
            <div className={styles.breakdownItem}>
              <span className={styles.breakdownLabel}>Labs</span>
              <span className={styles.breakdownValue}>{activityBreakdown.labsWorked}</span>
            </div>
          </div>
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className={styles.listView}>
          {sessions.map((session) => (
            <div key={session.session_id} className={styles.sessionCard}>
              <div className={styles.sessionHeader}>
                <span className={styles.sessionDate}>
                  {new Date(session.started_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                </span>
                <span
                  className={styles.engagementBadge}
                  style={{
                    backgroundColor:
                      session.engagement_score >= 80
                        ? '#4caf50'
                        : session.engagement_score >= 60
                        ? '#2196f3'
                        : session.engagement_score >= 40
                        ? '#ff9800'
                        : '#f44336',
                  }}
                >
                  {session.engagement_score}% engaged
                </span>
              </div>
              <div className={styles.sessionMetrics}>
                <div className={styles.sessionMetric}>
                  <span className={styles.metricIcon}>⏱️</span>
                  <span>{session.duration_minutes}m</span>
                </div>
                <div className={styles.sessionMetric}>
                  <span className={styles.metricIcon}>📄</span>
                  <span>{session.content_items_viewed} items</span>
                </div>
                <div className={styles.sessionMetric}>
                  <span className={styles.metricIcon}>📝</span>
                  <span>{session.quizzes_attempted} quizzes</span>
                </div>
                <div className={styles.sessionMetric}>
                  <span className={styles.metricIcon}>💻</span>
                  <span>{session.labs_worked_on} labs</span>
                </div>
              </div>
              <p className={styles.sessionActivities}>
                {session.activities_count} total activities
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      <div className={styles.summaryStats}>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Total Sessions</span>
          <span className={styles.summaryValue}>{summaryStats.totalSessions}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Total Time</span>
          <span className={styles.summaryValue}>
            {Math.round(summaryStats.totalDuration / 60)}h
          </span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Avg Duration</span>
          <span className={styles.summaryValue}>{summaryStats.avgDuration}m</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Avg Engagement</span>
          <span className={styles.summaryValue}>{summaryStats.avgEngagement}%</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Total Activities</span>
          <span className={styles.summaryValue}>{summaryStats.totalActivities}</span>
        </div>
      </div>
    </div>
  );
};

export default SessionActivityWidget;
