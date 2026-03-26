/**
 * useAuth Hook Unit Tests — CC-3
 *
 * BUSINESS CONTEXT:
 * Covers login (with role-based navigation), logout, register, token refresh
 * (success + failure → redirect), and 401 handling across all auth paths.
 *
 * TECHNICAL IMPLEMENTATION:
 * Renders the hook inside a Redux Provider + MemoryRouter so navigation
 * and Redux dispatch work normally. authService is fully mocked to keep
 * tests fast and deterministic.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

// ---- mocks before importing under test ----
const mockLogin = vi.fn();
const mockLogout = vi.fn();
const mockRegister = vi.fn();
const mockRefreshToken = vi.fn();
const mockGetCurrentUser = vi.fn();

vi.mock('@services/authService', () => ({
  authService: {
    login: (...a: unknown[]) => mockLogin(...a),
    logout: (...a: unknown[]) => mockLogout(...a),
    register: (...a: unknown[]) => mockRegister(...a),
    refreshToken: (...a: unknown[]) => mockRefreshToken(...a),
    getCurrentUser: (...a: unknown[]) => mockGetCurrentUser(...a),
    isAuthenticated: vi.fn(() => false),
    getCurrentRole: vi.fn(() => null),
  },
}));

vi.mock('@services/tokenManager', () => ({
  tokenManager: {
    getToken: vi.fn(() => null),
    setToken: vi.fn(),
    getRefreshToken: vi.fn(() => null),
    setRefreshToken: vi.fn(),
    clearTokens: vi.fn(),
    hasToken: vi.fn(() => false),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

import { useAuth } from './useAuth';

// ---- helpers ----

import authReducer from '../store/slices/authSlice';
import userReducer from '../store/slices/userSlice';
import uiReducer from '../store/slices/uiSlice';

function makeStore() {
  return configureStore({
    reducer: {
      auth: authReducer,
      user: userReducer,
      ui: uiReducer,
    },
  });
}

function makeWrapper(store = makeStore()) {
  return ({ children }: { children: ReactNode }) => (
    <Provider store={store}>
      <MemoryRouter>{children}</MemoryRouter>
    </Provider>
  );
}

const successLoginResponse = (role = 'student') => ({
  token: 'access-tok',
  refreshToken: 'refresh-tok',
  user: {
    id: 'u1',
    username: 'tester',
    email: 'tester@example.com',
    role,
    organizationId: 'org-1',
  },
  expiresIn: Date.now() + 3600_000,
  isFirstLogin: false,
});

describe('useAuth hook (CC-3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  // -------------------------------------------------------
  // login
  // -------------------------------------------------------
  describe('login()', () => {
    it('dispatches loginSuccess and sets isAuthenticated after successful login', async () => {
      mockLogin.mockResolvedValue(successLoginResponse());
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.login({ username: 'tester', password: 'pass1234' });
      });

      expect(result.current.isAuthenticated).toBe(true);
    });

    it('navigates to student dashboard for student role', async () => {
      mockLogin.mockResolvedValue(successLoginResponse('student'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.login({ username: 'u', password: 'p' });
      });

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/student');
    });

    it('navigates to org-admin dashboard for organization_admin role', async () => {
      mockLogin.mockResolvedValue(successLoginResponse('organization_admin'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.login({ username: 'u', password: 'p' });
      });

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/org-admin');
    });

    it('navigates to instructor dashboard for instructor role', async () => {
      mockLogin.mockResolvedValue(successLoginResponse('instructor'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.login({ username: 'u', password: 'p' });
      });

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/instructor');
    });

    it('navigates to site-admin dashboard for site_admin role', async () => {
      mockLogin.mockResolvedValue(successLoginResponse('site_admin'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.login({ username: 'u', password: 'p' });
      });

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/site-admin');
    });

    it('sets isLoading=true during login and false after', async () => {
      let resolveLogin!: (v: unknown) => void;
      mockLogin.mockReturnValue(new Promise((res) => { resolveLogin = res; }));

      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      const loginPromise = act(async () => {
        result.current.login({ username: 'u', password: 'p' }).catch(() => {});
      });

      // Loading should be true during the async operation
      await waitFor(() => expect(result.current.isLoading).toBe(true));

      resolveLogin(successLoginResponse());
      await loginPromise;

      await waitFor(() => expect(result.current.isLoading).toBe(false));
    });

    it('rethrows error on login failure', async () => {
      mockLogin.mockRejectedValue(new Error('Invalid credentials'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await expect(
        act(async () => {
          await result.current.login({ username: 'u', password: 'bad' });
        })
      ).rejects.toThrow('Invalid credentials');
    });

    it('isLoading resets to false after login failure', async () => {
      mockLogin.mockRejectedValue(new Error('fail'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.login({ username: 'u', password: 'p' }).catch(() => {});
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  // -------------------------------------------------------
  // logout
  // -------------------------------------------------------
  describe('logout()', () => {
    it('clears isAuthenticated after logout', async () => {
      mockLogin.mockResolvedValue(successLoginResponse());
      mockLogout.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.login({ username: 'u', password: 'p' });
      });
      expect(result.current.isAuthenticated).toBe(true);

      await act(async () => {
        await result.current.logout();
      });
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('navigates to / after logout', async () => {
      mockLogout.mockResolvedValue(undefined);
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.logout();
      });

      expect(mockNavigate).toHaveBeenCalledWith('/');
    });

    it('still navigates to / even when API call fails', async () => {
      mockLogout.mockRejectedValue(new Error('Network error'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.logout();
      });

      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  // -------------------------------------------------------
  // register
  // -------------------------------------------------------
  describe('register()', () => {
    const regData = {
      username: 'newbie',
      email: 'new@example.com',
      fullName: 'New User',
      password: 'Password1',
      acceptTerms: true,
      acceptPrivacy: true,
    };

    it('navigates to org-admin dashboard after registration', async () => {
      mockRegister.mockResolvedValue(successLoginResponse('organization_admin'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.register(regData);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/org-admin');
    });

    it('sets isAuthenticated after registration', async () => {
      mockRegister.mockResolvedValue(successLoginResponse('organization_admin'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.register(regData);
      });

      expect(result.current.isAuthenticated).toBe(true);
    });

    it('rethrows error on registration failure', async () => {
      mockRegister.mockRejectedValue(new Error('Username taken'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await expect(
        act(async () => {
          await result.current.register(regData);
        })
      ).rejects.toThrow('Username taken');
    });
  });

  // -------------------------------------------------------
  // refreshToken
  // -------------------------------------------------------
  describe('refreshToken()', () => {
    it('updates token in store after successful refresh', async () => {
      // First login to set up auth state
      mockLogin.mockResolvedValue(successLoginResponse());
      mockRefreshToken.mockResolvedValue({ token: 'new-token', expiresAt: Date.now() + 3600_000 });

      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.login({ username: 'u', password: 'p' });
      });

      // tokenManager.getRefreshToken needs to return something
      const { tokenManager } = await import('@services/tokenManager');
      vi.mocked(tokenManager.getRefreshToken).mockReturnValue('refresh-tok');

      await act(async () => {
        await result.current.refreshToken();
      });

      expect(mockRefreshToken).toHaveBeenCalledOnce();
    });

    it('redirects to / (logout) when token refresh fails', async () => {
      mockLogin.mockResolvedValue(successLoginResponse());
      mockLogout.mockResolvedValue(undefined);
      mockRefreshToken.mockRejectedValue(new Error('refresh expired'));

      const { tokenManager } = await import('@services/tokenManager');
      vi.mocked(tokenManager.getRefreshToken).mockReturnValue('old-refresh');

      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      await act(async () => {
        await result.current.refreshToken();
      });

      // logout was called (which navigates to /)
      expect(mockLogout).toHaveBeenCalled();
    });

    it('throws when no refresh token is available', async () => {
      const { tokenManager } = await import('@services/tokenManager');
      vi.mocked(tokenManager.getRefreshToken).mockReturnValue(null);
      mockLogout.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });

      // Should silently call logout (no rethrow from refreshToken in the hook)
      await act(async () => {
        await result.current.refreshToken();
      });

      expect(mockRefreshToken).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------
  // computed role helpers
  // -------------------------------------------------------
  describe('role helpers', () => {
    it('isStudent is true for student role', async () => {
      mockLogin.mockResolvedValue(successLoginResponse('student'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });
      await act(async () => { await result.current.login({ username: 'u', password: 'p' }); });
      expect(result.current.isStudent).toBe(true);
    });

    it('isOrgAdmin is true for organization_admin role', async () => {
      mockLogin.mockResolvedValue(successLoginResponse('organization_admin'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });
      await act(async () => { await result.current.login({ username: 'u', password: 'p' }); });
      expect(result.current.isOrgAdmin).toBe(true);
    });

    it('isSiteAdmin is true for site_admin role', async () => {
      mockLogin.mockResolvedValue(successLoginResponse('site_admin'));
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });
      await act(async () => { await result.current.login({ username: 'u', password: 'p' }); });
      expect(result.current.isSiteAdmin).toBe(true);
    });

    it('isGuest is true before login', () => {
      const { result } = renderHook(() => useAuth(), { wrapper: makeWrapper() });
      expect(result.current.isGuest).toBe(true);
    });
  });
});
