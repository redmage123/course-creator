/**
 * Security Utilities for XSS Protection
 *
 * BUSINESS REQUIREMENT:
 * Prevent Cross-Site Scripting (XSS) attacks by sanitizing all user-generated
 * content before inserting into the DOM.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses DOMPurify library for robust HTML sanitization
 * - Provides safe alternatives to innerHTML
 * - Implements defense-in-depth with multiple escaping strategies
 *
 * SECURITY CONSIDERATIONS:
 * - All user-generated content MUST be sanitized
 * - Prefer textContent over innerHTML when HTML not needed
 * - Use parameterized approaches when possible
 */

/**
 * HTML escaping function for text-only content
 *
 * Use this when you need to display user input as text (no HTML formatting)
 *
 * @param {string} unsafe - Unsafe user input
 * @returns {string} HTML-escaped safe string
 */
export function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') {
        return '';
    }

    const div = document.createElement('div');
    div.textContent = unsafe;
    return div.innerHTML;
}

/**
 * Safely set innerHTML with DOMPurify sanitization
 *
 * Use this when you need to render HTML content from user input or API
 *
 * @param {HTMLElement} element - Target DOM element
 * @param {string} html - HTML string to sanitize and insert
 * @param {Object} options - DOMPurify configuration options
 */
export function safeSetHTML(element, html, options = {}) {
    if (!element) {
        console.error('safeSetHTML: element is null or undefined');
        return;
    }

    if (typeof html !== 'string') {
        element.innerHTML = '';
        return;
    }

    // Default DOMPurify config
    const defaultConfig = {
        ALLOWED_TAGS: [
            'b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li',
            'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'blockquote', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
        ],
        ALLOWED_ATTR: ['href', 'title', 'class', 'id', 'target', 'rel'],
        ALLOW_DATA_ATTR: false,  // Prevent data-* attributes
        FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
        FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
        ...options
    };

    // Check if DOMPurify is available
    if (typeof DOMPurify !== 'undefined') {
        const clean = DOMPurify.sanitize(html, defaultConfig);
        element.innerHTML = clean;
    } else {
        // Fallback: escape all HTML if DOMPurify not loaded
        console.warn('DOMPurify not available - falling back to text escaping');
        element.textContent = html;
    }
}

/**
 * Safely append text content (no HTML)
 *
 * Preferred method when you just need to display text
 *
 * @param {HTMLElement} element - Target element
 * @param {string} text - Text to append
 */
export function safeSetText(element, text) {
    if (!element) {
        console.error('safeSetText: element is null or undefined');
        return;
    }

    element.textContent = text || '';
}

/**
 * Create element with safe text content
 *
 * @param {string} tagName - HTML tag name (e.g., 'div', 'span')
 * @param {string} text - Text content
 * @param {string} className - Optional CSS class
 * @returns {HTMLElement} Created element
 */
export function createSafeElement(tagName, text = '', className = '') {
    const element = document.createElement(tagName);

    if (text) {
        element.textContent = text;
    }

    if (className) {
        element.className = className;
    }

    return element;
}

/**
 * Sanitize URL to prevent javascript: protocol
 *
 * @param {string} url - URL to sanitize
 * @returns {string} Safe URL or '#' if invalid
 */
export function sanitizeUrl(url) {
    if (typeof url !== 'string') {
        return '#';
    }

    // Remove whitespace
    url = url.trim();

    // Block dangerous protocols
    const dangerousProtocols = /^(javascript|data|vbscript):/i;
    if (dangerousProtocols.test(url)) {
        console.warn('Blocked dangerous URL protocol:', url);
        return '#';
    }

    // Allow only safe protocols
    const safeProtocols = /^(https?|mailto|tel):/i;
    if (url.includes(':') && !safeProtocols.test(url)) {
        console.warn('Blocked non-whitelisted protocol:', url);
        return '#';
    }

    return url;
}

/**
 * Safely set link href with URL validation
 *
 * @param {HTMLAnchorElement} link - Link element
 * @param {string} url - URL to set
 * @param {boolean} openInNewTab - Whether to open in new tab
 */
export function safeSetLink(link, url, openInNewTab = false) {
    if (!link || !(link instanceof HTMLAnchorElement)) {
        console.error('safeSetLink: invalid link element');
        return;
    }

    const safeUrl = sanitizeUrl(url);
    link.href = safeUrl;

    if (openInNewTab && safeUrl !== '#') {
        link.target = '_blank';
        link.rel = 'noopener noreferrer';  // Security best practice
    }
}

/**
 * Render user profile name safely
 *
 * Common use case: displaying user names in UI
 *
 * @param {Object} user - User object
 * @param {string} fallback - Fallback text if name unavailable
 * @returns {string} Escaped name
 */
export function renderUserName(user, fallback = 'Unknown User') {
    if (!user) {
        return escapeHtml(fallback);
    }

    const name = user.full_name || user.name || user.username || user.email;
    return escapeHtml(name || fallback);
}

/**
 * Render markdown content safely
 *
 * If you have a markdown library, this wraps it with sanitization
 *
 * @param {HTMLElement} element - Target element
 * @param {string} markdown - Markdown content
 */
export function renderMarkdownSafely(element, markdown) {
    if (!element) {
        console.error('renderMarkdownSafely: element is null');
        return;
    }

    // Check if markdown library is available (e.g., marked.js)
    if (typeof marked !== 'undefined') {
        const html = marked.parse(markdown);
        safeSetHTML(element, html);
    } else {
        // Fallback: display as plain text
        console.warn('Markdown library not available');
        element.textContent = markdown;
    }
}

/**
 * Sanitize JSON before eval/parsing from user input
 *
 * @param {string} jsonString - JSON string from user
 * @returns {Object|null} Parsed object or null if invalid
 */
export function safeParseJSON(jsonString) {
    try {
        // Validate JSON structure before parsing
        const parsed = JSON.parse(jsonString);

        // Additional validation: ensure it's an object or array
        if (typeof parsed !== 'object') {
            console.warn('safeParseJSON: not an object or array');
            return null;
        }

        return parsed;
    } catch (e) {
        console.error('safeParseJSON: invalid JSON', e);
        return null;
    }
}

/**
 * CSP (Content Security Policy) helper
 * Check if inline scripts are blocked
 *
 * @returns {boolean} True if CSP is active
 */
export function hasCSP() {
    try {
        // Try to execute inline script - will fail if CSP active
        new Function('return true;')();
        return false;
    } catch (e) {
        return true;  // CSP is active
    }
}

/**
 * Security headers check for debugging
 *
 * @returns {Object} Security header status
 */
export async function checkSecurityHeaders() {
    try {
        const response = await fetch(window.location.href, { method: 'HEAD' });

        return {
            csp: response.headers.get('Content-Security-Policy'),
            xFrameOptions: response.headers.get('X-Frame-Options'),
            xContentTypeOptions: response.headers.get('X-Content-Type-Options'),
            strictTransportSecurity: response.headers.get('Strict-Transport-Security'),
            referrerPolicy: response.headers.get('Referrer-Policy')
        };
    } catch (e) {
        console.error('Failed to check security headers:', e);
        return null;
    }
}

// Export all functions as default object for easier importing
export default {
    escapeHtml,
    safeSetHTML,
    safeSetText,
    createSafeElement,
    sanitizeUrl,
    safeSetLink,
    renderUserName,
    renderMarkdownSafely,
    safeParseJSON,
    hasCSP,
    checkSecurityHeaders
};
