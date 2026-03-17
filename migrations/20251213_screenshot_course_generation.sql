-- Screenshot Course Generation Migration
-- Created: 2025-12-13
-- Purpose: Tables for screenshot upload, analysis, and course generation tracking

-- ========================================
-- SCREENSHOT UPLOADS TABLE
-- ========================================
-- Stores metadata about uploaded screenshots for course generation

CREATE TABLE IF NOT EXISTS screenshot_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    image_width INTEGER,
    image_height INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Valid status values
    CONSTRAINT chk_screenshot_status CHECK (
        status IN ('uploaded', 'processing', 'analyzed', 'generating', 'completed', 'failed')
    ),
    -- Valid mime types for images
    CONSTRAINT chk_screenshot_mime CHECK (
        mime_type IN ('image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif')
    )
);

-- Indexes for screenshot_uploads
CREATE INDEX IF NOT EXISTS idx_screenshot_uploads_org ON screenshot_uploads(organization_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_uploads_user ON screenshot_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_screenshot_uploads_status ON screenshot_uploads(status);
CREATE INDEX IF NOT EXISTS idx_screenshot_uploads_hash ON screenshot_uploads(file_hash);
CREATE INDEX IF NOT EXISTS idx_screenshot_uploads_created ON screenshot_uploads(created_at DESC);

-- ========================================
-- SCREENSHOT ANALYSIS RESULTS TABLE
-- ========================================
-- Stores the AI analysis results from vision models

CREATE TABLE IF NOT EXISTS screenshot_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screenshot_id UUID NOT NULL REFERENCES screenshot_uploads(id) ON DELETE CASCADE,
    llm_config_id UUID REFERENCES organization_llm_config(id) ON DELETE SET NULL,
    provider_name VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,

    -- Extracted content
    extracted_text TEXT,
    detected_language VARCHAR(10),
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Structured analysis
    course_structure JSONB DEFAULT '{}',
    detected_elements JSONB DEFAULT '[]',
    suggested_title VARCHAR(500),
    suggested_description TEXT,
    suggested_topics JSONB DEFAULT '[]',
    suggested_difficulty VARCHAR(50),
    suggested_duration_hours INTEGER,

    -- Processing metrics
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    processing_time_ms INTEGER,
    api_cost_estimate DECIMAL(10,6),

    -- Status
    analysis_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Valid analysis status
    CONSTRAINT chk_analysis_status CHECK (
        analysis_status IN ('pending', 'processing', 'completed', 'failed', 'retrying')
    )
);

-- Indexes for analysis results
CREATE INDEX IF NOT EXISTS idx_analysis_screenshot ON screenshot_analysis_results(screenshot_id);
CREATE INDEX IF NOT EXISTS idx_analysis_status ON screenshot_analysis_results(analysis_status);
CREATE INDEX IF NOT EXISTS idx_analysis_provider ON screenshot_analysis_results(provider_name);
CREATE INDEX IF NOT EXISTS idx_analysis_created ON screenshot_analysis_results(created_at DESC);

-- ========================================
-- GENERATED COURSES FROM SCREENSHOTS TABLE
-- ========================================
-- Links screenshots to generated courses for tracking and lineage

CREATE TABLE IF NOT EXISTS screenshot_generated_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screenshot_id UUID NOT NULL REFERENCES screenshot_uploads(id) ON DELETE CASCADE,
    analysis_id UUID NOT NULL REFERENCES screenshot_analysis_results(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Generation details
    generation_prompt TEXT,
    generation_parameters JSONB DEFAULT '{}',
    provider_name VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,

    -- Generated content summary
    modules_generated INTEGER DEFAULT 0,
    lessons_generated INTEGER DEFAULT 0,
    quizzes_generated INTEGER DEFAULT 0,

    -- Metrics
    total_tokens_used INTEGER DEFAULT 0,
    generation_time_ms INTEGER,
    total_cost_estimate DECIMAL(10,6),

    -- Status
    generation_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,

    -- User feedback
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    was_published BOOLEAN DEFAULT FALSE,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,

    -- Valid generation status
    CONSTRAINT chk_generation_status CHECK (
        generation_status IN ('pending', 'generating', 'completed', 'failed', 'cancelled')
    )
);

-- Indexes for generated courses
CREATE INDEX IF NOT EXISTS idx_gen_courses_screenshot ON screenshot_generated_courses(screenshot_id);
CREATE INDEX IF NOT EXISTS idx_gen_courses_course ON screenshot_generated_courses(course_id);
CREATE INDEX IF NOT EXISTS idx_gen_courses_org ON screenshot_generated_courses(organization_id);
CREATE INDEX IF NOT EXISTS idx_gen_courses_status ON screenshot_generated_courses(generation_status);
CREATE INDEX IF NOT EXISTS idx_gen_courses_created ON screenshot_generated_courses(created_at DESC);

-- ========================================
-- SCREENSHOT PROCESSING QUEUE TABLE
-- ========================================
-- Queue for async processing of screenshot analysis

CREATE TABLE IF NOT EXISTS screenshot_processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screenshot_id UUID NOT NULL REFERENCES screenshot_uploads(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    processing_type VARCHAR(50) NOT NULL DEFAULT 'analysis',
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    worker_id VARCHAR(100),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',

    -- Valid status
    CONSTRAINT chk_queue_status CHECK (
        status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')
    ),
    -- Valid processing type
    CONSTRAINT chk_processing_type CHECK (
        processing_type IN ('analysis', 'course_generation', 'rag_indexing')
    )
);

-- Indexes for processing queue
CREATE INDEX IF NOT EXISTS idx_queue_status ON screenshot_processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_scheduled ON screenshot_processing_queue(scheduled_at) WHERE status = 'queued';
CREATE INDEX IF NOT EXISTS idx_queue_priority ON screenshot_processing_queue(priority DESC, scheduled_at) WHERE status = 'queued';
CREATE INDEX IF NOT EXISTS idx_queue_retry ON screenshot_processing_queue(next_retry_at) WHERE status = 'failed' AND attempts < max_attempts;

-- ========================================
-- HELPER FUNCTIONS
-- ========================================

-- Function to get next item from processing queue
CREATE OR REPLACE FUNCTION get_next_screenshot_job(p_worker_id VARCHAR)
RETURNS TABLE (
    job_id UUID,
    screenshot_id UUID,
    processing_type VARCHAR,
    priority INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job_id UUID;
BEGIN
    -- Lock and claim the next available job
    UPDATE screenshot_processing_queue
    SET
        status = 'processing',
        worker_id = p_worker_id,
        started_at = NOW(),
        attempts = attempts + 1
    WHERE id = (
        SELECT id FROM screenshot_processing_queue
        WHERE status = 'queued'
          AND (scheduled_at IS NULL OR scheduled_at <= NOW())
        ORDER BY priority DESC, scheduled_at
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    RETURNING id INTO v_job_id;

    IF v_job_id IS NOT NULL THEN
        RETURN QUERY
        SELECT
            spq.id AS job_id,
            spq.screenshot_id,
            spq.processing_type,
            spq.priority
        FROM screenshot_processing_queue spq
        WHERE spq.id = v_job_id;
    END IF;
END;
$$;

-- Function to complete a processing job
CREATE OR REPLACE FUNCTION complete_screenshot_job(
    p_job_id UUID,
    p_success BOOLEAN,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_success THEN
        UPDATE screenshot_processing_queue
        SET
            status = 'completed',
            completed_at = NOW(),
            error_message = NULL
        WHERE id = p_job_id;
    ELSE
        UPDATE screenshot_processing_queue
        SET
            status = CASE
                WHEN attempts >= max_attempts THEN 'failed'
                ELSE 'queued'
            END,
            error_message = p_error_message,
            next_retry_at = CASE
                WHEN attempts < max_attempts THEN NOW() + (attempts * INTERVAL '5 minutes')
                ELSE NULL
            END,
            worker_id = NULL,
            completed_at = CASE
                WHEN attempts >= max_attempts THEN NOW()
                ELSE NULL
            END
        WHERE id = p_job_id;
    END IF;
END;
$$;

-- Function to get screenshot analysis summary
CREATE OR REPLACE FUNCTION get_screenshot_summary(p_screenshot_id UUID)
RETURNS TABLE (
    screenshot_id UUID,
    status VARCHAR,
    analysis_status VARCHAR,
    generation_status VARCHAR,
    course_id INTEGER,
    suggested_title VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        su.id AS screenshot_id,
        su.status,
        sar.analysis_status,
        sgc.generation_status,
        sgc.course_id,
        sar.suggested_title,
        su.created_at
    FROM screenshot_uploads su
    LEFT JOIN screenshot_analysis_results sar ON sar.screenshot_id = su.id
    LEFT JOIN screenshot_generated_courses sgc ON sgc.screenshot_id = su.id
    WHERE su.id = p_screenshot_id;
END;
$$;

-- ========================================
-- VIEWS
-- ========================================

-- View for screenshot generation metrics by organization
CREATE OR REPLACE VIEW v_screenshot_generation_metrics AS
SELECT
    o.id AS organization_id,
    o.name AS organization_name,
    COUNT(DISTINCT su.id) AS total_screenshots,
    COUNT(DISTINCT CASE WHEN su.status = 'completed' THEN su.id END) AS successful_screenshots,
    COUNT(DISTINCT sgc.course_id) AS courses_generated,
    SUM(sgc.total_tokens_used) AS total_tokens_used,
    SUM(sgc.total_cost_estimate) AS total_cost,
    AVG(sgc.user_rating) AS avg_user_rating,
    COUNT(DISTINCT CASE WHEN sgc.was_published THEN sgc.id END) AS published_courses
FROM organizations o
LEFT JOIN screenshot_uploads su ON su.organization_id = o.id
LEFT JOIN screenshot_generated_courses sgc ON sgc.screenshot_id = su.id
GROUP BY o.id, o.name;

-- ========================================
-- COMMENTS
-- ========================================

COMMENT ON TABLE screenshot_uploads IS 'Stores uploaded screenshots for AI-powered course generation';
COMMENT ON TABLE screenshot_analysis_results IS 'AI vision model analysis results for screenshots';
COMMENT ON TABLE screenshot_generated_courses IS 'Tracks courses generated from screenshot analysis';
COMMENT ON TABLE screenshot_processing_queue IS 'Async processing queue for screenshot analysis jobs';
COMMENT ON FUNCTION get_next_screenshot_job IS 'Atomically claim the next available processing job';
COMMENT ON FUNCTION complete_screenshot_job IS 'Mark a processing job as completed or failed';
COMMENT ON FUNCTION get_screenshot_summary IS 'Get complete status summary for a screenshot';
COMMENT ON VIEW v_screenshot_generation_metrics IS 'Aggregated metrics for screenshot generation by organization';
