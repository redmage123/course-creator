/**
 * Registration Page Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Registration page provides secure, accessible,
 * and GDPR/CCPA-compliant user onboarding flow.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests form validation, submission, error handling, terms acceptance
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { RegistrationPage } from './RegistrationPage';

// Mock useAuth hook
const mockRegister = vi.fn();
const mockUseAuth = vi.fn(() => ({
  register: mockRegister,
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

describe('RegistrationPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      register: mockRegister,
      isLoading: false,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderRegistrationPage = () => {
    return render(
      <HelmetProvider>
        <BrowserRouter>
          <RegistrationPage />
        </BrowserRouter>
      </HelmetProvider>
    );
  };

  describe('Rendering', () => {
    it('renders registration page with all elements', () => {
      renderRegistrationPage();

      expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument();
      expect(screen.getByText('Join the Course Creator Platform')).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
    });

    it('renders terms and privacy checkboxes', () => {
      renderRegistrationPage();

      expect(screen.getByText(/Terms of Service/i)).toBeInTheDocument();
      expect(screen.getByText(/Privacy Policy/i)).toBeInTheDocument();
    });

    it('renders newsletter opt-in checkbox', () => {
      renderRegistrationPage();

      expect(
        screen.getByText(/Send me updates and educational content via email/i)
      ).toBeInTheDocument();
    });

    it('renders login link', () => {
      renderRegistrationPage();

      const loginLink = screen.getByText('Sign in');
      expect(loginLink).toBeInTheDocument();
      expect(loginLink).toHaveAttribute('href', '/login');
    });

    it('email input has autofocus', () => {
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toHaveFocus();
    });
  });

  describe('Form Validation - Email', () => {
    it('shows error when email is empty', async () => {
      renderRegistrationPage();

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/email is required/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when email is invalid', async () => {
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'invalid-email');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/please enter a valid email address/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });
  });

  describe('Form Validation - Username', () => {
    it('shows error when username is empty', async () => {
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      await userEvent.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/username is required/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when username is too short', async () => {
      renderRegistrationPage();

      const usernameInput = screen.getByLabelText(/^username/i);
      await userEvent.type(usernameInput, 'ab');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/username must be at least 3 characters/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when username contains invalid characters', async () => {
      renderRegistrationPage();

      const usernameInput = screen.getByLabelText(/^username/i);
      await userEvent.type(usernameInput, 'user@name!');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(
        /username can only contain letters, numbers, hyphens, and underscores/i
      );
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });
  });

  describe('Form Validation - Password', () => {
    it('shows error when password is empty', async () => {
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/password is required/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when password is too short', async () => {
      renderRegistrationPage();

      const passwordInput = screen.getByLabelText(/^password/i);
      await userEvent.type(passwordInput, 'Short1');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/password must be at least 8 characters/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when password missing lowercase', async () => {
      renderRegistrationPage();

      const passwordInput = screen.getByLabelText(/^password/i);
      await userEvent.type(passwordInput, 'PASSWORD123');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(
        /password must contain at least one lowercase letter/i
      );
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when password missing uppercase', async () => {
      renderRegistrationPage();

      const passwordInput = screen.getByLabelText(/^password/i);
      await userEvent.type(passwordInput, 'password123');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(
        /password must contain at least one uppercase letter/i
      );
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when password missing number', async () => {
      renderRegistrationPage();

      const passwordInput = screen.getByLabelText(/^password/i);
      await userEvent.type(passwordInput, 'PasswordABC');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(
        /password must contain at least one number/i
      );
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });
  });

  describe('Form Validation - Confirm Password', () => {
    it('shows error when confirm password is empty', async () => {
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/please confirm your password/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when passwords do not match', async () => {
      renderRegistrationPage();

      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password456');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/passwords do not match/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });
  });

  describe('Form Validation - Terms Acceptance', () => {
    it('shows error when terms not accepted', async () => {
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/you must accept the terms of service/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });

    it('shows error when privacy policy not accepted', async () => {
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');

      // Accept terms but not privacy
      const termsCheckbox = screen.getByRole('checkbox', {
        name: /terms of service/i,
      });
      await userEvent.click(termsCheckbox);

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      const errorMessage = await screen.findByText(/you must accept the privacy policy/i);
      expect(errorMessage).toBeInTheDocument();

      expect(mockRegister).not.toHaveBeenCalled();
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      mockRegister.mockResolvedValue(undefined);
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const termsCheckbox = screen.getByRole('checkbox', {
        name: /terms of service/i,
      });
      const privacyCheckbox = screen.getByRole('checkbox', {
        name: /privacy policy/i,
      });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');
      await userEvent.click(termsCheckbox);
      await userEvent.click(privacyCheckbox);

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          email: 'test@example.com',
          username: 'testuser',
          password: 'Password123',
          acceptTerms: true,
          acceptPrivacy: true,
          newsletterOptIn: false,
        });
      });
    });

    it('submits with newsletter opt-in', async () => {
      mockRegister.mockResolvedValue(undefined);
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const termsCheckbox = screen.getByRole('checkbox', {
        name: /terms of service/i,
      });
      const privacyCheckbox = screen.getByRole('checkbox', {
        name: /privacy policy/i,
      });
      const newsletterCheckbox = screen.getByRole('checkbox', {
        name: /send me updates/i,
      });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');
      await userEvent.click(termsCheckbox);
      await userEvent.click(privacyCheckbox);
      await userEvent.click(newsletterCheckbox);

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          email: 'test@example.com',
          username: 'testuser',
          password: 'Password123',
          acceptTerms: true,
          acceptPrivacy: true,
          newsletterOptIn: true,
        });
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message on registration failure', async () => {
      mockRegister.mockRejectedValue(new Error('Username already exists'));
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const termsCheckbox = screen.getByRole('checkbox', {
        name: /terms of service/i,
      });
      const privacyCheckbox = screen.getByRole('checkbox', {
        name: /privacy policy/i,
      });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');
      await userEvent.click(termsCheckbox);
      await userEvent.click(privacyCheckbox);

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Username already exists')).toBeInTheDocument();
      });
    });

    it('displays generic error message for unknown errors', async () => {
      mockRegister.mockRejectedValue('Unknown error');
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const termsCheckbox = screen.getByRole('checkbox', {
        name: /terms of service/i,
      });
      const privacyCheckbox = screen.getByRole('checkbox', {
        name: /privacy policy/i,
      });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');
      await userEvent.click(termsCheckbox);
      await userEvent.click(privacyCheckbox);

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText('Registration failed. Please try again.')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('disables inputs during loading', () => {
      mockUseAuth.mockReturnValue({
        register: mockRegister,
        isLoading: true,
      });

      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      expect(emailInput).toBeDisabled();
      expect(usernameInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
      expect(confirmPasswordInput).toBeDisabled();
    });

    it('shows loading button text', () => {
      mockUseAuth.mockReturnValue({
        register: mockRegister,
        isLoading: true,
      });

      renderRegistrationPage();

      const submitButton = screen.getByRole('button', { name: /creating account/i });
      expect(submitButton).toBeDisabled();
      expect(screen.getByText('Creating Account...')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderRegistrationPage();

      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    it('has proper autocomplete attributes', () => {
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      expect(emailInput).toHaveAttribute('autocomplete', 'email');
      expect(usernameInput).toHaveAttribute('autocomplete', 'username');
      expect(passwordInput).toHaveAttribute('autocomplete', 'new-password');
      expect(confirmPasswordInput).toHaveAttribute('autocomplete', 'new-password');
    });

    it('error banner has alert role', async () => {
      mockRegister.mockRejectedValue(new Error('Test error'));
      renderRegistrationPage();

      const emailInput = screen.getByLabelText(/email address/i);
      const usernameInput = screen.getByLabelText(/^username/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const termsCheckbox = screen.getByRole('checkbox', {
        name: /terms of service/i,
      });
      const privacyCheckbox = screen.getByRole('checkbox', {
        name: /privacy policy/i,
      });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');
      await userEvent.type(confirmPasswordInput, 'Password123');
      await userEvent.click(termsCheckbox);
      await userEvent.click(privacyCheckbox);

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveTextContent('Test error');
      });
    });

    it('form has noValidate to use custom validation', () => {
      const { container } = renderRegistrationPage();

      const form = container.querySelector('form');
      expect(form).toHaveAttribute('novalidate');
    });
  });
});
