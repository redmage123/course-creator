/**
 * Metadata Client Unit Tests
 *
 * TDD METHODOLOGY:
 * These tests are written FIRST (RED phase), then implementation follows (GREEN phase)
 *
 * BUSINESS VALUE:
 * Ensure fuzzy search works correctly in the frontend for typo-tolerant course discovery
 */

// Mock fetch globally
global.fetch = jest.fn();

// Import the class (we'll need to make it exportable)
const MetadataClient = require('../../../frontend/js/metadata-client.js');

describe('MetadataClient Fuzzy Search', () => {
    let client;

    beforeEach(() => {
        // Reset mocks before each test
        fetch.mockClear();
        client = new MetadataClient('https://localhost:8011/api/v1/metadata');
    });

    /**
     * TEST 1: Fuzzy search with typo
     *
     * TDD CYCLE:
     * - RED: Write this test expecting it to FAIL (searchFuzzy doesn't exist yet)
     * - GREEN: Implement searchFuzzy method
     * - REFACTOR: Clean up code if needed
     *
     * BUSINESS USE CASE:
     * Student types "pyton" instead of "python" - should still find courses
     */
    test('searchFuzzy handles typos - student searches for "pyton"', async () => {
        // Arrange: Mock API response
        const mockResponse = {
            results: [
                {
                    entity_id: '123e4567-e89b-12d3-a456-426614174000',
                    entity_type: 'course',
                    title: 'Python Programming Fundamentals',
                    description: 'Learn Python from scratch',
                    tags: ['python', 'programming', 'beginner'],
                    similarity_score: 0.44
                }
            ]
        };

        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        // Act: Search with typo
        const results = await client.searchFuzzy('pyton', {
            entity_types: ['course'],
            similarity_threshold: 0.3
        });

        // Assert: Verify API was called correctly
        expect(fetch).toHaveBeenCalledWith(
            'https://localhost:8011/api/v1/metadata/search/fuzzy',
            expect.objectContaining({
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: 'pyton',
                    entity_types: ['course'],
                    similarity_threshold: 0.3,
                    limit: 20
                })
            })
        );

        // Assert: Verify results returned
        expect(results).toHaveLength(1);
        expect(results[0].title).toBe('Python Programming Fundamentals');
        expect(results[0].similarity_score).toBe(0.44);
    });

    /**
     * TEST 2: Fuzzy search returns similarity scores
     *
     * BUSINESS USE CASE:
     * Display match quality to users so they know how relevant results are
     */
    test('searchFuzzy returns similarity scores with results', async () => {
        // Arrange
        const mockResponse = {
            results: [
                {
                    entity_id: '111',
                    title: 'Python Basics',
                    similarity_score: 0.85  // High similarity
                },
                {
                    entity_id: '222',
                    title: 'Advanced Python',
                    similarity_score: 0.45  // Lower similarity
                }
            ]
        };

        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        // Act
        const results = await client.searchFuzzy('python', {
            entity_types: ['course']
        });

        // Assert: Both results have similarity scores
        expect(results[0].similarity_score).toBeGreaterThan(0.8);
        expect(results[1].similarity_score).toBeGreaterThan(0.4);
        expect(results[1].similarity_score).toBeLessThan(0.5);
    });

    /**
     * TEST 3: Fuzzy search with partial match
     *
     * BUSINESS USE CASE:
     * Student types incomplete word - should still find matches
     */
    test('searchFuzzy handles partial matches - "prog" finds "programming"', async () => {
        // Arrange
        const mockResponse = {
            results: [
                {
                    title: 'Introduction to Programming',
                    similarity_score: 0.50
                },
                {
                    title: 'Advanced Programming Techniques',
                    similarity_score: 0.48
                }
            ]
        };

        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        // Act
        const results = await client.searchFuzzy('prog', {
            entity_types: ['course'],
            similarity_threshold: 0.3
        });

        // Assert
        expect(results).toHaveLength(2);
        expect(results[0].title).toContain('Programming');
        expect(results[1].title).toContain('Programming');
    });

    /**
     * TEST 4: Fuzzy search fallback on error
     *
     * BUSINESS USE CASE:
     * If fuzzy search fails, gracefully fall back to empty results
     */
    test('searchFuzzy returns empty array on API error', async () => {
        // Arrange: Mock API failure
        fetch.mockResolvedValueOnce({
            ok: false,
            statusText: 'Internal Server Error'
        });

        // Act
        const results = await client.searchFuzzy('test');

        // Assert: Returns empty array instead of throwing
        expect(results).toEqual([]);
    });

    /**
     * TEST 5: Fuzzy search uses cache
     *
     * BUSINESS USE CASE:
     * Reduce API calls for same search term
     */
    test('searchFuzzy uses cache for repeated searches', async () => {
        // Arrange
        const mockResponse = {
            results: [{ title: 'Python Course', similarity_score: 0.9 }]
        };

        fetch.mockResolvedValue({
            ok: true,
            json: async () => mockResponse
        });

        // Act: Search twice with same term
        await client.searchFuzzy('python');
        await client.searchFuzzy('python');

        // Assert: API called only once (second used cache)
        expect(fetch).toHaveBeenCalledTimes(1);
    });
});
