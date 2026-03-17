-- Migration: Materialized Views and Full-Text Search Enhancements
-- Purpose: Add analytics materialized views and enhance full-text search for course materials
-- Date: 2025-10-07

-- ============================================================================
-- PART 1: FULL-TEXT SEARCH ENHANCEMENTS
-- ============================================================================

-- Add entity type for course material tracking
ALTER TABLE entity_metadata
    ADD COLUMN IF NOT EXISTS entity_type_enhanced VARCHAR(100);

UPDATE entity_metadata
SET entity_type_enhanced = entity_type
WHERE entity_type_enhanced IS NULL;

-- Create GIN index on tags array for fast tag-based queries
CREATE INDEX IF NOT EXISTS idx_entity_metadata_tags_gin
ON entity_metadata USING GIN (tags);

-- Create GIN index on keywords array for fast keyword searches
CREATE INDEX IF NOT EXISTS idx_entity_metadata_keywords_gin
ON entity_metadata USING GIN (keywords);

-- Create composite index for entity_type filtering
CREATE INDEX IF NOT EXISTS idx_entity_metadata_entity_type_created
ON entity_metadata (entity_type, created_at DESC);

-- Enhance the search_vector trigger function to include metadata fields
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    -- Extract searchable text from JSONB metadata
    -- Prioritize: title (A), description (B), tags (C), keywords (C), metadata fields (D)
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.keywords, ' '), '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(
            -- Extract filename from metadata
            NEW.metadata->>'filename', ''
        )), 'D') ||
        setweight(to_tsvector('english', COALESCE(
            -- Extract file_type from metadata
            NEW.metadata->>'file_type', ''
        )), 'D');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Ensure trigger exists and is using the updated function
DROP TRIGGER IF EXISTS trigger_update_search_vector ON entity_metadata;
CREATE TRIGGER trigger_update_search_vector
    BEFORE INSERT OR UPDATE ON entity_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Create GIN index on search_vector for fast full-text search
CREATE INDEX IF NOT EXISTS idx_entity_metadata_search_vector
ON entity_metadata USING GIN (search_vector);

-- ============================================================================
-- PART 2: MATERIALIZED VIEW - FILE UPLOAD ANALYTICS
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_file_upload_analytics AS
SELECT
    -- Course information
    (metadata->>'course_id')::INTEGER AS course_id,

    -- File type breakdown
    metadata->>'file_type' AS file_type,

    -- User role (instructor vs student uploads)
    CASE
        WHEN 'instructor_upload' = ANY(tags) THEN 'instructor'
        WHEN 'student_upload' = ANY(tags) THEN 'student'
        ELSE 'unknown'
    END AS uploader_role,

    -- Aggregated metrics
    COUNT(*) AS total_uploads,
    SUM((metadata->>'file_size_bytes')::BIGINT) AS total_bytes,
    AVG((metadata->>'file_size_bytes')::BIGINT) AS avg_file_size_bytes,
    MIN(created_at) AS first_upload_at,
    MAX(created_at) AS last_upload_at,

    -- Unique uploaders
    COUNT(DISTINCT metadata->>'instructor_id') AS unique_instructors,
    COUNT(DISTINCT metadata->>'student_id') AS unique_students,

    -- Recent activity (last 7 days)
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS uploads_last_7_days,
    SUM((metadata->>'file_size_bytes')::BIGINT) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS bytes_last_7_days,

    -- Recent activity (last 30 days)
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS uploads_last_30_days,
    SUM((metadata->>'file_size_bytes')::BIGINT) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS bytes_last_30_days

FROM entity_metadata
WHERE entity_type = 'course_material_upload'
    AND metadata ? 'course_id'  -- Ensure course_id exists in metadata
GROUP BY
    course_id,
    file_type,
    uploader_role;

-- Create UNIQUE index for concurrent refresh capability
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_upload_unique
ON mv_file_upload_analytics (course_id, file_type, uploader_role);

-- Create additional indexes on materialized view for fast queries
CREATE INDEX IF NOT EXISTS idx_mv_upload_course_id
ON mv_file_upload_analytics (course_id);

CREATE INDEX IF NOT EXISTS idx_mv_upload_file_type
ON mv_file_upload_analytics (file_type);

CREATE INDEX IF NOT EXISTS idx_mv_upload_role
ON mv_file_upload_analytics (uploader_role);

-- ============================================================================
-- PART 3: MATERIALIZED VIEW - FILE DOWNLOAD ANALYTICS
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_file_download_analytics AS
SELECT
    -- Course information
    (metadata->>'course_id')::INTEGER AS course_id,

    -- File type breakdown
    metadata->>'file_type' AS file_type,

    -- User role (instructor vs student downloads)
    CASE
        WHEN 'instructor_download' = ANY(tags) THEN 'instructor'
        WHEN 'student_download' = ANY(tags) THEN 'student'
        ELSE 'unknown'
    END AS downloader_role,

    -- Aggregated metrics
    COUNT(*) AS total_downloads,
    SUM((metadata->>'file_size_bytes')::BIGINT) AS total_bytes,
    AVG((metadata->>'file_size_bytes')::BIGINT) AS avg_file_size_bytes,
    MIN(created_at) AS first_download_at,
    MAX(created_at) AS last_download_at,

    -- Unique downloaders
    COUNT(DISTINCT metadata->>'instructor_id') AS unique_instructors,
    COUNT(DISTINCT metadata->>'student_id') AS unique_students,

    -- Recent activity (last 7 days)
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS downloads_last_7_days,
    SUM((metadata->>'file_size_bytes')::BIGINT) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS bytes_last_7_days,

    -- Recent activity (last 30 days)
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS downloads_last_30_days,
    SUM((metadata->>'file_size_bytes')::BIGINT) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS bytes_last_30_days,

    -- Popular files (most downloaded)
    mode() WITHIN GROUP (ORDER BY metadata->>'filename') AS most_downloaded_filename

FROM entity_metadata
WHERE entity_type = 'course_material_download'
    AND metadata ? 'course_id'
GROUP BY
    course_id,
    file_type,
    downloader_role;

-- Create UNIQUE index for concurrent refresh capability
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_download_unique
ON mv_file_download_analytics (course_id, file_type, downloader_role);

-- Create additional indexes on download analytics materialized view
CREATE INDEX IF NOT EXISTS idx_mv_download_course_id
ON mv_file_download_analytics (course_id);

CREATE INDEX IF NOT EXISTS idx_mv_download_file_type
ON mv_file_download_analytics (file_type);

CREATE INDEX IF NOT EXISTS idx_mv_download_role
ON mv_file_download_analytics (downloader_role);

-- ============================================================================
-- PART 4: MATERIALIZED VIEW - COMBINED UPLOAD/DOWNLOAD SUMMARY
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_course_material_summary AS
SELECT
    COALESCE(u.course_id, d.course_id) AS course_id,
    COALESCE(u.file_type, d.file_type) AS file_type,

    -- Upload metrics
    COALESCE(u.total_uploads, 0) AS total_uploads,
    COALESCE(u.total_bytes, 0) AS total_upload_bytes,
    COALESCE(u.uploads_last_7_days, 0) AS uploads_last_7_days,
    COALESCE(u.uploads_last_30_days, 0) AS uploads_last_30_days,

    -- Download metrics
    COALESCE(d.total_downloads, 0) AS total_downloads,
    COALESCE(d.total_bytes, 0) AS total_download_bytes,
    COALESCE(d.downloads_last_7_days, 0) AS downloads_last_7_days,
    COALESCE(d.downloads_last_30_days, 0) AS downloads_last_30_days,

    -- Engagement ratio (downloads per upload)
    CASE
        WHEN COALESCE(u.total_uploads, 0) > 0
        THEN ROUND(COALESCE(d.total_downloads, 0)::NUMERIC / u.total_uploads, 2)
        ELSE 0
    END AS downloads_per_upload,

    -- Unique users
    COALESCE(u.unique_instructors, 0) AS uploading_instructors,
    COALESCE(d.unique_students, 0) AS downloading_students,

    -- Activity dates
    LEAST(u.first_upload_at, d.first_download_at) AS first_activity_at,
    GREATEST(u.last_upload_at, d.last_download_at) AS last_activity_at

FROM mv_file_upload_analytics u
FULL OUTER JOIN mv_file_download_analytics d
    ON u.course_id = d.course_id
    AND u.file_type = d.file_type;

-- Create UNIQUE index for concurrent refresh capability
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_summary_unique
ON mv_course_material_summary (course_id, file_type);

-- Create additional indexes on summary materialized view
CREATE INDEX IF NOT EXISTS idx_mv_summary_course_id
ON mv_course_material_summary (course_id);

CREATE INDEX IF NOT EXISTS idx_mv_summary_file_type
ON mv_course_material_summary (file_type);

CREATE INDEX IF NOT EXISTS idx_mv_summary_engagement
ON mv_course_material_summary (downloads_per_upload DESC);

-- ============================================================================
-- PART 5: MATERIALIZED VIEW REFRESH FUNCTION
-- ============================================================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_course_material_analytics()
RETURNS void AS $$
BEGIN
    -- Refresh in dependency order (summary depends on upload/download)
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_file_upload_analytics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_file_download_analytics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_course_material_summary;

    RAISE NOTICE 'All course material analytics materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 6: HELPER FUNCTIONS FOR FULL-TEXT SEARCH
-- ============================================================================

-- Function for ranked full-text search with highlighting
CREATE OR REPLACE FUNCTION search_course_materials(
    search_query TEXT,
    entity_type_filter TEXT DEFAULT NULL,
    course_id_filter INTEGER DEFAULT NULL,
    limit_results INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    entity_id UUID,
    entity_type VARCHAR,
    title TEXT,
    description TEXT,
    tags TEXT[],
    filename TEXT,
    file_type TEXT,
    course_id INTEGER,
    rank REAL,
    headline TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.id,
        em.entity_id,
        em.entity_type,
        em.title,
        em.description,
        em.tags,
        em.metadata->>'filename' AS filename,
        em.metadata->>'file_type' AS file_type,
        (em.metadata->>'course_id')::INTEGER AS course_id,
        ts_rank(em.search_vector, to_tsquery('english', search_query)) AS rank,
        ts_headline('english', COALESCE(em.title || ' ' || em.description, ''),
                    to_tsquery('english', search_query),
                    'MaxWords=50, MinWords=25') AS headline
    FROM entity_metadata em
    WHERE em.search_vector @@ to_tsquery('english', search_query)
        AND (entity_type_filter IS NULL OR em.entity_type = entity_type_filter)
        AND (course_id_filter IS NULL OR (em.metadata->>'course_id')::INTEGER = course_id_filter)
    ORDER BY rank DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Function for fuzzy matching (similarity search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_entity_metadata_title_trgm
ON entity_metadata USING GIN (title gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_entity_metadata_description_trgm
ON entity_metadata USING GIN (description gin_trgm_ops);

-- Fuzzy search function with similarity scoring
CREATE OR REPLACE FUNCTION fuzzy_search_course_materials(
    search_text TEXT,
    similarity_threshold REAL DEFAULT 0.3,
    limit_results INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    entity_id UUID,
    entity_type VARCHAR,
    title TEXT,
    description TEXT,
    filename TEXT,
    file_type TEXT,
    course_id INTEGER,
    title_similarity REAL,
    desc_similarity REAL,
    combined_similarity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.id,
        em.entity_id,
        em.entity_type,
        em.title,
        em.description,
        em.metadata->>'filename' AS filename,
        em.metadata->>'file_type' AS file_type,
        (em.metadata->>'course_id')::INTEGER AS course_id,
        similarity(COALESCE(em.title, ''), search_text) AS title_similarity,
        similarity(COALESCE(em.description, ''), search_text) AS desc_similarity,
        (
            similarity(COALESCE(em.title, ''), search_text) * 0.7 +
            similarity(COALESCE(em.description, ''), search_text) * 0.3
        ) AS combined_similarity
    FROM entity_metadata em
    WHERE (
        similarity(COALESCE(em.title, ''), search_text) > similarity_threshold OR
        similarity(COALESCE(em.description, ''), search_text) > similarity_threshold
    )
    ORDER BY combined_similarity DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 7: INITIAL DATA REFRESH
-- ============================================================================

-- Perform initial refresh of materialized views
SELECT refresh_course_material_analytics();

-- ============================================================================
-- PART 8: COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON MATERIALIZED VIEW mv_file_upload_analytics IS
'Analytics for file uploads aggregated by course, file type, and uploader role. Includes recent activity metrics.';

COMMENT ON MATERIALIZED VIEW mv_file_download_analytics IS
'Analytics for file downloads aggregated by course, file type, and downloader role. Includes engagement metrics.';

COMMENT ON MATERIALIZED VIEW mv_course_material_summary IS
'Combined upload/download summary with engagement ratios and activity tracking.';

COMMENT ON FUNCTION refresh_course_material_analytics() IS
'Refreshes all course material analytics materialized views. Should be called periodically (e.g., hourly or daily).';

COMMENT ON FUNCTION search_course_materials(TEXT, TEXT, INTEGER, INTEGER) IS
'Full-text search for course materials with ranking and highlighting. Supports entity type and course ID filtering.';

COMMENT ON FUNCTION fuzzy_search_course_materials(TEXT, REAL, INTEGER) IS
'Fuzzy similarity search for course materials using trigram matching. Useful for typo-tolerant searches.';
