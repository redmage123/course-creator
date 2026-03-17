/**
 * Test Utilities and Custom Render Functions
 *
 * BUSINESS CONTEXT:
 * Provides reusable test utilities for rendering React components with proper context providers.
 * Ensures all tests have access to Redux store, React Router, and React Query.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Custom render function wraps components with all necessary providers
 * - Mock store setup with configurable initial state
 * - Router integration for testing navigation
 * - User event simulation utilities
 *
 * WHY THIS APPROACH:
 * - Eliminates boilerplate in individual test files
 * - Ensures consistent test environment across all component tests
 * - Makes tests easier to write and maintain
 * - Provides realistic testing environment matching production
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HelmetProvider } from 'react-helmet-async';
import { configureStore, PreloadedState } from '@reduxjs/toolkit';
import type { RenderResult } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Import reducers
import authReducer from '../store/slices/authSlice';
import userReducer from '../store/slices/userSlice';
import uiReducer from '../store/slices/uiSlice';
import type { RootState } from '../store';

/**
 * CUSTOM RENDER OPTIONS INTERFACE
 *
 * BUSINESS REQUIREMENT:
 * Tests need to configure initial Redux state and routing context.
 *
 * TECHNICAL IMPLEMENTATION:
 * Extends React Testing Library's RenderOptions with Redux and Router configuration.
 */
interface ExtendedRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  /**
   * Initial Redux store state
   */
  preloadedState?: PreloadedState<RootState>;

  /**
   * Custom store instance (optional)
   */
  store?: ReturnType<typeof setupStore>;

  /**
   * Initial router entries for MemoryRouter
   */
  initialEntries?: string[];

  /**
   * Whether to use MemoryRouter (true) or BrowserRouter (false)
   * Default: true (MemoryRouter is better for tests)
   */
  useMemoryRouter?: boolean;
}

/**
 * SETUP TEST STORE
 *
 * BUSINESS REQUIREMENT:
 * Each test needs an isolated Redux store with configurable initial state.
 *
 * TECHNICAL IMPLEMENTATION:
 * Creates a new Redux store with all reducers and optional preloaded state.
 * If no auth state is preloaded, reads from localStorage to simulate page reload.
 *
 * WHY THIS APPROACH:
 * - Each test gets a fresh store (no state pollution)
 * - Preloaded state allows testing specific scenarios
 * - Matches production store configuration for realistic tests
 * - Simulates localStorage restoration on page reload
 *
 * @param preloadedState - Initial state for the store
 * @returns Configured Redux store instance
 */
export function setupStore(preloadedState?: PreloadedState<RootState>) {
  // If no auth state is provided, read from localStorage to simulate page reload
  let finalPreloadedState = preloadedState;

  if (!preloadedState?.auth) {
    const storedToken = localStorage.getItem('authToken');
    const storedRefreshToken = localStorage.getItem('refreshToken');
    const storedRole = localStorage.getItem('userRole');
    const storedUserId = localStorage.getItem('userId');
    const storedOrganizationId = localStorage.getItem('organizationId');

    // Only create auth state if there's data in localStorage
    if (storedToken || storedRole || storedUserId) {
      finalPreloadedState = {
        ...preloadedState,
        auth: {
          isAuthenticated: !!storedToken,
          token: storedToken,
          refreshToken: storedRefreshToken,
          role: storedRole as any,
          userId: storedUserId,
          organizationId: storedOrganizationId,
          expiresAt: null,
        },
      };
    }
  }

  return configureStore({
    reducer: {
      auth: authReducer,
      user: userReducer,
      ui: uiReducer,
    },
    preloadedState: finalPreloadedState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false, // Disable for tests
      }),
  });
}

/**
 * CREATE QUERY CLIENT FOR TESTS
 *
 * BUSINESS REQUIREMENT:
 * Components using React Query need a query client for data fetching.
 *
 * TECHNICAL IMPLEMENTATION:
 * Creates a query client with test-friendly configuration.
 *
 * WHY THIS APPROACH:
 * - Disables retries for faster test execution
 * - Disables refetch on mount/focus to prevent unexpected requests
 * - Reduces cache time for cleaner test isolation
 *
 * @returns Configured QueryClient instance
 */
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnMount: false,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
        staleTime: 0,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * CUSTOM RENDER WITH ALL PROVIDERS
 *
 * BUSINESS REQUIREMENT:
 * Components need to be tested with all context providers (Redux, Router, Query).
 *
 * TECHNICAL IMPLEMENTATION:
 * Wraps component with Redux Provider, Router, and Query Client before rendering.
 *
 * WHY THIS APPROACH:
 * - Matches production component hierarchy
 * - Eliminates provider boilerplate in tests
 * - Allows testing connected components naturally
 * - Supports navigation testing
 *
 * USAGE:
 * ```tsx
 * const { getByText } = renderWithProviders(<MyComponent />, {
 *   preloadedState: { auth: { isAuthenticated: true } },
 *   initialEntries: ['/dashboard']
 * });
 * ```
 *
 * @param ui - React component to render
 * @param options - Render options including store state and routing
 * @returns Render result with utilities
 */
export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState = {},
    store = setupStore(preloadedState),
    initialEntries = ['/'],
    useMemoryRouter = true,
    ...renderOptions
  }: ExtendedRenderOptions = {}
): RenderResult & { store: ReturnType<typeof setupStore> } {
  const queryClient = createTestQueryClient();

  /**
   * ALL PROVIDERS WRAPPER
   *
   * TECHNICAL IMPLEMENTATION:
   * Wraps component with Redux, Router, and React Query providers.
   * When useMemoryRouter is false, skips router wrapping (test provides its own).
   *
   * WHY THIS ORDER:
   * 1. Redux Provider (outermost) - state management
   * 2. Router - navigation context (optional if test provides own router)
   * 3. Query Client - data fetching
   * 4. Component (innermost) - actual component under test
   */
  function Wrapper({ children }: { children: React.ReactNode }) {
    const content = (
      <HelmetProvider>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </HelmetProvider>
    );

    // If test provides its own router (e.g., MemoryRouter with custom routes), skip router wrapping
    if (useMemoryRouter === false) {
      return (
        <Provider store={store}>
          {content}
        </Provider>
      );
    }

    // Otherwise, wrap with MemoryRouter for navigation testing
    return (
      <Provider store={store}>
        <MemoryRouter initialEntries={initialEntries}>
          {content}
        </MemoryRouter>
      </Provider>
    );
  }

  return {
    store,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

/**
 * WAIT FOR LOADING TO FINISH
 *
 * BUSINESS REQUIREMENT:
 * Tests need to wait for async operations (API calls, state updates) to complete.
 *
 * TECHNICAL IMPLEMENTATION:
 * Utility function that waits for loading indicators to disappear.
 *
 * WHY THIS APPROACH:
 * - Prevents race conditions in tests
 * - Ensures component is in stable state before assertions
 * - More reliable than arbitrary timeouts
 *
 * @param container - Container to search for loading indicators
 */
export async function waitForLoadingToFinish(container: HTMLElement) {
  const { waitForElementToBeRemoved, queryByRole, queryByTestId } = await import('@testing-library/react');

  // Wait for common loading indicators to disappear
  const loadingSpinner = queryByRole(container, 'status') || queryByTestId(container, 'loading');

  if (loadingSpinner) {
    await waitForElementToBeRemoved(loadingSpinner);
  }
}

/**
 * SETUP USER EVENT
 *
 * BUSINESS REQUIREMENT:
 * Tests need to simulate realistic user interactions (clicks, typing, etc.).
 *
 * TECHNICAL IMPLEMENTATION:
 * Creates a userEvent instance for simulating user interactions.
 *
 * WHY THIS APPROACH:
 * - userEvent is more realistic than fireEvent (handles focus, blur, etc.)
 * - Includes proper event sequencing
 * - Better simulates actual user behavior
 *
 * USAGE:
 * ```tsx
 * const user = setupUserEvent();
 * await user.click(button);
 * await user.type(input, 'test text');
 * ```
 *
 * @returns userEvent instance
 */
export function setupUserEvent() {
  return userEvent.setup();
}

/**
 * CREATE MOCK USER PROFILE
 *
 * BUSINESS REQUIREMENT:
 * Tests need realistic user data for authentication and authorization scenarios.
 *
 * TECHNICAL IMPLEMENTATION:
 * Factory function that creates user profile objects with sensible defaults.
 *
 * WHY THIS APPROACH:
 * - Consistent test data across all tests
 * - Easy to override specific fields for edge cases
 * - Matches production user structure
 *
 * @param overrides - Custom values to override defaults
 * @returns Mock user profile
 */
export function createMockUser(overrides: Partial<{
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'site_admin' | 'org_admin' | 'instructor' | 'student' | 'guest';
  organizationId: string;
  organizationName: string;
}> = {}) {
  return {
    id: 'user-123',
    username: 'testuser',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    role: 'student' as const,
    organizationId: 'org-123',
    organizationName: 'Test Organization',
    ...overrides,
  };
}

/**
 * CREATE MOCK AUTH STATE
 *
 * BUSINESS REQUIREMENT:
 * Tests need realistic authentication state for protected route testing.
 *
 * TECHNICAL IMPLEMENTATION:
 * Factory function that creates auth state objects.
 *
 * @param overrides - Custom values to override defaults
 * @returns Mock auth state
 */
export function createMockAuthState(overrides: Partial<{
  isAuthenticated: boolean;
  token: string | null;
  refreshToken: string | null;
  role: string | null;
  userId: string | null;
  organizationId: string | null;
  expiresAt: number | null;
}> = {}) {
  return {
    isAuthenticated: true,
    token: 'mock-jwt-token',
    refreshToken: 'mock-refresh-token',
    role: 'student',
    userId: 'user-123',
    organizationId: 'org-123',
    expiresAt: Date.now() + 3600000,
    ...overrides,
  };
}

/**
 * MOCK API RESPONSE HELPERS
 *
 * BUSINESS REQUIREMENT:
 * Tests need to mock API responses for service layer testing.
 *
 * TECHNICAL IMPLEMENTATION:
 * Helper functions for creating mock API responses.
 */
export const mockApiResponse = {
  /**
   * SUCCESS RESPONSE
   */
  success: function <T>(data: T) {
    return {
      data,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any,
    };
  },

  /**
   * ERROR RESPONSE
   */
  error: (message: string, status: number = 400) => ({
    response: {
      data: { message },
      status,
      statusText: 'Error',
      headers: {},
      config: {} as any,
    },
  }),
};

/**
 * EXPORT ALL TESTING UTILITIES
 *
 * BUSINESS REQUIREMENT:
 * Tests need convenient access to all testing utilities.
 *
 * TECHNICAL IMPLEMENTATION:
 * Re-export Testing Library utilities alongside custom utilities.
 */
export * from '@testing-library/react';
export { renderWithProviders as render };
