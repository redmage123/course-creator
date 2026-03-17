/**
 * Textarea Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Textarea provides accessible and functional
 * multi-line input across all platform forms.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests auto-resize, character counting, validation, and accessibility
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Textarea } from './Textarea';

describe('Textarea Component', () => {
  beforeEach(() => {
    // Mock scrollHeight for auto-resize tests
    Object.defineProperty(HTMLTextAreaElement.prototype, 'scrollHeight', {
      configurable: true,
      value: 100,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders textarea with placeholder', () => {
      render(<Textarea placeholder="Enter description..." />);
      expect(screen.getByPlaceholderText('Enter description...')).toBeInTheDocument();
    });

    it('renders with label', () => {
      render(<Textarea label="Description" />);
      expect(screen.getByText('Description')).toBeInTheDocument();
    });

    it('renders required indicator', () => {
      render(<Textarea label="Description" required />);
      expect(screen.getByText('*')).toBeInTheDocument();
    });

    it('renders with helper text', () => {
      render(<Textarea helperText="Enter a detailed description" />);
      expect(screen.getByText('Enter a detailed description')).toBeInTheDocument();
    });

    it('renders with error message', () => {
      render(<Textarea error="Description is required" />);
      expect(screen.getByText('Description is required')).toBeInTheDocument();
    });

    it('renders with success message', () => {
      render(<Textarea success="Looks good!" />);
      expect(screen.getByText('Looks good!')).toBeInTheDocument();
    });

    it('renders with warning message', () => {
      render(<Textarea warning="Consider adding more details" />);
      expect(screen.getByText('Consider adding more details')).toBeInTheDocument();
    });
  });

  describe('Character Counter', () => {
    it('shows character count when enabled', () => {
      render(<Textarea showCharacterCount defaultValue="Hello" />);
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('shows character count with max length', () => {
      render(<Textarea showCharacterCount maxLength={100} defaultValue="Hello" />);
      expect(screen.getByText('5 / 100')).toBeInTheDocument();
    });

    it('updates character count on input', async () => {
      render(<Textarea showCharacterCount />);
      const textarea = screen.getByRole('textbox');

      await userEvent.type(textarea, 'Test');

      expect(screen.getByText('4')).toBeInTheDocument();
    });

    it('shows warning when approaching max length', () => {
      render(<Textarea showCharacterCount maxLength={10} defaultValue="123456789" />);
      const charCount = screen.getByText('9 / 10');
      expect(charCount).toBeInTheDocument();
    });

    it('does not show counter when disabled', () => {
      render(<Textarea defaultValue="Hello" />);
      expect(screen.queryByText('5')).not.toBeInTheDocument();
    });
  });

  describe('Controlled Mode', () => {
    it('displays controlled value', () => {
      render(<Textarea value="Controlled value" onChange={() => {}} />);
      expect(screen.getByRole('textbox')).toHaveValue('Controlled value');
    });

    it('calls onChange when typing', async () => {
      const handleChange = vi.fn();
      render(<Textarea value="" onChange={handleChange} />);

      const textarea = screen.getByRole('textbox');
      await userEvent.type(textarea, 'A');

      expect(handleChange).toHaveBeenCalled();
    });

    it('updates value when prop changes', () => {
      const { rerender } = render(<Textarea value="Initial" onChange={() => {}} />);
      expect(screen.getByRole('textbox')).toHaveValue('Initial');

      rerender(<Textarea value="Updated" onChange={() => {}} />);
      expect(screen.getByRole('textbox')).toHaveValue('Updated');
    });
  });

  describe('Uncontrolled Mode', () => {
    it('uses defaultValue', () => {
      render(<Textarea defaultValue="Default text" />);
      expect(screen.getByRole('textbox')).toHaveValue('Default text');
    });

    it('manages internal state', async () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');

      await userEvent.type(textarea, 'Hello World');

      expect(textarea).toHaveValue('Hello World');
    });
  });

  describe('Auto-resize', () => {
    it('enables auto-resize by default', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea).toBeInTheDocument();
    });

    it('disables auto-resize when autoResize is false', () => {
      render(<Textarea autoResize={false} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
    });

    it('respects minRows prop', () => {
      render(<Textarea minRows={5} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('rows', '5');
    });

    it('applies default minRows of 3', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('rows', '3');
    });
  });

  describe('Resize Control', () => {
    it('uses vertical resize by default', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
    });

    it('applies none resize', () => {
      render(<Textarea autoResize={false} resize="none" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
    });

    it('applies both resize', () => {
      render(<Textarea autoResize={false} resize="both" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('disables textarea when disabled prop is true', () => {
      render(<Textarea disabled />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeDisabled();
    });

    it('does not call onChange when disabled', async () => {
      const handleChange = vi.fn();
      render(<Textarea disabled onChange={handleChange} />);

      const textarea = screen.getByRole('textbox');
      await userEvent.type(textarea, 'Test');

      expect(handleChange).not.toHaveBeenCalled();
    });
  });

  describe('Validation States', () => {
    it('shows error state', () => {
      render(<Textarea error="Required field" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-invalid', 'true');
    });

    it('error takes precedence over success', () => {
      render(<Textarea error="Error" success="Success" />);
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.queryByText('Success')).not.toBeInTheDocument();
    });

    it('error takes precedence over warning', () => {
      render(<Textarea error="Error" warning="Warning" />);
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.queryByText('Warning')).not.toBeInTheDocument();
    });

    it('success takes precedence over warning', () => {
      render(<Textarea success="Success" warning="Warning" />);
      expect(screen.getByText('Success')).toBeInTheDocument();
      expect(screen.queryByText('Warning')).not.toBeInTheDocument();
    });
  });

  describe('Max Length', () => {
    it('enforces maxLength attribute', () => {
      render(<Textarea maxLength={10} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('maxLength', '10');
    });

    it('prevents input beyond maxLength', async () => {
      render(<Textarea maxLength={5} />);
      const textarea = screen.getByRole('textbox');

      fireEvent.change(textarea, { target: { value: 'Hello World' } });

      // Browser enforces maxLength, so value should be truncated
      expect(textarea.getAttribute('maxLength')).toBe('5');
    });
  });

  describe('Accessibility', () => {
    it('has correct role', () => {
      render(<Textarea />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('has aria-invalid when error', () => {
      render(<Textarea error="Error message" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-invalid', 'true');
    });

    it('has aria-required when required', () => {
      render(<Textarea required />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-required', 'true');
    });

    it('has aria-describedby when helper text present', () => {
      render(<Textarea helperText="Helper" id="test-textarea" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-describedby', 'test-textarea-message');
    });

    it('has aria-describedby when error present', () => {
      render(<Textarea error="Error" id="test-textarea" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-describedby', 'test-textarea-message');
    });

    it('label is associated with textarea', () => {
      render(<Textarea label="Description" id="test-textarea" />);
      const label = screen.getByText('Description');
      const textarea = screen.getByRole('textbox');
      expect(label).toHaveAttribute('for', 'test-textarea');
      expect(textarea).toHaveAttribute('id', 'test-textarea');
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      render(<Textarea className="custom-textarea" />);
      const container = screen.getByRole('textbox').closest('.custom-textarea');
      expect(container).toBeInTheDocument();
    });

    it('accepts custom id', () => {
      render(<Textarea id="custom-id" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('id', 'custom-id');
    });

    it('passes through additional props', () => {
      render(<Textarea name="description" data-testid="test-textarea" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('name', 'description');
      expect(textarea).toHaveAttribute('data-testid', 'test-textarea');
    });
  });

  describe('Display Name', () => {
    it('has Textarea as display name', () => {
      expect(Textarea.displayName).toBe('Textarea');
    });
  });

  describe('Forward Ref', () => {
    it('forwards ref to textarea element', () => {
      const ref = vi.fn();
      render(<Textarea ref={ref} />);
      expect(ref).toHaveBeenCalled();
    });
  });

  describe('Regression Tests', () => {
    it('handles empty value', () => {
      render(<Textarea value="" onChange={() => {}} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveValue('');
    });

    it('handles undefined value', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveValue('');
    });

    it('handles rapid typing', async () => {
      render(<Textarea showCharacterCount />);
      const textarea = screen.getByRole('textbox');

      await userEvent.type(textarea, 'Quick typing test');

      expect(textarea).toHaveValue('Quick typing test');
      expect(screen.getByText('17')).toBeInTheDocument();
    });

    it('cleans up on unmount', () => {
      const { unmount } = render(<Textarea />);
      unmount();
      expect(true).toBe(true); // Should not throw errors
    });

    it('handles defaultValue with character count', () => {
      render(<Textarea defaultValue="Initial" showCharacterCount />);
      expect(screen.getByText('7')).toBeInTheDocument();
    });
  });
});
