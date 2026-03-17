-- Bug Tracking System Migration
-- Version: 1.0.0
-- Date: 2025-12-12
--
-- BUSINESS CONTEXT:
-- Implements automated bug tracking with Claude AI analysis integration.
-- Supports the workflow: Submit Bug -> Claude Analysis -> Auto-Fix -> PR -> Email Notification
--
-- SECURITY CONTEXT:
-- - submitter_email is required for notification delivery
-- - submitter_user_id links to authenticated users (optional for guest submissions)
-- - GDPR compliance: Bug reports may contain personal data, subject to retention policies

-- Bug Reports Table
-- Stores user-submitted bug reports with full context for AI analysis
CREATE TABLE IF NOT EXISTS bug_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Bug identification and description
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    steps_to_reproduce TEXT,
    expected_behavior TEXT,
    actual_behavior TEXT,

    -- Classification
    severity VARCHAR(50) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(50) DEFAULT 'submitted' CHECK (status IN (
        'submitted',           -- Initial submission
        'analyzing',           -- Claude is analyzing
        'analysis_complete',   -- Analysis done, awaiting fix
        'analysis_failed',     -- Analysis encountered error
        'fixing',              -- Generating fix
        'fix_ready',           -- Fix generated, awaiting PR
        'pr_opened',           -- PR created
        'resolved',            -- Bug fixed and verified
        'closed',              -- Closed without fix
        'wont_fix'             -- Determined not to fix
    )),

    -- Submitter information
    submitter_email VARCHAR(255) NOT NULL,
    submitter_user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Technical context
    affected_component VARCHAR(255),
    browser_info TEXT,
    error_logs TEXT,
    screenshot_urls JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for common queries
    CONSTRAINT bug_reports_title_length CHECK (char_length(title) >= 10),
    CONSTRAINT bug_reports_description_length CHECK (char_length(description) >= 20)
);

-- Bug Analysis Results Table
-- Stores Claude's analysis of bug reports
CREATE TABLE IF NOT EXISTS bug_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bug_report_id UUID NOT NULL REFERENCES bug_reports(id) ON DELETE CASCADE,

    -- Analysis content
    root_cause_analysis TEXT NOT NULL,
    suggested_fix TEXT NOT NULL,
    affected_files JSONB DEFAULT '[]'::jsonb,

    -- Analysis metadata
    confidence_score DECIMAL(5,2) CHECK (confidence_score >= 0 AND confidence_score <= 100),
    complexity_estimate VARCHAR(50) CHECK (complexity_estimate IN ('trivial', 'simple', 'moderate', 'complex', 'major')),

    -- Claude API usage tracking
    claude_model_used VARCHAR(100) NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    analysis_duration_ms INTEGER,

    -- Timestamps
    analysis_started_at TIMESTAMP WITH TIME ZONE,
    analysis_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- One analysis per bug (can be retried, new record created)
    UNIQUE(bug_report_id, created_at)
);

-- Bug Fix Attempts Table
-- Tracks automated fix generation and PR creation
CREATE TABLE IF NOT EXISTS bug_fix_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bug_report_id UUID NOT NULL REFERENCES bug_reports(id) ON DELETE CASCADE,
    analysis_id UUID NOT NULL REFERENCES bug_analysis_results(id) ON DELETE CASCADE,

    -- Git/PR information
    branch_name VARCHAR(255),
    pr_number INTEGER,
    pr_url VARCHAR(500),
    commit_sha VARCHAR(40),

    -- Fix details
    files_changed JSONB DEFAULT '[]'::jsonb,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending',             -- Awaiting processing
        'generating',          -- Claude generating fix
        'testing',             -- Running tests
        'tests_failed',        -- Tests did not pass
        'creating_pr',         -- Creating pull request
        'pr_created',          -- PR successfully created
        'pr_merged',           -- PR was merged
        'pr_closed',           -- PR was closed without merge
        'failed'               -- Fix generation failed
    )),
    error_message TEXT,

    -- Test results
    tests_run INTEGER DEFAULT 0,
    tests_passed INTEGER DEFAULT 0,
    tests_failed INTEGER DEFAULT 0,
    test_output TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Claude API usage for fix generation
    fix_tokens_used INTEGER DEFAULT 0
);

-- Bug Tracking Jobs Table
-- Manages async job processing for bug analysis
CREATE TABLE IF NOT EXISTS bug_tracking_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bug_report_id UUID NOT NULL REFERENCES bug_reports(id) ON DELETE CASCADE,

    -- Job type and status
    job_type VARCHAR(50) NOT NULL CHECK (job_type IN ('analyze', 'fix', 'notify')),
    status VARCHAR(50) DEFAULT 'queued' CHECK (status IN (
        'queued',
        'processing',
        'completed',
        'failed',
        'cancelled'
    )),

    -- Processing details
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,

    -- Timestamps
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Worker assignment
    worker_id VARCHAR(100)
);

-- Email Notifications Table
-- Tracks bug-related email notifications
CREATE TABLE IF NOT EXISTS bug_email_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bug_report_id UUID NOT NULL REFERENCES bug_reports(id) ON DELETE CASCADE,

    -- Email details
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    template_name VARCHAR(100) NOT NULL,

    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending',
        'sent',
        'failed',
        'bounced'
    )),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bug_reports_status ON bug_reports(status);
CREATE INDEX IF NOT EXISTS idx_bug_reports_severity ON bug_reports(severity);
CREATE INDEX IF NOT EXISTS idx_bug_reports_submitter_email ON bug_reports(submitter_email);
CREATE INDEX IF NOT EXISTS idx_bug_reports_submitter_user_id ON bug_reports(submitter_user_id);
CREATE INDEX IF NOT EXISTS idx_bug_reports_created_at ON bug_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bug_reports_affected_component ON bug_reports(affected_component);

CREATE INDEX IF NOT EXISTS idx_bug_analysis_results_bug_report_id ON bug_analysis_results(bug_report_id);
CREATE INDEX IF NOT EXISTS idx_bug_analysis_results_confidence ON bug_analysis_results(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_bug_fix_attempts_bug_report_id ON bug_fix_attempts(bug_report_id);
CREATE INDEX IF NOT EXISTS idx_bug_fix_attempts_status ON bug_fix_attempts(status);
CREATE INDEX IF NOT EXISTS idx_bug_fix_attempts_pr_number ON bug_fix_attempts(pr_number);

CREATE INDEX IF NOT EXISTS idx_bug_tracking_jobs_status ON bug_tracking_jobs(status);
CREATE INDEX IF NOT EXISTS idx_bug_tracking_jobs_job_type ON bug_tracking_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_bug_tracking_jobs_priority ON bug_tracking_jobs(priority DESC, queued_at ASC);

CREATE INDEX IF NOT EXISTS idx_bug_email_notifications_bug_report_id ON bug_email_notifications(bug_report_id);
CREATE INDEX IF NOT EXISTS idx_bug_email_notifications_status ON bug_email_notifications(status);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_bug_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_bug_reports_updated_at ON bug_reports;
CREATE TRIGGER trigger_bug_reports_updated_at
    BEFORE UPDATE ON bug_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_bug_reports_updated_at();

-- Comments for documentation
COMMENT ON TABLE bug_reports IS 'User-submitted bug reports for automated analysis and fixing';
COMMENT ON TABLE bug_analysis_results IS 'Claude AI analysis results for bug reports';
COMMENT ON TABLE bug_fix_attempts IS 'Automated fix generation attempts and PR tracking';
COMMENT ON TABLE bug_tracking_jobs IS 'Async job queue for bug processing';
COMMENT ON TABLE bug_email_notifications IS 'Email notification tracking for bug updates';

COMMENT ON COLUMN bug_reports.severity IS 'Bug severity: low, medium, high, critical';
COMMENT ON COLUMN bug_reports.status IS 'Current bug processing status';
COMMENT ON COLUMN bug_analysis_results.confidence_score IS 'Claude confidence in analysis (0-100)';
COMMENT ON COLUMN bug_fix_attempts.status IS 'Fix generation and PR status';
