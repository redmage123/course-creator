/**
 * Prerequisite Checker Component
 *
 * BUSINESS REQUIREMENT:
 * Display course prerequisites and check if student has met them
 * before allowing enrollment.
 *
 * FEATURES:
 * - Visual prerequisite tree
 * - Completed/incomplete status indicators
 * - Alternative prerequisite paths
 * - Recommended courses to take first
 * - Enrollment readiness indicator
 *
 * USAGE:
 * const checker = new PrerequisiteChecker(courseId, studentId);
 * await checker.render('prerequisite-container');
 */

import { knowledgeGraphClient } from '../knowledge-graph-client.js';

class PrerequisiteChecker {
    constructor(courseId, studentId = null) {
        this.courseId = courseId;
        this.studentId = studentId;
        this.data = null;
    }

    /**
     * Load prerequisite data from API
     */
    async loadData() {
        try {
            this.data = await knowledgeGraphClient.checkPrerequisites(
                this.courseId,
                this.studentId
            );
            return this.data;
        } catch (error) {
            console.error('Error loading prerequisites:', error);
            // Fail open - assume no prerequisites
            this.data = {
                ready: true,
                prerequisites: [],
                missing_prerequisites: [],
                recommended_courses: [],
                message: 'No prerequisites found'
            };
            return this.data;
        }
    }

    /**
     * Render prerequisite checker in container
     *
     * Args:
     *     containerId: DOM element ID
     */
    async render(containerId) {
        if (!this.data) {
            await this.loadData();
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        container.innerHTML = this._generateHTML();
        this._attachEventListeners(container);
    }

    /**
     * Generate HTML for prerequisite checker
     *
     * BUSINESS LOGIC:
     * - Show readiness status prominently
     * - List all prerequisites with status
     * - Highlight missing prerequisites
     * - Suggest next courses if not ready
     */
    _generateHTML() {
        const { ready, prerequisites, missing_prerequisites, recommended_courses, message } = this.data;

        return `
            <div class="prerequisite-checker">
                <!-- Readiness Status -->
                <div class="readiness-status ${ready ? 'ready' : 'not-ready'}">
                    <div class="status-icon">
                        ${ready ?
                            '<i class="fas fa-check-circle"></i>' :
                            '<i class="fas fa-exclamation-circle"></i>'}
                    </div>
                    <div class="status-content">
                        <h4>${ready ? 'You\'re ready to enroll!' : 'Prerequisites needed'}</h4>
                        <p>${message || (ready ?
                            'You have met all prerequisites for this course.' :
                            'Complete the prerequisites below before enrolling.')}</p>
                    </div>
                </div>

                <!-- Prerequisites List -->
                ${prerequisites && prerequisites.length > 0 ? `
                    <div class="prerequisites-section">
                        <h5>Prerequisites:</h5>
                        <div class="prerequisites-list">
                            ${prerequisites.map(prereq => this._renderPrerequisite(prereq)).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Missing Prerequisites (if not ready) -->
                ${!ready && missing_prerequisites && missing_prerequisites.length > 0 ? `
                    <div class="missing-prerequisites-section">
                        <h5>Missing Prerequisites:</h5>
                        <div class="missing-list">
                            ${missing_prerequisites.map(prereq => `
                                <div class="missing-prerequisite">
                                    <i class="fas fa-times-circle"></i>
                                    <span>${prereq.title || prereq}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Recommended Courses -->
                ${!ready && recommended_courses && recommended_courses.length > 0 ? `
                    <div class="recommendations-section">
                        <h5>
                            <i class="fas fa-lightbulb"></i>
                            Recommended to take first:
                        </h5>
                        <div class="recommendations-list">
                            ${recommended_courses.map(course => `
                                <a href="/course/${course.id}" class="recommended-course">
                                    <div class="course-info">
                                        <h6>${course.title}</h6>
                                        ${course.difficulty ? `
                                            <span class="difficulty-badge ${course.difficulty}">
                                                ${course.difficulty}
                                            </span>
                                        ` : ''}
                                        ${course.duration ? `
                                            <span class="duration">
                                                <i class="fas fa-clock"></i> ${course.duration}h
                                            </span>
                                        ` : ''}
                                    </div>
                                    <i class="fas fa-arrow-right"></i>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Enrollment Actions -->
                <div class="enrollment-actions">
                    ${ready ? `
                        <button class="btn btn-primary enroll-btn" data-course-id="${this.courseId}">
                            <i class="fas fa-user-plus"></i>
                            Enroll in Course
                        </button>
                    ` : `
                        <button class="btn btn-secondary view-path-btn" data-course-id="${this.courseId}">
                            <i class="fas fa-route"></i>
                            View Learning Path
                        </button>
                        <button class="btn btn-outline enroll-anyway-btn" data-course-id="${this.courseId}">
                            <i class="fas fa-exclamation-triangle"></i>
                            Enroll Anyway (Not Recommended)
                        </button>
                    `}
                </div>
            </div>
        `;
    }

    /**
     * Render a single prerequisite item
     *
     * BUSINESS LOGIC:
     * - Show completion status
     * - Indicate in-progress courses
     * - Show alternative prerequisites
     * - Link to prerequisite course
     */
    _renderPrerequisite(prereq) {
        const status = prereq.completed ? 'completed' :
                      prereq.in_progress ? 'in-progress' :
                      'not-started';

        return `
            <div class="prerequisite-item ${status}">
                <div class="prereq-status">
                    ${prereq.completed ?
                        '<i class="fas fa-check-circle status-icon completed"></i>' :
                      prereq.in_progress ?
                        '<i class="fas fa-spinner status-icon in-progress"></i>' :
                        '<i class="far fa-circle status-icon not-started"></i>'}
                </div>
                <div class="prereq-content">
                    <div class="prereq-title">
                        <a href="/course/${prereq.id}">${prereq.title}</a>
                        ${prereq.mandatory === false ?
                            '<span class="optional-badge">Optional</span>' : ''}
                    </div>
                    ${prereq.alternative ? `
                        <div class="prereq-alternative">
                            <i class="fas fa-random"></i>
                            or ${prereq.alternative}
                        </div>
                    ` : ''}
                    ${prereq.progress !== undefined && prereq.progress > 0 ? `
                        <div class="prereq-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${prereq.progress}%"></div>
                            </div>
                            <span class="progress-text">${prereq.progress}%</span>
                        </div>
                    ` : ''}
                </div>
                <div class="prereq-actions">
                    ${!prereq.completed && !prereq.in_progress ? `
                        <a href="/course/${prereq.id}" class="btn btn-sm btn-outline">
                            Start
                        </a>
                    ` : prereq.in_progress ? `
                        <a href="/course/${prereq.id}" class="btn btn-sm btn-primary">
                            Continue
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Attach event listeners
     */
    _attachEventListeners(container) {
        // Enroll button
        const enrollBtn = container.querySelector('.enroll-btn');
        if (enrollBtn) {
            enrollBtn.addEventListener('click', () => this._handleEnroll());
        }

        // View learning path button
        const viewPathBtn = container.querySelector('.view-path-btn');
        if (viewPathBtn) {
            viewPathBtn.addEventListener('click', () => this._handleViewPath());
        }

        // Enroll anyway button
        const enrollAnywayBtn = container.querySelector('.enroll-anyway-btn');
        if (enrollAnywayBtn) {
            enrollAnywayBtn.addEventListener('click', () => this._handleEnrollAnyway());
        }
    }

    /**
     * Handle enrollment
     */
    async _handleEnroll() {
        if (typeof window.enrollInCourse === 'function') {
            await window.enrollInCourse(this.courseId);
        } else {
            console.log('Enrolling in course:', this.courseId);
            window.location.href = `/enroll/${this.courseId}`;
        }
    }

    /**
     * Handle view learning path
     */
    async _handleViewPath() {
        if (typeof window.showLearningPath === 'function') {
            await window.showLearningPath(this.courseId);
        } else {
            console.log('Viewing learning path for:', this.courseId);
            window.location.href = `/learning-path?target=${this.courseId}`;
        }
    }

    /**
     * Handle enroll anyway (with warning)
     */
    async _handleEnrollAnyway() {
        const confirmed = confirm(
            'Warning: This course has prerequisites you haven\'t completed. ' +
            'Enrolling without prerequisites may make the course more difficult. ' +
            'Do you want to continue?'
        );

        if (confirmed) {
            await this._handleEnroll();
        }
    }

    /**
     * Update data and re-render
     */
    async refresh(containerId) {
        await this.loadData();
        await this.render(containerId);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PrerequisiteChecker };
}

// Make available globally
window.PrerequisiteChecker = PrerequisiteChecker;
