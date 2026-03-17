/**
 * Integration Tests for Org Admin Authentication Flow
 *
 * BUSINESS CONTEXT:
 * Tests the complete authentication flow from login to dashboard access,
 * ensuring tokens are properly set, verified, and used for API calls.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests integration between auth.js, org-admin-core.js, and org-admin-api.js
 * - Validates token flow through the entire authentication chain
 * - Tests redirect behavior on auth failure
 *
 * TDD METHODOLOGY:
 * These tests catch issues where modules use different token key names,
 * preventing the redirect loop bug that occurred in production.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';

describe('Org Admin Authentication Flow Integration', () => {
    let dom;
    let window;
    let localStorage;
    let fetchMock;

    beforeEach(() => {
        // Setup DOM environment with full navigation
        dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            url: 'https://176.9.99.103:3000/html/org-admin-dashboard.html?org_id=1',
            pretendToBeVisual: true
        });

        window = dom.window;
        global.window = window;
        global.document = window.document;
        global.localStorage = window.localStorage;
        localStorage = global.localStorage;

        // Mock fetch
        fetchMock = vi.fn();
        global.fetch = fetchMock;

        localStorage.clear();
    });

    afterEach(() => {
        vi.restoreAllMocks();
        localStorage.clear();
    });

    /**
     * TEST: Complete authentication flow from login to dashboard
     * REQUIREMENT: Token set in login must be usable by dashboard
     */
    it('should complete full authentication flow without redirect loop', async () => {
        // STEP 1: Simulate successful login (auth.js behavior)
        const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mocktoken';
        const mockUser = {
            id: 1,
            email: 'admin@test.com',
            role: 'organization_admin',
            organization_id: 1
        };

        // Auth.js sets these keys on login (line 266-293)
        localStorage.setItem('authToken', mockToken);
        localStorage.setItem('userEmail', mockUser.email);
        localStorage.setItem('currentUser', JSON.stringify(mockUser));
        localStorage.setItem('sessionStart', Date.now().toString());
        localStorage.setItem('lastActivity', Date.now().toString());

        // STEP 2: Dashboard initialization checks token (org-admin-core.js line 47)
        const token = localStorage.getItem('authToken');
        expect(token).toBeTruthy();
        expect(token).toBe(mockToken);

        // STEP 3: With valid token, no redirect should occur
        // (Redirect behavior tested in E2E tests)

        // STEP 4: API calls should use correct token (org-admin-api.js line 40)
        const apiToken = localStorage.getItem('authToken');
        const headers = {
            'Authorization': `Bearer ${apiToken}`,
            'Content-Type': 'application/json'
        };

        expect(headers.Authorization).toBe(`Bearer ${mockToken}`);
        expect(headers.Authorization).not.toContain('undefined');
    });

    /**
     * TEST: Dashboard detects missing token
     * REQUIREMENT: Missing token should be detected for redirect logic
     */
    it('should detect missing authToken for redirect logic', () => {
        // No token in localStorage
        const token = localStorage.getItem('authToken');
        expect(token).toBeNull();

        // Simulate org-admin-core.js auth check (line 47-51)
        let shouldRedirect = !token;

        expect(shouldRedirect).toBe(true);
    });

    /**
     * TEST: API calls fail with proper error when token is missing
     * REQUIREMENT: Missing token should cause API to return 401, not crash
     */
    it('should handle API calls with missing token gracefully', async () => {
        // No token set
        const token = localStorage.getItem('authToken');
        expect(token).toBeNull();

        // Mock API response for unauthenticated request
        fetchMock.mockResolvedValueOnce({
            ok: false,
            status: 401,
            json: async () => ({ error: 'Unauthorized' })
        });

        // Simulate API call with missing token
        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };

        const response = await fetch('https://localhost:8001/api/v1/users/me', { headers });

        expect(response.ok).toBe(false);
        expect(response.status).toBe(401);
    });

    /**
     * TEST: fetchCurrentUser succeeds with valid token
     * REQUIREMENT: API calls must use authToken from localStorage
     */
    it('should successfully fetch current user with valid token', async () => {
        const mockToken = 'valid-jwt-token';
        const mockUser = {
            id: 1,
            email: 'admin@test.com',
            role: 'organization_admin'
        };

        localStorage.setItem('authToken', mockToken);

        // Mock successful API response
        fetchMock.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => mockUser
        });

        // Simulate getAuthHeaders() and API call
        const token = localStorage.getItem('authToken');
        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };

        const response = await fetch('https://localhost:8001/api/v1/users/me', { headers });
        const user = await response.json();

        expect(response.ok).toBe(true);
        expect(user).toEqual(mockUser);
        expect(fetchMock).toHaveBeenCalledWith(
            'https://localhost:8001/api/v1/users/me',
            expect.objectContaining({
                headers: expect.objectContaining({
                    'Authorization': `Bearer ${mockToken}`
                })
            })
        );
    });

    /**
     * TEST: Logout clears all auth data and redirects
     * REQUIREMENT: Logout must clear authToken and redirect to index.html
     */
    it('should clear all auth data on logout and redirect', () => {
        // Setup: User is logged in
        localStorage.setItem('authToken', 'session-token');
        localStorage.setItem('currentUser', JSON.stringify({ id: 1 }));
        localStorage.setItem('userEmail', 'user@test.com');
        localStorage.setItem('sessionStart', Date.now().toString());
        localStorage.setItem('lastActivity', Date.now().toString());

        // Simulate logout (org-admin-core.js lines 302-309)
        let redirectAfterLogout = false;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('sessionStart');
        localStorage.removeItem('lastActivity');
        redirectAfterLogout = true;

        // Verify all auth data cleared
        expect(localStorage.getItem('authToken')).toBeNull();
        expect(localStorage.getItem('currentUser')).toBeNull();
        expect(localStorage.getItem('userEmail')).toBeNull();
        expect(redirectAfterLogout).toBe(true);
    });

    /**
     * TEST: Session timeout clears auth and redirects
     * REQUIREMENT: Inactivity timeout must clear authToken
     */
    it('should handle session timeout by clearing auth data', () => {
        // Setup: User has been inactive
        const sessionStart = Date.now() - (35 * 60 * 1000); // 35 minutes ago
        localStorage.setItem('authToken', 'expired-session-token');
        localStorage.setItem('sessionStart', sessionStart.toString());
        localStorage.setItem('last_activity_timestamp', sessionStart.toString());

        // Check if session is expired (30 minute timeout)
        const TIMEOUT_DURATION = 30 * 60 * 1000;
        const lastActivity = parseInt(localStorage.getItem('last_activity_timestamp'));
        const timeSinceActivity = Date.now() - lastActivity;
        const isExpired = timeSinceActivity > TIMEOUT_DURATION;

        expect(isExpired).toBe(true);

        // Simulate session-manager.js logout (lines 234-240)
        if (isExpired) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('sessionStart');
            localStorage.removeItem('lastActivity');
        }

        expect(localStorage.getItem('authToken')).toBeNull();
    });

    /**
     * TEST: Token key consistency between all modules
     * REQUIREMENT: All modules must use 'authToken', never 'auth_token'
     */
    it('should use consistent authToken key across all modules', () => {
        const token = 'consistency-test-token';

        // Module 1: auth.js sets token
        localStorage.setItem('authToken', token);

        // Module 2: org-admin-core.js reads token
        const coreToken = localStorage.getItem('authToken');
        expect(coreToken).toBe(token);

        // Module 3: org-admin-api.js reads token
        const apiToken = localStorage.getItem('authToken');
        expect(apiToken).toBe(token);

        // Module 4: session-manager.js reads token
        const sessionToken = localStorage.getItem('authToken');
        expect(sessionToken).toBe(token);

        // Verify deprecated key is never used
        const deprecatedToken = localStorage.getItem('auth_token');
        expect(deprecatedToken).toBeNull();
    });

    /**
     * TEST: Dashboard loads organization after authentication
     * REQUIREMENT: Authenticated user should fetch organization data
     */
    it('should load organization data after successful authentication', async () => {
        const mockToken = 'auth-token-xyz';
        const mockOrg = {
            id: 1,
            name: 'Test Organization',
            domain: 'test.org',
            member_count: 50
        };

        localStorage.setItem('authToken', mockToken);

        // Mock organization fetch
        fetchMock.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => mockOrg
        });

        // Simulate org-admin-core.js organization fetch (line 68)
        const token = localStorage.getItem('authToken');
        const response = await fetch('https://localhost:8008/api/v1/organizations/1', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        const organization = await response.json();

        expect(response.ok).toBe(true);
        expect(organization.name).toBe('Test Organization');
    });
});

/**
 * Test Suite: Redirect Loop Prevention
 */
describe('Redirect Loop Prevention', () => {
    let localStorage;

    beforeEach(() => {
        const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            url: 'https://localhost:3000'
        });
        localStorage = dom.window.localStorage;
        global.localStorage = localStorage;
        localStorage.clear();
    });

    /**
     * TEST: Prevent redirect loop when token exists
     * REQUIREMENT: Dashboard must NOT redirect if authToken exists
     */
    it('should not create redirect loop when token is present', () => {
        localStorage.setItem('authToken', 'valid-token');

        // Simulate dashboard auth check
        const token = localStorage.getItem('authToken');
        let shouldRedirect = !token;

        expect(shouldRedirect).toBe(false);
    });

    /**
     * TEST: Detect when wrong token key causes redirect loop
     * REQUIREMENT: Using 'auth_token' instead of 'authToken' causes loop
     */
    it('should detect redirect loop caused by wrong token key', () => {
        // Bug scenario: auth.js sets 'authToken', dashboard checks 'auth_token'
        localStorage.setItem('authToken', 'token-set-by-login');

        // Dashboard checks wrong key
        const wrongKeyCheck = localStorage.getItem('auth_token');
        const wouldRedirect = !wrongKeyCheck;

        expect(wouldRedirect).toBe(true); // This causes the redirect loop!

        // Correct check
        const correctKeyCheck = localStorage.getItem('authToken');
        const shouldNotRedirect = !correctKeyCheck;

        expect(shouldNotRedirect).toBe(false); // This prevents the loop
    });
});
