-- =============================================================================
-- Migration 004: Add Sub-Projects (Locations) Feature - Simplified Version
-- =============================================================================
--
-- BUSINESS CONTEXT:
-- Implements hierarchical project structure to support multi-locations training
-- programs. This version works with the current minimal schema.
--
-- NOTE: This migration does not create foreign key constraints to tables
-- that don't exist in this database (users, tracks, enrollments, organizations).
-- Those constraints will be handled by their respective services.
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: Enhance Projects Table
-- =============================================================================

-- Add template and sub-project flags to existing projects table
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS has_sub_projects BOOLEAN DEFAULT false;

COMMENT ON COLUMN projects.is_template IS
    'Indicates if this project is a template (main project) for creating sub-projects/locations';

COMMENT ON COLUMN projects.has_sub_projects IS
    'Indicates if this project has sub-projects enabled (multi-locations program)';

-- Add index for template projects
CREATE INDEX IF NOT EXISTS idx_projects_template ON projects(is_template) WHERE is_template = true;

-- Update existing projects to explicitly be non-templates (backwards compatibility)
UPDATE projects
SET is_template = false, has_sub_projects = false
WHERE is_template IS NULL OR has_sub_projects IS NULL;

-- =============================================================================
-- STEP 2: Create Sub-Projects Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS sub_projects (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Parent Relationship
    parent_project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,  -- No FK constraint (different service/database)

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,  -- No FK constraint
    updated_by UUID,  -- No FK constraint

    -- Metadata (flexible JSON storage for additional data)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Business Rules
    CONSTRAINT sub_projects_dates_valid CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    CONSTRAINT sub_projects_capacity_valid CHECK (max_participants IS NULL OR current_participants <= max_participants),
    CONSTRAINT sub_projects_unique UNIQUE(organization_id, parent_project_id, slug)
);

-- Comments
COMMENT ON TABLE sub_projects IS
    'Sub-projects (locations) represent specific instances of a main project in different locations with customized schedules';

COMMENT ON COLUMN sub_projects.metadata IS
    'Flexible JSON storage for additional locations-specific data (instructors, tracks, etc.)';

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_sub_projects_parent ON sub_projects(parent_project_id);
CREATE INDEX IF NOT EXISTS idx_sub_projects_organization ON sub_projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_sub_projects_location_country ON sub_projects(location_country);
CREATE INDEX IF NOT EXISTS idx_sub_projects_location_region ON sub_projects(location_region);
CREATE INDEX IF NOT EXISTS idx_sub_projects_location_city ON sub_projects(location_city);
CREATE INDEX IF NOT EXISTS idx_sub_projects_dates ON sub_projects(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_sub_projects_status ON sub_projects(status);
CREATE INDEX IF NOT EXISTS idx_sub_projects_metadata ON sub_projects USING gin(metadata);

-- Composite index for common query pattern: filter by parent + locations
CREATE INDEX IF NOT EXISTS idx_sub_projects_parent_location
    ON sub_projects(parent_project_id, location_country, location_region, location_city);

-- Composite index for date range queries
CREATE INDEX IF NOT EXISTS idx_sub_projects_parent_dates
    ON sub_projects(parent_project_id, start_date, end_date);

-- =============================================================================
-- STEP 3: Create Helper Functions
-- =============================================================================

-- Function: Auto-calculate duration_weeks from start_date and end_date
CREATE OR REPLACE FUNCTION calculate_sub_project_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.start_date IS NOT NULL AND NEW.end_date IS NOT NULL THEN
        NEW.duration_weeks := CEIL((NEW.end_date - NEW.start_date) / 7.0);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-calculate duration on INSERT/UPDATE
DROP TRIGGER IF EXISTS trigger_calculate_sub_project_duration ON sub_projects;
CREATE TRIGGER trigger_calculate_sub_project_duration
    BEFORE INSERT OR UPDATE ON sub_projects
    FOR EACH ROW
    WHEN (NEW.start_date IS NOT NULL AND NEW.end_date IS NOT NULL)
    EXECUTE FUNCTION calculate_sub_project_duration();

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_sub_project_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update timestamp on sub_projects
DROP TRIGGER IF EXISTS trigger_update_sub_project_timestamp ON sub_projects;
CREATE TRIGGER trigger_update_sub_project_timestamp
    BEFORE UPDATE ON sub_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_sub_project_timestamp();

-- =============================================================================
-- STEP 4: Create Views for Reporting
-- =============================================================================

-- View: Sub-projects with basic stats (without joins to other services' tables)
CREATE OR REPLACE VIEW sub_projects_with_stats AS
SELECT
    sp.id,
    sp.parent_project_id,
    sp.organization_id,
    sp.name,
    sp.slug,
    sp.description,
    sp.location_country,
    sp.location_region,
    sp.location_city,
    sp.timezone,
    sp.start_date,
    sp.end_date,
    sp.duration_weeks,
    sp.max_participants,
    sp.current_participants,
    sp.status,
    sp.created_at,
    sp.updated_at,
    sp.metadata,
    CASE
        WHEN sp.max_participants > 0 THEN
            ROUND((sp.current_participants::NUMERIC / sp.max_participants) * 100, 2)
        ELSE 0
    END as capacity_percentage
FROM sub_projects sp;

COMMENT ON VIEW sub_projects_with_stats IS
    'Enhanced view of sub-projects with calculated capacity metrics';

-- =============================================================================
-- STEP 5: Sample Data for Testing (Optional - Remove in Production)
-- =============================================================================

-- This section can be commented out for production deployments
-- Uncomment for development/testing environments

/*
-- Sample: Create a template project first
INSERT INTO projects (organization_id, name, slug, description, is_template, has_sub_projects, created_at)
VALUES (
    uuid_generate_v4(),  -- Replace with actual org ID
    'Cloud Architecture Graduate Program',
    'cloud-arch-grad-program',
    'Comprehensive cloud architecture training for graduate engineers',
    true,
    true,
    CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;

-- Sample: Create Boston locations
INSERT INTO sub_projects (
    parent_project_id,
    organization_id,
    name,
    slug,
    description,
    location_country,
    location_region,
    location_city,
    timezone,
    start_date,
    end_date,
    max_participants,
    status
) VALUES (
    (SELECT id FROM projects WHERE slug = 'cloud-arch-grad-program' LIMIT 1),
    (SELECT organization_id FROM projects LIMIT 1),
    'Boston Locations Fall 2025',
    'boston-fall-2025',
    'Graduate training program for Boston office',
    'United States',
    'Massachusetts',
    'Boston',
    'America/New_York',
    '2025-09-01',
    '2025-12-15',
    30,
    'draft'
) ON CONFLICT DO NOTHING;
*/

-- =============================================================================
-- STEP 6: Verification Queries
-- =============================================================================

-- Verify schema creation
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'sub_projects') = 1,
        'sub_projects table not created';
    ASSERT (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'is_template') = 1,
        'is_template column not added to projects';
    ASSERT (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'has_sub_projects') = 1,
        'has_sub_projects column not added to projects';

    RAISE NOTICE '✅ Migration 004 completed successfully';
    RAISE NOTICE '📋 Created sub_projects table with locations tracking';
    RAISE NOTICE '🌍 Supports multi-locations locations with independent schedules';
    RAISE NOTICE '📊 Added capacity management and status lifecycle';
END;
$$;

COMMIT;

-- =============================================================================
-- ROLLBACK SCRIPT (For Reference - DO NOT RUN IN PRODUCTION)
-- =============================================================================

/*
BEGIN;

-- Drop triggers
DROP TRIGGER IF EXISTS trigger_calculate_sub_project_duration ON sub_projects;
DROP TRIGGER IF EXISTS trigger_update_sub_project_timestamp ON sub_projects;

-- Drop functions
DROP FUNCTION IF EXISTS calculate_sub_project_duration();
DROP FUNCTION IF EXISTS update_sub_project_timestamp();

-- Drop views
DROP VIEW IF EXISTS sub_projects_with_stats;

-- Drop tables
DROP TABLE IF EXISTS sub_projects CASCADE;

-- Remove columns from projects
ALTER TABLE projects
    DROP COLUMN IF EXISTS is_template,
    DROP COLUMN IF EXISTS has_sub_projects;

COMMIT;
*/

-- =============================================================================
-- END OF MIGRATION 004
-- =============================================================================
