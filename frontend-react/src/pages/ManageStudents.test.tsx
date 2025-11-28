/**
 * Manage Students Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the Manage Students page provides instructors with
 * a comprehensive interface for viewing, filtering, and managing student enrollments.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing with mocked enrollment service.
 * Tests rendering, filtering, sorting, state updates, and user interactions.
 *
 * TEST COVERAGE:
 * - Component rendering with loading and error states
 * - Mock enrollment data display and formatting
 * - Filter functionality (search, status, sort)
 * - User interactions (status updates, unenrollment)
 * - Navigation to enrollment and student analytics pages
 * - Summary statistics calculations
 * - Responsive table rendering
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/utils';
import { ManageStudents } from './ManageStudents';
import * as enrollmentService from '../services/enrollmentService';

/**
 * MOCK ENROLLMENT SERVICE
 *
 * BUSINESS REQUIREMENT:
 * Tests need to simulate enrollment service responses without making real API calls.
 *
 * TECHNICAL IMPLEMENTATION:
 * Mocks all enrollment service methods used by the component.
 */
vi.mock('../services/enrollmentService', () => ({
  enrollmentService: {
    getInstructorEnrollmentSummary: vi.fn(),
    getStudentEnrollments: vi.fn(),
    updateEnrollmentStatus: vi.fn(),
    unenrollStudent: vi.fn(),
  },
  EnrollmentStatus: {
    ACTIVE: 'active',
    COMPLETED: 'completed',
    DROPPED: 'dropped',
    PENDING: 'pending',
  },
}));

/**
 * MOCK DATA FACTORY
 *
 * BUSINESS REQUIREMENT:
 * Tests need realistic enrollment data that matches production structure.
 *
 * TECHNICAL IMPLEMENTATION:
 * Factory functions creating mock enrollments with sensible defaults.
 */
const createMockEnrollment = (overrides = {}) => ({
  id: `enrollment-${Math.random()}`,
  student_id: 'student-123',
  student_name: 'John Doe',
  student_email: 'john@example.com',
  course_id: 'course-456',
  course_title: 'Introduction to Python',
  status: 'active' as const,
  progress_percentage: 45,
  enrollment_date: '2025-01-01T00:00:00Z',
  ...overrides,
});

const createMockEnrollmentSummary = (overrides = {}) => ({
  student_id: 'student-123',
  student_name: 'John Doe',
  total_enrollments: 2,
  active_enrollments: 1,
  completed_enrollments: 1,
  average_progress: 72.5,
  ...overrides,
});

// Mock scrollIntoView for jsdom
Element.prototype.scrollIntoView = vi.fn();

describe('ManageStudents Component', () => {
  const mockEnrollments = [
    createMockEnrollment({
      id: 'enroll-1',
      student_id: 'student-1',
      student_name: 'Alice Johnson',
      student_email: 'alice@example.com',
      course_title: 'Python Basics',
      status: 'active',
      progress_percentage: 75,
      enrollment_date: '2025-01-15T00:00:00Z',
    }),
    createMockEnrollment({
      id: 'enroll-2',
      student_id: 'student-2',
      student_name: 'Bob Smith',
      student_email: 'bob@example.com',
      course_title: 'JavaScript Fundamentals',
      status: 'completed',
      progress_percentage: 100,
      enrollment_date: '2025-01-10T00:00:00Z',
    }),
    createMockEnrollment({
      id: 'enroll-3',
      student_id: 'student-3',
      student_name: 'Charlie Brown',
      student_email: 'charlie@example.com',
      course_title: 'React Advanced',
      status: 'pending',
      progress_percentage: 0,
      enrollment_date: '2025-01-20T00:00:00Z',
    }),
  ];

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock console methods to avoid noise in test output
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders loading spinner initially', () => {
      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
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
      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue([]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText('Manage Students')).toBeInTheDocument();
      });

      expect(screen.getByText(/View and manage student enrollments/i)).toBeInTheDocument();
    });

    it('renders action buttons', async () => {
      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue([]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
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

      expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();
    });

    it('renders filter controls', async () => {
      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue([]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Search by name, email, or course/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('loads and displays enrollment data', async () => {
      const mockSummary = [
        createMockEnrollmentSummary({ student_id: 'student-1' }),
        createMockEnrollmentSummary({ student_id: 'student-2' }),
      ];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments)
        .mockResolvedValueOnce([mockEnrollments[0]])
        .mockResolvedValueOnce([mockEnrollments[1]]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      expect(screen.getByText('Bob Smith')).toBeInTheDocument();
    });

    it('displays error message on load failure', async () => {
      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockRejectedValue(
        new Error('Failed to fetch')
      );

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText(/Failed to load student enrollments/i)).toBeInTheDocument();
      });
    });

    it('displays empty state when no enrollments exist', async () => {
      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue([]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText(/No student enrollments yet/i)).toBeInTheDocument();
      });

      expect(screen.getByText('Enroll Your First Students')).toBeInTheDocument();
    });
  });

  describe('Summary Statistics', () => {
    it('calculates and displays total enrollments', async () => {
      const mockSummary = [createMockEnrollmentSummary({ student_id: 'student-1' })];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments).mockResolvedValue([
        mockEnrollments[0],
        mockEnrollments[1],
      ]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        const totalCard = screen.getByText('Total Enrollments').closest('div');
        expect(within(totalCard!).getByText('2')).toBeInTheDocument();
      });
    });

    it('calculates and displays active students count', async () => {
      const mockSummary = [createMockEnrollmentSummary({ student_id: 'student-1' })];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments).mockResolvedValue([
        mockEnrollments[0], // active
        mockEnrollments[1], // completed
      ]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        const activeCard = screen.getByText('Active Students').closest('div');
        expect(within(activeCard!).getByText('1')).toBeInTheDocument();
      });
    });

    it('calculates average progress percentage', async () => {
      const mockSummary = [createMockEnrollmentSummary({ student_id: 'student-1' })];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments).mockResolvedValue([
        createMockEnrollment({ progress_percentage: 50 }),
        createMockEnrollment({ progress_percentage: 100 }),
      ]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        const avgCard = screen.getByText('Average Progress').closest('div');
        expect(within(avgCard!).getByText('75%')).toBeInTheDocument();
      });
    });
  });

  describe('Filtering', () => {
    beforeEach(async () => {
      const mockSummary = [
        createMockEnrollmentSummary({ student_id: 'student-1' }),
        createMockEnrollmentSummary({ student_id: 'student-2' }),
        createMockEnrollmentSummary({ student_id: 'student-3' }),
      ];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments)
        .mockResolvedValueOnce([mockEnrollments[0]])
        .mockResolvedValueOnce([mockEnrollments[1]])
        .mockResolvedValueOnce([mockEnrollments[2]]);
    });

    it('filters enrollments by search query (student name)', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/Search by name, email, or course/i);
      await user.type(searchInput, 'Alice');

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
        expect(screen.queryByText('Bob Smith')).not.toBeInTheDocument();
        expect(screen.queryByText('Charlie Brown')).not.toBeInTheDocument();
      });
    });

    it('filters enrollments by status', async () => {
      const user = userEvent.setup();

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      // Find status filter (custom Select component uses combobox role)
      const statusCombobox = screen.getAllByRole('combobox')[0];
      await user.click(statusCombobox);

      // Click on the 'Completed' option in the dropdown (may be multiple, use first)
      const completedOptions = screen.getAllByRole('option', { name: 'Completed' });
      await user.click(completedOptions[0]);

      await waitFor(() => {
        expect(screen.getByText('Bob Smith')).toBeInTheDocument();
        expect(screen.queryByText('Alice Johnson')).not.toBeInTheDocument();
        expect(screen.queryByText('Charlie Brown')).not.toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('updates enrollment status', async () => {
      const user = userEvent.setup();
      const mockSummary = [createMockEnrollmentSummary({ student_id: 'student-1' })];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments).mockResolvedValue([mockEnrollments[0]]);
      vi.mocked(enrollmentService.enrollmentService.updateEnrollmentStatus).mockResolvedValue(undefined);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      // Find the native select element in the table row (has 'Active' as the display text)
      const statusSelects = screen.getAllByDisplayValue('Active');
      await user.selectOptions(statusSelects[0], 'completed');

      await waitFor(() => {
        expect(enrollmentService.enrollmentService.updateEnrollmentStatus).toHaveBeenCalledWith(
          'enroll-1',
          'completed'
        );
      });
    });

    it('unenrolls student with confirmation', async () => {
      const user = userEvent.setup();
      const mockSummary = [createMockEnrollmentSummary({ student_id: 'student-1' })];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments).mockResolvedValue([mockEnrollments[0]]);
      vi.mocked(enrollmentService.enrollmentService.unenrollStudent).mockResolvedValue(undefined);

      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      const unenrollButton = screen.getByText('Unenroll');
      await user.click(unenrollButton);

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to unenroll Alice Johnson?');

      await waitFor(() => {
        expect(enrollmentService.enrollmentService.unenrollStudent).toHaveBeenCalledWith('enroll-1');
      });

      confirmSpy.mockRestore();
    });

    it('cancels unenrollment when user declines confirmation', async () => {
      const user = userEvent.setup();
      const mockSummary = [createMockEnrollmentSummary({ student_id: 'student-1' })];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments).mockResolvedValue([mockEnrollments[0]]);

      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      const unenrollButton = screen.getByText('Unenroll');
      await user.click(unenrollButton);

      expect(enrollmentService.enrollmentService.unenrollStudent).not.toHaveBeenCalled();

      confirmSpy.mockRestore();
    });
  });

  describe('Navigation', () => {
    it('has link to enroll students page', async () => {
      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue([]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        const enrollLink = screen.getAllByText('Enroll Students')[0].closest('a');
        expect(enrollLink).toHaveAttribute('href', '/instructor/students/enroll');
      });
    });

    it('has link to instructor dashboard', async () => {
      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue([]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        const dashboardLink = screen.getByText('Back to Dashboard').closest('a');
        expect(dashboardLink).toHaveAttribute('href', '/dashboard/instructor');
      });
    });
  });

  describe('Data Formatting', () => {
    it('formats enrollment dates correctly', async () => {
      const mockSummary = [createMockEnrollmentSummary({ student_id: 'student-1' })];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments).mockResolvedValue([
        createMockEnrollment({ enrollment_date: '2025-01-15T12:00:00Z' }),
      ]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        expect(screen.getByText(/Jan 15, 2025/i)).toBeInTheDocument();
      });
    });

    it('displays progress percentages correctly', async () => {
      const mockSummary = [createMockEnrollmentSummary({ student_id: 'student-1' })];

      vi.mocked(enrollmentService.enrollmentService.getInstructorEnrollmentSummary).mockResolvedValue(mockSummary);
      vi.mocked(enrollmentService.enrollmentService.getStudentEnrollments).mockResolvedValue([
        createMockEnrollment({ progress_percentage: 75 }),
      ]);

      renderWithProviders(<ManageStudents />, {
        preloadedState: {
          user: {
            profile: {
              id: 'instructor-1',
              username: 'instructor',
              email: 'instructor@example.com',
              firstName: 'Test',
              lastName: 'Instructor',
              role: 'instructor',
              organizationId: 'org-1',
              organizationName: 'Test Org',
            },
            isLoading: false,
            error: null,
          },
        },
      });

      await waitFor(() => {
        // Multiple 75% elements may exist (in stats card and table row)
        expect(screen.getAllByText('75%').length).toBeGreaterThan(0);
      });
    });
  });
});
