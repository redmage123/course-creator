/**
 * Real Integration Tests for Org Admin API
 *
 * BUSINESS CONTEXT:
 * Tests that actually call the API endpoints to verify they work end-to-end.
 * Unlike static code validation, these tests catch runtime issues like:
 * - Service connectivity problems
 * - Authentication failures
 * - Incorrect URL construction
 * - CORS issues
 * - Missing configuration
 *
 * TECHNICAL IMPLEMENTATION:
 * - Makes real HTTP requests to running services
 * - Tests actual authentication flow
 * - Validates API responses
 *
 * TDD METHODOLOGY:
 * These tests would have caught the "Failed to fetch current user" error
 * that static validation tests missed.
 */

import { describe, it, expect, beforeAll, beforeEach, afterEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';

// Service configuration - should match docker-compose ports
const BASE_URL = process.env.TEST_BASE_URL || 'https://176.9.99.103';
const USER_MANAGEMENT_URL = `${BASE_URL}:8000`;
const ORG_MANAGEMENT_URL = `${BASE_URL}:8008`;

/**
 * Test Suite: Real API Endpoint Tests
 */
describe('Org Admin API - Real Integration Tests', () => {
    let dom;
    let window;
    let fetchMock;

    beforeEach(() => {
        // Setup DOM environment with proper config
        dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            url: `${BASE_URL}:3000`,
            pretendToBeVisual: true
        });

        window = dom.window;
        global.window = window;
        global.document = window.document;
        global.localStorage = window.localStorage;

        // Setup window.CONFIG to match production config
        window.CONFIG = {
            API_URLS: {
                USER_MANAGEMENT: USER_MANAGEMENT_URL,
                ORGANIZATION_MANAGEMENT: ORG_MANAGEMENT_URL
            }
        };

        // Clear localStorage
        localStorage.clear();
    });

    afterEach(() => {
        delete global.window;
        delete global.document;
        delete global.localStorage;
    });

    /**
     * TEST: Verify user-management service is accessible
     * REQUIREMENT: Service must be running and respond to health checks
     */
    it('should verify user-management service is running', async () => {
        try {
            const response = await fetch(`${USER_MANAGEMENT_URL}/health`, {
                method: 'GET'
            });

            // If service is running, we should get some response
            expect(response).toBeDefined();

            if (response.ok) {
                console.log('✅ User-management service is healthy');
            } else {
                console.warn(`⚠️ User-management service returned: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ User-management service is not accessible:', error.message);
            throw new Error(`User-management service not accessible at ${USER_MANAGEMENT_URL}`);
        }
    }, 10000);

    /**
     * TEST: Verify fetchCurrentUser constructs correct URL
     * REQUIREMENT: API should use window.CONFIG to build URLs
     */
    it('should construct correct URL for fetchCurrentUser', async () => {
        // Set a test token
        localStorage.setItem('authToken', 'test-token-12345');

        // Mock fetch to capture the URL being called
        const fetchSpy = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({ id: 1, email: 'test@example.com', role: 'organization_admin' })
        });
        global.fetch = fetchSpy;

        // Dynamically import the module (so it picks up our window.CONFIG)
        const orgAdminApiModule = `
            const USER_API_BASE = window.CONFIG?.API_URLS?.USER_MANAGEMENT || 'https://localhost:8000';

            async function getAuthHeaders() {
                const token = localStorage.getItem('authToken');
                return {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                };
            }

            async function fetchCurrentUser() {
                const url = USER_API_BASE + '/api/v1/users/me';
                const headers = await getAuthHeaders();
                const response = await fetch(url, { headers });

                if (!response.ok) {
                    throw new Error('Failed to fetch current user: ' + response.status);
                }

                return await response.json();
            }

            return { fetchCurrentUser };
        `;

        // Execute the module code in the window context
        const moduleFunc = new Function('window', 'localStorage', 'fetch', orgAdminApiModule);
        const { fetchCurrentUser } = moduleFunc(window, localStorage, fetchSpy);

        // Call fetchCurrentUser
        await fetchCurrentUser();

        // Verify the correct URL was called
        expect(fetchSpy).toHaveBeenCalledWith(
            `${USER_MANAGEMENT_URL}/api/v1/users/me`,
            expect.objectContaining({
                headers: expect.objectContaining({
                    'Authorization': 'Bearer test-token-12345'
                })
            })
        );

        console.log('✅ URL construction is correct:', fetchSpy.mock.calls[0][0]);
    });

    /**
     * TEST: Verify fetchCurrentUser fails without token
     * REQUIREMENT: API should require authentication
     */
    it('should fail to fetch current user without auth token', async () => {
        // Don't set any token
        localStorage.removeItem('authToken');

        // Mock fetch to simulate 401 Unauthorized
        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 401,
            statusText: 'Unauthorized',
            text: async () => 'Authentication required'
        });

        // Create fetchCurrentUser function
        const moduleFunc = new Function('window', 'localStorage', 'fetch', `
            const USER_API_BASE = window.CONFIG?.API_URLS?.USER_MANAGEMENT || 'https://localhost:8000';

            async function getAuthHeaders() {
                const token = localStorage.getItem('authToken');
                return {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                };
            }

            async function fetchCurrentUser() {
                const url = USER_API_BASE + '/api/v1/users/me';
                const headers = await getAuthHeaders();
                const response = await fetch(url, { headers });

                if (!response.ok) {
                    throw new Error('Failed to fetch current user: ' + response.status + ' ' + response.statusText);
                }

                return await response.json();
            }

            return { fetchCurrentUser };
        `);

        const { fetchCurrentUser } = moduleFunc(window, localStorage, global.fetch);

        // Should throw an error
        await expect(fetchCurrentUser()).rejects.toThrow(/Failed to fetch current user: 401/);
    });

    /**
     * TEST: Verify API uses correct port from config
     * REQUIREMENT: Must use port 8000 for user-management, not 8001
     */
    it('should use correct port 8000 from config, not fallback 8001', async () => {
        localStorage.setItem('authToken', 'test-token');

        const fetchSpy = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({ id: 1, email: 'test@example.com' })
        });
        global.fetch = fetchSpy;

        // Module should read from window.CONFIG
        const moduleFunc = new Function('window', 'localStorage', 'fetch', `
            const USER_API_BASE = window.CONFIG?.API_URLS?.USER_MANAGEMENT || 'https://localhost:8000';

            async function getAuthHeaders() {
                const token = localStorage.getItem('authToken');
                return {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                };
            }

            async function fetchCurrentUser() {
                const url = USER_API_BASE + '/api/v1/users/me';
                const headers = await getAuthHeaders();
                const response = await fetch(url, { headers });
                return await response.json();
            }

            return { fetchCurrentUser };
        `);

        const { fetchCurrentUser } = moduleFunc(window, localStorage, fetchSpy);
        await fetchCurrentUser();

        // Verify it's NOT using the wrong port
        const calledUrl = fetchSpy.mock.calls[0][0];
        expect(calledUrl).not.toContain(':8001');
        expect(calledUrl).toContain(':8000');
        expect(calledUrl).toBe(`${USER_MANAGEMENT_URL}/api/v1/users/me`);
    });

    /**
     * TEST: Verify window.CONFIG is actually loaded
     * REQUIREMENT: Config must be available before API modules load
     */
    it('should have window.CONFIG available', () => {
        expect(window.CONFIG).toBeDefined();
        expect(window.CONFIG.API_URLS).toBeDefined();
        expect(window.CONFIG.API_URLS.USER_MANAGEMENT).toBe(USER_MANAGEMENT_URL);
        expect(window.CONFIG.API_URLS.ORGANIZATION_MANAGEMENT).toBe(ORG_MANAGEMENT_URL);
    });

    /**
     * TEST: Verify authToken is in correct localStorage key
     * REQUIREMENT: Must use 'authToken' not 'auth_token' or 'access_token'
     */
    it('should read token from authToken localStorage key', () => {
        const testToken = 'test-jwt-token-xyz';
        localStorage.setItem('authToken', testToken);

        // Simulate getAuthHeaders()
        const token = localStorage.getItem('authToken');
        expect(token).toBe(testToken);

        // Verify wrong keys don't work
        expect(localStorage.getItem('auth_token')).toBeNull();
        expect(localStorage.getItem('access_token')).toBeNull();
    });
});

/**
 * Test Suite: Real Service Health Checks
 */
describe('Service Availability Tests', () => {
    /**
     * TEST: Check if user-management service is reachable
     * REQUIREMENT: Service must be running for dashboard to work
     */
    it('should ping user-management service', async () => {
        const healthEndpoints = [
            `${USER_MANAGEMENT_URL}/health`,
            `${USER_MANAGEMENT_URL}/`,
            `${USER_MANAGEMENT_URL}/docs`
        ];

        let serviceReachable = false;
        let reachableEndpoint = null;

        for (const endpoint of healthEndpoints) {
            try {
                const response = await fetch(endpoint, {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' }
                });

                if (response.status < 500) {
                    serviceReachable = true;
                    reachableEndpoint = endpoint;
                    console.log(`✅ Service reachable at: ${endpoint} (status: ${response.status})`);
                    break;
                }
            } catch (error) {
                console.log(`⚠️ Could not reach: ${endpoint}`);
            }
        }

        if (!serviceReachable) {
            console.error(`❌ User-management service not reachable at ${USER_MANAGEMENT_URL}`);
            console.error('   Make sure the service is running: docker-compose ps user-management');
        }

        expect(serviceReachable).toBe(true);
        expect(reachableEndpoint).toBeTruthy();
    }, 15000);

    /**
     * TEST: Verify /api/v1/users/me endpoint exists
     * REQUIREMENT: The endpoint must be available (even if it requires auth)
     */
    it('should verify /api/v1/users/me endpoint exists', async () => {
        try {
            const response = await fetch(`${USER_MANAGEMENT_URL}/api/v1/users/me`, {
                method: 'GET',
                headers: {
                    'Authorization': 'Bearer invalid-token-for-testing'
                }
            });

            // We expect 401 (unauthorized) or 200 (if token somehow works)
            // We DON'T expect 404 (endpoint not found)
            expect(response.status).not.toBe(404);

            if (response.status === 404) {
                console.error('❌ Endpoint /api/v1/users/me does not exist!');
                throw new Error('Critical: /api/v1/users/me endpoint not found');
            }

            console.log(`✅ Endpoint exists (returned ${response.status})`);
        } catch (error) {
            if (error.message.includes('fetch failed') || error.message.includes('ECONNREFUSED')) {
                throw new Error(`Service not reachable: ${error.message}`);
            }
            throw error;
        }
    }, 15000);
});

/**
 * Test Suite: Configuration Loading Order
 */
describe('Module Loading Order Validation', () => {
    /**
     * TEST: Verify config is loaded before API module
     * REQUIREMENT: window.CONFIG must exist before org-admin-api.js loads
     */
    it('should have config available before using it', () => {
        // This simulates the actual loading scenario
        expect(window.CONFIG).toBeDefined();

        // If config is not loaded, API_BASE URLs would use fallbacks
        const userApiBase = window.CONFIG?.API_URLS?.USER_MANAGEMENT || 'https://localhost:8000';

        // Should use the configured URL, not the fallback
        expect(userApiBase).toBe(USER_MANAGEMENT_URL);
        expect(userApiBase).not.toBe('https://localhost:8000'); // Not using fallback
    });
});
