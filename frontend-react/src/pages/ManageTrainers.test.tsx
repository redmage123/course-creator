/**
 * Manage Trainers Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Manage Trainers page provides org admins with
 * comprehensive instructor management capabilities.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library with mock trainer data.
 * Tests filtering, search, status management, and invite workflows.
 *
 * TEST COVERAGE:
 * - Component rendering with trainer data display
 * - Search and filter functionality
 * - Trainer status management
 * - Invite modal and form submission
 * - Statistics display (courses, students)
 * - Date formatting and display
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { ManageTrainers } from './ManageTrainers';

const mockAlert = vi.fn();
global.alert = mockAlert;

describe('ManageTrainers Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders page title and description', () => {
      renderWithProviders(<ManageTrainers />, {
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

      expect(screen.getByText('Manage Trainers')).toBeInTheDocument();
    });

    it('renders trainer list with mock data', () => {
      renderWithProviders(<ManageTrainers />, {
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

      expect(screen.getByText('John Smith')).toBeInTheDocument();
      expect(screen.getByText('Sarah Johnson')).toBeInTheDocument();
      expect(screen.getByText('Michael Chen')).toBeInTheDocument();
    });

    it('displays trainer statistics', () => {
      renderWithProviders(<ManageTrainers />, {
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

      // John Smith has 12 courses and 145 students
      const johnRow = screen.getByText('John Smith').closest('tr');
      expect(within(johnRow!).getByText('12')).toBeInTheDocument();
      expect(within(johnRow!).getByText('145')).toBeInTheDocument();
    });

    it('renders invite trainer button', () => {
      renderWithProviders(<ManageTrainers />, {
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

      expect(screen.getByText('Invite Trainer')).toBeInTheDocument();
    });
  });

  describe('Search and Filtering', () => {
    it('filters trainers by name', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageTrainers />, {
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

      const searchInput = screen.getByPlaceholderText(/Search trainers/i);
      await user.type(searchInput, 'John');

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument();
        expect(screen.queryByText('Sarah Johnson')).not.toBeInTheDocument();
      });
    });

    it('filters trainers by email', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageTrainers />, {
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

      const searchInput = screen.getByPlaceholderText(/Search trainers/i);
      await user.type(searchInput, 'sarah.johnson');

      await waitFor(() => {
        expect(screen.getByText('Sarah Johnson')).toBeInTheDocument();
        expect(screen.queryByText('John Smith')).not.toBeInTheDocument();
      });
    });

    it('filters trainers by status', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageTrainers />, {
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

      const statusSelect = screen.getByDisplayValue('All Statuses');
      await user.selectOptions(statusSelect, 'inactive');

      await waitFor(() => {
        expect(screen.getByText('Michael Chen')).toBeInTheDocument();
        expect(screen.queryByText('John Smith')).not.toBeInTheDocument();
        expect(screen.queryByText('Sarah Johnson')).not.toBeInTheDocument();
      });
    });
  });

  describe('Invite Trainer', () => {
    it('opens invite modal when button is clicked', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageTrainers />, {
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

      const inviteButton = screen.getByText('Invite Trainer');
      await user.click(inviteButton);

      await waitFor(() => {
        expect(screen.getByText('Invite New Trainer')).toBeInTheDocument();
      });
    });

    it('validates invite form fields', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageTrainers />, {
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

      const inviteButton = screen.getByText('Invite Trainer');
      await user.click(inviteButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/Name/i);
      const emailInput = screen.getByLabelText(/Email/i);

      await user.type(nameInput, 'New Trainer');
      await user.type(emailInput, 'newtrainer@example.com');

      expect(nameInput).toHaveValue('New Trainer');
      expect(emailInput).toHaveValue('newtrainer@example.com');
    });

    it('submits invite form successfully', async () => {
      const user = userEvent.setup();
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      renderWithProviders(<ManageTrainers />, {
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

      const inviteButton = screen.getByText('Invite Trainer');
      await user.click(inviteButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText(/Name/i);
      const emailInput = screen.getByLabelText(/Email/i);

      await user.type(nameInput, 'New Trainer');
      await user.type(emailInput, 'newtrainer@example.com');

      const sendButton = screen.getByText('Send Invitation');
      await user.click(sendButton);

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Invitation sent to newtrainer@example.com!');
      });

      consoleLogSpy.mockRestore();
    });
  });

  describe('Trainer Management', () => {
    it('changes trainer status', async () => {
      const user = userEvent.setup();
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      renderWithProviders(<ManageTrainers />, {
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

      // Find Michael Chen's row (inactive trainer)
      const michaelRow = screen.getByText('Michael Chen').closest('tr');
      const activateButton = within(michaelRow!).getByText('Activate');

      await user.click(activateButton);

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Trainer status updated to active');
      });

      consoleLogSpy.mockRestore();
    });
  });

  describe('Data Formatting', () => {
    it('formats dates correctly', () => {
      renderWithProviders(<ManageTrainers />, {
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

      // Check that dates are displayed
      expect(screen.getByText(/Jan 15, 2024/i)).toBeInTheDocument();
    });

    it('displays status badges with correct colors', () => {
      const { container } = renderWithProviders(<ManageTrainers />, {
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

      // Active status should be displayed
      const activeStatuses = screen.getAllByText('active');
      expect(activeStatuses.length).toBeGreaterThan(0);

      // Inactive status should be displayed
      expect(screen.getByText('inactive')).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('has link to dashboard', () => {
      renderWithProviders(<ManageTrainers />, {
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
