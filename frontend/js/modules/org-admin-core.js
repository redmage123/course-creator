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

import { fetchOrganization, fetchCurrentUser } from './org-admin-api.js';
import { showNotification } from './org-admin-utils.js';

import { initializeProjectsManagement, loadProjectsData } from './org-admin-projects.js';
import { initializeInstructorsManagement, loadInstructorsData } from './org-admin-instructors.js';
import { initializeStudentsManagement, loadStudentsData } from './org-admin-students.js';
import { initializeTracksManagement, loadTracksData } from './org-admin-tracks.js';
import { initializeSettingsManagement, loadSettingsData } from './org-admin-settings.js';

// Global state
let currentOrganization = null;
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
    try {
        // Verify authentication
        const token = localStorage.getItem('auth_token');
        if (!token) {
            window.location.href = '/login.html';
            return;
        }

        // Load current user
        currentUser = await fetchCurrentUser();
        console.log('Dashboard initialized for user:', currentUser.email);

        // Get organization ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const orgId = urlParams.get('org_id');

        if (!orgId) {
            showNotification('No organization specified', 'error');
            setTimeout(() => window.location.href = '/organizations.html', 2000);
            return;
        }

        // Load organization
        currentOrganization = await fetchOrganization(orgId);
        console.log('Loaded organization:', currentOrganization.name);

        // Update UI with organization info
        updateOrganizationHeader(currentOrganization);

        // Initialize all sub-modules with organization context
        initializeProjectsManagement(orgId);
        initializeInstructorsManagement(orgId);
        initializeStudentsManagement(orgId);
        initializeTracksManagement(orgId);
        initializeSettingsManagement(orgId);

        // Set up navigation event listeners
        setupNavigationListeners();

        // Load initial tab (overview)
        loadTabContent('overview');

        // Set up logout handler
        setupLogoutHandler();

    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showNotification('Failed to initialize dashboard', 'error');
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
    // Update organization name
    const orgNameEl = document.getElementById('organizationName');
    if (orgNameEl) {
        orgNameEl.textContent = organization.name;
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

        // Load recent activity
        await loadRecentActivity();

    } catch (error) {
        console.error('Error loading overview:', error);
    }
}

/**
 * Load recent activity feed
 *
 * BUSINESS CONTEXT:
 * Shows recent events like enrollments, completions, new members
 *
 * @returns {Promise<void>}
 */
async function loadRecentActivity() {
    // This would fetch from an activity/events API endpoint
    // For now, show placeholder
    const activityEl = document.getElementById('recentActivity');
    if (activityEl) {
        activityEl.innerHTML = '<p style="color: var(--text-muted);">Recent activity loading...</p>';
    }
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
                // Clear authentication
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_data');

                // Redirect to login
                window.location.href = '/login.html';
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
