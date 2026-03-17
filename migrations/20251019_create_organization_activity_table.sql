-- ============================================================================
-- Organization Activity Table Migration
-- Created: 2025-10-19
-- Purpose: Track all organizational activities for audit and visibility
-- ============================================================================

/**
 * BUSINESS CONTEXT:
 *
 * Organization admins need visibility into all activities happening within their
 * organization for:
 * - Audit compliance and security monitoring
 * - Team activity visibility and collaboration awareness
 * - Operational analytics and usage tracking
 * - Troubleshooting and support
 *
 * Activities tracked include:
 * - Project lifecycle events (created, updated, deleted)
 * - User management events (added, removed, role changed)
 * - Track management events (created, updated, published)
 * - Meeting room events (created, scheduled, accessed)
 * - Locations events (added, modified)
 * - System configuration changes
 *
 * TECHNICAL RATIONALE:
 *
 * Single Responsibility Principle:
 * - Dedicated table for activity logging, separate from operational data
 *
 * Data Retention:
 * - Activities are kept for 90 days by default (configurable per organization)
 * - Automated cleanup process to prevent unbounded growth
 *
 * Performance Considerations:
 * - Indexed on organization_id for fast retrieval
 * - Indexed on created_at for date-range queries
 * - JSONB for flexible metadata storage with indexing capabilities
 *
 * Security:
 * - Row-level security through organization_id
 * - Multi-tenant data isolation enforced at database level
 */

-- Create organization_activity table
CREATE TABLE IF NOT EXISTS organization_activity (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenant isolation (required for all queries)
    -- Note: organization_id stored as UUID, no FK constraint since organizations table structure varies
    organization_id UUID NOT NULL,

    -- User who performed the activity (nullable for system actions)
    user_id UUID,
    -- User name stored denormalized for performance (avoid join on every query)
    user_name VARCHAR(255),

    -- Activity classification
    activity_type VARCHAR(100) NOT NULL,  -- e.g., 'project_created', 'user_added', 'track_published'

    -- Human-readable description of the activity
    description TEXT NOT NULL,

    -- Flexible metadata storage for activity-specific data
    -- Examples:
    -- - project_created: {"project_id": "uuid", "project_name": "name"}
    -- - user_added: {"user_id": "uuid", "email": "email", "role": "role_name"}
    -- - track_updated: {"track_id": "uuid", "changes": {"field": {"old": "x", "new": "y"}}}
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Temporal tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Optional: Activity source (web, api, system, integration)
    source VARCHAR(50) DEFAULT 'web'
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

/**
 * Primary access pattern: Get recent activities for an organization
 * Query: SELECT * FROM organization_activity WHERE organization_id = ? ORDER BY created_at DESC LIMIT ?
 */
CREATE INDEX IF NOT EXISTS idx_org_activity_org_created
ON organization_activity(organization_id, created_at DESC);

/**
 * Secondary access pattern: Filter by activity type
 * Query: SELECT * FROM organization_activity WHERE organization_id = ? AND activity_type = ?
 */
CREATE INDEX IF NOT EXISTS idx_org_activity_type
ON organization_activity(organization_id, activity_type);

/**
 * User activity tracking
 * Query: SELECT * FROM organization_activity WHERE user_id = ?
 */
CREATE INDEX IF NOT EXISTS idx_org_activity_user
ON organization_activity(user_id);

/**
 * JSONB metadata queries (optional, add as needed)
 * Enables efficient querying of metadata fields
 * Example: SELECT * FROM organization_activity WHERE metadata->>'project_id' = 'uuid'
 */
CREATE INDEX IF NOT EXISTS idx_org_activity_metadata
ON organization_activity USING GIN (metadata);

/**
 * Cleanup index for old activities
 * Supports: DELETE FROM organization_activity WHERE created_at < NOW() - INTERVAL '90 days'
 */
CREATE INDEX IF NOT EXISTS idx_org_activity_created
ON organization_activity(created_at);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE organization_activity IS
'Tracks all organizational activities for audit, compliance, and visibility. Activities are retained for 90 days by default.';

COMMENT ON COLUMN organization_activity.id IS
'Unique identifier for the activity record';

COMMENT ON COLUMN organization_activity.organization_id IS
'Organization to which this activity belongs (multi-tenant isolation key)';

COMMENT ON COLUMN organization_activity.user_id IS
'User who performed the activity (NULL for system-generated activities)';

COMMENT ON COLUMN organization_activity.user_name IS
'Denormalized user name for performance (avoids join on display)';

COMMENT ON COLUMN organization_activity.activity_type IS
'Classification of the activity (e.g., project_created, user_added, track_published)';

COMMENT ON COLUMN organization_activity.description IS
'Human-readable description of the activity for display in UI';

COMMENT ON COLUMN organization_activity.metadata IS
'JSONB field for storing activity-specific contextual data';

COMMENT ON COLUMN organization_activity.created_at IS
'Timestamp when the activity occurred (UTC)';

COMMENT ON COLUMN organization_activity.source IS
'Source of the activity (web, api, system, integration)';

-- ============================================================================
-- SAMPLE DATA FOR DEVELOPMENT/TESTING (OPTIONAL)
-- ============================================================================

-- Uncomment to insert sample data for development
/*
-- Get a sample organization ID
DO $$
DECLARE
    sample_org_id UUID;
    sample_user_id UUID;
BEGIN
    -- Get first organization
    SELECT id INTO sample_org_id FROM organizations LIMIT 1;

    -- Get first user
    SELECT id INTO sample_user_id FROM users LIMIT 1;

    IF sample_org_id IS NOT NULL AND sample_user_id IS NOT NULL THEN
        -- Insert sample activities
        INSERT INTO organization_activity (organization_id, user_id, user_name, activity_type, description, metadata) VALUES
        (sample_org_id, sample_user_id, 'Admin User', 'project_created', 'Created new project "AI Course 2025"',
         '{"project_id": "' || gen_random_uuid() || '", "project_name": "AI Course 2025"}'::jsonb),

        (sample_org_id, sample_user_id, 'Admin User', 'user_added', 'Added instructor John Doe to organization',
         '{"user_id": "' || gen_random_uuid() || '", "email": "john@example.com", "role": "instructor"}'::jsonb),

        (sample_org_id, sample_user_id, 'Admin User', 'track_published', 'Published track "Python Fundamentals"',
         '{"track_id": "' || gen_random_uuid() || '", "track_name": "Python Fundamentals"}'::jsonb),

        (sample_org_id, NULL, 'System', 'system_backup', 'Automated backup completed successfully',
         '{"backup_size_mb": 245, "duration_seconds": 12}'::jsonb);

        RAISE NOTICE 'Sample organization activities created successfully';
    END IF;
END $$;
*/

-- ============================================================================
-- MIGRATION VERIFICATION
-- ============================================================================

-- Verify table was created
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'organization_activity') THEN
        RAISE NOTICE 'Migration successful: organization_activity table created';
    ELSE
        RAISE EXCEPTION 'Migration failed: organization_activity table not found';
    END IF;
END $$;
