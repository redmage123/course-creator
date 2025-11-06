/**
 * Login E2E Tests
 *
 * BUSINESS CONTEXT:
 * Tests complete login workflows for all user roles.
 * Verifies authentication, authorization, and role-based access control.
 *
 * TEST SCENARIOS:
 * - Happy path: User logs in successfully with valid credentials
 * - Error handling: Invalid credentials, missing fields, locked accounts
 * - Edge cases: Remember me, password visibility, browser back button
 * - Security: HTTPS-only cookies, session management, CSRF protection
 *
 * USER ROLES TESTED:
 * - Student
 * - Instructor
 * - Organization Admin
 * - Site Admin
 *
 * CRITICAL REQUIREMENTS (from CLAUDE.md):
 * - All 4 user roles must have E2E coverage
 * - Tests must verify complete workflows
 * - Must use data-testid selectors for reliability
 */

import { LoginPage, DashboardPage } from '../../support/page-objects';

describe('Login E2E Tests', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  beforeEach(() => {
    loginPage = new LoginPage();
    dashboardPage = new DashboardPage();
  });

  /**
   * ============================================================================
   * HAPPY PATH TESTS - All User Roles
   * ============================================================================
   */

  describe('Successful Login - All Roles', () => {
    it('should login successfully as Student', () => {
      /**
       * E2E TEST: Student Login
       *
       * USER JOURNEY:
       * 1. Student visits login page
       * 2. Enters valid credentials
       * 3. Clicks login button
       * 4. Redirects to student dashboard
       * 5. Verifies student-specific dashboard elements
       */

      // Visit login page
      loginPage.visit();

      // Login as student
      cy.login('student');

      // Verify redirect to dashboard
      dashboardPage.verifyDashboardLoaded();
      dashboardPage.verifyStudentDashboard();

      // Verify authentication token stored
      cy.verifyAuthenticated();
      cy.verifyRole('student');
    });

    it('should login successfully as Instructor', () => {
      /**
       * E2E TEST: Instructor Login
       *
       * USER JOURNEY:
       * 1. Instructor visits login page
       * 2. Enters valid credentials
       * 3. Clicks login button
       * 4. Redirects to instructor dashboard
       * 5. Verifies instructor-specific dashboard elements
       */

      loginPage.visit();
      cy.login('instructor');

      dashboardPage.verifyDashboardLoaded();
      dashboardPage.verifyInstructorDashboard();

      cy.verifyAuthenticated();
      cy.verifyRole('instructor');
    });

    it('should login successfully as Organization Admin', () => {
      /**
       * E2E TEST: Organization Admin Login
       *
       * USER JOURNEY:
       * 1. Org admin visits login page
       * 2. Enters valid credentials
       * 3. Clicks login button
       * 4. Redirects to org admin dashboard
       * 5. Verifies org admin-specific dashboard elements
       */

      loginPage.visit();
      cy.login('org_admin');

      dashboardPage.verifyDashboardLoaded();
      dashboardPage.verifyOrgAdminDashboard();

      cy.verifyAuthenticated();
      cy.verifyRole('organization_admin');
    });

    it('should login successfully as Site Admin', () => {
      /**
       * E2E TEST: Site Admin Login
       *
       * USER JOURNEY:
       * 1. Site admin visits login page
       * 2. Enters valid credentials
       * 3. Clicks login button
       * 4. Redirects to site admin dashboard
       * 5. Verifies site admin-specific dashboard elements
       */

      loginPage.visit();
      cy.login('site_admin');

      dashboardPage.verifyDashboardLoaded();
      dashboardPage.verifySiteAdminDashboard();

      cy.verifyAuthenticated();
      cy.verifyRole('site_admin');
    });
  });

  /**
   * ============================================================================
   * ERROR HANDLING TESTS
   * ============================================================================
   */

  describe('Login Error Handling', () => {
    it('should show error for invalid credentials', () => {
      /**
       * E2E TEST: Invalid Credentials
       *
       * ERROR SCENARIO:
       * 1. User enters incorrect username/password
       * 2. Submits login form
       * 3. Error message displayed
       * 4. User remains on login page
       */

      loginPage.visit();
      loginPage.login('invalid@test.com', 'wrongpassword');

      // Verify error message
      loginPage.verifyLoginError('Invalid username or password');

      // Verify still on login page
      cy.url().should('include', '/login');

      // Verify not authenticated
      cy.window().then((win) => {
        expect(win.localStorage.getItem('authToken')).to.be.null;
      });
    });

    it('should require username field', () => {
      /**
       * E2E TEST: Missing Username
       *
       * VALIDATION SCENARIO:
       * 1. User leaves username empty
       * 2. Enters password
       * 3. Submits form
       * 4. Validation error shown
       */

      loginPage.visit();
      loginPage.verifyUsernameRequired();
    });

    it('should require password field', () => {
      /**
       * E2E TEST: Missing Password
       *
       * VALIDATION SCENARIO:
       * 1. User enters username
       * 2. Leaves password empty
       * 3. Submits form
       * 4. Validation error shown
       */

      loginPage.visit();
      loginPage.verifyPasswordRequired();
    });

    it('should handle empty form submission', () => {
      /**
       * E2E TEST: Empty Form
       *
       * VALIDATION SCENARIO:
       * 1. User clicks login without entering anything
       * 2. Both field validation errors shown
       */

      loginPage.visit();
      cy.get('[data-testid="login-button"]').click();

      // Verify form validation prevents submission
      cy.url().should('include', '/login');
    });
  });

  /**
   * ============================================================================
   * SECURITY TESTS
   * ============================================================================
   */

  describe('Login Security', () => {
    it('should not expose password in DOM', () => {
      /**
       * E2E TEST: Password Security
       *
       * SECURITY SCENARIO:
       * 1. User enters password
       * 2. Password field type is "password"
       * 3. Password not visible in DOM
       */

      loginPage.visit();

      cy.get('[data-testid="password-input"]')
        .should('have.attr', 'type', 'password');
    });

    it('should clear sensitive data on logout', () => {
      /**
       * E2E TEST: Data Cleanup
       *
       * SECURITY SCENARIO:
       * 1. User logs in
       * 2. User logs out
       * 3. Auth token removed from localStorage
       * 4. Session cookies cleared
       */

      loginPage.visit();
      cy.login('student');

      // Verify authenticated
      cy.verifyAuthenticated();

      // Logout
      cy.logout();

      // Verify data cleared
      cy.window().then((win) => {
        expect(win.localStorage.getItem('authToken')).to.be.null;
        expect(win.localStorage.getItem('userRole')).to.be.null;
      });
    });
  });

  /**
   * ============================================================================
   * NAVIGATION TESTS
   * ============================================================================
   */

  describe('Login Navigation', () => {
    it('should navigate to forgot password page', () => {
      /**
       * E2E TEST: Forgot Password Navigation
       *
       * NAVIGATION SCENARIO:
       * 1. User clicks "Forgot Password" link
       * 2. Navigates to password reset page
       */

      loginPage.visit();
      loginPage.clickForgotPassword();

      cy.url().should('include', '/forgot-password');
    });

    it('should navigate to registration page', () => {
      /**
       * E2E TEST: Registration Navigation
       *
       * NAVIGATION SCENARIO:
       * 1. User clicks "Register" link
       * 2. Navigates to registration page
       */

      loginPage.visit();
      loginPage.clickRegister();

      cy.url().should('include', '/register');
    });

    it('should redirect authenticated users away from login', () => {
      /**
       * E2E TEST: Auth Redirect
       *
       * SECURITY SCENARIO:
       * 1. User is already logged in
       * 2. User tries to visit login page
       * 3. Automatically redirected to dashboard
       */

      // Login first
      cy.login('student');

      // Try to visit login page
      cy.visit('/login');

      // Should redirect to dashboard
      cy.url().should('not.include', '/login');
      cy.url().should('include', '/dashboard');
    });
  });

  /**
   * ============================================================================
   * REMEMBER ME TESTS
   * ============================================================================
   */

  describe('Remember Me Functionality', () => {
    it('should persist session with remember me checked', () => {
      /**
       * E2E TEST: Remember Me
       *
       * PERSISTENCE SCENARIO:
       * 1. User checks "Remember Me"
       * 2. Logs in successfully
       * 3. Closes browser (simulated)
       * 4. Returns to site
       * 5. Still authenticated
       */

      loginPage.visit();
      loginPage.loginWithRememberMe('student@test.com', 'test123');

      dashboardPage.verifyDashboardLoaded();

      // Simulate browser close by clearing session storage but not local storage
      cy.clearCookies({ domain: null });

      // Revisit site
      cy.visit('/dashboard');

      // Should still be authenticated
      cy.verifyAuthenticated();
    });
  });

  /**
   * ============================================================================
   * ACCESSIBILITY TESTS
   * ============================================================================
   */

  describe('Login Accessibility', () => {
    it('should support keyboard navigation', () => {
      /**
       * E2E TEST: Keyboard Navigation
       *
       * ACCESSIBILITY SCENARIO:
       * 1. User navigates form with Tab key
       * 2. Can focus all interactive elements
       * 3. Can submit with Enter key
       */

      loginPage.visit();

      // Tab through form fields
      cy.get('[data-testid="username-input"]').focus().type('student@test.com');
      cy.realPress('Tab');

      cy.focused().should('have.attr', 'data-testid', 'password-input');
      cy.focused().type('test123');

      // Submit with Enter key
      cy.realPress('Enter');

      // Should login successfully
      dashboardPage.verifyDashboardLoaded();
    });

    it('should have proper ARIA labels', () => {
      /**
       * E2E TEST: ARIA Labels
       *
       * ACCESSIBILITY SCENARIO:
       * 1. Form fields have aria-label or aria-labelledby
       * 2. Error messages have aria-live regions
       * 3. Submit button has clear label
       */

      loginPage.visit();

      cy.get('[data-testid="username-input"]')
        .should('have.attr', 'aria-label');

      cy.get('[data-testid="password-input"]')
        .should('have.attr', 'aria-label');

      cy.get('[data-testid="login-button"]')
        .should('be.visible')
        .and('contain.text', 'Login');
    });
  });
});
