/*
 * Knowledge Graph System Migration
 *
 * BUSINESS REQUIREMENT:
 * Implement a knowledge graph to represent semantic relationships between courses,
 * topics, concepts, skills, and learning outcomes for intelligent learning path
 * generation and prerequisite tracking.
 *
 * FEATURES:
 * - Node-edge graph structure for flexible relationships
 * - Support for multiple entity types (courses, concepts, skills, topics)
 * - Weighted edges for relationship strength
 * - Path materialization for performance
 * - Graph traversal optimization via indexes
 *
 * TECHNICAL APPROACH:
 * - PostgreSQL with recursive CTEs for graph queries
 * - JSONB for flexible node/edge properties
 * - GIN indexes for fast graph traversal
 * - Materialized paths for common queries
 */

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- KNOWLEDGE GRAPH NODES
-- ========================================

/*
 * Nodes represent entities in the knowledge graph
 *
 * ENTITY TYPES:
 * - course: Educational courses
 * - topic: Subject areas (e.g., "Python Programming", "Machine Learning")
 * - concept: Specific concepts (e.g., "recursion", "neural networks")
 * - skill: Learnable skills (e.g., "debugging", "algorithm design")
 * - learning_outcome: Educational objectives
 * - resource: Learning resources (videos, articles, etc.)
 */
CREATE TABLE IF NOT EXISTS knowledge_graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Node classification
    node_type VARCHAR(50) NOT NULL CHECK (node_type IN (
        'course', 'topic', 'concept', 'skill', 'learning_outcome', 'resource'
    )),

    -- Reference to actual entity
    entity_id UUID NOT NULL,

    -- Human-readable label
    label VARCHAR(255) NOT NULL,

    -- Node properties (flexible JSONB structure)
    -- Examples:
    -- course: {difficulty, duration, category}
    -- concept: {complexity, domain, bloom_level}
    -- skill: {proficiency_level, category}
    properties JSONB NOT NULL DEFAULT '{}',

    -- Additional metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,

    -- Ensure unique entity references
    UNIQUE(node_type, entity_id)
);

-- Indexes for efficient node queries
CREATE INDEX idx_kg_nodes_type ON knowledge_graph_nodes(node_type);
CREATE INDEX idx_kg_nodes_entity ON knowledge_graph_nodes(entity_id);
CREATE INDEX idx_kg_nodes_label ON knowledge_graph_nodes(label);
CREATE INDEX idx_kg_nodes_properties ON knowledge_graph_nodes USING GIN(properties);
CREATE INDEX idx_kg_nodes_created_at ON knowledge_graph_nodes(created_at);

-- Full-text search on labels
CREATE INDEX idx_kg_nodes_label_fts ON knowledge_graph_nodes USING GIN(to_tsvector('english', label));

COMMENT ON TABLE knowledge_graph_nodes IS 'Nodes in the knowledge graph representing courses, concepts, skills, and other educational entities';
COMMENT ON COLUMN knowledge_graph_nodes.node_type IS 'Type of node: course, topic, concept, skill, learning_outcome, resource';
COMMENT ON COLUMN knowledge_graph_nodes.entity_id IS 'Reference to the actual entity (course_id, concept_id, etc.)';
COMMENT ON COLUMN knowledge_graph_nodes.properties IS 'Flexible JSON properties specific to node type';

-- ========================================
-- KNOWLEDGE GRAPH EDGES
-- ========================================

/*
 * Edges represent relationships between nodes
 *
 * RELATIONSHIP TYPES:
 * - prerequisite_of: Course A is prerequisite of Course B
 * - teaches: Course teaches Concept
 * - builds_on: Concept builds on another Concept
 * - covers: Course covers Topic
 * - develops: Course develops Skill
 * - achieves: Course achieves Learning Outcome
 * - relates_to: General relationship between entities
 * - part_of: Topic is part of Domain
 * - requires: Skill requires another Skill
 * - references: Resource references Concept/Topic/Course
 */
CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationship type
    edge_type VARCHAR(50) NOT NULL CHECK (edge_type IN (
        'prerequisite_of', 'teaches', 'builds_on', 'covers', 'develops',
        'achieves', 'relates_to', 'part_of', 'requires', 'references',
        'similar_to', 'alternative_to'
    )),

    -- Source and target nodes
    source_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,

    -- Relationship strength/weight (0.0 to 1.0)
    weight DECIMAL(3,2) DEFAULT 1.0 CHECK (weight >= 0.0 AND weight <= 1.0),

    -- Edge properties (flexible JSONB structure)
    -- Examples:
    -- prerequisite_of: {mandatory, strength, substitutable}
    -- teaches: {coverage_depth, bloom_level}
    -- builds_on: {dependency_strength}
    properties JSONB DEFAULT '{}',

    -- Additional metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,

    -- Prevent duplicate edges
    UNIQUE(edge_type, source_node_id, target_node_id),

    -- Prevent self-loops for most edge types
    CHECK (
        source_node_id != target_node_id OR
        edge_type IN ('relates_to', 'similar_to')
    )
);

-- Indexes for efficient edge queries and graph traversal
CREATE INDEX idx_kg_edges_type ON knowledge_graph_edges(edge_type);
CREATE INDEX idx_kg_edges_source ON knowledge_graph_edges(source_node_id);
CREATE INDEX idx_kg_edges_target ON knowledge_graph_edges(target_node_id);
CREATE INDEX idx_kg_edges_weight ON knowledge_graph_edges(weight);
CREATE INDEX idx_kg_edges_properties ON knowledge_graph_edges USING GIN(properties);

-- Composite indexes for common queries
CREATE INDEX idx_kg_edges_source_type ON knowledge_graph_edges(source_node_id, edge_type);
CREATE INDEX idx_kg_edges_target_type ON knowledge_graph_edges(target_node_id, edge_type);
CREATE INDEX idx_kg_edges_type_weight ON knowledge_graph_edges(edge_type, weight);

COMMENT ON TABLE knowledge_graph_edges IS 'Edges representing relationships between knowledge graph nodes';
COMMENT ON COLUMN knowledge_graph_edges.edge_type IS 'Type of relationship: prerequisite_of, teaches, builds_on, etc.';
COMMENT ON COLUMN knowledge_graph_edges.weight IS 'Relationship strength from 0.0 (weak) to 1.0 (strong)';
COMMENT ON COLUMN knowledge_graph_edges.properties IS 'Flexible JSON properties specific to edge type';

-- ========================================
-- MATERIALIZED PATHS (for performance)
-- ========================================

/*
 * Pre-computed paths between nodes for common queries
 *
 * USE CASES:
 * - Learning paths from course A to course B
 * - Prerequisite chains
 * - Concept dependency sequences
 *
 * APPROACH:
 * Materialized view that is refreshed periodically or on-demand
 */
CREATE TABLE IF NOT EXISTS knowledge_graph_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Start and end nodes
    start_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    end_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,

    -- Path information
    path_nodes UUID[] NOT NULL,              -- Array of node IDs in order
    path_edges UUID[] NOT NULL,              -- Array of edge IDs in order
    path_length INTEGER NOT NULL,            -- Number of hops
    total_weight DECIMAL(10,2),              -- Sum of edge weights

    -- Path classification
    path_type VARCHAR(50) NOT NULL CHECK (path_type IN (
        'learning_path', 'prerequisite_chain', 'concept_dependency',
        'skill_progression', 'shortest_path', 'optimal_path'
    )),

    -- Additional path metadata
    metadata JSONB DEFAULT '{}',

    -- Computation tracking
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Ensure unique paths
    UNIQUE(start_node_id, end_node_id, path_type)
);

-- Indexes for path queries
CREATE INDEX idx_kg_paths_start ON knowledge_graph_paths(start_node_id);
CREATE INDEX idx_kg_paths_end ON knowledge_graph_paths(end_node_id);
CREATE INDEX idx_kg_paths_type ON knowledge_graph_paths(path_type);
CREATE INDEX idx_kg_paths_length ON knowledge_graph_paths(path_length);
CREATE INDEX idx_kg_paths_computed ON knowledge_graph_paths(computed_at);

COMMENT ON TABLE knowledge_graph_paths IS 'Materialized paths for fast path queries';
COMMENT ON COLUMN knowledge_graph_paths.path_nodes IS 'Ordered array of node UUIDs forming the path';
COMMENT ON COLUMN knowledge_graph_paths.path_type IS 'Classification of path: learning_path, prerequisite_chain, etc.';

-- ========================================
-- GRAPH ANALYTICS CACHE
-- ========================================

/*
 * Cache for expensive graph analytics computations
 *
 * ANALYTICS:
 * - PageRank scores for importance
 * - Betweenness centrality for key concepts
 * - Community detection results
 * - Node similarity scores
 */
CREATE TABLE IF NOT EXISTS knowledge_graph_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Analytics type
    analytics_type VARCHAR(50) NOT NULL CHECK (analytics_type IN (
        'pagerank', 'betweenness_centrality', 'closeness_centrality',
        'community_detection', 'node_similarity', 'clustering_coefficient'
    )),

    -- Node-specific analytics
    node_id UUID REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,

    -- Analytics results
    score DECIMAL(10,6),
    rank INTEGER,
    community_id INTEGER,
    results JSONB DEFAULT '{}',

    -- Computation metadata
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    parameters JSONB DEFAULT '{}',

    UNIQUE(analytics_type, node_id)
);

-- Indexes for analytics queries
CREATE INDEX idx_kg_analytics_type ON knowledge_graph_analytics(analytics_type);
CREATE INDEX idx_kg_analytics_node ON knowledge_graph_analytics(node_id);
CREATE INDEX idx_kg_analytics_score ON knowledge_graph_analytics(score DESC);
CREATE INDEX idx_kg_analytics_rank ON knowledge_graph_analytics(rank);

COMMENT ON TABLE knowledge_graph_analytics IS 'Cached graph analytics computations';
COMMENT ON COLUMN knowledge_graph_analytics.analytics_type IS 'Type of analytics: pagerank, centrality, community detection, etc.';

-- ========================================
-- HELPER FUNCTIONS
-- ========================================

/*
 * Function: Find neighbors of a node
 *
 * Returns all nodes connected to the given node via specified edge types
 */
CREATE OR REPLACE FUNCTION kg_get_neighbors(
    p_node_id UUID,
    p_edge_types VARCHAR[] DEFAULT NULL,
    p_direction VARCHAR DEFAULT 'both'  -- 'outgoing', 'incoming', 'both'
)
RETURNS TABLE (
    node_id UUID,
    node_type VARCHAR,
    label VARCHAR,
    edge_type VARCHAR,
    edge_weight DECIMAL,
    direction VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    -- Outgoing edges
    SELECT
        n.id,
        n.node_type,
        n.label,
        e.edge_type,
        e.weight,
        'outgoing'::VARCHAR
    FROM knowledge_graph_edges e
    JOIN knowledge_graph_nodes n ON e.target_node_id = n.id
    WHERE e.source_node_id = p_node_id
        AND (p_edge_types IS NULL OR e.edge_type = ANY(p_edge_types))
        AND p_direction IN ('outgoing', 'both')

    UNION ALL

    -- Incoming edges
    SELECT
        n.id,
        n.node_type,
        n.label,
        e.edge_type,
        e.weight,
        'incoming'::VARCHAR
    FROM knowledge_graph_edges e
    JOIN knowledge_graph_nodes n ON e.source_node_id = n.id
    WHERE e.target_node_id = p_node_id
        AND (p_edge_types IS NULL OR e.edge_type = ANY(p_edge_types))
        AND p_direction IN ('incoming', 'both');
END;
$$ LANGUAGE plpgsql;

/*
 * Function: Find shortest path between two nodes
 *
 * Uses recursive CTE to find shortest path
 * Returns path as array of node IDs
 */
CREATE OR REPLACE FUNCTION kg_find_shortest_path(
    p_start_node_id UUID,
    p_end_node_id UUID,
    p_max_depth INTEGER DEFAULT 10
)
RETURNS UUID[] AS $$
DECLARE
    v_path UUID[];
BEGIN
    WITH RECURSIVE path AS (
        -- Base case: start node
        SELECT
            p_start_node_id AS node_id,
            ARRAY[p_start_node_id] AS path_nodes,
            0 AS depth

        UNION ALL

        -- Recursive case: traverse edges
        SELECT
            e.target_node_id,
            p.path_nodes || e.target_node_id,
            p.depth + 1
        FROM path p
        JOIN knowledge_graph_edges e ON p.node_id = e.source_node_id
        WHERE
            p.depth < p_max_depth
            AND NOT (e.target_node_id = ANY(p.path_nodes))  -- Avoid cycles
            AND p.node_id != p_end_node_id  -- Stop when we reach end node
    )
    SELECT path_nodes INTO v_path
    FROM path
    WHERE node_id = p_end_node_id
    ORDER BY depth
    LIMIT 1;

    RETURN v_path;
END;
$$ LANGUAGE plpgsql;

/*
 * Function: Get all prerequisites for a course
 *
 * Returns all courses that are prerequisites (direct and transitive)
 */
CREATE OR REPLACE FUNCTION kg_get_all_prerequisites(
    p_course_node_id UUID,
    p_max_depth INTEGER DEFAULT 5
)
RETURNS TABLE (
    prerequisite_node_id UUID,
    prerequisite_label VARCHAR,
    depth INTEGER,
    path UUID[]
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE prereqs AS (
        -- Base case: direct prerequisites
        SELECT
            n.id AS prereq_id,
            n.label AS prereq_label,
            1 AS prereq_depth,
            ARRAY[e.source_node_id] AS prereq_path
        FROM knowledge_graph_edges e
        JOIN knowledge_graph_nodes n ON e.source_node_id = n.id
        WHERE e.target_node_id = p_course_node_id
            AND e.edge_type = 'prerequisite_of'
            AND n.node_type = 'course'

        UNION ALL

        -- Recursive case: prerequisites of prerequisites
        SELECT
            n.id,
            n.label,
            pr.prereq_depth + 1,
            pr.prereq_path || e.source_node_id
        FROM prereqs pr
        JOIN knowledge_graph_edges e ON pr.prereq_id = e.target_node_id
        JOIN knowledge_graph_nodes n ON e.source_node_id = n.id
        WHERE
            pr.prereq_depth < p_max_depth
            AND e.edge_type = 'prerequisite_of'
            AND n.node_type = 'course'
            AND NOT (e.source_node_id = ANY(pr.prereq_path))  -- Avoid cycles
    )
    SELECT DISTINCT ON (prereqs.prereq_id)
        prereqs.prereq_id,
        prereqs.prereq_label,
        prereqs.prereq_depth,
        prereqs.prereq_path
    FROM prereqs
    ORDER BY prereqs.prereq_id, prereqs.prereq_depth;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- TRIGGERS
-- ========================================

/*
 * Trigger: Update updated_at timestamp
 */
CREATE OR REPLACE FUNCTION update_kg_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_kg_nodes_updated_at
    BEFORE UPDATE ON knowledge_graph_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_kg_timestamp();

CREATE TRIGGER trigger_kg_edges_updated_at
    BEFORE UPDATE ON knowledge_graph_edges
    FOR EACH ROW
    EXECUTE FUNCTION update_kg_timestamp();

-- ========================================
-- SAMPLE DATA (for testing)
-- ========================================

/*
 * Insert sample course nodes
 */
INSERT INTO knowledge_graph_nodes (node_type, entity_id, label, properties) VALUES
    ('course', gen_random_uuid(), 'Introduction to Python',
     '{"difficulty": "beginner", "duration": 40, "category": "programming"}'),
    ('course', gen_random_uuid(), 'Data Structures',
     '{"difficulty": "intermediate", "duration": 60, "category": "computer-science"}'),
    ('course', gen_random_uuid(), 'Algorithms',
     '{"difficulty": "intermediate", "duration": 80, "category": "computer-science"}'),
    ('course', gen_random_uuid(), 'Machine Learning Basics',
     '{"difficulty": "advanced", "duration": 100, "category": "ai-ml"}')
ON CONFLICT (node_type, entity_id) DO NOTHING;

/*
 * Insert sample concept nodes
 */
INSERT INTO knowledge_graph_nodes (node_type, entity_id, label, properties) VALUES
    ('concept', gen_random_uuid(), 'Variables and Data Types',
     '{"complexity": "low", "domain": "programming-fundamentals"}'),
    ('concept', gen_random_uuid(), 'Control Flow',
     '{"complexity": "low", "domain": "programming-fundamentals"}'),
    ('concept', gen_random_uuid(), 'Recursion',
     '{"complexity": "medium", "domain": "algorithms"}'),
    ('concept', gen_random_uuid(), 'Neural Networks',
     '{"complexity": "high", "domain": "machine-learning"}')
ON CONFLICT (node_type, entity_id) DO NOTHING;

COMMENT ON SCHEMA public IS 'Knowledge Graph system for tracking relationships between courses, concepts, skills, and learning outcomes';
