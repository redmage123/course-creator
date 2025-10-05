/**
 * Knowledge Graph Service Client Library
 *
 * BUSINESS REQUIREMENT:
 * Frontend integration with knowledge-graph-service for visualizing
 * relationships, learning paths, and prerequisites.
 *
 * USAGE:
 * - Import this module in any frontend JavaScript
 * - Use KnowledgeGraphClient to interact with graph service
 * - Provides graph queries, path finding, and visualization data
 */

class KnowledgeGraphClient {
    constructor(baseUrl = 'https://localhost:8012/api/v1/graph') {
        this.baseUrl = baseUrl;
        this.cache = new Map();
        this.cacheTTL = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Get graph visualization data
     *
     * FEATURES:
     * - Filter by organization, difficulty, category
     * - Returns nodes and edges for D3.js
     * - Cached for performance
     */
    async getGraphVisualization(filters = {}) {
        const cacheKey = `viz:${JSON.stringify(filters)}`;
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        try {
            const params = new URLSearchParams(filters);
            const response = await fetch(`${this.baseUrl}/visualize/courses?${params}`);

            if (!response.ok) {
                throw new Error(`Graph visualization failed: ${response.statusText}`);
            }

            const data = await response.json();
            this._setCache(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Error fetching graph visualization:', error);
            return { nodes: [], edges: [] };
        }
    }

    /**
     * Find learning path between courses
     *
     * BUSINESS USE CASE:
     * Student wants to know how to get from course A to course B
     *
     * Args:
     *     startCourseId: Starting course UUID
     *     endCourseId: Target course UUID
     *     studentId: Optional student ID for personalization
     *     optimization: 'shortest', 'easiest', 'fastest'
     *
     * Returns:
     *     Learning path with courses, duration, difficulty progression
     */
    async findLearningPath(startCourseId, endCourseId, studentId = null, optimization = 'shortest') {
        try {
            const params = new URLSearchParams({
                start: startCourseId,
                end: endCourseId,
                optimization: optimization
            });
            if (studentId) params.append('student', studentId);

            const response = await fetch(`${this.baseUrl}/paths/learning-path?${params}`);

            if (!response.ok) {
                throw new Error(`Path finding failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error finding learning path:', error);
            return null;
        }
    }

    /**
     * Check prerequisites for a course
     *
     * BUSINESS USE CASE:
     * Student wants to enroll in a course and needs to know
     * if they meet the prerequisites
     *
     * Args:
     *     courseId: Course UUID
     *     studentId: Student UUID for checking completed courses
     *
     * Returns:
     *     {
     *         ready: boolean,
     *         prerequisites: [{id, title, completed, in_progress}],
     *         missing_prerequisites: [],
     *         recommended_courses: []
     *     }
     */
    async checkPrerequisites(courseId, studentId) {
        const cacheKey = `prereq:${courseId}:${studentId}`;
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        try {
            const params = studentId ? new URLSearchParams({ student: studentId }) : '';
            const response = await fetch(`${this.baseUrl}/prerequisites/${courseId}?${params}`);

            if (!response.ok) {
                throw new Error(`Prerequisite check failed: ${response.statusText}`);
            }

            const data = await response.json();
            this._setCache(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Error checking prerequisites:', error);
            return {
                ready: true, // Fail open - allow enrollment
                prerequisites: [],
                missing_prerequisites: [],
                recommended_courses: []
            };
        }
    }

    /**
     * Get neighbors of a node
     *
     * BUSINESS USE CASE:
     * Show related courses, concepts, or skills
     *
     * Args:
     *     nodeId: Node UUID
     *     edgeTypes: Array of edge types to follow
     *     depth: How many hops (1-3)
     *     direction: 'incoming', 'outgoing', 'both'
     *
     * Returns:
     *     Array of connected nodes
     */
    async getNeighbors(nodeId, edgeTypes = null, depth = 1, direction = 'both') {
        try {
            const params = new URLSearchParams({
                depth: depth,
                direction: direction
            });
            if (edgeTypes) params.append('edge_types', edgeTypes.join(','));

            const response = await fetch(`${this.baseUrl}/neighbors/${nodeId}?${params}`);

            if (!response.ok) {
                throw new Error(`Get neighbors failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting neighbors:', error);
            return [];
        }
    }

    /**
     * Get concept map for a topic
     *
     * BUSINESS USE CASE:
     * Student or instructor wants to explore concepts in a topic
     *
     * Args:
     *     topicId: Topic UUID (optional, null for all)
     *     depth: Hierarchy depth
     *
     * Returns:
     *     Hierarchical concept structure
     */
    async getConceptMap(topicId = null, depth = 3) {
        const cacheKey = `concepts:${topicId}:${depth}`;
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        try {
            const params = new URLSearchParams({ depth: depth });
            if (topicId) params.append('topic', topicId);

            const response = await fetch(`${this.baseUrl}/visualize/concepts?${params}`);

            if (!response.ok) {
                throw new Error(`Concept map failed: ${response.statusText}`);
            }

            const data = await response.json();
            this._setCache(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Error getting concept map:', error);
            return { concepts: [], relationships: [] };
        }
    }

    /**
     * Get skill progression for student
     *
     * BUSINESS USE CASE:
     * Student wants to see their skill development
     *
     * Args:
     *     studentId: Student UUID
     *     targetSkills: Optional array of target skills
     *
     * Returns:
     *     Skill tree with current levels and recommendations
     */
    async getSkillProgression(studentId, targetSkills = null) {
        try {
            const params = new URLSearchParams({ student: studentId });
            if (targetSkills) params.append('target_skills', targetSkills.join(','));

            const response = await fetch(`${this.baseUrl}/skills/progression?${params}`);

            if (!response.ok) {
                throw new Error(`Skill progression failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting skill progression:', error);
            return {
                current_skills: [],
                skill_gaps: [],
                recommended_courses: []
            };
        }
    }

    /**
     * Get related courses (graph-based)
     *
     * BUSINESS USE CASE:
     * Recommend courses based on graph relationships
     *
     * Args:
     *     courseId: Course UUID
     *     relationshipTypes: Types of relationships to follow
     *     limit: Maximum results
     *
     * Returns:
     *     Array of related courses with relationship info
     */
    async getRelatedCourses(courseId, relationshipTypes = ['similar_to', 'alternative_to'], limit = 5) {
        try {
            const params = new URLSearchParams({
                relationships: relationshipTypes.join(','),
                limit: limit
            });

            const response = await fetch(`${this.baseUrl}/courses/${courseId}/related?${params}`);

            if (!response.ok) {
                throw new Error(`Related courses failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting related courses:', error);
            return [];
        }
    }

    /**
     * Search graph nodes
     *
     * BUSINESS USE CASE:
     * Find nodes by name, type, or properties
     *
     * Args:
     *     query: Search query
     *     nodeTypes: Filter by node types
     *     limit: Maximum results
     *
     * Returns:
     *     Array of matching nodes
     */
    async searchNodes(query, nodeTypes = null, limit = 20) {
        try {
            const params = new URLSearchParams({
                q: query,
                limit: limit
            });
            if (nodeTypes) params.append('types', nodeTypes.join(','));

            const response = await fetch(`${this.baseUrl}/search?${params}`);

            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error searching nodes:', error);
            return [];
        }
    }

    /**
     * Get graph statistics
     *
     * BUSINESS USE CASE:
     * Admin dashboard showing graph health metrics
     *
     * Returns:
     *     Statistics about nodes, edges, paths
     */
    async getGraphStatistics() {
        const cacheKey = 'stats';
        const cached = this._getFromCache(cacheKey);
        if (cached) return cached;

        try {
            const response = await fetch(`${this.baseUrl}/statistics`);

            if (!response.ok) {
                throw new Error(`Statistics failed: ${response.statusText}`);
            }

            const data = await response.json();
            this._setCache(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Error getting statistics:', error);
            return {
                total_nodes: 0,
                total_edges: 0,
                node_types: {},
                edge_types: {}
            };
        }
    }

    // Admin functions (require authentication)

    /**
     * Create a node (admin only)
     */
    async createNode(nodeData) {
        try {
            const response = await fetch(`${this.baseUrl}/nodes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                },
                body: JSON.stringify(nodeData)
            });

            if (!response.ok) {
                throw new Error(`Create node failed: ${response.statusText}`);
            }

            this.clearCache(); // Invalidate cache
            return await response.json();
        } catch (error) {
            console.error('Error creating node:', error);
            throw error;
        }
    }

    /**
     * Create an edge (admin only)
     */
    async createEdge(edgeData) {
        try {
            const response = await fetch(`${this.baseUrl}/edges`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                },
                body: JSON.stringify(edgeData)
            });

            if (!response.ok) {
                throw new Error(`Create edge failed: ${response.statusText}`);
            }

            this.clearCache(); // Invalidate cache
            return await response.json();
        } catch (error) {
            console.error('Error creating edge:', error);
            throw error;
        }
    }

    /**
     * Bulk import graph data (admin only)
     */
    async bulkImport(graphData) {
        try {
            const response = await fetch(`${this.baseUrl}/bulk-import`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                },
                body: JSON.stringify(graphData)
            });

            if (!response.ok) {
                throw new Error(`Bulk import failed: ${response.statusText}`);
            }

            this.clearCache(); // Invalidate cache
            return await response.json();
        } catch (error) {
            console.error('Error bulk importing:', error);
            throw error;
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

    clearCache() {
        this.cache.clear();
    }
}

// Create singleton instance
const knowledgeGraphClient = new KnowledgeGraphClient();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KnowledgeGraphClient, knowledgeGraphClient };
}
