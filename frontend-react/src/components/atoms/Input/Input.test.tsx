/**
 * Input Component Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring Input component maintains Tami design standards
 * and provides consistent, accessible form inputs across all user roles.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests all variants, sizes, states, and accessibility features
 *
 * COVERAGE REQUIREMENTS:
 * - All 4 variants (default, success, error, warning)
 * - All 3 sizes (small, medium, large)
 * - All states (default, focus, hover, disabled)
 * - Accessibility (ARIA, labels, helper text, required fields)
 * - User interactions (typing, focus, blur)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from './Input';

describe('Input Component', () => {
  describe('Rendering', () => {
    it('renders input element', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('renders with placeholder text', () => {
      render(<Input placeholder="Enter your email" />);
      expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    });

    it('has type="text" by default', () => {
      render(<Input />);
      expect(screen.getByRole('textbox')).toHaveAttribute('type', 'text');
    });

    it('accepts custom type prop', () => {
      render(<Input type="email" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('type', 'email');
    });

    it('renders password input', () => {
      render(<Input type="password" />);
      const input = document.querySelector('input[type="password"]');
      expect(input).toBeInTheDocument();
    });
  });

  describe('Label', () => {
    it('renders label when provided', () => {
      render(<Input label="Email Address" />);
      expect(screen.getByText('Email Address')).toBeInTheDocument();
    });

    it('associates label with input', () => {
      render(<Input label="Username" />);
      const input = screen.getByLabelText('Username');
      expect(input).toBeInTheDocument();
    });

    it('renders without label when not provided', () => {
      render(<Input />);
      const labels = document.querySelectorAll('label');
      expect(labels).toHaveLength(0);
    });

    it('shows required indicator when required=true', () => {
      render(<Input label="Password" required />);
      const requiredIndicator = screen.getByText('*');
      expect(requiredIndicator).toBeInTheDocument();
      expect(requiredIndicator).toHaveAttribute('aria-label', 'required');
    });

    it('does not show required indicator by default', () => {
      render(<Input label="Email" />);
      expect(screen.queryByText('*')).not.toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('renders default variant by default', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('renders success variant', () => {
      render(<Input variant="success" />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('renders error variant', () => {
      render(<Input variant="error" />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('renders warning variant', () => {
      render(<Input variant="warning" />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });
  });

  describe('Sizes', () => {
    it('renders medium size by default', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('renders small size', () => {
      render(<Input size="small" />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('renders large size', () => {
      render(<Input size="large" />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });
  });

  describe('Helper Text', () => {
    it('renders helper text when provided', () => {
      render(<Input helperText="Enter a valid email address" />);
      expect(screen.getByText('Enter a valid email address')).toBeInTheDocument();
    });

    it('associates helper text with input via aria-describedby', () => {
      render(<Input helperText="Must be at least 8 characters" />);
      const input = screen.getByRole('textbox');
      const helperText = screen.getByText('Must be at least 8 characters');
      const describedBy = input.getAttribute('aria-describedby');
      expect(describedBy).toBeTruthy();
      expect(helperText).toHaveAttribute('id', describedBy!);
    });

    it('renders error helper text with role="alert"', () => {
      render(<Input variant="error" helperText="This field is required" />);
      const helperText = screen.getByText('This field is required');
      expect(helperText).toHaveAttribute('role', 'alert');
    });

    it('does not add role="alert" for non-error variants', () => {
      render(<Input variant="success" helperText="Looks good!" />);
      const helperText = screen.getByText('Looks good!');
      expect(helperText).not.toHaveAttribute('role');
    });

    it('renders without helper text when not provided', () => {
      const { container } = render(<Input />);
      const helperTexts = container.querySelectorAll('[role="alert"]');
      expect(helperTexts).toHaveLength(0);
    });
  });

  describe('Icons', () => {
    it('renders left icon', () => {
      render(
        <Input leftIcon={<span data-testid="search-icon">🔍</span>} />
      );
      expect(screen.getByTestId('search-icon')).toBeInTheDocument();
    });

    it('renders right icon', () => {
      render(
        <Input rightIcon={<span data-testid="clear-icon">✕</span>} />
      );
      expect(screen.getByTestId('clear-icon')).toBeInTheDocument();
    });

    it('renders both left and right icons', () => {
      render(
        <Input
          leftIcon={<span data-testid="left-icon">←</span>}
          rightIcon={<span data-testid="right-icon">→</span>}
        />
      );
      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
    });

    it('sets aria-hidden=true on icon wrappers', () => {
      render(
        <Input leftIcon={<span data-testid="icon">🔍</span>} />
      );
      const icon = screen.getByTestId('icon');
      expect(icon.parentElement).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Disabled State', () => {
    it('disables input when disabled=true', () => {
      render(<Input disabled />);
      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });

    it('does not accept input when disabled', async () => {
      render(<Input disabled />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      await userEvent.type(input, 'test');
      expect(input.value).toBe('');
    });

    it('is enabled by default', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).not.toBeDisabled();
    });
  });

  describe('Full Width', () => {
    it('renders full width input', () => {
      render(<Input fullWidth />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('renders normal width by default', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('accepts text input', async () => {
      render(<Input />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      await userEvent.type(input, 'Hello World');
      expect(input.value).toBe('Hello World');
    });

    it('calls onChange when value changes', async () => {
      const handleChange = vi.fn();
      render(<Input onChange={handleChange} />);
      const input = screen.getByRole('textbox');
      await userEvent.type(input, 'a');
      expect(handleChange).toHaveBeenCalled();
    });

    it('calls onFocus when input gains focus', async () => {
      const handleFocus = vi.fn();
      render(<Input onFocus={handleFocus} />);
      const input = screen.getByRole('textbox');
      await userEvent.click(input);
      expect(handleFocus).toHaveBeenCalledTimes(1);
    });

    it('calls onBlur when input loses focus', async () => {
      const handleBlur = vi.fn();
      render(<Input onBlur={handleBlur} />);
      const input = screen.getByRole('textbox');
      await userEvent.click(input);
      await userEvent.tab();
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });

    it('allows clearing input value', async () => {
      render(<Input />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      await userEvent.type(input, 'Test');
      expect(input.value).toBe('Test');
      await userEvent.clear(input);
      expect(input.value).toBe('');
    });
  });

  describe('Accessibility', () => {
    it('has role="textbox" by default', () => {
      render(<Input />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('is focusable by default', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      input.focus();
      expect(document.activeElement).toBe(input);
    });

    it('is not focusable when disabled', () => {
      render(<Input disabled />);
      const input = screen.getByRole('textbox');
      input.focus();
      expect(document.activeElement).not.toBe(input);
    });

    it('sets aria-invalid=true for error variant', () => {
      render(<Input variant="error" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('does not set aria-invalid for other variants', () => {
      render(<Input variant="success" />);
      const input = screen.getByRole('textbox');
      expect(input).not.toHaveAttribute('aria-invalid', 'true');
    });

    it('sets required attribute when required=true', () => {
      render(<Input required />);
      const input = screen.getByRole('textbox');
      expect(input).toBeRequired();
    });

    it('accepts aria-label prop', () => {
      render(<Input aria-label="Search input" />);
      expect(screen.getByRole('textbox', { name: /search input/i })).toBeInTheDocument();
    });

    it('accepts aria-describedby prop and combines with helper text', () => {
      render(
        <>
          <Input aria-describedby="external-desc" helperText="Helper text" />
          <span id="external-desc">External description</span>
        </>
      );
      const input = screen.getByRole('textbox');
      const describedBy = input.getAttribute('aria-describedby');
      expect(describedBy).toContain('external-desc');
      expect(describedBy).toContain('helper');
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      render(<Input className="custom-input" />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('accepts custom containerClassName', () => {
      render(<Input containerClassName="custom-container" />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('forwards ref to input element', () => {
      const ref = vi.fn();
      render(<Input ref={ref} />);
      expect(ref).toHaveBeenCalledWith(expect.any(HTMLInputElement));
    });

    it('spreads additional props to input element', () => {
      render(<Input data-testid="custom-input" data-analytics="input-event" />);
      const input = screen.getByTestId('custom-input');
      expect(input).toHaveAttribute('data-analytics', 'input-event');
    });

    it('accepts id prop', () => {
      render(<Input id="email-input" />);
      expect(screen.getByRole('textbox')).toHaveAttribute('id', 'email-input');
    });

    it('accepts name prop', () => {
      render(<Input name="username" />);
      expect(screen.getByRole('textbox')).toHaveAttribute('name', 'username');
    });

    it('accepts value prop', () => {
      render(<Input value="controlled value" onChange={() => {}} />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('controlled value');
    });

    it('accepts defaultValue prop', () => {
      render(<Input defaultValue="default value" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('default value');
    });

    it('accepts maxLength prop', () => {
      render(<Input maxLength={10} />);
      expect(screen.getByRole('textbox')).toHaveAttribute('maxLength', '10');
    });

    it('accepts pattern prop', () => {
      render(<Input pattern="[0-9]*" />);
      expect(screen.getByRole('textbox')).toHaveAttribute('pattern', '[0-9]*');
    });
  });

  describe('Combined Props', () => {
    it('renders complete input with all features', () => {
      render(
        <Input
          label="Email Address"
          placeholder="you@example.com"
          helperText="We'll never share your email"
          variant="default"
          size="medium"
          required
          leftIcon={<span data-testid="email-icon">✉</span>}
        />
      );
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
      expect(screen.getByText("We'll never share your email")).toBeInTheDocument();
      expect(screen.getByTestId('email-icon')).toBeInTheDocument();
      expect(screen.getByText('*')).toBeInTheDocument();
    });

    it('renders error input with message', () => {
      render(
        <Input
          label="Password"
          variant="error"
          helperText="Password must be at least 8 characters"
          required
        />
      );
      const input = screen.getByLabelText(/password/i);
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(screen.getByRole('alert')).toHaveTextContent('Password must be at least 8 characters');
    });

    it('renders success input with confirmation', () => {
      render(
        <Input
          label="Username"
          variant="success"
          helperText="Username is available"
          leftIcon={<span data-testid="check-icon">✓</span>}
        />
      );
      expect(screen.getByLabelText('Username')).toBeInTheDocument();
      expect(screen.getByText('Username is available')).toBeInTheDocument();
      expect(screen.getByTestId('check-icon')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has Input as display name', () => {
      expect(Input.displayName).toBe('Input');
    });
  });

  describe('Regression Tests', () => {
    it('handles rapid typing without errors', async () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      await userEvent.type(input, 'Quick brown fox jumps over lazy dog');
      expect(input).toHaveValue('Quick brown fox jumps over lazy dog');
    });

    it('transitions between variants', () => {
      const { rerender } = render(<Input variant="default" />);
      let input = screen.getByRole('textbox');
      expect(input).not.toHaveAttribute('aria-invalid', 'true');

      rerender(<Input variant="error" />);
      input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-invalid', 'true');

      rerender(<Input variant="success" />);
      input = screen.getByRole('textbox');
      expect(input).not.toHaveAttribute('aria-invalid', 'true');
    });

    it('maintains value during re-renders', () => {
      const { rerender } = render(<Input defaultValue="test" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('test');

      rerender(<Input defaultValue="test" helperText="New helper text" />);
      expect(input.value).toBe('test');
    });
  });
});
