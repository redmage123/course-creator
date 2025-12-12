/**
 * Syllabus Generation Service
 *
 * BUSINESS CONTEXT:
 * Enables URL-based course generation from external third-party documentation.
 * Instructors can provide documentation URLs (Salesforce, AWS, internal wikis, etc.)
 * and the system will automatically generate comprehensive training materials.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Calls course-generator API for URL-based generation
 * - Supports progress tracking for long-running operations
 * - Type-safe TypeScript interfaces
 * - Error handling for various failure scenarios
 *
 * @version 3.3.2
 */

import { apiClient } from './apiClient';

/**
 * Course difficulty levels
 */
export type CourseLevel = 'beginner' | 'intermediate' | 'advanced';

/**
 * Content source types for external documentation
 */
export type ContentSourceType =
  | 'documentation'
  | 'tutorial'
  | 'api_reference'
  | 'knowledge_base'
  | 'blog'
  | 'wiki'
  | 'general';

/**
 * External source configuration
 *
 * Allows advanced configuration for documentation sources
 * including type classification and priority for multi-URL requests.
 */
export interface ExternalSourceConfig {
  url: string;
  source_type?: ContentSourceType;
  priority?: number; // 1-10, higher = more important
  description?: string;
}

/**
 * Module topic within a syllabus module
 */
export interface ModuleTopic {
  title: string;
  description: string;
  duration?: number; // minutes
  objectives?: string[];
}

/**
 * Syllabus module
 */
export interface SyllabusModule {
  module_number: number;
  title: string;
  description: string;
  duration?: number; // minutes
  objectives?: string[];
  topics?: ModuleTopic[];
  source_url?: string; // Attribution to source URL
}

/**
 * Generated syllabus data
 */
export interface SyllabusData {
  title: string;
  description: string;
  level: CourseLevel;
  duration?: number; // hours
  objectives?: string[];
  prerequisites?: string[];
  target_audience?: string;
  modules: SyllabusModule[];
  external_sources?: Array<{
    url: string;
    title?: string;
  }>;
  generated_at?: string;
  generation_method?: string;
}

/**
 * Request for syllabus generation
 *
 * SUPPORTS TWO MODES:
 * - Standard: Generate from title/description only
 * - URL-based: Generate from external documentation URLs
 */
export interface GenerateSyllabusRequest {
  title: string;
  description: string;
  level?: CourseLevel;
  duration?: number; // hours
  objectives?: string[];
  prerequisites?: string[];
  target_audience?: string;

  // URL-based generation fields (v3.3.2)
  source_url?: string;
  source_urls?: string[];
  external_sources?: ExternalSourceConfig[];

  // URL processing options
  use_rag_enhancement?: boolean;
  include_code_examples?: boolean;
  max_content_chunks?: number;
}

/**
 * Source summary from URL-based generation
 */
export interface SourceSummary {
  urls_processed: number;
  urls_failed: number;
  total_words?: number;
  total_chunks?: number;
  code_examples_found?: number;
  sources?: Array<{
    url: string;
    title?: string;
    word_count?: number;
  }>;
}

/**
 * Response from syllabus generation
 */
export interface GenerateSyllabusResponse {
  success: boolean;
  syllabus?: SyllabusData;
  message?: string;
  course_id?: string;
  generation_method?: string;
  source_summary?: SourceSummary;
  processing_time_ms?: number;
  request_id?: string;
}

/**
 * Generation progress information
 */
export interface GenerationProgress {
  request_id: string;
  status: string;
  total_urls: number;
  urls_fetched: number;
  urls_failed: number;
  chunks_created: number;
  chunks_ingested: number;
  generation_started: boolean;
  generation_complete: boolean;
  current_step: string;
  error_count: number;
  elapsed_seconds: number;
}

/**
 * Progress response
 */
export interface GetProgressResponse {
  success: boolean;
  progress: GenerationProgress;
}

/**
 * Validation error details
 */
export interface ValidationErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/**
 * API error response
 */
export interface APIErrorResponse {
  detail?: string | { error: string; message: string; error_code?: string } | ValidationErrorDetail[];
}

/**
 * Syllabus Generation Service
 *
 * WHY THIS APPROACH:
 * - Dedicated service for syllabus generation operations
 * - Separate from course management CRUD operations
 * - Supports long-running operations with progress tracking
 * - Clear error handling for URL-related failures
 */
class SyllabusService {
  private baseUrl = '/api/v1/syllabus';

  /**
   * Generate syllabus from provided parameters
   *
   * SUPPORTS TWO GENERATION MODES:
   * 1. Standard: Uses title/description only
   * 2. URL-based: Fetches content from external URLs
   *
   * @param request - Generation request with optional URLs
   * @returns Generated syllabus with source attribution
   */
  async generateSyllabus(request: GenerateSyllabusRequest): Promise<GenerateSyllabusResponse> {
    try {
      const response = await apiClient.post<GenerateSyllabusResponse>(
        `${this.baseUrl}/generate`,
        request
      );
      return response;
    } catch (error) {
      // Transform error for better UI handling
      throw this.transformError(error);
    }
  }

  /**
   * Get progress of a generation request
   *
   * BUSINESS CONTEXT:
   * URL-based generation can take time due to fetching multiple URLs.
   * This allows the UI to show real-time progress updates.
   *
   * @param requestId - UUID of the generation request
   * @returns Progress information
   */
  async getGenerationProgress(requestId: string): Promise<GetProgressResponse> {
    try {
      const response = await apiClient.get<GetProgressResponse>(
        `${this.baseUrl}/generate/progress/${requestId}`
      );
      return response;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Validate URL format
   *
   * @param url - URL to validate
   * @returns Whether URL is valid
   */
  validateUrl(url: string): { valid: boolean; error?: string } {
    if (!url || !url.trim()) {
      return { valid: false, error: 'URL cannot be empty' };
    }

    const trimmedUrl = url.trim();

    // Check scheme
    if (!trimmedUrl.startsWith('http://') && !trimmedUrl.startsWith('https://')) {
      return { valid: false, error: 'URL must start with http:// or https://' };
    }

    // Check length
    if (trimmedUrl.length > 2048) {
      return { valid: false, error: 'URL exceeds maximum length of 2048 characters' };
    }

    // Basic URL format check
    try {
      new URL(trimmedUrl);
    } catch {
      return { valid: false, error: 'Invalid URL format' };
    }

    return { valid: true };
  }

  /**
   * Validate multiple URLs
   *
   * @param urls - Array of URLs to validate
   * @returns Validation results
   */
  validateUrls(urls: string[]): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Check count limit
    if (urls.length > 10) {
      errors.push('Maximum 10 URLs allowed');
    }

    // Validate each URL
    urls.forEach((url, index) => {
      const result = this.validateUrl(url);
      if (!result.valid) {
        errors.push(`URL ${index + 1}: ${result.error}`);
      }
    });

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Transform API errors for UI display
   *
   * @param error - Raw error from API
   * @returns Transformed error with user-friendly message
   */
  private transformError(error: unknown): Error {
    if (error instanceof Error) {
      // Check if it's an API error with details
      const apiError = error as Error & { response?: { data?: APIErrorResponse } };

      if (apiError.response?.data?.detail) {
        const detail = apiError.response.data.detail;

        if (typeof detail === 'string') {
          return new Error(detail);
        }

        if (Array.isArray(detail)) {
          // Validation errors
          const messages = detail.map(
            (d: ValidationErrorDetail) => `${d.loc.join('.')}: ${d.msg}`
          );
          return new Error(`Validation failed: ${messages.join(', ')}`);
        }

        if (typeof detail === 'object' && 'message' in detail) {
          return new Error(detail.message);
        }
      }

      return error;
    }

    return new Error('An unexpected error occurred');
  }

  /**
   * Check if generation request has external sources
   *
   * @param request - Generation request
   * @returns Whether request includes external URLs
   */
  hasExternalSources(request: GenerateSyllabusRequest): boolean {
    return Boolean(
      request.source_url ||
        (request.source_urls && request.source_urls.length > 0) ||
        (request.external_sources && request.external_sources.length > 0)
    );
  }

  /**
   * Get all source URLs from request
   *
   * @param request - Generation request
   * @returns Array of all source URLs
   */
  getAllSourceUrls(request: GenerateSyllabusRequest): string[] {
    const urls: string[] = [];

    if (request.source_url) {
      urls.push(request.source_url);
    }

    if (request.source_urls) {
      urls.push(...request.source_urls);
    }

    if (request.external_sources) {
      request.external_sources.forEach((source) => {
        if (!urls.includes(source.url)) {
          urls.push(source.url);
        }
      });
    }

    return urls;
  }
}

// Export singleton instance
export const syllabusService = new SyllabusService();
