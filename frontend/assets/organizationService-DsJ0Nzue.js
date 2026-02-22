import { c as apiClient } from "./index-C0G9mbri.js";
class OrganizationService {
  baseUrl = "/organizations";
  /**
   * Get all organizations (site admin only)
   */
  async getOrganizations(page = 1, limit = 20) {
    return await apiClient.get(this.baseUrl, {
      params: { page, limit }
    });
  }
  /**
   * Get organization by ID
   */
  async getOrganizationById(id) {
    return await apiClient.get(`${this.baseUrl}/${id}`);
  }
  /**
   * Get current user's organization
   */
  async getMyOrganization() {
    return await apiClient.get(`${this.baseUrl}/me`);
  }
  /**
   * Create new organization (site admin only)
   */
  async createOrganization(data) {
    return await apiClient.post(this.baseUrl, data);
  }
  /**
   * Update organization
   */
  async updateOrganization(id, data) {
    return await apiClient.put(`${this.baseUrl}/${id}`, data);
  }
  /**
   * Delete organization (site admin only)
   */
  async deleteOrganization(id) {
    await apiClient.delete(`${this.baseUrl}/${id}`);
  }
  /**
   * Get organization members (trainers and admins)
   */
  async getOrganizationMembers(organizationId) {
    return await apiClient.get(`${this.baseUrl}/${organizationId}/members`);
  }
  /**
   * Get organization trainers (instructors only)
   */
  async getOrganizationTrainers(organizationId) {
    const members = await this.getOrganizationMembers(organizationId);
    return members.filter((member) => member.role === "instructor");
  }
  /**
   * Add member to organization
   */
  async addMember(organizationId, data) {
    return await apiClient.post(
      `${this.baseUrl}/${organizationId}/members`,
      data
    );
  }
  /**
   * Bulk add members to organization
   */
  async bulkAddMembers(organizationId, data) {
    return await apiClient.post(
      `${this.baseUrl}/${organizationId}/members/bulk`,
      data
    );
  }
  /**
   * Remove member from organization
   */
  async removeMember(organizationId, userId) {
    await apiClient.delete(`${this.baseUrl}/${organizationId}/members/${userId}`);
  }
  /**
   * Update member role
   */
  async updateMemberRole(organizationId, userId, role) {
    return await apiClient.put(
      `${this.baseUrl}/${organizationId}/members/${userId}`,
      { role }
    );
  }
  /**
   * Get organization statistics
   */
  async getOrganizationStats(organizationId) {
    return await apiClient.get(`${this.baseUrl}/${organizationId}/stats`);
  }
  /**
   * Search organizations (site admin only)
   */
  async searchOrganizations(query) {
    return await apiClient.get(`${this.baseUrl}/search`, {
      params: { q: query }
    });
  }
  /**
   * Activate/deactivate organization
   */
  async toggleOrganizationStatus(id, active) {
    return await apiClient.put(`${this.baseUrl}/${id}/status`, { active });
  }
  /**
   * Register new organization (public self-service registration)
   *
   * BUSINESS CONTEXT:
   * Public registration endpoint for organizations to sign up.
   * Creates organization + admin account in single transaction.
   * Returns JWT token for auto-login after successful registration.
   *
   * @param formData - FormData object containing organization and admin details
   * @returns Organization data with access_token and user info
   */
  async registerOrganization(formData) {
    const data = {};
    if (formData instanceof FormData) {
      for (const [key, value] of formData.entries()) {
        if (!(value instanceof File)) {
          data[key] = value;
        }
      }
    } else {
      Object.assign(data, formData);
    }
    data.admin_role = "organization_admin";
    return await apiClient.post(`${this.baseUrl}`, data);
  }
}
const organizationService = new OrganizationService();
export {
  organizationService as o
};
//# sourceMappingURL=organizationService-DsJ0Nzue.js.map
