/**
 * Student Service - Single Responsibility for Student Operations
 *
 * BUSINESS CONTEXT:
 * Handles all student-related CRUD operations and enrollment management
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only manages student operations
 * - Open/Closed: Extensible for new student features without modification
 * - Dependency Inversion: Depends on Auth abstraction, not concrete implementation
 *
 * TECHNICAL IMPLEMENTATION:
 * - Async/await for all API calls
 * - Centralized error handling
 * - Authentication integration
 * - Configuration-based endpoints
 */

import { Auth } from '../modules/auth.js';

export class StudentService {
    constructor() {
        this.baseUrl = window.CONFIG?.API_URLS?.USER_MANAGEMENT || 'https://localhost:8000';
    }

    /**
     * Load all students for the current instructor
     *
     * @returns {Promise<Array>} Array of student objects
     */
    async loadStudents() {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.baseUrl}/users?role=student&organization_id=${currentUser.organization_id}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load students: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading students:', error);
            throw error;
        }
    }

    /**
     * Add a new student to the system
     *
     * @param {Object} studentData - Student data object
     * @returns {Promise<Object>} Created student object
     */
    async addStudent(studentData) {
        try {
            const authToken = localStorage.getItem('authToken');
            const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

            const response = await fetch(`${this.baseUrl}/users`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...studentData,
                    role: 'student',
                    organization_id: currentUser.organization_id
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to add student');
            }

            return await response.json();
        } catch (error) {
            console.error('Error adding student:', error);
            throw error;
        }
    }

    /**
     * Remove a student from the system
     *
     * @param {string} studentId - Student ID to remove
     * @returns {Promise<void>}
     */
    async removeStudent(studentId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/users/${studentId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to remove student');
            }

            return true;
        } catch (error) {
            console.error('Error removing student:', error);
            throw error;
        }
    }

    /**
     * Get a single student by ID
     *
     * @param {string} studentId - Student ID
     * @returns {Promise<Object>} Student object
     */
    async getStudent(studentId) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/users/${studentId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load student: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading student:', error);
            throw error;
        }
    }

    /**
     * Update student information
     *
     * @param {string} studentId - Student ID
     * @param {Object} studentData - Updated student data
     * @returns {Promise<Object>} Updated student object
     */
    async updateStudent(studentId, studentData) {
        try {
            const authToken = localStorage.getItem('authToken');

            const response = await fetch(`${this.baseUrl}/users/${studentId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(studentData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update student');
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating student:', error);
            throw error;
        }
    }

    /**
     * Get student progress for a specific course
     *
     * @param {string} studentId - Student ID
     * @param {string} courseId - Course ID
     * @returns {Promise<Object>} Student progress object
     */
    async getStudentProgress(studentId, courseId) {
        try {
            const authToken = localStorage.getItem('authToken');
            const analyticsUrl = window.CONFIG?.API_URLS?.ANALYTICS || 'https://localhost:8008';

            const response = await fetch(`${analyticsUrl}/analytics/student/${studentId}/course/${courseId}/progress`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load student progress: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading student progress:', error);
            throw error;
        }
    }

    /**
     * Enroll a student in a course instance
     *
     * @param {string} studentId - Student ID
     * @param {string} instanceId - Course instance ID
     * @returns {Promise<Object>} Enrollment confirmation
     */
    async enrollStudent(studentId, instanceId) {
        try {
            const authToken = localStorage.getItem('authToken');
            const courseUrl = window.CONFIG?.API_URLS?.COURSE_MANAGEMENT || 'https://localhost:8004';

            const response = await fetch(`${courseUrl}/instances/${instanceId}/enroll`, {
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
            console.error('Error enrolling student:', error);
            throw error;
        }
    }

    /**
     * Enroll a student by email in a course
     *
     * @param {string} email - Student email
     * @param {number} courseId - Course ID
     * @returns {Promise<Object>} Enrollment confirmation
     */
    async enrollStudentByEmail(email, courseId) {
        try {
            const authToken = localStorage.getItem('authToken');
            const courseUrl = window.CONFIG?.API_URLS?.COURSE_MANAGEMENT || 'https://localhost:8004';

            const response = await fetch(`${courseUrl}/enrollments`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    course_id: courseId,
                    student_email: email
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Enrollment failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Error enrolling student by email:', error);
            throw error;
        }
    }

    /**
     * Load students enrolled in a specific course
     *
     * @param {string} courseId - Course ID
     * @returns {Promise<Array>} Array of enrolled students
     */
    async getStudentsByCourse(courseId) {
        try {
            const authToken = localStorage.getItem('authToken');
            const courseUrl = window.CONFIG?.API_URLS?.COURSE_MANAGEMENT || 'https://localhost:8004';

            const response = await fetch(`${courseUrl}/courses/${courseId}/students`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load students for course: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error loading students for course:', error);
            throw error;
        }
    }
}

// Create singleton instance
export const studentService = new StudentService();
export default studentService;
