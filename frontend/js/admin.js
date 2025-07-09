const API_BASE = 'http://localhost:8000';
const authToken = localStorage.getItem('authToken');

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
            throw new Error('Failed to load stats');
        }
        
        const stats = await response.json();
        
        document.getElementById('total-users').textContent = stats.total_users;
        document.getElementById('active-users').textContent = stats.active_users;
        document.getElementById('admin-count').textContent = stats.users_by_role.admin;
        document.getElementById('instructor-count').textContent = stats.users_by_role.instructor;
        document.getElementById('student-count').textContent = stats.users_by_role.student;
        
    } catch (error) {
        showAlert('Error loading statistics: ' + error.message, 'error');
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
            throw new Error('Failed to load users');
        }
        
        const users = await response.json();
        displayUsers(users);
        
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
            throw new Error('Failed to delete user');
        }
        
        showAlert('User deleted successfully');
        loadUsers(); // Refresh the list
        
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
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create user');
        }
        
        showAlert('User created successfully');
        e.target.reset(); // Clear form
        
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
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update user');
        }
        
        showAlert('User updated successfully');
        closeModal();
        loadUsers(); // Refresh the list
        
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