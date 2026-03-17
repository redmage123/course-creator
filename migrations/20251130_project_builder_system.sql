-- Migration: AI-Powered Project Builder System
-- Purpose: Enable bulk project creation through AI conversation
-- Author: Course Creator Platform
-- Date: 2025-11-30
--
-- BUSINESS CONTEXT:
-- This migration creates the database schema for the AI-powered project builder feature.
-- The project builder enables organization administrators to create complete training
-- program structures through natural language conversation with an AI assistant.
--
-- WHAT THIS MIGRATION CREATES:
-- 1. project_builder_sessions - Track AI conversation state and collected data
-- 2. bulk_import_jobs - Track roster file import operations
-- 3. bulk_import_entries - Individual parsed entries from roster files
-- 4. schedule_proposals - Store generated schedule proposals for review
-- 5. schedule_proposal_entries - Individual entries in a schedule proposal
-- 6. schedule_proposal_conflicts - Conflicts detected in schedule proposals
-- 7. bulk_creation_jobs - Track bulk project creation operations
-- 8. bulk_creation_items - Individual items created in a bulk operation
--
-- WHY THIS ARCHITECTURE:
-- - Sessions enable multi-turn conversations with state persistence
-- - Import jobs support async processing of large roster files
-- - Schedule proposals allow human review before committing changes
-- - Creation jobs provide audit trail and enable rollback if needed

-- =============================================================================
-- SET SEARCH PATH
-- =============================================================================

-- Ensure we're working in the course_creator schema
SET search_path TO course_creator, public;

-- =============================================================================
-- ENUMERATIONS
-- =============================================================================

-- Project builder session states (matches domain enum)
DO $$ BEGIN
    CREATE TYPE project_builder_state AS ENUM (
        'initial',              -- Waiting for project description
        'collecting_details',   -- Gathering additional information
        'awaiting_rosters',     -- Waiting for file uploads
        'parsing_rosters',      -- Processing uploaded files
        'schedule_review',      -- Presenting schedule for approval
        'content_config',       -- Configuring content generation
        'zoom_config',          -- Configuring Zoom rooms
        'preview',              -- Showing creation preview
        'creating',             -- Executing creation
        'complete',             -- Creation finished
        'error'                 -- Error state
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Import job status
DO $$ BEGIN
    CREATE TYPE import_job_status AS ENUM (
        'pending',      -- Job created, not started
        'processing',   -- Currently processing
        'completed',    -- Successfully completed
        'failed',       -- Processing failed
        'partial'       -- Completed with some errors
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Conflict types for scheduling
DO $$ BEGIN
    CREATE TYPE schedule_conflict_type AS ENUM (
        'instructor_double_booking',
        'room_conflict',
        'capacity_exceeded',
        'date_conflict',
        'instructor_unavailable'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Bulk creation job status
DO $$ BEGIN
    CREATE TYPE bulk_creation_status AS ENUM (
        'pending',
        'in_progress',
        'completed',
        'failed',
        'rolled_back'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Bulk creation item types
DO $$ BEGIN
    CREATE TYPE bulk_creation_item_type AS ENUM (
        'project',
        'subproject',
        'track',
        'course',
        'instructor_user',
        'student_user',
        'enrollment',
        'schedule_entry',
        'zoom_room'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- PROJECT BUILDER SESSIONS
-- =============================================================================

CREATE TABLE IF NOT EXISTS project_builder_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Organization context
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Session state
    state project_builder_state NOT NULL DEFAULT 'initial',

    -- Collected specification data (JSONB for flexibility during conversation)
    specification_data JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Attached file references
    attached_files JSONB DEFAULT '[]'::jsonb,

    -- AI conversation context
    conversation_history JSONB DEFAULT '[]'::jsonb,

    -- Current step for multi-step operations
    current_step VARCHAR(100),
    current_step_data JSONB DEFAULT '{}'::jsonb,

    -- Error tracking
    last_error TEXT,
    error_context JSONB,

    -- Linked entities (populated during/after creation)
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    schedule_proposal_id UUID,
    creation_job_id UUID,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for project builder sessions
CREATE INDEX idx_pb_sessions_org ON project_builder_sessions(organization_id);
CREATE INDEX idx_pb_sessions_user ON project_builder_sessions(created_by);
CREATE INDEX idx_pb_sessions_state ON project_builder_sessions(state);
CREATE INDEX idx_pb_sessions_active ON project_builder_sessions(organization_id, created_by)
    WHERE state NOT IN ('complete', 'error');
CREATE INDEX idx_pb_sessions_expires ON project_builder_sessions(expires_at)
    WHERE state NOT IN ('complete', 'error');

COMMENT ON TABLE project_builder_sessions IS 'AI conversation sessions for bulk project creation';
COMMENT ON COLUMN project_builder_sessions.specification_data IS 'Incrementally collected project specification as JSONB';
COMMENT ON COLUMN project_builder_sessions.conversation_history IS 'AI conversation messages for context continuation';
COMMENT ON COLUMN project_builder_sessions.expires_at IS 'Session expiration for cleanup of abandoned sessions';

-- =============================================================================
-- BULK IMPORT JOBS (Roster File Processing)
-- =============================================================================

CREATE TABLE IF NOT EXISTS bulk_import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session reference
    session_id UUID REFERENCES project_builder_sessions(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- File information
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- csv, xlsx, xls, json
    file_size_bytes INTEGER,
    file_path TEXT, -- Storage path for uploaded file

    -- Import type
    import_type VARCHAR(50) NOT NULL CHECK (import_type IN ('instructors', 'students', 'courses', 'mixed')),

    -- Processing status
    status import_job_status NOT NULL DEFAULT 'pending',

    -- Progress tracking
    total_rows INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    successful_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,

    -- Column mapping (user-specified column names to standard fields)
    column_mapping JSONB DEFAULT '{}'::jsonb,

    -- Validation results
    validation_errors JSONB DEFAULT '[]'::jsonb,

    -- Parsed data summary
    parsed_summary JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Error details
    error_message TEXT,
    error_details JSONB,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for bulk import jobs
CREATE INDEX idx_import_jobs_session ON bulk_import_jobs(session_id);
CREATE INDEX idx_import_jobs_org ON bulk_import_jobs(organization_id);
CREATE INDEX idx_import_jobs_status ON bulk_import_jobs(status);
CREATE INDEX idx_import_jobs_type ON bulk_import_jobs(import_type);

COMMENT ON TABLE bulk_import_jobs IS 'Tracks roster file import operations';
COMMENT ON COLUMN bulk_import_jobs.column_mapping IS 'Maps file columns to standard fields (e.g., {"Full Name": "name", "Email Address": "email"})';

-- =============================================================================
-- BULK IMPORT ENTRIES (Parsed Roster Data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS bulk_import_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Job reference
    import_job_id UUID NOT NULL REFERENCES bulk_import_jobs(id) ON DELETE CASCADE,

    -- Entry details
    row_number INTEGER NOT NULL,
    entry_type VARCHAR(50) NOT NULL CHECK (entry_type IN ('instructor', 'student', 'course')),

    -- Raw and parsed data
    raw_data JSONB NOT NULL,
    parsed_data JSONB NOT NULL,

    -- Validation status
    is_valid BOOLEAN DEFAULT TRUE,
    validation_errors JSONB DEFAULT '[]'::jsonb,

    -- Processing status
    is_processed BOOLEAN DEFAULT FALSE,
    created_entity_id UUID, -- ID of entity created from this entry

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for bulk import entries
CREATE INDEX idx_import_entries_job ON bulk_import_entries(import_job_id);
CREATE INDEX idx_import_entries_type ON bulk_import_entries(entry_type);
CREATE INDEX idx_import_entries_valid ON bulk_import_entries(import_job_id, is_valid);
CREATE INDEX idx_import_entries_processed ON bulk_import_entries(import_job_id, is_processed);

COMMENT ON TABLE bulk_import_entries IS 'Individual entries parsed from roster files';
COMMENT ON COLUMN bulk_import_entries.raw_data IS 'Original row data from file';
COMMENT ON COLUMN bulk_import_entries.parsed_data IS 'Data after column mapping and transformation';

-- =============================================================================
-- SCHEDULE PROPOSALS
-- =============================================================================

CREATE TABLE IF NOT EXISTS schedule_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session reference
    session_id UUID REFERENCES project_builder_sessions(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Specification reference (snapshot of spec when proposal was generated)
    spec_snapshot JSONB NOT NULL,

    -- Schedule configuration
    schedule_config JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Generation strategy used
    generation_strategy VARCHAR(50) DEFAULT 'balanced',

    -- Summary statistics
    total_entries INTEGER DEFAULT 0,
    total_hours DECIMAL(10,2) DEFAULT 0,
    start_date DATE,
    end_date DATE,

    -- Validation status
    is_valid BOOLEAN DEFAULT TRUE,
    has_errors BOOLEAN DEFAULT FALSE,
    has_warnings BOOLEAN DEFAULT FALSE,

    -- Optimization suggestions
    suggestions JSONB DEFAULT '[]'::jsonb,
    warnings JSONB DEFAULT '[]'::jsonb,

    -- User approval
    is_approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approval_notes TEXT,

    -- If modified after generation
    is_modified BOOLEAN DEFAULT FALSE,
    modification_log JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for schedule proposals
CREATE INDEX idx_schedule_proposals_session ON schedule_proposals(session_id);
CREATE INDEX idx_schedule_proposals_org ON schedule_proposals(organization_id);
CREATE INDEX idx_schedule_proposals_approved ON schedule_proposals(is_approved);
CREATE INDEX idx_schedule_proposals_valid ON schedule_proposals(is_valid);

COMMENT ON TABLE schedule_proposals IS 'Generated schedule proposals for user review before creation';
COMMENT ON COLUMN schedule_proposals.spec_snapshot IS 'Snapshot of ProjectBuilderSpec when proposal was generated';
COMMENT ON COLUMN schedule_proposals.is_approved IS 'User must approve proposal before schedule creation';

-- =============================================================================
-- SCHEDULE PROPOSAL ENTRIES
-- =============================================================================

CREATE TABLE IF NOT EXISTS schedule_proposal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Proposal reference
    proposal_id UUID NOT NULL REFERENCES schedule_proposals(id) ON DELETE CASCADE,

    -- Entry details
    track_name VARCHAR(255) NOT NULL,
    course_title VARCHAR(255) NOT NULL,
    session_number INTEGER DEFAULT 1,

    -- Timing
    scheduled_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_hours DECIMAL(4,2) NOT NULL,

    -- Assignment
    instructor_email VARCHAR(255),
    instructor_name VARCHAR(255),

    -- Location
    location_name VARCHAR(255),
    room_name VARCHAR(100),
    zoom_link TEXT,

    -- Order within day
    sequence_order INTEGER DEFAULT 0,

    -- Status
    has_conflict BOOLEAN DEFAULT FALSE,
    conflict_ids UUID[] DEFAULT '{}',

    -- Created at
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for schedule proposal entries
CREATE INDEX idx_proposal_entries_proposal ON schedule_proposal_entries(proposal_id);
CREATE INDEX idx_proposal_entries_date ON schedule_proposal_entries(scheduled_date);
CREATE INDEX idx_proposal_entries_instructor ON schedule_proposal_entries(instructor_email);
CREATE INDEX idx_proposal_entries_track ON schedule_proposal_entries(track_name);
CREATE INDEX idx_proposal_entries_conflict ON schedule_proposal_entries(proposal_id, has_conflict)
    WHERE has_conflict = TRUE;

COMMENT ON TABLE schedule_proposal_entries IS 'Individual session entries in a schedule proposal';

-- =============================================================================
-- SCHEDULE PROPOSAL CONFLICTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS schedule_proposal_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Proposal reference
    proposal_id UUID NOT NULL REFERENCES schedule_proposals(id) ON DELETE CASCADE,

    -- Conflict details
    conflict_type schedule_conflict_type NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'error' CHECK (severity IN ('warning', 'error')),
    description TEXT NOT NULL,

    -- Affected entities
    affected_entry_ids UUID[] NOT NULL DEFAULT '{}',
    affected_date DATE,
    affected_instructor_email VARCHAR(255),
    affected_track_name VARCHAR(255),
    affected_room VARCHAR(100),

    -- Resolution
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_method VARCHAR(100),
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Suggestions
    suggestions JSONB DEFAULT '[]'::jsonb,

    -- Created at
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for schedule proposal conflicts
CREATE INDEX idx_proposal_conflicts_proposal ON schedule_proposal_conflicts(proposal_id);
CREATE INDEX idx_proposal_conflicts_type ON schedule_proposal_conflicts(conflict_type);
CREATE INDEX idx_proposal_conflicts_unresolved ON schedule_proposal_conflicts(proposal_id, is_resolved)
    WHERE is_resolved = FALSE;
CREATE INDEX idx_proposal_conflicts_instructor ON schedule_proposal_conflicts(affected_instructor_email)
    WHERE affected_instructor_email IS NOT NULL;

COMMENT ON TABLE schedule_proposal_conflicts IS 'Scheduling conflicts detected in a proposal';

-- =============================================================================
-- BULK CREATION JOBS
-- =============================================================================

CREATE TABLE IF NOT EXISTS bulk_creation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session reference
    session_id UUID REFERENCES project_builder_sessions(id) ON DELETE SET NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Job configuration
    spec_snapshot JSONB NOT NULL,
    schedule_proposal_id UUID REFERENCES schedule_proposals(id) ON DELETE SET NULL,

    -- Options
    dry_run BOOLEAN DEFAULT FALSE,
    generate_content BOOLEAN DEFAULT FALSE,
    create_zoom_rooms BOOLEAN DEFAULT FALSE,

    -- Status
    status bulk_creation_status NOT NULL DEFAULT 'pending',
    current_phase VARCHAR(50),

    -- Progress tracking
    total_items INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,

    -- Results
    result_summary JSONB DEFAULT '{}'::jsonb,

    -- Created entity references
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    created_subproject_ids UUID[] DEFAULT '{}',
    created_track_ids UUID[] DEFAULT '{}',
    created_course_ids UUID[] DEFAULT '{}',
    created_user_ids UUID[] DEFAULT '{}',
    created_enrollment_ids UUID[] DEFAULT '{}',
    created_schedule_ids UUID[] DEFAULT '{}',

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(10,3),

    -- Error handling
    errors JSONB DEFAULT '[]'::jsonb,
    warnings JSONB DEFAULT '[]'::jsonb,

    -- Rollback support
    can_rollback BOOLEAN DEFAULT TRUE,
    rollback_data JSONB,
    rolled_back_at TIMESTAMP WITH TIME ZONE,
    rolled_back_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for bulk creation jobs
CREATE INDEX idx_creation_jobs_session ON bulk_creation_jobs(session_id);
CREATE INDEX idx_creation_jobs_org ON bulk_creation_jobs(organization_id);
CREATE INDEX idx_creation_jobs_status ON bulk_creation_jobs(status);
CREATE INDEX idx_creation_jobs_project ON bulk_creation_jobs(project_id);
CREATE INDEX idx_creation_jobs_recent ON bulk_creation_jobs(organization_id, created_at DESC);

COMMENT ON TABLE bulk_creation_jobs IS 'Tracks bulk project creation operations with rollback support';
COMMENT ON COLUMN bulk_creation_jobs.spec_snapshot IS 'Full specification snapshot for audit and rollback';
COMMENT ON COLUMN bulk_creation_jobs.rollback_data IS 'Data needed to rollback all created entities';

-- =============================================================================
-- BULK CREATION ITEMS (Audit Trail)
-- =============================================================================

CREATE TABLE IF NOT EXISTS bulk_creation_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Job reference
    creation_job_id UUID NOT NULL REFERENCES bulk_creation_jobs(id) ON DELETE CASCADE,

    -- Item details
    item_type bulk_creation_item_type NOT NULL,
    item_order INTEGER NOT NULL, -- Order of creation

    -- Source data
    source_data JSONB NOT NULL,

    -- Created entity
    created_entity_id UUID,
    created_entity_data JSONB,

    -- Status
    is_successful BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    error_details JSONB,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Rollback status
    is_rolled_back BOOLEAN DEFAULT FALSE,
    rolled_back_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for bulk creation items
CREATE INDEX idx_creation_items_job ON bulk_creation_items(creation_job_id);
CREATE INDEX idx_creation_items_type ON bulk_creation_items(item_type);
CREATE INDEX idx_creation_items_entity ON bulk_creation_items(created_entity_id)
    WHERE created_entity_id IS NOT NULL;
CREATE INDEX idx_creation_items_failed ON bulk_creation_items(creation_job_id, is_successful)
    WHERE is_successful = FALSE;

COMMENT ON TABLE bulk_creation_items IS 'Individual items created in a bulk operation for audit and rollback';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamps trigger function (if not already exists)
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp triggers
CREATE TRIGGER trigger_pb_sessions_timestamp
    BEFORE UPDATE ON project_builder_sessions
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_schedule_proposals_timestamp
    BEFORE UPDATE ON schedule_proposals
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_creation_jobs_timestamp
    BEFORE UPDATE ON bulk_creation_jobs
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- =============================================================================
-- FOREIGN KEY TO LINK SESSIONS TO PROPOSALS
-- =============================================================================

-- Add foreign key now that schedule_proposals exists
ALTER TABLE project_builder_sessions
    ADD CONSTRAINT fk_pb_sessions_schedule_proposal
    FOREIGN KEY (schedule_proposal_id) REFERENCES schedule_proposals(id) ON DELETE SET NULL;

ALTER TABLE project_builder_sessions
    ADD CONSTRAINT fk_pb_sessions_creation_job
    FOREIGN KEY (creation_job_id) REFERENCES bulk_creation_jobs(id) ON DELETE SET NULL;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active sessions view
CREATE OR REPLACE VIEW active_project_builder_sessions AS
SELECT
    pbs.id,
    pbs.organization_id,
    o.name AS organization_name,
    pbs.created_by,
    u.full_name AS creator_name,
    u.email AS creator_email,
    pbs.state,
    pbs.specification_data->>'name' AS project_name,
    COALESCE(jsonb_array_length(pbs.specification_data->'tracks'), 0) AS track_count,
    COALESCE(jsonb_array_length(pbs.specification_data->'instructors'), 0) AS instructor_count,
    COALESCE(jsonb_array_length(pbs.specification_data->'students'), 0) AS student_count,
    pbs.created_at,
    pbs.updated_at,
    pbs.expires_at,
    CASE
        WHEN pbs.expires_at < CURRENT_TIMESTAMP THEN 'expired'
        WHEN pbs.state = 'complete' THEN 'completed'
        WHEN pbs.state = 'error' THEN 'failed'
        ELSE 'active'
    END AS session_status
FROM project_builder_sessions pbs
JOIN organizations o ON pbs.organization_id = o.id
JOIN users u ON pbs.created_by = u.id
WHERE pbs.state NOT IN ('complete', 'error')
  AND pbs.expires_at > CURRENT_TIMESTAMP;

COMMENT ON VIEW active_project_builder_sessions IS 'Active project builder sessions with summary information';

-- Creation jobs summary view
CREATE OR REPLACE VIEW bulk_creation_jobs_summary AS
SELECT
    bcj.id,
    bcj.organization_id,
    o.name AS organization_name,
    bcj.created_by,
    u.full_name AS creator_name,
    bcj.status,
    bcj.dry_run,
    bcj.spec_snapshot->>'name' AS project_name,
    bcj.project_id,
    bcj.total_items,
    bcj.completed_items,
    bcj.failed_items,
    CASE
        WHEN bcj.total_items > 0 THEN
            ROUND((bcj.completed_items::DECIMAL / bcj.total_items) * 100, 2)
        ELSE 0
    END AS progress_percentage,
    bcj.duration_seconds,
    bcj.started_at,
    bcj.completed_at,
    bcj.created_at,
    bcj.can_rollback,
    bcj.rolled_back_at IS NOT NULL AS is_rolled_back
FROM bulk_creation_jobs bcj
JOIN organizations o ON bcj.organization_id = o.id
JOIN users u ON bcj.created_by = u.id;

COMMENT ON VIEW bulk_creation_jobs_summary IS 'Summary view of bulk creation jobs with progress';

-- =============================================================================
-- CLEANUP FUNCTION
-- =============================================================================

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_project_builder_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired sessions that are not in complete/error state
    DELETE FROM project_builder_sessions
    WHERE expires_at < CURRENT_TIMESTAMP
      AND state NOT IN ('complete', 'error');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_project_builder_sessions IS 'Cleans up expired project builder sessions';

-- =============================================================================
-- DOCUMENTATION
-- =============================================================================

COMMENT ON TYPE project_builder_state IS 'State machine states for project builder conversation flow';
COMMENT ON TYPE import_job_status IS 'Status tracking for bulk import jobs';
COMMENT ON TYPE schedule_conflict_type IS 'Types of scheduling conflicts that can be detected';
COMMENT ON TYPE bulk_creation_status IS 'Status tracking for bulk creation jobs';
COMMENT ON TYPE bulk_creation_item_type IS 'Types of items that can be bulk created';

-- =============================================================================
-- ROLLBACK SECTION (commented out - uncomment to rollback)
-- =============================================================================

/*
-- To rollback this migration:

DROP VIEW IF EXISTS bulk_creation_jobs_summary;
DROP VIEW IF EXISTS active_project_builder_sessions;

DROP FUNCTION IF EXISTS cleanup_expired_project_builder_sessions;

DROP TRIGGER IF EXISTS trigger_creation_jobs_timestamp ON bulk_creation_jobs;
DROP TRIGGER IF EXISTS trigger_schedule_proposals_timestamp ON schedule_proposals;
DROP TRIGGER IF EXISTS trigger_pb_sessions_timestamp ON project_builder_sessions;

DROP TABLE IF EXISTS bulk_creation_items;
DROP TABLE IF EXISTS bulk_creation_jobs;
DROP TABLE IF EXISTS schedule_proposal_conflicts;
DROP TABLE IF EXISTS schedule_proposal_entries;
DROP TABLE IF EXISTS schedule_proposals;
DROP TABLE IF EXISTS bulk_import_entries;
DROP TABLE IF EXISTS bulk_import_jobs;
DROP TABLE IF EXISTS project_builder_sessions;

DROP TYPE IF EXISTS bulk_creation_item_type;
DROP TYPE IF EXISTS bulk_creation_status;
DROP TYPE IF EXISTS schedule_conflict_type;
DROP TYPE IF EXISTS import_job_status;
DROP TYPE IF EXISTS project_builder_state;
*/
