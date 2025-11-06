/**
 * Login Page Object Model
 *
 * BUSINESS CONTEXT:
 * Encapsulates login page interactions for authentication testing.
 * Provides methods for login workflows across all user roles.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Extends BasePage for common functionality
 * - Provides login-specific methods
 * - Handles authentication verification
 *
 * USAGE:
 * const loginPage = new LoginPage();
 * loginPage.visit();
 * loginPage.login('instructor@test.com', 'test123');
 * loginPage.verifyLoginSuccess();
 */

import { BasePage } from './BasePage';

export class LoginPage extends BasePage {
  // URL
  private url = '/login';

  // Selectors
  private selectors = {
    form: 'login-form',
    usernameInput: 'username-input',
    passwordInput: 'password-input',
    loginButton: 'login-button',
    forgotPasswordLink: 'forgot-password-link',
    registerLink: 'register-link',
    errorMessage: 'error-message',
    rememberMeCheckbox: 'remember-me-checkbox',
  };

  /**
   * Visit Login Page
   *
   * NAVIGATES: To login page
   */
  visit(): void {
    super.visit(this.url);
    this.verifyPageLoaded();
  }

  /**
   * Verify Page Loaded
   *
   * VERIFIES: Login page is fully loaded
   */
  verifyPageLoaded(): void {
    this.verifyVisible(this.selectors.form);
    this.verifyVisible(this.selectors.usernameInput);
    this.verifyVisible(this.selectors.passwordInput);
    this.verifyVisible(this.selectors.loginButton);
  }

  /**
   * Login
   *
   * PERFORMS: Login action with credentials
   */
  login(username: string, password: string): void {
    this.fillInput(this.selectors.usernameInput, username);
    this.fillInput(this.selectors.passwordInput, password);
    this.clickButton(this.selectors.loginButton);
  }

  /**
   * Login with Remember Me
   *
   * PERFORMS: Login with "Remember Me" checked
   */
  loginWithRememberMe(username: string, password: string): void {
    this.fillInput(this.selectors.usernameInput, username);
    this.fillInput(this.selectors.passwordInput, password);
    this.clickButton(this.selectors.rememberMeCheckbox);
    this.clickButton(this.selectors.loginButton);
  }

  /**
   * Verify Login Success
   *
   * VERIFIES: User successfully logged in (redirected away from login)
   */
  verifyLoginSuccess(): void {
    cy.url().should('not.include', this.url);
    cy.url().should('include', '/dashboard');
  }

  /**
   * Verify Login Error
   *
   * VERIFIES: Login error message displayed
   */
  verifyLoginError(errorText: string): void {
    this.verifyVisible(this.selectors.errorMessage);
    this.verifyText(this.selectors.errorMessage, errorText);
  }

  /**
   * Click Forgot Password
   *
   * CLICKS: Forgot password link
   */
  clickForgotPassword(): void {
    this.clickButton(this.selectors.forgotPasswordLink);
  }

  /**
   * Click Register
   *
   * CLICKS: Register link
   */
  clickRegister(): void {
    this.clickButton(this.selectors.registerLink);
  }

  /**
   * Verify Username Field Required
   *
   * VERIFIES: Username field shows required error
   */
  verifyUsernameRequired(): void {
    this.clickButton(this.selectors.loginButton);
    cy.get(`[data-testid="${this.selectors.usernameInput}"]`)
      .should('have.attr', 'required');
  }

  /**
   * Verify Password Field Required
   *
   * VERIFIES: Password field shows required error
   */
  verifyPasswordRequired(): void {
    this.fillInput(this.selectors.usernameInput, 'test@test.com');
    this.clickButton(this.selectors.loginButton);
    cy.get(`[data-testid="${this.selectors.passwordInput}"]`)
      .should('have.attr', 'required');
  }
}
