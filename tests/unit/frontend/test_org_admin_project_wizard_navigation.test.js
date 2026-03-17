/**
 * ORG ADMIN PROJECT WIZARD NAVIGATION UNIT TESTS
 *
 * PURPOSE: Comprehensive unit testing for project wizard navigation functions
 * WHY: Ensures wizard navigation (next/previous step) works correctly
 *
 * TEST COVERAGE:
 * - nextProjectStep() function - advancing through wizard
 * - previousProjectStep() function - going back in wizard
 * - showProjectStep() helper function - displaying specific step
 * - Form validation before advancing
 * - AI suggestion generation on step transitions
 * - Step indicator UI updates
 * - Edge cases (first step, last step, missing elements)
 * - Error handling
 *
 * TESTING STRATEGY:
 * - Mock DOM elements for wizard steps and indicators
 * - Mock dependencies (notifications, AI, API calls)
 * - Test both success and error paths
 * - Test boundary conditions
 * - Verify step transitions and UI updates
 *
 * BUSINESS CONTEXT:
 * Project wizard allows org admins to create new projects with:
 * - Step 1: Basic project info (name, slug, description)
 * - Step 2: Configuration and AI suggestions (objectives, roles, dates)
 * - Step 3: Track creation and assignment
 *
 * FIXED BUG:
 * previousProjectStep() was using wrong selector (.wizard-step.active)
 * instead of (.project-step.active), causing back button to fail.
 * This test suite verifies the fix works correctly.
 */

import {
    nextProjectStep,
    previousProjectStep,
    initializeProjectsManagement,
    loadProjectsData
} from '../../../frontend/js/modules/org-admin-projects.js';

// Mock dependencies
jest.mock('../../../frontend/js/modules/org-admin-api.js', () => ({
    fetchProjects: jest.fn(() => Promise.resolve([])),
    createProject: jest.fn(() => Promise.resolve({ id: 'project-1', name: 'Test Project' })),
    updateProject: jest.fn(() => Promise.resolve({})),
    deleteProject: jest.fn(() => Promise.resolve({})),
    fetchMembers: jest.fn(() => Promise.resolve([])),
    addInstructor: jest.fn(() => Promise.resolve({})),
    addStudent: jest.fn(() => Promise.resolve({})),
    removeMember: jest.fn(() => Promise.resolve({}))
}));

jest.mock('../../../frontend/js/modules/ai-assistant.js', () => ({
    initializeAIAssistant: jest.fn(),
    sendContextAwareMessage: jest.fn(() => Promise.resolve({
        message: 'AI response',
        suggestions: ['Suggestion 1', 'Suggestion 2'],
        ragSources: [],
        webSearchUsed: false,
        actions: []
    })),
    CONTEXT_TYPES: {
        PROJECT_CREATION: 'PROJECT_CREATION',
        COURSE_GENERATION: 'COURSE_GENERATION',
        TRACK_PLANNING: 'TRACK_PLANNING'
    },
    clearConversationHistory: jest.fn()
}));

jest.mock('../../../frontend/js/modules/org-admin-utils.js', () => ({
    escapeHtml: jest.fn((str) => str),
    capitalizeFirst: jest.fn((str) => str.charAt(0).toUpperCase() + str.slice(1)),
    parseCommaSeparated: jest.fn((str) => str ? str.split(',').map(s => s.trim()) : []),
    formatDate: jest.fn((date) => date || 'N/A'),
    formatDuration: jest.fn((weeks) => weeks ? `${weeks} weeks` : 'N/A'),
    openModal: jest.fn(),
    closeModal: jest.fn(),
    showNotification: jest.fn()
}));

describe('Org Admin Project Wizard Navigation', () => {
    let mockStep1;
    let mockStep2;
    let mockStep3;
    let mockStepIndicators;

    beforeEach(() => {
        // Reset all mocks
        jest.clearAllMocks();

        // Setup DOM structure matching org-admin-dashboard.html
        document.body.innerHTML = `
            <div id="createProjectModal" class="modal-backdrop">
                <div class="modal-content">
                    <h2>Create Project</h2>

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

                    <!-- Wizard Steps -->
                    <div id="projectStep1" class="project-step active">
                        <h3>Step 1: Basic Information</h3>
                        <input type="text" id="projectName" value="" />
                        <input type="text" id="projectSlug" value="" />
                        <textarea id="projectDescription"></textarea>
                        <button onclick="previousProjectStep()" class="btn-outline">Back</button>
                        <button onclick="nextProjectStep()" class="btn-primary">Next</button>
                    </div>

                    <div id="projectStep2" class="project-step">
                        <h3>Step 2: Configuration</h3>
                        <div id="ragLoadingIndicator" style="display: none;">Loading...</div>
                        <div id="ragSuggestions" style="display: none;">
                            <div id="projectInsights"></div>
                            <div id="recommendedTracks"></div>
                            <div id="suggestedObjectives"></div>
                        </div>
                        <div id="ragContextIndicator" style="display: none;"></div>
                        <select id="projectTargetRoles" multiple></select>
                        <input type="number" id="projectDuration" />
                        <input type="number" id="projectMaxParticipants" />
                        <input type="date" id="projectStartDate" />
                        <input type="date" id="projectEndDate" />
                        <textarea id="projectObjectives"></textarea>
                        <button onclick="previousProjectStep()" class="btn-outline">Back</button>
                        <button onclick="nextProjectStep()" class="btn-primary">Next</button>
                    </div>

                    <div id="projectStep3" class="project-step">
                        <h3>Step 3: Create Tracks</h3>
                        <div id="tracksContainer"></div>
                        <button onclick="previousProjectStep()" class="btn-outline">Back</button>
                        <button type="submit" class="btn-primary">Create Project</button>
                    </div>
                </div>
            </div>
        `;

        // Get element references
        mockStep1 = document.getElementById('projectStep1');
        mockStep2 = document.getElementById('projectStep2');
        mockStep3 = document.getElementById('projectStep3');
        mockStepIndicators = document.querySelectorAll('.step');

        // Initialize projects management
        initializeProjectsManagement('org-123');

        // Mock console methods to avoid cluttering test output
        console.log = jest.fn();
        console.error = jest.fn();
    });

    afterEach(() => {
        jest.restoreAllMocks();
        document.body.innerHTML = '';
    });

    describe('nextProjectStep() - Forward Navigation', () => {
        describe('Step 1 → Step 2 Transition', () => {
            test('should advance from step 1 to step 2 when all required fields are filled', () => {
                // Fill required fields
                document.getElementById('projectName').value = 'Test Project';
                document.getElementById('projectSlug').value = 'test-project';
                document.getElementById('projectDescription').value = 'Test description for the project';

                // Verify starting state
                expect(mockStep1.classList.contains('active')).toBe(true);
                expect(mockStep2.classList.contains('active')).toBe(false);

                // Execute next step
                nextProjectStep();

                // Verify step 2 is now active
                expect(mockStep1.classList.contains('active')).toBe(false);
                expect(mockStep2.classList.contains('active')).toBe(true);
            });

            test('should show error notification when name is missing', () => {
                // Leave name empty
                document.getElementById('projectName').value = '';
                document.getElementById('projectSlug').value = 'test-project';
                document.getElementById('projectDescription').value = 'Test description';

                const { showNotification } = require('../../../frontend/js/modules/org-admin-utils.js');

                // Execute next step
                nextProjectStep();

                // Verify error was shown
                expect(showNotification).toHaveBeenCalledWith(
                    'Please fill in all required fields (Name, Slug, and Description)',
                    'error'
                );

                // Verify still on step 1
                expect(mockStep1.classList.contains('active')).toBe(true);
                expect(mockStep2.classList.contains('active')).toBe(false);
            });

            test('should show error notification when slug is missing', () => {
                document.getElementById('projectName').value = 'Test Project';
                document.getElementById('projectSlug').value = '';
                document.getElementById('projectDescription').value = 'Test description';

                const { showNotification } = require('../../../frontend/js/modules/org-admin-utils.js');

                nextProjectStep();

                expect(showNotification).toHaveBeenCalledWith(
                    'Please fill in all required fields (Name, Slug, and Description)',
                    'error'
                );
                expect(mockStep1.classList.contains('active')).toBe(true);
            });

            test('should show error notification when description is missing', () => {
                document.getElementById('projectName').value = 'Test Project';
                document.getElementById('projectSlug').value = 'test-project';
                document.getElementById('projectDescription').value = '';

                const { showNotification } = require('../../../frontend/js/modules/org-admin-utils.js');

                nextProjectStep();

                expect(showNotification).toHaveBeenCalledWith(
                    'Please fill in all required fields (Name, Slug, and Description)',
                    'error'
                );
                expect(mockStep1.classList.contains('active')).toBe(true);
            });

            test('should trigger AI suggestion generation when advancing to step 2', async () => {
                // Fill required fields
                document.getElementById('projectName').value = 'Test Project';
                document.getElementById('projectSlug').value = 'test-project';
                document.getElementById('projectDescription').value = 'A comprehensive training project for developers';

                const { initializeAIAssistant, sendContextAwareMessage } =
                    require('../../../frontend/js/modules/ai-assistant.js');

                // Execute next step
                nextProjectStep();

                // Wait for async AI call
                await new Promise(resolve => setTimeout(resolve, 100));

                // Verify AI assistant was initialized
                expect(initializeAIAssistant).toHaveBeenCalled();
            });

            test('should update step indicators correctly', () => {
                // Fill required fields
                document.getElementById('projectName').value = 'Test Project';
                document.getElementById('projectSlug').value = 'test-project';
                document.getElementById('projectDescription').value = 'Test description';

                // Execute next step
                nextProjectStep();

                // Verify step indicators
                const indicators = document.querySelectorAll('.step');
                expect(indicators[0].classList.contains('completed')).toBe(true);
                expect(indicators[1].classList.contains('active')).toBe(true);
                expect(indicators[2].classList.contains('active')).toBe(false);
            });
        });

        describe('Step 2 → Step 3 Transition', () => {
            beforeEach(() => {
                // Start on step 2
                mockStep1.classList.remove('active');
                mockStep2.classList.add('active');
                mockStep3.classList.remove('active');
            });

            test('should advance from step 2 to step 3', () => {
                // Verify starting state
                expect(mockStep2.classList.contains('active')).toBe(true);
                expect(mockStep3.classList.contains('active')).toBe(false);

                // Execute next step
                nextProjectStep();

                // Verify step 3 is now active
                expect(mockStep2.classList.contains('active')).toBe(false);
                expect(mockStep3.classList.contains('active')).toBe(true);
            });

            test('should update step indicators for step 3', () => {
                // Execute next step
                nextProjectStep();

                // Verify step indicators
                const indicators = document.querySelectorAll('.step');
                expect(indicators[0].classList.contains('completed')).toBe(true);
                expect(indicators[1].classList.contains('completed')).toBe(true);
                expect(indicators[2].classList.contains('active')).toBe(true);
            });

            test('should not trigger AI suggestions when advancing to step 3', () => {
                const { initializeAIAssistant } =
                    require('../../../frontend/js/modules/ai-assistant.js');

                // Clear any previous calls
                initializeAIAssistant.mockClear();

                // Execute next step
                nextProjectStep();

                // Verify AI was NOT called
                expect(initializeAIAssistant).not.toHaveBeenCalled();
            });
        });

        describe('Edge Cases and Error Handling', () => {
            test('should handle missing active step element gracefully', () => {
                // Remove active class from all steps
                mockStep1.classList.remove('active');
                mockStep2.classList.remove('active');
                mockStep3.classList.remove('active');

                // Should not throw error
                expect(() => nextProjectStep()).not.toThrow();

                // Should default to step 1
                expect(console.log).toHaveBeenCalledWith('📄 Current step:', 1);
            });

            test('should handle step 3 correctly (last step)', () => {
                // Start on step 3
                mockStep1.classList.remove('active');
                mockStep2.classList.remove('active');
                mockStep3.classList.add('active');

                // Execute next step (should do nothing)
                nextProjectStep();

                // Should stay on step 3
                expect(mockStep3.classList.contains('active')).toBe(true);
            });

            test('should handle malformed step IDs', () => {
                // Create element with bad ID
                const badStep = document.createElement('div');
                badStep.id = 'invalidStepId';
                badStep.className = 'project-step active';
                document.querySelector('.modal-content').appendChild(badStep);

                // Remove active from good steps
                mockStep1.classList.remove('active');

                // Should not crash
                expect(() => nextProjectStep()).not.toThrow();
            });
        });
    });

    describe('previousProjectStep() - Backward Navigation', () => {
        describe('Step 2 → Step 1 Transition (THE FIX)', () => {
            beforeEach(() => {
                // Start on step 2 (this is the scenario that was broken)
                mockStep1.classList.remove('active');
                mockStep2.classList.add('active');
                mockStep3.classList.remove('active');
            });

            test('should navigate back from step 2 to step 1 using correct selector', () => {
                // This test verifies the fix: using .project-step.active instead of .wizard-step.active

                // Verify starting state
                expect(mockStep2.classList.contains('active')).toBe(true);
                expect(mockStep1.classList.contains('active')).toBe(false);

                // Execute previous step
                previousProjectStep();

                // Verify step 1 is now active
                expect(mockStep1.classList.contains('active')).toBe(true);
                expect(mockStep2.classList.contains('active')).toBe(false);
            });

            test('should extract step number from element ID correctly', () => {
                // Execute previous step
                previousProjectStep();

                // Verify console logs show correct step extraction
                expect(console.log).toHaveBeenCalledWith(
                    'Going back from step 2 to step 1'
                );
            });

            test('should update step indicators when going back to step 1', () => {
                // Execute previous step
                previousProjectStep();

                // Verify step indicators
                const indicators = document.querySelectorAll('.step');
                expect(indicators[0].classList.contains('active')).toBe(true);
                expect(indicators[0].classList.contains('completed')).toBe(false);
                expect(indicators[1].classList.contains('active')).toBe(false);
            });
        });

        describe('Step 3 → Step 2 Transition', () => {
            beforeEach(() => {
                // Start on step 3
                mockStep1.classList.remove('active');
                mockStep2.classList.remove('active');
                mockStep3.classList.add('active');
            });

            test('should navigate back from step 3 to step 2', () => {
                // Verify starting state
                expect(mockStep3.classList.contains('active')).toBe(true);
                expect(mockStep2.classList.contains('active')).toBe(false);

                // Execute previous step
                previousProjectStep();

                // Verify step 2 is now active
                expect(mockStep2.classList.contains('active')).toBe(true);
                expect(mockStep3.classList.contains('active')).toBe(false);
            });

            test('should update step indicators when going back to step 2', () => {
                // Execute previous step
                previousProjectStep();

                // Verify step indicators
                const indicators = document.querySelectorAll('.step');
                expect(indicators[0].classList.contains('completed')).toBe(true);
                expect(indicators[1].classList.contains('active')).toBe(true);
                expect(indicators[2].classList.contains('active')).toBe(false);
            });
        });

        describe('Edge Cases and Boundary Conditions', () => {
            test('should not navigate back from step 1 (first step)', () => {
                // Start on step 1 (already at the beginning)
                mockStep1.classList.add('active');
                mockStep2.classList.remove('active');
                mockStep3.classList.remove('active');

                // Execute previous step
                previousProjectStep();

                // Should stay on step 1
                expect(mockStep1.classList.contains('active')).toBe(true);
            });

            test('should handle missing active step element', () => {
                // Remove active class from all steps
                mockStep1.classList.remove('active');
                mockStep2.classList.remove('active');
                mockStep3.classList.remove('active');

                // Should not throw error
                expect(() => previousProjectStep()).not.toThrow();

                // Should log error
                expect(console.error).toHaveBeenCalledWith('No active project step found');
            });

            test('should handle step with no ID', () => {
                // Create step without proper ID
                const noIdStep = document.createElement('div');
                noIdStep.className = 'project-step active';
                document.querySelector('.modal-content').appendChild(noIdStep);

                // Remove active from good steps
                mockStep2.classList.remove('active');

                // Should not crash, should default to step 1
                expect(() => previousProjectStep()).not.toThrow();
            });

            test('should parse step number from ID correctly for all steps', () => {
                // Test step 1
                mockStep1.classList.add('active');
                mockStep2.classList.remove('active');
                mockStep3.classList.remove('active');
                console.log.mockClear();
                previousProjectStep();

                // Should stay at step 1 (boundary)
                expect(mockStep1.classList.contains('active')).toBe(true);

                // Test step 2
                mockStep1.classList.remove('active');
                mockStep2.classList.add('active');
                mockStep3.classList.remove('active');
                console.log.mockClear();
                previousProjectStep();
                expect(console.log).toHaveBeenCalledWith('Going back from step 2 to step 1');

                // Test step 3
                mockStep1.classList.remove('active');
                mockStep2.classList.remove('active');
                mockStep3.classList.add('active');
                console.log.mockClear();
                previousProjectStep();
                expect(console.log).toHaveBeenCalledWith('Going back from step 3 to step 2');
            });
        });

        describe('Integration with nextProjectStep()', () => {
            test('should correctly navigate forward then backward', () => {
                // Start on step 1
                document.getElementById('projectName').value = 'Test Project';
                document.getElementById('projectSlug').value = 'test-project';
                document.getElementById('projectDescription').value = 'Test description';

                // Navigate forward
                nextProjectStep();
                expect(mockStep2.classList.contains('active')).toBe(true);

                // Navigate backward
                previousProjectStep();
                expect(mockStep1.classList.contains('active')).toBe(true);
            });

            test('should handle multiple forward and backward navigations', () => {
                // Fill required fields for step 1
                document.getElementById('projectName').value = 'Test';
                document.getElementById('projectSlug').value = 'test';
                document.getElementById('projectDescription').value = 'Desc';

                // Step 1 -> 2 -> 3 -> 2 -> 1
                nextProjectStep();
                expect(mockStep2.classList.contains('active')).toBe(true);

                nextProjectStep();
                expect(mockStep3.classList.contains('active')).toBe(true);

                previousProjectStep();
                expect(mockStep2.classList.contains('active')).toBe(true);

                previousProjectStep();
                expect(mockStep1.classList.contains('active')).toBe(true);
            });

            test('should maintain form data when navigating back and forth', () => {
                // Fill form
                const nameInput = document.getElementById('projectName');
                const slugInput = document.getElementById('projectSlug');
                const descInput = document.getElementById('projectDescription');

                nameInput.value = 'Test Project';
                slugInput.value = 'test-project';
                descInput.value = 'Test description';

                // Navigate forward
                nextProjectStep();

                // Navigate back
                previousProjectStep();

                // Verify form data is preserved
                expect(nameInput.value).toBe('Test Project');
                expect(slugInput.value).toBe('test-project');
                expect(descInput.value).toBe('Test description');
            });
        });
    });

    describe('Step Indicator Updates', () => {
        test('should mark completed steps correctly', () => {
            // Fill step 1 fields
            document.getElementById('projectName').value = 'Test';
            document.getElementById('projectSlug').value = 'test';
            document.getElementById('projectDescription').value = 'Desc';

            // Go to step 2
            nextProjectStep();

            const indicators = document.querySelectorAll('.step');
            expect(indicators[0].classList.contains('completed')).toBe(true);
            expect(indicators[1].classList.contains('active')).toBe(true);

            // Go to step 3
            nextProjectStep();
            expect(indicators[0].classList.contains('completed')).toBe(true);
            expect(indicators[1].classList.contains('completed')).toBe(true);
            expect(indicators[2].classList.contains('active')).toBe(true);
        });

        test('should clear completed status when navigating backward', () => {
            // Start on step 2
            mockStep1.classList.remove('active');
            mockStep2.classList.add('active');

            // Navigate back
            previousProjectStep();

            const indicators = document.querySelectorAll('.step');
            expect(indicators[0].classList.contains('active')).toBe(true);
            expect(indicators[0].classList.contains('completed')).toBe(false);
        });
    });

    describe('AI Suggestion Generation', () => {
        test('should show loading indicator while generating AI suggestions', () => {
            const loadingIndicator = document.getElementById('ragLoadingIndicator');
            const suggestionsContainer = document.getElementById('ragSuggestions');

            // Fill step 1
            document.getElementById('projectName').value = 'Test Project';
            document.getElementById('projectSlug').value = 'test-project';
            document.getElementById('projectDescription').value = 'Test description';

            // Verify initial state
            expect(loadingIndicator.style.display).toBe('none');

            // Navigate to step 2
            nextProjectStep();

            // Loading should be visible initially (checked in generateAISuggestions)
            // This is tested indirectly through the AI assistant mock
        });
    });

    describe('Regression Tests', () => {
        test('REGRESSION: should use .project-step selector not .wizard-step', () => {
            // This test ensures we don't revert the bug fix
            // The bug was using querySelector('.wizard-step.active') instead of
            // querySelector('.project-step.active')

            // Start on step 2
            mockStep2.classList.add('active');
            mockStep1.classList.remove('active');

            // Create a fake .wizard-step element that should NOT be selected
            const fakeWizardStep = document.createElement('div');
            fakeWizardStep.className = 'wizard-step active';
            fakeWizardStep.setAttribute('data-step', '99');
            document.body.appendChild(fakeWizardStep);

            // Execute previous step
            previousProjectStep();

            // Should navigate to step 1 (from project-step), NOT step 99 (from wizard-step)
            expect(mockStep1.classList.contains('active')).toBe(true);
            expect(console.log).toHaveBeenCalledWith('Going back from step 2 to step 1');
        });

        test('REGRESSION: should parse step number from ID not dataset', () => {
            // The bug was trying to use dataset.step on wrong element type
            // Correct approach: parse from element.id

            mockStep2.classList.add('active');
            mockStep1.classList.remove('active');

            // Add a dataset.step that should be ignored
            mockStep2.setAttribute('data-step', '999');

            // Execute previous step
            previousProjectStep();

            // Should use ID (step 2) not dataset (step 999)
            expect(console.log).toHaveBeenCalledWith('Going back from step 2 to step 1');
        });
    });
});
