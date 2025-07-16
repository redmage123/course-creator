/**
 * Authentication Module
 * Handles user authentication, login, registration, and session management
 */

import { CONFIG } from '../config.js';
import { showNotification } from './notifications.js';
import { ActivityTracker } from './activity-tracker.js';

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.authToken = null;
        this.activityTracker = new ActivityTracker();
        this.authApiBase = CONFIG.API_URLS.USER_MANAGEMENT;
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
                
                // Start activity tracking
                this.activityTracker.start();
                
                // Get user profile
                const profile = await this.getUserProfile();
                if (profile) {
                    this.currentUser = profile;
                    localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
                } else {
                    this.currentUser = { email: credentials.username };
                    localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
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
                    console.log('Server session invalidated successfully');
                } else {
                    console.warn('Failed to invalidate server session, continuing with client logout');
                }
            }
        } catch (error) {
            console.error('Error during server logout:', error);
        }
        
        // Stop activity tracking
        this.activityTracker.stop();
        
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
        
        // Clear session data
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('userEmail');
        
        showNotification('Your session has expired. Please log in again.', 'error');
        
        // Redirect to login
        window.location.href = 'index.html';
    }

    /**
     * Handle inactivity timeout
     */
    handleInactivityTimeout() {
        this.activityTracker.stop();
        
        // Clear session data
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('userEmail');
        
        showNotification('Your session has expired due to inactivity. Please log in again.', 'error');
        
        // Redirect to login
        window.location.href = 'index.html';
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
}

// Create singleton instance
const authManager = new AuthManager();

export { authManager as Auth };
export default authManager;