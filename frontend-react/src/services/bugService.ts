/**
 * Bug Tracking Service
 *
 * BUSINESS CONTEXT:
 * API client for the bug tracking system. Allows users to submit bugs,
 * track their status, and view analysis results.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses apiClient for authenticated requests to bug-tracking microservice.
 * Supports bug submission, status tracking, and analysis viewing.
 *
 * SERVICE ENDPOINT: https://localhost:8017/api/v1
 */

import { apiClient } from './apiClient';

// ============================================================
// Type Definitions
// ============================================================

/**
 * Bug severity levels
 */
export type BugSeverity = 'low' | 'medium' | 'high' | 'critical';

/**
 * Bug status values
 */
export type BugStatus =
  | 'submitted'
  | 'analyzing'
  | 'analysis_complete'
  | 'fixing'
  | 'fix_ready'
  | 'pr_opened'
  | 'resolved'
  | 'closed'
  | 'wont_fix';

/**
 * Complexity estimate for fixes
 */
export type ComplexityEstimate = 'trivial' | 'simple' | 'moderate' | 'complex' | 'very_complex';

/**
 * Request to submit a new bug report
 */
export interface BugSubmissionRequest {
  title: string;
  description: string;
  steps_to_reproduce?: string;
  expected_behavior?: string;
  actual_behavior?: string;
  severity: BugSeverity;
  affected_component?: string;
  browser_info?: string;
  submitter_email: string;
}

/**
 * Bug report response from API
 */
export interface BugReport {
  id: string;
  title: string;
  description: string;
  steps_to_reproduce?: string;
  expected_behavior?: string;
  actual_behavior?: string;
  severity: BugSeverity;
  status: BugStatus;
  affected_component?: string;
  browser_info?: string;
  submitter_email: string;
  submitter_user_id?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Bug analysis result from Claude
 */
export interface BugAnalysis {
  id: string;
  bug_report_id: string;
  root_cause_analysis: string;
  suggested_fix: string;
  affected_files: string[];
  confidence_score: number;
  complexity_estimate: ComplexityEstimate;
  claude_model_used: string;
  tokens_used: number;
  analysis_completed_at?: string;
  created_at: string;
}

/**
 * File change in a fix attempt
 */
export interface FileChange {
  file_path: string;
  change_type: 'modify' | 'create' | 'delete';
  diff?: string;
  description: string;
}

/**
 * Bug fix attempt details
 */
export interface BugFix {
  id: string;
  bug_report_id: string;
  analysis_id: string;
  status: string;
  pr_number?: number;
  pr_url?: string;
  branch_name?: string;
  files_changed: FileChange[];
  lines_added: number;
  lines_removed: number;
  tests_passed: number;
  tests_failed: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

/**
 * Complete bug details with analysis and fix
 */
export interface BugDetail {
  bug: BugReport;
  analysis?: BugAnalysis;
  fix_attempt?: BugFix;
}

/**
 * Bug list response with pagination
 */
export interface BugListResponse {
  bugs: BugReport[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

/**
 * Filters for bug list queries
 */
export interface BugFilters {
  status?: BugStatus;
  severity?: BugSeverity;
  page?: number;
  limit?: number;
}

// ============================================================
// Bug Service Implementation
// ============================================================

/**
 * Bug Tracking API Service
 *
 * Provides methods for:
 * - Submitting new bug reports
 * - Retrieving bug status and analysis
 * - Listing user's submitted bugs
 * - Requesting re-analysis
 */
class BugService {
  /**
   * Base URL for bug tracking service
   * Uses port 8017 for the dedicated bug-tracking microservice
   */
  private baseUrl = '/api/v1/bugs';

  /**
   * Get the full service URL
   * In development, connects directly to bug-tracking service
   * In production, routes through nginx proxy
   */
  private getServiceUrl(): string {
    // In development, we might need to hit the bug-tracking service directly
    // Check if we're in development mode
    const isDev = import.meta.env.DEV;
    if (isDev) {
      // Use the bug-tracking service port directly
      return 'https://localhost:8017/api/v1';
    }
    // In production, use the proxied path
    return '/api/bug-tracking/v1';
  }

  /**
   * Submit a new bug report
   *
   * @param data - Bug submission data
   * @returns Created bug report with ID for tracking
   */
  async submitBug(data: BugSubmissionRequest): Promise<BugReport> {
    const url = `${this.getServiceUrl()}/bugs`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to submit bug' }));
      throw new Error(error.detail || 'Failed to submit bug');
    }

    return response.json();
  }

  /**
   * Get bug details by ID
   *
   * @param bugId - Bug report ID
   * @returns Complete bug details including analysis and fix attempt
   */
  async getBug(bugId: string): Promise<BugDetail> {
    const url = `${this.getServiceUrl()}/bugs/${bugId}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Bug report not found');
      }
      throw new Error('Failed to fetch bug details');
    }

    return response.json();
  }

  /**
   * Get analysis results for a bug
   *
   * @param bugId - Bug report ID
   * @returns Analysis results from Claude
   */
  async getBugAnalysis(bugId: string): Promise<BugAnalysis> {
    const url = `${this.getServiceUrl()}/bugs/${bugId}/analysis`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Analysis not found');
      }
      throw new Error('Failed to fetch analysis');
    }

    return response.json();
  }

  /**
   * Get fix attempt details for a bug
   *
   * @param bugId - Bug report ID
   * @returns Fix attempt details including PR info
   */
  async getBugFix(bugId: string): Promise<BugFix> {
    const url = `${this.getServiceUrl()}/bugs/${bugId}/fix`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Fix attempt not found');
      }
      throw new Error('Failed to fetch fix details');
    }

    return response.json();
  }

  /**
   * List all bugs (admin only)
   *
   * @param filters - Optional filters for status, severity, pagination
   * @returns Paginated list of bug reports
   */
  async listBugs(filters?: BugFilters): Promise<BugListResponse> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.severity) params.append('severity', filters.severity);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const url = `${this.getServiceUrl()}/bugs?${params.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch bugs');
    }

    return response.json();
  }

  /**
   * List bugs submitted by current user
   *
   * @param filters - Optional filters for status, severity, pagination
   * @returns Paginated list of user's bug reports
   */
  async listMyBugs(filters?: BugFilters): Promise<BugListResponse> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.severity) params.append('severity', filters.severity);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const url = `${this.getServiceUrl()}/bugs/my/reports?${params.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch your bugs');
    }

    return response.json();
  }

  /**
   * Request re-analysis of a bug
   *
   * @param bugId - Bug report ID to re-analyze
   * @returns Updated bug report
   */
  async requestReanalysis(bugId: string): Promise<BugReport> {
    const url = `${this.getServiceUrl()}/bugs/${bugId}/reanalyze`;
    const response = await fetch(url, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to request re-analysis');
    }

    return response.json();
  }

  /**
   * Get authentication headers from stored token
   */
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
    return {};
  }
}

// Export singleton instance
export const bugService = new BugService();
