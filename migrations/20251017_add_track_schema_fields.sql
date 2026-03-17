-- Migration: Add missing Track entity fields to tracks table
-- Date: 2025-10-17
-- Purpose: Update tracks table schema to match Track entity definition
--
-- BUSINESS CONTEXT:
-- The Track entity was designed with rich features (project association, sequencing,
-- skill tracking, enrollment limits) but the database table only had basic fields.
-- This migration adds all missing columns to enable full Track entity functionality.
--
-- CHANGES:
-- 1. Add project_id and sub_project_id for flexible hierarchy
-- 2. Add XOR constraint (track belongs to project OR sub-project, not both)
-- 3. Add slug for URL-safe identifiers
-- 4. Add track_type (sequential, flexible, milestone_based)
-- 5. Add JSONB fields for target_audience and skills_taught
-- 6. Add duration_weeks and max_students for enrollment management
-- 7. Add display_order for sequencing within parent
-- 8. Add auto_enroll_enabled for automated enrollment
-- 9. Add status (draft, active, completed, archived)
-- 10. Add settings JSONB for extensibility
-- 11. Add created_by for audit trail

BEGIN;

-- Step 1: Add new columns (all nullable initially for safe migration)
ALTER TABLE course_creator.tracks
    ADD COLUMN IF NOT EXISTS project_id UUID,
    ADD COLUMN IF NOT EXISTS sub_project_id UUID,
    ADD COLUMN IF NOT EXISTS slug VARCHAR(255),
    ADD COLUMN IF NOT EXISTS track_type VARCHAR(50) DEFAULT 'sequential',
    ADD COLUMN IF NOT EXISTS target_audience JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS duration_weeks INTEGER,
    ADD COLUMN IF NOT EXISTS max_students INTEGER,
    ADD COLUMN IF NOT EXISTS skills_taught JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS auto_enroll_enabled BOOLEAN DEFAULT true,
    ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft',
    ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_by UUID;

-- Step 2: Migrate existing data
-- For existing tracks, generate slugs from names and set to active status
UPDATE course_creator.tracks
SET
    slug = LOWER(REGEXP_REPLACE(REGEXP_REPLACE(name, '[^a-zA-Z0-9\s-]', '', 'g'), '\s+', '-', 'g'))
    WHERE slug IS NULL;

-- Set existing tracks to active status (they were implicitly active via is_active=true)
UPDATE course_creator.tracks
SET status = CASE
    WHEN is_active = true THEN 'active'
    WHEN is_active = false THEN 'archived'
    ELSE 'draft'
END
WHERE status = 'draft';

-- Step 3: Add foreign key constraints
ALTER TABLE course_creator.tracks
    ADD CONSTRAINT fk_tracks_project FOREIGN KEY (project_id)
        REFERENCES course_creator.projects(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_tracks_sub_project FOREIGN KEY (sub_project_id)
        REFERENCES course_creator.sub_projects(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_tracks_created_by FOREIGN KEY (created_by)
        REFERENCES course_creator.users(id) ON DELETE SET NULL;

-- Step 4: Add XOR constraint (track must belong to project OR sub-project, not both or neither)
-- BUSINESS RULE: Flexible hierarchy - track belongs to main project OR sub-project
ALTER TABLE course_creator.tracks
    ADD CONSTRAINT chk_tracks_parent_xor CHECK (
        (project_id IS NOT NULL AND sub_project_id IS NULL) OR
        (project_id IS NULL AND sub_project_id IS NOT NULL)
    );

-- Step 5: Add unique constraint for slug within organization
-- BUSINESS RULE: Slugs must be unique within organization for URL routing
ALTER TABLE course_creator.tracks
    ADD CONSTRAINT uq_tracks_organization_slug UNIQUE (organization_id, slug);

-- Step 6: Add check constraints for data validation
ALTER TABLE course_creator.tracks
    ADD CONSTRAINT chk_tracks_duration_weeks CHECK (duration_weeks IS NULL OR (duration_weeks >= 1 AND duration_weeks <= 104)),
    ADD CONSTRAINT chk_tracks_max_students CHECK (max_students IS NULL OR max_students >= 1),
    ADD CONSTRAINT chk_tracks_display_order CHECK (display_order >= 0),
    ADD CONSTRAINT chk_tracks_status CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    ADD CONSTRAINT chk_tracks_track_type CHECK (track_type IN ('sequential', 'flexible', 'milestone_based'));

-- Step 7: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tracks_project_id ON course_creator.tracks(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tracks_sub_project_id ON course_creator.tracks(sub_project_id) WHERE sub_project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tracks_slug ON course_creator.tracks(slug);
CREATE INDEX IF NOT EXISTS idx_tracks_status ON course_creator.tracks(status);
CREATE INDEX IF NOT EXISTS idx_tracks_display_order ON course_creator.tracks(display_order);
CREATE INDEX IF NOT EXISTS idx_tracks_created_by ON course_creator.tracks(created_by) WHERE created_by IS NOT NULL;

-- Step 8: Add comments for documentation
COMMENT ON COLUMN course_creator.tracks.project_id IS 'Parent project ID (XOR with sub_project_id)';
COMMENT ON COLUMN course_creator.tracks.sub_project_id IS 'Parent sub-project ID (XOR with project_id)';
COMMENT ON COLUMN course_creator.tracks.slug IS 'URL-safe identifier unique within organization';
COMMENT ON COLUMN course_creator.tracks.track_type IS 'Learning path type: sequential, flexible, or milestone_based';
COMMENT ON COLUMN course_creator.tracks.target_audience IS 'JSON array of target audience roles/personas';
COMMENT ON COLUMN course_creator.tracks.duration_weeks IS 'Estimated completion time in weeks (1-104)';
COMMENT ON COLUMN course_creator.tracks.max_students IS 'Maximum enrollment limit (NULL = unlimited)';
COMMENT ON COLUMN course_creator.tracks.skills_taught IS 'JSON array of skills taught in this track';
COMMENT ON COLUMN course_creator.tracks.display_order IS 'Display order within parent project/sub-project (0-based)';
COMMENT ON COLUMN course_creator.tracks.auto_enroll_enabled IS 'Enable automatic enrollment when student joins parent';
COMMENT ON COLUMN course_creator.tracks.status IS 'Track lifecycle status: draft, active, completed, archived';
COMMENT ON COLUMN course_creator.tracks.settings IS 'JSON object for extensible track configuration';
COMMENT ON COLUMN course_creator.tracks.created_by IS 'User who created this track (audit trail)';

-- Step 9: Update trigger to handle updated_at
-- (Assuming trigger already exists, but we'll ensure it covers new columns)
CREATE OR REPLACE FUNCTION course_creator.update_tracks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_tracks_updated_at ON course_creator.tracks;
CREATE TRIGGER trigger_tracks_updated_at
    BEFORE UPDATE ON course_creator.tracks
    FOR EACH ROW
    EXECUTE FUNCTION course_creator.update_tracks_updated_at();

COMMIT;

-- Verification query
-- Run this to confirm all columns exist:
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'course_creator' AND table_name = 'tracks'
-- ORDER BY ordinal_position;
