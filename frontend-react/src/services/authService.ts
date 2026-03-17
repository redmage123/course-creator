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
import { tokenManager } from './tokenManager';
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
    full_name?: string;
    role: UserRole;
    organizationId?: string;
    organization?: string;
  };
  expiresIn: number;
  isFirstLogin?: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  fullName: string;
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
      // Backend returns: { access_token, token_type, expires_in, user }
      // Frontend expects: { token, refreshToken, user, expiresIn }
      const backendResponse: any = await apiClient.post('/auth/login', credentials);

      // Calculate token expiration timestamp
      const expiresAt = Date.now() + backendResponse.expires_in * 1000;

      // Transform backend response to match frontend LoginResponse interface
      return {
        token: backendResponse.access_token,
        refreshToken: backendResponse.refresh_token,
        user: {
          id: backendResponse.user.id,
          username: backendResponse.user.username,
          email: backendResponse.user.email,
          full_name: backendResponse.user.full_name,
          role: backendResponse.user.role,
          organizationId: backendResponse.user.organization_id,
          organization: backendResponse.user.organization,
        },
        expiresIn: expiresAt,
        isFirstLogin: backendResponse.is_first_login || false,
      };
    } catch (error: any) {
      console.error('[AuthService] Login failed:', error);
      // Handle rate limiting (429 Too Many Requests)
      if (error?.status === 429 || error?.response?.status === 429) {
        throw new Error('Too many login attempts. Please try again later.');
      }
      // Handle other errors
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
      // Clear all auth data from memory
      tokenManager.clearTokens();
      // Clear non-token data from localStorage (for role-based routing only)
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
      // Transform camelCase frontend data to snake_case for backend
      const backendData = {
        username: data.username,
        email: data.email,
        full_name: data.fullName,
        password: data.password,
        first_name: data.firstName,
        last_name: data.lastName,
        role: 'student', // Default role for self-registration
      };

      const response = await apiClient.post<any>('/auth/register', backendData);

      // Backend returns user object, need to construct login response
      // After successful registration, user may need to login separately
      // or backend may return a token - handle both cases
      if (response.access_token) {
        const expiresAt = Date.now() + (response.expires_in || 3600) * 1000;
        return {
          token: response.access_token,
          user: {
            id: response.user?.id || response.id,
            username: response.user?.username || response.username,
            email: response.user?.email || response.email,
            role: response.user?.role || response.role || 'student',
            organizationId: response.user?.organization_id,
          },
          expiresIn: expiresAt,
        };
      }

      // If no token returned, registration succeeded but user needs to login
      return {
        token: '',
        user: {
          id: response.id,
          username: response.username,
          email: response.email,
          role: response.role || 'student',
        },
        expiresIn: 0,
      };
    } catch (error: any) {
      console.error('[AuthService] Registration failed:', error);
      // Extract error message from response if available
      const errorMessage = error?.response?.data?.detail ||
                          error?.message ||
                          'Registration failed. Username or email may already exist.';
      throw new Error(errorMessage);
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
   * Change password for authenticated user
   *
   * BUSINESS LOGIC:
   * Allows authenticated users to change their password by providing
   * current password for verification and new password.
   * Distinct from password reset flow (which uses email token).
   *
   * @param data - Current and new password
   */
  async changePassword(data: { current_password: string; new_password: string }): Promise<void> {
    try {
      await apiClient.post('/auth/change-password', data);
    } catch (error) {
      console.error('[AuthService] Password change failed:', error);
      throw error;
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
    return tokenManager.hasToken();
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
