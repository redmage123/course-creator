/**
 * ACCESSIBILITY MANAGER - Comprehensive accessibility enhancements
 * Implements WCAG 2.1 AA compliance patterns across all pages
 *
 * FEATURES:
 * - Focus management (keyboard vs mouse detection)
 * - Skip links navigation
 * - Modal focus trap
 * - ARIA live regions for dynamic content
 * - Keyboard navigation enhancements
 * - Tab panel management
 */

class AccessibilityManager {
    constructor() {
        this.isUsingKeyboard = false;
        this.lastFocusedElement = null;
        this.modalStack = [];

        this.init();
    }

    /**
     * Initialize all accessibility features
     */
    init() {
        this.detectInputMethod();
        this.initSkipLinks();
        this.initAriaLiveRegions();
        this.initModalManagement();
        this.initTabPanels();
        this.initFormValidation();
        this.enhanceKeyboardNavigation();
    }

    /**
     * WCAG 2.1.1: Detect keyboard vs mouse input
     * Shows focus indicators only for keyboard users
     */
    detectInputMethod() {
        // Start assuming keyboard until mouse is used
        document.body.classList.add('using-keyboard');

        // Detect keyboard usage
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                this.isUsingKeyboard = true;
                document.body.classList.add('using-keyboard');
                document.body.classList.remove('using-mouse');
            }
        });

        // Detect mouse usage
        document.addEventListener('mousedown', () => {
            this.isUsingKeyboard = false;
            document.body.classList.add('using-mouse');
            document.body.classList.remove('using-keyboard');
        });
    }

    /**
     * WCAG 2.4.1: Bypass blocks with skip links
     */
    initSkipLinks() {
        // Add skip links to page if they don't exist
        if (!document.querySelector('.skip-links')) {
            const skipLinks = document.createElement('div');
            skipLinks.className = 'skip-links';
            skipLinks.innerHTML = `
                <a href="#main-content" class="skip-link">Skip to main content</a>
                <a href="#navigation" class="skip-link">Skip to navigation</a>
            `;
            document.body.insertBefore(skipLinks, document.body.firstChild);
        }

        // Handle skip link clicks
        document.querySelectorAll('.skip-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.setAttribute('tabindex', '-1');
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    /**
     * WCAG 4.1.3: Create ARIA live regions for dynamic content
     */
    initAriaLiveRegions() {
        // Create live regions if they don't exist
        if (!document.getElementById('aria-live-polite')) {
            const polite = document.createElement('div');
            polite.id = 'aria-live-polite';
            polite.setAttribute('role', 'status');
            polite.setAttribute('aria-live', 'polite');
            polite.setAttribute('aria-atomic', 'true');
            polite.className = 'sr-only';
            document.body.appendChild(polite);
        }

        if (!document.getElementById('aria-live-assertive')) {
            const assertive = document.createElement('div');
            assertive.id = 'aria-live-assertive';
            assertive.setAttribute('role', 'alert');
            assertive.setAttribute('aria-live', 'assertive');
            assertive.setAttribute('aria-atomic', 'true');
            assertive.className = 'sr-only';
            document.body.appendChild(assertive);
        }
    }

    /**
     * Announce message to screen readers
     * @param {string} message - Message to announce
     * @param {string} priority - 'polite' or 'assertive'
     */
    announce(message, priority = 'polite') {
        const regionId = priority === 'assertive' ? 'aria-live-assertive' : 'aria-live-polite';
        const region = document.getElementById(regionId);

        if (region) {
            // Clear previous message
            region.textContent = '';

            // Add new message after brief delay (ensures announcement)
            setTimeout(() => {
                region.textContent = message;
            }, 100);
        }
    }

    /**
     * WCAG 2.4.3: Modal focus management
     */
    initModalManagement() {
        // Observe DOM for modal additions
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.matches('[role="dialog"], .modal')) {
                        this.trapFocusInModal(node);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Trap focus within modal dialog
     * @param {HTMLElement} modal - Modal element
     */
    trapFocusInModal(modal) {
        // Store last focused element
        this.lastFocusedElement = document.activeElement;
        this.modalStack.push(modal);

        // Get all focusable elements in modal
        const focusableElements = modal.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), ' +
            'input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        // Focus first element
        firstFocusable.focus();

        // Trap focus
        const trapFocus = (e) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstFocusable) {
                    lastFocusable.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastFocusable) {
                    firstFocusable.focus();
                    e.preventDefault();
                }
            }
        };

        // Handle Escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.closeModal(modal);
            }
        };

        modal.addEventListener('keydown', trapFocus);
        modal.addEventListener('keydown', handleEscape);

        // Store handlers for cleanup
        modal._focusTrap = trapFocus;
        modal._escapeHandler = handleEscape;
    }

    /**
     * Close modal and restore focus
     * @param {HTMLElement} modal - Modal element to close
     */
    closeModal(modal) {
        // Remove event listeners
        if (modal._focusTrap) {
            modal.removeEventListener('keydown', modal._focusTrap);
        }
        if (modal._escapeHandler) {
            modal.removeEventListener('keydown', modal._escapeHandler);
        }

        // Remove from stack
        const index = this.modalStack.indexOf(modal);
        if (index > -1) {
            this.modalStack.splice(index, 1);
        }

        // Hide modal
        modal.setAttribute('aria-hidden', 'true');
        modal.style.display = 'none';

        // Restore focus
        if (this.lastFocusedElement) {
            this.lastFocusedElement.focus();
            this.lastFocusedElement = null;
        }

        this.announce('Dialog closed', 'polite');
    }

    /**
     * WCAG 4.1.2: Tab panel ARIA pattern
     */
    initTabPanels() {
        document.querySelectorAll('[role="tablist"]').forEach(tablist => {
            const tabs = tablist.querySelectorAll('[role="tab"]');

            tabs.forEach((tab, index) => {
                // Set initial states
                const isSelected = tab.getAttribute('aria-selected') === 'true';
                const panel = document.getElementById(tab.getAttribute('aria-controls'));

                if (panel) {
                    panel.setAttribute('role', 'tabpanel');
                    panel.setAttribute('aria-labelledby', tab.id);
                    panel.hidden = !isSelected;
                }

                // Click handler
                tab.addEventListener('click', () => {
                    this.selectTab(tab);
                });

                // Keyboard navigation
                tab.addEventListener('keydown', (e) => {
                    let newTab = null;

                    switch (e.key) {
                        case 'ArrowLeft':
                            newTab = tabs[index - 1] || tabs[tabs.length - 1];
                            break;
                        case 'ArrowRight':
                            newTab = tabs[index + 1] || tabs[0];
                            break;
                        case 'Home':
                            newTab = tabs[0];
                            break;
                        case 'End':
                            newTab = tabs[tabs.length - 1];
                            break;
                        default:
                            return;
                    }

                    e.preventDefault();
                    this.selectTab(newTab);
                    newTab.focus();
                });
            });
        });
    }

    /**
     * Select a tab and update ARIA states
     * @param {HTMLElement} selectedTab - Tab to select
     */
    selectTab(selectedTab) {
        const tablist = selectedTab.closest('[role="tablist"]');
        const tabs = tablist.querySelectorAll('[role="tab"]');

        tabs.forEach(tab => {
            const isSelected = tab === selectedTab;
            const panel = document.getElementById(tab.getAttribute('aria-controls'));

            tab.setAttribute('aria-selected', isSelected);
            tab.setAttribute('tabindex', isSelected ? '0' : '-1');

            if (panel) {
                panel.hidden = !isSelected;
            }
        });

        this.announce(`${selectedTab.textContent} tab selected`, 'polite');
    }

    /**
     * WCAG 3.3.1, 3.3.3: Form validation enhancements
     */
    initFormValidation() {
        document.querySelectorAll('form').forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');

            inputs.forEach(input => {
                // Add aria-required for required fields
                if (input.hasAttribute('required')) {
                    input.setAttribute('aria-required', 'true');
                }

                // Real-time validation on blur
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });

                // Clear errors on input
                input.addEventListener('input', () => {
                    if (input.getAttribute('aria-invalid') === 'true') {
                        this.clearFieldError(input);
                    }
                });
            });
        });
    }

    /**
     * Validate form field
     * @param {HTMLElement} field - Input field to validate
     */
    validateField(field) {
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        let errorMessage = '';

        // Required validation
        if (isRequired && !value) {
            errorMessage = `${this.getFieldLabel(field)} is required`;
        }
        // Email validation
        else if (field.type === 'email' && value && !this.isValidEmail(value)) {
            errorMessage = 'Please enter a valid email address';
        }
        // Custom validation
        else if (field.hasAttribute('pattern') && value && !new RegExp(field.getAttribute('pattern')).test(value)) {
            errorMessage = field.getAttribute('data-error-message') || 'Invalid format';
        }

        if (errorMessage) {
            this.showFieldError(field, errorMessage);
            return false;
        } else {
            this.clearFieldError(field);
            return true;
        }
    }

    /**
     * Show field error with ARIA
     * @param {HTMLElement} field - Input field
     * @param {string} message - Error message
     */
    showFieldError(field, message) {
        field.setAttribute('aria-invalid', 'true');
        field.classList.add('is-invalid');

        // Get or create error element
        let errorId = field.getAttribute('aria-describedby');
        let errorElement = errorId ? document.getElementById(errorId) : null;

        if (!errorElement) {
            errorId = `${field.id || 'field'}-error`;
            errorElement = document.createElement('div');
            errorElement.id = errorId;
            errorElement.className = 'error-message';
            errorElement.setAttribute('role', 'alert');
            field.setAttribute('aria-describedby', errorId);
            field.parentNode.appendChild(errorElement);
        }

        errorElement.textContent = message;
        this.announce(message, 'assertive');
    }

    /**
     * Clear field error
     * @param {HTMLElement} field - Input field
     */
    clearFieldError(field) {
        field.setAttribute('aria-invalid', 'false');
        field.classList.remove('is-invalid');

        const errorId = field.getAttribute('aria-describedby');
        if (errorId) {
            const errorElement = document.getElementById(errorId);
            if (errorElement && errorElement.classList.contains('error-message')) {
                errorElement.textContent = '';
            }
        }
    }

    /**
     * Get readable label for field
     * @param {HTMLElement} field - Input field
     * @returns {string} Field label
     */
    getFieldLabel(field) {
        const label = field.labels && field.labels[0];
        return label ? label.textContent.replace('*', '').trim() : field.name || 'This field';
    }

    /**
     * Validate email format
     * @param {string} email - Email address
     * @returns {boolean} Is valid
     */
    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    /**
     * WCAG 2.1.1: Enhance keyboard navigation
     */
    enhanceKeyboardNavigation() {
        // Add keyboard support to clickable divs
        document.querySelectorAll('[onclick]:not(button):not(a)').forEach(element => {
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
            if (!element.hasAttribute('role')) {
                element.setAttribute('role', 'button');
            }

            element.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    element.click();
                }
            });
        });
    }

    /**
     * Show loading state for button
     * @param {HTMLElement} button - Button element
     * @param {string} message - Loading message
     */
    showButtonLoading(button, message = 'Loading...') {
        button.setAttribute('aria-busy', 'true');
        button.disabled = true;
        button.classList.add('btn-loading');
        button._originalText = button.textContent;
        button.textContent = message;

        this.announce(message, 'polite');
    }

    /**
     * Hide loading state for button
     * @param {HTMLElement} button - Button element
     */
    hideButtonLoading(button) {
        button.setAttribute('aria-busy', 'false');
        button.disabled = false;
        button.classList.remove('btn-loading');
        if (button._originalText) {
            button.textContent = button._originalText;
        }
    }
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.accessibilityManager = new AccessibilityManager();
    });
} else {
    window.accessibilityManager = new AccessibilityManager();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccessibilityManager;
}
