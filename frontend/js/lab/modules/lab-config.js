/**
 * Lab Configuration Module
 * Single Responsibility: Manage lab environment configuration
 */

export class LabConfig {
    constructor() {
        this.config = {
            endpoints: {
                exercises: (courseId) => `${this.getBaseUrl()}/exercises/${courseId}`,
                syllabus: (courseId) => `${this.getBaseUrl()}/syllabus/${courseId}`,
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

    getBaseUrl() {
        // Use global CONFIG if available, otherwise fallback
        if (typeof window.CONFIG !== 'undefined' && window.CONFIG.BASE_URL) {
            return window.CONFIG.BASE_URL;
        }
        return 'http://localhost:8001'; // Default fallback
    }

    getEndpoint(name, ...args) {
        const endpoint = this.config.endpoints[name];
        return typeof endpoint === 'function' ? endpoint(...args) : endpoint;
    }

    isCommandAllowed(command) {
        return this.config.security.allowedCommands.includes(command);
    }

    isPathBlocked(path) {
        return this.config.security.blockedPaths.some(blocked => path.startsWith(blocked));
    }

    getSandboxRoot() {
        return this.config.security.sandboxRoot;
    }

    getDefaultPanelStates() {
        return { ...this.config.defaultPanelStates };
    }

    getSupportedLanguages() {
        return [...this.config.supportedLanguages];
    }

    updateConfig(updates) {
        this.config = { ...this.config, ...updates };
    }
}