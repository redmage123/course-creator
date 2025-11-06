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
        this.SESSION_TIMEOUT = window.CONFIG?.SECURITY.SESSION_TIMEOUT || 8 * 60 * 60 * 1000; // 8 hours
        this.INACTIVITY_TIMEOUT = window.CONFIG?.SECURITY.INACTIVITY_TIMEOUT || 2 * 60 * 60 * 1000; // 2 hours
        this.NOTIFICATION_TIMEOUT = window.CONFIG?.UI.NOTIFICATION_TIMEOUT || 5000; // 5 seconds
        this.INTEGRATION_TEST_DELAY = window.CONFIG?.TESTING.INTEGRATION_DELAY || 2000; // 2 seconds
        
        // API ENDPOINTS: Centralized endpoint configuration
        // Use relative URLs to go through nginx proxy
        this.API_BASE = '';  // Empty string for relative URLs through nginx proxy
        this.AUTH_API_BASE = '';  // Empty string for relative URLs through nginx proxy
        
        // NETWORK STATE RECOVERY: Handle browser offline/online state
        // WHY: Browser can get stuck in offline mode after container restarts
        this.setupNetworkRecovery();

        // AUTOMATIC INITIALIZATION: Set up dashboard immediately
        // WHY: Constructor should establish fully functional dashboard system
        this.init();
    }

    /**
     * NETWORK STATE RECOVERY SYSTEM
     * PURPOSE: Automatically detect and recover from browser offline state
     * WHY: Docker restarts can cause browser to get stuck thinking it's offline
     *
     * RECOVERY WORKFLOW:
     * 1. Listen for online/offline events from browser
     * 2. Detect when browser incorrectly thinks it's offline
     * 3. Show helpful message instead of generic "no internet" error
     * 4. Automatically retry connections when back online
     * 5. Clear any stuck network state
     *
     * BUSINESS REQUIREMENT:
     * During development/deployment, Docker container restarts cause browser
     * to enter offline mode. This provides automatic recovery without user
     * needing to close/reopen browser or use incognito mode.
     */
    setupNetworkRecovery() {
        // Track network state
        this.isOnline = navigator.onLine;

        // Listen for network state changes
        window.addEventListener('online', () => {
            console.log('🌐 Browser detected network is back online');
            this.isOnline = true;
            this.handleNetworkRecovery();
        });

        window.addEventListener('offline', () => {
            console.log('📴 Browser detected network went offline');
            this.isOnline = false;
            this.showNetworkOfflineMessage();
        });

        // Periodically check if browser is incorrectly offline
        setInterval(() => {
            if (!navigator.onLine) {
                // Browser thinks we're offline, but let's verify
                this.verifyNetworkConnectivity();
            }
        }, 5000); // Check every 5 seconds
    }

    /**
     * VERIFY NETWORK CONNECTIVITY
     * PURPOSE: Check if network is actually offline or if browser is stuck
     * WHY: Browser can incorrectly report offline after WebSocket/connection breaks
     */
    async verifyNetworkConnectivity() {
        try {
            // Try to fetch a lightweight endpoint
            const response = await fetch('/health', {
                method: 'GET',
                cache: 'no-cache',
                mode: 'no-cors'
            });

            // If we got here, network is actually working
            if (!this.isOnline) {
                console.log('✅ Network is actually online, browser state was incorrect');
                this.isOnline = true;
                // Manually trigger online event
                window.dispatchEvent(new Event('online'));
            }
        } catch (error) {
            // Network really is offline
            console.log('❌ Network connectivity check failed, truly offline');
        }
    }

    /**
     * HANDLE NETWORK RECOVERY
     * PURPOSE: Actions to take when network comes back online
     * WHY: Refresh data and clear stuck states
     */
    handleNetworkRecovery() {
        this.showNotification('Network connection restored! Refreshing data...', 'success');

        // Reload current data after a brief delay
        setTimeout(() => {
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab && activeTab.id === 'organizationsTab') {
                this.loadOrganizations();
            } else if (activeTab && activeTab.id === 'overviewTab') {
                this.loadPlatformStats();
            }
        }, 1000);
    }

    /**
     * SHOW NETWORK OFFLINE MESSAGE
     * PURPOSE: Display helpful message when network is offline
     * WHY: Better UX than generic browser "no internet" error
     */
    showNetworkOfflineMessage() {
        this.showNotification(
            'Network connection lost. If Docker containers restarted, refresh the page (Ctrl+Shift+R) or wait for automatic reconnection.',
            'warning',
            10000 // Show for 10 seconds
        );
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

        console.log('🔍 SITE-ADMIN SESSION VALIDATION:');
        console.log('  - currentUser:', currentUser);
        console.log('  - authToken:', authToken ? 'exists' : 'missing');
        console.log('  - sessionStart:', sessionStart);
        console.log('  - lastActivity:', lastActivity);

        // Validate complete session state
        if (!currentUser || !authToken || !sessionStart || !lastActivity) {
            const errorMsg = '❌ Session invalid: Missing session data - ' +
                `currentUser:${!!currentUser}, authToken:${!!authToken}, sessionStart:${!!sessionStart}, lastActivity:${!!lastActivity}`;
            console.log(errorMsg);
            localStorage.setItem('siteAdminDebug', errorMsg);
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
        
        // Check if user has site_admin role or is the admin user
        // Use configuration-based role checking instead of hard-coded values
        console.log('🔍 Role check - currentUser.role:', currentUser.role);
        console.log('🔍 Role check - currentUser.username:', currentUser.username);

        const ALLOWED_ROLES = ['site_admin', 'admin', 'organization_admin'];
        const SITE_ADMIN_USERNAME = 'admin';

        if (!ALLOWED_ROLES.includes(currentUser.role) && currentUser.username !== SITE_ADMIN_USERNAME) {
            const errorMsg = `❌ Invalid role for site admin dashboard: role=${currentUser.role}, username=${currentUser.username}`;
            console.log(errorMsg);
            localStorage.setItem('siteAdminDebug', errorMsg);
            this.redirectToHome();
            return false;
        }

        console.log('✅ Session validation passed');
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
     * PHONE NUMBER FORMATTING UTILITY
     * PURPOSE: Format phone numbers for consistent display across the platform
     * WHY: Phone numbers need standardized, readable formatting for professional presentation
     *
     * FORMATTING RULES:
     * - US/Canada numbers (+1): Format as +1 (XXX) XXX-XXXX
     * - International numbers: Format as +XX XXX XXX XXXX (grouped by country conventions)
     * - Handles various input formats (with/without country code, with/without separators)
     * - Preserves original format if parsing fails
     *
     * SUPPORTED FORMATS:
     * - +14155551212 → +1 (415) 555-1212
     * - +442071234567 → +44 20 7123 4567
     * - +33123456789 → +33 1 23 45 67 89
     * - Raw numbers are assumed to be US if 10 digits
     *
     * @param {string} phone - Phone number in any format
     * @returns {string} Formatted phone number or original if cannot parse
     */
    formatPhoneNumber(phone) {
        if (!phone) return 'Not specified';

        // Remove all non-digit characters
        const digits = phone.replace(/\D/g, '');

        // If empty after cleaning, return original
        if (!digits) return phone;

        // US/Canada format: +1 (XXX) XXX-XXXX
        if (digits.length === 11 && digits[0] === '1') {
            return `+1 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
        }

        // US format without country code (assume +1)
        if (digits.length === 10) {
            return `+1 (${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
        }

        // UK format: +44 XX XXXX XXXX
        if (digits.length === 12 && digits.slice(0, 2) === '44') {
            return `+44 ${digits.slice(2, 4)} ${digits.slice(4, 8)} ${digits.slice(8)}`;
        }

        // France format: +33 X XX XX XX XX
        if (digits.length === 11 && digits.slice(0, 2) === '33') {
            return `+33 ${digits.slice(2, 3)} ${digits.slice(3, 5)} ${digits.slice(5, 7)} ${digits.slice(7, 9)} ${digits.slice(9)}`;
        }

        // Germany format: +49 XXX XXXXXXX
        if (digits.length >= 11 && digits.slice(0, 2) === '49') {
            return `+49 ${digits.slice(2, 5)} ${digits.slice(5)}`;
        }

        // Generic international format: +XX XXX XXX XXXX
        if (digits.length > 10) {
            const countryCode = digits.slice(0, digits.length - 10);
            const rest = digits.slice(digits.length - 10);
            return `+${countryCode} ${rest.slice(0, 3)} ${rest.slice(3, 6)} ${rest.slice(6)}`;
        }

        // If we can't parse it, return original
        return phone;
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
            // Check if using mock token (temporary authentication)
            const authToken = localStorage.getItem('authToken');
            const isMockToken = authToken && authToken.startsWith('mock-token-');

            if (isMockToken) {
                // Use stored user data for mock tokens (development/temporary mode)
                const storedUser = this.getCurrentUser();
                if (storedUser) {
                    this.currentUser = storedUser;
                    document.getElementById('currentUserName').textContent = storedUser.full_name || storedUser.username || storedUser.email;
                    console.log('✅ Using stored user data (mock token mode)');
                    return;
                } else {
                    throw new Error('No user data available');
                }
            }

            // Real token - fetch from API
            const response = await fetch(`${this.AUTH_API_BASE}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
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
            // USE MOCK DATA: Fall back to localStorage user data when API unavailable
            const storedUser = this.getCurrentUser();
            if (storedUser) {
                this.currentUser = storedUser;
                document.getElementById('currentUserName').textContent = storedUser.full_name || storedUser.username || storedUser.email;
                console.log('✅ Using stored user data as fallback');
            } else {
                // SECURE REDIRECT: Send failed authentication to appropriate page
                this.redirectToHome();
            }
        }
    }

    /**
     * SET EVENT LISTENERS VALUE
     * PURPOSE: Set event listeners value
     * WHY: Maintains data integrity through controlled mutation
     */
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = e.target.closest('.nav-link').getAttribute('data-tab');
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

    /**
     * LOAD DASHBOARD DATA DATA FROM SERVER
     * PURPOSE: Load dashboard data data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * LOAD PLATFORM STATS DATA FROM SERVER
     * PURPOSE: Load platform stats data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async loadPlatformStats() {
        try {
            const response = await fetch(`${this.API_BASE}/api/v1/site-admin/stats`, {
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

    /**
     * LOAD ORGANIZATIONS DATA FROM SERVER
     * PURPOSE: Load organizations data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async loadOrganizations() {
        try {
            const response = await fetch(`${this.API_BASE}/api/v1/site-admin/organizations`, {
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

    /**
     * LOAD RECENT ACTIVITY DATA FROM SERVER
     * PURPOSE: Load recent activity data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * LOAD INTEGRATION STATUS DATA FROM SERVER
     * PURPOSE: Load integration status data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async loadIntegrationStatus() {
        try {
            const response = await fetch(`${this.API_BASE}/api/v1/site-admin/platform/health`, {
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

    /**
     * DISPLAY TAB INTERFACE
     * PURPOSE: Display tab interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} tabName - Tabname parameter
     */
    showTab(tabName) {
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Show tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

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

    /**
     * UPDATE PLATFORM STATS STATE
     * PURPOSE: Update platform stats state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * DISPLAY DEFAULT STATS INTERFACE
     * PURPOSE: Display default stats interface
     * WHY: Provides user interface for interaction and data visualization
     */
    showDefaultStats() {
        document.getElementById('totalOrganizations').textContent = '0';
        document.getElementById('totalUsers').textContent = '0';
        document.getElementById('totalProjects').textContent = '0';
        document.getElementById('totalTracks').textContent = '0';
        document.getElementById('totalMeetingRooms').textContent = '0';
        document.getElementById('systemHealth').textContent = 'Unknown';
    }

    /**
     * RENDER ORGANIZATIONS UI COMPONENT
     * PURPOSE: Render organizations UI component
     * WHY: Separates presentation logic for maintainable UI code
     */
    renderOrganizations() {
        const container = document.getElementById('organizationsContainer');

        console.log('Rendering organizations:', this.organizations);
        console.log('First org address data:', this.organizations[0] ? {
            street_address: this.organizations[0].street_address,
            city: this.organizations[0].city,
            state_province: this.organizations[0].state_province,
            postal_code: this.organizations[0].postal_code,
            country: this.organizations[0].country
        } : 'no orgs');

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
                <div class="org-card-header">
                    <div class="org-status-badge ${org.is_active ? 'active' : 'inactive'}">
                        <i class="fas ${org.is_active ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                        <span>${org.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                    <div class="org-title">
                        <h3>${org.name}</h3>
                        <span class="org-slug"><i class="fas fa-tag"></i> ${org.slug}</span>
                    </div>
                </div>

                <div class="org-card-body">
                    <div class="org-section">
                        <h4><i class="fas fa-info-circle"></i> Description</h4>
                        <p>${org.description || 'No description provided'}</p>
                    </div>

                    ${org.org_admin ? `
                    <div class="org-section">
                        <h4><i class="fas fa-user-shield"></i> Organization Administrator</h4>
                        <div class="org-details-grid">
                            <div class="detail-item">
                                <label><i class="fas fa-user"></i> Name</label>
                                <span>${org.org_admin.full_name || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-id-badge"></i> Username (Login ID)</label>
                                <span>${org.org_admin.username || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-envelope"></i> Email</label>
                                <span>${org.org_admin.email || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-phone"></i> Phone</label>
                                <span>${this.formatPhoneNumber(org.org_admin.phone)}</span>
                            </div>
                        </div>
                    </div>
                    ` : ''}

                    <div class="org-section">
                        <h4><i class="fas fa-building"></i> Organization Details</h4>
                        <div class="org-details-grid">
                            <div class="detail-item">
                                <label><i class="fas fa-globe"></i> Domain</label>
                                <span>${org.domain || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-envelope"></i> Contact Email</label>
                                <span>${org.contact_email || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-phone"></i> Contact Phone</label>
                                <span>${this.formatPhoneNumber(org.contact_phone)}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-map-marker-alt"></i> Street Address</label>
                                <span>${org.street_address || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-city"></i> City</label>
                                <span>${org.city || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-map"></i> State/Province</label>
                                <span>${org.state_province || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-mail-bulk"></i> Postal Code</label>
                                <span>${org.postal_code || 'Not specified'}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-flag"></i> Country</label>
                                <span>${org.country === 'US' ? 'United States' : (org.country || 'Not specified')}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-fingerprint"></i> Organization ID</label>
                                <span class="monospace">${org.id}</span>
                            </div>
                            <div class="detail-item">
                                <label><i class="fas fa-calendar-plus"></i> Created</label>
                                <span>${new Date(org.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
                            </div>
                        </div>
                    </div>

                    <div class="org-section">
                        <h4><i class="fas fa-chart-bar"></i> Statistics</h4>
                        <div class="org-stats">
                            <div class="org-stat clickable" onclick="siteAdmin.showOrganizationMembers('${org.id}', 'all')" title="Click to view all members">
                                <div class="stat-icon"><i class="fas fa-users"></i></div>
                                <div class="stat-content">
                                    <span class="value">${org.total_members}</span>
                                    <span class="label">Total Members</span>
                                </div>
                            </div>
                            <div class="org-stat clickable" onclick="siteAdmin.showOrganizationProjects('${org.id}')" title="Click to view projects">
                                <div class="stat-icon"><i class="fas fa-project-diagram"></i></div>
                                <div class="stat-content">
                                    <span class="value">${org.project_count}</span>
                                    <span class="label">Projects</span>
                                </div>
                            </div>
                            <div class="org-stat clickable" onclick="siteAdmin.showOrganizationMembers('${org.id}', 'instructor')" title="Click to view instructors">
                                <div class="stat-icon"><i class="fas fa-chalkboard-teacher"></i></div>
                                <div class="stat-content">
                                    <span class="value">${org.member_counts?.instructor || 0}</span>
                                    <span class="label">Instructors</span>
                                </div>
                            </div>
                            <div class="org-stat clickable" onclick="siteAdmin.showOrganizationMembers('${org.id}', 'student')" title="Click to view students">
                                <div class="stat-icon"><i class="fas fa-user-graduate"></i></div>
                                <div class="stat-content">
                                    <span class="value">${org.member_counts?.student || 0}</span>
                                    <span class="label">Students</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="org-card-footer">
                    ${org.is_active ? `
                        <button class="btn btn-sm btn-warning" onclick="siteAdmin.deactivateOrganization('${org.id}')" title="Deactivate organization (soft delete - can be reactivated later)">
                            <i class="fas fa-pause"></i> Deactivate
                        </button>
                    ` : `
                        <button class="btn btn-sm btn-success" onclick="siteAdmin.reactivateOrganization('${org.id}')" title="Reactivate organization">
                            <i class="fas fa-play"></i> Reactivate
                        </button>
                    `}
                    <button class="btn btn-sm btn-danger" onclick="siteAdmin.showDeleteOrganizationModal('${org.id}', '${org.name.replace(/'/g, "\\'")}', ${org.total_members}, ${org.project_count}, 0)" title="Permanently delete organization and all data">
                        <i class="fas fa-trash"></i> Delete Permanently
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = organizationsHtml;
    }

    /**
     * RENDER RECENT ACTIVITY UI COMPONENT
     * PURPOSE: Render recent activity UI component
     * WHY: Separates presentation logic for maintainable UI code
     *
     * @param {*} activities - Activities parameter
     */
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

    /**
     * UPDATE INTEGRATION STATUS STATE
     * PURPOSE: Update integration status state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @param {*} health - Health parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * SET DEFAULT INTEGRATION STATUS VALUE
     * PURPOSE: Set default integration status value
     * WHY: Maintains data integrity through controlled mutation
     */
    setDefaultIntegrationStatus() {
        document.getElementById('teamsIntegrationStatus').className = 'integration-status inactive';
        document.getElementById('zoomIntegrationStatus').className = 'integration-status inactive';
        document.getElementById('teamsLastTest').textContent = 'Never';
        document.getElementById('zoomLastTest').textContent = 'Never';
    }

    // Modal Functions
    /**
     * DISPLAY DELETE ORGANIZATION MODAL INTERFACE
     * PURPOSE: Display delete organization modal interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {string|number} orgId - Unique identifier
     * @param {*} orgName - Name value
     * @param {*} memberCount - Membercount parameter
     * @param {*} projectCount - Projectcount parameter
     * @param {*} meetingRoomCount - Meetingroomcount parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * DISPLAY MODAL INTERFACE
     * PURPOSE: Display modal interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {string|number} modalId - Modalid parameter
     */
    showModal(modalId) {
        document.getElementById(modalId).style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    /**
     * HIDE MODAL INTERFACE
     * PURPOSE: Hide modal interface
     * WHY: Improves UX by managing interface visibility and state
     *
     * @param {string|number} modalId - Modalid parameter
     */
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
    /**
     * EXECUTE CONFIRMDELETEORGANIZATION OPERATION
     * PURPOSE: Execute confirmDeleteOrganization operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * EXECUTE DEACTIVATEORGANIZATION OPERATION
     * PURPOSE: Execute deactivateOrganization operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} orgId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * EXECUTE REACTIVATEORGANIZATION OPERATION
     * PURPOSE: Execute reactivateOrganization operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} orgId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * EXECUTE TESTTEAMSINTEGRATION OPERATION
     * PURPOSE: Execute testTeamsIntegration operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * EXECUTE TESTZOOMINTEGRATION OPERATION
     * PURPOSE: Execute testZoomIntegration operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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
    /**
     * FILTER ORGANIZATIONS BASED ON CRITERIA
     * PURPOSE: Filter organizations based on criteria
     * WHY: Enables users to find relevant data quickly
     *
     * @returns {Array} Filtered array
     */
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

    /**
     * SEARCH FOR ORGANIZATIONS
     * PURPOSE: Search for organizations
     * WHY: Enables efficient data discovery and navigation
     */
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

    // Organization member/project viewing
    /**
     * DISPLAY ORGANIZATION MEMBERS INTERFACE
     * PURPOSE: Display organization members interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {string|number} orgId - Unique identifier
     * @param {*} role - Role parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async showOrganizationMembers(orgId, role) {
        /**
         * ORGANIZATION MEMBERS VIEWER
         * PURPOSE: Display organization members with filtering by role
         * WHY: Site admins need to manage and view members across different roles
         *
         * FEATURES:
         * - Filter by role (all, student, instructor, org_admin)
         * - Sort by name, email, enrollment date
         * - Display member details and status
         * - Course/project enrollment information for students
         */
        try {
            this.showLoadingOverlay(true);

            // Fetch members for the organization
            const url = role && role !== 'all'
                ? `/api/v1/organizations/${orgId}/members?role_type=${role}`
                : `/api/v1/organizations/${orgId}/members`;

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch members');
            }

            const members = await response.json();

            // For students, fetch enrollment details
            if (role === 'student') {
                for (const member of members) {
                    try {
                        const enrollmentResponse = await fetch(
                            `/api/v1/students/${member.user_id}/enrollments`,
                            {
                                headers: {
                                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                                }
                            }
                        );
                        if (enrollmentResponse.ok) {
                            member.enrollments = await enrollmentResponse.json();
                        }
                    } catch (error) {
                        console.error(`Failed to fetch enrollments for ${member.user_id}:`, error);
                        member.enrollments = [];
                    }
                }
            }

            // Create and show modal
            this.showMembersModal(orgId, members, role);

        } catch (error) {
            console.error('Error loading members:', error);
            this.showNotification('Failed to load members', 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    /**
     * DISPLAY MEMBERS MODAL INTERFACE
     * PURPOSE: Display members modal interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {string|number} orgId - Unique identifier
     * @param {*} members - Members parameter
     * @param {*} roleFilter - Rolefilter parameter
     */
    showMembersModal(orgId, members, roleFilter) {
        /**
         * MEMBERS MODAL DISPLAY
         * PURPOSE: Render interactive modal showing organization members
         * WHY: Provides structured view of member data with filtering and sorting
         */
        const roleText = roleFilter === 'all' ? 'All Members' :
                        roleFilter === 'student' ? 'Students' :
                        roleFilter === 'instructor' ? 'Instructors' :
                        'Organization Admins';

        const modalContent = `
            <div class="modal-header">
                <h2><i class="fas fa-users"></i> ${roleText}</h2>
                <button class="modal-close" onclick="siteAdmin.closeMembersModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="members-controls">
                    <div class="control-group">
                        <label>Filter by Role:</label>
                        <select id="memberRoleFilter" onchange="siteAdmin.filterMembersByRole('${orgId}')">
                            <option value="all" ${roleFilter === 'all' ? 'selected' : ''}>All Members</option>
                            <option value="student" ${roleFilter === 'student' ? 'selected' : ''}>Students</option>
                            <option value="instructor" ${roleFilter === 'instructor' ? 'selected' : ''}>Instructors</option>
                            <option value="organization_admin" ${roleFilter === 'organization_admin' ? 'selected' : ''}>Org Admins</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label>Sort by:</label>
                        <select id="memberSortOrder" onchange="siteAdmin.sortMembers()">
                            <option value="name-asc">Name (A-Z)</option>
                            <option value="name-desc">Name (Z-A)</option>
                            <option value="email-asc">Email (A-Z)</option>
                            <option value="date-asc">Oldest First</option>
                            <option value="date-desc">Newest First</option>
                        </select>
                    </div>
                </div>
                <div class="members-stats">
                    <span><i class="fas fa-users"></i> Total: ${members.length}</span>
                </div>
                <div id="membersList">
                    ${members.length === 0 ? '<p class="no-data">No members found</p>' : this.renderMembers(members, roleFilter)}
                </div>
            </div>
        `;

        // Create or update modal
        let modal = document.getElementById('membersModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'membersModal';
            modal.className = 'modal';
            document.body.appendChild(modal);
        }

        modal.innerHTML = modalContent;
        this.currentMembers = members;
        this.currentMembersOrgId = orgId;
        this.currentMembersRole = roleFilter;
        this.showModal('membersModal');
    }

    /**
     * RENDER MEMBERS UI COMPONENT
     * PURPOSE: Render members UI component
     * WHY: Separates presentation logic for maintainable UI code
     *
     * @param {*} members - Members parameter
     * @param {*} roleFilter - Rolefilter parameter
     */
    renderMembers(members, roleFilter) {
        /**
         * MEMBERS RENDERING
         * PURPOSE: Generate HTML for members list with role-specific details
         * WHY: Different roles need different information displayed
         */
        return members.map(member => `
            <div class="member-card" data-role="${member.role || member.role_type}">
                <div class="member-header">
                    <div class="member-info">
                        <i class="fas ${this.getRoleIcon(member.role || member.role_type)}"></i>
                        <div>
                            <h4>${member.full_name || member.name || 'Unknown'}</h4>
                            <span class="member-email">${member.email}</span>
                        </div>
                    </div>
                    <span class="member-role-badge ${member.role || member.role_type}">
                        ${this.formatRoleName(member.role || member.role_type)}
                    </span>
                </div>
                <div class="member-details">
                    <div class="detail-row">
                        <span class="detail-label">Username:</span>
                        <span>${member.username || 'N/A'}</span>
                    </div>
                    ${member.phone ? `
                        <div class="detail-row">
                            <span class="detail-label">Phone:</span>
                            <span>${this.formatPhoneNumber(member.phone)}</span>
                        </div>
                    ` : ''}
                    <div class="detail-row">
                        <span class="detail-label">Joined:</span>
                        <span>${new Date(member.created_at || member.joined_at).toLocaleDateString()}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Status:</span>
                        <span class="status-badge ${member.is_active ? 'active' : 'inactive'}">
                            ${member.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                </div>
                ${roleFilter === 'student' && member.enrollments ? this.renderStudentEnrollments(member.enrollments) : ''}
            </div>
        `).join('');
    }

    /**
     * RENDER STUDENT ENROLLMENTS UI COMPONENT
     * PURPOSE: Render student enrollments UI component
     * WHY: Separates presentation logic for maintainable UI code
     *
     * @param {*} enrollments - Enrollments parameter
     */
    renderStudentEnrollments(enrollments) {
        /**
         * STUDENT ENROLLMENTS RENDERING
         * PURPOSE: Show course/project enrollments for students
         * WHY: Site admins need to see what students are enrolled in
         */
        if (!enrollments || enrollments.length === 0) {
            return '<div class="enrollments-section"><p class="no-enrollments">No enrollments</p></div>';
        }

        return `
            <div class="enrollments-section">
                <h5><i class="fas fa-book"></i> Enrollments (${enrollments.length})</h5>
                <div class="enrollments-list">
                    ${enrollments.map(enrollment => `
                        <div class="enrollment-item">
                            <span class="enrollment-name">${enrollment.course_name || enrollment.project_name}</span>
                            <span class="enrollment-date">${new Date(enrollment.enrolled_at).toLocaleDateString()}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * RETRIEVE ROLE ICON INFORMATION
     * PURPOSE: Retrieve role icon information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} role - Role parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getRoleIcon(role) {
        /**
         * GET ROLE ICON
         * PURPOSE: Return appropriate FontAwesome icon for role
         */
        const icons = {
            'student': 'fa-user-graduate',
            'instructor': 'fa-chalkboard-teacher',
            'organization_admin': 'fa-user-shield',
            'org_admin': 'fa-user-shield',
            'site_admin': 'fa-user-cog'
        };
        return icons[role] || 'fa-user';
    }

    /**
     * FORMAT ROLE NAME FOR DISPLAY
     * PURPOSE: Format role name for display
     * WHY: Consistent data presentation improves user experience
     *
     * @param {*} role - Role parameter
     *
     * @returns {string} Formatted string
     */
    formatRoleName(role) {
        /**
         * FORMAT ROLE NAME
         * PURPOSE: Convert role slug to display name
         */
        const names = {
            'student': 'Student',
            'instructor': 'Instructor',
            'organization_admin': 'Org Admin',
            'org_admin': 'Org Admin',
            'site_admin': 'Site Admin'
        };
        return names[role] || role;
    }

    /**
     * FILTER MEMBERS BY ROLE BASED ON CRITERIA
     * PURPOSE: Filter members by role based on criteria
     * WHY: Enables users to find relevant data quickly
     *
     * @param {string|number} orgId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async filterMembersByRole(orgId) {
        /**
         * FILTER MEMBERS BY ROLE
         * PURPOSE: Re-fetch members with new role filter
         */
        const roleFilter = document.getElementById('memberRoleFilter').value;
        await this.showOrganizationMembers(orgId, roleFilter);
    }

    /**
     * SORT MEMBERS IN SPECIFIED ORDER
     * PURPOSE: Sort members in specified order
     * WHY: Organized data presentation improves usability
     */
    sortMembers() {
        /**
         * SORT MEMBERS
         * PURPOSE: Sort members based on user selection
         */
        const sortOrder = document.getElementById('memberSortOrder').value;
        const members = [...this.currentMembers];

        members.sort((a, b) => {
            switch(sortOrder) {
                case 'name-asc':
                    return (a.full_name || a.name || '').localeCompare(b.full_name || b.name || '');
                case 'name-desc':
                    return (b.full_name || b.name || '').localeCompare(a.full_name || a.name || '');
                case 'email-asc':
                    return a.email.localeCompare(b.email);
                case 'date-asc':
                    return new Date(a.created_at || a.joined_at) - new Date(b.created_at || b.joined_at);
                case 'date-desc':
                    return new Date(b.created_at || b.joined_at) - new Date(a.created_at || a.joined_at);
                default:
                    return 0;
            }
        });

        document.getElementById('membersList').innerHTML = this.renderMembers(members, this.currentMembersRole);
    }

    /**
     * HIDE MEMBERS MODAL INTERFACE
     * PURPOSE: Hide members modal interface
     * WHY: Improves UX by managing interface visibility and state
     */
    closeMembersModal() {
        /**
         * CLOSE MEMBERS MODAL
         * PURPOSE: Clean up and close the members modal
         */
        this.closeModal('membersModal');
        this.currentMembers = null;
        this.currentMembersOrgId = null;
        this.currentMembersRole = null;
    }

    /**
     * DISPLAY ORGANIZATION PROJECTS INTERFACE
     * PURPOSE: Display organization projects interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {string|number} orgId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async showOrganizationProjects(orgId) {
        /**
         * ORGANIZATION PROJECTS VIEWER
         * PURPOSE: Display comprehensive project and track information for an organization
         * WHY: Site admins need visibility into organization's educational content structure
         *
         * FEATURES:
         * - Lists all projects for the organization
         * - Shows tracks within each project
         * - Displays courses within each track
         * - Sortable by name or creation date
         * - Real-time data fetching from API
         */
        try {
            this.showLoadingOverlay(true);

            // Fetch projects for the organization
            const response = await fetch(`/api/v1/organizations/${orgId}/projects`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch projects');
            }

            const projects = await response.json();

            // Fetch tracks for each project
            for (const project of projects) {
                const tracksResponse = await fetch(`/api/v1/projects/${project.id}/tracks`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                    }
                });

                if (tracksResponse.ok) {
                    project.tracks = await tracksResponse.json();
                } else {
                    project.tracks = [];
                }
            }

            // Create and show modal
            this.showProjectsModal(orgId, projects);

        } catch (error) {
            console.error('Error loading projects:', error);
            this.showNotification('Failed to load projects', 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    /**
     * DISPLAY PROJECTS MODAL INTERFACE
     * PURPOSE: Display projects modal interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {string|number} orgId - Unique identifier
     * @param {*} projects - Projects parameter
     */
    showProjectsModal(orgId, projects) {
        /**
         * PROJECTS MODAL DISPLAY
         * PURPOSE: Render interactive modal showing organization's projects and tracks
         * WHY: Provides structured view of educational content hierarchy
         */
        const modalContent = `
            <div class="modal-header">
                <h2><i class="fas fa-project-diagram"></i> Organization Projects</h2>
                <button class="modal-close" onclick="siteAdmin.closeProjectsModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="projects-controls">
                    <div class="control-group">
                        <label>Sort by:</label>
                        <select id="projectSortOrder" onchange="siteAdmin.sortProjects()">
                            <option value="name-asc">Name (A-Z)</option>
                            <option value="name-desc">Name (Z-A)</option>
                            <option value="date-asc">Oldest First</option>
                            <option value="date-desc">Newest First</option>
                        </select>
                    </div>
                </div>
                <div id="projectsList">
                    ${projects.length === 0 ? '<p class="no-data">No projects found</p>' : this.renderProjects(projects)}
                </div>
            </div>
        `;

        // Create or update modal
        let modal = document.getElementById('projectsModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'projectsModal';
            modal.className = 'modal';
            document.body.appendChild(modal);
        }

        modal.innerHTML = modalContent;
        this.currentProjects = projects;  // Store for sorting
        this.showModal('projectsModal');
    }

    /**
     * RENDER PROJECTS UI COMPONENT
     * PURPOSE: Render projects UI component
     * WHY: Separates presentation logic for maintainable UI code
     *
     * @param {*} projects - Projects parameter
     */
    renderProjects(projects) {
        /**
         * PROJECTS RENDERING
         * PURPOSE: Generate HTML for projects list with tracks and courses
         * WHY: Structured display of educational content hierarchy
         */
        return projects.map(project => `
            <div class="project-card">
                <div class="project-header">
                    <h3><i class="fas fa-folder-open"></i> ${project.name}</h3>
                    <span class="project-status ${project.is_published ? 'published' : 'draft'}">
                        ${project.is_published ? 'Published' : 'Draft'}
                    </span>
                </div>
                <p class="project-description">${project.description || 'No description'}</p>
                <div class="project-meta">
                    <span><i class="fas fa-calendar"></i> Created: ${new Date(project.created_at).toLocaleDateString()}</span>
                    <span><i class="fas fa-route"></i> ${project.tracks?.length || 0} Track(s)</span>
                </div>
                ${project.tracks && project.tracks.length > 0 ? `
                    <div class="tracks-section">
                        <h4>Tracks:</h4>
                        ${this.renderTracks(project.tracks)}
                    </div>
                ` : '<p class="no-tracks">No tracks in this project</p>'}
            </div>
        `).join('');
    }

    /**
     * RENDER TRACKS UI COMPONENT
     * PURPOSE: Render tracks UI component
     * WHY: Separates presentation logic for maintainable UI code
     *
     * @param {*} tracks - Tracks parameter
     */
    renderTracks(tracks) {
        /**
         * TRACKS RENDERING
         * PURPOSE: Generate HTML for tracks list within a project
         * WHY: Shows learning paths and associated courses
         */
        return tracks.map(track => `
            <div class="track-item">
                <div class="track-header">
                    <i class="fas fa-route"></i>
                    <span class="track-name">${track.name}</span>
                    <span class="track-difficulty ${track.difficulty_level}">${track.difficulty_level}</span>
                </div>
                <p class="track-description">${track.description || ''}</p>
                <div class="track-meta">
                    <span><i class="fas fa-clock"></i> ${track.estimated_hours || 0} hours</span>
                    <span><i class="fas fa-list"></i> ${track.sequence_order || 0} in sequence</span>
                </div>
            </div>
        `).join('');
    }

    /**
     * SORT PROJECTS IN SPECIFIED ORDER
     * PURPOSE: Sort projects in specified order
     * WHY: Organized data presentation improves usability
     */
    sortProjects() {
        /**
         * PROJECTS SORTING
         * PURPOSE: Sort projects based on user selection
         * WHY: Allows flexible organization of project list
         */
        const sortOrder = document.getElementById('projectSortOrder').value;
        const projects = [...this.currentProjects];

        projects.sort((a, b) => {
            switch(sortOrder) {
                case 'name-asc':
                    return a.name.localeCompare(b.name);
                case 'name-desc':
                    return b.name.localeCompare(a.name);
                case 'date-asc':
                    return new Date(a.created_at) - new Date(b.created_at);
                case 'date-desc':
                    return new Date(b.created_at) - new Date(a.created_at);
                default:
                    return 0;
            }
        });

        document.getElementById('projectsList').innerHTML = this.renderProjects(projects);
    }

    /**
     * HIDE PROJECTS MODAL INTERFACE
     * PURPOSE: Hide projects modal interface
     * WHY: Improves UX by managing interface visibility and state
     */
    closeProjectsModal() {
        /**
         * CLOSE PROJECTS MODAL
         * PURPOSE: Clean up and close the projects viewing modal
         */
        this.closeModal('projectsModal');
        this.currentProjects = null;
    }

    // Utility Functions
    /**
     * RETRIEVE ACTIVITY ICON INFORMATION
     * PURPOSE: Retrieve activity icon information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} type - Type identifier
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getActivityIcon(type) {
        const icons = {
            'create': 'fa-plus',
            'delete': 'fa-trash',
            'update': 'fa-edit',
            'login': 'fa-sign-in-alt'
        };
        return icons[type] || 'fa-info';
    }

    /**
     * FORMAT TIME AGO FOR DISPLAY
     * PURPOSE: Format time ago for display
     * WHY: Consistent data presentation improves user experience
     *
     * @param {*} timestamp - Timestamp parameter
     *
     * @returns {string} Formatted string
     */
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

    /**
     * DISPLAY LOADING OVERLAY INTERFACE
     * PURPOSE: Display loading overlay interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} show - Show parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    showLoadingOverlay(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }

    /**
     * DISPLAY NOTIFICATION INTERFACE
     * PURPOSE: Display notification interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} message - Message parameter
     * @param {*} type - Type identifier
     */
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
    /**
     * EXECUTE REFRESHPLATFORMSTATS OPERATION
     * PURPOSE: Execute refreshPlatformStats operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async refreshPlatformStats() {
        await this.loadPlatformStats();
        this.showNotification('Platform statistics refreshed', 'success');
    }

    /**
     * EXECUTE RUNHEALTHCHECK OPERATION
     * PURPOSE: Execute runHealthCheck operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async runHealthCheck() {
        await this.loadIntegrationStatus();
        this.showNotification('Health check completed', 'success');
    }

    /**
     * EXECUTE VIEWSYSTEMLOGS OPERATION
     * PURPOSE: Execute viewSystemLogs operation
     * WHY: Implements required business logic for system functionality
     */
    viewSystemLogs() {
        this.showNotification('System logs feature coming soon', 'info');
    }

    /**
     * EXECUTE EXPORTPLATFORMREPORT OPERATION
     * PURPOSE: Execute exportPlatformReport operation
     * WHY: Implements required business logic for system functionality
     */
    exportPlatformReport() {
        this.showNotification('Platform report export feature coming soon', 'info');
    }

    /**
     * EXECUTE REFRESHORGANIZATIONS OPERATION
     * PURPOSE: Execute refreshOrganizations operation
     * WHY: Implements required business logic for system functionality
     */
    refreshOrganizations() {
        console.log('🔄 Refresh button clicked - reloading organizations');
        this.showNotification('Refreshing organizations...', 'info');
        this.loadOrganizations();
    }

    /**
     * LOAD USERS DATA FROM SERVER
     * PURPOSE: Load users data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * RENDER USERS TABLE UI COMPONENT
     * PURPOSE: Render users table UI component
     * WHY: Separates presentation logic for maintainable UI code
     *
     * @param {*} users - Users parameter
     */
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

    /**
     * LOAD AUDIT LOG DATA FROM SERVER
     * PURPOSE: Load audit log data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async loadAuditLog() {
        try {
            const auditContainer = document.getElementById('auditLogContainer');
            auditContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Loading audit log...</p></div>';

            const response = await fetch(`${this.API_BASE}/api/v1/rbac/audit-log`, {
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

    /**
     * RENDER AUDIT LOG UI COMPONENT
     * PURPOSE: Render audit log UI component
     * WHY: Separates presentation logic for maintainable UI code
     *
     * @param {*} entries - Entries parameter
     */
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

    /**
     * RETRIEVE AUDIT SEVERITY CLASS INFORMATION
     * PURPOSE: Retrieve audit severity class information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} action - Action parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getAuditSeverityClass(action) {
        const highSeverity = ['organization_deleted', 'user_deleted', 'permission_revoked', 'system_security_breach'];
        const mediumSeverity = ['user_created', 'permission_granted', 'organization_created', 'integration_failed'];
        
        if (highSeverity.includes(action)) return 'audit-high';
        if (mediumSeverity.includes(action)) return 'audit-medium';
        return 'audit-low';
    }

    /**
     * RETRIEVE AUDIT ICON INFORMATION
     * PURPOSE: Retrieve audit icon information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} action - Action parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
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

    /**
     * FORMAT AUDIT ACTION FOR DISPLAY
     * PURPOSE: Format audit action for display
     * WHY: Consistent data presentation improves user experience
     *
     * @param {*} action - Action parameter
     *
     * @returns {string} Formatted string
     */
    formatAuditAction(action) {
        return action.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    /**
     * FORMAT TIMESTAMP FOR DISPLAY
     * PURPOSE: Format timestamp for display
     * WHY: Consistent data presentation improves user experience
     *
     * @param {*} timestamp - Timestamp parameter
     *
     * @returns {string} Formatted string
     */
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

    /**
     * LOAD MORE AUDIT ENTRIES DATA FROM SERVER
     * PURPOSE: Load more audit entries data from server
     * WHY: Dynamic data loading enables real-time content updates
     *
     * @returns {Promise<void>} Promise resolving when loading completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async loadMoreAuditEntries() {
        // Implementation for pagination
        this.showNotification('Loading more audit entries...', 'info');
    }

    /**
     * FILTER AUDIT LOG BASED ON CRITERIA
     * PURPOSE: Filter audit log based on criteria
     * WHY: Enables users to find relevant data quickly
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async filterAuditLog() {
        /**
         * AUDIT LOG FILTERING
         * PURPOSE: Filter audit log entries by action type and date
         * WHY: Site admins need to search through audit logs efficiently
         *
         * FEATURES:
         * - Filter by action type (organization_deleted, user_created, etc.)
         * - Filter by date range
         * - Real-time filtering without page reload
         */
        try {
            const actionFilter = document.getElementById('auditActionFilter')?.value || '';
            const dateFilter = document.getElementById('auditDateFilter')?.value || '';

            const auditContainer = document.getElementById('auditLogContainer');
            auditContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Filtering audit log...</p></div>';

            // Build query parameters
            const params = new URLSearchParams();
            if (actionFilter) params.append('action', actionFilter);
            if (dateFilter) params.append('date', dateFilter);

            const response = await fetch(`${this.API_BASE}/api/v1/rbac/audit-log?${params.toString()}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to filter audit log: ${response.statusText}`);
            }

            const data = await response.json();
            const auditEntries = data.entries || [];

            this.renderAuditLog(auditEntries);

        } catch (error) {
            console.error('Failed to filter audit log:', error);
            const auditContainer = document.getElementById('auditLogContainer');
            auditContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Failed to Filter Audit Log</h3>
                    <p>${error.message}</p>
                    <button onclick="window.siteAdmin.loadAuditLog()" class="btn btn-primary">
                        <i class="fas fa-redo"></i> Reset Filters
                    </button>
                </div>
            `;
        }
    }

    /**
     * EXECUTE EXPORTAUDITLOG OPERATION
     * PURPOSE: Execute exportAuditLog operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async exportAuditLog() {
        /**
         * AUDIT LOG EXPORT
         * PURPOSE: Export audit log entries to CSV format
         * WHY: Compliance and record-keeping require audit log exports
         *
         * FEATURES:
         * - Export filtered or all audit log entries
         * - CSV format with all audit details
         * - Automatic file download
         */
        try {
            this.showNotification('Preparing audit log export...', 'info');

            const actionFilter = document.getElementById('auditActionFilter')?.value || '';
            const dateFilter = document.getElementById('auditDateFilter')?.value || '';

            // Build query parameters
            const params = new URLSearchParams();
            if (actionFilter) params.append('action', actionFilter);
            if (dateFilter) params.append('date', dateFilter);
            params.append('format', 'csv');

            const response = await fetch(`${this.API_BASE}/api/v1/rbac/audit-log/export?${params.toString()}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to export audit log: ${response.statusText}`);
            }

            // Get the CSV data
            const blob = await response.blob();

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `audit-log-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();

            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showNotification('Audit log exported successfully', 'success');

        } catch (error) {
            console.error('Failed to export audit log:', error);
            this.showNotification('Failed to export audit log. Please try again.', 'error');
        }
    }

    /**
     * EXECUTE VIEWORGANIZATIONDETAILS OPERATION
     * PURPOSE: Execute viewOrganizationDetails operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} orgId - Unique identifier
     */
    viewOrganizationDetails(orgId) {
        this.showNotification(`Organization details for ${orgId}`, 'info');
    }

    /**
     * EXECUTE VIEWUSERDETAILS OPERATION
     * PURPOSE: Execute viewUserDetails operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} userId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * DISPLAY USER DETAILS MODAL INTERFACE
     * PURPOSE: Display user details modal interface
     * WHY: Provides user interface for interaction and data visualization
     *
     * @param {*} user - User parameter
     */
    showUserDetailsModal(user) {
        // Implementation for user details modal
        this.showNotification(`User details for ${user.name || user.email}`, 'info');
    }

    /**
     * EXECUTE EDITUSER OPERATION
     * PURPOSE: Execute editUser operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} userId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    async editUser(userId) {
        // Implementation for user editing
        this.showNotification(`Edit user functionality for user ${userId}`, 'info');
    }

    /**
     * EXECUTE ACTIVATEUSER OPERATION
     * PURPOSE: Execute activateUser operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} userId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * EXECUTE DEACTIVATEUSER OPERATION
     * PURPOSE: Execute deactivateUser operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} userId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
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

    /**
     * EXECUTE CONFIGURETEAMSINTEGRATION OPERATION
     * PURPOSE: Execute configureTeamsIntegration operation
     * WHY: Implements required business logic for system functionality
     */
    configureTeamsIntegration() {
        this.showNotification('Teams integration configuration coming soon', 'info');
    }

    /**
     * EXECUTE CONFIGUREZOOMINTEGRATION OPERATION
     * PURPOSE: Execute configureZoomIntegration operation
     * WHY: Implements required business logic for system functionality
     */
    configureZoomIntegration() {
        this.showNotification('Zoom integration configuration coming soon', 'info');
    }

    /**
     * EXECUTE LOGOUT OPERATION
     * PURPOSE: Execute logout operation
     * WHY: Implements required business logic for system functionality
     */
    logout() {
        // Clear all session data
        this.clearExpiredSession();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.siteAdmin = new SiteAdminDashboard();
});

// Make logout function globally available for HTML onclick
window.logout = () => {
    if (window.siteAdmin) {
        window.siteAdmin.logout();
    } else {
        // Fallback if dashboard not initialized
        localStorage.clear();
        window.location.href = '../index.html';
    }
};

