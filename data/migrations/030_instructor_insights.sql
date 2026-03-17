-- ============================================================================
-- Migration 030: Instructor Insights
-- ============================================================================
-- What: Creates tables for comprehensive instructor analytics and insights
-- Where: Analytics module for measuring teaching effectiveness
-- Why: Provides instructors with actionable insights to improve teaching quality,
--      track student engagement, and optimize course content delivery

-- ============================================================================
-- TEACHING EFFECTIVENESS METRICS
-- ============================================================================
-- Tracks core teaching quality indicators per instructor

CREATE TABLE IF NOT EXISTS instructor_effectiveness_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    organization_id UUID,

    -- Core metrics
    overall_rating DECIMAL(3, 2) CHECK (overall_rating >= 0 AND overall_rating <= 5),
    teaching_quality_score DECIMAL(5, 2) CHECK (teaching_quality_score >= 0 AND teaching_quality_score <= 100),
    content_clarity_score DECIMAL(5, 2) CHECK (content_clarity_score >= 0 AND content_clarity_score <= 100),
    engagement_score DECIMAL(5, 2) CHECK (engagement_score >= 0 AND engagement_score <= 100),
    responsiveness_score DECIMAL(5, 2) CHECK (responsiveness_score >= 0 AND responsiveness_score <= 100),

    -- Derived metrics
    total_students_taught INTEGER DEFAULT 0,
    course_completion_rate DECIMAL(5, 2) CHECK (course_completion_rate >= 0 AND course_completion_rate <= 100),
    average_quiz_score DECIMAL(5, 2),
    student_retention_rate DECIMAL(5, 2) CHECK (student_retention_rate >= 0 AND student_retention_rate <= 100),

    -- Trends
    rating_trend VARCHAR(20) CHECK (rating_trend IN ('improving', 'stable', 'declining')),
    engagement_trend VARCHAR(20) CHECK (engagement_trend IN ('improving', 'stable', 'declining')),

    -- Period tracking
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instructor_effectiveness_instructor ON instructor_effectiveness_metrics(instructor_id);
CREATE INDEX idx_instructor_effectiveness_org ON instructor_effectiveness_metrics(organization_id);
CREATE INDEX idx_instructor_effectiveness_period ON instructor_effectiveness_metrics(period_start, period_end);

-- ============================================================================
-- COURSE PERFORMANCE ANALYTICS
-- ============================================================================
-- Per-course performance metrics for each instructor

CREATE TABLE IF NOT EXISTS instructor_course_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    course_id UUID NOT NULL,
    course_instance_id UUID,
    organization_id UUID,

    -- Enrollment metrics
    total_enrolled INTEGER DEFAULT 0,
    active_students INTEGER DEFAULT 0,
    completed_students INTEGER DEFAULT 0,
    dropped_students INTEGER DEFAULT 0,

    -- Performance metrics
    average_score DECIMAL(5, 2),
    median_score DECIMAL(5, 2),
    score_std_deviation DECIMAL(5, 2),
    pass_rate DECIMAL(5, 2) CHECK (pass_rate >= 0 AND pass_rate <= 100),

    -- Engagement metrics
    average_time_to_complete INTERVAL,
    content_views_per_student DECIMAL(10, 2),
    lab_completions_per_student DECIMAL(10, 2),
    quiz_attempts_per_student DECIMAL(10, 2),

    -- Quality indicators
    content_rating DECIMAL(3, 2) CHECK (content_rating >= 0 AND content_rating <= 5),
    difficulty_rating DECIMAL(3, 2) CHECK (difficulty_rating >= 0 AND difficulty_rating <= 5),
    workload_rating DECIMAL(3, 2) CHECK (workload_rating >= 0 AND workload_rating <= 5),

    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(instructor_id, course_id, course_instance_id, period_start)
);

CREATE INDEX idx_instructor_course_perf_instructor ON instructor_course_performance(instructor_id);
CREATE INDEX idx_instructor_course_perf_course ON instructor_course_performance(course_id);
CREATE INDEX idx_instructor_course_perf_period ON instructor_course_performance(period_start, period_end);

-- ============================================================================
-- STUDENT ENGAGEMENT METRICS PER INSTRUCTOR
-- ============================================================================
-- Aggregated student engagement data per instructor

CREATE TABLE IF NOT EXISTS instructor_student_engagement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    organization_id UUID,

    -- Session metrics
    total_sessions INTEGER DEFAULT 0,
    total_session_duration INTERVAL,
    average_session_duration INTERVAL,
    peak_hour INTEGER CHECK (peak_hour >= 0 AND peak_hour <= 23),

    -- Interaction metrics
    total_content_views INTEGER DEFAULT 0,
    total_lab_sessions INTEGER DEFAULT 0,
    total_quiz_attempts INTEGER DEFAULT 0,
    total_forum_posts INTEGER DEFAULT 0,
    total_questions_asked INTEGER DEFAULT 0,

    -- Response metrics
    questions_answered INTEGER DEFAULT 0,
    average_response_time INTERVAL,

    -- Engagement patterns
    most_active_day VARCHAR(10),
    engagement_distribution JSONB DEFAULT '{}',
    activity_heatmap JSONB DEFAULT '{}',

    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(instructor_id, period_start, period_end)
);

CREATE INDEX idx_instructor_engagement_instructor ON instructor_student_engagement(instructor_id);
CREATE INDEX idx_instructor_engagement_period ON instructor_student_engagement(period_start, period_end);

-- ============================================================================
-- CONTENT QUALITY RATINGS
-- ============================================================================
-- Student ratings and feedback on instructor content

CREATE TABLE IF NOT EXISTS instructor_content_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    course_id UUID NOT NULL,
    content_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    student_id UUID NOT NULL,

    -- Ratings (1-5 scale)
    clarity_rating INTEGER CHECK (clarity_rating >= 1 AND clarity_rating <= 5),
    helpfulness_rating INTEGER CHECK (helpfulness_rating >= 1 AND helpfulness_rating <= 5),
    relevance_rating INTEGER CHECK (relevance_rating >= 1 AND relevance_rating <= 5),
    difficulty_rating INTEGER CHECK (difficulty_rating >= 1 AND difficulty_rating <= 5),

    -- Feedback
    feedback_text TEXT,
    feedback_sentiment VARCHAR(20) CHECK (feedback_sentiment IN ('positive', 'neutral', 'negative', 'mixed')),

    -- Metadata
    is_anonymous BOOLEAN DEFAULT false,
    is_verified_enrollment BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(content_id, student_id)
);

CREATE INDEX idx_content_ratings_instructor ON instructor_content_ratings(instructor_id);
CREATE INDEX idx_content_ratings_course ON instructor_content_ratings(course_id);
CREATE INDEX idx_content_ratings_content ON instructor_content_ratings(content_id);
CREATE INDEX idx_content_ratings_sentiment ON instructor_content_ratings(feedback_sentiment);

-- ============================================================================
-- INSTRUCTOR FEEDBACK/REVIEWS
-- ============================================================================
-- Overall instructor reviews from students

CREATE TABLE IF NOT EXISTS instructor_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    course_id UUID,
    student_id UUID NOT NULL,
    organization_id UUID,

    -- Overall rating
    overall_rating INTEGER NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),

    -- Dimension ratings
    knowledge_rating INTEGER CHECK (knowledge_rating >= 1 AND knowledge_rating <= 5),
    communication_rating INTEGER CHECK (communication_rating >= 1 AND communication_rating <= 5),
    availability_rating INTEGER CHECK (availability_rating >= 1 AND availability_rating <= 5),
    feedback_quality_rating INTEGER CHECK (feedback_quality_rating >= 1 AND feedback_quality_rating <= 5),
    organization_rating INTEGER CHECK (organization_rating >= 1 AND organization_rating <= 5),

    -- Review content
    review_title VARCHAR(200),
    review_text TEXT,
    pros TEXT,
    cons TEXT,

    -- Moderation
    is_approved BOOLEAN DEFAULT false,
    is_flagged BOOLEAN DEFAULT false,
    flagged_reason VARCHAR(100),
    moderated_by UUID,
    moderated_at TIMESTAMP WITH TIME ZONE,

    -- Helpful votes
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(instructor_id, course_id, student_id)
);

CREATE INDEX idx_instructor_reviews_instructor ON instructor_reviews(instructor_id);
CREATE INDEX idx_instructor_reviews_course ON instructor_reviews(course_id);
CREATE INDEX idx_instructor_reviews_rating ON instructor_reviews(overall_rating);
CREATE INDEX idx_instructor_reviews_approved ON instructor_reviews(is_approved);

-- ============================================================================
-- TEACHING LOAD DISTRIBUTION
-- ============================================================================
-- Tracks instructor workload and capacity

CREATE TABLE IF NOT EXISTS instructor_teaching_load (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    organization_id UUID,

    -- Course load
    active_courses INTEGER DEFAULT 0,
    total_courses_taught INTEGER DEFAULT 0,
    courses_this_period INTEGER DEFAULT 0,

    -- Student load
    current_students INTEGER DEFAULT 0,
    total_students_capacity INTEGER,
    student_load_percentage DECIMAL(5, 2),

    -- Time allocation
    teaching_hours_per_week DECIMAL(5, 2),
    grading_hours_per_week DECIMAL(5, 2),
    support_hours_per_week DECIMAL(5, 2),
    content_creation_hours_per_week DECIMAL(5, 2),

    -- Workload metrics
    assignments_pending_grading INTEGER DEFAULT 0,
    questions_pending_response INTEGER DEFAULT 0,
    estimated_pending_hours DECIMAL(5, 2),

    -- Capacity status
    capacity_status VARCHAR(20) CHECK (capacity_status IN ('available', 'moderate', 'high', 'overloaded')),
    recommended_action VARCHAR(100),

    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(instructor_id, period_start, period_end)
);

CREATE INDEX idx_teaching_load_instructor ON instructor_teaching_load(instructor_id);
CREATE INDEX idx_teaching_load_status ON instructor_teaching_load(capacity_status);
CREATE INDEX idx_teaching_load_period ON instructor_teaching_load(period_start, period_end);

-- ============================================================================
-- RESPONSE TIME METRICS
-- ============================================================================
-- Tracks instructor response times for grading, questions, etc.

CREATE TABLE IF NOT EXISTS instructor_response_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    organization_id UUID,

    -- Grading response times
    avg_grading_time INTERVAL,
    median_grading_time INTERVAL,
    grading_sla_compliance DECIMAL(5, 2) CHECK (grading_sla_compliance >= 0 AND grading_sla_compliance <= 100),
    assignments_graded INTEGER DEFAULT 0,
    assignments_overdue INTEGER DEFAULT 0,

    -- Question response times
    avg_question_response_time INTERVAL,
    median_question_response_time INTERVAL,
    question_sla_compliance DECIMAL(5, 2) CHECK (question_sla_compliance >= 0 AND question_sla_compliance <= 100),
    questions_answered INTEGER DEFAULT 0,
    questions_unanswered INTEGER DEFAULT 0,

    -- Feedback response times
    avg_feedback_time INTERVAL,
    feedback_quality_score DECIMAL(5, 2) CHECK (feedback_quality_score >= 0 AND feedback_quality_score <= 100),

    -- Communication metrics
    messages_sent INTEGER DEFAULT 0,
    announcements_made INTEGER DEFAULT 0,
    forum_participation_rate DECIMAL(5, 2),

    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(instructor_id, period_start, period_end)
);

CREATE INDEX idx_response_metrics_instructor ON instructor_response_metrics(instructor_id);
CREATE INDEX idx_response_metrics_period ON instructor_response_metrics(period_start, period_end);

-- ============================================================================
-- IMPROVEMENT RECOMMENDATIONS
-- ============================================================================
-- AI-generated recommendations for instructors

CREATE TABLE IF NOT EXISTS instructor_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    course_id UUID,
    organization_id UUID,

    -- Recommendation details
    recommendation_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    category VARCHAR(50) NOT NULL,

    -- Content
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    action_items JSONB DEFAULT '[]',
    expected_impact VARCHAR(100),
    estimated_effort VARCHAR(50),

    -- Source data
    based_on_metrics JSONB DEFAULT '{}',
    comparison_data JSONB DEFAULT '{}',

    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'acknowledged', 'in_progress', 'completed', 'dismissed')),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    dismissed_reason TEXT,

    -- Effectiveness
    outcome_measured BOOLEAN DEFAULT false,
    outcome_data JSONB,

    -- Timestamps
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_recommendations_instructor ON instructor_recommendations(instructor_id);
CREATE INDEX idx_recommendations_type ON instructor_recommendations(recommendation_type);
CREATE INDEX idx_recommendations_priority ON instructor_recommendations(priority);
CREATE INDEX idx_recommendations_status ON instructor_recommendations(status);
CREATE INDEX idx_recommendations_expires ON instructor_recommendations(expires_at);

-- ============================================================================
-- COMPARATIVE ANALYTICS
-- ============================================================================
-- Peer comparison metrics (anonymized)

CREATE TABLE IF NOT EXISTS instructor_peer_comparison (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    organization_id UUID,
    comparison_group VARCHAR(50) NOT NULL,

    -- Instructor's metrics
    instructor_score DECIMAL(5, 2),

    -- Peer metrics (anonymized)
    peer_average DECIMAL(5, 2),
    peer_median DECIMAL(5, 2),
    peer_min DECIMAL(5, 2),
    peer_max DECIMAL(5, 2),
    peer_std_deviation DECIMAL(5, 2),

    -- Percentile ranking
    percentile_rank INTEGER CHECK (percentile_rank >= 0 AND percentile_rank <= 100),

    -- Metric details
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    sample_size INTEGER,

    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(instructor_id, metric_name, comparison_group, period_start)
);

CREATE INDEX idx_peer_comparison_instructor ON instructor_peer_comparison(instructor_id);
CREATE INDEX idx_peer_comparison_metric ON instructor_peer_comparison(metric_name);
CREATE INDEX idx_peer_comparison_period ON instructor_peer_comparison(period_start, period_end);

-- ============================================================================
-- GOAL TRACKING
-- ============================================================================
-- Personal improvement goals set by instructors

CREATE TABLE IF NOT EXISTS instructor_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL,
    organization_id UUID,

    -- Goal details
    goal_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- Target metrics
    metric_name VARCHAR(100) NOT NULL,
    baseline_value DECIMAL(10, 2),
    target_value DECIMAL(10, 2) NOT NULL,
    current_value DECIMAL(10, 2),

    -- Progress
    progress_percentage DECIMAL(5, 2) DEFAULT 0,

    -- Timeline
    start_date DATE NOT NULL,
    target_date DATE NOT NULL,
    completed_date DATE,

    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'completed', 'failed', 'cancelled')),

    -- Notes
    milestones JSONB DEFAULT '[]',
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instructor_goals_instructor ON instructor_goals(instructor_id);
CREATE INDEX idx_instructor_goals_type ON instructor_goals(goal_type);
CREATE INDEX idx_instructor_goals_status ON instructor_goals(status);
CREATE INDEX idx_instructor_goals_dates ON instructor_goals(target_date);

-- ============================================================================
-- TRIGGER: Update timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_instructor_insights_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables
DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'instructor_effectiveness_metrics',
        'instructor_course_performance',
        'instructor_student_engagement',
        'instructor_content_ratings',
        'instructor_reviews',
        'instructor_teaching_load',
        'instructor_response_metrics',
        'instructor_recommendations',
        'instructor_goals'
    ])
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%s_timestamp ON %I;
            CREATE TRIGGER update_%s_timestamp
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_instructor_insights_timestamp();
        ', tbl, tbl, tbl, tbl);
    END LOOP;
END $$;

-- ============================================================================
-- SEED: Default recommendation types
-- ============================================================================

INSERT INTO instructor_recommendations (
    instructor_id,
    recommendation_type,
    priority,
    category,
    title,
    description,
    action_items,
    expected_impact,
    estimated_effort,
    status
) VALUES
    (
        '00000000-0000-0000-0000-000000000000'::UUID,
        'TEMPLATE_ENGAGEMENT',
        'medium',
        'engagement',
        '[Template] Improve Student Engagement',
        'This is a template recommendation for improving student engagement through interactive activities.',
        '["Add discussion prompts", "Include hands-on exercises", "Use multimedia content"]'::JSONB,
        'Increase engagement by 15-25%',
        '2-4 hours',
        'dismissed'
    ),
    (
        '00000000-0000-0000-0000-000000000000'::UUID,
        'TEMPLATE_GRADING',
        'high',
        'responsiveness',
        '[Template] Improve Grading Turnaround',
        'This is a template recommendation for faster grading and feedback delivery.',
        '["Set grading schedule", "Use rubrics", "Batch similar assignments"]'::JSONB,
        'Reduce grading time by 30%',
        '1-2 hours setup',
        'dismissed'
    )
ON CONFLICT DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE instructor_effectiveness_metrics IS 'Core teaching effectiveness scores per instructor';
COMMENT ON TABLE instructor_course_performance IS 'Per-course performance analytics for instructors';
COMMENT ON TABLE instructor_student_engagement IS 'Aggregated student engagement metrics per instructor';
COMMENT ON TABLE instructor_content_ratings IS 'Student ratings on specific content items';
COMMENT ON TABLE instructor_reviews IS 'Overall instructor reviews from students';
COMMENT ON TABLE instructor_teaching_load IS 'Workload and capacity tracking for instructors';
COMMENT ON TABLE instructor_response_metrics IS 'Response time metrics for grading and questions';
COMMENT ON TABLE instructor_recommendations IS 'AI-generated improvement recommendations';
COMMENT ON TABLE instructor_peer_comparison IS 'Anonymized peer comparison metrics';
COMMENT ON TABLE instructor_goals IS 'Personal improvement goals set by instructors';
