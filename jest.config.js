/**
 * Jest Configuration for Course Creator Platform
 *
 * BUSINESS CONTEXT:
 * Configures JavaScript testing framework for frontend unit tests
 * and integration tests.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Supports ES6+ syntax
 * - Mocks browser APIs
 * - Provides coverage reporting
 * - Integrates with CI/CD pipelines
 */

module.exports = {
    // Test environment
    testEnvironment: 'jsdom',

    // Test file patterns
    testMatch: [
        '**/tests/frontend/**/*.test.js',
        '**/tests/frontend/**/*.spec.js'
    ],

    // Coverage collection
    collectCoverage: true,
    collectCoverageFrom: [
        'frontend/js/**/*.js',
        '!frontend/js/**/*.min.js',
        '!frontend/js/vendor/**',
        '!frontend/js/lib/**'
    ],

    // Coverage thresholds
    coverageThreshold: {
        global: {
            branches: 70,
            functions: 70,
            lines: 70,
            statements: 70
        }
    },

    // Coverage output
    coverageDirectory: 'tests/reports/coverage/frontend',
    coverageReporters: ['text', 'lcov', 'html', 'json-summary'],

    // Module paths
    moduleDirectories: ['node_modules', 'frontend/js'],

    // Setup files
    setupFilesAfterEnv: ['<rootDir>/tests/frontend/setup.js'],

    // Transform files
    transform: {
        '^.+\\.js$': 'babel-jest'
    },

    // Mock static assets
    moduleNameMapper: {
        '\\.(css|less|scss|sass)$': '<rootDir>/tests/frontend/__mocks__/styleMock.js',
        '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/tests/frontend/__mocks__/fileMock.js'
    },

    // Ignore patterns
    testPathIgnorePatterns: [
        '/node_modules/',
        '/dist/',
        '/build/',
        '/.venv/',
        '/venv/'
    ],

    // Watch ignore patterns
    watchPathIgnorePatterns: [
        '/node_modules/',
        '/dist/',
        '/build/'
    ],

    // Verbose output
    verbose: true,

    // Clear mocks between tests
    clearMocks: true,

    // Reset mocks between tests
    resetMocks: true,

    // Restore mocks between tests
    restoreMocks: true,

    // Test timeout (milliseconds)
    testTimeout: 10000,

    // Globals available in tests
    globals: {
        'NODE_ENV': 'test'
    },

    // Reporter configuration
    reporters: [
        'default',
        [
            'jest-html-reporter',
            {
                pageTitle: 'Course Creator - Frontend Test Report',
                outputPath: 'tests/reports/frontend-test-report.html',
                includeFailureMsg: true,
                includeConsoleLog: true,
                sort: 'status'
            }
        ]
    ],

    // Error handling
    bail: false,
    errorOnDeprecated: true
};
