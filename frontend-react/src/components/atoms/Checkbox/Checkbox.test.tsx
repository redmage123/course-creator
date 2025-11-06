/**
 * Checkbox Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Checkbox provides accessible and functional
 * checkbox inputs across all platform forms.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests indeterminate state, validation, and accessibility
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Checkbox } from './Checkbox';

describe('Checkbox Component', () => {
  beforeEach(() => {
    // Setup
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders checkbox without label', () => {
      render(<Checkbox />);
      expect(screen.getByRole('checkbox')).toBeInTheDocument();
    });

    it('renders with label', () => {
      render(<Checkbox label="Accept terms" />);
      expect(screen.getByText('Accept terms')).toBeInTheDocument();
    });

    it('renders with helper text', () => {
      render(<Checkbox helperText="This is required" />);
      expect(screen.getByText('This is required')).toBeInTheDocument();
    });

    it('renders with error message', () => {
      render(<Checkbox error="You must accept the terms" />);
      expect(screen.getByText('You must accept the terms')).toBeInTheDocument();
    });

    it('label is clickable', async () => {
      render(<Checkbox label="Click me" />);
      const label = screen.getByText('Click me');
      const checkbox = screen.getByRole('checkbox');

      await userEvent.click(label);

      expect(checkbox).toBeChecked();
    });
  });

  describe('Controlled Mode', () => {
    it('displays checked state', () => {
      render(<Checkbox checked onChange={() => {}} />);
      expect(screen.getByRole('checkbox')).toBeChecked();
    });

    it('displays unchecked state', () => {
      render(<Checkbox checked={false} onChange={() => {}} />);
      expect(screen.getByRole('checkbox')).not.toBeChecked();
    });

    it('calls onChange when clicked', async () => {
      const handleChange = vi.fn();
      render(<Checkbox checked={false} onChange={handleChange} label="Click me" />);

      const label = screen.getByText('Click me');
      await userEvent.click(label);

      expect(handleChange).toHaveBeenCalledTimes(1);
    });

    it('updates state when prop changes', () => {
      const { rerender } = render(<Checkbox checked={false} onChange={() => {}} />);
      expect(screen.getByRole('checkbox')).not.toBeChecked();

      rerender(<Checkbox checked={true} onChange={() => {}} />);
      expect(screen.getByRole('checkbox')).toBeChecked();
    });
  });

  describe('Uncontrolled Mode', () => {
    it('uses defaultChecked', () => {
      render(<Checkbox defaultChecked />);
      expect(screen.getByRole('checkbox')).toBeChecked();
    });

    it('manages internal state', async () => {
      render(<Checkbox label="Toggle me" />);
      const checkbox = screen.getByRole('checkbox');
      const label = screen.getByText('Toggle me');

      expect(checkbox).not.toBeChecked();

      await userEvent.click(label);

      expect(checkbox).toBeChecked();
    });

    it('toggles on multiple clicks', async () => {
      render(<Checkbox label="Toggle me" />);
      const checkbox = screen.getByRole('checkbox');
      const label = screen.getByText('Toggle me');

      await userEvent.click(label);
      expect(checkbox).toBeChecked();

      await userEvent.click(label);
      expect(checkbox).not.toBeChecked();

      await userEvent.click(label);
      expect(checkbox).toBeChecked();
    });
  });

  describe('Indeterminate State', () => {
    it('sets indeterminate property', () => {
      render(<Checkbox indeterminate />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.indeterminate).toBe(true);
    });

    it('updates indeterminate when prop changes', () => {
      const { rerender } = render(<Checkbox indeterminate={false} />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.indeterminate).toBe(false);

      rerender(<Checkbox indeterminate={true} />);
      expect(checkbox.indeterminate).toBe(true);
    });

    it('can be both checked and indeterminate', () => {
      render(<Checkbox checked indeterminate onChange={() => {}} />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);
      expect(checkbox.indeterminate).toBe(true);
    });
  });

  describe('Size Variants', () => {
    it('renders small size', () => {
      render(<Checkbox size="small" label="Small" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
    });

    it('renders medium size by default', () => {
      render(<Checkbox label="Medium" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
    });

    it('renders large size', () => {
      render(<Checkbox size="large" label="Large" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('disables checkbox when disabled prop is true', () => {
      render(<Checkbox disabled />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeDisabled();
    });

    it('does not call onChange when disabled', async () => {
      const handleChange = vi.fn();
      render(<Checkbox disabled onChange={handleChange} label="Disabled" />);

      const label = screen.getByText('Disabled');
      await userEvent.click(label);

      expect(handleChange).not.toHaveBeenCalled();
    });

    it('cannot be checked when disabled', async () => {
      render(<Checkbox disabled label="Disabled" />);
      const checkbox = screen.getByRole('checkbox');
      const label = screen.getByText('Disabled');

      await userEvent.click(label);

      expect(checkbox).not.toBeChecked();
    });
  });

  describe('Error State', () => {
    it('shows error message', () => {
      render(<Checkbox error="This field is required" />);
      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });

    it('has aria-invalid when error', () => {
      render(<Checkbox error="Error message" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('aria-invalid', 'true');
    });

    it('error takes precedence over helper text', () => {
      render(<Checkbox error="Error" helperText="Helper" />);
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.queryByText('Helper')).not.toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('can be focused with Tab', () => {
      render(<Checkbox label="Focusable" />);
      const checkbox = screen.getByRole('checkbox');

      checkbox.focus();

      expect(checkbox).toHaveFocus();
    });

    it('can be toggled with Space key', async () => {
      render(<Checkbox label="Keyboard toggle" />);
      const checkbox = screen.getByRole('checkbox');

      checkbox.focus();
      await userEvent.keyboard(' ');

      expect(checkbox).toBeChecked();

      await userEvent.keyboard(' ');

      expect(checkbox).not.toBeChecked();
    });
  });

  describe('Accessibility', () => {
    it('has correct role', () => {
      render(<Checkbox />);
      expect(screen.getByRole('checkbox')).toBeInTheDocument();
    });

    it('has aria-invalid when error', () => {
      render(<Checkbox error="Error" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('aria-invalid', 'true');
    });

    it('has aria-describedby when helper text present', () => {
      render(<Checkbox helperText="Helper" id="test-checkbox" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('aria-describedby', 'test-checkbox-message');
    });

    it('has aria-describedby when error present', () => {
      render(<Checkbox error="Error" id="test-checkbox" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('aria-describedby', 'test-checkbox-message');
    });

    it('label is associated with checkbox', () => {
      render(<Checkbox label="Test" id="test-checkbox" />);
      const checkbox = screen.getByRole('checkbox');
      const labelElement = checkbox.parentElement?.querySelector('label');
      expect(labelElement).toHaveAttribute('for', 'test-checkbox');
      expect(checkbox).toHaveAttribute('id', 'test-checkbox');
    });

    it('generates unique id when not provided', () => {
      const { container } = render(<Checkbox label="Auto ID" />);
      const checkbox = container.querySelector('input[type="checkbox"]');
      expect(checkbox).toHaveAttribute('id');
      expect(checkbox?.getAttribute('id')).toMatch(/^checkbox-/);
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      render(<Checkbox className="custom-checkbox" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox.closest('.custom-checkbox')).toBeInTheDocument();
    });

    it('accepts custom id', () => {
      render(<Checkbox id="custom-id" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('id', 'custom-id');
    });

    it('passes through additional props', () => {
      render(<Checkbox name="agreement" data-testid="test-checkbox" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('name', 'agreement');
      expect(checkbox).toHaveAttribute('data-testid', 'test-checkbox');
    });

    it('supports required attribute', () => {
      render(<Checkbox required />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeRequired();
    });
  });

  describe('Display Name', () => {
    it('has Checkbox as display name', () => {
      expect(Checkbox.displayName).toBe('Checkbox');
    });
  });

  describe('Forward Ref', () => {
    it('forwards ref to input element', () => {
      const ref = vi.fn();
      render(<Checkbox ref={ref} />);
      expect(ref).toHaveBeenCalled();
    });

    it('ref can access input properties', () => {
      const ref = { current: null as HTMLInputElement | null };
      render(<Checkbox ref={ref} />);
      expect(ref.current).toBeInstanceOf(HTMLInputElement);
      expect(ref.current?.type).toBe('checkbox');
    });
  });

  describe('Regression Tests', () => {
    it('handles rapid clicks', async () => {
      render(<Checkbox label="Rapid" />);
      const checkbox = screen.getByRole('checkbox');
      const label = screen.getByText('Rapid');

      await userEvent.click(label);
      await userEvent.click(label);
      await userEvent.click(label);

      expect(checkbox).toBeChecked();
    });

    it('handles label click same as checkbox click', async () => {
      const handleChange = vi.fn();
      render(<Checkbox label="Click label" onChange={handleChange} />);

      const label = screen.getByText('Click label');
      await userEvent.click(label);

      expect(handleChange).toHaveBeenCalledTimes(1);
    });

    it('cleans up on unmount', () => {
      const { unmount } = render(<Checkbox />);
      unmount();
      expect(true).toBe(true); // Should not throw errors
    });

    it('handles indeterminate to checked transition', async () => {
      const { rerender } = render(<Checkbox indeterminate checked onChange={() => {}} />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.indeterminate).toBe(true);
      expect(checkbox.checked).toBe(true);

      rerender(<Checkbox indeterminate={false} checked onChange={() => {}} />);
      expect(checkbox.indeterminate).toBe(false);
      expect(checkbox.checked).toBe(true);
    });

    it('works without label', async () => {
      const { container } = render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox');
      const label = container.querySelector('label');

      await userEvent.click(label!);

      expect(checkbox).toBeChecked();
    });
  });
});
