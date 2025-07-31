/**
 * Component Loader Module
 * Single Responsibility: Load and manage HTML components dynamically
 * Following SOLID principles with dependency injection and clean interfaces
 */

export class ComponentLoader {
    constructor() {
        this.loadedComponents = new Map();
        this.componentCache = new Map();
        this.loadingPromises = new Map();
        
        this.initialize();
    }

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

    // Component-specific initialization methods
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

    async initializeCourseCreationComponent(target, data) {
        // Initialize course creation form
        const form = target.querySelector('#courseForm');
        if (form && window.courseManager) {
            // Form handling is managed by CourseManager
        }
    }

    async initializeCourseManagementComponent(target, data) {
        // Initialize course management
        if (window.courseManager) {
            window.courseManager.refreshCoursesDisplay();
        }
    }

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

    async initializeAnalyticsComponent(target, data) {
        // Initialize analytics dashboard
        if (typeof window.loadAnalytics === 'function') {
            window.loadAnalytics();
        }
    }

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