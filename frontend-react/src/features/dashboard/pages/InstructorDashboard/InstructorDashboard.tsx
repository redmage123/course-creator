/**
 * Instructor Dashboard Page
 *
 * BUSINESS CONTEXT:
 * Main dashboard for corporate IT trainers delivering graduate-level AI/IT training.
 * Trainers are B2B customers who enroll students in corporate training programs,
 * create course content, and track learner progress. Focus on enterprise-scale
 * training delivery with bulk student management.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses DashboardLayout for consistent structure
 * - Fetches real instructor analytics from backend API
 * - Displays corporate training metrics and student cohorts
 * - Quick links to student enrollment, content generation, and analytics
 * - Loading states and error handling with React Query
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { SEO } from '../../../../components/common/SEO';
import { DashboardLayout } from '../../../../components/templates/DashboardLayout';
import { Card } from '../../../../components/atoms/Card';
import { Button } from '../../../../components/atoms/Button';
import { Heading } from '../../../../components/atoms/Heading';
import { Spinner } from '../../../../components/atoms/Spinner';
import { useAuth } from '../../../../hooks/useAuth';
import { analyticsService } from '../../../../services';
import styles from './InstructorDashboard.module.css';

/**
 * Instructor Dashboard Component
 *
 * WHY THIS APPROACH:
 * - Card-based layout for corporate training program management
 * - Quick access to student enrollment and content generation tools
 * - Analytics overview for training effectiveness and compliance
 * - Focus on enterprise-scale training delivery
 * - Real-time data from backend analytics API
 */
export const InstructorDashboard: React.FC = () => {
  const { user } = useAuth();

  // SEO for Instructor Dashboard
  const seoElement = (
    <SEO
      title="Instructor Dashboard"
      description="Manage your courses, create AI-powered content, track student progress, and view teaching analytics on the Course Creator Platform."
      keywords="instructor dashboard, course management, student analytics, content creation, teaching tools"
    />
  );

  /**
   * Fetch instructor analytics data from backend API
   * Uses React Query for caching, loading states, and automatic refetching
   */
  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['instructorAnalytics', 'me'],
    queryFn: () => analyticsService.getMyInstructorAnalytics(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 2,
  });

  const displayName = user?.firstName
    ? `${user.firstName} ${user.lastName || ''}`
    : user?.username || 'Instructor';

  /**
   * Loading State
   * Show spinner while fetching analytics data
   */
  if (isLoading) {
    return (
      <>
        {seoElement}
        <DashboardLayout>
          <div className={styles['instructor-dashboard']}>
            <div className={styles['welcome-section']}>
            <Heading level="h1" gutterBottom>
              Corporate Trainer Dashboard
            </Heading>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
            <Spinner size="large" />
          </div>
        </div>
        </DashboardLayout>
      </>
    );
  }

  /**
   * Error State
   * Show error message if API call fails
   */
  if (error) {
    return (
      <DashboardLayout>
        <div className={styles['instructor-dashboard']}>
          <div className={styles['welcome-section']}>
            <Heading level="h1" gutterBottom>
              Corporate Trainer Dashboard
            </Heading>
            <Card variant="outlined" padding="large">
              <p style={{ color: 'var(--color-error)', textAlign: 'center' }}>
                Unable to load dashboard data. Please try refreshing the page.
              </p>
            </Card>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Success State
   * Display real analytics data from API
   */
  return (
    <>
      {seoElement}
      <DashboardLayout>
        <div className={styles['instructor-dashboard']}>
          {/* Welcome Section */}
          <div className={styles['welcome-section']}>
          <Heading level="h1" gutterBottom>
            Corporate Trainer Dashboard
          </Heading>
          <p className={styles['welcome-text']}>
            Welcome back, {displayName}! Manage your IT training programs, enroll students, and create AI-focused course content.
          </p>
        </div>

        {/* Quick Stats - Real Data from API */}
        <div className={styles['stats-grid']}>
          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>{analytics?.total_programs || 0}</div>
              <div className={styles['stat-label']}>Training Programs</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>{analytics?.total_students || 0}</div>
              <div className={styles['stat-label']}>Enrolled Students</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>
                {analytics?.average_completion_rate
                  ? Math.round(analytics.average_completion_rate)
                  : 0}%
              </div>
              <div className={styles['stat-label']}>Avg Completion Rate</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>
                {analytics?.average_course_rating?.toFixed(1) || '0.0'}
              </div>
              <div className={styles['stat-label']}>Course Rating</div>
            </div>
          </Card>
        </div>

        {/* Main Content */}
        <div className={styles['content-grid']}>
          {/* Training Programs */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              IT Training Programs
            </Heading>
            <p className={styles['section-description']}>
              Manage your AI/IT training programs, update content, and track student engagement
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/instructor/programs">
                <Button variant="primary" size="medium">
                  Manage Programs
                </Button>
              </Link>
              <Link to="/instructor/programs/create">
                <Button variant="secondary" size="medium">
                  Create New Program
                </Button>
              </Link>
            </div>
          </Card>

          {/* Student Enrollment & Management */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Student Enrollment
            </Heading>
            <p className={styles['section-description']}>
              Enroll students, track progress, and manage training cohorts
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/instructor/students">
                <Button variant="primary" size="medium">
                  Manage Students
                </Button>
              </Link>
              <Link to="/instructor/students/enroll">
                <Button variant="secondary" size="medium">
                  Enroll Students
                </Button>
              </Link>
            </div>
          </Card>

          {/* Training Analytics */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Training Analytics
            </Heading>
            <p className={styles['section-description']}>
              Track training effectiveness, completion rates, and certification metrics
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/instructor/analytics">
                <Button variant="primary" size="medium">
                  View Reports
                </Button>
              </Link>
            </div>
          </Card>

          {/* AI Content Generation */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              AI Content Generator
            </Heading>
            <p className={styles['section-description']}>
              Generate quizzes, labs, slides, and training materials with AI assistance
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/instructor/content-generator">
                <Button variant="primary" size="medium" data-action="generate">
                  Generate Content
                </Button>
              </Link>
              <Link to="/instructor/content-generator?type=quiz">
                <Button variant="secondary" size="medium" data-action="create-quiz">
                  Create Quiz
                </Button>
              </Link>
              <Link to="/instructor/content-generator?type=slides">
                <Button variant="secondary" size="medium" data-action="create-slides">
                  Create Slides
                </Button>
              </Link>
            </div>
          </Card>

          {/* Course & Lab Creation */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Course & Lab Creation
            </Heading>
            <p className={styles['section-description']}>
              Create new courses with labs, quizzes, and interactive content
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/organization/courses/create">
                <Button variant="primary" size="medium" data-action="create-course">
                  Create Course
                </Button>
              </Link>
              <Link to="/instructor/labs/create">
                <Button variant="secondary" size="medium" data-action="create-lab">
                  Create Lab
                </Button>
              </Link>
              <Link to="/instructor/students/bulk-enroll">
                <Button variant="secondary" size="medium" data-action="bulk-enroll">
                  Bulk Enroll
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
      </DashboardLayout>
    </>
  );
};
