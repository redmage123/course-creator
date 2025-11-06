/**
 * Lab Configuration Module
 * Single Responsibility: Manage lab environment configuration
 */
// Use global CONFIG (loaded via script tag in HTML)

export class LabConfig {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     */
    constructor() {
        this.config = {
            endpoints: {
    /**
     * EXECUTE EXERCISES OPERATION
     * PURPOSE: Execute exercises operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
                exercises: (courseId) => `${this.getBaseUrl()}/exercises/${courseId}`,
    /**
     * EXECUTE SYLLABUS OPERATION
     * PURPOSE: Execute syllabus operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} courseId - Unique identifier
     */
                syllabus: (courseId) => `${this.getBaseUrl()}/syllabus/${courseId}`,
    /**
     * EXECUTE GENERATEEXERCISES OPERATION
     * PURPOSE: Execute generateExercises operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {string|Object} Generated content
     */
                generateExercises: () => `${this.getBaseUrl()}/generate-exercises`,
                refreshLabExercises: `${this.getBaseUrl()}/lab/refresh-exercises`
            },
            security: {
                allowedCommands: ['help', 'ls', 'cd', 'pwd', 'cat', 'echo', 'mkdir', 'touch', 'clear', 'whoami', 'date', 'nano', 'vim', 'python', 'node', 'gcc'],
                blockedPaths: ['/etc', '/root', '/sys', '/proc', '/dev'],
                sandboxRoot: '/home/student'
            },
            defaultPanelStates: {
                exercises: true,
                editor: true,
                terminal: true,
                assistant: true
            },
            supportedLanguages: ['javascript', 'python', 'bash', 'c', 'cpp', 'java']
        };
    }

    /**
     * RETRIEVE BASE URL INFORMATION
     * PURPOSE: Retrieve base url information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getBaseUrl() {
        // Use CONFIG system for consistent API endpoints
        return window.CONFIG?.API_URLS.COURSE_GENERATOR;
    }

    /**
     * RETRIEVE ENDPOINT INFORMATION
     * PURPOSE: Retrieve endpoint information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} name - Name value
     * @param {*} ...args - ...args parameter
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getEndpoint(name, ...args) {
        const endpoint = this.config.endpoints[name];
        return typeof endpoint === 'function' ? endpoint(...args) : endpoint;
    }

    /**
     * EXECUTE ISCOMMANDALLOWED OPERATION
     * PURPOSE: Execute isCommandAllowed operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} command - Command parameter
     *
     * @returns {boolean} True if condition is met, false otherwise
     */
    isCommandAllowed(command) {
        return this.config.security.allowedCommands.includes(command);
    }

    /**
     * EXECUTE ISPATHBLOCKED OPERATION
     * PURPOSE: Execute isPathBlocked operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} path - Path parameter
     *
     * @returns {boolean} True if condition is met, false otherwise
     */
    isPathBlocked(path) {
        return this.config.security.blockedPaths.some(blocked => path.startsWith(blocked));
    }

    /**
     * RETRIEVE SANDBOX ROOT INFORMATION
     * PURPOSE: Retrieve sandbox root information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getSandboxRoot() {
        return this.config.security.sandboxRoot;
    }

    /**
     * RETRIEVE DEFAULT PANEL STATES INFORMATION
     * PURPOSE: Retrieve default panel states information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getDefaultPanelStates() {
        return { ...this.config.defaultPanelStates };
    }

    /**
     * RETRIEVE SUPPORTED LANGUAGES INFORMATION
     * PURPOSE: Retrieve supported languages information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
    getSupportedLanguages() {
        return [...this.config.supportedLanguages];
    }

    /**
     * UPDATE CONFIG STATE
     * PURPOSE: Update config state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @param {*} updates - Updates parameter
     *
     * @throws {Error} If operation fails or validation errors occur
     */
    updateConfig(updates) {
        this.config = { ...this.config, ...updates };
    }
}