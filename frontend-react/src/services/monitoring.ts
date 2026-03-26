/**
 * Monitoring Service
 *
 * BUSINESS CONTEXT:
 * Centralises error reporting so all uncaught application errors are
 * captured in Sentry for investigation. Wraps the Sentry SDK so the
 * rest of the app never imports Sentry directly — swapping providers
 * only requires changing this file.
 *
 * TECHNICAL IMPLEMENTATION:
 * Initialises Sentry on first import when VITE_SENTRY_DSN is set.
 * Exposes captureException used by ErrorBoundary (and any future callers).
 * When the DSN is not configured the functions are no-ops so local dev
 * and test environments work without Sentry credentials.
 */

import * as Sentry from '@sentry/react';

const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;

if (dsn) {
  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    // Capture 100% of transactions in dev/staging; tune down in production.
    tracesSampleRate: import.meta.env.PROD ? 0.2 : 1.0,
  });
}

/**
 * Report an exception to the monitoring backend (Sentry).
 * Safe to call in any environment — silently no-ops when Sentry is not
 * initialised (e.g., local dev without a DSN).
 *
 * @param error - The error to report
 * @param context - Optional additional context attached to the event
 */
export function captureException(
  error: unknown,
  context?: Record<string, unknown>
): void {
  if (!dsn) {
    return;
  }
  Sentry.captureException(error, context ? { extra: context } : undefined);
}
