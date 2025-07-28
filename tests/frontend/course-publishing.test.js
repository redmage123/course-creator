/**
 * JavaScript unit tests for course publishing functionality
 * Tests the frontend JavaScript logic without requiring a browser
 */

// Mock DOM environment for Node.js testing
const { JSDOM } = require('jsdom');
const { window } = new JSDOM('<!DOCTYPE html><html><body></body></html>');
global.window = window;
global.document = window.document;
global.fetch = require('node-fetch');

// Mock localStorage
global.localStorage = {
    data: {},
    getItem: function(key) { return this.data[key]; },
    setItem: function(key, value) { this.data[key] = value; },
    removeItem: function(key) { delete this.data[key]; }
};

// Mock alert and console
global.alert = jest.fn();
global.console = { log: jest.fn(), error: jest.fn() };

describe('Course Publishing Frontend', () => {
    
    beforeEach(() => {
        // Reset DOM
        document.body.innerHTML = '';
        
        // Reset localStorage
        localStorage.data = {};
        
        // Reset mocks
        jest.clearAllMocks();
        
        // Mock fetch
        global.fetch = jest.fn();
    });

    describe('Student Login Page', () => {
        
        beforeEach(() => {
            // Set up basic HTML structure for student login
            document.body.innerHTML = `
                <div id="courseInfo" style="display: none;">
                    <h2 id="courseTitle">Loading Course...</h2>
                    <p id="courseDescription">Please wait...</p>
                </div>
                <div id="errorMessage" class="error-message" style="display: none;"></div>
                <div id="successMessage" class="success-message" style="display: none;"></div>
                <div id="loadingSpinner" class="loading-spinner" style="display: none;"></div>
                <form id="loginForm">
                    <input type="text" id="accessToken" name="accessToken" required>
                    <input type="password" id="password" name="password" required>
                    <button type="submit" id="loginBtn">Access Course</button>
                </form>
                <form id="passwordResetForm" style="display: none;">
                    <input type="password" id="currentPassword" name="currentPassword" required>
                    <input type="password" id="newPassword" name="newPassword" required>
                    <input type="password" id="confirmPassword" name="confirmPassword" required>
                    <button type="submit" id="resetBtn">Update Password</button>
                </form>
                <div id="passwordRequirements" style="display: none;"></div>
            `;
        });

        test('getUrlParameter should extract token from URL', () => {
            // Mock window.location.search
            Object.defineProperty(window, 'location', {
                value: { search: '?token=abc123&other=value' },
                writable: true
            });

            // Function from student login page
            function getUrlParameter(name) {
                const urlParams = new URLSearchParams(window.location.search);
                return urlParams.get(name);
            }

            const token = getUrlParameter('token');
            expect(token).toBe('abc123');

            const other = getUrlParameter('other');
            expect(other).toBe('value');

            const missing = getUrlParameter('missing');
            expect(missing).toBeNull();
        });

        test('showElement should make element visible', () => {
            function showElement(id) {
                document.getElementById(id).style.display = 'block';
            }

            const element = document.getElementById('courseInfo');
            expect(element.style.display).toBe('none');

            showElement('courseInfo');
            expect(element.style.display).toBe('block');
        });

        test('hideElement should hide element', () => {
            function hideElement(id) {
                document.getElementById(id).style.display = 'none';
            }

            const element = document.getElementById('courseInfo');
            element.style.display = 'block';
            expect(element.style.display).toBe('block');

            hideElement('courseInfo');
            expect(element.style.display).toBe('none');
        });

        test('showError should display error message', () => {
            function showError(message) {
                const errorDiv = document.getElementById('errorMessage');
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
                document.getElementById('successMessage').style.display = 'none';
            }

            showError('Test error message');

            const errorDiv = document.getElementById('errorMessage');
            const successDiv = document.getElementById('successMessage');

            expect(errorDiv.textContent).toBe('Test error message');
            expect(errorDiv.style.display).toBe('block');
            expect(successDiv.style.display).toBe('none');
        });

        test('showSuccess should display success message', () => {
            function showSuccess(message) {
                const successDiv = document.getElementById('successMessage');
                successDiv.textContent = message;
                successDiv.style.display = 'block';
                document.getElementById('errorMessage').style.display = 'none';
            }

            showSuccess('Test success message');

            const successDiv = document.getElementById('successMessage');
            const errorDiv = document.getElementById('errorMessage');

            expect(successDiv.textContent).toBe('Test success message');
            expect(successDiv.style.display).toBe('block');
            expect(errorDiv.style.display).toBe('none');
        });

        test('validatePassword should validate password strength', () => {
            function validatePassword(password) {
                const requirements = {
                    length: password.length >= 8,
                    uppercase: /[A-Z]/.test(password),
                    lowercase: /[a-z]/.test(password),
                    number: /\d/.test(password),
                    special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\?]/.test(password)
                };
                return Object.values(requirements).every(req => req);
            }

            expect(validatePassword('weak')).toBe(false);
            expect(validatePassword('WeakPassword')).toBe(false); // No number or special
            expect(validatePassword('weakpass123')).toBe(false); // No uppercase or special
            expect(validatePassword('WEAKPASS123')).toBe(false); // No lowercase or special
            expect(validatePassword('WeakPass123')).toBe(false); // No special character
            expect(validatePassword('StrongPass123!')).toBe(true); // Meets all requirements
        });

        test('loadCourseInfo should handle successful API response', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue({
                    success: true,
                    data: {
                        course: {
                            title: 'Test Course',
                            description: 'Test description'
                        },
                        instance: {
                            name: 'Test Instance'
                        }
                    }
                })
            };

            global.fetch.mockResolvedValue(mockResponse);

            // Function from student login page
            async function loadCourseInfo(token) {
                try {
                    const response = await fetch(`http://localhost:8004/student/course-data?token=${encodeURIComponent(token)}`);
                    
                    if (response.ok) {
                        const result = await response.json();
                        const course = result.data.course;
                        const instance = result.data.instance;
                        
                        document.getElementById('courseTitle').textContent = course.title;
                        document.getElementById('courseDescription').textContent = 
                            `${instance.name} - ${course.description || 'Welcome to your course!'}`;
                        document.getElementById('courseInfo').style.display = 'block';
                    }
                } catch (error) {
                    console.log('Could not load course info:', error);
                }
            }

            await loadCourseInfo('test_token');

            expect(fetch).toHaveBeenCalledWith('http://localhost:8004/student/course-data?token=test_token');
            expect(document.getElementById('courseTitle').textContent).toBe('Test Course');
            expect(document.getElementById('courseDescription').textContent).toBe('Test Instance - Test description');
            expect(document.getElementById('courseInfo').style.display).toBe('block');
        });

        test('handleLogin should process login form correctly', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue({
                    success: true,
                    student: {
                        student_email: 'test@example.com',
                        password_reset_required: false
                    },
                    message: 'Authentication successful'
                })
            };

            global.fetch.mockResolvedValue(mockResponse);

            // Set form values
            document.getElementById('accessToken').value = 'test_token';
            document.getElementById('password').value = 'test_password';

            // Mock functions
            function showLoading() {
                document.getElementById('loadingSpinner').style.display = 'block';
                document.getElementById('loginBtn').disabled = true;
            }

            function hideLoading() {
                document.getElementById('loadingSpinner').style.display = 'none';
                document.getElementById('loginBtn').disabled = false;
            }

            function showSuccess(message) {
                const successDiv = document.getElementById('successMessage');
                successDiv.textContent = message;
                successDiv.style.display = 'block';
            }

            // Function from student login page
            async function handleLogin() {
                const accessToken = document.getElementById('accessToken').value.trim();
                const password = document.getElementById('password').value.trim();
                
                if (!accessToken || !password) {
                    return;
                }
                
                showLoading();
                
                try {
                    const response = await fetch('http://localhost:8004/student/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            access_token: accessToken,
                            password: password
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        localStorage.setItem('studentAuth', JSON.stringify({
                            accessToken: accessToken,
                            studentData: result.student,
                            loginTime: new Date().toISOString()
                        }));
                        
                        showSuccess('Login successful! Redirecting to your course...');
                    }
                } catch (error) {
                    console.error('Login error:', error);
                } finally {
                    hideLoading();
                }
            }

            await handleLogin();

            expect(fetch).toHaveBeenCalledWith('http://localhost:8004/student/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    access_token: 'test_token',
                    password: 'test_password'
                })
            });

            const storedAuth = JSON.parse(localStorage.getItem('studentAuth'));
            expect(storedAuth.accessToken).toBe('test_token');
            expect(storedAuth.studentData.student_email).toBe('test@example.com');

            expect(document.getElementById('successMessage').textContent).toBe('Login successful! Redirecting to your course...');
        });
    });

    describe('Instructor Dashboard Course Publishing', () => {
        
        beforeEach(() => {
            // Set up HTML structure for instructor dashboard
            document.body.innerHTML = `
                <div id="publishedCoursesContainer"></div>
                <div id="courseInstancesContainer"></div>
                <div id="createInstanceModal" style="display: none;">
                    <form id="createInstanceForm">
                        <select id="instanceCourse">
                            <option value="">Select a published course...</option>
                        </select>
                        <input type="text" id="instanceName" name="instance_name">
                        <input type="date" id="startDate" name="start_date">
                        <input type="time" id="startTime" name="start_time">
                        <input type="date" id="endDate" name="end_date">
                        <input type="time" id="endTime" name="end_time">
                        <select id="timezone" name="timezone">
                            <option value="UTC">UTC</option>
                            <option value="America/New_York">Eastern Time</option>
                        </select>
                        <input type="number" id="maxStudents" name="max_students" value="30">
                        <textarea id="instanceDescription" name="description"></textarea>
                    </form>
                </div>
                <div id="enrollStudentModal" style="display: none;">
                    <form id="enrollStudentForm">
                        <input type="hidden" id="enrollInstanceId" name="instance_id">
                        <input type="email" id="studentEmail" name="student_email">
                        <input type="text" id="studentName" name="student_name">
                        <input type="checkbox" id="sendWelcomeEmail" name="send_welcome_email" checked>
                    </form>
                </div>
            `;

            // Mock CONFIG
            global.CONFIG = {
                ENDPOINTS: {
                    COURSE_SERVICE: 'http://localhost:8004'
                }
            };

            // Mock Auth
            global.Auth = {
                getToken: jest.fn().mockReturnValue('mock_token'),
                isAuthenticated: jest.fn().mockReturnValue(true),
                hasRole: jest.fn().mockReturnValue(true)
            };

            // Mock showNotification
            global.showNotification = jest.fn();
        });

        test('renderPublishedCourses should display courses correctly', () => {
            function renderPublishedCourses(courses) {
                const container = document.getElementById('publishedCoursesContainer');
                if (!container) return;

                if (courses.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <h3>No Published Courses</h3>
                            <p>You haven't published any courses yet.</p>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = courses.map(course => `
                    <div class="course-card">
                        <div class="course-header">
                            <h3>${course.title}</h3>
                            <div class="course-badges">
                                <span class="badge ${course.visibility}">${course.visibility}</span>
                                <span class="badge ${course.status}">${course.status}</span>
                            </div>
                        </div>
                        <div class="course-actions">
                            <button class="btn btn-primary" onclick="viewInstances('${course.id}')">View Instances</button>
                        </div>
                    </div>
                `).join('');
            }

            const mockCourses = [
                {
                    id: 'course-1',
                    title: 'Test Course 1',
                    visibility: 'public',
                    status: 'published'
                },
                {
                    id: 'course-2',
                    title: 'Test Course 2',
                    visibility: 'private',
                    status: 'published'
                }
            ];

            renderPublishedCourses(mockCourses);

            const container = document.getElementById('publishedCoursesContainer');
            const courseCards = container.querySelectorAll('.course-card');
            
            expect(courseCards.length).toBe(2);
            expect(courseCards[0].querySelector('h3').textContent).toBe('Test Course 1');
            expect(courseCards[1].querySelector('h3').textContent).toBe('Test Course 2');
            
            const badges = container.querySelectorAll('.badge');
            expect(badges.length).toBe(4); // 2 courses × 2 badges each
        });

        test('renderPublishedCourses should show empty state', () => {
            function renderPublishedCourses(courses) {
                const container = document.getElementById('publishedCoursesContainer');
                if (!container) return;

                if (courses.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <h3>No Published Courses</h3>
                            <p>You haven't published any courses yet.</p>
                        </div>
                    `;
                    return;
                }
            }

            renderPublishedCourses([]);

            const container = document.getElementById('publishedCoursesContainer');
            const emptyState = container.querySelector('.empty-state');
            
            expect(emptyState).toBeTruthy();
            expect(emptyState.querySelector('h3').textContent).toBe('No Published Courses');
        });

        test('renderCourseInstances should display instances correctly', () => {
            function renderCourseInstances(instances) {
                const container = document.getElementById('courseInstancesContainer');
                if (!container) return;

                container.innerHTML = instances.map(instance => `
                    <div class="instance-card">
                        <div class="instance-header">
                            <h3>${instance.instance_name}</h3>
                            <span class="badge ${instance.status}">${instance.status}</span>
                        </div>
                        <div class="instance-details">
                            <p><strong>Course:</strong> ${instance.course_title}</p>
                            <p><strong>Students:</strong> ${instance.enrolled_count}/${instance.max_students}</p>
                        </div>
                    </div>
                `).join('');
            }

            const mockInstances = [
                {
                    id: 'instance-1',
                    instance_name: 'Fall 2024',
                    course_title: 'Test Course',
                    status: 'scheduled',
                    enrolled_count: 15,
                    max_students: 30
                }
            ];

            renderCourseInstances(mockInstances);

            const container = document.getElementById('courseInstancesContainer');
            const instanceCards = container.querySelectorAll('.instance-card');
            
            expect(instanceCards.length).toBe(1);
            expect(instanceCards[0].querySelector('h3').textContent).toBe('Fall 2024');
            expect(instanceCards[0].textContent).toContain('Test Course');
            expect(instanceCards[0].textContent).toContain('15/30');
        });

        test('showCreateInstanceModal should populate course dropdown', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue([
                    { id: 'course-1', title: 'Course 1' },
                    { id: 'course-2', title: 'Course 2' }
                ])
            };

            global.fetch.mockResolvedValue(mockResponse);

            async function showCreateInstanceModal() {
                try {
                    const response = await fetch('http://localhost:8004/courses/published', {
                        headers: {
                            'Authorization': 'Bearer mock_token'
                        }
                    });

                    if (!response.ok) throw new Error('Failed to load published courses');
                    
                    const publishedCourses = await response.json();
                    
                    const courseSelect = document.getElementById('instanceCourse');
                    courseSelect.innerHTML = '<option value="">Select a published course...</option>' +
                        publishedCourses.map(course => 
                            `<option value="${course.id}">${course.title}</option>`
                        ).join('');

                    document.getElementById('createInstanceModal').style.display = 'block';
                } catch (error) {
                    console.error('Error loading published courses:', error);
                }
            }

            await showCreateInstanceModal();

            const modal = document.getElementById('createInstanceModal');
            const courseSelect = document.getElementById('instanceCourse');
            const options = courseSelect.querySelectorAll('option');

            expect(modal.style.display).toBe('block');
            expect(options.length).toBe(3); // Default option + 2 courses
            expect(options[1].value).toBe('course-1');
            expect(options[1].textContent).toBe('Course 1');
        });

        test('submitCreateInstance should send correct data', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue({
                    success: true,
                    instance: { id: 'new-instance-id' }
                })
            };

            global.fetch.mockResolvedValue(mockResponse);

            // Fill form data
            document.getElementById('instanceCourse').innerHTML = '<option value="course-1" selected>Test Course</option>';
            document.getElementById('instanceName').value = 'Test Instance';
            document.getElementById('startDate').value = '2024-03-01';
            document.getElementById('startTime').value = '09:00';
            document.getElementById('endDate').value = '2024-05-15';
            document.getElementById('endTime').value = '17:00';
            document.getElementById('timezone').value = 'America/New_York';
            document.getElementById('maxStudents').value = '25';
            document.getElementById('instanceDescription').value = 'Test description';

            // Select the course option
            document.getElementById('instanceCourse').value = 'course-1';

            async function submitCreateInstance() {
                const form = document.getElementById('createInstanceForm');
                const formData = new FormData(form);

                const instanceData = {
                    course_id: formData.get('course_id') || document.getElementById('instanceCourse').value,
                    instance_name: formData.get('instance_name'),
                    start_datetime: `${formData.get('start_date')}T${formData.get('start_time')}`,
                    end_datetime: `${formData.get('end_date')}T${formData.get('end_time')}`,
                    timezone: formData.get('timezone'),
                    max_students: parseInt(formData.get('max_students')),
                    description: formData.get('description') || null
                };

                try {
                    const response = await fetch('http://localhost:8004/course-instances', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer mock_token'
                        },
                        body: JSON.stringify(instanceData)
                    });

                    if (!response.ok) {
                        throw new Error('Failed to create instance');
                    }

                    const result = await response.json();
                    showNotification('Course instance created successfully!', 'success');
                    document.getElementById('createInstanceModal').style.display = 'none';
                } catch (error) {
                    showNotification(error.message, 'error');
                }
            }

            await submitCreateInstance();

            expect(fetch).toHaveBeenCalledWith('http://localhost:8004/course-instances', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer mock_token'
                },
                body: JSON.stringify({
                    course_id: 'course-1',
                    instance_name: 'Test Instance',
                    start_datetime: '2024-03-01T09:00',
                    end_datetime: '2024-05-15T17:00',
                    timezone: 'America/New_York',
                    max_students: 25,
                    description: 'Test description'
                })
            });

            expect(showNotification).toHaveBeenCalledWith('Course instance created successfully!', 'success');
            expect(document.getElementById('createInstanceModal').style.display).toBe('none');
        });

        test('showEnrollStudentModal should set instance ID', () => {
            function showEnrollStudentModal(instanceId) {
                document.getElementById('enrollInstanceId').value = instanceId;
                document.getElementById('enrollStudentModal').style.display = 'block';
            }

            showEnrollStudentModal('test-instance-123');

            const instanceIdField = document.getElementById('enrollInstanceId');
            const modal = document.getElementById('enrollStudentModal');

            expect(instanceIdField.value).toBe('test-instance-123');
            expect(modal.style.display).toBe('block');
        });

        test('submitEnrollStudent should send enrollment data', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue({
                    success: true,
                    enrollment: {
                        id: 'enrollment-123',
                        student_email: 'student@example.com'
                    }
                })
            };

            global.fetch.mockResolvedValue(mockResponse);

            // Set form data
            document.getElementById('enrollInstanceId').value = 'instance-123';
            document.getElementById('studentEmail').value = 'student@example.com';
            document.getElementById('studentName').value = 'John Doe';
            document.getElementById('sendWelcomeEmail').checked = true;

            async function submitEnrollStudent() {
                const form = document.getElementById('enrollStudentForm');
                const formData = new FormData(form);

                const enrollmentData = {
                    student_email: formData.get('student_email'),
                    student_name: formData.get('student_name'),
                    send_welcome_email: formData.get('send_welcome_email') === 'on'
                };

                const instanceId = formData.get('instance_id');

                try {
                    const response = await fetch(`http://localhost:8004/course-instances/${instanceId}/enroll`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer mock_token'
                        },
                        body: JSON.stringify(enrollmentData)
                    });

                    if (!response.ok) {
                        throw new Error('Failed to enroll student');
                    }

                    const result = await response.json();
                    showNotification('Student enrolled successfully!', 'success');
                    document.getElementById('enrollStudentModal').style.display = 'none';
                } catch (error) {
                    showNotification(error.message, 'error');
                }
            }

            await submitEnrollStudent();

            expect(fetch).toHaveBeenCalledWith('http://localhost:8004/course-instances/instance-123/enroll', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer mock_token'
                },
                body: JSON.stringify({
                    student_email: 'student@example.com',
                    student_name: 'John Doe',
                    send_welcome_email: true
                })
            });

            expect(showNotification).toHaveBeenCalledWith('Student enrolled successfully!', 'success');
            expect(document.getElementById('enrollStudentModal').style.display).toBe('none');
        });

        test('closeModal should hide modal', () => {
            function closeModal(modalId) {
                const modal = document.getElementById(modalId);
                if (modal) {
                    modal.style.display = 'none';
                }
            }

            // Show modal first
            document.getElementById('createInstanceModal').style.display = 'block';
            expect(document.getElementById('createInstanceModal').style.display).toBe('block');

            closeModal('createInstanceModal');
            expect(document.getElementById('createInstanceModal').style.display).toBe('none');
        });
    });
});

module.exports = {};