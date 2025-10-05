/**
 * ACTIVITY TRACKER MODULE - SESSION SECURITY AND TIMEOUT MANAGEMENT
 * 
 * PURPOSE: Monitor user activity to prevent unauthorized access on unattended devices
 * WHY: Security requirement for educational platforms handling sensitive student data
 * ARCHITECTURE: Event-driven activity monitoring with configurable timeout thresholds
 * 
 * SECURITY REQUIREMENTS:
 * - 30-minute inactivity timeout (educational platform standard)
 * - 5-minute advance warning before session expiry
 * - Automatic session cleanup and redirect on timeout
 * - User-friendly warning with extension capability
 * 
 * ACTIVITY MONITORING EVENTS:
 * - Mouse: mousedown, mousemove, click
 * - Keyboard: keypress, focus, blur
 * - Touch: touchstart (mobile support)
 * - Navigation: scroll events
 * 
 * BUSINESS BENEFITS:
 * - Prevents unauthorized access on shared/public computers
 * - Protects student privacy and data security
 * - Meets educational institution compliance requirements
 * - Balances security with user experience (reasonable timeout duration)
 * - Provides clear warning and extension opportunity
 * 
 * INTEGRATION:
 * - Works with authentication module for session management
 * - Uses notification system for user feedback
 * - Coordinates with lab lifecycle for resource cleanup
 */

import { showNotification } from './notifications.js';

export class ActivityTracker {
    /**
     * ACTIVITY TRACKER CONSTRUCTOR
     * PURPOSE: Initialize activity monitoring system with security-focused configuration
     * WHY: Proper initialization ensures reliable session timeout enforcement
     */
    constructor() {
        // ACTIVITY STATE TRACKING
        this.lastActivityTime = Date.now();        // Timestamp of last detected user activity
        this.activityCheckInterval = null;         // Interval reference for periodic activity checks
        this.sessionWarningShown = false;         // Prevents duplicate warning displays
        
        // SECURITY CONFIGURATION - Educational Platform Standards
        // WHY THESE SPECIFIC TIMEOUTS:
        
        // 30-MINUTE TIMEOUT: Industry standard for educational platforms
        // - Long enough for reading lengthy content and taking breaks
        // - Short enough to prevent unauthorized access on shared computers
        // - Balances security with user experience for students
        this.ACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutes
        
        // 1-MINUTE CHECK INTERVAL: Reasonable monitoring frequency
        // - Frequent enough for accurate timeout enforcement
        // - Infrequent enough to minimize performance impact
        this.ACTIVITY_CHECK_INTERVAL = 60 * 1000; // Check every minute
        
        // 5-MINUTE WARNING: Adequate warning period
        // - Gives users time to save work and extend session
        // - Prevents unexpected logouts during active work
        this.ACTIVITY_WARNING_TIME = 5 * 60 * 1000; // Show warning 5 minutes before timeout
        
        // 30-SECOND AUTO DISMISS: Automatic warning removal timeout
        // - Prevents warning from cluttering interface indefinitely
        // - Sufficient time for user to read and understand message
        // - Balances visibility with non-intrusive user experience
        this.WARNING_AUTO_DISMISS_TIME = 30 * 1000; // Remove warning after 30 seconds
        
        // METHOD BINDING: Ensure proper 'this' context in event handlers
        // WHY: Event listeners lose 'this' context without explicit binding
        this.trackActivity = this.trackActivity.bind(this);
        this.checkActivity = this.checkActivity.bind(this);
    }

    /**
     * USER ACTIVITY TRACKING METHOD
     * PURPOSE: Record user activity and reset session timeout timer
     * WHY: Any user interaction should extend the session and remove warnings
     * 
     * ACTIVITY DETECTION STRATEGY:
     * - Updates last activity timestamp to current time
     * - Resets warning state to allow future warnings
     * - Removes any displayed session warning (user is now active)
     * - Called by multiple event listeners for comprehensive activity detection
     * 
     * BUSINESS LOGIC: User activity indicates continued engagement and should
     * extend the session timeout period for security while maintaining usability
     */
    trackActivity() {
        // UPDATE ACTIVITY TIMESTAMP: Reset the session timeout clock
        this.lastActivityTime = Date.now();
        
        // RESET WARNING STATE: Allow future warnings to be shown
        this.sessionWarningShown = false;
        
        // REMOVE EXISTING WARNING: User activity dismisses timeout warnings
        // WHY: If user is active, they don't need to see session expiry warnings
        const existingWarning = document.getElementById('session-warning');
        if (existingWarning) {
            existingWarning.remove();
        }
    }

    /**
     * ACTIVITY TRACKING INITIALIZATION
     * PURPOSE: Start comprehensive user activity monitoring system
     * WHY: Session security requires active monitoring once user is authenticated
     * 
     * MONITORING STRATEGY:
     * 1. Clean up any existing tracking to prevent duplicates
     * 2. Attach event listeners for comprehensive activity detection
     * 3. Start periodic activity checking with configurable interval
     * 4. Use passive event listeners for optimal performance
     * 
     * ACTIVITY EVENTS MONITORED:
     * - Mouse: mousedown, mousemove, click (user interaction)
     * - Keyboard: keypress, focus, blur (typing and navigation)
     * - Touch: touchstart (mobile device support)
     * - Scroll: scroll events (content consumption)
     * 
     * PERFORMANCE CONSIDERATIONS: Passive listeners prevent scroll blocking
     */
    start() {
        // CLEANUP EXISTING TRACKING: Prevent duplicate event listeners and intervals
        this.stop();
        
        // COMPREHENSIVE ACTIVITY EVENT DETECTION
        // WHY THESE SPECIFIC EVENTS: Cover all meaningful user interactions
        const activityEvents = [
            'mousedown',    // Mouse button presses (clicks, drags)
            'mousemove',    // Mouse movement (active user presence)
            'keypress',     // Keyboard input (typing, shortcuts)
            'scroll',       // Content scrolling (reading, navigation)
            'touchstart',   // Touch device interaction (mobile support)
            'click',        // Button clicks and UI interaction
            'focus',        // Element focus changes (form navigation)
            'blur'          // Element blur events (tab switching)
        ];
        
        // ATTACH ACTIVITY LISTENERS: Monitor all user interaction types
        // PASSIVE LISTENERS: Improve scroll performance by not blocking default behavior
        activityEvents.forEach(event => {
            document.addEventListener(event, this.trackActivity, { passive: true });
        });
        
        // START PERIODIC MONITORING: Check activity status at regular intervals
        this.activityCheckInterval = setInterval(this.checkActivity, this.ACTIVITY_CHECK_INTERVAL);
    }

    /**
     * ACTIVITY TRACKING TERMINATION
     * PURPOSE: Completely stop all activity monitoring and clean up resources
     * WHY: Prevents memory leaks and unnecessary background processing after logout
     * 
     * CLEANUP PROCEDURE:
     * 1. Clear periodic activity checking interval
     * 2. Remove all event listeners to prevent memory leaks
     * 3. Clean up any displayed session warnings
     * 4. Reset internal state to allow clean restart
     * 
     * RESOURCE MANAGEMENT:
     * - Prevents zombie event listeners consuming memory
     * - Stops background interval processing
     * - Cleans up DOM elements created by warnings
     * - Ensures clean slate for next session
     * 
     * WHEN CALLED:
     * - User logout (manual or automatic)
     * - Session timeout expiry
     * - Page navigation away from dashboard
     * - Application shutdown or error recovery
     */
    stop() {
        // STOP PERIODIC MONITORING: Clear the interval that checks activity status
        // WHY: Prevents unnecessary background processing after user leaves
        if (this.activityCheckInterval) {
            clearInterval(this.activityCheckInterval);
            this.activityCheckInterval = null;
        }
        
        // REMOVE ALL EVENT LISTENERS: Prevent memory leaks from orphaned listeners
        // WHY: Event listeners keep references to objects, preventing garbage collection
        const activityEvents = [
            'mousedown',    // Mouse button interactions
            'mousemove',    // Mouse movement detection
            'keypress',     // Keyboard input monitoring
            'scroll',       // Page scrolling activity
            'touchstart',   // Mobile device touch events
            'click',        // UI element interactions
            'focus',        // Element focus changes
            'blur'          // Element blur events
        ];
        
        // CLEANUP EVENT LISTENERS: Remove each activity event listener
        activityEvents.forEach(event => {
            document.removeEventListener(event, this.trackActivity);
        });
        
        // REMOVE SESSION WARNING UI: Clean up any displayed timeout warnings
        // WHY: Warning should disappear when activity tracking stops
        const existingWarning = document.getElementById('session-warning');
        if (existingWarning) {
            existingWarning.remove();
        }
    }

    /**
     * PERIODIC ACTIVITY VALIDATION
     * PURPOSE: Check current user activity status and enforce timeout policies
     * WHY: Regular monitoring ensures timely warnings and automatic session cleanup
     * 
     * VALIDATION PROCESS:
     * 1. Calculate time elapsed since last user activity
     * 2. Check if user should receive timeout warning (5 minutes before expiry)
     * 3. Check if session has exceeded maximum inactivity period (30 minutes)
     * 4. Take appropriate action based on activity status
     * 
     * TWO-STAGE TIMEOUT SYSTEM:
     * - WARNING STAGE: 25 minutes of inactivity (5 minutes before timeout)
     * - TIMEOUT STAGE: 30 minutes of inactivity (automatic logout)
     * 
     * BUSINESS LOGIC:
     * - Users get fair warning before logout occurs
     * - System maintains security by enforcing inactivity limits
     * - Educational platform standard: reasonable timeout for learning activities
     * - Prevents multiple warnings from being shown for same timeout period
     */
    checkActivity() {
        // CALCULATE INACTIVITY DURATION: Time since user's last detected activity
        const timeSinceLastActivity = Date.now() - this.lastActivityTime;
        
        // WARNING THRESHOLD CHECK: Show warning 5 minutes before timeout
        // WHY: Users need advance notice to save work and extend session
        // CONDITION: User is close to timeout but hasn't exceeded it yet, and warning not already shown
        if (timeSinceLastActivity > (this.ACTIVITY_TIMEOUT - this.ACTIVITY_WARNING_TIME) && 
            timeSinceLastActivity < this.ACTIVITY_TIMEOUT &&
            !this.sessionWarningShown) {
            
            // DISPLAY WARNING: Alert user about impending session expiry
            this.showSessionWarning();
            
            // PREVENT DUPLICATE WARNINGS: Mark warning as shown for this timeout period
            // WHY: Multiple warnings would be annoying and confusing
            this.sessionWarningShown = true;
        }
        
        // TIMEOUT ENFORCEMENT: Check if maximum inactivity period has been exceeded
        // WHY: Security requirement to automatically log out inactive users
        if (timeSinceLastActivity > this.ACTIVITY_TIMEOUT) {
            this.handleTimeout();  // Execute complete session cleanup and logout
        }
    }

    /**
     * SESSION WARNING DISPLAY SYSTEM
     * PURPOSE: Show user-friendly warning about impending session timeout
     * WHY: Users need advance notice to save work and prevent unexpected logouts
     * 
     * WARNING UI FEATURES:
     * - Prominent placement (top-right corner, high z-index)
     * - Clear visual hierarchy with icon, title, and message
     * - Professional styling with Course Creator branding
     * - Manual close button for user control
     * - Automatic dismissal after 30 seconds
     * - Mobile-responsive design
     * 
     * USER EXPERIENCE DESIGN:
     * - Orange color indicates warning (not error)
     * - Clear instructions on how to extend session
     * - Non-blocking overlay that doesn't interrupt workflow
     * - Accessible with proper contrast and readable fonts
     * 
     * TECHNICAL IMPLEMENTATION:
     * - Prevents duplicate warnings with existence check
     * - Self-contained CSS injection for component independence
     * - Clean DOM manipulation with proper cleanup
     * - Responsive design with flexible sizing
     */
    showSessionWarning() {
        // DUPLICATE WARNING PREVENTION: Check if warning already exists
        // WHY: Multiple warnings would be confusing and visually cluttered
        const existingWarning = document.getElementById('session-warning');
        if (existingWarning) {
            return; // Warning already displayed, exit early
        }
        
        // CREATE WARNING CONTAINER: Main warning element with semantic structure
        const warningDiv = document.createElement('div');
        warningDiv.id = 'session-warning';
        
        // WARNING CONTENT STRUCTURE: Semantic HTML with accessibility considerations
        // WHY: Proper structure enables screen readers and maintains visual hierarchy
        warningDiv.innerHTML = `
            <div class="session-warning-content">
                <div class="warning-icon">⚠️</div>
                <div class="warning-text">
                    <strong>Session Warning</strong>
                    <p>Your session will expire in 5 minutes due to inactivity.<br>
                    Click anywhere to extend your session.</p>
                </div>
                <button class="warning-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // DYNAMIC STYLING INJECTION: Self-contained component styling
        // WHY: Component independence ensures styling works regardless of page CSS
        const style = document.createElement('style');
        style.textContent = `
            #session-warning {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ff9800;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                max-width: 350px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .session-warning-content {
                display: flex;
                align-items: flex-start;
                gap: 10px;
            }
            
            .warning-icon {
                font-size: 20px;
                line-height: 1;
            }
            
            .warning-text {
                flex: 1;
            }
            
            .warning-text strong {
                display: block;
                margin-bottom: 5px;
                font-size: 16px;
            }
            
            .warning-text p {
                margin: 0;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .warning-close {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                line-height: 1;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .warning-close:hover {
                opacity: 0.8;
            }
        `;
        
        // INJECT STYLING AND WARNING: Add to DOM for immediate display
        document.head.appendChild(style);
        document.body.appendChild(warningDiv);
        
        // AUTOMATIC CLEANUP: Remove warning after reasonable viewing time
        // WHY: Prevents warning from cluttering interface indefinitely
        // USES CONFIGURED TIMEOUT: Configurable auto-dismiss period from class constant
        setTimeout(() => {
            const warning = document.getElementById('session-warning');
            if (warning) {
                warning.remove();  // Clean removal from DOM
            }
        }, this.WARNING_AUTO_DISMISS_TIME);  // Use configured auto-dismiss timeout
    }

    /**
     * SESSION TIMEOUT HANDLER
     * PURPOSE: Execute complete session cleanup and user logout on inactivity timeout
     * WHY: Security requirement to prevent unauthorized access on unattended devices
     * 
     * TIMEOUT PROCEDURE:
     * 1. Stop all activity monitoring to prevent resource leaks
     * 2. Clear all authentication data from localStorage
     * 3. Show user-friendly notification explaining the logout
     * 4. Redirect to login page after brief delay for notification visibility
     * 
     * SECURITY ACTIONS:
     * - Complete session data cleanup (tokens, user info)
     * - Graceful user notification (avoids confusion)
     * - Automatic redirect to secure login state
     * - Cleanup prevents session hijacking on shared computers
     * 
     * USER EXPERIENCE CONSIDERATIONS:
     * - Clear explanation of why logout occurred
     * - 2-second delay allows user to read notification
     * - Redirect to familiar login page, not error page
     */
    handleTimeout() {
        // STOP MONITORING: Clean up intervals and event listeners
        this.stop();
        
        // COMPLETE SESSION CLEANUP: Remove all authentication data
        // WHY: Comprehensive cleanup prevents any residual access
        localStorage.removeItem('authToken');     // Remove JWT token
        localStorage.removeItem('currentUser');   // Remove user profile data
        localStorage.removeItem('userEmail');     // Remove email reference
        
        // USER NOTIFICATION: Explain why logout occurred
        // WHY: Users need to understand this is a security feature, not an error
        showNotification(
            'Your session has expired due to inactivity. Please log in again.', 
            'error'
        );
        
        // GRACEFUL REDIRECT: Allow time for notification to be read
        // WHY: Immediate redirect prevents user from seeing the explanation
        setTimeout(() => {
            window.location.href = window.location.pathname.includes('/html/') ? '../index.html' : 'index.html';
        }, 2000);  // 2-second delay for notification visibility
    }

    /**
     * TIMEOUT CALCULATION UTILITY
     * PURPOSE: Calculate remaining time until session timeout occurs
     * WHY: External components need to know timeout status for UI updates and warnings
     * 
     * CALCULATION METHOD:
     * - Determines time elapsed since last activity
     * - Subtracts elapsed time from maximum allowed timeout period
     * - Returns 0 if timeout has already been exceeded
     * 
     * USAGE SCENARIOS:
     * - Dashboard UI showing remaining session time
     * - Warning systems calculating when to display alerts
     * - Session extension prompts showing urgency level
     * - Analytics tracking session duration patterns
     * 
     * @returns {number} Milliseconds remaining until timeout (0 if already timed out)
     */
    getTimeUntilTimeout() {
        // CALCULATE ELAPSED TIME: How long since user was last active
        const timeSinceLastActivity = Date.now() - this.lastActivityTime;
        
        // RETURN REMAINING TIME: Ensure non-negative result even if timeout exceeded
        // WHY: Math.max prevents negative values for cleaner external usage
        return Math.max(0, this.ACTIVITY_TIMEOUT - timeSinceLastActivity);
    }

    /**
     * WARNING THRESHOLD DETECTOR
     * PURPOSE: Determine if session warning should be displayed to user
     * WHY: External components can check warning status without duplicating logic
     * 
     * WARNING CRITERIA:
     * - Remaining time is within warning threshold (5 minutes)
     * - Session hasn't already expired (time remaining > 0)
     * - Used by UI components to show warning indicators
     * 
     * BUSINESS LOGIC:
     * - Warning period starts 5 minutes before timeout
     * - Provides adequate time for users to save work and extend session
     * - Prevents warnings for already expired sessions
     * 
     * @returns {boolean} True if warning should be shown, false otherwise
     */
    shouldShowWarning() {
        const timeUntilTimeout = this.getTimeUntilTimeout();
        
        // CHECK WARNING THRESHOLD: User is within warning period but session still valid
        return timeUntilTimeout <= this.ACTIVITY_WARNING_TIME && timeUntilTimeout > 0;
    }

    /**
     * ACTIVITY TIMER RESET UTILITY
     * PURPOSE: Provide convenient method to reset activity tracking
     * WHY: External components may need to manually trigger activity updates
     * 
     * USAGE SCENARIOS:
     * - Manual session extension buttons
     * - API call success handlers that indicate user activity
     * - Background operations that should count as activity
     * - Integration with other activity detection systems
     * 
     * IMPLEMENTATION: Delegates to main trackActivity method for consistency
     * WHY: Single source of truth for activity tracking logic
     */
    resetTimer() {
        // DELEGATE TO MAIN METHOD: Use existing trackActivity logic
        // WHY: Maintains consistency and avoids code duplication
        this.trackActivity();
    }
}

export default ActivityTracker;