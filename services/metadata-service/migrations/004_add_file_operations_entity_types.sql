-- Migration 004: Add File Explorer Operations Entity Types
-- Business Requirement: Track file uploads, downloads, renames, and deletions through file explorer
-- TDD: Migration created after file explorer module implementation

-- Update entity_metadata table constraint to include file explorer entity types
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
    'file_upload',
    'file_download',
    'file_rename',
    'file_delete',
    'test'
));

-- Create index for file operations for faster queries
CREATE INDEX IF NOT EXISTS idx_metadata_file_operations
ON entity_metadata (entity_id)
WHERE entity_type IN ('file_upload', 'file_download', 'file_rename', 'file_delete');

-- Create index for file operations by user
CREATE INDEX IF NOT EXISTS idx_metadata_file_ops_by_user
ON entity_metadata ((metadata->>'uploaded_by'), (metadata->>'downloaded_by'), (metadata->>'renamed_by'), (metadata->>'deleted_by'))
WHERE entity_type IN ('file_upload', 'file_download', 'file_rename', 'file_delete');

-- Add comment explaining the indexes
COMMENT ON INDEX idx_metadata_file_operations IS
'Optimizes queries for file explorer operations (upload, download, rename, delete)';

COMMENT ON INDEX idx_metadata_file_ops_by_user IS
'Optimizes queries for file operations by specific users for audit trail';
