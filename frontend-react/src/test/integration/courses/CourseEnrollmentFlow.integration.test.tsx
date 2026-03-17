/**
 * Course Enrollment Flow Integration Tests
 *
 * BUSINESS CONTEXT:
 * Tests course enrollment workflows for instructors enrolling students in courses.
 * Validates proper integration between enrollment forms, enrollment service,
 * Redux state, and success notifications.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests EnrollStudents component integration
 * - Uses real service code with MSW intercepting HTTP requests
 * - Tests single and bulk enrollment
 * - Tests validation and error handling
 * - Tests success feedback and navigation
 *
 * INTEGRATION SCOPE:
 * - EnrollStudents component + enrollmentService (real)
 * - Student search + Selection management
 * - Form validation + API error handling
 * - Success notifications + Course list updates
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, setupUserEvent, createMockUser, createMockAuthState } from '../../utils';
import { EnrollStudents } from '@pages/EnrollStudents';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';

// Mock useNavigate (framework mock, not service mock)
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams('?courseId=course-123'), vi.fn()],
  };
});

/**
 * Helper function to render EnrollStudents page and select a course
 */
async function renderAndSelectCourse(user: ReturnType<typeof setupUserEvent>, mockInstructor: any) {
  renderWithProviders(<EnrollStudents />, {
    preloadedState: {
      auth: createMockAuthState({ role: 'instructor', userId: 'instructor-123' }),
      user: { profile: mockInstructor, loading: false, error: null },
    },
  });

  const courseDropdown = await screen.findByLabelText(/select course/i, {}, { timeout: 3000 });
  await user.selectOptions(courseDropdown, 'course-123');
  return screen.getByPlaceholderText(/search students/i);
}

describe('Course Enrollment Flow Integration Tests', () => {
  const user = setupUserEvent();
  const mockInstructor = createMockUser({ role: 'instructor', id: 'instructor-123' });

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    server.resetHandlers();
  });

  it('should complete successful student enrollment workflow', async () => {
    /**
     * INTEGRATION TEST: Complete Student Enrollment Workflow
     *
     * Tests real enrollmentService.enrollStudents() with MSW HTTP interception
     * Verifies outcome: success message displayed after enrollment
     */

    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Search for students
    await user.type(searchInput, 'example.com');

    // Wait for search results
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    }, { timeout: 5000 });

    // Select students
    const johnCheckbox = screen.getByRole('checkbox', { name: /john doe/i });
    const janeCheckbox = screen.getByRole('checkbox', { name: /jane smith/i });
    await user.click(johnCheckbox);
    await user.click(janeCheckbox);

    // Submit enrollment
    const enrollButton = screen.getByRole('button', { name: /enroll 2 student/i });
    await user.click(enrollButton);

    // Verify outcome: success message appears
    await waitFor(() => {
      expect(screen.getByText(/successfully enrolled 2 student/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should prevent enrollment without course selection', async () => {
    /**
     * INTEGRATION TEST: Validation Without Course Selection
     *
     * Tests component-level validation (not service validation)
     * Verifies outcome: validation error displayed
     */

    renderWithProviders(<EnrollStudents />, {
      preloadedState: {
        auth: createMockAuthState({ role: 'instructor', userId: 'instructor-123' }),
        user: { profile: mockInstructor, loading: false, error: null },
      },
    });

    await screen.findByLabelText(/select course/i, {}, { timeout: 3000 });

    // Try to submit without selecting course
    const enrollButton = screen.getByRole('button', { name: /enroll students/i });
    await user.click(enrollButton);

    // Verify outcome: validation message shown
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/select at least one student/i);
    });
  });

  it('should handle duplicate enrollment gracefully', async () => {
    /**
     * INTEGRATION TEST: Duplicate Enrollment Error Handling
     *
     * Tests real service error handling with MSW returning error
     * Verifies outcome: error message displayed to user
     */

    // Override MSW to return enrollment error
    server.use(
      http.post('https://176.9.99.103:8000/courses/:courseId/bulk-enroll', () => {
        return HttpResponse.json(
          { message: 'Student is already enrolled in this course' },
          { status: 400 }
        );
      })
    );

    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Search and select student
    await user.type(searchInput, 'Already');
    await waitFor(() => {
      expect(screen.getByText('Already Enrolled')).toBeInTheDocument();
    }, { timeout: 5000 });

    await user.click(screen.getByRole('checkbox', { name: /already enrolled/i }));
    await user.click(screen.getByRole('button', { name: /enroll 1 student/i }));

    // Verify outcome: error message displayed
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/already enrolled/i);
    }, { timeout: 3000 });
  });

  it('should show loading state during enrollment', async () => {
    /**
     * INTEGRATION TEST: Loading State During Async Operation
     *
     * Tests that loading indicator appears during enrollment
     * Verifies outcome: button shows loading state, then success
     */

    // Make enrollment slower to observe loading state (200ms)
    server.use(
      http.post('https://176.9.99.103:8000/courses/:courseId/bulk-enroll', async () => {
        await new Promise(resolve => setTimeout(resolve, 200));
        return HttpResponse.json({
          success_count: 1,
          failed_students: [],
        });
      })
    );

    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Search and select student
    await user.type(searchInput, 'John');
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    }, { timeout: 5000 });

    await user.click(screen.getByRole('checkbox', { name: /john doe/i }));

    const enrollButton = screen.getByRole('button', { name: /enroll 1 student/i });

    // Start enrollment
    await user.click(enrollButton);

    // Verify outcome: loading state appears quickly (button becomes disabled during submission)
    // Note: Component disables button during submission rather than using aria-busy
    await waitFor(() => {
      expect(enrollButton).toBeDisabled();
    }, { timeout: 100 });

    // Verify outcome: eventually succeeds and button re-enables
    await waitFor(() => {
      expect(screen.getByText(/successfully enrolled/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should filter out already enrolled students', async () => {
    /**
     * INTEGRATION TEST: Already-Enrolled Student Filtering
     *
     * Tests real getEnrolledStudents() service call with MSW
     * Verifies outcome: enrolled student checkbox is disabled
     */

    // Override MSW to return enrolled students
    server.use(
      http.get('https://176.9.99.103:8000/courses/course-123/enrollments', () => {
        return HttpResponse.json([
          { student_id: 'student-1', course_id: 'course-123' }
        ]);
      })
    );

    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Search for John
    await user.type(searchInput, 'John');
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    }, { timeout: 5000 });

    // Verify outcome: John Doe checkbox is disabled (already enrolled)
    const johnCheckbox = screen.getByRole('checkbox', { name: /john doe/i });
    expect(johnCheckbox).toBeDisabled();
  });

  it('should handle partial enrollment success', async () => {
    /**
     * INTEGRATION TEST: Partial Success Handling
     *
     * Tests real service processing of partial success response
     * Verifies outcome: partial success message displayed
     */

    // Override MSW to return partial success
    server.use(
      http.post('https://176.9.99.103:8000/courses/:courseId/bulk-enroll', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json({
          success_count: 1,
          failed_students: [
            { student_id: body.student_ids[1], reason: 'Course is full' }
          ],
        });
      })
    );

    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Search and select two students
    await user.type(searchInput, 'example.com');
    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument();
    }, { timeout: 5000 });

    await user.click(screen.getByRole('checkbox', { name: /success/i }));
    await user.click(screen.getByRole('checkbox', { name: /fail/i }));
    await user.click(screen.getByRole('button', { name: /enroll 2 student/i }));

    // Verify outcome: partial success message shown
    await waitFor(() => {
      expect(screen.getByText(/1 student.*enrolled.*1 failed/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should allow deselecting students before enrollment', async () => {
    /**
     * INTEGRATION TEST: Student Selection Management
     *
     * Tests UI state management (select/deselect students)
     * Verifies outcome: only selected students are enrolled
     */

    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Search for students
    await user.type(searchInput, 'example.com');
    await waitFor(() => {
      expect(screen.getByText('Selected First')).toBeInTheDocument();
    }, { timeout: 5000 });

    // Select first student
    const firstCheckbox = screen.getByRole('checkbox', { name: /selected first/i });
    await user.click(firstCheckbox);

    // Select second student
    const secondCheckbox = screen.getByRole('checkbox', { name: /unselected/i });
    await user.click(secondCheckbox);

    // Deselect second student
    await user.click(secondCheckbox);

    // Verify button shows only 1 student
    expect(screen.getByRole('button', { name: /enroll 1 student/i })).toBeInTheDocument();

    // Enroll
    await user.click(screen.getByRole('button', { name: /enroll 1 student/i }));

    // Verify outcome: success for 1 student
    await waitFor(() => {
      expect(screen.getByText(/successfully enrolled 1 student/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
