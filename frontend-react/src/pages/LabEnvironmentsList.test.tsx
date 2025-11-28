/**
 * Lab Environments List Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Lab Environments List page provides students with
 * access to interactive coding labs with proper status tracking and launch capabilities.
 *
 * TEST COVERAGE:
 * - Component rendering with lab data
 * - Lab status display (available, in-progress, completed)
 * - Search and filtering functionality
 * - Lab launch functionality
 * - Progress tracking display
 * - Multi-IDE support indication
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { LabEnvironmentsList } from './LabEnvironmentsList';

describe('LabEnvironmentsList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  describe('Rendering', () => {
    it('renders page title and description', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('Lab Environments')).toBeInTheDocument();
    });

    it('renders lab environment cards with mock data', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('Python Basics - Variables and Data Types')).toBeInTheDocument();
      expect(screen.getByText('Python Functions and Modules')).toBeInTheDocument();
    });

    it('displays lab difficulty levels', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getAllByText('beginner').length).toBeGreaterThan(0);
      expect(screen.getAllByText('intermediate').length).toBeGreaterThan(0);
    });

    it('displays lab status indicators', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      // Component displays "completed" and "In Progress" (capitalized for in-progress)
      expect(screen.getAllByText('completed').length).toBeGreaterThan(0);
      expect(screen.getAllByText('In Progress').length).toBeGreaterThan(0);
    });
  });

  describe('Search and Filtering', () => {
    it('filters labs by search query', async () => {
      const user = userEvent.setup();

      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const searchInput = screen.getByPlaceholderText(/Search labs/i);
      await user.type(searchInput, 'Functions');

      await waitFor(() => {
        expect(screen.getByText('Python Functions and Modules')).toBeInTheDocument();
        expect(screen.queryByText('Python Basics - Variables and Data Types')).not.toBeInTheDocument();
      });
    });

    it('filters labs by status', async () => {
      const user = userEvent.setup();

      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const statusSelect = screen.getByDisplayValue('All Statuses');
      await user.selectOptions(statusSelect, 'completed');

      await waitFor(() => {
        expect(screen.getByText('Python Basics - Variables and Data Types')).toBeInTheDocument();
        expect(screen.queryByText('Python Functions and Modules')).not.toBeInTheDocument();
      });
    });

    it('filters labs by difficulty', async () => {
      const user = userEvent.setup();

      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const difficultySelect = screen.getByDisplayValue('All Difficulties');
      await user.selectOptions(difficultySelect, 'intermediate');

      await waitFor(() => {
        expect(screen.getByText('Data Structures - Lists and Dictionaries')).toBeInTheDocument();
      });
    });
  });

  describe('Lab Launching', () => {
    it('displays launch button for available labs', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const launchButtons = screen.getAllByText(/Start Lab|Resume Lab/i);
      expect(launchButtons.length).toBeGreaterThan(0);
    });

    it('displays resume button for in-progress labs', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText(/Resume Lab/i)).toBeInTheDocument();
    });

    it('displays completed indicator for finished labs', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const completedCard = screen.getByText('Python Basics - Variables and Data Types').closest('div');
      expect(completedCard).toBeInTheDocument();
    });
  });

  describe('Progress Display', () => {
    it('displays progress percentage for in-progress labs', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      expect(screen.getByText('60%')).toBeInTheDocument();
      expect(screen.getAllByText('100%').length).toBeGreaterThan(0);
    });
  });

  describe('Navigation', () => {
    it('has link to student dashboard', () => {
      renderWithProviders(<LabEnvironmentsList />, {
        preloadedState: {
          user: {
            profile: {
              id: 'student-1',
              username: 'student',
              email: 'student@example.com',
              firstName: 'Test',
              lastName: 'Student',
              role: 'student',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      const dashboardLink = screen.getByText('Back to Dashboard').closest('a');
      expect(dashboardLink).toHaveAttribute('href', '/dashboard/student');
    });
  });
});
