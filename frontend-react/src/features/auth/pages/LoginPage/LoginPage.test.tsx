/**
 * Login Page Component Tests — CC-4
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Login page provides secure, accessible,
 * and user-friendly authentication flow using react-hook-form + zod.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing.
 * Tests form validation (zod schema), submission, error handling, and navigation.
 *
 * SCHEMA COVERAGE:
 * - identifier: required, min 3 chars
 * - password: required, min 8 chars
 * - rememberMe: boolean (default false)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { LoginPage } from './LoginPage';

// Mock useAuth hook
const mockLogin = vi.fn();
const mockUseAuth = vi.fn(() => ({
  login: mockLogin,
  isLoading: false,
}));

vi.mock('../../../../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      isLoading: false,
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  const renderLoginPage = () => {
    return render(
      <HelmetProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </HelmetProvider>
    );
  };

  describe('Rendering', () => {
    it('renders login page with all elements', () => {
      renderLoginPage();

      expect(screen.getByText('Welcome Back')).toBeInTheDocument();
      expect(screen.getByText('Sign in to your Course Creator account')).toBeInTheDocument();
      expect(screen.getByLabelText(/email or username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    it('renders remember me checkbox', () => {
      renderLoginPage();
      expect(screen.getByLabelText('Remember me')).toBeInTheDocument();
    });

    it('renders forgot password link', () => {
      renderLoginPage();
      const forgotLink = screen.getByText('Forgot password?');
      expect(forgotLink).toBeInTheDocument();
      expect(forgotLink).toHaveAttribute('href', '/forgot-password');
    });

    it('renders registration link', () => {
      renderLoginPage();
      const registerLink = screen.getByText('Create one now');
      expect(registerLink).toBeInTheDocument();
      expect(registerLink).toHaveAttribute('href', '/register');
    });

    it('identifier input has autofocus', () => {
      renderLoginPage();
      const identifierInput = screen.getByLabelText(/email or username/i);
      expect(identifierInput).toHaveFocus();
    });
  });

  describe('Zod schema validation', () => {
    it('shows error when identifier is empty (required)', async () => {
      renderLoginPage();

      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      const errorMessage = await screen.findByText(/email or username is required/i);
      expect(errorMessage).toBeInTheDocument();
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('shows error when identifier is too short (< 3 chars)', async () => {
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'ab');
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      const errorMessage = await screen.findByText(/please enter a valid email or username/i);
      expect(errorMessage).toBeInTheDocument();
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('shows error when password is empty (required)', async () => {
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'testuser');
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      const errorMessage = await screen.findByText(/password is required/i);
      expect(errorMessage).toBeInTheDocument();
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('shows error when password is too short (< 8 chars)', async () => {
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'testuser');
      await userEvent.type(screen.getByLabelText(/password/i), 'short');
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      const errorMessage = await screen.findByText(/password must be at least 8 characters/i);
      expect(errorMessage).toBeInTheDocument();
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('zod schema rejects passwords shorter than 8 characters', async () => {
      // Directly test schema
      const { z } = await import('zod');
      const schema = z.object({
        identifier: z.string().min(1).min(3),
        password: z.string().min(1).min(8),
        rememberMe: z.boolean(),
      });

      const result = schema.safeParse({ identifier: 'user', password: 'short', rememberMe: false });
      expect(result.success).toBe(false);
      if (!result.success) {
        const passwordError = result.error.issues.find((i) => i.path[0] === 'password');
        expect(passwordError).toBeDefined();
      }
    });

    it('zod schema accepts valid credentials', async () => {
      const { z } = await import('zod');
      const schema = z.object({
        identifier: z.string().min(1).min(3),
        password: z.string().min(1).min(8),
        rememberMe: z.boolean(),
      });

      const result = schema.safeParse({
        identifier: 'validuser',
        password: 'validpassword',
        rememberMe: false,
      });
      expect(result.success).toBe(true);
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid credentials', async () => {
      mockLogin.mockResolvedValue(undefined);
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'test@example.com');
      await userEvent.type(screen.getByLabelText(/password/i), 'password123');
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'test@example.com',
          password: 'password123',
        });
      });
    });

    it('stores rememberMe in localStorage when checked', async () => {
      mockLogin.mockResolvedValue(undefined);
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'test@example.com');
      await userEvent.type(screen.getByLabelText(/password/i), 'password123');
      await userEvent.click(screen.getByLabelText('Remember me'));
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled();
        expect(localStorage.getItem('rememberMe')).toBe('true');
      });
    });

    it('removes rememberMe from localStorage when unchecked', async () => {
      localStorage.setItem('rememberMe', 'true');
      mockLogin.mockResolvedValue(undefined);
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'test@example.com');
      await userEvent.type(screen.getByLabelText(/password/i), 'password123');
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(localStorage.getItem('rememberMe')).toBeNull();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message on login failure', async () => {
      mockLogin.mockRejectedValue(new Error('Invalid credentials'));
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'test@example.com');
      await userEvent.type(screen.getByLabelText(/password/i), 'wrongpassword');
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
      });
    });

    it('displays generic error for unknown errors', async () => {
      mockLogin.mockRejectedValue('Unknown error');
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'test@example.com');
      await userEvent.type(screen.getByLabelText(/password/i), 'password123');
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(
          screen.getByText('Login failed. Please check your credentials and try again.')
        ).toBeInTheDocument();
      });
    });

    it('error banner has alert role', async () => {
      mockLogin.mockRejectedValue(new Error('Test error'));
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'test@example.com');
      await userEvent.type(screen.getByLabelText(/password/i), 'password123');
      await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveTextContent('Test error');
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading text during login', () => {
      mockUseAuth.mockReturnValue({ login: mockLogin, isLoading: true });
      renderLoginPage();
      expect(screen.getByText('Signing in...')).toBeInTheDocument();
    });

    it('disables submit button during loading', () => {
      mockUseAuth.mockReturnValue({ login: mockLogin, isLoading: true });
      renderLoginPage();
      expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
    });

    it('disables inputs during loading', () => {
      mockUseAuth.mockReturnValue({ login: mockLogin, isLoading: true });
      renderLoginPage();
      expect(screen.getByLabelText(/email or username/i)).toBeDisabled();
      expect(screen.getByLabelText(/password/i)).toBeDisabled();
      expect(screen.getByLabelText('Remember me')).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderLoginPage();
      expect(screen.getByLabelText(/email or username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('form has noValidate attribute', () => {
      const { container } = renderLoginPage();
      const form = container.querySelector('form');
      expect(form).toHaveAttribute('novalidate');
    });
  });

  describe('Keyboard Navigation', () => {
    it('can submit form with Enter key', async () => {
      mockLogin.mockResolvedValue(undefined);
      renderLoginPage();

      await userEvent.type(screen.getByLabelText(/email or username/i), 'test@example.com');
      await userEvent.type(screen.getByLabelText(/password/i), 'password123{Enter}');

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'test@example.com',
          password: 'password123',
        });
      });
    });
  });
});
