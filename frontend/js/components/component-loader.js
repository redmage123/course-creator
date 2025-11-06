/**
 * Component Loader Module
 * Single Responsibility: Load and manage HTML components dynamically
 * Following SOLID principles with dependency injection and clean interfaces
 */
export class ComponentLoader {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     */
    constructor() {
        this.loadedComponents = new Map();
        this.componentCache = new Map();
        this.loadingPromises = new Map();
        
        this.initialize();
    }

    /**
     * INITIALIZE  COMPONENT
     * PURPOSE: Initialize  component
     * WHY: Proper initialization ensures component reliability and correct state
     */
    initialize() {
        this.setupComponentDirectives();
    }

    /**
     * Load and inject HTML component into target element
     * @param {string} componentPath - Path to the component HTML file
     * @param {HTMLElement|string} target - Target element or selector
     * @param {Object} data - Data to pass to component
     */
    async loadComponent(componentPath, target, data = {}) {
        try {
            // Resolve target element
            const targetElement = typeof target === 'string' 
                ? document.querySelector(target) 
                : target;

            if (!targetElement) {
                throw new Error(`Target element not found: ${target}`);
            }

            // Check if already loading
            const loadingKey = `${componentPath}_${targetElement.id || targetElement.className}`;
            if (this.loadingPromises.has(loadingKey)) {
                return await this.loadingPromises.get(loadingKey);
            }

            // Create loading promise
            const loadingPromise = this.performComponentLoad(componentPath, targetElement, data);
            this.loadingPromises.set(loadingKey, loadingPromise);

            const result = await loadingPromise;
            
            // Clean up loading promise
            this.loadingPromises.delete(loadingKey);
            
            return result;

        } catch (error) {
            console.error(`Failed to load component ${componentPath}:`, error);
            throw error;
        }
    }

    /**
     * Perform the actual component loading operation
     *
     * PURPOSE: Internal method to fetch, cache, process, and inject HTML components
     * WHY: Separates loading logic from duplicate request prevention for cleaner code organization
     *
     * BUSINESS LOGIC:
     * - Checks in-memory cache to avoid redundant network requests
     * - Fetches component HTML if not cached
     * - Processes template variables for dynamic content
     * - Injects processed HTML into target element
     * - Initializes component-specific JavaScript functionality
     * - Dispatches events for component lifecycle hooks
     *
     * @param {string} componentPath - Path to the component HTML file
     * @param {HTMLElement} targetElement - DOM element to inject component into
     * @param {Object} data - Data object for template variable substitution
     * @returns {Promise<Object>} Component load result with path, target, and data
     * @throws {Error} If component fetch fails or target element is invalid
     */
    async performComponentLoad(componentPath, targetElement, data) {
        // Check cache first
        let componentHTML = this.componentCache.get(componentPath);
        
        if (!componentHTML) {
            // Fetch component HTML
            const response = await fetch(componentPath);
            if (!response.ok) {
                throw new Error(`Failed to fetch component: ${response.statusText}`);
            }
            
            componentHTML = await response.text();
            
            // Cache the component
            this.componentCache.set(componentPath, componentHTML);
        }

        // Process template variables
        const processedHTML = this.processTemplate(componentHTML, data);
        
        // Inject into target
        targetElement.innerHTML = processedHTML;
        
        // Track loaded component
        this.loadedComponents.set(targetElement, {
            path: componentPath,
            data: data,
            loadedAt: new Date()
        });

        // Initialize component-specific JavaScript
        await this.initializeComponentScripts(componentPath, targetElement, data);
        
        // Dispatch component loaded event
        this.dispatchComponentEvent('componentLoaded', {
            path: componentPath,
            target: targetElement,
            data: data
        });

        return {
            path: componentPath,
            target: targetElement,
            data: data
        };
    }

    /**
     * Process template variables in HTML
     * @param {string} html - HTML template
     * @param {Object} data - Data object
     */
    processTemplate(html, data) {
        return html.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return data[key] !== undefined ? data[key] : match;
        });
    }

    /**
     * Initialize component-specific scripts
     * @param {string} componentPath - Component path
     * @param {HTMLElement} targetElement - Target element
     * @param {Object} data - Component data
     */
    async initializeComponentScripts(componentPath, targetElement, data) {
        // Map component paths to their JavaScript modules
        const componentScripts = {
            'components/dashboard-header.html': () => this.initializeHeaderComponent(targetElement, data),
            'components/dashboard-sidebar.html': () => this.initializeSidebarComponent(targetElement, data),
            'components/course-overview.html': () => this.initializeOverviewComponent(targetElement, data),
            'components/course-creation.html': () => this.initializeCourseCreationComponent(targetElement, data),
            'components/course-management.html': () => this.initializeCourseManagementComponent(targetElement, data),
            'components/student-management.html': () => this.initializeStudentManagementComponent(targetElement, data),
            'components/analytics-dashboard.html': () => this.initializeAnalyticsComponent(targetElement, data)
        };

        const initFunction = componentScripts[componentPath];
        if (initFunction) {
            await initFunction();
        }
    }

    /**
     * Initialize dashboard header component
     *
     * PURPOSE: Set up header UI elements with user information
     * WHY: Headers need dynamic user data display for personalization
     *
     * BUSINESS LOGIC:
     * - Populates user name from data object
     * - Displays user role for context awareness
     * - Provides visual identity for logged-in user
     *
     * @param {HTMLElement} target - Header component DOM element
     * @param {Object} data - Component data including user information
     * @param {Object} data.user - User object with name and role properties
     * @returns {Promise<void>}
     */
    async initializeHeaderComponent(target, data) {
        // Initialize header functionality
        const userNameEl = target.querySelector('#user-name');
        const userRoleEl = target.querySelector('#user-role');
        
        if (userNameEl && data.user) {
            userNameEl.textContent = data.user.name || 'Instructor';
        }
        
        if (userRoleEl && data.user) {
            userRoleEl.textContent = data.user.role || 'Instructor';
        }
    }

    /**
     * Initialize dashboard sidebar navigation component
     *
     * PURPOSE: Set up sidebar navigation with section routing functionality
     * WHY: Sidebar navigation requires event handlers for section switching
     *
     * BUSINESS LOGIC:
     * - Attaches click event handlers to all navigation links
     * - Integrates with global dashboardNavigation system
     * - Enables single-page application routing within dashboard
     * - Prevents default link behavior for SPA navigation
     *
     * @param {HTMLElement} target - Sidebar component DOM element
     * @param {Object} data - Component data (currently unused)
     * @returns {Promise<void>}
     */
    async initializeSidebarComponent(target, data) {
        // Initialize sidebar navigation
        const navLinks = target.querySelectorAll('.nav-link[data-section]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                if (window.dashboardNavigation) {
                    window.dashboardNavigation.navigateTo(section);
                }
            });
        });
    }

    /**
     * Initialize dashboard overview component with statistics
     *
     * PURPOSE: Display course and student statistics in overview section
     * WHY: Overview dashboard requires dynamic data display for instructor insights
     *
     * BUSINESS LOGIC:
     * - Populates total courses count
     * - Displays total enrolled students
     * - Shows published courses count
     * - Displays active course instances
     * - Provides quick metrics for instructor decision-making
     *
     * @param {HTMLElement} target - Overview component DOM element
     * @param {Object} data - Component data including statistics
     * @param {Object} data.stats - Statistics object with course and student metrics
     * @param {number} data.stats.totalCourses - Total number of courses
     * @param {number} data.stats.totalStudents - Total enrolled students
     * @param {number} data.stats.publishedCourses - Number of published courses
     * @param {number} data.stats.activeInstances - Number of active course instances
     * @returns {Promise<void>}
     */
    async initializeOverviewComponent(target, data) {
        // Initialize overview statistics
        if (data.stats) {
            const statElements = {
                'total-courses': data.stats.totalCourses || 0,
                'total-students': data.stats.totalStudents || 0,
                'published-courses': data.stats.publishedCourses || 0,
                'active-instances': data.stats.activeInstances || 0
            };

            Object.entries(statElements).forEach(([id, value]) => {
                const element = target.querySelector(`#${id}`);
                if (element) {
                    element.textContent = value;
                }
            });
        }
    }

    /**
     * Initialize course creation form component
     *
     * PURPOSE: Set up course creation form with validation and submission handlers
     * WHY: Course creation requires form management and CourseManager integration
     *
     * BUSINESS LOGIC:
     * - Delegates form handling to CourseManager for separation of concerns
     * - Maintains clean architecture with single responsibility
     * - Enables AI-powered course generation workflow
     *
     * @param {HTMLElement} target - Course creation form component DOM element
     * @param {Object} data - Component data (currently unused, form managed by CourseManager)
     * @returns {Promise<void>}
     */
    async initializeCourseCreationComponent(target, data) {
        // Initialize course creation form
        const form = target.querySelector('#courseForm');
        if (form && window.courseManager) {
            // Form handling is managed by CourseManager
        }
    }

    /**
     * Initialize course management component
     *
     * PURPOSE: Refresh and display course list in management interface
     * WHY: Course management section needs up-to-date course data on load
     *
     * BUSINESS LOGIC:
     * - Triggers course data refresh from CourseManager
     * - Ensures latest course information is displayed
     * - Supports course listing, filtering, and actions
     *
     * @param {HTMLElement} target - Course management component DOM element
     * @param {Object} data - Component data (currently unused)
     * @returns {Promise<void>}
     */
    async initializeCourseManagementComponent(target, data) {
        // Initialize course management
        if (window.courseManager) {
            window.courseManager.refreshCoursesDisplay();
        }
    }

    /**
     * Initialize student management component with tab navigation
     *
     * PURPOSE: Set up student management interface with enrollment and enrolled student tabs
     * WHY: Student management requires tab-based navigation for different workflows
     *
     * BUSINESS LOGIC:
     * - Attaches click handlers to tab navigation buttons
     * - Switches between enrollment and enrolled student views
     * - Enables instructor workflow for student management
     * - Provides clear separation between enrollment actions and student tracking
     *
     * @param {HTMLElement} target - Student management component DOM element
     * @param {Object} data - Component data (currently unused)
     * @returns {Promise<void>}
     */
    async initializeStudentManagementComponent(target, data) {
        // Initialize student management
        const tabButtons = target.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.textContent.toLowerCase().includes('enrollment') ? 'enrollment' : 'enrolled';
                this.showStudentTab(tabName);
            });
        });
    }

    /**
     * Initialize analytics dashboard component
     *
     * PURPOSE: Load and display analytics data for instructor insights
     * WHY: Analytics dashboard requires data fetching and visualization setup
     *
     * BUSINESS LOGIC:
     * - Triggers analytics data loading via global function
     * - Supports performance metrics visualization
     * - Enables data-driven instruction decisions
     * - Provides insights into student progress and course effectiveness
     *
     * @param {HTMLElement} target - Analytics component DOM element
     * @param {Object} data - Component data (currently unused)
     * @returns {Promise<void>}
     */
    async initializeAnalyticsComponent(target, data) {
        // Initialize analytics dashboard
        if (typeof window.loadAnalytics === 'function') {
            window.loadAnalytics();
        }
    }

    /**
     * Show specific student management tab
     *
     * PURPOSE: Switch between enrollment and enrolled student tabs
     * WHY: Tab-based navigation requires programmatic tab switching
     *
     * BUSINESS LOGIC:
     * - Hides all tab content panels
     * - Deactivates all tab navigation buttons
     * - Shows target tab content
     * - Activates corresponding tab button
     * - Provides smooth tab transition for better UX
     *
     * @param {string} tabName - Name of tab to show ('enrollment' or 'enrolled')
     * @returns {void}
     */
    showStudentTab(tabName) {
        const tabs = document.querySelectorAll('.tab-content');
        const buttons = document.querySelectorAll('.tab-button');
        
        tabs.forEach(tab => tab.classList.remove('active'));
        buttons.forEach(button => button.classList.remove('active'));
        
        const targetTab = document.getElementById(`${tabName}-tab`);
        const targetButton = document.querySelector(`[onclick*="${tabName}"]`);
        
        if (targetTab) targetTab.classList.add('active');
        if (targetButton) targetButton.classList.add('active');
    }

    /**
     * Setup automatic component loading via data attributes
     */
    setupComponentDirectives() {
        // Look for elements with data-component attribute
        const componentElements = document.querySelectorAll('[data-component]');
        
        componentElements.forEach(async (element) => {
            const componentPath = element.getAttribute('data-component');
            const componentData = element.getAttribute('data-component-data');
            
            let data = {};
            if (componentData) {
                try {
                    data = JSON.parse(componentData);
                } catch (e) {
                    console.warn('Invalid component data JSON:', componentData);
                }
            }
            
            await this.loadComponent(componentPath, element, data);
        });
    }

    /**
     * Reload a component
     * @param {HTMLElement} targetElement - Target element
     */
    async reloadComponent(targetElement) {
        const componentInfo = this.loadedComponents.get(targetElement);
        if (componentInfo) {
            await this.loadComponent(componentInfo.path, targetElement, componentInfo.data);
        }
    }

    /**
     * Unload a component
     * @param {HTMLElement} targetElement - Target element
     */
    unloadComponent(targetElement) {
        if (this.loadedComponents.has(targetElement)) {
            targetElement.innerHTML = '';
            this.loadedComponents.delete(targetElement);
            
            this.dispatchComponentEvent('componentUnloaded', {
                target: targetElement
            });
        }
    }

    /**
     * Get loaded component info
     * @param {HTMLElement} targetElement - Target element
     */
    getComponentInfo(targetElement) {
        return this.loadedComponents.get(targetElement);
    }

    /**
     * Clear component cache
     */
    clearCache() {
        this.componentCache.clear();
    }

    /**
     * Dispatch component events
     * @param {string} eventName - Event name
     * @param {Object} detail - Event detail
     */
    dispatchComponentEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    /**
     * Batch load multiple components
     * @param {Array} components - Array of {path, target, data} objects
     */
    async loadComponents(components) {
        const promises = components.map(({ path, target, data }) => 
            this.loadComponent(path, target, data)
        );
        
        return await Promise.all(promises);
    }
}

// Global instance
let componentLoaderInstance = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    componentLoaderInstance = new ComponentLoader();
    window.componentLoader = componentLoaderInstance;
});

export default ComponentLoader;