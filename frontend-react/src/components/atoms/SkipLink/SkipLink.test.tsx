/**
 * SkipLink Component Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring SkipLink component provides proper
 * accessibility bypass functionality for keyboard and screen reader users.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests all states, interactions, and accessibility features
 *
 * COVERAGE REQUIREMENTS:
 * - Rendering and default props
 * - Focus behavior and visibility
 * - Keyboard interactions (Enter, Space)
 * - Click interactions
 * - Target element focus management
 * - Custom props and className
 * - Accessibility attributes
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SkipLink } from './SkipLink';

describe('SkipLink Component', () => {
  // Setup: Create target element before each test
  beforeEach(() => {
    // Create a target element for the skip link
    const mainContent = document.createElement('div');
    mainContent.id = 'main-content';
    mainContent.textContent = 'Main Content Area';
    document.body.appendChild(mainContent);
  });

  // Cleanup: Remove target element after each test
  afterEach(() => {
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
      document.body.removeChild(mainContent);
    }

    // Clean up any custom target elements
    const customTarget = document.getElementById('custom-target');
    if (customTarget) {
      document.body.removeChild(customTarget);
    }
  });

  describe('Rendering', () => {
    it('renders with default text', () => {
      render(<SkipLink />);
      expect(screen.getByText('Skip to main content')).toBeInTheDocument();
    });

    it('renders as an anchor element', () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');
      expect(link.tagName).toBe('A');
    });

    it('has correct href attribute', () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');
      expect(link).toHaveAttribute('href', '#main-content');
    });

    it('renders with custom children text', () => {
      render(<SkipLink>Jump to content</SkipLink>);
      expect(screen.getByText('Jump to content')).toBeInTheDocument();
    });

    it('renders with custom targetId', () => {
      render(<SkipLink targetId="custom-target" />);
      const link = screen.getByTestId('skip-link');
      expect(link).toHaveAttribute('href', '#custom-target');
    });

    it('applies custom className', () => {
      render(<SkipLink className="custom-class" />);
      const link = screen.getByTestId('skip-link');
      expect(link.className).toContain('custom-class');
    });
  });

  describe('Focus Behavior', () => {
    it('is focusable via keyboard', () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');
      link.focus();
      expect(document.activeElement).toBe(link);
    });

    it('can receive focus via Tab key', async () => {
      render(
        <>
          <SkipLink />
          <button>Other Button</button>
        </>
      );

      // Tab should focus the skip link first
      await userEvent.tab();
      expect(screen.getByTestId('skip-link')).toHaveFocus();
    });
  });

  describe('Click Interactions', () => {
    it('focuses target element on click', async () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');

      await userEvent.click(link);

      const target = document.getElementById('main-content');
      expect(target).toHaveFocus();
    });

    it('adds tabindex=-1 to target if not already focusable', async () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');
      const target = document.getElementById('main-content');

      // Ensure target doesn't have tabindex initially
      expect(target).not.toHaveAttribute('tabindex');

      await userEvent.click(link);

      expect(target).toHaveAttribute('tabindex', '-1');
    });

    it('preserves existing tabindex on target', async () => {
      const target = document.getElementById('main-content');
      target?.setAttribute('tabindex', '0');

      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');

      await userEvent.click(link);

      expect(target).toHaveAttribute('tabindex', '0');
    });

    it('handles missing target gracefully', async () => {
      // Remove the target element
      const target = document.getElementById('main-content');
      if (target) {
        document.body.removeChild(target);
      }

      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');

      // Should not throw error
      await expect(userEvent.click(link)).resolves.not.toThrow();
    });
  });

  describe('Keyboard Interactions', () => {
    it('activates on Enter key', async () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');

      link.focus();
      fireEvent.keyDown(link, { key: 'Enter' });

      const target = document.getElementById('main-content');
      expect(target).toHaveFocus();
    });

    it('activates on Space key', async () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');

      link.focus();
      fireEvent.keyDown(link, { key: ' ' });

      const target = document.getElementById('main-content');
      expect(target).toHaveFocus();
    });

    it('does not activate on other keys', async () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');

      link.focus();
      fireEvent.keyDown(link, { key: 'a' });

      // Link should still have focus, not target
      expect(link).toHaveFocus();
    });
  });

  describe('Custom Target', () => {
    it('focuses custom target element', async () => {
      // Create custom target
      const customTarget = document.createElement('div');
      customTarget.id = 'custom-target';
      customTarget.textContent = 'Custom Target';
      document.body.appendChild(customTarget);

      render(<SkipLink targetId="custom-target" />);
      const link = screen.getByTestId('skip-link');

      await userEvent.click(link);

      expect(customTarget).toHaveFocus();
    });
  });

  describe('Accessibility', () => {
    it('has accessible name from children', () => {
      render(<SkipLink>Skip navigation</SkipLink>);
      expect(screen.getByRole('link', { name: /skip navigation/i })).toBeInTheDocument();
    });

    it('has data-testid for testing', () => {
      render(<SkipLink />);
      expect(screen.getByTestId('skip-link')).toBeInTheDocument();
    });

    it('is a valid link element', () => {
      render(<SkipLink />);
      expect(screen.getByRole('link')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has SkipLink as display name', () => {
      expect(SkipLink.displayName).toBe('SkipLink');
    });
  });

  describe('Regression Tests', () => {
    it('handles rapid clicks without errors', async () => {
      render(<SkipLink />);
      const link = screen.getByTestId('skip-link');

      // Rapid clicks should not cause errors
      await userEvent.click(link);
      await userEvent.click(link);
      await userEvent.click(link);

      const target = document.getElementById('main-content');
      expect(target).toHaveFocus();
    });

    it('works with React strict mode double rendering', () => {
      const { unmount } = render(
        <SkipLink />
      );

      expect(screen.getByTestId('skip-link')).toBeInTheDocument();

      unmount();

      // Re-render
      render(<SkipLink />);
      expect(screen.getByTestId('skip-link')).toBeInTheDocument();
    });
  });
});
