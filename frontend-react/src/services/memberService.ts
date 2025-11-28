/**
 * Member Management Service
 *
 * BUSINESS CONTEXT:
 * Manages organization members (instructors, students, org admins).
 * Organization admins can add, edit, and remove members from their organization.
 * Supports role-based filtering and member search.
 *
 * TECHNICAL IMPLEMENTATION:
 * - RESTful API calls to user-management and organization-management services
 * - Type-safe TypeScript interfaces
 * - Error handling and validation
 * - Support for pagination and filtering
 */

import { apiClient } from './apiClient';

/**
 * Member role types
 */
export type MemberRole = 'site_admin' | 'org_admin' | 'instructor' | 'student' | 'guest';

/**
 * Member entity
 */
export interface Member {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  role_name: MemberRole;
  organization_id?: string;
  organization_name?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

/**
 * Create member request
 */
export interface CreateMemberRequest {
  username: string;
  email: string;
  full_name?: string;
  password: string;
  role_name: MemberRole;
  organization_id: string;
}

/**
 * Update member request
 */
export interface UpdateMemberRequest {
  full_name?: string;
  role_name?: MemberRole;
  is_active?: boolean;
}

/**
 * Member list response
 */
export interface MemberListResponse {
  members: Member[];
  total: number;
  page: number;
  limit: number;
}

/**
 * Member Service
 *
 * WHY THIS APPROACH:
 * - Centralized member management logic
 * - Type-safe API interactions
 * - Consistent error handling
 * - Easy to test and mock
 */
class MemberService {
  /**
   * Get organization members
   *
   * @param organizationId - Organization ID
   * @param role - Optional role filter
   * @returns List of members
   */
  async getOrganizationMembers(
    organizationId: string,
    role?: MemberRole
  ): Promise<Member[]> {
    const params = new URLSearchParams();
    if (role) {
      params.append('role', role);
    }

    const queryString = params.toString();
    const url = `/organizations/${organizationId}/members${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<Member[]>(url);
    return response;
  }

  /**
   * Get member by ID
   *
   * @param memberId - Member/User ID
   * @returns Member details
   */
  async getMemberById(memberId: string): Promise<Member> {
    const response = await apiClient.get<Member>(`/users/${memberId}`);
    return response;
  }

  /**
   * Create new member
   *
   * BUSINESS CONTEXT:
   * Organization admins create members (instructors/students) within their organization.
   * This uses the organization-specific member creation endpoint to ensure proper
   * organization association and permission validation.
   *
   * TECHNICAL IMPLEMENTATION:
   * - Calls POST /organizations/{org_id}/members endpoint
   * - Organization-management service handles permission verification
   * - User-management service creates the user account
   * - Automatic organization_id association
   *
   * @param memberData - Member creation data
   * @returns Created member
   */
  async createMember(memberData: CreateMemberRequest): Promise<Member> {
    const { organization_id, ...requestData } = memberData;
    const response = await apiClient.post<Member>(
      `/organizations/${organization_id}/members`,
      requestData
    );
    return response;
  }

  /**
   * Update member
   *
   * @param memberId - Member ID
   * @param updates - Member updates
   * @returns Updated member
   */
  async updateMember(memberId: string, updates: UpdateMemberRequest): Promise<Member> {
    const response = await apiClient.patch<Member>(`/users/${memberId}`, updates);
    return response;
  }

  /**
   * Delete member (soft delete)
   *
   * @param memberId - Member ID
   */
  async deleteMember(memberId: string): Promise<void> {
    // Soft delete by setting is_active to false
    await this.updateMember(memberId, { is_active: false });
  }

  /**
   * Reactivate member
   *
   * @param memberId - Member ID
   */
  async reactivateMember(memberId: string): Promise<Member> {
    return await this.updateMember(memberId, { is_active: true });
  }

  /**
   * Search members
   *
   * @param query - Search query
   * @param organizationId - Optional organization filter
   * @returns Matching members
   */
  async searchMembers(query: string, organizationId?: string): Promise<Member[]> {
    const params = new URLSearchParams({
      q: query,
    });

    if (organizationId) {
      params.append('organization_id', organizationId);
    }

    const response = await apiClient.get<Member[]>(`/users/search?${params.toString()}`);
    return response;
  }

  /**
   * Get available roles
   *
   * @returns List of available roles
   */
  getAvailableRoles(): MemberRole[] {
    return ['org_admin', 'instructor', 'student'];
  }

  /**
   * Get role display name
   *
   * @param role - Role name
   * @returns Human-readable role name
   */
  getRoleDisplayName(role: MemberRole): string {
    const roleNames: Record<MemberRole, string> = {
      site_admin: 'Site Administrator',
      org_admin: 'Organization Admin',
      instructor: 'Instructor',
      student: 'Student',
      guest: 'Guest',
    };
    return roleNames[role] || role;
  }
}

// Export singleton instance
export const memberService = new MemberService();
