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

/**
 * CORE MODULE IMPORTS
 * PURPOSE: Import all essential platform modules for initialization
 * WHY: Explicit imports make dependencies clear and enable tree-shaking
 */
import { App } from './modules/app.js';                    // Main application controller and lifecycle management
import { Auth } from './modules/auth.js';                  // Authentication system and session management  
import { Navigation } from './modules/navigation.js';      // Site navigation and routing logic
import { showNotification } from './modules/notifications.js'; // User notification system
import UIComponents from './modules/ui-components.js';     // Reusable UI component library

/**
 * APPLICATION INITIALIZATION
 * PURPOSE: Start the main application with proper initialization sequence
 * WHY: App.init() handles startup tasks like DOM ready checks, service connections, etc.
 * TIMING: Executed immediately when this module loads
 */
App.init();

/**
 * MODULE RE-EXPORTS
 * PURPOSE: Make core modules available to other parts of the application
 * WHY: Allows other modules to import from main.js instead of individual files
 * PATTERN: Re-export pattern creates a unified public API
 */
export { App, Auth, Navigation, showNotification, UIComponents };

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
}

