-- Migration: 020_add_project_notes.sql
-- Purpose: Create projects table and add project notes field for extensive documentation
--
-- BUSINESS CONTEXT:
-- Organization projects need a notes widget that can store extensive documentation.
-- Notes can be edited directly or uploaded as HTML/Markdown files.
-- This supports project managers in documenting project requirements, guidelines,
-- schedules, and other important information that doesn't fit in the description field.
--
-- TECHNICAL DECISIONS:
-- - Creating projects table in course_creator schema for consistency
-- - Using TEXT type instead of VARCHAR to handle extensive content without length limits
-- - Adding notes_content_type to track format (html/markdown) for proper rendering
-- - Adding notes_updated_at for tracking when notes were last modified
-- - Adding notes_updated_by for audit trail of who made changes

-- First, create the projects table if it doesn't exist
CREATE TABLE IF NOT EXISTS course_creator.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES course_creator.organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    objectives TEXT[],
    target_roles TEXT[],
    duration_weeks INTEGER,
    max_participants INTEGER,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'draft',
    settings JSONB DEFAULT '{}',
    created_by UUID REFERENCES course_creator.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    -- Notes fields for extensive project documentation
    notes TEXT DEFAULT NULL,
    notes_content_type VARCHAR(20) DEFAULT 'markdown',
    notes_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    notes_updated_by UUID REFERENCES course_creator.users(id) DEFAULT NULL,
    UNIQUE(organization_id, slug)
);

-- Create indexes for the projects table
CREATE INDEX IF NOT EXISTS idx_projects_organization ON course_creator.projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_projects_slug ON course_creator.projects(organization_id, slug);
CREATE INDEX IF NOT EXISTS idx_projects_status ON course_creator.projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_notes_content_type ON course_creator.projects(notes_content_type);

-- If the table already exists, add the notes columns
DO $$
BEGIN
    -- Add notes column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'course_creator'
                   AND table_name = 'projects'
                   AND column_name = 'notes') THEN
        ALTER TABLE course_creator.projects ADD COLUMN notes TEXT DEFAULT NULL;
    END IF;

    -- Add notes_content_type column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'course_creator'
                   AND table_name = 'projects'
                   AND column_name = 'notes_content_type') THEN
        ALTER TABLE course_creator.projects ADD COLUMN notes_content_type VARCHAR(20) DEFAULT 'markdown';
    END IF;

    -- Add notes_updated_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'course_creator'
                   AND table_name = 'projects'
                   AND column_name = 'notes_updated_at') THEN
        ALTER TABLE course_creator.projects ADD COLUMN notes_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
    END IF;

    -- Add notes_updated_by column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'course_creator'
                   AND table_name = 'projects'
                   AND column_name = 'notes_updated_by') THEN
        ALTER TABLE course_creator.projects ADD COLUMN notes_updated_by UUID REFERENCES course_creator.users(id) DEFAULT NULL;
    END IF;

    -- Add is_active column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'course_creator'
                   AND table_name = 'projects'
                   AND column_name = 'is_active') THEN
        ALTER TABLE course_creator.projects ADD COLUMN is_active BOOLEAN DEFAULT true;
    END IF;
END $$;

-- Add comments explaining the notes field purpose
COMMENT ON COLUMN course_creator.projects.notes IS 'Extensive project documentation in HTML or Markdown format. Can be edited directly or uploaded from files.';
COMMENT ON COLUMN course_creator.projects.notes_content_type IS 'Format of the notes content: markdown (default) or html';
COMMENT ON COLUMN course_creator.projects.notes_updated_at IS 'Timestamp when notes were last modified';
COMMENT ON COLUMN course_creator.projects.notes_updated_by IS 'UUID of user who last updated the notes';

-- Create trigger for updated_at if it doesn't exist
CREATE OR REPLACE FUNCTION course_creator.update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_projects_updated_at ON course_creator.projects;
CREATE TRIGGER trigger_projects_updated_at
    BEFORE UPDATE ON course_creator.projects
    FOR EACH ROW
    EXECUTE FUNCTION course_creator.update_projects_updated_at();
