/**
 * Organization Admin Dashboard - Utility Functions Module
 *
 * BUSINESS CONTEXT:
 * Provides utility and helper functions for the organization admin dashboard,
 * including data parsing, UI helpers, and development mock data.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Only utility/helper functions
 * - Open/Closed: New utilities can be added without modification
 * - Interface Segregation: Focused, single-purpose functions
 *
 * ARCHITECTURE:
 * Extracted from monolithic org-admin-dashboard.js to improve testability
 * and reusability across different modules.
 */

// Data Parsing Utilities
export function parseCommaSeparated(value) {
    if (!value) return [];
    return value.split(',').map(v => v.trim()).filter(v => v.length > 0);
}

// User/Organization Utilities
export function getCurrentUserOrgId() {
    const user = Auth.getCurrentUser();
    if (user && user.organization_id) {
        console.log('📋 Using organization_id from user:', user.organization_id);
        return user.organization_id;
    }

    console.warn('⚠️ No organization_id found in user data, using fallback');
    return 'org-123';
}

// UI State Utilities
export function showLoadingSpinner() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) spinner.style.display = 'flex';
}

export function hideLoadingSpinner() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) spinner.style.display = 'none';
}

export function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        const form = modal.querySelector('form');
        if (form) form.reset();
    }
}

// Notification System
export function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}]`, message);
    // TODO: Implement visual notification system
    if (type === 'error') {
        alert(`Error: ${message}`);
    }
}

// HTML Escaping for Security
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Date Formatting
export function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

export function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Mock Data for Development
export function getMockProjects() {
    return [
        {
            id: 'project-1',
            name: 'Graduate Developer Training Program',
            slug: 'grad-dev-program',
            description: 'Comprehensive training program for new graduate developers',
            target_roles: ['Application Developer', 'DevOps Engineer'],
            duration_weeks: 16,
            max_participants: 50,
            current_participants: 32,
            start_date: '2024-01-15',
            end_date: '2024-05-15',
            status: 'active'
        },
        {
            id: 'project-2',
            name: 'Business Analysis Bootcamp',
            slug: 'ba-bootcamp',
            description: 'Intensive business analysis training',
            target_roles: ['Business Analyst', 'Product Manager'],
            duration_weeks: 12,
            max_participants: 30,
            current_participants: 15,
            start_date: '2024-02-01',
            status: 'draft'
        }
    ];
}

export function getMockInstructors() {
    return [
        {
            user_id: 'user-1',
            email: 'john.doe@techuni.edu',
            first_name: 'John',
            last_name: 'Doe',
            role: 'instructor',
            is_active: true,
            joined_at: '2024-01-01T00:00:00Z',
            last_login: '2024-01-20T10:30:00Z'
        },
        {
            user_id: 'user-2',
            email: 'jane.smith@techuni.edu',
            first_name: 'Jane',
            last_name: 'Smith',
            role: 'project_manager',
            is_active: true,
            joined_at: '2024-01-15T00:00:00Z',
            last_login: '2024-01-19T14:20:00Z'
        }
    ];
}

export function getMockStudents() {
    return [
        {
            user_id: 'user-3',
            email: 'student1@techuni.edu',
            first_name: 'Alice',
            last_name: 'Johnson',
            project_count: 2,
            is_active: true,
            joined_at: '2024-01-10T00:00:00Z',
            last_active: '2024-09-28T00:00:00Z'
        },
        {
            user_id: 'user-4',
            email: 'student2@techuni.edu',
            first_name: 'Bob',
            last_name: 'Wilson',
            project_count: 1,
            is_active: true,
            joined_at: '2024-01-12T00:00:00Z',
            last_active: '2024-09-30T00:00:00Z'
        },
        {
            user_id: 'user-5',
            email: 'student3@techuni.edu',
            first_name: 'Charlie',
            last_name: 'Brown',
            project_count: 3,
            is_active: true,
            joined_at: '2024-02-01T00:00:00Z',
            last_active: '2024-10-01T00:00:00Z'
        }
    ];
}

export function getMockTrackTemplates() {
    return [
        {
            id: 'template-1',
            name: 'Fundamentals of Programming',
            description: 'Learn core programming concepts',
            difficulty_level: 'beginner',
            duration_weeks: 4
        },
        {
            id: 'template-2',
            name: 'Advanced Web Development',
            description: 'Master modern web technologies',
            difficulty_level: 'advanced',
            duration_weeks: 8
        }
    ];
}
