/**
 * Main Application Entry Point (Modular)
 * This is the new ES6 module-based main file
 */

import { App } from './modules/app.js';
import { Auth } from './modules/auth.js';
import { Navigation } from './modules/navigation.js';
import { showNotification } from './modules/notifications.js';
import UIComponents from './modules/ui-components.js';

// Initialize the application
App.init();

// Export main components for other modules
export { App, Auth, Navigation, showNotification, UIComponents };

// Make available globally for debugging
if (typeof window !== 'undefined') {
    window.App = App;
    window.Auth = Auth;
    window.Navigation = Navigation;
    window.showNotification = showNotification;
    window.UIComponents = UIComponents;
}

console.log('Course Creator Platform (Modular) loaded successfully');