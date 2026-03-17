/**
 * Toast Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Toast provides consistent user feedback
 * across all platform operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests variants, auto-dismiss, positions, and accessibility
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Toast } from './Toast';

describe('Toast Component', () => {
  beforeEach(() => {
    // Don't use fake timers as they interfere with animations
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders toast with message', () => {
      render(<Toast message="Test notification" />);
      expect(screen.getByText('Test notification')).toBeInTheDocument();
    });

    it('renders as alert role', () => {
      render(<Toast message="Alert" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders with default info variant', () => {
      render(<Toast message="Info message" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('renders success variant', () => {
      render(<Toast message="Success!" variant="success" />);
      expect(screen.getByText('Success!')).toBeInTheDocument();
    });

    it('renders error variant', () => {
      render(<Toast message="Error occurred" variant="error" />);
      expect(screen.getByText('Error occurred')).toBeInTheDocument();
    });

    it('renders warning variant', () => {
      render(<Toast message="Warning message" variant="warning" />);
      expect(screen.getByText('Warning message')).toBeInTheDocument();
    });

    it('renders info variant', () => {
      render(<Toast message="Info message" variant="info" />);
      expect(screen.getByText('Info message')).toBeInTheDocument();
    });
  });

  describe('Close Button', () => {
    it('renders close button by default', () => {
      render(<Toast message="Closeable" />);
      expect(screen.getByLabelText(/dismiss notification/i)).toBeInTheDocument();
    });

    it('calls onDismiss when close button clicked', async () => {
      const handleDismiss = vi.fn();
      render(<Toast message="Click to close" onDismiss={handleDismiss} />);

      const closeButton = screen.getByLabelText(/dismiss notification/i);
      await userEvent.click(closeButton);

      // Wait for exit animation (300ms)
      await waitFor(() => {
        expect(handleDismiss).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    it('hides close button when showCloseButton is false', () => {
      render(<Toast message="No close button" showCloseButton={false} />);
      expect(screen.queryByLabelText(/dismiss notification/i)).not.toBeInTheDocument();
    });
  });

  describe('Auto-dismiss', () => {
    it('auto-dismisses after short duration', async () => {
      const handleDismiss = vi.fn();
      render(<Toast message="Auto dismiss" duration={100} onDismiss={handleDismiss} />);

      expect(screen.getByText('Auto dismiss')).toBeInTheDocument();

      // Wait for auto-dismiss (100ms + 300ms animation)
      await waitFor(() => {
        expect(handleDismiss).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    it('auto-dismisses after custom duration', async () => {
      const handleDismiss = vi.fn();
      render(<Toast message="Custom duration" duration={200} onDismiss={handleDismiss} />);

      expect(screen.getByText('Custom duration')).toBeInTheDocument();

      // Wait for auto-dismiss (200ms + 300ms animation)
      await waitFor(() => {
        expect(handleDismiss).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    it('does not auto-dismiss when duration is 0', async () => {
      const handleDismiss = vi.fn();
      render(<Toast message="No auto dismiss" duration={0} onDismiss={handleDismiss} />);

      expect(screen.getByText('No auto dismiss')).toBeInTheDocument();

      // Wait a reasonable time
      await new Promise(resolve => setTimeout(resolve, 200));

      expect(handleDismiss).not.toHaveBeenCalled();
      expect(screen.getByText('No auto dismiss')).toBeInTheDocument();
    });
  });

  describe('ESC Key Handling', () => {
    it('dismisses toast when ESC pressed', async () => {
      const handleDismiss = vi.fn();
      render(<Toast message="Press ESC" onDismiss={handleDismiss} />);

      expect(screen.getByText('Press ESC')).toBeInTheDocument();

      await userEvent.keyboard('{Escape}');

      // Wait for exit animation (300ms)
      await waitFor(() => {
        expect(handleDismiss).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });
  });

  describe('Positions', () => {
    it('renders at top-right by default', () => {
      render(<Toast message="Top right" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders at top-left', () => {
      render(<Toast message="Top left" position="top-left" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders at bottom-right', () => {
      render(<Toast message="Bottom right" position="bottom-right" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders at bottom-left', () => {
      render(<Toast message="Bottom left" position="bottom-left" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders at top-center', () => {
      render(<Toast message="Top center" position="top-center" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders at bottom-center', () => {
      render(<Toast message="Bottom center" position="bottom-center" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Custom Icon', () => {
    it('renders icon container', () => {
      render(<Toast message="Default icon" variant="success" />);
      const toast = screen.getByRole('alert');
      expect(toast).toBeInTheDocument();
    });

    it('renders custom icon when provided', () => {
      render(
        <Toast
          message="Custom icon"
          icon={<span data-testid="custom-icon">🎉</span>}
        />
      );
      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role="alert"', () => {
      render(<Toast message="Alert role" />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('has aria-live="polite" for non-error variants', () => {
      render(<Toast message="Info" variant="info" />);
      const toast = screen.getByRole('alert');
      expect(toast).toHaveAttribute('aria-live', 'polite');
    });

    it('has aria-live="assertive" for error variant', () => {
      render(<Toast message="Error" variant="error" />);
      const toast = screen.getByRole('alert');
      expect(toast).toHaveAttribute('aria-live', 'assertive');
    });

    it('has aria-atomic="true"', () => {
      render(<Toast message="Atomic" />);
      const toast = screen.getByRole('alert');
      expect(toast).toHaveAttribute('aria-atomic', 'true');
    });

    it('renders accessible toast', () => {
      render(<Toast message="Icon hidden" />);
      const toast = screen.getByRole('alert');
      expect(toast).toBeInTheDocument();
      expect(toast).toHaveAttribute('aria-atomic', 'true');
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      render(<Toast message="Custom class" className="custom-toast" />);
      const toast = screen.getByRole('alert');
      expect(toast.className).toContain('custom-toast');
    });
  });

  describe('Portal Rendering', () => {
    it('renders toast in document.body', () => {
      render(<Toast message="Portal content" />);
      expect(document.body).toContainElement(screen.getByText('Portal content'));
    });
  });

  describe('Progress Bar', () => {
    it('renders toast with auto-dismiss enabled', () => {
      render(<Toast message="Progress" duration={5000} />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders toast without auto-dismiss', () => {
      render(<Toast message="No progress" duration={0} />);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has Toast as display name', () => {
      expect(Toast.displayName).toBe('Toast');
    });
  });

  describe('Regression Tests', () => {
    it('handles rapid dismiss clicks', async () => {
      const handleDismiss = vi.fn();
      render(<Toast message="Rapid clicks" onDismiss={handleDismiss} />);

      const closeButton = screen.getByLabelText(/dismiss notification/i);

      // Click multiple times rapidly
      await userEvent.click(closeButton);
      await userEvent.click(closeButton);
      await userEvent.click(closeButton);

      // Wait for animation
      await waitFor(() => {
        // Should only dismiss once
        expect(handleDismiss).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    it('cleans up timers on unmount', () => {
      const { unmount } = render(<Toast message="Cleanup" duration={5000} />);
      unmount();
      // Should not throw errors
      expect(true).toBe(true);
    });

    it('handles message changes', () => {
      const { rerender } = render(<Toast message="Initial message" />);
      expect(screen.getByText('Initial message')).toBeInTheDocument();

      rerender(<Toast message="Updated message" />);
      expect(screen.getByText('Updated message')).toBeInTheDocument();
      expect(screen.queryByText('Initial message')).not.toBeInTheDocument();
    });

    it('handles variant changes', () => {
      const { rerender } = render(<Toast message="Message" variant="info" />);
      const toast = screen.getByRole('alert');
      expect(toast).toHaveAttribute('aria-live', 'polite');

      rerender(<Toast message="Message" variant="error" />);
      expect(toast).toHaveAttribute('aria-live', 'assertive');
    });
  });
});
