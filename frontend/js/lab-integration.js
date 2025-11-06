/**
 * Lab Integration Script
 * Integrates lab lifecycle management with the authentication system
 * and provides global functions for lab management
 */

import authManager from './modules/auth.js';
import { labLifecycleManager } from './modules/lab-lifecycle.js';

class LabIntegration {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     */
    constructor() {
        this.initialized = false;
    }

    /**
     * Initialize lab integration
     */
    async initialize() {
        if (this.initialized) return;


        try {
            // Check if user is authenticated
            const currentUser = authManager.getCurrentUser();
            
            if (currentUser && currentUser.role === 'student') {
                // Initialize lab lifecycle manager for students
                await labLifecycleManager.initialize(currentUser);
                
                // Set up automatic enrollment detection
                this.setupEnrollmentDetection();
            }

            this.initialized = true;
            
        } catch (error) {
            console.error('Error initializing lab integration:', error);
        }
    }

    /**
     * Set up detection for new course enrollments
     */
    setupEnrollmentDetection() {
        // Listen for enrollment changes in localStorage
        window.addEventListener('storage', (event) => {
            if (event.key === 'enrolledCourses' && event.newValue) {
                try {
                    const courses = JSON.parse(event.newValue);
                    labLifecycleManager.updateEnrolledCourses(courses);
                } catch (error) {
                    console.error('Error updating enrolled courses:', error);
                }
            }
        });

        // Check for enrolled courses periodically
        setInterval(async () => {
            try {
                const storedCourses = localStorage.getItem('enrolledCourses');
                if (storedCourses) {
                    const courses = JSON.parse(storedCourses);
                    await labLifecycleManager.updateEnrolledCourses(courses);
                }
            } catch (error) {
                console.error('Error checking enrolled courses:', error);
            }
        }, 60000); // Check every minute
    }

    /**
     * Enhanced logout function with lab cleanup
     */
    async logout() {
        try {
            
            // Use auth manager logout (which includes lab cleanup)
            await authManager.logout();
            
            // Additional cleanup
            localStorage.removeItem('enrolledCourses');
            
            // Redirect to login
            window.location.href = 'html/index.html';
            
        } catch (error) {
            console.error('Error during enhanced logout:', error);
            // Force redirect even if cleanup fails
            window.location.href = 'html/index.html';
        }
    }

    /**
     * Enhanced lab access function
     */
    async openLabEnvironment(courseId) {
        try {
            
            // Check if user is authenticated
            if (!authManager.isAuthenticated()) {
                throw new Error('User not authenticated');
            }

            const currentUser = authManager.getCurrentUser();
            if (currentUser.role !== 'student') {
                throw new Error('Lab access is only available for students');
            }

            // Show loading notification
            this.showNotification('Preparing lab environment...', 'info');
            
            // Get lab access URL through lifecycle manager
            const labUrl = await labLifecycleManager.accessLab(courseId);
            
            if (labUrl) {
                // Open lab in new window/tab
                const labWindow = window.open(
                    labUrl, 
                    `lab-${courseId}`, 
                    'width=1200,height=800,scrollbars=yes,resizable=yes,menubar=no,toolbar=no'
                );
                
                if (labWindow) {
                    this.showNotification('Lab environment opened successfully!', 'success');
                    
                    // Focus the new window
                    labWindow.focus();
                    
                    // Track lab access
                    this.trackLabAccess(courseId);
                } else {
                    this.showNotification('Please allow popups to open the lab environment', 'warning');
                }
            } else {
                throw new Error('Lab environment is not ready');
            }
            
        } catch (error) {
            console.error('Error opening lab environment:', error);
            this.showNotification('Error opening lab: ' + error.message, 'error');
            
            // Try to recover by initializing lab
            try {
                await labLifecycleManager.getOrCreateStudentLab(courseId);
                this.showNotification('Lab environment is being created. Please try again in a few moments.', 'info');
            } catch (initError) {
                console.error('Error initializing lab:', initError);
                this.showNotification('Failed to initialize lab environment. Please contact support.', 'error');
            }
        }
    }

    /**
     * Get lab status with enhanced error handling
     */
    getLabStatus(courseId) {
        try {
            return labLifecycleManager.getLabStatus(courseId);
        } catch (error) {
            console.error('Error getting lab status:', error);
            return 'error';
        }
    }

    /**
     * Check if lab is ready with enhanced validation
     */
    isLabReady(courseId) {
        try {
            return labLifecycleManager.isLabReady(courseId);
        } catch (error) {
            console.error('Error checking lab readiness:', error);
            return false;
        }
    }

    /**
     * Track lab access for analytics
     */
    trackLabAccess(courseId) {
        try {
            const accessData = {
                courseId: courseId,
                timestamp: new Date().toISOString(),
                userId: authManager.getCurrentUser()?.id || 'unknown'
            };

            // Store access data
            const existingAccess = JSON.parse(localStorage.getItem('labAccess') || '[]');
            existingAccess.push(accessData);
            
            // Keep only last 100 accesses
            if (existingAccess.length > 100) {
                existingAccess.splice(0, existingAccess.length - 100);
            }
            
            localStorage.setItem('labAccess', JSON.stringify(existingAccess));
            
            
        } catch (error) {
            console.error('Error tracking lab access:', error);
        }
    }

    /**
     * Show notifications with enhanced styling
     */
    showNotification(message, type = 'info') {
        // Check if we're in a browser environment
        if (typeof document === 'undefined') return;

        const notification = document.createElement('div');
        notification.className = `lab-notification lab-notification-${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        notification.innerHTML = `
            <div class="lab-notification-content">
                <i class="${icons[type] || icons.info}"></i>
                <span class="lab-notification-message">${message}</span>
                <button class="lab-notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add custom styles if not already present
        if (!document.getElementById('lab-notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'lab-notification-styles';
            styles.textContent = `
                .lab-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    min-width: 300px;
                    max-width: 500px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    animation: slideIn 0.3s ease-out;
                }
                
                .lab-notification-success { border-left: 4px solid #28a745; }
                .lab-notification-error { border-left: 4px solid #dc3545; }
                .lab-notification-warning { border-left: 4px solid #ffc107; }
                .lab-notification-info { border-left: 4px solid #17a2b8; }
                
                .lab-notification-content {
                    display: flex;
                    align-items: center;
                    padding: 15px;
                    gap: 10px;
                }
                
                .lab-notification-message {
                    flex: 1;
                    font-size: 14px;
                    color: #333;
                }
                
                .lab-notification-close {
                    background: none;
                    border: none;
                    color: #666;
                    cursor: pointer;
                    padding: 5px;
                    border-radius: 3px;
                }
                
                .lab-notification-close:hover {
                    background: #f8f9fa;
                    color: #333;
                }
                
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOut 0.3s ease-in forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    /**
     * Get lab analytics data
     */
    getLabAnalytics() {
        try {
            const accessData = JSON.parse(localStorage.getItem('labAccess') || '[]');
            return {
                totalAccesses: accessData.length,
                coursesAccessed: [...new Set(accessData.map(a => a.courseId))].length,
                lastAccess: accessData.length > 0 ? accessData[accessData.length - 1].timestamp : null,
                accessHistory: accessData
            };
        } catch (error) {
            console.error('Error getting lab analytics:', error);
            return {
                totalAccesses: 0,
                coursesAccessed: 0,
                lastAccess: null,
                accessHistory: []
            };
        }
    }
}

// Create global instance
const labIntegration = new LabIntegration();

// Auto-initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        labIntegration.initialize();
    });
} else {
    labIntegration.initialize();
}

// Make functions globally available
window.labIntegration = labIntegration;
window.logout = () => labIntegration.logout();
window.openLabEnvironment = (courseId) => labIntegration.openLabEnvironment(courseId);
window.getLabStatus = (courseId) => labIntegration.getLabStatus(courseId);
window.isLabReady = (courseId) => labIntegration.isLabReady(courseId);

// Export for module use
export { labIntegration, LabIntegration };