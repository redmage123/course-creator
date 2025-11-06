/**
 * Authentication Service
 *
 * BUSINESS CONTEXT:
 * Handles all authentication operations including login, logout, registration,
 * password reset, and token management for the Course Creator Platform.
 *
 * TECHNICAL IMPLEMENTATION:
 * Communicates with user-management service (port 8000) for authentication
 * operations. Manages JWT tokens and session persistence.
 */

import { apiClient } from './apiClient';
import type { UserRole } from '@store/slices/authSlice';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  refreshToken?: string;
  user: {
    id: string;
    username: string;
    email: string;
    role: UserRole;
    organizationId?: string;
  };
  expiresIn: number;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
  newsletterOptIn?: boolean;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  newPassword: string;
}

/**
 * Authentication Service Class
 *
 * WHY THIS APPROACH:
 * - Centralized authentication logic
 * - Type-safe API calls
 * - Consistent error handling
 * - Easy to mock for testing
 */
class AuthService {
  /**
   * Login user with credentials
   *
   * BUSINESS LOGIC:
   * Authenticates user against user-management service. Returns JWT token
   * and user profile data for session management.
   *
   * @param credentials - Username and password
   * @returns Login response with token and user data
   * @throws Error if credentials are invalid
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', credentials);

      // Calculate token expiration timestamp
      const expiresAt = Date.now() + response.expiresIn * 1000;

      return {
        ...response,
        expiresIn: expiresAt,
      };
    } catch (error) {
      console.error('[AuthService] Login failed:', error);
      throw new Error('Invalid credentials. Please try again.');
    }
  }

  /**
   * Logout current user
   *
   * BUSINESS LOGIC:
   * Invalidates the current session and clears all stored authentication data.
   * Notifies backend to blacklist the token.
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('[AuthService] Logout failed:', error);
      // Continue with local logout even if API call fails
    } finally {
      // Clear all auth data from localStorage
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userId');
      localStorage.removeItem('organizationId');
    }
  }

  /**
   * Refresh authentication token
   *
   * BUSINESS LOGIC:
   * Exchanges refresh token for a new access token when the current token expires.
   * Prevents users from being logged out during active sessions.
   *
   * @param refreshToken - Current refresh token
   * @returns New access token and expiration
   */
  async refreshToken(refreshToken: string): Promise<{ token: string; expiresAt: number }> {
    try {
      const response = await apiClient.post<{ token: string; expiresIn: number }>(
        '/auth/refresh',
        { refreshToken }
      );

      const expiresAt = Date.now() + response.expiresIn * 1000;

      return {
        token: response.token,
        expiresAt,
      };
    } catch (error) {
      console.error('[AuthService] Token refresh failed:', error);
      throw new Error('Session expired. Please login again.');
    }
  }

  /**
   * Register new user account
   *
   * BUSINESS LOGIC:
   * Creates new user account with provided information. Default role is 'student'.
   * Org admins and site admins are created through different workflows.
   *
   * @param data - Registration information
   * @returns Created user profile
   */
  async register(data: RegisterData): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/register', data);

      const expiresAt = Date.now() + response.expiresIn * 1000;

      return {
        ...response,
        expiresIn: expiresAt,
      };
    } catch (error) {
      console.error('[AuthService] Registration failed:', error);
      throw new Error('Registration failed. Username or email may already exist.');
    }
  }

  /**
   * Request password reset
   *
   * BUSINESS LOGIC:
   * Sends password reset email to user's registered email address.
   * Email contains time-limited reset token.
   *
   * @param data - Email address
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
    try {
      await apiClient.post('/auth/password-reset/request', data);
    } catch (error) {
      console.error('[AuthService] Password reset request failed:', error);
      throw new Error('Failed to send password reset email.');
    }
  }

  /**
   * Confirm password reset with token
   *
   * BUSINESS LOGIC:
   * Validates reset token and updates user password.
   * Token expires after 1 hour for security.
   *
   * @param data - Reset token and new password
   */
  async confirmPasswordReset(data: PasswordResetConfirm): Promise<void> {
    try {
      await apiClient.post('/auth/password-reset/confirm', data);
    } catch (error) {
      console.error('[AuthService] Password reset confirmation failed:', error);
      throw new Error('Invalid or expired reset token.');
    }
  }

  /**
   * Get current user profile
   *
   * BUSINESS LOGIC:
   * Fetches current user's profile data using the JWT token.
   * Used to restore session on page reload.
   *
   * @returns User profile data
   */
  async getCurrentUser(): Promise<LoginResponse['user']> {
    try {
      const response = await apiClient.get<LoginResponse['user']>('/users/me');
      return response;
    } catch (error) {
      console.error('[AuthService] Get current user failed:', error);
      throw new Error('Failed to fetch user profile.');
    }
  }

  /**
   * Check if user is authenticated
   *
   * @returns True if valid token exists
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('authToken');
    return !!token;
  }

  /**
   * Get current user's role
   *
   * @returns User role or null
   */
  getCurrentRole(): UserRole | null {
    return (localStorage.getItem('userRole') as UserRole) || null;
  }
}

// Export singleton instance
export const authService = new AuthService();
