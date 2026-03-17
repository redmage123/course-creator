/**
 * Unit Tests: Audience-to-Track Mapping
 *
 * BUSINESS CONTEXT:
 * When an organization admin selects target audiences for a project,
 * the system should automatically propose creating one track per audience.
 * This streamlines the track creation process and ensures each audience
 * gets appropriate training content.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Tests mapAudiencesToTracks() function
 * - Tests AUDIENCE_TRACK_MAPPING configuration
 * - Tests track proposal generation
 * - Tests handling of various audience combinations
 *
 * TDD METHODOLOGY: RED PHASE
 * These tests are written BEFORE implementation and should initially FAIL.
 */

import {
    mapAudiencesToTracks,
    getSelectedAudiences,
    AUDIENCE_TRACK_MAPPING
} from '../../../frontend/js/modules/org-admin-projects.js';

describe('Audience-to-Track Mapping - TDD RED Phase', () => {
    beforeEach(() => {
        // Setup mock DOM with audience selection
        document.body.innerHTML = `
            <div id="projectStep2" class="project-step active">
                <div class="form-group">
                    <label>Target Audiences</label>
                    <select id="targetAudiences" multiple>
                        <option value="application_developers">Application Developers</option>
                        <option value="business_analysts">Business Analysts</option>
                        <option value="operations_engineers">Operations Engineers</option>
                        <option value="data_scientists">Data Scientists</option>
                        <option value="qa_engineers">QA Engineers</option>
                        <option value="devops_engineers">DevOps Engineers</option>
                    </select>
                </div>
            </div>
        `;
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.clearAllMocks();
    });

    describe('AUDIENCE_TRACK_MAPPING - Configuration object', () => {
        test('should exist and be defined', () => {
            /**
             * TEST: Mapping configuration exists
             * REQUIREMENT: Predefined audience-to-track mappings
             * SUCCESS CRITERIA: Configuration object is defined
             */
            expect(AUDIENCE_TRACK_MAPPING).toBeDefined();
            expect(typeof AUDIENCE_TRACK_MAPPING).toBe('object');
        });

        test('should contain mapping for application developers', () => {
            /**
             * TEST: Application developer audience mapping
             * REQUIREMENT: Support for app developer training tracks
             * SUCCESS CRITERIA: Mapping includes application_developers
             */
            expect(AUDIENCE_TRACK_MAPPING).toHaveProperty('application_developers');
            expect(AUDIENCE_TRACK_MAPPING.application_developers).toHaveProperty('name');
            expect(AUDIENCE_TRACK_MAPPING.application_developers).toHaveProperty('description');
            expect(AUDIENCE_TRACK_MAPPING.application_developers).toHaveProperty('difficulty');
        });

        test('should contain mapping for business analysts', () => {
            /**
             * TEST: Business analyst audience mapping
             * REQUIREMENT: Support for business analyst training tracks
             * SUCCESS CRITERIA: Mapping includes business_analysts
             */
            expect(AUDIENCE_TRACK_MAPPING).toHaveProperty('business_analysts');
            expect(AUDIENCE_TRACK_MAPPING.business_analysts.name).toContain('Business Analyst');
        });

        test('should contain mapping for operations engineers', () => {
            /**
             * TEST: Operations engineer audience mapping
             * REQUIREMENT: Support for ops engineer training tracks
             * SUCCESS CRITERIA: Mapping includes operations_engineers
             */
            expect(AUDIENCE_TRACK_MAPPING).toHaveProperty('operations_engineers');
            expect(AUDIENCE_TRACK_MAPPING.operations_engineers.name).toContain('Operations');
        });

        test('should include required fields for each mapping', () => {
            /**
             * TEST: Mapping structure validation
             * REQUIREMENT: Each mapping has required fields
             * SUCCESS CRITERIA: All mappings have name, description, difficulty
             */
            const requiredFields = ['name', 'description', 'difficulty'];

            Object.values(AUDIENCE_TRACK_MAPPING).forEach(mapping => {
                requiredFields.forEach(field => {
                    expect(mapping).toHaveProperty(field);
                });
            });
        });

        test('should have appropriate difficulty levels', () => {
            /**
             * TEST: Difficulty level validation
             * REQUIREMENT: Valid difficulty levels for tracks
             * SUCCESS CRITERIA: Difficulty is beginner, intermediate, or advanced
             */
            const validDifficulties = ['beginner', 'intermediate', 'advanced'];

            Object.values(AUDIENCE_TRACK_MAPPING).forEach(mapping => {
                expect(validDifficulties).toContain(mapping.difficulty);
            });
        });
    });

    describe('mapAudiencesToTracks() - Core mapping function', () => {
        test('should exist and be a function', () => {
            /**
             * TEST: Function exists
             * REQUIREMENT: Core mapping functionality
             * SUCCESS CRITERIA: Function is defined
             */
            expect(mapAudiencesToTracks).toBeDefined();
            expect(typeof mapAudiencesToTracks).toBe('function');
        });

        test('should return empty array for empty input', () => {
            /**
             * TEST: Handle empty audience list
             * REQUIREMENT: Graceful handling of no audiences
             * SUCCESS CRITERIA: Returns empty array for empty input
             */
            const result = mapAudiencesToTracks([]);

            expect(result).toEqual([]);
            expect(Array.isArray(result)).toBe(true);
        });

        test('should return empty array for null input', () => {
            /**
             * TEST: Handle null input
             * REQUIREMENT: Defensive programming
             * SUCCESS CRITERIA: Returns empty array for null
             */
            const result = mapAudiencesToTracks(null);

            expect(result).toEqual([]);
        });

        test('should return empty array for undefined input', () => {
            /**
             * TEST: Handle undefined input
             * REQUIREMENT: Defensive programming
             * SUCCESS CRITERIA: Returns empty array for undefined
             */
            const result = mapAudiencesToTracks(undefined);

            expect(result).toEqual([]);
        });

        test('should create one track for one audience', () => {
            /**
             * TEST: Single audience mapping
             * REQUIREMENT: One-to-one audience-track mapping
             * SUCCESS CRITERIA: One audience creates one track
             */
            const audiences = ['application_developers'];

            const result = mapAudiencesToTracks(audiences);

            expect(result).toHaveLength(1);
            expect(result[0]).toHaveProperty('name');
            expect(result[0]).toHaveProperty('description');
        });

        test('should create three tracks for three audiences', () => {
            /**
             * TEST: Multiple audience mapping
             * REQUIREMENT: Create track for each selected audience
             * SUCCESS CRITERIA: Three audiences create three tracks
             */
            const audiences = [
                'application_developers',
                'business_analysts',
                'operations_engineers'
            ];

            const result = mapAudiencesToTracks(audiences);

            expect(result).toHaveLength(3);
        });

        test('should include track name derived from audience', () => {
            /**
             * TEST: Track naming convention
             * REQUIREMENT: Track names reflect target audience
             * SUCCESS CRITERIA: Track name contains audience type
             */
            const audiences = ['application_developers'];

            const result = mapAudiencesToTracks(audiences);

            expect(result[0].name).toContain('Application Developer');
        });

        test('should include appropriate track description', () => {
            /**
             * TEST: Track description quality
             * REQUIREMENT: Meaningful track descriptions
             * SUCCESS CRITERIA: Description is not empty and relevant
             */
            const audiences = ['business_analysts'];

            const result = mapAudiencesToTracks(audiences);

            expect(result[0].description).toBeTruthy();
            expect(result[0].description.length).toBeGreaterThan(10);
        });

        test('should include difficulty level in track', () => {
            /**
             * TEST: Difficulty level in output
             * REQUIREMENT: Tracks have appropriate difficulty
             * SUCCESS CRITERIA: Each track has difficulty property
             */
            const audiences = ['application_developers'];

            const result = mapAudiencesToTracks(audiences);

            expect(result[0]).toHaveProperty('difficulty');
            expect(['beginner', 'intermediate', 'advanced']).toContain(result[0].difficulty);
        });

        test('should include audience reference in each track', () => {
            /**
             * TEST: Track-audience relationship
             * REQUIREMENT: Track linked back to source audience
             * SUCCESS CRITERIA: Each track has audience property
             */
            const audiences = ['data_scientists'];

            const result = mapAudiencesToTracks(audiences);

            expect(result[0]).toHaveProperty('audience');
            expect(result[0].audience).toBe('data_scientists');
        });

        test('should handle unsupported audience gracefully', () => {
            /**
             * TEST: Unknown audience handling
             * REQUIREMENT: Graceful degradation for unknown audiences
             * SUCCESS CRITERIA: Creates generic track for unknown audience
             */
            const audiences = ['unknown_audience_type'];

            const result = mapAudiencesToTracks(audiences);

            expect(result).toHaveLength(1);
            expect(result[0]).toHaveProperty('name');
            expect(result[0]).toHaveProperty('description');
        });

        test('should create unique track for each audience', () => {
            /**
             * TEST: Unique tracks per audience
             * REQUIREMENT: No duplicate tracks
             * SUCCESS CRITERIA: Each track has different name
             */
            const audiences = [
                'application_developers',
                'business_analysts',
                'operations_engineers'
            ];

            const result = mapAudiencesToTracks(audiences);

            const names = result.map(track => track.name);
            const uniqueNames = new Set(names);

            expect(uniqueNames.size).toBe(3);
        });

        test('should maintain audience order in track list', () => {
            /**
             * TEST: Predictable track ordering
             * REQUIREMENT: Track order matches audience selection order
             * SUCCESS CRITERIA: First audience creates first track
             */
            const audiences = [
                'business_analysts',
                'application_developers'
            ];

            const result = mapAudiencesToTracks(audiences);

            expect(result[0].audience).toBe('business_analysts');
            expect(result[1].audience).toBe('application_developers');
        });

        test('should include all required fields in each track', () => {
            /**
             * TEST: Complete track structure
             * REQUIREMENT: Tracks have all necessary fields
             * SUCCESS CRITERIA: Each track has name, description, difficulty, audience
             */
            const audiences = ['qa_engineers'];

            const result = mapAudiencesToTracks(audiences);
            const track = result[0];

            expect(track).toHaveProperty('name');
            expect(track).toHaveProperty('description');
            expect(track).toHaveProperty('difficulty');
            expect(track).toHaveProperty('audience');
        });
    });

    describe('getSelectedAudiences() - Extract audiences from UI', () => {
        test('should exist and be a function', () => {
            /**
             * TEST: Function exists
             * REQUIREMENT: Extract selected audiences from DOM
             * SUCCESS CRITERIA: Function is defined
             */
            expect(getSelectedAudiences).toBeDefined();
            expect(typeof getSelectedAudiences).toBe('function');
        });

        test('should return empty array when no audiences selected', () => {
            /**
             * TEST: Handle no selection
             * REQUIREMENT: Graceful handling of no selection
             * SUCCESS CRITERIA: Returns empty array
             */
            const result = getSelectedAudiences();

            expect(result).toEqual([]);
        });

        test('should return single selected audience', () => {
            /**
             * TEST: Single selection
             * REQUIREMENT: Extract single audience
             * SUCCESS CRITERIA: Returns array with one audience
             */
            const select = document.getElementById('targetAudiences');
            select.options[0].selected = true; // application_developers

            const result = getSelectedAudiences();

            expect(result).toHaveLength(1);
            expect(result[0]).toBe('application_developers');
        });

        test('should return multiple selected audiences', () => {
            /**
             * TEST: Multiple selection
             * REQUIREMENT: Extract multiple audiences
             * SUCCESS CRITERIA: Returns array with all selected audiences
             */
            const select = document.getElementById('targetAudiences');
            select.options[0].selected = true; // application_developers
            select.options[1].selected = true; // business_analysts
            select.options[2].selected = true; // operations_engineers

            const result = getSelectedAudiences();

            expect(result).toHaveLength(3);
            expect(result).toContain('application_developers');
            expect(result).toContain('business_analysts');
            expect(result).toContain('operations_engineers');
        });

        test('should return empty array if select element does not exist', () => {
            /**
             * TEST: Handle missing DOM element
             * REQUIREMENT: Defensive programming
             * SUCCESS CRITERIA: Returns empty array if element not found
             */
            document.getElementById('targetAudiences').remove();

            const result = getSelectedAudiences();

            expect(result).toEqual([]);
        });
    });

    describe('Integration - Full audience-to-track workflow', () => {
        test('should map selected UI audiences to track proposals', () => {
            /**
             * TEST: Complete workflow
             * REQUIREMENT: UI selection → track proposals
             * SUCCESS CRITERIA: Selected audiences create appropriate tracks
             */
            const select = document.getElementById('targetAudiences');
            select.options[0].selected = true; // application_developers
            select.options[2].selected = true; // operations_engineers

            const selectedAudiences = getSelectedAudiences();
            const proposedTracks = mapAudiencesToTracks(selectedAudiences);

            expect(proposedTracks).toHaveLength(2);
            expect(proposedTracks[0].name).toContain('Application Developer');
            expect(proposedTracks[1].name).toContain('Operations');
        });

        test('should create consistent results for same audience selection', () => {
            /**
             * TEST: Deterministic mapping
             * REQUIREMENT: Consistent results for same input
             * SUCCESS CRITERIA: Multiple calls with same input produce same output
             */
            const audiences = ['business_analysts', 'data_scientists'];

            const result1 = mapAudiencesToTracks(audiences);
            const result2 = mapAudiencesToTracks(audiences);

            expect(result1).toEqual(result2);
        });
    });
});
