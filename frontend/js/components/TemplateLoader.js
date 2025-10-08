/**
 * Template Loader - Dynamic HTML Component Loading
 *
 * BUSINESS CONTEXT:
 * Implements SOLID principles for dashboard modularity:
 * - Single Responsibility: Only loads and caches HTML templates
 * - Open/Closed: Extensible for new components without modification
 * - Dependency Inversion: Dashboards depend on this abstraction
 *
 * TECHNICAL IMPLEMENTATION:
 * - Async template loading with fetch API
 * - In-memory caching to prevent redundant network requests
 * - Variable substitution for dynamic content
 * - Error handling with fallbacks
 */

class TemplateLoader {
    constructor() {
        // In-memory cache for loaded templates
        this.cache = new Map();
        // Base path for component templates
        this.basePath = '/html';
    }

    /**
     * Load HTML template from file
     *
     * @param {string} templatePath - Path to template file (relative to basePath)
     * @param {boolean} useCache - Whether to use cached version (default: true)
     * @returns {Promise<string>} HTML content
     */
    async loadTemplate(templatePath, useCache = true) {
        // Check cache first
        if (useCache && this.cache.has(templatePath)) {
            return this.cache.get(templatePath);
        }

        try {
            const fullPath = `${this.basePath}/${templatePath}`;
            const response = await fetch(fullPath);

            if (!response.ok) {
                throw new Error(`Failed to load template: ${templatePath} (${response.status})`);
            }

            const html = await response.text();

            // Cache the template
            this.cache.set(templatePath, html);

            return html;
        } catch (error) {
            console.error(`TemplateLoader error loading ${templatePath}:`, error);
            return this.getErrorTemplate(templatePath, error.message);
        }
    }

    /**
     * Load template and substitute variables
     *
     * BUSINESS LOGIC:
     * Allows dynamic content injection into templates using {{variable}} syntax
     * Example: <h1>{{title}}</h1> with {title: "Dashboard"} becomes <h1>Dashboard</h1>
     *
     * @param {string} templatePath - Path to template file
     * @param {Object} variables - Variables to substitute {key: value}
     * @param {boolean} useCache - Whether to use cached version
     * @returns {Promise<string>} HTML with substituted variables
     */
    async loadTemplateWithVars(templatePath, variables = {}, useCache = true) {
        let html = await this.loadTemplate(templatePath, useCache);

        // Substitute variables using {{variableName}} syntax
        Object.entries(variables).forEach(([key, value]) => {
            const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
            html = html.replace(regex, value);
        });

        return html;
    }

    /**
     * Load multiple templates in parallel
     *
     * PERFORMANCE OPTIMIZATION:
     * Loads all templates concurrently for faster page load
     *
     * @param {Array<string>} templatePaths - Array of template paths
     * @returns {Promise<Object>} Object with {path: html} mappings
     */
    async loadMultiple(templatePaths) {
        const promises = templatePaths.map(path =>
            this.loadTemplate(path).then(html => ({ path, html }))
        );

        const results = await Promise.all(promises);

        // Convert array to object for easy access
        return results.reduce((acc, { path, html }) => {
            acc[path] = html;
            return acc;
        }, {});
    }

    /**
     * Inject template into DOM element
     *
     * @param {string} selector - CSS selector for target element
     * @param {string} templatePath - Path to template
     * @param {Object} variables - Variables to substitute
     * @returns {Promise<HTMLElement>} The target element
     */
    async injectTemplate(selector, templatePath, variables = {}) {
        const element = document.querySelector(selector);

        if (!element) {
            console.error(`TemplateLoader: Element not found: ${selector}`);
            return null;
        }

        const html = await this.loadTemplateWithVars(templatePath, variables);
        element.innerHTML = html;

        return element;
    }

    /**
     * Append template to DOM element
     *
     * @param {string} selector - CSS selector for target element
     * @param {string} templatePath - Path to template
     * @param {Object} variables - Variables to substitute
     * @returns {Promise<HTMLElement>} The target element
     */
    async appendTemplate(selector, templatePath, variables = {}) {
        const element = document.querySelector(selector);

        if (!element) {
            console.error(`TemplateLoader: Element not found: ${selector}`);
            return null;
        }

        const html = await this.loadTemplateWithVars(templatePath, variables);
        element.insertAdjacentHTML('beforeend', html);

        return element;
    }

    /**
     * Clear template cache
     *
     * BUSINESS LOGIC:
     * Use when templates need to be reloaded (e.g., during development)
     *
     * @param {string} templatePath - Optional specific template to clear
     */
    clearCache(templatePath = null) {
        if (templatePath) {
            this.cache.delete(templatePath);
        } else {
            this.cache.clear();
        }
    }

    /**
     * Get error template HTML
     *
     * @param {string} templatePath - Path that failed to load
     * @param {string} message - Error message
     * @returns {string} Error HTML
     */
    getErrorTemplate(templatePath, message) {
        return `
            <div style="padding: var(--space-6); background: #fee2e2; border: 1px solid #ef4444; border-radius: var(--radius-lg); color: #991b1b;">
                <h3 style="margin: 0 0 var(--space-2); font-size: var(--text-lg);">
                    <i class="fas fa-exclamation-triangle"></i>
                    Template Load Error
                </h3>
                <p style="margin: 0 0 var(--space-2); font-size: var(--text-sm);">
                    <strong>Template:</strong> ${templatePath}
                </p>
                <p style="margin: 0; font-size: var(--text-sm);">
                    <strong>Error:</strong> ${message}
                </p>
            </div>
        `;
    }

    /**
     * Preload templates for faster access
     *
     * PERFORMANCE OPTIMIZATION:
     * Preload common templates during initial page load
     *
     * @param {Array<string>} templatePaths - Templates to preload
     */
    async preload(templatePaths) {
        await this.loadMultiple(templatePaths);
        console.log(`TemplateLoader: Preloaded ${templatePaths.length} templates`);
    }
}

// Create global singleton instance
window.templateLoader = window.templateLoader || new TemplateLoader();

// Export for module usage
export default TemplateLoader;
