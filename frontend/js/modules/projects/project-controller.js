/**
 * Project Controller
 *
 * BUSINESS CONTEXT:
 * Orchestrates project management workflows by coordinating between
 * API services, state management, and UI rendering. Acts as the central
 * coordinator for all project-related operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - MVC Controller pattern
 * - Event-driven architecture
 * - Separation of concerns
 * - Error handling and user notifications
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Orchestration only (no business logic or rendering)
 * - Open/Closed: Extensible through event system
 * - Dependency Inversion: Depends on abstractions (store, UI, API interfaces)
 * - Interface Segregation: Clean, focused public API
 *
 * @module projects/project-controller
 */
export class ProjectController {
    /**
     * Initialize the project controller
     *
     * @param {ProjectStore} projectStore - State management instance
     * @param {ProjectListRenderer} projectUI - UI rendering instance
     * @param {Object} projectAPI - API service instance (from org-admin-api.js)
     * @param {Object} notificationService - Notification service for user feedback
     */
    constructor(projectStore, projectUI, projectAPI, notificationService) {
        if (!projectStore) throw new Error('ProjectStore is required');
        if (!projectUI) throw new Error('ProjectListRenderer is required');
        if (!projectAPI) throw new Error('ProjectAPI is required');

        /**
         * Dependencies (injected)
         * @private
         */
        this.store = projectStore;
        this.ui = projectUI;
        this.api = projectAPI;
        this.notificationService = notificationService;

        /**
         * Current organization context
         * @private
         */
        this.organizationId = null;

        /**
         * Subscribe to state changes
         * @private
         */
        this.initializeStateSubscriptions();

        /**
         * Subscribe to UI events
         * @private
         */
        this.initializeUIEventListeners();
    }

    // ============================================================
    // INITIALIZATION
    // ============================================================

    /**
     * Initialize project controller for an organization
     *
     * BUSINESS LOGIC:
     * Sets up the controller for a specific organization and loads
     * initial project data. This should be called once when the
     * org admin dashboard loads.
     *
     * @param {string} organizationId - Organization UUID
     */
    async initialize(organizationId) {
        this.organizationId = organizationId;
        console.log('Project controller initialized for organization:', organizationId);

        // Load initial data
        await this.loadProjects();
    }

    /**
     * Subscribe to state changes and update UI accordingly
     *
     * TECHNICAL NOTE:
     * This creates a reactive binding between state and UI.
     * Whenever state changes, the UI automatically updates.
     *
     * @private
     */
    initializeStateSubscriptions() {
        this.store.subscribe((newState, oldState) => {
            // Re-render when projects list changes
            if (newState.projects !== oldState.projects) {
                if (newState.loading) {
                    this.ui.renderLoading();
                } else if (newState.error) {
                    this.ui.renderError(newState.error);
                } else {
                    const filteredProjects = this.store.getFilteredProjects();
                    this.ui.render(filteredProjects);
                }
            }

            // Update UI when filters change
            if (newState.filters !== oldState.filters) {
                const filteredProjects = this.store.getFilteredProjects();
                this.ui.render(filteredProjects);
            }

            // Show/hide loading indicators
            if (newState.loading !== oldState.loading) {
                if (newState.loading) {
                    this.ui.renderLoading();
                }
            }

            // Display errors
            if (newState.error !== oldState.error && newState.error) {
                this.ui.renderError(newState.error);
                if (this.notificationService) {
                    this.notificationService.error(newState.error);
                }
            }
        });
    }

    /**
     * Subscribe to UI events
     *
     * TECHNICAL NOTE:
     * This decouples the UI from the controller. The UI emits events,
     * and the controller handles them. This follows the Observer pattern.
     *
     * @private
     */
    initializeUIEventListeners() {
        // Project actions
        this.ui.on('project:view', (projectId) => this.viewProject(projectId));
        this.ui.on('project:edit', (projectId) => this.editProject(projectId));
        this.ui.on('project:delete', (projectId) => this.deleteProjectPrompt(projectId));
        this.ui.on('project:members', (projectId) => this.manageMembers(projectId));
        this.ui.on('project:create', () => this.showCreateProjectModal());
        this.ui.on('project:retry', () => this.loadProjects());
    }

    // ============================================================
    // PROJECT LOADING
    // ============================================================

    /**
     * Load projects for current organization
     *
     * BUSINESS LOGIC:
     * Fetches all projects for the organization with optional filters.
     * Updates state which triggers UI re-render through subscriptions.
     *
     * @param {Object} filters - Optional filters { status?, search? }
     * @returns {Promise<void>}
     */
    async loadProjects(filters = {}) {
        if (!this.organizationId) {
            console.error('Cannot load projects: organization ID not set');
            return;
        }

        try {
            // Set loading state
            this.store.setLoading(true);
            this.store.clearError();

            // Merge with current filters
            const currentFilters = this.store.getState().filters;
            const mergedFilters = { ...currentFilters, ...filters };

            // Fetch projects from API
            const projects = await this.api.fetchProjects(this.organizationId, mergedFilters);

            // Update state (this triggers UI update through subscription)
            this.store.setProjects(projects);
            this.store.setFilters(mergedFilters);

        } catch (error) {
            console.error('Error loading projects:', error);
            this.store.setError(error.message || 'Failed to load projects');
        } finally {
            this.store.setLoading(false);
        }
    }

    /**
     * Filter projects by status
     *
     * BUSINESS LOGIC:
     * Applies client-side filtering for instant feedback.
     * Can optionally refetch from server for server-side filtering.
     *
     * @param {string} status - Project status ('', 'active', 'draft', 'completed')
     * @param {boolean} refetch - Whether to refetch from server (default: false)
     */
    async filterByStatus(status, refetch = false) {
        if (refetch) {
            await this.loadProjects({ status });
        } else {
            this.store.setFilters({ status });
        }
    }

    /**
     * Search projects by keyword
     *
     * @param {string} searchTerm - Search keyword
     * @param {boolean} refetch - Whether to refetch from server (default: false)
     */
    async search(searchTerm, refetch = false) {
        if (refetch) {
            await this.loadProjects({ search: searchTerm });
        } else {
            this.store.setFilters({ search: searchTerm });
        }
    }

    // ============================================================
    // PROJECT CRUD OPERATIONS
    // ============================================================

    /**
     * View project details
     *
     * BUSINESS LOGIC:
     * Navigates to project detail view or opens modal with project info.
     *
     * @param {string} projectId - Project UUID
     */
    async viewProject(projectId) {
        try {
            const project = this.store.getProjectById(projectId);

            if (!project) {
                throw new Error('Project not found');
            }

            this.store.setCurrentProject(project);

            // Emit event for other parts of the application to handle
            this.emit('project:view', project);

            if (this.notificationService) {
                this.notificationService.info(`Viewing project: ${project.name}`);
            }

        } catch (error) {
            console.error('Error viewing project:', error);
            if (this.notificationService) {
                this.notificationService.error('Failed to view project');
            }
        }
    }

    /**
     * Show create project modal
     *
     * BUSINESS LOGIC:
     * Opens the project creation wizard/modal. The actual form handling
     * is done by a separate wizard component.
     */
    showCreateProjectModal() {
        // Emit event for modal management
        this.emit('project:showCreateModal');
    }

    /**
     * Create a new project
     *
     * BUSINESS LOGIC:
     * Creates a new project via API and refreshes the projects list.
     * Shows success/error notifications to user.
     *
     * @param {Object} projectData - Project creation data
     * @returns {Promise<Object>} Created project object
     */
    async createProject(projectData) {
        if (!this.organizationId) {
            throw new Error('Organization ID not set');
        }

        try {
            this.store.setLoading(true);

            // Call API to create project
            const newProject = await this.api.createProject(this.organizationId, projectData);

            // Refresh projects list
            await this.loadProjects();

            if (this.notificationService) {
                this.notificationService.success(`Project "${newProject.name}" created successfully`);
            }

            // Emit event
            this.emit('project:created', newProject);

            return newProject;

        } catch (error) {
            console.error('Error creating project:', error);
            this.store.setError(error.message || 'Failed to create project');

            if (this.notificationService) {
                this.notificationService.error('Failed to create project');
            }

            throw error;

        } finally {
            this.store.setLoading(false);
        }
    }

    /**
     * Edit existing project
     *
     * BUSINESS LOGIC:
     * Opens the project editing modal/form with pre-filled data.
     *
     * @param {string} projectId - Project UUID
     */
    async editProject(projectId) {
        try {
            const project = this.store.getProjectById(projectId);

            if (!project) {
                throw new Error('Project not found');
            }

            this.store.setCurrentProject(project);

            // Emit event for modal management
            this.emit('project:showEditModal', project);

        } catch (error) {
            console.error('Error editing project:', error);
            if (this.notificationService) {
                this.notificationService.error('Failed to load project for editing');
            }
        }
    }

    /**
     * Update existing project
     *
     * @param {string} projectId - Project UUID
     * @param {Object} updates - Project updates
     * @returns {Promise<Object>} Updated project object
     */
    async updateProject(projectId, updates) {
        try {
            this.store.setLoading(true);

            // Call API to update project
            const updatedProject = await this.api.updateProject(
                this.organizationId,
                projectId,
                updates
            );

            // Refresh projects list
            await this.loadProjects();

            if (this.notificationService) {
                this.notificationService.success('Project updated successfully');
            }

            // Emit event
            this.emit('project:updated', updatedProject);

            return updatedProject;

        } catch (error) {
            console.error('Error updating project:', error);
            this.store.setError(error.message || 'Failed to update project');

            if (this.notificationService) {
                this.notificationService.error('Failed to update project');
            }

            throw error;

        } finally {
            this.store.setLoading(false);
        }
    }

    /**
     * Show delete confirmation prompt
     *
     * BUSINESS LOGIC:
     * Shows a confirmation dialog before deleting a project.
     * This prevents accidental deletions.
     *
     * @param {string} projectId - Project UUID
     */
    deleteProjectPrompt(projectId) {
        const project = this.store.getProjectById(projectId);

        if (!project) {
            console.error('Project not found');
            return;
        }

        this.store.setCurrentProjectId(projectId);

        // Emit event for modal management
        this.emit('project:showDeleteModal', project);
    }

    /**
     * Delete project after confirmation
     *
     * @param {string} projectId - Project UUID
     * @returns {Promise<void>}
     */
    async deleteProject(projectId) {
        try {
            this.store.setLoading(true);

            // Call API to delete project
            await this.api.deleteProject(this.organizationId, projectId);

            // Refresh projects list
            await this.loadProjects();

            if (this.notificationService) {
                this.notificationService.success('Project deleted successfully');
            }

            // Emit event
            this.emit('project:deleted', projectId);

        } catch (error) {
            console.error('Error deleting project:', error);
            this.store.setError(error.message || 'Failed to delete project');

            if (this.notificationService) {
                this.notificationService.error('Failed to delete project');
            }

            throw error;

        } finally {
            this.store.setLoading(false);
        }
    }

    // ============================================================
    // MEMBER MANAGEMENT
    // ============================================================

    /**
     * Manage project members
     *
     * BUSINESS LOGIC:
     * Opens member management interface for adding/removing instructors
     * and students from a project.
     *
     * @param {string} projectId - Project UUID
     */
    async manageMembers(projectId) {
        try {
            const project = this.store.getProjectById(projectId);

            if (!project) {
                throw new Error('Project not found');
            }

            this.store.setCurrentProject(project);
            this.store.setLoading(true);

            // Fetch project members
            const members = await this.api.fetchMembers(this.organizationId, {
                project_id: projectId
            });

            this.store.setMembers(members);

            // Emit event for modal management
            this.emit('project:showMembersModal', { project, members });

        } catch (error) {
            console.error('Error loading project members:', error);
            if (this.notificationService) {
                this.notificationService.error('Failed to load project members');
            }
        } finally {
            this.store.setLoading(false);
        }
    }

    // ============================================================
    // EVENT EMITTER PATTERN
    // ============================================================

    /**
     * Event listeners registry
     * @private
     */
    eventListeners = new Map();

    /**
     * Register event listener
     *
     * @param {string} event - Event name
     * @param {Function} callback - Event handler
     * @returns {Function} Unsubscribe function
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);

        return () => {
            const callbacks = this.eventListeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) callbacks.splice(index, 1);
        };
    }

    /**
     * Emit event
     *
     * @private
     * @param {string} event - Event name
     * @param {...any} args - Event arguments
     */
    emit(event, ...args) {
        const callbacks = this.eventListeners.get(event) || [];
        callbacks.forEach(callback => {
            try {
                callback(...args);
            } catch (error) {
                console.error(`Error in event handler for ${event}:`, error);
            }
        });
    }

    // ============================================================
    // CLEANUP
    // ============================================================

    /**
     * Cleanup and destroy controller
     *
     * BUSINESS LOGIC:
     * Cleans up subscriptions and resets state when navigating away
     * from the projects page.
     */
    destroy() {
        this.store.reset();
        this.ui.clear();
        this.eventListeners.clear();
        console.log('Project controller destroyed');
    }
}
