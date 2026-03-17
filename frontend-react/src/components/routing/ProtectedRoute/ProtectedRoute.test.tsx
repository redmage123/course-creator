/**
 * Protected Route Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring ProtectedRoute enforces authentication and
 * role-based access control properly.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests authentication, authorization, and redirect behavior
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';

// Mock useAuth hook
let mockIsAuthenticated = false;
let mockUser: any = null;

vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: mockIsAuthenticated,
    user: mockUser,
  }),
}));

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    mockIsAuthenticated = false;
    mockUser = null;
  });

  const renderProtectedRoute = (
    ui: React.ReactElement,
    { initialEntries = ['/protected'] } = {}
  ) => {
    return render(
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
          <Route path="/protected" element={ui} />
        </Routes>
      </MemoryRouter>
    );
  };

  describe('Unauthenticated User', () => {
    it('redirects to login when not authenticated', () => {
      renderProtectedRoute(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Login Page')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('redirects to custom path when specified', () => {
      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route path="/custom-login" element={<div>Custom Login</div>} />
            <Route
              path="/protected"
              element={
                <ProtectedRoute redirectTo="/custom-login">
                  <div>Protected Content</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Custom Login')).toBeInTheDocument();
    });

    it('redirects when user is null even if isAuthenticated is true', () => {
      mockIsAuthenticated = true;
      mockUser = null;

      renderProtectedRoute(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });
  });

  describe('Authenticated User - No Role Requirements', () => {
    beforeEach(() => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'student',
      };
    });

    it('renders protected content when authenticated', () => {
      renderProtectedRoute(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
      expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
    });

    it('renders complex protected content', () => {
      renderProtectedRoute(
        <ProtectedRoute>
          <div>
            <h1>Dashboard</h1>
            <p>Welcome, user!</p>
          </div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Welcome, user!')).toBeInTheDocument();
    });
  });

  describe('Role-Based Access Control', () => {
    it('allows access when user has required role', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'admin',
        email: 'admin@example.com',
        role: 'site_admin',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={['site_admin']}>
          <div>Admin Panel</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Admin Panel')).toBeInTheDocument();
    });

    it('allows access when user has one of multiple required roles', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '2',
        username: 'orgadmin',
        email: 'orgadmin@example.com',
        role: 'org_admin',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={['site_admin', 'org_admin']}>
          <div>Admin Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Admin Content')).toBeInTheDocument();
    });

    it('denies access when user lacks required role', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '3',
        username: 'student',
        email: 'student@example.com',
        role: 'student',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={['site_admin', 'org_admin']}>
          <div>Admin Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Unauthorized Page')).toBeInTheDocument();
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();
    });

    it('redirects to custom unauthorized page', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '3',
        username: 'student',
        email: 'student@example.com',
        role: 'student',
      };

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route path="/access-denied" element={<div>Access Denied</div>} />
            <Route
              path="/protected"
              element={
                <ProtectedRoute
                  requiredRoles={['site_admin']}
                  unauthorizedRedirect="/access-denied"
                >
                  <div>Admin Content</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
    });
  });

  describe('Different User Roles', () => {
    it('allows student access to student-only route', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'student1',
        email: 'student@example.com',
        role: 'student',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={['student']}>
          <div>Student Dashboard</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Student Dashboard')).toBeInTheDocument();
    });

    it('allows instructor access to instructor-only route', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '2',
        username: 'instructor1',
        email: 'instructor@example.com',
        role: 'instructor',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={['instructor']}>
          <div>Instructor Panel</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Instructor Panel')).toBeInTheDocument();
    });

    it('allows org_admin access to org admin routes', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '3',
        username: 'orgadmin1',
        email: 'orgadmin@example.com',
        role: 'org_admin',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={['org_admin']}>
          <div>Organization Dashboard</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Organization Dashboard')).toBeInTheDocument();
    });

    it('allows site_admin access to site admin routes', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '4',
        username: 'siteadmin',
        email: 'admin@example.com',
        role: 'site_admin',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={['site_admin']}>
          <div>Site Administration</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Site Administration')).toBeInTheDocument();
    });

    it('denies student access to instructor route', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'student1',
        email: 'student@example.com',
        role: 'student',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={['instructor']}>
          <div>Instructor Panel</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Unauthorized Page')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('allows access with empty requiredRoles array', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        role: 'student',
      };

      renderProtectedRoute(
        <ProtectedRoute requiredRoles={[]}>
          <div>Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('renders multiple children correctly', () => {
      mockIsAuthenticated = true;
      mockUser = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        role: 'student',
      };

      renderProtectedRoute(
        <ProtectedRoute>
          <div>
            <h1>Title</h1>
            <p>Paragraph</p>
            <button>Button</button>
          </div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.getByText('Button')).toBeInTheDocument();
    });
  });
});
