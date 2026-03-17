/**
 * Lab Service API Client
 *
 * Centralized API client for lab management operations
 * Handles communication with lab-manager service (port 8005)
 *
 * @module features/labs/services/labService
 */

import type { LabSession, LabStatus, LabFile } from '../LabEnvironment';
import type { TerminalCommand } from '../components/TerminalEmulator';
import type { AIMessage } from '../components/AIAssistant';
import type { ResourceUsage } from '../components/ResourceMonitor';

const LAB_API_BASE = 'https://176.9.99.103:8005/api/v1/labs';

/**
 * Custom error class for lab service errors
 */
export class LabServiceError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'LabServiceError';
  }
}

/**
 * Handle API response and errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: 'An error occurred'
    }));

    throw new LabServiceError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData.detail
    );
  }

  return response.json();
}

/**
 * Student Labs List
 * Fetches student-specific lab data with proper data isolation
 */
export const studentLabService = {
  /**
   * Get all labs for the authenticated student.
   *
   * Security Context:
   * Uses student_id from JWT token to ensure data isolation.
   * Prevents cross-user data leakage (OWASP A01:2021).
   *
   * Business Context:
   * Returns labs the student has actually interacted with,
   * fixing the "Retry Lab" button appearing for labs never attempted.
   */
  async getStudentLabs(studentId: string): Promise<{
    student_id: string;
    total_labs: number;
    labs: Array<{
      lab_id: string;
      course_id: string;
      status: string;
      created_at: string;
      last_accessed: string | null;
      ide_urls: Record<string, string>;
      container_name: string;
    }>;
  }> {
    const response = await fetch(`${LAB_API_BASE}/student/${studentId}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' }
    });
    return handleResponse(response);
  }
};

/**
 * Lab Session Management
 */
export const labSessionService = {
  /**
   * Check for existing session
   */
  async getSession(labId: string, courseId: string): Promise<{ session: LabSession | null }> {
    const response = await fetch(
      `${LAB_API_BASE}/session?labId=${labId}&courseId=${courseId}`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Start a new lab session
   */
  async startSession(labId: string, courseId: string): Promise<{ session: LabSession }> {
    const response = await fetch(
      `${LAB_API_BASE}/start`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ labId, courseId })
      }
    );
    return handleResponse(response);
  },

  /**
   * Pause lab session
   */
  async pauseSession(sessionId: string): Promise<{ session: LabSession }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/pause`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Resume lab session
   */
  async resumeSession(sessionId: string): Promise<{ session: LabSession }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/resume`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Stop lab session
   */
  async stopSession(sessionId: string): Promise<void> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/stop`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get resource usage
   */
  async getResourceUsage(sessionId: string): Promise<{ resourceUsage: ResourceUsage }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/resources`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  }
};

/**
 * File System Operations
 */
export const labFileService = {
  /**
   * Get all files in session
   */
  async listFiles(sessionId: string): Promise<{ files: LabFile[] }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/files`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get specific file
   */
  async getFile(sessionId: string, fileId: string): Promise<{ file: LabFile }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/files/${fileId}`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Create new file
   */
  async createFile(
    sessionId: string,
    name: string,
    content: string = '',
    language: string = 'plaintext'
  ): Promise<{ file: LabFile }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/files`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, content, language })
      }
    );
    return handleResponse(response);
  },

  /**
   * Update file content
   */
  async updateFile(
    sessionId: string,
    fileId: string,
    content: string
  ): Promise<{ file: LabFile }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/files/${fileId}`,
      {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      }
    );
    return handleResponse(response);
  },

  /**
   * Delete file
   */
  async deleteFile(sessionId: string, fileId: string): Promise<void> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/files/${fileId}`,
      {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Rename file
   */
  async renameFile(
    sessionId: string,
    fileId: string,
    newName: string
  ): Promise<{ file: LabFile }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/files/${fileId}/rename`,
      {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName })
      }
    );
    return handleResponse(response);
  },

  /**
   * Create folder
   */
  async createFolder(sessionId: string, name: string): Promise<void> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/folders`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      }
    );
    return handleResponse(response);
  }
};

/**
 * Terminal Operations
 */
export const labTerminalService = {
  /**
   * Execute command
   */
  async executeCommand(
    sessionId: string,
    command: string,
    shell: string = '/bin/bash'
  ): Promise<{ output: string; exitCode: number }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/execute`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command, shell })
      }
    );
    return handleResponse(response);
  },

  /**
   * Get command history
   */
  async getHistory(sessionId: string): Promise<{ history: TerminalCommand[] }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/history`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  }
};

/**
 * AI Assistant Operations
 */
export const labAIService = {
  /**
   * Send message to AI assistant
   */
  async sendMessage(
    sessionId: string,
    message: string,
    context?: {
      file?: string;
      code?: string;
      error?: string;
    }
  ): Promise<{ response: string; messageId: string }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/ai/chat`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, context })
      }
    );
    return handleResponse(response);
  },

  /**
   * Get AI chat history
   */
  async getChatHistory(sessionId: string): Promise<{ messages: AIMessage[] }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/ai/history`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get code explanation
   */
  async explainCode(
    sessionId: string,
    code: string,
    language: string
  ): Promise<{ explanation: string }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/ai/explain`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language })
      }
    );
    return handleResponse(response);
  },

  /**
   * Get debugging help
   */
  async debugError(
    sessionId: string,
    error: string,
    code: string,
    language: string
  ): Promise<{ suggestion: string }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/ai/debug`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error, code, language })
      }
    );
    return handleResponse(response);
  }
};

/**
 * Lab Analytics
 */
export const labAnalyticsService = {
  /**
   * Track lab event
   */
  async trackEvent(
    sessionId: string,
    eventType: string,
    metadata?: Record<string, any>
  ): Promise<void> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/analytics/event`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ eventType, metadata })
      }
    );
    return handleResponse(response);
  },

  /**
   * Get lab analytics summary
   */
  async getAnalytics(sessionId: string): Promise<{
    timeSpent: number;
    filesCreated: number;
    commandsExecuted: number;
    errorsEncountered: number;
  }> {
    const response = await fetch(
      `${LAB_API_BASE}/${sessionId}/analytics`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  }
};

/**
 * Unified lab service export
 */
export const labService = {
  student: studentLabService,
  session: labSessionService,
  files: labFileService,
  terminal: labTerminalService,
  ai: labAIService,
  analytics: labAnalyticsService
};

export default labService;
