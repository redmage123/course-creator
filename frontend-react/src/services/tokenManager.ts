/**
 * Token Manager Service
 *
 * BUSINESS CONTEXT:
 * Manages JWT tokens in-memory for enhanced security. Tokens are never persisted
 * to localStorage, reducing XSS attack surface. Users must re-authenticate on
 * page reload, which is a security trade-off for better token protection.
 *
 * TECHNICAL IMPLEMENTATION:
 * Simple in-memory storage for access and refresh tokens. Tokens are cleared
 * on page reload/refresh. This prevents token theft via localStorage access
 * but requires users to login again after browser refresh.
 *
 * WHY THIS APPROACH:
 * - Prevents XSS attacks from stealing tokens via localStorage
 * - Reduces attack surface for credential theft
 * - Industry best practice for high-security applications
 * - Trade-off: Convenience (session persistence) vs Security (token safety)
 */

/**
 * In-memory token storage
 * Tokens stored here are cleared on page reload
 */
let accessToken: string | null = null;
let refreshToken: string | null = null;

/**
 * Token Manager - Secure in-memory token storage
 *
 * SECURITY BENEFITS:
 * - Tokens never touch localStorage (XSS-proof)
 * - No persistent token storage in browser
 * - Automatic cleanup on page navigation/reload
 * - Cannot be accessed by malicious scripts reading localStorage
 */
export const tokenManager = {
  /**
   * Get current access token
   * @returns Access token or null if not set
   */
  getToken: (): string | null => {
    return accessToken;
  },

  /**
   * Set access token
   * @param token - JWT access token to store in memory
   */
  setToken: (token: string | null): void => {
    accessToken = token;
  },

  /**
   * Get current refresh token
   * @returns Refresh token or null if not set
   */
  getRefreshToken: (): string | null => {
    return refreshToken;
  },

  /**
   * Set refresh token
   * @param token - JWT refresh token to store in memory
   */
  setRefreshToken: (token: string | null): void => {
    refreshToken = token;
  },

  /**
   * Clear all tokens from memory
   * Called during logout or session expiration
   */
  clearTokens: (): void => {
    accessToken = null;
    refreshToken = null;
  },

  /**
   * Check if access token exists
   * @returns True if token is set, false otherwise
   */
  hasToken: (): boolean => {
    return accessToken !== null;
  },
};
