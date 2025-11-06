/**
 * Project Creation Wizard - State Management
 *
 * BUSINESS CONTEXT:
 * Manages the state of the multi-step project creation wizard including
 * form data, current step, validation status, and proposed tracks. Provides
 * reactive state updates via Observer pattern.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Centralized state management for wizard flow
 * - Observer pattern for reactive UI updates
 * - Immutable state updates (new state object on each change)
 * - Step-by-step data collection and validation
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Wizard state management only
 * - Open/Closed: Extensible through subscriptions
 * - Liskov Substitution: Consistent state interface
 *
 * USAGE:
 * import { WizardState } from './wizard-state.js';
 *
 * const state = new WizardState();
 * state.subscribe((newState, oldState) => {
 *   console.log('Wizard state changed:', newState);
 * });
 * state.setCurrentStep(2);
 *
 * @module projects/wizard/wizard-state
 */
export class WizardState {
    /**
     * Initialize wizard state
     *
     * BUSINESS CONTEXT:
     * Sets up initial wizard state with default values for all fields.
     * All data starts empty, wizard begins at step 1.
     */
    constructor() {
        this.state = {
            // Navigation
            currentStep: 1,
            totalSteps: 3,

            // Step 1: Basic Info
            projectName: '',
            projectSlug: '',
            projectDescription: '',
            projectObjectives: [],

            // Step 2: Configuration
            durationWeeks: null,
            maxParticipants: null,
            targetRoles: [],
            projectType: 'single_location', // 'single_location' | 'multi_location'
            locations: [],

            // Step 3: Tracks
            proposedTracks: [],
            approvedTracks: [],

            // Validation
            step1Valid: false,
            step2Valid: false,
            step3Valid: false,

            // UI States
            loading: false,
            error: null,
            aiSuggestionsLoading: false,
            aiSuggestions: null,

            // Metadata
            organizationId: null,
            createdProject: null
        };

        this.subscribers = [];
    }

    /**
     * Get current state snapshot
     *
     * @returns {Object} Current state (immutable copy)
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Update state with new values
     *
     * BUSINESS LOGIC:
     * Creates new state object with updates and notifies all subscribers.
     * Maintains immutability by spreading old state and overwriting with updates.
     *
     * @param {Object} updates - Partial state updates
     */
    setState(updates) {
        const oldState = { ...this.state };
        this.state = {
            ...this.state,
            ...updates
        };
        this.notify(oldState, this.state);
    }

    /**
     * Subscribe to state changes
     *
     * TECHNICAL IMPLEMENTATION:
     * Observer pattern - subscribers are notified whenever state changes.
     *
     * @param {Function} callback - Called with (newState, oldState) on changes
     * @returns {Function} Unsubscribe function
     */
    subscribe(callback) {
        if (typeof callback !== 'function') {
            throw new Error('Subscriber callback must be a function');
        }

        this.subscribers.push(callback);

        // Return unsubscribe function
        return () => {
            const index = this.subscribers.indexOf(callback);
            if (index > -1) {
                this.subscribers.splice(index, 1);
            }
        };
    }

    /**
     * Notify all subscribers of state change
     *
     * @param {Object} oldState - Previous state
     * @param {Object} newState - New state
     * @private
     */
    notify(oldState, newState) {
        this.subscribers.forEach(callback => {
            try {
                callback(newState, oldState);
            } catch (error) {
                console.error('Error in state subscriber:', error);
            }
        });
    }

    // ========================================
    // Navigation Methods
    // ========================================

    /**
     * Set current wizard step
     *
     * @param {number} stepNumber - Step number (1, 2, or 3)
     */
    setCurrentStep(stepNumber) {
        if (stepNumber < 1 || stepNumber > this.state.totalSteps) {
            console.warn(`Invalid step number: ${stepNumber}`);
            return;
        }

        this.setState({ currentStep: stepNumber });
    }

    /**
     * Navigate to next step
     *
     * @returns {boolean} True if navigation successful
     */
    nextStep() {
        if (this.state.currentStep < this.state.totalSteps) {
            this.setCurrentStep(this.state.currentStep + 1);
            return true;
        }
        return false;
    }

    /**
     * Navigate to previous step
     *
     * @returns {boolean} True if navigation successful
     */
    previousStep() {
        if (this.state.currentStep > 1) {
            this.setCurrentStep(this.state.currentStep - 1);
            return true;
        }
        return false;
    }

    /**
     * Check if on first step
     *
     * @returns {boolean}
     */
    isFirstStep() {
        return this.state.currentStep === 1;
    }

    /**
     * Check if on last step
     *
     * @returns {boolean}
     */
    isLastStep() {
        return this.state.currentStep === this.state.totalSteps;
    }

    // ========================================
    // Step 1: Basic Info Methods
    // ========================================

    /**
     * Set project name
     *
     * @param {string} name - Project name
     */
    setProjectName(name) {
        this.setState({ projectName: name || '' });
    }

    /**
     * Set project slug
     *
     * @param {string} slug - URL-friendly project identifier
     */
    setProjectSlug(slug) {
        this.setState({ projectSlug: slug || '' });
    }

    /**
     * Set project description
     *
     * @param {string} description - Project description
     */
    setProjectDescription(description) {
        this.setState({ projectDescription: description || '' });
    }

    /**
     * Set project objectives
     *
     * @param {string[]} objectives - Array of learning objectives
     */
    setProjectObjectives(objectives) {
        this.setState({
            projectObjectives: Array.isArray(objectives) ? objectives : []
        });
    }

    /**
     * Update Step 1 data (batch)
     *
     * @param {Object} data - Step 1 data { name, slug, description, objectives }
     */
    updateStep1Data(data) {
        const updates = {};
        if (data.name !== undefined) updates.projectName = data.name;
        if (data.slug !== undefined) updates.projectSlug = data.slug;
        if (data.description !== undefined) updates.projectDescription = data.description;
        if (data.objectives !== undefined) updates.projectObjectives = data.objectives;

        this.setState(updates);
    }

    /**
     * Validate Step 1 data
     *
     * BUSINESS LOGIC:
     * Step 1 is valid if name, slug, and description are all provided.
     *
     * @returns {boolean} True if Step 1 is valid
     */
    validateStep1() {
        const valid = !!(
            this.state.projectName &&
            this.state.projectSlug &&
            this.state.projectDescription
        );

        this.setState({ step1Valid: valid });
        return valid;
    }

    // ========================================
    // Step 2: Configuration Methods
    // ========================================

    /**
     * Set duration in weeks
     *
     * @param {number} weeks - Duration in weeks
     */
    setDurationWeeks(weeks) {
        this.setState({ durationWeeks: weeks });
    }

    /**
     * Set maximum participants
     *
     * @param {number} max - Maximum number of participants
     */
    setMaxParticipants(max) {
        this.setState({ maxParticipants: max });
    }

    /**
     * Set target roles (audiences)
     *
     * @param {string[]} roles - Array of role identifiers
     */
    setTargetRoles(roles) {
        this.setState({
            targetRoles: Array.isArray(roles) ? roles : []
        });
    }

    /**
     * Set project type
     *
     * @param {string} type - 'single_location' | 'multi_location'
     */
    setProjectType(type) {
        this.setState({ projectType: type });
    }

    /**
     * Set locations (for multi-locations projects)
     *
     * @param {Object[]} locations - Array of locations configurations
     */
    setLocations(locations) {
        this.setState({
            locations: Array.isArray(locations) ? locations : []
        });
    }

    /**
     * Add locations
     *
     * @param {Object} locations - Locations configuration
     */
    addLocation(locations) {
        const locations = [...this.state.locations, locations];
        this.setState({ locations });
    }

    /**
     * Remove locations
     *
     * @param {number} index - Locations index to remove
     */
    removeLocation(index) {
        const locations = this.state.locations.filter((_, i) => i !== index);
        this.setState({ locations });
    }

    /**
     * Update Step 2 data (batch)
     *
     * @param {Object} data - Step 2 data
     */
    updateStep2Data(data) {
        const updates = {};
        if (data.durationWeeks !== undefined) updates.durationWeeks = data.durationWeeks;
        if (data.maxParticipants !== undefined) updates.maxParticipants = data.maxParticipants;
        if (data.targetRoles !== undefined) updates.targetRoles = data.targetRoles;
        if (data.projectType !== undefined) updates.projectType = data.projectType;
        if (data.locations !== undefined) updates.locations = data.locations;

        this.setState(updates);
    }

    /**
     * Validate Step 2 data
     *
     * BUSINESS LOGIC:
     * Step 2 is valid if:
     * - At least one target role is selected
     * - If multi-locations, at least one locations is defined
     *
     * @returns {boolean} True if Step 2 is valid
     */
    validateStep2() {
        const hasRoles = this.state.targetRoles.length > 0;
        const locationsValid = this.state.projectType !== 'multi_location' ||
                           this.state.locations.length > 0;

        const valid = hasRoles && locationsValid;
        this.setState({ step2Valid: valid });
        return valid;
    }

    // ========================================
    // Step 3: Tracks Methods
    // ========================================

    /**
     * Set proposed tracks
     *
     * @param {Object[]} tracks - Array of proposed track configurations
     */
    setProposedTracks(tracks) {
        this.setState({
            proposedTracks: Array.isArray(tracks) ? tracks : []
        });
    }

    /**
     * Set approved tracks
     *
     * @param {Object[]} tracks - Array of approved track configurations
     */
    setApprovedTracks(tracks) {
        this.setState({
            approvedTracks: Array.isArray(tracks) ? tracks : []
        });
    }

    /**
     * Validate Step 3 data
     *
     * BUSINESS LOGIC:
     * Step 3 is always valid (tracks are optional).
     *
     * @returns {boolean} Always true
     */
    validateStep3() {
        this.setState({ step3Valid: true });
        return true;
    }

    // ========================================
    // AI Suggestions Methods
    // ========================================

    /**
     * Set AI suggestions loading state
     *
     * @param {boolean} loading
     */
    setAISuggestionsLoading(loading) {
        this.setState({ aiSuggestionsLoading: loading });
    }

    /**
     * Set AI suggestions
     *
     * @param {Object} suggestions - AI-generated suggestions
     */
    setAISuggestions(suggestions) {
        this.setState({
            aiSuggestions: suggestions,
            aiSuggestionsLoading: false
        });
    }

    /**
     * Clear AI suggestions
     */
    clearAISuggestions() {
        this.setState({
            aiSuggestions: null,
            aiSuggestionsLoading: false
        });
    }

    // ========================================
    // General State Methods
    // ========================================

    /**
     * Set organization ID
     *
     * @param {string} organizationId - Organization UUID
     */
    setOrganizationId(organizationId) {
        this.setState({ organizationId });
    }

    /**
     * Set loading state
     *
     * @param {boolean} loading
     */
    setLoading(loading) {
        this.setState({ loading });
    }

    /**
     * Set error
     *
     * @param {string|null} error - Error message or null
     */
    setError(error) {
        this.setState({ error });
    }

    /**
     * Clear error
     */
    clearError() {
        this.setState({ error: null });
    }

    /**
     * Set created project
     *
     * @param {Object} project - Created project object from API
     */
    setCreatedProject(project) {
        this.setState({ createdProject: project });
    }

    /**
     * Reset wizard to initial state
     *
     * BUSINESS LOGIC:
     * Clears all wizard data and returns to step 1.
     * Used when wizard is closed or completed.
     */
    reset() {
        this.setState({
            currentStep: 1,
            projectName: '',
            projectSlug: '',
            projectDescription: '',
            projectObjectives: [],
            durationWeeks: null,
            maxParticipants: null,
            targetRoles: [],
            projectType: 'single_location',
            locations: [],
            proposedTracks: [],
            approvedTracks: [],
            step1Valid: false,
            step2Valid: false,
            step3Valid: false,
            loading: false,
            error: null,
            aiSuggestionsLoading: false,
            aiSuggestions: null,
            createdProject: null
        });
    }

    /**
     * Get complete project data for API submission
     *
     * BUSINESS LOGIC:
     * Aggregates all wizard data into a single object ready for API submission.
     *
     * @returns {Object} Complete project data
     */
    getProjectData() {
        return {
            name: this.state.projectName,
            slug: this.state.projectSlug,
            description: this.state.projectDescription,
            objectives: this.state.projectObjectives,
            duration_weeks: this.state.durationWeeks,
            max_participants: this.state.maxParticipants,
            target_roles: this.state.targetRoles,
            project_type: this.state.projectType,
            locations: this.state.locations,
            organization_id: this.state.organizationId
        };
    }

    /**
     * Check if wizard can be submitted
     *
     * BUSINESS LOGIC:
     * Wizard can be submitted if all steps are valid.
     *
     * @returns {boolean} True if wizard is ready for submission
     */
    canSubmit() {
        return this.state.step1Valid &&
               this.state.step2Valid &&
               this.state.step3Valid &&
               !this.state.loading;
    }
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic usage
 * =======================
 * import { WizardState } from './wizard-state.js';
 *
 * const state = new WizardState();
 * state.setProjectName('Python Bootcamp');
 * state.setProjectSlug('python-bootcamp');
 * console.log(state.getState().projectName); // "Python Bootcamp"
 *
 *
 * Example 2: Subscribe to changes
 * ================================
 * import { WizardState } from './wizard-state.js';
 *
 * const state = new WizardState();
 * const unsubscribe = state.subscribe((newState, oldState) => {
 *   if (newState.currentStep !== oldState.currentStep) {
 *     console.log(`Step changed: ${oldState.currentStep} → ${newState.currentStep}`);
 *   }
 * });
 *
 * state.nextStep(); // Logs: "Step changed: 1 → 2"
 * unsubscribe(); // Stop receiving updates
 *
 *
 * Example 3: Validation workflow
 * ================================
 * import { WizardState } from './wizard-state.js';
 *
 * const state = new WizardState();
 * state.setProjectName('Python Bootcamp');
 * state.setProjectSlug('python-bootcamp');
 * state.setProjectDescription('Learn Python from scratch');
 *
 * if (state.validateStep1()) {
 *   state.nextStep();
 * }
 *
 *
 * Example 4: Get project data for submission
 * ============================================
 * import { WizardState } from './wizard-state.js';
 *
 * const state = new WizardState();
 * // ... set all fields ...
 *
 * if (state.canSubmit()) {
 *   const projectData = state.getProjectData();
 *   await createProject(projectData);
 * }
 */