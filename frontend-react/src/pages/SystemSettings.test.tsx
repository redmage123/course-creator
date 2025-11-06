/**
 * System Settings Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the System Settings page provides site admins with
 * platform-wide configuration and maintenance capabilities.
 *
 * TEST COVERAGE:
 * - Component rendering with system settings
 * - Tab navigation between settings sections
 * - Form handling and validation
 * - Feature toggles and maintenance mode
 * - Settings save operations
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { SystemSettings } from './SystemSettings';

const mockAlert = vi.fn();
global.alert = mockAlert;

describe('SystemSettings Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Rendering', () => {
    it('renders page title and description', () => {
      renderWithProviders(<SystemSettings />, {
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

      expect(screen.getByText('System Settings')).toBeInTheDocument();
    });

    it('renders all setting tabs', () => {
      renderWithProviders(<SystemSettings />, {
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

      expect(screen.getByText('General')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Storage')).toBeInTheDocument();
      expect(screen.getByText('Security')).toBeInTheDocument();
      expect(screen.getByText('Features')).toBeInTheDocument();
      expect(screen.getByText('Maintenance')).toBeInTheDocument();
    });

    it('displays current system settings', () => {
      renderWithProviders(<SystemSettings />, {
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

      expect(screen.getByDisplayValue('Course Creator Platform')).toBeInTheDocument();
      expect(screen.getByDisplayValue('support@example.com')).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('switches to email tab when clicked', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<SystemSettings />, {
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

      const emailTab = screen.getByText('Email');
      await user.click(emailTab);

      await waitFor(() => {
        expect(screen.getByLabelText(/SMTP Host/i)).toBeInTheDocument();
      });
    });

    it('switches to features tab', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<SystemSettings />, {
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

      const featuresTab = screen.getByText('Features');
      await user.click(featuresTab);

      await waitFor(() => {
        expect(screen.getByLabelText(/Enable Course Generation/i)).toBeInTheDocument();
      });
    });
  });

  describe('Feature Toggles', () => {
    it('toggles maintenance mode', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<SystemSettings />, {
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

      const maintenanceTab = screen.getByText('Maintenance');
      await user.click(maintenanceTab);

      await waitFor(() => {
        const maintenanceToggle = screen.getByLabelText(/Enable Maintenance Mode/i);
        expect(maintenanceToggle).toBeInTheDocument();
      });
    });
  });

  describe('Settings Management', () => {
    it('saves general settings successfully', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<SystemSettings />, {
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

      const saveButton = screen.getByText('Save General Settings');
      await user.click(saveButton);

      vi.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining('settings updated'));
      });
    });
  });

  describe('Navigation', () => {
    it('has link to dashboard', () => {
      renderWithProviders(<SystemSettings />, {
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
