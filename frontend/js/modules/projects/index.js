/**
 * Projects Module - Public API
 *
 * BUSINESS CONTEXT:
 * Provides a clean, simple API for managing projects in the organization
 * admin dashboard. Encapsulates all complexity and provides a single
 * entry point for project management functionality.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Factory pattern for module initialization
 * - Dependency injection for testability
 * - Clean public API hiding implementation details
 * - ES6 modules for proper encapsulation
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Module composition and initialization only
 * - Open/Closed: Extensible without modifying existing code
 * - Dependency Inversion: Depends on abstractions, not implementations
 * - Interface Segregation: Clean, minimal public API
 *
 * @module projects
 */
import { ProjectStore } from './state/project-store.js';
import { ProjectListRenderer } from './ui/project-list-renderer.js';
import { ProjectController } from './project-controller.js';

/**
 * Create and initialize projects module
 *
 * BUSINESS LOGIC:
 * Sets up all dependencies and returns a simple API for project management.
 * This factory function handles all the complexity of wiring up dependencies.
 *
 * USAGE:
 * import { createProjectsModule } from './modules/projects/index.js';
 *
 * const projects = createProjectsModule({
 *   containerSelector: '#projects-container',
 *   projectAPI: orgAdminAPI,
 *   notificationService: notifications
 * });
 *
 * projects.initialize('org-123');
 *
 * @param {Object} config - Configuration object
 * @param {string} config.containerSelector - CSS selector for projects container
 * @param {Object} config.projectAPI - API service instance
 * @param {Object} [config.notificationService] - Optional notification service
 * @returns {Object} Projects module public API
 */
export function createProjectsModule(config) {
    // Validate required configuration
    if (!config || !config.containerSelector) {
        throw new Error('ProjectsModule: containerSelector is required');
    }

    if (!config.projectAPI) {
        throw new Error('ProjectsModule: projectAPI is required');
    }

    // Initialize dependencies with dependency injection
    const projectStore = new ProjectStore();
    const projectUI = new ProjectListRenderer(config.containerSelector);
    const projectController = new ProjectController(
        projectStore,
        projectUI,
        config.projectAPI,
        config.notificationService || null
    );

    // Return public API
    return {
        /**
         * Initialize projects module for an organization
         *
         * @param {string} organizationId - Organization UUID
         * @returns {Promise<void>}
         */
        initialize: (organizationId) => projectController.initialize(organizationId),

        /**
         * Load projects with optional filters
         *
         * @param {Object} [filters] - Optional filters { status?, search? }
         * @returns {Promise<void>}
         */
        loadProjects: (filters) => projectController.loadProjects(filters),

        /**
         * Filter projects by status
         *
         * @param {string} status - Project status
         * @param {boolean} [refetch=false] - Whether to refetch from server
         * @returns {Promise<void>}
         */
        filterByStatus: (status, refetch) => projectController.filterByStatus(status, refetch),

        /**
         * Search projects by keyword
         *
         * @param {string} searchTerm - Search keyword
         * @param {boolean} [refetch=false] - Whether to refetch from server
         * @returns {Promise<void>}
         */
        search: (searchTerm, refetch) => projectController.search(searchTerm, refetch),

        /**
         * Create a new project
         *
         * @param {Object} projectData - Project creation data
         * @returns {Promise<Object>} Created project
         */
        createProject: (projectData) => projectController.createProject(projectData),

        /**
         * Update existing project
         *
         * @param {string} projectId - Project UUID
         * @param {Object} updates - Project updates
         * @returns {Promise<Object>} Updated project
         */
        updateProject: (projectId, updates) => projectController.updateProject(projectId, updates),

        /**
         * Delete project
         *
         * @param {string} projectId - Project UUID
         * @returns {Promise<void>}
         */
        deleteProject: (projectId) => projectController.deleteProject(projectId),

        /**
         * Subscribe to project events
         *
         * @param {string} event - Event name
         * @param {Function} callback - Event handler
         * @returns {Function} Unsubscribe function
         */
        on: (event, callback) => projectController.on(event, callback),

        /**
         * Get current state snapshot
         *
         * @returns {Object} Current state
         */
        getState: () => projectStore.getState(),

        /**
         * Cleanup and destroy module
         *
         * @returns {void}
         */
        destroy: () => projectController.destroy()
    };
}

/**
 * Project Module Factory (Alternative API)
 *
 * Provides a class-based API for those who prefer instantiation syntax.
 *
 * USAGE:
 * import { ProjectsModule } from './modules/projects/index.js';
 *
 * const projects = new ProjectsModule({
 *   containerSelector: '#projects-container',
 *   projectAPI: orgAdminAPI,
 *   notificationService: notifications
 * });
 *
 * await projects.initialize('org-123');
 */
export class ProjectsModule {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {Object} config - Configuration options
     */
    constructor(config) {
        const module = createProjectsModule(config);

        // Expose all public methods
        this.initialize = module.initialize;
        this.loadProjects = module.loadProjects;
        this.filterByStatus = module.filterByStatus;
        this.search = module.search;
        this.createProject = module.createProject;
        this.updateProject = module.updateProject;
        this.deleteProject = module.deleteProject;
        this.on = module.on;
        this.getState = module.getState;
        this.destroy = module.destroy;
    }
}

// Export individual components for advanced usage
export { ProjectStore } from './state/project-store.js';
export { ProjectListRenderer } from './ui/project-list-renderer.js';
export { ProjectController } from './project-controller.js';
export { ProjectAPIService } from './services/project-api-service.js';

// Export data models
export {
    createProject,
    validateProject,
    updateProject,
    isProjectActive,
    isProjectAcceptingEnrollments,
    isProjectFull,
    getProjectCompletion,
    getProjectDaysRemaining,
    generateSlug,
    createProjectFromAPI,
    ProjectStatus,
    ProjectDifficulty
} from './models/project.js';

export {
    createMember,
    validateMember,
    updateMember,
    isInstructor,
    isStudent,
    isMemberActive,
    hasMemberCompleted,
    getMemberFullName,
    getMemberInitials,
    groupMembersByRole,
    filterActiveMembers,
    sortMembersByName,
    sortMembersByProgress,
    calculateAverageProgress,
    getMembersAtRisk,
    createMemberFromAPI,
    MemberRole,
    MemberStatus
} from './models/project-member.js';

// Export utility functions
export * from './utils/formatting.js';

// Export Project Creation Wizard
export {
    createProjectWizard,
    ProjectWizard,
    WizardState,
    WizardController
} from './wizard/index.js';

// Export wizard utilities
export {
    AUDIENCE_TRACK_MAPPING,
    getTrackConfigForAudience,
    hasAudienceMapping,
    getAllAudienceIdentifiers,
    getAudiencesByDifficulty,
    searchAudiencesBySkill,
    mapAudiencesToConfigs
} from './wizard/audience-mapping.js';

export {
    generateTrackName,
    generateTrackSlug,
    generateTrackDescription,
    validateAudienceIdentifier,
    extractProfession,
    extractPrefixes,
    hasProfessionRule,
    addProfessionRule
} from './wizard/track-generator.js';

export {
    showTrackConfirmationDialog,
    showTrackApprovalSuccess,
    showTrackCancellationMessage,
    validateTracksForConfirmation,
    formatTracksForDisplay
} from './wizard/track-confirmation-dialog.js';

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic Usage (Function-based)
 * ==========================================
 * import { createProjectsModule } from './modules/projects/index.js';
 * import { orgAdminAPI } from './modules/org-admin-api.js';
 * import { notificationService } from './services/notifications.js';
 *
 * const projects = createProjectsModule({
 *   containerSelector: '#projects-container',
 *   projectAPI: orgAdminAPI,
 *   notificationService: notificationService
 * });
 *
 * // Initialize for organization
 * await projects.initialize('org-123');
 *
 * // Load projects with filters
 * await projects.loadProjects({ status: 'active' });
 *
 * // Search projects
 * await projects.search('python');
 *
 * // Listen to events
 * projects.on('project:created', (project) => {
 *   console.log('New project created:', project);
 * });
 *
 * // Create project
 * await projects.createProject({
 *   name: 'Python Bootcamp',
 *   description: 'Learn Python basics',
 *   duration_weeks: 12
 * });
 *
 * // Cleanup
 * projects.destroy();
 *
 *
 * Example 2: Class-based Usage
 * =============================
 * import { ProjectsModule } from './modules/projects/index.js';
 *
 * const projects = new ProjectsModule({
 *   containerSelector: '#projects-container',
 *   projectAPI: orgAdminAPI
 * });
 *
 * await projects.initialize('org-123');
 *
 *
 * Example 3: Advanced Usage (Direct Component Access)
 * ====================================================
 * import { ProjectStore, ProjectController } from './modules/projects/index.js';
 *
 * // Create custom store
 * const store = new ProjectStore();
 *
 * // Subscribe to specific state changes
 * store.subscribe((newState, oldState) => {
 *   if (newState.projects.length !== oldState.projects.length) {
 *     console.log('Project count changed');
 *   }
 * });
 *
 *
 * Example 4: Testing
 * ===================
 * import { createProjectsModule } from './modules/projects/index.js';
 *
 * // Mock dependencies
 * const mockAPI = {
 *   fetchProjects: jest.fn().mockResolvedValue([...]),
 *   createProject: jest.fn().mockResolvedValue({...})
 * };
 *
 * const projects = createProjectsModule({
 *   containerSelector: document.createElement('div'),
 *   projectAPI: mockAPI
 * });
 *
 * await projects.loadProjects();
 * expect(mockAPI.fetchProjects).toHaveBeenCalled();
 */