/**
 * Cypress E2E Test Configuration
 *
 * BUSINESS CONTEXT:
 * Configures end-to-end testing for complete user workflows across all roles
 * in the Course Creator Platform. Ensures comprehensive testing coverage for
 * student, instructor, organization admin, and site admin journeys.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Runs against local development server (http://localhost:3000)
 * - Supports multiple viewports (desktop 1280x720, tablet 768x1024, mobile 375x667)
 * - Records videos for failed tests to aid in debugging
 * - Captures screenshots on failure for visual debugging
 * - Retries flaky tests automatically (2 retries in CI, 0 in interactive mode)
 * - Configures appropriate timeouts for API calls and UI interactions
 * - Supports Chrome, Firefox, and Edge browsers
 *
 * TESTING STRATEGY:
 * - Unit tests: Vitest (component-level)
 * - Integration tests: Vitest + React Testing Library (component integration)
 * - E2E tests: Cypress (complete user workflows)
 *
 * CRITICAL REQUIREMENTS:
 * - All 4 user roles must have comprehensive E2E coverage
 * - Tests must verify complete workflows, not just individual features
 * - Tests must be reliable and reproducible
 * - Failed tests must provide clear debugging information
 */

import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    // Base URL for the React application
    baseUrl: 'http://localhost:3000',

    // Default viewport (desktop)
    viewportWidth: 1280,
    viewportHeight: 720,

    // Video recording (only on failures to save disk space)
    video: true,
    videoCompression: 32,
    videosFolder: 'cypress/videos',

    // Screenshot configuration
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/screenshots',

    // Timeout configurations
    defaultCommandTimeout: 10000,  // 10s for DOM queries
    requestTimeout: 10000,          // 10s for API requests
    responseTimeout: 10000,         // 10s for API responses
    pageLoadTimeout: 60000,         // 60s for page loads

    // Test file patterns
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/e2e.ts',
    fixturesFolder: 'cypress/fixtures',

    // Retry configuration
    retries: {
      runMode: 2,    // 2 retries in CI
      openMode: 0,   // No retries in interactive mode
    },

    // Environment variables
    env: {
      // API endpoints
      apiUrl: 'http://localhost:80',
      userManagementApi: 'http://localhost:8000',
      courseManagementApi: 'http://localhost:8001',
      contentManagementApi: 'http://localhost:8002',
      courseGeneratorApi: 'http://localhost:8003',
      analyticsApi: 'http://localhost:8004',
      metadataApi: 'http://localhost:8005',
      demoServiceApi: 'http://localhost:8010',

      // Test user credentials
      coverage: false,  // Enable code coverage collection
    },

    // Setup node event listeners
    setupNodeEvents(on, config) {
      // Implement node event listeners here

      // Log console output from the browser
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
        table(message) {
          console.table(message);
          return null;
        },
      });

      // Code coverage support (if enabled)
      // require('@cypress/code-coverage/task')(on, config);

      return config;
    },
  },

  // Component testing configuration (future enhancement)
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite',
    },
    specPattern: 'src/**/*.cy.{js,jsx,ts,tsx}',
  },
});
