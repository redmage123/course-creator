/**
 * Organization Admin Dashboard - Tracks Management Module
 *
 * BUSINESS CONTEXT:
 * Manages learning tracks within the organization admin dashboard.
 * Tracks are structured learning paths within projects that students
 * can enroll in and instructors can manage. Each track has difficulty levels,
 * prerequisites, learning objectives, and enrollment limits.
 *
 * TECHNICAL IMPLEMENTATION:
 * - CRUD operations for tracks using organization-management API
 * - Modal-based UI for create/edit/view operations
 * - Client-side filtering by project, status, difficulty, and search
 * - Integration with projects API for dropdown population
 *
 * @module org-admin-tracks
 */
import {
    fetchTracks,
    fetchTrack,
    createTrack,
    updateTrack,
    deleteTrack,
    fetchProjects
} from './org-admin-api.js';

import {
    escapeHtml,
    capitalizeFirst,
    parseCommaSeparated,
    openModal,
    closeModal,
    showNotification
} from './org-admin-utils.js';

// Current organization ID (set during initialization)
let currentOrganizationId = null;

/**
 * Initialize tracks management module
 *
 * BUSINESS CONTEXT:
 * Sets up the tracks module with organization context
 * Called when dashboard loads
 *
 * @param {string} organizationId - UUID of current organization
 *
 * @example
 * initializeTracksManagement('123e4567-e89b-12d3-a456-426614174000');
 */
export function initializeTracksManagement(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Tracks management initialized for organization:', organizationId);
}

/**
 * Load and display tracks data
 *
 * BUSINESS LOGIC:
 * Fetches tracks based on current filter settings and updates UI
 * Filters include: project, status, difficulty level, search term
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reads filter values from DOM elements
 * - Calls API with query parameters
 * - Updates table and statistics
 *
 * @returns {Promise<void>}
 */
export async function loadTracksData() {
    try {
        // Get filter values from UI
        const filters = {
            project_id: document.getElementById('trackProjectFilter')?.value || '',
            status: document.getElementById('trackStatusFilter')?.value || '',
            difficulty_level: document.getElementById('trackDifficultyFilter')?.value || '',
            search: document.getElementById('trackSearchInput')?.value || ''
        };

        // Fetch tracks with filters
        const tracks = await fetchTracks(filters);

        // Update UI components
        renderTracksTable(tracks);
        updateTracksStats(tracks);

    } catch (error) {
        console.error('Error loading tracks:', error);
        renderTracksTable([]);
    }
}

/**
 * Render tracks table
 *
 * BUSINESS CONTEXT:
 * Displays tracks in a data table with key information:
 * - Name and description
 * - Project association
 * - Difficulty level
 * - Duration and enrollment stats
 * - Action buttons (view, edit, delete)
 *
 * @param {Array} tracks - Array of track objects from API
 */
function renderTracksTable(tracks) {
    const tbody = document.getElementById('tracksTableBody');

    if (!tbody) return;

    // Handle empty state
    if (!tracks || tracks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No tracks found</td></tr>';
        return;
    }

    // Render track rows
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
                <button class="btn-icon" onclick="window.OrgAdmin.Tracks.viewTrackDetails('${track.id}')" title="View Details">
                    👁️
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Tracks.editTrack('${track.id}')" title="Edit">
                    ✏️
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Tracks.manageTrack('${track.id}')" title="Manage Track">
                    📊
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Tracks.deleteTrackPrompt('${track.id}')" title="Delete">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Update tracks statistics display
 *
 * BUSINESS CONTEXT:
 * Updates the total tracks count in dashboard overview
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
 * Opens modal in "create" mode with empty form
 * Loads projects dropdown for track assignment
 */
export function showCreateTrackModal() {
    const modal = document.getElementById('trackModal');
    const form = document.getElementById('trackForm');
    const title = document.getElementById('trackModalTitle');
    const submitBtn = document.getElementById('trackSubmitBtn');

    if (!modal || !form) return;

    // Reset form to empty state
    form.reset();
    document.getElementById('trackId').value = '';

    // Set modal UI for creation
    title.textContent = 'Create New Track';
    submitBtn.textContent = 'Create Track';

    // Load projects for dropdown
    loadProjectsForTrackForm();

    // Show modal
    openModal('trackModal');
}

/**
 * Load projects for track form dropdown
 *
 * BUSINESS CONTEXT:
 * Populates project selection dropdown in track form
 * Also updates filter dropdown for consistency
 *
 * TECHNICAL IMPLEMENTATION:
 * Fetches projects from API and populates two select elements:
 * - trackProject (form dropdown)
 * - trackProjectFilter (filter dropdown)
 */
async function loadProjectsForTrackForm() {
    try {
        const projects = await fetchProjects(currentOrganizationId);

        // Populate form dropdown
        const select = document.getElementById('trackProject');
        if (select) {
            select.innerHTML = '<option value="">Select Project</option>' +
                projects.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
        }

        // Populate filter dropdown
        const filterSelect = document.getElementById('trackProjectFilter');
        if (filterSelect) {
            filterSelect.innerHTML = '<option value="">All Projects</option>' +
                projects.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
        }

    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

/**
 * Submit track form (create or update)
 *
 * BUSINESS LOGIC:
 * Handles both track creation and updates
 * Validates form data and submits to API
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function submitTrack(event) {
    event.preventDefault();

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

        // Call appropriate API method
        if (isUpdate) {
            await updateTrack(trackId, formData);
            showNotification('Track updated successfully', 'success');
        } else {
            await createTrack(formData);
            showNotification('Track created successfully', 'success');
        }

        // Close modal and refresh data
        closeModal('trackModal');
        loadTracksData();

    } catch (error) {
        // Error already shown by API layer
        console.error('Error saving track:', error);
    }
}

/**
 * View track details in modal
 *
 * BUSINESS CONTEXT:
 * Displays comprehensive track information in read-only modal
 * Shows all track properties including arrays (prerequisites, objectives)
 *
 * @param {string} trackId - UUID of track to view
 * @returns {Promise<void>}
 */
export async function viewTrackDetails(trackId) {
    try {
        const track = await fetchTrack(trackId);

        // Populate details modal with track data
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

        // Store track ID for edit button in modal
        document.getElementById('trackDetailsModal').dataset.trackId = trackId;

        // Show details modal
        openModal('trackDetailsModal');

    } catch (error) {
        console.error('Error loading track details:', error);
    }
}

/**
 * Edit track from details modal
 *
 * BUSINESS CONTEXT:
 * Allows quick switch from view mode to edit mode
 * Closes details modal and opens edit form
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
 *
 * BUSINESS LOGIC:
 * Loads track data into form and opens modal in edit mode
 *
 * @param {string} trackId - UUID of track to edit
 * @returns {Promise<void>}
 */
export async function editTrack(trackId) {
    try {
        const track = await fetchTrack(trackId);

        // Populate form with track data
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

        // Set modal UI for editing
        document.getElementById('trackModalTitle').textContent = 'Edit Track';
        document.getElementById('trackSubmitBtn').textContent = 'Update Track';

        // Load projects dropdown
        await loadProjectsForTrackForm();

        // Show modal
        openModal('trackModal');

    } catch (error) {
        console.error('Error loading track for edit:', error);
    }
}

/**
 * Show delete confirmation modal
 *
 * BUSINESS CONTEXT:
 * Prevents accidental deletion by requiring confirmation
 * Warns about enrollment removal
 *
 * @param {string} trackId - UUID of track to delete
 */
export function deleteTrackPrompt(trackId) {
    // Store track ID for confirmation
    document.getElementById('deleteTrackId').value = trackId;

    // Show warning message
    const warning = document.getElementById('deleteTrackWarning');
    if (warning) {
        warning.textContent = 'This action cannot be undone. All enrollments will be removed.';
    }

    // Show confirmation modal
    openModal('deleteTrackModal');
}

/**
 * Confirm and execute track deletion
 *
 * BUSINESS LOGIC:
 * Deletes track after user confirmation
 * Refreshes track list on success
 *
 * @returns {Promise<void>}
 */
export async function confirmDeleteTrack() {
    const trackId = document.getElementById('deleteTrackId').value;

    if (!trackId) return;

    try {
        await deleteTrack(trackId);
        showNotification('Track deleted successfully', 'success');
        closeModal('deleteTrackModal');
        loadTracksData();

    } catch (error) {
        // Error already shown by API layer
        console.error('Error deleting track:', error);
    }
}

/**
 * Show custom track form with advanced options
 *
 * BUSINESS CONTEXT:
 * Opens advanced custom track creation modal with extended configuration options
 * including scheduling, assessment requirements, and automation settings
 *
 * TECHNICAL IMPLEMENTATION:
 * - Opens customTrackModal
 * - Loads projects dropdown
 * - Resets form to default values
 */
export async function showCustomTrackForm() {
    const modal = document.getElementById('customTrackModal');
    const form = document.getElementById('customTrackForm');

    if (!modal || !form) {
        showNotification('Custom track modal not found', 'error');
        return;
    }

    // Reset form to default values
    form.reset();

    // Load projects for dropdown
    try {
        const projects = await fetchProjects(currentOrganizationId);

        const select = document.getElementById('customTrackProject');
        if (select) {
            select.innerHTML = '<option value="">Select Project</option>' +
                projects.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
        }
    } catch (error) {
        console.error('Error loading projects:', error);
    }

    // Show modal
    openModal('customTrackModal');
}

/**
 * Submit custom track form with advanced options
 *
 * BUSINESS CONTEXT:
 * Creates a new track with extended configuration options including
 * scheduling, assessment requirements, and automation settings
 *
 * TECHNICAL IMPLEMENTATION:
 * - Gathers comprehensive form data from customTrackForm
 * - Validates required fields
 * - Submits to API via createTrack
 * - Handles errors and displays notifications
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function submitCustomTrack(event) {
    event.preventDefault();

    const form = document.getElementById('customTrackForm');
    if (!form) {
        console.error('Custom track form not found');
        return;
    }

    try {
        // Gather basic information
        const formData = {
            name: document.getElementById('customTrackName')?.value,
            description: document.getElementById('customTrackDescription')?.value || null,
            project_id: document.getElementById('customTrackProject')?.value,
            category: document.getElementById('customTrackCategory')?.value || null,
            difficulty_level: document.getElementById('customTrackDifficulty')?.value || 'beginner',
            tags: parseCommaSeparated(document.getElementById('customTrackTags')?.value || ''),

            // Schedule & Duration
            duration_weeks: parseInt(document.getElementById('customTrackDuration')?.value) || null,
            hours_per_week: parseInt(document.getElementById('customTrackHoursPerWeek')?.value) || null,
            start_date: document.getElementById('customTrackStartDate')?.value || null,
            end_date: document.getElementById('customTrackEndDate')?.value || null,
            self_paced: document.getElementById('customTrackSelfPaced')?.value === 'true',

            // Enrollment & Capacity
            max_students: parseInt(document.getElementById('customTrackMaxStudents')?.value) || null,
            enrollment_deadline: document.getElementById('customTrackEnrollmentDeadline')?.value || null,
            auto_enroll: document.getElementById('customTrackAutoEnroll')?.checked || false,

            // Prerequisites & Requirements
            prerequisites: parseCommaSeparated(document.getElementById('customTrackPrerequisites')?.value || ''),
            target_audience: parseCommaSeparated(document.getElementById('customTrackAudience')?.value || ''),
            learning_objectives: parseCommaSeparated(document.getElementById('customTrackObjectives')?.value || ''),

            // Assessment Settings
            requires_assessment: document.getElementById('customTrackRequiresAssessment')?.checked || false,
            pass_threshold: parseInt(document.getElementById('customTrackPassThreshold')?.value) || 70,
            certificate_enabled: document.getElementById('customTrackCertificate')?.checked || true,

            // Automation Settings
            auto_progress: document.getElementById('customTrackAutoProgress')?.checked || false,
            reminder_emails: document.getElementById('customTrackReminders')?.checked || true,
            progress_notifications: document.getElementById('customTrackProgressNotifications')?.checked || true,

            // Initial status
            status: 'draft'
        };

        // Validate required fields
        if (!formData.name) {
            showNotification('Track name is required', 'error');
            return;
        }

        if (!formData.project_id) {
            showNotification('Project is required', 'error');
            return;
        }

        // Create track via API
        await createTrack(formData);
        showNotification('Custom track created successfully', 'success');

        // Close modal and refresh data
        closeModal('customTrackModal');
        loadTracksData();

        // Reset form
        form.reset();

    } catch (error) {
        console.error('Error creating custom track:', error);
        showNotification(`Failed to create track: ${error.message}`, 'error');
    }
}

/**
 * Manage a specific track from the main Tracks list
 *
 * BUSINESS CONTEXT:
 * Provides quick access to track management from the Tracks tab without
 * needing to navigate through projects. Organization admins can configure
 * track details, assign instructors, add courses, and enroll students.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches track details from API
 * - Imports and calls openTrackManagement from org-admin-projects module
 * - Loads track data into modal for editing
 * - Reuses existing track management modal UI
 *
 * @param {string} trackId - UUID of the track to manage
 * @returns {Promise<void>}
 */
/**
 * Manage a single track from the Tracks tab main list
 *
 * BUSINESS CONTEXT:
 * Organization admins need direct access to track management from the Tracks list
 * without navigating through Projects first. This provides a focused view for
 * track-specific operations like adding courses, assigning instructors, and
 * enrolling students.
 *
 * WHY THIS EXISTS:
 * - Tracks can be viewed as independent entities, not just project sub-components
 * - Admins often work with specific tracks directly (e.g., "Python Track")
 * - Having to navigate Projects → Project → Tracks → Manage is too many clicks
 * - This function provides direct access: Tracks → Manage (2 clicks vs 4)
 * - Improves UX efficiency for track-focused workflows
 *
 * ARCHITECTURAL DECISIONS:
 * - Delegates to Projects module modal (DEPENDENCY INVERSION PRINCIPLE)
 * - Uses window.OrgAdmin global namespace for cross-module communication
 * - Does NOT duplicate modal code (DRY principle maintained)
 * - Transforms single track into array format for modal compatibility
 *
 * WHY USE window.OrgAdmin INSTEAD OF IMPORT:
 * - Avoids circular dependency between org-admin-tracks.js and org-admin-projects.js
 * - Both modules are loaded by org-admin-main.js which sets up window.OrgAdmin
 * - Global namespace is already established for backwards compatibility
 * - Alternative would be to create a third module for the modal (over-engineering)
 *
 * LISKOV SUBSTITUTION PRINCIPLE:
 * - This function can substitute for manageProjectTracks() behaviorally
 * - Both load track data and open the same modal interface
 * - Modal doesn't know or care whether called from Projects or Tracks tab
 *
 * SINGLE RESPONSIBILITY PRINCIPLE:
 * - Only responsibility: Load single track and delegate to modal
 * - Authentication: delegated to localStorage
 * - API calls: delegated to fetch API
 * - Modal rendering: delegated to Projects module
 * - Data transformation: minimal, just format adaptation
 *
 * TECHNICAL IMPLEMENTATION:
 * 1. Validates authentication and organization context
 * 2. Fetches track details from organization-scoped endpoint
 * 3. Validates modal functions are available (defensive programming)
 * 4. Transforms track data to match modal's expected format
 * 5. Wraps single track in array (modal expects array from wizard context)
 * 6. Delegates to Projects module for UI rendering
 *
 * @param {string} trackId - UUID of the track to manage
 * @returns {Promise<void>}
 *
 * @throws {Error} If track fetch fails
 * @throws {Error} If modal functions not available
 *
 * @example
 * // Called from Tracks table "Manage" button
 * <button onclick="window.OrgAdmin.Tracks.manageTrack('track-uuid-456')">
 *   📊 Manage
 * </button>
 */
export async function manageTrack(trackId) {
    console.log('📊 Managing track:', trackId);

    try {
        // AUTHENTICATION CHECK
        // WHY: Prevent unauthorized access to track data
        // Security boundary: All API calls require authentication token
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            showNotification('Please log in to continue', 'error');
            return;
        }

        // ORGANIZATION CONTEXT CHECK
        // WHY: Multi-tenant system requires organization scope for all operations
        // Prevents cross-organization data access (security requirement)
        const orgId = localStorage.getItem('currentOrgId');
        if (!orgId) {
            showNotification('No organization selected', 'error');
            return;
        }

        // FETCH TRACK DATA
        // WHY: Need fresh track data including courses, instructors, students
        // Uses organization-scoped endpoint to enforce multi-tenant boundaries
        const trackResponse = await fetch(`${window.API_BASE_URL || 'https://localhost'}/api/v1/organizations/${orgId}/tracks/${trackId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!trackResponse.ok) {
            throw new Error(`Failed to fetch track: ${trackResponse.status}`);
        }

        const track = await trackResponse.json();
        console.log('📋 Track data:', track);

        // VALIDATE MODAL AVAILABILITY
        // WHY: Defensive programming - ensure Projects module loaded before calling
        // Fails gracefully with clear message if module not initialized
        // INTERFACE SEGREGATION PRINCIPLE: Only depends on specific modal functions needed
        if (!window.OrgAdmin?.Projects?.openTrackManagement) {
            console.error('Track management modal not available');
            showNotification('Track management feature not available', 'error');
            return;
        }

        // DATA TRANSFORMATION
        // WHY: Modal expects array of tracks with specific structure
        // Transform single track into array format for modal compatibility
        // OPEN/CLOSED PRINCIPLE: Adapt data to interface without modifying modal code
        const trackData = {
            id: track.id,
            name: track.name,
            description: track.description || '',
            difficulty_level: track.difficulty_level || 'beginner',
            duration_weeks: track.duration_weeks || 0,
            instructors: track.instructors || [],
            courses: track.courses || [],
            students: track.students || [],
            project_id: track.project_id,
            project_name: track.project_name || 'N/A'
        };

        // VALIDATE POPULATE FUNCTION
        // WHY: Second defensive check - ensure list population function available
        // Modal needs track list populated before opening
        if (!window.OrgAdmin?.Projects?.populateTrackReviewList) {
            console.error('Track review list population not available');
            showNotification('Track management feature not available', 'error');
            return;
        }

        // POPULATE TRACK LIST
        // WHY: Modal expects tracks in generatedTracks array (from wizard context)
        // Wrap single track in array to match wizard's multi-track interface
        // ADAPTER PATTERN: Adapting single-track workflow to multi-track modal
        window.OrgAdmin.Projects.populateTrackReviewList([trackData]);

        // OPEN MODAL
        // WHY: Delegate to Projects module for modal rendering
        // Pass index 0 since we only have one track in the array
        // DEPENDENCY INVERSION: Depend on modal abstraction, not concrete implementation
        window.OrgAdmin.Projects.openTrackManagement(0);

    } catch (error) {
        // ERROR HANDLING
        // WHY: Provide clear user feedback when operations fail
        // Log technical details for debugging, show user-friendly message
        console.error('❌ Error managing track:', error);
        showNotification(`Failed to load track: ${error.message}`, 'error');
    }
}
