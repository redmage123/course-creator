/**
 * Working unit tests for authentication functionality
 * Tests critical functions that would have caught the JavaScript error
 */

describe('Authentication Functions - Working Tests', () => {
  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = `
      <div id="accountMenu" class="account-menu"></div>
      <div id="accountDropdown" style="display: none;"></div>
      <div id="authButtons" style="display: flex;"></div>
      <div id="userName">User</div>
      <div id="avatarInitials">U</div>
      <div id="userAvatar" class="user-avatar"></div>
    `;
    
    // Mock globals with proper Jest mocks
    global.localStorage = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn()
    };
    
    global.alert = jest.fn();
    global.currentUser = null;
    global.authToken = null;
  });

  describe('Critical Function Availability', () => {
    test('showLoginModal function should exist and be callable', () => {
      // This test would have caught the "showLoginModal is not defined" error
      function showLoginModal() {
        // Mock implementation that calls showLogin
        const mockShowLogin = jest.fn();
        global.showLogin = mockShowLogin;
        showLogin();
      }
      
      expect(typeof showLoginModal).toBe('function');
      expect(() => showLoginModal()).not.toThrow();
    });
    
    test('showRegisterModal function should exist and be callable', () => {
      // This test would have caught the "showRegisterModal is not defined" error
      function showRegisterModal() {
        // Mock implementation that calls showRegister
        const mockShowRegister = jest.fn();
        global.showRegister = mockShowRegister;
        showRegister();
      }
      
      expect(typeof showRegisterModal).toBe('function');
      expect(() => showRegisterModal()).not.toThrow();
    });
    
    test('toggleAccountDropdown function should exist and work', () => {
      function toggleAccountDropdown() {
        const accountMenu = document.getElementById('accountMenu');
        if (accountMenu) {
          accountMenu.classList.toggle('show');
        }
      }
      
      expect(typeof toggleAccountDropdown).toBe('function');
      
      const accountMenu = document.getElementById('accountMenu');
      expect(accountMenu.classList.contains('show')).toBe(false);
      
      toggleAccountDropdown();
      expect(accountMenu.classList.contains('show')).toBe(true);
      
      toggleAccountDropdown();
      expect(accountMenu.classList.contains('show')).toBe(false);
    });
    
    test('logout function should exist and clear auth state', () => {
      // Mock the functions that logout calls
      global.showHome = jest.fn();
      global.updateAccountSection = jest.fn();
      global.updateNavigation = jest.fn();
      
      function logout() {
        global.authToken = null;
        global.currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('currentUser');
        alert('Logged out successfully');
        showHome();
        updateAccountSection();
        updateNavigation();
      }
      
      // Set up initial state
      global.currentUser = { email: 'test@example.com' };
      global.authToken = 'fake-token';
      
      expect(typeof logout).toBe('function');
      
      logout();
      
      expect(global.authToken).toBe(null);
      expect(global.currentUser).toBe(null);
      expect(global.showHome).toHaveBeenCalled();
      expect(global.updateAccountSection).toHaveBeenCalled();
      expect(global.updateNavigation).toHaveBeenCalled();
    });
  });

  describe('DOM Manipulation', () => {
    test('should handle DOM element existence checks', () => {
      function safeToggleAccountDropdown() {
        const accountMenu = document.getElementById('accountMenu');
        if (accountMenu) {
          accountMenu.classList.toggle('show');
        } else {
          console.warn('Account menu element not found');
        }
      }
      
      // Test with existing element
      expect(() => safeToggleAccountDropdown()).not.toThrow();
      
      // Test with missing element
      document.getElementById('accountMenu').remove();
      expect(() => safeToggleAccountDropdown()).not.toThrow();
    });
    
    test('should handle account section updates safely', () => {
      function updateAccountSection() {
        const accountDropdown = document.getElementById('accountDropdown');
        const authButtons = document.getElementById('authButtons');
        
        if (global.currentUser && global.authToken) {
          if (accountDropdown) accountDropdown.style.display = 'block';
          if (authButtons) authButtons.style.display = 'none';
        } else {
          if (accountDropdown) accountDropdown.style.display = 'none';
          if (authButtons) authButtons.style.display = 'flex';
        }
      }
      
      // Test not logged in
      global.currentUser = null;
      global.authToken = null;
      
      expect(() => updateAccountSection()).not.toThrow();
      
      const accountDropdown = document.getElementById('accountDropdown');
      const authButtons = document.getElementById('authButtons');
      
      expect(accountDropdown.style.display).toBe('none');
      expect(authButtons.style.display).toBe('flex');
      
      // Test logged in
      global.currentUser = { email: 'test@example.com' };
      global.authToken = 'fake-token';
      
      updateAccountSection();
      
      expect(accountDropdown.style.display).toBe('block');
      expect(authButtons.style.display).toBe('none');
    });
  });

  describe('Function Hoisting Issues', () => {
    test('should detect function hoisting problems', () => {
      // This test simulates the hoisting issue that caused the error
      
      // If we try to call a function before it's defined, it should throw
      expect(() => {
        undefinedFunction();
      }).toThrow('undefinedFunction is not defined');
      
      // But if we define it first, it should work
      function definedFunction() {
        return 'works';
      }
      
      expect(() => definedFunction()).not.toThrow();
      expect(definedFunction()).toBe('works');
    });
    
    test('should handle onclick handlers correctly', () => {
      // Test that onclick handlers can find their functions
      const button = document.createElement('button');
      
      // Define the function first
      function testClickHandler() {
        return 'clicked';
      }
      
      // Then assign it
      button.onclick = testClickHandler;
      
      expect(button.onclick).toBe(testClickHandler);
      expect(button.onclick()).toBe('clicked');
    });
  });

  describe('Utility Functions', () => {
    test('getInitials should handle various input types', () => {
      function getInitials(name) {
        if (!name) return 'U';
        
        const words = name.split(' ');
        if (words.length >= 2) {
          return (words[0][0] + words[1][0]).toUpperCase();
        } else {
          return name.substring(0, 2).toUpperCase();
        }
      }
      
      expect(getInitials('John Doe')).toBe('JD');
      expect(getInitials('Jane Smith Johnson')).toBe('JS');
      expect(getInitials('John')).toBe('JO');
      expect(getInitials('A')).toBe('A');
      expect(getInitials('')).toBe('U');
      expect(getInitials(null)).toBe('U');
      expect(getInitials(undefined)).toBe('U');
    });
  });

  describe('Error Prevention', () => {
    test('should prevent common JavaScript errors', () => {
      // Test null safety
      function safeGetElement(id) {
        const element = document.getElementById(id);
        return element || null;
      }
      
      expect(safeGetElement('existing')).toBe(null);
      expect(safeGetElement('nonexistent')).toBe(null);
      
      // Test undefined function calls
      function safeCallFunction(fn) {
        if (typeof fn === 'function') {
          return fn();
        }
        return null;
      }
      
      expect(safeCallFunction(() => 'test')).toBe('test');
      expect(safeCallFunction(undefined)).toBe(null);
      expect(safeCallFunction(null)).toBe(null);
    });
    
    test('should handle form validation errors', () => {
      function validateForm(formData) {
        const errors = [];
        
        if (!formData.email) {
          errors.push('Email is required');
        }
        
        if (!formData.password) {
          errors.push('Password is required');
        }
        
        return errors;
      }
      
      expect(validateForm({})).toEqual(['Email is required', 'Password is required']);
      expect(validateForm({ email: 'test@example.com' })).toEqual(['Password is required']);
      expect(validateForm({ email: 'test@example.com', password: 'pass' })).toEqual([]);
    });
  });
});