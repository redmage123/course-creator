/**
 * Quiz Service API Client
 *
 * Centralized API client for quiz operations
 * Communicates with content-management (port 8001) and course-management (port 8002) services
 *
 * @module features/quizzes/services/quizService
 */

import type { Quiz, QuizAttempt } from '../QuizTaking';

const CONTENT_API_BASE = 'https://176.9.99.103:8001/api/v1';
const COURSE_API_BASE = 'https://176.9.99.103:8002/api/v1';

/**
 * Custom error class for quiz service errors
 */
export class QuizServiceError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'QuizServiceError';
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

    throw new QuizServiceError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData.detail
    );
  }

  return response.json();
}

/**
 * Quiz Service
 */
export const quizService = {
  /**
   * Get quiz by ID
   */
  async getQuiz(quizId: string): Promise<Quiz> {
    const response = await fetch(
      `${CONTENT_API_BASE}/quizzes/${quizId}`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get all quizzes for a course
   */
  async getQuizzesForCourse(courseId: string): Promise<Quiz[]> {
    const response = await fetch(
      `${CONTENT_API_BASE}/courses/${courseId}/quizzes`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get active quiz attempt for student
   */
  async getActiveAttempt(quizId: string): Promise<QuizAttempt | null> {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/active?quizId=${quizId}`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );

    if (response.status === 404) {
      return null;
    }

    return handleResponse(response);
  },

  /**
   * Start new quiz attempt
   */
  async startQuiz(quizId: string): Promise<QuizAttempt> {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quiz_id: quizId,
          started_at: new Date().toISOString()
        })
      }
    );
    return handleResponse(response);
  },

  /**
   * Save answer for a question
   */
  async saveAnswer(
    attemptId: string,
    questionIndex: number,
    answer: string
  ): Promise<void> {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/${attemptId}/answers`,
      {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_index: questionIndex,
          answer
        })
      }
    );
    return handleResponse(response);
  },

  /**
   * Submit quiz attempt
   */
  async submitQuiz(
    attemptId: string,
    answers: Record<number, string>
  ): Promise<QuizAttempt> {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/${attemptId}/submit`,
      {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          answers,
          submitted_at: new Date().toISOString()
        })
      }
    );
    return handleResponse(response);
  },

  /**
   * Get quiz attempts history for student
   */
  async getAttemptHistory(quizId: string): Promise<QuizAttempt[]> {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/history?quizId=${quizId}`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  },

  /**
   * Get quiz attempt by ID
   */
  async getAttempt(attemptId: string): Promise<QuizAttempt> {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/${attemptId}`,
      {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    return handleResponse(response);
  }
};

export default quizService;
