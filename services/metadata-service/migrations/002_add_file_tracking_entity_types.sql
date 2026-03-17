-- Migration: Add File Tracking Entity Types
-- Purpose: Add course_material_upload and course_material_download to valid entity types
-- Date: 2025-10-07

-- Drop existing check constraint
ALTER TABLE entity_metadata DROP CONSTRAINT IF EXISTS entity_metadata_check_type;

-- Re-create check constraint with new entity types
ALTER TABLE entity_metadata ADD CONSTRAINT entity_metadata_check_type
CHECK (entity_type IN (
    'course', 'content', 'user', 'lab', 'project',
    'track', 'quiz', 'exercise', 'video', 'slide',
    'course_material_upload', 'course_material_download',
    'test'
));

COMMENT ON CONSTRAINT entity_metadata_check_type ON entity_metadata IS
'Valid entity types including file tracking types (course_material_upload, course_material_download)';
