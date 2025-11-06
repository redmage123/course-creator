/**
 * Bulk Enroll Students Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Bulk Enroll Students page provides org admins with
 * comprehensive tools for large-scale student enrollment operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library with mocked enrollment and training program services.
 * Tests course and track enrollment modes, CSV processing, and bulk operations.
 *
 * TEST COVERAGE:
 * - Component rendering with loading states
 * - Target selection (course vs track)
 * - Manual bulk enrollment with student ID lists
 * - CSV file upload and processing
 * - Bulk result display with success/failure feedback
 * - Form validation and error handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { BulkEnrollStudents } from './BulkEnrollStudents';
import * as enrollmentService from '../services/enrollmentService';
import * as trainingProgramService from '../services/trainingProgramService';

vi.mock('../services/enrollmentService');
vi.mock('../services/trainingProgramService');

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('BulkEnrollStudents Component', () => {
  const mockPrograms = [
    { id: 'prog-1', title: 'Python Basics', difficulty_level: 'Beginner', track_id: 'track-1', published: true },
    { id: 'prog-2', title: 'Data Science', difficulty_level: 'Advanced', track_id: 'track-1', published: true },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Rendering', () => {
    it('renders loading spinner while fetching programs', () => {
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockImplementation(
        () => new Promise(() => {})
      );

      renderWithProviders(<BulkEnrollStudents />, {
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

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders page title and description', async () => {
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockResolvedValue({
        data: mockPrograms,
      } as any);

      renderWithProviders(<BulkEnrollStudents />, {
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

      await waitFor(() => {
        expect(screen.getByText('Bulk Enroll Students')).toBeInTheDocument();
      });
    });

    it('renders course and track enrollment options', async () => {
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockResolvedValue({
        data: mockPrograms,
      } as any);

      renderWithProviders(<BulkEnrollStudents />, {
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

      await waitFor(() => {
        expect(screen.getByText(/Enroll in Single Course/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Enroll in Learning Track/i)).toBeInTheDocument();
    });
  });

  describe('Program Loading', () => {
    it('loads and displays organization programs', async () => {
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockResolvedValue({
        data: mockPrograms,
      } as any);

      renderWithProviders(<BulkEnrollStudents />, {
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

      await waitFor(() => {
        expect(trainingProgramService.trainingProgramService.getTrainingPrograms).toHaveBeenCalledWith({
          organization_id: 'org-1',
          published: true,
        });
      });
    });

    it('displays error when program loading fails', async () => {
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockRejectedValue(
        new Error('Network error')
      );

      renderWithProviders(<BulkEnrollStudents />, {
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

      await waitFor(() => {
        expect(screen.getByText(/Failed to load organization training programs/i)).toBeInTheDocument();
      });
    });
  });

  describe('Bulk Enrollment', () => {
    it('validates required fields', async () => {
      const user = userEvent.setup({ delay: null });
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockResolvedValue({
        data: mockPrograms,
      } as any);

      renderWithProviders(<BulkEnrollStudents />, {
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

      await waitFor(() => {
        expect(screen.getByText('Enroll Students')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('Enroll Students');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Please select a training program/i)).toBeInTheDocument();
      });
    });

    it('successfully processes bulk enrollment', async () => {
      const user = userEvent.setup({ delay: null });
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockResolvedValue({
        data: mockPrograms,
      } as any);
      vi.mocked(enrollmentService.enrollmentService.bulkEnrollStudents).mockResolvedValue({
        success_count: 3,
        failed_count: 0,
        failed_students: [],
      });

      renderWithProviders(<BulkEnrollStudents />, {
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

      await waitFor(() => {
        expect(screen.getByText('Python Basics (Beginner)')).toBeInTheDocument();
      });

      // Select course
      const courseSelect = screen.getByRole('combobox');
      await user.selectOptions(courseSelect, 'prog-1');

      // Enter student IDs
      const idsTextarea = screen.getByPlaceholderText(/Enter student IDs/i);
      await user.type(idsTextarea, 'student1\nstudent2\nstudent3');

      // Submit
      const submitButton = screen.getByText('Enroll Students');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Successfully enrolled 3 student\(s\)/i)).toBeInTheDocument();
      });
    });
  });

  describe('CSV Upload', () => {
    it('switches to CSV upload mode', async () => {
      const user = userEvent.setup({ delay: null });
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockResolvedValue({
        data: mockPrograms,
      } as any);

      renderWithProviders(<BulkEnrollStudents />, {
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

      await waitFor(() => {
        expect(screen.getByText(/Use CSV Upload/i)).toBeInTheDocument();
      });

      const csvToggle = screen.getByLabelText(/Use CSV Upload/i);
      await user.click(csvToggle);

      await waitFor(() => {
        expect(screen.getByLabelText(/CSV File/i)).toBeInTheDocument();
      });
    });

    it('handles CSV file upload successfully', async () => {
      const user = userEvent.setup({ delay: null });
      vi.mocked(trainingProgramService.trainingProgramService.getTrainingPrograms).mockResolvedValue({
        data: mockPrograms,
      } as any);
      vi.mocked(enrollmentService.enrollmentService.bulkEnrollFromCSV).mockResolvedValue({
        success_count: 5,
        failed_count: 0,
        failed_students: [],
      });

      renderWithProviders(<BulkEnrollStudents />, {
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

      await waitFor(() => {
        expect(screen.getByText(/Use CSV Upload/i)).toBeInTheDocument();
      });

      // Switch to CSV mode
      const csvToggle = screen.getByLabelText(/Use CSV Upload/i);
      await user.click(csvToggle);

      await waitFor(() => {
        expect(screen.getByLabelText(/CSV File/i)).toBeInTheDocument();
      });

      // Select course
      const courseSelect = screen.getByRole('combobox');
      await user.selectOptions(courseSelect, 'prog-1');

      // Upload file
      const file = new File(['student_id\nstudent1'], 'students.csv', { type: 'text/csv' });
      const fileInput = screen.getByLabelText(/CSV File/i);
      await user.upload(fileInput, file);

      // Submit
      const submitButton = screen.getByText('Enroll Students');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Successfully enrolled 5 student\(s\) from CSV/i)).toBeInTheDocument();
      });
    });
  });
});
