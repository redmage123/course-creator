/**
 * Teaching Recommendations Widget Component
 *
 * Displays AI-powered teaching improvement recommendations.
 * Shows priority, category, action items, and status tracking.
 *
 * BUSINESS CONTEXT:
 * Provides instructors with data-driven suggestions to improve
 * teaching effectiveness based on analytics patterns.
 *
 * @module features/instructor-insights/components/TeachingRecommendationsWidget
 */

import React, { useState } from 'react';
import type {
  TeachingRecommendation,
  RecommendationPriority,
  RecommendationCategory,
} from '@services/instructorInsightsService';
import styles from './TeachingRecommendationsWidget.module.css';

export interface TeachingRecommendationsWidgetProps {
  /** Recommendations data */
  recommendations: TeachingRecommendation[];
  /** Callback when recommendation is acknowledged */
  onAcknowledge: (id: string) => Promise<void>;
  /** Callback when work starts on recommendation */
  onStart: (id: string) => Promise<void>;
  /** Callback when recommendation is completed */
  onComplete: (id: string, outcome?: Record<string, any>) => Promise<void>;
  /** Callback when recommendation is dismissed */
  onDismiss: (id: string, reason: string) => Promise<void>;
}

/**
 * Teaching Recommendations Widget
 *
 * WHY THIS APPROACH:
 * - Card-based recommendations display
 * - Priority and category filtering
 * - Action buttons for status management
 * - Expandable details with action items
 * - Color-coded priority levels
 */
export const TeachingRecommendationsWidget: React.FC<TeachingRecommendationsWidgetProps> = ({
  recommendations,
  onAcknowledge,
  onStart,
  onComplete,
  onDismiss,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | RecommendationPriority>('all');
  const [processing, setProcessing] = useState<string | null>(null);

  /**
   * Get priority color
   */
  const getPriorityColor = (priority: RecommendationPriority): string => {
    const colors: Record<RecommendationPriority, string> = {
      critical: '#d32f2f',
      high: '#f57c00',
      medium: '#fbc02d',
      low: '#689f38',
    };
    return colors[priority];
  };

  /**
   * Get category icon
   */
  const getCategoryIcon = (category: RecommendationCategory): string => {
    const icons: Record<RecommendationCategory, string> = {
      engagement: '🎯',
      content_quality: '📚',
      responsiveness: '⚡',
      assessment: '✅',
      communication: '💬',
      organization: '📋',
      accessibility: '♿',
      technical: '⚙️',
    };
    return icons[category] || '📌';
  };

  /**
   * Handle action
   */
  const handleAction = async (
    id: string,
    action: 'acknowledge' | 'start' | 'complete' | 'dismiss',
    reason?: string
  ) => {
    try {
      setProcessing(id);
      switch (action) {
        case 'acknowledge':
          await onAcknowledge(id);
          break;
        case 'start':
          await onStart(id);
          break;
        case 'complete':
          await onComplete(id);
          break;
        case 'dismiss':
          if (reason) {
            await onDismiss(id, reason);
          }
          break;
      }
    } catch (error) {
      console.error('Error performing action:', error);
      alert('Failed to perform action. Please try again.');
    } finally {
      setProcessing(null);
    }
  };

  /**
   * Toggle expanded view
   */
  const toggleExpanded = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  // Filter recommendations
  const filteredRecommendations =
    filter === 'all'
      ? recommendations
      : recommendations.filter((rec) => rec.priority === filter);

  // Sort by priority (critical first)
  const sortedRecommendations = [...filteredRecommendations].sort((a, b) => {
    const priorityOrder: Record<RecommendationPriority, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3,
    };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className={styles.widget}>
        <h2 className={styles.title}>Teaching Recommendations</h2>
        <div className={styles.emptyState}>
          <p>🎉 Great job! No recommendations at this time.</p>
          <p className={styles.emptySubtext}>
            Keep up the excellent work with your teaching.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <h2 className={styles.title}>Teaching Recommendations</h2>
        <div className={styles.filters}>
          <button
            className={`${styles.filterButton} ${filter === 'all' ? styles.active : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({recommendations.length})
          </button>
          <button
            className={`${styles.filterButton} ${filter === 'critical' ? styles.active : ''}`}
            onClick={() => setFilter('critical')}
          >
            Critical ({recommendations.filter((r) => r.priority === 'critical').length})
          </button>
          <button
            className={`${styles.filterButton} ${filter === 'high' ? styles.active : ''}`}
            onClick={() => setFilter('high')}
          >
            High ({recommendations.filter((r) => r.priority === 'high').length})
          </button>
        </div>
      </div>

      <div className={styles.recommendationsList}>
        {sortedRecommendations.map((rec) => (
          <div
            key={rec.id}
            className={`${styles.recommendationCard} ${
              expandedId === rec.id ? styles.expanded : ''
            }`}
          >
            <div className={styles.cardHeader} onClick={() => toggleExpanded(rec.id)}>
              <div className={styles.headerLeft}>
                <span className={styles.categoryIcon}>{getCategoryIcon(rec.category)}</span>
                <div className={styles.headerContent}>
                  <h3 className={styles.recommendationTitle}>{rec.title}</h3>
                  <p className={styles.recommendationCategory}>
                    {rec.category.replace('_', ' ')}
                  </p>
                </div>
              </div>
              <div className={styles.headerRight}>
                <span
                  className={styles.priorityBadge}
                  style={{ backgroundColor: getPriorityColor(rec.priority) }}
                >
                  {rec.priority}
                </span>
                <span className={styles.statusBadge}>{rec.status.replace('_', ' ')}</span>
                <span className={styles.expandIcon}>{expandedId === rec.id ? '▼' : '▶'}</span>
              </div>
            </div>

            {expandedId === rec.id && (
              <div className={styles.cardBody}>
                <p className={styles.description}>{rec.description}</p>

                {rec.action_items && rec.action_items.length > 0 && (
                  <div className={styles.actionItems}>
                    <h4 className={styles.actionItemsTitle}>Action Items:</h4>
                    <ul className={styles.actionItemsList}>
                      {rec.action_items.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {rec.expected_impact && (
                  <div className={styles.impact}>
                    <strong>Expected Impact:</strong> {rec.expected_impact}
                  </div>
                )}

                {rec.estimated_effort && (
                  <div className={styles.effort}>
                    <strong>Estimated Effort:</strong> {rec.estimated_effort}
                  </div>
                )}

                <div className={styles.cardActions}>
                  {rec.status === 'pending' && (
                    <>
                      <button
                        className={styles.actionButton}
                        onClick={() => handleAction(rec.id, 'acknowledge')}
                        disabled={processing === rec.id}
                      >
                        Acknowledge
                      </button>
                      <button
                        className={styles.actionButton}
                        onClick={() => handleAction(rec.id, 'start')}
                        disabled={processing === rec.id}
                      >
                        Start Working
                      </button>
                    </>
                  )}

                  {rec.status === 'acknowledged' && (
                    <button
                      className={styles.actionButton}
                      onClick={() => handleAction(rec.id, 'start')}
                      disabled={processing === rec.id}
                    >
                      Start Working
                    </button>
                  )}

                  {rec.status === 'in_progress' && (
                    <button
                      className={`${styles.actionButton} ${styles.primaryButton}`}
                      onClick={() => handleAction(rec.id, 'complete')}
                      disabled={processing === rec.id}
                    >
                      Mark Complete
                    </button>
                  )}

                  <button
                    className={`${styles.actionButton} ${styles.dismissButton}`}
                    onClick={() => {
                      const reason = prompt('Why are you dismissing this recommendation?');
                      if (reason) {
                        handleAction(rec.id, 'dismiss', reason);
                      }
                    }}
                    disabled={processing === rec.id}
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TeachingRecommendationsWidget;
