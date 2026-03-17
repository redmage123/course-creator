/**
 * User Slice Unit Tests
 *
 * BUSINESS CONTEXT:
 * Tests the user profile state management slice to ensure proper handling of user data,
 * loading states, and error management. Validates state updates for profile operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests all action creators (setUserProfile, updateUserProfile, setLoading, setError, clearUser)
 * - Validates reducer logic with partial updates and error scenarios
 * - Tests loading state management
 * - Tests error handling and state clearing
 * - Verifies type safety and state immutability
 * - Uses vitest for test execution and assertions
 *
 * WHY THIS APPROACH:
 * - Comprehensive testing ensures user data integrity
 * - Loading state tests ensure proper UI feedback
 * - Error handling tests prevent data corruption
 * - Partial update tests validate flexible profile management
 * - Follows TDD principles with clear test structure
 *
 * TEST COVERAGE:
 * - Initial state verification
 * - Setting complete user profile
 * - Partial profile updates
 * - Loading state management
 * - Error state handling
 * - User data clearing
 * - Edge cases (null values, partial data)
 */

import { describe, it, expect, beforeEach } from 'vitest';
import userReducer, {
  setUserProfile,
  updateUserProfile,
  setLoading,
  setError,
  clearUser,
} from '../../../store/slices/userSlice';
import type { UserRole } from '../../../store/slices/authSlice';

/**
 * TEST HELPER: Create mock user profile
 *
 * BUSINESS REQUIREMENT:
 * Tests need realistic user profile data for validation.
 *
 * TECHNICAL IMPLEMENTATION:
 * Factory function to create complete or partial user profiles.
 */
const createMockProfile = (overrides = {}) => ({
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  role: 'student' as UserRole,
  organizationId: 'org-456',
  organizationName: 'Test Organization',
  avatar: 'https://example.com/avatar.jpg',
  preferences: { theme: 'dark', language: 'en' },
  ...overrides,
});

describe('userSlice', () => {
  /**
   * INITIAL STATE TESTS
   *
   * BUSINESS REQUIREMENT:
   * User state must start with no profile loaded.
   *
   * TEST COVERAGE:
   * - Default empty profile state
   * - Initial loading and error states
   */
  describe('initial state', () => {
    it('should return the initial state with no user profile', () => {
      const state = userReducer(undefined, { type: '@@INIT' });

      expect(state).toEqual({
        profile: null,
        isLoading: false,
        error: null,
      });
    });
  });

  /**
   * SET USER PROFILE ACTION TESTS
   *
   * BUSINESS REQUIREMENT:
   * Setting a user profile must completely replace current profile data.
   *
   * TEST COVERAGE:
   * - Complete profile with all fields
   * - Profile with optional fields omitted
   * - Error clearing on successful profile set
   * - Multiple role types
   */
  describe('setUserProfile', () => {
    it('should set user profile with all fields', () => {
      const initialState = userReducer(undefined, { type: '@@INIT' });
      const profile = createMockProfile();

      const state = userReducer(initialState, setUserProfile(profile));

      expect(state.profile).toEqual(profile);
      expect(state.error).toBe(null);
    });

    it('should set user profile with minimal required fields', () => {
      const initialState = userReducer(undefined, { type: '@@INIT' });
      const minimalProfile = {
        id: 'user-789',
        username: 'minimal',
        email: 'minimal@example.com',
        role: 'guest' as UserRole,
      };

      const state = userReducer(initialState, setUserProfile(minimalProfile));

      expect(state.profile).toEqual(minimalProfile);
      expect(state.profile?.firstName).toBeUndefined();
      expect(state.profile?.lastName).toBeUndefined();
      expect(state.profile?.organizationId).toBeUndefined();
    });

    it('should clear error when setting user profile', () => {
      const stateWithError = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setError('Previous error')
      );

      expect(stateWithError.error).toBe('Previous error');

      const state = userReducer(stateWithError, setUserProfile(createMockProfile()));

      expect(state.error).toBe(null);
      expect(state.profile).not.toBe(null);
    });

    it('should handle all user roles in profile', () => {
      const roles: UserRole[] = ['site_admin', 'org_admin', 'instructor', 'student', 'guest'];

      roles.forEach((role) => {
        const profile = createMockProfile({ role });
        const state = userReducer(userReducer(undefined, { type: '@@INIT' }), setUserProfile(profile));

        expect(state.profile?.role).toBe(role);
      });
    });

    it('should replace existing profile completely', () => {
      const firstProfile = createMockProfile({ id: 'user-1', username: 'first' });
      const secondProfile = createMockProfile({ id: 'user-2', username: 'second' });

      let state = userReducer(userReducer(undefined, { type: '@@INIT' }), setUserProfile(firstProfile));
      expect(state.profile?.username).toBe('first');

      state = userReducer(state, setUserProfile(secondProfile));
      expect(state.profile?.username).toBe('second');
      expect(state.profile?.id).toBe('user-2');
    });
  });

  /**
   * UPDATE USER PROFILE ACTION TESTS
   *
   * BUSINESS REQUIREMENT:
   * Partial profile updates must merge with existing data.
   *
   * TEST COVERAGE:
   * - Single field updates
   * - Multiple field updates
   * - Updating optional fields
   * - No-op when profile is null
   * - Nested preference updates
   */
  describe('updateUserProfile', () => {
    it('should update single profile field', () => {
      const initialProfile = createMockProfile({ firstName: 'Old' });
      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(initialProfile)
      );

      const state = userReducer(stateWithProfile, updateUserProfile({ firstName: 'New' }));

      expect(state.profile?.firstName).toBe('New');
      // Other fields preserved
      expect(state.profile?.lastName).toBe(initialProfile.lastName);
      expect(state.profile?.email).toBe(initialProfile.email);
      expect(state.profile?.username).toBe(initialProfile.username);
    });

    it('should update multiple profile fields', () => {
      const initialProfile = createMockProfile();
      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(initialProfile)
      );

      const state = userReducer(
        stateWithProfile,
        updateUserProfile({
          firstName: 'Updated',
          lastName: 'Name',
          email: 'updated@example.com',
        })
      );

      expect(state.profile?.firstName).toBe('Updated');
      expect(state.profile?.lastName).toBe('Name');
      expect(state.profile?.email).toBe('updated@example.com');
      // Other fields preserved
      expect(state.profile?.username).toBe(initialProfile.username);
      expect(state.profile?.id).toBe(initialProfile.id);
    });

    it('should add optional fields through update', () => {
      const minimalProfile = {
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        role: 'student' as UserRole,
      };

      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(minimalProfile)
      );

      const state = userReducer(
        stateWithProfile,
        updateUserProfile({
          firstName: 'Added',
          lastName: 'Name',
          organizationId: 'org-new',
        })
      );

      expect(state.profile?.firstName).toBe('Added');
      expect(state.profile?.lastName).toBe('Name');
      expect(state.profile?.organizationId).toBe('org-new');
    });

    it('should not update when profile is null', () => {
      const initialState = userReducer(undefined, { type: '@@INIT' });

      const state = userReducer(
        initialState,
        updateUserProfile({ firstName: 'Should Not Apply' })
      );

      expect(state.profile).toBe(null);
    });

    it('should update preferences object', () => {
      const initialProfile = createMockProfile({
        preferences: { theme: 'light', language: 'en' },
      });

      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(initialProfile)
      );

      const state = userReducer(
        stateWithProfile,
        updateUserProfile({
          preferences: { theme: 'dark', notifications: true },
        })
      );

      // Preferences should be replaced, not merged deeply
      expect(state.profile?.preferences).toEqual({
        theme: 'dark',
        notifications: true,
      });
    });

    it('should update avatar URL', () => {
      const initialProfile = createMockProfile({ avatar: 'old-avatar.jpg' });
      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(initialProfile)
      );

      const state = userReducer(
        stateWithProfile,
        updateUserProfile({ avatar: 'new-avatar.jpg' })
      );

      expect(state.profile?.avatar).toBe('new-avatar.jpg');
    });
  });

  /**
   * SET LOADING ACTION TESTS
   *
   * BUSINESS REQUIREMENT:
   * Loading states must track async operations for UI feedback.
   *
   * TEST COVERAGE:
   * - Setting loading to true
   * - Setting loading to false
   * - Loading state transitions
   */
  describe('setLoading', () => {
    it('should set loading to true', () => {
      const initialState = userReducer(undefined, { type: '@@INIT' });

      const state = userReducer(initialState, setLoading(true));

      expect(state.isLoading).toBe(true);
    });

    it('should set loading to false', () => {
      const loadingState = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setLoading(true)
      );

      const state = userReducer(loadingState, setLoading(false));

      expect(state.isLoading).toBe(false);
    });

    it('should not affect other state when setting loading', () => {
      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(createMockProfile())
      );

      const state = userReducer(stateWithProfile, setLoading(true));

      expect(state.isLoading).toBe(true);
      expect(state.profile).toEqual(stateWithProfile.profile);
      expect(state.error).toBe(null);
    });
  });

  /**
   * SET ERROR ACTION TESTS
   *
   * BUSINESS REQUIREMENT:
   * Errors must be tracked and stop loading state.
   *
   * TEST COVERAGE:
   * - Setting error message
   * - Error stops loading
   * - Multiple error messages
   * - Error with existing profile
   */
  describe('setError', () => {
    it('should set error message', () => {
      const initialState = userReducer(undefined, { type: '@@INIT' });

      const state = userReducer(initialState, setError('Test error message'));

      expect(state.error).toBe('Test error message');
    });

    it('should set loading to false when error occurs', () => {
      const loadingState = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setLoading(true)
      );

      const state = userReducer(loadingState, setError('Error occurred'));

      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Error occurred');
    });

    it('should replace existing error', () => {
      const stateWithError = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setError('First error')
      );

      const state = userReducer(stateWithError, setError('Second error'));

      expect(state.error).toBe('Second error');
    });

    it('should not affect profile when setting error', () => {
      const profile = createMockProfile();
      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(profile)
      );

      const state = userReducer(stateWithProfile, setError('Error message'));

      expect(state.error).toBe('Error message');
      expect(state.profile).toEqual(profile);
    });

    it('should handle empty error message', () => {
      const state = userReducer(userReducer(undefined, { type: '@@INIT' }), setError(''));

      expect(state.error).toBe('');
      expect(state.isLoading).toBe(false);
    });

    it('should handle very long error messages', () => {
      const longError = 'Error: '.repeat(1000);
      const state = userReducer(userReducer(undefined, { type: '@@INIT' }), setError(longError));

      expect(state.error).toBe(longError);
    });
  });

  /**
   * CLEAR USER ACTION TESTS
   *
   * BUSINESS REQUIREMENT:
   * Clearing user data must reset state to initial values.
   *
   * TEST COVERAGE:
   * - Profile cleared
   * - Error cleared
   * - Loading stopped
   * - Idempotent clearing
   */
  describe('clearUser', () => {
    it('should clear user profile', () => {
      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(createMockProfile())
      );

      const state = userReducer(stateWithProfile, clearUser());

      expect(state.profile).toBe(null);
    });

    it('should clear error when clearing user', () => {
      const stateWithError = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setError('Test error')
      );

      const state = userReducer(stateWithError, clearUser());

      expect(state.error).toBe(null);
    });

    it('should set loading to false when clearing user', () => {
      const loadingState = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setLoading(true)
      );

      const state = userReducer(loadingState, clearUser());

      expect(state.isLoading).toBe(false);
    });

    it('should clear all state to initial values', () => {
      const complexState = userReducer(
        userReducer(
          userReducer(userReducer(undefined, { type: '@@INIT' }), setUserProfile(createMockProfile())),
          setError('Error')
        ),
        setLoading(true)
      );

      const state = userReducer(complexState, clearUser());

      expect(state).toEqual({
        profile: null,
        isLoading: false,
        error: null,
      });
    });

    it('should be idempotent when already cleared', () => {
      const initialState = userReducer(undefined, { type: '@@INIT' });
      const state = userReducer(initialState, clearUser());

      expect(state).toEqual(initialState);
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
   * - Profile objects not shared
   */
  describe('state immutability', () => {
    it('should not mutate original state on setUserProfile', () => {
      const initialState = userReducer(undefined, { type: '@@INIT' });
      const originalState = { ...initialState };

      userReducer(initialState, setUserProfile(createMockProfile()));

      expect(initialState).toEqual(originalState);
    });

    it('should not mutate original state on updateUserProfile', () => {
      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(createMockProfile())
      );
      const originalState = { ...stateWithProfile };

      userReducer(stateWithProfile, updateUserProfile({ firstName: 'Changed' }));

      expect(stateWithProfile).toEqual(originalState);
    });

    it('should create new profile object on update', () => {
      const initialProfile = createMockProfile();
      const stateWithProfile = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(initialProfile)
      );

      const updatedState = userReducer(stateWithProfile, updateUserProfile({ firstName: 'New' }));

      // Profile object reference should change
      expect(updatedState.profile).not.toBe(stateWithProfile.profile);
      // Original profile object not mutated
      expect(initialProfile.firstName).toBe('Test');
    });
  });

  /**
   * WORKFLOW TESTS
   *
   * BUSINESS REQUIREMENT:
   * Common user profile workflows must work correctly.
   *
   * TEST COVERAGE:
   * - Load profile workflow
   * - Update profile workflow
   * - Error recovery workflow
   * - Logout workflow
   */
  describe('common workflows', () => {
    it('should handle typical profile load workflow', () => {
      let state = userReducer(undefined, { type: '@@INIT' });

      // Start loading
      state = userReducer(state, setLoading(true));
      expect(state.isLoading).toBe(true);

      // Profile loaded successfully
      state = userReducer(state, setUserProfile(createMockProfile()));
      expect(state.profile).not.toBe(null);
      expect(state.error).toBe(null);

      // Stop loading (typically done by async thunk)
      state = userReducer(state, setLoading(false));
      expect(state.isLoading).toBe(false);
    });

    it('should handle profile load error workflow', () => {
      let state = userReducer(undefined, { type: '@@INIT' });

      // Start loading
      state = userReducer(state, setLoading(true));
      expect(state.isLoading).toBe(true);

      // Error occurs (automatically stops loading)
      state = userReducer(state, setError('Failed to load profile'));
      expect(state.error).toBe('Failed to load profile');
      expect(state.isLoading).toBe(false);
      expect(state.profile).toBe(null);
    });

    it('should handle profile update workflow', () => {
      let state = userReducer(undefined, { type: '@@INIT' });

      // Initial profile loaded
      state = userReducer(state, setUserProfile(createMockProfile({ firstName: 'Original' })));

      // Start update
      state = userReducer(state, setLoading(true));

      // Update applied
      state = userReducer(state, updateUserProfile({ firstName: 'Updated' }));

      // Update complete
      state = userReducer(state, setLoading(false));

      expect(state.profile?.firstName).toBe('Updated');
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should handle logout workflow', () => {
      let state = userReducer(undefined, { type: '@@INIT' });

      // User logged in with profile
      state = userReducer(state, setUserProfile(createMockProfile()));
      expect(state.profile).not.toBe(null);

      // User logs out - clear all user data
      state = userReducer(state, clearUser());

      expect(state.profile).toBe(null);
      expect(state.error).toBe(null);
      expect(state.isLoading).toBe(false);
    });

    it('should handle error recovery workflow', () => {
      let state = userReducer(undefined, { type: '@@INIT' });

      // Error occurred
      state = userReducer(state, setError('Network error'));
      expect(state.error).toBe('Network error');

      // Retry - start loading
      state = userReducer(state, setLoading(true));

      // Success - error cleared by setUserProfile
      state = userReducer(state, setUserProfile(createMockProfile()));

      expect(state.profile).not.toBe(null);
      expect(state.error).toBe(null);
    });
  });

  /**
   * EDGE CASE TESTS
   *
   * BUSINESS REQUIREMENT:
   * Handle unusual but valid scenarios gracefully.
   *
   * TEST COVERAGE:
   * - Empty string values
   * - Special characters in names
   * - Very long strings
   * - Undefined vs null preference handling
   */
  describe('edge cases', () => {
    it('should handle empty string values in profile', () => {
      const profileWithEmptyStrings = createMockProfile({
        firstName: '',
        lastName: '',
        organizationName: '',
      });

      const state = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(profileWithEmptyStrings)
      );

      expect(state.profile?.firstName).toBe('');
      expect(state.profile?.lastName).toBe('');
      expect(state.profile?.organizationName).toBe('');
    });

    it('should handle special characters in names', () => {
      const profileWithSpecialChars = createMockProfile({
        firstName: "O'Brien",
        lastName: 'Müller-Schmidt',
        username: 'user@domain.com',
      });

      const state = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(profileWithSpecialChars)
      );

      expect(state.profile?.firstName).toBe("O'Brien");
      expect(state.profile?.lastName).toBe('Müller-Schmidt');
    });

    it('should handle very long strings in profile', () => {
      const longString = 'a'.repeat(10000);
      const profileWithLongStrings = createMockProfile({
        firstName: longString,
      });

      const state = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(profileWithLongStrings)
      );

      expect(state.profile?.firstName).toBe(longString);
      expect(state.profile?.firstName?.length).toBe(10000);
    });

    it('should handle undefined preferences', () => {
      const profileWithoutPreferences = createMockProfile({
        preferences: undefined,
      });

      const state = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(profileWithoutPreferences)
      );

      expect(state.profile?.preferences).toBeUndefined();
    });

    it('should handle empty preferences object', () => {
      const profileWithEmptyPreferences = createMockProfile({
        preferences: {},
      });

      const state = userReducer(
        userReducer(undefined, { type: '@@INIT' }),
        setUserProfile(profileWithEmptyPreferences)
      );

      expect(state.profile?.preferences).toEqual({});
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
   */
  describe('type safety', () => {
    it('should export all action creators', () => {
      expect(typeof setUserProfile).toBe('function');
      expect(typeof updateUserProfile).toBe('function');
      expect(typeof setLoading).toBe('function');
      expect(typeof setError).toBe('function');
      expect(typeof clearUser).toBe('function');
    });

    it('should handle all UserRole types in profile', () => {
      const roles: UserRole[] = ['site_admin', 'org_admin', 'instructor', 'student', 'guest'];

      roles.forEach((role) => {
        const profile = createMockProfile({ role });
        const state = userReducer(userReducer(undefined, { type: '@@INIT' }), setUserProfile(profile));

        expect(state.profile?.role).toBe(role);
      });
    });
  });
});
