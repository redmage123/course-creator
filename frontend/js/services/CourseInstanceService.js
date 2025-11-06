/**
 * Course Instance Service - Single Responsibility for Course Instance Operations
 *
 * BUSINESS CONTEXT:
 * Handles all course instance (course offering/session) operations
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only manages course instance operations
 * - Open/Closed: Extensible for new instance features without modification
 * - Dependency Inversion: Depends on Auth abstraction, not concrete implementation
 *
 * TECHNICAL IMPLEMENTATION:
 * - Async/await for all API calls
 * - Centralized error handling
 * - Authentication integration
 * - Configuration-based endpoints
 */
import { Auth } from '../modules/auth.js';

export class CourseInstanceService {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     */
    constructor() {
        this.baseUrl = window.CONFIG?.API_URLS?.COURSE_MANAGEMENT || 'https://localhost:8004';
        this.endpoints = window.CONFIG?.ENDPOINTS || {};
    }

    /**
     * Load course instances for an instructor
     *
     * @param {string} instructorId - Instructor ID
     * @returns {Promise<Array>} Array of course instances
     */
    async loadInstructorInstances(instructorId) {
        try {
            const authToken = localStorage.getItem('authToken');

            // Use endpoint if available, otherwise construct URL
            const url = this.endpoints.INSTRUCTOR_INSTANCES
                ? this.endpoints.INSTRUCTOR_INSTANCES(instructorId)
                : `${this.baseUrl}/instructors/${instructorId}/instances`;

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load course instances: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading instructor instances:', error);
            throw error;
        }
    }

    /**
     * Load all course instances
     *
     * @returns {Promise<Array>} Array of course instances
     */
    async loadAllInstances() {
        try {
            const authToken = localStorage.getItem('authToken');

            const url = this.endpoints.COURSE_INSTANCES || `${this.baseUrl}/instances`;

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load course instances: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading course instances:', error);
            throw error;
        }
    }

    /**
     * Create a new course instance
     *
     * @param {Object} instanceData - Instance data
     * @returns {Promise<Object>} Created instance object
     */
    async createInstance(instanceData) {
        try {
            const authToken = localStorage.getItem('authToken');

            const url = this.endpoints.COURSE_INSTANCES || `${this.baseUrl}/instances`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(instanceData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create course instance');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating course instance:', error);
            throw error;
        }
    }

    /**
     * Get a single course instance by ID
     *
     * @param {string} instanceId - Instance ID
     * @returns {Promise<Object>} Instance object
     */
    async getInstance(instanceId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/instances/${instanceId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load instance: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading instance:', error);
            throw error;
        }
    }

    /**
     * Update a course instance
     *
     * @param {string} instanceId - Instance ID
     * @param {Object} instanceData - Updated instance data
     * @returns {Promise<Object>} Updated instance object
     */
    async updateInstance(instanceId, instanceData) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/instances/${instanceId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(instanceData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update instance');
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating instance:', error);
            throw error;
        }
    }

    /**
     * Delete a course instance
     *
     * @param {string} instanceId - Instance ID to delete
     * @returns {Promise<void>}
     */
    async deleteInstance(instanceId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/instances/${instanceId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete instance');
            }

            return true;
        } catch (error) {
            console.error('Error deleting instance:', error);
            throw error;
        }
    }

    /**
     * Get instances for a specific course
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Array>} Array of instances for the course
     */
    async getInstancesByCourse(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/courses/${courseId}/instances`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load instances for course: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading instances for course:', error);
            throw error;
        }
    }

    /**
     * Enroll student in a course instance
     *
     * @param {string} instanceId - Instance ID
     * @param {string} studentId - Student ID
     * @returns {Promise<Object>} Enrollment confirmation
     */
    async enrollStudentInInstance(instanceId, studentId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/instances/${instanceId}/enroll`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ student_id: studentId })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to enroll student');
            }

            return await response.json();
        } catch (error) {
            console.error('Error enrolling student in instance:', error);
            throw error;
        }
    }

    /**
     * Get enrolled students for an instance
     *
     * @param {string} instanceId - Instance ID
     * @returns {Promise<Array>} Array of enrolled students
     */
    async getInstanceStudents(instanceId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/instances/${instanceId}/students`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load instance students: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading instance students:', error);
            throw error;
        }
    }

    /**
     * Change instance status
     *
     * @param {string} instanceId - Instance ID
     * @param {string} status - New status ('scheduled', 'active', 'completed', 'cancelled')
     * @returns {Promise<Object>} Updated instance
     */
    async updateInstanceStatus(instanceId, status) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/instances/${instanceId}/status`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update instance status');
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating instance status:', error);
            throw error;
        }
    }
}

// Create singleton instance
export const courseInstanceService = new CourseInstanceService();
export default courseInstanceService;
