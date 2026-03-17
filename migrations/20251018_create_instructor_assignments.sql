-- =============================================================================
-- Migration: Create Instructor Assignment Tables
-- Date: 2025-10-18
-- Purpose:
--   1. Create instructor_track_assignments table (many-to-many: instructors <-> tracks)
--   2. Create instructor_location_assignments table (many-to-many: instructors <-> locations)
--
-- BUSINESS CONTEXT:
-- The platform allows organization admins to assign instructors to specific tracks
-- and locations. This enables:
-- - Track-level assignments: Instructor teaches all content in a track
-- - Locations-level assignments: Instructor teaches at specific geographic locations
-- - Flexible instructor workload management
-- - Multi-instructor support per track/locations
--
-- This supports the organizational hierarchy:
-- Organization → Projects → Tracks → Instructors (by track)
-- Organization → Projects → Locations → Instructors (by locations)
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: Create Instructor Track Assignments Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS instructor_track_assignments (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Assignment Relationships
    instructor_id UUID NOT NULL REFERENCES course_creator.users(id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES course_creator.organizations(id) ON DELETE CASCADE,

    -- Assignment Status
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'completed')),

    -- Assignment Details
    assigned_role VARCHAR(50) DEFAULT 'primary' CHECK (assigned_role IN ('primary', 'assistant', 'substitute', 'guest')),
    responsibilities TEXT, -- Optional description of instructor's specific responsibilities

    -- Scheduling (optional - for time-based assignments)
    start_date DATE,
    end_date DATE,

    -- Audit Fields
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,

    -- Metadata (flexible JSON storage for additional assignment data)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Business Rules
    CONSTRAINT track_assignments_dates_valid CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    CONSTRAINT track_assignments_unique UNIQUE(instructor_id, track_id, organization_id)
);

COMMENT ON TABLE instructor_track_assignments IS
    'Assigns instructors to tracks - many-to-many relationship allowing multiple instructors per track';

COMMENT ON COLUMN instructor_track_assignments.assigned_role IS
    'Role of instructor: primary (main instructor), assistant (co-instructor), substitute (backup), guest (temporary)';

COMMENT ON COLUMN instructor_track_assignments.metadata IS
    'Flexible JSON storage for assignment-specific data (e.g., teaching hours, compensation, notes)';

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_instructor_track_instructor ON instructor_track_assignments(instructor_id);
CREATE INDEX IF NOT EXISTS idx_instructor_track_track ON instructor_track_assignments(track_id);
CREATE INDEX IF NOT EXISTS idx_instructor_track_organization ON instructor_track_assignments(organization_id);
CREATE INDEX IF NOT EXISTS idx_instructor_track_status ON instructor_track_assignments(status);
CREATE INDEX IF NOT EXISTS idx_instructor_track_dates ON instructor_track_assignments(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_instructor_track_assigned_by ON instructor_track_assignments(assigned_by) WHERE assigned_by IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_instructor_track_org_instructor
    ON instructor_track_assignments(organization_id, instructor_id, status);

CREATE INDEX IF NOT EXISTS idx_instructor_track_org_track
    ON instructor_track_assignments(organization_id, track_id, status);

-- =============================================================================
-- STEP 2: Create Instructor Locations Assignments Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS instructor_location_assignments (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Assignment Relationships
    instructor_id UUID NOT NULL REFERENCES course_creator.users(id) ON DELETE CASCADE,
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES course_creator.organizations(id) ON DELETE CASCADE,

    -- Assignment Status
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'completed')),

    -- Assignment Details
    assigned_role VARCHAR(50) DEFAULT 'primary' CHECK (assigned_role IN ('primary', 'assistant', 'substitute', 'guest')),
    responsibilities TEXT, -- Optional description of instructor's specific responsibilities

    -- Scheduling (optional - for time-based assignments)
    start_date DATE,
    end_date DATE,

    -- Audit Fields
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,

    -- Metadata (flexible JSON storage for additional assignment data)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Business Rules
    CONSTRAINT location_assignments_dates_valid CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    CONSTRAINT location_assignments_unique UNIQUE(instructor_id, location_id, organization_id)
);

COMMENT ON TABLE instructor_location_assignments IS
    'Assigns instructors to specific locations - enables locations-based instructor scheduling';

COMMENT ON COLUMN instructor_location_assignments.assigned_role IS
    'Role of instructor: primary (main instructor), assistant (co-instructor), substitute (backup), guest (temporary)';

COMMENT ON COLUMN instructor_location_assignments.metadata IS
    'Flexible JSON storage for locations-specific data (e.g., travel details, local contact)';

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_instructor_location_instructor ON instructor_location_assignments(instructor_id);
CREATE INDEX IF NOT EXISTS idx_instructor_location_location ON instructor_location_assignments(location_id);
CREATE INDEX IF NOT EXISTS idx_instructor_location_organization ON instructor_location_assignments(organization_id);
CREATE INDEX IF NOT EXISTS idx_instructor_location_status ON instructor_location_assignments(status);
CREATE INDEX IF NOT EXISTS idx_instructor_location_dates ON instructor_location_assignments(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_instructor_location_assigned_by ON instructor_location_assignments(assigned_by) WHERE assigned_by IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_instructor_location_org_instructor
    ON instructor_location_assignments(organization_id, instructor_id, status);

CREATE INDEX IF NOT EXISTS idx_instructor_location_org_location
    ON instructor_location_assignments(organization_id, location_id, status);

-- =============================================================================
-- STEP 3: Create Triggers for Timestamp Updates
-- =============================================================================

-- Track Assignments Timestamp Update
CREATE OR REPLACE FUNCTION update_instructor_track_assignment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_instructor_track_assignment_timestamp ON instructor_track_assignments;
CREATE TRIGGER trigger_update_instructor_track_assignment_timestamp
    BEFORE UPDATE ON instructor_track_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_instructor_track_assignment_timestamp();

-- Locations Assignments Timestamp Update
CREATE OR REPLACE FUNCTION update_instructor_location_assignment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_instructor_location_assignment_timestamp ON instructor_location_assignments;
CREATE TRIGGER trigger_update_instructor_location_assignment_timestamp
    BEFORE UPDATE ON instructor_location_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_instructor_location_assignment_timestamp();

-- =============================================================================
-- STEP 4: Create Views for Instructor Assignments
-- =============================================================================

-- View: Instructor Track Assignments with Details
CREATE OR REPLACE VIEW instructor_track_assignments_view AS
SELECT
    ita.id,
    ita.instructor_id,
    u.username as instructor_username,
    u.email as instructor_email,
    u.full_name as instructor_full_name,
    ita.track_id,
    t.name as track_name,
    t.description as track_description,
    t.status as track_status,
    ita.organization_id,
    o.name as organization_name,
    ita.status as assignment_status,
    ita.assigned_role,
    ita.responsibilities,
    ita.start_date,
    ita.end_date,
    ita.assigned_at,
    ita.assigned_by,
    assigned_by_user.username as assigned_by_username,
    ita.updated_at,
    ita.metadata,
    CASE
        WHEN ita.end_date IS NOT NULL AND ita.end_date < CURRENT_DATE THEN 'expired'
        WHEN ita.start_date IS NOT NULL AND ita.start_date > CURRENT_DATE THEN 'future'
        WHEN ita.status = 'active' THEN 'current'
        ELSE ita.status
    END as computed_status
FROM instructor_track_assignments ita
JOIN course_creator.users u ON ita.instructor_id = u.id
JOIN tracks t ON ita.track_id = t.id
JOIN course_creator.organizations o ON ita.organization_id = o.id
LEFT JOIN course_creator.users assigned_by_user ON ita.assigned_by = assigned_by_user.id;

COMMENT ON VIEW instructor_track_assignments_view IS
    'Enhanced view of instructor track assignments with user, track, and organization details';

-- View: Instructor Locations Assignments with Details
CREATE OR REPLACE VIEW instructor_location_assignments_view AS
SELECT
    ila.id,
    ila.instructor_id,
    u.username as instructor_username,
    u.email as instructor_email,
    u.full_name as instructor_full_name,
    ila.location_id,
    l.name as location_name,
    l.location_city,
    l.location_region,
    l.location_country,
    l.status as location_status,
    ila.organization_id,
    o.name as organization_name,
    ila.status as assignment_status,
    ila.assigned_role,
    ila.responsibilities,
    ila.start_date,
    ila.end_date,
    ila.assigned_at,
    ila.assigned_by,
    assigned_by_user.username as assigned_by_username,
    ila.updated_at,
    ila.metadata,
    CASE
        WHEN ila.end_date IS NOT NULL AND ila.end_date < CURRENT_DATE THEN 'expired'
        WHEN ila.start_date IS NOT NULL AND ila.start_date > CURRENT_DATE THEN 'future'
        WHEN ila.status = 'active' THEN 'current'
        ELSE ila.status
    END as computed_status
FROM instructor_location_assignments ila
JOIN course_creator.users u ON ila.instructor_id = u.id
JOIN locations l ON ila.location_id = l.id
JOIN course_creator.organizations o ON ila.organization_id = o.id
LEFT JOIN course_creator.users assigned_by_user ON ila.assigned_by = assigned_by_user.id;

COMMENT ON VIEW instructor_location_assignments_view IS
    'Enhanced view of instructor locations assignments with user, locations, and organization details';

-- View: Instructor Workload Summary
CREATE OR REPLACE VIEW instructor_workload_summary AS
SELECT
    u.id as instructor_id,
    u.username,
    u.email,
    u.full_name,
    om.organization_id,
    o.name as organization_name,
    COUNT(DISTINCT ita.track_id) as total_tracks,
    COUNT(DISTINCT ila.location_id) as total_locations,
    COUNT(DISTINCT CASE WHEN ita.status = 'active' THEN ita.track_id END) as active_tracks,
    COUNT(DISTINCT CASE WHEN ila.status = 'active' THEN ila.location_id END) as active_locations
FROM course_creator.users u
JOIN course_creator.organization_memberships om ON u.id = om.user_id
JOIN course_creator.organizations o ON om.organization_id = o.id
LEFT JOIN instructor_track_assignments ita ON u.id = ita.instructor_id
LEFT JOIN instructor_location_assignments ila ON u.id = ila.instructor_id
WHERE u.role = 'instructor'
GROUP BY u.id, u.username, u.email, u.full_name, om.organization_id, o.name;

COMMENT ON VIEW instructor_workload_summary IS
    'Summary view showing instructor assignment counts for workload management';

-- =============================================================================
-- STEP 5: Create Helper Functions
-- =============================================================================

-- Function to get all assignments for an instructor
CREATE OR REPLACE FUNCTION get_instructor_assignments(
    p_instructor_id UUID,
    p_organization_id UUID DEFAULT NULL
)
RETURNS TABLE(
    assignment_type VARCHAR,
    assignment_id UUID,
    entity_id UUID,
    entity_name VARCHAR,
    status VARCHAR,
    assigned_role VARCHAR,
    start_date DATE,
    end_date DATE
) AS $$
BEGIN
    RETURN QUERY
    -- Track assignments
    SELECT
        'track'::VARCHAR as assignment_type,
        ita.id as assignment_id,
        ita.track_id as entity_id,
        t.name as entity_name,
        ita.status,
        ita.assigned_role,
        ita.start_date,
        ita.end_date
    FROM instructor_track_assignments ita
    JOIN tracks t ON ita.track_id = t.id
    WHERE ita.instructor_id = p_instructor_id
        AND (p_organization_id IS NULL OR ita.organization_id = p_organization_id)
        AND ita.status = 'active'

    UNION ALL

    -- Locations assignments
    SELECT
        'locations'::VARCHAR as assignment_type,
        ila.id as assignment_id,
        ila.location_id as entity_id,
        l.name as entity_name,
        ila.status,
        ila.assigned_role,
        ila.start_date,
        ila.end_date
    FROM instructor_location_assignments ila
    JOIN locations l ON ila.location_id = l.id
    WHERE ila.instructor_id = p_instructor_id
        AND (p_organization_id IS NULL OR ila.organization_id = p_organization_id)
        AND ila.status = 'active'

    ORDER BY assignment_type, entity_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_instructor_assignments IS
    'Returns all active assignments (tracks and locations) for a given instructor';

COMMIT;

-- Verification
SELECT 'Migration completed successfully!' as status;
SELECT 'Created instructor_track_assignments table' as step_1;
SELECT 'Created instructor_location_assignments table' as step_2;
SELECT 'Created views and helper functions' as step_3;
