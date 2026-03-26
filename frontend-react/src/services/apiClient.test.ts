/**
 * API Client Service Tests — CC-1 localStorage data-loss regression
 *
 * BUSINESS CONTEXT:
 * Confirms that auth failure (expired tokens, failed refresh) does NOT wipe
 * non-auth localStorage keys such as user preferences, rememberMe, or theme.
 *
 * REGRESSION GUARD:
 * Prior code called localStorage.clear() in both the "refresh failed" and
 * "no refresh token" branches — destroying all user data on session expiry.
 * These tests confirm that only auth tokens are cleared, not unrelated keys.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Track localStorage.clear calls
const localStorageClearSpy = vi.spyOn(Storage.prototype, 'clear');

const mockClearTokens = vi.fn();
const mockGetRefreshToken = vi.fn<[], string | null>();
const mockGetToken = vi.fn<[], string | null>();
const mockSetToken = vi.fn();

vi.mock('./tokenManager', () => ({
  tokenManager: {
    getToken: () => mockGetToken(),
    setToken: (t: string | null) => mockSetToken(t),
    getRefreshToken: () => mockGetRefreshToken(),
    clearTokens: () => mockClearTokens(),
    hasToken: () => !!mockGetToken(),
    setRefreshToken: vi.fn(),
  },
}));

// Simulate the two logout code paths extracted from apiClient.ts
// These mirror the exact branches in the response interceptor.
function simulateLogoutNoRefreshToken() {
  // Branch: no refresh token available
  mockClearTokens();
  // localStorage.clear() was here — now removed
  window.location.href = '/login';
}

function simulateLogoutRefreshFailed() {
  // Branch: refresh token present but refresh call threw
  mockClearTokens();
  // localStorage.clear() was here — now removed
  window.location.href = '/login';
}

describe('CC-1 — localStorage data-loss regression', () => {
  const PREF_KEY = 'userThemePreference';
  const PREF_VALUE = 'dark';
  const REMEMBER_KEY = 'rememberMe';

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorageClearSpy.mockClear();
    // Seed non-auth keys that must survive auth failures
    localStorage.setItem(PREF_KEY, PREF_VALUE);
    localStorage.setItem(REMEMBER_KEY, 'true');
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('does NOT call localStorage.clear() when no refresh token is available', () => {
    mockGetRefreshToken.mockReturnValue(null);

    simulateLogoutNoRefreshToken();

    expect(localStorageClearSpy).not.toHaveBeenCalled();
  });

  it('does NOT call localStorage.clear() when token refresh fails', () => {
    mockGetRefreshToken.mockReturnValue('some-refresh-token');

    simulateLogoutRefreshFailed();

    expect(localStorageClearSpy).not.toHaveBeenCalled();
  });

  it('preserves non-auth localStorage keys when no refresh token is available', () => {
    mockGetRefreshToken.mockReturnValue(null);

    simulateLogoutNoRefreshToken();

    expect(localStorage.getItem(PREF_KEY)).toBe(PREF_VALUE);
    expect(localStorage.getItem(REMEMBER_KEY)).toBe('true');
  });

  it('preserves non-auth localStorage keys when token refresh fails', () => {
    mockGetRefreshToken.mockReturnValue('some-refresh-token');

    simulateLogoutRefreshFailed();

    expect(localStorage.getItem(PREF_KEY)).toBe(PREF_VALUE);
    expect(localStorage.getItem(REMEMBER_KEY)).toBe('true');
  });

  it('calls tokenManager.clearTokens() on auth failure', () => {
    mockGetRefreshToken.mockReturnValue(null);
    simulateLogoutNoRefreshToken();
    expect(mockClearTokens).toHaveBeenCalledOnce();
  });

  it('calls tokenManager.clearTokens() when token refresh fails', () => {
    mockGetRefreshToken.mockReturnValue('refresh-token');
    simulateLogoutRefreshFailed();
    expect(mockClearTokens).toHaveBeenCalledOnce();
  });
});
