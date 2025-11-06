/**
 * Cypress E2E Support Configuration
 *
 * BUSINESS CONTEXT:
 * Global test setup and configuration for all E2E tests.
 * Loads custom commands and provides test environment setup.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Imports custom commands (authentication, navigation, actions)
 * - Configures global test hooks (beforeEach, afterEach)
 * - Sets up test data cleanup
 * - Provides consistent test environment
 *
 * USAGE:
 * This file is automatically loaded before every test spec.
 * Add global configurations and hooks here.
 */

// Import custom commands
import './commands';

// Import Cypress types
/// <reference types="cypress" />

/**
 * Global Before Hook
 *
 * RUNS: Once before all tests in the spec file
 *
 * PURPOSE:
 * - Clear cookies and local storage
 * - Reset application state
 * - Ensure clean test environment
 */
beforeEach(() => {
  // Clear cookies and local storage before each test
  cy.clearCookies();
  cy.clearLocalStorage();

  // Set default viewport
  cy.viewport(1280, 720);
});

/**
 * Global After Hook
 *
 * RUNS: Once after all tests in the spec file
 *
 * PURPOSE:
 * - Cleanup test data
 * - Log test results
 */
afterEach(function () {
  // Log test status
  if (this.currentTest?.state === 'failed') {
    cy.task('log', `❌ Test failed: ${this.currentTest.title}`);
  }
});

/**
 * Exception Handler
 *
 * PREVENTS: Tests from failing due to uncaught exceptions
 *
 * USE CASES:
 * - Third-party library errors
 * - Non-critical application errors
 * - Network errors during cleanup
 *
 * NOTE: Comment out or modify for production-critical error handling
 */
Cypress.on('uncaught:exception', (err, runnable) => {
  // Log the error but don't fail the test
  console.error('Uncaught exception:', err);

  // Return false to prevent Cypress from failing the test
  // Modify this logic to fail on specific errors if needed
  return false;
});

/**
 * Console Log Handler
 *
 * CAPTURES: Browser console logs in Cypress output
 *
 * DEBUGGING: Helps identify issues in browser console
 */
Cypress.on('window:before:load', (win) => {
  // Capture console.error
  cy.stub(win.console, 'error').callsFake((msg) => {
    cy.task('log', `🔴 Console Error: ${msg}`);
  });

  // Capture console.warn
  cy.stub(win.console, 'warn').callsFake((msg) => {
    cy.task('log', `🟡 Console Warning: ${msg}`);
  });
});
