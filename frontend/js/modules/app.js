/**
 * Main Application Module
 * Initializes and coordinates all other modules
 */

import { Auth } from './auth.js';
import { Navigation } from './navigation.js';
import { showNotification } from './notifications.js';
import UIComponents from './ui-components.js';
import { ActivityTracker } from './activity-tracker.js';
import configManager from './config-manager.js';
import assetCacheManager from './asset-cache.js';

class App {
    constructor() {
        this.initialized = false;
        this.currentPage = this.getCurrentPage();
        this.configManager = configManager;
        this.assetCacheManager = assetCacheManager;
        
        // Bind methods
        this.init = this.init.bind(this);
        this.handleGlobalError = this.handleGlobalError.bind(this);
        this.handleUnhandledRejection = this.handleUnhandledRejection.bind(this);
        this.setupGlobalHandlers = this.setupGlobalHandlers.bind(this);
        this.setupGlobalExports = this.setupGlobalExports.bind(this);
    }

    /**
     * Get current page filename
     */
    getCurrentPage() {
        return window.location.pathname.split('/').pop() || 'index.html';
    }

    /**
     * Initialize the application
     */
    async init() {
        if (this.initialized) return;

        try {
            console.log('Initializing Course Creator Application with advanced caching...');
            
            // Initialize configuration and asset caching first
            await this._initializePerformanceOptimizations();
            
            // Setup global error handlers
            this.setupGlobalHandlers();
            
            // Initialize authentication
            Auth.initializeAuth();
            
            // Initialize navigation
            Navigation.init();
            
            // Initialize activity tracking for dashboard pages
            if (this.currentPage.includes('dashboard')) {
                this.activityTracker = new ActivityTracker();
                this.activityTracker.start();
            }
            
            // Setup global function exports for backward compatibility
            this.setupGlobalExports();
            
            // Page-specific initialization
            this.initializePage();
            
            // Preload page-specific assets
            await this._preloadPageAssets();
            
            this.initialized = true;
            console.log('Course Creator Application initialized successfully');
            
        } catch (error) {
            console.error('Error initializing application:', error);
            this.handleGlobalError(error);
        }
    }

    /**
     * Setup global error handlers
     */
    setupGlobalHandlers() {
        // Global error handler
        window.addEventListener('error', this.handleGlobalError);
        
        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', this.handleUnhandledRejection);
        
        // Visibility change handler for activity tracking
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && Auth.isAuthenticated()) {
                Auth.activityTracker.trackActivity();
            }
        });
        
        // ServiceWorker message handler for updates
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'SW_UPDATED') {
                    console.log('ServiceWorker updated to version:', event.data.version);
                }
            });
        }
    }

    /**
     * Handle global JavaScript errors
     */
    handleGlobalError(event) {
        const error = event.error || event;
        console.error('Global error caught:', error);
        
        // Log error details
        const errorDetails = {
            message: error.message || event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: error.stack
        };
        
        // Store error in localStorage for debugging
        this.logError('JavaScript Error', errorDetails);
        
        // Show user-friendly error notification
        if (this.initialized) {
            showNotification(
                'An unexpected error occurred. Please refresh the page if the problem persists.',
                'error',
                { timeout: 8000 }
            );
        }
    }

    /**
     * Handle unhandled promise rejections
     */
    handleUnhandledRejection(event) {
        console.error('Unhandled promise rejection:', event.reason);
        
        this.logError('Unhandled Promise Rejection', {
            reason: event.reason?.toString(),
            stack: event.reason?.stack
        });
        
        // Show user-friendly error notification
        if (this.initialized) {
            showNotification(
                'A network or processing error occurred. Please try again.',
                'error',
                { timeout: 6000 }
            );
        }
    }

    /**
     * Log error to localStorage for debugging
     */
    logError(type, details) {
        const timestamp = new Date().toISOString();
        const errorLog = {
            timestamp,
            type,
            details,
            page: this.currentPage,
            userAgent: navigator.userAgent
        };
        
        try {
            let logs = [];
            const existing = localStorage.getItem('errorLogs');
            if (existing) {
                logs = JSON.parse(existing);
            }
            
            logs.push(errorLog);
            
            // Keep only last 20 logs
            if (logs.length > 20) {
                logs = logs.slice(-20);
            }
            
            localStorage.setItem('errorLogs', JSON.stringify(logs));
        } catch (e) {
            console.error('Failed to log error to localStorage:', e);
        }
    }

    /**
     * Setup global function exports for backward compatibility
     */
    setupGlobalExports() {
        // Auth functions
        window.getCurrentUser = () => Auth.getCurrentUser();
        window.logout = async () => {
            const result = await Auth.logout();
            if (result.success) {
                showNotification('Logged out successfully', 'success');
                if (this.currentPage.includes('dashboard') || this.currentPage.includes('admin')) {
                    window.location.href = 'html/index.html';
                } else {
                    Navigation.updateAccountSection();
                    Navigation.updateNavigation();
                    Navigation.showHome();
                }
            }
        };
        
        // Navigation functions
        window.showHome = () => Navigation.showHome();
        window.showLogin = () => Navigation.showLogin();
        window.showRegister = () => Navigation.showRegister();
        window.showProfile = () => Navigation.showProfile();
        window.showSettings = () => Navigation.showSettings();
        window.showHelp = () => Navigation.showHelp();
        window.showPasswordReset = () => Navigation.showPasswordReset();
        
        // UI functions
        window.togglePasswordVisibility = (inputId, buttonId) => {
            const input = document.getElementById(inputId);
            const button = document.getElementById(buttonId);
            
            if (input && button) {
                const icon = button.querySelector('i');
                if (input.type === 'password') {
                    input.type = 'text';
                    if (icon) {
                        icon.className = 'fas fa-eye-slash';
                    }
                    button.title = 'Hide password';
                } else {
                    input.type = 'password';
                    if (icon) {
                        icon.className = 'fas fa-eye';
                    }
                    button.title = 'Show password';
                }
            }
        };
        
        // Account dropdown functions
        window.toggleAccountDropdown = () => {
            const accountMenu = document.getElementById('accountMenu');
            if (accountMenu) {
                const isVisible = accountMenu.style.display === 'block' && 
                                 accountMenu.style.visibility === 'visible';
                
                if (isVisible) {
                    accountMenu.style.display = 'none';
                    accountMenu.style.visibility = 'hidden';
                } else {
                    accountMenu.style.display = 'block';
                    accountMenu.style.visibility = 'visible';
                    accountMenu.style.opacity = '1';
                    accountMenu.style.position = 'absolute';
                    accountMenu.style.top = '100%';
                    accountMenu.style.right = '0';
                    accountMenu.style.zIndex = '9999';
                    accountMenu.style.background = 'white';
                    accountMenu.style.border = '1px solid #ccc';
                    accountMenu.style.borderRadius = '8px';
                    accountMenu.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                    accountMenu.style.minWidth = '200px';
                    accountMenu.style.padding = '0.5rem 0';
                    accountMenu.style.marginTop = '5px';
                }
            }
        };
        
        // Modal functions
        window.showLoginModal = () => Navigation.showLogin();
        window.showRegisterModal = () => Navigation.showRegister();
        
        // Course loading function
        window.loadCourses = () => {
            const currentUser = Auth.getCurrentUser();
            if (currentUser) {
                // User is logged in, redirect to appropriate dashboard
                if (currentUser.role === 'instructor') {
                    window.location.href = 'html/instructor-dashboard.html';
                } else {
                    window.location.href = 'html/student-dashboard.html';
                }
            } else {
                // User is not logged in, show login modal
                Navigation.showLogin();
            }
        };
        
        // Session management
        window.handleSessionExpired = () => Auth.handleSessionExpired();
        window.handleInactivityTimeout = () => Auth.handleInactivityTimeout();
        
        // Activity tracking
        window.trackActivity = () => Auth.activityTracker.trackActivity();
        window.authenticatedFetch = (url, options) => Auth.authenticatedFetch(url, options);
        
        // Logout function
        window.logout = async () => {
            const result = await Auth.logout();
            if (result.success) {
                // Redirect to home page after logout
                window.location.href = 'index.html';
            }
        };
        
        // Error log viewing
        window.showErrorLogs = () => {
            try {
                const logs = localStorage.getItem('errorLogs');
                if (logs) {
                    const parsed = JSON.parse(logs);
                    parsed.forEach((log, index) => {
                    });
                    return parsed;
                } else {
                    return [];
                }
            } catch (e) {
                console.error('Error reading logs:', e);
                return [];
            }
        };
        
        // Utility functions
        window.debounce = UIComponents.debounce;
        window.throttle = UIComponents.throttle;
        window.formatDate = UIComponents.formatDate;
        window.showNotification = showNotification;
        
        // Configuration and caching functions
        window.getConfig = (key, options) => this.configManager.getConfig(key, options);
        window.setConfig = (key, value, options) => this.configManager.setConfig(key, value, options);
        window.preloadAssets = (assets) => this.assetCacheManager.preloadAssets(assets);
        window.getCacheStats = () => ({
            config: this.configManager.getCacheStats(),
            assets: this.assetCacheManager.getStats()
        });
    }

    /**
     * Initialize page-specific functionality
     */
    initializePage() {
        // Setup dropdown close handlers
        document.addEventListener('click', (event) => {
            const accountDropdown = document.getElementById('accountDropdown');
            const accountMenu = document.getElementById('accountMenu');
            
            if (accountMenu && accountDropdown && !accountDropdown.contains(event.target)) {
                accountMenu.style.display = 'none';
                accountMenu.style.visibility = 'hidden';
            }
        });
        
        // Prevent dropdown from closing when clicking inside
        document.addEventListener('click', (event) => {
            const accountMenu = document.getElementById('accountMenu');
            if (accountMenu && accountMenu.contains(event.target)) {
                if (!event.target.textContent.includes('Logout')) {
                    event.stopPropagation();
                }
            }
        });
    }

    /**
     * Check if current page requires authentication
     */
    requiresAuth() {
        const protectedPages = [
            'admin.html',
            'instructor-dashboard.html',
            'student-dashboard.html',
            'lab.html'
        ];
        
        return protectedPages.includes(this.currentPage);
    }

    /**
     * Get application state
     */
    getState() {
        return {
            initialized: this.initialized,
            currentPage: this.currentPage,
            isAuthenticated: Auth.isAuthenticated(),
            user: Auth.getCurrentUser(),
            performance: {
                configCache: this.configManager.getCacheStats(),
                assetCache: this.assetCacheManager.getStats()
            }
        };
    }
    
    /**
     * PERFORMANCE OPTIMIZATION INITIALIZATION
     * 
     * Initializes advanced configuration and asset caching systems for
     * improved application performance and user experience.
     */
    async _initializePerformanceOptimizations() {
        try {
            // The configuration and asset managers are already initialized
            // in their constructors, so we just need to warm critical caches
            
            // Warm configuration cache with critical settings
            const criticalConfigs = [
                'api.baseUrl',
                'ui.theme', 
                'performance.cacheEnabled',
                'security.sessionTimeout'
            ];
            
            await Promise.allSettled(
                criticalConfigs.map(key => this.configManager.getConfig(key))
            );
            
            console.log('Performance optimizations initialized successfully');
            
        } catch (error) {
            console.warn('Error initializing performance optimizations:', error);
            // Continue without advanced optimizations
        }
    }
    
    /**
     * PAGE-SPECIFIC ASSET PRELOADING
     * 
     * Preloads assets specific to the current page for improved performance.
     */
    async _preloadPageAssets() {
        try {
            const pageAssets = this._getPageSpecificAssets();
            
            if (pageAssets.length > 0) {
                console.log(`Preloading ${pageAssets.length} page-specific assets...`);
                const result = await this.assetCacheManager.preloadAssets(pageAssets);
                console.log(`Asset preloading completed: ${result.successful}/${result.total} successful`);
            }
            
        } catch (error) {
            console.warn('Error preloading page assets:', error);
        }
    }
    
    /**
     * GET PAGE-SPECIFIC ASSETS FOR PRELOADING
     */
    _getPageSpecificAssets() {
        const assets = [];
        
        switch (this.currentPage) {
            case 'student-dashboard.html':
                assets.push(
                    '/js/student-dashboard.js',
                    '/css/components/student-interface.css',
                    '/js/modules/student-file-manager.js'
                );
                break;
                
            case 'instructor-dashboard.html':
                assets.push(
                    '/js/modules/instructor-dashboard.js',
                    '/css/components/course-creation.css',
                    '/js/components/course-manager.js'
                );
                break;
                
            case 'admin.html':
                assets.push(
                    '/js/admin.js',
                    '/css/components/admin-panel.css',
                    '/js/modules/analytics-dashboard.js'
                );
                break;
                
            case 'lab.html':
            case 'lab-multi-ide.html':
                assets.push(
                    '/js/lab-integration.js',
                    '/css/components/lab-interface.css',
                    '/js/lab/lab-controller.js'
                );
                break;
        }
        
        return assets;
    }
}

// Create singleton instance
const app = new App();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', app.init);
} else {
    app.init();
}

export { app as App };
export default app;