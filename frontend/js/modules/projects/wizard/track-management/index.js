/**
 * Track Management Module - Public API
 *
 * BUSINESS CONTEXT:
 * Provides a clean, simple API for managing tracks within projects.
 * Encapsulates all complexity of track editing, including instructors,
 * courses, and student enrollments.
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
 * @module projects/wizard/track-management
 */
import { TrackManagementState } from './track-management-state.js';
import { TrackManagementController } from './track-management-controller.js';

/**
 * Create and initialize track management module
 *
 * BUSINESS LOGIC:
 * Sets up all dependencies and returns a simple API for track management.
 * This factory function handles all the complexity of wiring up dependencies.
 *
 * USAGE:
 * import { createTrackManagement } from './wizard/track-management/index.js';
 *
 * const trackManagement = createTrackManagement({
 *   trackAPI: projectAPI,
 *   openModal: modalUtils.open,
 *   closeModal: modalUtils.close,
 *   showNotification: notifications.show,
 *   courseModal: courseCreationModal
 * });
 *
 * trackManagement.openTrackModal(trackData);
 *
 * @param {Object} dependencies - External dependencies
 * @param {Object} dependencies.trackAPI - Track API service
 * @param {Function} dependencies.openModal - Open modal function
 * @param {Function} dependencies.closeModal - Close modal function
 * @param {Function} dependencies.showNotification - Notification function
 * @param {Object} [dependencies.courseModal] - Optional course modal service
 * @returns {Object} Track management module public API
 */
export function createTrackManagement(dependencies) {
    // Validate required dependencies
    if (!dependencies || !dependencies.trackAPI) {
        throw new Error('TrackManagement: trackAPI is required');
    }

    if (!dependencies.openModal || !dependencies.closeModal) {
        throw new Error('TrackManagement: openModal and closeModal are required');
    }

    if (!dependencies.showNotification) {
        throw new Error('TrackManagement: showNotification is required');
    }

    // Initialize dependencies with dependency injection
    const trackState = new TrackManagementState();
    const trackController = new TrackManagementController(trackState, dependencies);

    // Return public API
    return {
        /**
         * Open Track Management Modal
         *
         * @param {Object} track - Track object to edit
         * @param {number} [trackIndex] - Optional track index for reference
         * @returns {void}
         */
        openTrackModal: (track, trackIndex) =>
            trackController.openTrackManagementModal(track, trackIndex),

        /**
         * Close Track Management Modal
         *
         * @param {boolean} [force=false] - Force close without dirty check
         * @returns {void}
         */
        closeTrackModal: (force) =>
            trackController.closeTrackManagementModal(force),

        /**
         * Get current track state
         *
         * @returns {Object|null} Current track data
         */
        getTrack: () => trackState.getTrack(),

        /**
         * Get current state snapshot
         *
         * @returns {Object} Current state
         */
        getState: () => trackState.getState(),

        /**
         * Check if track has unsaved changes
         *
         * @returns {boolean} True if track has unsaved changes
         */
        isDirty: () => trackState.isDirty(),

        /**
         * Subscribe to track management events
         *
         * Events:
         * - track-management:opened - Modal opened
         * - track-management:closed - Modal closed
         * - track:updated - Track saved successfully
         * - track:instructor-added - Instructor added to track
         * - track:instructor-removed - Instructor removed from track
         * - track:course-added - Course added to track
         * - track:course-removed - Course removed from track
         * - track:course-edit-requested - Course edit requested
         * - track:student-enrolled - Student enrolled in track
         * - track:student-removed - Student removed from track
         * - track:view-student-progress - Student progress view requested
         * - track:bulk-enroll-requested - Bulk enrollment requested
         *
         * @param {string} eventName - Event name
         * @param {Function} callback - Event handler
         * @returns {Function} Unsubscribe function
         */
        on: (eventName, callback) => trackController.on(eventName, callback),

        /**
         * Cleanup and destroy module
         *
         * @returns {void}
         */
        destroy: () => trackController.destroy()
    };
}

/**
 * Track Management Module Factory (Alternative API)
 *
 * Provides a class-based API for those who prefer instantiation syntax.
 *
 * USAGE:
 * import { TrackManagement } from './wizard/track-management/index.js';
 *
 * const trackManagement = new TrackManagement({
 *   trackAPI: projectAPI,
 *   openModal: modalUtils.open,
 *   closeModal: modalUtils.close,
 *   showNotification: notifications.show
 * });
 *
 * trackManagement.openTrackModal(trackData);
 */
export class TrackManagement {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {*} dependencies - Dependencies parameter
     */
    constructor(dependencies) {
        const module = createTrackManagement(dependencies);

        // Expose all public methods
        this.openTrackModal = module.openTrackModal;
        this.closeTrackModal = module.closeTrackModal;
        this.getTrack = module.getTrack;
        this.getState = module.getState;
        this.isDirty = module.isDirty;
        this.on = module.on;
        this.destroy = module.destroy;
    }
}

// Export individual components for advanced usage
export { TrackManagementState } from './track-management-state.js';
export { TrackManagementController } from './track-management-controller.js';

// Export tab renderers
export { renderTrackInfoTab, renderTrackSummary, renderTrackStats } from './tabs/info-tab.js';
export { renderTrackInstructorsTab } from './tabs/instructors-tab.js';
export { renderTrackCoursesTab } from './tabs/courses-tab.js';
export { renderTrackStudentsTab } from './tabs/students-tab.js';

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic Usage (Function-based)
 * ========================================
 * import { createTrackManagement } from './wizard/track-management/index.js';
 * import { projectAPI } from './services/project-api.js';
 * import { modalUtils } from './utils/modal-utils.js';
 * import { notifications } from './services/notifications.js';
 *
 * const trackManagement = createTrackManagement({
 *   trackAPI: projectAPI,
 *   openModal: modalUtils.open,
 *   closeModal: modalUtils.close,
 *   showNotification: notifications.show
 * });
 *
 * // Open track management modal
 * trackManagement.openTrackModal({
 *   id: 'track-123',
 *   name: 'Application Development',
 *   description: 'Software development training',
 *   instructors: [...],
 *   courses: [...],
 *   students: [...]
 * });
 *
 * // Listen to events
 * trackManagement.on('track:updated', ({ track }) => {
 *   console.log('Track updated:', track);
 *   refreshProjectsList();
 * });
 *
 * // Check for unsaved changes
 * if (trackManagement.isDirty()) {
 *   console.log('Track has unsaved changes');
 * }
 *
 * // Cleanup
 * trackManagement.destroy();
 *
 *
 * Example 2: Class-based Usage
 * =============================
 * import { TrackManagement } from './wizard/track-management/index.js';
 *
 * const trackManagement = new TrackManagement({
 *   trackAPI: projectAPI,
 *   openModal: modalUtils.open,
 *   closeModal: modalUtils.close,
 *   showNotification: notifications.show,
 *   courseModal: courseCreationModal // Optional
 * });
 *
 * trackManagement.openTrackModal(trackData);
 *
 *
 * Example 3: Integration with Projects Module
 * ============================================
 * import { createProjectsModule } from './modules/projects/index.js';
 * import { createTrackManagement } from './modules/projects/wizard/track-management/index.js';
 *
 * const projects = createProjectsModule({
 *   containerSelector: '#projects-container',
 *   projectAPI: orgAdminAPI
 * });
 *
 * const trackManagement = createTrackManagement({
 *   trackAPI: orgAdminAPI,
 *   openModal: modalUtils.open,
 *   closeModal: modalUtils.close,
 *   showNotification: notifications.show
 * });
 *
 * // Open track modal from projects list
 * projects.on('project:track-selected', ({ track }) => {
 *   trackManagement.openTrackModal(track);
 * });
 *
 * // Refresh projects when track updated
 * trackManagement.on('track:updated', () => {
 *   projects.loadProjects();
 * });
 *
 *
 * Example 4: Advanced Usage (Direct Component Access)
 * ====================================================
 * import { TrackManagementState, TrackManagementController } from './wizard/track-management/index.js';
 *
 * // Create custom state
 * const state = new TrackManagementState();
 *
 * // Subscribe to specific state changes
 * state.subscribe((newState, oldState) => {
 *   if (newState.instructors.length !== oldState.instructors.length) {
 *     console.log('Instructors changed');
 *     updateInstructorsList(newState.instructors);
 *   }
 * });
 *
 * // Create controller with custom state
 * const controller = new TrackManagementController(state, {
 *   trackAPI: customAPI,
 *   openModal: customModalOpen,
 *   closeModal: customModalClose,
 *   showNotification: customNotify
 * });
 *
 *
 * Example 5: Event Handling
 * ==========================
 * const trackManagement = createTrackManagement(dependencies);
 *
 * // Listen to all track events
 * trackManagement.on('track-management:opened', ({ track }) => {
 *   console.log('Track modal opened:', track.name);
 * });
 *
 * trackManagement.on('track:instructor-added', ({ instructor }) => {
 *   console.log('Instructor added:', instructor.name);
 *   sendNotificationEmail(instructor);
 * });
 *
 * trackManagement.on('track:course-added', ({ course }) => {
 *   console.log('Course added:', course.name);
 *   updateCourseAnalytics();
 * });
 *
 * trackManagement.on('track:student-enrolled', ({ student }) => {
 *   console.log('Student enrolled:', student.name);
 *   sendWelcomeEmail(student);
 * });
 *
 * trackManagement.on('track:bulk-enroll-requested', ({ track }) => {
 *   openBulkEnrollmentModal(track);
 * });
 *
 *
 * Example 6: Testing
 * ===================
 * import { createTrackManagement } from './wizard/track-management/index.js';
 *
 * // Mock dependencies
 * const mockAPI = {
 *   updateTrack: jest.fn().mockResolvedValue({ id: 'track-123', name: 'Updated Track' })
 * };
 *
 * const mockModal = {
 *   open: jest.fn(),
 *   close: jest.fn()
 * };
 *
 * const mockNotifications = {
 *   show: jest.fn()
 * };
 *
 * const trackManagement = createTrackManagement({
 *   trackAPI: mockAPI,
 *   openModal: mockModal.open,
 *   closeModal: mockModal.close,
 *   showNotification: mockNotifications.show
 * });
 *
 * // Test opening modal
 * const trackData = { id: 'track-123', name: 'Test Track' };
 * trackManagement.openTrackModal(trackData);
 * expect(mockModal.open).toHaveBeenCalled();
 *
 * // Test event emission
 * const eventHandler = jest.fn();
 * trackManagement.on('track:updated', eventHandler);
 * // ... trigger save action ...
 * expect(eventHandler).toHaveBeenCalledWith(expect.objectContaining({
 *   track: expect.any(Object)
 * }));
 */