-- Migration: Add Track and Locations Support to Courses
-- Purpose: Enable courses to be associated with tracks and locations for org-based course delivery
-- Author: Course Creator Platform
-- Date: 2025-10-18

-- =============================================================================
-- FORWARD MIGRATION
-- =============================================================================

-- Add track_id and location_id columns to courses table
-- This allows courses to be part of a curriculum track and delivered at a specific locations

ALTER TABLE courses
ADD COLUMN IF NOT EXISTS track_id UUID REFERENCES tracks(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES course_creator.organizations(id) ON DELETE CASCADE;

-- Add comment documentation
COMMENT ON COLUMN courses.track_id IS 'Reference to the curriculum track this course belongs to (optional)';
COMMENT ON COLUMN courses.location_id IS 'Reference to the locations where this course is delivered (optional)';
COMMENT ON COLUMN courses.organization_id IS 'Reference to the organization that owns this course (for multi-tenant isolation)';

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_courses_track_id ON courses(track_id) WHERE track_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_courses_location_id ON courses(location_id) WHERE location_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_courses_organization_id ON courses(organization_id) WHERE organization_id IS NOT NULL;

-- Create composite index for common queries (courses by track and locations)
CREATE INDEX IF NOT EXISTS idx_courses_track_location ON courses(track_id, location_id)
WHERE track_id IS NOT NULL AND location_id IS NOT NULL;

-- Create view to join courses with track and locations details
CREATE OR REPLACE VIEW courses_with_context AS
SELECT
    c.id as course_id,
    c.title as course_title,
    c.description as course_description,
    c.instructor_id,
    c.category,
    c.difficulty_level,
    c.estimated_duration,
    c.duration_unit,
    c.price,
    c.is_published,
    c.status as course_status,
    c.created_at as course_created_at,
    c.updated_at as course_updated_at,
    -- Track information
    t.id as track_id,
    t.name as track_name,
    t.slug as track_slug,
    t.difficulty as track_difficulty,
    t.estimated_hours as track_estimated_hours,
    t.status as track_status,
    -- Locations information
    l.id as location_id,
    l.name as location_name,
    l.location_country,
    l.location_region,
    l.location_city,
    l.timezone,
    l.status as location_status,
    -- Organization information
    o.id as organization_id,
    o.name as organization_name,
    o.slug as organization_slug
FROM courses c
LEFT JOIN tracks t ON c.track_id = t.id
LEFT JOIN locations l ON c.location_id = l.id
LEFT JOIN course_creator.organizations o ON c.organization_id = o.id;

COMMENT ON VIEW courses_with_context IS 'Comprehensive view of courses with their track, locations, and organization context';

-- =============================================================================
-- ROLLBACK MIGRATION
-- =============================================================================

-- DROP VIEW IF EXISTS courses_with_context;
-- DROP INDEX IF EXISTS idx_courses_track_location;
-- DROP INDEX IF EXISTS idx_courses_organization_id;
-- DROP INDEX IF EXISTS idx_courses_location_id;
-- DROP INDEX IF EXISTS idx_courses_track_id;
-- ALTER TABLE courses DROP COLUMN IF EXISTS organization_id;
-- ALTER TABLE courses DROP COLUMN IF EXISTS location_id;
-- ALTER TABLE courses DROP COLUMN IF EXISTS track_id;
