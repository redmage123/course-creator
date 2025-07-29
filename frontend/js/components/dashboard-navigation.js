/**
 * Dashboard Navigation Module
 * Single Responsibility: Handle navigation between dashboard sections
 * Following SOLID principles with clean separation of concerns
 */

export class DashboardNavigation {
    constructor() {
        this.currentSection = 'overview';
        this.sidebarCollapsed = false;
        this.sections = [
            'overview', 'courses', 'create-course', 'published-courses',
            'course-instances', 'students', 'analytics', 'content'
        ];
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.restoreNavigationState();
    }

    setupEventListeners() {
        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // Navigation links
        document.querySelectorAll('.nav-link[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                this.showSection(section);
            });
        });

        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.section) {
                this.showSection(e.state.section, false);
            }
        });
    }

    toggleSidebar() {
        const sidebar = document.getElementById('dashboard-sidebar');
        const main = document.querySelector('.dashboard-main');
        
        if (sidebar && main) {
            this.sidebarCollapsed = !this.sidebarCollapsed;
            sidebar.classList.toggle('collapsed', this.sidebarCollapsed);
            main.classList.toggle('sidebar-collapsed', this.sidebarCollapsed);
            
            // Save state
            localStorage.setItem('sidebarCollapsed', this.sidebarCollapsed);
        }
    }

    showSection(sectionName, addToHistory = true) {
        if (!this.sections.includes(sectionName)) {
            console.warn(`Unknown section: ${sectionName}`);
            return;
        }

        // Hide all sections
        this.sections.forEach(section => {
            const element = document.getElementById(`${section}-section`);
            if (element) {
                element.style.display = 'none';
            }
        });

        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
            this.currentSection = sectionName;
            
            // Update navigation state
            this.updateNavigationState(sectionName);
            
            // Save to localStorage
            localStorage.setItem('currentSection', sectionName);
            
            // Add to browser history
            if (addToHistory) {
                const url = new URL(window.location);
                url.searchParams.set('section', sectionName);
                history.pushState({ section: sectionName }, '', url);
            }
            
            // Trigger section-specific initialization
            this.onSectionChanged(sectionName);
        }
    }

    updateNavigationState(activeSection) {
        // Update sidebar navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-section') === activeSection) {
                link.classList.add('active');
            }
        });

        // Update page title
        const sectionTitles = {
            'overview': 'Dashboard Overview',
            'courses': 'My Courses',
            'create-course': 'Create Course',
            'published-courses': 'Published Courses',
            'course-instances': 'Course Instances',
            'students': 'Student Management',
            'analytics': 'Analytics Dashboard',
            'content': 'Course Content'
        };

        document.title = `${sectionTitles[activeSection] || 'Dashboard'} - Course Creator`;
    }

    onSectionChanged(sectionName) {
        // Dispatch custom event for other modules to listen to
        const event = new CustomEvent('sectionChanged', {
            detail: { section: sectionName, previousSection: this.currentSection }
        });
        document.dispatchEvent(event);

        // Section-specific initialization
        switch (sectionName) {
            case 'courses':
                this.initializeCoursesSection();
                break;
            case 'students':
                this.initializeStudentsSection();
                break;
            case 'analytics':
                this.initializeAnalyticsSection();
                break;
            case 'published-courses':
                this.initializePublishedCoursesSection();
                break;
            case 'course-instances':
                this.initializeCourseInstancesSection();
                break;
        }
    }

    initializeCoursesSection() {
        // Trigger course loading if not already loaded
        if (typeof window.loadUserCourses === 'function') {
            window.loadUserCourses();
        }
    }

    initializeStudentsSection() {
        // Load student enrollment data
        if (typeof window.loadEnrolledStudents === 'function') {
            window.loadEnrolledStudents();
        }
    }

    initializeAnalyticsSection() {
        // Load analytics data
        if (typeof window.loadAnalytics === 'function') {
            window.loadAnalytics();
        }
    }

    initializePublishedCoursesSection() {
        // Load published courses
        if (typeof window.loadPublishedCourses === 'function') {
            window.loadPublishedCourses();
        }
    }

    initializeCourseInstancesSection() {
        // Load course instances
        if (typeof window.loadCourseInstances === 'function') {
            window.loadCourseInstances();
        }
    }

    restoreNavigationState() {
        // Restore sidebar state
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed) {
            this.toggleSidebar();
        }

        // Restore current section from URL or localStorage
        const urlParams = new URLSearchParams(window.location.search);
        const urlSection = urlParams.get('section');
        const savedSection = localStorage.getItem('currentSection');
        
        const targetSection = urlSection || savedSection || 'overview';
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