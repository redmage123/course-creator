/**
 * Track Management Controller
 *
 * BUSINESS CONTEXT:
 * Orchestrates the Track Management Modal, coordinating state updates,
 * UI rendering, event handling, and API integration for track editing.
 *
 * TECHNICAL IMPLEMENTATION:
 * - MVC controller pattern
 * - Event delegation for performance
 * - Reactive UI updates via state subscriptions
 * - Dependency injection for external services
 * - Event emitter for loose coupling
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Track management orchestration only
 * - Open/Closed: Extensible via events and dependency injection
 * - Liskov Substitution: Consistent controller interface
 * - Interface Segregation: Focused API
 * - Dependency Inversion: Depends on abstractions (injected dependencies)
 *
 * @module projects/wizard/track-management/track-management-controller
 */
import { TrackManagementState } from './track-management-state.js';
import { renderTrackInfoTab } from './tabs/info-tab.js';
import { renderTrackInstructorsTab } from './tabs/instructors-tab.js';
import { renderTrackCoursesTab } from './tabs/courses-tab.js';
import { renderTrackStudentsTab } from './tabs/students-tab.js';

/**
 * Track Management Controller
 *
 * BUSINESS LOGIC:
 * - Opens/closes Track Management Modal
 * - Switches between tabs (Info, Instructors, Courses, Students)
 * - Handles CRUD operations on instructors, courses, students
 * - Persists changes to backend API
 * - Emits events for external listeners
 *
 * DEPENDENCIES (injected):
 * - trackAPI: API service for track operations
 * - openModal: Function to open modal
 * - closeModal: Function to close modal
 * - showNotification: Function to show toast/notification
 * - courseModal: (Optional) Course creation modal service
 */
export class TrackManagementController {
    /**
     * Initialize controller
     *
     * @param {TrackManagementState} trackState - Track management state instance
     * @param {Object} dependencies - External dependencies
     * @param {Object} dependencies.trackAPI - Track API service
     * @param {Function} dependencies.openModal - Open modal function
     * @param {Function} dependencies.closeModal - Close modal function
     * @param {Function} dependencies.showNotification - Notification function
     * @param {Object} [dependencies.courseModal] - Optional course modal service
     */
    constructor(trackState, dependencies) {
        this.state = trackState;
        this.trackAPI = dependencies.trackAPI;
        this.openModal = dependencies.openModal;
        this.closeModal = dependencies.closeModal;
        this.showNotification = dependencies.showNotification;
        this.courseModal = dependencies.courseModal || null;

        this.modalId = 'trackManagementModal';
        this.eventHandlers = [];

        this.initializeStateSubscriptions();
    }

    /**
     * Initialize state change subscriptions
     *
     * @private
     */
    initializeStateSubscriptions() {
        this.state.subscribe((newState, oldState) => {
            // Re-render active tab when state changes
            if (newState.activeTab !== oldState.activeTab ||
                newState.instructors !== oldState.instructors ||
                newState.courses !== oldState.courses ||
                newState.students !== oldState.students) {
                this.renderActiveTab();
            }

            // Update tab indicators when data changes
            if (newState.instructors.length !== oldState.instructors.length ||
                newState.courses.length !== oldState.courses.length ||
                newState.students.length !== oldState.students.length) {
                this.updateTabIndicators();
            }
        });
    }

    /**
     * Open Track Management Modal for editing
     *
     * @param {Object} track - Track object to edit
     * @param {number} [trackIndex] - Optional track index for reference
     * @returns {void}
     */
    openTrackManagementModal(track, trackIndex = null) {
        if (!track) {
            console.error('TrackManagementController: track is required');
            return;
        }

        // Set track in state
        this.state.setTrack(track, trackIndex);

        // Render modal
        this.renderModal();

        // Attach event handlers
        this.attachEventHandlers();

        // Open modal
        this.openModal(this.modalId);

        // Emit event
        this.emit('track-management:opened', { track });
    }

    /**
     * Close Track Management Modal
     *
     * @param {boolean} [force=false] - Force close without dirty check
     * @returns {void}
     */
    closeTrackManagementModal(force = false) {
        if (!force && this.state.isDirty()) {
            const confirmed = confirm(
                'You have unsaved changes. Are you sure you want to close without saving?'
            );
            if (!confirmed) return;
        }

        // Detach event handlers
        this.detachEventHandlers();

        // Close modal
        this.closeModal(this.modalId);

        // Clear state
        this.state.clearTrack();

        // Emit event
        this.emit('track-management:closed');
    }

    /**
     * Render modal HTML structure
     *
     * @private
     */
    renderModal() {
        const track = this.state.getTrack();
        if (!track) return;

        const modalHtml = `
            <div id="${this.modalId}" class="modal modal-large" role="dialog" aria-labelledby="trackModalTitle">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 id="trackModalTitle">Manage Track: ${this.escapeHtml(track.name)}</h2>
                        <button class="modal-close" data-action="close-modal" aria-label="Close modal">×</button>
                    </div>

                    <!-- Tab Navigation -->
                    <div class="modal-tabs" role="tablist">
                        <button class="modal-tab active" data-tab="info" role="tab" aria-selected="true" aria-controls="infoTabContent">
                            ℹ️ Info
                            <span class="tab-indicator" data-tab-indicator="info"></span>
                        </button>
                        <button class="modal-tab" data-tab="instructors" role="tab" aria-selected="false" aria-controls="instructorsTabContent">
                            👨‍🏫 Instructors
                            <span class="tab-indicator" data-tab-indicator="instructors">${track.instructors?.length || 0}</span>
                        </button>
                        <button class="modal-tab" data-tab="courses" role="tab" aria-selected="false" aria-controls="coursesTabContent">
                            📚 Courses
                            <span class="tab-indicator" data-tab-indicator="courses">${track.courses?.length || 0}</span>
                        </button>
                        <button class="modal-tab" data-tab="students" role="tab" aria-selected="false" aria-controls="studentsTabContent">
                            👥 Students
                            <span class="tab-indicator" data-tab-indicator="students">${track.students?.length || 0}</span>
                        </button>
                    </div>

                    <!-- Tab Content -->
                    <div class="modal-body">
                        <div id="trackTabContent" class="tab-content"></div>
                    </div>

                    <!-- Modal Actions -->
                    <div class="modal-actions">
                        <button class="btn btn-secondary" data-action="close-modal">Cancel</button>
                        <button class="btn btn-primary" data-action="save-track">
                            💾 Save Changes
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if present
        const existing = document.getElementById(this.modalId);
        if (existing) existing.remove();

        // Insert new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Render initial tab content
        this.renderActiveTab();
    }

    /**
     * Render active tab content
     *
     * @private
     */
    renderActiveTab() {
        const track = this.state.getTrack();
        if (!track) return;

        const activeTab = this.state.getActiveTab();
        const contentContainer = document.getElementById('trackTabContent');
        if (!contentContainer) return;

        let html = '';

        switch (activeTab) {
            case 'info':
                html = renderTrackInfoTab(track);
                break;
            case 'instructors':
                html = renderTrackInstructorsTab(track);
                break;
            case 'courses':
                html = renderTrackCoursesTab(track);
                break;
            case 'students':
                html = renderTrackStudentsTab(track);
                break;
            default:
                html = '<p>Unknown tab</p>';
        }

        contentContainer.innerHTML = html;
    }

    /**
     * Update tab indicator badges
     *
     * @private
     */
    updateTabIndicators() {
        const track = this.state.getTrack();
        if (!track) return;

        const indicators = {
            instructors: track.instructors?.length || 0,
            courses: track.courses?.length || 0,
            students: track.students?.length || 0
        };

        Object.entries(indicators).forEach(([tab, count]) => {
            const indicator = document.querySelector(`[data-tab-indicator="${tab}"]`);
            if (indicator) {
                indicator.textContent = count;
            }
        });
    }

    /**
     * Switch to a different tab
     *
     * @param {string} tabName - Tab name to switch to
     * @private
     */
    switchTab(tabName) {
        // Update state
        this.state.setActiveTab(tabName);

        // Update tab button states
        const tabs = document.querySelectorAll('.modal-tab');
        tabs.forEach(tab => {
            const isActive = tab.dataset.tab === tabName;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-selected', isActive);
        });

        // Content is rendered automatically via state subscription
    }

    /**
     * Attach event handlers via delegation
     *
     * @private
     */
    attachEventHandlers() {
        const modal = document.getElementById(this.modalId);
        if (!modal) return;

        // Tab switching
    /**
     * EXECUTE TABHANDLER OPERATION
     * PURPOSE: Execute tabHandler operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {Event} e - Event object
     */
        const tabHandler = (e) => {
            const tab = e.target.closest('[data-tab]');
            if (tab) {
                this.switchTab(tab.dataset.tab);
            }
        };
        modal.addEventListener('click', tabHandler);
        this.eventHandlers.push({ element: modal, event: 'click', handler: tabHandler });

        // Action delegation
    /**
     * EXECUTE ACTIONHANDLER OPERATION
     * PURPOSE: Execute actionHandler operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {Event} e - Event object
     */
        const actionHandler = (e) => {
            const action = e.target.dataset.action;
            if (!action) return;

            this.handleAction(action, e.target);
        };
        modal.addEventListener('click', actionHandler);
        this.eventHandlers.push({ element: modal, event: 'click', handler: actionHandler });
    }

    /**
     * Detach all event handlers
     *
     * @private
     */
    detachEventHandlers() {
        this.eventHandlers.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventHandlers = [];
    }

    /**
     * Handle action button clicks
     *
     * @param {string} action - Action identifier
     * @param {HTMLElement} target - Button element
     * @private
     */
    async handleAction(action, target) {
        const index = target.dataset.index;

        switch (action) {
            // Modal actions
            case 'close-modal':
                this.closeTrackManagementModal();
                break;

            case 'save-track':
                await this.saveTrackChanges();
                break;

            // Instructor actions
            case 'add-instructor':
                await this.addInstructor();
                break;

            case 'remove-instructor':
                this.removeInstructor(parseInt(index, 10));
                break;

            // Course actions
            case 'create-course':
                await this.createCourse();
                break;

            case 'remove-course':
                this.removeCourse(parseInt(index, 10));
                break;

            case 'edit-course':
                this.editCourse(parseInt(index, 10));
                break;

            // Student actions
            case 'enroll-student':
                await this.enrollStudent();
                break;

            case 'bulk-enroll':
                await this.bulkEnrollStudents();
                break;

            case 'remove-student':
                this.removeStudent(parseInt(index, 10));
                break;

            case 'view-student-progress':
                this.viewStudentProgress(parseInt(index, 10));
                break;

            default:
                console.warn(`Unknown action: ${action}`);
        }
    }

    // ========================================
    // Instructor Management
    // ========================================

    /**
     * Add instructor to track
     *
     * @private
     */
    async addInstructor() {
        // Simple prompt-based input (to be replaced with proper modal)
        const name = prompt('Enter instructor name:');
        if (!name) return;

        const email = prompt('Enter instructor email:');
        if (!email) return;

        const instructor = { name, email };
        this.state.addInstructor(instructor);

        this.showNotification(`Instructor "${name}" added`, 'success');
        this.emit('track:instructor-added', { instructor });
    }

    /**
     * Remove instructor from track
     *
     * @param {number} index - Instructor index
     * @private
     */
    removeInstructor(index) {
        const instructors = this.state.getInstructors();
        const instructor = instructors[index];

        if (!instructor) return;

        const confirmed = confirm(`Remove instructor "${instructor.name}"?`);
        if (!confirmed) return;

        this.state.removeInstructor(index);
        this.showNotification(`Instructor removed`, 'success');
        this.emit('track:instructor-removed', { instructor });
    }

    // ========================================
    // Course Management
    // ========================================

    /**
     * Create new course for track
     *
     * @private
     */
    async createCourse() {
        if (this.courseModal) {
            // Use external course creation modal
            const track = this.state.getTrack();
            this.courseModal.open(track);
        } else {
            // Fallback: simple prompt
            const name = prompt('Enter course name:');
            if (!name) return;

            const description = prompt('Enter course description:');

            const course = { name, description, enrolled: 0 };
            this.state.addCourse(course);

            this.showNotification(`Course "${name}" created`, 'success');
            this.emit('track:course-added', { course });
        }
    }

    /**
     * Remove course from track
     *
     * @param {number} index - Course index
     * @private
     */
    removeCourse(index) {
        const courses = this.state.getCourses();
        const course = courses[index];

        if (!course) return;

        const confirmed = confirm(`Remove course "${course.name}"?`);
        if (!confirmed) return;

        this.state.removeCourse(index);
        this.showNotification(`Course removed`, 'success');
        this.emit('track:course-removed', { course });
    }

    /**
     * Edit existing course
     *
     * @param {number} index - Course index
     * @private
     */
    editCourse(index) {
        const courses = this.state.getCourses();
        const course = courses[index];

        if (!course) return;

        // Emit event for external handling
        this.emit('track:course-edit-requested', { course, index });
    }

    // ========================================
    // Student Management
    // ========================================

    /**
     * Enroll student in track
     *
     * @private
     */
    async enrollStudent() {
        // Simple prompt-based input (to be replaced with proper modal)
        const name = prompt('Enter student name:');
        if (!name) return;

        const email = prompt('Enter student email:');
        if (!email) return;

        const student = { name, email, progress: 0, status: 'active' };
        this.state.addStudent(student);

        this.showNotification(`Student "${name}" enrolled`, 'success');
        this.emit('track:student-enrolled', { student });
    }

    /**
     * Bulk enroll students
     *
     * @private
     */
    async bulkEnrollStudents() {
        // Emit event for external bulk enrollment modal
        this.emit('track:bulk-enroll-requested', { track: this.state.getTrack() });
    }

    /**
     * Remove student from track
     *
     * @param {number} index - Student index
     * @private
     */
    removeStudent(index) {
        const students = this.state.getStudents();
        const student = students[index];

        if (!student) return;

        const confirmed = confirm(`Remove student "${student.name}" from this track?`);
        if (!confirmed) return;

        this.state.removeStudent(index);
        this.showNotification(`Student removed`, 'success');
        this.emit('track:student-removed', { student });
    }

    /**
     * View student progress details
     *
     * @param {number} index - Student index
     * @private
     */
    viewStudentProgress(index) {
        const students = this.state.getStudents();
        const student = students[index];

        if (!student) return;

        // Emit event for external progress viewer
        this.emit('track:view-student-progress', { student });
    }

    // ========================================
    // Persistence
    // ========================================

    /**
     * Save track changes to backend
     *
     * @private
     */
    async saveTrackChanges() {
        if (!this.state.isDirty()) {
            this.showNotification('No changes to save', 'info');
            return;
        }

        const track = this.state.getTrack();
        if (!track || !track.id) {
            console.error('Track ID is required for saving');
            return;
        }

        this.state.setLoading(true);

        try {
            // Prepare update payload
            const updates = {
                instructors: this.state.getInstructors(),
                courses: this.state.getCourses(),
                students: this.state.getStudents()
            };

            // Call API
            const updatedTrack = await this.trackAPI.updateTrack(track.id, updates);

            // Mark as saved
            this.state.markSaved();

            this.showNotification('Track updated successfully', 'success');
            this.emit('track:updated', { track: updatedTrack });

            // Close modal after save
            this.closeTrackManagementModal(true);

        } catch (error) {
            console.error('Failed to save track:', error);
            this.state.setError(error.message);
            this.showNotification('Failed to save track changes', 'error');
        } finally {
            this.state.setLoading(false);
        }
    }

    // ========================================
    // Event Emitter
    // ========================================

    /**
     * Emit custom event
     *
     * @param {string} eventName - Event name
     * @param {Object} detail - Event detail data
     * @private
     */
    emit(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            detail,
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(event);
    }

    /**
     * Subscribe to controller events
     *
     * @param {string} eventName - Event name
     * @param {Function} callback - Event handler
     * @returns {Function} Unsubscribe function
     */
    on(eventName, callback) {
    /**
     * HANDLE  EVENT
     * PURPOSE: Handle  event
     * WHY: Encapsulates event handling logic for better code organization
     *
     * @param {Event} e - Event object
     */
        const handler = (e) => callback(e.detail);
        document.addEventListener(eventName, handler);
        return () => document.removeEventListener(eventName, handler);
    }

    // ========================================
    // Utilities
    // ========================================

    /**
     * Escape HTML to prevent XSS
     *
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     * @private
     */
    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Cleanup and destroy controller
     *
     * @returns {void}
     */
    destroy() {
        this.detachEventHandlers();
        this.state.clearTrack();
    }
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic usage
 * =======================
 * import { TrackManagementState } from './track-management-state.js';
 * import { TrackManagementController } from './track-management-controller.js';
 *
 * const state = new TrackManagementState();
 * const controller = new TrackManagementController(state, {
 *   trackAPI: trackAPIService,
 *   openModal: (id) => { ... },
 *   closeModal: (id) => { ... },
 *   showNotification: (msg, type) => { ... }
 * });
 *
 * // Open modal for editing
 * controller.openTrackManagementModal(trackData);
 *
 *
 * Example 2: Listen to events
 * ============================
 * controller.on('track:updated', ({ track }) => {
 *   console.log('Track updated:', track);
 *   refreshProjectsList();
 * });
 *
 * controller.on('track:instructor-added', ({ instructor }) => {
 *   console.log('Instructor added:', instructor);
 * });
 *
 *
 * Example 3: External course modal integration
 * ==============================================
 * const controller = new TrackManagementController(state, {
 *   trackAPI: trackAPIService,
 *   openModal: modalUtils.open,
 *   closeModal: modalUtils.close,
 *   showNotification: notifications.show,
 *   courseModal: courseCreationModal // External modal service
 * });
 */