/**
 * Application Bootstrap
 *
 * BUSINESS CONTEXT:
 * Initializes the Course Creator Platform frontend application with proper
 * dependency injection, service registration, and environment configuration.
 * This is the single entry point for setting up the entire frontend infrastructure.
 *
 * SOLID PRINCIPLES APPLIED:
 *
 * 1. Dependency Inversion Principle (DIP):
 *    - Application depends on Container abstraction, not concrete implementations
 *    - Services are injected rather than hard-coded
 *
 * 2. Single Responsibility Principle (SRP):
 *    - Bootstrap has ONE job: initialize and wire up the application
 *    - Each service registration is separate and focused
 *
 * 3. Open/Closed Principle (OCP):
 *    - New services can be added without modifying bootstrap logic
 *    - Just register new services in the appropriate section
 *
 * ARCHITECTURE BENEFITS:
 * - Centralized dependency management
 * - Easy testing with mock services
 * - Clear application initialization flow
 * - No global namespace pollution
 * - Explicit dependency declarations
 *
 * MIGRATION FROM WINDOW GLOBALS:
 * Before: window.MyService = new MyService()
 * After:  container.register('myService', () => new MyService(), true)
 * Usage:  const myService = container.get('myService')
 *
 * @module core/bootstrap
 */
import { container } from './Container.js';

/**
 * Register core infrastructure services
 *
 * These are fundamental services needed by all other parts of the application:
 * - Configuration management
 * - Authentication
 * - API communication
 * - Notification system
 * - Session management
 */
function registerInfrastructureServices() {
    // Configuration Service (singleton)
    container.register('config', () => {
        return {
            apiBaseUrl: window.location.origin,
            environment: 'production', // Could read from env variable
            features: {
                analytics: true,
                ai_assistant: true,
                labs: true
            }
        };
    }, true);

    // Notification Service (singleton)
    container.register('notificationService', (c) => {
        // Import dynamically to avoid circular dependencies
        return {
    /**
     * EXECUTE SUCCESS OPERATION
     * PURPOSE: Execute success operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} message - Message parameter
     */
            success: (message) => {
                console.log(`[SUCCESS] ${message}`);
                // TODO: Implement actual notification UI
            },
    /**
     * EXECUTE ERROR OPERATION
     * PURPOSE: Execute error operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} message - Message parameter
     */
            error: (message) => {
                console.error(`[ERROR] ${message}`);
                // TODO: Implement actual notification UI
            },
    /**
     * EXECUTE INFO OPERATION
     * PURPOSE: Execute info operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} message - Message parameter
     */
            info: (message) => {
                console.log(`[INFO] ${message}`);
                // TODO: Implement actual notification UI
            }
        };
    }, true);

    // HTTP Client (singleton)
    container.register('httpClient', (c) => {
        const config = c.get('config');
        return {
    /**
     * RETRIEVE  INFORMATION
     * PURPOSE: Retrieve  information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {*} url - Url parameter
     * @param {Object} options - Configuration options
     *
     * @returns {Promise<Object>} Promise resolving to requested data
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            get: async (url, options = {}) => {
                const response = await fetch(`${config.apiBaseUrl}${url}`, {
                    ...options,
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    }
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            },
    /**
     * EXECUTE POST OPERATION
     * PURPOSE: Execute post operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} url - Url parameter
     * @param {Object} data - Data object
     * @param {Object} options - Configuration options
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            post: async (url, data, options = {}) => {
                const response = await fetch(`${config.apiBaseUrl}${url}`, {
                    ...options,
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    body: JSON.stringify(data)
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            },
    /**
     * EXECUTE PUT OPERATION
     * PURPOSE: Execute put operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} url - Url parameter
     * @param {Object} data - Data object
     * @param {Object} options - Configuration options
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            put: async (url, data, options = {}) => {
                const response = await fetch(`${config.apiBaseUrl}${url}`, {
                    ...options,
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    body: JSON.stringify(data)
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            },
    /**
     * REMOVE  FROM SYSTEM
     * PURPOSE: Remove  from system
     * WHY: Manages resource cleanup and data consistency
     *
     * @param {*} url - Url parameter
     * @param {Object} options - Configuration options
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            delete: async (url, options = {}) => {
                const response = await fetch(`${config.apiBaseUrl}${url}`, {
                    ...options,
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    }
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            }
        };
    }, true);

    // Auth Service (singleton)
    container.register('authService', (c) => {
        const httpClient = c.get('httpClient');
        const notificationService = c.get('notificationService');

        return {
    /**
     * RETRIEVE TOKEN INFORMATION
     * PURPOSE: Retrieve token information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
            getToken: () => {
                return localStorage.getItem('authToken');
            },
    /**
     * SET TOKEN VALUE
     * PURPOSE: Set token value
     * WHY: Maintains data integrity through controlled mutation
     *
     * @param {*} token - Token parameter
     */
            setToken: (token) => {
                localStorage.setItem('authToken', token);
            },
    /**
     * REMOVE TOKEN FROM SYSTEM
     * PURPOSE: Remove token from system
     * WHY: Manages resource cleanup and data consistency
     */
            removeToken: () => {
                localStorage.removeItem('authToken');
            },
    /**
     * EXECUTE ISAUTHENTICATED OPERATION
     * PURPOSE: Execute isAuthenticated operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {boolean} True if condition is met, false otherwise
     */
            isAuthenticated: () => {
                const token = localStorage.getItem('authToken');
                return token !== null && token !== '';
            },
    /**
     * RETRIEVE CURRENT USER INFORMATION
     * PURPOSE: Retrieve current user information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Promise<Object>} Promise resolving to requested data
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            getCurrentUser: async () => {
                try {
                    const token = localStorage.getItem('authToken');
                    if (!token) {
                        throw new Error('No authentication token');
                    }
                    return await httpClient.get('/api/v1/users/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                } catch (error) {
                    notificationService.error('Failed to get current user');
                    throw error;
                }
            },
    /**
     * EXECUTE LOGIN OPERATION
     * PURPOSE: Execute login operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} username - Name value
     * @param {*} password - Password parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            login: async (username, password) => {
                try {
                    const response = await httpClient.post('/api/v1/auth/login', {
                        username,
                        password
                    });
                    if (response.token) {
                        localStorage.setItem('authToken', response.token);
                        notificationService.success('Login successful');
                        return response;
                    }
                    throw new Error('No token received');
                } catch (error) {
                    notificationService.error('Login failed');
                    throw error;
                }
            },
    /**
     * EXECUTE LOGOUT OPERATION
     * PURPOSE: Execute logout operation
     * WHY: Implements required business logic for system functionality
     */
            logout: () => {
                localStorage.removeItem('authToken');
                notificationService.info('Logged out successfully');
                window.location.href = '/';
            }
        };
    }, true);

    // Session Manager (singleton)
    container.register('sessionManager', (c) => {
        const authService = c.get('authService');

        return {
    /**
     * EXECUTE STARTSESSION OPERATION
     * PURPOSE: Execute startSession operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} user - User parameter
     */
            startSession: (user) => {
                sessionStorage.setItem('currentUser', JSON.stringify(user));
                sessionStorage.setItem('sessionStart', new Date().toISOString());
            },
    /**
     * EXECUTE ENDSESSION OPERATION
     * PURPOSE: Execute endSession operation
     * WHY: Implements required business logic for system functionality
     */
            endSession: () => {
                sessionStorage.removeItem('currentUser');
                sessionStorage.removeItem('sessionStart');
                authService.logout();
            },
    /**
     * RETRIEVE CURRENT SESSION INFORMATION
     * PURPOSE: Retrieve current session information
     * WHY: Provides controlled access to internal data and state
     *
     * @returns {Object|null} Retrieved data or null if not found
     */
            getCurrentSession: () => {
                const userStr = sessionStorage.getItem('currentUser');
                return userStr ? JSON.parse(userStr) : null;
            },
    /**
     * EXECUTE ISSESSIONACTIVE OPERATION
     * PURPOSE: Execute isSessionActive operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {boolean} True if condition is met, false otherwise
     */
            isSessionActive: () => {
                return sessionStorage.getItem('currentUser') !== null;
            }
        };
    }, true);
}

/**
 * Register application services
 *
 * These are business logic services for specific features:
 * - Course management
 * - Student management
 * - Analytics
 * - Labs
 * - Quiz management
 */
function registerApplicationServices() {
    // Project Service (singleton)
    container.register('projectService', (c) => {
        const httpClient = c.get('httpClient');
        const authService = c.get('authService');
        const notificationService = c.get('notificationService');

        return {
    /**
     * EXECUTE LIST OPERATION
     * PURPOSE: Execute list operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} organizationId - Organizationid parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            list: async (organizationId) => {
                try {
                    const token = authService.getToken();
                    return await httpClient.get(
                        `/api/v1/organizations/${organizationId}/projects`,
                        { headers: { 'Authorization': `Bearer ${token}` } }
                    );
                } catch (error) {
                    notificationService.error('Failed to load projects');
                    throw error;
                }
            },
    /**
     * CREATE NEW  INSTANCE
     * PURPOSE: Create new  instance
     * WHY: Factory method pattern for consistent object creation
     *
     * @param {string|number} organizationId - Organizationid parameter
     * @param {*} projectData - Projectdata parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            create: async (organizationId, projectData) => {
                try {
                    const token = authService.getToken();
                    const response = await httpClient.post(
                        `/api/v1/organizations/${organizationId}/projects`,
                        projectData,
                        { headers: { 'Authorization': `Bearer ${token}` } }
                    );
                    notificationService.success('Project created successfully');
                    return response;
                } catch (error) {
                    notificationService.error('Failed to create project');
                    throw error;
                }
            }
        };
    }, true);

    // Course Service (singleton)
    container.register('courseService', (c) => {
        const httpClient = c.get('httpClient');
        const authService = c.get('authService');
        const notificationService = c.get('notificationService');

        return {
    /**
     * EXECUTE LIST OPERATION
     * PURPOSE: Execute list operation
     * WHY: Implements required business logic for system functionality
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            list: async () => {
                try {
                    const token = authService.getToken();
                    return await httpClient.get('/api/v1/courses', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                } catch (error) {
                    notificationService.error('Failed to load courses');
                    throw error;
                }
            },
    /**
     * RETRIEVE  INFORMATION
     * PURPOSE: Retrieve  information
     * WHY: Provides controlled access to internal data and state
     *
     * @param {string|number} courseId - Unique identifier
     *
     * @returns {Promise<Object>} Promise resolving to requested data
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            get: async (courseId) => {
                try {
                    const token = authService.getToken();
                    return await httpClient.get(`/api/v1/courses/${courseId}`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                } catch (error) {
                    notificationService.error('Failed to load course');
                    throw error;
                }
            },
    /**
     * CREATE NEW  INSTANCE
     * PURPOSE: Create new  instance
     * WHY: Factory method pattern for consistent object creation
     *
     * @param {*} courseData - Coursedata parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            create: async (courseData) => {
                try {
                    const token = authService.getToken();
                    const response = await httpClient.post(
                        '/api/v1/courses',
                        courseData,
                        { headers: { 'Authorization': `Bearer ${token}` } }
                    );
                    notificationService.success('Course created successfully');
                    return response;
                } catch (error) {
                    notificationService.error('Failed to create course');
                    throw error;
                }
            }
        };
    }, true);

    // Track Service (singleton)
    container.register('trackService', (c) => {
        const httpClient = c.get('httpClient');
        const authService = c.get('authService');
        const notificationService = c.get('notificationService');

        return {
    /**
     * EXECUTE LIST OPERATION
     * PURPOSE: Execute list operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} projectId - Unique identifier
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            list: async (projectId) => {
                try {
                    const token = authService.getToken();
                    return await httpClient.get(`/api/v1/projects/${projectId}/tracks`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                } catch (error) {
                    notificationService.error('Failed to load tracks');
                    throw error;
                }
            },
    /**
     * CREATE NEW  INSTANCE
     * PURPOSE: Create new  instance
     * WHY: Factory method pattern for consistent object creation
     *
     * @param {*} trackData - Trackdata parameter
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            create: async (trackData) => {
                try {
                    const token = authService.getToken();
                    const response = await httpClient.post(
                        '/api/v1/tracks',
                        trackData,
                        { headers: { 'Authorization': `Bearer ${token}` } }
                    );
                    notificationService.success('Track created successfully');
                    return response;
                } catch (error) {
                    notificationService.error('Failed to create track');
                    throw error;
                }
            }
        };
    }, true);
}

/**
 * Register UI controllers
 *
 * These are transient (non-singleton) because they manage UI state
 * and should be created fresh when needed.
 */
function registerControllers() {
    // Dashboard Controller (transient)
    container.register('dashboardController', (c) => {
        const courseService = c.get('courseService');
        const projectService = c.get('projectService');
        const authService = c.get('authService');

        return {
    /**
     * INITIALIZE  COMPONENT
     * PURPOSE: Initialize  component
     * WHY: Proper initialization ensures component reliability and correct state
     *
     * @returns {Promise} Promise resolving when operation completes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            init: async () => {
                // Load user data
                const user = await authService.getCurrentUser();

                // Load dashboard data based on role
                if (user.role === 'instructor') {
                    const courses = await courseService.list();
                    // Render instructor dashboard
                } else if (user.role === 'student') {
                    const courses = await courseService.list();
                    // Render student dashboard
                }
            }
        };
    }, false); // transient - new instance each time
}

/**
 * Initialize the application
 *
 * This is the main entry point called from HTML pages.
 * Registers all services and performs initial setup.
 *
 * @returns {Container} The initialized DI container
 *
 * @example
 * // In your HTML
 * <script type="module">
 *   import { initializeApp } from './js/core/bootstrap.js';
 *   const container = initializeApp();
 *
 *   // Get services from container
 *   const authService = container.get('authService');
 *   authService.login('user', 'pass');
 * </script>
 */
export function initializeApp() {
    console.log('=== Initializing Course Creator Platform ===');

    // Register all services
    registerInfrastructureServices();
    registerApplicationServices();
    registerControllers();

    console.log(`✓ Registered ${container.getServiceNames().length} services`);
    console.log('✓ Application initialized');

    return container;
}

/**
 * Export container for direct access
 * Useful for debugging and console access
 */
export { container };
