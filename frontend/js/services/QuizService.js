/**
 * Quiz Service - Single Responsibility for Quiz Operations
 *
 * BUSINESS CONTEXT:
 * Handles all quiz-related operations including generation, publication, and management
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only manages quiz operations
 * - Open/Closed: Extensible for new quiz features without modification
 * - Dependency Inversion: Depends on Auth abstraction, not concrete implementation
 *
 * TECHNICAL IMPLEMENTATION:
 * - Async/await for all API calls
 * - Centralized error handling
 * - Authentication integration
 * - Configuration-based endpoints
 * - Integration with both course-generator (creation) and course-management (publication)
 */

import { Auth } from '../modules/auth.js';

export class QuizService {
    constructor() {
        this.contentUrl = window.CONFIG?.API_URLS?.CONTENT_MANAGEMENT || 'https://localhost:8002';
        this.courseUrl = window.CONFIG?.API_URLS?.COURSE_MANAGEMENT || 'https://localhost:8004';
        this.generatorUrl = window.CONFIG?.API_URLS?.COURSE_GENERATOR || 'https://localhost:8001';
    }

    /**
     * Load all quizzes for a course
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Array>} Array of quiz objects
     */
    async loadQuizzes(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.contentUrl}/api/v1/courses/${courseId}/content?type=quiz`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load quizzes: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading quizzes:', error);
            throw error;
        }
    }

    /**
     * Generate a new quiz using AI
     *
     * @param {Object} quizRequest - Quiz generation parameters
     * @returns {Promise<Object>} Generated quiz object
     */
    async generateQuiz(quizRequest) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.generatorUrl}/api/v1/generate/quiz`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(quizRequest)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate quiz');
            }

            return await response.json();
        } catch (error) {
            console.error('Error generating quiz:', error);
            throw error;
        }
    }

    /**
     * Create a new quiz manually
     *
     * @param {Object} quizData - Quiz data object
     * @returns {Promise<Object>} Created quiz object
     */
    async createQuiz(quizData) {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.contentUrl}/api/v1/quizzes`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...quizData,
                    created_by: currentUser.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create quiz');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating quiz:', error);
            throw error;
        }
    }

    /**
     * Get a single quiz by ID
     *
     * @param {string} quizId - Quiz ID
     * @returns {Promise<Object>} Quiz object
     */
    async getQuiz(quizId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.contentUrl}/api/v1/quizzes/${quizId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load quiz: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading quiz:', error);
            throw error;
        }
    }

    /**
     * Update an existing quiz
     *
     * @param {string} quizId - Quiz ID
     * @param {Object} quizData - Updated quiz data
     * @returns {Promise<Object>} Updated quiz object
     */
    async updateQuiz(quizId, quizData) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.contentUrl}/api/v1/quizzes/${quizId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(quizData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update quiz');
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating quiz:', error);
            throw error;
        }
    }

    /**
     * Delete a quiz
     *
     * @param {string} quizId - Quiz ID to delete
     * @returns {Promise<void>}
     */
    async deleteQuiz(quizId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.contentUrl}/api/v1/quizzes/${quizId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete quiz');
            }

            return true;
        } catch (error) {
            console.error('Error deleting quiz:', error);
            throw error;
        }
    }

    /**
     * Publish a quiz to a course instance
     *
     * @param {Object} publicationRequest - Quiz publication request
     * @returns {Promise<Object>} Quiz publication confirmation
     */
    async publishQuiz(publicationRequest) {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.courseUrl}/quizzes/publish`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...publicationRequest,
                    instructor_id: currentUser.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to publish quiz');
            }

            return await response.json();
        } catch (error) {
            console.error('Error publishing quiz:', error);
            throw error;
        }
    }

    /**
     * Unpublish a quiz from a course instance
     *
     * @param {string} publicationId - Quiz publication ID
     * @returns {Promise<void>}
     */
    async unpublishQuiz(publicationId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.courseUrl}/quizzes/publications/${publicationId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to unpublish quiz');
            }

            return true;
        } catch (error) {
            console.error('Error unpublishing quiz:', error);
            throw error;
        }
    }

    /**
     * Get quiz publications for a course instance
     *
     * @param {string} instanceId - Course instance ID
     * @returns {Promise<Array>} Array of quiz publications
     */
    async getQuizPublications(instanceId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.courseUrl}/course-instances/${instanceId}/quiz-publications`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load quiz publications: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading quiz publications:', error);
            throw error;
        }
    }

    /**
     * Submit a quiz attempt (primarily for students, but instructors can preview)
     *
     * @param {Object} attemptData - Quiz attempt data
     * @returns {Promise<Object>} Quiz attempt results
     */
    async submitQuizAttempt(attemptData) {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.courseUrl}/quiz-attempts`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...attemptData,
                    user_id: currentUser.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to submit quiz attempt');
            }

            return await response.json();
        } catch (error) {
            console.error('Error submitting quiz attempt:', error);
            throw error;
        }
    }

    /**
     * Get quiz analytics for a course
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Object>} Quiz analytics data
     */
    async getQuizAnalytics(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');
            const analyticsUrl = window.CONFIG?.API_URLS?.ANALYTICS || 'https://localhost:8008';

            const response = await fetch(`${analyticsUrl}/analytics/courses/${courseId}/quizzes`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load quiz analytics: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading quiz analytics:', error);
            throw error;
        }
    }
}

// Create singleton instance
export const quizService = new QuizService();
export default quizService;
