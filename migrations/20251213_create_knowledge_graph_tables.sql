-- Knowledge Graph Tables Migration
-- Created: 2025-12-13
-- Purpose: Create tables and functions for the Knowledge Graph service

-- ========================================
-- KNOWLEDGE GRAPH NODES TABLE
-- ========================================

CREATE TABLE IF NOT EXISTS knowledge_graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    label VARCHAR(500) NOT NULL,
    properties JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,

    -- Ensure unique entity per type
    CONSTRAINT uq_knowledge_graph_entity UNIQUE (entity_id, node_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_kg_nodes_type ON knowledge_graph_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_entity ON knowledge_graph_nodes(entity_id);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_label ON knowledge_graph_nodes USING gin(to_tsvector('english', label));
CREATE INDEX IF NOT EXISTS idx_kg_nodes_properties ON knowledge_graph_nodes USING gin(properties);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_created ON knowledge_graph_nodes(created_at);

-- ========================================
-- KNOWLEDGE GRAPH EDGES TABLE
-- ========================================

CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edge_type VARCHAR(50) NOT NULL,
    source_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    weight DECIMAL(5,4) DEFAULT 1.0 CHECK (weight >= 0 AND weight <= 1),
    properties JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,

    -- Prevent duplicate edges between same nodes with same type
    CONSTRAINT uq_knowledge_graph_edge UNIQUE (source_node_id, target_node_id, edge_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_kg_edges_type ON knowledge_graph_edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON knowledge_graph_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON knowledge_graph_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_weight ON knowledge_graph_edges(weight DESC);

-- ========================================
-- HELPER FUNCTIONS
-- ========================================

-- Function to get node neighbors
CREATE OR REPLACE FUNCTION kg_get_neighbors(
    p_node_id UUID,
    p_edge_types VARCHAR[],
    p_direction VARCHAR DEFAULT 'both'
)
RETURNS TABLE (
    neighbor_id UUID,
    node_type VARCHAR,
    label VARCHAR,
    edge_type VARCHAR,
    weight DECIMAL,
    direction VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id AS neighbor_id,
        n.node_type::VARCHAR,
        n.label::VARCHAR,
        e.edge_type::VARCHAR,
        e.weight,
        CASE
            WHEN e.source_node_id = p_node_id THEN 'outgoing'::VARCHAR
            ELSE 'incoming'::VARCHAR
        END AS direction
    FROM knowledge_graph_edges e
    JOIN knowledge_graph_nodes n ON (
        CASE
            WHEN e.source_node_id = p_node_id THEN e.target_node_id = n.id
            ELSE e.source_node_id = n.id
        END
    )
    WHERE
        (p_direction = 'both' OR
         (p_direction = 'outgoing' AND e.source_node_id = p_node_id) OR
         (p_direction = 'incoming' AND e.target_node_id = p_node_id))
        AND (e.source_node_id = p_node_id OR e.target_node_id = p_node_id)
        AND (p_edge_types IS NULL OR e.edge_type = ANY(p_edge_types))
    ORDER BY e.weight DESC;
END;
$$;

-- Function to find shortest path between two nodes
CREATE OR REPLACE FUNCTION kg_find_shortest_path(
    p_start_node_id UUID,
    p_end_node_id UUID,
    p_max_depth INTEGER DEFAULT 10
)
RETURNS UUID[]
LANGUAGE plpgsql
AS $$
DECLARE
    v_path UUID[];
BEGIN
    -- Use recursive CTE for BFS path finding
    WITH RECURSIVE path_search AS (
        -- Base case: start node
        SELECT
            ARRAY[source_node_id, target_node_id] AS path,
            target_node_id AS current_node,
            1 AS depth
        FROM knowledge_graph_edges
        WHERE source_node_id = p_start_node_id

        UNION ALL

        -- Recursive case: extend path
        SELECT
            ps.path || e.target_node_id,
            e.target_node_id,
            ps.depth + 1
        FROM path_search ps
        JOIN knowledge_graph_edges e ON e.source_node_id = ps.current_node
        WHERE
            NOT e.target_node_id = ANY(ps.path)  -- Avoid cycles
            AND ps.depth < p_max_depth
    )
    SELECT path INTO v_path
    FROM path_search
    WHERE current_node = p_end_node_id
    ORDER BY depth
    LIMIT 1;

    RETURN v_path;
END;
$$;

-- Function to get all prerequisites (recursive)
CREATE OR REPLACE FUNCTION kg_get_all_prerequisites(
    p_course_node_id UUID,
    p_max_depth INTEGER DEFAULT 5
)
RETURNS TABLE (
    node_id UUID,
    node_type VARCHAR,
    label VARCHAR,
    depth INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE prereqs AS (
        -- Base case: direct prerequisites
        SELECT
            n.id AS node_id,
            n.node_type::VARCHAR,
            n.label::VARCHAR,
            1 AS depth
        FROM knowledge_graph_edges e
        JOIN knowledge_graph_nodes n ON e.source_node_id = n.id
        WHERE e.target_node_id = p_course_node_id
          AND e.edge_type = 'prerequisite'

        UNION

        -- Recursive case: prerequisites of prerequisites
        SELECT
            n.id,
            n.node_type::VARCHAR,
            n.label::VARCHAR,
            pr.depth + 1
        FROM prereqs pr
        JOIN knowledge_graph_edges e ON e.target_node_id = pr.node_id
        JOIN knowledge_graph_nodes n ON e.source_node_id = n.id
        WHERE e.edge_type = 'prerequisite'
          AND pr.depth < p_max_depth
    )
    SELECT DISTINCT ON (prereqs.node_id)
        prereqs.node_id,
        prereqs.node_type,
        prereqs.label,
        prereqs.depth
    FROM prereqs
    ORDER BY prereqs.node_id, prereqs.depth;
END;
$$;

-- ========================================
-- COMMENTS
-- ========================================

COMMENT ON TABLE knowledge_graph_nodes IS 'Nodes in the knowledge graph representing courses, skills, concepts, etc.';
COMMENT ON TABLE knowledge_graph_edges IS 'Edges representing relationships between knowledge graph nodes';
COMMENT ON FUNCTION kg_get_neighbors IS 'Get neighboring nodes for a given node';
COMMENT ON FUNCTION kg_find_shortest_path IS 'Find shortest path between two nodes using BFS';
COMMENT ON FUNCTION kg_get_all_prerequisites IS 'Get all prerequisites for a course recursively';
