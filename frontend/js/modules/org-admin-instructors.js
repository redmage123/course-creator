/**
 * Organization Admin Dashboard - Instructors Management Module
 *
 * BUSINESS CONTEXT:
 * Manages instructors within an organization. Instructors are teachers/facilitators
 * who deliver content, grade assignments, and interact with students. Organization
 * admins can add, remove, and assign instructors to projects and tracks.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Instructor CRUD operations via organization-management API
 * - Project and track assignment management
 * - Activity tracking and performance metrics
 * - Email invitation system for new instructors
 *
 * @module org-admin-instructors
 */
import {
    fetchMembers,
    addInstructor,
    removeMember
} from './org-admin-api.js';

import {
    escapeHtml,
    capitalizeFirst,
    formatDate,
    openModal,
    closeModal,
    showNotification,
    validateEmail
} from './org-admin-utils.js';

// Current organization context
let currentOrganizationId = null;

/**
 * Initialize instructors management module
 *
 * @param {string} organizationId - UUID of current organization
 */
export function initializeInstructorsManagement(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Instructors management initialized for organization:', organizationId);
}

/**
 * Load and display instructors data
 *
 * BUSINESS LOGIC:
 * Fetches all instructors for the organization
 * Supports filtering by status and search term
 *
 * @returns {Promise<void>}
 */
export async function loadInstructorsData() {
    try {
        // Get filter values
        const filters = {
            role: 'instructor',
            search: document.getElementById('instructorSearchInput')?.value || '',
            is_active: document.getElementById('instructorStatusFilter')?.value || undefined
        };

        const instructors = await fetchMembers(currentOrganizationId, filters);

        // Update UI
        renderInstructorsTable(instructors);
        updateInstructorsStats(instructors);

    } catch (error) {
        console.error('Error loading instructors:', error);
        renderInstructorsTable([]);
    }
}

/**
 * Render instructors table
 *
 * BUSINESS CONTEXT:
 * Displays instructors with key information:
 * - Name and email
 * - Active status
 * - Join date and last login
 * - Action buttons
 *
 * @param {Array} instructors - Array of instructor objects
 */
function renderInstructorsTable(instructors) {
    const tbody = document.getElementById('instructorsTableBody');

    if (!tbody) return;

    if (!instructors || instructors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No instructors found</td></tr>';
        return;
    }

    tbody.innerHTML = instructors.map(instructor => `
        <tr>
            <td>
                <strong>${escapeHtml(instructor.first_name)} ${escapeHtml(instructor.last_name)}</strong>
            </td>
            <td>${escapeHtml(instructor.email)}</td>
            <td>
                <span class="status-badge status-${instructor.is_active ? 'active' : 'inactive'}">
                    ${instructor.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${formatDate(instructor.joined_at)}</td>
            <td>${formatDate(instructor.last_login)}</td>
            <td>
                <button class="btn-icon" onclick="window.OrgAdmin.Instructors.viewInstructor('${instructor.user_id}')" title="View Details">
                    👁️
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Instructors.assignInstructor('${instructor.user_id}')" title="Assign to Project">
                    📋
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Instructors.removeInstructorPrompt('${instructor.user_id}')" title="Remove">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Update instructors statistics
 *
 * @param {Array} instructors - Array of instructor objects
 */
function updateInstructorsStats(instructors) {
    const totalInstructorsEl = document.getElementById('totalInstructors');
    if (totalInstructorsEl) {
        totalInstructorsEl.textContent = instructors.length;
    }

    const activeInstructorsEl = document.getElementById('activeInstructors');
    if (activeInstructorsEl) {
        const activeCount = instructors.filter(i => i.is_active).length;
        activeInstructorsEl.textContent = activeCount;
    }
}

/**
 * Show add instructor modal
 *
 * BUSINESS CONTEXT:
 * Opens modal to add new instructor to organization
 * Sends email invitation with account setup instructions
 */
export function showAddInstructorModal() {
    const modal = document.getElementById('addInstructorModal');
    const form = document.getElementById('addInstructorForm');

    if (!modal || !form) return;

    // Reset form
    form.reset();

    // Open modal
    openModal('addInstructorModal');
}

/**
 * Submit add instructor form
 *
 * BUSINESS LOGIC:
 * Validates instructor data and creates account
 * Sends welcome email with login credentials
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function submitAddInstructor(event) {
    event.preventDefault();

    try {
        // Gather form data
        const email = document.getElementById('instructorEmail')?.value;
        const firstName = document.getElementById('instructorFirstName')?.value;
        const lastName = document.getElementById('instructorLastName')?.value;
        const sendEmail = document.getElementById('instructorSendEmail')?.checked ?? true;

        // Validate email
        if (!validateEmail(email)) {
            showNotification('Please enter a valid email address', 'error');
            return;
        }

        // Validate names
        if (!firstName || !lastName) {
            showNotification('Please provide first and last name', 'error');
            return;
        }

        const instructorData = {
            email: email.toLowerCase(),
            first_name: firstName,
            last_name: lastName,
            role: 'instructor',
            send_welcome_email: sendEmail
        };

        await addInstructor(currentOrganizationId, instructorData);
        showNotification(`Instructor added successfully${sendEmail ? ' and invitation sent' : ''}`, 'success');
        closeModal('addInstructorModal');
        loadInstructorsData();

    } catch (error) {
        console.error('Error adding instructor:', error);
    }
}

/**
 * View instructor details
 *
 * @param {string} instructorId - UUID of instructor
 */
export function viewInstructor(instructorId) {
    console.log('View instructor:', instructorId);
    showNotification('Instructor details feature coming soon', 'info');
}

// Assignment state management
let currentAssignmentInstructorId = null;
let availableTracks = [];

/**
 * Assign instructor to project/track
 *
 * BUSINESS CONTEXT:
 * Opens modal to assign instructor to specific projects or tracks
 * Allows selection of tracks and locations within those tracks
 *
 * @param {string} instructorId - UUID of instructor
 * @returns {Promise<void>}
 */
export async function assignInstructor(instructorId) {
    console.log('🎯 Opening assignment modal for instructor:', instructorId);

    currentAssignmentInstructorId = instructorId;

    // Get instructor details from table row
    const instructorRow = document.querySelector(`tr button[onclick*="${instructorId}"]`)?.closest('tr');
    if (!instructorRow) {
        showNotification('Instructor not found', 'error');
        return;
    }

    const instructorName = instructorRow.querySelector('td:nth-child(1) strong')?.textContent || 'Unknown';
    const instructorEmail = instructorRow.querySelector('td:nth-child(2)')?.textContent || '';

    // Populate instructor info
    const infoSection = document.getElementById('assignmentInstructorInfo');
    if (infoSection) {
        infoSection.innerHTML = `
            <div style="padding: 1rem; background: var(--card-background, #f8f9fa); border-radius: 8px;">
                <strong style="display: block; margin-bottom: 0.5rem;">${escapeHtml(instructorName)}</strong>
                <span style="color: var(--text-muted, #6c757d); font-size: 0.9rem;">${escapeHtml(instructorEmail)}</span>
            </div>
        `;
    }

    // Show modal first (will load tracks asynchronously)
    openModal('instructorAssignmentModal');

    // Load tracks and current assignments (async)
    await loadTracksForAssignment(instructorId);
}

/**
 * Close assignment modal
 *
 * BUSINESS LOGIC:
 * Closes the assignment modal and resets state
 */
export function closeAssignmentModal() {
    closeModal('instructorAssignmentModal');

    // Reset state
    currentAssignmentInstructorId = null;
    availableTracks = [];
}

/**
 * Load tracks for assignment
 *
 * BUSINESS LOGIC:
 * Fetches all tracks for the organization and the instructor's current assignments
 * Renders track checkboxes with current assignments pre-selected
 *
 * @param {string} instructorId - UUID of instructor
 * @returns {Promise<void>}
 */
async function loadTracksForAssignment(instructorId) {
    try {
        // Get all tracks for this organization
        const tracksResponse = await fetch(`/api/v1/tracks?organization_id=${currentOrganizationId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!tracksResponse.ok) {
            throw new Error('Failed to load tracks');
        }

        availableTracks = await tracksResponse.json();
        console.log('📚 Loaded tracks:', availableTracks.length);

        // Get instructor's current assignments (may not exist yet)
        let currentAssignments = { track_ids: [], location_ids: [] };
        try {
            const assignmentsResponse = await fetch(`/api/v1/instructors/${instructorId}/assignments`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (assignmentsResponse.ok) {
                currentAssignments = await assignmentsResponse.json();
                console.log('📋 Current assignments:', currentAssignments);
            }
        } catch (error) {
            console.log('ℹ️ No existing assignments found');
        }

        // Render track checkboxes
        renderTrackCheckboxes(availableTracks, currentAssignments.track_ids || []);

        // If there are assigned tracks, load locations
        if (currentAssignments.track_ids && currentAssignments.track_ids.length > 0) {
            for (const trackId of currentAssignments.track_ids) {
                await loadLocationsForTrack(trackId, currentAssignments.location_ids || []);
            }
            updateLocationSectionVisibility();
        }

    } catch (error) {
        console.error('Error loading tracks:', error);

        // Show error message in track container
        const container = document.getElementById('trackAssignmentList');
        if (container) {
            container.innerHTML = '<p style="color: var(--error-color, #dc3545); font-style: italic;">Failed to load tracks. The tracks API may not be available yet.</p>';
        }

        showNotification('Failed to load tracks - continuing with empty list', 'warning');
    }
}

/**
 * Render track checkboxes
 *
 * BUSINESS CONTEXT:
 * Displays available tracks as checkboxes for instructor assignment
 *
 * @param {Array} tracks - Array of track objects
 * @param {Array} assignedTrackIds - Array of currently assigned track IDs
 */
function renderTrackCheckboxes(tracks, assignedTrackIds = []) {
    const container = document.getElementById('trackAssignmentList');
    if (!container) return;

    if (!tracks || tracks.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted, #6c757d); font-style: italic;">No tracks available</p>';
        return;
    }

    container.innerHTML = tracks.map(track => {
        const isChecked = assignedTrackIds.includes(track.id);
        return `
            <div style="padding: 0.75rem; border: 1px solid var(--border-color, #dee2e6); border-radius: 6px; margin-bottom: 0.5rem;">
                <label style="display: flex; align-items: flex-start; gap: 0.75rem; cursor: pointer;">
                    <input
                        type="checkbox"
                        id="track_${track.id}"
                        value="${track.id}"
                        ${isChecked ? 'checked' : ''}
                        onchange="window.OrgAdmin.Instructors.onTrackSelectionChange('${track.id}')"
                        style="margin-top: 0.25rem; width: 18px; height: 18px; cursor: pointer;"
                    >
                    <div style="flex: 1;">
                        <strong style="display: block; margin-bottom: 0.25rem;">${escapeHtml(track.name)}</strong>
                        ${track.description ? `<span style="color: var(--text-muted, #6c757d); font-size: 0.875rem;">${escapeHtml(track.description)}</span>` : ''}
                    </div>
                </label>
            </div>
        `;
    }).join('');
}

/**
 * Handle track selection change
 *
 * BUSINESS LOGIC:
 * When a track is selected, loads its locations
 * When deselected, removes locations options
 *
 * @param {string} trackId - UUID of track
 * @returns {Promise<void>}
 */
export async function onTrackSelectionChange(trackId) {
    const checkbox = document.getElementById(`track_${trackId}`);
    if (!checkbox) return;

    const isChecked = checkbox.checked;

    if (isChecked) {
        // Track selected - load locations for this track
        await loadLocationsForTrack(trackId, []);
    } else {
        // Track unselected - remove locations options for this track
        removeLocationsForTrack(trackId);
    }

    // Show/hide locations section based on whether any tracks are selected
    updateLocationSectionVisibility();
}

/**
 * Load locations for a specific track
 *
 * BUSINESS LOGIC:
 * Fetches all locations/locations for a track and renders them as checkboxes
 *
 * @param {string} trackId - UUID of track
 * @param {Array} assignedLocationIds - Array of pre-selected locations IDs
 * @returns {Promise<void>}
 */
async function loadLocationsForTrack(trackId, assignedLocationIds = []) {
    try {
        const response = await fetch(`/api/v1/tracks/${trackId}/locations`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) {
            console.log('ℹ️ No locations found for track:', trackId);
            return;
        }

        const locations = await response.json();
        console.log(`📍 Loaded ${locations.length} locations for track:`, trackId);

        renderLocationsForTrack(trackId, locations, assignedLocationIds);

    } catch (error) {
        console.error('Error loading locations:', error);
    }
}

/**
 * Render locations for a track
 *
 * BUSINESS CONTEXT:
 * Displays locations as checkboxes under the track they belong to
 *
 * @param {string} trackId - UUID of track
 * @param {Array} locations - Array of locations objects
 * @param {Array} assignedLocationIds - Array of pre-selected locations IDs
 */
function renderLocationsForTrack(trackId, locations, assignedLocationIds = []) {
    const container = document.getElementById('locationAssignmentList');
    if (!container) return;

    const track = availableTracks.find(t => t.id === trackId);
    if (!track) return;

    // Remove existing section for this track if it exists
    const existingSection = document.getElementById(`locations_track_${trackId}`);
    if (existingSection) {
        existingSection.remove();
    }

    // Create section for this track's locations
    const trackSection = document.createElement('div');
    trackSection.id = `locations_track_${trackId}`;
    trackSection.style.marginBottom = '1.5rem';
    trackSection.style.paddingBottom = '1.5rem';
    trackSection.style.borderBottom = '1px solid var(--border-color, #dee2e6)';

    if (locations.length === 0) {
        trackSection.innerHTML = `
            <h4 style="color: var(--primary-color, #007bff); font-size: 1rem; margin-bottom: 1rem;">${escapeHtml(track.name)} - Locations</h4>
            <p style="color: var(--text-muted, #6c757d); font-style: italic;">No locations available for this track</p>
        `;
    } else {
        trackSection.innerHTML = `
            <h4 style="color: var(--primary-color, #007bff); font-size: 1rem; margin-bottom: 1rem;">${escapeHtml(track.name)} - Locations</h4>
            ${locations.map(locations => {
                const isChecked = assignedLocationIds.includes(locations.id);
                return `
                    <div style="padding: 0.5rem; margin-bottom: 0.5rem;">
                        <label style="display: flex; align-items: center; gap: 0.75rem; cursor: pointer;">
                            <input
                                type="checkbox"
                                id="location_${locations.id}"
                                value="${locations.id}"
                                data-track-id="${trackId}"
                                ${isChecked ? 'checked' : ''}
                                style="width: 18px; height: 18px; cursor: pointer;"
                            >
                            <div>
                                <strong>${escapeHtml(locations.name)}</strong>
                                ${locations.locations ? `<span style="color: var(--text-muted, #6c757d); margin-left: 0.5rem; font-size: 0.875rem;">${escapeHtml(locations.locations)}</span>` : ''}
                            </div>
                        </label>
                    </div>
                `;
            }).join('')}
        `;
    }

    container.appendChild(trackSection);
}

/**
 * Remove locations for a track
 *
 * BUSINESS LOGIC:
 * Removes locations checkboxes when track is deselected
 *
 * @param {string} trackId - UUID of track
 */
function removeLocationsForTrack(trackId) {
    const section = document.getElementById(`locations_track_${trackId}`);
    if (section) {
        section.remove();
    }
}

/**
 * Update locations section visibility
 *
 * BUSINESS LOGIC:
 * Shows locations section only if at least one track is selected
 */
function updateLocationSectionVisibility() {
    const anyTracksSelected = Array.from(document.querySelectorAll('#trackAssignmentList input[type="checkbox"]'))
        .some(cb => cb.checked);

    const locationSection = document.getElementById('locationAssignmentSection');
    if (locationSection) {
        locationSection.style.display = anyTracksSelected ? 'block' : 'none';
    }
}

/**
 * Save instructor assignments
 *
 * BUSINESS LOGIC:
 * Collects selected tracks and locations and saves via API
 * Refreshes instructor table on success
 *
 * @returns {Promise<void>}
 */
export async function saveAssignments() {
    console.log('💾 Saving instructor assignments...');

    // Collect selected tracks
    const selectedTrackIds = Array.from(document.querySelectorAll('#trackAssignmentList input[type="checkbox"]:checked'))
        .map(cb => cb.value);

    // Collect selected locations
    const selectedLocationIds = Array.from(document.querySelectorAll('#locationAssignmentList input[type="checkbox"]:checked'))
        .map(cb => cb.value);

    console.log('Selected tracks:', selectedTrackIds);
    console.log('Selected locations:', selectedLocationIds);

    try {
        const response = await fetch(`/api/v1/instructors/${currentAssignmentInstructorId}/assignments`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                track_ids: selectedTrackIds,
                location_ids: selectedLocationIds
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to save assignments');
        }

        showNotification('Instructor assignments saved successfully', 'success');
        closeAssignmentModal();

        // Refresh instructor table to show new assignments
        await loadInstructorsData();

    } catch (error) {
        console.error('Error saving assignments:', error);
        showNotification('Failed to save assignments: ' + error.message, 'error');
    }
}

/**
 * Show remove instructor confirmation
 *
 * @param {string} instructorId - UUID of instructor to remove
 */
export function removeInstructorPrompt(instructorId) {
    // Store instructor ID for confirmation
    document.getElementById('removeInstructorId').value = instructorId;

    // Show warning
    const warning = document.getElementById('removeInstructorWarning');
    if (warning) {
        warning.textContent = 'This will remove the instructor from the organization and all assigned projects. This action cannot be undone.';
    }

    // Open confirmation modal
    openModal('removeInstructorModal');
}

/**
 * Confirm and execute instructor removal
 *
 * @returns {Promise<void>}
 */
export async function confirmRemoveInstructor() {
    const instructorId = document.getElementById('removeInstructorId')?.value;

    if (!instructorId) return;

    try {
        await removeMember(currentOrganizationId, instructorId);
        showNotification('Instructor removed successfully', 'success');
        closeModal('removeInstructorModal');
        loadInstructorsData();

    } catch (error) {
        console.error('Error removing instructor:', error);
    }
}

/**
 * Filter instructors based on search and status
 */
export function filterInstructors() {
    loadInstructorsData();
}
