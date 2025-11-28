/**
 * Course Management Service
 *
 * BUSINESS CONTEXT:
 * Manages course creation, updates, and lifecycle within the educational platform.
 * Supports both standalone course creation (individual instructors) and organizational
 * course creation (corporate training programs with track/project hierarchy).
 *
 * TECHNICAL IMPLEMENTATION:
 * - RESTful API calls to course-management service
 * - Type-safe TypeScript interfaces
 * - Error handling and validation
 * - Support for filtering and search
 */

import { apiClient } from './apiClient';

/**
 * Difficulty levels for courses
 */
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

/**
 * Duration units for course timing
 */
export type DurationUnit = 'hours' | 'days' | 'weeks' | 'months';

/**
 * Course entity
 */
export interface Course {
  id: string;
  title: string;
  description: string;
  instructor_id: string;
  category?: string;
  difficulty_level: DifficultyLevel;
  estimated_duration?: number;
  duration_unit: DurationUnit;
  price: number;
  tags: string[];
  is_published: boolean;
  organization_id?: string;
  track_id?: string;
  location_id?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Create course request
 *
 * SUPPORTS TWO MODES:
 * - Standalone: organization_id, track_id, location_id are null
 * - Organizational: Can provide organization_id, track_id, location_id for hierarchy
 */
export interface CreateCourseRequest {
  title: string;
  description: string;
  category?: string;
  difficulty_level?: DifficultyLevel;
  estimated_duration?: number;
  duration_unit?: DurationUnit;
  price?: number;
  tags?: string[];
  // Organizational context (optional)
  organization_id?: string;
  track_id?: string;
  location_id?: string;
}

/**
 * Update course request
 */
export interface UpdateCourseRequest {
  title?: string;
  description?: string;
  category?: string;
  difficulty_level?: DifficultyLevel;
  estimated_duration?: number;
  duration_unit?: DurationUnit;
  price?: number;
  tags?: string[];
}

/**
 * Course list response
 */
export interface CourseListResponse {
  courses: Course[];
  total: number;
  page?: number;
  limit?: number;
}

/**
 * Course filters
 */
export interface CourseFilters {
  organization_id?: string;
  track_id?: string;
  instructor_id?: string;
  difficulty_level?: DifficultyLevel;
  category?: string;
  published_only?: boolean;
}

/**
 * Course Service
 *
 * WHY THIS APPROACH:
 * - Centralized course management logic
 * - Type-safe API interactions
 * - Consistent error handling
 * - Easy to test and mock
 */
class CourseService {
  /**
   * Get all courses with optional filters
   *
   * @param filters - Optional filters for courses
   * @returns List of courses
   */
  async getCourses(filters?: CourseFilters): Promise<Course[]> {
    const params = new URLSearchParams();

    if (filters) {
      if (filters.organization_id) params.append('organization_id', filters.organization_id);
      if (filters.track_id) params.append('track_id', filters.track_id);
      if (filters.instructor_id) params.append('instructor_id', filters.instructor_id);
      if (filters.difficulty_level) params.append('difficulty_level', filters.difficulty_level);
      if (filters.category) params.append('category', filters.category);
      if (filters.published_only !== undefined) params.append('published_only', String(filters.published_only));
    }

    const queryString = params.toString();
    const url = `/courses${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<Course[]>(url);
    return response;
  }

  /**
   * Get course by ID
   *
   * @param courseId - Course ID
   * @returns Course details
   */
  async getCourseById(courseId: string): Promise<Course> {
    const response = await apiClient.get<Course>(`/courses/${courseId}`);
    return response;
  }

  /**
   * Create new course
   *
   * BUSINESS CONTEXT:
   * Creates a new course in the platform. Supports both standalone course creation
   * (for individual instructors) and organizational course creation (for corporate
   * training programs with organizational hierarchy).
   *
   * TECHNICAL IMPLEMENTATION:
   * - Calls POST /courses endpoint
   * - Instructor ID is automatically assigned from authentication token
   * - Course starts in unpublished/draft state
   * - Returns created course with generated ID
   *
   * @param courseData - Course creation data
   * @returns Created course
   */
  async createCourse(courseData: CreateCourseRequest): Promise<Course> {
    const response = await apiClient.post<Course>('/courses', courseData);
    return response;
  }

  /**
   * Update course
   *
   * @param courseId - Course ID
   * @param updates - Course updates
   * @returns Updated course
   */
  async updateCourse(courseId: string, updates: UpdateCourseRequest): Promise<Course> {
    const response = await apiClient.put<Course>(`/courses/${courseId}`, updates);
    return response;
  }

  /**
   * Delete course
   *
   * @param courseId - Course ID
   */
  async deleteCourse(courseId: string): Promise<void> {
    await apiClient.delete(`/courses/${courseId}`);
  }

  /**
   * Publish course
   *
   * @param courseId - Course ID
   * @returns Published course
   */
  async publishCourse(courseId: string): Promise<Course> {
    const response = await apiClient.post<Course>(`/courses/${courseId}/publish`, {});
    return response;
  }

  /**
   * Unpublish course
   *
   * @param courseId - Course ID
   * @returns Unpublished course
   */
  async unpublishCourse(courseId: string): Promise<Course> {
    const response = await apiClient.post<Course>(`/courses/${courseId}/unpublish`, {});
    return response;
  }

  /**
   * Get courses by track
   *
   * @param trackId - Track ID
   * @returns List of courses in the track
   */
  async getCoursesByTrack(trackId: string): Promise<Course[]> {
    return this.getCourses({ track_id: trackId });
  }

  /**
   * Get courses by organization
   *
   * @param organizationId - Organization ID
   * @param publishedOnly - Filter for published courses only
   * @returns List of courses in the organization
   */
  async getCoursesByOrganization(
    organizationId: string,
    publishedOnly: boolean = false
  ): Promise<Course[]> {
    return this.getCourses({ organization_id: organizationId, published_only: publishedOnly });
  }
}

// Export singleton instance
export const courseService = new CourseService();
