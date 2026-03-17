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

// Mock scrollIntoView for jsdom
Element.prototype.scrollIntoView = vi.fn();

describe('BulkEnrollStudents Component', () => {
  const mockPrograms = [
    { id: 'prog-1', title: 'Python Basics', difficulty_level: 'Beginner', track_id: 'track-1', published: true },
    { id: 'prog-2', title: 'Data Science', difficulty_level: 'Advanced', track_id: 'track-1', published: true },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
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
        // Component shows "Single Training Program" and "Complete Learning Track" cards
        expect(screen.getByText(/Single Training Program/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Complete Learning Track/i)).toBeInTheDocument();
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

      // Wait for page to load
      await waitFor(() => {
        expect(screen.getByText(/Enroll Students in Course/i)).toBeInTheDocument();
      });

      // The submit button is disabled when no program is selected and no student IDs entered
      // This IS the validation behavior - button is disabled until valid input
      // Note: getByText returns the span inside the button, so we need to find the button
      const submitButtonText = screen.getByText(/Enroll Students in Course/i);
      const submitButton = submitButtonText.closest('button');
      expect(submitButton).toBeDisabled();
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

      // Wait for combobox and programs to load
      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });

      // Select course using the custom Select component
      const courseSelect = screen.getByRole('combobox');
      await user.click(courseSelect);

      // Select the first program option from dropdown
      await waitFor(() => {
        const options = screen.getAllByRole('option');
        expect(options.length).toBeGreaterThan(0);
      });
      const programOption = screen.getByRole('option', { name: /Python Basics/i });
      await user.click(programOption);

      // Enter student IDs in the textarea
      const idsTextarea = screen.getByRole('textbox', { name: /Student IDs/i });
      await user.type(idsTextarea, 'student1\nstudent2\nstudent3');

      // Submit - button says "Enroll Students in Course"
      const submitButton = screen.getByText(/Enroll Students in Course/i);
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

      // Wait for Input Method section to render
      await waitFor(() => {
        expect(screen.getByText(/Input Method/i)).toBeInTheDocument();
      });

      // Initially Manual Entry is selected, so student IDs textarea should be visible
      expect(screen.getByRole('textbox', { name: /Student IDs/i })).toBeInTheDocument();

      // Find and click on the CSV Upload card - it's inside a Card component
      // Look for the "Upload file with student list" text which is unique to the CSV card
      const csvCardText = screen.getByText(/Upload file with student list/i);
      const csvCard = csvCardText.closest('[style*="cursor"]') || csvCardText.parentElement?.parentElement;
      if (csvCard) {
        await user.click(csvCard);
      }

      // After clicking, the file input should appear
      await waitFor(() => {
        const fileInput = document.querySelector('input[type="file"]');
        expect(fileInput).toBeInTheDocument();
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

      // Wait for page to load
      await waitFor(() => {
        expect(screen.getByText(/Input Method/i)).toBeInTheDocument();
      });

      // Switch to CSV mode by clicking on the card
      const csvCardText = screen.getByText(/Upload file with student list/i);
      const csvCard = csvCardText.closest('[style*="cursor"]') || csvCardText.parentElement?.parentElement;
      if (csvCard) {
        await user.click(csvCard);
      }

      // Wait for file input to appear
      await waitFor(() => {
        const fileInput = document.querySelector('input[type="file"]');
        expect(fileInput).toBeInTheDocument();
      });

      // Select course using the custom Select component
      const courseSelect = screen.getByRole('combobox');
      await user.click(courseSelect);
      await waitFor(() => {
        const options = screen.getAllByRole('option');
        expect(options.length).toBeGreaterThan(0);
      });
      const programOption = screen.getByRole('option', { name: /Python Basics/i });
      await user.click(programOption);

      // Upload file
      const file = new File(['student_id\nstudent1'], 'students.csv', { type: 'text/csv' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      await user.upload(fileInput, file);

      // Submit - button says "Upload & Enroll" in CSV mode
      const submitButton = screen.getByText(/Upload & Enroll/i);
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Successfully enrolled 5 student\(s\) from CSV/i)).toBeInTheDocument();
      });
    });
  });
});
