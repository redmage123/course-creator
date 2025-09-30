/**
 * Accessibility Manager - Comprehensive A11y Support
 * Handles screen reader announcements, keyboard navigation, and ARIA management
 */

class AccessibilityManager {
    constructor() {
        this.liveRegion = null;
        this.assertiveRegion = null;
        this.focusHistory = [];
        this.keyboardNavigation = true;
        this.currentModal = null;
        
        this.init();
    }

    /**
     * Initialize accessibility manager
     */
    init() {
        this.createLiveRegions();
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupModalSupport();
        this.setupTabNavigation();
        this.detectKeyboardNavigation();
        
        // Announce page load
        this.announcePageLoad();
        
        console.log('Accessibility Manager initialized');
    }

    /**
     * Create ARIA live regions for screen reader announcements
     */
    createLiveRegions() {
        // Polite live region for general announcements
        this.liveRegion = document.getElementById('live-region') || this.createLiveRegion('polite');
        
        // Assertive live region for urgent announcements
        this.assertiveRegion = document.getElementById('live-region-assertive') || this.createLiveRegion('assertive');
    }

    createLiveRegion(politeness) {
        const region = document.createElement('div');
        region.setAttribute('aria-live', politeness);
        region.setAttribute('aria-atomic', 'true');
        region.className = 'sr-only';
        region.id = `live-region${politeness === 'assertive' ? '-assertive' : ''}`;
        document.body.appendChild(region);
        return region;
    }

    /**
     * Announce message to screen readers
     */
    announce(message, priority = 'polite') {
        if (!message) return;
        
        const region = priority === 'assertive' ? this.assertiveRegion : this.liveRegion;
        
        // Clear and then set message with slight delay for better screen reader support
        region.textContent = '';
        setTimeout(() => {
            region.textContent = message;
        }, 100);
        
        console.log(`A11y Announcement (${priority}):`, message);
    }

    /**
     * Announce page navigation changes
     */
    announcePageChange(pageTitle, pageDescription) {
        const message = `Navigated to ${pageTitle}. ${pageDescription}`;
        this.announce(message);
        
        // Update page title for screen readers
        document.title = `${pageTitle} - Course Creator Platform`;
    }

    /**
     * Announce form errors
     */
    announceFormError(fieldName, errorMessage) {
        const message = `Error in ${fieldName}: ${errorMessage}`;
        this.announce(message, 'assertive');
    }

    /**
     * Announce success messages
     */
    announceSuccess(message) {
        this.announce(`Success: ${message}`);
    }

    /**
     * Announce loading states
     */
    announceLoading(action) {
        this.announce(`Loading ${action}, please wait`);
    }

    announceLoadingComplete(result) {
        this.announce(`Loading complete. ${result}`);
    }

    /**
     * Set up keyboard navigation
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (event) => {
            // Handle Escape key for modals
            if (event.key === 'Escape' && this.currentModal) {
                this.closeModal(this.currentModal);
            }
            
            // Handle keyboard shortcuts
            this.handleKeyboardShortcuts(event);
        });
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        // Skip if user is typing in form fields
        if (event.target.matches('input, textarea, select, [contenteditable]')) {
            return;
        }

        // Alt + shortcuts for main navigation
        if (event.altKey) {
            switch (event.key) {
                case '1':
                    event.preventDefault();
                    this.navigateToTab('overview');
                    break;
                case '2':
                    event.preventDefault();
                    this.navigateToTab('projects');
                    break;
                case '3':
                    event.preventDefault();
                    this.navigateToTab('members');
                    break;
                case '4':
                    event.preventDefault();
                    this.navigateToTab('settings');
                    break;
            }
        }
    }

    /**
     * Navigate to tab and announce
     */
    navigateToTab(tabName) {
        const tabButton = document.querySelector(`[data-tab="${tabName}"]`);
        if (tabButton) {
            tabButton.click();
            
            const tabContent = {
                'overview': 'Organization overview with statistics and recent activity',
                'projects': 'Project management interface with project list and creation tools',
                'members': 'Organization member management and role assignments',
                'settings': 'Organization settings and configuration options'
            };
            
            this.announcePageChange(
                tabName.charAt(0).toUpperCase() + tabName.slice(1),
                tabContent[tabName] || 'Dashboard section'
            );
        }
    }

    /**
     * Setup focus management
     */
    setupFocusManagement() {
        // Track focus for restoration
        document.addEventListener('focusin', (event) => {
            if (!event.target.closest('.modal')) {
                this.focusHistory.push(event.target);
                // Keep only last 5 focused elements
                if (this.focusHistory.length > 5) {
                    this.focusHistory.shift();
                }
            }
        });
    }

    /**
     * Detect if user is navigating with keyboard
     */
    detectKeyboardNavigation() {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Tab') {
                this.keyboardNavigation = true;
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            this.keyboardNavigation = false;
            document.body.classList.remove('keyboard-navigation');
        });
    }

    /**
     * Setup tab navigation with ARIA
     */
    setupTabNavigation() {
        const tablist = document.querySelector('[role="tablist"]');
        if (!tablist) return;

        const tabs = Array.from(tablist.querySelectorAll('[role="tab"]'));
        
        tabs.forEach((tab, index) => {
            tab.addEventListener('keydown', (event) => {
                this.handleTabKeydown(event, tabs, index);
            });
            
            tab.addEventListener('click', () => {
                this.activateTab(tab, tabs);
            });
        });
    }

    /**
     * Handle keyboard navigation within tabs
     */
    handleTabKeydown(event, tabs, currentIndex) {
        let newIndex = currentIndex;

        switch (event.key) {
            case 'ArrowLeft':
                event.preventDefault();
                newIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
                break;
            case 'ArrowRight':
                event.preventDefault();
                newIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
                break;
            case 'Home':
                event.preventDefault();
                newIndex = 0;
                break;
            case 'End':
                event.preventDefault();
                newIndex = tabs.length - 1;
                break;
            case 'Enter':
            case ' ':
                event.preventDefault();
                this.activateTab(tabs[currentIndex], tabs);
                return;
        }

        if (newIndex !== currentIndex) {
            tabs[newIndex].focus();
        }
    }

    /**
     * Activate tab with proper ARIA management
     */
    activateTab(activeTab, allTabs) {
        // Update ARIA attributes
        allTabs.forEach(tab => {
            tab.setAttribute('aria-selected', 'false');
            tab.setAttribute('tabindex', '-1');
            tab.classList.remove('active');
            
            // Hide corresponding panel
            const panelId = tab.getAttribute('aria-controls');
            const panel = document.getElementById(panelId);
            if (panel) {
                panel.style.display = 'none';
                panel.setAttribute('aria-hidden', 'true');
            }
        });

        // Activate selected tab
        activeTab.setAttribute('aria-selected', 'true');
        activeTab.setAttribute('tabindex', '0');
        activeTab.classList.add('active');

        // Show corresponding panel
        const activePanelId = activeTab.getAttribute('aria-controls');
        const activePanel = document.getElementById(activePanelId);
        if (activePanel) {
            activePanel.style.display = 'block';
            activePanel.setAttribute('aria-hidden', 'false');
            
            // Set focus to panel for screen readers
            if (this.keyboardNavigation) {
                activePanel.focus();
            }
        }

        // Announce tab change
        const tabText = activeTab.textContent.trim();
        this.announce(`${tabText} tab selected`);
    }

    /**
     * Setup modal accessibility
     */
    setupModalSupport() {
        // Handle modal opening
        document.addEventListener('modal:open', (event) => {
            this.openModal(event.detail.modal);
        });

        // Handle modal closing
        document.addEventListener('modal:close', (event) => {
            this.closeModal(event.detail.modal);
        });
    }

    /**
     * Open modal with accessibility support
     */
    openModal(modal) {
        this.currentModal = modal;
        
        // Store current focus
        this.previousFocus = document.activeElement;
        
        // Set modal attributes
        modal.setAttribute('aria-hidden', 'false');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        
        // Prevent background scrolling
        document.body.style.overflow = 'hidden';
        document.body.classList.add('focus-trap-active');
        
        // Focus first focusable element
        const firstFocusable = this.getFirstFocusableElement(modal);
        if (firstFocusable) {
            firstFocusable.focus();
        }
        
        // Announce modal opening
        const title = modal.querySelector('.modal-title')?.textContent || 'Dialog';
        this.announce(`${title} dialog opened. Press Escape to close.`);
        
        // Setup focus trap
        this.setupFocusTrap(modal);
    }

    /**
     * Close modal with accessibility support
     */
    closeModal(modal) {
        if (!modal) return;
        
        modal.setAttribute('aria-hidden', 'true');
        modal.style.display = 'none';
        
        // Restore scrolling
        document.body.style.overflow = '';
        document.body.classList.remove('focus-trap-active');
        
        // Restore focus
        if (this.previousFocus) {
            this.previousFocus.focus();
        }
        
        this.announce('Dialog closed');
        this.currentModal = null;
    }

    /**
     * Setup focus trap for modal
     */
    setupFocusTrap(modal) {
        const focusableElements = this.getFocusableElements(modal);
        
        modal.addEventListener('keydown', (event) => {
            if (event.key === 'Tab') {
                this.trapFocus(event, focusableElements);
            }
        });
    }

    /**
     * Trap focus within modal
     */
    trapFocus(event, focusableElements) {
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (event.shiftKey) {
            if (document.activeElement === firstElement) {
                event.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                event.preventDefault();
                firstElement.focus();
            }
        }
    }

    /**
     * Get focusable elements within container
     */
    getFocusableElements(container) {
        const focusableSelectors = [
            'button:not([disabled])',
            '[href]',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ].join(', ');
        
        return Array.from(container.querySelectorAll(focusableSelectors))
            .filter(el => !el.hasAttribute('aria-hidden'));
    }

    /**
     * Get first focusable element
     */
    getFirstFocusableElement(container) {
        const focusableElements = this.getFocusableElements(container);
        return focusableElements[0];
    }

    /**
     * Announce page load
     */
    announcePageLoad() {
        setTimeout(() => {
            const pageTitle = document.title;
            const mainHeading = document.querySelector('h1, h2')?.textContent;
            const message = `${pageTitle} loaded. ${mainHeading || 'Dashboard ready for use.'}`;
            this.announce(message);
        }, 1000);
    }

    /**
     * Update form field validation
     */
    updateFieldValidation(field, isValid, errorMessage = '') {
        field.setAttribute('aria-invalid', !isValid);
        
        const errorId = `${field.id}-error`;
        let errorElement = document.getElementById(errorId);
        
        if (!isValid && errorMessage) {
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.id = errorId;
                errorElement.className = 'form-error';
                errorElement.setAttribute('role', 'alert');
                field.parentNode.appendChild(errorElement);
                
                // Link error to field
                const describedBy = field.getAttribute('aria-describedby') || '';
                field.setAttribute('aria-describedby', `${describedBy} ${errorId}`.trim());
            }
            
            errorElement.textContent = errorMessage;
            this.announceFormError(field.labels?.[0]?.textContent || field.name, errorMessage);
        } else if (errorElement) {
            errorElement.textContent = '';
        }
    }

    /**
     * Announce dynamic content changes
     */
    announceContentChange(description) {
        this.announce(description);
    }

    /**
     * Setup keyboard shortcuts help
     */
    showKeyboardShortcuts() {
        const shortcuts = [
            'Alt + 1: Navigate to Overview',
            'Alt + 2: Navigate to Projects', 
            'Alt + 3: Navigate to Members',
            'Alt + 4: Navigate to Settings',
            'Escape: Close modal or dialog',
            'Tab: Navigate between elements',
            'Arrow keys: Navigate within tab groups'
        ];
        
        this.announce(`Keyboard shortcuts available: ${shortcuts.join('. ')}`);
    }
}

// Create global accessibility manager instance
window.a11y = new AccessibilityManager();

// Export for ES6 modules
export { AccessibilityManager };
export default AccessibilityManager;