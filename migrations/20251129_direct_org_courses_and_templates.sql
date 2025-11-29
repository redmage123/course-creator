/**
 * Migration: Direct Organization Courses and Slide Templates
 * Version: 3.3.2
 * Date: 2025-11-29
 *
 * BUSINESS PURPOSE:
 * This migration enables organizations to create courses directly without requiring
 * projects, subprojects, or tracks. It also adds slide template functionality for
 * consistent course presentation branding.
 *
 * CHANGES:
 * 1. Add check constraint to validate organizational course context
 * 2. Create slide_templates table for organization-level template management
 * 3. Add template_id foreign key to slides table
 * 4. Create organization_content_overview view for unified project/course listing
 *
 * ROLLBACK:
 * See bottom of file for rollback statements
 */

-- ============================================================================
-- SECTION 1: Validate and Update Course Organizational Context
-- ============================================================================

/**
 * Add check constraint ensuring valid organizational context combinations:
 * 1. Standalone course: organization_id IS NULL AND track_id IS NULL
 * 2. Direct org course: organization_id IS NOT NULL AND track_id IS NULL
 * 3. Track-based course: organization_id IS NOT NULL AND track_id IS NOT NULL
 * 4. INVALID: organization_id IS NULL AND track_id IS NOT NULL (orphaned track)
 */
DO $$
BEGIN
    -- Only add constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_course_organizational_context'
    ) THEN
        ALTER TABLE courses ADD CONSTRAINT check_course_organizational_context
        CHECK (
            -- Standalone: no org, no track (independent instructor course)
            (organization_id IS NULL AND track_id IS NULL)
            OR
            -- Direct org: org set, no track (org creates course directly)
            (organization_id IS NOT NULL AND track_id IS NULL)
            OR
            -- Track-based: both set (traditional org→project→track→course)
            (organization_id IS NOT NULL AND track_id IS NOT NULL)
        );

        RAISE NOTICE 'Added check_course_organizational_context constraint to courses table';
    ELSE
        RAISE NOTICE 'Constraint check_course_organizational_context already exists';
    END IF;
END $$;


-- ============================================================================
-- SECTION 2: Create Slide Templates Table
-- ============================================================================

/**
 * slide_templates table stores organization-level presentation templates
 * that can be applied to course slides for consistent branding.
 *
 * BUSINESS RULES:
 * - Templates belong to an organization (organization_id required)
 * - Default templates are marked with is_default flag (one per org)
 * - Templates contain CSS/styling configuration in template_config JSONB
 * - Templates can include header/footer content
 */
CREATE TABLE IF NOT EXISTS slide_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Template identification
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Template configuration (JSONB for flexibility)
    template_config JSONB NOT NULL DEFAULT '{
        "theme": "default",
        "primaryColor": "#1976d2",
        "secondaryColor": "#dc004e",
        "fontFamily": "Roboto, sans-serif",
        "headerStyle": {},
        "footerStyle": {},
        "slideStyle": {}
    }'::jsonb,

    -- Optional header/footer content
    header_html TEXT,
    footer_html TEXT,

    -- Logo and branding
    logo_url VARCHAR(500),
    background_image_url VARCHAR(500),

    -- Template status
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit fields
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique template names within organization
    CONSTRAINT unique_template_name_per_org UNIQUE (organization_id, name)
);

-- Index for fast template lookup by organization
CREATE INDEX IF NOT EXISTS idx_slide_templates_organization
ON slide_templates(organization_id) WHERE is_active = TRUE;

-- Index for default template lookup
CREATE INDEX IF NOT EXISTS idx_slide_templates_default
ON slide_templates(organization_id, is_default) WHERE is_default = TRUE;

-- Trigger to ensure only one default template per organization
CREATE OR REPLACE FUNCTION ensure_single_default_template()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        UPDATE slide_templates
        SET is_default = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE organization_id = NEW.organization_id
          AND id != NEW.id
          AND is_default = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_ensure_single_default_template ON slide_templates;
CREATE TRIGGER trigger_ensure_single_default_template
BEFORE INSERT OR UPDATE ON slide_templates
FOR EACH ROW
EXECUTE FUNCTION ensure_single_default_template();

COMMENT ON TABLE slide_templates IS
'Organization-level slide templates for consistent course presentation branding';


-- ============================================================================
-- SECTION 3: Add Template Reference to Slides Table
-- ============================================================================

/**
 * Add template_id to slides table to link slides with templates.
 * This is optional - slides without a template use default styling.
 */
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'slides' AND column_name = 'template_id'
    ) THEN
        ALTER TABLE slides ADD COLUMN template_id UUID REFERENCES slide_templates(id) ON DELETE SET NULL;

        RAISE NOTICE 'Added template_id column to slides table';
    ELSE
        RAISE NOTICE 'Column template_id already exists in slides table';
    END IF;
END $$;

-- Index for template usage tracking
CREATE INDEX IF NOT EXISTS idx_slides_template ON slides(template_id) WHERE template_id IS NOT NULL;


-- ============================================================================
-- SECTION 4: Create Organization Content Overview View
-- ============================================================================

/**
 * organization_content_overview provides a unified view of all projects
 * and direct courses within an organization for the organization overview page.
 *
 * This view supports the new workflow where organizations can have:
 * - Projects (with optional tracks and courses)
 * - Direct courses (not attached to any project/track)
 */
CREATE OR REPLACE VIEW organization_content_overview AS
SELECT
    o.id as organization_id,
    o.name as organization_name,

    -- Project info (NULL for direct courses)
    p.id as project_id,
    p.name as project_name,
    p.status as project_status,
    p.created_at as project_created_at,

    -- Course info
    c.id as course_id,
    c.title as course_title,
    c.description as course_description,
    c.difficulty_level,
    c.is_published,
    c.created_at as course_created_at,

    -- Track info (for track-based courses)
    t.id as track_id,
    t.name as track_name,

    -- Content type indicator
    CASE
        WHEN p.id IS NOT NULL AND t.id IS NOT NULL THEN 'track_course'
        WHEN p.id IS NOT NULL AND t.id IS NULL THEN 'project_course'
        WHEN c.id IS NOT NULL AND p.id IS NULL THEN 'direct_course'
        ELSE 'project_only'
    END as content_type,

    -- Instructor info
    u.id as instructor_id,
    u.username as instructor_name

FROM organizations o

-- Left join to get projects
LEFT JOIN projects p ON p.organization_id = o.id

-- Left join to get tracks (tracks belong to projects)
LEFT JOIN tracks t ON t.project_id = p.id OR t.organization_id = o.id

-- Left join to get courses (can be direct, track-based, or via junction)
LEFT JOIN courses c ON (
    -- Direct organization course (no track)
    (c.organization_id = o.id AND c.track_id IS NULL)
    OR
    -- Track-based course
    (c.track_id = t.id)
)

-- Join instructor info
LEFT JOIN users u ON c.instructor_id::uuid = u.id

WHERE o.is_active = TRUE
ORDER BY o.name, p.name NULLS LAST, t.name NULLS LAST, c.title;

COMMENT ON VIEW organization_content_overview IS
'Unified view of organization content including projects and direct courses for the organization overview page';


-- ============================================================================
-- SECTION 5: Create Helper Functions
-- ============================================================================

/**
 * Function to get organization content summary (projects count, direct courses count)
 */
CREATE OR REPLACE FUNCTION get_organization_content_summary(org_id UUID)
RETURNS TABLE (
    project_count BIGINT,
    direct_course_count BIGINT,
    track_course_count BIGINT,
    total_course_count BIGINT,
    published_course_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM projects WHERE organization_id = org_id)::BIGINT as project_count,
        (SELECT COUNT(*) FROM courses WHERE organization_id = org_id AND track_id IS NULL)::BIGINT as direct_course_count,
        (SELECT COUNT(*) FROM courses c
         JOIN tracks t ON c.track_id = t.id
         WHERE t.organization_id = org_id)::BIGINT as track_course_count,
        (SELECT COUNT(*) FROM courses WHERE organization_id = org_id)::BIGINT as total_course_count,
        (SELECT COUNT(*) FROM courses WHERE organization_id = org_id AND is_published = TRUE)::BIGINT as published_course_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_organization_content_summary IS
'Returns content counts for an organization including projects and courses';


-- ============================================================================
-- ROLLBACK STATEMENTS (for manual rollback if needed)
-- ============================================================================
/*
-- To rollback this migration:

-- Remove template reference from slides
ALTER TABLE slides DROP COLUMN IF EXISTS template_id;

-- Drop slide templates table and related objects
DROP TRIGGER IF EXISTS trigger_ensure_single_default_template ON slide_templates;
DROP FUNCTION IF EXISTS ensure_single_default_template();
DROP TABLE IF EXISTS slide_templates CASCADE;

-- Drop view and function
DROP VIEW IF EXISTS organization_content_overview;
DROP FUNCTION IF EXISTS get_organization_content_summary(UUID);

-- Remove course organizational context constraint
ALTER TABLE courses DROP CONSTRAINT IF EXISTS check_course_organizational_context;
*/


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Migration 20251129_direct_org_courses_and_templates completed successfully';
END $$;
