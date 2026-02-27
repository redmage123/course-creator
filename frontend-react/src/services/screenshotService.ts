/**
 * Screenshot Course Generation Service
 *
 * BUSINESS CONTEXT:
 * Enables instructors to create courses from screenshots of existing content.
 * Users can upload screenshots (slides, diagrams, documentation) and have AI
 * automatically extract content and generate a complete course structure.
 *
 * TECHNICAL IMPLEMENTATION:
 * - File upload to course-generator service
 * - Progress tracking for long-running analysis
 * - Integration with multi-provider LLM system
 * - Support for various image formats (PNG, JPG, WEBP)
 *
 * MULTI-PROVIDER SUPPORT:
 * - OpenAI GPT-5.2 Vision
 * - Anthropic Claude Vision
 * - Deepseek-VL
 * - Qwen-VL
 * - Ollama (LLaVA)
 * - Meta Llama 3.2 Vision
 * - Google Gemini
 * - Mistral
 */

import axios from 'axios';
import { tokenManager } from './tokenManager';

// Base URL for course-generator service
const COURSE_GENERATOR_URL = import.meta.env.VITE_COURSE_GENERATOR_URL || '/api/course-generator';

/**
 * Screenshot upload response
 */
export interface ScreenshotUploadResponse {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  status: string;
  organization_id: string;
  uploaded_by: string;
  created_at: string;
}

/**
 * Screenshot analysis result
 */
export interface ScreenshotAnalysisResult {
  screenshot_id: string;
  extracted_text: string;
  content_type: string;
  subject_area: string;
  difficulty_level: string;
  confidence_score: number;
  course_structure: CourseStructure;
  llm_provider: string;
  analyzed_at: string;
}

/**
 * Course structure generated from screenshot
 */
export interface CourseStructure {
  title: string;
  description: string;
  modules: ModuleStructure[];
  learning_objectives: string[];
  prerequisites: string[];
  estimated_duration: string;
}

/**
 * Module structure within a course
 */
export interface ModuleStructure {
  title: string;
  description: string;
  lessons: LessonStructure[];
  duration_minutes: number;
}

/**
 * Lesson structure within a module
 */
export interface LessonStructure {
  title: string;
  content_summary: string;
  learning_objectives: string[];
}

/**
 * Screenshot processing status
 */
export interface ScreenshotStatus {
  id: string;
  status: 'pending' | 'processing' | 'analyzed' | 'course_generated' | 'failed';
  progress_percent: number;
  current_step: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Course generation request
 */
export interface GenerateCourseFromScreenshotRequest {
  screenshot_id: string;
  organization_id?: string;
  track_id?: string;
  create_course: boolean;
  llm_provider?: string;
}

/**
 * Course generation response
 */
export interface GenerateCourseResponse {
  screenshot_id: string;
  course_id?: string;
  course_structure: CourseStructure;
  status: string;
  message: string;
}

/**
 * Similar screenshot search result
 */
export interface SimilarScreenshot {
  screenshot_id: string;
  course_id?: string;
  course_title?: string;
  content_type: string;
  subject_area: string;
  similarity_score: number;
  extracted_text_preview: string;
}

/**
 * LLM provider configuration
 */
export interface LLMProviderConfig {
  id: string;
  organization_id: string;
  provider_name: string;
  model_name: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
}

/**
 * Available LLM providers
 */
export interface AvailableLLMProvider {
  name: string;
  display_name: string;
  models: string[];
  supports_vision: boolean;
  requires_api_key: boolean;
}

/**
 * Screenshot Service
 *
 * BUSINESS VALUE:
 * - Reduces course creation time from hours to minutes
 * - Leverages existing content for rapid course development
 * - Supports multi-provider LLM flexibility
 */
class ScreenshotService {
  /**
   * Upload a screenshot for analysis
   *
   * @param file - Image file to upload
   * @param organizationId - Organization ID for the upload
   * @returns Upload response with screenshot ID
   */
  async uploadScreenshot(
    file: File,
    organizationId: string
  ): Promise<ScreenshotUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization_id', organizationId);

    const response = await axios.post<ScreenshotUploadResponse>(
      `${COURSE_GENERATOR_URL}/api/v1/screenshots/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data;
  }

  /**
   * Upload multiple screenshots as a batch
   *
   * @param files - Array of image files
   * @param organizationId - Organization ID
   * @returns Batch upload response with all screenshot IDs
   */
  async uploadScreenshotBatch(
    files: File[],
    organizationId: string
  ): Promise<{ batch_id: string; screenshots: ScreenshotUploadResponse[] }> {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`files`, file);
    });
    formData.append('organization_id', organizationId);

    const response = await axios.post(
      `${COURSE_GENERATOR_URL}/api/v1/screenshots/upload/batch`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data;
  }

  /**
   * Get screenshot processing status
   *
   * @param screenshotId - Screenshot ID to check
   * @returns Current processing status
   */
  async getScreenshotStatus(screenshotId: string): Promise<ScreenshotStatus> {
    const response = await axios.get<ScreenshotStatus>(
      `${COURSE_GENERATOR_URL}/api/v1/screenshots/${screenshotId}/status`,
      {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data;
  }

  /**
   * Get screenshot analysis result
   *
   * @param screenshotId - Screenshot ID
   * @returns Analysis result with extracted content and course structure
   */
  async getAnalysisResult(screenshotId: string): Promise<ScreenshotAnalysisResult> {
    const response = await axios.get<ScreenshotAnalysisResult>(
      `${COURSE_GENERATOR_URL}/api/v1/screenshots/${screenshotId}/result`,
      {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data;
  }

  /**
   * Trigger screenshot analysis manually
   *
   * @param screenshotId - Screenshot ID to analyze
   * @param llmProvider - Optional specific LLM provider to use
   * @returns Analysis status
   */
  async analyzeScreenshot(
    screenshotId: string,
    llmProvider?: string
  ): Promise<{ status: string; message: string }> {
    const response = await axios.post(
      `${COURSE_GENERATOR_URL}/api/v1/screenshots/${screenshotId}/analyze`,
      { llm_provider: llmProvider },
      {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data;
  }

  /**
   * Generate course from screenshot analysis
   *
   * BUSINESS CONTEXT:
   * Takes analyzed screenshot content and creates a full course in the system.
   * Optionally assigns to a track for organizational courses.
   *
   * @param request - Course generation parameters
   * @returns Generated course details
   */
  async generateCourseFromScreenshot(
    request: GenerateCourseFromScreenshotRequest
  ): Promise<GenerateCourseResponse> {
    const response = await axios.post<GenerateCourseResponse>(
      `${COURSE_GENERATOR_URL}/api/v1/screenshots/${request.screenshot_id}/generate-course`,
      request,
      {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data;
  }

  /**
   * Find similar screenshots via semantic search
   *
   * BUSINESS VALUE:
   * - Prevents duplicate course creation
   * - Enables content reuse and inspiration
   * - Helps discover existing related courses
   *
   * @param queryText - Text to search for
   * @param organizationId - Optional org filter
   * @param nResults - Maximum number of results
   * @returns List of similar screenshots with scores
   */
  async findSimilarScreenshots(
    queryText: string,
    organizationId?: string,
    nResults: number = 5
  ): Promise<SimilarScreenshot[]> {
    const response = await axios.post<{ results: SimilarScreenshot[] }>(
      `${COURSE_GENERATOR_URL}/api/v1/rag/screenshots/find-similar`,
      {
        query_text: queryText,
        organization_id: organizationId,
        n_results: nResults,
      },
      {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data.results;
  }

  /**
   * Get screenshot statistics
   *
   * @param organizationId - Optional organization filter
   * @returns Statistics about screenshot usage
   */
  async getScreenshotStats(
    organizationId?: string
  ): Promise<{
    total_screenshots: number;
    by_provider: Record<string, number>;
    by_content_type: Record<string, number>;
    by_status: Record<string, number>;
  }> {
    const params = organizationId ? `?organization_id=${organizationId}` : '';
    const response = await axios.get(
      `${COURSE_GENERATOR_URL}/api/v1/rag/screenshots/stats${params}`,
      {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data.statistics;
  }

  /**
   * Get available LLM providers for the organization
   *
   * @param organizationId - Organization ID
   * @returns List of configured LLM providers
   */
  async getLLMProviders(organizationId: string): Promise<LLMProviderConfig[]> {
    const response = await axios.get<{ configs: LLMProviderConfig[] }>(
      `/api/v1/organizations/${organizationId}/llm-config`,
      {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data.configs;
  }

  /**
   * Get list of available LLM providers
   *
   * @returns List of all supported LLM providers
   */
  async getAvailableLLMProviders(): Promise<AvailableLLMProvider[]> {
    const response = await axios.get<{ providers: AvailableLLMProvider[] }>(
      `/api/v1/organizations/llm-config/providers`,
      {
        headers: {
          Authorization: `Bearer ${tokenManager.getToken()}`,
        },
      }
    );

    return response.data.providers;
  }

  /**
   * Poll for screenshot status until complete
   *
   * TECHNICAL IMPLEMENTATION:
   * Polls the status endpoint at regular intervals until processing
   * is complete or fails. Returns the final status.
   *
   * @param screenshotId - Screenshot ID to poll
   * @param onProgress - Optional callback for progress updates
   * @param intervalMs - Polling interval in milliseconds
   * @param maxAttempts - Maximum polling attempts
   * @returns Final status when complete
   */
  async pollUntilComplete(
    screenshotId: string,
    onProgress?: (status: ScreenshotStatus) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 60
  ): Promise<ScreenshotStatus> {
    return new Promise((resolve, reject) => {
      let attempts = 0;

      const poll = async () => {
        try {
          const status = await this.getScreenshotStatus(screenshotId);

          if (onProgress) {
            onProgress(status);
          }

          if (status.status === 'analyzed' || status.status === 'course_generated') {
            resolve(status);
            return;
          }

          if (status.status === 'failed') {
            reject(new Error(status.error_message || 'Screenshot analysis failed'));
            return;
          }

          attempts++;
          if (attempts >= maxAttempts) {
            reject(new Error('Timeout waiting for screenshot analysis'));
            return;
          }

          setTimeout(poll, intervalMs);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  /**
   * Validate image file for upload
   *
   * @param file - File to validate
   * @returns Validation result with any error message
   */
  validateImageFile(file: File): { valid: boolean; error?: string } {
    const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
    const maxSizeMB = 10;

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Invalid file type. Please upload PNG, JPEG, or WEBP images.',
      };
    }

    if (file.size > maxSizeMB * 1024 * 1024) {
      return {
        valid: false,
        error: `File too large. Maximum size is ${maxSizeMB}MB.`,
      };
    }

    return { valid: true };
  }
}

// Export singleton instance
export const screenshotService = new ScreenshotService();
