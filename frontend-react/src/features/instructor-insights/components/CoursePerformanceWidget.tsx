/**
 * Course Performance Widget Component
 *
 * Displays course performance metrics and peer comparisons.
 * Shows enrollment stats, completion rates, and benchmarking data.
 *
 * BUSINESS CONTEXT:
 * Helps instructors understand how their courses are performing
 * relative to peers and identify courses needing attention.
 *
 * @module features/instructor-insights/components/CoursePerformanceWidget
 */

import React, { useState } from 'react';
import type {
  InstructorCoursePerformance,
  PeerComparison,
} from '@services/instructorInsightsService';
import styles from './CoursePerformanceWidget.module.css';

export interface CoursePerformanceWidgetProps {
  /** Course performance data */
  coursePerformances: InstructorCoursePerformance[];
  /** Peer comparison data */
  peerComparisons: PeerComparison[];
}

/**
 * Course Performance Widget
 *
 * WHY THIS APPROACH:
 * - Tabular view of all courses
 * - Sortable columns for analysis
 * - Color coding for quick identification
 * - Peer comparison section for benchmarking
 */
export const CoursePerformanceWidget: React.FC<CoursePerformanceWidgetProps> = ({
  coursePerformances,
  peerComparisons,
}) => {
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);

  if (!coursePerformances || coursePerformances.length === 0) {
    return (
      <div className={styles.widget}>
        <h2 className={styles.title}>Course Performance</h2>
        <div className={styles.emptyState}>
          <p>No course data available.</p>
        </div>
      </div>
    );
  }

  /**
   * Get color based on score
   */
  const getScoreColor = (score?: number): string => {
    if (!score) return '#999';
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  /**
   * Handle course selection
   */
  const handleCourseClick = (courseId: string) => {
    setSelectedCourse(selectedCourse === courseId ? null : courseId);
  };

  return (
    <div className={styles.widget}>
      <h2 className={styles.title}>Course Performance</h2>

      {/* Course List */}
      <div className={styles.courseList}>
        {coursePerformances.map((course) => (
          <div
            key={course.id}
            className={`${styles.courseCard} ${
              selectedCourse === course.course_id ? styles.selected : ''
            }`}
            onClick={() => handleCourseClick(course.course_id)}
          >
            <div className={styles.courseHeader}>
              <h3 className={styles.courseName}>
                {course.course_title || `Course ${course.course_id.slice(0, 8)}`}
              </h3>
              <div className={styles.enrollmentBadge}>
                {course.total_enrolled} students
              </div>
            </div>

            <div className={styles.courseMetrics}>
              <div className={styles.metricItem}>
                <span className={styles.metricLabel}>Active</span>
                <span className={styles.metricValue}>{course.active_students}</span>
              </div>
              <div className={styles.metricItem}>
                <span className={styles.metricLabel}>Completed</span>
                <span className={styles.metricValue}>{course.completed_students}</span>
              </div>
              <div className={styles.metricItem}>
                <span className={styles.metricLabel}>Dropped</span>
                <span className={styles.metricValue}>{course.dropped_students}</span>
              </div>
            </div>

            <div className={styles.performanceMetrics}>
              <div className={styles.performanceItem}>
                <span className={styles.performanceLabel}>Average Score</span>
                <span
                  className={styles.performanceValue}
                  style={{ color: getScoreColor(course.average_score) }}
                >
                  {course.average_score?.toFixed(1) || 'N/A'}%
                </span>
              </div>
              <div className={styles.performanceItem}>
                <span className={styles.performanceLabel}>Pass Rate</span>
                <span
                  className={styles.performanceValue}
                  style={{ color: getScoreColor(course.pass_rate) }}
                >
                  {course.pass_rate?.toFixed(1) || 'N/A'}%
                </span>
              </div>
            </div>

            {/* Ratings */}
            {(course.content_rating || course.difficulty_rating || course.workload_rating) && (
              <div className={styles.ratings}>
                {course.content_rating && (
                  <div className={styles.ratingItem}>
                    <span className={styles.ratingLabel}>Content</span>
                    <span className={styles.ratingStars}>
                      {'★'.repeat(Math.round(course.content_rating))}
                      {'☆'.repeat(5 - Math.round(course.content_rating))}
                    </span>
                  </div>
                )}
                {course.difficulty_rating && (
                  <div className={styles.ratingItem}>
                    <span className={styles.ratingLabel}>Difficulty</span>
                    <span className={styles.ratingStars}>
                      {'★'.repeat(Math.round(course.difficulty_rating))}
                      {'☆'.repeat(5 - Math.round(course.difficulty_rating))}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Peer Comparisons */}
      {peerComparisons && peerComparisons.length > 0 && (
        <div className={styles.peerSection}>
          <h3 className={styles.peerTitle}>Peer Benchmarking</h3>
          <p className={styles.peerDescription}>
            See how you compare to other instructors (anonymized)
          </p>

          <div className={styles.peerList}>
            {peerComparisons.slice(0, 3).map((comparison) => (
              <div key={comparison.id} className={styles.peerItem}>
                <div className={styles.peerMetric}>
                  <span className={styles.peerMetricName}>{comparison.metric_name}</span>
                  <span className={styles.peerPosition}>{comparison.position_description}</span>
                </div>
                <div className={styles.peerStats}>
                  <div className={styles.peerStat}>
                    <span className={styles.peerStatLabel}>You</span>
                    <span className={styles.peerStatValue}>
                      {comparison.instructor_score?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                  <div className={styles.peerStat}>
                    <span className={styles.peerStatLabel}>Avg</span>
                    <span className={styles.peerStatValue}>
                      {comparison.peer_average?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                  <div className={styles.peerStat}>
                    <span className={styles.peerStatLabel}>Median</span>
                    <span className={styles.peerStatValue}>
                      {comparison.peer_median?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CoursePerformanceWidget;
