-- Migration: 026_content_versioning.sql
-- Description: Content versioning system for non-destructive editing and audit trails
--
-- WHAT: Creates tables for version control of all content types
-- WHERE: Used across course, module, lesson, quiz, and other content entities
-- WHY: Enables full version history, rollback, branching, and approval workflows
--
-- Features:
-- - Version snapshots with content hash integrity
-- - Branch-based parallel development
-- - Multi-reviewer approval workflows
-- - Edit locking to prevent conflicts
-- - Merge tracking for branch reconciliation

-- =============================================================================
-- Enum Types
-- =============================================================================

-- Content entity types that can be versioned
DO $$ BEGIN
    CREATE TYPE content_entity_type AS ENUM (
        'course',
        'module',
        'lesson',
        'quiz',
        'question',
        'assignment',
        'resource',
        'syllabus',
        'interactive_element',
        'slide',
        'video',
        'document'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Version lifecycle status
DO $$ BEGIN
    CREATE TYPE version_status AS ENUM (
        'draft',
        'pending_review',
        'in_review',
        'approved',
        'rejected',
        'published',
        'superseded',
        'archived'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Types of changes in version diffs
DO $$ BEGIN
    CREATE TYPE change_type AS ENUM (
        'created',
        'updated',
        'deleted',
        'renamed',
        'moved',
        'restructured'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Approval decision status
DO $$ BEGIN
    CREATE TYPE approval_status AS ENUM (
        'pending',
        'approved',
        'rejected',
        'changes_requested',
        'withdrawn'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Merge strategies for branch reconciliation
DO $$ BEGIN
    CREATE TYPE merge_strategy AS ENUM (
        'ours',
        'theirs',
        'manual',
        'auto'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Content Versions: Snapshots of content at specific points in time
CREATE TABLE IF NOT EXISTS content_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type content_entity_type NOT NULL,
    entity_id UUID NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,

    -- Content snapshot
    content_data JSONB NOT NULL DEFAULT '{}',
    content_hash VARCHAR(64) NOT NULL,

    -- Metadata
    title VARCHAR(500),
    description TEXT,
    changelog TEXT,
    tags TEXT[] DEFAULT '{}',

    -- Status
    status version_status NOT NULL DEFAULT 'draft',
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    is_latest BOOLEAN NOT NULL DEFAULT TRUE,

    -- Authorship
    created_by UUID NOT NULL,
    organization_id UUID,

    -- Lineage
    parent_version_id UUID REFERENCES content_versions(id),
    branch_id UUID,
    branch_name VARCHAR(100) NOT NULL DEFAULT 'main',

    -- Size and metrics
    content_size_bytes INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,

    -- Review
    reviewer_id UUID,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    UNIQUE(entity_type, entity_id, version_number, branch_name)
);

-- Version Branches: Parallel development tracks
CREATE TABLE IF NOT EXISTS version_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type content_entity_type NOT NULL,
    entity_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Branch point
    parent_branch_id UUID REFERENCES version_branches(id),
    parent_branch_name VARCHAR(100) DEFAULT 'main',
    branched_from_version_id UUID REFERENCES content_versions(id),

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,

    -- Merge info
    merged_to_branch_id UUID REFERENCES version_branches(id),
    merged_at TIMESTAMP WITH TIME ZONE,
    merge_commit_version_id UUID REFERENCES content_versions(id),

    -- Ownership
    created_by UUID NOT NULL,
    organization_id UUID,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    UNIQUE(entity_type, entity_id, name)
);

-- Update content_versions to reference branches
ALTER TABLE content_versions
ADD CONSTRAINT fk_content_versions_branch
FOREIGN KEY (branch_id) REFERENCES version_branches(id);

-- Version Diffs: Changes between versions
CREATE TABLE IF NOT EXISTS version_diffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type content_entity_type NOT NULL,
    entity_id UUID NOT NULL,
    source_version_id UUID NOT NULL REFERENCES content_versions(id),
    target_version_id UUID NOT NULL REFERENCES content_versions(id),

    -- Diff data
    changes JSONB NOT NULL DEFAULT '[]',

    -- Statistics
    fields_added INTEGER DEFAULT 0,
    fields_modified INTEGER DEFAULT 0,
    fields_deleted INTEGER DEFAULT 0,
    total_changes INTEGER DEFAULT 0,

    -- Content changes
    words_added INTEGER DEFAULT 0,
    words_deleted INTEGER DEFAULT 0,
    net_word_change INTEGER DEFAULT 0,

    -- Metadata
    generated_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    UNIQUE(source_version_id, target_version_id)
);

-- Version Approvals: Review decisions
CREATE TABLE IF NOT EXISTS version_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES content_versions(id),
    reviewer_id UUID NOT NULL,

    -- Decision
    status approval_status NOT NULL DEFAULT 'pending',
    decision_notes TEXT,

    -- Change requests
    requested_changes JSONB DEFAULT '[]',

    -- Metadata
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMP WITH TIME ZONE,

    -- Follow-up
    changes_addressed BOOLEAN NOT NULL DEFAULT FALSE,
    follow_up_version_id UUID REFERENCES content_versions(id),

    -- Constraints
    UNIQUE(version_id, reviewer_id)
);

-- Content Locks: Edit locking for conflict prevention
CREATE TABLE IF NOT EXISTS content_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type content_entity_type NOT NULL,
    entity_id UUID NOT NULL,
    version_id UUID NOT NULL REFERENCES content_versions(id),

    -- Lock holder
    locked_by UUID NOT NULL,
    lock_reason TEXT,

    -- Lock settings
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    lock_level VARCHAR(20) NOT NULL DEFAULT 'exclusive',
    inherited_from_parent BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timing
    acquired_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Metadata
    user_agent TEXT,
    ip_address VARCHAR(45)
);

-- Version Merges: Branch merge history
CREATE TABLE IF NOT EXISTS version_merges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type content_entity_type NOT NULL,
    entity_id UUID NOT NULL,

    -- Merge participants
    source_branch_id UUID NOT NULL REFERENCES version_branches(id),
    source_version_id UUID NOT NULL REFERENCES content_versions(id),
    target_branch_id UUID NOT NULL REFERENCES version_branches(id),
    target_version_id UUID NOT NULL REFERENCES content_versions(id),

    -- Result
    result_version_id UUID REFERENCES content_versions(id),
    merge_strategy merge_strategy NOT NULL DEFAULT 'auto',

    -- Status
    is_complete BOOLEAN NOT NULL DEFAULT FALSE,
    had_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    conflicts_resolved BOOLEAN NOT NULL DEFAULT TRUE,

    -- Conflicts
    conflict_details JSONB DEFAULT '[]',

    -- Authorship
    merged_by UUID NOT NULL,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Content Versions indexes
CREATE INDEX IF NOT EXISTS idx_content_versions_entity
ON content_versions(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_content_versions_status
ON content_versions(status);

CREATE INDEX IF NOT EXISTS idx_content_versions_current
ON content_versions(entity_type, entity_id, is_current)
WHERE is_current = TRUE;

CREATE INDEX IF NOT EXISTS idx_content_versions_latest
ON content_versions(entity_type, entity_id, branch_name, is_latest)
WHERE is_latest = TRUE;

CREATE INDEX IF NOT EXISTS idx_content_versions_branch
ON content_versions(branch_id);

CREATE INDEX IF NOT EXISTS idx_content_versions_parent
ON content_versions(parent_version_id);

CREATE INDEX IF NOT EXISTS idx_content_versions_creator
ON content_versions(created_by);

CREATE INDEX IF NOT EXISTS idx_content_versions_org
ON content_versions(organization_id);

CREATE INDEX IF NOT EXISTS idx_content_versions_hash
ON content_versions(content_hash);

CREATE INDEX IF NOT EXISTS idx_content_versions_created
ON content_versions(created_at DESC);

-- Version Branches indexes
CREATE INDEX IF NOT EXISTS idx_version_branches_entity
ON version_branches(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_version_branches_active
ON version_branches(entity_type, entity_id, is_active)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_version_branches_default
ON version_branches(entity_type, entity_id, is_default)
WHERE is_default = TRUE;

-- Version Diffs indexes
CREATE INDEX IF NOT EXISTS idx_version_diffs_entity
ON version_diffs(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_version_diffs_source
ON version_diffs(source_version_id);

CREATE INDEX IF NOT EXISTS idx_version_diffs_target
ON version_diffs(target_version_id);

-- Version Approvals indexes
CREATE INDEX IF NOT EXISTS idx_version_approvals_version
ON version_approvals(version_id);

CREATE INDEX IF NOT EXISTS idx_version_approvals_reviewer
ON version_approvals(reviewer_id);

CREATE INDEX IF NOT EXISTS idx_version_approvals_status
ON version_approvals(status);

CREATE INDEX IF NOT EXISTS idx_version_approvals_pending
ON version_approvals(reviewer_id, status)
WHERE status = 'pending';

-- Content Locks indexes
CREATE INDEX IF NOT EXISTS idx_content_locks_entity
ON content_locks(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_content_locks_active
ON content_locks(entity_type, entity_id, is_active)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_content_locks_holder
ON content_locks(locked_by, is_active)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_content_locks_expires
ON content_locks(expires_at)
WHERE is_active = TRUE AND expires_at IS NOT NULL;

-- Version Merges indexes
CREATE INDEX IF NOT EXISTS idx_version_merges_entity
ON version_merges(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_version_merges_source
ON version_merges(source_branch_id);

CREATE INDEX IF NOT EXISTS idx_version_merges_target
ON version_merges(target_branch_id);

CREATE INDEX IF NOT EXISTS idx_version_merges_pending
ON version_merges(is_complete)
WHERE is_complete = FALSE;

-- =============================================================================
-- Triggers
-- =============================================================================

-- Auto-update updated_at for content_versions
CREATE OR REPLACE FUNCTION update_content_versions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_content_versions_updated_at ON content_versions;
CREATE TRIGGER trigger_content_versions_updated_at
    BEFORE UPDATE ON content_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_content_versions_updated_at();

-- Auto-update updated_at for version_branches
DROP TRIGGER IF EXISTS trigger_version_branches_updated_at ON version_branches;
CREATE TRIGGER trigger_version_branches_updated_at
    BEFORE UPDATE ON version_branches
    FOR EACH ROW
    EXECUTE FUNCTION update_content_versions_updated_at();

-- =============================================================================
-- Functions
-- =============================================================================

-- Function to get the current published version for an entity
CREATE OR REPLACE FUNCTION get_current_version(
    p_entity_type content_entity_type,
    p_entity_id UUID
) RETURNS UUID AS $$
DECLARE
    v_version_id UUID;
BEGIN
    SELECT id INTO v_version_id
    FROM content_versions
    WHERE entity_type = p_entity_type
      AND entity_id = p_entity_id
      AND is_current = TRUE
      AND status = 'published'
    LIMIT 1;

    RETURN v_version_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get version history count
CREATE OR REPLACE FUNCTION get_version_count(
    p_entity_type content_entity_type,
    p_entity_id UUID
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM content_versions
    WHERE entity_type = p_entity_type
      AND entity_id = p_entity_id;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Function to check if entity is locked
CREATE OR REPLACE FUNCTION is_entity_locked(
    p_entity_type content_entity_type,
    p_entity_id UUID,
    p_user_id UUID DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_lock_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM content_locks
        WHERE entity_type = p_entity_type
          AND entity_id = p_entity_id
          AND is_active = TRUE
          AND (expires_at IS NULL OR expires_at > NOW())
          AND (p_user_id IS NULL OR locked_by != p_user_id)
    ) INTO v_lock_exists;

    RETURN v_lock_exists;
END;
$$ LANGUAGE plpgsql;

-- Function to supersede old current version when publishing new one
CREATE OR REPLACE FUNCTION supersede_current_version()
RETURNS TRIGGER AS $$
BEGIN
    -- If this version is being marked as current
    IF NEW.is_current = TRUE AND NEW.status = 'published' THEN
        -- Supersede the old current version
        UPDATE content_versions
        SET is_current = FALSE,
            status = 'superseded',
            updated_at = NOW()
        WHERE entity_type = NEW.entity_type
          AND entity_id = NEW.entity_id
          AND is_current = TRUE
          AND id != NEW.id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_supersede_current_version ON content_versions;
CREATE TRIGGER trigger_supersede_current_version
    BEFORE UPDATE ON content_versions
    FOR EACH ROW
    WHEN (NEW.is_current = TRUE AND NEW.status = 'published')
    EXECUTE FUNCTION supersede_current_version();

-- Function to update is_latest flags
CREATE OR REPLACE FUNCTION update_latest_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark all other versions in the same branch as not latest
    UPDATE content_versions
    SET is_latest = FALSE,
        updated_at = NOW()
    WHERE entity_type = NEW.entity_type
      AND entity_id = NEW.entity_id
      AND branch_name = NEW.branch_name
      AND id != NEW.id
      AND is_latest = TRUE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_latest_version ON content_versions;
CREATE TRIGGER trigger_update_latest_version
    AFTER INSERT ON content_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_latest_version();

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE content_versions IS 'Stores version snapshots of all content entities with full history';
COMMENT ON TABLE version_branches IS 'Manages parallel development branches for content';
COMMENT ON TABLE version_diffs IS 'Records differences between content versions';
COMMENT ON TABLE version_approvals IS 'Tracks approval workflow decisions';
COMMENT ON TABLE content_locks IS 'Manages editing locks to prevent conflicts';
COMMENT ON TABLE version_merges IS 'Records branch merge operations';

COMMENT ON COLUMN content_versions.content_hash IS 'SHA-256 hash of content_data for integrity verification';
COMMENT ON COLUMN content_versions.is_current IS 'True if this is the currently published version';
COMMENT ON COLUMN content_versions.is_latest IS 'True if this is the latest version in its branch';
COMMENT ON COLUMN version_branches.is_protected IS 'Protected branches require approval for changes';
COMMENT ON COLUMN content_locks.last_heartbeat IS 'Updated periodically to indicate active editing';
