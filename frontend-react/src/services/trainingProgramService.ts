/**
 * Training Program Service
 *
 * BUSINESS CONTEXT:
 * Handles all API interactions for corporate IT training programs.
 * In the B2B model, these are courses created and managed by trainers,
 * then assigned to students (not browsed/selected by students).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses centralized apiClient with authentication
 * - Provides TypeScript interfaces for type safety
 * - Handles pagination, filtering, and error responses
 * - Integrates with course-management service (port 8001)
 */

import { apiClient } from './apiClient';

/**
 * Training Program Interface
 * Represents a corporate IT training course
 */
export interface TrainingProgram {
  id: string;
  title: string;
  description: string;
  category?: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_duration?: number;
  duration_unit: 'hours' | 'days' | 'weeks' | 'months';
  price?: number;
  tags: string[];
  instructor_id: string;
  instructor_name?: string;
  organization_id?: string;
  project_id?: string;
  track_id?: string;
  location_id?: string;
  published: boolean;
  created_at: string;
  updated_at: string;
  enrolled_students?: number;
  completion_rate?: number;
}

/**
 * Training Program List Response
 */
export interface TrainingProgramListResponse {
  data: TrainingProgram[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Training Program Creation Request
 */
export interface CreateTrainingProgramRequest {
  title: string;
  description: string;
  category?: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_duration?: number;
  duration_unit: 'hours' | 'days' | 'weeks' | 'months';
  price?: number;
  tags?: string[];
  organization_id?: string;
  project_id?: string;
  track_id?: string;
  location_id?: string;
}

/**
 * Training Program Update Request
 */
export interface UpdateTrainingProgramRequest extends Partial<CreateTrainingProgramRequest> {}

/**
 * Training Program Filters
 */
export interface TrainingProgramFilters {
  organization_id?: string;
  project_id?: string;
  track_id?: string;
  instructor_id?: string;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  published?: boolean;
  /** Backend parameter for filtering published status (use this for API calls) */
  published_only?: boolean;
  page?: number;
  limit?: number;
}

/**
 * API Response interface (matches backend CourseResponseDTO)
 * Backend uses is_published, frontend uses published
 */
interface ApiTrainingProgram {
  id: string;
  title: string;
  description: string;
  category?: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_duration?: number;
  duration_unit: 'hours' | 'days' | 'weeks' | 'months';
  price?: number;
  tags: string[];
  instructor_id: string;
  instructor_name?: string;
  organization_id?: string;
  project_id?: string;
  track_id?: string;
  location_id?: string;
  is_published: boolean;  // Backend field name
  created_at: string;
  updated_at: string;
  enrolled_students?: number;
  completion_rate?: number;
}

interface ApiTrainingProgramListResponse {
  data: ApiTrainingProgram[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Transform API response to frontend interface
 * Maps is_published (backend) to published (frontend)
 */
function transformProgram(apiProgram: ApiTrainingProgram): TrainingProgram {
  const { is_published, ...rest } = apiProgram;
  return {
    ...rest,
    published: is_published,
  };
}

function transformProgramList(apiResponse: ApiTrainingProgramListResponse): TrainingProgramListResponse {
  return {
    ...apiResponse,
    data: apiResponse.data.map(transformProgram),
  };
}

/**
 * Training Program Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized training program API logic
 * - Type-safe interfaces for all operations
 * - Consistent error handling via apiClient
 * - Supports B2B workflows (bulk operations, filtering)
 * - Transforms API responses to match frontend interfaces
 */
class TrainingProgramService {
  private baseUrl = '/courses'; // Using /courses as backend endpoint name

  /**
   * Get all training programs (with optional filters)
   */
  async getTrainingPrograms(
    filters?: TrainingProgramFilters
  ): Promise<TrainingProgramListResponse> {
    const params = new URLSearchParams();

    if (filters) {
      if (filters.organization_id) params.append('organization_id', filters.organization_id);
      if (filters.project_id) params.append('project_id', filters.project_id);
      if (filters.track_id) params.append('track_id', filters.track_id);
      if (filters.instructor_id) params.append('instructor_id', filters.instructor_id);
      if (filters.difficulty_level) params.append('difficulty_level', filters.difficulty_level);
      if (filters.published !== undefined) params.append('published', String(filters.published));
      // Backend expects published_only parameter for filtering published status
      if (filters.published_only !== undefined) params.append('published_only', String(filters.published_only));
      if (filters.page) params.append('page', String(filters.page));
      if (filters.limit) params.append('limit', String(filters.limit));
    }

    const queryString = params.toString();
    const url = queryString ? `${this.baseUrl}?${queryString}` : this.baseUrl;

    const apiResponse = await apiClient.get<ApiTrainingProgramListResponse>(url);
    return transformProgramList(apiResponse);
  }

  /**
   * Get training program by ID
   */
  async getTrainingProgramById(id: string): Promise<TrainingProgram> {
    const apiResponse = await apiClient.get<ApiTrainingProgram>(`${this.baseUrl}/${id}`);
    return transformProgram(apiResponse);
  }

  /**
   * Create new training program
   */
  async createTrainingProgram(
    data: CreateTrainingProgramRequest
  ): Promise<TrainingProgram> {
    const apiResponse = await apiClient.post<ApiTrainingProgram>(this.baseUrl, data);
    return transformProgram(apiResponse);
  }

  /**
   * Update existing training program
   */
  async updateTrainingProgram(
    id: string,
    data: UpdateTrainingProgramRequest
  ): Promise<TrainingProgram> {
    const apiResponse = await apiClient.put<ApiTrainingProgram>(`${this.baseUrl}/${id}`, data);
    return transformProgram(apiResponse);
  }

  /**
   * Publish training program (make available to students)
   */
  async publishTrainingProgram(id: string): Promise<TrainingProgram> {
    const apiResponse = await apiClient.post<ApiTrainingProgram>(`${this.baseUrl}/${id}/publish`);
    return transformProgram(apiResponse);
  }

  /**
   * Unpublish training program (remove from student access)
   */
  async unpublishTrainingProgram(id: string): Promise<TrainingProgram> {
    const apiResponse = await apiClient.post<ApiTrainingProgram>(`${this.baseUrl}/${id}/unpublish`);
    return transformProgram(apiResponse);
  }

  /**
   * Delete training program
   */
  async deleteTrainingProgram(id: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}`);
  }

  /**
   * Get student's assigned training programs
   * (B2B Model: Students only see courses assigned to them)
   */
  async getMyAssignedPrograms(): Promise<TrainingProgramListResponse> {
    // This will be filtered by backend based on student's enrollments
    const apiResponse = await apiClient.get<ApiTrainingProgramListResponse>(`${this.baseUrl}/my-courses`);
    return transformProgramList(apiResponse);
  }

  /**
   * Get training programs by instructor
   *
   * Note: Instructors should see ALL their programs (published and unpublished),
   * so we pass published_only=false to the backend.
   */
  async getInstructorPrograms(instructorId: string): Promise<TrainingProgramListResponse> {
    return this.getTrainingPrograms({ instructor_id: instructorId, published_only: false });
  }

  /**
   * Get training programs by organization
   *
   * Note: Org admins should see ALL programs (published and unpublished),
   * so we pass published_only=false to the backend.
   */
  async getOrganizationPrograms(organizationId: string): Promise<TrainingProgramListResponse> {
    return this.getTrainingPrograms({ organization_id: organizationId, published_only: false });
  }
}

// Export singleton instance
export const trainingProgramService = new TrainingProgramService();
