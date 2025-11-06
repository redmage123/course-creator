/**
 * Login Page Component
 *
 * BUSINESS CONTEXT:
 * Authenticates users and redirects to appropriate dashboard based on role.
 * Supports instructor, org admin, student, and site admin login.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses useAuth hook for authentication logic and Redux for state management.
 * Integrates with user-management service (port 8000) for authentication.
 */

import React, { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Card } from '../../components/atoms/Card';
import { Button } from '../../components/atoms/Button';
import { Heading } from '../../components/atoms/Heading';
import { Spinner } from '../../components/atoms/Spinner';
import styles from './Login.module.css';

/**
 * Login Page Component
 *
 * WHY THIS APPROACH:
 * - Form validation before submission
 * - Loading states for better UX
 * - Error handling with user feedback
 * - Remember me functionality
 * - Links to registration and password reset
 */
export const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');

  /**
   * Handle form submission
   *
   * BUSINESS LOGIC:
   * Validates inputs, calls login API, handles success/error states
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    try {
      // Note: Backend expects "username" but we're collecting email
      // The backend will accept either email or username
      await login({ username: email, password });
      // Navigation is handled by useAuth hook
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    }
  };

  return (
    <div className={styles['login-container']}>
      <Card variant="elevated" padding="large" className={styles['login-card']}>
        {/* Header */}
        <div className={styles['login-header']}>
          <Heading level="h1" gutterBottom>
            Welcome Back
          </Heading>
          <p className={styles['subtitle']}>
            Sign in to your Course Creator Platform account
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className={styles['login-form']}>
          {/* Error Message */}
          {error && (
            <div className={styles['error-message']} role="alert">
              {error}
            </div>
          )}

          {/* Email Input */}
          <div className={styles['form-group']}>
            <label htmlFor="email" className={styles['form-label']}>
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={styles['form-input']}
              placeholder="instructor@example.com"
              disabled={isLoading}
              autoComplete="email"
              required
            />
          </div>

          {/* Password Input */}
          <div className={styles['form-group']}>
            <label htmlFor="password" className={styles['form-label']}>
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={styles['form-input']}
              placeholder="Enter your password"
              disabled={isLoading}
              autoComplete="current-password"
              required
            />
          </div>

          {/* Remember Me & Forgot Password */}
          <div className={styles['form-options']}>
            <label className={styles['checkbox-label']}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={isLoading}
              />
              <span>Remember me</span>
            </label>

            <Link
              to="/forgot-password"
              className={styles['forgot-password-link']}
            >
              Forgot password?
            </Link>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            variant="primary"
            size="large"
            fullWidth
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Spinner size="small" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </Button>
        </form>

        {/* Divider */}
        <div className={styles['divider']}>
          <span>or</span>
        </div>

        {/* Register Link */}
        <div className={styles['register-section']}>
          <p className={styles['register-text']}>
            Don't have an account?{' '}
            <Link to="/register" className={styles['register-link']}>
              Sign up now
            </Link>
          </p>
        </div>

        {/* Demo Credentials */}
        <Card variant="outlined" padding="small" className={styles['demo-info']}>
          <Heading level="h5" gutterBottom>
            Demo Credentials
          </Heading>
          <div className={styles['demo-credentials']}>
            <div>
              <strong>Instructor:</strong> instructor@example.com / password123
            </div>
            <div>
              <strong>Org Admin:</strong> orgadmin@example.com / password123
            </div>
            <div>
              <strong>Student:</strong> student@example.com / password123
            </div>
          </div>
        </Card>
      </Card>
    </div>
  );
};
