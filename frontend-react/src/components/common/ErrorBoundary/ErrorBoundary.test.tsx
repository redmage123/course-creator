/**
 * ErrorBoundary Tests — CC-2 monitoring wire-up
 *
 * BUSINESS CONTEXT:
 * Confirms that errors caught by ErrorBoundary are forwarded to the
 * monitoring service (captureException) so engineers are alerted to
 * runtime crashes in production.
 *
 * TECHNICAL IMPLEMENTATION:
 * Mocks the monitoring module to intercept captureException calls.
 * Renders a component that deliberately throws to trigger the boundary,
 * then asserts captureException was called with the thrown error.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

// Mock monitoring service — must be hoisted before imports resolve
const mockCaptureException = vi.fn();
vi.mock('../../../services/monitoring', () => ({
  captureException: (...args: unknown[]) => mockCaptureException(...args),
}));

// Helper: a child component that throws on demand
const ThrowingChild = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error from child');
  }
  return <div>Healthy child</div>;
};

describe('ErrorBoundary — monitoring integration (CC-2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Suppress React's console.error for intentional throws in tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('calls captureException when a child component throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow />
      </ErrorBoundary>
    );

    expect(mockCaptureException).toHaveBeenCalledOnce();
    const [caughtError] = mockCaptureException.mock.calls[0];
    expect(caughtError).toBeInstanceOf(Error);
    expect((caughtError as Error).message).toBe('Test error from child');
  });

  it('passes componentStack context to captureException', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow />
      </ErrorBoundary>
    );

    const [, context] = mockCaptureException.mock.calls[0];
    expect(context).toHaveProperty('componentStack');
  });

  it('does NOT call captureException when no error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(mockCaptureException).not.toHaveBeenCalled();
    expect(screen.getByText('Healthy child')).toBeInTheDocument();
  });

  it('shows fallback UI when an error is caught', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('calls custom onError prop in addition to monitoring', () => {
    const onError = vi.fn();
    render(
      <ErrorBoundary onError={onError}>
        <ThrowingChild shouldThrow />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalledOnce();
    expect(mockCaptureException).toHaveBeenCalledOnce();
  });

  it('calls captureException only once per error event', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow />
      </ErrorBoundary>
    );

    expect(mockCaptureException).toHaveBeenCalledOnce();
  });
});
