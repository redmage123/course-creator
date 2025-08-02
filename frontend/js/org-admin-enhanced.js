/**
 * Enhanced Organization Admin Dashboard
 * Comprehensive RBAC and Meeting Room Management
 */

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
        
        // Validate complete session state
        if (!currentUser || !authToken || !sessionStart || !lastActivity) {
            console.log('Session invalid: Missing session data');
            this.redirectToHome();
            return false;
        }
        
        // Check session timeout (8 hours from start)
        const now = Date.now();
        const sessionAge = now - parseInt(sessionStart);
        const timeSinceActivity = now - parseInt(lastActivity);
        const SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8 hours
        const INACTIVITY_TIMEOUT = 2 * 60 * 60 * 1000; // 2 hours
        
        if (sessionAge > SESSION_TIMEOUT || timeSinceActivity > INACTIVITY_TIMEOUT) {
            console.log('Session expired: Redirecting to home page');
            this.clearExpiredSession();
            return false;
        }
        
        // Check if user has org_admin role
        if (currentUser.role !== 'org_admin' && currentUser.role !== 'admin') {
            console.log('Invalid role for org admin dashboard:', currentUser.role);
            this.redirectToHome();
            return false;
        }
        
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
            
            // Show overview tab by default
            this.showTab('overview');
            
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showNotification('Failed to load dashboard', 'error');
        }
    }

    async loadCurrentUser() {
        """
        COMPREHENSIVE SESSION VALIDATION ON PAGE LOAD - ORG ADMIN DASHBOARD
        
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
        """
        
        // Validate session before making API calls
        if (!this.validateSession()) {
            return; // Validation function handles redirect
        }
        
        try {
            const response = await fetch('/api/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.clearExpiredSession();
                    return;
                }
                throw new Error('Failed to load user info');
            }

            this.currentUser = await response.json();
            this.currentOrganizationId = this.currentUser.organization_id;
            
            // Update UI
            document.getElementById('currentUserName').textContent = this.currentUser.name || this.currentUser.email;
            
        } catch (error) {
            console.error('Failed to load user:', error);
            // Redirect to login if authentication fails
            window.location.href = '/login.html';
        }
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.getAttribute('data-tab');
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
            await Promise.all([
                this.loadMembers(),
                this.loadTracks(),
                this.loadMeetingRooms(),
                this.loadProjects(),
                this.updateOverviewStats()
            ]);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async loadMembers() {
        try {
            const response = await fetch(`/api/v1/rbac/organizations/${this.currentOrganizationId}/members`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load members');
            }

            this.members = await response.json();
            this.renderMembers();
            
        } catch (error) {
            console.error('Failed to load members:', error);
            document.getElementById('membersContainer').innerHTML = 
                '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load members</p></div>';
        }
    }

    async loadTracks() {
        try {
            const response = await fetch(`/api/v1/organizations/${this.currentOrganizationId}/tracks`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load tracks');
            }

            this.tracks = await response.json();
            this.renderTracks();
            this.populateTrackSelects();
            
        } catch (error) {
            console.error('Failed to load tracks:', error);
            document.getElementById('tracksContainer').innerHTML = 
                '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load tracks</p></div>';
        }
    }

    async loadMeetingRooms() {
        try {
            const response = await fetch(`/api/v1/rbac/organizations/${this.currentOrganizationId}/meeting-rooms`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load meeting rooms');
            }

            this.meetingRooms = await response.json();
            this.renderMeetingRooms();
            
        } catch (error) {
            console.error('Failed to load meeting rooms:', error);
            document.getElementById('meetingRoomsContainer').innerHTML = 
                '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load meeting rooms</p></div>';
        }
    }

    async loadProjects() {
        try {
            const response = await fetch(`/api/v1/organizations/${this.currentOrganizationId}/projects`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load projects');
            }

            this.projects = await response.json();
            this.populateProjectSelects();
            
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    showTab(tabName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Show tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load tab-specific data
        switch (tabName) {
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
            // Count members by role
            const memberCounts = this.members.reduce((acc, member) => {
                acc[member.role_type] = (acc[member.role_type] || 0) + 1;
                return acc;
            }, {});

            // Update stats
            document.getElementById('totalMembers').textContent = this.members.length;
            document.getElementById('totalInstructors').textContent = memberCounts.instructor || 0;
            document.getElementById('totalStudents').textContent = memberCounts.student || 0;
            document.getElementById('totalTracks').textContent = this.tracks.length;
            document.getElementById('totalMeetingRooms').textContent = this.meetingRooms.length;

            // Update organization name
            if (this.currentUser && this.currentUser.organization_name) {
                document.getElementById('orgName').textContent = this.currentUser.organization_name;
            }

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

            const response = await fetch(`/api/v1/rbac/organizations/${this.currentOrganizationId}/members`, {
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
            this.showNotification('Member added successfully', 'success');
            
        } catch (error) {
            console.error('Failed to add member:', error);
            this.showNotification(error.message, 'error');
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

            const response = await fetch(`/api/v1/rbac/projects/${selectedTrack.project_id}/students`, {
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
            this.showNotification('Student added successfully', 'success');
            
        } catch (error) {
            console.error('Failed to add student:', error);
            this.showNotification(error.message, 'error');
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

            const response = await fetch(`/api/v1/rbac/organizations/${this.currentOrganizationId}/meeting-rooms`, {
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
            this.showNotification('Meeting room created successfully', 'success');
            
        } catch (error) {
            console.error('Failed to create meeting room:', error);
            this.showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async removeMember(membershipId) {
        if (!confirm('Are you sure you want to remove this member? This action cannot be undone.')) {
            return;
        }

        try {
            this.showLoadingOverlay(true);
            
            const response = await fetch(`/api/v1/rbac/organizations/${this.currentOrganizationId}/members/${membershipId}`, {
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
            this.showNotification('Member removed successfully', 'success');
            
        } catch (error) {
            console.error('Failed to remove member:', error);
            this.showNotification(error.message, 'error');
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
            
            const response = await fetch(`/api/v1/rbac/meeting-rooms/${roomId}`, {
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
            this.showNotification('Meeting room deleted successfully', 'success');
            
        } catch (error) {
            console.error('Failed to delete meeting room:', error);
            this.showNotification(error.message, 'error');
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

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        const icon = notification.querySelector('.notification-icon');
        const messageElement = notification.querySelector('.notification-message');
        
        // Set icon based on type
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        icon.className = `notification-icon ${icons[type] || icons.info}`;
        messageElement.textContent = message;
        notification.className = `notification ${type}`;
        notification.style.display = 'flex';
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.orgAdmin = new OrgAdminDashboard();
});

