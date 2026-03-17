/**
 * Learning Path Progress Component
 *
 * WHAT: Visualizes progress through learning paths and tracks
 * WHERE: Learning Analytics Dashboard learning path section
 * WHY: Shows curriculum progress, current position, and completion status
 *
 * BUSINESS CONTEXT:
 * Displays structured learning path information:
 * - Overall path progress percentage
 * - Current course/module position
 * - Milestones completed
 * - Time tracking (actual vs estimated)
 * - Path status (on track, behind, at risk)
 * - Assessment performance
 *
 * TECHNICAL IMPLEMENTATION:
 * - Progress bar visualizations
 * - Status indicators with color coding
 * - Timeline view for milestones
 * - Expandable path details
 * - Responsive card layout
 *
 * @module features/learning-analytics/components/LearningPathProgress
 */

import React, { useState } from 'react';
import type {
  LearningPathProgress as LearningPathData,
  LearningPathStatus,
} from '../../../services/learningAnalyticsService';
import styles from './LearningPathProgress.module.css';

/**
 * Component Props Interface
 */
export interface LearningPathProgressProps {
  paths: LearningPathData[];
}

/**
 * Learning Path Progress Component
 *
 * WHY THIS APPROACH:
 * - Card-based layout for multiple paths
 * - Expandable details for comprehensive view
 * - Status color coding for quick assessment
 * - Milestone timeline shows progress checkpoints
 * - Time tracking compares actual vs estimated
 */
export const LearningPathProgress: React.FC<LearningPathProgressProps> = ({ paths }) => {
  const [expandedPath, setExpandedPath] = useState<string | null>(null);

  /**
   * Empty State Handler
   */
  if (!paths || paths.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No active learning paths</p>
        <span className={styles.emptyIcon}>🛤️</span>
      </div>
    );
  }

  /**
   * Get Status Color
   *
   * WHAT: Maps path status to visual color
   * WHERE: Status badges and progress bars
   * WHY: Provides instant visual feedback on path health
   */
  const getStatusColor = (status: LearningPathStatus): string => {
    const colorMap: Record<LearningPathStatus, string> = {
      not_started: '#9e9e9e',
      in_progress: '#2196f3',
      on_track: '#4caf50',
      behind: '#ff9800',
      at_risk: '#f44336',
      completed: '#8bc34a',
      abandoned: '#757575',
    };
    return colorMap[status] || '#9e9e9e';
  };

  /**
   * Get Status Label
   *
   * WHAT: Converts status enum to display text
   * WHERE: Status badges
   * WHY: User-friendly status display
   */
  const getStatusLabel = (status: LearningPathStatus): string => {
    return status
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  /**
   * Toggle Path Expansion
   *
   * WHAT: Expands/collapses path details
   * WHERE: Path card click handler
   * WHY: Shows detailed information on demand
   */
  const togglePathExpansion = (pathId: string) => {
    setExpandedPath(expandedPath === pathId ? null : pathId);
  };

  /**
   * Calculate Time Difference
   *
   * WHAT: Compares actual vs estimated completion time
   * WHERE: Time tracking display
   * WHY: Shows if student is ahead or behind schedule
   */
  const calculateTimeDifference = (path: LearningPathData): string | null => {
    if (!path.estimated_completion_at) return null;

    const now = new Date();
    const estimated = new Date(path.estimated_completion_at);
    const diffDays = Math.ceil((estimated.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (path.actual_completion_at) {
      const actual = new Date(path.actual_completion_at);
      const completionDiff = Math.ceil(
        (actual.getTime() - estimated.getTime()) / (1000 * 60 * 60 * 24)
      );
      return completionDiff > 0
        ? `Completed ${completionDiff} days late`
        : `Completed ${Math.abs(completionDiff)} days early`;
    }

    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days overdue`;
    } else if (diffDays === 0) {
      return 'Due today';
    } else {
      return `${diffDays} days remaining`;
    }
  };

  return (
    <div className={styles.pathsContainer}>
      {paths.map((path) => {
        const isExpanded = expandedPath === path.id;
        const timeDiff = calculateTimeDifference(path);

        return (
          <div key={path.id} className={styles.pathCard}>
            {/* Path Header */}
            <div
              className={styles.pathHeader}
              onClick={() => togglePathExpansion(path.id)}
              role="button"
              tabIndex={0}
              onKeyPress={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  togglePathExpansion(path.id);
                }
              }}
            >
              <div className={styles.pathTitleSection}>
                <h3 className={styles.pathTitle}>Learning Path {path.track_id}</h3>
                <span
                  className={styles.statusBadge}
                  style={{ backgroundColor: getStatusColor(path.status) }}
                >
                  {getStatusLabel(path.status)}
                </span>
              </div>
              <button className={styles.expandButton} aria-expanded={isExpanded}>
                {isExpanded ? '▼' : '▶'}
              </button>
            </div>

            {/* Progress Bar */}
            <div className={styles.progressSection}>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{
                    width: `${path.overall_progress}%`,
                    backgroundColor: getStatusColor(path.status),
                  }}
                />
              </div>
              <span className={styles.progressValue}>{path.overall_progress.toFixed(1)}%</span>
            </div>

            {/* Quick Stats */}
            <div className={styles.quickStats}>
              <div className={styles.stat}>
                <span className={styles.statIcon}>⏱️</span>
                <span className={styles.statText}>
                  {Math.round(path.total_time_spent_minutes / 60)}h
                </span>
              </div>
              {path.avg_quiz_score !== undefined && (
                <div className={styles.stat}>
                  <span className={styles.statIcon}>📝</span>
                  <span className={styles.statText}>{path.avg_quiz_score.toFixed(0)}%</span>
                </div>
              )}
              {path.milestones_completed && path.milestones_completed.length > 0 && (
                <div className={styles.stat}>
                  <span className={styles.statIcon}>🏆</span>
                  <span className={styles.statText}>
                    {path.milestones_completed.length} milestones
                  </span>
                </div>
              )}
            </div>

            {/* Time Difference */}
            {timeDiff && (
              <p
                className={`${styles.timeDiff} ${
                  timeDiff.includes('overdue') || timeDiff.includes('late')
                    ? styles.timeDiffWarning
                    : styles.timeDiffSuccess
                }`}
              >
                {timeDiff}
              </p>
            )}

            {/* Expanded Details */}
            {isExpanded && (
              <div className={styles.expandedContent}>
                {/* Current Position */}
                {path.current_course_id && (
                  <div className={styles.currentPosition}>
                    <h4>Current Position</h4>
                    <p>Course ID: {path.current_course_id}</p>
                    {path.current_module_order && (
                      <p>Module: {path.current_module_order}</p>
                    )}
                  </div>
                )}

                {/* Dates */}
                <div className={styles.datesSection}>
                  <h4>Timeline</h4>
                  <div className={styles.datesList}>
                    {path.started_at && (
                      <div className={styles.dateItem}>
                        <span className={styles.dateLabel}>Started:</span>
                        <span className={styles.dateValue}>
                          {new Date(path.started_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                    {path.estimated_completion_at && (
                      <div className={styles.dateItem}>
                        <span className={styles.dateLabel}>Est. Completion:</span>
                        <span className={styles.dateValue}>
                          {new Date(path.estimated_completion_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                    {path.actual_completion_at && (
                      <div className={styles.dateItem}>
                        <span className={styles.dateLabel}>Completed:</span>
                        <span className={styles.dateValue}>
                          {new Date(path.actual_completion_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                    {path.last_activity_at && (
                      <div className={styles.dateItem}>
                        <span className={styles.dateLabel}>Last Activity:</span>
                        <span className={styles.dateValue}>
                          {new Date(path.last_activity_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Milestones */}
                {path.milestones_completed && path.milestones_completed.length > 0 && (
                  <div className={styles.milestonesSection}>
                    <h4>Completed Milestones</h4>
                    <div className={styles.milestonesList}>
                      {path.milestones_completed.map((milestone, index) => (
                        <div key={index} className={styles.milestoneItem}>
                          <span className={styles.milestoneIcon}>✓</span>
                          <div className={styles.milestoneContent}>
                            <p className={styles.milestoneName}>{milestone.name}</p>
                            <p className={styles.milestoneDate}>
                              {new Date(milestone.completed_at).toLocaleDateString()}
                            </p>
                            {milestone.score !== undefined && (
                              <p className={styles.milestoneScore}>
                                Score: {milestone.score}%
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Performance Metrics */}
                <div className={styles.performanceMetrics}>
                  <h4>Performance</h4>
                  <div className={styles.metricsGrid}>
                    {path.avg_quiz_score !== undefined && (
                      <div className={styles.metricItem}>
                        <span className={styles.metricLabel}>Avg Quiz Score</span>
                        <span className={styles.metricValue}>
                          {path.avg_quiz_score.toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {path.avg_assignment_score !== undefined && (
                      <div className={styles.metricItem}>
                        <span className={styles.metricLabel}>Avg Assignment Score</span>
                        <span className={styles.metricValue}>
                          {path.avg_assignment_score.toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default LearningPathProgress;
