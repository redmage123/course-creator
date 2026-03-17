/**
 * Password Reset Flow Integration Tests
 *
 * BUSINESS CONTEXT:
 * Tests complete password reset workflow including forgot password request and reset confirmation.
 * Validates proper integration between password reset pages, authService, and navigation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests two-step password reset flow (request + confirm)
 * - Mocks API calls but tests real service layer logic
 * - Tests email validation and token handling
 * - Tests user interactions across multiple pages
 *
 * INTEGRATION SCOPE:
 * - ForgotPasswordPage + ResetPasswordPage components
 * - authService password reset methods
 * - Navigation between password reset steps
 * - Success/error message handling
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, setupUserEvent } from '../../utils';
import { ForgotPasswordPage } from '@features/auth/ForgotPassword';
import { ResetPasswordPage } from '@features/auth/ResetPassword';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';

// Mock useNavigate and useSearchParams (framework mocks, not service mocks)
const mockNavigate = vi.fn();
const mockSearchParams = new URLSearchParams();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [mockSearchParams, vi.fn()],
  };
});

describe('Password Reset Flow Integration Tests', () => {
  const user = setupUserEvent();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    mockSearchParams.delete('token');
    server.resetHandlers();
  });

  describe('Forgot Password Request Flow', () => {
    it('should complete successful password reset request flow', async () => {
      /**
       * INTEGRATION TEST: Complete Forgot Password Request Workflow
       *
       * SIMULATES:
       * 1. User navigates to forgot password page
       * 2. User enters email address
       * 3. User submits form
       * 4. API call sends reset email
       * 5. Success message is displayed
       * 6. Instructions are shown to check email
       */

      // Default MSW handler handles password reset request

      renderWithProviders(<ForgotPasswordPage />);

      // Act - Step 1: Enter email
      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, 'user@example.com');

      // Act - Step 2: Submit form
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await user.click(submitButton);

      // API call happens (real service with MSW)

      // Assert - Success message is displayed
      await waitFor(() => {
        expect(screen.getByText(/check your email/i)).toBeInTheDocument();
      });

      // Assert - Instructions are shown
      expect(screen.getByText(/sent.*instructions/i)).toBeInTheDocument();
    });

    it('should validate email format before submission', async () => {
      /**
       * INTEGRATION TEST: Email Validation in Forgot Password
       */

      renderWithProviders(<ForgotPasswordPage />);

      // Act - Enter invalid email
      await user.type(screen.getByLabelText(/email/i), 'invalid-email');
      await user.click(screen.getByRole('button', { name: /send reset link/i }));

      // Assert - Validation error is shown
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/valid email/i);
      });

      // Assert - Error shown, no success message
      expect(screen.queryByText(/check your email/i)).not.toBeInTheDocument();
    });

    it('should handle API errors gracefully', async () => {
      /**
       * INTEGRATION TEST: Error Handling in Forgot Password
       *
       * SIMULATES:
       * 1. User submits email
       * 2. API returns error (e.g., email not found)
       * 3. Error message is displayed
       * 4. User can retry
       */

      // Override MSW to return error
      server.use(
        http.post('https://176.9.99.103:8000/auth/password-reset/request', () => {
          return HttpResponse.json(
            { message: 'Failed to send password reset email.' },
            { status: 500 }
          );
        })
      );

      renderWithProviders(<ForgotPasswordPage />);

      // Act
      await user.type(screen.getByLabelText(/email/i), 'nonexistent@example.com');
      await user.click(screen.getByRole('button', { name: /send reset link/i }));

      // Assert - Error message is displayed
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/failed/i);
      });
    });

    it('should show loading state during API call', async () => {
      /**
       * INTEGRATION TEST: Loading State in Forgot Password
       */

      // Override MSW with delayed response
      server.use(
        http.post('https://176.9.99.103:8000/auth/password-reset/request', async () => {
          await new Promise(resolve => setTimeout(resolve, 100));
          return HttpResponse.json({ success: true, message: 'Reset email sent' });
        })
      );

      renderWithProviders(<ForgotPasswordPage />);

      // Act
      await user.type(screen.getByLabelText(/email/i), 'user@example.com');
      await user.click(screen.getByRole('button', { name: /send reset link/i }));

      // Assert - Loading state is shown
      expect(screen.getByRole('button', { name: /sending/i })).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText(/check your email/i)).toBeInTheDocument();
      });
    });

    it('should navigate back to login page via link', async () => {
      /**
       * INTEGRATION TEST: Navigation to Login from Forgot Password
       */

      renderWithProviders(<ForgotPasswordPage />, {
        initialEntries: ['/forgot-password'],
      });

      // Assert - Login link exists
      const loginLink = screen.getByRole('link', { name: /back to login|sign in/i });
      expect(loginLink).toHaveAttribute('href', '/login');
    });
  });

  describe('Password Reset Confirmation Flow', () => {
    it('should complete successful password reset confirmation flow', async () => {
      /**
       * INTEGRATION TEST: Complete Password Reset Confirmation Workflow
       *
       * SIMULATES:
       * 1. User clicks reset link in email (arrives with token in URL)
       * 2. User enters new password
       * 3. User confirms new password
       * 4. User submits form
       * 5. API validates token and updates password
       * 6. Success message is displayed
       * 7. User is redirected to login page
       */

      // Arrange - Set token in URL params
      mockSearchParams.set('token', 'valid-reset-token-123');

      // Default MSW handler handles password reset confirmation

      renderWithProviders(<ResetPasswordPage />);

      // Act - Step 1: Enter new password
      const passwordInput = screen.getByLabelText(/new password/i);
      await user.type(passwordInput, 'NewSecurePass123!');

      // Act - Step 2: Confirm new password
      const confirmPasswordInput = screen.getByLabelText(/confirm.*password/i);
      await user.type(confirmPasswordInput, 'NewSecurePass123!');

      // Act - Step 3: Submit form
      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await user.click(submitButton);

      // API call happens (real service with MSW)

      // Assert - Success message is displayed
      await waitFor(() => {
        expect(screen.getByText(/password.*reset.*success/i)).toBeInTheDocument();
      });

      // Assert - Navigation to login page
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      });
    });

    it('should validate password match', async () => {
      /**
       * INTEGRATION TEST: Password Match Validation
       */

      mockSearchParams.set('token', 'valid-token');

      renderWithProviders(<ResetPasswordPage />);

      // Act - Enter mismatched passwords
      await user.type(screen.getByLabelText(/new password/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm.*password/i), 'DifferentPassword123!');
      await user.click(screen.getByRole('button', { name: /reset password/i }));

      // Assert - Validation error is shown
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/passwords.*match/i);
      });

      // Assert - No navigation (validation prevented submission)
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('should validate password strength', async () => {
      /**
       * INTEGRATION TEST: Password Strength Validation in Reset
       */

      mockSearchParams.set('token', 'valid-token');

      renderWithProviders(<ResetPasswordPage />);

      // Act - Enter weak password
      await user.type(screen.getByLabelText(/new password/i), 'weak');
      await user.type(screen.getByLabelText(/confirm.*password/i), 'weak');
      await user.click(screen.getByRole('button', { name: /reset password/i }));

      // Assert - Validation error is shown
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(
          /password.*8 characters|password.*strong/i
        );
      });

      // Assert - No navigation (validation prevented submission)
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('should handle expired or invalid token', async () => {
      /**
       * INTEGRATION TEST: Invalid/Expired Token Handling
       *
       * SIMULATES:
       * 1. User clicks old reset link with expired token
       * 2. User enters new password
       * 3. API rejects expired token
       * 4. Error message is displayed
       * 5. Link to request new reset is shown
       */

      mockSearchParams.set('token', 'expired-token');

      // Override MSW to return token validation error
      server.use(
        http.post('https://176.9.99.103:8000/auth/password-reset/confirm', () => {
          return HttpResponse.json(
            { message: 'Invalid or expired reset token.' },
            { status: 400 }
          );
        })
      );

      renderWithProviders(<ResetPasswordPage />);

      // Act
      await user.type(screen.getByLabelText(/new password/i), 'NewPassword123!');
      await user.type(screen.getByLabelText(/confirm.*password/i), 'NewPassword123!');
      await user.click(screen.getByRole('button', { name: /reset password/i }));

      // Assert - Error message is displayed
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/invalid|expired/i);
      });

      // Assert - Link to request new reset exists
      expect(screen.getByRole('link', { name: /request.*reset/i })).toHaveAttribute(
        'href',
        '/forgot-password'
      );
    });

    it('should show error if no token in URL', async () => {
      /**
       * INTEGRATION TEST: Missing Token Validation
       *
       * BUSINESS REQUIREMENT:
       * Reset page requires token in URL query params
       */

      // Note: No token set in mockSearchParams

      renderWithProviders(<ResetPasswordPage />);

      // Assert - Error message about missing token
      expect(screen.getByText(/invalid.*link|missing.*token/i)).toBeInTheDocument();

      // Assert - Submit button should be disabled or form hidden
      const submitButton = screen.queryByRole('button', { name: /reset password/i });
      expect(submitButton).toBeDisabled();
    });

    it('should show loading state during password reset', async () => {
      /**
       * INTEGRATION TEST: Loading State in Password Reset
       */

      mockSearchParams.set('token', 'valid-token');

      // Override MSW with delayed response
      server.use(
        http.post('https://176.9.99.103:8000/auth/password-reset/confirm', async () => {
          await new Promise(resolve => setTimeout(resolve, 100));
          return HttpResponse.json({ success: true, message: 'Password reset successful' });
        })
      );

      renderWithProviders(<ResetPasswordPage />);

      // Act
      await user.type(screen.getByLabelText(/new password/i), 'NewPassword123!');
      await user.type(screen.getByLabelText(/confirm.*password/i), 'NewPassword123!');
      await user.click(screen.getByRole('button', { name: /reset password/i }));

      // Assert - Loading state is shown
      expect(screen.getByRole('button', { name: /resetting/i })).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalled();
      });
    });
  });

  describe('Complete Password Reset Journey', () => {
    it('should complete full password reset journey from forgot to reset', async () => {
      /**
       * INTEGRATION TEST: End-to-End Password Reset Journey
       *
       * SIMULATES COMPLETE USER JOURNEY:
       * 1. User forgets password
       * 2. Requests reset via email
       * 3. Receives email with reset link
       * 4. Clicks link (arrives at reset page with token)
       * 5. Enters new password
       * 6. Successfully resets password
       * 7. Redirected to login
       * 8. Can log in with new password
       *
       * This test documents the complete flow across multiple pages
       */

      // Step 1: Forgot Password Request
      // Default MSW handler handles password reset request

      const { unmount } = renderWithProviders(<ForgotPasswordPage />);

      await user.type(screen.getByLabelText(/email/i), 'user@example.com');
      await user.click(screen.getByRole('button', { name: /send reset link/i }));

      await waitFor(() => {
        expect(screen.getByText(/check your email/i)).toBeInTheDocument();
      });

      unmount();

      // Step 2: Password Reset Confirmation (user clicked email link)
      mockSearchParams.set('token', 'reset-token-from-email');
      // Default MSW handler handles password reset confirmation

      renderWithProviders(<ResetPasswordPage />);

      await user.type(screen.getByLabelText(/new password/i), 'MyNewPassword123!');
      await user.type(screen.getByLabelText(/confirm.*password/i), 'MyNewPassword123!');
      await user.click(screen.getByRole('button', { name: /reset password/i }));

      // Assert - Complete flow successful
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      });
    });
  });
});
