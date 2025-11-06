/**
 * Tracks CRUD Operations Module
 *
 * BUSINESS CONTEXT:
 * Handles Create, Read, Update, Delete operations for learning tracks in the
 * organization admin dashboard. Tracks are structured learning paths within
 * an organization that define difficulty levels, prerequisites, learning objectives,
 * and estimated duration.
 *
 * DATABASE MAPPING:
 * Maps to course_creator.tracks table with the following schema:
 * - id: uuid (PRIMARY KEY, auto-generated)
 * - organization_id: uuid (NOT NULL, FK to organizations)
 * - name: varchar(255) (NOT NULL)
 * - description: text (NULLABLE)
 * - difficulty_level: varchar(50) (DEFAULT 'intermediate')
 * - estimated_duration_hours: integer (NULLABLE)
 * - prerequisites: jsonb (DEFAULT '[]')
 * - learning_objectives: jsonb (DEFAULT '[]')
 * - is_active: boolean (DEFAULT true)
 * - created_at: timestamp with time zone
 * - updated_at: timestamp with time zone
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only handles track CRUD operations
 * - Open/Closed: Extensible for new operations without modifying existing
 * - Dependency Inversion: Depends on abstractions (state, utils modules)
 *
 * @module tracks-crud
 */

import { closeModal, showNotification } from './utils.js';

/**
 * Get API base URL for organization management service
 *
 * TECHNICAL NOTE:
 * Returns empty string to use relative URLs that go through nginx proxy
 * This avoids CORS issues by keeping requests on the same origin (localhost:3000)
 * Nginx routes /api/v1/tracks/ to organization-management service (port 8008)
 *
 * @returns {string} Empty string for relative URLs through nginx
 */
function getOrgApiBase() {
    return ''; // Use relative URLs through nginx proxy to avoid CORS
}

/**
 * Get authentication token from localStorage
 *
 * @returns {string} JWT authentication token
 */
function getAuthToken() {
    return localStorage.getItem('authToken');
}

/**
 * Get current organization ID from URL or state
 *
 * @returns {string|null} Organization UUID or null
 */
function getCurrentOrgId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('org_id') || localStorage.getItem('currentOrgId');
}

/**
 * Parse JSON array field from textarea
 * Validates and returns parsed array or empty array if invalid
 *
 * @param {string} fieldValue - JSON string from textarea
 * @returns {Array} Parsed array or empty array
 */
function parseJsonArrayField(fieldValue) {
    if (!fieldValue || fieldValue.trim() === '') {
        return [];
    }

    try {
        const parsed = JSON.parse(fieldValue);
        if (Array.isArray(parsed)) {
            return parsed;
        }
        return [];
    } catch (error) {
        console.error('Invalid JSON in field:', error);
        return [];
    }
}

/**
 * Fetch all tracks for the current organization
 *
 * BUSINESS LOGIC:
 * Retrieves all tracks with filtering support
 * Applies organization-level multi-tenancy isolation
 *
 * @returns {Promise<Array>} Array of track objects
 */
export async function fetchTracks() {
    const orgId = getCurrentOrgId();

    if (!orgId) {
        console.error('No organization ID available');
        return [];
    }

    try {
        const response = await fetch(`${getOrgApiBase()}/api/v1/tracks/?organization_id=${orgId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error Response:', errorText);
            throw new Error(`Failed to fetch tracks: ${response.status} ${response.statusText} - ${errorText.substring(0, 200)}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching tracks:', error);
        showNotification(`Failed to load tracks: ${error.message}`, 'error');
        return [];
    }
}

/**
 * Render tracks in table
 *
 * BUSINESS CONTEXT:
 * Displays tracks with name, description, difficulty, duration,
 * active status, and action buttons
 *
 * @param {Array} tracks - Array of track objects
 */
export function renderTracksTable(tracks) {
    const tbody = document.getElementById('tracksTableBody');

    if (!tbody) {
        console.error('Tracks table body not found');
        return;
    }

    if (!tracks || tracks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No tracks found</td></tr>';
        return;
    }

    tbody.innerHTML = tracks.map(track => `
        <tr>
            <td>
                <strong>${escapeHtml(track.name)}</strong>
                ${track.description ? `<br><small style="color: var(--text-muted);">${escapeHtml(track.description.substring(0, 100))}${track.description.length > 100 ? '...' : ''}</small>` : ''}
            </td>
            <td>
                <span class="badge badge-${track.difficulty_level || 'beginner'}">
                    ${capitalizeFirst(track.difficulty_level || 'beginner')}
                </span>
            </td>
            <td>${track.estimated_duration_hours ? `${track.estimated_duration_hours} hours` : 'N/A'}</td>
            <td>
                <span class="status-badge status-${track.is_active ? 'active' : 'inactive'}">
                    ${track.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <button class="btn-icon" onclick="window.editTrack('${track.id}')" title="Edit Track" aria-label="Edit track ${escapeHtml(track.name)}">
                    ✏️
                </button>
                <button class="btn-icon" onclick="window.deleteTrack('${track.id}')" title="Delete Track" aria-label="Delete track ${escapeHtml(track.name)}">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Escape HTML to prevent XSS attacks
 *
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Capitalize first letter of string
 *
 * @param {string} text - Text to capitalize
 * @returns {string} Capitalized text
 */
function capitalizeFirst(text) {
    if (!text) return '';
    return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Load and display tracks data
 *
 * WORKFLOW:
 * 1. Fetch tracks from API
 * 2. Render in table
 * 3. Update statistics
 *
 * @returns {Promise<void>}
 */
export async function loadTracksData() {
    const tracks = await fetchTracks();
    renderTracksTable(tracks);
    updateTracksStats(tracks);
}

/**
 * Update tracks statistics display
 *
 * @param {Array} tracks - Array of track objects
 */
function updateTracksStats(tracks) {
    const totalTracksEl = document.getElementById('totalTracks');
    if (totalTracksEl) {
        totalTracksEl.textContent = tracks.length;
    }
}

/**
 * Show create track modal
 *
 * BUSINESS LOGIC:
 * Opens modal with empty form for creating new track
 * Resets all fields to default values
 */
export function showCreateTrackModal() {
    const modal = document.getElementById('createTrackModal');
    const form = document.getElementById('createTrackForm');

    if (!modal || !form) {
        console.error('Create track modal or form not found');
        return;
    }

    // Reset form
    form.reset();

    // Set default values for JSONB fields
    document.getElementById('trackPrerequisites').value = '[]';
    document.getElementById('trackLearningObjectives').value = '[]';
    document.getElementById('trackIsActive').checked = true;

    // Show modal
    modal.style.display = 'block';
}

/**
 * Submit create track form
 *
 * BUSINESS LOGIC:
 * Validates form data and creates new track via API
 * Closes modal and refreshes table on success
 *
 * VALIDATION:
 * - Track name is required
 * - JSON fields must be valid JSON arrays
 * - Duration must be positive integer
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function submitCreateTrack(event) {
    event.preventDefault();

    const orgId = getCurrentOrgId();
    if (!orgId) {
        showNotification('No organization selected', 'error');
        return;
    }

    try {
        // Gather form data
        const formData = {
            organization_id: orgId,
            name: document.getElementById('trackName').value.trim(),
            description: document.getElementById('trackDescription').value.trim() || null,
            difficulty_level: document.getElementById('trackDifficultyLevel').value,
            estimated_duration_hours: parseInt(document.getElementById('trackDurationHours').value) || null,
            prerequisites: parseJsonArrayField(document.getElementById('trackPrerequisites').value),
            learning_objectives: parseJsonArrayField(document.getElementById('trackLearningObjectives').value),
            is_active: document.getElementById('trackIsActive').checked
        };

        // Validate required fields
        if (!formData.name) {
            showNotification('Track name is required', 'error');
            return;
        }

        // Validate duration if provided
        if (formData.estimated_duration_hours !== null && formData.estimated_duration_hours <= 0) {
            showNotification('Duration must be a positive number', 'error');
            return;
        }

        // Submit to API
        const response = await fetch(`${getOrgApiBase()}/api/v1/tracks/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create track');
        }

        showNotification('Track created successfully', 'success');
        closeModal('createTrackModal');
        loadTracksData();

    } catch (error) {
        console.error('Error creating track:', error);
        showNotification(`Failed to create track: ${error.message}`, 'error');
    }
}

/**
 * Edit track
 *
 * BUSINESS LOGIC:
 * Fetches track data from API and populates edit form
 * Opens edit modal with pre-filled data
 *
 * @param {string} trackId - UUID of track to edit
 * @returns {Promise<void>}
 */
export async function editTrack(trackId) {
    if (!trackId) {
        console.error('No track ID provided');
        return;
    }

    try {
        // Fetch track data
        const response = await fetch(`${getOrgApiBase()}/api/v1/tracks/${trackId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch track');
        }

        const track = await response.json();

        // Populate form fields
        document.getElementById('editTrackId').value = track.id;
        document.getElementById('editTrackName').value = track.name;
        document.getElementById('editTrackDescription').value = track.description || '';
        document.getElementById('editTrackDifficultyLevel').value = track.difficulty_level || 'intermediate';
        document.getElementById('editTrackDurationHours').value = track.estimated_duration_hours || '';

        // Populate JSONB fields as JSON strings
        document.getElementById('editTrackPrerequisites').value = JSON.stringify(track.prerequisites || [], null, 2);
        document.getElementById('editTrackLearningObjectives').value = JSON.stringify(track.learning_objectives || [], null, 2);

        document.getElementById('editTrackIsActive').checked = track.is_active !== false;

        // Show modal
        document.getElementById('editTrackModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading track for edit:', error);
        showNotification('Failed to load track', 'error');
    }
}

/**
 * Submit edit track form
 *
 * BUSINESS LOGIC:
 * Validates form data and updates track via API
 * Closes modal and refreshes table on success
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function submitEditTrack(event) {
    event.preventDefault();

    const trackId = document.getElementById('editTrackId').value;

    if (!trackId) {
        showNotification('No track ID found', 'error');
        return;
    }

    try {
        // Gather form data
        const formData = {
            name: document.getElementById('editTrackName').value.trim(),
            description: document.getElementById('editTrackDescription').value.trim() || null,
            difficulty_level: document.getElementById('editTrackDifficultyLevel').value,
            estimated_duration_hours: parseInt(document.getElementById('editTrackDurationHours').value) || null,
            prerequisites: parseJsonArrayField(document.getElementById('editTrackPrerequisites').value),
            learning_objectives: parseJsonArrayField(document.getElementById('editTrackLearningObjectives').value),
            is_active: document.getElementById('editTrackIsActive').checked
        };

        // Validate required fields
        if (!formData.name) {
            showNotification('Track name is required', 'error');
            return;
        }

        // Submit to API
        const response = await fetch(`${getOrgApiBase()}/api/v1/tracks/${trackId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update track');
        }

        showNotification('Track updated successfully', 'success');
        closeModal('editTrackModal');
        loadTracksData();

    } catch (error) {
        console.error('Error updating track:', error);
        showNotification(`Failed to update track: ${error.message}`, 'error');
    }
}

/**
 * Show delete track confirmation modal
 *
 * BUSINESS CONTEXT:
 * Prevents accidental deletion by requiring confirmation
 * Displays warning about cascade effects
 *
 * @param {string} trackId - UUID of track to delete
 */
export function deleteTrack(trackId) {
    if (!trackId) {
        console.error('No track ID provided');
        return;
    }

    // Store track ID for confirmation
    document.getElementById('deleteTrackId').value = trackId;

    // Show warning
    const warning = document.getElementById('deleteTrackWarning');
    if (warning) {
        warning.textContent = 'This action cannot be undone. All associated enrollments will be removed.';
    }

    // Show modal
    document.getElementById('deleteTrackModal').style.display = 'block';
}

/**
 * Confirm and execute track deletion
 *
 * BUSINESS LOGIC:
 * Deletes track after user confirmation
 * Cascade deletes related enrollments (via FK constraint)
 * Refreshes table on success
 *
 * @returns {Promise<void>}
 */
export async function confirmDeleteTrack() {
    const trackId = document.getElementById('deleteTrackId').value;

    if (!trackId) {
        showNotification('No track ID found', 'error');
        return;
    }

    try {
        const response = await fetch(`${getOrgApiBase()}/api/v1/tracks/${trackId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete track');
        }

        showNotification('Track deleted successfully', 'success');
        closeModal('deleteTrackModal');
        loadTracksData();

    } catch (error) {
        console.error('Error deleting track:', error);
        showNotification(`Failed to delete track: ${error.message}`, 'error');
    }
}

// Wire up form submission handlers using data-attributes (Separation of Concerns)
document.addEventListener('DOMContentLoaded', () => {
    // Create track form
    const createForm = document.getElementById('createTrackForm');
    if (createForm) {
        createForm.addEventListener('submit', submitCreateTrack);
    }

    // Edit track form
    const editForm = document.getElementById('editTrackForm');
    if (editForm) {
        editForm.addEventListener('submit', submitEditTrack);
    }

    // Modal close buttons with data-dismiss attribute
    document.querySelectorAll('[data-dismiss="modal"]').forEach(button => {
        button.addEventListener('click', (event) => {
            const modalId = event.target.getAttribute('data-modal-id');
            if (modalId) {
                closeModal(modalId);
            }
        });
    });

    // Delete confirmation button with data-action attribute
    const confirmDeleteBtn = document.getElementById('confirmDeleteTrackBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', confirmDeleteTrack);
    }
});

// Export functions to window for onclick handlers
window.showCreateTrackModal = showCreateTrackModal;
window.editTrack = editTrack;
window.deleteTrack = deleteTrack;
window.confirmDeleteTrack = confirmDeleteTrack;
window.loadTracksData = loadTracksData;
