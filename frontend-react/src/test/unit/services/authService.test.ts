/**
 * Auth Service Unit Tests — CC-3
 *
 * BUSINESS CONTEXT:
 * Covers all authentication paths: login (success/error/rate-limit),
 * logout (success/API-failure), register (success/error),
 * token refresh (success/failure), and helper methods.
 *
 * TECHNICAL IMPLEMENTATION:
 * Mocks apiClient and tokenManager to isolate AuthService logic.
 * No HTTP calls are made — all API responses are stubbed.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// ---- mock apiClient before authService imports it ----
const mockPost = vi.fn();
const mockGet = vi.fn();

vi.mock('../../../services/apiClient', () => ({
  apiClient: {
    post: (...args: unknown[]) => mockPost(...args),
    get: (...args: unknown[]) => mockGet(...args),
  },
}));

const mockClearTokens = vi.fn();
const mockHasToken = vi.fn<[], boolean>();

vi.mock('../../../services/tokenManager', () => ({
  tokenManager: {
    getToken: vi.fn(),
    setToken: vi.fn(),
    getRefreshToken: vi.fn(),
    setRefreshToken: vi.fn(),
    clearTokens: () => mockClearTokens(),
    hasToken: () => mockHasToken(),
  },
}));

import { authService } from '../../../services/authService';

// Backend response shape returned by /auth/login
const makeBackendLoginResponse = (overrides = {}) => ({
  access_token: 'jwt-access',
  refresh_token: 'jwt-refresh',
  expires_in: 3600,
  is_first_login: false,
  user: {
    id: 'user-1',
    username: 'tester',
    email: 'tester@example.com',
    full_name: 'Test User',
    role: 'student',
    organization_id: 'org-1',
    organization: 'Acme',
  },
  ...overrides,
});

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  // -------------------------------------------------------
  // login
  // -------------------------------------------------------
  describe('login()', () => {
    it('returns transformed LoginResponse on success', async () => {
      mockPost.mockResolvedValue(makeBackendLoginResponse());

      const result = await authService.login({ username: 'tester', password: 'pass1234' });

      expect(result.token).toBe('jwt-access');
      expect(result.refreshToken).toBe('jwt-refresh');
      expect(result.user.id).toBe('user-1');
      expect(result.user.username).toBe('tester');
      expect(result.user.role).toBe('student');
      expect(result.isFirstLogin).toBe(false);
    });

    it('sets expiresIn as a future timestamp (not raw seconds)', async () => {
      const before = Date.now();
      mockPost.mockResolvedValue(makeBackendLoginResponse({ expires_in: 3600 }));
      const result = await authService.login({ username: 'u', password: 'p' });
      const after = Date.now();

      expect(result.expiresIn).toBeGreaterThan(before);
      expect(result.expiresIn).toBeLessThanOrEqual(after + 3600 * 1000 + 50);
    });

    it('sets isFirstLogin=true when backend returns true', async () => {
      mockPost.mockResolvedValue(makeBackendLoginResponse({ is_first_login: true }));
      const result = await authService.login({ username: 'u', password: 'p' });
      expect(result.isFirstLogin).toBe(true);
    });

    it('throws "Invalid credentials" on API error', async () => {
      mockPost.mockRejectedValue(new Error('401 Unauthorized'));
      await expect(authService.login({ username: 'u', password: 'bad' }))
        .rejects.toThrow('Invalid credentials. Please try again.');
    });

    it('throws rate-limit message on 429 response', async () => {
      const err: any = new Error('Too many requests');
      err.response = { status: 429 };
      mockPost.mockRejectedValue(err);

      await expect(authService.login({ username: 'u', password: 'p' }))
        .rejects.toThrow('Too many login attempts. Please try again later.');
    });

    it('calls /auth/login with the provided credentials', async () => {
      mockPost.mockResolvedValue(makeBackendLoginResponse());
      await authService.login({ username: 'tester', password: 'secret123' });
      expect(mockPost).toHaveBeenCalledWith('/auth/login', { username: 'tester', password: 'secret123' });
    });
  });

  // -------------------------------------------------------
  // logout
  // -------------------------------------------------------
  describe('logout()', () => {
    it('calls /auth/logout and then clears tokens', async () => {
      mockPost.mockResolvedValue({});
      await authService.logout();
      expect(mockPost).toHaveBeenCalledWith('/auth/logout');
      expect(mockClearTokens).toHaveBeenCalledOnce();
    });

    it('removes targeted auth localStorage keys on logout', async () => {
      localStorage.setItem('userRole', 'student');
      localStorage.setItem('userId', 'user-1');
      localStorage.setItem('organizationId', 'org-1');
      localStorage.setItem('userThemePreference', 'dark'); // non-auth key

      mockPost.mockResolvedValue({});
      await authService.logout();

      expect(localStorage.getItem('userRole')).toBeNull();
      expect(localStorage.getItem('userId')).toBeNull();
      expect(localStorage.getItem('organizationId')).toBeNull();
      // Non-auth key must survive
      expect(localStorage.getItem('userThemePreference')).toBe('dark');
    });

    it('still clears tokens even when API call fails', async () => {
      mockPost.mockRejectedValue(new Error('Network error'));
      await authService.logout(); // should not throw
      expect(mockClearTokens).toHaveBeenCalledOnce();
    });
  });

  // -------------------------------------------------------
  // register
  // -------------------------------------------------------
  describe('register()', () => {
    const registerData = {
      username: 'newuser',
      email: 'new@example.com',
      fullName: 'New User',
      password: 'Password1',
      acceptTerms: true,
      acceptPrivacy: true,
    };

    it('returns LoginResponse on success', async () => {
      mockPost.mockResolvedValue({
        access_token: 'reg-token',
        expires_in: 3600,
        user: {
          id: 'new-1',
          username: 'newuser',
          email: 'new@example.com',
          role: 'organization_admin',
        },
      });

      const result = await authService.register(registerData);
      expect(result.token).toBe('reg-token');
      expect(result.user.role).toBe('organization_admin');
      expect(result.isFirstLogin).toBe(true);
    });

    it('throws on registration failure with backend detail message', async () => {
      const err: any = new Error();
      err.response = { data: { detail: 'Username already taken' } };
      mockPost.mockRejectedValue(err);

      await expect(authService.register(registerData))
        .rejects.toThrow('Username already taken');
    });

    it('sends role as organization_admin to backend', async () => {
      mockPost.mockResolvedValue({
        access_token: 't',
        expires_in: 3600,
        user: { id: '1', username: 'u', email: 'e@e.com', role: 'organization_admin' },
      });

      await authService.register(registerData);
      const [, payload] = mockPost.mock.calls[0];
      expect((payload as any).role).toBe('organization_admin');
    });
  });

  // -------------------------------------------------------
  // refreshToken
  // -------------------------------------------------------
  describe('refreshToken()', () => {
    it('returns new token and expiresAt on success', async () => {
      const before = Date.now();
      mockPost.mockResolvedValue({ token: 'new-token', expiresIn: 1800 });

      const result = await authService.refreshToken('old-refresh');

      expect(result.token).toBe('new-token');
      expect(result.expiresAt).toBeGreaterThan(before + 1799_000);
    });

    it('throws "Session expired" on refresh failure', async () => {
      mockPost.mockRejectedValue(new Error('401'));
      await expect(authService.refreshToken('bad-refresh'))
        .rejects.toThrow('Session expired. Please login again.');
    });
  });

  // -------------------------------------------------------
  // isAuthenticated / getCurrentRole
  // -------------------------------------------------------
  describe('isAuthenticated()', () => {
    it('returns true when tokenManager has a token', () => {
      mockHasToken.mockReturnValue(true);
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('returns false when tokenManager has no token', () => {
      mockHasToken.mockReturnValue(false);
      expect(authService.isAuthenticated()).toBe(false);
    });
  });

  describe('getCurrentRole()', () => {
    it('returns role from localStorage', () => {
      localStorage.setItem('userRole', 'instructor');
      expect(authService.getCurrentRole()).toBe('instructor');
    });

    it('returns null when no role is stored', () => {
      expect(authService.getCurrentRole()).toBeNull();
    });
  });
});
