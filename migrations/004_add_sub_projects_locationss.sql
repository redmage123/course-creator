-- =============================================================================
-- Migration 004: Add Sub-Projects (Locations) Feature
-- =============================================================================
--
-- BUSINESS CONTEXT:
-- Implements hierarchical project structure to support multi-locations training
-- programs. Main projects serve as templates, while sub-projects (locations)
-- represent specific instances in different locations with customized schedules.
--
-- KEY FEATURES:
-- - Main project → Multiple sub-projects (locations)
-- - Locations tracking (country, region, city)
-- - Independent scheduling per locations
-- - Track assignment with date overrides
-- - Capacity management per locations
-- - Status lifecycle (draft → active → completed → archived)
--
-- BACKWARDS COMPATIBILITY:
-- - Existing projects remain unchanged (is_template = false)
-- - Existing enrollments continue to work (project_id remains valid)
-- - New functionality is opt-in via project type selection
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Parent Relationship
    parent_project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

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
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),

    -- Business Rules
    CONSTRAINT sub_projects_dates_valid CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    CONSTRAINT sub_projects_capacity_valid CHECK (max_participants IS NULL OR current_participants <= max_participants),
    CONSTRAINT sub_projects_unique UNIQUE(organization_id, parent_project_id, slug)
);

-- Comments
COMMENT ON TABLE sub_projects IS
    'Sub-projects (locations) represent specific instances of a main project in different locations with customized schedules';

COMMENT ON COLUMN sub_projects.parent_project_id IS
    'Reference to the main project (template) that this locations instantiates';

COMMENT ON COLUMN sub_projects.slug IS
    'URL-friendly identifier unique within parent project scope (e.g., "boston-fall-2025")';

COMMENT ON COLUMN sub_projects.location_country IS
    'ISO country name (e.g., "United States", "United Kingdom", "Japan")';

COMMENT ON COLUMN sub_projects.location_region IS
    'State/Province/Region (e.g., "Massachusetts", "England", "Tokyo")';

COMMENT ON COLUMN sub_projects.location_city IS
    'City name (e.g., "Boston", "London", "Shibuya")';

COMMENT ON COLUMN sub_projects.timezone IS
    'IANA timezone identifier (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")';

COMMENT ON COLUMN sub_projects.current_participants IS
    'Auto-incremented/decremented counter tracking enrolled students';

COMMENT ON COLUMN sub_projects.status IS
    'Lifecycle status: draft (planning), active (running), completed (finished), cancelled (aborted), archived (historical)';

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_sub_projects_parent ON sub_projects(parent_project_id);
CREATE INDEX IF NOT EXISTS idx_sub_projects_organization ON sub_projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_sub_projects_location_country ON sub_projects(location_country);
CREATE INDEX IF NOT EXISTS idx_sub_projects_location_region ON sub_projects(location_region);
CREATE INDEX IF NOT EXISTS idx_sub_projects_location_city ON sub_projects(location_city);
CREATE INDEX IF NOT EXISTS idx_sub_projects_dates ON sub_projects(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_sub_projects_status ON sub_projects(status);

-- Composite index for common query pattern: filter by parent + locations
CREATE INDEX IF NOT EXISTS idx_sub_projects_parent_location
    ON sub_projects(parent_project_id, location_country, location_region, location_city);

-- Composite index for date range queries
CREATE INDEX IF NOT EXISTS idx_sub_projects_parent_dates
    ON sub_projects(parent_project_id, start_date, end_date);

-- =============================================================================
-- STEP 3: Create Sub-Project Tracks Assignment Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS sub_project_tracks (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    sub_project_id UUID NOT NULL REFERENCES sub_projects(id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,

    -- Schedule Overrides (optional - overrides track's default dates)
    start_date DATE,
    end_date DATE,

    -- Instructor Assignment
    primary_instructor_id UUID REFERENCES users(id),

    -- Ordering
    sequence_order INTEGER DEFAULT 0,

    -- Audit Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    -- Business Rules
    CONSTRAINT sub_project_tracks_dates_valid CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    CONSTRAINT sub_project_tracks_unique UNIQUE(sub_project_id, track_id)
);

-- Comments
COMMENT ON TABLE sub_project_tracks IS
    'Assigns tracks to sub-projects with optional date overrides and instructor assignments';

COMMENT ON COLUMN sub_project_tracks.start_date IS
    'Optional override for track start date within this locations (overrides track default)';

COMMENT ON COLUMN sub_project_tracks.end_date IS
    'Optional override for track end date within this locations (overrides track default)';

COMMENT ON COLUMN sub_project_tracks.sequence_order IS
    'Determines the order tracks are presented/executed within the locations (0 = first)';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sub_project_tracks_sub_project ON sub_project_tracks(sub_project_id);
CREATE INDEX IF NOT EXISTS idx_sub_project_tracks_track ON sub_project_tracks(track_id);
CREATE INDEX IF NOT EXISTS idx_sub_project_tracks_instructor ON sub_project_tracks(primary_instructor_id);

-- =============================================================================
-- STEP 4: Modify Enrollments Table to Support Sub-Projects
-- =============================================================================

-- Add sub_project_id column to enrollments
ALTER TABLE enrollments
    ADD COLUMN IF NOT EXISTS sub_project_id UUID REFERENCES sub_projects(id) ON DELETE CASCADE;

-- Add constraint: either project_id OR sub_project_id must be set (not both)
ALTER TABLE enrollments
    DROP CONSTRAINT IF EXISTS enrollments_project_or_sub_project,
    ADD CONSTRAINT enrollments_project_or_sub_project CHECK (
        (project_id IS NOT NULL AND sub_project_id IS NULL) OR
        (project_id IS NULL AND sub_project_id IS NOT NULL)
    );

COMMENT ON COLUMN enrollments.sub_project_id IS
    'Optional reference to sub-project (locations) for multi-locations programs';

-- Index for sub-project enrollments
CREATE INDEX IF NOT EXISTS idx_enrollments_sub_project ON enrollments(sub_project_id);

-- Composite index for common query: get all enrollments for a locations
CREATE INDEX IF NOT EXISTS idx_enrollments_sub_project_student
    ON enrollments(sub_project_id, student_id);

-- =============================================================================
-- STEP 5: Create Helper Functions
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

-- Function: Update current_participants count on enrollment
CREATE OR REPLACE FUNCTION update_sub_project_participant_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Increment participant count
        UPDATE sub_projects
        SET current_participants = current_participants + 1
        WHERE id = NEW.sub_project_id;
    ELSIF TG_OP = 'DELETE' THEN
        -- Decrement participant count
        UPDATE sub_projects
        SET current_participants = GREATEST(0, current_participants - 1)
        WHERE id = OLD.sub_project_id;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update participant count when enrollments change
DROP TRIGGER IF EXISTS trigger_update_sub_project_participants ON enrollments;
CREATE TRIGGER trigger_update_sub_project_participants
    AFTER INSERT OR DELETE ON enrollments
    FOR EACH ROW
    WHEN (NEW.sub_project_id IS NOT NULL OR OLD.sub_project_id IS NOT NULL)
    EXECUTE FUNCTION update_sub_project_participant_count();

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_sub_project_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
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
-- STEP 6: Create Views for Reporting
-- =============================================================================

-- View: Sub-projects with aggregated stats
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
    COUNT(DISTINCT spt.track_id) as track_count,
    COUNT(DISTINCT e.student_id) as enrolled_students_count,
    ROUND((sp.current_participants::NUMERIC / NULLIF(sp.max_participants, 0)) * 100, 2) as capacity_percentage
FROM sub_projects sp
LEFT JOIN sub_project_tracks spt ON sp.id = spt.sub_project_id
LEFT JOIN enrollments e ON sp.id = e.sub_project_id
GROUP BY sp.id;

COMMENT ON VIEW sub_projects_with_stats IS
    'Enhanced view of sub-projects with aggregated track counts, enrollment counts, and capacity metrics';

-- =============================================================================
-- STEP 7: Sample Data for Testing (Optional - Remove in Production)
-- =============================================================================

-- This section can be commented out for production deployments
-- Uncomment for development/testing environments

/*
-- Sample: Create a template project
INSERT INTO projects (id, organization_id, name, slug, description, is_template, has_sub_projects, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    (SELECT id FROM organizations LIMIT 1),
    'Cloud Architecture Graduate Program',
    'cloud-arch-grad-program',
    'Comprehensive cloud architecture training for graduate engineers',
    true,
    true,
    NOW()
);

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
    '00000000-0000-0000-0000-000000000001',
    (SELECT id FROM organizations LIMIT 1),
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
);

-- Sample: Create London locations
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
    '00000000-0000-0000-0000-000000000001',
    (SELECT id FROM organizations LIMIT 1),
    'London Locations Spring 2026',
    'london-spring-2026',
    'Graduate training program for London office',
    'United Kingdom',
    'England',
    'London',
    'Europe/London',
    '2026-03-01',
    '2026-06-15',
    25,
    'draft'
);

-- Sample: Create Tokyo locations
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
    '00000000-0000-0000-0000-000000000001',
    (SELECT id FROM organizations LIMIT 1),
    'Tokyo Locations Fall 2026',
    'tokyo-fall-2026',
    'Graduate training program for Tokyo office',
    'Japan',
    'Tokyo',
    'Shibuya',
    'Asia/Tokyo',
    '2026-10-01',
    '2027-01-15',
    20,
    'draft'
);
*/

-- =============================================================================
-- STEP 8: Permissions and Security
-- =============================================================================

-- Grant permissions to application role (adjust role name as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON sub_projects TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON sub_project_tracks TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- =============================================================================
-- STEP 9: Verification Queries
-- =============================================================================

-- Verify schema creation
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'sub_projects') = 1,
        'sub_projects table not created';
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'sub_project_tracks') = 1,
        'sub_project_tracks table not created';
    ASSERT (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'is_template') = 1,
        'is_template column not added to projects';
    ASSERT (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'enrollments' AND column_name = 'sub_project_id') = 1,
        'sub_project_id column not added to enrollments';

    RAISE NOTICE '✅ Migration 004 completed successfully';
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
DROP TRIGGER IF EXISTS trigger_update_sub_project_participants ON enrollments;
DROP TRIGGER IF EXISTS trigger_update_sub_project_timestamp ON sub_projects;

-- Drop functions
DROP FUNCTION IF EXISTS calculate_sub_project_duration();
DROP FUNCTION IF EXISTS update_sub_project_participant_count();
DROP FUNCTION IF EXISTS update_sub_project_timestamp();

-- Drop views
DROP VIEW IF EXISTS sub_projects_with_stats;

-- Drop tables (CASCADE will drop foreign key constraints)
DROP TABLE IF EXISTS sub_project_tracks CASCADE;
DROP TABLE IF EXISTS sub_projects CASCADE;

-- Remove columns from enrollments
ALTER TABLE enrollments
    DROP CONSTRAINT IF EXISTS enrollments_project_or_sub_project,
    DROP COLUMN IF EXISTS sub_project_id;

-- Remove columns from projects
ALTER TABLE projects
    DROP COLUMN IF EXISTS is_template,
    DROP COLUMN IF EXISTS has_sub_projects;

COMMIT;
*/

-- =============================================================================
-- END OF MIGRATION 004
-- =============================================================================
