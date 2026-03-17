/**
 * TDD Tests for Track Management in Project Wizard
 *
 * BUSINESS CONTEXT:
 * Tests the track management functionality within the project creation wizard.
 * Org admins need to populate tracks with instructors, courses, and students
 * after tracks are auto-generated during project creation.
 *
 * TECHNICAL IMPLEMENTATION:
 * Tests cover:
 * - Track detail viewing within wizard
 * - Instructor assignment to tracks
 * - Course creation integration
 * - Student assignment to tracks
 * - Modal visibility and blur issues
 */

describe('Track Management in Project Wizard', () => {
    let mockOrganizationId;
    let mockProjectId;
    let mockTrack;

    beforeEach(() => {
        mockOrganizationId = 'org-123';
        mockProjectId = 'project-456';
        mockTrack = {
            id: 'track-789',
            name: 'Application Development',
            description: 'Training for app developers',
            difficulty: 'intermediate',
            skills: ['coding', 'testing'],
            audience: 'application_developers'
        };

        // Setup DOM
        document.body.innerHTML = `
            <div id="trackManagementModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 id="trackManagementTitle"></h2>
                    </div>
                    <div class="modal-body">
                        <div class="modal-tabs">
                            <button id="trackInfoTab" class="modal-tab active">Info</button>
                            <button id="trackInstructorsTab" class="modal-tab">Instructors</button>
                            <button id="trackCoursesTab" class="modal-tab">Courses</button>
                            <button id="trackStudentsTab" class="modal-tab">Students</button>
                        </div>
                        <div id="trackInfoContent" class="tab-content active"></div>
                        <div id="trackInstructorsContent" class="tab-content"></div>
                        <div id="trackCoursesContent" class="tab-content"></div>
                        <div id="trackStudentsContent" class="tab-content"></div>
                    </div>
                </div>
            </div>
            <div id="tracksReviewList"></div>
        `;
    });

    describe('openTrackManagement', () => {
        test('should open track management modal with track info', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');

            module.openTrackManagement(mockTrack);

            const modal = document.getElementById('trackManagementModal');
            const title = document.getElementById('trackManagementTitle');

            expect(modal.style.display).not.toBe('none');
            expect(title.textContent).toContain('Application Development');
        });

        test('should populate track info tab with track details', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');

            module.openTrackManagement(mockTrack);

            const content = document.getElementById('trackInfoContent');
            expect(content.innerHTML).toContain('Application Development');
            expect(content.innerHTML).toContain('intermediate');
            expect(content.innerHTML).toContain('coding');
        });

        test('should load instructors tab when clicked', async () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: async () => ([
                    { id: 'inst-1', name: 'John Doe', email: 'john@example.com' }
                ])
            });

            module.openTrackManagement(mockTrack);

            const instructorsTab = document.getElementById('trackInstructorsTab');
            instructorsTab.click();

            await new Promise(resolve => setTimeout(resolve, 0));

            const content = document.getElementById('trackInstructorsContent');
            expect(content.innerHTML).toContain('John Doe');
        });

        test('should show "Add Instructor" button in instructors tab', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');

            module.openTrackManagement(mockTrack);

            const instructorsTab = document.getElementById('trackInstructorsTab');
            instructorsTab.click();

            const content = document.getElementById('trackInstructorsContent');
            expect(content.innerHTML).toContain('Add Instructor');
        });
    });

    describe('addInstructorToTrack', () => {
        test('should open instructor selection modal', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');

            document.body.innerHTML += `
                <div id="instructorSelectionModal" class="modal" style="display: none;"></div>
            `;

            module.addInstructorToTrack('track-789');

            const modal = document.getElementById('instructorSelectionModal');
            expect(modal.style.display).not.toBe('none');
        });

        test('should load available instructors from organization', async () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: async () => ([
                    { id: 'inst-1', name: 'John Doe', email: 'john@example.com' },
                    { id: 'inst-2', name: 'Jane Smith', email: 'jane@example.com' }
                ])
            });

            document.body.innerHTML += `
                <div id="availableInstructorsList"></div>
            `;

            await module.addInstructorToTrack('track-789');

            const list = document.getElementById('availableInstructorsList');
            expect(list.innerHTML).toContain('John Doe');
            expect(list.innerHTML).toContain('Jane Smith');
        });
    });

    describe('createCourseForTrack', () => {
        test('should open course creation wizard', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');
            window.OrgAdmin = {
                Courses: {
                    showCreateCourseModal: jest.fn()
                }
            };

            module.createCourseForTrack('track-789');

            expect(window.OrgAdmin.Courses.showCreateCourseModal).toHaveBeenCalledWith({
                trackId: 'track-789'
            });
        });

        test('should pre-populate course wizard with track context', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');
            window.OrgAdmin = {
                Courses: {
                    showCreateCourseModal: jest.fn()
                }
            };

            module.createCourseForTrack('track-789', {
                trackName: 'Application Development',
                difficulty: 'intermediate'
            });

            expect(window.OrgAdmin.Courses.showCreateCourseModal).toHaveBeenCalledWith({
                trackId: 'track-789',
                trackName: 'Application Development',
                difficulty: 'intermediate'
            });
        });
    });

    describe('Modal Blur Background Fix', () => {
        test('should not apply blur filter to modal overlay', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');

            module.openTrackManagement(mockTrack);

            const overlay = document.querySelector('.modal-overlay');
            const computedStyle = window.getComputedStyle(overlay);

            expect(computedStyle.backdropFilter).not.toContain('blur');
            expect(computedStyle.webkitBackdropFilter).not.toContain('blur');
        });

        test('should have transparent black background instead of blur', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');

            module.openTrackManagement(mockTrack);

            const overlay = document.querySelector('.modal-overlay');
            const computedStyle = window.getComputedStyle(overlay);

            expect(computedStyle.backgroundColor).toMatch(/rgba\(0,\s*0,\s*0,\s*0\.\d+\)/);
        });
    });

    describe('Track Management Integration', () => {
        test('should add "Manage" button to each track in review list', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');

            const tracks = [mockTrack];
            module.populateTrackReviewList(tracks);

            const reviewList = document.getElementById('tracksReviewList');
            expect(reviewList.innerHTML).toContain('Manage Track');
            expect(reviewList.innerHTML).toContain(`openTrackManagement`);
        });

        test('should pass track data when manage button clicked', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');
            module.openTrackManagement = jest.fn();

            const tracks = [mockTrack];
            module.populateTrackReviewList(tracks);

            const manageButton = document.querySelector('[onclick*="openTrackManagement"]');
            expect(manageButton).toBeTruthy();
        });
    });

    describe('Tab Switching', () => {
        test('should switch to instructors tab and load instructors', async () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: async () => ([])
            });

            module.openTrackManagement(mockTrack);

            const tab = document.getElementById('trackInstructorsTab');
            tab.click();

            await new Promise(resolve => setTimeout(resolve, 0));

            expect(tab.classList.contains('active')).toBe(true);
            expect(document.getElementById('trackInstructorsContent').style.display).not.toBe('none');
        });

        test('should switch to courses tab and show course list', () => {
            const module = require('../../../frontend/js/modules/org-admin-projects.js');

            module.openTrackManagement(mockTrack);

            const tab = document.getElementById('trackCoursesTab');
            tab.click();

            expect(tab.classList.contains('active')).toBe(true);
            expect(document.getElementById('trackCoursesContent').style.display).not.toBe('none');
        });
    });
});
