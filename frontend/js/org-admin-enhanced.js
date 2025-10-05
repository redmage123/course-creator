/**
 * Enhanced Organization Admin Dashboard
 * Comprehensive RBAC and Meeting Room Management
 */

// Import ES6 modules
import { showNotification } from './modules/notifications.js';
import AccessibilityManager from './modules/accessibility-manager.js';
import NavigationManager from './modules/navigation-manager.js';
import DataVisualization from './modules/data-visualization.js';
import OnboardingSystem from './modules/onboarding-system.js';
import { safeSetHTML, escapeHtml, createSafeElement } from './security-utils.js';

// Global logout function for logout button
window.logout = async function() {
    try {
        // Use global CONFIG to get the auth API URL
        const authApiBase = window.CONFIG?.API_URLS?.USER_MANAGEMENT || `https://${window.location.hostname}:8000`;
        const authToken = localStorage.getItem('authToken');
        
        if (authToken) {
            await fetch(`${authApiBase}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    // Clear session data
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('sessionStart');
    localStorage.removeItem('lastActivity');
    
    // Redirect to home
    window.location.href = '../index.html';
};

class OrgAdminDashboard {
    constructor() {
        this.currentOrganizationId = null;
        this.currentUser = null;
        this.members = [];
        this.tracks = [];
        this.meetingRooms = [];
        this.projects = [];
        
        this.init();
    }

    /**
     * Validate current session for org admin dashboard
     */
    validateSession() {
        const currentUser = this.getCurrentUser();
        const authToken = localStorage.getItem('authToken');
        const sessionStart = localStorage.getItem('sessionStart');
        const lastActivity = localStorage.getItem('lastActivity');

        console.log('🔍 Session Validation:', {
            hasUser: !!currentUser,
            hasToken: !!authToken,
            hasSessionStart: !!sessionStart,
            hasLastActivity: !!lastActivity,
            userRole: currentUser?.role
        });

        // Validate complete session state
        if (!currentUser || !authToken) {
            console.log('❌ Session invalid: Missing user or token');
            this.redirectToHome();
            return false;
        }

        // Session timestamps are optional - create them if missing
        if (!sessionStart || !lastActivity) {
            console.log('⚠️ Creating missing session timestamps');
            const now = Date.now();
            localStorage.setItem('sessionStart', now.toString());
            localStorage.setItem('lastActivity', now.toString());
        }

        // Check session timeout (8 hours from start)
        const now = Date.now();
        const sessionAge = now - parseInt(sessionStart || now);
        const timeSinceActivity = now - parseInt(lastActivity || now);
        const SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8 hours
        const INACTIVITY_TIMEOUT = 2 * 60 * 60 * 1000; // 2 hours

        if (sessionAge > SESSION_TIMEOUT || timeSinceActivity > INACTIVITY_TIMEOUT) {
            console.log('❌ Session expired: Redirecting to home page');
            this.clearExpiredSession();
            return false;
        }

        // Check if user has org_admin or organization_admin role
        if (currentUser.role !== 'org_admin' && currentUser.role !== 'organization_admin' && currentUser.role !== 'admin') {
            console.log('❌ Invalid role for org admin dashboard:', currentUser.role);
            this.redirectToHome();
            return false;
        }

        console.log('✅ Session validation passed');
        return true;
    }

    /**
     * Get current user from localStorage
     */
    getCurrentUser() {
        try {
            const userStr = localStorage.getItem('currentUser');
            return userStr ? JSON.parse(userStr) : null;
        } catch (error) {
            console.error('Error getting current user:', error);
            return null;
        }
    }

    /**
     * Clear expired session data and redirect
     */
    clearExpiredSession() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('sessionStart');
        localStorage.removeItem('lastActivity');
        this.redirectToHome();
    }

    /**
     * Redirect to home page
     */
    redirectToHome() {
        window.location.href = window.location.pathname.includes('/html/') ? '../index.html' : 'index.html';
    }

    async init() {
        try {
            // Initialize authentication
            await this.loadCurrentUser();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Load initial data
            await this.loadDashboardData();
            
            // Initialize data visualizations
            this.initializeDataVisualizations();
            
            // Show overview tab by default
            this.showTab('overview');
            
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            showNotification('Failed to load dashboard', 'error');
        }
    }

    async loadCurrentUser() {
        /*
         * COMPREHENSIVE SESSION VALIDATION ON PAGE LOAD - ORG ADMIN DASHBOARD
        
        BUSINESS REQUIREMENT:
        When an org admin refreshes the dashboard page after session expiry,
        they should be redirected to the home page with proper validation.
        
        TECHNICAL IMPLEMENTATION:
        1. Check if user data exists in localStorage
        2. Validate session timestamps against timeout thresholds  
        3. Check if authentication token is present and valid
        4. Verify user has correct role (org_admin)
        5. Redirect to home page if any validation fails
        6. Prevent dashboard initialization for expired sessions
         */
        
        // Validate session before making API calls
        if (!this.validateSession()) {
            return; // Validation function handles redirect
        }
        
        try {
            // Use user data already stored in localStorage (set during login)
            this.currentUser = this.getCurrentUser();
            if (!this.currentUser) {
                console.error('No user data found in localStorage');
                this.clearExpiredSession();
                return;
            }
            
            // Set organization ID from user data or JWT token
            this.currentOrganizationId = this.getCurrentUserOrgId();
            console.log('🏢 Current Organization ID:', this.currentOrganizationId);

            // Update UI
            document.getElementById('currentUserName').textContent = this.currentUser.full_name || this.currentUser.name || this.currentUser.email;
            
            // Set user initials for avatar
            const initials = this.getUserInitials(this.currentUser.full_name || this.currentUser.name || this.currentUser.email);
            document.getElementById('userInitials').textContent = initials;
            
        } catch (error) {
            console.error('Failed to load user:', error);
            // Clear session and redirect to home if user data is corrupted
            this.clearExpiredSession();
        }
    }

    /**
     * Get current user's organization ID from JWT token
     */
    getCurrentUserOrgId() {
        // Try to get from URL parameter first
        const urlParams = new URLSearchParams(window.location.search);
        const urlOrgId = urlParams.get('orgId');
        if (urlOrgId) {
            return urlOrgId;
        }

        // Try to extract from JWT token
        const token = Auth.getToken();
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                if (payload.organization_id) {
                    return payload.organization_id;
                }
            } catch (error) {
                console.error('Error parsing token:', error);
            }
        }

        // Fallback to user data
        if (this.currentUser) {
            return this.currentUser.organization_id || this.currentUser.organization;
        }

        // Final fallback to AI Elevate org for testing
        return '259da6df-c148-40c2-bcd9-dc6889e7e9fb';
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                // Use currentTarget to get the tab button, not the clicked child element
                const tabName = e.currentTarget.getAttribute('data-tab');
                this.showTab(tabName);
            });
        });

        // Member role filter
        document.getElementById('memberRoleFilter').addEventListener('change', () => {
            this.filterMembers();
        });

        // Meeting room filters
        document.getElementById('platformFilter').addEventListener('change', () => {
            this.filterMeetingRooms();
        });
        
        document.getElementById('roomTypeFilter').addEventListener('change', () => {
            this.filterMeetingRooms();
        });

        // Room type change handler
        document.getElementById('roomType').addEventListener('change', () => {
            this.updateRoomTypeFields();
        });

        // Member role change handler
        document.getElementById('memberRole').addEventListener('change', () => {
            this.updateMemberRoleFields();
        });

        // Modal close handlers
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    async loadDashboardData() {
        this.showLoadingOverlay(true);
        
        try {
            // Load dashboard data with resilient error handling
            await Promise.allSettled([
                this.loadProjects(),
                this.loadMembers(),
                this.loadTracks(),
                this.loadMeetingRooms()
            ]);
            
            // Update overview stats with loaded data
            await this.updateOverviewStats();
            
            console.log('Dashboard loaded successfully with timeout protection');
            
        } catch (error) {
            console.error('Critical error loading dashboard:', error);
            showNotification('Some dashboard features may not be available', 'warning');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async loadMembers() {
        try {
            // Use the organization management service endpoint (port 8008) 
            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
            
            const response = await fetch(`${orgApiBase}/api/v1/rbac/organizations/${this.currentOrganizationId}/members`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error('Failed to load members');
            }

            this.members = await response.json();
            this.renderMembers();
            
        } catch (error) {
            console.error('Failed to load members:', error);
            document.getElementById('membersContainer').innerHTML = 
                `<div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Unable to load members</p>
                    <small>This feature is being set up for your organization</small>
                </div>`;
            // Set empty array so overview stats work
            this.members = [];
        }
    }

    async loadTracks() {
        try {
            // Tracks are managed by the course generation service (port 8001)
            const courseApiBase = window.CONFIG?.API_URLS?.COURSE_GENERATION || `https://${window.location.hostname}:8001`;
            
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
            
            const response = await fetch(`${courseApiBase}/organizations/${this.currentOrganizationId}/tracks`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error('Failed to load tracks');
            }

            this.tracks = await response.json();
            this.renderTracks();
            this.populateTrackSelects();
            
        } catch (error) {
            console.error('Failed to load tracks:', error);
            document.getElementById('tracksContainer').innerHTML = 
                `<div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Unable to load learning tracks</p>
                    <small>This feature is being set up for your organization</small>
                </div>`;
            // Set empty array so overview stats work
            this.tracks = [];
        }
    }

    async loadMeetingRooms() {
        try {
            // Meeting rooms are managed by organization management service (port 8008)
            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
            
            const response = await fetch(`${orgApiBase}/api/v1/rbac/organizations/${this.currentOrganizationId}/meeting-rooms`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error('Failed to load meeting rooms');
            }

            this.meetingRooms = await response.json();
            this.renderMeetingRooms();
            
        } catch (error) {
            console.error('Failed to load meeting rooms:', error);
            document.getElementById('meetingRoomsContainer').innerHTML = 
                `<div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Unable to load meeting rooms</p>
                    <small>This feature is being set up for your organization</small>
                </div>`;
            // Set empty array so overview stats work
            this.meetingRooms = [];
        }
    }

    async loadProjects() {
        try {
            // Projects might be managed by organization management service (port 8008)
            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            
            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout for projects
            
            const response = await fetch(`${orgApiBase}/api/v1/organizations/${this.currentOrganizationId}/projects`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error('Failed to load projects');
            }

            this.projects = await response.json();
            this.populateProjectSelects();
            
        } catch (error) {
            console.error('Failed to load projects:', error);
            // Set empty array so overview stats work and selects don't break
            this.projects = [];
        }
    }

    showTab(tabName) {
        // Validate tabName parameter
        if (!tabName || typeof tabName !== 'string') {
            console.error('showTab called with invalid tabName:', tabName);
            return;
        }

        // Update active tab with ARIA attributes
        document.querySelectorAll('.nav-tab[role="tab"]').forEach(tab => {
            tab.classList.remove('active');
            tab.setAttribute('aria-selected', 'false');
            tab.setAttribute('tabindex', '-1');

            // Remove screen reader indication
            const srText = tab.querySelector('.sr-only');
            if (srText) {
                srText.textContent = '';
            }
        });
        
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
            activeTab.setAttribute('aria-selected', 'true');
            activeTab.setAttribute('tabindex', '0');
            
            // Add screen reader indication
            let srText = activeTab.querySelector('.sr-only');
            if (!srText) {
                srText = document.createElement('span');
                srText.className = 'sr-only';
                activeTab.appendChild(srText);
            }
            srText.textContent = ' - Currently selected';
        }

        // Show tab content with ARIA
        document.querySelectorAll('.tab-content[role="tabpanel"]').forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
            content.setAttribute('aria-hidden', 'true');
        });
        
        const activePanel = document.getElementById(`${tabName}-panel`);
        if (activePanel) {
            activePanel.classList.add('active');
            activePanel.style.display = 'block';
            activePanel.setAttribute('aria-hidden', 'false');
        }

        // Announce tab change
        const tabContent = {
            'overview': 'Organization overview with statistics and recent activity',
            'projects': 'Project management interface with project list and creation tools',
            'members': 'Organization member management and role assignments',
            'tracks': 'Learning track management and course organization',
            'assignments': 'Role assignment and permission management',
            'meeting-rooms': 'Virtual meeting room management and scheduling',
            'settings': 'Organization settings and configuration options'
        };
        
        if (window.a11y) {
            window.a11y.announcePageChange(
                tabName.charAt(0).toUpperCase() + tabName.slice(1),
                tabContent[tabName] || 'Dashboard section'
            );
        }

        // Load tab-specific data
        switch (tabName) {
            case 'projects':
                this.renderProjects();
                break;
            case 'assignments':
                this.loadAssignments();
                break;
            case 'settings':
                this.loadSettings();
                break;
        }
    }

    renderMembers() {
        const container = document.getElementById('membersContainer');
        
        if (this.members.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h3>No Members Found</h3>
                    <p>Start by adding organization admins and instructors.</p>
                    <button class="btn btn-primary" onclick="orgAdmin.showAddMemberModal()">
                        <i class="fas fa-user-plus"></i> Add First Member
                    </button>
                </div>
            `;
            return;
        }

        const membersHtml = this.members.map(member => `
            <div class="member-card" data-role="${member.role_type}">
                <div class="member-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="member-info">
                    <h4>${member.name || member.email}</h4>
                    <p class="member-email">${member.email}</p>
                    <div class="member-role role-${member.role_type}">
                        <i class="fas ${this.getRoleIcon(member.role_type)}"></i>
                        ${this.formatRoleName(member.role_type)}
                    </div>
                    <div class="member-status status-${member.status}">
                        ${member.status}
                    </div>
                </div>
                <div class="member-actions">
                    <button class="btn btn-sm btn-outline" onclick="orgAdmin.viewMemberDetails('${member.membership_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="orgAdmin.removeMember('${member.membership_id}')">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = membersHtml;
    }

    renderTracks() {
        const container = document.getElementById('tracksContainer');
        
        if (this.tracks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-road"></i>
                    <h3>No Tracks Found</h3>
                    <p>Create learning tracks to organize your courses.</p>
                    <button class="btn btn-primary" onclick="orgAdmin.showCreateTrackModal()">
                        <i class="fas fa-plus"></i> Create First Track
                    </button>
                </div>
            `;
            return;
        }

        const tracksHtml = this.tracks.map(track => `
            <div class="track-card">
                <div class="track-header">
                    <h4>${track.name}</h4>
                    <div class="track-status status-${track.status}">
                        ${track.status}
                    </div>
                </div>
                <div class="track-info">
                    <p class="track-description">${track.description || 'No description'}</p>
                    <div class="track-meta">
                        <span class="meta-item">
                            <i class="fas fa-users"></i>
                            ${track.target_audience ? track.target_audience.join(', ') : 'Any'}
                        </span>
                        <span class="meta-item">
                            <i class="fas fa-clock"></i>
                            ${track.duration_weeks || 0} weeks
                        </span>
                        <span class="meta-item">
                            <i class="fas fa-signal"></i>
                            ${track.difficulty_level || 'beginner'}
                        </span>
                    </div>
                </div>
                <div class="track-actions">
                    <button class="btn btn-sm btn-outline" onclick="orgAdmin.viewTrackDetails('${track.id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="orgAdmin.manageTrackAssignments('${track.id}')">
                        <i class="fas fa-user-tag"></i> Assignments
                    </button>
                    <button class="btn btn-sm btn-success" onclick="orgAdmin.createTrackRoom('${track.id}')">
                        <i class="fas fa-video"></i> Create Room
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = tracksHtml;
    }

    renderProjects() {
        const container = document.getElementById('projectsContainer');
        
        if (this.projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <h3>No Projects Found</h3>
                    <p>Projects are the foundation of your organization. Create your first project to get started with learning tracks, teams, and resources.</p>
                    <button class="btn btn-primary" onclick="orgAdmin.showCreateProjectModal()">
                        <i class="fas fa-folder-plus"></i> Create First Project
                    </button>
                </div>
            `;
            return;
        }

        const projectsHtml = this.projects.map(project => `
            <div class="project-card" data-status="${project.status}" onclick="orgAdmin.selectProject('${project.id}')">
                <div class="project-header">
                    <h4>${project.name}</h4>
                    <div class="project-status status-${project.status}">
                        ${project.status}
                    </div>
                </div>
                <div class="project-info">
                    <p class="project-description">${project.description || 'No description'}</p>
                    <div class="project-meta">
                        <span class="meta-item">
                            <i class="fas fa-users"></i>
                            ${project.current_participants || 0}/${project.max_participants || '∞'} participants
                        </span>
                        ${project.duration_weeks ? `
                            <span class="meta-item">
                                <i class="fas fa-clock"></i>
                                ${project.duration_weeks} weeks
                            </span>
                        ` : ''}
                        ${project.start_date ? `
                            <span class="meta-item">
                                <i class="fas fa-calendar"></i>
                                ${new Date(project.start_date).toLocaleDateString()}
                            </span>
                        ` : ''}
                    </div>
                </div>
                <div class="project-actions">
                    <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); orgAdmin.selectProject('${project.id}')">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="event.stopPropagation(); orgAdmin.editProject('${project.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-success" onclick="event.stopPropagation(); orgAdmin.manageProjectMembers('${project.id}')">
                        <i class="fas fa-users"></i> Members
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = projectsHtml;
    }

    renderMeetingRooms() {
        const container = document.getElementById('meetingRoomsContainer');
        
        if (this.meetingRooms.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-video"></i>
                    <h3>No Meeting Rooms Found</h3>
                    <p>Create meeting rooms for your tracks and instructors.</p>
                    <button class="btn btn-primary" onclick="orgAdmin.showCreateMeetingRoomModal()">
                        <i class="fas fa-video"></i> Create First Room
                    </button>
                </div>
            `;
            return;
        }

        const roomsHtml = this.meetingRooms.map(room => `
            <div class="meeting-room-card" data-platform="${room.platform}" data-type="${room.room_type}">
                <div class="room-header">
                    <div class="room-platform platform-${room.platform}">
                        <i class="fas ${room.platform === 'teams' ? 'fa-microsoft' : 'fa-video'}"></i>
                        ${room.platform === 'teams' ? 'Teams' : 'Zoom'}
                    </div>
                    <div class="room-status status-${room.status}">
                        ${room.status}
                    </div>
                </div>
                <div class="room-info">
                    <h4>${room.display_name}</h4>
                    <p class="room-type">${this.formatRoomType(room.room_type)}</p>
                    <div class="room-meta">
                        <span class="meta-item">
                            <i class="fas fa-calendar-plus"></i>
                            Created ${new Date(room.created_at).toLocaleDateString()}
                        </span>
                        ${room.meeting_id ? `
                            <span class="meta-item">
                                <i class="fas fa-key"></i>
                                ID: ${room.meeting_id}
                            </span>
                        ` : ''}
                    </div>
                </div>
                <div class="room-actions">
                    <button class="btn btn-sm btn-success" onclick="orgAdmin.joinRoom('${room.join_url}')" ${!room.join_url ? 'disabled' : ''}>
                        <i class="fas fa-sign-in-alt"></i> Join
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="orgAdmin.inviteToRoom('${room.id}')">
                        <i class="fas fa-envelope"></i> Invite
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="orgAdmin.viewRoomDetails('${room.id}')">
                        <i class="fas fa-eye"></i> Details
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="orgAdmin.deleteRoom('${room.id}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = roomsHtml;
    }

    async updateOverviewStats() {
        try {
            // Update simplified stats
            document.getElementById('totalProjects').textContent = this.projects.length;
            
            // Update organization name
            if (this.currentUser && this.currentUser.organization) {
                document.getElementById('orgName').textContent = this.currentUser.organization;
            } else if (this.currentOrganizationId) {
                document.getElementById('orgName').textContent = this.currentOrganizationId;
            } else {
                document.getElementById('orgName').textContent = 'Your Organization';
            }
            
            // Set organization created date (placeholder for now)
            document.getElementById('orgCreatedDate').textContent = new Date().getFullYear();
            
            // Set organization status
            document.getElementById('orgStatus').textContent = 'Active';

        } catch (error) {
            console.error('Failed to update overview stats:', error);
        }
    }

    // Modal Functions
    showAddMemberModal(roleType = 'instructor') {
        document.getElementById('memberRole').value = roleType;
        this.updateMemberRoleFields();
        this.showModal('addMemberModal');
    }

    showAddStudentModal() {
        this.showModal('addStudentModal');
    }

    showCreateProjectModal() {
        // Auto-generate slug from name when typing
        const nameInput = document.getElementById('projectName');
        const slugInput = document.getElementById('projectSlug');
        
        nameInput.addEventListener('input', () => {
            const slug = nameInput.value
                .toLowerCase()
                .replace(/[^a-z0-9\s-]/g, '')
                .replace(/\s+/g, '-')
                .replace(/-+/g, '-')
                .trim();
            slugInput.value = slug;
        });
        
        this.showModal('createProjectModal');
    }

    showCreateMeetingRoomModal() {
        this.updateRoomTypeFields();
        this.showModal('createMeetingRoomModal');
    }

    showModal(modalId) {
        document.getElementById(modalId).style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Clear form
        const modal = document.getElementById(modalId);
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }

    updateMemberRoleFields() {
        const role = document.getElementById('memberRole').value;
        const projectGroup = document.getElementById('projectAccessGroup');
        
        if (role === 'instructor') {
            projectGroup.style.display = 'block';
        } else {
            projectGroup.style.display = 'none';
        }
    }

    updateRoomTypeFields() {
        const roomType = document.getElementById('roomType').value;
        
        // Hide all specific fields
        document.getElementById('projectSelectGroup').style.display = 'none';
        document.getElementById('trackSelectGroup').style.display = 'none';
        document.getElementById('instructorSelectGroup').style.display = 'none';
        
        // Show relevant fields
        switch (roomType) {
            case 'project_room':
                document.getElementById('projectSelectGroup').style.display = 'block';
                break;
            case 'track_room':
                document.getElementById('trackSelectGroup').style.display = 'block';
                break;
            case 'instructor_room':
                document.getElementById('instructorSelectGroup').style.display = 'block';
                break;
        }
    }

    populateProjectSelects() {
        const selects = ['projectAccess', 'roomProject'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = this.projects.map(project => 
                    `<option value="${project.id}">${project.name}</option>`
                ).join('');
            }
        });
    }

    populateTrackSelects() {
        const selects = ['studentTrack', 'roomTrack'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = '<option value="">Select a track...</option>' +
                    this.tracks.map(track => 
                        `<option value="${track.id}">${track.name}</option>`
                    ).join('');
            }
        });
    }

    // API Functions
    async addMember() {
        try {
            this.showLoadingOverlay(true);
            
            const form = document.getElementById('addMemberForm');
            const formData = new FormData(form);
            
            const data = {
                user_email: formData.get('user_email'),
                role_type: formData.get('role_type'),
                project_ids: Array.from(document.getElementById('projectAccess').selectedOptions)
                    .map(option => option.value)
            };

            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            const response = await fetch(`${orgApiBase}/api/v1/rbac/organizations/${this.currentOrganizationId}/members`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to add member');
            }

            await this.loadMembers();
            this.closeModal('addMemberModal');
            showNotification('Member added successfully', 'success');
            
        } catch (error) {
            console.error('Failed to add member:', error);
            showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async addStudent() {
        try {
            this.showLoadingOverlay(true);
            
            const form = document.getElementById('addStudentForm');
            const formData = new FormData(form);
            
            const data = {
                user_email: formData.get('user_email'),
                track_id: formData.get('track_id')
            };

            // Get project ID from selected track
            const selectedTrack = this.tracks.find(track => track.id === data.track_id);
            if (!selectedTrack) {
                throw new Error('Invalid track selected');
            }

            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            const response = await fetch(`${orgApiBase}/api/v1/rbac/projects/${selectedTrack.project_id}/students`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to add student');
            }

            await this.loadMembers();
            this.closeModal('addStudentModal');
            showNotification('Student added successfully', 'success');
            
        } catch (error) {
            console.error('Failed to add student:', error);
            showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async createMeetingRoom() {
        try {
            this.showLoadingOverlay(true);
            
            const form = document.getElementById('createMeetingRoomForm');
            const formData = new FormData(form);
            
            const data = {
                name: formData.get('name'),
                platform: formData.get('platform'),
                room_type: formData.get('room_type'),
                project_id: formData.get('project_id') || null,
                track_id: formData.get('track_id') || null,
                instructor_id: formData.get('instructor_id') || null,
                settings: {
                    auto_recording: formData.has('auto_recording'),
                    waiting_room: formData.has('waiting_room'),
                    mute_on_entry: formData.has('mute_on_entry'),
                    allow_screen_sharing: formData.has('allow_screen_sharing')
                }
            };

            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            const response = await fetch(`${orgApiBase}/api/v1/rbac/organizations/${this.currentOrganizationId}/meeting-rooms`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create meeting room');
            }

            await this.loadMeetingRooms();
            this.closeModal('createMeetingRoomModal');
            showNotification('Meeting room created successfully', 'success');
            
        } catch (error) {
            console.error('Failed to create meeting room:', error);
            showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async createProject() {
        try {
            this.showLoadingOverlay(true);
            
            const form = document.getElementById('createProjectForm');
            const formData = new FormData(form);
            
            const data = {
                name: formData.get('name'),
                slug: formData.get('slug'),
                description: formData.get('description'),
                duration_weeks: formData.get('duration_weeks') ? parseInt(formData.get('duration_weeks')) : null,
                max_participants: formData.get('max_participants') ? parseInt(formData.get('max_participants')) : null,
                start_date: formData.get('start_date') || null,
                end_date: formData.get('end_date') || null,
                objectives: formData.get('objectives') ? formData.get('objectives').split('\n').filter(obj => obj.trim()) : [],
                target_roles: formData.get('target_roles') ? formData.get('target_roles').split(',').map(role => role.trim()).filter(role => role) : [],
                settings: {}
            };

            const authToken = localStorage.getItem('authToken');
            console.log('Creating project with token segments:', authToken ? authToken.split('.').length : 'no token');
            
            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            const response = await fetch(`${orgApiBase}/api/v1/organizations/${this.currentOrganizationId}/projects`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                let errorMessage = 'Failed to create project';
                try {
                    const error = await response.json();
                    errorMessage = error.detail || error.message || `HTTP ${response.status}`;
                } catch (e) {
                    const errorText = await response.text();
                    errorMessage = `HTTP ${response.status}: ${errorText}`;
                }
                
                if (response.status === 401) {
                    console.error('Authentication failed. Token may be expired.');
                    // Check if we need to redirect to login
                    if (!localStorage.getItem('authToken')) {
                        window.location.href = '../index.html';
                        return;
                    }
                    errorMessage = 'Authentication failed. Please refresh the page and try again.';
                }
                
                throw new Error(errorMessage);
            }

            const newProject = await response.json();
            this.projects.push(newProject);
            this.renderProjects();
            this.updateOverviewStats();
            this.closeModal('createProjectModal');
            showNotification('Project created successfully', 'success');
            
        } catch (error) {
            console.error('Failed to create project:', error);
            showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    selectProject(projectId) {
        const project = this.projects.find(p => p.id === projectId);
        if (!project) {
            showNotification('Project not found', 'error');
            return;
        }
        
        // Store selected project
        this.selectedProject = project;
        
        // Switch to project details view
        this.showProjectDetails(project);
        
        // Update navigation to show project context
        this.showTab('project-details');
        
        showNotification(`Viewing project: ${project.name}`, 'success');
    }

    showProjectDetails(project) {
        // Update tab label and project name
        document.getElementById('projectDetailsTabLabel').textContent = project.name;
        document.getElementById('selectedProjectName').textContent = project.name;
        
        // Show the project details tab
        const projectDetailsTab = document.querySelector('[data-tab="project-details"]');
        if (projectDetailsTab) {
            projectDetailsTab.style.display = 'block';
        }
        
        // Display project information
        this.displayProjectInfo(project);
        
        // Load project-specific data
        this.loadProjectData(project);
        
        // Set up project content tab switching
        this.setupProjectContentTabs();
    }

    displayProjectInfo(project) {
        const projectInfoDisplay = document.getElementById('projectInfoDisplay');
        
        const projectInfo = `
            <div class="project-info-grid">
                <div class="info-item">
                    <label>Description:</label>
                    <span>${project.description || 'No description provided'}</span>
                </div>
                <div class="info-item">
                    <label>Status:</label>
                    <span class="status-badge status-${project.status}">${project.status}</span>
                </div>
                <div class="info-item">
                    <label>Duration:</label>
                    <span>${project.duration_weeks ? `${project.duration_weeks} weeks` : 'Not specified'}</span>
                </div>
                <div class="info-item">
                    <label>Max Participants:</label>
                    <span>${project.max_participants || 'Unlimited'}</span>
                </div>
                <div class="info-item">
                    <label>Start Date:</label>
                    <span>${project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Not scheduled'}</span>
                </div>
                <div class="info-item">
                    <label>End Date:</label>
                    <span>${project.end_date ? new Date(project.end_date).toLocaleDateString() : 'Not scheduled'}</span>
                </div>
                ${project.objectives && project.objectives.length > 0 ? `
                    <div class="info-item full-width">
                        <label>Learning Objectives:</label>
                        <ul class="objectives-list">
                            ${project.objectives.map(obj => `<li>${obj}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${project.target_roles && project.target_roles.length > 0 ? `
                    <div class="info-item full-width">
                        <label>Target Roles:</label>
                        <span>${project.target_roles.join(', ')}</span>
                    </div>
                ` : ''}
            </div>
        `;
        
        projectInfoDisplay.innerHTML = projectInfo;
    }

    async loadProjectData(project) {
        try {
            // Load project-specific members, tracks, and meeting rooms
            await Promise.allSettled([
                this.loadProjectMembers(project.id),
                this.loadProjectTracks(project.id),
                this.loadProjectMeetingRooms(project.id)
            ]);
            
            // Update project stats
            this.updateProjectStats();
            
        } catch (error) {
            console.error('Failed to load project data:', error);
            showNotification('Failed to load project data', 'error');
        }
    }

    async loadProjectMembers(projectId) {
        try {
            // For now, filter existing members by project
            // In a real implementation, this would be a project-specific API call
            this.projectMembers = this.members.filter(member => 
                member.project_ids && member.project_ids.includes(projectId)
            );
            
            this.renderProjectMembers();
            
        } catch (error) {
            console.error('Failed to load project members:', error);
            this.projectMembers = [];
        }
    }

    async loadProjectTracks(projectId) {
        try {
            // For now, filter existing tracks by project
            // In a real implementation, this would be a project-specific API call
            this.projectTracks = this.tracks.filter(track => 
                track.project_id === projectId
            );
            
            this.renderProjectTracks();
            
        } catch (error) {
            console.error('Failed to load project tracks:', error);
            this.projectTracks = [];
        }
    }

    async loadProjectMeetingRooms(projectId) {
        try {
            // For now, filter existing meeting rooms by project
            // In a real implementation, this would be a project-specific API call
            this.projectMeetingRooms = this.meetingRooms.filter(room => 
                room.project_id === projectId
            );
            
            this.renderProjectMeetingRooms();
            
        } catch (error) {
            console.error('Failed to load project meeting rooms:', error);
            this.projectMeetingRooms = [];
        }
    }

    updateProjectStats() {
        // Count different types of members
        const instructors = this.projectMembers.filter(m => m.role_type === 'instructor').length;
        
        // Update stat displays
        document.getElementById('projectMemberCount').textContent = this.projectMembers.length;
        document.getElementById('projectTrackCount').textContent = this.projectTracks.length;
        document.getElementById('projectMeetingRoomCount').textContent = this.projectMeetingRooms.length;
        document.getElementById('projectInstructorCount').textContent = instructors;
    }

    renderProjectMembers() {
        const container = document.getElementById('projectMembersContainer');
        
        if (this.projectMembers.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h4>No Members Yet</h4>
                    <p>Add members to this project to get started.</p>
                    <button class="btn btn-primary" onclick="orgAdmin.showAddProjectMemberModal()">
                        <i class="fas fa-user-plus"></i> Add First Member
                    </button>
                </div>
            `;
            return;
        }

        const membersHtml = this.projectMembers.map(member => `
            <div class="member-card">
                <div class="member-info">
                    <h4>${member.name || 'Unknown Name'}</h4>
                    <p class="member-email">${member.email}</p>
                    <span class="member-role role-${member.role_type}">${member.role_type}</span>
                </div>
                <div class="member-actions">
                    <button class="btn btn-sm btn-outline" onclick="orgAdmin.editProjectMember('${member.membership_id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="orgAdmin.removeProjectMember('${member.membership_id}')">
                        <i class="fas fa-user-minus"></i> Remove
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = membersHtml;
    }

    renderProjectTracks() {
        const container = document.getElementById('projectTracksContainer');
        
        if (this.projectTracks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-road"></i>
                    <h4>No Learning Tracks</h4>
                    <p>Create learning tracks to organize course content for this project.</p>
                    <button class="btn btn-primary" onclick="orgAdmin.showCreateProjectTrackModal()">
                        <i class="fas fa-plus"></i> Create First Track
                    </button>
                </div>
            `;
            return;
        }

        const tracksHtml = this.projectTracks.map(track => `
            <div class="track-card">
                <div class="track-info">
                    <h4>${track.name}</h4>
                    <p class="track-description">${track.description || 'No description'}</p>
                    <div class="track-meta">
                        <span class="meta-item">
                            <i class="fas fa-users"></i>
                            ${track.enrolled_count || 0} students
                        </span>
                        <span class="meta-item">
                            <i class="fas fa-clock"></i>
                            ${track.estimated_hours || 0} hours
                        </span>
                    </div>
                </div>
                <div class="track-actions">
                    <button class="btn btn-sm btn-primary" onclick="orgAdmin.viewTrack('${track.id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="orgAdmin.editTrack('${track.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = tracksHtml;
    }

    renderProjectMeetingRooms() {
        const container = document.getElementById('projectMeetingRoomsContainer');
        
        if (this.projectMeetingRooms.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-video"></i>
                    <h4>No Meeting Rooms</h4>
                    <p>Create meeting rooms for project collaboration and training sessions.</p>
                    <button class="btn btn-primary" onclick="orgAdmin.showCreateProjectRoomModal()">
                        <i class="fas fa-video"></i> Create First Room
                    </button>
                </div>
            `;
            return;
        }

        const roomsHtml = this.projectMeetingRooms.map(room => `
            <div class="meeting-room-card">
                <div class="room-info">
                    <h4>${room.name}</h4>
                    <p class="room-platform">${room.platform} • ${room.room_type}</p>
                    <div class="room-meta">
                        <span class="room-status status-${room.status}">${room.status}</span>
                        ${room.max_participants ? `<span class="meta-item">${room.max_participants} max</span>` : ''}
                    </div>
                </div>
                <div class="room-actions">
                    ${room.join_url ? `
                        <button class="btn btn-sm btn-success" onclick="window.open('${room.join_url}', '_blank')">
                            <i class="fas fa-video"></i> Join
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-outline" onclick="orgAdmin.editMeetingRoom('${room.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = roomsHtml;
    }

    setupProjectContentTabs() {
        // Handle project content tab switching
        const tabButtons = document.querySelectorAll('.project-content-tabs .tab-button');
        const tabPanes = document.querySelectorAll('.project-content-tabs .tab-pane');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetContent = button.getAttribute('data-content');
                
                // Update active button
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update active pane
                tabPanes.forEach(pane => {
                    pane.classList.remove('active');
                });
                
                const targetPane = document.getElementById(targetContent);
                if (targetPane) {
                    targetPane.classList.add('active');
                }
            });
        });
    }

    backToProjects() {
        // Hide project details tab and show projects tab
        const projectDetailsTab = document.querySelector('[data-tab="project-details"]');
        if (projectDetailsTab) {
            projectDetailsTab.style.display = 'none';
        }
        
        // Clear selected project
        this.selectedProject = null;
        
        // Switch back to projects tab
        this.showTab('projects');
        
        showNotification('Returned to projects view', 'info');
    }

    editProject(projectId) {
        showNotification('Project editing will be available soon', 'info');
        // TODO: Implement project editing
    }

    manageProjectMembers(projectId) {
        showNotification('Project member management will be available soon', 'info');
        // TODO: Implement project member management
    }

    filterProjects() {
        const statusFilter = document.getElementById('projectStatusFilter').value;
        const projectCards = document.querySelectorAll('.project-card');
        
        projectCards.forEach(card => {
            if (!statusFilter || card.getAttribute('data-status') === statusFilter) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    viewReports() {
        showNotification('Organization reports will be available soon', 'info');
        // TODO: Implement reports view
    }

    async removeMember(membershipId) {
        if (!confirm('Are you sure you want to remove this member? This action cannot be undone.')) {
            return;
        }

        try {
            this.showLoadingOverlay(true);
            
            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            const response = await fetch(`${orgApiBase}/api/v1/rbac/organizations/${this.currentOrganizationId}/members/${membershipId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to remove member');
            }

            await this.loadMembers();
            showNotification('Member removed successfully', 'success');
            
        } catch (error) {
            console.error('Failed to remove member:', error);
            showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async deleteRoom(roomId) {
        if (!confirm('Are you sure you want to delete this meeting room? This action cannot be undone.')) {
            return;
        }

        try {
            this.showLoadingOverlay(true);
            
            const orgApiBase = window.CONFIG?.API_URLS?.ORGANIZATION_MANAGEMENT || `https://${window.location.hostname}:8008`;
            const response = await fetch(`${orgApiBase}/api/v1/rbac/meeting-rooms/${roomId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete meeting room');
            }

            await this.loadMeetingRooms();
            showNotification('Meeting room deleted successfully', 'success');
            
        } catch (error) {
            console.error('Failed to delete meeting room:', error);
            showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    // Filter Functions
    filterMembers() {
        const roleFilter = document.getElementById('memberRoleFilter').value;
        const memberCards = document.querySelectorAll('.member-card');
        
        memberCards.forEach(card => {
            if (!roleFilter || card.getAttribute('data-role') === roleFilter) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    filterMeetingRooms() {
        const platformFilter = document.getElementById('platformFilter').value;
        const typeFilter = document.getElementById('roomTypeFilter').value;
        const roomCards = document.querySelectorAll('.meeting-room-card');
        
        roomCards.forEach(card => {
            const platform = card.getAttribute('data-platform');
            const type = card.getAttribute('data-type');
            
            const matchesPlatform = !platformFilter || platform === platformFilter;
            const matchesType = !typeFilter || type === typeFilter;
            
            if (matchesPlatform && matchesType) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Utility Functions
    getRoleIcon(role) {
        const icons = {
            'organization_admin': 'fa-crown',
            'instructor': 'fa-chalkboard-teacher',
            'student': 'fa-user-graduate'
        };
        return icons[role] || 'fa-user';
    }

    formatRoleName(role) {
        const names = {
            'organization_admin': 'Organization Admin',
            'instructor': 'Instructor',
            'student': 'Student'
        };
        return names[role] || role;
    }

    formatRoomType(type) {
        const names = {
            'organization_room': 'Organization Room',
            'project_room': 'Project Room',
            'track_room': 'Track Room',
            'instructor_room': 'Instructor Room'
        };
        return names[type] || type;
    }

    joinRoom(joinUrl) {
        if (joinUrl) {
            window.open(joinUrl, '_blank');
        }
    }

    showLoadingOverlay(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }
    
    showNewOrganizationWelcome() {
        // Add a welcome message to the overview tab for new organizations
        const overviewTab = document.getElementById('overview-tab');
        const existingWelcome = overviewTab.querySelector('.welcome-message');
        
        if (!existingWelcome) {
            const welcomeHTML = `
                <div class="welcome-message" style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #495057; margin-bottom: 15px;">
                        <i class="fas fa-rocket" style="color: #007bff;"></i> 
                        Welcome to Your Organization Dashboard!
                    </h3>
                    <p style="color: #6c757d; margin-bottom: 15px;">
                        Your organization is being set up. The RBAC (Role-Based Access Control) system is still being configured. 
                        In the meantime, you can explore the interface and see what features will be available.
                    </p>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <span style="background: #e9ecef; padding: 5px 10px; border-radius: 4px; font-size: 14px;">
                            <i class="fas fa-users"></i> Member Management
                        </span>
                        <span style="background: #e9ecef; padding: 5px 10px; border-radius: 4px; font-size: 14px;">
                            <i class="fas fa-road"></i> Learning Tracks
                        </span>
                        <span style="background: #e9ecef; padding: 5px 10px; border-radius: 4px; font-size: 14px;">
                            <i class="fas fa-video"></i> Meeting Rooms
                        </span>
                    </div>
                </div>
            `;
            
            // Insert after the overview stats grid
            const statsGrid = overviewTab.querySelector('.overview-grid');
            if (statsGrid) {
                statsGrid.insertAdjacentHTML('afterend', welcomeHTML);
            }
        }
    }
    
    /**
     * Get user initials for avatar display
     */
    getUserInitials(name) {
        if (!name) return '?';
        
        // Handle email format
        if (name.includes('@')) {
            name = name.split('@')[0];
        }
        
        // Split by space and take first letter of each word
        const nameParts = name.split(' ').filter(part => part.length > 0);
        if (nameParts.length >= 2) {
            return (nameParts[0][0] + nameParts[1][0]).toUpperCase();
        } else if (nameParts.length === 1) {
            return nameParts[0].substring(0, 2).toUpperCase();
        }
        
        return '?';
    }
    
    /**
     * Show loading state for async operations
     */
    showLoading(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="loading-container" style="display: flex; align-items: center; justify-content: center; padding: 2rem; flex-direction: column; gap: 1rem;">
                    <div class="loading-spinner"></div>
                    <p style="color: var(--text-secondary); font-size: var(--font-size-sm);">${message}</p>
                </div>
            `;
        }
    }
    
    /**
     * Create skeleton loading placeholder
     */
    createSkeleton(width = '100%', height = '20px') {
        return `<div class="skeleton" style="width: ${width}; height: ${height};"></div>`;
    }
    
    /**
     * Initialize data visualizations
     */
    initializeDataVisualizations() {
        // Create enhanced stat cards
        this.createStatCards();
        
        // Create analytics charts
        this.createAnalyticsCharts();
        
        // Create projects data table
        this.createProjectsTable();
        
        // Create activity timeline
        this.createActivityTimeline();
    }
    
    /**
     * Create enhanced stat cards with trends
     */
    createStatCards() {
        // Projects stat card
        window.dataViz.createStatCard('projects-stat-card', {
            title: 'Active Projects',
            value: this.projects.length || 0,
            trend: 15,
            trendValue: 15,
            icon: 'fas fa-folder-open',
            description: 'Currently active learning projects',
            miniChart: { percentage: 75 }
        });
        
        // Members stat card
        window.dataViz.createStatCard('members-stat-card', {
            title: 'Team Members',
            value: this.members.length || 0,
            trend: 8,
            trendValue: 8,
            icon: 'fas fa-users',
            description: 'Organization members and instructors',
            miniChart: { percentage: 60 }
        });
        
        // Activity stat card
        window.dataViz.createStatCard('activity-stat-card', {
            title: 'Weekly Activity',
            value: 342,
            trend: 12,
            trendValue: 12,
            icon: 'fas fa-chart-line',
            description: 'Learning activities this week',
            miniChart: { percentage: 85 }
        });
        
        // Completion stat card
        window.dataViz.createStatCard('completion-stat-card', {
            title: 'Completion Rate',
            value: '89%',
            trend: 5,
            trendValue: 5,
            icon: 'fas fa-trophy',
            description: 'Average course completion rate',
            miniChart: { percentage: 89 }
        });
    }
    
    /**
     * Create analytics charts
     */
    createAnalyticsCharts() {
        // Activity chart
        window.dataViz.createChartContainer('activity-chart', {
            title: 'Learning Activity Trends',
            type: 'line',
            icon: 'fas fa-chart-area',
            controls: [
                { label: '7D', value: '7d', onclick: 'orgAdmin.updateActivityChart("7d")' },
                { label: '30D', value: '30d', onclick: 'orgAdmin.updateActivityChart("30d")' },
                { label: '90D', value: '90d', onclick: 'orgAdmin.updateActivityChart("90d")' }
            ]
        });
        
        // Progress overview with ring charts
        const progressContainer = document.getElementById('progress-overview');
        if (progressContainer) {
            progressContainer.innerHTML = `
                <div class="chart-container">
                    <div class="chart-header">
                        <h3 class="chart-title">
                            <i class="fas fa-chart-pie" aria-hidden="true"></i>
                            Progress Overview
                        </h3>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); padding: var(--space-md);">
                        <div id="course-progress-ring"></div>
                        <div id="project-progress-ring"></div>
                    </div>
                </div>
            `;
            
            // Create progress rings
            window.dataViz.createProgressRing('course-progress-ring', {
                value: 78,
                max: 100,
                label: 'Course Progress'
            });
            
            window.dataViz.createProgressRing('project-progress-ring', {
                value: 65,
                max: 100,
                label: 'Project Completion'
            });
        }
    }
    
    /**
     * Create enhanced projects table
     */
    createProjectsTable() {
        const projectsData = {
            title: 'Recent Projects',
            columns: [
                { key: 'name', label: 'Project Name', type: 'text' },
                { key: 'members', label: 'Members', type: 'text' },
                { key: 'progress', label: 'Progress', type: 'chart' },
                { key: 'status', label: 'Status', type: 'badge' },
                { key: 'trend', label: 'Trend', type: 'trend' }
            ],
            rows: [
                {
                    name: 'AI Fundamentals Course',
                    members: '24 students',
                    progress: 78,
                    status: 'Active',
                    trend: 12
                },
                {
                    name: 'Data Science Track',
                    members: '18 students', 
                    progress: 45,
                    status: 'Active',
                    trend: 8
                },
                {
                    name: 'Web Development Bootcamp',
                    members: '32 students',
                    progress: 92,
                    status: 'Completing',
                    trend: 15
                },
                {
                    name: 'Machine Learning Lab',
                    members: '12 students',
                    progress: 23,
                    status: 'Active',
                    trend: -2
                }
            ],
            actions: [
                {
                    label: 'Export',
                    icon: 'fas fa-download',
                    onclick: 'orgAdmin.exportProjectData()'
                },
                {
                    label: 'Refresh',
                    icon: 'fas fa-sync-alt',
                    onclick: 'orgAdmin.refreshProjectsTable()'
                }
            ]
        };
        
        window.dataViz.createDataTable('projects-table', projectsData);
    }
    
    /**
     * Create activity timeline
     */
    createActivityTimeline() {
        const activities = [
            {
                title: 'New Course Launched',
                description: 'AI Fundamentals Course has been published and is now available for enrollment.',
                timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() // 2 hours ago
            },
            {
                title: 'Student Milestone Achieved',
                description: 'Sarah Chen completed the Data Science Track with a perfect score.',
                timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString() // 5 hours ago
            },
            {
                title: 'Meeting Room Created',
                description: 'New virtual meeting room set up for the Machine Learning Lab sessions.',
                timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() // 1 day ago
            },
            {
                title: 'Instructor Added',
                description: 'Dr. Michael Rodriguez joined as a new instructor for advanced courses.',
                timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString() // 3 days ago
            }
        ];
        
        window.dataViz.createActivityTimeline('activity-timeline', activities);
    }
    
    /**
     * Update activity chart for different time periods
     */
    updateActivityChart(period) {
        // Update chart period selection
        document.querySelectorAll('.chart-period-selector').forEach(btn => {
            btn.classList.remove('active');
        });
        
        document.querySelector(`[data-period="${period}"]`).classList.add('active');
        
        // Show loading state
        window.dataViz.showChartLoading('activity-chart');
        
        // Simulate data loading
        setTimeout(() => {
            const content = document.getElementById('activity-chart-content');
            if (content) {
                content.innerHTML = `
                    <div style="height: 200px; display: flex; align-items: center; justify-content: center; color: var(--text-muted);">
                        <div style="text-align: center;">
                            <i class="fas fa-chart-line" style="font-size: 3rem; margin-bottom: 1rem; color: var(--brand-primary-500);"></i>
                            <p>Activity data for ${period.toUpperCase()} period</p>
                            <p style="font-size: var(--font-size-sm);">Chart integration ready for external library</p>
                        </div>
                    </div>
                `;
            }
        }, 1000);
        
        if (window.a11y) {
            window.a11y.announce(`Activity chart updated to show ${period} period`);
        }
    }
    
    /**
     * Export project data
     */
    exportProjectData() {
        if (window.a11y) {
            window.a11y.announce('Exporting project data');
        }
        showNotification('Project data export started', 'info');
        console.log('Exporting project data...');
    }
    
    /**
     * Refresh projects table
     */
    refreshProjectsTable() {
        if (window.a11y) {
            window.a11y.announce('Refreshing projects table');
        }
        showNotification('Projects table refreshed', 'success');
        this.createProjectsTable();
    }

    /**
     * Load assignments tab data
     * PURPOSE: Fetch and display track assignments for the organization
     */
    async loadAssignments() {
        try {
            const orgId = this.currentOrgId;
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/organizations/${orgId}/assignments`, {
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`
                }
            });

            if (response.ok) {
                const assignments = await response.json();
                this.renderAssignments(assignments);
            } else {
                console.error('Failed to load assignments');
                showNotification('Failed to load assignments', 'error');
            }
        } catch (error) {
            console.error('Error loading assignments:', error);
            showNotification('Error loading assignments', 'error');
        }
    }

    /**
     * Render assignments in the assignments tab
     */
    renderAssignments(assignments) {
        const container = document.getElementById('assignmentsContainer');
        if (!container) return;

        if (!assignments || assignments.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No assignments found</p></div>';
            return;
        }

        const assignmentsHtml = assignments.map(assignment => `
            <div class="assignment-card">
                <h4>${assignment.track_name || 'Unknown Track'}</h4>
                <p>Assigned to: ${assignment.user_name || 'Unknown User'}</p>
                <p>Status: ${assignment.status || 'Active'}</p>
            </div>
        `).join('');

        container.innerHTML = assignmentsHtml;
    }

    /**
     * Load settings tab data
     * PURPOSE: Display organization settings and configuration options
     */
    async loadSettings() {
        try {
            const orgId = this.currentOrgId;
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/organizations/${orgId}`, {
                headers: {
                    'Authorization': `Bearer ${Auth.getToken()}`
                }
            });

            if (response.ok) {
                const orgData = await response.json();
                this.renderSettings(orgData);
            } else {
                console.error('Failed to load settings');
                showNotification('Failed to load organization settings', 'error');
            }
        } catch (error) {
            console.error('Error loading settings:', error);
            showNotification('Error loading settings', 'error');
        }
    }

    /**
     * Render settings in the settings tab
     */
    renderSettings(orgData) {
        const container = document.getElementById('settingsContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="settings-section">
                <h3>Organization Settings</h3>
                <div class="setting-item">
                    <label>Organization Name:</label>
                    <p>${orgData.name || 'N/A'}</p>
                </div>
                <div class="setting-item">
                    <label>Organization ID:</label>
                    <p>${orgData.id || 'N/A'}</p>
                </div>
                <div class="setting-item">
                    <label>Status:</label>
                    <p>${orgData.is_active ? 'Active' : 'Inactive'}</p>
                </div>
            </div>
        `;
    }

}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.orgAdmin = new OrgAdminDashboard();
});

