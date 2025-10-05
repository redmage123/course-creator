/**
 * Metadata Service Client Library
 *
 * BUSINESS REQUIREMENT:
 * Frontend integration with metadata-service for intelligent search,
 * recommendations, and content discovery.
 *
 * USAGE:
 * - Import this module in any frontend JavaScript
 * - Use MetadataClient to interact with metadata service
 * - Provides search, recommendations, and content discovery
 */

class MetadataClient {
    constructor(baseUrl = 'https://localhost:8011/api/v1/metadata') {
        this.baseUrl = baseUrl;
        this.cache = new Map(); // Simple in-memory cache
        this.cacheTTL = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Search for content using metadata
     *
     * FEATURES:
     * - Full-text search across all metadata
     * - Filter by entity types
     * - Filter by required tags
     * - Ranked by relevance
     */
    async search(query, options = {}) {
        const {
            entity_types = null,
            required_tags = null,
            limit = 20
        } = options;

        const cacheKey = `search:${query}:${entity_types}:${required_tags}:${limit}`;
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        try {
            const response = await fetch(`${this.baseUrl}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query,
                    entity_types,
                    required_tags,
                    limit
                })
            });

            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }

            const results = await response.json();
            this._setCache(cacheKey, results);
            return results;
        } catch (error) {
            console.error('Metadata search error:', error);
            return [];
        }
    }

    /**
     * Fuzzy search with typo tolerance
     *
     * BUSINESS VALUE:
     * Students can find courses even with typos or partial search terms
     *
     * FEATURES:
     * - Typo tolerance: "pyton" → finds "python"
     * - Partial matching: "prog" → finds "programming"
     * - Similarity scores: Shows match quality (0.0-1.0)
     * - Caching: Reduces API calls
     *
     * @param {string} query - Search query (typos allowed!)
     * @param {Object} options - Search options
     * @param {Array<string>} options.entity_types - Filter by entity types
     * @param {number} options.similarity_threshold - Minimum similarity (0.0-1.0)
     * @param {number} options.limit - Maximum results
     * @returns {Promise<Array>} Results with similarity scores
     */
    async searchFuzzy(query, options = {}) {
        const {
            entity_types = null,
            similarity_threshold = 0.3,
            limit = 20
        } = options;

        const cacheKey = `fuzzy:${query}:${entity_types}:${similarity_threshold}:${limit}`;
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        try {
            const response = await fetch(`${this.baseUrl}/search/fuzzy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query,
                    entity_types,
                    similarity_threshold,
                    limit
                })
            });

            if (!response.ok) {
                throw new Error(`Fuzzy search failed: ${response.statusText}`);
            }

            const data = await response.json();
            const results = data.results || [];

            this._setCache(cacheKey, results);
            return results;
        } catch (error) {
            console.error('Fuzzy search error:', error);
            return [];
        }
    }

    /**
     * Get recommendations based on user's activity
     *
     * ALGORITHM:
     * 1. Get metadata for completed courses
     * 2. Extract topics and tags
     * 3. Find similar courses at next difficulty level
     */
    async getRecommendations(completedCourseIds, options = {}) {
        const {
            difficulty_level = 'intermediate',
            limit = 5
        } = options;

        try {
            // Get metadata for completed courses
            const completedMetadata = await Promise.all(
                completedCourseIds.map(id => this.getByEntity(id, 'course'))
            );

            // Extract all topics and tags
            const allTags = new Set();
            completedMetadata.forEach(metadata => {
                if (metadata) {
                    metadata.tags.forEach(tag => allTags.add(tag));
                    if (metadata.metadata.educational?.topics) {
                        metadata.metadata.educational.topics.forEach(topic =>
                            allTags.add(topic.toLowerCase())
                        );
                    }
                }
            });

            // Search for courses with similar tags at next level
            const topTags = Array.from(allTags).slice(0, 5); // Top 5 tags
            const query = topTags.join(' ');

            return await this.search(query, {
                entity_types: ['course'],
                required_tags: [difficulty_level],
                limit
            });
        } catch (error) {
            console.error('Get recommendations error:', error);
            return [];
        }
    }

    /**
     * Get related content for current context
     *
     * USE CASE:
     * Show related videos, labs, exercises while viewing content
     */
    async getRelatedContent(entityId, entityType, options = {}) {
        const {
            content_types = ['video', 'lab', 'exercise'],
            limit = 5
        } = options;

        try {
            // Get metadata for current entity
            const metadata = await this.getByEntity(entityId, entityType);
            if (!metadata || !metadata.tags.length) {
                return [];
            }

            // Search for related content with same tags
            const query = metadata.tags.join(' ');
            const results = await this.search(query, {
                entity_types: content_types,
                limit: limit + 5 // Get extras to filter out current item
            });

            // Filter out the current entity
            return results
                .filter(item => item.entity_id !== entityId)
                .slice(0, limit);
        } catch (error) {
            console.error('Get related content error:', error);
            return [];
        }
    }

    /**
     * Get content by tags
     *
     * USE CASE:
     * Filter content by topic tags
     */
    async getByTags(tags, options = {}) {
        const {
            entity_type = null,
            limit = 100
        } = options;

        const tagsParam = tags.join(',');
        const params = new URLSearchParams();
        if (entity_type) params.append('entity_type', entity_type);
        params.append('limit', limit);

        try {
            const response = await fetch(
                `${this.baseUrl}/tags/${tagsParam}?${params}`,
                { method: 'GET' }
            );

            if (!response.ok) {
                throw new Error(`Get by tags failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Get by tags error:', error);
            return [];
        }
    }

    /**
     * Get metadata by entity
     */
    async getByEntity(entityId, entityType) {
        const cacheKey = `entity:${entityId}:${entityType}`;
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        try {
            const params = new URLSearchParams({ entity_type: entityType });
            const response = await fetch(
                `${this.baseUrl}/entity/${entityId}?${params}`,
                { method: 'GET' }
            );

            if (!response.ok) {
                if (response.status === 404) return null;
                throw new Error(`Get by entity failed: ${response.statusText}`);
            }

            const metadata = await response.json();
            this._setCache(cacheKey, metadata);
            return metadata;
        } catch (error) {
            console.error('Get by entity error:', error);
            return null;
        }
    }

    /**
     * Create metadata (for admin/instructor use)
     */
    async create(metadataData) {
        try {
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(metadataData)
            });

            if (!response.ok) {
                throw new Error(`Create metadata failed: ${response.statusText}`);
            }

            const created = await response.json();
            this._invalidateEntityCache(created.entity_id, created.entity_type);
            return created;
        } catch (error) {
            console.error('Create metadata error:', error);
            throw error;
        }
    }

    /**
     * Update metadata (for admin/instructor use)
     */
    async update(metadataId, updates) {
        try {
            const response = await fetch(`${this.baseUrl}/${metadataId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (!response.ok) {
                throw new Error(`Update metadata failed: ${response.statusText}`);
            }

            const updated = await response.json();
            this._invalidateEntityCache(updated.entity_id, updated.entity_type);
            return updated;
        } catch (error) {
            console.error('Update metadata error:', error);
            throw error;
        }
    }

    /**
     * Auto-enrich metadata (extract tags, topics)
     */
    async enrich(metadataId) {
        try {
            const response = await fetch(`${this.baseUrl}/${metadataId}/enrich`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Enrich metadata failed: ${response.statusText}`);
            }

            const enriched = await response.json();
            this._invalidateEntityCache(enriched.entity_id, enriched.entity_type);
            return enriched;
        } catch (error) {
            console.error('Enrich metadata error:', error);
            throw error;
        }
    }

    /**
     * Get popular tags across platform
     *
     * IMPLEMENTATION:
     * Aggregates tags from search results
     */
    async getPopularTags(entityType = 'course', limit = 20) {
        try {
            // Get all entities of this type
            const response = await fetch(`${this.baseUrl}/type/${entityType}?limit=1000`);
            if (!response.ok) return [];

            const metadata = await response.json();

            // Count tag frequencies
            const tagCounts = {};
            metadata.forEach(item => {
                item.tags.forEach(tag => {
                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                });
            });

            // Sort by frequency and return top N
            return Object.entries(tagCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, limit)
                .map(([tag, count]) => ({ tag, count }));
        } catch (error) {
            console.error('Get popular tags error:', error);
            return [];
        }
    }

    /**
     * Build a learning path from start to goal
     *
     * ALGORITHM:
     * 1. Get all courses in topic
     * 2. Sort by difficulty
     * 3. Return ordered sequence
     */
    async buildLearningPath(topic, options = {}) {
        const {
            start_level = 'beginner',
            end_level = 'advanced',
            max_courses = 10
        } = options;

        try {
            // Search for all courses in this topic
            const allCourses = await this.search(topic, {
                entity_types: ['course'],
                limit: 100
            });

            // Group by difficulty
            const difficultyOrder = ['beginner', 'intermediate', 'advanced', 'expert'];
            const startIdx = difficultyOrder.indexOf(start_level);
            const endIdx = difficultyOrder.indexOf(end_level);

            const path = allCourses
                .filter(course => {
                    const difficulty = course.metadata?.educational?.difficulty;
                    const diffIdx = difficultyOrder.indexOf(difficulty);
                    return diffIdx >= startIdx && diffIdx <= endIdx;
                })
                .sort((a, b) => {
                    const aDiff = difficultyOrder.indexOf(a.metadata?.educational?.difficulty || 'beginner');
                    const bDiff = difficultyOrder.indexOf(b.metadata?.educational?.difficulty || 'beginner');
                    return aDiff - bDiff;
                })
                .slice(0, max_courses);

            return path;
        } catch (error) {
            console.error('Build learning path error:', error);
            return [];
        }
    }

    // Cache helpers
    _getFromCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        const { data, timestamp } = cached;
        if (Date.now() - timestamp > this.cacheTTL) {
            this.cache.delete(key);
            return null;
        }

        return data;
    }

    _setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    _invalidateEntityCache(entityId, entityType) {
        const cacheKey = `entity:${entityId}:${entityType}`;
        this.cache.delete(cacheKey);
    }

    clearCache() {
        this.cache.clear();
    }
}

// Create singleton instance
const metadataClient = new MetadataClient();

// Export for use in other modules
export { MetadataClient, metadataClient };
