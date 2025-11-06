/**
 * Forgot Password Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Forgot Password page provides secure password reset request flow.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests form validation, submission, success state, error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ForgotPasswordPage } from './ForgotPasswordPage';
import { authService } from '../../../../services/authService';

// Mock authService
vi.mock('../../../../services/authService', () => ({
  authService: {
    requestPasswordReset: vi.fn(),
  },
}));

describe('ForgotPasswordPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderForgotPasswordPage = () => {
    return render(
      <BrowserRouter>
        <ForgotPasswordPage />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('renders forgot password page with all elements', () => {
      renderForgotPasswordPage();

      expect(screen.getByRole('heading', { name: 'Forgot Password?' })).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
    });

    it('renders back to login link', () => {
      renderForgotPasswordPage();

      const backLinks = screen.getAllByText(/back to login/i);
      expect(backLinks.length).toBeGreaterThan(0);
      backLinks.forEach((link) => {
        expect(link).toHaveAttribute('href', '/login');
      });
    });

    it('email input has autofocus', () => {
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toHaveFocus();
    });
  });

  describe('Form Validation', () => {
    it('shows error when email is empty', async () => {
      renderForgotPasswordPage();

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/email is required/i);
      expect(errorMessage).toBeInTheDocument();

      expect(authService.requestPasswordReset).not.toHaveBeenCalled();
    });

    it('shows error when email is invalid', async () => {
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'invalid-email');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/please enter a valid email address/i);
      expect(errorMessage).toBeInTheDocument();

      expect(authService.requestPasswordReset).not.toHaveBeenCalled();
    });

    it('clears error when user starts typing', async () => {
      renderForgotPasswordPage();

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/email is required/i);
      expect(errorMessage).toBeInTheDocument();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      await waitFor(() => {
        expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid email', async () => {
      vi.mocked(authService.requestPasswordReset).mockResolvedValue(undefined);
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(authService.requestPasswordReset).toHaveBeenCalledWith({
          email: 'test@example.com',
        });
      });
    });

    it('shows success message after successful submission', async () => {
      vi.mocked(authService.requestPasswordReset).mockResolvedValue(undefined);
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/check your email/i)).toBeInTheDocument();
        expect(screen.getByText(/test@example.com/i)).toBeInTheDocument();
      });
    });

    it('allows retry after success', async () => {
      vi.mocked(authService.requestPasswordReset).mockResolvedValue(undefined);
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/check your email/i)).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /try again/i });
      await userEvent.click(retryButton);

      // Should show form again
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('displays error message on request failure', async () => {
      vi.mocked(authService.requestPasswordReset).mockRejectedValue(
        new Error('Email not found')
      );
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'notfound@example.com');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Email not found')).toBeInTheDocument();
      });
    });

    it('displays generic error message for unknown errors', async () => {
      vi.mocked(authService.requestPasswordReset).mockRejectedValue('Unknown error');
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText('Failed to send reset email. Please try again.')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('disables input during loading', async () => {
      vi.mocked(authService.requestPasswordReset).mockImplementation(
        () => new Promise(() => {})
      ); // Never resolves
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeDisabled();
      });
    });

    it('shows loading button text', async () => {
      vi.mocked(authService.requestPasswordReset).mockImplementation(
        () => new Promise(() => {})
      );
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Sending...')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderForgotPasswordPage();

      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });

    it('error banner has alert role', async () => {
      vi.mocked(authService.requestPasswordReset).mockRejectedValue(new Error('Test error'));
      renderForgotPasswordPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveTextContent('Test error');
      });
    });

    it('form has noValidate to use custom validation', () => {
      const { container } = renderForgotPasswordPage();

      const form = container.querySelector('form');
      expect(form).toHaveAttribute('novalidate');
    });
  });
});
