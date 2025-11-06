/**
 * Reset Password Page Component
 *
 * BUSINESS CONTEXT:
 * Password reset confirmation page where users set a new password.
 * Uses token from email link to securely verify the reset request.
 *
 * TECHNICAL IMPLEMENTATION:
 * Form validation with controlled inputs, token extraction from URL,
 * password strength validation, and success confirmation.
 *
 * DESIGN PRINCIPLES:
 * - Clean, centered layout with Tami design system
 * - Strong password validation (8+ chars, mixed case, numbers)
 * - Clear success/error messages
 * - Accessible form with proper labels and ARIA attributes
 */

import React, { useState, FormEvent, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Input } from '../../../../components/atoms/Input';
import { Button } from '../../../../components/atoms/Button';
import { Heading } from '../../../../components/atoms/Heading';
import { Card } from '../../../../components/atoms/Card';
import { authService } from '../../../../services/authService';
import styles from './ResetPasswordPage.module.css';

interface ResetPasswordFormData {
  password: string;
  confirmPassword: string;
}

interface ResetPasswordFormErrors {
  password?: string;
  confirmPassword?: string;
  submit?: string;
}

/**
 * Reset Password Page Component
 *
 * WHY THIS APPROACH:
 * - Extracts token from URL query params
 * - Controlled form inputs for validation
 * - Direct authService call (no auth state needed)
 * - Success state to show confirmation message
 * - Loading states to prevent double submission
 * - Clear error messages for user feedback
 *
 * @example
 * ```tsx
 * <Route path="/reset-password" element={<ResetPasswordPage />} />
 * ```
 */
export const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [formData, setFormData] = useState<ResetPasswordFormData>({
    password: '',
    confirmPassword: '',
  });

  const [errors, setErrors] = useState<ResetPasswordFormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Validate token exists
  useEffect(() => {
    if (!token) {
      setErrors({
        submit: 'Invalid or missing reset token. Please request a new password reset.',
      });
    }
  }, [token]);

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const newErrors: ResetPasswordFormErrors = {};

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one lowercase letter';
    } else if (!/(?=.*[A-Z])/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one uppercase letter';
    } else if (!/(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one number';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Check token exists
    if (!token) {
      setErrors({
        submit: 'Invalid or missing reset token. Please request a new password reset.',
      });
      return;
    }

    // Clear previous submit errors
    setErrors((prev) => ({ ...prev, submit: undefined }));

    // Validate form
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Confirm password reset
      await authService.confirmPasswordReset({
        token,
        newPassword: formData.password,
      });

      // Show success message
      setIsSuccess(true);

      // Redirect to login immediately after success
      // User will see success message briefly before redirect
      navigate('/login');
    } catch (error) {
      // Handle error
      setErrors({
        submit:
          error instanceof Error
            ? error.message
            : 'Failed to reset password. The token may be expired.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (field: keyof ResetPasswordFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));

    // Clear field error on change
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  return (
    <div className={styles['reset-password-page']}>
      <div className={styles['reset-password-container']}>
        <div className={styles['reset-password-header']}>
          <Heading level="h1" align="center" gutterBottom={false}>
            Reset Password
          </Heading>
          <p className={styles['reset-password-subtitle']}>
            Enter your new password below
          </p>
        </div>

        <Card variant="elevated" padding="large">
          {isSuccess ? (
            // Success confirmation
            <div className={styles['reset-password-success']}>
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
                Password Reset Successful
              </Heading>

              <p className={styles['success-message']}>
                Your password has been successfully reset. You can now sign in with your new
                password.
              </p>

              <p className={styles['success-note']}>
                Redirecting to login page in 3 seconds...
              </p>

              <Link to="/login" className={styles['go-to-login']}>
                <Button variant="primary" size="large" fullWidth>
                  Go to Login
                </Button>
              </Link>
            </div>
          ) : (
            // Reset form
            <form
              onSubmit={handleSubmit}
              className={styles['reset-password-form']}
              noValidate
            >
              {/* Submit Error Message */}
              {errors.submit && (
                <div className={styles['reset-password-error-banner']} role="alert">
                  {errors.submit}
                  <div style={{ marginTop: '12px' }}>
                    <Link to="/forgot-password" className={styles['reset-password-link']}>
                      Request a new password reset
                    </Link>
                  </div>
                </div>
              )}

              {/* Password Input */}
              <Input
                type="password"
                label="New Password"
                placeholder="Enter your new password"
                value={formData.password}
                onChange={handleChange('password')}
                error={errors.password}
                required
                autoComplete="new-password"
                autoFocus
                disabled={isLoading || !token}
              />

              {/* Confirm Password Input */}
              <Input
                type="password"
                label="Confirm Password"
                placeholder="Re-enter your new password"
                value={formData.confirmPassword}
                onChange={handleChange('confirmPassword')}
                error={errors.confirmPassword}
                required
                autoComplete="new-password"
                disabled={isLoading || !token}
              />

              {/* Password Requirements */}
              <div className={styles['password-requirements']}>
                <p className={styles['requirements-title']}>Password must contain:</p>
                <ul className={styles['requirements-list']}>
                  <li>At least 8 characters</li>
                  <li>One uppercase letter</li>
                  <li>One lowercase letter</li>
                  <li>One number</li>
                </ul>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                variant="primary"
                size="large"
                fullWidth
                loading={isLoading}
                disabled={isLoading || !token}
              >
                {isLoading ? 'Resetting Password...' : 'Reset Password'}
              </Button>

              {/* Back to Login Link */}
              <div className={styles['reset-password-footer']}>
                <Link to="/login" className={styles['reset-password-link']}>
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
