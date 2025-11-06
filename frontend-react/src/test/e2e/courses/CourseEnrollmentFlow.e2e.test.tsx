/**
 * Course Enrollment Flow E2E Tests
 *
 * BUSINESS CONTEXT:
 * End-to-end tests for course enrollment workflows using real service implementations.
 * Tests the complete flow from component → service → API (intercepted by MSW).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses real enrollmentService and trainingProgramService code
 * - MSW intercepts HTTP requests at network level
 * - No service mocking - tests actual service logic
 * - Tests real user workflows with realistic API responses
 *
 * DIFFERENCE FROM INTEGRATION TESTS:
 * - Integration tests mock services (test component behavior)
 * - E2E tests use real services (test full stack behavior)
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, setupUserEvent, createMockUser, createMockAuthState } from '../../utils';
import { EnrollStudents } from '@pages/EnrollStudents';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';

const API_BASE_URL = '/api/v1';

/**
 * Helper function to render EnrollStudents page and select a course
 * This is required because the search input is disabled until a course is selected.
 */
async function renderAndSelectCourse(user: ReturnType<typeof setupUserEvent>, mockInstructor: any) {
  renderWithProviders(<EnrollStudents />, {
    preloadedState: {
      auth: createMockAuthState({ role: 'instructor', userId: 'instructor-123' }),
      user: { profile: mockInstructor, loading: false, error: null },
    },
  });

  // Wait for courses to load
  const courseDropdown = await screen.findByLabelText(/select course/i, {}, { timeout: 3000 });

  // Select the test course
  await user.selectOptions(courseDropdown, 'course-123');

  // Return the search input (now enabled)
  return screen.getByPlaceholderText(/search students/i);
}

describe('Course Enrollment Flow E2E Tests', () => {
  const user = setupUserEvent();
  const mockInstructor = createMockUser({ role: 'instructor', id: 'instructor-123' });

  beforeEach(() => {
    // Reset any custom handlers between tests
    server.resetHandlers();
  });

  it('should complete full enrollment workflow with real services', async () => {
    /**
     * E2E TEST: Complete enrollment using real service code
     *
     * Flow:
     * 1. Component loads → trainingProgramService.getTrainingPrograms() → MSW returns courses
     * 2. User types search → enrollmentService.searchStudents() → MSW returns students
     * 3. User selects students → UI updates
     * 4. User submits → enrollmentService.enrollStudents() → bulkEnrollStudents() → MSW processes
     * 5. Success message shown
     *
     * NOTE: EnrollStudents has 300ms debounce on search - must wait for it
     */

    // Render and select course to enable search
    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Search for "example.com" to get multiple students (John Doe, Jane Smith, etc.)
    // Note: Component has 300ms debounce delay
    await user.type(searchInput, 'example.com');

    // Wait for debounce + search results (MSW returns all students with @example.com email)
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    }, { timeout: 5000 }); // Increased timeout to account for debounce

    // Verify Jane Smith also appears
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();

    // Select both students
    const johnCheckbox = screen.getByRole('checkbox', { name: /john doe/i });
    const janeCheckbox = screen.getByRole('checkbox', { name: /jane smith/i });
    await user.click(johnCheckbox);
    await user.click(janeCheckbox);

    // Submit enrollment (real enrollmentService.enrollStudents → bulkEnrollStudents)
    const enrollButton = screen.getByRole('button', { name: /enroll 2 student/i });
    await user.click(enrollButton);

    // Verify success message (after real service processes MSW response)
    await waitFor(() => {
      expect(screen.getByText(/successfully enrolled 2 student/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should handle enrollment validation with real service logic', async () => {
    /**
     * E2E TEST: Validation using real service code
     */

    // Render and select course to enable search
    await renderAndSelectCourse(user, mockInstructor);

    // Try to enroll without selecting students
    const enrollButton = screen.getByRole('button', { name: /enroll students/i });
    await user.click(enrollButton);

    // Validation error from component (not service)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/select at least one student/i);
    });
  });

  it('should handle API errors through real service error handling', async () => {
    /**
     * E2E TEST: Error handling through real service code
     */

    // Override MSW handler to return error
    server.use(
      http.post('http://localhost:8000/courses/:courseId/bulk-enroll', () => {
        return HttpResponse.json(
          { message: 'Student is already enrolled in this course' },
          { status: 400 }
        );
      })
    );

    // Render and select course to enable search
    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Search and select student
    await user.type(searchInput, 'Already');
    await waitFor(() => {
      expect(screen.getByText('Already Enrolled')).toBeInTheDocument();
    }, { timeout: 5000 });

    await user.click(screen.getByRole('checkbox', { name: /already enrolled/i }));
    await user.click(screen.getByRole('button', { name: /enroll 1 student/i }));

    // Real service's error handling displays the error
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/already enrolled/i);
    }, { timeout: 3000 });
  });

  it('should handle partial enrollment success through real service logic', async () => {
    /**
     * E2E TEST: Partial success scenario with real service processing
     */

    // Override MSW to return partial success
    server.use(
      http.post('http://localhost:8000/courses/:courseId/bulk-enroll', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json({
          success_count: 1,
          failed_students: [
            { student_id: body.student_ids[1], reason: 'Course is full' }
          ],
        });
      })
    );

    // Render and select course to enable search
    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Select two students
    await user.type(searchInput, 'example.com');
    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument();
    }, { timeout: 5000 });

    await user.click(screen.getByRole('checkbox', { name: /success/i }));
    await user.click(screen.getByRole('checkbox', { name: /fail/i }));
    await user.click(screen.getByRole('button', { name: /enroll 2 student/i }));

    // Real service processes partial success response
    await waitFor(() => {
      expect(screen.getByText(/1 student.*enrolled.*1 failed/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should filter enrolled students using real service calls', async () => {
    /**
     * E2E TEST: Already-enrolled filtering with real getEnrolledStudents service call
     */

    // Override MSW to return enrolled students
    server.use(
      http.get('http://localhost:8000/courses/course-123/enrollments', () => {
        return HttpResponse.json([
          { student_id: 'student-1', course_id: 'course-123' }
        ]);
      })
    );

    // Render and select course to enable search
    const searchInput = await renderAndSelectCourse(user, mockInstructor);

    // Real service calls getEnrolledStudents when course is selected
    // Search for John to find John Doe
    await user.type(searchInput, 'John');
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    }, { timeout: 5000 });

    // John Doe checkbox should be disabled (already enrolled)
    const johnCheckbox = screen.getByRole('checkbox', { name: /john doe/i });
    expect(johnCheckbox).toBeDisabled();
  });
});
