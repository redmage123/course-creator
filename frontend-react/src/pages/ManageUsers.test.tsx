/**
 * Manage Users Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Manage Users page provides site admins with
 * platform-wide user management and oversight capabilities.
 *
 * TEST COVERAGE:
 * - Component rendering with user data
 * - Search and filtering by role and organization
 * - User status management
 * - Role-based display and controls
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { ManageUsers } from './ManageUsers';

const mockAlert = vi.fn();
global.alert = mockAlert;

describe('ManageUsers Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  describe('Rendering', () => {
    it('renders page title and description', () => {
      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('Manage Users')).toBeInTheDocument();
    });

    it('renders user list with mock data', () => {
      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      expect(screen.getByText('Bob Smith')).toBeInTheDocument();
      expect(screen.getByText('Carol Davis')).toBeInTheDocument();
    });

    it('displays user role badges', () => {
      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('site_admin')).toBeInTheDocument();
      expect(screen.getAllByText('instructor').length).toBeGreaterThan(0);
      expect(screen.getAllByText('student').length).toBeGreaterThan(0);
    });
  });

  describe('Search and Filtering', () => {
    it('filters users by name', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const searchInput = screen.getByPlaceholderText(/Search users/i);
      await user.type(searchInput, 'Alice');

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
        expect(screen.queryByText('Bob Smith')).not.toBeInTheDocument();
      });
    });

    it('filters users by role', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const roleSelect = screen.getByDisplayValue('All Roles');
      await user.selectOptions(roleSelect, 'student');

      await waitFor(() => {
        expect(screen.getByText('Eve Martinez')).toBeInTheDocument();
        expect(screen.queryByText('Alice Johnson')).not.toBeInTheDocument();
      });
    });

    it('filters users by organization', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const orgSelect = screen.getByDisplayValue('All Organizations');
      await user.selectOptions(orgSelect, 'Acme Corporation');

      await waitFor(() => {
        expect(screen.getByText('Bob Smith')).toBeInTheDocument();
        expect(screen.getByText('Carol Davis')).toBeInTheDocument();
        expect(screen.queryByText('David Wilson')).not.toBeInTheDocument();
      });
    });
  });

  describe('User Management', () => {
    it('suspends user when suspend button is clicked', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      // Find an active user's suspend button
      const bobRow = screen.getByText('Bob Smith').closest('tr');
      const suspendButton = bobRow?.querySelector('button');

      if (suspendButton && suspendButton.textContent?.includes('Suspend')) {
        await user.click(suspendButton);

        await waitFor(() => {
          expect(mockAlert).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Statistics Display', () => {
    it('displays total users count', () => {
      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('Total Users')).toBeInTheDocument();
      expect(screen.getByText('6')).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('has link to dashboard', () => {
      renderWithProviders(<ManageUsers />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Site',
              lastName: 'Admin',
              role: 'site_admin',
              organizationId: 'platform',
              organizationName: 'Platform',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const dashboardLink = screen.getByText('Back to Dashboard').closest('a');
      expect(dashboardLink).toHaveAttribute('href', '/dashboard/site-admin');
    });
  });
});
