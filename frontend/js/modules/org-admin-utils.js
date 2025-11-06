/**
 * Organization Admin Dashboard - Utility Functions
 *
 * BUSINESS CONTEXT:
 * Provides shared utility functions used across all dashboard modules
 * including HTML escaping, formatting, validation, and DOM manipulation
 *
 * TECHNICAL IMPLEMENTATION:
 * Pure functions with no side effects, following functional programming principles
 * All functions are thoroughly documented and handle edge cases
 *
 * @module org-admin-utils
 */
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Capitalize the first letter of a string
 *
 * BUSINESS CONTEXT:
 * Used for formatting status badges, difficulty levels, and other
 * display values to ensure consistent capitalization
 *
 * @param {string} str - String to capitalize
 * @returns {string} String with first letter capitalized
 *
 * @example
 * capitalizeFirst('beginner') // Returns: 'Beginner'
 * capitalizeFirst('ADVANCED') // Returns: 'ADVANCED' (only first letter affected)
 */
export function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Parse comma-separated values into array
 *
 * BUSINESS CONTEXT:
 * Used for parsing multi-value form fields like prerequisites,
 * learning objectives, and target audience lists
 *
 * @param {string} value - Comma-separated string
 * @returns {string[]} Array of trimmed, non-empty values
 *
 * @example
 * parseCommaSeparated('Python, JavaScript, Java  ')
 * // Returns: ['Python', 'JavaScript', 'Java']
 *
 * parseCommaSeparated('  ,  , Hello,  , World  ')
 * // Returns: ['Hello', 'World']
 */
export function parseCommaSeparated(value) {
    if (!value) return [];
    return value.split(',')
        .map(v => v.trim())
        .filter(v => v.length > 0);
}

/**
 * Format date to localized string
 *
 * BUSINESS CONTEXT:
 * Provides consistent date formatting across the dashboard
 * Uses browser's locale for international support
 *
 * @param {string|Date} date - Date to format (ISO string or Date object)
 * @returns {string} Formatted date string
 *
 * @example
 * formatDate('2025-10-04T12:00:00Z')
 * // Returns: '10/4/2025, 12:00:00 PM' (en-US locale)
 */
export function formatDate(date) {
    if (!date) return 'N/A';
    try {
        return new Date(date).toLocaleString();
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Invalid Date';
    }
}

/**
 * Format duration in weeks to human-readable string
 *
 * BUSINESS CONTEXT:
 * Converts numeric week duration to user-friendly display format
 *
 * @param {number} weeks - Number of weeks
 * @returns {string} Formatted duration string
 *
 * @example
 * formatDuration(1)  // Returns: '1 week'
 * formatDuration(8)  // Returns: '8 weeks'
 * formatDuration(52) // Returns: '52 weeks (1 year)'
 */
export function formatDuration(weeks) {
    if (!weeks) return 'N/A';
    if (weeks === 1) return '1 week';
    if (weeks >= 52) return `${weeks} weeks (${Math.floor(weeks / 52)} year${weeks >= 104 ? 's' : ''})`;
    return `${weeks} weeks`;
}

/**
 * Show notification message to user
 *
 * BUSINESS CONTEXT:
 * Provides user feedback for actions (success, error, warning, info)
 * Critical for UX to confirm actions and report errors
 *
 * @param {string} message - Message to display
 * @param {string} type - Notification type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (default: 3000)
 *
 * @example
 * showNotification('Track created successfully', 'success')
 * showNotification('Failed to load data', 'error', 5000)
 */
export function showNotification(message, type = 'info', duration = 3000) {
    // Check if notification container exists, create if not
    let container = document.getElementById('notification-container');

    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        padding: 1rem 1.5rem;
        margin-bottom: 10px;
        border-radius: 8px;
        background: var(--card-background);
        border-left: 4px solid ${getNotificationColor(type)};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideInRight 0.3s ease;
    `;

    // Add icon based on type
    const icon = getNotificationIcon(type);
    notification.innerHTML = `
        <span style="font-size: 1.2rem;">${icon}</span>
        <span style="flex: 1;">${escapeHtml(message)}</span>
        <button onclick="this.parentElement.remove()"
                style="background: none; border: none; cursor: pointer; font-size: 1.2rem;">
            ×
        </button>
    `;

    container.appendChild(notification);

    // Auto-remove after duration
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

/**
 * Get notification color based on type
 * @private
 */
function getNotificationColor(type) {
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    return colors[type] || colors.info;
}

/**
 * Get notification icon based on type
 * @private
 */
function getNotificationIcon(type) {
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    return icons[type] || icons.info;
}

/**
 * Open modal by ID
 *
 * BUSINESS CONTEXT:
 * Centralized modal management for consistent behavior
 *
 * @param {string} modalId - ID of modal element to open
 *
 * @example
 * openModal('createProjectModal')
 */
export function openModal(modalId) {
    const modal = document.getElementById(modalId);
    console.log('openModal called for:', modalId, 'found:', !!modal);
    if (modal) {
        console.log('Adding show class to modal');
        modal.classList.add('show');

        // Explicitly show the modal
        modal.style.display = 'flex';

        // Show overlay if present
        const overlay = modal.querySelector('.modal-overlay');
        if (overlay) {
            overlay.style.display = 'block';
        }

        console.log('Modal classes:', modal.className);

        // Initialize all date inputs within the modal to current date
        // This makes it easier for users to select dates relative to today
        const dateInputs = modal.querySelectorAll('input[type="date"]');
        if (dateInputs.length > 0) {
            const currentDate = getCurrentDateString();
            dateInputs.forEach(input => {
                // Only set if the input doesn't already have a value
                if (!input.value) {
                    input.value = currentDate;
                }
            });
        }

        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    } else {
        console.error(`Modal not found: ${modalId}`);
    }
}

/**
 * Show loading spinner
 *
 * BUSINESS CONTEXT:
 * Displays loading indicator during async operations
 *
 * @param {string} message - Loading message to display
 *
 * @example
 * showLoading('Loading data...')
 */
export function showLoading(message = 'Loading...') {
    let spinner = document.getElementById('loadingSpinner');
    if (!spinner) {
        spinner = document.createElement('div');
        spinner.id = 'loadingSpinner';
        spinner.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;';
        spinner.innerHTML = `<div style="background: white; padding: 2rem; border-radius: 8px; text-align: center;"><div class="loading-spinner"></div><p>${message}</p></div>`;
        document.body.appendChild(spinner);
    }
    spinner.style.display = 'flex';
}

/**
 * Hide loading spinner
 *
 * BUSINESS CONTEXT:
 * Removes loading indicator after async operation completes
 *
 * @example
 * hideLoading()
 */
export function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

/**
 * Close modal by ID
 *
 * BUSINESS CONTEXT:
 * Closes modal and resets any associated form data
 *
 * @param {string} modalId - ID of modal element to close
 *
 * @example
 * closeModal('createProjectModal')
 */
export function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');

        // Explicitly hide the modal to prevent black screen
        modal.style.display = 'none';

        // Re-enable body scroll
        document.body.style.overflow = 'auto';

        // Hide any modal overlays/backdrops
        const overlay = modal.querySelector('.modal-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }

        // Reset form if it exists within the modal
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }

        // Restore floating dashboard AI Assistant when project modal closes
        if (modalId === 'createProjectModal') {
            const dashboardAI = document.getElementById('dashboardAIChatPanel');
            if (dashboardAI) {
                dashboardAI.style.display = '';
            }
            const aiButton = document.getElementById('aiAssistantButton');
            if (aiButton) {
                aiButton.style.display = '';
            }
        }

        console.log(`✅ Modal '${modalId}' closed successfully`);
    }
}

/**
 * Validate email address format
 *
 * BUSINESS CONTEXT:
 * Client-side validation for email fields before API submission
 * Reduces unnecessary API calls for invalid data
 *
 * @param {string} email - Email address to validate
 * @returns {boolean} True if email format is valid
 *
 * @example
 * validateEmail('user@example.com')  // Returns: true
 * validateEmail('invalid-email')     // Returns: false
 */
export function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Debounce function calls
 *
 * BUSINESS CONTEXT:
 * Prevents excessive API calls during rapid user input (e.g., search)
 * Improves performance and reduces server load
 *
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 *
 * @example
 * const debouncedSearch = debounce((term) => searchTracks(term), 300);
 * searchInput.addEventListener('keyup', (e) => debouncedSearch(e.target.value));
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
    /**
     * EXECUTE LATER OPERATION
     * PURPOSE: Execute later operation
     * WHY: Implements required business logic for system functionality
     */
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Generate unique ID
 *
 * BUSINESS CONTEXT:
 * Creates unique identifiers for temporary client-side objects
 *
 * @returns {string} Unique ID string
 *
 * @example
 * const tempId = generateUniqueId()
 * // Returns: 'id_1696435200123_abc123'
 */
export function generateUniqueId() {
    return `id_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Check if user has permission
 *
 * BUSINESS CONTEXT:
 * Client-side permission check for UI element visibility
 * Server-side validation is still required for security
 *
 * @param {string} permission - Permission to check
 * @param {Object} currentUser - Current user object
 * @returns {boolean} True if user has permission
 *
 * @example
 * if (hasPermission('create_track', currentUser)) {
 *   showCreateButton();
 * }
 */
export function hasPermission(permission, currentUser) {
    if (!currentUser) return false;

    // Site admins have all permissions
    if (currentUser.role === 'site_admin') return true;

    // Organization admins have org-level permissions
    if (currentUser.role === 'organization_admin') {
        const orgPermissions = [
            'create_project',
            'create_track',
            'add_instructor',
            'add_student',
            'view_analytics'
        ];
        return orgPermissions.includes(permission);
    }

    // Instructors have limited permissions
    if (currentUser.role === 'instructor') {
        const instructorPermissions = [
            'view_project',
            'view_track',
            'view_students'
        ];
        return instructorPermissions.includes(permission);
    }

    return false;
}

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
 *
 * @example
 * calculateProjectStatus({ start_date: '2025-01-01', end_date: '2025-12-31' })
 * // Returns: 'active' (if current date is in 2025)
 *
 * calculateProjectStatus({ start_date: '2024-01-01', end_date: '2024-12-31' })
 * // Returns: 'completed' (if current date is after 2024)
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

/**
 * Get current date in YYYY-MM-DD format for date inputs
 *
 * BUSINESS CONTEXT:
 * Provides standardized current date string for initializing HTML5 date inputs.
 * Makes it easier for users to select dates relative to today by pre-selecting
 * the current date in calendar widgets.
 *
 * @returns {string} Current date in YYYY-MM-DD format
 *
 * @example
 * getCurrentDateString()
 * // Returns: '2025-10-19' (if today is October 19, 2025)
 */
export function getCurrentDateString() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
