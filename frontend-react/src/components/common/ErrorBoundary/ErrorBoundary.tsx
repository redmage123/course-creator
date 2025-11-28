/**
 * Error Boundary Component
 *
 * BUSINESS CONTEXT:
 * Provides a fallback UI when React component errors occur, preventing
 * complete application crashes and improving user experience.
 *
 * TECHNICAL IMPLEMENTATION:
 * React class component implementing error boundary lifecycle methods.
 * Catches JavaScript errors anywhere in the child component tree,
 * logs errors, and displays a fallback UI.
 *
 * WHY CLASS COMPONENT:
 * Error boundaries must be class components as React hooks don't yet
 * support error boundary functionality (componentDidCatch/getDerivedStateFromError).
 */

import { Component, ReactNode, ErrorInfo } from 'react';
import styles from './ErrorBoundary.module.css';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary Class Component
 *
 * LIFECYCLE METHODS:
 * - getDerivedStateFromError: Updates state to trigger fallback UI
 * - componentDidCatch: Logs error information for debugging
 *
 * STATE MANAGEMENT:
 * - hasError: Boolean flag to show/hide error UI
 * - error: The caught error object
 * - errorInfo: React component stack trace
 *
 * FEATURES:
 * - Custom fallback UI support
 * - Error logging callback
 * - "Try Again" button to reset error state
 * - Development mode error details
 * - Production mode user-friendly message
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * Update state when error is caught
   * This enables the next render to show the fallback UI
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Log error information after error is caught
   * Useful for error reporting services (e.g., Sentry)
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error);
      console.error('Component stack:', errorInfo.componentStack);
    }

    // Update state with error details
    this.setState({
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // TODO: Send error to logging service (e.g., Sentry, LogRocket)
    // Example: Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });
  }

  /**
   * Reset error boundary state
   * Allows user to retry after fixing the issue
   */
  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  /**
   * Reload the page
   * Last resort for unrecoverable errors
   */
  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Default error UI
      return (
        <div className={styles.errorBoundary}>
          <div className={styles.errorCard}>
            <div className={styles.errorIcon}>
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>

            <h1 className={styles.errorTitle}>Something went wrong</h1>

            <p className={styles.errorMessage}>
              We're sorry for the inconvenience. An unexpected error has occurred.
            </p>

            {/* Show error details in development mode */}
            {process.env.NODE_ENV === 'development' && error && (
              <details className={styles.errorDetails}>
                <summary className={styles.errorDetailsSummary}>
                  Technical Details (Development Only)
                </summary>
                <div className={styles.errorDetailsContent}>
                  <p className={styles.errorName}>
                    <strong>Error:</strong> {error.toString()}
                  </p>
                  {errorInfo && (
                    <pre className={styles.errorStack}>
                      {errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </details>
            )}

            <div className={styles.errorActions}>
              <button
                onClick={this.handleReset}
                className={`${styles.button} ${styles.buttonPrimary}`}
                type="button"
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className={`${styles.button} ${styles.buttonSecondary}`}
                type="button"
              >
                Reload Page
              </button>
            </div>

            <p className={styles.errorHelp}>
              If the problem persists, please contact support or try again later.
            </p>
          </div>
        </div>
      );
    }

    return children;
  }
}
