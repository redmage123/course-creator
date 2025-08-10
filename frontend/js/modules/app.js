/**
 * MAIN APPLICATION MODULE - CENTRAL COORDINATOR AND LIFECYCLE MANAGER
 * 
 * PURPOSE: Primary application controller that orchestrates all platform functionality
 * WHY: Centralized initialization ensures proper startup sequence and dependency management
 * ARCHITECTURE: Singleton pattern with lifecycle management and error handling
 * 
 * RESPONSIBILITIES:
 * - Module coordination and initialization
 * - Global error handling and logging
 * - Performance optimization and asset caching
 * - Legacy function export for backward compatibility
 * - Page-specific initialization and routing
 */

/**
 * MODULE DEPENDENCY IMPORTS
 * PURPOSE: Import all core modules that App coordinates
 * WHY: Explicit imports make dependencies clear and enable proper initialization order
 */
import { Auth } from './auth.js';                    // Authentication and session management
import { Navigation } from './navigation.js';        // Site navigation and routing
import { showNotification } from './notifications.js'; // User notification system
import UIComponents from './ui-components.js';       // Reusable UI component library
import { ActivityTracker } from './activity-tracker.js'; // User activity monitoring
import configManager from './config-manager.js';     // Configuration management system
import assetCacheManager from './asset-cache.js';    // Performance optimization and caching

/**
 * MAIN APPLICATION CLASS
 * PATTERN: Singleton class that manages the entire application lifecycle
 * WHY: Single instance ensures consistent state and prevents initialization conflicts
 */
class App {
    /**
     * CONSTRUCTOR - APPLICATION STATE INITIALIZATION
     * PURPOSE: Set up initial application state and method bindings
     * WHY: Proper method binding ensures 'this' context is preserved in callbacks
     */
    constructor() {
        // INITIALIZATION STATE: Prevents duplicate initialization
        this.initialized = false;
        
        // PAGE CONTEXT: Determines what functionality to initialize
        this.currentPage = this.getCurrentPage();
        
        // SUBSYSTEM MANAGERS: References to major platform components
        this.configManager = configManager;
        this.assetCacheManager = assetCacheManager;
        
        // METHOD BINDING: Ensure proper 'this' context for event handlers
        // WHY: Event listeners lose 'this' context without explicit binding
        this.init = this.init.bind(this);
        this.handleGlobalError = this.handleGlobalError.bind(this);
        this.handleUnhandledRejection = this.handleUnhandledRejection.bind(this);
        this.setupGlobalHandlers = this.setupGlobalHandlers.bind(this);
        this.setupGlobalExports = this.setupGlobalExports.bind(this);
        this.setupAuthEventListeners = this.setupAuthEventListeners.bind(this);
    }

    /**
     * CURRENT PAGE DETECTION
     * PURPOSE: Determine which page the user is currently viewing
     * WHY: Different pages require different initialization logic and features
     * USAGE: Used to conditionally load page-specific functionality
     */
    getCurrentPage() {
        // Extract filename from URL path, defaulting to index.html if empty
        // WHY: Empty pathname typically means root, which serves index.html
        return window.location.pathname.split('/').pop() || 'index.html';
    }

    /**
     * MAIN APPLICATION INITIALIZATION
     * PURPOSE: Orchestrate the complete application startup sequence
     * WHY: Proper initialization order prevents race conditions and ensures stability
     * PATTERN: Async initialization with comprehensive error handling
     * 
     * INITIALIZATION SEQUENCE:
     * 1. Performance optimizations (caching, config)
     * 2. Global error handlers
     * 3. Core authentication system
     * 4. Navigation system
     * 5. Page-specific features (activity tracking for dashboards)
     * 6. Legacy compatibility layer  
     * 7. Page-specific initialization
     * 8. Asset preloading for performance
     */
    async init() {
        // DUPLICATE INITIALIZATION PREVENTION
        // WHY: Multiple calls to init() could cause conflicts and memory leaks
        if (this.initialized) return;

        try {
            console.log('Initializing Course Creator Application with advanced caching...');
            
            // STEP 1: Initialize performance systems first
            // WHY: Caching and config must be ready before other modules use them
            await this._initializePerformanceOptimizations();
            
            // STEP 2: Setup global error handling early
            // WHY: Catch errors from subsequent initialization steps
            this.setupGlobalHandlers();
            
            // STEP 3: Initialize authentication system
            // WHY: Many other modules depend on user authentication state
            Auth.initializeAuth();
            
            // STEP 4: Initialize navigation system
            // WHY: Navigation must be ready for route changes and menu updates
            Navigation.init();
            
            // STEP 5: Initialize activity tracking for dashboard pages
            // WHY: Dashboard pages need session timeout and activity monitoring
            if (this.currentPage.includes('dashboard')) {
                this.activityTracker = new ActivityTracker();
                this.activityTracker.start();
            }
            
            // STEP 6: Setup legacy compatibility layer
            // WHY: Support older HTML pages that expect global functions
            this.setupGlobalExports();
            
            // STEP 6.5: Setup event listeners for auth buttons
            // WHY: Avoid timing issues with ES6 module loading and onclick handlers
            // Use setTimeout to ensure DOM elements exist
            setTimeout(() => {
                this.setupAuthEventListeners();
            }, 100);
            
            // STEP 7: Initialize page-specific functionality
            // WHY: Different pages have different requirements and components
            this.initializePage();
            
            // STEP 8: Preload page-specific assets for performance
            // WHY: Improves user experience by loading likely-needed resources
            await this._preloadPageAssets();
            
            // MARK INITIALIZATION COMPLETE
            this.initialized = true;
            console.log('Course Creator Application initialized successfully');
            
        } catch (error) {
            // INITIALIZATION ERROR HANDLING
            // WHY: Graceful error handling prevents blank pages and provides debugging info
            console.error('Error initializing application:', error);
            this.handleGlobalError(error);
        }
    }

    /**
     * GLOBAL ERROR HANDLING SYSTEM SETUP
     * PURPOSE: Establish comprehensive error handling for the entire application
     * WHY: Unhandled errors can crash the application or leave users in broken states
     * COVERAGE: JavaScript errors, promise rejections, visibility changes, ServiceWorker updates
     * 
     * ERROR HANDLING STRATEGY:
     * - Capture all unhandled errors and log them for debugging
     * - Show user-friendly error messages without technical details
     * - Store error logs in localStorage for developer troubleshooting
     * - Maintain application stability even when errors occur
     */
    setupGlobalHandlers() {
        // JAVASCRIPT ERROR HANDLER: Catches all unhandled JavaScript errors
        // WHY: Prevents errors from crashing the application and provides debugging info
        window.addEventListener('error', this.handleGlobalError);
        
        // PROMISE REJECTION HANDLER: Catches unhandled promise rejections
        // WHY: Async operations can fail silently without this handler
        window.addEventListener('unhandledrejection', this.handleUnhandledRejection);
        
        // VISIBILITY CHANGE HANDLER: Track user activity when they return to the tab
        // WHY: Session timeout management requires knowing when user is active
        // BUSINESS LOGIC: Only track activity for authenticated users
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && Auth.isAuthenticated()) {
                Auth.activityTracker.trackActivity();
            }
        });
        
        // SERVICEWORKER UPDATE HANDLER: Handle background updates from service worker
        // WHY: Provides feedback when the application has been updated in the background
        // PROGRESSIVE WEB APP: Enables offline functionality and update notifications
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'SW_UPDATED') {
                    console.log('ServiceWorker updated to version:', event.data.version);
                    // Future enhancement: Show user notification about updates
                }
            });
        }
    }

    /**
     * GLOBAL JAVASCRIPT ERROR HANDLER
     * PURPOSE: Process and log all unhandled JavaScript errors in the application
     * WHY: Unhandled errors can break functionality and create poor user experience
     * 
     * ERROR PROCESSING WORKFLOW:
     * 1. Extract error details (message, filename, line number, stack trace)
     * 2. Log comprehensive error information for debugging
     * 3. Store error in localStorage for developer access
     * 4. Show user-friendly notification without technical details
     * 5. Maintain application stability and user confidence
     */
    handleGlobalError(event) {
        // EXTRACT ERROR OBJECT: Handle both Error objects and ErrorEvent objects
        const error = event.error || event;
        console.error('Global error caught:', error);
        
        // COLLECT COMPREHENSIVE ERROR DETAILS: Gather all available debugging information
        // WHY: Complete error context is essential for effective debugging
        const errorDetails = {
            message: error.message || event.message,           // Human-readable error message
            filename: event.filename,                          // File where error occurred
            lineno: event.lineno,                             // Line number of error
            colno: event.colno,                               // Column number of error
            stack: error.stack                                // Complete stack trace
        };
        
        // PERSISTENT ERROR LOGGING: Store error for developer troubleshooting
        // WHY: Developers need access to error details even after page refresh
        this.logError('JavaScript Error', errorDetails);
        
        // USER-FRIENDLY ERROR NOTIFICATION: Show helpful message without technical details
        // WHY: Users need to know something went wrong but don't need technical information
        // BUSINESS LOGIC: Only show notification after app is fully initialized
        if (this.initialized) {
            showNotification(
                'An unexpected error occurred. Please refresh the page if the problem persists.',
                'error',
                { timeout: 8000 }  // 8 second timeout for error messages
            );
        }
    }

    /**
     * UNHANDLED PROMISE REJECTION HANDLER
     * PURPOSE: Catch and process promises that reject without .catch() handlers
     * WHY: Unhandled promise rejections can indicate network issues, API failures, or logic errors
     * 
     * COMMON CAUSES:
     * - Network requests that fail without error handling
     * - Async/await functions with missing try/catch blocks
     * - Third-party library promises that reject unexpectedly
     * - Database or API calls that timeout or return errors
     * 
     * HANDLING STRATEGY:
     * - Log the rejection reason for debugging
     * - Store error details for developer analysis
     * - Show user-friendly message about network/processing issues
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
     * PERSISTENT ERROR LOGGING SYSTEM
     * PURPOSE: Store detailed error information in localStorage for debugging
     * WHY: Developers need access to error details to diagnose and fix issues
     * 
     * ERROR LOG STRUCTURE:
     * - Timestamp: When the error occurred
     * - Type: Category of error (JavaScript Error, Promise Rejection, etc.)
     * - Details: Complete error information (message, stack, location)
     * - Page: Which page the error occurred on
     * - User Agent: Browser and device information for compatibility debugging
     * 
     * STORAGE MANAGEMENT:
     * - Maintains only the 20 most recent errors to prevent storage overflow
     * - Gracefully handles localStorage failures (quota exceeded, disabled)
     * - Provides structured data that can be easily analyzed or exported
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
     * AUTHENTICATION EVENT LISTENERS SETUP
     * PURPOSE: Attach event listeners to auth buttons to avoid timing issues
     * WHY: ES6 modules load asynchronously, onclick handlers need immediate functions
     */
    setupAuthEventListeners() {
        // Wait for DOM to be ready and retry if elements not found
        const attachListeners = () => {
            // LOGIN BUTTON: Attach click handler
            const loginBtn = document.getElementById('loginBtn');
            if (loginBtn) {
                // Remove any existing listeners first
                loginBtn.removeEventListener('click', this.handleLoginClick);
                loginBtn.addEventListener('click', this.handleLoginClick);
                console.log('✅ Login button event listener attached');
            } else {
                console.log('⚠️ Login button not found');
            }
            
            // REGISTER BUTTON: Attach click handler  
            const registerBtn = document.getElementById('registerBtn');
            if (registerBtn) {
                // Remove any existing listeners first
                registerBtn.removeEventListener('click', this.handleRegisterClick);
                registerBtn.addEventListener('click', this.handleRegisterClick);
                console.log('✅ Register button event listener attached');
            } else {
                console.log('⚠️ Register button not found');
            }
            
            // Return whether both buttons were found
            return loginBtn && registerBtn;
        };

        // Try to attach listeners immediately
        const success = attachListeners();
        
        if (!success) {
            // If elements not found, retry after DOM is loaded
            console.log('🔄 Elements not found, waiting for DOM...');
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', attachListeners);
            } else {
                // DOM already loaded, try again after a short delay
                setTimeout(attachListeners, 100);
            }
        }
    }

    handleLoginClick = () => {
        console.log('🔐 Login button clicked');
        if (Navigation && Navigation.showLogin) {
            Navigation.showLogin();
        } else {
            console.error('❌ Navigation.showLogin not available');
        }
    }

    handleRegisterClick = () => {
        console.log('📝 Register button clicked');
        console.log('🔍 Checking Navigation availability...');
        console.log('   - Navigation object:', Navigation);
        console.log('   - Navigation.showRegister:', Navigation?.showRegister);
        console.log('   - window.Navigation:', window.Navigation);
        console.log('   - window.Navigation.showRegister:', window.Navigation?.showRegister);
        
        // Try multiple ways to call showRegister
        let success = false;
        
        // Method 1: Direct import
        if (Navigation && Navigation.showRegister) {
            console.log('✅ Calling Navigation.showRegister() via import');
            try {
                Navigation.showRegister();
                success = true;
            } catch (error) {
                console.error('❌ Error calling Navigation.showRegister():', error);
            }
        }
        
        // Method 2: Global window object
        else if (window.Navigation && window.Navigation.showRegister) {
            console.log('✅ Calling window.Navigation.showRegister()');
            try {
                window.Navigation.showRegister();
                success = true;
            } catch (error) {
                console.error('❌ Error calling window.Navigation.showRegister():', error);
            }
        }
        
        // Method 3: Try global showRegister function
        else if (typeof window.showRegister === 'function') {
            console.log('✅ Calling window.showRegister()');
            try {
                window.showRegister();
                success = true;
            } catch (error) {
                console.error('❌ Error calling window.showRegister():', error);
            }
        }
        
        else {
            console.error('❌ No Navigation.showRegister method found');
            console.log('Available window properties:', Object.keys(window).filter(key => 
                key.includes('Navigation') || key.includes('show') || key.includes('register')
            ));
        }
        
        if (success) {
            console.log('✅ showRegister() called successfully');
        } else {
            console.error('❌ Failed to call showRegister() - trying fallback');
            // Fallback: manually update content
            const main = document.getElementById('main-content');
            if (main) {
                main.innerHTML = '<div style="padding: 20px; color: red;">Registration functionality temporarily unavailable. Navigation module not properly loaded.</div>';
            }
        }
    }

    /**
     * GLOBAL FUNCTION EXPORTS FOR LEGACY COMPATIBILITY
     * PURPOSE: Export modern module functions as global window functions
     * WHY: Older HTML pages and inline scripts expect global functions to exist
     * 
     * LEGACY SUPPORT STRATEGY:
     * - Maintain compatibility with existing HTML pages that use onclick handlers
     * - Bridge modern ES6 modules with legacy global function expectations
     * - Provide consistent API surface for both modern and legacy code
     * - Enable gradual migration from global functions to module imports
     * 
     * FUNCTION CATEGORIES:
     * - Authentication: Login, logout, user management
     * - Navigation: Page transitions and routing
     * - UI Utilities: Password visibility, dropdowns, modals
     * - Configuration: Access to modern config and caching systems
     * - Error Handling: Access to error logs and debugging tools
     */
    setupGlobalExports() {
        // AUTHENTICATION FUNCTIONS: User session management
        // WHY: Legacy HTML pages need access to authentication without module imports
        window.getCurrentUser = () => Auth.getCurrentUser();
        window.logout = async () => {
            const result = await Auth.logout();
            if (result.success) {
                showNotification('Logged out successfully', 'success');
                // CONTEXT-AWARE REDIRECT: Different pages need different logout behaviors
                if (this.currentPage.includes('dashboard') || this.currentPage.includes('admin')) {
                    window.location.href = 'html/index.html';  // Redirect admin/dashboard pages
                } else {
                    // UPDATE UI IN-PLACE: For public pages, update navigation without redirect
                    Navigation.updateAccountSection();
                    Navigation.updateNavigation();
                    Navigation.showHome();
                }
            }
        };
        
        // NAVIGATION FUNCTIONS: Page routing and transitions
        // WHY: Onclick handlers in HTML need direct access to navigation functions
        window.showHome = () => Navigation.showHome();
        window.showLogin = () => Navigation.showLogin();
        window.showRegister = () => Navigation.showRegister();
        window.showInstructorRegistration = () => Navigation.showInstructorRegistration();
        window.showProfile = () => Navigation.showProfile();
        window.showSettings = () => Navigation.showSettings();
        window.showHelp = () => Navigation.showHelp();
        window.showPasswordReset = () => Navigation.showPasswordReset();
        
        // UI UTILITY FUNCTIONS: Common interface interactions
        // WHY: Forms and interactive elements need consistent behavior across pages
        
        // PASSWORD VISIBILITY TOGGLE: Show/hide password in input fields
        // BUSINESS LOGIC: Improves user experience by allowing password verification
        window.togglePasswordVisibility = (inputId, buttonId) => {
            const input = document.getElementById(inputId);
            const button = document.getElementById(buttonId);
            
            if (input && button) {
                const icon = button.querySelector('i');
                if (input.type === 'password') {
                    // REVEAL PASSWORD: Change input type and update icon
                    input.type = 'text';
                    if (icon) {
                        icon.className = 'fas fa-eye-slash';  // "Hide" icon
                    }
                    button.title = 'Hide password';
                } else {
                    // HIDE PASSWORD: Restore password type and update icon
                    input.type = 'password';
                    if (icon) {
                        icon.className = 'fas fa-eye';        // "Show" icon
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
        
        // Demo mode function
        window.startDemo = async () => {
            try {
                // Show loading state
                showNotification('Starting demo session...', 'info', { timeout: 2000 });
                
                // Call demo service to start session
                const response = await fetch('/api/v1/demo/start?user_type=instructor', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Failed to start demo session');
                }
                
                const demoData = await response.json();
                
                // Store demo session data
                localStorage.setItem('demoSession', JSON.stringify({
                    sessionId: demoData.session_id,
                    user: demoData.user,
                    expiresAt: demoData.expires_at,
                    isDemo: true
                }));
                localStorage.setItem('currentUser', JSON.stringify(demoData.user));
                
                // Show success notification
                showNotification(
                    `Welcome ${demoData.user.name}! You're now exploring as a Demo Instructor. This session expires in 2 hours.`,
                    'success',
                    { timeout: 5000 }
                );
                
                // Redirect to instructor dashboard with demo session
                setTimeout(() => {
                    window.location.href = `html/instructor-dashboard.html?demo=true&session=${demoData.session_id}`;
                }, 2000);
                
            } catch (error) {
                console.error('Failed to start demo:', error);
                showNotification(
                    'Failed to start demo session. Please try again.',
                    'error',
                    { timeout: 5000 }
                );
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
     * PAGE-SPECIFIC INITIALIZATION
     * PURPOSE: Set up functionality that only applies to the current page
     * WHY: Different pages have different interaction patterns and requirements
     * 
     * CURRENT FUNCTIONALITY:
     * - Account dropdown click-outside-to-close behavior
     * - Prevent dropdown from closing when clicking inside (except logout)
     * - Future: Page-specific component initialization, event handlers, etc.
     * 
     * DESIGN PATTERN: 
     * - Use event delegation for better performance
     * - Check for element existence before attaching handlers
     * - Use page detection to conditionally initialize features
     */
    initializePage() {
        // DROPDOWN CLOSE-ON-OUTSIDE-CLICK: Account dropdown behavior
        // WHY: Standard UI pattern - dropdowns should close when clicking outside
        document.addEventListener('click', (event) => {
            const accountDropdown = document.getElementById('accountDropdown');
            const accountMenu = document.getElementById('accountMenu');
            
            // CLICK OUTSIDE DETECTION: Close dropdown if click is outside the dropdown trigger
            if (accountMenu && accountDropdown && !accountDropdown.contains(event.target)) {
                accountMenu.style.display = 'none';
                accountMenu.style.visibility = 'hidden';
            }
        });
        
        // DROPDOWN INTERNAL CLICK HANDLING: Prevent accidental closure
        // WHY: Clicking inside dropdown shouldn't close it (except for logout action)
        document.addEventListener('click', (event) => {
            const accountMenu = document.getElementById('accountMenu');
            if (accountMenu && accountMenu.contains(event.target)) {
                // SELECTIVE PROPAGATION: Allow logout to close dropdown, prevent others
                if (!event.target.textContent.includes('Logout')) {
                    event.stopPropagation();  // Prevent dropdown from closing
                }
            }
        });
    }

    /**
     * AUTHENTICATION REQUIREMENT CHECKER
     * PURPOSE: Determine if the current page requires user authentication
     * WHY: Some pages are public, others require login - this enables conditional logic
     * 
     * PROTECTED PAGES:
     * - admin.html: Administrator functionality
     * - instructor-dashboard.html: Course creation and management
     * - student-dashboard.html: Course consumption and progress
     * - lab.html: Interactive lab environment
     * 
     * USAGE: Guards can check this before initializing authenticated features
     */
    requiresAuth() {
        const protectedPages = [
            'admin.html',                    // Platform administration
            'instructor-dashboard.html',     // Course creation interface  
            'student-dashboard.html',        // Student learning interface
            'lab.html'                      // Interactive coding environment
        ];
        
        return protectedPages.includes(this.currentPage);
    }

    /**
     * APPLICATION STATE INSPECTOR
     * PURPOSE: Provide complete view of current application state
     * WHY: Debugging, monitoring, and state-dependent logic need access to app state
     * 
     * STATE INFORMATION INCLUDES:
     * - Initialization status
     * - Current page context
     * - Authentication state and user info
     * - Performance metrics (cache hit rates, etc.)
     * 
     * USAGE: Debugging tools, health checks, conditional feature loading
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

// Auto-initialization removed - main.js handles initialization to prevent duplicate calls

export { app as App };
export default app;