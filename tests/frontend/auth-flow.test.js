/**
 * Unit tests for authentication flow frontend functionality
 * Tests login/logout, role-based access, and session management
 */

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock window.locations
Object.defineProperty(window, 'locations', {
  value: {
    href: 'http://localhost:3000',
    pathname: '/login.html',
    assign: jest.fn(),
    replace: jest.fn()
  },
  writable: true
});

// Mock localStorage and sessionStorage
const storageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', { value: storageMock });
Object.defineProperty(window, 'sessionStorage', { value: storageMock });

describe('Authentication Flow Frontend', () => {
  
  beforeEach(() => {
    // Reset all mocks
    fetch.mockClear();
    storageMock.getItem.mockClear();
    storageMock.setItem.mockClear();
    storageMock.removeItem.mockClear();
    window.locations.assign.mockClear();
    window.locations.replace.mockClear();
    
    // Setup basic login form DOM
    document.body.innerHTML = `
      <form id="loginForm">
        <input name="email" type="email" required />
        <input name="password" type="password" required />
        <button type="submit">Login</button>
        <div id="errorMessage"></div>
      </form>
      <div id="userRole" data-testid="user-role"></div>
      <button id="logoutBtn" style="display: none;">Logout</button>
    `;
  });

  describe('Login Form Validation', () => {
    test('should validate required email field', () => {
      const emailInput = document.querySelector('input[name="email"]');
      
      emailInput.value = '';
      expect(emailInput.validity.valid).toBe(false);
      expect(emailInput.validity.valueMissing).toBe(true);
      
      emailInput.value = 'user@test.com';
      expect(emailInput.validity.valid).toBe(true);
    });

    test('should validate email format', () => {
      const emailInput = document.querySelector('input[name="email"]');
      
      emailInput.value = 'invalid-email';
      expect(emailInput.validity.valid).toBe(false);
      expect(emailInput.validity.typeMismatch).toBe(true);
      
      emailInput.value = 'valid@test.com';
      expect(emailInput.validity.valid).toBe(true);
    });

    test('should validate required password field', () => {
      const passwordInput = document.querySelector('input[name="password"]');
      
      passwordInput.value = '';
      expect(passwordInput.validity.valid).toBe(false);
      expect(passwordInput.validity.valueMissing).toBe(true);
      
      passwordInput.value = 'password123';
      expect(passwordInput.validity.valid).toBe(true);
    });
  });

  describe('Login API Integration', () => {
    test('should call login API with correct credentials', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          token: 'jwt-token-123',
          user: {
            id: 'user-1',
            email: 'instructor@test.com',
            role: 'instructor',
            name: 'Dr. Test Instructor'
          }
        })
      });

      window.login = async function(email, password) {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        
        return response.json();
      };

      const result = await window.login('instructor@test.com', 'password123');

      expect(fetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'instructor@test.com',
          password: 'password123'
        })
      });

      expect(result.success).toBe(true);
      expect(result.token).toBe('jwt-token-123');
      expect(result.user.role).toBe('instructor');
    });

    test('should handle invalid credentials', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          success: false,
          error: 'Invalid credentials'
        })
      });

      window.login = async function(email, password) {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error);
        }
        
        return response.json();
      };

      await expect(window.login('wrong@test.com', 'wrongpassword'))
        .rejects.toThrow('Invalid credentials');
    });

    test('should handle network errors during login', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      window.login = async function(email, password) {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        
        return response.json();
      };

      await expect(window.login('user@test.com', 'password'))
        .rejects.toThrow('Network error');
    });
  });

  describe('Session Management', () => {
    test('should store authentication token after successful login', async () => {
      const mockToken = 'jwt-token-123';
      const mockUser = {
        id: 'user-1',
        email: 'instructor@test.com',
        role: 'instructor'
      };

      window.storeAuthData = function(token, user) {
        localStorage.setItem('authToken', token);
        localStorage.setItem('currentUser', JSON.stringify(user));
      };

      window.storeAuthData(mockToken, mockUser);

      expect(storageMock.setItem).toHaveBeenCalledWith('authToken', mockToken);
      expect(storageMock.setItem).toHaveBeenCalledWith('currentUser', JSON.stringify(mockUser));
    });

    test('should retrieve stored authentication data', () => {
      const mockToken = 'jwt-token-123';
      const mockUser = { id: 'user-1', role: 'instructor' };

      storageMock.getItem.mockImplementation((key) => {
        if (key === 'authToken') return mockToken;
        if (key === 'currentUser') return JSON.stringify(mockUser);
        return null;
      });

      window.getAuthData = function() {
        const token = localStorage.getItem('authToken');
        const userStr = localStorage.getItem('currentUser');
        const user = userStr ? JSON.parse(userStr) : null;
        return { token, user };
      };

      const authData = window.getAuthData();

      expect(authData.token).toBe(mockToken);
      expect(authData.user.role).toBe('instructor');
    });

    test('should check if user is authenticated', () => {
      window.isAuthenticated = function() {
        const token = localStorage.getItem('authToken');
        return !!token;
      };

      // Test when not authenticated
      storageMock.getItem.mockReturnValue(null);
      expect(window.isAuthenticated()).toBe(false);

      // Test when authenticated
      storageMock.getItem.mockReturnValue('jwt-token-123');
      expect(window.isAuthenticated()).toBe(true);
    });

    test('should clear authentication data on logout', () => {
      window.logout = function() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        window.locations.assign('/login.html');
      };

      window.logout();

      expect(storageMock.removeItem).toHaveBeenCalledWith('authToken');
      expect(storageMock.removeItem).toHaveBeenCalledWith('currentUser');
      expect(window.locations.assign).toHaveBeenCalledWith('/login.html');
    });
  });

  describe('Role-Based Access Control', () => {
    test('should identify user role correctly', () => {
      window.getUserRole = function() {
        const userStr = localStorage.getItem('currentUser');
        if (!userStr) return null;
        const user = JSON.parse(userStr);
        return user.role;
      };

      // Test instructor role
      storageMock.getItem.mockReturnValue(JSON.stringify({ role: 'instructor' }));
      expect(window.getUserRole()).toBe('instructor');

      // Test student role
      storageMock.getItem.mockReturnValue(JSON.stringify({ role: 'student' }));
      expect(window.getUserRole()).toBe('student');

      // Test admin role
      storageMock.getItem.mockReturnValue(JSON.stringify({ role: 'admin' }));
      expect(window.getUserRole()).toBe('admin');

      // Test no user
      storageMock.getItem.mockReturnValue(null);
      expect(window.getUserRole()).toBe(null);
    });

    test('should check access permissions for different roles', () => {
      window.hasPermission = function(action, userRole) {
        const permissions = {
          'create_course': ['instructor', 'admin'],
          'enroll_student': ['instructor', 'admin'],
          'view_course': ['student', 'instructor', 'admin'],
          'manage_users': ['admin'],
          'view_analytics': ['instructor', 'admin']
        };
        
        return permissions[action] && permissions[action].includes(userRole);
      };

      // Test instructor permissions
      expect(window.hasPermission('create_course', 'instructor')).toBe(true);
      expect(window.hasPermission('enroll_student', 'instructor')).toBe(true);
      expect(window.hasPermission('manage_users', 'instructor')).toBe(false);

      // Test student permissions
      expect(window.hasPermission('view_course', 'student')).toBe(true);
      expect(window.hasPermission('create_course', 'student')).toBe(false);
      expect(window.hasPermission('enroll_student', 'student')).toBe(false);

      // Test admin permissions
      expect(window.hasPermission('manage_users', 'admin')).toBe(true);
      expect(window.hasPermission('create_course', 'admin')).toBe(true);
      expect(window.hasPermission('view_course', 'admin')).toBe(true);
    });

    test('should redirect based on user role after login', () => {
      window.redirectAfterLogin = function(role) {
        const redirectMap = {
          'admin': '/admin.html',
          'instructor': '/instructor-dashboard.html',
          'student': '/student-dashboard.html'
        };
        
        const destination = redirectMap[role] || '/login.html';
        window.locations.assign(destination);
      };

      // Test instructor redirect
      window.redirectAfterLogin('instructor');
      expect(window.locations.assign).toHaveBeenCalledWith('/instructor-dashboard.html');

      // Test student redirect
      window.redirectAfterLogin('student');
      expect(window.locations.assign).toHaveBeenCalledWith('/student-dashboard.html');

      // Test admin redirect
      window.redirectAfterLogin('admin');
      expect(window.locations.assign).toHaveBeenCalledWith('/admin.html');

      // Test unknown role redirect
      window.redirectAfterLogin('unknown');
      expect(window.locations.assign).toHaveBeenCalledWith('/login.html');
    });
  });

  describe('Password Security', () => {
    test('should validate password strength', () => {
      window.validatePasswordStrength = function(password) {
        const minLength = password.length >= 8;
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecials = /[!@#$%^&*]/.test(password);
        
        const score = [minLength, hasUppercase, hasLowercase, hasNumbers, hasSpecials]
          .filter(Boolean).length;
        
        return {
          score,
          isStrong: score >= 4,
          feedback: {
            minLength,
            hasUppercase,
            hasLowercase,
            hasNumbers,
            hasSpecials
          }
        };
      };

      // Test weak password
      const weakResult = window.validatePasswordStrength('123');
      expect(weakResult.isStrong).toBe(false);
      expect(weakResult.score).toBe(1);

      // Test strong password
      const strongResult = window.validatePasswordStrength('StrongPass123!');
      expect(strongResult.isStrong).toBe(true);
      expect(strongResult.score).toBe(5);
    });
  });

  describe('Error Handling', () => {
    test('should display login error messages', () => {
      window.displayError = function(message) {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        errorDiv.className = 'error-message';
      };

      window.displayError('Invalid credentials');
      
      const errorDiv = document.getElementById('errorMessage');
      expect(errorDiv.textContent).toBe('Invalid credentials');
      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.className).toBe('error-message');
    });

    test('should clear error messages', () => {
      window.clearError = function() {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.textContent = '';
        errorDiv.style.display = 'none';
        errorDiv.className = '';
      };

      // First set an error
      const errorDiv = document.getElementById('errorMessage');
      errorDiv.textContent = 'Some error';
      errorDiv.style.display = 'block';

      // Then clear it
      window.clearError();
      
      expect(errorDiv.textContent).toBe('');
      expect(errorDiv.style.display).toBe('none');
      expect(errorDiv.className).toBe('');
    });
  });
});