-- Migration 004: Add File Deletion Entity Type
-- Business Requirement: Track file deletion operations for audit trail
-- TDD: Migration created after file explorer implementation

-- Update entity_metadata table constraint to include file_deletion
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
    'file_deletion',
    'test'
));

-- Create index for file deletion tracking for audit queries
CREATE INDEX IF NOT EXISTS idx_metadata_file_deletions
ON entity_metadata (entity_id, created_at)
WHERE entity_type = 'file_deletion';

-- Add comment explaining the index
COMMENT ON INDEX idx_metadata_file_deletions IS
'Optimizes audit trail queries for file deletions by entity_id and timestamp';
