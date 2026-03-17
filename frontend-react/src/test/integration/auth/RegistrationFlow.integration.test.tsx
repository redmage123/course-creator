/**
 * Registration Flow Integration Tests
 *
 * BUSINESS CONTEXT:
 * Tests complete user registration workflow from form submission to dashboard redirect.
 * Validates proper integration between RegistrationPage component, authService, Redux state,
 * and navigation. Tests form validation, terms acceptance, and auto-login after registration.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests component + service + state management integration
 * - Mocks API calls but tests real service layer logic
 * - Tests Redux state propagation across registration flow
 * - Tests complex form validation rules
 * - Tests user interactions across multiple steps
 *
 * INTEGRATION SCOPE:
 * - RegistrationPage component + useAuth hook
 * - authService registration + Auto-login flow
 * - Form validation + Terms/Privacy acceptance
 * - Navigation + Authentication state
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, setupUserEvent } from '../../utils';
import { RegisterPage } from '@features/auth/Register';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';

// Mock useNavigate (framework mock, not service mock)
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Registration Flow Integration Tests', () => {
  const user = setupUserEvent();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    localStorage.clear();
    server.resetHandlers();
  });

  it('should complete successful registration and auto-login flow', async () => {
    /**
     * INTEGRATION TEST: Complete Registration + Auto-Login Workflow
     *
     * SIMULATES:
     * 1. User navigates to registration page
     * 2. User fills in all required fields
     * 3. User accepts terms and privacy policy
     * 4. User submits form
     * 5. API call creates account
     * 6. User is automatically logged in
     * 7. Redux state is updated with auth data
     * 8. User is redirected to student dashboard (default role)
     */

    // Default MSW handler will handle registration
    // No need to override unless testing error scenarios

    const { store } = renderWithProviders(<RegisterPage />);

    // Act - Step 1: Fill in username
    const usernameInput = screen.getByLabelText(/username/i);
    await user.type(usernameInput, 'newuser');

    // Act - Step 2: Fill in email
    const emailInput = screen.getByLabelText(/email address/i);
    await user.type(emailInput, 'newuser@example.com');

    // Act - Step 3: Fill in password
    const passwordInput = screen.getAllByLabelText(/password/i)[0];
    await user.type(passwordInput, 'SecurePass123!');

    // Act - Step 4: Confirm password
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    await user.type(confirmPasswordInput, 'SecurePass123!');

    // Act - Step 5: Accept terms
    const termsCheckbox = screen.getByLabelText(/terms of service/i);
    await user.click(termsCheckbox);

    // Act - Step 6: Accept privacy policy
    const privacyCheckbox = screen.getByLabelText(/privacy policy/i);
    await user.click(privacyCheckbox);

    // Act - Step 7: Submit form
    const submitButton = screen.getByRole('button', { name: /create account/i });
    await user.click(submitButton);

    // Assert - Verify Redux state was updated (auto-login outcome)
    await waitFor(() => {
      const authState = store.getState().auth;
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.token).toBe('mock-jwt-token');
      expect(authState.role).toBe('student');
      expect(authState.userId).toBe('new-user-123');
    }, { timeout: 3000 });

    // Assert - Verify localStorage was updated (user info only, tokens in-memory)
    expect(localStorage.getItem('userRole')).toBe('student');

    // Assert - Verify navigation to dashboard (outcome)
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/student');
    });
  });

  it('should validate password match before submission', async () => {
    /**
     * INTEGRATION TEST: Password Confirmation Validation
     *
     * SIMULATES:
     * 1. User enters password
     * 2. User enters different confirmation password
     * 3. Form validation catches mismatch
     * 4. Error is displayed
     * 5. API is not called
     */

    renderWithProviders(<RegisterPage />);

    // Act - Fill form with mismatched passwords
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getAllByLabelText(/password/i)[0], 'Password123!');
    await user.type(screen.getByLabelText(/confirm password/i), 'DifferentPassword123!');
    await user.click(screen.getByLabelText(/terms of service/i));
    await user.click(screen.getByLabelText(/privacy policy/i));
    await user.click(screen.getByRole('button', { name: /create account/i }));

    // Assert - Validation error is shown (outcome)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/passwords.*match/i);
    });

    // Assert - No navigation (validation prevented submission)
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should validate password strength requirements', async () => {
    /**
     * INTEGRATION TEST: Password Strength Validation
     *
     * BUSINESS REQUIREMENT:
     * Password must be at least 8 characters and contain uppercase, lowercase, number
     */

    renderWithProviders(<RegisterPage />);

    // Act - Enter weak password
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getAllByLabelText(/password/i)[0], 'weak');
    await user.type(screen.getByLabelText(/confirm password/i), 'weak');
    await user.click(screen.getByLabelText(/terms of service/i));
    await user.click(screen.getByLabelText(/privacy policy/i));
    await user.click(screen.getByRole('button', { name: /create account/i }));

    // Assert - Validation error is shown (outcome)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        /password.*8 characters|password.*strong/i
      );
    });

    // Assert - No navigation (validation prevented submission)
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should require terms and privacy acceptance', async () => {
    /**
     * INTEGRATION TEST: Legal Agreement Validation
     *
     * BUSINESS REQUIREMENT:
     * Users must explicitly accept terms of service and privacy policy
     */

    renderWithProviders(<RegisterPage />);

    // Act - Fill form without accepting terms
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getAllByLabelText(/password/i)[0], 'SecurePass123!');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123!');
    // Note: NOT checking terms/privacy checkboxes
    await user.click(screen.getByRole('button', { name: /create account/i }));

    // Assert - Validation error is shown (checkbox errors have role="alert")
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      const hasTermsOrPrivacyError = alerts.some(alert =>
        /terms|privacy/i.test(alert.textContent || '')
      );
      expect(hasTermsOrPrivacyError).toBe(true);
    });

    // Assert - No navigation (validation prevented submission)
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle duplicate username error', async () => {
    /**
     * INTEGRATION TEST: Duplicate Username Error Handling
     *
     * SIMULATES:
     * 1. User enters username that already exists
     * 2. API returns conflict error
     * 3. Error message is displayed
     * 4. User remains on registration page
     */

    // Override MSW to return registration error
    server.use(
      http.post('https://176.9.99.103:8000/auth/register', () => {
        return HttpResponse.json(
          { message: 'Registration failed. Username or email may already exist.' },
          { status: 409 }
        );
      })
    );

    const { store } = renderWithProviders(<RegisterPage />);

    // Act - Fill and submit form
    await user.type(screen.getByLabelText(/username/i), 'existinguser');
    await user.type(screen.getByLabelText(/email address/i), 'existing@example.com');
    await user.type(screen.getAllByLabelText(/password/i)[0], 'SecurePass123!');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123!');
    await user.click(screen.getByLabelText(/terms of service/i));
    await user.click(screen.getByLabelText(/privacy policy/i));
    await user.click(screen.getByRole('button', { name: /create account/i }));

    // Assert - Error message is displayed
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/already exist/i);
    });

    // Assert - User remains unauthenticated
    const authState = store.getState().auth;
    expect(authState.isAuthenticated).toBe(false);

    // Assert - No navigation occurred
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should validate email format', async () => {
    /**
     * INTEGRATION TEST: Email Format Validation
     */

    renderWithProviders(<RegisterPage />);

    // Act - Enter invalid email
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    await user.type(screen.getByLabelText(/email address/i), 'invalid-email');
    await user.type(screen.getAllByLabelText(/password/i)[0], 'SecurePass123!');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123!');
    await user.click(screen.getByLabelText(/terms of service/i));
    await user.click(screen.getByLabelText(/privacy policy/i));
    await user.click(screen.getByRole('button', { name: /create account/i }));

    // Assert - Validation error is shown
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/valid email/i);
    });

    // Assert - No navigation (validation prevented submission)
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should show loading state during registration', async () => {
    /**
     * INTEGRATION TEST: Loading State Management
     */

    // Override MSW with delayed response
    server.use(
      http.post('https://176.9.99.103:8000/auth/register', async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return HttpResponse.json({
          token: 'token',
          user: {
            id: '1',
            username: 'user',
            email: 'user@example.com',
            role: 'student',
          },
          expiresIn: 3600, // seconds
        });
      })
    );

    renderWithProviders(<RegisterPage />);

    // Act - Fill and submit form
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getAllByLabelText(/password/i)[0], 'SecurePass123!');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123!');
    await user.click(screen.getByLabelText(/terms of service/i));
    await user.click(screen.getByLabelText(/privacy policy/i));
    await user.click(screen.getByRole('button', { name: /create account/i }));

    // Assert - Loading state is shown
    expect(screen.getByText(/creating account/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /creating account/i })).toBeDisabled();

    // Wait for completion
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled();
    });
  });

  it('should optionally include newsletter opt-in', async () => {
    /**
     * INTEGRATION TEST: Newsletter Opt-In (Optional)
     *
     * BUSINESS REQUIREMENT:
     * Newsletter subscription is optional (not required like terms/privacy)
     */

    // Default MSW handler handles newsletter opt-in

    renderWithProviders(<RegisterPage />);

    // Act - Fill form with newsletter opt-in
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await user.type(screen.getAllByLabelText(/password/i)[0], 'SecurePass123!');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123!');
    await user.click(screen.getByLabelText(/terms of service/i));
    await user.click(screen.getByLabelText(/privacy policy/i));

    // Optional: Check newsletter if field exists
    const newsletterCheckbox = screen.queryByLabelText(/newsletter|updates/i);
    if (newsletterCheckbox) {
      await user.click(newsletterCheckbox);
    }

    await user.click(screen.getByRole('button', { name: /create account/i }));

    // Assert - Registration completes successfully (outcome)
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/student');
    }, { timeout: 3000 });
  });

  it('should navigate to login page via link', async () => {
    /**
     * INTEGRATION TEST: Navigation to Login Page
     */

    renderWithProviders(<RegisterPage />, {
      initialEntries: ['/register'],
    });

    // Act - Find login link
    const loginLink = screen.getByRole('link', { name: /sign in|login/i });
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  it('should validate required fields', async () => {
    /**
     * INTEGRATION TEST: Required Field Validation
     */

    renderWithProviders(<RegisterPage />);

    // Act - Submit without filling fields
    await user.click(screen.getByRole('button', { name: /create account/i }));

    // Assert - Validation errors are shown (multiple fields will have errors with role="alert")
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.length).toBeGreaterThan(0);
    });

    // Assert - No navigation (validation prevented submission)
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
