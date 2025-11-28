/**
 * Track Service
 *
 * BUSINESS CONTEXT:
 * Manages learning tracks (learning paths) within organizations.
 * Tracks are collections of courses that form a structured learning journey.
 * Organization admins create and manage tracks for their teams.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses centralized apiClient with authentication
 * - Handles track CRUD operations
 * - Manages track enrollments and analytics
 * - Integrates with organization-management service (port 8005)
 */

import { apiClient } from './apiClient';

/**
 * Track Interface
 */
export interface Track {
  id: string;
  name: string;
  description?: string;
  project_id: string;
  organization_id: string;
  target_audience: string[];
  prerequisites: string[];
  learning_objectives: string[];
  duration_weeks?: number;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  max_students?: number;
  status: 'draft' | 'active' | 'archived';
  enrollment_count: number;
  instructor_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * Create Track Request
 */
export interface CreateTrackRequest {
  name: string;
  description?: string;
  project_id: string;
  target_audience?: string[];
  prerequisites?: string[];
  learning_objectives?: string[];
  duration_weeks?: number;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  max_students?: number;
}

/**
 * Update Track Request
 */
export interface UpdateTrackRequest {
  name?: string;
  description?: string;
  target_audience?: string[];
  prerequisites?: string[];
  learning_objectives?: string[];
  duration_weeks?: number;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  max_students?: number;
  status?: 'draft' | 'active' | 'archived';
}

/**
 * Track List Response (for pagination support)
 */
export interface TrackListResponse {
  data: Track[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Track Enrollment Request
 */
export interface TrackEnrollmentRequest {
  student_emails: string[];
  auto_approve?: boolean;
}

/**
 * Track Enrollment Response
 */
export interface TrackEnrollmentResponse {
  track_id: string;
  successful_enrollments: string[];
  failed_enrollments: Array<{ email: string; reason: string }>;
  total_enrolled: number;
}

/**
 * Track Analytics
 */
export interface TrackAnalytics {
  track_id: string;
  track_name: string;
  enrollment_count: number;
  completion_rate: number;
  average_progress: number;
  active_students: number;
  completed_students: number;
  generated_at: string;
}

/**
 * Track Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized track API logic
 * - Type-safe interfaces for all operations
 * - Supports organization-level track management
 * - Handles course sequencing and learning paths
 */
class TrackService {
  private baseUrl = '/tracks/';

  /**
   * Get all tracks for an organization
   *
   * BUSINESS LOGIC:
   * Organization admins view all tracks in their organization.
   * Supports filtering by project, status, and difficulty.
   *
   * @param organizationId - Organization ID
   * @param filters - Optional filters (project_id, status, difficulty_level)
   * @returns Array of tracks
   */
  async getOrganizationTracks(
    organizationId: string,
    filters?: {
      project_id?: string;
      status?: string;
      difficulty_level?: string;
    }
  ): Promise<Track[]> {
    const params: Record<string, string> = {
      organization_id: organizationId,
    };

    if (filters?.project_id) params.project_id = filters.project_id;
    if (filters?.status) params.track_status = filters.status;
    if (filters?.difficulty_level) params.difficulty_level = filters.difficulty_level;

    return await apiClient.get<Track[]>(this.baseUrl, { params });
  }

  /**
   * Get tracks by project
   *
   * BUSINESS LOGIC:
   * View all tracks within a specific project.
   * Projects can have multiple tracks (e.g., "Web Dev Fundamentals", "Advanced Web Dev").
   *
   * @param projectId - Project ID
   * @param status - Optional status filter
   * @returns Array of tracks
   */
  async getProjectTracks(projectId: string, status?: string): Promise<Track[]> {
    const params: Record<string, string> = {
      project_id: projectId,
    };

    if (status) params.track_status = status;

    return await apiClient.get<Track[]>(this.baseUrl, { params });
  }

  /**
   * Get track by ID
   *
   * @param trackId - Track ID
   * @returns Track details with enrollment and instructor counts
   */
  async getTrackById(trackId: string): Promise<Track> {
    return await apiClient.get<Track>(`${this.baseUrl}/${trackId}`);
  }

  /**
   * Create new track
   *
   * BUSINESS LOGIC:
   * Organization admins create learning tracks to structure course content.
   * Each track belongs to a project and can contain multiple courses.
   *
   * @param data - Track creation data
   * @returns Created track
   */
  async createTrack(data: CreateTrackRequest): Promise<Track> {
    return await apiClient.post<Track>(this.baseUrl, data);
  }

  /**
   * Update existing track
   *
   * BUSINESS LOGIC:
   * Organization admins can modify track details, learning objectives,
   * difficulty level, and capacity limits.
   *
   * @param trackId - Track ID
   * @param data - Updated track data
   * @returns Updated track
   */
  async updateTrack(trackId: string, data: UpdateTrackRequest): Promise<Track> {
    return await apiClient.put<Track>(`${this.baseUrl}/${trackId}`, data);
  }

  /**
   * Delete track
   *
   * BUSINESS LOGIC:
   * Soft delete for tracks with active enrollments.
   * Hard delete only allowed for tracks with no enrollments.
   *
   * @param trackId - Track ID
   */
  async deleteTrack(trackId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${trackId}`);
  }

  /**
   * Publish track (make available for enrollment)
   *
   * BUSINESS LOGIC:
   * Publishing a track makes it visible to students for enrollment.
   * Requires track to have at least one course assigned.
   *
   * @param trackId - Track ID
   * @returns Published track with updated status
   */
  async publishTrack(trackId: string): Promise<{ message: string; track_id: string; status: string }> {
    return await apiClient.post(`${this.baseUrl}/${trackId}/publish`);
  }

  /**
   * Unpublish track (make unavailable for enrollment)
   *
   * BUSINESS LOGIC:
   * Unpublishing a track hides it from new enrollments.
   * Existing enrollments remain active.
   *
   * @param trackId - Track ID
   * @returns Unpublished track with updated status
   */
  async unpublishTrack(trackId: string): Promise<{ message: string; track_id: string; status: string }> {
    return await apiClient.post(`${this.baseUrl}/${trackId}/unpublish`);
  }

  /**
   * Bulk enroll students in track
   *
   * BUSINESS LOGIC:
   * Organization admins can enroll multiple students at once.
   * Students are enrolled in all courses within the track.
   *
   * @param trackId - Track ID
   * @param data - Enrollment request with student emails
   * @returns Enrollment results (successful and failed)
   */
  async bulkEnrollStudents(
    trackId: string,
    data: TrackEnrollmentRequest
  ): Promise<TrackEnrollmentResponse> {
    return await apiClient.post<TrackEnrollmentResponse>(
      `${this.baseUrl}/${trackId}/enroll`,
      data
    );
  }

  /**
   * Get track enrollments
   *
   * BUSINESS LOGIC:
   * View all student enrollments for a track.
   * Supports filtering by enrollment status.
   *
   * @param trackId - Track ID
   * @param enrollmentStatus - Optional status filter
   * @returns Enrollment list with student details
   */
  async getTrackEnrollments(
    trackId: string,
    enrollmentStatus?: string
  ): Promise<{
    track_id: string;
    enrollments: any[];
    total_count: number;
  }> {
    const params: Record<string, string> = {};
    if (enrollmentStatus) params.enrollment_status = enrollmentStatus;

    return await apiClient.get(`${this.baseUrl}/${trackId}/enrollments`, { params });
  }

  /**
   * Get track analytics
   *
   * BUSINESS LOGIC:
   * Comprehensive analytics for track performance:
   * - Enrollment trends
   * - Completion rates
   * - Student progress
   * - Engagement metrics
   *
   * @param trackId - Track ID
   * @returns Track analytics data
   */
  async getTrackAnalytics(trackId: string): Promise<TrackAnalytics> {
    const response = await apiClient.get<{
      track_id: string;
      track_name: string;
      analytics: TrackAnalytics;
      generated_at: string;
    }>(`${this.baseUrl}/${trackId}/analytics`);

    return response.analytics;
  }

  /**
   * Duplicate track
   *
   * BUSINESS LOGIC:
   * Create a copy of an existing track with new name.
   * Useful for creating similar tracks or versioning.
   *
   * @param trackId - Track ID to duplicate
   * @param newName - Optional new name for duplicated track
   * @returns Duplicated track details
   */
  async duplicateTrack(
    trackId: string,
    newName?: string
  ): Promise<{
    message: string;
    original_track_id: string;
    new_track_id: string;
    new_track_name: string;
  }> {
    const body = newName ? { new_name: newName } : {};
    return await apiClient.post(`${this.baseUrl}/${trackId}/duplicate`, body);
  }

  /**
   * Get track locations (for instructor assignment)
   *
   * BUSINESS LOGIC:
   * When a track belongs to a project with multiple geographic locations,
   * instructors can be assigned to specific locations.
   * This returns available locations for the track's parent project.
   *
   * @param trackId - Track ID
   * @returns Array of available locations
   */
  async getTrackLocations(trackId: string): Promise<any[]> {
    return await apiClient.get<any[]>(`${this.baseUrl}/${trackId}/locations`);
  }

  /**
   * Search tracks by name
   *
   * BUSINESS LOGIC:
   * Search tracks within organization by name or description.
   * Client-side filtering is preferred for better UX.
   *
   * @param organizationId - Organization ID
   * @param query - Search query
   * @returns Matching tracks
   */
  async searchTracks(organizationId: string, query: string): Promise<Track[]> {
    const allTracks = await this.getOrganizationTracks(organizationId);

    const lowerQuery = query.toLowerCase();
    return allTracks.filter(
      (track) =>
        track.name.toLowerCase().includes(lowerQuery) ||
        track.description?.toLowerCase().includes(lowerQuery)
    );
  }
}

// Export singleton instance
export const trackService = new TrackService();
