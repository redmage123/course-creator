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

/**
 * Assign instructor to project/track
 *
 * BUSINESS CONTEXT:
 * Opens modal to assign instructor to specific projects or tracks
 *
 * @param {string} instructorId - UUID of instructor
 */
export function assignInstructor(instructorId) {
    console.log('Assign instructor:', instructorId);
    showNotification('Instructor assignment feature coming soon', 'info');
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
