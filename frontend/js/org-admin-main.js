/**
 * Organization Admin Dashboard - Main Entry Point
 *
 * BUSINESS CONTEXT:
 * Main orchestration file for the organization admin dashboard.
 * Imports all modular components and exposes them globally for HTML onclick handlers.
 * Initializes the dashboard on page load.
 *
 * TECHNICAL IMPLEMENTATION:
 * - ES6 module imports for all dashboard modules
 * - Global window object exposure for legacy HTML compatibility
 * - Dashboard initialization coordination
 * - Error boundary handling
 *
 * @module org-admin-main
 */

// Import core module
import { initializeDashboard, loadTabContent, refreshCurrentTab } from './modules/org-admin-core.js';

// Import feature modules
import * as Projects from './modules/org-admin-projects.js';
import * as Instructors from './modules/org-admin-instructors.js';
import * as Students from './modules/org-admin-students.js';
import * as Tracks from './modules/org-admin-tracks.js';
import * as Settings from './modules/org-admin-settings.js';

// Import utilities (for potential direct use)
import * as Utils from './modules/org-admin-utils.js';
import * as API from './modules/org-admin-api.js';

// Import metadata-driven analytics module
import * as Analytics from './modules/org-admin-analytics.js';

// Import metadata client for analytics and insights
import { metadataClient } from './metadata-client.js';

/**
 * Global namespace for organization admin dashboard
 *
 * BUSINESS CONTEXT:
 * Exposes all dashboard functionality to global window object
 * This allows HTML onclick handlers and legacy code to access functions
 *
 * TECHNICAL IMPLEMENTATION:
 * Creates window.OrgAdmin namespace with sub-namespaces for each module
 */
window.OrgAdmin = {
    // Core functions
    Core: {
        init: initializeDashboard,
        loadTab: loadTabContent,
        refresh: refreshCurrentTab
    },

    // Projects module
    Projects: {
        load: Projects.loadProjectsData,
        showCreate: Projects.showCreateProjectModal,
        submit: Projects.submitProjectForm,
        view: Projects.viewProject,
        edit: Projects.editProject,
        manageMembers: Projects.manageMembers,
        removeMemberFromProject: Projects.removeMemberFromProject,
        deletePrompt: Projects.deleteProjectPrompt,
        confirmDelete: Projects.confirmDeleteProject,
        filter: Projects.filterProjects,
        nextStep: Projects.nextProjectStep,
        previousStep: Projects.previousProjectStep
    },

    // Instructors module
    Instructors: {
        load: Instructors.loadInstructorsData,
        showAdd: Instructors.showAddInstructorModal,
        submitAdd: Instructors.submitAddInstructor,
        view: Instructors.viewInstructor,
        assign: Instructors.assignInstructor,
        removePrompt: Instructors.removeInstructorPrompt,
        confirmRemove: Instructors.confirmRemoveInstructor,
        filter: Instructors.filterInstructors
    },

    // Students module
    Students: {
        load: Students.loadStudentsData,
        showAdd: Students.showAddStudentModal,
        submitAdd: Students.submitAddStudent,
        view: Students.viewStudent,
        enroll: Students.enrollStudent,
        viewProgress: Students.viewProgress,
        removePrompt: Students.removeStudentPrompt,
        confirmRemove: Students.confirmRemoveStudent,
        filter: Students.filterStudents,
        showBulkImport: Students.showBulkImportModal,
        processBulkImport: Students.processBulkImport
    },

    // Tracks module
    Tracks: {
        load: Tracks.loadTracksData,
        showCreate: Tracks.showCreateTrackModal,
        submit: Tracks.submitTrack,
        viewTrackDetails: Tracks.viewTrackDetails,
        editFromDetails: Tracks.editTrackFromDetails,
        editTrack: Tracks.editTrack,
        deleteTrackPrompt: Tracks.deleteTrackPrompt,
        confirmDelete: Tracks.confirmDeleteTrack
    },

    // Settings module
    Settings: {
        load: Settings.loadSettingsData,
        saveProfile: Settings.saveOrganizationProfile,
        saveContact: Settings.saveContactInformation,
        saveBranding: Settings.saveBrandingSettings,
        savePreferences: Settings.savePreferences,
        uploadLogo: Settings.uploadLogo,
        resetDefaults: Settings.resetToDefaults
    },

    // Analytics module (metadata-driven)
    Analytics: {
        loadContent: Analytics.loadContentAnalytics,
        filterByTag: Analytics.filterByTag,
        analyzeGaps: Analytics.analyzeContentGaps,
        viewTrends: Analytics.viewSearchTrends,
        generateRecommendations: Analytics.generateContentRecommendations
    },

    // Utilities (exposed for potential direct use)
    Utils: {
        escapeHtml: Utils.escapeHtml,
        capitalizeFirst: Utils.capitalizeFirst,
        parseCommaSeparated: Utils.parseCommaSeparated,
        formatDate: Utils.formatDate,
        formatDuration: Utils.formatDuration,
        showNotification: Utils.showNotification,
        openModal: Utils.openModal,
        closeModal: Utils.closeModal,
        validateEmail: Utils.validateEmail,
        debounce: Utils.debounce,
        generateUniqueId: Utils.generateUniqueId,
        hasPermission: Utils.hasPermission
    },

    // Metadata client (exposed for direct access)
    Metadata: metadataClient
};

/**
 * Initialize dashboard on DOM ready
 *
 * BUSINESS LOGIC:
 * Waits for DOM to be fully loaded before initializing dashboard
 * Implements error boundary to catch initialization failures
 */
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('Organization Admin Dashboard - Initializing...');
        await initializeDashboard();
        console.log('Organization Admin Dashboard - Ready');
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        Utils.showNotification('Dashboard initialization failed. Please refresh the page.', 'error', 10000);
    }
});

/**
 * Handle global errors
 *
 * TECHNICAL IMPLEMENTATION:
 * Catches unhandled errors and displays user-friendly messages
 */
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    Utils.showNotification('An unexpected error occurred. Please try again.', 'error');
});

/**
 * Handle unhandled promise rejections
 */
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    Utils.showNotification('An unexpected error occurred. Please try again.', 'error');
});

// Export for potential module-based usage
export { initializeDashboard, OrgAdmin };
