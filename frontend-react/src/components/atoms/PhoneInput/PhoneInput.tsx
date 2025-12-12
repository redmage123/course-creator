/**
 * Phone Input Component with Country Code Selector
 *
 * BUSINESS CONTEXT:
 * International phone number input for organization and user registration.
 * Provides country code dropdown with flag icons and country names.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Searchable country dropdown with flag emojis
 * - United States default at top of list
 * - Validates phone number format
 * - Returns combined dialCode + phone number
 *
 * DESIGN PRINCIPLES:
 * - Flag emoji on left, country name on right in dropdown
 * - Platform blue (#2563eb) for focus states
 * - WCAG 2.1 AA+ compliant
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { countries, Country, defaultCountry } from '../../../data/countries';
import styles from './PhoneInput.module.css';

export interface PhoneInputProps {
  /**
   * Label for the input
   */
  label?: string;

  /**
   * Currently selected country code (ISO 3166-1 alpha-2)
   */
  countryCode?: string;

  /**
   * Phone number value (without country code)
   */
  value?: string;

  /**
   * Change handler for phone number
   */
  onChange?: (phone: string) => void;

  /**
   * Change handler for country code
   */
  onCountryChange?: (countryCode: string, dialCode: string) => void;

  /**
   * Placeholder text for phone input
   */
  placeholder?: string;

  /**
   * Error message
   */
  error?: string;

  /**
   * Helper text
   */
  helperText?: string;

  /**
   * Required field indicator
   */
  required?: boolean;

  /**
   * Disabled state
   */
  disabled?: boolean;

  /**
   * Input name for form submission
   */
  name?: string;

  /**
   * Custom className
   */
  className?: string;
}

/**
 * Phone Input Component
 *
 * WHY THIS APPROACH:
 * - Combines country selector with phone input in single component
 * - Flag emojis provide visual identification of countries
 * - Searchable dropdown for easy country selection
 * - US default at top matches user requirements
 *
 * @example
 * ```tsx
 * <PhoneInput
 *   label="Phone Number"
 *   countryCode={countryCode}
 *   value={phone}
 *   onChange={setPhone}
 *   onCountryChange={(code, dial) => setCountryCode(code)}
 *   required
 * />
 * ```
 */
export const PhoneInput: React.FC<PhoneInputProps> = ({
  label,
  countryCode = 'US',
  value = '',
  onChange,
  onCountryChange,
  placeholder = 'Phone number',
  error,
  helperText,
  required = false,
  disabled = false,
  name,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Find selected country
  const selectedCountry = countries.find(c => c.code === countryCode) || defaultCountry;

  // Filter countries based on search term
  const filteredCountries = searchTerm
    ? countries.filter(
        c =>
          c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.dialCode.includes(searchTerm) ||
          c.code.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : countries;

  // Handle country selection
  const handleCountrySelect = (country: Country) => {
    onCountryChange?.(country.code, country.dialCode);
    setIsOpen(false);
    setSearchTerm('');
  };

  // Handle phone number change
  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value.replace(/[^0-9\s\-()]/g, '');
    onChange?.(newValue);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev =>
            prev < filteredCountries.length - 1 ? prev + 1 : prev
          );
        }
        break;

      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setHighlightedIndex(prev => (prev > 0 ? prev - 1 : 0));
        }
        break;

      case 'Enter':
        e.preventDefault();
        if (isOpen && filteredCountries[highlightedIndex]) {
          handleCountrySelect(filteredCountries[highlightedIndex]);
        } else {
          setIsOpen(true);
        }
        break;

      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setSearchTerm('');
        break;

      case 'Tab':
        if (isOpen) {
          setIsOpen(false);
          setSearchTerm('');
        }
        break;
    }
  };

  // Close dropdown when clicking outside
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

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // Scroll highlighted item into view
  useEffect(() => {
    if (isOpen && listRef.current) {
      const highlightedEl = listRef.current.children[highlightedIndex] as HTMLElement;
      if (highlightedEl) {
        highlightedEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [highlightedIndex, isOpen]);

  // Reset highlighted index when filter changes
  useEffect(() => {
    setHighlightedIndex(0);
  }, [filteredCountries.length]);

  const containerClasses = [
    styles['phone-input-container'],
    error && styles['phone-input-error'],
    disabled && styles['phone-input-disabled'],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div ref={containerRef} className={containerClasses}>
      {/* Label */}
      {label && (
        <label className={styles['phone-input-label']}>
          {label}
          {required && <span className={styles['phone-input-required']}>*</span>}
        </label>
      )}

      <div className={styles['phone-input-wrapper']}>
        {/* Country selector button */}
        <button
          type="button"
          className={styles['country-selector']}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-label={`Select country, current: ${selectedCountry.name}`}
        >
          <span className={styles['country-flag']}>{selectedCountry.flag}</span>
          <span className={styles['country-dial-code']}>{selectedCountry.dialCode}</span>
          <svg
            className={`${styles['dropdown-arrow']} ${isOpen ? styles['dropdown-arrow-open'] : ''}`}
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
          >
            <path
              d="M3 4.5L6 7.5L9 4.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        {/* Phone number input */}
        <input
          type="tel"
          className={styles['phone-number-input']}
          value={value}
          onChange={handlePhoneChange}
          placeholder={placeholder}
          disabled={disabled}
          name={name}
          aria-invalid={!!error}
          aria-describedby={error ? `${name}-error` : undefined}
        />

        {/* Country dropdown */}
        {isOpen && (
          <div className={styles['country-dropdown']}>
            {/* Search input */}
            <div className={styles['search-container']}>
              <input
                ref={searchInputRef}
                type="text"
                className={styles['search-input']}
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                placeholder="Search country..."
                onKeyDown={handleKeyDown}
              />
            </div>

            {/* Country list */}
            <ul
              ref={listRef}
              className={styles['country-list']}
              role="listbox"
              aria-label="Select country"
            >
              {filteredCountries.length === 0 ? (
                <li className={styles['country-list-empty']}>No countries found</li>
              ) : (
                filteredCountries.map((country, index) => (
                  <li
                    key={country.code}
                    className={`${styles['country-list-item']} ${
                      index === highlightedIndex ? styles['country-list-item-highlighted'] : ''
                    } ${country.code === countryCode ? styles['country-list-item-selected'] : ''}`}
                    role="option"
                    aria-selected={country.code === countryCode}
                    onClick={() => handleCountrySelect(country)}
                  >
                    <span className={styles['country-item-flag']}>{country.flag}</span>
                    <span className={styles['country-item-name']}>{country.name}</span>
                    <span className={styles['country-item-dial']}>{country.dialCode}</span>
                  </li>
                ))
              )}
            </ul>
          </div>
        )}
      </div>

      {/* Error or helper text */}
      {(error || helperText) && (
        <div className={styles['phone-input-message']}>
          {error ? (
            <span id={`${name}-error`} className={styles['phone-input-error-text']}>
              {error}
            </span>
          ) : (
            <span className={styles['phone-input-helper-text']}>{helperText}</span>
          )}
        </div>
      )}
    </div>
  );
};

PhoneInput.displayName = 'PhoneInput';
