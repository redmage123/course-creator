/**
 * Organization Admin Dashboard JavaScript
 * Manages organization settings, projects, instructors, and members
 */

// Configuration
const ORG_API_BASE = CONFIG.ENDPOINTS.ORGANIZATION_SERVICE || 'http://localhost:8008/api/v1';

// Global state
let currentOrganization = null;
let currentTab = 'overview';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!Auth.isAuthenticated() || !Auth.hasRole(['org_admin', 'super_admin'])) {
        window.location.href = '/login.html';
        return;
    }

    await initializeDashboard();
    setupEventListeners();
    setupTabNavigation();
});

async function initializeDashboard() {
    try {
        showLoadingSpinner();
        
        // Load organization data
        await loadOrganizationData();
        
        // Load initial tab content
        await loadTabContent(currentTab);
        
        hideLoadingSpinner();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
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
            domain: 'techuni.edu',
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
    document.getElementById('orgDescription').textContent = currentOrganization.description || 'Manage your organization\'s training programs and team members';
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
            case 'members':
                await loadMembersData();
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
    
    document.getElementById('totalProjects').textContent = stats.active_projects || 0;
    document.getElementById('totalInstructors').textContent = stats.instructors || 0;
    document.getElementById('totalMembers').textContent = stats.total_members || 0;
    document.getElementById('totalCourses').textContent = stats.courses || 0;

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

async function loadMembersData() {
    try {
        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/members`, {
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            }
        });

        let members = [];
        if (response.ok) {
            members = await response.json();
        } else {
            // Mock data for development
            members = getMockMembers();
        }

        displayMembers(members);
    } catch (error) {
        console.error('Error loading members:', error);
        displayMembers(getMockMembers());
    }
}

async function loadSettingsData() {
    // Populate settings form with current organization data
    document.getElementById('orgNameSetting').value = currentOrganization.name || '';
    document.getElementById('orgDescriptionSetting').value = currentOrganization.description || '';
    document.getElementById('orgDomainSetting').value = currentOrganization.domain || '';
    document.getElementById('orgLogoSetting').value = currentOrganization.logo_url || '';

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

function displayMembers(members) {
    const tbody = document.querySelector('#membersTable tbody');
    
    if (members.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No members found.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = members.map(member => `
        <tr>
            <td>${member.first_name || ''} ${member.last_name || ''}</td>
            <td>${member.email}</td>
            <td><span class="role-badge role-${member.role}">${member.role.replace('_', ' ')}</span></td>
            <td>${member.project_count || 0}</td>
            <td>${new Date(member.joined_at).toLocaleDateString()}</td>
            <td><span class="status-${member.is_active ? 'active' : 'inactive'}">${member.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button class="action-btn btn-edit" onclick="editMember('${member.user_id}')">Edit</button>
                <button class="action-btn btn-delete" onclick="removeMember('${member.user_id}')">Remove</button>
            </td>
        </tr>
    `).join('');
}

function setupEventListeners() {
    // Form submissions
    document.getElementById('addInstructorForm').addEventListener('submit', handleAddInstructor);
    document.getElementById('createProjectForm').addEventListener('submit', handleCreateProject);
    document.getElementById('addMemberForm').addEventListener('submit', handleAddMember);
    document.getElementById('orgSettingsForm').addEventListener('submit', handleUpdateSettings);
    document.getElementById('orgPreferencesForm').addEventListener('submit', handleUpdatePreferences);

    // Auto-generate slug from project name
    document.getElementById('projectName').addEventListener('input', function(e) {
        const slug = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        document.getElementById('projectSlug').value = slug;
    });
}

// Modal functions
function showCreateProjectModal() {
    document.getElementById('createProjectModal').style.display = 'block';
}

function showAddInstructorModal() {
    document.getElementById('addInstructorModal').style.display = 'block';
}

function showAddMemberModal() {
    document.getElementById('addMemberModal').style.display = 'block';
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

async function handleAddMember(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const memberData = {
            user_email: formData.get('user_email'),
            role: formData.get('role')
        };

        const orgId = currentOrganization.id;
        const response = await fetch(`${ORG_API_BASE}/organizations/${orgId}/members`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(memberData)
        });

        if (response.ok) {
            showNotification('Member added successfully', 'success');
            closeModal('addMemberModal');
            if (currentTab === 'members') {
                await loadMembersData();
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to add member', 'error');
        }
    } catch (error) {
        console.error('Error adding member:', error);
        showNotification('Failed to add member', 'error');
    }
}

async function handleUpdateSettings(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const settingsData = {
            name: formData.get('name'),
            description: formData.get('description'),
            domain: formData.get('domain'),
            logo_url: formData.get('logo_url')
        };

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
            showNotification('Settings updated successfully', 'success');
            // Update local organization data
            Object.assign(currentOrganization, settingsData);
            updateOrganizationDisplay();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to update settings', 'error');
        }
    } catch (error) {
        console.error('Error updating settings:', error);
        showNotification('Failed to update settings', 'error');
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
    // In production, extract from JWT token or user context
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

function getMockMembers() {
    return [
        {
            user_id: 'user-3',
            email: 'student1@techuni.edu',
            first_name: 'Alice',
            last_name: 'Johnson',
            role: 'student',
            project_count: 2,
            is_active: true,
            joined_at: '2024-01-10T00:00:00Z'
        },
        {
            user_id: 'user-4',
            email: 'student2@techuni.edu',
            first_name: 'Bob',
            last_name: 'Wilson',
            role: 'student',
            project_count: 1,
            is_active: true,
            joined_at: '2024-01-12T00:00:00Z'
        }
    ];
}

async function getOrganizationStats() {
    return {
        active_projects: 3,
        instructors: 8,
        total_members: 156,
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

// Placeholder functions for actions that need implementation
function editProject(projectId) {
    showNotification('Edit project functionality coming soon', 'info');
}

function manageProjectMembers(projectId) {
    showNotification('Project member management coming soon', 'info');
}

function activateProject(projectId) {
    showNotification('Project activation functionality coming soon', 'info');
}

function deleteProject(projectId) {
    if (confirm('Are you sure you want to delete this project?')) {
        showNotification('Project deletion functionality coming soon', 'info');
    }
}

function editInstructor(userId) {
    showNotification('Edit instructor functionality coming soon', 'info');
}

function editMember(userId) {
    showNotification('Edit member functionality coming soon', 'info');
}

function removeMember(userId) {
    if (confirm('Are you sure you want to remove this member?')) {
        showNotification('Member removal functionality coming soon', 'info');
    }
}