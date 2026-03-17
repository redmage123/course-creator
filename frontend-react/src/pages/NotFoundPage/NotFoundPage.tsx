/**
 * 404 Not Found Page Component
 *
 * BUSINESS CONTEXT:
 * Displays a user-friendly error message when a requested page doesn't exist.
 * Provides navigation options to help users return to valid pages.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses consistent gradient background
 * - Provides clear messaging
 * - Offers navigation back to home or login
 * - Accessible error page design
 */

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card } from '../../components/atoms/Card';
import { Button } from '../../components/atoms/Button';
import { Heading } from '../../components/atoms/Heading';
import { useAuth } from '../../hooks/useAuth';
import styles from './NotFoundPage.module.css';

/**
 * NotFoundPage Component
 *
 * WHY THIS APPROACH:
 * - Consistent visual design with auth pages
 * - Context-aware navigation (authenticated vs. unauthenticated)
 * - Clear, friendly error messaging
 * - Encourages users to return to valid pages
 */
export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleGoHome = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/');
    }
  };

  return (
    <div className={styles['not-found-page']}>
      <Card variant="elevated" padding="large" className={styles['not-found-card']}>
        <div className={styles['error-code']}>404</div>

        <Heading level="h1" align="center" gutterBottom>
          Page Not Found
        </Heading>

        <p className={styles['error-message']}>
          Oops! The page you're looking for doesn't exist or has been moved.
        </p>

        <div className={styles['action-buttons']}>
          <Button
            variant="primary"
            size="large"
            onClick={handleGoHome}
            fullWidth
          >
            {isAuthenticated ? 'Go to Dashboard' : 'Go to Homepage'}
          </Button>

          <Button
            variant="secondary"
            size="large"
            onClick={handleGoBack}
            fullWidth
          >
            Go Back
          </Button>
        </div>

        {!isAuthenticated && (
          <div className={styles['auth-links']}>
            <p className={styles['auth-text']}>Need an account?</p>
            <div className={styles['auth-buttons']}>
              <Link to="/login" className={styles['auth-link']}>
                Log In
              </Link>
              <span className={styles['auth-separator']}>•</span>
              <Link to="/register" className={styles['auth-link']}>
                Sign Up
              </Link>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
