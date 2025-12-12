/**
 * Organization Admin Dashboard Page
 *
 * BUSINESS CONTEXT:
 * Main dashboard for organization administrators in corporate IT training context.
 * Manages corporate trainers (instructors), bulk student enrollments, and
 * organization-level training programs. Serves B2B customers who need to train
 * employees in graduate-level IT courses (especially AI-focused training).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses DashboardLayout for consistent structure
 * - Fetches real organization analytics from backend API
 * - Displays organization-level training metrics
 * - Quick links to trainer and student enrollment management
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
import { analyticsService, organizationService } from '../../../../services';
import styles from './OrgAdminDashboard.module.css';

/**
 * Organization Admin Dashboard Component
 *
 * WHY THIS APPROACH:
 * - Organization-level corporate training overview
 * - Trainer (instructor) and student enrollment management
 * - Bulk student enrollment capabilities
 * - Training program administration and compliance
 * - Real-time analytics from backend API
 */
export const OrgAdminDashboard: React.FC = () => {
  const { user } = useAuth();

  // SEO for Organization Admin Dashboard
  const seoElement = (
    <SEO
      title="Organization Admin Dashboard"
      description="Manage your organization's training programs, instructors, students, and view organization-wide analytics on the Course Creator Platform."
      keywords="org admin dashboard, organization management, training programs, instructor management, corporate training"
    />
  );

  /**
   * Fetch organization data first
   * Needed to get organization ID for analytics
   */
  const { data: organization, isLoading: orgLoading, error: orgError } = useQuery({
    queryKey: ['organization', 'me'],
    queryFn: () => organizationService.getMyOrganization(),
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes
    retry: 2,
  });

  /**
   * Fetch organization analytics using organization ID
   * Dependent query - only runs after organization is fetched
   */
  const { data: analytics, isLoading: analyticsLoading, error: analyticsError } = useQuery({
    queryKey: ['organizationAnalytics', organization?.id],
    queryFn: () => analyticsService.getOrganizationAnalytics(organization!.id),
    enabled: !!organization?.id, // Only run if organization ID is available
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 2,
  });

  const displayName = user?.firstName
    ? `${user.firstName} ${user.lastName || ''}`
    : user?.username || 'Admin';

  const orgName = organization?.name || user?.organizationName || 'Your Organization';

  const isLoading = orgLoading || analyticsLoading;
  const error = orgError || analyticsError;

  /**
   * Loading State
   * Show spinner while fetching organization and analytics data
   */
  if (isLoading) {
    return (
      <>
        {seoElement}
        <DashboardLayout>
          <div className={styles['org-admin-dashboard']}>
            <div className={styles['welcome-section']}>
            <Heading level="h1" gutterBottom>
              Organization Administration
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
      <>
        {seoElement}
        <DashboardLayout>
        <div className={styles['org-admin-dashboard']}>
          <div className={styles['welcome-section']}>
            <Heading level="h1" gutterBottom>
              Organization Administration
            </Heading>
            <Card variant="outlined" padding="large">
              <p style={{ color: 'var(--color-error)', textAlign: 'center' }}>
                Unable to load dashboard data. Please try refreshing the page.
              </p>
            </Card>
          </div>
        </div>
        </DashboardLayout>
      </>
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
      <div className={styles['org-admin-dashboard']}>
        {/* Organization Title - Prominent at top */}
        <div className={styles['org-header']}>
          <div className={styles['org-title-row']}>
            <i className="fas fa-building" aria-hidden="true"></i>
            <h1 className={styles['org-title']}>{orgName}</h1>
          </div>
          <p className={styles['org-subtitle']}>Organization Administration Dashboard</p>
        </div>

        {/* Welcome Section */}
        <div className={styles['welcome-section']}>
          <p className={styles['welcome-text']}>
            Welcome, {displayName}! Manage your corporate trainers, enroll students in IT training programs, and track organizational learning metrics.
          </p>
        </div>

        {/* Quick Stats - Real Data from API */}
        <div className={styles['stats-grid']}>
          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>{analytics?.total_students || 0}</div>
              <div className={styles['stat-label']}>Enrolled Students</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>{analytics?.total_training_programs || 0}</div>
              <div className={styles['stat-label']}>Training Programs</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>{analytics?.total_trainers || 0}</div>
              <div className={styles['stat-label']}>Corporate Trainers</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>
                {analytics?.engagement_rate ? Math.round(analytics.engagement_rate) : 0}%
              </div>
              <div className={styles['stat-label']}>Engagement Rate</div>
            </div>
          </Card>
        </div>

        {/* Main Content */}
        <div className={styles['content-grid']}>
          {/* Trainer & Student Management */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Trainer & Student Management
            </Heading>
            <p className={styles['section-description']}>
              Manage corporate trainers, organization members, enroll students in bulk, and organize learning tracks
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/organization/members">
                <Button variant="primary" size="medium">
                  Manage Members
                </Button>
              </Link>
              <Link to="/organization/trainers">
                <Button variant="secondary" size="medium">
                  Manage Trainers
                </Button>
              </Link>
              <Link to="/organization/students/enroll">
                <Button variant="secondary" size="medium">
                  Bulk Enroll Students
                </Button>
              </Link>
            </div>
          </Card>

          {/* Training Programs */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Training Programs
            </Heading>
            <p className={styles['section-description']}>
              Manage IT training courses, learning tracks, assign programs to students, and track completions
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/organization/programs">
                <Button variant="primary" size="medium">
                  View Programs
                </Button>
              </Link>
              <Link to="/organization/tracks">
                <Button variant="secondary" size="medium">
                  Manage Tracks
                </Button>
              </Link>
              <Link to="/organization/programs/create">
                <Button variant="secondary" size="medium">
                  Create New Program
                </Button>
              </Link>
            </div>
          </Card>

          {/* Import & Templates */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Import & AI Automation
            </Heading>
            <p className={styles['section-description']}>
              Import organization templates and let AI automatically create projects and tracks
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/organization/import">
                <Button variant="primary" size="medium" data-action="import">
                  Import Template
                </Button>
              </Link>
              <Link to="/organization/ai-create">
                <Button variant="secondary" size="medium" data-action="ai-create-project">
                  AI Auto Create Project
                </Button>
              </Link>
              <Link to="/organization/templates/download">
                <Button variant="secondary" size="medium" data-action="download-template">
                  Download Template
                </Button>
              </Link>
            </div>
          </Card>

          {/* Training Analytics */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Training Analytics & Compliance
            </Heading>
            <p className={styles['section-description']}>
              Track training completion rates, certifications, and compliance metrics
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/organization/analytics">
                <Button variant="primary" size="medium">
                  View Reports
                </Button>
              </Link>
            </div>
          </Card>

          {/* Settings */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Organization Settings
            </Heading>
            <p className={styles['section-description']}>
              Configure branding, billing, and organizational preferences
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/organization/settings">
                <Button variant="secondary" size="medium">
                  Manage Settings
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
