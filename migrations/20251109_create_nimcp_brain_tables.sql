-- ============================================================================
-- NIMCP Brain Tables Migration
-- ============================================================================
-- Description: Creates database schema for NIMCP brain instances, interactions,
--              and self-awareness tracking as part of the self-aware learning
--              platform brain integration.
--
-- Business Context:
--   This migration establishes the persistence layer for the platform's
--   neuromorphic AI brain system. Each brain instance (Platform Brain,
--   Student Brains, Instructor Brains) maintains:
--   - Neural state persistence (.bin file references)
--   - Learning and performance metrics
--   - Meta-cognitive self-awareness data
--   - Copy-on-Write (COW) hierarchy tracking
--   - Interaction history for continuous learning
--
-- Architecture:
--   - brain_instances: Core brain entity metadata
--   - brain_interactions: Every interaction logged for learning
--   - brain_self_assessments: Meta-cognitive capability tracking
--   - Hierarchical structure via parent_brain_id (COW clones)
--
-- Author: Course Creator Platform Team
-- Version: 1.0.0
-- Created: 2025-11-09
-- ============================================================================

-- ============================================================================
-- Table: brain_instances
-- ============================================================================
-- Purpose: Store metadata for each brain instance in the hierarchical system
--
-- Business Rules:
--   - Platform brain: brain_type='platform', owner_id=NULL, parent_brain_id=NULL
--   - Student brain: brain_type='student', owner_id=student_id, parent_brain_id=platform_brain_id
--   - Instructor brain: brain_type='instructor', owner_id=instructor_id
--   - Content brain: brain_type='content', owner_id=NULL
--   - Ethics brain: brain_type='ethics', owner_id=NULL
--
-- COW Hierarchy:
--   - parent_brain_id links to the brain this was cloned from (NULL if original)
--   - cow_shared_bytes tracks memory shared with parent (not copied)
--   - cow_copied_bytes tracks memory copied due to unique learning
--
-- Performance Tracking:
--   - total_interactions: Every prediction, learning, reinforcement event
--   - neural_inference_count: Predictions handled by neural network
--   - llm_query_count: Predictions requiring LLM fallback
--   - average_confidence: Running average of prediction confidence
--   - average_accuracy: Running average of prediction accuracy
--
-- Self-Awareness:
--   - strong_domains: JSON object with domain -> accuracy mapping for strengths
--   - weak_domains: JSON object with domain -> accuracy mapping for weaknesses
--   - bias_detections: JSON object with bias_type -> count mapping
-- ============================================================================

CREATE TABLE IF NOT EXISTS brain_instances (
    -- Primary identity
    brain_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brain_type VARCHAR(50) NOT NULL CHECK (brain_type IN ('platform', 'student', 'instructor', 'content', 'ethics')),
    owner_id UUID,  -- student_id, instructor_id, or NULL for platform/content/ethics brains
    parent_brain_id UUID REFERENCES brain_instances(brain_id) ON DELETE SET NULL,  -- For COW hierarchy

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Neural state persistence
    state_file_path VARCHAR(512) NOT NULL,  -- Path to .bin file with neural weights (e.g., /app/brain_states/student_123.bin)
    is_active BOOLEAN DEFAULT TRUE,

    -- Performance metrics (updated with every interaction)
    total_interactions BIGINT DEFAULT 0,
    neural_inference_count BIGINT DEFAULT 0,  -- Queries handled by neural inference (fast, free)
    llm_query_count BIGINT DEFAULT 0,         -- Queries requiring LLM fallback (slow, costly)
    average_confidence REAL DEFAULT 0.0,      -- Running average of prediction confidence (0-1)
    average_accuracy REAL DEFAULT 0.0,        -- Running average of prediction accuracy (0-1)
    last_learning_timestamp TIMESTAMP,        -- When brain last learned something new

    -- Copy-on-Write (COW) metrics
    is_cow_clone BOOLEAN DEFAULT FALSE,
    cow_shared_bytes BIGINT DEFAULT 0,  -- Bytes shared with parent brain (memory savings)
    cow_copied_bytes BIGINT DEFAULT 0,  -- Bytes copied due to unique learning

    -- Self-awareness metadata (meta-cognitive layer)
    strong_domains JSONB DEFAULT '{}'::jsonb,        -- e.g., {"math": 0.92, "writing": 0.87}
    weak_domains JSONB DEFAULT '{}'::jsonb,          -- e.g., {"advanced_calculus": 0.54}
    bias_detections JSONB DEFAULT '{}'::jsonb,       -- e.g., {"overconfidence_math": 3}
    capability_boundaries JSONB DEFAULT '{}'::jsonb  -- Known limitations and boundary conditions
);

-- Indexes for efficient querying
CREATE INDEX idx_brain_instances_type ON brain_instances(brain_type);
CREATE INDEX idx_brain_instances_owner ON brain_instances(owner_id) WHERE owner_id IS NOT NULL;
CREATE INDEX idx_brain_instances_parent ON brain_instances(parent_brain_id) WHERE parent_brain_id IS NOT NULL;
CREATE INDEX idx_brain_instances_active ON brain_instances(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_brain_instances_last_updated ON brain_instances(last_updated DESC);

-- Unique constraint: Each student/instructor can have only one brain of each type
CREATE UNIQUE INDEX idx_brain_instances_unique_owner_type
    ON brain_instances(owner_id, brain_type)
    WHERE owner_id IS NOT NULL;

-- Unique constraint: Only one platform brain
CREATE UNIQUE INDEX idx_brain_instances_unique_platform
    ON brain_instances(brain_type)
    WHERE brain_type = 'platform';

-- Comments for documentation
COMMENT ON TABLE brain_instances IS 'Neuromorphic AI brain instances for the self-aware learning platform';
COMMENT ON COLUMN brain_instances.brain_id IS 'Unique identifier for this brain instance';
COMMENT ON COLUMN brain_instances.brain_type IS 'Type of brain: platform (master), student, instructor, content, or ethics';
COMMENT ON COLUMN brain_instances.owner_id IS 'Owner UUID (student_id or instructor_id), NULL for platform/shared brains';
COMMENT ON COLUMN brain_instances.parent_brain_id IS 'Parent brain ID for COW cloning hierarchy';
COMMENT ON COLUMN brain_instances.state_file_path IS 'Filesystem path to .bin file containing neural network weights';
COMMENT ON COLUMN brain_instances.total_interactions IS 'Total number of interactions (predictions, learning, reinforcement)';
COMMENT ON COLUMN brain_instances.neural_inference_count IS 'Number of predictions handled by neural network (not LLM)';
COMMENT ON COLUMN brain_instances.llm_query_count IS 'Number of predictions requiring LLM fallback due to low confidence';
COMMENT ON COLUMN brain_instances.cow_shared_bytes IS 'Bytes shared with parent brain through COW (memory savings)';
COMMENT ON COLUMN brain_instances.cow_copied_bytes IS 'Bytes copied due to unique learning (COW overhead)';

-- ============================================================================
-- Table: brain_interactions
-- ============================================================================
-- Purpose: Log every interaction for continuous learning and analytics
--
-- Business Logic:
--   Every interaction (prediction, learning, reinforcement) is logged for:
--   - Analytics: Track brain learning progress over time
--   - Debugging: Investigate unexpected behaviors
--   - Reinforcement Learning: Delayed reward assignment
--   - Meta-Cognitive Updates: Confidence calibration
--
-- Interaction Types:
--   - 'prediction': Neural inference or LLM fallback
--   - 'learning': Supervised learning from explicit examples
--   - 'reinforcement': Reward-based learning from outcomes
--
-- Performance Considerations:
--   - High-volume table (100K+ rows per active brain)
--   - Partitioned by interaction_timestamp (monthly)
--   - Archived after 6 months to maintain performance
-- ============================================================================

CREATE TABLE IF NOT EXISTS brain_interactions (
    -- Primary identity
    interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brain_id UUID NOT NULL REFERENCES brain_instances(brain_id) ON DELETE CASCADE,

    -- Interaction metadata
    interaction_type VARCHAR(50) NOT NULL CHECK (interaction_type IN ('prediction', 'learning', 'reinforcement')),
    interaction_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Input data
    features_vector JSONB,  -- Input feature vector (e.g., [0.5, 0.3, 0.8])
    context_data JSONB,     -- Additional context (e.g., {"module_id": "123", "difficulty": "medium"})

    -- Output data
    prediction_output JSONB,  -- Neural network or LLM output
    prediction_confidence REAL,  -- Confidence score (0-1)
    used_llm BOOLEAN DEFAULT FALSE,  -- Whether LLM was used (vs neural inference)

    -- Learning data
    ground_truth_label VARCHAR(255),  -- For supervised learning
    reward_signal REAL,               -- For reinforcement learning (0-1)
    actual_accuracy REAL,             -- Measured accuracy if outcome observed

    -- Meta-cognitive tracking
    domain VARCHAR(100),  -- Knowledge domain (e.g., "math", "writing", "programming")
    bias_detected VARCHAR(100),  -- If bias was detected in this interaction

    -- Performance tracking
    inference_latency_ms REAL,  -- How long the prediction took
    llm_cost_usd REAL           -- Cost if LLM was used
);

-- Indexes for efficient querying
CREATE INDEX idx_brain_interactions_brain_id ON brain_interactions(brain_id);
CREATE INDEX idx_brain_interactions_timestamp ON brain_interactions(interaction_timestamp DESC);
CREATE INDEX idx_brain_interactions_type ON brain_interactions(interaction_type);
CREATE INDEX idx_brain_interactions_domain ON brain_interactions(domain) WHERE domain IS NOT NULL;
CREATE INDEX idx_brain_interactions_used_llm ON brain_interactions(used_llm) WHERE used_llm = TRUE;

-- Composite index for analytics queries
CREATE INDEX idx_brain_interactions_brain_timestamp
    ON brain_interactions(brain_id, interaction_timestamp DESC);

-- Comments
COMMENT ON TABLE brain_interactions IS 'Log of every brain interaction for continuous learning and analytics';
COMMENT ON COLUMN brain_interactions.interaction_type IS 'Type of interaction: prediction, learning, or reinforcement';
COMMENT ON COLUMN brain_interactions.features_vector IS 'Input feature vector as JSON array';
COMMENT ON COLUMN brain_interactions.used_llm IS 'Whether LLM was used (TRUE) or neural inference (FALSE)';
COMMENT ON COLUMN brain_interactions.reward_signal IS 'Reward for reinforcement learning (0=failure, 1=success)';

-- ============================================================================
-- Table: brain_self_assessments
-- ============================================================================
-- Purpose: Track meta-cognitive self-awareness over time
--
-- Business Logic:
--   Periodic snapshots of the brain's self-assessment of its capabilities,
--   biases, and confidence calibration. Used to detect:
--   - Overconfidence: Predicting high confidence but low accuracy
--   - Underconfidence: Predicting low confidence but high accuracy
--   - Domain drift: Previously strong domains becoming weak
--   - Learning progress: Weak domains becoming strong over time
--
-- Update Frequency:
--   - After every 1000 interactions
--   - When significant accuracy changes detected
--   - Daily for platform brain
-- ============================================================================

CREATE TABLE IF NOT EXISTS brain_self_assessments (
    -- Primary identity
    assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brain_id UUID NOT NULL REFERENCES brain_instances(brain_id) ON DELETE CASCADE,
    assessment_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Confidence calibration
    confidence_accuracy_correlation REAL,  -- Correlation between confidence and actual accuracy (-1 to 1)
    overconfidence_rate REAL,              -- % of high-confidence predictions that were wrong
    underconfidence_rate REAL,             -- % of low-confidence predictions that were right

    -- Domain assessments
    strong_domains JSONB DEFAULT '{}'::jsonb,  -- Snapshot of strong domains at this time
    weak_domains JSONB DEFAULT '{}'::jsonb,    -- Snapshot of weak domains at this time
    improving_domains JSONB DEFAULT '[]'::jsonb,  -- Domains showing improvement
    degrading_domains JSONB DEFAULT '[]'::jsonb,  -- Domains showing degradation

    -- Bias tracking
    detected_biases JSONB DEFAULT '{}'::jsonb,  -- Active biases detected
    corrective_actions JSONB DEFAULT '[]'::jsonb,  -- Actions taken to correct biases

    -- Learning velocity
    learning_rate_estimate REAL,  -- Estimated learning rate (how fast brain improves)
    plateau_detected BOOLEAN DEFAULT FALSE,  -- Whether learning has plateaued

    -- Capability boundaries
    known_limitations JSONB DEFAULT '[]'::jsonb,  -- Known things the brain can't do well
    edge_cases JSONB DEFAULT '[]'::jsonb          -- Identified edge cases where brain struggles
);

-- Indexes
CREATE INDEX idx_brain_self_assessments_brain_id ON brain_self_assessments(brain_id);
CREATE INDEX idx_brain_self_assessments_timestamp ON brain_self_assessments(assessment_timestamp DESC);

-- Comments
COMMENT ON TABLE brain_self_assessments IS 'Meta-cognitive self-awareness assessments over time';
COMMENT ON COLUMN brain_self_assessments.confidence_accuracy_correlation IS 'Correlation between predicted confidence and actual accuracy';
COMMENT ON COLUMN brain_self_assessments.overconfidence_rate IS 'Percentage of high-confidence predictions that were incorrect';
COMMENT ON COLUMN brain_self_assessments.learning_rate_estimate IS 'Estimated rate of learning improvement';

-- ============================================================================
-- Views for Analytics
-- ============================================================================

-- View: Brain performance summary
CREATE OR REPLACE VIEW brain_performance_summary AS
SELECT
    b.brain_id,
    b.brain_type,
    b.owner_id,
    b.created_at,
    b.total_interactions,
    b.neural_inference_count,
    b.llm_query_count,
    CASE
        WHEN b.total_interactions > 0
        THEN (b.neural_inference_count::real / b.total_interactions::real) * 100
        ELSE 0
    END AS neural_inference_rate_percent,
    CASE
        WHEN b.total_interactions > 0
        THEN (b.llm_query_count::real / b.total_interactions::real) * 100
        ELSE 0
    END AS llm_usage_rate_percent,
    b.average_confidence,
    b.average_accuracy,
    b.cow_shared_bytes,
    b.cow_copied_bytes,
    CASE
        WHEN (b.cow_shared_bytes + b.cow_copied_bytes) > 0
        THEN (b.cow_shared_bytes::real / (b.cow_shared_bytes + b.cow_copied_bytes)::real) * 100
        ELSE 0
    END AS cow_efficiency_percent,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - b.last_updated)) / 3600 AS hours_since_last_update
FROM brain_instances b
WHERE b.is_active = TRUE;

COMMENT ON VIEW brain_performance_summary IS 'Summary of brain performance metrics for analytics dashboards';

-- View: Daily brain activity
CREATE OR REPLACE VIEW brain_daily_activity AS
SELECT
    brain_id,
    DATE(interaction_timestamp) AS activity_date,
    COUNT(*) AS total_interactions,
    COUNT(*) FILTER (WHERE interaction_type = 'prediction') AS predictions,
    COUNT(*) FILTER (WHERE interaction_type = 'learning') AS learning_events,
    COUNT(*) FILTER (WHERE interaction_type = 'reinforcement') AS reinforcement_events,
    COUNT(*) FILTER (WHERE used_llm = TRUE) AS llm_queries,
    COUNT(*) FILTER (WHERE used_llm = FALSE) AS neural_inferences,
    AVG(prediction_confidence) AS avg_confidence,
    AVG(actual_accuracy) FILTER (WHERE actual_accuracy IS NOT NULL) AS avg_accuracy,
    SUM(llm_cost_usd) AS total_llm_cost
FROM brain_interactions
GROUP BY brain_id, DATE(interaction_timestamp);

COMMENT ON VIEW brain_daily_activity IS 'Daily aggregation of brain interactions for analytics';

-- ============================================================================
-- Functions for Brain Management
-- ============================================================================

-- Function: Update brain statistics after interaction
CREATE OR REPLACE FUNCTION update_brain_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE brain_instances
    SET
        total_interactions = total_interactions + 1,
        neural_inference_count = neural_inference_count + CASE WHEN NEW.used_llm = FALSE THEN 1 ELSE 0 END,
        llm_query_count = llm_query_count + CASE WHEN NEW.used_llm = TRUE THEN 1 ELSE 0 END,
        last_updated = CURRENT_TIMESTAMP
    WHERE brain_id = NEW.brain_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update brain stats on interaction insert
DROP TRIGGER IF EXISTS trigger_update_brain_stats ON brain_interactions;
CREATE TRIGGER trigger_update_brain_stats
    AFTER INSERT ON brain_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_brain_stats();

COMMENT ON FUNCTION update_brain_stats() IS 'Automatically update brain statistics when interactions are logged';

-- Function: Calculate COW efficiency
CREATE OR REPLACE FUNCTION calculate_cow_efficiency(
    p_brain_id UUID
)
RETURNS REAL AS $$
DECLARE
    v_shared_bytes BIGINT;
    v_copied_bytes BIGINT;
    v_efficiency REAL;
BEGIN
    SELECT cow_shared_bytes, cow_copied_bytes
    INTO v_shared_bytes, v_copied_bytes
    FROM brain_instances
    WHERE brain_id = p_brain_id;

    IF (v_shared_bytes + v_copied_bytes) = 0 THEN
        RETURN 0.0;
    END IF;

    v_efficiency := (v_shared_bytes::real / (v_shared_bytes + v_copied_bytes)::real) * 100;
    RETURN v_efficiency;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_cow_efficiency(UUID) IS 'Calculate Copy-on-Write memory efficiency percentage for a brain';

-- ============================================================================
-- Initial Data: Create Platform Brain Entry
-- ============================================================================
-- Note: The actual platform brain will be created by the NIMCP service on first startup
-- This is just a placeholder to demonstrate the schema

-- INSERT INTO brain_instances (
--     brain_type,
--     owner_id,
--     parent_brain_id,
--     state_file_path,
--     is_active
-- ) VALUES (
--     'platform',
--     NULL,
--     NULL,
--     '/app/brain_states/platform_brain_initial.bin',
--     TRUE
-- )
-- ON CONFLICT DO NOTHING;

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Grant permissions (adjust based on your database user setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON brain_instances TO nimcp_service_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON brain_interactions TO nimcp_service_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON brain_self_assessments TO nimcp_service_user;
-- GRANT SELECT ON brain_performance_summary TO nimcp_service_user;
-- GRANT SELECT ON brain_daily_activity TO nimcp_service_user;
