/**
 * Focus Manager - Detects keyboard vs mouse users for intelligent focus styling
 *
 * Purpose:
 * - Adds 'using-mouse' class when user interacts with mouse
 * - Removes class when user presses Tab for keyboard navigation
 * - Allows CSS to provide subtle focus for mouse users, prominent for keyboard
 *
 * WCAG 2.4.7 Level AA: Focus Visible
 * Ensures keyboard focus is clearly visible without being intrusive for mouse users
 *
 * Business Context:
 * This enhances accessibility for keyboard-only users (including those with motor
 * disabilities) while maintaining a clean visual experience for mouse users.
 *
 * @module focus-manager
 * @version 1.0.0
 */

(function() {
    'use strict';

    /**
     * Track current interaction mode
     * @type {boolean}
     */
    let usingMouse = false;

    /**
     * Handle mouse interaction
     * Adds 'using-mouse' class to body for subtle focus styling
     */
    function handleMouseDown() {
        if (!usingMouse) {
            usingMouse = true;
            document.body.classList.add('using-mouse');
        }
    }

    /**
     * Handle keyboard interaction (Tab key)
     * Removes 'using-mouse' class for prominent focus indicators
     * @param {KeyboardEvent} e - Keyboard event
     */
    function handleKeyDown(e) {
        // Only respond to Tab key (forward and backward navigation)
        if (e.key === 'Tab' && usingMouse) {
            usingMouse = false;
            document.body.classList.remove('using-mouse');
        }
    }

    /**
     * Initialize focus manager when DOM is ready
     */
    function initialize() {
        // Set initial state based on first interaction
        document.addEventListener('mousedown', handleMouseDown);
        document.addEventListener('keydown', handleKeyDown);

        // Also detect touch events for mobile
        document.addEventListener('touchstart', handleMouseDown);

        // Log initialization for debugging
        console.debug('[FocusManager] Initialized - Tracking user interaction mode');
    }

    // Initialize immediately if DOM is ready, otherwise wait
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();
