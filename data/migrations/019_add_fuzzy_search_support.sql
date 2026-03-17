/*
 * Migration 019: Add Fuzzy Search Support
 * Created: 2025-10-05
 * Purpose: Enable fuzzy text matching using PostgreSQL trigram similarity
 *
 * BUSINESS REQUIREMENT:
 * Improve search experience by handling typos, partial matches, and
 * semantic similarity in course and content searches.
 *
 * TECHNICAL APPROACH:
 * - PostgreSQL pg_trgm extension for trigram similarity
 * - GIN indexes for fast fuzzy matching
 * - Similarity threshold-based search functions
 *
 * BENEFITS:
 * - Handles typos: "pyton" → "python"
 * - Partial matches: "prog" → "programming"
 * - Better UX: Students find courses despite imperfect search terms
 */

-- ========================================
-- ENABLE TRIGRAM EXTENSION
-- ========================================

/*
 * pg_trgm extension provides:
 * - similarity(text, text) → float (0.0 to 1.0)
 * - word_similarity(text, text) → float
 * - GIN/GiST indexes for fast similarity search
 */
CREATE EXTENSION IF NOT EXISTS pg_trgm;

COMMENT ON EXTENSION pg_trgm IS 'Trigram similarity for fuzzy text matching in search';

-- ========================================
-- TRIGRAM INDEXES FOR METADATA SEARCH
-- ========================================

/*
 * Add GIN indexes for trigram similarity on searchable fields
 *
 * PERFORMANCE:
 * - Enables fast similarity queries (typo tolerance)
 * - Index size: ~10-20% of text data size
 * - Query speedup: 10-100x for similarity searches
 */

-- Title fuzzy search
CREATE INDEX IF NOT EXISTS idx_entity_metadata_title_trgm
ON entity_metadata USING GIN (title gin_trgm_ops);

-- Description fuzzy search
CREATE INDEX IF NOT EXISTS idx_entity_metadata_description_trgm
ON entity_metadata USING GIN (description gin_trgm_ops);

COMMENT ON INDEX idx_entity_metadata_title_trgm IS 'Trigram index for fuzzy title search';
COMMENT ON INDEX idx_entity_metadata_description_trgm IS 'Trigram index for fuzzy description search';

-- ========================================
-- FUZZY SEARCH FUNCTIONS
-- ========================================

/*
 * Function: Fuzzy search metadata with similarity scoring
 *
 * ALGORITHM:
 * 1. Calculate similarity scores for title, description, tags
 * 2. Use maximum similarity as relevance score
 * 3. Filter by similarity threshold
 * 4. Order by relevance (highest similarity first)
 *
 * SIMILARITY THRESHOLD:
 * - 0.0: No match
 * - 0.3: Loose match (handles significant typos)
 * - 0.5: Medium match (partial word matches)
 * - 0.7: Strong match (close to exact)
 * - 1.0: Exact match
 */
CREATE OR REPLACE FUNCTION search_metadata_fuzzy(
    p_search_term TEXT,
    p_entity_types TEXT[] DEFAULT NULL,
    p_similarity_threshold FLOAT DEFAULT 0.3,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    entity_id UUID,
    entity_type VARCHAR,
    title TEXT,
    description TEXT,
    tags TEXT[],
    keywords TEXT[],
    metadata JSONB,
    similarity_score DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (em.id)
        em.id,
        em.entity_id,
        em.entity_type,
        em.title,
        em.description,
        em.tags,
        em.keywords,
        em.metadata,
        CAST(GREATEST(
            -- Title similarity
            COALESCE(similarity(em.title, p_search_term), 0),
            -- Description similarity
            COALESCE(similarity(em.description, p_search_term), 0),
            -- Maximum similarity across all tags (check each element individually)
            COALESCE((
                SELECT MAX(similarity(tag_elem, p_search_term))
                FROM unnest(em.tags) AS tag_elem
            ), 0),
            -- Maximum similarity across all keywords (check each element individually)
            COALESCE((
                SELECT MAX(similarity(kw_elem, p_search_term))
                FROM unnest(em.keywords) AS kw_elem
            ), 0)
        ) AS DOUBLE PRECISION) AS similarity_score,
        em.created_at,
        em.updated_at,
        em.created_by,
        em.updated_by
    FROM entity_metadata em
    WHERE (
        -- Title matches
        similarity(em.title, p_search_term) > p_similarity_threshold
        OR
        -- Description matches
        similarity(em.description, p_search_term) > p_similarity_threshold
        OR
        -- ANY tag matches (check each element individually for better accuracy)
        EXISTS (
            SELECT 1 FROM unnest(em.tags) AS tag_elem
            WHERE similarity(tag_elem, p_search_term) > p_similarity_threshold
        )
        OR
        -- ANY keyword matches (check each element individually for better accuracy)
        EXISTS (
            SELECT 1 FROM unnest(em.keywords) AS kw_elem
            WHERE similarity(kw_elem, p_search_term) > p_similarity_threshold
        )
    )
    AND (
        -- Filter by entity type if specified
        p_entity_types IS NULL OR em.entity_type = ANY(p_entity_types)
    )
    ORDER BY em.id, similarity_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_metadata_fuzzy IS 'Fuzzy search with trigram similarity scoring';

-- ========================================
-- COURSE SIMILARITY FUNCTION
-- ========================================

/*
 * Function: Calculate similarity between two courses
 *
 * BUSINESS USE CASE:
 * Determine if Course A can substitute for Course B as a prerequisite
 *
 * SIMILARITY FACTORS:
 * - Title similarity (weight: 0.4)
 * - Tag overlap (weight: 0.3)
 * - Keyword overlap (weight: 0.2)
 * - Description similarity (weight: 0.1)
 *
 * RETURNS:
 * Float 0.0 to 1.0 representing similarity confidence
 */
CREATE OR REPLACE FUNCTION calculate_course_similarity(
    p_course_id_1 UUID,
    p_course_id_2 UUID
)
RETURNS FLOAT AS $$
DECLARE
    v_title_sim FLOAT := 0.0;
    v_desc_sim FLOAT := 0.0;
    v_tag_overlap FLOAT := 0.0;
    v_keyword_overlap FLOAT := 0.0;
    v_total_similarity FLOAT := 0.0;

    v_course1_title TEXT;
    v_course1_desc TEXT;
    v_course1_tags TEXT[];
    v_course1_keywords TEXT[];

    v_course2_title TEXT;
    v_course2_desc TEXT;
    v_course2_tags TEXT[];
    v_course2_keywords TEXT[];

    v_common_tags INTEGER;
    v_total_tags INTEGER;
    v_common_keywords INTEGER;
    v_total_keywords INTEGER;
BEGIN
    -- Get course 1 data
    SELECT title, description, tags, keywords
    INTO v_course1_title, v_course1_desc, v_course1_tags, v_course1_keywords
    FROM entity_metadata
    WHERE entity_id = p_course_id_1 AND entity_type = 'course';

    -- Get course 2 data
    SELECT title, description, tags, keywords
    INTO v_course2_title, v_course2_desc, v_course2_tags, v_course2_keywords
    FROM entity_metadata
    WHERE entity_id = p_course_id_2 AND entity_type = 'course';

    -- Return 0 if either course not found
    IF v_course1_title IS NULL OR v_course2_title IS NULL THEN
        RETURN 0.0;
    END IF;

    -- Calculate title similarity (weight: 0.4)
    v_title_sim := similarity(v_course1_title, v_course2_title) * 0.4;

    -- Calculate description similarity (weight: 0.1)
    IF v_course1_desc IS NOT NULL AND v_course2_desc IS NOT NULL THEN
        v_desc_sim := similarity(v_course1_desc, v_course2_desc) * 0.1;
    END IF;

    -- Calculate tag overlap (weight: 0.3)
    IF v_course1_tags IS NOT NULL AND v_course2_tags IS NOT NULL THEN
        v_common_tags := (
            SELECT COUNT(*)
            FROM unnest(v_course1_tags) AS tag
            WHERE tag = ANY(v_course2_tags)
        );
        v_total_tags := (
            SELECT COUNT(DISTINCT tag)
            FROM unnest(v_course1_tags || v_course2_tags) AS tag
        );
        IF v_total_tags > 0 THEN
            v_tag_overlap := (v_common_tags::FLOAT / v_total_tags::FLOAT) * 0.3;
        END IF;
    END IF;

    -- Calculate keyword overlap (weight: 0.2)
    IF v_course1_keywords IS NOT NULL AND v_course2_keywords IS NOT NULL THEN
        v_common_keywords := (
            SELECT COUNT(*)
            FROM unnest(v_course1_keywords) AS kw
            WHERE kw = ANY(v_course2_keywords)
        );
        v_total_keywords := (
            SELECT COUNT(DISTINCT kw)
            FROM unnest(v_course1_keywords || v_course2_keywords) AS kw
        );
        IF v_total_keywords > 0 THEN
            v_keyword_overlap := (v_common_keywords::FLOAT / v_total_keywords::FLOAT) * 0.2;
        END IF;
    END IF;

    -- Total similarity (weighted sum)
    v_total_similarity := v_title_sim + v_desc_sim + v_tag_overlap + v_keyword_overlap;

    RETURN v_total_similarity;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_course_similarity IS 'Calculate weighted similarity score between two courses';

-- ========================================
-- HELPER FUNCTION: Get Similar Courses
-- ========================================

/*
 * Function: Find courses similar to a given course
 *
 * USE CASE:
 * - Find course alternatives/substitutes
 * - Recommend similar courses
 * - Validate prerequisite flexibility
 */
CREATE OR REPLACE FUNCTION get_similar_courses(
    p_course_id UUID,
    p_min_similarity FLOAT DEFAULT 0.5,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    similar_course_id UUID,
    similar_course_title TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.entity_id,
        em.title,
        calculate_course_similarity(p_course_id, em.entity_id) AS similarity_score
    FROM entity_metadata em
    WHERE em.entity_type = 'course'
      AND em.entity_id != p_course_id
      AND calculate_course_similarity(p_course_id, em.entity_id) >= p_min_similarity
    ORDER BY similarity_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_similar_courses IS 'Find courses similar to given course ID';

-- ========================================
-- CONFIGURATION: Set similarity threshold
-- ========================================

/*
 * Global similarity threshold for % operator
 * Default: 0.3 (30% similarity)
 *
 * Allows using: SELECT * FROM table WHERE column % 'search_term'
 */
SET pg_trgm.similarity_threshold = 0.3;

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

/*
 * Test fuzzy search (uncomment to test after data exists):
 *
 * -- Test typo tolerance
 * SELECT * FROM search_metadata_fuzzy('pyton programming', ARRAY['course'], 0.3, 10);
 *
 * -- Test partial match
 * SELECT * FROM search_metadata_fuzzy('prog basics', ARRAY['course'], 0.3, 10);
 *
 * -- Test course similarity
 * -- (Replace UUIDs with actual course IDs)
 * SELECT calculate_course_similarity(
 *     '00000000-0000-0000-0000-000000000001'::UUID,
 *     '00000000-0000-0000-0000-000000000002'::UUID
 * );
 */

-- ========================================
-- INDEXES SUMMARY
-- ========================================

/*
 * New indexes created:
 * 1. idx_entity_metadata_title_trgm - Title fuzzy search
 * 2. idx_entity_metadata_description_trgm - Description fuzzy search
 *
 * Storage overhead: ~15-20% of text data size
 * Query speedup: 10-100x for similarity searches
 */
