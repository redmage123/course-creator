-- Migration 017: Comprehensive Metadata System
-- Created: 2025-10-05
-- Purpose: Add unified metadata management system for enhanced search and discovery

-- ============================================================================
-- 1. ENTITY METADATA TABLE (Core metadata for all entities)
-- ============================================================================

CREATE TABLE IF NOT EXISTS entity_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Entity reference
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'course', 'content', 'user', 'lab', 'project', etc.

    -- Core metadata (JSONB for flexibility)
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Searchable fields (extracted from metadata for performance)
    title TEXT,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    keywords TEXT[] DEFAULT '{}',

    -- Full-text search vector (automatically updated)
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
        setweight(to_tsvector('english', array_to_string(COALESCE(tags, '{}'), ' ')), 'C') ||
        setweight(to_tsvector('english', array_to_string(COALESCE(keywords, '{}'), ' ')), 'D')
    ) STORED,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,

    -- Constraints
    CONSTRAINT unique_entity_metadata UNIQUE (entity_id, entity_type),
    CONSTRAINT entity_metadata_check_type CHECK (
        entity_type IN ('course', 'content', 'user', 'lab', 'project', 'track', 'quiz', 'exercise', 'video', 'slide')
    )
);

-- Indexes for entity_metadata
CREATE INDEX idx_entity_metadata_entity ON entity_metadata(entity_id, entity_type);
CREATE INDEX idx_entity_metadata_type ON entity_metadata(entity_type);
CREATE INDEX idx_entity_metadata_jsonb ON entity_metadata USING GIN (metadata);
CREATE INDEX idx_entity_metadata_tags ON entity_metadata USING GIN (tags);
CREATE INDEX idx_entity_metadata_keywords ON entity_metadata USING GIN (keywords);
CREATE INDEX idx_entity_metadata_search ON entity_metadata USING GIN (search_vector);
CREATE INDEX idx_entity_metadata_created_at ON entity_metadata(created_at DESC);
CREATE INDEX idx_entity_metadata_updated_at ON entity_metadata(updated_at DESC);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_entity_metadata_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_entity_metadata_updated_at
    BEFORE UPDATE ON entity_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_entity_metadata_updated_at();

-- ============================================================================
-- 2. METADATA TAXONOMY TABLE (Hierarchical categorization)
-- ============================================================================

CREATE TABLE IF NOT EXISTS metadata_taxonomy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Taxonomy structure (hierarchical)
    parent_id UUID REFERENCES metadata_taxonomy(id) ON DELETE CASCADE,
    level INTEGER NOT NULL DEFAULT 0,
    path TEXT NOT NULL,  -- Materialized path: 'programming/python/web-development'

    -- Taxonomy details
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    taxonomy_type VARCHAR(50) NOT NULL,  -- 'subject', 'skill', 'industry', 'topic', 'certification'

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,

    -- Ordering
    sort_order INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_taxonomy_path UNIQUE (path),
    CONSTRAINT taxonomy_type_check CHECK (
        taxonomy_type IN ('subject', 'skill', 'industry', 'topic', 'certification', 'tool', 'framework')
    )
);

-- Indexes for metadata_taxonomy
CREATE INDEX idx_taxonomy_parent ON metadata_taxonomy(parent_id);
CREATE INDEX idx_taxonomy_path ON metadata_taxonomy(path);
CREATE INDEX idx_taxonomy_type ON metadata_taxonomy(taxonomy_type);
CREATE INDEX idx_taxonomy_level ON metadata_taxonomy(level);
CREATE INDEX idx_taxonomy_active ON metadata_taxonomy(is_active) WHERE is_active = true;
CREATE INDEX idx_taxonomy_usage ON metadata_taxonomy(usage_count DESC);

-- Trigger to update updated_at
CREATE TRIGGER trigger_update_taxonomy_updated_at
    BEFORE UPDATE ON metadata_taxonomy
    FOR EACH ROW
    EXECUTE FUNCTION update_entity_metadata_updated_at();

-- Function to update taxonomy level and path
CREATE OR REPLACE FUNCTION update_taxonomy_hierarchy()
RETURNS TRIGGER AS $$
DECLARE
    parent_path TEXT;
    parent_level INTEGER;
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.level = 0;
        NEW.path = NEW.name;
    ELSE
        SELECT level, path INTO parent_level, parent_path
        FROM metadata_taxonomy
        WHERE id = NEW.parent_id;

        NEW.level = parent_level + 1;
        NEW.path = parent_path || '/' || NEW.name;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_taxonomy_hierarchy
    BEFORE INSERT OR UPDATE ON metadata_taxonomy
    FOR EACH ROW
    EXECUTE FUNCTION update_taxonomy_hierarchy();

-- ============================================================================
-- 3. METADATA RELATIONSHIPS TABLE (Entity relationships)
-- ============================================================================

CREATE TABLE IF NOT EXISTS metadata_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source and target entities
    source_entity_id UUID NOT NULL,
    source_entity_type VARCHAR(50) NOT NULL,
    target_entity_id UUID NOT NULL,
    target_entity_type VARCHAR(50) NOT NULL,

    -- Relationship details
    relationship_type VARCHAR(100) NOT NULL,  -- 'prerequisite', 'related', 'part_of', 'similar_to', 'next_in_path'
    strength DECIMAL(3,2) DEFAULT 0.5 CHECK (strength >= 0.0 AND strength <= 1.0),  -- 0.0 to 1.0
    bidirectional BOOLEAN DEFAULT false,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    -- Constraints
    CONSTRAINT unique_relationship UNIQUE (
        source_entity_id, source_entity_type,
        target_entity_id, target_entity_type,
        relationship_type
    ),
    CONSTRAINT no_self_reference CHECK (
        NOT (source_entity_id = target_entity_id AND source_entity_type = target_entity_type)
    ),
    CONSTRAINT relationship_type_check CHECK (
        relationship_type IN (
            'prerequisite', 'related', 'part_of', 'similar_to',
            'next_in_path', 'alternative', 'complementary', 'deprecated_by'
        )
    )
);

-- Indexes for metadata_relationships
CREATE INDEX idx_relationships_source ON metadata_relationships(source_entity_id, source_entity_type);
CREATE INDEX idx_relationships_target ON metadata_relationships(target_entity_id, target_entity_type);
CREATE INDEX idx_relationships_type ON metadata_relationships(relationship_type);
CREATE INDEX idx_relationships_strength ON metadata_relationships(strength DESC);
CREATE INDEX idx_relationships_active ON metadata_relationships(is_active) WHERE is_active = true;
CREATE INDEX idx_relationships_bidirectional ON metadata_relationships(bidirectional) WHERE bidirectional = true;

-- Trigger to update updated_at
CREATE TRIGGER trigger_update_relationships_updated_at
    BEFORE UPDATE ON metadata_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_entity_metadata_updated_at();

-- ============================================================================
-- 4. METADATA HISTORY TABLE (Versioning and audit)
-- ============================================================================

CREATE TABLE IF NOT EXISTS metadata_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to metadata
    metadata_id UUID NOT NULL REFERENCES entity_metadata(id) ON DELETE CASCADE,

    -- Historical data
    metadata_snapshot JSONB NOT NULL,
    change_type VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'deleted', 'restored'

    -- Change details
    changed_fields TEXT[],  -- Array of changed field names
    change_description TEXT,

    -- User tracking
    changed_by UUID,
    change_source VARCHAR(100),  -- 'manual', 'ai_extraction', 'api', 'batch_import'

    -- Timestamps
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT change_type_check CHECK (
        change_type IN ('created', 'updated', 'deleted', 'restored', 'merged')
    )
);

-- Indexes for metadata_history
CREATE INDEX idx_metadata_history_id ON metadata_history(metadata_id);
CREATE INDEX idx_metadata_history_changed_at ON metadata_history(changed_at DESC);
CREATE INDEX idx_metadata_history_changed_by ON metadata_history(changed_by);
CREATE INDEX idx_metadata_history_type ON metadata_history(change_type);
CREATE INDEX idx_metadata_history_source ON metadata_history(change_source);

-- ============================================================================
-- 5. ADD METADATA COLUMNS TO EXISTING TABLES
-- ============================================================================

-- Add metadata JSONB column to courses if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'courses' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE courses ADD COLUMN metadata JSONB DEFAULT '{}';
        CREATE INDEX idx_courses_metadata ON courses USING GIN (metadata);
    END IF;
END $$;

-- Add metadata JSONB column to users if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE users ADD COLUMN metadata JSONB DEFAULT '{}';
        CREATE INDEX idx_users_metadata ON users USING GIN (metadata);
    END IF;
END $$;

-- Add metadata JSONB column to projects if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE projects ADD COLUMN metadata JSONB DEFAULT '{}';
        CREATE INDEX idx_projects_metadata ON projects USING GIN (metadata);
    END IF;
END $$;

-- ============================================================================
-- 6. HELPER FUNCTIONS FOR METADATA OPERATIONS
-- ============================================================================

-- Function to search metadata using full-text search
CREATE OR REPLACE FUNCTION search_metadata(
    search_query TEXT,
    entity_types TEXT[] DEFAULT NULL,
    limit_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    entity_id UUID,
    entity_type VARCHAR(50),
    title TEXT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.entity_id,
        em.entity_type,
        em.title,
        ts_rank(em.search_vector, to_tsquery('english', search_query)) AS rank
    FROM entity_metadata em
    WHERE em.search_vector @@ to_tsquery('english', search_query)
        AND (entity_types IS NULL OR em.entity_type = ANY(entity_types))
    ORDER BY rank DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Function to get related entities
CREATE OR REPLACE FUNCTION get_related_entities(
    p_entity_id UUID,
    p_entity_type VARCHAR(50),
    p_relationship_types TEXT[] DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    entity_id UUID,
    entity_type VARCHAR(50),
    relationship_type VARCHAR(100),
    strength DECIMAL(3,2),
    title TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        mr.target_entity_id AS entity_id,
        mr.target_entity_type AS entity_type,
        mr.relationship_type,
        mr.strength,
        em.title
    FROM metadata_relationships mr
    LEFT JOIN entity_metadata em ON em.entity_id = mr.target_entity_id
        AND em.entity_type = mr.target_entity_type
    WHERE mr.source_entity_id = p_entity_id
        AND mr.source_entity_type = p_entity_type
        AND mr.is_active = true
        AND (p_relationship_types IS NULL OR mr.relationship_type = ANY(p_relationship_types))
    ORDER BY mr.strength DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get taxonomy tree
CREATE OR REPLACE FUNCTION get_taxonomy_tree(
    p_taxonomy_type VARCHAR(50),
    p_parent_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    parent_id UUID,
    name VARCHAR(255),
    display_name VARCHAR(255),
    path TEXT,
    level INTEGER,
    usage_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE taxonomy_tree AS (
        -- Base case: get root or specified parent
        SELECT
            t.id, t.parent_id, t.name, t.display_name,
            t.path, t.level, t.usage_count
        FROM metadata_taxonomy t
        WHERE t.taxonomy_type = p_taxonomy_type
            AND (
                (p_parent_id IS NULL AND t.parent_id IS NULL) OR
                (p_parent_id IS NOT NULL AND t.parent_id = p_parent_id)
            )
            AND t.is_active = true

        UNION ALL

        -- Recursive case: get children
        SELECT
            t.id, t.parent_id, t.name, t.display_name,
            t.path, t.level, t.usage_count
        FROM metadata_taxonomy t
        INNER JOIN taxonomy_tree tt ON t.parent_id = tt.id
        WHERE t.is_active = true
    )
    SELECT * FROM taxonomy_tree
    ORDER BY level, sort_order, name;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. INITIAL TAXONOMY DATA (Seed data)
-- ============================================================================

-- Insert core subject taxonomies
INSERT INTO metadata_taxonomy (name, display_name, taxonomy_type, description, sort_order) VALUES
    ('programming', 'Programming', 'subject', 'Software programming and development', 1),
    ('data-science', 'Data Science', 'subject', 'Data analysis and machine learning', 2),
    ('web-development', 'Web Development', 'subject', 'Frontend and backend web development', 3),
    ('devops', 'DevOps', 'subject', 'DevOps and infrastructure', 4),
    ('cybersecurity', 'Cybersecurity', 'subject', 'Security and ethical hacking', 5),
    ('cloud', 'Cloud Computing', 'subject', 'Cloud platforms and services', 6),
    ('mobile', 'Mobile Development', 'subject', 'iOS and Android development', 7),
    ('ai-ml', 'AI/ML', 'subject', 'Artificial Intelligence and Machine Learning', 8)
ON CONFLICT (path) DO NOTHING;

-- Insert skill level taxonomies
INSERT INTO metadata_taxonomy (name, display_name, taxonomy_type, description, sort_order) VALUES
    ('beginner', 'Beginner', 'skill', 'Entry level skills', 1),
    ('intermediate', 'Intermediate', 'skill', 'Intermediate level skills', 2),
    ('advanced', 'Advanced', 'skill', 'Advanced level skills', 3),
    ('expert', 'Expert', 'skill', 'Expert level skills', 4)
ON CONFLICT (path) DO NOTHING;

-- ============================================================================
-- 8. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE entity_metadata IS 'Unified metadata storage for all platform entities';
COMMENT ON TABLE metadata_taxonomy IS 'Hierarchical taxonomy for content categorization';
COMMENT ON TABLE metadata_relationships IS 'Relationships between entities for recommendations';
COMMENT ON TABLE metadata_history IS 'Audit trail for metadata changes';

COMMENT ON COLUMN entity_metadata.metadata IS 'Flexible JSONB storage for entity-specific metadata';
COMMENT ON COLUMN entity_metadata.search_vector IS 'Automatically generated full-text search index';
COMMENT ON COLUMN metadata_taxonomy.path IS 'Materialized path for hierarchical queries';
COMMENT ON COLUMN metadata_relationships.strength IS 'Relationship strength from 0.0 (weak) to 1.0 (strong)';

-- ============================================================================
-- Migration Complete
-- ============================================================================
