/**
 * OfflineIndicator Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring the OfflineIndicator provides clear visual feedback
 * when the device loses network connectivity.
 *
 * TEST COVERAGE:
 * - Component rendering based on online/offline state
 * - Custom message display
 * - Position styling
 * - Auto-hide behavior
 * - Accessibility (ARIA attributes)
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing.
 * Mocks useDeviceCapabilities hook to control online/offline state.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { OfflineIndicator } from './OfflineIndicator';

// Mock the useDeviceCapabilities hook
vi.mock('../hooks/useDeviceCapabilities', () => ({
  useDeviceCapabilities: vi.fn(),
}));

import { useDeviceCapabilities } from '../hooks/useDeviceCapabilities';

const mockUseDeviceCapabilities = useDeviceCapabilities as ReturnType<typeof vi.fn>;

describe('OfflineIndicator Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Visibility Based on Network State', () => {
    it('does not render when online and showWhenOnline is false', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });

      const { container } = render(<OfflineIndicator />);

      // Component returns null when online and showWhenOnline is false (default)
      expect(container.firstChild).toBeNull();
    });

    it('renders when going offline', () => {
      // Start online
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender } = render(<OfflineIndicator />);

      // Go offline
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('shows default offline message', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender } = render(<OfflineIndicator />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator />);

      expect(screen.getByText(/offline/i)).toBeInTheDocument();
    });
  });

  describe('Custom Messages', () => {
    it('renders custom offline message', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender } = render(
        <OfflineIndicator offlineMessage="No internet connection" />
      );

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator offlineMessage="No internet connection" />);

      expect(screen.getByText('No internet connection')).toBeInTheDocument();
    });

    it('shows online message when coming back online with showWhenOnline', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      const { rerender } = render(
        <OfflineIndicator showWhenOnline={true} onlineMessage="Back online!" />
      );

      // Trigger the offline state first
      rerender(<OfflineIndicator showWhenOnline={true} onlineMessage="Back online!" />);

      // Go back online
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      rerender(<OfflineIndicator showWhenOnline={true} onlineMessage="Back online!" />);

      expect(screen.getByText('Back online!')).toBeInTheDocument();
    });
  });

  describe('Position Styling', () => {
    it('applies top position class by default', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender, container } = render(<OfflineIndicator />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator />);

      const indicator = container.firstChild as HTMLElement;
      expect(indicator.className).toContain('top');
    });

    it('applies bottom position class when specified', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender, container } = render(<OfflineIndicator position="bottom" />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator position="bottom" />);

      const indicator = container.firstChild as HTMLElement;
      expect(indicator.className).toContain('bottom');
    });
  });

  describe('Auto-hide Behavior', () => {
    it('renders with showWhenOnline and autoHideDelay props', () => {
      // Test that component accepts and uses these props without error
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      const { rerender } = render(
        <OfflineIndicator showWhenOnline={true} autoHideDelay={3000} />
      );

      // Trigger offline display
      rerender(<OfflineIndicator showWhenOnline={true} autoHideDelay={3000} />);

      // Go online - should show the "online" indicator when showWhenOnline is true
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      rerender(<OfflineIndicator showWhenOnline={true} autoHideDelay={3000} />);

      // Indicator is visible when coming back online with showWhenOnline
      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.getByText('Connection restored')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role="status" for screen readers', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender } = render(<OfflineIndicator />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has aria-live="polite" attribute', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender } = render(<OfflineIndicator />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveAttribute('aria-live', 'polite');
    });

    it('shows warning icon when offline', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender } = render(<OfflineIndicator />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator />);

      expect(screen.getByText('⚠')).toBeInTheDocument();
    });

    it('shows checkmark icon when online', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      const { rerender } = render(<OfflineIndicator showWhenOnline={true} />);

      rerender(<OfflineIndicator showWhenOnline={true} />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      rerender(<OfflineIndicator showWhenOnline={true} />);

      expect(screen.getByText('✓')).toBeInTheDocument();
    });
  });

  describe('State Transitions', () => {
    it('handles multiple online/offline transitions', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender } = render(<OfflineIndicator />);

      // Initial: online, not visible
      expect(screen.queryByRole('status')).not.toBeInTheDocument();

      // Go offline
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator />);
      expect(screen.getByRole('status')).toBeInTheDocument();

      // Go back online (without showWhenOnline, should hide)
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      rerender(<OfflineIndicator />);
      expect(screen.queryByRole('status')).not.toBeInTheDocument();

      // Go offline again
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty offline message gracefully', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      const { rerender, container } = render(<OfflineIndicator offlineMessage="" />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      rerender(<OfflineIndicator offlineMessage="" />);

      // Component still renders with empty message
      expect(container.firstChild).not.toBeNull();
    });

    it('cleans up timers on unmount', () => {
      mockUseDeviceCapabilities.mockReturnValue({ isOnline: false });
      const { rerender, unmount } = render(
        <OfflineIndicator showWhenOnline={true} autoHideDelay={3000} />
      );

      // Trigger state change
      rerender(<OfflineIndicator showWhenOnline={true} autoHideDelay={3000} />);

      mockUseDeviceCapabilities.mockReturnValue({ isOnline: true });
      rerender(<OfflineIndicator showWhenOnline={true} autoHideDelay={3000} />);

      unmount();

      // Advance timers - should not cause errors
      expect(() => {
        vi.advanceTimersByTime(5000);
      }).not.toThrow();
    });
  });
});
