/**
 * Track Confirmation Dialog
 *
 * BUSINESS CONTEXT:
 * Before automatically creating tracks, shows the user a confirmation dialog
 * listing all proposed tracks. This provides transparency and control over
 * what will be created, allowing users to review track details before approval.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Dynamically generates modal HTML with track list
 * - Escapes HTML to prevent XSS attacks
 * - Attaches approve and cancel callbacks to buttons
 * - Opens modal using utility function
 * - Closes modal and executes callback on button click
 * - Automatically removes modal from DOM after use
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Track confirmation UI only
 * - Dependency Inversion: Uses injected utility functions
 *
 * USAGE:
 * import { showTrackConfirmationDialog } from './track-confirmation-dialog.js';
 *
 * showTrackConfirmationDialog(
 *   proposedTracks,
 *   (approvedTracks) => console.log('Approved:', approvedTracks),
 *   () => console.log('Cancelled')
 * );
 *
 * @module projects/wizard/track-confirmation-dialog
 */
export function showTrackConfirmationDialog(
    proposedTracks,
    onApprove,
    onCancel,
    dependencies = {}
) {
    // Validate inputs
    if (!Array.isArray(proposedTracks) || proposedTracks.length === 0) {
        console.error('proposedTracks must be a non-empty array');
        return;
    }

    if (typeof onApprove !== 'function' || typeof onCancel !== 'function') {
        console.error('onApprove and onCancel must be functions');
        return;
    }

    // Dependency injection (use provided or import from org-admin-utils)
    const {
        escapeHtml = defaultEscapeHtml,
        openModal = defaultOpenModal,
        closeModal = defaultCloseModal
    } = dependencies;

    const modalId = 'trackConfirmationModal';

    // Create modal HTML
    const modalHtml = `
        <div id="${modalId}" class="modal" role="dialog" aria-modal="true" style="display: none;">
            <div class="modal-overlay"></div>
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h2>Confirm Track Creation</h2>
                    <button class="close-modal" aria-label="Close modal" onclick="document.getElementById('${modalId}').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <p style="margin-bottom: 1rem;">
                        The following tracks will be created based on your selected target audiences:
                    </p>
                    <ul id="proposedTracksList" style="list-style: none; padding: 0; margin: 0 0 1.5rem 0;">
                        ${proposedTracks.map(track => `
                            <li style="padding: 1rem; margin-bottom: 0.75rem;
                                       background: var(--hover-color); border-radius: 8px;
                                       border-left: 4px solid var(--primary-color);">
                                <strong style="color: var(--primary-color); font-size: 1.1rem;">
                                    ${escapeHtml(track.name)}
                                </strong>
                                <p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.9rem;">
                                    ${escapeHtml(track.description)}
                                </p>
                                <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                                    <span>📊 Difficulty: ${escapeHtml(track.difficulty)}</span>
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <div class="modal-actions">
                    <button id="approveTracksBtn" class="btn btn-primary">
                        ✓ Approve and Create Tracks
                    </button>
                    <button id="cancelTracksBtn" class="btn btn-secondary">
                        ✗ Cancel
                    </button>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present (prevents duplicates)
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }

    // Insert modal into DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    openModal(modalId);

    // Attach event listeners
    const approveBtn = document.getElementById('approveTracksBtn');
    const cancelBtn = document.getElementById('cancelTracksBtn');

    if (approveBtn) {
        approveBtn.addEventListener('click', () => {
            closeModal(modalId);
            // Small delay to allow modal close animation
            setTimeout(() => {
                document.getElementById(modalId)?.remove();
                onApprove(proposedTracks);
            }, 100);
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            closeModal(modalId);
            setTimeout(() => {
                document.getElementById(modalId)?.remove();
                onCancel();
            }, 100);
        });
    }
}

/**
 * Default HTML escaping function
 *
 * SECURITY:
 * Prevents XSS attacks by escaping HTML special characters.
 * Used as fallback if escapeHtml is not provided via dependency injection.
 *
 * @param {string} unsafe - Unsafe HTML string
 * @returns {string} Escaped HTML string
 * @private
 */
function defaultEscapeHtml(unsafe) {
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
 * Default modal opening function
 *
 * @param {string} modalId - Modal element ID
 * @private
 */
function defaultOpenModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

/**
 * Default modal closing function
 *
 * @param {string} modalId - Modal element ID
 * @private
 */
function defaultCloseModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Show track approval success message
 *
 * BUSINESS LOGIC:
 * Displays success notification after tracks are created.
 * Helper function for common post-approval flow.
 *
 * @param {number} trackCount - Number of tracks created
 * @param {Function} [showNotification] - Optional notification function
 *
 * @example
 * showTrackApprovalSuccess(3, showNotification);
 * // Shows: "3 tracks created successfully"
 */
export function showTrackApprovalSuccess(trackCount, showNotification) {
    const message = `${trackCount} track${trackCount === 1 ? '' : 's'} created successfully`;

    if (showNotification && typeof showNotification === 'function') {
        showNotification(message, 'success');
    } else {
        console.log('✅', message);
    }
}

/**
 * Show track cancellation message
 *
 * BUSINESS LOGIC:
 * Displays info notification when user cancels track creation.
 *
 * @param {Function} [showNotification] - Optional notification function
 *
 * @example
 * showTrackCancellationMessage(showNotification);
 * // Shows: "Track creation cancelled"
 */
export function showTrackCancellationMessage(showNotification) {
    const message = 'Track creation cancelled';

    if (showNotification && typeof showNotification === 'function') {
        showNotification(message, 'info');
    } else {
        console.log('ℹ️', message);
    }
}

/**
 * Validate track data before showing dialog
 *
 * BUSINESS LOGIC:
 * Ensures all tracks have required fields before displaying confirmation dialog.
 *
 * @param {Object[]} tracks - Tracks to validate
 * @returns {Object} Validation result { valid: boolean, errors: string[] }
 *
 * @example
 * const validation = validateTracksForConfirmation(tracks);
 * if (!validation.valid) {
 *   console.error('Invalid tracks:', validation.errors);
 * }
 */
export function validateTracksForConfirmation(tracks) {
    const errors = [];

    if (!Array.isArray(tracks)) {
        errors.push('Tracks must be an array');
        return { valid: false, errors };
    }

    if (tracks.length === 0) {
        errors.push('At least one track is required');
        return { valid: false, errors };
    }

    tracks.forEach((track, index) => {
        if (!track.name || track.name.trim().length === 0) {
            errors.push(`Track ${index + 1}: Name is required`);
        }

        if (!track.description || track.description.trim().length === 0) {
            errors.push(`Track ${index + 1}: Description is required`);
        }

        if (!track.difficulty || !['beginner', 'intermediate', 'advanced', 'expert'].includes(track.difficulty)) {
            errors.push(`Track ${index + 1}: Valid difficulty level is required`);
        }
    });

    return {
        valid: errors.length === 0,
        errors
    };
}

/**
 * Format tracks for display
 *
 * UTILITY:
 * Formats track data for display in confirmation dialog.
 * Truncates long descriptions, ensures proper capitalization.
 *
 * @param {Object[]} tracks - Raw track data
 * @param {number} [maxDescriptionLength=200] - Max description length
 * @returns {Object[]} Formatted tracks
 */
export function formatTracksForDisplay(tracks, maxDescriptionLength = 200) {
    return tracks.map(track => ({
        ...track,
        name: track.name.trim(),
        description: truncateText(track.description, maxDescriptionLength),
        difficulty: track.difficulty.toLowerCase()
    }));
}

/**
 * Truncate text with ellipsis
 *
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 * @private
 */
function truncateText(text, maxLength) {
    if (!text || text.length <= maxLength) {
        return text;
    }

    return text.substring(0, maxLength - 3) + '...';
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic usage
 * =======================
 * import { showTrackConfirmationDialog } from './track-confirmation-dialog.js';
 *
 * const tracks = [
 *   { name: 'Application Development', description: '...', difficulty: 'intermediate' }
 * ];
 *
 * showTrackConfirmationDialog(
 *   tracks,
 *   (approved) => {
 *     console.log('User approved tracks:', approved);
 *     createTracks(approved);
 *   },
 *   () => {
 *     console.log('User cancelled');
 *   }
 * );
 *
 *
 * Example 2: With dependency injection
 * ======================================
 * import { showTrackConfirmationDialog } from './track-confirmation-dialog.js';
 * import { escapeHtml, openModal, closeModal } from '../utils/formatting.js';
 *
 * showTrackConfirmationDialog(
 *   tracks,
 *   onApprove,
 *   onCancel,
 *   { escapeHtml, openModal, closeModal }
 * );
 *
 *
 * Example 3: With validation
 * ============================
 * import { showTrackConfirmationDialog, validateTracksForConfirmation } from './track-confirmation-dialog.js';
 *
 * const validation = validateTracksForConfirmation(tracks);
 *
 * if (validation.valid) {
 *   showTrackConfirmationDialog(tracks, onApprove, onCancel);
 * } else {
 *   console.error('Invalid tracks:', validation.errors);
 * }
 *
 *
 * Example 4: Format before display
 * ==================================
 * import { formatTracksForDisplay, showTrackConfirmationDialog } from './track-confirmation-dialog.js';
 *
 * const formattedTracks = formatTracksForDisplay(rawTracks);
 * showTrackConfirmationDialog(formattedTracks, onApprove, onCancel);
 */