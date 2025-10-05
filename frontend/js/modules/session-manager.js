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

/**
 * Session configuration
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
 * Session timeout manager class
 */
class SessionManager {
    constructor() {
        this.timeoutId = null;
        this.warningTimeoutId = null;
        this.warningShown = false;
        this.isActive = false;
    }

    /**
     * Initialize session timeout monitoring
     *
     * BUSINESS LOGIC:
     * Starts monitoring user activity and sets up auto-logout
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
     * Set up event listeners for user activity
     */
    setupActivityListeners() {
        const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];

        events.forEach(event => {
            document.addEventListener(event, () => this.onUserActivity(), { passive: true });
        });
    }

    /**
     * Handle user activity
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
     * Update last activity timestamp
     */
    updateActivity() {
        const timestamp = Date.now();
        localStorage.setItem(SESSION_CONFIG.LAST_ACTIVITY_KEY, timestamp.toString());
    }

    /**
     * Reset the session timeout
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
     * Show session timeout warning
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
     * Hide session warning modal
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
     * Check if existing session has expired
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
     * Logout user due to session timeout
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
     * Manually end session (user logout)
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
