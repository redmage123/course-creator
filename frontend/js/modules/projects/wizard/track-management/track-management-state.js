/**
 * Track Management State
 *
 * BUSINESS CONTEXT:
 * Manages the state of a track being edited in the Track Management Modal.
 * Tracks changes to instructors, courses, and students, and provides reactive
 * updates via Observer pattern.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Centralized state management for track editing
 * - Observer pattern for reactive UI updates
 * - Immutable state updates
 * - Tab navigation state
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Track editing state management only
 * - Open/Closed: Extensible through subscriptions
 * - Liskov Substitution: Consistent state interface
 *
 * USAGE:
 * import { TrackManagementState } from './track-management-state.js';
 *
 * const state = new TrackManagementState();
 * state.setTrack(trackData);
 * state.subscribe((newState) => console.log('Track updated:', newState));
 *
 * @module projects/wizard/track-management/track-management-state
 */
export class TrackManagementState {
    /**
     * Initialize track management state
     */
    constructor() {
        this.state = {
            // Track data
            track: null,
            trackId: null,
            trackIndex: null,

            // Tab navigation
            activeTab: 'info',

            // Track components
            instructors: [],
            courses: [],
            students: [],

            // State management
            isDirty: false,
            loading: false,
            error: null
        };

        this.subscribers = [];
    }

    /**
     * Get current state snapshot
     *
     * @returns {Object} Current state (immutable copy)
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Update state with new values
     *
     * @param {Object} updates - Partial state updates
     * @private
     */
    setState(updates) {
        const oldState = { ...this.state };
        this.state = {
            ...this.state,
            ...updates
        };
        this.notify(oldState, this.state);
    }

    /**
     * Subscribe to state changes
     *
     * @param {Function} callback - Called with (newState, oldState) on changes
     * @returns {Function} Unsubscribe function
     */
    subscribe(callback) {
        if (typeof callback !== 'function') {
            throw new Error('Subscriber callback must be a function');
        }

        this.subscribers.push(callback);

        // Return unsubscribe function
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
     * @param {Object} oldState - Previous state
     * @param {Object} newState - New state
     * @private
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

    // ========================================
    // Track Management
    // ========================================

    /**
     * Set track data for editing
     *
     * @param {Object} track - Track object to edit
     * @param {number} [trackIndex] - Optional track index for reference
     */
    setTrack(track, trackIndex = null) {
        if (!track) {
            throw new Error('Track data is required');
        }

        this.setState({
            track: { ...track },
            trackId: track.id || null,
            trackIndex: trackIndex,
            instructors: track.instructors ? [...track.instructors] : [],
            courses: track.courses ? [...track.courses] : [],
            students: track.students ? [...track.students] : [],
            isDirty: false,
            activeTab: 'info'
        });
    }

    /**
     * Clear track data
     */
    clearTrack() {
        this.setState({
            track: null,
            trackId: null,
            trackIndex: null,
            instructors: [],
            courses: [],
            students: [],
            isDirty: false,
            activeTab: 'info'
        });
    }

    /**
     * Get current track data
     *
     * @returns {Object|null} Current track data
     */
    getTrack() {
        if (!this.state.track) {
            return null;
        }

        return {
            ...this.state.track,
            instructors: this.state.instructors,
            courses: this.state.courses,
            students: this.state.students
        };
    }

    // ========================================
    // Tab Navigation
    // ========================================

    /**
     * Set active tab
     *
     * @param {string} tabName - Tab name ('info'|'instructors'|'courses'|'students')
     */
    setActiveTab(tabName) {
        const validTabs = ['info', 'instructors', 'courses', 'students'];
        if (!validTabs.includes(tabName)) {
            console.warn(`Invalid tab name: ${tabName}`);
            return;
        }

        this.setState({ activeTab: tabName });
    }

    /**
     * Get active tab
     *
     * @returns {string} Active tab name
     */
    getActiveTab() {
        return this.state.activeTab;
    }

    // ========================================
    // Instructors Management
    // ========================================

    /**
     * Add instructor to track
     *
     * @param {Object} instructor - Instructor data { name, email, ... }
     */
    addInstructor(instructor) {
        if (!instructor) {
            throw new Error('Instructor data is required');
        }

        const instructors = [...this.state.instructors, instructor];
        this.setState({ instructors, isDirty: true });
    }

    /**
     * Remove instructor from track
     *
     * @param {number} index - Instructor index to remove
     */
    removeInstructor(index) {
        if (index < 0 || index >= this.state.instructors.length) {
            console.warn(`Invalid instructor index: ${index}`);
            return;
        }

        const instructors = this.state.instructors.filter((_, i) => i !== index);
        this.setState({ instructors, isDirty: true });
    }

    /**
     * Update instructor data
     *
     * @param {number} index - Instructor index
     * @param {Object} updates - Instructor updates
     */
    updateInstructor(index, updates) {
        if (index < 0 || index >= this.state.instructors.length) {
            console.warn(`Invalid instructor index: ${index}`);
            return;
        }

        const instructors = [...this.state.instructors];
        instructors[index] = { ...instructors[index], ...updates };
        this.setState({ instructors, isDirty: true });
    }

    /**
     * Get all instructors
     *
     * @returns {Array} Array of instructors
     */
    getInstructors() {
        return [...this.state.instructors];
    }

    // ========================================
    // Courses Management
    // ========================================

    /**
     * Add course to track
     *
     * @param {Object} course - Course data { name, description, ... }
     */
    addCourse(course) {
        if (!course) {
            throw new Error('Course data is required');
        }

        const courses = [...this.state.courses, course];
        this.setState({ courses, isDirty: true });
    }

    /**
     * Remove course from track
     *
     * @param {number} index - Course index to remove
     */
    removeCourse(index) {
        if (index < 0 || index >= this.state.courses.length) {
            console.warn(`Invalid course index: ${index}`);
            return;
        }

        const courses = this.state.courses.filter((_, i) => i !== index);
        this.setState({ courses, isDirty: true });
    }

    /**
     * Update course data
     *
     * @param {number} index - Course index
     * @param {Object} updates - Course updates
     */
    updateCourse(index, updates) {
        if (index < 0 || index >= this.state.courses.length) {
            console.warn(`Invalid course index: ${index}`);
            return;
        }

        const courses = [...this.state.courses];
        courses[index] = { ...courses[index], ...updates };
        this.setState({ courses, isDirty: true });
    }

    /**
     * Get all courses
     *
     * @returns {Array} Array of courses
     */
    getCourses() {
        return [...this.state.courses];
    }

    // ========================================
    // Students Management
    // ========================================

    /**
     * Add student to track
     *
     * @param {Object} student - Student data { name, email, ... }
     */
    addStudent(student) {
        if (!student) {
            throw new Error('Student data is required');
        }

        const students = [...this.state.students, student];
        this.setState({ students, isDirty: true });
    }

    /**
     * Remove student from track
     *
     * @param {number} index - Student index to remove
     */
    removeStudent(index) {
        if (index < 0 || index >= this.state.students.length) {
            console.warn(`Invalid student index: ${index}`);
            return;
        }

        const students = this.state.students.filter((_, i) => i !== index);
        this.setState({ students, isDirty: true });
    }

    /**
     * Update student data
     *
     * @param {number} index - Student index
     * @param {Object} updates - Student updates
     */
    updateStudent(index, updates) {
        if (index < 0 || index >= this.state.students.length) {
            console.warn(`Invalid student index: ${index}`);
            return;
        }

        const students = [...this.state.students];
        students[index] = { ...students[index], ...updates };
        this.setState({ students, isDirty: true });
    }

    /**
     * Get all students
     *
     * @returns {Array} Array of students
     */
    getStudents() {
        return [...this.state.students];
    }

    // ========================================
    // State Management
    // ========================================

    /**
     * Check if track has unsaved changes
     *
     * @returns {boolean} True if track has unsaved changes
     */
    isDirty() {
        return this.state.isDirty;
    }

    /**
     * Mark track as saved
     */
    markSaved() {
        this.setState({ isDirty: false });
    }

    /**
     * Set loading state
     *
     * @param {boolean} loading
     */
    setLoading(loading) {
        this.setState({ loading });
    }

    /**
     * Set error
     *
     * @param {string|null} error - Error message or null
     */
    setError(error) {
        this.setState({ error });
    }

    /**
     * Clear error
     */
    clearError() {
        this.setState({ error: null });
    }
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic usage
 * =======================
 * import { TrackManagementState } from './track-management-state.js';
 *
 * const state = new TrackManagementState();
 * state.setTrack({
 *   id: 'track-123',
 *   name: 'Application Development',
 *   description: '...',
 *   instructors: [],
 *   courses: [],
 *   students: []
 * });
 *
 * console.log(state.getState());
 *
 *
 * Example 2: Subscribe to changes
 * ================================
 * const state = new TrackManagementState();
 * const unsubscribe = state.subscribe((newState, oldState) => {
 *   if (newState.instructors.length !== oldState.instructors.length) {
 *     console.log('Instructors changed');
 *     renderInstructorsList(newState.instructors);
 *   }
 * });
 *
 *
 * Example 3: Manage instructors
 * ==============================
 * state.addInstructor({ name: 'John Doe', email: 'john@example.com' });
 * state.updateInstructor(0, { email: 'newemail@example.com' });
 * state.removeInstructor(0);
 *
 *
 * Example 4: Track dirty state
 * ==============================
 * if (state.isDirty()) {
 *   const confirmed = confirm('You have unsaved changes. Save before closing?');
 *   if (confirmed) {
 *     await saveTrackChanges();
 *     state.markSaved();
 *   }
 * }
 *
 *
 * Example 5: Tab navigation
 * ==========================
 * state.setActiveTab('instructors');
 * console.log(state.getActiveTab()); // 'instructors'
 */