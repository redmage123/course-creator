/**
 * MAIN APPLICATION ENTRY POINT (ES6 MODULE ARCHITECTURE)
 * 
 * PURPOSE: Central initialization and module coordination for Course Creator Platform
 * WHY: Modular architecture enables better code organization, testing, and maintenance
 * PATTERN: Uses ES6 modules for clean dependency management and namespace separation
 * 
 * ARCHITECTURE DECISIONS:
 * - ES6 modules for modern browser compatibility and cleaner imports
 * - Centralized initialization to ensure proper startup sequence
 * - Global exposure for debugging while maintaining module boundaries
 * - Single entry point reduces complexity and enables unified error handling
 */
import { App } from './modules/app.js';                    // Main application controller and lifecycle management
import { Auth } from './modules/auth.js';                  // Authentication system and session management  
import { Navigation } from './modules/navigation.js';      // Site navigation and routing logic
import { showNotification } from './modules/notifications.js'; // User notification system
import UIComponents from './modules/ui-components.js';     // Reusable UI component library
import Slideshow from './modules/slideshow.js';           // Homepage feature slideshow component

/**
 * APPLICATION INITIALIZATION
 * PURPOSE: Start the main application with proper initialization sequence
 * WHY: App.init() handles startup tasks like DOM ready checks, service connections, etc.
 * TIMING: Wait for DOM to be ready before initializing
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}

/**
 * SLIDESHOW INITIALIZATION
 * PURPOSE: Initialize the homepage feature slideshow if container exists
 * WHY: Slideshow is page-specific and should only initialize on pages that contain it
 * TIMING: Wait for both DOM and CSS to be fully loaded to prevent display issues
 */
function initializeSlideshow() {
    try {
        const slideshowContainer = document.querySelector('.hero-slideshow');
        if (slideshowContainer) {
            // Ensure CSS is fully loaded before initializing slideshow
    /**
     * EXECUTE CHECKCSSLOADED OPERATION
     * PURPOSE: Execute checkCSSLoaded operation
     * WHY: Implements required business logic for system functionality
     *
     * @throws {Error} If operation fails or validation errors occur
     */
            const checkCSSLoaded = () => {
                const slideshowWrapper = slideshowContainer.querySelector('.slideshow-wrapper');
                if (slideshowWrapper && getComputedStyle(slideshowWrapper).display !== 'none') {
                    window.slideshow = new Slideshow('.hero-slideshow');
                    console.log('Hero slideshow initialized');
                } else {
                    // Retry after a short delay if CSS isn't loaded yet
                    setTimeout(checkCSSLoaded, 50);
                }
            };
            checkCSSLoaded();
        } else {
            console.log('No slideshow container found - skipping slideshow initialization');
        }
    } catch (error) {
        console.error('Error initializing slideshow:', error);
    }
}

// Wait for both DOM content and window load to ensure CSS is ready
    /**
     * EXECUTE WAITFORFULLLOAD OPERATION
     * PURPOSE: Execute waitForFullLoad operation
     * WHY: Implements required business logic for system functionality
     *
     * @throws {Error} If operation fails or validation errors occur
     */
function waitForFullLoad() {
    if (document.readyState === 'complete') {
        initializeSlideshow();
    } else {
        window.addEventListener('load', initializeSlideshow);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', waitForFullLoad);
} else {
    waitForFullLoad();
}

/**
 * MODULE RE-EXPORTS
 * PURPOSE: Make core modules available to other parts of the application
 * WHY: Allows other modules to import from main.js instead of individual files
 * PATTERN: Re-export pattern creates a unified public API
 */
export { App, Auth, Navigation, showNotification, UIComponents, Slideshow };

/**
 * GLOBAL DEBUGGING INTERFACE
 * PURPOSE: Expose modules globally for browser console debugging and testing
 * WHY: Enables developers to inspect and interact with modules via window object
 * SECURITY: Only enabled in browser environments, not in Node.js/server contexts
 * 
 * USAGE EXAMPLES:
 * - window.App.getCurrentUser() - Check current user state
 * - window.Auth.logout() - Programmatically log out user
 * - window.showNotification('Test message') - Test notification system
 */
if (typeof window !== 'undefined') {
    window.App = App;
    window.Auth = Auth;
    window.Navigation = Navigation;
    window.showNotification = showNotification;
    window.UIComponents = UIComponents;
    window.Slideshow = Slideshow;
}

