/*
 * Migration: Create courses table for training programs
 *
 * BUSINESS CONTEXT:
 * The course-management service DAO expects a 'courses' table to store
 * training program data. This table represents the primary course/program
 * entity with all metadata including pricing, difficulty, organizational
 * assignment, and track/location relationships.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Stores comprehensive course metadata
 * - Links to organizations for multi-tenant isolation
 * - Supports track and location assignment
 * - JSONB metadata field for extensibility (tags, custom fields)
 * - Audit fields (created_at, updated_at)
 *
 * WHY THIS APPROACH:
 * - DAO already references this table in INSERT/UPDATE operations
 * - Frontend sends data matching this schema
 * - Provides clear separation from course_outlines (templates) and
 *   course_instances (specific program runs)
 */

-- Create courses table
CREATE TABLE IF NOT EXISTS course_creator.courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    instructor_id UUID,
    category VARCHAR(255),
    difficulty_level VARCHAR(50) NOT NULL,
    estimated_duration NUMERIC(5,2),
    duration_unit VARCHAR(20),
    price NUMERIC(10,2) DEFAULT 0,
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    organization_id UUID,
    track_id UUID,
    location_id UUID,

    -- Foreign key constraints
    CONSTRAINT fk_courses_instructor
        FOREIGN KEY (instructor_id)
        REFERENCES course_creator.users(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_courses_organization
        FOREIGN KEY (organization_id)
        REFERENCES course_creator.organizations(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_courses_track
        FOREIGN KEY (track_id)
        REFERENCES course_creator.tracks(id)
        ON DELETE SET NULL

    -- Note: location_id FK omitted as locations table may not exist yet
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_courses_instructor ON course_creator.courses(instructor_id);
CREATE INDEX IF NOT EXISTS idx_courses_organization ON course_creator.courses(organization_id);
CREATE INDEX IF NOT EXISTS idx_courses_track ON course_creator.courses(track_id);
CREATE INDEX IF NOT EXISTS idx_courses_published ON course_creator.courses(is_published);
CREATE INDEX IF NOT EXISTS idx_courses_created_at ON course_creator.courses(created_at DESC);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION course_creator.update_courses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_courses_updated_at
    BEFORE UPDATE ON course_creator.courses
    FOR EACH ROW
    EXECUTE FUNCTION course_creator.update_courses_updated_at();

-- Add comment documenting the table
COMMENT ON TABLE course_creator.courses IS 'Training programs/courses with full metadata. This is the primary entity for courses created through the platform UI, distinct from course_outlines (templates) and course_instances (specific runs).';
