/**
 * User Onboarding and Help System
 * Interactive tutorials, guided tours, and contextual help
 */

class OnboardingSystem {
    constructor() {
        this.currentTour = null;
        this.currentStep = 0;
        this.tours = new Map();
        this.helpWidgetOpen = false;
        this.quickTipsOpen = false;
        this.userProgress = this.loadUserProgress();
        
        this.init();
    }

    /**
     * Initialize onboarding system
     */
    init() {
        this.createHelpWidget();
        this.createQuickTipsPanel();
        this.setupTours();
        this.checkFirstVisit();
        
        console.log('Onboarding System initialized');
    }

    /**
     * Load user progress from localStorage
     */
    loadUserProgress() {
        try {
            const saved = localStorage.getItem('course-creator-onboarding-progress');
            return saved ? JSON.parse(saved) : {
                completedTours: [],
                dismissedTips: [],
                firstVisit: true,
                lastHelpAccess: null
            };
        } catch (error) {
            console.warn('Failed to load onboarding progress:', error);
            return {
                completedTours: [],
                dismissedTips: [],
                firstVisit: true,
                lastHelpAccess: null
            };
        }
    }

    /**
     * Save user progress to localStorage
     */
    saveUserProgress() {
        try {
            localStorage.setItem('course-creator-onboarding-progress', JSON.stringify(this.userProgress));
        } catch (error) {
            console.warn('Failed to save onboarding progress:', error);
        }
    }

    /**
     * Check if this is user's first visit
     */
    checkFirstVisit() {
        if (this.userProgress.firstVisit) {
            setTimeout(() => {
                this.showWelcomeBanner();
            }, 1000);
        }
    }

    /**
     * Create help widget
     */
    createHelpWidget() {
        const widget = document.createElement('div');
        widget.className = 'help-widget';
        widget.innerHTML = `
            <button class="help-toggle" aria-label="Open help menu" id="helpToggle">
                <i class="fas fa-question" id="helpIcon"></i>
            </button>
            
            <div class="help-menu" id="helpMenu" role="menu" aria-labelledby="helpToggle">
                <div class="help-menu-header">
                    <div>
                        <h3 class="help-menu-title">Need Help?</h3>
                        <p class="help-menu-subtitle">Get started with our platform</p>
                    </div>
                </div>
                
                <a href="#" class="help-menu-item" data-action="start-tour" role="menuitem">
                    <div class="help-menu-item-icon">
                        <i class="fas fa-route"></i>
                    </div>
                    <div class="help-menu-item-content">
                        <div class="help-menu-item-title">Take a Tour</div>
                        <div class="help-menu-item-description">Interactive walkthrough</div>
                    </div>
                </a>
                
                <a href="#" class="help-menu-item" data-action="show-tips" role="menuitem">
                    <div class="help-menu-item-icon">
                        <i class="fas fa-lightbulb"></i>
                    </div>
                    <div class="help-menu-item-content">
                        <div class="help-menu-item-title">Quick Tips</div>
                        <div class="help-menu-item-description">Helpful shortcuts</div>
                    </div>
                </a>
                
                <a href="#" class="help-menu-item" data-action="show-shortcuts" role="menuitem">
                    <div class="help-menu-item-icon">
                        <i class="fas fa-keyboard"></i>
                    </div>
                    <div class="help-menu-item-content">
                        <div class="help-menu-item-title">Keyboard Shortcuts</div>
                        <div class="help-menu-item-description">Navigate faster</div>
                    </div>
                </a>
                
                <a href="#" class="help-menu-item" data-action="show-docs" role="menuitem">
                    <div class="help-menu-item-icon">
                        <i class="fas fa-book"></i>
                    </div>
                    <div class="help-menu-item-content">
                        <div class="help-menu-item-title">Documentation</div>
                        <div class="help-menu-item-description">Detailed guides</div>
                    </div>
                </a>
                
                <a href="#" class="help-menu-item" data-action="contact-support" role="menuitem">
                    <div class="help-menu-item-icon">
                        <i class="fas fa-life-ring"></i>
                    </div>
                    <div class="help-menu-item-content">
                        <div class="help-menu-item-title">Contact Support</div>
                        <div class="help-menu-item-description">Get personalized help</div>
                    </div>
                </a>
            </div>
        `;
        
        document.body.appendChild(widget);
        this.setupHelpWidgetEvents();
    }

    /**
     * Setup help widget event listeners
     */
    setupHelpWidgetEvents() {
        const toggle = document.getElementById('helpToggle');
        const menu = document.getElementById('helpMenu');
        const icon = document.getElementById('helpIcon');
        
        toggle.addEventListener('click', () => {
            this.toggleHelpMenu();
        });
        
        // Handle menu item clicks
        menu.addEventListener('click', (event) => {
            const item = event.target.closest('.help-menu-item');
            if (item) {
                event.preventDefault();
                const action = item.getAttribute('data-action');
                this.handleHelpAction(action);
                this.closeHelpMenu();
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.help-widget') && this.helpWidgetOpen) {
                this.closeHelpMenu();
            }
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.helpWidgetOpen) {
                this.closeHelpMenu();
            }
        });
    }

    /**
     * Toggle help menu
     */
    toggleHelpMenu() {
        if (this.helpWidgetOpen) {
            this.closeHelpMenu();
        } else {
            this.openHelpMenu();
        }
    }

    /**
     * Open help menu
     */
    openHelpMenu() {
        const menu = document.getElementById('helpMenu');
        const icon = document.getElementById('helpIcon');
        
        menu.classList.add('active');
        icon.className = 'fas fa-times';
        this.helpWidgetOpen = true;
        
        // Update last help access
        this.userProgress.lastHelpAccess = new Date().toISOString();
        this.saveUserProgress();
        
        // Announce to screen readers
        if (window.a11y) {
            window.a11y.announce('Help menu opened');
        }
    }

    /**
     * Close help menu
     */
    closeHelpMenu() {
        const menu = document.getElementById('helpMenu');
        const icon = document.getElementById('helpIcon');
        
        menu.classList.remove('active');
        icon.className = 'fas fa-question';
        this.helpWidgetOpen = false;
        
        if (window.a11y) {
            window.a11y.announce('Help menu closed');
        }
    }

    /**
     * Handle help menu actions
     */
    handleHelpAction(action) {
        switch (action) {
            case 'start-tour':
                this.startTour('dashboard-overview');
                break;
            case 'show-tips':
                this.showQuickTips();
                break;
            case 'show-shortcuts':
                if (window.navManager && typeof window.navManager.showKeyboardShortcuts === 'function') {
                    window.navManager.showKeyboardShortcuts();
                }
                break;
            case 'show-docs':
                this.showDocumentation();
                break;
            case 'contact-support':
                this.showContactSupport();
                break;
        }
    }

    /**
     * Setup predefined tours
     */
    setupTours() {
        // Dashboard Overview Tour
        this.tours.set('dashboard-overview', {
            title: 'Dashboard Overview',
            description: 'Learn how to navigate your organization dashboard',
            steps: [
                {
                    target: '#navigation',
                    title: 'Navigation Tabs',
                    content: 'Use these tabs to navigate between different sections of your dashboard. You can also use Alt+1-7 keyboard shortcuts.',
                    icon: 'fas fa-compass',
                    position: 'bottom'
                },
                {
                    target: '.stat-cards-grid',
                    title: 'Key Metrics',
                    content: 'Monitor your organization\'s performance with these real-time statistics and trend indicators.',
                    icon: 'fas fa-chart-bar',
                    position: 'bottom'
                },
                {
                    target: '#activity-chart',
                    title: 'Activity Analytics',
                    content: 'Track learning activity trends over different time periods. Click the period buttons to change the view.',
                    icon: 'fas fa-chart-line',
                    position: 'top'
                },
                {
                    target: '#projects-table',
                    title: 'Projects Overview',
                    content: 'View and manage all your active projects. Click column headers to sort, and use action buttons to export data.',
                    icon: 'fas fa-table',
                    position: 'top'
                },
                {
                    target: '.help-widget',
                    title: 'Help is Always Available',
                    content: 'Click here anytime you need assistance. We\'ll guide you through any feature or answer your questions.',
                    icon: 'fas fa-life-ring',
                    position: 'left'
                }
            ]
        });

        // Project Management Tour
        this.tours.set('project-management', {
            title: 'Project Management',
            description: 'Master project creation and management',
            steps: [
                {
                    target: '[data-tab="projects"]',
                    title: 'Projects Section',
                    content: 'Click here to access all project management features.',
                    icon: 'fas fa-folder-open',
                    position: 'bottom'
                }
            ]
        });
    }

    /**
     * Start a guided tour
     */
    startTour(tourId) {
        const tour = this.tours.get(tourId);
        if (!tour) {
            console.warn(`Tour ${tourId} not found`);
            return;
        }

        this.currentTour = tour;
        this.currentStep = 0;
        
        // Create overlay
        this.createTourOverlay();
        
        // Show first step
        this.showTourStep();
        
        if (window.a11y) {
            window.a11y.announce(`Started ${tour.title} tour`);
        }
    }

    /**
     * Create tour overlay
     */
    createTourOverlay() {
        // Remove existing overlay
        const existing = document.querySelector('.onboarding-overlay');
        if (existing) {
            existing.remove();
        }

        const overlay = document.createElement('div');
        overlay.className = 'onboarding-overlay';
        overlay.innerHTML = '<div class="onboarding-spotlight"></div>';
        
        document.body.appendChild(overlay);
        
        // Activate overlay
        setTimeout(() => {
            overlay.classList.add('active');
        }, 10);
    }

    /**
     * Show current tour step
     */
    showTourStep() {
        if (!this.currentTour || this.currentStep >= this.currentTour.steps.length) {
            return;
        }

        const step = this.currentTour.steps[this.currentStep];
        const target = document.querySelector(step.target);
        
        if (!target) {
            console.warn(`Tour target ${step.target} not found`);
            this.nextStep();
            return;
        }

        // Update spotlight
        this.updateSpotlight(target);
        
        // Create step popup
        this.createStepPopup(step, target);
    }

    /**
     * Update spotlight position
     */
    updateSpotlight(target) {
        const spotlight = document.querySelector('.onboarding-spotlight');
        if (!spotlight) return;

        const rect = target.getBoundingClientRect();
        const padding = 8;
        
        spotlight.style.left = `${rect.left - padding}px`;
        spotlight.style.top = `${rect.top - padding}px`;
        spotlight.style.width = `${rect.width + padding * 2}px`;
        spotlight.style.height = `${rect.height + padding * 2}px`;
    }

    /**
     * Create step popup
     */
    createStepPopup(step, target) {
        // Remove existing popup
        const existing = document.querySelector('.tour-step');
        if (existing) {
            existing.remove();
        }

        const popup = document.createElement('div');
        popup.className = `tour-step position-${step.position}`;
        
        const progress = ((this.currentStep + 1) / this.currentTour.steps.length) * 100;
        
        popup.innerHTML = `
            <div class="tour-step-header">
                <div class="tour-step-icon">
                    <i class="${step.icon}"></i>
                </div>
                <h3 class="tour-step-title">${step.title}</h3>
                <div class="tour-step-counter">${this.currentStep + 1}/${this.currentTour.steps.length}</div>
            </div>
            
            <div class="tour-step-content">
                ${step.content}
            </div>
            
            <div class="tour-step-actions">
                <div class="tour-progress">
                    <div class="tour-progress-fill" style="width: ${progress}%"></div>
                </div>
                
                <div class="tour-controls">
                    ${this.currentStep > 0 ? 
                        '<button class="tour-btn tour-btn-secondary" data-action="prev">Previous</button>' : 
                        '<button class="tour-btn tour-btn-ghost" data-action="skip">Skip Tour</button>'
                    }
                    
                    ${this.currentStep < this.currentTour.steps.length - 1 ? 
                        '<button class="tour-btn tour-btn-primary" data-action="next">Next</button>' : 
                        '<button class="tour-btn tour-btn-primary" data-action="finish">Finish</button>'
                    }
                </div>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        // Position popup
        this.positionStepPopup(popup, target, step.position);
        
        // Setup event listeners
        this.setupStepEvents(popup);
        
        // Activate popup
        setTimeout(() => {
            popup.classList.add('active');
        }, 10);
    }

    /**
     * Position step popup relative to target
     */
    positionStepPopup(popup, target, position) {
        const targetRect = target.getBoundingClientRect();
        const popupRect = popup.getBoundingClientRect();
        const spacing = 20;
        
        let left, top;
        
        switch (position) {
            case 'bottom':
                left = targetRect.left + (targetRect.width / 2) - (popupRect.width / 2);
                top = targetRect.bottom + spacing;
                break;
            case 'top':
                left = targetRect.left + (targetRect.width / 2) - (popupRect.width / 2);
                top = targetRect.top - popupRect.height - spacing;
                break;
            case 'left':
                left = targetRect.left - popupRect.width - spacing;
                top = targetRect.top + (targetRect.height / 2) - (popupRect.height / 2);
                break;
            case 'right':
                left = targetRect.right + spacing;
                top = targetRect.top + (targetRect.height / 2) - (popupRect.height / 2);
                break;
        }
        
        // Ensure popup stays within viewport
        left = Math.max(10, Math.min(left, window.innerWidth - popupRect.width - 10));
        top = Math.max(10, Math.min(top, window.innerHeight - popupRect.height - 10));
        
        popup.style.left = `${left}px`;
        popup.style.top = `${top}px`;
    }

    /**
     * Setup step event listeners
     */
    setupStepEvents(popup) {
        popup.addEventListener('click', (event) => {
            const action = event.target.getAttribute('data-action');
            
            switch (action) {
                case 'next':
                    this.nextStep();
                    break;
                case 'prev':
                    this.prevStep();
                    break;
                case 'skip':
                    this.skipTour();
                    break;
                case 'finish':
                    this.finishTour();
                    break;
            }
        });
    }

    /**
     * Move to next step
     */
    nextStep() {
        this.currentStep++;
        if (this.currentStep < this.currentTour.steps.length) {
            this.showTourStep();
        } else {
            this.finishTour();
        }
    }

    /**
     * Move to previous step
     */
    prevStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showTourStep();
        }
    }

    /**
     * Skip current tour
     */
    skipTour() {
        this.closeTour();
        
        if (window.a11y) {
            window.a11y.announce('Tour skipped');
        }
    }

    /**
     * Finish current tour
     */
    finishTour() {
        if (this.currentTour) {
            // Mark tour as completed
            const tourId = Array.from(this.tours.entries())
                .find(([, tour]) => tour === this.currentTour)?.[0];
            
            if (tourId && !this.userProgress.completedTours.includes(tourId)) {
                this.userProgress.completedTours.push(tourId);
                this.saveUserProgress();
            }
        }
        
        this.closeTour();
        
        if (window.a11y) {
            window.a11y.announce('Tour completed successfully');
        }
    }

    /**
     * Close current tour
     */
    closeTour() {
        // Remove overlay and popup
        const overlay = document.querySelector('.onboarding-overlay');
        const popup = document.querySelector('.tour-step');
        
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
        }
        
        if (popup) {
            popup.classList.remove('active');
            setTimeout(() => popup.remove(), 300);
        }
        
        this.currentTour = null;
        this.currentStep = 0;
    }

    /**
     * Show welcome banner for first-time users
     */
    showWelcomeBanner() {
        const overviewPanel = document.getElementById('overview-panel');
        if (!overviewPanel) return;

        const banner = document.createElement('div');
        banner.className = 'welcome-banner';
        banner.innerHTML = `
            <div class="welcome-banner-content">
                <h2 class="welcome-banner-title">Welcome to Course Creator Platform! 🎉</h2>
                <p class="welcome-banner-subtitle">
                    Let's get you started with a quick tour of your organization dashboard.
                </p>
                <div class="welcome-banner-actions">
                    <button class="welcome-banner-btn primary" onclick="window.onboarding.startTour('dashboard-overview')">
                        <i class="fas fa-play"></i> Start Tour
                    </button>
                    <button class="welcome-banner-btn" onclick="window.onboarding.dismissWelcome()">
                        <i class="fas fa-times"></i> Maybe Later
                    </button>
                </div>
            </div>
        `;
        
        // Insert banner at the top of overview panel
        overviewPanel.insertBefore(banner, overviewPanel.firstChild);
        
        // Mark as no longer first visit
        this.userProgress.firstVisit = false;
        this.saveUserProgress();
    }

    /**
     * Dismiss welcome banner
     */
    dismissWelcome() {
        const banner = document.querySelector('.welcome-banner');
        if (banner) {
            banner.style.opacity = '0';
            banner.style.transform = 'translateY(-20px)';
            setTimeout(() => banner.remove(), 300);
        }
        
        if (window.a11y) {
            window.a11y.announce('Welcome banner dismissed');
        }
    }

    /**
     * Create quick tips panel
     */
    createQuickTipsPanel() {
        const panel = document.createElement('div');
        panel.className = 'quick-tips-panel';
        panel.id = 'quickTipsPanel';
        panel.innerHTML = `
            <div class="quick-tips-header">
                <h3 class="quick-tips-title">Quick Tips</h3>
                <button class="quick-tips-close" aria-label="Close quick tips">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="quick-tips-content">
                <div class="quick-tip-item">
                    <div class="quick-tip-number">1</div>
                    <div class="quick-tip-text">
                        Use <strong>Alt + 1-7</strong> to quickly navigate between dashboard sections.
                    </div>
                </div>
                
                <div class="quick-tip-item">
                    <div class="quick-tip-number">2</div>
                    <div class="quick-tip-text">
                        Search dashboard sections by pressing <strong>Ctrl + /</strong> and typing keywords.
                    </div>
                </div>
                
                <div class="quick-tip-item">
                    <div class="quick-tip-number">3</div>
                    <div class="quick-tip-text">
                        Click on chart period buttons (7D, 30D, 90D) to view different time ranges.
                    </div>
                </div>
                
                <div class="quick-tip-item">
                    <div class="quick-tip-number">4</div>
                    <div class="quick-tip-text">
                        Right-click on navigation tabs for additional context menu options.
                    </div>
                </div>
                
                <div class="quick-tip-item">
                    <div class="quick-tip-number">5</div>
                    <div class="quick-tip-text">
                        Press <strong>?</strong> to view all available keyboard shortcuts.
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        
        // Setup close button
        panel.querySelector('.quick-tips-close').addEventListener('click', () => {
            this.hideQuickTips();
        });
    }

    /**
     * Show quick tips panel
     */
    showQuickTips() {
        const panel = document.getElementById('quickTipsPanel');
        if (panel) {
            panel.classList.add('active');
            this.quickTipsOpen = true;
            
            if (window.a11y) {
                window.a11y.announce('Quick tips panel opened');
            }
            
            // Auto-hide after 15 seconds
            setTimeout(() => {
                if (this.quickTipsOpen) {
                    this.hideQuickTips();
                }
            }, 15000);
        }
    }

    /**
     * Hide quick tips panel
     */
    hideQuickTips() {
        const panel = document.getElementById('quickTipsPanel');
        if (panel) {
            panel.classList.remove('active');
            this.quickTipsOpen = false;
            
            if (window.a11y) {
                window.a11y.announce('Quick tips panel closed');
            }
        }
    }

    /**
     * Show documentation
     */
    showDocumentation() {
        // This would typically open a documentation modal or redirect to docs
        if (window.a11y) {
            window.a11y.announce('Opening documentation');
        }
        
        console.log('Documentation feature - would open comprehensive guides');
        alert('Documentation feature - In a real implementation, this would open comprehensive user guides and API documentation.');
    }

    /**
     * Show contact support
     */
    showContactSupport() {
        if (window.a11y) {
            window.a11y.announce('Opening support contact');
        }
        
        console.log('Contact support feature - would open support ticket system');
        alert('Contact Support feature - In a real implementation, this would open a support ticket system or live chat.');
    }

    /**
     * Add contextual help tooltip
     */
    addHelpTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'help-tooltip';
        tooltip.innerHTML = `
            <button class="help-tooltip-trigger" aria-label="Help information">
                <i class="fas fa-question"></i>
            </button>
            <div class="help-tooltip-content" role="tooltip">
                ${text}
            </div>
        `;
        
        element.appendChild(tooltip);
        return tooltip;
    }

    /**
     * Highlight new features
     */
    highlightFeature(selector, duration = 5000) {
        const element = document.querySelector(selector);
        if (element) {
            element.classList.add('feature-highlight');
            
            setTimeout(() => {
                element.classList.remove('feature-highlight');
            }, duration);
        }
    }

    /**
     * Check if tour is completed
     */
    isTourCompleted(tourId) {
        return this.userProgress.completedTours.includes(tourId);
    }

    /**
     * Reset user progress (for testing)
     */
    resetProgress() {
        this.userProgress = {
            completedTours: [],
            dismissedTips: [],
            firstVisit: true,
            lastHelpAccess: null
        };
        this.saveUserProgress();
        
        if (window.a11y) {
            window.a11y.announce('Onboarding progress reset');
        }
    }
}

// Create global onboarding instance
window.onboarding = new OnboardingSystem();

// Export for ES6 modules
export { OnboardingSystem };
export default OnboardingSystem;