/**
 * Training Program Detail Page
 *
 * BUSINESS CONTEXT:
 * Displays comprehensive details of a single training program.
 * Different views for students (assigned courses), instructors (manage),
 * and org admins (overview).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches program details from backend API
 * - Role-based action buttons (enroll, edit, publish)
 * - Displays syllabus, content modules, and enrollment stats
 * - Loading states and error handling
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/templates/DashboardLayout';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import { Heading } from '../../../components/atoms/Heading';
import { Spinner } from '../../../components/atoms/Spinner';
import { useAuth } from '../../../hooks/useAuth';
import { trainingProgramService } from '../../../services';
import styles from './TrainingProgramDetailPage.module.css';

/**
 * Training Program Detail Page Component
 *
 * WHY THIS APPROACH:
 * - Comprehensive program information display
 * - Role-based UI and available actions
 * - Clean, accessible layout with semantic HTML
 * - Proper loading and error states
 */
export const TrainingProgramDetailPage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  /**
   * Fetch training program details
   */
  const { data: program, isLoading, error } = useQuery({
    queryKey: ['trainingProgram', courseId],
    queryFn: () => trainingProgramService.getTrainingProgramById(courseId!),
    enabled: !!courseId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  /**
   * Format duration for display
   */
  const formatDuration = () => {
    if (!program?.estimated_duration) return 'Duration not specified';
    const unit = program.duration_unit || 'hours';
    return `${program.estimated_duration} ${unit}`;
  };

  /**
   * Format difficulty level
   */
  const formatDifficulty = (level?: string) => {
    if (!level) return 'Not specified';
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  /**
   * Format price
   */
  const formatPrice = (price?: number) => {
    if (price === undefined || price === null) return 'Free';
    if (price === 0) return 'Free';
    return `$${price.toFixed(2)}`;
  };

  /**
   * Check if user can edit this program
   */
  const canEdit = () => {
    return (
      user?.role === 'instructor' &&
      program?.instructor_id === user?.id
    );
  };

  /**
   * Handle edit navigation
   */
  const handleEdit = () => {
    navigate(`/instructor/programs/${courseId}/edit`);
  };

  /**
   * Handle back navigation
   */
  const handleBack = () => {
    if (user?.role === 'instructor') {
      navigate('/instructor/programs');
    } else if (user?.role === 'org_admin') {
      navigate('/organization/programs');
    } else if (user?.role === 'student') {
      navigate('/courses/my-courses');
    } else {
      navigate(-1);
    }
  };

  /**
   * Loading State
   */
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className={styles['detail-page']}>
          <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
            <Spinner size="large" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Error State
   */
  if (error || !program) {
    return (
      <DashboardLayout>
        <div className={styles['detail-page']}>
          <Card variant="outlined" padding="large">
            <p style={{ color: 'var(--color-error)', textAlign: 'center' }}>
              Unable to load training program details. Please try refreshing the page.
            </p>
            <div style={{ textAlign: 'center', marginTop: '1rem' }}>
              <Button variant="secondary" onClick={handleBack}>
                Go Back
              </Button>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Success State - Display Program Details
   */
  return (
    <DashboardLayout>
      <div className={styles['detail-page']}>
        {/* Breadcrumb / Back Button */}
        <div className={styles['breadcrumb']}>
          <Button variant="text" onClick={handleBack}>
            ← Back to Programs
          </Button>
        </div>

        {/* Program Header */}
        <Card variant="outlined" padding="large" className={styles['header-card']}>
          <div className={styles['header-content']}>
            <div className={styles['title-section']}>
              <Heading level="h1" gutterBottom>
                {program.title}
              </Heading>
              <div className={styles['status-badges']}>
                <span
                  className={`${styles['status-badge']} ${
                    program.published ? styles['status-published'] : styles['status-draft']
                  }`}
                >
                  {program.published ? 'Published' : 'Draft'}
                </span>
                {program.category && (
                  <span className={styles['category-badge']}>
                    {program.category}
                  </span>
                )}
              </div>
            </div>

            {canEdit() && (
              <Button variant="primary" onClick={handleEdit}>
                Edit Program
              </Button>
            )}
          </div>

          {/* Program Description */}
          {program.description && (
            <p className={styles['description']}>
              {program.description}
            </p>
          )}

          {/* Program Metadata Grid */}
          <div className={styles['metadata-grid']}>
            <div className={styles['metadata-item']}>
              <span className={styles['metadata-label']}>Difficulty Level</span>
              <span className={styles['metadata-value']}>
                {formatDifficulty(program.difficulty_level)}
              </span>
            </div>
            <div className={styles['metadata-item']}>
              <span className={styles['metadata-label']}>Duration</span>
              <span className={styles['metadata-value']}>
                {formatDuration()}
              </span>
            </div>
            <div className={styles['metadata-item']}>
              <span className={styles['metadata-label']}>Price</span>
              <span className={styles['metadata-value']}>
                {formatPrice(program.price)}
              </span>
            </div>
            {(user?.role === 'instructor' || user?.role === 'org_admin') && (
              <>
                <div className={styles['metadata-item']}>
                  <span className={styles['metadata-label']}>Enrolled Students</span>
                  <span className={styles['metadata-value']}>
                    {program.enrolled_students || 0}
                  </span>
                </div>
                <div className={styles['metadata-item']}>
                  <span className={styles['metadata-label']}>Completion Rate</span>
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
              <span className={styles['tags-label']}>Tags:</span>
              <div className={styles['tags-list']}>
                {program.tags.map((tag, index) => (
                  <span key={index} className={styles['tag']}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Course Content Section */}
        <Card variant="outlined" padding="large" className={styles['content-card']}>
          <Heading level="h2" gutterBottom>
            Course Content
          </Heading>
          <p className={styles['content-description']}>
            Detailed course syllabus, modules, and learning materials will be displayed here.
            This section will include:
          </p>
          <ul className={styles['content-features']}>
            <li>Course modules and lessons</li>
            <li>Video lectures and presentations</li>
            <li>Lab exercises and assignments</li>
            <li>Quizzes and assessments</li>
            <li>Downloadable resources</li>
          </ul>
          <p className={styles['coming-soon']}>
            📋 Detailed syllabus view coming in next phase
          </p>
        </Card>

        {/* Enrollment Section (for instructors/admins) */}
        {(user?.role === 'instructor' || user?.role === 'org_admin') && program.published && (
          <Card variant="outlined" padding="large" className={styles['enrollment-card']}>
            <Heading level="h2" gutterBottom>
              Student Enrollment
            </Heading>
            <p className={styles['enrollment-description']}>
              Manage student enrollments, track progress, and view analytics for this program.
            </p>
            <div className={styles['enrollment-actions']}>
              <Button variant="primary">
                View Enrolled Students
              </Button>
              <Button variant="secondary">
                Enroll New Students
              </Button>
            </div>
          </Card>
        )}

        {/* Student Actions */}
        {user?.role === 'student' && program.published && (
          <Card variant="outlined" padding="large" className={styles['student-actions-card']}>
            <Heading level="h2" gutterBottom>
              Get Started
            </Heading>
            <p className={styles['action-description']}>
              Ready to begin your learning journey with this training program?
            </p>
            <Button variant="primary" size="large">
              Start Learning
            </Button>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};
