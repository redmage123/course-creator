/**
 * Select Component - Tami Design System
 *
 * BUSINESS CONTEXT:
 * Dropdown selection component for forms and filters across the platform.
 * Used for course selection, user role assignment, filter options, etc.
 *
 * TECHNICAL IMPLEMENTATION:
 * Custom dropdown with keyboard navigation, search, and accessibility.
 * Supports single/multi-select, option groups, and controlled/uncontrolled modes.
 *
 * DESIGN PRINCIPLES:
 * - Platform blue (#2563eb) for focus states
 * - 8px border radius
 * - Smooth dropdown animations
 * - WCAG 2.1 AA+ compliant (ARIA combobox pattern)
 */

import React, { useState, useRef, useEffect, useCallback, forwardRef } from 'react';
import styles from './Select.module.css';

export interface SelectOption {
  /**
   * Option value (used in form submission)
   */
  value: string;

  /**
   * Display label for the option
   */
  label: string;

  /**
   * Whether the option is disabled
   */
  disabled?: boolean;

  /**
   * Optional group for this option
   */
  group?: string;
}

export interface SelectProps {
  /**
   * Available options
   */
  options: SelectOption[];

  /**
   * Selected value(s)
   * - String for single select
   * - Array for multi-select
   */
  value?: string | string[];

  /**
   * Default value (uncontrolled mode)
   */
  defaultValue?: string | string[];

  /**
   * Change handler
   */
  onChange?: (value: string | string[]) => void;

  /**
   * Placeholder text when no selection
   */
  placeholder?: string;

  /**
   * Label for the select
   */
  label?: string;

  /**
   * Helper text below select
   */
  helperText?: string;

  /**
   * Error message (shows error state)
   */
  error?: string;

  /**
   * Required field indicator
   */
  required?: boolean;

  /**
   * Disabled state
   */
  disabled?: boolean;

  /**
   * Allow searching/filtering options
   * @default false
   */
  searchable?: boolean;

  /**
   * Allow selecting multiple options
   * @default false
   */
  multiple?: boolean;

  /**
   * Size variant
   * @default "medium"
   */
  size?: 'small' | 'medium' | 'large';

  /**
   * Custom className
   */
  className?: string;

  /**
   * Name attribute for form submission
   */
  name?: string;

  /**
   * ID for the select input
   */
  id?: string;
}

/**
 * Select Component
 *
 * WHY THIS APPROACH:
 * - Custom dropdown for full style control and accessibility
 * - ARIA combobox pattern for screen reader support
 * - Keyboard navigation matches native select behavior
 * - Search filtering for large option lists
 * - Multi-select with chips for selected items
 *
 * @example
 * ```tsx
 * // Single select
 * <Select
 *   label="Course"
 *   options={[
 *     { value: 'python', label: 'Python Basics' },
 *     { value: 'react', label: 'React Advanced' }
 *   ]}
 *   value={selectedCourse}
 *   onChange={setSelectedCourse}
 * />
 *
 * // Multi-select with search
 * <Select
 *   label="Tags"
 *   options={tagOptions}
 *   multiple
 *   searchable
 *   value={selectedTags}
 *   onChange={setSelectedTags}
 * />
 *
 * // With error state
 * <Select
 *   label="Role"
 *   options={roleOptions}
 *   required
 *   error="Please select a role"
 * />
 * ```
 */
export const Select = forwardRef<HTMLDivElement, SelectProps>(({
  options,
  value,
  defaultValue,
  onChange,
  placeholder = 'Select...',
  label,
  helperText,
  error,
  required = false,
  disabled = false,
  searchable = false,
  multiple = false,
  size = 'medium',
  className,
  name,
  id,
}, ref) => {
  // State management
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState<number>(0);
  const [internalValue, setInternalValue] = useState<string | string[]>(
    defaultValue ?? (multiple ? [] : '')
  );

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);

  // Use controlled or uncontrolled value
  const currentValue = value !== undefined ? value : internalValue;

  // Filter options based on search term
  const filteredOptions = searchTerm
    ? options.filter(option =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  // Get display text for selected value(s)
  const getDisplayText = useCallback(() => {
    if (multiple && Array.isArray(currentValue)) {
      if (currentValue.length === 0) return placeholder;
      if (currentValue.length === 1) {
        const option = options.find(opt => opt.value === currentValue[0]);
        return option?.label || placeholder;
      }
      return `${currentValue.length} selected`;
    }

    const option = options.find(opt => opt.value === currentValue);
    return option?.label || placeholder;
  }, [currentValue, multiple, options, placeholder]);

  // Handle option selection
  const handleSelect = (optionValue: string) => {
    let newValue: string | string[];

    if (multiple && Array.isArray(currentValue)) {
      // Toggle selection for multi-select
      if (currentValue.includes(optionValue)) {
        newValue = currentValue.filter(v => v !== optionValue);
      } else {
        newValue = [...currentValue, optionValue];
      }
    } else {
      // Single select
      newValue = optionValue;
      setIsOpen(false);
    }

    // Update internal state if uncontrolled
    if (value === undefined) {
      setInternalValue(newValue);
    }

    // Call onChange handler
    onChange?.(newValue);

    // Reset search
    setSearchTerm('');
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (disabled) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev =>
            prev < filteredOptions.length - 1 ? prev + 1 : prev
          );
        }
        break;

      case 'ArrowUp':
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex(prev => (prev > 0 ? prev - 1 : 0));
        }
        break;

      case 'Enter':
        event.preventDefault();
        if (isOpen && filteredOptions[highlightedIndex]) {
          const option = filteredOptions[highlightedIndex];
          if (!option.disabled) {
            handleSelect(option.value);
          }
        } else {
          setIsOpen(true);
        }
        break;

      case 'Escape':
        event.preventDefault();
        setIsOpen(false);
        setSearchTerm('');
        break;

      case ' ':
        if (!searchable) {
          event.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
          } else if (filteredOptions[highlightedIndex]) {
            const option = filteredOptions[highlightedIndex];
            if (!option.disabled) {
              handleSelect(option.value);
            }
          }
        }
        break;

      case 'Tab':
        if (isOpen) {
          setIsOpen(false);
        }
        break;
    }
  };

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll highlighted option into view
  useEffect(() => {
    if (isOpen && listboxRef.current) {
      const highlightedElement = listboxRef.current.children[
        highlightedIndex
      ] as HTMLElement;

      if (highlightedElement) {
        highlightedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth',
        });
      }
    }
  }, [highlightedIndex, isOpen]);

  // Reset highlighted index when options change
  useEffect(() => {
    setHighlightedIndex(0);
  }, [filteredOptions]);

  // Check if option is selected
  const isSelected = (optionValue: string) => {
    if (multiple && Array.isArray(currentValue)) {
      return currentValue.includes(optionValue);
    }
    return currentValue === optionValue;
  };

  // Generate unique ID if not provided
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
  const listboxId = `${selectId}-listbox`;

  // Build container classes
  const containerClasses = [
    styles['select-container'],
    styles[`select-${size}`],
    error && styles['select-error'],
    disabled && styles['select-disabled'],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div ref={containerRef} className={containerClasses}>
      {/* Label */}
      {label && (
        <label htmlFor={selectId} className={styles['select-label']}>
          {label}
          {required && <span className={styles['select-required']}>*</span>}
        </label>
      )}

      {/* Select trigger */}
      <div
        ref={ref}
        className={styles['select-trigger']}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls={listboxId}
        aria-labelledby={label ? `${selectId}-label` : undefined}
        aria-invalid={!!error}
        aria-required={required}
        tabIndex={disabled ? -1 : 0}
      >
        {/* Selected value display or search input */}
        {searchable && isOpen ? (
          <input
            ref={inputRef}
            type="text"
            className={styles['select-search']}
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Type to search..."
          />
        ) : (
          <span className={styles['select-value']}>
            {getDisplayText()}
          </span>
        )}

        {/* Dropdown arrow */}
        <svg
          className={`${styles['select-arrow']} ${isOpen ? styles['select-arrow-open'] : ''}`}
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
        >
          <path
            d="M5 7.5L10 12.5L15 7.5"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {/* Dropdown listbox */}
      {isOpen && (
        <ul
          ref={listboxRef}
          id={listboxId}
          className={styles['select-dropdown']}
          role="listbox"
          aria-multiselectable={multiple}
        >
          {filteredOptions.length === 0 ? (
            <li className={styles['select-option-empty']} role="option">
              No options found
            </li>
          ) : (
            filteredOptions.map((option, index) => (
              <li
                key={option.value}
                className={`${styles['select-option']} ${
                  isSelected(option.value) ? styles['select-option-selected'] : ''
                } ${
                  index === highlightedIndex ? styles['select-option-highlighted'] : ''
                } ${option.disabled ? styles['select-option-disabled'] : ''}`}
                role="option"
                aria-selected={isSelected(option.value)}
                aria-disabled={option.disabled}
                onClick={() => !option.disabled && handleSelect(option.value)}
              >
                {/* Checkbox for multi-select */}
                {multiple && (
                  <span className={styles['select-checkbox']}>
                    {isSelected(option.value) && (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path
                          d="M13.333 4L6 11.333L2.667 8"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    )}
                  </span>
                )}

                {/* Option label */}
                <span className={styles['select-option-label']}>
                  {option.label}
                </span>

                {/* Checkmark for single select */}
                {!multiple && isSelected(option.value) && (
                  <svg
                    className={styles['select-checkmark']}
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                  >
                    <path
                      d="M13.333 4L6 11.333L2.667 8"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </li>
            ))
          )}
        </ul>
      )}

      {/* Helper text or error */}
      {(helperText || error) && (
        <div className={styles['select-message']}>
          {error ? (
            <span className={styles['select-error-text']}>{error}</span>
          ) : (
            <span className={styles['select-helper-text']}>{helperText}</span>
          )}
        </div>
      )}

      {/* Hidden input for form submission */}
      {name && (
        <input
          type="hidden"
          name={name}
          value={
            Array.isArray(currentValue)
              ? currentValue.join(',')
              : currentValue
          }
        />
      )}
    </div>
  );
});

Select.displayName = 'Select';
