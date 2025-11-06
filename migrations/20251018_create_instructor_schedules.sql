-- Migration: Instructor Scheduling System
-- Purpose: Enable time-based scheduling of instructors to courses with conflict detection
-- Author: Course Creator Platform
-- Date: 2025-10-18
--
-- BUSINESS CONTEXT:
-- - Org admins need to create schedules mapping which instructor teaches which course at what times
-- - Supports recurring schedules (weekly patterns)
-- - Prevents scheduling conflicts (same instructor, overlapping times)
-- - Tracks room assignments and locations details
-- - Enables calendar view and resource planning

-- =============================================================================
-- FORWARD MIGRATION
-- =============================================================================

-- Create instructor_schedules table
CREATE TABLE IF NOT EXISTS instructor_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core relationships
    instructor_id UUID NOT NULL REFERENCES course_creator.users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES course_creator.organizations(id) ON DELETE CASCADE,
    location_id UUID REFERENCES locations(id) ON DELETE SET NULL,

    -- Schedule details
    schedule_name VARCHAR(255),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Sunday, 6=Saturday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    CONSTRAINT schedule_time_valid CHECK (start_time < end_time),

    -- Locations details
    room_number VARCHAR(50),
    building VARCHAR(100),
    virtual_meeting_link TEXT,
    meeting_platform VARCHAR(50) CHECK (meeting_platform IN ('zoom', 'teams', 'google_meet', 'webex', 'in_person', 'hybrid')),

    -- Recurrence pattern
    is_recurring BOOLEAN NOT NULL DEFAULT TRUE,
    recurrence_pattern VARCHAR(50) DEFAULT 'weekly' CHECK (recurrence_pattern IN ('weekly', 'biweekly', 'monthly', 'one_time')),

    -- Effective date range
    effective_from DATE NOT NULL,
    effective_until DATE,
    CONSTRAINT schedule_dates_valid CHECK (effective_from <= effective_until OR effective_until IS NULL),

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'completed', 'suspended')),

    -- Capacity and attendance tracking
    max_students INTEGER,
    expected_attendance INTEGER,

    -- Notes and special instructions
    notes TEXT,
    preparation_notes TEXT, -- What instructor needs to prepare

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES course_creator.users(id) ON DELETE SET NULL,

    -- Additional metadata (calendar IDs, integration data, etc.)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add table comment
COMMENT ON TABLE instructor_schedules IS 'Time-based scheduling for instructor-course assignments with conflict detection support';

-- Add column comments
COMMENT ON COLUMN instructor_schedules.instructor_id IS 'Instructor assigned to this time slot';
COMMENT ON COLUMN instructor_schedules.course_id IS 'Course being taught in this time slot';
COMMENT ON COLUMN instructor_schedules.day_of_week IS 'Day of week: 0=Sunday, 1=Monday, ..., 6=Saturday';
COMMENT ON COLUMN instructor_schedules.start_time IS 'Start time of the teaching session';
COMMENT ON COLUMN instructor_schedules.end_time IS 'End time of the teaching session';
COMMENT ON COLUMN instructor_schedules.room_number IS 'Room number where session takes place';
COMMENT ON COLUMN instructor_schedules.meeting_platform IS 'Platform: zoom, teams, google_meet, webex, in_person, hybrid';
COMMENT ON COLUMN instructor_schedules.is_recurring IS 'Whether this is a recurring schedule';
COMMENT ON COLUMN instructor_schedules.recurrence_pattern IS 'Pattern: weekly, biweekly, monthly, one_time';
COMMENT ON COLUMN instructor_schedules.effective_from IS 'Start date for this schedule';
COMMENT ON COLUMN instructor_schedules.effective_until IS 'End date for this schedule (NULL = ongoing)';

-- Create indexes for efficient querying
CREATE INDEX idx_schedules_instructor ON instructor_schedules(instructor_id)
    WHERE status = 'active';
CREATE INDEX idx_schedules_course ON instructor_schedules(course_id)
    WHERE status = 'active';
CREATE INDEX idx_schedules_location ON instructor_schedules(location_id)
    WHERE location_id IS NOT NULL;
CREATE INDEX idx_schedules_organization ON instructor_schedules(organization_id);
CREATE INDEX idx_schedules_day_time ON instructor_schedules(day_of_week, start_time, end_time)
    WHERE status = 'active';
CREATE INDEX idx_schedules_effective_dates ON instructor_schedules(effective_from, effective_until)
    WHERE status = 'active';
CREATE INDEX idx_schedules_status ON instructor_schedules(status);

-- Create composite index for conflict detection
CREATE INDEX idx_schedules_conflict_detection ON instructor_schedules(
    instructor_id, day_of_week, start_time, end_time, effective_from, effective_until
) WHERE status = 'active';

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_instructor_schedules_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_instructor_schedules_timestamp
    BEFORE UPDATE ON instructor_schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_instructor_schedules_timestamp();

-- Create comprehensive view for schedule details
CREATE OR REPLACE VIEW instructor_schedules_view AS
SELECT
    s.id as schedule_id,
    s.schedule_name,
    s.instructor_id,
    u.full_name as instructor_name,
    u.email as instructor_email,
    s.course_id,
    c.title as course_title,
    c.difficulty_level as course_difficulty,
    s.day_of_week,
    CASE s.day_of_week
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as day_name,
    s.start_time,
    s.end_time,
    s.start_time::TEXT || ' - ' || s.end_time::TEXT as time_slot,
    EXTRACT(EPOCH FROM (s.end_time - s.start_time))/3600 as duration_hours,
    s.room_number,
    s.building,
    s.meeting_platform,
    s.virtual_meeting_link,
    s.is_recurring,
    s.recurrence_pattern,
    s.effective_from,
    s.effective_until,
    s.status,
    s.max_students,
    s.expected_attendance,
    -- Locations information
    l.id as location_id,
    l.name as location_name,
    l.location_city,
    l.location_country,
    l.timezone,
    -- Track information
    t.id as track_id,
    t.name as track_name,
    -- Organization information
    o.id as organization_id,
    o.name as organization_name,
    -- Creator information
    creator.full_name as created_by_name,
    s.created_at,
    s.updated_at
FROM instructor_schedules s
JOIN course_creator.users u ON s.instructor_id = u.id
JOIN courses c ON s.course_id = c.id
LEFT JOIN locations l ON s.location_id = l.id
LEFT JOIN tracks t ON c.track_id = t.id
JOIN course_creator.organizations o ON s.organization_id = o.id
LEFT JOIN course_creator.users creator ON s.created_by = creator.id;

COMMENT ON VIEW instructor_schedules_view IS 'Comprehensive view of instructor schedules with instructor, course, locations, and organization details';

-- Create weekly schedule summary view
CREATE OR REPLACE VIEW instructor_weekly_schedule AS
SELECT
    instructor_id,
    instructor_name,
    organization_id,
    organization_name,
    day_of_week,
    day_name,
    COUNT(*) as sessions_count,
    SUM(duration_hours) as total_hours_per_day,
    STRING_AGG(
        course_title || ' (' || time_slot || ')',
        ', '
        ORDER BY start_time
    ) as daily_schedule
FROM instructor_schedules_view
WHERE status = 'active'
  AND (effective_from <= CURRENT_DATE)
  AND (effective_until IS NULL OR effective_until >= CURRENT_DATE)
GROUP BY instructor_id, instructor_name, organization_id, organization_name, day_of_week, day_name
ORDER BY instructor_name, day_of_week;

COMMENT ON VIEW instructor_weekly_schedule IS 'Weekly schedule summary for each instructor showing daily sessions and hours';

-- Create function to detect scheduling conflicts
CREATE OR REPLACE FUNCTION check_schedule_conflict(
    p_instructor_id UUID,
    p_day_of_week INTEGER,
    p_start_time TIME,
    p_end_time TIME,
    p_effective_from DATE,
    p_effective_until DATE DEFAULT NULL,
    p_exclude_schedule_id UUID DEFAULT NULL
)
RETURNS TABLE(
    conflict_schedule_id UUID,
    conflict_course_title VARCHAR,
    conflict_day_of_week INTEGER,
    conflict_start_time TIME,
    conflict_end_time TIME,
    conflict_location VARCHAR,
    conflict_room VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id as conflict_schedule_id,
        c.title as conflict_course_title,
        s.day_of_week as conflict_day_of_week,
        s.start_time as conflict_start_time,
        s.end_time as conflict_end_time,
        l.name as conflict_location,
        s.room_number as conflict_room
    FROM instructor_schedules s
    JOIN courses c ON s.course_id = c.id
    LEFT JOIN locations l ON s.location_id = l.id
    WHERE s.instructor_id = p_instructor_id
      AND s.status = 'active'
      AND s.day_of_week = p_day_of_week
      AND (p_exclude_schedule_id IS NULL OR s.id != p_exclude_schedule_id)
      -- Time overlap check
      AND (
          (s.start_time <= p_start_time AND s.end_time > p_start_time) OR  -- Existing starts before, ends during new
          (s.start_time < p_end_time AND s.end_time >= p_end_time) OR      -- Existing starts during, ends after new
          (s.start_time >= p_start_time AND s.end_time <= p_end_time)      -- Existing completely within new
      )
      -- Date range overlap check
      AND (
          (s.effective_from <= p_effective_from AND (s.effective_until IS NULL OR s.effective_until >= p_effective_from)) OR
          (s.effective_from <= COALESCE(p_effective_until, '9999-12-31'::DATE) AND (s.effective_until IS NULL OR s.effective_until >= COALESCE(p_effective_until, '9999-12-31'::DATE))) OR
          (s.effective_from >= p_effective_from AND s.effective_from <= COALESCE(p_effective_until, '9999-12-31'::DATE))
      );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_schedule_conflict IS 'Detect scheduling conflicts for an instructor based on day, time, and date range overlaps';

-- Create function to get instructor's schedule for a date range
CREATE OR REPLACE FUNCTION get_instructor_schedule(
    p_instructor_id UUID,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE(
    schedule_id UUID,
    course_title VARCHAR,
    day_of_week INTEGER,
    day_name VARCHAR,
    start_time TIME,
    end_time TIME,
    location_name VARCHAR,
    room_number VARCHAR,
    meeting_platform VARCHAR,
    virtual_meeting_link TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id as schedule_id,
        c.title as course_title,
        s.day_of_week,
        CASE s.day_of_week
            WHEN 0 THEN 'Sunday'
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            WHEN 6 THEN 'Saturday'
        END::VARCHAR as day_name,
        s.start_time,
        s.end_time,
        l.name as location_name,
        s.room_number,
        s.meeting_platform,
        s.virtual_meeting_link
    FROM instructor_schedules s
    JOIN courses c ON s.course_id = c.id
    LEFT JOIN locations l ON s.location_id = l.id
    WHERE s.instructor_id = p_instructor_id
      AND s.status = 'active'
      AND s.effective_from <= p_end_date
      AND (s.effective_until IS NULL OR s.effective_until >= p_start_date)
    ORDER BY s.day_of_week, s.start_time;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_instructor_schedule IS 'Get instructor''s active schedule for a specific date range';

-- =============================================================================
-- ROLLBACK MIGRATION
-- =============================================================================

-- DROP FUNCTION IF EXISTS get_instructor_schedule;
-- DROP FUNCTION IF EXISTS check_schedule_conflict;
-- DROP VIEW IF EXISTS instructor_weekly_schedule;
-- DROP VIEW IF EXISTS instructor_schedules_view;
-- DROP TRIGGER IF EXISTS trigger_update_instructor_schedules_timestamp ON instructor_schedules;
-- DROP FUNCTION IF EXISTS update_instructor_schedules_timestamp;
-- DROP INDEX IF EXISTS idx_schedules_conflict_detection;
-- DROP INDEX IF EXISTS idx_schedules_status;
-- DROP INDEX IF EXISTS idx_schedules_effective_dates;
-- DROP INDEX IF EXISTS idx_schedules_day_time;
-- DROP INDEX IF EXISTS idx_schedules_organization;
-- DROP INDEX IF EXISTS idx_schedules_location;
-- DROP INDEX IF EXISTS idx_schedules_course;
-- DROP INDEX IF EXISTS idx_schedules_instructor;
-- DROP TABLE IF EXISTS instructor_schedules;
