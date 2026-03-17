/**
 * TDD Tests for Course Creation Modal Integration with Track Management
 *
 * BUSINESS CONTEXT:
 * Organization admins need to create courses for tracks during project setup.
 * The course creation modal must integrate with existing CourseManager infrastructure
 * while pre-populating track context (trackId, trackName, difficulty).
 *
 * TECHNICAL IMPLEMENTATION:
 * Tests cover:
 * - Modal opening with track context
 * - Form pre-population with track data
 * - Integration with CourseManager.createCourse() API
 * - Course data persistence to track
 * - Error handling and validation
 */

describe('Course Creation Modal Integration', () => {
    let mockTrackContext;
    let mockCourseManager;

    beforeEach(() => {
        // Mock track context passed from track management
        mockTrackContext = {
            trackId: 'track-789',
            trackName: 'Application Development',
            difficulty: 'intermediate'
        };

        // Setup DOM
        document.body.innerHTML = `
            <div id="courseCreationModal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 id="courseModalTitle">Create Course</h2>
                    </div>
                    <div class="modal-body">
                        <form id="courseCreationForm">
                            <input type="hidden" id="courseTrackId" />
                            <input type="text" id="courseTitle" placeholder="Course Title" />
                            <textarea id="courseDescription" placeholder="Course Description"></textarea>
                            <select id="courseDifficulty">
                                <option value="beginner">Beginner</option>
                                <option value="intermediate">Intermediate</option>
                                <option value="advanced">Advanced</option>
                            </select>
                            <input type="text" id="courseCategory" placeholder="Category" />
                            <input type="number" id="courseDuration" placeholder="Duration" />
                            <select id="courseDurationUnit">
                                <option value="hours">Hours</option>
                                <option value="days">Days</option>
                                <option value="weeks">Weeks</option>
                            </select>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button id="cancelCourseBtn" class="btn btn-secondary">Cancel</button>
                        <button id="createCourseBtn" class="btn btn-primary">Create Course</button>
                    </div>
                </div>
            </div>
        `;

        // Mock CourseManager
        mockCourseManager = {
            createCourse: jest.fn().mockResolvedValue({
                id: 'course-123',
                title: 'Test Course',
                description: 'Test Description',
                track_id: 'track-789'
            })
        };

        window.CourseManager = mockCourseManager;
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('showCreateCourseModal', () => {
        test('should open course creation modal when called', () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            const modal = document.getElementById('courseCreationModal');
            expect(modal.style.display).toBe('block');
        });

        test('should pre-populate track context in form', () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            const trackIdField = document.getElementById('courseTrackId');
            const difficultyField = document.getElementById('courseDifficulty');

            expect(trackIdField.value).toBe('track-789');
            expect(difficultyField.value).toBe('intermediate');
        });

        test('should display track name in modal title', () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            const title = document.getElementById('courseModalTitle');
            expect(title.textContent).toContain('Application Development');
        });

        test('should prevent body scroll when modal opens', () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            expect(document.body.style.overflow).toBe('hidden');
        });
    });

    describe('Course Creation Form Submission', () => {
        test('should call CourseManager.createCourse with track_id when form submitted', async () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            // Fill form
            document.getElementById('courseTitle').value = 'Python Fundamentals';
            document.getElementById('courseDescription').value = 'Learn Python basics';
            document.getElementById('courseCategory').value = 'Programming';
            document.getElementById('courseDuration').value = '8';
            document.getElementById('courseDurationUnit').value = 'weeks';

            // Submit form
            const createBtn = document.getElementById('createCourseBtn');
            createBtn.click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(mockCourseManager.createCourse).toHaveBeenCalledWith({
                title: 'Python Fundamentals',
                description: 'Learn Python basics',
                difficulty_level: 'intermediate',
                category: 'Programming',
                estimated_duration: 8,
                duration_unit: 'weeks',
                track_id: 'track-789',  // ← Critical: track_id must be included
                price: 0.0,
                tags: []
            });
        });

        test('should close modal after successful course creation', async () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            document.getElementById('courseTitle').value = 'Test Course';
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            const modal = document.getElementById('courseCreationModal');
            expect(modal.style.display).toBe('none');
        });

        test('should restore body scroll after modal closes', async () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);
            document.getElementById('courseTitle').value = 'Test Course';
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(document.body.style.overflow).toBe('auto');
        });

        test('should return created course to calling context', async () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');
            const onCourseCreated = jest.fn();

            module.showCreateCourseModal(mockTrackContext, onCourseCreated);

            document.getElementById('courseTitle').value = 'Test Course';
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(onCourseCreated).toHaveBeenCalledWith({
                id: 'course-123',
                title: 'Test Course',
                description: 'Test Description',
                track_id: 'track-789'
            });
        });
    });

    describe('Form Validation', () => {
        test('should prevent submission with empty title', async () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            // Leave title empty
            document.getElementById('courseTitle').value = '';
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(mockCourseManager.createCourse).not.toHaveBeenCalled();
        });

        test('should show validation error message for empty title', async () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            document.getElementById('courseTitle').value = '';
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            const titleField = document.getElementById('courseTitle');
            expect(titleField.classList.contains('error')).toBe(true);
        });

        test('should prevent submission with title too long (>200 chars)', async () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            document.getElementById('courseTitle').value = 'a'.repeat(201);
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(mockCourseManager.createCourse).not.toHaveBeenCalled();
        });
    });

    describe('Error Handling', () => {
        test('should display error message when course creation fails', async () => {
            mockCourseManager.createCourse = jest.fn().mockRejectedValue(
                new Error('Failed to create course')
            );

            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            document.getElementById('courseTitle').value = 'Test Course';
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            // Modal should stay open
            const modal = document.getElementById('courseCreationModal');
            expect(modal.style.display).toBe('block');
        });

        test('should show network error message on API failure', async () => {
            mockCourseManager.createCourse = jest.fn().mockRejectedValue(
                new Error('Network error')
            );

            const module = require('../../../frontend/js/modules/org-admin-courses.js');
            window.showNotification = jest.fn();

            module.showCreateCourseModal(mockTrackContext);

            document.getElementById('courseTitle').value = 'Test Course';
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(window.showNotification).toHaveBeenCalledWith(
                expect.stringContaining('Network error'),
                'error'
            );
        });
    });

    describe('Cancel Functionality', () => {
        test('should close modal when cancel button clicked', () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            const cancelBtn = document.getElementById('cancelCourseBtn');
            cancelBtn.click();

            const modal = document.getElementById('courseCreationModal');
            expect(modal.style.display).toBe('none');
        });

        test('should not create course when cancelled', () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            document.getElementById('courseTitle').value = 'Test Course';
            document.getElementById('cancelCourseBtn').click();

            expect(mockCourseManager.createCourse).not.toHaveBeenCalled();
        });

        test('should reset form when modal cancelled', () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            module.showCreateCourseModal(mockTrackContext);

            document.getElementById('courseTitle').value = 'Test Course';
            document.getElementById('cancelCourseBtn').click();

            // Reopen modal
            module.showCreateCourseModal(mockTrackContext);

            const titleField = document.getElementById('courseTitle');
            expect(titleField.value).toBe('');
        });
    });

    describe('Integration with Track Management', () => {
        test('should be callable from window.OrgAdmin.Courses namespace', () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');

            expect(window.OrgAdmin.Courses.showCreateCourseModal).toBeDefined();
            expect(typeof window.OrgAdmin.Courses.showCreateCourseModal).toBe('function');
        });

        test('should accept callback for course creation success', async () => {
            const module = require('../../../frontend/js/modules/org-admin-courses.js');
            const callback = jest.fn();

            module.showCreateCourseModal(mockTrackContext, callback);

            document.getElementById('courseTitle').value = 'Test Course';
            document.getElementById('createCourseBtn').click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(callback).toHaveBeenCalled();
        });
    });
});
