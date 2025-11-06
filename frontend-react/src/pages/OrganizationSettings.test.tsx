/**
 * Organization Settings Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Organization Settings page provides org admins with
 * comprehensive configuration options for branding, policies, and integrations.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library with mock settings data.
 * Tests tabbed navigation, form handling, and settings updates.
 *
 * TEST COVERAGE:
 * - Component rendering with settings data
 * - Tab navigation between settings sections
 * - Form input handling and validation
 * - Settings save operations
 * - Branding preview functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { OrganizationSettings } from './OrganizationSettings';

const mockAlert = vi.fn();
global.alert = mockAlert;

describe('OrganizationSettings Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Rendering', () => {
    it('renders page title and description', () => {
      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('Organization Settings')).toBeInTheDocument();
    });

    it('renders all setting tabs', () => {
      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('Organization Profile')).toBeInTheDocument();
      expect(screen.getByText('Branding')).toBeInTheDocument();
      expect(screen.getByText('Training Policies')).toBeInTheDocument();
      expect(screen.getByText('Integrations')).toBeInTheDocument();
      expect(screen.getByText('Subscription')).toBeInTheDocument();
    });

    it('defaults to profile tab', () => {
      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByLabelText(/Organization Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Contact Email/i)).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('switches to branding tab when clicked', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const brandingTab = screen.getByText('Branding');
      await user.click(brandingTab);

      await waitFor(() => {
        expect(screen.getByLabelText(/Primary Color/i)).toBeInTheDocument();
      });
    });

    it('switches to training policies tab', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const trainingTab = screen.getByText('Training Policies');
      await user.click(trainingTab);

      await waitFor(() => {
        expect(screen.getByLabelText(/Minimum Passing Score/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Handling', () => {
    it('updates organization name', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const nameInput = screen.getByLabelText(/Organization Name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Organization');

      expect(nameInput).toHaveValue('Updated Organization');
    });

    it('saves profile settings successfully', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const saveButton = screen.getByText('Save Profile');
      await user.click(saveButton);

      vi.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Profile settings updated successfully!');
      });
    });
  });

  describe('Settings Display', () => {
    it('displays current organization settings', () => {
      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByDisplayValue('Acme Corporation')).toBeInTheDocument();
      expect(screen.getByDisplayValue('admin@acme.com')).toBeInTheDocument();
    });

    it('displays subscription information in subscription tab', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const subscriptionTab = screen.getByText('Subscription');
      await user.click(subscriptionTab);

      await waitFor(() => {
        expect(screen.getByText(/Enterprise/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('has link to dashboard', () => {
      renderWithProviders(<OrganizationSettings />, {
        preloadedState: {
          user: {
            profile: {
              id: 'admin-1',
              username: 'admin',
              email: 'admin@example.com',
              firstName: 'Test',
              lastName: 'Admin',
              role: 'org_admin',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const dashboardLink = screen.getByText('Back to Dashboard').closest('a');
      expect(dashboardLink).toHaveAttribute('href', '/dashboard/org-admin');
    });
  });
});
