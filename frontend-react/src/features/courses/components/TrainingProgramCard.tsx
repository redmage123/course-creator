/**
 * Training Program Card Component
 *
 * BUSINESS CONTEXT:
 * Displays a single training program in a card format.
 * Used in list views for instructors, org admins, and students.
 * Shows program metadata, enrollment counts, and quick action buttons.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reusable card component with role-based action buttons
 * - Links to program detail page
 * - Displays publish status, enrollment stats, and metadata
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import type { TrainingProgram } from '../../../services';
import styles from './TrainingProgramCard.module.css';

/**
 * Training Program Card Props
 */
export interface TrainingProgramCardProps {
  program: TrainingProgram;
  /** User role viewing the card */
  viewerRole: 'student' | 'instructor' | 'org_admin' | 'site_admin';
  /** Optional callback when edit button is clicked */
  onEdit?: (programId: string) => void;
  /** Optional callback when delete button is clicked */
  onDelete?: (programId: string) => void;
  /** Optional callback when publish/unpublish button is clicked */
  onTogglePublish?: (programId: string, currentStatus: boolean) => void;
}

/**
 * Training Program Card Component
 *
 * WHY THIS APPROACH:
 * - Reusable card for different user roles
 * - Conditional rendering based on viewer role
 * - Clean, accessible card layout
 * - Quick actions without navigation
 */
export const TrainingProgramCard: React.FC<TrainingProgramCardProps> = ({
  program,
  viewerRole,
  onEdit,
  onDelete,
  onTogglePublish,
}) => {
  /**
   * Format duration for display
   */
  const formatDuration = () => {
    if (!program.estimated_duration) return 'Duration not specified';
    const unit = program.duration_unit || 'hours';
    return `${program.estimated_duration} ${unit}`;
  };

  /**
   * Format difficulty level for display
   */
  const formatDifficulty = (level: string) => {
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  /**
   * Get publish status badge color
   */
  const getPublishStatusClass = () => {
    return program.published
      ? styles['status-published']
      : styles['status-draft'];
  };

  return (
    <Card variant="outlined" padding="medium" className={styles['program-card']}>
      {/* Card Header */}
      <div className={styles['card-header']}>
        <div className={styles['title-section']}>
          <Link
            to={`/courses/${program.id}`}
            className={styles['program-title']}
          >
            {program.title}
          </Link>
          <div className={styles['status-badges']}>
            <span className={`${styles['status-badge']} ${getPublishStatusClass()}`}>
              {program.published ? 'Published' : 'Draft'}
            </span>
            {program.category && (
              <span className={styles['category-badge']}>
                {program.category}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Card Body */}
      <div className={styles['card-body']}>
        {/* Description */}
        <p className={styles['program-description']}>
          {program.description || 'No description available'}
        </p>

        {/* Metadata */}
        <div className={styles['metadata-grid']}>
          <div className={styles['metadata-item']}>
            <span className={styles['metadata-label']}>Difficulty:</span>
            <span className={styles['metadata-value']}>
              {formatDifficulty(program.difficulty_level)}
            </span>
          </div>
          <div className={styles['metadata-item']}>
            <span className={styles['metadata-label']}>Duration:</span>
            <span className={styles['metadata-value']}>
              {formatDuration()}
            </span>
          </div>
          {viewerRole !== 'student' && (
            <>
              <div className={styles['metadata-item']}>
                <span className={styles['metadata-label']}>Enrolled:</span>
                <span className={styles['metadata-value']}>
                  {program.enrolled_students || 0} students
                </span>
              </div>
              <div className={styles['metadata-item']}>
                <span className={styles['metadata-label']}>Completion:</span>
                <span className={styles['metadata-value']}>
                  {program.completion_rate
                    ? `${Math.round(program.completion_rate)}%`
                    : 'N/A'}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Tags */}
        {program.tags && program.tags.length > 0 && (
          <div className={styles['tags-section']}>
            {program.tags.slice(0, 5).map((tag, index) => (
              <span key={index} className={styles['tag']}>
                {tag}
              </span>
            ))}
            {program.tags.length > 5 && (
              <span className={styles['tag-more']}>
                +{program.tags.length - 5} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Card Footer - Action Buttons (Role-Based) */}
      <div className={styles['card-footer']}>
        {/* Student View - Simple View Details Button */}
        {viewerRole === 'student' && (
          <Link to={`/courses/${program.id}`}>
            <Button variant="primary" size="small">
              View Course
            </Button>
          </Link>
        )}

        {/* Instructor/Org Admin View - Management Actions */}
        {(viewerRole === 'instructor' || viewerRole === 'org_admin') && (
          <div className={styles['action-buttons']}>
            <Link to={`/courses/${program.id}`}>
              <Button variant="secondary" size="small">
                View Details
              </Button>
            </Link>

            {viewerRole === 'instructor' && onEdit && (
              <Button
                variant="secondary"
                size="small"
                onClick={() => onEdit(program.id)}
              >
                Edit
              </Button>
            )}

            {viewerRole === 'instructor' && onTogglePublish && (
              <Button
                variant={program.published ? 'secondary' : 'primary'}
                size="small"
                onClick={() => onTogglePublish(program.id, program.published)}
              >
                {program.published ? 'Unpublish' : 'Publish'}
              </Button>
            )}

            {viewerRole === 'instructor' && onDelete && !program.published && (
              <Button
                variant="danger"
                size="small"
                onClick={() => onDelete(program.id)}
              >
                Delete
              </Button>
            )}
          </div>
        )}

        {/* Site Admin View - All Actions */}
        {viewerRole === 'site_admin' && (
          <div className={styles['action-buttons']}>
            <Link to={`/courses/${program.id}`}>
              <Button variant="primary" size="small">
                View Details
              </Button>
            </Link>
          </div>
        )}
      </div>
    </Card>
  );
};
