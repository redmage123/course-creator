/**
 * Enhanced Navigation Manager
 * Advanced navigation UX with search, breadcrumbs, and shortcuts
 */

class NavigationManager {
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
     * Initialize navigation manager
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
     * Setup navigation search functionality
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
     * Handle navigation search
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
     * Execute search and navigate to first match
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
     * Clear search highlights
     */
    clearSearchHighlights() {
        document.querySelectorAll('.nav-tab.search-highlight').forEach(tab => {
            tab.classList.remove('search-highlight');
        });
    }

    /**
     * Setup scroll indicators for navigation tabs
     */
    setupScrollIndicators() {
        const navTabs = document.querySelector('.nav-tabs');
        if (!navTabs) return;

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
     * Setup enhanced keyboard shortcuts
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
     * Focus on search input
     */
    focusSearch() {
        const searchInput = document.getElementById('navSearchInput');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    /**
     * Setup tab enhancements
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
     * Navigate to tab with enhanced UX
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
     * Scroll tab into view
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
     * Update breadcrumb navigation
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
     * Show tab context menu
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
     * Show keyboard shortcuts overlay
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
     * Hide keyboard shortcuts overlay
     */
    hideKeyboardShortcuts() {
        const overlay = document.querySelector('.nav-shortcuts');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
        }
    }

    /**
     * Bookmark tab (placeholder for future feature)
     */
    bookmarkTab(tabName) {
        const tabMeta = this.tabMeta[tabName];
        if (window.a11y) {
            window.a11y.announce(`${tabMeta.title} bookmarked`);
        }
        console.log(`Bookmarked: ${tabName}`);
    }

    /**
     * Show tab information
     */
    showTabInfo(tabName) {
        const tabMeta = this.tabMeta[tabName];
        if (window.a11y) {
            window.a11y.announce(`${tabMeta.title}: ${tabMeta.description}`);
        }
        console.log(`Tab Info: ${tabMeta.title} - ${tabMeta.description}`);
    }

    /**
     * Get navigation history
     */
    getNavigationHistory() {
        return [...this.navigationHistory];
    }

    /**
     * Go back to previous tab
     */
    goBack() {
        if (this.navigationHistory.length > 1) {
            this.navigationHistory.pop(); // Remove current
            const previousTab = this.navigationHistory[this.navigationHistory.length - 1];
            this.navigateToTab(previousTab);
        }
    }

    /**
     * Add notification badge to tab
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
     * Remove notification badge from tab
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