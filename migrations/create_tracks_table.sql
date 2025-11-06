-- Migration: Create Base Tracks Table
-- Version: 1.0
-- Date: 2025-10-15
-- Author: TDD Implementation
--
-- BUSINESS PURPOSE:
-- Create the foundational tracks table that supports flexible hierarchy
-- allowing tracks to belong to either main projects OR sub-projects
--
-- FEATURES:
-- - Tracks can belong to main project (project_id) OR sub-project (sub_project_id)
-- - XOR constraint ensures tracks reference one parent only
-- - Support for difficulty levels, status tracking, and metadata
-- - Slug-based URLs for SEO-friendly track pages
-- - Comprehensive audit trail with timestamps

-- ==============================================================================
-- STEP 1: Create Base Tracks Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Organization context (required for multi-tenancy)
    -- Note: No FK constraint since organizations table doesn't exist yet
    organization_id UUID NOT NULL,

    -- Flexible parent reference (project OR sub-project, not both)
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    sub_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Track identity
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,

    -- Track metadata
    difficulty VARCHAR(50) DEFAULT 'beginner' CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')),
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived', 'deprecated')),

    -- Estimated completion time (in hours)
    estimated_hours INTEGER,

    -- Track ordering within parent project/sub-project
    display_order INTEGER DEFAULT 0,

    -- Audit trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Note: No FK constraints for created_by/updated_by since users table doesn't exist yet
    created_by UUID,
    updated_by UUID,

    -- Unique constraint: slug must be unique within organization
    CONSTRAINT unique_track_slug_per_org UNIQUE(organization_id, slug)
);

-- ==============================================================================
-- STEP 2: Add XOR Constraint (Project OR Sub-Project)
-- ==============================================================================

-- Enforce business rule: Track must reference EITHER project_id OR sub_project_id
-- This allows tracks to go directly under main projects OR under sub-projects
ALTER TABLE tracks
    ADD CONSTRAINT check_track_parent_reference CHECK (
        (project_id IS NOT NULL AND sub_project_id IS NULL) OR
        (project_id IS NULL AND sub_project_id IS NOT NULL)
    );

COMMENT ON CONSTRAINT check_track_parent_reference ON tracks IS
    'Enforce that track belongs to EITHER project OR sub-project, not both or neither (XOR constraint)';

-- ==============================================================================
-- STEP 3: Create Indexes for Query Performance
-- ==============================================================================

-- Index for querying tracks by main project
CREATE INDEX IF NOT EXISTS idx_tracks_project_id
    ON tracks(project_id)
    WHERE project_id IS NOT NULL;

-- Index for querying tracks by sub-project
CREATE INDEX IF NOT EXISTS idx_tracks_subproject_id
    ON tracks(sub_project_id)
    WHERE sub_project_id IS NOT NULL;

-- Index for querying tracks by organization
CREATE INDEX IF NOT EXISTS idx_tracks_organization_id
    ON tracks(organization_id);

-- Index for filtering by status
CREATE INDEX IF NOT EXISTS idx_tracks_status
    ON tracks(status)
    WHERE status = 'active';

-- Index for filtering by difficulty
CREATE INDEX IF NOT EXISTS idx_tracks_difficulty
    ON tracks(difficulty);

-- Index for ordering tracks
CREATE INDEX IF NOT EXISTS idx_tracks_display_order
    ON tracks(display_order);

-- Index for audit queries
CREATE INDEX IF NOT EXISTS idx_tracks_created_by
    ON tracks(created_by)
    WHERE created_by IS NOT NULL;

-- ==============================================================================
-- STEP 4: Create Trigger for Updated Timestamp
-- ==============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_tracks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on every UPDATE
CREATE TRIGGER tracks_updated_at_trigger
BEFORE UPDATE ON tracks
FOR EACH ROW
EXECUTE FUNCTION update_tracks_updated_at();

COMMENT ON FUNCTION update_tracks_updated_at() IS
    'Automatically update updated_at timestamp when track is modified';

-- ==============================================================================
-- STEP 5: Add Table and Column Comments
-- ==============================================================================

COMMENT ON TABLE tracks IS
    'Learning tracks that organize courses into structured learning paths. Can belong to main project or sub-project.';

COMMENT ON COLUMN tracks.organization_id IS
    'Reference to organization that owns this track (multi-tenancy)';

COMMENT ON COLUMN tracks.project_id IS
    'Reference to main project (NULL if track belongs to sub-project)';

COMMENT ON COLUMN tracks.sub_project_id IS
    'Reference to sub-project (NULL if track belongs to main project)';

COMMENT ON COLUMN tracks.name IS
    'Display name of the track (e.g., "Python Fundamentals", "DevOps Engineer Path")';

COMMENT ON COLUMN tracks.slug IS
    'URL-safe identifier for track (e.g., "python-fundamentals")';

COMMENT ON COLUMN tracks.description IS
    'Detailed description of track content, learning objectives, and target audience';

COMMENT ON COLUMN tracks.difficulty IS
    'Difficulty level: beginner, intermediate, advanced, expert';

COMMENT ON COLUMN tracks.status IS
    'Track lifecycle status: draft, active, archived, deprecated';

COMMENT ON COLUMN tracks.estimated_hours IS
    'Estimated time to complete track in hours';

COMMENT ON COLUMN tracks.display_order IS
    'Sort order for displaying tracks within parent project/sub-project';

-- ==============================================================================
-- STEP 6: Grant Permissions
-- ==============================================================================

-- Grant permissions to application role (assuming 'course_creator_app' role exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'course_creator_app') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON tracks TO course_creator_app;
    END IF;
END $$;

-- ==============================================================================
-- STEP 7: Create Sample Validation View
-- ==============================================================================

-- View to validate track parent references
CREATE OR REPLACE VIEW track_parent_validation AS
SELECT
    t.id AS track_id,
    t.name AS track_name,
    t.organization_id,
    t.project_id,
    t.sub_project_id,
    CASE
        WHEN t.project_id IS NOT NULL AND t.sub_project_id IS NULL THEN 'Main Project'
        WHEN t.project_id IS NULL AND t.sub_project_id IS NOT NULL THEN 'Sub-Project'
        ELSE 'INVALID: Both or Neither'
    END AS parent_type,
    COALESCE(p1.name, p2.name) AS parent_name
FROM tracks t
LEFT JOIN projects p1 ON t.project_id = p1.id
LEFT JOIN projects p2 ON t.sub_project_id = p2.id;

COMMENT ON VIEW track_parent_validation IS
    'Validation view showing track parent relationships for debugging and verification';

-- ==============================================================================
-- STEP 8: Migration Complete - Add Version Record
-- ==============================================================================

-- Create migrations tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Record this migration
INSERT INTO schema_migrations (version, description)
VALUES ('20251015_create_tracks_table', 'Create base tracks table with flexible project/sub-project hierarchy')
ON CONFLICT (version) DO NOTHING;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

-- Verify migration
DO $$
BEGIN
    RAISE NOTICE 'Base tracks table migration completed successfully!';
    RAISE NOTICE 'Table created: tracks';
    RAISE NOTICE 'Constraints: XOR (project OR sub-project), unique slug per org';
    RAISE NOTICE 'Indexes: 7 indexes for query optimization';
    RAISE NOTICE 'Triggers: auto-update updated_at timestamp';
    RAISE NOTICE 'Views: track_parent_validation for debugging';
END $$;
