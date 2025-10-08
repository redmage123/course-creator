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
import * as TargetRoles from './modules/org-admin-target-roles.js';
import * as AIAssistant from './modules/ai-assistant.js';
import * as FileManager from './modules/org-admin-file-manager.js';

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
        previousStep: Projects.previousProjectStep,
        regenerateAI: Projects.regenerateAISuggestions,
        toggleChat: Projects.toggleAIChatPanel,
        sendChatMessage: Projects.sendAIChatMessage
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

    // Target Roles module
    TargetRoles: {
        get: TargetRoles.getTargetRoles,
        add: TargetRoles.addTargetRole,
        update: TargetRoles.updateTargetRole,
        delete: TargetRoles.deleteTargetRole,
        reset: TargetRoles.resetTargetRolesToDefaults,
        render: TargetRoles.renderTargetRolesList,
        init: TargetRoles.initializeTargetRolesManagement
    },

    // Analytics module (metadata-driven)
    Analytics: {
        loadContent: Analytics.loadContentAnalytics,
        filterByTag: Analytics.filterByTag,
        analyzeGaps: Analytics.analyzeContentGaps,
        viewTrends: Analytics.viewSearchTrends,
        generateRecommendations: Analytics.generateContentRecommendations
    },

    // File Manager module
    Files: {
        initExplorer: FileManager.initOrgAdminFileExplorer
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
    Metadata: metadataClient,

    // AI Assistant (context-aware with RAG and web search)
    AI: {
        initialize: AIAssistant.initializeAIAssistant,
        sendMessage: AIAssistant.sendContextAwareMessage,
        getContext: AIAssistant.getCurrentContext,
        clearHistory: AIAssistant.clearConversationHistory,
        exportHistory: AIAssistant.exportConversationHistory,
        CONTEXTS: AIAssistant.CONTEXT_TYPES
    }
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

/**
 * Global function aliases for HTML onclick handlers
 *
 * BUSINESS CONTEXT:
 * HTML onclick attributes cannot access namespaced functions, so we create
 * global aliases for commonly-used functions.
 *
 * TECHNICAL IMPLEMENTATION:
 * These are simple wrapper functions that delegate to the namespaced versions
 */
// Modal functions
window.showCreateProjectModal = () => window.OrgAdmin.Projects.showCreate();
window.showAddInstructorModal = () => window.OrgAdmin.Instructors.showAdd();
window.showAddStudentModal = () => window.OrgAdmin.Students.showAdd();
window.showCreateTrackModal = () => window.OrgAdmin.Tracks.showCreate();
window.closeModal = (modalId) => window.OrgAdmin.Utils.closeModal(modalId);

// Project wizard functions
window.nextProjectStep = () => window.OrgAdmin.Projects.nextStep();
window.previousProjectStep = () => window.OrgAdmin.Projects.previousStep();
window.finalizeProjectCreation = () => window.OrgAdmin.Projects.submit();
window.regenerateAISuggestions = () => window.OrgAdmin.Projects.regenerateAI();
window.toggleAIChatPanel = () => window.OrgAdmin.Projects.toggleChat();
window.sendAIChatMessage = () => window.OrgAdmin.Projects.sendChatMessage();

// Target roles functions
window.deleteTargetRole = (roleName) => window.OrgAdmin.TargetRoles.delete(roleName);
window.resetTargetRolesToDefaults = () => window.OrgAdmin.TargetRoles.reset();

// Filter and load functions
window.filterProjects = () => window.OrgAdmin.Projects.load();
window.loadTracks = () => window.OrgAdmin.Tracks.load();
window.filterInstructors = () => window.OrgAdmin.Instructors.load();
window.filterStudents = () => window.OrgAdmin.Students.load();

// Auth function
window.logout = () => {
    localStorage.removeItem('authToken');
    window.location.href = '../index.html';
};

// Export for potential module-based usage
export { initializeDashboard };
export const OrgAdmin = window.OrgAdmin;
