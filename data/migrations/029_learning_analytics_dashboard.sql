-- Migration: 029_learning_analytics_dashboard.sql
-- Enhancement 9: Learning Analytics Dashboard
--
-- What: Creates tables for customizable analytics dashboards with widgets,
--       scheduled reports, cohort analytics, and learning path tracking.
--
-- Where: Extends the existing analytics module with dashboard-specific features
--        that enable personalized data visualization and automated reporting.
--
-- Why: The existing analytics service provides raw data and calculations.
--      This enhancement adds:
--      1. User-customizable dashboard layouts with draggable widgets
--      2. Scheduled report generation with email/export delivery
--      3. Cohort-based analytics for comparing student groups
--      4. Learning path progress visualization
--      5. Real-time notification thresholds for at-risk students
--
-- Created: 2025-01-15
-- Author: Course Creator Platform

-- ============================================================================
-- DASHBOARD CONFIGURATION TABLES
-- ============================================================================

-- Dashboard Templates: Pre-defined dashboard layouts by role
CREATE TABLE IF NOT EXISTS dashboard_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- What: Target role for this dashboard template
    -- Where: Used to provide role-appropriate default dashboards
    -- Why: Different roles need different analytics views (instructor vs student)
    target_role VARCHAR(50) NOT NULL CHECK (target_role IN ('site_admin', 'org_admin', 'instructor', 'student')),

    -- What: JSON configuration for widget layout
    -- Where: Stores grid positions, sizes, and widget references
    -- Why: Enables drag-and-drop dashboard customization
    layout_config JSONB NOT NULL DEFAULT '{"columns": 12, "rows": [], "widgets": []}',

    -- What: Whether this is the default template for the role
    -- Where: Applied when user first accesses dashboard
    -- Why: Provides sensible defaults without requiring configuration
    is_default BOOLEAN DEFAULT false,

    -- What: Template visibility scope
    -- Where: Controls who can use this template
    -- Why: Allows org-specific templates vs platform-wide templates
    scope VARCHAR(20) DEFAULT 'platform' CHECK (scope IN ('platform', 'organization', 'personal')),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_default_per_role_scope UNIQUE NULLS NOT DISTINCT (target_role, scope, organization_id, is_default)
        DEFERRABLE INITIALLY DEFERRED
);

-- User Dashboards: Individual user's dashboard configurations
CREATE TABLE IF NOT EXISTS user_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- What: Dashboard name for multiple dashboard support
    -- Where: Users can create multiple named dashboards
    -- Why: Different contexts need different views (daily vs weekly analysis)
    name VARCHAR(100) NOT NULL DEFAULT 'My Dashboard',

    -- What: Base template this dashboard was created from
    -- Where: Links to pre-defined template
    -- Why: Enables "reset to default" functionality
    template_id UUID REFERENCES dashboard_templates(id) ON DELETE SET NULL,

    -- What: Customized layout configuration
    -- Where: Overrides template layout with user modifications
    -- Why: Users can customize widget positions and sizes
    layout_config JSONB NOT NULL DEFAULT '{"columns": 12, "rows": [], "widgets": []}',

    -- What: User preference settings
    -- Where: Stores refresh interval, theme, date range preferences
    -- Why: Personalizes dashboard behavior
    preferences JSONB DEFAULT '{"refreshInterval": 300, "dateRange": "30d", "theme": "auto"}',

    is_active BOOLEAN DEFAULT true,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_user_dashboard_name UNIQUE (user_id, name)
);

-- Dashboard Widgets: Available widget types and configurations
CREATE TABLE IF NOT EXISTS dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What: Widget type identifier
    -- Where: Maps to frontend component
    -- Why: Determines rendering logic and data requirements
    widget_type VARCHAR(50) NOT NULL CHECK (widget_type IN (
        'kpi_card',           -- Single metric display
        'line_chart',         -- Time series visualization
        'bar_chart',          -- Comparison visualization
        'pie_chart',          -- Distribution visualization
        'heatmap',            -- Activity heatmap
        'table',              -- Data table
        'progress_ring',      -- Circular progress indicator
        'leaderboard',        -- Ranked list
        'activity_feed',      -- Recent activity stream
        'risk_indicator',     -- At-risk student alerts
        'cohort_comparison',  -- Group comparison
        'learning_path',      -- Path progress visualization
        'completion_funnel',  -- Funnel visualization
        'engagement_score',   -- Engagement metric
        'custom'              -- Custom widget
    )),

    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- What: Default widget dimensions
    -- Where: Used when adding widget to dashboard
    -- Why: Ensures reasonable initial sizing
    default_width INTEGER DEFAULT 4 CHECK (default_width BETWEEN 1 AND 12),
    default_height INTEGER DEFAULT 2 CHECK (default_height BETWEEN 1 AND 8),
    min_width INTEGER DEFAULT 2,
    min_height INTEGER DEFAULT 1,

    -- What: Data source configuration
    -- Where: Specifies API endpoint and parameters
    -- Why: Widgets need to know where to fetch data
    data_source JSONB NOT NULL,

    -- What: Widget-specific configuration schema
    -- Where: JSON Schema for validation
    -- Why: Ensures valid configuration when customizing
    config_schema JSONB DEFAULT '{}',

    -- What: Default configuration values
    -- Where: Applied when widget is first added
    -- Why: Provides sensible defaults
    default_config JSONB DEFAULT '{}',

    -- What: Roles that can use this widget
    -- Where: Controls widget visibility by role
    -- Why: Some widgets only make sense for certain roles
    allowed_roles VARCHAR(50)[] DEFAULT ARRAY['site_admin', 'org_admin', 'instructor', 'student'],

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Widget Instances: Specific widget configurations on dashboards
CREATE TABLE IF NOT EXISTS widget_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID NOT NULL REFERENCES user_dashboards(id) ON DELETE CASCADE,
    widget_id UUID NOT NULL REFERENCES dashboard_widgets(id) ON DELETE CASCADE,

    -- What: Grid position coordinates
    -- Where: Determines widget placement in layout
    -- Why: Enables drag-and-drop positioning
    grid_x INTEGER NOT NULL DEFAULT 0,
    grid_y INTEGER NOT NULL DEFAULT 0,
    grid_width INTEGER NOT NULL DEFAULT 4,
    grid_height INTEGER NOT NULL DEFAULT 2,

    -- What: Instance-specific configuration
    -- Where: Overrides widget defaults
    -- Why: Same widget type can show different data
    config JSONB DEFAULT '{}',

    -- What: Custom title override
    -- Where: Displayed in widget header
    -- Why: Users may want custom labels
    title_override VARCHAR(100),

    is_visible BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SCHEDULED REPORTS TABLES
-- ============================================================================

-- Report Templates: Reusable report configurations
CREATE TABLE IF NOT EXISTS report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- What: Report type classification
    -- Where: Determines report generation logic
    -- Why: Different reports need different data aggregation
    report_type VARCHAR(50) NOT NULL CHECK (report_type IN (
        'student_progress',      -- Individual student progress
        'course_analytics',      -- Course-level metrics
        'cohort_comparison',     -- Group comparison
        'engagement_summary',    -- Engagement metrics
        'completion_report',     -- Completion rates
        'assessment_analysis',   -- Quiz/assessment results
        'instructor_summary',    -- Instructor performance
        'organization_overview', -- Org-wide metrics
        'custom'                 -- Custom report
    )),

    -- What: Report configuration
    -- Where: Specifies metrics, filters, groupings
    -- Why: Defines what data appears in report
    config JSONB NOT NULL DEFAULT '{}',

    -- What: Output format options
    -- Where: Determines file generation
    -- Why: Users may need PDF, Excel, or CSV
    output_formats VARCHAR(10)[] DEFAULT ARRAY['pdf', 'csv'],

    -- What: Scope of report availability
    -- Where: Controls who can use this template
    -- Why: Allows org-specific vs platform-wide templates
    scope VARCHAR(20) DEFAULT 'platform' CHECK (scope IN ('platform', 'organization', 'personal')),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled Reports: User-configured report schedules
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES report_templates(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,

    -- What: Schedule configuration
    -- Where: Determines when reports run
    -- Why: Enables daily, weekly, monthly automation
    schedule_type VARCHAR(20) NOT NULL CHECK (schedule_type IN (
        'once',      -- One-time report
        'daily',     -- Every day
        'weekly',    -- Every week
        'biweekly',  -- Every two weeks
        'monthly',   -- Every month
        'quarterly'  -- Every quarter
    )),

    -- What: Cron-like schedule expression
    -- Where: Precise timing control
    -- Why: Allows "every Monday at 9am" type schedules
    schedule_cron VARCHAR(100),

    -- What: Day of week/month for scheduling
    -- Where: Used with weekly/monthly schedules
    -- Why: "Every Monday" or "1st of month"
    schedule_day INTEGER CHECK (schedule_day BETWEEN 0 AND 31),
    schedule_time TIME DEFAULT '09:00:00',
    schedule_timezone VARCHAR(50) DEFAULT 'UTC',

    -- What: Report-specific configuration overrides
    -- Where: Customizes template settings
    -- Why: Same template, different filters per schedule
    config_overrides JSONB DEFAULT '{}',

    -- What: Output format for this schedule
    -- Where: Determines generated file type
    -- Why: Different schedules may need different formats
    output_format VARCHAR(10) DEFAULT 'pdf',

    -- What: Delivery configuration
    -- Where: How/where to send the report
    -- Why: Email, download, or external integration
    delivery_method VARCHAR(20) DEFAULT 'email' CHECK (delivery_method IN ('email', 'download', 'webhook', 'storage')),
    delivery_config JSONB DEFAULT '{}',

    -- What: Recipients list
    -- Where: Who receives the report
    -- Why: Reports can go to multiple people
    recipients JSONB DEFAULT '[]',

    is_active BOOLEAN DEFAULT true,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_run_status VARCHAR(20),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Report Executions: History of generated reports
CREATE TABLE IF NOT EXISTS report_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheduled_report_id UUID REFERENCES scheduled_reports(id) ON DELETE SET NULL,
    template_id UUID REFERENCES report_templates(id) ON DELETE SET NULL,

    -- What: User who triggered/owns the report
    -- Where: For tracking and access control
    -- Why: Users should only see their own reports
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- What: Execution status
    -- Where: Tracks report generation progress
    -- Why: Enables async generation with status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',     -- Queued for generation
        'generating',  -- Currently being generated
        'completed',   -- Successfully generated
        'failed',      -- Generation failed
        'expired'      -- File no longer available
    )),

    -- What: Report parameters used
    -- Where: Snapshot of configuration at execution time
    -- Why: Historical record of what was generated
    parameters JSONB DEFAULT '{}',

    -- What: Date range covered by report
    -- Where: Defines data scope
    -- Why: Clear indication of report timeframe
    date_range_start DATE,
    date_range_end DATE,

    -- What: Generated file information
    -- Where: Storage location and metadata
    -- Why: Enables download and delivery
    output_format VARCHAR(10),
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    file_checksum VARCHAR(64),

    -- What: Execution timing metrics
    -- Where: Performance tracking
    -- Why: Helps identify slow reports
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    generation_time_ms INTEGER,

    -- What: Error information if failed
    -- Where: Debugging and retry logic
    -- Why: Helps diagnose generation failures
    error_message TEXT,
    error_details JSONB,

    -- What: File expiration
    -- Where: Cleanup scheduling
    -- Why: Reports shouldn't be stored forever
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- COHORT ANALYTICS TABLES
-- ============================================================================

-- Cohorts: Groups of students for comparison
CREATE TABLE IF NOT EXISTS analytics_cohorts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- What: Cohort type classification
    -- Where: Determines membership rules
    -- Why: Different cohort types have different use cases
    cohort_type VARCHAR(30) NOT NULL CHECK (cohort_type IN (
        'enrollment_date',   -- Based on when students enrolled
        'course',            -- Students in specific course
        'track',             -- Students in learning track
        'manual',            -- Manually selected students
        'performance',       -- Based on performance criteria
        'dynamic'            -- Rule-based dynamic membership
    )),

    -- What: Membership criteria
    -- Where: Rules for automatic membership
    -- Why: Dynamic cohorts update automatically
    membership_rules JSONB DEFAULT '{}',

    -- What: Linked entity for cohort
    -- Where: Course or track reference
    -- Why: Some cohorts are tied to specific content
    linked_course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    linked_track_id UUID REFERENCES learning_tracks(id) ON DELETE SET NULL,

    -- What: Cohort metadata
    -- Where: Additional categorization
    -- Why: Enables filtering and grouping
    tags VARCHAR(50)[] DEFAULT ARRAY[]::VARCHAR[],

    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    member_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cohort Members: Students in each cohort
CREATE TABLE IF NOT EXISTS cohort_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id UUID NOT NULL REFERENCES analytics_cohorts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- What: Membership timestamp
    -- Where: When student joined cohort
    -- Why: Important for time-based analysis
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- What: Membership status
    -- Where: Active vs historical membership
    -- Why: Track membership changes over time
    is_active BOOLEAN DEFAULT true,
    left_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT unique_cohort_member UNIQUE (cohort_id, user_id)
);

-- Cohort Snapshots: Point-in-time cohort metrics
CREATE TABLE IF NOT EXISTS cohort_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id UUID NOT NULL REFERENCES analytics_cohorts(id) ON DELETE CASCADE,

    -- What: Snapshot timestamp
    -- Where: When metrics were captured
    -- Why: Enables trend analysis over time
    snapshot_date DATE NOT NULL,

    -- What: Aggregate metrics
    -- Where: Computed cohort statistics
    -- Why: Pre-computed for fast retrieval
    member_count INTEGER NOT NULL DEFAULT 0,
    avg_completion_rate DECIMAL(5,2),
    avg_quiz_score DECIMAL(5,2),
    avg_engagement_score DECIMAL(5,2),
    avg_time_spent_minutes INTEGER,

    -- What: Distribution metrics
    -- Where: Performance distribution within cohort
    -- Why: Shows spread, not just averages
    completion_distribution JSONB DEFAULT '{}',
    score_distribution JSONB DEFAULT '{}',

    -- What: Activity metrics
    -- Where: Engagement indicators
    -- Why: Tracks cohort activity levels
    active_member_count INTEGER DEFAULT 0,
    at_risk_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,

    -- What: Detailed metrics
    -- Where: Full metric breakdown
    -- Why: Comprehensive snapshot storage
    metrics JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_cohort_snapshot UNIQUE (cohort_id, snapshot_date)
);

-- ============================================================================
-- LEARNING PATH ANALYTICS TABLES
-- ============================================================================

-- Learning Path Progress: Track student progress through paths
CREATE TABLE IF NOT EXISTS learning_path_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES learning_tracks(id) ON DELETE CASCADE,

    -- What: Overall path progress
    -- Where: Aggregate completion percentage
    -- Why: Quick overview of position in path
    overall_progress DECIMAL(5,2) DEFAULT 0.00,

    -- What: Current position in path
    -- Where: Which course/module is current
    -- Why: Shows where student is in sequence
    current_course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    current_module_order INTEGER,

    -- What: Milestone tracking
    -- Where: Key checkpoints completed
    -- Why: Visualize major progress points
    milestones_completed JSONB DEFAULT '[]',

    -- What: Time tracking
    -- Where: Duration metrics
    -- Why: Pace analysis and predictions
    started_at TIMESTAMP WITH TIME ZONE,
    estimated_completion_at TIMESTAMP WITH TIME ZONE,
    actual_completion_at TIMESTAMP WITH TIME ZONE,
    total_time_spent_minutes INTEGER DEFAULT 0,

    -- What: Performance metrics
    -- Where: Path-level performance
    -- Why: Track quality of progress
    avg_quiz_score DECIMAL(5,2),
    avg_assignment_score DECIMAL(5,2),

    -- What: Status indicators
    -- Where: Current state tracking
    -- Why: Quick status identification
    status VARCHAR(20) DEFAULT 'not_started' CHECK (status IN (
        'not_started',
        'in_progress',
        'on_track',
        'behind',
        'at_risk',
        'completed',
        'abandoned'
    )),

    last_activity_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_user_track_progress UNIQUE (user_id, track_id)
);

-- Learning Path Events: Detailed progress events
CREATE TABLE IF NOT EXISTS learning_path_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    progress_id UUID NOT NULL REFERENCES learning_path_progress(id) ON DELETE CASCADE,

    -- What: Event type
    -- Where: Classification of progress event
    -- Why: Different events need different handling
    event_type VARCHAR(30) NOT NULL CHECK (event_type IN (
        'path_started',
        'course_started',
        'course_completed',
        'module_completed',
        'quiz_completed',
        'milestone_reached',
        'certificate_earned',
        'status_changed',
        'pace_adjusted'
    )),

    -- What: Event details
    -- Where: Specific event data
    -- Why: Full context for each event
    event_data JSONB DEFAULT '{}',

    -- What: Related entities
    -- Where: What entity triggered event
    -- Why: Enables drill-down analysis
    related_course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    related_module_id UUID,

    -- What: Metrics at event time
    -- Where: Snapshot of progress
    -- Why: Historical progress tracking
    progress_at_event DECIMAL(5,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- NOTIFICATION THRESHOLDS TABLES
-- ============================================================================

-- Alert Thresholds: Configurable alert rules
CREATE TABLE IF NOT EXISTS analytics_alert_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What: Alert owner
    -- Where: User or organization-level alerts
    -- Why: Different alert scopes
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- What: Alert metric type
    -- Where: What metric triggers alert
    -- Why: Different metrics need different thresholds
    metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN (
        'engagement_score',
        'completion_rate',
        'quiz_score',
        'days_inactive',
        'at_risk_count',
        'drop_rate',
        'time_spent',
        'progress_rate'
    )),

    -- What: Threshold configuration
    -- Where: Trigger conditions
    -- Why: Customizable alert sensitivity
    threshold_operator VARCHAR(10) NOT NULL CHECK (threshold_operator IN (
        'lt', 'lte', 'gt', 'gte', 'eq', 'between'
    )),
    threshold_value DECIMAL(10,2) NOT NULL,
    threshold_value_upper DECIMAL(10,2),  -- For 'between' operator

    -- What: Alert scope
    -- Where: What entities to monitor
    -- Why: Course-specific vs org-wide alerts
    scope VARCHAR(20) DEFAULT 'organization' CHECK (scope IN (
        'course', 'track', 'organization', 'platform'
    )),
    scope_entity_id UUID,

    -- What: Alert severity
    -- Where: Prioritization
    -- Why: Different response urgency
    severity VARCHAR(20) DEFAULT 'warning' CHECK (severity IN (
        'info', 'warning', 'critical'
    )),

    -- What: Notification configuration
    -- Where: How to deliver alerts
    -- Why: Different delivery preferences
    notification_channels VARCHAR(20)[] DEFAULT ARRAY['in_app'],
    notification_config JSONB DEFAULT '{}',

    -- What: Cooldown period
    -- Where: Minimum time between alerts
    -- Why: Prevents alert fatigue
    cooldown_minutes INTEGER DEFAULT 60,
    last_triggered_at TIMESTAMP WITH TIME ZONE,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT alert_owner_check CHECK (
        (user_id IS NOT NULL AND organization_id IS NULL) OR
        (user_id IS NULL AND organization_id IS NOT NULL)
    )
);

-- Alert History: Record of triggered alerts
CREATE TABLE IF NOT EXISTS analytics_alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    threshold_id UUID NOT NULL REFERENCES analytics_alert_thresholds(id) ON DELETE CASCADE,

    -- What: Alert trigger details
    -- Where: What caused the alert
    -- Why: Context for investigation
    triggered_value DECIMAL(10,2) NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- What: Affected entities
    -- Where: Which students/courses triggered
    -- Why: Actionable information
    affected_entities JSONB DEFAULT '[]',
    affected_count INTEGER DEFAULT 0,

    -- What: Alert resolution
    -- Where: How/when addressed
    -- Why: Track response to alerts
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN (
        'active', 'acknowledged', 'resolved', 'dismissed'
    )),
    acknowledged_by UUID REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,

    -- What: Notification delivery
    -- Where: Track delivery status
    -- Why: Ensure alerts are received
    notifications_sent JSONB DEFAULT '[]',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Dashboard indexes
CREATE INDEX IF NOT EXISTS idx_dashboard_templates_role ON dashboard_templates(target_role);
CREATE INDEX IF NOT EXISTS idx_dashboard_templates_scope ON dashboard_templates(scope, organization_id);
CREATE INDEX IF NOT EXISTS idx_user_dashboards_user ON user_dashboards(user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_widget_instances_dashboard ON widget_instances(dashboard_id);

-- Report indexes
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_user ON scheduled_reports(user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_next_run ON scheduled_reports(next_run_at) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_report_executions_user ON report_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_report_executions_status ON report_executions(status) WHERE status IN ('pending', 'generating');
CREATE INDEX IF NOT EXISTS idx_report_executions_expires ON report_executions(expires_at) WHERE status = 'completed';

-- Cohort indexes
CREATE INDEX IF NOT EXISTS idx_analytics_cohorts_org ON analytics_cohorts(organization_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_cohort_members_cohort ON cohort_members(cohort_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_cohort_members_user ON cohort_members(user_id);
CREATE INDEX IF NOT EXISTS idx_cohort_snapshots_cohort_date ON cohort_snapshots(cohort_id, snapshot_date DESC);

-- Learning path indexes
CREATE INDEX IF NOT EXISTS idx_learning_path_progress_user ON learning_path_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_path_progress_track ON learning_path_progress(track_id);
CREATE INDEX IF NOT EXISTS idx_learning_path_progress_status ON learning_path_progress(status) WHERE status IN ('in_progress', 'at_risk');
CREATE INDEX IF NOT EXISTS idx_learning_path_events_progress ON learning_path_events(progress_id);
CREATE INDEX IF NOT EXISTS idx_learning_path_events_type ON learning_path_events(event_type, created_at DESC);

-- Alert indexes
CREATE INDEX IF NOT EXISTS idx_alert_thresholds_user ON analytics_alert_thresholds(user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_alert_thresholds_org ON analytics_alert_thresholds(organization_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_alert_history_threshold ON analytics_alert_history(threshold_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_status ON analytics_alert_history(status) WHERE status = 'active';

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to calculate next run time for scheduled reports
CREATE OR REPLACE FUNCTION calculate_next_run_time(
    p_schedule_type VARCHAR(20),
    p_schedule_day INTEGER,
    p_schedule_time TIME,
    p_schedule_timezone VARCHAR(50)
) RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    v_now TIMESTAMP WITH TIME ZONE;
    v_next_run TIMESTAMP WITH TIME ZONE;
    v_target_time TIME;
BEGIN
    v_now := CURRENT_TIMESTAMP AT TIME ZONE p_schedule_timezone;
    v_target_time := COALESCE(p_schedule_time, '09:00:00'::TIME);

    CASE p_schedule_type
        WHEN 'daily' THEN
            v_next_run := DATE_TRUNC('day', v_now) + v_target_time;
            IF v_next_run <= v_now THEN
                v_next_run := v_next_run + INTERVAL '1 day';
            END IF;

        WHEN 'weekly' THEN
            v_next_run := DATE_TRUNC('week', v_now) + ((COALESCE(p_schedule_day, 1) - 1) || ' days')::INTERVAL + v_target_time;
            IF v_next_run <= v_now THEN
                v_next_run := v_next_run + INTERVAL '1 week';
            END IF;

        WHEN 'biweekly' THEN
            v_next_run := DATE_TRUNC('week', v_now) + ((COALESCE(p_schedule_day, 1) - 1) || ' days')::INTERVAL + v_target_time;
            IF v_next_run <= v_now THEN
                v_next_run := v_next_run + INTERVAL '2 weeks';
            END IF;

        WHEN 'monthly' THEN
            v_next_run := DATE_TRUNC('month', v_now) + ((COALESCE(p_schedule_day, 1) - 1) || ' days')::INTERVAL + v_target_time;
            IF v_next_run <= v_now THEN
                v_next_run := v_next_run + INTERVAL '1 month';
            END IF;

        WHEN 'quarterly' THEN
            v_next_run := DATE_TRUNC('quarter', v_now) + ((COALESCE(p_schedule_day, 1) - 1) || ' days')::INTERVAL + v_target_time;
            IF v_next_run <= v_now THEN
                v_next_run := v_next_run + INTERVAL '3 months';
            END IF;

        ELSE
            RETURN NULL;
    END CASE;

    RETURN v_next_run AT TIME ZONE p_schedule_timezone;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update cohort member count
CREATE OR REPLACE FUNCTION update_cohort_member_count() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE analytics_cohorts
        SET member_count = (
            SELECT COUNT(*) FROM cohort_members
            WHERE cohort_id = NEW.cohort_id AND is_active = true
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.cohort_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE analytics_cohorts
        SET member_count = (
            SELECT COUNT(*) FROM cohort_members
            WHERE cohort_id = OLD.cohort_id AND is_active = true
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.cohort_id;
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_cohort_member_count
    AFTER INSERT OR UPDATE OR DELETE ON cohort_members
    FOR EACH ROW EXECUTE FUNCTION update_cohort_member_count();

-- Trigger to update scheduled report next_run_at
CREATE OR REPLACE FUNCTION update_scheduled_report_next_run() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = true AND NEW.schedule_type != 'once' THEN
        NEW.next_run_at := calculate_next_run_time(
            NEW.schedule_type,
            NEW.schedule_day,
            NEW.schedule_time,
            NEW.schedule_timezone
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_scheduled_report_next_run
    BEFORE INSERT OR UPDATE ON scheduled_reports
    FOR EACH ROW EXECUTE FUNCTION update_scheduled_report_next_run();

-- Trigger to track learning path events on progress changes
CREATE OR REPLACE FUNCTION track_learning_path_status_change() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO learning_path_events (
            progress_id, event_type, event_data, progress_at_event
        ) VALUES (
            NEW.id,
            'status_changed',
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status
            ),
            NEW.overall_progress
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_track_learning_path_status_change
    AFTER UPDATE ON learning_path_progress
    FOR EACH ROW EXECUTE FUNCTION track_learning_path_status_change();

-- ============================================================================
-- SEED DATA: Default Dashboard Templates
-- ============================================================================

-- Insert default dashboard widgets
INSERT INTO dashboard_widgets (widget_type, name, description, default_width, default_height, data_source, allowed_roles) VALUES
    ('kpi_card', 'Active Students', 'Shows count of currently active students', 3, 1,
     '{"endpoint": "/api/analytics/kpi/active-students", "refreshInterval": 300}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('kpi_card', 'Course Completion Rate', 'Average completion rate across courses', 3, 1,
     '{"endpoint": "/api/analytics/kpi/completion-rate", "refreshInterval": 300}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('kpi_card', 'Average Quiz Score', 'Platform-wide average quiz score', 3, 1,
     '{"endpoint": "/api/analytics/kpi/avg-quiz-score", "refreshInterval": 300}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('kpi_card', 'At-Risk Students', 'Count of students flagged as at-risk', 3, 1,
     '{"endpoint": "/api/analytics/kpi/at-risk-count", "refreshInterval": 60}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('line_chart', 'Enrollment Trends', 'New enrollments over time', 6, 3,
     '{"endpoint": "/api/analytics/charts/enrollment-trends", "refreshInterval": 3600}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('line_chart', 'Activity Timeline', 'Student activity over time', 6, 3,
     '{"endpoint": "/api/analytics/charts/activity-timeline", "refreshInterval": 300}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('bar_chart', 'Course Performance', 'Comparison of course metrics', 6, 3,
     '{"endpoint": "/api/analytics/charts/course-performance", "refreshInterval": 3600}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('pie_chart', 'Completion Status', 'Distribution of completion statuses', 4, 3,
     '{"endpoint": "/api/analytics/charts/completion-distribution", "refreshInterval": 3600}',
     ARRAY['site_admin', 'org_admin', 'instructor', 'student']),

    ('heatmap', 'Weekly Activity', 'Activity heatmap by day and hour', 8, 3,
     '{"endpoint": "/api/analytics/charts/activity-heatmap", "refreshInterval": 3600}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('table', 'Recent Activity', 'Latest student activities', 6, 4,
     '{"endpoint": "/api/analytics/tables/recent-activity", "refreshInterval": 60}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('leaderboard', 'Top Performers', 'Highest achieving students', 4, 4,
     '{"endpoint": "/api/analytics/tables/top-performers", "refreshInterval": 3600}',
     ARRAY['site_admin', 'org_admin', 'instructor', 'student']),

    ('risk_indicator', 'At-Risk Alerts', 'Students requiring attention', 6, 3,
     '{"endpoint": "/api/analytics/alerts/at-risk", "refreshInterval": 60}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('progress_ring', 'My Progress', 'Personal course progress', 3, 2,
     '{"endpoint": "/api/analytics/student/my-progress", "refreshInterval": 300}',
     ARRAY['student']),

    ('learning_path', 'Learning Path Progress', 'Track progress visualization', 12, 3,
     '{"endpoint": "/api/analytics/student/learning-path", "refreshInterval": 300}',
     ARRAY['student']),

    ('cohort_comparison', 'Cohort Comparison', 'Compare student group performance', 8, 4,
     '{"endpoint": "/api/analytics/cohorts/comparison", "refreshInterval": 3600}',
     ARRAY['site_admin', 'org_admin', 'instructor']),

    ('engagement_score', 'Engagement Score', 'Personal engagement metrics', 4, 2,
     '{"endpoint": "/api/analytics/student/engagement", "refreshInterval": 300}',
     ARRAY['student']),

    ('completion_funnel', 'Completion Funnel', 'Student journey visualization', 6, 4,
     '{"endpoint": "/api/analytics/charts/completion-funnel", "refreshInterval": 3600}',
     ARRAY['site_admin', 'org_admin', 'instructor'])
ON CONFLICT DO NOTHING;

-- Insert default report templates
INSERT INTO report_templates (name, description, report_type, config, output_formats) VALUES
    ('Weekly Student Progress', 'Summary of student progress for the past week', 'student_progress',
     '{"metrics": ["completion_rate", "quiz_scores", "time_spent", "activity_count"], "groupBy": "course"}',
     ARRAY['pdf', 'csv']),

    ('Monthly Course Analytics', 'Comprehensive course performance report', 'course_analytics',
     '{"metrics": ["enrollments", "completions", "avg_score", "engagement"], "includeCharts": true}',
     ARRAY['pdf', 'xlsx']),

    ('At-Risk Student Report', 'Students identified as at-risk of not completing', 'engagement_summary',
     '{"filters": {"riskLevel": ["high", "critical"]}, "includeRecommendations": true}',
     ARRAY['pdf', 'csv']),

    ('Cohort Comparison Report', 'Compare performance across student groups', 'cohort_comparison',
     '{"metrics": ["completion_rate", "avg_score", "engagement_score", "time_to_complete"]}',
     ARRAY['pdf', 'xlsx']),

    ('Organization Overview', 'High-level organizational metrics', 'organization_overview',
     '{"metrics": ["total_users", "active_courses", "completion_rates", "certifications_issued"]}',
     ARRAY['pdf'])
ON CONFLICT DO NOTHING;

COMMIT;
