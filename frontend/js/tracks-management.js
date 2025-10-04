/**
 * Tracks Management Module
 *
 * BUSINESS CONTEXT:
 * Manages learning tracks within the organization admin dashboard.
 * Tracks are structured learning paths within projects that students
 * can enroll in and instructors can manage.
 *
 * TECHNICAL IMPLEMENTATION:
 * - CRUD operations for tracks
 * - Integration with organization-management API (port 8008)
 * - Filtering and search functionality
 * - Modal-based UI for create/edit/view
 *
 * API ENDPOINTS:
 * - GET /api/v1/tracks - List all tracks
 * - POST /api/v1/tracks - Create track
 * - GET /api/v1/tracks/{id} - Get track details
 * - PUT /api/v1/tracks/{id} - Update track
 * - DELETE /api/v1/tracks/{id} - Delete track
 */

import { getAuthHeaders, showNotification } from './config-global.js';

// API Configuration
const ORGANIZATION_API = window.ENV?.API_URLS?.ORGANIZATION_MANAGEMENT || 'https://localhost:8008';
const API_BASE = `${ORGANIZATION_API}/api/v1`;

// Current organization ID (loaded on page init)
let currentOrganizationId = null;

/**
 * Initialize tracks management
 * Called when organization dashboard loads
 */
export async function initializeTracksManagement(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Tracks management initialized for organization:', organizationId);
}

/**
 * Load tracks data for the tracks tab
 *
 * BUSINESS LOGIC:
 * Fetches tracks based on filters (project, status, difficulty, search)
 * and populates the tracks table
 */
export async function loadTracksData() {
    try {
        // Get filter values
        const projectId = document.getElementById('trackProjectFilter')?.value || '';
        const status = document.getElementById('trackStatusFilter')?.value || '';
        const difficulty = document.getElementById('trackDifficultyFilter')?.value || '';
        const searchTerm = document.getElementById('trackSearchInput')?.value || '';

        // Build query parameters
        const params = new URLSearchParams();
        if (projectId) params.append('project_id', projectId);
        if (status) params.append('status', status);
        if (difficulty) params.append('difficulty_level', difficulty);
        if (searchTerm) params.append('search', searchTerm);

        const url = `${API_BASE}/tracks?${params.toString()}`;

        const response = await fetch(url, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Failed to load tracks: ${response.statusText}`);
        }

        const tracks = await response.json();

        // Update UI
        renderTracksTable(tracks);
        updateTracksStats(tracks);

    } catch (error) {
        console.error('Error loading tracks:', error);
        showNotification('Failed to load tracks', 'error');
    }
}

/**
 * Render tracks in the table
 */
function renderTracksTable(tracks) {
    const tbody = document.getElementById('tracksTableBody');

    if (!tbody) return;

    if (!tracks || tracks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No tracks found</td></tr>';
        return;
    }

    tbody.innerHTML = tracks.map(track => `
        <tr>
            <td>
                <strong>${escapeHtml(track.name)}</strong>
                ${track.description ? `<br><small style="color: var(--text-muted);">${escapeHtml(track.description.substring(0, 100))}${track.description.length > 100 ? '...' : ''}</small>` : ''}
            </td>
            <td>${escapeHtml(track.project_name || 'N/A')}</td>
            <td>
                <span class="badge badge-${track.difficulty_level || 'beginner'}">
                    ${capitalizeFirst(track.difficulty_level || 'beginner')}
                </span>
            </td>
            <td>${track.duration_weeks ? `${track.duration_weeks} weeks` : 'N/A'}</td>
            <td>
                <span class="stat-badge">${track.enrollment_count || 0}</span>
                ${track.max_students ? `<small>/ ${track.max_students}</small>` : ''}
            </td>
            <td><span class="stat-badge">${track.instructor_count || 0}</span></td>
            <td>
                <span class="status-badge status-${track.status || 'draft'}">
                    ${capitalizeFirst(track.status || 'draft')}
                </span>
            </td>
            <td>
                <button class="btn-icon" onclick="viewTrackDetails('${track.id}')" title="View Details">
                    👁️
                </button>
                <button class="btn-icon" onclick="editTrack('${track.id}')" title="Edit">
                    ✏️
                </button>
                <button class="btn-icon" onclick="deleteTrack('${track.id}')" title="Delete">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Update tracks statistics in overview
 */
function updateTracksStats(tracks) {
    const totalTracksEl = document.getElementById('totalTracks');
    if (totalTracksEl) {
        totalTracksEl.textContent = tracks.length;
    }
}

/**
 * Show create track modal
 */
export function showCreateTrackModal() {
    const modal = document.getElementById('trackModal');
    const form = document.getElementById('trackForm');
    const title = document.getElementById('trackModalTitle');
    const submitBtn = document.getElementById('trackSubmitBtn');

    if (!modal || !form) return;

    // Reset form
    form.reset();
    document.getElementById('trackId').value = '';

    // Set modal title and button
    title.textContent = 'Create New Track';
    submitBtn.textContent = 'Create Track';

    // Load projects for the dropdown
    loadProjectsForTrackForm();

    // Show modal
    modal.style.display = 'block';
}

/**
 * Load projects for track form dropdown
 */
async function loadProjectsForTrackForm() {
    try {
        const response = await fetch(`${API_BASE}/organizations/${currentOrganizationId}/projects`, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to load projects');
        }

        const projects = await response.json();
        const select = document.getElementById('trackProject');

        if (select) {
            select.innerHTML = '<option value="">Select Project</option>' +
                projects.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
        }

        // Also update filter dropdown
        const filterSelect = document.getElementById('trackProjectFilter');
        if (filterSelect) {
            filterSelect.innerHTML = '<option value="">All Projects</option>' +
                projects.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
        }

    } catch (error) {
        console.error('Error loading projects:', error);
        showNotification('Failed to load projects', 'error');
    }
}

/**
 * Submit track form (create or update)
 */
export async function submitTrack(event) {
    event.preventDefault();

    const form = event.target;
    const trackId = document.getElementById('trackId').value;
    const isUpdate = trackId !== '';

    try {
        // Gather form data
        const formData = {
            name: document.getElementById('trackName').value,
            description: document.getElementById('trackDescription').value || null,
            project_id: document.getElementById('trackProject').value,
            difficulty_level: document.getElementById('trackDifficulty').value,
            duration_weeks: parseInt(document.getElementById('trackDuration').value) || null,
            max_students: parseInt(document.getElementById('trackMaxStudents').value) || null,
            target_audience: parseCommaSeparated(document.getElementById('trackAudience').value),
            prerequisites: parseCommaSeparated(document.getElementById('trackPrerequisites').value),
            learning_objectives: parseCommaSeparated(document.getElementById('trackObjectives').value)
        };

        const url = isUpdate ? `${API_BASE}/tracks/${trackId}` : `${API_BASE}/tracks`;
        const method = isUpdate ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: {
                ...await getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save track');
        }

        const track = await response.json();

        showNotification(`Track ${isUpdate ? 'updated' : 'created'} successfully`, 'success');
        closeModal('trackModal');
        loadTracksData();

    } catch (error) {
        console.error('Error saving track:', error);
        showNotification(error.message, 'error');
    }
}

/**
 * View track details
 */
export async function viewTrackDetails(trackId) {
    try {
        const response = await fetch(`${API_BASE}/tracks/${trackId}`, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to load track details');
        }

        const track = await response.json();

        // Populate details modal
        const content = document.getElementById('trackDetailsContent');
        if (content) {
            content.innerHTML = `
                <div style="display: grid; gap: 1.5rem;">
                    <div>
                        <h3>${escapeHtml(track.name)}</h3>
                        <p>${escapeHtml(track.description || 'No description provided')}</p>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <strong>Project:</strong> ${escapeHtml(track.project_name || 'N/A')}
                        </div>
                        <div>
                            <strong>Status:</strong>
                            <span class="status-badge status-${track.status}">${capitalizeFirst(track.status)}</span>
                        </div>
                        <div>
                            <strong>Difficulty:</strong>
                            <span class="badge badge-${track.difficulty_level}">${capitalizeFirst(track.difficulty_level)}</span>
                        </div>
                        <div>
                            <strong>Duration:</strong> ${track.duration_weeks ? `${track.duration_weeks} weeks` : 'N/A'}
                        </div>
                        <div>
                            <strong>Students:</strong> ${track.enrollment_count || 0}${track.max_students ? ` / ${track.max_students}` : ''}
                        </div>
                        <div>
                            <strong>Instructors:</strong> ${track.instructor_count || 0}
                        </div>
                    </div>

                    ${track.target_audience && track.target_audience.length > 0 ? `
                        <div>
                            <strong>Target Audience:</strong>
                            <ul>
                                ${track.target_audience.map(a => `<li>${escapeHtml(a)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    ${track.prerequisites && track.prerequisites.length > 0 ? `
                        <div>
                            <strong>Prerequisites:</strong>
                            <ul>
                                ${track.prerequisites.map(p => `<li>${escapeHtml(p)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    ${track.learning_objectives && track.learning_objectives.length > 0 ? `
                        <div>
                            <strong>Learning Objectives:</strong>
                            <ul>
                                ${track.learning_objectives.map(o => `<li>${escapeHtml(o)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    <div style="font-size: 0.9rem; color: var(--text-muted);">
                        <div>Created: ${new Date(track.created_at).toLocaleString()}</div>
                        <div>Last Updated: ${new Date(track.updated_at).toLocaleString()}</div>
                    </div>
                </div>
            `;
        }

        // Store track ID for edit action
        document.getElementById('trackDetailsModal').dataset.trackId = trackId;

        // Show modal
        openModal('trackDetailsModal');

    } catch (error) {
        console.error('Error loading track details:', error);
        showNotification('Failed to load track details', 'error');
    }
}

/**
 * Edit track (from details modal)
 */
export function editTrackFromDetails() {
    const trackId = document.getElementById('trackDetailsModal').dataset.trackId;
    if (trackId) {
        closeModal('trackDetailsModal');
        editTrack(trackId);
    }
}

/**
 * Edit track
 */
export async function editTrack(trackId) {
    try {
        // Fetch track details
        const response = await fetch(`${API_BASE}/tracks/${trackId}`, {
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to load track details');
        }

        const track = await response.json();

        // Populate form
        document.getElementById('trackId').value = track.id;
        document.getElementById('trackName').value = track.name;
        document.getElementById('trackDescription').value = track.description || '';
        document.getElementById('trackProject').value = track.project_id;
        document.getElementById('trackDifficulty').value = track.difficulty_level;
        document.getElementById('trackDuration').value = track.duration_weeks || '';
        document.getElementById('trackMaxStudents').value = track.max_students || '';
        document.getElementById('trackAudience').value = (track.target_audience || []).join(', ');
        document.getElementById('trackPrerequisites').value = (track.prerequisites || []).join(', ');
        document.getElementById('trackObjectives').value = (track.learning_objectives || []).join(', ');

        // Update modal title and button
        document.getElementById('trackModalTitle').textContent = 'Edit Track';
        document.getElementById('trackSubmitBtn').textContent = 'Update Track';

        // Load projects
        await loadProjectsForTrackForm();

        // Show modal
        openModal('trackModal');

    } catch (error) {
        console.error('Error loading track for edit:', error);
        showNotification('Failed to load track', 'error');
    }
}

/**
 * Delete track
 */
export function deleteTrack(trackId) {
    // Store track ID
    document.getElementById('deleteTrackId').value = trackId;

    // Show warning
    const warning = document.getElementById('deleteTrackWarning');
    if (warning) {
        warning.textContent = 'This action cannot be undone. All enrollments will be removed.';
    }

    // Show modal
    openModal('deleteTrackModal');
}

/**
 * Confirm track deletion
 */
export async function confirmDeleteTrack() {
    const trackId = document.getElementById('deleteTrackId').value;

    if (!trackId) return;

    try {
        const response = await fetch(`${API_BASE}/tracks/${trackId}`, {
            method: 'DELETE',
            headers: await getAuthHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete track');
        }

        showNotification('Track deleted successfully', 'success');
        closeModal('deleteTrackModal');
        loadTracksData();

    } catch (error) {
        console.error('Error deleting track:', error);
        showNotification(error.message, 'error');
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Parse comma-separated values into array
 */
function parseCommaSeparated(value) {
    if (!value) return [];
    return value.split(',').map(v => v.trim()).filter(v => v.length > 0);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Capitalize first letter
 */
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Open modal
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

/**
 * Close modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Export all public functions
export {
    loadTracksData as loadTracks,
    showCreateTrackModal,
    submitTrack,
    viewTrackDetails,
    editTrackFromDetails,
    editTrack,
    deleteTrack,
    confirmDeleteTrack
};
