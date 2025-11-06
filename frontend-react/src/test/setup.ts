/**
 * Vitest Test Setup Configuration
 *
 * BUSINESS CONTEXT:
 * Configures global test environment for all unit and integration tests in the React application.
 * Ensures consistent test behavior, proper mocking, and comprehensive test utilities.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Extends matchers with @testing-library/jest-dom for enhanced assertions
 * - Sets up global test mocks for browser APIs not available in jsdom
 * - Configures React Testing Library with custom render utilities
 * - Provides mock implementations for external dependencies
 *
 * WHY THIS APPROACH:
 * - jsdom doesn't provide all browser APIs (matchMedia, IntersectionObserver, etc.)
 * - Consistent mock implementations prevent test failures from missing APIs
 * - Global setup reduces boilerplate in individual test files
 * - Testing Library extensions provide better assertions for React components
 */

import { expect, afterEach, beforeAll, afterAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';
import { server } from './mocks/server';

/**
 * MSW SERVER SETUP
 *
 * BUSINESS REQUIREMENT:
 * Tests should use real service implementations without mocking services directly.
 * Network requests are intercepted at the HTTP level instead.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Starts MSW server before all tests to intercept HTTP requests
 * - Resets handlers after each test for isolation
 * - Stops server after all tests complete
 *
 * WHY THIS APPROACH:
 * - Services use real code, improving test reliability
 * - HTTP interception is more realistic than service mocking
 * - Test behavior matches production more closely
 */
beforeAll(() => {
  console.log('[TEST SETUP] Starting MSW server...');
  server.listen({
    onUnhandledRequest: (req) => {
      console.log('[MSW] Unhandled request:', req.method, req.url);
    }
  });
  console.log('[TEST SETUP] MSW server started');
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  console.log('[TEST SETUP] Stopping MSW server...');
  server.close();
});

/**
 * EXTEND VITEST MATCHERS WITH JEST-DOM
 *
 * BUSINESS REQUIREMENT:
 * Tests need semantic assertions for DOM elements (toBeInTheDocument, toHaveClass, etc.)
 * rather than low-level DOM API checks.
 *
 * TECHNICAL IMPLEMENTATION:
 * Adds Testing Library matchers to Vitest's expect function for enhanced DOM assertions.
 *
 * EXAMPLES:
 * - expect(element).toBeInTheDocument()
 * - expect(button).toBeDisabled()
 * - expect(input).toHaveValue('test')
 */
expect.extend(matchers);

/**
 * CLEANUP AFTER EACH TEST
 *
 * BUSINESS REQUIREMENT:
 * Tests must not affect each other - each test should run in isolation.
 *
 * TECHNICAL IMPLEMENTATION:
 * Automatically unmounts React components and cleans up DOM after each test.
 *
 * WHY THIS PREVENTS BUGS:
 * - Prevents test pollution where one test affects another
 * - Ensures consistent test results regardless of execution order
 * - Avoids memory leaks from unmounted components
 */
afterEach(() => {
  cleanup();
});

/**
 * MOCK WINDOW.MATCHMEDIA
 *
 * PROBLEM ADDRESSED:
 * jsdom doesn't implement window.matchMedia, causing tests to fail when components
 * use media queries for responsive behavior.
 *
 * SOLUTION:
 * Provide a mock implementation that returns a basic MediaQueryList object.
 *
 * USAGE IN CODE:
 * Components using responsive design (useMediaQuery, CSS media queries) will not fail.
 */
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

/**
 * MOCK INTERSECTION OBSERVER API
 *
 * PROBLEM ADDRESSED:
 * jsdom doesn't implement IntersectionObserver, which is used for lazy loading,
 * infinite scroll, and visibility tracking.
 *
 * SOLUTION:
 * Provide a mock implementation that simulates immediate intersection.
 *
 * USAGE IN CODE:
 * Components using lazy loading or scroll-based features will work in tests.
 */
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as any;

/**
 * MOCK RESIZE OBSERVER API
 *
 * PROBLEM ADDRESSED:
 * jsdom doesn't implement ResizeObserver, used for detecting element size changes.
 *
 * SOLUTION:
 * Provide a mock implementation that prevents errors in components using resize detection.
 *
 * USAGE IN CODE:
 * Components that adapt to container size changes will work in tests.
 */
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;

/**
 * MOCK WINDOW.SCROLLTO
 *
 * PROBLEM ADDRESSED:
 * jsdom doesn't implement window.scrollTo, causing errors in components with
 * scroll behavior.
 *
 * SOLUTION:
 * Provide a no-op implementation that prevents errors.
 *
 * USAGE IN CODE:
 * Components that trigger scroll behavior (smooth scrolling, scroll to top) will work.
 */
window.scrollTo = vi.fn();

/**
 * MOCK LOCAL STORAGE
 *
 * BUSINESS REQUIREMENT:
 * Application uses localStorage for session persistence, user preferences, and cache.
 *
 * TECHNICAL IMPLEMENTATION:
 * Provides a working localStorage implementation for tests that matches browser behavior.
 *
 * WHY THIS APPROACH:
 * - jsdom's localStorage implementation can be unreliable
 * - This ensures consistent localStorage behavior across all tests
 * - Each test gets a fresh localStorage instance via cleanup
 */
const localStorageMock = {
  getItem: vi.fn((key: string) => localStorageMock.store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    localStorageMock.store[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete localStorageMock.store[key];
  }),
  clear: vi.fn(() => {
    localStorageMock.store = {};
  }),
  store: {} as Record<string, string>,
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

/**
 * CLEAR LOCALSTORAGE BETWEEN TESTS
 *
 * BUSINESS REQUIREMENT:
 * Tests must not be affected by localStorage state from previous tests.
 *
 * TECHNICAL IMPLEMENTATION:
 * Clears localStorage after each test to ensure isolation.
 */
afterEach(() => {
  localStorageMock.clear();
});

/**
 * MOCK CONSOLE METHODS FOR CLEAN TEST OUTPUT
 *
 * BUSINESS REQUIREMENT:
 * Tests should not spam console with expected errors/warnings during test runs.
 *
 * TECHNICAL IMPLEMENTATION:
 * Suppress console.error and console.warn during tests unless explicitly needed.
 *
 * WHY THIS APPROACH:
 * - Expected React errors (e.g., testing error boundaries) shouldn't clutter output
 * - Tests can still assert on specific console calls when needed
 * - Unexpected errors will still be visible in test failures
 */
global.console = {
  ...console,
  error: vi.fn(),
  warn: vi.fn(),
};

/**
 * MOCK CRYPTO.RANDOMUUID
 *
 * PROBLEM ADDRESSED:
 * Some Node environments don't have crypto.randomUUID available.
 *
 * SOLUTION:
 * Provide a simple UUID v4 implementation for tests.
 */
if (!global.crypto) {
  global.crypto = {} as any;
}

if (!global.crypto.randomUUID) {
  global.crypto.randomUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  };
}

/**
 * ENVIRONMENT VARIABLES FOR TESTS
 *
 * BUSINESS REQUIREMENT:
 * Tests need consistent environment configuration.
 *
 * TECHNICAL IMPLEMENTATION:
 * Sets default environment variables for test environment.
 */
process.env.NODE_ENV = 'test';
process.env.VITE_API_BASE_URL = 'https://176.9.99.103:8000';
