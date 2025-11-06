/**
 * Session Management Module
 *
 * BUSINESS CONTEXT:
 * Manages user session timeouts for security and compliance.
 * Automatically logs out inactive users after a configurable timeout period.
 *
 * SECURITY BENEFITS:
 * - Prevents unauthorized access to abandoned sessions
 * - Reduces risk of session hijacking
 * - Complies with security best practices (OWASP)
 * - Protects sensitive educational data
 *
 * @module session-manager
 */
const SESSION_CONFIG = {
    // Timeout duration in milliseconds (default: 30 minutes)
    TIMEOUT_DURATION: 30 * 60 * 1000,

    // Warning before logout (5 minutes before timeout)
    WARNING_DURATION: 5 * 60 * 1000,

    // Local storage keys
    LAST_ACTIVITY_KEY: 'last_activity_timestamp',
    SESSION_WARNING_SHOWN: 'session_warning_shown'
};

/**
 * Session Timeout Manager Class
 *
 * BUSINESS REQUIREMENT:
 * Manages automatic user logout after periods of inactivity to enhance
 * security and comply with best practices.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tracks user activity events (mouse, keyboard, touch)
 * - Implements timeout counters with configurable duration
 * - Shows warning before auto-logout
 * - Cleans up session data on logout
 *
 * WHY THIS MATTERS:
 * Session timeouts prevent unauthorized access to abandoned sessions,
 * protecting sensitive educational data and user privacy.
 *
 * @class
 */
class SessionManager {
    /**
     * Session Manager Constructor
     *
     * BUSINESS LOGIC:
     * Initializes session manager with default inactive state and
     * prepares timeout tracking variables.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Initializes timeout IDs to null
     * - Sets warning shown flag to false
     * - Sets active flag to false
     *
     * WHY THIS MATTERS:
     * Proper initialization ensures clean state before monitoring begins.
     *
     * @constructor
     */
    constructor() {
        this.timeoutId = null;
        this.warningTimeoutId = null;
        this.warningShown = false;
        this.isActive = false;
    }

    /**
     * Initialize Session Timeout Monitoring
     *
     * BUSINESS LOGIC:
     * Starts monitoring user activity and sets up auto-logout functionality.
     * Prevents re-initialization if already active.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Updates last activity timestamp
     * - Registers activity event listeners (mouse, keyboard, scroll, touch)
     * - Starts timeout countdown
     * - Checks for existing expired sessions
     * - Sets active flag to true
     *
     * WHY THIS MATTERS:
     * Session monitoring must start immediately after login to ensure
     * security policies are enforced throughout the user's session.
     *
     * @returns {void}
     */
    init() {
        if (this.isActive) return;

        console.log('Session timeout initialized:', SESSION_CONFIG.TIMEOUT_DURATION / 1000 / 60, 'minutes');

        // Update last activity timestamp
        this.updateActivity();

        // Set up activity listeners
        this.setupActivityListeners();

        // Start timeout countdown
        this.resetTimeout();

        // Check for existing sessions
        this.checkExistingSession();

        this.isActive = true;
    }

    /**
     * Setup Activity Event Listeners
     *
     * BUSINESS LOGIC:
     * Registers event listeners for various user interactions to detect activity
     * and reset the session timeout.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Listens for: mousedown, keydown, scroll, touchstart, click events
     * - Uses passive listeners for performance
     * - Triggers onUserActivity() on any detected event
     *
     * WHY THIS MATTERS:
     * Comprehensive activity detection ensures users aren't logged out while
     * actively using the application.
     *
     * @returns {void}
     */
    setupActivityListeners() {
        const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];

        events.forEach(event => {
            document.addEventListener(event, () => this.onUserActivity(), { passive: true });
        });
    }

    /**
     * Handle User Activity Event
     *
     * BUSINESS LOGIC:
     * Responds to user activity by updating the activity timestamp,
     * resetting the timeout, and hiding any active warnings.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Updates last activity timestamp in localStorage
     * - Resets both warning and logout timeouts
     * - Hides warning modal if currently shown
     *
     * WHY THIS MATTERS:
     * Activity handling ensures users aren't interrupted or logged out
     * while actively working.
     *
     * @returns {void}
     */
    onUserActivity() {
        this.updateActivity();
        this.resetTimeout();

        // Hide warning if shown
        if (this.warningShown) {
            this.hideWarning();
        }
    }

    /**
     * Update Last Activity Timestamp
     *
     * BUSINESS LOGIC:
     * Records the current time as the last user activity timestamp
     * for timeout calculation.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Gets current timestamp using Date.now()
     * - Stores timestamp in localStorage for persistence
     * - Converts to string for localStorage compatibility
     *
     * WHY THIS MATTERS:
     * Timestamp persistence enables session timeout enforcement even
     * if the user navigates between pages.
     *
     * @returns {void}
     */
    updateActivity() {
        const timestamp = Date.now();
        localStorage.setItem(SESSION_CONFIG.LAST_ACTIVITY_KEY, timestamp.toString());
    }

    /**
     * Reset Session Timeout Counters
     *
     * BUSINESS LOGIC:
     * Clears existing timeouts and starts new countdown timers for
     * warning display and automatic logout.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Clears existing timeout and warning timeout IDs
     * - Resets warning shown flag
     * - Removes warning flag from localStorage
     * - Sets new warning timeout (25 minutes by default)
     * - Sets new logout timeout (30 minutes by default)
     *
     * WHY THIS MATTERS:
     * Resetting timeouts on activity ensures users get the full timeout
     * period from their last action.
     *
     * @returns {void}
     */
    resetTimeout() {
        // Clear existing timeouts
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        if (this.warningTimeoutId) {
            clearTimeout(this.warningTimeoutId);
        }

        // Reset warning flag
        this.warningShown = false;
        localStorage.removeItem(SESSION_CONFIG.SESSION_WARNING_SHOWN);

        // Set warning timeout (5 minutes before logout)
        const warningTime = SESSION_CONFIG.TIMEOUT_DURATION - SESSION_CONFIG.WARNING_DURATION;
        this.warningTimeoutId = setTimeout(() => this.showWarning(), warningTime);

        // Set logout timeout
        this.timeoutId = setTimeout(() => this.logout(), SESSION_CONFIG.TIMEOUT_DURATION);
    }

    /**
     * Show Session Timeout Warning Modal
     *
     * BUSINESS LOGIC:
     * Displays a warning modal to inform users their session will expire soon
     * due to inactivity, giving them a chance to continue or logout.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Prevents duplicate warnings if already shown
     * - Sets warning shown flag and localStorage marker
     * - Creates and injects modal HTML dynamically
     * - Calculates remaining minutes from WARNING_DURATION
     * - Adds event listeners for Continue and Logout buttons
     *
     * WHY THIS MATTERS:
     * Warning modals prevent unexpected logouts and give users control
     * over session continuation.
     *
     * @returns {void}
     */
    showWarning() {
        if (this.warningShown) return;

        this.warningShown = true;
        localStorage.setItem(SESSION_CONFIG.SESSION_WARNING_SHOWN, 'true');

        const minutesLeft = SESSION_CONFIG.WARNING_DURATION / 1000 / 60;

        // Create warning modal
        const warningHTML = `
            <div id="sessionWarningModal" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div style="
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    max-width: 400px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <h3 style="margin-top: 0; color: #f59e0b;">⚠️ Session Expiring</h3>
                    <p>Your session will expire in ${minutesLeft} minutes due to inactivity.</p>
                    <p><strong>Move your mouse or press any key to stay logged in.</strong></p>
                    <div style="margin-top: 1.5rem; display: flex; gap: 1rem;">
                        <button id="continueSessionBtn" style="
                            flex: 1;
                            padding: 0.75rem;
                            background: #2563eb;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-weight: 600;
                        ">Continue Session</button>
                        <button id="logoutNowBtn" style="
                            flex: 1;
                            padding: 0.75rem;
                            background: #dc2626;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-weight: 600;
                        ">Logout Now</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', warningHTML);

        // Add event listeners
        document.getElementById('continueSessionBtn').addEventListener('click', () => {
            this.onUserActivity();
            this.hideWarning();
        });

        document.getElementById('logoutNowBtn').addEventListener('click', () => {
            this.logout();
        });
    }

    /**
     * Hide Session Warning Modal
     *
     * BUSINESS LOGIC:
     * Removes the session warning modal from the DOM and clears warning flags.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Finds and removes modal element from DOM
     * - Resets warning shown flag to false
     * - Removes warning flag from localStorage
     *
     * WHY THIS MATTERS:
     * Proper cleanup prevents duplicate modals and ensures clean UI state.
     *
     * @returns {void}
     */
    hideWarning() {
        const modal = document.getElementById('sessionWarningModal');
        if (modal) {
            modal.remove();
        }
        this.warningShown = false;
        localStorage.removeItem(SESSION_CONFIG.SESSION_WARNING_SHOWN);
    }

    /**
     * Check if Existing Session Has Expired
     *
     * BUSINESS LOGIC:
     * Validates whether the user's session has expired based on stored
     * last activity timestamp, logging them out if necessary.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Reads last activity timestamp from localStorage
     * - Calculates time elapsed since last activity
     * - Compares against TIMEOUT_DURATION threshold
     * - Triggers logout if threshold exceeded
     *
     * WHY THIS MATTERS:
     * Session validation on page load ensures security even if the user
     * navigates away and returns after the timeout period.
     *
     * @returns {void}
     */
    checkExistingSession() {
        const lastActivity = localStorage.getItem(SESSION_CONFIG.LAST_ACTIVITY_KEY);

        if (lastActivity) {
            const timeSinceActivity = Date.now() - parseInt(lastActivity);

            if (timeSinceActivity > SESSION_CONFIG.TIMEOUT_DURATION) {
                console.log('Session expired due to inactivity');
                this.logout();
            }
        }
    }

    /**
     * Logout User Due to Session Timeout
     *
     * BUSINESS LOGIC:
     * Performs automatic logout by clearing all session data and redirecting
     * to the login page with an expiration message.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Logs timeout event to console
     * - Removes all session-related localStorage items:
     *   - Activity timestamps
     *   - Auth tokens
     *   - User data
     *   - Session start times
     * - Shows alert informing user of timeout
     * - Redirects to login page (../index.html)
     *
     * WHY THIS MATTERS:
     * Complete session cleanup prevents security vulnerabilities and ensures
     * users must re-authenticate to access protected resources.
     *
     * @returns {void}
     */
    logout() {
        console.log('Session timeout - logging out user');

        // Clear session data
        localStorage.removeItem(SESSION_CONFIG.LAST_ACTIVITY_KEY);
        localStorage.removeItem(SESSION_CONFIG.SESSION_WARNING_SHOWN);
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('sessionStart');
        localStorage.removeItem('lastActivity');

        // Show logout message
        alert('Your session has expired due to inactivity. Please log in again.');

        // Redirect to login
        window.location.href = '../index.html';
    }

    /**
     * Manually End Session (User-Initiated Logout)
     *
     * BUSINESS LOGIC:
     * Cleanly terminates session monitoring when user logs out manually,
     * cleaning up timers and storage without redirecting.
     *
     * TECHNICAL IMPLEMENTATION:
     * - Clears timeout timer IDs to stop monitoring
     * - Clears warning timeout timer ID
     * - Removes activity timestamp from localStorage
     * - Removes warning flag from localStorage
     * - Sets active flag to false
     *
     * WHY THIS MATTERS:
     * Proper cleanup on manual logout prevents memory leaks and ensures
     * session monitoring doesn't continue after logout.
     *
     * @returns {void}
     */
    endSession() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        if (this.warningTimeoutId) {
            clearTimeout(this.warningTimeoutId);
        }

        localStorage.removeItem(SESSION_CONFIG.LAST_ACTIVITY_KEY);
        localStorage.removeItem(SESSION_CONFIG.SESSION_WARNING_SHOWN);

        this.isActive = false;
    }
}

// Create singleton instance
const sessionManager = new SessionManager();

// Export for use in other modules
export default sessionManager;
export { SESSION_CONFIG };
