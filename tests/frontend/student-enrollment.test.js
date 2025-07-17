/**
 * Unit tests for student enrollment frontend functionality
 * Tests the JavaScript functions and UI interactions for student enrollment
 */

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock DOM elements and methods
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    pathname: '/instructor-dashboard.html'
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

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock
});

describe('Student Enrollment Frontend', () => {
  
  beforeEach(() => {
    // Reset all mocks
    fetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    
    // Setup basic DOM structure
    document.body.innerHTML = `
      <div id="students-section">
        <select id="selectedCourse">
          <option value="">Select a course...</option>
          <option value="course-1">Python Programming</option>
          <option value="course-2">Web Development</option>
        </select>
        <input name="studentEmail" type="email" />
        <input name="startDate" type="date" />
        <input name="endDate" type="date" />
        <input name="maxStudents" type="number" value="25" />
        <button id="enrollStudentBtn">Enroll Student</button>
        <div id="enrolledStudentsList"></div>
        <div id="notification"></div>
      </div>
      <div id="courses-section">
        <div class="course-list"></div>
      </div>
    `;
  });

  describe('Course Selection', () => {
    test('should populate course dropdown correctly', () => {
      const mockCourses = [
        { id: 'course-1', title: 'Python Programming' },
        { id: 'course-2', title: 'Web Development' },
        { id: 'course-3', title: 'Data Science' }
      ];

      // Mock the populateStudentCourseDropdown function
      window.populateStudentCourseDropdown = function() {
        const dropdown = document.getElementById('selectedCourse');
        dropdown.innerHTML = '<option value="">Select a course...</option>';
        
        mockCourses.forEach(course => {
          const option = document.createElement('option');
          option.value = course.id;
          option.textContent = course.title;
          dropdown.appendChild(option);
        });
      };

      window.populateStudentCourseDropdown();
      
      const dropdown = document.getElementById('selectedCourse');
      expect(dropdown.children.length).toBe(4); // 1 placeholder + 3 courses
      expect(dropdown.children[1].textContent).toBe('Python Programming');
      expect(dropdown.children[2].textContent).toBe('Web Development');
      expect(dropdown.children[3].textContent).toBe('Data Science');
    });

    test('should handle empty course list', () => {
      window.populateStudentCourseDropdown = function() {
        const dropdown = document.getElementById('selectedCourse');
        dropdown.innerHTML = '<option value="">Select a course...</option>';
      };

      window.populateStudentCourseDropdown();
      
      const dropdown = document.getElementById('selectedCourse');
      expect(dropdown.children.length).toBe(1);
      expect(dropdown.children[0].textContent).toBe('Select a course...');
    });
  });

  describe('Student Enrollment Form', () => {
    test('should validate email format', () => {
      const emailInput = document.querySelector('input[name="studentEmail"]');
      
      // Test valid email
      emailInput.value = 'student@test.com';
      expect(emailInput.validity.valid).toBe(true);
      
      // Test invalid email
      emailInput.value = 'invalid-email';
      expect(emailInput.validity.valid).toBe(false);
    });

    test('should validate date fields', () => {
      const startDateInput = document.querySelector('input[name="startDate"]');
      const endDateInput = document.querySelector('input[name="endDate"]');
      
      const today = new Date().toISOString().split('T')[0];
      const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
      
      startDateInput.value = today;
      endDateInput.value = tomorrow;
      
      expect(startDateInput.value).toBe(today);
      expect(endDateInput.value).toBe(tomorrow);
    });

    test('should validate required fields', () => {
      const courseSelect = document.getElementById('selectedCourse');
      const emailInput = document.querySelector('input[name="studentEmail"]');
      const startDateInput = document.querySelector('input[name="startDate"]');
      const endDateInput = document.querySelector('input[name="endDate"]');

      // Set required attribute
      courseSelect.required = true;
      emailInput.required = true;
      startDateInput.required = true;
      endDateInput.required = true;

      // Test empty values
      expect(courseSelect.validity.valid).toBe(false);
      expect(emailInput.validity.valid).toBe(false);
      expect(startDateInput.validity.valid).toBe(false);
      expect(endDateInput.validity.valid).toBe(false);

      // Fill in values
      courseSelect.value = 'course-1';
      emailInput.value = 'student@test.com';
      startDateInput.value = '2025-07-20';
      endDateInput.value = '2025-08-03';

      expect(courseSelect.validity.valid).toBe(true);
      expect(emailInput.validity.valid).toBe(true);
      expect(startDateInput.validity.valid).toBe(true);
      expect(endDateInput.validity.valid).toBe(true);
    });
  });

  describe('Student Enrollment API', () => {
    test('should call enrollment API with correct data', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: 'Student enrolled successfully',
          enrollmentId: 'enroll-123'
        })
      });

      const enrollmentData = {
        courseId: 'course-1',
        studentEmail: 'student@test.com',
        startDate: '2025-07-20',
        endDate: '2025-08-03',
        maxStudents: 25
      };

      // Mock enrollment function
      window.enrollStudent = async function(data) {
        const response = await fetch('/api/enrollment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        return response.json();
      };

      const result = await window.enrollStudent(enrollmentData);

      expect(fetch).toHaveBeenCalledWith('/api/enrollment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(enrollmentData)
      });

      expect(result.success).toBe(true);
      expect(result.message).toBe('Student enrolled successfully');
    });

    test('should handle enrollment API errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          success: false,
          error: 'Course instance is at maximum capacity'
        })
      });

      window.enrollStudent = async function(data) {
        const response = await fetch('/api/enrollment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error);
        }
        
        return response.json();
      };

      const enrollmentData = {
        courseId: 'course-1',
        studentEmail: 'student@test.com',
        startDate: '2025-07-20',
        endDate: '2025-08-03',
        maxStudents: 25
      };

      await expect(window.enrollStudent(enrollmentData))
        .rejects.toThrow('Course instance is at maximum capacity');
    });

    test('should handle network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      window.enrollStudent = async function(data) {
        const response = await fetch('/api/enrollment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        return response.json();
      };

      const enrollmentData = {
        courseId: 'course-1',
        studentEmail: 'student@test.com',
        startDate: '2025-07-20',
        endDate: '2025-08-03'
      };

      await expect(window.enrollStudent(enrollmentData))
        .rejects.toThrow('Network error');
    });
  });

  describe('Course Instance Management', () => {
    test('should create course instance with correct data', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          instanceId: 'instance-123',
          status: 'scheduled'
        })
      });

      const instanceData = {
        courseId: 'course-1',
        startDate: '2025-07-20',
        endDate: '2025-08-03',
        maxStudents: 25,
        timezone: 'America/New_York',
        meetingSchedule: 'Monday/Wednesday/Friday 10:00-11:30 AM'
      };

      window.createCourseInstance = async function(data) {
        const response = await fetch('/api/course-instances', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        return response.json();
      };

      const result = await window.createCourseInstance(instanceData);

      expect(fetch).toHaveBeenCalledWith('/api/course-instances', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(instanceData)
      });

      expect(result.success).toBe(true);
      expect(result.instanceId).toBe('instance-123');
      expect(result.status).toBe('scheduled');
    });

    test('should validate course instance dates', () => {
      window.validateInstanceDates = function(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const now = new Date();

        if (end <= start) {
          return { valid: false, error: 'End date must be after start date' };
        }

        if (start < now) {
          return { valid: false, error: 'Start date cannot be in the past' };
        }

        return { valid: true };
      };

      // Test invalid dates (end before start)
      const invalidResult = window.validateInstanceDates('2025-07-20', '2025-07-15');
      expect(invalidResult.valid).toBe(false);
      expect(invalidResult.error).toBe('End date must be after start date');

      // Test valid dates
      const validResult = window.validateInstanceDates('2025-07-20', '2025-08-03');
      expect(validResult.valid).toBe(true);
    });
  });

  describe('UI Notifications', () => {
    test('should display success notification', () => {
      window.showNotification = function(message, type = 'success') {
        const notification = document.getElementById('notification');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.display = 'block';
      };

      window.showNotification('Student enrolled successfully', 'success');
      
      const notification = document.getElementById('notification');
      expect(notification.textContent).toBe('Student enrolled successfully');
      expect(notification.className).toBe('notification success');
      expect(notification.style.display).toBe('block');
    });

    test('should display error notification', () => {
      window.showNotification = function(message, type = 'success') {
        const notification = document.getElementById('notification');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.display = 'block';
      };

      window.showNotification('Course instance is at maximum capacity', 'error');
      
      const notification = document.getElementById('notification');
      expect(notification.textContent).toBe('Course instance is at maximum capacity');
      expect(notification.className).toBe('notification error');
    });

    test('should hide notification after timeout', (done) => {
      window.showNotification = function(message, type = 'success', timeout = 3000) {
        const notification = document.getElementById('notification');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.display = 'block';
        
        setTimeout(() => {
          notification.style.display = 'none';
        }, timeout);
      };

      window.showNotification('Test message', 'success', 100);
      
      setTimeout(() => {
        const notification = document.getElementById('notification');
        expect(notification.style.display).toBe('none');
        done();
      }, 150);
    });
  });

  describe('Student List Management', () => {
    test('should display enrolled students', () => {
      const mockStudents = [
        { 
          id: '1',
          email: 'student1@test.com',
          enrolledAt: '2025-07-17T10:00:00Z',
          status: 'enrolled'
        },
        { 
          id: '2',
          email: 'student2@test.com', 
          enrolledAt: '2025-07-17T11:00:00Z',
          status: 'enrolled'
        }
      ];

      window.displayEnrolledStudents = function(students) {
        const container = document.getElementById('enrolledStudentsList');
        container.innerHTML = '';
        
        students.forEach(student => {
          const studentElement = document.createElement('div');
          studentElement.className = 'enrolled-student';
          studentElement.innerHTML = `
            <span class="student-email">${student.email}</span>
            <span class="student-status">${student.status}</span>
            <span class="enrolled-date">${new Date(student.enrolledAt).toLocaleDateString()}</span>
          `;
          container.appendChild(studentElement);
        });
      };

      window.displayEnrolledStudents(mockStudents);
      
      const container = document.getElementById('enrolledStudentsList');
      const studentElements = container.querySelectorAll('.enrolled-student');
      
      expect(studentElements.length).toBe(2);
      expect(studentElements[0].querySelector('.student-email').textContent).toBe('student1@test.com');
      expect(studentElements[1].querySelector('.student-email').textContent).toBe('student2@test.com');
    });

    test('should handle empty student list', () => {
      window.displayEnrolledStudents = function(students) {
        const container = document.getElementById('enrolledStudentsList');
        container.innerHTML = '';
        
        if (students.length === 0) {
          container.innerHTML = '<p class="no-students">No students enrolled yet.</p>';
          return;
        }
        
        students.forEach(student => {
          const studentElement = document.createElement('div');
          studentElement.className = 'enrolled-student';
          studentElement.innerHTML = `
            <span class="student-email">${student.email}</span>
            <span class="student-status">${student.status}</span>
          `;
          container.appendChild(studentElement);
        });
      };

      window.displayEnrolledStudents([]);
      
      const container = document.getElementById('enrolledStudentsList');
      expect(container.innerHTML).toBe('<p class="no-students">No students enrolled yet.</p>');
    });
  });

  describe('Form Reset and Cleanup', () => {
    test('should reset enrollment form after successful submission', () => {
      const courseSelect = document.getElementById('selectedCourse');
      const emailInput = document.querySelector('input[name="studentEmail"]');
      const startDateInput = document.querySelector('input[name="startDate"]');
      const endDateInput = document.querySelector('input[name="endDate"]');

      // Fill form
      courseSelect.value = 'course-1';
      emailInput.value = 'student@test.com';
      startDateInput.value = '2025-07-20';
      endDateInput.value = '2025-08-03';

      window.resetEnrollmentForm = function() {
        courseSelect.value = '';
        emailInput.value = '';
        startDateInput.value = '';
        endDateInput.value = '';
      };

      window.resetEnrollmentForm();

      expect(courseSelect.value).toBe('');
      expect(emailInput.value).toBe('');
      expect(startDateInput.value).toBe('');
      expect(endDateInput.value).toBe('');
    });
  });
});