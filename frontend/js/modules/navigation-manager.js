/**
 * Enhanced Navigation Manager
 * Advanced navigation UX with search, breadcrumbs, and shortcuts
 */
class NavigationManager {
    /**
     * Creates a new NavigationManager instance with enhanced UX features.
     *
     * Initializes the navigation system with search, breadcrumbs, keyboard shortcuts, and scroll
     * indicators. Manages tab navigation state, history tracking, and accessibility features.
     *
     * WHY: Provides a centralized navigation management system with advanced UX features like search,
     * keyboard shortcuts, and breadcrumb navigation, improving user productivity and accessibility.
     *
     * @constructor
     */
    constructor() {
        this.currentTab = 'overview';
        this.navigationHistory = ['overview'];
        this.searchTimeout = null;
        this.shortcuts = {
            '1': 'overview',
            '2': 'projects', 
            '3': 'members',
            '4': 'tracks',
            '5': 'assignments',
            '6': 'meeting-rooms',
            '7': 'settings'
        };
        
        this.tabMeta = {
            'overview': {
                title: 'Overview',
                description: 'Organization dashboard and statistics',
                icon: 'fas fa-chart-line',
                parent: null
            },
            'projects': {
                title: 'Projects',
                description: 'Manage organization projects',
                icon: 'fas fa-folder-open',
                parent: null
            },
            'project-details': {
                title: 'Project Details',
                description: 'Detailed project information',
                icon: 'fas fa-folder-open',
                parent: 'projects'
            },
            'members': {
                title: 'Members',
                description: 'Organization member management',
                icon: 'fas fa-users',
                parent: null
            },
            'tracks': {
                title: 'Learning Tracks',
                description: 'Educational content tracks',
                icon: 'fas fa-road',
                parent: null
            },
            'assignments': {
                title: 'Assignments',
                description: 'Member role assignments',
                icon: 'fas fa-user-tag',
                parent: null
            },
            'meeting-rooms': {
                title: 'Meeting Rooms',
                description: 'Virtual meeting room management',
                icon: 'fas fa-video',
                parent: null
            },
            'settings': {
                title: 'Settings',
                description: 'Organization configuration',
                icon: 'fas fa-cog',
                parent: null
            }
        };
        
        this.init();
    }

    /**
     * Initializes all navigation manager features and event listeners.
     *
     * Sets up navigation search, scroll indicators, keyboard shortcuts, tab enhancements,
     * and initial breadcrumb display. Called once during constructor initialization.
     *
     * WHY: Centralizes all initialization logic to ensure features are activated in the
     * correct order and all event listeners are properly registered.
     *
     * @returns {void}
     */
    init() {
        this.setupNavigationSearch();
        this.setupScrollIndicators();
        this.setupKeyboardShortcuts();
        this.setupTabEnhancements();
        this.updateBreadcrumbs();
        
        console.log('Navigation Manager initialized');
    }

    /**
     * Sets up the navigation search input with debounced search and keyboard event handling.
     *
     * Adds event listeners for input (debounced search), Enter key (execute search), and
     * Escape key (clear search). Implements 300ms debounce to avoid excessive searches.
     *
     * WHY: Search functionality helps users quickly find specific sections without manually
     * scanning through all tabs, especially useful for dashboards with many sections.
     *
     * @returns {void}
     */
    setupNavigationSearch() {
        const searchInput = document.getElementById('navSearchInput');
        if (!searchInput) return;

        searchInput.addEventListener('input', (event) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.handleNavigationSearch(event.target.value);
            }, 300);
        });

        searchInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                this.executeSearch(event.target.value);
            } else if (event.key === 'Escape') {
                event.target.value = '';
                this.clearSearchHighlights();
            }
        });
    }

    /**
     * Handles navigation search by filtering and highlighting matching tabs.
     *
     * Searches through all tab titles and descriptions for the query string (case-insensitive).
     * Adds 'search-highlight' class to matching tabs and announces results to screen readers.
     *
     * WHY: Visual highlighting helps users identify matching sections at a glance, while
     * screen reader announcements ensure accessibility for vision-impaired users.
     *
     * @param {string} query - The search query entered by the user
     * @returns {void}
     */
    handleNavigationSearch(query) {
        if (!query.trim()) {
            this.clearSearchHighlights();
            return;
        }

        const tabs = document.querySelectorAll('.nav-tab');
        let matches = [];

        tabs.forEach(tab => {
            const tabName = tab.getAttribute('data-tab');
            const tabMeta = this.tabMeta[tabName];
            
            if (tabMeta) {
                const searchText = `${tabMeta.title} ${tabMeta.description}`.toLowerCase();
                const isMatch = searchText.includes(query.toLowerCase());
                
                if (isMatch) {
                    matches.push(tab);
                    tab.classList.add('search-highlight');
                } else {
                    tab.classList.remove('search-highlight');
                }
            }
        });

        // Announce search results to screen readers
        if (window.a11y) {
            window.a11y.announce(`Found ${matches.length} matching sections for "${query}"`);
        }
    }

    /**
     * Executes the search by navigating to the first highlighted match.
     *
     * Finds the first tab with 'search-highlight' class, navigates to it, clears the search
     * input, and removes all highlights. Triggered when user presses Enter in search input.
     *
     * WHY: Enter key should perform an action (navigate) rather than just highlighting,
     * providing a faster keyboard-based workflow for power users.
     *
     * @param {string} query - The search query (unused but kept for interface consistency)
     * @returns {void}
     */
    executeSearch(query) {
        const highlightedTab = document.querySelector('.nav-tab.search-highlight');
        if (highlightedTab) {
            const tabName = highlightedTab.getAttribute('data-tab');
            this.navigateToTab(tabName);
            
            // Clear search
            document.getElementById('navSearchInput').value = '';
            this.clearSearchHighlights();
        }
    }

    /**
     * Removes the 'search-highlight' class from all tabs.
     *
     * Clears visual highlighting from tabs after search is executed or cancelled.
     * Used when user presses Escape or completes a search.
     *
     * WHY: Highlighted tabs should only show during active search to avoid visual clutter
     * and confusion about the current navigation state.
     *
     * @returns {void}
     */
    clearSearchHighlights() {
        document.querySelectorAll('.nav-tab.search-highlight').forEach(tab => {
            tab.classList.remove('search-highlight');
        });
    }

    /**
     * Sets up visual indicators showing when tab navigation is scrollable.
     *
     * Adds CSS classes 'scrollable-left' and 'scrollable-right' to indicate scroll availability.
     * Updates indicators on scroll and window resize events to reflect current state.
     *
     * WHY: Users need visual feedback when tab navigation extends beyond viewport width,
     * indicating that more tabs are available by scrolling horizontally.
     *
     * @returns {void}
     */
    setupScrollIndicators() {
        const navTabs = document.querySelector('.nav-tabs');
        if (!navTabs) return;

    /**
     * UPDATE SCROLL INDICATORS STATE
     * PURPOSE: Update scroll indicators state
     * WHY: Keeps application state synchronized with user actions and data changes
     *
     * @throws {Error} If operation fails or validation errors occur
     */
        const updateScrollIndicators = () => {
            const canScrollLeft = navTabs.scrollLeft > 0;
            const canScrollRight = navTabs.scrollLeft < (navTabs.scrollWidth - navTabs.clientWidth);
            
            navTabs.classList.toggle('scrollable-left', canScrollLeft);
            navTabs.classList.toggle('scrollable-right', canScrollRight);
        };

        navTabs.addEventListener('scroll', updateScrollIndicators);
        window.addEventListener('resize', updateScrollIndicators);
        
        // Initial check
        setTimeout(updateScrollIndicators, 100);
    }

    /**
     * Sets up global keyboard shortcuts for navigation and search.
     *
     * Registers shortcuts: Alt+1-7 (navigate to specific tabs), Ctrl+/ (focus search),
     * Shift+? (show shortcuts help), and Escape (hide shortcuts). Skips shortcuts when
     * user is typing in input fields.
     *
     * WHY: Keyboard shortcuts dramatically improve productivity for power users who prefer
     * keyboard navigation over mouse clicks, reducing time to switch between sections.
     *
     * @returns {void}
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Skip if user is typing in input fields
            if (event.target.matches('input, textarea, select, [contenteditable]')) {
                return;
            }

            // Number key shortcuts (1-7 for tabs)
            if (event.altKey && this.shortcuts[event.key]) {
                event.preventDefault();
                this.navigateToTab(this.shortcuts[event.key]);
            }
            
            // Additional shortcuts
            switch (event.key) {
                case '/':
                    if (event.ctrlKey || event.metaKey) {
                        event.preventDefault();
                        this.focusSearch();
                    }
                    break;
                case '?':
                    if (event.shiftKey) {
                        event.preventDefault();
                        this.showKeyboardShortcuts();
                    }
                    break;
                case 'Escape':
                    this.hideKeyboardShortcuts();
                    break;
            }
        });
    }

    /**
     * Focuses and selects all text in the navigation search input.
     *
     * Programmatically focuses the search input and selects its current content for easy
     * replacement. Triggered by Ctrl+/ keyboard shortcut.
     *
     * WHY: Quick access to search via keyboard shortcut enables faster navigation workflow,
     * and selecting existing text allows immediate typing without manual clearing.
     *
     * @returns {void}
     */
    focusSearch() {
        const searchInput = document.getElementById('navSearchInput');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    /**
     * Enhances all navigation tabs with tooltips, click handlers, and context menus.
     *
     * Adds title attributes with descriptions for tooltips, click event handlers for
     * navigation, and right-click context menus for additional actions.
     *
     * WHY: Tooltips provide helpful descriptions on hover, click handlers centralize navigation
     * logic, and context menus offer power-user features like bookmarking and section info.
     *
     * @returns {void}
     */
    setupTabEnhancements() {
        const tabs = document.querySelectorAll('.nav-tab');
        
        tabs.forEach(tab => {
            // Add tooltip with description
            const tabName = tab.getAttribute('data-tab');
            const tabMeta = this.tabMeta[tabName];
            
            if (tabMeta) {
                tab.setAttribute('title', tabMeta.description);
            }
            
            // Enhanced click handling
            tab.addEventListener('click', (event) => {
                event.preventDefault();
                this.navigateToTab(tabName);
            });
            
            // Right-click context menu
            tab.addEventListener('contextmenu', (event) => {
                event.preventDefault();
                this.showTabContextMenu(event, tab);
            });
        });
    }

    /**
     * Navigates to the specified tab with enhanced UX features.
     *
     * Updates navigation history, scrolls tab into view if needed, updates breadcrumbs,
     * triggers the actual tab change via orgAdmin.showTab(), and announces navigation to
     * screen readers for accessibility.
     *
     * WHY: Centralized navigation method ensures consistent behavior across all navigation
     * triggers (clicks, keyboard shortcuts, search) and handles all UX concerns in one place.
     *
     * @param {string} tabName - The tab identifier to navigate to (e.g., 'overview', 'projects')
     * @returns {void}
     */
    navigateToTab(tabName) {
        const tab = document.querySelector(`[data-tab="${tabName}"]`);
        if (!tab) return;

        // Update navigation history
        if (this.currentTab !== tabName) {
            this.navigationHistory.push(tabName);
            if (this.navigationHistory.length > 10) {
                this.navigationHistory.shift();
            }
        }

        this.currentTab = tabName;
        
        // Scroll tab into view if needed
        this.scrollTabIntoView(tab);
        
        // Update breadcrumbs
        this.updateBreadcrumbs();
        
        // Trigger tab change (this will be handled by existing dashboard code)
        if (window.orgAdmin && typeof window.orgAdmin.showTab === 'function') {
            window.orgAdmin.showTab(tabName);
        }
        
        // Announce navigation
        const tabMeta = this.tabMeta[tabName];
        if (window.a11y && tabMeta) {
            window.a11y.announcePageChange(tabMeta.title, tabMeta.description);
        }
    }

    /**
     * Smoothly scrolls a tab into view if it's outside the visible navigation area.
     *
     * Checks if the tab is partially or fully outside the navigation container's viewport
     * and smoothly scrolls it to center if needed. Uses smooth scrolling for better UX.
     *
     * WHY: When navigating via keyboard shortcuts or search, the target tab may be off-screen.
     * Auto-scrolling ensures the active tab is always visible without manual scrolling.
     *
     * @param {HTMLElement} tab - The tab element to scroll into view
     * @returns {void}
     */
    scrollTabIntoView(tab) {
        const navTabs = document.querySelector('.nav-tabs');
        if (!navTabs) return;

        const tabRect = tab.getBoundingClientRect();
        const navRect = navTabs.getBoundingClientRect();
        
        if (tabRect.left < navRect.left || tabRect.right > navRect.right) {
            tab.scrollIntoView({
                behavior: 'smooth',
                inline: 'center'
            });
        }
    }

    /**
     * Updates the breadcrumb navigation trail based on the current tab.
     *
     * Shows hierarchical breadcrumb trail for nested pages (e.g., Dashboard > Projects > Project Details).
     * Hides breadcrumbs for top-level pages. Adds click handlers to breadcrumb links.
     *
     * WHY: Breadcrumbs help users understand their current locations in the hierarchy and provide
     * quick navigation back to parent sections without using browser back button.
     *
     * @returns {void}
     */
    updateBreadcrumbs() {
        const breadcrumbNav = document.getElementById('breadcrumbNav');
        const breadcrumbContent = document.getElementById('breadcrumbContent');
        const currentBreadcrumb = document.getElementById('currentBreadcrumb');
        
        if (!breadcrumbContent || !currentBreadcrumb) return;

        const tabMeta = this.tabMeta[this.currentTab];
        if (!tabMeta) return;

        // Show breadcrumbs for nested pages
        if (tabMeta.parent) {
            breadcrumbNav.classList.add('active');
            
            const parentMeta = this.tabMeta[tabMeta.parent];
            breadcrumbContent.innerHTML = `
                <div class="breadcrumb-item">
                    <a href="#" data-tab="overview">Dashboard</a>
                </div>
                <div class="breadcrumb-item">
                    <a href="#" data-tab="${tabMeta.parent}">${parentMeta.title}</a>
                </div>
                <div class="breadcrumb-item current">
                    <span>${tabMeta.title}</span>
                </div>
            `;
            
            // Add click handlers for breadcrumb links
            breadcrumbContent.querySelectorAll('a[data-tab]').forEach(link => {
                link.addEventListener('click', (event) => {
                    event.preventDefault();
                    const targetTab = event.target.getAttribute('data-tab');
                    this.navigateToTab(targetTab);
                });
            });
        } else {
            breadcrumbNav.classList.remove('active');
        }
    }

    /**
     * Displays a right-click context menu for a navigation tab.
     *
     * Shows a menu with options to open the tab, bookmark it, or view section info.
     * Positions the menu at cursor locations and handles outside clicks for auto-close.
     *
     * WHY: Context menus provide power-user features and alternative navigation methods
     * without cluttering the main interface with additional buttons.
     *
     * @param {MouseEvent} event - The contextmenu event containing cursor position
     * @param {HTMLElement} tab - The tab element that was right-clicked
     * @returns {void}
     */
    showTabContextMenu(event, tab) {
        // Remove existing context menu
        const existingMenu = document.querySelector('.nav-context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }

        const tabName = tab.getAttribute('data-tab');
        const tabMeta = this.tabMeta[tabName];
        
        const contextMenu = document.createElement('div');
        contextMenu.className = 'nav-context-menu';
        contextMenu.innerHTML = `
            <div class="nav-context-item" data-action="open">
                <i class="fas fa-external-link-alt"></i>
                <span>Open ${tabMeta.title}</span>
            </div>
            <div class="nav-context-item" data-action="bookmark">
                <i class="fas fa-bookmark"></i>
                <span>Bookmark</span>
            </div>
            <div class="nav-context-item" data-action="info">
                <i class="fas fa-info-circle"></i>
                <span>Section Info</span>
            </div>
        `;

        // Position menu
        contextMenu.style.left = `${event.pageX}px`;
        contextMenu.style.top = `${event.pageY}px`;
        
        document.body.appendChild(contextMenu);
        
        // Show menu
        setTimeout(() => {
            contextMenu.classList.add('active');
        }, 10);

        // Handle menu actions
        contextMenu.addEventListener('click', (e) => {
            const action = e.target.closest('.nav-context-item')?.getAttribute('data-action');
            
            switch (action) {
                case 'open':
                    this.navigateToTab(tabName);
                    break;
                case 'bookmark':
                    this.bookmarkTab(tabName);
                    break;
                case 'info':
                    this.showTabInfo(tabName);
                    break;
            }
            
            contextMenu.remove();
        });

        // Close menu on outside click
    /**
     * HIDE MENU INTERFACE
     * PURPOSE: Hide menu interface
     * WHY: Improves UX by managing interface visibility and state
     *
     * @param {Event} e - Event object
     */
        const closeMenu = (e) => {
            if (!contextMenu.contains(e.target)) {
                contextMenu.remove();
                document.removeEventListener('click', closeMenu);
            }
        };
        
        setTimeout(() => {
            document.addEventListener('click', closeMenu);
        }, 10);
    }

    /**
     * Displays an overlay showing all available keyboard shortcuts.
     *
     * Shows a modal overlay listing all keyboard shortcuts with their functions. Auto-hides
     * after 10 seconds. Toggles off if called again while visible.
     *
     * WHY: Users need a way to discover and learn keyboard shortcuts without consulting
     * documentation. The overlay provides in-app help that's always accessible via Shift+?.
     *
     * @returns {void}
     */
    showKeyboardShortcuts() {
        // Remove existing shortcuts overlay
        const existingOverlay = document.querySelector('.nav-shortcuts');
        if (existingOverlay) {
            existingOverlay.remove();
            return;
        }

        const shortcutsOverlay = document.createElement('div');
        shortcutsOverlay.className = 'nav-shortcuts';
        shortcutsOverlay.innerHTML = `
            <h3>Keyboard Shortcuts</h3>
            <div class="shortcut-item">
                <span>Navigate to Overview</span>
                <div class="shortcut-keys">
                    <span class="shortcut-key">Alt</span>
                    <span class="shortcut-key">1</span>
                </div>
            </div>
            <div class="shortcut-item">
                <span>Navigate to Projects</span>
                <div class="shortcut-keys">
                    <span class="shortcut-key">Alt</span>
                    <span class="shortcut-key">2</span>
                </div>
            </div>
            <div class="shortcut-item">
                <span>Navigate to Members</span>
                <div class="shortcut-keys">
                    <span class="shortcut-key">Alt</span>
                    <span class="shortcut-key">3</span>
                </div>
            </div>
            <div class="shortcut-item">
                <span>Search Sections</span>
                <div class="shortcut-keys">
                    <span class="shortcut-key">Ctrl</span>
                    <span class="shortcut-key">/</span>
                </div>
            </div>
            <div class="shortcut-item">
                <span>Show This Help</span>
                <div class="shortcut-keys">
                    <span class="shortcut-key">?</span>
                </div>
            </div>
            <div class="shortcut-item">
                <span>Close Dialog</span>
                <div class="shortcut-keys">
                    <span class="shortcut-key">Esc</span>
                </div>
            </div>
        `;

        document.body.appendChild(shortcutsOverlay);
        
        // Show overlay
        setTimeout(() => {
            shortcutsOverlay.classList.add('active');
        }, 10);

        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.hideKeyboardShortcuts();
        }, 10000);
    }

    /**
     * Hides the keyboard shortcuts overlay with smooth fade-out animation.
     *
     * Removes the 'active' class for CSS transition, then removes the element from DOM
     * after animation completes (300ms delay).
     *
     * WHY: Smooth fade-out provides better UX than instant removal, and delayed DOM
     * removal allows CSS transitions to complete.
     *
     * @returns {void}
     */
    hideKeyboardShortcuts() {
        const overlay = document.querySelector('.nav-shortcuts');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
        }
    }

    /**
     * Bookmarks a tab for quick access (placeholder for future feature).
     *
     * Currently logs the bookmark action and announces it to screen readers. Intended
     * for future implementation of a bookmark/favorites system.
     *
     * WHY: Bookmarking frequently accessed sections would improve workflow efficiency.
     * Placeholder ensures consistent interface for future feature implementation.
     *
     * @param {string} tabName - The tab identifier to bookmark
     * @returns {void}
     */
    bookmarkTab(tabName) {
        const tabMeta = this.tabMeta[tabName];
        if (window.a11y) {
            window.a11y.announce(`${tabMeta.title} bookmarked`);
        }
        console.log(`Bookmarked: ${tabName}`);
    }

    /**
     * Shows detailed information about a specific tab section.
     *
     * Announces the tab's title and description to screen readers and logs to console.
     * Triggered from context menu "Section Info" option.
     *
     * WHY: Provides additional context about a section's purpose and contents, helpful
     * for new users or when section names are abbreviated.
     *
     * @param {string} tabName - The tab identifier to show info for
     * @returns {void}
     */
    showTabInfo(tabName) {
        const tabMeta = this.tabMeta[tabName];
        if (window.a11y) {
            window.a11y.announce(`${tabMeta.title}: ${tabMeta.description}`);
        }
        console.log(`Tab Info: ${tabMeta.title} - ${tabMeta.description}`);
    }

    /**
     * Returns a copy of the navigation history array.
     *
     * Provides access to the user's navigation path through the application. Returns a copy
     * to prevent external modification of the internal history state.
     *
     * WHY: Navigation history enables features like "back" navigation, analytics tracking
     * of user paths, and breadcrumb generation. Copy prevents external code from breaking state.
     *
     * @returns {Array<string>} Array of tab names in navigation order (most recent last)
     */
    getNavigationHistory() {
        return [...this.navigationHistory];
    }

    /**
     * Navigates back to the previously visited tab.
     *
     * Removes the current tab from history and navigates to the previous entry. Only works
     * if history contains more than one entry (current tab).
     *
     * WHY: Provides browser-like back navigation within the application, allowing users to
     * retrace their steps without manually clicking tabs or using browser back button.
     *
     * @returns {void}
     */
    goBack() {
        if (this.navigationHistory.length > 1) {
            this.navigationHistory.pop(); // Remove current
            const previousTab = this.navigationHistory[this.navigationHistory.length - 1];
            this.navigateToTab(previousTab);
        }
    }

    /**
     * Adds or updates a notification badge on a tab showing the notification count.
     *
     * Creates a badge element if it doesn't exist, updates the count display (shows "99+"
     * for counts over 99), and shows/hides based on count. Used for alerts, unread items, etc.
     *
     * WHY: Notification badges provide at-a-glance awareness of pending items or alerts in
     * other sections without navigating away from the current tab.
     *
     * @param {string} tabName - The tab identifier to add badge to
     * @param {number} count - The notification count to display (0 hides badge)
     * @returns {void}
     */
    addNotificationBadge(tabName, count) {
        const tab = document.querySelector(`[data-tab="${tabName}"]`);
        if (!tab) return;

        let badge = tab.querySelector('.badge');
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'badge';
            tab.appendChild(badge);
        }

        badge.textContent = count > 99 ? '99+' : count.toString();
        badge.style.display = count > 0 ? 'flex' : 'none';
    }

    /**
     * Removes the notification badge from a tab.
     *
     * Finds and removes the badge element from the specified tab. Used when notifications
     * are cleared or read by the user.
     *
     * WHY: Badges should be removed when no longer relevant to avoid badge fatigue and
     * maintain clean UI when there are no pending notifications.
     *
     * @param {string} tabName - The tab identifier to remove badge from
     * @returns {void}
     */
    removeNotificationBadge(tabName) {
        const tab = document.querySelector(`[data-tab="${tabName}"]`);
        if (!tab) return;

        const badge = tab.querySelector('.badge');
        if (badge) {
            badge.remove();
        }
    }
}

// Create global navigation manager instance
window.navManager = new NavigationManager();

// Export for ES6 modules
export { NavigationManager };
export default NavigationManager;