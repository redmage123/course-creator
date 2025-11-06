/**
 * Analytics Service - Single Responsibility for Analytics Operations
 *
 * BUSINESS CONTEXT:
 * Handles all analytics and reporting operations for instructors
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only manages analytics operations
 * - Open/Closed: Extensible for new analytics features without modification
 * - Dependency Inversion: Depends on Auth abstraction, not concrete implementation
 *
 * TECHNICAL IMPLEMENTATION:
 * - Async/await for all API calls
 * - Centralized error handling
 * - Authentication integration
 * - Configuration-based endpoints
 */
import { Auth } from '../modules/auth.js';

export class AnalyticsService {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     */
    constructor() {
        this.baseUrl = window.CONFIG?.API_URLS?.ANALYTICS || 'https://localhost:8008';
    }

    /**
     * Load analytics data for instructor
     *
     * @param {Object} params - Analytics parameters
     * @param {string} params.instructorId - Instructor ID
     * @param {string} params.courseId - Optional course ID filter
     * @param {string} params.timeRange - Time range in days (default: 30)
     * @returns {Promise<Object>} Analytics data
     */
    async loadInstructorAnalytics(params) {
        try {
            const authToken = localStorage.getItem('authToken');

            const url = new URL(`${this.baseUrl}/instructor/analytics`);
            url.searchParams.append('instructor_id', params.instructorId);
            if (params.courseId) {
                url.searchParams.append('course_id', params.courseId);
            }
            url.searchParams.append('time_range', params.timeRange || '30');

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load analytics: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading instructor analytics:', error);
            throw error;
        }
    }

    /**
     * Load overview statistics for instructor
     *
     * @param {string} instructorId - Instructor ID
     * @returns {Promise<Object>} Overview statistics
     */
    async loadOverviewStats(instructorId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/instructor/overview?instructor_id=${instructorId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load overview stats: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading overview stats:', error);
            throw error;
        }
    }

    /**
     * Load course analytics
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Object>} Course analytics data
     */
    async loadCourseAnalytics(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/courses/${courseId}/analytics`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load course analytics: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading course analytics:', error);
            throw error;
        }
    }

    /**
     * Load student performance analytics
     *
     * @param {string} studentId - Student ID
     * @param {string} courseId - Optional course ID filter
     * @returns {Promise<Object>} Student performance data
     */
    async loadStudentPerformance(studentId, courseId = null) {
        try {
            const authToken = localStorage.getItem('authToken');

            let url = `${this.baseUrl}/students/${studentId}/performance`;
            if (courseId) {
                url += `?course_id=${courseId}`;
            }

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load student performance: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading student performance:', error);
            throw error;
        }
    }

    /**
     * Export analytics report
     *
     * @param {Object} params - Export parameters
     * @param {string} params.instructorId - Instructor ID
     * @param {string} params.format - Export format ('csv', 'pdf', 'json')
     * @param {string} params.timeRange - Time range
     * @returns {Promise<Blob>} Report file blob
     */
    async exportAnalyticsReport(params) {
        try {
            const authToken = localStorage.getItem('authToken');

            const url = new URL(`${this.baseUrl}/instructor/analytics/export`);
            url.searchParams.append('instructor_id', params.instructorId);
            url.searchParams.append('format', params.format || 'csv');
            url.searchParams.append('time_range', params.timeRange || '30');

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to export analytics: ${response.status}`);
            }

            return await response.blob();
        } catch (error) {
            console.error('Error exporting analytics:', error);
            throw error;
        }
    }

    /**
     * Get engagement metrics for a course
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Object>} Engagement metrics
     */
    async getEngagementMetrics(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/courses/${courseId}/engagement`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load engagement metrics: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading engagement metrics:', error);
            throw error;
        }
    }
}

// Create singleton instance
export const analyticsService = new AnalyticsService();
export default analyticsService;
