/**
 * Project Creation Wizard - Controller
 *
 * BUSINESS CONTEXT:
 * Orchestrates the multi-step project creation wizard flow including navigation,
 * validation, track generation, AI suggestions, and final project submission.
 * Coordinates between WizardState, UI components, API services, and user actions.
 *
 * TECHNICAL IMPLEMENTATION:
 * - MVC Controller pattern
 * - Event-driven architecture
 * - Dependency injection for testability
 * - Step-by-step validation flow
 * - Reactive state management
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Wizard orchestration only
 * - Open/Closed: Extensible through events and dependencies
 * - Dependency Inversion: Depends on abstractions (injected dependencies)
 *
 * USAGE:
 * import { WizardController } from './wizard-controller.js';
 *
 * const controller = new WizardController(wizardState, dependencies);
 * controller.openWizard('org-123');
 *
 * @module projects/wizard/wizard-controller
 */
import { mapAudiencesToConfigs } from './audience-mapping.js';
import { generateTrackName, generateTrackDescription } from './track-generator.js';
import { showTrackConfirmationDialog } from './track-confirmation-dialog.js';

/**
 * Wizard Controller Class
 *
 * BUSINESS LOGIC:
 * Manages complete wizard lifecycle:
 * - Opening/closing wizard
 * - Step navigation with validation
 * - AI suggestion generation
 * - Track proposal and confirmation
 * - Final project creation with tracks
 */
export class WizardController {
    /**
     * Initialize wizard controller
     *
     * @param {WizardState} wizardState - Wizard state management instance
     * @param {Object} dependencies - Injected dependencies
     * @param {Object} dependencies.projectAPI - Project API service
     * @param {Function} dependencies.openModal - Modal utility function
     * @param {Function} dependencies.closeModal - Modal utility function
     * @param {Function} dependencies.showNotification - Notification utility function
     * @param {Object} [dependencies.aiAssistant] - AI assistant service (optional)
     */
    constructor(wizardState, dependencies) {
        // Validate required dependencies
        if (!wizardState) {
            throw new Error('WizardController: wizardState is required');
        }

        if (!dependencies || !dependencies.projectAPI) {
            throw new Error('WizardController: projectAPI dependency is required');
        }

        this.state = wizardState;
        this.projectAPI = dependencies.projectAPI;
        this.openModal = dependencies.openModal || this.defaultOpenModal;
        this.closeModal = dependencies.closeModal || this.defaultCloseModal;
        this.showNotification = dependencies.showNotification || this.defaultShowNotification;
        this.aiAssistant = dependencies.aiAssistant || null;

        // Event listeners for cleanup
        this.eventListeners = [];

        this.initializeStateSubscriptions();
    }

    /**
     * Initialize state subscriptions
     *
     * BUSINESS LOGIC:
     * Subscribes to wizard state changes to automatically update UI.
     * Implements reactive programming pattern.
     *
     * @private
     */
    initializeStateSubscriptions() {
        const unsubscribe = this.state.subscribe((newState, oldState) => {
            // Step navigation changed
            if (newState.currentStep !== oldState.currentStep) {
                this.renderStep(newState.currentStep);
            }

            // Loading state changed
            if (newState.loading !== oldState.loading) {
                this.updateLoadingState(newState.loading);
            }

            // Error state changed
            if (newState.error !== oldState.error && newState.error) {
                this.showNotification(newState.error, 'error');
            }
        });

        this.eventListeners.push(unsubscribe);
    }

    // ========================================
    // Wizard Lifecycle
    // ========================================

    /**
     * Open wizard modal
     *
     * BUSINESS LOGIC:
     * Initializes wizard for new project creation:
     * - Resets all state to defaults
     * - Sets organization context
     * - Opens modal
     * - Navigates to step 1
     *
     * @param {string} organizationId - Organization UUID
     */
    openWizard(organizationId) {
        if (!organizationId) {
            console.error('Organization ID is required');
            return;
        }

        console.log('📋 Opening project creation wizard...');

        // Reset state
        this.state.reset();
        this.state.setOrganizationId(organizationId);

        // Open modal
        this.openModal('createProjectModal');

        // Show first step
        this.renderStep(1);

        console.log('✅ Wizard opened');
    }

    /**
     * Close wizard modal
     *
     * BUSINESS LOGIC:
     * Closes wizard and cleans up state.
     * Confirms with user if data is entered.
     */
    closeWizard() {
        const currentState = this.state.getState();

        // Check if user has entered data
        const hasData = currentState.projectName ||
                       currentState.projectDescription ||
                       currentState.targetRoles.length > 0;

        if (hasData) {
            const confirmed = confirm('Are you sure you want to close? All entered data will be lost.');
            if (!confirmed) {
                return;
            }
        }

        this.closeModal('createProjectModal');
        this.state.reset();
        console.log('✅ Wizard closed');
    }

    /**
     * Destroy controller and cleanup
     *
     * BUSINESS LOGIC:
     * Removes all event listeners and cleans up resources.
     */
    destroy() {
        this.eventListeners.forEach(unsubscribe => unsubscribe());
        this.eventListeners = [];
    }

    // ========================================
    // Step Navigation
    // ========================================

    /**
     * Navigate to next step
     *
     * BUSINESS LOGIC:
     * Validates current step before advancing.
     * Step-specific logic:
     * - Step 1 → 2: Validates basic info, triggers AI suggestions
     * - Step 2 → 3: Validates configuration, generates track proposals
     *
     * @returns {Promise<boolean>} True if navigation successful
     */
    async nextStep() {
        const currentStep = this.state.getState().currentStep;
        console.log('📄 Navigating from step:', currentStep);

        if (currentStep === 1) {
            return await this.advanceFromStep1();
        } else if (currentStep === 2) {
            return await this.advanceFromStep2();
        } else if (currentStep === 3) {
            // Step 3 is final - submit project
            return await this.submitProject();
        }

        return false;
    }

    /**
     * Advance from Step 1 to Step 2
     *
     * BUSINESS LOGIC:
     * - Validates Step 1 data (name, slug, description)
     * - Navigates to Step 2
     * - Triggers AI suggestions (non-blocking)
     *
     * @returns {Promise<boolean>}
     * @private
     */
    async advanceFromStep1() {
        // Validate Step 1
        if (!this.state.validateStep1()) {
            this.showNotification('Please fill in all required fields (Name, Slug, and Description)', 'error');
            return false;
        }

        // Navigate to Step 2
        this.state.nextStep();

        // Generate AI suggestions (non-blocking - continue even if it fails)
        if (this.aiAssistant) {
            this.generateAISuggestions().catch(err => {
                console.warn('AI suggestions failed (optional):', err);
                // Continue without AI suggestions
            });
        }

        return true;
    }

    /**
     * Advance from Step 2 to Step 3
     *
     * BUSINESS LOGIC:
     * - Validates Step 2 data (target roles)
     * - Generates track proposals based on selected audiences
     * - Shows track confirmation dialog
     * - On approval: navigates to Step 3
     * - On cancel: stays on Step 2
     *
     * @returns {Promise<boolean>}
     * @private
     */
    async advanceFromStep2() {
        // Validate Step 2
        if (!this.state.validateStep2()) {
            this.showNotification('Please select at least one target audience', 'error');
            return false;
        }

        const currentState = this.state.getState();
        const selectedAudiences = currentState.targetRoles;

        // Generate track proposals
        const proposedTracks = this.generateTrackProposals(selectedAudiences);

        if (proposedTracks.length === 0) {
            // No tracks needed - proceed directly to Step 3
            this.state.nextStep();
            return true;
        }

        console.log(`📋 Proposing ${proposedTracks.length} tracks based on selected audiences`);

        // Show track confirmation dialog
        return new Promise((resolve) => {
            showTrackConfirmationDialog(
                proposedTracks,
                // On approve
                (approvedTracks) => {
                    console.log(`✅ User approved ${approvedTracks.length} tracks`);
                    this.state.setApprovedTracks(approvedTracks);
                    this.state.nextStep();
                    resolve(true);
                },
                // On cancel
                () => {
                    console.log('ℹ️ Track creation cancelled');
                    resolve(false);
                }
            );
        });
    }

    /**
     * Navigate to previous step
     *
     * @returns {boolean} True if navigation successful
     */
    previousStep() {
        return this.state.previousStep();
    }

    /**
     * Navigate to specific step
     *
     * @param {number} stepNumber - Step number (1, 2, or 3)
     */
    goToStep(stepNumber) {
        this.state.setCurrentStep(stepNumber);
    }

    // ========================================
    // Track Generation
    // ========================================

    /**
     * Generate track proposals from selected audiences
     *
     * BUSINESS LOGIC:
     * For each selected audience:
     * 1. Check if predefined mapping exists
     * 2. If yes: Use predefined track configuration
     * 3. If no: Generate track using NLP-based name generator
     *
     * @param {string[]} audiences - Selected audience identifiers
     * @returns {Object[]} Array of proposed track configurations
     * @private
     */
    generateTrackProposals(audiences) {
        if (!audiences || audiences.length === 0) {
            return [];
        }

        // Try to map using predefined configurations
        let tracks = mapAudiencesToConfigs(audiences);

        // For audiences without predefined configs, generate using NLP
        const mappedAudiences = tracks.map(t => t.audience);
        const unmappedAudiences = audiences.filter(a => !mappedAudiences.includes(a));

        if (unmappedAudiences.length > 0) {
            console.log(`🔤 Using NLP to generate ${unmappedAudiences.length} track names...`);

            const nlpTracks = unmappedAudiences.map(audience => ({
                name: generateTrackName(audience),
                description: generateTrackDescription(audience),
                difficulty: 'intermediate',
                skills: [],
                audience: audience
            }));

            tracks = [...tracks, ...nlpTracks];
        }

        return tracks;
    }

    // ========================================
    // AI Integration
    // ========================================

    /**
     * Generate AI suggestions for project
     *
     * BUSINESS LOGIC:
     * Uses RAG-enhanced AI assistant to provide:
     * - Key insights about project scope
     * - Recommended track structure
     * - Specific learning objectives
     *
     * @returns {Promise<void>}
     * @private
     */
    async generateAISuggestions() {
        if (!this.aiAssistant) {
            console.warn('AI assistant not available');
            return;
        }

        console.log('🤖 Generating AI suggestions...');

        this.state.setAISuggestionsLoading(true);

        try {
            const currentState = this.state.getState();

            // Initialize AI assistant context
            await this.aiAssistant.initialize('PROJECT_CREATION', {
                projectName: currentState.projectName,
                projectDescription: currentState.projectDescription,
                targetRoles: currentState.targetRoles,
                organizationId: currentState.organizationId
            });

            // Generate prompt
            const prompt = this.buildAIPrompt(currentState);

            // Send to AI assistant
            const response = await this.aiAssistant.sendMessage(prompt, {
                forceWebSearch: true
            });

            // Parse and store suggestions
            const suggestions = this.parseAIResponse(response);
            this.state.setAISuggestions(suggestions);

            console.log('✅ AI suggestions generated');
        } catch (error) {
            console.error('❌ Error generating AI suggestions:', error);
            this.state.setAISuggestionsLoading(false);
            // Don't throw - AI suggestions are optional
        }
    }

    /**
     * Build AI prompt from current state
     *
     * @param {Object} state - Current wizard state
     * @returns {string} AI prompt
     * @private
     */
    buildAIPrompt(state) {
        return `
I need help creating a training project with the following details:

Project Name: ${state.projectName}
Description: ${state.projectDescription}
Target Roles: ${state.targetRoles.join(', ')}

Please analyze this and provide:
1. Key insights about the project scope
2. Recommended track structure (3-5 tracks)
3. Specific learning objectives (5-8 objectives)

Use web search if needed to research current best practices for these roles.
        `.trim();
    }

    /**
     * Parse AI response into suggestions format
     *
     * @param {Object} response - AI assistant response
     * @returns {Object} Parsed suggestions
     * @private
     */
    parseAIResponse(response) {
        // Use AI suggestions if provided
        if (response.suggestions && response.suggestions.length > 0) {
            return {
                insights: [response.message],
                tracks: response.suggestions
                    .filter(s => s.includes('track'))
                    .map((s, i) => ({
                        name: `Track ${i + 1}`,
                        description: s,
                        duration: '2-3 weeks',
                        modules: 4 + i
                    })),
                objectives: response.suggestions.filter(s => !s.includes('track'))
            };
        }

        // Fallback: return message only
        return {
            insights: [response.message],
            tracks: [],
            objectives: []
        };
    }

    // ========================================
    // Project Submission
    // ========================================

    /**
     * Submit project creation
     *
     * BUSINESS LOGIC:
     * Finalizes project creation:
     * 1. Validates all data
     * 2. Creates project via API
     * 3. Creates approved tracks (if any)
     * 4. Shows success notification
     * 5. Closes wizard
     * 6. Emits project:created event
     *
     * @returns {Promise<boolean>} True if submission successful
     */
    async submitProject() {
        console.log('✅ Submitting project creation...');

        // Validate all steps
        if (!this.state.canSubmit()) {
            this.showNotification('Please complete all required steps', 'error');
            return false;
        }

        this.state.setLoading(true);

        try {
            const projectData = this.state.getProjectData();
            const approvedTracks = this.state.getState().approvedTracks;

            // Create project
            const createdProject = await this.projectAPI.createProject(projectData);

            console.log('✅ Project created:', createdProject);

            // Create tracks if approved
            if (approvedTracks.length > 0) {
                await this.createTracks(createdProject.id, approvedTracks);
            }

            // Success notification
            const message = approvedTracks.length > 0
                ? `Project created successfully with ${approvedTracks.length} tracks`
                : 'Project created successfully';

            this.showNotification(message, 'success');

            // Store created project in state
            this.state.setCreatedProject(createdProject);

            // Close wizard
            this.closeModal('createProjectModal');

            // Emit event for external listeners
            this.emit('project:created', createdProject);

            return true;

        } catch (error) {
            console.error('❌ Error creating project:', error);
            this.state.setError(`Failed to create project: ${error.message || 'Unknown error'}`);
            return false;

        } finally {
            this.state.setLoading(false);
        }
    }

    /**
     * Create tracks for project
     *
     * BUSINESS LOGIC:
     * Creates all approved tracks via API, associating them with the project.
     *
     * @param {string} projectId - Project UUID
     * @param {Object[]} tracks - Approved track configurations
     * @returns {Promise<void>}
     * @private
     */
    async createTracks(projectId, tracks) {
        console.log(`📋 Creating ${tracks.length} tracks for project...`);

        const currentState = this.state.getState();

        for (const track of tracks) {
            const trackData = {
                organization_id: currentState.organizationId,
                project_id: projectId,
                name: track.name,
                description: track.description,
                difficulty: track.difficulty || 'intermediate',
                skills: track.skills || [],
                audience: track.audience
            };

            await this.projectAPI.createTrack(trackData);
            console.log('✅ Created track:', track.name);
        }
    }

    // ========================================
    // UI Rendering
    // ========================================

    /**
     * Render specific wizard step
     *
     * BUSINESS LOGIC:
     * Updates UI to show the specified step and hide others.
     *
     * @param {number} stepNumber - Step number to render
     * @private
     */
    renderStep(stepNumber) {
        console.log(`📄 Rendering step ${stepNumber}`);

        // Hide all steps
        document.querySelectorAll('.project-step').forEach(step => {
            step.classList.remove('active');
        });

        // Show target step
        const targetStep = document.getElementById(`projectStep${stepNumber}`);
        if (targetStep) {
            targetStep.classList.add('active');
            console.log(`✅ Step ${stepNumber} rendered`);
        } else {
            console.error(`❌ projectStep${stepNumber} not found`);
        }

        // Update navigation buttons
        this.updateNavigationButtons(stepNumber);
    }

    /**
     * Update navigation button states
     *
     * @param {number} currentStep - Current step number
     * @private
     */
    updateNavigationButtons(currentStep) {
        const prevBtn = document.getElementById('prevStepBtn');
        const nextBtn = document.getElementById('nextStepBtn');
        const submitBtn = document.getElementById('submitProjectBtn');

        if (prevBtn) {
            prevBtn.disabled = currentStep === 1;
        }

        if (nextBtn) {
            nextBtn.style.display = currentStep < 3 ? 'inline-block' : 'none';
        }

        if (submitBtn) {
            submitBtn.style.display = currentStep === 3 ? 'inline-block' : 'none';
        }
    }

    /**
     * Update loading state in UI
     *
     * @param {boolean} loading - Loading state
     * @private
     */
    updateLoadingState(loading) {
        const spinner = document.getElementById('wizardLoadingSpinner');
        if (spinner) {
            spinner.style.display = loading ? 'block' : 'none';
        }
    }

    // ========================================
    // Event Emitter
    // ========================================

    /**
     * Emit event to external listeners
     *
     * @param {string} event - Event name
     * @param {any} data - Event data
     * @private
     */
    emit(event, data) {
        const customEvent = new CustomEvent(event, {
            detail: data,
            bubbles: true
        });
        document.dispatchEvent(customEvent);
    }

    // ========================================
    // Default Implementations
    // ========================================

    /**
     * EXECUTE DEFAULTOPENMODAL OPERATION
     * PURPOSE: Execute defaultOpenModal operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} modalId - Modalid parameter
     */
    defaultOpenModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
        }
    }

    /**
     * EXECUTE DEFAULTCLOSEMODAL OPERATION
     * PURPOSE: Execute defaultCloseModal operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {string|number} modalId - Modalid parameter
     */
    defaultCloseModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * EXECUTE DEFAULTSHOWNOTIFICATION OPERATION
     * PURPOSE: Execute defaultShowNotification operation
     * WHY: Implements required business logic for system functionality
     *
     * @param {*} message - Message parameter
     * @param {*} type - Type identifier
     */
    defaultShowNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic usage
 * =======================
 * import { WizardController } from './wizard-controller.js';
 * import { WizardState } from './wizard-state.js';
 * import { ProjectAPIService } from '../services/project-api-service.js';
 *
 * const state = new WizardState();
 * const projectAPI = new ProjectAPIService('org-123');
 *
 * const controller = new WizardController(state, {
 *   projectAPI,
 *   openModal,
 *   closeModal,
 *   showNotification
 * });
 *
 * controller.openWizard('org-123');
 *
 *
 * Example 2: With AI assistant
 * ==============================
 * const controller = new WizardController(state, {
 *   projectAPI,
 *   openModal,
 *   closeModal,
 *   showNotification,
 *   aiAssistant: aiAssistantService
 * });
 *
 *
 * Example 3: Listen to events
 * =============================
 * document.addEventListener('project:created', (event) => {
 *   console.log('New project created:', event.detail);
 *   refreshProjectsList();
 * });
 */