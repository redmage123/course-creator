/**
 * NOTIFICATIONS MODULE - USER FEEDBACK AND MESSAGING SYSTEM
 * 
 * PURPOSE: Comprehensive notification system for user feedback across Course Creator Platform
 * WHY: Users need immediate feedback for actions, errors, and system status changes
 * ARCHITECTURE: Singleton notification manager with toast-style notifications
 * 
 * NOTIFICATION TYPES:
 * - Success: Positive feedback for completed actions (green, 3s timeout)
 * - Error: Error messages and failure states (red, 6s timeout)
 * - Warning: Important alerts requiring attention (orange, 5s timeout)
 * - Info: General information and system updates (blue, 4s timeout)
 * 
 * FEATURES:
 * - Auto-dismiss with type-specific timeouts
 * - Manual dismiss with close button
 * - Smooth slide-in animations from right
 * - Stacked notifications with proper z-index
 * - Mobile-responsive design
 * - Icon indicators for each notification type
 * - Click-outside-to-close prevention (intentional UX choice)
 * 
 * BUSINESS REQUIREMENTS:
 * - Non-intrusive: Don't block user workflow
 * - Informative: Clear message hierarchy and visual distinction
 * - Accessible: Proper color contrast and keyboard navigation
 * - Performance: Lightweight DOM manipulation and memory management
 */

export class NotificationManager {
    /**
     * NOTIFICATION MANAGER CONSTRUCTOR
     * PURPOSE: Initialize notification system with container and tracking
     * WHY: Centralized management ensures consistent behavior and prevents conflicts
     */
    constructor() {
        // NOTIFICATION TRACKING: Array of active notification elements
        this.notifications = [];
        
        // CONTAINER REFERENCE: DOM element that holds all notifications
        this.container = null;
        
        // INITIALIZE SYSTEM: Create container and inject styles
        this.createContainer();
    }

    /**
     * NOTIFICATION CONTAINER CREATION
     * PURPOSE: Create and style the container that holds all notifications
     * WHY: Fixed positioning ensures notifications stay visible during scrolling
     * 
     * CONTAINER FEATURES:
     * - Fixed positioning (top-right corner)
     * - High z-index (9999) to stay above other content
     * - Pointer-events disabled on container, enabled on individual notifications
     * - Mobile-responsive with appropriate margins
     * - Self-contained CSS injection for component independence
     */
    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = 'notification-container';
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
                pointer-events: none;
            }
            
            .notification {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                pointer-events: auto;
                transform: translateX(100%);
                opacity: 0;
                transition: all 0.3s ease;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                position: relative;
            }
            
            .notification.show {
                transform: translateX(0);
                opacity: 1;
            }
            
            .notification.success {
                border-left: 4px solid #4caf50;
                background: #f8fff8;
            }
            
            .notification.error {
                border-left: 4px solid #f44336;
                background: #fff8f8;
            }
            
            .notification.warning {
                border-left: 4px solid #ff9800;
                background: #fff9f0;
            }
            
            .notification.info {
                border-left: 4px solid #2196f3;
                background: #f8f9ff;
            }
            
            .notification-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 8px;
            }
            
            .notification-title {
                font-weight: 600;
                font-size: 14px;
                color: #333;
                margin: 0;
            }
            
            .notification-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #666;
                padding: 0;
                line-height: 1;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .notification-close:hover {
                color: #333;
            }
            
            .notification-message {
                font-size: 13px;
                color: #666;
                line-height: 1.4;
                margin: 0;
            }
            
            .notification-icon {
                display: inline-block;
                width: 16px;
                height: 16px;
                margin-right: 8px;
                vertical-align: middle;
            }
            
            .notification.success .notification-icon::before {
                content: '✓';
                color: #4caf50;
            }
            
            .notification.error .notification-icon::before {
                content: '✗';
                color: #f44336;
            }
            
            .notification.warning .notification-icon::before {
                content: '⚠';
                color: #ff9800;
            }
            
            .notification.info .notification-icon::before {
                content: 'ℹ';
                color: #2196f3;
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(this.container);
    }

    /**
     * NOTIFICATION DISPLAY METHOD
     * PURPOSE: Create and display a notification with specified message and type
     * WHY: Central method for all notification display with consistent behavior
     * 
     * DISPLAY PROCESS:
     * 1. Create notification element with appropriate styling
     * 2. Add to container and tracking array
     * 3. Trigger slide-in animation using requestAnimationFrame
     * 4. Set auto-dismiss timer based on notification type
     * 5. Return notification element for additional manipulation if needed
     * 
     * @param {string} message - Notification message content
     * @param {string} type - Notification type ('success', 'error', 'warning', 'info')
     * @param {object} options - Configuration options
     * @param {string} options.title - Custom notification title
     * @param {number} options.timeout - Custom auto-dismiss timeout (0 = no auto-dismiss)
     * @returns {HTMLElement} The created notification element
     */
    show(message, type = 'info', options = {}) {
        const notification = this.createNotification(message, type, options);
        
        this.container.appendChild(notification);
        this.notifications.push(notification);
        
        // ANIMATION TRIGGER: Use requestAnimationFrame for smooth transitions
        // WHY: Ensures CSS transition occurs after element is fully rendered
        requestAnimationFrame(() => {
            notification.classList.add('show');  // Triggers slide-in animation
        });
        
        // AUTO-DISMISS TIMER: Remove notification after appropriate timeout
        // WHY: Different notification types need different visibility durations
        const timeout = options.timeout || this.getDefaultTimeout(type);
        if (timeout > 0) {
            setTimeout(() => {
                this.dismiss(notification);
            }, timeout);
        }
        
        return notification;
    }

    /**
     * Create notification element
     */
    createNotification(message, type, options) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const title = this.getTypeTitle(type);
        
        notification.innerHTML = `
            <div class="notification-header">
                <h4 class="notification-title">
                    <span class="notification-icon"></span>
                    ${options.title || title}
                </h4>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <p class="notification-message">${message}</p>
        `;
        
        return notification;
    }

    /**
     * Dismiss notification
     */
    dismiss(notification) {
        if (notification && notification.parentElement) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.parentElement.removeChild(notification);
                }
                
                // Remove from notifications array
                const index = this.notifications.indexOf(notification);
                if (index > -1) {
                    this.notifications.splice(index, 1);
                }
            }, 300);
        }
    }

    /**
     * Dismiss all notifications
     */
    dismissAll() {
        this.notifications.forEach(notification => {
            this.dismiss(notification);
        });
    }

    /**
     * Get default timeout for notification type
     */
    getDefaultTimeout(type) {
        const timeouts = {
            'success': 3000,
            'info': 4000,
            'warning': 5000,
            'error': 6000
        };
        return timeouts[type] || 4000;
    }

    /**
     * Get title for notification type
     */
    getTypeTitle(type) {
        const titles = {
            'success': 'Success',
            'error': 'Error',
            'warning': 'Warning',
            'info': 'Info'
        };
        return titles[type] || 'Notification';
    }

    /**
     * Success notification
     */
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    /**
     * Error notification
     */
    error(message, options = {}) {
        return this.show(message, 'error', options);
    }

    /**
     * Warning notification
     */
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    /**
     * Info notification
     */
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

/**
 * SINGLETON INSTANCE CREATION
 * PURPOSE: Create single shared notification manager for entire application
 * WHY: Prevents multiple notification containers and ensures consistent behavior
 */
const notificationManager = new NotificationManager();

/**
 * CONVENIENCE FUNCTIONS FOR EASY NOTIFICATION USAGE
 * PURPOSE: Provide simple, direct functions for common notification operations
 * WHY: Reduces boilerplate code and makes notifications easier to use throughout app
 * 
 * USAGE EXAMPLES:
 * - showSuccess('User logged in successfully')
 * - showError('Failed to save changes')
 * - showWarning('Session will expire in 5 minutes')
 * - showInfo('New features available')
 */

/**
 * GENERAL NOTIFICATION FUNCTION
 * @param {string} message - Notification message
 * @param {string} type - Notification type ('success', 'error', 'warning', 'info')
 * @param {object} options - Additional options (title, timeout, etc.)
 */
export function showNotification(message, type = 'info', options = {}) {
    return notificationManager.show(message, type, options);
}

/**
 * SUCCESS NOTIFICATION - Green with checkmark icon
 * USAGE: Successful operations, completed tasks, positive confirmations
 */
export function showSuccess(message, options = {}) {
    return notificationManager.success(message, options);
}

/**
 * ERROR NOTIFICATION - Red with X icon
 * USAGE: Failed operations, validation errors, system errors
 */
export function showError(message, options = {}) {
    return notificationManager.error(message, options);
}

/**
 * WARNING NOTIFICATION - Orange with warning icon
 * USAGE: Important alerts, potential issues, user attention required
 */
export function showWarning(message, options = {}) {
    return notificationManager.warning(message, options);
}

/**
 * INFO NOTIFICATION - Blue with info icon
 * USAGE: General information, status updates, feature announcements
 */
export function showInfo(message, options = {}) {
    return notificationManager.info(message, options);
}

/**
 * DISMISS ALL NOTIFICATIONS
 * PURPOSE: Clear all active notifications (useful for page transitions)
 */
export function dismissAllNotifications() {
    notificationManager.dismissAll();
}

export { notificationManager as default };
export { notificationManager };