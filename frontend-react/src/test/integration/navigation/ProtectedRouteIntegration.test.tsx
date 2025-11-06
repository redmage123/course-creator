/**
 * Protected Route Integration Tests
 *
 * BUSINESS CONTEXT:
 * Tests protected route authentication and authorization integration.
 * Validates that routes properly enforce authentication and role-based access control.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests ProtectedRoute component with React Router
 * - Tests authentication state + navigation logic
 * - Tests role-based access control enforcement
 * - Tests redirect behavior for unauthenticated/unauthorized users
 *
 * INTEGRATION SCOPE:
 * - ProtectedRoute + React Router + Redux auth state
 * - Navigation redirects + Authentication checks
 * - Role validation + Unauthorized access handling
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, createMockAuthState, createMockUser } from '../../utils';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '@components/routing/ProtectedRoute';

// Mock page components
const MockStudentDashboard = () => <div>Student Dashboard</div>;
const MockInstructorDashboard = () => <div>Instructor Dashboard</div>;
const MockOrgAdminDashboard = () => <div>Org Admin Dashboard</div>;
const MockSiteAdminDashboard = () => <div>Site Admin Dashboard</div>;
const MockLoginPage = () => <div>Login Page</div>;
const MockUnauthorized = () => <div>Unauthorized Access</div>;

describe('Protected Route Integration Tests', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should allow authenticated student to access student dashboard', async () => {
    /**
     * INTEGRATION TEST: Authenticated Access - Student Role
     *
     * SIMULATES:
     * 1. Student is logged in
     * 2. Navigates to student dashboard
     * 3. Route allows access
     * 4. Dashboard is rendered
     */

    renderWithProviders(
      <MemoryRouter initialEntries={['/dashboard/student']}>
        <Routes>
          <Route path="/login" element={<MockLoginPage />} />
          <Route
            path="/dashboard/student"
            element={
              <ProtectedRoute requiredRoles={['student']}>
                <MockStudentDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ role: 'student', userId: 'student-123' }),
          user: { profile: createMockUser({ role: 'student', id: 'student-123' }) },
        },
        useMemoryRouter: false, // Test provides its own MemoryRouter
      }
    );

    // Assert - Student dashboard is rendered
    expect(screen.getByText('Student Dashboard')).toBeInTheDocument();
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
  });

  it('should redirect unauthenticated user to login', async () => {
    /**
     * INTEGRATION TEST: Unauthenticated Redirect
     *
     * SIMULATES:
     * 1. User is not logged in
     * 2. Tries to access protected route
     * 3. Is redirected to login page
     */

    renderWithProviders(
      <MemoryRouter initialEntries={['/dashboard/student']}>
        <Routes>
          <Route path="/login" element={<MockLoginPage />} />
          <Route
            path="/dashboard/student"
            element={
              <ProtectedRoute requiredRoles={['student']}>
                <MockStudentDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ isAuthenticated: false, token: null, role: null }),
        },
        useMemoryRouter: false,
      }
    );

    // Assert - Redirected to login
    await waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });
    expect(screen.queryByText('Student Dashboard')).not.toBeInTheDocument();
  });

  it('should block unauthorized role from accessing protected route', async () => {
    /**
     * INTEGRATION TEST: Role-Based Access Control
     *
     * SIMULATES:
     * 1. Student is logged in
     * 2. Tries to access instructor-only route
     * 3. Access is denied
     * 4. Redirected to unauthorized page
     */

    renderWithProviders(
      <MemoryRouter initialEntries={['/dashboard/instructor']}>
        <Routes>
          <Route path="/unauthorized" element={<MockUnauthorized />} />
          <Route
            path="/dashboard/instructor"
            element={
              <ProtectedRoute requiredRoles={['instructor']}>
                <MockInstructorDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ role: 'student', userId: 'student-123' }), // Student trying to access instructor route
          user: { profile: createMockUser({ role: 'student', id: 'student-123' }) },
        },
        useMemoryRouter: false,
      }
    );

    // Assert - Access denied, redirected to unauthorized
    await waitFor(() => {
      expect(screen.getByText('Unauthorized Access')).toBeInTheDocument();
    });
    expect(screen.queryByText('Instructor Dashboard')).not.toBeInTheDocument();
  });

  it('should allow instructor to access instructor-only routes', async () => {
    /**
     * INTEGRATION TEST: Correct Role Access
     */

    renderWithProviders(
      <MemoryRouter initialEntries={['/dashboard/instructor']}>
        <Routes>
          <Route path="/unauthorized" element={<MockUnauthorized />} />
          <Route
            path="/dashboard/instructor"
            element={
              <ProtectedRoute requiredRoles={['instructor']}>
                <MockInstructorDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ role: 'instructor', userId: 'instructor-123' }),
          user: { profile: createMockUser({ role: 'instructor', id: 'instructor-123' }) },
        },
        useMemoryRouter: false,
      }
    );

    // Assert - Instructor can access
    expect(screen.getByText('Instructor Dashboard')).toBeInTheDocument();
  });

  it('should allow site admin to access site admin routes', async () => {
    /**
     * INTEGRATION TEST: Site Admin Access
     */

    renderWithProviders(
      <MemoryRouter initialEntries={['/dashboard/site-admin']}>
        <Routes>
          <Route
            path="/dashboard/site-admin"
            element={
              <ProtectedRoute requiredRoles={['site_admin']}>
                <MockSiteAdminDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ role: 'site_admin', userId: 'admin-123' }),
          user: { profile: createMockUser({ role: 'site_admin', id: 'admin-123' }) },
        },
        useMemoryRouter: false,
      }
    );

    // Assert - Site admin can access
    expect(screen.getByText('Site Admin Dashboard')).toBeInTheDocument();
  });

  it('should allow org admin to access org admin routes', async () => {
    /**
     * INTEGRATION TEST: Organization Admin Access
     */

    renderWithProviders(
      <MemoryRouter initialEntries={['/dashboard/org-admin']}>
        <Routes>
          <Route
            path="/dashboard/org-admin"
            element={
              <ProtectedRoute requiredRoles={['org_admin']}>
                <MockOrgAdminDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ role: 'org_admin', userId: 'orgadmin-123', organizationId: 'org-456' }),
          user: { profile: createMockUser({ role: 'org_admin', id: 'orgadmin-123', organizationId: 'org-456' }) },
        },
        useMemoryRouter: false,
      }
    );

    // Assert - Org admin can access
    expect(screen.getByText('Org Admin Dashboard')).toBeInTheDocument();
  });

  it('should support routes accessible by multiple roles', async () => {
    /**
     * INTEGRATION TEST: Multi-Role Route Access
     *
     * BUSINESS REQUIREMENT:
     * Some routes should be accessible by multiple roles
     */

    const MockSharedPage = () => <div>Shared Content</div>;

    // Test with instructor role
    const { unmount } = renderWithProviders(
      <MemoryRouter initialEntries={['/shared']}>
        <Routes>
          <Route
            path="/shared"
            element={
              <ProtectedRoute requiredRoles={['instructor', 'org_admin']}>
                <MockSharedPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ role: 'instructor' }),
          user: { profile: createMockUser({ role: 'instructor' }) },
        },
        useMemoryRouter: false,
      }
    );

    expect(screen.getByText('Shared Content')).toBeInTheDocument();
    unmount();

    // Test with org_admin role
    renderWithProviders(
      <MemoryRouter initialEntries={['/shared']}>
        <Routes>
          <Route
            path="/shared"
            element={
              <ProtectedRoute requiredRoles={['instructor', 'org_admin']}>
                <MockSharedPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ role: 'org_admin' }),
          user: { profile: createMockUser({ role: 'org_admin' }) },
        },
        useMemoryRouter: false,
      }
    );

    expect(screen.getByText('Shared Content')).toBeInTheDocument();
  });

  it('should handle expired token as unauthenticated', async () => {
    /**
     * INTEGRATION TEST: Expired Token Handling
     *
     * SIMULATES:
     * 1. User has expired token
     * 2. Tries to access protected route
     * 3. Treated as unauthenticated
     * 4. Redirected to login
     */

    renderWithProviders(
      <MemoryRouter initialEntries={['/dashboard/student']}>
        <Routes>
          <Route path="/login" element={<MockLoginPage />} />
          <Route
            path="/dashboard/student"
            element={
              <ProtectedRoute requiredRoles={['student']}>
                <MockStudentDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({
            expiresAt: Date.now() - 1000, // Expired 1 second ago
            role: 'student',
          }),
        },
        useMemoryRouter: false,
      }
    );

    // Assert - Redirected to login (token expired)
    await waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });
  });

  it('should preserve intended destination for post-login redirect', async () => {
    /**
     * INTEGRATION TEST: Post-Login Redirect
     *
     * BUSINESS REQUIREMENT:
     * After login, user should be redirected to originally requested page
     *
     * Note: This test documents the expected behavior
     * Actual implementation requires redirect state management
     */

    // This would require the ProtectedRoute component to store
    // the intended destination in navigation state or localStorage
    // for retrieval after login

    renderWithProviders(
      <MemoryRouter initialEntries={['/dashboard/student']}>
        <Routes>
          <Route path="/login" element={<MockLoginPage />} />
          <Route
            path="/dashboard/student"
            element={
              <ProtectedRoute requiredRoles={['student']}>
                <MockStudentDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
      {
        preloadedState: {
          auth: createMockAuthState({ isAuthenticated: false, token: null, role: null }),
        },
        useMemoryRouter: false,
      }
    );

    // User is redirected to login
    await waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });

    // After login, should redirect back to /dashboard/student
    // This behavior would be tested in login flow integration tests
  });
});
