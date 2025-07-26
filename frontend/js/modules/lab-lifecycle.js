/**
 * Lab Lifecycle Manager
 * Handles automatic lab container lifecycle management based on user authentication events
 */

import { CONFIG } from '../config.js';
import { showNotification } from './notifications.js';

class LabLifecycleManager {
    constructor() {
        this.labApiBase = 'http://localhost:8006';
        this.currentUser = null;
        this.enrolledCourses = [];
        this.activeLabs = {};
        this.labCheckInterval = null;
        this.isInitialized = false;
    }

    /**
     * Initialize the lab lifecycle manager
     */
    async initialize(user) {
        if (this.isInitialized) {
            return;
        }

        this.currentUser = user;
        console.log('Initializing Lab Lifecycle Manager for user:', user);

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
            console.log('Lab Lifecycle Manager initialized successfully');
            
        } catch (error) {
            console.error('Error initializing Lab Lifecycle Manager:', error);
        }
    }

    /**
     * Load enrolled courses for the current user
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
            
            console.log('Loaded enrolled courses:', this.enrolledCourses);
            
        } catch (error) {
            console.error('Error loading enrolled courses:', error);
            this.enrolledCourses = [];
        }
    }

    /**
     * Initialize labs for all enrolled courses
     */
    async initializeUserLabs() {
        if (!this.currentUser || this.enrolledCourses.length === 0) {
            console.log('No enrolled courses found, skipping lab initialization');
            return;
        }

        console.log('Initializing labs for enrolled courses...');

        for (const course of this.enrolledCourses) {
            try {
                await this.getOrCreateStudentLab(course.id);
            } catch (error) {
                console.error(`Error initializing lab for course ${course.id}:`, error);
            }
        }
    }

    /**
     * Get or create a student lab for a specific course
     */
    async getOrCreateStudentLab(courseId) {
        try {
            const requestData = {
                user_id: this.currentUser.id || this.currentUser.email,
                course_id: courseId
            };

            console.log('Getting or creating student lab:', requestData);

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
                
                console.log(`Lab initialized for course ${courseId}:`, labData);
                
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
     * Poll lab status until it's ready
     */
    async pollLabStatus(labId, courseId) {
        const maxAttempts = 30; // 5 minutes with 10-second intervals
        let attempts = 0;

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
     * Pause all active labs (called on logout or window unload)
     */
    async pauseAllLabs() {
        console.log('Pausing all active labs...');

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
                        console.log(`Lab paused for course ${courseId}`);
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
        console.log('All labs paused');
    }

    /**
     * Resume all paused labs (called on login)
     */
    async resumeAllLabs() {
        console.log('Resuming all paused labs...');

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
                        console.log(`Lab resumed for course ${courseId}`);
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
        console.log('All labs resumed');
    }

    /**
     * Get lab access URL for a specific course
     */
    getLabAccessUrl(courseId) {
        const lab = this.activeLabs[courseId];
        if (lab && lab.access_url && lab.status === 'running') {
            return lab.access_url;
        }
        return null;
    }

    /**
     * Check if lab is ready for a specific course
     */
    isLabReady(courseId) {
        const lab = this.activeLabs[courseId];
        return lab && lab.status === 'running';
    }

    /**
     * Get lab status for a specific course
     */
    getLabStatus(courseId) {
        const lab = this.activeLabs[courseId];
        return lab ? lab.status : 'not_created';
    }

    /**
     * Start periodic health checks for all active labs
     */
    startLabHealthChecks() {
        // Check lab health every 5 minutes
        this.labCheckInterval = setInterval(async () => {
            await this.performLabHealthCheck();
        }, 5 * 60 * 1000);

        console.log('Lab health checks started');
    }

    /**
     * Stop lab health checks
     */
    stopLabHealthChecks() {
        if (this.labCheckInterval) {
            clearInterval(this.labCheckInterval);
            this.labCheckInterval = null;
            console.log('Lab health checks stopped');
        }
    }

    /**
     * Perform health check on all active labs
     */
    async performLabHealthCheck() {
        console.log('Performing lab health check...');

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
     * Set up window unload handler to pause labs when user leaves
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
     * Quick pause all labs using sendBeacon for reliability during page unload
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
     * Clean up resources and pause all labs
     */
    async cleanup() {
        console.log('Cleaning up Lab Lifecycle Manager...');
        
        this.stopLabHealthChecks();
        await this.pauseAllLabs();
        
        this.activeLabs = {};
        this.enrolledCourses = [];
        this.currentUser = null;
        this.isInitialized = false;
        
        console.log('Lab Lifecycle Manager cleaned up');
    }

    /**
     * Update enrolled courses (called when student enrolls in new course)
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
     * Access a lab for a specific course
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
     * Resume a specific lab
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
     * Update lab last accessed time
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