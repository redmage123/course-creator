-- Migration: Course-Instructor Assignments
-- Purpose: Enable assignment of multiple instructors to courses with different roles
-- Author: Course Creator Platform
-- Date: 2025-10-18
--
-- BUSINESS CONTEXT:
-- - A course can have multiple instructors (primary, assistant, guest lecturer, substitute)
-- - Each assignment tracks role, status, time period, and assignment audit trail
-- - Supports workload management and scheduling for instructors
-- - Different from track-level assignments (instructor_track_assignments)

-- =============================================================================
-- FORWARD MIGRATION
-- =============================================================================

-- Create course_instructor_assignments table
CREATE TABLE IF NOT EXISTS course_instructor_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core relationships
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    instructor_id UUID NOT NULL REFERENCES course_creator.users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES course_creator.organizations(id) ON DELETE CASCADE,

    -- Assignment details
    assigned_role VARCHAR(50) NOT NULL DEFAULT 'primary'
        CHECK (assigned_role IN ('primary', 'assistant', 'substitute', 'guest_lecturer', 'co_instructor')),
    status VARCHAR(50) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'suspended', 'completed', 'cancelled')),

    -- Teaching responsibilities and notes
    responsibilities TEXT,
    teaching_hours_per_week DECIMAL(5,2),

    -- Time period for assignment
    start_date DATE,
    end_date DATE,
    CONSTRAINT course_instructor_dates_valid
        CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),

    -- Audit trail
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,

    -- Additional metadata (compensation, performance metrics, etc.)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Ensure unique active assignment per instructor-course-role combination
    CONSTRAINT course_instructor_unique UNIQUE(course_id, instructor_id, assigned_role)
);

-- Add table comment
COMMENT ON TABLE course_instructor_assignments IS 'Tracks assignment of instructors to courses with roles, responsibilities, and time periods';

-- Add column comments
COMMENT ON COLUMN course_instructor_assignments.course_id IS 'Reference to the course being taught';
COMMENT ON COLUMN course_instructor_assignments.instructor_id IS 'Reference to the instructor teaching the course';
COMMENT ON COLUMN course_instructor_assignments.organization_id IS 'Organization ID for multi-tenant isolation';
COMMENT ON COLUMN course_instructor_assignments.assigned_role IS 'Role: primary, assistant, substitute, guest_lecturer, co_instructor';
COMMENT ON COLUMN course_instructor_assignments.status IS 'Assignment status: active, inactive, suspended, completed, cancelled';
COMMENT ON COLUMN course_instructor_assignments.responsibilities IS 'Specific teaching responsibilities for this assignment';
COMMENT ON COLUMN course_instructor_assignments.teaching_hours_per_week IS 'Expected teaching hours per week for this course';
COMMENT ON COLUMN course_instructor_assignments.metadata IS 'Additional data: compensation, performance metrics, etc.';

-- Create indexes for efficient querying
CREATE INDEX idx_course_instructors_course ON course_instructor_assignments(course_id)
    WHERE status = 'active';
CREATE INDEX idx_course_instructors_instructor ON course_instructor_assignments(instructor_id)
    WHERE status = 'active';
CREATE INDEX idx_course_instructors_organization ON course_instructor_assignments(organization_id);
CREATE INDEX idx_course_instructors_status ON course_instructor_assignments(status);
CREATE INDEX idx_course_instructors_role ON course_instructor_assignments(assigned_role);
CREATE INDEX idx_course_instructors_dates ON course_instructor_assignments(start_date, end_date)
    WHERE start_date IS NOT NULL;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_course_instructor_assignments_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_course_instructor_assignments_timestamp
    BEFORE UPDATE ON course_instructor_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_course_instructor_assignments_timestamp();

-- Create comprehensive view joining courses, instructors, tracks, locations
CREATE OR REPLACE VIEW course_instructor_assignments_view AS
SELECT
    cia.id as assignment_id,
    cia.course_id,
    c.title as course_title,
    c.difficulty_level as course_difficulty,
    c.status as course_status,
    cia.instructor_id,
    u.full_name as instructor_name,
    u.email as instructor_email,
    cia.assigned_role,
    cia.status as assignment_status,
    cia.responsibilities,
    cia.teaching_hours_per_week,
    cia.start_date,
    cia.end_date,
    cia.assigned_at,
    cia.updated_at,
    -- Track information
    t.id as track_id,
    t.name as track_name,
    t.difficulty as track_difficulty,
    -- Locations information
    l.id as location_id,
    l.name as location_name,
    l.location_city,
    l.location_country,
    l.timezone,
    -- Organization information
    o.id as organization_id,
    o.name as organization_name,
    -- Assigner information
    assigner.full_name as assigned_by_name
FROM course_instructor_assignments cia
JOIN courses c ON cia.course_id = c.id
JOIN course_creator.users u ON cia.instructor_id = u.id
LEFT JOIN tracks t ON c.track_id = t.id
LEFT JOIN locations l ON c.location_id = l.id
JOIN course_creator.organizations o ON cia.organization_id = o.id
LEFT JOIN course_creator.users assigner ON cia.assigned_by = assigner.id;

COMMENT ON VIEW course_instructor_assignments_view IS 'Comprehensive view of course-instructor assignments with course, track, locations, and organization context';

-- Create view for instructor workload summary
CREATE OR REPLACE VIEW instructor_course_workload AS
SELECT
    cia.instructor_id,
    u.full_name as instructor_name,
    u.email as instructor_email,
    cia.organization_id,
    o.name as organization_name,
    COUNT(DISTINCT cia.course_id) as total_courses,
    COUNT(DISTINCT CASE WHEN cia.assigned_role = 'primary' THEN cia.course_id END) as primary_courses,
    COUNT(DISTINCT CASE WHEN cia.assigned_role = 'assistant' THEN cia.course_id END) as assistant_courses,
    SUM(cia.teaching_hours_per_week) as total_teaching_hours_per_week,
    COUNT(DISTINCT c.track_id) as tracks_teaching_in,
    COUNT(DISTINCT c.location_id) as locations_teaching_at
FROM course_instructor_assignments cia
JOIN course_creator.users u ON cia.instructor_id = u.id
JOIN course_creator.organizations o ON cia.organization_id = o.id
JOIN courses c ON cia.course_id = c.id
WHERE cia.status = 'active'
  AND (cia.start_date IS NULL OR cia.start_date <= CURRENT_DATE)
  AND (cia.end_date IS NULL OR cia.end_date >= CURRENT_DATE)
GROUP BY cia.instructor_id, u.full_name, u.email, cia.organization_id, o.name;

COMMENT ON VIEW instructor_course_workload IS 'Summary of each instructor''s active course assignments and teaching workload';

-- Create helper function to get course instructors
CREATE OR REPLACE FUNCTION get_course_instructors(
    p_course_id UUID,
    p_include_inactive BOOLEAN DEFAULT FALSE
)
RETURNS TABLE(
    instructor_id UUID,
    instructor_name VARCHAR,
    instructor_email VARCHAR,
    assigned_role VARCHAR,
    status VARCHAR,
    teaching_hours_per_week DECIMAL,
    start_date DATE,
    end_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cia.instructor_id,
        u.full_name as instructor_name,
        u.email as instructor_email,
        cia.assigned_role,
        cia.status,
        cia.teaching_hours_per_week,
        cia.start_date,
        cia.end_date
    FROM course_instructor_assignments cia
    JOIN course_creator.users u ON cia.instructor_id = u.id
    WHERE cia.course_id = p_course_id
      AND (p_include_inactive OR cia.status = 'active')
    ORDER BY
        CASE cia.assigned_role
            WHEN 'primary' THEN 1
            WHEN 'co_instructor' THEN 2
            WHEN 'assistant' THEN 3
            WHEN 'substitute' THEN 4
            WHEN 'guest_lecturer' THEN 5
            ELSE 6
        END,
        cia.assigned_at;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_course_instructors IS 'Get all instructors assigned to a course, ordered by role priority';

-- =============================================================================
-- ROLLBACK MIGRATION
-- =============================================================================

-- DROP FUNCTION IF EXISTS get_course_instructors;
-- DROP VIEW IF EXISTS instructor_course_workload;
-- DROP VIEW IF EXISTS course_instructor_assignments_view;
-- DROP TRIGGER IF EXISTS trigger_update_course_instructor_assignments_timestamp ON course_instructor_assignments;
-- DROP FUNCTION IF EXISTS update_course_instructor_assignments_timestamp;
-- DROP INDEX IF EXISTS idx_course_instructors_dates;
-- DROP INDEX IF EXISTS idx_course_instructors_role;
-- DROP INDEX IF EXISTS idx_course_instructors_status;
-- DROP INDEX IF EXISTS idx_course_instructors_organization;
-- DROP INDEX IF EXISTS idx_course_instructors_instructor;
-- DROP INDEX IF EXISTS idx_course_instructors_course;
-- DROP TABLE IF EXISTS course_instructor_assignments;
