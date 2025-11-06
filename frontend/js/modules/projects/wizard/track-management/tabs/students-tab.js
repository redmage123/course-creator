/**
 * Students Tab Renderer
 *
 * BUSINESS CONTEXT:
 * Renders the "Students" tab showing all students enrolled in a track.
 * Provides UI for enrolling students and managing enrollments.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure rendering function
 * - XSS protection via HTML escaping
 * - Conditional rendering for empty state
 * - Student search and filtering support
 * - Event delegation via data-action attributes
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Students tab rendering only
 * - Open/Closed: Extensible via template customization
 *
 * @module projects/wizard/track-management/tabs/students-tab
 */
import { escapeHtml } from '../../../utils/formatting.js';

/**
 * Render track students tab content
 *
 * BUSINESS LOGIC:
 * Displays all students enrolled in the track:
 * - Student cards with name, email, and progress
 * - "Enroll Students" button to add new students
 * - Bulk enrollment support
 * - Remove student functionality
 * - Progress tracking visualization
 * - Empty state when no students enrolled
 *
 * @param {Object} track - Track data object
 * @param {Array<Object>} [track.students] - Array of student objects
 * @returns {string} HTML string for students tab
 *
 * @example
 * const html = renderTrackStudentsTab({
 *   name: 'Application Development',
 *   students: [
 *     { id: 's1', name: 'John Doe', email: 'john@example.com', progress: 75 },
 *     { id: 's2', name: 'Jane Smith', email: 'jane@example.com', progress: 50 }
 *   ]
 * });
 */
export function renderTrackStudentsTab(track) {
    const students = track.students || [];

    return `
        <div style="display: grid; gap: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0;">Enrolled Students</h4>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="btn btn-secondary" data-action="bulk-enroll">
                        📄 Bulk Enroll
                    </button>
                    <button class="btn btn-primary" data-action="enroll-student">
                        ➕ Enroll Student
                    </button>
                </div>
            </div>

            ${students.length > 0 ? `
                <div style="display: grid; gap: 0.75rem;">
                    ${students.map((student, idx) => renderStudentCard(student, idx)).join('')}
                </div>
            ` : `
                <div style="text-align: center; padding: 2rem; background: var(--hover-color);
                            border-radius: 8px; color: var(--text-muted);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">👥</div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">No students enrolled yet</div>
                    <div>Click "Enroll Student" to add students to this track.</div>
                    <div style="margin-top: 0.5rem;">
                        Use "Bulk Enroll" to add multiple students via spreadsheet.
                    </div>
                </div>
            `}

            ${students.length > 0 ? renderStudentsStats(students) : ''}
        </div>
    `;
}

/**
 * Render individual student card
 *
 * @param {Object} student - Student object
 * @param {number} index - Student index in array
 * @returns {string} HTML string for student card
 * @private
 */
function renderStudentCard(student, index) {
    const progress = student.progress || student.completion_percentage || 0;
    const progressColor = getProgressColor(progress);
    const status = student.status || 'active';
    const statusBadge = getStatusBadge(status);

    return `
        <div style="display: flex; justify-content: space-between; align-items: center;
                    padding: 1rem; background: var(--card-background);
                    border: 1px solid var(--border-color); border-radius: 8px;">
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.25rem;">
                    <div style="width: 40px; height: 40px; border-radius: 50%;
                                background: var(--primary-color); color: white;
                                display: flex; align-items: center; justify-content: center;
                                font-weight: 600; font-size: 0.9rem;">
                        ${getInitials(student.name)}
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-weight: 600;">${escapeHtml(student.name || 'Unnamed Student')}</span>
                            ${statusBadge}
                        </div>
                        <div style="font-size: 0.85rem; color: var(--text-muted);">
                            ${escapeHtml(student.email || '')}
                        </div>
                    </div>
                </div>
            </div>

            <div style="display: flex; align-items: center; gap: 1rem; margin-left: 1rem;">
                ${renderProgressBar(progress, progressColor)}
                <div style="display: flex; gap: 0.5rem;">
                    <button class="btn btn-sm btn-secondary" data-action="view-student-progress" data-index="${index}"
                            title="View detailed progress">
                        📊
                    </button>
                    <button class="btn btn-sm btn-danger" data-action="remove-student" data-index="${index}"
                            title="Remove student from track">
                        🗑️
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render progress bar with percentage
 *
 * @param {number} progress - Progress percentage (0-100)
 * @param {string} color - Progress bar color
 * @returns {string} HTML string for progress bar
 * @private
 */
function renderProgressBar(progress, color) {
    return `
        <div style="display: flex; align-items: center; gap: 0.5rem; min-width: 150px;">
            <div style="flex: 1; height: 8px; background: var(--hover-color);
                        border-radius: 4px; overflow: hidden;">
                <div style="height: 100%; background: ${color}; width: ${progress}%;
                            transition: width 0.3s ease;"></div>
            </div>
            <div style="font-size: 0.85rem; font-weight: 600; color: ${color};
                        min-width: 40px; text-align: right;">
                ${progress}%
            </div>
        </div>
    `;
}

/**
 * Get initials from name
 *
 * @param {string} name - Full name
 * @returns {string} Initials (up to 2 letters)
 * @private
 */
function getInitials(name) {
    if (!name) return '?';
    const words = name.trim().split(/\s+/);
    if (words.length === 1) {
        return words[0].charAt(0).toUpperCase();
    }
    return (words[0].charAt(0) + words[words.length - 1].charAt(0)).toUpperCase();
}

/**
 * Get progress bar color based on percentage
 *
 * @param {number} progress - Progress percentage
 * @returns {string} CSS color value
 * @private
 */
function getProgressColor(progress) {
    if (progress >= 75) return 'var(--success-color, #4caf50)';
    if (progress >= 50) return 'var(--info-color, #2196f3)';
    if (progress >= 25) return 'var(--warning-color, #ff9800)';
    return 'var(--danger-color, #f44336)';
}

/**
 * Get status badge HTML
 *
 * @param {string} status - Student status
 * @returns {string} HTML for status badge
 * @private
 */
function getStatusBadge(status) {
    const badges = {
        'active': '<span class="badge badge-success">Active</span>',
        'inactive': '<span class="badge badge-secondary">Inactive</span>',
        'completed': '<span class="badge badge-primary">Completed</span>',
        'dropped': '<span class="badge badge-danger">Dropped</span>'
    };

    return badges[status] || badges['active'];
}

/**
 * Render students statistics summary
 *
 * BUSINESS LOGIC:
 * Shows aggregate statistics across all students:
 * - Total enrolled students
 * - Average progress
 * - Active vs inactive students
 * - Completion rate
 *
 * @param {Array<Object>} students - Array of student objects
 * @returns {string} HTML string for statistics
 * @private
 */
function renderStudentsStats(students) {
    const totalStudents = students.length;
    const activeStudents = students.filter(s => (s.status || 'active') === 'active').length;
    const completedStudents = students.filter(s => (s.progress || 0) >= 100 || s.status === 'completed').length;

    const totalProgress = students.reduce((sum, s) => sum + (s.progress || s.completion_percentage || 0), 0);
    const avgProgress = totalStudents > 0 ? Math.round(totalProgress / totalStudents) : 0;

    const completionRate = totalStudents > 0 ? Math.round((completedStudents / totalStudents) * 100) : 0;

    return `
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
                    padding: 1rem; background: var(--info-bg, #e3f2fd); border-radius: 8px;
                    border-left: 4px solid var(--info-color, #2196f3);">
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                    ${totalStudents}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Total Enrolled
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--success-color, #4caf50);">
                    ${activeStudents}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Active
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--info-color, #2196f3);">
                    ${avgProgress}%
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Avg Progress
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                    ${completionRate}%
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Completion Rate
                </div>
            </div>
        </div>
    `;
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Render students tab
 * ================================
 * import { renderTrackStudentsTab } from './tabs/students-tab.js';
 *
 * const track = {
 *   name: 'Application Development',
 *   students: [
 *     {
 *       id: 's1',
 *       name: 'John Doe',
 *       email: 'john@example.com',
 *       progress: 75,
 *       status: 'active'
 *     },
 *     {
 *       id: 's2',
 *       name: 'Jane Smith',
 *       email: 'jane@example.com',
 *       progress: 50,
 *       status: 'active'
 *     }
 *   ]
 * };
 *
 * const html = renderTrackStudentsTab(track);
 * document.getElementById('studentsTabContent').innerHTML = html;
 *
 *
 * Example 2: Empty state
 * ======================
 * const emptyTrack = { name: 'New Track', students: [] };
 * const html = renderTrackStudentsTab(emptyTrack);
 * // Shows empty state with enrollment prompts
 *
 *
 * Example 3: Handle student actions
 * ==================================
 * // Event delegation in controller
 * document.addEventListener('click', (e) => {
 *   const action = e.target.dataset.action;
 *   const index = e.target.dataset.index;
 *
 *   if (action === 'enroll-student') {
 *     openStudentEnrollmentModal(track);
 *   } else if (action === 'bulk-enroll') {
 *     openBulkEnrollmentModal(track);
 *   } else if (action === 'remove-student') {
 *     removeStudentFromTrack(track, index);
 *   } else if (action === 'view-student-progress') {
 *     viewStudentProgress(track.students[index]);
 *   }
 * });
 */