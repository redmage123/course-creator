/**
 * Organization Admin Dashboard - Students Management Module
 *
 * BUSINESS CONTEXT:
 * Manages students (learners) within an organization. Students enroll in projects,
 * complete tracks, and progress through learning materials. Organization admins
 * can add students, manage enrollments, and track progress.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Student CRUD operations via organization-management API
 * - Enrollment management for projects and tracks
 * - Progress tracking and analytics
 * - Bulk student import functionality
 *
 * @module org-admin-students
 */
import {
    fetchMembers,
    addStudent,
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
 * Initialize students management module
 *
 * @param {string} organizationId - UUID of current organization
 */
export function initializeStudentsManagement(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Students management initialized for organization:', organizationId);
}

/**
 * Load and display students data
 *
 * BUSINESS LOGIC:
 * Fetches all students for the organization
 * Supports filtering by status, enrollment, and search term
 *
 * @returns {Promise<void>}
 */
export async function loadStudentsData() {
    try {
        // Get filter values
        const filters = {
            role: 'student',
            search: document.getElementById('studentSearchInput')?.value || '',
            is_active: document.getElementById('studentStatusFilter')?.value || undefined
        };

        const students = await fetchMembers(currentOrganizationId, filters);

        // Update UI
        renderStudentsTable(students);
        updateStudentsStats(students);

    } catch (error) {
        console.error('Error loading students:', error);
        renderStudentsTable([]);
    }
}

/**
 * Render students table
 *
 * BUSINESS CONTEXT:
 * Displays students with key information:
 * - Name and email
 * - Active status
 * - Join date and last login
 * - Enrollment count
 * - Action buttons
 *
 * @param {Array} students - Array of student objects
 */
function renderStudentsTable(students) {
    const tbody = document.getElementById('studentsTableBody');

    if (!tbody) return;

    if (!students || students.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No students found</td></tr>';
        return;
    }

    tbody.innerHTML = students.map(student => `
        <tr>
            <td>
                <strong>${escapeHtml(student.first_name)} ${escapeHtml(student.last_name)}</strong>
            </td>
            <td>${escapeHtml(student.email)}</td>
            <td>
                <span class="status-badge status-${student.is_active ? 'active' : 'inactive'}">
                    ${student.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td><span class="stat-badge">${student.enrollment_count || 0}</span></td>
            <td>${student.progress_percentage ? `${student.progress_percentage}%` : 'N/A'}</td>
            <td>${formatDate(student.joined_at)}</td>
            <td>
                <button class="btn-icon" onclick="window.OrgAdmin.Students.viewStudent('${student.user_id}')" title="View Details">
                    👁️
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Students.enrollStudent('${student.user_id}')" title="Manage Enrollments">
                    📚
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Students.viewProgress('${student.user_id}')" title="View Progress">
                    📊
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Students.removeStudentPrompt('${student.user_id}')" title="Remove">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Update students statistics
 *
 * @param {Array} students - Array of student objects
 */
function updateStudentsStats(students) {
    const totalStudentsEl = document.getElementById('totalStudents');
    if (totalStudentsEl) {
        totalStudentsEl.textContent = students.length;
    }

    const activeStudentsEl = document.getElementById('activeStudents');
    if (activeStudentsEl) {
        const activeCount = students.filter(s => s.is_active).length;
        activeStudentsEl.textContent = activeCount;
    }
}

/**
 * Show add student modal
 *
 * BUSINESS CONTEXT:
 * Opens modal to add new student to organization
 * Supports single student addition or bulk import
 */
export function showAddStudentModal() {
    const modal = document.getElementById('addStudentModal');
    const form = document.getElementById('addStudentForm');

    if (!modal || !form) return;

    // Reset form
    form.reset();

    // Open modal
    openModal('addStudentModal');
}

/**
 * Submit add student form
 *
 * BUSINESS LOGIC:
 * Validates student data and creates account
 * Sends welcome email with login credentials
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function submitAddStudent(event) {
    event.preventDefault();

    try {
        // Gather form data
        const email = document.getElementById('studentEmail')?.value;
        const firstName = document.getElementById('studentFirstName')?.value;
        const lastName = document.getElementById('studentLastName')?.value;
        const sendEmail = document.getElementById('studentSendEmail')?.checked ?? true;

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

        const studentData = {
            email: email.toLowerCase(),
            first_name: firstName,
            last_name: lastName,
            role: 'student',
            send_welcome_email: sendEmail
        };

        await addStudent(currentOrganizationId, studentData);
        showNotification(`Student added successfully${sendEmail ? ' and invitation sent' : ''}`, 'success');
        closeModal('addStudentModal');
        loadStudentsData();

    } catch (error) {
        console.error('Error adding student:', error);
    }
}

/**
 * View student details
 *
 * BUSINESS CONTEXT:
 * Shows comprehensive student information including:
 * - Personal details
 * - Enrollment history
 * - Progress across all tracks
 * - Activity timeline
 *
 * @param {string} studentId - UUID of student
 */
export function viewStudent(studentId) {
    console.log('View student:', studentId);
    showNotification('Student details feature coming soon', 'info');
}

/**
 * Manage student enrollments
 *
 * BUSINESS CONTEXT:
 * Opens modal to enroll student in projects and tracks
 * Shows current enrollments and available options
 *
 * @param {string} studentId - UUID of student
 */
export function enrollStudent(studentId) {
    console.log('Enroll student:', studentId);
    showNotification('Student enrollment feature coming soon', 'info');
}

/**
 * View student progress
 *
 * BUSINESS CONTEXT:
 * Opens detailed progress dashboard for student
 * Shows completion rates, quiz scores, and activity
 *
 * @param {string} studentId - UUID of student
 */
export function viewProgress(studentId) {
    console.log('View student progress:', studentId);
    showNotification('Student progress feature coming soon', 'info');
}

/**
 * Show remove student confirmation
 *
 * @param {string} studentId - UUID of student to remove
 */
export function removeStudentPrompt(studentId) {
    // Store student ID for confirmation
    document.getElementById('removeStudentId').value = studentId;

    // Show warning
    const warning = document.getElementById('removeStudentWarning');
    if (warning) {
        warning.textContent = 'This will remove the student from the organization and all enrollments. Progress data will be archived but no longer accessible. This action cannot be undone.';
    }

    // Open confirmation modal
    openModal('removeStudentModal');
}

/**
 * Confirm and execute student removal
 *
 * @returns {Promise<void>}
 */
export async function confirmRemoveStudent() {
    const studentId = document.getElementById('removeStudentId')?.value;

    if (!studentId) return;

    try {
        await removeMember(currentOrganizationId, studentId);
        showNotification('Student removed successfully', 'success');
        closeModal('removeStudentModal');
        loadStudentsData();

    } catch (error) {
        console.error('Error removing student:', error);
    }
}

/**
 * Filter students based on search and status
 */
export function filterStudents() {
    loadStudentsData();
}

/**
 * Show bulk student import modal
 *
 * BUSINESS CONTEXT:
 * Allows CSV upload of multiple students
 * Validates data and creates accounts in batch
 */
export function showBulkImportModal() {
    const modal = document.getElementById('bulkImportModal');

    if (!modal) return;

    // Open modal
    openModal('bulkImportModal');
}

/**
 * Process bulk student import
 *
 * TECHNICAL IMPLEMENTATION:
 * - Parses CSV file
 * - Validates each row
 * - Creates student accounts in batch
 * - Reports success/failure for each entry
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function processBulkImport(event) {
    event.preventDefault();

    const fileInput = document.getElementById('bulkImportFile');
    const file = fileInput?.files[0];

    if (!file) {
        showNotification('Please select a CSV file', 'error');
        return;
    }

    try {
        // Read and parse CSV file
        const text = await file.text();
        const rows = text.split('\n').map(row => row.split(','));

        // Validate header row
        const headers = rows[0].map(h => h.trim().toLowerCase());
        if (!headers.includes('email') || !headers.includes('first_name') || !headers.includes('last_name')) {
            showNotification('CSV must include email, first_name, and last_name columns', 'error');
            return;
        }

        // Process each student (skip header row)
        let successCount = 0;
        let errorCount = 0;

        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            if (row.length < 3) continue; // Skip empty rows

            const studentData = {
                email: row[headers.indexOf('email')]?.trim().toLowerCase(),
                first_name: row[headers.indexOf('first_name')]?.trim(),
                last_name: row[headers.indexOf('last_name')]?.trim(),
                role: 'student',
                send_welcome_email: true
            };

            try {
                await addStudent(currentOrganizationId, studentData);
                successCount++;
            } catch (error) {
                console.error(`Error adding student ${studentData.email}:`, error);
                errorCount++;
            }
        }

        showNotification(`Import complete: ${successCount} added, ${errorCount} failed`, successCount > 0 ? 'success' : 'error');
        closeModal('bulkImportModal');
        loadStudentsData();

    } catch (error) {
        console.error('Error processing bulk import:', error);
        showNotification('Failed to process CSV file', 'error');
    }
}
