/**
 * Project List Renderer
 *
 * BUSINESS CONTEXT:
 * Renders the projects list table with key metrics including status,
 * duration, participant counts, and action buttons. Provides interactive
 * elements for viewing, editing, managing members, and deleting projects.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure rendering logic (no business logic)
 * - Event delegation for performance
 * - XSS protection through HTML escaping
 * - Responsive table design
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: UI rendering only
 * - Open/Closed: Extensible through event emitters
 * - Dependency Inversion: Depends on data models, not implementations
 *
 * @module projects/ui/project-list-renderer
 */
import {
    escapeHtml,
    formatDate,
    formatDuration
} from '../utils/formatting.js';

/**
 * ProjectListRenderer Class
 *
 * Handles rendering of project list table and emits events for user actions.
 * Uses event delegation for efficient event handling.
 *
 * USAGE:
 * const renderer = new ProjectListRenderer('#projects-container');
 * renderer.on('project:view', (projectId) => { ... });
 * renderer.render(projects);
 */
export class ProjectListRenderer {
    /**
     * Initialize the project list renderer
     *
     * @param {string|HTMLElement} container - Container selector or element
     */
    constructor(container) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!this.container) {
            throw new Error(`ProjectListRenderer: Container not found`);
        }

        /**
         * Event listeners registry
         * @private
         */
        this.eventListeners = new Map();

        // Initialize event delegation
        this.initializeEventDelegation();
    }

    /**
     * Set up event delegation on container
     *
     * TECHNICAL NOTE:
     * Event delegation is more efficient than attaching individual handlers
     * to each button. We listen at the container level and determine which
     * action was triggered based on the clicked element's data attributes.
     *
     * @private
     */
    initializeEventDelegation() {
        this.container.addEventListener('click', (event) => {
            const target = event.target.closest('[data-action]');
            if (!target) return;

            event.preventDefault();

            const action = target.dataset.action;
            const projectId = target.dataset.projectId;

            // Emit event based on action
            this.emit(`project:${action}`, projectId);
        });
    }

    /**
     * Render projects table
     *
     * BUSINESS LOGIC:
     * Displays all projects in a table format with:
     * - Project name and description
     * - Status badge (color-coded)
     * - Duration in weeks
     * - Participant counts (current/max)
     * - Start and end dates
     * - Action buttons (view, edit, members, delete)
     *
     * @param {Array<Project>} projects - Array of project objects
     */
    render(projects) {
        if (!projects || projects.length === 0) {
            this.renderEmpty();
            return;
        }

        const html = `
            <div class="projects-table-container">
                <table class="projects-table">
                    <thead>
                        ${this.renderTableHeader()}
                    </thead>
                    <tbody>
                        ${this.renderTableBody(projects)}
                    </tbody>
                </table>
            </div>
        `;

        this.container.innerHTML = html;
    }

    /**
     * Render table header
     *
     * @private
     * @returns {string} HTML for table header
     */
    renderTableHeader() {
        return `
            <tr>
                <th>Project Name</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Participants</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Actions</th>
            </tr>
        `;
    }

    /**
     * Render table body rows
     *
     * @private
     * @param {Array<Project>} projects - Array of project objects
     * @returns {string} HTML for table body
     */
    renderTableBody(projects) {
        return projects.map(project => this.renderProjectRow(project)).join('');
    }

    /**
     * Render single project row
     *
     * BUSINESS LOGIC:
     * Each row shows:
     * - Project name (bold) with description (truncated to 100 chars)
     * - Status badge with appropriate color
     * - Duration in human-readable format
     * - Participant count with max capacity
     * - Formatted dates
     * - Action buttons with icons
     *
     * TECHNICAL NOTE:
     * Uses data attributes for event delegation. This is more efficient
     * than onclick handlers and allows for easier testing.
     *
     * @private
     * @param {Project} project - Project object
     * @returns {string} HTML for project row
     */
    renderProjectRow(project) {
        return `
            <tr data-project-id="${project.id}">
                <td>
                    <div class="project-name">
                        <strong>${escapeHtml(project.name)}</strong>
                        ${project.description ? `
                            <div class="project-description">
                                ${escapeHtml(this.truncate(project.description, 100))}
                            </div>
                        ` : ''}
                    </div>
                </td>
                <td>
                    ${this.renderStatusBadge(project.status)}
                </td>
                <td>
                    ${formatDuration(project.duration_weeks)}
                </td>
                <td>
                    <span class="participant-count">
                        <strong>${project.current_participants || 0}</strong>
                        ${project.max_participants ? ` / ${project.max_participants}` : ''}
                    </span>
                </td>
                <td>${formatDate(project.start_date)}</td>
                <td>${formatDate(project.end_date)}</td>
                <td>
                    ${this.renderActionButtons(project.id)}
                </td>
            </tr>
        `;
    }

    /**
     * Render status badge with appropriate color
     *
     * BUSINESS LOGIC:
     * Status badges use color coding:
     * - draft: Blue (planning phase)
     * - active: Green (currently running)
     * - completed: Gray (finished)
     * - archived: Dark gray (archived)
     *
     * @private
     * @param {string} status - Project status
     * @returns {string} HTML for status badge
     */
    renderStatusBadge(status) {
        const statusClass = `status-badge status-badge--${status || 'draft'}`;
        const statusText = status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Draft';

        return `<span class="${statusClass}">${statusText}</span>`;
    }

    /**
     * Render action buttons
     *
     * BUSINESS LOGIC:
     * Provides four actions for each project:
     * - View: See project details
     * - Edit: Modify project settings
     * - Members: Manage project membership
     * - Delete: Remove project
     *
     * TECHNICAL NOTE:
     * Uses data attributes for action type and project ID.
     * Event delegation handles all clicks at container level.
     *
     * @private
     * @param {string} projectId - Project UUID
     * @returns {string} HTML for action buttons
     */
    renderActionButtons(projectId) {
        return `
            <div class="action-buttons">
                <button
                    class="btn-icon btn-icon--view"
                    data-action="view"
                    data-project-id="${projectId}"
                    title="View Details"
                    aria-label="View project details">
                    👁️
                </button>
                <button
                    class="btn-icon btn-icon--edit"
                    data-action="edit"
                    data-project-id="${projectId}"
                    title="Edit"
                    aria-label="Edit project">
                    ✏️
                </button>
                <button
                    class="btn-icon btn-icon--members"
                    data-action="members"
                    data-project-id="${projectId}"
                    title="Manage Members"
                    aria-label="Manage project members">
                    👥
                </button>
                <button
                    class="btn-icon btn-icon--delete"
                    data-action="delete"
                    data-project-id="${projectId}"
                    title="Delete"
                    aria-label="Delete project">
                    🗑️
                </button>
            </div>
        `;
    }

    /**
     * Render empty state
     *
     * BUSINESS LOGIC:
     * Shown when no projects exist. Provides guidance to create first project.
     *
     * @private
     */
    renderEmpty() {
        this.container.innerHTML = `
            <div class="projects-empty-state">
                <div class="empty-state-icon">📁</div>
                <h3>No Projects Found</h3>
                <p>Get started by creating your first project.</p>
                <button
                    class="btn btn-primary"
                    data-action="create"
                    data-project-id="">
                    Create Project
                </button>
            </div>
        `;
    }

    /**
     * Render loading state
     *
     * BUSINESS LOGIC:
     * Shows loading spinner while projects are being fetched.
     */
    renderLoading() {
        this.container.innerHTML = `
            <div class="projects-loading-state">
                <div class="loading-spinner"></div>
                <p>Loading projects...</p>
            </div>
        `;
    }

    /**
     * Render error state
     *
     * BUSINESS LOGIC:
     * Shows error message when project loading fails.
     *
     * @param {string} errorMessage - Error message to display
     */
    renderError(errorMessage) {
        this.container.innerHTML = `
            <div class="projects-error-state">
                <div class="error-icon">⚠️</div>
                <h3>Error Loading Projects</h3>
                <p>${escapeHtml(errorMessage)}</p>
                <button
                    class="btn btn-secondary"
                    data-action="retry"
                    data-project-id="">
                    Retry
                </button>
            </div>
        `;
    }

    // ============================================================
    // EVENT EMITTER PATTERN
    // ============================================================

    /**
     * Register event listener
     *
     * TECHNICAL NOTE:
     * Implements a simple event emitter pattern. This decouples the
     * renderer from the controller, following the Dependency Inversion
     * Principle.
     *
     * @param {string} event - Event name (e.g., 'project:view')
     * @param {Function} callback - Event handler function
     * @returns {Function} Unsubscribe function
     *
     * @example
     * renderer.on('project:view', (projectId) => {
     *   console.log('View project:', projectId);
     * });
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }

        this.eventListeners.get(event).push(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.eventListeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        };
    }

    /**
     * Emit event to all registered listeners
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
    // UTILITY METHODS
    // ============================================================

    /**
     * Truncate text to specified length
     *
     * @private
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated text with ellipsis if needed
     */
    truncate(text, maxLength) {
        if (!text || text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength) + '...';
    }

    /**
     * Clear container
     *
     * BUSINESS LOGIC:
     * Used when navigating away or resetting the view.
     */
    clear() {
        this.container.innerHTML = '';
    }
}
