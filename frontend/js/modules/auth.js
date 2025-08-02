/**
 * Authentication Module
 * Handles user authentication, login, registration, and session management
 */

import { CONFIG } from '../config.js';
import { showNotification } from './notifications.js';
import { ActivityTracker } from './activity-tracker.js';
import { labLifecycleManager } from './lab-lifecycle.js';

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.authToken = null;
        this.activityTracker = new ActivityTracker();
        this.authApiBase = CONFIG.API_URLS.USER_MANAGEMENT;
        
        """
        Session Management Configuration and Business Requirements
        
        SECURITY TIMEOUT CONFIGURATION:
        - SESSION_TIMEOUT: 8 hours (28,800,000 ms) - Maximum session duration
        - INACTIVITY_TIMEOUT: 2 hours (7,200,000 ms) - Inactivity threshold
        - AUTO_LOGOUT_WARNING: 5 minutes (300,000 ms) - Warning before expiry
        
        WHY THESE SPECIFIC TIMEOUTS:
        
        8-Hour Absolute Session Timeout:
        - Aligns with standard work day expectations
        - Balances security with user convenience
        - Prevents indefinite session persistence
        - Meets educational platform security requirements
        - Reduces risk of session hijacking over time
        
        2-Hour Inactivity Timeout:
        - Prevents sessions from remaining active when users step away
        - Common industry standard for educational platforms
        - Allows for lunch breaks and meetings without forced logout
        - Protects against unauthorized access on unattended devices
        
        5-Minute Warning Period:
        - Provides sufficient time for users to save work
        - Allows users to extend session through activity
        - Prevents unexpected data loss from automatic logout
        - User-friendly approach to session management
        """
        this.SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8 hours absolute maximum
        this.INACTIVITY_TIMEOUT = 2 * 60 * 60 * 1000; // 2 hours of inactivity
        this.AUTO_LOGOUT_WARNING = 5 * 60 * 1000; // 5 minutes warning period
        
        // Initialize session monitoring state
        this.sessionCheckInterval = null;
        this.warningShown = false;
    }

    /**
     * Get current user from localStorage or memory
     */
    getCurrentUser() {
        try {
            const userStr = localStorage.getItem('currentUser');
            if (userStr) {
                return JSON.parse(userStr);
            }
            
            // Fallback to userEmail if currentUser is not available
            const userEmail = localStorage.getItem('userEmail');
            if (userEmail) {
                return { email: userEmail, username: userEmail };
            }
            
            return null;
        } catch (error) {
            console.error('Error getting current user:', error);
            // Try fallback to userEmail
            const userEmail = localStorage.getItem('userEmail');
            return userEmail ? { email: userEmail, username: userEmail } : null;
        }
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!(this.getCurrentUser() && localStorage.getItem('authToken'));
    }

    /**
     * Initialize auth state from localStorage
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
     * Login user with credentials
     */
    async login(credentials) {
        try {
            const response = await fetch(`${this.authApiBase}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(credentials)
            });
            
            if (response.ok) {
                const data = await response.json();
                this.authToken = data.access_token;
                localStorage.setItem('authToken', this.authToken);
                localStorage.setItem('userEmail', credentials.username);
                
                // Initialize session timestamps for proper timeout handling
                const sessionStart = Date.now();
                localStorage.setItem('sessionStart', sessionStart.toString());
                localStorage.setItem('lastActivity', sessionStart.toString());
                
                // Start activity tracking
                this.activityTracker.start();
                
                // Start session monitoring for automatic logout
                this.startSessionMonitoring();
                
                // Get user profile
                const profile = await this.getUserProfile();
                if (profile) {
                    this.currentUser = profile;
                    localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
                } else {
                    this.currentUser = { email: credentials.username, id: credentials.username };
                    localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
                }
                
                // Initialize lab lifecycle manager for students
                if (this.currentUser.role === 'student') {
                    try {
                        await labLifecycleManager.initialize(this.currentUser);
                    } catch (error) {
                        console.error('Error initializing lab lifecycle manager:', error);
                        // Don't fail login if lab manager fails
                    }
                }
                
                return { success: true, user: this.currentUser };
            } else {
                return { success: false, error: 'Login failed' };
            }
        } catch (error) {
            console.error('Error logging in:', error);
            return { success: false, error: 'Login failed: ' + error.message };
        }
    }

    /**
     * Register new user
     */
    async register(userData) {
        try {
            const response = await fetch(`${this.authApiBase}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            
            if (response.ok) {
                return { success: true };
            } else {
                const errorData = await response.json();
                return { success: false, error: errorData.detail || 'Registration failed' };
            }
        } catch (error) {
            console.error('Error registering:', error);
            return { success: false, error: 'Registration failed: ' + error.message };
        }
    }

    /**
     * Reset password
     */
    async resetPassword(email, newPassword) {
        try {
            const response = await fetch(CONFIG.ENDPOINTS.RESET_PASSWORD, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    new_password: newPassword
                })
            });
            
            if (response.ok) {
                return { success: true };
            } else {
                const errorData = await response.json();
                return { success: false, error: errorData.detail || 'Password reset failed' };
            }
        } catch (error) {
            console.error('Error resetting password:', error);
            return { success: false, error: 'Password reset failed: ' + error.message };
        }
    }

    /**
     * Get user profile
     */
    async getUserProfile() {
        try {
            const response = await fetch(`${this.authApiBase}/users/profile`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.user;
            }
            return null;
        } catch (error) {
            console.error('Error getting profile:', error);
            return null;
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            // Call server logout endpoint to invalidate session
            if (this.authToken) {
                const response = await fetch(`${this.authApiBase}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                } else {
                    console.warn('Failed to invalidate server session, continuing with client logout');
                }
            }
        } catch (error) {
            console.error('Error during server logout:', error);
        }
        
        // Stop activity tracking
        this.activityTracker.stop();
        
        // Clean up lab lifecycle manager
        try {
            await labLifecycleManager.cleanup();
        } catch (error) {
            console.error('Error cleaning up lab lifecycle manager:', error);
        }
        
        // Clear client-side data
        this.authToken = null;
        this.currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('currentUser');
        
        return { success: true };
    }

    /**
     * Make authenticated API request
     */
    async authenticatedFetch(url, options = {}) {
        // Track this API call as activity
        this.activityTracker.trackActivity();
        
        const token = localStorage.getItem('authToken');
        if (!token) {
            throw new Error('No authentication token found');
        }
        
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            }
        };
        
        const response = await fetch(url, { ...options, ...defaultOptions });
        
        if (response.status === 401) {
            this.handleSessionExpired();
            throw new Error('Session expired');
        }
        
        return response;
    }

    /**
     * Handle session expiration
     */
    handleSessionExpired() {
        this.activityTracker.stop();
        
        // Clear session data including timestamps
        this.clearAllSessionData();
        
        showNotification('Your session has expired. Please log in again.', 'error');
        
        // Redirect to home page (not login page) to show proper landing page
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
     * Get user role
     */
    getUserRole() {
        const user = this.getCurrentUser();
        return user ? user.role : null;
    }

    /**
     * Check if user has specific role
     */
    hasRole(role) {
        return this.getUserRole() === role;
    }

    /**
     * Check if user has permission to access page
     */
    hasPageAccess(page) {
        const userRole = this.getUserRole();
        if (!userRole) return false;
        
        const pageAccess = {
            'student': ['student-dashboard.html', 'lab.html', 'index.html'],
            'instructor': ['instructor-dashboard.html', 'lab.html', 'index.html'],
            'admin': ['admin.html', 'instructor-dashboard.html', 'student-dashboard.html', 'lab.html', 'index.html']
        };
        
        return pageAccess[userRole]?.includes(page) || false;
    }

    /**
     * Get redirect URL based on user role
     */
    getRedirectUrl() {
        const userRole = this.getUserRole();
        
        switch (userRole) {
            case 'admin':
                return 'admin.html';
            case 'instructor':
                return 'instructor-dashboard.html';
            case 'student':
                return 'student-dashboard.html';
            default:
                return 'index.html';
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