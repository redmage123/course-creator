/**
 * Organization Admin Dashboard - API Client Module
 *
 * BUSINESS CONTEXT:
 * Centralized API client for all organization admin operations including organization management,
 * project lifecycle management, instructor assignments, student enrollments, track management,
 * and analytics. This module serves as the single source of truth for all backend API interactions.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Each function handles exactly one API operation
 * - Open/Closed: New API endpoints can be added without modifying existing functions
 * - Dependency Inversion: Depends on abstractions (ORG_API_BASE) rather than concrete implementations
 * - Interface Segregation: Functions are grouped by domain for easy navigation
 *
 * ARCHITECTURE:
 * Extracted from monolithic org-admin-dashboard.js (3,273 lines) to improve:
 * - Testability: Each API function can be unit tested in isolation
 * - Maintainability: Clear separation between API calls and UI logic
 * - Reusability: API functions can be imported and used across multiple modules
 * - Error Handling: Centralized error handling patterns for all API operations
 */

import { ORG_API_BASE } from './state.js';
import { Auth } from '../auth.js';

// =============================================================================
// ORGANIZATION OPERATIONS
// =============================================================================

/**
 * Load organization data by ID
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Object>} Organization data
 * @throws {Error} If API request fails
 */
export async function loadOrganizationData(orgId) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load organization data');
    }

    return await response.json();
}

/**
 * Update organization settings
 *
 * @param {string} orgId - Organization ID
 * @param {Object} settingsData - Organization settings to update
 * @returns {Promise<Object>} Updated organization data
 * @throws {Error} If API request fails
 */
export async function updateOrganizationSettings(orgId, settingsData) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settingsData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update organization information');
    }

    return await response.json();
}

/**
 * Get organization statistics
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Object>} Organization statistics
 */
export async function getOrganizationStats(orgId) {
    // Note: This currently returns mock data as the endpoint is not yet implemented
    return {
        active_projects: 3,
        instructors: 2,
        total_students: 3,
        courses: 24
    };
}

// =============================================================================
// PROJECT OPERATIONS
// =============================================================================

/**
 * Load all projects for an organization
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Array>} Array of project objects
 * @throws {Error} If API request fails
 */
export async function loadProjectsData(orgId) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/projects`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load projects');
    }

    return await response.json();
}

/**
 * Create a new project
 *
 * @param {string} orgId - Organization ID
 * @param {Object} projectData - Project data to create
 * @returns {Promise<Object>} Created project object
 * @throws {Error} If API request fails
 */
export async function createProject(orgId, projectData) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/projects`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(projectData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create project');
    }

    return await response.json();
}

/**
 * Activate a project
 *
 * @param {string} projectId - Project ID
 * @returns {Promise<Object>} Activation result
 * @throws {Error} If API request fails
 */
export async function activateProject(projectId) {
    const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/activate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to activate project');
    }

    return await response.json();
}

/**
 * Delete a project
 *
 * @param {string} projectId - Project ID
 * @returns {Promise<void>}
 * @throws {Error} If API request fails
 */
export async function deleteProject(projectId) {
    const response = await fetch(`${ORG_API_BASE}/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete project');
    }
}

/**
 * Instantiate a project (create default tracks and modules)
 *
 * @param {string} projectId - Project ID
 * @param {Object} options - Instantiation options
 * @returns {Promise<Object>} Instantiation result
 * @throws {Error} If API request fails
 */
export async function instantiateProject(projectId, options) {
    const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/instantiate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(options)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to instantiate project');
    }

    return await response.json();
}

// =============================================================================
// INSTRUCTOR OPERATIONS
// =============================================================================

/**
 * Load all instructors for an organization
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Array>} Array of instructor objects
 * @throws {Error} If API request fails
 */
export async function loadInstructorsData(orgId) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load instructors');
    }

    return await response.json();
}

/**
 * Add a new instructor to an organization
 *
 * @param {string} orgId - Organization ID
 * @param {Object} instructorData - Instructor data to create
 * @returns {Promise<Object>} Created instructor object
 * @throws {Error} If API request fails
 */
export async function addInstructor(orgId, instructorData) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(instructorData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add instructor');
    }

    return await response.json();
}

/**
 * Remove an instructor from an organization
 *
 * @param {string} orgId - Organization ID
 * @param {string} instructorId - Instructor user ID
 * @returns {Promise<void>}
 * @throws {Error} If API request fails
 */
export async function removeInstructor(orgId, instructorId) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors/${instructorId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`
        }
    });

    if (!response.ok) {
        throw new Error('Failed to remove instructor');
    }
}

/**
 * Load available instructors for assignment
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Array>} Array of available instructor objects
 * @throws {Error} If API request fails
 */
export async function loadAvailableInstructors(orgId) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load available instructors');
    }

    return await response.json();
}

/**
 * Load assigned instructors for a project
 *
 * @param {string} projectId - Project ID
 * @returns {Promise<Array>} Array of assigned instructor objects
 * @throws {Error} If API request fails
 */
export async function loadAssignedInstructorsForProject(projectId) {
    const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/assigned-instructors`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load assigned instructors');
    }

    return await response.json();
}

/**
 * Save instructor assignments for a project
 *
 * @param {string} projectId - Project ID
 * @param {Object} assignments - Instructor assignment data
 * @returns {Promise<Object>} Assignment result
 * @throws {Error} If API request fails
 */
export async function saveInstructorAssignments(projectId, assignments) {
    const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/instructor-assignments`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(assignments)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save instructor assignments');
    }

    return await response.json();
}

/**
 * Remove instructors from a project
 *
 * @param {string} endpoint - API endpoint for removal
 * @param {Object} removalData - Removal options
 * @returns {Promise<Object>} Removal result
 * @throws {Error} If API request fails
 */
export async function removeInstructorsFromProject(endpoint, removalData) {
    const response = await fetch(endpoint, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(removalData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to remove instructor');
    }

    return await response.json();
}

// =============================================================================
// STUDENT OPERATIONS
// =============================================================================

/**
 * Load all students for an organization
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Array>} Array of student objects
 * @throws {Error} If API request fails
 */
export async function loadStudentsData(orgId) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/students`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load students');
    }

    return await response.json();
}

/**
 * Add a new student to an organization
 *
 * @param {string} orgId - Organization ID
 * @param {Object} studentData - Student data to create
 * @returns {Promise<Object>} Created student object
 * @throws {Error} If API request fails
 */
export async function addStudent(orgId, studentData) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/students`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(studentData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add student');
    }

    return await response.json();
}

/**
 * Load available students for enrollment
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Array>} Array of available student objects
 * @throws {Error} If API request fails
 */
export async function loadAvailableStudents(orgId) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/students`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load available students');
    }

    return await response.json();
}

/**
 * Load enrolled students for a project
 *
 * @param {string} projectId - Project ID
 * @returns {Promise<Array>} Array of enrolled student objects
 * @throws {Error} If API request fails
 */
export async function loadEnrolledStudentsForProject(projectId) {
    const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/enrolled-students`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load enrolled students');
    }

    return await response.json();
}

/**
 * Enroll students in a project track
 *
 * @param {string} projectId - Project ID
 * @param {Object} enrollmentData - Enrollment data (track_id, student_ids)
 * @returns {Promise<Object>} Enrollment result
 * @throws {Error} If API request fails
 */
export async function enrollStudents(projectId, enrollmentData) {
    const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/enroll-students`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(enrollmentData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to enroll students');
    }

    return await response.json();
}

/**
 * Unenroll a student from a project or track
 *
 * @param {string} endpoint - API endpoint for unenrollment
 * @param {Object} unenrollmentData - Unenrollment options
 * @returns {Promise<Object>} Unenrollment result
 * @throws {Error} If API request fails
 */
export async function unenrollStudent(endpoint, unenrollmentData) {
    const response = await fetch(endpoint, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(unenrollmentData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to unenroll student');
    }

    return await response.json();
}

// =============================================================================
// TRACK OPERATIONS
// =============================================================================

/**
 * Load tracks data with optional filters
 *
 * @param {Object} filters - Filter parameters (project_id, status, difficulty_level, search)
 * @returns {Promise<Array>} Array of track objects
 * @throws {Error} If API request fails
 */
export async function loadTracksData(filters = {}) {
    const params = new URLSearchParams();

    if (filters.projectId) params.append('project_id', filters.projectId);
    if (filters.status) params.append('status', filters.status);
    if (filters.difficulty) params.append('difficulty_level', filters.difficulty);
    if (filters.search) params.append('search', filters.search);

    const url = `${ORG_API_BASE}/tracks?${params.toString()}`;

    const response = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load tracks');
    }

    return await response.json();
}

/**
 * Get track details by ID
 *
 * @param {string} trackId - Track ID
 * @returns {Promise<Object>} Track object
 * @throws {Error} If API request fails
 */
export async function getTrackDetails(trackId) {
    const response = await fetch(`${ORG_API_BASE}/tracks/${trackId}`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load track details');
    }

    return await response.json();
}

/**
 * Create a new track
 *
 * @param {Object} trackData - Track data to create
 * @returns {Promise<Object>} Created track object
 * @throws {Error} If API request fails
 */
export async function createTrack(trackData) {
    const response = await fetch(`${ORG_API_BASE}/tracks`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(trackData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create track');
    }

    return await response.json();
}

/**
 * Update an existing track
 *
 * @param {string} trackId - Track ID
 * @param {Object} trackData - Track data to update
 * @returns {Promise<Object>} Updated track object
 * @throws {Error} If API request fails
 */
export async function updateTrack(trackId, trackData) {
    const response = await fetch(`${ORG_API_BASE}/tracks/${trackId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(trackData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update track');
    }

    return await response.json();
}

/**
 * Delete a track
 *
 * @param {string} trackId - Track ID
 * @returns {Promise<void>}
 * @throws {Error} If API request fails
 */
export async function deleteTrack(trackId) {
    const response = await fetch(`${ORG_API_BASE}/tracks/${trackId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete track');
    }
}

/**
 * Load track templates for an organization
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Array>} Array of track template objects
 * @throws {Error} If API request fails
 */
export async function loadTrackTemplates(orgId) {
    const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/track-templates`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load track templates');
    }

    return await response.json();
}

// =============================================================================
// ANALYTICS OPERATIONS
// =============================================================================

/**
 * Load analytics data for a project
 *
 * @param {string} projectId - Project ID
 * @returns {Promise<Object>} Project analytics data
 * @throws {Error} If API request fails
 */
export async function loadProjectAnalytics(projectId) {
    const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/analytics`, {
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load project analytics');
    }

    return await response.json();
}

/**
 * Get recent projects (for overview dashboard)
 *
 * @param {string} orgId - Organization ID
 * @param {number} limit - Number of projects to return
 * @returns {Promise<Array>} Array of recent project objects
 */
export async function getRecentProjects(orgId, limit = 3) {
    // Note: This should be enhanced with actual API endpoint when available
    const projects = await loadProjectsData(orgId);
    return projects.slice(0, limit);
}

/**
 * Get recent activity (for overview dashboard)
 *
 * @param {string} orgId - Organization ID
 * @returns {Promise<Array>} Array of recent activity objects
 */
export async function getRecentActivity(orgId) {
    // Note: This currently returns mock data as the endpoint is not yet implemented
    return [
        { action: 'New instructor added', user: 'John Doe', time: '2 hours ago' },
        { action: 'Project "BA Bootcamp" created', user: 'Jane Smith', time: '1 day ago' },
        { action: '15 students enrolled', user: 'System', time: '2 days ago' }
    ];
}

// =============================================================================
// RAG (AI ENHANCEMENT) OPERATIONS
// =============================================================================

/**
 * Query RAG service for project planning suggestions
 *
 * @param {Object} queryData - RAG query data
 * @returns {Promise<Object>} RAG suggestions
 * @throws {Error} If API request fails
 */
export async function generateRAGSuggestions(queryData) {
    const response = await fetch(`${window.CONFIG?.API_URLS.RAG}/api/v1/rag/query`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(queryData)
    });

    if (!response.ok) {
        throw new Error('Failed to generate RAG suggestions');
    }

    return await response.json();
}

// =============================================================================
// FILE UPLOAD OPERATIONS
// =============================================================================

/**
 * Upload organization logo file
 *
 * @param {File} file - Logo file to upload
 * @param {string} orgId - Organization ID
 * @returns {Promise<string>} Uploaded file URL
 * @throws {Error} If upload fails
 */
export async function uploadLogoFile(file, orgId) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', 'organization_logo');
    formData.append('organization_id', orgId);

    const response = await fetch(`${window.CONFIG?.API_URLS.CONTENT_MANAGEMENT}/api/v1/files/upload`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Auth.getToken()}`
        },
        body: formData
    });

    if (!response.ok) {
        throw new Error('Upload failed');
    }

    const result = await response.json();
    return result.file_url || result.url;
}
