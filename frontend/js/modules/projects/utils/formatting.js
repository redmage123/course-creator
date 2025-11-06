/**
 * Formatting Utilities
 *
 * BUSINESS CONTEXT:
 * Provides consistent formatting for dates, durations, and text across
 * the projects module. Ensures uniform display and XSS protection.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure functions (no side effects)
 * - XSS protection through HTML escaping
 * - Internationalization-ready
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Formatting only
 * - Open/Closed: Easy to extend with new formats
 * - Interface Segregation: Small, focused functions
 *
 * @module projects/utils/formatting
 */
export function escapeHtml(unsafe) {
    if (!unsafe) return '';

    const htmlEscapeMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };

    return String(unsafe).replace(/[&<>"']/g, (match) => htmlEscapeMap[match]);
}

/**
 * Format date for display
 *
 * BUSINESS LOGIC:
 * Displays dates in a consistent, user-friendly format.
 * Returns 'N/A' for null/undefined dates.
 *
 * FORMAT: MMM DD, YYYY (e.g., "Jan 15, 2025")
 *
 * @param {string|Date|null} date - Date to format (ISO string, Date object, or null)
 * @returns {string} Formatted date string or 'N/A'
 *
 * @example
 * formatDate('2025-01-15')  // 'Jan 15, 2025'
 * formatDate(null)          // 'N/A'
 */
export function formatDate(date) {
    if (!date) return 'N/A';

    try {
        const dateObj = typeof date === 'string' ? new Date(date) : date;

        // Check for invalid date
        if (isNaN(dateObj.getTime())) {
            return 'Invalid Date';
        }

        // Format options
        const options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };

        return dateObj.toLocaleDateString('en-US', options);
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Invalid Date';
    }
}

/**
 * Format duration in weeks to human-readable string
 *
 * BUSINESS LOGIC:
 * Converts week counts to readable format with appropriate pluralization:
 * - 1 week
 * - 2 weeks
 * - 12 weeks (3 months)
 * - 52 weeks (1 year)
 *
 * @param {number|null} weeks - Number of weeks
 * @returns {string} Formatted duration string
 *
 * @example
 * formatDuration(1)   // '1 week'
 * formatDuration(2)   // '2 weeks'
 * formatDuration(12)  // '12 weeks (3 months)'
 * formatDuration(52)  // '52 weeks (1 year)'
 * formatDuration(null) // 'N/A'
 */
export function formatDuration(weeks) {
    if (!weeks || weeks === 0) return 'N/A';

    const weeksNum = parseInt(weeks, 10);

    if (isNaN(weeksNum) || weeksNum < 0) {
        return 'N/A';
    }

    // Base format: "X week(s)"
    const weekText = weeksNum === 1 ? 'week' : 'weeks';
    let result = `${weeksNum} ${weekText}`;

    // Add helpful conversion for longer durations
    if (weeksNum >= 52) {
        const years = Math.floor(weeksNum / 52);
        const remainingWeeks = weeksNum % 52;

        if (remainingWeeks === 0) {
            const yearText = years === 1 ? 'year' : 'years';
            result += ` (${years} ${yearText})`;
        } else {
            result += ` (~${years}.${Math.round((remainingWeeks / 52) * 10)} years)`;
        }
    } else if (weeksNum >= 4) {
        const months = Math.floor(weeksNum / 4);
        const monthText = months === 1 ? 'month' : 'months';
        result += ` (~${months} ${monthText})`;
    }

    return result;
}

/**
 * Format participant count with capacity
 *
 * BUSINESS LOGIC:
 * Shows current participants vs maximum capacity.
 * Used in project cards and lists.
 *
 * @param {number} current - Current participant count
 * @param {number|null} max - Maximum participants (null = unlimited)
 * @returns {string} Formatted participant string
 *
 * @example
 * formatParticipants(25, 100)  // '25 / 100'
 * formatParticipants(50, null) // '50'
 * formatParticipants(0, 50)    // '0 / 50'
 */
export function formatParticipants(current, max) {
    const currentNum = parseInt(current, 10) || 0;

    if (!max || max === 0) {
        return `${currentNum}`;
    }

    const maxNum = parseInt(max, 10);
    return `${currentNum} / ${maxNum}`;
}

/**
 * Capitalize first letter of string
 *
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 *
 * @example
 * capitalizeFirst('active')  // 'Active'
 * capitalizeFirst('DRAFT')   // 'Draft'
 */
export function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Format file size in bytes to human-readable format
 *
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted size string
 *
 * @example
 * formatFileSize(1024)       // '1 KB'
 * formatFileSize(1048576)    // '1 MB'
 * formatFileSize(1073741824) // '1 GB'
 */
export function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Truncate text to maximum length with ellipsis
 *
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length before truncation
 * @param {string} ellipsis - Ellipsis string (default: '...')
 * @returns {string} Truncated text
 *
 * @example
 * truncate('This is a long text', 10)  // 'This is a...'
 * truncate('Short', 10)                // 'Short'
 */
export function truncate(text, maxLength, ellipsis = '...') {
    if (!text || text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength - ellipsis.length) + ellipsis;
}

/**
 * Parse comma-separated values into array
 *
 * BUSINESS LOGIC:
 * Used for parsing user input like target roles, objectives, etc.
 *
 * @param {string} csvString - Comma-separated string
 * @returns {Array<string>} Array of trimmed, non-empty values
 *
 * @example
 * parseCommaSeparated('python, java, javascript')
 * // Returns: ['python', 'java', 'javascript']
 *
 * parseCommaSeparated('  , , hello,  world,  ')
 * // Returns: ['hello', 'world']
 */
export function parseCommaSeparated(csvString) {
    if (!csvString) return [];

    return csvString
        .split(',')
        .map(item => item.trim())
        .filter(item => item.length > 0);
}

/**
 * Format phone number
 *
 * @param {string} phone - Phone number string
 * @returns {string} Formatted phone number
 *
 * @example
 * formatPhone('1234567890')  // '(123) 456-7890'
 * formatPhone('123-456-7890') // '(123) 456-7890'
 */
export function formatPhone(phone) {
    if (!phone) return '';

    // Remove all non-digit characters
    const cleaned = phone.replace(/\D/g, '');

    // Format based on length
    if (cleaned.length === 10) {
        return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned[0] === '1') {
        return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
    }

    // Return original if can't format
    return phone;
}

/**
 * Format currency (USD)
 *
 * @param {number} amount - Amount in dollars
 * @returns {string} Formatted currency string
 *
 * @example
 * formatCurrency(1234.56)  // '$1,234.56'
 * formatCurrency(0)        // '$0.00'
 */
export function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '$0.00';

    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Format percentage
 *
 * @param {number} value - Decimal value (0-1)
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage string
 *
 * @example
 * formatPercentage(0.756)    // '75.6%'
 * formatPercentage(0.756, 0) // '76%'
 * formatPercentage(1)        // '100.0%'
 */
export function formatPercentage(value, decimals = 1) {
    if (value === null || value === undefined) return '0%';

    const percentage = value * 100;
    return `${percentage.toFixed(decimals)}%`;
}

/**
 * Format relative time (time ago)
 *
 * @param {string|Date} date - Date to format
 * @returns {string} Relative time string
 *
 * @example
 * formatRelativeTime(new Date(Date.now() - 60000))      // '1 minute ago'
 * formatRelativeTime(new Date(Date.now() - 3600000))    // '1 hour ago'
 * formatRelativeTime(new Date(Date.now() - 86400000))   // '1 day ago'
 */
export function formatRelativeTime(date) {
    if (!date) return '';

    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const now = new Date();
    const diffMs = now - dateObj;
    const diffSeconds = Math.floor(diffMs / 1000);

    if (diffSeconds < 60) {
        return 'just now';
    } else if (diffSeconds < 3600) {
        const minutes = Math.floor(diffSeconds / 60);
        return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
    } else if (diffSeconds < 86400) {
        const hours = Math.floor(diffSeconds / 3600);
        return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
    } else if (diffSeconds < 604800) {
        const days = Math.floor(diffSeconds / 86400);
        return `${days} ${days === 1 ? 'day' : 'days'} ago`;
    } else {
        return formatDate(dateObj);
    }
}
