/**
 * WizardFramework - Reusable Multi-Step Wizard Component
 *
 * BUSINESS CONTEXT:
 * Provides a consistent, reusable framework for all multi-step wizards
 * in the Course Creator Platform (Project Creation, Track Creation, etc.).
 * Eliminates code duplication and ensures consistent UX across all wizards.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Manages wizard state (current step, history)
 * - Handles navigation (next, previous, jump to step)
 * - Integrates optional components (progress, validation, draft)
 * - Provides event callbacks for custom behavior
 * - Graceful degradation when components fail
 *
 * USAGE:
 * ```javascript
 * const wizard = new WizardFramework({
 *     wizardId: 'my-wizard',
 *     steps: [
 *         { id: 'step-1', label: 'Step 1', panelSelector: '#step1' },
 *         { id: 'step-2', label: 'Step 2', panelSelector: '#step2' }
 *     ],
 *     progress: { enabled: true, containerSelector: '#progress' },
 *     validation: { enabled: true, formSelector: '#form' },
 *     draft: { enabled: true, autoSaveInterval: 30000 },
 *     onStepChange: (oldIdx, newIdx) => console.log(`Step ${oldIdx} → ${newIdx}`),
 *     onComplete: (data) => console.log('Wizard complete!', data)
 * });
 *
 * await wizard.initialize();
 * await wizard.nextStep();
 * wizard.previousStep();
 * wizard.reset();
 * ```
 *
 * @module wizard-framework
 * @version 1.0.0
 * @since Wave 5
 */

import { WizardProgress } from './wizard-progress.js';
import { WizardValidator } from './wizard-validation.js';
import { WizardDraft } from './wizard-draft.js';
import { showToast } from './feedback-system.js';

/**
 * WizardFramework class - Core wizard framework
 */
export class WizardFramework {
    /**
     * Create a new wizard instance
     *
     * @param {Object} options - Wizard configuration options
     * @param {string} options.wizardId - Unique identifier for this wizard
     * @param {Array<Object>} options.steps - Array of step definitions
     * @param {Object} [options.progress] - Progress indicator configuration
     * @param {Object} [options.validation] - Validation configuration
     * @param {Object} [options.draft] - Draft system configuration
     * @param {Function} [options.onStepChange] - Callback when step changes
     * @param {Function} [options.onValidationError] - Callback on validation error
     * @param {Function} [options.onDraftSaved] - Callback when draft saved
     * @param {Function} [options.onComplete] - Callback when wizard completes
     * @param {Function} [options.onError] - Callback on error
     */
    constructor(options = {}) {
        // Validate required options
        if (!options.wizardId) {
            throw new Error('wizardId is required');
        }

        if (!options.steps || !Array.isArray(options.steps) || options.steps.length === 0) {
            throw new Error('At least one step is required');
        }

        // Core configuration
        this.wizardId = options.wizardId;
        this.steps = options.steps;
        this.totalSteps = this.steps.length;

        // State
        this.currentStepIndex = 0;
        this.stepHistory = [0];
        this._isDirty = false;
        this._isInitialized = false;
        this._isDestroyed = false;

        // Component options
        this.progressOptions = options.progress || {};
        this.validationOptions = options.validation || {};
        this.draftOptions = options.draft || {};

        // Component instances (initialized later)
        this.progressComponent = null;
        this.validatorComponent = null;
        this.draftComponent = null;

        // Event callbacks
        this.onStepChange = options.onStepChange || null;
        this.onValidationError = options.onValidationError || null;
        this.onDraftSaved = options.onDraftSaved || null;
        this.onComplete = options.onComplete || null;
        this.onError = options.onError || null;

        console.log(`✅ WizardFramework created: ${this.wizardId} (${this.totalSteps} steps)`);
    }

    /**
     * Initialize the wizard and all components
     *
     * BUSINESS CONTEXT:
     * Sets up the wizard UI, initializes optional components,
     * and shows the first step. Must be called before navigation.
     *
     * @returns {Promise<boolean>} True if initialization successful
     */
    async initialize() {
        // Allow re-initialization after destroy
        if (this._isDestroyed) {
            console.log(`Re-initializing previously destroyed wizard: ${this.wizardId}`);
            this._isDestroyed = false;
        }

        if (this._isInitialized) {
            console.warn(`Wizard ${this.wizardId} already initialized`);
            return true;
        }

        try {
            console.log(`🚀 Initializing wizard: ${this.wizardId}`);

            // Initialize optional components
            await this._initializeComponents();

            // Set up form change listeners for dirty tracking
            this._setupFormListeners();

            // Show first step
            this.currentStepIndex = 0;
            this.stepHistory = [0];
            this._showStep(0);

            this._isInitialized = true;
            console.log(`✅ Wizard ${this.wizardId} initialized successfully`);
            return true;
        } catch (error) {
            console.error(`Error initializing wizard ${this.wizardId}:`, error);
            this._callErrorCallback({
                type: 'initialization_error',
                message: error.message,
                error
            });
            return false;
        }
    }

    /**
     * Initialize optional components (progress, validator, draft) with graceful degradation
     * @private
     */
    async _initializeComponents() {
        let successCount = 0;
        let failureCount = 0;

        // 1. Initialize Progress Indicator (non-critical)
        if (this.progressOptions.enabled) {
            try {
                this.progressComponent = new WizardProgress({
                    container: this.progressOptions.containerSelector,
                    steps: this.steps.map(s => ({ id: s.id, label: s.label })),
                    currentStep: 0,
                    allowBackNavigation: this.progressOptions.allowBackNavigation !== false,
                    onStepChange: (newStepIndex) => {
                        return this._handleProgressClick(newStepIndex);
                    }
                });
                console.log('✅ WizardProgress initialized');
                successCount++;
            } catch (error) {
                console.warn('⚠️ WizardProgress failed to initialize (wizard will work without it):', error);
                this.progressComponent = null;
                failureCount++;
            }
        }

        // 2. Initialize Validator (non-critical)
        if (this.validationOptions.enabled) {
            try {
                this.validatorComponent = new WizardValidator({
                    form: this.validationOptions.formSelector,
                    validateOnBlur: this.validationOptions.validateOnBlur !== false,
                    validateOnSubmit: this.validationOptions.validateOnSubmit !== false,
                    showErrorsInline: this.validationOptions.showErrorsInline !== false
                });
                console.log('✅ WizardValidator initialized');
                successCount++;
            } catch (error) {
                console.warn('⚠️ WizardValidator failed to initialize (validation will be handled by browser):', error);
                this.validatorComponent = null;
                failureCount++;
            }
        }

        // 3. Initialize Draft System (non-critical)
        if (this.draftOptions.enabled) {
            try {
                this.draftComponent = new WizardDraft({
                    wizardId: this.wizardId,
                    autoSaveInterval: this.draftOptions.autoSaveInterval || 30000,
                    storage: this.draftOptions.storage || 'localStorage',
                    formSelector: this.draftOptions.formSelector || null,
                    onSave: (draft) => {
                        console.log('Draft saved:', draft);
                        if (this.onDraftSaved) {
                            this.onDraftSaved(draft);
                        }
                    },
                    onLoad: (draft) => {
                        console.log('Draft loaded:', draft);
                    }
                });

                this.draftComponent.startAutoSave();
                console.log('✅ WizardDraft initialized with auto-save');
                successCount++;

                // Check for existing drafts
                this._checkForExistingDrafts();
            } catch (error) {
                console.warn('⚠️ WizardDraft failed to initialize (manual save will still work):', error);
                this.draftComponent = null;
                failureCount++;
            }
        }

        // Report initialization results
        console.log(`📊 Component initialization: ${successCount} succeeded, ${failureCount} failed`);

        if (successCount === 0 && (this.progressOptions.enabled || this.validationOptions.enabled || this.draftOptions.enabled)) {
            console.warn('⚠️ Wizard running in basic mode (all enhancements unavailable)');
            showToast('Wizard initialized in basic mode', 'warning', 4000);
        } else if (failureCount > 0) {
            console.log('⚠️ Wizard running in degraded mode with partial enhancements');
            showToast(`Wizard initialized (${successCount}/${successCount + failureCount} enhancements active)`, 'info', 3000);
        }
    }

    /**
     * Check for existing drafts and prompt user to restore
     * @private
     */
    _checkForExistingDrafts() {
        if (!this.draftComponent) return;

        const existingDraft = this.draftComponent.checkForDraft();
        if (existingDraft) {
            const lastSaved = new Date(existingDraft.timestamp);
            const message = `You have an unsaved draft from ${lastSaved.toLocaleString()}. Would you like to restore it?`;

            if (confirm(message)) {
                this.draftComponent.loadDraft();
            }
        }
    }

    /**
     * Set up form change listeners for dirty state tracking
     * @private
     */
    _setupFormListeners() {
        // Find form element from validation or draft options
        const formSelector = this.validationOptions.formSelector ||
                           (this.draftOptions.enabled ? this.draftOptions.formSelector : null);

        // If no form selector specified, try to find any form in the document
        let form = null;
        if (formSelector) {
            form = document.querySelector(formSelector);
        } else {
            // Try to find the first form element
            form = document.querySelector('form');
        }

        if (!form) {
            console.warn('Form not found for dirty tracking');
            return;
        }

        // Mark as dirty on any form change
        const markDirty = () => {
            this._isDirty = true;
        };

        form.addEventListener('input', markDirty);
        form.addEventListener('change', markDirty);

        // Store listeners for cleanup
        this._formListeners = { form, markDirty };
    }

    /**
     * Navigate to next step
     *
     * BUSINESS CONTEXT:
     * Advances user to the next step after validating current step data.
     * Saves draft before advancing to prevent data loss.
     *
     * @returns {Promise<boolean>} True if navigation successful
     */
    async nextStep() {
        try {
            // Check if already at last step
            if (this.currentStepIndex >= this.totalSteps - 1) {
                console.warn('Already at last wizard step');
                showToast('Already at final step', 'info', 2000);

                // Call onComplete callback if at final step
                if (this.onComplete) {
                    this.onComplete({
                        wizardId: this.wizardId,
                        completedSteps: this.totalSteps
                    });
                }

                return false;
            }

            // Validate current step before proceeding
            if (this.validatorComponent) {
                try {
                    const isValid = await this.validatorComponent.validateAll();
                    if (!isValid) {
                        showToast('Please fix validation errors before proceeding', 'error', 4000);
                        if (this.onValidationError) {
                            this.onValidationError({ step: this.currentStepIndex });
                        }
                        return false;
                    }
                } catch (validationError) {
                    console.error('Validation error:', validationError);
                    // Continue anyway (graceful degradation)
                    showToast('Validation unavailable, proceeding with caution', 'warning', 3000);
                }
            }

            // Save draft before navigating
            if (this.draftComponent) {
                try {
                    await this.draftComponent.saveDraft();
                } catch (draftError) {
                    console.error('Draft save error:', draftError);
                    // Continue anyway (draft saving is non-critical)
                    showToast('Could not save draft, but continuing navigation', 'warning', 3000);
                }
            }

            // Calculate next step index
            const oldStepIndex = this.currentStepIndex;
            const nextStepIndex = oldStepIndex + 1;

            // Show next step panel
            const stepShown = this._showStep(nextStepIndex);
            if (!stepShown) {
                showToast('Failed to show next step panel', 'error');
                return false;
            }

            // Update state
            this.currentStepIndex = nextStepIndex;
            this.stepHistory.push(nextStepIndex);

            // Update progress indicator
            if (this.progressComponent) {
                try {
                    this.progressComponent.nextStep();
                } catch (progressError) {
                    console.error('Progress indicator error:', progressError);
                    // Continue anyway (progress indicator is non-critical)
                }
            }

            // Call onStepChange callback
            if (this.onStepChange) {
                this.onStepChange(oldStepIndex, nextStepIndex);
            }

            // If we just reached the final step, call onComplete
            if (nextStepIndex === this.totalSteps - 1 && this.onComplete) {
                this.onComplete({
                    wizardId: this.wizardId,
                    completedSteps: this.totalSteps
                });
            }

            console.log(`✅ Navigated to wizard step ${nextStepIndex + 1} of ${this.totalSteps}`);
            showToast(`Step ${nextStepIndex + 1} of ${this.totalSteps}`, 'success', 2000);

            return true;
        } catch (error) {
            console.error('Error navigating wizard step:', error);
            showToast('Failed to proceed to next step', 'error');
            this._callErrorCallback({
                type: 'navigation_error',
                message: 'Failed to proceed to next step',
                error
            });
            return false;
        }
    }

    /**
     * Navigate to previous step
     *
     * BUSINESS CONTEXT:
     * Allows users to navigate back to review/modify previous inputs.
     * Does NOT validate (users should be able to go back freely).
     *
     * @returns {boolean} True if navigation successful
     */
    previousStep() {
        try {
            // Check if already at first step
            if (this.currentStepIndex <= 0) {
                console.warn('Already at first wizard step');
                showToast('Already at first step', 'info', 2000);
                return false;
            }

            // Calculate previous step index
            const oldStepIndex = this.currentStepIndex;
            const previousStepIndex = oldStepIndex - 1;

            // Show previous step panel
            const stepShown = this._showStep(previousStepIndex);
            if (!stepShown) {
                showToast('Failed to show previous step panel', 'error');
                return false;
            }

            // Update state
            this.currentStepIndex = previousStepIndex;
            this.stepHistory.push(previousStepIndex);

            // Update progress indicator
            if (this.progressComponent) {
                try {
                    this.progressComponent.previousStep();
                } catch (progressError) {
                    console.error('Progress indicator error:', progressError);
                    // Continue anyway (progress indicator is non-critical)
                }
            }

            // Call onStepChange callback
            if (this.onStepChange) {
                this.onStepChange(oldStepIndex, previousStepIndex);
            }

            console.log(`✅ Navigated back to wizard step ${previousStepIndex + 1} of ${this.totalSteps}`);
            showToast(`Returned to step ${previousStepIndex + 1}`, 'info', 2000);
            return true;
        } catch (error) {
            console.error('Error navigating back:', error);
            showToast('Failed to navigate to previous step', 'error');
            this._callErrorCallback({
                type: 'navigation_error',
                message: 'Failed to navigate to previous step',
                error
            });
            return false;
        }
    }

    /**
     * Navigate to specific step by index
     *
     * @param {number} stepIndex - Zero-based step index
     * @returns {boolean} True if navigation successful
     */
    goToStep(stepIndex) {
        try {
            // Validate step index
            if (stepIndex < 0 || stepIndex >= this.totalSteps) {
                console.error(`Invalid step index: ${stepIndex}. Must be 0-${this.totalSteps - 1}`);
                return false;
            }

            const oldStepIndex = this.currentStepIndex;

            // Show requested step
            const stepShown = this._showStep(stepIndex);
            if (!stepShown) {
                return false;
            }

            // Update state
            this.currentStepIndex = stepIndex;
            this.stepHistory.push(stepIndex);

            // Update progress indicator
            if (this.progressComponent) {
                try {
                    this.progressComponent.goToStep(stepIndex);
                } catch (progressError) {
                    console.error('Progress indicator error:', progressError);
                }
            }

            // Call onStepChange callback
            if (this.onStepChange) {
                this.onStepChange(oldStepIndex, stepIndex);
            }

            console.log(`✅ Jumped to wizard step ${stepIndex + 1} of ${this.totalSteps}`);
            return true;
        } catch (error) {
            console.error('Error navigating to step:', error);
            this._callErrorCallback({
                type: 'navigation_error',
                message: `Failed to navigate to step ${stepIndex}`,
                error
            });
            return false;
        }
    }

    /**
     * Show specific wizard step panel and hide others
     *
     * @private
     * @param {number} stepIndex - Zero-based index of step to show
     * @returns {boolean} True if step was shown successfully
     */
    _showStep(stepIndex) {
        try {
            // Validate step index
            if (stepIndex < 0 || stepIndex >= this.totalSteps) {
                console.error(`Invalid step index: ${stepIndex}. Must be 0-${this.totalSteps - 1}`);
                return false;
            }

            // Hide all steps
            for (let i = 0; i < this.totalSteps; i++) {
                const step = this.steps[i];
                const panel = document.querySelector(step.panelSelector);

                if (panel) {
                    panel.classList.remove('active');
                    panel.style.display = 'none';
                } else if (i === stepIndex) {
                    // Only error if it's the step we're trying to show
                    console.error(`Step panel not found: ${step.panelSelector}`);
                    this._callErrorCallback({
                        type: 'navigation_error',
                        message: `Step panel not found: ${step.panelSelector}`
                    });
                    return false;
                }
            }

            // Show requested step
            const targetStep = this.steps[stepIndex];
            const targetPanel = document.querySelector(targetStep.panelSelector);

            if (!targetPanel) {
                console.error(`Step panel not found: ${targetStep.panelSelector}`);
                return false;
            }

            targetPanel.classList.add('active');
            targetPanel.style.display = 'block';

            console.log(`✅ Showing wizard step ${stepIndex + 1} of ${this.totalSteps}`);
            return true;
        } catch (error) {
            console.error('Error showing wizard step:', error);
            showToast(`Failed to navigate to step ${stepIndex + 1}`, 'error');
            return false;
        }
    }

    /**
     * Handle click on progress indicator step
     *
     * @private
     * @param {number} newStepIndex - Step index clicked
     * @returns {boolean} True if navigation allowed
     */
    _handleProgressClick(newStepIndex) {
        // For now, allow backward navigation only
        if (newStepIndex < this.currentStepIndex) {
            return this.goToStep(newStepIndex);
        }

        // Forward navigation requires validation
        if (newStepIndex > this.currentStepIndex) {
            showToast('Please use Next button to advance', 'info', 2000);
            return false;
        }

        return true;
    }

    /**
     * Reset wizard to initial state
     *
     * BUSINESS CONTEXT:
     * Cleans up wizard state after completion or cancellation.
     * Ensures wizard starts fresh for next use.
     *
     * @returns {boolean} True if reset successful
     */
    reset() {
        try {
            console.log(`🔄 Resetting wizard: ${this.wizardId}`);

            // Reset state
            this.currentStepIndex = 0;
            this.stepHistory = [0];
            this._isDirty = false;

            // Show first step
            this._showStep(0);

            // Clear form if exists
            const formSelector = this.validationOptions.formSelector;
            if (formSelector) {
                const form = document.querySelector(formSelector);
                if (form) {
                    form.reset();
                }
            }

            // Stop auto-save timer
            if (this.draftComponent) {
                try {
                    this.draftComponent.stopAutoSave();
                } catch (error) {
                    console.warn('Could not stop auto-save:', error);
                }
            }

            // Clear validation errors
            if (this.validatorComponent) {
                try {
                    this.validatorComponent.clearAllErrors();
                } catch (error) {
                    console.warn('Could not clear validation errors:', error);
                }
            }

            // Reset progress indicator
            if (this.progressComponent) {
                try {
                    this.progressComponent.reset();
                } catch (error) {
                    console.warn('Could not reset progress indicator:', error);
                }
            }

            console.log('✅ Wizard reset complete');
            return true;
        } catch (error) {
            console.error('Error resetting wizard:', error);
            return false;
        }
    }

    /**
     * Destroy wizard and cleanup resources
     *
     * BUSINESS CONTEXT:
     * Cleanup method for when wizard is no longer needed.
     * Stops timers, removes listeners, frees memory.
     */
    destroy() {
        console.log(`🗑️ Destroying wizard: ${this.wizardId}`);

        // Stop auto-save timer
        if (this.draftComponent) {
            try {
                this.draftComponent.stopAutoSave();
            } catch (error) {
                console.warn('Error stopping auto-save:', error);
            }
        }

        // Remove form listeners
        if (this._formListeners) {
            const { form, markDirty } = this._formListeners;
            form.removeEventListener('input', markDirty);
            form.removeEventListener('change', markDirty);
            this._formListeners = null;
        }

        // Clear component references
        this.progressComponent = null;
        this.validatorComponent = null;
        this.draftComponent = null;

        // Mark as destroyed
        this._isDestroyed = true;
        this._isInitialized = false;

        console.log('✅ Wizard destroyed');
    }

    /**
     * Call error callback if defined
     * @private
     */
    _callErrorCallback(error) {
        if (this.onError) {
            this.onError(error);
        }
    }

    // Getter methods

    /**
     * Get current step index
     * @returns {number} Current step index (0-based)
     */
    getCurrentStep() {
        return this.currentStepIndex;
    }

    /**
     * Get total number of steps
     * @returns {number} Total steps
     */
    getTotalSteps() {
        return this.totalSteps;
    }

    /**
     * Get step navigation history
     * @returns {Array<number>} Array of step indices visited
     */
    getStepHistory() {
        return [...this.stepHistory];
    }

    /**
     * Check if wizard has unsaved changes
     * @returns {boolean} True if dirty
     */
    isDirty() {
        return this._isDirty;
    }

    /**
     * Check if wizard has been destroyed
     * @returns {boolean} True if destroyed
     */
    isDestroyed() {
        return this._isDestroyed;
    }

    /**
     * Check if wizard has progress indicator
     * @returns {boolean} True if progress indicator enabled
     */
    hasProgressIndicator() {
        return this.progressComponent !== null;
    }

    /**
     * Check if wizard has validator
     * @returns {boolean} True if validator enabled
     */
    hasValidator() {
        return this.validatorComponent !== null;
    }

    /**
     * Check if wizard has draft system
     * @returns {boolean} True if draft system enabled
     */
    hasDraftSystem() {
        return this.draftComponent !== null;
    }
}

// Export for testing and module usage
export default WizardFramework;
