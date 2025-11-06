/**
 * Dependency Injection Container
 *
 * BUSINESS CONTEXT:
 * In a complex educational platform with multiple microservices and rich UI interactions,
 * we need a centralized way to manage dependencies between components. This prevents
 * tight coupling, makes testing easier, and allows us to swap implementations without
 * changing consuming code.
 *
 * SOLID PRINCIPLES APPLIED:
 *
 * 1. Single Responsibility Principle (SRP):
 *    - Container has ONE job: manage service registration and resolution
 *    - Does not know about specific services or their implementations
 *
 * 2. Open/Closed Principle (OCP):
 *    - Open for extension: can register new services without modifying Container code
 *    - Closed for modification: Container logic doesn't change when adding services
 *
 * 3. Liskov Substitution Principle (LSP):
 *    - Services registered with same name are interchangeable
 *    - Mock implementations can replace real ones (critical for testing)
 *
 * 4. Interface Segregation Principle (ISP):
 *    - Container exposes minimal interface: register(), get(), has()
 *    - Clients only depend on what they need
 *
 * 5. Dependency Inversion Principle (DIP):
 *    - High-level modules (controllers, UI components) depend on this abstraction
 *    - Low-level modules (API clients, storage) are injected through this abstraction
 *    - Both depend on the Container abstraction, not on each other
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses ES6 Map for O(1) service lookup
 * - Factory pattern: services are created by factory functions
 * - Singleton support: services can be registered as singletons (created once, reused)
 * - Transient support: services can be created fresh on each get() call
 * - Lazy initialization: services only created when first requested
 *
 * USAGE EXAMPLE:
 *
 * ```javascript
 * // Setup (in main.js or bootstrap.js)
 * import { Container } from './core/Container.js';
 *
 * const container = new Container();
 *
 * // Register services
 * container.register('apiClient', (c) => new ApiClient(), true); // singleton
 * container.register('authService', (c) => new AuthService(c.get('apiClient')), true);
 * container.register('notificationService', (c) => new NotificationService(), true);
 *
 * // Register controllers (transient - new instance each time)
 * container.register('projectController', (c) => {
 *     return new ProjectController(
 *         c.get('apiClient'),
 *         c.get('notificationService')
 *     );
 * }, false); // false = transient
 *
 * // In your code
 * const projectController = container.get('projectController');
 * projectController.createProject(data);
 * ```
 *
 * TESTING BENEFITS:
 *
 * ```javascript
 * // In tests, replace real services with mocks
 * const testContainer = new Container();
 * testContainer.register('apiClient', () => new MockApiClient());
 * testContainer.register('authService', () => new MockAuthService());
 *
 * // Controller gets mocked dependencies automatically
 * const controller = testContainer.get('projectController');
 * // Test without hitting real API
 * ```
 *
 * @class Container
 * @example
 * const container = new Container();
 * container.register('myService', () => new MyService(), true);
 * const service = container.get('myService');
 */
export class Container {
    /**
     * Create a new dependency injection container
     *
     * @constructor
     */
    constructor() {
        /**
         * Map of service name -> service definition
         * Service definition: { factory: Function, singleton: boolean }
         * @private
         * @type {Map<string, {factory: Function, singleton: boolean}>}
         */
        this._services = new Map();

        /**
         * Map of singleton service name -> service instance
         * Only populated for singleton services after first get()
         * @private
         * @type {Map<string, any>}
         */
        this._singletons = new Map();

        /**
         * Set of service names currently being resolved
         * Used to detect circular dependencies
         * @private
         * @type {Set<string>}
         */
        this._resolving = new Set();
    }

    /**
     * Register a service with the container
     *
     * DESIGN PATTERN: Factory Pattern
     * The factory function allows lazy initialization - services are only created
     * when first requested, not at registration time. This improves startup performance
     * and allows services to have dependencies that are registered later.
     *
     * @param {string} name - Unique identifier for the service
     * @param {Function} factory - Factory function that creates the service
     *                             Receives the container as parameter for resolving dependencies
     * @param {boolean} [singleton=false] - If true, service is created once and reused
     *                                      If false, new instance created on each get()
     * @returns {Container} Returns this for method chaining
     *
     * @example
     * // Singleton service (created once)
     * container.register('config', () => new Config(), true);
     *
     * @example
     * // Service with dependencies
     * container.register('userService', (c) => {
     *     return new UserService(c.get('apiClient'), c.get('authService'));
     * }, true);
     *
     * @example
     * // Transient service (new instance each time)
     * container.register('formValidator', () => new FormValidator(), false);
     *
     * @throws {Error} If service name is empty
     * @throws {Error} If factory is not a function
     */
    register(name, factory, singleton = false) {
        // Validation
        if (!name || typeof name !== 'string') {
            throw new Error('Service name must be a non-empty string');
        }

        if (typeof factory !== 'function') {
            throw new Error(`Factory for service '${name}' must be a function`);
        }

        // Warn if overwriting existing service (helps catch configuration bugs)
        if (this._services.has(name)) {
            console.warn(`Warning: Overwriting existing service '${name}'`);
            // Also clear singleton instance if it exists
            this._singletons.delete(name);
        }

        // Store service definition
        this._services.set(name, { factory, singleton });

        // Return this for method chaining
        return this;
    }

    /**
     * Resolve and return a service instance
     *
     * LAZY INITIALIZATION:
     * Services are only created when first requested. This improves startup performance
     * and allows services to be registered in any order.
     *
     * SINGLETON PATTERN:
     * Singleton services are cached after first creation and reused on subsequent calls.
     *
     * CIRCULAR DEPENDENCY DETECTION:
     * Tracks services being resolved to detect and prevent circular dependencies.
     *
     * @param {string} name - Service identifier
     * @returns {any} The service instance
     *
     * @example
     * const apiClient = container.get('apiClient');
     *
     * @throws {Error} If service is not registered
     * @throws {Error} If circular dependency is detected
     */
    get(name) {
        // Check if service is registered
        if (!this._services.has(name)) {
            throw new Error(
                `Service '${name}' is not registered. ` +
                `Available services: ${Array.from(this._services.keys()).join(', ')}`
            );
        }

        // Check for circular dependency
        if (this._resolving.has(name)) {
            const resolvingChain = Array.from(this._resolving).join(' -> ');
            throw new Error(
                `Circular dependency detected: ${resolvingChain} -> ${name}. ` +
                `Please refactor your services to break this cycle.`
            );
        }

        const service = this._services.get(name);

        // If singleton and already created, return cached instance
        if (service.singleton && this._singletons.has(name)) {
            return this._singletons.get(name);
        }

        // Mark as currently resolving (for circular dependency detection)
        this._resolving.add(name);

        try {
            // Create service instance by calling factory
            const instance = service.factory(this);

            // Cache singleton instances
            if (service.singleton) {
                this._singletons.set(name, instance);
            }

            return instance;
        } catch (error) {
            // Enhance error message with context
            throw new Error(
                `Failed to create service '${name}': ${error.message}. ` +
                `Check the factory function for service '${name}'.`
            );
        } finally {
            // Remove from resolving set
            this._resolving.delete(name);
        }
    }

    /**
     * Check if a service is registered
     *
     * Useful for conditional logic or feature detection
     *
     * @param {string} name - Service identifier
     * @returns {boolean} True if service is registered
     *
     * @example
     * if (container.has('advancedFeature')) {
     *     const feature = container.get('advancedFeature');
     *     feature.enable();
     * }
     */
    has(name) {
        return this._services.has(name);
    }

    /**
     * Get all registered service names
     *
     * Useful for debugging and diagnostics
     *
     * @returns {string[]} Array of service names
     *
     * @example
     * console.log('Registered services:', container.getServiceNames());
     */
    getServiceNames() {
        return Array.from(this._services.keys());
    }

    /**
     * Clear all services and singletons
     *
     * Useful for testing - allows complete reset between tests
     *
     * @example
     * afterEach(() => {
     *     container.clear();
     * });
     */
    clear() {
        this._services.clear();
        this._singletons.clear();
        this._resolving.clear();
    }

    /**
     * Create a child container that inherits parent's services
     *
     * DESIGN PATTERN: Hierarchical Dependency Injection
     * Child containers can override parent services while still having access
     * to all parent services. Useful for creating scoped containers (per-request,
     * per-component, etc.)
     *
     * @returns {Container} New child container
     *
     * @example
     * const childContainer = container.child();
     * // Child has access to all parent services
     * childContainer.get('apiClient'); // From parent
     * // But can override them
     * childContainer.register('apiClient', () => new MockApiClient());
     */
    child() {
        const childContainer = new Container();

        // Copy parent services (but not singletons - child creates its own instances)
        for (const [name, service] of this._services) {
            childContainer._services.set(name, service);
        }

        return childContainer;
    }
}

/**
 * Global container instance
 *
 * USAGE NOTE:
 * This is provided for convenience, but you can also create your own container instances.
 * In tests, you should create separate container instances to avoid test pollution.
 *
 * @type {Container}
 * @example
 * import { container } from './core/Container.js';
 * container.register('myService', () => new MyService());
 */
export const container = new Container();
