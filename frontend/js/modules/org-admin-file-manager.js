/**
 * Organization Admin File Manager Module
 *
 * BUSINESS CONTEXT:
 * Initializes the file explorer widget for organization admin dashboard
 * with org-level permissions and file management capabilities.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Imports FileExplorer widget
 * - Configures for organization admin role
 * - Sets up org-scoped file filtering
 * - Enables upload, delete, download features
 * - Integrates with drag-drop upload
 *
 * AUTHORIZATION:
 * - Org admin can delete files within their organization
 * - Org admin can upload files
 * - Org admin can download files
 * - Files scoped to organization_id
 *
 * @module org-admin-file-manager
 */

import { FileExplorer } from './file-explorer.js';
import { CONFIG } from '../config.js';

/**
 * Initialize file explorer for organization admin
 *
 * BUSINESS LOGIC:
 * Creates file explorer instance for org admin with appropriate permissions
 * and filters files to organization scope
 *
 * @param {string} containerId - Container element ID
 * @param {number} organizationId - Organization ID for filtering files
 * @returns {FileExplorer} File explorer instance
 */
export function initOrgAdminFileExplorer(containerId, organizationId) {
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

        // Filter to organization
        organizationId: organizationId,
        fileTypes: ['syllabus', 'slides', 'video', 'document', 'pdf', 'image', 'logo'],

        // View options
        viewMode: 'grid',
        sortBy: 'date',
        sortOrder: 'desc',

        // Feature flags
        allowUpload: true,
        allowDelete: true,
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
    initOrgAdminFileExplorer
};
