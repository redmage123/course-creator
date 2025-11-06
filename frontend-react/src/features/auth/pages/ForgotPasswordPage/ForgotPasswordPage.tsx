/**
 * Forgot Password Page Component
 *
 * BUSINESS CONTEXT:
 * Password reset request page for users who forgot their password.
 * Sends password reset link via email for secure account recovery.
 *
 * TECHNICAL IMPLEMENTATION:
 * Form validation with controlled input, auth service integration,
 * success confirmation, and clear user feedback.
 *
 * DESIGN PRINCIPLES:
 * - Clean, centered layout with Tami design system
 * - Email validation before submission
 * - Clear success/error messages
 * - Accessible form with proper labels and ARIA attributes
 */

import React, { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Input } from '../../../../components/atoms/Input';
import { Button } from '../../../../components/atoms/Button';
import { Heading } from '../../../../components/atoms/Heading';
import { Card } from '../../../../components/atoms/Card';
import { authService } from '../../../../services/authService';
import styles from './ForgotPasswordPage.module.css';

interface ForgotPasswordFormData {
  email: string;
}

interface ForgotPasswordFormErrors {
  email?: string;
  submit?: string;
}

/**
 * Forgot Password Page Component
 *
 * WHY THIS APPROACH:
 * - Controlled form input for validation
 * - Direct authService call (no auth state needed)
 * - Success state to show confirmation message
 * - Loading states to prevent double submission
 * - Clear error messages for user feedback
 *
 * @example
 * ```tsx
 * <Route path="/forgot-password" element={<ForgotPasswordPage />} />
 * ```
 */
export const ForgotPasswordPage: React.FC = () => {
  const [formData, setFormData] = useState<ForgotPasswordFormData>({
    email: '',
  });

  const [errors, setErrors] = useState<ForgotPasswordFormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const newErrors: ForgotPasswordFormErrors = {};

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Clear previous submit errors
    setErrors((prev) => ({ ...prev, submit: undefined }));

    // Validate form
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Request password reset
      await authService.requestPasswordReset({ email: formData.email });

      // Show success message
      setIsSuccess(true);
    } catch (error) {
      // Handle error
      setErrors({
        submit:
          error instanceof Error
            ? error.message
            : 'Failed to send reset email. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ email: e.target.value });

    // Clear email error on change
    if (errors.email) {
      setErrors((prev) => ({
        ...prev,
        email: undefined,
      }));
    }
  };

  return (
    <div className={styles['forgot-password-page']}>
      <div className={styles['forgot-password-container']}>
        <div className={styles['forgot-password-header']}>
          <Heading level="h1" align="center" gutterBottom={false}>
            Forgot Password?
          </Heading>
          <p className={styles['forgot-password-subtitle']}>
            Enter your email address and we'll send you a link to reset your password
          </p>
        </div>

        <Card variant="elevated" padding="large">
          {isSuccess ? (
            // Success confirmation
            <div className={styles['forgot-password-success']}>
              <div className={styles['success-icon']} aria-hidden="true">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="#dcfce7" />
                  <path
                    d="M20 32L28 40L44 24"
                    stroke="#16a34a"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>

              <Heading level="h2" align="center" gutterBottom={true}>
                Check Your Email
              </Heading>

              <p className={styles['success-message']}>
                We've sent a password reset link to <strong>{formData.email}</strong>.
                Please check your inbox and follow the instructions to reset your password.
              </p>

              <p className={styles['success-note']}>
                Didn't receive the email? Check your spam folder or{' '}
                <button
                  type="button"
                  onClick={() => setIsSuccess(false)}
                  className={styles['retry-link']}
                >
                  try again
                </button>
                .
              </p>

              <Link to="/login" className={styles['back-to-login']}>
                <Button variant="secondary" size="large" fullWidth>
                  Back to Login
                </Button>
              </Link>
            </div>
          ) : (
            // Request form
            <form
              onSubmit={handleSubmit}
              className={styles['forgot-password-form']}
              noValidate
            >
              {/* Submit Error Message */}
              {errors.submit && (
                <div className={styles['forgot-password-error-banner']} role="alert">
                  {errors.submit}
                </div>
              )}

              {/* Email Input */}
              <Input
                type="email"
                label="Email Address"
                placeholder="you@example.com"
                value={formData.email}
                onChange={handleChange}
                error={errors.email}
                required
                autoComplete="email"
                autoFocus
                disabled={isLoading}
              />

              {/* Submit Button */}
              <Button
                type="submit"
                variant="primary"
                size="large"
                fullWidth
                loading={isLoading}
                disabled={isLoading}
              >
                {isLoading ? 'Sending...' : 'Send Reset Link'}
              </Button>

              {/* Back to Login Link */}
              <div className={styles['forgot-password-footer']}>
                <Link to="/login" className={styles['forgot-password-link']}>
                  ← Back to Login
                </Link>
              </div>
            </form>
          )}
        </Card>
      </div>
    </div>
  );
};
