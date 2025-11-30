/**
 * Login Page Component
 *
 * BUSINESS CONTEXT:
 * Primary authentication entry point for the Course Creator Platform.
 * Supports login for Site Admin, Org Admin, Instructor, and Student roles.
 *
 * TECHNICAL IMPLEMENTATION:
 * Form validation with controlled inputs, auth service integration,
 * error handling, and loading states.
 *
 * DESIGN PRINCIPLES:
 * - Clean, centered layout with Tami design system
 * - Client-side validation before submission
 * - Clear error messages for failed login attempts
 * - Accessible form with proper labels and ARIA attributes
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
import styles from './LoginPage.module.css';

interface LoginFormData {
  identifier: string;  // Can be email OR username/userid
  password: string;
  rememberMe: boolean;
}

interface LoginFormErrors {
  identifier?: string;
  password?: string;
  submit?: string;
}

/**
 * Login Page Component
 *
 * WHY THIS APPROACH:
 * - Controlled form inputs for validation
 * - useAuth hook for authentication state management
 * - Client-side validation before API call
 * - Loading states to prevent double submission
 * - Role-based redirects after successful login
 * - Clear error messages for user feedback
 *
 * @example
 * ```tsx
 * <Route path="/login" element={<LoginPage />} />
 * ```
 */
export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();

  const [formData, setFormData] = useState<LoginFormData>({
    identifier: '',
    password: '',
    rememberMe: false,
  });

  const [errors, setErrors] = useState<LoginFormErrors>({});

  /**
   * Validate form data
   * Accepts either email address OR username/userid
   */
  const validateForm = (): boolean => {
    const newErrors: LoginFormErrors = {};

    // Identifier validation (email or username)
    if (!formData.identifier) {
      newErrors.identifier = 'Email or username is required';
    } else if (formData.identifier.length < 3) {
      newErrors.identifier = 'Please enter a valid email or username';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
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
      // Store remember me preference
      if (formData.rememberMe) {
        localStorage.setItem('rememberMe', 'true');
      } else {
        localStorage.removeItem('rememberMe');
      }

      // Attempt login (identifier can be email or username)
      await login({
        username: formData.identifier,
        password: formData.password,
      });

      // Redirect will be handled by useAuth hook based on user role
      // Site Admin -> /admin/dashboard
      // Org Admin -> /org-admin/dashboard
      // Instructor -> /instructor/dashboard
      // Student -> /student/dashboard
    } catch (error) {
      // Handle login error
      setErrors({
        submit:
          error instanceof Error
            ? error.message
            : 'Login failed. Please check your credentials and try again.',
      });
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (field: keyof LoginFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = field === 'rememberMe' ? e.target.checked : e.target.value;

    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear field error on change
    if (errors[field as keyof LoginFormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  return (
    <>
      <SEO
        title="Login"
        description="Sign in to your Course Creator Platform account to access courses, labs, and analytics. Supports Site Admin, Org Admin, Instructor, and Student roles."
        keywords="login, sign in, authentication, course creator, student portal, instructor dashboard"
      />
      <main className={styles['login-page']}>
      <div className={styles['login-container']}>
        <div className={styles['login-header']}>
          <Heading level="h1" align="center" gutterBottom={false}>
            Welcome Back
          </Heading>
          <p className={styles['login-subtitle']}>
            Sign in to your Course Creator account
          </p>
        </div>

        <Card variant="elevated" padding="large">
          <form onSubmit={handleSubmit} className={styles['login-form']} noValidate>
            {/* Submit Error Message */}
            {errors.submit && (
              <div className={styles['login-error-banner']} role="alert">
                {errors.submit}
              </div>
            )}

            {/* Email or Username Input */}
            <Input
              type="text"
              label="Email or Username"
              placeholder="you@example.com or username"
              value={formData.identifier}
              onChange={handleChange('identifier')}
              error={errors.identifier}
              required
              autoComplete="username"
              autoFocus
              disabled={isLoading}
            />

            {/* Password Input */}
            <Input
              type="password"
              label="Password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange('password')}
              error={errors.password}
              required
              autoComplete="current-password"
              showPasswordToggle
              disabled={isLoading}
            />

            {/* Remember Me & Forgot Password Row */}
            <div className={styles['login-options']}>
              <Checkbox
                label="Remember me"
                checked={formData.rememberMe}
                onChange={handleChange('rememberMe')}
                disabled={isLoading}
              />

              <Link to="/forgot-password" className={styles['login-link']}>
                Forgot password?
              </Link>
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
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>

            {/* Registration Link */}
            <div className={styles['login-footer']}>
              <p className={styles['login-footer-text']}>
                Don't have an account?{' '}
                <Link to="/register" className={styles['login-link']}>
                  Create one now
                </Link>
              </p>
            </div>
          </form>
        </Card>

        {/* Demo Credentials (Development Only) */}
        {import.meta.env.DEV && (
          <Card variant="outlined" padding="medium" className={styles['demo-credentials']}>
            <Heading level="h2" gutterBottom={true}>
              Demo Credentials
            </Heading>
            <div className={styles['demo-list']}>
              <p>
                <strong>Site Admin:</strong> admin@courseplatform.com / admin123456
              </p>
              <p>
                <strong>Org Admin:</strong> orgadmin@example.com / orgadmin123
              </p>
              <p>
                <strong>Instructor:</strong> instructor@example.com / instructor123
              </p>
              <p>
                <strong>Student:</strong> student@example.com / student123
              </p>
            </div>
          </Card>
        )}
      </div>
    </main>
    </>
  );
};
