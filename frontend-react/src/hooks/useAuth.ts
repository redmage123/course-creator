/**
 * Authentication Hook
 *
 * BUSINESS CONTEXT:
 * Provides authentication state and methods throughout the application.
 * Centralizes auth logic for consistent behavior across all components.
 *
 * TECHNICAL IMPLEMENTATION:
 * Combines Redux state with authentication service for a unified auth API.
 */

import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from './useRedux';
import { loginSuccess, logout as logoutAction, refreshTokenSuccess, clearFirstLoginFlag } from '@store/slices/authSlice';
import { setUserProfile, clearUser } from '@store/slices/userSlice';
import { authService, LoginCredentials, RegisterData } from '@services/authService';
import { tokenManager } from '@services/tokenManager';
import { addNotification } from '@store/slices/uiSlice';

/**
 * Authentication Hook
 *
 * WHY THIS APPROACH:
 * - Single hook for all auth operations
 * - Automatic Redux state updates
 * - Consistent error handling
 * - Navigation integration
 *
 * @returns Authentication state and methods
 */
export const useAuth = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isAuthenticated, token, role, userId, organizationId, isFirstLogin } = useAppSelector((state) => state.auth);
  const { profile } = useAppSelector((state) => state.user);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Login user with credentials
   *
   * BUSINESS LOGIC:
   * Authenticates user, updates Redux state, and redirects to appropriate dashboard
   * based on user role.
   */
  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setIsLoading(true);
      try {
        const response = await authService.login(credentials);

        // Update Redux state
        dispatch(
          loginSuccess({
            token: response.token,
            refreshToken: response.refreshToken,
            role: response.user.role,
            userId: response.user.id,
            organizationId: response.user.organizationId,
            expiresAt: response.expiresIn,
            isFirstLogin: response.isFirstLogin,
          })
        );

        dispatch(setUserProfile(response.user));

        // Show success notification
        dispatch(
          addNotification({
            type: 'success',
            message: `Welcome back, ${response.user.username}!`,
            duration: 3000,
          })
        );

        // Redirect based on role
        const dashboardRoutes = {
          site_admin: '/dashboard/site-admin',
          organization_admin: '/dashboard/org-admin',
          instructor: '/dashboard/instructor',
          student: '/dashboard/student',
          guest: '/',
        };

        navigate(dashboardRoutes[response.user.role] || '/');
      } catch (error) {
        dispatch(
          addNotification({
            type: 'error',
            message: error instanceof Error ? error.message : 'Login failed',
            duration: 5000,
          })
        );
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [dispatch, navigate]
  );

  /**
   * Logout current user
   *
   * BUSINESS LOGIC:
   * Clears session, updates Redux state, and redirects to homepage.
   */
  const logout = useCallback(async () => {
    try {
      await authService.logout();

      // Clear Redux state
      dispatch(logoutAction());
      dispatch(clearUser());

      dispatch(
        addNotification({
          type: 'info',
          message: 'You have been logged out',
          duration: 3000,
        })
      );

      navigate('/');
    } catch (error) {
      console.error('[useAuth] Logout error:', error);
      // Force logout locally even if API call fails
      dispatch(logoutAction());
      dispatch(clearUser());
      navigate('/');
    }
  }, [dispatch, navigate]);

  /**
   * Register new user
   *
   * BUSINESS LOGIC:
   * Creates account and automatically logs in the new user.
   */
  const register = useCallback(
    async (data: RegisterData) => {
      setIsLoading(true);
      try {
        const response = await authService.register(data);

        // Auto-login after registration
        dispatch(
          loginSuccess({
            token: response.token,
            refreshToken: response.refreshToken,
            role: response.user.role,
            userId: response.user.id,
            organizationId: response.user.organizationId,
            expiresAt: response.expiresIn,
          })
        );

        dispatch(setUserProfile(response.user));

        dispatch(
          addNotification({
            type: 'success',
            message: 'Account created successfully!',
            duration: 3000,
          })
        );

        // Redirect based on role (same as login)
        const dashboardRoutes = {
          site_admin: '/dashboard/site-admin',
          organization_admin: '/dashboard/org-admin',
          instructor: '/dashboard/instructor',
          student: '/dashboard/student',
          guest: '/',
        };

        navigate(dashboardRoutes[response.user.role] || '/dashboard');
      } catch (error) {
        dispatch(
          addNotification({
            type: 'error',
            message: error instanceof Error ? error.message : 'Registration failed',
            duration: 5000,
          })
        );
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [dispatch, navigate]
  );

  /**
   * Refresh authentication token
   *
   * BUSINESS LOGIC:
   * Automatically called when token is about to expire to maintain session.
   */
  const refreshToken = useCallback(async () => {
    try {
      const refreshTokenValue = tokenManager.getRefreshToken();
      if (!refreshTokenValue) {
        throw new Error('No refresh token available');
      }

      const response = await authService.refreshToken(refreshTokenValue);

      dispatch(refreshTokenSuccess({
        token: response.token,
        expiresAt: response.expiresAt,
      }));
    } catch (error) {
      console.error('[useAuth] Token refresh failed:', error);
      // Force logout if refresh fails
      await logout();
    }
  }, [dispatch, logout]);

  /**
   * Restore session on app load
   *
   * BUSINESS LOGIC:
   * Fetches current user profile if token exists to restore session after page reload.
   */
  const restoreSession = useCallback(async () => {
    try {
      if (token) {
        const user = await authService.getCurrentUser();
        dispatch(setUserProfile(user));
      }
    } catch (error) {
      console.error('[useAuth] Session restore failed:', error);
      // Clear invalid session
      dispatch(logoutAction());
      dispatch(clearUser());
    }
  }, [token, dispatch]);

  /**
   * Clear first login flag
   *
   * BUSINESS LOGIC:
   * Called after the welcome popup is shown/dismissed to prevent
   * showing it again on subsequent page loads.
   */
  const clearFirstLogin = useCallback(() => {
    dispatch(clearFirstLoginFlag());
  }, [dispatch]);

  /**
   * Auto-restore session on mount
   */
  useEffect(() => {
    if (token && !profile) {
      restoreSession();
    }
  }, [token, profile, restoreSession]);

  return {
    // State
    isAuthenticated,
    token,
    role,
    userId,
    organizationId,
    user: profile,
    isLoading,
    isFirstLogin,

    // Methods
    login,
    logout,
    register,
    refreshToken,
    restoreSession,
    clearFirstLogin,

    // Computed
    isStudent: role === 'student',
    isInstructor: role === 'instructor',
    isOrgAdmin: role === 'organization_admin',
    isSiteAdmin: role === 'site_admin',
    isGuest: role === 'guest' || !role,
  };
};
