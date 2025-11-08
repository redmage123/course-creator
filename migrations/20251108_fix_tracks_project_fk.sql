/*
 * Migration: Fix tracks table foreign key to reference courses instead of projects
 *
 * BUSINESS CONTEXT:
 * The tracks table has a foreign key constraint pointing to a non-existent "projects" table.
 * Training programs/projects are actually stored in the "courses" table, so the FK
 * must be updated to reference courses.id instead of projects.id.
 *
 * TECHNICAL IMPLEMENTATION:
 * 1. Drop the old FK constraint that references projects table
 * 2. Add new FK constraint that references course_creator.courses table
 *
 * WHY THIS APPROACH:
 * - Enables proper referential integrity for track-to-program relationships
 * - Aligns database schema with actual data model (courses = projects)
 * - Allows track creation to succeed by validating against existing courses
 */

-- Drop the old foreign key constraint that references non-existent projects table
ALTER TABLE course_creator.tracks
DROP CONSTRAINT IF EXISTS tracks_project_id_fkey;

-- Add new foreign key constraint that references courses table
ALTER TABLE course_creator.tracks
ADD CONSTRAINT tracks_project_id_fkey
    FOREIGN KEY (project_id)
    REFERENCES course_creator.courses(id)
    ON DELETE CASCADE;

-- Add comment documenting the change
COMMENT ON CONSTRAINT tracks_project_id_fkey ON course_creator.tracks IS 'References courses table (training programs/projects), updated from non-existent projects table';
