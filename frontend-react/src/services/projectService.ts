/**
 * Project Service
 *
 * BUSINESS CONTEXT:
 * Handles project management for organization training programs.
 * Projects are the top-level organizational unit containing tracks and enrollments.
 * Includes project notes functionality for extensive documentation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses centralized apiClient with authentication
 * - Handles project CRUD operations
 * - Manages project notes (get, update, upload, delete)
 * - Integrates with organization-management service (port 8005)
 */

import { apiClient } from './apiClient';

/**
 * Project Notes Interface
 *
 * BUSINESS CONTEXT:
 * Notes allow organization admins to add extensive documentation to projects.
 * Notes can be in markdown or HTML format for flexible content authoring.
 */
export interface ProjectNotes {
  project_id: string;
  project_name: string;
  notes: string | null;
  notes_content_type: 'markdown' | 'html';
  notes_updated_at: string | null;
  notes_updated_by: string | null;
  updated_by_name: string | null;
  updated_by_email: string | null;
}

/**
 * Update Notes Request
 */
export interface UpdateNotesRequest {
  notes: string;
  content_type: 'markdown' | 'html';
}

/**
 * Upload Notes Request
 */
export interface UploadNotesRequest {
  file_content: string;  // Base64 encoded
  file_name: string;
  content_type?: 'markdown' | 'html';
}

/**
 * Project Interface
 */
export interface Project {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string;
  target_roles: string[];
  duration_weeks?: number;
  max_participants?: number;
  current_participants: number;
  start_date?: string;
  end_date?: string;
  status: 'draft' | 'active' | 'completed' | 'archived';
  created_by: string;
  created_at: string;
  updated_at: string;
  notes?: string;
  notes_content_type?: string;
}

/**
 * Create Project Request
 */
export interface CreateProjectRequest {
  name: string;
  slug: string;
  description: string;
  target_roles?: string[];
  duration_weeks?: number;
  max_participants?: number;
  start_date?: string;
  end_date?: string;
}

/**
 * Project Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized project API logic
 * - Supports notes management with multiple formats
 * - Type-safe interfaces for all operations
 * - Handles file upload for notes
 */
class ProjectService {
  private baseUrl = '/organizations';

  /**
   * Get projects for an organization
   */
  async getProjects(organizationId: string): Promise<Project[]> {
    return await apiClient.get<Project[]>(
      `${this.baseUrl}/${organizationId}/projects`
    );
  }

  /**
   * Get project by ID
   */
  async getProject(projectId: string): Promise<Project> {
    return await apiClient.get<Project>(`/projects/${projectId}`);
  }

  /**
   * Create new project
   */
  async createProject(
    organizationId: string,
    data: CreateProjectRequest
  ): Promise<Project> {
    return await apiClient.post<Project>(
      `${this.baseUrl}/${organizationId}/projects`,
      data
    );
  }

  /**
   * Publish project
   */
  async publishProject(projectId: string): Promise<{ message: string; status: string }> {
    return await apiClient.post(`/projects/${projectId}/publish`);
  }

  // ==========================================================================
  // PROJECT NOTES OPERATIONS
  // ==========================================================================

  /**
   * Get project notes
   *
   * BUSINESS CONTEXT:
   * Retrieves the notes content along with metadata about who updated it and when.
   * Notes can be in markdown or HTML format for flexible rendering.
   */
  async getProjectNotes(
    organizationId: string,
    projectId: string
  ): Promise<ProjectNotes> {
    return await apiClient.get<ProjectNotes>(
      `${this.baseUrl}/${organizationId}/projects/${projectId}/notes`
    );
  }

  /**
   * Update project notes
   *
   * BUSINESS CONTEXT:
   * Allows organization admins to update project documentation.
   * Notes are stored with audit information for compliance tracking.
   *
   * @param organizationId - Organization UUID
   * @param projectId - Project UUID
   * @param data - Notes content and content type
   */
  async updateProjectNotes(
    organizationId: string,
    projectId: string,
    data: UpdateNotesRequest
  ): Promise<ProjectNotes> {
    return await apiClient.put<ProjectNotes>(
      `${this.baseUrl}/${organizationId}/projects/${projectId}/notes`,
      data
    );
  }

  /**
   * Upload project notes from file
   *
   * BUSINESS CONTEXT:
   * Allows uploading notes from external markdown or HTML files.
   * Content is base64 encoded for safe transmission.
   * Content type is auto-detected from file extension if not specified.
   *
   * @param organizationId - Organization UUID
   * @param projectId - Project UUID
   * @param file - File object to upload
   */
  async uploadProjectNotes(
    organizationId: string,
    projectId: string,
    file: File
  ): Promise<ProjectNotes> {
    // Read file content and encode to base64
    const fileContent = await this.readFileAsBase64(file);

    const data: UploadNotesRequest = {
      file_content: fileContent,
      file_name: file.name,
    };

    return await apiClient.post<ProjectNotes>(
      `${this.baseUrl}/${organizationId}/projects/${projectId}/notes/upload`,
      data
    );
  }

  /**
   * Delete project notes
   *
   * BUSINESS CONTEXT:
   * Clears all notes content from a project.
   * Deletion is tracked with timestamp and user ID for audit purposes.
   */
  async deleteProjectNotes(
    organizationId: string,
    projectId: string
  ): Promise<{ message: string; project_id: string }> {
    return await apiClient.delete(
      `${this.baseUrl}/${organizationId}/projects/${projectId}/notes`
    );
  }

  /**
   * Helper: Read file as base64 encoded string
   */
  private readFileAsBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Remove data URL prefix (e.g., "data:text/markdown;base64,")
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }
}

// Export singleton instance
export const projectService = new ProjectService();
