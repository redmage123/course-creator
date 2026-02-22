import { c as apiClient } from "./index-C0G9mbri.js";
function transformProgram(apiProgram) {
  const { is_published, ...rest } = apiProgram;
  return {
    ...rest,
    published: is_published
  };
}
function transformProgramList(apiResponse) {
  return {
    ...apiResponse,
    data: apiResponse.data.map(transformProgram)
  };
}
class TrainingProgramService {
  baseUrl = "/courses";
  // Using /courses as backend endpoint name
  /**
   * Get all training programs (with optional filters)
   */
  async getTrainingPrograms(filters) {
    const params = new URLSearchParams();
    if (filters) {
      if (filters.organization_id) params.append("organization_id", filters.organization_id);
      if (filters.project_id) params.append("project_id", filters.project_id);
      if (filters.track_id) params.append("track_id", filters.track_id);
      if (filters.instructor_id) params.append("instructor_id", filters.instructor_id);
      if (filters.difficulty_level) params.append("difficulty_level", filters.difficulty_level);
      if (filters.published !== void 0) params.append("published", String(filters.published));
      if (filters.published_only !== void 0) params.append("published_only", String(filters.published_only));
      if (filters.page) params.append("page", String(filters.page));
      if (filters.limit) params.append("limit", String(filters.limit));
    }
    const queryString = params.toString();
    const url = queryString ? `${this.baseUrl}?${queryString}` : this.baseUrl;
    const apiResponse = await apiClient.get(url);
    return transformProgramList(apiResponse);
  }
  /**
   * Get training program by ID
   */
  async getTrainingProgramById(id) {
    const apiResponse = await apiClient.get(`${this.baseUrl}/${id}`);
    return transformProgram(apiResponse);
  }
  /**
   * Create new training program
   */
  async createTrainingProgram(data) {
    const apiResponse = await apiClient.post(this.baseUrl, data);
    return transformProgram(apiResponse);
  }
  /**
   * Update existing training program
   */
  async updateTrainingProgram(id, data) {
    const apiResponse = await apiClient.put(`${this.baseUrl}/${id}`, data);
    return transformProgram(apiResponse);
  }
  /**
   * Publish training program (make available to students)
   */
  async publishTrainingProgram(id) {
    const apiResponse = await apiClient.post(`${this.baseUrl}/${id}/publish`);
    return transformProgram(apiResponse);
  }
  /**
   * Unpublish training program (remove from student access)
   */
  async unpublishTrainingProgram(id) {
    const apiResponse = await apiClient.post(`${this.baseUrl}/${id}/unpublish`);
    return transformProgram(apiResponse);
  }
  /**
   * Delete training program
   */
  async deleteTrainingProgram(id) {
    await apiClient.delete(`${this.baseUrl}/${id}`);
  }
  /**
   * Get student's assigned training programs
   * (B2B Model: Students only see courses assigned to them)
   */
  async getMyAssignedPrograms() {
    const apiResponse = await apiClient.get(`${this.baseUrl}/my-courses`);
    return transformProgramList(apiResponse);
  }
  /**
   * Get training programs by instructor
   *
   * Note: Instructors should see ALL their programs (published and unpublished),
   * so we pass published_only=false to the backend.
   */
  async getInstructorPrograms(instructorId) {
    return this.getTrainingPrograms({ instructor_id: instructorId, published_only: false });
  }
  /**
   * Get training programs by organization
   *
   * Note: Org admins should see ALL programs (published and unpublished),
   * so we pass published_only=false to the backend.
   */
  async getOrganizationPrograms(organizationId) {
    return this.getTrainingPrograms({ organization_id: organizationId, published_only: false });
  }
}
const trainingProgramService = new TrainingProgramService();
export {
  trainingProgramService as t
};
//# sourceMappingURL=trainingProgramService-B-up7yl_.js.map
