/**
 * Lab Lifecycle Manager
 * Handles automatic lab container lifecycle management based on user authentication events
 */
import { showNotification } from './notifications.js';

class LabLifecycleManager {
    /**
     * Creates a new LabLifecycleManager instance for managing student lab containers.
     *
     * Initializes lab management system that automatically handles container lifecycle based on
     * user authentication events (login, logout, tab switching). Manages lab state tracking,
     * health monitoring, and automatic pause/resume.
     *
     * WHY: Students need persistent lab environments that survive page reloads and resume automatically
     * when returning to the platform, while conserving resources by pausing inactive labs.
     *
     * @constructor
     */
    constructor() {
        // Use global CONFIG (loaded via script tag in HTML)
        this.labApiBase = window.CONFIG?.API_URLS?.LAB_MANAGER || 'http://localhost:8006';
        this.currentUser = null;
        this.enrolledCourses = [];
        this.activeLabs = {};
        this.labCheckInterval = null;
        this.isInitialized = false;
    }

    /**
     * Initializes the lab lifecycle manager for a specific user.
     *
     * Loads enrolled courses, initializes lab containers for each course, starts health check
     * monitoring, and sets up window unload handlers. Only initializes once per session.
     *
     * WHY: Automatic initialization ensures students have lab environments ready when they need them,
     * without requiring manual setup or understanding of container management.
     *
     * @param {Object} user - The authenticated user object
     * @param {string|number} user.id - User identifier
     * @param {string} user.email - User email address
     * @returns {Promise<void>}
     */
    async initialize(user) {
        if (this.isInitialized) {
            return;
        }

        this.currentUser = user;

        try {
            // Load enrolled courses for the user
            await this.loadEnrolledCourses();
            
            // Start lab management
            await this.initializeUserLabs();
            
            // Set up periodic lab health checks
            this.startLabHealthChecks();
            
            // Set up window unload event to pause labs
            this.setupWindowUnloadHandler();
            
            this.isInitialized = true;
            
        } catch (error) {
            console.error('Error initializing Lab Lifecycle Manager:', error);
        }
    }

    /**
     * Loads the list of courses the current user is enrolled in.
     *
     * Fetches enrolled courses from localStorage or API. Falls back to empty array if
     * authentication token is missing or fetch fails.
     *
     * WHY: The system needs to know which courses the user is enrolled in to create and manage
     * the appropriate lab containers - one container per enrolled course.
     *
     * @returns {Promise<void>}
     * @throws {Error} If no authentication token is found
     */
    async loadEnrolledCourses() {
        try {
            // This would typically call the user management service
            // For now, we'll simulate getting courses from localStorage or API
            const authToken = localStorage.getItem('authToken');
            
            if (!authToken) {
                throw new Error('No authentication token found');
            }

            // Simulate API call to get enrolled courses
            // In a real implementation, this would call the course management service
            const storedCourses = localStorage.getItem('enrolledCourses');
            if (storedCourses) {
                this.enrolledCourses = JSON.parse(storedCourses);
            }
            
            
        } catch (error) {
            console.error('Error loading enrolled courses:', error);
            this.enrolledCourses = [];
        }
    }

    /**
     * Initializes lab containers for all enrolled courses.
     *
     * Iterates through enrolled courses and creates/retrieves lab container for each.
     * Handles failures gracefully by logging errors but continuing with remaining courses.
     *
     * WHY: Students need lab environments ready for all their courses, not just the current one.
     * Parallel initialization during login ensures labs are available when needed.
     *
     * @returns {Promise<void>}
     */
    async initializeUserLabs() {
        if (!this.currentUser || this.enrolledCourses.length === 0) {
            return;
        }


        for (const course of this.enrolledCourses) {
            try {
                await this.getOrCreateStudentLab(course.id);
            } catch (error) {
                console.error(`Error initializing lab for course ${course.id}:`, error);
            }
        }
    }

    /**
     * Gets an existing lab container or creates a new one for a specific course.
     *
     * Sends POST request to lab manager API with user ID and course ID. Stores lab data in
     * activeLabs map and shows notification based on status. Polls for completion if building.
     *
     * WHY: Lab containers must be created on-demand per course/user combination. This method
     * ensures idempotency - calling multiple times won't create duplicate containers.
     *
     * @param {string|number} courseId - The course identifier to get/create lab for
     * @returns {Promise<Object|null>} The lab data object, or null if creation failed
     */
    async getOrCreateStudentLab(courseId) {
        try {
            const requestData = {
                user_id: this.currentUser.id || this.currentUser.email,
                course_id: courseId
            };


            const response = await fetch(`${this.labApiBase}/labs/student`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                },
                body: JSON.stringify(requestData)
            });

            if (response.ok) {
                const labData = await response.json();
                this.activeLabs[courseId] = labData;
                
                
                // Show notification if lab is ready
                if (labData.status === 'running') {
                    showNotification(`Lab environment ready for course ${courseId}`, 'success');
                } else if (labData.status === 'building') {
                    showNotification(`Lab environment is building for course ${courseId}...`, 'info');
                    this.pollLabStatus(labData.lab_id, courseId);
                }
                
                return labData;
            } else {
                console.error('Failed to get/create student lab:', response.statusText);
                return null;
            }
            
        } catch (error) {
            console.error('Error getting/creating student lab:', error);
            return null;
        }
    }

    /**
     * Polls a building lab's status until it's running or encounters an error.
     *
     * Checks lab status every 10 seconds with maximum 30 attempts (5 minutes total).
     * Shows notifications when lab becomes ready, errors, or times out.
     *
     * WHY: Lab container builds can take 30-120 seconds. Polling provides feedback to users
     * and updates internal state when containers become available.
     *
     * @param {string} labId - The lab identifier to poll
     * @param {string|number} courseId - The course identifier for user notification
     * @returns {Promise<void>}
     */
    async pollLabStatus(labId, courseId) {
        const maxAttempts = 30; // 5 minutes with 10-second intervals
        let attempts = 0;

    /**
     * EXECUTE CHECKSTATUS OPERATION
     * PURPOSE: Execute checkStatus operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
        const checkStatus = async () => {
            try {
                const response = await fetch(`${this.labApiBase}/labs/${labId}`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                    }
                });

                if (response.ok) {
                    const labData = await response.json();
                    this.activeLabs[courseId] = labData;

                    if (labData.status === 'running') {
                        showNotification(`Lab environment ready for course ${courseId}!`, 'success');
                        return;
                    } else if (labData.status === 'error') {
                        showNotification(`Lab environment failed for course ${courseId}`, 'error');
                        return;
                    }
                }

                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkStatus, 10000); // Check again in 10 seconds
                } else {
                    showNotification(`Lab environment is taking longer than expected for course ${courseId}`, 'warning');
                }

            } catch (error) {
                console.error('Error polling lab status:', error);
            }
        };

        setTimeout(checkStatus, 5000); // Start checking after 5 seconds
    }

    /**
     * Pauses all currently running lab containers.
     *
     * Sends pause requests to all running labs in parallel using Promise.allSettled.
     * Updates local state to reflect paused status. Called on logout or long inactivity.
     *
     * WHY: Running containers consume significant server resources. Pausing inactive labs
     * preserves student work while freeing resources for active users.
     *
     * @returns {Promise<void>}
     */
    async pauseAllLabs() {

        const pausePromises = Object.entries(this.activeLabs).map(async ([courseId, labData]) => {
            if (labData.status === 'running') {
                try {
                    const response = await fetch(`${this.labApiBase}/labs/${labData.lab_id}/pause`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                        }
                    });

                    if (response.ok) {
                        this.activeLabs[courseId].status = 'paused';
                    } else {
                        console.error(`Failed to pause lab for course ${courseId}`);
                    }
                } catch (error) {
                    console.error(`Error pausing lab for course ${courseId}:`, error);
                }
            }
        });

        await Promise.allSettled(pausePromises);
    }

    /**
     * Resumes all paused lab containers.
     *
     * Sends resume requests to all paused labs in parallel using Promise.allSettled.
     * Updates local state to reflect running status. Called on login or tab re-focus.
     *
     * WHY: Students expect their lab environment to resume where they left off. Auto-resume
     * eliminates manual restart steps and provides seamless user experience.
     *
     * @returns {Promise<void>}
     */
    async resumeAllLabs() {

        const resumePromises = Object.entries(this.activeLabs).map(async ([courseId, labData]) => {
            if (labData.status === 'paused') {
                try {
                    const response = await fetch(`${this.labApiBase}/labs/${labData.lab_id}/resume`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                        }
                    });

                    if (response.ok) {
                        this.activeLabs[courseId].status = 'running';
                    } else {
                        console.error(`Failed to resume lab for course ${courseId}`);
                    }
                } catch (error) {
                    console.error(`Error resuming lab for course ${courseId}:`, error);
                }
            }
        });

        await Promise.allSettled(resumePromises);
    }

    /**
     * Returns the access URL for a course's lab container if running.
     *
     * Retrieves the lab's access URL from the activeLabs map. Returns null if lab doesn't
     * exist, has no URL, or is not in running state.
     *
     * WHY: Lab containers are accessed via unique URLs (typically VS Code Server or JupyterLab).
     * This method provides safe access to URLs only when labs are ready.
     *
     * @param {string|number} courseId - The course identifier
     * @returns {string|null} The lab access URL, or null if not available
     */
    getLabAccessUrl(courseId) {
        const lab = this.activeLabs[courseId];
        if (lab && lab.access_url && lab.status === 'running') {
            return lab.access_url;
        }
        return null;
    }

    /**
     * Checks if a course's lab container is ready to use.
     *
     * Returns true only if the lab exists and has status 'running'. Used to enable/disable
     * lab access buttons and show appropriate UI states.
     *
     * WHY: UI needs to know lab state to show accurate status (ready, building, paused, error)
     * and prevent users from trying to access labs that aren't running.
     *
     * @param {string|number} courseId - The course identifier
     * @returns {boolean} True if lab is running and ready, false otherwise
     */
    isLabReady(courseId) {
        const lab = this.activeLabs[courseId];
        return lab && lab.status === 'running';
    }

    /**
     * Returns the current status of a course's lab container.
     *
     * Returns the lab's status string ('running', 'paused', 'building', 'error', or 'not_created').
     * Used for displaying lab status indicators and conditional logic.
     *
     * WHY: Different lab states require different UI treatments and user messaging. This method
     * provides a single source of truth for lab status throughout the application.
     *
     * @param {string|number} courseId - The course identifier
     * @returns {string} The lab status ('running', 'paused', 'building', 'error', 'not_created')
     */
    getLabStatus(courseId) {
        const lab = this.activeLabs[courseId];
        return lab ? lab.status : 'not_created';
    }

    /**
     * Starts periodic health checks for all active lab containers.
     *
     * Sets up an interval that runs health checks every 5 minutes. Helps detect and
     * respond to container failures, network issues, or resource problems.
     *
     * WHY: Lab containers can fail silently due to OOM errors, network issues, or Docker problems.
     * Regular health checks detect failures early so users can be notified and containers restarted.
     *
     * @returns {void}
     */
    startLabHealthChecks() {
        // Check lab health every 5 minutes
        this.labCheckInterval = setInterval(async () => {
            await this.performLabHealthCheck();
        }, 5 * 60 * 1000);

    }

    /**
     * Stops the periodic health check interval.
     *
     * Clears the health check interval when manager is cleaned up or user logs out.
     * Prevents memory leaks from continued polling after user session ends.
     *
     * WHY: Intervals must be explicitly cleared to prevent memory leaks and unnecessary
     * network requests after the lab manager is no longer needed.
     *
     * @returns {void}
     */
    stopLabHealthChecks() {
        if (this.labCheckInterval) {
            clearInterval(this.labCheckInterval);
            this.labCheckInterval = null;
        }
    }

    /**
     * Performs a health check on all active lab containers.
     *
     * Fetches current status for each lab from the API and updates local state.
     * Logs warnings for failed health checks but continues checking remaining labs.
     *
     * WHY: Container state can change outside this manager (manual intervention, crashes, etc.).
     * Health checks ensure local state stays synchronized with actual container state.
     *
     * @returns {Promise<void>}
     */
    async performLabHealthCheck() {

        for (const [courseId, labData] of Object.entries(this.activeLabs)) {
            try {
                const response = await fetch(`${this.labApiBase}/labs/${labData.lab_id}`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                    }
                });

                if (response.ok) {
                    const updatedLabData = await response.json();
                    this.activeLabs[courseId] = updatedLabData;
                } else {
                    console.warn(`Lab health check failed for course ${courseId}`);
                }
            } catch (error) {
                console.error(`Error checking lab health for course ${courseId}:`, error);
            }
        }
    }

    /**
     * Sets up event handlers for window unload and visibility changes.
     *
     * Registers beforeunload handler (browser close/navigation) to pause labs and visibilitychange
     * handler (tab switching) to pause after 30 seconds of inactivity or resume when tab becomes visible.
     *
     * WHY: Labs should pause when students leave the platform to conserve resources, but resume
     * automatically when they return for seamless workflow.
     *
     * @returns {void}
     */
    setupWindowUnloadHandler() {
        // Handle page unload (browser close, tab close, navigation)
        window.addEventListener('beforeunload', async (event) => {
            // For a quick departure, we need to use navigator.sendBeacon for reliability
            await this.quickPauseAllLabs();
        });

        // Handle page visibility changes (tab switching)
        document.addEventListener('visibilitychange', async () => {
            if (document.hidden) {
                // Tab is hidden, pause labs after a delay
                setTimeout(async () => {
                    if (document.hidden) {
                        await this.pauseAllLabs();
                    }
                }, 30000); // 30 second delay before pausing
            } else {
                // Tab is visible, resume labs
                await this.resumeAllLabs();
            }
        });
    }

    /**
     * Quickly pauses all labs using sendBeacon for page unload scenarios.
     *
     * Uses navigator.sendBeacon instead of fetch because regular requests are often cancelled
     * during page unload. SendBeacon ensures pause requests are sent even as page closes.
     *
     * WHY: Normal async requests don't complete during page unload. SendBeacon is specifically
     * designed for sending analytics/cleanup data during unload and is more reliable.
     *
     * @returns {Promise<void>}
     */
    async quickPauseAllLabs() {
        const authToken = localStorage.getItem('authToken');
        if (!authToken) return;

        Object.entries(this.activeLabs).forEach(([courseId, labData]) => {
            if (labData.status === 'running') {
                try {
                    // Use sendBeacon for reliability during page unload
                    const data = JSON.stringify({});
                    navigator.sendBeacon(
                        `${this.labApiBase}/labs/${labData.lab_id}/pause`,
                        data
                    );
                } catch (error) {
                    console.error(`Error quick-pausing lab for course ${courseId}:`, error);
                }
            }
        });
    }

    /**
     * Cleans up all resources and pauses all labs.
     *
     * Stops health checks, pauses all labs, clears all state, and resets initialization flag.
     * Called on logout or when manager is being destroyed.
     *
     * WHY: Proper cleanup prevents memory leaks, unnecessary network requests, and ensures
     * clean state for next user session or manager re-initialization.
     *
     * @returns {Promise<void>}
     */
    async cleanup() {
        
        this.stopLabHealthChecks();
        await this.pauseAllLabs();
        
        this.activeLabs = {};
        this.enrolledCourses = [];
        this.currentUser = null;
        this.isInitialized = false;
        
    }

    /**
     * Updates the enrolled courses list and initializes labs for new enrollments.
     *
     * Replaces the enrolled courses list and creates lab containers for any newly enrolled
     * courses that don't already have active labs.
     *
     * WHY: When students enroll in new courses, their lab containers should be created
     * automatically without requiring logout/login or manual initialization.
     *
     * @param {Array<Object>} courses - Array of course objects student is enrolled in
     * @param {string|number} courses[].id - Course identifier
     * @returns {Promise<void>}
     */
    async updateEnrolledCourses(courses) {
        this.enrolledCourses = courses;
        
        // Initialize labs for any new courses
        for (const course of courses) {
            if (!this.activeLabs[course.id]) {
                await this.getOrCreateStudentLab(course.id);
            }
        }
    }

    /**
     * Accesses a lab container, resuming it if paused, and returns the access URL.
     *
     * Checks lab exists, resumes it if paused, updates last access time, and returns the
     * access URL. Throws errors if lab doesn't exist or isn't ready.
     *
     * WHY: Provides a single method for accessing labs that handles all necessary state
     * transitions (pause to running) and validation before returning the URL.
     *
     * @param {string|number} courseId - The course identifier
     * @returns {Promise<string>} The lab access URL
     * @throws {Error} If lab not found or not ready
     */
    async accessLab(courseId) {
        const lab = this.activeLabs[courseId];
        
        if (!lab) {
            throw new Error('Lab not found for this course');
        }
        
        if (lab.status === 'paused') {
            // Resume the lab first
            showNotification('Resuming lab environment...', 'info');
            await this.resumeSpecificLab(courseId);
        }
        
        if (lab.status === 'running' && lab.access_url) {
            // Update last accessed time
            await this.updateLabAccess(lab.lab_id);
            return lab.access_url;
        } else {
            throw new Error('Lab environment is not ready');
        }
    }

    /**
     * Resumes a specific paused lab container.
     *
     * Sends resume request to lab manager API, updates local state, and shows success
     * notification. Throws error if resume fails.
     *
     * WHY: Sometimes only one lab needs to be resumed (user accessing specific course) rather
     * than resuming all labs. This saves resources and reduces resume time.
     *
     * @param {string|number} courseId - The course identifier
     * @returns {Promise<void>}
     * @throws {Error} If lab not found or resume fails
     */
    async resumeSpecificLab(courseId) {
        const lab = this.activeLabs[courseId];
        if (!lab) return;

        try {
            const response = await fetch(`${this.labApiBase}/labs/${lab.lab_id}/resume`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.ok) {
                this.activeLabs[courseId].status = 'running';
                showNotification('Lab environment resumed!', 'success');
            } else {
                throw new Error('Failed to resume lab');
            }
        } catch (error) {
            console.error('Error resuming lab:', error);
            throw error;
        }
    }

    /**
     * Updates the last accessed timestamp for a lab container.
     *
     * Sends a GET request to the lab endpoint to update its last access time in the database.
     * Used for auto-pause policies based on inactivity and usage analytics.
     *
     * WHY: Labs that haven't been accessed recently can be automatically paused or deleted
     * to conserve resources. Access tracking enables intelligent resource management policies.
     *
     * @param {string} labId - The lab identifier
     * @returns {Promise<void>}
     */
    async updateLabAccess(labId) {
        try {
            await fetch(`${this.labApiBase}/labs/${labId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });
        } catch (error) {
            console.error('Error updating lab access time:', error);
        }
    }
}

// Create global instance
const labLifecycleManager = new LabLifecycleManager();

export { labLifecycleManager, LabLifecycleManager };