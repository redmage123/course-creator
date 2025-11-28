/**
 * Student Dashboard Page
 *
 * BUSINESS CONTEXT:
 * Main dashboard for students enrolled in corporate IT training programs.
 * This platform serves B2B customers - corporate and personal trainers who
 * enroll students in graduate-level IT courses (especially AI-focused).
 * Students are ASSIGNED courses by trainers - they do NOT choose courses themselves.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses DashboardLayout for consistent structure
 * - Fetches real analytics data from backend API
 * - Displays assigned courses and training progress
 * - Quick links to assigned labs and training resources
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
import { StatCard } from '../../../../components/molecules/StatCard';
import { useAuth } from '../../../../hooks/useAuth';
import { analyticsService } from '../../../../services';
import styles from './StudentDashboard.module.css';

/**
 * Student Dashboard Component
 *
 * WHY THIS APPROACH:
 * - Clean, card-based layout for corporate training context
 * - Focus on assigned courses and trainer-directed learning
 * - Quick access to assigned labs and progress tracking
 * - Personalized greeting for engagement
 * - Placeholder for future data integration
 */
export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();

  // SEO for Student Dashboard
  const seoElement = (
    <SEO
      title="Student Dashboard"
      description="Access your assigned courses, track learning progress, view analytics, and manage your course work on the Course Creator Platform."
      keywords="student dashboard, my courses, learning progress, course analytics, student portal"
    />
  );

  /**
   * Fetch student analytics data from backend API
   * Uses React Query for caching, loading states, and automatic refetching
   */
  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['studentAnalytics', 'me'],
    queryFn: () => analyticsService.getMyAnalytics(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 2,
  });

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const displayName = user?.firstName
    ? `${user.firstName} ${user.lastName || ''}`
    : user?.username || 'Student';

  /**
   * Loading State
   * Show spinner while fetching analytics data
   */
  if (isLoading) {
    return (
      <>
        {seoElement}
        <DashboardLayout>
          <div className={styles['student-dashboard']}>
          <div className={styles['welcome-section']}>
            <Heading level="h1" gutterBottom>
              {getGreeting()}, {displayName}!
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
        <div className={styles['student-dashboard']}>
          <div className={styles['welcome-section']}>
            <Heading level="h1" gutterBottom>
              {getGreeting()}, {displayName}!
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
        <div className={styles['student-dashboard']}>
          {/* Welcome Section */}
        <div className={styles['welcome-section']}>
          <Heading level="h1" gutterBottom>
            {getGreeting()}, {displayName}!
          </Heading>
          <p className={styles['welcome-text']}>
            Welcome to your corporate training dashboard. View your assigned courses, track your progress, and access lab environments.
          </p>
        </div>

        {/* Quick Stats - Real Data from API with Trend Indicators */}
        <div className={styles['stats-grid']}>
          <StatCard
            value={analytics?.active_courses || 0}
            label="Assigned Courses"
            trend={analytics?.courses_trend}
            trendLabel="vs last month"
          />

          <StatCard
            value={analytics?.average_progress ? Math.round(analytics.average_progress) : 0}
            label="Average Progress"
            valueFormat="percentage"
            trend={analytics?.progress_trend}
            trendLabel="vs last week"
          />

          <StatCard
            value={analytics?.total_labs_completed || 0}
            label="Labs Completed"
            trend={analytics?.labs_trend}
            trendLabel="vs last month"
          />

          <StatCard
            value={analytics?.certificates_earned || 0}
            label="Certificates Earned"
            trend={analytics?.certificates_trend}
            trendLabel="this quarter"
          />
        </div>

        {/* Main Content */}
        <div className={styles['content-grid']}>
          {/* Assigned Courses */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Assigned Training Courses
            </Heading>
            <p className={styles['section-description']}>
              Continue your corporate training from where you left off
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/courses/my-courses">
                <Button variant="primary" size="medium">
                  View Assigned Courses
                </Button>
              </Link>
            </div>
          </Card>

          {/* Active Labs */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Active Labs
            </Heading>
            <p className={styles['section-description']}>
              Practice your skills in hands-on lab environments with Monaco, Jupyter, or VS Code
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/labs">
                <Button variant="primary" size="medium" data-action="launch-lab">
                  Launch Labs
                </Button>
              </Link>
              <Link to="/labs?ide=vscode">
                <Button variant="secondary" size="medium" data-ide="vscode">
                  VS Code
                </Button>
              </Link>
              <Link to="/labs?ide=jupyter">
                <Button variant="secondary" size="medium" data-ide="jupyter">
                  Jupyter
                </Button>
              </Link>
            </div>
          </Card>

          {/* Quizzes & Assessments */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Quizzes & Assessments
            </Heading>
            <p className={styles['section-description']}>
              Complete quizzes to test your knowledge and track progress
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/quizzes">
                <Button variant="primary" size="medium" data-action="take-quiz">
                  Take Quiz
                </Button>
              </Link>
              <Link to="/quizzes/history">
                <Button variant="secondary" size="medium">
                  View History
                </Button>
              </Link>
            </div>
          </Card>

          {/* Progress Tracking */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Progress & Achievements
            </Heading>
            <p className={styles['section-description']}>
              Track your learning journey and earned certificates
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/progress">
                <Button variant="primary" size="medium">
                  View Progress
                </Button>
              </Link>
              <Link to="/certificates">
                <Button variant="secondary" size="medium">
                  My Certificates
                </Button>
              </Link>
            </div>
          </Card>

          {/* Learning Resources & Downloads */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Learning Resources
            </Heading>
            <p className={styles['section-description']}>
              Access course materials, videos, and documentation
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/resources">
                <Button variant="primary" size="medium">
                  Browse Resources
                </Button>
              </Link>
              <Link to="/resources/download">
                <Button variant="secondary" size="medium" data-action="download">
                  Download Materials
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
