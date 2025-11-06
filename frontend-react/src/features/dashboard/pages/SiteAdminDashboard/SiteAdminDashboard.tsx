/**
 * Site Admin Dashboard Page
 *
 * BUSINESS CONTEXT:
 * Main dashboard for site administrators showing platform-wide metrics,
 * organization management, user oversight, and system administration tools.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses DashboardLayout for consistent structure
 * - Fetches real platform-wide analytics from backend API
 * - Displays platform-level metrics across all organizations
 * - Quick links to organization and user management
 * - System health monitoring and configuration
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
import styles from './SiteAdminDashboard.module.css';

/**
 * Site Admin Dashboard Component
 *
 * WHY THIS APPROACH:
 * - Platform-wide overview and management
 * - Multi-organization administration
 * - System configuration and monitoring
 * - Real-time platform analytics from backend API
 */
export const SiteAdminDashboard: React.FC = () => {
  const { user } = useAuth();

  // SEO for Site Admin Dashboard
  const seoElement = (
    <SEO
      title="Site Admin Dashboard"
      description="Platform-wide administration dashboard. Manage all organizations, monitor system health, view platform analytics, and configure global settings."
      keywords="site admin dashboard, platform administration, system management, platform analytics, global settings"
    />
  );

  /**
   * Fetch platform-wide dashboard statistics
   * Returns site admin-specific metrics (organizations, users, revenue, uptime)
   */
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboardStats', 'platform'],
    queryFn: () => analyticsService.getDashboardStats(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 2,
  });

  const displayName = user?.firstName
    ? `${user.firstName} ${user.lastName || ''}`
    : user?.username || 'Admin';

  /**
   * Loading State
   * Show spinner while fetching platform analytics
   */
  if (isLoading) {
    return (
      <>
        {seoElement}
      <DashboardLayout>
        <div className={styles['site-admin-dashboard']}>
          <div className={styles['welcome-section']}>
            <Heading level="h1" gutterBottom>
              Platform Administration
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
          <div className={styles['site-admin-dashboard']}>
          <div className={styles['welcome-section']}>
            <Heading level="h1" gutterBottom>
              Platform Administration
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
   * Format currency for display
   */
  const formatCurrency = (value?: number): string => {
    if (!value) return '$0';
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
    return `$${value}`;
  };

  /**
   * Success State
   * Display real platform analytics from API
   */
  return (
    <>
      {seoElement}
      <DashboardLayout>
        <div className={styles['site-admin-dashboard']}>
          {/* Welcome Section */}
          <div className={styles['welcome-section']}>
          <Heading level="h1" gutterBottom>
            Platform Administration
          </Heading>
          <p className={styles['welcome-text']}>
            Welcome, {displayName}! Manage the entire platform, organizations, users, and system configuration.
          </p>
        </div>

        {/* Quick Stats - Real Data from API */}
        <div className={styles['stats-grid']}>
          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>{stats?.total_organizations || 0}</div>
              <div className={styles['stat-label']}>Organizations</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>
                {stats?.total_users?.toLocaleString() || '0'}
              </div>
              <div className={styles['stat-label']}>Total Users</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>
                {formatCurrency(stats?.monthly_revenue)}
              </div>
              <div className={styles['stat-label']}>Monthly Revenue</div>
            </div>
          </Card>

          <Card variant="elevated" padding="medium">
            <div className={styles['stat-card']}>
              <div className={styles['stat-value']}>
                {stats?.system_uptime ? Math.round(stats.system_uptime) : 0}%
              </div>
              <div className={styles['stat-label']}>System Uptime</div>
            </div>
          </Card>
        </div>

        {/* Main Content */}
        <div className={styles['content-grid']}>
          {/* Organization Management */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Organization Management
            </Heading>
            <p className={styles['section-description']}>
              View, create, and manage all organizations on the platform
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/admin/organizations">
                <Button variant="primary" size="medium">
                  Manage Organizations
                </Button>
              </Link>
              <Link to="/admin/organizations/create">
                <Button variant="secondary" size="medium">
                  Create Organization
                </Button>
              </Link>
            </div>
          </Card>

          {/* User Management */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              User Management
            </Heading>
            <p className={styles['section-description']}>
              Manage all users across the platform and their permissions
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/admin/users">
                <Button variant="primary" size="medium">
                  Manage Users
                </Button>
              </Link>
            </div>
          </Card>

          {/* Platform Analytics */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              Platform Analytics
            </Heading>
            <p className={styles['section-description']}>
              View platform-wide metrics, usage statistics, and performance data
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/admin/analytics">
                <Button variant="primary" size="medium">
                  View Analytics
                </Button>
              </Link>
            </div>
          </Card>

          {/* System Settings */}
          <Card variant="elevated" padding="large">
            <Heading level="h2" gutterBottom>
              System Configuration
            </Heading>
            <p className={styles['section-description']}>
              Configure platform settings, features, and system-wide preferences
            </p>
            <div className={styles['action-buttons']}>
              <Link to="/admin/settings">
                <Button variant="secondary" size="medium">
                  System Settings
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
