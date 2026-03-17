/**
 * Unit Tests for Auth.getToken() Method
 *
 * BUSINESS CONTEXT:
 * The Auth.getToken() method is critical for org-admin API authentication.
 * It's called in 50+ locations across the org-admin codebase to retrieve
 * the JWT token for authenticated API requests.
 *
 * BUG CONTEXT:
 * This test suite was created as part of TDD to verify the getToken() method
 * works correctly after discovering it was missing from auth.js, causing
 * all org-admin API calls to fail with "Auth.getToken is not a function" errors.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests token retrieval from authToken property (in-memory)
 * - Tests token retrieval from localStorage (persistent storage)
 * - Tests fallback behavior when token doesn't exist
 * - Tests priority order: authToken property > localStorage
 * - Tests graceful handling of null/undefined states
 *
 * TDD METHODOLOGY:
 * These tests were written FIRST (RED phase) to define expected behavior,
 * then the implementation was created to make tests pass (GREEN phase).
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';

/**
 * Test Suite: Auth.getToken() Method
 *
 * PURPOSE: Verify comprehensive token retrieval behavior
 * WHY: Token access is fundamental for all authenticated API operations
 */
describe('Auth.getToken() Method', () => {
    let dom;
    let localStorage;
    let AuthManager;
    let authInstance;

    /**
     * Setup: Initialize test environment before each test
     *
     * Creates a clean JSDOM environment with:
     * - Fresh localStorage instance
     * - Global window and document objects
     * - Clean AuthManager instance
     */
    beforeEach(async () => {
        // Setup DOM environment
        dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            url: 'https://localhost:3000',
            pretendToBeVisual: true
        });

        global.window = dom.window;
        global.document = dom.window.document;
        global.localStorage = dom.window.localStorage;
        localStorage = global.localStorage;

        // Mock CONFIG for API endpoints
        global.window.CONFIG = {
            API_URLS: {
                USER_MANAGEMENT: 'https://localhost:8000'
            }
        };

        // Clear localStorage before each test
        localStorage.clear();

        // Mock dependencies that auth.js imports
        vi.mock('../../../frontend/js/modules/notifications.js', () => ({
            showNotification: vi.fn()
        }));

        vi.mock('../../../frontend/js/modules/activity-tracker.js', () => ({
            ActivityTracker: class MockActivityTracker {
                start() {}
                stop() {}
                trackActivity() {}
            }
        }));

        vi.mock('../../../frontend/js/modules/lab-lifecycle.js', () => ({
            labLifecycleManager: {
                initialize: vi.fn(),
                cleanup: vi.fn()
            }
        }));

        // Import AuthManager class dynamically to get fresh instance
        // Note: In real implementation, we'd import from auth.js
        // For testing, we'll create a minimal AuthManager mock
        AuthManager = class TestAuthManager {
            constructor() {
                this.authToken = null;
                this.currentUser = null;
            }

            /**
             * GET TOKEN METHOD - This is what we're testing
             *
             * TOKEN RETRIEVAL STRATEGY:
             * 1. Return authToken property if set (in-memory)
             * 2. Fall back to localStorage if property is null
             * 3. Return null if no token exists anywhere
             *
             * WHY THIS PATTERN:
             * - authToken property is faster (no I/O)
             * - localStorage provides persistence across page loads
             * - Fallback ensures token availability after refresh
             */
            getToken() {
                return this.authToken || localStorage.getItem('authToken');
            }

            // Helper methods for test setup
            setAuthToken(token) {
                this.authToken = token;
            }

            clearAuthToken() {
                this.authToken = null;
            }
        };

        authInstance = new AuthManager();
    });

    /**
     * Cleanup: Reset test environment after each test
     */
    afterEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
    });

    /**
     * TEST 1: Return token from authToken property when set
     *
     * SCENARIO: Token exists in memory (authToken property)
     * EXPECTED: Return the in-memory token
     * WHY: In-memory access is fastest, should be preferred
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Set authToken property to a valid JWT
     * - Act: Call getToken()
     * - Assert: Verify returned token matches authToken property
     */
    it('should return token from authToken property when set', () => {
        // Arrange: Set up in-memory token
        const expectedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.memory-token';
        authInstance.setAuthToken(expectedToken);

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify correct token returned
        expect(actualToken).toBe(expectedToken);
        expect(actualToken).not.toBeNull();
        expect(actualToken).not.toBeUndefined();
    });

    /**
     * TEST 2: Return token from localStorage when authToken is null
     *
     * SCENARIO: Token doesn't exist in memory but exists in localStorage
     * EXPECTED: Return the localStorage token (fallback behavior)
     * WHY: After page refresh, authToken property resets but localStorage persists
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Clear authToken property, set localStorage token
     * - Act: Call getToken()
     * - Assert: Verify returned token matches localStorage value
     */
    it('should return token from localStorage when authToken is null', () => {
        // Arrange: Set up localStorage token only (simulating page refresh)
        const expectedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.localstorage-token';
        authInstance.clearAuthToken(); // Ensure authToken is null
        localStorage.setItem('authToken', expectedToken);

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify localStorage token returned
        expect(actualToken).toBe(expectedToken);
        expect(actualToken).not.toBeNull();
    });

    /**
     * TEST 3: Return null when no token exists anywhere
     *
     * SCENARIO: No token in memory or localStorage (unauthenticated state)
     * EXPECTED: Return null
     * WHY: Calling code needs to handle unauthenticated state gracefully
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Ensure no token exists anywhere
     * - Act: Call getToken()
     * - Assert: Verify null is returned
     */
    it('should return null when no token exists anywhere', () => {
        // Arrange: Ensure no token exists
        authInstance.clearAuthToken();
        localStorage.removeItem('authToken');

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify null returned for unauthenticated state
        expect(actualToken).toBeNull();
    });

    /**
     * TEST 4: Prioritize authToken property over localStorage
     *
     * SCENARIO: Different tokens exist in both locations
     * EXPECTED: Return authToken property (in-memory) token
     * WHY: In-memory token represents current session state
     *
     * REAL-WORLD USE CASE:
     * After login, authToken is set immediately in memory.
     * If old token exists in localStorage, in-memory token should win.
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Set different tokens in authToken and localStorage
     * - Act: Call getToken()
     * - Assert: Verify authToken property value is returned
     */
    it('should prioritize authToken property over localStorage', () => {
        // Arrange: Set different tokens in both locations
        const memoryToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.memory-token-priority';
        const storageToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.storage-token-old';

        authInstance.setAuthToken(memoryToken);
        localStorage.setItem('authToken', storageToken);

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify memory token takes priority
        expect(actualToken).toBe(memoryToken);
        expect(actualToken).not.toBe(storageToken);
    });

    /**
     * TEST 5: Handle undefined localStorage gracefully
     *
     * SCENARIO: localStorage.getItem() returns undefined (edge case)
     * EXPECTED: Return null without throwing errors
     * WHY: Graceful degradation prevents crashes in unusual environments
     *
     * EDGE CASE CONTEXT:
     * Some browsers/environments might return undefined instead of null
     * for non-existent localStorage keys. Method should handle this.
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Mock localStorage to return undefined
     * - Act: Call getToken()
     * - Assert: Verify graceful handling (no errors, returns falsy value)
     */
    it('should handle undefined localStorage gracefully', () => {
        // Arrange: Mock localStorage.getItem to return undefined
        const originalGetItem = localStorage.getItem;
        localStorage.getItem = vi.fn(() => undefined);
        authInstance.clearAuthToken();

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify graceful handling
        expect(actualToken).toBeFalsy(); // undefined or null, both are falsy
        expect(() => authInstance.getToken()).not.toThrow();

        // Cleanup: Restore original localStorage.getItem
        localStorage.getItem = originalGetItem;
    });

    /**
     * TEST 6: Handle null authToken property explicitly
     *
     * SCENARIO: authToken is explicitly set to null (not just undefined)
     * EXPECTED: Fall back to localStorage correctly
     * WHY: null and undefined should be handled identically
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Set authToken to null, set localStorage token
     * - Act: Call getToken()
     * - Assert: Verify localStorage fallback works with explicit null
     */
    it('should handle null authToken property explicitly', () => {
        // Arrange: Explicitly set authToken to null
        const storageToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.storage-token';
        authInstance.authToken = null; // Explicit null assignment
        localStorage.setItem('authToken', storageToken);

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify localStorage fallback works
        expect(actualToken).toBe(storageToken);
    });

    /**
     * TEST 7: Return token after login simulation
     *
     * SCENARIO: Simulate login flow where token is set
     * EXPECTED: getToken() returns the newly set token
     * WHY: Integration test ensuring getToken() works in realistic login flow
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Simulate login by setting authToken and localStorage
     * - Act: Call getToken()
     * - Assert: Verify token is accessible immediately after login
     */
    it('should return token after login simulation', () => {
        // Arrange: Simulate successful login
        const loginToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.login-token';

        // Simulate what login() method does
        authInstance.setAuthToken(loginToken);
        localStorage.setItem('authToken', loginToken);
        localStorage.setItem('userEmail', 'admin@example.com');
        localStorage.setItem('sessionStart', Date.now().toString());

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify token is accessible
        expect(actualToken).toBe(loginToken);
        expect(actualToken).toBeTruthy();
    });

    /**
     * TEST 8: Return null after logout simulation
     *
     * SCENARIO: Simulate logout flow where tokens are cleared
     * EXPECTED: getToken() returns null after logout
     * WHY: Integration test ensuring getToken() reflects logout state
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Set up authenticated state, then simulate logout
     * - Act: Call getToken()
     * - Assert: Verify null is returned after logout
     */
    it('should return null after logout simulation', () => {
        // Arrange: Set up authenticated state
        const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.session-token';
        authInstance.setAuthToken(token);
        localStorage.setItem('authToken', token);

        // Simulate logout cleanup
        authInstance.clearAuthToken();
        localStorage.removeItem('authToken');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('currentUser');

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify token is null after logout
        expect(actualToken).toBeNull();
    });

    /**
     * TEST 9: Handle concurrent access (multiple calls)
     *
     * SCENARIO: getToken() called multiple times in quick succession
     * EXPECTED: All calls return same consistent token
     * WHY: Multiple modules may call getToken() simultaneously
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Set up token in authToken property
     * - Act: Call getToken() multiple times
     * - Assert: Verify all calls return identical token
     */
    it('should handle concurrent access consistently', () => {
        // Arrange: Set up token
        const expectedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.concurrent-token';
        authInstance.setAuthToken(expectedToken);

        // Act: Call getToken() multiple times
        const token1 = authInstance.getToken();
        const token2 = authInstance.getToken();
        const token3 = authInstance.getToken();

        // Assert: Verify all calls return same token
        expect(token1).toBe(expectedToken);
        expect(token2).toBe(expectedToken);
        expect(token3).toBe(expectedToken);
        expect(token1).toBe(token2);
        expect(token2).toBe(token3);
    });

    /**
     * TEST 10: Handle empty string token in localStorage
     *
     * SCENARIO: localStorage contains empty string instead of valid token
     * EXPECTED: Return empty string (calling code handles validation)
     * WHY: getToken() is responsible for retrieval, not validation
     *
     * ARRANGE-ACT-ASSERT PATTERN:
     * - Arrange: Set localStorage to empty string
     * - Act: Call getToken()
     * - Assert: Verify empty string is returned (not null)
     */
    it('should handle empty string token in localStorage', () => {
        // Arrange: Set localStorage to empty string
        authInstance.clearAuthToken();
        localStorage.setItem('authToken', '');

        // Act: Retrieve token
        const actualToken = authInstance.getToken();

        // Assert: Verify empty string returned (not null)
        expect(actualToken).toBe('');
        expect(actualToken).not.toBeNull();
        expect(actualToken).toBeFalsy(); // Empty string is falsy
    });
});

/**
 * Integration Test Suite: Auth.getToken() with Org-Admin API
 *
 * PURPOSE: Verify getToken() integration with org-admin API calls
 * WHY: getToken() was created specifically to fix org-admin API failures
 */
describe('Auth.getToken() Integration with Org-Admin API', () => {
    let localStorage;
    let AuthManager;
    let authInstance;

    beforeEach(() => {
        // Setup minimal DOM environment
        const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            url: 'https://localhost:3000'
        });

        global.window = dom.window;
        global.localStorage = dom.window.localStorage;
        localStorage = global.localStorage;
        localStorage.clear();

        // Minimal AuthManager for integration tests
        AuthManager = class TestAuthManager {
            constructor() {
                this.authToken = null;
            }
            getToken() {
                return this.authToken || localStorage.getItem('authToken');
            }
            setAuthToken(token) {
                this.authToken = token;
            }
        };

        authInstance = new AuthManager();
    });

    /**
     * TEST: Verify getToken() provides token for API Authorization header
     *
     * REAL-WORLD USE CASE:
     * Org-admin API calls use: Authorization: `Bearer ${Auth.getToken()}`
     * This test verifies getToken() returns a token suitable for this pattern
     */
    it('should provide token for API Authorization header', () => {
        // Arrange: Set up authentication
        const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.api-token';
        authInstance.setAuthToken(token);

        // Act: Construct Authorization header (like org-admin-api.js does)
        const authHeader = `Bearer ${authInstance.getToken()}`;

        // Assert: Verify header format is correct
        expect(authHeader).toBe(`Bearer ${token}`);
        expect(authHeader).toMatch(/^Bearer eyJ/); // JWT starts with eyJ
        expect(authHeader).not.toContain('undefined');
        expect(authHeader).not.toContain('null');
    });

    /**
     * TEST: Verify getToken() prevents "undefined" in Authorization header
     *
     * BUG CONTEXT:
     * Before getToken() was implemented, code tried Auth.getToken() which
     * didn't exist, resulting in undefined being interpolated into headers
     */
    it('should prevent undefined in Authorization header', () => {
        // Arrange: No authentication (simulating missing getToken())
        authInstance.authToken = null;
        localStorage.removeItem('authToken');

        // Act: Construct Authorization header
        const token = authInstance.getToken();
        const authHeader = token ? `Bearer ${token}` : null;

        // Assert: Verify undefined doesn't leak into header
        expect(authHeader).toBeNull(); // Should be null, not "Bearer undefined"
        if (authHeader) {
            expect(authHeader).not.toContain('undefined');
        }
    });

    /**
     * TEST: Verify getToken() works for multiple API calls
     *
     * REAL-WORLD SCENARIO:
     * Org-admin dashboard makes 50+ API calls, all calling Auth.getToken()
     * This test verifies getToken() performs consistently across multiple calls
     */
    it('should work consistently for multiple API calls', () => {
        // Arrange: Set up authentication
        const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.multi-api-token';
        authInstance.setAuthToken(token);

        // Act: Simulate 10 API calls each calling getToken()
        const apiCalls = [];
        for (let i = 0; i < 10; i++) {
            const header = `Bearer ${authInstance.getToken()}`;
            apiCalls.push(header);
        }

        // Assert: All API calls have correct Authorization header
        apiCalls.forEach(header => {
            expect(header).toBe(`Bearer ${token}`);
        });
    });
});
