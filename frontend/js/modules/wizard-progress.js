/**
 * Wizard Progress Indicator Module
 *
 * BUSINESS CONTEXT:
 * Multi-step wizards are critical conversion points in the Course Creator platform.
 * Studies show that clear progress indicators can:
 * - Reduce abandonment rates by 30%
 * - Improve completion rates by 25%
 * - Decrease support tickets about "how many steps are left"
 *
 * This module provides a reusable, accessible wizard progress component that:
 * - Shows total steps and current position
 * - Allows back-navigation to completed steps
 * - Provides visual feedback for validation errors
 * - Works on mobile and desktop
 * - Supports keyboard navigation
 *
 * TECHNICAL IMPLEMENTATION:
 * - Event-driven architecture (emits 'step-change' events)
 * - DOM-based state management
 * - Accessible (ARIA labels, keyboard navigation)
 * - Uses OUR blue (#2563eb) for all primary actions
 * - No external dependencies or references
 *
 * @module wizard-progress
 * @version 1.0.0
 * @date 2025-10-17
 */

/**
 * Wizard Progress Indicator Class
 *
 * Usage:
 * const wizard = new WizardProgress({
 *     container: '#my-wizard-progress',
 *     steps: [
 *         { id: 'basic-info', label: 'Basic Info', description: 'Project details' },
 *         { id: 'tracks', label: 'Tracks', description: 'Learning paths' },
 *         { id: 'review', label: 'Review', description: 'Confirm details' }
 *     ],
 *     currentStep: 0,
 *     allowBackNavigation: true
 * });
 *
 * wizard.on('step-change', (stepIndex) => {
 *     console.log('User navigated to step:', stepIndex);
 * });
 */
export class WizardProgress {
    /**
     * @param {Object} options - Configuration options
     * @param {string} options.container - CSS selector for container element
     * @param {Array} options.steps - Array of step objects { id, label, description? }
     * @param {number} options.currentStep - Zero-based index of current step (default: 0)
     * @param {boolean} options.allowBackNavigation - Allow clicking completed steps (default: true)
     * @param {boolean} options.compact - Use compact mode for modals (default: false)
     */
    constructor(options = {}) {
        // Validate required options
        if (!options.container) {
            throw new Error('WizardProgress: container option is required');
        }

        if (!options.steps || !Array.isArray(options.steps) || options.steps.length < 2) {
            throw new Error('WizardProgress: steps must be an array with at least 2 steps');
        }

        // Store configuration
        this.container = document.querySelector(options.container);
        if (!this.container) {
            throw new Error(`WizardProgress: container element not found: ${options.container}`);
        }

        this.steps = options.steps;
        this.currentStepIndex = options.currentStep || 0;
        this.allowBackNavigation = options.allowBackNavigation !== false; // Default true
        this.compact = options.compact || false;

        // Event listeners
        this.eventListeners = {
            'step-change': []
        };

        // Completed steps tracker (Set for O(1) lookup)
        this.completedSteps = new Set();

        // Initialize
        this.render();
        this.attachEventListeners();
    }

    /**
     * Render the wizard progress indicator
     *
     * BUSINESS LOGIC:
     * Creates the visual progress bar with steps, connectors, and labels
     */
    render() {
        // Set data attributes
        this.container.setAttribute('data-wizard-progress', '');
        if (this.compact) {
            this.container.setAttribute('data-compact', 'true');
        }

        // Add progress line HTML
        const progressLineHTML = `
            <div class="wizard-progress-line">
                <div class="wizard-progress-line-fill" style="width: ${this.getProgressLineWidth()}%"></div>
            </div>
        `;

        // Generate HTML for all steps
        const stepsHTML = this.steps.map((step, index) => {
            const status = this.getStepStatus(index);
            const isClickable = this.allowBackNavigation && this.completedSteps.has(index);

            return `
                <div
                    class="wizard-step is-${status} ${isClickable ? 'is-clickable' : ''}"
                    data-wizard-step
                    data-step-id="${this.escapeHtml(step.id)}"
                    data-step-index="${index}"
                    data-status="${status}"
                    role="button"
                    tabindex="${isClickable ? '0' : '-1'}"
                    aria-label="Step ${index + 1}: ${this.escapeHtml(step.label)}"
                    aria-current="${status === 'current' ? 'step' : 'false'}"
                >
                    <div class="wizard-step-circle">
                        <span class="wizard-step-number">${index + 1}</span>
                        <span class="wizard-step-icon">
                            ${this.getCheckmarkSVG()}
                        </span>
                    </div>

                    <div class="wizard-step-label">
                        ${this.escapeHtml(step.label)}
                    </div>

                    ${step.description ? `
                        <div class="wizard-step-description">
                            ${this.escapeHtml(step.description)}
                        </div>
                    ` : ''}

                    <span class="wizard-sr-only">
                        ${status === 'completed' ? 'Completed' :
                          status === 'current' ? 'Current step' : 'Not completed'}
                    </span>
                </div>
            `;
        }).join('');

        // Add step count indicator
        const stepCountHTML = `
            <div class="wizard-step-count">
                Step ${this.currentStepIndex + 1} of ${this.steps.length}
            </div>
        `;

        // Update container
        this.container.innerHTML = progressLineHTML + stepsHTML + stepCountHTML;
        this.container.classList.add('wizard-progress');
    }

    /**
     * Attach event listeners for step navigation
     */
    attachEventListeners() {
        // Delegate click events to step elements
        this.container.addEventListener('click', (e) => {
            const stepElement = e.target.closest('[data-wizard-step]');
            if (!stepElement) return;

            const stepIndex = parseInt(stepElement.getAttribute('data-step-index'));
            const status = stepElement.getAttribute('data-status');

            // Only allow navigation to completed steps
            if (this.allowBackNavigation && status === 'completed') {
                this.goToStep(stepIndex);
            }
        });

        // Keyboard navigation (Enter/Space on completed steps)
        this.container.addEventListener('keydown', (e) => {
            if (e.key !== 'Enter' && e.key !== ' ') return;

            const stepElement = e.target.closest('[data-wizard-step]');
            if (!stepElement) return;

            const stepIndex = parseInt(stepElement.getAttribute('data-step-index'));
            const status = stepElement.getAttribute('data-status');

            if (this.allowBackNavigation && status === 'completed') {
                e.preventDefault();
                this.goToStep(stepIndex);
            }
        });
    }

    /**
     * Get status for a given step
     *
     * @param {number} index - Step index
     * @returns {string} 'completed' | 'current' | 'pending'
     */
    getStepStatus(index) {
        if (this.completedSteps.has(index)) {
            return 'completed';
        } else if (index === this.currentStepIndex) {
            return 'current';
        } else {
            return 'pending';
        }
    }

    /**
     * Navigate to the next step
     *
     * BUSINESS LOGIC:
     * Marks current step as completed and advances to next
     */
    nextStep() {
        if (this.currentStepIndex >= this.steps.length - 1) {
            console.warn('WizardProgress: Already at last step');
            return;
        }

        // Mark current step as completed
        this.markComplete(this.currentStepIndex);

        // Advance to next step
        this.currentStepIndex++;
        this.render();

        // Emit event with detailed data
        this.emit('step-change', {
            currentStep: this.currentStepIndex,
            progress: this.getProgress(),
            stepId: this.steps[this.currentStepIndex].id
        });
    }

    /**
     * Navigate to the previous step
     *
     * BUSINESS LOGIC:
     * Allows going back without marking incomplete
     */
    previousStep() {
        if (this.currentStepIndex <= 0) {
            console.warn('WizardProgress: Already at first step');
            return;
        }

        this.currentStepIndex--;
        this.render();

        // Emit event with detailed data
        this.emit('step-change', {
            currentStep: this.currentStepIndex,
            progress: this.getProgress(),
            stepId: this.steps[this.currentStepIndex].id
        });
    }

    /**
     * Go to a specific step (by index)
     *
     * @param {number} stepIndex - Target step index
     */
    goToStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.steps.length) {
            console.warn(`WizardProgress: Invalid step index: ${stepIndex}`);
            return;
        }

        // Only allow if going backward to completed step
        if (!this.allowBackNavigation) {
            console.warn('WizardProgress: Back navigation is disabled');
            return;
        }

        if (stepIndex > this.currentStepIndex) {
            console.warn('WizardProgress: Cannot skip forward to incomplete steps');
            return;
        }

        this.currentStepIndex = stepIndex;
        this.render();

        // Emit event with detailed data
        this.emit('step-change', {
            currentStep: this.currentStepIndex,
            progress: this.getProgress(),
            stepId: this.steps[this.currentStepIndex].id
        });
    }

    /**
     * Mark a step as completed
     *
     * @param {number} stepIndex - Step to mark complete
     */
    markComplete(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.steps.length) {
            console.warn(`WizardProgress: Invalid step index: ${stepIndex}`);
            return;
        }

        this.completedSteps.add(stepIndex);
        this.render();
    }

    /**
     * Mark a step as incomplete
     *
     * @param {number} stepIndex - Step to mark incomplete
     */
    markIncomplete(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.steps.length) {
            console.warn(`WizardProgress: Invalid step index: ${stepIndex}`);
            return;
        }

        this.completedSteps.delete(stepIndex);
        this.render();
    }

    /**
     * Show loading state on current step
     */
    showLoading() {
        const currentStepElement = this.container.querySelector(
            `[data-step-index="${this.currentStepIndex}"]`
        );

        if (currentStepElement) {
            currentStepElement.setAttribute('data-loading', 'true');
        }
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        const currentStepElement = this.container.querySelector(
            `[data-step-index="${this.currentStepIndex}"]`
        );

        if (currentStepElement) {
            currentStepElement.removeAttribute('data-loading');
        }
    }

    /**
     * Show error state on current step
     *
     * @param {boolean} hasError - Whether to show error
     */
    setError(hasError) {
        const currentStepElement = this.container.querySelector(
            `[data-step-index="${this.currentStepIndex}"]`
        );

        if (currentStepElement) {
            if (hasError) {
                currentStepElement.setAttribute('data-error', 'true');
            } else {
                currentStepElement.removeAttribute('data-error');
            }
        }
    }

    /**
     * Get checkmark SVG icon
     *
     * @returns {string} SVG markup
     */
    getCheckmarkSVG() {
        return `
            <svg
                data-wizard-step-checkmark
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
            >
                <path
                    d="M16.7071 5.29289C17.0976 5.68342 17.0976 6.31658 16.7071 6.70711L8.70711 14.7071C8.31658 15.0976 7.68342 15.0976 7.29289 14.7071L3.29289 10.7071C2.90237 10.3166 2.90237 9.68342 3.29289 9.29289C3.68342 8.90237 4.31658 8.90237 4.70711 9.29289L8 12.5858L15.2929 5.29289C15.6834 4.90237 16.3166 4.90237 16.7071 5.29289Z"
                    fill="currentColor"
                />
            </svg>
        `;
    }

    /**
     * Escape HTML to prevent XSS
     *
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Register event listener
     *
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }

    /**
     * Emit event to all listeners
     *
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }

    /**
     * Get current step index
     *
     * @returns {number} Current step (zero-based)
     */
    getCurrentStep() {
        return this.currentStepIndex;
    }

    /**
     * Get total number of steps
     *
     * @returns {number} Total steps
     */
    getTotalSteps() {
        return this.steps.length;
    }

    /**
     * Get progress percentage
     *
     * BUSINESS LOGIC:
     * Progress is calculated based on current step position.
     * Step 0 of 5 = 0%, Step 1 of 5 = 20%, Step 2 of 5 = 40%, etc.
     *
     * @returns {number} Progress percentage (0-100)
     */
    getProgress() {
        if (this.steps.length === 0) return 0;
        return Math.round((this.currentStepIndex / this.steps.length) * 100);
    }

    /**
     * Get progress line fill width
     *
     * BUSINESS LOGIC:
     * Progress line shows visual progress between steps.
     * If 2 of 5 steps completed, line should be 40% filled.
     *
     * @returns {number} Width percentage (0-100)
     */
    getProgressLineWidth() {
        if (this.steps.length === 0) return 0;
        if (this.completedSteps.size === 0) return 0;

        // Calculate based on completed steps
        return Math.round((this.completedSteps.size / this.steps.length) * 100);
    }

    /**
     * Check if wizard is complete
     *
     * @returns {boolean} True if all steps completed
     */
    isComplete() {
        return this.completedSteps.size === this.steps.length;
    }

    /**
     * Reset wizard to first step
     */
    reset() {
        this.currentStepIndex = 0;
        this.completedSteps.clear();
        this.render();
    }

    /**
     * Destroy the wizard progress indicator
     *
     * BUSINESS LOGIC:
     * Clean up event listeners and DOM
     */
    destroy() {
        // Remove all event listeners
        this.eventListeners = {
            'step-change': []
        };

        // Clear container
        if (this.container) {
            this.container.innerHTML = '';
            this.container.removeAttribute('data-wizard-progress');
            this.container.removeAttribute('data-compact');
        }
    }
}

/**
 * Initialize wizard progress from HTML data attributes
 *
 * Usage in HTML:
 * <div
 *     id="my-wizard"
 *     data-wizard-progress
 *     data-wizard-steps='[{"id":"step1","label":"Step 1"},{"id":"step2","label":"Step 2"}]'
 *     data-wizard-current="0"
 * ></div>
 *
 * <script>
 * import { initWizardProgressFromElement } from './wizard-progress.js';
 * initWizardProgressFromElement('#my-wizard');
 * </script>
 *
 * @param {string} selector - CSS selector for wizard container
 * @returns {WizardProgress|null} Wizard instance or null if not found
 */
export function initWizardProgressFromElement(selector) {
    const element = document.querySelector(selector);
    if (!element) {
        console.warn(`WizardProgress: Element not found: ${selector}`);
        return null;
    }

    try {
        const stepsData = element.getAttribute('data-wizard-steps');
        const currentStep = parseInt(element.getAttribute('data-wizard-current')) || 0;
        const allowBack = element.getAttribute('data-wizard-allow-back') !== 'false';
        const compact = element.hasAttribute('data-compact');

        if (!stepsData) {
            throw new Error('data-wizard-steps attribute is required');
        }

        const steps = JSON.parse(stepsData);

        return new WizardProgress({
            container: selector,
            steps,
            currentStep,
            allowBackNavigation: allowBack,
            compact
        });

    } catch (error) {
        console.error('Error initializing wizard progress:', error);
        return null;
    }
}

// Auto-initialize on DOM ready if elements exist
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        const wizardElements = document.querySelectorAll('[data-wizard-progress][data-wizard-steps]');
        wizardElements.forEach(element => {
            initWizardProgressFromElement(`#${element.id}`);
        });
    });
}

// Export for testing
if (typeof window !== 'undefined') {
    window.WizardProgress = WizardProgress;
    window.initWizardProgressFromElement = initWizardProgressFromElement;
}
