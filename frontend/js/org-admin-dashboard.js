/**
 * Organization Admin Dashboard JavaScript
 * Manages organization settings, projects, instructors, and students
 */



// Configuration
const ORG_API_BASE = window.CONFIG?.API_URLS.ORGANIZATION;

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        Auth.logout();
        window.location.href = '../index.html';
    }
}

// Global state
let currentOrganization = null;
let currentTab = 'overview';
let currentProjectStep = 1;
let selectedTrackTemplates = [];
let ragSuggestionsCache = null;
let selectedProjectForAction = null;
let instructorAssignments = {
    tracks: {},
    modules: {}
};
let selectedStudents = [];
let availableInstructors = [];
let currentAnalyticsProject = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 ORG ADMIN DASHBOARD - Starting initialization');

    if (!Auth.isAuthenticated()) {
        console.log('❌ Not authenticated - redirecting to home');
        window.location.href = '../index.html';
        return;
    }

    const userRole = Auth.getUserRole();
    const allowedRoles = ['org_admin', 'organization_admin', 'super_admin', 'admin'];

    console.log('🔍 User role:', userRole);

    if (!allowedRoles.includes(userRole)) {
        console.log('❌ Role check failed - redirecting to home');
        window.location.href = '../index.html';
        return;
    }

    console.log('✅ Auth check passed - initializing dashboard');
    await initializeDashboard();
    setupEventListeners();
    setupTabNavigation();
});

async function initializeDashboard() {
    try {
        console.log('📊 Initialize dashboard - step 1: show spinner');
        showLoadingSpinner();

        console.log('📊 Initialize dashboard - step 2: load org data');
        // Load organization data
        await loadOrganizationData();
        console.log('✅ Organization data loaded:', currentOrganization);

        console.log('📊 Initialize dashboard - step 3: load tab content');
        // Load initial tab content
        await loadTabContent(currentTab);
        console.log('✅ Tab content loaded');

        console.log('📊 Initialize dashboard - step 4: hide spinner');
        hideLoadingSpinner();
        console.log('✅ Dashboard initialization complete');
    } catch (error) {
        console.error('❌ Error initializing dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
        hideLoadingSpinner();
    }
}

async function loadOrganizationData() {
    try {
        // In production, get org ID from user token/context
        const orgId = getCurrentUserOrgId();
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load organization data');
        }

        currentOrganization = await response.json();
        updateOrganizationDisplay();
    } catch (error) {
        // Mock data for development
        currentOrganization = {
            id: 'org-123',
            name: 'Tech University',
            slug: 'tech-university',
            description: 'Leading technology education institution',
            address: '123 University Ave, Tech City, TC 12345',
            contact_email: 'contact@techuni.edu',
            contact_phone: '+1555-123-4567',
            domain: 'https://techuni.edu',
            logo_url: '',
            member_count: 234,
            project_count: 12,
            is_active: true
        };
        updateOrganizationDisplay();
    }
}

function updateOrganizationDisplay() {
    document.getElementById('orgName').textContent = currentOrganization.name;
    document.getElementById('orgDomain').textContent = currentOrganization.domain || 'No domain set';
    document.getElementById('orgTitle').textContent = `${currentOrganization.name} Dashboard`;
    document.getElementById('orgDescription').textContent = currentOrganization.description || 'Manage your organization\'s training programs and students';
}

function setupTabNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', async function(e) {
            e.preventDefault();
            const tabName = this.dataset.tab;
            await switchTab(tabName);
        });
    });
}

async function switchTab(tabName) {
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update active tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    currentTab = tabName;
    await loadTabContent(tabName);
}

async function loadTabContent(tabName) {
    try {
        switch (tabName) {
            case 'overview':
                await loadOverviewData();
                break;
            case 'projects':
                await loadProjectsData();
                break;
            case 'instructors':
                await loadInstructorsData();
                break;
            case 'students':
                await loadStudentsData();
                break;
            case 'tracks':
                await loadTracksData();
                break;
            case 'settings':
                await loadSettingsData();
                break;
        }
    } catch (error) {
        console.error(`Error loading ${tabName} data:`, error);
        showNotification(`Failed to load ${tabName} data`, 'error');
    }
}

async function loadOverviewData() {
    // Load overview statistics
    const stats = await getOrganizationStats();

    const totalProjectsEl = document.getElementById('totalProjects');
    if (totalProjectsEl) totalProjectsEl.textContent = stats.active_projects || 0;

    const totalInstructorsEl = document.getElementById('totalInstructors');
    if (totalInstructorsEl) totalInstructorsEl.textContent = stats.instructors || 0;

    const totalStudentsEl = document.getElementById('totalStudents');
    if (totalStudentsEl) totalStudentsEl.textContent = stats.total_students || 0;

    const totalCoursesEl = document.getElementById('totalCourses');
    if (totalCoursesEl) totalCoursesEl.textContent = stats.courses || 0;

    // Load recent projects
    const recentProjects = await getRecentProjects();
    displayRecentProjects(recentProjects);

    // Load recent activity
    const recentActivity = await getRecentActivity();
    displayRecentActivity(recentActivity);
}

async function loadProjectsData() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/projects`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        let projects = [];
        if (response.ok) {
            projects = await response.json();
        } else {
            // Mock data for development
            projects = getMockProjects();
        }

        displayProjects(projects);
    } catch (error) {
        console.error('Error loading projects:', error);
        displayProjects(getMockProjects());
    }
}

async function loadInstructorsData() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        let instructors = [];
        if (response.ok) {
            instructors = await response.json();
        } else {
            // Mock data for development
            instructors = getMockInstructors();
        }

        displayInstructors(instructors);
    } catch (error) {
        console.error('Error loading instructors:', error);
        displayInstructors(getMockInstructors());
    }
}

async function loadStudentsData() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/students`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        let students = [];
        if (response.ok) {
            students = await response.json();
        } else {
            // Mock data for development
            students = getMockStudents();
        }

        displayStudents(students);
    } catch (error) {
        console.error('Error loading students:', error);
        displayStudents(getMockStudents());
    }
}

async function loadTracksData() {
    /**
     * Load tracks data from API
     *
     * BUSINESS CONTEXT:
     * Fetches all tracks for the current organization with filtering support
     *
     * TECHNICAL IMPLEMENTATION:
     * Uses organization-management API /api/v1/tracks endpoint
     */
    try {
        const orgId = currentOrganization.id;

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

        const url = `${ORG_API_BASE}/tracks?${params.toString()}`;

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        let tracks = [];
        if (response.ok) {
            tracks = await response.json();
        } else {
            console.error('Failed to load tracks:', response.statusText);
        }

        displayTracks(tracks);
        updateTracksStats(tracks);

    } catch (error) {
        console.error('Error loading tracks:', error);
        displayTracks([]);
    }
}

function displayTracks(tracks) {
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

function updateTracksStats(tracks) {
    const totalTracksEl = document.getElementById('totalTracks');
    if (totalTracksEl) {
        totalTracksEl.textContent = tracks.length;
    }
}

async function loadSettingsData() {
    console.log('📋 Loading settings data');
    console.log('Current organization:', currentOrganization);

    // If currentOrganization is not loaded, reload it
    if (!currentOrganization || !currentOrganization.id) {
        console.log('⚠️ Organization data not loaded, reloading...');
        await loadOrganizationData();
    }

    // Populate settings form with current organization data
    document.getElementById('orgNameSetting').value = currentOrganization.name || '';
    document.getElementById('orgSlugSetting').value = currentOrganization.slug || '';
    document.getElementById('orgDescriptionSetting').value = currentOrganization.description || '';
    document.getElementById('orgStreetAddressSetting').value = currentOrganization.street_address || '';
    document.getElementById('orgCitySetting').value = currentOrganization.city || '';
    document.getElementById('orgStateProvinceSetting').value = currentOrganization.state_province || '';
    document.getElementById('orgPostalCodeSetting').value = currentOrganization.postal_code || '';
    document.getElementById('orgCountrySetting').value = currentOrganization.country || 'US';
    document.getElementById('orgContactEmailSetting').value = currentOrganization.contact_email || '';
    document.getElementById('orgContactPhoneSetting').value = currentOrganization.contact_phone || '';
    document.getElementById('orgDomainSetting').value = currentOrganization.domain || '';
    document.getElementById('orgLogoSetting').value = currentOrganization.logo_url || '';

    console.log('✅ Settings form populated');

    // Set the country code for the contact phone
    if (currentOrganization.contact_phone) {
        const countrySelect = document.getElementById('orgContactPhoneCountry');
        // Extract country code from phone number if available
        const phoneNumber = currentOrganization.contact_phone;
        if (phoneNumber.startsWith('+1')) {
            countrySelect.value = '+1';
        } else if (phoneNumber.startsWith('+44')) {
            countrySelect.value = '+44';
        }
        // Add more country code detection as needed
    }

    // Initialize logo upload functionality
    initializeLogoUpload();
    
    // Load preferences (mock data for now)
    document.getElementById('autoAssignByDomain').checked = true;
    document.getElementById('enableProjectTemplates').checked = true;
    document.getElementById('enableCustomBranding').checked = false;
}

function displayProjects(projects) {
    const container = document.getElementById('projectsList');
    
    if (projects.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                <h3>No projects yet</h3>
                <p>Create your first training project to get started.</p>
                <button class="btn btn-primary" onclick="showCreateProjectModal()">Create Project</button>
            </div>
        `;
        return;
    }

    container.innerHTML = projects.map(project => `
        <div class="project-card">
            <div class="project-header">
                <div>
                    <h3 style="margin: 0 0 0.5rem 0;">${project.name}</h3>
                    <p style="margin: 0; color: var(--text-muted);">${project.description || 'No description'}</p>
                </div>
                <span class="project-status status-${project.status}">${project.status.charAt(0).toUpperCase() + project.status.slice(1)}</span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div>
                    <strong>Duration:</strong><br>
                    ${project.duration_weeks ? `${project.duration_weeks} weeks` : 'Not set'}
                </div>
                <div>
                    <strong>Participants:</strong><br>
                    ${project.current_participants || 0}/${project.max_participants || '∞'}
                </div>
                <div>
                    <strong>Start Date:</strong><br>
                    ${project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Not set'}
                </div>
            </div>

            ${project.target_roles && project.target_roles.length > 0 ? `
                <div>
                    <strong>Target Roles:</strong>
                    <div class="target-roles">
                        ${project.target_roles.map(role => `<span class="role-tag">${role}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <button class="action-btn btn-edit" onclick="editProject('${project.id}')">Edit</button>
                <button class="action-btn btn-primary" onclick="manageProjectMembers('${project.id}')">Members</button>
                ${project.status === 'draft' ? `<button class="action-btn btn-add" onclick="activateProject('${project.id}')">Activate</button>` : ''}
                <button class="action-btn btn-delete" onclick="deleteProject('${project.id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function displayInstructors(instructors) {
    const tbody = document.querySelector('#instructorsTable tbody');
    
    if (instructors.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No instructors found. Add your first instructor to get started.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = instructors.map(instructor => `
        <tr>
            <td>${instructor.first_name || ''} ${instructor.last_name || ''}</td>
            <td>${instructor.email}</td>
            <td><span class="role-badge role-${instructor.role}">${instructor.role.replace('_', ' ')}</span></td>
            <td>${new Date(instructor.joined_at).toLocaleDateString()}</td>
            <td>${instructor.last_login ? new Date(instructor.last_login).toLocaleDateString() : 'Never'}</td>
            <td><span class="status-${instructor.is_active ? 'active' : 'inactive'}">${instructor.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button class="action-btn btn-edit" onclick="editInstructor('${instructor.user_id}')">Edit</button>
                <button class="action-btn btn-delete" onclick="removeInstructor('${instructor.user_id}')">Remove</button>
            </td>
        </tr>
    `).join('');
}

function displayStudents(students) {
    const tbody = document.querySelector('#studentsTable tbody');

    if (students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No students found.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = students.map(student => `
        <tr>
            <td>${student.first_name || ''} ${student.last_name || ''}</td>
            <td>${student.email}</td>
            <td>${student.project_count || 0}</td>
            <td>${new Date(student.joined_at).toLocaleDateString()}</td>
            <td>${student.last_active ? new Date(student.last_active).toLocaleDateString() : 'Never'}</td>
            <td><span class="status-${student.is_active ? 'active' : 'inactive'}">${student.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button class="action-btn btn-edit" onclick="editStudent('${student.user_id}')">Edit</button>
                <button class="action-btn btn-delete" onclick="removeStudent('${student.user_id}')">Remove</button>
            </td>
        </tr>
    `).join('');
}

function setupEventListeners() {
    // Form submissions - with null checks for safety
    const addInstructorForm = document.getElementById('addInstructorForm');
    if (addInstructorForm) {
        addInstructorForm.addEventListener('submit', handleAddInstructor);
    }

    const createProjectForm = document.getElementById('createProjectForm');
    if (createProjectForm) {
        createProjectForm.addEventListener('submit', handleCreateProject);
    }

    const addStudentForm = document.getElementById('addStudentForm');
    if (addStudentForm) {
        addStudentForm.addEventListener('submit', handleAddStudent);
    }

    const orgSettingsForm = document.getElementById('orgSettingsForm');
    if (orgSettingsForm) {
        orgSettingsForm.addEventListener('submit', handleUpdateSettings);
    }

    const orgPreferencesForm = document.getElementById('orgPreferencesForm');
    if (orgPreferencesForm) {
        orgPreferencesForm.addEventListener('submit', handleUpdatePreferences);
    }

    // Auto-generate slug from project name
    const projectNameInput = document.getElementById('projectName');
    if (projectNameInput) {
        projectNameInput.addEventListener('input', function(e) {
            const slug = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            const projectSlugInput = document.getElementById('projectSlug');
            if (projectSlugInput) {
                projectSlugInput.value = slug;
            }
        });
    }

    // Cancel button for organization settings
    const cancelBtn = document.getElementById('cancelOrgSettingsBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            cancelOrganizationChanges();
        });
    }
}

// Modal functions
function showCreateProjectModal() {
    const modal = document.getElementById('createProjectModal');
    const modalContent = modal.querySelector('.draggable-modal');

    // Reset position
    if (modalContent) {
        modalContent.style.transform = 'translate(0px, 0px)';
    }

    modal.style.display = 'block';
}

function showAddInstructorModal() {
    document.getElementById('addInstructorModal').style.display = 'block';
}

function showAddStudentModal() {
    document.getElementById('addStudentModal').style.display = 'block';
}

async function showCreateTrackModal() {
    /**
     * Show create track modal
     *
     * BUSINESS CONTEXT:
     * Allows organization admins to create new learning tracks
     */
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
    await loadProjectsForTrackForm();

    // Show modal
    modal.style.display = 'block';
}

async function loadProjectsForTrackForm() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/projects`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
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

async function submitTrack(event) {
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

        const url = isUpdate ? `${ORG_API_BASE}/tracks/${trackId}` : `${ORG_API_BASE}/tracks`;
        const method = isUpdate ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
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

async function viewTrackDetails(trackId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/tracks/${trackId}`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
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
        document.getElementById('trackDetailsModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading track details:', error);
        showNotification('Failed to load track details', 'error');
    }
}

function editTrackFromDetails() {
    const trackId = document.getElementById('trackDetailsModal').dataset.trackId;
    if (trackId) {
        closeModal('trackDetailsModal');
        editTrack(trackId);
    }
}

async function editTrack(trackId) {
    try {
        // Fetch track details
        const response = await fetch(`${ORG_API_BASE}/tracks/${trackId}`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
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
        document.getElementById('trackModal').style.display = 'block';

    } catch (error) {
        console.error('Error loading track for edit:', error);
        showNotification('Failed to load track', 'error');
    }
}

function deleteTrack(trackId) {
    // Store track ID
    document.getElementById('deleteTrackId').value = trackId;

    // Show warning
    const warning = document.getElementById('deleteTrackWarning');
    if (warning) {
        warning.textContent = 'This action cannot be undone. All enrollments will be removed.';
    }

    // Show modal
    document.getElementById('deleteTrackModal').style.display = 'block';
}

async function confirmDeleteTrack() {
    const trackId = document.getElementById('deleteTrackId').value;

    if (!trackId) return;

    try {
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

        showNotification('Track deleted successfully', 'success');
        closeModal('deleteTrackModal');
        loadTracksData();

    } catch (error) {
        console.error('Error deleting track:', error);
        showNotification(error.message, 'error');
    }
}

// Helper function: Parse comma-separated values
function parseCommaSeparated(value) {
    if (!value) return [];
    return value.split(',').map(v => v.trim()).filter(v => v.length > 0);
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    // Reset form if it exists
    const form = document.querySelector(`#${modalId} form`);
    if (form) {
        form.reset();
    }
}

// Event handlers
async function handleAddInstructor(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const instructorData = {
            email: formData.get('email'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'),
            role: formData.get('role'),
            send_welcome_email: formData.get('send_welcome_email') === 'on'
        };

        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(instructorData)
        });

        if (response.ok) {
            showNotification('Instructor added successfully', 'success');
            closeModal('addInstructorModal');
            if (currentTab === 'instructors') {
                await loadInstructorsData();
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to add instructor', 'error');
        }
    } catch (error) {
        console.error('Error adding instructor:', error);
        showNotification('Failed to add instructor', 'error');
    }
}

async function handleCreateProject(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const targetRoles = formData.get('target_roles')
            ? formData.get('target_roles').split('\n').map(role => role.trim()).filter(role => role)
            : [];

        const projectData = {
            name: formData.get('name'),
            slug: formData.get('slug'),
            description: formData.get('description'),
            target_roles: targetRoles,
            duration_weeks: formData.get('duration_weeks') ? parseInt(formData.get('duration_weeks')) : null,
            max_participants: formData.get('max_participants') ? parseInt(formData.get('max_participants')) : null,
            start_date: formData.get('start_date') || null,
            end_date: formData.get('end_date') || null
        };

        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/projects`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });

        if (response.ok) {
            showNotification('Project created successfully', 'success');
            closeModal('createProjectModal');
            if (currentTab === 'projects') {
                await loadProjectsData();
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to create project', 'error');
        }
    } catch (error) {
        console.error('Error creating project:', error);
        showNotification('Failed to create project', 'error');
    }
}

async function handleAddStudent(e) {
    e.preventDefault();

    try {
        const formData = new FormData(e.target);
        const studentData = {
            user_email: formData.get('user_email'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'),
            send_welcome_email: formData.get('send_welcome_email') === 'on',
            role: 'student'
        };

        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/students`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });

        if (response.ok) {
            showNotification('Student added successfully', 'success');
            closeModal('addStudentModal');
            if (currentTab === 'students') {
                await loadStudentsData();
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to add student', 'error');
        }
    } catch (error) {
        console.error('Error adding student:', error);
        showNotification('Failed to add student', 'error');
    }
}

async function handleUpdateSettings(e) {
    e.preventDefault();
    
    try {
        // Show saving state
        const saveBtn = document.getElementById('saveOrgSettingsBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        saveBtn.disabled = true;

        const formData = new FormData(e.target);
        
        // Combine country code with phone number
        const countryCode = document.getElementById('orgContactPhoneCountry').value;
        const phoneNumber = formData.get('contact_phone');
        const fullPhoneNumber = phoneNumber ? `${countryCode}${phoneNumber.replace(/^\+?[\d\s\-\(\)]*/, '')}` : '';

        const settingsData = {
            name: formData.get('name'),
            description: formData.get('description'),
            address: formData.get('address'),
            contact_email: formData.get('contact_email'),
            contact_phone: fullPhoneNumber,
            domain: formData.get('domain'),
            logo_url: formData.get('logo_url')
        };

        // Handle logo file upload if present
        const logoFile = document.getElementById('orgLogoFile').files[0];
        if (logoFile) {
            try {
                const logoUrl = await uploadLogoFile(logoFile);
                settingsData.logo_url = logoUrl;
            } catch (uploadError) {
                console.error('Logo upload failed:', uploadError);
                showNotification('Logo upload failed, but other settings will be saved', 'warning');
            }
        }

        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settingsData)
        });

        if (response.ok) {
            const updatedOrg = await response.json();
            showNotification('Organization information updated successfully', 'success');
            // Update local organization data
            Object.assign(currentOrganization, updatedOrg);
            updateOrganizationDisplay();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update organization information', 'error');
        }
    } catch (error) {
        console.error('Error updating settings:', error);
        showNotification('Failed to update organization information', 'error');
    } finally {
        // Restore button state
        const saveBtn = document.getElementById('saveOrgSettingsBtn');
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }
}

async function handleUpdatePreferences(e) {
    e.preventDefault();
    showNotification('Preferences updated successfully', 'success');
}

// Action functions
async function removeInstructor(userId) {
    if (!confirm('Are you sure you want to remove this instructor?')) {
        return;
    }

    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`
            }
        });

        if (response.ok) {
            showNotification('Instructor removed successfully', 'success');
            await loadInstructorsData();
        } else {
            showNotification('Failed to remove instructor', 'error');
        }
    } catch (error) {
        console.error('Error removing instructor:', error);
        showNotification('Failed to remove instructor', 'error');
    }
}

// Utility functions
function getCurrentUserOrgId() {
    // Extract organization_id from current user data
    const user = Auth.getCurrentUser();
    if (user && user.organization_id) {
        console.log('📋 Using organization_id from user:', user.organization_id);
        return user.organization_id;
    }

    // Fallback to hardcoded value for development
    console.warn('⚠️ No organization_id found in user data, using fallback');
    return 'org-123';
}

function showLoadingSpinner() {
    // Implementation depends on your loading spinner design
}

function hideLoadingSpinner() {
    // Implementation depends on your loading spinner design
}

// Mock data functions for development
function getMockProjects() {
    return [
        {
            id: 'project-1',
            name: 'Graduate Developer Training Program',
            slug: 'grad-dev-program',
            description: 'Comprehensive training program for new graduate developers',
            target_roles: ['Application Developer', 'DevOps Engineer'],
            duration_weeks: 16,
            max_participants: 50,
            current_participants: 32,
            start_date: '2024-01-15',
            end_date: '2024-05-15',
            status: 'active'
        },
        {
            id: 'project-2',
            name: 'Business Analysis Bootcamp',
            slug: 'ba-bootcamp',
            description: 'Intensive business analysis training',
            target_roles: ['Business Analyst', 'Product Manager'],
            duration_weeks: 12,
            max_participants: 30,
            current_participants: 15,
            start_date: '2024-02-01',
            status: 'draft'
        }
    ];
}

function getMockInstructors() {
    return [
        {
            user_id: 'user-1',
            email: 'john.doe@techuni.edu',
            first_name: 'John',
            last_name: 'Doe',
            role: 'instructor',
            is_active: true,
            joined_at: '2024-01-01T00:00:00Z',
            last_login: '2024-01-20T10:30:00Z'
        },
        {
            user_id: 'user-2',
            email: 'jane.smith@techuni.edu',
            first_name: 'Jane',
            last_name: 'Smith',
            role: 'project_manager',
            is_active: true,
            joined_at: '2024-01-15T00:00:00Z',
            last_login: '2024-01-19T14:20:00Z'
        }
    ];
}

function getMockStudents() {
    return [
        {
            user_id: 'user-3',
            email: 'student1@techuni.edu',
            first_name: 'Alice',
            last_name: 'Johnson',
            project_count: 2,
            is_active: true,
            joined_at: '2024-01-10T00:00:00Z',
            last_active: '2024-09-28T00:00:00Z'
        },
        {
            user_id: 'user-4',
            email: 'student2@techuni.edu',
            first_name: 'Bob',
            last_name: 'Wilson',
            project_count: 1,
            is_active: true,
            joined_at: '2024-01-12T00:00:00Z',
            last_active: '2024-09-30T00:00:00Z'
        },
        {
            user_id: 'user-5',
            email: 'student3@techuni.edu',
            first_name: 'Charlie',
            last_name: 'Brown',
            project_count: 3,
            is_active: true,
            joined_at: '2024-02-01T00:00:00Z',
            last_active: '2024-10-01T00:00:00Z'
        }
    ];
}

async function getOrganizationStats() {
    return {
        active_projects: 3,
        instructors: 2,
        total_students: 3,
        courses: 24
    };
}

async function getRecentProjects() {
    return getMockProjects().slice(0, 3);
}

async function getRecentActivity() {
    return [
        { action: 'New instructor added', user: 'John Doe', time: '2 hours ago' },
        { action: 'Project "BA Bootcamp" created', user: 'Jane Smith', time: '1 day ago' },
        { action: '15 students enrolled', user: 'System', time: '2 days ago' }
    ];
}

function displayRecentProjects(projects) {
    const container = document.getElementById('recentProjects');
    if (projects.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No recent projects</p>';
        return;
    }

    container.innerHTML = projects.map(project => `
        <div style="padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 0.5rem;">
            <strong>${project.name}</strong><br>
            <small style="color: var(--text-muted);">${project.current_participants || 0} participants</small>
        </div>
    `).join('');
}

function displayRecentActivity(activities) {
    const container = document.getElementById('recentActivity');
    if (activities.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No recent activity</p>';
        return;
    }

    container.innerHTML = activities.map(activity => `
        <div style="padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 0.5rem;">
            <div>${activity.action}</div>
            <small style="color: var(--text-muted);">by ${activity.user} • ${activity.time}</small>
        </div>
    `).join('');
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

// =============================================================================
// PROJECT CREATION WITH RAG INTEGRATION
// =============================================================================

// Project creation step navigation
function nextProjectStep() {
    if (currentProjectStep === 1) {
        // Validate step 1 form
        const form = document.getElementById('createProjectForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        // Move to step 2 and get RAG suggestions
        showProjectStep(2);
        generateRAGSuggestions();
    } else if (currentProjectStep === 2) {
        // Move to step 3 and load track templates
        showProjectStep(3);
        loadTrackTemplates();
    }
}

function previousProjectStep() {
    if (currentProjectStep > 1) {
        showProjectStep(currentProjectStep - 1);
    }
}

function showProjectStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.project-step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Update step indicators
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 === stepNumber) {
            step.classList.add('active');
        } else if (index + 1 < stepNumber) {
            step.classList.add('completed');
        }
    });
    
    // Show current step
    document.getElementById(`projectStep${stepNumber}`).classList.add('active');
    currentProjectStep = stepNumber;
}

async function generateRAGSuggestions() {
    try {
        const formData = new FormData(document.getElementById('createProjectForm'));
        const projectDescription = formData.get('description');
        const targetRoles = formData.get('target_roles');
        
        if (!projectDescription.trim()) {
            showNotification('Please provide a project description to get AI suggestions', 'warning');
            return;
        }
        
        // Show loading indicator
        document.getElementById('ragLoadingIndicator').style.display = 'block';
        document.getElementById('ragSuggestions').style.display = 'none';
        
        // Query RAG service for project planning assistance
        const ragQuery = `Create training project for: ${projectDescription}. Target roles: ${targetRoles || 'General'}`;
        
        const response = await fetch(`${window.CONFIG?.API_URLS.RAG}/api/v1/rag/query`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: ragQuery,
                domain: 'project_planning',
                n_results: 5,
                metadata_filter: {
                    content_type: 'project_planning',
                    target_roles: targetRoles?.split('\n').map(r => r.trim()).filter(r => r) || []
                }
            })
        });
        
        if (response.ok) {
            const ragResult = await response.json();
            ragSuggestionsCache = ragResult;
            displayRAGSuggestions(ragResult, projectDescription, targetRoles);
        } else {
            // Fallback to mock suggestions if RAG service is unavailable
            const mockSuggestions = generateMockRAGSuggestions(projectDescription, targetRoles);
            displayRAGSuggestions(mockSuggestions, projectDescription, targetRoles);
        }
    } catch (error) {
        console.error('Error generating RAG suggestions:', error);
        // Show mock suggestions as fallback
        const mockSuggestions = generateMockRAGSuggestions(
            document.getElementById('projectDescription').value,
            document.getElementById('projectTargetRoles').value
        );
        displayRAGSuggestions(mockSuggestions);
    }
}

function displayRAGSuggestions(ragResult, projectDescription, targetRoles) {
    // Hide loading and show suggestions
    document.getElementById('ragLoadingIndicator').style.display = 'none';
    document.getElementById('ragSuggestions').style.display = 'block';
    
    // Display project insights
    const insightsContainer = document.getElementById('projectInsights');
    insightsContainer.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <strong>Project Analysis:</strong>
            <p>${ragResult.enhanced_context || ragResult.analysis || 'AI analysis of your project description suggests a comprehensive training approach.'}</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div class="insight-metric">
                <strong>Recommended Duration:</strong><br>
                <span style="color: var(--primary-color);">${ragResult.recommended_duration || '12-16 weeks'}</span>
            </div>
            <div class="insight-metric">
                <strong>Difficulty Level:</strong><br>
                <span style="color: var(--info-color);">${ragResult.difficulty_level || 'Intermediate'}</span>
            </div>
            <div class="insight-metric">
                <strong>Optimal Cohort Size:</strong><br>
                <span style="color: var(--success-color);">${ragResult.cohort_size || '20-30 participants'}</span>
            </div>
        </div>
    `;
    
    // Display recommended tracks
    const tracksContainer = document.getElementById('recommendedTracks');
    const recommendedTracks = ragResult.recommended_tracks || [
        { name: 'Foundation Track', description: 'Core concepts and fundamentals' },
        { name: 'Practical Application Track', description: 'Hands-on exercises and projects' },
        { name: 'Advanced Topics Track', description: 'Deep dive into specialized areas' }
    ];
    
    tracksContainer.innerHTML = recommendedTracks.map(track => `
        <div style="background: white; padding: 1rem; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid var(--info-color);">
            <strong>${track.name}</strong><br>
            <small style="color: var(--text-muted);">${track.description}</small>
        </div>
    `).join('');
    
    // Display suggested learning objectives
    const objectivesContainer = document.getElementById('suggestedObjectives');
    const objectives = ragResult.learning_objectives || [
        'Understand core principles and concepts',
        'Apply knowledge through practical exercises',
        'Demonstrate proficiency in key skills',
        'Collaborate effectively in team environments',
        'Present and communicate solutions clearly'
    ];
    
    objectivesContainer.innerHTML = `
        <ul style="margin: 0; padding-left: 1.5rem;">
            ${objectives.map(obj => `<li style="margin-bottom: 0.5rem;">${obj}</li>`).join('')}
        </ul>
    `;
}

function generateMockRAGSuggestions(description, targetRoles) {
    return {
        analysis: `Based on your project description, this appears to be a ${targetRoles ? 'role-specific' : 'general'} training program that would benefit from a structured, multi-track approach.`,
        recommended_duration: '14 weeks',
        difficulty_level: 'Intermediate',
        cohort_size: '25 participants',
        recommended_tracks: [
            { name: 'Foundation Track', description: 'Essential knowledge and core concepts' },
            { name: 'Hands-On Track', description: 'Practical exercises and real-world applications' },
            { name: 'Capstone Track', description: 'Final project and portfolio development' }
        ],
        learning_objectives: [
            'Master fundamental concepts and principles',
            'Apply knowledge through practical projects',
            'Develop professional skills and competencies',
            'Build a comprehensive portfolio',
            'Demonstrate readiness for advanced roles'
        ]
    };
}

async function regenerateAISuggestions() {
    ragSuggestionsCache = null;
    await generateRAGSuggestions();
}

async function loadTrackTemplates() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/track-templates`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        let templates = [];
        if (response.ok) {
            templates = await response.json();
        } else {
            // Use mock track templates
            templates = getMockTrackTemplates();
        }
        
        displayTrackTemplates(templates);
    } catch (error) {
        console.error('Error loading track templates:', error);
        displayTrackTemplates(getMockTrackTemplates());
    }
}

function displayTrackTemplates(templates) {
    const container = document.getElementById('trackTemplates');
    
    container.innerHTML = templates.map(template => `
        <div class="track-template-card" onclick="toggleTrackTemplate('${template.id}')" data-track-id="${template.id}">
            <div class="track-category">${template.template_category || 'General'}</div>
            <h4 style="margin: 0.5rem 0;">${template.name}</h4>
            <p style="color: var(--text-muted); font-size: 0.875rem; margin: 0.5rem 0;">${template.description}</p>
            <div class="track-duration">
                ⏱️ ${template.estimated_duration_hours} hours
                ${template.difficulty_level ? `• 📊 ${template.difficulty_level}` : ''}
            </div>
        </div>
    `).join('');
}

function toggleTrackTemplate(templateId) {
    const card = document.querySelector(`[data-track-id="${templateId}"]`);
    
    if (card.classList.contains('selected')) {
        card.classList.remove('selected');
        selectedTrackTemplates = selectedTrackTemplates.filter(id => id !== templateId);
    } else {
        card.classList.add('selected');
        selectedTrackTemplates.push(templateId);
    }
    
    updateSelectedTracksDisplay();
}

function updateSelectedTracksDisplay() {
    const container = document.getElementById('selectedTracks');
    const listContainer = document.getElementById('selectedTracksList');
    
    if (selectedTrackTemplates.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    // Get template details for selected tracks
    const templates = getMockTrackTemplates(); // In production, get from loaded templates
    const selectedTemplates = templates.filter(t => selectedTrackTemplates.includes(t.id));
    
    listContainer.innerHTML = selectedTemplates.map(template => `
        <div class="selected-track-item">
            <div>
                <strong>${template.name}</strong><br>
                <small style="color: var(--text-muted);">${template.estimated_duration_hours} hours • ${template.difficulty_level}</small>
            </div>
            <button class="btn btn-sm btn-secondary" onclick="toggleTrackTemplate('${template.id}')">Remove</button>
        </div>
    `).join('');
}

async function finalizeProjectCreation() {
    try {
        const formData = new FormData(document.getElementById('createProjectForm'));
        const targetRoles = formData.get('target_roles') 
            ? formData.get('target_roles').split('\n').map(role => role.trim()).filter(role => role)
            : [];

        const projectData = {
            name: formData.get('name'),
            slug: formData.get('slug'),
            description: formData.get('description'),
            target_roles: targetRoles,
            duration_weeks: formData.get('duration_weeks') ? parseInt(formData.get('duration_weeks')) : null,
            max_participants: formData.get('max_participants') ? parseInt(formData.get('max_participants')) : null,
            start_date: formData.get('start_date') || null,
            end_date: formData.get('end_date') || null,
            selected_track_templates: selectedTrackTemplates,
            rag_context_used: ragSuggestionsCache ? JSON.stringify(ragSuggestionsCache) : null
        };

        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/projects`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });

        if (response.ok) {
            const createdProject = await response.json();
            showNotification('Project created successfully! Navigate to the project dashboard to add modules.', 'success');
            closeModal('createProjectModal');
            
            // Reset modal state
            resetProjectCreationModal();
            
            if (currentTab === 'projects') {
                await loadProjectsData();
            }
            
            // Optionally redirect to project dashboard
            if (createdProject.id) {
                setTimeout(() => {
                    if (confirm('Would you like to go to the project dashboard to set up tracks and modules?')) {
                        window.location.href = `/project-dashboard.html?project=${createdProject.id}`;
                    }
                }, 1000);
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to create project', 'error');
        }
    } catch (error) {
        console.error('Error creating project:', error);
        showNotification('Failed to create project', 'error');
    }
}

function resetProjectCreationModal() {
    currentProjectStep = 1;
    selectedTrackTemplates = [];
    ragSuggestionsCache = null;
    
    // Reset form
    document.getElementById('createProjectForm').reset();
    
    // Reset steps
    showProjectStep(1);
    
    // Clear displays
    document.getElementById('ragSuggestions').style.display = 'none';
    document.getElementById('selectedTracks').style.display = 'none';
}

function showCustomTrackForm() {
    showNotification('Custom track creation will open in a new modal - coming soon!', 'info');
    // TODO: Implement custom track creation modal
}

function getMockTrackTemplates() {
    return [
        {
            id: 'template-1',
            name: 'Application Development Track',
            description: 'Comprehensive full-stack development training',
            template_category: 'Software Development',
            estimated_duration_hours: 160,
            difficulty_level: 'intermediate'
        },
        {
            id: 'template-2',
            name: 'Business Analyst Track',
            description: 'Requirements analysis and stakeholder management',
            template_category: 'Business Analysis',
            estimated_duration_hours: 120,
            difficulty_level: 'beginner'
        },
        {
            id: 'template-3',
            name: 'DevOps Engineer Track',
            description: 'Infrastructure automation and CI/CD pipelines',
            template_category: 'DevOps',
            estimated_duration_hours: 200,
            difficulty_level: 'advanced'
        },
        {
            id: 'template-4',
            name: 'Data Science Track',
            description: 'Data analysis and machine learning fundamentals',
            template_category: 'Data Science',
            estimated_duration_hours: 180,
            difficulty_level: 'intermediate'
        }
    ];
}

// =============================================================================
// PROJECT MANAGEMENT FUNCTIONS
// =============================================================================

async function editProject(projectId) {
    // Navigate to project dashboard for editing
    window.location.href = `/project-dashboard.html?project=${projectId}`;
}

async function manageProjectMembers(projectId) {
    // Navigate to project members management
    window.location.href = `/project-members.html?project=${projectId}`;
}

async function activateProject(projectId) {
    if (!confirm('Are you sure you want to activate this project? This will make it available to participants.')) {
        return;
    }

    try {
        const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/activate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('Project activated successfully', 'success');
            await loadProjectsData();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to activate project', 'error');
        }
    } catch (error) {
        console.error('Error activating project:', error);
        showNotification('Failed to activate project', 'error');
    }
}

async function deleteProject(projectId) {
    if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${ORG_API_BASE}/projects/${projectId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`
            }
        });

        if (response.ok) {
            showNotification('Project deleted successfully', 'success');
            await loadProjectsData();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to delete project', 'error');
        }
    } catch (error) {
        console.error('Error deleting project:', error);
        showNotification('Failed to delete project', 'error');
    }
}

// Placeholder functions for instructor and student management
function editInstructor(userId) {
    showNotification('Edit instructor functionality coming soon', 'info');
}

function editStudent(userId) {
    showNotification('Edit student functionality coming soon', 'info');
}

function removeStudent(userId) {
    if (confirm('Are you sure you want to remove this student?')) {
        showNotification('Student removal functionality coming soon', 'info');
    }
}

// =============================================================================
// ENHANCED PROJECT MANAGEMENT FUNCTIONS
// =============================================================================

function filterProjects() {
    const filterValue = document.getElementById('projectStatusFilter').value;
    // In production, this would filter the displayed projects
    showNotification(`Filtering projects by status: ${filterValue || 'All'}`, 'info');
}

async function instantiateProject(projectId) {
    selectedProjectForAction = projectId;
    
    // Load project details for instantiation modal
    try {
        // In production, fetch actual project details
        const projectDetails = {
            id: projectId,
            name: 'Graduate Developer Training Program',
            description: 'Comprehensive training program for new graduate developers with hands-on projects and mentorship',
            target_roles: ['Application Developer', 'DevOps Engineer'],
            duration_weeks: 16,
            max_participants: 50,
            tracks_count: 2,
            modules_count: 8,
            has_tracks: true
        };
        
        displayProjectInstantiationDetails(projectDetails);
        document.getElementById('instantiateProjectModal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading project details for instantiation:', error);
        showNotification('Failed to load project details', 'error');
    }
}

function displayProjectInstantiationDetails(project) {
    const container = document.getElementById('projectInstantiationDetails');
    container.innerHTML = `
        <div class="project-details-summary">
            <h3>${project.name}</h3>
            <p style="margin: 1rem 0;">${project.description}</p>
            
            <div class="project-details-grid">
                <div class="detail-item">
                    <span class="detail-label">Target Roles</span>
                    <span class="detail-value">${project.target_roles.join(', ')}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Duration</span>
                    <span class="detail-value">${project.duration_weeks} weeks</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Max Participants</span>
                    <span class="detail-value">${project.max_participants}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Existing Tracks</span>
                    <span class="detail-value">${project.tracks_count} tracks</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Existing Modules</span>
                    <span class="detail-value">${project.modules_count} modules</span>
                </div>
            </div>
            
            ${!project.has_tracks ? `
                <div style="margin-top: 1rem; padding: 1rem; background: var(--warning-color); color: white; border-radius: 6px;">
                    <strong>⚠️ No tracks found!</strong> Default tracks and modules will be created based on the project description and target roles.
                </div>
            ` : ''}
        </div>
    `;
}

async function confirmProjectInstantiation() {
    const processWithAI = document.getElementById('processWithAI').checked;
    
    try {
        const response = await fetch(`${ORG_API_BASE}/projects/${selectedProjectForAction}/instantiate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                process_with_ai: processWithAI,
                create_default_content: true
            })
        });

        if (response.ok) {
            showNotification('Project instantiated successfully! Students can now be enrolled.', 'success');
            closeModal('instantiateProjectModal');
            await loadProjectsData();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to instantiate project', 'error');
        }
    } catch (error) {
        console.error('Error instantiating project:', error);
        showNotification('Failed to instantiate project', 'error');
    }
}

// =============================================================================
// INSTRUCTOR ASSIGNMENT FUNCTIONS
// =============================================================================

async function showInstructorAssignmentModal(projectId) {
    selectedProjectForAction = projectId;
    
    try {
        // Load available instructors
        await loadAvailableInstructors();
        
        // Load project tracks and modules
        const tracks = await loadProjectTracksForAssignment(projectId);
        const modules = await loadProjectModulesForAssignment(projectId);
        
        // Display assignment interface
        displayTrackAssignments(tracks);
        displayModuleAssignments(modules);
        
        document.getElementById('instructorAssignmentModal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading instructor assignment data:', error);
        showNotification('Failed to load instructor assignment interface', 'error');
    }
}

async function loadAvailableInstructors() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            availableInstructors = await response.json();
        } else {
            // Mock instructors
            availableInstructors = [
                { id: 'instructor-1', name: 'Dr. Sarah Johnson', email: 'sarah.johnson@techuni.edu', specialties: ['JavaScript', 'React', 'Node.js'] },
                { id: 'instructor-2', name: 'Prof. Michael Chen', email: 'michael.chen@techuni.edu', specialties: ['Python', 'Data Science', 'Machine Learning'] },
                { id: 'instructor-3', name: 'Dr. Emily Rodriguez', email: 'emily.rodriguez@techuni.edu', specialties: ['DevOps', 'Cloud Computing', 'Docker'] },
                { id: 'instructor-4', name: 'Prof. David Kim', email: 'david.kim@techuni.edu', specialties: ['Database Design', 'SQL', 'System Architecture'] }
            ];
        }
    } catch (error) {
        console.error('Error loading instructors:', error);
        availableInstructors = [];
    }
}

async function loadProjectTracksForAssignment(projectId) {
    // Mock tracks data
    return [
        { id: 'track-1', name: 'Foundation Track', description: 'Programming fundamentals', assigned_instructors: [] },
        { id: 'track-2', name: 'Web Development Track', description: 'Modern web development', assigned_instructors: [] }
    ];
}

async function loadProjectModulesForAssignment(projectId) {
    // Mock modules data
    return [
        { 
            id: 'module-1', 
            name: 'Development Environment Setup', 
            track_name: 'Foundation Track',
            assigned_instructors: [],
            required_instructors: 2
        },
        { 
            id: 'module-2', 
            name: 'Programming Fundamentals', 
            track_name: 'Foundation Track',
            assigned_instructors: [],
            required_instructors: 2
        },
        { 
            id: 'module-3', 
            name: 'Frontend Development', 
            track_name: 'Web Development Track',
            assigned_instructors: [],
            required_instructors: 2
        }
    ];
}

function displayTrackAssignments(tracks) {
    const container = document.getElementById('trackAssignmentList');
    container.innerHTML = tracks.map(track => `
        <div class="instructor-assignment-item">
            <h4>${track.name}</h4>
            <p style="margin: 0 0 1rem 0; color: var(--text-muted);">${track.description}</p>
            
            <div class="instructor-selector">
                <select onchange="addInstructorToTrack('${track.id}', this.value, this)" style="width: 100%;">
                    <option value="">Select instructor to assign...</option>
                    ${availableInstructors.map(instructor => `
                        <option value="${instructor.id}">${instructor.name} (${instructor.specialties.join(', ')})</option>
                    `).join('')}
                </select>
                <select onchange="setInstructorRole('${track.id}', this.value)">
                    <option value="instructor">Instructor</option>
                    <option value="lead_instructor">Lead Instructor</option>
                    <option value="assistant">Assistant</option>
                </select>
                <button type="button" class="btn btn-sm btn-primary" onclick="assignSelectedInstructor('${track.id}')">Assign</button>
            </div>
            
            <div class="assigned-instructors" id="trackInstructors-${track.id}">
                ${track.assigned_instructors.map(instructor => `
                    <span class="instructor-tag">
                        ${instructor.name} (${instructor.role})
                        <button class="remove-btn" onclick="removeInstructorFromTrack('${track.id}', '${instructor.id}')">×</button>
                    </span>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function displayModuleAssignments(modules) {
    const container = document.getElementById('moduleAssignmentList');
    container.innerHTML = modules.map(module => `
        <div class="instructor-assignment-item">
            <h4>${module.name} <span style="font-size: 0.875rem; color: var(--text-muted);">(${module.track_name})</span></h4>
            
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                <span style="font-size: 0.875rem;">
                    <strong>Required instructors:</strong> ${module.required_instructors}
                </span>
                <span style="font-size: 0.875rem; color: ${module.assigned_instructors.length >= module.required_instructors ? 'var(--success-color)' : 'var(--error-color)'};">
                    <strong>Currently assigned:</strong> ${module.assigned_instructors.length}
                </span>
            </div>
            
            <div class="instructor-selector">
                <select onchange="addInstructorToModule('${module.id}', this.value, this)" style="width: 100%;">
                    <option value="">Select instructor to assign...</option>
                    ${availableInstructors.map(instructor => `
                        <option value="${instructor.id}">${instructor.name} (${instructor.specialties.join(', ')})</option>
                    `).join('')}
                </select>
                <select onchange="setModuleInstructorRole('${module.id}', this.value)">
                    <option value="co_instructor">Co-Instructor</option>
                    <option value="lead_instructor">Lead Instructor</option>
                    <option value="assistant">Assistant</option>
                </select>
                <button type="button" class="btn btn-sm btn-primary" onclick="assignSelectedModuleInstructor('${module.id}')">Assign</button>
            </div>
            
            <div class="assigned-instructors" id="moduleInstructors-${module.id}">
                ${module.assigned_instructors.map(instructor => `
                    <span class="instructor-tag">
                        ${instructor.name} (${instructor.role})
                        <button class="remove-btn" onclick="removeInstructorFromModule('${module.id}', '${instructor.id}')">×</button>
                    </span>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function switchAssignmentTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.assignment-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.assignment-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + 'AssignmentTab').classList.add('active');
    
    // Activate selected tab button
    event.target.classList.add('active');
}

async function saveInstructorAssignments() {
    try {
        const response = await fetch(`${ORG_API_BASE}/projects/${selectedProjectForAction}/instructor-assignments`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(instructorAssignments)
        });

        if (response.ok) {
            showNotification('Instructor assignments saved successfully', 'success');
            closeModal('instructorAssignmentModal');
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to save instructor assignments', 'error');
        }
    } catch (error) {
        console.error('Error saving instructor assignments:', error);
        showNotification('Failed to save instructor assignments', 'error');
    }
}

// =============================================================================
// STUDENT ENROLLMENT FUNCTIONS  
// =============================================================================

async function showStudentEnrollmentModal(projectId) {
    selectedProjectForAction = projectId;
    selectedStudents = [];
    
    try {
        // Load available students and project tracks
        await loadAvailableStudents();
        await loadProjectTracksForEnrollment(projectId);
        
        document.getElementById('studentEnrollmentModal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading student enrollment data:', error);
        showNotification('Failed to load student enrollment interface', 'error');
    }
}

async function loadAvailableStudents() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/students`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const students = await response.json();
            displayAvailableStudents(students);
        } else {
            // Mock students
            const mockStudents = [
                { id: 'student-1', name: 'Alice Johnson', email: 'alice@techuni.edu', enrolled: false },
                { id: 'student-2', name: 'Bob Wilson', email: 'bob@techuni.edu', enrolled: false },
                { id: 'student-3', name: 'Carol Davis', email: 'carol@techuni.edu', enrolled: true },
                { id: 'student-4', name: 'David Brown', email: 'david@techuni.edu', enrolled: false },
                { id: 'student-5', name: 'Eva Garcia', email: 'eva@techuni.edu', enrolled: false }
            ];
            displayAvailableStudents(mockStudents);
        }
    } catch (error) {
        console.error('Error loading students:', error);
        displayAvailableStudents([]);
    }
}

async function loadProjectTracksForEnrollment(projectId) {
    const tracks = [
        { id: 'track-1', name: 'Foundation Track' },
        { id: 'track-2', name: 'Web Development Track' }
    ];
    
    const trackSelect = document.getElementById('enrollmentTrackSelect');
    trackSelect.innerHTML = '<option value="">Select Track...</option>' +
        tracks.map(track => `<option value="${track.id}">${track.name}</option>`).join('');
}

function displayAvailableStudents(students) {
    const container = document.getElementById('availableStudentsList');
    container.innerHTML = students.map(student => `
        <div class="student-item ${selectedStudents.includes(student.id) ? 'selected' : ''}" 
             onclick="toggleStudentSelection('${student.id}')">
            <div class="student-info">
                <div class="student-name">${student.name}</div>
                <div class="student-email">${student.email}</div>
            </div>
            <div class="enrollment-status status-${student.enrolled ? 'enrolled' : 'not-enrolled'}">
                ${student.enrolled ? 'Enrolled' : 'Available'}
            </div>
        </div>
    `).join('');
}

function toggleStudentSelection(studentId) {
    const index = selectedStudents.indexOf(studentId);
    if (index > -1) {
        selectedStudents.splice(index, 1);
    } else {
        selectedStudents.push(studentId);
    }
    
    // Update UI
    const studentElement = document.querySelector(`[onclick="toggleStudentSelection('${studentId}')"]`);
    studentElement.classList.toggle('selected');
    
    updateEnrollmentSummary();
}

function updateEnrollmentSummary() {
    const selectedCount = selectedStudents.length;
    const trackSelect = document.getElementById('enrollmentTrackSelect');
    const selectedTrack = trackSelect.options[trackSelect.selectedIndex]?.text || 'No track selected';
    
    // Update UI to show selection summary
    console.log(`${selectedCount} students selected for enrollment in: ${selectedTrack}`);
}

async function bulkEnrollStudents() {
    const trackId = document.getElementById('enrollmentTrackSelect').value;
    
    if (!trackId) {
        showNotification('Please select a track for enrollment', 'warning');
        return;
    }
    
    if (selectedStudents.length === 0) {
        showNotification('Please select students to enroll', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${ORG_API_BASE}/projects/${selectedProjectForAction}/enroll-students`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                track_id: trackId,
                student_ids: selectedStudents
            })
        });

        if (response.ok) {
            showNotification(`Successfully enrolled ${selectedStudents.length} students`, 'success');
            selectedStudents = [];
            await loadAvailableStudents(); // Refresh the list
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to enroll students', 'error');
        }
    } catch (error) {
        console.error('Error enrolling students:', error);
        showNotification('Failed to enroll students', 'error');
    }
}

function searchStudents() {
    const searchTerm = document.getElementById('studentSearchInput').value.toLowerCase();
    const studentItems = document.querySelectorAll('.student-item');
    
    studentItems.forEach(item => {
        const name = item.querySelector('.student-name').textContent.toLowerCase();
        const email = item.querySelector('.student-email').textContent.toLowerCase();
        
        if (name.includes(searchTerm) || email.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// =============================================================================
// ANALYTICS FUNCTIONS
// =============================================================================

async function showProjectAnalytics(projectId) {
    currentAnalyticsProject = projectId;
    
    try {
        // Load project analytics data
        const analytics = await loadProjectAnalytics(projectId);
        displayAnalyticsSummary(analytics);
        
        // Load default analytics tab (overview)
        switchAnalyticsTab('overview');
        
        document.getElementById('projectAnalyticsModal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading project analytics:', error);
        showNotification('Failed to load project analytics', 'error');
    }
}

async function loadProjectAnalytics(projectId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/analytics`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            // Mock analytics data
            return {
                total_enrolled_students: 32,
                active_students: 28,
                completed_students: 4,
                average_progress_percentage: 67.5,
                average_quiz_score: 84.2,
                engagement_metrics: {
                    avg_time_per_session: 45,
                    total_lab_sessions: 156,
                    forum_participation: 78
                }
            };
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
        return {};
    }
}

function displayAnalyticsSummary(analytics) {
    document.getElementById('analyticsEnrolledStudents').textContent = analytics.total_enrolled_students || 0;
    document.getElementById('analyticsActiveStudents').textContent = analytics.active_students || 0;
    document.getElementById('analyticsCompletedStudents').textContent = analytics.completed_students || 0;
    document.getElementById('analyticsAverageProgress').textContent = `${analytics.average_progress_percentage || 0}%`;
    document.getElementById('analyticsAverageScore').textContent = `${analytics.average_quiz_score || 0}%`;
}

function switchAnalyticsTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.analytics-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Load tab content
    loadAnalyticsTabContent(tabName);
}

function loadAnalyticsTabContent(tabName) {
    const container = document.getElementById('analyticsTabContent');
    
    switch(tabName) {
        case 'overview':
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div>
                        <h4>Enrollment Trends</h4>
                        <div style="height: 200px; background: var(--hover-color); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                            📈 Enrollment Chart Placeholder
                        </div>
                    </div>
                    <div>
                        <h4>Progress Distribution</h4>
                        <div style="height: 200px; background: var(--hover-color); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                            📊 Progress Chart Placeholder
                        </div>
                    </div>
                </div>
            `;
            break;
        case 'progress':
            container.innerHTML = `
                <div>
                    <h4>Student Progress Tracking</h4>
                    <div style="background: var(--hover-color); border-radius: 8px; padding: 2rem; text-align: center;">
                        📋 Detailed progress tracking table will be implemented here
                    </div>
                </div>
            `;
            break;
        case 'performance':
            container.innerHTML = `
                <div>
                    <h4>Performance Metrics</h4>
                    <div style="background: var(--hover-color); border-radius: 8px; padding: 2rem; text-align: center;">
                        🎯 Performance analytics and quiz scores will be displayed here
                    </div>
                </div>
            `;
            break;
        case 'engagement':
            container.innerHTML = `
                <div>
                    <h4>Student Engagement</h4>
                    <div style="background: var(--hover-color); border-radius: 8px; padding: 2rem; text-align: center;">
                        👥 Engagement metrics and activity patterns will be shown here
                    </div>
                </div>
            `;
            break;
    }
}

function exportAnalytics() {
    showNotification('Analytics export functionality coming soon', 'info');
}

// Update project display to include new action buttons
function displayProjects(projects) {
    const container = document.getElementById('projectsList');
    
    if (projects.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                <h3>No projects yet</h3>
                <p>Create your first training project to get started.</p>
                <button class="btn btn-primary" onclick="showCreateProjectModal()">Create Project</button>
            </div>
        `;
        return;
    }

    container.innerHTML = projects.map(project => `
        <div class="project-card">
            <div class="project-header">
                <div>
                    <h3 style="margin: 0 0 0.5rem 0;">${project.name}</h3>
                    <p style="margin: 0; color: var(--text-muted);">${project.description || 'No description'}</p>
                </div>
                <span class="project-status status-${project.status}">${project.status.charAt(0).toUpperCase() + project.status.slice(1)}</span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div>
                    <strong>Duration:</strong><br>
                    ${project.duration_weeks ? `${project.duration_weeks} weeks` : 'Not set'}
                </div>
                <div>
                    <strong>Participants:</strong><br>
                    ${project.current_participants || 0}/${project.max_participants || '∞'}
                </div>
                <div>
                    <strong>Start Date:</strong><br>
                    ${project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Not set'}
                </div>
            </div>

            ${project.target_roles && project.target_roles.length > 0 ? `
                <div>
                    <strong>Target Roles:</strong>
                    <div class="target-roles">
                        ${project.target_roles.map(role => `<span class="role-tag">${role}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            <div style="display: flex; gap: 0.5rem; margin-top: 1rem; flex-wrap: wrap;">
                <button class="action-btn btn-edit" onclick="editProject('${project.id}')">✏️ Edit</button>
                <button class="action-btn btn-primary" onclick="manageProjectMembers('${project.id}')">👥 Members</button>
                
                ${project.status === 'draft' ? `
                    <button class="action-btn btn-success" onclick="instantiateProject('${project.id}')">🚀 Instantiate</button>
                ` : ''}
                
                ${project.status === 'active' ? `
                    <button class="action-btn btn-info" onclick="showInstructorAssignmentModal('${project.id}')">👨‍🏫 Assign Instructors</button>
                    <button class="action-btn btn-warning" onclick="showInstructorRemovalModal('${project.id}')">🗑️ Remove Instructors</button>
                    <button class="action-btn btn-primary" onclick="showStudentEnrollmentModal('${project.id}')">📝 Enroll Students</button>
                    <button class="action-btn btn-warning" onclick="showStudentUnenrollmentModal('${project.id}')">❌ Unenroll Students</button>
                    <button class="action-btn btn-secondary" onclick="showProjectAnalytics('${project.id}')">📊 Analytics</button>
                ` : ''}
                
                <button class="action-btn btn-delete" onclick="deleteProject('${project.id}')">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
}

// =============================================================================
// STUDENT UNENROLLMENT FUNCTIONS
// =============================================================================

async function showStudentUnenrollmentModal(projectId) {
    selectedProjectForAction = projectId;
    selectedStudents = [];
    
    try {
        // Load enrolled students for this project
        await loadEnrolledStudentsForProject(projectId);
        
        document.getElementById('studentUnenrollmentModal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading student unenrollment data:', error);
        showNotification('Failed to load student unenrollment interface', 'error');
    }
}

async function loadEnrolledStudentsForProject(projectId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/enrolled-students`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const enrolledStudents = await response.json();
            displayEnrolledStudents(enrolledStudents);
        } else {
            // Mock enrolled students
            const mockEnrolledStudents = [
                { 
                    id: 'student-1', 
                    name: 'Alice Johnson', 
                    email: 'alice@techuni.edu', 
                    track_name: 'Foundation Track',
                    track_id: 'track-1',
                    progress_percentage: 45.5,
                    enrollment_date: '2024-01-15'
                },
                { 
                    id: 'student-3', 
                    name: 'Carol Davis', 
                    email: 'carol@techuni.edu', 
                    track_name: 'Web Development Track',
                    track_id: 'track-2',
                    progress_percentage: 78.3,
                    enrollment_date: '2024-01-10'
                },
                { 
                    id: 'student-6', 
                    name: 'Frank Miller', 
                    email: 'frank@techuni.edu', 
                    track_name: 'Foundation Track',
                    track_id: 'track-1',
                    progress_percentage: 23.1,
                    enrollment_date: '2024-01-20'
                }
            ];
            displayEnrolledStudents(mockEnrolledStudents);
        }
    } catch (error) {
        console.error('Error loading enrolled students:', error);
        displayEnrolledStudents([]);
    }
}

function displayEnrolledStudents(students) {
    const container = document.getElementById('enrolledStudentsList');
    if (!container) return;

    if (students.length === 0) {
        container.innerHTML = '<p>No students enrolled in this project.</p>';
        return;
    }

    container.innerHTML = students.map(student => `
        <div class="student-item enrolled-student-item">
            <div class="student-selection">
                <input type="checkbox" id="unenroll-${student.id}" value="${student.id}" 
                       onchange="toggleStudentForUnenrollment('${student.id}')">
                <label for="unenroll-${student.id}">
                    <div class="student-info">
                        <div class="student-name">${student.name}</div>
                        <div class="student-email">${student.email}</div>
                        <div class="student-track">Track: ${student.track_name}</div>
                        <div class="student-progress">Progress: ${student.progress_percentage.toFixed(1)}%</div>
                        <div class="student-enrollment-date">Enrolled: ${new Date(student.enrollment_date).toLocaleDateString()}</div>
                    </div>
                </label>
            </div>
        </div>
    `).join('');
}

function toggleStudentForUnenrollment(studentId) {
    const checkbox = document.getElementById(`unenroll-${studentId}`);
    if (checkbox.checked) {
        if (!selectedStudents.includes(studentId)) {
            selectedStudents.push(studentId);
        }
    } else {
        selectedStudents = selectedStudents.filter(id => id !== studentId);
    }
    
    // Update unenroll button state
    const unenrollBtn = document.querySelector('#studentUnenrollmentModal .btn-danger');
    if (unenrollBtn) {
        unenrollBtn.disabled = selectedStudents.length === 0;
    }
}

async function confirmStudentUnenrollment() {
    if (selectedStudents.length === 0) {
        showNotification('Please select at least one student to unenroll', 'warning');
        return;
    }
    
    const unenrollFromProject = document.getElementById('unenrollFromProject').checked;
    const preserveProgress = document.getElementById('preserveProgress').checked;
    
    try {
        const promises = selectedStudents.map(studentId => {
            const endpoint = unenrollFromProject 
                ? `${ORG_API_BASE}/projects/${selectedProjectForAction}/students/${studentId}/unenroll`
                : `${ORG_API_BASE}/projects/${selectedProjectForAction}/tracks/current/students/${studentId}/unenroll`;
                
            return fetch(endpoint, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    preserve_progress: preserveProgress,
                    unenroll_from_project: unenrollFromProject
                })
            });
        });
        
        const responses = await Promise.all(promises);
        const allSuccessful = responses.every(response => response.ok);
        
        if (allSuccessful) {
            showNotification(`Successfully unenrolled ${selectedStudents.length} student(s)`, 'success');
            closeModal('studentUnenrollmentModal');
            // Refresh project data
            loadProjects();
        } else {
            showNotification('Some unenrollments failed. Please check the logs.', 'warning');
        }
        
    } catch (error) {
        console.error('Error unenrolling students:', error);
        showNotification('Failed to unenroll students', 'error');
    }
}

// =============================================================================
// INSTRUCTOR REMOVAL FUNCTIONS
// =============================================================================

async function showInstructorRemovalModal(projectId) {
    selectedProjectForAction = projectId;
    selectedInstructors = [];
    
    try {
        // Load assigned instructors for this project
        await loadAssignedInstructorsForProject(projectId);
        
        document.getElementById('instructorRemovalModal').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading instructor removal data:', error);
        showNotification('Failed to load instructor removal interface', 'error');
    }
}

async function loadAssignedInstructorsForProject(projectId) {
    try {
        const response = await fetch(`${ORG_API_BASE}/projects/${projectId}/assigned-instructors`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const assignedInstructors = await response.json();
            displayAssignedInstructors(assignedInstructors);
        } else {
            // Mock assigned instructors
            const mockAssignedInstructors = [
                { 
                    id: 'instructor-1', 
                    name: 'Dr. Sarah Johnson', 
                    email: 'sarah@techuni.edu', 
                    tracks: ['Foundation Track', 'Web Development Track'],
                    modules: ['Programming Fundamentals', 'Web APIs', 'Database Design'],
                    role: 'lead_instructor',
                    assignment_date: '2024-01-01'
                },
                { 
                    id: 'instructor-2', 
                    name: 'Prof. Mike Chen', 
                    email: 'mike@techuni.edu', 
                    tracks: ['Web Development Track'],
                    modules: ['Frontend Development', 'Backend Development'],
                    role: 'instructor',
                    assignment_date: '2024-01-05'
                },
                { 
                    id: 'instructor-3', 
                    name: 'Dr. Lisa Rodriguez', 
                    email: 'lisa@techuni.edu', 
                    tracks: ['Foundation Track'],
                    modules: ['Programming Fundamentals'],
                    role: 'co_instructor',
                    assignment_date: '2024-01-08'
                }
            ];
            displayAssignedInstructors(mockAssignedInstructors);
        }
    } catch (error) {
        console.error('Error loading assigned instructors:', error);
        displayAssignedInstructors([]);
    }
}

function displayAssignedInstructors(instructors) {
    const container = document.getElementById('assignedInstructorsList');
    if (!container) return;

    if (instructors.length === 0) {
        container.innerHTML = '<p>No instructors assigned to this project.</p>';
        return;
    }

    container.innerHTML = instructors.map(instructor => `
        <div class="instructor-item assigned-instructor-item">
            <div class="instructor-selection">
                <input type="checkbox" id="remove-${instructor.id}" value="${instructor.id}" 
                       onchange="toggleInstructorForRemoval('${instructor.id}')">
                <label for="remove-${instructor.id}">
                    <div class="instructor-info">
                        <div class="instructor-name">${instructor.name}</div>
                        <div class="instructor-email">${instructor.email}</div>
                        <div class="instructor-role">Role: ${instructor.role.replace('_', ' ').toUpperCase()}</div>
                        <div class="instructor-tracks">Tracks: ${instructor.tracks.join(', ')}</div>
                        <div class="instructor-modules">Modules: ${instructor.modules.join(', ')}</div>
                        <div class="instructor-assignment-date">Assigned: ${new Date(instructor.assignment_date).toLocaleDateString()}</div>
                    </div>
                </label>
            </div>
        </div>
    `).join('');
}

function toggleInstructorForRemoval(instructorId) {
    const checkbox = document.getElementById(`remove-${instructorId}`);
    if (checkbox.checked) {
        if (!selectedInstructors.includes(instructorId)) {
            selectedInstructors.push(instructorId);
        }
    } else {
        selectedInstructors = selectedInstructors.filter(id => id !== instructorId);
    }
    
    // Update remove button state
    const removeBtn = document.querySelector('#instructorRemovalModal .btn-danger');
    if (removeBtn) {
        removeBtn.disabled = selectedInstructors.length === 0;
    }
}

async function confirmInstructorRemoval() {
    if (selectedInstructors.length === 0) {
        showNotification('Please select at least one instructor to remove', 'warning');
        return;
    }
    
    const removeFromOrganization = document.getElementById('removeFromOrganization').checked;
    const transferAssignments = document.getElementById('transferAssignments').checked;
    const replacementInstructorId = document.getElementById('replacementInstructorSelect').value;
    
    if (transferAssignments && !replacementInstructorId) {
        showNotification('Please select a replacement instructor when transferring assignments', 'warning');
        return;
    }
    
    try {
        const promises = selectedInstructors.map(instructorId => {
            let endpoint;
            let body = {
                transfer_assignments: transferAssignments,
                replacement_instructor_id: replacementInstructorId || null
            };
            
            if (removeFromOrganization) {
                endpoint = `${ORG_API_BASE}/organizations/${currentOrganization.id}/instructors/${instructorId}`;
            } else {
                endpoint = `${ORG_API_BASE}/projects/${selectedProjectForAction}/instructors/${instructorId}`;
            }
                
            return fetch(endpoint, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });
        });
        
        const responses = await Promise.all(promises);
        const allSuccessful = responses.every(response => response.ok);
        
        if (allSuccessful) {
            const action = removeFromOrganization ? 'removed from organization' : 'removed from project';
            showNotification(`Successfully ${action} ${selectedInstructors.length} instructor(s)`, 'success');
            closeModal('instructorRemovalModal');
            // Refresh project data
            loadProjects();
        } else {
            showNotification('Some instructor removals failed. Please check the logs.', 'warning');
        }
        
    } catch (error) {
        console.error('Error removing instructors:', error);
        showNotification('Failed to remove instructors', 'error');
    }
}

// Global variables for instructor/student selections
let selectedInstructors = [];

// Event listeners for instructor removal options
document.addEventListener('DOMContentLoaded', function() {
    // Toggle replacement instructor section visibility
    const transferCheckbox = document.getElementById('transferAssignments');
    const replacementSection = document.getElementById('replacementInstructorSection');
    
    if (transferCheckbox && replacementSection) {
        transferCheckbox.addEventListener('change', function() {
            if (this.checked) {
                replacementSection.style.display = 'block';
                loadReplacementInstructorOptions();
            } else {
                replacementSection.style.display = 'none';
            }
        });
    }
});

async function loadReplacementInstructorOptions() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/instructors`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const instructors = await response.json();
            populateReplacementInstructorSelect(instructors);
        } else {
            // Mock instructors
            const mockInstructors = [
                { id: 'instructor-4', name: 'Dr. James Wilson', email: 'james@techuni.edu' },
                { id: 'instructor-5', name: 'Prof. Anna Smith', email: 'anna@techuni.edu' },
                { id: 'instructor-6', name: 'Dr. Robert Davis', email: 'robert@techuni.edu' }
            ];
            populateReplacementInstructorSelect(mockInstructors);
        }
    } catch (error) {
        console.error('Error loading replacement instructors:', error);
        populateReplacementInstructorSelect([]);
    }
}

function populateReplacementInstructorSelect(instructors) {
    const select = document.getElementById('replacementInstructorSelect');
    if (!select) return;
    
    // Clear existing options (keep the first default option)
    select.innerHTML = '<option value="">-- Select Replacement --</option>';
    
    // Add instructor options
    instructors.forEach(instructor => {
        // Don't include instructors that are being removed
        if (!selectedInstructors.includes(instructor.id)) {
            const option = document.createElement('option');
            option.value = instructor.id;
            option.textContent = `${instructor.name} (${instructor.email})`;
            select.appendChild(option);
        }
    });
}

// =============================================================================
// ORGANIZATION SETTINGS FUNCTIONS
// =============================================================================

/**
 * Initialize logo upload functionality with drag & drop support
 */
function initializeLogoUpload() {
    const uploadArea = document.getElementById('logoUploadAreaSettings');
    const fileInput = document.getElementById('orgLogoFile');
    const uploadLink = uploadArea.querySelector('.upload-link');
    const preview = document.getElementById('logoPreview');
    const previewImg = document.getElementById('logoPreviewImg');
    const removeBtn = document.getElementById('removeLogo');

    if (!uploadArea || !fileInput) return;

    // Click to browse functionality
    uploadLink.addEventListener('click', (e) => {
        e.preventDefault();
        fileInput.click();
    });

    uploadArea.addEventListener('click', (e) => {
        if (e.target === uploadArea || e.target.classList.contains('upload-content')) {
            fileInput.click();
        }
    });

    // File input change handler
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleLogoFile(file);
        }
    });

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary-color)';
        uploadArea.style.backgroundColor = 'rgba(var(--primary-color-rgb), 0.1)';
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        uploadArea.style.backgroundColor = '';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        uploadArea.style.backgroundColor = '';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                fileInput.files = files;
                handleLogoFile(file);
            } else {
                showNotification('Please upload an image file', 'error');
            }
        }
    });

    // Remove logo button
    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            removeLogo();
        });
    }

    // Show existing logo if available
    if (currentOrganization && currentOrganization.logo_url) {
        previewImg.src = currentOrganization.logo_url;
        preview.style.display = 'block';
    }
}

/**
 * Handle logo file selection and preview
 * @param {File} file - The selected logo file
 */
function handleLogoFile(file) {
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Please upload a valid image file (JPG, PNG, GIF)', 'error');
        return;
    }

    // Validate file size (5MB limit)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
        showNotification('File size must be less than 5MB', 'error');
        return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('logoPreview');
        const previewImg = document.getElementById('logoPreviewImg');
        
        previewImg.src = e.target.result;
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

/**
 * Upload logo file to the server
 * @param {File} file - The logo file to upload
 * @returns {Promise<string>} - The uploaded file URL
 */
async function uploadLogoFile(file) {
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', 'organization_logo');
    formData.append('organization_id', currentOrganization.id);

    try {
        const response = await fetch(`${window.CONFIG?.API_URLS.CONTENT_MANAGEMENT}/api/v1/files/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`
            },
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            return result.file_url || result.url;
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        console.error('Logo upload error:', error);
        throw new Error('Failed to upload logo');
    }
}

/**
 * Remove logo preview and clear file input
 */
function removeLogo() {
    
    const preview = document.getElementById('logoPreview');
    const fileInput = document.getElementById('orgLogoFile');
    const logoUrlInput = document.getElementById('orgLogoSetting');

    preview.style.display = 'none';
    fileInput.value = '';
    
    // Also clear the URL input if it matches the preview
    if (logoUrlInput && logoUrlInput.value === currentOrganization.logo_url) {
        logoUrlInput.value = '';
    }
}

/**
 * Cancel organization changes and restore original values
 */
function cancelOrganizationChanges() {
    
    if (confirm('Are you sure you want to cancel your changes? Any unsaved changes will be lost.')) {
        // Reload the settings data to restore original values
        loadSettingsData();
        showNotification('Changes cancelled', 'info');
    }
}

/**
 * Handle contact email validation
 */
function validateContactEmail(email) {
    
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        return { valid: false, message: 'Please enter a valid email address' };
    }

    // Check for professional domains (exclude common personal email providers)
    const personalDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'];
    const domain = email.split('@')[1].toLowerCase();
    
    if (personalDomains.includes(domain)) {
        return { 
            valid: false, 
            message: 'Please use a professional email address for organization contact' 
        };
    }

    return { valid: true, message: 'Valid professional email address' };
}

/**
 * Handle phone number formatting
 */
function formatPhoneNumber(phoneNumber, countryCode) {
    
    // Remove all non-digit characters
    const digits = phoneNumber.replace(/\D/g, '');
    
    // Format based on country code
    switch (countryCode) {
        case '+1': // US/Canada
            if (digits.length === 10) {
                return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
            }
            break;
        case '+44': // UK
            if (digits.length >= 10) {
                return `${digits.slice(0,4)} ${digits.slice(4,7)} ${digits.slice(7)}`;
            }
            break;
        default:
            // Generic international format
            return digits.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
    }
    
    return phoneNumber; // Return original if no format applies
}

// Initialize organization settings when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add real-time email validation
    const contactEmailInput = document.getElementById('orgContactEmailSetting');
    if (contactEmailInput) {
        contactEmailInput.addEventListener('blur', function() {
            const validation = validateContactEmail(this.value);
            const helpText = this.parentNode.querySelector('.form-help');
            
            if (helpText) {
                helpText.textContent = validation.message;
                helpText.style.color = validation.valid ? 'var(--success-color)' : 'var(--error-color)';
            }
        });
    }

    // Add phone number formatting
    const phoneInput = document.getElementById('orgContactPhoneSetting');
    const countrySelect = document.getElementById('orgContactPhoneCountry');
    
    if (phoneInput && countrySelect) {
        phoneInput.addEventListener('input', function() {
            const formatted = formatPhoneNumber(this.value, countrySelect.value);
            if (formatted !== this.value) {
                const cursorPos = this.selectionStart;
                this.value = formatted;
                this.setSelectionRange(cursorPos, cursorPos);
            }
        });
    }

    // Initialize draggable modals
    initDraggableModals();
});

// Make modals draggable
function initDraggableModals() {
    const modals = document.querySelectorAll('.draggable-modal');

    modals.forEach(modal => {
        const handle = modal.querySelector('.draggable-handle');
        if (!handle) return;

        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        let xOffset = 0;
        let yOffset = 0;

        handle.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);

        function dragStart(e) {
            // Don't drag if clicking the close button
            if (e.target.classList.contains('close')) return;

            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;

            if (e.target === handle || handle.contains(e.target)) {
                isDragging = true;
            }
        }

        function drag(e) {
            if (isDragging) {
                e.preventDefault();

                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;

                xOffset = currentX;
                yOffset = currentY;

                setTranslate(currentX, currentY, modal);
            }
        }

        function dragEnd(e) {
            initialX = currentX;
            initialY = currentY;
            isDragging = false;
        }

        function setTranslate(xPos, yPos, el) {
            el.style.transform = `translate(${xPos}px, ${yPos}px)`;
        }
    });
}
// Floating Action Button (FAB) functionality
function toggleFabMenu() {
    const fabMenu = document.getElementById('fabMenu');
    const fabIcon = document.getElementById('fabIcon');

    fabMenu.classList.toggle('active');

    // Rotate icon when menu is open
    if (fabMenu.classList.contains('active')) {
        fabIcon.style.transform = 'rotate(45deg)';
    } else {
        fabIcon.style.transform = 'rotate(0deg)';
    }
}

function fabAction(action) {
    // Close the menu
    const fabMenu = document.getElementById('fabMenu');
    const fabIcon = document.getElementById('fabIcon');
    fabMenu.classList.remove('active');
    fabIcon.style.transform = 'rotate(0deg)';

    // Execute the action
    switch(action) {
        case 'project':
            showCreateProjectModal();
            break;
        case 'instructor':
            showAddInstructorModal();
            break;
        case 'student':
            showAddStudentModal();
            break;
        case 'track':
            showCreateTrackModal();
            break;
        case 'settings':
            document.querySelector('[data-tab="settings"]').click();
            break;
    }
}

// Close FAB menu when clicking outside
document.addEventListener('click', function(event) {
    const fabButton = document.getElementById('fabButton');
    const fabMenu = document.getElementById('fabMenu');
    const fabIcon = document.getElementById('fabIcon');

    if (fabButton && fabMenu && fabIcon) {
        if (!fabButton.contains(event.target) && !fabMenu.contains(event.target)) {
            fabMenu.classList.remove('active');
            fabIcon.style.transform = 'rotate(0deg)';
        }
    }
});
