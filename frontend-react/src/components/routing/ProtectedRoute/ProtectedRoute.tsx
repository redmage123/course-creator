/**
 * Protected Route Component
 *
 * BUSINESS CONTEXT:
 * Route wrapper that enforces authentication and role-based access control.
 * Ensures only authorized users can access protected pages.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Checks authentication status from Redux store
 * - Validates user role against required roles
 * - Redirects to login for unauthenticated users
 * - Redirects to unauthorized for insufficient permissions
 * - Preserves intended destination for post-login redirect
 *
 * SECURITY:
 * - All dashboard and feature pages must use this wrapper
 * - Role validation prevents privilege escalation
 * - Login redirect preserves user's intended destination
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { UserRole } from '../../../store/slices/authSlice';

export interface ProtectedRouteProps {
  /**
   * Content to render if authorized
   */
  children: React.ReactNode;

  /**
   * Required roles to access this route (optional)
   * If not provided, only checks authentication
   */
  requiredRoles?: UserRole[];

  /**
   * Redirect path for unauthenticated users
   * @default '/login'
   */
  redirectTo?: string;

  /**
   * Redirect path for users without required role
   * @default '/unauthorized'
   */
  unauthorizedRedirect?: string;
}

/**
 * Protected Route Component
 *
 * WHY THIS APPROACH:
 * - Centralized auth checking reduces duplication
 * - Role-based access control for multi-tenant security
 * - Preserves destination URL for better UX after login
 * - Clear separation between authentication and authorization
 *
 * @example Basic protection (authentication only)
 * ```tsx
 * <Route
 *   path="/dashboard"
 *   element={
 *     <ProtectedRoute>
 *       <Dashboard />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 *
 * @example Role-based protection
 * ```tsx
 * <Route
 *   path="/admin"
 *   element={
 *     <ProtectedRoute requiredRoles={['site_admin', 'org_admin']}>
 *       <AdminPanel />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  redirectTo = '/login',
  unauthorizedRedirect = '/unauthorized',
}) => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  // Not authenticated or no user profile - redirect to login
  // User must be both authenticated AND have a loaded user profile
  if (!isAuthenticated || !user) {
    // Preserve the attempted location for redirect after login
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Check role-based access (only if roles are required)
  if (requiredRoles && requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.includes(user.role);

    if (!hasRequiredRole) {
      return <Navigate to={unauthorizedRedirect} replace />;
    }
  }

  // User is authorized - render the protected content
  return <>{children}</>;
};
