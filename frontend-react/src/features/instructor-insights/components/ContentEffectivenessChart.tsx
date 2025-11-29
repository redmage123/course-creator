/**
 * Content Effectiveness Chart Component
 *
 * Visualizes content performance across different content types.
 * Shows ratings, completion rates, and engagement scores to identify
 * which content types are most effective.
 *
 * BUSINESS CONTEXT:
 * Helps instructors identify which content types (videos, readings, labs, etc.)
 * are most engaging and effective. Highlights areas needing improvement.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Bar chart showing metrics by content type
 * - Color-coded bars for quick identification
 * - Tooltips with detailed metrics
 * - Responsive SVG chart
 *
 * @module features/instructor-insights/components/ContentEffectivenessChart
 */

import React from 'react';
import type { ContentEffectiveness, TimeRange } from '@services/instructorInsightsService';
import styles from './ContentEffectivenessChart.module.css';

export interface ContentEffectivenessChartProps {
  /** Content effectiveness data */
  contentEffectiveness: ContentEffectiveness[];
  /** Time range for context */
  timeRange: TimeRange;
}

/**
 * Content Effectiveness Chart Component
 *
 * WHY THIS APPROACH:
 * - Visual comparison across content types
 * - Multiple metrics in one view (rating, completion, engagement)
 * - Color coding highlights problem areas
 * - Simple bar chart for clarity
 */
export const ContentEffectivenessChart: React.FC<ContentEffectivenessChartProps> = ({
  contentEffectiveness,
  timeRange,
}) => {
  /**
   * Get color based on score
   */
  const getScoreColor = (score: number, needsImprovement: boolean): string => {
    if (needsImprovement) return '#f44336';
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  /**
   * Format time range for display
   */
  const formatTimeRange = (range: TimeRange): string => {
    const ranges: Record<TimeRange, string> = {
      '7d': 'Last 7 Days',
      '30d': 'Last 30 Days',
      '90d': 'Last 90 Days',
      '1y': 'Last Year',
      all: 'All Time',
    };
    return ranges[range];
  };

  // Empty state
  if (!contentEffectiveness || contentEffectiveness.length === 0) {
    return (
      <div className={styles.widget}>
        <div className={styles.header}>
          <h2 className={styles.title}>Content Effectiveness</h2>
          <span className={styles.timeRange}>{formatTimeRange(timeRange)}</span>
        </div>
        <div className={styles.emptyState}>
          <p>No content data available for this time period.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <h2 className={styles.title}>Content Effectiveness</h2>
        <span className={styles.timeRange}>{formatTimeRange(timeRange)}</span>
      </div>

      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendColor} style={{ backgroundColor: '#2196f3' }}></span>
          <span>Average Rating</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendColor} style={{ backgroundColor: '#4caf50' }}></span>
          <span>Completion Rate</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendColor} style={{ backgroundColor: '#ff9800' }}></span>
          <span>Engagement Score</span>
        </div>
      </div>

      <div className={styles.chartContainer}>
        {contentEffectiveness.map((content, index) => (
          <div key={index} className={styles.contentRow}>
            <div className={styles.contentType}>
              <h3 className={styles.contentLabel}>{content.content_type}</h3>
              <span className={styles.contentCount}>{content.total_items} items</span>
              {content.needs_improvement && (
                <span className={styles.improvementBadge}>Needs Improvement</span>
              )}
            </div>

            <div className={styles.metrics}>
              {/* Average Rating */}
              <div className={styles.metricBar}>
                <div className={styles.metricLabel}>
                  <span>Rating</span>
                  <span className={styles.metricValue}>
                    {content.average_rating.toFixed(1)}/5.0
                  </span>
                </div>
                <div className={styles.barBackground}>
                  <div
                    className={styles.barFill}
                    style={{
                      width: `${(content.average_rating / 5) * 100}%`,
                      backgroundColor: getScoreColor(
                        (content.average_rating / 5) * 100,
                        content.needs_improvement
                      ),
                    }}
                  ></div>
                </div>
              </div>

              {/* Completion Rate */}
              <div className={styles.metricBar}>
                <div className={styles.metricLabel}>
                  <span>Completion</span>
                  <span className={styles.metricValue}>{content.completion_rate.toFixed(1)}%</span>
                </div>
                <div className={styles.barBackground}>
                  <div
                    className={styles.barFill}
                    style={{
                      width: `${content.completion_rate}%`,
                      backgroundColor: getScoreColor(
                        content.completion_rate,
                        content.needs_improvement
                      ),
                    }}
                  ></div>
                </div>
              </div>

              {/* Engagement Score */}
              <div className={styles.metricBar}>
                <div className={styles.metricLabel}>
                  <span>Engagement</span>
                  <span className={styles.metricValue}>{content.engagement_score.toFixed(0)}/100</span>
                </div>
                <div className={styles.barBackground}>
                  <div
                    className={styles.barFill}
                    style={{
                      width: `${content.engagement_score}%`,
                      backgroundColor: getScoreColor(
                        content.engagement_score,
                        content.needs_improvement
                      ),
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className={styles.summary}>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Content Types:</span>
          <span className={styles.summaryValue}>{contentEffectiveness.length}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Total Items:</span>
          <span className={styles.summaryValue}>
            {contentEffectiveness.reduce((sum, c) => sum + c.total_items, 0)}
          </span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Needs Improvement:</span>
          <span className={styles.summaryValue}>
            {contentEffectiveness.filter((c) => c.needs_improvement).length}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ContentEffectivenessChart;
