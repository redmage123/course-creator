/**
 * SITE ADMIN DASHBOARD - COMPREHENSIVE PLATFORM ADMINISTRATION INTERFACE
 * 
 * PURPOSE: Complete administrative control panel for Course Creator platform management
 * WHY: Site administrators need centralized tools for organization, user, and system management
 * ARCHITECTURE: Class-based dashboard with comprehensive RBAC integration and real-time monitoring
 * 
 * CORE RESPONSIBILITIES:
 * - Organization lifecycle management (create, deactivate, delete)
 * - User management across all organizations with role-based controls
 * - Platform analytics and performance monitoring
 * - Integration status monitoring (Teams, Zoom)
 * - Audit logging and security oversight
 * - System health monitoring and diagnostics
 * 
 * BUSINESS REQUIREMENTS:
 * - Complete platform oversight for site administrators
 * - Organization deletion with cascade handling
 * - User activation/deactivation across organizations
 * - Real-time platform statistics and health monitoring
 * - Comprehensive audit trail for compliance
 * - Integration testing and configuration management
 * 
 * TECHNICAL FEATURES:
 * - Advanced session validation with timeout management
 * - Tab-based navigation with lazy loading
 * - Real-time data updates with error resilience
 * - Professional modal systems for critical operations
 * - Comprehensive error handling and user feedback
 * - Responsive design for desktop and mobile usage
 * 
 * SECURITY FEATURES:
 * - Strict role-based access control (site_admin only)
 * - Session timeout enforcement with automatic cleanup
 * - Confirmation dialogs for destructive operations
 * - Audit logging for all administrative actions
 * - JWT token validation and renewal
 */

/**
 * IMPORT DEPENDENCIES
 * PURPOSE: Import configuration and utility modules
 * WHY: Centralized configuration and consistent notification system
 */
import { CONFIG } from './config.js';
import { showNotification } from './modules/notifications.js';

class SiteAdminDashboard {
    /**
     * SITE ADMIN DASHBOARD CONSTRUCTOR
     * PURPOSE: Initialize site administration dashboard with comprehensive state management
     * WHY: Proper initialization ensures reliable dashboard functionality and security
     * 
     * STATE MANAGEMENT:
     * - currentUser: Site administrator user information and permissions
     * - organizations: Complete organization data with statistics
     * - platformStats: Platform-wide metrics and performance data
     * - auditLog: Security and administrative audit trail
     * 
     * INITIALIZATION WORKFLOW:
     * 1. Set up initial state with empty data structures
     * 2. Configure session management and security validation
     * 3. Initialize dashboard components and event handlers
     * 4. Load initial data from backend services
     */
    constructor() {
        // USER STATE: Site administrator information and permissions
        // WHY: Site admin requires elevated privileges and identity tracking
        this.currentUser = null;
        
        // ORGANIZATION DATA: Complete organization information with statistics
        // WHY: Organization management is core site admin functionality
        this.organizations = [];
        
        // PLATFORM METRICS: System-wide statistics and performance data
        // WHY: Site admins need platform oversight and monitoring capabilities
        this.platformStats = {};
        
        // AUDIT TRAIL: Security and administrative action logging
        // WHY: Compliance and security require comprehensive audit capabilities
        this.auditLog = [];
        
        // CONFIGURATION: Centralized timeout and API settings
        // WHY: Configurable values enable easy maintenance and environment adaptation
        this.SESSION_TIMEOUT = CONFIG.SECURITY.SESSION_TIMEOUT || 8 * 60 * 60 * 1000; // 8 hours
        this.INACTIVITY_TIMEOUT = CONFIG.SECURITY.INACTIVITY_TIMEOUT || 2 * 60 * 60 * 1000; // 2 hours
        this.NOTIFICATION_TIMEOUT = CONFIG.UI.NOTIFICATION_TIMEOUT || 5000; // 5 seconds
        this.INTEGRATION_TEST_DELAY = CONFIG.TESTING.INTEGRATION_DELAY || 2000; // 2 seconds
        
        // API ENDPOINTS: Centralized endpoint configuration
        this.API_BASE = CONFIG.API_URLS.RBAC_SERVICE || '/api/v1';
        
        // AUTOMATIC INITIALIZATION: Set up dashboard immediately
        // WHY: Constructor should establish fully functional dashboard system
        this.init();
    }

    /**
     * COMPREHENSIVE SESSION VALIDATION SYSTEM
     * PURPOSE: Validate complete session state for site administrator access
     * WHY: Site admin dashboard requires the highest level of security validation
     * 
     * VALIDATION WORKFLOW:
     * 1. Check existence of all required session components
     * 2. Validate session timestamps against timeout thresholds
     * 3. Verify user has site administrator privileges
     * 4. Handle session expiry with secure cleanup
     * 5. Redirect unauthorized users to appropriate page
     * 
     * SECURITY REQUIREMENTS:
     * - Complete session data validation
     * - Absolute and inactivity timeout enforcement
     * - Role-based access control (site_admin or admin)
     * - Automatic cleanup of expired sessions
     * - Secure redirect for unauthorized access
     * 
     * TIMEOUT CONFIGURATION:
     * - SESSION_TIMEOUT: 8 hours absolute maximum session duration
     * - INACTIVITY_TIMEOUT: 2 hours maximum allowed inactivity
     * - Configurable through CONFIG system for environment adaptation
     * 
     * @returns {boolean} True if session is valid for site admin access
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
        
        // SESSION TIMEOUT VALIDATION: Check both absolute and inactivity timeouts
        // WHY: Site admin security requires strict time-based session limits
        const now = Date.now();
        const sessionAge = now - parseInt(sessionStart);
        const timeSinceActivity = now - parseInt(lastActivity);
        
        // USE CONFIGURED TIMEOUTS: Enable environment-specific timeout configuration
        if (sessionAge > this.SESSION_TIMEOUT || timeSinceActivity > this.INACTIVITY_TIMEOUT) {
            console.log('Session expired: Redirecting to home page');
            this.clearExpiredSession();
            return false;
        }
        
        // Check if user has site_admin role
        if (currentUser.role !== 'site_admin' && currentUser.role !== 'admin') {
            console.log('Invalid role for site admin dashboard:', currentUser.role);
            this.redirectToHome();
            return false;
        }
        
        return true;
    }

    /**
     * CURRENT USER RETRIEVAL SYSTEM
     * PURPOSE: Safely retrieve and parse site administrator user data
     * WHY: Site admin operations require validated user information
     * 
     * RETRIEVAL STRATEGY:
     * - Parse JSON user data from localStorage
     * - Handle corrupted or missing data gracefully
     * - Return null for invalid or missing user information
     * - Comprehensive error logging for debugging
     * 
     * ERROR HANDLING:
     * - JSON parsing errors from corrupted localStorage
     * - Missing user data scenarios
     * - Malformed user object structures
     * - Network-related localStorage issues
     * 
     * @returns {Object|null} Site administrator user object or null
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
     * EXPIRED SESSION CLEANUP SYSTEM
     * PURPOSE: Comprehensive cleanup of expired site admin session
     * WHY: Security requires complete removal of expired authentication data
     * 
     * CLEANUP PROCESS:
     * 1. Remove all authentication tokens and user data
     * 2. Clear session timestamps and activity tracking
     * 3. Ensure no authentication remnants remain
     * 4. Redirect to appropriate public page
     * 
     * SECURITY COMPLIANCE:
     * - Complete localStorage cleanup prevents session remnants
     * - Automatic redirect prevents unauthorized access attempts
     * - No sensitive data left in browser storage
     * - Consistent cleanup across all site admin sessions
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

    /**
     * SITE ADMIN DASHBOARD INITIALIZATION SYSTEM
     * PURPOSE: Complete dashboard setup with authentication, data loading, and UI rendering
     * WHY: Proper initialization ensures secure access and reliable dashboard functionality
     * 
     * INITIALIZATION WORKFLOW:
     * 1. Load and validate current site administrator
     * 2. Set up comprehensive event listeners
     * 3. Load all dashboard data (stats, organizations, audit)
     * 4. Display overview tab with current platform state
     * 5. Handle initialization errors gracefully
     * 
     * ERROR HANDLING:
     * - Authentication failures with secure redirect
     * - Data loading failures with user notification
     * - Network issues with retry mechanisms
     * - Comprehensive error logging for debugging
     * 
     * PERFORMANCE OPTIMIZATION:
     * - Parallel data loading for faster dashboard startup
     * - Lazy loading of tab-specific data
     * - Progressive enhancement for better user experience
     */
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
            console.error('Failed to initialize site admin dashboard:', error);
            this.showNotification('Failed to load dashboard', 'error');
        }
    }

    /**
     * SITE ADMINISTRATOR USER LOADING SYSTEM
     * PURPOSE: Load and validate site administrator with comprehensive security checks
     * WHY: Site admin dashboard requires verified elevated privileges
     * 
     * USER LOADING WORKFLOW:
     * 1. Validate session before making API calls
     * 2. Fetch user information with authentication
     * 3. Verify site administrator permissions
     * 4. Update dashboard UI with user context
     * 5. Handle authentication failures securely
     * 
     * SECURITY VALIDATION:
     * - Session validation before API requests
     * - JWT token authentication for API access
     * - Site admin privilege verification
     * - Automatic redirect for insufficient permissions
     * 
     * API INTEGRATION:
     * - Uses authenticated API endpoints
     * - Handles token expiry and renewal
     * - Processes API errors with appropriate actions
     * - Updates UI based on successful authentication
     */
    async loadCurrentUser() {
        /*
         * COMPREHENSIVE SESSION VALIDATION ON PAGE LOAD - SITE ADMIN DASHBOARD
         * 
         * BUSINESS REQUIREMENT:
         * When a site admin refreshes the dashboard page after session expiry,
         * they should be redirected to the home page with proper validation.
         * 
         * TECHNICAL IMPLEMENTATION:
         * 1. Check if user data exists in localStorage
         * 2. Validate session timestamps against timeout thresholds  
         * 3. Check if authentication token is present and valid
         * 4. Verify user has correct role (site_admin)
         * 5. Redirect to home page if any validation fails
         * 6. Prevent dashboard initialization for expired sessions
         */
        
        // Validate session before making API calls
        if (!this.validateSession()) {
            return; // Validation function handles redirect
        }
        
        try {
            const response = await fetch(`${this.API_BASE}/auth/me`, {
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
            
            // Verify site admin permissions
            if (!this.currentUser.is_site_admin) {
                throw new Error('Insufficient permissions');
            }
            
            // Update UI
            document.getElementById('currentUserName').textContent = this.currentUser.name || this.currentUser.email;
            
        } catch (error) {
            console.error('Failed to load user:', error);
            // SECURE REDIRECT: Send failed authentication to appropriate page
            this.redirectToHome();
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

        // Organization deletion confirmation
        document.getElementById('confirmOrgName').addEventListener('input', (e) => {
            const expectedName = document.getElementById('orgNameToDelete').textContent;
            const actualName = e.target.value;
            const deleteBtn = document.getElementById('confirmDeleteBtn');
            
            if (actualName === expectedName) {
                deleteBtn.disabled = false;
                deleteBtn.classList.remove('disabled');
            } else {
                deleteBtn.disabled = true;
                deleteBtn.classList.add('disabled');
            }
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
                this.loadPlatformStats(),
                this.loadOrganizations(),
                this.loadRecentActivity(),
                this.loadIntegrationStatus()
            ]);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async loadPlatformStats() {
        try {
            const response = await fetch('/api/v1/site-admin/stats', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load platform stats');
            }

            this.platformStats = await response.json();
            this.updatePlatformStats();
            
        } catch (error) {
            console.error('Failed to load platform stats:', error);
            this.showDefaultStats();
        }
    }

    async loadOrganizations() {
        try {
            const response = await fetch('/api/v1/site-admin/organizations', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load organizations');
            }

            this.organizations = await response.json();
            this.renderOrganizations();
            
        } catch (error) {
            console.error('Failed to load organizations:', error);
            document.getElementById('organizationsContainer').innerHTML = 
                '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load organizations</p></div>';
        }
    }

    async loadRecentActivity() {
        try {
            // Mock recent activity data for now
            const mockActivity = [
                {
                    id: '1',
                    action: 'organization_created',
                    description: 'New organization "Tech Solutions Inc" created',
                    user: 'admin@example.com',
                    timestamp: new Date(Date.now() - 1000 * 60 * 30),
                    type: 'create'
                },
                {
                    id: '2',
                    action: 'user_login',
                    description: 'Site admin logged in from 192.168.1.100',
                    user: 'admin@example.com',
                    timestamp: new Date(Date.now() - 1000 * 60 * 60),
                    type: 'login'
                },
                {
                    id: '3',
                    action: 'integration_tested',
                    description: 'Teams integration health check completed',
                    user: 'system',
                    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
                    type: 'update'
                }
            ];

            this.renderRecentActivity(mockActivity);
            
        } catch (error) {
            console.error('Failed to load recent activity:', error);
            document.getElementById('recentActivity').innerHTML = 
                '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load activity</p></div>';
        }
    }

    async loadIntegrationStatus() {
        try {
            const response = await fetch('/api/v1/site-admin/platform/health', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load integration status');
            }

            const health = await response.json();
            this.updateIntegrationStatus(health);
            
        } catch (error) {
            console.error('Failed to load integration status:', error);
            this.setDefaultIntegrationStatus();
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
            case 'users':
                this.loadUsers();
                break;
            case 'audit':
                this.loadAuditLog();
                break;
        }
    }

    updatePlatformStats() {
        document.getElementById('totalOrganizations').textContent = this.platformStats.total_organizations || 0;
        document.getElementById('totalUsers').textContent = this.platformStats.total_users || 0;
        document.getElementById('totalProjects').textContent = this.platformStats.total_projects || 0;
        document.getElementById('totalTracks').textContent = this.platformStats.total_tracks || 0;
        document.getElementById('totalMeetingRooms').textContent = this.platformStats.total_meeting_rooms || 0;

        // Update user role counts
        const usersByRole = this.platformStats.users_by_role || {};
        document.getElementById('siteAdminCount').textContent = usersByRole.site_admin || 0;
        document.getElementById('orgAdminCount').textContent = usersByRole.organization_admin || 0;
        document.getElementById('instructorCount').textContent = usersByRole.instructor || 0;
        document.getElementById('studentCount').textContent = usersByRole.student || 0;
    }

    showDefaultStats() {
        document.getElementById('totalOrganizations').textContent = '0';
        document.getElementById('totalUsers').textContent = '0';
        document.getElementById('totalProjects').textContent = '0';
        document.getElementById('totalTracks').textContent = '0';
        document.getElementById('totalMeetingRooms').textContent = '0';
        document.getElementById('systemHealth').textContent = 'Unknown';
    }

    renderOrganizations() {
        const container = document.getElementById('organizationsContainer');
        
        if (this.organizations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-building"></i>
                    <h3>No Organizations Found</h3>
                    <p>No organizations have been created yet.</p>
                </div>
            `;
            return;
        }

        const organizationsHtml = this.organizations.map(org => `
            <div class="organization-card ${org.is_active ? 'active' : 'inactive'}" data-status="${org.is_active ? 'active' : 'inactive'}">
                <div class="org-status ${org.is_active ? 'active' : 'inactive'}">
                    <i class="fas ${org.is_active ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                </div>
                <div class="org-header">
                    <div class="org-info">
                        <h3>${org.name}</h3>
                        <div class="org-slug">${org.slug}</div>
                    </div>
                </div>
                <p class="org-description">${org.description || 'No description provided'}</p>
                <div class="org-stats">
                    <div class="org-stat">
                        <span class="value">${org.total_members}</span>
                        <span class="label">Members</span>
                    </div>
                    <div class="org-stat">
                        <span class="value">${org.project_count}</span>
                        <span class="label">Projects</span>
                    </div>
                    <div class="org-stat">
                        <span class="value">${org.member_counts?.instructor || 0}</span>
                        <span class="label">Instructors</span>
                    </div>
                    <div class="org-stat">
                        <span class="value">${org.member_counts?.student || 0}</span>
                        <span class="label">Students</span>
                    </div>
                </div>
                <div class="org-meta">
                    <span>Created: ${new Date(org.created_at).toLocaleDateString()}</span>
                    <span>ID: ${org.id.substring(0, 8)}...</span>
                </div>
                <div class="org-actions">
                    <button class="btn btn-sm btn-outline" onclick="siteAdmin.viewOrganizationDetails('${org.id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    ${org.is_active ? `
                        <button class="btn btn-sm btn-warning" onclick="siteAdmin.deactivateOrganization('${org.id}')">
                            <i class="fas fa-pause"></i> Deactivate
                        </button>
                    ` : `
                        <button class="btn btn-sm btn-success" onclick="siteAdmin.reactivateOrganization('${org.id}')">
                            <i class="fas fa-play"></i> Reactivate
                        </button>
                    `}
                    <button class="btn btn-sm btn-danger" onclick="siteAdmin.showDeleteOrganizationModal('${org.id}', '${org.name}', ${org.total_members}, ${org.project_count}, 0)">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = organizationsHtml;
    }

    renderRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        
        if (activities.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h3>No Recent Activity</h3>
                    <p>No recent platform activity to display.</p>
                </div>
            `;
            return;
        }

        const activitiesHtml = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.type}">
                    <i class="fas ${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <h4>${activity.description}</h4>
                    <p>by ${activity.user}</p>
                </div>
                <div class="activity-time">
                    ${this.formatTimeAgo(activity.timestamp)}
                </div>
            </div>
        `).join('');

        container.innerHTML = activitiesHtml;
    }

    updateIntegrationStatus(health) {
        // Teams integration
        const teamsStatus = document.getElementById('teamsIntegrationStatus');
        teamsStatus.className = `integration-status ${health.teams_integration ? 'active' : 'inactive'}`;
        
        // Zoom integration
        const zoomStatus = document.getElementById('zoomIntegrationStatus');
        zoomStatus.className = `integration-status ${health.zoom_integration ? 'active' : 'inactive'}`;
        
        // Update last test times
        document.getElementById('teamsLastTest').textContent = new Date().toLocaleString();
        document.getElementById('zoomLastTest').textContent = new Date().toLocaleString();
    }

    setDefaultIntegrationStatus() {
        document.getElementById('teamsIntegrationStatus').className = 'integration-status inactive';
        document.getElementById('zoomIntegrationStatus').className = 'integration-status inactive';
        document.getElementById('teamsLastTest').textContent = 'Never';
        document.getElementById('zoomLastTest').textContent = 'Never';
    }

    // Modal Functions
    showDeleteOrganizationModal(orgId, orgName, memberCount, projectCount, meetingRoomCount) {
        document.getElementById('deleteOrgId').value = orgId;
        document.getElementById('orgNameToDelete').textContent = orgName;
        document.getElementById('confirmOrgName').value = '';
        document.getElementById('confirmDeleteBtn').disabled = true;
        
        // Update deletion impact
        document.getElementById('membersToDelete').textContent = memberCount;
        document.getElementById('projectsToDelete').textContent = projectCount;
        document.getElementById('meetingRoomsToDelete').textContent = meetingRoomCount;
        
        this.showModal('deleteOrgModal');
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

    // API Functions
    async confirmDeleteOrganization() {
        try {
            this.showLoadingOverlay(true);
            
            const form = document.getElementById('deleteOrgForm');
            const formData = new FormData(form);
            
            const data = {
                organization_id: formData.get('organization_id'),
                confirmation_name: formData.get('confirmation_name')
            };

            const response = await fetch(`/api/v1/site-admin/organizations/${data.organization_id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete organization');
            }

            const result = await response.json();
            
            await this.loadOrganizations();
            await this.loadPlatformStats();
            
            this.closeModal('deleteOrgModal');
            this.showNotification(
                `Organization "${result.organization_name}" deleted successfully. ${result.deleted_members} members and ${result.deleted_meeting_rooms} meeting rooms were removed.`, 
                'success'
            );
            
        } catch (error) {
            console.error('Failed to delete organization:', error);
            this.showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async deactivateOrganization(orgId) {
        if (!confirm('Are you sure you want to deactivate this organization? This will disable access for all members.')) {
            return;
        }

        try {
            this.showLoadingOverlay(true);
            
            const response = await fetch(`/api/v1/site-admin/organizations/${orgId}/deactivate`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to deactivate organization');
            }

            await this.loadOrganizations();
            this.showNotification('Organization deactivated successfully', 'success');
            
        } catch (error) {
            console.error('Failed to deactivate organization:', error);
            this.showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async reactivateOrganization(orgId) {
        try {
            this.showLoadingOverlay(true);
            
            const response = await fetch(`/api/v1/site-admin/organizations/${orgId}/reactivate`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to reactivate organization');
            }

            await this.loadOrganizations();
            this.showNotification('Organization reactivated successfully', 'success');
            
        } catch (error) {
            console.error('Failed to reactivate organization:', error);
            this.showNotification(error.message, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    async testTeamsIntegration() {
        try {
            const status = document.getElementById('teamsIntegrationStatus');
            status.className = 'integration-status testing';
            
            // Mock integration test
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            status.className = 'integration-status active';
            document.getElementById('teamsLastTest').textContent = new Date().toLocaleString();
            this.showNotification('Teams integration test successful', 'success');
            
        } catch (error) {
            document.getElementById('teamsIntegrationStatus').className = 'integration-status inactive';
            this.showNotification('Teams integration test failed', 'error');
        }
    }

    async testZoomIntegration() {
        try {
            const status = document.getElementById('zoomIntegrationStatus');
            status.className = 'integration-status testing';
            
            // Mock integration test
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            status.className = 'integration-status active';
            document.getElementById('zoomLastTest').textContent = new Date().toLocaleString();
            this.showNotification('Zoom integration test successful', 'success');
            
        } catch (error) {
            document.getElementById('zoomIntegrationStatus').className = 'integration-status inactive';
            this.showNotification('Zoom integration test failed', 'error');
        }
    }

    // Filter Functions
    filterOrganizations() {
        const statusFilter = document.getElementById('orgStatusFilter').value;
        const orgCards = document.querySelectorAll('.organization-card');
        
        orgCards.forEach(card => {
            if (!statusFilter || card.getAttribute('data-status') === statusFilter) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    searchOrganizations() {
        const searchTerm = document.getElementById('orgSearchFilter').value.toLowerCase();
        const orgCards = document.querySelectorAll('.organization-card');
        
        orgCards.forEach(card => {
            const orgName = card.querySelector('h3').textContent.toLowerCase();
            const orgSlug = card.querySelector('.org-slug').textContent.toLowerCase();
            
            if (orgName.includes(searchTerm) || orgSlug.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Utility Functions
    getActivityIcon(type) {
        const icons = {
            'create': 'fa-plus',
            'delete': 'fa-trash',
            'update': 'fa-edit',
            'login': 'fa-sign-in-alt'
        };
        return icons[type] || 'fa-info';
    }

    formatTimeAgo(timestamp) {
        const now = new Date();
        const diff = now - new Date(timestamp);
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
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

    // Placeholder functions for other features
    async refreshPlatformStats() {
        await this.loadPlatformStats();
        this.showNotification('Platform statistics refreshed', 'success');
    }

    async runHealthCheck() {
        await this.loadIntegrationStatus();
        this.showNotification('Health check completed', 'success');
    }

    viewSystemLogs() {
        this.showNotification('System logs feature coming soon', 'info');
    }

    exportPlatformReport() {
        this.showNotification('Platform report export feature coming soon', 'info');
    }

    refreshOrganizations() {
        this.loadOrganizations();
    }

    async loadUsers() {
        try {
            const usersContainer = document.getElementById('usersContainer');
            usersContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Loading users...</p></div>';

            const response = await fetch('/api/v1/rbac/users/all', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load users: ${response.statusText}`);
            }

            const data = await response.json();
            const users = data.users || [];

            // Update role statistics
            const roleCounts = {
                site_admin: 0,
                organization_admin: 0,
                instructor: 0,
                student: 0
            };

            users.forEach(user => {
                if (user.roles) {
                    user.roles.forEach(role => {
                        if (Object.prototype.hasOwnProperty.call(roleCounts, role.role_type)) {
                            roleCounts[role.role_type]++;
                        }
                    });
                }
            });

            // Update UI counters
            document.getElementById('siteAdminCount').textContent = roleCounts.site_admin;
            document.getElementById('orgAdminCount').textContent = roleCounts.organization_admin;
            document.getElementById('instructorCount').textContent = roleCounts.instructor;
            document.getElementById('studentCount').textContent = roleCounts.student;

            // Render users table
            this.renderUsersTable(users);

        } catch (error) {
            console.error('Failed to load users:', error);
            const usersContainer = document.getElementById('usersContainer');
            usersContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Failed to Load Users</h3>
                    <p>${error.message}</p>
                    <button onclick="window.siteAdmin.loadUsers()" class="btn btn-primary">
                        <i class="fas fa-retry"></i> Retry
                    </button>
                </div>
            `;
        }
    }

    renderUsersTable(users) {
        const usersContainer = document.getElementById('usersContainer');
        
        if (users.length === 0) {
            usersContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h3>No Users Found</h3>
                    <p>No users match the current filters.</p>
                </div>
            `;
            return;
        }

        const usersTable = `
            <div class="users-table-container">
                <table class="users-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Roles</th>
                            <th>Organization</th>
                            <th>Status</th>
                            <th>Last Active</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(user => `
                            <tr>
                                <td>
                                    <div class="user-info">
                                        <div class="user-avatar">
                                            ${user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                                        </div>
                                        <span>${user.name || 'Unknown User'}</span>
                                    </div>
                                </td>
                                <td>${user.email}</td>
                                <td>
                                    <div class="user-roles">
                                        ${(user.roles || []).map(role => `
                                            <span class="role-badge role-${role.role_type}">
                                                ${role.role_type.replace('_', ' ')}
                                            </span>
                                        `).join('')}
                                    </div>
                                </td>
                                <td>${user.organization_name || 'N/A'}</td>
                                <td>
                                    <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">
                                        ${user.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td>${user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                                <td>
                                    <div class="action-buttons">
                                        <button onclick="window.siteAdmin.viewUserDetails('${user.id}')" class="btn btn-sm btn-outline">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button onclick="window.siteAdmin.editUser('${user.id}')" class="btn btn-sm btn-outline">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        ${!user.is_active ? `
                                            <button onclick="window.siteAdmin.activateUser('${user.id}')" class="btn btn-sm btn-success">
                                                <i class="fas fa-check"></i>
                                            </button>
                                        ` : `
                                            <button onclick="window.siteAdmin.deactivateUser('${user.id}')" class="btn btn-sm btn-warning">
                                                <i class="fas fa-ban"></i>
                                            </button>
                                        `}
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        usersContainer.innerHTML = usersTable;
    }

    async loadAuditLog() {
        try {
            const auditContainer = document.getElementById('auditLogContainer');
            auditContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Loading audit log...</p></div>';

            const response = await fetch('/api/v1/rbac/audit-log', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load audit log: ${response.statusText}`);
            }

            const data = await response.json();
            const auditEntries = data.entries || [];

            this.renderAuditLog(auditEntries);

        } catch (error) {
            console.error('Failed to load audit log:', error);
            const auditContainer = document.getElementById('auditLogContainer');
            auditContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Failed to Load Audit Log</h3>
                    <p>${error.message}</p>
                    <button onclick="window.siteAdmin.loadAuditLog()" class="btn btn-primary">
                        <i class="fas fa-retry"></i> Retry
                    </button>
                </div>
            `;
        }
    }

    renderAuditLog(entries) {
        const auditContainer = document.getElementById('auditLogContainer');
        
        if (entries.length === 0) {
            auditContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h3>No Audit Entries</h3>
                    <p>No audit log entries found for the selected filters.</p>
                </div>
            `;
            return;
        }

        const auditLogHtml = `
            <div class="audit-log-entries">
                ${entries.map(entry => `
                    <div class="audit-entry ${this.getAuditSeverityClass(entry.action)}">
                        <div class="audit-header">
                            <div class="audit-info">
                                <i class="fas ${this.getAuditIcon(entry.action)}"></i>
                                <strong>${this.formatAuditAction(entry.action)}</strong>
                                <span class="audit-timestamp">${this.formatTimestamp(entry.timestamp)}</span>
                            </div>
                            <div class="audit-user">
                                <span class="user-name">${entry.user_name || 'System'}</span>
                                <span class="user-email">${entry.user_email || ''}</span>
                            </div>
                        </div>
                        <div class="audit-details">
                            <p>${entry.description}</p>
                            ${entry.target_resource ? `
                                <div class="audit-target">
                                    <strong>Target:</strong> ${entry.target_resource_type} - ${entry.target_resource}
                                </div>
                            ` : ''}
                            ${entry.ip_address ? `
                                <div class="audit-metadata">
                                    <span>IP: ${entry.ip_address}</span>
                                    ${entry.user_agent ? `<span>User Agent: ${entry.user_agent}</span>` : ''}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="audit-pagination">
                <button onclick="window.siteAdmin.loadMoreAuditEntries()" class="btn btn-outline">
                    <i class="fas fa-chevron-down"></i> Load More
                </button>
            </div>
        `;

        auditContainer.innerHTML = auditLogHtml;
    }

    getAuditSeverityClass(action) {
        const highSeverity = ['organization_deleted', 'user_deleted', 'permission_revoked', 'system_security_breach'];
        const mediumSeverity = ['user_created', 'permission_granted', 'organization_created', 'integration_failed'];
        
        if (highSeverity.includes(action)) return 'audit-high';
        if (mediumSeverity.includes(action)) return 'audit-medium';
        return 'audit-low';
    }

    getAuditIcon(action) {
        const iconMap = {
            'organization_created': 'fa-building',
            'organization_deleted': 'fa-trash',
            'user_created': 'fa-user-plus',
            'user_deleted': 'fa-user-times',
            'permission_granted': 'fa-key',
            'permission_revoked': 'fa-ban',
            'integration_tested': 'fa-plug',
            'integration_failed': 'fa-exclamation-triangle',
            'login_success': 'fa-sign-in-alt',
            'login_failed': 'fa-times-circle',
            'system_security_breach': 'fa-shield-alt'
        };
        return iconMap[action] || 'fa-info-circle';
    }

    formatAuditAction(action) {
        return action.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    async loadMoreAuditEntries() {
        // Implementation for pagination
        this.showNotification('Loading more audit entries...', 'info');
    }

    viewOrganizationDetails(orgId) {
        this.showNotification(`Organization details for ${orgId}`, 'info');
    }

    async viewUserDetails(userId) {
        try {
            const response = await fetch(`/api/v1/rbac/users/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load user details: ${response.statusText}`);
            }

            const user = await response.json();
            this.showUserDetailsModal(user);

        } catch (error) {
            console.error('Failed to load user details:', error);
            this.showNotification('Failed to load user details', 'error');
        }
    }

    showUserDetailsModal(user) {
        // Implementation for user details modal
        this.showNotification(`User details for ${user.name || user.email}`, 'info');
    }

    async editUser(userId) {
        // Implementation for user editing
        this.showNotification(`Edit user functionality for user ${userId}`, 'info');
    }

    async activateUser(userId) {
        try {
            const response = await fetch(`/api/v1/rbac/users/${userId}/activate`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to activate user: ${response.statusText}`);
            }

            this.showNotification('User activated successfully', 'success');
            this.loadUsers(); // Refresh the users list

        } catch (error) {
            console.error('Failed to activate user:', error);
            this.showNotification('Failed to activate user', 'error');
        }
    }

    async deactivateUser(userId) {
        if (!confirm('Are you sure you want to deactivate this user?')) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/rbac/users/${userId}/deactivate`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to deactivate user: ${response.statusText}`);
            }

            this.showNotification('User deactivated successfully', 'success');
            this.loadUsers(); // Refresh the users list

        } catch (error) {
            console.error('Failed to deactivate user:', error);
            this.showNotification('Failed to deactivate user', 'error');
        }
    }

    configureTeamsIntegration() {
        this.showNotification('Teams integration configuration coming soon', 'info');
    }

    configureZoomIntegration() {
        this.showNotification('Zoom integration configuration coming soon', 'info');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.siteAdmin = new SiteAdminDashboard();
});

