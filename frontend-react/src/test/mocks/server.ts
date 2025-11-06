/**
 * MSW Server Setup for Tests
 *
 * BUSINESS CONTEXT:
 * Configures Mock Service Worker for Node.js test environment.
 * Intercepts network requests during tests without modifying service code.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Creates MSW server instance with handlers
 * - Integrates with Vitest test lifecycle
 * - Provides clean API mocking without service mocking
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Create MSW server with default handlers
export const server = setupServer(...handlers);
