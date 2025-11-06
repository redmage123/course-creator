/**
 * Authentication State Slice
 *
 * BUSINESS CONTEXT:
 * Manages authentication state for the Course Creator Platform including JWT tokens,
 * login status, and user session management.
 *
 * TECHNICAL IMPLEMENTATION:
 * Redux Toolkit slice with actions for login, logout, token refresh. Persists
 * auth token to localStorage for session persistence across page reloads.
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export type UserRole = 'site_admin' | 'org_admin' | 'instructor' | 'student' | 'guest';

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  refreshToken: string | null;
  role: UserRole | null;
  userId: string | null;
  organizationId: string | null;
  expiresAt: number | null;
}

// Restore auth state from localStorage on initialization
const storedToken = localStorage.getItem('authToken');
const storedRefreshToken = localStorage.getItem('refreshToken');
const storedRole = localStorage.getItem('userRole') as UserRole;
const storedUserId = localStorage.getItem('userId');
const storedOrganizationId = localStorage.getItem('organizationId');

const initialState: AuthState = {
  isAuthenticated: !!storedToken, // Authenticated if token exists
  token: storedToken,
  refreshToken: storedRefreshToken,
  role: storedRole || null,
  userId: storedUserId,
  organizationId: storedOrganizationId,
  expiresAt: null,
};

/**
 * Authentication slice with reducers for auth operations
 *
 * WHY THIS APPROACH:
 * - Centralized auth state management
 * - Type-safe actions with TypeScript
 * - Automatic localStorage synchronization
 * - Immutable state updates with Immer
 */
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginSuccess: (
      state,
      action: PayloadAction<{
        token: string;
        refreshToken?: string;
        role: UserRole;
        userId: string;
        organizationId?: string;
        expiresAt: number;
      }>
    ) => {
      state.isAuthenticated = true;
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken || null;
      state.role = action.payload.role;
      state.userId = action.payload.userId;
      state.organizationId = action.payload.organizationId || null;
      state.expiresAt = action.payload.expiresAt;

      // Persist to localStorage
      localStorage.setItem('authToken', action.payload.token);
      if (action.payload.refreshToken) {
        localStorage.setItem('refreshToken', action.payload.refreshToken);
      }
      localStorage.setItem('userRole', action.payload.role);
      localStorage.setItem('userId', action.payload.userId);
      if (action.payload.organizationId) {
        localStorage.setItem('organizationId', action.payload.organizationId);
      }
    },

    logout: (state) => {
      state.isAuthenticated = false;
      state.token = null;
      state.refreshToken = null;
      state.role = null;
      state.userId = null;
      state.organizationId = null;
      state.expiresAt = null;

      // Clear localStorage
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userId');
      localStorage.removeItem('organizationId');
    },

    refreshTokenSuccess: (
      state,
      action: PayloadAction<{ token: string; expiresAt: number }>
    ) => {
      state.token = action.payload.token;
      state.expiresAt = action.payload.expiresAt;
      localStorage.setItem('authToken', action.payload.token);
    },

    updateOrganization: (state, action: PayloadAction<string>) => {
      state.organizationId = action.payload;
      localStorage.setItem('organizationId', action.payload);
    },
  },
});

export const { loginSuccess, logout, refreshTokenSuccess, updateOrganization } =
  authSlice.actions;

export default authSlice.reducer;
