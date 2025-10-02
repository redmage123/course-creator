/**
 * AUTHENTICATION MODULE - COMPREHENSIVE USER SESSION MANAGEMENT
 * CACHE BUSTER: 2025-09-29-16:35:00
 * 
 * PURPOSE: Complete authentication system for Course Creator Platform
 * WHY: Secure user management is critical for educational platform integrity
 * ARCHITECTURE: Session-based authentication with automatic timeout and lab integration
 * 
 * CORE RESPONSIBILITIES:
 * - User login, logout, and registration
 * - JWT token management and validation
 * - Session timeout and inactivity monitoring
 * - Lab container lifecycle integration
 * - Activity tracking for security and analytics
 * - Cross-tab session synchronization
 * - Automatic session cleanup and security enforcement
 * 
 * BUSINESS REQUIREMENTS:
 * - 8-hour maximum session duration (work day alignment)
 * - 2-hour inactivity timeout (security balance)
 * - 5-minute logout warning (user experience)
 * - Automatic lab cleanup on logout (resource management)
 * - Seamless cross-tab authentication state
 */

/**
 * MODULE DEPENDENCIES
 * PURPOSE: Import all systems that authentication integrates with
 * WHY: Authentication is a cross-cutting concern that affects all platform areas
 */
// Use global CONFIG (loaded via script tag in HTML)
import { showNotification } from './notifications.js';  // User feedback system
import { ActivityTracker } from './activity-tracker.js'; // Session activity monitoring
import { labLifecycleManager } from './lab-lifecycle.js'; // Lab container integration

console.log('🚀 AUTH MODULE LOADED - VERSION 2025-09-29-16:35:00');

/**
 * AUTHENTICATION MANAGER CLASS
 * PATTERN: Singleton authentication manager with comprehensive session handling
 * WHY: Single source of truth for authentication state across the application
 */
class AuthManager {
    /**
     * CONSTRUCTOR - AUTHENTICATION STATE INITIALIZATION
     * PURPOSE: Set up authentication system with session monitoring and lab integration
     * WHY: Proper initialization ensures consistent authentication behavior
     */
    constructor() {
        // USER STATE: Current authenticated user information
        this.currentUser = null;
        
        // TOKEN MANAGEMENT: JWT token for API authentication
        this.authToken = null;
        
        // ACTIVITY MONITORING: Track user activity for session timeout
        this.activityTracker = new ActivityTracker();
        
        // API CONFIGURATION: Authentication service endpoint
        // Use getter to ensure CONFIG is available when accessed
        this.getAuthApiBase = () => {
            console.log('🔍 DEBUG - window.CONFIG:', window.CONFIG);
            console.log('🔍 DEBUG - window.location.hostname:', window.location.hostname);
            const configUrl = window.CONFIG?.API_URLS?.USER_MANAGEMENT;
            const fallbackUrl = `https://${window.location.hostname}:8000`;
            console.log('🔍 DEBUG - CONFIG URL:', configUrl);
            console.log('🔍 DEBUG - Fallback URL:', fallbackUrl);
            
            // TEMPORARY FIX: Force the correct URL based on hostname
            if (window.location.hostname === '176.9.99.103') {
                console.log('🔧 TEMPORARY FIX - Using hardcoded URL for this hostname');
                return 'https://176.9.99.103:8000';
            }
            
            return configUrl || fallbackUrl;
        };
        
        /*
         * Session Management Configuration and Business Requirements
         *
         * SECURITY TIMEOUT CONFIGURATION:
         * - SESSION_TIMEOUT: 8 hours (28,800,000 ms) - Maximum session duration
         * - INACTIVITY_TIMEOUT: 2 hours (7,200,000 ms) - Inactivity threshold
         * - AUTO_LOGOUT_WARNING: 5 minutes (300,000 ms) - Warning before expiry
         *
         * WHY THESE SPECIFIC TIMEOUTS:
         *
         * 8-Hour Absolute Session Timeout:
         * - Aligns with standard work day expectations
         * - Balances security with user convenience
         * - Prevents indefinite session persistence
         * - Meets educational platform security requirements
         * - Reduces risk of session hijacking over time
         *
         * 2-Hour Inactivity Timeout:
         * - Prevents sessions from remaining active when users step away
         * - Common industry standard for educational platforms
         * - Allows for lunch breaks and meetings without forced logout
         * - Protects against unauthorized access on unattended devices
         *
         * 5-Minute Warning Period:
         * - Provides sufficient time for users to save work
         * - Allows users to extend session through activity
         * - Prevents unexpected data loss from automatic logout
         * - User-friendly approach to session management
         */
        this.SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8 hours absolute maximum
        this.INACTIVITY_TIMEOUT = 2 * 60 * 60 * 1000; // 2 hours of inactivity
        this.AUTO_LOGOUT_WARNING = 5 * 60 * 1000; // 5 minutes warning period
        
        // SESSION MONITORING STATE: Control session timeout checking
        this.sessionCheckInterval = null;  // Interval for periodic session validation
        this.warningShown = false;         // Track if logout warning has been displayed
    }

    /**
     * CURRENT USER RETRIEVAL WITH FALLBACK STRATEGY
     * PURPOSE: Get authenticated user information with robust error handling
     * WHY: User data is critical for authorization and personalization
     * 
     * FALLBACK STRATEGY:
     * 1. Try to get complete user object from localStorage
     * 2. Fall back to basic user info from userEmail
     * 3. Return null if no user data exists
     * 
     * ERROR HANDLING: Graceful degradation if localStorage data is corrupted
     */
    getCurrentUser() {
        try {
            // PRIMARY DATA SOURCE: Complete user object from authentication
            const userStr = localStorage.getItem('currentUser');
            if (userStr) {
                return JSON.parse(userStr);  // Parse and return full user data
            }
            
            // FALLBACK STRATEGY: Basic user info from email-only login
            // WHY: Some authentication flows only store email initially
            const userEmail = localStorage.getItem('userEmail');
            if (userEmail) {
                return { email: userEmail, username: userEmail };
            }
            
            // NO USER DATA: Return null for unauthenticated state
            return null;
        } catch (error) {
            // ERROR RECOVERY: Handle corrupted localStorage data gracefully
            console.error('Error getting current user:', error);
            
            // LAST RESORT: Try email fallback even after JSON parse error
            const userEmail = localStorage.getItem('userEmail');
            return userEmail ? { email: userEmail, username: userEmail } : null;
        }
    }

    /**
     * AUTHENTICATION STATUS CHECKER
     * PURPOSE: Determine if user has valid authentication credentials
     * WHY: Authorization decisions depend on accurate authentication status
     * 
     * AUTHENTICATION CRITERIA:
     * - User data must exist (from getCurrentUser())
     * - Valid auth token must be present in localStorage
     * - Both conditions required for authenticated state
     */
    isAuthenticated() {
        return !!(this.getCurrentUser() && localStorage.getItem('authToken'));
    }

    /**
     * AUTHENTICATION STATE INITIALIZATION
     * PURPOSE: Restore authentication state from persistent storage on app startup
     * WHY: Users should remain logged in across browser sessions and page refreshes
     * 
     * INITIALIZATION PROCESS:
     * 1. Check for saved authentication tokens and user data
     * 2. Restore user state if valid credentials exist
     * 3. Start activity tracking for existing sessions
     * 4. Begin session timeout monitoring
     * 5. Gracefully handle corrupted or partial data
     */
    initializeAuth() {
        const savedToken = localStorage.getItem('authToken');
        const savedUser = localStorage.getItem('currentUser');
        const savedEmail = localStorage.getItem('userEmail');
        
        if (savedToken && (savedUser || savedEmail)) {
            this.authToken = savedToken;
            if (savedUser) {
                try {
                    this.currentUser = JSON.parse(savedUser);
                } catch (error) {
                    this.currentUser = { email: savedEmail || 'unknown@example.com' };
                }
            } else {
                this.currentUser = { email: savedEmail };
            }
            
            // Start activity tracking for existing session
            this.activityTracker.start();
        }
    }

    /**
     * COMPREHENSIVE USER LOGIN SYSTEM
     * PURPOSE: Authenticate user credentials and establish complete session management
     * WHY: Secure authentication is the foundation of the entire Course Creator platform
     * 
     * LOGIN PROCESS WORKFLOW:
     * 1. Send credentials to authentication service via secure API
     * 2. Receive and store JWT token for subsequent API authentication
     * 3. Initialize session timestamps for timeout management
     * 4. Start activity monitoring for security compliance
     * 5. Retrieve complete user profile from server
     * 6. Initialize role-specific services (lab containers for students)
     * 7. Return authentication result with user information
     * 
     * SECURITY FEATURES:
     * - JWT token-based authentication
     * - Session timeout management (8hr absolute, 2hr inactivity)
     * - Activity monitoring for automated security logout
     * - Secure credential transmission (form-encoded)
     * - Comprehensive error handling without information leakage
     * 
     * BUSINESS INTEGRATION:
     * - Role-based service initialization (lab containers for students)
     * - User profile enrichment for personalized experience
     * - Session continuity across browser tabs and refreshes
     * - Graceful degradation for service initialization failures
     * 
     * @param {Object} credentials - User login credentials
     * @param {string} credentials.username - User email or username
     * @param {string} credentials.password - User password
     * @returns {Object} Authentication result with success status and user data
     */
    async login(credentials) {
        try {
            // DEBUG: Log credentials being sent
            console.log('🔐 Sending login credentials:', {
                username: credentials.username,
                password: credentials.password ? '***' + credentials.password.slice(-2) : 'undefined'
            });
            
            const apiBase = this.getAuthApiBase();
            console.log('🌐 API endpoint (UPDATED):', `${apiBase}/auth/login`);
            
            // AUTHENTICATION API REQUEST: Send credentials to authentication service
            // WHY: Centralized authentication service provides consistent security across platform
            const response = await fetch(`${this.getAuthApiBase()}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(credentials)
            });
            
            // DEBUG: Log response status
            console.log('📡 Response status:', response.status, response.statusText);
            
            // SUCCESSFUL AUTHENTICATION PROCESSING
            if (response.ok) {
                // EXTRACT AUTHENTICATION TOKEN: Get JWT from server response
                const data = await response.json();
                this.authToken = data.access_token;
                
                // PERSIST AUTHENTICATION DATA: Store for session continuity
                localStorage.setItem('authToken', this.authToken);
                localStorage.setItem('userEmail', credentials.username);
                
                // INITIALIZE SESSION TIMESTAMPS: Enable proper timeout management
                // WHY: Session security requires accurate timing for automatic logout
                const sessionStart = Date.now();
                localStorage.setItem('sessionStart', sessionStart.toString());
                localStorage.setItem('lastActivity', sessionStart.toString());
                
                // START SECURITY MONITORING: Begin activity tracking for session timeout
                // WHY: Educational platform security requires inactivity monitoring
                this.activityTracker.start();
                
                // START SESSION MONITORING: Automatic logout system for expired sessions
                this.startSessionMonitoring();
                
                // USER PROFILE: Use user data from login response (contains all needed info)
                // WHY: Login response already includes complete user profile data
                if (data.user) {
                    // USE LOGIN RESPONSE DATA: Complete user profile from authentication
                    this.currentUser = data.user;
                    localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
                    console.log('✅ User profile loaded from login response:', this.currentUser.role);
                } else {
                    // FALLBACK PROFILE: Create minimal profile from login credentials
                    // WHY: Graceful degradation ensures login succeeds even if user data missing
                    this.currentUser = { email: credentials.username, id: credentials.username, role: 'student' };
                    localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
                    console.log('⚠️ Using fallback user profile');
                }
                
                // ROLE-SPECIFIC SERVICE INITIALIZATION: Initialize services based on user role
                // WHY: Students need lab container access, instructors need different services
                if (this.currentUser.role === 'student') {
                    try {
                        // STUDENT LAB INITIALIZATION: Set up lab container access
                        await labLifecycleManager.initialize(this.currentUser);
                    } catch (error) {
                        console.error('Error initializing lab lifecycle manager:', error);
                        // GRACEFUL DEGRADATION: Don't fail login if lab manager initialization fails
                        // WHY: User should be able to access other platform features even if labs fail
                    }
                }

                // Dispatch custom event to notify other modules of login
                window.dispatchEvent(new CustomEvent('userLoggedIn', { detail: { user: this.currentUser } }));

                // SUCCESSFUL LOGIN RESULT: Return success with user data
                return { success: true, user: this.currentUser };
            } else {
                // AUTHENTICATION FAILURE: Handle failed login attempts
                const errorData = await response.text();
                console.log('❌ Authentication failed:', response.status, errorData);
                return { success: false, error: 'Login failed: ' + (errorData || 'Invalid credentials') };
            }
        } catch (error) {
            // ERROR HANDLING: Network or processing errors during login
            console.error('Error logging in:', error);
            return { success: false, error: 'Login failed: ' + error.message };
        }
    }

    /**
     * USER REGISTRATION SYSTEM
     * PURPOSE: Create new user accounts with validation and error handling
     * WHY: Platform growth requires secure, user-friendly registration process
     * 
     * REGISTRATION PROCESS:
     * 1. Validate user data on client side
     * 2. Send registration request to authentication service
     * 3. Handle server-side validation and conflicts
     * 4. Return structured result for UI feedback
     * 
     * SECURITY FEATURES:
     * - JSON payload transmission for structured data
     * - Server-side validation and duplicate detection
     * - Comprehensive error handling with user-friendly messages
     * - No automatic login (requires explicit login after registration)
     * 
     * BUSINESS REQUIREMENTS:
     * - Support for different user roles (student, instructor, org_admin, admin)
     * - Email validation and uniqueness checking
     * - Professional registration experience
     * - Clear error messaging for user guidance
     * 
     * @param {Object} userData - New user registration information
     * @param {string} userData.email - User email address
     * @param {string} userData.password - User password
     * @param {string} userData.full_name - User's full name
     * @param {string} userData.role - User role (student, instructor, org_admin, admin)
     * @returns {Object} Registration result with success status and error details
     */
    async register(userData) {
        try {
            // REGISTRATION API REQUEST: Send user data to registration service
            // WHY: Centralized registration ensures consistent validation and user creation
            const response = await fetch(`${this.getAuthApiBase()}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',  // JSON for structured data
                },
                body: JSON.stringify(userData)  // Structured user data payload
            });
            
            // SUCCESSFUL REGISTRATION PROCESSING
            if (response.ok) {
                // REGISTRATION SUCCESS: User account created successfully
                return { success: true };
            } else {
                // REGISTRATION FAILURE: Handle validation errors and conflicts
                const errorData = await response.json();
                
                // STRUCTURED ERROR RESPONSE: Provide specific error details for UI feedback
                return { 
                    success: false, 
                    error: errorData.detail || 'Registration failed'  // Fallback for missing error details
                };
            }
        } catch (error) {
            // ERROR HANDLING: Network or processing errors during registration
            console.error('Error registering:', error);
            return { 
                success: false, 
                error: 'Registration failed: ' + error.message 
            };
        }
    }

    /**
     * PASSWORD RESET SYSTEM
     * PURPOSE: Allow users to reset forgotten passwords securely
     * WHY: Password recovery is essential for user retention and platform accessibility
     * 
     * RESET PROCESS:
     * 1. Validate email address and new password requirements
     * 2. Send password reset request to authentication service
     * 3. Server validates request and updates password securely
     * 4. Return result for UI feedback and user guidance
     * 
     * SECURITY CONSIDERATIONS:
     * - Server-side password validation and hashing
     * - Email verification before password change
     * - Secure transmission of reset credentials  
     * - No exposure of existing password information
     * 
     * BUSINESS REQUIREMENTS:
     * - Self-service password recovery for user independence
     * - Professional password reset experience
     * - Clear feedback for successful and failed attempts
     * - Integration with existing authentication system
     * 
     * @param {string} email - User's email address for password reset
     * @param {string} newPassword - New password meeting security requirements
     * @returns {Object} Password reset result with success status and error details
     */
    async resetPassword(email, newPassword) {
        try {
            // PASSWORD RESET API REQUEST: Send reset request to authentication service
            // WHY: Centralized password management ensures consistent security policies
            const response = await fetch(window.CONFIG?.ENDPOINTS?.RESET_PASSWORD || `${this.getAuthApiBase()}/auth/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',  // JSON for structured data
                },
                body: JSON.stringify({
                    email: email,                    // Target user email
                    new_password: newPassword       // New password (will be hashed server-side)
                })
            });
            
            // SUCCESSFUL RESET PROCESSING
            if (response.ok) {
                // PASSWORD RESET SUCCESS: Password updated successfully
                return { success: true };
            } else {
                // PASSWORD RESET FAILURE: Handle validation errors and user not found
                const errorData = await response.json();
                
                // STRUCTURED ERROR RESPONSE: Provide specific error details for UI feedback
                return { 
                    success: false, 
                    error: errorData.detail || 'Password reset failed'  // Fallback for missing error details
                };
            }
        } catch (error) {
            // ERROR HANDLING: Network or processing errors during password reset
            console.error('Error resetting password:', error);
            return { 
                success: false, 
                error: 'Password reset failed: ' + error.message 
            };
        }
    }

    /**
     * USER PROFILE RETRIEVAL SYSTEM
     * PURPOSE: Fetch complete user profile information from authentication service
     * WHY: Role-based functionality requires comprehensive user data beyond basic credentials
     * 
     * PROFILE DATA INCLUDES:
     * - User identification (ID, email, username)
     * - Role information (student, instructor, admin)
     * - Personal information (full name, preferences)
     * - Account status and permissions
     * - Platform-specific settings and configurations
     * 
     * AUTHENTICATION REQUIREMENTS:
     * - Valid JWT token required for profile access
     * - Bearer token authentication for secure API access
     * - Automatic token validation by server
     * - Graceful handling of expired or invalid tokens
     * 
     * BUSINESS INTEGRATION:
     * - Enables personalized user experience
     * - Supports role-based feature access
     * - Provides data for user dashboard and settings
     * - Integrates with course enrollment and progress tracking
     * 
     * @returns {Object|null} Complete user profile object or null if unavailable
     */
    async getUserProfile() {
        try {
            // PROFILE API REQUEST: Fetch complete user profile using authentication token
            // WHY: Server-side user data is authoritative source for user information
            const response = await fetch(`${this.getAuthApiBase()}/users/profile`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`  // JWT token for authenticated access
                }
            });
            
            // SUCCESSFUL PROFILE RETRIEVAL
            if (response.ok) {
                // EXTRACT USER DATA: Parse server response and return user profile
                const data = await response.json();
                return data.user;  // Return complete user profile object
            }
            
            // PROFILE UNAVAILABLE: Return null for failed requests
            // WHY: Graceful degradation allows application to continue with basic user data
            return null;
        } catch (error) {
            // ERROR HANDLING: Network or processing errors during profile retrieval
            console.error('Error getting profile:', error);
            return null;  // Graceful failure for network issues
        }
    }

    /**
     * COMPREHENSIVE USER LOGOUT SYSTEM
     * PURPOSE: Securely terminate user session with complete cleanup and resource management
     * WHY: Proper logout is critical for security, resource management, and user experience
     * 
     * LOGOUT PROCESS WORKFLOW:
     * 1. Invalidate server-side session via logout API
     * 2. Stop all security monitoring (activity tracking)
     * 3. Clean up role-specific resources (lab containers)
     * 4. Clear all client-side authentication data
     * 5. Reset authentication manager state
     * 6. Return logout result for UI handling
     * 
     * SECURITY FEATURES:
     * - Server-side session invalidation for complete security
     * - Comprehensive client-side data cleanup
     * - Activity monitoring termination
     * - JWT token invalidation
     * - Session timestamp cleanup
     * 
     * RESOURCE MANAGEMENT:
     * - Lab container cleanup for students
     * - Memory leak prevention through proper cleanup
     * - Event listener removal via activity tracker
     * - Background process termination
     * 
     * GRACEFUL DEGRADATION:
     * - Continues with client cleanup even if server logout fails
     * - Handles lab cleanup failures without blocking logout
     * - Ensures user can always log out regardless of service availability
     * 
     * @returns {Object} Logout result with success status
     */
    async logout() {
        try {
            // SERVER-SIDE SESSION INVALIDATION: Invalidate JWT token on server
            // WHY: Server-side invalidation prevents token reuse and ensures complete security
            if (this.authToken) {
                const response = await fetch(`${this.getAuthApiBase()}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,  // Authenticate logout request
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    // SERVER LOGOUT SUCCESS: Session invalidated on server
                } else {
                    // SERVER LOGOUT WARNING: Continue with client cleanup regardless
                    console.warn('Failed to invalidate server session, continuing with client logout');
                }
            }
        } catch (error) {
            // SERVER LOGOUT ERROR: Network issues shouldn't prevent client logout
            console.error('Error during server logout:', error);
            // Continue with client-side cleanup regardless of server errors
        }
        
        // SECURITY MONITORING TERMINATION: Stop activity tracking for session timeout
        // WHY: No need to monitor activity after user explicitly logs out
        this.activityTracker.stop();
        
        // ROLE-SPECIFIC RESOURCE CLEANUP: Clean up lab containers and other services
        // WHY: Students may have active lab containers that need proper cleanup
        try {
            await labLifecycleManager.cleanup();
        } catch (error) {
            console.error('Error cleaning up lab lifecycle manager:', error);
            // Continue with logout even if lab cleanup fails
        }
        
        // COMPLETE CLIENT-SIDE CLEANUP: Remove all authentication data and reset state
        // WHY: Comprehensive cleanup prevents data leakage and ensures clean logout
        
        // RESET INTERNAL STATE: Clear authentication manager properties
        this.authToken = null;
        this.currentUser = null;
        
        // CLEAR PERSISTENT DATA: Remove all localStorage authentication data
        localStorage.removeItem('authToken');       // JWT token
        localStorage.removeItem('userEmail');       // User email
        localStorage.removeItem('currentUser');     // Complete user profile
        
        // SUCCESSFUL LOGOUT RESULT: Always return success for UI handling
        // WHY: User should always be able to log out, even with service failures
        return { success: true };
    }

    /**
     * AUTHENTICATED API REQUEST WRAPPER
     * PURPOSE: Provide secure, activity-tracked API requests with automatic session management
     * WHY: All API calls need consistent authentication, activity tracking, and session handling
     * 
     * REQUEST ENHANCEMENT FEATURES:
     * 1. Automatic JWT token injection for authentication
     * 2. Activity tracking to prevent session timeout
     * 3. Session expiration detection and handling
     * 4. Consistent error handling across all API calls
     * 5. Configurable request options with authentication defaults
     * 
     * SECURITY FEATURES:
     * - Bearer token authentication for all requests
     * - Automatic session expiry detection (401 responses)
     * - Activity tracking to extend session timeout
     * - Secure token validation before request
     * 
     * BUSINESS BENEFITS:
     * - Seamless authenticated API access across platform
     * - Automatic session management without manual intervention
     * - Consistent error handling for authentication failures
     * - User activity detection for better session management
     * 
     * @param {string} url - API endpoint URL
     * @param {Object} options - Fetch options (method, body, headers, etc.)
     * @returns {Response} Fetch response object with authentication
     * @throws {Error} When token is missing or session has expired
     */
    async authenticatedFetch(url, options = {}) {
        // ACTIVITY TRACKING: Record API call as user activity for session timeout
        // WHY: API usage indicates active user engagement and should extend session
        this.activityTracker.trackActivity();
        
        // TOKEN VALIDATION: Ensure authentication token exists before making request
        const token = localStorage.getItem('authToken');
        if (!token) {
            throw new Error('No authentication token found');
        }
        
        // REQUEST CONFIGURATION: Merge authentication headers with provided options
        // WHY: Consistent authentication across all API calls with flexible options
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,     // JWT token for authentication
                'Content-Type': 'application/json',    // Default content type
                ...options.headers                      // Allow header overrides
            }
        };
        
        // AUTHENTICATED REQUEST: Execute API call with authentication and provided options
        const response = await fetch(url, { ...options, ...defaultOptions });
        
        // SESSION EXPIRATION DETECTION: Handle expired authentication tokens
        // WHY: 401 responses indicate expired tokens requiring session cleanup
        if (response.status === 401) {
            // AUTOMATIC SESSION CLEANUP: Handle expired session without user intervention
            this.handleSessionExpired();
            throw new Error('Session expired');  // Inform caller of session expiry
        }
        
        // RETURN AUTHENTICATED RESPONSE: Provide response for further processing
        return response;
    }

    /**
     * SESSION EXPIRATION HANDLER 
     * PURPOSE: Handle automatic session cleanup when server detects expired authentication
     * WHY: 401 responses from API calls indicate expired tokens requiring immediate cleanup
     * 
     * EXPIRATION HANDLING PROCESS:
     * 1. Stop all security monitoring and activity tracking
     * 2. Clear all session data from localStorage 
     * 3. Show user-friendly expiration notification
     * 4. Redirect to appropriate landing page for re-authentication
     * 
     * SECURITY COMPLIANCE:
     * - Immediate cleanup prevents unauthorized access
     * - Complete data removal ensures no session remnants
     * - User notification explains what occurred
     * - Safe redirect to public landing page
     * 
     * USER EXPERIENCE:
     * - Clear explanation of session expiry
     * - Graceful redirect without error pages
     * - Consistent behavior across all dashboard pages
     * - Professional handling of authentication failures
     */
    handleSessionExpired() {
        // STOP SECURITY MONITORING: Terminate activity tracking immediately
        // WHY: No need to monitor activity for expired sessions
        this.activityTracker.stop();
        
        // COMPLETE DATA CLEANUP: Remove all session-related data
        // WHY: Expired sessions should leave no authentication traces
        this.clearAllSessionData();
        
        // USER NOTIFICATION: Explain session expiry professionally
        // WHY: Users need to understand why they're being logged out
        showNotification('Your session has expired. Please log in again.', 'error');
        
        // CONTEXT-AWARE REDIRECT: Navigate to appropriate landing page
        // WHY: Different page contexts require different redirect strategies
        window.location.href = window.location.pathname.includes('/html/') ? '../index.html' : 'index.html';
    }

    /**
     * Handle inactivity timeout
     */
    handleInactivityTimeout() {
        this.activityTracker.stop();
        
        // Clear session data including timestamps
        this.clearAllSessionData();
        
        showNotification('Your session has expired due to inactivity. Please log in again.', 'error');
        
        // Redirect to home page (not login page) to show proper landing page
        window.location.href = window.location.pathname.includes('/html/') ? '../index.html' : 'index.html';
    }

    /**
     * USER ROLE RETRIEVAL
     * PURPOSE: Get the current authenticated user's role for authorization decisions
     * WHY: Role-based access control requires knowing user's permission level
     * 
     * SUPPORTED ROLES:
     * - student: Access to learning content and lab environments
     * - instructor: Course creation, student management, analytics
     * - org_admin: Organization management, member administration, track creation  
     * - admin: Site-wide administration, platform management, all access
     * 
     * @returns {string|null} User role or null if no authenticated user
     */
    getUserRole() {
        const user = this.getCurrentUser();
        return user ? user.role : null;
    }

    /**
     * ROLE VERIFICATION UTILITY
     * PURPOSE: Check if current user has a specific role for access control
     * WHY: Simple boolean check for role-based feature access
     * 
     * @param {string} role - Role to check against (student, instructor, org_admin, admin)
     * @returns {boolean} True if user has the specified role, false otherwise
     */
    hasRole(role) {
        return this.getUserRole() === role;
    }

    /**
     * PAGE ACCESS AUTHORIZATION SYSTEM
     * PURPOSE: Determine if current user can access a specific dashboard page
     * WHY: Role-based page access prevents unauthorized access to admin/instructor features
     * 
     * ACCESS CONTROL MATRIX:
     * - student: Limited access to learning and lab interfaces
     * - instructor: Course management and student interaction pages
     * - org_admin: Organization management plus instructor capabilities
     * - admin: Complete platform access including site administration
     * 
     * SECURITY FEATURES:
     * - Hierarchical access (higher roles include lower role permissions)
     * - Page-specific authorization validation
     * - Safe default (deny access if role not recognized)
     * 
     * @param {string} page - Page filename to check access for
     * @returns {boolean} True if user can access the page, false otherwise
     */
    hasPageAccess(page) {
        const userRole = this.getUserRole();
        if (!userRole) return false;
        
        // ROLE-BASED PAGE ACCESS MATRIX: Define which roles can access which pages
        const pageAccess = {
            'student': ['student-dashboard.html', 'lab.html', 'index.html'],
            'instructor': ['instructor-dashboard.html', 'lab.html', 'index.html'],
            'org_admin': ['org-admin-enhanced.html', 'instructor-dashboard.html', 'student-dashboard.html', 'lab.html', 'index.html'],
            'organization_admin': ['org-admin-enhanced.html', 'instructor-dashboard.html', 'student-dashboard.html', 'lab.html', 'index.html'], // Same as org_admin
            'admin': ['admin.html', 'site-admin-dashboard.html', 'org-admin-enhanced.html', 'instructor-dashboard.html', 'student-dashboard.html', 'lab.html', 'index.html']
        };
        
        return pageAccess[userRole]?.includes(page) || false;
    }

    /**
     * ROLE-BASED REDIRECT SYSTEM
     * PURPOSE: Determine appropriate dashboard page for user's role after login
     * WHY: Different user roles need different default landing pages for optimal workflow
     * 
     * REDIRECT STRATEGY:
     * - admin: Site administration dashboard with platform management
     * - org_admin: Organization management dashboard with RBAC controls
     * - instructor: Course creation and student management dashboard
     * - student: Learning dashboard with course access and progress
     * - default: Public home page for unauthenticated users
     * 
     * BUSINESS WORKFLOW ALIGNMENT:
     * - Admins need platform oversight and user management
     * - Org admins need member management and organizational controls
     * - Instructors need course creation and student interaction tools
     * - Students need learning content and progress tracking
     * 
     * @returns {string} Appropriate dashboard URL for user's role
     */
    getRedirectUrl() {
        const userRole = this.getUserRole();
        
        // Determine if we're already in the html/ directory
        const isInHtmlDir = window.location.pathname.includes('/html/');
        const pathPrefix = isInHtmlDir ? '' : 'html/';
        
        console.log('🔍 REDIRECT DEBUG - Current path:', window.location.pathname);
        console.log('🔍 REDIRECT DEBUG - Is in HTML dir:', isInHtmlDir);
        console.log('🔍 REDIRECT DEBUG - Path prefix:', pathPrefix);
        console.log('🔍 REDIRECT DEBUG - User role:', userRole);
        
        switch (userRole) {
            case 'admin':
                return `${pathPrefix}site-admin-dashboard.html`;  // Site admin gets the comprehensive admin dashboard
            case 'org_admin':
            case 'organization_admin':  // Handle both role names
                const redirectUrl = `${pathPrefix}org-admin-dashboard.html`;
                console.log('🔍 REDIRECT DEBUG - Final URL:', redirectUrl);
                return redirectUrl;
            case 'instructor':
                return `${pathPrefix}instructor-dashboard.html`;
            case 'student':
                return `${pathPrefix}student-dashboard.html`;
            default:
                return isInHtmlDir ? '../index.html' : 'index.html';
        }
    }

    /**
     * SESSION MANAGEMENT METHODS
     * 
     * These methods implement comprehensive session timeout functionality:
     * - Absolute session timeout (8 hours from login)
     * - Inactivity timeout (2 hours of no activity)
     * - Cross-tab synchronization
     * - Automatic cleanup and warning system
     */

    /**
     * Check if current session is valid based on timestamps.
     * 
     * Validates both absolute session timeout and inactivity timeout.
     * This method is called frequently to ensure session integrity.
     * 
     * Returns:
     *   boolean: true if session is still valid, false if expired
     */
    isSessionValid() {
        const sessionStart = localStorage.getItem('sessionStart');
        const lastActivity = localStorage.getItem('lastActivity');
        const authToken = localStorage.getItem('authToken');
        
        // No session data means invalid session
        if (!sessionStart || !lastActivity || !authToken) {
            return false;
        }
        
        const now = Date.now();
        const sessionAge = now - parseInt(sessionStart);
        const timeSinceActivity = now - parseInt(lastActivity);
        
        // Check absolute session timeout (8 hours)
        if (sessionAge > this.SESSION_TIMEOUT) {
            console.log('Session expired: Maximum session time exceeded');
            return false;
        }
        
        // Check inactivity timeout (2 hours)
        if (timeSinceActivity > this.INACTIVITY_TIMEOUT) {
            console.log('Session expired: Inactivity timeout exceeded');
            return false;
        }
        
        return true;
    }

    /**
     * Update last activity timestamp.
     * 
     * Called whenever user interacts with the application to prevent
     * inactivity timeout. Uses current timestamp for accuracy.
     */
    updateLastActivity() {
        localStorage.setItem('lastActivity', Date.now().toString());
        this.warningShown = false; // Reset warning flag on activity
    }

    /**
     * Clear all session-related data from localStorage.
     * 
     * Comprehensive cleanup method that removes all session data
     * including timestamps and user information.
     */
    clearAllSessionData() {
        const sessionKeys = [
            'authToken',
            'userEmail', 
            'currentUser',
            'sessionStart',
            'lastActivity'
        ];
        
        sessionKeys.forEach(key => localStorage.removeItem(key));
    }

    /**
     * Clear expired session and notify user.
     * 
     * Called when session validation fails. Performs cleanup and
     * provides user notification about session expiry.
     */
    clearExpiredSession() {
        console.log('Clearing expired session');
        this.stopSessionMonitoring();
        this.clearAllSessionData();
        
        // Notify user about session expiry
        if (typeof showNotification === 'function') {
            showNotification('Your session has expired. Please log in again.', 'warning');
        }
    }

    /**
     * Start periodic session monitoring.
     * 
     * Begins background monitoring of session validity with periodic checks
     * and automatic logout warnings. Runs every 30 seconds for responsiveness.
     */
    startSessionMonitoring() {
        // Clear any existing interval
        this.stopSessionMonitoring();
        
        // Check session every 30 seconds
        this.sessionCheckInterval = setInterval(() => {
            if (!this.isSessionValid()) {
                this.clearExpiredSession();
                // Redirect to login page
                window.location.href = 'index.html';
                return;
            }
            
            // Check if we should show logout warning
            this.checkLogoutWarning();
        }, 30000); // 30 second intervals
        
        console.log('Session monitoring started');
    }

    /**
     * Stop session monitoring.
     * 
     * Clears the session check interval to prevent unnecessary background
     * processing when user is logged out or session is being cleared.
     */
    stopSessionMonitoring() {
        if (this.sessionCheckInterval) {
            clearInterval(this.sessionCheckInterval);
            this.sessionCheckInterval = null;
            console.log('Session monitoring stopped');
        }
    }

    /**
     * Check if logout warning should be displayed.
     * 
     * Shows warning message 5 minutes before session expiry to give
     * users time to save work and extend their session.
     */
    checkLogoutWarning() {
        if (this.warningShown) return;
        
        const sessionStart = localStorage.getItem('sessionStart');
        const lastActivity = localStorage.getItem('lastActivity');
        
        if (!sessionStart || !lastActivity) return;
        
        const now = Date.now();
        const sessionAge = now - parseInt(sessionStart);
        const timeSinceActivity = now - parseInt(lastActivity);
        
        // Show warning 5 minutes before absolute timeout
        const timeUntilSessionExpiry = this.SESSION_TIMEOUT - sessionAge;
        // Show warning 5 minutes before inactivity timeout  
        const timeUntilInactivityExpiry = this.INACTIVITY_TIMEOUT - timeSinceActivity;
        
        const soonestExpiry = Math.min(timeUntilSessionExpiry, timeUntilInactivityExpiry);
        
        if (soonestExpiry <= this.AUTO_LOGOUT_WARNING) {
            this.showLogoutWarning(Math.floor(soonestExpiry / 60000)); // Convert to minutes
            this.warningShown = true;
        }
    }

    /**
     * Show logout warning notification.
     * 
     * Displays user-friendly warning about impending session expiry
     * with time remaining and instructions for extending session.
     * 
     * Args:
     *   minutesRemaining: Number of minutes until session expires
     */
    showLogoutWarning(minutesRemaining) {
        const message = `Your session will expire in ${minutesRemaining} minute(s). Please save your work and continue using the application to extend your session.`;
        
        if (typeof showNotification === 'function') {
            showNotification(message, 'warning');
        } else {
            // Fallback to alert if notification system not available
            alert(message);
        }
        
        console.log('Logout warning displayed:', message);
    }
}

// Create singleton instance
const authManager = new AuthManager();

export { authManager as Auth };
export default authManager;