/**
 * Activity-Based Token Manager
 *
 * Business Context:
 * - Users should not be logged out while actively using the platform
 * - Tokens expire after 30 minutes of INACTIVITY, not 30 minutes from login
 * - Automatic token refresh maintains session during active use
 * - Security: No activity for 30+ minutes = automatic logout
 *
 * Technical Implementation:
 * - Tracks mouse, keyboard, and click activity
 * - Refreshes token every 20 minutes if user has been active
 * - Token expires after 30 minutes of complete inactivity
 * - Uses /auth/refresh endpoint to get fresh tokens
 *
 * @module activity-token-manager
 */

const ACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes of inactivity
const TOKEN_REFRESH_INTERVAL_MS = 20 * 60 * 1000; // Refresh every 20 minutes
const ACTIVITY_CHECK_INTERVAL_MS = 60 * 1000; // Check activity every minute

class ActivityTokenManager {
    constructor() {
        this.lastActivityTime = Date.now();
        this.lastTokenRefreshTime = Date.now();
        this.activityCheckInterval = null;
        this.isActive = false;

        console.log('🔄 Activity-based token manager initialized');
    }

    /**
     * Initialize activity tracking
     *
     * Business Context:
     * - Starts tracking user activity to maintain session
     * - Prevents unexpected logouts during active use
     * - Implements sliding window token expiration
     */
    start() {
        if (this.isActive) {
            console.log('⚠️ Activity manager already active');
            return;
        }

        this.isActive = true;
        this.lastActivityTime = Date.now();
        this.lastTokenRefreshTime = Date.now();

        // Track user activity events
        this.attachActivityListeners();

        // Start periodic activity check
        this.activityCheckInterval = setInterval(() => {
            this.checkActivity();
        }, ACTIVITY_CHECK_INTERVAL_MS);

        console.log('✅ Activity tracking started - token will refresh on activity');
    }

    /**
     * Stop activity tracking
     *
     * Called on logout or when session ends
     */
    stop() {
        if (!this.isActive) {
            return;
        }

        this.isActive = false;

        // Remove event listeners
        this.detachActivityListeners();

        // Clear interval
        if (this.activityCheckInterval) {
            clearInterval(this.activityCheckInterval);
            this.activityCheckInterval = null;
        }

        console.log('🛑 Activity tracking stopped');
    }

    /**
     * Attach activity event listeners
     *
     * Technical Implementation:
     * - Debounced to avoid excessive function calls
     * - Tracks mouse, keyboard, and click events
     * - Updates lastActivityTime on any user interaction
     */
    attachActivityListeners() {
        // Debounced activity handler (update at most once per 10 seconds)
        let debounceTimeout = null;
        this.activityHandler = () => {
            if (debounceTimeout) return;

            debounceTimeout = setTimeout(() => {
                this.recordActivity();
                debounceTimeout = null;
            }, 10000); // 10 seconds debounce
        };

        // Track multiple types of user activity
        document.addEventListener('mousemove', this.activityHandler, { passive: true });
        document.addEventListener('keypress', this.activityHandler, { passive: true });
        document.addEventListener('click', this.activityHandler, { passive: true });
        document.addEventListener('scroll', this.activityHandler, { passive: true });
        document.addEventListener('touchstart', this.activityHandler, { passive: true });

        console.log('👂 Activity event listeners attached');
    }

    /**
     * Remove activity event listeners
     */
    detachActivityListeners() {
        if (this.activityHandler) {
            document.removeEventListener('mousemove', this.activityHandler);
            document.removeEventListener('keypress', this.activityHandler);
            document.removeEventListener('click', this.activityHandler);
            document.removeEventListener('scroll', this.activityHandler);
            document.removeEventListener('touchstart', this.activityHandler);
        }

        console.log('👂 Activity event listeners removed');
    }

    /**
     * Record user activity
     *
     * Updates the last activity timestamp
     */
    recordActivity() {
        this.lastActivityTime = Date.now();
        console.log('✨ User activity detected');
    }

    /**
     * Check if token refresh is needed
     *
     * Business Logic:
     * - Only refresh if user has been active
     * - Refresh every 20 minutes during active sessions
     * - No refresh if inactive for 30+ minutes (will expire naturally)
     *
     * Security:
     * - Prevents indefinite sessions without activity
     * - Maintains session during active use
     */
    async checkActivity() {
        const now = Date.now();
        const timeSinceLastActivity = now - this.lastActivityTime;
        const timeSinceLastRefresh = now - this.lastTokenRefreshTime;

        console.log(`⏱️ Activity check: ${Math.floor(timeSinceLastActivity / 1000)}s since last activity`);

        // If inactive for more than 30 minutes, stop tracking (token will expire)
        if (timeSinceLastActivity > ACTIVITY_TIMEOUT_MS) {
            console.log('💤 User inactive for 30+ minutes - allowing token to expire');
            this.stop();

            // Redirect to login page after inactivity timeout
            this.handleInactivityTimeout();
            return;
        }

        // If active and 20+ minutes since last refresh, refresh token
        if (timeSinceLastRefresh >= TOKEN_REFRESH_INTERVAL_MS) {
            console.log('🔄 Refreshing token (20+ minutes since last refresh)');
            await this.refreshToken();
        }
    }

    /**
     * Refresh the JWT token
     *
     * Calls backend /auth/refresh endpoint to get a new token
     * Updates localStorage with the new token
     */
    async refreshToken() {
        try {
            const currentToken = localStorage.getItem('token');
            if (!currentToken) {
                console.warn('⚠️ No token found - cannot refresh');
                return;
            }

            console.log('🔄 Calling /auth/refresh endpoint...');

            const response = await fetch('https://176.9.99.103/api/v1/auth/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${currentToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    console.error('❌ Token refresh failed: Invalid or expired token');
                    this.handleTokenExpired();
                    return;
                }
                throw new Error(`Token refresh failed: ${response.status}`);
            }

            const data = await response.json();

            if (data.access_token) {
                // Update token in localStorage
                localStorage.setItem('token', data.access_token);
                this.lastTokenRefreshTime = Date.now();

                console.log('✅ Token refreshed successfully');

                // Show brief notification to user
                this.showRefreshNotification();
            } else {
                console.error('❌ Token refresh response missing access_token');
            }

        } catch (error) {
            console.error('❌ Error refreshing token:', error);

            // Don't immediately log out on refresh error - might be temporary network issue
            // Let the token expire naturally and user will be logged out then
        }
    }

    /**
     * Handle inactivity timeout
     *
     * Called when user has been inactive for 30+ minutes
     * Redirects to login page with message
     */
    handleInactivityTimeout() {
        console.log('🚪 Redirecting to login due to inactivity...');

        // Clear auth data
        localStorage.removeItem('token');
        localStorage.removeItem('user');

        // Show notification before redirect
        if (typeof showNotification === 'function') {
            showNotification('Your session expired due to inactivity. Please log in again.', 'info');
        }

        // Redirect to login after a short delay
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }

    /**
     * Handle token expired
     *
     * Called when token refresh fails with 401
     * Redirects to login page
     */
    handleTokenExpired() {
        console.log('🚪 Token expired - redirecting to login...');

        // Clear auth data
        localStorage.removeItem('token');
        localStorage.removeItem('user');

        // Redirect to login
        window.location.href = '/';
    }

    /**
     * Show brief notification when token is refreshed
     *
     * Optional visual feedback for debugging/transparency
     */
    showRefreshNotification() {
        // Only show in debug mode to avoid annoying users
        if (window.location.search.includes('debug=true')) {
            if (typeof showNotification === 'function') {
                showNotification('Session refreshed', 'success');
            }
        }
    }
}

// Create singleton instance
const activityTokenManager = new ActivityTokenManager();

// Export for use in other modules
export { activityTokenManager };
export default activityTokenManager;
