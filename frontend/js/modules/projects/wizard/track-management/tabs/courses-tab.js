/**
 * Courses Tab Renderer
 *
 * BUSINESS CONTEXT:
 * Renders the "Courses" tab showing all courses associated with a track.
 * Provides UI for creating new courses and removing existing courses.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure rendering function
 * - XSS protection via HTML escaping
 * - Conditional rendering for empty state
 * - Integration with external course creation modal
 * - Event delegation via data-action attributes
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Courses tab rendering only
 * - Open/Closed: Extensible via template customization
 *
 * @module projects/wizard/track-management/tabs/courses-tab
 */
import { escapeHtml } from '../../../utils/formatting.js';

/**
 * Render track courses tab content
 *
 * BUSINESS LOGIC:
 * Displays all courses associated with the track:
 * - Course cards with name, description, and enrollment info
 * - "Create Course" button to open course creation modal
 * - Remove course functionality for each course
 * - Empty state when no courses exist
 *
 * @param {Object} track - Track data object
 * @param {Array<Object>} [track.courses] - Array of course objects
 * @returns {string} HTML string for courses tab
 *
 * @example
 * const html = renderTrackCoursesTab({
 *   name: 'Application Development',
 *   courses: [
 *     { id: 'c1', name: 'Python Basics', description: 'Learn Python', enrolled: 25 },
 *     { id: 'c2', name: 'Advanced Python', description: 'Master Python', enrolled: 15 }
 *   ]
 * });
 */
export function renderTrackCoursesTab(track) {
    const courses = track.courses || [];

    return `
        <div style="display: grid; gap: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0;">Track Courses</h4>
                <button class="btn btn-primary" data-action="create-course">
                    ➕ Create Course
                </button>
            </div>

            ${courses.length > 0 ? `
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    ${courses.map((course, idx) => renderCourseCard(course, idx)).join('')}
                </div>
            ` : `
                <div style="text-align: center; padding: 2rem; background: var(--hover-color);
                            border-radius: 8px; color: var(--text-muted);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📚</div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">No courses yet</div>
                    <div>Click "Create Course" to add your first course to this track.</div>
                </div>
            `}

            ${courses.length > 0 ? renderCoursesStats(courses) : ''}
        </div>
    `;
}

/**
 * Render individual course card
 *
 * @param {Object} course - Course object
 * @param {number} index - Course index in array
 * @returns {string} HTML string for course card
 * @private
 */
function renderCourseCard(course, index) {
    const enrolledCount = course.enrolled || course.enrollment_count || 0;
    const maxEnrollment = course.max_enrollment || course.capacity || null;
    const enrollmentText = maxEnrollment
        ? `${enrolledCount} / ${maxEnrollment} enrolled`
        : `${enrolledCount} enrolled`;

    const status = course.status || 'draft';
    const statusBadge = getStatusBadge(status);

    return `
        <div style="display: flex; justify-content: space-between; align-items: flex-start;
                    padding: 1.25rem; background: var(--card-background);
                    border: 1px solid var(--border-color); border-radius: 8px;">
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                    <h5 style="margin: 0; font-size: 1.1rem;">${escapeHtml(course.name || 'Unnamed Course')}</h5>
                    ${statusBadge}
                </div>
                <p style="margin: 0.5rem 0; color: var(--text-muted); font-size: 0.9rem;">
                    ${escapeHtml(course.description || 'No description provided')}
                </p>
                <div style="display: flex; gap: 1.5rem; margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-muted);">
                    <div>
                        <span style="font-weight: 600;">📊</span> ${enrollmentText}
                    </div>
                    ${course.duration_hours ? `
                        <div>
                            <span style="font-weight: 600;">⏱️</span> ${course.duration_hours} hours
                        </div>
                    ` : ''}
                    ${course.difficulty ? `
                        <div>
                            <span style="font-weight: 600;">📈</span> ${escapeHtml(capitalize(course.difficulty))}
                        </div>
                    ` : ''}
                </div>
            </div>
            <div style="display: flex; gap: 0.5rem; margin-left: 1rem;">
                <button class="btn btn-sm btn-secondary" data-action="edit-course" data-index="${index}"
                        title="Edit course details">
                    ✏️
                </button>
                <button class="btn btn-sm btn-danger" data-action="remove-course" data-index="${index}"
                        title="Remove course from track">
                    🗑️
                </button>
            </div>
        </div>
    `;
}

/**
 * Get status badge HTML
 *
 * @param {string} status - Course status
 * @returns {string} HTML for status badge
 * @private
 */
function getStatusBadge(status) {
    const badges = {
        'published': '<span class="badge badge-success">Published</span>',
        'draft': '<span class="badge badge-secondary">Draft</span>',
        'archived': '<span class="badge badge-warning">Archived</span>',
        'active': '<span class="badge badge-success">Active</span>'
    };

    return badges[status] || badges['draft'];
}

/**
 * Capitalize first letter of string
 *
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 * @private
 */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Render courses statistics summary
 *
 * BUSINESS LOGIC:
 * Shows aggregate statistics across all courses in the track:
 * - Total courses
 * - Total enrolled students
 * - Total course hours
 *
 * @param {Array<Object>} courses - Array of course objects
 * @returns {string} HTML string for statistics
 * @private
 */
function renderCoursesStats(courses) {
    const totalCourses = courses.length;
    const totalEnrolled = courses.reduce((sum, c) => sum + (c.enrolled || c.enrollment_count || 0), 0);
    const totalHours = courses.reduce((sum, c) => sum + (c.duration_hours || 0), 0);

    return `
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
                    padding: 1rem; background: var(--info-bg, #e3f2fd); border-radius: 8px;
                    border-left: 4px solid var(--info-color, #2196f3);">
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                    ${totalCourses}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Course${totalCourses === 1 ? '' : 's'}
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                    ${totalEnrolled}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Total Enrolled
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary-color);">
                    ${totalHours}
                </div>
                <div style="font-size: 0.85rem; color: var(--text-muted);">
                    Total Hours
                </div>
            </div>
        </div>
    `;
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Render courses tab
 * ==============================
 * import { renderTrackCoursesTab } from './tabs/courses-tab.js';
 *
 * const track = {
 *   name: 'Application Development',
 *   courses: [
 *     {
 *       id: 'c1',
 *       name: 'Python Basics',
 *       description: 'Introduction to Python programming',
 *       status: 'published',
 *       enrolled: 25,
 *       max_enrollment: 50,
 *       duration_hours: 40,
 *       difficulty: 'beginner'
 *     },
 *     {
 *       id: 'c2',
 *       name: 'Advanced Python',
 *       description: 'Advanced Python concepts',
 *       status: 'draft',
 *       enrolled: 0,
 *       duration_hours: 60,
 *       difficulty: 'advanced'
 *     }
 *   ]
 * };
 *
 * const html = renderTrackCoursesTab(track);
 * document.getElementById('coursesTabContent').innerHTML = html;
 *
 *
 * Example 2: Empty state
 * ======================
 * const emptyTrack = { name: 'New Track', courses: [] };
 * const html = renderTrackCoursesTab(emptyTrack);
 * // Shows empty state with "Create Course" prompt
 *
 *
 * Example 3: Handle course actions
 * =================================
 * // Event delegation in controller
 * document.addEventListener('click', (e) => {
 *   const action = e.target.dataset.action;
 *   const index = e.target.dataset.index;
 *
 *   if (action === 'create-course') {
 *     openCourseCreationModal(track);
 *   } else if (action === 'remove-course') {
 *     removeCourseFromTrack(track, index);
 *   } else if (action === 'edit-course') {
 *     editCourse(track.courses[index]);
 *   }
 * });
 */