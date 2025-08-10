/**
 * ADMIN DASHBOARD MODULE - COMPREHENSIVE USER MANAGEMENT SYSTEM
 * 
 * PURPOSE: Complete administrative interface for Course Creator platform user management
 * WHY: Platform administrators need comprehensive tools for user oversight and management
 * ARCHITECTURE: Client-side dashboard with RESTful API integration and real-time updates
 * 
 * CORE RESPONSIBILITIES:
 * - Platform-wide user management (create, read, update, delete)
 * - User role administration and permission management
 * - Dashboard statistics and analytics display
 * - Bulk user operations for administrative efficiency
 * - Advanced filtering, sorting, and search capabilities
 * - Session security and authentication validation
 * 
 * BUSINESS REQUIREMENTS:
 * - Complete administrative control over platform users
 * - Real-time statistics for platform oversight
 * - Efficient bulk operations for large user bases
 * - Advanced filtering for quick user location
 * - Professional interface matching platform standards
 * - Security compliance with session validation
 * 
 * USER ROLES MANAGED:
 * - admin: Site-wide administration and platform management
 * - org_admin: Organization-specific administration and member management
 * - instructor: Course creation, student management, and analytics
 * - student: Learning content access and lab environment usage
 * 
 * SECURITY FEATURES:
 * - Comprehensive session validation with timeout enforcement
 * - JWT token-based API authentication
 * - Role-based access control (admin-only access)
 * - Automatic session cleanup on expiration
 * - Authentication error handling with graceful redirects
 * 
 * TECHNICAL ARCHITECTURE:
 * - Modern JavaScript with ES6+ features
 * - RESTful API integration with error handling
 * - Real-time DOM manipulation for dynamic updates
 * - Event-driven architecture for user interactions
 * - Responsive design for cross-device compatibility
 */

// CONFIGURATION AND AUTHENTICATION SETUP
// PURPOSE: Initialize API endpoints and authentication state for admin operations
// WHY: Centralized configuration ensures consistent API access across all admin functions

const API_BASE = CONFIG.API_URLS.USER_MANAGEMENT;  // User management service endpoint
const authToken = localStorage.getItem('authToken');  // JWT token for authenticated requests

// NOTIFICATION CONFIGURATION
// PURPOSE: Centralized configuration for admin notification system
// WHY: Configurable timeouts enable easy adjustment of user experience
const NOTIFICATION_TIMEOUT = 5 * 1000;  // 5 seconds - Professional notification display duration

// GLOBAL USER DATA STORAGE
// PURPOSE: Cache all users for efficient client-side filtering and sorting
// WHY: Reduces API calls and enables instant filtering/sorting without server round-trips
let allUsers = [];

/**
 * AUTHENTICATION ERROR HANDLER
 * PURPOSE: Handle API authentication failures with consistent user experience
 * WHY: Expired or invalid tokens require immediate cleanup and user redirection
 * 
 * ERROR HANDLING PROCESS:
 * 1. Detect authentication failures (401/403 responses)
 * 2. Clear expired authentication data
 * 3. Provide user-friendly notification
 * 4. Redirect to login page for re-authentication
 * 
 * SECURITY COMPLIANCE:
 * - Immediate cleanup prevents unauthorized access attempts
 * - Clear notification explains what occurred
 * - Safe redirect to public login page
 * 
 * @param {Response} response - HTTP response object to check for auth errors
 * @returns {boolean} True if auth error was handled, false otherwise
 */
function handleAuthError(response) {
    // AUTHENTICATION FAILURE DETECTION: Check for unauthorized or forbidden responses
    if (response.status === 401 || response.status === 403) {
        // IMMEDIATE CLEANUP: Remove expired authentication data
        localStorage.removeItem('authToken');
        
        // USER NOTIFICATION: Explain session expiry professionally
        alert('Your session has expired. Please login again.');
        
        // SECURE REDIRECT: Return to login page for re-authentication
        window.location.href = 'html/index.html';
        return true;  // Indicate auth error was handled
    }
    return false;  // No auth error detected
}

/*
 * COMPREHENSIVE SESSION VALIDATION ON PAGE LOAD - ADMIN DASHBOARD

BUSINESS REQUIREMENT:
When an admin refreshes the dashboard page after session expiry,
they should be redirected to the home page with proper validation.

TECHNICAL IMPLEMENTATION:
1. Check if user data exists in localStorage
2. Validate session timestamps against timeout thresholds  
3. Check if authentication token is present and valid
4. Verify user has correct role (admin)
5. Redirect to home page if any validation fails
6. Prevent dashboard initialization for expired sessions
 */

/**
 * CURRENT USER RETRIEVAL WITH ERROR HANDLING
 * PURPOSE: Safely retrieve and parse current user data from localStorage
 * WHY: User data is critical for session validation and role-based access control
 * 
 * ERROR HANDLING: Graceful degradation if localStorage data is corrupted or missing
 * SECURITY: Validates JSON parsing to prevent security issues from malformed data
 * 
 * @returns {Object|null} Current user object or null if unavailable
 */
function getCurrentUser() {
    try {
        // RETRIEVE USER DATA: Get stored user information from localStorage
        const userStr = localStorage.getItem('currentUser');
        
        // PARSE AND RETURN: Convert JSON string to user object
        return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
        // ERROR RECOVERY: Handle corrupted or invalid user data gracefully
        console.error('Error getting current user:', error);
        return null;  // Return null for any parsing errors
    }
}

/**
 * COMPREHENSIVE ADMIN SESSION VALIDATION SYSTEM
 * PURPOSE: Validate complete session state before allowing admin dashboard access
 * WHY: Admin dashboard requires stringent security validation to prevent unauthorized access
 * 
 * VALIDATION CHECKLIST:
 * 1. User data existence and validity
 * 2. Authentication token presence
 * 3. Session timestamp validation
 * 4. Absolute session timeout enforcement (8 hours)
 * 5. Inactivity timeout enforcement (2 hours)
 * 6. Admin role verification
 * 
 * SECURITY ENFORCEMENT:
 * - Multiple validation layers for comprehensive security
 * - Automatic cleanup of expired session data
 * - Safe redirect to public page on validation failure
 * - Prevention of admin dashboard access for non-admin users
 * 
 * BUSINESS COMPLIANCE:
 * - Educational platform security standards
 * - Administrative access control requirements
 * - Session timeout policies for sensitive operations
 * 
 * @returns {boolean} True if session is valid for admin access, false otherwise
 */
function validateAdminSession() {
    // GATHER SESSION DATA: Collect all required session information
    const currentUser = getCurrentUser();
    const authToken = localStorage.getItem('authToken');
    const sessionStart = localStorage.getItem('sessionStart');
    const lastActivity = localStorage.getItem('lastActivity');
    
    // SESSION DATA VALIDATION: Ensure all required session components exist
    // WHY: Incomplete session data indicates invalid or expired session
    if (!currentUser || !authToken || !sessionStart || !lastActivity) {
        console.log('Session invalid: Missing session data');
        
        // SECURE REDIRECT: Navigate to public page for re-authentication
        window.location.href = window.location.pathname.includes('/html/') ? '../index.html' : 'index.html';
        return false;
    }
    
    // SESSION TIMEOUT VALIDATION: Check both absolute and inactivity timeouts
    // WHY: Educational platform security requires time-based session limits
    const now = Date.now();
    const sessionAge = now - parseInt(sessionStart);
    const timeSinceActivity = now - parseInt(lastActivity);
    
    // SECURITY TIMEOUT CONFIGURATION: Educational platform standards
    const SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8 hours absolute maximum
    const INACTIVITY_TIMEOUT = 2 * 60 * 60 * 1000; // 2 hours inactivity limit
    
    // TIMEOUT ENFORCEMENT: Automatic logout for expired sessions
    if (sessionAge > SESSION_TIMEOUT || timeSinceActivity > INACTIVITY_TIMEOUT) {
        console.log('Session expired: Redirecting to home page');
        
        // COMPREHENSIVE CLEANUP: Remove all expired session data
        localStorage.removeItem('authToken');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('sessionStart');
        localStorage.removeItem('lastActivity');
        
        // SECURE REDIRECT: Navigate to public page
        window.location.href = window.location.pathname.includes('/html/') ? '../index.html' : 'index.html';
        return false;
    }
    
    // ADMIN ROLE VERIFICATION: Ensure user has administrative privileges
    // WHY: Admin dashboard should only be accessible to admin users
    if (currentUser.role !== 'admin') {
        console.log('Invalid role for admin dashboard:', currentUser.role);
        
        // ACCESS DENIED REDIRECT: Navigate to appropriate user page
        window.location.href = window.location.pathname.includes('/html/') ? '../index.html' : 'index.html';
        return false;
    }
    
    // VALIDATION SUCCESS: All security checks passed
    return true;
}

// Check if user is logged in and has admin role
if (!validateAdminSession()) {
    // Function handles redirect, just return
}

/**
 * ADMIN DASHBOARD SECTION NAVIGATION SYSTEM
 * PURPOSE: Switch between different admin dashboard sections with proper state management
 * WHY: Admin dashboard has multiple sections (stats, users) requiring coordinated UI updates
 * 
 * NAVIGATION WORKFLOW:
 * 1. Hide all currently active sections
 * 2. Clear navigation button active states
 * 3. Show target section with appropriate styling
 * 4. Update navigation button active state
 * 5. Load section-specific data as needed
 * 
 * SECTION MANAGEMENT:
 * - dashboard: Statistics and overview data
 * - users: User management interface with CRUD operations
 * 
 * UI CONSISTENCY:
 * - Professional section transitions
 * - Clear visual indicators for active section
 * - Automatic data loading for data-dependent sections
 * 
 * @param {string} sectionId - Target section identifier ('dashboard' or 'users')
 */
// eslint-disable-next-line no-unused-vars
function showSection(sectionId) {
    // HIDE ALL SECTIONS: Clear current section display
    const sections = document.querySelectorAll('.admin-section');
    sections.forEach(section => section.classList.remove('active'));
    
    // CLEAR NAVIGATION STATES: Remove active styling from all navigation buttons
    const navButtons = document.querySelectorAll('.admin-nav button');
    navButtons.forEach(button => button.classList.remove('active'));
    
    // SHOW TARGET SECTION: Make selected section visible
    document.getElementById(sectionId).classList.add('active');
    
    // UPDATE NAVIGATION STATE: Highlight clicked navigation button
    event.target.classList.add('active');
    
    // SECTION-SPECIFIC DATA LOADING: Load appropriate data for each section
    // WHY: Different sections require different data sets and API calls
    if (sectionId === 'dashboard') {
        loadDashboardStats();  // Load platform statistics and metrics
    } else if (sectionId === 'users') {
        loadUsers();  // Load user list for management operations
    }
}

/**
 * ADMIN NOTIFICATION SYSTEM
 * PURPOSE: Display user feedback messages with appropriate styling and auto-dismissal
 * WHY: Admin operations need clear feedback for success/failure states
 * 
 * NOTIFICATION FEATURES:
 * - Type-based styling (success, error, warning, info)
 * - Automatic dismissal after 5 seconds
 * - Manual dismissal capability
 * - Professional styling matching admin interface
 * - Non-blocking overlay design
 * 
 * NOTIFICATION TYPES:
 * - success: Successful operations (green styling)
 * - error: Failed operations or validation errors (red styling)
 * - warning: Important alerts requiring attention (orange styling)
 * - info: General information and status updates (blue styling)
 * 
 * @param {string} message - Notification message content
 * @param {string} type - Notification type ('success', 'error', 'warning', 'info')
 */
function showAlert(message, type = 'success') {
    // LOCATE ALERTS CONTAINER: Find notification display area
    const alertsDiv = document.getElementById('alerts');
    
    // CREATE NOTIFICATION ELEMENT: Build styled notification
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;  // Apply type-based styling
    alertDiv.textContent = message;
    
    // DISPLAY NOTIFICATION: Add to alerts container
    alertsDiv.appendChild(alertDiv);
    
    // AUTO-DISMISSAL: Remove notification after reasonable viewing time
    // WHY: Configured timeout provides adequate time for user to read without cluttering interface
    setTimeout(() => {
        alertDiv.remove();  // Clean removal from DOM
    }, NOTIFICATION_TIMEOUT);  // Use configured notification display duration
}

/**
 * PLATFORM STATISTICS LOADER
 * PURPOSE: Load and display comprehensive platform statistics for administrative oversight
 * WHY: Administrators need real-time platform metrics for management decisions
 * 
 * STATISTICS DISPLAYED:
 * - Total users: Complete platform user count
 * - Active users: Currently active/enabled user count
 * - Role distribution: Breakdown by admin, instructor, student roles
 * 
 * DATA FLOW:
 * 1. Fetch statistics from admin API endpoint
 * 2. Handle authentication errors with graceful degradation
 * 3. Update dashboard display with real-time data
 * 4. Provide error handling with user feedback
 * 5. Display fallback values on API failure
 * 
 * ERROR HANDLING:
 * - Authentication error detection and redirect
 * - Network error handling with user notification
 * - Graceful fallback display ("Error") for failed loads
 * - Comprehensive logging for debugging
 * 
 * BUSINESS VALUE:
 * - Platform growth monitoring
 * - User engagement analytics
 * - Role distribution oversight
 * - System health indicators
 */
async function loadDashboardStats() {
    try {
        // STATISTICS API REQUEST: Fetch platform metrics from admin service
        // WHY: Real-time data ensures admin decisions are based on current platform state
        const response = await fetch(`${API_BASE}/admin/stats`, {
            headers: {
                'Authorization': `Bearer ${authToken}`  // JWT authentication for admin API
            }
        });
        
        // RESPONSE VALIDATION: Check for successful API response
        if (!response.ok) {
            // AUTHENTICATION ERROR HANDLING: Check for expired tokens
            if (handleAuthError(response)) {
                return; // handleAuthError manages redirect, exit function
            }
            
            // API ERROR PROCESSING: Handle non-auth API failures
            const errorText = await response.text();
            console.error('API Error:', errorText);
            throw new Error(`Failed to load stats: ${response.status} - ${errorText}`);
        }
        
        // DATA EXTRACTION: Parse statistics from API response
        const stats = await response.json();
        
        // DASHBOARD UPDATES: Display statistics in admin interface
        // WHY: Real-time display keeps admin informed of platform status
        document.getElementById('total-users').textContent = stats.total_users || 0;
        document.getElementById('active-users').textContent = stats.active_users || 0;
        document.getElementById('admin-count').textContent = stats.users_by_role?.admin || 0;
        document.getElementById('instructor-count').textContent = stats.users_by_role?.instructor || 0;
        document.getElementById('student-count').textContent = stats.users_by_role?.student || 0;
        
    } catch (error) {
        // ERROR HANDLING: Comprehensive error processing and user feedback
        console.error('Error loading statistics:', error);
        showAlert('Error loading statistics: ' + error.message, 'error');
        
        // FALLBACK DISPLAY: Show error indicators instead of stale/missing data
        // WHY: Clear indication that data is unavailable prevents incorrect decisions
        document.getElementById('total-users').textContent = 'Error';
        document.getElementById('active-users').textContent = 'Error';
        document.getElementById('admin-count').textContent = 'Error';
        document.getElementById('instructor-count').textContent = 'Error';
        document.getElementById('student-count').textContent = 'Error';
    }
}

// Load users list
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/admin/users`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            // Check if it's an authentication error
            if (handleAuthError(response)) {
                return; // handleAuthError will redirect
            }
            throw new Error('Failed to load users');
        }
        
        const users = await response.json();
        allUsers = users; // Store all users globally for filtering
        filterUsers(); // Apply current filters
        
    } catch (error) {
        showAlert('Error loading users: ' + error.message, 'error');
    }
}

// Display users in table
function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="checkbox" class="user-checkbox" value="${user.id}" onchange="updateBulkActions()"></td>
            <td>${user.full_name}</td>
            <td>${user.email}</td>
            <td><span class="role-badge role-${user.role}">${user.role}</span></td>
            <td>${user.is_active ? 'Active' : 'Inactive'}</td>
            <td>
                <button onclick="editUser('${user.id}')" class="btn btn-warning">Edit</button>
                <button onclick="deleteUser('${user.id}')" class="btn btn-danger">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // Reset bulk actions
    updateBulkActions();
}

// Refresh users list
// eslint-disable-next-line no-unused-vars
function refreshUsers() {
    loadUsers();
    showAlert('Users list refreshed');
}

// Edit user
// eslint-disable-next-line no-unused-vars
async function editUser(userId) {
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            // Check if it's an authentication error
            if (handleAuthError(response)) {
                return; // handleAuthError will redirect
            }
            throw new Error('Failed to load user');
        }
        
        const user = await response.json();
        
        // Populate edit form
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-email').value = user.email;
        document.getElementById('edit-full-name').value = user.full_name;
        document.getElementById('edit-role').value = user.role;
        document.getElementById('edit-is-active').value = user.is_active.toString();
        
        // Show modal
        document.getElementById('edit-user-modal').style.display = 'block';
        
    } catch (error) {
        showAlert('Error loading user: ' + error.message, 'error');
    }
}

// Close modal
function closeModal() {
    document.getElementById('edit-user-modal').style.display = 'none';
}

// Delete user
// eslint-disable-next-line no-unused-vars
async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            // Check if it's an authentication error
            if (handleAuthError(response)) {
                return; // handleAuthError will redirect
            }
            throw new Error('Failed to delete user');
        }
        
        showAlert('User deleted successfully');
        loadUsers(); // Refresh the list
        loadDashboardStats(); // Refresh dashboard statistics
        
    } catch (error) {
        showAlert('Error deleting user: ' + error.message, 'error');
    }
}

// Handle create user form submission
document.getElementById('create-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const userData = {
        email: formData.get('email'),
        full_name: formData.get('full_name'),
        password: formData.get('password'),
        role: formData.get('role')
    };
    
    try {
        const response = await fetch(`${API_BASE}/admin/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) {
            // Check if it's an authentication error
            if (handleAuthError(response)) {
                return; // handleAuthError will redirect
            }
            
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create user');
        }
        
        showAlert('User created successfully');
        e.target.reset(); // Clear form
        loadDashboardStats(); // Refresh dashboard statistics
        
    } catch (error) {
        showAlert('Error creating user: ' + error.message, 'error');
    }
});

// Handle edit user form submission
document.getElementById('edit-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userId = document.getElementById('edit-user-id').value;
    const formData = new FormData(e.target);
    const userData = {
        email: formData.get('email'),
        full_name: formData.get('full_name'),
        role: formData.get('role'),
        is_active: formData.get('is_active') === 'true'
    };
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) {
            // Check if it's an authentication error
            if (handleAuthError(response)) {
                return; // handleAuthError will redirect
            }
            
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update user');
        }
        
        showAlert('User updated successfully');
        closeModal();
        loadUsers(); // Refresh the list
        loadDashboardStats(); // Refresh dashboard statistics
        
    } catch (error) {
        showAlert('Error updating user: ' + error.message, 'error');
    }
});

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('edit-user-modal');
    if (e.target === modal) {
        closeModal();
    }
});

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
});

// Add logout functionality
// eslint-disable-next-line no-unused-vars
function logout() {
    localStorage.removeItem('authToken');
    window.location.href = 'index.html';
}

// Bulk user management functions
// eslint-disable-next-line no-unused-vars
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const userCheckboxes = document.querySelectorAll('.user-checkbox');
    
    userCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateBulkActions();
}

function updateBulkActions() {
    const selectedCheckboxes = document.querySelectorAll('.user-checkbox:checked');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    const selectedCountSpan = document.getElementById('selected-count');
    const selectAllCheckbox = document.getElementById('select-all');
    
    const count = selectedCheckboxes.length;
    
    if (count > 0) {
        bulkDeleteBtn.style.display = 'inline-block';
        selectedCountSpan.textContent = `${count} user(s) selected`;
    } else {
        bulkDeleteBtn.style.display = 'none';
        selectedCountSpan.textContent = '';
    }
    
    // Update select all checkbox state
    const allCheckboxes = document.querySelectorAll('.user-checkbox');
    if (count === 0) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = false;
    } else if (count === allCheckboxes.length) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = true;
    } else {
        selectAllCheckbox.indeterminate = true;
        selectAllCheckbox.checked = false;
    }
}

// eslint-disable-next-line no-unused-vars
async function bulkDeleteUsers() {
    const selectedCheckboxes = document.querySelectorAll('.user-checkbox:checked');
    const selectedUserIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (selectedUserIds.length === 0) {
        showAlert('No users selected for deletion', 'error');
        return;
    }
    
    const confirmation = confirm(
        `Are you sure you want to delete ${selectedUserIds.length} user(s)? This action cannot be undone.`
    );
    
    if (!confirmation) {
        return;
    }
    
    try {
        let successCount = 0;
        let errorCount = 0;
        const errors = [];
        
        // Delete users one by one
        for (const userId of selectedUserIds) {
            try {
                const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                });
                
                if (!response.ok) {
                    // Check if it's an authentication error
                    if (handleAuthError(response)) {
                        return; // handleAuthError will redirect
                    }
                    
                    const errorText = await response.text();
                    errors.push(`User ${userId}: ${errorText}`);
                    errorCount++;
                } else {
                    successCount++;
                }
            } catch (error) {
                errors.push(`User ${userId}: ${error.message}`);
                errorCount++;
            }
        }
        
        // Show results
        if (successCount > 0) {
            showAlert(`Successfully deleted ${successCount} user(s)`);
        }
        
        if (errorCount > 0) {
            showAlert(`Failed to delete ${errorCount} user(s): ${errors.join(', ')}`, 'error');
        }
        
        // Refresh the users list and dashboard statistics
        loadUsers();
        loadDashboardStats();
        
    } catch (error) {
        showAlert('Error during bulk delete: ' + error.message, 'error');
    }
}

// Filtering and sorting functions
function filterUsers() {
    if (!allUsers || allUsers.length === 0) {
        return;
    }
    
    const searchTerm = document.getElementById('search-users').value.toLowerCase();
    const roleFilter = document.getElementById('filter-role').value;
    const statusFilter = document.getElementById('filter-status').value;
    const sortBy = document.getElementById('sort-users').value;
    
    // Filter users
    let filteredUsers = allUsers.filter(user => {
        // Search filter (name or email)
        const matchesSearch = !searchTerm || 
            user.full_name.toLowerCase().includes(searchTerm) ||
            user.email.toLowerCase().includes(searchTerm);
        
        // Role filter
        const matchesRole = !roleFilter || user.role === roleFilter;
        
        // Status filter
        const matchesStatus = !statusFilter || 
            (statusFilter === 'active' && user.is_active) ||
            (statusFilter === 'inactive' && !user.is_active);
        
        return matchesSearch && matchesRole && matchesStatus;
    });
    
    // Sort users
    filteredUsers.sort((a, b) => {
        let comparison = 0;
        
        switch (sortBy) {
            case 'name-asc':
                comparison = a.full_name.localeCompare(b.full_name);
                break;
            case 'name-desc':
                comparison = b.full_name.localeCompare(a.full_name);
                break;
            case 'email-asc':
                comparison = a.email.localeCompare(b.email);
                break;
            case 'email-desc':
                comparison = b.email.localeCompare(a.email);
                break;
            case 'role-asc':
                comparison = a.role.localeCompare(b.role);
                break;
            case 'role-desc':
                comparison = b.role.localeCompare(a.role);
                break;
            default:
                comparison = a.full_name.localeCompare(b.full_name);
        }
        
        return comparison;
    });
    
    // Update results info
    updateFilterResults(filteredUsers.length, allUsers.length);
    
    // Display filtered users
    displayUsers(filteredUsers);
}

function updateFilterResults(filteredCount, totalCount) {
    const resultsDiv = document.getElementById('filter-results');
    if (filteredCount === totalCount) {
        resultsDiv.textContent = `Showing all ${totalCount} users`;
    } else {
        resultsDiv.textContent = `Showing ${filteredCount} of ${totalCount} users`;
    }
}

// eslint-disable-next-line no-unused-vars
function clearFilters() {
    document.getElementById('search-users').value = '';
    document.getElementById('filter-role').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('sort-users').value = 'name-asc';
    filterUsers();
}