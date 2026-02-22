import { c as apiClient } from "./index-C0G9mbri.js";
class AnalyticsService {
  baseUrl = "/analytics";
  /**
   * Get student analytics (for student dashboard)
   */
  async getStudentAnalytics(studentId) {
    return await apiClient.get(`${this.baseUrl}/student/${studentId}`);
  }
  /**
   * Get current student's analytics (for logged-in student)
   */
  async getMyAnalytics() {
    return await apiClient.get(`${this.baseUrl}/student/me`);
  }
  /**
   * Get training program analytics (for instructor dashboard)
   */
  async getTrainingProgramAnalytics(courseId) {
    return await apiClient.get(`${this.baseUrl}/course/${courseId}`);
  }
  /**
   * Get instructor analytics (for instructor dashboard)
   */
  async getInstructorAnalytics(instructorId) {
    return await apiClient.get(`${this.baseUrl}/instructor/${instructorId}`);
  }
  /**
   * Get current instructor's analytics
   */
  async getMyInstructorAnalytics() {
    return await apiClient.get(`${this.baseUrl}/instructor/me`);
  }
  /**
   * Get organization analytics (for org admin dashboard)
   */
  async getOrganizationAnalytics(organizationId) {
    return await apiClient.get(`${this.baseUrl}/organization/${organizationId}`);
  }
  /**
   * Get dashboard stats for current user
   * (Returns role-appropriate stats based on user role)
   */
  async getDashboardStats() {
    return await apiClient.get(`${this.baseUrl}/dashboard/stats`);
  }
  /**
   * Get platform-wide analytics (for site admin dashboard)
   */
  async getPlatformAnalytics() {
    return await apiClient.get(`${this.baseUrl}/platform`);
  }
  /**
   * Get progress over time (for charts)
   */
  async getProgressTimeSeries(entityType, entityId, timeRange = "30d") {
    return await apiClient.get(
      `${this.baseUrl}/${entityType}/${entityId}/progress-timeline`,
      { params: { range: timeRange } }
    );
  }
  /**
   * Get enrollment trends over time
   */
  async getEnrollmentTrends(organizationId, timeRange = "30d") {
    const params = { range: timeRange, organization_id: organizationId };
    return await apiClient.get(
      `${this.baseUrl}/enrollments/trends`,
      { params }
    );
  }
  /**
   * Get completion trends over time
   */
  async getCompletionTrends(organizationId, timeRange = "30d") {
    const params = { range: timeRange, organization_id: organizationId };
    return await apiClient.get(
      `${this.baseUrl}/completions/trends`,
      { params }
    );
  }
  /**
   * Get compliance report (for org admin)
   */
  async getComplianceReport(organizationId) {
    return await apiClient.get(`${this.baseUrl}/organization/${organizationId}/compliance`);
  }
  /**
   * Export analytics report
   */
  async exportReport(reportType, entityId, format = "pdf") {
    return await apiClient.get(
      `${this.baseUrl}/${reportType}/${entityId}/export`,
      {
        params: { format },
        responseType: "blob"
      }
    );
  }
}
const analyticsService = new AnalyticsService();
export {
  analyticsService as a
};
//# sourceMappingURL=analyticsService-DsWqh8bd.js.map
