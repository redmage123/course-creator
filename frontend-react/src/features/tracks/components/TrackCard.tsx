/**
 * Track Card Component
 *
 * BUSINESS CONTEXT:
 * Displays a single learning track in a card format.
 * Shows track metadata, enrollment counts, difficulty level, and quick actions.
 * Used by organization admins to manage learning paths.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reusable card component with action buttons
 * - Links to track detail page (courses within track)
 * - Displays status, enrollment stats, and learning objectives
 */

import React from 'react';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import type { Track } from '../../../services';
import styles from './TrackCard.module.css';

/**
 * Track Card Props
 */
export interface TrackCardProps {
  track: Track;
  /** Optional callback when edit button is clicked */
  onEdit?: (trackId: string) => void;
  /** Optional callback when delete button is clicked */
  onDelete?: (trackId: string) => void;
  /** Optional callback when view courses button is clicked */
  onViewCourses?: (trackId: string) => void;
}

/**
 * Track Card Component
 *
 * WHY THIS APPROACH:
 * - Reusable card for track management views
 * - Clean, accessible card layout
 * - Quick actions without navigation
 * - Visual status indicators
 */
export const TrackCard: React.FC<TrackCardProps> = ({
  track,
  onEdit,
  onDelete,
  onViewCourses,
}) => {
  /**
   * Format duration for display
   */
  const formatDuration = () => {
    if (!track.duration_weeks) return 'Duration not specified';
    const weeks = track.duration_weeks;
    if (weeks === 1) return '1 week';
    return `${weeks} weeks`;
  };

  /**
   * Format difficulty level for display
   */
  const formatDifficulty = (level: string) => {
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  /**
   * Get status badge color
   */
  const getStatusClass = () => {
    switch (track.status) {
      case 'active':
        return styles['status-active'];
      case 'draft':
        return styles['status-draft'];
      case 'archived':
        return styles['status-archived'];
      default:
        return styles['status-draft'];
    }
  };

  /**
   * Get difficulty badge color
   */
  const getDifficultyClass = () => {
    switch (track.difficulty_level) {
      case 'beginner':
        return styles['difficulty-beginner'];
      case 'intermediate':
        return styles['difficulty-intermediate'];
      case 'advanced':
        return styles['difficulty-advanced'];
      default:
        return styles['difficulty-beginner'];
    }
  };

  /**
   * Get enrollment capacity percentage
   */
  const getCapacityPercentage = () => {
    if (!track.max_students) return 0;
    return Math.round((track.enrollment_count / track.max_students) * 100);
  };

  /**
   * Get capacity status (for color coding)
   */
  const getCapacityStatus = () => {
    const percentage = getCapacityPercentage();
    if (percentage >= 90) return 'critical';
    if (percentage >= 75) return 'warning';
    return 'healthy';
  };

  return (
    <Card variant="outlined" padding="medium" className={styles['track-card']}>
      {/* Card Header */}
      <div className={styles['card-header']}>
        <div className={styles['title-section']}>
          <h3 className={styles['track-title']}>{track.name}</h3>
          <div className={styles['status-badges']}>
            <span className={`${styles['status-badge']} ${getStatusClass()}`}>
              {track.status.charAt(0).toUpperCase() + track.status.slice(1)}
            </span>
            <span className={`${styles['difficulty-badge']} ${getDifficultyClass()}`}>
              {formatDifficulty(track.difficulty_level)}
            </span>
          </div>
        </div>
      </div>

      {/* Card Body */}
      <div className={styles['card-body']}>
        {/* Description */}
        <p className={styles['track-description']}>
          {track.description || 'No description available'}
        </p>

        {/* Metadata Grid */}
        <div className={styles['metadata-grid']}>
          <div className={styles['metadata-item']}>
            <span className={styles['metadata-icon']}>📅</span>
            <div className={styles['metadata-content']}>
              <span className={styles['metadata-label']}>Duration</span>
              <span className={styles['metadata-value']}>{formatDuration()}</span>
            </div>
          </div>

          <div className={styles['metadata-item']}>
            <span className={styles['metadata-icon']}>👥</span>
            <div className={styles['metadata-content']}>
              <span className={styles['metadata-label']}>Enrolled</span>
              <span className={styles['metadata-value']}>
                {track.enrollment_count}
                {track.max_students && ` / ${track.max_students}`}
              </span>
            </div>
          </div>

          <div className={styles['metadata-item']}>
            <span className={styles['metadata-icon']}>👨‍🏫</span>
            <div className={styles['metadata-content']}>
              <span className={styles['metadata-label']}>Instructors</span>
              <span className={styles['metadata-value']}>
                {track.instructor_count || 0}
              </span>
            </div>
          </div>

          <div className={styles['metadata-item']}>
            <span className={styles['metadata-icon']}>🎯</span>
            <div className={styles['metadata-content']}>
              <span className={styles['metadata-label']}>Objectives</span>
              <span className={styles['metadata-value']}>
                {track.learning_objectives.length || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Capacity Bar (if max_students is set) */}
        {track.max_students && (
          <div className={styles['capacity-section']}>
            <div className={styles['capacity-label']}>
              <span>Enrollment Capacity</span>
              <span className={styles['capacity-percentage']}>
                {getCapacityPercentage()}%
              </span>
            </div>
            <div className={styles['capacity-bar']}>
              <div
                className={`${styles['capacity-fill']} ${
                  styles[`capacity-${getCapacityStatus()}`]
                }`}
                style={{ width: `${getCapacityPercentage()}%` }}
              />
            </div>
          </div>
        )}

        {/* Learning Objectives Preview */}
        {track.learning_objectives.length > 0 && (
          <div className={styles['objectives-section']}>
            <h4 className={styles['objectives-title']}>Learning Objectives:</h4>
            <ul className={styles['objectives-list']}>
              {track.learning_objectives.slice(0, 3).map((objective, index) => (
                <li key={index} className={styles['objective-item']}>
                  {objective}
                </li>
              ))}
              {track.learning_objectives.length > 3 && (
                <li className={styles['objective-item-more']}>
                  +{track.learning_objectives.length - 3} more...
                </li>
              )}
            </ul>
          </div>
        )}
      </div>

      {/* Card Footer - Action Buttons */}
      <div className={styles['card-footer']}>
        <div className={styles['action-buttons']}>
          {onViewCourses && (
            <Button
              variant="ghost"
              size="small"
              onClick={() => onViewCourses(track.id)}
            >
              View Courses
            </Button>
          )}
          {onEdit && (
            <Button
              variant="ghost"
              size="small"
              onClick={() => onEdit(track.id)}
            >
              Edit
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="small"
              onClick={() => onDelete(track.id)}
              className={styles['delete-button']}
            >
              Delete
            </Button>
          )}
        </div>

        {/* Metadata Footer */}
        <div className={styles['metadata-footer']}>
          <span className={styles['metadata-footer-item']}>
            Created {new Date(track.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </Card>
  );
};
