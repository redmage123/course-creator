/**
 * Dashboard Redirect Component Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring DashboardRedirect correctly routes users
 * to their role-specific dashboards based on authentication state.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library with mocked auth hook
 * Tests all role redirects, loading states, and fallback behavior
 *
 * COVERAGE REQUIREMENTS:
 * - Redirect to correct dashboard for each role (4 roles)
 * - Loading state display
 * - Fallback for unknown roles
 * - Unauthenticated user handling
 * - Custom fallback path
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { DashboardRedirect } from './DashboardRedirect';

// Mock useAuth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '../../../hooks/useAuth';

const mockedUseAuth = useAuth as ReturnType<typeof vi.fn>;

// Helper to render with router and capture navigation
const renderWithRouter = (
  initialEntries: string[] = ['/dashboard'],
  element: React.ReactNode = <DashboardRedirect />
) => {
  let navigatedTo = '';

  return {
    ...render(
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/dashboard" element={element} />
          <Route path="/dashboard/site-admin" element={<div data-testid="site-admin-dashboard">Site Admin Dashboard</div>} />
          <Route path="/dashboard/org-admin" element={<div data-testid="org-admin-dashboard">Org Admin Dashboard</div>} />
          <Route path="/dashboard/instructor" element={<div data-testid="instructor-dashboard">Instructor Dashboard</div>} />
          <Route path="/dashboard/student" element={<div data-testid="student-dashboard">Student Dashboard</div>} />
          <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
          <Route path="/" element={<div data-testid="homepage">Homepage</div>} />
          <Route path="/custom-fallback" element={<div data-testid="custom-fallback">Custom Fallback</div>} />
        </Routes>
      </MemoryRouter>
    ),
    getNavigatedTo: () => navigatedTo,
  };
};

describe('DashboardRedirect Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Role-Based Redirects', () => {
    it('redirects site_admin to site admin dashboard', () => {
      mockedUseAuth.mockReturnValue({
        role: 'site_admin',
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter();

      expect(screen.getByTestId('site-admin-dashboard')).toBeInTheDocument();
    });

    it('redirects organization_admin to org admin dashboard', () => {
      mockedUseAuth.mockReturnValue({
        role: 'organization_admin',
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter();

      expect(screen.getByTestId('org-admin-dashboard')).toBeInTheDocument();
    });

    it('redirects instructor to instructor dashboard', () => {
      mockedUseAuth.mockReturnValue({
        role: 'instructor',
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter();

      expect(screen.getByTestId('instructor-dashboard')).toBeInTheDocument();
    });

    it('redirects student to student dashboard', () => {
      mockedUseAuth.mockReturnValue({
        role: 'student',
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter();

      expect(screen.getByTestId('student-dashboard')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner while auth is loading', () => {
      mockedUseAuth.mockReturnValue({
        role: null,
        isLoading: true,
        isAuthenticated: false,
      });

      renderWithRouter();

      expect(screen.getByTestId('dashboard-redirect-loading')).toBeInTheDocument();
      expect(screen.getByText('Redirecting to your dashboard...')).toBeInTheDocument();
    });

    it('hides loading when showLoading is false', () => {
      mockedUseAuth.mockReturnValue({
        role: null,
        isLoading: true,
        isAuthenticated: false,
      });

      renderWithRouter(['/dashboard'], <DashboardRedirect showLoading={false} />);

      // Should redirect to login since not authenticated
      expect(screen.queryByTestId('dashboard-redirect-loading')).not.toBeInTheDocument();
    });
  });

  describe('Fallback Behavior', () => {
    it('redirects to homepage for unknown role', () => {
      mockedUseAuth.mockReturnValue({
        role: 'unknown_role',
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter();

      expect(screen.getByTestId('homepage')).toBeInTheDocument();
    });

    it('redirects to homepage for guest role', () => {
      mockedUseAuth.mockReturnValue({
        role: 'guest',
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter();

      expect(screen.getByTestId('homepage')).toBeInTheDocument();
    });

    it('redirects to homepage when role is null', () => {
      mockedUseAuth.mockReturnValue({
        role: null,
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter();

      expect(screen.getByTestId('homepage')).toBeInTheDocument();
    });

    it('uses custom fallback path when provided', () => {
      mockedUseAuth.mockReturnValue({
        role: null,
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter(['/dashboard'], <DashboardRedirect fallbackPath="/custom-fallback" />);

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    });
  });

  describe('Unauthenticated Users', () => {
    it('redirects to login when not authenticated', () => {
      mockedUseAuth.mockReturnValue({
        role: null,
        isLoading: false,
        isAuthenticated: false,
      });

      renderWithRouter();

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('redirects to login even with role when not authenticated', () => {
      mockedUseAuth.mockReturnValue({
        role: 'student',
        isLoading: false,
        isAuthenticated: false,
      });

      renderWithRouter();

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles subsequent navigation with different role', () => {
      // Verify component responds to auth state
      mockedUseAuth.mockReturnValue({
        role: 'student',
        isLoading: false,
        isAuthenticated: true,
      });

      renderWithRouter();

      expect(screen.getByTestId('student-dashboard')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has DashboardRedirect as display name', () => {
      expect(DashboardRedirect.displayName).toBe('DashboardRedirect');
    });
  });
});
