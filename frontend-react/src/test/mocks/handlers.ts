/**
 * MSW (Mock Service Worker) Request Handlers
 *
 * BUSINESS CONTEXT:
 * Intercepts HTTP requests at the network level, allowing tests to use
 * real service implementations while controlling API responses.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses MSW to intercept fetch/axios requests
 * - Provides realistic API responses for testing
 * - Maintains service logic integrity (no service mocking)
 * - Covers all major API endpoints used by services
 */

import { http, HttpResponse } from 'msw';

// HTTPS production server URL
const API_BASE_URL = 'https://176.9.99.103:8000';

export const handlers = [
  // ============================================================================
  // AUTHENTICATION SERVICE
  // ============================================================================

  // Login
  http.post(`${API_BASE_URL}/auth/login`, async ({ request }) => {
    const body = await request.json() as any;
    // Accept either username or email as login identifier
    const identifier = body.username || body.email;
    const { password } = body;

    if (identifier === 'admin@example.com' && password === 'password123') {
      return HttpResponse.json({
        token: 'mock-jwt-token',
        refreshToken: 'mock-refresh-token',
        user: {
          id: 'user-123',
          username: 'admin@example.com',
          email: 'admin@example.com',
          name: 'Admin User',
          role: 'instructor',
        },
        expiresIn: 3600, // seconds
      });
    }

    return HttpResponse.json(
      { message: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  // Logout
  http.post(`${API_BASE_URL}/auth/logout`, () => {
    return HttpResponse.json({ success: true });
  }),

  // Register
  http.post(`${API_BASE_URL}/auth/register`, async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      token: 'mock-jwt-token',
      refreshToken: 'mock-refresh-token',
      user: {
        id: 'new-user-123',
        username: body.username,
        email: body.email,
        name: body.name,
        role: 'student',
      },
      expiresIn: 3600, // seconds
    });
  }),

  // Request password reset
  http.post(`${API_BASE_URL}/auth/password-reset/request`, () => {
    return HttpResponse.json({ success: true, message: 'Reset email sent' });
  }),

  // Confirm password reset
  http.post(`${API_BASE_URL}/auth/password-reset/confirm`, () => {
    return HttpResponse.json({ success: true, message: 'Password reset successful' });
  }),

  // ============================================================================
  // TRAINING PROGRAM SERVICE
  // ============================================================================

  // Get courses/training programs
  http.get(`${API_BASE_URL}/courses`, ({ request }) => {
    const url = new URL(request.url);
    const instructorId = url.searchParams.get('instructor_id');
    const published = url.searchParams.get('published');

    return HttpResponse.json({
      data: [
        {
          id: 'course-123',
          title: 'Test Course',
          description: 'A test course for demonstrations',
          instructor_id: instructorId,
          published: published === 'true',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    });
  }),

  // Get single course
  http.get(`${API_BASE_URL}/courses/:courseId`, ({ params }) => {
    return HttpResponse.json({
      id: params.courseId,
      title: 'Test Course',
      description: 'A test course',
      instructor_id: 'instructor-123',
      published: true,
    });
  }),

  // Create course
  http.post(`${API_BASE_URL}/courses`, async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      id: 'new-course-123',
      ...body,
      created_at: new Date().toISOString(),
    });
  }),

  // Update course
  http.put(`${API_BASE_URL}/courses/:courseId`, async ({ request, params }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      id: params.courseId,
      ...body,
      updated_at: new Date().toISOString(),
    });
  }),

  // Delete course
  http.delete(`${API_BASE_URL}/courses/:courseId`, () => {
    return HttpResponse.json({ success: true });
  }),

  // ============================================================================
  // ENROLLMENT SERVICE
  // ============================================================================

  // Enrollment Service - Search Students
  http.get(`${API_BASE_URL}/students/search`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('q');

    console.log('[MSW] Search students request:', { url: request.url, query });

    const allStudents = [
      { id: 'student-1', name: 'John Doe', email: 'john@example.com' },
      { id: 'student-2', name: 'Jane Smith', email: 'jane@example.com' },
      { id: 'student-3', name: 'Selected First', email: 'first@example.com' },
      { id: 'student-4', name: 'Unselected', email: 'second@example.com' },
      { id: 'student-5', name: 'Already Enrolled', email: 'enrolled@example.com' },
      { id: 'student-6', name: 'Success', email: 'success@example.com' },
      { id: 'student-7', name: 'Fail', email: 'fail@example.com' },
    ];

    const results = query
      ? allStudents.filter(s =>
          s.name.toLowerCase().includes(query.toLowerCase()) ||
          s.email.toLowerCase().includes(query.toLowerCase())
        )
      : [];

    console.log('[MSW] Returning search results:', results.length, 'students');
    return HttpResponse.json(results);
  }),

  // Enrollment Service - Get Enrolled Students
  http.get(`${API_BASE_URL}/courses/:courseId/enrollments`, ({ params }) => {
    return HttpResponse.json([]);
  }),

  // Enrollment Service - Bulk Enroll Students
  http.post(`${API_BASE_URL}/courses/:courseId/bulk-enroll`, async ({ request }) => {
    const body = await request.json() as any;
    const { student_ids } = body;

    console.log('[MSW] Bulk enroll request:', { student_ids });

    return HttpResponse.json({
      success_count: student_ids.length,
      failed_students: [],
    });
  }),

  // ============================================================================
  // ANALYTICS SERVICE
  // ============================================================================

  // Get course analytics
  http.get(`${API_BASE_URL}/analytics/courses/:courseId`, ({ params }) => {
    return HttpResponse.json({
      course_id: params.courseId,
      total_students: 25,
      completion_rate: 0.68,
      average_score: 82.5,
      engagement_metrics: {
        video_views: 450,
        quiz_attempts: 180,
        lab_sessions: 95,
      },
    });
  }),

  // Get student analytics
  http.get(`${API_BASE_URL}/analytics/students/:studentId`, ({ params }) => {
    return HttpResponse.json({
      student_id: params.studentId,
      courses_enrolled: 3,
      courses_completed: 1,
      average_score: 85.0,
      total_time_spent: 45.5, // hours
    });
  }),

  // ============================================================================
  // ORGANIZATION SERVICE
  // ============================================================================

  // Get organizations
  http.get(`${API_BASE_URL}/organizations`, () => {
    return HttpResponse.json({
      data: [
        {
          id: 'org-123',
          name: 'Test Organization',
          description: 'A test organization',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    });
  }),

  // Get single organization
  http.get(`${API_BASE_URL}/organizations/:orgId`, ({ params }) => {
    return HttpResponse.json({
      id: params.orgId,
      name: 'Test Organization',
      description: 'A test organization',
      created_at: '2024-01-01T00:00:00Z',
    });
  }),

  // Create organization
  http.post(`${API_BASE_URL}/organizations`, async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      id: 'new-org-123',
      ...body,
      created_at: new Date().toISOString(),
    });
  }),

  // Update organization
  http.put(`${API_BASE_URL}/organizations/:orgId`, async ({ request, params }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      id: params.orgId,
      ...body,
      updated_at: new Date().toISOString(),
    });
  }),
];
