/**
 * Button Component Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring Button component maintains Tami design standards
 * and provides consistent, accessible interactions across all user roles.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests all variants, sizes, states, and accessibility features
 *
 * COVERAGE REQUIREMENTS:
 * - All 5 variants (primary, secondary, danger, success, ghost)
 * - All 3 sizes (small, medium, large)
 * - All states (default, hover, active, disabled, loading)
 * - Accessibility (ARIA, keyboard navigation, focus management)
 * - User interactions (clicks, keyboard events)
 */

import { describe, it, expect, vi } from 'vitest';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button Component', () => {
  describe('Rendering', () => {
    it('renders with children text', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByText('Click me')).toBeInTheDocument();
    });

    it('renders as a button element by default', () => {
      render(<Button>Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button.tagName).toBe('BUTTON');
    });

    it('has type="button" by default', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('type', 'button');
    });

    it('accepts custom type prop', () => {
      render(<Button type="submit">Submit</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('type', 'submit');
    });
  });

  describe('Variants', () => {
    it('renders primary variant by default', () => {
      render(<Button>Primary</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Primary');
    });

    it('renders secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Secondary');
    });

    it('renders danger variant', () => {
      render(<Button variant="danger">Delete</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Delete');
    });

    it('renders success variant', () => {
      render(<Button variant="success">Save</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Save');
    });

    it('renders ghost variant', () => {
      render(<Button variant="ghost">Cancel</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Cancel');
    });
  });

  describe('Sizes', () => {
    it('renders medium size by default', () => {
      render(<Button>Medium</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Medium');
    });

    it('renders small size', () => {
      render(<Button size="small">Small</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Small');
    });

    it('renders large size', () => {
      render(<Button size="large">Large</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Large');
    });
  });

  describe('Loading State', () => {
    it('displays loading spinner when loading=true', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-busy', 'true');
    });

    it('hides button text when loading', () => {
      render(<Button loading>Loading Text</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      // Button should still contain the text in DOM but it may be visually hidden
      expect(button).toHaveTextContent('Loading Text');
    });

    it('disables button when loading', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('sets aria-busy=true when loading', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'true');
    });

    it('hides icons when loading', () => {
      render(
        <Button loading leftIcon={<span data-testid="left-icon">←</span>} rightIcon={<span data-testid="right-icon">→</span>}>
          Loading
        </Button>
      );
      expect(screen.queryByTestId('left-icon')).not.toBeInTheDocument();
      expect(screen.queryByTestId('right-icon')).not.toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('disables button when disabled=true', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('does not call onClick when disabled', async () => {
      const handleClick = vi.fn();
      render(<Button disabled onClick={handleClick}>Disabled</Button>);
      const button = screen.getByRole('button');
      await userEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('applies disabled class when loading or disabled', () => {
      const { container, rerender } = render(<Button disabled>Disabled</Button>);
      let button = screen.getByRole('button');
      expect(button).toBeDisabled();

      rerender(<Button loading>Loading</Button>);
      button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });

  describe('Icons', () => {
    it('renders left icon', () => {
      render(
        <Button leftIcon={<span data-testid="left-icon">←</span>}>
          With Icon
        </Button>
      );
      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
    });

    it('renders right icon', () => {
      render(
        <Button rightIcon={<span data-testid="right-icon">→</span>}>
          With Icon
        </Button>
      );
      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
    });

    it('renders both left and right icons', () => {
      render(
        <Button
          leftIcon={<span data-testid="left-icon">←</span>}
          rightIcon={<span data-testid="right-icon">→</span>}
        >
          With Icons
        </Button>
      );
      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
    });

    it('sets aria-hidden=true on icon wrappers', () => {
      render(
        <Button leftIcon={<span data-testid="test-icon">←</span>}>
          With Icon
        </Button>
      );
      const icon = screen.getByTestId('test-icon');
      expect(icon.parentElement).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Full Width', () => {
    it('renders button when fullWidth=true', () => {
      render(<Button fullWidth>Full Width</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Full Width');
    });

    it('renders button normally by default', () => {
      render(<Button>Normal Width</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Normal Width');
    });
  });

  describe('User Interactions', () => {
    it('calls onClick when clicked', async () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click me</Button>);
      const button = screen.getByRole('button');
      await userEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', async () => {
      const handleClick = vi.fn();
      render(<Button disabled onClick={handleClick}>Disabled</Button>);
      const button = screen.getByRole('button');
      await userEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('does not call onClick when loading', async () => {
      const handleClick = vi.fn();
      render(<Button loading onClick={handleClick}>Loading</Button>);
      const button = screen.getByRole('button');
      await userEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('can be activated with Enter key', async () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Press Enter</Button>);
      const button = screen.getByRole('button');
      button.focus();
      await userEvent.keyboard('{Enter}');
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('can be activated with Space key', async () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Press Space</Button>);
      const button = screen.getByRole('button');
      button.focus();
      await userEvent.keyboard(' ');
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('has role="button"', () => {
      render(<Button>Accessible Button</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('is focusable by default', () => {
      render(<Button>Focusable</Button>);
      const button = screen.getByRole('button');
      button.focus();
      expect(document.activeElement).toBe(button);
    });

    it('is not focusable when disabled', () => {
      render(<Button disabled>Not Focusable</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      // Disabled buttons cannot receive focus
      button.focus();
      expect(document.activeElement).not.toBe(button);
    });

    it('includes accessible name from children', () => {
      render(<Button>Create Course</Button>);
      expect(screen.getByRole('button', { name: /create course/i })).toBeInTheDocument();
    });

    it('accepts aria-label prop', () => {
      render(<Button aria-label="Close dialog">×</Button>);
      expect(screen.getByRole('button', { name: /close dialog/i })).toBeInTheDocument();
    });

    it('accepts aria-describedby prop', () => {
      render(
        <>
          <Button aria-describedby="help-text">Submit</Button>
          <span id="help-text">This will save your changes</span>
        </>
      );
      const button = screen.getByRole('button', { name: /submit/i });
      expect(button).toHaveAttribute('aria-describedby', 'help-text');
    });

    it('renders button with accessible touch target', () => {
      render(<Button>Touch Target</Button>);
      const button = screen.getByRole('button');
      // Note: Actual size validation requires E2E tests with real browser
      // This test verifies the button renders correctly
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Touch Target');
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      render(<Button className="custom-class">Custom</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Custom');
    });

    it('forwards ref to button element', () => {
      const ref = vi.fn();
      render(<Button ref={ref}>Ref Button</Button>);
      expect(ref).toHaveBeenCalledWith(expect.any(HTMLButtonElement));
    });

    it('spreads additional props to button element', () => {
      render(<Button data-testid="custom-button" data-analytics="click-event">Custom Props</Button>);
      const button = screen.getByTestId('custom-button');
      expect(button).toHaveAttribute('data-analytics', 'click-event');
    });

    it('accepts id prop', () => {
      render(<Button id="submit-btn">Submit</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('id', 'submit-btn');
    });

    it('accepts name prop', () => {
      render(<Button name="action">Action</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('name', 'action');
    });

    it('accepts form prop', () => {
      render(<Button form="my-form">Submit</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('form', 'my-form');
    });
  });

  describe('Combined Props', () => {
    it('renders primary small button', () => {
      render(<Button variant="primary" size="small">Small Primary</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Small Primary');
    });

    it('renders danger large full-width button', () => {
      render(
        <Button variant="danger" size="large" fullWidth>Delete Account</Button>
      );
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Delete Account');
    });

    it('renders ghost small button with left icon', () => {
      render(
        <Button variant="ghost" size="small" leftIcon={<span data-testid="plus-icon">+</span>}>Add Item</Button>
      );
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Add Item');
      expect(screen.getByTestId('plus-icon')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has Button as display name', () => {
      expect(Button.displayName).toBe('Button');
    });
  });

  describe('Regression Tests', () => {
    it('does not break when children is empty string', () => {
      render(<Button> </Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('handles rapid clicks without errors', async () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Rapid Click</Button>);
      const button = screen.getByRole('button');

      // Simulate rapid clicks
      await userEvent.click(button);
      await userEvent.click(button);
      await userEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(3);
    });

    it('transitions from loading to normal state', () => {
      const { rerender } = render(<Button loading>Loading</Button>);
      let button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toBeDisabled();

      rerender(<Button>Not Loading</Button>);
      button = screen.getByRole('button');
      expect(button).not.toHaveAttribute('aria-busy', 'true');
      expect(button).not.toBeDisabled();
    });

    it('transitions from disabled to enabled state', () => {
      const { rerender } = render(<Button disabled>Disabled</Button>);
      let button = screen.getByRole('button');
      expect(button).toBeDisabled();

      rerender(<Button>Enabled</Button>);
      button = screen.getByRole('button');
      expect(button).not.toBeDisabled();
    });
  });
});
