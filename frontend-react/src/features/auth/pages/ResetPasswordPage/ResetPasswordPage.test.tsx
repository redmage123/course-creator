/**
 * Reset Password Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Reset Password page provides secure password update flow.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests token validation, form validation, submission, success state
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { ResetPasswordPage } from './ResetPasswordPage';
import { authService } from '../../../../services/authService';

// Mock authService
vi.mock('../../../../services/authService', () => ({
  authService: {
    confirmPasswordReset: vi.fn(),
  },
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

describe('ResetPasswordPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  const renderResetPasswordPage = (token = 'valid-token-123') => {
    return render(
      <MemoryRouter initialEntries={[`/reset-password?token=${token}`]}>
        <ResetPasswordPage />
      </MemoryRouter>
    );
  };

  describe('Rendering', () => {
    it('renders reset password page with all elements', () => {
      renderResetPasswordPage();

      expect(screen.getByRole('heading', { name: 'Reset Password' })).toBeInTheDocument();
      expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reset password/i })).toBeInTheDocument();
    });

    it('renders password requirements', () => {
      renderResetPasswordPage();

      expect(screen.getByText(/password must contain/i)).toBeInTheDocument();
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
      expect(screen.getByText(/one uppercase letter/i)).toBeInTheDocument();
      expect(screen.getByText(/one lowercase letter/i)).toBeInTheDocument();
      expect(screen.getByText(/one number/i)).toBeInTheDocument();
    });

    it('shows error when token is missing', () => {
      render(
        <MemoryRouter initialEntries={['/reset-password']}>
          <ResetPasswordPage />
        </MemoryRouter>
      );

      expect(
        screen.getByText(/invalid or missing reset token/i)
      ).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows error when password is empty', async () => {
      renderResetPasswordPage();

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/password is required/i);
      expect(errorMessage).toBeInTheDocument();

      expect(authService.confirmPasswordReset).not.toHaveBeenCalled();
    });

    it('shows error when password is too short', async () => {
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      await userEvent.type(passwordInput, 'Short1');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/password must be at least 8 characters/i);
      expect(errorMessage).toBeInTheDocument();
    });

    it('shows error when password missing lowercase', async () => {
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      await userEvent.type(passwordInput, 'PASSWORD123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(
        /password must contain at least one lowercase letter/i
      );
      expect(errorMessage).toBeInTheDocument();
    });

    it('shows error when password missing uppercase', async () => {
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      await userEvent.type(passwordInput, 'password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(
        /password must contain at least one uppercase letter/i
      );
      expect(errorMessage).toBeInTheDocument();
    });

    it('shows error when password missing number', async () => {
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      await userEvent.type(passwordInput, 'PasswordABC');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(
        /password must contain at least one number/i
      );
      expect(errorMessage).toBeInTheDocument();
    });

    it('shows error when passwords do not match', async () => {
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password456');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/passwords do not match/i);
      expect(errorMessage).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid password', async () => {
      vi.mocked(authService.confirmPasswordReset).mockResolvedValue(undefined);
      renderResetPasswordPage('test-token-123');

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(authService.confirmPasswordReset).toHaveBeenCalledWith({
          token: 'test-token-123',
          newPassword: 'Password123',
        });
      });
    });

    it('shows success message after successful submission', async () => {
      vi.mocked(authService.confirmPasswordReset).mockResolvedValue(undefined);
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password reset successful/i)).toBeInTheDocument();
      });
    });

    it('shows auto-redirect message', async () => {
      vi.mocked(authService.confirmPasswordReset).mockResolvedValue(undefined);
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/redirecting to login page in 3 seconds/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message on reset failure', async () => {
      vi.mocked(authService.confirmPasswordReset).mockRejectedValue(
        new Error('Invalid or expired token')
      );
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Invalid or expired token')).toBeInTheDocument();
      });
    });

    it('displays generic error message for unknown errors', async () => {
      vi.mocked(authService.confirmPasswordReset).mockRejectedValue('Unknown error');
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/failed to reset password/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('disables inputs during loading', async () => {
      vi.mocked(authService.confirmPasswordReset).mockImplementation(
        () => new Promise(() => {})
      );
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/new password/i)).toBeDisabled();
        expect(screen.getByLabelText(/confirm password/i)).toBeDisabled();
      });
    });

    it('shows loading button text', async () => {
      vi.mocked(authService.confirmPasswordReset).mockImplementation(
        () => new Promise(() => {})
      );
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Resetting Password...')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderResetPasswordPage();

      expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    it('error banner has alert role', async () => {
      vi.mocked(authService.confirmPasswordReset).mockRejectedValue(new Error('Test error'));
      renderResetPasswordPage();

      const passwordInput = screen.getByLabelText(/new password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /reset password/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveTextContent('Test error');
      });
    });
  });
});
