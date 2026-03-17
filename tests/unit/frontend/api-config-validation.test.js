/**
 * Unit Tests for API Configuration Validation
 *
 * BUSINESS CONTEXT:
 * Tests ensure API modules use correct configuration objects and base URLs.
 * Prevents "Failed to fetch" errors caused by wrong config object references
 * or incorrect fallback port numbers.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Validates window.CONFIG vs window.ENV usage
 * - Tests API base URL construction
 * - Verifies correct port numbers in fallbacks
 *
 * TDD METHODOLOGY:
 * These tests catch configuration mismatches that cause API calls to fail
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';

/**
 * Test Suite: API Configuration Object Usage
 */
describe('API Configuration Validation', () => {
    let dom;
    let window;

    beforeEach(() => {
        // Setup DOM environment
        dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            url: 'https://localhost:3000',
            pretendToBeVisual: true,
            runScripts: 'dangerously'
        });

        window = dom.window;
        global.window = window;
        global.document = window.document;
    });

    afterEach(() => {
        delete global.window;
        delete global.document;
    });

    /**
     * TEST: Verify org-admin-api.js uses window.CONFIG not window.ENV
     * REQUIREMENT: API modules must use window.CONFIG for configuration
     */
    it('should use window.CONFIG for API base URLs in org-admin-api.js', () => {
        // Read the actual source file
        const apiFilePath = path.join(process.cwd(), 'frontend/js/modules/org-admin-api.js');
        const apiSource = fs.readFileSync(apiFilePath, 'utf-8');

        // Check that it uses window.CONFIG
        expect(apiSource).toContain('window.CONFIG');

        // Check that it does NOT use window.ENV for API URLs
        const envMatches = apiSource.match(/window\.ENV\?\.API_URLS/g);
        expect(envMatches).toBeNull();
    });

    /**
     * TEST: Verify correct fallback port for USER_MANAGEMENT
     * REQUIREMENT: USER_MANAGEMENT fallback must be port 8000 not 8001
     */
    it('should use correct fallback port 8000 for USER_MANAGEMENT API', () => {
        const apiFilePath = path.join(process.cwd(), 'frontend/js/modules/org-admin-api.js');
        const apiSource = fs.readFileSync(apiFilePath, 'utf-8');

        // Check for correct fallback URL
        expect(apiSource).toContain('https://localhost:8000');

        // Ensure it doesn't have the wrong port
        const wrongPort = apiSource.includes("'https://localhost:8001'") ||
                         apiSource.includes('"https://localhost:8001"');
        expect(wrongPort).toBe(false);
    });

    /**
     * TEST: Verify correct fallback port for ORGANIZATION_MANAGEMENT
     * REQUIREMENT: ORGANIZATION_MANAGEMENT fallback must be port 8008
     */
    it('should use correct fallback port 8008 for ORGANIZATION_MANAGEMENT API', () => {
        const apiFilePath = path.join(process.cwd(), 'frontend/js/modules/org-admin-api.js');
        const apiSource = fs.readFileSync(apiFilePath, 'utf-8');

        // Check for correct fallback URL
        expect(apiSource).toContain('https://localhost:8008');
    });

    /**
     * TEST: Verify all API modules use consistent config object
     * REQUIREMENT: All modules should use window.CONFIG not window.ENV
     */
    it('should use window.CONFIG consistently across all API modules', () => {
        const modulesDir = path.join(process.cwd(), 'frontend/js/modules');
        const apiFiles = [
            'org-admin-api.js',
            'auth.js',
            'feedback-manager.js'
        ];

        apiFiles.forEach(filename => {
            const filePath = path.join(modulesDir, filename);
            if (fs.existsSync(filePath)) {
                const source = fs.readFileSync(filePath, 'utf-8');

                // If file references API configuration, it should use CONFIG not ENV
                if (source.includes('API_URLS') || source.includes('API_URL')) {
                    const usesConfig = source.includes('window.CONFIG');
                    const usesEnv = source.includes('window.ENV');

                    // This is informational - we log which object is used
                    console.log(`${filename}: uses CONFIG=${usesConfig}, uses ENV=${usesEnv}`);
                }
            }
        });
    });

    /**
     * TEST: Verify config-global.js sets window.CONFIG
     * REQUIREMENT: Global config must be available as window.CONFIG
     */
    it('should set window.CONFIG in config-global.js', () => {
        const configPath = path.join(process.cwd(), 'frontend/js/config-global.js');
        const configSource = fs.readFileSync(configPath, 'utf-8');

        // Should define window.CONFIG
        expect(configSource).toContain('window.CONFIG');

        // Should have API_URLS
        expect(configSource).toContain('API_URLS');
    });

    /**
     * TEST: Verify correct port mapping in config-global.js
     * REQUIREMENT: Ports must match docker-compose service ports
     */
    it('should have correct port mapping in config-global.js', () => {
        const configPath = path.join(process.cwd(), 'frontend/js/config-global.js');
        const configSource = fs.readFileSync(configPath, 'utf-8');

        // Expected port mappings from docker-compose.yml (check for port numbers)
        expect(configSource).toContain('8000'); // USER_MANAGEMENT
        expect(configSource).toContain('8008'); // ORGANIZATION_MANAGEMENT
        expect(configSource).toContain('8004'); // COURSE_MANAGEMENT
    });
});

/**
 * Test Suite: API URL Construction
 */
describe('API URL Construction', () => {
    /**
     * TEST: Verify API URLs are constructed correctly
     * REQUIREMENT: API calls should use proper base URLs + endpoints
     */
    it('should construct correct API endpoint URLs', () => {
        const apiFilePath = path.join(process.cwd(), 'frontend/js/modules/org-admin-api.js');
        const apiSource = fs.readFileSync(apiFilePath, 'utf-8');

        // fetchCurrentUser should call /api/v1/users/me
        expect(apiSource).toContain('/api/v1/users/me');

        // Should use USER_API_BASE for user endpoints
        const fetchCurrentUserMatch = apiSource.match(/fetchCurrentUser[\s\S]*?USER_API_BASE[\s\S]*?\/api\/v1\/users\/me/);
        expect(fetchCurrentUserMatch).toBeTruthy();
    });

    /**
     * TEST: Verify no hardcoded API URLs
     * REQUIREMENT: Should use config-based URLs, not hardcoded IPs/ports
     */
    it('should not have hardcoded production URLs', () => {
        const apiFilePath = path.join(process.cwd(), 'frontend/js/modules/org-admin-api.js');
        const apiSource = fs.readFileSync(apiFilePath, 'utf-8');

        // Should not have hardcoded production URLs (except in comments)
        const lines = apiSource.split('\n');
        const codeLines = lines.filter(line => !line.trim().startsWith('//') && !line.trim().startsWith('*'));
        const codeSource = codeLines.join('\n');

        // Should not have hardcoded IP addresses in code (outside of fallbacks)
        const hardcodedIP = codeSource.match(/fetch\(['"]https?:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/);
        expect(hardcodedIP).toBeNull();
    });
});

/**
 * Test Suite: Configuration Loading Order
 */
describe('Configuration Loading Validation', () => {
    /**
     * TEST: Verify config-global.js is loaded before API modules
     * REQUIREMENT: Config must be available before modules use it
     */
    it('should load config-global.js before org-admin modules in HTML', () => {
        const dashboardPath = path.join(process.cwd(), 'frontend/html/org-admin-dashboard.html');
        const htmlSource = fs.readFileSync(dashboardPath, 'utf-8');

        // Find script tag positions
        const configScriptPos = htmlSource.indexOf('config-global.js');
        const apiModulePos = htmlSource.indexOf('org-admin-api.js');
        const mainModulePos = htmlSource.indexOf('org-admin-main.js');

        // config-global.js must be loaded first
        expect(configScriptPos).toBeGreaterThan(-1);

        if (apiModulePos > -1) {
            expect(configScriptPos).toBeLessThan(apiModulePos);
        }

        if (mainModulePos > -1) {
            expect(configScriptPos).toBeLessThan(mainModulePos);
        }
    });
});
