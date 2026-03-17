-- Migration: Add Sub-Projects and Track Assignment System
-- Version: 1.0
-- Date: 2025-10-15
-- Author: TDD Implementation
--
-- BUSINESS PURPOSE:
-- Enable optional sub-project hierarchy and track-instructor-student assignments
-- with load balancing support
--
-- FEATURES:
-- - Optional sub-projects under main projects
-- - Tracks can belong to project OR sub-project
-- - Track instructor assignments with communication links (Zoom, Teams, Slack)
-- - Track student assignments with instructor assignment
-- - Auto-balance flag for load balancing (opt-in)
-- - Minimum 1 instructor enforcement

-- ==============================================================================
-- STEP 1: Add Sub-Project Support to Projects Table
-- ==============================================================================

-- Add new columns for sub-project functionality
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS parent_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS is_sub_project BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS auto_balance_students BOOLEAN DEFAULT FALSE;

-- Add constraint: Sub-projects must have parent, main projects cannot
ALTER TABLE projects
    ADD CONSTRAINT check_subproject_hierarchy CHECK (
        (is_sub_project = TRUE AND parent_project_id IS NOT NULL) OR
        (is_sub_project = FALSE AND parent_project_id IS NULL)
    );

-- Add index for efficient sub-project queries
CREATE INDEX IF NOT EXISTS idx_projects_parent_id
    ON projects(parent_project_id)
    WHERE parent_project_id IS NOT NULL;

-- Add index for sub-project flag
CREATE INDEX IF NOT EXISTS idx_projects_is_subproject
    ON projects(is_sub_project)
    WHERE is_sub_project = TRUE;

COMMENT ON COLUMN projects.parent_project_id IS 'Reference to parent project (NULL for main projects, set for sub-projects)';
COMMENT ON COLUMN projects.is_sub_project IS 'Flag indicating if this is a sub-project (TRUE) or main project (FALSE)';
COMMENT ON COLUMN projects.auto_balance_students IS 'Enable auto-balancing of students across instructors (opt-in, default FALSE)';


-- ==============================================================================
-- STEP 2: Add Flexible Track Assignment (Project OR Sub-Project)
-- ==============================================================================

-- Add sub_project_id column to tracks table
ALTER TABLE tracks
    ADD COLUMN IF NOT EXISTS sub_project_id UUID REFERENCES projects(id) ON DELETE CASCADE;

-- Add constraint: Track must reference EITHER project_id OR sub_project_id (XOR)
ALTER TABLE tracks
    ADD CONSTRAINT check_track_parent_reference CHECK (
        (project_id IS NOT NULL AND sub_project_id IS NULL) OR
        (project_id IS NULL AND sub_project_id IS NOT NULL)
    );

-- Add index for sub-project track queries
CREATE INDEX IF NOT EXISTS idx_tracks_subproject_id
    ON tracks(sub_project_id)
    WHERE sub_project_id IS NOT NULL;

COMMENT ON COLUMN tracks.sub_project_id IS 'Reference to sub-project (NULL if track belongs to main project, set if track belongs to sub-project)';
COMMENT ON CONSTRAINT check_track_parent_reference ON tracks IS 'Enforce that track belongs to EITHER project OR sub-project, not both or neither';


-- ==============================================================================
-- STEP 3: Create Track Instructors Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS track_instructors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    -- Note: No FK constraint to users table since it doesn't exist yet
    user_id UUID NOT NULL,

    -- Instructor communication links
    zoom_link VARCHAR(500),
    teams_link VARCHAR(500),
    slack_links JSONB DEFAULT '[]'::jsonb,  -- Array of Slack channel/DM links

    -- Assignment metadata
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Note: No FK constraint to users table since it doesn't exist yet
    assigned_by UUID,

    -- Unique constraint: One instructor can only be assigned once per track
    CONSTRAINT unique_track_instructor UNIQUE(track_id, user_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_track_instructors_track_id
    ON track_instructors(track_id);

CREATE INDEX IF NOT EXISTS idx_track_instructors_user_id
    ON track_instructors(user_id);

CREATE INDEX IF NOT EXISTS idx_track_instructors_assigned_by
    ON track_instructors(assigned_by)
    WHERE assigned_by IS NOT NULL;

-- Table and column comments
COMMENT ON TABLE track_instructors IS 'Junction table for track-instructor assignments with communication links';
COMMENT ON COLUMN track_instructors.zoom_link IS 'Zoom meeting link for this instructor (e.g., office hours, lectures)';
COMMENT ON COLUMN track_instructors.teams_link IS 'Microsoft Teams meeting link for this instructor';
COMMENT ON COLUMN track_instructors.slack_links IS 'Array of Slack channel/DM links (JSON array of strings)';
COMMENT ON COLUMN track_instructors.assigned_by IS 'User ID of org admin who made the assignment';


-- ==============================================================================
-- STEP 4: Create Track Students Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS track_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    -- Note: No FK constraint to users table since it doesn't exist yet
    student_id UUID NOT NULL,

    -- Instructor assignment for load balancing
    -- Note: No FK constraint to users table since it doesn't exist yet
    assigned_instructor_id UUID,

    -- Assignment metadata
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Note: No FK constraint to users table since it doesn't exist yet
    assigned_by UUID,
    last_reassigned_at TIMESTAMP,

    -- Unique constraint: One student can only be enrolled once per track
    CONSTRAINT unique_track_student UNIQUE(track_id, student_id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_track_students_track_id
    ON track_students(track_id);

CREATE INDEX IF NOT EXISTS idx_track_students_student_id
    ON track_students(student_id);

CREATE INDEX IF NOT EXISTS idx_track_students_instructor_id
    ON track_students(assigned_instructor_id)
    WHERE assigned_instructor_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_track_students_assigned_by
    ON track_students(assigned_by)
    WHERE assigned_by IS NOT NULL;

-- Table and column comments
COMMENT ON TABLE track_students IS 'Junction table for track-student enrollments with instructor assignments';
COMMENT ON COLUMN track_students.assigned_instructor_id IS 'Reference to instructor assigned to this student (NULL if not yet assigned)';
COMMENT ON COLUMN track_students.last_reassigned_at IS 'Timestamp of last reassignment to different instructor (for audit trail)';


-- ==============================================================================
-- STEP 5: Add Foreign Key Constraint for Instructor Assignment
-- ==============================================================================

-- Ensure assigned_instructor_id references a valid track instructor
-- Note: This is enforced at application level due to composite FK complexity
-- Database trigger provides additional enforcement

CREATE OR REPLACE FUNCTION validate_student_instructor_assignment()
RETURNS TRIGGER AS $$
BEGIN
    -- If instructor is assigned, verify they are assigned to this track
    IF NEW.assigned_instructor_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
            FROM track_instructors
            WHERE track_id = NEW.track_id
            AND user_id = NEW.assigned_instructor_id
        ) THEN
            RAISE EXCEPTION 'Assigned instructor (%) is not assigned to track (%)',
                NEW.assigned_instructor_id, NEW.track_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_student_instructor_assignment
BEFORE INSERT OR UPDATE ON track_students
FOR EACH ROW
EXECUTE FUNCTION validate_student_instructor_assignment();

COMMENT ON FUNCTION validate_student_instructor_assignment() IS 'Ensure student can only be assigned to instructors who teach their track';


-- ==============================================================================
-- STEP 6: Add Minimum Instructor Enforcement
-- ==============================================================================

-- Function to validate minimum 1 instructor per track
CREATE OR REPLACE FUNCTION validate_minimum_instructors()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if this deletion would leave track with 0 instructors
    IF (SELECT COUNT(*) FROM track_instructors WHERE track_id = OLD.track_id) <= 1 THEN
        RAISE EXCEPTION 'Cannot remove instructor: Track must have at least 1 instructor assigned';
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prevent removing last instructor
CREATE TRIGGER enforce_min_instructors
BEFORE DELETE ON track_instructors
FOR EACH ROW
EXECUTE FUNCTION validate_minimum_instructors();

COMMENT ON FUNCTION validate_minimum_instructors() IS 'Prevent deletion of last instructor from a track (minimum 1 required)';


-- ==============================================================================
-- STEP 7: Create Views for Common Queries
-- ==============================================================================

-- View: Track with instructor and student counts
CREATE OR REPLACE VIEW track_statistics AS
SELECT
    t.id AS track_id,
    t.name AS track_name,
    t.project_id,
    t.sub_project_id,
    COALESCE(i.instructor_count, 0) AS instructor_count,
    COALESCE(s.student_count, 0) AS student_count,
    CASE
        WHEN COALESCE(i.instructor_count, 0) > 0 THEN
            ROUND(COALESCE(s.student_count, 0)::numeric / i.instructor_count, 2)
        ELSE 0
    END AS students_per_instructor
FROM tracks t
LEFT JOIN (
    SELECT track_id, COUNT(*) AS instructor_count
    FROM track_instructors
    GROUP BY track_id
) i ON t.id = i.track_id
LEFT JOIN (
    SELECT track_id, COUNT(*) AS student_count
    FROM track_students
    GROUP BY track_id
) s ON t.id = s.track_id;

COMMENT ON VIEW track_statistics IS 'Track statistics with instructor/student counts and load metrics';


-- View: Instructor load distribution per track
-- Note: Simplified version without username since users table doesn't exist yet
CREATE OR REPLACE VIEW instructor_load_distribution AS
SELECT
    ti.track_id,
    ti.user_id AS instructor_id,
    COALESCE(ts.student_count, 0) AS student_count,
    ti.zoom_link,
    ti.teams_link,
    ti.slack_links,
    ti.assigned_at
FROM track_instructors ti
LEFT JOIN (
    SELECT assigned_instructor_id, COUNT(*) AS student_count
    FROM track_students
    WHERE assigned_instructor_id IS NOT NULL
    GROUP BY assigned_instructor_id
) ts ON ti.user_id = ts.assigned_instructor_id;

COMMENT ON VIEW instructor_load_distribution IS 'Instructor workload distribution across tracks (without username - users table not yet available)';


-- ==============================================================================
-- STEP 8: Add Helper Functions for Load Balancing
-- ==============================================================================

-- Function to get instructor with lowest student count for a track
CREATE OR REPLACE FUNCTION get_least_loaded_instructor(p_track_id UUID)
RETURNS UUID AS $$
BEGIN
    RETURN (
        SELECT ti.user_id
        FROM track_instructors ti
        LEFT JOIN track_students ts ON ts.assigned_instructor_id = ti.user_id
            AND ts.track_id = p_track_id
        WHERE ti.track_id = p_track_id
        GROUP BY ti.user_id
        ORDER BY COUNT(ts.id) ASC, ti.assigned_at ASC
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_least_loaded_instructor(UUID) IS 'Returns instructor ID with fewest students for given track (for load balancing)';


-- ==============================================================================
-- STEP 9: Grant Permissions
-- ==============================================================================

-- Grant permissions to application role (assuming 'course_creator_app' role exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'course_creator_app') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON track_instructors TO course_creator_app;
        GRANT SELECT, INSERT, UPDATE, DELETE ON track_students TO course_creator_app;
        GRANT SELECT ON track_statistics TO course_creator_app;
        GRANT SELECT ON instructor_load_distribution TO course_creator_app;
        GRANT USAGE ON SEQUENCE track_instructors_id_seq TO course_creator_app;
        GRANT USAGE ON SEQUENCE track_students_id_seq TO course_creator_app;
    END IF;
END $$;


-- ==============================================================================
-- STEP 10: Migration Complete - Add Version Record
-- ==============================================================================

-- Create migrations tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Record this migration
INSERT INTO schema_migrations (version, description)
VALUES ('20251015_subprojects_track_assignments', 'Add sub-projects and track assignment system with load balancing')
ON CONFLICT (version) DO NOTHING;


-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

-- Verify migration
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'New tables: track_instructors, track_students';
    RAISE NOTICE 'Modified tables: projects (3 columns), tracks (1 column)';
    RAISE NOTICE 'New views: track_statistics, instructor_load_distribution';
    RAISE NOTICE 'New triggers: 2 (min instructor enforcement, instructor assignment validation)';
END $$;
