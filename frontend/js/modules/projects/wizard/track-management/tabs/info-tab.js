/**
 * Track Info Tab Renderer
 *
 * BUSINESS CONTEXT:
 * Renders the "Track Info" tab showing track metadata including name, description,
 * difficulty level, audience, and associated skills.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure rendering function
 * - XSS protection via HTML escaping
 * - Responsive grid layout
 * - Conditional rendering for optional fields
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Track info rendering only
 * - Open/Closed: Extensible via template customization
 *
 * @module projects/wizard/track-management/tabs/info-tab
 */
import { escapeHtml } from '../../../utils/formatting.js';

/**
 * Render track info tab content
 *
 * BUSINESS LOGIC:
 * Displays read-only track information in an organized format:
 * - Track name and description (header)
 * - Difficulty and audience (grid)
 * - Skills (badge list, conditional)
 * - Help tip for next steps
 *
 * @param {Object} track - Track data object
 * @param {string} track.name - Track name
 * @param {string} [track.description] - Track description
 * @param {string} [track.difficulty] - Difficulty level
 * @param {string} [track.audience] - Target audience
 * @param {Array<string>} [track.skills] - Associated skills
 * @returns {string} HTML string for track info tab
 *
 * @example
 * const html = renderTrackInfoTab({
 *   name: 'Application Development',
 *   description: 'Comprehensive software development training',
 *   difficulty: 'intermediate',
 *   audience: 'application_developers',
 *   skills: ['coding', 'debugging', 'testing']
 * });
 */
export function renderTrackInfoTab(track) {
    return `
        <div style="display: grid; gap: 1.5rem;">
            <div>
                <h4 style="margin: 0 0 0.5rem 0;">${escapeHtml(track.name)}</h4>
                <p style="margin: 0; color: var(--text-muted);">
                    ${escapeHtml(track.description || 'No description provided')}
                </p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <strong>Difficulty:</strong>
                    <span class="badge badge-${escapeHtml(track.difficulty || 'intermediate')}">
                        ${escapeHtml((track.difficulty || 'intermediate').charAt(0).toUpperCase() + (track.difficulty || 'intermediate').slice(1))}
                    </span>
                </div>
                <div>
                    <strong>Audience:</strong>
                    ${escapeHtml(formatAudience(track.audience))}
                </div>
            </div>

            ${renderSkillsSection(track.skills)}

            <div style="background: var(--info-bg, #e3f2fd); padding: 1rem; border-radius: 8px;
                        border-left: 4px solid var(--info-color, #2196f3);">
                <strong>💡 Tip:</strong> Use the tabs above to add instructors, create courses,
                and manage student enrollments for this track.
            </div>
        </div>
    `;
}

/**
 * Render skills section (conditional)
 *
 * @param {Array<string>} skills - Array of skill strings
 * @returns {string} HTML string for skills section or empty string
 * @private
 */
function renderSkillsSection(skills) {
    if (!skills || skills.length === 0) {
        return '';
    }

    return `
        <div>
            <strong>Skills:</strong>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                ${skills.map(skill => `
                    <span style="padding: 0.25rem 0.75rem; background: var(--hover-color);
                                 border: 1px solid var(--border-color); border-radius: 16px;
                                 font-size: 0.85rem;">
                        ${escapeHtml(skill)}
                    </span>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * Format audience identifier for display
 *
 * BUSINESS LOGIC:
 * Converts underscore-separated audience identifiers to human-readable format.
 *
 * @param {string} audience - Audience identifier (e.g., 'application_developers')
 * @returns {string} Formatted audience (e.g., 'Application Developers')
 * @private
 *
 * @example
 * formatAudience('application_developers'); // "Application Developers"
 * formatAudience('qa_engineers');          // "QA Engineers"
 */
function formatAudience(audience) {
    if (!audience) {
        return 'N/A';
    }

    return audience
        .split('_')
        .map(word => {
            // Handle acronyms
            if (word.toLowerCase() === 'qa') return 'QA';
            if (word.toLowerCase() === 'devops') return 'DevOps';
            if (word.toLowerCase() === 'api') return 'API';

            // Standard capitalization
            return word.charAt(0).toUpperCase() + word.slice(1);
        })
        .join(' ');
}

/**
 * Render track metadata summary (compact version)
 *
 * UTILITY:
 * Renders a compact summary of track info for use in other contexts
 * (e.g., dropdown previews, tooltips).
 *
 * @param {Object} track - Track data object
 * @returns {string} HTML string for compact track summary
 *
 * @example
 * const summary = renderTrackSummary(track);
 * // Returns: "<div><strong>App Dev</strong> • Intermediate • 5 skills</div>"
 */
export function renderTrackSummary(track) {
    const skillCount = track.skills ? track.skills.length : 0;
    const skillText = skillCount === 1 ? '1 skill' : `${skillCount} skills`;

    return `
        <div style="font-size: 0.9rem; color: var(--text-muted);">
            <strong>${escapeHtml(track.name)}</strong> •
            ${escapeHtml(track.difficulty || 'intermediate')} •
            ${skillText}
        </div>
    `;
}

/**
 * Render track statistics
 *
 * UTILITY:
 * Renders track statistics (instructors, courses, students count) for display.
 *
 * @param {Object} track - Track data object
 * @returns {string} HTML string for track statistics
 *
 * @example
 * const stats = renderTrackStats(track);
 */
export function renderTrackStats(track) {
    const instructorCount = track.instructors ? track.instructors.length : 0;
    const courseCount = track.courses ? track.courses.length : 0;
    const studentCount = track.students ? track.students.length : 0;

    return `
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
                    padding: 1rem; background: var(--hover-color); border-radius: 8px;">
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                    ${instructorCount}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Instructor${instructorCount === 1 ? '' : 's'}
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                    ${courseCount}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Course${courseCount === 1 ? '' : 's'}
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                    ${studentCount}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Student${studentCount === 1 ? '' : 's'}
                </div>
            </div>
        </div>
    `;
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Render track info tab
 * ==================================
 * import { renderTrackInfoTab } from './tabs/info-tab.js';
 *
 * const track = {
 *   name: 'Application Development',
 *   description: 'Software development training',
 *   difficulty: 'intermediate',
 *   audience: 'application_developers',
 *   skills: ['coding', 'debugging', 'testing']
 * };
 *
 * const html = renderTrackInfoTab(track);
 * document.getElementById('trackInfoContent').innerHTML = html;
 *
 *
 * Example 2: Render track summary
 * ================================
 * import { renderTrackSummary } from './tabs/info-tab.js';
 *
 * const summary = renderTrackSummary(track);
 * // Use in dropdown or tooltip
 *
 *
 * Example 3: Render track statistics
 * ====================================
 * import { renderTrackStats } from './tabs/info-tab.js';
 *
 * const stats = renderTrackStats(track);
 * document.getElementById('trackStats').innerHTML = stats;
 */