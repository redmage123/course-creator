/**
 * UI Slice Unit Tests
 *
 * BUSINESS CONTEXT:
 * Tests the UI state management slice to ensure proper handling of global UI state including
 * sidebar visibility, notifications, modals, and loading indicators. Validates state updates
 * for user interface operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests all action creators (toggleSidebar, setSidebarOpen, addNotification, removeNotification,
 *   clearNotifications, openModal, closeModal, setGlobalLoading)
 * - Validates reducer logic with notification management and modal state
 * - Tests notification ID generation and uniqueness
 * - Tests sidebar toggle behavior
 * - Verifies type safety and state immutability
 * - Uses vitest for test execution and assertions
 *
 * WHY THIS APPROACH:
 * - Comprehensive testing ensures UI state reliability
 * - Notification tests validate queue management
 * - Modal tests ensure single active modal constraint
 * - Sidebar tests validate responsive UI behavior
 * - Follows TDD principles with clear test structure
 *
 * TEST COVERAGE:
 * - Initial state verification
 * - Sidebar toggle and explicit setting
 * - Notification addition and removal
 * - Notification queue management
 * - Modal opening and closing
 * - Global loading state
 * - Edge cases (duplicate notifications, non-existent IDs)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import uiReducer, {
  toggleSidebar,
  setSidebarOpen,
  addNotification,
  removeNotification,
  clearNotifications,
  openModal,
  closeModal,
  setGlobalLoading,
  type NotificationType,
} from '../../../store/slices/uiSlice';

describe('uiSlice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * INITIAL STATE TESTS
   *
   * BUSINESS REQUIREMENT:
   * UI state must start with sensible defaults.
   *
   * TEST COVERAGE:
   * - Default sidebar open
   * - Empty notification queue
   * - No active modal
   * - Not loading initially
   */
  describe('initial state', () => {
    it('should return the initial state with default UI values', () => {
      const state = uiReducer(undefined, { type: '@@INIT' });

      expect(state).toEqual({
        sidebarOpen: true,
        notifications: [],
        activeModal: null,
        globalLoading: false,
      });
    });
  });

  /**
   * SIDEBAR TOGGLE TESTS
   *
   * BUSINESS REQUIREMENT:
   * Users can toggle sidebar visibility for responsive UI.
   *
   * TEST COVERAGE:
   * - Toggle from open to closed
   * - Toggle from closed to open
   * - Multiple toggles
   * - Other state preserved during toggle
   */
  describe('toggleSidebar', () => {
    it('should toggle sidebar from open to closed', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });
      expect(initialState.sidebarOpen).toBe(true);

      const state = uiReducer(initialState, toggleSidebar());

      expect(state.sidebarOpen).toBe(false);
    });

    it('should toggle sidebar from closed to open', () => {
      const closedState = uiReducer(
        uiReducer(undefined, { type: '@@INIT' }),
        setSidebarOpen(false)
      );
      expect(closedState.sidebarOpen).toBe(false);

      const state = uiReducer(closedState, toggleSidebar());

      expect(state.sidebarOpen).toBe(true);
    });

    it('should toggle sidebar multiple times correctly', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });
      expect(state.sidebarOpen).toBe(true);

      state = uiReducer(state, toggleSidebar());
      expect(state.sidebarOpen).toBe(false);

      state = uiReducer(state, toggleSidebar());
      expect(state.sidebarOpen).toBe(true);

      state = uiReducer(state, toggleSidebar());
      expect(state.sidebarOpen).toBe(false);
    });

    it('should not affect other UI state when toggling sidebar', () => {
      const stateWithModal = uiReducer(
        uiReducer(undefined, { type: '@@INIT' }),
        openModal('test-modal')
      );

      const state = uiReducer(stateWithModal, toggleSidebar());

      expect(state.sidebarOpen).toBe(false);
      expect(state.activeModal).toBe('test-modal');
      expect(state.notifications).toEqual([]);
    });
  });

  /**
   * SET SIDEBAR OPEN TESTS
   *
   * BUSINESS REQUIREMENT:
   * Explicit sidebar state setting for programmatic control.
   *
   * TEST COVERAGE:
   * - Set to true
   * - Set to false
   * - Idempotent setting
   */
  describe('setSidebarOpen', () => {
    it('should set sidebar to open', () => {
      const closedState = uiReducer(
        uiReducer(undefined, { type: '@@INIT' }),
        setSidebarOpen(false)
      );

      const state = uiReducer(closedState, setSidebarOpen(true));

      expect(state.sidebarOpen).toBe(true);
    });

    it('should set sidebar to closed', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });

      const state = uiReducer(initialState, setSidebarOpen(false));

      expect(state.sidebarOpen).toBe(false);
    });

    it('should be idempotent when setting to same state', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });
      expect(initialState.sidebarOpen).toBe(true);

      const state = uiReducer(initialState, setSidebarOpen(true));

      expect(state.sidebarOpen).toBe(true);
    });
  });

  /**
   * ADD NOTIFICATION TESTS
   *
   * BUSINESS REQUIREMENT:
   * System must display notifications to users with various types.
   *
   * TEST COVERAGE:
   * - Add single notification
   * - Add multiple notifications
   * - All notification types
   * - Auto-generated unique IDs
   * - Optional duration field
   */
  describe('addNotification', () => {
    it('should add a notification with auto-generated ID', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });

      const state = uiReducer(
        initialState,
        addNotification({
          type: 'success',
          message: 'Operation successful',
        })
      );

      expect(state.notifications).toHaveLength(1);
      expect(state.notifications[0]).toMatchObject({
        type: 'success',
        message: 'Operation successful',
      });
      expect(state.notifications[0].id).toBeDefined();
      expect(typeof state.notifications[0].id).toBe('string');
    });

    it('should add notification with duration', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });

      const state = uiReducer(
        initialState,
        addNotification({
          type: 'info',
          message: 'Info message',
          duration: 5000,
        })
      );

      expect(state.notifications[0]).toMatchObject({
        type: 'info',
        message: 'Info message',
        duration: 5000,
      });
    });

    it('should add multiple notifications to queue', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(
        state,
        addNotification({
          type: 'success',
          message: 'First notification',
        })
      );

      state = uiReducer(
        state,
        addNotification({
          type: 'error',
          message: 'Second notification',
        })
      );

      state = uiReducer(
        state,
        addNotification({
          type: 'warning',
          message: 'Third notification',
        })
      );

      expect(state.notifications).toHaveLength(3);
      expect(state.notifications[0].message).toBe('First notification');
      expect(state.notifications[1].message).toBe('Second notification');
      expect(state.notifications[2].message).toBe('Third notification');
    });

    it('should generate unique IDs for each notification', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(
        state,
        addNotification({
          type: 'info',
          message: 'Notification 1',
        })
      );

      state = uiReducer(
        state,
        addNotification({
          type: 'info',
          message: 'Notification 2',
        })
      );

      expect(state.notifications[0].id).not.toBe(state.notifications[1].id);
    });

    it('should handle all notification types', () => {
      const types: NotificationType[] = ['success', 'error', 'warning', 'info'];
      let state = uiReducer(undefined, { type: '@@INIT' });

      types.forEach((type) => {
        state = uiReducer(
          state,
          addNotification({
            type,
            message: `${type} message`,
          })
        );
      });

      expect(state.notifications).toHaveLength(4);
      types.forEach((type, index) => {
        expect(state.notifications[index].type).toBe(type);
      });
    });

    it('should handle empty message string', () => {
      const state = uiReducer(
        uiReducer(undefined, { type: '@@INIT' }),
        addNotification({
          type: 'info',
          message: '',
        })
      );

      expect(state.notifications[0].message).toBe('');
    });

    it('should handle very long messages', () => {
      const longMessage = 'A'.repeat(10000);
      const state = uiReducer(
        uiReducer(undefined, { type: '@@INIT' }),
        addNotification({
          type: 'info',
          message: longMessage,
        })
      );

      expect(state.notifications[0].message).toBe(longMessage);
      expect(state.notifications[0].message.length).toBe(10000);
    });
  });

  /**
   * REMOVE NOTIFICATION TESTS
   *
   * BUSINESS REQUIREMENT:
   * Users can dismiss notifications manually.
   *
   * TEST COVERAGE:
   * - Remove existing notification
   * - Remove non-existent notification (no error)
   * - Remove from multiple notifications
   * - Remove by correct ID
   */
  describe('removeNotification', () => {
    it('should remove notification by ID', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(
        state,
        addNotification({
          type: 'success',
          message: 'Test notification',
        })
      );

      const notificationId = state.notifications[0].id;
      expect(state.notifications).toHaveLength(1);

      state = uiReducer(state, removeNotification(notificationId));

      expect(state.notifications).toHaveLength(0);
    });

    it('should remove correct notification from multiple', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(
        state,
        addNotification({
          type: 'info',
          message: 'First',
        })
      );

      state = uiReducer(
        state,
        addNotification({
          type: 'info',
          message: 'Second',
        })
      );

      state = uiReducer(
        state,
        addNotification({
          type: 'info',
          message: 'Third',
        })
      );

      const secondId = state.notifications[1].id;
      expect(state.notifications).toHaveLength(3);

      state = uiReducer(state, removeNotification(secondId));

      expect(state.notifications).toHaveLength(2);
      expect(state.notifications[0].message).toBe('First');
      expect(state.notifications[1].message).toBe('Third');
    });

    it('should not error when removing non-existent notification ID', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(
        state,
        addNotification({
          type: 'info',
          message: 'Test',
        })
      );

      const originalLength = state.notifications.length;

      state = uiReducer(state, removeNotification('non-existent-id'));

      expect(state.notifications).toHaveLength(originalLength);
    });

    it('should handle removing from empty notifications', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });

      const state = uiReducer(initialState, removeNotification('any-id'));

      expect(state.notifications).toEqual([]);
    });
  });

  /**
   * CLEAR NOTIFICATIONS TESTS
   *
   * BUSINESS REQUIREMENT:
   * Clear all notifications at once.
   *
   * TEST COVERAGE:
   * - Clear multiple notifications
   * - Clear when already empty
   * - Other state preserved
   */
  describe('clearNotifications', () => {
    it('should clear all notifications', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      // Add multiple notifications
      state = uiReducer(
        state,
        addNotification({ type: 'success', message: 'First' })
      );
      state = uiReducer(
        state,
        addNotification({ type: 'error', message: 'Second' })
      );
      state = uiReducer(
        state,
        addNotification({ type: 'info', message: 'Third' })
      );

      expect(state.notifications).toHaveLength(3);

      state = uiReducer(state, clearNotifications());

      expect(state.notifications).toEqual([]);
    });

    it('should be idempotent when clearing empty notifications', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });

      const state = uiReducer(initialState, clearNotifications());

      expect(state.notifications).toEqual([]);
    });

    it('should not affect other UI state when clearing notifications', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(state, openModal('test-modal'));
      state = uiReducer(state, setSidebarOpen(false));
      state = uiReducer(
        state,
        addNotification({ type: 'info', message: 'Test' })
      );

      state = uiReducer(state, clearNotifications());

      expect(state.notifications).toEqual([]);
      expect(state.activeModal).toBe('test-modal');
      expect(state.sidebarOpen).toBe(false);
    });
  });

  /**
   * OPEN MODAL TESTS
   *
   * BUSINESS REQUIREMENT:
   * Display modals by name for user interactions.
   *
   * TEST COVERAGE:
   * - Open modal by name
   * - Replace active modal
   * - Modal name validation
   */
  describe('openModal', () => {
    it('should open modal by name', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });

      const state = uiReducer(initialState, openModal('login-modal'));

      expect(state.activeModal).toBe('login-modal');
    });

    it('should replace active modal when opening new one', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(state, openModal('first-modal'));
      expect(state.activeModal).toBe('first-modal');

      state = uiReducer(state, openModal('second-modal'));
      expect(state.activeModal).toBe('second-modal');
    });

    it('should handle various modal name formats', () => {
      const modalNames = [
        'simple',
        'kebab-case-modal',
        'camelCaseModal',
        'modal_with_underscores',
        'Modal123',
        'UPPERCASE_MODAL',
      ];

      modalNames.forEach((modalName) => {
        const state = uiReducer(uiReducer(undefined, { type: '@@INIT' }), openModal(modalName));
        expect(state.activeModal).toBe(modalName);
      });
    });

    it('should not affect other UI state when opening modal', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(state, setSidebarOpen(false));
      state = uiReducer(
        state,
        addNotification({ type: 'info', message: 'Test' })
      );

      state = uiReducer(state, openModal('test-modal'));

      expect(state.activeModal).toBe('test-modal');
      expect(state.sidebarOpen).toBe(false);
      expect(state.notifications).toHaveLength(1);
    });
  });

  /**
   * CLOSE MODAL TESTS
   *
   * BUSINESS REQUIREMENT:
   * Close active modal to return to normal view.
   *
   * TEST COVERAGE:
   * - Close active modal
   * - Close when no modal open
   * - Other state preserved
   */
  describe('closeModal', () => {
    it('should close active modal', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(state, openModal('test-modal'));
      expect(state.activeModal).toBe('test-modal');

      state = uiReducer(state, closeModal());
      expect(state.activeModal).toBe(null);
    });

    it('should be idempotent when no modal is open', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });
      expect(initialState.activeModal).toBe(null);

      const state = uiReducer(initialState, closeModal());
      expect(state.activeModal).toBe(null);
    });

    it('should not affect other UI state when closing modal', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(state, setSidebarOpen(false));
      state = uiReducer(
        state,
        addNotification({ type: 'success', message: 'Test' })
      );
      state = uiReducer(state, openModal('test-modal'));

      state = uiReducer(state, closeModal());

      expect(state.activeModal).toBe(null);
      expect(state.sidebarOpen).toBe(false);
      expect(state.notifications).toHaveLength(1);
    });
  });

  /**
   * GLOBAL LOADING TESTS
   *
   * BUSINESS REQUIREMENT:
   * Display global loading indicator for async operations.
   *
   * TEST COVERAGE:
   * - Set loading to true
   * - Set loading to false
   * - Loading state transitions
   */
  describe('setGlobalLoading', () => {
    it('should set global loading to true', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });

      const state = uiReducer(initialState, setGlobalLoading(true));

      expect(state.globalLoading).toBe(true);
    });

    it('should set global loading to false', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(state, setGlobalLoading(true));
      expect(state.globalLoading).toBe(true);

      state = uiReducer(state, setGlobalLoading(false));
      expect(state.globalLoading).toBe(false);
    });

    it('should not affect other UI state when setting loading', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(state, openModal('modal'));
      state = uiReducer(state, addNotification({ type: 'info', message: 'Test' }));
      state = uiReducer(state, setSidebarOpen(false));

      state = uiReducer(state, setGlobalLoading(true));

      expect(state.globalLoading).toBe(true);
      expect(state.activeModal).toBe('modal');
      expect(state.notifications).toHaveLength(1);
      expect(state.sidebarOpen).toBe(false);
    });
  });

  /**
   * STATE IMMUTABILITY TESTS
   *
   * BUSINESS REQUIREMENT:
   * Redux state must be immutable to ensure predictable updates.
   *
   * TEST COVERAGE:
   * - Reducers return new state objects
   * - Original state not mutated
   * - Notification arrays not shared
   */
  describe('state immutability', () => {
    it('should not mutate original state on addNotification', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });
      const originalState = { ...initialState };

      uiReducer(
        initialState,
        addNotification({ type: 'info', message: 'Test' })
      );

      expect(initialState).toEqual(originalState);
    });

    it('should create new notifications array on add', () => {
      const initialState = uiReducer(undefined, { type: '@@INIT' });
      const originalNotifications = initialState.notifications;

      const state = uiReducer(
        initialState,
        addNotification({ type: 'info', message: 'Test' })
      );

      expect(state.notifications).not.toBe(originalNotifications);
    });

    it('should create new notifications array on remove', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      state = uiReducer(
        state,
        addNotification({ type: 'info', message: 'Test' })
      );

      const notificationId = state.notifications[0].id;
      const originalNotifications = state.notifications;

      const newState = uiReducer(state, removeNotification(notificationId));

      expect(newState.notifications).not.toBe(originalNotifications);
    });
  });

  /**
   * WORKFLOW TESTS
   *
   * BUSINESS REQUIREMENT:
   * Common UI workflows must work correctly.
   *
   * TEST COVERAGE:
   * - Notification lifecycle
   * - Modal lifecycle
   * - Sidebar responsive behavior
   * - Complex multi-action workflows
   */
  describe('common workflows', () => {
    it('should handle notification lifecycle', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      // Show notification
      state = uiReducer(
        state,
        addNotification({
          type: 'success',
          message: 'Data saved successfully',
          duration: 3000,
        })
      );

      expect(state.notifications).toHaveLength(1);

      // Dismiss notification
      const notificationId = state.notifications[0].id;
      state = uiReducer(state, removeNotification(notificationId));

      expect(state.notifications).toHaveLength(0);
    });

    it('should handle modal workflow', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      // Open modal
      state = uiReducer(state, openModal('settings-modal'));
      expect(state.activeModal).toBe('settings-modal');

      // Close modal
      state = uiReducer(state, closeModal());
      expect(state.activeModal).toBe(null);
    });

    it('should handle responsive sidebar workflow', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });
      expect(state.sidebarOpen).toBe(true);

      // Mobile view - close sidebar
      state = uiReducer(state, setSidebarOpen(false));
      expect(state.sidebarOpen).toBe(false);

      // Desktop view - open sidebar
      state = uiReducer(state, setSidebarOpen(true));
      expect(state.sidebarOpen).toBe(true);
    });

    it('should handle complex multi-action workflow', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      // Start loading
      state = uiReducer(state, setGlobalLoading(true));

      // Open modal
      state = uiReducer(state, openModal('data-modal'));

      // Add notification
      state = uiReducer(
        state,
        addNotification({ type: 'info', message: 'Loading data...' })
      );

      // Close sidebar for space
      state = uiReducer(state, setSidebarOpen(false));

      // Verify all state updated correctly
      expect(state.globalLoading).toBe(true);
      expect(state.activeModal).toBe('data-modal');
      expect(state.notifications).toHaveLength(1);
      expect(state.sidebarOpen).toBe(false);

      // Complete loading
      state = uiReducer(state, setGlobalLoading(false));

      // Clear loading notification
      state = uiReducer(state, clearNotifications());

      // Add success notification
      state = uiReducer(
        state,
        addNotification({ type: 'success', message: 'Data loaded' })
      );

      // Close modal
      state = uiReducer(state, closeModal());

      // Final state check
      expect(state.globalLoading).toBe(false);
      expect(state.activeModal).toBe(null);
      expect(state.notifications).toHaveLength(1);
      expect(state.notifications[0].type).toBe('success');
    });
  });

  /**
   * EDGE CASE TESTS
   *
   * BUSINESS REQUIREMENT:
   * Handle unusual but valid scenarios gracefully.
   *
   * TEST COVERAGE:
   * - Empty modal names
   * - Special characters in modal names
   * - Very large notification queues
   * - Rapid state changes
   */
  describe('edge cases', () => {
    it('should handle empty modal name', () => {
      const state = uiReducer(uiReducer(undefined, { type: '@@INIT' }), openModal(''));

      expect(state.activeModal).toBe('');
    });

    it('should handle special characters in modal names', () => {
      const specialNames = [
        'modal!@#$%',
        'modal with spaces',
        'モーダル',
        'modal\nwith\nnewlines',
      ];

      specialNames.forEach((name) => {
        const state = uiReducer(uiReducer(undefined, { type: '@@INIT' }), openModal(name));
        expect(state.activeModal).toBe(name);
      });
    });

    it('should handle very large notification queue', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      // Add 100 notifications
      for (let i = 0; i < 100; i++) {
        state = uiReducer(
          state,
          addNotification({
            type: 'info',
            message: `Notification ${i}`,
          })
        );
      }

      expect(state.notifications).toHaveLength(100);

      // Clear all
      state = uiReducer(state, clearNotifications());
      expect(state.notifications).toHaveLength(0);
    });

    it('should handle rapid sidebar toggles', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });
      const initialState = state.sidebarOpen; // true

      for (let i = 0; i < 50; i++) {
        state = uiReducer(state, toggleSidebar());
      }

      // Should be back to initial state after even number of toggles (50)
      // Initial: true -> 50 toggles (even) -> true
      expect(state.sidebarOpen).toBe(initialState);
    });

    it('should handle rapid modal changes', () => {
      let state = uiReducer(undefined, { type: '@@INIT' });

      for (let i = 0; i < 10; i++) {
        state = uiReducer(state, openModal(`modal-${i}`));
      }

      // Should have last modal open
      expect(state.activeModal).toBe('modal-9');
    });
  });

  /**
   * TYPE SAFETY TESTS
   *
   * BUSINESS REQUIREMENT:
   * TypeScript types must prevent invalid state.
   *
   * TEST COVERAGE:
   * - Action creator exports
   * - Type inference validation
   * - NotificationType enum
   */
  describe('type safety', () => {
    it('should export all action creators', () => {
      expect(typeof toggleSidebar).toBe('function');
      expect(typeof setSidebarOpen).toBe('function');
      expect(typeof addNotification).toBe('function');
      expect(typeof removeNotification).toBe('function');
      expect(typeof clearNotifications).toBe('function');
      expect(typeof openModal).toBe('function');
      expect(typeof closeModal).toBe('function');
      expect(typeof setGlobalLoading).toBe('function');
    });

    it('should handle all NotificationType values', () => {
      const types: NotificationType[] = ['success', 'error', 'warning', 'info'];

      types.forEach((type) => {
        const state = uiReducer(
          uiReducer(undefined, { type: '@@INIT' }),
          addNotification({
            type,
            message: `Test ${type}`,
          })
        );

        expect(state.notifications[0].type).toBe(type);
      });
    });
  });
});
