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
import * as Courses from './modules/org-admin-courses.js';
import * as Instructors from './modules/org-admin-instructors.js';
import * as Students from './modules/org-admin-students.js';
// import * as Tracks from './modules/org-admin-tracks.js'; // OLD: Uses outdated schema
import * as Tracks from './modules/org-admin/tracks-crud.js'; // NEW: TDD implementation matching course_creator.tracks
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

// Import activity-based token manager
import { activityTokenManager } from './modules/activity-token-manager.js';

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
        nextProjectStep: Projects.nextProjectStep,
        previousProjectStep: Projects.previousProjectStep,
        resetProjectWizard: Projects.resetProjectWizard,
        toggleWizardProgress: Projects.toggleWizardProgress,
        regenerateAI: Projects.regenerateAISuggestions,
        toggleChat: Projects.toggleAIChatPanel,
        sendChatMessage: Projects.sendAIChatMessage,
        // Sub-project/Locations management (Step 2)
        showAddLocationForm: Projects.showAddLocationForm,
        cancelLocationForm: Projects.cancelLocationForm,
        saveLocation: Projects.saveLocation,
        removeLocationFromWizard: Projects.removeLocationFromWizard,
        // Track management (Step 4)
        populateTrackReviewList: Projects.populateTrackReviewList,
        openTrackManagement: Projects.openTrackManagement,
        closeTrackManagement: Projects.closeTrackManagement,
        switchTrackTab: Projects.switchTrackTab,
        saveTrackChanges: Projects.saveTrackChanges,
        addInstructorToTrack: Projects.addInstructorToTrack,
        removeInstructorFromTrack: Projects.removeInstructorFromTrack,
        createCourseForTrack: Projects.createCourseForTrack,
        removeCourseFromTrack: Projects.removeCourseFromTrack,
        addStudentToTrack: Projects.addStudentToTrack,
        removeStudentFromTrack: Projects.removeStudentFromTrack,
        // Track management from main list views
        manageProjectTracks: Projects.manageProjectTracks,
        // Project creation finalization (Step 4 - Create button)
        finalizeProjectCreation: Projects.finalizeProjectCreation,
        // Project summary toggle
        toggleProjectSummary: Projects.toggleProjectSummary
    },

    // Courses module
    Courses: {
        showCreateCourseModal: Courses.showCreateCourseModal,
        closeCourseModal: Courses.closeCourseModal,
        submitCourseForm: Courses.submitCourseForm
    },

    // Instructors module
    Instructors: {
        load: Instructors.loadInstructorsData,
        showAdd: Instructors.showAddInstructorModal,
        submitAdd: Instructors.submitAddInstructor,
        view: Instructors.viewInstructor,
        assign: Instructors.assignInstructor,
        assignInstructor: Instructors.assignInstructor,
        closeAssignmentModal: Instructors.closeAssignmentModal,
        onTrackSelectionChange: Instructors.onTrackSelectionChange,
        saveAssignments: Instructors.saveAssignments,
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
        showCustomForm: Tracks.showCustomTrackForm,
        submit: Tracks.submitTrack,
        submitCustom: Tracks.submitCustomTrack,
        viewTrackDetails: Tracks.viewTrackDetails,
        editFromDetails: Tracks.editTrackFromDetails,
        editTrack: Tracks.editTrack,
        deleteTrackPrompt: Tracks.deleteTrackPrompt,
        confirmDelete: Tracks.confirmDeleteTrack,
        manageTrack: Tracks.manageTrack
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

        // Start activity-based token refresh
        // This prevents logout during active use (30 min inactivity timeout)
        activityTokenManager.start();
        console.log('🔄 Activity-based token refresh enabled');

        // Attach course form event listeners
        const generateCourseForm = document.getElementById('generateCourseForm');
        if (generateCourseForm) {
            generateCourseForm.addEventListener('submit', window.submitGenerateCourse);
        }

        const editSyllabusForm = document.getElementById('editSyllabusForm');
        if (editSyllabusForm) {
            editSyllabusForm.addEventListener('submit', window.submitSyllabusEdits);
        }

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
window.showCreateProjectModal = () => {
    console.log('🔵 showCreateProjectModal wrapper called');
    console.log('🔵 window.OrgAdmin:', window.OrgAdmin);
    console.log('🔵 window.OrgAdmin.Projects:', window.OrgAdmin.Projects);
    console.log('🔵 window.OrgAdmin.Projects.showCreate:', window.OrgAdmin.Projects.showCreate);
    window.OrgAdmin.Projects.showCreate();
};
window.showAddInstructorModal = () => window.OrgAdmin.Instructors.showAdd();
window.showAddStudentModal = () => window.OrgAdmin.Students.showAdd();
window.showCreateTrackModal = () => window.OrgAdmin.Tracks.showCreate();
window.showCustomTrackForm = () => window.OrgAdmin.Tracks.showCustomForm();
window.showGenerateCourseModal = () => window.OrgAdmin.Utils.openModal('generateCourseModal');
window.showEditSyllabusModal = () => window.OrgAdmin.Utils.openModal('editSyllabusModal');
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

// Course generation functions (real backend implementation)
window.submitGenerateCourse = async (event) => {
    event.preventDefault();
    console.log('Course generation requested');

    // Get form values
    const title = document.getElementById('generateCourseTitle').value;
    const description = document.getElementById('generateCourseDescription').value;
    const category = document.getElementById('generateCourseCategory').value;
    const difficulty = document.getElementById('generateCourseDifficulty').value;

    // Get current user and org from localStorage
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const urlParams = new URLSearchParams(window.location.search);
    const orgId = urlParams.get('org_id');

    // Show loading state
    const statusDiv = document.getElementById('courseGenerationStatus');
    if (statusDiv) {
        statusDiv.style.display = 'flex';
    }

    try {
        // Call backend API to create course (course-management service on port 8004)
        const response = await fetch('https://localhost:8004/courses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
                title: title,
                description: description,
                category: category,
                difficulty_level: difficulty,
                estimated_duration: 4,
                duration_unit: 'weeks',
                price: 0.0,
                tags: [],
                organization_id: orgId,
                project_id: null,
                track_id: null
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to create course: ${response.statusText}`);
        }

        const createdCourse = await response.json();
        console.log('Course created:', createdCourse);

        // Hide loading
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }

        // Show success message
        const successDiv = document.getElementById('generateCourseSuccess');
        if (successDiv) {
            successDiv.style.display = 'block';

            // Auto-close modal and refresh after short delay
            setTimeout(() => {
                successDiv.style.display = 'none';
                window.OrgAdmin.Utils.closeModal('generateCourseModal');
                window.OrgAdmin.Utils.showNotification('Course generated successfully!', 'success');

                // Refresh the courses list
                if (window.OrgAdmin && window.OrgAdmin.Core) {
                    window.OrgAdmin.Core.loadTab('courses');
                }
            }, 2000);
        }

    } catch (error) {
        console.error('Error generating course:', error);
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
        window.OrgAdmin.Utils.showNotification(`Failed to generate course: ${error.message}`, 'error');
    }
};

window.submitSyllabusEdits = async (event) => {
    event.preventDefault();
    console.log('Syllabus edits submitted');

    // Get form values
    const title = document.getElementById('editSyllabusTitle').value;
    const courseId = document.getElementById('editSyllabusModal').dataset.courseId;

    if (!courseId) {
        window.OrgAdmin.Utils.showNotification('No course selected for editing', 'error');
        return;
    }

    try {
        // Call backend API to update course
        const response = await fetch(`https://localhost:8001/courses/${courseId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
                title: title
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to update course: ${response.statusText}`);
        }

        const updatedCourse = await response.json();
        console.log('Course updated:', updatedCourse);

        // Show success
        const successDiv = document.getElementById('saveSyllabusSuccess');
        if (successDiv) {
            successDiv.style.display = 'block';
            setTimeout(() => {
                successDiv.style.display = 'none';
                window.OrgAdmin.Utils.closeModal('editSyllabusModal');
                window.OrgAdmin.Utils.showNotification('Syllabus updated successfully', 'success');

                // Refresh the courses list
                if (window.OrgAdmin && window.OrgAdmin.Core) {
                    window.OrgAdmin.Core.loadTab('courses');
                }
            }, 1500);
        }

    } catch (error) {
        console.error('Error updating course:', error);
        window.OrgAdmin.Utils.showNotification(`Failed to update course: ${error.message}`, 'error');
    }
};

// Course viewing and editing functions
window.viewCourseDetails = async (courseId, courseData) => {
    console.log('Viewing course:', courseId, courseData);

    try {
        // Parse course data if it's a string
        const course = typeof courseData === 'string' ? JSON.parse(courseData) : courseData;

        // Populate course details modal
        const modalTitle = document.getElementById('courseDetailsModalTitle');
        const modalContent = document.getElementById('courseDetailsContent');

        if (modalTitle && modalContent) {
            modalTitle.textContent = course.title || 'Course Details';

            // Populate modal with course information
            modalContent.innerHTML = `
                <div style="margin-bottom: 2rem;">
                    <h3 style="margin-top: 0;">Course Information</h3>
                    <p><strong>Description:</strong> ${window.OrgAdmin.Utils.escapeHtml(course.description)}</p>
                    <p><strong>Category:</strong> ${course.category || 'Uncategorized'}</p>
                    <p><strong>Difficulty:</strong> ${course.difficulty_level}</p>
                    <p><strong>Duration:</strong> ${course.estimated_duration} ${course.duration_unit}</p>
                    <p><strong>Status:</strong> ${course.is_published ? 'Published' : 'Draft'}</p>
                </div>

                <div id="courseSyllabusContent" style="margin-bottom: 2rem;">
                    <h3>Course Syllabus</h3>
                    <div class="course-module" style="padding: 1rem; border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 1rem;">
                        <h4>Module 1: Introduction</h4>
                        <p>Introduction to the course topics and learning objectives.</p>
                    </div>
                    <div class="course-module" style="padding: 1rem; border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 1rem;">
                        <h4>Module 2: Core Concepts</h4>
                        <p>Deep dive into core concepts and fundamental principles.</p>
                    </div>
                    <div class="course-module" style="padding: 1rem; border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 1rem;">
                        <h4>Module 3: Practical Applications</h4>
                        <p>Hands-on exercises and real-world applications.</p>
                    </div>
                </div>

                <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                    <button class="btn btn-secondary" onclick="closeModal('courseDetailsModal')">Close</button>
                    <button class="btn btn-primary" onclick="editCourse('${course.id}', '${window.OrgAdmin.Utils.escapeHtml(course.title)}'); closeModal('courseDetailsModal');">Edit Course</button>
                </div>
            `;
        }

        // Open the modal
        window.OrgAdmin.Utils.openModal('courseDetailsModal');

    } catch (error) {
        console.error('Error viewing course details:', error);
        window.OrgAdmin.Utils.showNotification('Failed to load course details', 'error');
    }
};

window.editCourse = (courseId, courseTitle) => {
    console.log('Editing course:', courseId, courseTitle);

    // Populate edit modal
    const editModal = document.getElementById('editSyllabusModal');
    const titleInput = document.getElementById('editSyllabusTitle');

    if (editModal && titleInput) {
        // Store course ID in modal for later use
        editModal.dataset.courseId = courseId;

        // Populate fields
        titleInput.value = courseTitle;

        // Open modal
        window.OrgAdmin.Utils.openModal('editSyllabusModal');
    } else {
        window.OrgAdmin.Utils.showNotification('Edit form not found', 'error');
    }
};

// Custom track submission handler (delegates to module)
window.submitCustomTrack = (event) => window.OrgAdmin.Tracks.submitCustom(event);

// Auth function
window.logout = () => {
    localStorage.removeItem('authToken');
    window.location.href = '../index.html';
};

// Export for potential module-based usage
export { initializeDashboard };
export const OrgAdmin = window.OrgAdmin;
