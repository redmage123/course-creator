/**
 * Redux Hooks Unit Tests
 *
 * BUSINESS CONTEXT:
 * Tests the typed Redux hooks (useAppDispatch and useAppSelector) to ensure proper
 * TypeScript integration with the Redux store. Validates that hooks provide correct
 * type inference and work correctly with React components.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests useAppDispatch for typed dispatch functionality
 * - Tests useAppSelector for typed state selection
 * - Validates type safety with TypeScript
 * - Tests hooks within React component context
 * - Uses @testing-library/react for component testing
 * - Uses vitest for test execution and assertions
 *
 * WHY THIS APPROACH:
 * - Hook tests ensure TypeScript integration works correctly
 * - Component-based tests validate real-world usage
 * - Type safety tests catch TypeScript errors early
 * - Follows React Testing Library best practices
 * - Ensures hooks work with Redux Toolkit patterns
 *
 * TEST COVERAGE:
 * - useAppDispatch dispatches actions correctly
 * - useAppDispatch has correct TypeScript types
 * - useAppSelector selects state correctly
 * - useAppSelector has correct TypeScript types
 * - Hooks work with all store slices
 * - Hooks work in component lifecycle
 * - Re-render behavior on state changes
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { createElement, type ReactNode } from 'react';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import authReducer, { loginSuccess, logout } from '../../../store/slices/authSlice';
import userReducer, { setUserProfile, clearUser } from '../../../store/slices/userSlice';
import uiReducer, { addNotification, toggleSidebar } from '../../../store/slices/uiSlice';

/**
 * TEST HELPER: Create test store
 *
 * BUSINESS REQUIREMENT:
 * Tests need isolated Redux store instances for proper test isolation.
 *
 * TECHNICAL IMPLEMENTATION:
 * Factory function to create fresh store for each test.
 */
const createTestStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer,
      user: userReducer,
      ui: uiReducer,
    },
  });
};

/**
 * TEST HELPER: Create wrapper component with Provider
 *
 * BUSINESS REQUIREMENT:
 * Hooks must be tested within React context with Redux Provider.
 *
 * TECHNICAL IMPLEMENTATION:
 * Creates wrapper component with store for renderHook utility.
 * Uses createElement instead of JSX to avoid TypeScript JSX configuration issues in tests.
 */
const createWrapper = (store: ReturnType<typeof createTestStore>) => {
  return ({ children }: { children: ReactNode }) =>
    createElement(Provider, { store }, children);
};

describe('Redux Hooks', () => {
  let store: ReturnType<typeof createTestStore>;

  beforeEach(() => {
    store = createTestStore();
  });

  /**
   * USE APP DISPATCH TESTS
   *
   * BUSINESS REQUIREMENT:
   * Components need type-safe action dispatching.
   *
   * TEST COVERAGE:
   * - Dispatch auth actions
   * - Dispatch user actions
   * - Dispatch UI actions
   * - Action effects on state
   * - Type safety validation
   */
  describe('useAppDispatch', () => {
    it('should dispatch auth actions correctly', () => {
      const { result } = renderHook(() => useAppDispatch(), {
        wrapper: createWrapper(store),
      });

      const dispatch = result.current;

      act(() => {
        dispatch(
          loginSuccess({
            token: 'test-token',
            role: 'student',
            userId: 'user-123',
            expiresAt: Date.now() + 3600000,
          })
        );
      });

      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.token).toBe('test-token');
      expect(authState.userId).toBe('user-123');
    });

    it('should dispatch user actions correctly', () => {
      const { result } = renderHook(() => useAppDispatch(), {
        wrapper: createWrapper(store),
      });

      const dispatch = result.current;

      act(() => {
        dispatch(
          setUserProfile({
            id: 'user-456',
            username: 'testuser',
            email: 'test@example.com',
            role: 'instructor',
          })
        );
      });

      const userState = store.getState().user;
      expect(userState.profile).not.toBe(null);
      expect(userState.profile?.username).toBe('testuser');
    });

    it('should dispatch UI actions correctly', () => {
      const { result } = renderHook(() => useAppDispatch(), {
        wrapper: createWrapper(store),
      });

      const dispatch = result.current;

      act(() => {
        dispatch(
          addNotification({
            type: 'success',
            message: 'Test notification',
          })
        );
      });

      const uiState = store.getState().ui;
      expect(uiState.notifications).toHaveLength(1);
      expect(uiState.notifications[0].message).toBe('Test notification');
    });

    it('should dispatch multiple actions sequentially', () => {
      const { result } = renderHook(() => useAppDispatch(), {
        wrapper: createWrapper(store),
      });

      const dispatch = result.current;

      act(() => {
        // Login
        dispatch(
          loginSuccess({
            token: 'token',
            role: 'student',
            userId: 'user-1',
            expiresAt: Date.now() + 3600000,
          })
        );

        // Set profile
        dispatch(
          setUserProfile({
            id: 'user-1',
            username: 'student1',
            email: 'student@example.com',
            role: 'student',
          })
        );

        // Toggle sidebar
        dispatch(toggleSidebar());
      });

      const state = store.getState();
      expect(state.auth.isAuthenticated).toBe(true);
      expect(state.user.profile?.username).toBe('student1');
      expect(state.ui.sidebarOpen).toBe(false);
    });

    it('should return same dispatch function reference', () => {
      const { result, rerender } = renderHook(() => useAppDispatch(), {
        wrapper: createWrapper(store),
      });

      const firstDispatch = result.current;
      rerender();
      const secondDispatch = result.current;

      expect(firstDispatch).toBe(secondDispatch);
    });

    it('should dispatch logout action', () => {
      const { result } = renderHook(() => useAppDispatch(), {
        wrapper: createWrapper(store),
      });

      const dispatch = result.current;

      // First login
      act(() => {
        dispatch(
          loginSuccess({
            token: 'token',
            role: 'student',
            userId: 'user-1',
            expiresAt: Date.now() + 3600000,
          })
        );
      });

      expect(store.getState().auth.isAuthenticated).toBe(true);

      // Then logout
      act(() => {
        dispatch(logout());
      });

      expect(store.getState().auth.isAuthenticated).toBe(false);
      expect(store.getState().auth.token).toBe(null);
    });
  });

  /**
   * USE APP SELECTOR TESTS
   *
   * BUSINESS REQUIREMENT:
   * Components need type-safe state selection.
   *
   * TEST COVERAGE:
   * - Select auth state
   * - Select user state
   * - Select UI state
   * - Select nested properties
   * - Re-render on state changes
   * - Type safety validation
   */
  describe('useAppSelector', () => {
    it('should select auth state correctly', () => {
      const { result } = renderHook(
        () => useAppSelector((state) => state.auth),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBe(null);
      expect(result.current.userId).toBe(null);
    });

    it('should select user state correctly', () => {
      const { result } = renderHook(
        () => useAppSelector((state) => state.user),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current.profile).toBe(null);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(null);
    });

    it('should select UI state correctly', () => {
      const { result } = renderHook(() => useAppSelector((state) => state.ui), {
        wrapper: createWrapper(store),
      });

      expect(result.current.sidebarOpen).toBe(true);
      expect(result.current.notifications).toEqual([]);
      expect(result.current.activeModal).toBe(null);
      expect(result.current.globalLoading).toBe(false);
    });

    it('should select nested auth properties', () => {
      const { result } = renderHook(
        () => ({
          isAuthenticated: useAppSelector((state) => state.auth.isAuthenticated),
          token: useAppSelector((state) => state.auth.token),
          role: useAppSelector((state) => state.auth.role),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBe(null);
      expect(result.current.role).toBe(null);
    });

    it('should select nested user properties', () => {
      const { result } = renderHook(
        () => ({
          username: useAppSelector((state) => state.user.profile?.username),
          email: useAppSelector((state) => state.user.profile?.email),
          isLoading: useAppSelector((state) => state.user.isLoading),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current.username).toBeUndefined();
      expect(result.current.email).toBeUndefined();
      expect(result.current.isLoading).toBe(false);
    });

    it('should select nested UI properties', () => {
      const { result } = renderHook(
        () => ({
          sidebarOpen: useAppSelector((state) => state.ui.sidebarOpen),
          notificationCount: useAppSelector((state) => state.ui.notifications.length),
          activeModal: useAppSelector((state) => state.ui.activeModal),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current.sidebarOpen).toBe(true);
      expect(result.current.notificationCount).toBe(0);
      expect(result.current.activeModal).toBe(null);
    });

    it('should re-render when auth state changes', () => {
      const { result, rerender } = renderHook(
        () => useAppSelector((state) => state.auth.isAuthenticated),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current).toBe(false);

      act(() => {
        store.dispatch(
          loginSuccess({
            token: 'token',
            role: 'student',
            userId: 'user-1',
            expiresAt: Date.now() + 3600000,
          })
        );
      });

      rerender();
      expect(result.current).toBe(true);
    });

    it('should re-render when user state changes', () => {
      const { result, rerender } = renderHook(
        () => useAppSelector((state) => state.user.profile?.username),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current).toBeUndefined();

      act(() => {
        store.dispatch(
          setUserProfile({
            id: 'user-1',
            username: 'newuser',
            email: 'new@example.com',
            role: 'student',
          })
        );
      });

      rerender();
      expect(result.current).toBe('newuser');
    });

    it('should re-render when UI state changes', () => {
      const { result, rerender } = renderHook(
        () => useAppSelector((state) => state.ui.notifications.length),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current).toBe(0);

      act(() => {
        store.dispatch(
          addNotification({
            type: 'info',
            message: 'Test',
          })
        );
      });

      rerender();
      expect(result.current).toBe(1);

      act(() => {
        store.dispatch(
          addNotification({
            type: 'success',
            message: 'Test 2',
          })
        );
      });

      rerender();
      expect(result.current).toBe(2);
    });

    it('should only re-render when selected state changes', () => {
      let renderCount = 0;

      const { result } = renderHook(
        () => {
          renderCount++;
          return useAppSelector((state) => state.auth.isAuthenticated);
        },
        {
          wrapper: createWrapper(store),
        }
      );

      const initialRenderCount = renderCount;
      expect(result.current).toBe(false);

      // Change user state (not auth state) - should NOT cause re-render
      act(() => {
        store.dispatch(
          setUserProfile({
            id: 'user-1',
            username: 'test',
            email: 'test@example.com',
            role: 'student',
          })
        );
      });

      // renderCount should not increase because auth state didn't change
      expect(renderCount).toBe(initialRenderCount);

      // Change auth state - SHOULD cause re-render
      act(() => {
        store.dispatch(
          loginSuccess({
            token: 'token',
            role: 'student',
            userId: 'user-1',
            expiresAt: Date.now() + 3600000,
          })
        );
      });

      // Now renderCount should increase
      expect(renderCount).toBe(initialRenderCount + 1);
      expect(result.current).toBe(true);
    });
  });

  /**
   * INTEGRATION TESTS
   *
   * BUSINESS REQUIREMENT:
   * Hooks must work together in realistic component scenarios.
   *
   * TEST COVERAGE:
   * - Using both hooks together
   * - Complex state selection
   * - Multiple dispatch operations
   * - State synchronization
   */
  describe('hooks integration', () => {
    it('should use dispatch and selector together', () => {
      const { result } = renderHook(
        () => ({
          dispatch: useAppDispatch(),
          isAuthenticated: useAppSelector((state) => state.auth.isAuthenticated),
          username: useAppSelector((state) => state.user.profile?.username),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.username).toBeUndefined();

      act(() => {
        result.current.dispatch(
          loginSuccess({
            token: 'token',
            role: 'instructor',
            userId: 'user-1',
            expiresAt: Date.now() + 3600000,
          })
        );

        result.current.dispatch(
          setUserProfile({
            id: 'user-1',
            username: 'instructor1',
            email: 'instructor@example.com',
            role: 'instructor',
          })
        );
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.username).toBe('instructor1');
    });

    it('should handle complete login workflow', () => {
      const { result } = renderHook(
        () => ({
          dispatch: useAppDispatch(),
          auth: useAppSelector((state) => state.auth),
          user: useAppSelector((state) => state.user),
          ui: useAppSelector((state) => state.ui),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      // Perform login workflow
      act(() => {
        // Dispatch login
        result.current.dispatch(
          loginSuccess({
            token: 'jwt-token-abc',
            role: 'org_admin',
            userId: 'user-org-admin',
            organizationId: 'org-123',
            expiresAt: Date.now() + 3600000,
          })
        );

        // Set user profile
        result.current.dispatch(
          setUserProfile({
            id: 'user-org-admin',
            username: 'orgadmin',
            email: 'admin@org.com',
            role: 'org_admin',
            organizationId: 'org-123',
            organizationName: 'Test Organization',
          })
        );

        // Show success notification
        result.current.dispatch(
          addNotification({
            type: 'success',
            message: 'Login successful',
          })
        );
      });

      // Verify complete state
      expect(result.current.auth.isAuthenticated).toBe(true);
      expect(result.current.auth.role).toBe('org_admin');
      expect(result.current.user.profile?.username).toBe('orgadmin');
      expect(result.current.ui.notifications).toHaveLength(1);
    });

    it('should handle complete logout workflow', () => {
      const { result } = renderHook(
        () => ({
          dispatch: useAppDispatch(),
          auth: useAppSelector((state) => state.auth),
          user: useAppSelector((state) => state.user),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      // First login
      act(() => {
        result.current.dispatch(
          loginSuccess({
            token: 'token',
            role: 'student',
            userId: 'user-1',
            expiresAt: Date.now() + 3600000,
          })
        );

        result.current.dispatch(
          setUserProfile({
            id: 'user-1',
            username: 'student',
            email: 'student@example.com',
            role: 'student',
          })
        );
      });

      expect(result.current.auth.isAuthenticated).toBe(true);
      expect(result.current.user.profile).not.toBe(null);

      // Then logout
      act(() => {
        result.current.dispatch(logout());
        result.current.dispatch(clearUser());
      });

      expect(result.current.auth.isAuthenticated).toBe(false);
      expect(result.current.auth.token).toBe(null);
      expect(result.current.user.profile).toBe(null);
    });

    it('should select derived state correctly', () => {
      const { result } = renderHook(
        () => ({
          dispatch: useAppDispatch(),
          hasNotifications: useAppSelector((state) => state.ui.notifications.length > 0),
          hasProfile: useAppSelector((state) => state.user.profile !== null),
          isLoggedIn: useAppSelector((state) => state.auth.isAuthenticated),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      expect(result.current.hasNotifications).toBe(false);
      expect(result.current.hasProfile).toBe(false);
      expect(result.current.isLoggedIn).toBe(false);

      act(() => {
        result.current.dispatch(
          addNotification({
            type: 'info',
            message: 'Test',
          })
        );

        result.current.dispatch(
          setUserProfile({
            id: 'user-1',
            username: 'test',
            email: 'test@example.com',
            role: 'student',
          })
        );

        result.current.dispatch(
          loginSuccess({
            token: 'token',
            role: 'student',
            userId: 'user-1',
            expiresAt: Date.now() + 3600000,
          })
        );
      });

      expect(result.current.hasNotifications).toBe(true);
      expect(result.current.hasProfile).toBe(true);
      expect(result.current.isLoggedIn).toBe(true);
    });
  });

  /**
   * TYPE SAFETY TESTS
   *
   * BUSINESS REQUIREMENT:
   * TypeScript must provide correct type inference.
   *
   * TEST COVERAGE:
   * - Dispatch type inference
   * - Selector type inference
   * - State type safety
   */
  describe('type safety', () => {
    it('should infer dispatch type correctly', () => {
      const { result } = renderHook(() => useAppDispatch(), {
        wrapper: createWrapper(store),
      });

      const dispatch = result.current;

      // TypeScript should allow valid actions
      act(() => {
        dispatch(logout());
        dispatch(clearUser());
        dispatch(toggleSidebar());
      });

      // No TypeScript errors expected
      expect(typeof dispatch).toBe('function');
    });

    it('should infer selector return type correctly', () => {
      const { result } = renderHook(
        () => ({
          // TypeScript should infer these types correctly
          isAuth: useAppSelector((state) => state.auth.isAuthenticated),
          username: useAppSelector((state) => state.user.profile?.username),
          notifCount: useAppSelector((state) => state.ui.notifications.length),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      // Type assertions to verify TypeScript inference
      const isAuthBool: boolean = result.current.isAuth;
      const usernameStr: string | undefined = result.current.username;
      const countNum: number = result.current.notifCount;

      expect(typeof isAuthBool).toBe('boolean');
      expect(typeof countNum).toBe('number');
    });

    it('should work with all state slices', () => {
      const { result } = renderHook(
        () => ({
          auth: useAppSelector((state) => state.auth),
          user: useAppSelector((state) => state.user),
          ui: useAppSelector((state) => state.ui),
        }),
        {
          wrapper: createWrapper(store),
        }
      );

      // Verify all slices accessible
      expect(result.current.auth).toBeDefined();
      expect(result.current.user).toBeDefined();
      expect(result.current.ui).toBeDefined();

      // Verify correct structure
      expect(result.current.auth).toHaveProperty('isAuthenticated');
      expect(result.current.user).toHaveProperty('profile');
      expect(result.current.ui).toHaveProperty('sidebarOpen');
    });
  });
});
