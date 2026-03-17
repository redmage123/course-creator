/**
 * Base Page Object Model
 *
 * BUSINESS CONTEXT:
 * Provides common functionality for all page objects.
 * Implements reusable navigation, verification, and interaction patterns.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Parent class for all page objects
 * - Provides common selectors and methods
 * - Implements DRY principle for page object testing
 *
 * USAGE:
 * Extend this class for specific page objects:
 * class LoginPage extends BasePage { ... }
 */

export class BasePage {
  /**
   * Visit Page
   *
   * NAVIGATES: To specified URL
   */
  visit(url: string): void {
    cy.visit(url);
  }

  /**
   * Verify URL
   *
   * VERIFIES: Current URL matches expected pattern
   */
  verifyUrl(urlPattern: string): void {
    cy.url().should('include', urlPattern);
  }

  /**
   * Verify Page Title
   *
   * VERIFIES: Page title matches expected text
   */
  verifyPageTitle(title: string): void {
    cy.get('[data-testid="page-title"]').should('contain', title);
  }

  /**
   * Click Button
   *
   * CLICKS: Button by data-testid
   */
  clickButton(testId: string): void {
    cy.get(`[data-testid="${testId}"]`).click();
  }

  /**
   * Fill Input
   *
   * FILLS: Input field by data-testid
   */
  fillInput(testId: string, value: string): void {
    cy.get(`[data-testid="${testId}"]`).clear().type(value);
  }

  /**
   * Select Option
   *
   * SELECTS: Dropdown option by data-testid
   */
  selectOption(testId: string, value: string): void {
    cy.get(`[data-testid="${testId}"]`).select(value);
  }

  /**
   * Verify Element Visible
   *
   * VERIFIES: Element is visible
   */
  verifyVisible(testId: string): void {
    cy.get(`[data-testid="${testId}"]`).should('be.visible');
  }

  /**
   * Verify Element Not Visible
   *
   * VERIFIES: Element is not visible or does not exist
   */
  verifyNotVisible(testId: string): void {
    cy.get(`[data-testid="${testId}"]`).should('not.exist');
  }

  /**
   * Verify Text Content
   *
   * VERIFIES: Element contains expected text
   */
  verifyText(testId: string, text: string): void {
    cy.get(`[data-testid="${testId}"]`).should('contain', text);
  }

  /**
   * Wait For Element
   *
   * WAITS: For element to appear
   */
  waitForElement(testId: string, timeout: number = 10000): void {
    cy.get(`[data-testid="${testId}"]`, { timeout }).should('exist');
  }

  /**
   * Wait For Loading
   *
   * WAITS: For loading spinner to disappear
   */
  waitForLoading(): void {
    cy.waitForSpinner();
  }
}
