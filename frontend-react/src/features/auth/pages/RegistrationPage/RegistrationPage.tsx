/**
 * Registration Page Component
 *
 * BUSINESS CONTEXT:
 * User registration entry point for the Course Creator Platform.
 * Collects user information and ensures consent to terms and privacy policy.
 *
 * TECHNICAL IMPLEMENTATION:
 * Form validation with controlled inputs, auth service integration,
 * error handling, loading states, and legal compliance.
 *
 * DESIGN PRINCIPLES:
 * - Clean, centered layout with Tami design system
 * - Client-side validation before submission
 * - Clear error messages for failed registration
 * - Accessible form with proper labels and ARIA attributes
 * - GDPR/CCPA compliant with explicit consent checkboxes
 */

import React, { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { SEO } from '../../../../components/common/SEO';
import { Input } from '../../../../components/atoms/Input';
import { Button } from '../../../../components/atoms/Button';
import { Checkbox } from '../../../../components/atoms/Checkbox';
import { Heading } from '../../../../components/atoms/Heading';
import { Card } from '../../../../components/atoms/Card';
import { useAuth } from '../../../../hooks/useAuth';
import styles from './RegistrationPage.module.css';

interface RegistrationFormData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
  newsletterOptIn: boolean;
}

interface RegistrationFormErrors {
  email?: string;
  username?: string;
  password?: string;
  confirmPassword?: string;
  acceptTerms?: string;
  acceptPrivacy?: string;
  submit?: string;
}

/**
 * Registration Page Component
 *
 * WHY THIS APPROACH:
 * - Controlled form inputs for validation
 * - useAuth hook for authentication state management
 * - Client-side validation before API call
 * - Loading states to prevent double submission
 * - Role-based redirects after successful registration
 * - Clear error messages for user feedback
 * - GDPR/CCPA compliance with explicit consent
 *
 * @example
 * ```tsx
 * <Route path="/register" element={<RegistrationPage />} />
 * ```
 */
export const RegistrationPage: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuth();

  const [formData, setFormData] = useState<RegistrationFormData>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
    acceptPrivacy: false,
    newsletterOptIn: false,
  });

  const [errors, setErrors] = useState<RegistrationFormErrors>({});

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const newErrors: RegistrationFormErrors = {};

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Username validation
    if (!formData.username) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    } else if (formData.username.length > 30) {
      newErrors.username = 'Username must be at most 30 characters';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, hyphens, and underscores';
    }

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

    // Terms acceptance validation
    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'You must accept the Terms of Service';
    }

    // Privacy policy acceptance validation
    if (!formData.acceptPrivacy) {
      newErrors.acceptPrivacy = 'You must accept the Privacy Policy';
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

    try {
      // Attempt registration
      await register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        acceptTerms: formData.acceptTerms,
        acceptPrivacy: formData.acceptPrivacy,
        newsletterOptIn: formData.newsletterOptIn,
      });

      // Redirect will be handled by useAuth hook based on user role
      // Default is likely /dashboard for new users
    } catch (error) {
      // Handle registration error
      setErrors({
        submit:
          error instanceof Error
            ? error.message
            : 'Registration failed. Please try again.',
      });
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (field: keyof RegistrationFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value =
      field === 'acceptTerms' ||
      field === 'acceptPrivacy' ||
      field === 'newsletterOptIn'
        ? e.target.checked
        : e.target.value;

    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear field error on change
    if (errors[field as keyof RegistrationFormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  return (
    <>
      <SEO
        title="Register"
        description="Create your Course Creator Platform account. Join thousands of learners and instructors. GDPR and CCPA compliant registration with secure data handling."
        keywords="register, sign up, create account, join course creator, student registration, instructor registration"
      />
      <main className={styles['registration-page']}>
      <div className={styles['registration-container']}>
        <div className={styles['registration-header']}>
          <Heading level="h1" align="center" gutterBottom={false}>
            Create Account
          </Heading>
          <p className={styles['registration-subtitle']}>
            Join the Course Creator Platform
          </p>
        </div>

        <Card variant="elevated" padding="large">
          <form
            onSubmit={handleSubmit}
            className={styles['registration-form']}
            noValidate
          >
            {/* Submit Error Message */}
            {errors.submit && (
              <div className={styles['registration-error-banner']} role="alert">
                {errors.submit}
              </div>
            )}

            {/* Email Input */}
            <Input
              type="email"
              label="Email Address"
              placeholder="you@example.com"
              value={formData.email}
              onChange={handleChange('email')}
              error={errors.email}
              required
              autoComplete="email"
              autoFocus
              disabled={isLoading}
            />

            {/* Username Input */}
            <Input
              type="text"
              label="Username"
              placeholder="Choose a unique username"
              value={formData.username}
              onChange={handleChange('username')}
              error={errors.username}
              required
              autoComplete="username"
              disabled={isLoading}
            />

            {/* Password Input */}
            <Input
              type="password"
              label="Password"
              placeholder="Create a strong password"
              value={formData.password}
              onChange={handleChange('password')}
              error={errors.password}
              required
              autoComplete="new-password"
              disabled={isLoading}
            />

            {/* Confirm Password Input */}
            <Input
              type="password"
              label="Confirm Password"
              placeholder="Re-enter your password"
              value={formData.confirmPassword}
              onChange={handleChange('confirmPassword')}
              error={errors.confirmPassword}
              required
              autoComplete="new-password"
              disabled={isLoading}
            />

            {/* Terms and Privacy Section */}
            <div className={styles['registration-legal']}>
              <Checkbox
                label={
                  <span>
                    I accept the{' '}
                    <Link
                      to="/terms"
                      className={styles['registration-link']}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Terms of Service
                    </Link>
                  </span>
                }
                checked={formData.acceptTerms}
                onChange={handleChange('acceptTerms')}
                error={errors.acceptTerms}
                disabled={isLoading}
                required
              />

              <Checkbox
                label={
                  <span>
                    I accept the{' '}
                    <Link
                      to="/privacy"
                      className={styles['registration-link']}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Privacy Policy
                    </Link>
                  </span>
                }
                checked={formData.acceptPrivacy}
                onChange={handleChange('acceptPrivacy')}
                error={errors.acceptPrivacy}
                disabled={isLoading}
                required
              />

              <Checkbox
                label="Send me updates and educational content via email"
                checked={formData.newsletterOptIn}
                onChange={handleChange('newsletterOptIn')}
                disabled={isLoading}
              />
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              variant="primary"
              size="large"
              fullWidth
              loading={isLoading}
              disabled={isLoading}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </Button>

            {/* Login Link */}
            <div className={styles['registration-footer']}>
              <p className={styles['registration-footer-text']}>
                Already have an account?{' '}
                <Link to="/login" className={styles['registration-link']}>
                  Sign in
                </Link>
              </p>
            </div>
          </form>
        </Card>
      </div>
    </main>
    </>
  );
};
