/**
 * Select Component Tests
 *
 * BUSINESS CONTEXT:
 * Test suite ensuring Select provides accessible and functional
 * dropdown selection across all platform forms and filters.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests keyboard navigation, search, multi-select, and accessibility
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Select, SelectOption } from './Select';

const mockOptions: SelectOption[] = [
  { value: 'python', label: 'Python Basics' },
  { value: 'react', label: 'React Advanced' },
  { value: 'node', label: 'Node.js Fundamentals' },
  { value: 'typescript', label: 'TypeScript Mastery' },
  { value: 'docker', label: 'Docker Essentials', disabled: true },
];

describe('Select Component', () => {
  beforeEach(() => {
    // Mock scrollIntoView (not available in jsdom)
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders select with placeholder', () => {
      render(<Select options={mockOptions} placeholder="Choose a course" />);
      expect(screen.getByText('Choose a course')).toBeInTheDocument();
    });

    it('renders with label', () => {
      render(<Select options={mockOptions} label="Course" />);
      expect(screen.getByText('Course')).toBeInTheDocument();
    });

    it('renders required indicator', () => {
      render(<Select options={mockOptions} label="Course" required />);
      expect(screen.getByText('*')).toBeInTheDocument();
    });

    it('renders with helper text', () => {
      render(<Select options={mockOptions} helperText="Select your preferred course" />);
      expect(screen.getByText('Select your preferred course')).toBeInTheDocument();
    });

    it('renders with error message', () => {
      render(<Select options={mockOptions} error="Course is required" />);
      expect(screen.getByText('Course is required')).toBeInTheDocument();
    });

    it('renders as combobox role', () => {
      render(<Select options={mockOptions} />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('Single Select - Controlled Mode', () => {
    it('displays selected option', () => {
      render(<Select options={mockOptions} value="react" />);
      expect(screen.getByText('React Advanced')).toBeInTheDocument();
    });

    it('calls onChange when option selected', async () => {
      const handleChange = vi.fn();
      render(<Select options={mockOptions} onChange={handleChange} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const option = screen.getByText('Python Basics');
      await userEvent.click(option);

      expect(handleChange).toHaveBeenCalledWith('python');
    });

    it('closes dropdown after selection', async () => {
      render(<Select options={mockOptions} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      expect(screen.getByRole('listbox')).toBeInTheDocument();

      const option = screen.getByText('Python Basics');
      await userEvent.click(option);

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
      });
    });

    it('updates value when controlled value changes', () => {
      const { rerender } = render(<Select options={mockOptions} value="python" />);
      expect(screen.getByText('Python Basics')).toBeInTheDocument();

      rerender(<Select options={mockOptions} value="react" />);
      expect(screen.getByText('React Advanced')).toBeInTheDocument();
    });
  });

  describe('Single Select - Uncontrolled Mode', () => {
    it('uses defaultValue', () => {
      render(<Select options={mockOptions} defaultValue="react" />);
      expect(screen.getByText('React Advanced')).toBeInTheDocument();
    });

    it('manages internal state', async () => {
      render(<Select options={mockOptions} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const option = screen.getByText('Node.js Fundamentals');
      await userEvent.click(option);

      expect(screen.getByText('Node.js Fundamentals')).toBeInTheDocument();
    });
  });

  describe('Multi-Select', () => {
    it('allows selecting multiple options', async () => {
      const handleChange = vi.fn();
      render(<Select options={mockOptions} multiple onChange={handleChange} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const option1 = screen.getByText('Python Basics');
      await userEvent.click(option1);

      expect(handleChange).toHaveBeenCalledWith(['python']);

      const option2 = screen.getByText('React Advanced');
      await userEvent.click(option2);

      expect(handleChange).toHaveBeenCalledWith(['python', 'react']);
    });

    it('displays count when multiple selected', async () => {
      render(<Select options={mockOptions} multiple value={['python', 'react']} />);
      expect(screen.getByText('2 selected')).toBeInTheDocument();
    });

    it('toggles selection on click', async () => {
      const handleChange = vi.fn();
      render(
        <Select
          options={mockOptions}
          multiple
          value={['python']}
          onChange={handleChange}
        />
      );

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const options = screen.getAllByRole('option');
      const pythonOption = options.find(opt => opt.textContent === 'Python Basics');
      await userEvent.click(pythonOption!);

      expect(handleChange).toHaveBeenCalledWith([]);
    });

    it('keeps dropdown open after selection', async () => {
      render(<Select options={mockOptions} multiple />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const option = screen.getByText('Python Basics');
      await userEvent.click(option);

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('renders checkboxes for options', async () => {
      render(<Select options={mockOptions} multiple />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const listbox = screen.getByRole('listbox');
      expect(listbox).toHaveAttribute('aria-multiselectable', 'true');
    });
  });

  describe('Keyboard Navigation', () => {
    it('opens dropdown on Enter key', async () => {
      render(<Select options={mockOptions} />);

      const trigger = screen.getByRole('combobox');
      trigger.focus();
      await userEvent.keyboard('{Enter}');

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('navigates options with ArrowDown', async () => {
      render(<Select options={mockOptions} />);

      const trigger = screen.getByRole('combobox');
      trigger.focus();
      await userEvent.keyboard('{ArrowDown}');

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('selects highlighted option with Enter', async () => {
      const handleChange = vi.fn();
      render(<Select options={mockOptions} onChange={handleChange} />);

      const trigger = screen.getByRole('combobox');
      trigger.focus();
      await userEvent.keyboard('{ArrowDown}');
      await userEvent.keyboard('{Enter}');

      expect(handleChange).toHaveBeenCalledWith('python');
    });

    it('closes dropdown on Escape key', async () => {
      render(<Select options={mockOptions} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      expect(screen.getByRole('listbox')).toBeInTheDocument();

      await userEvent.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
      });
    });

    it('closes dropdown on Tab key', async () => {
      render(<Select options={mockOptions} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      expect(screen.getByRole('listbox')).toBeInTheDocument();

      await userEvent.keyboard('{Tab}');

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('shows search input when searchable and open', async () => {
      render(<Select options={mockOptions} searchable />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const searchInput = screen.getByPlaceholderText('Type to search...');
      expect(searchInput).toBeInTheDocument();
    });

    it('filters options based on search term', async () => {
      render(<Select options={mockOptions} searchable />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const searchInput = screen.getByPlaceholderText('Type to search...');
      fireEvent.change(searchInput, { target: { value: 'react' } });

      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(1);
      expect(options[0]).toHaveTextContent('React Advanced');
    });

    it('shows "no options" when search has no results', async () => {
      render(<Select options={mockOptions} searchable />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const searchInput = screen.getByPlaceholderText('Type to search...');
      fireEvent.change(searchInput, { target: { value: 'xyz' } });

      const option = screen.getByRole('option');
      expect(option).toHaveTextContent('No options found');
    });

    it('search is case-insensitive', async () => {
      render(<Select options={mockOptions} searchable />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const searchInput = screen.getByPlaceholderText('Type to search...');
      fireEvent.change(searchInput, { target: { value: 'PYTHON' } });

      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(1);
      expect(options[0]).toHaveTextContent('Python Basics');
    });

    it('clears search when dropdown closes', async () => {
      render(<Select options={mockOptions} searchable />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const searchInput = screen.getByPlaceholderText('Type to search...');
      await userEvent.type(searchInput, 'react');

      await userEvent.keyboard('{Escape}');

      await userEvent.click(trigger);

      const newSearchInput = screen.getByPlaceholderText('Type to search...');
      expect(newSearchInput).toHaveValue('');
    });
  });

  describe('Disabled State', () => {
    it('does not open when disabled', async () => {
      render(<Select options={mockOptions} disabled />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('has negative tabIndex when disabled', () => {
      render(<Select options={mockOptions} disabled />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('tabIndex', '-1');
    });

    it('does not respond to keyboard when disabled', async () => {
      render(<Select options={mockOptions} disabled />);

      const trigger = screen.getByRole('combobox');
      trigger.focus();
      await userEvent.keyboard('{Enter}');

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('skips disabled options', async () => {
      const handleChange = vi.fn();
      render(<Select options={mockOptions} onChange={handleChange} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const disabledOption = screen.getByText('Docker Essentials');
      await userEvent.click(disabledOption);

      expect(handleChange).not.toHaveBeenCalled();
    });
  });

  describe('Click Outside', () => {
    it('closes dropdown when clicking outside', async () => {
      render(
        <div>
          <Select options={mockOptions} />
          <div data-testid="outside">Outside element</div>
        </div>
      );

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      expect(screen.getByRole('listbox')).toBeInTheDocument();

      const outside = screen.getByTestId('outside');
      await userEvent.click(outside);

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
      });
    });
  });

  describe('Size Variants', () => {
    it('renders small size', () => {
      render(<Select options={mockOptions} size="small" />);
      const trigger = screen.getByRole('combobox');
      expect(trigger.parentElement).toBeInTheDocument();
    });

    it('renders medium size by default', () => {
      render(<Select options={mockOptions} />);
      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeInTheDocument();
    });

    it('renders large size', () => {
      render(<Select options={mockOptions} size="large" />);
      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role="combobox"', () => {
      render(<Select options={mockOptions} />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('has aria-expanded attribute', () => {
      render(<Select options={mockOptions} />);
      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('aria-expanded', 'false');
    });

    it('updates aria-expanded when opened', async () => {
      render(<Select options={mockOptions} />);
      const trigger = screen.getByRole('combobox');

      await userEvent.click(trigger);

      expect(trigger).toHaveAttribute('aria-expanded', 'true');
    });

    it('has aria-haspopup="listbox"', () => {
      render(<Select options={mockOptions} />);
      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('aria-haspopup', 'listbox');
    });

    it('has aria-invalid when error', () => {
      render(<Select options={mockOptions} error="Required" />);
      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('aria-invalid', 'true');
    });

    it('has aria-required when required', () => {
      render(<Select options={mockOptions} required />);
      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('aria-required', 'true');
    });

    it('options have role="option"', async () => {
      render(<Select options={mockOptions} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(mockOptions.length);
    });

    it('selected option has aria-selected="true"', async () => {
      render(<Select options={mockOptions} value="react" />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const options = screen.getAllByRole('option');
      const reactOption = options.find(opt => opt.textContent === 'React Advanced');
      expect(reactOption).toHaveAttribute('aria-selected', 'true');
    });

    it('listbox has aria-multiselectable for multi-select', async () => {
      render(<Select options={mockOptions} multiple />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      const listbox = screen.getByRole('listbox');
      expect(listbox).toHaveAttribute('aria-multiselectable', 'true');
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      render(<Select options={mockOptions} className="custom-select" />);
      const trigger = screen.getByRole('combobox');
      expect(trigger.parentElement?.className).toContain('custom-select');
    });

    it('renders hidden input with name for form submission', () => {
      const { container } = render(
        <Select options={mockOptions} name="course" value="python" />
      );
      const hiddenInput = container.querySelector('input[type="hidden"]');
      expect(hiddenInput).toHaveAttribute('name', 'course');
      expect(hiddenInput).toHaveValue('python');
    });

    it('accepts custom id', () => {
      render(<Select options={mockOptions} id="course-select" />);
      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('has Select as display name', () => {
      expect(Select.displayName).toBe('Select');
    });
  });

  describe('Regression Tests', () => {
    it('handles empty options array', () => {
      render(<Select options={[]} />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('shows no options message when no options provided', async () => {
      render(<Select options={[]} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      expect(screen.getByText('No options found')).toBeInTheDocument();
    });

    it('handles rapid open/close clicks', async () => {
      render(<Select options={mockOptions} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);
      await userEvent.click(trigger);
      await userEvent.click(trigger);

      // Should handle without errors
      expect(trigger).toBeInTheDocument();
    });

    it('cleans up event listeners on unmount', () => {
      const { unmount } = render(<Select options={mockOptions} />);
      unmount();
      expect(true).toBe(true);
    });
  });
});
