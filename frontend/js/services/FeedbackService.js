/**
 * Feedback Service - Single Responsibility for Feedback Operations
 *
 * BUSINESS CONTEXT:
 * Handles all bi-directional feedback operations between students and instructors
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only manages feedback operations
 * - Open/Closed: Extensible for new feedback features without modification
 * - Dependency Inversion: Depends on Auth abstraction, not concrete implementation
 *
 * TECHNICAL IMPLEMENTATION:
 * - Async/await for all API calls
 * - Centralized error handling
 * - Authentication integration
 * - Configuration-based endpoints
 * - Support for course feedback (student → course) and student feedback (instructor → student)
 */

import { Auth } from '../modules/auth.js';

export class FeedbackService {
    constructor() {
        this.baseUrl = window.CONFIG?.API_URLS?.COURSE_MANAGEMENT || 'https://localhost:8004';
    }

    /**
     * Submit course feedback (student providing feedback about a course)
     *
     * @param {Object} feedbackData - Course feedback data
     * @returns {Promise<Object>} Created feedback object
     */
    async submitCourseFeedback(feedbackData) {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.baseUrl}/feedback/course`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...feedbackData,
                    student_id: currentUser.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to submit course feedback');
            }

            return await response.json();
        } catch (error) {
            console.error('Error submitting course feedback:', error);
            throw error;
        }
    }

    /**
     * Load course feedback for a specific course
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Array>} Array of course feedback objects
     */
    async loadCourseFeedback(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/feedback/course/${courseId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load course feedback: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading course feedback:', error);
            throw error;
        }
    }

    /**
     * Submit student feedback (instructor providing feedback about a student)
     *
     * @param {Object} feedbackData - Student feedback data
     * @returns {Promise<Object>} Created feedback object
     */
    async submitStudentFeedback(feedbackData) {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.baseUrl}/feedback/student`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...feedbackData,
                    instructor_id: currentUser.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to submit student feedback');
            }

            return await response.json();
        } catch (error) {
            console.error('Error submitting student feedback:', error);
            throw error;
        }
    }

    /**
     * Load feedback for a specific student
     *
     * @param {string} studentId - Student ID
     * @returns {Promise<Array>} Array of student feedback objects
     */
    async loadStudentFeedback(studentId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/feedback/student/${studentId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load student feedback: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading student feedback:', error);
            throw error;
        }
    }

    /**
     * Load all feedback data (both course and student feedback)
     *
     * @returns {Promise<Object>} Object containing courseFeedback and studentFeedback arrays
     */
    async loadAllFeedbackData() {
        try {
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            // Load instructor's course feedback and student feedback in parallel
            const courseFeedbackPromises = [];
            const studentFeedbackPromises = [];

            // For instructors, load feedback for their courses
            if (currentUser.role === 'instructor' || currentUser.role_name === 'instructor') {
                // This would typically fetch courses first, then get feedback for each
                // For now, we'll structure it to be filled in by the calling code
                return {
                    courseFeedback: [],
                    studentFeedback: []
                };
            }

            return {
                courseFeedback: [],
                studentFeedback: []
            };
        } catch (error) {
            console.error('Error loading feedback data:', error);
            throw error;
        }
    }

    /**
     * Respond to course feedback
     *
     * @param {string} feedbackId - Feedback ID
     * @param {string} responseText - Response text
     * @returns {Promise<Object>} Updated feedback object
     */
    async respondToFeedback(feedbackId, responseText) {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.baseUrl}/feedback/${feedbackId}/respond`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    response_text: responseText,
                    responder_id: currentUser.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to respond to feedback');
            }

            return await response.json();
        } catch (error) {
            console.error('Error responding to feedback:', error);
            throw error;
        }
    }

    /**
     * Mark feedback as resolved
     *
     * @param {string} feedbackId - Feedback ID
     * @returns {Promise<Object>} Updated feedback object
     */
    async markFeedbackResolved(feedbackId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/feedback/${feedbackId}/resolve`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to mark feedback as resolved');
            }

            return await response.json();
        } catch (error) {
            console.error('Error marking feedback as resolved:', error);
            throw error;
        }
    }

    /**
     * Filter feedback by status
     *
     * @param {Array} feedbackArray - Array of feedback objects
     * @param {string} status - Status filter ('all', 'pending', 'responded', 'resolved')
     * @returns {Array} Filtered feedback array
     */
    filterFeedback(feedbackArray, status) {
        if (status === 'all') {
            return feedbackArray;
        }

        return feedbackArray.filter(feedback => {
            if (status === 'pending') {
                return !feedback.response && !feedback.resolved;
            } else if (status === 'responded') {
                return feedback.response && !feedback.resolved;
            } else if (status === 'resolved') {
                return feedback.resolved;
            }
            return true;
        });
    }

    /**
     * Export feedback report
     *
     * @param {string} courseId - Course ID for report
     * @param {string} format - Export format ('csv', 'pdf', 'json')
     * @returns {Promise<Blob>} Report file blob
     */
    async exportFeedbackReport(courseId, format = 'csv') {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/feedback/course/${courseId}/export?format=${format}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to export feedback report: ${response.status}`);
            }

            return await response.blob();
        } catch (error) {
            console.error('Error exporting feedback report:', error);
            throw error;
        }
    }

    /**
     * Get feedback statistics for a course
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Object>} Feedback statistics
     */
    async getFeedbackStatistics(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');
            const analyticsUrl = window.CONFIG?.API_URLS?.ANALYTICS || 'https://localhost:8008';

            const response = await fetch(`${analyticsUrl}/analytics/courses/${courseId}/feedback/statistics`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load feedback statistics: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading feedback statistics:', error);
            throw error;
        }
    }
}

// Create singleton instance
export const feedbackService = new FeedbackService();
export default feedbackService;
