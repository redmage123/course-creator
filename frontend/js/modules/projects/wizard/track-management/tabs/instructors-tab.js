/**
 * Instructors Tab Renderer
 *
 * BUSINESS CONTEXT:
 * Renders the "Instructors" tab showing all instructors assigned to a track.
 * Provides UI for adding new instructors and removing existing instructors.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure rendering function
 * - XSS protection via HTML escaping
 * - Conditional rendering for empty state
 * - Event delegation via data-action attributes
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Instructors tab rendering only
 * - Open/Closed: Extensible via template customization
 *
 * @module projects/wizard/track-management/tabs/instructors-tab
 */

import { escapeHtml } from '../../../utils/formatting.js';

/**
 * Render track instructors tab content
 *
 * BUSINESS LOGIC:
 * Displays all instructors assigned to the track:
 * - Instructor cards with name and email
 * - "Add Instructor" button to assign new instructors
 * - Remove instructor functionality for each instructor
 * - Empty state when no instructors assigned
 *
 * @param {Object} track - Track data object
 * @param {Array<Object>} [track.instructors] - Array of instructor objects
 * @param {Function} [onAddClick] - Optional callback for add button (deprecated - use event delegation)
 * @param {Function} [onRemoveClick] - Optional callback for remove button (deprecated - use event delegation)
 * @returns {string} HTML string for instructors tab
 *
 * @example
 * const html = renderTrackInstructorsTab({
 *   name: 'Application Development',
 *   instructors: [
 *     { id: 'i1', name: 'John Doe', email: 'john@example.com' },
 *     { id: 'i2', name: 'Jane Smith', email: 'jane@example.com' }
 *   ]
 * });
 *
 * @example
 * // With empty state
 * const emptyTrack = { name: 'New Track', instructors: [] };
 * const html = renderTrackInstructorsTab(emptyTrack);
 * // Shows empty state with "Add Instructor" prompt
 *
 * @example
 * // Event delegation in controller
 * document.addEventListener('click', (e) => {
 *   const action = e.target.dataset.action;
 *   const index = e.target.dataset.index;
 *
 *   if (action === 'add-instructor') {
 *     openInstructorSelectionModal(track);
 *   } else if (action === 'remove-instructor') {
 *     removeInstructorFromTrack(track, index);
 *   }
 * });
 */
export function renderTrackInstructorsTab(track, onAddClick, onRemoveClick) {
    const instructors = track.instructors || [];

    return `
        <div style="display: grid; gap: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0;">Assigned Instructors</h4>
                <button class="btn btn-primary" data-action="add-instructor">
                    ➕ Add Instructor
                </button>
            </div>

            ${instructors.length > 0 ? `
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    ${instructors.map((instructor, idx) => `
                        <div style="display: flex; justify-content: space-between; align-items: center;
                                    padding: 1rem; background: var(--card-background);
                                    border: 1px solid var(--border-color); border-radius: 8px;">
                            <div>
                                <div style="font-weight: 600;">${escapeHtml(instructor.name || 'Unnamed')}</div>
                                <div style="font-size: 0.85rem; color: var(--text-muted);">
                                    ${escapeHtml(instructor.email || '')}
                                </div>
                            </div>
                            <button class="btn btn-sm btn-danger" data-action="remove-instructor" data-index="${idx}">
                                Remove
                            </button>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div style="text-align: center; padding: 2rem; background: var(--hover-color);
                            border-radius: 8px; color: var(--text-muted);">
                    No instructors assigned yet. Click "Add Instructor" to get started.
                </div>
            `}
        </div>
    `;
}
