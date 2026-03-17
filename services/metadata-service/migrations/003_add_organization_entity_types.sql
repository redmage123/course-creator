-- Migration 003: Add Organization-Related Entity Types
-- Business Requirement: Track organization logo uploads and document uploads
-- TDD: Migration created after org admin drag-drop integration

-- Update entity_metadata table constraint to include organization entity types
ALTER TABLE entity_metadata DROP CONSTRAINT IF EXISTS entity_metadata_check_type;

ALTER TABLE entity_metadata ADD CONSTRAINT entity_metadata_check_type
CHECK (entity_type IN (
    'course',
    'content',
    'user',
    'lab',
    'project',
    'track',
    'quiz',
    'exercise',
    'video',
    'slide',
    'course_material_upload',
    'course_material_download',
    'organization_logo_upload',
    'organization_document_upload',
    'test'
));

-- Create index for organization uploads for faster queries
CREATE INDEX IF NOT EXISTS idx_metadata_org_uploads
ON entity_metadata (entity_id)
WHERE entity_type IN ('organization_logo_upload', 'organization_document_upload');

-- Add comment explaining the index
COMMENT ON INDEX idx_metadata_org_uploads IS
'Optimizes queries for organization file uploads (logos and documents)';
