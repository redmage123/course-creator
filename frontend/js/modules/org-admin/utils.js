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

// Import authentication manager for user context
import { Auth } from '../auth.js';

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

// Project Status Calculation
/**
 * Calculate project status based on current date and project dates
 *
 * BUSINESS LOGIC:
 * Projects automatically transition through lifecycle stages based on their
 * start and end dates. This ensures accurate status reporting and prevents
 * projects from appearing "active" when they've already ended.
 *
 * Status transitions:
 * - draft: No start/end dates configured yet
 * - planned: Dates set, but start date is in the future
 * - active: Currently between start and end dates
 * - completed: Past the end date (inactive)
 *
 * @param {Object} project - Project object with start_date and end_date
 * @returns {string} Calculated status: 'draft', 'planned', 'active', or 'completed'
 */
export function calculateProjectStatus(project) {
    // If no dates set, keep as draft
    if (!project.start_date || !project.end_date) {
        return 'draft';
    }

    const now = new Date();
    const startDate = new Date(project.start_date);
    const endDate = new Date(project.end_date);

    // Normalize dates to midnight for accurate day-based comparison
    now.setHours(0, 0, 0, 0);
    startDate.setHours(0, 0, 0, 0);
    endDate.setHours(0, 0, 0, 0);

    // Project hasn't started yet
    if (now < startDate) {
        return 'planned';
    }

    // Project has ended (INACTIVE - as requested by user)
    if (now > endDate) {
        return 'completed';
    }

    // Project is currently running
    return 'active';
}
