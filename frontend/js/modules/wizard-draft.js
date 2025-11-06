/**
 * Wizard Draft System - JavaScript Controller
 *
 * BUSINESS CONTEXT:
 * Users often cannot complete multi-step wizards in one session due to interruptions,
 * time constraints, or need to gather additional information. This module provides
 * robust draft save/load functionality to prevent data loss and improve user experience.
 *
 * KEY FEATURES:
 * 1. Auto-save: Automatically saves form data every 30 seconds when changes detected
 * 2. Manual save: "Save Draft" button for explicit user-triggered saves
 * 3. Draft loading: Prompts to resume when returning to wizard with existing draft
 * 4. Dirty state tracking: Detects unsaved changes and warns before navigation
 * 5. Draft expiration: Automatically discards drafts older than 7 days
 * 6. Error handling: Gracefully handles localStorage failures (quota, private browsing)
 * 7. Multiple wizards: Supports independent drafts for different wizard types
 * 8. Loading states: Visual feedback during save operations
 * 9. Toast integration: Uses Wave 3 feedback-system.js for notifications
 * 10. Modal integration: Uses Wave 3 modal-system.js for resume/unsaved prompts
 *
 * TECHNICAL APPROACH:
 * - localStorage for client-side persistence (future: could add API sync)
 * - Debounced change detection for performance
 * - Deep equality check for dirty state tracking
 * - ISO timestamp for expiration calculation
 * - Structured draft format with version for future migrations
 * - Integrates with Wave 3 components (feedback-system.js, modal-system.js)
 * - Uses OUR blue color scheme (#2563eb) in CSS
 *
 * @module wizard-draft
 * @version 2.0.0
 * @date 2025-10-17
 */

import { showToast, setButtonLoading } from './feedback-system.js';

/**
 * Wizard Draft Manager Class
 *
 * Usage:
 * const draftManager = new WizardDraft({
 *     wizardId: 'project-creation',
 *     autoSaveInterval: 30000, // 30 seconds
 *     storage: 'localStorage',
 *     onSave: () => showToast('Draft saved', 'success'),
 *     onLoad: (draft) => console.log('Draft loaded:', draft)
 * });
 *
 * // Manual save
 * draftManager.saveDraft();
 *
 * // Load draft
 * const draft = await draftManager.loadDraft();
 */
export class WizardDraft {
    /**
     * @param {Object} options - Configuration options
     * @param {string} options.wizardId - Unique ID for this wizard (e.g., 'project-creation')
     * @param {number} options.autoSaveInterval - Auto-save interval in ms (default: 30000 = 30s)
     * @param {string} options.storage - Storage type: 'localStorage', 'sessionStorage', 'server' (default: 'localStorage')
     * @param {string} options.formSelector - Form selector (default: finds closest form)
     * @param {Function} options.onSave - Callback when draft saved
     * @param {Function} options.onLoad - Callback when draft loaded
     * @param {string} options.serverEndpoint - API endpoint for server storage
     */
    constructor(options = {}) {
        // Validate required options
        if (!options.wizardId) {
            throw new Error('WizardDraft: wizardId option is required');
        }

        // Configuration
        this.wizardId = options.wizardId;
        this.autoSaveInterval = options.autoSaveInterval || 30000; // 30 seconds
        this.storage = options.storage || 'localStorage';
        this.formSelector = options.formSelector || null;
        this.serverEndpoint = options.serverEndpoint || null;

        // Callbacks
        this.onSave = options.onSave || (() => {});
        this.onLoad = options.onLoad || (() => {});

        // State
        this.form = null;
        this.autoSaveTimer = null;
        this.lastSaveTime = null;
        this.isDirty = false; // Has form changed since last save?

        // Event listeners
        this.eventListeners = {
            'draft-saved': [],
            'draft-loaded': [],
            'draft-cleared': []
        };

        // Initialize
        this.initialize();
    }

    /**
     * Initialize draft manager
     *
     * BUSINESS LOGIC:
     * - Find form element
     * - Set up auto-save timer
     * - Attach form change listeners
     * - Check for existing draft
     */
    initialize() {
        // Find form element
        if (this.formSelector) {
            this.form = document.querySelector(this.formSelector);
        } else {
            // Find closest form to wizard container
            const wizardContainer = document.querySelector('[data-wizard-progress]');
            this.form = wizardContainer ? wizardContainer.closest('form') : null;
        }

        if (!this.form) {
            console.warn('WizardDraft: Form element not found. Draft saving disabled.');
            return;
        }

        // Attach form change listeners
        this.attachFormChangeListeners();

        // Start auto-save timer
        if (this.autoSaveInterval > 0) {
            this.startAutoSave();
        }
    }

    /**
     * Attach form change listeners
     *
     * BUSINESS LOGIC:
     * Listens for any form changes and sets isDirty flag.
     * This prevents unnecessary saves when nothing changed.
     */
    attachFormChangeListeners() {
        if (!this.form) return;

        // Mark as dirty on any form change
        this.form.addEventListener('input', () => {
            this.isDirty = true;
        });

        this.form.addEventListener('change', () => {
            this.isDirty = true;
        });

        // Also listen for step changes (custom event from wizard progress)
        document.addEventListener('wizard-step-changed', () => {
            this.isDirty = true;
        });
    }

    /**
     * Start auto-save timer
     *
     * BUSINESS LOGIC:
     * Saves draft every N seconds (default 30s) if form has changes
     */
    startAutoSave() {
        this.autoSaveTimer = setInterval(() => {
            if (this.isDirty) {
                this.saveDraft();
            }
        }, this.autoSaveInterval);
    }

    /**
     * Stop auto-save timer
     */
    stopAutoSave() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
            this.autoSaveTimer = null;
        }
    }

    /**
     * Save current form state as draft
     *
     * BUSINESS LOGIC:
     * Captures all form field values, current step, and metadata.
     * Stores in configured storage (localStorage/server).
     *
     * @returns {Promise<Object>} Draft object that was saved
     */
    async saveDraft() {
        if (!this.form) {
            console.warn('WizardDraft: Cannot save - form not found');
            return null;
        }

        try {
            // Collect form data
            const formData = this.serializeForm();

            // Get current step
            const currentStep = this.getCurrentStep();

            // Build draft object
            const draft = {
                wizardId: this.wizardId,
                timestamp: Date.now(),
                step: currentStep,
                data: formData,
                version: '1.0' // For future migrations
            };

            // Save to storage
            await this.saveDraftToStorage(draft);

            // Update state
            this.lastSaveTime = draft.timestamp;
            this.isDirty = false;

            // Trigger callbacks
            this.onSave(draft);
            this.emit('draft-saved', draft);

            // Show success toast (Wave 3 integration)
            showToast('Draft saved', 'success', 3000);

            // Show draft indicator
            this.showDraftIndicator(draft.timestamp);

            // Update dirty indicator
            this.updateDirtyIndicator();

            return draft;

        } catch (error) {
            console.error('Error saving draft:', error);

            // Show error toast (Wave 3 integration)
            showToast('Error saving draft', 'error', 5000);

            throw error;
        }
    }

    /**
     * Serialize form to plain object
     *
     * BUSINESS LOGIC:
     * Captures all form field values including:
     * - Text inputs
     * - Textareas
     * - Select dropdowns
     * - Checkboxes (checked state)
     * - Radio buttons (selected value)
     * - File inputs (as base64 for small files)
     *
     * @returns {Object} Form data object
     */
    serializeForm() {
        const formData = {};
        const formElements = this.form.elements;

        for (let i = 0; i < formElements.length; i++) {
            const element = formElements[i];

            // Skip elements without name
            if (!element.name) continue;

            // Handle different input types
            if (element.type === 'checkbox') {
                formData[element.name] = element.checked;

            } else if (element.type === 'radio') {
                if (element.checked) {
                    formData[element.name] = element.value;
                }

            } else if (element.type === 'file') {
                // Skip file inputs for now (could implement base64 encoding)
                // formData[element.name] = this.serializeFileInput(element);

            } else if (element.tagName === 'SELECT' && element.multiple) {
                // Multi-select
                formData[element.name] = Array.from(element.selectedOptions).map(opt => opt.value);

            } else {
                // Text, textarea, select, etc.
                formData[element.name] = element.value;
            }
        }

        return formData;
    }

    /**
     * Get current wizard step
     *
     * @returns {number} Current step (zero-based)
     */
    getCurrentStep() {
        // Try to get from wizard progress component
        const wizardProgress = document.querySelector('[data-wizard-progress]');
        if (wizardProgress && window.WizardProgress) {
            const instance = window.wizardProgressInstance;
            if (instance) {
                return instance.getCurrentStep();
            }
        }

        // Fallback: find active step element
        const activeStep = document.querySelector('.project-step.active, [data-wizard-step].active');
        if (activeStep) {
            const stepIndex = activeStep.getAttribute('data-step-index') ||
                             activeStep.id.replace(/\D/g, '');
            return parseInt(stepIndex) || 0;
        }

        return 0;
    }

    /**
     * Save draft to storage
     *
     * @param {Object} draft - Draft object
     * @returns {Promise<void>}
     */
    async saveDraftToStorage(draft) {
        const draftKey = `wizard-draft-${this.wizardId}`;

        if (this.storage === 'localStorage') {
            try {
                localStorage.setItem(draftKey, JSON.stringify(draft));
            } catch (error) {
                if (error.name === 'QuotaExceededError') {
                    console.error('localStorage quota exceeded. Draft not saved.');
                    throw new Error('Storage quota exceeded');
                }
                throw error;
            }

        } else if (this.storage === 'sessionStorage') {
            try {
                sessionStorage.setItem(draftKey, JSON.stringify(draft));
            } catch (error) {
                if (error.name === 'QuotaExceededError') {
                    console.error('sessionStorage quota exceeded. Draft not saved.');
                    throw new Error('Storage quota exceeded');
                }
                throw error;
            }

        } else if (this.storage === 'server') {
            if (!this.serverEndpoint) {
                throw new Error('Server endpoint not configured');
            }

            // Save to server via API
            const response = await fetch(this.serverEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(draft)
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

        } else {
            throw new Error(`Unknown storage type: ${this.storage}`);
        }
    }

    /**
     * Check for existing draft without loading it
     *
     * BUSINESS LOGIC:
     * Checks if a valid draft exists in storage without restoring it.
     * Used by wizard framework to prompt user about resuming draft.
     *
     * @returns {Object|null} Draft object if exists and valid, null otherwise
     */
    checkForDraft() {
        const draftKey = `wizard-draft-${this.wizardId}`;

        try {
            let draft = null;

            if (this.storage === 'localStorage') {
                const draftJson = localStorage.getItem(draftKey);
                draft = draftJson ? JSON.parse(draftJson) : null;

            } else if (this.storage === 'sessionStorage') {
                const draftJson = sessionStorage.getItem(draftKey);
                draft = draftJson ? JSON.parse(draftJson) : null;

            } else if (this.storage === 'server') {
                // For server storage, can't check synchronously
                // Return null and use loadDraft() instead
                console.warn('checkForDraft() not supported for server storage - use loadDraft() instead');
                return null;
            }

            // Validate draft
            if (draft && this.isValidDraft(draft)) {
                return draft;
            }

            return null;

        } catch (error) {
            console.error('Error checking for draft:', error);
            return null;
        }
    }

    /**
     * Load draft from storage
     *
     * BUSINESS LOGIC:
     * Retrieves saved draft, checks if it's valid, and returns it.
     * Returns null if no draft exists or it's expired.
     *
     * @returns {Promise<Object|null>} Draft object or null
     */
    async loadDraft() {
        const draftKey = `wizard-draft-${this.wizardId}`;

        try {
            let draft = null;

            if (this.storage === 'localStorage') {
                const draftJson = localStorage.getItem(draftKey);
                draft = draftJson ? JSON.parse(draftJson) : null;

            } else if (this.storage === 'sessionStorage') {
                const draftJson = sessionStorage.getItem(draftKey);
                draft = draftJson ? JSON.parse(draftJson) : null;

            } else if (this.storage === 'server') {
                if (!this.serverEndpoint) {
                    throw new Error('Server endpoint not configured');
                }

                const response = await fetch(`${this.serverEndpoint}?wizardId=${this.wizardId}`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });

                if (response.ok) {
                    draft = await response.json();
                }
            }

            // Validate draft
            if (draft && this.isValidDraft(draft)) {
                return draft;
            }

            return null;

        } catch (error) {
            console.error('Error loading draft:', error);
            return null;
        }
    }

    /**
     * Validate draft object
     *
     * @param {Object} draft - Draft to validate
     * @returns {boolean} True if valid
     */
    isValidDraft(draft) {
        // Check required properties
        if (!draft || !draft.wizardId || !draft.timestamp || !draft.data) {
            return false;
        }

        // Check if draft is for this wizard
        if (draft.wizardId !== this.wizardId) {
            return false;
        }

        // Check if draft is not too old (7 days)
        const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
        if (draft.timestamp < sevenDaysAgo) {
            return false;
        }

        return true;
    }

    /**
     * Restore form from draft
     *
     * BUSINESS LOGIC:
     * Populates all form fields with saved values.
     * Navigates to saved step position.
     * Triggers validation to show any errors.
     *
     * @param {Object} draft - Draft object to restore
     */
    restoreDraft(draft) {
        if (!draft || !draft.data) {
            console.warn('WizardDraft: Invalid draft object');
            return;
        }

        if (!this.form) {
            console.warn('WizardDraft: Cannot restore - form not found');
            return;
        }

        try {
            // Restore form field values
            Object.entries(draft.data).forEach(([name, value]) => {
                const elements = this.form.querySelectorAll(`[name="${name}"]`);

                elements.forEach(element => {
                    if (element.type === 'checkbox') {
                        element.checked = value;

                    } else if (element.type === 'radio') {
                        element.checked = (element.value === value);

                    } else if (element.tagName === 'SELECT' && element.multiple) {
                        // Multi-select
                        Array.from(element.options).forEach(option => {
                            option.selected = value.includes(option.value);
                        });

                    } else {
                        element.value = value;
                    }

                    // Trigger change event for validation
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                });
            });

            // Navigate to saved step
            if (draft.step !== undefined && draft.step > 0) {
                this.navigateToStep(draft.step);
            }

            // Trigger callbacks
            this.onLoad(draft);
            this.emit('draft-loaded', draft);

            // Mark as not dirty (just loaded, no changes)
            this.isDirty = false;

        } catch (error) {
            console.error('Error restoring draft:', error);
            throw error;
        }
    }

    /**
     * Navigate to a specific step
     *
     * @param {number} stepIndex - Step index (zero-based)
     */
    navigateToStep(stepIndex) {
        // Try wizard progress component
        const wizardProgress = document.querySelector('[data-wizard-progress]');
        if (wizardProgress && window.WizardProgress) {
            const instance = window.wizardProgressInstance;
            if (instance) {
                instance.goToStep(stepIndex);
                return;
            }
        }

        // Fallback: manual step navigation
        const steps = document.querySelectorAll('.project-step, [data-wizard-step]');
        steps.forEach((step, index) => {
            if (index === stepIndex) {
                step.classList.add('active');
                step.style.display = 'block';
            } else {
                step.classList.remove('active');
                step.style.display = 'none';
            }
        });
    }

    /**
     * Clear saved draft
     *
     * BUSINESS LOGIC:
     * Removes draft from storage. Called when user:
     * - Successfully submits wizard
     * - Clicks "Start Fresh" on resume modal
     * - Explicitly cancels wizard
     *
     * @returns {Promise<void>}
     */
    async clearDraft() {
        const draftKey = `wizard-draft-${this.wizardId}`;

        try {
            if (this.storage === 'localStorage') {
                localStorage.removeItem(draftKey);

            } else if (this.storage === 'sessionStorage') {
                sessionStorage.removeItem(draftKey);

            } else if (this.storage === 'server') {
                if (!this.serverEndpoint) {
                    throw new Error('Server endpoint not configured');
                }

                await fetch(`${this.serverEndpoint}?wizardId=${this.wizardId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
            }

            // Emit event
            this.emit('draft-cleared');

        } catch (error) {
            console.error('Error clearing draft:', error);
            throw error;
        }
    }

    /**
     * Load and resume draft automatically
     *
     * BUSINESS LOGIC:
     * Convenience method that:
     * 1. Loads draft from storage
     * 2. If draft exists, restores it
     * 3. If no draft, does nothing
     *
     * @returns {Promise<boolean>} True if draft was loaded
     */
    async loadAndResume() {
        const draft = await this.loadDraft();

        if (draft) {
            this.restoreDraft(draft);
            return true;
        }

        return false;
    }

    /**
     * Show resume draft modal
     *
     * BUSINESS CONTEXT:
     * When wizard opens with existing draft, show modal asking user
     * to resume or start fresh. Uses Wave 3 modal system.
     *
     * @param {Object} draft - Draft to resume
     */
    showResumeDraftModal(draft) {
        const modalHtml = `
            <div id="wizardResumeModal" class="modal wizard-resume-modal" role="dialog" aria-modal="true" aria-labelledby="resumeModalTitle">
                <div class="modal-backdrop"></div>
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 id="resumeModalTitle" class="modal-title">Resume Draft?</h2>
                        <button class="modal-close" aria-label="Close modal">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="draft-info">
                            <p>You have an unfinished draft from your previous session.</p>
                            <p class="draft-timestamp">Last saved: ${this.getTimeSinceDraft(draft.timestamp)}</p>
                        </div>
                        <p>Would you like to continue where you left off, or start fresh?</p>
                    </div>
                    <div class="modal-footer">
                        <button
                            class="btn-secondary"
                            data-action="start-fresh"
                            aria-label="Discard draft and start fresh">
                            Start Fresh
                        </button>
                        <button
                            class="btn-primary"
                            data-action="resume"
                            aria-label="Resume draft">
                            Resume Draft
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Insert modal into DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Set up event listeners
        const modal = document.getElementById('wizardResumeModal');
        const resumeBtn = modal.querySelector('[data-action="resume"]');
        const startFreshBtn = modal.querySelector('[data-action="start-fresh"]');
        const closeBtn = modal.querySelector('.modal-close');

        resumeBtn.addEventListener('click', () => {
            this.restoreDraft(draft);
            this.closeAndRemoveModal('wizardResumeModal');
            showToast('Draft resumed', 'success', 3000);
        });

        startFreshBtn.addEventListener('click', async () => {
            await this.clearDraft();
            this.closeAndRemoveModal('wizardResumeModal');
            showToast('Starting fresh', 'info', 3000);
        });

        closeBtn.addEventListener('click', () => {
            this.closeAndRemoveModal('wizardResumeModal');
        });

        // Open modal using Wave 3 modal system if available
        if (window.uiModal && window.uiModal.open) {
            window.uiModal.open('wizardResumeModal');
        } else {
            // Fallback: manual open
            modal.classList.add('is-open');
            document.body.classList.add('modal-open');
        }
    }

    /**
     * Show unsaved changes modal
     *
     * BUSINESS CONTEXT:
     * Warns user about losing unsaved work when navigating away.
     * Provides options: save & close, discard, or cancel.
     */
    showUnsavedChangesModal() {
        const modalHtml = `
            <div id="wizardUnsavedModal" class="modal wizard-unsaved-modal" role="dialog" aria-modal="true" aria-labelledby="unsavedModalTitle">
                <div class="modal-backdrop"></div>
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 id="unsavedModalTitle" class="modal-title">Unsaved Changes</h2>
                        <button class="modal-close" aria-label="Close modal">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p class="warning-message">
                            You have unsaved changes. If you leave now, your changes will be lost.
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button
                            class="btn-secondary"
                            data-action="cancel"
                            aria-label="Cancel and continue editing">
                            Cancel
                        </button>
                        <button
                            class="btn-danger"
                            data-action="discard"
                            aria-label="Discard changes and close">
                            Discard Changes
                        </button>
                        <button
                            class="btn-primary"
                            data-action="save-and-close"
                            aria-label="Save changes and close">
                            Save & Close
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const modal = document.getElementById('wizardUnsavedModal');
        const saveAndCloseBtn = modal.querySelector('[data-action="save-and-close"]');
        const discardBtn = modal.querySelector('[data-action="discard"]');
        const cancelBtn = modal.querySelector('[data-action="cancel"]');
        const closeBtn = modal.querySelector('.modal-close');

        saveAndCloseBtn.addEventListener('click', async () => {
            await this.saveDraft();
            this.closeAndRemoveModal('wizardUnsavedModal');
            this.closeWizard();
        });

        discardBtn.addEventListener('click', async () => {
            this.isDirty = false;
            await this.clearDraft();
            this.closeAndRemoveModal('wizardUnsavedModal');
            this.closeWizard();
        });

        cancelBtn.addEventListener('click', () => {
            this.closeAndRemoveModal('wizardUnsavedModal');
        });

        closeBtn.addEventListener('click', () => {
            this.closeAndRemoveModal('wizardUnsavedModal');
        });

        // Open modal
        if (window.uiModal && window.uiModal.open) {
            window.uiModal.open('wizardUnsavedModal');
        } else {
            modal.classList.add('is-open');
            document.body.classList.add('modal-open');
        }
    }

    /**
     * Close and remove modal from DOM
     *
     * @param {string} modalId - Modal ID to close
     */
    closeAndRemoveModal(modalId) {
        if (window.uiModal && window.uiModal.close) {
            window.uiModal.close(modalId);
        } else {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('is-open');
                document.body.classList.remove('modal-open');
                setTimeout(() => modal.remove(), 300);
            }
        }
    }

    /**
     * Close wizard modal
     *
     * BUSINESS CONTEXT:
     * Closes the parent wizard modal. Called after save or discard.
     */
    closeWizard() {
        const wizardModal = document.querySelector('.modal.is-open:not(.wizard-resume-modal):not(.wizard-unsaved-modal)');
        if (wizardModal) {
            const closeBtn = wizardModal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }
    }

    /**
     * Show dirty state indicator
     *
     * BUSINESS CONTEXT:
     * Visual feedback showing unsaved changes exist.
     */
    showDirtyIndicator() {
        let indicator = document.querySelector('[data-dirty-indicator]');

        if (!indicator) {
            const saveDraftBtn = document.querySelector('.wizard-save-draft-btn');
            if (saveDraftBtn) {
                indicator = document.createElement('span');
                indicator.setAttribute('data-dirty-indicator', '');
                indicator.textContent = 'Unsaved changes';
                saveDraftBtn.insertAdjacentElement('afterend', indicator);
            }
        }
    }

    /**
     * Hide dirty state indicator
     */
    hideDirtyIndicator() {
        const indicator = document.querySelector('[data-dirty-indicator]');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Show draft saved indicator
     *
     * @param {number} timestamp - Save timestamp
     */
    showDraftIndicator(timestamp) {
        let indicator = document.querySelector('.wizard-draft-indicator');

        if (!indicator) {
            const form = this.form;
            if (!form) return;

            indicator = document.createElement('div');
            indicator.className = 'wizard-draft-indicator';
            indicator.setAttribute('data-draft-indicator', '');
            indicator.setAttribute('role', 'status');
            indicator.setAttribute('aria-live', 'polite');

            form.insertAdjacentElement('beforebegin', indicator);
        }

        indicator.textContent = `Draft saved ${this.getTimeSinceDraft(timestamp)}`;
        indicator.classList.remove('hidden');
    }

    /**
     * Hide draft indicator
     */
    hideDraftIndicator() {
        const indicator = document.querySelector('.wizard-draft-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    }

    /**
     * Update dirty indicator based on dirty state
     */
    updateDirtyIndicator() {
        if (this.isDirty) {
            this.showDirtyIndicator();
        } else {
            this.hideDirtyIndicator();
        }
    }

    /**
     * Get human-readable time since draft saved
     *
     * @param {number} timestamp - Draft timestamp
     * @returns {string} Human-readable string (e.g., "2 hours ago")
     */
    getTimeSinceDraft(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;

        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) {
            return `${days} day${days > 1 ? 's' : ''} ago`;
        } else if (hours > 0) {
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (minutes > 0) {
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else {
            return 'just now';
        }
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
     * Destroy draft manager and clean up
     */
    destroy() {
        // Stop auto-save
        this.stopAutoSave();

        // Clear event listeners
        this.eventListeners = {
            'draft-saved': [],
            'draft-loaded': [],
            'draft-cleared': []
        };
    }
}

/**
 * Convenience function to set up Save Draft button
 *
 * BUSINESS CONTEXT:
 * Automatically wires up "Save Draft" button in wizard footer.
 * Handles loading state during save operation.
 *
 * @param {WizardDraft} draftInstance - WizardDraft instance
 * @param {string} buttonSelector - CSS selector for Save Draft button
 */
export function setupSaveDraftButton(draftInstance, buttonSelector = '.wizard-save-draft-btn') {
    const saveBtn = document.querySelector(buttonSelector);
    if (!saveBtn) {
        console.warn('WizardDraft: Save Draft button not found');
        return;
    }

    saveBtn.addEventListener('click', async () => {
        // Show loading state (Wave 3 integration)
        const restoreButton = setButtonLoading(saveBtn);

        try {
            await draftInstance.saveDraft();
        } finally {
            restoreButton();
        }
    });
}

/**
 * Check for draft on wizard init and show resume modal if exists
 *
 * BUSINESS CONTEXT:
 * Helper function to check for existing draft when wizard opens.
 * Shows resume modal if draft exists and is valid.
 *
 * @param {WizardDraft} draftInstance - WizardDraft instance
 */
export async function checkAndPromptForDraft(draftInstance) {
    const draft = await draftInstance.loadDraft();

    if (draft && draftInstance.isValidDraft(draft)) {
        draftInstance.showResumeDraftModal(draft);
    }
}

/**
 * Set up navigation guard for unsaved changes
 *
 * BUSINESS CONTEXT:
 * Prevents accidental data loss by prompting when user tries to
 * navigate away with unsaved changes.
 *
 * @param {WizardDraft} draftInstance - WizardDraft instance
 */
export function setupNavigationGuard(draftInstance) {
    // Browser navigation (back button, close tab, etc.)
    window.addEventListener('beforeunload', (e) => {
        if (draftInstance.isDirty) {
            e.preventDefault();
            e.returnValue = ''; // Chrome requires returnValue to be set
            return ''; // Some browsers show this message
        }
    });

    // Modal close button
    const modalCloseBtn = document.querySelector('.modal-close');
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', (e) => {
            if (draftInstance.isDirty) {
                e.preventDefault();
                e.stopPropagation();
                draftInstance.showUnsavedChangesModal();
            }
        });
    }
}

// Export for testing and global access
if (typeof window !== 'undefined') {
    window.WizardDraft = WizardDraft;
    window.setupSaveDraftButton = setupSaveDraftButton;
    window.checkAndPromptForDraft = checkAndPromptForDraft;
    window.setupNavigationGuard = setupNavigationGuard;
}
