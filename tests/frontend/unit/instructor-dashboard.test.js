/**
 * INSTRUCTOR DASHBOARD UNIT TESTS
 *
 * PURPOSE: Comprehensive unit testing for instructor dashboard JavaScript functionality
 * WHY: Ensures instructor dashboard methods work correctly in isolation
 *
 * TEST COVERAGE:
 * - InstructorDashboard class initialization
 * - Tab switching functionality
 * - Course management operations (create, edit, delete)
 * - Student management operations (add, remove, feedback)
 * - Feedback data loading and display
 * - Course/student rendering methods
 * - Modal creation and interaction
 * - Data validation and error handling
 *
 * TESTING STRATEGY:
 * - Mock DOM elements for UI operations
 * - Mock fetch API for network requests
 * - Mock Auth module for authentication
 * - Isolated unit tests for each method
 * - Test both success and error paths
 */

import { InstructorDashboard } from '../../../frontend/js/modules/instructor-dashboard.js';

// Mock dependencies
jest.mock('../../../frontend/js/modules/auth.js', () => ({
    Auth: {
        isAuthenticated: jest.fn(() => true),
        hasRole: jest.fn((role) => role === 'instructor'),
        getCurrentUser: jest.fn(() => ({
            id: 'instructor-123',
            full_name: 'Test Instructor',
            email: 'instructor@test.com',
            role: 'instructor'
        })),
        getToken: jest.fn(() => 'mock-token'),
        authenticatedFetch: jest.fn()
    }
}));

jest.mock('../../../frontend/js/modules/notifications.js', () => ({
    showNotification: jest.fn()
}));

jest.mock('../../../frontend/js/modules/ui-components.js', () => ({
    default: {
        createModal: jest.fn(),
        createConfirmDialog: jest.fn(),
        createAvatar: jest.fn(() => ({ outerHTML: '<div>Avatar</div>' })),
        formatDate: jest.fn((date) => new Date(date).toLocaleDateString())
    }
}));

describe('InstructorDashboard', () => {
    let dashboard;
    let mockMain;

    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = '<div id="main-content"></div>';
        mockMain = document.getElementById('main-content');

        // Mock window.CONFIG
        window.CONFIG = {
            BASE_URL: 'http://localhost:8000',
            ENDPOINTS: {
                COURSES: 'http://localhost:8002/courses',
                COURSE_BY_ID: (id) => `http://localhost:8002/courses/${id}`,
                ENROLL_STUDENT: 'http://localhost:8002/enrollments',
                REMOVE_ENROLLMENT: (id) => `http://localhost:8002/enrollments/${id}`,
                USER_SERVICE: 'http://localhost:8001',
                COURSE_SERVICE: 'http://localhost:8002'
            }
        };

        // Clear all mocks
        jest.clearAllMocks();

        // Mock fetch globally
        global.fetch = jest.fn();
    });

    afterEach(() => {
        jest.restoreAllMocks();
        document.body.innerHTML = '';
    });

    describe('Constructor and Initialization', () => {
        test('should initialize with default state', () => {
            dashboard = new InstructorDashboard();

            expect(dashboard.courses).toEqual([]);
            expect(dashboard.students).toEqual([]);
            expect(dashboard.currentCourse).toBeNull();
            expect(dashboard.activeTab).toBe('courses');
            expect(dashboard.feedbackData).toEqual({
                courseFeedback: [],
                studentFeedback: []
            });
        });

        test('should redirect if not authenticated', () => {
            const { Auth } = require('../../../frontend/js/modules/auth.js');
            Auth.isAuthenticated.mockReturnValue(false);

            delete window.location;
            window.location = { href: '' };

            dashboard = new InstructorDashboard();

            expect(window.location.href).toBe('html/index.html');
        });

        test('should redirect if not instructor role', () => {
            const { Auth } = require('../../../frontend/js/modules/auth.js');
            Auth.hasRole.mockReturnValue(false);

            delete window.location;
            window.location = { href: '' };

            dashboard = new InstructorDashboard();

            expect(window.location.href).toBe('html/index.html');
        });
    });

    describe('Tab Switching', () => {
        beforeEach(() => {
            dashboard = new InstructorDashboard();
        });

        test('should switch to courses tab', () => {
            dashboard.switchTab('courses');
            expect(dashboard.activeTab).toBe('courses');
        });

        test('should switch to students tab', () => {
            dashboard.switchTab('students');
            expect(dashboard.activeTab).toBe('students');
        });

        test('should switch to analytics tab', () => {
            dashboard.switchTab('analytics');
            expect(dashboard.activeTab).toBe('analytics');
        });

        test('should switch to content tab', () => {
            dashboard.switchTab('content');
            expect(dashboard.activeTab).toBe('content');
        });

        test('should load feedback data when switching to feedback tab', () => {
            dashboard.loadFeedbackData = jest.fn();
            dashboard.switchTab('feedback');

            expect(dashboard.activeTab).toBe('feedback');
            expect(dashboard.loadFeedbackData).toHaveBeenCalled();
        });
    });

    describe('Course Management', () => {
        beforeEach(() => {
            dashboard = new InstructorDashboard();
            dashboard.courses = [
                { id: '1', title: 'Course 1', description: 'Test course 1', is_published: true },
                { id: '2', title: 'Course 2', description: 'Test course 2', is_published: false }
            ];
        });

        describe('loadCourses', () => {
            test('should load courses successfully', async () => {
                const mockCourses = [
                    { id: '1', title: 'Course 1' },
                    { id: '2', title: 'Course 2' }
                ];

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: true,
                    json: async () => ({ courses: mockCourses })
                });

                await dashboard.loadCourses();

                expect(dashboard.courses).toEqual(mockCourses);
            });

            test('should handle courses array directly', async () => {
                const mockCourses = [
                    { id: '1', title: 'Course 1' },
                    { id: '2', title: 'Course 2' }
                ];

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: true,
                    json: async () => mockCourses
                });

                await dashboard.loadCourses();

                expect(dashboard.courses).toEqual(mockCourses);
            });

            test('should handle course loading error', async () => {
                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: false,
                    status: 500,
                    statusText: 'Internal Server Error',
                    text: async () => 'Server error'
                });

                await expect(dashboard.loadCourses()).rejects.toThrow();
            });
        });

        describe('createCourse', () => {
            test('should create course successfully', async () => {
                const formData = new FormData();
                formData.set('title', 'New Course');
                formData.set('description', 'Course description');
                formData.set('difficulty', 'beginner');
                formData.set('category', 'Programming');

                const newCourse = {
                    id: '3',
                    title: 'New Course',
                    description: 'Course description',
                    difficulty: 'beginner',
                    category: 'Programming'
                };

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: true,
                    json: async () => newCourse
                });

                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.createCourse(formData);

                expect(dashboard.courses).toContainEqual(newCourse);
                expect(showNotification).toHaveBeenCalledWith('Course created successfully!', 'success');
            });

            test('should handle course creation error', async () => {
                const formData = new FormData();
                formData.set('title', 'New Course');

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: false,
                    status: 400
                });

                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.createCourse(formData);

                expect(showNotification).toHaveBeenCalledWith('Error creating course', 'error');
            });
        });

        describe('deleteCourse', () => {
            test('should delete course successfully', async () => {
                const courseId = '1';
                dashboard.courses = [
                    { id: '1', title: 'Course 1' },
                    { id: '2', title: 'Course 2' }
                ];

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: true
                });

                const UIComponents = require('../../../frontend/js/modules/ui-components.js').default;
                UIComponents.createConfirmDialog.mockImplementation((message, callback) => {
                    callback();
                    return {};
                });

                await dashboard.deleteCourse(courseId);

                expect(dashboard.courses).toHaveLength(1);
                expect(dashboard.courses[0].id).toBe('2');
            });

            test('should handle delete course error', async () => {
                const courseId = '1';

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: false,
                    status: 500
                });

                const UIComponents = require('../../../frontend/js/modules/ui-components.js').default;
                UIComponents.createConfirmDialog.mockImplementation((message, callback) => {
                    callback();
                    return {};
                });

                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.deleteCourse(courseId);

                expect(showNotification).toHaveBeenCalledWith('Error deleting course', 'error');
            });

            test('should not delete if course not found', async () => {
                const originalLength = dashboard.courses.length;

                await dashboard.deleteCourse('nonexistent-id');

                expect(dashboard.courses).toHaveLength(originalLength);
            });
        });
    });

    describe('Student Management', () => {
        beforeEach(() => {
            dashboard = new InstructorDashboard();
            dashboard.students = [
                { id: '1', full_name: 'Student 1', email: 'student1@test.com', course_id: 'course-1' },
                { id: '2', full_name: 'Student 2', email: 'student2@test.com', course_id: 'course-1' }
            ];
        });

        describe('addStudent', () => {
            test('should add student successfully', async () => {
                const formData = new FormData();
                formData.set('email', 'newstudent@test.com');
                formData.set('course_id', 'course-1');

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: true,
                    json: async () => ({ success: true })
                });

                dashboard.loadStudents = jest.fn();
                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.addStudent(formData);

                expect(dashboard.loadStudents).toHaveBeenCalled();
                expect(showNotification).toHaveBeenCalledWith('Student added successfully!', 'success');
            });

            test('should handle add student error', async () => {
                const formData = new FormData();
                formData.set('email', 'newstudent@test.com');
                formData.set('course_id', 'course-1');

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: false,
                    status: 400
                });

                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.addStudent(formData);

                expect(showNotification).toHaveBeenCalledWith('Error adding student', 'error');
            });
        });

        describe('removeStudent', () => {
            test('should remove student successfully', async () => {
                const studentId = '1';

                const { Auth } = require('../../../frontend/js/modules/auth.js');
                Auth.authenticatedFetch.mockResolvedValue({
                    ok: true
                });

                const UIComponents = require('../../../frontend/js/modules/ui-components.js').default;
                UIComponents.createConfirmDialog.mockImplementation((message, callback) => {
                    callback();
                    return {};
                });

                await dashboard.removeStudent(studentId);

                expect(dashboard.students).toHaveLength(1);
                expect(dashboard.students[0].id).toBe('2');
            });

            test('should not remove if student not found', async () => {
                const originalLength = dashboard.students.length;

                await dashboard.removeStudent('nonexistent-id');

                expect(dashboard.students).toHaveLength(originalLength);
            });
        });
    });

    describe('Rendering Methods', () => {
        beforeEach(() => {
            dashboard = new InstructorDashboard();
            dashboard.courses = [
                {
                    id: '1',
                    title: 'Test Course',
                    description: 'Test description',
                    difficulty: 'beginner',
                    category: 'Programming',
                    enrolled_count: 10,
                    is_published: true,
                    created_at: '2025-01-01'
                }
            ];
        });

        describe('renderCourseCard', () => {
            test('should render course card with correct data', () => {
                const course = dashboard.courses[0];
                const html = dashboard.renderCourseCard(course);

                expect(html).toContain('Test Course');
                expect(html).toContain('Test description');
                expect(html).toContain('beginner');
                expect(html).toContain('Programming');
                expect(html).toContain('10 students');
                expect(html).toContain('Published');
            });

            test('should show draft status for unpublished courses', () => {
                const course = { ...dashboard.courses[0], is_published: false };
                const html = dashboard.renderCourseCard(course);

                expect(html).toContain('Draft');
            });

            test('should handle missing optional fields', () => {
                const course = {
                    id: '1',
                    title: 'Minimal Course',
                    created_at: '2025-01-01'
                };
                const html = dashboard.renderCourseCard(course);

                expect(html).toContain('No description');
                expect(html).toContain('Beginner');
                expect(html).toContain('General');
                expect(html).toContain('0 students');
            });
        });

        describe('renderStudentRow', () => {
            test('should render student row with correct data', () => {
                const student = {
                    id: '1',
                    full_name: 'Test Student',
                    email: 'test@student.com',
                    course_title: 'Test Course',
                    course_id: 'course-1',
                    progress: 75,
                    enrolled_at: '2025-01-01'
                };

                const html = dashboard.renderStudentRow(student);

                expect(html).toContain('Test Student');
                expect(html).toContain('test@student.com');
                expect(html).toContain('Test Course');
                expect(html).toContain('75%');
            });

            test('should handle missing progress', () => {
                const student = {
                    id: '1',
                    full_name: 'Test Student',
                    email: 'test@student.com',
                    course_id: 'course-1',
                    enrolled_at: '2025-01-01'
                };

                const html = dashboard.renderStudentRow(student);

                expect(html).toContain('0%');
            });
        });

        describe('renderStarRating', () => {
            test('should render 5 stars for rating 5', () => {
                const html = dashboard.renderStarRating(5);
                const activeStars = (html.match(/fa-star active/g) || []).length;
                expect(activeStars).toBe(5);
            });

            test('should render 3 stars for rating 3', () => {
                const html = dashboard.renderStarRating(3);
                const activeStars = (html.match(/fa-star active/g) || []).length;
                expect(activeStars).toBe(3);
            });

            test('should render 0 stars for rating 0', () => {
                const html = dashboard.renderStarRating(0);
                const activeStars = (html.match(/fa-star active/g) || []).length;
                expect(activeStars).toBe(0);
            });
        });
    });

    describe('Feedback Management', () => {
        beforeEach(() => {
            dashboard = new InstructorDashboard();
            dashboard.courses = [
                { id: '1', title: 'Course 1' }
            ];
            dashboard.students = [
                { id: '1', full_name: 'Student 1', course_id: '1' }
            ];
        });

        describe('loadFeedbackData', () => {
            test('should load feedback data successfully', async () => {
                // Mock feedback manager
                const mockFeedbackManager = {
                    getCourseFeedback: jest.fn().mockResolvedValue([
                        { id: '1', rating: 5, comment: 'Great course!' }
                    ]),
                    getStudentFeedback: jest.fn().mockResolvedValue([
                        { id: '1', comment: 'Good progress' }
                    ])
                };

                // Mock dynamic import
                global.feedbackManager = mockFeedbackManager;

                dashboard.updateCourseFeedbackDisplay = jest.fn();

                await dashboard.loadFeedbackData();

                expect(dashboard.feedbackData.courseFeedback).toHaveLength(1);
                expect(dashboard.feedbackData.studentFeedback).toHaveLength(1);
                expect(dashboard.updateCourseFeedbackDisplay).toHaveBeenCalled();
            });

            test('should handle missing feedback manager', async () => {
                global.feedbackManager = null;

                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.loadFeedbackData();

                expect(showNotification).toHaveBeenCalledWith('Feedback system is loading...', 'info');
            });

            test('should handle feedback loading error', async () => {
                const mockFeedbackManager = {
                    getCourseFeedback: jest.fn().mockRejectedValue(new Error('API error')),
                    getStudentFeedback: jest.fn().mockResolvedValue([])
                };

                global.feedbackManager = mockFeedbackManager;

                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.loadFeedbackData();

                expect(showNotification).toHaveBeenCalledWith('Error loading feedback data', 'error');
            });
        });
    });

    describe('Course Instance Management', () => {
        beforeEach(() => {
            dashboard = new InstructorDashboard();
        });

        describe('completeCourseInstance', () => {
            test('should complete course instance successfully', async () => {
                global.confirm = jest.fn(() => true);
                global.fetch.mockResolvedValue({
                    ok: true,
                    json: async () => ({ success: true })
                });

                dashboard.loadCourseInstances = jest.fn();
                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.completeCourseInstance('instance-1', 'Test Instance');

                expect(showNotification).toHaveBeenCalledWith(
                    expect.stringContaining('completed successfully'),
                    'success'
                );
                expect(dashboard.loadCourseInstances).toHaveBeenCalled();
            });

            test('should not complete if user cancels confirmation', async () => {
                global.confirm = jest.fn(() => false);
                dashboard.loadCourseInstances = jest.fn();

                await dashboard.completeCourseInstance('instance-1', 'Test Instance');

                expect(dashboard.loadCourseInstances).not.toHaveBeenCalled();
            });

            test('should handle completion error', async () => {
                global.confirm = jest.fn(() => true);
                global.fetch.mockResolvedValue({
                    ok: false,
                    json: async () => ({ detail: 'Error message' })
                });

                const { showNotification } = require('../../../frontend/js/modules/notifications.js');

                await dashboard.completeCourseInstance('instance-1', 'Test Instance');

                expect(showNotification).toHaveBeenCalledWith(
                    expect.stringContaining('Error completing'),
                    'error'
                );
            });
        });
    });

    describe('Quiz Management', () => {
        beforeEach(() => {
            dashboard = new InstructorDashboard();
        });

        test('should show quiz management modal for course with instances', async () => {
            const mockInstances = [
                {
                    id: 'instance-1',
                    instance_name: 'Winter 2025',
                    start_date: '2025-01-15'
                }
            ];

            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ instances: mockInstances })
            });

            await dashboard.showQuizManagement('course-1');

            const modal = document.querySelector('.modal-overlay');
            expect(modal).toBeTruthy();
            expect(modal.innerHTML).toContain('Winter 2025');
        });

        test('should show empty state for course without instances', async () => {
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ instances: [] })
            });

            await dashboard.showQuizManagement('course-1');

            const modal = document.querySelector('.modal-overlay');
            expect(modal).toBeTruthy();
            expect(modal.innerHTML).toContain('No Course Instances');
            expect(modal.innerHTML).toContain('Create Instance');
        });

        test('should handle quiz management loading error', async () => {
            global.fetch.mockResolvedValue({
                ok: false,
                status: 500
            });

            const { showNotification } = require('../../../frontend/js/modules/notifications.js');

            await dashboard.showQuizManagement('course-1');

            expect(showNotification).toHaveBeenCalledWith('Error loading quiz management', 'error');
        });
    });
});
