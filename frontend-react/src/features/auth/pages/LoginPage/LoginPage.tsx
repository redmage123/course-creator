/**
 * Login Page Component
 *
 * BUSINESS CONTEXT:
 * Primary authentication entry point for the Course Creator Platform.
 * Supports login for Site Admin, Org Admin, Instructor, and Student roles.
 *
 * TECHNICAL IMPLEMENTATION:
 * Form validation via react-hook-form + zod, matching the pattern used
 * across all other auth forms (RegistrationPage, etc.).
 *
 * DESIGN PRINCIPLES:
 * - Clean, centered layout with Tami design system
 * - Schema-driven validation (zod) — single source of truth for rules
 * - Clear error messages for failed login attempts
 * - Accessible form with proper labels and ARIA attributes
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { SEO } from '../../../../components/common/SEO';
import { Input } from '../../../../components/atoms/Input';
import { Button } from '../../../../components/atoms/Button';
import { Checkbox } from '../../../../components/atoms/Checkbox';
import { Heading } from '../../../../components/atoms/Heading';
import { Card } from '../../../../components/atoms/Card';
import { useAuth } from '../../../../hooks/useAuth';
import styles from './LoginPage.module.css';

/**
 * Zod schema — single source of truth for login validation rules.
 * Accepts either an email address or a username/userid (min 3 chars).
 */
const loginSchema = z.object({
  identifier: z
    .string()
    .min(1, 'Email or username is required')
    .min(3, 'Please enter a valid email or username'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters'),
  rememberMe: z.boolean(),
});

type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Login Page Component
 *
 * WHY THIS APPROACH:
 * - react-hook-form reduces re-renders vs controlled state
 * - zod schema is the single source of validation truth
 * - Matches RegistrationPage and all other auth form patterns
 * - Role-based redirects after successful login handled by useAuth
 *
 * @example
 * ```tsx
 * <Route path="/login" element={<LoginPage />} />
 * ```
 */
export const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    watch,
    setValue,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      identifier: '',
      password: '',
      rememberMe: false,
    },
  });

  const rememberMe = watch('rememberMe');

  /**
   * Handle validated form submission
   */
  const onSubmit = async (data: LoginFormData) => {
    try {
      // Store remember me preference
      if (data.rememberMe) {
        localStorage.setItem('rememberMe', 'true');
      } else {
        localStorage.removeItem('rememberMe');
      }

      // Attempt login (identifier can be email or username)
      await login({
        username: data.identifier,
        password: data.password,
      });

      // Redirect will be handled by useAuth hook based on user role
      // Site Admin -> /admin/dashboard
      // Org Admin -> /org-admin/dashboard
      // Instructor -> /instructor/dashboard
      // Student -> /student/dashboard
    } catch (error) {
      setError('root', {
        message:
          error instanceof Error
            ? error.message
            : 'Login failed. Please check your credentials and try again.',
      });
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
          <form onSubmit={handleSubmit(onSubmit)} className={styles['login-form']} noValidate>
            {/* Root / submit error message */}
            {errors.root && (
              <div className={styles['login-error-banner']} role="alert">
                {errors.root.message}
              </div>
            )}

            {/* Email or Username Input */}
            <Input
              type="text"
              label="Email or Username"
              placeholder="you@example.com or username"
              error={errors.identifier?.message}
              required
              autoComplete="username"
              autoFocus
              disabled={isLoading}
              {...register('identifier')}
            />

            {/* Password Input */}
            <Input
              type="password"
              label="Password"
              placeholder="Enter your password"
              error={errors.password?.message}
              required
              autoComplete="current-password"
              showPasswordToggle
              disabled={isLoading}
              {...register('password')}
            />

            {/* Remember Me & Forgot Password Row */}
            <div className={styles['login-options']}>
              <Checkbox
                label="Remember me"
                checked={rememberMe}
                onChange={(e) => setValue('rememberMe', e.target.checked)}
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
