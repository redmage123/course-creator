/**
 * Organization Admin Dashboard - Core Module
 *
 * BUSINESS CONTEXT:
 * Core initialization and navigation logic for the organization admin dashboard.
 * Handles authentication state, tab switching, organization loading, and
 * coordination between all dashboard modules.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Dashboard initialization on page load
 * - Tab-based navigation system
 * - Organization context management
 * - Authentication verification
 * - Module coordination
 *
 * @module org-admin-core
 */
import { fetchOrganization, fetchCurrentUser, getAuthHeaders } from './org-admin-api.js';
import { showNotification } from './org-admin-utils.js';
import { activityTokenManager } from './activity-token-manager.js';

import { initializeProjectsManagement, loadProjectsData } from './org-admin-projects.js';
import { initializeInstructorsManagement, loadInstructorsData } from './org-admin-instructors.js';
import { initializeStudentsManagement, loadStudentsData } from './org-admin-students.js';
// import { initializeTracksManagement, loadTracksData } from './org-admin-tracks.js'; // OLD: Uses outdated schema
import { loadTracksData } from './org-admin/tracks-crud.js'; // NEW: TDD implementation matching course_creator.tracks
import { initializeSettingsManagement, loadSettingsData } from './org-admin-settings.js';

// Global state
let currentOrganization = null;
let currentOrganizationId = null;
let currentUser = null;

/**
 * Initialize organization admin dashboard
 *
 * BUSINESS LOGIC:
 * - Verifies user authentication
 * - Loads organization data from URL parameter
 * - Initializes all sub-modules
 * - Sets up event listeners
 * - Loads initial tab content
 *
 * @returns {Promise<void>}
 */
export async function initializeDashboard() {
    console.log('🚀 initializeDashboard called');

    // Set up navigation event listeners FIRST
    // This ensures tab navigation works even if API calls fail
    setupNavigationListeners();

    try {
        // Verify authentication
        const token = localStorage.getItem('authToken');
        const sessionStart = localStorage.getItem('sessionStart');
        const lastActivity = localStorage.getItem('lastActivity');

        console.log('🔍 localStorage check:', {
            hasToken: !!token,
            hasSessionStart: !!sessionStart,
            hasLastActivity: !!lastActivity,
            tokenPreview: token ? token.substring(0, 20) + '...' : 'none'
        });

        if (!token) {
            console.log('❌ No token found, redirecting to login');
            window.location.href = '../index.html';
            return;
        }

        // NOTE: Session monitoring is now started in the HTML inline script
        // This ensures it starts immediately when Auth module loads
        // The code below is kept as a backup in case HTML initialization fails
        if (window.Auth && !window.Auth.sessionCheckInterval) {
            console.log('🔐 Starting session monitoring from core (backup)...');
            window.Auth.startSessionMonitoring();
            window.Auth.activityTracker.start();
            console.log('✅ Session monitoring active (backup initialization)');
        } else if (window.Auth && window.Auth.sessionCheckInterval) {
            console.log('✅ Session monitoring already active from HTML initialization');
        } else {
            console.warn('⚠️ Auth module not available - session monitoring disabled');
        }

        // Set up logout handler early
        setupLogoutHandler();

        // Load current user
        currentUser = await fetchCurrentUser();
        console.log('Dashboard initialized for user:', currentUser.email);

        // Get organization ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const orgId = urlParams.get('org_id');

        if (!orgId) {
            showNotification('No organization specified. Please select your organization.', 'error');
            setTimeout(() => window.location.href = '../index.html', 2000);
            return;
        }

        // Load organization
        currentOrganizationId = orgId;
        currentOrganization = await fetchOrganization(orgId);
        console.log('Loaded organization:', currentOrganization.name);

        // Update UI with organization info
        updateOrganizationHeader(currentOrganization);

        // Initialize all sub-modules with organization context
        initializeProjectsManagement(orgId);
        initializeInstructorsManagement(orgId);
        initializeStudentsManagement(orgId);
        // initializeTracksManagement(orgId); // OLD: Not needed with new tracks-crud.js (gets org from URL)
        initializeSettingsManagement(orgId);

        // Load initial tab (overview) - AFTER modules are initialized
        await loadTabContent('overview');

        // Hide loading spinner after successful initialization
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
            console.log('✅ Loading spinner hidden');
        }

    } catch (error) {
        console.error('💥 Error initializing dashboard:', error);
        console.error('💥 Error stack:', error.stack);
        console.error('💥 Current user:', currentUser);
        console.error('💥 Org ID from URL:', new URLSearchParams(window.location.search).get('org_id'));
        showNotification(`Failed to initialize dashboard: ${error.message}`, 'error');

        // Hide loading spinner even on error
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
            console.log('⚠️  Loading spinner hidden (error state)');
        }

        // Don't redirect on error - let user see what happened
        // setTimeout(() => window.location.href = '../index.html', 5000);
    }
}

/**
 * Update organization header display
 *
 * BUSINESS CONTEXT:
 * Shows organization name, logo, and key info in dashboard header
 *
 * @param {Object} organization - Organization data object
 */
function updateOrganizationHeader(organization) {
    console.log('updateOrganizationHeader called with:', organization);

    // Update main dashboard title with organization name
    const orgTitleEl = document.getElementById('orgTitle');
    if (orgTitleEl) {
        orgTitleEl.textContent = `${organization.name} Organization Dashboard`;
        console.log('Set organization title to:', orgTitleEl.textContent);
    }

    // Update organization name in sidebar (if exists)
    const orgNameEl = document.getElementById('organizationName');
    console.log('organizationName element:', orgNameEl);
    if (orgNameEl) {
        orgNameEl.textContent = organization.name;
        console.log('Set organization name to:', organization.name);
    }

    // Update organization domain
    const orgDomainEl = document.getElementById('organizationDomain');
    console.log('organizationDomain element:', orgDomainEl);
    if (orgDomainEl && organization.domain) {
        orgDomainEl.textContent = organization.domain;
        console.log('Set organization domain to:', organization.domain);
    }

    // Update organization logo if present
    const orgLogoEl = document.getElementById('organizationLogo');
    if (orgLogoEl && organization.logo_url) {
        orgLogoEl.src = organization.logo_url;
        orgLogoEl.style.display = 'block';
    }

    // Update member count
    const memberCountEl = document.getElementById('totalMembers');
    if (memberCountEl) {
        memberCountEl.textContent = organization.member_count || 0;
    }

    // Update project count
    const projectCountEl = document.getElementById('totalProjects');
    if (projectCountEl) {
        projectCountEl.textContent = organization.project_count || 0;
    }
}

/**
 * Setup navigation event listeners
 *
 * TECHNICAL IMPLEMENTATION:
 * Attaches click handlers to all navigation links
 * Implements tab-based navigation with history support
 */
function setupNavigationListeners() {
    // Get all navigation links
    const navLinks = document.querySelectorAll('.nav-link[data-tab]');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();

            const tabName = link.getAttribute('data-tab');
            if (tabName) {
                loadTabContent(tabName);

                // Update active state
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                // Update URL without page reload
                const url = new URL(window.location);
                url.searchParams.set('tab', tabName);
                window.history.pushState({}, '', url);
            }
        });
    });

    // Handle browser back/forward
    window.addEventListener('popstate', () => {
        const urlParams = new URLSearchParams(window.location.search);
        const tabName = urlParams.get('tab') || 'overview';
        loadTabContent(tabName);
    });
}

/**
 * Load and display tab content
 *
 * BUSINESS LOGIC:
 * Hides all tab content and shows requested tab
 * Loads fresh data for the selected tab
 *
 * @param {string} tabName - Name of tab to load (overview, projects, instructors, students, tracks, settings)
 * @returns {Promise<void>}
 */
export async function loadTabContent(tabName) {
    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
        tab.style.display = 'none';
    });

    // Show target tab
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.classList.add('active');
        targetTab.style.display = 'block';
    }

    // Load tab-specific data
    try {
        switch (tabName) {
            case 'overview':
                await loadOverviewData();
                break;

            case 'projects':
                await loadProjectsData();
                break;

            case 'instructors':
                await loadInstructorsData();
                break;

            case 'students':
                await loadStudentsData();
                break;

            case 'tracks':
                await loadTracksData();
                break;

            case 'settings':
                await loadSettingsData();
                break;

            case 'courses':
                await loadCoursesData();
                break;

            default:
                console.warn(`Unknown tab: ${tabName}`);
        }
    } catch (error) {
        console.error(`Error loading ${tabName} data:`, error);
        showNotification(`Failed to load ${tabName} data`, 'error');
    }
}

/**
 * Load overview/dashboard data
 *
 * BUSINESS CONTEXT:
 * Shows high-level organization statistics and recent activity
 *
 * @returns {Promise<void>}
 */
async function loadOverviewData() {
    try {
        // Load summary statistics
        await Promise.all([
            loadProjectsData(),
            loadInstructorsData(),
            loadStudentsData(),
            loadTracksData()
        ]);

        // Load recent projects and activity
        await Promise.all([
            loadRecentProjects(),
            loadRecentActivity()
        ]);

    } catch (error) {
        console.error('Error loading overview:', error);
    }
}

/**
 * Load recent projects
 *
 * BUSINESS CONTEXT:
 * Shows the 5 most recently created or modified projects
 *
 * @returns {Promise<void>}
 */
async function loadRecentProjects() {
    const projectsEl = document.getElementById('recentProjects');
    if (!projectsEl) return;

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const orgId = urlParams.get('org_id');

        // Fetch projects from API (organization-specific endpoint)
        const response = await fetch(`/api/v1/organizations/${orgId}/projects`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch projects');
        }

        const projects = await response.json();

        // Sort by creation date (most recent first) and take top 5
        const recentProjects = projects
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 5);

        if (recentProjects.length === 0) {
            projectsEl.innerHTML = `
                <div style="padding: 2rem; text-align: center; background: var(--bg-secondary); border-radius: 8px;">
                    <div style="font-size: 2rem; margin-bottom: 0.75rem;">📁</div>
                    <p style="margin: 0; color: var(--text-muted); font-size: 0.875rem;">
                        No projects yet
                    </p>
                    <button class="btn btn-primary mt-md" onclick="showCreateProjectModal()" style="margin-top: 1rem;">
                        Create First Project
                    </button>
                </div>
            `;
        } else {
            projectsEl.innerHTML = `
                <div style="background: var(--bg-secondary); border-radius: 8px; padding: 1rem;">
                    ${recentProjects.map(project => `
                        <div style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); cursor: pointer;"
                             onclick="document.querySelector('[data-tab=projects]').click()">
                            <div style="font-weight: 500;">${escapeHtml(project.name)}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">
                                ${formatTimeAgo(project.created_at)}
                            </div>
                        </div>
                    `).join('')}
                </div>
                <button class="btn btn-outline mt-md" onclick="document.querySelector('[data-tab=projects]').click()" style="margin-top: 1rem; width: 100%;">
                    View All Projects
                </button>
            `;
        }
    } catch (error) {
        console.error('Error loading recent projects:', error);
        projectsEl.innerHTML = `
            <p style="color: var(--text-muted); font-size: 0.875rem; text-align: center;">
                Failed to load projects
            </p>
        `;
    }
}

/**
 * Load recent activity feed
 *
 * BUSINESS CONTEXT:
 * Shows recent events within the organization
 * Note: Platform-wide audit logs require site_admin role and are not available to org admins
 *
 * @returns {Promise<void>}
 */
async function loadRecentActivity() {
    const activityEl = document.getElementById('recentActivity');
    if (!activityEl) return;

    try {
        /**
         * WHY TRACK ACTIVITY:
         * - Provides org admins with visibility into recent actions
         * - Helps identify active users and engagement patterns
         * - Enables quick access to recent changes for context
         *
         * SECURITY NOTE:
         * - Endpoint uses HTTPS (enforced at nginx/SSL layer)
         * - Authentication via JWT token (getAuthHeaders)
         * - Multi-tenant isolation via organization_id
         */

        // Fetch recent activity from HTTPS API endpoint
        const response = await fetch(`/api/v1/organizations/${currentOrganizationId}/activity`, {
            headers: await getAuthHeaders()
        });

        let activities = [];

        if (response.ok) {
            const data = await response.json();
            activities = data.activities || [];
        } else {
            console.warn(`Failed to fetch activities: ${response.status} ${response.statusText}`);
        }

        if (activities.length === 0) {
            activityEl.innerHTML = `
                <div style="padding: 2rem; text-align: center; background: var(--bg-secondary); border-radius: 8px;">
                    <div style="font-size: 2rem; margin-bottom: 0.75rem;">📊</div>
                    <p style="margin: 0; color: var(--text-muted); font-size: 0.875rem;">
                        No recent activity to display
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.75rem;">
                        Activity will appear here as your organization members take actions.
                    </p>
                </div>
            `;
            return;
        }

        // Display recent activities
        activityEl.innerHTML = `
            <div style="background: var(--bg-secondary); border-radius: 8px; padding: 1rem;">
                ${activities.slice(0, 5).map((activity, index) => `
                    <div style="display: flex; align-items: start; gap: 0.75rem; padding: 0.75rem; ${index < activities.slice(0, 5).length - 1 ? 'border-bottom: 1px solid var(--border-color);' : ''} border-left: 3px solid ${getActivityColor(activity.type)};">
                        <div style="font-size: 1.25rem; flex-shrink: 0;">
                            ${getActivityIcon(activity.type)}
                        </div>
                        <div style="flex: 1; min-width: 0;">
                            <div style="font-size: 0.875rem; color: var(--text-primary); margin-bottom: 0.25rem;">
                                ${escapeHtml(activity.description)}
                            </div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">
                                ${activity.user_name ? escapeHtml(activity.user_name) + ' • ' : ''}${formatTimeAgo(activity.created_at)}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <button class="btn btn-outline mt-md" style="margin-top: 1rem; width: 100%; visibility: hidden;">
                View All Activity
            </button>
        `;

    } catch (error) {
        console.error('Error loading recent activity:', error);
        activityEl.innerHTML = `
            <div style="padding: 2rem; text-align: center; background: var(--bg-secondary); border-radius: 8px;">
                <div style="font-size: 2rem; margin-bottom: 0.75rem;">⚠️</div>
                <p style="margin: 0; color: var(--text-muted); font-size: 0.875rem;">
                    Unable to load activity
                </p>
                <p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.75rem;">
                    ${escapeHtml(error.message)}
                </p>
            </div>
        `;
    }
}

/**
 * Get icon for activity type
 *
 * @param {string} type - Activity type
 * @returns {string} Emoji icon
 */
function getActivityIcon(type) {
    const icons = {
        'project_created': '📁',
        'project_updated': '📝',
        'track_created': '🛤️',
        'track_updated': '✏️',
        'member_added': '👤',
        'member_removed': '👋',
        'course_created': '📚',
        'course_updated': '📖',
        'enrollment': '✅',
        'login': '🔐',
        'settings_changed': '⚙️'
    };
    return icons[type] || '•';
}

/**
 * Get color for activity type
 *
 * @param {string} type - Activity type
 * @returns {string} CSS color
 */
function getActivityColor(type) {
    const colors = {
        'project_created': '#10b981',
        'project_updated': '#3b82f6',
        'track_created': '#8b5cf6',
        'track_updated': '#6366f1',
        'member_added': '#14b8a6',
        'member_removed': '#f59e0b',
        'course_created': '#06b6d4',
        'course_updated': '#0ea5e9',
        'enrollment': '#10b981',
        'login': '#64748b',
        'settings_changed': '#f97316'
    };
    return colors[type] || '#94a3b8';
}

/**
 * Format timestamp as relative time (e.g., "2 hours ago")
 *
 * @param {string} timestamp - ISO timestamp
 * @returns {string} Formatted relative time
 */
function formatTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) {
        return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    }
}

/**
 * Load courses data
 *
 * BUSINESS CONTEXT:
 * Loads AI-generated courses for the organization
 * Allows organization admins to generate and edit course content
 *
 * @returns {Promise<void>}
 */
async function loadCoursesData() {
    try {
        const coursesGrid = document.getElementById('coursesGrid');
        if (!coursesGrid) return;

        // Show loading state
        coursesGrid.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
                <p>Loading courses...</p>
            </div>
        `;

        // Get current organization
        const urlParams = new URLSearchParams(window.location.search);
        const orgId = urlParams.get('org_id');

        // Fetch courses from backend via nginx proxy (relative URL uses same protocol as page)
        const response = await fetch(`/api/v1/courses?published_only=false`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch courses: ${response.statusText}`);
        }

        const courses = await response.json();
        console.log('Loaded courses:', courses);

        // Filter courses by organization if needed
        const orgCourses = courses.filter(course =>
            course.organization_id === orgId || course.organization_id === null
        );

        if (orgCourses.length === 0) {
            // Show empty state
            coursesGrid.innerHTML = `
                <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
                    <p style="font-size: 1.2rem; margin-bottom: 1rem;">No courses generated yet</p>
                    <p>Click "Generate Course with AI" to create your first course</p>
                </div>
            `;
        } else {
            // Render course cards
            coursesGrid.innerHTML = orgCourses.map(course => `
                <div class="course-card"
                     style="border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; cursor: pointer;"
                     onclick="viewCourseDetails('${course.id}', ${escapeHtml(JSON.stringify(course))})">
                    <h3 style="margin-top: 0;">${escapeHtml(course.title)}</h3>
                    <p style="color: var(--text-muted); margin-bottom: 1rem;">${escapeHtml(course.description)}</p>
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;">
                        <span style="background: var(--bg-secondary); padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem;">
                            ${course.category || 'Uncategorized'}
                        </span>
                        <span style="background: var(--bg-secondary); padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem;">
                            ${course.difficulty_level}
                        </span>
                        <span style="background: var(--bg-secondary); padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem;">
                            ${course.estimated_duration} ${course.duration_unit}
                        </span>
                    </div>
                    <div style="display: flex; gap: 0.5rem;" onclick="event.stopPropagation();">
                        <button class="btn btn-secondary" onclick="editCourse('${course.id}', '${escapeHtml(course.title)}')">✏️ Edit</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading courses:', error);
        showNotification('Failed to load courses', 'error');

        const coursesGrid = document.getElementById('coursesGrid');
        if (coursesGrid) {
            coursesGrid.innerHTML = `
                <div style="text-align: center; padding: 3rem; color: var(--text-error);">
                    <p>Failed to load courses</p>
                    <p style="font-size: 0.875rem;">${error.message}</p>
                </div>
            `;
        }
    }
}

// Helper function to escape HTML
    /**
     * EXECUTE ESCAPEHTML OPERATION
     * PURPOSE: Execute escapeHtml operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} text - Text parameter
     */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Setup logout handler
 *
 * SECURITY:
 * Clears authentication token and redirects to login
 */
function setupLogoutHandler() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();

            // Confirm logout
            if (confirm('Are you sure you want to logout?')) {
                // Stop activity-based token refresh
                activityTokenManager.stop();
                console.log('🛑 Activity tracking stopped on logout');

                // Clear authentication
                localStorage.removeItem('authToken');
                localStorage.removeItem('currentUser');
                localStorage.removeItem('userEmail');
                localStorage.removeItem('sessionStart');
                localStorage.removeItem('lastActivity');
                localStorage.removeItem('token'); // Also clear 'token' key

                // Redirect to login
                window.location.href = '../index.html';
            }
        });
    }
}

/**
 * Get current organization
 *
 * @returns {Object|null} Current organization object
 */
export function getCurrentOrganization() {
    return currentOrganization;
}

/**
 * Get current user
 *
 * @returns {Object|null} Current user object
 */
export function getCurrentUser() {
    return currentUser;
}

/**
 * Refresh current tab
 *
 * BUSINESS CONTEXT:
 * Reloads data for currently active tab
 * Used after data modifications
 */
export function refreshCurrentTab() {
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab) {
        const tabName = activeTab.getAttribute('data-tab');
        if (tabName) {
            loadTabContent(tabName);
        }
    }
}

// Export for global window access
window.OrgAdminCore = {
    initializeDashboard,
    loadTabContent,
    refreshCurrentTab,
    getCurrentOrganization,
    getCurrentUser
};
