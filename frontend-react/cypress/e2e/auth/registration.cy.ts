/**
 * Registration E2E Tests
 *
 * BUSINESS CONTEXT:
 * Tests user registration workflows for new accounts.
 * Verifies account creation, validation, and initial setup.
 *
 * TEST SCENARIOS:
 * - Happy path: New user registers successfully
 * - Validation: Email format, password strength, required fields
 * - Error handling: Duplicate accounts, invalid data
 * - Organization creation: Optional organization setup during registration
 *
 * CRITICAL REQUIREMENTS:
 * - GDPR compliance for guest sessions
 * - Email verification workflow
 * - Password strength requirements
 */

import { LoginPage } from '../../support/page-objects';

describe('Registration E2E Tests', () => {
  beforeEach(() => {
    cy.visit('/register');
  });

  describe('Successful Registration', () => {
    it('should register new student account', () => {
      /**
       * E2E TEST: Student Registration
       *
       * USER JOURNEY:
       * 1. User visits registration page
       * 2. Fills in personal information
       * 3. Selects student role
       * 4. Submits registration
       * 5. Receives confirmation
       * 6. Redirects to dashboard or email verification
       */

      const userData = {
        username: `student_${Date.now()}`,
        email: `student${Date.now()}@test.com`,
        password: 'SecurePass123!',
        firstName: 'Test',
        lastName: 'Student',
      };

      cy.register(userData);

      // Verify redirect or confirmation
      cy.url().should('not.include', '/register');
      cy.verifyToastMessage('Registration successful');
    });

    it('should register new instructor with organization', () => {
      /**
       * E2E TEST: Instructor Registration with Org
       *
       * USER JOURNEY:
       * 1. User selects instructor role
       * 2. Creates new organization
       * 3. Becomes org admin of new organization
       */

      const userData = {
        username: `instructor_${Date.now()}`,
        email: `instructor${Date.now()}@test.com`,
        password: 'SecurePass123!',
        firstName: 'Test',
        lastName: 'Instructor',
        organizationName: `Test Org ${Date.now()}`,
      };

      cy.register(userData);

      cy.url().should('not.include', '/register');
      cy.verifyToastMessage('Registration successful');
    });
  });

  describe('Validation Tests', () => {
    it('should validate email format', () => {
      /**
       * E2E TEST: Email Validation
       *
       * VALIDATION: Email must be valid format
       */

      cy.get('[data-testid="email-input"]').type('invalid-email');
      cy.get('[data-testid="register-button"]').click();

      cy.get('[data-testid="email-input"]')
        .should('have.attr', 'type', 'email');
    });

    it('should validate password strength', () => {
      /**
       * E2E TEST: Password Strength
       *
       * VALIDATION: Password must meet strength requirements
       */

      cy.get('[data-testid="password-input"]').type('weak');
      cy.get('[data-testid="password-strength-indicator"]')
        .should('contain', 'Weak');

      cy.get('[data-testid="password-input"]').clear().type('StrongPass123!');
      cy.get('[data-testid="password-strength-indicator"]')
        .should('contain', 'Strong');
    });

    it('should validate password confirmation match', () => {
      /**
       * E2E TEST: Password Confirmation
       *
       * VALIDATION: Passwords must match
       */

      cy.get('[data-testid="password-input"]').type('Password123!');
      cy.get('[data-testid="confirm-password-input"]').type('DifferentPass123!');
      cy.get('[data-testid="register-button"]').click();

      cy.get('[data-testid="error-message"]')
        .should('contain', 'Passwords do not match');
    });

    it('should require all mandatory fields', () => {
      /**
       * E2E TEST: Required Fields
       *
       * VALIDATION: All required fields must be filled
       */

      cy.get('[data-testid="register-button"]').click();

      // Verify required field indicators
      cy.get('[data-testid="username-input"]').should('have.attr', 'required');
      cy.get('[data-testid="email-input"]').should('have.attr', 'required');
      cy.get('[data-testid="password-input"]').should('have.attr', 'required');
    });
  });

  describe('Error Handling', () => {
    it('should handle duplicate email registration', () => {
      /**
       * E2E TEST: Duplicate Email
       *
       * ERROR SCENARIO: Email already registered
       */

      const userData = {
        username: 'duplicate_user',
        email: 'student@test.com', // Existing email
        password: 'Password123!',
        firstName: 'Test',
        lastName: 'User',
      };

      cy.register(userData);

      cy.get('[data-testid="error-message"]')
        .should('contain', 'Email already registered');
    });

    it('should handle network errors gracefully', () => {
      /**
       * E2E TEST: Network Error Handling
       *
       * ERROR SCENARIO: Registration API fails
       */

      // Intercept registration API
      cy.intercept('POST', '**/api/v1/auth/register', {
        statusCode: 500,
        body: { error: 'Internal server error' },
      });

      const userData = {
        username: 'test_user',
        email: 'test@test.com',
        password: 'Password123!',
        firstName: 'Test',
        lastName: 'User',
      };

      cy.register(userData);

      cy.get('[data-testid="error-message"]')
        .should('contain', 'Registration failed');
    });
  });

  describe('Privacy Compliance', () => {
    it('should display privacy policy checkbox', () => {
      /**
       * E2E TEST: Privacy Policy Consent
       *
       * COMPLIANCE: GDPR/CCPA requires explicit consent
       */

      cy.get('[data-testid="privacy-policy-checkbox"]')
        .should('exist')
        .and('not.be.checked');

      cy.get('[data-testid="privacy-policy-link"]')
        .should('have.attr', 'href', '/privacy-policy');
    });

    it('should require privacy policy acceptance', () => {
      /**
       * E2E TEST: Privacy Policy Required
       *
       * COMPLIANCE: Cannot register without accepting policy
       */

      const userData = {
        username: 'test_user',
        email: 'test@test.com',
        password: 'Password123!',
        firstName: 'Test',
        lastName: 'User',
      };

      cy.fillForm({
        'username-input': userData.username,
        'email-input': userData.email,
        'password-input': userData.password,
        'confirm-password-input': userData.password,
        'first-name-input': userData.firstName,
        'last-name-input': userData.lastName,
      });

      // Try to submit without accepting privacy policy
      cy.get('[data-testid="register-button"]').click();

      cy.get('[data-testid="error-message"]')
        .should('contain', 'You must accept the privacy policy');
    });
  });
});
