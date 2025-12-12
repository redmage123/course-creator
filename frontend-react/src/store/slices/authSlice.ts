/**
 * Authentication State Slice
 *
 * BUSINESS CONTEXT:
 * Manages authentication state for the Course Creator Platform including JWT tokens,
 * login status, and user session management.
 *
 * TECHNICAL IMPLEMENTATION:
 * Redux Toolkit slice with actions for login, logout, token refresh. Uses in-memory
 * token storage via tokenManager for enhanced security (no localStorage persistence).
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { tokenManager } from '@services/tokenManager';

export type UserRole = 'site_admin' | 'organization_admin' | 'instructor' | 'student' | 'guest';

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  refreshToken: string | null;
  role: UserRole | null;
  userId: string | null;
  organizationId: string | null;
  expiresAt: number | null;
  isFirstLogin: boolean;
}

/**
 * Initial auth state
 *
 * WHY NO TOKEN PERSISTENCE:
 * Tokens are stored in-memory only (via tokenManager) for security.
 * On page reload, user must re-authenticate. This prevents XSS token theft
 * via localStorage access. Role/user metadata stored in localStorage for
 * routing purposes only (not sensitive data).
 */
const storedRole = localStorage.getItem('userRole') as UserRole;
const storedUserId = localStorage.getItem('userId');
const storedOrganizationId = localStorage.getItem('organizationId');

const initialState: AuthState = {
  isAuthenticated: false, // Always false on reload - requires re-authentication
  token: null,
  refreshToken: null,
  role: storedRole || null,
  userId: storedUserId,
  organizationId: storedOrganizationId,
  expiresAt: null,
  isFirstLogin: false,
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
        isFirstLogin?: boolean;
      }>
    ) => {
      state.isAuthenticated = true;
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken || null;
      state.role = action.payload.role;
      state.userId = action.payload.userId;
      state.organizationId = action.payload.organizationId || null;
      state.expiresAt = action.payload.expiresAt;
      state.isFirstLogin = action.payload.isFirstLogin || false;

      // Store tokens in memory (secure - not in localStorage)
      tokenManager.setToken(action.payload.token);
      if (action.payload.refreshToken) {
        tokenManager.setRefreshToken(action.payload.refreshToken);
      }

      // Store non-sensitive metadata in localStorage (for routing purposes)
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
      state.isFirstLogin = false;

      // Clear tokens from memory
      tokenManager.clearTokens();

      // Clear metadata from localStorage
      localStorage.removeItem('userRole');
      localStorage.removeItem('userId');
      localStorage.removeItem('organizationId');
    },

    clearFirstLoginFlag: (state) => {
      state.isFirstLogin = false;
    },

    refreshTokenSuccess: (
      state,
      action: PayloadAction<{ token: string; expiresAt: number }>
    ) => {
      state.token = action.payload.token;
      state.expiresAt = action.payload.expiresAt;
      // Store refreshed token in memory (not localStorage)
      tokenManager.setToken(action.payload.token);
    },

    updateOrganization: (state, action: PayloadAction<string>) => {
      state.organizationId = action.payload;
      localStorage.setItem('organizationId', action.payload);
    },
  },
});

export const { loginSuccess, logout, refreshTokenSuccess, updateOrganization, clearFirstLoginFlag } =
  authSlice.actions;

export default authSlice.reducer;
