/**
 * Project Creation Wizard - Public API
 *
 * BUSINESS CONTEXT:
 * Provides a clean, simple API for the multi-step project creation wizard.
 * Encapsulates all wizard complexity and provides a single entry point for
 * creating new projects with optional track generation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Factory pattern for module initialization
 * - Dependency injection for testability
 * - Clean public API hiding implementation details
 * - Event-driven architecture for loose coupling
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Module composition and initialization only
 * - Open/Closed: Extensible without modifying existing code
 * - Dependency Inversion: Depends on abstractions, not implementations
 * - Interface Segregation: Clean, minimal public API
 *
 * @module projects/wizard
 */
import { WizardState } from './wizard-state.js';
import { WizardController } from './wizard-controller.js';

/**
 * Create and initialize project creation wizard
 *
 * BUSINESS LOGIC:
 * Sets up all wizard dependencies and returns a simple API for project creation.
 * This factory function handles all the complexity of wiring up dependencies.
 *
 * USAGE:
 * import { createProjectWizard } from './modules/projects/wizard/index.js';
 *
 * const wizard = createProjectWizard({
 *   projectAPI: orgAdminAPI,
 *   openModal: openModal,
 *   closeModal: closeModal,
 *   showNotification: showNotification,
 *   aiAssistant: aiAssistantService
 * });
 *
 * wizard.open('org-123');
 *
 * @param {Object} dependencies - Wizard dependencies
 * @param {Object} dependencies.projectAPI - Project API service
 * @param {Function} dependencies.openModal - Modal opening function
 * @param {Function} dependencies.closeModal - Modal closing function
 * @param {Function} dependencies.showNotification - Notification function
 * @param {Object} [dependencies.aiAssistant] - Optional AI assistant service
 * @returns {Object} Wizard public API
 */
export function createProjectWizard(dependencies) {
    // Validate required dependencies
    if (!dependencies || !dependencies.projectAPI) {
        throw new Error('ProjectWizard: projectAPI dependency is required');
    }

    // Initialize components
    const wizardState = new WizardState();
    const wizardController = new WizardController(wizardState, dependencies);

    // Return public API
    return {
        /**
         * Open wizard for new project creation
         *
         * @param {string} organizationId - Organization UUID
         * @returns {void}
         */
        open: (organizationId) => wizardController.openWizard(organizationId),

        /**
         * Close wizard
         *
         * @returns {void}
         */
        close: () => wizardController.closeWizard(),

        /**
         * Navigate to next step
         *
         * @returns {Promise<boolean>} True if navigation successful
         */
        nextStep: () => wizardController.nextStep(),

        /**
         * Navigate to previous step
         *
         * @returns {boolean} True if navigation successful
         */
        previousStep: () => wizardController.previousStep(),

        /**
         * Navigate to specific step
         *
         * @param {number} stepNumber - Step number (1, 2, or 3)
         * @returns {void}
         */
        goToStep: (stepNumber) => wizardController.goToStep(stepNumber),

        /**
         * Submit project creation
         *
         * @returns {Promise<boolean>} True if submission successful
         */
        submit: () => wizardController.submitProject(),

        /**
         * Get current wizard state
         *
         * @returns {Object} Current state snapshot
         */
        getState: () => wizardState.getState(),

        /**
         * Subscribe to wizard events
         *
         * AVAILABLE EVENTS:
         * - 'project:created' - Fired when project is successfully created
         *
         * @param {string} event - Event name
         * @param {Function} callback - Event handler
         * @returns {Function} Unsubscribe function
         *
         * @example
         * const unsubscribe = wizard.on('project:created', (event) => {
         *   console.log('Project created:', event.detail);
         * });
         */
        on: (event, callback) => {
            document.addEventListener(event, callback);
            return () => document.removeEventListener(event, callback);
        },

        /**
         * Cleanup and destroy wizard
         *
         * @returns {void}
         */
        destroy: () => wizardController.destroy()
    };
}

/**
 * Project Wizard Factory (Alternative API)
 *
 * Provides a class-based API for those who prefer instantiation syntax.
 *
 * USAGE:
 * import { ProjectWizard } from './modules/projects/wizard/index.js';
 *
 * const wizard = new ProjectWizard({
 *   projectAPI: orgAdminAPI,
 *   openModal: openModal,
 *   closeModal: closeModal,
 *   showNotification: showNotification
 * });
 *
 * wizard.open('org-123');
 */
export class ProjectWizard {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {*} dependencies - Dependencies parameter
     */
    constructor(dependencies) {
        const wizard = createProjectWizard(dependencies);

        // Expose all public methods
        this.open = wizard.open;
        this.close = wizard.close;
        this.nextStep = wizard.nextStep;
        this.previousStep = wizard.previousStep;
        this.goToStep = wizard.goToStep;
        this.submit = wizard.submit;
        this.getState = wizard.getState;
        this.on = wizard.on;
        this.destroy = wizard.destroy;
    }
}

// Export individual components for advanced usage
export { WizardState } from './wizard-state.js';
export { WizardController } from './wizard-controller.js';

// Export wizard utilities
export {
    AUDIENCE_TRACK_MAPPING,
    getTrackConfigForAudience,
    hasAudienceMapping,
    getAllAudienceIdentifiers,
    getAudiencesByDifficulty,
    searchAudiencesBySkill,
    mapAudiencesToConfigs
} from './audience-mapping.js';

export {
    generateTrackName,
    generateTrackSlug,
    generateTrackDescription,
    validateAudienceIdentifier,
    extractProfession,
    extractPrefixes,
    hasProfessionRule,
    addProfessionRule
} from './track-generator.js';

export {
    showTrackConfirmationDialog,
    showTrackApprovalSuccess,
    showTrackCancellationMessage,
    validateTracksForConfirmation,
    formatTracksForDisplay
} from './track-confirmation-dialog.js';

// Export Track Management Module
export {
    createTrackManagement,
    TrackManagement,
    TrackManagementState,
    TrackManagementController
} from './track-management/index.js';

export {
    renderTrackInfoTab,
    renderTrackSummary,
    renderTrackStats
} from './track-management/tabs/info-tab.js';

export { renderTrackInstructorsTab } from './track-management/tabs/instructors-tab.js';
export { renderTrackCoursesTab } from './track-management/tabs/courses-tab.js';
export { renderTrackStudentsTab } from './track-management/tabs/students-tab.js';

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic Usage (Function-based)
 * =========================================
 * import { createProjectWizard } from './modules/projects/wizard/index.js';
 * import { orgAdminAPI } from './modules/org-admin-api.js';
 *
 * const wizard = createProjectWizard({
 *   projectAPI: orgAdminAPI,
 *   openModal: (id) => document.getElementById(id).style.display = 'block',
 *   closeModal: (id) => document.getElementById(id).style.display = 'none',
 *   showNotification: (msg, type) => console.log(`[${type}] ${msg}`)
 * });
 *
 * // Open wizard
 * wizard.open('org-123');
 *
 * // Listen to project creation
 * wizard.on('project:created', (event) => {
 *   console.log('New project:', event.detail);
 *   refreshProjectsList();
 * });
 *
 *
 * Example 2: Class-based Usage
 * ==============================
 * import { ProjectWizard } from './modules/projects/wizard/index.js';
 *
 * const wizard = new ProjectWizard({
 *   projectAPI: orgAdminAPI,
 *   openModal: openModal,
 *   closeModal: closeModal,
 *   showNotification: showNotification
 * });
 *
 * wizard.open('org-123');
 *
 *
 * Example 3: With AI Assistant
 * ==============================
 * import { createProjectWizard } from './modules/projects/wizard/index.js';
 * import { aiAssistantService } from './modules/ai-assistant.js';
 *
 * const wizard = createProjectWizard({
 *   projectAPI: orgAdminAPI,
 *   openModal: openModal,
 *   closeModal: closeModal,
 *   showNotification: showNotification,
 *   aiAssistant: aiAssistantService
 * });
 *
 * // AI suggestions will be automatically generated in Step 2
 * wizard.open('org-123');
 *
 *
 * Example 4: Manual Step Control
 * ================================
 * import { createProjectWizard } from './modules/projects/wizard/index.js';
 *
 * const wizard = createProjectWizard(dependencies);
 *
 * // Open wizard
 * wizard.open('org-123');
 *
 * // Programmatically navigate
 * await wizard.nextStep();           // Step 1 → 2
 * await wizard.nextStep();           // Step 2 → 3
 *
 * wizard.previousStep();             // Step 3 → 2
 * wizard.goToStep(1);               // Jump to Step 1
 *
 * // Submit
 * await wizard.submit();
 *
 *
 * Example 5: Access State
 * ========================
 * import { createProjectWizard } from './modules/projects/wizard/index.js';
 *
 * const wizard = createProjectWizard(dependencies);
 * wizard.open('org-123');
 *
 * // Get current state
 * const state = wizard.getState();
 * console.log('Current step:', state.currentStep);
 * console.log('Project name:', state.projectName);
 * console.log('Target roles:', state.targetRoles);
 *
 *
 * Example 6: Advanced - Direct Component Access
 * ===============================================
 * import { WizardState, WizardController } from './modules/projects/wizard/index.js';
 *
 * // Create custom state
 * const state = new WizardState();
 *
 * // Subscribe to specific state changes
 * state.subscribe((newState, oldState) => {
 *   if (newState.currentStep !== oldState.currentStep) {
 *     console.log(`Step changed: ${oldState.currentStep} → ${newState.currentStep}`);
 *   }
 * });
 *
 * // Create custom controller
 * const controller = new WizardController(state, dependencies);
 *
 *
 * Example 7: Track Generation Utilities
 * =======================================
 * import {
 *   generateTrackName,
 *   getTrackConfigForAudience,
 *   mapAudiencesToConfigs
 * } from './modules/projects/wizard/index.js';
 *
 * // Generate track name using NLP
 * const trackName = generateTrackName('application_developers');
 * // Returns: "Application Development"
 *
 * // Get predefined track config
 * const config = getTrackConfigForAudience('data_scientists');
 * // Returns: { name, description, difficulty, skills }
 *
 * // Map multiple audiences to track configs
 * const audiences = ['application_developers', 'qa_engineers'];
 * const trackConfigs = mapAudiencesToConfigs(audiences);
 * // Returns array of track configurations
 *
 *
 * Example 8: Testing
 * ===================
 * import { createProjectWizard } from './modules/projects/wizard/index.js';
 *
 * // Mock dependencies
 * const mockAPI = {
 *   createProject: jest.fn().mockResolvedValue({ id: 'project-123' }),
 *   createTrack: jest.fn().mockResolvedValue({ id: 'track-123' })
 * };
 *
 * const wizard = createProjectWizard({
 *   projectAPI: mockAPI,
 *   openModal: jest.fn(),
 *   closeModal: jest.fn(),
 *   showNotification: jest.fn()
 * });
 *
 * wizard.open('org-123');
 * await wizard.submit();
 *
 * expect(mockAPI.createProject).toHaveBeenCalled();
 */