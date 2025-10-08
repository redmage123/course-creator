/**
 * Inline Form Validation Module
 * Provides real-time form validation feedback
 *
 * Purpose:
 * - Validates form fields as users complete them (on blur)
 * - Provides immediate error feedback with ARIA announcements
 * - Clears errors progressively as users fix issues (on input)
 * - Implements WCAG 3.3.1 (Error Identification) and 3.3.3 (Error Suggestion)
 *
 * Business Context:
 * Improves user experience by catching errors early, reducing form submission
 * failures and user frustration. Critical for accessibility - screen reader users
 * get immediate feedback about form errors.
 *
 * WCAG Compliance:
 * - 3.3.1 (Level A): Error Identification
 * - 3.3.3 (Level AA): Error Suggestion
 * - 3.3.4 (Level AA): Error Prevention
 *
 * @module inline-validation
 * @version 1.0.0
 */

(function() {
    'use strict';

    /**
     * Inline Form Validator Class
     * Manages validation for a single form
     */
    class InlineValidator {
        /**
         * Create a new validator for a form
         * @param {HTMLFormElement|string} formSelector - Form element or CSS selector
         */
        constructor(formSelector) {
            // Get form element
            if (typeof formSelector === 'string') {
                this.form = document.querySelector(formSelector);
            } else {
                this.form = formSelector;
            }

            if (!this.form) {
                console.warn('[InlineValidator] Form not found:', formSelector);
                return;
            }

            // Find all validatable inputs
            this.inputs = this.form.querySelectorAll('input, select, textarea');

            // Initialize validation event listeners
            this.initValidation();

            console.debug('[InlineValidator] Initialized for form:', this.form.id || this.form.name);
        }

        /**
         * Initialize validation event listeners
         */
        initValidation() {
            this.inputs.forEach(input => {
                // Skip inputs that shouldn't be validated
                if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') {
                    return;
                }

                // Validate on blur (after user leaves field)
                input.addEventListener('blur', () => this.validateField(input));

                // Clear errors as user types (progressive enhancement)
                input.addEventListener('input', () => {
                    if (input.classList.contains('is-invalid') || input.getAttribute('aria-invalid') === 'true') {
                        this.validateField(input);
                    }
                });

                // For checkboxes and radios, validate on change
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.addEventListener('change', () => this.validateField(input));
                }
            });

            // Prevent form submission if there are errors
            this.form.addEventListener('submit', (e) => {
                if (!this.validateForm()) {
                    e.preventDefault();
                    this.focusFirstError();
                }
            });
        }

        /**
         * Validate a single form field
         * @param {HTMLInputElement} input - The input element to validate
         * @returns {boolean} - True if valid, false if invalid
         */
        validateField(input) {
            const errorId = `${input.id}-error`;
            let errorDiv = document.getElementById(errorId);

            // Create error div if it doesn't exist
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.id = errorId;
                errorDiv.className = 'error-message';
                errorDiv.setAttribute('role', 'alert');
                errorDiv.setAttribute('aria-live', 'assertive');
                errorDiv.style.display = 'none';

                // Insert after the input (or after label if input is inside label)
                const insertAfter = input.parentElement.tagName === 'LABEL'
                    ? input.parentElement
                    : input;
                insertAfter.parentElement.insertBefore(errorDiv, insertAfter.nextSibling);

                // Link error to input for accessibility
                const describedBy = input.getAttribute('aria-describedby') || '';
                input.setAttribute('aria-describedby', `${describedBy} ${errorId}`.trim());
            }

            let errorMessage = '';

            // Check built-in HTML5 validity
            if (input.validity.valueMissing) {
                const label = this.getFieldLabel(input);
                errorMessage = `${label} is required`;
            } else if (input.validity.typeMismatch) {
                if (input.type === 'email') {
                    errorMessage = 'Please enter a valid email address (e.g., user@example.com)';
                } else if (input.type === 'url') {
                    errorMessage = 'Please enter a valid URL (e.g., https://example.com)';
                } else {
                    errorMessage = `Please enter a valid ${input.type}`;
                }
            } else if (input.validity.tooShort) {
                errorMessage = `Must be at least ${input.minLength} characters (currently ${input.value.length})`;
            } else if (input.validity.tooLong) {
                errorMessage = `Must be no more than ${input.maxLength} characters (currently ${input.value.length})`;
            } else if (input.validity.rangeUnderflow) {
                errorMessage = `Must be at least ${input.min}`;
            } else if (input.validity.rangeOverflow) {
                errorMessage = `Must be no more than ${input.max}`;
            } else if (input.validity.patternMismatch) {
                // Use custom error message if provided
                errorMessage = input.getAttribute('data-error') || input.getAttribute('title') || 'Invalid format';
            } else if (input.validity.badInput) {
                errorMessage = 'Invalid input';
            }

            // Custom validation for confirm password fields
            if (input.name && input.name.includes('confirm') && input.name.includes('password')) {
                const passwordField = this.form.querySelector('[name="password"], [type="password"]');
                if (passwordField && input.value !== passwordField.value) {
                    errorMessage = 'Passwords do not match';
                }
            }

            // Apply validation state
            if (errorMessage) {
                input.setAttribute('aria-invalid', 'true');
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
                errorDiv.textContent = errorMessage;
                errorDiv.style.display = 'block';
                return false;
            } else {
                // Only mark as valid if field has been touched and has content
                if (input.value.trim()) {
                    input.setAttribute('aria-invalid', 'false');
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                } else {
                    input.removeAttribute('aria-invalid');
                    input.classList.remove('is-invalid', 'is-valid');
                }
                errorDiv.style.display = 'none';
                return true;
            }
        }

        /**
         * Get user-friendly label for a field
         * @param {HTMLInputElement} input - The input element
         * @returns {string} - The field label text
         */
        getFieldLabel(input) {
            // Try to find associated label
            const label = input.labels && input.labels[0];
            if (label) {
                return label.textContent.replace('*', '').trim();
            }

            // Fallback to input name or id
            if (input.name) {
                return input.name.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim();
            }

            return 'This field';
        }

        /**
         * Validate entire form
         * @returns {boolean} - True if all fields valid, false otherwise
         */
        validateForm() {
            let isValid = true;

            this.inputs.forEach(input => {
                if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') {
                    return;
                }

                if (!this.validateField(input)) {
                    isValid = false;
                }
            });

            return isValid;
        }

        /**
         * Focus the first field with an error
         */
        focusFirstError() {
            const firstInvalid = this.form.querySelector('.is-invalid, [aria-invalid="true"]');
            if (firstInvalid) {
                firstInvalid.focus();
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }

    /**
     * Initialize validators for all forms on page
     */
    function initializeAllForms() {
        const forms = document.querySelectorAll('form');

        forms.forEach(form => {
            // Skip if form has data-no-validation attribute
            if (form.hasAttribute('data-no-validation')) {
                return;
            }

            new InlineValidator(form);
        });

        console.debug(`[InlineValidator] Initialized ${forms.length} forms`);
    }

    /**
     * Expose InlineValidator globally for manual initialization
     */
    window.InlineValidator = InlineValidator;

    /**
     * Auto-initialize when DOM is ready
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeAllForms);
    } else {
        initializeAllForms();
    }
})();
