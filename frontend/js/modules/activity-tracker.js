/**
 * Activity Tracker Module
 * Handles session activity tracking and inactivity timeouts
 */

import { showNotification } from './notifications.js';

export class ActivityTracker {
    constructor() {
        this.lastActivityTime = Date.now();
        this.activityCheckInterval = null;
        this.sessionWarningShown = false;
        
        // Configuration
        this.ACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutes
        this.ACTIVITY_CHECK_INTERVAL = 60 * 1000; // Check every minute
        this.ACTIVITY_WARNING_TIME = 5 * 60 * 1000; // Show warning 5 minutes before timeout
        
        // Bind methods
        this.trackActivity = this.trackActivity.bind(this);
        this.checkActivity = this.checkActivity.bind(this);
    }

    /**
     * Track user activity
     */
    trackActivity() {
        this.lastActivityTime = Date.now();
        this.sessionWarningShown = false;
        
        // Remove any existing warning
        const existingWarning = document.getElementById('session-warning');
        if (existingWarning) {
            existingWarning.remove();
        }
    }

    /**
     * Start activity tracking
     */
    start() {
        this.stop(); // Stop any existing tracking
        
        // Set up activity event listeners
        const activityEvents = [
            'mousedown', 'mousemove', 'keypress', 'scroll', 
            'touchstart', 'click', 'focus', 'blur'
        ];
        
        activityEvents.forEach(event => {
            document.addEventListener(event, this.trackActivity, { passive: true });
        });
        
        // Start monitoring
        this.activityCheckInterval = setInterval(this.checkActivity, this.ACTIVITY_CHECK_INTERVAL);
        
        console.log('Activity tracking started');
    }

    /**
     * Stop activity tracking
     */
    stop() {
        if (this.activityCheckInterval) {
            clearInterval(this.activityCheckInterval);
            this.activityCheckInterval = null;
        }
        
        // Remove event listeners
        const activityEvents = [
            'mousedown', 'mousemove', 'keypress', 'scroll', 
            'touchstart', 'click', 'focus', 'blur'
        ];
        
        activityEvents.forEach(event => {
            document.removeEventListener(event, this.trackActivity);
        });
        
        // Remove any warning
        const existingWarning = document.getElementById('session-warning');
        if (existingWarning) {
            existingWarning.remove();
        }
        
        console.log('Activity tracking stopped');
    }

    /**
     * Check for inactivity
     */
    checkActivity() {
        const timeSinceLastActivity = Date.now() - this.lastActivityTime;
        
        // Show warning if user is close to timeout
        if (timeSinceLastActivity > (this.ACTIVITY_TIMEOUT - this.ACTIVITY_WARNING_TIME) && 
            timeSinceLastActivity < this.ACTIVITY_TIMEOUT &&
            !this.sessionWarningShown) {
            this.showSessionWarning();
            this.sessionWarningShown = true;
        }
        
        // Check if session has timed out
        if (timeSinceLastActivity > this.ACTIVITY_TIMEOUT) {
            this.handleTimeout();
        }
    }

    /**
     * Show session warning
     */
    showSessionWarning() {
        const existingWarning = document.getElementById('session-warning');
        if (existingWarning) {
            return; // Warning already shown
        }
        
        const warningDiv = document.createElement('div');
        warningDiv.id = 'session-warning';
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
        
        // Add styles
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
        
        document.head.appendChild(style);
        document.body.appendChild(warningDiv);
        
        // Auto-remove warning after 30 seconds
        setTimeout(() => {
            const warning = document.getElementById('session-warning');
            if (warning) {
                warning.remove();
            }
        }, 30000);
    }

    /**
     * Handle activity timeout
     */
    handleTimeout() {
        this.stop();
        
        // Clear session data
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('userEmail');
        
        // Show notification
        showNotification('Your session has expired due to inactivity. Please log in again.', 'error');
        
        // Redirect to login
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 2000);
    }

    /**
     * Get time until timeout
     */
    getTimeUntilTimeout() {
        const timeSinceLastActivity = Date.now() - this.lastActivityTime;
        return Math.max(0, this.ACTIVITY_TIMEOUT - timeSinceLastActivity);
    }

    /**
     * Check if warning should be shown
     */
    shouldShowWarning() {
        const timeUntilTimeout = this.getTimeUntilTimeout();
        return timeUntilTimeout <= this.ACTIVITY_WARNING_TIME && timeUntilTimeout > 0;
    }

    /**
     * Reset activity timer
     */
    resetTimer() {
        this.trackActivity();
    }
}

export default ActivityTracker;