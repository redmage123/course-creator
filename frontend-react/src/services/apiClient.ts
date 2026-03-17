/**
 * API Client Service
 *
 * BUSINESS CONTEXT:
 * Centralized HTTP client for communicating with backend microservices.
 * Handles authentication, request/response interceptors, and error handling.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses axios for HTTP requests with automatic JWT token injection,
 * request retries, and standardized error handling.
 */

import axios, { type AxiosInstance, AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { tokenManager } from './tokenManager';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

/**
 * Create axios instance with default configuration
 *
 * WHY THIS APPROACH:
 * - Centralized configuration for all API calls
 * - Automatic JWT token injection via interceptors
 * - Standardized error handling
 * - Request/response logging in development
 */
class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        // CSRF protection: Custom header that cross-origin requests cannot set
        // This header indicates the request was made by our application
        'X-Requested-With': 'XMLHttpRequest',
      },
      // Ensure cookies are sent with requests (if any)
      withCredentials: true,
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   *
   * WHY THIS APPROACH:
   * - Automatic token injection prevents manual token handling
   * - Centralized error handling reduces code duplication
   * - Request logging aids debugging in development
   */
  private setupInterceptors() {
    // Request interceptor - add auth token from memory
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = tokenManager.getToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Log requests in development
        if (import.meta.env.DEV) {
          console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
        }

        return config;
      },
      (error: AxiosError) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => {
        if (import.meta.env.DEV) {
          console.log(`[API Response] ${response.config.url}`, response.data);
        }
        return response;
      },
      async (error: AxiosError) => {
        // Handle 401 Unauthorized - token expired
        // IMPORTANT: Don't redirect for login endpoint - let the error propagate
        // so the Login component can display the error message to the user
        const isLoginRequest = error.config?.url?.includes('/auth/login');

        if (error.response?.status === 401 && !isLoginRequest) {
          const refreshToken = tokenManager.getRefreshToken();
          if (refreshToken) {
            try {
              // Attempt token refresh
              const response = await axios.post(
                `${API_BASE_URL}/auth/refresh`,
                { refreshToken }
              );
              const { token } = response.data;
              tokenManager.setToken(token);

              // Retry original request with new token
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${token}`;
                return this.client(error.config);
              }
            } catch (refreshError) {
              // Refresh failed - logout user
              tokenManager.clearTokens();
              localStorage.clear();
              window.location.href = '/login';
            }
          } else {
            // No refresh token - logout
            tokenManager.clearTokens();
            localStorage.clear();
            window.location.href = '/login';
          }
        }

        console.error('[API Response Error]', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  /**
   * HTTP GET request
   */
  async get<T>(url: string, config = {}): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  /**
   * HTTP POST request
   */
  async post<T>(url: string, data?: unknown, config = {}): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  /**
   * HTTP PUT request
   */
  async put<T>(url: string, data?: unknown, config = {}): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  /**
   * HTTP PATCH request
   */
  async patch<T>(url: string, data?: unknown, config = {}): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  /**
   * HTTP DELETE request
   */
  async delete<T>(url: string, config = {}): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();
