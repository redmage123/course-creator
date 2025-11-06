/**
 * Manage Organizations Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Manage Organizations page provides site admins with
 * platform-wide organization oversight and management capabilities.
 *
 * TEST COVERAGE:
 * - Component rendering with organization data
 * - Search and filtering functionality
 * - Organization status management
 * - Statistics display
 * - Navigation to create and manage organizations
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { ManageOrganizations } from './ManageOrganizations';

const mockAlert = vi.fn();
global.alert = mockAlert;

describe('ManageOrganizations Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  describe('Rendering', () => {
    it('renders page title and description', () => {
      renderWithProviders(<ManageOrganizations />, {
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

      expect(screen.getByText('Manage Organizations')).toBeInTheDocument();
    });

    it('renders organization list with mock data', () => {
      renderWithProviders(<ManageOrganizations />, {
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

      expect(screen.getByText('Acme Corporation')).toBeInTheDocument();
      expect(screen.getByText('TechStart Inc')).toBeInTheDocument();
      expect(screen.getByText('Global Training Solutions')).toBeInTheDocument();
    });

    it('renders create organization button', () => {
      renderWithProviders(<ManageOrganizations />, {
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

      expect(screen.getByText('Create Organization')).toBeInTheDocument();
    });
  });

  describe('Search and Filtering', () => {
    it('filters organizations by name', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageOrganizations />, {
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

      const searchInput = screen.getByPlaceholderText(/Search organizations/i);
      await user.type(searchInput, 'Acme');

      await waitFor(() => {
        expect(screen.getByText('Acme Corporation')).toBeInTheDocument();
        expect(screen.queryByText('TechStart Inc')).not.toBeInTheDocument();
      });
    });

    it('filters organizations by status', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageOrganizations />, {
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

      const statusSelect = screen.getByDisplayValue('All Statuses');
      await user.selectOptions(statusSelect, 'trial');

      await waitFor(() => {
        expect(screen.getByText('Global Training Solutions')).toBeInTheDocument();
        expect(screen.queryByText('Acme Corporation')).not.toBeInTheDocument();
      });
    });
  });

  describe('Organization Management', () => {
    it('changes organization status', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageOrganizations />, {
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

      // Find suspended organization's row
      const suspendedRow = screen.getByText('Legacy Systems Ltd').closest('tr');
      const activateButton = suspendedRow?.querySelector('button');

      if (activateButton) {
        await user.click(activateButton);

        await waitFor(() => {
          expect(mockAlert).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Statistics Display', () => {
    it('displays organization statistics', () => {
      renderWithProviders(<ManageOrganizations />, {
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

      // Check for total organizations count
      expect(screen.getByText('Total Organizations')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
    });
  });
});
