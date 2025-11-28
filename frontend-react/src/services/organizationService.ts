/**
 * Organization Service
 *
 * BUSINESS CONTEXT:
 * Handles organization management for B2B corporate training platform.
 * Manages corporate customers, their trainers (instructors), and organizational structure.
 * Supports multi-tenant architecture with organization-level isolation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses centralized apiClient with authentication
 * - Handles organization CRUD operations
 * - Manages trainer/member assignments
 * - Integrates with organization-management service (port 8005)
 */

import { apiClient } from './apiClient';
import type { UserRole } from '../store/slices/authSlice';

/**
 * Organization Interface
 */
export interface Organization {
  id: string;
  name: string;
  description?: string;
  industry?: string;
  size?: 'small' | 'medium' | 'large' | 'enterprise';
  website?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  logo_url?: string;
  created_at: string;
  updated_at: string;
  active: boolean;
  member_count?: number;
  trainer_count?: number;
  student_count?: number;
}

/**
 * Organization Member (Trainer or Admin)
 */
export interface OrganizationMember {
  id: string;
  user_id: string;
  organization_id: string;
  username: string;
  email: string;
  full_name: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  joined_date: string;
  last_active?: string;
  active: boolean;
}

/**
 * Create Organization Request
 */
export interface CreateOrganizationRequest {
  name: string;
  description?: string;
  industry?: string;
  size?: 'small' | 'medium' | 'large' | 'enterprise';
  website?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
}

/**
 * Update Organization Request
 */
export interface UpdateOrganizationRequest extends Partial<CreateOrganizationRequest> {}

/**
 * Add Member Request
 */
export interface AddMemberRequest {
  user_id: string;
  role: UserRole;
}

/**
 * Bulk Add Members Request
 */
export interface BulkAddMembersRequest {
  user_ids: string[];
  role: UserRole;
}

/**
 * Organization List Response
 */
export interface OrganizationListResponse {
  data: Organization[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Organization Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized organization API logic
 * - Supports multi-tenant B2B architecture
 * - Type-safe interfaces for all operations
 * - Handles trainer and member management
 */
class OrganizationService {
  private baseUrl = '/organizations';

  /**
   * Get all organizations (site admin only)
   */
  async getOrganizations(page: number = 1, limit: number = 20): Promise<OrganizationListResponse> {
    return await apiClient.get<OrganizationListResponse>(this.baseUrl, {
      params: { page, limit },
    });
  }

  /**
   * Get organization by ID
   */
  async getOrganizationById(id: string): Promise<Organization> {
    return await apiClient.get<Organization>(`${this.baseUrl}/${id}`);
  }

  /**
   * Get current user's organization
   */
  async getMyOrganization(): Promise<Organization> {
    return await apiClient.get<Organization>(`${this.baseUrl}/me`);
  }

  /**
   * Create new organization (site admin only)
   */
  async createOrganization(data: CreateOrganizationRequest): Promise<Organization> {
    return await apiClient.post<Organization>(this.baseUrl, data);
  }

  /**
   * Update organization
   */
  async updateOrganization(id: string, data: UpdateOrganizationRequest): Promise<Organization> {
    return await apiClient.put<Organization>(`${this.baseUrl}/${id}`, data);
  }

  /**
   * Delete organization (site admin only)
   */
  async deleteOrganization(id: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}`);
  }

  /**
   * Get organization members (trainers and admins)
   */
  async getOrganizationMembers(organizationId: string): Promise<OrganizationMember[]> {
    return await apiClient.get<OrganizationMember[]>(`${this.baseUrl}/${organizationId}/members`);
  }

  /**
   * Get organization trainers (instructors only)
   */
  async getOrganizationTrainers(organizationId: string): Promise<OrganizationMember[]> {
    const members = await this.getOrganizationMembers(organizationId);
    return members.filter(member => member.role === 'instructor');
  }

  /**
   * Add member to organization
   */
  async addMember(organizationId: string, data: AddMemberRequest): Promise<OrganizationMember> {
    return await apiClient.post<OrganizationMember>(
      `${this.baseUrl}/${organizationId}/members`,
      data
    );
  }

  /**
   * Bulk add members to organization
   */
  async bulkAddMembers(organizationId: string, data: BulkAddMembersRequest): Promise<{
    success_count: number;
    failed_count: number;
    message: string;
  }> {
    return await apiClient.post(
      `${this.baseUrl}/${organizationId}/members/bulk`,
      data
    );
  }

  /**
   * Remove member from organization
   */
  async removeMember(organizationId: string, userId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${organizationId}/members/${userId}`);
  }

  /**
   * Update member role
   */
  async updateMemberRole(
    organizationId: string,
    userId: string,
    role: UserRole
  ): Promise<OrganizationMember> {
    return await apiClient.put<OrganizationMember>(
      `${this.baseUrl}/${organizationId}/members/${userId}`,
      { role }
    );
  }

  /**
   * Get organization statistics
   */
  async getOrganizationStats(organizationId: string): Promise<{
    total_members: number;
    total_trainers: number;
    total_students: number;
    total_programs: number;
    total_enrollments: number;
    completion_rate: number;
  }> {
    return await apiClient.get(`${this.baseUrl}/${organizationId}/stats`);
  }

  /**
   * Search organizations (site admin only)
   */
  async searchOrganizations(query: string): Promise<Organization[]> {
    return await apiClient.get<Organization[]>(`${this.baseUrl}/search`, {
      params: { q: query },
    });
  }

  /**
   * Activate/deactivate organization
   */
  async toggleOrganizationStatus(id: string, active: boolean): Promise<Organization> {
    return await apiClient.put<Organization>(`${this.baseUrl}/${id}/status`, { active });
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
  async registerOrganization(formData: any): Promise<{
    data: any;
    access_token?: string;
    user?: any;
  }> {
    // Convert FormData to JSON object for the backend endpoint
    const data: any = {};
    if (formData instanceof FormData) {
      for (const [key, value] of formData.entries()) {
        // Skip File objects - backend JSON endpoint doesn't handle file uploads
        if (!(value instanceof File)) {
          data[key] = value;
        }
      }
    } else {
      Object.assign(data, formData);
    }

    // Add required admin_role field
    data.admin_role = 'organization_admin';

    // Backend expects JSON at POST /api/v1/organizations
    return await apiClient.post(`${this.baseUrl}`, data);
  }
}

// Export singleton instance
export const organizationService = new OrganizationService();
