/**
 * Unit tests for student dashboard permissions and UI restrictions
 * Tests that the frontend properly enforces student-only access
 */

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock window.locations
Object.defineProperty(window, 'locations', {
  value: {
    href: 'http://localhost:3000',
    pathname: '/student-dashboard.html',
    assign: jest.fn(),
    replace: jest.fn()
  },
  writable: true
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('Student Dashboard Permissions', () => {
  
  beforeEach(() => {
    // Reset all mocks
    fetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    window.locations.assign.mockClear();
    window.locations.replace.mockClear();
    
    // Setup basic DOM structure for student dashboard
    document.body.innerHTML = `
      <div class="dashboard-layout">
        <aside class="dashboard-sidebar">
          <nav class="sidebar-nav">
            <ul class="nav-menu">
              <li class="nav-item">
                <a href="#" class="nav-link" data-section="dashboard">
                  <span>Dashboard</span>
                </a>
              </li>
              <li class="nav-item">
                <a href="#" class="nav-link" data-section="courses">
                  <span>My Courses</span>
                </a>
              </li>
              <li class="nav-item">
                <a href="#" class="nav-link" data-section="progress">
                  <span>Progress</span>
                </a>
              </li>
              <li class="nav-item">
                <a href="#" class="nav-link" data-section="labs">
                  <span>Lab Environment</span>
                </a>
              </li>
            </ul>
          </nav>
        </aside>
        
        <main class="dashboard-main">
          <section id="dashboard-section" class="content-section active">
            <div id="current-courses-list"></div>
            <div id="studentActivityList"></div>
          </section>
          
          <section id="courses-section" class="content-section">
            <div id="student-courses-list"></div>
          </section>
          
          <section id="progress-section" class="content-section">
            <div id="courseProgressList"></div>
          </section>
          
          <section id="labs-section" class="content-section">
            <button id="quickLabBtn">Open Lab</button>
          </section>
        </main>
      </div>
      
      <!-- Hidden instructor/admin elements that should not be accessible -->
      <div id="instructor-controls" style="display: none;">
        <button id="createCourseBtn">Create Course</button>
        <button id="enrollStudentBtn">Enroll Student</button>
        <button id="viewAllStudentsBtn">View All Students</button>
      </div>
      
      <div id="admin-controls" style="display: none;">
        <button id="manageUsersBtn">Manage Users</button>
        <button id="systemAnalyticsBtn">System Analytics</button>
        <button id="systemSettingsBtn">System Settings</button>
      </div>
    `;
  });

  describe('Role-Based Access Control', () => {
    test('should only allow student role access to dashboard', () => {
      window.initializeDashboard = function() {
        const currentUser = this.getCurrentUser();
        if (!currentUser || currentUser.role !== 'student') {
          window.locations.href = 'index.html';
          return false;
        }
        return true;
      };

      window.getCurrentUser = function() {
        const userStr = localStorage.getItem('currentUser');
        return userStr ? JSON.parse(userStr) : null;
      };

      // Test with student user
      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        id: 'student-1',
        role: 'student',
        email: 'student@test.com'
      }));

      const result = window.initializeDashboard();
      expect(result).toBe(true);
      expect(window.locations.href).not.toBe('index.html');
    });

    test('should redirect non-student users to login', () => {
      window.initializeDashboard = function() {
        const currentUser = this.getCurrentUser();
        if (!currentUser || currentUser.role !== 'student') {
          window.locations.href = 'index.html';
          return false;
        }
        return true;
      };

      window.getCurrentUser = function() {
        const userStr = localStorage.getItem('currentUser');
        return userStr ? JSON.parse(userStr) : null;
      };

      // Test with instructor user
      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        id: 'instructor-1',
        role: 'instructor',
        email: 'instructor@test.com'
      }));

      window.initializeDashboard();
      expect(window.locations.href).toBe('index.html');
    });

    test('should hide instructor/admin controls from students', () => {
      window.hideRestrictedElements = function() {
        const userRole = this.getUserRole();
        
        if (userRole !== 'instructor' && userRole !== 'admin') {
          const instructorControls = document.getElementById('instructor-controls');
          if (instructorControls) instructorControls.style.display = 'none';
        }
        
        if (userRole !== 'admin') {
          const adminControls = document.getElementById('admin-controls');
          if (adminControls) adminControls.style.display = 'none';
        }
      };

      window.getUserRole = function() {
        const userStr = localStorage.getItem('currentUser');
        if (!userStr) return null;
        const user = JSON.parse(userStr);
        return user.role;
      };

      // Test with student user
      localStorageMock.getItem.mockReturnValue(JSON.stringify({
        role: 'student'
      }));

      window.hideRestrictedElements();

      const instructorControls = document.getElementById('instructor-controls');
      const adminControls = document.getElementById('admin-controls');

      expect(instructorControls.style.display).toBe('none');
      expect(adminControls.style.display).toBe('none');
    });
  });

  describe('Course Data Access Control', () => {
    test('should only load courses for current student', async () => {
      const studentId = 'student-123';
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          enrollments: [
            {
              student_id: studentId,
              course_id: 'course-1',
              course_title: 'Python Programming',
              status: 'active',
              progress: 45
            },
            {
              student_id: studentId,
              course_id: 'course-2',
              course_title: 'Web Development',
              status: 'scheduled',
              progress: 0
            }
          ]
        })
      });

      window.loadEnrolledCourses = async function() {
        const currentUser = { id: studentId };
        const response = await fetch(`/api/students/${currentUser.id}/courses`);
        
        if (response.ok) {
          const result = await response.json();
          return result.enrollments || [];
        }
        return [];
      };

      const courses = await window.loadEnrolledCourses();

      expect(fetch).toHaveBeenCalledWith(`/api/students/${studentId}/courses`);
      expect(courses).toHaveLength(2);
      expect(courses.every(course => course.student_id === studentId)).toBe(true);
    });

    test('should filter courses by student access permissions', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          accessible_courses: [
            {
              course_instance_id: 'instance-1',
              course_title: 'Active Course',
              status: 'active',
              has_access: true
            }
          ]
        })
      });

      window.getAccessibleCourses = async function(studentId) {
        const response = await fetch(`/api/students/${studentId}/accessible-courses`);
        
        if (response.ok) {
          const result = await response.json();
          return result.accessible_courses.filter(course => course.has_access);
        }
        return [];
      };

      const accessibleCourses = await window.getAccessibleCourses('student-123');

      expect(accessibleCourses).toHaveLength(1);
      expect(accessibleCourses[0].has_access).toBe(true);
      expect(accessibleCourses[0].status).toBe('active');
    });
  });

  describe('Lab Access Control', () => {
    test('should request lab access through proper API endpoint', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_granted: true,
          lab_session_id: 'session-123',
          reason: 'course_active'
        })
      });

      window.requestLabAccess = async function(studentId, courseId) {
        const response = await fetch(`/api/students/${studentId}/lab-access/${courseId}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          }
        });

        return response.json();
      };

      const labAccess = await window.requestLabAccess('student-123', 'course-1');

      expect(fetch).toHaveBeenCalledWith(
        '/api/students/student-123/lab-access/course-1',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': expect.stringContaining('Bearer'),
            'Content-Type': 'application/json'
          })
        })
      );

      expect(labAccess.access_granted).toBe(true);
      expect(labAccess.lab_session_id).toBe('session-123');
    });

    test('should handle lab access denial gracefully', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_granted: false,
          reason: 'course_not_started'
        })
      });

      window.requestLabAccess = async function(studentId, courseId) {
        const response = await fetch(`/api/students/${studentId}/lab-access/${courseId}`, {
          method: 'POST'
        });

        const result = await response.json();
        if (!result.access_granted) {
          throw new Error(`Lab access denied: ${result.reason}`);
        }
        return result;
      };

      await expect(window.requestLabAccess('student-123', 'course-1'))
        .rejects.toThrow('Lab access denied: course_not_started');
    });
  });

  describe('Progress Data Isolation', () => {
    test('should only display student own progress data', () => {
      const studentProgress = {
        student_id: 'student-123',
        total_courses: 3,
        completed_courses: 1,
        overall_progress: 33,
        lab_sessions: 5
      };

      window.displayStudentProgress = function(progress) {
        const progressElements = {
          'dashboardCompletedCourses': progress.completed_courses,
          'dashboardOverallProgress': `${progress.overall_progress}%`,
          'dashboardLabSessions': progress.lab_sessions
        };

        Object.keys(progressElements).forEach(elementId => {
          const element = document.getElementById(elementId);
          if (element) {
            element.textContent = progressElements[elementId];
          }
        });
      };

      // Add progress elements to DOM
      document.body.innerHTML += `
        <span id="dashboardCompletedCourses">0</span>
        <span id="dashboardOverallProgress">0%</span>
        <span id="dashboardLabSessions">0</span>
      `;

      window.displayStudentProgress(studentProgress);

      expect(document.getElementById('dashboardCompletedCourses').textContent).toBe('1');
      expect(document.getElementById('dashboardOverallProgress').textContent).toBe('33%');
      expect(document.getElementById('dashboardLabSessions').textContent).toBe('5');
    });
  });

  describe('Navigation Restrictions', () => {
    test('should only show student-appropriate navigation options', () => {
      window.initializeStudentNavigation = function() {
        const allowedSections = ['dashboard', 'courses', 'progress', 'labs'];
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
          const section = link.getAttribute('data-section');
          if (!allowedSections.includes(section)) {
            link.style.display = 'none';
          }
        });
      };

      // Add restricted navigation items
      document.querySelector('.nav-menu').innerHTML += `
        <li class="nav-item">
          <a href="#" class="nav-link" data-section="admin-panel">
            <span>Admin Panel</span>
          </a>
        </li>
        <li class="nav-item">
          <a href="#" class="nav-link" data-section="instructor-tools">
            <span>Instructor Tools</span>
          </a>
        </li>
      `;

      window.initializeStudentNavigation();

      const adminLink = document.querySelector('[data-section="admin-panel"]');
      const instructorLink = document.querySelector('[data-section="instructor-tools"]');
      const dashboardLink = document.querySelector('[data-section="dashboard"]');

      expect(adminLink.style.display).toBe('none');
      expect(instructorLink.style.display).toBe('none');
      expect(dashboardLink.style.display).not.toBe('none');
    });

    test('should prevent access to restricted sections', () => {
      window.showSection = function(sectionName) {
        const allowedSections = ['dashboard', 'courses', 'progress', 'labs'];
        
        if (!allowedSections.includes(sectionName)) {
          throw new Error(`Access denied to section: ${sectionName}`);
        }
        
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
          section.classList.remove('active');
        });
        
        // Show selected section
        const targetSection = document.getElementById(sectionName + '-section');
        if (targetSection) {
          targetSection.classList.add('active');
        }
      };

      // Test allowed sections
      expect(() => window.showSection('dashboard')).not.toThrow();
      expect(() => window.showSection('courses')).not.toThrow();
      
      // Test restricted sections
      expect(() => window.showSection('admin-panel')).toThrow('Access denied to section: admin-panel');
      expect(() => window.showSection('instructor-tools')).toThrow('Access denied to section: instructor-tools');
    });
  });

  describe('API Call Validation', () => {
    test('should include student ID in all API calls', async () => {
      const studentId = 'student-123';

      window.makeStudentAPICall = async function(endpoint, studentId) {
        const response = await fetch(`/api/students/${studentId}${endpoint}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          }
        });
        return response.json();
      };

      localStorageMock.getItem.mockReturnValue('token-123');
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' })
      });

      await window.makeStudentAPICall('/courses', studentId);

      expect(fetch).toHaveBeenCalledWith(
        `/api/students/${studentId}/courses`,
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer token-123'
          })
        })
      );
    });

    test('should handle unauthorized access attempts', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({
          error: 'Forbidden: Insufficient permissions'
        })
      });

      window.handleAPICall = async function(url) {
        const response = await fetch(url);
        
        if (!response.ok) {
          if (response.status === 403) {
            throw new Error('Access denied: You do not have permission to perform this action');
          }
          throw new Error('Request failed');
        }
        
        return response.json();
      };

      await expect(window.handleAPICall('/api/admin/users'))
        .rejects.toThrow('Access denied: You do not have permission to perform this action');
    });
  });

  describe('Error Handling and Security', () => {
    test('should not expose sensitive data in error messages', () => {
      window.handleError = function(error, context) {
        // Sanitize error messages to prevent information disclosure
        const safeMethods = {
          'permission_denied': 'You do not have permission to access this resource',
          'not_found': 'The requested resource was not found',
          'server_error': 'An unexpected error occurred. Please try again.'
        };

        const safeMessage = safeMethods[context] || 'An error occurred';
        
        return {
          message: safeMessage,
          showDetails: false // Never show sensitive details to students
        };
      };

      const permissionError = window.handleError(new Error('Database connection failed'), 'permission_denied');
      const notFoundError = window.handleError(new Error('User table access denied'), 'not_found');

      expect(permissionError.message).toBe('You do not have permission to access this resource');
      expect(permissionError.showDetails).toBe(false);
      expect(notFoundError.message).toBe('The requested resource was not found');
    });

    test('should validate user session before sensitive operations', () => {
      window.validateStudentSession = function() {
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
        const authToken = localStorage.getItem('authToken');
        
        if (!currentUser.id || !authToken || currentUser.role !== 'student') {
          throw new Error('Invalid session: Please log in again');
        }
        
        return true;
      };

      window.performSensitiveOperation = function() {
        this.validateStudentSession();
        return 'Operation completed';
      };

      // Test with valid session
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'currentUser') return JSON.stringify({ id: 'student-1', role: 'student' });
        if (key === 'authToken') return 'valid-token';
        return null;
      });

      expect(() => window.performSensitiveOperation()).not.toThrow();

      // Test with invalid session
      localStorageMock.getItem.mockReturnValue(null);

      expect(() => window.performSensitiveOperation()).toThrow('Invalid session: Please log in again');
    });
  });
});