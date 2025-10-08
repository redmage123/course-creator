/**
 * Course Service - Single Responsibility for Course Operations
 *
 * BUSINESS CONTEXT:
 * Handles all course-related CRUD operations for instructors
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only manages course operations
 * - Open/Closed: Extensible for new course features without modification
 * - Dependency Inversion: Depends on Auth abstraction, not concrete implementation
 *
 * TECHNICAL IMPLEMENTATION:
 * - Async/await for all API calls
 * - Centralized error handling
 * - Authentication integration
 * - Configuration-based endpoints
 */

import { Auth } from '../modules/auth.js';

export class CourseService {
    constructor() {
        this.baseUrl = window.CONFIG?.API_URLS?.COURSE_MANAGEMENT || 'https://localhost:8004';
    }

    /**
     * Load all courses for the current instructor
     *
     * @returns {Promise<Array>} Array of course objects
     */
    async loadCourses() {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.baseUrl}/courses?instructor_id=${currentUser.id}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load courses: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading courses:', error);
            throw error;
        }
    }

    /**
     * Create a new course
     *
     * @param {Object} courseData - Course data object
     * @returns {Promise<Object>} Created course object
     */
    async createCourse(courseData) {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.baseUrl}/courses`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...courseData,
                    instructor_id: currentUser.id,
                    organization_id: currentUser.organization_id,
                    status: courseData.status || 'draft'
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create course');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating course:', error);
            throw error;
        }
    }

    /**
     * Update an existing course
     *
     * @param {string} courseId - Course ID
     * @param {Object} courseData - Updated course data
     * @returns {Promise<Object>} Updated course object
     */
    async updateCourse(courseId, courseData) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/courses/${courseId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(courseData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update course');
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating course:', error);
            throw error;
        }
    }

    /**
     * Delete a course
     *
     * @param {string} courseId - Course ID to delete
     * @returns {Promise<void>}
     */
    async deleteCourse(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/courses/${courseId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete course');
            }

            return true;
        } catch (error) {
            console.error('Error deleting course:', error);
            throw error;
        }
    }

    /**
     * Get a single course by ID
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Object>} Course object
     */
    async getCourse(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/courses/${courseId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load course: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading course:', error);
            throw error;
        }
    }

    /**
     * Load published courses
     *
     * @returns {Promise<Array>} Array of published courses
     */
    async loadPublishedCourses() {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/courses?status=published`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load published courses: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading published courses:', error);
            throw error;
        }
    }

    /**
     * Publish a course
     *
     * @param {string} courseId - Course ID to publish
     * @returns {Promise<Object>} Updated course object
     */
    async publishCourse(courseId) {
        return this.updateCourse(courseId, { status: 'published' });
    }

    /**
     * Unpublish a course
     *
     * @param {string} courseId - Course ID to unpublish
     * @returns {Promise<Object>} Updated course object
     */
    async unpublishCourse(courseId) {
        return this.updateCourse(courseId, { status: 'draft' });
    }
}

// Create singleton instance
export const courseService = new CourseService();
export default courseService;
