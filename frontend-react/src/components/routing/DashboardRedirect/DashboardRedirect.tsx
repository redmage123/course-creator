/**
 * Dashboard Redirect Component
 *
 * BUSINESS CONTEXT:
 * Automatically redirects users to their role-specific dashboard when they
 * access the generic /dashboard route. Improves UX by eliminating the need
 * to remember role-specific URLs.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses auth state to determine user role
 * - Redirects to appropriate dashboard based on role mapping
 * - Shows loading state while auth state is being determined
 * - Falls back to homepage for guests or unknown roles
 *
 * SECURITY:
 * - Only authenticated users reach this component (wrapped by ProtectedRoute)
 * - Role validation happens at the destination dashboard
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { Spinner } from '../../atoms/Spinner';
import styles from './DashboardRedirect.module.css';

/**
 * Dashboard route mapping by user role
 *
 * WHY THIS MAPPING:
 * - Each role has a dedicated dashboard with role-specific features
 * - Guests redirect to homepage since they have no dashboard
 * - Keeps routing logic centralized for maintainability
 */
const DASHBOARD_ROUTES: Record<string, string> = {
  site_admin: '/dashboard/site-admin',
  organization_admin: '/dashboard/org-admin',
  instructor: '/dashboard/instructor',
  student: '/dashboard/student',
};

export interface DashboardRedirectProps {
  /**
   * Fallback path if role cannot be determined
   * @default '/'
   */
  fallbackPath?: string;

  /**
   * Show loading indicator while determining redirect
   * @default true
   */
  showLoading?: boolean;
}

/**
 * Dashboard Redirect Component
 *
 * WHY THIS APPROACH:
 * - Centralizes redirect logic in one component
 * - Handles loading state gracefully
 * - Provides fallback for edge cases
 * - Keeps App.tsx routing clean and declarative
 *
 * @example
 * ```tsx
 * <Route
 *   path="/dashboard"
 *   element={
 *     <ProtectedRoute>
 *       <DashboardRedirect />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
export const DashboardRedirect: React.FC<DashboardRedirectProps> = ({
  fallbackPath = '/',
  showLoading = true,
}) => {
  const { role, isLoading, isAuthenticated } = useAuth();

  // Show loading while auth state is being determined
  if (isLoading && showLoading) {
    return (
      <div className={styles.container} data-testid="dashboard-redirect-loading">
        <Spinner size="large" />
        <p className={styles.message}>Redirecting to your dashboard...</p>
      </div>
    );
  }

  // Not authenticated - redirect to login (shouldn't happen with ProtectedRoute)
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Determine redirect path based on role
  const redirectPath = role ? DASHBOARD_ROUTES[role] : null;

  // Redirect to role-specific dashboard or fallback
  if (redirectPath) {
    return <Navigate to={redirectPath} replace />;
  }

  // Fallback for unknown roles or guests
  return <Navigate to={fallbackPath} replace />;
};

DashboardRedirect.displayName = 'DashboardRedirect';
