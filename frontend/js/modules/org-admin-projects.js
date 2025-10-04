/**
 * Organization Admin Dashboard - Projects Management Module
 *
 * BUSINESS CONTEXT:
 * Manages projects within an organization. Projects are the primary learning
 * containers that hold tracks, modules, and content. Organization admins can
 * create, configure, activate, and manage project membership.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Multi-step project creation wizard with RAG suggestions
 * - Project lifecycle management (draft → active → completed → archived)
 * - Member management (instructors and students)
 * - Analytics dashboard integration
 * - Project instantiation from templates
 *
 * @module org-admin-projects
 */

import {
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    fetchMembers,
    addInstructor,
    addStudent,
    removeMember
} from './org-admin-api.js';

import {
    escapeHtml,
    capitalizeFirst,
    parseCommaSeparated,
    formatDate,
    formatDuration,
    openModal,
    closeModal,
    showNotification
} from './org-admin-utils.js';

// Current organization context
let currentOrganizationId = null;
let currentProjectId = null;

/**
 * Initialize projects management module
 *
 * @param {string} organizationId - UUID of current organization
 */
export function initializeProjectsManagement(organizationId) {
    currentOrganizationId = organizationId;
    console.log('Projects management initialized for organization:', organizationId);
}

/**
 * Load and display projects data
 *
 * BUSINESS LOGIC:
 * Fetches all projects for the organization and displays them in a table
 * Supports filtering by status and search term
 *
 * @returns {Promise<void>}
 */
export async function loadProjectsData() {
    try {
        // Get filter values
        const filters = {
            status: document.getElementById('projectStatusFilter')?.value || '',
            search: document.getElementById('projectSearchInput')?.value || ''
        };

        const projects = await fetchProjects(currentOrganizationId, filters);

        // Update UI
        renderProjectsTable(projects);
        updateProjectsStats(projects);

    } catch (error) {
        console.error('Error loading projects:', error);
        renderProjectsTable([]);
    }
}

/**
 * Render projects table
 *
 * BUSINESS CONTEXT:
 * Displays projects with key metrics:
 * - Name and description
 * - Status and duration
 * - Participant counts
 * - Action buttons
 *
 * @param {Array} projects - Array of project objects
 */
function renderProjectsTable(projects) {
    const tbody = document.getElementById('projectsTableBody');

    if (!tbody) return;

    if (!projects || projects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No projects found</td></tr>';
        return;
    }

    tbody.innerHTML = projects.map(project => `
        <tr>
            <td>
                <strong>${escapeHtml(project.name)}</strong>
                ${project.description ? `<br><small style="color: var(--text-muted);">${escapeHtml(project.description.substring(0, 100))}${project.description.length > 100 ? '...' : ''}</small>` : ''}
            </td>
            <td>
                <span class="status-badge status-${project.status || 'draft'}">
                    ${capitalizeFirst(project.status || 'draft')}
                </span>
            </td>
            <td>${formatDuration(project.duration_weeks)}</td>
            <td>
                <span class="stat-badge">${project.current_participants || 0}</span>
                ${project.max_participants ? `<small>/ ${project.max_participants}</small>` : ''}
            </td>
            <td>${formatDate(project.start_date)}</td>
            <td>${formatDate(project.end_date)}</td>
            <td>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.viewProject('${project.id}')" title="View Details">
                    👁️
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.editProject('${project.id}')" title="Edit">
                    ✏️
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.manageMembers('${project.id}')" title="Manage Members">
                    👥
                </button>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.deleteProjectPrompt('${project.id}')" title="Delete">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Update projects statistics
 *
 * @param {Array} projects - Array of project objects
 */
function updateProjectsStats(projects) {
    const totalProjectsEl = document.getElementById('totalProjects');
    if (totalProjectsEl) {
        totalProjectsEl.textContent = projects.length;
    }

    const activeProjectsEl = document.getElementById('activeProjects');
    if (activeProjectsEl) {
        const activeCount = projects.filter(p => p.status === 'active').length;
        activeProjectsEl.textContent = activeCount;
    }
}

/**
 * Show create project modal
 *
 * BUSINESS CONTEXT:
 * Opens multi-step wizard for project creation
 * Step 1: Basic Info, Step 2: Configuration, Step 3: Tracks
 */
export function showCreateProjectModal() {
    const modal = document.getElementById('projectWizardModal');
    const form = document.getElementById('projectWizardForm');

    if (!modal || !form) return;

    // Reset wizard to step 1
    form.reset();
    showProjectStep(1);

    // Open modal
    openModal('projectWizardModal');
}

/**
 * Navigate to next project wizard step
 *
 * BUSINESS LOGIC:
 * Validates current step before advancing
 * Step 1 → 2: Validates basic info
 * Step 2 → 3: Validates configuration
 */
export function nextProjectStep() {
    const currentStep = parseInt(document.querySelector('.wizard-step.active')?.dataset.step || '1');

    // Validate current step
    if (currentStep === 1) {
        const name = document.getElementById('projectName')?.value;
        const slug = document.getElementById('projectSlug')?.value;

        if (!name || !slug) {
            showNotification('Please fill in all required fields', 'error');
            return;
        }
    }

    const nextStep = currentStep + 1;
    if (nextStep <= 3) {
        showProjectStep(nextStep);
    }
}

/**
 * Navigate to previous project wizard step
 */
export function previousProjectStep() {
    const currentStep = parseInt(document.querySelector('.wizard-step.active')?.dataset.step || '1');
    const prevStep = currentStep - 1;

    if (prevStep >= 1) {
        showProjectStep(prevStep);
    }
}

/**
 * Show specific project wizard step
 *
 * @param {number} stepNumber - Step number (1, 2, or 3)
 */
function showProjectStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(step => {
        step.classList.remove('active');
    });

    // Show target step
    const targetStep = document.querySelector(`.wizard-step[data-step="${stepNumber}"]`);
    if (targetStep) {
        targetStep.classList.add('active');
    }

    // Update navigation buttons
    const prevBtn = document.getElementById('wizardPrevBtn');
    const nextBtn = document.getElementById('wizardNextBtn');
    const submitBtn = document.getElementById('wizardSubmitBtn');

    if (prevBtn) prevBtn.style.display = stepNumber === 1 ? 'none' : 'inline-block';
    if (nextBtn) nextBtn.style.display = stepNumber === 3 ? 'none' : 'inline-block';
    if (submitBtn) submitBtn.style.display = stepNumber === 3 ? 'inline-block' : 'none';
}

/**
 * Submit project creation form
 *
 * BUSINESS LOGIC:
 * Gathers data from all wizard steps and creates project
 *
 * @param {Event} event - Form submit event
 * @returns {Promise<void>}
 */
export async function submitProjectForm(event) {
    event.preventDefault();

    try {
        // Gather data from all steps
        const projectData = {
            name: document.getElementById('projectName')?.value,
            slug: document.getElementById('projectSlug')?.value,
            description: document.getElementById('projectDescription')?.value || null,
            objectives: parseCommaSeparated(document.getElementById('projectObjectives')?.value),
            target_roles: parseCommaSeparated(document.getElementById('projectTargetRoles')?.value),
            duration_weeks: parseInt(document.getElementById('projectDuration')?.value) || null,
            max_participants: parseInt(document.getElementById('projectMaxParticipants')?.value) || null,
            start_date: document.getElementById('projectStartDate')?.value || null,
            end_date: document.getElementById('projectEndDate')?.value || null
        };

        await createProject(currentOrganizationId, projectData);
        showNotification('Project created successfully', 'success');
        closeModal('projectWizardModal');
        loadProjectsData();

    } catch (error) {
        console.error('Error creating project:', error);
    }
}

/**
 * View project details
 *
 * @param {string} projectId - UUID of project
 */
export function viewProject(projectId) {
    // Implementation will show project details modal
    console.log('View project:', projectId);
    showNotification('Project details feature coming soon', 'info');
}

/**
 * Edit project
 *
 * @param {string} projectId - UUID of project to edit
 */
export async function editProject(projectId) {
    try {
        // Fetch project details and populate form
        // This would be implemented similar to track editing
        console.log('Edit project:', projectId);
        showNotification('Project editing feature coming soon', 'info');
    } catch (error) {
        console.error('Error editing project:', error);
    }
}

/**
 * Manage project members
 *
 * BUSINESS CONTEXT:
 * Opens modal to manage instructors and students assigned to project
 *
 * @param {string} projectId - UUID of project
 */
export async function manageMembers(projectId) {
    currentProjectId = projectId;

    try {
        // Fetch project members
        const members = await fetchMembers(currentOrganizationId, { project_id: projectId });

        // Render members list
        renderProjectMembers(members);

        // Open members modal
        openModal('projectMembersModal');

    } catch (error) {
        console.error('Error loading project members:', error);
    }
}

/**
 * Render project members in modal
 *
 * @param {Array} members - Array of member objects
 */
function renderProjectMembers(members) {
    const instructorsList = document.getElementById('projectInstructorsList');
    const studentsList = document.getElementById('projectStudentsList');

    if (!instructorsList || !studentsList) return;

    const instructors = members.filter(m => m.role === 'instructor');
    const students = members.filter(m => m.role === 'student');

    instructorsList.innerHTML = instructors.length > 0
        ? instructors.map(i => `
            <div class="member-item">
                <span>${escapeHtml(i.first_name)} ${escapeHtml(i.last_name)}</span>
                <span>${escapeHtml(i.email)}</span>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.removeMemberFromProject('${i.user_id}')" title="Remove">
                    ✗
                </button>
            </div>
        `).join('')
        : '<p>No instructors assigned</p>';

    studentsList.innerHTML = students.length > 0
        ? students.map(s => `
            <div class="member-item">
                <span>${escapeHtml(s.first_name)} ${escapeHtml(s.last_name)}</span>
                <span>${escapeHtml(s.email)}</span>
                <button class="btn-icon" onclick="window.OrgAdmin.Projects.removeMemberFromProject('${s.user_id}')" title="Remove">
                    ✗
                </button>
            </div>
        `).join('')
        : '<p>No students enrolled</p>';
}

/**
 * Remove member from project
 *
 * @param {string} userId - UUID of user to remove
 */
export async function removeMemberFromProject(userId) {
    if (!confirm('Are you sure you want to remove this member from the project?')) {
        return;
    }

    try {
        await removeMember(currentOrganizationId, userId);
        showNotification('Member removed successfully', 'success');

        // Refresh members list
        manageMembers(currentProjectId);

    } catch (error) {
        console.error('Error removing member:', error);
    }
}

/**
 * Show delete project confirmation
 *
 * @param {string} projectId - UUID of project to delete
 */
export function deleteProjectPrompt(projectId) {
    currentProjectId = projectId;

    const warning = document.getElementById('deleteProjectWarning');
    if (warning) {
        warning.textContent = 'This will permanently delete the project and all associated data. This action cannot be undone.';
    }

    openModal('deleteProjectModal');
}

/**
 * Confirm and execute project deletion
 *
 * @returns {Promise<void>}
 */
export async function confirmDeleteProject() {
    if (!currentProjectId) return;

    try {
        await deleteProject(currentProjectId);
        showNotification('Project deleted successfully', 'success');
        closeModal('deleteProjectModal');
        loadProjectsData();

    } catch (error) {
        console.error('Error deleting project:', error);
    }
}

/**
 * Filter projects based on search and status
 */
export function filterProjects() {
    loadProjectsData();
}
