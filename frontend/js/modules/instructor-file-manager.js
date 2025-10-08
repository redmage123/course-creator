/**
 * Instructor File Manager Module
 *
 * BUSINESS CONTEXT:
 * Initializes the file explorer widget for instructor dashboard
 * with course-level permissions and file management capabilities.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Imports FileExplorer widget
 * - Configures for instructor role
 * - Sets up course-scoped file filtering
 * - Enables upload, conditional delete, download features
 * - Integrates with drag-drop upload
 *
 * AUTHORIZATION:
 * - Instructor can delete only files they uploaded
 * - Instructor can upload files
 * - Instructor can download files
 * - Files scoped to course_id
 *
 * @module instructor-file-manager
 */

import { FileExplorer } from './file-explorer.js';
import { CONFIG } from '../config.js';

/**
 * Initialize file explorer for instructor
 *
 * BUSINESS LOGIC:
 * Creates file explorer instance for instructor with appropriate permissions
 * and filters files to course scope
 *
 * @param {string} containerId - Container element ID
 * @param {number} courseId - Course ID for filtering files (optional - shows all instructor files if not provided)
 * @returns {FileExplorer} File explorer instance
 */
export function initInstructorFileExplorer(containerId, courseId = null) {
    const container = document.getElementById(containerId);

    if (!container) {
        console.error(`Container ${containerId} not found`);
        return null;
    }

    // Get current user
    const currentUser = getCurrentUser();

    if (!currentUser) {
        console.error('No current user found');
        return null;
    }

    // Create file explorer instance
    const fileExplorer = new FileExplorer(container, {
        // API configuration
        apiEndpoint: `${CONFIG.ENDPOINTS.METADATA_SERVICE}/files`,
        uploadEndpoint: `${CONFIG.ENDPOINTS.CONTENT_SERVICE}/upload`,

        // Filter to course (if provided)
        courseId: courseId,
        fileTypes: ['syllabus', 'slides', 'video', 'document', 'pdf', 'image'],

        // View options
        viewMode: 'grid',
        sortBy: 'date',
        sortOrder: 'desc',

        // Feature flags
        allowUpload: true,
        allowDelete: true,  // File explorer will enforce RBAC (only own files)
        allowDownload: true,
        allowPreview: true,
        enableDragDrop: true,
        multiSelect: true,

        // Event callbacks
        onFileSelect: (file) => {
            console.log('File selected:', file);
        },

        onFileDelete: (file) => {
            console.log('File deleted:', file);
            showNotification(`File "${file.filename}" deleted successfully`, 'success');

            // Refresh file count
            updateFileStats();
        },

        onFileUpload: (response, file) => {
            console.log('File uploaded:', file);
            showNotification(`File "${file.name}" uploaded successfully`, 'success');

            // Refresh file count
            updateFileStats();
        },

        onError: (error) => {
            console.error('File explorer error:', error);
            showNotification(error.message || 'An error occurred', 'error');
        }
    });

    return fileExplorer;
}

/**
 * Get current authenticated user
 *
 * @returns {Object|null} Current user object
 */
function getCurrentUser() {
    try {
        const userStr = localStorage.getItem('currentUser');
        return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
        console.error('Failed to get current user:', error);
        return null;
    }
}

/**
 * Show notification to user
 *
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info, warning)
 */
function showNotification(message, type = 'info') {
    // TODO: Integrate with global notification system
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Fallback to alert for now
    if (type === 'error') {
        alert(message);
    }
}

/**
 * Update file statistics in dashboard
 */
function updateFileStats() {
    // TODO: Implement file statistics update
    console.log('Updating file statistics...');
}

// Export for use in dashboard
export default {
    initInstructorFileExplorer
};
