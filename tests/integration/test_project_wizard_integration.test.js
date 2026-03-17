/**
 * PROJECT WIZARD INTEGRATION TESTS
 *
 * PURPOSE: End-to-end integration testing for complete project wizard flow
 * WHY: Ensures wizard navigation, validation, AI integration, and form submission work together
 *
 * TEST COVERAGE:
 * - Complete wizard flow from start to finish
 * - Multi-step validation
 * - AI suggestion generation and integration
 * - Form data persistence across steps
 * - Project creation API integration
 * - Error handling across wizard steps
 * - User workflow scenarios
 *
 * TESTING STRATEGY:
 * - Simulate real user interactions
 * - Mock external APIs (AI, backend)
 * - Verify complete workflow integration
 * - Test error recovery scenarios
 * - Validate data flow between components
 *
 * BUSINESS CONTEXT:
 * Organization admins use the project wizard to create new training projects.
 * The wizard guides them through:
 * 1. Basic project details (name, description)
 * 2. AI-powered configuration suggestions (tracks, objectives)
 * 3. Track creation and customization
 *
 * This integration test verifies the entire workflow functions correctly
 * with all components working together.
 */

import {
    nextProjectStep,
    previousProjectStep,
    initializeProjectsManagement,
    showCreateProjectModal,
    submitProjectForm
} from '../../frontend/js/modules/org-admin-projects.js';

// Mock all external dependencies
jest.mock('../../frontend/js/modules/org-admin-api.js', () => ({
    fetchProjects: jest.fn(() => Promise.resolve([
        { id: 'project-1', name: 'Existing Project', status: 'active' }
    ])),
    createProject: jest.fn((orgId, data) => Promise.resolve({
        id: 'new-project-123',
        ...data,
        created_at: new Date().toISOString()
    })),
    updateProject: jest.fn(() => Promise.resolve({})),
    deleteProject: jest.fn(() => Promise.resolve({})),
    fetchMembers: jest.fn(() => Promise.resolve([])),
    addInstructor: jest.fn(() => Promise.resolve({})),
    addStudent: jest.fn(() => Promise.resolve({})),
    removeMember: jest.fn(() => Promise.resolve({}))
}));

jest.mock('../../frontend/js/modules/ai-assistant.js', () => ({
    initializeAIAssistant: jest.fn(),
    sendContextAwareMessage: jest.fn(() => Promise.resolve({
        message: 'AI analysis complete. Here are my recommendations...',
        suggestions: [
            'Track 1: Fundamentals - 2 weeks',
            'Track 2: Intermediate - 3 weeks',
            'Track 3: Advanced - 3 weeks',
            'Objective: Master core concepts',
            'Objective: Build practical skills',
            'Objective: Create portfolio projects'
        ],
        ragSources: [
            { title: 'Similar Project Template', relevance: 0.9 }
        ],
        webSearchUsed: true,
        actions: ['update_track_structure']
    })),
    CONTEXT_TYPES: {
        PROJECT_CREATION: 'PROJECT_CREATION',
        COURSE_GENERATION: 'COURSE_GENERATION',
        TRACK_PLANNING: 'TRACK_PLANNING'
    },
    clearConversationHistory: jest.fn()
}));

jest.mock('../../frontend/js/modules/org-admin-utils.js', () => ({
    escapeHtml: jest.fn((str) => str),
    capitalizeFirst: jest.fn((str) => str.charAt(0).toUpperCase() + str.slice(1)),
    parseCommaSeparated: jest.fn((str) => str ? str.split(',').map(s => s.trim()) : []),
    formatDate: jest.fn((date) => date || 'N/A'),
    formatDuration: jest.fn((weeks) => weeks ? `${weeks} weeks` : 'N/A'),
    openModal: jest.fn(),
    closeModal: jest.fn(),
    showNotification: jest.fn()
}));

describe('Project Wizard Integration Tests', () => {
    let organizationId;

    beforeEach(() => {
        // Reset mocks
        jest.clearAllMocks();

        // Setup complete wizard DOM structure
        document.body.innerHTML = `
            <div id="createProjectModal" class="modal-backdrop" style="display: none;">
                <div class="modal-content">
                    <h2>Create New Project</h2>

                    <!-- Step Indicators -->
                    <div class="wizard-steps">
                        <div class="step active" data-step="1">
                            <span class="step-number">1</span>
                            <span class="step-label">Basic Info</span>
                        </div>
                        <div class="step" data-step="2">
                            <span class="step-number">2</span>
                            <span class="step-label">Configuration</span>
                        </div>
                        <div class="step" data-step="3">
                            <span class="step-number">3</span>
                            <span class="step-label">Tracks</span>
                        </div>
                    </div>

                    <form id="createProjectForm">
                        <!-- Step 1: Basic Info -->
                        <div id="projectStep1" class="project-step active">
                            <input type="text" id="projectName" placeholder="Project Name" />
                            <input type="text" id="projectSlug" placeholder="project-slug" />
                            <textarea id="projectDescription" placeholder="Description"></textarea>
                            <button type="button" onclick="nextProjectStep()">Next</button>
                        </div>

                        <!-- Step 2: Configuration -->
                        <div id="projectStep2" class="project-step">
                            <div id="ragLoadingIndicator" style="display: none;">Loading AI suggestions...</div>
                            <div id="ragSuggestions" style="display: none;">
                                <div id="projectInsights"></div>
                                <div id="recommendedTracks"></div>
                                <div id="suggestedObjectives"></div>
                            </div>
                            <div id="ragContextIndicator" style="display: none;"></div>

                            <select id="projectTargetRoles" multiple>
                                <option value="developer">Developer</option>
                                <option value="designer">Designer</option>
                                <option value="manager">Manager</option>
                            </select>
                            <input type="number" id="projectDuration" placeholder="Duration (weeks)" />
                            <input type="number" id="projectMaxParticipants" placeholder="Max participants" />
                            <input type="date" id="projectStartDate" />
                            <input type="date" id="projectEndDate" />
                            <textarea id="projectObjectives" placeholder="Learning objectives"></textarea>

                            <button type="button" onclick="previousProjectStep()">Back</button>
                            <button type="button" onclick="nextProjectStep()">Next</button>
                        </div>

                        <!-- Step 3: Tracks -->
                        <div id="projectStep3" class="project-step">
                            <div id="tracksContainer">
                                <p>Create tracks for this project</p>
                            </div>
                            <button type="button" onclick="previousProjectStep()">Back</button>
                            <button type="submit">Create Project</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Initialize
        organizationId = 'org-test-123';
        initializeProjectsManagement(organizationId);

        // Mock console
        console.log = jest.fn();
        console.error = jest.fn();
    });

    afterEach(() => {
        jest.restoreAllMocks();
        document.body.innerHTML = '';
    });

    describe('Complete Wizard Flow - Happy Path', () => {
        test('should complete entire wizard flow from start to finish', async () => {
            const { createProject } = require('../../frontend/js/modules/org-admin-api.js');
            const { showNotification } = require('../../frontend/js/modules/org-admin-utils.js');

            // Step 1: Fill basic information
            document.getElementById('projectName').value = 'Web Development Bootcamp';
            document.getElementById('projectSlug').value = 'web-dev-bootcamp';
            document.getElementById('projectDescription').value =
                'Comprehensive web development training program covering HTML, CSS, JavaScript, and React';

            // Navigate to step 2
            nextProjectStep();

            // Verify step 2 is active
            expect(document.getElementById('projectStep2').classList.contains('active')).toBe(true);

            // Wait for AI suggestions to load (async)
            await new Promise(resolve => setTimeout(resolve, 200));

            // Step 2: Fill configuration
            const targetRoles = document.getElementById('projectTargetRoles');
            targetRoles.options[0].selected = true; // developer
            document.getElementById('projectDuration').value = '12';
            document.getElementById('projectMaxParticipants').value = '30';
            document.getElementById('projectStartDate').value = '2025-02-01';
            document.getElementById('projectEndDate').value = '2025-04-30';
            document.getElementById('projectObjectives').value = 'Build web apps, Master React, Deploy projects';

            // Navigate to step 3
            nextProjectStep();

            // Verify step 3 is active
            expect(document.getElementById('projectStep3').classList.contains('active')).toBe(true);

            // Step 3: Submit form
            const form = document.getElementById('createProjectForm');
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });

            await submitProjectForm(submitEvent);

            // Verify project was created with correct data
            expect(createProject).toHaveBeenCalledWith(
                organizationId,
                expect.objectContaining({
                    name: 'Web Development Bootcamp',
                    slug: 'web-dev-bootcamp',
                    description: expect.stringContaining('web development'),
                    duration_weeks: 12,
                    max_participants: 30
                })
            );

            // Verify success notification
            expect(showNotification).toHaveBeenCalledWith(
                'Project created successfully',
                'success'
            );
        });

        test('should persist form data when navigating between steps', () => {
            // Fill step 1
            document.getElementById('projectName').value = 'Test Project';
            document.getElementById('projectSlug').value = 'test-project';
            document.getElementById('projectDescription').value = 'Test description';

            // Navigate forward to step 2
            nextProjectStep();
            expect(document.getElementById('projectStep2').classList.contains('active')).toBe(true);

            // Fill step 2
            document.getElementById('projectDuration').value = '8';
            document.getElementById('projectMaxParticipants').value = '20';

            // Navigate back to step 1
            previousProjectStep();
            expect(document.getElementById('projectStep1').classList.contains('active')).toBe(true);

            // Verify step 1 data is preserved
            expect(document.getElementById('projectName').value).toBe('Test Project');
            expect(document.getElementById('projectSlug').value).toBe('test-project');
            expect(document.getElementById('projectDescription').value).toBe('Test description');

            // Navigate forward again
            nextProjectStep();

            // Verify step 2 data is preserved
            expect(document.getElementById('projectDuration').value).toBe('8');
            expect(document.getElementById('projectMaxParticipants').value).toBe('20');
        });

        test('should generate and display AI suggestions on step 2', async () => {
            const { initializeAIAssistant, sendContextAwareMessage } =
                require('../../frontend/js/modules/ai-assistant.js');

            // Fill step 1
            document.getElementById('projectName').value = 'Python Programming Course';
            document.getElementById('projectSlug').value = 'python-course';
            document.getElementById('projectDescription').value = 'Learn Python from basics to advanced';

            // Navigate to step 2
            nextProjectStep();

            // Wait for async AI call
            await new Promise(resolve => setTimeout(resolve, 200));

            // Verify AI assistant was initialized with correct context
            expect(initializeAIAssistant).toHaveBeenCalledWith(
                'PROJECT_CREATION',
                expect.objectContaining({
                    projectName: 'Python Programming Course',
                    projectDescription: 'Learn Python from basics to advanced',
                    organizationId: organizationId
                })
            );

            // Verify AI message was sent
            expect(sendContextAwareMessage).toHaveBeenCalled();
        });
    });

    describe('Validation and Error Handling', () => {
        test('should prevent advancing from step 1 with incomplete data', () => {
            const { showNotification } = require('../../frontend/js/modules/org-admin-utils.js');

            // Leave fields empty
            document.getElementById('projectName').value = '';
            document.getElementById('projectSlug').value = '';
            document.getElementById('projectDescription').value = '';

            // Try to advance
            nextProjectStep();

            // Verify error notification
            expect(showNotification).toHaveBeenCalledWith(
                expect.stringContaining('required fields'),
                'error'
            );

            // Verify still on step 1
            expect(document.getElementById('projectStep1').classList.contains('active')).toBe(true);
        });

        test('should handle API error during project creation', async () => {
            const { createProject } = require('../../frontend/js/modules/org-admin-api.js');
            const { showNotification } = require('../../frontend/js/modules/org-admin-utils.js');

            // Mock API error
            createProject.mockRejectedValueOnce(new Error('API connection failed'));

            // Fill all steps and submit
            document.getElementById('projectName').value = 'Test Project';
            document.getElementById('projectSlug').value = 'test-project';
            document.getElementById('projectDescription').value = 'Description';

            nextProjectStep();
            nextProjectStep();

            const form = document.getElementById('createProjectForm');
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });

            await submitProjectForm(submitEvent);

            // Verify error was logged (actual error handling in submitProjectForm)
            expect(console.error).toHaveBeenCalled();
        });

        test('should allow navigation back from any step', () => {
            // Navigate through all steps
            document.getElementById('projectName').value = 'Test';
            document.getElementById('projectSlug').value = 'test';
            document.getElementById('projectDescription').value = 'Test';

            nextProjectStep(); // Step 2
            nextProjectStep(); // Step 3

            expect(document.getElementById('projectStep3').classList.contains('active')).toBe(true);

            // Navigate back to step 2
            previousProjectStep();
            expect(document.getElementById('projectStep2').classList.contains('active')).toBe(true);

            // Navigate back to step 1
            previousProjectStep();
            expect(document.getElementById('projectStep1').classList.contains('active')).toBe(true);

            // Try to go back from step 1 (boundary)
            previousProjectStep();
            expect(document.getElementById('projectStep1').classList.contains('active')).toBe(true);
        });
    });

    describe('Step Indicators', () => {
        test('should update step indicators throughout wizard flow', () => {
            // Fill step 1
            document.getElementById('projectName').value = 'Test';
            document.getElementById('projectSlug').value = 'test';
            document.getElementById('projectDescription').value = 'Test';

            const indicators = document.querySelectorAll('.step');

            // Initial state
            expect(indicators[0].classList.contains('active')).toBe(true);
            expect(indicators[1].classList.contains('active')).toBe(false);
            expect(indicators[2].classList.contains('active')).toBe(false);

            // Move to step 2
            nextProjectStep();
            expect(indicators[0].classList.contains('completed')).toBe(true);
            expect(indicators[1].classList.contains('active')).toBe(true);
            expect(indicators[2].classList.contains('active')).toBe(false);

            // Move to step 3
            nextProjectStep();
            expect(indicators[0].classList.contains('completed')).toBe(true);
            expect(indicators[1].classList.contains('completed')).toBe(true);
            expect(indicators[2].classList.contains('active')).toBe(true);

            // Move back to step 2
            previousProjectStep();
            expect(indicators[0].classList.contains('completed')).toBe(true);
            expect(indicators[1].classList.contains('active')).toBe(true);
            expect(indicators[2].classList.contains('active')).toBe(false);
        });
    });

    describe('Modal Integration', () => {
        test('should open wizard modal correctly', () => {
            const { openModal } = require('../../frontend/js/modules/org-admin-utils.js');

            showCreateProjectModal();

            // Verify modal was opened
            expect(openModal).toHaveBeenCalledWith('createProjectModal');

            // Verify wizard is reset to step 1
            expect(document.getElementById('projectStep1').classList.contains('active')).toBe(true);
            expect(document.getElementById('projectStep2').classList.contains('active')).toBe(false);
            expect(document.getElementById('projectStep3').classList.contains('active')).toBe(false);
        });

        test('should close modal after successful project creation', async () => {
            const { closeModal } = require('../../frontend/js/modules/org-admin-utils.js');

            // Complete wizard
            document.getElementById('projectName').value = 'Test';
            document.getElementById('projectSlug').value = 'test';
            document.getElementById('projectDescription').value = 'Test';

            const form = document.getElementById('createProjectForm');
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });

            await submitProjectForm(submitEvent);

            // Verify modal was closed
            expect(closeModal).toHaveBeenCalledWith('projectWizardModal');
        });
    });

    describe('Data Parsing and Transformation', () => {
        test('should parse comma-separated objectives correctly', async () => {
            const { createProject } = require('../../frontend/js/modules/org-admin-api.js');
            const { parseCommaSeparated } = require('../../frontend/js/modules/org-admin-utils.js');

            // Fill form with comma-separated objectives
            document.getElementById('projectName').value = 'Test';
            document.getElementById('projectSlug').value = 'test';
            document.getElementById('projectDescription').value = 'Test';
            document.getElementById('projectObjectives').value = 'Objective 1, Objective 2, Objective 3';

            nextProjectStep();
            nextProjectStep();

            const form = document.getElementById('createProjectForm');
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });

            await submitProjectForm(submitEvent);

            // Verify parseCommaSeparated was called
            expect(parseCommaSeparated).toHaveBeenCalledWith('Objective 1, Objective 2, Objective 3');
        });

        test('should handle empty optional fields gracefully', async () => {
            const { createProject } = require('../../frontend/js/modules/org-admin-api.js');

            // Fill only required fields
            document.getElementById('projectName').value = 'Minimal Project';
            document.getElementById('projectSlug').value = 'minimal';
            document.getElementById('projectDescription').value = 'Min desc';

            nextProjectStep();
            nextProjectStep();

            const form = document.getElementById('createProjectForm');
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });

            await submitProjectForm(submitEvent);

            // Verify project was created with null for optional fields
            expect(createProject).toHaveBeenCalledWith(
                organizationId,
                expect.objectContaining({
                    name: 'Minimal Project',
                    duration_weeks: null,
                    max_participants: null,
                    start_date: null,
                    end_date: null
                })
            );
        });
    });
});
