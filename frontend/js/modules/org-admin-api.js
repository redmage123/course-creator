/**
 * Organization Admin Dashboard - API Service Layer
 *
 * BUSINESS CONTEXT:
 * Centralizes all HTTP API calls to backend microservices, providing a clean
 * abstraction layer for data access. This module handles authentication headers,
 * error handling, and response parsing for all API interactions.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses fetch API with JWT bearer token authentication
 * Handles responses from organization-management (8008), user-management (8001),
 * and other microservices
 *
 * @module org-admin-api
 */

import { showNotification } from './org-admin-utils.js';

/**
 * API Base URLs from environment configuration
 * BUSINESS CONTEXT: Multi-microservice architecture requires different base URLs
 */
const ORG_API_BASE = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || 'https://localhost:8008';
const USER_API_BASE = window.CONFIG?.API_URLS?.USER_MANAGEMENT || 'https://localhost:8000';

// Debug logging for API configuration
console.log('🔧 API Configuration:', {
    hasConfig: !!window.CONFIG,
    USER_API_BASE,
    ORG_API_BASE,
    configApiUrls: window.CONFIG?.API_URLS
});

/**
 * Get authentication headers for API requests
 *
 * BUSINESS CONTEXT:
 * All API requests require JWT bearer token for authentication
 * Headers include authorization and content type
 *
 * @returns {Object} Headers object with Authorization and Content-Type
 *
 * @example
 * const headers = await getAuthHeaders();
 * fetch(url, { headers });
 */
export async function getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// ============================================================================
// ORGANIZATION API
// ============================================================================

/**
 * Fetch organization details by ID
 *
 * BUSINESS CONTEXT:
 * Retrieves comprehensive organization data including member counts,
 * project counts, and contact information
 *
 * @param {string} organizationId - UUID of organization
 * @returns {Promise<Object>} Organization details object
 */
export async function fetchOrganization(organizationId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/organizations/${organizationId}`, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch organization: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching organization:', error);
        showNotification('Failed to load organization details', 'error');
        throw error;
    }
}

/**
 * Update organization details
 *
 * @param {string} organizationId - UUID of organization
 * @param {Object} data - Update data object
 * @returns {Promise<Object>} Updated organization object
 */
export async function updateOrganization(organizationId, data) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/organizations/${organizationId}`, {
            method: 'PUT',
            headers: await getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update organization');
        }

        return await response.json();
    } catch (error) {
        console.error('Error updating organization:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

// ============================================================================
// PROJECTS API
// ============================================================================

/**
 * Fetch all projects for an organization
 *
 * BUSINESS CONTEXT:
 * Projects are the primary learning containers within an organization
 * Used for enrollment, track management, and content organization
 *
 * @param {string} organizationId - UUID of organization
 * @param {Object} filters - Optional filters (status, search)
 * @returns {Promise<Array>} Array of project objects
 */
export async function fetchProjects(organizationId, filters = {}) {
    try {
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.search) params.append('search', filters.search);

        const url = `${ORG_API_BASE}/api/v1/organizations/${organizationId}/projects?${params.toString()}`;

        const response = await fetch(url, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch projects: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching projects:', error);
        showNotification('Failed to load projects', 'error');
        return [];
    }
}

/**
 * Create new project
 *
 * @param {string} organizationId - UUID of organization
 * @param {Object} projectData - Project creation data
 * @returns {Promise<Object>} Created project object
 */
export async function createProject(organizationId, projectData) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/organizations/${organizationId}/projects`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(projectData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create project');
        }

        return await response.json();
    } catch (error) {
        console.error('Error creating project:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

/**
 * Update existing project
 *
 * @param {string} projectId - UUID of project
 * @param {Object} projectData - Updated project data
 * @returns {Promise<Object>} Updated project object
 */
export async function updateProject(projectId, projectData) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/projects/${projectId}`, {
            method: 'PUT',
            headers: await getAuthHeaders(),
            body: JSON.stringify(projectData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update project');
        }

        return await response.json();
    } catch (error) {
        console.error('Error updating project:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

/**
 * Delete project
 *
 * @param {string} projectId - UUID of project
 * @returns {Promise<void>}
 */
export async function deleteProject(projectId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/projects/${projectId}`, {
            method: 'DELETE',
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete project');
        }
    } catch (error) {
        console.error('Error deleting project:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

// ============================================================================
// TRACKS API
// ============================================================================

/**
 * Fetch all tracks with optional filtering
 *
 * BUSINESS CONTEXT:
 * Tracks are structured learning paths within projects
 * Support filtering by project, status, difficulty, and search term
 *
 * @param {Object} filters - Filter parameters (project_id, status, difficulty_level, search)
 * @returns {Promise<Array>} Array of track objects
 */
export async function fetchTracks(filters = {}) {
    try {
        const params = new URLSearchParams();
        if (filters.project_id) params.append('project_id', filters.project_id);
        if (filters.status) params.append('status', filters.status);
        if (filters.difficulty_level) params.append('difficulty_level', filters.difficulty_level);
        if (filters.search) params.append('search', filters.search);

        const url = `${ORG_API_BASE}/api/v1/tracks?${params.toString()}`;

        const response = await fetch(url, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch tracks: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching tracks:', error);
        showNotification('Failed to load tracks', 'error');
        return [];
    }
}

/**
 * Fetch single track details
 *
 * @param {string} trackId - UUID of track
 * @returns {Promise<Object>} Track details object
 */
export async function fetchTrack(trackId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/tracks/${trackId}`, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch track: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching track:', error);
        showNotification('Failed to load track details', 'error');
        throw error;
    }
}

/**
 * Create new track
 *
 * @param {Object} trackData - Track creation data
 * @returns {Promise<Object>} Created track object
 */
export async function createTrack(trackData) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/tracks`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(trackData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create track');
        }

        return await response.json();
    } catch (error) {
        console.error('Error creating track:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

/**
 * Update existing track
 *
 * @param {string} trackId - UUID of track
 * @param {Object} trackData - Updated track data
 * @returns {Promise<Object>} Updated track object
 */
export async function updateTrack(trackId, trackData) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/tracks/${trackId}`, {
            method: 'PUT',
            headers: await getAuthHeaders(),
            body: JSON.stringify(trackData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update track');
        }

        return await response.json();
    } catch (error) {
        console.error('Error updating track:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

/**
 * Delete track
 *
 * @param {string} trackId - UUID of track
 * @returns {Promise<void>}
 */
export async function deleteTrack(trackId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/tracks/${trackId}`, {
            method: 'DELETE',
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete track');
        }
    } catch (error) {
        console.error('Error deleting track:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

// ============================================================================
// MEMBERS API (Instructors & Students)
// ============================================================================

/**
 * Fetch organization members
 *
 * BUSINESS CONTEXT:
 * Members include instructors and students within an organization
 * Supports role-based filtering
 *
 * @param {string} organizationId - UUID of organization
 * @param {Object} filters - Filter parameters (role, search, is_active)
 * @returns {Promise<Array>} Array of member objects
 */
export async function fetchMembers(organizationId, filters = {}) {
    try {
        const params = new URLSearchParams();
        if (filters.role) params.append('role', filters.role);
        if (filters.search) params.append('search', filters.search);
        if (filters.is_active !== undefined) params.append('is_active', filters.is_active);

        const url = `${ORG_API_BASE}/api/v1/organizations/${organizationId}/members?${params.toString()}`;

        const response = await fetch(url, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch members: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching members:', error);
        showNotification('Failed to load members', 'error');
        return [];
    }
}

/**
 * Add instructor to organization
 *
 * @param {string} organizationId - UUID of organization
 * @param {Object} instructorData - Instructor creation data (email, first_name, last_name)
 * @returns {Promise<Object>} Created instructor object
 */
export async function addInstructor(organizationId, instructorData) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/organizations/${organizationId}/instructors`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(instructorData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add instructor');
        }

        return await response.json();
    } catch (error) {
        console.error('Error adding instructor:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

/**
 * Add student to organization
 *
 * @param {string} organizationId - UUID of organization
 * @param {Object} studentData - Student creation data
 * @returns {Promise<Object>} Created student object
 */
export async function addStudent(organizationId, studentData) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/organizations/${organizationId}/students`, {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify(studentData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add student');
        }

        return await response.json();
    } catch (error) {
        console.error('Error adding student:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

/**
 * Remove member from organization
 *
 * @param {string} organizationId - UUID of organization
 * @param {string} userId - UUID of user to remove
 * @returns {Promise<void>}
 */
export async function removeMember(organizationId, userId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/api/v1/organizations/${organizationId}/members/${userId}`, {
            method: 'DELETE',
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to remove member');
        }
    } catch (error) {
        console.error('Error removing member:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}

// ============================================================================
// USER MANAGEMENT API
// ============================================================================

/**
 * Fetch current user profile
 *
 * @returns {Promise<Object>} Current user object
 */
export async function fetchCurrentUser() {
    try {
        const url = `${USER_API_BASE}/users/me`;
        const headers = await getAuthHeaders();

        console.log('🔍 Fetching current user from:', url);
        console.log('🔑 Auth headers:', {
            hasToken: !!headers.Authorization,
            tokenPreview: headers.Authorization ? headers.Authorization.substring(0, 20) + '...' : 'none'
        });

        const response = await fetch(url, { headers });

        console.log('📡 Response status:', response.status, response.statusText);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ API Error:', response.status, errorText);
            throw new Error(`Failed to fetch current user: ${response.status} ${response.statusText}`);
        }

        const userData = await response.json();
        console.log('✅ User data fetched:', userData.email);
        return userData;
    } catch (error) {
        console.error('💥 Error fetching current user:', error);
        throw error;
    }
}

/**
 * Update user profile
 *
 * @param {Object} userData - Updated user data
 * @returns {Promise<Object>} Updated user object
 */
export async function updateUserProfile(userData) {
    try {
        const response = await fetch(`${USER_API_BASE}/api/v1/users/me`, {
            method: 'PUT',
            headers: await getAuthHeaders(),
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update profile');
        }

        return await response.json();
    } catch (error) {
        console.error('Error updating profile:', error);
        showNotification(error.message, 'error');
        throw error;
    }
}
