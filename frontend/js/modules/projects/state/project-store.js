/**
 * Project State Store
 *
 * BUSINESS CONTEXT:
 * Manages centralized state for project data and provides reactive updates
 * to all subscribed components. This ensures a single source of truth for
 * project information across the organization admin dashboard.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Observer pattern for reactive state updates
 * - Immutable state updates
 * - Type-safe state structure
 * - Subscription-based notifications
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: State management only
 * - Open/Closed: Extensible through subscriptions
 * - Interface Segregation: Clean subscription API
 *
 * @module projects/state/project-store
 */
export class ProjectStore {
    /**
     * Initialize the project store with default state
     */
    constructor() {
        /**
         * Internal state object
         * @private
         */
        this.state = {
            projects: [],
            currentProject: null,
            currentProjectId: null,
            filters: {
                status: '',
                search: ''
            },
            loading: false,
            error: null,
            members: [],
            stats: {
                total: 0,
                active: 0,
                draft: 0,
                completed: 0
            }
        };

        /**
         * Array of subscriber callback functions
         * @private
         */
        this.subscribers = [];
    }

    /**
     * Update state with new values
     *
     * TECHNICAL NOTE:
     * Uses object spread to ensure immutability. This is critical for
     * detecting changes in React-like frameworks and preventing
     * accidental state mutations.
     *
     * @param {Object} updates - Partial state updates to apply
     */
    setState(updates) {
        const oldState = { ...this.state };
        this.state = {
            ...this.state,
            ...updates,
            // Deep merge for nested objects
            filters: updates.filters ? { ...this.state.filters, ...updates.filters } : this.state.filters,
            stats: updates.stats ? { ...this.state.stats, ...updates.stats } : this.state.stats
        };
        this.notify(oldState, this.state);
    }

    /**
     * Get current state snapshot
     *
     * TECHNICAL NOTE:
     * Returns a shallow copy to prevent external mutations of internal state.
     * Use this for reading state, not modifying it.
     *
     * @returns {Object} Current state snapshot
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Subscribe to state changes
     *
     * BUSINESS LOGIC:
     * Allows UI components to react to state changes without polling.
     * This is more efficient than manually checking for updates.
     *
     * @param {Function} callback - Function to call on state change (newState, oldState) => void
     * @returns {Function} Unsubscribe function
     *
     * @example
     * const unsubscribe = store.subscribe((newState, oldState) => {
     *   if (newState.projects !== oldState.projects) {
     *     updateUI(newState.projects);
     *   }
     * });
     * // Later: unsubscribe();
     */
    subscribe(callback) {
        this.subscribers.push(callback);

        // Return unsubscribe function (closure pattern)
        return () => {
            const index = this.subscribers.indexOf(callback);
            if (index > -1) {
                this.subscribers.splice(index, 1);
            }
        };
    }

    /**
     * Notify all subscribers of state change
     *
     * @private
     * @param {Object} oldState - Previous state
     * @param {Object} newState - New state
     */
    notify(oldState, newState) {
        this.subscribers.forEach(callback => {
            try {
                callback(newState, oldState);
            } catch (error) {
                console.error('Error in state subscriber:', error);
            }
        });
    }

    // ============================================================
    // ACTION METHODS - Semantic state update methods
    // ============================================================

    /**
     * Set projects list
     *
     * BUSINESS LOGIC:
     * Updates the projects list and clears any previous errors.
     * Also calculates statistics for dashboard display.
     *
     * @param {Array<Project>} projects - Array of project objects
     */
    setProjects(projects) {
        const stats = this.calculateStats(projects);
        this.setState({
            projects,
            stats,
            error: null
        });
    }

    /**
     * Set current project (for detail view)
     *
     * @param {Project} project - Project object
     */
    setCurrentProject(project) {
        this.setState({
            currentProject: project,
            currentProjectId: project?.id || null
        });
    }

    /**
     * Set current project ID
     *
     * @param {string} projectId - Project UUID
     */
    setCurrentProjectId(projectId) {
        this.setState({
            currentProjectId: projectId
        });
    }

    /**
     * Set project members
     *
     * @param {Array<Member>} members - Array of member objects
     */
    setMembers(members) {
        this.setState({ members });
    }

    /**
     * Set filters
     *
     * @param {Object} filters - Filter object { status?, search? }
     */
    setFilters(filters) {
        this.setState({
            filters: { ...this.state.filters, ...filters }
        });
    }

    /**
     * Set loading state
     *
     * BUSINESS LOGIC:
     * Used to show loading indicators in the UI while data is being fetched.
     *
     * @param {boolean} loading - Loading state
     */
    setLoading(loading) {
        this.setState({ loading });
    }

    /**
     * Set error state
     *
     * BUSINESS LOGIC:
     * Stores error messages for display to users. Automatically sets
     * loading to false since an error means the operation completed.
     *
     * @param {string|null} error - Error message or null to clear
     */
    setError(error) {
        this.setState({
            error,
            loading: false
        });
    }

    /**
     * Clear error state
     */
    clearError() {
        this.setState({ error: null });
    }

    /**
     * Reset state to initial values
     *
     * BUSINESS LOGIC:
     * Used when navigating away from projects or logging out.
     */
    reset() {
        this.state = {
            projects: [],
            currentProject: null,
            currentProjectId: null,
            filters: { status: '', search: '' },
            loading: false,
            error: null,
            members: [],
            stats: { total: 0, active: 0, draft: 0, completed: 0 }
        };
        this.notify({}, this.state);
    }

    // ============================================================
    // HELPER METHODS
    // ============================================================

    /**
     * Calculate project statistics
     *
     * BUSINESS LOGIC:
     * Computes aggregate statistics for dashboard display:
     * - Total project count
     * - Active projects
     * - Draft projects
     * - Completed projects
     *
     * @private
     * @param {Array<Project>} projects - Array of projects
     * @returns {Object} Statistics object
     */
    calculateStats(projects) {
        return {
            total: projects.length,
            active: projects.filter(p => p.status === 'active').length,
            draft: projects.filter(p => p.status === 'draft').length,
            completed: projects.filter(p => p.status === 'completed').length,
            archived: projects.filter(p => p.status === 'archived').length
        };
    }

    /**
     * Get projects filtered by current filters
     *
     * BUSINESS LOGIC:
     * Applies client-side filtering to projects list. This is useful
     * for instant filtering without server round-trips.
     *
     * @returns {Array<Project>} Filtered projects
     */
    getFilteredProjects() {
        let filtered = [...this.state.projects];

        // Filter by status
        if (this.state.filters.status) {
            filtered = filtered.filter(p => p.status === this.state.filters.status);
        }

        // Filter by search term
        if (this.state.filters.search) {
            const search = this.state.filters.search.toLowerCase();
            filtered = filtered.filter(p =>
                p.name.toLowerCase().includes(search) ||
                (p.description && p.description.toLowerCase().includes(search))
            );
        }

        return filtered;
    }

    /**
     * Get project by ID
     *
     * @param {string} projectId - Project UUID
     * @returns {Project|null} Project object or null if not found
     */
    getProjectById(projectId) {
        return this.state.projects.find(p => p.id === projectId) || null;
    }
}
