// Debug: Check what CONFIG is returning

const API_BASE = CONFIG.API_URLS.USER_MANAGEMENT;

const authToken = localStorage.getItem('authToken');

// Global variable to store all users for filtering
let allUsers = [];

// Handle authentication errors
function handleAuthError(response) {
    if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('authToken');
        alert('Your session has expired. Please login again.');
        window.location.href = 'html/index.html';
        return true;
    }
    return false;
}

// Check if user is logged in and has admin role
if (!authToken) {
    alert('Please login first');
    window.location.href = 'index.html';
}

// Show/hide sections
// eslint-disable-next-line no-unused-vars
function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.admin-section');
    sections.forEach(section => section.classList.remove('active'));
    
    // Remove active class from all nav buttons
    const navButtons = document.querySelectorAll('.admin-nav button');
    navButtons.forEach(button => button.classList.remove('active'));
    
    // Show selected section
    document.getElementById(sectionId).classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Load data for the section
    if (sectionId === 'dashboard') {
        loadDashboardStats();
    } else if (sectionId === 'users') {
        loadUsers();
    }
}

// Show alerts
function showAlert(message, type = 'success') {
    const alertsDiv = document.getElementById('alerts');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertsDiv.appendChild(alertDiv);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        
        const response = await fetch(`${API_BASE}/admin/stats`, {
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
            console.error('API Error:', errorText);
            throw new Error(`Failed to load stats: ${response.status} - ${errorText}`);
        }
        
        const stats = await response.json();
        
        document.getElementById('total-users').textContent = stats.total_users || 0;
        document.getElementById('active-users').textContent = stats.active_users || 0;
        document.getElementById('admin-count').textContent = stats.users_by_role?.admin || 0;
        document.getElementById('instructor-count').textContent = stats.users_by_role?.instructor || 0;
        document.getElementById('student-count').textContent = stats.users_by_role?.student || 0;
        
    } catch (error) {
        console.error('Error loading statistics:', error);
        showAlert('Error loading statistics: ' + error.message, 'error');
        
        // Set defaults in case of error
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