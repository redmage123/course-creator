/**
 * Notifications Module
 * Handles displaying user notifications, alerts, and messages
 */

export class NotificationManager {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.createContainer();
    }

    /**
     * Create notification container
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
     * Show notification
     */
    show(message, type = 'info', options = {}) {
        const notification = this.createNotification(message, type, options);
        
        this.container.appendChild(notification);
        this.notifications.push(notification);
        
        // Trigger animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
        
        // Auto-dismiss after timeout
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

// Create singleton instance
const notificationManager = new NotificationManager();

// Export convenience functions
export function showNotification(message, type = 'info', options = {}) {
    return notificationManager.show(message, type, options);
}

export function showSuccess(message, options = {}) {
    return notificationManager.success(message, options);
}

export function showError(message, options = {}) {
    return notificationManager.error(message, options);
}

export function showWarning(message, options = {}) {
    return notificationManager.warning(message, options);
}

export function showInfo(message, options = {}) {
    return notificationManager.info(message, options);
}

export function dismissAllNotifications() {
    notificationManager.dismissAll();
}

export { notificationManager as default };
export { notificationManager };