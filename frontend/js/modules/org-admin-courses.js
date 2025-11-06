/**
 * Organization Admin - Course Management Module
 *
 * BUSINESS CONTEXT:
 * Organization admins need to create and manage courses for their tracks during project setup.
 * This module provides course creation modal integration with track management,
 * pre-populating course context and persisting created courses to tracks.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Dynamic modal creation for course creation
 * - Integration with CourseManager API service
 * - Track context pre-population (trackId, trackName, difficulty)
 * - Form validation and error handling
 * - Callback-based course return to track management
 *
 * DEPENDENCIES:
 * - CourseManager (frontend/js/components/course-manager.js)
 * - Notification system (showNotification)
 * - Track management module (org-admin-projects.js)
 */
import { CourseManager } from '../components/course-manager.js';

// Module state
let courseManager = null;
let currentTrackContext = null;
let onCourseCreatedCallback = null;

/**
 * Initialize course manager instance
 */
function initializeCourseManager() {
    if (!courseManager) {
        courseManager = new CourseManager({
            ENDPOINTS: {
                COURSE_SERVICE: window.API_BASE_URL || 'https://localhost:8001'
            }
        });
    }
    return courseManager;
}

/**
 * Show course creation modal with track context
 *
 * BUSINESS LOGIC:
 * Opens a modal for creating a course within the context of a specific track.
 * Pre-populates form with track information (difficulty, trackId) and allows
 * org admin to fill in course details. On success, returns created course
 * to calling context (track management) via callback.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Dynamically creates modal HTML to avoid CSS conflicts
 * - Pre-populates hidden field with track_id
 * - Pre-selects difficulty based on track
 * - Validates form before submission
 * - Calls CourseManager.createCourse() API
 * - Returns created course via callback
 *
 * @param {Object} trackContext - Track context object
 * @param {string} trackContext.trackId - Track ID to associate course with
 * @param {string} trackContext.trackName - Track name for display
 * @param {string} trackContext.difficulty - Track difficulty (beginner/intermediate/advanced)
 * @param {Function} onCourseCreated - Callback function receiving created course object
 */
export function showCreateCourseModal(trackContext, onCourseCreated = null) {
    // Store context and callback
    currentTrackContext = trackContext;
    onCourseCreatedCallback = onCourseCreated;

    // Initialize CourseManager
    initializeCourseManager();

    // Remove existing modal if present
    const existingModal = document.getElementById('courseCreationModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create modal HTML dynamically
    const modalHtml = `
        <div id="courseCreationModal" class="modal" style="display: none;">
            <!-- Modal backdrop with click-to-close -->
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background-color: rgba(0, 0, 0, 0.75); z-index: 9999;"
                 onclick="window.OrgAdmin.Courses.closeCourseModal()"></div>

            <!-- Modal content -->
            <div class="modal-content" style="position: relative; z-index: 10000; max-width: 700px;
                        margin: 2rem auto; background: var(--surface-color); border-radius: 12px;">
                <div class="modal-header">
                    <h2 id="courseModalTitle">Create Course for "${escapeHtml(trackContext.trackName)}"</h2>
                    <button class="modal-close" onclick="window.OrgAdmin.Courses.closeCourseModal()">&times;</button>
                </div>

                <div class="modal-body">
                    <form id="courseCreationForm">
                        <!-- Hidden field for track_id -->
                        <input type="hidden" id="courseTrackId" value="${escapeHtml(trackContext.trackId)}" />

                        <!-- Course Title -->
                        <div class="form-group">
                            <label for="courseTitle">Course Title <span class="required">*</span></label>
                            <input type="text" id="courseTitle" class="form-control"
                                   placeholder="e.g., Python Fundamentals"
                                   maxlength="200" required />
                            <span class="validation-error" id="courseTitleError"></span>
                        </div>

                        <!-- Course Description -->
                        <div class="form-group">
                            <label for="courseDescription">Description <span class="required">*</span></label>
                            <textarea id="courseDescription" class="form-control"
                                      placeholder="Describe what students will learn..."
                                      maxlength="2000" rows="4" required></textarea>
                            <span class="validation-error" id="courseDescriptionError"></span>
                        </div>

                        <!-- Difficulty Level (pre-selected from track) -->
                        <div class="form-group">
                            <label for="courseDifficulty">Difficulty Level</label>
                            <select id="courseDifficulty" class="form-control">
                                <option value="beginner" ${trackContext.difficulty === 'beginner' ? 'selected' : ''}>Beginner</option>
                                <option value="intermediate" ${trackContext.difficulty === 'intermediate' ? 'selected' : ''}>Intermediate</option>
                                <option value="advanced" ${trackContext.difficulty === 'advanced' ? 'selected' : ''}>Advanced</option>
                            </select>
                        </div>

                        <!-- Category -->
                        <div class="form-group">
                            <label for="courseCategory">Category</label>
                            <input type="text" id="courseCategory" class="form-control"
                                   placeholder="e.g., Programming, Data Science" />
                        </div>

                        <!-- Locations (Optional) -->
                        <div class="form-group">
                            <label for="courseLocation">Locations (Optional)</label>
                            <select id="courseLocation" class="form-control">
                                <option value="">-- No specific locations --</option>
                                <!-- Locations will be populated dynamically -->
                            </select>
                            <small class="form-text">Select the locations where this course will be delivered</small>
                        </div>

                        <!-- Duration -->
                        <div class="form-group" style="display: flex; gap: 1rem;">
                            <div style="flex: 1;">
                                <label for="courseDuration">Duration</label>
                                <input type="number" id="courseDuration" class="form-control"
                                       placeholder="e.g., 8" min="1" />
                            </div>
                            <div style="flex: 1;">
                                <label for="courseDurationUnit">Unit</label>
                                <select id="courseDurationUnit" class="form-control">
                                    <option value="hours">Hours</option>
                                    <option value="days">Days</option>
                                    <option value="weeks" selected>Weeks</option>
                                    <option value="months">Months</option>
                                </select>
                            </div>
                        </div>

                        <!-- Tags (optional) -->
                        <div class="form-group">
                            <label for="courseTags">Tags (comma-separated)</label>
                            <input type="text" id="courseTags" class="form-control"
                                   placeholder="e.g., python, programming, beginner-friendly" />
                            <small class="form-text">Separate multiple tags with commas</small>
                        </div>
                    </form>
                </div>

                <div class="modal-footer">
                    <button id="cancelCourseBtn" class="btn btn-secondary"
                            onclick="window.OrgAdmin.Courses.closeCourseModal()">
                        Cancel
                    </button>
                    <button id="createCourseBtn" class="btn btn-primary"
                            onclick="window.OrgAdmin.Courses.submitCourseForm()">
                        ✓ Create Course
                    </button>
                </div>
            </div>
        </div>
    `;

    // Insert modal into DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = document.getElementById('courseCreationModal');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    // Populate locations dropdown with organization's locations
    populateLocationDropdown(trackContext.trackId);

    // Focus on title field
    setTimeout(() => {
        document.getElementById('courseTitle').focus();
    }, 100);
}

/**
 * Close course creation modal
 *
 * BUSINESS LOGIC:
 * Closes the course creation modal and restores normal page scroll.
 * Resets form and clears validation errors.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Hides modal
 * - Restores body scroll
 * - Resets form fields
 * - Removes modal from DOM
 */
export function closeCourseModal() {
    const modal = document.getElementById('courseCreationModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';

        // Reset form
        const form = document.getElementById('courseCreationForm');
        if (form) {
            form.reset();
        }

        // Clear validation errors
        document.querySelectorAll('.validation-error').forEach(el => {
            el.textContent = '';
        });
        document.querySelectorAll('.form-control.error').forEach(el => {
            el.classList.remove('error');
        });

        // Remove modal from DOM
        setTimeout(() => {
            modal.remove();
        }, 300);
    }

    // Clear context
    currentTrackContext = null;
    onCourseCreatedCallback = null;
}

/**
 * Populate locations dropdown with organization's locations
 *
 * BUSINESS LOGIC:
 * Fetches available locations for the organization and populates the course
 * locations dropdown. Locations are optional for course creation - if fetch fails,
 * dropdown remains with only the placeholder option.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches locations from track's organization via API
 * - Populates courseLocation select element with locations options
 * - Handles errors gracefully (locations are optional)
 * - Maintains placeholder as first option
 *
 * @param {string} trackId - Track ID to fetch associated locations
 * @returns {Promise<void>}
 */
async function populateLocationDropdown(trackId) {
    try {
        const locationSelect = document.getElementById('courseLocation');
        if (!locationSelect) {
            console.warn('Locations dropdown not found in DOM');
            return;
        }

        // Clear existing options except placeholder
        locationSelect.innerHTML = '<option value="">-- No specific locations --</option>';

        // Fetch locations associated with this track's organization
        // The track belongs to an organization, and locations are organization-scoped
        const response = await fetch(`${window.API_BASE_URL}/api/v1/tracks/${trackId}/locations`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            console.warn('Could not fetch locations (optional field), leaving dropdown with placeholder only');
            return;
        }

        const locations = await response.json();

        // Populate dropdown with locations options
        if (locations && Array.isArray(locations) && locations.length > 0) {
            locations.forEach(locations => {
                const option = document.createElement('option');
                option.value = locations.id || locations.location_id;
                option.textContent = locations.name || locations.location_name;
                locationSelect.appendChild(option);
            });
            console.log(`Populated ${locations.length} locations in dropdown`);
        } else {
            console.log('No locations available for this organization');
        }
    } catch (error) {
        console.error('Error loading locations:', error);
        // Locations are optional, so we don't show an error notification to the user
        // The dropdown will remain with just the placeholder option
    }
}

/**
 * Validate course creation form
 *
 * BUSINESS LOGIC:
 * Ensures all required fields are filled and meet validation criteria
 * before submitting to the API.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Title: 1-200 characters, required
 * - Description: 1-2000 characters, required
 * - Duration: positive number if provided
 * - Shows inline validation errors
 *
 * @returns {boolean} True if form is valid, false otherwise
 */
function validateCourseForm() {
    let isValid = true;

    // Clear previous errors
    document.querySelectorAll('.validation-error').forEach(el => {
        el.textContent = '';
    });
    document.querySelectorAll('.form-control.error').forEach(el => {
        el.classList.remove('error');
    });

    // Validate title
    const title = document.getElementById('courseTitle');
    if (!title.value.trim()) {
        showFieldError('courseTitle', 'Course title is required');
        isValid = false;
    } else if (title.value.length > 200) {
        showFieldError('courseTitle', 'Title must be 200 characters or less');
        isValid = false;
    }

    // Validate description
    const description = document.getElementById('courseDescription');
    if (!description.value.trim()) {
        showFieldError('courseDescription', 'Course description is required');
        isValid = false;
    } else if (description.value.length > 2000) {
        showFieldError('courseDescription', 'Description must be 2000 characters or less');
        isValid = false;
    }

    // Validate duration (if provided)
    const duration = document.getElementById('courseDuration');
    if (duration.value && parseInt(duration.value) <= 0) {
        showFieldError('courseDuration', 'Duration must be a positive number');
        isValid = false;
    }

    return isValid;
}

/**
 * Show validation error for specific field
 *
 * @param {string} fieldId - ID of the form field
 * @param {string} message - Error message to display
 */
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorSpan = document.getElementById(fieldId + 'Error');

    if (field) {
        field.classList.add('error');
    }
    if (errorSpan) {
        errorSpan.textContent = message;
    }
}

/**
 * Submit course creation form
 *
 * BUSINESS LOGIC:
 * Validates form, creates course via CourseManager API, and returns
 * created course to track management via callback.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates form fields
 * - Builds CourseCreateRequest DTO
 * - Calls CourseManager.createCourse() with track_id
 * - On success: closes modal, invokes callback with created course
 * - On error: shows error notification, keeps modal open
 *
 * @returns {Promise<void>}
 */
export async function submitCourseForm() {
    // Validate form
    if (!validateCourseForm()) {
        return;
    }

    // Disable submit button to prevent double-submit
    const submitBtn = document.getElementById('createCourseBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '⏳ Creating...';

    try {
        // Build course data object matching CourseCreateRequest DTO
        const courseData = {
            title: document.getElementById('courseTitle').value.trim(),
            description: document.getElementById('courseDescription').value.trim(),
            difficulty_level: document.getElementById('courseDifficulty').value,
            category: document.getElementById('courseCategory').value.trim() || null,
            estimated_duration: parseInt(document.getElementById('courseDuration').value) || null,
            duration_unit: document.getElementById('courseDurationUnit').value,
            track_id: currentTrackContext.trackId,  // ← Critical: associate with track
            location_id: document.getElementById('courseLocation').value || null,  // ← Optional locations
            price: 0.0,
            tags: parseTags(document.getElementById('courseTags').value)
        };

        // Call CourseManager API to create course
        const createdCourse = await courseManager.createCourse(courseData);

        // Show success notification
        if (window.showNotification) {
            window.showNotification(
                `Course "${createdCourse.title}" created successfully for track "${currentTrackContext.trackName}"`,
                'success'
            );
        }

        // Return created course to track management via callback
        if (onCourseCreatedCallback && typeof onCourseCreatedCallback === 'function') {
            onCourseCreatedCallback(createdCourse);
        }

        // Close modal
        closeCourseModal();

    } catch (error) {
        console.error('Error creating course:', error);

        // Show error notification
        if (window.showNotification) {
            window.showNotification(
                error.message || 'Failed to create course. Please try again.',
                'error'
            );
        }

        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

/**
 * Parse comma-separated tags string into array
 *
 * @param {string} tagsString - Comma-separated tags
 * @returns {string[]} Array of trimmed, non-empty tags
 */
function parseTags(tagsString) {
    if (!tagsString || !tagsString.trim()) {
        return [];
    }

    return tagsString
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);
}

/**
 * Escape HTML to prevent XSS
 *
 * @param {string} text - Text to escape
 * @returns {string} HTML-safe text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show course details modal with instructors management
 *
 * BUSINESS LOGIC:
 * Displays detailed information about a course including assigned instructors.
 * Allows org admins to manage instructor assignments (add/remove instructors,
 * assign roles like primary instructor or assistant instructor).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches course details from API
 * - Creates tabbed modal with Overview and Instructors tabs
 * - Loads instructor list from course-instructor assignment API
 * - Provides add/remove instructor functionality
 *
 * @param {string} courseId - ID of the course to display
 * @returns {Promise<void>}
 */
export async function showCourseDetailsModal(courseId) {
    try {
        // Initialize CourseManager if needed
        initializeCourseManager();

        // Fetch course details
        const response = await fetch(`${window.API_BASE_URL}/api/v1/courses/${courseId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to fetch course details');
        }

        const course = await response.json();

        // Remove existing modal if present
        const existingModal = document.getElementById('courseDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create course details modal HTML
        const modalHtml = `
            <div id="courseDetailsModal" class="modal" style="display: none;">
                <!-- Modal backdrop -->
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                            background-color: rgba(0, 0, 0, 0.75); z-index: 9999;"
                     onclick="window.OrgAdmin.Courses.closeCourseDetailsModal()"></div>

                <!-- Modal content -->
                <div class="modal-content" style="position: relative; z-index: 10000; max-width: 900px;
                            margin: 2rem auto; background: var(--surface-color); border-radius: 12px;">
                    <div class="modal-header">
                        <h2 id="courseDetailsTitle">${escapeHtml(course.title)}</h2>
                        <button class="modal-close" onclick="window.OrgAdmin.Courses.closeCourseDetailsModal()">&times;</button>
                    </div>

                    <!-- Tabs Navigation -->
                    <div class="modal-tabs">
                        <button class="tab-btn active" data-tab="overview" onclick="window.OrgAdmin.Courses.switchCourseTab('overview')">
                            Overview
                        </button>
                        <button class="tab-btn" data-tab="instructors" onclick="window.OrgAdmin.Courses.switchCourseTab('instructors')">
                            Instructors
                        </button>
                    </div>

                    <div class="modal-body">
                        <!-- Overview Tab -->
                        <div id="overviewTabContent" class="tab-pane active">
                            <div class="course-details-grid">
                                <div class="detail-item">
                                    <label>Description:</label>
                                    <p>${escapeHtml(course.description || 'No description provided')}</p>
                                </div>
                                <div class="detail-item">
                                    <label>Difficulty:</label>
                                    <p><span class="badge badge-${course.difficulty_level}">${course.difficulty_level || 'Not specified'}</span></p>
                                </div>
                                <div class="detail-item">
                                    <label>Category:</label>
                                    <p>${escapeHtml(course.category || 'Not specified')}</p>
                                </div>
                                <div class="detail-item">
                                    <label>Duration:</label>
                                    <p>${course.estimated_duration ? course.estimated_duration + ' ' + course.duration_unit : 'Not specified'}</p>
                                </div>
                            </div>
                        </div>

                        <!-- Instructors Tab -->
                        <div id="instructorsTabContent" class="tab-pane" style="display: none;">
                            <div id="courseInstructorsSection">
                                <div class="section-header">
                                    <h3>Assigned Instructors</h3>
                                    <button id="addInstructorBtn" class="btn btn-primary btn-sm"
                                            onclick="window.OrgAdmin.Courses.showAddInstructorModal('${courseId}')">
                                        + Add Instructor
                                    </button>
                                </div>

                                <!-- Instructors List -->
                                <div id="courseInstructorsList" class="instructors-list">
                                    <div class="loading-spinner"></div>
                                    <p class="text-center">Loading instructors...</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="window.OrgAdmin.Courses.closeCourseDetailsModal()">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Insert modal into DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = document.getElementById('courseDetailsModal');
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';

        // Load instructors if instructors tab is visible
        // (Will be loaded when tab is clicked, but we can preload)
        loadCourseInstructors(courseId);

    } catch (error) {
        console.error('Error showing course details:', error);
        if (window.showNotification) {
            window.showNotification(
                'Failed to load course details: ' + error.message,
                'error'
            );
        }
    }
}

/**
 * Close course details modal
 */
export function closeCourseDetailsModal() {
    const modal = document.getElementById('courseDetailsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';

        // Remove modal from DOM
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

/**
 * Switch between tabs in course details modal
 *
 * @param {string} tabName - Name of tab to switch to ('overview' or 'instructors')
 */
export function switchCourseTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.style.display = 'none';
        pane.classList.remove('active');
    });

    const targetPane = document.getElementById(`${tabName}TabContent`);
    if (targetPane) {
        targetPane.style.display = 'block';
        targetPane.classList.add('active');
    }
}

/**
 * Load and display instructors for a course
 *
 * BUSINESS LOGIC:
 * Fetches the list of instructors assigned to a course and displays them
 * with their roles (primary instructor or assistant instructor).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Calls GET /api/v1/courses/{course_id}/instructors
 * - Displays instructor list with roles
 * - Shows empty state if no instructors assigned
 *
 * @param {string} courseId - ID of the course
 * @returns {Promise<void>}
 */
export async function loadCourseInstructors(courseId) {
    const instructorsList = document.getElementById('courseInstructorsList');
    if (!instructorsList) return;

    try {
        // Show loading state
        instructorsList.innerHTML = `
            <div class="loading-spinner"></div>
            <p class="text-center">Loading instructors...</p>
        `;

        // Fetch instructors from API
        const response = await fetch(`${window.API_BASE_URL}/api/v1/courses/${courseId}/instructors`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to fetch instructors');
        }

        const instructors = await response.json();

        // Display instructors
        if (!instructors || instructors.length === 0) {
            instructorsList.innerHTML = `
                <div class="no-instructors-message empty-state">
                    <p>No instructors assigned to this course yet.</p>
                    <p class="text-sm">Click "Add Instructor" to assign instructors.</p>
                </div>
            `;
        } else {
            instructorsList.innerHTML = instructors.map(instructor => `
                <div class="instructor-item" data-instructor-id="${instructor.instructor_id || instructor.id}">
                    <div class="instructor-info">
                        <span class="instructor-name">${escapeHtml(instructor.name || instructor.username)}</span>
                        <span class="instructor-role-badge badge badge-${instructor.role === 'primary' ? 'primary' : 'secondary'}">
                            ${instructor.role === 'primary' ? 'Primary Instructor' : 'Assistant Instructor'}
                        </span>
                    </div>
                    <div class="instructor-actions">
                        <button class="btn btn-sm btn-danger" data-action="remove-instructor"
                                onclick="window.OrgAdmin.Courses.removeInstructor('${courseId}', '${instructor.instructor_id || instructor.id}')">
                            Remove
                        </button>
                    </div>
                </div>
            `).join('');
        }

    } catch (error) {
        console.error('Error loading instructors:', error);
        instructorsList.innerHTML = `
            <div class="alert alert-error">
                Failed to load instructors: ${error.message}
            </div>
        `;
    }
}

/**
 * Show add instructor modal
 *
 * BUSINESS LOGIC:
 * Opens a modal to assign a new instructor to the course with a specific role.
 *
 * @param {string} courseId - ID of the course
 */
export async function showAddInstructorModal(courseId) {
    // Remove existing modal if present
    const existingModal = document.getElementById('addInstructorModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Create add instructor modal HTML
    const modalHtml = `
        <div id="addInstructorModal" class="modal" style="display: none;">
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background-color: rgba(0, 0, 0, 0.75); z-index: 10000;"
                 onclick="window.OrgAdmin.Courses.closeAddInstructorModal()"></div>

            <div class="modal-content" style="position: relative; z-index: 10001; max-width: 500px;
                        margin: 4rem auto; background: var(--surface-color); border-radius: 12px;">
                <div class="modal-header">
                    <h3>Add Instructor to Course</h3>
                    <button class="modal-close" onclick="window.OrgAdmin.Courses.closeAddInstructorModal()">&times;</button>
                </div>

                <div class="modal-body">
                    <form id="addInstructorForm">
                        <!-- Instructor Selection -->
                        <div class="form-group">
                            <label for="instructorSelect">Select Instructor <span class="required">*</span></label>
                            <select id="instructorSelect" class="form-control" required>
                                <option value="">-- Select an instructor --</option>
                                <!-- Options will be populated dynamically -->
                            </select>
                        </div>

                        <!-- Role Selection -->
                        <div class="form-group">
                            <label>Instructor Role <span class="required">*</span></label>
                            <div class="radio-group">
                                <label class="radio-label">
                                    <input type="radio" name="instructorRole" id="rolePrimary" value="primary" checked>
                                    <span>Primary Instructor</span>
                                    <small class="form-text">Lead instructor responsible for the course</small>
                                </label>
                                <label class="radio-label">
                                    <input type="radio" name="instructorRole" id="roleAssistant" value="assistant">
                                    <span>Assistant Instructor</span>
                                    <small class="form-text">Supporting instructor for the course</small>
                                </label>
                            </div>
                        </div>
                    </form>
                </div>

                <div class="modal-footer">
                    <button class="btn btn-secondary btn-cancel" onclick="window.OrgAdmin.Courses.closeAddInstructorModal()">
                        Cancel
                    </button>
                    <button id="submitInstructorBtn" class="btn btn-primary"
                            onclick="window.OrgAdmin.Courses.submitInstructorAssignment('${courseId}')">
                        Add Instructor
                    </button>
                </div>
            </div>
        </div>
    `;

    // Insert modal into DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = document.getElementById('addInstructorModal');
    modal.style.display = 'block';

    // Populate instructor dropdown
    await populateInstructorDropdown();
}

/**
 * Close add instructor modal
 */
export function closeAddInstructorModal() {
    const modal = document.getElementById('addInstructorModal');
    if (modal) {
        modal.style.display = 'none';
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

/**
 * Populate instructor dropdown with available instructors
 *
 * BUSINESS LOGIC:
 * Fetches list of instructors in the organization who can be assigned to courses.
 *
 * @returns {Promise<void>}
 */
async function populateInstructorDropdown() {
    const instructorSelect = document.getElementById('instructorSelect');
    if (!instructorSelect) return;

    try {
        // Fetch instructors from organization
        // Note: This endpoint might need to be adjusted based on actual API structure
        const response = await fetch(`${window.API_BASE_URL}/api/v1/instructors`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            console.warn('Could not fetch instructors');
            return;
        }

        const instructors = await response.json();

        // Populate dropdown
        if (instructors && instructors.length > 0) {
            instructors.forEach(instructor => {
                const option = document.createElement('option');
                option.value = instructor.id || instructor.user_id;
                option.textContent = instructor.name || instructor.username || instructor.email;
                instructorSelect.appendChild(option);
            });
        }

    } catch (error) {
        console.error('Error loading instructors:', error);
    }
}

/**
 * Submit instructor assignment to course
 *
 * BUSINESS LOGIC:
 * Assigns selected instructor to the course with specified role.
 * Calls POST /api/v1/courses/{course_id}/instructors endpoint.
 *
 * @param {string} courseId - ID of the course
 * @returns {Promise<void>}
 */
export async function submitInstructorAssignment(courseId) {
    const instructorSelect = document.getElementById('instructorSelect');
    const roleInputs = document.getElementsByName('instructorRole');
    const submitBtn = document.getElementById('submitInstructorBtn');

    // Get selected values
    const instructorId = instructorSelect.value;
    let role = 'primary';
    for (const radio of roleInputs) {
        if (radio.checked) {
            role = radio.value;
            break;
        }
    }

    // Validate
    if (!instructorId) {
        if (window.showNotification) {
            window.showNotification('Please select an instructor', 'error');
        }
        return;
    }

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding...';

    try {
        // Call API to assign instructor
        const response = await fetch(`${window.API_BASE_URL}/api/v1/courses/${courseId}/instructors`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                instructor_id: instructorId,
                role: role
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to assign instructor');
        }

        // Show success notification
        if (window.showNotification) {
            window.showNotification('Instructor assigned successfully', 'success');
        }

        // Close modal
        closeAddInstructorModal();

        // Reload instructor list
        await loadCourseInstructors(courseId);

    } catch (error) {
        console.error('Error assigning instructor:', error);
        if (window.showNotification) {
            window.showNotification(
                'Failed to assign instructor: ' + error.message,
                'error'
            );
        }

        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.textContent = 'Add Instructor';
    }
}

/**
 * Remove instructor from course
 *
 * BUSINESS LOGIC:
 * Removes instructor assignment from the course.
 * Calls DELETE /api/v1/courses/{course_id}/instructors/{instructor_id} endpoint.
 *
 * @param {string} courseId - ID of the course
 * @param {string} instructorId - ID of the instructor to remove
 * @returns {Promise<void>}
 */
export async function removeInstructor(courseId, instructorId) {
    // Confirm removal
    if (!confirm('Are you sure you want to remove this instructor from the course?')) {
        return;
    }

    try {
        // Call API to remove instructor
        const response = await fetch(
            `${window.API_BASE_URL}/api/v1/courses/${courseId}/instructors/${instructorId}`,
            {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to remove instructor');
        }

        // Show success notification
        if (window.showNotification) {
            window.showNotification('Instructor removed successfully', 'success');
        }

        // Reload instructor list
        await loadCourseInstructors(courseId);

    } catch (error) {
        console.error('Error removing instructor:', error);
        if (window.showNotification) {
            window.showNotification(
                'Failed to remove instructor: ' + error.message,
                'error'
            );
        }
    }
}

// Export functions to window.OrgAdmin.Courses namespace
if (!window.OrgAdmin) {
    window.OrgAdmin = {};
}

if (!window.OrgAdmin.Courses) {
    window.OrgAdmin.Courses = {};
}

window.OrgAdmin.Courses = {
    ...window.OrgAdmin.Courses,
    showCreateCourseModal,
    closeCourseModal,
    submitCourseForm,
    showCourseDetailsModal,
    closeCourseDetailsModal,
    switchCourseTab,
    loadCourseInstructors,
    showAddInstructorModal,
    closeAddInstructorModal,
    submitInstructorAssignment,
    removeInstructor
};
