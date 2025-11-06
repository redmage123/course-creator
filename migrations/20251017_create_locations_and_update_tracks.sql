-- =============================================================================
-- Migration: Create Locations Table and Update Tracks Schema
-- Date: 2025-10-17
-- Purpose:
--   1. Create locations table (multi-locations instances of projects)
--   2. Add all missing fields to tracks table to match Track entity
--
-- BUSINESS CONTEXT:
-- The platform supports multi-locations training programs where a main project
-- can have multiple locations-specific instances. Tracks can belong to either:
-- - A main project (project_id set, location_id NULL)
-- - A specific locations (location_id set, project_id NULL)
--
-- This enables hierarchical organization: Project → Locations → Tracks
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: Create Locations Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS locations (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Parent Relationship
    parent_project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES course_creator.organizations(id) ON DELETE CASCADE,

    -- Identification
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,

    -- Locations Information
    location_country VARCHAR(100) NOT NULL,
    location_region VARCHAR(100),
    location_city VARCHAR(100),
    location_address TEXT,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',

    -- Scheduling
    start_date DATE,
    end_date DATE,
    duration_weeks INTEGER,

    -- Capacity Management
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0 CHECK (current_participants >= 0),

    -- Status Lifecycle
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'cancelled', 'archived')),

    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,

    -- Metadata (flexible JSON storage for additional data)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Business Rules
    CONSTRAINT locations_dates_valid CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    CONSTRAINT locations_capacity_valid CHECK (max_participants IS NULL OR current_participants <= max_participants),
    CONSTRAINT locations_unique UNIQUE(organization_id, parent_project_id, slug)
);

COMMENT ON TABLE locations IS
    'Locations represent specific geographic instances of a main project with customized schedules and capacity';

COMMENT ON COLUMN locations.metadata IS
    'Flexible JSON storage for additional locations-specific data';

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_locations_parent ON locations(parent_project_id);
CREATE INDEX IF NOT EXISTS idx_locations_organization ON locations(organization_id);
CREATE INDEX IF NOT EXISTS idx_locations_country ON locations(location_country);
CREATE INDEX IF NOT EXISTS idx_locations_region ON locations(location_region);
CREATE INDEX IF NOT EXISTS idx_locations_city ON locations(location_city);
CREATE INDEX IF NOT EXISTS idx_locations_dates ON locations(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_locations_status ON locations(status);
CREATE INDEX IF NOT EXISTS idx_locations_metadata ON locations USING gin(metadata);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_locations_parent_location
    ON locations(parent_project_id, location_country, location_region, location_city);

CREATE INDEX IF NOT EXISTS idx_locations_parent_dates
    ON locations(parent_project_id, start_date, end_date);

-- =============================================================================
-- STEP 2: Add Missing Columns to Tracks Table
-- =============================================================================

-- Add all missing columns (nullable initially for safe migration)
ALTER TABLE tracks
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
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
    ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL;

-- =============================================================================
-- STEP 3: Migrate Existing Data
-- =============================================================================

-- Generate slugs for existing tracks from names (only if slug column exists and is empty)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='course_creator'
               AND table_name='tracks'
               AND column_name='slug') THEN
        UPDATE tracks
        SET slug = LOWER(REGEXP_REPLACE(REGEXP_REPLACE(name, '[^a-zA-Z0-9\s-]', '', 'g'), '\s+', '-', 'g'))
        WHERE slug IS NULL;
    END IF;
END $$;

-- =============================================================================
-- STEP 4: Add Constraints (with IF NOT EXISTS handling)
-- =============================================================================

-- XOR constraint: track must belong to project OR locations, not both or neither
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tracks_parent_xor') THEN
        ALTER TABLE tracks
            ADD CONSTRAINT chk_tracks_parent_xor CHECK (
                (project_id IS NOT NULL AND location_id IS NULL) OR
                (project_id IS NULL AND location_id IS NOT NULL)
            );
    END IF;
END $$;

-- Unique constraint for slug within organization
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_tracks_organization_slug') THEN
        ALTER TABLE tracks
            ADD CONSTRAINT uq_tracks_organization_slug UNIQUE (organization_id, slug);
    END IF;
END $$;

-- Data validation constraints
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tracks_duration_weeks') THEN
        ALTER TABLE tracks ADD CONSTRAINT chk_tracks_duration_weeks CHECK (duration_weeks IS NULL OR (duration_weeks >= 1 AND duration_weeks <= 104));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tracks_max_students') THEN
        ALTER TABLE tracks ADD CONSTRAINT chk_tracks_max_students CHECK (max_students IS NULL OR max_students >= 1);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tracks_display_order') THEN
        ALTER TABLE tracks ADD CONSTRAINT chk_tracks_display_order CHECK (display_order >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tracks_status') THEN
        ALTER TABLE tracks ADD CONSTRAINT chk_tracks_status CHECK (status IN ('draft', 'active', 'completed', 'archived'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_tracks_track_type') THEN
        ALTER TABLE tracks ADD CONSTRAINT chk_tracks_track_type CHECK (track_type IN ('sequential', 'flexible', 'milestone_based'));
    END IF;
END $$;

-- =============================================================================
-- STEP 5: Create Indexes
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_tracks_project_id ON tracks(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tracks_location_id ON tracks(location_id) WHERE location_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tracks_slug ON tracks(slug);
CREATE INDEX IF NOT EXISTS idx_tracks_status ON tracks(status);
CREATE INDEX IF NOT EXISTS idx_tracks_display_order ON tracks(display_order);
CREATE INDEX IF NOT EXISTS idx_tracks_created_by ON tracks(created_by) WHERE created_by IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tracks_track_type ON tracks(track_type);

-- =============================================================================
-- STEP 6: Add Column Comments
-- =============================================================================

COMMENT ON COLUMN tracks.project_id IS 'Parent project ID (XOR with location_id)';
COMMENT ON COLUMN tracks.location_id IS 'Parent locations ID (XOR with project_id)';
COMMENT ON COLUMN tracks.slug IS 'URL-safe identifier unique within organization';
COMMENT ON COLUMN tracks.track_type IS 'Learning path type: sequential, flexible, or milestone_based';
COMMENT ON COLUMN tracks.target_audience IS 'JSON array of target audience roles/personas';
COMMENT ON COLUMN tracks.duration_weeks IS 'Estimated completion time in weeks (1-104)';
COMMENT ON COLUMN tracks.max_students IS 'Maximum enrollment limit (NULL = unlimited)';
COMMENT ON COLUMN tracks.skills_taught IS 'JSON array of skills taught in this track';
COMMENT ON COLUMN tracks.display_order IS 'Display order within parent project/locations (0-based)';
COMMENT ON COLUMN tracks.auto_enroll_enabled IS 'Enable automatic enrollment when student joins parent';
COMMENT ON COLUMN tracks.status IS 'Track lifecycle status: draft, active, completed, archived';
COMMENT ON COLUMN tracks.settings IS 'JSON object for extensible track configuration';
COMMENT ON COLUMN tracks.created_by IS 'User who created this track (audit trail)';

-- =============================================================================
-- STEP 7: Update Triggers
-- =============================================================================

-- Function to auto-calculate duration for locations
CREATE OR REPLACE FUNCTION calculate_location_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.start_date IS NOT NULL AND NEW.end_date IS NOT NULL THEN
        NEW.duration_weeks := CEIL((NEW.end_date - NEW.start_date) / 7.0);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_calculate_location_duration ON locations;
CREATE TRIGGER trigger_calculate_location_duration
    BEFORE INSERT OR UPDATE ON locations
    FOR EACH ROW
    WHEN (NEW.start_date IS NOT NULL AND NEW.end_date IS NOT NULL)
    EXECUTE FUNCTION calculate_location_duration();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_location_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_location_timestamp ON locations;
CREATE TRIGGER trigger_update_location_timestamp
    BEFORE UPDATE ON locations
    FOR EACH ROW
    EXECUTE FUNCTION update_location_timestamp();

-- Update tracks updated_at trigger
CREATE OR REPLACE FUNCTION update_tracks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_tracks_updated_at ON tracks;
CREATE TRIGGER trigger_tracks_updated_at
    BEFORE UPDATE ON tracks
    FOR EACH ROW
    EXECUTE FUNCTION update_tracks_updated_at();

-- =============================================================================
-- STEP 8: Create Views
-- =============================================================================

CREATE OR REPLACE VIEW locations_with_stats AS
SELECT
    l.id,
    l.parent_project_id,
    l.organization_id,
    l.name,
    l.slug,
    l.description,
    l.location_country,
    l.location_region,
    l.location_city,
    l.timezone,
    l.start_date,
    l.end_date,
    l.duration_weeks,
    l.max_participants,
    l.current_participants,
    l.status,
    l.created_at,
    l.updated_at,
    l.metadata,
    CASE
        WHEN l.max_participants > 0 THEN
            ROUND((l.current_participants::NUMERIC / l.max_participants) * 100, 2)
        ELSE 0
    END as capacity_percentage
FROM locations l;

COMMENT ON VIEW locations_with_stats IS
    'Enhanced view of locations with calculated capacity metrics';

COMMIT;

-- Verification
SELECT 'Migration completed successfully!' as status;
SELECT 'Created locations table' as step_1;
SELECT 'Updated tracks table with all missing fields' as step_2;
SELECT 'Added XOR constraint (project_id OR location_id)' as step_3;
