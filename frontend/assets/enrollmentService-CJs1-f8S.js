import { c as apiClient } from "./index-C0G9mbri.js";
class EnrollmentService {
  baseUrl = "/enrollments";
  /**
   * Enroll single student in training program
   */
  async enrollStudent(data) {
    return await apiClient.post(this.baseUrl, data);
  }
  /**
   * Bulk enroll students in training program
   * (Corporate training feature - enroll multiple students at once)
   */
  async bulkEnrollStudents(data) {
    return await apiClient.post(
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
  async bulkEnrollStudentsInTrack(data) {
    return await apiClient.post(
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
  async getCourseEnrollments(courseId) {
    return await apiClient.get(`/courses/${courseId}/enrollments`);
  }
  /**
   * Get enrollments for a specific student
   */
  async getStudentEnrollments(studentId) {
    return await apiClient.get(`/students/${studentId}/enrollments`);
  }
  /**
   * Get current user's enrollments (for student dashboard)
   */
  async getMyEnrollments() {
    return await apiClient.get(`${this.baseUrl}/me`);
  }
  /**
   * Update enrollment status
   */
  async updateEnrollmentStatus(enrollmentId, status) {
    return await apiClient.put(`${this.baseUrl}/${enrollmentId}`, { status });
  }
  /**
   * Remove student from training program
   */
  async unenrollStudent(enrollmentId) {
    await apiClient.delete(`${this.baseUrl}/${enrollmentId}`);
  }
  /**
   * Get enrollment summary for organization
   * (For org admin dashboard)
   */
  async getOrganizationEnrollmentSummary(organizationId) {
    return await apiClient.get(
      `/organizations/${organizationId}/enrollments/summary`
    );
  }
  /**
   * Get enrollment summary for instructor
   * (For instructor dashboard)
   */
  async getInstructorEnrollmentSummary(instructorId) {
    return await apiClient.get(
      `/instructors/${instructorId}/enrollments/summary`
    );
  }
  /**
   * Bulk upload students via CSV
   * (Enterprise feature for bulk operations)
   */
  async bulkEnrollFromCSV(courseId, csvFile) {
    const formData = new FormData();
    formData.append("file", csvFile);
    formData.append("course_id", courseId);
    return await apiClient.post(
      "/enrollments/bulk-upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data"
        }
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
  async searchStudents(query) {
    return await apiClient.get(
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
  async getEnrolledStudents(courseId) {
    const enrollments = await apiClient.get(`/courses/${courseId}/enrollments`);
    return enrollments.map((enrollment) => enrollment.student_id);
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
  async enrollStudents(params) {
    const result = await this.bulkEnrollStudents({
      course_id: params.courseId,
      student_ids: params.studentIds
    });
    return {
      enrolled: params.studentIds.filter(
        (id, index) => !result.failed_students.some((failed) => failed.student_id === id)
      ),
      courseId: params.courseId,
      enrolledCount: result.success_count,
      failed: result.failed_students.map((f) => ({ id: f.student_id, reason: f.reason }))
    };
  }
}
const enrollmentService = new EnrollmentService();
export {
  enrollmentService as e
};
//# sourceMappingURL=enrollmentService-CJs1-f8S.js.map
