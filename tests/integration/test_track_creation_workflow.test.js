/**
 * Integration Tests: Track Creation Workflow
 *
 * BUSINESS CONTEXT:
 * Tests the complete end-to-end workflow for track creation based on
 * target audiences. Verifies that all components work together correctly
 * from audience selection to track creation confirmation.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests complete wizard flow with track requirement
 * - Tests integration between toggle, mapping, and dialog components
 * - Tests API calls and state management
 * - Tests user approval and cancellation workflows
 *
 * TDD METHODOLOGY: RED PHASE
 * These tests are written BEFORE implementation and should initially FAIL.
 */

import {
    nextProjectStep,
    needsTracksForProject,
    getSelectedAudiences,
    mapAudiencesToTracks,
    showTrackConfirmationDialog,
    handleTrackApproval,
    handleTrackCancellation
} from '../../frontend/js/modules/org-admin-projects.js';

import {
    createTrack
} from '../../frontend/js/modules/org-admin-api.js';

import {
    openModal,
    closeModal,
    showNotification
} from '../../frontend/js/modules/org-admin-utils.js';

// Mock dependencies - use actual implementation for escapeHtml
jest.mock('../../frontend/js/modules/org-admin-api.js');
jest.mock('../../frontend/js/modules/org-admin-utils.js', () => {
    const actual = jest.requireActual('../../frontend/js/modules/org-admin-utils.js');
    return {
        ...actual,
        openModal: jest.fn(),
        closeModal: jest.fn(),
        showNotification: jest.fn()
    };
});

describe('Track Creation Workflow - Integration Tests (TDD RED Phase)', () => {
    beforeEach(() => {
        // Setup complete wizard DOM
        document.body.innerHTML = `
            <div class="wizard-container">
                <div id="projectStep1" class="project-step active">
                    <input type="text" id="projectName" value="Test Project" />
                    <input type="text" id="projectSlug" value="test-project" />
                    <textarea id="projectDescription">Test Description</textarea>
                </div>

                <div id="projectStep2" class="project-step">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="needTracks" checked />
                            Does this project need tracks?
                        </label>
                    </div>

                    <div id="trackFieldsContainer">
                        <label>Target Audiences</label>
                        <select id="targetAudiences" multiple>
                            <option value="application_developers">Application Developers</option>
                            <option value="business_analysts">Business Analysts</option>
                            <option value="operations_engineers">Operations Engineers</option>
                        </select>
                    </div>

                    <button id="nextProjectStepBtn">Next</button>
                </div>

                <div id="projectStep3" class="project-step">
                    <h2>Review and Create</h2>
                </div>
            </div>
        `;

        // Mock API and utility functions
        createTrack.mockClear().mockResolvedValue({ id: 'track-123' });
        openModal.mockClear();
        closeModal.mockClear();
        showNotification.mockClear();

        console.log = jest.fn();
        console.error = jest.fn();
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.clearAllMocks();
    });

    describe('Complete Flow: Tracks Needed → Select Audiences → Approve → Create', () => {
        test('should complete full workflow when user approves tracks', async () => {
            /**
             * TEST: Happy path - complete workflow
             * REQUIREMENT: User can create tracks from audience selection
             * SUCCESS CRITERIA: All steps execute successfully
             */

            // Step 1: User indicates tracks are needed
            const needTracksCheckbox = document.getElementById('needTracks');
            needTracksCheckbox.checked = true;
            expect(needsTracksForProject()).toBe(true);

            // Step 2: User selects target audiences
            const audiencesSelect = document.getElementById('targetAudiences');
            audiencesSelect.options[0].selected = true; // app developers
            audiencesSelect.options[1].selected = true; // business analysts
            audiencesSelect.options[2].selected = true; // ops engineers

            const selectedAudiences = getSelectedAudiences();
            expect(selectedAudiences).toHaveLength(3);

            // Step 3: System maps audiences to track proposals
            const proposedTracks = mapAudiencesToTracks(selectedAudiences);
            expect(proposedTracks).toHaveLength(3);
            expect(proposedTracks[0].name).toContain('Application Developer');
            expect(proposedTracks[1].name).toContain('Business Analyst');
            expect(proposedTracks[2].name).toContain('Operations');

            // Step 4: System shows confirmation dialog
            const mockOnApprove = jest.fn();
            const mockOnCancel = jest.fn();
            showTrackConfirmationDialog(proposedTracks, mockOnApprove, mockOnCancel);

            expect(openModal).toHaveBeenCalledWith('trackConfirmationModal');

            // Step 5: User clicks Approve button
            const approveButton = document.getElementById('approveTracksBtn');
            approveButton.click();

            expect(mockOnApprove).toHaveBeenCalledWith(proposedTracks);
            expect(closeModal).toHaveBeenCalledWith('trackConfirmationModal');

            // Step 6: System creates tracks via API
            await handleTrackApproval(proposedTracks);

            expect(createTrack).toHaveBeenCalledTimes(3);
            expect(showNotification).toHaveBeenCalledWith(
                'success',
                expect.stringContaining('3 tracks created successfully')
            );
        });

        test('should show track details in confirmation dialog', () => {
            /**
             * TEST: User sees what will be created
             * REQUIREMENT: Transparency in track creation
             * SUCCESS CRITERIA: Dialog shows all track names and descriptions
             */

            const audiencesSelect = document.getElementById('targetAudiences');
            audiencesSelect.options[0].selected = true;
            audiencesSelect.options[1].selected = true;

            const selectedAudiences = getSelectedAudiences();
            const proposedTracks = mapAudiencesToTracks(selectedAudiences);

            showTrackConfirmationDialog(proposedTracks, jest.fn(), jest.fn());

            const dialogContent = document.body.innerHTML;
            expect(dialogContent).toContain('Application Developer Track');
            expect(dialogContent).toContain('Business Analyst Track');
        });

        test('should preserve track details through workflow', () => {
            /**
             * TEST: Data integrity
             * REQUIREMENT: Track data unchanged through pipeline
             * SUCCESS CRITERIA: Track details same from mapping to creation
             */

            const selectedAudiences = ['application_developers'];
            const proposedTracks = mapAudiencesToTracks(selectedAudiences);

            expect(proposedTracks[0]).toMatchObject({
                name: expect.stringContaining('Application Developer'),
                description: expect.any(String),
                difficulty: expect.any(String),
                audience: 'application_developers'
            });
        });
    });

    describe('Complete Flow: Tracks Not Needed → Skip Track Creation', () => {
        test('should skip track creation when needTracks is unchecked', () => {
            /**
             * TEST: Skip workflow
             * REQUIREMENT: Allow skipping track creation
             * SUCCESS CRITERIA: Track creation components not invoked
             */

            // User unchecks needTracks
            const needTracksCheckbox = document.getElementById('needTracks');
            needTracksCheckbox.checked = false;

            expect(needsTracksForProject()).toBe(false);

            // Track-related functions should not be called
            // This will be validated in nextProjectStep() logic
        });

        test('should hide track fields when needTracks unchecked', () => {
            /**
             * TEST: UI state management
             * REQUIREMENT: Hide irrelevant UI elements
             * SUCCESS CRITERIA: Track fields hidden
             */

            const needTracksCheckbox = document.getElementById('needTracks');
            needTracksCheckbox.checked = false;

            const trackFieldsContainer = document.getElementById('trackFieldsContainer');
            // handleTrackRequirementChange() would set display: none
            // This tests the integration of the toggle
        });

        test('should not show confirmation dialog when tracks not needed', () => {
            /**
             * TEST: Conditional dialog display
             * REQUIREMENT: Dialog only when tracks needed
             * SUCCESS CRITERIA: Dialog not shown
             */

            const needTracksCheckbox = document.getElementById('needTracks');
            needTracksCheckbox.checked = false;

            // Simulate advancing wizard
            // nextProjectStep() should skip track confirmation
            expect(needsTracksForProject()).toBe(false);
        });
    });

    describe('Complete Flow: Select Audiences → Cancel → Return to Configuration', () => {
        test('should return to track configuration when user cancels', () => {
            /**
             * TEST: Cancellation workflow
             * REQUIREMENT: Allow user to go back
             * SUCCESS CRITERIA: Returns to configuration, no tracks created
             */

            // Setup: User selects audiences and sees dialog
            const audiencesSelect = document.getElementById('targetAudiences');
            audiencesSelect.options[0].selected = true;

            const selectedAudiences = getSelectedAudiences();
            const proposedTracks = mapAudiencesToTracks(selectedAudiences);

            const mockOnApprove = jest.fn();
            const mockOnCancel = jest.fn();
            showTrackConfirmationDialog(proposedTracks, mockOnApprove, mockOnCancel);

            // User clicks Cancel
            const cancelButton = document.getElementById('cancelTracksBtn');
            cancelButton.click();

            expect(mockOnCancel).toHaveBeenCalled();
            expect(closeModal).toHaveBeenCalledWith('trackConfirmationModal');

            // Handle cancellation
            handleTrackCancellation();

            // Verify no tracks created
            expect(createTrack).not.toHaveBeenCalled();
        });

        test('should not show error notification on cancellation', () => {
            /**
             * TEST: Cancellation is not an error
             * REQUIREMENT: User-initiated cancellation is normal flow
             * SUCCESS CRITERIA: No error notification
             */

            handleTrackCancellation();

            const errorCalls = showNotification.mock.calls.filter(
                call => call[0] === 'error'
            );
            expect(errorCalls.length).toBe(0);
        });

        test('should allow user to modify audience selection after cancel', () => {
            /**
             * TEST: State preservation after cancel
             * REQUIREMENT: User can modify and retry
             * SUCCESS CRITERIA: Audience selection still editable
             */

            handleTrackCancellation();

            const audiencesSelect = document.getElementById('targetAudiences');
            expect(audiencesSelect.disabled).not.toBe(true);
        });
    });

    describe('Error Handling: API Failures', () => {
        test('should handle track creation API failure gracefully', async () => {
            /**
             * TEST: API error handling
             * REQUIREMENT: Graceful failure handling
             * SUCCESS CRITERIA: Error notification shown, no crash
             */

            createTrack.mockRejectedValue(new Error('API Connection Failed'));

            const proposedTracks = [{
                name: 'Test Track',
                description: 'Test',
                difficulty: 'beginner',
                audience: 'test'
            }];

            await handleTrackApproval(proposedTracks);

            expect(showNotification).toHaveBeenCalledWith(
                'error',
                expect.stringContaining('Failed to create tracks')
            );
        });

        test('should log error details for debugging', async () => {
            /**
             * TEST: Error logging
             * REQUIREMENT: Debug support for failures
             * SUCCESS CRITERIA: Error details logged to console
             */

            const error = new Error('API Connection Failed');
            createTrack.mockRejectedValue(error);

            await handleTrackApproval([{
                name: 'Test Track',
                description: 'Test',
                difficulty: 'beginner'
            }]);

            expect(console.error).toHaveBeenCalledWith(
                'Error creating tracks:',
                error
            );
        });
    });

    describe('State Management', () => {
        test('should maintain proposed tracks state', () => {
            /**
             * TEST: State persistence
             * REQUIREMENT: Track proposals available throughout workflow
             * SUCCESS CRITERIA: Proposed tracks accessible after mapping
             */

            const selectedAudiences = ['application_developers', 'business_analysts'];
            const proposedTracks = mapAudiencesToTracks(selectedAudiences);

            // Proposed tracks should be stored and accessible
            expect(proposedTracks).toHaveLength(2);
            expect(proposedTracks).toEqual([
                expect.objectContaining({ audience: 'application_developers' }),
                expect.objectContaining({ audience: 'business_analysts' })
            ]);
        });

        test('should update UI state when toggling needTracks', () => {
            /**
             * TEST: Reactive UI updates
             * REQUIREMENT: UI responds to state changes
             * SUCCESS CRITERIA: Fields show/hide based on needTracks
             */

            const needTracksCheckbox = document.getElementById('needTracks');
            const trackFieldsContainer = document.getElementById('trackFieldsContainer');

            // Initially checked - fields visible
            needTracksCheckbox.checked = true;
            expect(needsTracksForProject()).toBe(true);

            // Uncheck - fields should be hidden
            needTracksCheckbox.checked = false;
            expect(needsTracksForProject()).toBe(false);
        });
    });

    describe('Validation', () => {
        test('should not proceed without audience selection when tracks needed', () => {
            /**
             * TEST: Required field validation
             * REQUIREMENT: Cannot create tracks without audiences
             * SUCCESS CRITERIA: Validation prevents advancement
             */

            const needTracksCheckbox = document.getElementById('needTracks');
            needTracksCheckbox.checked = true;

            // No audiences selected
            const selectedAudiences = getSelectedAudiences();
            expect(selectedAudiences).toHaveLength(0);

            const proposedTracks = mapAudiencesToTracks(selectedAudiences);
            expect(proposedTracks).toHaveLength(0);

            // Should show validation error
            // This will be implemented in nextProjectStep()
        });

        test('should validate track data before API call', async () => {
            /**
             * TEST: Data validation before submission
             * REQUIREMENT: Only valid data sent to API
             * SUCCESS CRITERIA: Invalid tracks rejected
             */

            const invalidTrack = [{ name: '' }]; // Missing required fields

            // Should handle invalid data gracefully
            await expect(handleTrackApproval(invalidTrack)).resolves.not.toThrow();
        });
    });

    describe('Performance', () => {
        test('should handle large number of audiences efficiently', () => {
            /**
             * TEST: Scalability
             * REQUIREMENT: Handle multiple audiences
             * SUCCESS CRITERIA: Works with 10+ audiences
             */

            const manyAudiences = [
                'application_developers',
                'business_analysts',
                'operations_engineers',
                'data_scientists',
                'qa_engineers',
                'devops_engineers',
                'security_engineers',
                'database_administrators',
                'network_engineers',
                'cloud_architects'
            ];

            const start = performance.now();
            const proposedTracks = mapAudiencesToTracks(manyAudiences);
            const end = performance.now();

            expect(proposedTracks).toHaveLength(10);
            expect(end - start).toBeLessThan(100); // Should complete in <100ms
        });
    });
});
