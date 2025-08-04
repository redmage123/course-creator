/**
 * DASHBOARD NAVIGATION MODULE - SINGLE PAGE APPLICATION ROUTING AND UI MANAGEMENT
 * 
 * PURPOSE: Comprehensive navigation system for Course Creator dashboard interfaces
 * WHY: Modern web applications need seamless navigation without page reloads for better UX
 * ARCHITECTURE: Single-page application (SPA) routing with state management and persistence
 * 
 * CORE RESPONSIBILITIES:
 * - Section-based navigation within dashboard pages
 * - Sidebar collapse/expand functionality with state persistence
 * - Browser history management for proper back/forward navigation
 * - URL synchronization with current dashboard state
 * - Section-specific initialization and data loading
 * - Responsive design support with mobile-friendly navigation
 * 
 * BUSINESS REQUIREMENTS:
 * - Instructor workflow: Overview → Courses → Create Course → Analytics
 * - Student workflow: Overview → Enrolled Courses → Course Content
 * - Admin workflow: Overview → Student Management → Analytics
 * - Persistent UI state across browser sessions
 * - Professional navigation experience matching modern web standards
 * 
 * DASHBOARD SECTIONS SUPPORTED:
 * - Overview: Dashboard summary and quick actions
 * - Courses: Course management and viewing
 * - Create Course: AI-powered course creation interface
 * - Published Courses: Published course management
 * - Course Instances: Session-specific course management
 * - Students: Student enrollment and progress management
 * - Analytics: Performance metrics and insights
 * - Content: Course content management and editing
 * 
 * TECHNICAL FEATURES:
 * - State persistence using localStorage
 * - Custom event system for inter-module communication
 * - URL parameter synchronization
 * - Breadcrumb navigation support
 * - Responsive sidebar with mobile optimization
 * - Section-specific lazy loading and initialization
 */

export class DashboardNavigation {
    /**
     * DASHBOARD NAVIGATION CONSTRUCTOR
     * PURPOSE: Initialize navigation system with default state and supported sections
     * WHY: Proper initialization ensures consistent navigation behavior across all dashboards
     * 
     * INITIALIZATION COMPONENTS:
     * - Default section: 'overview' (safe fallback for all user types)
     * - Sidebar state: Expanded by default for desktop experience
     * - Section registry: All supported dashboard sections for validation
     * - Automatic setup: Event listeners and state restoration
     */
    constructor() {
        // CURRENT NAVIGATION STATE: Track which section is currently active
        // WHY: Single source of truth for navigation state throughout the application
        this.currentSection = 'overview';  // Default to safe overview section
        
        // SIDEBAR UI STATE: Track sidebar collapse/expand status
        // WHY: Responsive design requires sidebar state management for mobile/desktop
        this.sidebarCollapsed = false;     // Start expanded for better desktop UX
        
        // SECTION REGISTRY: All valid dashboard sections for routing validation
        // WHY: Prevents navigation to non-existent sections and enables section validation
        this.sections = [
            'overview',          // Dashboard summary and quick actions
            'courses',           // Course listing and management
            'create-course',     // AI-powered course creation wizard
            'published-courses', // Published course management interface
            'course-instances',  // Session-specific course instance management
            'students',          // Student enrollment and progress tracking
            'analytics',         // Performance metrics and reporting dashboard
            'content'            // Course content editing and management
        ];
        
        // AUTOMATIC INITIALIZATION: Set up navigation system immediately
        // WHY: Constructor should establish fully functional navigation system
        this.initialize();
    }

    /**
     * NAVIGATION SYSTEM INITIALIZATION
     * PURPOSE: Set up complete navigation functionality including event handlers and state restoration
     * WHY: Two-phase initialization ensures DOM is ready before establishing navigation behavior
     * 
     * INITIALIZATION PHASES:
     * 1. Event listener setup: Establish user interaction handlers
     * 2. State restoration: Restore previous navigation state from storage/URL
     * 
     * SEPARATION OF CONCERNS: Keeps constructor lightweight and delegates specialized setup
     */
    initialize() {
        // PHASE 1: EVENT SYSTEM SETUP: Establish all user interaction handlers
        this.setupEventListeners();
        
        // PHASE 2: STATE RESTORATION: Restore previous session navigation state
        this.restoreNavigationState();
    }

    /**
     * COMPREHENSIVE EVENT LISTENER SETUP
     * PURPOSE: Establish all user interaction handlers for navigation functionality
     * WHY: Centralized event management ensures consistent behavior and easier maintenance
     * 
     * EVENT CATEGORIES:
     * 1. Sidebar controls: Toggle button for responsive design
     * 2. Navigation links: Section switching within dashboard
     * 3. Browser history: Back/forward button support
     * 
     * DESIGN PATTERNS:
     * - Event delegation where appropriate for performance
     * - Graceful degradation when elements don't exist
     * - Consistent event handling patterns across all interactions
     */
    setupEventListeners() {
        // SIDEBAR TOGGLE CONTROL: Responsive sidebar collapse/expand functionality
        // WHY: Mobile devices need collapsible sidebar to maximize content space
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // NAVIGATION LINK HANDLERS: Section switching via sidebar navigation
        // WHY: Data attributes provide clean separation between HTML structure and JavaScript behavior
        // PATTERN: Use data-section attribute to specify target section for each navigation link
        document.querySelectorAll('.nav-link[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                // PREVENT DEFAULT LINK BEHAVIOR: Stop browser from following href
                e.preventDefault();
                
                // EXTRACT TARGET SECTION: Get section name from data attribute
                const section = link.getAttribute('data-section');
                
                // NAVIGATE TO SECTION: Trigger section change with history management
                this.showSection(section);
            });
        });

        // BROWSER HISTORY INTEGRATION: Support back/forward buttons in browser
        // WHY: Users expect browser navigation controls to work with SPA navigation
        // TECHNICAL: Use History API to maintain proper browser navigation experience
        window.addEventListener('popstate', (e) => {
            // CHECK FOR NAVIGATION STATE: Only process events with section information
            if (e.state && e.state.section) {
                // RESTORE SECTION: Navigate without adding new history entry
                // WHY: Prevents infinite history loops when using back/forward buttons
                this.showSection(e.state.section, false);
            }
        });
    }

    /**
     * RESPONSIVE SIDEBAR TOGGLE FUNCTIONALITY
     * PURPOSE: Collapse/expand sidebar for responsive design and user preference
     * WHY: Mobile devices need space optimization, desktop users may prefer more content space
     * 
     * RESPONSIVE DESIGN STRATEGY:
     * - Mobile: Sidebar typically starts collapsed to maximize content area
     * - Desktop: Sidebar typically starts expanded for easy navigation access
     * - User control: Manual toggle overrides default responsive behavior
     * 
     * STATE MANAGEMENT:
     * - Internal state tracking for consistent behavior
     * - CSS class manipulation for visual transitions
     * - Persistent storage for user preference across sessions
     * 
     * UI ELEMENTS AFFECTED:
     * - Sidebar: Collapsed state changes width and content visibility
     * - Main content: Adjusts layout to accommodate sidebar state changes
     * - Navigation: Maintains functionality in both collapsed and expanded states
     */
    toggleSidebar() {
        // LOCATE UI ELEMENTS: Find sidebar and main content areas
        const sidebar = document.getElementById('dashboard-sidebar');
        const main = document.querySelector('.dashboard-main');
        
        // GRACEFUL DEGRADATION: Only proceed if required elements exist
        // WHY: Some dashboard pages may have different DOM structures
        if (sidebar && main) {
            // UPDATE INTERNAL STATE: Toggle collapse status
            this.sidebarCollapsed = !this.sidebarCollapsed;
            
            // APPLY VISUAL CHANGES: Update CSS classes for transitions
            // WHY: CSS classes enable smooth animations and responsive behavior
            sidebar.classList.toggle('collapsed', this.sidebarCollapsed);
            main.classList.toggle('sidebar-collapsed', this.sidebarCollapsed);
            
            // PERSIST USER PREFERENCE: Save state for future sessions
            // WHY: Users expect their UI preferences to persist across browser sessions
            localStorage.setItem('sidebarCollapsed', this.sidebarCollapsed);
        }
    }

    /**
     * CORE SECTION NAVIGATION SYSTEM
     * PURPOSE: Switch between dashboard sections with complete state management
     * WHY: Single-page application navigation requires coordinated UI updates and state persistence
     * 
     * NAVIGATION PROCESS:
     * 1. Validate target section exists in registry
     * 2. Hide all currently visible sections
     * 3. Show target section with appropriate display
     * 4. Update internal navigation state
     * 5. Synchronize UI indicators (active states, titles)
     * 6. Persist state to localStorage for session continuity
     * 7. Update browser URL and history for proper back/forward support
     * 8. Trigger section-specific initialization and data loading
     * 
     * BUSINESS LOGIC:
     * - Supports all Course Creator workflow patterns
     * - Maintains professional UX with smooth transitions
     * - Enables deep linking to specific dashboard sections
     * - Preserves user context across browser sessions
     * 
     * @param {string} sectionName - Target section identifier
     * @param {boolean} addToHistory - Whether to add navigation to browser history (default: true)
     */
    showSection(sectionName, addToHistory = true) {
        // SECTION VALIDATION: Ensure target section is supported
        // WHY: Prevents navigation to non-existent sections that would break the UI
        if (!this.sections.includes(sectionName)) {
            console.warn(`Unknown section: ${sectionName}`);
            return;  // Exit early for invalid section requests
        }

        // HIDE ALL CURRENT SECTIONS: Clear the display area for section switching
        // WHY: Single-page application requires manual DOM manipulation for section visibility
        this.sections.forEach(section => {
            const element = document.getElementById(`${section}-section`);
            if (element) {
                element.style.display = 'none';  // Hide section completely
            }
        });

        // SHOW TARGET SECTION: Make the requested section visible
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            // DISPLAY TARGET SECTION: Make section visible to user
            targetSection.style.display = 'block';
            
            // UPDATE INTERNAL STATE: Track current section for state management
            this.currentSection = sectionName;
            
            // SYNCHRONIZE UI INDICATORS: Update navigation highlighting and page title
            // WHY: Users need visual feedback about current location in the application
            this.updateNavigationState(sectionName);
            
            // PERSIST NAVIGATION STATE: Save for session continuity
            // WHY: Users expect to return to their last viewed section on page refresh
            localStorage.setItem('currentSection', sectionName);
            
            // BROWSER HISTORY MANAGEMENT: Update URL and history for proper back/forward support
            // WHY: Users expect browser navigation controls to work with SPA navigation
            if (addToHistory) {
                // UPDATE URL: Add section parameter to current URL
                const url = new URL(window.location);
                url.searchParams.set('section', sectionName);
                
                // ADD HISTORY ENTRY: Enable back/forward button functionality
                history.pushState({ section: sectionName }, '', url);
            }
            
            // SECTION-SPECIFIC INITIALIZATION: Load data and initialize components for the section
            // WHY: Different sections may require different data loading and component setup
            this.onSectionChanged(sectionName);
        }
    }

    /**
     * NAVIGATION UI STATE SYNCHRONIZATION
     * PURPOSE: Update all UI indicators to reflect the current active section
     * WHY: Users need clear visual feedback about their current location in the application
     * 
     * UI UPDATES PERFORMED:
     * 1. Sidebar navigation: Highlight active section link
     * 2. Page title: Update browser tab title for context
     * 3. Breadcrumbs: Update navigation breadcrumb trail (if present)
     * 4. Section headers: Update any section-specific UI elements
     * 
     * PROFESSIONAL UX STANDARDS:
     * - Clear active state indicators
     * - Descriptive page titles for browser tabs
     * - Consistent visual hierarchy
     * - Accessibility-compliant state changes
     * 
     * @param {string} activeSection - The section that should be marked as active
     */
    updateNavigationState(activeSection) {
        // SIDEBAR NAVIGATION HIGHLIGHTING: Update active states for navigation links
        // WHY: Users need to see which section they're currently viewing
        document.querySelectorAll('.nav-link').forEach(link => {
            // CLEAR ALL ACTIVE STATES: Reset highlighting for all navigation links
            link.classList.remove('active');
            
            // HIGHLIGHT CURRENT SECTION: Add active class to matching navigation link
            if (link.getAttribute('data-section') === activeSection) {
                link.classList.add('active');  // CSS will style this appropriately
            }
        });

        // BROWSER TAB TITLE UPDATES: Set descriptive titles for better user experience
        // WHY: Browser tab titles help users identify specific dashboard sections
        const sectionTitles = {
            'overview': 'Dashboard Overview',           // Main dashboard summary
            'courses': 'My Courses',                   // Course listing and management
            'create-course': 'Create Course',          // AI-powered course creation
            'published-courses': 'Published Courses',  // Published course management
            'course-instances': 'Course Instances',    // Session-specific management
            'students': 'Student Management',          // Enrollment and progress
            'analytics': 'Analytics Dashboard',        // Performance metrics
            'content': 'Course Content'               // Content editing and management
        };

        // UPDATE BROWSER TAB TITLE: Set descriptive title with Course Creator branding
        document.title = `${sectionTitles[activeSection] || 'Dashboard'} - Course Creator`;
    }

    /**
     * SECTION CHANGE EVENT COORDINATOR
     * PURPOSE: Coordinate all actions that should occur when navigating to a new section
     * WHY: Different sections require different data loading, initialization, and component setup
     * 
     * COORDINATION RESPONSIBILITIES:
     * 1. Inter-module communication: Notify other modules about section changes
     * 2. Section-specific initialization: Load data and components for target section
     * 3. Event system integration: Provide hooks for external modules to react to navigation
     * 4. Lazy loading: Initialize components only when needed for performance
     * 
     * BUSINESS BENEFITS:
     * - Faster initial page load (components initialized on demand)
     * - Cleaner separation of concerns between navigation and content modules
     * - Extensible system for adding new section-specific functionality
     * - Professional user experience with context-appropriate content loading
     * 
     * @param {string} sectionName - The section that was just navigated to
     */
    onSectionChanged(sectionName) {
        // INTER-MODULE COMMUNICATION: Dispatch custom event for other modules
        // WHY: Other modules may need to react to section changes (analytics, content loading, etc.)
        const event = new CustomEvent('sectionChanged', {
            detail: { 
                section: sectionName,              // Current section being shown
                previousSection: this.currentSection  // Previous section for context
            }
        });
        document.dispatchEvent(event);

        // SECTION-SPECIFIC INITIALIZATION: Load data and initialize components per section
        // WHY: Different sections have different data requirements and component needs
        // PATTERN: Switch statement enables easy addition of new section initialization logic
        switch (sectionName) {
            case 'courses':
                // COURSE MANAGEMENT: Load user's courses and course management interface
                this.initializeCoursesSection();
                break;
            case 'students':
                // STUDENT MANAGEMENT: Load enrolled students and progress tracking
                this.initializeStudentsSection();
                break;
            case 'analytics':
                // ANALYTICS DASHBOARD: Load performance metrics and reporting tools
                this.initializeAnalyticsSection();
                break;
            case 'published-courses':
                // PUBLISHED COURSES: Load published course management interface
                this.initializePublishedCoursesSection();
                break;
            case 'course-instances':
                // COURSE INSTANCES: Load session-specific course management
                this.initializeCourseInstancesSection();
                break;
            // NOTE: 'overview', 'create-course', and 'content' sections use default initialization
        }
    }

    /**
     * COURSES SECTION INITIALIZATION
     * PURPOSE: Initialize course management interface with user's course data
     * WHY: Course section requires dynamic loading of user-specific course information
     */
    initializeCoursesSection() {
        // LAZY LOADING: Load course data only when section is accessed
        // WHY: Improves initial page load performance by loading data on demand
        if (typeof window.loadUserCourses === 'function') {
            window.loadUserCourses();  // Load instructor's courses or student's enrolled courses
        }
    }

    /**
     * STUDENTS SECTION INITIALIZATION
     * PURPOSE: Initialize student management interface with enrollment data
     * WHY: Student section requires loading of enrollment and progress tracking data
     */
    initializeStudentsSection() {
        // STUDENT DATA LOADING: Load enrollment and progress information
        // WHY: Student management requires up-to-date enrollment and progress data
        if (typeof window.loadEnrolledStudents === 'function') {
            window.loadEnrolledStudents();  // Load students enrolled in instructor's courses
        }
    }

    /**
     * ANALYTICS SECTION INITIALIZATION
     * PURPOSE: Initialize analytics dashboard with performance metrics
     * WHY: Analytics section requires loading of usage statistics and performance data
     */
    initializeAnalyticsSection() {
        // ANALYTICS DATA LOADING: Load performance metrics and usage statistics
        // WHY: Analytics dashboard needs current data for meaningful insights
        if (typeof window.loadAnalytics === 'function') {
            window.loadAnalytics();  // Load course performance and student progress analytics
        }
    }

    /**
     * PUBLISHED COURSES SECTION INITIALIZATION
     * PURPOSE: Initialize published course management interface
     * WHY: Published courses section requires loading of published course data and management tools
     */
    initializePublishedCoursesSection() {
        // PUBLISHED COURSE DATA: Load published courses for management and monitoring
        // WHY: Published courses require different management interface than draft courses
        if (typeof window.loadPublishedCourses === 'function') {
            window.loadPublishedCourses();  // Load instructor's published courses
        }
    }

    /**
     * COURSE INSTANCES SECTION INITIALIZATION
     * PURPOSE: Initialize course instance management for session-specific operations
     * WHY: Course instances require session-specific data loading and management tools
     */
    initializeCourseInstancesSection() {
        // COURSE INSTANCE DATA: Load session-specific course instance information
        // WHY: Course instances have unique scheduling, enrollment, and management requirements
        if (typeof window.loadCourseInstances === 'function') {
            window.loadCourseInstances();  // Load course instances with scheduling and enrollment data
        }
    }

    /**
     * NAVIGATION STATE RESTORATION SYSTEM
     * PURPOSE: Restore previous navigation state when user returns to dashboard
     * WHY: Users expect to return to their last viewed section and UI preferences
     * 
     * STATE RESTORATION PRIORITY:
     * 1. URL parameters (highest priority - enables deep linking)
     * 2. localStorage saved state (user's last session state)
     * 3. Default 'overview' section (safe fallback for new users)
     * 
     * UI STATE RESTORED:
     * - Current dashboard section
     * - Sidebar collapse/expand state
     * - Navigation highlighting
     * - Browser history state
     * 
     * BUSINESS BENEFITS:
     * - Professional user experience with state continuity
     * - Deep linking support for sharing specific dashboard sections
     * - Reduced user friction when returning to application
     * - Consistent behavior across different browsers and devices
     */
    restoreNavigationState() {
        // SIDEBAR STATE RESTORATION: Restore user's preferred sidebar state
        // WHY: Users expect their UI preferences to persist across sessions
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed) {
            this.toggleSidebar();  // Apply collapsed state if previously set
        }

        // SECTION STATE RESTORATION: Determine which section to display
        // PRIORITY ORDER: URL parameter > localStorage > default fallback
        const urlParams = new URLSearchParams(window.location.search);
        const urlSection = urlParams.get('section');          // Deep linking support
        const savedSection = localStorage.getItem('currentSection');  // Session continuity
        
        // DETERMINE TARGET SECTION: Use priority order for state restoration
        const targetSection = urlSection || savedSection || 'overview';
        
        // RESTORE SECTION: Navigate to determined section without adding to history
        // WHY: Don't add history entry for initial state restoration
        this.showSection(targetSection, false);
    }

    getCurrentSection() {
        return this.currentSection;
    }

    isSidebarCollapsed() {
        return this.sidebarCollapsed;
    }

    // Public API for external access
    navigateTo(section) {
        this.showSection(section);
    }

    // Breadcrumb navigation support
    getBreadcrumbs() {
        const breadcrumbPaths = {
            'overview': ['Dashboard'],
            'courses': ['Dashboard', 'My Courses'],
            'create-course': ['Dashboard', 'Create Course'],
            'published-courses': ['Dashboard', 'Published Courses'],
            'course-instances': ['Dashboard', 'Course Instances'],
            'students': ['Dashboard', 'Students'],
            'analytics': ['Dashboard', 'Analytics'],
            'content': ['Dashboard', 'My Courses', 'Course Content']
        };

        return breadcrumbPaths[this.currentSection] || ['Dashboard'];
    }
}

// Global instance for backward compatibility
let navigationInstance = null;

// Initialize navigation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    navigationInstance = new DashboardNavigation();
    
    // Export to window for global access
    window.dashboardNavigation = navigationInstance;
    
    // Backward compatibility functions
    window.showSection = (section) => navigationInstance.showSection(section);
    window.toggleSidebar = () => navigationInstance.toggleSidebar();
});

export default DashboardNavigation;