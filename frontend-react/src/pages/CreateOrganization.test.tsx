/**
 * Create Organization Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Create Organization page provides site admins with
 * a streamlined multi-step workflow for onboarding new organizations.
 *
 * TEST COVERAGE:
 * - Multi-step form navigation
 * - Form validation for each step
 * - Plan preset selection
 * - Organization creation submission
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { CreateOrganization } from './CreateOrganization';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockAlert = vi.fn();
global.alert = mockAlert;

describe('CreateOrganization Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Rendering', () => {
    it('renders page title and step 1', () => {
      renderWithProviders(<CreateOrganization />, {
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

      expect(screen.getByText('Create New Organization')).toBeInTheDocument();
      expect(screen.getByText(/Step 1/i)).toBeInTheDocument();
    });

    it('renders basic information form fields', () => {
      renderWithProviders(<CreateOrganization />, {
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

      expect(screen.getByLabelText(/Organization Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Contact Email/i)).toBeInTheDocument();
    });
  });

  describe('Multi-step Navigation', () => {
    it('advances to step 2 when next is clicked', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<CreateOrganization />, {
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

      // Fill required fields
      const orgNameInput = screen.getByLabelText(/Organization Name/i);
      const emailInput = screen.getByLabelText(/Contact Email/i);

      await user.type(orgNameInput, 'New Organization');
      await user.type(emailInput, 'contact@neworg.com');

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/Step 2/i)).toBeInTheDocument();
      });
    });

    it('goes back to step 1 when back is clicked', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<CreateOrganization />, {
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

      // Fill and advance to step 2
      const orgNameInput = screen.getByLabelText(/Organization Name/i);
      await user.type(orgNameInput, 'New Organization');

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/Step 2/i)).toBeInTheDocument();
      });

      // Go back
      const backButton = screen.getByText('Back');
      await user.click(backButton);

      await waitFor(() => {
        expect(screen.getByText(/Step 1/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('validates required fields in step 1', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<CreateOrganization />, {
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

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(expect.stringContaining('required'));
      });
    });
  });

  describe('Plan Selection', () => {
    it('applies plan presets when plan is selected', async () => {
      const user = userEvent.setup({ delay: null });

      renderWithProviders(<CreateOrganization />, {
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

      // Navigate to step 3 (subscription)
      const orgNameInput = screen.getByLabelText(/Organization Name/i);
      await user.type(orgNameInput, 'New Organization');

      let nextButton = screen.getByText('Next');
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/Step 2/i)).toBeInTheDocument();
      });

      nextButton = screen.getByText('Next');
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/Step 3/i)).toBeInTheDocument();
      });

      // Select Enterprise plan
      const planSelect = screen.getByDisplayValue('Professional');
      await user.selectOptions(planSelect, 'Enterprise');

      // Check that preset values are applied (Enterprise has 50 max trainers)
      const maxTrainersInput = screen.getByLabelText(/Maximum Trainers/i);
      expect(maxTrainersInput).toHaveValue(50);
    });
  });
});
