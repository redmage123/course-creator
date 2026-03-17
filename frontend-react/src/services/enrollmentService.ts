/**
 * Enrollment Service
 *
 * BUSINESS CONTEXT:
 * Handles student enrollment operations for B2B corporate training.
 * Trainers and org admins enroll students in training programs (bulk operations).
 * Students do NOT self-enroll - they are assigned courses by trainers.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses centralized apiClient with authentication
 * - Supports bulk enrollment operations for enterprise scale
 * - Handles enrollment status tracking and completion
 * - Integrates with course-management service (port 8001)
 */

import { apiClient } from './apiClient';

/**
 * Enrollment Status
 */
export type EnrollmentStatus = 'active' | 'completed' | 'dropped' | 'pending';

/**
 * Enrollment Interface
 */
export interface Enrollment {
  id: string;
  student_id: string;
  student_name?: string;
  student_email?: string;
  course_id: string;
  course_title?: string;
  enrollment_date: string;
  completion_date?: string;
  status: EnrollmentStatus;
  progress_percentage: number;
  last_accessed?: string;
}

/**
 * Single Enrollment Request
 */
export interface EnrollStudentRequest {
  student_id: string;
  course_id: string;
  enrollment_date?: string;
}

/**
 * Bulk Enrollment Request (for courses)
 */
export interface BulkEnrollStudentsRequest {
  course_id: string;
  student_ids: string[];
  enrollment_date?: string;
}

/**
 * Bulk Enrollment Request (for tracks)
 */
export interface BulkEnrollStudentsInTrackRequest {
  track_id: string;
  student_ids: string[];
  enrollment_date?: string;
}

/**
 * Bulk Enrollment Response
 */
export interface BulkEnrollmentResponse {
  success_count: number;
  failed_count: number;
  failed_students: Array<{
    student_id: string;
    reason: string;
  }>;
  message: string;
}

/**
 * Student Enrollment Summary
 */
export interface StudentEnrollmentSummary {
  student_id: string;
  student_name: string;
  total_enrollments: number;
  active_enrollments: number;
  completed_enrollments: number;
  average_progress: number;
}

/**
 * Enrollment Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized enrollment API logic
 * - Supports B2B bulk operations
 * - Type-safe interfaces for all operations
 * - Handles both single and bulk enrollments
 */
class EnrollmentService {
  private baseUrl = '/enrollments';

  /**
   * Enroll single student in training program
   */
  async enrollStudent(data: EnrollStudentRequest): Promise<Enrollment> {
    return await apiClient.post<Enrollment>(this.baseUrl, data);
  }

  /**
   * Bulk enroll students in training program
   * (Corporate training feature - enroll multiple students at once)
   */
  async bulkEnrollStudents(data: BulkEnrollStudentsRequest): Promise<BulkEnrollmentResponse> {
    return await apiClient.post<BulkEnrollmentResponse>(
      `/courses/${data.course_id}/bulk-enroll`,
      {
        student_ids: data.student_ids,
        enrollment_date: data.enrollment_date
      }
    );
  }

  /**
   * Bulk enroll students in training track
   * (Corporate training feature - enroll students in entire track)
   */
  async bulkEnrollStudentsInTrack(
    data: BulkEnrollStudentsInTrackRequest
  ): Promise<BulkEnrollmentResponse> {
    return await apiClient.post<BulkEnrollmentResponse>(
      `/tracks/${data.track_id}/bulk-enroll`,
      {
        student_ids: data.student_ids,
        enrollment_date: data.enrollment_date
      }
    );
  }

  /**
   * Get enrollments for a specific training program
   */
  async getCourseEnrollments(courseId: string): Promise<Enrollment[]> {
    return await apiClient.get<Enrollment[]>(`/courses/${courseId}/enrollments`);
  }

  /**
   * Get enrollments for a specific student
   */
  async getStudentEnrollments(studentId: string): Promise<Enrollment[]> {
    return await apiClient.get<Enrollment[]>(`/students/${studentId}/enrollments`);
  }

  /**
   * Get current user's enrollments (for student dashboard)
   */
  async getMyEnrollments(): Promise<Enrollment[]> {
    return await apiClient.get<Enrollment[]>(`${this.baseUrl}/me`);
  }

  /**
   * Update enrollment status
   */
  async updateEnrollmentStatus(enrollmentId: string, status: EnrollmentStatus): Promise<Enrollment> {
    return await apiClient.put<Enrollment>(`${this.baseUrl}/${enrollmentId}`, { status });
  }

  /**
   * Remove student from training program
   */
  async unenrollStudent(enrollmentId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${enrollmentId}`);
  }

  /**
   * Get enrollment summary for organization
   * (For org admin dashboard)
   */
  async getOrganizationEnrollmentSummary(organizationId: string): Promise<StudentEnrollmentSummary[]> {
    return await apiClient.get<StudentEnrollmentSummary[]>(
      `/organizations/${organizationId}/enrollments/summary`
    );
  }

  /**
   * Get enrollment summary for instructor
   * (For instructor dashboard)
   */
  async getInstructorEnrollmentSummary(instructorId: string): Promise<StudentEnrollmentSummary[]> {
    return await apiClient.get<StudentEnrollmentSummary[]>(
      `/instructors/${instructorId}/enrollments/summary`
    );
  }

  /**
   * Bulk upload students via CSV
   * (Enterprise feature for bulk operations)
   */
  async bulkEnrollFromCSV(courseId: string, csvFile: File): Promise<BulkEnrollmentResponse> {
    const formData = new FormData();
    formData.append('file', csvFile);
    formData.append('course_id', courseId);

    return await apiClient.post<BulkEnrollmentResponse>(
      '/enrollments/bulk-upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  }

  /**
   * Search for students (for enrollment UI)
   *
   * BUSINESS CONTEXT:
   * Instructors need to search and find students to enroll in courses.
   * Searches by name, email, or student ID.
   *
   * @param query - Search term (name, email, or ID)
   * @returns Array of matching students
   */
  async searchStudents(query: string): Promise<Array<{ id: string; name: string; email: string }>> {
    return await apiClient.get<Array<{ id: string; name: string; email: string }>>(
      `/students/search?q=${encodeURIComponent(query)}`
    );
  }

  /**
   * Get enrolled students for a course (for filtering)
   *
   * BUSINESS CONTEXT:
   * When enrolling students, need to know who is already enrolled
   * to prevent duplicates and show enrollment status.
   *
   * @param courseId - Course ID
   * @returns Array of enrolled student IDs
   */
  async getEnrolledStudents(courseId: string): Promise<string[]> {
    const enrollments = await apiClient.get<Enrollment[]>(`/courses/${courseId}/enrollments`);
    return enrollments.map(enrollment => enrollment.student_id);
  }

  /**
   * Enroll multiple students in a course (convenience method)
   *
   * BUSINESS CONTEXT:
   * Simplified method for enrollment UI that matches test expectations.
   * Wraps bulkEnrollStudents with a cleaner interface.
   *
   * @param params - Course ID and student IDs to enroll
   * @returns Enrollment result with success/failure details
   */
  async enrollStudents(params: { courseId: string; studentIds: string[] }): Promise<{
    enrolled: string[];
    courseId: string;
    enrolledCount: number;
    failed?: Array<{ id: string; reason: string }>;
  }> {
    const result = await this.bulkEnrollStudents({
      course_id: params.courseId,
      student_ids: params.studentIds,
    });

    return {
      enrolled: params.studentIds.filter((id, index) =>
        !result.failed_students.some(failed => failed.student_id === id)
      ),
      courseId: params.courseId,
      enrolledCount: result.success_count,
      failed: result.failed_students.map(f => ({ id: f.student_id, reason: f.reason })),
    };
  }
}

// Export singleton instance
export const enrollmentService = new EnrollmentService();
