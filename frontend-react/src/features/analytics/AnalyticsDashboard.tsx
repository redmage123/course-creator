/**
 * Analytics Dashboard Component
 *
 * Comprehensive analytics interface showing:
 * - Student progress and performance
 * - Course completion rates
 * - Lab proficiency metrics
 * - Quiz performance analytics
 * - Engagement scores
 * - Risk assessment
 *
 * @module features/analytics/AnalyticsDashboard
 */

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAnalytics } from './hooks/useAnalytics';
import { EngagementChart } from './components/EngagementChart';
import { ProgressChart } from './components/ProgressChart';
import { QuizPerformanceChart } from './components/QuizPerformanceChart';
import { LabProficiencyChart } from './components/LabProficiencyChart';
import { RiskAssessmentCard } from './components/RiskAssessmentCard';
import { StatCard } from './components/StatCard';
import styles from './AnalyticsDashboard.module.css';

export type AnalyticsViewType = 'student' | 'course' | 'instructor';

export interface AnalyticsDashboardProps {
  viewType: AnalyticsViewType;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ viewType }) => {
  const { studentId, courseId } = useParams<{ studentId?: string; courseId?: string }>();
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'quarter' | 'year'>('month');

  const {
    engagement,
    progress,
    quizPerformance,
    labProficiency,
    riskAssessment,
    courseAnalytics,
    isLoading,
    error
  } = useAnalytics(viewType, studentId, courseId, timeRange);

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner}></div>
        <p>Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <h2>Error Loading Analytics</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className={styles.dashboardContainer}>
      {/* Header */}
      <div className={styles.dashboardHeader}>
        <div>
          <h1>Analytics Dashboard</h1>
          <p className={styles.subtitle}>
            {viewType === 'student' && 'Your Learning Progress'}
            {viewType === 'course' && 'Course Performance Overview'}
            {viewType === 'instructor' && 'Student Analytics'}
          </p>
        </div>

        <div className={styles.timeRangeSelector}>
          {(['week', 'month', 'quarter', 'year'] as const).map((range) => (
            <button
              key={range}
              className={`${styles.timeRangeBtn} ${timeRange === range ? styles.active : ''}`}
              onClick={() => setTimeRange(range)}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className={styles.metricsGrid}>
        {engagement && (
          <StatCard
            title="Engagement Score"
            value={`${engagement.score}%`}
            trend={engagement.trend}
            icon="📊"
            color="#4caf50"
          />
        )}

        {progress && (
          <StatCard
            title="Course Progress"
            value={`${progress.completion_percentage}%`}
            subtitle={`${progress.completed_items}/${progress.total_items} completed`}
            icon="✅"
            color="#2196f3"
          />
        )}

        {quizPerformance && (
          <StatCard
            title="Quiz Average"
            value={`${quizPerformance.average_score}%`}
            subtitle={`${quizPerformance.quizzes_passed}/${quizPerformance.quizzes_taken} passed`}
            icon="🎯"
            color="#ff9800"
          />
        )}

        {labProficiency && (
          <StatCard
            title="Lab Proficiency"
            value={`${labProficiency.proficiency_score}%`}
            subtitle={`${labProficiency.labs_completed} labs completed`}
            icon="💻"
            color="#9c27b0"
          />
        )}
      </div>

      {/* Risk Assessment (for instructors) */}
      {viewType === 'instructor' && riskAssessment && (
        <RiskAssessmentCard riskData={riskAssessment} />
      )}

      {/* Charts */}
      <div className={styles.chartsGrid}>
        {engagement && (
          <div className={styles.chartCard}>
            <h3>Engagement Over Time</h3>
            <EngagementChart data={engagement.history} />
          </div>
        )}

        {progress && (
          <div className={styles.chartCard}>
            <h3>Progress Timeline</h3>
            <ProgressChart data={progress.timeline} />
          </div>
        )}

        {quizPerformance && (
          <div className={styles.chartCard}>
            <h3>Quiz Performance</h3>
            <QuizPerformanceChart data={quizPerformance.history} />
          </div>
        )}

        {labProficiency && (
          <div className={styles.chartCard}>
            <h3>Lab Proficiency</h3>
            <LabProficiencyChart data={labProficiency.skills} />
          </div>
        )}
      </div>

      {/* Course-level analytics */}
      {viewType === 'course' && courseAnalytics && (
        <div className={styles.courseAnalyticsSection}>
          <h2>Course Analytics Summary</h2>
          <div className={styles.courseStatsGrid}>
            <div className={styles.courseStat}>
              <span className={styles.courseStatLabel}>Total Students</span>
              <span className={styles.courseStatValue}>{courseAnalytics.total_students}</span>
            </div>
            <div className={styles.courseStat}>
              <span className={styles.courseStatLabel}>Active Students</span>
              <span className={styles.courseStatValue}>{courseAnalytics.active_students}</span>
            </div>
            <div className={styles.courseStat}>
              <span className={styles.courseStatLabel}>Completion Rate</span>
              <span className={styles.courseStatValue}>{courseAnalytics.completion_rate}%</span>
            </div>
            <div className={styles.courseStat}>
              <span className={styles.courseStatLabel}>Average Grade</span>
              <span className={styles.courseStatValue}>{courseAnalytics.average_grade}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
